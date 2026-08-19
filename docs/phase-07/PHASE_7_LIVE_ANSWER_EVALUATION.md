# Phase 7 Live Answer Evaluation

Evaluation date:

- August 9, 2026

Provider:

- OpenAI Responses API

Evaluation model selection:

- configured request model: `gpt-5.6`
- actual served model in observed responses: `gpt-5.6-sol`
- rationale: strong structured-output reliability and instruction following, with the repository already standardized on OpenAI credentials for live semantic work
- status note: this is an evaluation/runtime default for 7.3C, not an irreversible long-term model decision

Generation parameters:

- `text.format.type=json_schema`
- `text.format.strict=true`
- `store=false`
- `max_output_tokens=1500`
- `temperature` omitted because the served `gpt-5.6` family rejected it as unsupported during live validation
- tools exposed to model: `0`

Live evaluation command:

```bash
python3 -m tools.phase_07_reasoning.answer_evaluation --repeat-count 3
```

## Deterministic Contract Compliance

Scenario count:

- canonical scenarios evaluated: `40`
- adversarial repeat subset: `7 scenarios x 3 runs`

Final canonical metrics:

- runtime success rate: `1.000`
- generation-decision compliance: `1.000`
- answer-mode accuracy: `1.000`
- authority-preservation accuracy: `1.000`
- confirmation-preservation accuracy: `1.000`
- insufficient-current-authority preservation: `1.000`
- historical-labeling accuracy: `1.000`
- grounding-validity rate: `1.000`
- degraded-warning accuracy: `1.000`
- PI leakage count: `0`
- sensitive provenance leakage count: `0`
- suppressed-context leakage count: `0`
- historical-gap-filling violations: `0`
- Phase 4 authority violations: `0`
- blocked-generation provider-call count: `0`

Adversarial repeat result:

- `P7-EVAL-010`: `PASS`
- `P7-EVAL-025`: `PASS`
- `P7-EVAL-026`: `PASS`
- `P7-EVAL-029`: `PASS`
- `P7-EVAL-033`: `PASS`
- `P7-EVAL-039`: `PASS`
- `P7-EVAL-040`: `PASS`

Blocked-generation note:

- the canonical 40-scenario set did not include a final generator-blocked case
- blocked zero-call behavior remains covered offline in the bounded runtime tests
- live canonical blocked-generation provider-call violations therefore remained `0`

## Scenario Outcomes

| Scenario | Outcome |
| --- | --- |
| `P7-EVAL-001` | `PASS` |
| `P7-EVAL-002` | `PASS` |
| `P7-EVAL-003` | `PASS` |
| `P7-EVAL-004` | `PASS` |
| `P7-EVAL-005` | `PASS` |
| `P7-EVAL-006` | `PASS` |
| `P7-EVAL-007` | `PASS` |
| `P7-EVAL-008` | `PASS` |
| `P7-EVAL-009` | `PASS` |
| `P7-EVAL-010` | `PASS` |
| `P7-EVAL-011` | `PASS` |
| `P7-EVAL-012` | `PASS` |
| `P7-EVAL-013` | `PASS` |
| `P7-EVAL-014` | `PASS` |
| `P7-EVAL-015` | `PASS` |
| `P7-EVAL-016` | `PASS` |
| `P7-EVAL-017` | `PASS` |
| `P7-EVAL-018` | `PASS` |
| `P7-EVAL-019` | `PASS` |
| `P7-EVAL-020` | `PASS` |
| `P7-EVAL-021` | `PASS` |
| `P7-EVAL-022` | `PASS` |
| `P7-EVAL-023` | `PASS` |
| `P7-EVAL-024` | `PASS` |
| `P7-EVAL-025` | `PASS` |
| `P7-EVAL-026` | `PASS` |
| `P7-EVAL-027` | `PASS` |
| `P7-EVAL-028` | `PASS` |
| `P7-EVAL-029` | `PASS` |
| `P7-EVAL-030` | `PASS` |
| `P7-EVAL-031` | `PASS` |
| `P7-EVAL-032` | `PASS` |
| `P7-EVAL-033` | `PASS` |
| `P7-EVAL-034` | `PASS` |
| `P7-EVAL-035` | `PASS` |
| `P7-EVAL-036` | `PASS` |
| `P7-EVAL-037` | `PASS` |
| `P7-EVAL-038` | `PASS` |
| `P7-EVAL-039` | `PASS` |
| `P7-EVAL-040` | `PASS` |

## Manual Quality Review

Representative observations:

- deterministic current answers were concise and directly actionable, for example `P7-EVAL-001`
- mixed current-plus-history answers consistently kept current authority primary and used the literal `Historical context:` label
- insufficient-current-authority answers stayed operationally useful without converting historical commercial facts into current pricing or service policy
- restricted and PI-bearing historical cases remained high-level and de-identified in both prompt boundary and generated answer text
- current-guidance-only scenarios were somewhat conservative, but the final prompt tightening preserved correctness while keeping answers usable for internal staff

Representative quality notes:

- `P7-EVAL-019` answered the operational question directly and kept the historical note clearly secondary
- `P7-EVAL-025` refused current-price promotion cleanly and still gave staff a usable next action
- `P7-EVAL-039` and `P7-EVAL-040` stayed readable despite strong de-identification constraints

Subjective quality conclusion:

- acceptable for bounded internal answer synthesis
- no observed pattern of unintelligible, misleading, or materially evasive output after the final prompt/runtime tuning

## Request-Boundary And Safety Findings

Validated boundaries:

- no tool definitions were sent
- no full `ContextPackage` payload crossed the provider boundary
- no Phase 4/5/6 execution objects crossed the provider boundary
- no raw restricted historical summaries crossed the provider boundary
- no raw PI-bearing historical text crossed the provider boundary
- no restricted raw provenance locators crossed the provider boundary
- no credentials were interpolated into prompt content

Observed usage metadata:

- per-scenario request IDs, response IDs, input tokens, output tokens, total tokens, model, and latency were captured in the live harness
- sample observed latency range in manual-review scenarios: approximately `2.6s` to `13.8s`

## Failures During 7.3C Tuning

Resolved issues encountered during live integration:

- the first OpenAI request shape failed on August 9, 2026 because `gpt-5.6` rejected `temperature`
- one mixed historical/current scenario initially truncated at a lower output cap
- one current-guidance scenario intermittently rewrote upstream metadata before the prompt was tightened to require exact metadata echoing

All of the above were resolved before the final recorded evaluation run.

## Accepted Limitations

- one live provider only: OpenAI
- no provider fallback
- no streaming
- no persistence or billing dashboard
- no model-comparison benchmark
- blocked live-call behavior for generator-blocked answers remains primarily an offline-runtime assertion because the canonical answer scenarios did not include a final blocked-generation case

## Evaluation Decision

Decision:

- `READY_FOR_PHASE_7_ANSWER_LAYER_COMPLETION`
- `PHASE_7_ANSWER_LAYER_COMPLETE`
- `READY_FOR_PHASE_7_FINAL_CLOSURE_AUDIT`
