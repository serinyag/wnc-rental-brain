from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import pytest
from tools.phase_08_workflow import asana_custom_fields as f
from tools.phase_08_workflow.tests.test_asana_operator_adapter import operator, rich_transport
from tools.phase_08_workflow.tests.test_asana_projection import harness, execute, NOW
from tools.phase_08_workflow.tests.test_working_proposal import add_fact


def test_exact_field_mapping_and_explicit_removals_without_confirmation():
    repo, _, _ = harness()
    add_fact(repo, 'catering_arrangement', 'client_external_caterer', 0)
    add_fact(repo, 'technical_requirements', ['microphones'], 0)
    add_fact(repo, 'primary_contact', {'email': 'maria@example.com'}, 0)
    v = f.project(repo.load_case_snapshot(1))
    assert v == {f.ROOM: f.ROOMS['studio_space'], f.EVENT: f.EVENTS['team_workshop'],
                 f.CONTACT: 'maria@example.com', f.ADDONS: [f.CATERING, f.TECH]}
    add_fact(repo, 'requested_rental_scope', 'entire_venue', 1)
    add_fact(repo, 'catering_arrangement', 'drinks_refreshments_only', 1)
    add_fact(repo, 'technical_requirements', ['none'], 1)
    add_fact(repo, 'primary_contact', {'email': 'new@example.com'}, 1)
    add_fact(repo, 'event_type', 'uncatalogued_event', 1)
    v = f.project(repo.load_case_snapshot(1))
    assert v == {f.ROOM: f.ROOMS['entire_venue'], f.EVENT: None,
                 f.CONTACT: 'new@example.com', f.ADDONS: [f.DRINKS]}
    assert not repo.load_case_snapshot(1).workflow_events


def field_transport(transport):
    original = transport.send_json
    defs = {f.RENT: {'gid':f.RENT,'id_prefix':'RENT','resource_subtype':'text'},
            f.ROOM:{'gid':f.ROOM,'resource_subtype':'enum','enum_options':[{'gid':gid,'enabled':True} for gid in f.ROOMS.values()]},
            f.EVENT:{'gid':f.EVENT,'resource_subtype':'enum','enum_options':[{'gid':gid,'enabled':True} for gid in set(f.EVENTS.values())]},
            f.CONTACT:{'gid':f.CONTACT,'resource_subtype':'text'},
            f.ADDONS:{'gid':f.ADDONS,'resource_subtype':'multi_enum','enum_options':[{'gid':gid,'enabled':True} for gid in [f.CATERING,f.DRINKS,f.TECH]]}}
    def send(**kw):
        payload = kw['payload'].get('data',{})
        if 'custom_fields' in payload:
            payload['custom_fields'] = [{'gid':gid, **({'text_value':value} if gid==f.CONTACT else
                 {'multi_enum_values':[{'gid':v} for v in value]} if gid==f.ADDONS else
                 {'enum_value':{'gid':value} if value else None})} for gid,value in payload['custom_fields'].items()]
            payload['custom_fields'].append({'gid':f.RENT,'display_value':'RENT-68'})
        status, body, headers = original(**kw)
        if kw['method']=='GET' and '/projects/222?' in kw['url']:
            parsed=json.loads(body);parsed['data']['custom_field_settings']=[{'custom_field':v} for v in defs.values()]
            body=json.dumps(parsed)
        return status, body, headers
    transport.send_json=send


def test_adapter_fields_same_master_rent_and_replay_with_drift_fence(monkeypatch):
    monkeypatch.setattr(f,'WORKSPACE','111')
    repo, transport, adapter = harness();rich_transport(transport);field_transport(transport)
    action=operator(repo)
    assert execute(repo,adapter,action).action_status_after=='succeeded'
    first=repo.load_case_snapshot(1).execution_attempts[-1].response_snapshot['bindings']['master']
    assert first['rent_id']=='RENT-68'
    repo.rental_cases[1]=replace(repo.rental_cases[1],case_revision=1)
    add_fact(repo,'requested_rental_scope','entire_venue',1)
    add_fact(repo,'primary_contact',{'email':'new@example.com'},1)
    followup=operator(repo)
    assert execute(repo,adapter,followup).action_status_after=='succeeded'
    latest=repo.load_case_snapshot(1).execution_attempts[-1].response_snapshot['bindings']['master']
    assert latest['gid']==first['gid'] and latest['rent_id']==first['rent_id']
    assert adapter.observe(action=followup)['status']=='matches_projection'
    n=len(transport.mutations)
    assert execute(repo,adapter,followup).already_succeeded_idempotently
    assert len(transport.mutations)==n
    transport.tasks[first['gid']]['custom_fields'][-1]['display_value']='RENT-69'
    assert adapter.observe(action=followup)['status']=='review_required'
    repo.rental_cases[1]=replace(repo.rental_cases[1],case_revision=2)
    assert execute(repo,adapter,operator(repo)).action_status_after=='failed'
    assert len(transport.mutations)==n


def test_disabled_option_is_rejected_before_mutation():
    with pytest.raises(ValueError):
        f.verify_definitions({'custom_field_settings':[]},{f.ROOM:f.ROOMS['studio_space']})
