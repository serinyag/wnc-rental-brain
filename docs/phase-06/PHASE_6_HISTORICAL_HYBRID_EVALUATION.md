# Phase 6 Historical Hybrid Evaluation

Date: August 8, 2026

## 1. Corpus State

- searchable active historical cases: `9`
- searchable active historical case versions: `9`
- searchable current historical units: `112`
- current embeddings: `112`
- missing embeddings: `0`
- stale embeddings: `0`

## 2. Retrieval Baselines

- FTS Hit@1: `17 / 21 = 80.95%`
- FTS Hit@3: `19 / 21 = 90.48%`
- semantic Hit@1: `17 / 21 = 80.95%`
- semantic Hit@3: `19 / 21 = 90.48%`
- semantic paraphrase Hit@1: `6 / 8 = 75.00%`
- semantic paraphrase Hit@3: `8 / 8 = 100.00%`

## 3. Hybrid Configuration(s)

| Configuration | Strategy | Candidate Depth | Hit@1 | Hit@3 | Paraphrase Hit@1 | Paraphrase Hit@3 | Notes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `historical_rrf_balanced_d20` | `historical_rrf_balanced` | `20` | `19/21` | `21/21` | `6/8` | `8/8` | Neutral fusion baseline with the smallest evaluated deep candidate pool. |
| `historical_rrf_balanced_d30` | `historical_rrf_balanced` | `30` | `19/21` | `21/21` | `6/8` | `8/8` | Neutral fusion with a slightly deeper candidate pool. |
| `historical_rrf_balanced_d50` | `historical_rrf_balanced` | `50` | `19/21` | `21/21` | `6/8` | `8/8` | Neutral fusion with near-corpus-depth retrieval. |
| `historical_rrf_lexical_125_d20` | `historical_rrf_lexical_125` | `20` | `19/21` | `21/21` | `6/8` | `8/8` | Tests whether a mild lexical boost preserves exact-match strengths better. |
| `historical_rrf_semantic_125_d20` | `historical_rrf_semantic_125` | `20` | `19/21` | `21/21` | `6/8` | `8/8` | Tests whether a mild semantic boost better preserves paraphrase recovery. |

## 4. Final Chosen Strategy

- strategy code: `historical_rrf_balanced`
- configuration code: `historical_rrf_balanced_d20`
- RRF formula: `weight * (1 / (k + rank))`
- RRF k: `20`
- lexical weight: `1`
- semantic weight: `1`
- candidate depth per retriever: `20`
- selection note: chose the strongest shared-benchmark configuration that preserved semantic paraphrase Hit@3.

## 5. Shared Benchmark

### `multi-day venue takeover`

- expected cases: `HC-001`
- FTS rank: `1`
- semantic rank: `1`
- hybrid rank: `1`
- winner: tie between FTS, semantic, hybrid
- hybrid query latency: `130.97 ms`
- top hybrid result: `HC-001` / `case_narrative` / score `0.095238`
- top hybrid cases/units:
  - `1` `HC-001` / `case_narrative` | availability `active` | hybrid `0.095238` | fts_rank `1` | semantic_rank `1` | preview: Case 01: Merrachi Multi-Day Retail Pop-Up Rental type: Multi-day entire-venue brand / retail takeover. Why this case matters WNC’s cleare...
  - `2` `HC-006` / `case_narrative` | availability `active` | hybrid `0.090909` | fts_rank `2` | semantic_rank `2` | preview: Case 06: Sheso Trading Event Rental type: PR / industry event with high guest turnover, client team, external catering and wellness eleme...
  - `3` `HC-001` / `lesson` | availability `active` | hybrid `0.043478` | fts_rank `None` | semantic_rank `3` | preview: Once fully handed over, a client-run takeover may not require ongoing WNC operational involvement.

### `whole venue clearing`

- expected cases: `HC-001`
- FTS rank: `miss`
- semantic rank: `1`
- hybrid rank: `3`
- winner: semantic ranked the expected case highest
- hybrid query latency: `146.42 ms`
- top hybrid result: `HC-006` / `lesson` / score `0.083333`
- top hybrid cases/units:
  - `1` `HC-006` / `lesson` | availability `active` | hybrid `0.083333` | fts_rank `1` | semantic_rank `8` | preview: Later case modelling should allow both partial clearing and full clearing rather than flattening them into one whole-venue concept.
  - `2` `HC-007` / `case_narrative` | availability `active` | hybrid `0.073232` | fts_rank `2` | semantic_rank `16` | preview: Case 07: MOOI / Little Wonderland PR Activation Rental type: Whole-venue PR / beauty activation. Why this case matters A useful precedent...
  - `3` `HC-001` / `case_narrative` | availability `active` | hybrid `0.047619` | fts_rank `None` | semantic_rank `1` | preview: Case 01: Merrachi Multi-Day Retail Pop-Up Rental type: Multi-day entire-venue brand / retail takeover. Why this case matters WNC’s cleare...

### `client operated event`

- expected cases: `HC-001, HC-003`
- FTS rank: `3`
- semantic rank: `4`
- hybrid rank: `3`
- winner: tie between FTS, hybrid
- hybrid query latency: `137.93 ms`
- top hybrid result: `HC-004` / `responsibility` / score `0.093074`
- top hybrid cases/units:
  - `1` `HC-004` / `responsibility` | availability `limited` | hybrid `0.093074` | fts_rank `2` | semantic_rank `1` | preview: The client controlled catering decisions and PR or brand-event operation.
  - `2` `HC-006` / `responsibility` | availability `active` | hybrid `0.091097` | fts_rank `1` | semantic_rank `3` | preview: The client handled build-up activity, event materials, and event operation.
  - `3` `HC-001` / `responsibility` | availability `active` | hybrid `0.081940` | fts_rank `3` | semantic_rank `6` | preview: The client handled event operation, drinks, cleaning, products, and day-to-day operation after handover.

### `heavy electrical equipment`

- expected cases: `HC-002`
- FTS rank: `1`
- semantic rank: `1`
- hybrid rank: `1`
- winner: tie between FTS, semantic, hybrid
- hybrid query latency: `123.89 ms`
- top hybrid result: `HC-002` / `case_narrative` / score `0.093074`
- top hybrid cases/units:
  - `1` `HC-002` / `case_narrative` | availability `active` | hybrid `0.093074` | fts_rank `1` | semantic_rank `2` | preview: Case 02: Philips Coffee Machine Showcase Rental type: Brand activation / product showcase with significant technical and catering require...
  - `2` `HC-002` / `lesson` | availability `active` | hybrid `0.047619` | fts_rank `None` | semantic_rank `1` | preview: Recommend qualified electrical assessment for heavy-load setups.
  - `3` `HC-002` / `decision` | availability `active` | hybrid `0.043478` | fts_rank `None` | semantic_rank `3` | preview: WNC should not independently validate complex electrical load; client production should bring qualified technical assessment.

### `strong catering smell`

- expected cases: `HC-004`
- FTS rank: `1`
- semantic rank: `1`
- hybrid rank: `1`
- winner: tie between FTS, semantic, hybrid
- hybrid query latency: `123.35 ms`
- top hybrid result: `HC-004` / `case_narrative` / score `0.089286`
- top hybrid cases/units:
  - `1` `HC-004` / `case_narrative` | availability `limited` | hybrid `0.089286` | fts_rank `1` | semantic_rank `4` | preview: Case 04: Amoué PR Wellness Event Rental type: Beauty / PR brand event with wellness programming. Why this case matters This event produce...
  - `2` `HC-004` / `lesson` | availability `limited` | hybrid `0.047619` | fts_rank `None` | semantic_rank `1` | preview: Catering smell should match the intended guest experience.
  - `3` `HC-004` / `decision` | availability `limited` | hybrid `0.045455` | fts_rank `None` | semantic_rank `2` | preview: Strong-smelling food should be avoided for scent-sensitive beauty or perfume activations.

### `sensory-sensitive beauty event`

- expected cases: `HC-004`
- FTS rank: `miss`
- semantic rank: `1`
- hybrid rank: `1`
- winner: tie between semantic, hybrid
- hybrid query latency: `157.77 ms`
- top hybrid result: `HC-004` / `decision` / score `0.047619`
- top hybrid cases/units:
  - `1` `HC-004` / `decision` | availability `limited` | hybrid `0.047619` | fts_rank `None` | semantic_rank `1` | preview: Strong-smelling food should be avoided for scent-sensitive beauty or perfume activations.
  - `2` `HC-004` / `case_narrative` | availability `limited` | hybrid `0.045455` | fts_rank `None` | semantic_rank `2` | preview: Case 04: Amoué PR Wellness Event Rental type: Beauty / PR brand event with wellness programming. Why this case matters This event produce...
  - `3` `HC-004` / `lesson` | availability `limited` | hybrid `0.043478` | fts_rank `None` | semantic_rank `3` | preview: Scent-sensitive activations should avoid strong-smelling food.

### `late build-up`

- expected cases: `HC-006`
- FTS rank: `1`
- semantic rank: `2`
- hybrid rank: `1`
- winner: tie between FTS, hybrid
- hybrid query latency: `152.79 ms`
- top hybrid result: `HC-006` / `lesson` / score `0.093074`
- top hybrid cases/units:
  - `1` `HC-006` / `lesson` | availability `active` | hybrid `0.093074` | fts_rank `1` | semantic_rank `2` | preview: Late build-up should not create indefinite WNC onsite obligation.
  - `2` `HC-006` / `decision` | availability `active` | hybrid `0.087121` | fts_rank `2` | semantic_rank `4` | preview: If build-up runs late, additional WNC staffing or overtime should apply.
  - `3` `HC-006` / `case_narrative` | availability `active` | hybrid `0.086957` | fts_rank `3` | semantic_rank `3` | preview: Case 06: Sheso Trading Event Rental type: PR / industry event with high guest turnover, client team, external catering and wellness eleme...

### `fake snow cleanup`

- expected cases: `HC-007`
- FTS rank: `1`
- semantic rank: `1`
- hybrid rank: `1`
- winner: tie between FTS, semantic, hybrid
- hybrid query latency: `192.62 ms`
- top hybrid result: `HC-007` / `case_narrative` / score `0.091097`
- top hybrid cases/units:
  - `1` `HC-007` / `case_narrative` | availability `active` | hybrid `0.091097` | fts_rank `1` | semantic_rank `3` | preview: Case 07: MOOI / Little Wonderland PR Activation Rental type: Whole-venue PR / beauty activation. Why this case matters A useful precedent...
  - `2` `HC-007` / `decision` | availability `active` | hybrid `0.047619` | fts_rank `None` | semantic_rank `1` | preview: Fake snow is not permitted.
  - `3` `HC-007` / `lesson` | availability `active` | hybrid `0.045455` | fts_rank `None` | semantic_rank `2` | preview: Fake snow is prohibited in this historical precedent.

### `external storage`

- expected cases: `HC-001, HC-003`
- FTS rank: `1`
- semantic rank: `1`
- hybrid rank: `1`
- winner: tie between FTS, semantic, hybrid
- hybrid query latency: `180.21 ms`
- top hybrid result: `HC-001` / `decision` / score `0.095238`
- top hybrid cases/units:
  - `1` `HC-001` / `decision` | availability `active` | hybrid `0.095238` | fts_rank `1` | semantic_rank `1` | preview: External storage was used because onsite space was insufficient.
  - `2` `HC-003` / `decision` | availability `limited` | hybrid `0.078788` | fts_rank `2` | semantic_rank `10` | preview: External bike-storage / hallway storage was hired for EUR 300 for the day.
  - `3` `HC-006` / `case_narrative` | availability `active` | hybrid `0.078462` | fts_rank `5` | semantic_rank `6` | preview: Case 06: Sheso Trading Event Rental type: PR / industry event with high guest turnover, client team, external catering and wellness eleme...

### `competitor branding`

- expected cases: `HC-008`
- FTS rank: `1`
- semantic rank: `1`
- hybrid rank: `1`
- winner: tie between FTS, semantic, hybrid
- hybrid query latency: `173.84 ms`
- top hybrid result: `HC-008` / `decision` / score `0.095238`
- top hybrid cases/units:
  - `1` `HC-008` / `decision` | availability `limited` | hybrid `0.095238` | fts_rank `1` | semantic_rank `1` | preview: Competitor-brand visibility mattered materially to the client.
  - `2` `HC-008` / `lesson` | availability `limited` | hybrid `0.088933` | fts_rank `2` | semantic_rank `3` | preview: Ask about competitor-brand restrictions for branded-company events.
  - `3` `HC-008` / `responsibility` | availability `limited` | hybrid `0.087121` | fts_rank `4` | semantic_rank `2` | preview: The client imposed branded-company and competitor-visibility constraints on the event experience.

### `permit compliance`

- expected cases: `HC-009`
- FTS rank: `1`
- semantic rank: `1`
- hybrid rank: `1`
- winner: tie between FTS, semantic, hybrid
- hybrid query latency: `149.90 ms`
- top hybrid result: `HC-009` / `lesson` / score `0.093074`
- top hybrid cases/units:
  - `1` `HC-009` / `lesson` | availability `limited` | hybrid `0.093074` | fts_rank `1` | semantic_rank `2` | preview: High-impact or non-standard events need early permit and compliance review.
  - `2` `HC-009` / `responsibility` | availability `limited` | hybrid `0.088933` | fts_rank `2` | semantic_rank `3` | preview: WNC needed to trigger an early permit and compliance review for higher-impact ADE-style events.
  - `3` `HC-009` / `lesson` | availability `limited` | hybrid `0.087619` | fts_rank `5` | semantic_rank `1` | preview: Historical compliance solutions must not be reused without current legal checking.

### `client provided wine`

- expected cases: `HC-005`
- FTS rank: `1`
- semantic rank: `1`
- hybrid rank: `1`
- winner: tie between FTS, semantic, hybrid
- hybrid query latency: `158.74 ms`
- top hybrid result: `HC-005` / `responsibility` / score `0.095238`
- top hybrid cases/units:
  - `1` `HC-005` / `responsibility` | availability `active` | hybrid `0.095238` | fts_rank `1` | semantic_rank `1` | preview: The client provided the wine for the reception.
  - `2` `HC-003` / `case_narrative` | availability `limited` | hybrid `0.079193` | fts_rank `3` | semantic_rank `8` | preview: Case 03: WineGB Trade & Press Showcase Rental type: Trade / press showcase with significant WNC production support. Why this case matters...
  - `3` `HC-005` / `case_narrative` | availability `active` | hybrid `0.071096` | fts_rank `2` | semantic_rank `19` | preview: Case 05: British Embassy / GreenTech Corporate Reception Rental type: Corporate networking / reception. Why this case matters A useful ex...

### `WNC cleared the venue`

- expected cases: `HC-001`
- FTS rank: `2`
- semantic rank: `4`
- hybrid rank: `1`
- winner: hybrid ranked the expected case highest
- hybrid query latency: `129.19 ms`
- top hybrid result: `HC-001` / `decision` / score `0.087121`
- top hybrid cases/units:
  - `1` `HC-001` / `decision` | availability `active` | hybrid `0.087121` | fts_rank `2` | semantic_rank `4` | preview: WNC cleared the venue and handed over a white-box-style space.
  - `2` `HC-001` / `responsibility` | availability `active` | hybrid `0.083478` | fts_rank `3` | semantic_rank `5` | preview: WNC cleared agreed venue areas and moved WNC stock, furniture, equipment, kitchen items, and Back Office contents out of sight.
  - `3` `HC-002` / `responsibility` | availability `active` | hybrid `0.080952` | fts_rank `1` | semantic_rank `10` | preview: WNC handled venue preparation and agreed venue clearing.

### `external caterer responsibility`

- expected cases: `HC-003, HC-006`
- FTS rank: `1`
- semantic rank: `1`
- hybrid rank: `1`
- winner: tie between FTS, semantic, hybrid
- hybrid query latency: `177.50 ms`
- top hybrid result: `HC-006` / `responsibility` / score `0.095238`
- top hybrid cases/units:
  - `1` `HC-006` / `responsibility` | availability `active` | hybrid `0.095238` | fts_rank `1` | semantic_rank `1` | preview: External suppliers supported catering and wellness elements where engaged.
  - `2` `HC-005` / `responsibility` | availability `active` | hybrid `0.088933` | fts_rank `2` | semantic_rank `3` | preview: External suppliers supported catering or AV scope where engaged.
  - `3` `HC-003` / `responsibility` | availability `limited` | hybrid `0.085145` | fts_rank `3` | semantic_rank `4` | preview: External suppliers handled catering and hired production items where applicable.

### `current legal precedent`

- expected cases: `HC-009`
- FTS rank: `1`
- semantic rank: `1`
- hybrid rank: `1`
- winner: tie between FTS, semantic, hybrid
- hybrid query latency: `195.21 ms`
- top hybrid result: `HC-009` / `decision` / score `0.095238`
- top hybrid cases/units:
  - `1` `HC-009` / `decision` | availability `limited` | hybrid `0.095238` | fts_rank `1` | semantic_rank `1` | preview: The historical ADE solution is not current legal precedent.
  - `2` `HC-009` / `case_narrative` | availability `limited` | hybrid `0.090909` | fts_rank `2` | semantic_rank `2` | preview: ADE Event: Permit, Alcohol, Sound & Operational Compliance Planning for an ADE event exposed several issues that had not historically bee...
  - `3` `HC-009` / `lesson` | availability `limited` | hybrid `0.086957` | fts_rank `3` | semantic_rank `3` | preview: Historical compliance solutions must not be reused without current legal checking.

### `grace period setup`

- expected cases: `HC-007`
- FTS rank: `1`
- semantic rank: `1`
- hybrid rank: `1`
- winner: tie between FTS, semantic, hybrid
- hybrid query latency: `163.76 ms`
- top hybrid result: `HC-007` / `decision` / score `0.093074`
- top hybrid cases/units:
  - `1` `HC-007` / `decision` | availability `active` | hybrid `0.093074` | fts_rank `2` | semantic_rank `1` | preview: The 30-minute entire-venue grace period is for arrival, not free setup time.
  - `2` `HC-007` / `lesson` | availability `active` | hybrid `0.093074` | fts_rank `1` | semantic_rank `2` | preview: Grace period does not equal setup time, and the historical misuse must not be treated as a current setup allowance.
  - `3` `HC-007` / `case_narrative` | availability `active` | hybrid `0.086957` | fts_rank `3` | semantic_rank `3` | preview: Case 07: MOOI / Little Wonderland PR Activation Rental type: Whole-venue PR / beauty activation. Why this case matters A useful precedent...

### `damage cleanup`

- expected cases: `HC-007`
- FTS rank: `1`
- semantic rank: `1`
- hybrid rank: `1`
- winner: tie between FTS, semantic, hybrid
- hybrid query latency: `168.96 ms`
- top hybrid result: `HC-007` / `case_narrative` / score `0.083333`
- top hybrid cases/units:
  - `1` `HC-007` / `case_narrative` | availability `active` | hybrid `0.083333` | fts_rank `1` | semantic_rank `8` | preview: Case 07: MOOI / Little Wonderland PR Activation Rental type: Whole-venue PR / beauty activation. Why this case matters A useful precedent...
  - `2` `HC-007` / `responsibility` | availability `active` | hybrid `0.047619` | fts_rank `None` | semantic_rank `1` | preview: The client carried cleanup obligations for production materials.
  - `3` `HC-007` / `responsibility` | availability `active` | hybrid `0.045455` | fts_rank `None` | semantic_rank `2` | preview: WNC set cleanup and reset expectations and protected venue equipment.

### `300 storage`

- expected cases: `HC-003`
- FTS rank: `1`
- semantic rank: `3`
- hybrid rank: `1`
- winner: tie between FTS, hybrid
- hybrid query latency: `160.06 ms`
- top hybrid result: `HC-003` / `decision` / score `0.082102`
- top hybrid cases/units:
  - `1` `HC-003` / `decision` | availability `limited` | hybrid `0.082102` | fts_rank `1` | semantic_rank `9` | preview: External bike-storage / hallway storage was hired for EUR 300 for the day.
  - `2` `HC-003` / `case_narrative` | availability `limited` | hybrid `0.072482` | fts_rank `2` | semantic_rank `17` | preview: Case 03: WineGB Trade & Press Showcase Rental type: Trade / press showcase with significant WNC production support. Why this case matters...
  - `3` `HC-006` / `lesson` | availability `active` | hybrid `0.047619` | fts_rank `None` | semantic_rank `1` | preview: Ask about approximate storage volume.

### `florals`

- expected cases: `HC-003`
- FTS rank: `1`
- semantic rank: `1`
- hybrid rank: `1`
- winner: tie between FTS, semantic, hybrid
- hybrid query latency: `184.73 ms`
- top hybrid result: `HC-003` / `decision` / score `0.095238`
- top hybrid cases/units:
  - `1` `HC-003` / `decision` | availability `limited` | hybrid `0.095238` | fts_rank `1` | semantic_rank `1` | preview: Haylin could provide floral arrangement support where included.
  - `2` `HC-003` / `responsibility` | availability `limited` | hybrid `0.090909` | fts_rank `2` | semantic_rank `2` | preview: WNC could include floral arrangement support where agreed.
  - `3` `HC-003` / `case_narrative` | availability `limited` | hybrid `0.071256` | fts_rank `3` | semantic_rank `16` | preview: Case 03: WineGB Trade & Press Showcase Rental type: Trade / press showcase with significant WNC production support. Why this case matters...

### `overtime charge`

- expected cases: `HC-006`
- FTS rank: `1`
- semantic rank: `1`
- hybrid rank: `1`
- winner: tie between FTS, semantic, hybrid
- hybrid query latency: `200.13 ms`
- top hybrid result: `HC-006` / `case_narrative` / score `0.083333`
- top hybrid cases/units:
  - `1` `HC-006` / `case_narrative` | availability `active` | hybrid `0.083333` | fts_rank `1` | semantic_rank `8` | preview: Case 06: Sheso Trading Event Rental type: PR / industry event with high guest turnover, client team, external catering and wellness eleme...
  - `2` `HC-006` / `decision` | availability `active` | hybrid `0.047619` | fts_rank `None` | semantic_rank `1` | preview: If build-up runs late, additional WNC staffing or overtime should apply.
  - `3` `HC-006` / `decision` | availability `active` | hybrid `0.045455` | fts_rank `None` | semantic_rank `2` | preview: Build-up hours need a firm end time.

### `discount exposure gifts`

- expected cases: `HC-004`
- FTS rank: `1`
- semantic rank: `1`
- hybrid rank: `1`
- winner: tie between FTS, semantic, hybrid
- hybrid query latency: `188.61 ms`
- top hybrid result: `HC-004` / `decision` / score `0.095238`
- top hybrid cases/units:
  - `1` `HC-004` / `decision` | availability `limited` | hybrid `0.095238` | fts_rank `1` | semantic_rank `1` | preview: Upcoming-brand status and gifts or exposure did not automatically justify discounted rental.
  - `2` `HC-004` / `lesson` | availability `limited` | hybrid `0.090909` | fts_rank `2` | semantic_rank `2` | preview: WNC should not discount merely because a brand is new or offers exposure or gifts.
  - `3` `HC-004` / `case_narrative` | availability `limited` | hybrid `0.086957` | fts_rank `3` | semantic_rank `3` | preview: Case 04: Amoué PR Wellness Event Rental type: Beauty / PR brand event with wellness programming. Why this case matters This event produce...

## 6. Aggregate Shared Metrics

- hybrid Hit@1: `19 / 21 = 90.48%`
- hybrid Hit@3: `21 / 21 = 100.00%`
- hybrid MRR: `0.9365`

## 7. Paraphrase Benchmark

- hybrid Hit@1: `6 / 8 = 75.00%`
- hybrid Hit@3: `8 / 8 = 100.00%`
- semantic Hit@1 baseline: `6 / 8 = 75.00%`
- semantic Hit@3 baseline: `8 / 8 = 100.00%`

## 8. Complementarity Analysis

- `whole venue clearing`: FTS rank `miss`, semantic rank `1`, hybrid rank `3`.
- `sensory-sensitive beauty event`: FTS rank `miss`, semantic rank `1`, hybrid rank `1`.
- `client operated event`: FTS rank `3`, semantic rank `4`, hybrid rank `3`.
- `WNC cleared the venue`: FTS rank `2`, semantic rank `4`, hybrid rank `1`.

## 9. Exact-Match Preservation

- `300 storage`: FTS rank `1`, semantic rank `3`, hybrid rank `1`.
- `fake snow cleanup`: FTS rank `1`, semantic rank `1`, hybrid rank `1`.
- `permit compliance`: FTS rank `1`, semantic rank `1`, hybrid rank `1`.
- `florals`: FTS rank `1`, semantic rank `1`, hybrid rank `1`.
- `overtime charge`: FTS rank `1`, semantic rank `1`, hybrid rank `1`.

## 10. Failure Analysis

- `whole venue clearing`: category `FTS miss`; FTS `miss` / semantic `1` / hybrid `3`.

## 11. Safety Metadata Review

- `300 storage`: top result `HC-003` / `decision` keeps `source_layer_role=historical_precedent`, `precedent_availability=limited`, `lesson_kind=None`, `historical_value_only=True`, `contamination_risk_level=high`, `current_authority_disposition=potential_conflict_with_current_knowledge`, `effective_confidentiality_level_code=restricted`, `primary_source_locator=Case 03: WineGB Trade & Press Showcase`, `source_link_count=1`.
- `discount exposure gifts`: top result `HC-004` / `decision` keeps `source_layer_role=historical_precedent`, `precedent_availability=limited`, `lesson_kind=None`, `historical_value_only=True`, `contamination_risk_level=high`, `current_authority_disposition=current_status_unknown`, `effective_confidentiality_level_code=restricted`, `primary_source_locator=Case 04: Amoué PR Wellness Event`, `source_link_count=1`.
- `overtime charge`: top result `HC-006` / `case_narrative` keeps `source_layer_role=historical_precedent`, `precedent_availability=active`, `lesson_kind=None`, `historical_value_only=None`, `contamination_risk_level=None`, `current_authority_disposition=None`, `effective_confidentiality_level_code=restricted`, `primary_source_locator=Case 06: Sheso Trading Event`, `source_link_count=1`.
- `fake snow cleanup`: top result `HC-007` / `case_narrative` keeps `source_layer_role=historical_precedent`, `precedent_availability=active`, `lesson_kind=None`, `historical_value_only=None`, `contamination_risk_level=None`, `current_authority_disposition=None`, `effective_confidentiality_level_code=restricted`, `primary_source_locator=Case 07: MOOI / Little Wonderland PR Activation`, `source_link_count=1`.
- `current legal precedent`: top result `HC-009` / `decision` keeps `source_layer_role=historical_precedent`, `precedent_availability=limited`, `lesson_kind=None`, `historical_value_only=True`, `contamination_risk_level=high`, `current_authority_disposition=potential_conflict_with_current_knowledge`, `effective_confidentiality_level_code=restricted`, `primary_source_locator=ADE Event: Permit, Alcohol, Sound & Operational Compliance`, `source_link_count=1`.
- `Later modelling may need`: top result `HC-009` / `lesson` keeps `source_layer_role=historical_precedent`, `precedent_availability=limited`, `lesson_kind=analyst_inference`, `historical_value_only=False`, `contamination_risk_level=low`, `current_authority_disposition=no_current_rule_implication`, `effective_confidentiality_level_code=restricted`, `primary_source_locator=ADE Event: Permit, Alcohol, Sound & Operational Compliance`, `source_link_count=1`.

