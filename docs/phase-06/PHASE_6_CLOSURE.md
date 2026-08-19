# Phase 6 Closure

Date: August 8, 2026

## 1. Closure Status

Phase 6 is:

- `PHASE_6_COMPLETE`
- `PHASE_6_READY_FOR_DOWNSTREAM_USE`

Meaning:

- the governed historical case and precedent layer is complete and frozen for downstream use
- Phase 6 may now be used as the historical precedent layer beneath later orchestration work
- this does not imply current+historical fusion, answer generation, RAG, agents, workflows, or Phase 7 are complete

## 2. Phase Objective

Phase 6 exists to provide the governed Historical Case / Precedent Layer.

It preserves:

- what happened in prior WNC rentals
- operational complications and edge cases
- responsibility splits
- case-specific decisions
- lessons and cautions
- historical precedent relevant to unusual future rentals

It does not establish current policy. Authority order remains:

`Phase 4 deterministic rules`
-> `Phase 5 governed current knowledge`
-> `Phase 6 historical precedent`

## 3. Final Architecture

Final Phase 6 architecture:

```text
Stable historical case identity
-> governed versioning
-> source objects and case-specific locators
-> responsibilities / decisions / lessons with statement provenance
-> Phase 4 and Phase 5 stable authority connectivity
-> derived governed historical search units
-> historical FTS
-> historical embeddings / semantic retrieval
-> deterministic historical hybrid retrieval
-> server-side integration contract
```

Frozen architectural baseline:

- stable case identity is separate from evidence artifacts
- active corpus updates occur through superseding versions, not in-place mutation
- raw evidence remains separate from curated governed historical knowledge
- statement-level contamination control survives ingestion and retrieval
- derived search units remain a separate private historical retrieval layer
- the stable integration entry point is `tools.phase_06_search.historical_retrieval.retrieve_historical_precedents(...)`
- the documented CLI wrapper exists in `tools/phase_06_search/historical_retrieval.py`
- the integration input contract accepts `query_text`, `result_limit`, and optional `case_code`, `unit_type`, `precedent_availability`, `precedent_type`, `lesson_kind`, `historical_value_only`, and `contamination_risk_level`
- healthy retrieval is labeled `hybrid`; degraded semantic state is labeled `fts_fallback`
- integration responses preserve `retrieval_mode_requested`, `retrieval_mode_used`, `fallback_used`, and `fallback_reason`
- healthy hybrid requires embedding-state preflight confirming an active retrieval-approved embedding model plus `missing = 0` and `stale = 0`
- OpenAI key resolution order remains: shell environment -> `.env.local` -> `.env`

## 4. Final Corpus Baseline

Audited production corpus:

- stable historical cases: `9`
- active governed case versions: `9`
- responsibilities: `35`
- decisions: `25`
- lessons: `43`

Final availability:

- `HC-001`: `active`
- `HC-002`: `active`
- `HC-003`: `limited`
- `HC-004`: `limited`
- `HC-005`: `active`
- `HC-006`: `active`
- `HC-007`: `active`
- `HC-008`: `limited`
- `HC-009`: `limited`

Final authority connectivity:

- Phase 4 stable logical-rule relationships: `30`
- Phase 4 exact rule-version relationships: `0`
- Phase 5 stable knowledge-document relationships: `38`
- Phase 5 exact document-version relationships: `0`

The zero exact-version counts remain intentional because the current historical evidence does not justify false temporal precision.

## 5. Retrieval Baseline

Final retrieval metrics:

### FTS

- shared Hit@1: `17 / 21 = 80.95%`
- shared Hit@3: `19 / 21 = 90.48%`

### Semantic

- shared Hit@1: `17 / 21 = 80.95%`
- shared Hit@3: `19 / 21 = 90.48%`
- paraphrase Hit@1: `6 / 8 = 75.00%`
- paraphrase Hit@3: `8 / 8 = 100.00%`

### Hybrid

- shared Hit@1: `19 / 21 = 90.48%`
- shared Hit@3: `21 / 21 = 100.00%`
- paraphrase Hit@1: `6 / 8 = 75.00%`
- paraphrase Hit@3: `8 / 8 = 100.00%`

### Integration

- integrated shared Hit@1: `19 / 21 = 90.48%`
- integrated shared Hit@3: `21 / 21 = 100.00%`
- integrated paraphrase Hit@1: `6 / 8 = 75.00%`
- integrated paraphrase Hit@3: `8 / 8 = 100.00%`
- integrated parity with direct 6.4D hybrid ordering: `true`

Observed retrieval complementarity:

- FTS preserves exact lexical match strength
- semantic complements lexical misses and paraphrase queries
- hybrid preserves exact-match behavior while improving aggregate shared-benchmark recovery
- integrated retrieval preserves the frozen direct-hybrid behavior without ranking drift

## 6. Frozen Production Retrieval Strategy

Frozen production historical hybrid configuration:

- strategy code: `historical_rrf_balanced`
- configuration code: `historical_rrf_balanced_d20`
- RRF formula: `weight * (1 / (k + rank))`
- RRF `k`: `20`
- lexical weight: `1.0`
- semantic weight: `1.0`
- lexical candidate depth: `20`
- semantic candidate depth: `20`

Closure decision:

- the balanced strategy is frozen as the auditable production baseline
- no closure retuning was performed

## 7. Provenance / Governance

Statement provenance completeness:

- responsibilities: `35 / 35`
- decisions: `25 / 25`
- lessons: `43 / 43`

Search-unit provenance completeness:

- current historical search units: `112`
- case narratives: `9`
- responsibilities: `35`
- decisions: `25`
- lessons: `43`
- units with lineage: `112 / 112`
- units with surfaced primary locator: `112 / 112`
- analyst-inference lesson units: `8`

Embedding baseline:

- eligible historical units: `112`
- current embeddings: `112`
- missing embeddings: `0`
- stale embeddings: `0`
- provider: `openai`
- model code: `text-embedding-3-small`
- dimensions: `1536`
- embedding input surface: governed historical `search_text`
- raw evidence is not embedded
- Phase 5 current-knowledge chunks are not embedded

Governance findings:

- one shared Historical Case Library source object remains the primary current source object
- every governed case remains connected through a case-specific source locator
- statement provenance remains version-scoped
- statement provenance resolves through governed evidence associations
- the active corpus remains immutable outside draft/supersession workflows

## 8. Historical-Value / Authority Safeguards

Statement-level safeguards remain intact:

- `historical_value_only`
- `contamination_risk_level`
- `current_authority_disposition`

Protected high-risk examples remain preserved:

- `HC-003`: `EUR 300` storage detail and floral capability statements
- `HC-004`: discount / collaboration judgement
- `HC-006`: overtime and late-build-up handling
- `HC-007`: grace-period misuse, fake snow, cleanup and damage cautions
- `HC-009`: historical legal / compliance solution not treated as current authority

Authority ordering remains frozen:

- if Phase 6 conflicts with Phase 4 or Phase 5, Phase 4 / Phase 5 wins
- historical precedent remains evidence of what happened, not automatic current truth

Accepted retrieval limitation:

- `whole venue clearing` remains:
  - FTS `miss`
  - semantic rank `1`
  - hybrid rank `3`

This remains accepted because:

- semantic recovers the intended case at rank `1`
- hybrid still returns the intended case inside top `3`
- aggregate hybrid Hit@3 is `100.00%`
- the balanced strategy is more auditable than benchmark-specific weighting

## 9. Security / Privacy

Final Phase 6 posture:

- governed historical data remains private and server-side
- historical retrieval functions remain private
- derived historical search units remain private
- historical embeddings remain private
- the integration contract is server-side and internal
- no anonymous or client-facing historical retrieval surface exists
- raw evidence is not directly exposed or directly searchable
- confidentiality and PI metadata remain preserved through derived retrieval units
- retrieval operates over governed historical search units, not raw evidence artifacts
- Phase 6 retrieval does not call Phase 5 FTS, semantic, or hybrid search surfaces
- `private.current_knowledge_chunks` remains unchanged by Phase 6 materialization
- no current+historical fusion surface exists in the frozen Phase 6 baseline

## 10. Regression Baseline

Final verification snapshot:

- database regression: `33` files / `937` tests / `PASS`
- historical integration tests: `6 / 6` / `PASS`

Validated commands:

1. `npx -y supabase@latest test db --local supabase/tests`
2. `python3 -m unittest tools.phase_06_search.tests.test_historical_retrieval -v`

## 11. Accepted Limitations

Accepted Phase 6 limitations:

- the current corpus is primarily based on the curated Historical Case Library
- separate contemporaneous raw case files have not been added
- exact historical dates remain unknown across the current corpus
- limited precedents remain intentionally limited: `HC-003`, `HC-004`, `HC-008`, `HC-009`
- current floral capability is unresolved as current authority
- current deterministic collaboration / discount policy is unresolved as current authority
- exact Phase 4 rule-version links remain `0` by design
- exact Phase 5 document-version links remain `0` by design
- `whole venue clearing` remains hybrid rank `3`
- healthy hybrid requires live query-embedding model availability
- explicit `fts_fallback` exists for degraded semantic state
- Phase 6 alone does not answer current-policy questions

These limitations do not block Phase 6 closure.

## 12. Downstream-Use Contract

Downstream consumers may rely on Phase 6 to answer:

- have we handled something similar before
- what happened in a comparable case
- what responsibilities existed
- what complications occurred
- what decisions were made
- what lessons or cautions were preserved
- which current authority areas should be checked

Downstream consumers may not rely on Phase 6 alone to answer:

- what the current price is
- what fee applies now
- what cancellation rule applies now
- what current capacity applies
- what current legal solution is valid
- what service is currently offered
- what current policy staff must follow

Those remain Phase 4 / Phase 5 questions.

## 13. Maintenance / Versioning Contract

Future historical evidence updates must follow this workflow:

1. do not mutate the active historical case version
2. add or reuse the source object
3. create a new draft historical case version
4. attach new evidence
5. revise the governed reconstruction
6. update statements and relationships where justified
7. validate contamination and current-authority handling
8. supersede the prior active version
9. rebuild derived search units
10. regenerate stale embeddings
11. rerun retrieval validation where materially necessary

Current policy changes do not require rewriting history:

- historical case content remains what happened historically
- current truth must still resolve from Phase 4 / Phase 5
- future current-policy changes must not be copied into historical statements

## 14. Deferred Boundaries

Explicitly deferred beyond Phase 6:

- current+historical retrieval fusion
- cross-layer ranking
- authority-aware retrieval orchestration
- context-pack assembly
- RAG
- answer generation
- agent architecture
- proposal generation
- live client dossiers
- Outlook integration
- n8n integration
- Asana integration
- Phase 7 functionality

## 15. Final Invariants

Frozen Phase 6 invariants:

- `P6-INV-001 — Authority Separation`: Phase 6 never overrides Phase 4 or Phase 5.
- `P6-INV-002 — Stable Case Identity`: Historical cases have stable identity independent of evidence artifacts.
- `P6-INV-003 — Evidence Separation`: Raw evidence remains distinct from curated case knowledge.
- `P6-INV-004 — Historical Applicability`: Historical values and practices cannot be interpreted as current truth without current-authority lookup.
- `P6-INV-005 — Provenance`: Governed historical claims and retrieval units remain traceable to source evidence.
- `P6-INV-006 — Derived Artifact Boundary`: Generated or derived artifacts do not become governed historical fact automatically.
- `P6-INV-007 — Retrieval Role`: Historical precedent remains distinct from current governed knowledge.
- `P6-INV-008 — Confidentiality Separation`: Evidence may be more restricted than curated precedent.
- `P6-INV-009 — Version Supersession`: Active historical cases are updated through superseding versions, not in-place rewriting.
- `P6-INV-010 — Statement-Level Contamination Control`: Risky historical facts remain explicitly marked at statement level.
- `P6-INV-011 — Honest Retrieval Degradation`: degraded semantic state must be explicitly labeled as `fts_fallback`, never misrepresented as healthy hybrid retrieval.

## 16. Closure Decision

Closure assessment:

- objective met: `yes`
- governed corpus frozen: `yes`
- provenance complete: `yes`
- authority separation preserved: `yes`
- retrieval baseline validated: `yes`
- integration parity preserved: `yes`
- security and privacy posture preserved: `yes`
- Phase 5 isolation preserved: `yes`

Formal decision:

- `PHASE_6_COMPLETE`
- `PHASE_6_READY_FOR_DOWNSTREAM_USE`
