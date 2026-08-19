# Phase 8 Test Console Request Path Remediation

Date:

- August 14, 2026

Status:

- `PHASE_8_TEST_CONSOLE_REQUEST_PATH_REMEDIATION_COMPLETE`

Readiness assessment:

- `TEST_CONSOLE_REQUEST_PATH_STABLE_FOR_PROJECTION_REMEDIATION`

## Audit Finding

This remediation addresses only the first top-level failure from the realistic rental scenario validation audit:

1. console root and RentalCase pages repeatedly hang or load unreliably

It does not address the second major finding:

> The Working Proposal currently hides too much persisted structured truth behind `unknown`, and the reason-to-action chain remains too implicit for an operator.

That remains intentionally unresolved for:

- `Test Console Remediation B — Working Proposal Truth Projection & Operator Action Context`

## Root Cause Summary

Exact reproduced root causes:

1. case-detail reads used excessive blocking query fan-out
2. evidence loading used an N+1 pattern:
   - source records
   - per-source observations
   - per-observation effects
3. initial case render loaded an unbounded workflow-event timeline
4. every DB read used subprocess-backed `docker exec ... psql`, and every query also re-ran `docker ps`
5. the console used a single-threaded WSGI server, so overlapping requests serialized into apparent hangs
6. the console had no bounded DB subprocess timeout or normalized read-failure surface

Not root causes:

- Phase 7 reasoning on page load
- OpenAI / model calls on page load
- Asana calls on page load
- Outlook calls on page load
- workflow mutation on page load

## Reproduction Before Remediation

Direct HTTP reproduction before the fix:

- sequential:
  - `/` -> about `0.395s`
  - `/cases/143` -> about `3.109s`
  - `/cases/145` -> about `3.912s`
- overlapping requests against the same server:
  - `/cases/145` -> about `4.139s`
  - second `/cases/145` -> about `8.283s`
  - `/` queued behind them -> about `8.407s`

Direct service-level query counts before the fix:

- `list_test_cases()` -> `1` query
- `load_case_detail(143)` -> `25` queries
- `load_case_detail(145)` -> `34` queries
- `load_case_detail(146)` -> `22` queries
- `load_case_detail(148)` -> `20` queries

Observed request shape before remediation:

- root/list:
  - one list query
- case detail:
  - test-case metadata query
  - one repository query per snapshot table
  - one raw-evidence query
  - one source-record query
  - per-source observation queries
  - per-observation effect queries

## Implementation Changes

Files changed:

- `tools/phase_05_chunking/generate_pilot.py`
- `tools/phase_08_workflow/orchestration_repository.py`
- `tools/phase_08_workflow/supabase_observation_repository.py`
- `tools/phase_08_workflow/test_console_service.py`
- `tools/phase_08_workflow/test_console.py`
- `tools/phase_08_workflow/tests/test_test_console_service.py`
- `tools/phase_08_workflow/tests/test_test_console_app.py`
- `docs/phase-08/PHASE_8_TEST_CONSOLE_REQUEST_PATH_ROOT_CAUSE_NOTE.md`
- `docs/phase-08/PHASE_8_TEST_CONSOLE_REQUEST_PATH_REMEDIATION.md`

No migration was required.

No Supabase schema change was required.

Remediation changes applied:

1. cached local Supabase container discovery
   - removed repeated `docker ps` lookup from every query
2. added optional subprocess timeout support to `run_supabase_query()`
3. added console-specific timeout wrapper with normalized read errors:
   - `DATABASE_READ_TIMEOUT`
   - `DATABASE_READ_FAILED`
4. replaced case-detail core snapshot fan-out with one aggregated bounded read
5. added bounded workflow-event timeline read with total-count metadata
6. replaced evidence N+1 loading with batched case-scoped reads for:
   - source records
   - observations
   - observation effects
7. added partial read fallback for non-core panels:
   - evidence panel can degrade safely
   - workflow-event timeline can degrade safely
8. switched the console server from single-threaded WSGI to threaded WSGI
9. added request and stage timing instrumentation to the real console launch
10. added structured app-level error pages instead of raw stack traces for normal read failures

## Query / Request Architecture Before

### Root/List

- `GET /` and `GET /cases`
- one SQL query via `list_test_cases()`

### Case Detail

`GET /cases/{id}`:

1. load test-case metadata
2. load orchestration snapshot through many table-specific repository calls
3. load raw evidence mapping
4. load source records
5. for each source record:
   - load observations
   - for each observation, load effect
6. build projections in Python

This yielded `20-34` DB queries for a single case page in the observed audit cases.

## Query / Request Architecture After

### Root/List

- still a dedicated summary query only
- no full case-detail aggregation on root load

### Case Detail

`GET /cases/{id}` now uses a bounded, explainable 7-query shape:

1. test-case metadata
2. aggregated core case snapshot
3. bounded workflow events plus total event count
4. raw evidence event mapping
5. case source records
6. case observations
7. case observation effects

The core snapshot aggregation now loads:

- `RentalCase`
- case facts
- blockers
- requirements
- open questions
- approvals
- proposed changes
- reschedule requests
- case decisions
- WorkflowActions
- ExecutionAttempts
- FollowUps
- milestones
- artifacts
- reasoning projections

Workflow events are now loaded separately and bounded.

## WorkflowEvent Timeline Bound

Initial case render no longer loads the full event history.

Current bound:

- most recent `100` events by default

The case detail view also tracks:

- total event count
- whether the panel is showing a bounded subset

## Connection / Resource Handling

Improved:

- local DB container discovery is cached
- DB subprocesses now respect a bounded timeout when the console uses the default query runner
- request failures are surfaced as structured read errors instead of indefinite waits

Unchanged:

- the console still reads through the existing repository / Supabase boundary
- no persistence layer replacement was introduced

## Timeout / Error Handling

Console read failures now fail clearly instead of hanging indefinitely.

Operator-facing structured error behavior:

- `DATABASE_READ_TIMEOUT`
- `DATABASE_READ_FAILED`
- `RENTAL_CASE_NOT_FOUND`
- `TEST_CONSOLE_CASE_REQUIRED`
- `UNEXPECTED_SERVER_ERROR`

Unexpected exceptions are logged safely and surfaced to the operator as a structured server failure instead of a raw traceback.

## Provider / LLM Isolation

Observed before remediation:

- no Phase 7 / model invocation on root or case load
- no Asana or Outlook provider calls on root or case load

Observed after remediation:

- unchanged

Page load remains read-only and local-state driven.

The console renders persisted reasoning projections where present and does not require fresh model execution merely to view a page.

## Measured Results After Remediation

Direct service timings after the fix:

- `list_test_cases()` -> about `0.602s`
- `load_case_detail(143)` -> about `0.660s`
- `load_case_detail(145)` -> about `0.563s`
- `load_case_detail(146)` -> about `0.997s`

Direct service query counts after the fix:

- `list_test_cases()` -> `1` query
- `load_case_detail(143)` -> `7` queries
- `load_case_detail(145)` -> `7` queries

Real HTTP timings with the threaded server:

- sequential:
  - `/` -> about `0.620s`
  - `/cases/143` -> about `0.658s`
  - `/cases/145` -> about `0.564s`
- concurrent:
  - `/` -> about `0.105s`
  - `/cases/145` -> about `0.989s`
  - second `/cases/145` -> about `0.990s`

The overlapping-request queueing failure reproduced before remediation was no longer present after the fix.

## Manual Stability Run

Launch command used:

```bash
python3 -m tools.phase_08_workflow.test_console
```

Manual navigation sequence exercised:

- `/`
- `/cases/143`
- `/`
- `/cases/145`
- `/cases/146`
- `/`
- `/cases/145`
- `/`

Observed results:

- `/` -> `200`, about `0.352s`
- `/cases/143` -> `200`, about `0.613s`
- `/` -> `200`, about `0.116s`
- `/cases/145` -> `200`, about `0.562s`
- `/cases/146` -> `200`, about `0.517s`
- `/` -> `200`, about `0.115s`
- `/cases/145` -> `200`, about `0.609s`
- `/` -> `200`, about `0.092s`

Manual stability outcome:

- no hangs
- no endless loading
- no server restart required
- no progressive degradation observed

Repeated-load sample:

- root median -> `0.078s`
- root slowest -> `0.132s`
- rich-case median -> `0.525s`
- rich-case slowest -> `0.553s`

## Focused Console Tests

Focused console suite run:

```text
python3 -m unittest
  tools.phase_08_workflow.tests.test_test_console_projection
  tools.phase_08_workflow.tests.test_test_console_service
  tools.phase_08_workflow.tests.test_test_console_app
```

Result:

- `17 / 17 PASS`

Covered remediation checks include:

- structured read-failure normalization
- batched console read path usage
- repeated case-detail reads remaining non-mutating
- page-load provider isolation
- structured error rendering in the app layer

## Full Regressions

Phase 8:

- `python3 -m pytest tools/phase_08_workflow/tests -q`
- result: `125 / 125 PASS`

Phase 7:

- `python3 -m pytest tools/phase_07_reasoning/tests -q`
- result: `127 / 127 PASS`

Phase 5:

- `python3 -m pytest tools/phase_05_chunking/tests -q`
- result: `27 / 27 PASS`

Phase 6:

- `python3 -m pytest tools/phase_06_search/tests -q`
- result: `6 / 6 PASS`

Supabase:

- `npx -y supabase@latest test db --local`
- result: `41 files / 1059 tests PASS`

## Corpus Verification

Supabase reset was not required for this remediation.

Because no reset was performed, retrieval corpus restoration was not required in this task.

## Safety Metrics

- business-rule changes = `0`
- lifecycle semantic changes = `0`
- approval semantic changes = `0`
- WorkflowAction semantic changes = `0`
- Working Proposal semantic changes = `0`
- inquiry extraction added = `0`
- Outlook inbound added = `0`
- new autonomous agent behavior = `0`
- page-load lifecycle mutations = `0`
- page-load CaseDecision activations = `0`
- page-load WorkflowAction mutations = `0`
- page-load ExecutionAttempts created = `0`
- page-load Asana calls = `0`
- page-load Outlook calls = `0`
- page-load LLM calls = `0`
- browser-exposed privileged credentials = `0`
- indefinitely hanging tested requests after remediation = `0`

## Remaining Issues

Still intentionally unresolved:

1. the Working Proposal still hides too much persisted structured truth behind `unknown`
2. the reason-to-action chain is still too implicit for an operator

Those were preserved exactly as instructed.

Also still true:

- the event timeline is intentionally bounded rather than fully expanded on initial load
- the console remains a local read/control surface, not a business-logic owner

## Final Assessment

This remediation fixed the request-path stability problem without altering workflow semantics.

The console is now stable enough to support the next controlled remediation:

- `Test Console Remediation B — Working Proposal Truth Projection & Operator Action Context`

