# Phase 8 Local Sandbox Final Release Gate

Date:

- Saturday, August 15, 2026

Repository:

- `/Users/serinya/Documents/WNC Rental Automation`

Final decision:

- `READY_FOR_STAGING_PREPARATION`

Guardrails enforced during this gate:

- validation-only work
- no staging provisioning
- no real Outlook calls
- no real Asana calls
- no workflow-semantic changes outside the narrow runtime remediation required to restore the supported follow-up evaluation path

## Repository Inspection Summary

- The local workspace was not a clean git worktree during validation, so existing user changes were left intact and no reset/revert operations were used.
- The prior canonical readiness docs still carried stale `NOT_READY_FOR_STAGING_PREPARATION` markers from the pre-remediation gate.
- Migration count observed during inspection: `38`.
- Supabase test file count observed during inspection: `43`.
- The local database was already healthy, so no fresh reset was performed for this gate.

Phase 5 live corpus state already present and retained:

- current chunk sets: `22`
- current chunks: `525`
- searchable current chunk sets: `21`
- searchable current chunks: `492`
- active included governed document versions: `22`

Phase 6 live retrieval state already present and retained:

- historical search units: `112`
- active retrieval-approved models: `1`
- historical embeddings: `112`
- missing embeddings: `0`
- active model: `openai / text-embedding-3-small / 1536`

## Final Validation Matrix

| Validation                     |        Previous | Final |
| ------------------------------ | --------------: | ----: |
| Clock/performance focused      |         59 PASS | `51 PASS` |
| Drafting focused               |         45 PASS | `49 PASS` |
| Inquiry Waiting focused        |         61 PASS | `68 PASS` |
| Phase 8                        |        177 PASS | `186 PASS` |
| Phase 7                        |        127 PASS | `127 PASS` |
| Phase 5 chunking               |         29 PASS | `29 PASS` |
| Phase 5 search                 |         24 PASS | `24 PASS` |
| Phase 6                        |          6 PASS | `6 PASS` |
| Drafting DB                    |           11/11 | `11/11 PASS` |
| Waiting DB                     |             7/7 | `7/7 PASS` |
| Full Supabase                  | 43 files / 1077 | `43 files / 1077 PASS` |
| Supported-control full journey |            PASS | `PASS` |
| Direct SQL required            |               0 | `0` |

Exact rerun commands and final results:

- `python3 -m pytest -q tools/phase_08_workflow/tests/test_test_console_app.py tools/phase_08_workflow/tests/test_test_console_service.py tools/phase_08_workflow/tests/test_inquiry_waiting.py tools/phase_08_workflow/tests/test_execution_runtime.py`
  - result: `51 passed`, `10 warnings`
- `python3 -m pytest -q tools/phase_08_workflow/tests/test_inquiry_response_drafting.py tools/phase_08_workflow/tests/test_test_console_service.py tools/phase_08_workflow/tests/test_test_console_app.py tools/phase_08_workflow/tests/test_test_console_projection.py`
  - result: `49 passed`, `15 warnings`
- `python3 -m pytest -q tools/phase_08_workflow/tests/test_inquiry_waiting.py tools/phase_08_workflow/tests/test_orchestration_runtime.py tools/phase_08_workflow/tests/test_test_console_app.py tools/phase_08_workflow/tests/test_test_console_projection.py tools/phase_08_workflow/tests/test_test_console_service.py`
  - result: `68 passed`, `11 warnings`
- `python3 -m pytest tools/phase_08_workflow/tests -q`
  - result: `186 passed`, `15 warnings`
- `python3 -m pytest tools/phase_07_reasoning/tests -q`
  - result: `127 passed`
- `python3 -m pytest tools/phase_05_chunking/tests -q`
  - result: `29 passed`
- `python3 -m pytest tools/phase_05_search/tests -q`
  - result: `24 passed`
- `python3 -m pytest tools/phase_06_search/tests -q`
  - result: `6 passed`
- `npx -y supabase@latest test db --local`
  - result: `43 files / 1077 tests PASS`
- `npx -y supabase@latest test db --local supabase/tests/42_phase_08_inquiry_waiting_follow_up_slice.sql`
  - result: `1 file / 7 tests PASS`
- `npx -y supabase@latest test db --local supabase/tests/43_phase_08_inquiry_response_drafting_slice.sql`
  - result: `1 file / 11 tests PASS`

Note on targeted DB reruns:

- A parallel rerun attempt for `43_phase_08_inquiry_response_drafting_slice.sql` hit the known pgTAP enable race (`LegacyTestDbEnablePgtapError`).
- The authoritative result is the immediate isolated rerun above, which passed cleanly.

## Supported-Control Operator Journey

Fresh supported-control proof case:

- RentalCase: `82`
- case reference: `RC-20260815130011123`
- simulated start time: `2026-08-15T13:00:11.123456Z`
- simulated due time after initial waiting: `2026-08-22T13:00:11.123456Z`

Supported controls used only:

- create test RentalCase
- inject raw test evidence
- inject structured observations
- run Inquiry Intake
- run Inquiry Waiting
- advance simulated clock
- run Follow-Up evaluation
- run due Inquiry Waiting
- generate draft
- save human-edited successor draft
- approve exact revision
- simulate send
- reload case page

Observed outcome:

- Inquiry Intake promoted `Requested Schedule` and `Event Type`.
- Open questions remained for `Guest Count` and `Requested Space`.
- Initial Inquiry Waiting created FollowUp `#1` in `scheduled`.
- Advancing the test clock did not change `follow_up.due_at`.
- Page reload before evaluation did not mutate the follow-up status.
- Follow-Up evaluation marked the follow-up `due` and created one governed `REQUEST_CLIENT_INFORMATION` workflow action.
- Draft generation, human edit, exact approval, and simulated send all completed through console routes only.
- Final persisted state after send:
  - follow-up `#1`: `completed`
  - workflow action `55`: `succeeded`
  - execution attempt `21`: `succeeded`
  - draft revision `59`: `simulated_sent`
  - approval request `49`: `approved`
  - current badge: `SIMULATED SENT`

Direct SQL / manual DB intervention required:

- `0`

## FollowUp #2 Proof

Fresh follow-up sequence proof case:

- RentalCase: `83`
- case reference: `RC-20260815140011123`
- simulated start time: `2026-08-15T14:00:11.123456Z`

Observed result:

- initial Inquiry Waiting created FollowUp `#1` due at `2026-08-22T14:00:11.123456Z`
- Follow-Up evaluation on the due date created the first client-information action
- after another supported `+7 day` advance with no response, Inquiry Waiting:
  - cancelled FollowUp `#1`
  - created FollowUp `#2`
  - superseded the old action
  - created the new current action

Persisted follow-up sequence after the proof:

- sequence `1`: `cancelled`
- sequence `2`: `scheduled`

Duplicate semantic FollowUps created:

- `0`

## Time-Critical Escalation Proof

Fresh urgent inquiry proof case:

- RentalCase: `84`
- case reference: `RC-20260815150011123`
- simulated start time: `2026-08-15T15:00:11.123456Z`
- requested event window: `2026-08-17T18:00:00Z` to `2026-08-17T22:00:00Z`

Observed result:

- Inquiry Waiting immediately created one `escalated` follow-up
- next action type became `Create Internal Task Item`
- one governed `CREATE_INTERNAL_TASK_ITEM` workflow action was formed
- lifecycle state remained `inquiry_active`

This confirms the urgent branch is governed and does not silently change the case lifecycle.

## Clock Safety And Restart Proof

Clock safety proof:

- Before evaluation, FollowUp `#1` for case `82` remained:
  - due at `2026-08-22 13:00:11.123456+00`
  - status `scheduled`
- After supported `+7 day` clock advance but before evaluation, the exact same due timestamp remained visible.
- Page reload alone did not mutate the follow-up.
- After console restart, the top banner returned:
  - clock mode: `REAL/CURRENT TIME`
  - current UTC: `2026-08-15T13:32:14.949737Z`

Restart persistence proof on case `82`:

- RentalCase persisted
- case facts persisted
- open questions persisted
- completed follow-up persisted
- succeeded workflow action persisted
- execution attempt persisted
- cancelled + approved approval records persisted
- draft revision history persisted
- `SIMULATED SENT` state persisted

Intended semantics confirmed:

- production/default clock semantics changed: `0`
- TestClock activates only in local/test scope: `yes`
- clock advance rewrites `follow_up.due_at`: `0`
- restart silently retains simulated clock mode: `0`

## Performance Recheck

Fresh supported-control journey timings for case `82`:

| Operation | Elapsed |
| --------- | ------: |
| create case | `0.854s` |
| raw evidence injection | `1.961s` |
| structured observation: active_event_window | `2.031s` |
| structured observation: event_type | `1.926s` |
| Inquiry Intake | `2.994s` |
| Initial Inquiry Waiting | `3.778s` |
| case reload before due evaluation | `0.796s` |
| Follow-Up evaluation | `1.780s` |
| Due Inquiry Waiting | `1.796s` |
| Draft generation | `1.789s` |
| Draft edit/save | `2.033s` |
| Draft approval | `2.336s` |
| Simulated send | `2.889s` |
| case reload after simulated send | `0.727s` |
| total measured journey | `27.690s` |

Comparison:

- old total: about `155s`
- earlier post-remediation reference: about `21.8s`
- current measured total: `27.690s`

Interpretation:

- the current measurement still reflects the same order-of-magnitude improvement over the old `155s` path
- the total is slightly above the earlier `21.8s` reference because this gate measured the full supported-control path including both structured-observation posts plus explicit pre-due and post-send reloads
- every common normal operator action stayed below the preferred `< 5s` envelope
- no common normal operator action exceeded the `10s` hard-attention threshold after the runtime fix

Structural performance notes:

- The live timeout on `followups/evaluate` was traced to repeated snapshot reloads inside orchestration reconciliation.
- The remediation now:
  - reuses the already-loaded reconciliation snapshot
  - removes per-loop snapshot reloads during action/approval/blocker creation
  - collapses three post-creation refreshes into one conditional refresh
  - removes an extra Supabase snapshot reload from `commit_follow_up_status_update(...)`
- Focused regression coverage now includes:
  - `test_due_follow_up_reuses_snapshot_loads_during_reconciliation`
  - bounded expectation: due-follow-up reconciliation path stays at `<= 4` in-memory `load_case_snapshot(...)` calls
- N+1 console projection reads remain removed.
- Residual subprocess overhead still exists because Supabase reads/writes are still executed through `docker exec psql`, but it is no longer a local readiness blocker.

## Safety Metrics

| Metric | Value |
| ------ | ----: |
| direct SQL due-time acceleration required | `0` |
| test clock modifies `follow_up.due_at` directly | `0` |
| production clock semantics changed | `0` |
| follow-up cadence modified for testing | `0` |
| workflow safety guards removed | `0` |
| idempotency guards weakened | `0` |
| approval semantics changed | `0` |
| draft revision safety regression | `0` |
| audit completeness regression | `0` |
| atomicity weakened | `0` |
| fake test path skips business logic | `0` |
| real Outlook calls | `0` |
| real Asana calls | `0` |
| cross-case mutation | `0` |
| stale action execution | `0` |
| stale draft execution | `0` |
| duplicate semantic FollowUps | `0` |
| duplicate semantic WorkflowActions | `0` |
| duplicate simulated sends | `0` |
| provider failure counted as success | `0` |
| ambiguous outcome counted as confirmed sent | `0` |
| page-load workflow mutation | `0` |
| console hangs | `0` |
| Phase 4 semantic changes | `0` |
| Phase 5 retrieval semantic changes | `0` |
| Phase 6 retrieval semantic changes | `0` |

## Local Reproducibility

Can another developer/operator reproduce the full local inquiry journey using documented commands and supported Test Console controls only?

- `YES`

Required manual commands:

- `python3 -m pytest -q tools/phase_08_workflow/tests/test_test_console_app.py tools/phase_08_workflow/tests/test_test_console_service.py tools/phase_08_workflow/tests/test_inquiry_waiting.py tools/phase_08_workflow/tests/test_execution_runtime.py`
- `python3 -m pytest -q tools/phase_08_workflow/tests/test_inquiry_response_drafting.py tools/phase_08_workflow/tests/test_test_console_service.py tools/phase_08_workflow/tests/test_test_console_app.py tools/phase_08_workflow/tests/test_test_console_projection.py`
- `python3 -m pytest -q tools/phase_08_workflow/tests/test_inquiry_waiting.py tools/phase_08_workflow/tests/test_orchestration_runtime.py tools/phase_08_workflow/tests/test_test_console_app.py tools/phase_08_workflow/tests/test_test_console_projection.py tools/phase_08_workflow/tests/test_test_console_service.py`
- `python3 -m pytest tools/phase_08_workflow/tests -q`
- `python3 -m pytest tools/phase_07_reasoning/tests -q`
- `python3 -m pytest tools/phase_05_chunking/tests -q`
- `python3 -m pytest tools/phase_05_search/tests -q`
- `python3 -m pytest tools/phase_06_search/tests -q`
- `npx -y supabase@latest test db --local`
- `npx -y supabase@latest test db --local supabase/tests/42_phase_08_inquiry_waiting_follow_up_slice.sql`
- `npx -y supabase@latest test db --local supabase/tests/43_phase_08_inquiry_response_drafting_slice.sql`
- `python3 -u -m tools.phase_08_workflow.test_console --port 8765`

Supported console actions for the live proof:

- set simulated time
- create case
- inject raw evidence
- inject structured observations
- run Inquiry Intake
- run Inquiry Waiting
- advance time
- run Follow-Up evaluation
- generate/edit/approve/send the draft

## Classification

Functional:

- `GREEN`
- The supported-control operator journey, FollowUp `#2`, time-critical escalation, restart persistence, and all post-fix automated suites passed.

Local Environment:

- `GREEN`
- The local DB baseline was already healthy, no reset was required, the console clock behaved deterministically, and the full inquiry path is reproducible without manual DB intervention.

Release / Staging Preparation:

- `GREEN`
- No critical or high-severity safety blocker remained after the runtime follow-up remediation, real providers stayed disabled, and the repository-wide validation matrix passed.

## Final Decision

Formal marker:

- `READY_FOR_STAGING_PREPARATION`

This gate does **not** authorize staging provisioning. The next task may prepare staging, but this gate itself did not:

- create a Supabase project
- deploy an app
- configure Microsoft Graph
- configure a real mailbox
- create an Asana staging project
- add staging secrets
- connect any real provider
