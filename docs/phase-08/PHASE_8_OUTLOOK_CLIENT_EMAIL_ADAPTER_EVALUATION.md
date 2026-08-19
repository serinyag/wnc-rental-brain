# Phase 8.7B Outlook Client Email Adapter Evaluation

Date:

- August 13, 2026

Pre-phase readiness marker:

- `READY_FOR_PHASE_8_CLIENT_FACING_ADAPTER_ROLLOUT`

## Outcome

Phase 8.7B completed successfully within the requested boundary:

- Outlook implemented through the existing Phase 8.6 adapter boundary
- outbound new-message execution only
- reply execution deferred safely
- no DB migration required
- no inbound Outlook behavior introduced

## Verification Summary

Focused Outlook Python:

- `10 / 10 PASS`

Focused DB:

- not applicable
- no schema change was required for 8.7B

Phase 8:

- `108 / 108 PASS`

Phase 7:

- `127 / 127 PASS`

Phase 5:

- `24 / 24 PASS`

Phase 6:

- `6 / 6 PASS`

Supabase:

- `41 files / 1059 tests PASS`

Corpus reset:

- not performed

Corpus counts re-verified after this phase:

- Phase 5 current chunk sets: `22`
- Phase 5 chunks in current chunk sets: `525`
- Phase 5 searchable current chunk sets: `21`
- Phase 5 searchable current chunks: `492`
- Phase 6 historical embeddings: `112`

## Microsoft Graph Strategy Selected

API pattern chosen:

- OAuth client credentials token
- `POST /users/{mailbox}/messages`
- `POST /users/{mailbox}/messages/{id}/send`
- bounded `GET /users/{mailbox}/messages/{id}`

Why this path was chosen:

- direct `sendMail` does not preserve provider identity early enough for safe duplicate prevention
- draft-first allows one semantic action to bind to one provider message identity
- immutable IDs allow stable correlation across draft/send state changes

Auth mode:

- application permissions

Mailbox model:

- one explicit configured sender mailbox

Reply behavior:

- not implemented in this phase
- exact governed source-message identity was not proven available end-to-end

## Verification Semantics

`succeeded` means:

- the exact provider draft identity was sent
- the same immutable message identity was read back once
- `isDraft = false`
- `sentDateTime` was present

`succeeded` does not mean:

- delivered to recipient inbox
- opened by recipient
- replied to by recipient

## Safety Metrics

- real providers implemented = `2`
- Asana = `1`
- Outlook = `1`
- Google Calendar calls = `0`
- Mollie calls = `0`
- direct n8n execution dependency = `0`
- LLM-selected provider execution = `0`
- LLM direct Outlook calls = `0`
- execution-time LLM content generation = `0`
- pre-approval Outlook sends = `0`
- blocked Outlook sends = `0`
- stale Outlook sends = `0`
- superseded Outlook sends = `0`
- cancelled Outlook sends = `0`
- recipient inferred by adapter = `0`
- duplicate semantic client sends after verified success = `0`
- duplicate semantic client sends from concurrent workers = `0`
- blind resend after ambiguous outcome = `0`
- provider failure counted as success = `0`
- timeout counted as verified success = `0`
- ambiguous send counted as verified success = `0`
- malformed provider result counted as success = `0`
- successful Outlook execution without ExecutionAttempt = `0`
- Outlook send directly mutating lifecycle = `0`
- Outlook send directly activating CaseDecision = `0`
- Outlook send directly accepting ProposedCaseChange = `0`
- Outlook send directly resolving Blocker = `0`
- Outlook send directly satisfying Requirement without governed rule = `0`
- historical precedent promoted through Outlook execution = `0`
- cross-case message reference mutation = `0`
- credentials persisted in DB/audit = `0`
- credentials written to logs = `0`
- follow-up due directly invoking Outlook = `0`

## Acceptance Criteria Check

Satisfied:

- Outlook uses the Phase 8.6 adapter boundary
- no direct agent Outlook path exists
- recipient is explicit and validated
- sender mailbox is explicit and configured
- message mapping is deterministic
- provider identity is persisted on `ExecutionAttempt.external_reference`
- retries reuse the same provider identity when safe
- ambiguous sends are not blindly resent
- approval/stale/superseded/cancelled protections remain intact
- Outlook execution does not mutate workflow truth directly
- every real provider invocation has an `ExecutionAttempt`
- failed and ambiguous results do not count as success
- no inbound Outlook runtime was introduced
- no calendar or payment adapter was introduced

Intentionally deferred:

- reply execution
- reply-all
- attachments
- canonical recipient-authority model beyond explicit structured payload
- reconciliation worker for ambiguous outcomes

## Live Smoke Test

Live Outlook smoke test:

- `NOT PERFORMED`

Reason:

- safe test credentials, safe test mailbox, and explicit non-production recipient were not configured locally

## Final Evaluation

Phase 8.7B proves that governed client-facing outbound email can be executed safely through the existing Phase 8 runtime without collapsing the boundary between reasoning and reality.

The repository is now ready to stop adding low-level transport infrastructure and begin assembling the first governed end-to-end rental inquiry workflow.
