# Asana rental operational projection

## Existing implementation map

| Concern | Existing implementation | Audit finding |
| --- | --- | --- |
| Transport and configuration | `asana_adapter.py`: `AsanaAdapterConfig`, `UrllibAsanaTransport` | Token, workspace, default project, timeout; POST task creation only |
| Governed action | `CREATE_INTERNAL_TASK_ITEM`, adapter `task_surface` | Requires task_kind, summary, reason; optional project, section, assignee, due date and context |
| Orchestration | `orchestration_runtime.py`, `execution_runtime.py` | Existing approval, readiness, revision, idempotency, start and completion checks |
| Canonical persistence | `orchestration_repository.py`; workflow actions and execution attempts | Successful task ID on attempt.external_reference; unique successful external references |
| Ownership | `context_aware_drafting.py` ResolutionItem and existing resolution WorkflowActions | CLIENT, WNC_INTERNAL, EXTERNAL_PARTY, GOVERNED_DECISION; provider success is not obligation resolution |
| Console | `test_console_service.py`, `test_console.py`, `test_console_projection.py` | Synthetic standalone task endpoint, provider registry, inferred task reference |
| Safety | `runtime_environment.py`, `provider_safety.py` | Staging Asana gate and project allowlist; production console startup refused |
| Tests | `test_asana_adapter.py`, `test_execution_runtime.py`, `test_provider_safety.py` | Mocked create and action replay coverage |

No existing master-task lifecycle, update/subtask transport, custom-field mapping, provider reconciliation, or inbound task-completion ingestion was found. Old task notes exposed action IDs/UUIDs and semantic keys. The legacy adapter classified POST server errors as retryable; these now preserve ambiguity instead.

## Projection contract and preparation

`asana_projection.py` compiles current persisted case facts, timing, questions, pending review matters, and existing resolution actions into an immutable `asana_rental_projection_v1` action. `POST /api/operator/cases/{case}/asana-projection` prepares it without contacting providers. Exact plan content, case revision, case UUID, workspace/project identity and hash are checked again at execution and immediately before each mutation. Changed content receives a new canonical action; replay of identical content returns the same action.

`asana_projection` is an explicit adapter code on the existing CREATE_INTERNAL_TASK_ITEM action. One action applies a case projection, including its subordinate work. It uses the ordinary Phase 8 execution orchestration, not a separate send loop or alternate approval bypass.

## Operator task

One master task per case, with CLIENT, EVENT, CURRENT STATUS, OPEN ITEMS, NEXT ACTIONS and OUTLOOK sections. Dates are displayed in Europe/Amsterdam time. Existing lifecycle and open obligations determine a small status label in the description; native `completed` represents terminal closure. No custom fields, assignee or due date are fabricated.

Resolution work becomes subtasks. CLIENT obligations stay in the master summary. WNC_INTERNAL checks, WNC follow-up for EXTERNAL_PARTY obligations and GOVERNED_DECISION reviews retain distinct ownership. Explicit same-owner `resolution_group_key` and matching title allow one task to hold multiple semantic identities. Each binding retains its member keys and source action IDs in Supabase. Unknown ownership or conflicting grouping fails closed. Omission does not close a task, and unresolved members cannot disappear or silently move to a new group. Explicit governed resolved/completed/cancelled/superseded statuses complete existing work without deleting its history.

Existing unbound requirements and pending decisions/changes remain visible as open review matters in the master. The projection does not invent new requirements or commercial decisions. It does not generate a client reply, infer new dates, or rerun drafting.

## Persistence and idempotency

The existing execution-attempt response snapshot stores all confirmed provider bindings, including master/subtask GIDs, rental_case_id, workspace/project, projection action, attempt, owner and semantic members. Successful operations use an operation-specific external reference (`asana:projection:<case>:<attempt>`), because multiple update operations correctly target the same task. The console reads the master GID from the binding; the existing global uniqueness rule on successful execution references is preserved.

Migration `20261003000200_phase_08_asana_projection_fences.sql` adds two narrow triggers: immutable projection action content and a case-row-locked attempt fence. Concurrent projection actions cannot both start; a started or nonretryable failed attempt blocks later projections across revisions. The first attempt fixes workspace/project/case identity. A process crash or failed completion transaction intentionally leaves the fence in place.

Confirmed partial bindings survive retryable 429 responses. Retry verifies and reuses those objects. Timeout, 5xx after a mutation, malformed success, unexpected identity, or inconclusive verification is nonretryable. A new action/revision cannot bypass uncertainty. No automatic backoff loop calls Asana.

## Reconciliation and human edits

`POST /api/operator/cases/{case}/actions/{action}/observe-asana` performs bounded, paginated provider reads and appends an observation event. It locates a master using the exact WNC reference, then verifies workspace, project, parent relationships and projected content. Missing, duplicate, moved or edited objects require review. No match is not evidence that recreation is safe. No provider-supplied pagination URL is followed.

Before updates, every previously bound object is read and compared with the last governed projection. Human edits/completion stop the write and require review. Observation never changes facts, price, availability, booking state, policy, requirements or decisions; it never releases an ambiguity fence. Automatic adoption/resumption and inbound Asana truth synchronization are intentionally unsupported. An ambiguous live certification stops for separately governed reconciliation.

Asana OAuth-specific external metadata is not assumed: the existing integration uses an access token with no established OAuth app binding. A short visible WNC reference supports read-only candidate discovery. API details follow [Asana project task listing](https://developers.asana.com/reference/gettasksforproject), [subtask creation](https://developers.asana.com/reference/createsubtaskfortask) and [external metadata requirements](https://developers.asana.com/docs/custom-external-data).

## Provider boundary

The new adapter requires APP_ENV=staging, enabled Asana gate, configured token/workspace/project, allowlisted project and the official fixed API origin. It verifies the provider project's workspace and non-archived state before writing, and validates every existing task's scope. Local and production execution are rejected. The service's real mode also requires its global provider gate and installed database fence. Resolution actions cannot use the old one-task-per-action console real path; operators prepare the rental projection instead.

## Validation

Run `docs/staging/asana_operational_certification/run_provider_free.py` using the local Python test environment, with `focused`, `phase8` or `full_suite`. It selects the WNC local database/container explicitly and blocks external HTTP. PostgreSQL fixture rows and migration DDL are rolled back. The full suite uses importlib collection to avoid duplicate test_contracts module names across phases.

Coverage includes canonical contracts, creation, replay, updates, grouping and owners, closure, partial retries, ambiguous outcomes, crash fences, scope/production safety, read-only reconciliation, human-edit boundaries, authenticated routes, service registration and real PostgreSQL persistence.
