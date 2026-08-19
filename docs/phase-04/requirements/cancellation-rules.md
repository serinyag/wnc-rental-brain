# Cancellation Rules

## Purpose

The cancellation-rule slice answers:

> Given the known cancellation timing and scenario, what approved WNC contractual cancellation treatment applies?

This slice stores policy consequences only. It does not calculate live refund amounts, deductions, or payout balances for a specific rental.

## Authoritative Source Basis

Primary controlled sources for this slice:

- `WNC Rental Pricing, Fees & Payment Rules`
- `WNC Rental Policy Decisions & Change Log`

Supporting current sources:

- `Studio Space _ Terms and Conditions.docx`
- `Full Venue _ Rental Terms and Conditions.docx`
- `WNC Rental Agreement Template.docx`

Source review outcome:

- the supplied `xlsm` and `xlsx` pricing workbooks align on `CR-001`, `CR-002`, and `CR-003` for client-cancellation treatment and security-deposit treatment
- the decision log resolves the more-than-30-day and 30-days-or-fewer client-cancellation windows, plus production and production-coordination fee non-refundability
- the editable Studio and Full Venue terms add two controlled cancellation scenarios not represented in the workbook row set:
  - WNC cancellation unrelated to client breach -> refund all fees and deposits in full
  - client breach termination -> WNC may cancel immediately and retain all payments made
- facilitator class-cancellation charges remain outside this slice because they are a separate charge domain triggered by short-notice confirmation, not the core rental-cancellation policy itself
- postponement and rescheduling treatment are not currently governed as an authoritative deterministic policy

## Business Questions

This domain should answer:

- what happens to rental payments when the client cancels
- what happens to any booking fee
- what happens to agreed production or production-coordination fees
- how non-recoverable third-party costs are treated
- how security-deposit treatment is expressed where the cancellation policy explicitly mentions it
- what happens if WNC cancels for reasons unrelated to client breach
- what happens if WNC cancels because the client breached the agreement
- which outcomes still require manual assessment of live costs or deductions

## Inputs

Only approved inputs are required:

- `cancellation_scenario`
- optional `cancellation_date`
- optional `event_date`
- optional `cost_category`
- optional `as_of_date` for historical lookup

`rental_type` is not required because the current approved cancellation policy applies globally across the standard rental products in the authoritative source set.

## Structured Outcomes

The implemented machine-readable treatment values are:

- `refundable`
- `non_refundable`
- `refundable_less_nonrecoverable_costs`
- `client_remains_responsible_for_nonrecoverable_costs`
- `returned_unless_valid_deductions`
- `refunded_in_full`
- `retained_by_wnc`

Meaning:

- `refundable`: the covered amount category is refundable under the policy
- `non_refundable`: the covered amount category is not refundable
- `refundable_less_nonrecoverable_costs`: refund treatment applies, but committed or non-recoverable costs must still be deducted and therefore require live assessment
- `client_remains_responsible_for_nonrecoverable_costs`: the client still owes committed or non-recoverable costs even though the rental is cancelled
- `returned_unless_valid_deductions`: the security deposit is returned unless valid deduction grounds exist
- `refunded_in_full`: WNC refunds the covered fees and deposits in full
- `retained_by_wnc`: WNC may retain all payments already made

## Lead-Time Semantics

This slice reuses:

- `private.calculate_calendar_lead_time_days(start_date, end_date)`

For client-cancellation timing:

- `start_date = cancellation_date`
- `end_date = event_date`

Behavior:

- returns `end_date - start_date` in whole calendar days
- same-day cancellation returns `0`
- missing dates return `null`
- `start_date > end_date` raises a controlled validation error

The approved cancellation boundary is:

- `31+` calendar days before the event -> more-than-30-day rule
- `0-30` calendar days before the event -> 30-days-or-fewer rule

## Non-goals

Cancellation rules do not decide or store:

- a live client refund amount
- actual committed supplier costs
- refund processing
- Mollie actions
- cancellation emails
- proposal revisions
- operational rental-state updates
- AI judgement

## Query Contract

Cancellation retrieval can legitimately return multiple cost-category consequences for the same scenario.

For example, a client cancellation may yield distinct rows for:

- rental payments
- booking fee
- production and production-coordination fees
- non-recoverable third-party costs
- security deposit

These are cumulative category-specific consequences, not mutually exclusive single winners.

## Applicability Rules

- `client_cancellation` uses calendar lead time where the specific cost category depends on timing
- rows whose treatment is independent of lead time, such as booking-fee non-refundability, still apply even if the exact cancellation window is unknown
- lead-time-dependent rows return `insufficient_information` rather than guessing when the date context is missing
- `wnc_cancellation_no_client_breach` does not require lead-time context
- `client_breach_termination` does not require lead-time context
- `cancellation_date > event_date` raises a controlled validation error instead of being treated as a normal pre-event cancellation

## Example Queries

- `client_cancellation`, `cancellation_date = 2026-08-02`, `event_date = 2026-09-02` -> `31` days -> rental payments `refundable`
- `client_cancellation`, `cancellation_date = 2026-08-03`, `event_date = 2026-09-02` -> `30` days -> rental payments `non_refundable`
- `client_cancellation`, `cancellation_date = 2026-09-01`, `event_date = 2026-09-02` -> `1` day -> short-notice client-cancellation treatment applies
- `client_cancellation`, missing `cancellation_date` -> timing-dependent categories return `insufficient_information`, while timing-independent categories still return their controlled treatment
- `wnc_cancellation_no_client_breach` -> `all_fees_and_deposits` `refunded_in_full`
- `client_breach_termination` -> `all_payments_received` `retained_by_wnc`

## Manual-Assessment Boundary

This slice preserves policy consequences that still need live rental facts:

- committed third-party costs
- valid security-deposit deductions

Those rows are structurally marked `requires_manual_review = true`.

That means:

- the policy consequence is deterministic
- the euro amount is not

## Acceptance Criteria

1. Approved cancellation policy is represented in a typed relational table linked to `rule_catalogue`.
2. Client-cancellation treatment preserves category-specific consequences instead of collapsing them into one synthetic refund percentage.
3. The retrieval interface can return multiple applicable cost-category rows for the same cancellation scenario.
4. Missing cancellation timing does not cause timing-dependent cancellation treatment to be guessed.
5. `cancellation_date > event_date` raises a controlled validation error.
6. WNC cancellation unrelated to client breach and client-breach termination are represented as distinct controlled scenarios.
7. Manual assessment remains explicit where the policy depends on non-recoverable costs or valid deductions.
8. Active cancellation rules have provenance through `rule_source_links`.
9. Historical cancellation rule versions remain queryable by `as_of_date` while the current view excludes superseded versions.
10. `db reset` and the complete database test suite pass from Git-controlled files only.
