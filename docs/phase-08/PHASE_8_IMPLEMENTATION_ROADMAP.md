# Phase 8 Implementation Roadmap

Date:

- August 9, 2026

Status:

- `PHASE_8_0B_IMPLEMENTATION_SEQUENCE_PROPOSED`

## Purpose

Translate the frozen 8.0B architecture into an implementation sequence without implementing the runtime in this phase.

This roadmap is intentionally:

- architecture-aligned
- MVP-first
- progressive in autonomy
- explicit about what remains manual or configurable

## Non-Goals

This roadmap does not itself perform:

- database migrations
- runtime coding
- external integrations
- agent orchestration
- production automation

## Recommended Delivery Strategy

Build Phase 8 in layers that preserve deterministic business control at every step.

Recommended order:

1. persistence and audit foundation
2. lifecycle and guard evaluation
3. inbound observation and proposed-change handling
4. Phase 7 workflow consumption
5. approval, blocker, and action orchestration
6. execution, follow-up, and projection refresh support
7. external adapter rollout

## Workstream 1: Persistence Foundation

Primary objective:

- create the canonical workflow data model around `RentalCase`

Recommended scope:

- `RentalCase`
- lifecycle transition history
- `WorkflowEvent`
- `OpenQuestion`
- `Requirement`
- `Blocker`
- `CaseDecision`
- `ProposedCaseChange`
- `RescheduleRequest`
- `ApprovalRequest`
- `WorkflowAction`
- `ExecutionAttempt`
- `FollowUp`
- `Deadline` or `Milestone`
- `ArtifactReference`

Key implementation requirements:

- current-state plus history hybrid model
- append-only event and execution history
- status fields with constrained text semantics
- explicit supersession links
- `updated_at` discipline consistent with repository conventions

Exit condition:

- the schema can represent the frozen 8.0B domain model without adapters or UI

## Workstream 2: Lifecycle And Guard Engine

Primary objective:

- implement application-controlled lifecycle transitions

Recommended scope:

- lifecycle state evaluator
- transition guard library
- dormant reactivation rules
- readiness evaluation
- terminal-state rules
- manual override hooks

Key implementation requirements:

- no LLM-selected transitions
- deterministic target-state guard checks
- explicit blocker creation for failed guards
- append-only transition history

Exit condition:

- the application can evaluate and persist legal lifecycle transitions from structured inputs

## Workstream 3: Inbound Observation And Change Handling

Primary objective:

- ingest external or internal observations without mutating truth prematurely

Recommended scope:

- inbound event normalization
- proposed observation capture
- open-question creation
- proposed-case-change creation
- change-impact classification
- reschedule request handling

Key implementation requirements:

- extraction remains provisional
- material changes remain proposed until resolved
- event-to-change pipeline is auditable

Exit condition:

- inbound email, note, or operator input can become structured proposed workflow state safely

## Workstream 4: Phase 7 Workflow Consumption

Primary objective:

- connect Phase 7 reasoning outputs to workflow evaluation through the frozen contract

Recommended scope:

- `ContextPackage` ingestion boundary
- authority outcome mapping
- unresolved-authority blocker creation
- contamination-aware safety gates
- degraded retrieval posture handling
- minimal reasoning snapshot persistence

Key implementation requirements:

- no parsing of `answer_text` as truth
- structured provenance retention only
- future compatibility with a dedicated `WorkflowReasoningProjection`

Exit condition:

- workflow evaluation can safely consume Phase 7 without conflating reasoning and truth

## Workstream 5: Approval, Blocker, And Action Orchestration

Primary objective:

- implement the structured operational loop that turns workflow state into reviewable intent

Recommended scope:

- approval policy engine
- `ApprovalRequest` creation and decision handling
- blocker creation and resolution loop
- `WorkflowAction` creation and supersession
- internal-control actions such as stale-artifact marking

Key implementation requirements:

- approval is application-controlled
- blockers are explicit, not hidden in prose
- action creation is separate from execution

Exit condition:

- the system can prepare approval-aware structured work without calling external adapters

## Workstream 6: Execution And Follow-Up Runtime

Primary objective:

- add safe execution tracking and revisit loops

Recommended scope:

- `ExecutionAttempt` runtime
- idempotency-key generation and reuse
- retry policy
- follow-up cadence handling
- due and overdue evaluation
- stale-action supersession
- artifact freshness recalculation

Key implementation requirements:

- no success-dependent state advance without verified success
- duplicate-execution protection
- schedulable follow-up model

Exit condition:

- the system can execute low-risk actions safely and track waiting state deterministically

## Workstream 7: Projection And External Adapter Rollout

Primary objective:

- progressively connect workflow actions to external systems

Recommended rollout order:

1. internal drafting and artifact refresh
2. internal task-surface projection
3. human-reviewed outbound email send
4. payment-request creation
5. calendar support
6. additional sync targets

Key implementation requirements:

- adapters remain transport and execution layers only
- business authority stays in the application
- every adapter path uses normalized execution results

Exit condition:

- external systems can be updated safely without becoming workflow truth stores

## Recommended MVP Slice

First shippable slice:

```text
new inquiry
-> create or update RentalCase
-> record WorkflowEvent
-> create OpenQuestion and Requirement records
-> use Phase 7 when needed for missing-information or authority evaluation
-> create REQUEST_CLIENT_INFORMATION action
-> human review
-> send
-> record response
-> create ProposedCaseChange if needed
-> re-evaluate state
```

Why this slice first:

- it exercises the aggregate root
- it validates lifecycle control
- it proves the Phase 7 contract
- it does not require payment, calendar, or event-day integrations

## Open Policy Placeholders That Must Stay Configurable

The following unresolved items should not block implementation of the foundation, but their logic must remain configurable or human-routed:

- discovery-call versus site-visit trigger matrix
- security-deposit matrix
- venue-clearing lead time and prerequisites
- professional-cleaning trigger
- unusual-material approver identity
- staffing matrix

Implementation consequence:

- do not hard-code universal policy in these areas during the first foundation pass

## n8n Placement

n8n may be introduced only after the application-controlled workflow model exists.

Recommended role for n8n:

- scheduler
- event transport
- integration glue

Not recommended for n8n:

- lifecycle engine
- case-truth authority
- approval source of truth
- hidden business-rule storage

## Suggested Delivery Sequence

1. Implement schema and persistence primitives.
2. Implement lifecycle evaluator and transition history.
3. Implement event normalization plus proposed-change pipeline.
4. Implement Phase 7 contract boundary and reasoning snapshot persistence.
5. Implement blocker, requirement, approval, and action orchestration.
6. Implement execution attempts, idempotency, and follow-up scheduling.
7. Roll out drafting and low-risk sync adapters.
8. Expand into approved external sends and payment/calendar support.

## Readiness For The Next Phase

This roadmap assumes the repository proceeds into workflow foundation implementation next, not back into discovery.

It is compatible with the frozen 8.0B architecture because:

- the blocking business decisions have been resolved
- the domain model is explicit
- the Phase 7 machine boundary is now frozen
- the remaining unknowns are implementation-configurable rather than architecture-blocking

## Conclusion

The recommended implementation path is:

- `RentalCase` and audit foundation first
- deterministic lifecycle engine second
- Phase 7 contract integration before external automation
- progressive autonomy only after approval, idempotency, and audit controls exist

This is the authoritative Phase 8 implementation roadmap following 8.0B.
