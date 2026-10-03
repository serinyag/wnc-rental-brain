# Human-confirmed Outlook delivery reconciliation

The previous Outlook reconciliation operations inspect Graph drafts and can create successor revisions. They cannot record recipient confirmation of an ambiguous completed send without another provider call. Human-confirmed delivery now uses the existing `workflow_events` audit store, with no new evidence ledger.

`TestConsoleService.reconcile_human_confirmed_outlook_delivery` accepts an exact case/action/revision/approval/attempt lineage, recipient, subject, and human evidence note. It requires staging, a disabled send gate, an allowlisted recipient, an approved exact revision, and precisely one failed, non-retryable attempt whose automated post-send verification was inconclusive. It does not construct a provider adapter.

The repository invokes `reconcile_outlook_human_delivery` in PostgreSQL. The function locks and rechecks the lineage, appends `outlook_delivery_human_confirmed`, and atomically changes the action to `succeeded` and the draft delivery status to `human_confirmed_delivered`. Original attempt, approval, draft content, hashes, and automated delivery metadata remain unchanged. The event records operator provenance, the original attempt snapshot, human evidence, and explicit zero resend/provider-call flags. It records the confirmation time, not an invented receipt time.

A unique event identity per action/attempt makes repeated identical confirmations return the existing event. Conflicting evidence fails closed. Any persistence error rolls back the event and both state updates together. The terminal action and draft states block execution; the original ambiguous attempt still prohibits adapter retry.

The authenticated operator route is `POST /api/operator/cases/{case}/actions/{action}/confirm-delivery`. Required JSON fields are `draft_revision_id`, `approval_request_id`, `execution_attempt_id` (decimal strings), `recipient`, `subject`, and `evidence_note`. It is a human attestation endpoint, not independent provider delivery verification. Database function execution is restricted to the service role/owner and respects invoker permissions.

Apply `20261003000100_phase_08_human_delivery_reconciliation.sql` before using the route, and deploy the application support before storing the new draft status. The migration performs no historical row rewrites. Provider-free PostgreSQL tests use a local database and roll back fixtures, including migration DDL. No drafting model, editorial, realization, or date-normalization behavior changes.
