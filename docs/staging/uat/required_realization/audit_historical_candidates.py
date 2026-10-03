"""Provider-free check of saved prior outputs; never rerun their generations."""
from pathlib import Path
import json,sys
root=Path(__file__).resolve().parents[4];sys.path.insert(0,str(root))
from tools.phase_08_workflow.editorial_content_planner import EditorialContentItem,EditorialContentPlan,EditorialRole
from tools.phase_08_workflow.required_realization import validate_required_realization
p=root/'docs/staging/uat/final_drafting_closure';a=json.loads((p/'acceptance_planner_audit.json').read_text());r=json.loads((p/'acceptance_results.json').read_text());rows=[]
for c in r['results']:
 for t in c['turns']:
  x=next(x for x in a if x['rental_case_id']==c['rental_case_id'] and x['client_generation_payload']['latest_client_message']==t['incoming_message']['body'])
  plan=x['editorial_content_plan'];items=[]
  for role in EditorialRole:
   for v in plan[role.value.lower()]:items.append(EditorialContentItem(**{k:v[k] for k in EditorialContentItem.__dataclass_fields__}))
  plan=EditorialContentPlan(plan['response_intent'],tuple(plan['primary_client_need']),tuple(items),plan['substantive_budget'],plan['editorial_rationale'])
  checks=validate_required_realization(plan,t['draft']['draft_revision']['body_text'])
  rows.append({'turn':f"{c['scenario_id']}/{t['turn_number']}",'unmet':[v['semantic_key'] for v in checks if not v['realized']],'results':checks})
Path(__file__).with_name('historical_candidate_gate_audit.json').write_text(json.dumps(rows,indent=2)+'\n')
print([(r['turn'],r['unmet']) for r in rows if r['unmet']])
