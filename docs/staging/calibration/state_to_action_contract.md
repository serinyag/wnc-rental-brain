# State To Action Contract

| Semantic state | Operational posture | Forbidden posture |
| --- | --- | --- |
| `known_yes` | Proceed or respond within governed conditions; no internal blocker | Internal confirmation solely because unrelated evidence is incomplete |
| `known_no` | Communicate the deterministic restriction or supported alternative | Generic internal confirmation that implies approval could make the request allowed |
| `known_conditional` | State the condition and obtain only the fact or review needed to evaluate it | Treating the condition as unconditional support |
| `unknown_internal` | Create an internal confirmation/review blocker; do not ask the client for WNC policy knowledge | Promising capability or asking the client to supply internal authority |
| `missing_client_fact` | Create the specific client OpenQuestion and client-information action | Inventing the fact or substituting an internal authority review |

Approval remains separate from truth resolution. An approval-gated exception is a pending deviation from the governed baseline, not evidence that the baseline is uncertain or already changed.

