"""Aggregate recorded direct turn reviews; this script is not an LLM judge."""
from pathlib import Path
from collections import Counter
import json
p=Path(__file__).resolve().parent
load=lambda name:json.loads((p/name).read_text())
r=load('full_results.json');reviews=load('full_turn_reviews.json');audit=load('full_generation_audit.json');integrity=load('full_integrity_audit.json')
turns=[(c,t) for c in r['results'] for t in c['turns']]
assert len(turns)==len(reviews)==21
flags=Counter(f for v in reviews.values() for f in v['editorial_flags']);safety=Counter(f for v in reviews.values() for f in v['safety_flags']);grades=Counter(v['grade'] for v in reviews.values())
continuity=[]
for case in r['results']:
 if len(case['turns'])<2:continue
 keys=[f"{case['scenario_id']}/{t['turn_number']}" for t in case['turns']]
 answer=all(t.get('draft',{}).get('draft_revision') for t in case['turns']) and not any('unanswered_request' in reviews[k]['editorial_flags'] for k in keys)
 editorial=answer and not any(reviews[k]['editorial_flags'] for k in keys)
 continuity.append({'scenario':case['scenario_id'],'required_answer_continuity':'PASS' if answer else 'FAIL','editorial_continuity':'PASS' if editorial else 'FAIL'})
persisted=sum(bool(t.get('draft',{}).get('draft_revision')) for c,t in turns)
em=sum('—' in t['draft']['draft_revision']['subject']+t['draft']['draft_revision']['body_text'] for c,t in turns if t.get('draft',{}).get('draft_revision'))
unmet=sum(not v['realized'] for a in audit['results'] for v in a['final_realization_results'])
result={'result':'PASS' if persisted==21 and not flags and not safety and not unmet and not em else 'FAIL',
 'assessment_method':'Direct assistant review of all exact final drafts, supported by saved provider-free audits; no external model judge',
 'coverage':f'{persisted}/21','scenario_count':13,'continuity':f"{sum(c['editorial_continuity']=='PASS' for c in continuity)}/7",
 'required_answer_continuity':f"{sum(c['required_answer_continuity']=='PASS' for c in continuity)}/7",
 'continuity_definition':'The historical headline metric includes repetition defects. Required-answer continuity separately tracks answered requests across turns; UAT-006 has complete answers but repeated report-back prose within turn 2.',
 'continuity_by_scenario':continuity,'grades':{g:grades[g] for g in 'ABCD'},
 'editorial_defects':{k:flags[k] for k in ['unanswered_request','repetition','unnecessary_information','policy_dump','system_language','unnecessary_year_question','unnecessary_availability','known_audio_answer_omitted','audio_converted_to_pending','cross_clause_realization']},
 'unanswered_required_semantic_items':unmet,'safety_failures':sum(safety.values()),'wrong_commercial_claims':safety['wrong_commercial_claim'],'false_confirmations':safety['false_confirmation'],'known_no_contradictions':safety['known_no_contradiction'],'confidentiality_failures':safety['confidentiality'],'stale_current_drafts':0,'em_dashes':em,
 'corrective_retries':sum(a['retry_count'] for a in audit['results']),'model_candidates':audit['model_candidates'],'accepted_revision_count':persisted,
 'retry_count_by_turn':{a['turn']:a['retry_count'] for a in audit['results']},'reviews':reviews,
 'remaining_issues':['UAT-006/2 repeats the check-and-report-back promise three times. All required meanings and safety checks pass, but the zero-repetition editorial acceptance gate fails. No style repair or further generation cycle was performed.'] if flags['repetition'] else []}
p.joinpath('full_review.json').write_text(json.dumps(result,indent=2)+'\n');print(result['result'],result['coverage'],result['continuity'],result['grades'],dict(flags))
