# Phase 6 Historical Search-Unit Readiness Audit

Date: August 7, 2026

## 1. Executive Summary

The active historical corpus now materializes a separate governed historical retrieval foundation.

Final derived state:

- active production case versions represented: `9`
- eligible limited-precedent cases preserved: `HC-003`, `HC-004`, `HC-008`, `HC-009`
- current historical narratives: `9`
- current historical responsibilities: `35`
- current historical decisions: `25`
- current historical lessons: `43`
- current historical search units total: `112`
- lineage completeness: `112 / 112`
- primary locator completeness: `112 / 112`
- analyst-inference lesson units preserved: `8`
- Phase 5 current chunks affected: `0`

## 2. Derived Object Inventory

Created in the `private` schema:

- `historical_case_version_processing`
- `historical_case_search_units`
- `historical_case_unit_sources`
- `current_historical_case_search_units`
- `rebuild_historical_case_search_units_for_version(bigint)`
- `rebuild_current_historical_case_search_units()`

The seed flow now ends with:

- `select private.rebuild_current_historical_case_search_units();`

This makes the active historical retrieval layer deterministic on every `npx supabase db reset`.

## 3. Production Materialization Matrix

Per-type totals:

- `case_narrative`: `9`
- `responsibility`: `35`
- `decision`: `25`
- `lesson`: `43`

Per-case materialization:

| Case | Narrative | Responsibilities | Decisions | Lessons | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| `HC-001` | 1 | 3 | 3 | 5 | 12 |
| `HC-002` | 1 | 5 | 3 | 5 | 14 |
| `HC-003` | 1 | 7 | 3 | 7 | 18 |
| `HC-004` | 1 | 3 | 3 | 5 | 12 |
| `HC-005` | 1 | 5 | 3 | 4 | 13 |
| `HC-006` | 1 | 4 | 3 | 6 | 14 |
| `HC-007` | 1 | 4 | 3 | 5 | 13 |
| `HC-008` | 1 | 3 | 2 | 3 | 9 |
| `HC-009` | 1 | 1 | 2 | 3 | 7 |

## 4. Provenance Completeness

Every current production historical search unit resolves through:

search unit
-> `historical_case_unit_sources`
-> `historical_case_version_source_objects`
-> `knowledge_source_objects`
-> case-specific source locator

Audit result:

- units with lineage: `112 / 112`
- units missing lineage: `0`
- units with primary locator surfaced in the current view: `112 / 112`

No production unit is orphaned from governed evidence.

## 5. Eligibility and Exclusion Behavior

The current historical retrieval surface includes only:

- `governance_status = 'active'`
- `precedent_availability in ('active', 'limited')`

Included limited-precedent case totals:

- `HC-003`: `18`
- `HC-004`: `12`
- `HC-008`: `9`
- `HC-009`: `7`

Validated exclusions:

- `held` cases do not materialize
- `archived` cases do not materialize
- `draft` cases do not materialize
- `superseded` cases do not materialize
- `retired` cases do not materialize

## 6. Metadata Preservation

Historical units remain distinguishable from current knowledge through:

- `source_layer_role = 'historical_precedent'`
- case and version identity
- precedent type
- precedent availability
- case and unit evidence strength
- `actor_type`
- `lesson_kind`
- `historical_value_only`
- `contamination_risk_level`
- `current_authority_disposition`
- case-level historical-value summary state

Representative preserved outcomes:

- `HC-003` EUR 300 decision remains `limited`, `historical_value_only = true`, contamination `high`, authority disposition `potential_conflict_with_current_knowledge`
- `HC-009` compliance warning remains a `caution_warning` lesson with `historical_value_only = true` and contamination `high`
- analyst-inference lessons remain separately identifiable with total `8`

## 7. Confidentiality and PI Behavior

Derived units preserve both case-level and source-level privacy metadata, plus the strictest confidentiality across parent-case and linked evidence rows.

Representative audit rows:

| Case | Unit | Effective Confidentiality | Case PI | Source PI |
| --- | --- | --- | --- | --- |
| `HC-003` | `case_narrative` | `restricted` | `yes` | `yes` |
| `HC-004` | `case_narrative` | `restricted` | `no` | `yes` |
| `HC-008` | `case_narrative` | `commercially_sensitive` | `no` | `yes` |

This keeps derived historical search units safe for later surfaced retrieval rules.

## 8. Rebuild and Immutability Result

Rebuild behavior is deterministic and idempotent.

Verified outcomes:

- repeated rebuilds preserve `source_key -> search_unit_id` identity
- rebuilds do not mutate governed Phase 6 source tables
- processing state correctly records repeat rebuild attempts

Two implementation issues were found and corrected during audit:

- the initial processing-state success constraint blocked a version from moving from prior `succeeded` back to `in_progress` on a later rebuild attempt
- the first exclusion test attempted an invalid direct `draft -> superseded` transition instead of the governed lifecycle path

## 9. Security and Isolation

The new derived layer remains private.

Validated controls:

- RLS enabled on new private tables
- direct reads denied to `anon`
- direct reads denied to `authenticated`
- direct reads denied to `service_role`

Phase 5 isolation result:

- `private.current_knowledge_chunks` remains `0`

Historical retrieval materialization is therefore still separated from the Phase 5 current-knowledge retrieval layer.

## 10. Validation Result

Executed validation:

- `npx supabase db reset`
- targeted pgTAP run: `supabase/tests/30_phase_06_historical_search_unit_provenance_foundation.sql`
  - result: `1` file / `26` tests / `PASS`
- full pgTAP run: `supabase/tests`
  - result: `30` files / `833` tests / `PASS`

## 11. Readiness Decision

The active historical corpus is now ready for the next historical retrieval stage.

Final conclusion:

- `READY_FOR_6_4B`
