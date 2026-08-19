# Phase 5 Retrieval Readiness Audit

Date: August 7, 2026

## 1. Executive Summary

Phase 5 is functionally complete through production hybrid retrieval and is structurally reproducible after a clean rebuild.

The live audited state confirms:

- `24` logical Phase 5 knowledge documents are represented in the database
- `24` current corpus-decision rows exist
- `22` current `include` documents are `active`
- `2` current `include` documents remain `draft`
- `22` current chunk sets exist
- `525` current chunks exist
- `21` current documents are retrieval-eligible
- `492` current chunks are retrieval-eligible
- `492 / 492` retrieval-eligible chunks have current embeddings
- production hybrid retrieval reproduces the approved original fixture at:
  - `Hit@1 13/13`
  - `Hit@3 13/13`
  - `Preferred Before Secondary 13/13`

No closure-blocking integrity, security, eligibility-alignment, or retrieval-regression defect was found.

The remaining issues are accepted Phase 5 limitations or later-phase concerns, not Phase 5 closure blockers.

## 2. Corpus Counts

Canonical reconciliation:

- Phase 5 source matrix active logical-document candidate set: `25`
- controlled catalogue logical documents actually loaded: `24`
- deferred logical/source records intentionally not loaded as current knowledge: `6`
  - `GOV-004`
  - `COM-001`
  - `COM-001-XLSM`
  - `COM-001-XLSX`
  - `SERV-002`
  - `HC-AMO-000`
- provenance-only excluded exports intentionally not loaded as logical documents: `2`
  - `CF-004`
  - `CF-006`

Reconciliation note:

- the source matrix counted `CF-002` as a separate current export representation
- the implemented catalogue models that export as a source representation under logical document `CF-001`, not as its own current logical document
- this reduces the represented logical-document total from `25` candidate rows to `24` implemented logical documents without losing provenance

Current represented logical documents by readiness state:

| Code | Governance | Chunk/Search State | Retrieval State | Audit Classification |
| --- | --- | --- | --- | --- |
| `CF-001` | active | not chunked | not searchable | `NO_SAFE_PARSER` |
| `CF-003` | active | chunked | searchable + embedded | `CHUNKED_SEARCHABLE` |
| `CF-005` | active | chunked | searchable + embedded | `CHUNKED_SEARCHABLE` |
| `CF-007` | active | chunked | searchable + embedded | `CHUNKED_SEARCHABLE` |
| `GOV-001` | active | chunked | searchable + embedded | `CHUNKED_SEARCHABLE` |
| `GOV-002` | active | chunked | searchable + embedded | `CHUNKED_SEARCHABLE` |
| `GOV-003` | draft | not chunked | not searchable | `NOT_CURRENT` |
| `OPS-001` | draft | chunked | not retrieval-eligible | `CHUNKED_DRAFT_NOT_RETRIEVAL_ELIGIBLE` |
| `OPS-002` | active | chunked | searchable + embedded | `CHUNKED_SEARCHABLE` |
| `OPS-003` | active | chunked | searchable + embedded | `CHUNKED_SEARCHABLE` |
| `SERV-001` | active | chunked | searchable + embedded | `CHUNKED_SEARCHABLE` |
| `SERV-003` | active | chunked | searchable + embedded | `CHUNKED_SEARCHABLE` |
| `SERV-004` | active | chunked | searchable + embedded | `CHUNKED_SEARCHABLE` |
| `TPL-001` | active | chunked | searchable + embedded | `CHUNKED_SEARCHABLE` |
| `TPL-002` | active | chunked | searchable + embedded | `CHUNKED_SEARCHABLE` |
| `TPL-003` | active | chunked | searchable + embedded | `CHUNKED_SEARCHABLE` |
| `TPL-004` | active | chunked | searchable + embedded | `CHUNKED_SEARCHABLE` |
| `TPL-005` | active | chunked | searchable + embedded | `CHUNKED_SEARCHABLE` |
| `TPL-006` | active | chunked | searchable + embedded | `CHUNKED_SEARCHABLE` |
| `TPL-007` | active | chunked | searchable + embedded | `CHUNKED_SEARCHABLE` |
| `TPL-008` | active | chunked | searchable + embedded | `CHUNKED_SEARCHABLE` |
| `TPL-009` | active | chunked | searchable + embedded | `CHUNKED_SEARCHABLE` |
| `TPL-010` | active | chunked | searchable + embedded | `CHUNKED_SEARCHABLE` |
| `TPL-013` | active | chunked | searchable + embedded | `CHUNKED_SEARCHABLE` |

## 3. Governance Coverage

Observed governance coverage:

- document records: `24 / 24`
- current corpus-decision rows: `24 / 24`
- missing primary categories: `0`
- missing authority classifications: `0`
- missing confidentiality classifications: `0`
- documents with multiple current corpus rows: `0`
- documents with multiple versions: `0`
- versions without audience links: `0`
- versions without rental-type links: `2`

The two versions without rental-type links are:

- `TPL-004`
- `TPL-005`

Assessment:

- this is an accepted modeling choice, not a defect
- the catalogue intentionally left rental applicability unlinked for these proposal templates because the source matrix marked them as review-sensitive service-scope guidance rather than canonical rental-type-scoped products

Governance verdict:

- no missing required governance metadata was found
- no duplicate active-version defect was found
- no unsupported taxonomy-value defect was found

## 4. Source Provenance Coverage

Observed provenance coverage:

- versions without any source link: `0`
- version/source links without source role: `0`
- version/source links without usage disposition: `0`
- versions without preferred extraction source: `0`
- versions without primary representation: `0`
- source locators missing: `0`
- personal-information status missing: `0`
- personal-information status `unknown`: `27`
- personal-information status `yes`: `0`
- personal-information status `no`: `0`

Assessment:

- provenance integrity is structurally complete
- personal-information assessment is consistently present, but currently unresolved as `unknown` across all source objects
- `unknown` is valid and was not force-normalized to `no`

## 5. Known Provenance Exceptions

| Item | Status | Audit Conclusion |
| --- | --- | --- |
| missing editable `CF-001` master | `ACCEPTED_KNOWN_LIMITATION` | logical record and manual-reference provenance exist, but no local editable master is available |
| `CF-001` PNG/PDF governance-format mismatch | `ACCEPTED_KNOWN_LIMITATION` | mismatch remains documented but does not break source traceability |
| lifecycle wording drift for `GOV-002` | `ACCEPTED_KNOWN_LIMITATION` | wording drift remains documented in notes; implementation is internally consistent |
| lifecycle wording drift for `GOV-003` | `ACCEPTED_KNOWN_LIMITATION` | wording drift remains documented; live state still correctly treats the document as draft |
| `OPS-001` controlled-draft status | `ACCEPTED_KNOWN_LIMITATION` | preserved as a current draft with chunked procedural content but intentionally excluded from active retrieval |
| provenance-only historical `CF-004` | `RESOLVED` | retained as excluded export provenance under `CF-003` |
| provenance-only historical `CF-006` | `RESOLVED` | retained as excluded export provenance under `CF-005` |
| embedded `OPS-003` | `RESOLVED` | modeled as its own logical document with shared physical source |
| embedded `SERV-004` | `RESOLVED` | modeled as its own logical document with shared physical source |
| combined `TPL-008` | `RESOLVED` | modeled as its own logical document with shared physical source |
| combined `TPL-010` | `RESOLVED` | modeled as its own logical document with shared physical source |

No known provenance exception currently classifies as `BLOCKING`.

## 6. Rule Connectivity Coverage

Current actual counts:

- document-version stable logical-rule links: `42`
- document-version exact rule-version links: `0`
- chunk-level stable logical-rule links: `10`
- distinct linked current chunks: `9`
- chunk-level exact rule-version links: `0`

Assessment:

- the expected stable-link coverage is present
- the expected exact-link absence is present
- no evidence was found that an exact historical link exists in-source but was omitted from the implemented model

Rule-connectivity verdict:

- `PASS` for stable logical-rule coverage where implemented
- `ACCEPTED_PHASE_5_LIMITATION` for exact historical rule-version links remaining at zero until evidence justifies them

## 7. Chunking Coverage

Observed chunking state:

- current chunk sets: `22`
- current chunks: `525`
- current chunk provenance traces: `525`
- current included active documents: `22`
- current included draft documents: `2`

Intentional non-generation cases confirmed:

- `CF-001` -> `NO_SAFE_PARSER`
- `GOV-003` -> `NOT_CURRENT`

Important nuance:

- `OPS-001` is draft, but it remains chunked as a preserved controlled-draft operational manual
- it is not retrieval-eligible because the search and embedding surfaces only admit `active` governed versions

Chunking verdict:

- every document has an explicit chunking/readiness state
- every current chunk has provenance
- no unexpected unchunked current active document was found beyond `CF-001`

## 8. Chunk Integrity

Integrity audit results:

- blank current chunks: `0`
- duplicate ordinals within current sets: `0`
- duplicate current chunk sets per version: `0`
- current chunks without trace: `0`
- chunk traces linked to the wrong governed version: `0`
- current sets missing valid extraction-source provenance: `0`
- current sets created from excluded extraction sources: `0`
- superseded chunk sets still searchable: `0`

Chunk-integrity verdict:

- `0 integrity violations`

## 9. FTS Coverage

Current FTS state:

- searchable current documents: `21`
- searchable current chunks: `492`
- searchable chunks with populated search vectors: `492`
- searchable chunks missing search vectors: `0`
- GIN index present: `knowledge_chunks_search_vector_gin_idx`

Why `525` current chunks becomes `492` searchable chunks:

- current chunk sets include preserved draft `OPS-001` with `33` chunks
- `private.current_knowledge_chunks` intentionally filters to `governance_status = 'active'`
- `525 - 33 = 492`
- `GOV-003` contributes `0` chunks because it was intentionally not chunked while draft

FTS verdict:

- the current FTS surface is complete for the intended active retrieval corpus
- no deferred or non-current knowledge leaks into FTS eligibility

## 10. Embedding Coverage

Current approved embedding model:

- active retrieval-approved models: `1`
- provider: `openai`
- model: `text-embedding-3-small`
- dimensions: `1536`
- config fingerprint: `bb14a521b811468f796d06ff67938d34`

Coverage audit:

- eligible retrieval chunks: `492`
- matching current embeddings: `492`
- missing current embeddings: `0`
- stale current embeddings: `0`
- wrong dimensions: `0`
- duplicate current model/input representations: `0`

Idempotency rerun confirmed:

- `already_current: 492`
- `pending_generation: 0`

Embedding verdict:

- `100%` current eligible embedding coverage

## 11. Retrieval Corpus Alignment

Alignment audit:

- FTS chunks: `492`
- semantic input chunks: `492`
- semantic embedded chunks: `492`
- FTS chunks absent from semantic input: `0`
- semantic input chunks absent from FTS: `0`
- FTS chunks absent from semantic embedded corpus: `0`
- semantic embedded chunks absent from FTS: `0`

Alignment verdict:

- FTS, semantic, and hybrid retrieval operate over the same intended current active corpus
- no hidden eligibility mismatch exists

## 12. Hybrid Retrieval Readiness

Verified implementation properties:

- approved policy `rrf_policy_weighted`: present
- approved RRF parameter `k = 20`: present
- approved candidate depth `10`: present
- approved governed modifiers: present and match 5.6A/5.6B
- explainable score components: present
  - `fts_rank`
  - `semantic_rank`
  - `rrf_fts_score`
  - `rrf_semantic_score`
  - `rrf_base_score`
  - `policy_modifier`
  - `final_score`
- query-specific hacks: none found
- document-specific hardcoded boosts: none found
- LLM dependency in retrieval path: none found
- surface privacy: preserved

Hybrid-readiness verdict:

- production private hybrid retrieval conforms to the approved design

## 13. Retrieval Regression Results

Current production rerun:

- original fixture:
  - FTS `Hit@1 9/13`, `Hit@3 11/13`
  - Semantic `Hit@1 11/13`, `Hit@3 13/13`
  - Hybrid `Hit@1 13/13`, `Hit@3 13/13`, `Preferred Before Secondary 13/13`
- holdout fixture:
  - FTS `Hit@1 1/4`, `Hit@3 1/4`
  - Semantic `Hit@1 2/4`, `Hit@3 4/4`
  - Hybrid `Hit@1 2/4`, `Hit@3 4/4`, `Preferred Before Secondary 4/4`

Diagnostic cases:

- `payment within 14 days`
  - hybrid: `CF-003`, `CF-007`, `CF-005`
- `can we bring our own catering`
  - hybrid preserves explicit external-caterer guidance first
- `can we visit the venue beforehand`
  - hybrid preserves `TPL-008` above general access clauses
- `security deposit`
  - hybrid preserves `CF-007` first
- `when does the remaining balance need to be paid`
  - hybrid preserves the correct top result
  - known `TPL-013` vs `CF-007` secondary-order quirk remains

Regression verdict:

- no regression from approved 5.6B production behavior was found

## 14. Known Retrieval Limitations

| Limitation | Classification | Audit Conclusion |
| --- | --- | --- |
| remaining-balance secondary ordering | `ACCEPTED_PHASE_5_LIMITATION` | correct top result is preserved; no Phase 5 retuning justified |
| holdout `Hit@1 2/4` | `ACCEPTED_PHASE_5_LIMITATION` | holdouts remain useful and reviewable; Phase 5 never required `4/4` |
| small evaluation fixture size | `DEFER_TO_PHASE_6` | future retrieval-quality work should expand evaluation breadth |
| exact search rather than ANN | `FUTURE_OPTIMIZATION` | current corpus size does not justify ANN complexity |
| semantic false-positive tendency before policy weighting | `NOT_APPLICABLE` | this was the problem 5.6 solved; residual behavior is acceptable |
| limited chunk-level rule-link coverage | `ACCEPTED_PHASE_5_LIMITATION` | current narrow coverage is intentional and evidence-based |
| lack of exact historical rule-version links | `ACCEPTED_PHASE_5_LIMITATION` | no missing evidence-based exact links were discovered |

## 15. Security Readiness

Local equivalent security audit findings:

- public knowledge tables without RLS: none
- private table grants to `anon`/`authenticated`/`service_role`/`PUBLIC`: none
- search routine grants to ordinary client roles: none
- `api` knowledge-retrieval functions: none
- FTS search: private
- semantic search: private
- hybrid search: private

Phase 4 public contract still present:

- `current_booking_fee_rules`
- `current_cancellation_rules`
- `current_capacity_rules`
- `current_catering_supplier_rules`
- `current_expedited_surcharge_rules`
- `current_facilitator_requirement_rules`
- `current_operational_requirements`
- `current_payment_rules`
- `current_service_rules`
- `current_space_access_rules`
- `current_technical_capability_rules`
- `current_technical_equipment_inventory`

Security verdict:

- no unintended public knowledge-retrieval surface exists

## 16. Storage Readiness

Observed buckets:

- `rental-knowledge` private
- `rental-templates` private

Deferred buckets absent as expected:

- `rental-examples`
- `rental-client-files`

Bootstrap posture remains valid:

- no source binaries were uploaded into Storage during controlled bootstrap
- repository-backed and manual-reference provenance remains the current accepted source-of-truth arrangement

Storage verdict:

- Phase 5 storage posture is ready

## 17. Deterministic Rebuild

Rebuild sequence completed on August 7, 2026:

1. `npx supabase db reset`
   - passed
2. `npx supabase test db`
   - passed
3. `python3 -m unittest discover -s tools/phase_05_chunking/tests -v`
   - passed with `23` tests
4. `python3 -m unittest discover -s tools/phase_05_search/tests -v`
   - passed with `24` tests
5. `python3 -m tools.phase_05_chunking.generate_bulk --load-db`
   - passed
6. `python3 -m tools.phase_05_search.generate_embeddings`
   - passed with `492 / 492` coverage
7. `python3 -m tools.phase_05_search.generate_embeddings`
   - passed idempotently with `already_current: 492`
8. `python3 -m tools.phase_05_search.evaluate_hybrid`
   - passed and rewrote the production evaluation report

Determinism verdict:

- structural determinism: `PASS`
- input/model/config determinism: `PASS`
- provider vector-value bit identity: not required and not asserted

## 18. Test Inventory

Current test inventory:

- DB test files: `21`
- DB assertions: `459`
- parser/chunker Python tests: `23`
- search/semantic/hybrid Python tests: `24`
- total Python deterministic tests in the current Phase 5 chunking/search layer: `47`

Major invariants covered:

- governance schema and typed Phase 4 rule surfaces
- Phase 5 catalogue and provenance integrity
- chunking eligibility and parser correctness
- chunk-rule connectivity
- FTS search surface
- semantic embedding and vector search surface
- hybrid retrieval fusion, modifiers, filters, explainability, and privacy

Known invariant without deeper dedicated coverage:

- no standalone automated audit currently asserts the source-matrix-to-catalogue reconciliation decision that models `CF-002` as a source representation under `CF-001` rather than as its own current logical document

Assessment:

- this is a documentation/audit gap, not an architecture defect

## 19. Architecture Conformance

Frozen entity conformance:

- public entities implemented:
  - knowledge documents
  - corpus-state history
  - document versions
  - categories
  - audiences
  - confidentiality levels
  - source roles
  - source objects
  - version/source links
  - version/audience links
  - version/rental-type links
  - document logical-rule links
  - document exact-rule links
- private entities implemented:
  - processing
  - chunk sets
  - chunk-set sources
  - chunk sources
  - chunks
  - chunk logical-rule links
  - chunk exact-rule links
  - embedding models
  - embeddings
- later retrieval surfaces implemented:
  - `private.current_knowledge_chunks`
  - `private.current_knowledge_chunk_embedding_inputs`
  - `private.search_knowledge_chunks`
  - `private.search_knowledge_chunks_semantic`
  - `private.search_knowledge_chunks_hybrid`

Conformance verdict:

- implemented: all frozen Phase 5 entities required by the brief
- intentionally deferred: deferred sources and later application-layer exposure
- renamed with documented reason: none material
- not implemented unexpectedly: none found

## 20. Phase 5 Definition-of-Done Assessment

Original objective:

> Build a versioned, searchable knowledge base linked to structured Phase 4 rules.

Original completion condition:

> Every active document is versioned/searchable and connected to structured rules where applicable.

Assessment:

- Versioned: `PASS`
  - all represented logical documents have governed versions
- Searchable: `PARTIAL`
  - `21` active documents are retrieval-eligible
  - `CF-001` remains active but unsearchable because no safe parser exists for the available representation
  - `OPS-001` remains intentionally excluded from retrieval because it is still a controlled draft
- Source-traceable: `PARTIAL`
  - structural traceability is complete
  - `CF-001` still lacks the editable master and still carries the export-format discrepancy
- Governed: `PASS`
  - no missing governance metadata defect was found
- Linked to Phase 4 rules where applicable: `PASS`
  - stable link coverage exists where approved
  - no missing evidence-based exact-link defect was found
- Secure/private by default: `PASS`
  - no unintended public retrieval surface was found

Interpretation:

- the only non-PASS areas are already-known, explicitly documented Phase 5 limitations rather than newly discovered architecture defects

## 21. Remaining Issues Classification

| Issue | Classification |
| --- | --- |
| `CF-001` missing editable master | `ACCEPTED_PHASE_5_LIMITATION` |
| `CF-001` PNG/PDF provenance-format mismatch | `ACCEPTED_PHASE_5_LIMITATION` |
| `CF-001` no safe current parser | `ACCEPTED_PHASE_5_LIMITATION` |
| `GOV-002` lifecycle wording drift | `ACCEPTED_PHASE_5_LIMITATION` |
| `GOV-003` lifecycle wording drift | `ACCEPTED_PHASE_5_LIMITATION` |
| `OPS-001` remains controlled draft and non-retrieval-eligible | `ACCEPTED_PHASE_5_LIMITATION` |
| `TPL-004` and `TPL-005` lack canonical rental-type links | `ACCEPTED_PHASE_5_LIMITATION` |
| remaining-balance secondary ordering quirk | `ACCEPTED_PHASE_5_LIMITATION` |
| holdout fixture `Hit@1 2/4` | `ACCEPTED_PHASE_5_LIMITATION` |
| small retrieval evaluation fixture | `DEFER_TO_PHASE_6` |
| ANN/vector-scale optimization | `FUTURE_OPTIMIZATION` |
| exact historical rule-version linking expansion | `DEFER_TO_PHASE_6` |
| later answer-generation/RAG/application surfaces | `DEFER_TO_PHASE_7` |

No issue discovered in this audit is classified as `BLOCKS_PHASE_5_CLOSURE`.

## 22. Closure Recommendation

Recommendation:

- Phase 5 is complete enough to close from an engineering, governance, retrieval, provenance, and security perspective
- the remaining issues are documented and non-blocking
- the implemented system satisfies the approved retrieval architecture and clean-rebuild requirement

PHASE_5_READY_TO_CLOSE
