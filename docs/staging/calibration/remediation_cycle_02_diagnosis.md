# Calibration Remediation Cycle 2 Diagnosis

## Scope

This diagnosis is driven by the frozen failed unseen holdout, not by the original 32-case benchmark.

Frozen evidence:

- `/Users/serinya/Documents/WNC Rental Automation/docs/staging/calibration/holdout_scenarios.json`
- `/Users/serinya/Documents/WNC Rental Automation/docs/staging/calibration/holdout_report_latest.md`
- `/Users/serinya/Documents/WNC Rental Automation/docs/staging/calibration/holdout_results_latest.json`

## Root Cause Summary

Cycle 1 improved the original benchmark, but it did not establish a general semantic-state contract. The staging path still lost semantic polarity in two places:

1. the staging semantic bridge in `tools/phase_08_workflow/test_console_service.py`
2. the holdout scorer in `tools/staging_calibration/run_holdout_generalization.py`

That meant unseen cases were still vulnerable to this collapse:

`no explicit blocker mapping` -> `no issue synthesized` -> effective `known_yes`

The system therefore overfit to benchmark-shaped blocker patterns instead of preserving the real distinction between:

- supported
- restricted
- conditional
- internally unknown
- missing client fact

## First Incorrect Transitions

### 1. Technical requests silently fell through

The pre-cycle staging bridge only synthesized technical issues for a tiny hard-coded subset:

- `microphones`
- `dj_sound_booth`
- `power_requirements`
- `other_technical`

Unmapped normalized asks such as:

- `acoustic_noise`
- `branding_signage`
- `livestream_recording`
- mixed supported-plus-unknown combinations

produced no synthetic authority projection at all.

That was the first incorrect transition for:

- `HOLD-002`
- `HOLD-003`
- `HOLD-007`
- `HOLD-010`

### 2. Capacity semantics were flattened into confirmation

The staging bridge treated any non-`within_capacity` result as a confirmation-style issue and used a broad published studio max fallback that could suppress internal uncertainty completely.

That broke two distinct meanings:

- `exceeds_capacity` should remain `known_no`
- `insufficient_information` / `no_applicable_rule` should remain `unknown_internal`

This was the first incorrect transition for:

- `HOLD-004`
- `HOLD-005`

### 3. Approval-gated exception paths were flattened by the holdout scorer

`HOLD-009` already preserved the important workflow shape:

- baseline booking fee remained intact
- a proposed case decision existed
- approval gating remained explicit

But the holdout scorer only classified:

- `missing_client_fact`
- `unknown_internal`
- `known_yes`

So an approval-gated exception path could not be recognized as a governed `known_no` baseline with optional exception handling.

## Why Cycle 1 Passed The 32-Case Benchmark Anyway

Cycle 1 succeeded on the original benchmark because it improved the visible blocker and review behavior for benchmark-known shapes. But it mostly operated at the symptom level:

- add or preserve blocker creation
- prevent a few obvious unsafe yes-paths
- align known benchmark workflows

It did not force the system to carry explicit semantic polarity through the Phase 7 to Phase 8 staging boundary.

That is why the first unseen holdout exposed major failures even after the benchmark passed.

## Smallest General Fix

The smallest generalized fix is not a new architecture. It is a preserved semantic-state contract on the existing `WorkflowReasoningProjection`.

Cycle 2 therefore:

1. derives a dominant semantic state in Phase 7 consumption
2. stores it in `degraded_retrieval_summary.semantic_state_code`
3. makes the staging test-console bridge synthesize explicit semantic states for technical, capacity, and facilitator authority issues
4. creates a deterministic restriction effect for `known_no`
5. makes the holdout classifier read semantic-state projections instead of inferring solely from blocker presence

## Expected Post-Remediation Behavior

After this fix:

- unsupported technical asks remain deterministic restrictions
- missing current internal authority remains fail-closed review
- conditional governed support remains conditional
- missing client facts still route to client questions
- approval-gated exception paths stop being mislabeled as generic internal uncertainty

## Non-Goals

This cycle does not:

- hard-code holdout IDs
- build a new workflow engine
- add a new database schema
- replace the Phase 7 or Phase 8 architecture

The remediation is intentionally small and semantic rather than benchmark-specific.
