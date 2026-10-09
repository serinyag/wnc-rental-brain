# Real Outlook inbound staging bridge

This bounded staging implementation preserves the closed drafting, outbound Outlook and Asana components. It introduces provider evidence and routing, not commercial or operational authority.

## Transport and admission

An authenticated operator calls `POST /api/operator/outlook-inbound/sync` with an empty JSON object. There is no scheduler or automatic outbound execution. Independent `STAGING_ALLOW_REAL_OUTLOOK_INBOUND` defaults to false. A separate `STAGING_ALLOW_OUTLOOK_INBOUND_PREFLIGHT` authorizes read-only preflight without ingestion.

Graph Inbox delta retrieval uses an explicit received-time lower bound, one page per invocation, a requested page size of ten, immutable IDs on every request, and strict same-host/mailbox/folder cursor validation. Redirects are forbidden. Expired cursors or malformed/partial responses stop execution; there is no automatic reset or retry.

Delta requests select message metadata. Full bodies are fetched only for the configured synthetic sender/recipient and either a known bound conversation or the configured synthetic subject marker. Unrelated bodies are not fetched or persisted. Attachment requests select metadata only, capped at twenty attachments; attachment content is deferred. Larger attachment collections stop for review.

## Evidence and identity

`InboundEmailEnvelope` is provider-neutral. Original provider JSON/body, separate deterministic normalized text, message and conversation IDs, InternetMessageId, received timestamp, recipients, sender, attachment metadata and a SHA-256 evidence hash are retained. HTML normalization does not access links or load external content. Raw evidence and bindings are append-only at the database boundary.

Application identity is `(outlook, canonical mailbox, immutable Graph message ID)`, never subject or body similarity. Inbox removals are recorded as retrieval events and cannot delete canonical history or complete work.

## Case association and creation

Exact mailbox/conversation binding routes follow-ups. Sender identity alone never selects a rental. A new case requires the explicitly configured synthetic sender, recipient and exact new-enquiry subject, an unbound conversation, and no reply-reference headers. Other admitted, unbound conversations are `needs_review`; no case or reply action is created for them. Review metadata is available at authenticated `GET /api/operator/outlook-inbound/review`. No automatic association-review resolution is implemented.

New synthetic cases reuse the application's existing `create_test_case` creation path, starting at revision zero with `custom_scope` and unknown summaries. This is the existing staging case-registration path, not test email injection. Real sources are persisted directly through the existing observation repository, and provenance uses `outlook_inbound_evidence_recorded`, never `test_console_raw_evidence_recorded`. No production case-creation service is claimed.

## Governed handoff

The bridge reuses the existing `timing_components` extraction, structured observation ingestion and `apply_inquiry_intake`. Provider received time drives date normalization. Timing observations remain subject to normal validation/promotion/proposed-change semantics. It does not add a new general natural-language extractor: guest counts, commercial requests and operational details remain available as source evidence for existing structured observation/operator workflows; they are not invented or promoted by transport.

The existing case evidence reader accepts the new provider-origin event so reconciliation and governed drafting can consume the same evidence interface. The local fixture exercises case view, normal reconciliation, inquiry waiting, deterministic governed draft preparation and Asana projection preparation. It executes no providers. The live bridge itself stops at governed inquiry intake.

## Transaction and restart behavior

Migration `20261009000100` adds checkpoint, conversation binding, message evidence/binding and retrieval-event tables. All have RLS with no anonymous/authenticated direct grants. A mailbox-scoped transaction lock serializes sync; per-message database uniqueness also protects replay. The entire bounded page, new cases, sources, observations, intake effects, retrieval event and checkpoint version commit together.

Failure anywhere before commit rolls back everything, including checkpoint advancement. A response lost after commit is replay-safe: the durable checkpoint and message keys survive. A duplicate returns the existing source/case without re-extracting observations, drafting or executing work. A changed initial-window configuration requires review. Case/source linkage is checked by a database trigger.

## Scope and permission audit

The existing Outlook adapter already performs authenticated body reads and documents `Mail.ReadWrite`. Microsoft documents that permission as sufficient for reading messages; no additional permission has been demonstrated necessary. Neither Entra nor Exchange configuration is modified. Actual current Inbox access is established only by the separately authorized preflight. Application rejection of another mailbox is tested without accessing any unauthorized mailbox; this does not independently prove the tenant's complete Exchange/Entra effective permission scope.

Microsoft references:
- [Message delta](https://learn.microsoft.com/en-us/graph/api/message-delta)
- [Incremental message retrieval](https://learn.microsoft.com/en-us/graph/delta-query-messages)
- [Exchange application RBAC](https://learn.microsoft.com/en-us/exchange/permissions-exo/application-rbac)

## Deliberate limits

Staging-only; one configured mailbox and synthetic admission contract. No webhook, background worker, general enquiry classifier, attachment-content ingestion, arbitrary mailbox selection, permission widening, automatic send, automatic Asana execution, or silent resolution of unknown associations. The ready-for-human marker concerns this bounded synthetic certification, not production readiness or completed real inbound certification.
