import json,sys
from pathlib import Path
from types import SimpleNamespace
root=Path('/Users/serinya/Documents/WNC Rental Automation');sys.path.insert(0,str(root))
from tools.phase_08_workflow.outlook_action_contract import validate_outlook_action
p=root/'docs/staging/uat/required_realization';slug=sys.argv[1];data=json.loads((p/f'{slug}_results.json').read_text());checked=[]
for case in data['results']:
 for turn in case['turns']:
  draft=turn.get('draft',{});r=draft.get('draft_revision')
  if not r:continue
  action=SimpleNamespace(**draft['workflow_action']);contract=validate_outlook_action(action);approval=draft['approval_request']
  assert contract.draft_revision_id==r['inquiry_response_draft_revision_id']
  assert contract.draft_origin_workflow_action_id==r['workflow_action_id']==action.workflow_action_id
  assert contract.draft_content_hash==r['content_hash']
  assert contract.context_hash==r['context_hash']
  assert contract.subject==r['subject'] and contract.body==r['body_text']
  assert contract.recipient_email==r['recipient_email']
  assert approval['target_entity_reference']==contract.approval_target
  assert approval['status']=='open' and action.status=='awaiting_approval'
  checked.append({'scenario_id':case['scenario_id'],'turn':turn['turn_number'],'draft_revision_id':contract.draft_revision_id,'action_id':action.workflow_action_id,'canonical_payload':'PASS','revision_content_context_recipient_approval_binding':'PASS','approval_status':'open','message_mode':contract.message_mode})
(p/f'{slug}_captured_contract_validation.json').write_text(json.dumps({'provider_calls':0,'results':checked},indent=2)+'\n');print(len(checked),'captured canonical contracts validated provider-free.')
