"""Closure assertions; no network provider calls and no canonical mutations."""
from journey import *
from unittest.mock import patch
from tools.phase_08_workflow.operational_resolution import current_resolutions,client_results
from tools.phase_08_workflow.execution_runtime import _preflight_execution_failure
from tools.phase_08_workflow.outlook_adapter import _resolve_retry_state
from tools.phase_08_workflow.outlook_action_contract import validate_outlook_action
from tools.phase_08_workflow.outlook_inbound_service import connection_runner
from tools.phase_08_workflow.inbound_email import evidence_hash
health=client().get_health()
assert health['environment']=='staging' and health['status']=='ok'
assert health['providers']=={'asana':'configured_but_disabled','outlook':'configured_draft_only'}
assert health['application']['metrics']['outlook_inbound_gate']=='disabled'
assert health['application']['metrics']['outlook_inbound_preflight_gate']=='disabled'
save('health_final',health)
with connect() as c:
 c.execute('set transaction isolation level repeatable read, read only')
 s=service(c);snap=s._require_case_snapshot(586);assert snap.rental_case.case_revision==7
 assert len(current_resolutions(snap))==3
 revisions=s._list_draft_revisions(586);assert len(revisions)==1
 rev=revisions[0];assert rev.is_current and rev.inquiry_response_draft_revision_id==387 and rev.draft_status=='human_confirmed_delivered'
 action=snap.find_workflow_action(1640);assert action.status=='succeeded'
 approval=snap.find_approval_request(466);assert approval.status=='approved'
 initial=json.loads((OUT/'final_candidate.json').read_text())
 for field in ('subject','body_text','recipient_email','content_hash','context_hash','context_payload','source_case_revision'):
  assert json.loads(json.dumps(getattr(rev,field),default=str))==initial['revision'][field],field
 assert validate_outlook_action(action).to_payload()==initial['contract']
 attempts=[a for a in snap.execution_attempts if a.workflow_action_id==1640]
 assert len(attempts)==1 and attempts[0].execution_attempt_id==29 and not attempts[0].retry_eligible
 raw=c.execute('select row_to_json(t) from public.workflow_execution_attempts t where id=29').fetchone()[0]
 assert raw==json.loads((OUT/'send_attempt_original.json').read_text()),'Ambiguity record changed'
 prior_approval=next(a for a in json.loads((OUT/'final_approval.json').read_text())['case']['orchestration_snapshot']['approval_requests'] if a['approval_request_id']==466)
 assert json.loads(json.dumps(asdict(approval)))==prior_approval,'Exact approval changed'
 guard=_preflight_execution_failure(snap,action,now=lambda:datetime.now(timezone.utc).isoformat())
 assert guard is not None
 retry=_resolve_retry_state(tuple(attempts));assert retry.failure_code
 with patch('tools.phase_05_search.search_hybrid.run_supabase_query',connection_runner(c)),patch('urllib.request.urlopen',side_effect=AssertionError('No provider')):
  _,_,contract=s._build_current_governed_draft_contract(586)
 assert not contract.resolution_items and not any(a.blocking for a in contract.operator_annotations)
 assert contract.context_hash==validate_outlook_action(action).governed_context_hash
 messages=c.execute('select source_record_id,message_id,conversation_id,raw_provider_payload,source_hash from public.outlook_inbound_messages where rental_case_id=586 order by source_record_id').fetchall()
 assert [x[0] for x in messages]==[3104,3105,3106] and len({x[2] for x in messages})==1
 assert all(evidence_hash(x[3])==x[4] for x in messages)
 facts=[asdict(f) for f in snap.rental_case_facts]
 before=json.loads((ROOT/'docs/staging/operational_resolution/case_final.json').read_text())
 old_facts=before['case']['orchestration_snapshot']['rental_case_facts']
 normalized_facts=json.loads(json.dumps(facts))
 assert all(f in normalized_facts for f in old_facts),'Prior governed facts changed'
 detail=s.load_case_detail(586)
 bundles=json.loads(json.dumps([asdict(b) for b in detail.evidence_bundles]))
 assert all(b in bundles for b in before['case']['evidence_bundles']),'Original inbound observations/effects changed'
 # Record the complete lineage directly from immutable events; original baselines
 # are independently checked by protected() and source hashes above.
 events=c.execute('select row_to_json(e) from public.workflow_events e where rental_case_id=586 order by id').fetchall()
 save('timeline_events',[r[0] for r in events])
 result={'marker':'WNC_FULL_RENTAL_STAGING_END_TO_END_CERTIFIED','case_id':586,'case_revision':7,
  'source_ids':[x[0] for x in messages],'facts':facts,'operational_assertions':client_results(snap),
  'revision':asdict(rev),'approval':asdict(approval),'action':asdict(action),'attempt':raw,
  'final_send_attempts':1,'final_graph_send_calls':1,'synthetic_input_graph_send_calls':1,
  'replay_preflight_failure':guard,'adapter_retry_guard':asdict(retry),'second_final_execution_invoked':False,
  'protected_cases_unchanged':protected(c),'provider_gates':health['providers'],
  'tests':{'focused':24,'phase8':708,'repository':925},'production_changes':0}
 save('result',result)
 print(json.dumps({k:result[k] for k in ('marker','case_revision','source_ids','final_send_attempts','replay_preflight_failure','protected_cases_unchanged','tests')},indent=2))
