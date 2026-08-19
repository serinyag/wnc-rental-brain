# Phase 8 Inquiry Response Drafting Release Validation

Date:

- Saturday, August 15, 2026

Repository:

- `/Users/serinya/Documents/WNC Rental Automation`

Release decision:

- `READY_FOR_STAGING_PREPARATION`

## Executive Summary

This document is now superseded by the final local sandbox release gate:

- `docs/phase-08/PHASE_8_LOCAL_SANDBOX_FINAL_RELEASE_GATE.md`

Authoritative current status as of Saturday, August 15, 2026:

- `READY_FOR_STAGING_PREPARATION`

What changed after the earlier blocked validation:

- direct SQL due-time acceleration was eliminated from the supported operator proof
- the supported `followups/evaluate` path was remediated so the local route no longer times out
- the full supported-control journey now succeeds end to end on a fresh case
- FollowUp `#2`, the time-critical escalation branch, restart persistence, and clock-reset semantics are all proven in the final gate
- the post-fix repository-wide validation matrix is green

The historical sections below are preserved as pre-final-gate validation evidence only.

## Migration And Schema Verification

Fresh local reset was completed successfully with:

- `npx -y supabase@latest db reset --local --yes`

The new migration applied cleanly:

- `supabase/migrations/20260815000100_phase_08_inquiry_response_drafting_slice.sql`

Verified persisted objects:

- table: `public.inquiry_response_draft_revisions`
- indexes:
  - `idx_inquiry_response_drafts_case_created`
  - `idx_inquiry_response_drafts_workflow_action`
  - `idx_inquiry_response_drafts_conversation`
  - `uq_inquiry_response_drafts_current_conversation`
  - `uq_inquiry_response_drafts_current_approval`
- guard function: `private.guard_inquiry_response_draft_revision_write`
- trigger: `trg_guard_inquiry_response_draft_revision_write`

Draft-safety invariants now enforced at the database layer:

- workflow action and approval request must belong to the same `rental_case_id`
- superseded draft revisions must stay inside the same case and conversation
- approval target reference must match `workflow_action:<id>:draft_revision:<id>`
- only one current draft may exist per `(rental_case_id, conversation_key)`
- only one current draft may bind a given approval request
- immutable draft content cannot be rewritten in place through `UPDATE`

Focused drafting pgTAP coverage passed:

- `supabase/tests/43_phase_08_inquiry_response_drafting_slice.sql`
- result: `1 file / 11 tests PASS`

Full Supabase validation also passed on the migrated database:

- `npx -y supabase@latest test db --local`
- result: `43 files / 1077 tests PASS`

## Baseline Restoration

Phase 5 corpus restoration succeeded with:

- `python3 -m tools.phase_05_chunking.generate_bulk --load-db`

Observed live counts after restore:

- current chunk sets: `22`
- current chunks: `525`
- searchable current chunk sets: `21`
- searchable current chunks: `492`
- active included governed document versions: `22`

Phase 6 embedding restoration succeeded with:

- `python3 -m tools.phase_06_search.generate_embeddings`

Observed live counts after restore:

- historical search units: `112`
- active retrieval-approved models: `1`
- historical embeddings: `112`
- missing embeddings: `0`
- active model: `openai / text-embedding-3-small / 1536`

## Test And Regression Results

Completed earlier in the same fresh-reset validation session:

- focused drafting DB: `1 file / 11 tests PASS`
- Inquiry Waiting focused suite: `61 PASS`
- Phase 7: `127 PASS`
- Phase 5 search: `24 PASS`
- Phase 6: `6 PASS`
- full Supabase: `43 files / 1077 tests PASS`

Post-remediation reruns completed after the final live defects were fixed:

- `python3 -m pytest -q tools/phase_08_workflow/tests/test_inquiry_response_drafting.py tools/phase_08_workflow/tests/test_test_console_service.py tools/phase_08_workflow/tests/test_test_console_app.py tools/phase_08_workflow/tests/test_test_console_projection.py`
- result: `45 PASS`

- `python3 -m pytest tools/phase_08_workflow/tests -q`
- result: `177 PASS`

- `python3 -m pytest tools/phase_05_chunking/tests -q`
- result: `29 PASS`

## Validation Defects Found And Closed

This release gate surfaced four genuine defects during live validation:

1. The shared Supabase JSON query wrapper broke top-level `WITH ... INSERT ... RETURNING` statements.
2. Draft revision creation needed an explicit dependency on the `unset_current` CTE to keep current-draft demotion ordered.
3. Edit-after-approval successor actions reused the original workflow action `idempotency_key`, violating the live uniqueness constraint.
4. Ambiguous adapter outcomes were classified from operation-level `failure_codes` instead of the persisted execution-attempt failure code, causing `send_outcome_uncertain` to collapse into `send_failed`.

All four defects are now fixed in code and the last defect is specifically covered by:

- `test_execute_ambiguous_marks_current_draft_as_uncertain`

## Live Operator Validation

### Case 39: clean success path

The full simulated mailbox path succeeded end to end:

- generate draft `27`
- edit to draft `28`
- approve
- edit after approval to draft `29`
- successor action `25`
- execute success with attempt `7`

Final persisted state:

- current draft revision: `29`
- current draft status: `simulated_sent`
- workflow action `25`: `succeeded`
- delivery external reference: `fake:internal:25:1`
- restart persistence: confirmed after console restart

Important reproducibility note:

- this fresh case did not naturally become action-ready from console-only operations
- direct SQL due-time acceleration was required before the action formed cleanly

### Case 40: retryable failure path

Retryable failure behavior remained correct:

- workflow action `26`: `ready_to_execute`
- execution attempt `8`: `failed`
- failure code: `fake_retryable_failure`
- thread display status: `send_failed`

This preserved retry eligibility without falsely projecting a send success.

### Case 42: fresh ambiguous path after final fix

Fresh-case ambiguous send behavior now lands correctly:

- workflow action `31`
- approval request `26`
- execution attempt `11`
- attempt status: `failed`
- attempt failure code: `adapter_outcome_ambiguous`
- thread display status: `send_outcome_uncertain`
- current draft status: `send_outcome_uncertain`

Observed timings on this fresh case:

- `create_case`: `810.2ms`
- `raw_evidence`: `456.3ms`
- `structured_guest_count`: `3952.6ms`
- `structured_event_type`: `4067.6ms`
- `inquiry_intake`: `6145.9ms`
- `inquiry_waiting_initial`: `25519.0ms`
- `inquiry_waiting_after_due_1`: `25675.7ms`
- `evaluate_followups_1`: `20095.0ms`
- `reconcile_1`: `20856.5ms`
- `generate_draft`: `6857.6ms`
- `approve_draft`: `5144.4ms`
- `execute_ambiguous`: `32432.6ms`
- total end-to-end elapsed: `155061.0ms`

This case also required direct SQL due-time acceleration before the action formed.

### Case 41: pre-fix polluted live evidence

Before the final ambiguous-outcome fix, a live ambiguous-path attempt left a bad intermediate state:

- execution attempt `9` remained `started`
- the draft was recorded as `send_failed`
- the stored failure code was `execution_complete_failed`

That state came from the pre-fix validation run and is retained only as evidence of the bug that was found and then closed. The fresh-case proof for the fixed behavior is case `42`.

## Cross-Case Isolation

Cross-case misuse checks stayed closed on the live console:

- `POST /cases/40/approvals/22/approve`
  - rendered failure with `approval_target_invalid`
- `POST /cases/40/actions/25/execute`
  - rejected with `WorkflowAction 25 was not found for RentalCase 40`
- `POST /cases/40/mailbox/drafts/29/edit`
  - rejected with `INQUIRY_DRAFT_NOT_FOUND`

No foreign-case approval, action, or draft was allowed to mutate case `40`.

## Remaining Release-Gate Blockers

### Blocker 1: console-only action formation is still not reproducible

Fresh inquiry cases still needed direct SQL intervention to move follow-ups into an action-forming state:

- case `39`
- case `42`

The console route alone did not reliably produce the drafting action on a clean case in an operator-realistic way.

### Blocker 2: fresh-case local runtime is still too slow

The environment remained well above the local acceptance bar for operator usability:

- case `41` included repeated `38s` to `65s` inquiry-waiting and follow-up operations
- case `42` still required about `155s` total for a fresh ambiguous path
- several individual steps in cases `39`, `41`, and `42` exceeded the `10s` reporting threshold by a wide margin

This is no longer a correctness problem in the drafting logic. It is still an environment and readiness problem.

## Final Marker

- superseded by `docs/phase-08/PHASE_8_LOCAL_SANDBOX_FINAL_RELEASE_GATE.md`
- current authoritative marker: `READY_FOR_STAGING_PREPARATION`
