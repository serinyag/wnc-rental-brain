# Space Compatibility And Access Rules

## Purpose

This slice answers:

> Given a known rental type and a known venue space, what approved WNC access rule applies?

It also preserves the closely related operational question:

> Is the space included, shared, restricted, or only available with preparation?

This slice does not attempt to build a speculative all-spaces compatibility matrix.

## Authoritative Source Basis

Primary controlled sources for this slice:

- `WNC Venue Technical & Equipment Inventory`
- `WNC Venue Rental Operations Manual.docx`

Supporting current sources:

- `Studio Space _ Terms and Conditions.docx`
- `Full Venue _ Rental Terms and Conditions.docx`
- `WNC Rental Agreement Template.docx`

Source review outcome:

- the technical inventory contains explicit `ACC-001` through `ACC-009` room-access rows for standard Studio and Entire Venue access patterns
- the operations manual confirms the distinction between core event areas, flex or custom-scope space, support rooms, and shared circulation areas
- the Studio terms confirm that Retail Area operations remain live during Studio rentals
- the Full Venue terms confirm that the Storage Room is not guest-facing space and must remain accessible to WNC staff
- the agreement template confirms that hallway and bathroom access stays included while the hallway remains shared, and that 1:1 / Podcast Room, Back Office, and Storage Room scope must be recorded explicitly when used
- the approved source set supports deterministic Studio and Entire Venue access rules
- the approved source set does not yet support a room-by-room default matrix for `custom_scope`, so that path remains blocked rather than guessed

## Business Questions

This domain should answer:

- is this space included for this rental type
- is it shared rather than private
- is it restricted by default
- does it require preparation before it can be promised or used practically
- is it circulation or support space rather than ordinary private event space
- is there no approved rule for this combination yet
- is the input incomplete, so the system must not guess

## Inputs

Only approved inputs are required:

- `rental_type_code`
- `space_code`
- optional `as_of_date` for historical lookup

This slice does not add speculative inputs such as guest count, staffing level, calendar availability, or client-specific approval records.

## Canonical Vocabulary

### `access_status`

- `included`
- `shared`
- `restricted`

These are the stored rule-row outcomes.

### `access_mode`

- `exclusive_to_client`
- `client_use_within_agreed_setup`
- `shared_with_wnc_operations`
- `shared_circulation_and_facilities`
- `wnc_operational_use`

These preserve whether the client has private use, setup-constrained use, shared use, circulation-only access, or no standard client use.

### `space_function`

- `core_event_space`
- `flex_space`
- `support_space`
- `circulation_and_facilities`

These preserve the approved role of the space so support or access areas do not behave like ordinary private event rooms.

## Outputs

The implemented retrieval and evaluation surfaces expose:

- `access_status`
- `access_mode`
- `space_function`
- `included_by_default`
- `requires_preparation`
- `requires_confirmation`
- `conditions_summary`
- `applicability_status`

`applicability_status` values in the current slice:

- `included`
- `shared`
- `restricted`
- `included_for_access`
- `insufficient_information`
- `no_applicable_rule`

## Included Versus Usable

This slice keeps these concepts separate:

- contractual inclusion or restriction
- shared versus exclusive use
- whether preparation is required
- whether preparation is required

Example:

- the 1:1 / Podcast Room is stored as included for standard Studio and Entire Venue rentals while still carrying preparation-sensitive setup notes about furniture and remaining WNC items

## Support-Space Semantics

This slice explicitly preserves that:

- `back_office` and `storage_room` are support spaces, not default guest-facing event rooms
- `hallway_bathrooms` are circulation and facilities, not private event space
- `conversation_pit` follows the `retail_area` access pattern because the approved sources treat it as part of the Retail Area rather than a separately rentable area

## Retail Operational Status

The current approved sources support a structural distinction:

- `studio_space` rental + `retail_area` or `conversation_pit` -> `shared`
- `entire_venue` rental + `retail_area` or `conversation_pit` -> `included`

This preserves the approved rule that retail operations may remain live during Studio rentals without implying that the client has private use of that area.

## 1:1 / Podcast Room Treatment

The current source set does not support a simple unconditional `included` result.

Implemented interpretation:

- standard Studio and Entire Venue rows are stored with `included_by_default = true`
- those same rows also carry `requires_preparation = true`
- evaluated retrieval therefore returns `included`

This preserves the final approved policy that the room is included by default in both standard rental types while still keeping the setup and furniture nuance explicit.

## Back Office And Storage Room Treatment

The current structure keeps both spaces as `restricted`, and that is intentional.

Meaning in this slice:

- `restricted` does not mean the space can never be used operationally
- it means the space is not ordinary client event space and must not be treated as automatically available for general client use
- `back_office` also preserves `requires_preparation = true`, which captures the approved rule that it can be made usable for rental purposes with preparation
- `storage_room` keeps `access_mode = wnc_operational_use` and `space_function = support_space`, which preserves that it remains the default internal operational storage location without turning it into normal client event space

## Compatibility Modeling Decision

This slice does not create `public.space_compatibility_rules`.

Reason:

- the approved source set strongly supports rental-type-to-space access rules
- it also supports some access-side dependency notes, such as the Retail Area not being rented exclusively without the Studio in the published Entire Venue structure
- it does not yet provide a stable, reusable pairwise matrix of `space_a` plus `space_b` coexistence rules that would justify a second typed table

Current architectural decision:

- store the deterministic access rules in `public.space_access_rules`
- preserve dependency and coexistence notes inside `conditions_summary` where the approved sources express them only as scope notes
- defer a separate compatibility table until the source set contains genuine pairwise rules

## Missing-Information Semantics

- missing `rental_type_code` -> `insufficient_information`
- missing `space_code` -> `insufficient_information`
- unknown `space_code` or unresolved combination -> `no_applicable_rule`
- `custom_scope` combinations currently remain `no_applicable_rule` because the approved room-by-room default matrix is not yet seeded

No universal default inclusion rule is applied.

## Non-goals

This slice does not decide or store:

- guest capacity
- layout approval
- live calendar availability
- rental conflicts between different clients
- staffing plans
- production planning
- delivery scheduling
- clearing pricing
- client-specific written approvals

## Query Contract

### `api.get_space_access_rule(...)`

Exact rule lookup function that accepts:

- `rental_type_code`
- `space_code`
- optional `as_of_date`

Behavior:

- returns zero or one actual rule row
- returns no row when inputs are missing or unsupported
- raises an exception if bad data would create more than one matching active or historical row

### `api.evaluate_space_access(...)`

Higher-level evaluation surface that accepts:

- optional `rental_type_code`
- optional `space_code`
- optional `as_of_date`

Behavior:

- returns one structured result row
- resolves missing-input states to `insufficient_information`
- resolves known but unseeded or unsupported combinations to `no_applicable_rule`
- upgrades circulation-only included rows such as `hallway_bathrooms` to `included_for_access`
- leaves explicit restrictions as `restricted`

## Example Queries

- `rental_type_code = studio_space`, `space_code = studio_space` -> `included`
- `rental_type_code = studio_space`, `space_code = retail_area` -> `shared`
- `rental_type_code = studio_space`, `space_code = one_to_one_room` -> `included`
- `rental_type_code = studio_space`, `space_code = hallway_bathrooms` -> `included_for_access`
- `rental_type_code = studio_space`, `space_code = back_office` -> `restricted`
- `rental_type_code = entire_venue`, `space_code = conversation_pit` -> `included`
- `rental_type_code = custom_scope`, `space_code = one_to_one_room` -> `no_applicable_rule`
- missing `rental_type_code` with a known space -> `insufficient_information`

## Acceptance Criteria

1. Approved standard-rental access policy is represented in a typed relational table linked to `rule_catalogue`.
2. Shared, restricted, support-space, and circulation semantics stay explicit instead of collapsing into one boolean `included`.
3. 1:1 / Podcast Room access preserves default inclusion together with setup and preparation nuance, without incorrectly downgrading the standard-rental outcome to `requires_confirmation`.
4. Missing information and unresolved custom-scope combinations do not become default permission.
5. No separate pairwise compatibility table is created unless the approved source set genuinely supports it.
6. Active access rules have provenance through `rule_source_links`.
7. Historical access rule versions remain queryable by `as_of_date` while the current view excludes superseded versions.
8. `db reset` and the complete database test suite pass from Git-controlled files only.
