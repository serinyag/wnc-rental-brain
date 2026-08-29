# Holdout 2 Gold and Action-Contract Adjudication

- clean run: `holdout2-20260829-120008`
- frozen file SHA-256: `a2f99889c36d8853fc2feb5c370e08b4e2171510898dd7a0c0323a72ac2034c8`
- evidence posture: hosted case snapshots and current governed seed/rule sources only; no runtime, harness, gold, prompt, or hosted-case changes were made.
- provider posture: Outlook disabled; no Microsoft Graph or Asana execution.

## Executive Finding

`HOLDOUT2_EVALUATION_CONTRACT_REPAIR_REQUIRED`

The raw gate failure is primarily evaluation design, not a demonstrated runtime defect. The three primary semantic mismatches and six proposition semantic mismatches use gold that conflicts with current governed rules. The eight raw next-action misses are attributable to two gold defects, three proposition-provenance harness defects, and three scenarios that did not execute the waiting stage that forms `REQUEST_CLIENT_INFORMATION` actions. No material runtime defect remains after adjudication.

## Raw Metrics

| Metric | Raw result |
| --- | ---: |
| A/B/C/D | 4 / 8 / 0 / 0 |
| A+B | 100.0% |
| Critical failures | 0 |
| Unsupported assertions | 0 |
| Wrong-price failures | 0 |
| Unsupported commercial commitments | 0 |
| Authority / confidentiality | 100% / 100% |
| Primary semantic-state match | 9/12 (75.0%) |
| Correct-next-action | 4/12 (33.3%) |
| Over-caution failures | 1 |

## Current Truth and Taxonomy

The semantic implementation defines `known_no` from an authoritative external/not-available/restricted outcome, `known_conditional` from a confirmation requirement, and `unknown_internal` from manual review or absent current authority. Its dominant-state rule intentionally gives a deterministic prohibition priority over unrelated unresolved propositions. This makes a case-level state unsuitable for grading the action of one proposition in a compound case.

- `TECH_REQ_BASIC_PROJECTION_CONFIRM`: basic projection requires compatibility, adapters, files, and screenless-setup confirmation; it is `known_conditional`.
- `TECH_REQ_ORDINARY_AUDIO_SUPPORTED`: ordinary playback is supported; it is `known_yes`.
- `TECH_REQ_AMPLIFIED_SOUND_EXTERNAL`: amplified event sound is externally supplied; it is `known_no`.
- `TECH_REQ_CUSTOM_TECH_CONFIRM`: custom technical setup requires explicit review and confirmation; it is `known_conditional`, not an absence of authority.
- `FACILITATOR_WNC_PROVIDED_CONFIRMATION_REQUIRED`: WNC-provided facilitator scope is `known_conditional`.
- `CATER_EXTERNAL_CATERER_ALLOWED`: client external caterers are allowed; storage/power confirmation applies only when those needs are in scope.

These are current Phase 4/5 governed sources from `OPS-002`, `SERV-001`, and `SERV-003`. No historical/Phase 6 assertion was used to adjudicate gold.

## Primary Action Table

| Case | Expected state | Actual state | Expected action | Actual observable action | Raw match | Adjudication |
| --- | --- | --- | --- | --- | --- | --- |
| HOLD2-001 | known_yes | known_conditional | deterministic_response | confirmation blocker and internal review | no | GOLD_DEFECT |
| HOLD2-002 | known_yes | known_yes | deterministic_response | no blocker/action | yes | confirmed |
| HOLD2-003 | known_no | known_no | deterministic_response | deterministic restriction plus unrelated capacity-review task | no | HARNESS_DEFECT |
| HOLD2-004 | known_no | known_no | deterministic_response | deterministic restriction plus facilitator-confirmation task | no | HARNESS_DEFECT |
| HOLD2-005 | known_conditional | known_no | internal_confirmation | deterministic restriction only | no | GOLD_DEFECT |
| HOLD2-006 | known_conditional | known_conditional | internal_confirmation | confirmation blocker and internal review | yes | confirmed |
| HOLD2-007 | unknown_internal | known_conditional | internal_confirmation | confirmation blocker and internal review | yes | GOLD_DEFECT (semantic only) |
| HOLD2-008 | unknown_internal | unknown_internal | internal_confirmation | internal authority-review task | yes | confirmed |
| HOLD2-009 | missing_client_fact | missing_client_fact | ask_client | OpenQuestion only; no waiting follow-up/action | no | SCENARIO_EXECUTION_DEFECT |
| HOLD2-010 | missing_client_fact | missing_client_fact | ask_client | OpenQuestion only; no waiting follow-up/action | no | SCENARIO_EXECUTION_DEFECT |
| HOLD2-011 | missing_client_fact | missing_client_fact | ask_client | OpenQuestion plus unrelated internal reviews; no waiting follow-up/action | no | SCENARIO_EXECUTION_DEFECT |
| HOLD2-012 | known_no | known_no | deterministic_response | deterministic restriction plus unrelated technical-confirmation task | no | HARNESS_DEFECT |

`deterministic_response` is correctly understood as an absence/presence contract, not a literal workflow action: known-yes requires no unsupported uncertainty, while known-no requires the deterministic restriction to remain controlling. The raw evaluator failed the known-no cases because it attributed any case-level internal task to the known-no proposition.

## Semantic Mismatch Adjudication

| Case | Proposition | Expected | Actual | Primary classification | Secondary | Gold audit and evidence |
| --- | --- | --- | --- | --- | --- | --- |
| HOLD2-001 | primary / projection_display | known_yes | known_conditional | GOLD_DEFECT | none | `TECH_REQ_BASIC_PROJECTION_CONFIRM` directly requires confirmation. Gold inferred that projection support was unconditional; confidence: high. |
| HOLD2-002 | facilitator:client_external_caterer | known_conditional | no semantic projection / case known_yes | GOLD_DEFECT | HARNESS_DEFECT | `CATER_EXTERNAL_CATERER_ALLOWED` makes the stated arrangement allowed. No storage or power condition was supplied. The console does not emit a catering proposition projection; confidence: high. |
| HOLD2-005 | primary / technical:enhanced_sound_system | known_conditional | known_no | GOLD_DEFECT | none | `TECH_REQ_AMPLIFIED_SOUND_EXTERNAL` says installed Sonos is not internal amplified-event sound support. Gold was inferred, not supported; confidence: high. |
| HOLD2-007 | primary / technical:other_technical | unknown_internal | known_conditional | GOLD_DEFECT | none | `TECH_REQ_CUSTOM_TECH_CONFIRM` explicitly creates a confirmation path. The runtime has current authority for a conditional response; confidence: high. |
| HOLD2-009 | technical:projection_display | known_yes | known_conditional | GOLD_DEFECT | none | Same current basic-projection confirmation rule as HOLD2-001; confidence: high. |
| HOLD2-011 | technical:projection_display | known_yes | known_conditional | GOLD_DEFECT | none | Same current basic-projection confirmation rule as HOLD2-001; confidence: high. |
| HOLD2-012 | technical:other_technical | unknown_internal | known_conditional | GOLD_DEFECT | none | Same current custom-technical confirmation rule as HOLD2-007; confidence: high. |

The raw artifact counted nine proposition semantic misses because primary and named propositions overlap in HOLD2-001, HOLD2-005, and HOLD2-007. The seven rows above cover every distinct underlying mismatch; all are gold defects, with HOLD2-002 also exposing missing proposition-level evidence in the console/harness.

## Known-No Action Cases

HOLD2-003, HOLD2-004, and HOLD2-012 all preserved their deterministic restrictions. Their internal tasks have separate persisted `reason_entity_reference` values from the restriction blockers:

- HOLD2-003: task was for `capacity_studio_insufficient_information`, not the DJ restriction.
- HOLD2-004: task was for `facilitator_wnc_provided_confirmation`, not the capacity restriction.
- HOLD2-012: task was for `technical_requirements_summary` confirmation, not the capacity restriction.

The raw next-action grader used case-level action types and blocker types only. It could not join a task to the proposition/reasoning projection that created it. These are `HARNESS_DEFECT` findings, not runtime defects.

## Missing-Client Cases

HOLD2-009, HOLD2-010, and HOLD2-011 correctly created the required OpenQuestion and classified as `missing_client_fact`. Every frozen stage has `run_waiting=false`.

`run_scenario` calls `run_inquiry_waiting` only where that flag is true. The waiting runtime creates the follow-up whose `next_action_type` is `REQUEST_CLIENT_INFORMATION` for non-urgent client questions, then reconciliation materializes the action when eligible. Intake and reconciliation alone create the OpenQuestion/blocker but do not form that follow-up action. The action expectations therefore require an unexecuted workflow stage and are `SCENARIO_EXECUTION_DEFECT` findings.

## Action Taxonomy Assessment

- `deterministic_response` is useful, but must be proposition-local and state-aware.
- `internal_confirmation` maps cleanly to a review task only when its reason entity belongs to the proposition.
- `ask_client` is an intent; `request_client_information` is the persisted action created during waiting/follow-up processing. They are not interchangeable at an earlier stage.
- `state_condition_or_confirm` is meaningful only where the relevant proposition’s current rule establishes a confirmation path.

The existing five semantic states are sufficient for these cases. The apparent custom-technical ambiguity is resolved by the explicit current confirmation rule, so no new semantic state is warranted in this adjudication.

## Adjudicated Runtime Metrics

Only proven gold, harness, and scenario-execution defects are excluded. No raw history was rewritten.

| Metric | Adjudicated result |
| --- | ---: |
| Primary semantic accuracy | 9/9 (100.0%) after excluding HOLD2-001, HOLD2-005, HOLD2-007 gold defects |
| Proposition semantic accuracy | 18/18 (100.0%) after excluding the nine gold-derived raw mismatches |
| Next-action accuracy | 4/4 (100.0%) after excluding 2 gold, 3 harness, and 3 scenario-execution misses |
| Remaining runtime defects | 0 |

This is an analytical calculation only. It does not establish a new Holdout pass, alter the original `75%` / `33.3%` raw result, or authorize a rerun.
