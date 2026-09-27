"""Build the final report from immutable output evidence and direct editorial reviews."""
import json,sys
from pathlib import Path
p=Path(__file__).resolve().parent
load=lambda name:json.loads((p/name).read_text())
slug=sys.argv[1];status=load('program_status.json');data=load(f'{slug}_results.json');assessment=load(f'{slug}_assessment.json')
old=json.loads((p.parent/'autonomous_remediation/cycle3_results.json').read_text())
lines=['# Final Editorial Refinement','','**Two cycles completed: safety and coverage pass; the editorial target remains unmet.** Final grades are 14 A, 7 B, 0 C and 0 D. All 21 drafts persisted, with one recovered by a provider-free read after a result-fetch timeout. All seven multi-turn scenarios preserve continuity. Sending remains disabled. Work stops at the authorized two-cycle limit.','','This is a bounded refinement of the existing single-drafter architecture. No model, authority, commercial rule, approval architecture or provider-send setting changed. Scores and human-likeness reviews are direct assistant assessments of exact outputs, not an external LLM judge or independent human study.','','## Cycles','']
for cycle in status['cycles']:
 lines += [f"### Cycle {cycle['number']}",'',cycle['diagnosis'],'',cycle['changes'],'',f"Commit: `{cycle['commit']}`. Deployment: `{cycle['deploy_id']}`.",'','Tests: `'+json.dumps(cycle['tests'])+'`.','']
lines+=['## Metrics','','Historical starting point: 19/21 accepted drafts; A/B/C/D 10/9/0/0; tone, naturalness and confidence 4.53/5. Those prior grades are preserved and are not silently reinterpreted as meeting the stricter editorial bar.','']
bm=load('baseline_assessment.json')['metrics'];fm=assessment['metrics']
lines += ['The fresh baseline and final run below use the same frozen scenarios and the additional editorial review. Historical numeric scores above remain a separate comparison.','','| Metric | Fresh baseline | Final |','|---|---:|---:|',f"| Persisted drafts | {bm['accepted_drafts']}/21 | {fm['accepted_drafts']}/21 |",'| A / B / C / D | 5 / 16 / 0 / 0 | 14 / 7 / 0 / 0 |']
for key,label in [('factual_grounding','Factual grounding'),('wnc_tone','WNC tone'),('naturalness','Naturalness'),('concision','Concision'),('operator_confidence','Operator confidence')]:
 lines += [f"| {label} / 5 | {bm['mean_scores'][key]} | {fm['mean_scores'][key]} |"]
lines += [f"| Mean body words | {bm['mean_body_words']} | {fm['mean_body_words']} |",f"| Unnecessary information flags | {bm['human_likeness_flags']['unnecessary_information']} | {fm['human_likeness_flags']['unnecessary_information']} |",f"| Unnecessary repetition flags | {bm['human_likeness_flags']['repeated_information']} | {fm['human_likeness_flags']['repeated_information']} |",'',f"Mean body length fell approximately {100*(1-fm['mean_body_words']/bm['mean_body_words']):.1f}%. The final tone score of 4.29 remains below the previously published 4.53. Shorter prose alone does not establish a natural human voice.",'','Final direct harness capture was 20/21 (95.24%); persisted coverage is 21/21 after independently recovering the already-generated UAT-006 turn 2 draft. No generation retry was used.','']
for run in ['baseline','cycle1','cycle2']:
 if (p/f'{run}_assessment.json').exists():
  a=load(f'{run}_assessment.json');lines += [f'### {run}','','```json',json.dumps(a['metrics'],indent=2),'```','']
lines+=['### Final targets','','```json',json.dumps(status['final_targets'],indent=2),'```','','## Every Final Draft','','All subjects and bodies below are verbatim. None was approved or sent. “A” evaluates the prose, not execution authorization.']
for case in data['results']:
 for turn in case['turns']:
  lines+=['',f"### {case['scenario_id']} / Turn {turn['turn_number']}: {case['title']}"]
  r=turn.get('draft',{}).get('draft_revision')
  if not r:
   lines += ['', 'No accepted draft: '+turn.get('failure','Generation not completed.')];continue
  if turn.get('capture_recovery'):
   lines += ['', '**Capture note:** The post-generation GET timed out. This exact persisted revision was recovered by a provider-free read and matched to the incoming client message and completed generation event. The original timeout remains in the result artifact; no draft was regenerated.','','Recovery provenance: `'+json.dumps(turn['capture_recovery'])+'`.']
  a=next(x for x in assessment['assessments'] if x['scenario_id']==case['scenario_id'] and x['turn']==turn['turn_number'])
  lines += ['', '**Subject**','','```text',r['subject'],'```','','**Body**','','```text',r['body_text'],'```','','Grade: **'+a['grade']+'**. '+a['reason'],'','Scores: `'+json.dumps(a['scores'])+'`.','',f"Body words: {a['body_word_count']}. Safety flags: {a.get('safety_flags') or 'none'}."]
lines+=['','## Human-Likeness Review','','Independent editorial questions: would an operator type this; is a sentence present merely because a fact is known; is information premature; does it sound like policy copy; does it repeat earlier information; could it be 20–30% shorter; is it specific to this message? “Repeated” means unnecessary repetition, not a needed correction or answer to a repeated question.','','| Draft | Operator feel | Unnecessary info | Repeated info | Policy-copy feel | Materially shorter | Message-specific |','|---|---|---|---|---|---|---|']
for a in assessment['assessments']:
 h=a['human_review'];yn=lambda key:'yes' if h[key] else 'no'
 lines += [f"| {a['scenario_id']}/{a['turn']} | {h['human_operator_feel']} | {yn('unnecessary_information')} | {yn('repeated_information')} | {yn('policy_copy_feel')} | {yn('could_be_materially_shorter')} | {h['message_specific']} |"]
lines+=['','### Suite-level phrase variation','','Counts identify repetition for review; necessary prospective checks are not automatically defects. No cross-case prompt state or forced phrase rotation was introduced.','','```json',json.dumps(assessment['variation'],indent=2,ensure_ascii=False),'```','','## Before / After','','Every turn is included so materially changed drafts cannot be cherry-picked. OLD is the previous autonomous program’s final output, the primary evaluation source. FINAL is this pass’s last run.']
for case in data['results']:
 before=next(s for s in old['results'] if s['scenario_id']==case['scenario_id'])
 for turn in case['turns']:
  prior=next(t for t in before['turns'] if t['turn_number']==turn['turn_number']);r=turn.get('draft',{}).get('draft_revision');br=prior.get('draft',{}).get('draft_revision')
  lines += ['',f"### {case['scenario_id']} / Turn {turn['turn_number']}"]
  for label,draft in [('OLD',br),('FINAL',r)]:
   lines += ['',label+':']
   if draft:lines+=['','```text',draft['subject'],'',draft['body_text'],'```']
   else:lines+=['','No accepted draft in this run.']
  if r:
   a=next(x for x in assessment['assessments'] if x['scenario_id']==case['scenario_id'] and x['turn']==turn['turn_number']);lines+=['','Editorial assessment: '+a['reason']]
lines+=['','## Coverage Defects','']
for finding in status['coverage_findings']:lines += [finding,'']
replay=load('availability_false_positive_replay.json')
lines += ['### Exact historical UAT-003 candidate replay','','This was a rejected candidate, not a historical accepted draft. It now passes the narrow provider-free validator regression; that does not approve or execute its historical action.','','```text',replay['subject'],'',replay['body'],'```','','Original failure: `unsupported_availability_or_confirmation`. Current failure codes: none.','']
lines+=['## Tests','','Cycle 2: **67 focused tests plus 13 subtests; 603 full-suite tests plus 160 subtests; zero failures.** The full suite includes 386 Phase 8 tests. Cycle 1 counts are recorded above. JUnit XML is retained in this directory. Tests include prospective wording versus actual confirmations, editorial-history authority isolation, revision-history stability, guidance retention and malformed-response diagnostics.','','## Deployment','','```json',json.dumps(status['cycles'],indent=2),'```','','## Safety','','```json',json.dumps(status['safety'],indent=2),'```','','## Remaining Demonstrated Issues','']
for issue in status['remaining_issues']:lines += [issue,'']
lines+=['## Evidence','','Frozen scenarios and original evaluation artifacts are unchanged. Per-run JSON retains every accepted draft, current governed context, exact bindings, request logs and failure diagnostics. Quality grades are subjective; the human-likeness review applies the new editorial bar independently of earlier numeric scores. Rejected text is preserved separately where available.','','The raw final capture is retained in `cycle2_results_raw.json`; recovered results and their provenance are in `cycle2_results.json` and `cycle2_capture_recovery_508.json`. Provider-free canonical validation covers all 21 captured revisions; the final-state audit covers all 13 current case revisions. Neither check performs approval or execution.','','## Final Marker','',status['final_marker']]
(p/'FINAL_EDITORIAL_REFINEMENT.md').write_text('\n'.join(lines)+'\n')
print(p/'FINAL_EDITORIAL_REFINEMENT.md')
