# Phase 8 Execution & Follow-Up Runtime Evaluation

Date:

- August 13, 2026

Status:

- `PHASE_8_6_EVALUATION_COMPLETE`

## Scope Evaluated

Phase 8.6 evaluates the deterministic execution runtime that moves persisted governed `WorkflowAction` records through:

- execution eligibility validation
- provider-neutral adapter resolution
- deterministic fake/test adapter invocation
- `ExecutionAttempt` persistence
- normalized execution result handling
- controlled action terminal or retry posture updates
- structured follow-up status evaluation and follow-up-driven orchestration re-entry

Explicitly out of scope:

- live external providers
- autonomous retry loops
- RAG, agents, UI, or persistence beyond the Phase 8 workflow store
- anything from Phase 8.7 or later

## Inspection Summary

Live repository inspection confirmed:

1. execution-related contracts already existed for `WorkflowAction`, `ExecutionAttempt`, approval posture, action supersession, and case-revision binding
2. `workflow_execution_attempts` already existed in the schema, but its blanket append-only update trigger conflicted with completion-state mutation and required a controlled remediation
3. `FollowUp` and its frozen statuses already existed with due timing, cadence, escalation, and attempt-count fields
4. action idempotency already used semantic subject hashing plus `source_case_revision` and `idempotency_key`
5. atomic DB mutation patterns already used narrow `private.commit_phase8_*` helper functions
6. the exact pre-implementation readiness marker in use was `READY_FOR_PHASE_8_EXECUTION_AND_FOLLOW_UP_RUNTIME`
7. there was no architectural blocker, but the execution-attempt append-only trigger needed a narrow update guard so started attempts could be completed safely

## Repository Areas Evaluated

Architecture and readiness sources:

- `docs/phase-08/PHASE_8_WORKFLOW_EXECUTION_ARCHITECTURE.md`
- `docs/phase-08/PHASE_8_IMPLEMENTATION_ROADMAP.md`
- `docs/phase-08/PHASE_8_WORKFLOW_ACTION_TAXONOMY.md`
- `docs/phase-08/PHASE_8_APPROVAL_BLOCKER_ACTION_READINESS.md`

Live implementation surfaces:

- `tools/phase_08_workflow/contracts.py`
- `tools/phase_08_workflow/validation.py`
- `tools/phase_08_workflow/orchestration_repository.py`
- `tools/phase_08_workflow/orchestration_runtime.py`
- `tools/phase_08_workflow/execution_types.py`
- `tools/phase_08_workflow/execution_runtime.py`
- `tools/phase_08_workflow/__init__.py`
- `tools/phase_08_workflow/tests/test_execution_runtime.py`
- `tools/phase_08_workflow/tests/test_orchestration_runtime.py`
- `supabase/migrations/20260813000300_phase_08_execution_follow_up_runtime.sql`
- `supabase/tests/40_phase_08_execution_follow_up_runtime.sql`

## Acceptance Coverage

Focused Phase 8.6 runtime coverage now proves:

- ready-to-execute actions can execute through deterministic fake adapters only
- `human_only` actions never enter the automated execution path
- retry-eligible failures return the same action to `ready_to_execute`
- unavailable adapters fail closed before attempt creation
- malformed adapter results never become success
- adapter exceptions never become success
- already-succeeded actions short-circuit idempotently without duplicate invocation
- due follow-ups route back into normal orchestration and never directly invoke adapters
- completed and cancelled follow-ups are not reactivated
- successful follow-up-origin actions complete the related follow-up
- attempted follow-ups can become overdue or escalated deterministically

Focused DB coverage now proves:

- execution start atomically creates a started attempt and flips action state to `executing`
- execution completion atomically finalizes attempt state and action state
- retry-eligible failures return actions to `ready_to_execute`
- `human_only` actions are rejected before attempt creation
- follow-up status updates are atomic and auditable
- completed follow-ups fail closed on invalid reactivation
- terminal attempts cannot be completed twice

## Verification Results

Focused Phase 8.6 Python coverage:

- `python3 -m pytest tools/phase_08_workflow/tests/test_execution_runtime.py tools/phase_08_workflow/tests/test_orchestration_runtime.py -q`
- result: `25 / 25` passing

Full Phase 8 Python suite:

- `python3 -m pytest tools/phase_08_workflow/tests -q`
- result: `85 / 85` passing

Focused Phase 8.6 DB coverage:

- `npx -y supabase@latest test db --local supabase/tests/40_phase_08_execution_follow_up_runtime.sql`
- result: `12 / 12` assertions passing

Full DB regression:

- `npx -y supabase@latest test db --local`
- result: `40` files, `1054` tests, `PASS`

Post-reset local verification restoration:

- `npx -y supabase@latest db reset --local`
- `python3 -m tools.phase_05_chunking.generate_bulk --load-db`
- restored current bulk chunk coverage to `22` current chunk sets and `525` generated chunks before rerunning the full DB regression

## Evaluation Metrics

- focused execution runtime scenarios: `12`
- focused orchestration carry-forward scenarios: `13`
- focused Phase 8.6 DB assertions: `12`
- execution success-path accuracy: `1.0`
- retry posture accuracy: `1.0`
- adapter-unavailable fail-closed accuracy: `1.0`
- malformed-result fail-closed accuracy: `1.0`
- duplicate success invocation count: `0`
- execution-attempt creation coverage for real invocations: `1.0`
- follow-up direct-execution violation count: `0`
- duplicate semantic follow-up action count from repeated due evaluation: `0`
- terminal follow-up reactivation count: `0`
- lifecycle mutation violation count: `0`

## Validation Notes

The most important Phase 8.6 repository contradiction was the original blanket append-only guard on `workflow_execution_attempts`.

That has now been narrowed into a controlled completion-update guard which still preserves immutable attempt identity while allowing the single legal `started -> terminal` mutation required by the execution runtime.

The runtime also intentionally skips immediate orchestration re-entry for retry-eligible failures. Without that guard, the planner could supersede the same action that had just been returned to `ready_to_execute`, which would destroy the controlled retry posture.

## Final Judgment

Phase 8.6 now passes its deterministic execution and follow-up acceptance slice for both the in-memory runtime and the persisted Supabase helper boundary.

Readiness outcome:

- `READY_FOR_PHASE_8_EXTERNAL_ADAPTER_ROLLOUT`
