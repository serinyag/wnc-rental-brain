"""Provider-free verification of captured plan/payload boundaries and exact draft bindings."""
import json,sys,hashlib
from pathlib import Path
p=Path(__file__).resolve().parent
slug=sys.argv[1]
load=lambda f:json.loads((p/f).read_text())
r=load(f'{slug}_results.json');audits=load(f'{slug}_planner_audit.json')
by_revision={a['draft_revision_id']:a for a in audits if a.get('draft_revision_id')}
checked=[]
roles=['acknowledge','must_communicate','must_ask','helpful_now','already_communicated','defer','internal_only']
for case in r['results']:
 for turn in case['turns']:
  revision=turn.get('draft',{}).get('draft_revision')
  a=by_revision[revision['inquiry_response_draft_revision_id']] if revision else next(x for x in audits if x['rental_case_id']==case['rental_case_id'] and x['client_generation_payload']['latest_client_message']==turn['incoming_message']['body'])
  plan=a['editorial_content_plan'];payload=a['client_generation_payload']
  assert a['rental_case_id']==case['rental_case_id']
  assert payload['latest_client_message']==turn['incoming_message']['body']
  if revision:assert a['validation_failure_codes']==[]
  assert a['provider']=='openai' and a['model']=='gpt-5.6-sol'
  if revision:assert revision['recipient_email'].endswith('@example.test')
  mapping={'acknowledge':'acknowledgements','must_communicate':'must_say','must_ask':'open_client_questions','helpful_now':'optional_helpful_now'}
  for role,key in mapping.items():
   expected=[{'topic':i['topic'],**i['value']} for i in plan[role]]
   assert payload[key]==expected,(case['scenario_id'],turn['turn_number'],role)
  assert all(not i['included_in_model_payload'] for role in ['defer','internal_only','already_communicated'] for i in plan[role])
  assert 'prior_client_drafts_for_editorial_continuity_only' not in payload
  assert 'contextual_guidance' not in payload
  for item in plan['must_communicate']:
   if item['prior_turn_status']=='unchanged_answer_in_prior_draft':assert item['reason']=='explicit_current_turn_question_requires_answer_again'
  checked.append({'scenario_id':case['scenario_id'],'turn':turn['turn_number'],'revision_id':revision['inquiry_response_draft_revision_id'] if revision else None,
     'plan_payload_boundary':'PASS','novelty_override':'PASS','validation':'PASS' if revision else 'REJECTED', 'validation_codes':a.get('validation_codes',[]),
     'payload_bytes':len(json.dumps(payload,sort_keys=True).encode()),'candidate_count':sum(len(plan[k]) for k in roles),
     'included_item_count':sum(len(plan[k]) for k in mapping)})
(p/f'{slug}_plan_validation.json').write_text(json.dumps({'provider_calls':0,'results':checked},indent=2)+'\n')
print(len(checked),'plan/payload boundaries validated')
