# Booking Fee Rules

## Purpose

The booking-fee rule slice answers:

> For a known rental type and booked duration, what approved WNC booking-fee rule currently applies?

This slice validates the Phase 4 architecture for one narrow commercial domain without pulling in payment schedules, expedited surcharges, deposits, cancellations, or venue pricing logic.

## Authoritative Source Basis

Primary controlled sources for this slice:

- `WNC Rental Pricing, Fees & Payment Rules`
- `WNC Rental Policy Decisions & Change Log`

Supporting current sources:

- `Studio Space _ Terms and Conditions.docx`
- `Full Venue _ Rental Terms and Conditions.docx`
- `WNC Rental Agreement Template.docx`

Source review outcome:

- the supplied `xlsm` and `xlsx` pricing workbooks align on booking-fee values, refundability, waiver authority, and duration bands
- the broader workbook conflict remains real in other commercial domains, but it does not block booking-fee implementation
- waiver authority is approved
- waiver criteria are not approved and remain outside deterministic rule logic

## Business Question

The table determines whether a booking fee applies, and if so:

- how much it is
- what currency it uses
- what VAT rate applies
- whether it is refundable
- whether waiver is allowed
- which authority may waive it

## Inputs

Only approved booking-fee dimensions are implemented:

- `rental_type`
- `booked_duration_minutes`
- optional `as_of_date` for historical lookup

No additional dimension is modeled unless supported directly by the approved source set.

### Duration Interpretation

Booking-fee applicability is source-backed by duration bands:

- Studio Space: `1-3 hours`
- Studio Space: `4-8 hours`
- Entire Venue: `1-3 hours`
- Entire Venue: `4-7 hours`
- Entire Venue: `Full day`

For lookup purposes, durations are normalized into whole-hour rental buckets:

- `1` through `60` minutes = `1` hour
- `61` through `120` minutes = `2` hours
- `121` through `180` minutes = `3` hours
- `181` through `240` minutes = `4` hours
- in general, `rental_duration_hours = ceil(duration_minutes / 60)`

Exact hour boundaries remain in that hour bucket:

- `180` minutes = `3` hours
- `240` minutes = `4` hours

Any duration above a boundary moves to the next hour bucket:

- `181` minutes = `4` hours
- `210` minutes = `4` hours
- `241` minutes = `5` hours

The `Full day` band is interpreted as the `8-hour` bucket, which covers `421` through `480` minutes under this normalization. This is a narrow supporting dependency from the same controlled commercial source set, not a rollout of the venue-pricing domain.

## Outputs

The implemented structured outputs are:

- stable `rule_code`
- `rule_version`
- `status`
- effective dating from shared rule governance
- `rental_type`
- `duration_band_label`
- `duration_min_hours`
- `duration_max_hours`
- `is_fee_charged`
- `fee_ex_vat`
- `currency_code`
- `vat_rate`
- `is_refundable`
- `waiver_allowed`
- `waiver_authority`
- provenance through `rule_source_links`

## Non-goals

Booking-fee rules do not decide:

- expedited surcharge
- venue rental price
- payment schedule
- cancellation treatment
- deposits
- overtime
- class-cancellation fees
- full-production pricing
- when a waiver should be granted
- whether a client should receive an exception in practice

## Applicability Rules

- a rule matches only when `rental_type` and normalized whole-hour `booked_duration_minutes` identify a single approved duration band
- if a required input is missing, no rule is returned
- if the normalized hour bucket has no approved band, no rule is returned
- if multiple current rules match, that is a data-integrity failure and the query layer must not quietly choose one

## Example Queries

- Studio, `180` minutes -> `3-hour` bucket -> `1-3 hour` booking-fee rule
- Studio, `181` minutes -> `4-hour` bucket -> `4-8 hour` booking-fee rule
- Studio, `210` minutes -> `4-hour` bucket -> `4-8 hour` booking-fee rule
- Studio, `240` minutes -> `4-hour` bucket -> `4-8 hour` booking-fee rule
- Entire Venue, `420` minutes -> `7-hour` bucket -> `4-7 hour` booking-fee rule
- Entire Venue, `421` minutes -> `8-hour` bucket -> `Full day` no-booking-fee rule
- Entire Venue, `450` minutes -> `8-hour` bucket -> `Full day` no-booking-fee rule
- Entire Venue, `480` minutes -> `8-hour` bucket -> `Full day` no-booking-fee rule

## Acceptance Criteria

1. Approved booking-fee rules are represented in a typed relational table linked to `rule_catalogue`.
2. Each seeded booking-fee rule has provenance through `rule_source_links`.
3. The current lookup surface returns the correct rule for approved matching inputs.
4. Missing `rental_type` or `booked_duration_minutes` does not produce a guessed match.
5. Whole-hour normalization removes artificial gaps between labeled hour bands.
6. A full-day Entire Venue lookup returns the explicit no-booking-fee rule rather than falling through to no result.
7. Waiver authority is represented only where approved, and waiver criteria remain outside deterministic logic.
8. Overlapping active booking-fee applicability cannot be inserted for the same rental type and effective period.
9. Historical rule versions remain queryable by `as_of_date` while the current view excludes superseded versions.
10. `db reset` and the full database test suite pass from Git-controlled files only.
