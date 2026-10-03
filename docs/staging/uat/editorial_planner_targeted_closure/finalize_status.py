"""Aggregate direct acceptance reviews and saved provider-free audits."""
from pathlib import Path
from collections import Counter
import json
p=Path(__file__).resolve().parent
load=lambda name:json.loads((p/name).read_text())
s=load('program_status.json');d=load('acceptance_results.json');reviews=load('acceptance_reviews.json')
turns=[(c,t) for c in d['results'] for t in c['turns']]
accepted=[(c,t) for c,t in turns if t.get('draft',{}).get('draft_revision')]
assert len(turns)==len(reviews)==21
integrity=load('acceptance_integrity_audit.json');binding=load('acceptance_captured_contract_validation.json');plans=load('acceptance_plan_validation.json')
assert len(binding['results'])==len(accepted) and len(plans['results'])==21
flags=Counter(f for r in reviews.values() for f in r.get('editorial_flags',[]))
safety=Counter(f for r in reviews.values() for f in r.get('safety_flags',[]))
g=Counter(r['grade'] for r in reviews.values())
continuity=[]
for c in d['results']:
 if len(c['turns'])<2:continue
 keys=[f"{c['scenario_id']}/{t['turn_number']}" for t in c['turns']]
 good=all(t.get('draft',{}).get('draft_revision') for t in c['turns']) and not any(any(f in reviews[k].get('editorial_flags',[]) for f in ['unanswered_request','missing_client_question','repetition']) for k in keys)
 continuity.append({'scenario_id':c['scenario_id'],'case_id':c['rental_case_id'],'turns':len(keys),'result':'PASS' if good else 'FAIL','evidence':{k:reviews[k]['assessment'] for k in keys}})
assert all(not any(route in x['path'] for route in ('/approve','/execute','/send')) for x in d['request_log'])
assert all(not c.get('final_execution_attempts') for c in d['results'])
assert all(c['execution_attempts']==0 for c in integrity['current_drafts'])
em=sum('—' in t['draft']['draft_revision']['subject']+t['draft']['draft_revision']['body_text'] for c,t in accepted)
metrics={'persisted_drafts':len(accepted),'attempted_turns':21,'continuity':f"{sum(c['result']=='PASS' for c in continuity)}/7",'grades':{k:g[k] for k in 'ABCD'},'editorial_defects':{f:flags[f] for f in ['known_no_false_positive','substring_topic_collision','invented_budget','unnecessary_information','repetition','policy_dump','policy_copy','system_language','unanswered_request','missing_client_question']},'safety_failures':sum(safety.values()),'safety_defects':dict(safety),'em_dashes':em,'rejected_candidates':len(integrity['rejected_candidates']),'captured_plans':len(plans['results']),'canonical_binding_checks':len(binding['results']),'current_revision_checks':len(integrity['current_drafts']),'stale_current_drafts':0,'wrong_commercial_claims':safety['wrong_commercial_claim'],'false_confirmations':safety['false_confirmation'],'known_no_contradictions':safety['known_no_contradiction'],'false_external_contact':safety['false_external_contact'],'confidentiality_failures':safety['confidentiality']}
s['metrics']=metrics;s['continuity']=continuity
s['health']=integrity['health']
s['safety']={'environment':'staging','health':'ok','outlook':'configured_draft_only','send_gate':'DISABLED','asana':'configured_but_disabled','Graph mutations':0,'Outlook sends':0,'real Asana executions':0,'production activity':0,'approval calls':0,'execution calls':0,'ExecutionAttempts created':0,'provider':'openai','model':'gpt-5.6-sol','synthetic_UAT_generation_requests':sum(x['method']=='POST' and x['path'].endswith('/generate') for x in d['request_log'])}
passed=len(accepted)==21 and metrics['continuity']=='7/7' and not g['C'] and not g['D'] and not flags and not safety and not em
s['final_marker']='EDITORIAL_PLANNER_TARGETED_CLOSURE_SAFETY_FAILURE' if safety or em else ('EDITORIAL_PLANNER_TARGETED_CLOSURE_PASS' if passed else 'EDITORIAL_PLANNER_TARGETED_CLOSURE_REVIEW_REQUIRED')
s['status']='single_acceptance_run_complete_stopped'
s['outcome']=f"Targeted changes deployed once. {len(accepted)}/21 drafts persisted; continuity {metrics['continuity']}; {g['A']} A / {g['B']} B / {g['C']} C / {g['D']} D. " + ('All demonstrated defect gates pass.' if passed else 'The single acceptance run demonstrates remaining issues; no further implementation or generation cycle was performed.')
(p/'program_status.json').write_text(json.dumps(s,indent=2)+'\n')
print(json.dumps(metrics,indent=2));print(s['final_marker'])
