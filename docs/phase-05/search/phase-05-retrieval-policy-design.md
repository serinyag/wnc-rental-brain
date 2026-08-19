# Phase 5 Retrieval Policy Design

Date: August 7, 2026

## Scope

This task designs the deterministic retrieval policy that will sit above the existing Phase 5 retrieval substrates:

- PostgreSQL full-text search
- exact cosine semantic search over the governed 492-chunk corpus

This task does not change FTS configuration, embeddings, chunking, corpus eligibility, or answer generation. It only defines how already-retrieved governed chunks should be ordered when multiple relevant results exist.

## Inherited Evidence

The approved Phase 5 baseline results establish:

- FTS remains strong for exact governed terminology.
- Semantic search materially improves paraphrase recall.
- Neither substrate alone fully solves document-role ordering.

Baseline fixture metrics over 13 deterministic queries:

| Retrieval Layer | Hit@1 | Hit@3 | Preferred Before Secondary | Relevant@5 |
| --- | ---: | ---: | ---: | ---: |
| FTS | 9/13 | 11/13 | 10/13 | 0.508 |
| Semantic | 11/13 | 13/13 | 11/13 | 0.723 |

Interpretation:

- FTS is valuable and should not be replaced.
- Semantic search is the stronger candidate generator.
- Retrieval policy must improve top-result usefulness, not just broad relevance.

## Metadata Audit

The current searchable document families expose reusable governed signals without adding schema:

- `knowledge_categories.category_code`
- `knowledge_document_versions.authority_classification`
- current-governed corpus eligibility
- document-level stable rule relationships
- chunk-level stable rule relationships

Observed corpus facts from the current searchable set:

- searchable categories include `client_facing_controlled_document`, `governance_canonical`, `technical_venue_reference`, `service_supplier_guidance`, `communication_guidance`, `operational_procedure`, and `proposal_guidance`
- all searchable documents are already current and governed
- `authority_classification` is not highly discriminative on its own for ranking because most searchable material is already authoritative or approved guidance
- document-level rule links are present across several operational sources
- chunk-level rule links are too sparse to act as a safe corpus-wide ranking signal

Document-level rule-link counts in the searchable set:

- `CF-003` `3`
- `CF-005` `3`
- `CF-007` `2`
- `OPS-002` `6`
- `OPS-003` `3`
- `SERV-001` `6`
- `SERV-003` `5`
- `SERV-004` `3`
- most `TPL-*` operational guidance documents `0`

Chunk-level rule-link counts in the searchable set:

- only `SERV-001` has chunk-rule links in the current corpus snapshot
- all other searchable documents have `0`

Conclusion:

- category is the strongest reusable retrieval-priority signal available today
- governance-category downweighting is defensible
- chunk-rule boosting is not defensible yet
- document-rule boosting is possible in principle, but it is not broad enough to be the primary Phase 5 policy lever

## Retrieval Principles

The evaluation supports these retrieval principles:

1. Semantic relevance and operational retrieval priority are not the same thing.
2. Current operational guidance should usually outrank governance history when both are relevant to an operational rental query.
3. Governance and change-log sources should remain searchable, but usually not first for current operational questions.
4. Exact terminology should keep benefiting from FTS rather than being forced through semantic-first heuristics.
5. Retrieval policy should be corpus-wide and metadata-driven, not query-specific.

## Candidate Strategies Evaluated

### Option A: FTS-first append semantic

Behavior:

- preserves FTS exact-term strength
- fills semantic recall gaps only after FTS ordering

Result:

- Hit@1 `10/13`
- fixes some FTS misses
- still leaves `GOV-002` first for `payment within 14 days`
- still leaves general access clauses above site-visit guidance

Assessment:

- too conservative
- preserves lexical behavior more than operational usefulness

### Option B: Semantic-first append FTS

Behavior:

- uses semantic retrieval as the primary candidate ordering
- keeps FTS only as backfill

Result:

- Hit@1 `11/13`
- preserves paraphrase gains
- still allows semantic false-positive pressure such as kitchen-suitability material above explicit external-caterer guidance
- still leaves venue-access clauses above site-visit guidance

Assessment:

- strongest raw relevance
- not sufficient as a policy by itself

### Option C: Unweighted reciprocal rank fusion

Behavior:

- combines FTS and semantic rankings without pretending raw scores share a scale

Result:

- Hit@1 `11/13`
- better balanced than either substrate alone
- still leaves `GOV-002` first for `payment within 14 days`
- still leaves general access clauses above site-visit guidance

Assessment:

- the right fusion foundation
- not enough without governed modifiers

### Option C2: Reciprocal rank fusion with governed category modifiers

Behavior:

- fuses FTS and semantic rankings
- then applies small category-based policy modifiers

Evaluated modifier set:

- `operational_procedure` `+0.011`
- `communication_guidance` `+0.009`
- `service_supplier_guidance` `+0.007`
- `technical_venue_reference` `+0.007`
- `client_facing_controlled_document` `+0.005`
- `proposal_guidance` `+0.001`
- `governance_canonical` `-0.010`

Result:

- Hit@1 `13/13`
- Hit@3 `13/13`
- Preferred Before Secondary `13/13`
- Relevant@5 `0.692`

Assessment:

- preserves exact-term strength
- preserves semantic paraphrase recall
- fixes the key ordering conflicts without hiding governance material
- best overall Phase 5 candidate

### Option D: Query-family routing

Assessment only, not selected:

- could theoretically separate exact-policy queries from paraphrase/procedural queries
- would require brittle hand-built query classification rules or pseudo-NLP
- would be harder to govern and explain than rank fusion
- was not needed once weighted RRF solved the observed conflicts

Conclusion:

- reject for Phase 5.6A

## Recommended Policy

Recommend:

- deterministic reciprocal rank fusion
- small governed category modifiers
- no query-specific logic
- no document-specific hacks

Production-shape rule:

1. retrieve top candidates from FTS
2. retrieve top candidates from semantic search
3. combine via reciprocal rank fusion
4. apply small category-based modifiers
5. return a single ranked list with governance/history still present but usually lower for operational questions

Why this wins:

- it keeps FTS in the loop for governed terminology
- it keeps semantic retrieval for paraphrase recall
- it corrects document-role ordering problems that neither substrate solves alone
- it remains explainable and uses only existing governed metadata

## Signals Selected

- `knowledge_categories.category_code`
  - selected as the main deterministic proxy for document role
- fused FTS rank
  - selected because exact terminology remains important
- fused semantic rank
  - selected because paraphrase recovery is already proven

## Signals Rejected

- raw score blending across FTS and cosine similarity
  - rejected because the scales are not naturally comparable
- manual per-document boosts or penalties
  - rejected as non-governable and brittle
- query-specific boosts
  - rejected as fixture overfitting
- chunk-rule boost
  - rejected because current chunk-rule coverage is too sparse
- document-rule boost
  - rejected for Phase 5.6A because even small boosts introduced a site-visit ordering regression before they resolved the remaining-balance secondary-order issue
- authority classification as a direct weight
  - audited but not selected because it adds little discrimination beyond existing categories in the current searchable corpus
- corpus eligibility changes
  - rejected because retrieval weighting and corpus governance are separate systems

## Known-Case Outcomes

### Payment

Query:

- `payment within 14 days`

Outcome under recommended policy:

- `CF-003 4.1 Short-Notice Bookings` first
- `CF-007 Fees, payment and security deposit` second
- `GOV-002 DEC-007` third

Interpretation:

- direct operational payment sources now outrank governance history
- governance evidence remains visible in the top 3

### Catering

Query:

- `can we bring our own catering`

Outcome under recommended policy:

- `SERV-003 CBR-002 External caterers` first
- `SERV-003 CBR-001 Kitchen suitability` second
- `TPL-006 External Supplier Information Request` third

Interpretation:

- explicit external-caterer guidance now outranks adjacent kitchen-suitability content
- semantic adjacency still appears, but no longer dominates the top result

### Site Visit

Query:

- `can we visit the venue beforehand`

Outcome under recommended policy:

- `TPL-008 People & spaces` first
- `TPL-008 2. Site visit — if applicable` second
- `CF-005 11.1 Venue Access & Early Entry` third

Interpretation:

- specific operational site-visit guidance now outranks general access clauses
- this is the clearest evidence that governed category modifiers add real value

### Security Deposit

Query:

- `security deposit`

Outcome under recommended policy:

- `CF-007 Security deposit and inspection` first
- `GOV-002 DEC-030 Security deposit: studio` second
- `CF-003 5. Security Deposit` third

Interpretation:

- a direct client-facing deposit clause stays first
- governance history remains visible without displacing the operational answer

## Regressions And Risks

Observed tradeoffs:

- `Relevant@5` is lower than pure semantic search because the policy intentionally demotes some broadly relevant governance or adjacent-concept material in favor of operationally preferred sources
- `when does the remaining balance need to be paid` still places `TPL-013 Final notes` above `CF-007 Payment plan` in the recommended fused ordering

Risk assessment:

- the remaining-balance ordering issue is a secondary-order imperfection, not a top-result failure
- the document-role improvements are strong enough to justify adoption despite that residual imperfection
- if Phase 5.6B wants to refine secondary ordering, it should do so carefully and still avoid query-specific logic

## Recommendation Threshold Outcome

The recommended policy satisfies the Phase 5.6A threshold:

1. preserves FTS exact-term value
2. preserves semantic paraphrase gains
3. improves known document-role conflicts
4. avoids obvious new top-result regressions
5. remains simple and explainable
6. uses only deterministic search evidence plus governed metadata

## Deliverables

- evaluation tool: [tools/phase_05_search/evaluate_retrieval_policy.py](/Users/serinya/Documents/WNC%20Rental%20Automation/tools/phase_05_search/evaluate_retrieval_policy.py)
- evaluation report: [docs/phase-05/search/phase-05-retrieval-policy-evaluation.md](/Users/serinya/Documents/WNC%20Rental%20Automation/docs/phase-05/search/phase-05-retrieval-policy-evaluation.md)

Next gate:

- `PHASE_5_5.6A_RETRIEVAL_POLICY_REVIEW_REQUIRED`
