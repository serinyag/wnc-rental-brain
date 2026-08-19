# Phase 6 Historical Semantic Evaluation

Date: August 7, 2026

## 1. Model

- provider: `openai`
- model code: `text-embedding-3-small`
- model version: `None`
- dimensions: `1536`
- similarity metric: `cosine`
- embedding input format:
  - `Case: <case_title>`
  - `Case code: <case_code>` when present
  - `Unit type: <unit_type>` when present
  - `Actor type: <actor_type>` when present
  - `Lesson kind: <lesson_kind>` when present
  - governed historical `search_text` body

## 2. Corpus

- searchable active historical cases: `9`
- searchable active historical case versions: `9`
- searchable current historical units: `112`
- embedding completeness: `112 / 112`
- missing embeddings: `0`
- stale embeddings: `0`
- top results captured per query: `5`

## 3. Shared 21-Query Benchmark

### `multi-day venue takeover`

- category: `Similar historical situation`
- expected cases: `HC-001`
- preferred unit types: `case_narrative`
- required success condition: `Hit@1`
- fixture note: Exact title and narrative language should make the Merrachi takeover case dominate.
- FTS rank: `1`
- semantic rank: `1`
- semantic Hit@1: `yes`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- comparison: FTS and semantic search produced the same expected-case rank
- semantic query latency: `1163.42 ms`
- top semantic result: `HC-001` / `case_narrative` / score `0.565712`
- top semantic cases/units:
  - `1` `HC-001` / `case_narrative` | availability `active` | score `0.565712` | preview: Case 01: Merrachi Multi-Day Retail Pop-Up Rental type: Multi-day entire-venue brand / retail takeover. Why this case matters WNC’s cleare...
  - `2` `HC-006` / `case_narrative` | availability `active` | score `0.425641` | preview: Case 06: Sheso Trading Event Rental type: PR / industry event with high guest turnover, client team, external catering and wellness eleme...
  - `3` `HC-001` / `lesson` | availability `active` | score `0.416449` | preview: Once fully handed over, a client-run takeover may not require ongoing WNC operational involvement.

### `whole venue clearing`

- category: `Similar historical situation`
- expected cases: `HC-001`
- preferred unit types: `responsibility, decision, lesson`
- required success condition: `Hit@1`
- fixture note: HC-001 contains the clearest whole-venue clearing precedent.
- FTS rank: `miss`
- semantic rank: `1`
- semantic Hit@1: `yes`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- comparison: semantic search recovered a lexical miss
- semantic query latency: `1315.65 ms`
- top semantic result: `HC-001` / `case_narrative` / score `0.471486`
- top semantic cases/units:
  - `1` `HC-001` / `case_narrative` | availability `active` | score `0.471486` | preview: Case 01: Merrachi Multi-Day Retail Pop-Up Rental type: Multi-day entire-venue brand / retail takeover. Why this case matters WNC’s cleare...
  - `2` `HC-001` / `responsibility` | availability `active` | score `0.443467` | preview: WNC cleared agreed venue areas and moved WNC stock, furniture, equipment, kitchen items, and Back Office contents out of sight.
  - `3` `HC-002` / `case_narrative` | availability `active` | score `0.419211` | preview: Case 02: Philips Coffee Machine Showcase Rental type: Brand activation / product showcase with significant technical and catering require...

### `client operated event`

- category: `Similar historical situation`
- expected cases: `HC-001, HC-003`
- preferred unit types: `decision, responsibility, case_narrative`
- required success condition: `Hit@3`
- fixture note: Both HC-001 and HC-003 draw a boundary between WNC support and the client running the event.
- FTS rank: `3`
- semantic rank: `4`
- semantic Hit@1: `no`
- semantic Hit@3: `no`
- semantic ground-truth satisfied: `no`
- comparison: FTS ranked the expected case higher
- semantic query latency: `1365.84 ms`
- top semantic result: `HC-004` / `responsibility` / score `0.562098`
- top semantic cases/units:
  - `1` `HC-004` / `responsibility` | availability `limited` | score `0.562098` | preview: The client controlled catering decisions and PR or brand-event operation.
  - `2` `HC-004` / `responsibility` | availability `limited` | score `0.523395` | preview: The client negotiated commercial terms around discount or collaboration.
  - `3` `HC-006` / `responsibility` | availability `active` | score `0.511884` | preview: The client handled build-up activity, event materials, and event operation.

### `heavy electrical equipment`

- category: `Operational problem`
- expected cases: `HC-002`
- preferred unit types: `decision, lesson, case_narrative`
- required success condition: `Hit@1`
- fixture note: HC-002 is the corpus precedent for technical load and qualified electrical assessment.
- FTS rank: `1`
- semantic rank: `1`
- semantic Hit@1: `yes`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- comparison: FTS and semantic search produced the same expected-case rank
- semantic query latency: `1503.58 ms`
- top semantic result: `HC-002` / `lesson` / score `0.401446`
- top semantic cases/units:
  - `1` `HC-002` / `lesson` | availability `active` | score `0.401446` | preview: Recommend qualified electrical assessment for heavy-load setups.
  - `2` `HC-002` / `case_narrative` | availability `active` | score `0.364322` | preview: Case 02: Philips Coffee Machine Showcase Rental type: Brand activation / product showcase with significant technical and catering require...
  - `3` `HC-002` / `decision` | availability `active` | score `0.351941` | preview: WNC should not independently validate complex electrical load; client production should bring qualified technical assessment.

### `strong catering smell`

- category: `Operational problem`
- expected cases: `HC-004`
- preferred unit types: `decision, lesson`
- required success condition: `Hit@1`
- fixture note: HC-004 contains explicit smell and scent-sensitive event language.
- FTS rank: `1`
- semantic rank: `1`
- semantic Hit@1: `yes`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- comparison: FTS and semantic search produced the same expected-case rank
- semantic query latency: `1365.81 ms`
- top semantic result: `HC-004` / `lesson` / score `0.497948`
- top semantic cases/units:
  - `1` `HC-004` / `lesson` | availability `limited` | score `0.497948` | preview: Catering smell should match the intended guest experience.
  - `2` `HC-004` / `decision` | availability `limited` | score `0.451015` | preview: Strong-smelling food should be avoided for scent-sensitive beauty or perfume activations.
  - `3` `HC-004` / `lesson` | availability `limited` | score `0.419999` | preview: Scent-sensitive activations should avoid strong-smelling food.

### `sensory-sensitive beauty event`

- category: `Operational problem`
- expected cases: `HC-004`
- preferred unit types: `case_narrative, decision, lesson`
- required success condition: `Hit@3`
- fixture note: This is intentionally a slightly paraphrased lexical query for the scent-sensitive beauty-event precedent.
- FTS rank: `miss`
- semantic rank: `1`
- semantic Hit@1: `yes`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- comparison: semantic search recovered a lexical miss
- semantic query latency: `1267.33 ms`
- top semantic result: `HC-004` / `decision` / score `0.483935`
- top semantic cases/units:
  - `1` `HC-004` / `decision` | availability `limited` | score `0.483935` | preview: Strong-smelling food should be avoided for scent-sensitive beauty or perfume activations.
  - `2` `HC-004` / `case_narrative` | availability `limited` | score `0.452307` | preview: Case 04: Amoué PR Wellness Event Rental type: Beauty / PR brand event with wellness programming. Why this case matters This event produce...
  - `3` `HC-004` / `lesson` | availability `limited` | score `0.424549` | preview: Scent-sensitive activations should avoid strong-smelling food.

### `late build-up`

- category: `Operational problem`
- expected cases: `HC-006`
- preferred unit types: `decision, lesson`
- required success condition: `Hit@1`
- fixture note: HC-006 explicitly uses late build-up wording.
- FTS rank: `1`
- semantic rank: `2`
- semantic Hit@1: `no`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `no`
- comparison: FTS ranked the expected case higher
- semantic query latency: `1754.27 ms`
- top semantic result: `HC-007` / `case_narrative` / score `0.367048`
- top semantic cases/units:
  - `1` `HC-007` / `case_narrative` | availability `active` | score `0.367048` | preview: Case 07: MOOI / Little Wonderland PR Activation Rental type: Whole-venue PR / beauty activation. Why this case matters A useful precedent...
  - `2` `HC-006` / `lesson` | availability `active` | score `0.327075` | preview: Late build-up should not create indefinite WNC onsite obligation.
  - `3` `HC-006` / `case_narrative` | availability `active` | score `0.318506` | preview: Case 06: Sheso Trading Event Rental type: PR / industry event with high guest turnover, client team, external catering and wellness eleme...

### `fake snow cleanup`

- category: `Operational problem`
- expected cases: `HC-007`
- preferred unit types: `decision, lesson, responsibility, case_narrative`
- required success condition: `Hit@1`
- fixture note: HC-007 contains exact fake-snow and cleanup language.
- FTS rank: `1`
- semantic rank: `1`
- semantic Hit@1: `yes`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- comparison: FTS and semantic search produced the same expected-case rank
- semantic query latency: `1740.01 ms`
- top semantic result: `HC-007` / `decision` / score `0.450033`
- top semantic cases/units:
  - `1` `HC-007` / `decision` | availability `active` | score `0.450033` | preview: Fake snow is not permitted.
  - `2` `HC-007` / `lesson` | availability `active` | score `0.424392` | preview: Fake snow is prohibited in this historical precedent.
  - `3` `HC-007` / `case_narrative` | availability `active` | score `0.411343` | preview: Case 07: MOOI / Little Wonderland PR Activation Rental type: Whole-venue PR / beauty activation. Why this case matters A useful precedent...

### `external storage`

- category: `Operational problem`
- expected cases: `HC-001, HC-003`
- preferred unit types: `decision, lesson, case_narrative`
- required success condition: `Hit@3`
- fixture note: Both HC-001 and HC-003 discuss external storage, so case-level top-three coverage is sufficient.
- FTS rank: `1`
- semantic rank: `1`
- semantic Hit@1: `yes`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- comparison: FTS and semantic search produced the same expected-case rank
- semantic query latency: `1247.65 ms`
- top semantic result: `HC-001` / `decision` / score `0.414712`
- top semantic cases/units:
  - `1` `HC-001` / `decision` | availability `active` | score `0.414712` | preview: External storage was used because onsite space was insufficient.
  - `2` `HC-001` / `lesson` | availability `active` | score `0.366753` | preview: Offsite storage can become necessary when onsite capacity is insufficient.
  - `3` `HC-006` / `decision` | availability `active` | score `0.366574` | preview: For one-day activations, storage volume must be discussed explicitly, not just whether storage is needed.

### `competitor branding`

- category: `Operational problem`
- expected cases: `HC-008`
- preferred unit types: `decision, responsibility, lesson`
- required success condition: `Hit@1`
- fixture note: HC-008 is the branded-company / competitor-visibility precedent.
- FTS rank: `1`
- semantic rank: `1`
- semantic Hit@1: `yes`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- comparison: FTS and semantic search produced the same expected-case rank
- semantic query latency: `1796.78 ms`
- top semantic result: `HC-008` / `decision` / score `0.494864`
- top semantic cases/units:
  - `1` `HC-008` / `decision` | availability `limited` | score `0.494864` | preview: Competitor-brand visibility mattered materially to the client.
  - `2` `HC-008` / `responsibility` | availability `limited` | score `0.459425` | preview: The client imposed branded-company and competitor-visibility constraints on the event experience.
  - `3` `HC-008` / `lesson` | availability `limited` | score `0.440874` | preview: Ask about competitor-brand restrictions for branded-company events.

### `permit compliance`

- category: `Caution`
- expected cases: `HC-009`
- preferred unit types: `decision, lesson, responsibility, case_narrative`
- required success condition: `Hit@1`
- fixture note: HC-009 is the permit and compliance cautionary precedent.
- FTS rank: `1`
- semantic rank: `1`
- semantic Hit@1: `yes`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- comparison: FTS and semantic search produced the same expected-case rank
- semantic query latency: `1779.61 ms`
- top semantic result: `HC-009` / `lesson` / score `0.453203`
- top semantic cases/units:
  - `1` `HC-009` / `lesson` | availability `limited` | score `0.453203` | preview: Historical compliance solutions must not be reused without current legal checking.
  - `2` `HC-009` / `lesson` | availability `limited` | score `0.449043` | preview: High-impact or non-standard events need early permit and compliance review.
  - `3` `HC-009` / `responsibility` | availability `limited` | score `0.439828` | preview: WNC needed to trigger an early permit and compliance review for higher-impact ADE-style events.

### `client provided wine`

- category: `Responsibility`
- expected cases: `HC-005`
- preferred unit types: `responsibility, decision`
- required success condition: `Hit@1`
- fixture note: HC-005 contains exact wine-responsibility wording.
- FTS rank: `1`
- semantic rank: `1`
- semantic Hit@1: `yes`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- comparison: FTS and semantic search produced the same expected-case rank
- semantic query latency: `1194.39 ms`
- top semantic result: `HC-005` / `responsibility` / score `0.544156`
- top semantic cases/units:
  - `1` `HC-005` / `responsibility` | availability `active` | score `0.544156` | preview: The client provided the wine for the reception.
  - `2` `HC-003` / `responsibility` | availability `limited` | score `0.527831` | preview: WNC could include floral arrangement support where agreed.
  - `3` `HC-003` / `lesson` | availability `limited` | score `0.520898` | preview: WNC support can remain venue and production focused without turning into guest-facing service.

### `WNC cleared the venue`

- category: `Responsibility`
- expected cases: `HC-001`
- preferred unit types: `responsibility, decision`
- required success condition: `Hit@1`
- fixture note: HC-001 contains the clearest white-box clearing language.
- FTS rank: `2`
- semantic rank: `4`
- semantic Hit@1: `no`
- semantic Hit@3: `no`
- semantic ground-truth satisfied: `no`
- comparison: FTS ranked the expected case higher
- semantic query latency: `1281.76 ms`
- top semantic result: `HC-003` / `responsibility` / score `0.466720`
- top semantic cases/units:
  - `1` `HC-003` / `responsibility` | availability `limited` | score `0.466720` | preview: WNC provided venue cleanliness and operational support.
  - `2` `HC-004` / `responsibility` | availability `limited` | score `0.460422` | preview: WNC provided the venue and practical overflow use of the 1:1 / Podcast Room.
  - `3` `HC-003` / `responsibility` | availability `limited` | score `0.450727` | preview: WNC handled venue preparation and agreed production setup.

### `external caterer responsibility`

- category: `Responsibility`
- expected cases: `HC-003, HC-006`
- preferred unit types: `responsibility`
- required success condition: `Hit@3`
- fixture note: The corpus uses external-suppliers wording rather than a standardized external-caterer phrase.
- FTS rank: `1`
- semantic rank: `1`
- semantic Hit@1: `yes`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- comparison: FTS and semantic search produced the same expected-case rank
- semantic query latency: `1425.23 ms`
- top semantic result: `HC-006` / `responsibility` / score `0.520329`
- top semantic cases/units:
  - `1` `HC-006` / `responsibility` | availability `active` | score `0.520329` | preview: External suppliers supported catering and wellness elements where engaged.
  - `2` `HC-004` / `responsibility` | availability `limited` | score `0.520317` | preview: The client controlled catering decisions and PR or brand-event operation.
  - `3` `HC-005` / `responsibility` | availability `active` | score `0.501714` | preview: External suppliers supported catering or AV scope where engaged.

### `current legal precedent`

- category: `Caution`
- expected cases: `HC-009`
- preferred unit types: `decision, lesson, case_narrative`
- required success condition: `Hit@1`
- fixture note: HC-009 explicitly says the historical ADE solution is not current legal precedent.
- FTS rank: `1`
- semantic rank: `1`
- semantic Hit@1: `yes`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- comparison: FTS and semantic search produced the same expected-case rank
- semantic query latency: `1199.73 ms`
- top semantic result: `HC-009` / `decision` / score `0.510151`
- top semantic cases/units:
  - `1` `HC-009` / `decision` | availability `limited` | score `0.510151` | preview: The historical ADE solution is not current legal precedent.
  - `2` `HC-009` / `case_narrative` | availability `limited` | score `0.442763` | preview: ADE Event: Permit, Alcohol, Sound & Operational Compliance Planning for an ADE event exposed several issues that had not historically bee...
  - `3` `HC-009` / `lesson` | availability `limited` | score `0.401625` | preview: Historical compliance solutions must not be reused without current legal checking.

### `grace period setup`

- category: `Caution`
- expected cases: `HC-007`
- preferred unit types: `decision, lesson, case_narrative`
- required success condition: `Hit@1`
- fixture note: HC-007 explicitly ties the grace period to arrival rather than setup.
- FTS rank: `1`
- semantic rank: `1`
- semantic Hit@1: `yes`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- comparison: FTS and semantic search produced the same expected-case rank
- semantic query latency: `1286.76 ms`
- top semantic result: `HC-007` / `decision` / score `0.429172`
- top semantic cases/units:
  - `1` `HC-007` / `decision` | availability `active` | score `0.429172` | preview: The 30-minute entire-venue grace period is for arrival, not free setup time.
  - `2` `HC-007` / `lesson` | availability `active` | score `0.383738` | preview: Grace period does not equal setup time, and the historical misuse must not be treated as a current setup allowance.
  - `3` `HC-007` / `case_narrative` | availability `active` | score `0.378826` | preview: Case 07: MOOI / Little Wonderland PR Activation Rental type: Whole-venue PR / beauty activation. Why this case matters A useful precedent...

### `damage cleanup`

- category: `Caution`
- expected cases: `HC-007`
- preferred unit types: `responsibility, decision, case_narrative`
- required success condition: `Hit@3`
- fixture note: Damage and cleanup are both present in HC-007, but the wording is spread across multiple unit types.
- FTS rank: `1`
- semantic rank: `1`
- semantic Hit@1: `yes`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- comparison: FTS and semantic search produced the same expected-case rank
- semantic query latency: `1279.42 ms`
- top semantic result: `HC-007` / `responsibility` / score `0.349189`
- top semantic cases/units:
  - `1` `HC-007` / `responsibility` | availability `active` | score `0.349189` | preview: The client carried cleanup obligations for production materials.
  - `2` `HC-007` / `responsibility` | availability `active` | score `0.332567` | preview: WNC set cleanup and reset expectations and protected venue equipment.
  - `3` `HC-007` / `decision` | availability `active` | score `0.329316` | preview: Other residue or damage-prone materials should be discussed in advance.

### `300 storage`

- category: `Historical commercial specifics`
- expected cases: `HC-003`
- preferred unit types: `decision, case_narrative, lesson`
- required success condition: `Hit@1`
- fixture note: HC-003 contains the EUR 300 storage precedent.
- FTS rank: `1`
- semantic rank: `3`
- semantic Hit@1: `no`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `no`
- comparison: FTS ranked the expected case higher
- semantic query latency: `1271.54 ms`
- top semantic result: `HC-006` / `lesson` / score `0.453666`
- top semantic cases/units:
  - `1` `HC-006` / `lesson` | availability `active` | score `0.453666` | preview: Ask about approximate storage volume.
  - `2` `HC-006` / `decision` | availability `active` | score `0.453289` | preview: For one-day activations, storage volume must be discussed explicitly, not just whether storage is needed.
  - `3` `HC-003` / `lesson` | availability `limited` | score `0.426987` | preview: Clients should be asked how much must be stored, not just whether storage is needed.

### `florals`

- category: `Historical commercial specifics`
- expected cases: `HC-003`
- preferred unit types: `decision, responsibility, case_narrative`
- required success condition: `Hit@3`
- fixture note: The corpus uses floral-arrangement wording rather than a normalized floral-service taxonomy.
- FTS rank: `1`
- semantic rank: `1`
- semantic Hit@1: `yes`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- comparison: FTS and semantic search produced the same expected-case rank
- semantic query latency: `1278.97 ms`
- top semantic result: `HC-003` / `decision` / score `0.325849`
- top semantic cases/units:
  - `1` `HC-003` / `decision` | availability `limited` | score `0.325849` | preview: Haylin could provide floral arrangement support where included.
  - `2` `HC-003` / `responsibility` | availability `limited` | score `0.270331` | preview: WNC could include floral arrangement support where agreed.
  - `3` `HC-004` / `decision` | availability `limited` | score `0.229927` | preview: Strong-smelling food should be avoided for scent-sensitive beauty or perfume activations.

### `overtime charge`

- category: `Historical commercial specifics`
- expected cases: `HC-006`
- preferred unit types: `decision, lesson`
- required success condition: `Hit@1`
- fixture note: HC-006 is the overtime / staffing precedent for late build-up.
- FTS rank: `1`
- semantic rank: `1`
- semantic Hit@1: `yes`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- comparison: FTS and semantic search produced the same expected-case rank
- semantic query latency: `1433.92 ms`
- top semantic result: `HC-006` / `decision` / score `0.461050`
- top semantic cases/units:
  - `1` `HC-006` / `decision` | availability `active` | score `0.461050` | preview: If build-up runs late, additional WNC staffing or overtime should apply.
  - `2` `HC-006` / `decision` | availability `active` | score `0.362543` | preview: Build-up hours need a firm end time.
  - `3` `HC-007` / `decision` | availability `active` | score `0.327905` | preview: The 30-minute entire-venue grace period is for arrival, not free setup time.

### `discount exposure gifts`

- category: `Historical commercial specifics`
- expected cases: `HC-004`
- preferred unit types: `decision, lesson, responsibility`
- required success condition: `Hit@1`
- fixture note: HC-004 contains exact exposure / gifts / discount caution language.
- FTS rank: `1`
- semantic rank: `1`
- semantic Hit@1: `yes`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- comparison: FTS and semantic search produced the same expected-case rank
- semantic query latency: `1266.17 ms`
- top semantic result: `HC-004` / `decision` / score `0.446254`
- top semantic cases/units:
  - `1` `HC-004` / `decision` | availability `limited` | score `0.446254` | preview: Upcoming-brand status and gifts or exposure did not automatically justify discounted rental.
  - `2` `HC-004` / `lesson` | availability `limited` | score `0.410747` | preview: WNC should not discount merely because a brand is new or offers exposure or gifts.
  - `3` `HC-004` / `case_narrative` | availability `limited` | score `0.314436` | preview: Case 04: Amoué PR Wellness Event Rental type: Beauty / PR brand event with wellness programming. Why this case matters This event produce...

## 4. Semantic Paraphrase Benchmark

### `customer wanted the venue stripped back for several days`

- expected cases: `HC-001`
- preferred unit types: `case_narrative, decision, responsibility`
- required success condition: `Hit@3`
- fixture note: Paraphrases the whole-venue clearing and handover scenario without repeating the corpus wording.
- semantic rank: `1`
- semantic Hit@1: `yes`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- semantic query latency: `1283.35 ms`
- top semantic result: `HC-001` / `case_narrative` / score `0.470416`
- top semantic cases/units:
  - `1` `HC-001` / `case_narrative` | availability `active` | score `0.470416` | preview: Case 01: Merrachi Multi-Day Retail Pop-Up Rental type: Multi-day entire-venue brand / retail takeover. Why this case matters WNC’s cleare...
  - `2` `HC-006` / `case_narrative` | availability `active` | score `0.461829` | preview: Case 06: Sheso Trading Event Rental type: PR / industry event with high guest turnover, client team, external catering and wellness eleme...
  - `3` `HC-002` / `case_narrative` | availability `active` | score `0.435949` | preview: Case 02: Philips Coffee Machine Showcase Rental type: Brand activation / product showcase with significant technical and catering require...

### `event where smell could interfere with the brand experience`

- expected cases: `HC-004`
- preferred unit types: `decision, lesson, case_narrative`
- required success condition: `Hit@3`
- fixture note: Targets the scent-sensitive beauty-event precedent using brand-experience phrasing rather than smell wording.
- semantic rank: `1`
- semantic Hit@1: `yes`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- semantic query latency: `1307.96 ms`
- top semantic result: `HC-004` / `decision` / score `0.612197`
- top semantic cases/units:
  - `1` `HC-004` / `decision` | availability `limited` | score `0.612197` | preview: Strong-smelling food should be avoided for scent-sensitive beauty or perfume activations.
  - `2` `HC-004` / `lesson` | availability `limited` | score `0.526069` | preview: Scent-sensitive activations should avoid strong-smelling food.
  - `3` `HC-004` / `lesson` | availability `limited` | score `0.523588` | preview: Catering smell should match the intended guest experience.

### `production setup needed specialist electrical review`

- expected cases: `HC-002`
- preferred unit types: `decision, lesson, case_narrative`
- required success condition: `Hit@3`
- fixture note: Paraphrases the technical-load and qualified electrical-assessment precedent.
- semantic rank: `1`
- semantic Hit@1: `yes`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- semantic query latency: `1411.28 ms`
- top semantic result: `HC-002` / `decision` / score `0.475849`
- top semantic cases/units:
  - `1` `HC-002` / `decision` | availability `active` | score `0.475849` | preview: WNC should not independently validate complex electrical load; client production should bring qualified technical assessment.
  - `2` `HC-002` / `case_narrative` | availability `active` | score `0.426180` | preview: Case 02: Philips Coffee Machine Showcase Rental type: Brand activation / product showcase with significant technical and catering require...
  - `3` `HC-002` / `lesson` | availability `active` | score `0.420525` | preview: Recommend qualified electrical assessment for heavy-load setups.

### `event setup ran later than agreed`

- expected cases: `HC-006`
- preferred unit types: `decision, lesson, case_narrative`
- required success condition: `Hit@3`
- fixture note: Targets the late build-up and overtime precedent without using exact build-up wording.
- semantic rank: `2`
- semantic Hit@1: `no`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- semantic query latency: `1473.93 ms`
- top semantic result: `HC-007` / `decision` / score `0.384057`
- top semantic cases/units:
  - `1` `HC-007` / `decision` | availability `active` | score `0.384057` | preview: The 30-minute entire-venue grace period is for arrival, not free setup time.
  - `2` `HC-006` / `decision` | availability `active` | score `0.383638` | preview: Build-up hours need a firm end time.
  - `3` `HC-006` / `decision` | availability `active` | score `0.380316` | preview: If build-up runs late, additional WNC staffing or overtime should apply.

### `agency used a messy decorative material`

- expected cases: `HC-007`
- preferred unit types: `decision, lesson, responsibility, case_narrative`
- required success condition: `Hit@3`
- fixture note: Paraphrases the fake-snow cleanup precedent with broader decorative-material wording.
- semantic rank: `1`
- semantic Hit@1: `yes`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- semantic query latency: `1354.90 ms`
- top semantic result: `HC-007` / `case_narrative` / score `0.419395`
- top semantic cases/units:
  - `1` `HC-007` / `case_narrative` | availability `active` | score `0.419395` | preview: Case 07: MOOI / Little Wonderland PR Activation Rental type: Whole-venue PR / beauty activation. Why this case matters A useful precedent...
  - `2` `HC-007` / `decision` | availability `active` | score `0.385220` | preview: Other residue or damage-prone materials should be discussed in advance.
  - `3` `HC-007` / `responsibility` | availability `active` | score `0.376216` | preview: The client carried cleanup obligations for production materials.

### `client was worried about competitor logos being visible`

- expected cases: `HC-008`
- preferred unit types: `decision, responsibility, lesson`
- required success condition: `Hit@3`
- fixture note: Targets the branded-competitor visibility precedent using logo visibility language.
- semantic rank: `1`
- semantic Hit@1: `yes`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- semantic query latency: `1326.35 ms`
- top semantic result: `HC-008` / `decision` / score `0.505059`
- top semantic cases/units:
  - `1` `HC-008` / `decision` | availability `limited` | score `0.505059` | preview: Competitor-brand visibility mattered materially to the client.
  - `2` `HC-008` / `responsibility` | availability `limited` | score `0.482240` | preview: The client imposed branded-company and competitor-visibility constraints on the event experience.
  - `3` `HC-008` / `lesson` | availability `limited` | score `0.447354` | preview: Minor logo or equipment details can matter significantly to the client.

### `unusual event needed regulatory checks before approving it`

- expected cases: `HC-009`
- preferred unit types: `decision, lesson, responsibility, case_narrative`
- required success condition: `Hit@3`
- fixture note: Paraphrases the permit and compliance cautionary precedent without repeating permit wording.
- semantic rank: `1`
- semantic Hit@1: `yes`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- semantic query latency: `1151.68 ms`
- top semantic result: `HC-009` / `lesson` / score `0.481021`
- top semantic cases/units:
  - `1` `HC-009` / `lesson` | availability `limited` | score `0.481021` | preview: High-impact or non-standard events need early permit and compliance review.
  - `2` `HC-009` / `responsibility` | availability `limited` | score `0.480906` | preview: WNC needed to trigger an early permit and compliance review for higher-impact ADE-style events.
  - `3` `HC-009` / `decision` | availability `limited` | score `0.466311` | preview: Events involving DJs, amplified music, alcohol, non-standard guest use, or public-space activity should trigger early permit and complian...

### `did we ever charge for offsite storage because the venue had no room`

- expected cases: `HC-003, HC-001`
- preferred unit types: `decision, lesson, case_narrative`
- required success condition: `Hit@3`
- fixture note: Targets the historical offsite-storage precedents while preserving the risky historical-value boundary.
- semantic rank: `2`
- semantic Hit@1: `no`
- semantic Hit@3: `yes`
- semantic ground-truth satisfied: `yes`
- semantic query latency: `1342.40 ms`
- top semantic result: `HC-006` / `case_narrative` / score `0.476474`
- top semantic cases/units:
  - `1` `HC-006` / `case_narrative` | availability `active` | score `0.476474` | preview: Case 06: Sheso Trading Event Rental type: PR / industry event with high guest turnover, client team, external catering and wellness eleme...
  - `2` `HC-001` / `lesson` | availability `active` | score `0.395702` | preview: Offsite storage can become necessary when onsite capacity is insufficient.
  - `3` `HC-004` / `decision` | availability `limited` | score `0.387220` | preview: The 1:1 / Podcast Room was used as overflow storage in practice.

## 5. Aggregate Metrics

### Shared benchmark

- semantic Hit@1: `17 / 21 = 80.95%`
- semantic Hit@3: `19 / 21 = 90.48%`
- semantic MRR: `0.8730`
- FTS Hit@1: `17 / 21 = 80.95%`
- FTS Hit@3: `19 / 21 = 90.48%`

### Paraphrase benchmark

- semantic Hit@1: `6 / 8 = 75.00%`
- semantic Hit@3: `8 / 8 = 100.00%`
- semantic MRR: `0.8750`

## 6. Lexical Miss Recovery

- `whole venue clearing`: FTS rank `miss` vs semantic rank `1`; semantic search recovered a lexical miss.
- `sensory-sensitive beauty event`: FTS rank `miss` vs semantic rank `1`; semantic search recovered a lexical miss.
- `client operated event`: FTS rank `3` vs semantic rank `4`; FTS ranked the expected case higher.
- `WNC cleared the venue`: FTS rank `2` vs semantic rank `4`; FTS ranked the expected case higher.

## 7. Semantic Failure Analysis

- `client operated event`: category `ground-truth ambiguity`; semantic rank `4`; note: Expected case first appears at rank 4, outside the top three.
- `late build-up`: category `narrative dominating statement`; semantic rank `2`; note: Expected case appears at rank 2; top result is HC-007 / case_narrative.
- `WNC cleared the venue`: category `overly broad embedding similarity`; semantic rank `4`; note: Expected case first appears at rank 4, outside the top three.
- `300 storage`: category `overly broad embedding similarity`; semantic rank `3`; note: Expected case appears at rank 3; top result is HC-006 / lesson.

## 8. Safety Metadata Review

- `300 storage`: top result `HC-006` / `lesson` keeps `source_layer_role=historical_precedent`, `precedent_availability=active`, `lesson_kind=curated_lesson`, `historical_value_only=False`, `contamination_risk_level=medium`, `current_authority_disposition=check_phase_5`, `effective_confidentiality_level_code=restricted`, `primary_source_locator=Case 06: Sheso Trading Event`, `source_link_count=1`.
- `discount exposure gifts`: top result `HC-004` / `decision` keeps `source_layer_role=historical_precedent`, `precedent_availability=limited`, `lesson_kind=None`, `historical_value_only=True`, `contamination_risk_level=high`, `current_authority_disposition=current_status_unknown`, `effective_confidentiality_level_code=restricted`, `primary_source_locator=Case 04: Amoué PR Wellness Event`, `source_link_count=1`.
- `overtime charge`: top result `HC-006` / `decision` keeps `source_layer_role=historical_precedent`, `precedent_availability=active`, `lesson_kind=None`, `historical_value_only=True`, `contamination_risk_level=high`, `current_authority_disposition=check_phase_5`, `effective_confidentiality_level_code=restricted`, `primary_source_locator=Case 06: Sheso Trading Event`, `source_link_count=1`.
- `fake snow cleanup`: top result `HC-007` / `decision` keeps `source_layer_role=historical_precedent`, `precedent_availability=active`, `lesson_kind=None`, `historical_value_only=True`, `contamination_risk_level=high`, `current_authority_disposition=potential_conflict_with_current_knowledge`, `effective_confidentiality_level_code=restricted`, `primary_source_locator=Case 07: MOOI / Little Wonderland PR Activation`, `source_link_count=1`.
- `current legal precedent`: top result `HC-009` / `decision` keeps `source_layer_role=historical_precedent`, `precedent_availability=limited`, `lesson_kind=None`, `historical_value_only=True`, `contamination_risk_level=high`, `current_authority_disposition=potential_conflict_with_current_knowledge`, `effective_confidentiality_level_code=restricted`, `primary_source_locator=ADE Event: Permit, Alcohol, Sound & Operational Compliance`, `source_link_count=1`.
- `Later modelling may need`: top result `HC-009` / `lesson` keeps `source_layer_role=historical_precedent`, `precedent_availability=limited`, `lesson_kind=analyst_inference`, `historical_value_only=False`, `contamination_risk_level=low`, `current_authority_disposition=no_current_rule_implication`, `effective_confidentiality_level_code=restricted`, `primary_source_locator=ADE Event: Permit, Alcohol, Sound & Operational Compliance`, `source_link_count=1`.

## Comparison Summary

- semantic better on shared benchmark queries: `2`
- FTS better on shared benchmark queries: `4`
- ties on shared benchmark queries: `15`

