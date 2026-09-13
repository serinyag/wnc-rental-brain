# Canonical Outlook Execution Contract Audit

Date: 2026-09-13. Scope: Phase 8 application construction, persistence, projection,
approval, execution, retry lineage, final send governance, and deterministic fixtures.
No Graph, OpenAI, Outlook send, Asana, or production operations were used.

## Canonical contract

`outlook_action_contract.py` defines `OutlookActionIntent`, `OutlookExecutionInput`,
`reserve_governed_outlook_action`, `build_governed_outlook_action`, and
`validate_outlook_action`. Every supported executable Outlook action is bound by
this builder. Domain action: `SEND_INQUIRY_RESPONSE`; adapter: `outlook`; provider:
`microsoft_graph_outlook`; category: `communication`; posture: `approval_required`.

Required persisted payload keys (all keys are required, including explicitly nullable keys):

`contract_version`, `action_type`, `provider_type`, `rental_case_id`, `source_case_revision`, `response_intent`, `purpose`, `reason`, `conversation_key`, `draft_revision_id`, `draft_origin_workflow_action_id`, `draft_content_hash`, `context_hash`, `governed_context_hash`, `recipient_email`, `recipient_identity_hash`, `recipient_reference`, `subject`, `body`, `body_type`, `message_mode`, `graph_message_id`, `approval_target`, `provenance`, `plan_identity`, `recovery_draft_revision_id`, `recovery_origin_workflow_action_id`, `recovery_predecessor_action_id`.

`graph_message_id` is null only for a newly created provider draft. Existing-draft
mode requires one nonempty immutable Graph ID from local audit evidence. Recovery
revision/origin/predecessor keys are explicitly null when inapplicable. Recovery
revision and origin must match the bound draft, and its action must supersede that
origin. The current adapter supports one To recipient, text content, no CC/BCC,
attachments, or reply reference; unknown input keys fail instead of being dropped.

The action envelope additionally supplies its allocated ID/UUID, case ID and
revision, action code/category/adapter, approval posture, reason entity and
conversation reference, semantic governed-context hash, idempotency key, lineage,
and timestamps. No lifecycle status participates in identity. All immutable input
fields participate in execution idempotency except the separately checked allocated
approval target. Different revisions, content, recipients, and retry predecessors
therefore have different identities even within one case revision/context.

Subject/body and `draft_content_hash` are compared with the exact persisted
DraftRevision. `context_hash` is the immutable draft-context hash;
`governed_context_hash` is the separately rebuilt case-truth hash. Recipient email
and normalized recipient identity hash are both checked. Approval must target
`workflow_action:{action_id}:draft_revision:{revision_id}` with matching entity
ID/type; an old approval cannot authorize another action or revision.

Operator annotations are read from the persisted revision. A missing/malformed
annotation list fails closed; blocking annotations prevent approval/send. Current
case/context, current revision, recipient allowlist, and durable Graph evidence are
re-read. Approval granted and live send enabled remain separate gates. Provider
credentials/mailbox are deployment configuration, not copied into actions. External
references are execution outputs, not caller-supplied draft identities. Workflow
subtype is represented by action code and response intent; no additional hidden
subtype field is consumed.

## Reservation and immutable persistence

The existing DraftRevision foreign key requires an action ID before the draft can
be saved. A typed intent first creates a `governed_outlook_reservation_v1` action
without an approval. It fails the execution schema and cannot execute. After the
revision exists, the sole builder creates `governed_outlook_v1`; the repository
binds it once, only while awaiting approval and without any approval or attempt
history. Direct insertion of a full action is rejected because insertion allocates
an ID; full inputs must use the bind operation to retain their exact approval target.

The new partial unique index on case plus `plan_identity` retains construction
idempotency after binding changes the execution key. A stale construction snapshot
cannot insert a second reservation. Repeated generation of an already-bound exact
identity returns its existing revision and preserves approval/lifecycle state.
Historical rows have no reservation marker and are never backfilled or rebound.

## Action creation paths audited

C = the complete canonical payload above. P = non-executable reservation plan.

| Path | File / function | Purpose | Before / defect | After / builder | Payload | Idempotency | Revision binding | Approval binding | Graph binding |
|---|---|---|---|---|---|---|---|---|---|
| Governed generation | `test_console_service.generate_governed_client_response_draft`, `_ensure_governed_client_response_action` | Model-generated reply | Seven-field domain dictionary; transport data arrived later | P → persisted revision → `build_governed_outlook_action` | C | Plan identity, then immutable execution identity; replay reuses revision | Exact ID and both hashes | Exact action/revision | New mode, null ID until provider creates draft |
| Human Outlook edit | `_apply_outlook_reconciliation` | Reconcile trusted human-edited content | Reused partial generation payload; provenance/Graph identity split across layers | Same builder, `outlook_human_edit` provenance | C | New content and origin distinguish successor | Exact successor revision; origin re-read after provider boundary | Fresh exact approval | Trusted plan ID, matching synthetic/read snapshot, durable event |
| Failed-action recovery | `prepare_governed_outlook_send_recovery` | Retry exact current failed draft | Missing intent/purpose/reason and recipient hash; old fixed recovery key | Same builder, intent copied from origin and checked against current contract | C | Versioned plan plus predecessor; old 587 cannot collide | Exact existing revision retained | New exact open approval; historical approval preserved | Resolved from local audit; same immutable ID |
| Further recovery/retry | Same recovery method | Replace a later terminal recovery | No explicit subsequent predecessor identity | Same builder; terminal predecessor recorded; active canonical lineage reused | C | Stable per predecessor; new predecessor changes key | Original revision and origin retained | New action requires new approval | Same audit-bound ID; unknown send outcomes rejected |
| Deterministic staging draft | `generate_governed_client_response_draft(use_deterministic_fixture=True)` | Substitute model only | Inherited partial normal payload | Same generation and binding path; explicit fixture provenance | C | Same semantic rules | Same exact binding | Same exact approval | Same mode rules |
| Regeneration / rescheduled case | Governed generation after current-case rebuild | Rebuild communication from current truth | Current context/content could share status-filtered or content-only assumptions | Same builder; changed case/context/content gets new identity | C | Case revision, context and content distinguish | New exact revision | Fresh exact approval | New mode unless reconciled to existing draft |
| Generic inquiry clone/edit | `_ensure_draft_target_action`, `generate_inquiry_response_draft`, `edit_inquiry_response_draft` | Legacy local inquiry drafting | Generic clone could copy an incomplete Outlook payload | Governed Outlook cloning is rejected; operator uses governed generation/reconciliation | Legacy email fixture only; never an Outlook executable | Existing legacy rules for fake-only actions | Legacy local drafts | Cannot authorize real Outlook execution | No real mapping |
| Generic orchestration / Phase 7 derived communication | `orchestration_runtime.apply_orchestration_plan`, repository `create_workflow_action` | Domain task/email actions | Arbitrary dictionary and generic real-email mapping could bypass projection | Outlook insertion requires factory reservation; real email mapping requires canonical Outlook contract and send validator | C for Outlook; other domain schemas remain fake/local | Canonical Outlook rules | Canonical required before real mapping | Canonical required | No arbitrary raw-email send route |
| Test-console real mapping | `_build_execution_registry` | Choose a provider | Legacy `email` could map to Outlook without exact governed projection | Only canonical governed Outlook input can reach real Outlook adapter | C | Preserved | Preserved | Required | Preserved |
| Test-console fake success | `_build_execution_registry`, `outlook_simulation.DeterministicOutlookTransport` | Full provider-free simulation | Default fake registry did not register `outlook` and bypassed transport governance | Same Outlook adapter/parser/send validator over synthetic transport | C | Preserved, replay checked | Preserved | Required | Synthetic snapshot; no network; fake result/reference marked explicitly |
| SQL migration / enum fixtures | Migration `20260907000100`, test `44_...`; legacy SQL tests 34/38/39/40/43 | Test persistence/domain enums | Raw minimal rows were schema probes, not executable-contract fixtures | Remain historical/negative storage probes; Python execution rejects their incomplete payloads | Deliberately not C; not a supported executable construction path | SQL fixture identities only | None | Cannot pass execution | None |
| Repository persistence / races | `orchestration_repository.create_workflow_action`, `bind_outlook_action` | Persist generated actions | Accepted arbitrary partial Outlook dictionaries | Factory validation plus guarded one-time binding; plan identity unique index | P then C | Unique construction plan survives final key assignment | Builder binds persisted revision | Binding forbidden once approval exists | Included in immutable contract |

The legacy generic editor is intentionally not an alternate executable Outlook
builder: it cannot provide trustworthy Graph reconciliation evidence. It now directs
operators to the governed generation/reconciliation paths instead of copying a
partial dictionary. Legacy `REQUEST_CLIENT_INFORMATION` fake workflows remain
available under their existing domain contract.

## Projection and execution audit

The previous transport dictionary retained body/subject but dropped
`response_intent`, `purpose`, `reason`, recipient identity hash and other action
identity fields. An earlier patch restored `conversation_key` only. Projection now
parses the typed canonical input, checks it against the exact revision and local
Graph evidence, and copies the complete schema without selecting a subset of keys.

The generic execution validator uses the same `OutlookExecutionInput` schema. The
runtime checks the action envelope and exact approved target before creating an
attempt. A missing field never receives a recovery default. Historical malformed
inputs still return `invalid_execution_input` with no attempt or provider work.

Final send governance now runs before provider work for both new and existing
drafts. Both modes also receive the final draft-integrity check immediately before
send. Persisted action identity, exact revision/content/context, exact approval,
recipient allowlist, annotation state and Graph evidence remain checked. The live
send switch is still evaluated at the transport boundary. Retry history is scoped
to the executing action, so another action's attempt cannot supply a Graph ID.
The provider's legacy `email` result code is normalized to the action's `outlook`
code before completion persistence; successful external-reference uniqueness remains.

The Graph binding resolver accepts the two durable audit event forms (original
reconciliation and human-edit revision creation), requires exactly one ID, and
never consumes a message ID from operator request input. Human reconciliation
rejects a mismatched snapshot ID and re-reads its originating revision after the
provider boundary. Unknown/ambiguous send outcomes cannot create a recovery.

## Historical malformed actions

Provider-free staging inspection, before any remediation writes:

- **582**: `failed`, 1 attempt(s). Missing: `action_type`, `approval_target`, `body`, `body_type`, `contract_version`, `conversation_key`, `draft_content_hash`, `draft_origin_workflow_action_id`, `draft_revision_id`, `governed_context_hash`, `graph_message_id`, `message_mode`, `plan_identity`, `provenance`, `provider_type`, `recipient_email`, `recipient_identity_hash`, `recipient_reference`, `recovery_draft_revision_id`, `recovery_origin_workflow_action_id`, `recovery_predecessor_action_id`, `rental_case_id`, `source_case_revision`, `subject`.
- **586**: `failed`, 1 attempt(s). Missing: `action_type`, `approval_target`, `body`, `body_type`, `contract_version`, `draft_origin_workflow_action_id`, `draft_revision_id`, `governed_context_hash`, `graph_message_id`, `message_mode`, `plan_identity`, `provenance`, `provider_type`, `recipient_email`, `recipient_reference`, `recovery_draft_revision_id`, `recovery_origin_workflow_action_id`, `recovery_predecessor_action_id`, `rental_case_id`, `source_case_revision`, `subject`.
- **587**: `ready_to_execute`, 0 attempt(s). Missing: `action_type`, `approval_target`, `body`, `body_type`, `contract_version`, `draft_origin_workflow_action_id`, `draft_revision_id`, `graph_message_id`, `message_mode`, `plan_identity`, `provenance`, `provider_type`, `purpose`, `reason`, `recipient_identity_hash`, `recipient_reference`, `recovery_predecessor_action_id`, `rental_case_id`, `response_intent`, `source_case_revision`, `subject`.

Actions 582/586 store the governed case hash under `context_hash`; the new contract
keeps that separate from DraftRevision's immutable context hash. Action 587 retains
its exact historical recovery binding but is malformed and must not execute. Its
missing intent/purpose/reason are not patched or guessed. Origin 586 supplies
`REQUEST_CLIENT_INFORMATION`, `governed_client_response_draft`, and
`operator_requested_governed_client_response` for the new recovery, and the current
case contract agrees. DraftRevision 144, historical approvals 184/185, all three
historical actions, and their existing attempts are preserved and hash-compared.

## Provider-free validation

- Normal, human-edit successor, and recovery lifecycles each create an exact
  approval, approve only in memory, reach ready-to-execute, create an attempt, pass
  the real send validator and a matching synthetic Outlook snapshot, complete fake
  send successfully, persist success, and reject replay.
- Actual application generation and deterministic fixture generation produce the
  same schema. Actual reconciliation persistence creates the canonical successor
  and preserves the audit-bound Graph ID.
- Negative coverage includes every required missing/null input; missing intent,
  purpose, reason, conversation, draft ID, Graph ID, content/context hash, recipient
  hash; wrong revision, stale context, old/wrong approval, changed recipient/body,
  blocking annotations, historical failed action reuse, duplicate replay, disabled
  send gate, changed Outlook snapshot, and unrelated historical retry attempts.
- Contract defects fail before attempts; late truth defects fail governance before
  transport; snapshot drift/send-disabled outcomes cannot call fake send.
- PostgreSQL round trip (local Docker, rolled back) validates persistence, guarded
  binding, stale construction replay, and the unique construction-plan index.

Final test run: **343 passed, 126 subtests passed**, no failures or skips. All 23
warnings are pytest collection warnings for imported application classes with
constructors. `git diff --check` passes. The staging preview uses read-only database
transactions with HTTP provider calls patched to fail; it confirms canonical
payload/binding, matching current intent/context, allowlisted recipient, no blocking
annotations, and zero row writes.

## Fresh recovery and deployment evidence

Fresh lineage and hosted certification are recorded below after preparation.
The saved Render send switch was found enabled from the prior authorized attempt;
it was changed to `false` for this deployment. Asana remains disabled. No approval
or external action execution is authorized by this audit or its readiness endpoint.

Staging migration `20260913000100` was applied and registered. Fresh WorkflowAction
**588** binds DraftRevision **144**, origin action **586**, predecessor **587**, and
new ApprovalRequest **186**. Action status is `awaiting_approval`; approval status is
`open`; no execution attempt was created. The provider-free readiness endpoint
implementation, run against staging data, reports:

- Canonical payload validation: **PASS**
- Execution-input validation: **PASS**
- Pre-send governance input validation: **PASS**
- Exact revision, current case/context and recipient allowlist: **PASS**
- Exact approval required: **yes**
- Send gate: **disabled** (saved staging configuration)
- Graph operations / Outlook send performed: **0 / no**

Before/after full-row hashes match for all eight preserved historical records:
actions 582/586/587, approvals 184/185, revision 144, and the two prior attempts.
No historical artifact was edited. The deployment and live hosted endpoint are
verified separately in the task's final report after this commit is deployed.

Focused suite totals: canonical contract 13, database binding 1, execution runtime
14, orchestration/approval runtime 16, Outlook adapter 19, provider safety 4, and
test-console/reconciliation/recovery 59: **126 focused tests** within the complete
**343-test Phase 8 suite**, plus **126 subtests**. Local database changes rolled back.
