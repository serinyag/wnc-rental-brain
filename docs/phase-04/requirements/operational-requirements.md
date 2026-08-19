# Operational Requirements

## Objective

Model the approved fixed WNC operating conditions for build-up, breakdown, access timing, venue clearing, storage, supplier handling, installation restrictions, waste, and reset responsibilities without turning the database into a live event-production planner.

## Business Questions

- When can setup begin?
- What grace period applies to the selected rental type?
- Which access-timing constraints apply before or outside the booked timeline?
- What supplier access and supplier-responsibility defaults apply?
- What must be cleared, prepared, or explicitly defined before an Entire Venue rental can operate?
- How do Back Office and Storage Room operational-use rules interact with the existing access model?
- Which installation methods are prohibited and which remain conditional?
- What waste-removal and reset responsibility applies by default?
- When must cleaning remain a manual operational review instead of a guessed rule?

## Inputs

The approved source set supports these query inputs for the current typed slice:

- `rental_type_code`
- `requirement_type`
- `space_code`
- `multi_day`
- `context_code`
- `as_of_date`

The domain does not yet take live event facts such as supplier count, catering style, staffing plan, or guest activity schedule as deterministic inputs.

## Structured Outputs

The implementation uses `outcome` plus explicit qualifier fields.

Current seeded `outcome` values:

- `required`
- `prohibited`
- `conditional`
- `requires_confirmation`
- `client_responsibility`
- `manual_review_required`

Qualifier fields:

- `requires_confirmation`
- `requires_preparation`
- `manual_review_required`
- `responsible_party`
- `timing_minutes`
- `timing_reference`
- `timing_purpose`

This keeps policy like "Back Office use is conditional and prepared" distinct from "professional cleaning remains manual review" instead of flattening both into one boolean.

## Approved Requirement Types

Current seeded requirement families:

- `grace_period`
- `setup_start`
- `early_operational_access`
- `off_timeline_visit`
- `deliveries`
- `supplier_access`
- `supplier_information`
- `supplier_responsibility`
- `venue_clearing`
- `storage_use`
- `back_office_use`
- `multi_day_timeline`
- `multi_day_responsibility`
- `installation`
- `waste_removal`
- `cleaning_reset`
- `professional_cleaning`

## Grace And Setup Semantics

- Studio rentals return a `15` minute grace period.
- Entire Venue rentals return a `30` minute grace period.
- Grace periods are modeled with `timing_purpose = arrival_departure_only`.
- Setup is modeled separately and starts at `booked_start_time`.
- Earlier setup is not implied by grace time. It is represented as a separate `early_operational_access` rule that requires explicit approval.

## Current Operational Rules Represented

- Arrival and departure grace periods for Studio and Entire Venue rentals.
- Setup starts at booked time.
- Earlier operational access requires separately booked or approved access.
- Visits outside the timeline require confirmed appointment handling.
- Deliveries and supplier access stay inside approved access windows.
- Supplier details must be collected before handover when suppliers are in scope.
- Supplier responsibility stays with the client unless WNC has accepted it in writing.
- Entire Venue clearing is not automatic and must be defined explicitly.
- Storage Room operational storage remains conditional and non-guest-facing.
- Back Office use remains conditional and preparation-sensitive.
- Multi-day rentals require a day-by-day timeline, and Entire Venue multi-day reset responsibility remains with the client unless defined WNC tasks are included.
- Plaster-wall fixings and strong-bond adhesives are prohibited.
- Low-risk removable adhesives, wooden-beam fixings, and exterior items remain conditional.
- Waste removal and standard cleaning/reset remain client responsibilities unless separately included.
- Professional-cleaning triggers stay manual-review based rather than guessed from a fake threshold.

## Missing-Information Semantics

- If a rental-type-specific rule exists and `rental_type_code` is missing, the API returns `insufficient_information`.
- If a multi-day-only rule exists and `multi_day` is missing, the API returns `insufficient_information`.
- If no approved rule matches the supplied scope, the API returns `no_applicable_rule`.
- The domain never treats missing information as implicit permission.

## Non-Goals

This slice explicitly does not implement:

- live event schedules
- staffing counts or staff assignment
- vendor selection or competence checks
- proposal wording or email drafting
- live rental-record updates
- cleaning pricing
- overtime pricing
- AI judgement about whether a custom plan is sensible
- full production-management workflow

## Query Surfaces

- `public.current_operational_requirements`
- `api.get_operational_requirements(p_rental_type_code, p_requirement_type, p_space_code, p_multi_day, p_context_code, p_as_of_date)`

The API can return multiple applicable rows for the same known rental context.

## Example Queries

```sql
select timing_minutes, timing_purpose, outcome
from api.get_operational_requirements(
  'studio_space',
  'grace_period',
  null,
  false,
  null,
  date '2026-08-05'
);
```

Expected current result: `15`, `arrival_departure_only`, `required`

```sql
select requirement_type, outcome, timing_reference, requires_confirmation
from api.get_operational_requirements(
  'studio_space',
  'setup_start',
  null,
  false,
  null,
  date '2026-08-05'
);
```

Expected current result: setup starts at `booked_start_time`

```sql
select outcome, requires_confirmation
from api.get_operational_requirements(
  'studio_space',
  'early_operational_access',
  null,
  false,
  'approved_timeline_only',
  date '2026-08-05'
);
```

Expected current result: early access requires explicit approval

```sql
select outcome, requires_preparation, requires_confirmation
from api.get_operational_requirements(
  'entire_venue',
  'venue_clearing',
  null,
  false,
  'full_scope_definition',
  date '2026-08-05'
);
```

Expected current result: clearing is conditional and not automatic

```sql
select outcome, manual_review_required
from api.get_operational_requirements(
  null,
  'professional_cleaning',
  null,
  false,
  'significant_mess_or_residue',
  date '2026-08-05'
);
```

Expected current result: `manual_review_required = true`
