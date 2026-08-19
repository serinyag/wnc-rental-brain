# Phase 7 Context Safety Evaluation

Evaluation date:

- August 9, 2026

## 1. Scope

This evaluation covers Phase 7 task `7.2G` only:

- `tools.phase_07_reasoning.context_safety.finalize_context_safety(...)`
- generator-safe projection packaging inside `ContextPackage`
- final confidentiality / PI resolution
- final degraded-context safety packaging
- final generator-policy restrictions

This evaluation does not include answer generation.

## 2. Safety Gate Flow

Verified runtime flow:

1. `build_context_package(...)` builds a valid authority-resolved 7.2F package
2. `finalize_context_safety(...)` consumes that package without rerunning planning, retrieval, or authority resolution
3. safety finalization computes:
   - generator-safe projections
   - generator-safe grounding
   - final confidentiality state
   - final degraded-context packaging
   - final generator policy
4. the returned `ContextPackage` preserves internal context for audit and carries a separate generator-safe boundary

## 3. Confidentiality Merge

Implemented and verified:

- reused confidentiality taxonomy:
  - `externally_shareable`
  - `internal`
  - `commercially_sensitive`
  - `restricted`
- deterministic ordering confirmed from repository semantics:
  - `externally_shareable < internal < commercially_sensitive < restricted`
- final effective confidentiality is computed from generator-eligible context after safety projection
- Phase 4 default `internal` participation remains unchanged

## 4. PI Aggregation

Implemented and verified:

- item-level PI states remain intact internally
- generator-boundary PI posture is recomputed after projection
- de-identified projections remove raw PI-bearing detail from the generator-visible surface
- unknown PI remains conservative and emits `pi_status_unknown`

Package-level safety state resolves:

- `personal_information_status_summary`
- `personal_information_present`
- `de_identification_required`

## 5. De-Identification Policy

Initial deterministic 7.2G transforms:

- restricted historical precedent -> high-level, de-identified summary
- PI-bearing historical precedent -> high-level, de-identified summary
- current governed knowledge with sensitive/unknown PI posture -> generator-visible high-level projection when needed
- raw provenance locators are replaced with safe code-oriented locators for generator-visible grounding

No governed stored content is mutated.

## 6. Suppression Policy

Implemented suppression rules:

- source-level `generation_allowed = false` -> suppressed
- non-material sensitive detail with no generator-visible value after minimization -> suppressed
- suppressed items remain in internal authority context and audit state
- suppressed items are excluded from generator-visible grounding

Observed live 40-scenario result:

- suppressed item count across live scenarios: `0`

Reason:

- the live 40-scenario set required de-identified high-level historical projections, not full live suppression

Synthetic safety fixtures did verify:

- restricted/PI-bearing suppression
- generation-blocked fail-closed behavior

## 7. Generator Boundary

Supported 7.2G boundary:

- `internal_generation`

Not implemented:

- external/client generation
- prompt design
- answer generation
- RAG
- agents

## 8. Generation Decision Rules

Implemented decision classes:

- `allowed`
- `allowed_with_restrictions`
- `blocked`

Verified policy:

- unresolved authority does not automatically block generation
- confirmation-required states do not automatically block generation
- degraded retrieval does not automatically block generation
- material source-level generation prohibition blocks generation
- safety finalization fails closed

## 9. Degraded Context Packaging

Finalized `DegradedRetrievalState` now preserves:

- affected layers
- execution states
- fallback reasons
- `materially_affects_answer_completeness`
- generator warnings

Verified warning normalization:

- Phase 5 fallback -> `current_guidance_retrieval_degraded`
- Phase 6 fallback -> `historical_retrieval_degraded`
- Phase 5 unavailable -> `current_guidance_unavailable`
- Phase 4 failed/unavailable -> `deterministic_layer_failed`

## 10. 40-Scenario Safety Evaluation

| Scenario | Authority outcome | Effective confidentiality | PI state | De-identification applied | Suppressed item count | Generator decision | Warnings | Degraded state | Grounding valid | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P7-EVAL-001 | DETERMINISTIC_CURRENT | internal | no | no | 0 | allowed | `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-002 | DETERMINISTIC_CURRENT | internal | no | no | 0 | allowed | `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-003 | DETERMINISTIC_CURRENT | internal | no | no | 0 | allowed | `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-004 | DETERMINISTIC_CURRENT | internal | no | no | 0 | allowed | `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-005 | DETERMINISTIC_CURRENT | internal | no | no | 0 | allowed | `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-006 | DETERMINISTIC_CURRENT | internal | no | yes | 0 | allowed_with_restrictions | `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-007 | CURRENT_GUIDANCE | commercially_sensitive | no | yes | 0 | allowed_with_restrictions | `commercially_sensitive_context`, `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-008 | DETERMINISTIC_CURRENT | commercially_sensitive | no | yes | 0 | allowed_with_restrictions | `commercially_sensitive_context`, `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-009 | CURRENT_GUIDANCE | commercially_sensitive | no | yes | 0 | allowed_with_restrictions | `commercially_sensitive_context`, `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-010 | REQUIRES_CONFIRMATION | commercially_sensitive | no | yes | 0 | allowed_with_restrictions | `confirmation_required`, `commercially_sensitive_context`, `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-011 | CURRENT_GUIDANCE | internal | no | yes | 0 | allowed_with_restrictions | `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-012 | CURRENT_GUIDANCE | internal | no | yes | 0 | allowed_with_restrictions | `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-013 | CURRENT_GUIDANCE | commercially_sensitive | no | yes | 0 | allowed_with_restrictions | `commercially_sensitive_context`, `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-014 | CURRENT_GUIDANCE | internal | no | yes | 0 | allowed_with_restrictions | `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-015 | HISTORICAL_PRECEDENT | restricted | no | yes | 0 | allowed_with_restrictions | `pi_deidentified` | no | yes | PASS |
| P7-EVAL-016 | HISTORICAL_PRECEDENT | restricted | no | yes | 0 | allowed_with_restrictions | `pi_deidentified` | no | yes | PASS |
| P7-EVAL-017 | HISTORICAL_PRECEDENT | commercially_sensitive | no | yes | 0 | allowed_with_restrictions | `limited_precedent`, `commercially_sensitive_context`, `pi_deidentified` | no | yes | PASS |
| P7-EVAL-018 | HISTORICAL_PRECEDENT | restricted | no | yes | 0 | allowed_with_restrictions | `limited_precedent`, `pi_deidentified` | no | yes | PASS |
| P7-EVAL-019 | MIXED_WITH_CURRENT_PRIORITY | restricted | no | yes | 0 | allowed_with_restrictions | `limited_precedent`, `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-020 | MIXED_WITH_CURRENT_PRIORITY | restricted | no | yes | 0 | allowed_with_restrictions | `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-021 | MIXED_WITH_CURRENT_PRIORITY | restricted | no | yes | 0 | allowed_with_restrictions | `limited_precedent`, `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-022 | MIXED_WITH_CURRENT_PRIORITY | restricted | no | yes | 0 | allowed_with_restrictions | `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-023 | MIXED_WITH_CURRENT_PRIORITY | restricted | no | yes | 0 | allowed_with_restrictions | `limited_precedent`, `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-024 | REQUIRES_CONFIRMATION | restricted | no | yes | 0 | allowed_with_restrictions | `confirmation_required`, `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-025 | INSUFFICIENT_CURRENT_AUTHORITY | restricted | no | yes | 0 | allowed_with_restrictions | `current_authority_insufficient`, `historical_value_context_only`, `limited_precedent`, `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-026 | INSUFFICIENT_CURRENT_AUTHORITY | restricted | no | yes | 0 | allowed_with_restrictions | `current_authority_insufficient`, `historical_value_context_only`, `limited_precedent`, `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-027 | INSUFFICIENT_CURRENT_AUTHORITY | restricted | no | yes | 0 | allowed_with_restrictions | `current_authority_insufficient`, `historical_value_context_only`, `limited_precedent`, `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-028 | INSUFFICIENT_CURRENT_AUTHORITY | restricted | no | yes | 0 | allowed_with_restrictions | `current_authority_insufficient`, `historical_value_context_only`, `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-029 | REQUIRES_CONFIRMATION | restricted | no | yes | 0 | allowed_with_restrictions | `confirmation_required`, `historical_value_context_only`, `limited_precedent`, `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-030 | DETERMINISTIC_CURRENT | restricted | no | yes | 0 | allowed_with_restrictions | `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-031 | DETERMINISTIC_CURRENT | restricted | no | yes | 0 | allowed_with_restrictions | `historical_value_context_only`, `limited_precedent`, `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-032 | MIXED_WITH_CURRENT_PRIORITY | restricted | no | yes | 0 | allowed_with_restrictions | `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-033 | INSUFFICIENT_CURRENT_AUTHORITY | commercially_sensitive | no | yes | 0 | allowed_with_restrictions | `current_authority_insufficient`, `commercially_sensitive_context`, `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-034 | INSUFFICIENT_CURRENT_AUTHORITY | commercially_sensitive | no | yes | 0 | allowed_with_restrictions | `current_authority_insufficient`, `commercially_sensitive_context`, `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-035 | REQUIRES_CONFIRMATION | internal | no | yes | 0 | allowed_with_restrictions | `confirmation_required`, `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-036 | REQUIRES_CONFIRMATION | internal | no | yes | 0 | allowed_with_restrictions | `confirmation_required`, `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-037 | HISTORICAL_PRECEDENT | restricted | no | yes | 0 | allowed_with_restrictions | `historical_retrieval_degraded`, `pi_deidentified` | yes | yes | PASS |
| P7-EVAL-038 | DETERMINISTIC_CURRENT | internal | no | no | 0 | allowed_with_restrictions | `current_guidance_unavailable`, `pi_status_unknown` | yes | yes | PASS |
| P7-EVAL-039 | MIXED_WITH_CURRENT_PRIORITY | restricted | no | yes | 0 | allowed_with_restrictions | `limited_precedent`, `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |
| P7-EVAL-040 | MIXED_WITH_CURRENT_PRIORITY | restricted | no | yes | 0 | allowed_with_restrictions | `limited_precedent`, `pi_deidentified`, `pi_status_unknown` | no | yes | PASS |

## 11. Confidentiality Matrix Results

Deterministic confidentiality matrix status:

- `internal + externally_shareable + none -> internal`: PASS
- `internal + internal + internal -> internal`: PASS
- `internal + commercially_sensitive + internal -> commercially_sensitive`: PASS
- `internal + externally_shareable + restricted -> restricted`: PASS
- `internal + commercially_sensitive + restricted -> restricted`: PASS

## 12. PI Test Results

Verified safety cases:

- all-no PI projection path: PASS
- one-yes historical PI path: PASS
- one-unknown path: PASS
- yes + restricted historical path: PASS
- historical PI de-identification path: PASS
- no PI leakage into generator-visible projection: PASS

## 13. Restricted / Suppression Tests

Verified:

- restricted historical precedent is not passed raw to generator-visible context
- raw historical commercial detail is removed from generator-visible summaries
- generator-visible grounding does not reuse raw historical case-title locators
- fully suppressed / blocked behavior is covered by dedicated synthetic safety fixtures

## 14. Generation-Decision Tests

Verified:

- `allowed`: current deterministic scenarios where safe projection stays low-risk
- `allowed_with_restrictions`: confidentiality, PI, degraded, limited-precedent, unresolved, and confirmation-bound scenarios
- `blocked`: synthetic source-restricted material fixture

## 15. Degraded-Mode Tests

Verified:

- Phase 5 fallback -> `current_guidance_retrieval_degraded`
- Phase 6 fallback -> `historical_retrieval_degraded`
- Phase 5 unavailable with surviving Phase 4 truth -> `current_guidance_unavailable`
- Phase 4 failed -> safe uncertainty packaging with `deterministic_layer_failed`

## 16. Authority Regression Check

Authority invariants after safety finalization:

- historical-gap-filling violations: `0`
- Phase 4 authority violations: `0`
- authority outcome accuracy: `1.0`
- conflict-code recall: `1.0`
- contamination-annotation recall: `1.0`
- unresolved-state accuracy: `1.0`

Safety finalization did not mutate authority resolution.

## 17. Aggregate Metrics

- 40-scenario safety evaluation pass rate: `40 / 40`
- effective-confidentiality accuracy: `1.0`
- strictest-wins accuracy: `1.0`
- confidentiality escalation accuracy: `1.0`
- PI aggregation accuracy: `1.0`
- de-identification decision accuracy: `1.0`
- PI leakage count: `0`
- required suppression accuracy: `1.0`
- unsafe generator-visible item count: `0`
- generation-decision accuracy: `1.0`
- degraded-warning accuracy: `1.0`
- generator-visible grounding validity: `1.0`
- sensitive provenance leakage count: `0`
- historical-gap-filling violations: `0`
- Phase 4 authority violations: `0`

Supporting regression runs:

- Phase 7 reasoning suite: `89 / 89`
- combined Phase 5/6 Python regression: `77 / 77`
- Supabase DB regression: `PASS` (`33` files, `937` assertions)

## 18. Failures / Limitations

- no live 40-scenario case required full generator-visible suppression after projection; live scenarios were satisfied by de-identified high-level projections
- no live 40-scenario case required a blocked generator decision; fail-closed blocking was verified by deterministic synthetic safety fixtures
- answer generation remains intentionally out of scope
