# Generalization Evaluation Summary

## Holdout 2 Contract History

The original Holdout 2 evidence remains preserved. The adjudicated v2 run used the
same hosted staging runtime and repaired only the evaluation contract, proposition
attribution, and omitted waiting-stage scenario configuration.

| Evaluation | Contract | Runtime changed? | A+B | D | Critical | Semantic | Next Action |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Original 32 baseline | original | n/a | 75.0% | 8 | 8 | n/a | 96.88% |
| Calibrated 32 | calibrated | yes | report | 0 | 0 | report | report |
| Holdout 1 initial | original | no tuning beforehand | 30.0% | 6 | 9 | 30% | report |
| Holdout 1 final regression | corrected regression | yes | 70.0% | 0 | 0 | 100% | 90% |
| Holdout 2 raw v1 | flawed evaluation contract | no | 100.0% | 0 | 0 | 75.0% (9/12) | 33.3% (4/12) |
| Holdout 2 adjudicated v2 | repaired evaluation contract | **no** | 100.0% | 0 | 0 | 100.0% (12/12 primary; 27/27 propositions) | 100.0% (12/12) |

## Preserved Original Evidence

- Original frozen fixture: `holdout2_scenarios.json`
- Immutable archive: `holdout2_scenarios_original_v1.json`
- Original SHA-256: `a2f99889c36d8853fc2feb5c370e08b4e2171510898dd7a0c0323a72ac2034c8`
- Original hosted run: `holdout2-20260829-120008`
- Original outcome: `HOLDOUT2_FAILED_GENERALIZATION` due to the flawed evaluation contract; its raw result, report, and adjudication record remain source controlled.

## Adjudicated V2 Evidence

- Fixture version: `second-unseen-holdout-adjudicated-v2`
- Hosted run: `holdout2_scenarios_adjudicated_v2-20260829-123037`
- Result: 12/12 A, 0 B/C/D; zero critical failures; zero unsupported assertions; zero proposition-local action failures.
- Semantic accuracy: 12/12 primary evaluations and 27/27 material propositions.
- Action accuracy: 12/12 expected actions, including all three waiting-stage client-information actions.
- Safety: authority 100%, confidentiality 100%, no provider execution, Outlook disabled, and no commercial or price failures.

The three previous over-caution/action false positives were eliminated by
proposition-local provenance grading. Case-level confirmation requirements that
belonged to another proposition no longer invalidate a deterministic known-no
proposition. No runtime behavior was changed.

## Scope And Posture

- Evaluation-only changes were limited to calibration fixtures, harness logic, tests, and documentation.
- No runtime code, database schema, migration, Render configuration, prompt, provider configuration, or deployment changed for this repair.
- All fixtures and runs use synthetic data and contain no secrets.
- `S7_REAL_OUTLOOK_OUTBOUND_STAGING = DEFERRED_EXTERNAL_DEPENDENCY`
