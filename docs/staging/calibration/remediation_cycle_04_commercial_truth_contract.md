# Calibration Remediation Cycle 4: Commercial Truth Contract

## Diagnosis

The frozen `holdout-20260829-103354` artifact was generated on 2026-08-29; its
report and JSON metadata incorrectly contained the hard-coded date 2026-08-20.
The historical artifact is preserved. Future artifacts use their runtime UTC
timestamp.

HOLD-002 has a three-hour Studio window. The governed Phase 4 rule for one to
three hours is EUR 50, so the deployed result was correct and the frozen EUR 75
expectation was not. Its technical `unknown_internal` state was also correct.
The lookup now still uses the event date, rather than the service clock, so a
future-dated rule revision will be evaluated against the requested event.

HOLD-008 did not have enough governed schedule scope to resolve a duration.
The projection correctly returned `Not established` and no effective fee. The
frozen expectation incorrectly demanded a EUR 75 effective fee, which would
have been an unsupported commitment. The corrected gold expectation preserves
the missing timing question and requires no effective fee.

HOLD-009 contained a pending commercial exception decision. The generic
capacity inference created an unrelated `unknown_internal` feasibility effect,
which displaced the approval-only commercial posture. Pending commercial
decisions now remain approval-gated without generic capacity inference changing
their commercial status.

## Precedence

| Situation | Booking-fee baseline | Effective booking fee |
| --- | --- | --- |
| Current rule and current schedule scope | Current rule for the event date | Same baseline unless an approved exception is active |
| Current rule with proposed schedule | Reference only | Not produced |
| Client timing missing | Not established | Not produced |
| Historical fee or waiver | Context only | Never promoted |
| Proposed exception | Current baseline remains | Not produced until approved |
| Approved exception | Current baseline remains visible | Approved exception value |

Current authoritative rules resolve their own proposition even when historical
precedent differs. Confirmation is reserved for that proposition only; an
unrelated generic feasibility inference cannot convert an approval-gated
commercial decision into an authority gap.
