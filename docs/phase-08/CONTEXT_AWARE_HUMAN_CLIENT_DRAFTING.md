# Context-Aware Human Client Drafting

## Scope

This Phase 8 remediation improves client-draft context without changing who controls operational truth. The drafting provider may interpret and phrase the bounded contract. The application derives resolution ownership, creates governed internal actions, selects current factual guidance, validates output, and controls approval and execution.

Outlook and Microsoft Graph remain disabled in staging. Asana remains behind the existing allowlisted `task_surface` WorkflowAction execution path and is never called while generating a draft.

## Existing Architecture Used

- `OpenQuestion` remains the canonical client-owned missing-information record.
- `Blocker`, `Requirement`, Phase 7 reasoning projections, and `CaseDecision` remain canonical governed state.
- `WorkflowAction` remains the canonical idempotent work-routing record.
- `inquiry_response_draft_revisions.context_payload` persists immutable drafting context, including annotations and guidance provenance.
- Phase 5 hybrid retrieval supplies factual guidance. Phase 6 historical precedent is not accepted as client-facing factual guidance.
- Exact-revision approval and stale-draft invalidation remain unchanged.

## Resolution Semantics

The deterministic `context_aware_drafting` adapter derives a resolution item for each relevant persisted proposition:

- `CLIENT`: a fact only the client can provide. Its visibility is `ASK_CLIENT` and it becomes an open-client question in the DraftContract.
- `WNC_INTERNAL`: WNC can establish the answer. Its visibility is `INTERNAL_ONLY`; the client draft does not say WNC is awaiting confirmation.
- `EXTERNAL_PARTY`: a facilitator, supplier, or similar outside party is needed. `CONTACT_REQUIRED` never permits client prose claiming contact. Only the explicit `external_resolution_contacted` workflow event moves it to `CONTACTED_AWAITING_RESPONSE` and allows visible pending-contact language.
- `GOVERNED_DECISION`: a commercial or policy exception still requires the existing exact-state decision process. Its visibility is `DECISION_PENDING_VISIBLE`.

For unresolved WNC-internal and external-contact work, Phase 8 creates or reuses an idempotent `CREATE_INTERNAL_TASK_ITEM` action. The structured payload contains the resolution-item key, owner, status, task kind, and concise operational summary. Draft generation itself performs no provider execution.

## Operator Annotations

Each unresolved internal-only item creates a structured operator annotation in the immutable draft context:

```json
{
  "type": "INTERNAL_CONFIRMATION",
  "message": "Confirm Studio availability",
  "proposition_key": "blocker:42",
  "workflow_action_id": 123,
  "blocking": true
}
```

Annotations are shown separately in the Test Console and are never supplied as client prose to the model. A current draft with a blocking annotation cannot be approved or executed. Once the governed item resolves, ordinary case-state freshness invalidates the old revision; a new revision has a fresh context and no resolved annotation.

## Contextual Guidance And Style

Topic detection is deterministic and uses structured facts plus the latest client message. Supported topics include catering/kitchen, external supplier setup, technical capability, facilitator process, and capacity.

`Phase5HybridGuidanceSearch` uses the existing Phase 5 hybrid query in FTS-only mode. It retrieves a small set per topic and accepts only current `authoritative` or `guidance` chunks from the explicit client-safe factual document set. Template-library material (`TPL-006`) is excluded from factual guidance. Guidance is persisted with topic and provenance in the draft context, and is passed to the model as allowed contextual guidance.

The style profile is separate from factual retrieval. It is a stable WNC voice profile for warmth, greetings, acknowledgment, practical next steps, and complete signoff. It cannot introduce commercial facts, historical concessions, or client-specific precedent. A future approved style-example corpus can be added through a separate style-only retriever; none is treated as factual authority in this slice.

## Validation

Existing stale-context, question-set, availability, commercial, known-no, and pending-decision checks remain in place. Added checks are:

- `em_dash_not_allowed`: client subject and body cannot contain `—`.
- `dangling_signoff`: a terminal `Best,`, `Best regards,`, `Kind regards,`, or `Warm regards,` without a sender is rejected.
- `external_contact_not_recorded`: client claims such as “we've reached out” or “we're waiting to hear back” are rejected while any external resolution remains `CONTACT_REQUIRED`.
- blocking operator annotations prevent exact-revision approval and execution.

The persisted signoff continues to be `WNC Rentals`; generated client copy must include a complete sender and never use `WNC Rental Brain` as a client-facing identity.

## Retrieval Boundaries

Phase 5 contextual guidance is client-safe supporting information, not a decision engine. Phase 4 deterministic truth and Phase 7 authority/confidentiality rules continue to decide what is known, restricted, or unresolved. Historical Phase 6 material and template examples cannot enter factual allowed assertions.
