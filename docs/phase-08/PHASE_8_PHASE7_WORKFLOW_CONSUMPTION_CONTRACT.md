# Phase 8 Phase 7 Workflow Consumption Contract

Date:

- August 9, 2026

Status:

- `PHASE_8_0B_PHASE7_CONTRACT_FROZEN`

## Purpose

Freeze the machine boundary between Phase 7 reasoning outputs and Phase 8 workflow execution architecture.

This document defines:

- which Phase 7 structures Phase 8 may consume
- how those structures may influence workflow evaluation
- what Phase 8 must never infer from Phase 7
- what minimal reasoning provenance may be persisted for audit

This contract is architecture only.

## Contract Position

Phase 8 consumes structured Phase 7 outputs.

Phase 8 does not consume freeform model prose as workflow truth.

The binding architectural rule is:

```text
structured Phase 7 output may influence workflow state evaluation
freeform generated wording may not define workflow truth
```

## Contracted Inputs

### Primary Input

Primary workflow input from Phase 7:

- `ContextPackage`

Expected fields of interest:

- `query`
- `routing_plan`
- `layer_execution`
- `phase_4_context`
- `phase_5_context`
- `phase_6_context`
- `authority_resolution`
- `uncertainty_state`
- `confidentiality_state`
- `degraded_retrieval_state`
- `grounding`
- `generator_policy`
- `generator_safe_context`
- `context_contract_version`

### Secondary Inputs

Allowed secondary Phase 7 structures:

- `AnswerGenerationInput`
- `AnswerResult`

These secondary structures are allowed only for:

- human-facing answer or draft packaging
- audit context
- delivery traceability

They are not canonical workflow truth sources.

## Workflow-Relevant Semantics By Phase 7 Structure

### `authority_resolution`

This is the most workflow-critical Phase 7 structure.

Phase 8 may use it to determine:

- whether current authority exists
- whether only current guidance exists
- whether only historical precedent exists
- whether unresolved authority should create a blocker
- whether human confirmation is required

Workflow-safe mappings:

| Phase 7 signal | Phase 8 workflow meaning |
| --- | --- |
| `DETERMINISTIC_CURRENT` | Current authoritative truth exists and may support deterministic workflow evaluation. |
| `CURRENT_GUIDANCE` | Governed current guidance exists; may inform requirement detection or communication framing, but not silent deterministic policy claims beyond the guidance's scope. |
| `HISTORICAL_PRECEDENT` | Historical-only context may inform warnings or operator context, not workflow policy. |
| `MIXED_WITH_CURRENT_PRIORITY` | Current authority remains primary; historical precedent may be retained only as context. |
| `INSUFFICIENT_CURRENT_AUTHORITY` | Workflow must fail closed, create blocker, or require review rather than invent certainty. |
| `REQUIRES_CONFIRMATION` | Workflow must create a confirmation or approval path before committing consequential truth. |

### `resolved_current_truth_item_ids`

These item IDs may support:

- deterministic guard evaluation
- case-decision baseline reference
- requirement evidence
- audit traceability

They do not replace canonical case records.

### `current_guidance_item_ids`

These IDs may support:

- requirement detection
- guidance-backed operator context
- draft wording boundaries

They do not silently become hard deterministic case truth outside their governed scope.

### `historical_precedent_item_ids`

These IDs may support:

- operator awareness
- similarity review
- risk or exception context

They may not support:

- automatic pricing
- automatic eligibility
- automatic access policy
- automatic compliance resolution
- automatic staffing truth

### `conflict_records`

Conflict records must not be flattened away.

Workflow treatment:

- surface the conflict
- create blocker, review requirement, or confirmation path as appropriate
- preserve authority provenance

### `contamination_annotations`

Contamination annotations are safety signals.

Workflow treatment:

- do not use contaminated historical context to fill current truth
- preserve annotation for audit where operationally relevant
- create blocker or warning when the contamination affects a decision-critical scope

### `unresolved_authority_records`

These are direct inputs to workflow safety.

They may trigger:

- blocker creation
- approval request creation
- manual review requirement
- operator warning

They may not be silently ignored for consequential workflow branches.

### `uncertainty_state`

Phase 8 may use uncertainty to determine:

- whether automation is allowed
- whether human review is required
- whether a proposed change should stay provisional

Uncertainty may influence posture.

Uncertainty may not invent case truth.

### `confidentiality_state`

Phase 8 may use confidentiality posture to determine:

- whether an action payload must be restricted
- whether an external message draft may include certain fields
- whether internal-only handling is required

Confidentiality posture constrains communication and projection behavior.

It does not itself define lifecycle state.

### `degraded_retrieval_state`

Phase 8 may use degraded retrieval posture to determine:

- whether automation should pause
- whether a human warning is required
- whether a workflow decision should avoid consequential commitment

If degraded retrieval materially affects completeness, the workflow should bias toward review rather than commit unsupported truth.

### `grounding`

Grounding references may support:

- audit
- operator review
- explanation traces
- case-decision or blocker evidence links

The workflow should preserve minimal structured grounding, not whole freeform reasoning payloads.

### `generator_policy`

`generator_policy` constrains:

- what drafting actions are allowed
- what warnings are required
- confidentiality restrictions
- PI restrictions

It is especially relevant for:

- client communication drafting
- internal summary drafting
- artifact projection wording

It does not decide lifecycle transitions.

### `generator_safe_context`

This may be used only for:

- safe drafting
- safe answer presentation
- human-facing structured output packaging

It is not a canonical workflow-truth store.

## Allowed Phase 8 Consumption Patterns

### Pattern 1: Workflow Evaluation Support

Use `ContextPackage` to support:

- materiality or feasibility review
- requirement discovery
- blocker detection
- approval posture selection
- change-impact review

### Pattern 2: Operator Review Context

Use structured Phase 7 outputs to show:

- authority outcome
- unresolved authority
- current grounding references
- warnings and contamination annotations

### Pattern 3: Drafting Constraints

Use `generator_policy`, `generator_safe_context`, and relevant warnings to constrain:

- outbound client-message drafts
- proposal explanation drafts
- internal summaries

### Pattern 4: Audit Snapshotting

Persist minimal workflow-relevant reasoning snapshot data such as:

- authority outcome classification
- relevant item IDs
- warning codes
- degraded retrieval posture
- limited grounding references

## Prohibited Consumption Patterns

Phase 8 must not:

- parse `answer_text` and treat it as workflow truth
- infer lifecycle state from generated prose
- infer approval satisfaction from wording alone
- promote historical precedent into current policy automatically
- persist the entire `ContextPackage` as case truth
- hide authority conflicts by flattening them into a single optimistic answer
- treat a drafted communication as evidence that a requirement is satisfied

## `AnswerGenerationInput` Boundary

`AnswerGenerationInput` is allowed to influence:

- how a human-facing explanation or message is framed
- what warnings must accompany the output
- whether degraded-context messaging is required

It must not be used as the authoritative source for:

- lifecycle transition
- case truth mutation
- approval release

## `AnswerResult` Boundary

`AnswerResult` may be stored or linked for:

- delivery audit
- explanation traceability
- operator review of what was shown or drafted

Useful fields include:

- `status`
- `answer_mode`
- `authority_outcome`
- `generation_decision`
- `confirmation_required`
- `insufficient_current_authority`
- `degraded_context_present`
- `materially_affects_answer_completeness`
- `warning_codes`
- `failure_code`

`answer_text` itself is not workflow truth.

## Suggested Persistence Boundary

Recommended persistence from Phase 7 into workflow records:

- authority outcome classification
- conflict or contamination references where material
- unresolved-authority indicators
- relevant grounding item IDs
- required warning codes
- degraded retrieval posture when consequential
- confidentiality or PI restriction flags when consequential

Avoid persisting:

- whole prompt payloads
- whole model drafts
- entire safe-context blobs unless separately justified for auditing

## Future Projection Requirement

Phase 8 should eventually define a dedicated workflow-oriented projection from Phase 7 rather than overloading answer-generation shapes.

Recommended future concept:

- `WorkflowReasoningProjection`

Candidate fields:

- `projection_id`
- `rental_case_id`
- `reasoning_purpose`
- `authority_outcome_classification`
- `resolved_current_truth_item_ids`
- `current_guidance_item_ids`
- `historical_precedent_item_ids`
- `conflict_codes`
- `contamination_codes`
- `unresolved_authority_codes`
- `warning_codes`
- `degraded_retrieval_summary`
- `grounding_references`
- `phase7_contract_version`

This future projection is not required to freeze 8.0B architecture, but it is the preferred foundation for implementation.

## Contract Versioning

Phase 8 should preserve:

- the received `context_contract_version`
- the Phase 8 workflow-consumption-contract version

Recommended Phase 8 consumption contract label:

- `phase8_phase7_workflow_consumption_v1`

## Frozen Conclusion

The Phase 7 to Phase 8 contract is now frozen as:

- structured `ContextPackage`-first consumption
- limited audit-only use of `AnswerGenerationInput` and `AnswerResult`
- no freeform answer-prose authority
- minimal persisted reasoning provenance
- future preference for a dedicated `WorkflowReasoningProjection`

This is the authoritative machine boundary for workflow foundation implementation.
