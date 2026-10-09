"""Current governed draft inputs without a model or outbound provider call."""
from staging import *
from unittest.mock import patch
from tools.phase_08_workflow.outlook_inbound_service import connection_runner
response=client().request('POST','/api/operator/cases/586/reconcile',{})
save('reconciliation',response)
assert response['ok'],response['report']
with connect() as conn:
    conn.execute('set transaction read only')
    s=service(conn);runner=connection_runner(conn)
    with patch('tools.phase_05_search.search_hybrid.run_supabase_query',runner),patch('urllib.request.urlopen',side_effect=AssertionError('No external HTTP during context proof')):
        detail,snap,contract=s._build_current_governed_draft_contract(586)
    truths=current_resolutions(snap)
    assert snap.rental_case.case_revision==5 and len(truths)==2
    assert not any(i.proposition_key.startswith('availability:') for i in contract.resolution_items)
    assert len(client_results(snap))==2
    before=json.loads((OUT/'before.json').read_text())['snapshot']
    for f in before['rental_case_facts']:
        assert next(asdict(x) for x in snap.rental_case_facts if x.rental_case_fact_id==f['rental_case_fact_id'])==f
    capacity=[i for i in contract.resolution_items if 'layout' in i.message.lower()]
    assert capacity and all(i.blocking for i in capacity)
    data={'case_revision':snap.rental_case.case_revision,'resolutions':truths,
        'client_assertions':client_results(snap),'draft_contract':asdict(contract),
        'editorial_plan':asdict(contract.editorial_plan),'generation_payload':contract.to_provider_payload(),
        'remaining_resolution_items':[i.to_payload() for i in contract.resolution_items],
        'protected_cases_unchanged':protected(conn),
        'approval_blocked_by_internal_annotations':any(a.blocking for a in contract.operator_annotations),
        'current_reasoning_projections':[asdict(p) for p in snap.reasoning_projections if p.source_case_revision==5]}
save('current_context',data)
print(json.dumps({k:data[k] for k in ('case_revision','client_assertions','remaining_resolution_items','approval_blocked_by_internal_annotations','current_reasoning_projections')},indent=2))
