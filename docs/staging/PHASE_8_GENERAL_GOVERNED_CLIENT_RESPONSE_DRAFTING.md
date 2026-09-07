# Phase 8 General Governed Client Response Drafting

## Scope

This slice adds a bounded client-response drafting path on top of the existing
governed case state. It does not change Phase 5/6 retrieval, commercial or
feasibility authority, human approval, provider allowlists, SystemClock, or the
Outlook staging posture.

The application selects one response intent deterministically, builds a
client-safe `DraftContract`, makes at most one no-tool drafting call, validates
the returned prose, and then writes an immutable inquiry-response revision.
Only a validated revision receives a new exact-revision approval request.

## Intent Precedence

The resolver applies this stable precedence:

1. `REQUEST_CLIENT_INFORMATION` for current client open questions.
2. `CHANGE_ACKNOWLEDGEMENT` for an active material proposed change.
3. `RESCHEDULE_ACKNOWLEDGEMENT` for an active reschedule request.
4. `DECISION_PENDING` for a proposed or pending-approval decision.
5. `COMMUNICATE_RESTRICTION` for a governed `known_no` projection.
6. `PENDING_INTERNAL_CONFIRMATION` for another open internal blocker or conditional/unknown-internal state.
7. `COMPLETE_INQUIRY_RESPONSE` otherwise.

The contract carries the other relevant governed conditions as bounded content,
so a client-information response can still mention a supplied restriction or
pending decision without the model selecting authority or intent itself.

## Safety Invariants

- The provider receives only `DraftContract`, never direct database access,
  retrieval, tools, Outlook, Asana, or an autonomous loop.
- All response content is validated against current case revision/context, open
  questions, permitted monetary assertions, restrictions, and confirmation /
  decision claims before persistence.
- A material intake update retires an unsent current revision if its source case
  state is stale and cancels any open approval bound to it. A non-current or
  stale revision cannot be approved or executed.
- Outlook remains disabled in staging. `SEND_INQUIRY_RESPONSE` is approval-bound
  only; it does not make a delivery call in this slice.

## Provider Configuration Boundary

Default configuration is `CLIENT_DRAFT_PROVIDER=deterministic_fake`, which
makes no network request and is used by tests. The live option reuses the Phase
7 OpenAI Responses transport with `store: false` and strict JSON-schema output.

`READY_FOR_STAGING_LLM_PROVIDER_CONFIGURATION`

To enable a controlled synthetic staging smoke test later, set the following in
Render's staging service environment settings, not in Git or chat:

| Variable | Value | Secret |
| --- | --- | --- |
| `CLIENT_DRAFT_PROVIDER` | `openai` | no |
| `CLIENT_DRAFT_MODEL` | an approved model name available to the staging OpenAI project | no |
| `CLIENT_DRAFT_TIMEOUT_SECONDS` | optional positive seconds, default `60` | no |
| `OPENAI_API_KEY` | staging-project OpenAI API key | yes |

Return only safe status information: whether `OPENAI_API_KEY` is set, the
non-secret `CLIENT_DRAFT_MODEL` value, and confirmation that the other two
variables were set. Do not send the key to Codex. Keep Outlook disabled and use
only a synthetic case for the one-call smoke test.
