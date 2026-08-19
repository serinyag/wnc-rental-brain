# Phase 6 Historical Hybrid Readiness Audit

Date: August 8, 2026

## 1. Historical Corpus And Embedding State

Observed local state after successful reset, historical embedding generation, hybrid evaluation, and full regression:

- active historical cases: `9`
- current searchable historical units: `112`
- active retrieval-approved historical embedding models: `1`
- current embeddings: `112`
- missing embeddings: `0`
- stale embeddings: `0`

Hybrid retrieval preconditions are satisfied in the local environment.

## 2. Hybrid Search Surface

The hybrid search surface is implemented and locally validated:

- helper: `private.historical_hybrid_rrf_score(...)`
- search function: `private.search_historical_case_units_hybrid(...)`
- upstream lexical source: `private.search_historical_case_units(...)`
- upstream semantic source: `private.search_historical_case_units_semantic(...)`
- supported filters aligned across lexical, semantic, and hybrid retrieval

The search surface is both structurally and operationally ready.

## 3. Chosen Ranking Policy

Chosen policy:

- strategy code: `historical_rrf_balanced`
- configuration code: `historical_rrf_balanced_d20`
- formula: `weight * (1 / (k + rank))`
- `k = 20`
- lexical weight `= 1.0`
- semantic weight `= 1.0`
- candidate depth per retriever `= 20`

Decision basis:

- all evaluated strategies tied on aggregate benchmark metrics
- the shallowest effective candidate depth was selected
- the neutral historical strategy preserved the clearest audit posture

## 4. Evaluation

Hybrid evaluation report:

- `docs/phase-06/PHASE_6_HISTORICAL_HYBRID_EVALUATION.md`

Shared benchmark:

- hybrid Hit@1: `19 / 21 = 90.48%`
- hybrid Hit@3: `21 / 21 = 100.00%`

Paraphrase benchmark:

- hybrid Hit@1: `6 / 8 = 75.00%`
- hybrid Hit@3: `8 / 8 = 100.00%`

Comparison to baselines:

- FTS baseline: `17 / 21` Hit@1 and `19 / 21` Hit@3
- semantic baseline: `17 / 21` Hit@1 and `19 / 21` Hit@3
- hybrid improved FTS on `3` shared queries
- hybrid improved semantic on `4` shared queries
- all three tied on `15` shared queries

## 5. Complementarity Audit

The known complementarity checks now resolve as follows:

- `whole venue clearing`: FTS `miss`, semantic `1`, hybrid `3`
- `sensory-sensitive beauty event`: FTS `miss`, semantic `1`, hybrid `1`
- `client operated event`: FTS `3`, semantic `4`, hybrid `3`
- `WNC cleared the venue`: FTS `2`, semantic `4`, hybrid `1`

Interpretation:

- hybrid recovered both of the intended lexical misses into the top-3 window
- hybrid fully matched semantic recovery on `sensory-sensitive beauty event`
- hybrid preserved FTS performance on `client operated event`
- hybrid outperformed both baselines on `WNC cleared the venue`

## 6. Exact-Match Preservation

The exact-match checks remain preserved:

- `300 storage`: hybrid rank `1`
- `fake snow cleanup`: hybrid rank `1`
- `permit compliance`: hybrid rank `1`
- `florals`: hybrid rank `1`
- `overtime charge`: hybrid rank `1`

No exact-match regression was observed on the tracked lexical anchors.

## 7. Remaining Misses

Remaining shared-benchmark miss analysis:

- `whole venue clearing` is the only query not returned at hybrid rank `1`
- the expected case is still recovered at hybrid rank `3`
- failure category remains `FTS miss`, with semantic alone still ranking the expected case at `1`

This does not block readiness for `6.4E`, but it remains a useful known edge case for future ranking-policy work.

## 8. Safety Metadata

The implementation and evaluation confirm that hybrid results preserve:

- `source_layer_role=historical_precedent`
- limited-precedent availability markers
- analyst-inference lesson markers
- `historical_value_only`
- `contamination_risk_level`
- `current_authority_disposition`
- confidentiality metadata
- PI metadata
- provenance metadata
- primary source locator and source-link counts

Live evaluation examples confirmed:

- limited high-risk historical-only results for `300 storage`
- limited high-risk current-authority warnings for `current legal precedent`
- analyst-inference preservation for `Later modelling may need`

## 9. Isolation

Phase 5 remains isolated:

- no Phase 5 search contract changed
- no current-plus-historical fusion introduced
- `private.current_knowledge_chunks` remains unchanged
- the Phase 5 hybrid surface remains available and separate

## 10. Regression Result

Focused hybrid coverage:

- `supabase/tests/33_phase_06_historical_hybrid_retrieval.sql`
- `32` tests
- `PASS`

Full local database regression:

- `33` files
- `937` tests
- `PASS`

## 11. Readiness Decision

Historical hybrid retrieval is implemented, benchmarked, safety-preserving, and locally regression-clean.

Final conclusion:

- `READY_FOR_6_4E_HISTORICAL_RETRIEVAL_INTEGRATION`
