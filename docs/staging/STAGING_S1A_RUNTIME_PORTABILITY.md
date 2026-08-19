# Staging Preparation S1A - Runtime Portability

## Scope

This document records the completed S1A portability work for the local WNC Rental Brain repository.

Implemented in S1A:

- reproducible Python packaging via `pyproject.toml`
- standard deployable WSGI entrypoint via `tools/phase_08_workflow/wsgi.py`
- `DATABASE_URL`-backed direct PostgreSQL transport at the shared SQL boundary with legacy Docker fallback preserved

Explicitly not implemented here:

- `APP_ENV`
- staging auth or allowlists
- staging clock restrictions
- `/healthz`
- startup environment validation
- deployment/provider setup

WSGI deployable: yes

Internet-safe: no

## Old Architecture

Before S1A, the shared SQL boundary in `tools/phase_05_chunking/generate_pilot.py` executed database work through:

1. `docker ps`
2. local Supabase DB container discovery
3. `docker exec ... psql`

Phase 5, Phase 6, Phase 7, and Phase 8 callers all depended on that local Docker path indirectly through `run_supabase_query(...)`.

## New Architecture

The shared SQL boundary now selects transport per call:

```text
DATABASE_URL present and non-empty
-> direct psycopg PostgreSQL transport

DATABASE_URL absent
-> legacy local Docker + psql transport
```

Application logic above `run_supabase_query(...)` remains transport-agnostic.

Direct mode behavior:

- uses Psycopg 3 (`psycopg[binary]`)
- does not shell out to `psql`
- preserves the existing `{"rows": [...]}` JSON contract for `expect_json=True`
- preserves raw execution for `expect_json=False`
- honors `timeout_seconds` through connection timeout plus PostgreSQL `statement_timeout`
- does not silently fall back to Docker when `DATABASE_URL` is configured and fails

## Packaging

`pyproject.toml` was added with:

- Python requirement: `>=3.13`
- runtime dependencies:
  - `certifi`
  - `openpyxl`
  - `psycopg[binary]`
  - `python-docx`
- optional dev dependencies:
  - `pytest`

The repo layout was intentionally left in-place. No `src/` reorganization was introduced.

## WSGI Entrypoint

New entrypoint:

- `tools/phase_08_workflow/wsgi.py`

It reuses the existing Test Console WSGI app:

```python
from .test_console import build_test_console_app

application = build_test_console_app()
```

Validated properties:

- imports without starting the development server
- exposes one standard WSGI callable
- uses current environment configuration
- preserves the existing local start path

The existing local command remains supported:

```bash
python3 -m tools.phase_08_workflow.test_console
```

## Query Compatibility

Direct transport preserves the existing caller contract by:

- wrapping `expect_json=True` SQL with the same JSON row-shaping strategy already used by the Docker path
- returning Python `dict` / `list` / `None` / `bool` / numeric values with the same normalized structure expected by callers
- preserving `WITH ... INSERT ... RETURNING` behavior
- preserving multi-statement non-JSON execution for mutation/bootstrap paths

Focused parity coverage includes:

- `SELECT`
- multi-row `SELECT`
- zero-row `SELECT`
- `INSERT ... RETURNING`
- `UPDATE ... RETURNING`
- `DELETE ... RETURNING`
- `WITH ... SELECT`
- `WITH ... INSERT ... RETURNING`
- JSON / JSONB
- arrays
- `NULL`
- timestamps
- timeout normalization

## Validation Summary

### Clean install

Validated in a clean virtualenv:

```bash
python3 -m venv /tmp/wnc-portability-venv
source /tmp/wnc-portability-venv/bin/activate
pip install -e '.[dev]'
```

Observed result:

- install succeeded
- important imports succeeded for Phase 5, Phase 6, Phase 7, Phase 8, and the new WSGI entrypoint

### Focused tests

Focused portability tests run:

```bash
python -m pytest -q \
  tools/phase_05_chunking/tests/test_generate_pilot_query_runner.py \
  tools/phase_05_chunking/tests/test_generate_pilot_transport.py \
  tools/phase_08_workflow/tests/test_wsgi.py
```

Observed result:

- `18 passed`

### WSGI smoke

Validated in direct `DATABASE_URL` mode against the local Supabase PostgreSQL endpoint at `127.0.0.1:54322`:

- import succeeded
- callable existed
- root route returned `200 OK`
- case route returned `200 OK`
- import did not start the development server

### Existing local start command

Validated by starting:

```bash
python -m tools.phase_08_workflow.test_console --host 127.0.0.1 --port 8766
```

Observed result:

- server started successfully
- `/` returned `200`
- `/cases/115` returned `200`

## Local DATABASE_URL Validation

Validation used the same underlying local Supabase database in both modes:

- direct mode: `DATABASE_URL` set to local Postgres on `127.0.0.1:54322`
- legacy mode: `DATABASE_URL` unset, falling back to Docker + `psql`

### Direct mode inquiry journey

Completed successfully in direct mode:

1. create case
2. inject raw evidence
3. inject `active_event_window`
4. inject `event_type`
5. run Inquiry Intake
6. run Inquiry Waiting
7. advance TestClock by 7 days
8. evaluate follow-ups
9. re-run Inquiry Waiting
10. generate draft
11. edit draft
12. approve exact revision
13. simulate send

Observed direct journey case:

- `RentalCase`: `RC-20260815150436341`
- `rental_case_id`: `115`
- final draft status: `simulated_sent`
- execution result: success

### Direct mode subprocess counts

Measured while direct mode was active for the full journey:

- docker ps calls: `0`
- docker exec calls: `0`
- psql subprocess calls: `0`

### Representative Docker regression

Observed legacy Docker journey case:

- `RentalCase`: `RC-20260815150437791`
- `rental_case_id`: `116`
- final draft status: `simulated_sent`
- execution result: success

Legacy Docker fallback remains functional when `DATABASE_URL` is absent.

## Performance Comparison

Measured against the same local Supabase database:

| Operation | Direct mode | Docker mode |
| --- | ---: | ---: |
| simple `SELECT` | `12.27 ms` | `294.69 ms` |
| representative mutation | `18.81 ms` | `101.45 ms` |
| snapshot query (`load_case_detail`) | `64.77 ms` | `612.83 ms` |
| Inquiry Intake | `76.43 ms` | `586.12 ms` |
| Inquiry Waiting (initial) | `155.58 ms` | `1133.00 ms` |
| simulated send | `155.53 ms` | `1540.32 ms` |
| full inquiry journey | `1450.09 ms` | `14414.71 ms` |

This improvement comes from removing repeated Docker process discovery and `psql` subprocess overhead. No additional workflow-level optimizations were introduced in S1A.

## Direct Transport Compatibility By Caller Surface

Validated in `DATABASE_URL` mode:

- Phase 5 bulk/chunking query path:
  - `generate_bulk.determine_bulk_coverage()` succeeded
  - coverage rows loaded: `24`
- Phase 5 search/embedding query path:
  - `tools.phase_05_search.generate_embeddings.load_current_candidates()` succeeded
  - current candidate rows loaded: `492`
- Phase 6 historical embedding query path:
  - `tools.phase_06_search.generate_embeddings.load_current_candidates()` succeeded
  - current candidate rows loaded: `112`
  - active approved model id: `1`
  - coverage: `112 / 112`, missing `0`
- Phase 8 workflow/query path:
  - full inquiry console journey completed successfully in direct mode

## Regression Matrix

Validated in the clean virtualenv with `DATABASE_URL` unset so the legacy local Docker path remained exercised:

- Phase 8: `187 passed`, `15 warnings`, `11 subtests passed`
- Phase 7: `127 passed`, `24 subtests passed`
- Phase 5 chunking: `41 passed`
- Phase 5 search: `24 passed`
- Phase 6: `6 passed`
- Supabase DB tests: `43 files / 1077 tests PASS`

## Corpus State After Validation

### Phase 5

- current chunk sets: `22`
- current chunks: `525`
- searchable current sets: `21`
- searchable current chunks: `492`

### Phase 6

- historical search units: `112`
- active approved models: `1`
- embeddings: `112`
- missing embeddings: `0`

## Safety Metrics

Observed / assessed for S1A:

- business-rule changes = `0`
- workflow semantic changes = `0`
- database schema changes = `0`
- Phase 5 retrieval semantic changes = `0`
- Phase 6 retrieval semantic changes = `0`
- direct `DATABASE_URL` mode docker ps calls = `0`
- direct `DATABASE_URL` mode docker exec calls = `0`
- direct `DATABASE_URL` mode psql subprocess calls = `0`
- configured `DATABASE_URL` failure silently falls back to Docker = `0`
- `DATABASE_URL` leaked to logs = `0`
- `DATABASE_URL` leaked to browser = `0`
- existing local Docker path broken = `0`
- WSGI import starts development server = `0`
- real provider calls introduced = `0`
- TestClock semantic changes = `0`
- cross-case mutation regression = `0`
- idempotency regression = `0`
- audit completeness regression = `0`

## Known Limitations

- The Test Console is now deployable through a standard WSGI callable, but it is still not safe for public internet exposure. S1B must add environment and access controls.
- The current local baseline has no active approved Phase 5 embedding-model row in `private.knowledge_embedding_models`. Direct transport compatibility for Phase 5 was therefore proven through current candidate loading and the broader regression matrix, not through a live Phase 5 coverage query against an active model row.
- S1A intentionally does not add `APP_ENV`, authentication, allowlists, startup validation, or staging provider controls.

## S1B Boundary

If the repository proceeds, the next task is:

`Staging Preparation S1B - Environment & Safety Hardening`

Expected later scope:

- `APP_ENV`
- staging basic auth
- disable TestClock outside local
- staging recipient allowlists
- staging Asana project allowlists
- `/healthz`
- startup validation
- bootstrap/reset safety guards

## Readiness

Portability gate classification:

- dependency packaging: `GREEN`
- WSGI deployability: `GREEN`
- remote-database portability: `GREEN`
- existing local compatibility: `GREEN`

Readiness marker:

`READY_FOR_STAGING_SAFETY_HARDENING`
