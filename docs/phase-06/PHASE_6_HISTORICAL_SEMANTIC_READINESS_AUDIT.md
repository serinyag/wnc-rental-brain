# Phase 6 Historical Semantic Readiness Audit

Date: August 7, 2026

## 1. Embedding Completeness

Expected readiness target:

- eligible current historical units: `112`
- current embeddings: `112`
- missing: `0`
- stale: `0`

Observed local state after `npx supabase db reset` plus the blocked live backfill attempt:
Observed local state after `npx supabase db reset`, successful historical backfill, and live semantic evaluation:

- eligible current historical units: `112`
- active historical embedding models: `1`
- current embeddings: `112`
- missing: `0`
- stale: `0`

## 2. Semantic Search Surface

The semantic search surface itself is implemented and validated locally:

- corpus surface: `private.current_historical_case_search_units`
- semantic-input surface: `private.current_historical_case_embedding_inputs`
- search function: `private.search_historical_case_units_semantic(...)`
- filters aligned to historical FTS
- historical safety metadata preserved in the function contract

The search surface is both structurally and operationally ready in the local environment.

## 3. Evaluation

Shared semantic benchmark:

- Hit@1: `17 / 21 = 80.95%`
- Hit@3: `19 / 21 = 90.48%`

Semantic paraphrase benchmark:

- Hit@1: `6 / 8 = 75.00%`
- Hit@3: `8 / 8 = 100.00%`

FTS comparison:

- shared benchmark ties FTS exactly on aggregate Hit@1 and Hit@3
- semantic search performs better on `2` shared queries
- FTS performs better on `4` shared queries
- `15` shared queries are aggregate ties

Current lexical baseline remains:

- FTS Hit@1: `17 / 21 = 80.95%`
- FTS Hit@3: `19 / 21 = 90.48%`

## 4. Lexical Miss Recovery

The intended semantic recovery checks remain:

- `whole venue clearing`
- `sensory-sensitive beauty event`
- `client operated event`
- `WNC cleared the venue`

Audit result:

- `whole venue clearing`: semantic improved from FTS `miss` to semantic rank `1`
- `sensory-sensitive beauty event`: semantic improved from FTS `miss` to semantic rank `1`
- `client operated event`: FTS remained better with FTS rank `3` vs semantic rank `4`
- `WNC cleared the venue`: FTS remained better with FTS rank `2` vs semantic rank `4`

## 5. Safety Metadata

The implementation and pgTAP coverage confirm that semantic results preserve:

- `source_layer_role`
- limited availability
- analyst inference
- historical-value-only flags
- contamination risk
- current-authority disposition
- confidentiality
- provenance

Live semantic examples confirm the metadata survives retrieval, including limited precedent, analyst-inference lessons, historical-value-only content, contamination risk, authority disposition, confidentiality, and source provenance.

## 6. Isolation

Phase 5 remains unchanged.

Validated locally:

- `private.current_knowledge_chunks` unchanged
- Phase 5 semantic search function remains present
- full database suite passes with the new Phase 6 semantic objects added

Regression result:

- `32` files
- `905` tests
- `PASS`

## 7. Readiness Decision

Semantic retrieval is implemented, activated, and benchmarked in this local environment.

Final conclusion:

- `READY_FOR_6_4D_HISTORICAL_HYBRID_RETRIEVAL`
