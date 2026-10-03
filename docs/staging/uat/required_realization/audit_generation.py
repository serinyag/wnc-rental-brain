"""Validate persisted generation audit and exact plan witnesses, without providers."""
import json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[4];sys.path.insert(0,str(root))
from tools.phase_08_workflow.editorial_content_planner import EditorialContentItem,EditorialContentPlan,EditorialRole,digest
from tools.phase_08_workflow.required_realization import validate_required_realization
p=Path(__file__).resolve().parent;slug=sys.argv[1]
r=json.loads((p/f'{slug}_results.json').read_text());audits=json.loads((p/f'{slug}_planner_audit.json').read_text());rows=[]
for case in r['results']:
 for turn in case['turns']:
  candidates=[x for x in audits if x['rental_case_id']==case['rental_case_id'] and x['client_generation_payload']['latest_client_message']==turn['incoming_message']['body']]
  assert len(candidates)==1,(case['scenario_id'],turn['turn_number'],len(candidates))
  x=candidates[0];ga=x['generation_audit'];plan=x['editorial_content_plan'];items=[]
  for role in EditorialRole:
   for i in plan[role.value.lower()]:items.append(EditorialContentItem(**{k:i[k] for k in EditorialContentItem.__dataclass_fields__}))
  po=EditorialContentPlan(plan['response_intent'],tuple(plan['primary_client_need']),tuple(items),plan['substantive_budget'],plan['editorial_rationale'])
  assert ga['plan_identity']==digest(plan)
  assert ga['context_hash']==x['context_hash']
  assert 1<=len(ga['attempts'])<=2 and ga['corrective_retry_count']==len(ga['attempts'])-1
  if len(ga['attempts'])==2:
   assert ga['attempts'][0]['safety_failure_codes']==[] and ga['attempts'][0]['failed_realization_item_ids']
  d=turn.get('draft',{}).get('draft_revision')
  if d:
   checks=validate_required_realization(po,d['body_text']);assert {i['semantic_key']:i for i in checks}=={i['semantic_key']:i for i in ga['final_realization_results']}
   assert all(i['realized'] for i in checks)
   assert not ga['attempts'][-1]['safety_failure_codes']
   expected=digest({'subject':d['subject'],'body':d['body_text'],'question_ids':[q['open_question_id'] for q in x['client_generation_payload']['open_client_questions']]})
   assert ga['attempts'][-1]['candidate_hash']==expected
  rows.append({'turn':f"{case['scenario_id']}/{turn['turn_number']}",'persisted':bool(d),'retry_count':ga['corrective_retry_count'],'attempts':ga['attempts'],'plan_identity':'PASS','final_realization_results':ga['final_realization_results']})
(p/f'{slug}_generation_audit.json').write_text(json.dumps({'provider_calls':0,'results':rows,'generation_operations':len(rows),'model_candidates':sum(len(x['attempts']) for x in rows)},indent=2)+'\n')
print([(x['turn'],x['persisted'],x['retry_count']) for x in rows])
