# Phase 5 Closure

Date: August 7, 2026

## 1. Phase 5 Objective

Phase 5 objective:

> Build a governed, versioned, searchable organizational knowledge base connected to Phase 4 structured rules.

Phase 5 does not mean:

- AI answer generation
- RAG orchestration
- client dossier assembly
- automated proposal generation
- Phase 6 historical case reasoning
- Phase 7 agent or application behavior

## 2. Final Phase 5 Status

Phase 5 is:

- `PHASE_5_COMPLETE`
- `PHASE_5_READY_FOR_DOWNSTREAM_USE`

Meaning:

- later phases may now depend on the governed and searchable knowledge layer
- this does not imply a public application layer is complete
- this does not imply a public retrieval API is complete

## 3. Final Corpus Snapshot

Audited final counts:

- logical knowledge documents: `24`
- current corpus decision rows: `24`
- current active include documents: `22`
- current draft include documents: `2`
- current chunk sets: `22`
- current chunks: `525`
- retrieval-eligible documents: `21`
- retrieval-eligible chunks: `492`
- current embeddings: `492`
- embedding coverage: `100%`

Current rule connectivity counts:

- stable document-level logical-rule links: `42`
- exact document-level rule-version links: `0`
- stable chunk-level logical-rule links: `10`
- exact chunk-level rule-version links: `0`

The zero exact-link counts are preserved intentionally. The current source set does not justify exact historical rule-version linking beyond the stable logical links already implemented.

## 4. Current Retrieval Stack

Implemented retrieval path:

```text
Governed document
-> governed version
-> source provenance
-> semantic chunks
-> FTS
-> embeddings/vector search
-> deterministic hybrid retrieval
```

Approved hybrid strategy:

- policy: `rrf_policy_weighted`
- RRF `k = 20`
- candidate depth per substrate: `10`

Implemented governed category modifiers:

- `operational_procedure`: `+0.011`
- `communication_guidance`: `+0.009`
- `service_supplier_guidance`: `+0.007`
- `technical_venue_reference`: `+0.007`
- `client_facing_controlled_document`: `+0.005`
- `proposal_guidance`: `+0.001`
- `governance_canonical`: `-0.010`

## 5. Final Retrieval Quality Snapshot

Original fixture:

- FTS: `Hit@1 9 / 13`, `Hit@3 11 / 13`
- Semantic: `Hit@1 11 / 13`, `Hit@3 13 / 13`
- Hybrid: `Hit@1 13 / 13`, `Hit@3 13 / 13`, `Preferred Before Secondary 13 / 13`

Holdout:

- FTS: `Hit@1 1 / 4`, `Hit@3 1 / 4`
- Semantic: `Hit@1 2 / 4`, `Hit@3 4 / 4`
- Hybrid: `Hit@1 2 / 4`, `Hit@3 4 / 4`, `Preferred Before Secondary 4 / 4`

Closure interpretation:

- holdout `Hit@1 2 / 4` is an accepted Phase 5 limitation
- Phase 5 closure does not require additional tuning
- the production hybrid layer preserves the approved 5.6B behavior without regression

## 6. Final Search And Embedding Configuration

### FTS

- PostgreSQL full-text search
- weighted `tsvector`
- GIN index present: `knowledge_chunks_search_vector_gin_idx`
- current-knowledge eligibility enforced

### Semantic

- provider: `openai`
- model: `text-embedding-3-small`
- dimensions: `1536`
- config fingerprint: `bb14a521b811468f796d06ff67938d34`
- embedding coverage: `492 / 492`
- similarity: cosine
- vector search: exact search

### Optimization Boundary

- ANN indexes: not implemented
- classification: `FUTURE_OPTIMIZATION`

Phase 5 closure does not add HNSW or IVFFlat.

## 7. Final Security Posture

Approved Phase 5 posture:

- Phase 5 implementation data is private and server-side
- no approved `anon` Phase 5 knowledge access exists
- no approved ordinary `authenticated` Phase 5 knowledge access exists
- public Phase 4 read contract remains the `public.current_*` surface
- FTS surface is private
- semantic search is private
- hybrid retrieval is private
- no Phase 5 public retrieval RPC exists
- RLS is enabled where required
- no client policies exist for the private knowledge tables

The previously identified 26-table RLS-disabled advisory is resolved.

## 8. Final Storage Posture

Private buckets:

- `rental-knowledge`
- `rental-templates`

Deferred buckets:

- `rental-examples`
- `rental-client-files`

Current accepted bootstrap posture:

- no source binaries were uploaded during controlled bootstrap
- repository-backed and manual-reference provenance remain the accepted source-of-truth posture for current Phase 5 sources

## 9. Final Test Snapshot

Audited validation inventory:

- DB test files: `21`
- DB assertions: `459`
- parser or chunker Python tests: `23`
- search, semantic, or hybrid Python tests: `24`
- total current Phase 5 chunking and search Python deterministic tests: `47`

Clean rebuild validation passed on August 7, 2026:

1. `npx supabase db reset`
2. `npx supabase test db`
3. `python3 -m unittest discover -s tools/phase_05_chunking/tests -v`
4. `python3 -m unittest discover -s tools/phase_05_search/tests -v`
5. `python3 -m tools.phase_05_chunking.generate_bulk --load-db`
6. `python3 -m tools.phase_05_search.generate_embeddings`
7. `python3 -m tools.phase_05_search.generate_embeddings`
8. `python3 -m tools.phase_05_search.evaluate_hybrid`

## 10. Definition-Of-Done Closure

Final Phase 5 criteria assessment:

- Versioned: `PASS`
- Governed: `PASS`
- Searchable: `PASS WITH ACCEPTED EXCEPTION`
- Source-traceable: `PASS WITH ACCEPTED EXCEPTION`
- Linked to Phase 4 rules where applicable: `PASS`
- Secure and private by default: `PASS`

Accepted exceptions:

- `CF-001` has no safe parser or retrieval-suitable editable source representation
- `CF-001` editable-master and provenance-format limitations remain documented

Overall definition-of-done result:

- `PASS`

## 11. Accepted Phase 5 Limitations

`CF-001`

- missing editable master
- PNG or PDF provenance-format mismatch
- no safe parser
- remains governed but not searchable

`GOV-002`

- lifecycle wording drift remains documented

`GOV-003`

- lifecycle wording drift remains documented
- remains draft and non-current

`OPS-001`

- controlled draft
- chunked
- intentionally excluded from active retrieval

`TPL-004` and `TPL-005`

- no canonical rental-type links
- accepted modeling decision

Retrieval

- remaining-balance secondary ordering quirk
- holdout `Hit@1 2 / 4`
- small retrieval evaluation set

Rule connectivity

- limited chunk-level rule mapping
- zero exact historical rule-version links because the evidence does not justify them

## 12. Deferred Work Register

Phase 6:

- `rental-examples`
- historical rental cases
- unusual or difficult cases
- broader retrieval-evaluation expansion where useful
- evidence-based exact historical rule links if future cases justify them

Phase 7:

- retrieval orchestration
- context packs
- answer generation
- RAG
- client or rental dossier assembly
- proposal generation
- public or internal application APIs
- role-based UI access
- n8n, Outlook, or Asana integration where later approved

Future optimization:

- ANN, HNSW, or IVFFlat
- broader retrieval fixture
- additional ranking tuning
- additional chunk-rule mapping

## 13. Handover Invariants

Future phases must not violate these Phase 5 invariants:

1. Phase 4 remains deterministic truth for structured rental rules.
2. Phase 5 free text never overrides Phase 4 rule values.
3. Current retrieval must use governed current eligibility.
4. Deferred or historical knowledge must not silently become current.
5. Document provenance must remain source-traceable.
6. Chunk regeneration must not mutate governed document versions.
7. Embeddings remain derived and regenerable artifacts.
8. Retrieval ranking must remain deterministic unless later architecture explicitly approves otherwise.
9. Security and private posture must not be weakened accidentally.
10. Rule-policy changes must flow through the WNC governance and change-log process plus the controlled source documents.

## 14. Architecture Freeze Record

This is the frozen Phase 5 implementation baseline.

Governed public entities:

- logical rules
- knowledge documents
- document versions
- corpus-state history
- categories
- audiences
- confidentiality
- source objects
- provenance relationships
- rental applicability
- document-level rule connectivity

Derived private entities:

- processing state
- chunk sets
- chunk-set source provenance
- chunk source provenance
- chunks
- chunk-level rule connectivity
- embedding models
- embeddings

Retrieval surfaces:

- current knowledge chunks
- FTS
- semantic search
- hybrid retrieval

## 15. Handoff Boundary

Phase 5 closes the governed retrieval foundation only.

It does not close:

- user-facing applications
- LLM answer generation
- workflow automation
- live rental or client records
- proposal assembly
- downstream reasoning behavior

Those remain later-phase responsibilities.

## 16. Closure Basis

This closure record is based on the audited repository state captured in [PHASE_5_RETRIEVAL_READINESS_AUDIT.md](./PHASE_5_RETRIEVAL_READINESS_AUDIT.md).

The readiness audit found no engineering, governance, provenance, retrieval, integrity, or security defect that blocks closure.

## 17. Closure Decision

Phase 5 is formally closed as:

- `PHASE_5_COMPLETE`
- `PHASE_5_READY_FOR_DOWNSTREAM_USE`

Accepted limitations remain documented and non-blocking. Future work should build on this governed, versioned, searchable foundation rather than reopening the completed Phase 5 baseline.
