# Phase 7 Phase 6 Adapter Evaluation

Evaluation date:

- August 8, 2026

## 1. Scope

This evaluation covers Phase 7 task `7.2E` only:

- `tools/phase_07_reasoning.phase6_adapter.execute_phase6_plan(...)`

The goal was to prove that the adapter:

- reuses the Phase 6 contract directly
- preserves retrieval ordering
- preserves fallback labeling
- preserves historical safety metadata
- preserves provenance, confidentiality, and PI metadata
- does not rerank or reinterpret historical results

## 2. Healthy Hybrid Parity

Live direct-vs-adapter parity was exercised against representative historical queries:

- `storage price`
- `florals`
- `permit compliance`
- `whole venue clearing`

For each query:

- direct execution used `retrieve_historical_precedents(...)`
- adapter execution used `execute_phase6_plan(...)` with `phase_6_result_limit = 5`
- the first five `(case_code, source_key)` pairs were compared exactly

Result:

- `4 / 4` exact top-5 order matches

## 3. Healthy Hybrid Outcomes

`storage price`

- direct mode: `hybrid`
- adapter state: `success`
- exact top-5 parity: yes
- top adapter result: `HC-004 / case_narrative:4`
- preserved metadata:
  - `precedent_availability = limited`
  - `lesson_kind = null`
  - `historical_value_only = null`
  - `contamination_risk_level = null`
  - `current_authority_disposition = null`
  - `confidentiality = restricted`
  - `personal_information_status = yes`

`florals`

- direct mode: `hybrid`
- adapter state: `success`
- exact top-5 parity: yes
- top adapter result: `HC-003 / decision:9`
- preserved metadata:
  - `precedent_availability = limited`
  - `historical_value_only = true`
  - `contamination_risk_level = high`
  - `current_authority_disposition = current_status_unknown`
  - `confidentiality = restricted`
  - `personal_information_status = yes`

`permit compliance`

- direct mode: `hybrid`
- adapter state: `success`
- exact top-5 parity: yes
- top adapter result: `HC-009 / lesson:41`
- preserved metadata:
  - `precedent_availability = limited`
  - `lesson_kind = caution_warning`
  - `historical_value_only = false`
  - `contamination_risk_level = medium`
  - `current_authority_disposition = check_phase_5`
  - `confidentiality = restricted`
  - `personal_information_status = yes`

`whole venue clearing`

- direct mode: `hybrid`
- adapter state: `success`
- exact top-5 parity: yes
- top adapter result: `HC-006 / lesson:32`
- preserved metadata:
  - `precedent_availability = active`
  - `lesson_kind = analyst_inference`
  - `historical_value_only = false`
  - `contamination_risk_level = low`
  - `current_authority_disposition = check_phase_4`
  - `confidentiality = restricted`
  - `personal_information_status = yes`

Interpretation:

- the adapter preserved the live Phase 6 ranking exactly
- the adapter did not collapse narrative rows into statement-level metadata
- the adapter did not invent current-authority conclusions

## 4. Forced Fallback Parity

Forced degraded-mode evaluation simulated model-resolution failure inside the existing Phase 6 contract and then compared direct retrieval with adapter execution for:

- `permit compliance`

Observed result:

- direct retrieval mode: `fts_fallback`
- direct fallback reason: `embedding_model_resolution_failed`
- adapter execution state: `fallback`
- adapter fallback reason: `embedding_model_resolution_failed`
- exact top-5 order match: yes

Top-five parity:

1. `HC-009 / lesson:41`
2. `HC-009 / responsibility:35`
3. `HC-009 / decision:24`
4. `HC-009 / decision:25`
5. `HC-009 / lesson:42`

Interpretation:

- the adapter preserves explicit degraded labeling
- the adapter preserves fallback reason codes without relabeling
- the adapter preserves Phase 6 lexical-fallback ordering exactly

## 5. Unit Regression

Focused adapter regression:

- command: `python3 -m unittest tools.phase_07_reasoning.tests.test_phase6_adapter`
- result: `9 / 9` passing

Covered behaviors:

- `not_requested` skips retrieval entirely
- runtime result limit is used
- supported Phase 6 filters are forwarded unchanged
- healthy hybrid rows normalize into frozen Phase 7 contracts
- fallback rows preserve degraded retrieval metadata
- `no_results` remains distinct from failure
- database outage maps to `unavailable`
- non-database retrieval failure maps to `failed`
- PI normalization preserves `yes` / `no` / `unknown`
- JSON serialization keeps the historical layer payload intact

## 6. Broader Python Regression

Combined Python regression:

- command:
  - `python3 -m unittest tools.phase_07_reasoning.tests.test_contracts tools.phase_07_reasoning.tests.test_query_planner tools.phase_07_reasoning.tests.test_phase4_adapter tools.phase_07_reasoning.tests.test_phase5_wrapper tools.phase_07_reasoning.tests.test_phase6_adapter tools.phase_05_search.tests.test_hybrid_search tools.phase_06_search.tests.test_historical_retrieval`
- result: `77 / 77` passing

Interpretation:

- the new adapter did not regress shared contracts
- the adapter did not disturb Phase 4 or Phase 5 execution behavior
- the adapter remained compatible with the existing Phase 6 retrieval contract tests

## 7. Local Database Regression

Full local pgTAP regression:

- command: `npx -y supabase@latest test db --local`
- result: `937 / 937` passing

Interpretation:

- the repository remains clean against the live local database state
- Phase 7.2E introduced no DB regression

## 8. Findings

Findings:

- no adapter parity mismatch was found in the evaluated healthy scenarios
- no degraded-mode labeling mismatch was found in the forced fallback scenario
- no historical safety metadata loss was found in the evaluated rows
- no cross-layer behavior was added

Accepted limitation:

- the adapter intentionally preserves whatever Phase 6 ordering already returns, even when a scenario might not place a human-expected case at rank one
- this is correct for 7.2E because ranking ownership remains in Phase 6

## 9. Evaluation Decision

Decision:

- `PASS`

Reason:

- the Phase 6 adapter is behaving as a faithful Phase 7 normalization boundary over the approved Phase 6 retrieval contract
