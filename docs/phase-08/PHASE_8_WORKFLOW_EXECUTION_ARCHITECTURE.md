# Phase 8 Workflow Execution Architecture

Date:

- August 9, 2026

Status:

- `PHASE_8_0B_ARCHITECTURE_FROZEN`

## Objective

Freeze the application-controlled architecture that turns the Phase 4 through Phase 7 intelligence stack into a reliable, stateful rental workflow system.

This phase defines:

- canonical workflow concepts
- lifecycle semantics
- deterministic transition boundaries
- case-specific truth handling
- approval and execution safety boundaries
- auditability, idempotency, and failure semantics
- the exact machine boundary between Phase 7 and future workflow execution

This phase does not implement:

- runtime workflow code
- database migrations
- external integrations
- queues, schedulers, or UI

## Primary Architecture Position

The rental workflow is not an autonomous agent.

The workflow system must be:

- stateful
- deterministic where possible
- explicit about unresolved authority
- structured and auditable
- approval-aware
- failure-safe
- idempotent
- integration-independent

LLMs may help with:

- extraction
- summarization
- classification
- interpretation
- drafting

LLMs may not directly decide:

- lifecycle state
- state transition
- current policy
- approval requirement
- blocker resolution
- case-specific exception activation
- whether an adapter failure counts as success

## Relationship To Earlier Phases

### Phase 4

Owns:

- global current deterministic truth

Examples:

- pricing
- booking fee
- payment
- cancellation
- capacity
- access
- operational requirements
- technical capability
- service/facilitator rules

Phase 8 consumes Phase 4 but never rewrites it case-by-case.

### Phase 5

Owns:

- current governed knowledge

Phase 8 may use Phase 5 to identify:

- current workflow guidance
- operational requirements
- documentary expectations
- communication patterns

Phase 8 does not silently promote guidance into deterministic truth.

### Phase 6

Owns:

- historical precedent

Phase 8 may use Phase 6 only for:

- warning context
- similarity context
- operational pattern recognition

Historical precedent never becomes workflow policy automatically.

### Phase 7

Owns:

- query planning
- selective retrieval
- authority resolution
- contamination handling
- uncertainty
- confidentiality and PI safety
- generator-safe context
- bounded answer generation
- deterministic answer validation

Phase 8 must consume structured Phase 7 outputs.

Phase 8 must never infer workflow truth from generated answer prose.

## Frozen Architectural Principles

1. Canonical business state lives in the WNC rental workflow system.
2. Lifecycle state is explicit and persistent for every active rental.
3. State, blockers, requirements, approvals, actions, and artifacts are separate concepts.
4. Missing authority becomes structured workflow state, not invented certainty.
5. Material inbound changes remain proposed until resolved.
6. Case-specific truth is scoped to one `RentalCase` unless formally promoted through governance.
7. External tools are adapters, not the source of business truth.
8. Execution intent and execution result are separate records.
9. Verified success is required before success-dependent transitions occur.
10. Progressive automation is allowed only through application-controlled approval policy.

## Conceptual Runtime Pipeline

```text
Inbound Event
-> Normalize / Extract
-> RentalCase
-> Deterministic Workflow Evaluation
-> Phase 4-7 Intelligence When Needed
-> Structured Decision / Blocker / Requirement
-> WorkflowAction
-> Approval Gate
-> Execution Adapter
-> Verified Execution Result
-> State / Case Update
-> Next Evaluation
```

## Canonical Aggregate

Chosen aggregate root:

- `RentalCase`

Reason:

- it matches the human-approved Phase 8 concept of one rental opportunity/event over time
- it can carry opportunity, booking, pre-event, delivery, and close-out state without collapsing into one giant JSON blob
- it preserves the distinction between global policy and case-specific operational truth

### RentalCase Responsibilities

The `RentalCase` aggregate is responsible for:

- case identity
- canonical lifecycle state
- active event date or date range
- current scope snapshot
- client and primary-contact references
- commercial and operational summary posture
- case revision identity
- current stale-artifact summary
- links to related workflow records

The `RentalCase` aggregate is not responsible for embedding every dependent object inline.

### RentalCase Fields

Minimum conceptual fields:

| Field | Purpose |
| --- | --- |
| `rental_case_id` | stable case identifier |
| `case_reference_code` | human-facing stable reference |
| `lifecycle_state` | canonical workflow state |
| `case_revision` | monotonic revision for material truth changes |
| `active_event_date_start` | current active start date/time |
| `active_event_date_end` | current active end date/time |
| `rental_type_code` | canonical rental scope |
| `service_level_or_type` | current service scope |
| `client_account_ref` | external/internal client reference |
| `primary_contact_ref` | current primary contact reference |
| `commercial_summary_status` | summary only, not the primary transition engine |
| `operational_summary_status` | summary only, not the primary transition engine |
| `current_proposal_artifact_ref` | latest proposal projection reference |
| `current_agreement_artifact_ref` | latest agreement projection reference |
| `is_active` | convenience operational flag |
| `created_at` / `updated_at` | audit timestamps |

### RentalCase Boundaries

Do not store as one denormalized blob:

- open questions
- requirements
- blockers
- decisions
- approvals
- actions
- executions
- follow-ups
- deadlines
- artifact freshness

Those remain separate related records.

## Recommended Persistence Strategy

Recommended model:

- current-state tables for canonical entities
- append-only workflow event log
- append-only transition, approval, action, and execution history
- supersession links for mutable workflow records

Recommended approach:

- practical hybrid, not full event sourcing

Reason:

- current-state queries will be operationally simpler
- replay and audit still remain possible from append-only history
- full event sourcing is not required to meet reliability goals

## Lifecycle Model

Chosen canonical lifecycle states:

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

Why this shape:

- it is small enough to stay comprehensible
- it avoids encoding every task into state
- it preserves the key business distinctions discovered in Phase 8
- it supports the MVP inquiry-to-clarification slice
- it supports confirmed bookings without rewinding confirmed rentals back into pre-confirmation state

### State Versus Other Concepts

State answers:

- where is this rental in its business lifecycle

Requirement answers:

- what must be true for this rental

Blocker answers:

- what currently prevents a specific transition or action

Approval answers:

- what needs human authorization

Action answers:

- what the system intends to do

Follow-up answers:

- what the system is waiting on and when to revisit it

## Orthogonal Status Dimensions

To avoid state explosion, the architecture keeps several orthogonal dimensions out of lifecycle state.

Recommended summary dimensions:

| Dimension | Purpose |
| --- | --- |
| `commercial_summary_status` | whether proposal, payment, and agreement work are on track |
| `operational_summary_status` | whether planning, readiness, delivery, or close-out are at risk |
| `follow_up_summary_status` | whether the case is waiting, overdue, or escalated |
| `artifact_freshness_summary` | whether downstream projections are current or stale |

These are summary views.

They do not replace:

- canonical lifecycle state
- requirement records
- blocker records
- approval records

## WorkflowEvent Model

`WorkflowEvent` is the canonical fact log.

An event means:

> something happened

Events are never instructions.

Examples:

- `inquiry_received`
- `client_information_received`
- `proposal_sent`
- `client_response_received`
- `payment_received`
- `requirement_status_changed`
- `blocker_resolved`
- `approval_decided`
- `action_execution_succeeded`
- `action_execution_failed`
- `reschedule_requested`
- `event_completed`
- `manual_close_requested`

### Event Design Rules

- events are append-only
- events preserve source, actor, timestamp, and payload reference
- events may trigger deterministic evaluation
- events do not directly mutate state without workflow evaluation

## OpenQuestion

`OpenQuestion` represents information the workflow still needs.

Recommended fields:

| Field | Purpose |
| --- | --- |
| `open_question_id` | stable identifier |
| `rental_case_id` | owning case |
| `question_type` | structured category |
| `domain_code` | commercial, timing, supplier, compliance, and similar |
| `human_question_text` | clear human-facing wording |
| `blocking_scope` | none, action, transition, readiness, or commercial scope |
| `requested_from_role` | client, WNC, supplier, facilitator, or unknown |
| `status` | `open`, `answered_pending_validation`, `resolved`, `closed_not_needed`, `superseded` |
| `proposed_answer_payload` | candidate answer/value |
| `source_reference` | where the answer came from |
| `created_at` / `resolved_at` | audit timestamps |

Open questions are not hidden inside prose.

## Requirement

`Requirement` is distinct from an open question.

A requirement may exist even when no literal question exists.

Examples:

- confirmation payment required
- signed agreement required
- supplier details required
- final event-day contact required
- WNC staffing confirmation required
- permit requirement exists

Recommended statuses:

- `not_applicable`
- `required`
- `in_progress`
- `satisfied`
- `waived`
- `unresolved`

Recommended fields:

| Field | Purpose |
| --- | --- |
| `requirement_id` | stable identifier |
| `rental_case_id` | owning case |
| `requirement_type` | structured requirement family |
| `domain_code` | commercial, compliance, staffing, timeline, and similar |
| `applicability_basis` | why it applies |
| `owner_role` | who must drive it |
| `due_at` | milestone/deadline |
| `status` | requirement state |
| `blocking_scope` | what it can block |
| `evidence_reference` | supporting source or case evidence |
| `waiver_decision_id` | optional link to approved case-specific waiver |
| `created_at` / `resolved_at` | audit timestamps |

## Blocker

`Blocker` means:

> a defined workflow progression cannot safely occur until something is resolved

Examples:

- proposal cannot be sent
- confirmation cannot complete
- event cannot become ready
- external action cannot execute

Recommended fields:

| Field | Purpose |
| --- | --- |
| `blocker_id` | stable identifier |
| `rental_case_id` | owning case |
| `blocker_type` | missing info, approval required, authority unresolved, payment pending, and similar |
| `blocked_subject_type` | transition, action, readiness, decision, or artifact refresh |
| `blocked_subject_id` | the exact transition/action/decision affected |
| `origin_entity_type` | requirement, question, change, approval, decision, or system guard |
| `origin_entity_id` | source record |
| `severity` | low, medium, high |
| `status` | `open`, `resolved`, `superseded`, `cancelled` |
| `resolution_condition_text` | what must become true |
| `resolution_reference` | evidence or linked record proving resolution |
| `opened_at` / `resolved_at` | audit timestamps |

## Blocker Resolution Loop

```text
blocker detected
-> resolution question / requirement / approval / action created
-> resolution evidence arrives
-> structured record updated
-> guard re-evaluated
-> blocker resolves or remains open
-> workflow continues only if guard now passes
```

The workflow may automate the resolution process.

It may not invent the resolution.

## CaseDecision

`CaseDecision` is the first-class model for case-specific operational truth.

It exists because a rental-specific exception must not rewrite Phase 4 global truth.

Examples:

- booking fee waived for one rental
- custom setup access approved
- unusual payment term approved
- special supplier arrangement approved
- case-specific commercial exception approved

Recommended fields:

| Field | Purpose |
| --- | --- |
| `case_decision_id` | stable identifier |
| `rental_case_id` | owning case |
| `decision_type` | waiver, override, exception, special approval, and similar |
| `domain_code` | booking_fee, payment, access, staffing, supplier, and similar |
| `baseline_reference` | relevant Phase 4 or Phase 5 baseline |
| `proposed_value_payload` | candidate case-specific value |
| `scope_description` | what exactly the decision applies to |
| `evidence_reference` | supporting case evidence |
| `authority_basis` | why this decision is allowed |
| `approval_state` | workflow approval posture |
| `status` | `proposed`, `pending_approval`, `active`, `rejected`, `superseded`, `withdrawn` |
| `effective_at` | activation timestamp |
| `supersedes_case_decision_id` | previous case decision replaced |

## Effective Case Truth Resolution

Deterministic precedence:

```text
Phase 4 global deterministic truth
+ active approved CaseDecision
= effective case value
```

Resolution rules:

1. If no active case decision exists, the Phase 4 baseline remains effective.
2. Only `active` case decisions may affect effective truth.
3. `proposed` or `pending_approval` decisions do not affect truth.
4. `superseded` and `rejected` decisions do not affect truth.
5. Conflicting active case decisions in the same scope fail closed and create a blocker.
6. A case-specific decision may override only its declared scope.
7. Case-specific truth never rewrites the global rule row.

## ProposedCaseChange

`ProposedCaseChange` preserves material inbound change before activation.

Recommended fields:

| Field | Purpose |
| --- | --- |
| `proposed_case_change_id` | stable identifier |
| `rental_case_id` | owning case |
| `change_kind` | field update, scope change, date change, supplier change, and similar |
| `domain_code` | affected domain |
| `prior_value_payload` | value before change |
| `proposed_value_payload` | candidate replacement |
| `source_reference` | email, note, call summary, or internal input |
| `detected_at` | when identified |
| `impact_classification` | low, material, or fundamental |
| `affected_domains` | downstream domains to reassess |
| `review_requirement` | automatic, review required, approval required |
| `status` | `proposed`, `under_review`, `accepted`, `rejected`, `superseded`, `withdrawn` |
| `final_value_payload` | accepted value where applicable |

## Change Impact Model

Chosen model:

- `low_impact`
- `material_impact`
- `fundamental_scope_change`

Decision logic should combine:

- deterministic thresholds where known
- Phase 4 deterministic outputs where available
- Phase 5 current governed guidance where relevant
- Phase 7 authority and unresolved-state output
- human review when ambiguity remains

Default safety rule:

- unresolved or ambiguous impact classification defaults toward human review

## Rescheduling Model

Chosen structure:

- specialized `RescheduleRequest`
- linked to one or more `ProposedCaseChange` rows

Reason:

- date negotiation is multi-step and cannot be cleanly represented as one generic field update

Recommended fields:

| Field | Purpose |
| --- | --- |
| `reschedule_request_id` | stable identifier |
| `rental_case_id` | owning case |
| `current_active_date_payload` | current booked date/time |
| `requested_date_payload` | client-requested alternative |
| `candidate_dates_payload` | WNC-proposed options |
| `consequence_summary_payload` | pricing, staffing, class, supplier, and readiness effects |
| `status` | `proposed`, `evaluating`, `offered`, `awaiting_client_confirmation`, `confirmed`, `rejected`, `withdrawn`, `superseded` |
| `urgency_class` | normal or urgent-impact |
| `confirmed_change_id` | accepted linked proposed-case-change row |

Reschedule activation rule:

- active case date does not change until explicit confirmation is recorded

## ApprovalRequest

`ApprovalRequest` is interface-independent.

Recommended fields:

| Field | Purpose |
| --- | --- |
| `approval_request_id` | stable identifier |
| `rental_case_id` | owning case |
| `target_entity_type` | decision, change, action, closure, waiver, and similar |
| `target_entity_id` | exact record requiring approval |
| `approval_type` | commercial exception, operational risk, compliance ambiguity, send approval, and similar |
| `reason_text` | why approval is needed |
| `evidence_references` | context pointers |
| `required_approver_role` | open role or specific approver requirement |
| `status` | `open`, `approved`, `rejected`, `expired`, `cancelled`, `superseded` |
| `decision_payload` | approval outcome details |
| `decided_at` | decision timestamp |
| `decided_by_ref` | approver identity |
| `decision_notes` | optional comments |

## Approval Semantics

Chosen approval posture values:

- `automatic_allowed`
- `approval_required`
- `human_only`
- `blocked`

Interpretation:

| Policy | Meaning |
| --- | --- |
| `automatic_allowed` | application may execute automatically when guards pass |
| `approval_required` | application may prepare but not execute before approval |
| `human_only` | application may support, but the decision/execution stays human-led |
| `blocked` | application may not proceed because authority or policy is missing |

This policy is application-controlled.

The LLM does not choose it.

## WorkflowAction

`WorkflowAction` represents structured intent:

> something the system wants executed

Recommended fields:

| Field | Purpose |
| --- | --- |
| `workflow_action_id` | stable identifier |
| `rental_case_id` | owning case |
| `action_type` | structured action code |
| `action_category` | communication, approval, document, commercial, coordination, follow-up, sync |
| `target_adapter_code` | internal, email, task_surface, calendar, payment, document, and similar |
| `reason_entity_type` | blocker, requirement, change, decision, follow-up, lifecycle rule |
| `reason_entity_id` | linked record |
| `structured_payload` | adapter-ready but provider-agnostic action content |
| `approval_posture` | one of the application-controlled approval policies |
| `status` | action lifecycle state |
| `idempotency_key` | stable dedupe key |
| `due_at` | when it should happen |
| `created_at` | audit timestamp |

## Action Execution State

Chosen action states:

- `proposed`
- `awaiting_approval`
- `approved`
- `ready_to_execute`
- `executing`
- `succeeded`
- `failed`
- `cancelled`
- `superseded`

Transition rules:

- `proposed` -> `awaiting_approval` when approval posture requires it
- `proposed` -> `ready_to_execute` when guards pass and approval is not required
- `awaiting_approval` -> `approved` or `cancelled`
- `approved` -> `ready_to_execute`
- `ready_to_execute` -> `executing`
- `executing` -> `succeeded` or `failed`
- any pending state -> `superseded` when a newer case truth makes the action stale

## ExecutionAttempt

`ExecutionAttempt` records a single try against an adapter.

Recommended fields:

| Field | Purpose |
| --- | --- |
| `execution_attempt_id` | stable identifier |
| `workflow_action_id` | parent action |
| `attempt_number` | monotonic retry number |
| `adapter_code` | actual execution adapter |
| `started_at` / `completed_at` | timing |
| `external_reference` | provider-side identifier |
| `status` | `started`, `succeeded`, `failed`, `timeout`, `cancelled` |
| `failure_code` | normalized failure reason |
| `retry_eligible` | whether another attempt is allowed |
| `response_snapshot` | minimal provider result snapshot |

State transition rule:

- execution attempt does not itself advance business state
- only verified success may unlock success-dependent workflow transitions

## Idempotency

Every externally executable action must have stable idempotency identity.

Recommended idempotency-key composition:

```text
rental_case_id
+ action_type
+ target_adapter_code
+ semantic_subject_hash
+ source_case_revision
+ optional target_scope_key
```

Rules:

1. retries reuse the same idempotency key
2. superseded actions get a new action row, not the same key
3. different semantic intents must not share a key
4. adapter retries must never create duplicate external artifacts

Protected duplicate risks:

- duplicate emails
- duplicate task cards
- duplicate calendar entries
- duplicate payment requests
- duplicate proposal sends

## FollowUp

`FollowUp` is structured waiting state.

Recommended fields:

| Field | Purpose |
| --- | --- |
| `follow_up_id` | stable identifier |
| `rental_case_id` | owning case |
| `reason_code` | why follow-up exists |
| `waiting_for_role` | client, WNC, supplier, facilitator, approver |
| `due_at` | next follow-up time |
| `urgency_level` | low, medium, high, urgent |
| `cadence_policy_code` | adaptive policy reference |
| `attempt_count` | number of follow-up attempts |
| `escalate_after` | escalation threshold |
| `status` | `scheduled`, `due`, `overdue`, `escalated`, `completed`, `cancelled` |
| `next_action_type` | suggested action when due |

## Deadlines And Milestones

`Deadline` or `Milestone` records are first-class because timing matters independently of state.

Examples:

- proposal follow-up due
- confirmation payment due
- balance payment due
- staffed-rental final-information target at `T-30`
- non-staffed final-information urgent threshold at `T-14`
- readiness review due
- event start
- close-out target

Recommended milestone states:

- `scheduled`
- `reached`
- `completed`
- `missed`
- `superseded`

## Artifact Freshness

Downstream artifacts are projections of canonical case truth.

Examples:

- proposal
- agreement
- internal event brief
- readiness summary
- staffing plan
- supplier plan
- external task projection
- calendar projection

Recommended design:

| Field | Purpose |
| --- | --- |
| `artifact_reference_id` | stable identifier |
| `rental_case_id` | owning case |
| `artifact_type` | proposal, agreement, brief, calendar projection, and similar |
| `storage_or_external_ref` | where it lives |
| `derived_from_case_revision` | exact case revision used |
| `relevant_scope_fingerprint` | optional narrower dependency fingerprint |
| `freshness_status` | `current`, `stale`, `refresh_required`, `superseded` |
| `last_generated_at` | timestamp |
| `last_synced_at` | timestamp where adapter sync applies |

Rule:

- material case truth change marks dependent artifacts stale
- staleness does not automatically execute refresh

## Audit And Provenance

The system must be able to answer:

> why did this happen?

Trace chain:

```text
Inbound event
-> extracted observation
-> proposed change or decision
-> requirement or blocker
-> approval
-> action
-> execution attempt
-> state transition
```

Audit data to preserve:

- source reference
- actor
- timestamp
- old value
- new value
- authority basis
- linked approval
- linked action and execution

Do not persist the entire Phase 7 `ContextPackage`.

Persist:

- structured references
- required warnings
- authority outcome
- item IDs and grounding references where operationally relevant
- minimal deterministic snapshots needed for audit

## Manual Overrides

Manual override capabilities must be explicit and auditable.

Allowed conceptual overrides:

- state correction where permitted
- blocker closure
- approval decision
- action cancellation or supersession
- low-impact change acceptance
- requirement satisfaction
- close-out completion
- manual rental closure

Manual override rules:

1. every override creates a `WorkflowEvent`
2. every override preserves actor and reason
3. manual override does not rewrite Phase 4 global truth
4. manual override may create case-specific truth only through `CaseDecision`

## Closure Override

Pragmatic close-out requires explicit support for:

- `close_rental`

Before closure:

- material open issues must be surfaced
- human may hand off or acknowledge them
- trivial residual matters must not trap the workflow

Manual closure creates:

- closure event
- closure note
- unresolved-material-issue summary if any remain

## Phase 7 Consumption Boundary

Phase 8 consumes:

- structured `ContextPackage`
- structured `AnswerGenerationInput` where human-facing answer framing is needed
- structured `AnswerResult` only for delivery/audit context

Phase 8 does not consume:

- freeform model prose as workflow truth

Operational rule:

- workflow state derives from deterministic evaluation plus structured Phase 7 signals, not from reading `answer_text`

See:

- `docs/phase-08/PHASE_8_PHASE7_WORKFLOW_CONSUMPTION_CONTRACT.md`

## Interpretation Boundary

Future ingestion boundary:

```text
Raw external message
-> extracted observations
-> confidence and ambiguity
-> proposed update / change / decision
-> deterministic validation
-> approval or human review if required
-> canonical case truth update only after resolution
```

Extraction is not authority.

## Communication Drafting Boundary

Workflow decides:

- the action type
- what is missing
- what conditions apply
- what must be asked or communicated

AI may then draft wording.

Example:

- workflow creates `REQUEST_CLIENT_INFORMATION`
- AI drafts the email

The AI does not decide from scratch what operational information is required.

## Integration Adapter Boundary

Adapters receive structured actions such as:

- `SEND_CLIENT_MESSAGE`
- `CREATE_TASK_SURFACE_ITEM`
- `CREATE_CALENDAR_ENTRY`
- `CREATE_PAYMENT_REQUEST`
- `SYNC_ARTIFACT_PROJECTION`

Adapters return structured execution results.

Adapters do not contain:

- pricing authority
- lifecycle authority
- approval authority
- hidden business logic

## n8n Role

n8n is frozen as a possible:

- scheduler
- event transport
- integration glue layer

n8n is not:

- the workflow source of truth
- the lifecycle engine
- the pricing engine
- the authority resolver
- the hidden business-rules store

## Failure Semantics

Failure classes the architecture must represent:

| Failure class | Required behavior |
| --- | --- |
| invalid event | reject, audit, no state advance |
| missing `RentalCase` | create if allowed or block if not, never silently attach to the wrong case |
| duplicate event | dedupe, audit, no duplicate side effects |
| illegal transition | reject and audit |
| missing authority | create blocker or confirmation path |
| conflicting `CaseDecision` | fail closed and require review |
| approval required | do not execute action |
| blocked action | no adapter call |
| adapter failure | keep action failed or retryable; no success-dependent transition |
| timeout | no implicit success |
| duplicate execution | idempotency protection must collapse to one semantic action |
| stale action | supersede rather than execute |
| stale artifact | mark refresh required |
| unresolved change | keep proposed state only |
| malformed extracted input | reject or quarantine; no truth mutation |

## Replay And Determinism

Recommended model:

- current-state tables
- append-only event log
- append-only transition/action/approval/execution history

Not recommended:

- pure full event sourcing as the only persistence model

Reason:

- operational query simplicity matters
- deterministic replay is still possible from the hybrid history
- auditability does not require making every read reconstruct from scratch

## Security And Authority Boundaries

Architecture-level write boundaries:

- only the application lifecycle engine may set canonical lifecycle state
- only approved `CaseDecision` activation may change effective case truth
- only structured approval outcomes may satisfy approval-required gates
- only verified adapter success may satisfy execution-dependent guards
- automated extraction may write proposed observations and proposed changes, not material truth
- Phase 7 authority outcomes must remain preserved as received

## Initial Automation Posture

Recommended conservative rollout defaults:

| Capability | Initial posture |
| --- | --- |
| extraction of candidate observations | `automatic_allowed` |
| missing-information identification | `automatic_allowed` |
| internal proposed low-impact case update | `approval_required` when ambiguous, otherwise candidate automatic |
| communication drafting | `automatic_allowed` |
| sending external communication | `approval_required` |
| proposal drafting | `automatic_allowed` |
| proposal sending | `approval_required` |
| commercial exception activation | `approval_required` |
| compliance resolution | `human_only` |
| low-impact internal sync | `automatic_allowed` after validation |
| payment request creation | `approval_required` initially |
| artifact refresh marking | `automatic_allowed` |

## MVP Slice

First implementation slice remains:

```text
new inquiry
-> case creation or update
-> structured information extraction
-> missing-information detection
-> Phase 4 / 5 / 7 reasoning support
-> next structured workflow need
-> clarification email draft
-> human review
-> send
-> wait for reply
-> ingest reply
-> update case
-> re-evaluate
```

This architecture supports that slice without needing:

- payment automation
- calendar integration
- rescheduling execution
- event-day execution adapters

## Architecture Invariants

### `P8-INV-001`

Every active rental has explicit persistent lifecycle state.

### `P8-INV-002`

State transitions are application-controlled, not freely selected by an LLM.

### `P8-INV-003`

Phase 8 consumes structured Phase 7 output and does not infer workflow truth from generated answer prose.

### `P8-INV-004`

Phase 4 remains global deterministic authority.

### `P8-INV-005`

Case-specific decisions are scoped to one `RentalCase` unless separately promoted through governed policy change.

### `P8-INV-006`

Historical precedent never becomes workflow policy automatically.

### `P8-INV-007`

Missing authority produces a blocker or confirmation path, not an invented decision.

### `P8-INV-008`

Material inbound changes remain proposed until resolved.

### `P8-INV-009`

Operational actions are structured before execution.

### `P8-INV-010`

Approval requirements are enforced application-side.

### `P8-INV-011`

External integrations contain transport and execution logic, not business authority.

### `P8-INV-012`

External execution failure cannot silently advance workflow state.

### `P8-INV-013`

Externally executable actions are idempotency protected.

### `P8-INV-014`

Material decisions, changes, approvals, actions, executions, and transitions remain auditable.

### `P8-INV-015`

Generated communication wording cannot redefine structured operational intent.

### `P8-INV-016`

Manual overrides are explicit and auditable.

### `P8-INV-017`

Blocked and resolution states can resume deterministically when resolving evidence arrives.

### `P8-INV-018`

Downstream artifacts are projections of canonical case truth and may be marked stale after material case changes.

## Future Implementation Boundaries

Phase 8.0B freezes architecture only.

Deferred beyond this phase:

- persistence schema implementation
- lifecycle engine implementation
- extraction runtime
- approval runtime
- action execution runtime
- integrations
- scheduling infrastructure
- UI and operator console

## Conclusion

The canonical Phase 8 workflow architecture is:

- `RentalCase`-centered
- state-machine/application controlled
- explicit about blockers, requirements, approvals, and case-specific truth
- integration-independent
- safe for progressive autonomy

This architecture is the frozen baseline for workflow foundation implementation, not the workflow runtime itself.
