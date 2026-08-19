# Phase 8.7A Asana External Adapter Evaluation

Date:

- August 13, 2026

Status:

- `PHASE_8_7A_ASANA_EXTERNAL_ADAPTER_PASS`

## Scope

Phase 8.7A implemented one real external adapter only:

- real providers implemented = `1`
- real provider = `Asana`

No Outlook, calendar, payment, Slack, n8n, or additional provider execution was added in this phase.

## Repository Inspection Summary

Inspection before coding confirmed:

1. the live provider-neutral adapter contract already existed in `tools/phase_08_workflow/execution_runtime.py`
2. the safest existing action type for first rollout was `CREATE_INTERNAL_TASK_ITEM`
3. existing `ExecutionAttempt.external_reference` persistence already provided the correct correlation surface
4. semantic idempotency already lived on persisted `WorkflowAction.idempotency_key`
5. retry behavior was already deterministic but lacked a provider-neutral ambiguous-outcome code
6. environment loading already used uppercase env vars plus `load_env_value(...)`
7. no real Asana adapter existed in the repository
8. the repository already distinguished provider from action type through `target_adapter_code`
9. the narrowest safe rollout surface was outbound Asana task creation for governed internal-review work only
10. the pre-phase marker in force was `READY_FOR_PHASE_8_EXTERNAL_ADAPTER_ROLLOUT`

## Implemented Boundary

The governed execution path is now:

```text
WorkflowAction
-> Phase 8.6 execution eligibility
-> ExecutionAttempt start
-> adapter registry lookup
-> AsanaExecutionAdapter
-> Asana REST API
-> NormalizedExecutionResult
-> atomic attempt/action completion
-> WorkflowEvent audit
```

No orchestration, lifecycle, follow-up, observation, or Phase 7 consumer path bypasses `execution_runtime.py`.

## Authentication And Configuration

Authentication is Bearer-token based through environment-loaded configuration:

- `ASANA_ACCESS_TOKEN`
- `ASANA_WORKSPACE_GID`
- `ASANA_DEFAULT_PROJECT_GID`
- `ASANA_TEST_PROJECT_GID`
- `ASANA_API_BASE_URL`
- `ASANA_TIMEOUT_SECONDS`

Safety properties:

- credentials are loaded from environment/config only
- missing token, workspace, or destination fail closed before attempt creation
- tokens are not persisted into `WorkflowEvent`
- tokens are not persisted into `ExecutionAttempt.response_snapshot`
- tokens are not included in normalized adapter failures

## WorkflowAction Mapping

The first rollout supports only governed `CREATE_INTERNAL_TASK_ITEM` actions targeting `target_adapter_code="asana"`.

Deterministic payload mapping:

- `summary` -> Asana `name`
- `reason` + optional `task_surface_context_lines` + stable WNC references -> Asana `notes`
- `task_surface_project_id` or configured default project -> Asana `projects` or `memberships`
- `task_surface_section_id` -> Asana section membership
- `task_surface_assignee_id` -> Asana `assignee`
- `task_surface_due_on` or governed action due date -> Asana `due_on` / `due_at`

Embedded task references are deterministic and human-readable:

- rental case reference
- rental case id
- workflow action id
- workflow action UUID
- action type
- task kind
- semantic idempotency key

## Idempotency And Duplicate Prevention

Duplicate prevention now uses layered controls:

1. Phase 8.6 semantic idempotent success short-circuits re-execution after verified success
2. stable WNC action identity is embedded into Asana task notes for forensic correlation
3. successful provider task identity is persisted through `ExecutionAttempt.external_reference`
4. in-memory completion logic rejects cross-action or cross-case external-reference reuse
5. Supabase now enforces the same invariant with a unique partial index on successful `external_reference`

This phase intentionally does not rely on Asana task-title search as the primary duplicate-control mechanism.

## Ambiguous Outcomes

Phase 8.7A introduced a narrow provider-neutral correction:

- `EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS`

Ambiguous transport outcomes such as timeout/connection ambiguity now:

- never count as success
- are not blindly marked retry-eligible
- do not automatically create a duplicate Asana task on re-run

## Retry Classification

Deterministic provider mapping now behaves as follows:

- `400` -> `adapter_request_invalid`, not retryable
- `401` -> `adapter_authentication_failed`, not retryable
- `403` -> `adapter_forbidden`, not retryable
- `404` -> `adapter_resource_not_found`, not retryable
- `429` -> `adapter_rate_limited`, retryable
- `5xx` -> `adapter_server_error`, retryable
- invalid JSON / missing task gid -> `adapter_result_malformed`, not retryable
- ambiguous network/timeout path -> `adapter_outcome_ambiguous`, not retryable by default

## External Reference Persistence

Successful Asana task identity is stored as:

- `asana:task:<gid>`

It remains directly attributable to:

- `RentalCase`
- `WorkflowAction`
- `ExecutionAttempt`

No separate Asana mapping store was introduced.

## Focused Verification

Focused Python adapter/runtime coverage:

- `python3 -m unittest tools.phase_08_workflow.tests.test_asana_adapter`
- result: `13 / 13` passing

Focused DB external-reference guard:

- `npx -y supabase@latest test db --local supabase/tests/41_phase_08_asana_external_reference_guardrails.sql`
- result: `5 / 5` assertions passing

## Full Regression Results

Phase 8 Python:

- `python3 -m unittest discover -s tools/phase_08_workflow/tests`
- result: `98 / 98` passing

Phase 7 Python:

- `python3 -m unittest discover -s tools/phase_07_reasoning/tests`
- result: `127 / 127` passing

Phase 5 Python:

- `python3 -m unittest discover -s tools/phase_05_search/tests`
- result: `24 / 24` passing

Phase 6 Python:

- `python3 -m unittest discover -s tools/phase_06_search/tests`
- result: `6 / 6` passing

Supabase DB:

- `npx -y supabase@latest test db --local`
- result: `41` files, `1059` tests, `PASS`

## Local Corpus State

No full local DB reset was performed during 8.7A verification.

One local restoration step was required:

- `python3 -m tools.phase_06_search.generate_embeddings`

Observed live local counts after restoration:

- Phase 5 current chunk sets: `22`
- Phase 5 chunks in current chunk sets: `525`
- Phase 5 searchable current chunk surface: `21` chunk sets / `492` chunks
- Phase 6 deterministic historical embedding count: `112`

The distinction between `525` and `492` is expected:

- `525` counts all chunks in current chunk sets
- `492` is the narrower searchable `private.current_knowledge_chunks` surface

## Manual Smoke Test

Live smoke test:

- performed / not performed: `not performed`
- reason: this phase validated the real adapter through mocked transport only; no governed safe-project manual invocation was executed in this run

## Safety Metrics

- real providers implemented = `1`
- real provider = `Asana`
- Outlook calls = `0`
- Google Calendar calls = `0`
- Mollie calls = `0`
- n8n execution dependencies = `0`
- LLM-selected provider execution = `0`
- approval-required pre-approval Asana calls = `0`
- blocked Asana calls = `0`
- stale Asana calls = `0`
- superseded Asana calls = `0`
- cancelled Asana calls = `0`
- duplicate semantic Asana tasks from verified retry = `0`
- provider failure counted as success = `0`
- timeout counted as verified success = `0`
- malformed provider response counted as success = `0`
- successful Asana action without ExecutionAttempt = `0`
- Asana execution causing direct lifecycle mutation = `0`
- Asana execution directly activating CaseDecision = `0`
- Asana execution directly resolving Blocker = `0`
- Asana execution directly satisfying Requirement without governed rule = `0`
- cross-case external reference mutation = `0`
- credentials persisted in DB/audit = `0`
- credentials written to logs = `0`

## Limitations Preserved Intentionally

- no inbound Asana sync
- no task completion webhook handling
- no Asana comment ingestion
- no Outlook rollout
- no client-facing adapter execution
- no autonomous retry orchestration
- no provider-side duplicate lookup beyond stable local identity plus persisted external-reference controls

## Conclusion

Phase 8.7A successfully proved the first real outbound external adapter without violating the Phase 8.6 execution boundary.

The architecture is now ready for the next controlled external-adapter step:

- `READY_FOR_PHASE_8_CLIENT_FACING_ADAPTER_ROLLOUT`
