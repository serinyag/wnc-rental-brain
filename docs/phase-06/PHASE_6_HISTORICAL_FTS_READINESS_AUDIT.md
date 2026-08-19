# Phase 6 Historical FTS Readiness Audit

Date: August 7, 2026

## 1. Search Surface

Historical lexical search now operates over the current governed Phase 6 historical search-unit surface only.

Production searchable corpus:

- active historical cases: `9`
- active governed historical case versions: `9`
- searchable current historical units: `112`
- narratives: `9`
- responsibilities: `35`
- decisions: `25`
- lessons: `43`
- limited precedents preserved in-surface: `HC-003`, `HC-004`, `HC-008`, `HC-009`

Historical lexical retrieval does not search:

- Phase 5 knowledge chunks
- Phase 4 rule tables
- raw source artifacts
- inactive historical versions

## 2. Index Completeness

All eligible current historical units are FTS-ready.

Implemented FTS representation:

- generated stored `tsvector` on `private.historical_case_search_units`
- GIN index: `historical_case_search_units_search_vector_gin_idx`

Audit result:

- FTS-ready eligible units: `112 / 112`

Because the vector is generated on the `6.4A` derived table, the historical rebuild flow remains the single deterministic materialization path.

## 3. Query Safety

The historical lexical function is:

- private
- deterministic
- server-side
- free of dynamic SQL

Function behavior:

- parser: `websearch_to_tsquery`
- configuration: `english`
- empty/null/whitespace input returns zero rows
- invalid filter enums raise `22023`
- result limit is clamped
- ordering is deterministic

Private posture verified:

- direct execution revoked from `anon`
- direct execution revoked from `authenticated`
- direct execution revoked from `service_role`

## 4. Retrieval Evaluation

Deterministic evaluation artifact:

- `docs/phase-06/PHASE_6_HISTORICAL_FTS_EVALUATION.md`

Evaluation set:

- query count: `21`
- corpus: `9` cases / `112` units

Aggregate metrics:

- Hit@1: `17 / 21 = 80.95%`
- Hit@3: `19 / 21 = 90.48%`
- MRR: `0.8492`

Major lexical misses or weak cases:

- `whole venue clearing`
  - miss
  - current lexical surface prefers `HC-006` “whole-venue concept” language over `HC-001` white-box / clearing phrasing
- `sensory-sensitive beauty event`
  - miss
  - vocabulary mismatch against the corpus wording `scent-sensitive`
- `client operated event`
  - expected case appears at rank `3`
  - broad query with multiple legitimate client-operated precedents
- `WNC cleared the venue`
  - expected case appears at rank `2`
  - ranking tie against another WNC clearing responsibility precedent

These are appropriate lexical-baseline findings, not blockers for `6.4B`.

## 5. Safety Metadata

Historical lexical results preserve the metadata required for safe historical interpretation:

- historical source role
- limited status
- analyst inference
- historical-value-only flags
- contamination risk
- current-authority disposition
- confidentiality
- provenance

Verified examples:

- `300 storage`
  - top result: `HC-003` decision
  - `precedent_availability = limited`
  - `historical_value_only = true`
  - contamination `high`
  - authority disposition `potential_conflict_with_current_knowledge`
  - confidentiality `restricted`
  - primary locator preserved
- `current legal precedent`
  - top result: `HC-009` decision
  - still explicitly historical
  - still limited
  - still high risk
  - primary locator preserved
- `Later modelling may need`
  - top result: `HC-009` lesson
  - `lesson_kind = analyst_inference`
  - authority disposition `no_current_rule_implication`

Limited precedents remain searchable by default and visibly typed.

Analyst-inference lessons remain searchable and visibly typed.

Historical-value-only content remains searchable and visibly typed.

## 6. Phase 5 Isolation

Phase 5 current retrieval remains unchanged.

Confirmed:

- `private.current_knowledge_chunks` unchanged and still `0` rows in the current local reset baseline
- Phase 5 lexical functions unchanged
- Phase 5 semantic functions unchanged
- hybrid/RRF logic unchanged

Historical FTS remains independently testable and independent from the current-knowledge retrieval pool.

## 7. Readiness Decision

The deterministic historical lexical retrieval baseline is complete and suitable for semantic comparison in the next stage.

Final conclusion:

- `READY_FOR_6_4C_HISTORICAL_SEMANTIC_RETRIEVAL`
