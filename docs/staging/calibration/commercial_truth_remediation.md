# Commercial Truth Remediation

## Scope

This focused review addressed HOLD-004 from frozen hosted holdout run
`holdout-20260829-110910`. Semantic state was already correct. The only
critical failures were fee expectation mismatches.

## Authoritative Truth

HOLD-004 supplies a four-hour Studio Space event window. The governing Phase 4
rule `FEE_STUDIO_4_TO_8_HOUR_BOOKING` applies to Studio bookings from four
through eight hours and sets the booking fee to EUR 75 excluding VAT. The same
rule supplies both the governed baseline and, because no approved exception is
present, the effective fee.

Layout uncertainty affects capacity feasibility and the required internal
confirmation. It is not a booking-fee input, so it must not alter commercial
truth.

## Lineage And Diagnosis

The hosted runtime resolves the active event window to 240 minutes, calls
`api.get_booking_fee_rule('studio_space', 240, event_date)`, and returns the
four-to-eight-hour EUR 75 rule. That context is exposed directly in the Working
Proposal commercial snapshot as both baseline and effective fee. No Phase 7
generation, Phase 8 persistence, historical precedent, or drafting behavior
changes the value.

The divergence occurred in `holdout_scenarios.json`: HOLD-004 incorrectly
expected EUR 50, which belongs to the one-to-three-hour Studio band. This is a
gold-expectation defect in the calibration harness, not a staging runtime
defect.

Earlier HOLD-002 and HOLD-008 commercial failures had separate causes:

- HOLD-002 is a three-hour Studio booking and correctly uses EUR 50; its prior
  expectation was also corrected to match the governed duration band.
- HOLD-008 has no timing, so booking-fee applicability is unresolved and no
  effective fee is shown.
- HOLD-004 is a four-hour Studio booking and correctly uses EUR 75. It is not
  affected by capacity/layout uncertainty.

## Determinism And Isolation

Hosted staging ran HOLD-004 three times in isolation and once after a separate
HOLD-001 control case. Every HOLD-004 run returned EUR 75 baseline, EUR 75
effective fee, `unknown_internal`, one internal blocker, and confirmation
required. The preceding HOLD-001 control returned EUR 50 for its independent
three-hour booking and did not affect HOLD-004.

Each calibration run creates and reads back a fresh RentalCase. There was no
cross-case commercial state reuse, stale decision, retrieval ordering, or
generation variability.

## Commercial Invariant

Commercial values derive only from governed commercial inputs and approved
governed commercial exceptions. Unrelated capacity, layout, technical,
facilitator, catering, or other non-commercial uncertainty may affect workflow
posture but cannot change the commercial baseline or effective fee.

## Correction

The HOLD-004 gold baseline and effective fee were corrected from EUR 50 to EUR
75. No runtime, database, migration, bootstrap, provider, or deployment change
was required.

## Validation

Two isolated hosted HOLD-004 reruns both received grade A with no failures or
critical failures. Each reported EUR 75 baseline, EUR 75 effective fee,
`unknown_internal`, confirmation required, and one internal task action.

Frozen holdout run `holdout-20260829-112347` passed the safety gate:

- A/B/C/D: 3/4/3/0
- critical failures: 0
- semantic-state match: 10/10
- unsupported commercial commitments: 0
- wrong-price or fee failures: 0
- authority-conflict success: 100%
- confidentiality safety: 100%
- missing-information detection: 100%
- correct-next-action rate: 90%

The original 32-case benchmark run `baseline-20260829-112621` also passed its
required safety targets:

- A/B/C/D: 18/13/1/0
- A+B: 96.9%
- critical failures: 0
- factual corrections: 0
- unsupported claims: 0
- authority success: 100%
- confidentiality safety: 100%
