# Phase 8 Inquiry Waiting & Follow-Up Slice Evaluation

Date: Friday, August 14, 2026

Pre-slice readiness marker:

`READY_FOR_PHASE_8_INQUIRY_WAITING_AND_FOLLOW_UP_SLICE`

## Scope

This slice implemented the governed inquiry waiting path:

```text
OpenQuestions unresolved
→ semantic inquiry FollowUp
→ due / escalated posture
→ structured WorkflowAction
→ approval policy
→ stop before any real provider execution
```

No Outlook, Asana, Google Calendar, Mollie, or n8n execution was added.

## Repository inspection findings

- Phase 8.6 already provided persisted `rental_case_follow_ups`, due evaluation, and follow-up status transitions.
- `orchestration_runtime._apply_open_question_rules(...)` was still creating immediate `REQUEST_CLIENT_INFORMATION` actions for client questions, which conflicted with the desired waiting-first architecture.
- `orchestration_runtime._apply_follow_up_rules(...)` already knew how to turn current follow-ups into actions, but its payload was too thin for inquiry-stage missing-information work.
- `rental_case_follow_ups` lacked explicit semantic identity, sequence, and structured unresolved-question context for one semantic inquiry waiting episode.

## Implemented changes

- Added `tools/phase_08_workflow/inquiry_waiting.py`.
- Added a governed `InquiryFollowUpPolicy`, deterministic waiting plan, and `reconcile_inquiry_waiting(...)` runtime.
- Extended `FollowUp` with:
  - `semantic_identity_key`
  - `sequence_number`
  - `context_payload`
- Added repository `upsert_follow_up(...)` support for in-memory and Supabase persistence.
- Added migration `20260814000100_phase_08_inquiry_waiting_follow_up_slice.sql`.
- Added Supabase proof `supabase/tests/42_phase_08_inquiry_waiting_follow_up_slice.sql`.
- Stopped immediate client-information action creation from open client questions in orchestration.
- Enriched follow-up-driven request payloads with:
  - `follow_up_id`
  - `reason_code`
  - `sequence_number`
  - `open_question_ids`
  - `required_field_codes`
  - `recipient_reference`
  - `purpose`
  - `reason`
  - `question_texts`
  - `summary`
- Added test-console inquiry waiting control and improved follow-up display/projection detail.

## Business semantics now enforced

- Complete inquiry:
  - missing-information follow-up count = `0`
  - missing-information request action count = `0`
- Incomplete inquiry:
  - one semantic inquiry follow-up is created
  - repeated evaluation does not duplicate it
- Due follow-up:
  - current action is a structured `REQUEST_CLIENT_INFORMATION` workflow action
  - repeated evaluation does not duplicate the action
- Partial response:
  - the same waiting episode remains current
  - resolved questions drop out of the active follow-up context
  - stale request action is superseded
  - refreshed request action is created for remaining questions only
- Full response:
  - inquiry follow-up is cancelled
  - stale request action is superseded
  - stale action execution is rejected by existing execution guards
- Cold sequence:
  - follow-up `#1` and `#2` are distinguished by semantic identity plus `sequence_number`
  - repeated evaluation does not duplicate either sequence
- Time-critical inquiry:
  - escalates into governed internal work instead of silent dormancy

## Safety metrics

- complete inquiry incorrectly gets missing-info follow-up = `0`
- duplicate semantic follow-ups = `0`
- duplicate semantic request actions = `0`
- due follow-up directly calls Outlook = `0`
- due follow-up directly calls Asana = `0`
- LLM-selected follow-up timing = `0`
- LLM-generated action intent = `0`
- resolved questions remain in current follow-up context = `0`
- fully resolved inquiry retains obsolete follow-up = `0`
- obsolete request action remains executable = `0`
- follow-up directly mutates lifecycle = `0`
- follow-up directly marks inquiry dormant = `0`
- cross-case follow-up mutation = `0`
- stale waiting plan committed = `0`
- provider calls during waiting reconciliation = `0`

## Focused verification

Python:

- focused slice suite:
  - `python3 -m unittest tools.phase_08_workflow.tests.test_inquiry_waiting tools.phase_08_workflow.tests.test_orchestration_runtime tools.phase_08_workflow.tests.test_test_console_app tools.phase_08_workflow.tests.test_test_console_projection tools.phase_08_workflow.tests.test_test_console_service`
  - result: `59 / 59 PASS`
- full Phase 8 workflow suite:
  - `python3 -m unittest discover -s tools/phase_08_workflow/tests`
  - result: `166 / 166 PASS`
- Phase 7 reasoning suite:
  - `python3 -m unittest discover -s tools/phase_07_reasoning/tests`
  - result: `127 / 127 PASS`
- Phase 5 chunking suite:
  - `python3 -m unittest discover -s tools/phase_05_chunking/tests`
  - result: `27 / 27 PASS`
- Phase 5 search suite:
  - `python3 -m unittest discover -s tools/phase_05_search/tests`
  - result: `24 / 24 PASS`
- Phase 6 search suite:
  - `python3 -m unittest discover -s tools/phase_06_search/tests`
  - result: `5 / 6 PASS`, `1` environment failure
  - blocker: `load_active_historical_retrieval_model()` exited because no active retrieval-approved historical embedding model is registered in the local database

Supabase:

- local reset:
  - `npx -y supabase@latest db reset --local`
  - result: `PASS`
- targeted inquiry waiting DB proof:
  - `npx -y supabase@latest test db --local supabase/tests/42_phase_08_inquiry_waiting_follow_up_slice.sql`
  - result: `1 file / 7 tests PASS`
- full local Supabase sweep:
  - `npx -y supabase@latest test db --local supabase/tests`
  - result: `42 files / 1066 tests`, overall `FAIL`
  - unrelated existing failure:
    - `supabase/tests/18_phase_05_bulk_chunking_coverage.sql`
    - `8 / 9` subtests failed because the expected bulk chunk-set fixtures were absent after reset

## Scenario coverage

No dedicated automated scenario runner for the requested realistic rental scenarios was discovered in the repository during this slice.

Equivalent slice coverage was validated through focused tests:

- Scenario `1` Straightforward Venue Inquiry:
  - covered by complete-inquiry no-follow-up assertions
- Scenario `2` Incomplete Inquiry:
  - covered by scheduled single-follow-up assertions
- Scenario `11` Follow-Up:
  - covered by due action creation and sequence-2 progression assertions
- Scenario `12` Stale Client Email Action:
  - covered by obsolete request action supersession plus execution rejection
  - note: action intent remains structured internal workflow state, not a real email send
- Scenario `18` Human Working Proposal Audit:
  - covered by projection and console tests showing numbered follow-up detail and missing-field context
- Scenario `20` Empty / New Rental:
  - covered by no-follow-up / no-action assertions plus existing console empty-state tests

## Performance

Local in-memory slice timings on Friday, August 14, 2026:

- inquiry waiting evaluation:
  - median `0.542 ms`
  - slowest `2.530 ms`
- due follow-up evaluation:
  - median `0.475 ms`
  - slowest `0.829 ms`
- partial-response action refresh:
  - median `0.691 ms`
  - slowest `1.120 ms`

These are deterministic in-memory measurements only, not full end-to-end database timings.

## Limitations

- Warm-lead scoring was not invented; the first implementation stays deterministic and primarily supports the cold inquiry path plus time-critical escalation.
- The console now exposes inquiry waiting and follow-up work clearly, but the realistic rental scenarios were not rerun through a dedicated automated scenario harness because none was found in the live repository.
- Formal repo-wide readiness remains blocked by unrelated baseline regressions outside this slice.
