# Phase 6 Historical Case Repository Dependency Audit

Date: August 7, 2026

## 1. Executive Summary

The repository is structurally ready for Phase 6 discovery work, but it does not already contain a correct first-class model for stable historical rental cases.

Strongest reuse opportunities:

- Phase 4 already exposes stable logical rule identity through `public.logical_rules.rule_code` and exact historical rule-version identity through `public.rule_catalogue.id`.
- Phase 5 already provides reusable governed-document identity, generic source-object identity, provenance-trace conventions, chunking/search artifact boundaries, and private retrieval/security posture.
- The existing `public.knowledge_source_objects` model is generic enough to represent physical or referenced evidence artifacts such as repository files, Supabase Storage files, external URIs, or manual references.

Strongest semantic boundaries:

- Phase 4 remains deterministic truth and must not be redefined by precedent.
- Phase 5 remains current governed knowledge and must not be contaminated by historical-case semantics.
- Phase 6 historical cases are neither current policy documents nor ordinary Phase 5 knowledge documents.

Most important dependency findings:

- No existing entity correctly represents one stable historical rental case.
- `public.knowledge_document_version_source_objects` is explicitly governed-document-version-centric, so it is not a semantically clean direct association model for future case evidence.
- Current retrieval surfaces are intentionally built around `private.current_knowledge_chunks`, which filters to current governed knowledge only; naïvely adding historical cases to that pool would blur authority and result meaning.
- Existing private storage and RLS posture are reusable, but historical evidence introduces materially higher confidentiality and personal-information risk than the current Phase 5 bootstrap corpus.

Audit conclusion:

- a dedicated Phase 6 case identity layer is likely required
- generic source-object identity is reusable
- current knowledge, historical precedent, and raw evidence should remain explicitly separated
- nothing discovered here blocks Task 6.0B corpus audit work

## 2. Existing Architecture Relevant to Phase 6

### Phase 4 entities

- `public.logical_rules` in [supabase/migrations/20260806000100_phase_05_core_governance_foundation.sql](../../supabase/migrations/20260806000100_phase_05_core_governance_foundation.sql) provides one stable logical rule row per `rule_code`.
- `public.rule_catalogue` in [supabase/migrations/20260803000100_phase_04_foundation.sql](../../supabase/migrations/20260803000100_phase_04_foundation.sql) provides exact rule-version rows keyed by `id`, with immutable historical versioning via repeated `rule_code`, `rule_version`, `status`, and `supersedes_rule_id`.
- Phase 4 typed rule tables use `rule_id bigint primary key references public.rule_catalogue(id)`, so each typed row is an exact rule-version extension, not a stable logical parent.
- Canonical reusable scope entities already exist in `public.rental_types` and `public.venue_spaces`.
- `public.technical_equipment_inventory` is current mutable reference data rather than historical rule-version data and should therefore be treated differently from `rule_catalogue`-backed domains.

### Phase 5 entities

- `public.knowledge_documents` provides stable logical current-knowledge identity via `id` and unique `document_code`.
- `public.knowledge_document_versions` provides exact governed document-version identity via `id`, version numbering, governance status, authority classification, confidentiality, and effective dates.
- `public.knowledge_document_corpus_states` provides append-oriented corpus inclusion history for current knowledge only.
- `public.knowledge_source_objects` provides generic physical/source-artifact identity.
- `public.knowledge_document_version_source_objects` provides governed document version to source-object relationships.
- `public.knowledge_document_version_logical_rules` and `public.knowledge_document_version_rule_versions` provide current-knowledge-to-Phase-4 connectivity.
- `private.knowledge_document_version_processing`, `private.knowledge_chunk_sets`, `private.knowledge_chunk_set_sources`, `private.knowledge_chunks`, `private.knowledge_chunk_sources`, `private.knowledge_embeddings`, `private.current_knowledge_chunks`, `private.search_knowledge_chunks(...)`, `private.search_knowledge_chunks_semantic(...)`, and `private.search_knowledge_chunks_hybrid(...)` provide derived/search infrastructure for current governed knowledge.

### Provenance and storage

- `public.source_registry` remains the broader controlled source inventory.
- `public.knowledge_source_objects` bridges optionally back to `source_registry_id` and can exist independently of it.
- Private storage buckets `rental-knowledge` and `rental-templates` are created in [supabase/seed.sql](../../supabase/seed.sql).
- Deferred buckets `rental-examples` and `rental-client-files` are already named in Phase 5 docs but intentionally not created yet.

### Existing explicit historical/example boundary

- `HC-AMO-000` is seeded in `public.source_registry` as `source_type = 'historical_reference'`, `authority_level = 'reference_only'`, `lifecycle_status = 'historical_reference'` in [supabase/seed.sql](../../supabase/seed.sql).
- The source manifest explicitly states that historical cases are reference-only and excluded from authoritative rule retrieval in [docs/phase-04/governance/source-manifest.md](../phase-04/governance/source-manifest.md).
- The Phase 5 source corpus matrix defers `HC-AMO-000` and says it should not be promoted into active governed knowledge in [docs/phase-05/PHASE_5_SOURCE_CORPUS_MATRIX.md](../phase-05/PHASE_5_SOURCE_CORPUS_MATRIX.md).

## 3. Reuse Matrix

| Existing Component | Phase | Current Purpose | Potential Phase 6 Use | Reuse Status | Risks / Constraints |
| --- | --- | --- | --- | --- | --- |
| `public.logical_rules.rule_code` | 4 | Stable logical rule identity | Case relevance / precedent links to stable rule concepts | `REUSE_DIRECTLY` | Safe only if relationship semantics remain non-authoritative |
| `public.rule_catalogue.id` | 4 | Exact historical rule-version identity | Links to exact rule versions encountered in a case | `REUSE_DIRECTLY` | Must not imply current applicability |
| Phase 4 typed rule tables | 4 | Structured exact rule-version values | Reference context only | `REFERENCE_ONLY` | They are exact version extensions, not good generic precedent targets |
| `public.rental_types` | 4 | Canonical rental-type vocabulary | Case applicability tagging | `REUSE_DIRECTLY` | Safe canonical scope dimension |
| `public.venue_spaces` | 4 | Canonical venue-space vocabulary | Case space tagging or issue tagging | `REUSE_DIRECTLY` | Safe canonical scope dimension |
| `public.technical_equipment_inventory` | 4 | Current inventory facts | Context only | `REFERENCE_ONLY` | Not historical by design; should not be treated as case-history truth |
| `public.knowledge_documents` | 5 | Stable current governed knowledge identity | Long-lived case references to current knowledge documents | `REUSE_DIRECTLY` | Only for references to current knowledge, not as case identity |
| `public.knowledge_document_versions` | 5 | Exact governed document versions | Exact references to the current knowledge version reviewed during a case | `REUSE_DIRECTLY` | Version-coupled and current-knowledge-specific |
| `public.knowledge_document_corpus_states` | 5 | Current-knowledge corpus eligibility history | Pattern reference only | `REFERENCE_ONLY` | Its semantics are current knowledge curation, not historical cases |
| `public.knowledge_source_objects` | 5 | Generic source/artifact identity | Historical evidence artifact identity | `REUSE_DIRECTLY` | Artifact identity is reusable, but not case association semantics |
| `public.knowledge_document_version_source_objects` | 5 | Meaning of a source object to a governed document version | Possible design influence only | `DO_NOT_REUSE_SEMANTICALLY` | Hard-coupled to governed document versions |
| `public.knowledge_document_version_logical_rules` | 5 | Current-knowledge-to-logical-rule relationships | Pattern reference only | `REQUIRES_ARCHITECTURE_DECISION` | Semantics like `governed_by` / `explains` are wrong for cases |
| `public.knowledge_document_version_rule_versions` | 5 | Current-knowledge-to-exact-rule-version relationships | Pattern reference only | `REQUIRES_ARCHITECTURE_DECISION` | Case semantics differ from current knowledge semantics |
| `private.knowledge_chunks` and chunk provenance tables | 5 | Derived searchable text with exact provenance | Possible later case-search infrastructure | `REUSE_WITH_NEW_ASSOCIATION_LAYER` | Only if case content stays explicitly distinguishable from current knowledge |
| `private.knowledge_embeddings` and embedding models | 5 | Derived semantic retrieval artifacts | Later case embeddings | `REUSE_WITH_NEW_ASSOCIATION_LAYER` | Same artifact pattern is reusable; shared pool would blur authority unless separated |
| `private.current_knowledge_chunks` | 5 | Current governed retrieval surface | None directly | `DO_NOT_REUSE_SEMANTICALLY` | Explicitly filters to current governed knowledge only |
| `private.search_knowledge_chunks*` functions | 5 | Private retrieval over current governed chunks | Infrastructure reference only | `REUSE_WITH_NEW_ASSOCIATION_LAYER` | Current result shape assumes current governed knowledge |
| RLS, revoked grants, private storage posture | 5 | Keep knowledge private and server-side | Baseline Phase 6 security posture | `REUSE_DIRECTLY` | Historical evidence likely needs even narrower access |
| Deferred buckets `rental-examples`, `rental-client-files` | 5 planning | Reserved storage names | Future historical evidence storage candidates | `REQUIRES_ARCHITECTURE_DECISION` | Not created yet; semantics and access rules still undecided |

## 4. Existing Historical / Example Structures

Relevant structures found:

- `HC-AMO-000` in `public.source_registry` and [supabase/seed.sql](../../supabase/seed.sql)
  - current meaning: a source inventory row for the historical case library file
  - intended for Phase 6: yes, as a deferred later-phase source
  - reuse assessment: usable as source inventory only
  - constraint: it is not a case entity, evidence graph, or retrieval model

- historical case exclusion language in [docs/phase-04/governance/source-manifest.md](../phase-04/governance/source-manifest.md), [docs/phase-04/requirements/rule-classification-register.md](../phase-04/requirements/rule-classification-register.md), and [docs/phase-04/requirements/phase-04-scope.md](../phase-04/requirements/phase-04-scope.md)
  - current meaning: historical cases are examples/precedent only and excluded from authoritative rule activation
  - intended for Phase 6: yes, as a scope boundary
  - reuse assessment: usable as governance baseline

- deferred corpus row `HC-AMO-000` in [docs/phase-05/PHASE_5_SOURCE_CORPUS_MATRIX.md](../phase-05/PHASE_5_SOURCE_CORPUS_MATRIX.md)
  - current meaning: historical/example material intentionally deferred from active current knowledge
  - intended for Phase 6: yes
  - reuse assessment: usable evidence for keeping Phase 6 separate from Phase 5

- deferred bucket names `rental-examples` and `rental-client-files` in [docs/phase-05/implementation/5.2d-storage-controlled-catalogue.md](../phase-05/implementation/5.2d-storage-controlled-catalogue.md) and [docs/phase-05/PHASE_5_CLOSURE.md](../phase-05/PHASE_5_CLOSURE.md)
  - current meaning: reserved storage concepts not yet implemented
  - intended for Phase 6: likely yes
  - reuse assessment: incomplete and not yet active

No existing database model currently represents:

- one stable historical rental case
- one curated case fact set
- one case-to-evidence association
- one case-to-current-knowledge association
- one case-to-rule association
- one case-specific confidentiality/access layer

## 5. Phase 4 Dependency Findings

### Stable rule identity

Current stable rule identity works at two levels:

- stable logical rule identity: `public.logical_rules.rule_code`
- exact rule-version identity: `public.rule_catalogue.id`

This is the same distinction Phase 5 already adopted through:

- `public.knowledge_document_version_logical_rules.rule_code`
- `public.knowledge_document_version_rule_versions.rule_version_id`

### How Phase 5 references Phase 4

Phase 5 document-level relationships:

- `public.knowledge_document_version_logical_rules`
- `public.knowledge_document_version_rule_versions`

Phase 5 chunk-level relationships:

- `private.knowledge_chunk_logical_rules`
- `private.knowledge_chunk_rule_versions`

Important integrity behavior in [supabase/migrations/20260806000500_phase_05_chunk_rule_connectivity.sql](../../supabase/migrations/20260806000500_phase_05_chunk_rule_connectivity.sql):

- chunk-level rule links are allowed only if the parent document version already has the corresponding document-level link
- this preserves top-down semantic scope for current knowledge

### Safe candidates for future Phase 6 references

Safe candidates:

- `public.logical_rules.rule_code` for stable conceptual relevance
- `public.rule_catalogue.id` for exact historical rule-version relevance
- `public.rental_types.id` and `public.venue_spaces.id` for canonical scope tagging

Less safe or reference-only candidates:

- typed Phase 4 rule tables, because they are exact-version extensions rather than a general cross-layer identity surface
- `public.technical_equipment_inventory`, because it is a current mutable fact table, not a historical precedent model

### Semantic requirement

A case-to-rule relationship means relevance or precedent, not authority.

The existing Phase 5 relationship tables are structurally informative but semantically current-knowledge-centric. A future Phase 6 relationship must avoid implying:

- authoritative source for
- defines
- overrides
- governed by

and instead preserve semantics such as:

- relevant_to
- historical_precedent_for
- illustrates
- encountered_issue_related_to

## 6. Phase 5 Dependency Findings

### Stable knowledge identity

Phase 5 has a strong stable/exact identity split:

- stable logical current-knowledge document: `public.knowledge_documents.id` and `document_code`
- exact current-knowledge version: `public.knowledge_document_versions.id`

That makes Phase 5 referenceable from Phase 6 without requiring Phase 6 to become part of Phase 5 governance.

### Versioning and corpus state

Phase 5 versioning is explicit and immutable in practice:

- one logical document may have multiple versions
- only one `active` version per document is allowed
- corpus-state history is append-oriented through `public.knowledge_document_corpus_states`

This pattern is reusable as an implementation precedent, but the actual `knowledge_document_corpus_states` table should remain Phase-5-specific because it encodes current knowledge inclusion decisions, not historical case lifecycle.

### Provenance and evidence

What Phase 6 can safely reuse:

- generic source-object identity in `public.knowledge_source_objects`
- optional bridge to `public.source_registry`
- origin-type model: `repository_file`, `supabase_storage`, `external_uri`, `manual_reference`
- personal-information tri-state on source objects
- checksum, MIME type, file size, and origin-locator constraints

What should remain isolated:

- `public.knowledge_document_version_source_objects`, because it encodes what a source object means to a governed knowledge document version
- document-level current-knowledge relationship tables, because their semantics are tied to current governed documents
- current-knowledge categories and corpus eligibility, because they are tuned to active governed knowledge retrieval rather than precedent

### Current-knowledge references from future cases

For long-lived case references, the available reference targets are:

- `public.knowledge_documents.id` or `document_code` when the relationship should survive new versions
- `public.knowledge_document_versions.id` when the case needs to preserve the exact document version used at the time

This is a real distinction the later architecture will have to choose per relationship type.

### What must not be blurred

Phase 5 is current governed knowledge. Phase 6 is historical precedent.

Therefore the following Phase 5 patterns should not be reused semantically:

- treating a case as another `knowledge_document`
- treating case evidence as `knowledge_document_version_source_objects`
- treating precedent eligibility as `knowledge_document_corpus_states`
- treating case retrieval as `current_knowledge_chunks`

## 7. Source Provenance / Evidence Assessment

### Can existing source provenance support future historical evidence?

Partially yes.

Reusable elements:

- `public.source_registry` as a broader source inventory and authority/lifecycle register
- `public.knowledge_source_objects` as generic artifact identity
- origin types and locator integrity
- optional repository path, storage bucket/key, external URI, or manual reference
- `personal_information_status` and notes
- chunk/source provenance patterns as a design precedent for derived artifacts

Coupling limitations:

- `public.knowledge_document_version_source_objects` is explicitly coupled to `public.knowledge_document_versions`
- `private.knowledge_chunk_set_sources` and `private.knowledge_chunk_sources` are then coupled again to document-version source links
- existing provenance-to-search lineage assumes current governed document versions as the parent object

Architecture implication:

- generic source identities appear reusable independently of Phase 5 governed knowledge documents
- evidence association itself is not generic today
- a future Phase 6 architecture will likely need its own case-evidence association layer, or equivalent, if it wants to reuse `knowledge_source_objects` without semantic overloading

Raw evidence concerns for Phase 6:

- emails
- proposals
- agreements
- schedules
- handover files
- internal notes
- client files

These are more likely than the current Phase 5 bootstrap corpus to contain names, contact details, private commercial negotiations, and case-specific operational issues.

## 8. Retrieval Boundary Assessment

### Current retrieval pipeline

Current retrieval is intentionally limited to current governed knowledge:

- `private.current_knowledge_chunks` in [supabase/migrations/20260807000100_phase_05_full_text_search_foundation.sql](../../supabase/migrations/20260807000100_phase_05_full_text_search_foundation.sql)
- `private.search_knowledge_chunks(...)`
- `private.search_knowledge_chunks_semantic(...)`
- `private.search_knowledge_chunks_hybrid(...)`

Eligibility assumptions in `private.current_knowledge_chunks`:

- current corpus row only: `knowledge_document_corpus_states.is_current`
- included corpus status only: `corpus_status = 'include'`
- current governed knowledge only: `knowledge_document_versions.governance_status = 'active'`
- effective-date eligible only
- current chunk set only: `generation_status = 'current'`

Tests in [supabase/tests/19_phase_05_full_text_search_foundation.sql](../../supabase/tests/19_phase_05_full_text_search_foundation.sql) confirm that:

- superseded chunk sets are excluded
- deferred documents are excluded
- draft document versions are excluded
- future-dated active versions are excluded

### What breaks if historical precedent is added naïvely

If historical cases were mixed directly into the current Phase 5 retrieval pool:

- result meaning would blur because the current pool is intentionally “current governed knowledge”
- ranking modifiers are tuned to current knowledge categories, not precedent weight
- returned metadata does not include an explicit historical/current layer flag
- `authority_classification` alone would not cleanly distinguish current governed knowledge from precedent
- current retrieval surfaces would no longer guarantee that all results are current governed knowledge

### Existing retrieval components that appear reusable

Potentially reusable later:

- chunking and chunk provenance patterns
- FTS indexing pattern
- embedding-model registry
- embedding artifact storage pattern
- exact vector search infrastructure
- RRF scoring infrastructure shape

Not reusable semantically without a new boundary:

- `private.current_knowledge_chunks`
- direct use of Phase 5 category modifiers for precedent
- current result pool assumptions

Required invariants for later architecture:

- explicit source role or layer distinction
- explicit authority distinction
- separate eligibility semantics from current governed knowledge
- ability to label results as historical precedent
- ability to keep current knowledge and historical evidence separately searchable even if some shared infrastructure is reused

## 9. Security & Confidentiality Assessment

### Existing controls Phase 6 can inherit

Acceptable existing controls:

- RLS is enabled across the Phase 5 knowledge-governance tables and private artifact tables
- grants are revoked from `public`, `anon`, `authenticated`, and ordinary `service_role` access surfaces where appropriate
- retrieval functions are private/server-side only
- storage buckets created so far are private only
- confidentiality taxonomy already exists:
  - `externally_shareable`
  - `internal`
  - `commercially_sensitive`
  - `restricted`
- `knowledge_source_objects.personal_information_status` already anticipates privacy review

### Additional risks introduced by historical evidence

Architecture requirements:

- raw evidence may include personal information not present in current bootstrap documents
- historical case files may contain client identities, email content, attachments, schedules, internal notes, and negotiation history
- a curated case summary may need broader access than the underlying raw evidence
- search leakage risk is materially higher if raw evidence later becomes searchable alongside summaries or lessons

Implementation considerations:

- current seed posture leaves personal-information status as `unknown` for current Phase 5 source objects
- that is acceptable for bootstrap current knowledge but too weak for a mature historical-evidence layer
- historical evidence and case summaries may require different confidentiality classification and different retrieval eligibility

No current repository finding blocks 6.0B, but later Phase 6 architecture will need tighter visibility separation than Phase 5 current knowledge alone.

## 10. Governed vs Derived Boundary

Existing repository conventions already separate canonical/governed records from derived/search artifacts:

- governed identities: `rule_catalogue`, `logical_rules`, `knowledge_documents`, `knowledge_document_versions`
- source evidence/artifacts: `source_registry`, `knowledge_source_objects`, version/source links
- derived processing state: `private.knowledge_document_version_processing`
- derived chunk sets and chunks: `private.knowledge_chunk_sets`, `private.knowledge_chunks`
- derived provenance-to-search artifacts: `private.knowledge_chunk_set_sources`, `private.knowledge_chunk_sources`
- derived embeddings: `private.knowledge_embeddings`
- derived search surfaces: `private.current_knowledge_chunks`, FTS/semantic/hybrid functions

Applied to future Phase 6, the audit supports preserving distinct boundaries between:

- stable case identity
- historical source evidence
- curated case facts
- human-authored lessons / precedent interpretation
- generated summaries
- generated tags
- embeddings
- retrieval/search indexes

The repository strongly supports keeping these layers separate. It does not support flattening them into one generic “case document” concept without losing semantic clarity.

## 11. Open Architecture Questions for Task 6.1

1. Should Phase 6 introduce a dedicated stable case entity, or is there a defensible extension path that still avoids overloading `knowledge_documents`?
2. Should case evidence reuse `knowledge_source_objects` with a new association layer, or should Phase 6 define a parallel artifact model?
3. When a case references Phase 4, which relationships should point to `logical_rules.rule_code` versus exact `rule_catalogue.id`?
4. When a case references Phase 5, which relationships should point to `knowledge_documents` versus `knowledge_document_versions`?
5. Should case lessons and curated precedent be versioned/governed separately from raw evidence?
6. How should historical case confidentiality be separated between raw evidence and curated case summaries?
7. Should future case retrieval use shared chunking/embedding infrastructure with explicit layer separation, or separate materialized pools?
8. What case relationship vocabulary is needed so precedent links do not imply authority?
9. Should deferred buckets `rental-examples` and `rental-client-files` map directly to Phase 6 concepts, or are different storage boundaries required?
10. How should generated summaries, tags, and embeddings be marked so they never masquerade as governed case facts?

## 12. Blockers / Contradictions

| ID | Issue | Evidence | Affected Component | Severity | Blocks 6.0B | Blocks 6.1 |
| --- | --- | --- | --- | --- | --- | --- |
| `P6-AUDIT-001` | No existing stable historical-case entity exists. | No table or seed model represents one rental case; `HC-AMO-000` exists only as a deferred source row in `public.source_registry` and Phase 5 corpus docs. | Phase 6 case identity | architecture requirement | no | yes, until decided |
| `P6-AUDIT-002` | Existing provenance association is governed-document-version-specific. | `public.knowledge_document_version_source_objects` ties source objects to `knowledge_document_versions`; chunk provenance is then chained through that parent. | Phase 6 evidence association | architecture requirement | no | yes, until decided |
| `P6-AUDIT-003` | Current retrieval surfaces assume every result is current governed knowledge. | `private.current_knowledge_chunks` filters to `include` + `active` + effective-date-eligible + `current` chunk sets; tests confirm deferred/draft/superseded exclusion. | Future case retrieval boundary | architecture requirement | no | yes, until designed |
| `P6-AUDIT-004` | Historical evidence likely introduces higher confidentiality and personal-information risk than current Phase 5 bootstrap sources. | Deferred buckets `rental-examples` and `rental-client-files`; `HC-AMO-000` is marked internal historical/reference-only; `knowledge_source_objects.personal_information_status` currently defaults to `unknown`. | Phase 6 security and visibility | implementation consideration | no | no |

No contradiction was found that blocks Task 6.0B corpus audit work.

## 13. Readiness Decision

`READY_FOR_6_0B`

Reason:

- the repository baseline is clear
- the Phase 4 and Phase 5 reuse boundaries are now explicit
- no discovered issue prevents the next task from auditing the historical case corpus itself
- the unresolved items are architecture questions for Task 6.1, not blockers to 6.0B
