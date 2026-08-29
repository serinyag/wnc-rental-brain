# Calibration Remediation Cycle 3 Diagnosis

## Frozen Evidence Reviewed

- Original 32-case benchmark and Cycle 1 results
- Frozen first holdout definition and Cycle 2 hosted result
- Cycle 2 semantic-state contract and diagnosis
- Phase 7 consumption, Phase 8 orchestration, staging authority bridge, and calibration runners

## First Incorrect Transitions

### HOLD-001

Current Phase 5 technical evidence for ordinary audio and standard Wi-Fi was retrieved and classified as supported. The staging bridge represented supported technical evidence by emitting no projection. In parallel it evaluated studio capacity without a layout configuration and emitted a case-wide `unknown_internal` projection, even though the 14-guest request was within every published studio capacity limit. Phase 8 then created an authority-gap blocker and internal task.

The first incorrect transition was the staging authority bridge converting non-material capacity uncertainty into a case-wide authority gap. Cycle 3 preserves current affirmative evidence and treats a no-layout studio count inside all published limits as `known_yes`.

### HOLD-009

Current Phase 4 booking-fee truth remained intact and the legacy discount correctly became an approval-gated proposed case decision. The staging bridge nevertheless emitted `unknown_internal` for capacity before the commercial exception was evaluated, because it treated the 24-guest studio request as unresolved without a layout configuration. This turned a deterministic governed baseline plus approval-gated exception into a generic confirmation path.

The first incorrect transition was again the case-wide capacity authority projection, not Phase 4 or Phase 6 retrieval. The correct action is the approval-gated case-decision path with no `current_authority_missing` blocker.

## Independent Next-Action Defect

The calibration runner's previous action scorer considered only two outcomes: client follow-up or no blocker. It therefore assigned zero to correct deterministic restrictions and correct internal confirmation paths. This was independent of classification. Cycle 3 adds explicit expected-action evaluation for no action, client follow-up, internal confirmation, deterministic restriction, and approval-gated exception paths.

## Changed Layers

- Phase 7 semantic precedence and effect derivation
- Staging synthetic authority bridge capacity and positive-evidence handling
- Calibration action evaluator and action-matrix regression tests

Phase 5/6 retrieval, Microsoft Graph, Outlook, and provider execution are unchanged.

