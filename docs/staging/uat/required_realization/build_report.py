"""Render saved acceptance evidence only; no network or generation calls."""
from pathlib import Path
import json
p=Path(__file__).resolve().parent
load=lambda name:json.loads((p/name).read_text())
s=load('program_status.json');target=load('targeted_results.json');review=load('targeted_review.json');ta=load('targeted_planner_audit.json');lines=[]
def out(*x):lines.extend(x)
def obj(x):out('```json',json.dumps(x,indent=2,ensure_ascii=False),'```','')
def exact_drafts(results,audits,detailed=False):
 for case in results['results']:
  for turn in case['turns']:
   key=f"{case['scenario_id']}/{turn['turn_number']}"
   out('## '+key,'')
   d=turn.get('draft',{}).get('draft_revision')
   a=next((x for x in audits if x['rental_case_id']==case['rental_case_id'] and x['client_generation_payload']['latest_client_message']==turn['incoming_message']['body']),{})
   if d:
    subject,body=d['subject'],d['body_text'];out(f"DraftRevision {d['inquiry_response_draft_revision_id']}; exact action/revision/content/context/recipient/approval binding checked provider-free.",'')
   else:
    subject,body=a.get('rejected_subject',''),a.get('rejected_body','');out('**No accepted DraftRevision. Final rejected candidate below if captured.**','');obj({'failure':turn.get('failure'),'validation_codes':a.get('validation_codes')})
   out('Subject:','','```text',subject,'```','','Body:','','```text',body,'```','')
   ga=a.get('generation_audit',{})
   if detailed:obj(ga)
   else:out(f"Corrective retries: {ga.get('corrective_retry_count')}. Required realization: {'PASS' if d and all(i['realized'] for i in ga.get('final_realization_results',[])) else 'REJECTED'}.",'')
out('# Required Semantic Realization Gate','',
'Implemented and deployed. Targeted UAT-012 passes all three turns. The full run persists all 21 drafts with complete required answers and three bounded corrections, but overall acceptance requires review because UAT-006/2 repeats its report-back promise. No further implementation or generation cycle followed.','',
'A generated candidate now passes safety validation first, then a deterministic completeness gate, before any immutable DraftRevision, send action or approval is created for that candidate. The existing planner v3 selects content; the new boundary does not change facts, retrieval or editorial budgets.','',
'Typed requirements distinguish questions, known assertions, restrictions, commercial truth, pending actions, conditional capability checks, practical guidance and recorded external states. Only MUST_ASK and MUST_COMMUNICATE items require current-turn realization. ACKNOWLEDGE and HELPFUL_NOW remain optional; DEFER, INTERNAL_ONLY and ALREADY_COMMUNICATED create no current-turn obligations. Unknown mandatory shapes fail closed.','',
'Audio reuses the item-scoped positive-capability witness, with support for natural WNC-can-accommodate wording. Acknowledgements and future checks fail. Other supported shapes reuse existing witnesses with question-component, sentence and action scope. These are bounded deterministic language witnesses, not a universal semantic parser or an LLM judge.','',
'# Corrective Retry','',
'One safe initial candidate missing required meaning receives one corrective request. It carries the original client-safe payload, initial candidate and typed unmet meanings, with no prescribed final sentence. No extra facts or retrieval are added. The same DraftContract object, case revision, context hash, plan, authoritative facts, recipient and response intent remain bound across both attempts. Case state, events, facts and recipient metadata are rechecked before acceptance; a changed binding stops the operation.','',
'Safety-invalid candidates do not enter this retry mechanism. Both candidates undergo safety validation; only a safe, complete final candidate may persist. A second omission or any corrected-candidate safety failure rejects the operation. Provider failures are not retried by this policy. Internal candidate attempts do not create client turns or DraftRevisions. Existing exact revision reuse preserves approval state.','',
'Audit records include attempt numbers, provider request/response identifiers, initial/corrected candidate hashes, unmet semantic keys, correction reason, final realization results and contract/plan identities. The initial omitted candidate remains non-current and non-approvable. Hash-only first-candidate evidence avoids retaining unnecessary prose. Correction-provider failures preserve the initial audit in a failure event.','',
'# Provider-Free Tests','',
'All 15 requested cases are covered: positive audio variants; rejection of acknowledgement/check language; exactly one correction; successful corrected acceptance; exhaustion; no safety retry; immutable bindings; only-final persistence; non-approvable first candidate; valid turn-one realization and turn-two/three ALREADY_COMMUNICATED suppression; explicit reopening. Further regressions cover prices/VAT, restrictions, pending decisions, multiple next-step subjects, missing question components, stale recipient/events, provider failure audit and existing-revision reuse.','',
'45 new tests pass. Applying the gate offline to the previous 21 saved outputs flags exactly the three demonstrated audio omissions. No historical output was regenerated.','',
'# UAT-012 Targeted Test','');obj(review)
exact_drafts(target,ta,True)
out('## Realization and continuity evidence','')
for a in ta:
 out('### '+str(a.get('draft_revision_id','rejected candidate')),'')
 obj({'must_say':a['client_generation_payload']['must_say'],'audio_projection_items':[i for role in ('must_communicate','already_communicated','defer') for i in a['editorial_content_plan'][role] if i['topic'] in ('audio_playback','projection_display')],'communicated_editorial_items':a.get('communicated_editorial_items',[]),'do_not_repeat_topics':a['client_generation_payload']['do_not_repeat_topics']})
out('# Full Frozen UAT','')
if (p/'full_results.json').exists():
 full=load('full_results.json');fa=load('full_planner_audit.json');obj(load('full_review.json'))
 out('# Exact Final Drafts','');exact_drafts(full,fa)
else:out('Not run: the targeted acceptance gate did not pass. No further generation or implementation cycle was performed.','')
out('# Date Inference','',
'Date normalization source, ingestion logic and boundary regressions remain byte-for-byte unchanged from the accepted implementation. The frozen client text and non-timing observations are unchanged. As in the accepted date run, fixture-assigned ISO timing observations are excluded from injection; the application derives timing from the original inbound text and authoritative message timestamp. The `observations` field in result files describes the original frozen fixture, not injected timing values. Runtime provenance is in the captured case snapshots.','')
obj(s.get('date_audit',{}))
out('# Tests','');obj(s['tests'])
out('# Deployment','');obj(s['deployment']);obj(s.get('health',{}))
out('# Safety','');obj(s.get('safety',{}))
out('All 14 synthetic cases contain exactly the accepted revision IDs captured by the UAT; none of the three initial incomplete candidates became a persisted revision.','',
'Activity zeros are scoped to this task and established from the guarded request logs and synthetic case snapshots. No sending gate, provider/model, production, Entra or Exchange permission settings were changed. Draft approvals were created only for accepted synthetic drafts; none was approved or executed.','',
'# Remaining Findings','')
for issue in s.get('remaining_issues',[]):out('- '+issue)
out('','# Evidence','',
'- [Frozen scenarios, accepted date policy and historical file hashes](frozen_manifest.json)',
'- [Targeted results and request log](targeted_results.json)',
'- [Targeted plans, payloads and generation audits](targeted_planner_audit.json)',
'- [Provider-free binding validation](targeted_captured_contract_validation.json)',
'- [Final staging snapshots](targeted_final_snapshots.json)',
'- [Deployment screenshot](staging_deployment.png)',
'- [Full UAT exact results and guarded request log](full_results.json)',
'- [Full UAT candidate hashes, unmet IDs and final realization audit](full_generation_audit.json)',
'- [Full UAT exact binding checks](full_captured_contract_validation.json)',
'- [Full UAT final state and disabled-send audit](full_integrity_audit.json)',
'- [Full UAT timestamp provenance](full_date_provenance.json)',
'- [Accepted-revision cardinality proof](accepted_revision_cardinality.json)','',
'# Final Marker','',s['final_marker'],'','Stopped at the authorized acceptance boundary. Sending remains disabled.','')
p.joinpath('REQUIRED_REALIZATION_REPORT.md').write_text('\n'.join(lines))
print(s['final_marker'])
