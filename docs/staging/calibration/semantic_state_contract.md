# Semantic State Contract

## Purpose

Calibration Remediation Cycle 2 formalizes a small semantic contract across the Phase 7 to Phase 8 boundary so staging workflow behavior no longer treats absence of prohibition as affirmative support.

The workflow consumer must preserve the difference between:

- `known_yes`
- `known_no`
- `known_conditional`
- `unknown_internal`
- `missing_client_fact`

## Canonical Meanings

### `known_yes`

Use when current governed rules positively support the requested commitment as stated.

Expected workflow consequence:

- no internal confirmation blocker
- no deterministic restriction blocker
- the system may continue using the governed answer

Typical underlying evidence:

- `support_status in {'supported', 'standard', 'available_on_request'}`
- `capacity_evaluation_status = 'within_capacity'`
- `arrangement_status = 'allowed'`

### `known_no`

Use when current governed rules deterministically disallow the requested commitment as stated.

Expected workflow consequence:

- emit a deterministic restriction effect
- create a deterministic restriction blocker
- do not downgrade to confirmation-only handling

Typical underlying evidence:

- `support_status in {'external_supplier_required', 'not_available'}`
- `capacity_evaluation_status in {'exceeds_capacity', 'not_event_capacity_space'}`
- an approval-gated exception path where baseline governed policy remains unchanged pending approval

### `known_conditional`

Use when current governed rules explicitly define support as conditional rather than unsupported or unknown.

Expected workflow consequence:

- surface confirmation/review as the exact condition
- do not silently treat the request as supported

Typical underlying evidence:

- `support_status = 'requires_confirmation'`
- `arrangement_status = 'conditional'`
- explicit `requires_confirmation` flags in current governed payload

### `unknown_internal`

Use when the client request is clear enough to evaluate, but the current governed surface does not provide an authoritative yes/no answer.

Expected workflow consequence:

- fail closed
- create internal review / current-authority-missing handling
- do not ask the client for a fact the client already supplied

Typical underlying evidence:

- `capacity_evaluation_status in {'insufficient_information', 'no_applicable_rule'}`
- unmapped or uncovered normalized technical asks
- facilitator manual review states
- current-authority gaps preserved from Phase 7 unresolved authority

Important boundary:

`unknown_internal` is not the same as `known_conditional`.

If the governed surface does not say "yes, under this exact condition", the system must not synthesize a conditional yes.

### `missing_client_fact`

Use when a known rule exists, but the client has not yet supplied a required fact to apply it.

Expected workflow consequence:

- create or preserve an `OpenQuestion`
- request the missing fact from the client
- do not create an internal-only authority review in place of the client question

## Preservation Rules Across Phase 7 → Phase 8

Phase 7 authoritative items or unresolved authority must be reduced into a single dominant semantic state for each reasoning projection.

Priority order:

1. `known_no`
2. `unknown_internal`
3. `known_conditional`
4. `known_yes`

That semantic state must be stored on the projection in `degraded_retrieval_summary.semantic_state_code` so downstream orchestration and staging calibration can read the same contract without a schema migration.

## Forbidden Equivalences

The following collapses are not allowed:

- `nothing authoritative says no` = `known_yes`
- `known_no` = `known_conditional`
- `unknown_internal` = `missing_client_fact`
- `approval-gated exception` = `unknown_internal`

## Current Cycle 2 Implementation Boundary

This cycle keeps the existing architecture and uses the current `WorkflowReasoningProjection` shape. No migration is required.

The contract is enforced by:

- Phase 7 workflow consumption semantic-state derivation
- staging test-console synthetic authority projections
- orchestration deterministic restriction handling
- holdout classification consuming the same semantic-state field
