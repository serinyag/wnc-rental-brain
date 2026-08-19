# Phase 6 Ingestion Stage A Matrix

Date: August 7, 2026

## Summary

Task 6.3A loads the first production historical corpus slice for Phase 6:

- exactly nine stable historical case identities
- one draft `version_number = 1` case version per case
- one shared Historical Case Library source object reused across all nine versions
- one case-specific source locator association per case
- production precedent-topic assignments
- canonical rental-type assignments where justified
- canonical venue-space assignments where justified

Stage A intentionally stops before responsibilities, decisions, lessons, statement evidence links, current-authority relationships, and activation.

## Core Matrix

| Case | Stable Identity | Version | Availability | Type | Evidence Strength | Source Locator | Topics | Rental Types | Spaces | Status |
| ---- | --------------- | ------- | ------------ | ---- | ----------------- | -------------- | ------ | ------------ | ------ | ------ |
| `HC-001` | Merrachi Multi-Day Retail Pop-Up | `v1` draft | `active` | `full_case` | `strong` | `Case 01: Merrachi Multi-Day Retail Pop-Up` | `venue_clearing` (primary), `storage` (primary), `offsite_storage` (primary), `responsibility_boundaries` (primary), `client_operated_events` (primary), `class_schedule_interaction` (secondary) | `entire_venue` | `studio_space`, `one_to_one_room`, `retail_area`, `storage_room`, `back_office` | Loaded |
| `HC-002` | Philips Coffee Machine Showcase | `v1` draft | `active` | `full_case` | `strong` | `Case 02: Philips Coffee Machine Showcase` | `technical_assessment` (primary), `electrical_load` (primary), `materials_cleanup_damage` (primary), `catering_supplier_coordination` (secondary) | none | none | Loaded |
| `HC-003` | WineGB Trade & Press Showcase | `v1` draft | `active` | `full_case` | `strong` | `Case 03: WineGB Trade & Press Showcase` | `storage` (primary), `offsite_storage` (primary), `responsibility_boundaries` (primary), `client_operated_events` (secondary), `production_coordination` (primary) | none | none | Loaded |
| `HC-004` | Amoué PR Wellness Event | `v1` draft | `active` | `full_case` | `strong` | `Case 04: Amoué PR Wellness Event` | `catering_supplier_coordination` (primary), `branding_restrictions` (primary), `storage` (secondary) | none | `one_to_one_room` | Loaded |
| `HC-005` | British Embassy / GreenTech Corporate Reception | `v1` draft | `active` | `full_case` | `strong` | `Case 05: British Embassy / GreenTech Corporate Reception` | `responsibility_boundaries` (primary), `catering_supplier_coordination` (primary), `alcohol_beverage_boundaries` (primary), `technical_assessment` (secondary), `client_operated_events` (secondary) | none | none | Loaded |
| `HC-006` | Sheso Trading Event | `v1` draft | `active` | `full_case` | `strong` | `Case 06: Sheso Trading Event` | `storage` (primary), `responsibility_boundaries` (secondary), `production_access` (primary), `overtime` (primary), `venue_clearing` (secondary) | `entire_venue` | `retail_area` | Loaded |
| `HC-007` | MOOI / Little Wonderland PR Activation | `v1` draft | `active` | `full_case` | `strong` | `Case 07: MOOI / Little Wonderland PR Activation` | `production_access` (primary), `materials_cleanup_damage` (primary), `production_coordination` (secondary) | `entire_venue` | none | Loaded |
| `HC-008` | Vanessa Corporate Wellness Outing / Lululemon Branding Requirement | `v1` draft | `limited` | `limited_precedent` | `limited` | `Vanessa Corporate Wellness Outing / Lululemon Branding Requirement` | `branding_restrictions` (primary), `class_schedule_interaction` (primary) | `studio_space` | none | Loaded with limitations |
| `HC-009` | ADE Event Permit, Alcohol, Sound & Operational Compliance Precedent | `v1` draft | `limited` | `cautionary_precedent` | `limited` | `ADE Event: Permit, Alcohol, Sound & Operational Compliance` | `permits_compliance` (primary), `alcohol_beverage_boundaries` (secondary), `technical_assessment` (secondary) | none | none | Loaded with limitations |

## Aliases Loaded

| Case | Alias | Type | Why Loaded |
| ---- | ----- | ---- | ---------- |
| `HC-005` | `British Embassy` | `client` | Dual-titled identity; materially useful alternate label for the same reception |
| `HC-005` | `GreenTech` | `shorthand` | Dual-titled identity; materially useful alternate label retained in the corpus |
| `HC-007` | `MOOI` | `brand` | Dual-branded activation title |
| `HC-007` | `Little Wonderland` | `brand` | Dual-branded activation title |
| `HC-008` | `Vanessa` | `person` | The source title combines a person/event label with a separate brand requirement |
| `HC-008` | `Lululemon` | `brand` | Brand-specific restriction is part of the stable case identity |

No other aliases were loaded. Titles were not split mechanically across the rest of the corpus.

## Case-Version Governance and Sensitivity

| Case | Governance | Event Status | Temporal Status | Confidentiality | PI Status |
| ---- | ---------- | ------------ | --------------- | --------------- | --------- |
| `HC-001` | `draft` | `completed` | `unknown` / no dates inserted | `restricted` | `yes` |
| `HC-002` | `draft` | `completed` | `unknown` / no dates inserted | `commercially_sensitive` | `no` |
| `HC-003` | `draft` | `completed` | `unknown` / no dates inserted | `restricted` | `yes` |
| `HC-004` | `draft` | `completed` | `unknown` / no dates inserted | `restricted` | `no` |
| `HC-005` | `draft` | `completed` | `unknown` / no dates inserted | `commercially_sensitive` | `no` |
| `HC-006` | `draft` | `completed` | `unknown` / no dates inserted | `restricted` | `no` |
| `HC-007` | `draft` | `completed` | `unknown` / no dates inserted | `restricted` | `no` |
| `HC-008` | `draft` | `completed` | `unknown` / no dates inserted | `commercially_sensitive` | `no` |
| `HC-009` | `draft` | `planning_only` | `unknown` / no dates inserted | `restricted` | `no` |

## Shared Source Object and Evidence Associations

Shared source object reused for all nine cases:

- `source_registry.source_code = HC-AMO-000`
- `knowledge_source_objects.origin_type = repository_file`
- `knowledge_source_objects.repository_relative_path = sources/phase-01-03/Historical Cases/WNC Rental Historical Case Library.docx`
- file size = `1048346`
- SHA-256 = `a938439534a2c2c9f34936a28e5d76c59b93117364a3ae2114cf90d9d7b145fd`
- artifact PI status = `yes`

All nine initial evidence associations use:

- role = `curated_case_library_source`
- association evidence strength = `moderate`
- case-specific confidentiality:
  - `restricted` for `HC-001`, `HC-003`, `HC-004`, `HC-006`, `HC-007`, `HC-009`
  - `commercially_sensitive` for `HC-002`, `HC-005`, `HC-008`

Supported claim dimensions loaded:

- `HC-001`, `HC-002`, `HC-003`, `HC-005`, `HC-006`: `identity`, `responsibility`, `decision`, `lesson`, `context`
- `HC-004`, `HC-007`, `HC-008`: `identity`, `decision`, `lesson`, `context`
- `HC-009`: `identity`, `lesson`, `context`

No Stage A source association claims `date` support.

## Source and Corpus Discrepancies

- `HC-009` keeps the corpus-matrix canonical title `ADE Event Permit, Alcohol, Sound & Operational Compliance Precedent`, while its source locator reflects the actual library heading `ADE Event: Permit, Alcohol, Sound & Operational Compliance`.
- `HC-008` and `HC-009` remain thinner precedents than the first seven cases and were loaded with `limited` availability and narrower precedent-type treatment.
- No exact event dates were inserted for any case, matching the corpus audit.

## Deliberate Omissions

Canonical rental-type links were deliberately omitted for:

- `HC-002`, `HC-003`, `HC-004`, `HC-005`, `HC-009`

Canonical venue-space links were deliberately omitted for:

- `HC-002`, `HC-003`, `HC-005`, `HC-007`, `HC-008`, `HC-009`

The rationale is the same in each omitted case: the corpus preserves meaningful historical narrative, but the current canonical rental-type or space model would have required inference beyond what the audited evidence justified.

## Deferred Scope

Stage A intentionally does not load:

- responsibilities
- historical decisions
- lessons
- statement-level evidence links
- Phase 4 relationships
- Phase 5 relationships
- exact current-authority references
- activation

Those remain deferred to Task 6.3B.
