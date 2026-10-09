# Governed operational resolution — case 586

## Outcome

`WNC_OPERATIONAL_RESOLUTION_AUTHORITY_CERTIFIED_INTEGRATION_BLOCKED`

The operational authority bridge works in staging. Case **586 advanced from revision 3 to revision 5** through two explicit, typed, authenticated synthetic operator submissions. No replacement case was created. The final outbound approval checkpoint has **not** been reached.

The separate remaining boundary is the layout/capacity workflow: missing configuration is projected as blocking internal work, while the frozen draft approval guard blocks any draft containing that annotation. No requested layout is present in the certified client evidence, and no client-owned layout clarification question is created by the current core intake path. Availability and projection feasibility cannot supply that missing authority. The requested journey permits unknowns to remain pending/asked, but the current ownership/approval path does not permit an approval-ready clarification response in this state. This report does not bypass that guard or invent a client layout.

## Authority and provenance

| WorkflowAction | Accepted event | Case fact | Subject/outcome | Revision |
|---|---:|---:|---|---:|
| 1634 | 17144 | 1058 | Studio availability: **AVAILABLE** | 4 |
| 1633 | 17145 | 1059 | Requested projection display setup: **FEASIBLE** | 5 |

Both records are explicitly **staging synthetic operator evidence**, not real WNC operational evidence. The authority is derived from the authenticated staging operator, not from a JSON actor claim, an LLM or Asana. The exact scope is Studio space, **12 November 2026, 14:00–18:00 Europe/Amsterdam** (13:00–17:00 UTC), case 586 and each named semantic obligation/action. No booking, capacity approval, catering approval, microphone, technician, price change, waiver or other date was confirmed.

Both submissions were replayed through the authenticated endpoint. Each returned its original event/fact/revision; no extra acceptance event or case revision resulted. Replay after reconciliation was also verified. Existing inbound sources, observations and effects remain unchanged.

The implementation composes native WorkflowEvents, RentalCaseFacts and revision fencing. Evidence is append-only; current facts must match their acceptance event and current interval. Corrections require an explicit current predecessor. There is one authority state per operational kind and exact event scope, preventing competing truths from replacement actions. Partial technical coverage does not suppress the whole obligation. External-party evidence is rejected unless a separately governed acceptance contract exists; no such authority was invented here. Existing CaseDecision handling is unchanged.

See [authority contract](AUTHORITY_CONTRACT.md) for admission and correction details.

## Current reasoning and frozen drafting inputs

Current technical projection **607**, revision 5, is `known_yes` / `DETERMINISTIC_CURRENT`, grounded in event **17145**. Capacity projection **606** remains `unknown_internal` / `INSUFFICIENT_CURRENT_AUTHORITY`. Blocker **2386** remains open.

The existing governed drafting contract includes these narrowly permitted assertions:

- “The Studio is available for 12 November 2026 from 14:00 to 18:00 (Europe/Amsterdam).”
- “The requested projection setup is feasible for 12 November 2026 from 14:00 to 18:00 (Europe/Amsterdam).”

Availability and technical confirmation no longer appear in pending resolution items. Capacity/layout remains a blocking internal annotation. The typed fact extension uses the existing planner and realization pipeline; no new planner, date inference, tone system or authority hierarchy was introduced. Positive and negative outcomes are checked for realization, and broader unsupported claims remain rejected. Internal evidence/case identifiers do not enter the client generation payload.

Phase 7's prior knowledge-retrieval ContextPackage remains policy/knowledge context; operator evidence is not misrepresented as a Phase 4/5/6 document. Current operational truth is consumed through the existing Phase 8 case context and reasoning projection. No new embedding/retrieval model call was made.

**Final DraftRevision: none. Final outbound WorkflowAction: none. Final ApprovalRequest: none.** No final subject/body or hashes are fabricated. No model call was spent generating a purported final response that the unchanged approval guard would block.

## Real Asana proof

Exactly one master: **1219351043478952**.

| Subtask | Provider ID | Final state |
|---|---|---|
| Studio availability | 1219350621402939 | Completed |
| Requested layout against capacity | 1219350621444728 | Open |
| Event-specific projection setup | 1219350811582361 | Completed |

Initial projection: action **1635**, attempt **26**, four confirmed creates. Update: action **1637**, attempt **27**, three confirmed updates. Total: **7 mutation requests / 7 confirmed mutations**. Both attempts succeeded. Provider observations matched the saved projections before and after update. Both execution replays were blocked with `action_already_succeeded`; there are exactly two attempts, one per authorized projection action. The master and all three subtask bindings were preserved; no duplicate master or active subtask was created.

The existing projection retains one open capacity work item. The revised capacity blocker is 2386; the provider item retains its existing semantic work binding to avoid creating a duplicate during this stopped journey. No supplier or fee-decision work existed for this case and none was invented. Existing display fallbacks in the certified projection (client label and scope summary) were not redesigned in this authority task; canonical Studio scope is explicit in the case and resolution contracts.

## Remediation encountered

The first authenticated resolution request returned an application rejection. Read-only inspection verified **zero acceptance events and revision 3** before any retry. The cause was that the certified post-Asana reconciliation superseded unexecuted confirmation actions even though their obligations remained current. The gate was corrected to check current semantic obligation, not infer eligibility/truth from lifecycle status alone. The correction passed the complete provider-free suite before deployment and retry. This was not an ambiguous Asana outcome; no provider mutation was retried.

A defensive cross-action conflict fence and a client-payload identifier boundary were also tested and deployed. Staging schema changes only add/replace the narrow acceptance function and its privileges; no production schema was touched.

## Verification and closure

- **25 new authority tests**, included in **82 focused integration tests**.
- **684 Phase 8 tests** passed, with 26 existing warnings.
- **901 full repository tests** passed, with 41 existing warnings.
- No failures or skips. `git diff --check` passed.
- Closed case lineages **424, 584 and 585** match their protected baselines.
- Original case 586 inbound evidence is unchanged; only two operational facts and their immutable evidence were admitted.
- Outlook send, Outlook inbound, inbound preflight and real Asana gates are disabled at closure. Outlook remains `configured_draft_only`; Asana is `configured_but_disabled`.
- **Graph calls 0; outbound sends 0; OpenAI external calls 0; production changes 0.**

Live staging deployment: `dep-db4c40ks728c73a9uung` (verified after deployment, with gates disabled). Runtime commit: `ad928321a140e7c1de1a733a91ba7bd42f2cf003`, on `codex/outlook-inbound-staging`; main was not changed. Machine-readable evidence is in `result.json`, `health_final.json`, `current_context.json` and the bounded action/evidence records in this directory. The existing journey timeline is continued in `../case586_integrated/JOURNEY_TIMELINE.md`.

The next boundary is **missing-layout ownership and clarification eligibility**, not availability/technical authority. A later continuation must obtain/record the requested configuration through a governed path and evaluate capacity, or explicitly define a narrowly scoped clarification-response path that preserves consequential commitment guards. This task did neither by assumption.
