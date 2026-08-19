# Phase 7 Answer Layer Architecture

Date:

- August 9, 2026

## Purpose

Phase 7.3A freezes the contract between the completed 7.2G context layer and the future bounded answer generator.

The answer layer exists to synthesize already-resolved, already-sanitized context into user-facing prose without gaining any new authority, retrieval capability, or confidentiality access.

## Boundary With 7.2G

Upstream pipeline:

`Query`
-> `Planner`
-> `Phase 4 / Phase 5 / Phase 6`
-> `Authority Resolution`
-> `Context Safety Finalization`
-> finalized `ContextPackage`

Answer-layer boundary:

`Finalized ContextPackage`
-> `build_answer_generation_input(...)`
-> `generation-decision enforcement`
-> future bounded generator
-> `validate_answer_result(...)`
-> `AnswerResult`

No retrieval, tool choice, or raw layer access exists after `ContextPackage`.

## Answer-Layer Responsibilities

- consume only finalized 7.2G output
- project least-privilege generator-visible input
- preserve authority outcome and unresolved state
- preserve degraded-retrieval warnings
- preserve current-vs-historical distinctions
- preserve confidentiality and PI restrictions
- restrict grounding to generator-safe references only
- validate future structured answer results deterministically before downstream delivery

## Non-Responsibilities

- no independent retrieval
- no Phase 4 direct execution
- no Phase 5 direct execution
- no Phase 6 direct execution
- no database access
- no web lookup
- no RAG
- no tool selection
- no authority resolution
- no contamination resolution
- no confidentiality merge
- no persistence
- no model/provider selection in 7.3A

## Generator-Visible Input Contract

Decision:

- the future generator does **not** receive the full finalized `ContextPackage`
- it receives `AnswerGenerationInput`

Reason:

- `ContextPackage` intentionally retains internal authority context, suppressed projections, raw layer execution detail, internal grounding, and cross-layer audit artifacts
- the generator needs only the minimal safe synthesis surface

Implemented least-privilege input fields:

- `query_text`
- `query_class`
- `authority_outcome`
- `answer_mode`
- `generation_boundary`
- `generation_decision`
- `effective_confidentiality_level`
- `de_identification_required`
- `personal_information_status_summary`
- `confirmation_required`
- `insufficient_current_authority`
- finalized `DegradedRetrievalState`
- finalized `GeneratorPolicy`
- `claim_frames`
- `safe_grounding`
- `blocked_reason`
- `required_warning_codes`
- context/answer contract versions

Explicitly excluded from generator-visible input:

- raw `phase_4_context`
- raw `phase_5_context`
- raw `phase_6_context`
- suppressed projections
- internal grounding provenance
- raw unresolved-authority cross-references
- layer execution internals beyond the already-finalized degraded state
- conflict-resolution internals not required for synthesis

## Claim-Level Authority Handling

Decision:

- mixed-authority answers use lightweight claim frames rather than only a single answer-level label

Contract:

- `AnswerClaimFrame`

Per-frame fields preserve:

- `item_id`
- `source_layer_role`
- `authority_tier_code`
- generator-safe `claim_text`
- allowed grounding IDs for that claim
- claim-local warning codes
- `historical_context_only`
- `requires_high_level_only`
- `current_authority_supported`

Effect:

- historical material remains structurally marked as historical
- mixed P4/P5/P6 answers cannot blur source roles silently
- post-generation validation can reject grounding that crosses claim boundaries

## Generator Permissions

The future bounded generator may:

- synthesize provided safe context
- explain Phase 4 deterministic truth
- summarize Phase 5 governed guidance
- describe Phase 6 precedent as historical only
- compare current authority with historical precedent when the input mode allows it
- express uncertainty, confirmation requirements, insufficiency, and degraded retrieval warnings
- cite only the supplied generator-safe grounding IDs
- improve phrasing, sequencing, and readability

The generator does not gain new factual authority by reasoning.

## Generator Prohibitions

The future bounded generator may not:

- retrieve new information
- call Phase 4, Phase 5, or Phase 6 directly
- query SQL or Supabase
- invoke tools or choose tools
- use web retrieval
- use RAG
- invent deterministic values
- promote historical precedent into current policy
- override Phase 4
- override authority resolution
- override contamination handling
- erase confirmation requirements
- fill missing-current-authority gaps with history
- access suppressed content
- access restricted provenance
- reconstruct PI
- suppress required degraded warnings
- answer substantively when `generation_decision=blocked`

## Answer Modes

Answer modes are semantic modes, not security modes.

Implemented modes:

- `authoritative_current`
- `current_with_historical_context`
- `historical_descriptive`
- `confirmation_required`
- `insufficient_current_authority`
- `blocked`

Deterministic mapping:

1. `generation_decision=blocked` -> `blocked`
2. insufficient current authority present -> `insufficient_current_authority`
3. confirmation/manual review required -> `confirmation_required`
4. authority outcome `HISTORICAL_PRECEDENT` -> `historical_descriptive`
5. authority outcome `MIXED_WITH_CURRENT_PRIORITY` -> `current_with_historical_context`
6. otherwise -> `authoritative_current`

Important design choice:

- degraded retrieval is **not** an `AnswerMode`
- degraded behavior remains explicit through finalized `DegradedRetrievalState` and `required_warning_codes`
- restricted generation is **not** an `AnswerMode`
- restriction/blocking remains explicit through existing 7.2G `generation_decision`

This avoids duplicate enums for concepts already represented upstream.

## Current-Vs-Historical Semantics

- Phase 4 remains controlling current deterministic truth
- Phase 5 may explain current guidance but not override Phase 4
- Phase 6 claim frames always set `historical_context_only=true`
- `insufficient_current_authority` never becomes a current policy answer
- `confirmation_required` cannot be removed by the generator

Canonical preserved behavior:

- historical storage pricing may be described as precedent, not as current price
- historical florals handling may be described as precedent, not as current service availability
- historical ADE handling may be described as precedent, not as current compliance guidance

## Grounding Rules

The future answer generator may use only `safe_grounding` supplied in `AnswerGenerationInput`.

Rules:

- current deterministic claims may cite only safe Phase 4 grounding
- current governed guidance may cite only safe Phase 5 grounding
- historical claims may cite only safe Phase 6 grounding
- claim frames may cite only their own permitted grounding IDs
- internal `GroundingState` is never exposed to the generator

Post-generation validation rejects:

- unknown grounding IDs
- claim IDs not present in the input
- grounding IDs used outside the permitted claim frame
- source-role mismatches

## Generation-Decision Enforcement

Application-side enforcement uses the finalized 7.2G `generation_decision`.

Behavior:

- `allowed` -> generator may be invoked normally with bounded input
- `allowed_with_restrictions` -> generator may be invoked, but must preserve warnings, high-level-only handling, and authority restrictions
- `blocked` -> generator must not receive substantive claim frames or safe grounding and must not be invoked for substantive synthesis

Implemented helper:

- `answer_generation_may_invoke_model(...)`

Blocked inputs are structurally narrowed to:

- no claim frames
- no safe grounding
- explicit `blocked_reason`
- `answer_mode=blocked`

## Prompt Architecture

7.3A does not call a model, but the future prompt architecture is frozen conceptually:

1. immutable system rules
2. authority hierarchy and invariants
3. generator prohibitions
4. answer-mode instruction
5. bounded `AnswerGenerationInput`
6. safe grounding IDs
7. original user query
8. structured `AnswerResult` output shape

Prompt input must not include raw Phase 4/5/6 payloads.

## Answer Result Contract

Future structured output contract:

- `AnswerResult`

Fields:

- `status`
- `answer_mode`
- `authority_outcome`
- `generation_decision`
- `confirmation_required`
- `insufficient_current_authority`
- degraded flags
- optional `answer_text`
- `grounding_uses`
- `warning_codes`
- optional `failure_code`
- `answer_contract_version`

Status semantics:

- `completed`
- `blocked`
- `failed`

This separates generated prose from runtime/audit metadata so downstream consumers do not need to reinterpret authority.

## Deterministic Post-Generation Validation

Implemented validator:

- `validate_answer_result(...)`

Current deterministic checks:

- authority outcome preserved
- answer mode preserved
- generation decision preserved
- confirmation flag preserved
- insufficient-authority flag preserved
- degraded flags preserved
- blocked input cannot return a completed answer
- required warning codes remain present
- only known claim IDs may be referenced
- only known safe grounding IDs may be referenced
- grounding may appear only on permitted claim frames
- grounding source roles must match

Intentionally not attempted in 7.3A:

- full natural-language factual verification
- hallucination scoring
- semantic paraphrase detection

## Failure Behavior

Fail closed when safety or contract integrity is implicated.

Defined failure cases:

- missing finalized `generator_safe_context`
- missing authority outcome
- unexpected `context_contract_version`
- malformed `AnswerGenerationInput`
- malformed `AnswerResult`
- completed answer returned for blocked input
- unknown claim ID
- unknown grounding ID
- grounding/claim source-role mismatch
- required warnings dropped

No failure path triggers new retrieval or upstream reruns from the answer layer.

## Observability Requirements

Future safe audit/logging should capture:

- `context_contract_version`
- `answer_contract_version`
- `authority_outcome`
- `answer_mode`
- `generation_decision`
- degraded-state flags
- required warning codes
- grounding IDs used
- validation pass/failure codes
- generator invocation attempted or skipped
- future provider/model metadata

Do not log suppressed content, raw provenance payloads, or PI-bearing material.

## Security And Confidentiality Constraints

- the generator sees only `AnswerGenerationInput`
- blocked inputs expose no substantive claim frames
- suppressed internal projections never cross the boundary
- raw provenance never crosses the boundary
- PI restoration is structurally disallowed
- historical claims stay structurally historical

## Runtime Sequence

Text architecture:

`Finalized ContextPackage`
-> `Answer Input Builder`
-> `Generation Decision Enforcement`
-> `Future Bounded Generator`
-> `Deterministic Answer Validator`
-> `AnswerResult`

Implemented 7.3B runtime entry point:

- `tools.phase_07_reasoning.answer_generator.generate_bounded_answer(...)`

Implemented provider-neutral request boundary:

- `BoundedAnswerGeneratorRequest`

Implemented runtime result boundary:

- `BoundedAnswerRuntimeResult`

The runtime now performs:

1. input contract acceptance
2. blocked-vs-callable enforcement
3. deterministic bounded request assembly
4. injected generator invocation only when permitted
5. structured response parsing
6. deterministic post-generation validation
7. fail-closed failure result construction

## New Answer-Layer Invariants

- `P7-ANS-001` the generator may consume only finalized generator-safe context projected through `AnswerGenerationInput`
- `P7-ANS-002` the generator performs no retrieval
- `P7-ANS-003` the generator cannot alter upstream authority outcome
- `P7-ANS-004` the generator cannot fill missing current authority with historical precedent
- `P7-ANS-005` historical precedent must remain explicitly historical at claim level
- `P7-ANS-006` the generator cannot erase confirmation requirements
- `P7-ANS-007` only generator-safe grounding may appear in generated answers
- `P7-ANS-008` blocked generation is enforced application-side
- `P7-ANS-009` deterministic answer validation occurs after generation and before downstream delivery
- `P7-ANS-010` answer-generation failure never triggers retrieval or authority fallback

## Runtime Invariants

- `P7-GEN-001` a generator invocation may receive only `AnswerGenerationInput`-derived safe data
- `P7-GEN-002` blocked generation causes zero generator invocations
- `P7-GEN-003` the generator implementation has no retrieval capability
- `P7-GEN-004` the generator cannot change upstream authority state
- `P7-GEN-005` generator grounding is restricted to the supplied generator-safe grounding set
- `P7-GEN-006` malformed or policy-invalid generator output is rejected before delivery
- `P7-GEN-007` generator failure cannot trigger retrieval or authority fallback
- `P7-GEN-008` confirmation and insufficient-authority states survive generation
- `P7-GEN-009` historical claim frames remain explicitly historical through generation
- `P7-GEN-010` only validated `AnswerResult` objects may cross the answer-layer delivery boundary

## Explicit Anti-Patterns

Do not implement:

- LLM-driven retrieval after `ContextPackage`
- prompt-only enforcement without application-side gating
- raw `ContextPackage` delivery to the generator
- citations reconstructed from internal provenance
- historical precedent presented as current policy
- direct SQL or search tools from the answer layer
- agentic answer generation

## Acceptance Criteria

7.3A is complete when:

- the generator boundary is explicit
- least-privilege input is typed
- semantic answer modes are frozen
- generation-decision enforcement remains application-side
- mixed-authority claims preserve source roles
- safe grounding use is typed and validated
- blocked behavior is deterministic
- focused architecture tests pass
- Phase 7 regression remains green

## Next Implementation Boundary

Next allowed step:

- `7.3B — Bounded Answer Generator Implementation`

Still out of scope after 7.3A:

- live model calls
- provider integration
- prompt tuning against a model
- retrieval changes
- agents
- persistence
