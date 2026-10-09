# Outlook inbound staging implementation and stopped preflight

9 October 2026. **Not ready for real ingestion.** Provider-free implementation and staging deployment are complete, but the one authorized real preflight stopped on `inbound_cursor_scope_forbidden`. The returned cursor resource identity must be reconciled before readiness can be claimed. No second preflight was attempted.

## Outlook Inbound Architecture

`OutlookInboundAdapter → InboundEmailEnvelope → provider message binding + InboundSourceRecord → existing governed timing observation intake → inquiry intake`. New synthetic cases reuse existing application case registration; test email injection is never used. See [architecture](ARCHITECTURE.md) for deliberate limits and source locations.

## Graph Retrieval Strategy

One bounded Inbox delta page per authenticated manual sync. Initial received-time lower bound is explicitly configured; subsequent reads use the durable cursor. Immutable IDs are requested throughout. Metadata is read first, then full messages only for admitted synthetic messages/bound conversations. No webhooks or background polling.

## Provider Message Identity

Unique mailbox + immutable Graph message ID. Conversation ID, InternetMessageId, sender, recipients and receipt time are retained. Subject/sender similarity never routes a follow-up to an existing case.

## Raw Provenance

Original provider JSON and body are immutable; deterministic normalized text is separate. Hashes, source IDs and retrieval audit records tie evidence to provider identity. Attachment identity/name/type/size/inline metadata is bounded; bytes are not ingested.

## Case Association

Only exact mailbox/conversation bindings resolve existing cases. New-case admission additionally requires the configured synthetic sender, recipient, exact subject and no reply-reference headers. Unrelated mailbox bodies are not fetched or stored.

## New Case Creation

Existing staging `create_test_case` creates revision zero with `custom_scope` and unknown summaries. Real provider source persistence follows normal observation repository mechanisms. This preserves the existing staging case path without inventing a production registration service or populating business facts from email transport.

## Follow-Up Association

A second message with the bound conversation uses the original case and creates one new source. The provider-free fixture supplies missing event times through that follow-up and proves governed revision advancement. Same sender or similar subject in a different unbound conversation cannot select the existing case.

## Ambiguity Handling

Admitted unknown conversations enter `needs_review` without a case or automatic reply. Authenticated review endpoint: `GET /api/operator/outlook-inbound/review`. Provider/cursor errors roll back ingestion and stop. Review-state resolution is deliberately manual/deferred; no silent adoption exists.

## Exactly-Once / Checkpointing

Mailbox transaction lock, unique message identity, immutable conversation binding and source/case validation protect persistence. Whole-page effects and checkpoint advancement commit atomically. Fault-injection tests prove rollback before checkpoint advancement; replay and a fresh adapter instance reuse existing sources/cases/observations. Tombstones do not delete history.

## Governed Observation Handoff

Existing timing extraction and structured observation/normal inquiry intake are reused. Provider received time drives date normalization. The case evidence reader accepts the provider-origin event for downstream reasoning and drafting. No new general prose-to-fact extractor is introduced: guest counts and other prose remain evidence for existing structured workflows, not transport-authorized facts.

## Provider-Free Certification

Tests cover real local PostgreSQL persistence, new/replayed sources and cases, follow-up routing/revision, unsafe association, raw immutability, HTML, date provenance, attachments, checkpoint failures/restart, database binding checks, unauthorized scope, disabled gates, metadata-only admission and token-redacted cursor diagnostics. The local end-to-end fixture also runs existing reconciliation, inquiry waiting, deterministic governed draft preparation and Asana projection preparation with provider HTTP blocked.

## Tests

Latest diagnostic revision: **39 focused tests**, **629 Phase 8 tests**, **846 full repository tests**, all passed. No skips. `git diff --check` passed. Logs/JUnit files are alongside this report. Existing collection warnings remain; no runtime code change to the certified drafting provider/planner/realization, Outlook adapter/contract, or Asana projection modules. These were compared against runtime baseline `59e3a03`.

## Deployment

Branch: `codex/outlook-inbound-staging`; main unchanged.

- Bridge commit `912bef81d41c2ced687106049cdd8aa48e1fbe53`, live staging deploy `dep-db4afve7bikc73e4cgc0`.
- Gate shutdown deploy `dep-db4aherncjis73cckneg` confirmed live; health verified ingestion and preflight disabled.
- Diagnostic-only successor `1c5a21361ee0e4b75d7f6a9d6229d1f3566c12e9`, live deploy `dep-db4aijd9fdbs73bbv1dg`, preserves rejected origin/path and query parameter names, with cursor token values redacted. It does not relax validation or perform any extra Graph call.
- Migration `20261009000100` applied only to staging project `mspcopnsbounmdpivkvq`. It adds four inbound tables and integrity guards. All four remain empty.

## Real Read-Only Mailbox Preflight

Human separately authorized one bounded read-only preflight. Exactly one hosted preflight was invoked, with no retry. It returned HTTP 409, `INBOUND_STOPPED: inbound_cursor_scope_forbidden`.

Control-flow evidence establishes successful token acquisition, accepted Inbox metadata response and accepted delta response up to continuation-link validation. Expected network path: one OAuth token request, one Inbox metadata GET, one delta metadata GET. These are inferred from the error stage and implementation, not independent network tracing. No full body or attachment request was reached.

The original error did not preserve the returned cursor's origin/path. Its exact mismatch therefore remains unknown; no URL normalization or wider scope has been guessed. Diagnostic support is now prepared to capture that evidence on a separately authorized preflight. Entra/RBAC were unchanged. Inbox read access worked; tenant-wide negative authorization has not been independently re-audited, and no unauthorized/production mailbox was accessed.

## Proposed Synthetic Email

**Do not send yet.** Exact sender, recipient, subject, initial body and same-conversation follow-up are in [SYNTHETIC_EMAIL.md](SYNTHETIC_EMAIL.md).

Configured mailbox: `Serinya@whennaturecalls.nl`. Synthetic sender: same human-operated account. Subject: `SYNTHETIC TEST — WNC Outlook inbound certification`.

## Expected Real Provider Activity

Further activity requires authorization. A diagnostic preflight would acquire one token and make at most two Graph GETs (Inbox identity and one bounded metadata delta page), with no ingestion. Later authorized sync reads one metadata page, up to ten admitted full messages and up to one bounded attachment-metadata request per admitted message. There are no Graph mutation, email-send or Asana execution calls in this inbound path.

## Safety Gates

Ingestion gate false; read-only preflight gate false; Outlook send false; Asana real execution false. Outlook remains `configured_draft_only`, Asana `configured_but_disabled`. Hosted shutdown health is saved as `health_after_shutdown.json`; final diagnostic-deployment health is `health_final.json`, with all gates still disabled.

Post-preflight database audit: zero inbound messages, zero conversation bindings, zero checkpoints, zero sync events. Cases **424, 584 and 585** exactly match their protected rows. No real case, observation, draft, approval, workflow execution attempt, email or Asana task was created by this task. OpenAI calls, Graph mutations and production changes: zero.

## Final Marker

**No ready-for-human-ingestion or certification marker is emitted.** This is a stopped cursor-validation preflight, not a demonstrated Microsoft permission insufficiency or a material architecture redesign. The next required evidence is the token-redacted continuation resource identity from one newly authorized bounded read-only preflight. Your explicit stop-on-uncertainty rule and one-preflight authorization are the reasons further real reads are paused.
