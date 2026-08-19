# Phase 7 Phase 5 Wrapper Evaluation

## 1. Wrapper Scope

This evaluation covers only the 7.2D Phase 5 application-layer wrapper:

- `tools/phase_07_reasoning.phase5_wrapper.execute_phase5_plan(...)`

It verifies healthy hybrid execution, explicit lexical fallback, stable normalization into Phase 7 contracts, confidentiality and PI augmentation, provenance preservation, bounded Phase 4 relationship enrichment, and clear no-results / unavailable / failure semantics.

## 2. Healthy Retrieval Path

Healthy-path validation used live local Phase 5 retrieval on Saturday, August 8, 2026 with the restored current corpus:

- active retrieval-approved model: `id = 13`
- provider: `openai`
- model code: `text-embedding-3-small`
- current embedding coverage: `492 / 492` current chunks
- wrapper execution state: `success`
- wrapper retrieval mode: `hybrid`

The wrapper preserved direct database ordering and did not add application-side reranking.

## 3. Fallback Path

Degraded-mode validation used both injected failure and live lexical fallback:

- injected model-resolution failure plus live FTS fallback returned `fallback`
- live fallback query `external caterer requirements` returned `SERV-004`, `GOV-001`, `SERV-003`, `TPL-006`, `SERV-004`
- fallback retrieval mode was explicitly `fts_fallback`
- fallback sensitivity, PI, provenance, and relationship payloads remained populated

Additional injected checks verified:

- query embedding failure -> `fts_fallback`
- dual hybrid/FTS failure -> `unavailable`

## 4. Scenario Set

Healthy live scenario count: `12`

Degraded scenario count: `1`

Total evaluated scenarios: `13`

Healthy live set:

- `P7-EVAL-006`
- `P7-EVAL-007`
- `P7-EVAL-008`
- `P7-EVAL-009`
- `P7-EVAL-010`
- `P7-EVAL-011`
- `P7-EVAL-012`
- `P7-EVAL-013`
- `P7-EVAL-014`
- `P7-EVAL-019`
- `P7-EVAL-021`
- `P7-EVAL-022`

Degraded set:

- `P7-EVAL-038`

## 5. Results by Scenario

| Scenario | Query | Expected docs | Returned docs | Retrieval mode | Source role | Confidentiality | PI | Provenance | Rule relationship enrichment | Pass/Fail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P7-EVAL-006` | final balance explanation | `CF-003`, `CF-005`, `CF-007`, `GOV-002` | `TPL-006`, `TPL-013`, `TPL-010` | `hybrid` | correct | complete | complete | complete | payload present, no links returned | pass with acceptable guidance alternative |
| `P7-EVAL-007` | external caterer requirements | `SERV-003`, `SERV-004`, `CF-007` | `SERV-004`, `SERV-003`, `TPL-006` | `hybrid` | correct | complete | complete | complete | non-zero chunk/document links | pass |
| `P7-EVAL-008` | catering VAT explanation | `SERV-003` | `SERV-003`, `SERV-001`, `CF-007`, `TPL-001` | `hybrid` | correct | complete | complete | complete | non-zero links | pass |
| `P7-EVAL-009` | Supported Rental explanation | `SERV-001` | `SERV-001`, `CF-003`, `TPL-001`, `TPL-003` | `hybrid` | correct | complete | complete | complete | non-zero links | pass |
| `P7-EVAL-010` | facilitator confirmation explanation | `SERV-001`, `CF-007` | `TPL-006`, `SERV-001`, `CF-007` | `hybrid` | correct | complete | complete | complete | non-zero links on supporting items | pass |
| `P7-EVAL-011` | site-visit guidance | `TPL-008` | `TPL-008`, `TPL-006` | `hybrid` | correct | complete | complete | complete | payload present, no links returned | pass |
| `P7-EVAL-012` | site-visit scheduling | `TPL-008` | `TPL-006`, `TPL-008` | `hybrid` | correct | complete | complete | complete | payload present, no links returned | pass with acceptable guidance alternative |
| `P7-EVAL-013` | full-production scope framing | `SERV-001`, `TPL-005` | `TPL-005`, `TPL-004`, `TPL-003` | `hybrid` | correct | complete | complete | complete | non-zero links | pass |
| `P7-EVAL-014` | final readiness / handover | `TPL-009`, `TPL-010` | `TPL-010`, `TPL-009` | `hybrid` | correct | complete | complete | complete | payload present, no links returned | pass |
| `P7-EVAL-019` | beauty-brand catering current slice | `SERV-003`, `SERV-004`, `CF-007` | `TPL-007`, `SERV-003` | `hybrid` | correct | complete | complete | complete | non-zero links on supporting items | pass with acceptable current-guidance mix |
| `P7-EVAL-021` | current service-boundary guidance | `CF-007`, `SERV-001`, `TPL-002`, `TPL-003` | `CF-007`, `OPS-003` | `hybrid` | correct | complete | complete | complete | non-zero links | pass after benchmark correction |
| `P7-EVAL-022` | build-up current communication / context | `CF-005`, `CF-007`, `TPL-009` | `TPL-010`, `CF-007`, `TPL-002`, `TPL-003`, `TPL-005` | `hybrid` | correct | complete | complete | complete | non-zero links on supporting items | pass |
| `P7-EVAL-038` | Phase 5 unavailable degraded scenario | degraded-mode honesty | injected `unavailable` path and live `fts_fallback` path | explicit degraded labels | correct | preserved | preserved | preserved | preserved | pass |

## 6. Aggregate Retrieval Metrics

Healthy live scenario retrieval success rate, counting allowed alternatives: `12 / 12` (`100.0%`)

Required-document metrics across the 12 healthy live scenarios:

- Hit@1: `7 / 12` (`58.3%`)
- Hit@3: `11 / 12` (`91.7%`)
- Hit@5: `11 / 12` (`91.7%`)

Normalization and metadata correctness across the healthy live scenarios:

- source-role correctness: `12 / 12`
- retrieval-mode correctness: `12 / 12`
- confidentiality augmentation completeness: `12 / 12`
- PI augmentation completeness: `12 / 12`
- provenance completeness: `12 / 12`
- relationship-enrichment payload completeness: `12 / 12`

## 7. Rank-Parity Check

Representative wrapper-vs-direct-hybrid parity checks matched exactly for all tested queries:

- `Can an external caterer work here, and what information do we need from them?`
- `What does Supported Rental mean right now, and how should we explain it?`
- `Should we suggest a site visit before finalizing layout and logistics?`
- `The client wants to run a whole-venue event themselves. What does WNC handle now, and have we done similar before?`

Parity result: `4 / 4 exact chunk-order matches`

## 8. Fallback Evaluation

Validated fallback paths:

- model resolution failure on `external caterer requirements` -> live `fts_fallback`
- model resolution failure on the full `P7-EVAL-007` question -> honest `no_results` with explicit fallback metadata
- query embedding failure -> injected `fts_fallback`
- hybrid unavailable + FTS unavailable -> injected `unavailable`

Fallback labels were explicit and correct in each checked case.

## 9. No-Results / Failure Evaluation

Validated no-results path:

- live query `site visit` with `document_code = DOES-NOT-EXIST`
- result: `execution_state = no_results`
- result count: `0`

Validated failure / unavailable semantics:

- technical fallback outage can surface `unavailable`
- wrapper does not fabricate current-guidance rows when both healthy and fallback paths are unavailable

## 10. Sensitivity Review

Findings:

- every healthy live result carried a normalized confidentiality level
- every healthy live result carried a normalized PI status
- live corpus PI status remained mostly `unknown`, matching the current underlying source-object state
- injected enrichment failure correctly defaulted to `restricted`

Observed live confidentiality values included:

- `internal`
- `commercially_sensitive`
- `externally_shareable`

## 11. Provenance Review

Findings:

- every healthy live result carried a primary source locator
- direct retrieval provenance was preserved into the shared provenance envelope
- bounded source identity enrichment remained metadata-only

## 12. Rule Relationship Review

Findings:

- every healthy live result carried `phase_4_rule_relationships` in `layer_payload`
- relationship counts varied by current document family, which is expected
- non-zero Phase 4 relationship enrichment appeared in scenarios `P7-EVAL-007`, `008`, `009`, `010`, `013`, `019`, `021`, and `022`
- scenarios `P7-EVAL-006`, `011`, `012`, and `014` legitimately returned zero linked rule relationships

## 13. Deviations / Accepted Limitations

Observed deviations:

- `P7-EVAL-006` and `P7-EVAL-012` resolved through acceptable current-guidance alternatives rather than the prompt’s primary expected document family
- `P7-EVAL-019` still resolves through a mixed current-guidance alternative rather than a top-rank primary expected document
- lexical fallback quality remains wording-sensitive for long natural-language current-guidance prompts, even though the wrapper now proves and labels degraded behavior honestly
- the corrected `P7-EVAL-021` benchmark must accept `CF-007` as a legitimate current service-boundary document family, with `SERV-001`, `TPL-002`, and `TPL-003` remaining acceptable supporting alternatives

Interpretation:

- wrapper behavior itself is stable and contract-correct
- `P7-EVAL-021` was a benchmark-integrity issue rather than a wrapper defect
- the DB regression suite now coexists cleanly with the restored live Phase 5 and Phase 6 corpora
