# Phase 6 Historical Retrieval Integration Readiness Audit

Date: August 8, 2026

## 1. Production Retrieval State

Observed local state after integration implementation and evaluation:

- historical units: `112`
- current embeddings: `112`
- missing embeddings: `0`
- stale embeddings: `0`
- frozen strategy code: `historical_rrf_balanced`
- frozen configuration code: `historical_rrf_balanced_d20`

The validated historical hybrid baseline remains intact.

## 2. Stable Integration Contract

One operational entry point now exists:

- `tools.phase_06_search.historical_retrieval.retrieve_historical_precedents(...)`

Ordinary callers provide natural-language query text plus optional validated filters.

The contract:

- resolves the approved historical embedding model
- validates current historical embedding state
- generates the query embedding internally
- runs healthy hybrid retrieval when eligible
- runs explicit lexical fallback when configured healthy hybrid cannot run safely
- returns structured retrieval results only

## 3. Hybrid Parity

Healthy integrated retrieval preserves the validated 6.4D performance and ordering:

- shared Hit@1: `19 / 21 = 90.48%`
- shared Hit@3: `21 / 21 = 100.00%`
- paraphrase Hit@1: `6 / 8 = 75.00%`
- paraphrase Hit@3: `8 / 8 = 100.00%`
- direct 6.4D hybrid ordering parity across the full shared benchmark: `yes`

No integration-induced ranking regression was observed.

## 4. Safety Metadata

The integration contract preserves:

- `source_layer_role=historical_precedent`
- limited-precedent status
- analyst-inference status
- `historical_value_only`
- `contamination_risk_level`
- `current_authority_disposition`
- confidentiality metadata
- PI metadata
- provenance/source locator metadata

High-risk integrated query review confirmed this on:

- `300 storage`
- `florals`
- `discount exposure gifts`
- `current legal precedent`

## 5. Fallback Behavior

Fallback is:

- explicit
- deterministic
- safety-preserving

Implemented mode behavior:

- healthy request target: `hybrid`
- degraded mode: `fts_fallback`

Validated fallback causes:

- query embedding failure
- incomplete historical semantic corpus

Validated fallback labels:

- `retrieval_mode_requested`
- `retrieval_mode_used`
- `fallback_used`
- `fallback_reason`

Fallback results preserve historical safety metadata rather than returning stripped-down rows.

## 6. Error Behavior

Failures are not silently converted into incorrect healthy-hybrid success.

Validated behavior:

- invalid query rejected before embedding call
- invalid filters rejected before embedding call
- lexical fallback failure raises explicit `HistoricalRetrievalError`
- database / hybrid failures do not produce fake empty success

## 7. Phase 5 Isolation

No current knowledge is retrieved by the 6.4E path.

Confirmed:

- no Phase 5 FTS search call
- no Phase 5 semantic search call
- no Phase 5 hybrid search call
- no `private.current_knowledge_chunks` query

The authority boundary remains intact.

## 8. Remaining Limitations

Accepted limitations:

- `whole venue clearing` remains hybrid rank `3`
- healthy hybrid still depends on external query embedding availability
- historical retrieval alone does not answer current-policy questions
- limited precedent still requires downstream interpretation safeguards
- lexical fallback preserves safety metadata but does not preserve hybrid ranking signals

## 9. Readiness Decision

`READY_FOR_PHASE_6_CLOSURE`
