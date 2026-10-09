# Real Outlook inbound staging certification

9 October 2026. **The real synthetic initial message and follow-up are certified through the staging Inbox bridge.** One case, two provider messages, two source records, one exact conversation binding, governed timing completion, real duplicate-message suppression and durable checkpoint replay were verified. No client response or provider mutation was performed by this task.

## Certified lineage

- RentalCase **586**, revision **2**, active event window **14:00–18:00 Europe/Amsterdam** (stored as **13:00–17:00 UTC**) on **12 November 2026**.
- Initial source **3104**, validated timing observation **2721**: 12 November 2026, with times initially missing.
- Follow-up source **3105**, new immutable provider message, same provider conversation and same case.
- Follow-up observation **2722** remains quarantined as the original extraction evidence.
- Corrected observation **2723** is validated: **12 November 2026, 14:00–18:00**, using authored reply text and the original provider receipt timestamp.
- Exactly **two source records**, **two messages**, **one case**, **one conversation binding**. No authoritative facts or execution attempts were created. Three observations comprise two validated observations and the preserved quarantine.
- Raw provider JSON, full original/normalized bodies, provider message/conversation/InternetMessageId identities and evidence hashes remain stored. Hashes were independently recomputed from stored payloads. The initial message/source/observation stayed unchanged.

## Real replay evidence

Initial ingestion created checkpoint **1**; its replay advanced to **2** with no new records. The follow-up page advanced to **3** and contained both the new message and a real redelivery of the original provider message. The original returned `duplicate: true`, source **3104**, case **586**; the sync event recorded duplicate count **1**. No duplicate source, case or observation was created.

After the reply correction and a runtime redeploy, normal hosted sync resumed the durable checkpoint, returned an empty page and advanced to **4**, ready. Case/source/observation/event/raw-evidence rows and totals were identical before and after replay. Repeating the explicit correction also returned observation **2723**, without a duplicate or another revision advance.

## Safe reply correction

The initial follow-up extraction correctly stopped at the existing ambiguity guard: Outlook quoted the original message's `Sent: October 9, 2026` header alongside the requested November event date. It did not guess or promote authority.

The narrow inbound fix recognizes exactly one Outlook `divRplyFwdMsg` HTML boundary only when provider reply-reference headers exist. Timing extraction uses authored text above that boundary. Full immutable evidence remains unchanged. Missing/ambiguous boundaries preserve the original ambiguity behavior; multiple dates in authored text remain quarantined.

Source **3105** was explicitly reprocessed from stored evidence via the bridge's staging-only remediation function. That function checks the hash, mailbox/sender/recipient, conversation/case binding and original quarantine, then calls the existing observation validator/router and normal inquiry intake. It appended observation **2723** to the existing source, advanced the case to revision **2**, and retained observation **2722**. It made **zero provider calls**, source/case inserts, checkpoint changes or direct authority writes. No accepted drafting, outbound or Asana architecture was changed.

Earlier narrow fixes in this certification also accepted Graph's equivalent Inbox OData path and the exact project-qualified Supabase session-pooler route. No permissions, credentials or tenant mailbox scope were changed.

## Validation and runtime

- **69 focused tests**, **659 Phase 8 tests**, **876 repository tests** passed; no failures or skips. Existing collection warnings remain.
- Coverage includes exact cursor paths/origin, opaque state, wrong mailbox/folder, replay, restart, crash rollback, raw provenance, conservative association, reply boundaries, ambiguity retention and append-only correction idempotency.
- `git diff --check` passed.
- Runtime: **5cf64d975e8779040674bbc1488028d51288a758** on staging service **srv-da2m6qdg1s2s73d10ro0**; code deployment **dep-db4b6vdg1s2s738sj7tg**.
- Main and production were not modified.

## Scope and activity

Only **Serinya@whennaturecalls.nl** was read. A real hosted request attempting to override the mailbox to `booking@whennaturecalls.nl` returned **INBOUND_SCOPE_OVERRIDE_FORBIDDEN** before runtime/provider access. Provider-free wrong-mailbox/folder/origin tests also passed. No request was sent to an unauthorized mailbox; this certifies application isolation, not a fresh independent audit of tenant-wide Exchange RBAC enforcement.

This follow-up turn performed two successful hosted syncs. Control flow implies **three Graph GETs** (follow-up delta, admitted follow-up body, replay delta) and **two token acquisitions**. These are code-path counts, not independent network traces. Correction and scope-negative checks made no provider calls. Human-sent synthetic emails are the test input; agent sends, Graph mutations, OpenAI calls, Asana executions, new execution attempts and production changes are **zero**.

Protected case lineages **424, 584 and 585** exactly match their baseline rows. No historical approvals, attempts, outbound revisions or Asana bindings were altered.

## Closure

Closure deployment **dep-db4b7u7lot8c738eptgg** is live on the same runtime. Hosted health and disabled-gate rejection evidence are saved alongside this report. At closure:

- `STAGING_ALLOW_REAL_OUTLOOK_INBOUND=false`
- `STAGING_ALLOW_OUTLOOK_INBOUND_PREFLIGHT=false`
- `STAGING_ALLOW_REAL_OUTLOOK_SEND=false`
- `STAGING_ALLOW_REAL_ASANA=false`

Outlook remains `configured_draft_only`; Asana remains `configured_but_disabled`. The durable window stays `2026-10-09T09:02:18Z` and checkpoint version **4** is ready. No background polling is enabled.

**OUTLOOK_REAL_INBOUND_STAGING_CERTIFIED**
