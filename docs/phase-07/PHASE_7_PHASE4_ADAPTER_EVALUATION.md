# Phase 7 Phase 4 Adapter Evaluation

Date: August 8, 2026

## 1. Adapter Scope

This evaluation covers Phase 7 Task 7.2C only:

- Phase 4 adapter registry
- live RPC execution against local Supabase Phase 4 APIs
- normalization into frozen Phase 7 envelopes
- reasoning-state preservation
- direct and deep provenance preservation

It does not evaluate:

- Phase 5 wrapper execution
- Phase 6 adapter execution
- cross-layer orchestration
- context assembly
- answer generation

## 2. Domain Registry

Registered Phase 4 domains evaluated for 7.2C:

- `booking_fee`
- `payment`
- `expedited_surcharge`
- `cancellation`
- `capacity`
- `space_access`
- `operational_requirements`
- `catering_supplier`
- `technical_inventory`
- `technical_capability`
- `service_rules`
- `facilitator_requirements`

Registry coverage result:

- `12 / 12` frozen domains covered

## 3. Scenario Set

Phase 4 scenario set evaluated from the 7.0B / 7.2B matrix:

- `P7-EVAL-001`
- `P7-EVAL-002`
- `P7-EVAL-003`
- `P7-EVAL-004`
- `P7-EVAL-005`
- `P7-EVAL-006`
- `P7-EVAL-007`
- `P7-EVAL-010`
- `P7-EVAL-024`
- `P7-EVAL-030`
- `P7-EVAL-031`
- `P7-EVAL-035`
- `P7-EVAL-036`

## 4. Results by Scenario

| Scenario | Planned Domain(s) | Executed RPC(s) | Expected Rule(s) | Returned Rule(s) | Typed Value / State | Normalized Reasoning | Provenance | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P7-EVAL-001` | `payment` | `api.get_payment_rules` | `PAYMENT_CONFIRMATION_MINIMUM_30_PERCENT` | `PAYMENT_CONFIRMATION_MINIMUM_30_PERCENT` | `percentage_due = 30.0` | `resolved` | direct + deep | pass |
| `P7-EVAL-002` | `expedited_surcharge` | `api.get_expedited_surcharge_rule` | `EXPEDITED_SURCHARGE_WITHIN_14_DAYS` | `EXPEDITED_SURCHARGE_WITHIN_14_DAYS` | `applies = true` | `resolved` | direct + deep | pass |
| `P7-EVAL-003` | `capacity` | `api.get_capacity_rule` | `CAPACITY_ENTIRE_VENUE_LEGAL_MAXIMUM` | `CAPACITY_ENTIRE_VENUE_LEGAL_MAXIMUM` | `max_guests = 110` | `resolved` | direct + deep | pass |
| `P7-EVAL-004` | `capacity` | `api.get_capacity_rule` | `CAPACITY_STUDIO_LYING_DOWN` | `CAPACITY_STUDIO_LYING_DOWN` | `max_guests = 25` | `resolved` | direct + deep | pass |
| `P7-EVAL-005` | `space_access` | `api.evaluate_space_access` | `ACCESS_ENTIRE_VENUE_ONE_TO_ONE_INCLUDED` | `ACCESS_ENTIRE_VENUE_ONE_TO_ONE_INCLUDED` | `access_status = included` | `resolved` | direct + deep | pass |
| `P7-EVAL-006` | `payment` | `api.get_payment_rules` | `PAYMENT_FINAL_BALANCE_70_PERCENT_14_DAYS` | `PAYMENT_FINAL_BALANCE_70_PERCENT_14_DAYS` | `deadline_value = 14` | `resolved` | direct + deep | pass |
| `P7-EVAL-007` | `catering_supplier` | `api.get_catering_supplier_rules` | `CATER_EXTERNAL_CATERER_ALLOWED` | `CATER_EXTERNAL_CATERER_ALLOWED` | `outcome = allowed` | `resolved` | direct + deep | pass |
| `P7-EVAL-010` | `facilitator_requirements` | `api.get_facilitator_requirements` | `FACILITATOR_WNC_PROVIDED_CONFIRMATION_REQUIRED` | `FACILITATOR_WNC_PROVIDED_CONFIRMATION_REQUIRED` | `requires_availability_confirmation = true` | `requires_confirmation` | direct + deep | pass |
| `P7-EVAL-024` | `technical_capability` | `api.evaluate_technical_requirement` | `TECH_REQ_CUSTOM_TECH_CONFIRM` | `TECH_REQ_CUSTOM_TECH_CONFIRM` | `support_status = requires_confirmation` | `requires_confirmation` | direct + deep | pass |
| `P7-EVAL-030` | `operational_requirements` | `api.get_operational_requirements` | `OPER_SETUP_START_AT_BOOKED_TIME` | `OPER_SETUP_START_AT_BOOKED_TIME` | `timing_reference = booked_start_time` | `resolved` | direct + deep | pass |
| `P7-EVAL-031` | `space_access` | `api.evaluate_space_access` | `ACCESS_STUDIO_BACK_OFFICE_RESTRICTED` | `ACCESS_STUDIO_BACK_OFFICE_RESTRICTED` | `applicability_status = restricted` | `requires_confirmation` | direct + deep | pass |
| `P7-EVAL-035` | `technical_capability` | `api.evaluate_technical_requirement` | `TECH_REQ_CUSTOM_TECH_CONFIRM` | `TECH_REQ_CUSTOM_TECH_CONFIRM` | `client_may_self_organise = true` | `requires_confirmation` | direct + deep | pass |
| `P7-EVAL-036` | `capacity` | `api.evaluate_capacity` | benchmark did not require an exact code | `CAPACITY_ONE_TO_ONE_REQUIRES_CONFIRMATION` | `capacity_evaluation_status = requires_confirmation` | `requires_confirmation` | direct + deep | pass |

## 5. Aggregate Metrics

Measured adapter metrics:

- planned Phase 4 domain execution accuracy: `100%` (`13 / 13`)
- expected rule-code Hit rate: `100%` (`12 / 12` scenarios with explicit expected codes)
- deterministic typed-value accuracy: `100%` (`13 / 13`)
- normalized reasoning-state accuracy: `100%` (`13 / 13`)
- provenance completeness: `100%` (`12 / 12` rule-backed scenario results carried direct source codes plus deep enrichment)
- adapter execution success rate: `100%` (`13 / 13`)
- no-result / failure distinction accuracy: `100%` (`2 / 2` dedicated tests: one `no_applicable_rule`, one technical failure)

## 6. Uncertainty Tests

Uncertainty-specific checks passed:

- custom technical setup normalized to `requires_confirmation` with `TECH_REQ_CUSTOM_TECH_CONFIRM`
- 1:1 / Podcast Room capacity evaluation normalized to `requires_confirmation` while preserving `capacity_evaluation_status = requires_confirmation`
- missing payment lead-time input normalized to `insufficient_information` without inventing a deadline rule

## 7. No-Rule Tests

No-rule behavior was tested with:

- `catering_supplier`
- inputs: `external_caterer` + `allowance`

Observed result:

- execution succeeded
- normalized item returned
- reasoning state = `no_applicable_rule`
- no Phase 5 or Phase 6 substitution occurred

## 8. Failure Tests

Failure behavior was tested with a mocked database/RPC failure.

Observed result:

- `LayerExecutionRecord.execution_state = failed`
- `result_count = 0`
- no synthetic deterministic rule appeared
- safe error metadata named the failed Phase 4 domain without leaking runtime internals

## 9. Provenance Review

Representative rule-backed results confirmed:

- direct RPC source-code arrays are preserved
- deep enrichment adds `source_registry_ids`
- deep enrichment adds relation-aware source rows
- locators are populated from `relative_source_path` or `original_filename`
- provenance remains JSON serializable

Examples validated:

- payment confirmation rule
- whole-venue capacity rule
- entire-venue 1:1 room access rule
- custom technical confirmation rule

## 10. Deviations / Benchmark Mismatches

No repository contradiction blocked 7.2C.

Clarifications surfaced during live evaluation:

- `P7-EVAL-036` returns the live rule code `CAPACITY_ONE_TO_ONE_REQUIRES_CONFIRMATION`; the benchmark prompt required the reasoning outcome but did not freeze an exact code for that scenario
- the prompt’s operational exact-rule expectations included both `OPER_ENTIRE_VENUE_GRACE_PERIOD` and `OPER_SETUP_START_AT_BOOKED_TIME`; the formal scenario set exercised `OPER_SETUP_START_AT_BOOKED_TIME`, while multi-domain and direct adapter tests separately confirmed `OPER_ENTIRE_VENUE_GRACE_PERIOD`
