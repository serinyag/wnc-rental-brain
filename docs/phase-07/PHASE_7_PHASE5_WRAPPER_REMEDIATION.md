# Phase 7 Phase 5 Wrapper Remediation

## 1. Original Readiness Failure

The original 7.2D readiness decision was:

- `NOT_READY_FOR_7_2E_PHASE_6_ADAPTER`

Two blockers were recorded:

- `P7-EVAL-021` was scored as a live healthy retrieval miss for current service-boundary guidance.
- the full local pgTAP suite did not pass once the restored live Phase 5 current corpus and Phase 6 historical corpus were present in the database.

At the start of remediation, the full DB failure set was concentrated in `11` existing pgTAP files.

- `7` files had already been proven to rely on stale empty-baseline or global-count assumptions and were narrowed to fixture-owned scope.
- the remaining active rerun still showed `17` failing assertions across `4` files: `16`, `19`, `20`, and `21`.

## 2. P7-EVAL-021 Investigation

Canonical scenario:

- `P7-EVAL-021`
- question: `The client wants to run a whole-venue event themselves. What does WNC handle now, and have we done similar before?`

Phase 7 wrapper plan state:

- `phase_5.query_text` matched the canonical scenario question exactly
- `phase_5.filters.document_code = null`
- `phase_5.filters.category_code = null`
- `phase_5.filters.rental_type_code = null`
- effective wrapper result limit: `5`
- retrieval mode requested: `hybrid`

The canonical reasoning matrix already treats this scenario as a mixed current-plus-precedent request and explicitly supports current service-boundary guidance from:

- `CF-007`
- `SERV-001`
- `TPL-002`
- `TPL-003`

The prior wrapper evaluation had frozen a narrower expectation of `SERV-001 plus proposal guidance`, which omitted `CF-007` even though the matrix and live corpus support it.

## 3. Direct Hybrid vs Wrapper Comparison

Direct Phase 5 hybrid retrieval for `P7-EVAL-021` returned:

1. `CF-007` chunk `208` — `What we ask from the Client` — `0.0526190476190476`
2. `CF-007` chunk `204` — `3. Event, spaces and permitted use` — `0.0504545454545455`
3. `CF-007` chunk `212` — `9. Care of the Venue, branding, liability and insurance` — `0.0484782608695652`
4. `OPS-003` chunk `515` — `ACC-010 — Entire Venue rental` — `0.047`
5. `CF-007` chunk `207` — `What WNC will do` — `0.0466666666666667`
6. `OPS-003` chunk `524` — `COM-004 — Multi-day entire-venue rental`
7. `OPS-002` chunk `437` — `Back office overview`
8. `CF-005` chunk `181`
9. `SERV-001` chunk `543` — `Event Manager`
10. `TPL-002` chunk `599` — `6. Team & Responsibilities`

Phase 7 wrapper retrieval for the same query returned the same top-five chunk order:

1. `CF-007` chunk `208`
2. `CF-007` chunk `204`
3. `CF-007` chunk `212`
4. `OPS-003` chunk `515`
5. `CF-007` chunk `207`

Additional live parity reruns also matched exactly for:

- `P7-EVAL-007`
- `P7-EVAL-009`
- `P7-EVAL-011`

Final parity result:

- `4 / 4 exact chunk-order matches`

## 4. Retrieval Root Cause

Root cause:

- benchmark/query-evaluation mismatch, not wrapper behavior

Proof:

- wrapper query propagation was exact
- wrapper filters matched direct retrieval
- wrapper ranking matched direct retrieval
- direct retrieval itself produced the same `CF-007` / `OPS-003` result family
- the canonical scenario matrix already recognizes `CF-007` as a legitimate current service-boundary source for this scenario

No Phase 5 ranking retune was made.

No Phase 7 wrapper code change was required for `P7-EVAL-021`.

## 5. Resolution / Accepted Limitation

Resolution:

- `P7-EVAL-021` was re-scored as a pass after correcting the accepted current-document set to include `CF-007`, with `SERV-001`, `TPL-002`, and `TPL-003` retained as acceptable supporting alternatives

Accepted limitation status:

- no unresolved wrapper limitation remains for `P7-EVAL-021`

Residual nuance that remains accepted but non-blocking:

- `P7-EVAL-006`, `P7-EVAL-012`, and `P7-EVAL-019` still pass via acceptable alternatives rather than the prompt’s primary expected document family
- lexical fallback quality remains wording-sensitive for long natural-language current-guidance prompts, but the wrapper labels degraded behavior honestly

## 6. Full pgTAP Failure Inventory

Pre-remediation failing files:

- `supabase/tests/16_phase_05_semantic_chunking_foundation.sql`
- `supabase/tests/17_phase_05_chunk_rule_connectivity.sql`
- `supabase/tests/18_phase_05_bulk_chunking_coverage.sql`
- `supabase/tests/19_phase_05_full_text_search_foundation.sql`
- `supabase/tests/20_phase_05_semantic_embedding_foundation.sql`
- `supabase/tests/21_phase_05_hybrid_retrieval_surface.sql`
- `supabase/tests/29_phase_06_active_corpus_activation_audit.sql`
- `supabase/tests/30_phase_06_historical_search_unit_provenance_foundation.sql`
- `supabase/tests/31_phase_06_historical_full_text_search_foundation.sql`
- `supabase/tests/32_phase_06_historical_semantic_retrieval_foundation.sql`
- `supabase/tests/33_phase_06_historical_hybrid_retrieval.sql`

Remaining active failure rerun before the last remediation pass:

- file `16`: failures `1, 5, 7, 10, 15, 16`
- file `19`: failures `1, 3, 4, 10`
- file `20`: failures `5, 6, 7, 9, 10, 11`
- file `21`: failure `4`

## 7. Failure Classification

`STALE_GLOBAL_COUNT_ASSUMPTION`

- `29_phase_06_active_corpus_activation_audit.sql`
- `30_phase_06_historical_search_unit_provenance_foundation.sql`
- `31_phase_06_historical_full_text_search_foundation.sql`
- `32_phase_06_historical_semantic_retrieval_foundation.sql`
- `33_phase_06_historical_hybrid_retrieval.sql`

Why:

- these tests assumed `private.current_knowledge_chunks` should be globally empty after historical work
- that assumption became invalid once the live Phase 5 current corpus was intentionally restored
- the preserved invariant is now: historical work must not change the baseline Phase 5 current-corpus count

`EXPECTED_PRODUCTION_CORPUS_CHANGE`

- `18_phase_05_bulk_chunking_coverage.sql`

Why:

- the original first setup tried to insert a second copy of the live bulk corpus into a database that already contains the seeded production corpus
- the preserved invariant is now audited directly against the seeded live corpus

`FIXTURE_SCOPE_LEAK`

- `17_phase_05_chunk_rule_connectivity.sql`
- `16_phase_05_semantic_chunking_foundation.sql`
- `19_phase_05_full_text_search_foundation.sql`
- `20_phase_05_semantic_embedding_foundation.sql`
- `21_phase_05_hybrid_retrieval_surface.sql`

Why:

- these tests targeted seeded production document codes and global result surfaces instead of fixture-owned rows
- once live corpus rows existed, uniqueness constraints, shared search surfaces, and shared embedding-model state caused false failures

`OTHER`

- none

`GENUINE_REGRESSION`

- none

## 8. Test Fixture Changes

`supabase/tests/17_phase_05_chunk_rule_connectivity.sql`

- old behavior: selectors matched live seeded chunks plus fixture chunks because they scoped only by document code and section heading
- new behavior: selectors also require `chunking_strategy_version = 'test_chunk_rule_v1'`
- preserved invariant: chunk-to-rule relationships must validate against the fixture-owned chunk generation only

`supabase/tests/18_phase_05_bulk_chunking_coverage.sql`

- old behavior: first setup attempted to duplicate the live production bulk corpus
- new behavior: the test audits the seeded live corpus directly
- preserved invariant: the repository still proves bulk chunking coverage against the real governed current corpus

`supabase/tests/29` through `33`

- old behavior: each file asserted that the global current-corpus count should be `0`
- new behavior: each file captures the current-corpus baseline in a temp table and reasserts that historical work does not change that baseline
- preserved invariant: Phase 6 work must not mutate the active Phase 5 current corpus

`supabase/tests/16_phase_05_semantic_chunking_foundation.sql`

- old behavior: current-set, processing-row, and provenance assertions targeted seeded production documents such as `TPL-006` and `TPL-007`
- new behavior: the file creates fixture-owned governed documents `SCF-001` through `SCF-004` and runs all chunking and provenance constraints against them
- preserved invariant: processing status, current-chunk-set uniqueness, required extraction sources, excluded source rejection, per-chunk constraints, and provenance constraints all still hold

`supabase/tests/19_phase_05_full_text_search_foundation.sql`

- old behavior: FTS fixtures were layered onto seeded production documents and global `current_knowledge_chunks`
- new behavior: the file creates fixture-owned governed documents `FTSF-001` through `FTSF-006`, scopes live-surface counts to the fixture category, and uses fixture filters for search assertions
- preserved invariant: only current, active, effective, included chunk sets are searchable; deferred, draft, future, and superseded rows stay excluded; document/category/rental filters still work; provenance remains resolved

`supabase/tests/20_phase_05_semantic_embedding_foundation.sql`

- old behavior: semantic fixtures targeted seeded production docs, global embedding-input counts, and a second active retrieval-approved model
- new behavior: the file creates fixture-owned documents `SEMFX-001` through `SEMFX-003`, uses an explicit non-approved fixture model, scopes counts to fixture rows, and passes the model ID explicitly into semantic search
- preserved invariant: embedding model constraints, embedding uniqueness, dimensional validation, deferred exclusion, semantic ranking, document/category/rental filters, and provenance all still hold

`supabase/tests/21_phase_05_hybrid_retrieval_surface.sql`

- old behavior: hybrid fixtures targeted seeded production docs, a second active retrieval-approved model, and unrestricted FTS surfaces
- new behavior: the file creates fixture-owned documents `HYBFX-001` through `HYBFX-006`, uses an explicit non-approved fixture model, restores policy-sensitive categories where needed, and isolates hybrid probes with fixture-only lexical phrases and scoped filters
- preserved invariant: RRF scoring, policy modifiers, FTS-only degradation, semantic-only fusion, deterministic ordering, document/category/rental filters, deferred exclusion, and provenance remain covered

## 9. Production Corpus Integrity

Confirmed:

- no production Phase 5 document, chunk, embedding, or metadata row was deleted to satisfy tests
- no production Phase 6 historical row was deleted to satisfy tests
- the live seeded corpora remained present throughout remediation
- the final regression suite now passes with the live repository state intact

## 10. Final Phase 5 Wrapper Evaluation

Healthy live rerun:

- scenarios: `12`
- passes counting accepted alternatives: `12 / 12`
- required-document Hit@1: `7 / 12` (`58.3%`)
- required-document Hit@3: `11 / 12` (`91.7%`)
- required-document Hit@5: `11 / 12` (`91.7%`)
- source-role correctness: `12 / 12`
- retrieval-mode correctness: `12 / 12`
- confidentiality completeness: `12 / 12`
- PI completeness: `12 / 12`
- provenance completeness: `12 / 12`
- Phase 4 relationship payload completeness: `12 / 12`

`P7-EVAL-021` final outcome:

- direct hybrid top ten and wrapper top five prove parity
- `CF-007` is now treated as a valid current service-boundary hit for the scenario
- the earlier fail was removed as a benchmark-integrity defect

Fallback evaluation:

- forced model-resolution failure on `external caterer requirements` returned live `fts_fallback` with `SERV-004`, `GOV-001`, `SERV-003`, `TPL-006`, `SERV-004`
- forced model-resolution failure on the full `P7-EVAL-007` natural-language question returned honest `no_results` with explicit `fallback_reason = embedding_model_resolution_failed`
- injected query-embedding failure still returns `fts_fallback`
- injected dual hybrid-plus-FTS outage still returns `unavailable`

Healthy parity rerun:

- `P7-EVAL-007`, `P7-EVAL-009`, `P7-EVAL-011`, and `P7-EVAL-021` each matched direct hybrid exactly at the chunk-order level

## 11. Final Regression Results

- Phase 5 wrapper unit tests: `10 / 10`
- full Phase 7 regression (`contracts`, `planner`, `phase4_adapter`, `phase5_wrapper`): `50 / 50`
- combined Phase 5/6 Python regression: `80 / 80`
- full local pgTAP regression: `33` files, `937` assertions, `PASS`

Live corpus/embedding state at close:

- current Phase 5 chunks: `492`
- eligible current embedding inputs: `492`
- current approved embeddings: `492`
- missing approved embeddings: `0`

## 12. Remaining Limitations

Accepted non-blocking limitations:

- `P7-EVAL-006`, `P7-EVAL-012`, and `P7-EVAL-019` still rely on accepted alternatives rather than the scenario prompt’s primary expected document family
- lexical fallback quality is wording-sensitive for long natural-language prompts, even though fallback contract labeling is correct and honest

No blocking limitations remain for 7.2D.

## 13. Readiness Decision

Decision:

- `READY_FOR_7_2E_PHASE_6_ADAPTER`

Reason:

- the wrapper contract remained stable
- `P7-EVAL-021` root cause was proven and resolved at the benchmark layer
- no genuine implementation regression was found
- the full local DB suite now passes against the live seeded repository state
- no Phase 6 adapter, context assembly, or cross-layer orchestration was created during remediation
