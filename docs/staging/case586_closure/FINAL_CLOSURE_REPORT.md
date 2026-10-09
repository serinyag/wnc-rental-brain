# Case 586 — integrated staging closure

**WNC_FULL_RENTAL_STAGING_END_TO_END_CERTIFIED**

Completed 9 October 2026. Case **586**, revision **7**. This is a synthetic staging certification, not a real booking or production-readiness certification. The final message reached the configured staging Inbox. No second final send or production work was performed.

## Final lineage

| Record | Final result |
|---|---|
| Inbound sources | 3104, 3105, 3106; one inbound conversation and one case |
| Client layout | Observation 2729 → fact 1060 / event 17159 → revision 6 |
| Capacity/layout result | Action 1632 → event 17160 / fact 1061 → revision 7 |
| Asana update | Action 1639 / attempt 28; succeeded, two updates, zero creates |
| Final immutable draft | DraftRevision 387, current; content unchanged after approval |
| Exact approval | 466, approved; `workflow_action:1640:draft_revision:387` |
| Final Outlook action | 1640, reconciled to `succeeded` |
| Final execution attempt | 29, exactly one; original `adapter_outcome_ambiguous` preserved; retries disabled |
| Receipt | Graph matched exact sent and Inbox copies; received **11:00:28 UTC** |
| Reconciliation | Event 17175; repeated confirmation returned the same event |
| Draft delivery status | `human_confirmed_delivered` through the existing reconciliation contract |

The reconciliation contract retains its existing human-confirmation enum. Its evidence note explicitly identifies **authorized synthetic operator confirmation based on provider Inbox evidence**, and explicitly says that no human inbox observation is asserted. It does not rewrite the original ambiguous attempt.

## Inbound transport and provenance

The original synthetic enquiry and date follow-up remain unchanged. A minimal synthetic client reply supplied theatre-style seated seating for the **existing 24 guests**, without changing the event, timing, caterer, or projection request.

The fixture used Graph's [createReply operation](https://learn.microsoft.com/en-us/graph/api/message-createreply?view=graph-rest-1.0) and the existing send transport. Before sending, it verified the exact original conversation, sole staging recipient, synthetic subject, draft state, and exact body. Its durable start event blocks repeat execution after a crash or uncertain provider outcome. This input-fixture send is distinct from the one final client-response send.

| Source | Provider message suffix | Evidence |
|---|---|---|
| 3104 | `oZ8ZeAAA` | Original Studio team workshop enquiry: 24 guests, external caterer, basic projection |
| 3105 | `oZ8ZmgAA` | Authored follow-up establishing 12 November 2026, 14:00–18:00 Europe/Amsterdam |
| 3106 | `oZ8bcQAA` | Synthetic theatre-style seated layout preference |

All three inbound messages have this exact conversation ID:

`AAQkADgwMGM0Y2JhLTg2M2EtNDkwNy05YWU1LTU1MmI0MGM4ODRkMwAQAG4fYoUqabVKl4lpz9tZa3A=`

Full message IDs and SHA-256 hashes are in [inbound_proof.json](inbound_proof.json). The closure audit rehashed every immutable raw provider payload. Original source records, observations, effects, and prior governed facts compared equal to the pre-continuation snapshot.

Checkpoint 5 ingested source 3106 exactly once and recognized provider redelivery of source 3105 as a duplicate. Checkpoint 6 returned no new records. No case was created, no conversation association was guessed, and no raw database injection supplied the reply.

Operator extraction bound observation 2729 directly to source 3106. The existing case-fact mutation service then recorded explicit synthetic operator validation of the client preference. Its observation effect remains an immutable record that extraction alone did not promote truth. Capacity was established separately.

## Case revisions and authority

| Revision | Governed change | Source |
|---|---|---|
| 0–1 | Normal synthetic case creation and missing core inquiry questions | Source 3104; original inbound intake |
| 2 | Correct authored event interval | Observation 2723 / event 17121; original quoted-header observation 2722 remains quarantined |
| 3 | 24 guests, Studio rental scope, team workshop | Observations 2724–2726 / events 17128, 17130, 17132 |
| 4 | Studio availability confirmed for the exact interval | Synthetic WNC operator event 17144 / fact 1058 |
| 5 | Requested projection setup feasible for the exact interval | Synthetic WNC operator event 17145 / fact 1059 |
| 6 | Theatre-style seated client layout preference | Observation 2729 / event 17159 / fact 1060 |
| 7 | Independent practical capacity/layout result | Synthetic WNC operator event 17160 / fact 1061 |

Canonical timing remains **2026-11-12 13:00–17:00 UTC**, equivalent to **14:00–18:00 Europe/Amsterdam**. Studio scope is stored on the case, rather than being inferred from generated prose. Catering and technical requests retain their original source-backed observations 2727 and 2728.

The capacity check used `api.evaluate_capacity('studio_space', null, 'seated', 24, current_date)`, which returned within capacity. Published rule `CAPACITY_STUDIO_SEATED` has a maximum of 40, subject to practical layout conditions. The separate synthetic operator evidence explicitly confirmed 24 chairs, clear routes, and projection sightlines for this event. It did not establish a booking, fee waiver, supplier contact, or commercial exception.

The capacity authority extension is limited to synthetic case 586, Studio, seated layout, and 24 guests. It binds the complete canonical layout and guest count; changed inputs invalidate that result. Event 17160 replayed without another fact or revision. Existing availability and technical results remain current and unchanged. Task completion was never used as truth.

## Asana

| Task | Stable provider ID | Final state |
|---|---|---|
| Master | 1219351043478952 | Open rental inquiry; canonical Studio scope shown |
| Availability | 1219350621402939 | Completed |
| Capacity/layout | 1219350621444728 | Completed |
| Projection setup | 1219350811582361 | Completed |

Workspace `1208455784737302`; project `1217642260793817`.

The prior certified stages used actions 1635/1637 and attempts 26/27. This continuation used action **1639**, attempt **28**, updating only the master and existing capacity subtask. The two already completed checks stayed completed. Provider observation returned `matches_projection`, with no differences. Provider IDs and semantic keys match the previous bindings. Replay returned `action_already_succeeded` with no new attempt. There is one master and the same three subtasks, with no new active duplicate.

Action 1638 was a provider-free preview of the pre-fix summary and was never executed. The narrow summary fix reads the canonical case rental scope. Supplier/catering evidence remains available in governed context; no supplier contact, supplier approval, fee decision, or waiver was fabricated. The master remains open because this synthetic communication is not a booking completion.

## Current reasoning and frozen drafting

The current Phase 7 → Phase 8 run completed all three retrieval layers: Phase 4 deterministic authority, Phase 5 guidance, and Phase 6 historical context. The final run bound canonical `studio_space`, guest count 24, and `seated` directly into the Phase 4 plan rather than relying on prose extraction. Historical retrieval remained context only. See [reasoning_grounded_summary.json](reasoning_grounded_summary.json).

All three accepted operational results enter the governed drafting contract. There are **no remaining resolution items and no blocking operator annotations**. Supplier constraints and the normal commercial snapshot remain in context; the frozen planner deferred them because the current client turn only clarifies seating.

The first model response failed the unchanged safety validator; event 17167 records the rejection and no DraftRevision was created. A narrow provider-instruction correction removed a contradiction between the blanket availability prohibition and the already-supplied exact operational assertions. The instruction now requires those supplied sentences verbatim and still prohibits broader confirmation.

The Editorial Planner, realization gate, date normalization, tone profile, authority precedence, and approval/execution checks were not rewritten or weakened. The successful generation, event 17168, used the accepted architecture and model `gpt-5.6-sol`. All three mandatory facts passed realization on its first candidate; no corrective retry was needed. There were two generation requests overall: one rejected before the integration correction and one accepted afterward.

Final DraftRevision **387**:

> **Studio seating update**
>
> Hi there,
>
> Thanks for clarifying that you would prefer theatre-style seating for 24 guests.
>
> The Studio is available for 12 November 2026 from 14:00 to 18:00 (Europe/Amsterdam). The requested projection setup is feasible for 12 November 2026 from 14:00 to 18:00 (Europe/Amsterdam). The requested seated layout for 24 guests in the Studio is feasible for 12 November 2026 from 14:00 to 18:00 (Europe/Amsterdam).

Recipient: **serinya@whennaturecalls.nl**, the configured staging mailbox. This is part of the same synthetic case journey. No real client is involved, and no booking or commercial commitment is made. The normal exact approval API approved **466** under the user's explicit pre-authorization. Subject, body, recipient, content hash, revision context, canonical action contract, and approval remained unchanged through closure.

## One final send and evidence-based reconciliation

Action 1640 passed hosted readiness checks for canonical payload, exact revision, current case/context, recipient allowlist, and exact approval. It was invoked once at **11:00:23.875567 UTC**. Attempt 29 reached `verify_sent_message`; the immediate HTTP 200 result was inconclusive. No retry was performed, and the send gate was disabled.

The later bounded receipt verifier made **two Graph GET requests and zero Graph mutations**, with all execution gates closed. It checked the exact approved lineage, sole recipient, subject, body, sent state, Internet message ID, conversation identity, and receipt after the attempt began. It found:

- Sent at **11:00:26 UTC**, sent message suffix `oZ8bdgAA`.
- Received at **11:00:28 UTC**, Inbox message suffix `oZ8bfAAA`.
- Exact approved content and recipient in both copies.
- Identical Internet message ID in both copies.

Full provider identifiers: [provider_receipt.json](provider_receipt.json). The final outbound message uses the certified new-message send mode and therefore has its own provider conversation; the three inbound client messages remain in their single original conversation.

The existing reconciliation API recorded event **17175** using explicit synthetic operator receipt evidence. Repeating the same confirmation returned 17175 with `Already reconciled: True`, zero provider calls, and zero new attempts. Action 1640 is now succeeded and revision 387 is `human_confirmed_delivered`. Attempt 29 remains byte-for-byte equal to its original persisted ambiguous record.

The provider-free execution preflight now returns `action_already_succeeded`; the adapter's original ambiguity retry guard also remains active. No second final execution invocation was made.

Send accounting for this continuation: **one synthetic client-input fixture send plus one final client-response send**. The final response had exactly **one Graph send and one execution attempt**. Reconciliation never resent either message.

## Gates, deployment, tests, and isolation

Final verified state:

```
STAGING_ALLOW_REAL_OUTLOOK_INBOUND=false
STAGING_ALLOW_OUTLOOK_INBOUND_PREFLIGHT=false
STAGING_ALLOW_REAL_OUTLOOK_SEND=false
STAGING_ALLOW_REAL_ASANA=false
```

Health reports Outlook `configured_draft_only`, Asana `configured_but_disabled`, inbound disabled, preflight disabled, and healthy staging database/retrieval layers. See [health_final.json](health_final.json).

Runtime: `5d7ea19ba7f3516318974f28ad9add590f921d26`, Render staging deploy `dep-db4ck4btqb8s73erb1c0`. Earlier bounded runtime fixes were `a2c69b9` (synthetic transport/capacity bindings), `808001b` (canonical Asana scope), and `3b19037` (provider instruction alignment). The additive authority migration was applied only to staging project `mspcopnsbounmdpivkvq`.

Validation passed:

- **24 focused closure tests**, including incorrect recipient/content/message identity, duplicate or old receipts, production/open-send-gate rejection, and stale capacity inputs.
- **708 Phase 8 tests**.
- **925 full repository tests**.
- `git diff --check`.
- Live inbound deduplication, capacity event replay, Asana provider observation/replay, exact approval/readiness, sent/Inbox correlation, reconciliation replay, and final closure audit.

Tests ran against the pinned local WNC PostgreSQL environment with external HTTP forbidden. Existing warning counts were 26 for Phase 8 and 41 repository-wide. Local verification scripts were corrected where their assertions compared changing Asana projection content rather than stable IDs, or confused the revision-context hash with the governed-context hash; no provider action was repeated as a result. A reconciliation request with numeric JSON identifiers was rejected before mutation; the normal API's string identifier form was then accepted. No failed service request retried a provider send.

Protected cases **424, 584, and 585** compare unchanged against their prior row snapshots. Original case 586 evidence and prior facts also compare unchanged. No production access/change, real customer communication, payment, contract, booking, fee waiver, policy exception, destructive migration, tenant permission expansion, or secret disclosure occurred. No generated prose was promoted to truth.

The complete immutable event timeline follows. Raw audit evidence is in [timeline_events.json](timeline_events.json) and final assertions in [result.json](result.json).

## Complete persisted timeline (UTC)

| Event | Recorded UTC | Event type | Source / evidence reference |
|---|---|---|---|
| 17111 | 2026-10-09T09:17:54.581181+00:00 | test_console_case_registered | test_console:create_case |
| 17112 | 2026-10-09T09:17:53.891342+00:00 | inbound_observation_recorded | inbound_source_record:3104 |
| 17113 | 2026-10-09T09:12:12+00:00 | outlook_inbound_evidence_recorded | inbound_source_record:3104 |
| 17114 | 2026-10-09T09:17:53.891342+00:00 | inquiry_open_question_created | inquiry_intake:requested_schedule |
| 17115 | 2026-10-09T09:17:53.891342+00:00 | inquiry_open_question_created | inquiry_intake:guest_count |
| 17116 | 2026-10-09T09:17:53.891342+00:00 | inquiry_open_question_created | inquiry_intake:requested_space |
| 17117 | 2026-10-09T09:17:53.891342+00:00 | inquiry_open_question_created | inquiry_intake:event_type |
| 17118 | 2026-10-09T09:23:17.425071+00:00 | inbound_observation_recorded | inbound_source_record:3105 |
| 17119 | 2026-10-09T09:21:38+00:00 | outlook_inbound_evidence_recorded | inbound_source_record:3105 |
| 17120 | 2026-10-09T09:27:31.44327+00:00 | inbound_observation_recorded | inbound_source_record:3105 |
| 17121 | 2026-10-09T09:27:31.44327+00:00 | case_fact_promoted_from_observation | inbound_observation:2723 |
| 17122 | 2026-10-09T09:27:31.44327+00:00 | inquiry_open_question_resolved | inbound_observation:2723 |
| 17123 | 2026-10-09T09:44:58.628789+00:00 | inbound_observation_recorded | inbound_source_record:3104 |
| 17124 | 2026-10-09T09:44:58.628789+00:00 | inbound_observation_recorded | inbound_source_record:3104 |
| 17125 | 2026-10-09T09:44:58.628789+00:00 | inbound_observation_recorded | inbound_source_record:3104 |
| 17126 | 2026-10-09T09:44:58.628789+00:00 | inbound_observation_recorded | inbound_source_record:3104 |
| 17127 | 2026-10-09T09:44:58.628789+00:00 | inbound_observation_recorded | inbound_source_record:3104 |
| 17128 | 2026-10-09T09:44:58.628789+00:00 | case_fact_promoted_from_observation | inbound_observation:2724 |
| 17129 | 2026-10-09T09:44:58.628789+00:00 | inquiry_open_question_resolved | inbound_observation:2724 |
| 17130 | 2026-10-09T09:44:58.628789+00:00 | case_fact_promoted_from_observation | inbound_observation:2725 |
| 17131 | 2026-10-09T09:44:58.628789+00:00 | inquiry_open_question_resolved | inbound_observation:2725 |
| 17132 | 2026-10-09T09:44:58.628789+00:00 | case_fact_promoted_from_observation | inbound_observation:2726 |
| 17133 | 2026-10-09T09:44:58.628789+00:00 | inquiry_open_question_resolved | inbound_observation:2726 |
| 17134 | 2026-10-09T09:46:05.038014+00:00 | orchestration_blocker_created | RULE_AUTHORITY_GAP_BLOCK |
| 17135 | 2026-10-09T09:46:05.038014+00:00 | orchestration_blocker_created | RULE_CONFIRMATION_REQUIRED_BLOCK |
| 17136 | 2026-10-09T09:46:05.038014+00:00 | workflow_action_created | RULE_AUTHORITY_GAP_BLOCK |
| 17137 | 2026-10-09T09:46:05.038014+00:00 | workflow_action_created | RULE_CONFIRMATION_REQUIRED_BLOCK |
| 17138 | 2026-10-09T10:13:01.066878+00:00 | workflow_action_execution_started | workflow_action:1635 |
| 17139 | 2026-10-09T10:13:08.563116+00:00 | workflow_action_execution_completed | workflow_action:1635 |
| 17140 | 2026-10-09T10:13:08.563116+00:00 | workflow_action_superseded | context_aware_resolution:586:blocker:2384:REQUIRED:revision:3 |
| 17141 | 2026-10-09T10:13:08.563116+00:00 | workflow_action_superseded | context_aware_resolution:586:blocker:2385:REQUIRED:revision:3 |
| 17142 | 2026-10-09T10:13:08.563116+00:00 | workflow_action_superseded | context_aware_resolution:586:availability:2026-11-12 13:00:00+00:2026-11-12 17:00:00+00:REQUIRED:revision:3 |
| 17143 | 2026-10-09T10:13:24.675463+00:00 | asana_projection_observed | workflow_action:1635 |
| 17144 | 2026-10-09T10:19:19.738734+00:00 | operational_resolution_accepted | staging:case586:authorized-synthetic-operator:1634:v1 |
| 17145 | 2026-10-09T10:19:21.509219+00:00 | operational_resolution_accepted | staging:case586:authorized-synthetic-operator:1633:v1 |
| 17146 | 2026-10-09T10:19:55.300578+00:00 | orchestration_blocker_created | RULE_AUTHORITY_GAP_BLOCK |
| 17147 | 2026-10-09T10:19:55.300578+00:00 | workflow_action_created | RULE_AUTHORITY_GAP_BLOCK |
| 17148 | 2026-10-09T10:19:55.300578+00:00 | blocker_resolved | blocker:authority:missing:test-console-projection:e347093c59688a0b3579c6ca0374e73d74517fa5b1172a999c09fd37bd961634 |
| 17149 | 2026-10-09T10:19:55.300578+00:00 | blocker_resolved | blocker:authority:confirmation:test-console-projection:208387bd2d10d8e947b97d53adaf47e3d1bc2056e15b626194d1ea9567330732 |
| 17150 | 2026-10-09T10:19:55.300578+00:00 | workflow_action_superseded | action:CREATE_INTERNAL_TASK_ITEM:722cff81d7554a1502386a1f1a896b92f8ccc98c952aeac47592cbc242850cd1:3 |
| 17151 | 2026-10-09T10:19:55.300578+00:00 | workflow_action_superseded | action:CREATE_INTERNAL_TASK_ITEM:72594a38dbffd970c62b7a35f5f4bd469a674bbbb136a5dd3dea276246241341:3 |
| 17152 | 2026-10-09T10:20:10.508678+00:00 | workflow_action_execution_started | workflow_action:1637 |
| 17153 | 2026-10-09T10:20:15.470932+00:00 | workflow_action_execution_completed | workflow_action:1637 |
| 17154 | 2026-10-09T10:20:38.266642+00:00 | asana_projection_observed | workflow_action:1637 |
| 17155 | 2026-10-09T10:48:45.068044+00:00 | synthetic_client_transport_started | inbound_source_record:3105 |
| 17156 | 2026-10-09T10:48:46.665696+00:00 | synthetic_client_transport_accepted | outlook_message:AAkALgAAAAAAHYQDEapmEc2byACqAC-EWg0ArpH-EFDur06E-zl8MvU_HgABoZ8bawAA |
| 17157 | 2026-10-09T10:48:48+00:00 | outlook_inbound_evidence_recorded | inbound_source_record:3106 |
| 17158 | 2026-10-09T10:49:11.988912+00:00 | inbound_observation_recorded | inbound_source_record:3106 |
| 17159 | 2026-10-09T10:49:12.184519+00:00 | rental_case_fact_mutated | inbound_observation:2729 |
| 17160 | 2026-10-09T10:49:19.90104+00:00 | operational_resolution_accepted | synthetic:case586:operator:seated24:practical-check:v1 |
| 17161 | 2026-10-09T10:49:43.972597+00:00 | blocker_resolved | blocker:authority:missing:test-console-projection:cd988b2a35456f04a32158b687bce79596b49e2b7f820efed279255131a0b399 |
| 17162 | 2026-10-09T10:49:43.972597+00:00 | workflow_action_superseded | action:CREATE_INTERNAL_TASK_ITEM:c56c4418910e6c4228a9fc49350c32a04f271f7b01fdfe9fedd88bff2c500931:5 |
| 17163 | 2026-10-09T10:53:02.394579+00:00 | workflow_action_execution_started | workflow_action:1639 |
| 17164 | 2026-10-09T10:53:06.775001+00:00 | workflow_action_execution_completed | workflow_action:1639 |
| 17165 | 2026-10-09T10:53:06.775001+00:00 | workflow_action_superseded | asana_rental_projection_v1:586:f34426eb2772ed782cb4549d214a701ea182708439bd7cfa694f84457b0f7a9f |
| 17166 | 2026-10-09T10:53:17.597194+00:00 | asana_projection_observed | workflow_action:1639 |
| 17167 | 2026-10-09T10:53:29.998179+00:00 | governed_client_response_draft_rejected | governed_client_response_rejected:510e8d0f7ba66a4c0eff05570be10fa1deac98e2185ec97ba289d2b5df4b93ff |
| 17168 | 2026-10-09T10:57:28.832713+00:00 | governed_client_response_draft_generated | inquiry_response_draft:387 |
| 17169 | 2026-10-09T10:58:51.792518+00:00 | approval_decided | approval:466 |
| 17170 | 2026-10-09T10:58:51.792518+00:00 | workflow_action_status_changed | workflow_action:1640 |
| 17171 | 2026-10-09T10:58:51.792518+00:00 | workflow_action_status_changed | workflow_action:1640 |
| 17172 | 2026-10-09T10:58:52.083909+00:00 | inquiry_response_draft_approved | inquiry_response_draft:387 |
| 17173 | 2026-10-09T11:00:23.875567+00:00 | workflow_action_execution_started | workflow_action:1640 |
| 17174 | 2026-10-09T11:00:26.98376+00:00 | workflow_action_execution_completed | workflow_action:1640 |
| 17175 | 2026-10-09T11:05:19.615902+00:00 | outlook_delivery_human_confirmed | execution_attempt:29 |

Event 17144 retains an earlier evidence occurrence time than its acceptance; both timestamps remain in the raw timeline. Inbound occurrence timestamps similarly preserve provider receipt times.

**Stop condition met. No production-pilot work has begun.**
