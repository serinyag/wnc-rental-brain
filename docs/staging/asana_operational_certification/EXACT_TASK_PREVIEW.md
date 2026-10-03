# Exact proposed synthetic Asana task

Canonical staging case: 585; action: 1626. No provider task has been created.

Workspace: `1208455784737302`. Project: `1217642260793817`.

## Master task

SYNTHETIC TEST — WNC Operations — team workshop — 12 November 2026

```text
CLIENT
SYNTHETIC TEST — WNC Operations

EVENT
team workshop
Requested timing: 12 November 2026, 14:00 CET to 12 November 2026, 18:00 CET
Requested venue / scope: studio space
Guests: 24

CURRENT STATUS
Decision required
Client response is waiting on internal work.

OPEN ITEMS
- WNC follow-up with external party: Confirm supplier logistics
- WNC governed decision review: Review the requested fee adjustment
- WNC internal check: Confirm studio availability for the requested time
- Client to answer: Confirm the preferred room layout

NEXT ACTIONS
Complete the checks below and record their outcomes for review.

OUTLOOK
No verified conversation link is available for this case.

WNC reference: RC-20261003152913292 / 6db3e9eacf60
```

Custom fields: none (`{}`). Native completed: false. Assignee: unassigned. Due date: none.

## Subtasks

### Confirm supplier logistics

Ownership: `EXTERNAL_PARTY`. Native completed: false. Assignee: unassigned.

```text
WNC follow-up with external party

To do: Confirm supplier arrival timing
To do: Confirm handover arrangements
To do: Confirm the loading route

Record the outcome for governed review before treating it as confirmed.

WNC reference: RC-20261003152913292 / 6db3e9eacf60 / work d27d45b61c7a
```

### Review the requested fee adjustment

Ownership: `GOVERNED_DECISION`. Native completed: false. Assignee: unassigned.

```text
WNC governed decision review

To do: Review the requested fee adjustment

Record the outcome for governed review before treating it as confirmed.

WNC reference: RC-20261003152913292 / 6db3e9eacf60 / work 4c7e41cf0455
```

### Confirm studio availability for the requested time

Ownership: `WNC_INTERNAL`. Native completed: false. Assignee: unassigned.

```text
WNC internal check

To do: Confirm studio availability for the requested time

Record the outcome for governed review before treating it as confirmed.

WNC reference: RC-20261003152913292 / 6db3e9eacf60 / work fda5b0d1ab9f
```

## Authorized-next-stage scope (not yet authorized)

Create this one master and three subtasks through action 1626. Verify bindings and replay. Then apply one synthetic governed case update: guests 24 → 30, resolve venue availability, add “Confirm projector and microphone availability”. Update the same master, complete the existing venue subtask, create one new technical subtask, preserve supplier/decision work. Read/reconcile and replay. Stop immediately on ambiguity; never blindly repeat a create. Disable the staging Asana gate at closure.

## Operator review

The master makes the event, timing, scope, group size, blocking decisions, external follow-up and client question visible. Supplier arrival, handover and loading checks share one human task with three auditable obligations. No raw reasoning, JSON, commercial approval, guessed assignee, invented due date or unverified Outlook URL is exposed. The only system footer is the case/work reference needed for safe identification.
