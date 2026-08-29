# Holdout 2 Generalization Summary

- status: `HOLDOUT2_FAILED_GENERALIZATION`
- clean run slug: `holdout2-20260829-120008`
- environment: hosted staging; Outlook disabled; Asana configured only; no provider execution

## Threshold Outcome

| Metric | Result | Target | Outcome |
| --- | ---: | ---: | --- |
| A+B | 100.0% | >= 85% | pass |
| Critical failures | 0 | 0 | pass |
| Unsupported assertions | 0 | 0 | pass |
| Wrong-price failures | 0 | 0 | pass |
| Authority success | 100.0% | 100% | pass |
| Confidentiality success | 100.0% | 100% | pass |
| Semantic-state match | 75.0% (9/12) | >= 90% | fail |
| Correct-next-action rate | 33.3% (4/12) | >= 90% | fail |
| Over-caution failures | 1 | 0 | fail |

The clean run completed all twelve frozen scenarios once. The failures are runtime-quality findings for a later remediation cycle, not changes made during this evaluation.
