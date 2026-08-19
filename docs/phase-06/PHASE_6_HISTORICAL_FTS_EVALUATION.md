# Phase 6 Historical FTS Evaluation

Date: August 7, 2026

## Evaluation Corpus

- searchable active historical cases: `9`
- searchable active historical case versions: `9`
- searchable current historical units: `112`
- top results captured per query: `5`

## Configuration

- PostgreSQL text-search configuration: `english`
- query parser: `websearch_to_tsquery`
- ranking function: `ts_rank_cd` with length normalization `2`
- weighting:
  - `A`: case title
  - `B`: case code and governed search-unit text
  - `C`: unit type, responsibility actor, lesson kind
- searchable corpus surface: `private.current_historical_case_search_units`

## Query Set

- `multi-day venue takeover` | category `Similar historical situation` | expected cases `HC-001` | preferred units `case_narrative` | success target `Hit@1`
- `whole venue clearing` | category `Similar historical situation` | expected cases `HC-001` | preferred units `responsibility, decision, lesson` | success target `Hit@1`
- `client operated event` | category `Similar historical situation` | expected cases `HC-001, HC-003` | preferred units `decision, responsibility, case_narrative` | success target `Hit@3`
- `heavy electrical equipment` | category `Operational problem` | expected cases `HC-002` | preferred units `decision, lesson, case_narrative` | success target `Hit@1`
- `strong catering smell` | category `Operational problem` | expected cases `HC-004` | preferred units `decision, lesson` | success target `Hit@1`
- `sensory-sensitive beauty event` | category `Operational problem` | expected cases `HC-004` | preferred units `case_narrative, decision, lesson` | success target `Hit@3`
- `late build-up` | category `Operational problem` | expected cases `HC-006` | preferred units `decision, lesson` | success target `Hit@1`
- `fake snow cleanup` | category `Operational problem` | expected cases `HC-007` | preferred units `decision, lesson, responsibility, case_narrative` | success target `Hit@1`
- `external storage` | category `Operational problem` | expected cases `HC-001, HC-003` | preferred units `decision, lesson, case_narrative` | success target `Hit@3`
- `competitor branding` | category `Operational problem` | expected cases `HC-008` | preferred units `decision, responsibility, lesson` | success target `Hit@1`
- `permit compliance` | category `Caution` | expected cases `HC-009` | preferred units `decision, lesson, responsibility, case_narrative` | success target `Hit@1`
- `client provided wine` | category `Responsibility` | expected cases `HC-005` | preferred units `responsibility, decision` | success target `Hit@1`
- `WNC cleared the venue` | category `Responsibility` | expected cases `HC-001` | preferred units `responsibility, decision` | success target `Hit@1`
- `external caterer responsibility` | category `Responsibility` | expected cases `HC-003, HC-006` | preferred units `responsibility` | success target `Hit@3`
- `current legal precedent` | category `Caution` | expected cases `HC-009` | preferred units `decision, lesson, case_narrative` | success target `Hit@1`
- `grace period setup` | category `Caution` | expected cases `HC-007` | preferred units `decision, lesson, case_narrative` | success target `Hit@1`
- `damage cleanup` | category `Caution` | expected cases `HC-007` | preferred units `responsibility, decision, case_narrative` | success target `Hit@3`
- `300 storage` | category `Historical commercial specifics` | expected cases `HC-003` | preferred units `decision, case_narrative, lesson` | success target `Hit@1`
- `florals` | category `Historical commercial specifics` | expected cases `HC-003` | preferred units `decision, responsibility, case_narrative` | success target `Hit@3`
- `overtime charge` | category `Historical commercial specifics` | expected cases `HC-006` | preferred units `decision, lesson` | success target `Hit@1`
- `discount exposure gifts` | category `Historical commercial specifics` | expected cases `HC-004` | preferred units `decision, lesson, responsibility` | success target `Hit@1`

## Results

### `multi-day venue takeover`

- category: `Similar historical situation`
- expected cases: `HC-001`
- preferred unit types: `case_narrative`
- required success condition: `Hit@1`
- fixture note: Exact title and narrative language should make the Merrachi takeover case dominate.
- first matching rank: `1`
- Hit@1: `yes`
- Hit@3: `yes`
- ground-truth satisfied: `yes`
- preferred unit matched: `yes`
- notes: Top result is expected case HC-001 / case_narrative.
- top result: `HC-001` / `case_narrative` / score `0.000740`
- top 3 cases/units:
  - `1` `HC-001` / `case_narrative` | availability `active` | score `0.000740` | preview: Case 01: Merrachi Multi-Day Retail Pop-Up Rental type: Multi-day entire-venue brand / retail takeover. Why this case matters WNC’s cleare...
  - `2` `HC-006` / `case_narrative` | availability `active` | score `0.000094` | preview: Case 06: Sheso Trading Event Rental type: PR / industry event with high guest turnover, client team, external catering and wellness eleme...

### `whole venue clearing`

- category: `Similar historical situation`
- expected cases: `HC-001`
- preferred unit types: `responsibility, decision, lesson`
- required success condition: `Hit@1`
- fixture note: HC-001 contains the clearest whole-venue clearing precedent.
- first matching rank: `miss`
- Hit@1: `no`
- Hit@3: `no`
- ground-truth satisfied: `no`
- preferred unit matched: `no`
- notes: No expected case appeared in the captured result window.
- top result: `HC-006` / `lesson` / score `0.002174`
- top 3 cases/units:
  - `1` `HC-006` / `lesson` | availability `active` | score `0.002174` | preview: Later case modelling should allow both partial clearing and full clearing rather than flattening them into one whole-venue concept.
  - `2` `HC-007` / `case_narrative` | availability `active` | score `0.000023` | preview: Case 07: MOOI / Little Wonderland PR Activation Rental type: Whole-venue PR / beauty activation. Why this case matters A useful precedent...

### `client operated event`

- category: `Similar historical situation`
- expected cases: `HC-001, HC-003`
- preferred unit types: `decision, responsibility, case_narrative`
- required success condition: `Hit@3`
- fixture note: Both HC-001 and HC-003 draw a boundary between WNC support and the client running the event.
- first matching rank: `3`
- Hit@1: `no`
- Hit@3: `yes`
- ground-truth satisfied: `yes`
- preferred unit matched: `yes`
- notes: Expected case appears at rank 3; top result is HC-006 / responsibility.
- top result: `HC-006` / `responsibility` / score `0.012500`
- top 3 cases/units:
  - `1` `HC-006` / `responsibility` | availability `active` | score `0.012500` | preview: The client handled build-up activity, event materials, and event operation.
  - `2` `HC-004` / `responsibility` | availability `limited` | score `0.011438` | preview: The client controlled catering decisions and PR or brand-event operation.
  - `3` `HC-001` / `responsibility` | availability `active` | score `0.009855` | preview: The client handled event operation, drinks, cleaning, products, and day-to-day operation after handover.

### `heavy electrical equipment`

- category: `Operational problem`
- expected cases: `HC-002`
- preferred unit types: `decision, lesson, case_narrative`
- required success condition: `Hit@1`
- fixture note: HC-002 is the corpus precedent for technical load and qualified electrical assessment.
- first matching rank: `1`
- Hit@1: `yes`
- Hit@3: `yes`
- ground-truth satisfied: `yes`
- preferred unit matched: `yes`
- notes: Top result is expected case HC-002 / case_narrative.
- top result: `HC-002` / `case_narrative` / score `0.000451`
- top 3 cases/units:
  - `1` `HC-002` / `case_narrative` | availability `active` | score `0.000451` | preview: Case 02: Philips Coffee Machine Showcase Rental type: Brand activation / product showcase with significant technical and catering require...

### `strong catering smell`

- category: `Operational problem`
- expected cases: `HC-004`
- preferred unit types: `decision, lesson`
- required success condition: `Hit@1`
- fixture note: HC-004 contains explicit smell and scent-sensitive event language.
- first matching rank: `1`
- Hit@1: `yes`
- Hit@3: `yes`
- ground-truth satisfied: `yes`
- preferred unit matched: `no`
- notes: Top result is expected case HC-004 / case_narrative.
- top result: `HC-004` / `case_narrative` / score `0.000791`
- top 3 cases/units:
  - `1` `HC-004` / `case_narrative` | availability `limited` | score `0.000791` | preview: Case 04: Amoué PR Wellness Event Rental type: Beauty / PR brand event with wellness programming. Why this case matters This event produce...

### `sensory-sensitive beauty event`

- category: `Operational problem`
- expected cases: `HC-004`
- preferred unit types: `case_narrative, decision, lesson`
- required success condition: `Hit@3`
- fixture note: This is intentionally a slightly paraphrased lexical query for the scent-sensitive beauty-event precedent.
- first matching rank: `miss`
- Hit@1: `no`
- Hit@3: `no`
- ground-truth satisfied: `no`
- preferred unit matched: `no`
- notes: No expected case appeared in the captured result window.
- top result: none
- top 3 cases/units: none

### `late build-up`

- category: `Operational problem`
- expected cases: `HC-006`
- preferred unit types: `decision, lesson`
- required success condition: `Hit@1`
- fixture note: HC-006 explicitly uses late build-up wording.
- first matching rank: `1`
- Hit@1: `yes`
- Hit@3: `yes`
- ground-truth satisfied: `yes`
- preferred unit matched: `yes`
- notes: Top result is expected case HC-006 / lesson.
- top result: `HC-006` / `lesson` / score `0.025000`
- top 3 cases/units:
  - `1` `HC-006` / `lesson` | availability `active` | score `0.025000` | preview: Late build-up should not create indefinite WNC onsite obligation.
  - `2` `HC-006` / `decision` | availability `active` | score `0.008889` | preview: If build-up runs late, additional WNC staffing or overtime should apply.
  - `3` `HC-006` / `case_narrative` | availability `active` | score `0.000625` | preview: Case 06: Sheso Trading Event Rental type: PR / industry event with high guest turnover, client team, external catering and wellness eleme...

### `fake snow cleanup`

- category: `Operational problem`
- expected cases: `HC-007`
- preferred unit types: `decision, lesson, responsibility, case_narrative`
- required success condition: `Hit@1`
- fixture note: HC-007 contains exact fake-snow and cleanup language.
- first matching rank: `1`
- Hit@1: `yes`
- Hit@3: `yes`
- ground-truth satisfied: `yes`
- preferred unit matched: `yes`
- notes: Top result is expected case HC-007 / case_narrative.
- top result: `HC-007` / `case_narrative` / score `0.000619`
- top 3 cases/units:
  - `1` `HC-007` / `case_narrative` | availability `active` | score `0.000619` | preview: Case 07: MOOI / Little Wonderland PR Activation Rental type: Whole-venue PR / beauty activation. Why this case matters A useful precedent...

### `external storage`

- category: `Operational problem`
- expected cases: `HC-001, HC-003`
- preferred unit types: `decision, lesson, case_narrative`
- required success condition: `Hit@3`
- fixture note: Both HC-001 and HC-003 discuss external storage, so case-level top-three coverage is sufficient.
- first matching rank: `1`
- Hit@1: `yes`
- Hit@3: `yes`
- ground-truth satisfied: `yes`
- preferred unit matched: `yes`
- notes: Top result is expected case HC-001 / decision.
- top result: `HC-001` / `decision` / score `0.025000`
- top 3 cases/units:
  - `1` `HC-001` / `decision` | availability `active` | score `0.025000` | preview: External storage was used because onsite space was insufficient.
  - `2` `HC-003` / `decision` | availability `limited` | score `0.007843` | preview: External bike-storage / hallway storage was hired for EUR 300 for the day.
  - `3` `HC-001` / `case_narrative` | availability `active` | score `0.004158` | preview: Case 01: Merrachi Multi-Day Retail Pop-Up Rental type: Multi-day entire-venue brand / retail takeover. Why this case matters WNC’s cleare...

### `competitor branding`

- category: `Operational problem`
- expected cases: `HC-008`
- preferred unit types: `decision, responsibility, lesson`
- required success condition: `Hit@1`
- fixture note: HC-008 is the branded-company / competitor-visibility precedent.
- first matching rank: `1`
- Hit@1: `yes`
- Hit@3: `yes`
- ground-truth satisfied: `yes`
- preferred unit matched: `yes`
- notes: Top result is expected case HC-008 / decision.
- top result: `HC-008` / `decision` / score `0.030252`
- top 3 cases/units:
  - `1` `HC-008` / `decision` | availability `limited` | score `0.030252` | preview: Competitor-brand visibility mattered materially to the client.
  - `2` `HC-008` / `lesson` | availability `limited` | score `0.022935` | preview: Ask about competitor-brand restrictions for branded-company events.
  - `3` `HC-008` / `case_narrative` | availability `limited` | score `0.011437` | preview: Vanessa Corporate Wellness Outing / Lululemon Branding Requirement Small corporate wellness rental for approximately 12 guests involving...

### `permit compliance`

- category: `Caution`
- expected cases: `HC-009`
- preferred unit types: `decision, lesson, responsibility, case_narrative`
- required success condition: `Hit@1`
- fixture note: HC-009 is the permit and compliance cautionary precedent.
- first matching rank: `1`
- Hit@1: `yes`
- Hit@3: `yes`
- ground-truth satisfied: `yes`
- preferred unit matched: `yes`
- notes: Top result is expected case HC-009 / lesson.
- top result: `HC-009` / `lesson` / score `0.019633`
- top 3 cases/units:
  - `1` `HC-009` / `lesson` | availability `limited` | score `0.019633` | preview: High-impact or non-standard events need early permit and compliance review.
  - `2` `HC-009` / `responsibility` | availability `limited` | score `0.019505` | preview: WNC needed to trigger an early permit and compliance review for higher-impact ADE-style events.
  - `3` `HC-009` / `decision` | availability `limited` | score `0.015318` | preview: Events involving DJs, amplified music, alcohol, non-standard guest use, or public-space activity should trigger early permit and complian...

### `client provided wine`

- category: `Responsibility`
- expected cases: `HC-005`
- preferred unit types: `responsibility, decision`
- required success condition: `Hit@1`
- fixture note: HC-005 contains exact wine-responsibility wording.
- first matching rank: `1`
- Hit@1: `yes`
- Hit@3: `yes`
- ground-truth satisfied: `yes`
- preferred unit matched: `yes`
- notes: Top result is expected case HC-005 / responsibility.
- top result: `HC-005` / `responsibility` / score `0.019231`
- top 3 cases/units:
  - `1` `HC-005` / `responsibility` | availability `active` | score `0.019231` | preview: The client provided the wine for the reception.
  - `2` `HC-005` / `case_narrative` | availability `active` | score `0.004049` | preview: Case 05: British Embassy / GreenTech Corporate Reception Rental type: Corporate networking / reception. Why this case matters A useful ex...
  - `3` `HC-003` / `case_narrative` | availability `limited` | score `0.000054` | preview: Case 03: WineGB Trade & Press Showcase Rental type: Trade / press showcase with significant WNC production support. Why this case matters...

### `WNC cleared the venue`

- category: `Responsibility`
- expected cases: `HC-001`
- preferred unit types: `responsibility, decision`
- required success condition: `Hit@1`
- fixture note: HC-001 contains the clearest white-box clearing language.
- first matching rank: `2`
- Hit@1: `no`
- Hit@3: `yes`
- ground-truth satisfied: `no`
- preferred unit matched: `yes`
- notes: Expected case appears at rank 2; top result is HC-002 / responsibility.
- top result: `HC-002` / `responsibility` / score `0.015333`
- top 3 cases/units:
  - `1` `HC-002` / `responsibility` | availability `active` | score `0.015333` | preview: WNC handled venue preparation and agreed venue clearing.
  - `2` `HC-001` / `decision` | availability `active` | score `0.010526` | preview: WNC cleared the venue and handed over a white-box-style space.
  - `3` `HC-001` / `responsibility` | availability `active` | score `0.010370` | preview: WNC cleared agreed venue areas and moved WNC stock, furniture, equipment, kitchen items, and Back Office contents out of sight.

### `external caterer responsibility`

- category: `Responsibility`
- expected cases: `HC-003, HC-006`
- preferred unit types: `responsibility`
- required success condition: `Hit@3`
- fixture note: The corpus uses external-suppliers wording rather than a standardized external-caterer phrase.
- first matching rank: `1`
- Hit@1: `yes`
- Hit@3: `yes`
- ground-truth satisfied: `yes`
- preferred unit matched: `yes`
- notes: Top result is expected case HC-006 / responsibility.
- top result: `HC-006` / `responsibility` / score `0.005167`
- top 3 cases/units:
  - `1` `HC-006` / `responsibility` | availability `active` | score `0.005167` | preview: External suppliers supported catering and wellness elements where engaged.
  - `2` `HC-005` / `responsibility` | availability `active` | score `0.004559` | preview: External suppliers supported catering or AV scope where engaged.
  - `3` `HC-003` / `responsibility` | availability `limited` | score `0.003978` | preview: External suppliers handled catering and hired production items where applicable.

### `current legal precedent`

- category: `Caution`
- expected cases: `HC-009`
- preferred unit types: `decision, lesson, case_narrative`
- required success condition: `Hit@1`
- fixture note: HC-009 explicitly says the historical ADE solution is not current legal precedent.
- first matching rank: `1`
- Hit@1: `yes`
- Hit@3: `yes`
- ground-truth satisfied: `yes`
- preferred unit matched: `yes`
- notes: Top result is expected case HC-009 / decision.
- top result: `HC-009` / `decision` / score `0.026797`
- top 3 cases/units:
  - `1` `HC-009` / `decision` | availability `limited` | score `0.026797` | preview: The historical ADE solution is not current legal precedent.
  - `2` `HC-009` / `case_narrative` | availability `limited` | score `0.008579` | preview: ADE Event: Permit, Alcohol, Sound & Operational Compliance Planning for an ADE event exposed several issues that had not historically bee...
  - `3` `HC-009` / `lesson` | availability `limited` | score `0.002066` | preview: Historical compliance solutions must not be reused without current legal checking.

### `grace period setup`

- category: `Caution`
- expected cases: `HC-007`
- preferred unit types: `decision, lesson, case_narrative`
- required success condition: `Hit@1`
- fixture note: HC-007 explicitly ties the grace period to arrival rather than setup.
- first matching rank: `1`
- Hit@1: `yes`
- Hit@3: `yes`
- ground-truth satisfied: `yes`
- preferred unit matched: `yes`
- notes: Top result is expected case HC-007 / lesson.
- top result: `HC-007` / `lesson` / score `0.004545`
- top 3 cases/units:
  - `1` `HC-007` / `lesson` | availability `active` | score `0.004545` | preview: Grace period does not equal setup time, and the historical misuse must not be treated as a current setup allowance.
  - `2` `HC-007` / `decision` | availability `active` | score `0.003509` | preview: The 30-minute entire-venue grace period is for arrival, not free setup time.
  - `3` `HC-007` / `case_narrative` | availability `active` | score `0.001557` | preview: Case 07: MOOI / Little Wonderland PR Activation Rental type: Whole-venue PR / beauty activation. Why this case matters A useful precedent...

### `damage cleanup`

- category: `Caution`
- expected cases: `HC-007`
- preferred unit types: `responsibility, decision, case_narrative`
- required success condition: `Hit@3`
- fixture note: Damage and cleanup are both present in HC-007, but the wording is spread across multiple unit types.
- first matching rank: `1`
- Hit@1: `yes`
- Hit@3: `yes`
- ground-truth satisfied: `yes`
- preferred unit matched: `yes`
- notes: Top result is expected case HC-007 / case_narrative.
- top result: `HC-007` / `case_narrative` / score `0.001384`
- top 3 cases/units:
  - `1` `HC-007` / `case_narrative` | availability `active` | score `0.001384` | preview: Case 07: MOOI / Little Wonderland PR Activation Rental type: Whole-venue PR / beauty activation. Why this case matters A useful precedent...

### `300 storage`

- category: `Historical commercial specifics`
- expected cases: `HC-003`
- preferred unit types: `decision, case_narrative, lesson`
- required success condition: `Hit@1`
- fixture note: HC-003 contains the EUR 300 storage precedent.
- first matching rank: `1`
- Hit@1: `yes`
- Hit@3: `yes`
- ground-truth satisfied: `yes`
- preferred unit matched: `yes`
- notes: Top result is expected case HC-003 / decision.
- top result: `HC-003` / `decision` / score `0.004706`
- top 3 cases/units:
  - `1` `HC-003` / `decision` | availability `limited` | score `0.004706` | preview: External bike-storage / hallway storage was hired for EUR 300 for the day.
  - `2` `HC-003` / `case_narrative` | availability `limited` | score `0.000409` | preview: Case 03: WineGB Trade & Press Showcase Rental type: Trade / press showcase with significant WNC production support. Why this case matters...

### `florals`

- category: `Historical commercial specifics`
- expected cases: `HC-003`
- preferred unit types: `decision, responsibility, case_narrative`
- required success condition: `Hit@3`
- fixture note: The corpus uses floral-arrangement wording rather than a normalized floral-service taxonomy.
- first matching rank: `1`
- Hit@1: `yes`
- Hit@3: `yes`
- ground-truth satisfied: `yes`
- preferred unit matched: `yes`
- notes: Top result is expected case HC-003 / decision.
- top result: `HC-003` / `decision` / score `0.028571`
- top 3 cases/units:
  - `1` `HC-003` / `decision` | availability `limited` | score `0.028571` | preview: Haylin could provide floral arrangement support where included.
  - `2` `HC-003` / `responsibility` | availability `limited` | score `0.026667` | preview: WNC could include floral arrangement support where agreed.
  - `3` `HC-003` / `case_narrative` | availability `limited` | score `0.005000` | preview: Case 03: WineGB Trade & Press Showcase Rental type: Trade / press showcase with significant WNC production support. Why this case matters...

### `overtime charge`

- category: `Historical commercial specifics`
- expected cases: `HC-006`
- preferred unit types: `decision, lesson`
- required success condition: `Hit@1`
- fixture note: HC-006 is the overtime / staffing precedent for late build-up.
- first matching rank: `1`
- Hit@1: `yes`
- Hit@3: `yes`
- ground-truth satisfied: `yes`
- preferred unit matched: `no`
- notes: Top result is expected case HC-006 / case_narrative.
- top result: `HC-006` / `case_narrative` / score `0.001498`
- top 3 cases/units:
  - `1` `HC-006` / `case_narrative` | availability `active` | score `0.001498` | preview: Case 06: Sheso Trading Event Rental type: PR / industry event with high guest turnover, client team, external catering and wellness eleme...

### `discount exposure gifts`

- category: `Historical commercial specifics`
- expected cases: `HC-004`
- preferred unit types: `decision, lesson, responsibility`
- required success condition: `Hit@1`
- fixture note: HC-004 contains exact exposure / gifts / discount caution language.
- first matching rank: `1`
- Hit@1: `yes`
- Hit@3: `yes`
- ground-truth satisfied: `yes`
- preferred unit matched: `yes`
- notes: Top result is expected case HC-004 / decision.
- top result: `HC-004` / `decision` / score `0.003922`
- top 3 cases/units:
  - `1` `HC-004` / `decision` | availability `limited` | score `0.003922` | preview: Upcoming-brand status and gifts or exposure did not automatically justify discounted rental.
  - `2` `HC-004` / `lesson` | availability `limited` | score `0.002353` | preview: WNC should not discount merely because a brand is new or offers exposure or gifts.
  - `3` `HC-004` / `case_narrative` | availability `limited` | score `0.000562` | preview: Case 04: Amoué PR Wellness Event Rental type: Beauty / PR brand event with wellness programming. Why this case matters This event produce...

## Aggregate Metrics

- query count: `21`
- Hit@1: `17 / 21 = 80.95%`
- Hit@3: `19 / 21 = 90.48%`
- MRR: `0.8492`

## Miss Analysis

- `whole venue clearing`: category `semantic similarity required`; first matching rank `miss`; note: No expected case appeared in the captured result window.
- `client operated event`: category `ranking tie or broad query`; first matching rank `3`; note: Expected case appears at rank 3; top result is HC-006 / responsibility.
- `sensory-sensitive beauty event`: category `vocabulary mismatch`; first matching rank `miss`; note: No expected case appeared in the captured result window.
- `WNC cleared the venue`: category `ranking tie or broad query`; first matching rank `2`; note: Expected case appears at rank 2; top result is HC-002 / responsibility.

## Safety Metadata Review

- `300 storage`: top result `HC-003` / `decision` keeps `source_layer_role=historical_precedent`, `precedent_availability=limited`, `historical_value_only=True`, `contamination_risk_level=high`, `current_authority_disposition=potential_conflict_with_current_knowledge`, `lesson_kind=None`, `effective_confidentiality_level_code=restricted`, `primary_source_locator=Case 03: WineGB Trade & Press Showcase`.
- `current legal precedent`: top result `HC-009` / `decision` keeps `source_layer_role=historical_precedent`, `precedent_availability=limited`, `historical_value_only=True`, `contamination_risk_level=high`, `current_authority_disposition=potential_conflict_with_current_knowledge`, `lesson_kind=None`, `effective_confidentiality_level_code=restricted`, `primary_source_locator=ADE Event: Permit, Alcohol, Sound & Operational Compliance`.
- `Later modelling may need`: top result `HC-009` / `lesson` keeps `source_layer_role=historical_precedent`, `precedent_availability=limited`, `historical_value_only=False`, `contamination_risk_level=low`, `current_authority_disposition=no_current_rule_implication`, `lesson_kind=analyst_inference`, `effective_confidentiality_level_code=restricted`, `primary_source_locator=ADE Event: Permit, Alcohol, Sound & Operational Compliance`.

## Baseline Findings

- Historical lexical retrieval works well when the query reuses governed case titles, operational nouns, and statement phrasing already present in the search-unit text.
- The historical surface stays structurally distinct from current knowledge because every result self-identifies as `historical_precedent` and carries limited-status, contamination, authority-disposition, confidentiality, and provenance metadata.
- Queries that depend on paraphrase or vocabulary substitution still expose the expected lexical limit that 6.4C semantic retrieval is meant to test rather than hide.

