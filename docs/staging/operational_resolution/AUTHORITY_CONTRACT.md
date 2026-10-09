# Governed operational resolution v1

This staging-only extension composes existing WorkflowAction, immutable WorkflowEvent, RentalCaseFact and case revision primitives. It does not introduce a new workflow engine or promote action/provider completion to truth.

The authenticated operator route is `POST /api/operator/cases/{id}/operational-resolutions`. The server derives the actor from configured staging authentication. The current version accepts explicitly labelled **staging synthetic operator evidence** only. No production admission path is enabled.

## Admission and scope

The service derives the contract from the actual action and typed reasoning origin. Eligible classes are venue `AVAILABILITY_CONFIRMATION` and `TECHNICAL_CAPABILITY_CONFIRMATION` for explicitly requested, enumerated components. Venue, exact UTC interval, case, action, semantic obligation and subjects are bound in the submitted contract. Task prose does not select authority. A technical policy must require confirmation: missing policy authority and published prohibitions cannot be overridden.

An explicit outcome, evidence text/reference, occurred-at time and replay identity are required. External-party messages, Asana completion, model output, actor/authority overrides in request JSON, commercial changes, payment, booking and legal claims are rejected. External evidence requires a separately governed acceptance contract; v1 deliberately fails closed rather than creating one implicitly. Existing CaseDecision handling remains unchanged.

## Persistence, conflict and revision

`accept_operational_resolution` locks the case and action, verifies the expected revision and action identity, then atomically appends acceptance/evidence to WorkflowEvent, projects a current RentalCaseFact and advances the case revision. Existing append-only triggers protect the evidence journal. Original inbound sources and observations are untouched.

A correction must explicitly name the current acceptance event. Unacknowledged contradictory submissions are rejected with `conflicting_resolution_requires_explicit_correction`; no history is overwritten. The current fact points to the latest accepted evidence. Corrections state the complete new result: omitted technical components become pending. Replay returns the original event/fact/revision and never applies the evidence to the new revision. Changed replay payloads fail.

The fact is usable only when its complete value matches the immutable acceptance event and its case/venue/interval remains current. No action status is consulted as authority. Only complete semantic coverage suppresses pending work. Partial component results remain facts while the aggregate obligation remains pending.

## Existing context and provider consumers

The governed drafting contract exposes bounded operational assertions through the existing typed guidance/planner/realization pipeline. This adds a fact type, not a new planner, date inference, tone policy or authority hierarchy. Positive and negative results are mandatory scoped assertions; unfulfilled or broader claims fail validation. Booking remains forbidden. Conflicting current policy blocks contract creation.

Asana remains outbound projection only. An action carrying a governed resolution reference is complete in the projection only while its accepted scoped fact remains current. Provider observations cannot establish any fact. Phase 8's existing current-rule projection changes a confirmation-required technical issue to a grounded known result only when accepted evidence covers every requested component. General Phase 7 retrieval context remains a knowledge/policy context; it is not relabelled as operator evidence.

## Deliberate boundary

Unknown layout/capacity information is not an availability or technical confirmation. This contract cannot invent a requested room configuration or override the current capacity rules. Such unresolved work must remain visible; the existing frozen draft approval guard continues to block a draft containing blocking internal annotations.
