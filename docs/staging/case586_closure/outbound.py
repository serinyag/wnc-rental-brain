"""Exact synthetic approval and one final send; no execution retry path."""
from journey import *
from tools.phase_08_workflow.outlook_action_contract import validate_outlook_action
from tools.phase_08_workflow.governed_client_response import ClientResponseDraft,validate_client_response_draft
from tools.phase_08_workflow.outlook_inbound_service import connection_runner
from unittest.mock import patch
mode=sys.argv[1]
if mode=='generate':
 try:
  r=call('final_draft_generation_aligned','/api/operator/cases/586/mailbox/generate')
  assert r['ok'],r.get('report')
 except Exception as e:
  save('generation_aligned_error',getattr(e,'error_payload',{'error':str(e)}));raise
elif mode=='inspect':
 with connect() as c:
  c.execute('set transaction read only');s=service(c);snap=s._require_case_snapshot(586)
  current=[r for r in s._list_draft_revisions(586) if r.is_current];assert len(current)==1
  rev=current[0];action=snap.find_workflow_action(rev.workflow_action_id);value=validate_outlook_action(action)
  assert rev.recipient_email.casefold()=='serinya@whennaturecalls.nl' and snap.rental_case.case_revision==7
  with patch('tools.phase_05_search.search_hybrid.run_supabase_query',connection_runner(c)),patch('urllib.request.urlopen',side_effect=AssertionError('No provider in inspection')):
   _,_,contract=s._build_current_governed_draft_contract(586)
  assert contract.context_hash==value.governed_context_hash
  validation=validate_client_response_draft(contract=contract,draft=ClientResponseDraft(rev.subject,rev.body_text),
    current_case_revision=7,current_context_hash=contract.context_hash)
  assert validation.is_valid,validation
  approval=snap.find_approval_request(rev.approval_request_id)
  assert approval.target_entity_reference==f'workflow_action:{action.workflow_action_id}:draft_revision:{rev.inquiry_response_draft_revision_id}'
  assert not any(a.workflow_action_id==action.workflow_action_id for a in snap.execution_attempts)
  save('final_candidate',{'revision':asdict(rev),'action':asdict(action),'approval':asdict(approval),
   'contract':value.to_payload(),'validation':asdict(validation),'protected':protected(c)})
  print(json.dumps({'revision_id':rev.inquiry_response_draft_revision_id,'action_id':action.workflow_action_id,
    'approval_id':approval.approval_request_id,'subject':rev.subject,'body':rev.body_text,'validation':'PASS'},indent=2))
elif mode=='approve':
 x=json.loads((OUT/'final_candidate.json').read_text());aid=x['approval']['approval_request_id']
 r=call('final_approval',f'/api/operator/cases/586/approvals/{aid}/approve');assert r['ok']
elif mode=='send':
 x=json.loads((OUT/'final_candidate.json').read_text());aid=x['action']['workflow_action_id']
 health=client().get_health();assert health['providers']['outlook']=='configured' and health['environment']=='staging'
 readiness=client().request('GET',f'/api/operator/cases/586/actions/{aid}/outlook-send-readiness')
 save('send_readiness',readiness);assert readiness['ok'],readiness
 with connect() as c:
  c.execute('set transaction read only');s=service(c);snap=s._require_case_snapshot(586)
  assert not any(t.workflow_action_id==aid for t in snap.execution_attempts)
  revision=s._load_draft_revision_by_id(586,x['revision']['inquiry_response_draft_revision_id'])
  assert revision.is_current and revision.draft_status=='approved' and revision.content_hash==x['revision']['content_hash']
  protected(c)
 try:
  r=call('final_send',f'/api/operator/cases/586/actions/{aid}/execute',{'execution_mode':'real'})
 except Exception as e:
  save('final_send_transport_error',{'error':str(e),'retry':False});raise
 finally:
  print('Final send invocation finished. Disable send gate; never retry.')
