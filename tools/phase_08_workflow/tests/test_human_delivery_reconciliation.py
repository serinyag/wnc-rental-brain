"""Provider-free real PostgreSQL reconciliation, with every fixture rolled back."""
import json
import os
import sys
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlparse

import pytest

from tools.phase_08_workflow.execution_runtime import execute_workflow_action
from tools.phase_08_workflow.execution_types import WorkflowActionExecutionRequest
from tools.phase_08_workflow.outlook_simulation import DeterministicOutlookTransport
from tools.phase_08_workflow.test_console_service import TestConsoleError
from tools.phase_08_workflow.tests.test_outlook_recertification import generated_service

ROOT = Path(__file__).resolve().parents[3]
MIGRATION = ROOT / 'supabase/migrations/20261003000100_phase_08_human_delivery_reconciliation.sql'


def test_enabled_gate_blocks_before_any_repository_or_provider_call():
    service = generated_service()
    service.config = replace(service.config, runtime=replace(service.config.runtime, staging_allow_real_outlook_send=True))
    with patch.object(service, '_require_case_snapshot', side_effect=AssertionError('No read allowed')), pytest.raises(TestConsoleError, match='gate disabled'):
        service.reconcile_human_confirmed_outlook_delivery(rental_case_id=424, workflow_action_id=1,
            draft_revision_id=1, approval_request_id=1, execution_attempt_id=1,
            recipient='client@example.test', subject='Synthetic', evidence_note='Receipt confirmed')


@pytest.fixture
def ambiguous():
    dsn = os.environ.get('WNC_TEST_POSTGRES_DSN')
    if not dsn:
        pytest.skip('requires explicitly selected local PostgreSQL')
    assert urlparse(dsn).hostname in {'localhost', '127.0.0.1', '::1'}
    import psycopg
    sys.path.insert(0, str(ROOT / 'docs/staging/outlook_recertification'))
    from provider_free_fixture import service_for, create_candidate, SyntheticProvider
    with psycopg.connect(dsn) as conn, conn.transaction(force_rollback=True), patch('urllib.request.urlopen', side_effect=AssertionError('Network prohibited')):
        for name in ('20260829000100_phase_08_general_governed_client_response_drafting.sql',
                     '20260907000100_phase_08_governed_client_response_action_type.sql',
                     '20260913000100_phase_08_outlook_canonical_plan_identity.sql'):
            conn.execute((ROOT / 'supabase/migrations' / name).read_text())
        conn.execute(MIGRATION.read_text())
        service = service_for(conn)
        cid = create_candidate(service)
        with patch('tools.phase_08_workflow.test_console_service.DeterministicFakeClientResponseProvider', SyntheticProvider):
            assert service.generate_governed_client_response_draft(rental_case_id=cid, use_deterministic_fixture=True).success
        rev = service._list_draft_revisions(cid)[0]
        assert service.approve_request(rental_case_id=cid, approval_request_id=rev.approval_request_id).success
        original = DeterministicOutlookTransport.request
        def inconclusive(transport, **kw):
            result = original(transport, **kw)
            if kw['method']=='GET' and transport.sent:
                return 200, json.dumps({'id':'provider-eventual-consistency','isDraft':True}), {}
            return result
        with patch.object(DeterministicOutlookTransport, 'request', inconclusive):
            service.execute_action(rental_case_id=cid, workflow_action_id=rev.workflow_action_id, execution_mode='success')
        snap = service._require_case_snapshot(cid)
        attempt = snap.execution_attempts[0]
        assert attempt.failure_code == 'adapter_outcome_ambiguous'
        args = dict(rental_case_id=cid, workflow_action_id=rev.workflow_action_id,
            draft_revision_id=rev.inquiry_response_draft_revision_id, approval_request_id=rev.approval_request_id,
            execution_attempt_id=attempt.execution_attempt_id, recipient=rev.recipient_email,
            subject=rev.subject, evidence_note='Human recipient confirms receipt after ambiguous automated verification.')
        yield conn, service, args


def rows(conn, table, cid):
    return conn.execute(f'select row_to_json(r) from public.{table} r where rental_case_id=%s order by id', (cid,)).fetchall()


def test_receipt_persists_idempotently_without_rewriting_attempt_or_approval(ambiguous):
    conn, service, args = ambiguous
    cid=args['rental_case_id']; aid=args['workflow_action_id']
    attempts=rows(conn,'workflow_execution_attempts',cid)
    approvals=rows(conn,'rental_case_approval_requests',cid)
    draft=asdict(service._load_draft_revision_by_id(cid,args['draft_revision_id']))
    assert service.reconcile_human_confirmed_outlook_delivery(**args).success
    after_first=rows(conn,'workflow_events',cid)
    assert 'Already reconciled: True' in service.reconcile_human_confirmed_outlook_delivery(**args).lines
    assert rows(conn,'workflow_events',cid)==after_first
    assert rows(conn,'workflow_execution_attempts',cid)==attempts
    assert rows(conn,'rental_case_approval_requests',cid)==approvals
    snap=service._require_case_snapshot(cid)
    assert snap.find_workflow_action(aid).status=='succeeded'
    events=[e for e in snap.workflow_events if e.event_type_code=='outlook_delivery_human_confirmed']
    assert len(events)==1
    assert events[0].structured_payload['original_execution_attempt']==attempts[0][0]
    assert events[0].structured_payload['provider_call_performed'] is False
    updated=asdict(service._load_draft_revision_by_id(cid,args['draft_revision_id']))
    assert updated['draft_status']=='human_confirmed_delivered'
    assert {k:v for k,v in draft.items() if k not in {'draft_status','updated_at'}} == {k:v for k,v in updated.items() if k not in {'draft_status','updated_at'}}
    with patch.object(service,'_build_execution_registry',side_effect=AssertionError('Provider constructed')), pytest.raises(TestConsoleError):
        service.execute_action(rental_case_id=cid,workflow_action_id=aid,execution_mode='real')
    result=execute_workflow_action(service.orchestration_repository,
        WorkflowActionExecutionRequest(rental_case_id=cid,workflow_action_id=aid,actor_reference='local-test',started_at=service.now()))
    assert result.failure_codes==('action_already_succeeded',)
    assert rows(conn,'workflow_execution_attempts',cid)==attempts


@pytest.mark.parametrize('change', [dict(recipient='wrong@example.test'),dict(subject='Wrong subject'),
    dict(draft_revision_id=999999999),dict(approval_request_id=999999999),dict(execution_attempt_id=999999999),dict(evidence_note='')])
def test_exact_binding_and_evidence_fail_closed(ambiguous,change):
    conn,service,args=ambiguous
    before=rows(conn,'workflow_events',args['rental_case_id'])
    with pytest.raises(TestConsoleError):
        service.reconcile_human_confirmed_outlook_delivery(**(args|change))
    assert rows(conn,'workflow_events',args['rental_case_id'])==before


def test_stale_database_payload_and_conflicting_confirmation_are_rejected(ambiguous):
    conn,service,args=ambiguous
    snap=service._require_case_snapshot(args['rental_case_id'])
    action=snap.find_workflow_action(args['workflow_action_id'])
    with conn.transaction(force_rollback=True), pytest.raises(Exception,match='human_delivery_lineage_mismatch'):
        service.orchestration_repository.reconcile_outlook_human_delivery(
            **args, expected_payload=action.structured_payload|{'body':'tampered'}, actor_reference='local-test')
    assert service.reconcile_human_confirmed_outlook_delivery(**args).success
    with conn.transaction(force_rollback=True), pytest.raises(Exception,match='human_delivery_reconciliation_conflict'):
        service.reconcile_human_confirmed_outlook_delivery(**(args|{'evidence_note':'Different evidence'}))
    assert len(service._require_case_snapshot(args['rental_case_id']).execution_attempts)==1


def test_atomic_failure_rolls_back_confirmation_event(ambiguous):
    conn,service,args=ambiguous
    before=rows(conn,'workflow_events',args['rental_case_id'])
    with conn.transaction(force_rollback=True):
        conn.execute("""create function pg_temp.reject_settlement() returns trigger language plpgsql as
            $$ begin raise exception 'synthetic settlement failure'; end $$;
            create trigger local_reject_settlement before update on public.workflow_actions
            for each row execute function pg_temp.reject_settlement();""")
        with conn.transaction(force_rollback=True), pytest.raises(Exception,match='synthetic settlement failure'):
            service.reconcile_human_confirmed_outlook_delivery(**args)
        assert rows(conn,'workflow_events',args['rental_case_id'])==before
        assert service._require_case_snapshot(args['rental_case_id']).find_workflow_action(args['workflow_action_id']).status=='failed'


def test_operator_route_passes_exact_confirmation_and_never_executes():
    from tools.phase_08_workflow.tests.test_test_console_app import _FakeService, call_app_response
    from tools.phase_08_workflow.test_console import TestConsoleApp
    from tools.phase_08_workflow.test_console_service import OperationReport
    service=_FakeService()
    with patch.object(service,'reconcile_human_confirmed_outlook_delivery',create=True,
                      return_value=OperationReport(title='Confirmed',success=True,lines=())) as reconcile:
        body=dict(draft_revision_id='386',approval_request_id='465',execution_attempt_id='23',
                  recipient='Serinya@whennaturecalls.nl',subject='Synthetic',evidence_note='Receipt confirmed')
        status,_,response=call_app_response(TestConsoleApp(service),'POST',
            '/api/operator/cases/584/actions/1619/confirm-delivery',body=json.dumps(body).encode())
        assert status=='200 OK'
        assert json.loads(response)['report']['success']
        reconcile.assert_called_once_with(rental_case_id=584,workflow_action_id=1619,
            **(body|dict(draft_revision_id=386,approval_request_id=465,execution_attempt_id=23)))
