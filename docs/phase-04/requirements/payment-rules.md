# Payment Rules

## Purpose

The payment-rule slice answers:

> Given known rental and payment context, what approved WNC payment requirement applies?

This slice structures payment policy only. It does not calculate or store live payment state for a specific rental.

## Authoritative Source Basis

Primary controlled sources for this slice:

- `WNC Rental Pricing, Fees & Payment Rules`
- `WNC Rental Policy Decisions & Change Log`

Supporting current sources:

- `Studio Space _ Terms and Conditions.docx`
- `Full Venue _ Rental Terms and Conditions.docx`
- `WNC Rental Agreement Template.docx`

Source review outcome:

- the supplied `xlsm` and `xlsx` pricing workbooks align on the direct-rental payment rules from `PAY-001` through `PAY-006`
- the decision log resolves the canonical 30% / 100% upfront choice, the lead-time restriction on the 30% option, the 70% final-balance timing, and the 3-day / 24-hour short-notice deadlines
- `PAY-007 Storefront` is still marked `Working`, so platform-specific payment handling is excluded from deterministic seeding
- security deposits remain a separate domain and must not be treated as a normal rental-payment instalment

## Business Questions

This domain should answer:

- what upfront payment options are approved
- when the 30 percent upfront option is available or unavailable
- what minimum confirmation payment secures the booking
- whether payment of the confirmation amount records acceptance of the applicable terms
- whether a final balance rule applies
- what relative timing rule applies to that final balance
- what short-notice confirmation-payment deadline applies based on booking lead time
- whether an approved exception path exists and which role approves it

## Inputs

Only approved payment-policy dimensions are implemented:

- optional `payment_stage`
- optional `payment_plan_option`
- optional `booking_lead_time_days`
- optional `as_of_date` for historical lookup

`booking_lead_time_days` is a derived context input supplied by the caller. This slice does not calculate it from live booking and event records.

## Outputs

The implemented structured outputs are:

- stable `rule_code`
- `rule_version`
- `status`
- effective dating from shared rule governance
- `payment_stage`
- `payment_plan_option`
- `percentage_due`
- `payment_basis`
- `deadline_type`
- `deadline_value`
- `booking_lead_time_min_days`
- `booking_lead_time_max_days`
- `required_for_confirmation`
- `confirms_booking`
- `records_terms_acceptance`
- `exception_allowed`
- `exception_approver`
- provenance through `rule_source_links`

## Static Policy Versus Operational Date

This slice stores static policy such as:

- `remaining 70% due 14 days before event`
- `confirmation payment due within 24 hours`

It does not store derived operational facts such as:

- `rental ABC balance due on 2026-09-16`
- `invoice INV-123 is overdue`

Those belong to a future rental-state layer.

## Non-goals

Payment rules do not decide or store:

- live invoice status
- invoice IDs
- client payment records
- Mollie or Storefront transactions
- actual due dates for a specific rental
- overdue calculations for real rentals
- payment reminders
- invoice generation
- security-deposit risk logic
- platform-specific Storefront fee handling

## Query Contract

Payment rules are not mutually exclusive overall.

The approved policy contains stage-specific rules that can coexist, including:

- allowed upfront payment options
- booking-confirmation requirements
- short-notice confirmation-payment deadlines
- final-balance requirements

Therefore, the retrieval contract for this domain may return:

- zero rules
- one rule
- multiple stage-specific rules

The query layer does not collapse these into one winner.

## Applicability Rules

- `upfront_option` rules can return multiple approved options, but lead-time-limited options are returned only when `booking_lead_time_days` supports them
- `confirmation_requirement` returns the minimum confirmed-payment rule and its booking-confirmation consequence
- `confirmation_deadline` rules require `booking_lead_time_days`
- `final_balance` rules require the selected `payment_plan_option` and any lead-time applicability that makes that plan valid
- if required context is missing, the contingent rule is not returned
- for `0-14` day confirmations, only `upfront_100` is available and the `upfront_30` plus `final_balance` path is suppressed structurally
- payment rules remain static policy statements even when a later operational system would need to derive an actual due date

## Example Queries

- `payment_stage = upfront_option`, `booking_lead_time_days = 15` -> returns the approved `30%` and `100%` upfront options
- `payment_stage = upfront_option`, `booking_lead_time_days = 14` -> returns only the approved `100%` upfront option
- `payment_stage = confirmation_deadline`, `booking_lead_time_days = 20` -> returns the `within 3 days` confirmation-payment rules
- `payment_stage = confirmation_deadline`, `booking_lead_time_days = 10` -> returns only the `100% within 24 hours` confirmation-payment rule
- `payment_stage = final_balance`, `payment_plan_option = upfront_30`, `booking_lead_time_days = 15` -> returns the `70% due 14 days before event` rule
- `payment_stage = final_balance`, `payment_plan_option = upfront_30`, `booking_lead_time_days = 14` -> returns no rule because the 30% path is not permitted
- `payment_stage = final_balance`, missing `payment_plan_option` -> returns no rule rather than guessing

## Acceptance Criteria

1. Approved payment rules are represented in a typed relational table linked to `rule_catalogue`.
2. Each seeded active payment rule has provenance through `rule_source_links`.
3. The domain-specific retrieval interface can return multiple stage-specific rules where the source policy is cumulative or sequential.
4. Missing `booking_lead_time_days` or `payment_plan_option` does not cause option-dependent rules to be guessed.
5. Short-notice lead-time precedence is represented without overlapping active deadline rules.
6. The `upfront_30` path and its dependent `final_balance` rule are structurally unavailable for `0-14` day confirmations.
7. Static policy semantics such as `14 days before event` remain stored as relative policy, not converted into live rental due dates.
8. Platform-specific Storefront handling is excluded from deterministic seeding until the working rule is governed.
9. Historical payment-rule versions remain queryable by `as_of_date` while the current view excludes superseded versions.
10. `db reset` and the complete database test suite pass from Git-controlled files only.
