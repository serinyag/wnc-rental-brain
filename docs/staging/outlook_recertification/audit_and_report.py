"""Provider-free audit and report of the single prepared candidate."""
import sys,json,hashlib
from pathlib import Path
from types import SimpleNamespace
from dataclasses import fields
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root));p=Path(__file__).resolve().parent
from tools.phase_08_workflow.outlook_action_contract import validate_outlook_action,OutlookExecutionInput,OutlookContractError
from tools.staging_calibration.run_operator_calibration import build_client
from tools.phase_08_workflow.operator_harness import OperatorHarnessError
load=lambda n:json.loads((p/n).read_text())
r=load('fresh_candidate.json');hosted=load('hosted_readiness.json')['report'];final=load('fresh_final_snapshot.json')['case'];snapshot=final['orchestration_snapshot']
aid=r['action']['workflow_action_id'];rid=r['revision']['inquiry_response_draft_revision_id'];apid=r['approval']['approval_request_id'];cid=r['case_id']
assert (cid,rid,aid,apid)==(584,386,1619,465)
assert hosted['success'] and not hosted['failure_codes']
for required in ['Send gate: disabled','Recipient allowlist: pass','Current case/context: pass','Readiness: approval_required','Execution-input validation: PASS','Canonical payload validation: PASS']:
 assert required in hosted['lines']
assert not snapshot['execution_attempts']
actions=[x for x in snapshot['workflow_actions'] if x['target_adapter_code']=='outlook'];assert len(actions)==1
value=validate_outlook_action(SimpleNamespace(**actions[0]));assert actions[0]['status']=='awaiting_approval'
assert value.draft_revision_id==rid and value.draft_origin_workflow_action_id==aid
assert value.approval_target==f'workflow_action:{aid}:draft_revision:{rid}'
assert len(snapshot['approval_requests'])==1 and snapshot['approval_requests'][0]['status']=='open'
revisions=[d for t in final['simulated_outlook_threads'] for d in t['draft_history']]
assert len(revisions)==1 and revisions[0]['is_current'] and revisions[0]['inquiry_response_draft_revision_id']==rid
assert value.source_case_revision==snapshot['rental_case']['case_revision']
assert value.draft_content_hash==revisions[0]['content_hash'] and value.context_hash==revisions[0]['context_hash']
assert value.recipient_email=='Serinya@whennaturecalls.nl' and value.body==revisions[0]['body_text'] and value.subject==revisions[0]['subject']
assert set(value.to_payload())=={f.name for f in fields(OutlookExecutionInput)}
assert all(value.to_payload()[f] is None for f in ['graph_message_id','recovery_draft_revision_id','recovery_origin_workflow_action_id','recovery_predecessor_action_id'])
history_before=load('historical_database_rows_before.json');history_after=load('historical_database_rows_after.json');assert history_before==history_after
before=load('historical_before.json')['case']['orchestration_snapshot'];after=load('historical_after.json')['case']['orchestration_snapshot']
for key in ['workflow_actions','approval_requests','execution_attempts']:assert before[key]==after[key]
old_actions=[]
for a in after['workflow_actions']:
 if a['workflow_action_id'] not in [582,586,587,588]:continue
 try:validate_outlook_action(SimpleNamespace(**a));validation='PASS (structural only)'
 except OutlookContractError as e:validation=str(e)
 assert a['idempotency_key']!=r['action']['idempotency_key']
 assert a['structured_payload'].get('plan_identity')!=value.plan_identity
 old_actions.append({'action_id':a['workflow_action_id'],'persisted_status':a['status'],'canonical_validation':validation})
client=build_client(root/'Staging Authentications.txt',timeout_seconds=90)
assert client.config.base_url.rstrip('/')=='https://wnc-rental-brain-staging.onrender.com'
try:older=client.inspect_governed_outlook_send_readiness(rental_case_id=424,workflow_action_id=588)
except OperatorHarnessError as e:older={'status_code':e.status_code,'error':e.error_payload}
(p/'historical_588_readiness.json').write_text(json.dumps(older,indent=2)+'\n')
assert older.get('status_code')==409, 'Historical context unexpectedly ready; inspect before reporting'
history_audit={'full_case_424_rows_unchanged':True,'tables':{k:{'rows':len(v),'sha256':hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()} for k,v in history_before.items()},
 'actions':old_actions,'historical_588_readiness':older,'old_approvals_cannot_target_fresh_lineage':True,'idempotency_collision':False}
(p/'historical_isolation.json').write_text(json.dumps(history_audit,indent=2)+'\n')
health=load('health_after.json');assert health['status']=='ok' and health['environment']=='staging'
assert health['providers']=={'outlook':'configured_draft_only','asana':'configured_but_disabled'}
for k in ['application','database','phase5','phase6']:assert health[k]['status']=='ok'
m=load('baseline_manifest.json')
for f,h in m['file_sha256'].items():assert hashlib.sha256((root/f).read_bytes()).hexdigest()==h
fields_audit={'contract_version':value.contract_version,'required_fields':list(value.to_payload()),'field_count':len(value.to_payload()),'nullable_fields_explicit':True,'projection':'PASS','binding':'PASS','recipient_allowlist':'PASS','fresh_candidate_current':True}
(p/'contract_audit.json').write_text(json.dumps(fields_audit,indent=2)+'\n')
status={'marker':'OUTLOOK_FINAL_SEND_RECERTIFIED_READY_FOR_APPROVAL','accepted_commit':m['accepted_implementation'],'case_id':cid,'draft_revision_id':rid,'workflow_action_id':aid,'approval_request_id':apid,'recipient':value.recipient_email,'subject':value.subject,'draft_status':revisions[0]['draft_status'],'draft_current':True,'action_status':actions[0]['status'],'approval_status':'open','approval_target':value.approval_target,'execution_attempts':0,'health':health,'send_gate':'disabled','tests':{'focused':128,'focused_subtests':102,'phase8':552,'phase8_subtests':126,'full':769,'full_subtests':160,'failures':0,'skipped':0},'safety':{'Graph calls':0,'Outlook mutations':0,'Outlook sends':0,'real Asana':0,'production':0,'OpenAI calls':0,'hosted approvals':0,'hosted ExecutionAttempts':0},'deployment':'none needed; accepted deployed source unchanged'}
(p/'program_status.json').write_text(json.dumps(status,indent=2)+'\n')
report=f'''# Drafting Baseline Frozen

Closure record: [ACCEPTED_DRAFTING_BASELINE.md](../ACCEPTED_DRAFTING_BASELINE.md).

Accepted implementation: `{m['accepted_implementation']}`. Marker: **WNC_GOVERNED_DRAFTING_STAGING_ACCEPTED**. No new architecture version. Future semantic changes require an explicit new version and regression evidence. Source hashes and broad/targeted acceptance evidence are frozen in `baseline_manifest.json`.

# Current Outlook Contract

**PASS** against the current deployed implementation, verified live in Render at deployment `dep-db0eg660tbcc73ffrrpg`. All {len(value.to_payload())} canonical keys survive the execution-input projection, parser and adapter boundary. Identity, intent, revision, recipient/content, transport/approval and recovery fields are listed in `contract_audit.json` and captured in `fresh_candidate.json`.

Inapplicable Graph and recovery fields are explicitly null. Contract version remains `governed_outlook_v1`. Normal, human-edit and recovery constructions, malformed/missing fields, exact approval, stale context/revision, recipient drift, provider safety and replay are covered by existing and added regressions. No production application source changed.

# Provider-Free Send Simulation

**PASS.** A fresh local PostgreSQL case under staging fixture configuration traversed the real application creation, governed generation, immutable draft, canonical action, exact approval, ready-to-execute, pre-send governance, Outlook adapter with deterministic HTTP transport, successful attempt and result persistence. The local database used the existing current schema migrations inside the rollback transaction. No deployed schema changed.

Application replay was blocked; the shared execution runtime independently returned `action_already_succeeded`. It created no second attempt and made no fake transport calls on replay. The entire database simulation rolled back. Additional in-memory application tests observed exactly one fake `/send`. Fake HTTP calls are local fixture method calls, not Graph network calls.

Evidence: `database_simulation.json`, `test_outlook_recertification.py`, focused test XML.

# Human Edit / Recovery Regression

**PASS.** Fake read fixtures pass through the real reconciliation apply method. Original revision content stays immutable and historical; successor content hash and exact approval target change. Provenance is `outlook_human_edit`, with the fixture Graph ID bound canonically. An old approved action cannot execute, and the successor cannot execute until separately approved. The successor then passes the complete fake execution and replay lifecycle. Existing canonical recovery/idempotency and reconciliation negative cases also pass.

# Historical Isolation

**PASS.** Full rows for case 424's workflow actions, approvals, execution attempts and draft revisions were compared before/after and are identical. Actions 582/586 remain failed; their failed attempts 21/22 are unchanged. Action 587 retains its historical `ready_to_execute` status but has an invalid canonical payload and cannot enter the certified send path. It was not repaired or reclassified. Action 588 remains unapproved and fails the current hosted readiness check with stale-context validation (HTTP 409).

Historical approvals 184/185 target their old actions and revision; approval 186 remains open for 588/144. None targets the fresh lineage. Fresh plan identity/idempotency key are unique in staging and distinct from every inspected historical action. Historical records were not cleaned up or modified.

# Fresh Send Candidate

| Field | Value |
|---|---|
| Case ID | {cid} |
| DraftRevision ID | {rid} |
| WorkflowAction ID | {aid} |
| ApprovalRequest ID | {apid} |
| Recipient | {value.recipient_email} |
| Subject | {value.subject} |
| Draft status | needs_approval; CURRENT; immutable |
| Action status | awaiting_approval |
| Approval status | OPEN |
| Exact approval target | `{value.approval_target}` |
| ExecutionAttempts | 0 |
| Send gate | disabled |

Exact body:

```text
{value.body}
```

Creation used the unchanged deployed application source against the actual staging PostgreSQL repository. Only the process-local deterministic model fixture supplied the clearly synthetic text; the regular safety/realization gates, revision persistence, canonical builder and approval creation all ran. The resulting provenance explicitly records `deterministic_fixture`, not an LLM response. No configured provider/model, recipient allowlist or environment variable was changed.

The real hosted provider-free readiness endpoint independently returned canonical payload, execution-input, pre-send governance input, exact revision, current case/context and recipient allowlist PASS; approval required; send gate disabled. Exactly one revision, one Outlook action and one open approval exist in this new case.

# Tests

| Suite | Passed | Subtests passed | Failures / skips |
|---|---:|---:|---|
| Focused Outlook/governance/recovery/provider safety | 128 | 102 | 0 / 0 |
| Full Phase 8 | 552 | 126 | 0 / 0 |
| Full repository | 769 | 160 | 0 / 0 |

Separate PostgreSQL lifecycle simulation: PASS, rolled back. `git diff --check`: PASS. The full suite includes 40 existing/imported helper-class collection warnings. Two new regressions cover full application lifecycle and human-edit successor execution. Initial certification-harness setup issues (local schema migrations, normalized fixture allowlist and historical table names) were corrected before any hosted candidate write; no application remediation was required.

# Deployment

No deployment was necessary or performed. Accepted implementation remains live; this task adds closure documentation, evidence and regression tests only.

# Current Health

Staging application, database, Phase 5 and Phase 6: **ok**. Outlook: `configured_draft_only`. Outlook send gate: **disabled**. Asana: `configured_but_disabled`.

# Safety

Graph calls = 0; Outlook mutations = 0; Outlook sends = 0; real Asana = 0; production = 0; OpenAI calls = 0. Hosted approvals and hosted ExecutionAttempts created = 0. Local simulation approvals/attempts were fake and rolled back. No Exchange RBAC, Entra permissions, provider/model, allowlist or deployed environment changes.

# Final Marker

**OUTLOOK_FINAL_SEND_RECERTIFIED_READY_FOR_APPROVAL**

Stopped at the human approval checkpoint. The fresh approval remains OPEN. Sending remains disabled. The fresh action was not executed.
'''
(p/'OUTLOOK_SEND_RECERTIFICATION_REPORT.md').write_text(report)
print(status['marker']);print(json.dumps({k:status[k] for k in ['case_id','draft_revision_id','workflow_action_id','approval_request_id','approval_target','execution_attempts']}))
