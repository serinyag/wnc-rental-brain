# Phase 7 Downstream Dependency & Readiness Audit

Date: August 8, 2026

## 1. Executive Summary

Repository readiness for Phase 7 downstream audit is strong.

The most important findings are:

- Phase 4 already exposes real programmatic rule-access functions, but only as domain-specific APIs rather than one generic deterministic-rule interface.
- Phase 5 has a stable private retrieval substrate and stable Python search tooling, but it does not yet have a single integration wrapper equivalent to Phase 6.
- Phase 6 does have a stable downstream integration contract at `tools.phase_06_search.historical_retrieval.retrieve_historical_precedents(...)`.
- authority ordering is structurally preserved: Phase 4 deterministic truth, then Phase 5 current governed knowledge, then Phase 6 historical precedent.
- the largest downstream gaps are adapter-level, not data-foundation blockers:
  - no generic Phase 4 adapter
  - no single Phase 5 integration wrapper
  - no cross-layer source-role normalization
  - no query-routing/domain-resolution layer
  - no combined confidentiality merge contract

No repository contradiction was found that blocks Task `7.0B`.

Readiness decision:

- `READY_FOR_7_0B`

## 2. Phase 4 Downstream Surface

### 2.1 What currently exists

Phase 4 deterministic truth is implemented through:

- `public.rule_catalogue`
- domain-specific typed rule tables
- `public.current_*` views
- `api.*` query/evaluation functions

Deterministic rule identity layers:

- stable logical identity: `rule_code`
- exact version identity: `(rule_code, rule_version)` and `rule_catalogue.id`

Programmatic access is domain-specific, not generic.

Current callable Phase 4 functions found:

- `api.get_booking_fee_rule(...)`
- `api.get_payment_rules(...)`
- `api.get_expedited_surcharge_rule(...)`
- `api.get_cancellation_rules(...)`
- `api.get_capacity_rule(...)`
- `api.evaluate_capacity(...)`
- `api.get_space_access_rule(...)`
- `api.evaluate_space_access(...)`
- `api.get_operational_requirements(...)`
- `api.get_catering_supplier_rules(...)`
- `api.get_technical_equipment_inventory(...)`
- `api.evaluate_technical_equipment_quantity(...)`
- `api.get_technical_capability(...)`
- `api.evaluate_technical_requirement(...)`
- `api.get_service_rules(...)`
- `api.get_facilitator_requirements(...)`

Public current views found:

- `public.current_booking_fee_rules`
- `public.current_payment_rules`
- `public.current_expedited_surcharge_rules`
- `public.current_cancellation_rules`
- `public.current_capacity_rules`
- `public.current_space_access_rules`
- `public.current_operational_requirements`
- `public.current_catering_supplier_rules`
- `public.current_technical_equipment_inventory`
- `public.current_technical_capability_rules`
- `public.current_service_rules`
- `public.current_facilitator_requirement_rules`

### 2.2 Current rule resolution

Current resolution is not handled by one repository-wide helper.

Instead, each domain function resolves current applicability by querying:

- the domain table
- `public.rule_catalogue`
- `effective_from` / `effective_until`
- the function `as_of_date` parameter, defaulting to `current_date`

Important nuance:

- Phase 4 current resolution is not simply `status = 'active'`
- functions commonly admit `status in ('active', 'superseded', 'retired')` as long as the effective-date window still matches
- therefore “current applicable rule version” is date-window-driven, not just a single active-row lookup

### 2.3 Result shape and provenance

Phase 4 function results reliably expose:

- `rule_id`
- `rule_code`
- `rule_version`
- `status`
- `effective_from`
- `effective_until`
- `plain_language_explanation`
- domain-specific typed fields
- provenance as `primary_source_codes`, `governance_source_codes`, and `supporting_source_codes`

Phase 4 function results do not generally expose:

- `source_registry.id`
- `relative_source_path`
- `citation_locator`
- a machine-readable source-layer field such as `deterministic_rule`
- one normalized shape shared across all domains

Deeper provenance exists in raw tables:

- `public.rule_catalogue`
- `public.rule_source_links`
- `public.source_registry`

But a downstream caller must join those manually if it needs locator-level provenance beyond source-code arrays.

### 2.4 Usability from Phase 7

Phase 4 is reusable, but not through one stable generic interface.

Best audit classification:

- domain APIs: `REUSE_VIA_ADAPTER`
- raw `public.current_*` views: `REFERENCE_ONLY`
- raw rule tables: `REFERENCE_ONLY`

Reason:

- the data is strong and typed
- the callable functions are real and stable
- but the orchestrator would need domain knowledge to decide which function to call and how to interpret each result shape

### 2.5 Main downstream gaps

Phase 4 currently lacks:

- one generic deterministic-rule adapter
- one common response schema across domains
- one machine-readable source-role field
- one generic natural-language-to-domain mapping layer

## 3. Phase 5 Downstream Surface

### 3.1 What currently exists

Phase 5 current governed knowledge retrieval exists as:

- private FTS surface: `private.search_knowledge_chunks(...)`
- private semantic surface: `private.search_knowledge_chunks_semantic(...)`
- private hybrid surface: `private.search_knowledge_chunks_hybrid(...)`
- Python hybrid client helper: `tools.phase_05_search.search_hybrid.run_hybrid_search(...)`
- CLI wrapper: `python3 -m tools.phase_05_search.search_hybrid`

Current retrieval corpus surfaces:

- `private.current_knowledge_chunks`
- `private.current_knowledge_chunk_embedding_inputs`

### 3.2 Stable interface finding

There is no single stable Phase 5 integration entry point analogous to the Phase 6 contract.

The closest reusable pieces are:

- SQL: `private.search_knowledge_chunks_hybrid(...)`
- Python: `tools.phase_05_search.search_hybrid.run_hybrid_search(...)`

But these are not equivalent to Phase 6 integration because they require the caller to manage:

- query normalization context
- embedding-model lookup
- query embedding generation
- fallback choice
- top-level result labeling

Best audit classification:

- `private.search_knowledge_chunks_hybrid(...)`: `REUSE_VIA_ADAPTER`
- `tools.phase_05_search.search_hybrid.run_hybrid_search(...)`: `REUSE_VIA_ADAPTER`
- CLI module `tools.phase_05_search.search_hybrid`: `REFERENCE_ONLY`

### 3.3 Search modes and frozen strategy

Implemented retrieval modes:

- FTS
- semantic
- hybrid

Frozen production hybrid strategy:

- policy: `rrf_policy_weighted`
- RRF `k = 20`
- candidate depth per substrate: `10`

Hybrid behavior:

- if a query embedding is omitted, `private.search_knowledge_chunks_hybrid(...)` degrades to FTS-only ranking while preserving category modifiers
- however that degradation is not labeled with a top-level fallback contract

### 3.4 Filters

Supported Phase 5 filters found on the private search surfaces:

- `document_code`
- `category_code`
- `rental_type_code`

No broader integration-level filter contract exists today.

### 3.5 Result contract

Phase 5 hybrid results expose:

- chunk identity
- `document_code`
- `document_title`
- `document_version_id`
- `document_version_number`
- `chunk_set_id`
- `chunk_ordinal`
- `section_heading`
- `heading_path`
- `question_label`
- `body_text`
- `content_hash`
- `primary_chunk_source_id`
- `primary_document_version_source_object_id`
- `primary_source_locator`
- `primary_category_code`
- `authority_classification`
- `rental_type_codes`
- semantic model metadata
- `came_from_fts`
- `came_from_semantic`
- `fts_rank`
- `semantic_rank`
- `fts_relevance_score`
- `semantic_similarity_score`
- `semantic_cosine_distance`
- `rrf_k`
- `rrf_fts_score`
- `rrf_semantic_score`
- `rrf_base_score`
- `policy_modifier`
- `final_score`

Phase 5 retrieval results do not expose:

- explicit `source_layer_role = current_governed_knowledge`
- confidentiality level
- PI status
- chunk-rule relationship codes
- document-rule relationship codes
- top-level fallback labeling

### 3.6 Security and authority metadata

Security posture:

- all retrieval surfaces remain private
- no public RPC wrapper exists
- no `anon`, `authenticated`, or `service_role` execution grants exist on the private search functions

Authority metadata:

- `authority_classification` is explicit in results
- current-governed-knowledge role is implicit from the called surface, not explicit in returned rows

### 3.7 Usability from Phase 7

Phase 5 is a good retrieval dependency, but not yet a Phase 7-ready integration contract.

Main downstream limitations:

- no single stable entry point
- no explicit fallback labeling
- no explicit source-role field
- no confidentiality/PI fields in the result contract
- rule relationships exist in schema, but not in retrieval rows

## 4. Phase 6 Downstream Surface

### 4.1 Stable integration contract

Stable downstream entry point:

- `tools.phase_06_search.historical_retrieval.retrieve_historical_precedents(...)`

Operational CLI wrapper:

- `python3 -m tools.phase_06_search.historical_retrieval --json "<query>"`

Best audit classification:

- `REUSE_DIRECTLY`

### 4.2 Input contract

Inputs:

- `query_text`
- `result_limit`
- optional `case_code`
- optional `unit_type`
- optional `precedent_availability`
- optional `precedent_type`
- optional `lesson_kind`
- optional `historical_value_only`
- optional `contamination_risk_level`

### 4.3 Retrieval modes and fallback

Healthy mode:

- `hybrid`

Explicit degraded mode:

- `fts_fallback`

Top-level mode/fallback metadata:

- `retrieval_mode_requested`
- `retrieval_mode_used`
- `fallback_used`
- `fallback_reason`

Validated fallback reasons:

- `embedding_model_resolution_failed`
- `embedding_configuration_missing`
- `query_embedding_failed`
- `historical_embedding_corpus_incomplete`

### 4.4 Embedding behavior and preflight

The integration contract:

- resolves the active historical embedding model
- checks historical embedding coverage
- rejects empty queries
- validates filters before OpenAI embedding calls
- generates query embeddings internally
- uses the frozen historical hybrid surface without reordering results in application code

Healthy hybrid requires:

- one active retrieval-approved embedding model
- eligible count equals current embedding count
- `missing = 0`
- `stale = 0`

### 4.5 Result contract

Top-level response exposes:

- query text
- retrieval mode labels
- fallback labels
- frozen strategy/configuration codes
- result limits
- embedding model metadata
- embedding-state metadata
- timing
- result count
- results

Per-result rows expose:

- `source_layer_role`
- `search_unit_id`
- `source_key`
- `unit_type`
- `search_text`
- `historical_case_id`
- `historical_case_version_id`
- `case_code`
- `case_title`
- `precedent_type`
- `precedent_availability`
- `case_evidence_strength`
- `unit_evidence_strength`
- `actor_type`
- `lesson_kind`
- `historical_value_only`
- `contamination_risk_level`
- `current_authority_disposition`
- case-level historical-value summary
- confidentiality metadata
- PI metadata
- primary source identity
- primary source locator
- source-link count
- statement identifiers
- hybrid score/rank metadata on healthy hybrid results

### 4.6 Safety metadata

Phase 6 already provides the strongest machine-readable downstream safety envelope in the repository:

- `source_layer_role = historical_precedent`
- `historical_value_only`
- `contamination_risk_level`
- `current_authority_disposition`
- `precedent_availability`
- analyst-inference visibility through `lesson_kind`
- confidentiality and PI metadata

Important controlled `current_authority_disposition` values found:

- `no_current_rule_implication`
- `check_phase_4`
- `check_phase_5`
- `check_phase_4_and_5`
- `potential_conflict_with_current_knowledge`
- `current_status_unknown`

### 4.7 Usability from Phase 7

Phase 6 is suitable as a frozen downstream dependency for later orchestration.

Constraint:

- Phase 7 must preserve the meaning of historical safety metadata rather than flattening it into generic relevance output

## 5. Cross-Layer Contract Comparison

| Field / Concept | Phase 4 | Phase 5 | Phase 6 |
| --- | --- | --- | --- |
| source layer | implicit by API surface only | implicit by retrieval surface only | explicit `source_layer_role` |
| stable identity | `rule_code` | `document_code`, `chunk_id` | `case_code`, `source_key`, `search_unit_id` |
| exact version | `rule_version`, `rule_id` | `document_version_id`, `document_version_number` | `historical_case_version_id` |
| text content | `plain_language_explanation` plus typed columns | `body_text` plus heading metadata | `search_text` plus unit/case metadata |
| structured value | yes, typed domain columns | no deterministic value contract | no deterministic value contract |
| relevance score | no | yes | yes |
| authority classification | implicit deterministic truth by interface | explicit `authority_classification` | explicit historical role plus safety markers |
| confidentiality | none in result contract | stored underneath, not returned | explicit in results |
| PI | none in result contract | stored underneath, not returned | explicit in results |
| provenance | source-code arrays only in API results | source ids and locator in retrieval rows | case/version/source ids and locator in retrieval rows |
| current/historical status | current applicability by view/function | current corpus only, implicit | explicit historical precedent metadata |
| fallback mode | domain-specific uncertainty statuses, not retrieval fallback | no labeled integration fallback contract | explicit `hybrid` vs `fts_fallback` |

Directly compatible concepts:

- stable identity exists in all three layers
- exact version identity exists in all three layers
- provenance exists in all three layers, though at different depth

Intentionally different concepts:

- Phase 4 structured value semantics must not be normalized into free-text retrieval semantics
- Phase 5 authority classification is not the same concept as Phase 6 precedent safety metadata
- Phase 6 historical safety markers are not equivalent to Phase 4 applicability or Phase 5 authority class

Future adapter needs:

- explicit cross-layer source-role normalization
- confidentiality normalization
- provenance normalization
- uncertainty/fallback normalization

## 6. Reuse Matrix

| Existing Component | Phase | Current Purpose | Potential Phase 7 Use | Reuse Status | Constraints |
| --- | --- | --- | --- | --- | --- |
| `api.*` deterministic rule functions | 4 | domain-specific deterministic rule access | current-truth adapter inputs | `REUSE_VIA_ADAPTER` | heterogeneous signatures and outputs |
| `public.current_*` rule views | 4 | read-only current rule snapshots | validation/reference | `REFERENCE_ONLY` | not a generic reasoning contract |
| `public.rule_catalogue` + typed rule tables | 4 | canonical rule storage | provenance/reference backing | `REFERENCE_ONLY` | direct-table use would couple Phase 7 to schema details |
| `private.search_knowledge_chunks_hybrid(...)` | 5 | private current-knowledge hybrid retrieval | current-guidance retrieval adapter | `REUSE_VIA_ADAPTER` | caller must manage embeddings and fallback semantics |
| `tools.phase_05_search.search_hybrid.run_hybrid_search(...)` | 5 | Python access to private hybrid retrieval | possible Phase 5 adapter core | `REUSE_VIA_ADAPTER` | no top-level integration contract |
| `tools.phase_06_search.historical_retrieval.retrieve_historical_precedents(...)` | 6 | stable historical retrieval integration | direct historical dependency | `REUSE_DIRECTLY` | preserve safety metadata exactly |
| `tools.phase_05_search.semantic_common.load_env_value(...)` | 5 | shared env loading | model/config bootstrapping | `REUSE_DIRECTLY` | only env loading, not answer generation |
| `tools.phase_05_search.semantic_common.OpenAIEmbeddingsClient` | 5 | embedding API client | later model utility base | `REUSE_VIA_ADAPTER` | embedding-only, no chat/completions client |
| `EmbeddingModelConfig` | 5 | model config container | future model config reuse | `REUSE_VIA_ADAPTER` | designed for embeddings, not chat models |
| `tools.phase_06_search.retrieval_common` | 6 | historical retrieval config/preflight | direct Phase 6 helper reuse | `REUSE_DIRECTLY` | Phase 6-specific semantics |
| `run_supabase_query(...)` / `sql_text(...)` | shared tooling | local SQL execution utilities | internal adapter tooling | `REUSE_DIRECTLY` | local/server-side only |
| `evaluate_*` retrieval scripts | 5/6 | benchmark/report generation | scenario-matrix and regression harness patterns | `REFERENCE_ONLY` | not production interfaces |
| retrieval fixtures/assertion patterns in tests/evaluators | 5/6 | deterministic evaluation | benchmark scaffolding for 7.0B | `REUSE_DIRECTLY` | adapt to reasoning-specific metrics later |
| Phase 6 safety vocabulary | 6 | historical contamination control | future conflict-aware reasoning vocabulary | `REUSE_DIRECTLY` | do not rename or flatten |
| future cross-layer confidentiality merge logic | n/a | not implemented | required for answer-layer safety | `REQUIRES_PHASE_7_DECISION` | no existing app-layer contract |

## 7. Authority & Source-Role Findings

Machine-readable authority/source-role findings:

- Phase 4 has no explicit returned `source_layer_role`; deterministic authority is implicit from the API surface and the typed rule model.
- Phase 5 has no explicit returned `source_layer_role`; current-governed-knowledge role is implicit from the retrieval surface.
- Phase 5 does return `authority_classification`, but that is document authority class, not the same thing as cross-layer source role.
- Phase 6 explicitly returns `source_layer_role = historical_precedent`.

Current repository state therefore supports:

- explicit historical source-role handling
- implicit deterministic/current-governed source-role handling

Phase 7 will need:

- an adapter-level source-role field for Phase 4
- an adapter-level source-role field for Phase 5

## 8. Provenance Findings

### Phase 4

Direct function-level provenance available:

- `rule_code`
- `rule_version`
- `rule_id`
- source-code arrays

Deeper provenance available only through raw-table joins:

- `public.rule_source_links`
- `public.source_registry`
- `citation_locator`
- source file path / locator fields

### Phase 5

Retrieval-row provenance available:

- `document_code`
- `document_version_id`
- `document_version_number`
- `chunk_id`
- `chunk_set_id`
- `primary_chunk_source_id`
- `primary_document_version_source_object_id`
- `primary_source_locator`

Relationship provenance exists in schema but not retrieval rows:

- `public.knowledge_document_version_logical_rules`
- `public.knowledge_document_version_rule_versions`
- `private.knowledge_chunk_logical_rules`
- `private.knowledge_chunk_rule_versions`

### Phase 6

Retrieval-row provenance available:

- `case_code`
- `historical_case_version_id`
- `search_unit_id`
- `source_key`
- statement ids
- `primary_historical_case_version_source_object_id`
- `primary_source_object_id`
- `primary_source_locator`
- `source_link_count`

Current-authority connectivity exists in schema:

- `public.historical_case_version_logical_rules`
- `public.historical_case_version_rule_versions`
- `public.historical_case_version_knowledge_documents`
- `public.historical_case_version_knowledge_document_versions`

But those relationship rows are not returned directly by the current integration contract.

### Comparison

Provenance compatibility is good enough for Phase 7 adapters.

However:

- Phase 4 provenance is shallower in callable results
- Phase 5/6 retrieval rows are richer than Phase 4 API results
- cross-layer provenance normalization will still require adapter code

## 9. Confidentiality / PI Findings

### Alignment

Phase 5 and Phase 6 both rely on the Phase 5 confidentiality taxonomy:

- `public.knowledge_confidentiality_levels`

Phase 6 additionally uses helper functions:

- `private.strictest_knowledge_confidentiality_level_id(...)`
- `private.strictest_personal_information_status(...)`

This confirms a real “strictest wins” pattern exists in SQL for historical derived artifacts.

### Differences by phase

- Phase 4 has no equivalent confidentiality or PI field in its current callable contracts.
- Phase 5 stores confidentiality and PI underneath the retrieval layer, but does not return them in current retrieval rows.
- Phase 6 returns confidentiality and PI directly in retrieval results.

### Future combined-context implication

If a future Phase 7 context package combines:

- a broadly shareable Phase 4 rule
- a restricted Phase 5 chunk
- a restricted Phase 6 precedent

then the security boundary moves into application memory.

That boundary is not implemented yet.

Phase 7 will need an explicit rule for:

- strictest confidentiality wins across combined context
- PI-sensitive material handling before any answer-generation model call

## 10. Failure / Fallback Findings

### Phase 4

Phase 4 already distinguishes several non-success states, but not with one shared vocabulary across all domains.

Observed patterns:

- empty result set / `return` for some query functions
- explicit `insufficient_information`
- explicit `no_applicable_rule`
- explicit `requires_confirmation`
- explicit `manual_review_required`
- domain-specific evaluated states such as `restricted`, `quantity_available`, `insufficient_quantity`
- explicit exceptions on ambiguous multi-match conditions in some domains, such as booking fee rules

Important implication:

- “no current deterministic answer” is not equivalent to “historical precedent may answer instead”
- Phase 7 must preserve these distinctions

### Phase 5

Observed behavior:

- no single labeled integration fallback contract exists
- SQL hybrid degrades to FTS-only when query embedding is omitted
- CLI can intentionally force this through `--fts-only`
- query embedding or model resolution failures in the Python tooling are not wrapped in a stable current-knowledge retrieval response envelope

Important implication:

- Phase 7 cannot yet treat Phase 5 the way it can treat Phase 6 for explicit retrieval-mode reporting

### Phase 6

Observed behavior:

- healthy `hybrid`
- explicit degraded `fts_fallback`
- explicit `fallback_reason`
- explicit error categories
- limited-precedent and historical-value-only signals preserved during fallback
- `current_status_unknown`, `check_phase_4`, `check_phase_5`, and conflict-support metadata preserved in result rows

## 11. Query Routing / Domain Resolution Findings

No existing repository mechanism was found for:

- natural-language intent classification
- query routing across phases
- domain classification for deterministic rule lookup
- metadata-driven question planning
- cross-layer query planning

Deterministic routing looks feasible later because Phase 4 already has:

- typed domains
- stable rule codes
- rental-type and venue-space taxonomies
- explicit applicability fields in the domain tables

But it is not available yet from natural language alone.

Examples:

- “How long before an event does the final balance need to be paid?” can be answered only if the caller already routes to `api.get_payment_rules(...)`.
- “Can an external caterer use the venue?” requires the caller to know to use the catering-supplier domain rather than general retrieval.
- “Can the client access the Back Office?” requires the caller to route to space-access logic and possibly operational-requirement context separately.
- “What is the security deposit for a full venue rental?” cannot be cleanly routed to a Phase 4 answer because deposit logic remains an unresolved Phase 4 blocker rather than an implemented domain.

Conclusion:

- no query-routing capability exists today
- deterministic routing remains a real Phase 7 dependency
- 7.1 must decide whether routing is deterministic, heuristic, model-assisted, or mixed

## 12. Reusable Tooling

Reusable shared tooling found:

- `tools.phase_05_search.semantic_common.load_env_value(...)`
- `tools.phase_05_search.semantic_common.OpenAIEmbeddingsClient`
- `tools.phase_05_search.semantic_common.EmbeddingModelConfig`
- `tools.phase_05_search.semantic_common.embed_query_text(...)`
- `tools.phase_06_search.retrieval_common.load_active_historical_retrieval_model(...)`
- `tools.phase_06_search.retrieval_common.fetch_historical_embedding_coverage(...)`
- `tools.phase_06_search.retrieval_common.is_historical_embedding_state_complete(...)`
- `tools.phase_05_chunking.generate_pilot.run_supabase_query(...)`
- `tools.phase_05_chunking.generate_pilot.sql_text(...)`

Reusable evaluation infrastructure patterns found:

- fixture-based search evaluation
- deterministic benchmark comparison
- markdown report generation
- coverage reporting
- top-result and top-k success metrics
- focused integration regression tests

Best reuse targets for Task `7.0B`:

- evaluation/reporting patterns from `tools/phase_05_search/evaluate_*`
- evaluation/reporting patterns from `tools/phase_06_search/evaluate_*`
- test fixture style from `tools/phase_06_search/tests/test_historical_retrieval.py`

No answer-generation model utility exists yet.

Current OpenAI usage is limited to:

- embedding generation for Phase 5
- query embeddings for Phase 5 tooling
- historical embedding generation for Phase 6
- query embeddings for the Phase 6 integration contract

## 13. Existing Code To Avoid Reusing

No abandoned cross-layer orchestration, RAG, or context-pack implementation was found.

However, these should not be reused as production Phase 7 interfaces:

- `tools/phase_05_search/evaluate_*`
- `tools/phase_06_search/evaluate_*`

Reason:

- they are benchmark/report generators, not downstream retrieval contracts

Also avoid treating Phase 5 private SQL functions alone as the final Phase 7 current-knowledge interface, because:

- they lack top-level fallback labeling
- they lack explicit source-role labeling
- they require caller-managed embedding behavior

## 14. Phase 7 Dependency Gaps

Concrete gaps found:

- no stable generic Phase 4 adapter exists
- Phase 4 access remains domain-specific and parameter-shape-specific
- no single stable Phase 5 integration wrapper exists
- Phase 4 has no explicit returned source-role field
- Phase 5 has no explicit returned source-role field
- Phase 5 retrieval results do not expose confidentiality or PI
- Phase 5 retrieval results do not expose rule relationships directly
- no query-routing/domain-resolution capability exists
- no cross-layer confidentiality merge rule exists in application space
- no cross-layer result adapter exists
- no answer-generation model configuration exists

These are real Phase 7 dependencies, but not blockers to Task `7.0B`.

## 15. Architecture Questions Deferred to 7.1

Questions that 7.1 must decide:

- should every query touch all three layers or route selectively
- how should Phase 4 deterministic routing be implemented
- should Phase 4 routing be deterministic, heuristic, model-assisted, or mixed
- what Phase 4 adapter contract should normalize the domain-specific APIs
- should Phase 5 receive its own integration wrapper analogous to Phase 6
- what cross-layer source-role field should be emitted by adapters
- what unified context schema should exist across Phases 4–6
- how should cross-layer conflict and uncertainty be represented
- how should strictest confidentiality be enforced before any model call
- which retrieved rows, if any, must never be sent to an LLM
- how should `must_confirm`, `insufficient_information`, `no_applicable_rule`, `current_status_unknown`, and fallback states be preserved in reasoning outputs
- should Phase 6 current-authority references be joined into retrieval results during orchestration or only later in reasoning

## 16. Blockers / Contradictions

No blocker or contradiction records were identified.

No `P7-AUDIT-*` issue rose to the level of blocking either:

- Task `7.0B`
- later `7.1` architecture work

## 17. Readiness Decision

Final decision:

- `READY_FOR_7_0B`

Reason:

- Phases 4, 5, and 6 provide enough stable implemented surfaces and enough documented invariants to proceed to the next read-only Phase 7 planning task
- the remaining work is adapter/routing/architecture design, not dependency remediation
