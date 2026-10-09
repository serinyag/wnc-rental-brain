# Outlook inbound cursor unblocked — awaiting synthetic email

9 October 2026. **Read-only staging preflight and cursor replay passed. Real inbound certification remains pending the human-sent synthetic email.** This report supersedes the earlier stopped-preflight readiness assessment, while preserving that historical evidence.

## Root cause and correction

The application emitted `inbound_cursor_scope_forbidden` after successful token, Inbox identity and delta-page reads. The new redacted diagnostic established:

- Initial path: `/v1.0/users/Serinya%40whennaturecalls.nl/mailFolders/inbox/messages/delta`
- Returned path: `/v1.0/users/Serinya@whennaturecalls.nl/mailFolders('inbox')/messages/delta`
- Both origins: `https://graph.microsoft.com`
- Returned query parameter: `$deltatoken`; its value was never logged.

Graph used OData key syntax for the same Inbox. The validator now permits exactly the original path and this equivalent path for the configured mailbox. Percent decoding of path identity already existed. The full opaque query is preserved byte-for-byte. Other origins, mailbox/folder identities and endpoint families remain forbidden; no broad prefix matching or identity guessing was introduced.

No Entra permission, Exchange RBAC assignment, credential, or tenant scope change was necessary or performed. The provider successfully returned data under the existing configuration. No `/me` request was made.

## Validation and deployment

Runtime commit: `39a487c605ba1e8fe5b0d22156099092b2958b18`, deployed only to staging service `srv-da2m6qdg1s2s73d10ro0`; code deployment `dep-db4aqje0tbcc73dor1m0`. Main and production were untouched.

Provider-free results: **56 focused**, **646 Phase 8**, **863 full repository** tests passed, with no failures or skips. Existing collection warnings remain. Tests exercise nextLink and deltaLink in both path forms; unchanged opaque query state; wrong origin, mailbox, folder and endpoint rejection before fetch; and bounded read-only preflight replay. Existing persistence, crash rollback, restart, duplicate prevention, follow-up and provenance tests passed. `git diff --check` passed.

The authorized remediation used two hosted preflight invocations: one diagnosed the mismatch and one passed after deployment. The passing invocation acquired a token, read Inbox identity, read one bounded delta metadata page, and followed its returned cursor once. Both pages contained zero records; both statuses were ready. No durable checkpoint, source, observation or case was created.

The implementation implies **five Graph GETs and two OAuth token requests** across these two invocations; these counts are control-flow evidence, not independent network tracing. There were zero Graph mutations, sends, OpenAI calls, Asana executions, execution attempts or production changes.

Negative scope validation was proved in provider-free application tests. No request was sent to `booking@whennaturecalls.nl` or another unauthorized mailbox. Current tenant-wide negative RBAC enforcement was not independently re-audited; do not interpret the successful staging preflight as such a proof.

## Practical handoff

The available Outlook browser session for Serinya requires a password. No credential was requested, entered, changed or extracted. The human should send the exact initial message in [SYNTHETIC_EMAIL.md](../SYNTHETIC_EMAIL.md) from **Serinya@whennaturecalls.nl** to **Serinya@whennaturecalls.nl**. The subject is **SYNTHETIC TEST — WNC Outlook inbound certification**. Send the initial message only; the same-conversation reply follows after initial ingestion and replay verification.

Initial ingestion window was advanced, before any message or checkpoint exists, to **2026-10-09T09:02:18Z**. Sender, recipient and subject restrictions remain unchanged. The user has already authorized the later bounded ingestion and follow-up certification; no new architecture review or routine diagnostic approval is required.

No synthetic email has been sent or ingested by this task. Real source/case creation, durable checkpoint replay, same-conversation follow-up and governed case advancement still require certification. No final success marker is claimed.

## Closure

Closure configuration deployment `dep-db4arfp42hec73amtm30` is live on the same runtime commit. Hosted health and database isolation evidence are recorded beside this report. The inbound, preflight, outbound-send and Asana gates are disabled at handoff. Outlook remains `configured_draft_only`; Asana remains `configured_but_disabled`. All four inbound tables remain empty. Protected cases **424, 584 and 585** match their baseline rows exactly.

**OUTLOOK_INBOUND_WAITING_FOR_SYNTHETIC_EMAIL**
