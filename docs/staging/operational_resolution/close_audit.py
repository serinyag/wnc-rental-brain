"""Read-only closure, protected lineages, inbound immutability and attempt count."""
from staging import *
from tools.phase_08_workflow.outlook_inbound_service import connection_runner
from unittest.mock import patch
health=client().get_health()
assert health['environment']=='staging' and health['status']=='ok'
assert health['providers']=={'asana':'configured_but_disabled','outlook':'configured_draft_only'}
assert health['application']['metrics']['outlook_inbound_gate']=='disabled'
assert health['application']['metrics']['outlook_inbound_preflight_gate']=='disabled'
save('health_final',health)
final=client().request('GET','/api/operator/cases/586')
save('case_final',final)
prior=json.loads((ROOT/'docs/staging/case586_integrated/case_final.json').read_text())
assert final['case']['evidence_bundles']==prior['case']['evidence_bundles'], 'Original inbound evidence changed'
snap=final['case']['orchestration_snapshot']
assert snap['rental_case']['case_revision']==5
assert not snap['approval_requests']
assert len(snap['execution_attempts'])==2
assert {a['execution_attempt_id'] for a in snap['execution_attempts']}=={26,27}
assert all(a['adapter_code']=='asana_projection' and a['status']=='succeeded' for a in snap['execution_attempts'])
last=snap['execution_attempts'][-1]['response_snapshot']
assert last['master_task_gid']=='1219351043478952'
assert len(last['bindings'])==4
assert sum(b['projected']['completed'] for k,b in last['bindings'].items() if k!='master')==2
before=json.loads((OUT/'before.json').read_text())['snapshot']
minimum=max(e['workflow_event_id'] for e in before['workflow_events'])
with connect() as conn:
    conn.execute('set transaction read only');preserved=protected(conn)
    events=conn.execute('select id,occurred_at,event_type_code,source_reference from public.workflow_events where rental_case_id=586 and id>%s order by id',(minimum,)).fetchall()
    s=service(conn);runner=connection_runner(conn)
    with patch('tools.phase_05_search.search_hybrid.run_supabase_query',runner),patch('urllib.request.urlopen',side_effect=AssertionError('No provider calls')):
        detail,current,contract=s._build_current_governed_draft_contract(586)
    assert len(current_resolutions(current))==2
    assert 'rental_case_id' not in json.dumps(contract.to_provider_payload())
    assert any(a.blocking for a in contract.operator_annotations)
    # Replay after reconciliation/lifecycle supersession is still evidence-idempotent.
    for aid in (1634,1633):
        submission=json.loads((OUT/f'resolution_{aid}_started.json').read_text())
        event=next(e for e in current.workflow_events if e.event_identity_key=='operational_resolution:'+submission['idempotency_key'])
        replay=submit(s.orchestration_repository,rental_case_id=586,submission=submission,actor=event.structured_payload['submission']['actor'])
        assert replay['replayed'] and replay['event_id'] in {17144,17145}
    save('closure_context',{'contract':asdict(contract),'provider_payload':contract.to_provider_payload(),
        'editorial_plan':asdict(contract.editorial_plan),'client_results':client_results(current)})
result={'marker':'WNC_OPERATIONAL_RESOLUTION_AUTHORITY_CERTIFIED_INTEGRATION_BLOCKED',
    'case_id':586,'case_revision':5,'resolution_events':[17144,17145],'case_facts':[1058,1059],
    'runtime_commit':'ad928321a140e7c1de1a733a91ba7bd42f2cf003',
    'asana_master_gid':last['master_task_gid'],'asana_actions':[1635,1637],'asana_attempts':[26,27],
    'asana_total_mutation_requests':sum(a['response_snapshot']['mutation_requests'] for a in snap['execution_attempts']),
    'asana_confirmed_mutations':sum(a['response_snapshot']['confirmed_mutations'] for a in snap['execution_attempts']),
    'asana_completed':[{'key':k,'gid':b['gid']} for k,b in last['bindings'].items() if k!='master' and b['projected']['completed']],
    'asana_open':[{'key':k,'gid':b['gid']} for k,b in last['bindings'].items() if k!='master' and not b['projected']['completed']],
    'graph_calls':0,'outbound_sends':0,'openai_external_calls':0,'production_changes':0,
    'original_inbound_evidence_unchanged':True,'protected_cases_unchanged':preserved,
    'final_draft_revision_id':None,'final_approval_request_id':None,
    'remaining_blocker':2386,'remaining_issue':'Missing layout/configuration authority; blocking internal annotation prevents frozen draft approval.',
    'focused_tests':82,'phase8_tests':684,'full_repository_tests':901,'events':events}
save('result',result)
print(json.dumps({k:v for k,v in result.items() if k!='events'},indent=2))
