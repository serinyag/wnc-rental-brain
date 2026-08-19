# Phase 8 Test Console Request Path Root Cause Note

Date:

- August 14, 2026

Scope:

- pre-remediation inspection note for Test Console Remediation A

## Reproduced Symptoms

Observed request behavior before remediation:

- `GET /` loads successfully when executed alone, but becomes unavailable behind overlapping case-detail requests
- `GET /cases/143` takes about `3.1s` in direct HTTP reproduction
- `GET /cases/145` takes about `3.9s` in direct HTTP reproduction
- repeated or overlapping navigation through the single-server console makes the root page appear hung

Concrete reproduction using the live WSGI app in-process:

- sequential:
  - `/` -> about `0.395s`
  - `/cases/143` -> about `3.109s`
  - `/cases/145` -> about `3.912s`
- concurrent:
  - `/cases/145` -> about `4.139s`
  - second `/cases/145` -> about `8.283s`
  - `/` queued behind those reads -> about `8.407s`

This reproduces the audit symptom: the console does not deadlock immediately, but it becomes operationally unreliable and appears to hang under overlapping case navigation.

## Affected Routes

- root/list:
  - `GET /`
  - `GET /cases`
- case detail:
  - `GET /cases/{rental_case_id}`

POST mutation routes were not the primary source of the hang finding.

## Root Cause Classification

Primary causes:

1. excessive blocking query fan-out on case-detail page load
2. N+1 evidence loading on case-detail page load
3. unbounded workflow-event timeline loading
4. single-threaded WSGI request handling amplifying the slow read path into queueing/hang symptoms
5. no bounded timeout/error normalization at the DB subprocess boundary

Not observed as causes:

- Phase 7 invocation on page load
- OpenAI/model calls on page load
- Asana calls on page load
- Outlook calls on page load
- workflow mutation on page load

## Current Query / Request Shape

### Root/List

- one SQL query through `TestConsoleService.list_test_cases()`
- query joins `rental_cases`, `workflow_events`, blockers, questions, approvals, and actions to compute list summaries

### Case Detail

Current `GET /cases/{id}` path:

1. load test-case metadata from `workflow_events`
2. load orchestration snapshot through `SupabaseWorkflowOrchestrationRepository.load_case_snapshot()`
3. load raw evidence mapping from `workflow_events`
4. load case source records
5. for each source record:
   - load observations for that source
   - for each observation, load its effect
6. render Working Proposal and human-work preview from the loaded snapshot

Measured pre-remediation direct query counts:

- case `143`: `25` JSON queries
- case `145`: `34` JSON queries
- case `146`: `22` JSON queries
- case `147`: `22` JSON queries
- case `148`: `20` JSON queries

Each query currently flows through `run_supabase_query()`, which performs:

- `docker ps` to find the DB container
- then `docker exec ... psql`

That means the rich case-detail path is paying dozens of subprocess launches for one page render.

## Dominant Calls

The dominating cost is not a single expensive business-rule computation.

The dominating cost is repeated subprocess-backed read amplification:

- many small snapshot table reads
- per-source observation reads
- per-observation effect reads
- full event timeline read

This is made worse by the single-threaded `wsgiref.simple_server` server, which serializes overlapping requests.

## Proposed Minimum Fix

1. Replace the console case-detail read fan-out with bounded aggregated read helpers.
2. Batch evidence loading instead of per-source and per-observation queries.
3. Bound initial workflow-event timeline loading to the most recent N events.
4. Cache DB container discovery so every query does not re-run `docker ps`.
5. Add bounded timeout handling and normalized read errors at the console query boundary.
6. Add request timing instrumentation for root/detail stage timings.
7. Use a threaded WSGI server so overlapping reads do not serialize into apparent hangs.

## Why This Does Not Alter Workflow Semantics

The proposed changes affect only:

- how persisted state is read
- how much historical event data is loaded initially
- how errors/timeouts surface
- how concurrent HTTP requests are served

They do not change:

- rental business rules
- lifecycle transitions
- approval behavior
- WorkflowAction semantics
- Phase 7 reasoning semantics
- Working Proposal truth semantics
- provider execution behavior

This is a request-path remediation only.

