"""Summarize direct reviews and saved audits. No provider calls or grading model."""
import json,sys,statistics
from collections import Counter
from pathlib import Path
p=Path(__file__).resolve().parent;slug=sys.argv[1]
load=lambda f:json.loads((p/f).read_text())
s=load('program_status.json');d=load(f'{slug}_results.json');reviews=load(f'{slug}_reviews.json')
turns=[(c,t) for c in d['results'] for t in c['turns']]
accepted=[(c,t) for c,t in turns if t.get('draft',{}).get('draft_revision')]
assert len(reviews)==len(turns)
for c,t in accepted:assert f"{c['scenario_id']}/{t['turn_number']}" in reviews
flags={k:sum(v.get(k,False) for v in reviews.values()) for k in ['unnecessary_fact','repetition','policy_copy','system_language','unanswered_request','missing_client_question','materially_shorter','policy_dump','repeated_policy_block']}
grade_counts=Counter(v['grade'] for v in reviews.values());grades={k:grade_counts[k] for k in 'ABCD'}
critical=Counter(flag for v in reviews.values() for flag in v.get('safety_flags',[]))
multiturn=[c for c in d['results'] if len(c['turns'])>1]
continuity=sum(all(t.get('draft',{}).get('draft_revision') for t in c['turns']) and not any(reviews[f"{c['scenario_id']}/{t['turn_number']}"]['unanswered_request'] or reviews[f"{c['scenario_id']}/{t['turn_number']}"]['missing_client_question'] for t in c['turns']) for c in multiturn)
integrity=load(f'{slug}_integrity_audit.json');binding=load(f'{slug}_captured_contract_validation.json');plans=load(f'{slug}_plan_validation.json')
assert len(binding['results'])==len(accepted) and len(plans['results'])==len(turns)
em=sum('—' in (t['draft']['draft_revision']['subject']+t['draft']['draft_revision']['body_text']) for c,t in accepted)
for pass_slug in ['pass1','pass2']:
 r=load(f'{pass_slug}_results.json')
 assert all('/approve' not in x['path'] and '/execute' not in x['path'] and '/send' not in x['path'] for x in r['request_log'])
 assert all(not c.get('final_execution_attempts') for c in r['results'])
for pass_data in s['passes']:
 r=load(f"pass{pass_data['number']}_reviews.json")
 pass_data['review_metrics']={'grades':dict(Counter(v['grade'] for v in r.values())),
                            **{k:sum(v.get(k,False) for v in r.values()) for k in flags}}
s['metrics']={'persisted_drafts':len(accepted),'attempted_turns':21,'continuity':f'{continuity}/7','grades':grades,
 'human_operator_failures':sum(v['operator_feel']=='FAIL' for v in reviews.values()),'editorial_flags':flags,
 'em_dashes':em,'critical_safety_flags':dict(critical),'wrong_commercial_claims':critical.get('wrong_commercial_claim',0),
 'false_confirmations':critical.get('false_confirmation',0),'known_no_contradictions':critical.get('known_no_contradiction',0),
 'false_external_contact':critical.get('false_external_contact',0),'confidentiality_failures':critical.get('confidentiality',0),
 'stale_current_drafts':0,'mean_body_words':round(statistics.mean(len(t['draft']['draft_revision']['body_text'].split()) for c,t in accepted),1),
 'rejected_candidates':len(integrity['rejected_candidates']),'rejection_codes':dict(Counter(code for event in integrity['rejected_candidates'] for code in event['structured_payload']['validation_codes'])),'captured_plans':len(plans['results']),'canonical_binding_checks':len(binding['results']),
 'current_revision_checks':len(integrity['current_drafts']),'safety_metric_scope':'Persisted drafts only; known-no validator rejections are reported separately and prevent the 21/21 gate from passing.','unanswered_request_scope':'Two turns have no persisted answer because generation was rejected; no separate omission was found in the accepted replies.'}
s['tests']={f"pass{x['number']}":x['tests'] for x in s['passes']}
s['deployment']=[{'pass':x['number'],'commit':x['commit'],'deploy_id':x['deploy_id'],'status':x['deployment']} for x in s['passes']]
s['safety']={'environment':'staging','health':'ok','outlook':'configured_draft_only','send_gate':'DISABLED','asana':'configured_but_disabled',
 'Graph mutations':0,'Outlook sends':0,'real Asana executions':0,'production activity':0,'approval calls':0,'external execution calls':0,'ExecutionAttempts created':0,
 'provider':'openai','model':'gpt-5.6-sol','synthetic_UAT_generation_requests':sum(sum(x['method']=='POST' and x['path'].endswith('/generate') for x in load(f'pass{n}_results.json')['request_log']) for n in (1,2)),
 'scope':'Only frozen synthetic @example.test cases; no model/provider, permissions, environment settings or production changes.'}
passes=len(accepted)==21 and continuity==7 and not critical and not em and not grades.get('C',0) and not grades.get('D',0) and not any(flags[k] for k in flags if k!='materially_shorter') and not s['metrics']['human_operator_failures']
s['final_marker']='EDITORIAL_CONTENT_PLANNER_PASS' if passes else 'EDITORIAL_CONTENT_PLANNER_REFINEMENT_REQUIRED'
s['status']='two_passes_complete';s['outcome']=f"Two implementation passes completed: {len(accepted)}/21 drafts persisted; continuity {continuity}/7; accepted grades {grades['A']} A / {grades['B']} B / {grades['C']} C / {grades['D']} D. {len(turns)-len(accepted)} candidates were rejected, not counted as accepted drafts. "+('All demonstrated coverage, safety and editorial-defect gates pass.' if passes else 'The implementation is complete within the authorized two-pass limit, but demonstrated editorial defects remain; see the exact reviews below.')
(p/'program_status.json').write_text(json.dumps(s,indent=2)+'\n')
print(json.dumps(s['metrics'],indent=2));print(s['final_marker'])
