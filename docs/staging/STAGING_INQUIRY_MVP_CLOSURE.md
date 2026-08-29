# Staging Inquiry MVP Closure

**Closure date:** 2026-08-29
**Scope:** Hosted staging Inquiry MVP only. This record does not authorize production planning or production use.

## Closure Markers

`STAGING_INQUIRY_MVP_COMPLETE`
`RELIABLE_FOR_SUPERVISED_STAGING_USE`
`STRONG_SUPERVISED_INQUIRY_MVP`
`S7_REAL_OUTLOOK_OUTBOUND_STAGING = DEFERRED_EXTERNAL_DEPENDENCY`

## 1. Executive Summary

The WNC Rental Brain progressed from a local sandbox to a hosted, access-restricted
staging environment. It passed runtime portability, environment and safety
hardening, hosted Supabase deployment, hosted knowledge bootstrap, fake-provider
inquiry flow, real Asana staging execution, full hosted Inquiry MVP validation,
quality calibration, unseen holdout validation, and an adjudicated second holdout.

The current runtime and governance behavior are strong for human-reviewed staging
inquiries. Unseen quality and generalization evidence is also strong. Human
approval remains required. Real Outlook outbound is deferred because no clean,
staging-safe Microsoft 365 tenant/mailbox/admin-consented Graph path is currently
available, not because a demonstrated application defect remains.

## 2. Architecture Boundary

```text
Phase 4: current deterministic WNC truth
Phase 5: current governed knowledge
Phase 6: historical precedent
Phase 7: authority-aware reasoning
Phase 8: case-specific operational truth, workflow, approvals,
         actions, execution, and follow-up
```

> The AI may interpret and draft. The application controls reality.

Historical precedent never overrides current authority. Generated prose never
silently becomes workflow truth. External systems are adapters, not truth stores.

## 3. Current Hosted Staging Environment

- Render: `https://wnc-rental-brain-staging.onrender.com`
- Hosted Supabase project ref: `mspcopnsbounmdpivkvq`
- Runtime: `APP_ENV=staging`, `SystemClock`, and Basic Auth for Test Console routes.
- Data: separate hosted database; synthetic staging cases only; no production data; no Docker fallback.
- Knowledge health: Phase 5 has 492 eligible and embedded current chunks; Phase 6 has 112 eligible and embedded historical units; both reported healthy in the final staging preflight.
- Providers: Asana configured; Outlook disabled; communication testing uses the internal/fake pathway where applicable.
- `/healthz` exposes safe application, database, knowledge, and provider status without secrets or provider network calls.

## 4. Staging Milestone History

### S1A - Runtime Portability

Added a deployable WSGI entrypoint and `DATABASE_URL` Psycopg transport while
preserving the legacy Docker path for local-only use. A clean virtualenv install,
focused portability tests, and direct-database journey validated the portable path.

### S1B - Environment And Safety Hardening

Introduced `APP_ENV`, required staging Basic Auth and `DATABASE_URL`, disabled
mutable clocks and Docker fallback in staging, restricted the runtime to
`SystemClock`, added provider allowlists, `/healthz`, and environment-safe bootstrap
guards.

### S2/S3 - Hosted Resources And Deployment

Provisioned separate hosted Supabase staging and a Render staging service, keeping
both separate from the local Docker sandbox.

### S4 - Hosted Knowledge Bootstrap

Hosted Phase 5 and Phase 6 bootstrap completed and is healthy at 492 current
embedded chunks and 112 historical embedded units.

### S5 - Fake-Provider Inquiry Flow

Hosted synthetic inquiry validation proved the persisted journey from RentalCase
creation through observations, intake, reconciliation, waiting/follow-up, draft,
approval, simulated execution, and audit records.

### S6 - Real Asana Staging

A dedicated staging project was allowlisted and exercised through the real adapter.
Idempotency and replay protections were validated. A hosted-only `task_surface`
alias defect was found, fixed narrowly, and regression-tested.

### S7 - Real Outlook

`DEFERRED_EXTERNAL_DEPENDENCY`: no clean staging-safe Microsoft 365
tenant/mailbox/admin-consented Graph path is available. This is not an application
failure.

### S8 - Full Inquiry MVP Staging Validation

Multi-scenario hosted validation exercised the real operator path. A no-op schedule
normalization defect was found and fixed narrowly. Workflow truth integrity and
health remained green.

## 5. Technical Reliability Evidence

Hosted staging has validated persistence and reconstruction of RentalCases,
observations, Case Facts, OpenQuestions, Requirements, Blockers, decisions,
WorkflowActions, FollowUps, ApprovalRequests, ExecutionAttempts, WorkflowEvents,
and Asana external references. Approval is exact-revision-bound. Duplicate safety
and replay behavior were validated for provider execution.

The hosted defects found during validation, including the Asana alias and no-op
schedule normalization issues, were corrected with regression coverage. Staging was
therefore a meaningful defect-discovery environment, not a ceremonial deployment.

## 6. Quality Calibration History

The initial 32-case baseline exposed quality residue despite strong safety: the
recorded baseline included `18/13/1/0` A/B/C/D, 96.9% A+B, zero critical failures,
and a 62.5% next-action rate. Cycle 1 improved the known benchmark but the first
unseen holdout failed materially, demonstrating narrow semantic coverage rather
than reliable generalization.

Cycles 2 and 3 formalized the semantic-state and state-to-action contracts,
reduced permissiveness, surfaced over-caution, and made next-action evaluation
state-aware. The resulting contract distinguishes known yes, deterministic known
no, governed conditional support, unknown internal authority, and missing client
facts.

The commercial-truth investigation also corrected an evaluation-fixture defect.
The canonical record is `HOLD-002`: the event had a three-hour Studio window, for
which the authoritative current fee was EUR 50; the frozen gold incorrectly
expected EUR 75. The runtime was deterministic and correct. This closure uses the
repository record rather than the stale `HOLD-004`/four-hour characterization.

## 7. Holdout Generalization Evidence

### Holdout 1

The initial unseen holdout showed poor generalization and unsafe semantic behavior,
so remediation continued. The final regression achieved 10/10 semantic matches,
zero D outcomes, zero critical failures, 100% authority and confidentiality safety,
and a 90% next-action rate. Remaining quality residue was non-critical field
consumption/edit-burden work.

### Holdout 2 Original V1

The original frozen run recorded `4/8/0/0` A/B/C/D, 100% A+B, zero critical
failures, raw semantic `9/12`, and raw next action `4/12`. Its strict gate failed.
The original fixture, raw report, and raw result remain preserved.

### Holdout 2 Adjudication And V2

Adjudication established that the apparent failures came from incorrect gold
expectations, proposition-insensitive action attribution, and scenarios expecting
waiting-stage actions while `run_waiting=false`. The same hosted runtime was then
re-evaluated with a repaired evaluation contract.

The adjudicated v2 result was `12/12 A`, `0 B/C/D`, 100% A+B, zero critical
failures, zero unsupported assertions, zero wrong-price failures, zero unsupported
commercial commitments, 12/12 primary semantic matches, 27/27 proposition semantic
matches, and 12/12 next-action matches. Authority and confidentiality were both
100%. No provider execution occurred. The hosted runtime was unchanged.

## 8. Final Reliability Judgment

`RELIABLE_FOR_SUPERVISED_STAGING_USE`
`STRONG_SUPERVISED_INQUIRY_MVP`

The system can reliably support human-reviewed inquiry work in staging. Its
semantic reasoning generalized across unseen scenarios, safety boundaries held, and
the final adjudicated result had low edit burden. This is not autonomous production
readiness: human review and approval remain required.

## 9. What Is Proven

- Hosted staging operation and hosted database persistence.
- Basic Auth, SystemClock posture, and staging safety boundaries.
- Phase 5/6 bootstrap health and current-governed knowledge use.
- Governed intake, missing-information detection, and internal-versus-client uncertainty handling.
- Deterministic restrictions, conditional support, authority-conflict handling, and historical-precedent containment.
- Exact-revision approval, idempotency, and real allowlisted Asana execution.
- Strong unseen quality/generalization with no critical failures in final adjudicated evaluation.

## 10. What Is Not Proven

- Production deployment, data migration, or production readiness.
- Autonomous or no-human-review operation.
- Real Outlook outbound or inbound, Graph subscriptions/webhooks, email polling, or n8n.
- Worker/queue infrastructure, long-duration production-scale load, production observability/SLA, or broad multi-user rollout.

## 11. Known Limitations And Residue

- S7 Microsoft/Outlook remains an external dependency.
- The Test Console remains the current operator surface.
- Some low-level operator API payload shapes remain irregular.
- Minor field-consumption/edit-burden residue remains in Holdout 1 despite correct semantic and safety outcomes.
- Render's deployed commit SHA is not independently exposed by the public application surface.
- Calibration fixture and evidence history require deliberate source-control preservation.

## 12. Human Approval Boundary

Drafts require human review where the current architecture requires it. Approval
binds to an exact revision and does not manufacture missing authoritative truth.
Unknown internal knowledge remains blocked until governed confirmation or evidence
resolves it. A deterministic no remains no unless a governed exception path exists.

## 13. Provider Posture

### Asana

Configured, staging-only, allowlisted, and validated through real execution.
Duplicate safety was validated.

### Outlook

Disabled. Real outbound is deferred and no inbound implementation exists. Microsoft
Graph calls remained zero during final quality validation. Microsoft setup can be
revisited separately when a safe staging path exists without reopening the Inquiry
MVP architecture unless integration testing proves a specific defect.

## 14. Handover Invariants

1. Current authority outranks historical precedent.
2. Absence of prohibition does not equal permission.
3. Known no must not degrade into generic confirmation.
4. Unknown internal knowledge must not become known yes.
5. Missing client fact must be asked of the client.
6. Unrelated uncertainty must not alter commercial truth.
7. Generated prose cannot become workflow truth directly.
8. External providers remain adapters.
9. Approval is exact-revision-bound.
10. Staging remains isolated from production.
11. Real provider execution remains allowlisted.
12. Human approval remains part of the operational model.

## 15. Recommended Next Stage

The recommended next activity is **Supervised Operator UAT / usability
validation**. Use the actual Test Console with realistic synthetic or safely
de-identified inquiry sessions to observe operator friction, trust/readability,
edit burden, and UI/usability issues. This is distinct from semantic calibration
and is not another architecture phase. Microsoft Graph/Outlook may be revisited
separately when a staging-safe setup becomes available.

## 16. Production Boundary

Production planning is **not** authorized by this closure record. Any future
production-readiness phase needs a separate review of security, production secrets,
identity/access, data/privacy, monitoring, operational ownership, provider
configuration, backup/recovery, rollout, and support/incident handling. Those
matters are intentionally not designed here.

## 17. Evidence Index

- `docs/staging/WNC_RENTAL_STAGING_ARCHITECTURE_AND_SETUP_PLAN.md`
- `docs/staging/STAGING_S1A_RUNTIME_PORTABILITY.md`
- `docs/staging/STAGING_S1B_ENVIRONMENT_AND_SAFETY_HARDENING.md`
- `tools/phase_08_workflow/operator_harness.py`
- `docs/staging/calibration/baseline_report_latest.md`
- `docs/staging/calibration/remediation_cycle_02_diagnosis.md`
- `docs/staging/calibration/remediation_cycle_03_diagnosis.md`
- `docs/staging/calibration/remediation_cycle_04_commercial_truth_contract.md`
- `docs/staging/calibration/commercial_truth_remediation.md`
- `docs/staging/calibration/semantic_state_contract.md`
- `docs/staging/calibration/state_to_action_contract.md`
- `docs/staging/calibration/holdout_report_latest.md`
- `docs/staging/calibration/holdout2_scenarios_original_v1.json`
- `docs/staging/calibration/holdout2_report_holdout2-20260829-120008.md`
- `docs/staging/calibration/holdout2_adjudication.md`
- `docs/staging/calibration/holdout2_scenarios_adjudicated_v2.json`
- `docs/staging/calibration/holdout2_scenarios_adjudicated_v2_report_holdout2_scenarios_adjudicated_v2-20260829-123037.md`
- `docs/staging/calibration/generalization_summary.md`
- `docs/staging/STAGING_INQUIRY_MVP_CLOSURE.md`
