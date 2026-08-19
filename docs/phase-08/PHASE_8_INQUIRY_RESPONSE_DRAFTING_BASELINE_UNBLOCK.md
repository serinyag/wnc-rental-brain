# Phase 8 Inquiry Response Drafting Baseline Unblock

Date:

- Saturday, August 15, 2026

Status:

- `READY_FOR_PHASE_8_INQUIRY_RESPONSE_DRAFTING_SLICE`

## Initial Strict Readiness State

On Friday, August 14, 2026, Inquiry Waiting & Follow-Up was functionally passing but strict promotion remained blocked at:

- `NOT_READY_FOR_PHASE_8_INQUIRY_RESPONSE_DRAFTING_SLICE`

The slice itself was already clean:

- Inquiry Waiting focused suite: `59 / 59 PASS`
- Phase 8: `166 / 166 PASS`
- Phase 7: `127 / 127 PASS`
- Phase 5 chunking: `27 / 27 PASS`
- Phase 5 search: `24 / 24 PASS`
- targeted Phase 8 DB slice: `7 / 7 PASS`

The blockers were unrelated repository-baseline losses.

## Blocker Diagnosis

### Blocker A: Phase 5 Supabase Bulk Coverage

Classification:

- `CORPUS_NOT_RESTORED`

Expected state:

- live current bulk chunk corpus present after post-reset restoration
- historically observed local baseline:
  - current chunk sets near `22`
  - current chunks near `525`
  - searchable current chunk sets near `21`
  - searchable current chunks near `492`

Actual state before restoration:

- `private.knowledge_chunk_sets where generation_status = 'current'`: `0`
- current chunks in those current sets: `0`
- `supabase/tests/18_phase_05_bulk_chunking_coverage.sql`: `8 / 9` failed

Likely cause:

- `supabase db reset --local` restored seeded catalogue state but did not recreate the generated Phase 5 current chunk corpus

Did Inquiry Waiting cause it:

- no

Minimum correction:

- rerun the repository's established bulk generation/load command

### Blocker B: Phase 6 Historical Retrieval Environment

Classification:

- `ENVIRONMENT_STATE_LOSS`

Expected state:

- exactly one active retrieval-approved historical embedding model
- repo-aligned historical model identity:
  - provider: `openai`
  - model code: `text-embedding-3-small`
  - dimensions: `1536`
- complete historical embedding coverage for current eligible units

Actual state before restoration:

- `python3 -m pytest tools/phase_06_search/tests -q`: `5 / 6 PASS`, `1` fail
- failing test:
  - `HistoricalRetrievalContractTests::test_live_hybrid_order_matches_direct_hybrid_and_stays_phase6_only`
- exact error:
  - `No active retrieval-approved historical embedding model is registered. Run embedding generation first.`
- `private.current_historical_case_embedding_inputs`: `112`
- active retrieval-approved historical models: `0`
- historical embedding rows: `0`

Likely cause:

- local reset preserved the seeded historical search-unit corpus but removed the non-seeded model registry row and embedding rows

Did Inquiry Waiting cause it:

- no

Minimum correction:

- rerun the repository's live historical embedding generation command so the frozen approved model is re-registered and the current embedding corpus is repopulated

## Phase 6 Registry Mechanics

Model metadata is stored in:

- `private.historical_case_embedding_models`

The Phase 6 retrieval loader resolves the active model by selecting rows where:

- `is_retrieval_approved = true`
- `is_active = true`

The generation tool used by the live repository is:

- `python3 -m tools.phase_06_search.generate_embeddings`

Observed live behavior on Saturday, August 15, 2026:

- it registered or reused the repo-aligned model
- it restored one active retrieval-approved row
- it generated `112` current historical embeddings
- it left no duplicate competing active approved models

Therefore this blocker was not a Phase 6 code regression, not a schema regression, and not a governance-fabrication case.

## Restoration Commands Used

Phase 5 corpus restoration:

- `python3 -m tools.phase_05_chunking.generate_bulk --load-db`

Phase 6 model and embedding restoration:

- `python3 -m tools.phase_06_search.generate_embeddings`

Result:

- both current live repository procedures succeeded as implemented
- no tooling patch was required
- no schema or migration change was required

## Corpus Integrity Snapshot

### Phase 5

Before restoration:

- current chunk sets: `0`
- current chunks: `0`
- active included governed document versions: `22`
- effective searchable current surface: empty because no current chunk sets existed

After restoration:

- current chunk sets: `22`
- current chunks: `525`
- searchable current chunk sets: `21`
- searchable current chunks: `492`
- active included governed document versions: `22`

### Phase 6

Before restoration:

- historical search units: `112`
- historical embedding model rows: `0`
- active retrieval-approved historical models: `0`
- historical embeddings: `0`

After restoration:

- historical search units: `112`
- historical embedding model rows: `1`
- active retrieval-approved historical models: `1`
- historical embeddings: `112`
- embeddings grouped by model:
  - model `5`: `112`
- active model:
  - `id = 5`
  - provider: `openai`
  - model code: `text-embedding-3-small`
  - model version: `null`
  - dimensions: `1536`
  - config fingerprint: `abc6d49c002b09a49736d1ad1c0913fa`
  - `is_active = true`
  - `is_retrieval_approved = true`
- coverage:
  - eligible units: `112`
  - current embeddings: `112`
  - missing embeddings: `0`
  - stale embeddings: `0`

## Validation Results

Targeted Phase 5 bulk coverage:

- `npx -y supabase@latest test db --local supabase/tests/18_phase_05_bulk_chunking_coverage.sql`
- result: `1 file / 9 tests PASS`

Targeted Phase 8 inquiry waiting DB proof:

- `npx -y supabase@latest test db --local supabase/tests/42_phase_08_inquiry_waiting_follow_up_slice.sql`
- result: `1 file / 7 tests PASS`

Phase 6 rerun:

- `python3 -m pytest tools/phase_06_search/tests -q`
- result: `6 / 6 PASS`

Phase 5 search rerun:

- `python3 -m pytest tools/phase_05_search/tests -q`
- result: `24 / 24 PASS`

Phase 5 chunking rerun:

- `python3 -m pytest tools/phase_05_chunking/tests -q`
- result: `27 / 27 PASS`

Inquiry Waiting focused rerun:

- `python3 -m unittest tools.phase_08_workflow.tests.test_inquiry_waiting tools.phase_08_workflow.tests.test_orchestration_runtime tools.phase_08_workflow.tests.test_test_console_app tools.phase_08_workflow.tests.test_test_console_projection tools.phase_08_workflow.tests.test_test_console_service`
- result: `59 / 59 PASS`

Phase 8 rerun:

- `python3 -m pytest tools/phase_08_workflow/tests -q`
- result: `166 / 166 PASS`

Phase 7 rerun:

- `python3 -m pytest tools/phase_07_reasoning/tests -q`
- result: `127 / 127 PASS`

Full Supabase rerun:

- `npx -y supabase@latest test db --local`
- result: `42 files / 1066 tests PASS`

## Code, Schema, and Tooling Change Assessment

Runtime and retrieval changes:

- Inquiry Waiting runtime semantic changes: `0`
- WorkflowAction semantic changes: `0`
- FollowUp semantic changes: `0`
- approval semantic changes: `0`
- lifecycle semantic changes: `0`
- Phase 4 changes: `0`
- Phase 5 retrieval semantic changes: `0`
- Phase 6 retrieval semantic changes: `0`
- new embedding model substituted: `0`
- historical precedent authority changes: `0`
- test expectations weakened: `0`
- DB assertion counts intentionally reduced: `0`
- provider calls added: `0`
- LLM behavior changes: `0`

Repository change scope:

- code changes: `0`
- schema changes: `0`
- migration changes: `0`
- bootstrap/tooling changes: `0`
- documentation updates: `2`

Documentation updated:

- [PHASE_8_INQUIRY_WAITING_FOLLOW_UP_SLICE_READINESS.md](/Users/serinya/Documents/WNC%20Rental%20Automation/docs/phase-08/PHASE_8_INQUIRY_WAITING_FOLLOW_UP_SLICE_READINESS.md)
- [PHASE_8_INQUIRY_RESPONSE_DRAFTING_BASELINE_UNBLOCK.md](/Users/serinya/Documents/WNC%20Rental%20Automation/docs/phase-08/PHASE_8_INQUIRY_RESPONSE_DRAFTING_BASELINE_UNBLOCK.md)

## Final Validation Matrix

| Validation | Before | After |
| --- | ---: | ---: |
| Inquiry Waiting focused | 59 / 59 | 59 / 59 |
| Phase 8 | 166 / 166 | 166 / 166 |
| Phase 7 | 127 / 127 | 127 / 127 |
| Phase 5 chunking | 27 / 27 | 27 / 27 |
| Phase 5 search | 24 / 24 | 24 / 24 |
| Phase 6 | 5 / 6 + env blocker | 6 / 6 |
| Phase 5 DB bulk coverage | FAIL | 9 / 9 |
| New Phase 8 DB slice | 7 / 7 | 7 / 7 |
| Full Supabase | FAIL | 42 files / 1066 tests PASS |

## Final Verdict

1. Phase 5 blocker root cause:
   post-reset generated chunk corpus was not restored
2. Phase 6 blocker root cause:
   post-reset historical embedding registry row plus embeddings were absent
3. Classification:
   - Phase 5: `CORPUS_NOT_RESTORED`
   - Phase 6: `ENVIRONMENT_STATE_LOSS`
4. Were either caused by the Inquiry Waiting Slice:
   - no
5. Remaining blockers:
   - none observed in the validated local baseline

Strict readiness is now cleared.

Exact readiness marker:

- `READY_FOR_PHASE_8_INQUIRY_RESPONSE_DRAFTING_SLICE`
