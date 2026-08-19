# Phase 8 Rental Lifecycle State Transition Matrix

Date:

- August 9, 2026

Status:

- `PHASE_8_0B_LIFECYCLE_FROZEN`

## Purpose

Freeze the canonical lifecycle states and the allowed application-controlled transitions for the `RentalCase` aggregate.

This document is authoritative for:

- state names
- state intent
- allowed transition paths
- transition guard expectations
- terminal-state rules

This document does not implement a runtime engine.

## Canonical Lifecycle States

| State | Meaning | Notes |
| --- | --- | --- |
| `inquiry_active` | New or active inquiry is being qualified. | Pre-proposal discovery, clarification, and feasibility work. |
| `proposal_in_progress` | WNC is actively shaping scope, feasibility, pricing, or proposal content. | Internal working state before a proposal is out with the client. |
| `proposal_pending_client` | A proposal or scoped alternative is with the client and the workflow is waiting for response. | The workflow may still track follow-ups, blockers, and minor clarification. |
| `confirmation_pending` | The client intends to proceed, but confirmation conditions are still outstanding. | Typical gates include confirmation payment, agreement completion, or equivalent explicit booking confirmation requirements. |
| `confirmed_pre_event` | The booking is secured and the rental is now in pre-event delivery planning. | Material changes do not rewind to pre-confirmation states. |
| `event_ready` | No unresolved material delivery risk remains and all required responsibilities have explicit owner and status. | This is a readiness state, not merely a calendar countdown. |
| `event_in_progress` | The event delivery window is active. | Event-day execution and live operational handling. |
| `close_out_in_progress` | The event has completed, but post-event obligations are still being resolved. | Deposit, overtime, incident, invoice, follow-up, and closure work live here. |
| `dormant` | The case is intentionally parked rather than actively worked. | Only appropriate for selected pre-confirmed situations; reactivation must be deterministic. |
| `closed` | The rental is operationally complete. | Terminal in normal operation. |
| `closed_lost` | The opportunity ended without becoming a secured booking. | Declined, expired, or otherwise lost before confirmation. |
| `cancelled` | A secured or materially active rental was cancelled. | Distinct from `closed_lost`. |

## Modeling Notes

### `EVENT_COMPLETE` Preservation

The Phase 8 business decision record distinguishes `EVENT_COMPLETE`, `CLOSE_OUT_IN_PROGRESS`, and `CLOSED`.

The architecture preserves that distinction as:

- `event_completed` as a first-class `WorkflowEvent`
- optional `event_complete` milestone/deadline completion evidence
- `close_out_in_progress` as the canonical post-event lifecycle state

This keeps the lifecycle compact while still preserving staged completion semantics.

### `dormant` Reactivation

`dormant` is not a dead-end parking lot.

When a case is moved to `dormant`, the system should preserve:

- `dormant_origin_state`
- `resume_target_state`
- `dormant_reason_code`
- `dormant_review_at`

Reactivation must target an explicit active state rather than relying on operator memory.

## Transition Principles

1. Lifecycle state is application-controlled.
2. No transition may be derived from generated prose alone.
3. Target-state guards must be evaluated against structured case truth, blockers, requirements, approvals, and verified execution results.
4. Confirmed rentals do not rewind into pre-confirmation states.
5. Material change may degrade readiness, but it does so within the confirmed branch of the lifecycle.
6. Terminal states are terminal in normal workflow operation and reopen only through explicit manual override.

## Standard Transition Matrix

| From | To | Allowed when | Required guards or evidence | Typical side effects |
| --- | --- | --- | --- | --- |
| `inquiry_active` | `proposal_in_progress` | Enough scoping information exists to begin proposal shaping or alternative evaluation. | No hard feasibility blocker preventing proposal work. | Create or update proposal work items, open questions, and requirements. |
| `inquiry_active` | `dormant` | Client is non-responsive or waiting is intentional, and the case is safe to pause. | Adaptive follow-up policy permits parking; no urgent confirmed obligation exists. | Create follow-up, persist resume target, emit dormant event. |
| `inquiry_active` | `closed_lost` | The inquiry is declined, infeasible without supported path, expired, or follow-up exhaustion closes it. | Reason code recorded. | Close pending pre-booking actions, preserve audit trail. |
| `proposal_in_progress` | `proposal_pending_client` | A proposal or governed alternative has been sent to the client. | Proposal-ready materiality threshold passes. | Record proposal artifact reference, create reply follow-up. |
| `proposal_in_progress` | `dormant` | Proposal work is intentionally paused while waiting on client input and the case is safe to park. | Missing information or client wait is non-urgent. | Persist resume target, follow-up cadence, and pause rationale. |
| `proposal_in_progress` | `closed_lost` | The client declines, proposal expires, or the opportunity is abandoned pre-confirmation. | Loss reason captured. | Supersede pending proposal actions. |
| `proposal_pending_client` | `proposal_in_progress` | The client requests changes, asks questions that reopen proposal work, or a governed alternative path is being revised. | New information or requested change is captured structurally. | Open proposed case changes, re-evaluate scope and pricing. |
| `proposal_pending_client` | `confirmation_pending` | The client indicates intent to book and confirmation conditions become the next gate. | Proposal acceptance or equivalent booking-intent evidence exists. | Create confirmation requirements and follow-ups. |
| `proposal_pending_client` | `dormant` | Follow-up cadence has paused the case without declaring it lost. | Not time-critical; no stronger closure rule applies. | Emit dormant event and preserve resume target. |
| `proposal_pending_client` | `closed_lost` | The proposal is declined, expires, or non-response exhausts the configured dormant/follow-up policy. | Loss reason captured. | Cancel stale follow-ups and pending sends. |
| `confirmation_pending` | `confirmed_pre_event` | Booking confirmation conditions are satisfied. | Confirmation payment, agreement, and any other required confirmation gates pass. | Increment case revision, create readiness/final-info requirements. |
| `confirmation_pending` | `proposal_in_progress` | Material commercial, scope, or date change reopens proposal work before confirmation completes. | Change impact review shows the case must be reworked. | Create proposed change records and supersede stale confirmation actions. |
| `confirmation_pending` | `dormant` | A pre-confirmation case is intentionally paused without declaring it lost. | Adaptive follow-up policy allows it and no urgent event risk exists. | Persist resume target and follow-up. |
| `confirmation_pending` | `closed_lost` | The client abandons or declines before confirmation completes. | Explicit decline or exhausted follow-up rule. | Cancel confirmation-specific pending actions. |
| `confirmed_pre_event` | `event_ready` | All material pre-event requirements are satisfied and no unresolved delivery risk remains. | `EVENT_READY` gate passes. | Snapshot readiness status, schedule event-day actions. |
| `confirmed_pre_event` | `cancelled` | The secured rental is cancelled. | Cancellation reason and authority path recorded. | Supersede future actions, preserve downstream recovery tasks. |
| `event_ready` | `confirmed_pre_event` | New material change or blocker means the case is no longer ready. | Readiness guard fails on re-evaluation. | Mark affected artifacts stale, create blockers or approvals. |
| `event_ready` | `event_in_progress` | The delivery window begins and the event is operationally underway. | Event start evidence or explicit operator start action. | Create in-progress milestone event. |
| `event_ready` | `cancelled` | Cancellation occurs before the event starts. | Cancellation evidence recorded. | Supersede pre-event actions and preserve post-cancellation obligations. |
| `event_in_progress` | `close_out_in_progress` | The event is complete and the case moves into post-event handling. | `event_completed` event recorded. | Open close-out requirements, deposit/overtime/invoice follow-ups, and incident review if needed. |
| `close_out_in_progress` | `closed` | Remaining close-out obligations are resolved or human manual close is justified. | Material post-event issues are resolved or explicitly acknowledged through auditable manual close. | Emit closure event, freeze active workflow actions. |
| `dormant` | `inquiry_active` | A dormant inquiry resumes qualification. | Resume trigger arrives and stored resume target matches inquiry stage. | Re-open follow-up and evaluation loop. |
| `dormant` | `proposal_in_progress` | A dormant proposal case resumes internal working activity. | Resume trigger arrives and stored resume target matches proposal drafting/rework. | Re-open proposal tasks and stale artifacts review. |
| `dormant` | `proposal_pending_client` | A dormant pending proposal resumes waiting or active reply handling. | Resume trigger arrives and waiting posture is restored. | Resume follow-up cadence. |
| `dormant` | `confirmation_pending` | A dormant pre-confirmation booking attempt resumes. | Resume trigger arrives and the stored target is confirmation work. | Re-open confirmation tasks and due dates. |
| `dormant` | `closed_lost` | The dormant case ages out or is explicitly declared lost. | Closure policy or operator decision recorded. | End follow-up cadence and preserve loss reason. |

## Transition Guard Summary

| Target state | Guard summary |
| --- | --- |
| `proposal_in_progress` | Enough structured information exists to do real scoping work. |
| `proposal_pending_client` | Proposal-ready threshold passes and a concrete outbound proposal exists. |
| `confirmation_pending` | The client has signaled intent to proceed. |
| `confirmed_pre_event` | Confirmation gates are satisfied. |
| `event_ready` | No unresolved material delivery risk remains. |
| `event_in_progress` | Event-start evidence exists. |
| `close_out_in_progress` | Event completion evidence exists. |
| `closed` | Material close-out obligations are resolved or auditable manual close has been executed. |
| `dormant` | The case is safe to park and resume later. |
| `closed_lost` | The opportunity ended pre-confirmation. |
| `cancelled` | A confirmed or materially active rental is cancelled. |

## Prohibited Normal-Path Transitions

These are not part of the standard state machine:

- any direct jump from pre-confirmation states to `confirmed_pre_event` without confirmation evidence
- any direct jump from `confirmed_pre_event` to `event_in_progress` without readiness or explicit auditable override
- any direct jump from `event_in_progress` to `closed`
- any transition into an earlier pre-confirmation state from a confirmed booking
- any terminal-state exit without manual override

If business reality requires one of these paths, it must occur through an explicit manual override event and audit note rather than silent state mutation.

## Rescheduling Interaction

Rescheduling does not automatically change lifecycle state.

The workflow treatment is:

1. create `RescheduleRequest`
2. create one or more `ProposedCaseChange` rows
3. evaluate authority, impact, feasibility, and approval needs
4. update canonical date only after explicit confirmation
5. re-evaluate readiness and dependent artifacts

Possible lifecycle effect after confirmation:

- `event_ready` may degrade to `confirmed_pre_event`
- `confirmed_pre_event` typically remains `confirmed_pre_event`
- `close_out_in_progress` or `closed` rescheduling is not a standard path

## Terminal State Rules

| State | Terminal meaning | Reopen policy |
| --- | --- | --- |
| `closed` | Operationally complete. | Manual override only. |
| `closed_lost` | Opportunity ended without booking. | Manual override only. |
| `cancelled` | Booked or materially active rental was cancelled. | Manual override only. |

## Frozen Conclusion

The canonical lifecycle is now frozen as:

- 12 explicit lifecycle states
- staged completion through `event_completed` event plus `close_out_in_progress`
- deterministic confirmed-branch handling without pre-confirmation rewind
- explicit dormant reactivation

This matrix is the authoritative Phase 8.0B lifecycle transition model.
