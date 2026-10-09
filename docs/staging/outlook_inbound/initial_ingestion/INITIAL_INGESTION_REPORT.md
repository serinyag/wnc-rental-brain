# Real initial Outlook inbound verified — follow-up pending

9 October 2026. The human-confirmed synthetic email was retrieved through the hosted normal Inbox sync endpoint and created **case 586**, **source 3104**, and one validated timing observation. Case revision is **1**. One mailbox/conversation binding and one provider message exist. Raw provider evidence and the envelope are persisted; their hash was recomputed and verified. Provider immutable message ID, conversation ID and InternetMessageId are recorded in `result.json`.

The initial date is 12 November 2026, explicitly sourced to the client's email and provider receipt timestamp. The missing start/end times remain absent. Normal governed inquiry intake ran and created open questions. No authoritative facts, automatic responses, outbound actions executed, or execution attempts were created.

## Narrow runtime correction

The first sync stopped at the database destination guard, before token acquisition, Graph access or database connection. A read-only database audit proved every baseline row/count unchanged and no checkpoint. Render uses the staging Supabase session pooler; the original guard accepted only the direct host.

The correction permits exactly the observed session-pooler host and staging-project-qualified username, or the existing direct staging connection. PostgreSQL scheme, `postgres` database and session port 5432 are required; query routing overrides, other project usernames, hosts and databases are rejected before provider access. No credential or hosted database configuration was changed. No Entra/RBAC changes occurred.

Runtime commit **deca4b889336a7912731ac341a154f3d21b1693d**, staging deployment **dep-db4b1pu7bikc73e5sga0**. Tests: **65 focused**, **655 Phase 8**, **872 repository**, all passed without skips. `git diff --check` passed. Main and production remain untouched.

## Initial ingestion and replay

The second sync succeeded: one delta metadata record, one admitted full-message read, checkpoint version **1**, ready. The next normal sync resumed from the durable Graph cursor and returned an empty page, checkpoint version **2**, ready. Full case, source, observation, event, raw-message and conversation rows were unchanged across replay. No duplicates appeared. The real replay did not redeliver the same message; provider-free tests separately prove the same-message duplicate branch.

Across this turn: three sync invocations, one early guard stop, two successful syncs. Code-path evidence implies **three Graph GETs and two token requests**; these are not independent network traces. Zero sends, Graph mutations, OpenAI calls, Asana executions, new execution attempts or production changes.

Read-only comparisons confirm protected cases **424, 584 and 585** unchanged. No unauthorized mailbox was accessed. Provider-level negative RBAC enforcement remains independently unverified; application scope protections passed tests.

## Human follow-up

Reply to the received synthetic message in the **same conversation**, from and to **Serinya@whennaturecalls.nl**, keeping its reply subject. Send only:

> Hi WNC,
>
> Continuing the same synthetic staging enquiry: please use 14:00 to 18:00 on 12 November 2026.
>
> Thank you,
> Synthetic WNC client

The existing authorization covers the follow-up ingestion and replay. Expected: one new provider message/source, the same conversation and case 586, normal governed timing update, no duplicate case. Final certification is not yet claimed.

## Handoff safety

Inbound, read-only preflight, outbound-send and Asana gates are disabled at handoff; hosted health evidence is saved alongside this report. The initial window remains `2026-10-09T09:02:18Z`; it must not be changed after checkpoint creation.

**OUTLOOK_INBOUND_WAITING_FOR_SYNTHETIC_EMAIL** — waiting for the same-conversation follow-up.
