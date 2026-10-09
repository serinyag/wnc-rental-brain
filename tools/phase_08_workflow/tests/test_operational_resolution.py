"""Provider-free authority and persistence proofs, always rolled back locally."""
import copy
import json
import os
from dataclasses import replace
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace as NS
from uuid import uuid4

import pytest

from tools.phase_08_workflow.operational_resolution import (
    obligation, submit, validate_submission, current_resolutions, resolved_keys, client_results)
from tools.phase_08_workflow.context_aware_drafting import derive_resolution_items, with_workflow_actions
from tools.phase_08_workflow.governed_client_response import build_draft_contract, ClientResponseDraft, validate_client_response_draft
from tools.phase_08_workflow.tests.test_asana_projection_postgres import pg
from tools.phase_08_workflow.outlook_inbound_service import connection_runner
from tools.phase_08_workflow.orchestration_repository import SupabaseWorkflowOrchestrationRepository

ROOT = Path(__file__).resolve().parents[3]

@pytest.fixture
def resolution(pg):
    conn, repo, cid, *_ = pg
    conn.execute((ROOT/'supabase/migrations/20261009000100_phase_08_operational_resolution.sql').read_text())
    snap = repo.load_case_snapshot(cid)
    c = snap.rental_case
    base = snap.workflow_actions[0]
    key = f'availability:{c.active_event_start}:{c.active_event_end}'
    action = repo.create_workflow_action(replace(base, workflow_action_id=1,
        action_type='CREATE_INTERNAL_TASK_ITEM', status='ready_to_execute',
        idempotency_key='resolution-test-'+str(uuid4()), semantic_subject_hash='resolution-test',
        structured_payload={'resolution_item_key':key,'resolution_owner':'WNC_INTERNAL','resolution_status':'REQUIRED'}))
    snap = repo.load_case_snapshot(cid)
    contract = obligation(snap, action)
    request = dict(workflow_action_id=action.workflow_action_id, expected_case_revision=c.case_revision,
        contract=contract, outcomes={c.rental_type_code:'AVAILABLE'}, evidence_reference='synthetic:operator:test',
        evidence_text='staging synthetic operator evidence: explicit availability result',
        occurred_at=(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat(), idempotency_key=str(uuid4()), synthetic=True)
    def accept(r=None):
        return submit(repo, rental_case_id=cid, submission=r or request, actor='authenticated-test-operator')
    return conn,repo,cid,action,request,accept


def test_open_and_completed_actions_have_no_authority(resolution):
    conn,repo,cid,action,request,accept=resolution
    for completed in ('REQUIRED','resolved','completed'):
        conn.execute("update public.workflow_actions set structured_payload=structured_payload || %s::jsonb where id=%s",
                     (json.dumps({'resolution_status':completed,'completed':True}),action.workflow_action_id))
        s=repo.load_case_snapshot(cid)
        assert not current_resolutions(s)
        assert request['contract']['resolution_item_key'] in {i.proposition_key for i in derive_resolution_items(s)}
        assert with_workflow_actions(derive_resolution_items(s),s.workflow_actions)


@pytest.mark.parametrize('outcome',['AVAILABLE','UNAVAILABLE'])
def test_accept_fact_revision_scope_pending_and_drafting(resolution,outcome):
    conn,repo,cid,action,r,accept=resolution
    r['outcomes']={r['contract']['scope']['venue']:outcome}
    before=repo.load_case_snapshot(cid)
    result=accept()
    s=repo.load_case_snapshot(cid)
    assert s.rental_case.case_revision == before.rental_case.case_revision+1
    fact=current_resolutions(s)[0]
    assert fact['outcomes']==r['outcomes']
    assert fact['contract']['scope']==r['contract']['scope']
    assert r['contract']['resolution_item_key'] in resolved_keys(s)
    assert r['contract']['resolution_item_key'] not in {i.proposition_key for i in derive_resolution_items(s)}
    contract=build_draft_contract(snapshot=s,recipient_label='Avery',latest_client_message='Please confirm availability.')
    assertion=client_results(s)[0]['assertion']
    assert 'rental_case_id' not in json.dumps(contract.to_provider_payload())
    assert any(i.value.get('assertion')==assertion and i.included for i in contract.editorial_plan.items)
    draft=ClientResponseDraft('Studio availability','Hi Avery,\n\nThanks for the timing. '+assertion)
    validation=validate_client_response_draft(contract=contract,draft=draft,current_case_revision=s.rental_case.case_revision,current_context_hash=contract.context_hash)
    assert validation.is_valid,validation
    bad=replace(draft,body="Hi Avery,\n\nI'll check availability and come back to you.")
    assert not validate_client_response_draft(contract=contract,draft=bad,current_case_revision=s.rental_case.case_revision,current_context_hash=contract.context_hash).is_valid


def test_replay_and_conflicting_replay(resolution):
    conn,repo,cid,a,r,accept=resolution
    first=accept(); second=accept()
    assert second=={**first,'replayed':True}
    assert repo.load_case_snapshot(cid).rental_case.case_revision==first['case_revision']
    changed=copy.deepcopy(r);changed['evidence_text']='different evidence'
    with pytest.raises(Exception,match='resolution_replay_payload_conflict'),conn.transaction():accept(changed)


def test_correction_immutable_history_conflict_and_negative(resolution):
    conn,repo,cid,a,r,accept=resolution
    first=accept()
    before=conn.execute('select row_to_json(e) from public.workflow_events e where id=%s',(first['event_id'],)).fetchone()[0]
    correction=copy.deepcopy(r)
    correction.update(idempotency_key=str(uuid4()),expected_case_revision=first['case_revision'],outcomes={r['contract']['scope']['venue']:'UNAVAILABLE'})
    with pytest.raises(Exception,match='conflicting_resolution_requires_explicit_correction'),conn.transaction():accept(correction)
    correction['supersedes_event_id']=first['event_id']
    second=accept(correction)
    assert second['case_revision']==first['case_revision']+1
    assert conn.execute('select row_to_json(e) from public.workflow_events e where id=%s',(first['event_id'],)).fetchone()[0]==before
    assert 'unavailable' in client_results(repo.load_case_snapshot(cid))[0]['assertion']


@pytest.mark.parametrize('change',[{'actor':'llm'},{'authority_class':'WNC_INTERNAL_OPERATOR'},{'source':'Asana'},
    {'external_party':'supplier'},{'synthetic':False},{'evidence_text':''},{'outcomes':{'entire_venue':'AVAILABLE'}},
    {'outcomes':{'studio_space':'BOOKED'}},{'outcomes':{'payment':'PAID'}}])
def test_untrusted_sources_and_scope_expansion_rejected(resolution,change):
    conn,repo,cid,a,r,accept=resolution
    changed={**r,**change}
    with pytest.raises(ValueError):accept(changed)
    assert not current_resolutions(repo.load_case_snapshot(cid))


def test_other_case_action_scope_and_revision_fences(resolution):
    conn,repo,cid,a,r,accept=resolution
    for field,value in [('workflow_action_id',a.workflow_action_id+99999),('expected_case_revision',999)]:
        changed={**r,field:value}
        with pytest.raises(Exception),conn.transaction():accept(changed)
    for field,value in [('rental_case_id',cid+1),('venue','entire_venue'),('start','2027-11-12T13:00:00+00:00')]:
        changed=copy.deepcopy(r);changed['contract']['scope'][field]=value
        with pytest.raises(ValueError):accept(changed)
    accept()
    conn.execute("update public.rental_cases set active_event_start=active_event_start+interval '1 day',active_event_end=active_event_end+interval '1 day',case_revision=case_revision+1 where id=%s",(cid,))
    assert not current_resolutions(repo.load_case_snapshot(cid))


def test_technical_partial_resolution_contract_is_narrow(resolution):
    conn,repo,cid,a,r,accept=resolution
    s=repo.load_case_snapshot(cid)
    technical=replace(a,structured_payload={**a.structured_payload,'resolution_item_key':'blocker:7'})
    s=replace(s,blockers=(NS(blocker_id=7,origin_entity_reference='reasoning_projection:technical',status='open',blocker_type='technical_confirmation',resolution_condition_text='Confirm technical setup'),),
        reasoning_projections=(NS(projection_identity_key='technical',authority_outcome_classification='REQUIRES_CONFIRMATION',grounding_reference_keys=('test_console:technical_projection',)),))
    observed=(NS(field_code='technical_requirements',value_payload=['projection_display','microphones'],observation_status='validated'),)
    c=obligation(s,technical,observed_fields=observed)
    assert c['subjects']==['microphones','projection_display']
    r={**r,'contract':c,'outcomes':{'projection_display':'FEASIBLE'}}
    validated=validate_submission(c,r,actor='operator')
    assert set(validated['outcomes'])!=set(c['subjects'])
    for outcomes in ({'technician':'FEASIBLE'},{'microphones':'AVAILABLE'}):
        with pytest.raises(ValueError):validate_submission(c,{**r,'outcomes':outcomes},actor='operator')


def test_unbacked_fact_is_not_authority(resolution):
    conn,repo,cid,a,r,accept=resolution
    result=accept()
    conn.execute("update public.rental_case_facts set value_payload=jsonb_set(value_payload,'{outcomes}',%s::jsonb) where id=%s",
                 (json.dumps({r['contract']['scope']['venue']:'UNAVAILABLE'}),result['fact_id']))
    assert not current_resolutions(repo.load_case_snapshot(cid))


@pytest.mark.parametrize('outcome',['FEASIBLE','NOT_FEASIBLE'])
def test_technical_persistence_partial_then_full_and_asana(resolution,outcome):
    from unittest.mock import patch
    from tools.phase_08_workflow.asana_projection import build_projection
    conn,repo,cid,a,r,accept=resolution
    key='blocker:777'
    conn.execute("update public.workflow_actions set structured_payload=structured_payload || %s::jsonb where id=%s",
                 (json.dumps({'resolution_item_key':key,'summary':'Confirm requested projection and microphones'}),a.workflow_action_id))
    original=repo.load_case_snapshot
    def snapshot(case):
        s=original(case)
        return replace(s,blockers=(NS(blocker_id=777,origin_entity_reference='reasoning_projection:technical',
            status='open',blocker_type='technical_confirmation',origin_entity_type='reasoning_projection',
            resolution_condition_text='Confirm event technical setup'),),
            reasoning_projections=(NS(projection_identity_key='technical',authority_outcome_classification='REQUIRES_CONFIRMATION',
                grounding_reference_keys=('test_console:technical_projection',)),))
    observed=(NS(field_code='technical_requirements',value_payload=['projection_display','microphones'],observation_status='validated'),)
    s=snapshot(cid); a=next(x for x in s.workflow_actions if x.workflow_action_id==a.workflow_action_id)
    c=obligation(s,a,observed_fields=observed)
    r={**r,'contract':c,'outcomes':{'projection_display':outcome}}
    with patch.object(repo,'load_case_snapshot',side_effect=snapshot):
        first=submit(repo,rental_case_id=cid,submission=r,actor='operator',observed_fields=observed)
    s=original(cid)
    assert key not in resolved_keys(s)
    assert current_resolutions(s)[0]['outcomes']=={'projection_display':outcome}
    plan=build_projection(s,workspace_gid='111',project_gid='222')
    # Schema nesting is stable in the certified projection.
    assert key in json.dumps(plan)
    r={**r,'expected_case_revision':first['case_revision'],'idempotency_key':str(uuid4()),
       'supersedes_event_id':first['event_id'],'outcomes':{'projection_display':outcome,'microphones':'FEASIBLE'}}
    with patch.object(repo,'load_case_snapshot',side_effect=snapshot):
        submit(repo,rental_case_id=cid,submission=r,actor='operator',observed_fields=observed)
    s=original(cid)
    assert key in resolved_keys(s)
    assert len(client_results(s))==2
    assert ('not feasible' if outcome=='NOT_FEASIBLE' else 'is feasible') in client_results(s)[1]['assertion'] or any(
        ('not feasible' if outcome=='NOT_FEASIBLE' else 'is feasible') in item['assertion'] for item in client_results(s))
    contract=build_draft_contract(snapshot=s,recipient_label='Avery',latest_client_message='Can we use projection and microphones?')
    assert len([x for x in contract.editorial_plan.items if x.topic=='operational_confirmation' and x.included])==2


def test_evidence_journal_is_append_only(resolution):
    conn,repo,cid,a,r,accept=resolution
    result=accept()
    with pytest.raises(Exception,match='append-only'),conn.transaction():
        conn.execute("update public.workflow_events set structured_payload='{}'::jsonb where id=%s",(result['event_id'],))
    with pytest.raises(Exception,match='append-only'),conn.transaction():
        conn.execute('delete from public.workflow_events where id=%s',(result['event_id'],))


def test_booking_and_expanded_claim_still_rejected(resolution):
    conn,repo,cid,a,r,accept=resolution; accept();s=repo.load_case_snapshot(cid)
    contract=build_draft_contract(snapshot=s,recipient_label='Avery',latest_client_message='Availability?')
    for extra in ('Your booking is confirmed.','The entire venue is available.','The Studio is available tomorrow.'):
        body='Hi Avery,\n\nThanks for the timing. '+client_results(s)[0]['assertion']+' '+extra
        result=validate_client_response_draft(contract=contract,draft=ClientResponseDraft('Availability',body),
            current_case_revision=s.rental_case.case_revision,current_context_hash=contract.context_hash)
        assert not result.is_valid


def test_http_resolution_requires_authentication():
    from unittest.mock import Mock
    from tools.phase_08_workflow.tests.test_test_console_app import _FakeService, call_app, _basic_auth_header
    from tools.phase_08_workflow.test_console import TestConsoleApp
    from tools.phase_08_workflow.test_console_service import TestConsoleConfig
    from tools.runtime_environment import AppRuntimeConfig, AppEnvironment
    service=_FakeService(config=TestConsoleConfig(runtime=AppRuntimeConfig(app_env=AppEnvironment.STAGING,
        staging_basic_auth_username='operator',staging_basic_auth_password='test-password')))
    service.submit_operational_resolution=Mock(return_value={'event_id':1})
    app=TestConsoleApp(service);path='/api/operator/cases/1/operational-resolutions'
    assert call_app(app,'POST',path)[0]=='401 Unauthorized'
    service.submit_operational_resolution.assert_not_called()
    assert call_app(app,'POST',path,headers=_basic_auth_header('operator','test-password'))[0]=='200 OK'


def test_no_actor_and_external_evidence_require_authority(resolution):
    conn,repo,cid,a,r,accept=resolution
    with pytest.raises(ValueError):validate_submission(r['contract'],r,actor='')
    for extra in ({'source':'external_party'},{'source':'llm'},{'source':'asana','completed':True}):
        with pytest.raises(ValueError):validate_submission(r['contract'],{**r,**extra},actor='operator')


def test_superseded_lifecycle_can_report_only_still_current_obligation(resolution):
    conn,repo,cid,a,r,accept=resolution
    conn.execute("update public.workflow_actions set status='superseded' where id=%s",(a.workflow_action_id,))
    first=accept()
    assert current_resolutions(repo.load_case_snapshot(cid))
    assert accept()=={**first,'replayed':True}
    conn.execute("update public.rental_cases set active_event_start=active_event_start+interval '1 day',active_event_end=active_event_end+interval '1 day',case_revision=case_revision+1 where id=%s",(cid,))
    changed={**r,'idempotency_key':'different-current-obligation','expected_case_revision':first['case_revision']+1}
    with pytest.raises(ValueError,match='no_longer_current'):accept(changed)
