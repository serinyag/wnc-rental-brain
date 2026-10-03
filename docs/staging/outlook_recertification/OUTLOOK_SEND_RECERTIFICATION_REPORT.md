# Drafting Baseline Frozen

Closure record: [ACCEPTED_DRAFTING_BASELINE.md](../ACCEPTED_DRAFTING_BASELINE.md).

Accepted implementation: `7ef15d28bcad6bd8991510e6315ea1d32e12f54b`. Marker: **WNC_GOVERNED_DRAFTING_STAGING_ACCEPTED**. No new architecture version. Future semantic changes require an explicit new version and regression evidence. Source hashes and broad/targeted acceptance evidence are frozen in `baseline_manifest.json`.

# Current Outlook Contract

**PASS** against the current deployed implementation, verified live in Render at deployment `dep-db0eg660tbcc73ffrrpg`. All 28 canonical keys survive the execution-input projection, parser and adapter boundary. Identity, intent, revision, recipient/content, transport/approval and recovery fields are listed in `contract_audit.json` and captured in `fresh_candidate.json`.

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
| Case ID | 584 |
| DraftRevision ID | 386 |
| WorkflowAction ID | 1619 |
| ApprovalRequest ID | 465 |
| Recipient | Serinya@whennaturecalls.nl |
| Subject | SYNTHETIC TEST - Outlook final send certification |
| Draft status | needs_approval; CURRENT; immutable |
| Action status | awaiting_approval |
| Approval status | OPEN |
| Exact approval target | `workflow_action:1619:draft_revision:386` |
| ExecutionAttempts | 0 |
| Send gate | disabled |

Exact body:

```text
Hi Serinya,

This is a synthetic test message for the Outlook approval and execution path. No action is required from you.
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
