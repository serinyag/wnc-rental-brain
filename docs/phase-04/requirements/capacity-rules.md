# Capacity Rules

## Purpose

The capacity-rule slice answers:

> Given a known scope and event configuration, what approved WNC capacity rule applies?

Where a guest count is supplied, it also answers:

> Is that guest count within the matched approved capacity rule?

This slice stores static policy only. It does not choose layouts, design room flow, or grant live operational approval.

## Authoritative Source Basis

Primary controlled source for this slice:

- `WNC Venue Technical & Equipment Inventory`

Supporting current sources:

- `WNC Venue Rental Operations Manual.docx`
- `WNC Rental Agreement Template.docx`

Source review outcome:

- the technical inventory contains the authoritative `WNC Capacity & Space Use Rules` rows `CAP-001` through `CAP-010`
- the operations manual repeats the whole-venue legal maximum and the published Studio and Retail maxima, while warning that approved event capacity may still be lower depending on layout and safety conditions
- the agreement template repeats the whole-venue legal maximum and the rule that approved event capacity depends on the agreed guest number, activity, room setup, and safety requirements
- the current approved source set supports:
  - whole-venue legal maximum
  - Studio layout-specific capacities
  - Retail Area standing capacity
  - 1:1 / Podcast Room as `must_confirm`
  - controlled operational spaces that must not be counted toward guest capacity
- the current approved source set does not provide a standalone published capacity for the Conversation Pit, which remains folded into the Retail Area capacity note

## Business Questions

This domain should answer:

- what capacity rule applies to this scope and configuration
- what the approved maximum guest count is where a numeric maximum exists
- whether a supplied guest count is within that matched rule
- whether more information is required before capacity can be determined safely
- whether the situation requires manual confirmation instead of a published guest number
- whether the queried scope is not an event-capacity space at all

## Inputs

Only approved inputs are required:

- optional `space_code`
- optional `rental_type_code`
- optional `configuration_type`
- optional `guest_count`
- optional `as_of_date` for historical lookup

Input rules:

- exactly one of `space_code` or `rental_type_code` should be supplied
- `space_code` is used for physical-space rules such as Studio or Retail
- `rental_type_code = entire_venue` is used for the current whole-venue legal-capacity rule because the existing canonical entity set has an approved rental-type code for `entire_venue` but no separate canonical `whole_venue` space row
- `configuration_type` is required only where the approved capacity varies by configuration

## Canonical Vocabulary

Current approved or newly introduced machine values for this slice:

### `configuration_type`

- `lying_down`
- `movement`
- `seated`
- `standing`

These are used only where the authoritative source distinguishes a configuration-specific event capacity.

### `capacity_type`

- `legal_maximum`
- `operational_layout`
- `must_confirm`
- `not_event_capacity_space`

Meaning:

- `legal_maximum`: hard legal ceiling for the scoped venue context
- `operational_layout`: approved maximum for a specific event layout or activity
- `must_confirm`: no fixed published capacity exists; an approved guest number requires explicit confirmation
- `not_event_capacity_space`: the scope is operational or circulation space and must not be counted toward guest capacity

## Outputs

The implemented retrieval and evaluation surfaces expose:

- `max_guests`
- `capacity_type`
- `requires_confirmation`
- `conditions_summary`
- `applicability_status`
- `capacity_evaluation_status`
- `within_capacity`

`applicability_status` values:

- `applies`
- `insufficient_information`
- `requires_confirmation`
- `not_event_capacity_space`
- `no_applicable_rule`

`capacity_evaluation_status` values:

- `not_evaluated`
- `within_capacity`
- `exceeds_capacity`
- `insufficient_information`
- `requires_confirmation`
- `not_event_capacity_space`
- `no_applicable_rule`

`within_capacity` is:

- `true` when a numeric rule applies and the supplied guest count does not exceed the approved maximum
- `false` when a numeric rule applies and the supplied guest count exceeds the approved maximum
- `null` when no numeric evaluation is possible

## Boundary Semantics

Numeric maximums are inclusive.

Examples:

- `19` against Studio `movement = 20` -> `within_capacity`
- `20` against Studio `movement = 20` -> `within_capacity`
- `21` against Studio `movement = 20` -> `exceeds_capacity`

Guest-count validation:

- negative values are rejected
- `0` is treated as syntactically valid and evaluates `within_capacity` for any matched numeric rule because it does not exceed the approved maximum

## Missing-Information Semantics

- known scope plus exact approved configuration -> return the matched rule
- known scope plus missing required configuration -> `insufficient_information`
- known scope plus unknown configuration value -> `no_applicable_rule`
- unknown scope -> `no_applicable_rule`
- scope with no fixed published capacity but an approved confirmation-only rule -> `requires_confirmation`
- scope that is not an event-capacity space -> `not_event_capacity_space`

## Legal Maximum Versus Layout Maximum

This slice keeps the whole-venue legal maximum separate from layout-specific operational capacities.

Current rule hierarchy:

- `entire_venue` legal maximum: `110`
- Studio layout capacities: `25`, `20`, `40`, `40`
- Retail Area standing capacity: `60`

Important boundary:

- a legal maximum is not interchangeable with a layout-specific operational maximum
- for example, the whole-venue `110` ceiling must not be substituted for a Studio query whose required layout is still unknown

## Non-goals

Capacity rules do not decide or store:

- the best layout for the client
- room-design recommendations
- circulation planning
- production-footprint analysis
- live safe-capacity estimation
- interpretation of ambiguous event descriptions
- operational approval overrides
- full space-compatibility logic

## Query Contract

### `api.get_capacity_rule(...)`

- exact rule lookup only
- returns zero or one actual rule row
- does not guess when a scope has configuration-specific rules but `configuration_type` is missing
- returns generic non-configuration rules such as the whole-venue legal maximum, `must_confirm`, or `not_event_capacity_space` rows when those are the exact approved match

### `api.evaluate_capacity(...)`

- higher-level evaluation surface
- returns one structured result row
- can resolve:
  - matched numeric rule
  - `insufficient_information`
  - `requires_confirmation`
  - `not_event_capacity_space`
  - `no_applicable_rule`
- compares `guest_count` against static approved capacity only; it does not persist live rental state

## Example Queries

- `space_code = studio_space`, `configuration_type = movement` -> `max_guests = 20`
- `space_code = studio_space`, `configuration_type = movement`, `guest_count = 12` -> `within_capacity`
- `space_code = studio_space`, `configuration_type = movement`, `guest_count = 30` -> `exceeds_capacity`
- `space_code = studio_space`, `guest_count = 35`, missing `configuration_type` -> `insufficient_information`
- `rental_type_code = entire_venue`, `guest_count = 110` -> within the legal maximum rule
- `space_code = one_to_one_room` -> `requires_confirmation`
- `space_code = back_office` -> `not_event_capacity_space`
- `space_code = conversation_pit` -> `no_applicable_rule` for a standalone capacity lookup in the current slice

## Acceptance Criteria

1. Approved capacity policy is represented in a typed relational table linked to `rule_catalogue`.
2. Capacity remains configuration-aware and does not collapse a space into one generic number where the source set distinguishes layouts or activities.
3. Missing required configuration does not cause the system to guess a higher or lower capacity.
4. Whole-venue legal maximum and layout-specific operational maxima remain structurally distinct.
5. Guest-count evaluation is inclusive of the approved maximum.
6. Negative guest counts are rejected.
7. `must_confirm` and `not_event_capacity_space` outcomes remain explicit rather than being flattened into fake numeric capacities.
8. Active capacity rules have provenance through `rule_source_links`.
9. Historical capacity rule versions remain queryable by `as_of_date` while the current view excludes superseded versions.
10. `db reset` and the complete database test suite pass from Git-controlled files only.
