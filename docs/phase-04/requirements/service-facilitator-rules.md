# Service And Facilitator Requirement Rules

## Objective

Model the approved WNC service-level, service-item, and facilitator-arrangement rules without turning Phase 4 into a live facilitator-booking system or an individual facilitator catalogue.

## Business Questions

- What service level is available?
- Which service items are current approved WNC offerings?
- Is a service included by default, separately available, conditional, or manual-review scope?
- Does the requested service require WNC confirmation and written scope?
- Does the service require WNC coordination?
- Can the client provide their own facilitator?
- Does a WNC-arranged facilitator require availability confirmation?
- Can the system commit to a facilitator before confirmation?
- Who remains responsible for the facilitator arrangement?
- Which operational and technical dependencies remain authoritative in other domains?

## Cross-Domain Boundary

This slice adds service and facilitator arrangement policy only.

Still authoritative elsewhere:

- `operational_requirements`: supplier or facilitator access timing, support-space handling, timeline capture, and venue-use restrictions
- `technical_capability_rules`: facilitator equipment, power, projection, sound, or livestream feasibility
- `catering_supplier_rules`: beverage, catering, bar, and supplier overlays
- `space_access_rules`: room inclusion or restriction
- `capacity_rules`: guest-capacity consequences for the chosen activity or layout
- `cancellation_rules`: facilitator-related commercial cancellation charges are still outside this slice

This slice does not duplicate those rule families.

## Inputs

Current typed retrieval supports:

- `service_level`
- `service_type`
- `facilitator_arrangement`
- `as_of_date`

The current source-backed slice does not add speculative dimensions such as facilitator identity, personal availability, biography, ranking, or live calendar state.

## Structured Outputs

Current service-rule outputs are represented through:

- `availability_status`: `available`, `conditional`, `manual_review_required`
- `included_by_default`
- `requires_confirmation`
- `requires_written_scope`
- `manual_quote_required`
- `external_supplier_required`
- `client_approval_required`
- `wnc_coordination_required`
- `manual_review_required`

Current facilitator-arrangement outputs are represented through:

- `arrangement_status`: `not_applicable`, `allowed`, `conditional`, `manual_review_required`
- `responsible_party`
- `client_commitment_requires_facilitator_confirmation`
- `requires_availability_confirmation`
- `requires_scope_confirmation`
- `requires_technical_confirmation`
- `client_provided_allowed`
- `wnc_coordination_available`
- `wnc_coordination_required`
- `requires_confirmation`
- `manual_review_required`

The implementation does not flatten everything into one generic status string. For example, a client-provided facilitator can be `allowed` while still requiring scope and technical confirmation.

## Architecture Decision

This slice uses two typed rule tables:

- `public.service_rules`
- `public.facilitator_requirement_rules`

That keeps overall service level separate from individual service items, while still keeping the schema smaller than three or more specialized tables.

Important current canonical boundary:

- `production_coordination` is a current canonical `service_type`, not a `service_level`
- current canonical `service_level` values are `venue_only`, `supported_rental`, and `full_production`

## Current Canonical Vocabulary

Current seeded `service_level` values:

- `venue_only`
- `supported_rental`
- `full_production`

Current seeded `service_type` values in this slice:

- `onsite_host`
- `event_manager`
- `production_coordination`
- `furniture_equipment_sourcing`
- `catering_coordination`
- `facilitator_sourcing`
- `experience_design`
- `setup_support`
- `breakdown_reset_support`
- `technical_coordination`
- `beverage_package`
- `cleaning_service`
- `other_service`

Current seeded `facilitator_arrangement` values:

- `none`
- `client_provided`
- `wnc_provided`
- `recommendation_requested`
- `custom_experience_design`
- `under_consideration`
- `unknown`

## Approved Rules Represented

Current seeded service-level policy covers:

- `venue_only` as the standard venue-rental scope without added WNC operational or production services
- `supported_rental` as a written-scope service level that includes only the specifically agreed support deliverables
- `full_production` as a broader WNC-managed production scope that always requires explicit written scope and manual quote

Current seeded service-item policy covers:

- practical venue-support services such as `onsite_host`, `setup_support`, and `breakdown_reset_support`
- coordination services such as `production_coordination`, `furniture_equipment_sourcing`, `catering_coordination`, `facilitator_sourcing`, and `technical_coordination`
- creative or planning services such as `experience_design`
- scope-defined add-ons such as `beverage_package` and `cleaning_service`
- `other_service` as explicit manual-review scope rather than an inherited default

Current seeded facilitator-arrangement policy covers:

- `none` as not applicable
- `client_provided` as allowed while leaving client responsibility in place
- `wnc_provided` as confirmation-sensitive and availability-sensitive
- `recommendation_requested` as WNC-coordinated but not committed before confirmation
- `custom_experience_design` as manual-review scope
- `under_consideration` and `unknown` as uncertainty-preserving states

## Intentionally Excluded

This slice does not build:

- the deferred `WNC Facilitators & Rental Experiences` catalogue
- individual facilitator profiles
- facilitator contact records
- facilitator biographies
- individual class descriptions as authoritative rental products
- facilitator ranking or recommendation scoring
- facilitator outreach workflows
- live facilitator availability
- individual facilitator calendars
- live facilitator booking
- broad service pricing tables

## Controlled Gaps

Two deliberate boundaries remain documented instead of being guessed:

- the individual facilitator catalogue remains deferred to future enhancement `FE-002`
- `additional_host` appears in the services catalogue but is missing from the current approved Data Dictionary `service_type` machine-value list, so the current slice records that as blocker `BLK-022` instead of inventing an uncontrolled enum value

## Missing-Information Semantics

- Missing `service_level` and `service_type` returns `insufficient_information` from `api.get_service_rules(...)`
- Unknown or unseeded `service_level` or `service_type` returns `no_applicable_rule`
- Missing `facilitator_arrangement` returns `insufficient_information` from `api.get_facilitator_requirements(...)`
- Unknown `facilitator_arrangement` returns `no_applicable_rule`

## Query Surfaces

- `public.current_service_rules`
- `api.get_service_rules(p_service_level, p_service_type, p_as_of_date)`
- `public.current_facilitator_requirement_rules`
- `api.get_facilitator_requirements(p_facilitator_arrangement, p_as_of_date)`

## Example Queries

```sql
select service_level, availability_status, included_by_default
from api.get_service_rules(
  'venue_only',
  null,
  date '2026-08-05'
);
```

Expected current result: `venue_only`, `available`, included by default.

```sql
select service_type, availability_status, requires_written_scope, manual_quote_required
from api.get_service_rules(
  null,
  'production_coordination',
  date '2026-08-05'
);
```

Expected current result: `production_coordination` stays conditional, written-scope, and manual-quote based.

```sql
select facilitator_arrangement, arrangement_status, requires_availability_confirmation, client_commitment_requires_facilitator_confirmation
from api.get_facilitator_requirements(
  'wnc_provided',
  date '2026-08-05'
);
```

Expected current result: WNC-provided facilitator path is conditional and cannot be committed before availability confirmation.

```sql
select facilitator_arrangement, arrangement_status, responsible_party, client_provided_allowed
from api.get_facilitator_requirements(
  'client_provided',
  date '2026-08-05'
);
```

Expected current result: client-provided facilitator is allowed and remains client responsibility.
