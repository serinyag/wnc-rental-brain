# Phase 8 Workflow Architecture Readiness

Date:

- August 9, 2026

Status:

- `PHASE_8_0B_ARCHITECTURE_READINESS_COMPLETE`

## Purpose

Record the final architecture-readiness judgment for Phase 8.0B after freezing the workflow execution architecture, lifecycle model, domain model, action taxonomy, and Phase 7 workflow consumption boundary.

## Repository Areas Inspected

Architecture and decision records inspected:

- `docs/phase-08/PHASE_8_WORKFLOW_BUSINESS_DECISIONS.md`
- `docs/phase-08/PHASE_8_WORKFLOW_DISCOVERY_EVIDENCE_AUDIT.md`
- `docs/phase-08/PHASE_8_WORKFLOW_DISCOVERY_READINESS.md`
- `docs/phase-08/PHASE_8_WORKFLOW_EVIDENCE_MATRIX.md`
- `docs/phase-08/PHASE_8_WORKFLOW_UNRESOLVED_DECISIONS.md`
- `docs/phase-08/PHASE_8_CLOSED_PHASE_CONTRADICTION_REMEDIATION.md`

Phase 7 and contract surfaces inspected:

- `tools/phase_07_reasoning/contracts.py`
- `docs/phase-07/PHASE_7_CLOSURE.md`

Schema and repository-convention areas inspected:

- `supabase/migrations/20260803000100_phase_04_foundation.sql`
- `supabase/migrations/20260806000100_phase_05_core_governance_foundation.sql`
- `supabase/migrations/20260806000400_phase_05_semantic_chunking_foundation.sql`
- `docs/phase-04/architecture/table-specifications.md`
- `docs/phase-04/architecture/schema-boundaries.md`

Primary source artifacts inspected:

- `sources/phase-01-03/Client Facing Docs/WNC Rental Agreement Template.docx`
- `sources/phase-01-03/Venue & Operations/WNC Venue Rental Operations Manual.docx`
- `sources/phase-01-03/Checklists + Templates/WNC Rental Event Handover & Final Readiness Checklist.docx`
- `sources/phase-01-03/Checklists + Templates/WNC Rental Close-Out Checklist.docx`
- `sources/phase-01-03/Checklists + Templates/Proposal Templates/Entire Venue Proposal Template.docx`
- `sources/phase-01-03/Checklists + Templates/WNC Rental Email Template Library.docx`
- `sources/phase-01-03/Knowledge Governance/WNC Rental Data Dictionary.xlsm`

## Canonical Architecture Decisions Frozen

### Aggregate And Persistence Model

Frozen choice:

- `RentalCase` is the canonical aggregate root
- current-state records plus append-only history is the recommended persistence strategy
- full event sourcing is not required

Why this is sufficient:

- it matches the human-approved business notion of one rental over time
- it supports practical operational querying
- it preserves replay and audit without making every read reconstruct from scratch

### Lifecycle States Frozen

Frozen canonical states:

1. `inquiry_active`
2. `proposal_in_progress`
3. `proposal_pending_client`
4. `confirmation_pending`
5. `confirmed_pre_event`
6. `event_ready`
7. `event_in_progress`
8. `close_out_in_progress`
9. `dormant`
10. `closed`
11. `closed_lost`
12. `cancelled`

Important modeling note:

- the business distinction for `EVENT_COMPLETE` is preserved through `event_completed` event and milestone semantics rather than as a 13th canonical lifecycle state

### State-Transition Model Frozen

Frozen position:

- the lifecycle is an application-controlled state machine
- confirmed rentals do not rewind into pre-confirmation states
- `dormant` reactivation must preserve an explicit resume target
- terminal states reopen only through auditable manual override

### Event Model Frozen

Frozen position:

- `WorkflowEvent` is the append-only fact log
- events trigger evaluation but do not directly mutate truth on their own
- event, change, approval, action, execution, and transition history remain separable

### Open-Question, Requirement, And Blocker Model Frozen

Frozen position:

- `OpenQuestion` tracks unknowns
- `Requirement` tracks what must become true
- `Blocker` tracks what currently prevents safe progression
- blocker resolution is modeled as an explicit structured loop rather than disappearing into notes or email

### Case-Truth And Decision Model Frozen

Frozen position:

- global truth remains anchored in Phase 4
- case-specific truth may exist only through active approved `CaseDecision`
- conflicting active case decisions fail closed
- case-specific truth never rewrites global policy rows

### Proposed-Change, Impact, And Rescheduling Model Frozen

Frozen position:

- material inbound changes become `ProposedCaseChange`
- impact is classified as `low_impact`, `material_impact`, or `fundamental_scope_change`
- rescheduling is represented by specialized `RescheduleRequest` records plus linked proposed changes
- active case date does not change until explicit confirmation is recorded

### Approval Model Frozen

Frozen position:

- approval posture is application-controlled
- posture values are `automatic_allowed`, `approval_required`, `human_only`, and `blocked`
- approval requests are interface-independent records, not UI-specific decisions

### Action, Execution, And Idempotency Model Frozen

Frozen position:

- `WorkflowAction` is structured intent
- `ExecutionAttempt` is a separate append-only execution record
- no success-dependent state advance happens without verified execution success
- external actions use stable semantic idempotency keys

### Follow-Up, Deadline, And Artifact-Freshness Model Frozen

Frozen position:

- `FollowUp` is first-class waiting state
- deadlines and milestones are first-class timing records
- artifacts are projections of canonical case truth
- material case changes may mark downstream artifacts stale without automatically refreshing them

### Audit, Replay, And Manual Override Model Frozen

Frozen position:

- the hybrid current-state plus append-only-history model is sufficient for deterministic replay
- manual override is explicit, auditable, and non-destructive
- manual closure is allowed when automation no longer adds meaningful value

### Interpretation, Drafting, And Integration Boundaries Frozen

Frozen position:

- extraction is provisional and does not directly mutate truth
- generated wording may draft communication but does not decide workflow intent
- adapters execute structured actions but do not own business authority
- n8n may act as scheduler or glue, not as the workflow engine

### Phase 7 To Phase 8 Contract Frozen

Frozen position:

- Phase 8 consumes structured `ContextPackage`
- `AnswerGenerationInput` and `AnswerResult` are limited to human-facing packaging and audit use
- freeform `answer_text` is not workflow truth
- authority, contamination, conflict, degraded-retrieval, confidentiality, and warning signals may influence workflow safety posture only through structured fields

## Phase 8 Invariants Frozen

The following architecture invariants are now frozen:

- active rentals always have explicit lifecycle state
- state transitions are application-controlled
- structured Phase 7 output, not prose, informs workflow reasoning
- Phase 4 remains global deterministic authority
- historical precedent never silently becomes current policy
- missing authority becomes blocker, review, or confirmation state
- material changes remain proposed until resolved
- approvals are enforced application-side
- adapters cannot silently advance business state
- external execution is idempotency-protected
- actions, approvals, changes, and executions remain auditable

## MVP Workflow Architecture Frozen

Frozen MVP slice:

```text
new inquiry
-> case creation or update
-> structured observation capture
-> open questions and requirements
-> Phase 7 support when needed
-> structured workflow action
-> human review
-> send
-> wait for response
-> proposed change or answer capture
-> deterministic re-evaluation
```

This is sufficient to start implementation without payment, calendar, event-day, RAG, agent, or persistence-layer extras beyond the frozen workflow foundation.

## Remaining Unresolved Non-Blocking Questions

The following remain open and should stay configurable or human-routed in implementation:

- `WD-003` discovery-call versus site-visit trigger matrix
- `WD-013` security-deposit matrix
- `WD-014` venue-clearing lead time and prerequisites
- `WD-015` professional-cleaning trigger
- `WD-016` unusual-material approver identity
- `WD-017` staffing matrix

These are implementation-relevant but not architecture-blocking.

## Files Created By Phase 8.0B

- `docs/phase-08/PHASE_8_WORKFLOW_EXECUTION_ARCHITECTURE.md`
- `docs/phase-08/PHASE_8_RENTAL_LIFECYCLE_STATE_TRANSITION_MATRIX.md`
- `docs/phase-08/PHASE_8_WORKFLOW_DOMAIN_MODEL.md`
- `docs/phase-08/PHASE_8_WORKFLOW_ACTION_TAXONOMY.md`
- `docs/phase-08/PHASE_8_PHASE7_WORKFLOW_CONSUMPTION_CONTRACT.md`
- `docs/phase-08/PHASE_8_IMPLEMENTATION_ROADMAP.md`
- `docs/phase-08/PHASE_8_WORKFLOW_ARCHITECTURE_READINESS.md`

## Files Modified By Phase 8.0B

- `docs/phase-08/PHASE_8_WORKFLOW_ACTION_TAXONOMY.md` after creation to normalize an action-code spelling issue

## Blockers

Architecture blockers remaining:

- none

Implementation cautions remaining:

- unresolved configurable-policy areas must not be hard-coded as deterministic truth during the first implementation pass

## Final Judgment

The repository now has:

- a canonical aggregate model
- frozen lifecycle states
- a deterministic transition model
- explicit event, requirement, blocker, approval, action, execution, freshness, and override semantics
- a frozen Phase 7 to Phase 8 machine boundary
- a practical implementation roadmap

READY_FOR_PHASE_8_WORKFLOW_FOUNDATION_IMPLEMENTATION
