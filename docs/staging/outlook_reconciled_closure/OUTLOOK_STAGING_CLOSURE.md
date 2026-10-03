# Outlook real staging-send certification: reconciled and closed

Final marker: **OUTLOOK_REAL_STAGING_SEND_CERTIFIED_RECONCILED**

Human-confirmed delivery is persisted as workflow event **17096**, recorded at 2026-10-03T14:49:40.683595+00:00. The original automated attempt remains ambiguous and unchanged. No provider was contacted during reconciliation.

## Approved lineage and final state

| Record | ID | Final state |
|---|---:|---|
| Case | 584 | Exact certification case |
| DraftRevision | 386 | Current; human_confirmed_delivered |
| WorkflowAction | 1619 | succeeded, based on separate human reconciliation evidence |
| ApprovalRequest | 465 | approved; unchanged |
| ExecutionAttempt | 23 | failed / adapter_outcome_ambiguous; unchanged |
| Reconciliation event | 17096 | outlook_delivery_human_confirmed |

Exact approval target: `workflow_action:1619:draft_revision:386`.

Recipient: `Serinya@whennaturecalls.nl`.

Subject: `SYNTHETIC TEST - Outlook final send certification`.

Approved body remains exactly:

> Hi Serinya,
>
> This is a synthetic test message for the Outlook approval and execution path. No action is required from you.

## Automated observation and human confirmation

The original execution made one token request, one draft creation, one pre-send read, one send request accepted with a 2xx response, and one post-send read. The read returned HTTP 200 but did not establish every required sent-message field. The application recorded `send_verification_inconclusive` at `verify_sent_message`, with `adapter_outcome_ambiguous` and `retry_eligible=false`. No retry occurred. These operation counts derive from the persisted outcome and the deployed adapter's single-pass control flow, not an independent network trace.

The operator subsequently reported that the intended recipient confirmed receipt of the exact email. Event 17096 records:

- Source: `human_operator_confirmation`.
- Confirmation: `recipient_received_intended_message`.
- Outcome: `human_confirmed_delivered`.
- Resend performed: false.
- Provider call performed: false.
- Evidence note: Human operator reports that intended recipient Serinya@whennaturecalls.nl confirmed receipt of the exact synthetic certification email after ambiguous automated verification. No resend performed; no provider call performed.

The event also contains the full original ExecutionAttempt 23 snapshot. Its timestamp records when confirmation was persisted, not an invented delivery time. Automated `delivered_at`, external reference, and ambiguity code remain untouched on the revision; the distinct delivery status expresses human reconciliation.

## Audit and immutable binding

The complete Attempt 23 row and ApprovalRequest 465 row match their pre-reconciliation snapshots exactly. The original workflow events are unchanged. Only action status/updated_at and draft delivery status/updated_at changed; all draft content, recipient, hashes, provenance, and bindings remain immutable.

- Content hash: `4b32159890f4e22c33fa6aec3fa23d42aff6060297af7f651714eadb40e6417b`
- Context hash: `593d6264c01f5c1da0e24a8b8637b72b0da4401629ce67c583ef9476c10e479a`
- Governed context hash: `d48dbf7bd524eaed0e1f3471510c05fdfcdd4e8459ac44f41605f8622b9c68ed`
- Canonical contract and exact payload: PASS.
- Total ExecutionAttempts for the action: **1**.
- Historical case 424: PASS; action, approval, revision, attempt and workflow-event rows unchanged, including actions 582/586/587/588, approvals 184/185/186, and revision 144.

## Idempotency and replay

Two identical requests to the governed confirmation endpoint returned event **17096**. The second returned `Already reconciled: True`; exactly one reconciliation event exists. No new approval or attempt was created.

Provider-free checks after persistence:

- Shared runtime preflight: `action_already_succeeded`.
- Draft execution guard: `INQUIRY_DRAFT_NOT_APPROVED`, because its terminal delivery status is human_confirmed_delivered; the approval itself remains approved.
- Original attempt retry guard: `adapter_outcome_ambiguous` / `prior_outlook_attempt_requires_manual_reconciliation`.

No live execution endpoint was invoked to test replay. Local database tests also verified rejection before any new attempt/provider adapter could run. Conflicting confirmation evidence is rejected rather than overwriting the existing event.

## Architecture and deployment

Existing reconciliation covered Graph draft inspection and revision recovery; it did not support provider-free human delivery confirmation. The smallest added mechanism reuses `workflow_events` and its unique identity constraint. A single database transaction locks and revalidates the lineage, appends the human event, and settles the action and draft. It never updates execution evidence. Database execution is limited to service-role/owner privileges, and the application operation requires staging with the send gate disabled.

- Application commit: `45c907e9dc822d9abc3252c3373edbf28771f870`.
- Staging deployment: `dep-db0haonavr4c73fndod0`, verified Live.
- Migration: `20261003000100_phase_08_human_delivery_reconciliation.sql`, applied and recorded in staging migration history.
- Normal authenticated operator endpoint: `POST /api/operator/cases/584/actions/1619/confirm-delivery`.
- Accepted drafting behavior remains frozen; changes to the drafting module only recognize the terminal delivery status. No drafting UAT, OpenAI generation, or editorial/realization tuning was performed.

## Verification

- Focused provider-free tests: **11 passed**.
- Phase 8 regression: **563 passed; 126 subtests passed; no skips or failures**.
- Tests used local PostgreSQL and fake transport, with fixture changes rolled back.
- Atomic rollback, original-attempt immutability, persistence, exact binding, gate enforcement, duplicate confirmation, conflicting evidence, no duplicate attempts, and replay blocking passed.
- Final staging health: `ok`.
- Outlook posture: `configured_draft_only`.
- Send gate: `STAGING_ALLOW_REAL_OUTLOOK_SEND=false`; never enabled during this task.

## Safety for this reconciliation task

| Activity | Count |
|---|---:|
| Graph calls | 0 |
| Outlook sends | 0 |
| New staging ExecutionAttempts | 0 |
| OpenAI calls | 0 |
| Real Asana executions | 0 |
| Production activity | 0 |
| New drafts or approvals | 0 |

Asana configuration was unchanged. No Exchange or Entra changes occurred.

## Closure conclusion

The ambiguity guard behaved correctly. The system preferred an uncertain terminal state over risking duplicate client communication. Subsequent human evidence reconciled the outcome without another provider send, while retaining the original automated observation as historical truth.

**OUTLOOK_REAL_STAGING_SEND_CERTIFIED_RECONCILED**

Stopped. No further send, execution, or provider read was performed.
