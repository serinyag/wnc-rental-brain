# Phase 8 Workflow Action Taxonomy

Date:

- August 9, 2026

Status:

- `PHASE_8_0B_ACTION_TAXONOMY_FROZEN`

## Purpose

Freeze the structured action vocabulary that the workflow system may produce before execution.

This document defines:

- action categories
- canonical action codes
- adapter boundaries
- default approval posture
- idempotency subjects

This document does not implement adapters.

## Action Principles

1. Actions are structured intent, not truth.
2. The workflow decides what action is needed before any drafting or adapter work occurs.
3. Generated prose may fill wording fields inside a structured action, but may not invent the action type itself.
4. No action may silently mutate lifecycle state.
5. Externally executable actions must be idempotency-protected.

## Canonical Categories

| Category | Meaning |
| --- | --- |
| `communication` | Outbound or internally routed messages. |
| `document` | Drafting, refreshing, or syncing a proposal, agreement, or internal brief. |
| `commercial` | Payment, commercial exception handling, or proposal commitment tasks. |
| `coordination` | Task creation, calendar, or operational routing work. |
| `compliance` | Requirements, escalations, and human review for legal or policy-sensitive matters. |
| `approval` | Structured requests for human authorization. |
| `follow_up` | Reminders, nudges, dormant reviews, and escalation loops. |
| `sync` | Non-authoritative projections to external systems. |
| `internal_control` | Application-side operational actions such as marking artifacts stale or scheduling evaluation. |

## Canonical Action Codes

| Action code | Category | Semantic intent | Typical trigger | Default approval posture | Allowed adapter targets | Idempotency subject |
| --- | --- | --- | --- | --- | --- | --- |
| `REQUEST_CLIENT_INFORMATION` | `communication` | Ask the client for missing scoping or planning information. | Open question or requirement is blocking or time-sensitive. | `approval_required` for send in MVP | `email`, `task_surface`, `internal` | One outstanding request for the same question set and case revision. |
| `SEND_DISCOVERY_CALL_INVITE` | `communication` | Offer or schedule a discovery call. | Qualification path indicates live discussion is needed. | `approval_required` in MVP | `email`, `calendar`, `task_surface` | One invite per case, subject, and proposed slot set. |
| `SEND_SITE_VISIT_PROPOSAL` | `communication` | Offer or coordinate a site visit. | Qualification or operational planning requires an on-site review. | `approval_required` | `email`, `calendar`, `task_surface` | One site-visit proposal per case revision and visit scope. |
| `SEND_PROPOSAL_MESSAGE` | `communication` | Send a proposal or a proposal-linked explanation. | Proposal artifact is ready and human send gate passes. | `approval_required` | `email`, `document`, `task_surface` | One send per proposal artifact revision and recipient set. |
| `SEND_PROPOSAL_FOLLOW_UP` | `follow_up` | Nudge the client after proposal send. | Proposal pending and follow-up due. | `approval_required` initially | `email`, `task_surface` | One follow-up cadence step per proposal artifact revision. |
| `REQUEST_CONFIRMATION_PAYMENT` | `commercial` | Ask for the booking-confirmation payment. | Proposal accepted and payment is part of confirmation. | `approval_required` initially | `email`, `payment`, `task_surface` | One active payment request per case revision and confirmation gate. |
| `REQUEST_SIGNED_AGREEMENT` | `commercial` | Ask for agreement execution or acknowledgement. | Confirmation gate requires agreement completion. | `approval_required` initially | `email`, `document`, `task_surface` | One active agreement request per agreement artifact revision. |
| `REQUEST_FINAL_EVENT_INFORMATION` | `communication` | Ask for event-day logistics and final details. | Final information requirement reaches its active collection window. | `approval_required` initially | `email`, `task_surface` | One active package request per case revision and due window. |
| `REQUEST_SUPPLIER_INFORMATION` | `communication` | Ask the client or supplier for third-party details. | Supplier requirement is active or blocked. | `approval_required` initially | `email`, `task_surface` | One active request per supplier scope and case revision. |
| `ESCALATE_COMPLIANCE_REVIEW` | `compliance` | Route a case for human compliance review. | Legal or compliance ambiguity exists. | `human_only` | `task_surface`, `internal` | One open escalation per compliance scope and unresolved issue set. |
| `REQUEST_EXCEPTION_APPROVAL` | `approval` | Create a human approval request for a decision, change, or action. | Commercial exception, unusual risk, or unresolved authority needs approval. | `automatic_allowed` for creation | `internal`, `task_surface` | One request per target entity and approval type. |
| `CREATE_INTERNAL_TASK_ITEM` | `coordination` | Create or update a task in the chosen task surface. | A requirement, blocker, or review needs operational visibility. | `automatic_allowed` for low-risk sync | `task_surface` | One task projection per target entity and target system. |
| `CREATE_CALENDAR_HOLD` | `coordination` | Create or sync a calendar placeholder or confirmed slot. | Discovery call, site visit, or event scheduling step needs calendar support. | `approval_required` unless internal-only | `calendar` | One calendar object per subject, time range, and case revision. |
| `CREATE_PAYMENT_REQUEST` | `commercial` | Create a payment link or formal payment request artifact. | Confirmation or balance payment step is ready. | `approval_required` initially | `payment` | One active payment object per obligation and case revision. |
| `DRAFT_PROPOSAL_ARTIFACT` | `document` | Produce or refresh a proposal projection from canonical case truth. | Proposal work begins or a material change makes the current artifact stale. | `automatic_allowed` | `document`, `internal` | One draft per case revision and artifact type. |
| `DRAFT_AGREEMENT_ARTIFACT` | `document` | Produce or refresh the agreement projection. | Confirmation work requires a current agreement artifact. | `automatic_allowed` | `document`, `internal` | One draft per case revision and artifact type. |
| `DRAFT_INTERNAL_EVENT_BRIEF` | `document` | Produce or refresh an internal operational brief. | Confirmed rental planning or readiness review needs a fresh brief. | `automatic_allowed` | `document`, `internal` | One brief per case revision and relevant scope fingerprint. |
| `SYNC_ARTIFACT_PROJECTION` | `sync` | Push or update an already-defined projection in an external system. | Current artifact exists and sync is due. | `automatic_allowed` for low-risk internal sync | `document`, `calendar`, `task_surface` | One sync per artifact reference, destination, and case revision. |
| `MARK_ARTIFACT_REFRESH_REQUIRED` | `internal_control` | Flag downstream projections as stale or refresh-required. | Material case truth changes. | `automatic_allowed` | `internal` | One freshness change per artifact reference and case revision. |
| `SCHEDULE_FOLLOW_UP_REVIEW` | `follow_up` | Create or refresh a follow-up cadence checkpoint. | Waiting state or dormant review exists. | `automatic_allowed` | `internal`, `task_surface` | One scheduled follow-up per reason code and due slot. |
| `ESCALATE_DORMANT_CASE_REVIEW` | `follow_up` | Surface a dormant case for explicit review. | Dormant review threshold is hit or urgency changes. | `automatic_allowed` for surfacing, `human_only` for substantive decision | `task_surface`, `internal` | One escalation per dormant period and reason. |
| `SUPERSEDE_STALE_ACTIONS` | `internal_control` | Supersede actions invalidated by new case truth. | Material change makes a pending action unsafe. | `automatic_allowed` | `internal` | One supersession pass per case revision delta. |
| `RECORD_MANUAL_CLOSE_PACKET` | `internal_control` | Package closure notes and unresolved issue summary for auditable manual close. | Human chooses to close when automation no longer adds value. | `human_only` | `internal`, `document` | One close packet per closure attempt. |

## Taxonomy Notes

### Internal Control Versus External Execution

Some action codes are internal workflow operations rather than third-party calls.

Examples:

- `MARK_ARTIFACT_REFRESH_REQUIRED`
- `SCHEDULE_FOLLOW_UP_REVIEW`
- `SUPERSEDE_STALE_ACTIONS`

They still benefit from structured action records because they:

- preserve auditability
- align with the same approval model where needed
- give the workflow one consistent intent model

### Naming Normalization

Action codes should stay:

- imperative
- transport-agnostic
- business-meaningful
- stable across adapter replacement

Avoid action codes that leak provider names or UI details.

Bad examples:

- `SEND_GMAIL_MESSAGE`
- `CREATE_ASANA_TASK`
- `UPDATE_N8N_STATE`

Good replacements:

- `SEND_CLIENT_MESSAGE`
- `CREATE_INTERNAL_TASK_ITEM`
- `SCHEDULE_FOLLOW_UP_REVIEW`

Family-level labels may still appear in the broader architecture docs as umbrella examples.

Examples:

- `SEND_CLIENT_MESSAGE`
- `CREATE_TASK_SURFACE_ITEM`
- `CREATE_CALENDAR_ENTRY`

The frozen taxonomy in this document specializes those families into concrete workflow action codes such as:

- `REQUEST_CLIENT_INFORMATION`
- `SEND_PROPOSAL_MESSAGE`
- `CREATE_INTERNAL_TASK_ITEM`
- `CREATE_CALENDAR_HOLD`

## Approval Posture Defaults

The workflow architecture freezes these MVP defaults:

| Action pattern | Default posture |
| --- | --- |
| internal drafting or stale-marking | `automatic_allowed` |
| low-risk internal sync | `automatic_allowed` |
| outbound communication to client | `approval_required` |
| proposal send | `approval_required` |
| payment request creation | `approval_required` |
| commercial or operational exception routing | `approval_required` |
| compliance resolution decision | `human_only` |
| manual close | `human_only` |

These are policy defaults, not adapter decisions.

## Excluded Action Types

The following are intentionally not action codes:

- direct lifecycle transitions such as `MOVE_TO_EVENT_READY`
- direct business-truth mutation such as `CHANGE_BOOKING_FEE`
- silent auto-approval operations
- freeform provider-specific send commands

Lifecycle transitions remain consequences of evaluation, not arbitrary actions.

Business-truth mutation must flow through:

- `ProposedCaseChange`
- `CaseDecision`
- `ApprovalRequest`
- deterministic application evaluation

## Idempotency Guidance

Externally executable action types must use the Phase 8 idempotency composition:

```text
rental_case_id
+ action_type
+ target_adapter_code
+ semantic_subject_hash
+ source_case_revision
+ optional target_scope_key
```

Practical examples:

- proposal sends dedupe by proposal artifact revision plus recipient set
- final-information requests dedupe by request package and case revision
- payment requests dedupe by obligation type and case revision
- calendar entries dedupe by subject, time range, and case revision

## Phase 7 Interaction

Phase 7 may inform:

- what information is missing
- whether authority is unresolved
- whether a response should be blocked or require confirmation
- what warnings must accompany a drafted communication

Phase 7 may not invent action types or bypass this taxonomy.

## Frozen Conclusion

The Phase 8 action taxonomy is now frozen as:

- transport-agnostic structured action codes
- explicit approval-aware categories
- idempotency-protected external execution
- internal control actions for stale marking, follow-up, and closure packaging

This taxonomy is the authoritative action vocabulary for workflow foundation implementation.
