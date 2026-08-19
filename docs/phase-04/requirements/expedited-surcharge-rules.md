# Expedited Surcharge Rules

## Purpose

The expedited-surcharge slice answers:

> Given the known confirmation lead time, does the approved WNC expedited surcharge apply, what percentage applies, what is the calculation basis, what VAT treatment applies, and can the surcharge be waived?

This slice stores policy only. It does not calculate a live euro surcharge amount for a specific rental.

## Authoritative Source Basis

Primary controlled sources for this slice:

- `WNC Rental Pricing, Fees & Payment Rules`
- `WNC Rental Policy Decisions & Change Log`

Supporting current sources:

- `Studio Space _ Terms and Conditions.docx`
- `Full Venue _ Rental Terms and Conditions.docx`
- `WNC Rental Agreement Template.docx`

Source review outcome:

- the supplied `xlsm` and `xlsx` pricing workbooks align on the expedited-surcharge row `ES-001`
- the decision log resolves the trigger, all-rental-type scope, 10 percent rate, excluded charges, and 21 percent VAT treatment through `DEC-015` to `DEC-019`
- the controlled source set leaves waiver criteria open, so the database stores waiver permission and authority only
- source wording varies between `rental date` and `event date`; this slice implements the approved current policy semantics as confirmation lead time relative to the event date

## Business Questions

This domain should answer:

- whether the expedited surcharge applies for the known confirmation lead time
- what structured percentage rate applies
- what calculation basis applies
- what VAT rate applies to the surcharge line item
- whether the surcharge may be waived
- which role has waiver authority

## Inputs

Only approved inputs are required:

- `confirmation_date`
- `event_date`
- optional `as_of_date` for historical lookup

`rental_type` is not required because the approved current policy applies to all rental types.

## Outputs

The implemented structured outputs are:

- stable `rule_code`
- `rule_version`
- `status`
- effective dating from shared rule governance
- `lead_time_min_days`
- `lead_time_max_days`
- `percentage_rate`
- `calculation_basis`
- `vat_rate`
- `waiver_allowed`
- `waiver_authority`
- derived `lead_time_days`
- derived `applies`
- derived `applicability_status`
- `plain_language_explanation`
- provenance through `rule_source_links`

## Lead-Time Semantics

This slice uses a reusable helper:

- `private.calculate_calendar_lead_time_days(start_date, end_date)`

Behavior:

- returns `end_date - start_date` in whole calendar days
- same-day confirmation returns `0`
- confirmation exactly 14 calendar days before the event returns `14`
- missing dates return `null`
- `start_date > end_date` raises a controlled validation error

For this domain:

- `start_date = confirmation_date`
- `end_date = event_date`

The approved applicability rule is:

- `0` through `14` calendar days -> expedited surcharge applies
- `15+` calendar days -> expedited surcharge does not apply

## Non-goals

Expedited-surcharge rules do not decide or store:

- the final euro surcharge for a live rental
- the actual venue-rental subtotal
- invoice generation
- payment collection
- approval workflow UI
- automatic waiver decisions
- proposal totals

## Query Contract

This slice seeds one active policy rule version at a time, then derives applicability from the supplied dates.

The retrieval interface distinguishes:

- `applies`
- `does_not_apply`
- `insufficient_information`

Invalid input is handled separately:

- `confirmation_date > event_date` raises a controlled validation error instead of being treated as a normal non-applicable booking

## Applicability Rules

- if `confirmation_date` and `event_date` are both known and lead time is `0-14`, the rule returns `applicability_status = applies`
- if both dates are known and lead time is `15+`, the rule returns `applicability_status = does_not_apply`
- if either date is missing, the rule returns `applicability_status = insufficient_information`
- the stored calculation basis remains `venue_rental_only`, even when a future pricing layer would need a live venue-rental subtotal
- waiver permission is stored, but the actual waiver decision remains a future rental-specific exception record

## Example Queries

- `confirmation_date = 2026-08-18`, `event_date = 2026-09-02` -> `15` days -> `does_not_apply`
- `confirmation_date = 2026-08-19`, `event_date = 2026-09-02` -> `14` days -> `applies`
- `confirmation_date = 2026-08-26`, `event_date = 2026-09-02` -> `7` days -> `applies`
- `confirmation_date = 2026-09-02`, `event_date = 2026-09-02` -> `0` days -> `applies`
- missing `confirmation_date` or `event_date` -> `insufficient_information`
- `confirmation_date = 2026-09-03`, `event_date = 2026-09-02` -> controlled validation error

## Acceptance Criteria

1. Approved expedited-surcharge policy is represented in a typed relational table linked to `rule_catalogue`.
2. The stored rule captures `0-14` day applicability, `0.10` percentage rate, `venue_rental_only` basis, `0.21` VAT, and waiver authority.
3. The retrieval interface derives `applies`, `does_not_apply`, and `insufficient_information` without requiring a rental subtotal.
4. Missing `confirmation_date` or `event_date` does not produce a guessed applicable surcharge.
5. `confirmation_date > event_date` raises a controlled validation error.
6. Active expedited-surcharge rules have provenance through `rule_source_links`.
7. Historical expedited-surcharge rule versions remain queryable by `as_of_date` while the current view excludes superseded versions.
8. Waiver criteria are not invented or automated; only waiver permission and authority are stored.
9. `db reset` and the complete database test suite pass from Git-controlled files only.
