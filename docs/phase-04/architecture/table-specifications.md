# Table Specifications

## Design Approach

- Use text columns plus `CHECK` constraints for business vocabularies that are still evolving.
- Reserve PostgreSQL enums for values that are truly stable at the infrastructure level.
- Keep mutable governance fields explicit.
- Keep typed rule values in typed tables, not in generic JSON payloads.

## Implemented Foundation Tables

### `public.source_registry`

| Column | PostgreSQL type | Null? | Default | Constraint/FK | Purpose |
| ------ | --------------- | ----- | ------- | ------------- | ------- |
| `id` | `bigint` | no | identity | primary key | surrogate key |
| `source_code` | `text` | no | none | unique, non-empty | stable source identifier such as `GOV-003` |
| `title` | `text` | no | none | non-empty | human-readable title |
| `source_type` | `text` | no | none | non-empty | broad source category |
| `authority_level` | `text` | no | none | check-constrained | `authoritative`, `guidance`, `reference_only`, or `unverified` |
| `lifecycle_status` | `text` | no | none | non-empty | current, draft, historical, export, or similar lifecycle note |
| `original_filename` | `text` | no | none | non-empty | preserved source filename |
| `relative_source_path` | `text` | no | none | unique, non-empty | path under `sources/phase-01-03/` |
| `effective_date` | `date` | yes | none | none | explicit source effective date when known |
| `notes` | `text` | yes | none | none | governance and conflict notes |
| `created_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |
| `updated_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |

Primary key:

- `id`

Indexes and constraints:

- unique `source_code`
- unique `relative_source_path`
- `authority_level` check constraint
- non-empty text checks on required text columns

Delete behavior:

- referenced by `rule_source_links` with `ON DELETE RESTRICT`

Mutability:

- mutable for governance metadata
- source identity fields should be treated as stable after first load

### `public.rental_types`

| Column | PostgreSQL type | Null? | Default | Constraint/FK | Purpose |
| ------ | --------------- | ----- | ------- | ------------- | ------- |
| `id` | `bigint` | no | identity | primary key | surrogate key |
| `rental_type_code` | `text` | no | none | unique, non-empty | canonical machine value |
| `display_name` | `text` | no | none | non-empty | human label |
| `description` | `text` | no | none | non-empty | canonical description |
| `is_active` | `boolean` | no | `true` | none | soft lifecycle flag |
| `created_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |
| `updated_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |

Constraints:

- unique `rental_type_code`

Delete behavior:

- future typed rule tables should use `ON DELETE RESTRICT`

Mutability:

- new rows added for new canonical values
- existing codes should not be repurposed

### `public.venue_spaces`

| Column | PostgreSQL type | Null? | Default | Constraint/FK | Purpose |
| ------ | --------------- | ----- | ------- | ------------- | ------- |
| `id` | `bigint` | no | identity | primary key | surrogate key |
| `space_code` | `text` | no | none | unique, non-empty | canonical machine value |
| `display_name` | `text` | no | none | non-empty | human label |
| `description` | `text` | no | none | non-empty | canonical description |
| `sort_order` | `integer` | no | `0` | check `>= 0` | stable display ordering |
| `is_active` | `boolean` | no | `true` | none | soft lifecycle flag |
| `created_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |
| `updated_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |

Constraints:

- unique `space_code`

Delete behavior:

- future typed rule tables should use `ON DELETE RESTRICT`

### `public.rule_catalogue`

| Column | PostgreSQL type | Null? | Default | Constraint/FK | Purpose |
| ------ | --------------- | ----- | ------- | ------------- | ------- |
| `id` | `bigint` | no | identity | primary key | surrogate key |
| `rule_code` | `text` | no | none | non-empty | stable logical rule identifier |
| `rule_domain` | `text` | no | none | non-empty | fee, payment, VAT, capacity, access, and similar domain |
| `rule_kind` | `text` | no | none | check-constrained | `hard_rule` or `conditional_rule` |
| `rule_version` | `integer` | no | none | check `> 0` | immutable version counter |
| `status` | `text` | no | none | check-constrained | `draft`, `active`, `superseded`, or `retired` |
| `effective_from` | `date` | yes | none | none | explicit start date when known |
| `effective_until` | `date` | yes | none | none | explicit end date when known |
| `plain_language_explanation` | `text` | no | none | non-empty | human-readable summary |
| `owner_role` | `text` | yes | none | none | accountable role where person is unknown |
| `supersedes_rule_id` | `bigint` | yes | none | self FK | prior rule version replaced by this row |
| `last_reviewed_at` | `date` | yes | none | none | governance review date |
| `created_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |
| `updated_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |

Primary key:

- `id`

Uniqueness and checks:

- unique `(rule_code, rule_version)`
- partial unique index on `rule_code` where `status = 'active'`
- `rule_kind` check constraint
- `status` check constraint
- date-range check preventing `effective_until < effective_from`
- self-supersession prevention

Delete behavior:

- `supersedes_rule_id` uses `ON DELETE RESTRICT`
- referenced by `rule_source_links` with `ON DELETE CASCADE` from the rule to its provenance links

Mutability:

- business values should not be overwritten in place
- status and supersession metadata may change during governance
- historical rows remain preserved

Versioning behavior:

- insert new row for rule change
- never reuse old row to represent the new policy

### `public.rule_source_links`

| Column | PostgreSQL type | Null? | Default | Constraint/FK | Purpose |
| ------ | --------------- | ----- | ------- | ------------- | ------- |
| `id` | `bigint` | no | identity | primary key | surrogate key |
| `rule_id` | `bigint` | no | none | FK to `rule_catalogue` | linked rule version |
| `source_id` | `bigint` | no | none | FK to `source_registry` | linked source |
| `relation_type` | `text` | no | none | check-constrained | `primary`, `supporting`, `governance`, or `conflict` |
| `citation_locator` | `text` | yes | none | none | sheet, page, section, or row locator |
| `notes` | `text` | yes | none | none | provenance context |
| `created_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |

Uniqueness and checks:

- unique `(rule_id, source_id, relation_type)`
- `relation_type` check constraint

Delete behavior:

- `rule_id` uses `ON DELETE CASCADE`
- `source_id` uses `ON DELETE RESTRICT`

Mutability:

- add links as provenance improves
- do not silently replace source links without review

## Implemented Typed Rule Table

### `public.booking_fee_rules`

| Column | PostgreSQL type | Null? | Default | Constraint/FK | Purpose |
| ------ | --------------- | ----- | ------- | ------------- | ------- |
| `rule_id` | `bigint` | no | none | PK, FK to `rule_catalogue` | governance parent |
| `rental_type_id` | `bigint` | no | none | FK to `rental_types` | fee scope |
| `duration_band_label` | `text` | no | none | non-empty | preserved source-facing duration label |
| `duration_min_hours` | `integer` | no | none | check `> 0` | lower normalized rental-hour bucket |
| `duration_max_hours` | `integer` | no | none | check `>= duration_min_hours` | upper normalized rental-hour bucket |
| `is_fee_charged` | `boolean` | no | `true` | none | explicit no-fee support for full-day Entire Venue |
| `fee_ex_vat` | `numeric(12,2)` | no | none | check `>= 0` | fee amount |
| `currency_code` | `text` | no | none | 3-letter uppercase check | explicit currency |
| `vat_rate` | `numeric(5,4)` | no | none | check between `0` and `1` | VAT rate |
| `is_refundable` | `boolean` | yes | none | conditional check | nullable because `no booking fee` is not applicable rather than refundable |
| `waiver_allowed` | `boolean` | yes | none | conditional check | nullable because `no booking fee` is not applicable |
| `waiver_authority` | `text` | yes | none | conditional check | approved waiver authority where applicable |
| `created_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |
| `updated_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |

Primary key:

- `rule_id`

Indexes and constraints:

- primary key also enforces one typed booking-fee row per governed rule version
- range checks on normalized hour buckets and commercial values
- conditional check so `is_fee_charged = false` requires `fee_ex_vat = 0` and non-applicable waiver/refund metadata
- conditional check so `waiver_allowed = true` requires `waiver_authority`
- trigger-enforced parent-domain validation: the parent `rule_catalogue` row must be `rule_domain = 'booking_fee'` and `rule_kind = 'hard_rule'`
- trigger-enforced overlap protection across rental type, normalized hour-bucket range, and effective-date window for non-draft rules

Delete behavior:

- `rule_id` uses `ON DELETE CASCADE`
- `rental_type_id` uses `ON DELETE RESTRICT`

Mutability:

- business-rule value changes should create a new governed rule version instead of editing an existing row in place
- technical corrections to draft rows are allowed before activation

Versioning behavior:

- future booking-fee changes should insert a new `rule_catalogue` version row and a new `booking_fee_rules` row
- superseded rows remain preserved for historical lookup

## Retrieval Surfaces

### `public.current_booking_fee_rules`

Application-facing current-state view for active booking-fee rules effective on the database server's current date.

The view exposes the stored hour-bucket boundaries, not raw minute boundaries.

### `api.get_booking_fee_rule(...)`

Lookup function that accepts:

- `rental_type_code`
- `booked_duration_minutes`
- optional `as_of_date`

Behavior:

- normalizes `booked_duration_minutes` with `private.normalize_rental_duration_hours(...)` before matching any booking-fee band
- returns one matching rule when inputs uniquely match
- returns no rows for missing or unsupported inputs
- raises an exception if bad data would cause more than one match

## Implemented Typed Rule Table

### `public.payment_rules`

| Column | PostgreSQL type | Null? | Default | Constraint/FK | Purpose |
| ------ | --------------- | ----- | ------- | ------------- | ------- |
| `rule_id` | `bigint` | no | none | PK, FK to `rule_catalogue` | governance parent |
| `payment_stage` | `text` | no | none | stage check | payment-policy stage such as option, confirmation, deadline, or final balance |
| `payment_plan_option` | `text` | yes | none | option check | `upfront_30` or `upfront_100` where applicable |
| `percentage_due` | `numeric(5,2)` | no | none | check `> 0` and `<= 100` | exact percentage represented by the rule row |
| `payment_basis` | `text` | no | none | basis check | currently `total_rental_fee` |
| `deadline_type` | `text` | no | none | deadline check | `at_confirmation`, `upon_cleared_receipt`, `days_before_event`, `days_after_booking`, or `hours_after_booking` |
| `deadline_value` | `integer` | yes | none | conditional check | relative deadline value where the deadline type needs one |
| `booking_lead_time_min_days` | `integer` | yes | none | conditional check | optional lower lead-time bound for rules whose applicability depends on confirmation timing |
| `booking_lead_time_max_days` | `integer` | yes | none | conditional check | optional upper lead-time bound for rules whose applicability depends on confirmation timing |
| `required_for_confirmation` | `boolean` | no | `false` | none | whether this payment must be satisfied to confirm the rental |
| `confirms_booking` | `boolean` | no | `false` | none | whether cleared receipt of this payment confirms the rental |
| `records_terms_acceptance` | `boolean` | no | `false` | none | whether this payment also records acceptance of the applicable terms |
| `exception_allowed` | `boolean` | no | `false` | none | whether an approved exception path exists |
| `exception_approver` | `text` | yes | none | conditional check | approving role for an allowed exception |
| `created_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |
| `updated_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |

Primary key:

- `rule_id`

Indexes and constraints:

- primary key also enforces one typed payment row per governed rule version
- percentage, deadline, and lead-time checks reject impossible policy values while allowing open-ended lead-time applicability such as `15 or more days`
- stage-specific checks prevent invalid combinations such as a final-balance rule without `upfront_30`
- conditional check so `exception_allowed = true` requires `exception_approver`
- trigger-enforced parent-domain validation: the parent `rule_catalogue` row must be `rule_domain = 'payment'` and `rule_kind = 'hard_rule'`
- trigger-enforced overlap protection applies only within the same payment stage and payment-plan scope, so cumulative rules across different stages can coexist

Delete behavior:

- `rule_id` uses `ON DELETE CASCADE`

Mutability:

- business-rule value changes should create a new governed rule version instead of editing an existing row in place
- technical corrections to draft rows are allowed before activation

Versioning behavior:

- future payment-policy changes should insert a new `rule_catalogue` version row and a new `payment_rules` row
- superseded rows remain preserved for historical lookup

## Retrieval Surfaces

### `public.current_payment_rules`

Application-facing current-state view for active payment rules effective on the database server's current date.

### `api.get_payment_rules(...)`

Lookup function that accepts:

- optional `payment_stage`
- optional `payment_plan_option`
- optional `booking_lead_time_days`
- optional `as_of_date`

Behavior:

- returns zero, one, or multiple rows
- allows multiple stage-specific rules to coexist
- suppresses contingent rules when required context such as `booking_lead_time_days` or `payment_plan_option` is missing
- uses stored lead-time applicability on option and final-balance rows so `0-14 day` confirmations cannot return the `upfront_30` path
- preserves the stored relative policy semantics instead of deriving live due dates

## Implemented Typed Rule Table

### `public.expedited_surcharge_rules`

| Column | PostgreSQL type | Null? | Default | Constraint/FK | Purpose |
| ------ | --------------- | ----- | ------- | ------------- | ------- |
| `rule_id` | `bigint` | no | none | PK, FK to `rule_catalogue` | governance parent |
| `lead_time_min_days` | `integer` | no | none | check `>= 0` | inclusive lower calendar lead-time bound |
| `lead_time_max_days` | `integer` | no | none | check `>= lead_time_min_days` | inclusive upper calendar lead-time bound |
| `percentage_rate` | `numeric(5,4)` | no | none | check `> 0` and `<= 1` | structured rate representation of the 10% surcharge |
| `calculation_basis` | `text` | no | none | basis check | canonical basis value, currently `venue_rental_only` |
| `vat_rate` | `numeric(5,4)` | no | none | check `>= 0` and `<= 1` | VAT rate applied to the surcharge line item |
| `waiver_allowed` | `boolean` | no | `false` | none | whether the surcharge may be waived |
| `waiver_authority` | `text` | yes | none | conditional check | approving role for a permitted waiver |
| `created_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |
| `updated_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |

Primary key:

- `rule_id`

Indexes and constraints:

- primary key also enforces one typed expedited-surcharge row per governed rule version
- lead-time range checks reject negative or inverted calendar lead-time windows
- rate and VAT checks reject impossible percentage values
- conditional check so `waiver_allowed = true` requires `waiver_authority`
- trigger-enforced parent-domain validation: the parent `rule_catalogue` row must be `rule_domain = 'expedited_surcharge'` and `rule_kind = 'hard_rule'`
- trigger-enforced overlap protection rejects multiple active or historical rule rows with overlapping lead-time windows in the same effective-date window

Delete behavior:

- `rule_id` uses `ON DELETE CASCADE`

Mutability:

- business-rule value changes should create a new governed rule version instead of editing an existing row in place
- technical corrections to draft rows are allowed before activation

Versioning behavior:

- future expedited-surcharge policy changes should insert a new `rule_catalogue` version row and a new `expedited_surcharge_rules` row
- superseded rows remain preserved for historical lookup

## Retrieval Surfaces

### `public.current_expedited_surcharge_rules`

Application-facing current-state view for active expedited-surcharge rules effective on the database server's current date.

### `api.get_expedited_surcharge_rule(...)`

Lookup function that accepts:

- optional `confirmation_date`
- optional `event_date`
- optional `as_of_date`

Behavior:

- uses `private.calculate_calendar_lead_time_days(start_date, end_date)` to derive whole calendar lead time
- returns the effective expedited-surcharge rule row together with derived `lead_time_days`, `applies`, and `applicability_status`
- returns `applicability_status = applies` for `0-14` days
- returns `applicability_status = does_not_apply` for `15+` days
- returns `applicability_status = insufficient_information` when either date input is missing
- raises a controlled validation error when `confirmation_date > event_date`
- preserves the stored policy semantics and does not calculate a live surcharge total

## Implemented Typed Rule Table

### `public.cancellation_rules`

| Column | PostgreSQL type | Null? | Default | Constraint/FK | Purpose |
| ------ | --------------- | ----- | ------- | ------------- | ------- |
| `rule_id` | `bigint` | no | none | PK, FK to `rule_catalogue` | governance parent |
| `cancellation_scenario` | `text` | no | none | scenario check | controlled scenario such as client cancellation, WNC cancellation without client breach, or client-breach termination |
| `cost_category` | `text` | no | none | category check | category-specific consequence such as rental payments, booking fee, committed costs, or security deposit |
| `lead_time_min_days` | `integer` | yes | none | conditional check | inclusive lower calendar lead-time bound where timing matters |
| `lead_time_max_days` | `integer` | yes | none | conditional check | inclusive upper calendar lead-time bound where timing matters |
| `treatment` | `text` | no | none | treatment check | canonical outcome such as `refundable`, `non_refundable`, or `refunded_in_full` |
| `requires_manual_review` | `boolean` | no | `false` | treatment-alignment check | flags outcomes that remain fact-dependent, such as non-recoverable-cost deductions or valid deduction checks |
| `created_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |
| `updated_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |

Primary key:

- `rule_id`

Indexes and constraints:

- primary key also enforces one typed cancellation row per governed rule version
- scenario, category, treatment, and lead-time checks reject unsupported policy values and impossible lead-time windows
- `requires_manual_review = true` is reserved for outcomes that still depend on live committed-cost recovery or valid deduction facts
- trigger-enforced parent-domain validation: the parent `rule_catalogue` row must be `rule_domain = 'cancellation'` and `rule_kind = 'hard_rule'`
- trigger-enforced overlap protection rejects ambiguous rows within the same cancellation scenario, cost category, and effective-date window while still allowing multiple category-specific consequences for one cancellation scenario

Delete behavior:

- `rule_id` uses `ON DELETE CASCADE`

Mutability:

- business-rule value changes should create a new governed rule version instead of editing an existing row in place
- technical corrections to draft rows are allowed before activation

Versioning behavior:

- future cancellation-policy changes should insert a new `rule_catalogue` version row and a new `cancellation_rules` row
- superseded rows remain preserved for historical lookup

## Retrieval Surfaces

### `public.current_cancellation_rules`

Application-facing current-state view for active cancellation rules effective on the database server's current date.

### `api.get_cancellation_rules(...)`

Lookup function that accepts:

- optional `cancellation_scenario`
- optional `cancellation_date`
- optional `event_date`
- optional `cost_category`
- optional `as_of_date`

Behavior:

- uses `private.calculate_calendar_lead_time_days(cancellation_date, event_date)` for the shared `31+` versus `0-30` day boundary semantics
- returns zero, one, or multiple rows because a single cancellation scenario may carry multiple category-specific contractual consequences
- preserves timing-independent consequences such as booking-fee non-refundability even when cancellation timing is unknown
- returns one `applicability_status = insufficient_information` row per timing-dependent cost category when `cancellation_date` or `event_date` is missing
- suppresses out-of-window timing-dependent rows instead of returning irrelevant category duplicates
- raises a controlled validation error when `cancellation_date > event_date`
- preserves structured policy outcomes and manual-review flags instead of calculating a live refund amount

## Implemented Typed Rule Table

### `public.capacity_rules`

| Column | PostgreSQL type | Null? | Default | Constraint/FK | Purpose |
| ------ | --------------- | ----- | ------- | ------------- | ------- |
| `rule_id` | `bigint` | no | none | PK, FK to `rule_catalogue` | governance parent |
| `venue_space_id` | `bigint` | yes | none | FK to `venue_spaces` | physical-space scope where applicable |
| `rental_type_id` | `bigint` | yes | none | FK to `rental_types` | whole-venue legal-capacity scope under the current canonical entity set |
| `configuration_type` | `text` | yes | none | configuration check | nullable because some rules are scope-wide or inherently non-numeric |
| `capacity_type` | `text` | no | none | type check | `legal_maximum`, `operational_layout`, `must_confirm`, or `not_event_capacity_space` |
| `max_guests` | `integer` | yes | none | conditional check | numeric approved maximum where one exists |
| `requires_confirmation` | `boolean` | no | `false` | conditional check | explicit confirmation-only support for no-fixed-capacity cases |
| `conditions_summary` | `text` | yes | none | none | compact source-backed operating note |
| `created_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |
| `updated_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |

Primary key:

- `rule_id`

Indexes and constraints:

- primary key also enforces one typed capacity row per governed rule version
- exactly one scope reference must be present: either `venue_space_id` or `rental_type_id`
- `configuration_type` currently uses the explicit canonical values `lying_down`, `movement`, `seated`, and `standing`
- `capacity_type` and `max_guests` checks prevent fake numeric values for `must_confirm` or `not_event_capacity_space`
- trigger-enforced parent-domain validation: the parent `rule_catalogue` row must be `rule_domain = 'capacity'` and `rule_kind = 'hard_rule'`
- trigger-enforced overlap protection rejects ambiguous active or historical rules for the same exact scope and configuration

Delete behavior:

- `rule_id` uses `ON DELETE CASCADE`
- scope FKs use `ON DELETE RESTRICT`

Mutability:

- business-rule value changes should create a new governed rule version instead of editing an existing row in place
- technical corrections to draft rows are allowed before activation

Versioning behavior:

- future capacity-policy changes should insert a new `rule_catalogue` version row and a new `capacity_rules` row
- superseded rows remain preserved for historical lookup

## Retrieval Surfaces

### `public.current_capacity_rules`

Application-facing current-state view for active capacity rules effective on the database server's current date.

### `api.get_capacity_rule(...)`

Exact rule lookup function that accepts:

- optional `space_code`
- optional `rental_type_code`
- optional `configuration_type`
- optional `as_of_date`

Behavior:

- returns zero or one actual rule row
- rejects calls that supply both `space_code` and `rental_type_code`
- uses exact configuration matching for configuration-dependent capacities
- does not guess a capacity when a scope has configuration-specific rules but `configuration_type` is missing
- can still return generic scope-level rows such as the whole-venue legal maximum, `must_confirm`, or `not_event_capacity_space`

### `api.evaluate_capacity(...)`

Higher-level evaluation function that accepts:

- optional `space_code`
- optional `rental_type_code`
- optional `configuration_type`
- optional `guest_count`
- optional `as_of_date`

Behavior:

- returns one structured result row
- rejects negative guest counts
- resolves matched numeric rules to `within_capacity` or `exceeds_capacity`
- treats numeric maxima as inclusive
- returns `insufficient_information` when the scope is known but required configuration is missing
- returns `requires_confirmation` when the approved rule explicitly has no fixed published capacity
- returns `not_event_capacity_space` when the queried scope must not be counted toward guest capacity
- returns `no_applicable_rule` when no approved current rule matches the supplied scope/configuration

## Implemented Typed Rule Table

### `public.space_access_rules`

| Column | PostgreSQL type | Null? | Default | Constraint/FK | Purpose |
| ------ | --------------- | ----- | ------- | ------------- | ------- |
| `rule_id` | `bigint` | no | none | PK, FK to `rule_catalogue` | governance parent |
| `rental_type_id` | `bigint` | no | none | FK to `rental_types` | rental scope for the access rule |
| `venue_space_id` | `bigint` | no | none | FK to `venue_spaces` | canonical space governed by the rule |
| `access_status` | `text` | no | none | status check | stored outcome: `included`, `shared`, or `restricted` |
| `access_mode` | `text` | no | none | mode check | approved use mode such as exclusive, setup-constrained, shared, circulation-only, or WNC-controlled |
| `space_function` | `text` | no | none | function check | `core_event_space`, `flex_space`, `support_space`, or `circulation_and_facilities` |
| `included_by_default` | `boolean` | no | `false` | none | whether the approved source set treats the space as part of the standard scope absent special variation |
| `requires_preparation` | `boolean` | no | `false` | none | whether setup, clearing, or advance preparation is required before promise |
| `requires_confirmation` | `boolean` | no | `false` | none | whether the exact usable scope must be confirmed before promise |
| `conditions_summary` | `text` | yes | none | non-empty-when-present check | compact operating note preserving source-backed nuance |
| `created_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |
| `updated_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |

Primary key:

- `rule_id`

Indexes and constraints:

- primary key also enforces one typed space-access row per governed rule version
- `access_status`, `access_mode`, and `space_function` are text vocabularies constrained by `CHECK`
- trigger-enforced parent-domain validation: the parent `rule_catalogue` row must be `rule_domain = 'space_access'` and `rule_kind` must be either `hard_rule` or `conditional_rule`
- trigger-enforced overlap protection rejects ambiguous active or historical rules for the same exact `rental_type_id` plus `venue_space_id` applicability window

Delete behavior:

- `rule_id` uses `ON DELETE CASCADE`
- scope FKs use `ON DELETE RESTRICT`

Mutability:

- business-rule value changes should create a new governed rule version instead of editing an existing row in place
- technical corrections to draft rows are allowed before activation

Versioning behavior:

- future space-access policy changes should insert a new `rule_catalogue` version row and a new `space_access_rules` row
- superseded rows remain preserved for historical lookup

## Retrieval Surfaces

### `public.current_space_access_rules`

Application-facing current-state view for active space-access rules effective on the database server's current date.

### `api.get_space_access_rule(...)`

Exact rule lookup function that accepts:

- `rental_type_code`
- `space_code`
- optional `as_of_date`

Behavior:

- returns zero or one actual rule row
- requires both `rental_type_code` and `space_code` because access is scope-dependent
- returns no row when inputs are missing or the combination is not seeded
- raises an exception if bad data would create more than one matching rule

### `api.evaluate_space_access(...)`

Higher-level evaluation surface that accepts:

- optional `rental_type_code`
- optional `space_code`
- optional `as_of_date`

Behavior:

- returns one structured result row
- returns `insufficient_information` when required input is missing
- returns `no_applicable_rule` for unsupported or unseeded combinations such as the current unresolved `custom_scope` room matrix
- upgrades any included row whose stored `requires_confirmation = true` to `requires_confirmation`
- upgrades circulation-only included rows such as `hallway_bathrooms` to `included_for_access`
- leaves explicit `shared` and `restricted` outcomes unchanged

## Implemented Typed Rule Table

### `public.operational_requirements`

| Column | PostgreSQL type | Null? | Default | Constraint/FK | Purpose |
| ------ | --------------- | ----- | ------- | ------------- | ------- |
| `rule_id` | `bigint` | no | none | PK, FK to `rule_catalogue` | governance parent |
| `rental_type_id` | `bigint` | yes | none | FK to `rental_types` | optional rental-scope limiter |
| `venue_space_id` | `bigint` | yes | none | FK to `venue_spaces` | optional space-scope limiter |
| `requirement_type` | `text` | no | none | requirement-type check | stable operational-rule family such as `grace_period`, `supplier_access`, or `installation` |
| `context_code` | `text` | yes | none | context check | scoped qualifier such as `arrival_departure_only` or `plaster_wall_fixings` |
| `outcome` | `text` | no | none | outcome check | fixed policy consequence such as `required`, `prohibited`, `conditional`, or `client_responsibility` |
| `timing_minutes` | `integer` | yes | none | check `> 0` when present | explicit grace-period or timing amount where the source defines one |
| `timing_reference` | `text` | yes | none | timing-reference check | boundary such as `booked_start_time` or `approved_access_times_only` |
| `timing_purpose` | `text` | yes | none | purpose check | semantic limiter such as `arrival_departure_only` |
| `multi_day_scope` | `text` | no | `'any'` | scope check | whether the rule applies to any rental, only single-day, or only multi-day contexts |
| `responsible_party` | `text` | yes | none | responsibility check | `client`, `wnc`, or `shared` where responsibility is part of the rule |
| `requires_confirmation` | `boolean` | no | `false` | semantic check | whether explicit approval or scope confirmation is required |
| `requires_preparation` | `boolean` | no | `false` | semantic check | whether advance preparation or clearing is required |
| `manual_review_required` | `boolean` | no | `false` | semantic check | whether the rule must stay human-reviewed instead of auto-resolved |
| `conditions_summary` | `text` | yes | none | non-empty-when-present check | compact source-backed nuance |
| `created_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |
| `updated_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |

Primary key:

- `rule_id`

Indexes and constraints:

- primary key also enforces one typed operational row per governed rule version
- `requirement_type`, `context_code`, `outcome`, `timing_reference`, `timing_purpose`, `multi_day_scope`, and `responsible_party` are text vocabularies constrained by `CHECK`
- semantic checks ensure that responsibility outcomes align with `responsible_party`, timing purpose cannot exist without a timing value, and special flag-driven outcomes remain internally consistent
- trigger-enforced parent-domain validation: the parent `rule_catalogue` row must be `rule_domain = 'operational_requirement'` and `rule_kind` must be either `hard_rule` or `conditional_rule`
- trigger-enforced overlap protection rejects ambiguous active or historical rules for the same exact `rental_type_id`, `venue_space_id`, `requirement_type`, `context_code`, `multi_day_scope`, and overlapping effective-date window

Delete behavior:

- `rule_id` uses `ON DELETE CASCADE`
- scope FKs use `ON DELETE RESTRICT`

Mutability:

- business-rule value changes should create a new governed rule version instead of editing an existing row in place
- technical corrections to draft rows are allowed before activation

Versioning behavior:

- future operational-policy changes should insert a new `rule_catalogue` version row and a new `operational_requirements` row
- superseded rows remain preserved for historical lookup

## Retrieval Surfaces

### `public.current_operational_requirements`

Application-facing current-state view for active operational rules effective on the database server's current date.

### `api.get_operational_requirements(...)`

Operational rule retrieval function that accepts:

- optional `rental_type_code`
- optional `requirement_type`
- optional `space_code`
- optional `multi_day`
- optional `context_code`
- optional `as_of_date`

Behavior:

- returns zero, one, or many actual rule rows because multiple operational requirements can apply at the same time
- matches global rows together with scope-specific rows when the supplied context allows both
- returns `insufficient_information` when a relevant rule exists but required scope facts such as `rental_type_code`, `space_code`, or `multi_day` are missing
- returns `no_applicable_rule` when no approved rule matches the supplied context
- keeps manual-review and preparation semantics explicit instead of flattening them into a boolean allow or deny

## Implemented Typed Rule Table

### `public.catering_supplier_rules`

| Column | PostgreSQL type | Null? | Default | Constraint/FK | Purpose |
| ------ | --------------- | ----- | ------- | ------------- | ------- |
| `rule_id` | `bigint` | no | none | PK, FK to `rule_catalogue` | governance parent |
| `catering_arrangement` | `text` | yes | none | arrangement check | optional arrangement scope such as `external_caterer`, `wnc_catering_partner`, or `tap_water` |
| `rule_type` | `text` | no | none | rule-type check | stable category such as `arrangement_policy`, `kitchen_use`, `supplier_requirement`, `equipment_use`, or `vat_classification` |
| `context_code` | `text` | yes | none | context check | scoped qualifier such as `large_scale_food_production`, `storage_needs_confirmation`, or `mixed_catering_split` |
| `outcome` | `text` | no | none | outcome check | fixed policy consequence such as `allowed`, `conditional`, `requires_confirmation`, or `wnc_partner_available` |
| `external_supplier_required` | `boolean` | no | `false` | none | whether the arrangement depends on a non-WNC supplier path |
| `included_by_default` | `boolean` | no | `false` | none | whether the arrangement is included without a separate catering decision |
| `wnc_coordination_available` | `boolean` | no | `false` | semantic check | whether WNC may coordinate the supplier or arrangement if separately agreed |
| `wnc_coordination_included` | `boolean` | no | `false` | semantic check | whether WNC coordination is included by default |
| `kitchen_use_scope` | `text` | no | `'any'` | scope check | whether the rule applies generally or only when kitchen use is requested |
| `kitchen_use_status` | `text` | yes | none | kitchen-status check | kitchen or equipment boundary such as `limited_support_only`, `agreed_use_only`, or `requires_confirmation` |
| `vat_category` | `text` | yes | none | VAT-category check | catering-specific VAT classification family |
| `vat_rate` | `numeric(5,4)` | yes | none | check `>= 0` and `<= 1` | stored VAT rate where one deterministic rate applies |
| `requires_split_lines` | `boolean` | no | `false` | semantic check | whether mixed catering must be split across multiple line items |
| `requires_confirmation` | `boolean` | no | `false` | semantic check | whether explicit confirmation is required before promise |
| `manual_review_required` | `boolean` | no | `false` | semantic check | whether the rule must remain human-reviewed instead of auto-resolved |
| `conditions_summary` | `text` | yes | none | non-empty-when-present check | compact source-backed nuance |
| `created_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |
| `updated_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |

Primary key:

- `rule_id`

Indexes and constraints:

- primary key also enforces one typed catering-supplier row per governed rule version
- arrangement, rule-type, context, kitchen-scope, and VAT vocabularies are constrained by `CHECK`
- semantic checks keep coordination flags, partner-only outcomes, mixed-catering split behavior, and VAT-only fields internally consistent
- trigger-enforced parent-domain validation: the parent `rule_catalogue` row must be `rule_domain = 'catering_supplier'` and `rule_kind` must be either `hard_rule` or `conditional_rule`
- trigger-enforced overlap protection rejects ambiguous active or historical rules for the same exact `catering_arrangement`, `rule_type`, `context_code`, `vat_category`, `kitchen_use_scope`, and overlapping effective-date window

Delete behavior:

- `rule_id` uses `ON DELETE CASCADE`

Mutability:

- business-rule value changes should create a new governed rule version instead of editing an existing row in place
- technical corrections to draft rows are allowed before activation

Versioning behavior:

- future catering-policy changes should insert a new `rule_catalogue` version row and a new `catering_supplier_rules` row
- superseded rows remain preserved for historical lookup

## Retrieval Surfaces

### `public.current_catering_supplier_rules`

Application-facing current-state view for active catering-supplier rules effective on the database server's current date.

### `api.get_catering_supplier_rules(...)`

Catering-supplier retrieval function that accepts:

- optional `catering_arrangement`
- optional `rule_type`
- optional `context_code`
- optional `vat_category`
- optional `kitchen_use_requested`
- optional `as_of_date`

Behavior:

- returns zero, one, or many actual rule rows because arrangement, kitchen, supplier-requirement, and VAT rules may all apply together
- combines arrangement-specific rows with global rows where the supplied context allows both
- returns `insufficient_information` when the relevant rule family depends on missing `catering_arrangement`, `vat_category`, or `kitchen_use_requested`
- returns `no_applicable_rule` for unseeded arrangements such as the current unresolved generic `custom` path
- keeps WNC coordination, external-supplier requirement, kitchen limits, and VAT-split semantics explicit instead of collapsing them into one approval boolean

## Evaluated Typed Rule Tables For The Next Slices

These tables are still supported by the source set, but intentionally not migrated yet.

### `public.vat_rules` (evaluated, not migrated)

| Column | PostgreSQL type | Null? | Default | Constraint/FK | Purpose |
| ------ | --------------- | ----- | ------- | ------------- | ------- |
| `rule_id` | `bigint` | no | none | PK, FK to `rule_catalogue` | governance parent |
| `line_item_category` | `text` | no | none | non-empty | venue rental, booking fee, food products, etc. |
| `vat_rate` | `numeric(5,4)` | yes | none | check `>= 0` | VAT rate when single-rate |
| `requires_split_lines` | `boolean` | no | `false` | none | mixed-catering split handling |
| `split_rule_note` | `text` | yes | none | none | service versus product split note |

## Delete Behavior Summary

- canonical entity tables should generally use `ON DELETE RESTRICT`
- provenance rows may cascade from the parent rule
- superseded rules must not be deletable if another rule references them

## Timestamp Strategy

- all implemented tables use UTC `created_at`
- mutable tables also track `updated_at`

## Why Not JSONB For Core Rules

Core fee, payment, VAT, and capacity rules need:

- direct filtering
- range checks
- deterministic tests
- safe uniqueness constraints
- future RPC and view support

JSONB remains acceptable only for irregular support metadata that is genuinely not relational.

## Implemented Reference-Data Table

### `public.technical_equipment_inventory`

| Column | PostgreSQL type | Null? | Default | Constraint/FK | Purpose |
| ------ | --------------- | ----- | ------- | ------------- | ------- |
| `id` | `bigint` | no | identity | PK | surrogate key |
| `equipment_code` | `text` | no | none | unique, non-empty | stable machine value such as `yoga_mats` or `basic_projector` |
| `source_item_code` | `text` | no | none | unique, non-empty | preserved source row identifier such as `EQ-001` |
| `equipment_category` | `text` | no | none | category check | controlled family such as `wellness_equipment`, `projection`, or `sound` |
| `equipment_name` | `text` | no | none | non-empty | human-readable item name |
| `quantity_numeric` | `integer` | yes | none | check `> 0` when present | numeric count where the source gives one |
| `quantity_display` | `text` | no | none | non-empty | preserved display quantity such as `Variable` or `Installed throughout venue` |
| `primary_location` | `text` | no | none | non-empty | location summary from the source |
| `availability_status` | `text` | no | none | status check | inventory-facing status such as `standard`, `available_on_request`, or `must_confirm` |
| `normally_included` | `boolean` | no | `true` | none | whether the item is normally part of rental scope |
| `exact_count_guaranteed` | `boolean` | no | `false` | none | whether the source allows the item count to be treated as guaranteed |
| `source_id` | `bigint` | no | none | FK to `source_registry` | traceability to the authoritative inventory source |
| `source_locator` | `text` | no | none | non-empty | row or section locator inside the source |
| `conditions_summary` | `text` | yes | none | non-empty-when-present check | source-backed quantity or preparation nuance |
| `created_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |
| `updated_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |

Primary key:

- `id`

Indexes and constraints:

- unique `equipment_code`
- unique `source_item_code`
- category and availability vocabularies constrained by `CHECK`
- quantity must be positive when present
- required text fields cannot be empty

Delete behavior:

- `source_id` uses `ON DELETE RESTRICT`

Mutability:

- this table stores current authoritative inventory facts rather than governed policy versions
- updates should remain source-traceable and migration-driven, but they do not require `rule_catalogue` versioning

Why this is not a typed rule table:

- the current source rows are inventory facts, not governed business-policy statements
- the Phase 4 goal is current authoritative stock facts, not historical inventory-state replay
- requirement support still belongs in a separate governed rule table because possession does not equal feasibility

## Implemented Typed Rule Table

### `public.technical_capability_rules`

| Column | PostgreSQL type | Null? | Default | Constraint/FK | Purpose |
| ------ | --------------- | ----- | ------- | ------------- | ------- |
| `rule_id` | `bigint` | no | none | PK, FK to `rule_catalogue` | governance parent |
| `rule_type` | `text` | no | none | rule-type check | whether the row describes direct capability availability or evaluated requirement support |
| `technical_area` | `text` | no | none | area check | stable area such as `projection`, `sound`, `lighting`, or `power` |
| `capability_code` | `text` | yes | none | capability-code check | direct capability identifier for `capability_availability` rows |
| `requirement_code` | `text` | yes | none | requirement-code check | evaluated technical requirement identifier for `requirement_support` rows |
| `equipment_inventory_id` | `bigint` | yes | none | FK to `technical_equipment_inventory` | optional link to the physical inventory row that supports the capability |
| `support_status` | `text` | no | none | support-status check | structured consequence such as `standard`, `available_on_request`, `external_supplier_required`, `supported`, `not_available`, or `requires_confirmation` |
| `included_in_base_rental` | `boolean` | no | `false` | none | whether the capability is part of the base venue scope |
| `internal_equipment_exists` | `boolean` | no | `false` | semantic check | whether relevant WNC equipment exists at all |
| `internal_support_sufficient` | `boolean` | no | `false` | semantic check | whether WNC's own setup is sufficient for the capability or requirement |
| `client_may_self_organise` | `boolean` | no | `false` | none | whether the client may bring or arrange its own solution |
| `wnc_can_coordinate` | `boolean` | no | `false` | semantic check | whether WNC may coordinate an external technical solution if agreed |
| `coordination_fee_possible` | `boolean` | no | `false` | semantic check | whether a coordination or production fee may apply |
| `requires_confirmation` | `boolean` | no | `false` | semantic check | whether explicit confirmation is required before promise |
| `manual_review_required` | `boolean` | no | `false` | semantic check | whether the rule must remain human-reviewed |
| `conditions_summary` | `text` | yes | none | non-empty-when-present check | compact source-backed nuance |
| `created_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |
| `updated_at` | `timestamptz` | no | `timezone('utc', now())` | none | audit timestamp |

Primary key:

- `rule_id`

Indexes and constraints:

- one governed technical-capability row per rule version
- rule-type, technical-area, capability-code, requirement-code, and support-status vocabularies constrained by `CHECK`
- semantic checks enforce the split between `capability_availability` and `requirement_support`
- semantic checks ensure `supported` implies internal sufficiency, `not_available` implies no internal equipment or sufficiency, `requires_confirmation` and `must_confirm` semantics turn on the confirmation flag, and coordination fee flags cannot exist without coordination capability
- trigger-enforced parent-domain validation: the parent `rule_catalogue` row must be `rule_domain = 'technical_capability'` and `rule_kind` must be either `hard_rule` or `conditional_rule`
- trigger-enforced overlap protection rejects ambiguous active or historical rows for the same exact `rule_type`, `technical_area`, `capability_code`, `requirement_code`, and overlapping effective-date window

Delete behavior:

- `rule_id` uses `ON DELETE CASCADE`
- `equipment_inventory_id` uses `ON DELETE RESTRICT`

Mutability:

- business-rule value changes should create a new governed rule version instead of editing an existing row in place
- technical corrections to draft rows are allowed before activation

Versioning behavior:

- future technical-support policy changes should insert a new `rule_catalogue` version row and a new `technical_capability_rules` row
- superseded rows remain preserved for historical lookup

## Retrieval Surfaces

### `public.current_technical_equipment_inventory`

Application-facing current-state view for inventory rows with joined source metadata.

### `api.get_technical_equipment_inventory(...)`

Inventory retrieval function that accepts optional:

- `equipment_code`
- `equipment_category`

Behavior:

- returns current authoritative inventory facts only
- does not evaluate support or feasibility
- allows item lookup without pretending quantity equals capacity or technical support

### `api.evaluate_technical_equipment_quantity(...)`

Quantity-evaluation function that accepts:

- required `equipment_code`
- required positive `requested_quantity`

Behavior:

- returns `quantity_available` only when a numeric standard quantity exists and the count is guaranteed
- returns `insufficient_quantity` when the requested quantity exceeds a numeric standard quantity
- returns `requires_confirmation` when the item count is not guaranteed or the source presents the count as variable or confirmation-sensitive
- returns `no_applicable_equipment` when the item code is unknown
- evaluates quantity only and does not decide event feasibility or capacity

### `public.current_technical_capability_rules`

Application-facing current-state view for active technical support and capability rules effective on the database server's current date.

### `api.get_technical_capability(...)`

Technical capability retrieval function that accepts optional:

- `rule_type`
- `capability_code`
- `requirement_code`
- `technical_area`
- `as_of_date`

Behavior:

- returns actual rule rows when they match
- keeps direct capability availability separate from evaluated requirement support
- returns `insufficient_information` when the relevant lookup family is missing its key capability or requirement input
- returns `no_applicable_rule` when the requested capability or requirement is unseeded

### `api.evaluate_technical_requirement(...)`

Requirement-oriented wrapper over `api.get_technical_capability(...)` for `requirement_support` rows.

Behavior:

- evaluates supported ordinary requirements such as `standard_wifi`
- evaluates internal-versus-external distinctions such as `ordinary_audio_playback` versus `amplified_event_sound`
- preserves explicit confirmation semantics for `basic_projection`, `high_load_power`, and `custom_technical_setup`

## Implemented Typed Rule Tables

### `public.service_rules`

| Column | PostgreSQL type | Null? | Default | Constraint/FK | Purpose |
| ------ | --------------- | ----- | ------- | ------------- | ------- |
| `rule_id` | `bigint` | no | none | PK, FK to `rule_catalogue` | governance parent |
| `service_level` | `text` | yes | none | service-level check | current canonical overall service level |
| `service_type` | `text` | yes | none | service-type check | current canonical individual service item |
| `availability_status` | `text` | no | none | availability-status check | `available`, `conditional`, or `manual_review_required` |
| `included_by_default` | `boolean` | no | `false` | none | whether the scope is part of the base/default offer |
| `requires_confirmation` | `boolean` | no | `false` | semantic check | whether the service still requires explicit confirmation |
| `requires_written_scope` | `boolean` | no | `false` | semantic check | whether scope must be written explicitly |
| `manual_quote_required` | `boolean` | no | `false` | semantic check | whether pricing stays manual rather than deterministic |
| `external_supplier_required` | `boolean` | no | `false` | none | whether the service inherently depends on external supply |
| `client_approval_required` | `boolean` | no | `false` | none | whether the service must be client-approved in scope |
| `wnc_coordination_required` | `boolean` | no | `false` | none | whether WNC coordination is structurally part of the service |
| `manual_review_required` | `boolean` | no | `false` | semantic check | whether the row must remain human-reviewed |
| `conditions_summary` | `text` | yes | none | non-empty-when-present check | compact source-backed nuance |

Design notes:

- exactly one of `service_level` or `service_type` must be present
- `production_coordination` remains a `service_type` in the current approved vocabulary, not a seeded `service_level`
- `additional_host` is intentionally not allowed in the current constraint because it is missing from the approved Data Dictionary `service_type` enum list
- active overlap protection is enforced per exact service scope and effective-date window

### `public.facilitator_requirement_rules`

| Column | PostgreSQL type | Null? | Default | Constraint/FK | Purpose |
| ------ | --------------- | ----- | ------- | ------------- | ------- |
| `rule_id` | `bigint` | no | none | PK, FK to `rule_catalogue` | governance parent |
| `facilitator_arrangement` | `text` | no | none | arrangement check | current canonical facilitator-arrangement value |
| `arrangement_status` | `text` | no | none | status check | `not_applicable`, `allowed`, `conditional`, or `manual_review_required` |
| `responsible_party` | `text` | yes | none | responsible-party check | `client`, `wnc`, or `shared` where authoritative |
| `client_commitment_requires_facilitator_confirmation` | `boolean` | no | `false` | semantic check | whether the arrangement may be committed only after facilitator confirmation |
| `requires_availability_confirmation` | `boolean` | no | `false` | semantic check | whether availability still must be confirmed |
| `requires_scope_confirmation` | `boolean` | no | `false` | semantic check | whether session scope still must be confirmed |
| `requires_technical_confirmation` | `boolean` | no | `false` | semantic check | whether technical or equipment needs still must be confirmed |
| `client_provided_allowed` | `boolean` | no | `false` | semantic check | whether the client-provided path is allowed |
| `wnc_coordination_available` | `boolean` | no | `false` | semantic check | whether WNC may coordinate the facilitator path |
| `wnc_coordination_required` | `boolean` | no | `false` | semantic check | whether WNC coordination is structurally part of the arrangement |
| `requires_confirmation` | `boolean` | no | `false` | semantic check | whether the arrangement remains confirmation-sensitive |
| `manual_review_required` | `boolean` | no | `false` | semantic check | whether the arrangement must remain human-reviewed |
| `conditions_summary` | `text` | yes | none | non-empty-when-present check | compact source-backed nuance |

Design notes:

- `none` is constrained to the `not_applicable` state with no confirmation flags turned on
- overlap protection is enforced per exact facilitator-arrangement value and effective-date window
- the typed slice stores confirmation semantics only; it does not store individual facilitator identity or live availability

## Retrieval Surfaces

### `public.current_service_rules`

Application-facing current-state view for active service-level and service-item rules with provenance arrays.

### `api.get_service_rules(...)`

Service retrieval function that accepts optional:

- `service_level`
- `service_type`
- `as_of_date`

Behavior:

- returns matching service-level rows, service-item rows, or both when both scoped inputs are provided
- returns `insufficient_information` when neither service key is provided
- returns `no_applicable_rule` when the requested service value is unknown or unseeded

### `public.current_facilitator_requirement_rules`

Application-facing current-state view for active facilitator-arrangement rules with provenance arrays.

### `api.get_facilitator_requirements(...)`

Facilitator-arrangement retrieval function that accepts:

- `facilitator_arrangement`
- `as_of_date`

Behavior:

- returns the current structured arrangement rule when seeded
- preserves `not_applicable` for `none`
- returns `insufficient_information` for missing arrangement input
- returns `no_applicable_rule` for unknown arrangement values
