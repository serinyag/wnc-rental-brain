# Phase 8.7A Asana External Adapter Readiness

Date:

- August 13, 2026

Status:

- `READY_FOR_PHASE_8_CLIENT_FACING_ADAPTER_ROLLOUT`

## Readiness Decision

Phase 8.7A has now proven the first real external provider boundary safely enough to hand off to the next controlled client-facing adapter slice.

This readiness judgment is based on the following now being true:

- one real provider was implemented without bypassing Phase 8.6
- Asana remained an external execution surface rather than workflow authority
- configuration, auth failure, malformed responses, and ambiguity all fail closed
- successful provider identity is persisted on the existing execution-attempt record
- duplicate external-reference corruption is blocked in both Python and Supabase paths
- approval, blocked, stale, superseded, cancelled, and already-succeeded protections remain intact
- no direct lifecycle, blocker, requirement, or `CaseDecision` mutation can occur from Asana execution
- full Python and DB regressions remain green

## Why The Next Marker Uses This Name

The repository already established the immediate upstream marker:

- `READY_FOR_PHASE_8_EXTERNAL_ADAPTER_ROLLOUT`

The roadmap then describes the next progression inside workstream 7 as moving from internal projection surfaces toward human-reviewed outbound behavior.

No later frozen marker string existed in the repository before this phase, so the next marker has been formalized here using the existing naming style:

- `READY_FOR_PHASE_8_CLIENT_FACING_ADAPTER_ROLLOUT`

This is intentionally narrower than “all external systems ready” and intentionally later than “first external adapter rollout.”

## Required Conditions Met

- Asana adapter uses the provider-neutral execution interface
- execution always flows through `WorkflowAction -> execution_runtime -> ExecutionAttempt -> adapter registry -> adapter -> NormalizedExecutionResult`
- credentials are environment-loaded and not persisted into workflow history
- action-to-provider mapping is deterministic and governed
- verified success requires a valid Asana task GID
- ambiguous transport outcomes do not count as success
- external task identity is persisted and protected against cross-case corruption
- deterministic fake adapters remain available for non-live coverage
- no Outlook or other additional real adapter was introduced

## Residual Boundaries

Still intentionally outside this readiness marker:

- Outlook send or draft creation
- any client-visible email release flow
- inbound Asana synchronization
- provider-side reconciliation workers
- autonomous retry schedulers
- any Phase 8.8 work

## Final Verdict

The first real external adapter rollout is complete and regression-clean.

Canonical downstream marker:

- `READY_FOR_PHASE_8_CLIENT_FACING_ADAPTER_ROLLOUT`
