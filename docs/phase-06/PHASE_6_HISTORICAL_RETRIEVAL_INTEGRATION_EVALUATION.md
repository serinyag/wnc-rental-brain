# Phase 6 Historical Retrieval Integration Evaluation

Date: August 8, 2026

## 1. Integration Contract

- integration entry point: `tools.phase_06_search.historical_retrieval.retrieve_historical_precedents(...)`
- ordinary callers supply natural-language query text plus optional supported filters.
- the integration contract generates embeddings internally, validates historical embedding state, and returns retrieval results only.

## 2. Healthy-State Corpus

- historical units: `112`
- current embeddings: `112`
- missing embeddings: `0`
- stale embeddings: `0`

## 3. Healthy Hybrid Benchmark

- shared Hit@1: `19/21 = 90.48%`
- shared Hit@3: `21/21 = 100.00%`
- paraphrase Hit@1: `6/8 = 75.00%`
- paraphrase Hit@3: `8/8 = 100.00%`
- these match the validated 6.4D direct-hybrid aggregate results.

## 4. Rank-Parity Check

- integrated retrieval matched direct 6.4D hybrid ordering across the full shared benchmark: `yes`
- frozen strategy code: `historical_rrf_balanced`
- frozen configuration code: `historical_rrf_balanced_d20`

## 5. Known Weak Queries

- `whole venue clearing`: integrated rank `3`; top result `HC-006` / `lesson` / mode `hybrid`.
- `sensory-sensitive beauty event`: integrated rank `1`; top result `HC-004` / `decision` / mode `hybrid`.
- `client operated event`: integrated rank `3`; top result `HC-004` / `responsibility` / mode `hybrid`.
- `WNC cleared the venue`: integrated rank `1`; top result `HC-001` / `decision` / mode `hybrid`.

## 6. High-Risk Query Review

- `300 storage`: top result `HC-003` / `decision` keeps `source_layer_role=historical_precedent`, `precedent_availability=limited`, `historical_value_only=True`, `contamination_risk_level=high`, `current_authority_disposition=potential_conflict_with_current_knowledge`.
- `florals`: top result `HC-003` / `decision` keeps `source_layer_role=historical_precedent`, `precedent_availability=limited`, `historical_value_only=True`, `contamination_risk_level=high`, `current_authority_disposition=current_status_unknown`.
- `discount exposure gifts`: top result `HC-004` / `decision` keeps `source_layer_role=historical_precedent`, `precedent_availability=limited`, `historical_value_only=True`, `contamination_risk_level=high`, `current_authority_disposition=current_status_unknown`.
- `current legal precedent`: top result `HC-009` / `decision` keeps `source_layer_role=historical_precedent`, `precedent_availability=limited`, `historical_value_only=True`, `contamination_risk_level=high`, `current_authority_disposition=potential_conflict_with_current_knowledge`.

## 7. Fallback Evaluation

- simulated query-embedding failure: actual mode `fts_fallback`, fallback reason `query_embedding_failed`, result count `3`.
- simulated incomplete semantic corpus: actual mode `fts_fallback`, fallback reason `historical_embedding_corpus_incomplete`, result count `5`.
- both fallback paths preserved historical source role, availability, high-risk markers, confidentiality, and provenance fields.

## 8. Failure Handling

- simulated lexical-fallback failure raises explicit error instead of fake success: `fts_fallback_failed: Historical lexical fallback failed before any safe retrieval result could be returned.`
- invalid query and invalid filter values are rejected before OpenAI embedding calls.

## 9. Phase 5 Isolation

- the Phase 6 integration path calls only Phase 6 historical embedding state plus Phase 6 historical FTS/hybrid retrieval surfaces.
- no Phase 5 current-knowledge retrieval function or current-knowledge chunk surface is queried.
