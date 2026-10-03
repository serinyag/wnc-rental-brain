"""Report the single frozen UAT-006 run; no provider or network access."""
import json
from pathlib import Path
p=Path(__file__).resolve().parent
load=lambda n:json.loads((p/n).read_text())
r=load('targeted_results.json');g=load('targeted_generation_audit.json');s=load('targeted_final_snapshots.json');a=load('targeted_planner_audit.json')
assert len(r['results'])==1 and r['results'][0]['scenario_id']=='UAT-006'
case=r['results'][0];assert len(case['turns'])==2 and not case['failures']
assert len(g['results'])==2 and all(t['persisted'] for t in g['results'])
assert sum(x['path'].endswith('/generate') for x in r['request_log'])==2
assert not any('/approve' in x['path'] or '/execute' in x['path'] for x in r['request_log'])
c=s['cases'][0]['snapshot']['case'];o=c['orchestration_snapshot']
assert not o['execution_attempts'] and all(x['status']!='approved' for x in o['approval_requests'])
expected={t['draft']['draft_revision']['inquiry_response_draft_revision_id'] for t in case['turns']}
actual={d['inquiry_response_draft_revision_id'] for t in c['simulated_outlook_threads'] for d in t['draft_history']}
assert actual==expected=={384,385}
second=next(x for x in a if x.get('draft_revision_id')==385)
assert len(second['client_generation_payload']['must_say'])==1
checks=second['generation_audit']['final_realization_results']
assert len(checks)==3 and all(x['realized'] for x in checks)
body=case['turns'][1]['draft']['draft_revision']['body_text']
assert body.count('I’ll check')==1 and body.count('report back')==1
assert '30' in body and 'entire venue' in body and 'reschedule request' in body
assert '—' not in ''.join(t['draft']['draft_revision']['body_text'] for t in case['turns'])
review={'result':'PASS','assessment_method':'Direct assistant review of exact two drafts and provider-free audits; no model judge',
 'case_id':583,'draft_revisions':[384,385],'original_change_requirements':checks,
 'guest_count_change_realized':True,'full_venue_change_realized':True,'reschedule_realized':True,
 'consolidated_check_statement_count':1,'report_back_promise_count':1,'repetition_flag':0,
 'unnecessary_information':0,'unanswered_request':0,'false_confirmation':0,'safety_failures':0,'em_dash':0,'year_questions':0,
 'timing_note':'The draft acknowledges the reschedule request without restating 13 November, 15:00–20:00. No exact prose or date/time recap is required.',
 'generation_operations':2,'model_candidates':g['model_candidates'],'corrective_retries':[x['retry_count'] for x in g['results']],
 'accepted_revision_cardinality':'PASS'}
(p/'targeted_review.json').write_text(json.dumps(review,indent=2)+'\n')
safety={'Graph mutations':0,'Outlook sends':0,'actions approved':0,'ExecutionAttempts':0,'real Asana':0,'production':0,'send_gate':'DISABLED',
 'evidence':'Guarded staging-only request log, two persisted generations, zero execution attempts, no approval/execution routes, health provider postures; no independent provider-account telemetry queried.'}
status={'final_marker':'WNC_GOVERNED_DRAFTING_STAGING_ACCEPTED','deployment':load('deployment.json'),'tests':load('test_summary.json'),'targeted':review,'safety':safety,'health':s['health'],'stopped':True}
(p/'program_status.json').write_text(json.dumps(status,indent=2)+'\n')
text='''# Pending Check Consolidation

The writing payload repeated a check/report-back action for each selected requested change. The new deterministic post-plan projection emits one `pending_action_group` with all three subjects and one report-back instruction. It does not change Editorial Content Planner v3 selection or truth.

Grouping is restricted to recognized WNC-owned pending changes represented in the current message, or compatible current supplier-logistics checks. Facts, restrictions, questions, commercial decisions, external ownership and historical/unmentioned checks remain outside these groups. Unknown shapes stay separate. One narrow composition instruction requests one check and report-back promise; no sentence template or banned-phrase list was added.

# Realization Preservation

The original guest-count, rental-scope and reschedule items retain their semantic keys, values and fingerprints. The gate still evaluates each original item independently. Its existing generic requested-change witness was narrowed for these three recognized kinds so one missing subject fails only its original requirement. One sentence may satisfy all three; a vague “updated request” alone cannot.

The planner, date normalization, safety validator, one-retry control flow, provider/model, retrieval and Outlook approval/execution contract remain unchanged. Composition version is included in context identity. Tests demonstrate that a safe omission still receives exactly one correction under the same contract.

# Provider-Free Tests

All 12 requested proof categories pass, including frozen UAT-006/2 projection, independent omission failures, supplier logistics, material distinctions and unchanged bounded corrective retry. All frozen planner/date/prior evidence hashes pass. Captured canonical action/revision/content/context/recipient/approval bindings pass for both drafts. Exactly two accepted revisions exist; no extra candidate revision was persisted.

# UAT-006 Targeted Acceptance

Only frozen UAT-006 was run once (two turns), using the accepted application date-normalization adapter. Case 583; revisions 384 and 385. Both persisted on the initial candidate: two generation operations, two model candidates, zero corrective retries. No full 21-turn model suite was rerun.

'''
for t in case['turns']:
 d=t['draft']['draft_revision'];text+=f"## Turn {t['turn_number']} — exact draft\n\nSubject: {d['subject']}\n\n```text\n{d['body_text']}\n```\n\n"
text+='''## Turn 2 assessment

| Gate | Result |
|---|---|
| Guest-count change realized | Yes (30 acknowledged) |
| Full-venue change realized | Yes |
| Reschedule realized | Yes, prospective reschedule request |
| Consolidated check statements | 1 |
| Report-back promises | 1 |
| Repetition flag | 0 |
| Unnecessary information / unanswered request | 0 / 0 |
| False confirmation / safety failures | 0 / 0 |
| Em dashes / unnecessary year questions | 0 / 0 |

The changed timing is acknowledged as the “reschedule request”; the draft does not restate the exact date and hours. All three original semantic requirements independently returned `realized=true`. Turn 1 retains its working availability-check behavior. This assessment is direct review of this sample plus deterministic evidence, with no additional model judge.

# Tests

| Suite | Passed | Subtests passed | Failures | Skips |
|---|---:|---:|---:|---:|
| Focused grouping, realization/retry, planner and date | 130 | 0 | 0 | 0 |
| Full Phase 8 | 550 | 126 | 0 | 0 |
| Full repository | 767 | 160 | 0 | 0 |

`git diff --check`: PASS. Initial full-suite database discovery selected another local Docker container; a test-process-only WNC database binding corrected this. No staging environment settings changed. Full suite retains 39 collection warnings from existing service/helper class names.

# Deployment

Implementation commit: `7ef15d28bcad6bd8991510e6315ea1d32e12f54b`, pushed to main.

Render deploy: `dep-db0eg660tbcc73ffrrpg`, live. Health: staging / ok. Outlook: `configured_draft_only`; send gate: disabled. Asana: `configured_but_disabled`.

# Safety

| Activity | Count |
|---|---:|
| Graph mutations | 0 |
| Outlook sends | 0 |
| Actions approved | 0 |
| ExecutionAttempts created | 0 |
| Real Asana executions | 0 |
| Production activity | 0 |

Evidence: guarded staging request log, canonical bindings, zero saved execution attempts, unapproved drafts, and provider health posture. No independent provider-account telemetry was queried. No provider execution, gate change or historical recovery approval was performed.

# Final Marker

**WNC_GOVERNED_DRAFTING_STAGING_ACCEPTED**

Stopped after the targeted acceptance. Outlook sending remains disabled.
'''
(p/'PENDING_CHECK_CONSOLIDATION_REPORT.md').write_text(text)
print(status['final_marker'])
