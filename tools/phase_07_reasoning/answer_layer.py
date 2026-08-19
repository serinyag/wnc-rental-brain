from __future__ import annotations

from .contracts import (
    ANSWER_MODE_AUTHORITATIVE_CURRENT,
    ANSWER_MODE_BLOCKED,
    ANSWER_MODE_CONFIRMATION_REQUIRED,
    ANSWER_MODE_CURRENT_WITH_HISTORICAL_CONTEXT,
    ANSWER_MODE_HISTORICAL_DESCRIPTIVE,
    ANSWER_MODE_INSUFFICIENT_CURRENT_AUTHORITY,
    ANSWER_RESULT_STATUS_BLOCKED,
    ANSWER_RESULT_STATUS_COMPLETED,
    AUTHORITY_OUTCOME_HISTORICAL_PRECEDENT,
    AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
    AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY,
    GENERATION_DECISION_BLOCKED,
    GENERATOR_SAFE_VISIBILITY_DE_IDENTIFIED,
    GENERATOR_SAFE_VISIBILITY_SUPPRESSED,
    PHASE_7_CONTEXT_CONTRACT_VERSION,
    REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
    REASONING_STATE_MANUAL_REVIEW_REQUIRED,
    REASONING_STATE_REQUIRES_CONFIRMATION,
    SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
    AnswerClaimFrame,
    AnswerGenerationInput,
    AnswerResult,
    AnswerValidationResult,
    ContextPackage,
    GeneratorSafeGroundingReference,
    Phase7ContractError,
    authority_tier_for_source_role,
)


ANSWER_VALIDATION_BLOCKED_TEXT_FORBIDDEN = "blocked_answer_text_forbidden"
ANSWER_VALIDATION_BLOCKED_STATUS_REQUIRED = "blocked_status_required"
ANSWER_VALIDATION_CONFIRMATION_FLAG_MISMATCH = "confirmation_flag_mismatch"
ANSWER_VALIDATION_DEGRADED_FLAG_MISMATCH = "degraded_flag_mismatch"
ANSWER_VALIDATION_GENERATION_DECISION_MISMATCH = "generation_decision_mismatch"
ANSWER_VALIDATION_GROUNDING_REFERENCE_NOT_ALLOWED_FOR_CLAIM = "grounding_reference_not_allowed_for_claim"
ANSWER_VALIDATION_GROUNDING_SOURCE_ROLE_MISMATCH = "grounding_source_role_mismatch"
ANSWER_VALIDATION_INSUFFICIENT_AUTHORITY_FLAG_MISMATCH = "insufficient_authority_flag_mismatch"
ANSWER_VALIDATION_MATERIAL_DEGRADATION_FLAG_MISMATCH = "material_degradation_flag_mismatch"
ANSWER_VALIDATION_MISSING_REQUIRED_WARNING_CODES = "missing_required_warning_codes"
ANSWER_VALIDATION_UNKNOWN_CLAIM_ID = "unknown_claim_id"
ANSWER_VALIDATION_UNKNOWN_GROUNDING_REFERENCE = "unknown_grounding_reference"
ANSWER_VALIDATION_UNEXPECTED_BLOCKED_STATUS = "unexpected_blocked_status"
ANSWER_VALIDATION_AUTHORITY_OUTCOME_MISMATCH = "authority_outcome_mismatch"
ANSWER_VALIDATION_ANSWER_MODE_MISMATCH = "answer_mode_mismatch"


def build_answer_generation_input(
    context_package: ContextPackage,
) -> AnswerGenerationInput:
    if context_package.context_contract_version != PHASE_7_CONTEXT_CONTRACT_VERSION:
        raise Phase7ContractError(
            error_category="invalid_value",
            safe_message=(
                "answer generation input requires the current finalized "
                "context_contract_version."
            ),
        )

    generator_safe_context = context_package.generator_safe_context
    if generator_safe_context is None:
        raise Phase7ContractError(
            error_category="missing_required_field",
            safe_message=(
                "answer generation input requires a finalized "
                "generator_safe_context from 7.2G."
            ),
        )

    authority_outcome = context_package.authority_resolution.overall_outcome_classification
    if authority_outcome is None:
        raise Phase7ContractError(
            error_category="missing_required_field",
            safe_message=(
                "answer generation input requires a resolved authority outcome."
            ),
        )

    confirmation_required = any(
        record.reasoning_state in {
            REASONING_STATE_REQUIRES_CONFIRMATION,
            REASONING_STATE_MANUAL_REVIEW_REQUIRED,
        }
        for record in context_package.authority_resolution.unresolved_authority_records
    )
    insufficient_current_authority = (
        authority_outcome == AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY
        or any(
            record.reasoning_state == REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY
            for record in context_package.authority_resolution.unresolved_authority_records
        )
    )

    safe_grounding = (
        ()
        if generator_safe_context.generation_decision == GENERATION_DECISION_BLOCKED
        else generator_safe_context.grounding
    )
    claim_frames = (
        ()
        if generator_safe_context.generation_decision == GENERATION_DECISION_BLOCKED
        else _build_claim_frames(generator_safe_context.grounding, generator_safe_context.projections)
    )
    answer_mode = _determine_answer_mode(
        generation_decision=generator_safe_context.generation_decision,
        authority_outcome=authority_outcome,
        confirmation_required=confirmation_required,
        insufficient_current_authority=insufficient_current_authority,
    )

    return AnswerGenerationInput(
        query_text=context_package.query.query_text,
        query_class=context_package.routing_plan.query_class,
        authority_outcome=authority_outcome,
        answer_mode=answer_mode,
        generation_boundary=generator_safe_context.generation_boundary,
        generation_decision=generator_safe_context.generation_decision,
        effective_confidentiality_level=(
            context_package.confidentiality_state.effective_confidentiality_level
        ),
        de_identification_required=(
            context_package.confidentiality_state.de_identification_required
        ),
        personal_information_status_summary=(
            context_package.confidentiality_state.personal_information_status_summary
        ),
        confirmation_required=confirmation_required,
        insufficient_current_authority=insufficient_current_authority,
        degraded_retrieval_state=context_package.degraded_retrieval_state,
        generator_policy=context_package.generator_policy,
        claim_frames=claim_frames,
        safe_grounding=safe_grounding,
        blocked_reason=generator_safe_context.blocked_reason,
        required_warning_codes=context_package.generator_policy.required_warnings,
        context_contract_version=context_package.context_contract_version,
    )


def answer_generation_may_invoke_model(
    answer_generation_input: AnswerGenerationInput,
) -> bool:
    return answer_generation_input.generation_decision != GENERATION_DECISION_BLOCKED


def validate_answer_result(
    answer_generation_input: AnswerGenerationInput,
    answer_result: AnswerResult,
) -> AnswerValidationResult:
    failures: list[str] = []
    warnings: list[str] = []

    if answer_result.authority_outcome != answer_generation_input.authority_outcome:
        failures.append(ANSWER_VALIDATION_AUTHORITY_OUTCOME_MISMATCH)
    if answer_result.answer_mode != answer_generation_input.answer_mode:
        failures.append(ANSWER_VALIDATION_ANSWER_MODE_MISMATCH)
    if answer_result.generation_decision != answer_generation_input.generation_decision:
        failures.append(ANSWER_VALIDATION_GENERATION_DECISION_MISMATCH)
    if answer_result.confirmation_required != answer_generation_input.confirmation_required:
        failures.append(ANSWER_VALIDATION_CONFIRMATION_FLAG_MISMATCH)
    if (
        answer_result.insufficient_current_authority
        != answer_generation_input.insufficient_current_authority
    ):
        failures.append(ANSWER_VALIDATION_INSUFFICIENT_AUTHORITY_FLAG_MISMATCH)
    if (
        answer_result.degraded_context_present
        != answer_generation_input.degraded_retrieval_state.any_degradation
    ):
        failures.append(ANSWER_VALIDATION_DEGRADED_FLAG_MISMATCH)
    if (
        answer_result.materially_affects_answer_completeness
        != answer_generation_input.degraded_retrieval_state.materially_affects_answer_completeness
    ):
        failures.append(ANSWER_VALIDATION_MATERIAL_DEGRADATION_FLAG_MISMATCH)

    if answer_generation_input.generation_decision == GENERATION_DECISION_BLOCKED:
        if answer_result.status != ANSWER_RESULT_STATUS_BLOCKED:
            failures.append(ANSWER_VALIDATION_BLOCKED_STATUS_REQUIRED)
        if answer_result.answer_text is not None:
            failures.append(ANSWER_VALIDATION_BLOCKED_TEXT_FORBIDDEN)
    elif answer_result.status == ANSWER_RESULT_STATUS_BLOCKED:
        failures.append(ANSWER_VALIDATION_UNEXPECTED_BLOCKED_STATUS)

    required_warning_codes = set(answer_generation_input.required_warning_codes)
    actual_warning_codes = set(answer_result.warning_codes)
    if not required_warning_codes.issubset(actual_warning_codes):
        failures.append(ANSWER_VALIDATION_MISSING_REQUIRED_WARNING_CODES)

    if answer_result.status == ANSWER_RESULT_STATUS_COMPLETED:
        warnings.extend(
            sorted(required_warning_codes.intersection(actual_warning_codes))
        )

    claim_frames_by_id = {
        frame.claim_id: frame for frame in answer_generation_input.claim_frames
    }
    grounding_by_id = {
        reference.reference_id: reference
        for reference in answer_generation_input.safe_grounding
    }
    for grounding_use in answer_result.grounding_uses:
        claim_frame = claim_frames_by_id.get(grounding_use.claim_id)
        if claim_frame is None:
            failures.append(ANSWER_VALIDATION_UNKNOWN_CLAIM_ID)
            continue
        grounding_reference = grounding_by_id.get(grounding_use.reference_id)
        if grounding_reference is None:
            failures.append(ANSWER_VALIDATION_UNKNOWN_GROUNDING_REFERENCE)
            continue
        if grounding_use.reference_id not in claim_frame.allowed_grounding_reference_ids:
            failures.append(
                ANSWER_VALIDATION_GROUNDING_REFERENCE_NOT_ALLOWED_FOR_CLAIM
            )
        if grounding_use.source_layer_role != grounding_reference.source_layer_role:
            failures.append(ANSWER_VALIDATION_GROUNDING_SOURCE_ROLE_MISMATCH)
        if claim_frame.source_layer_role != grounding_reference.source_layer_role:
            failures.append(ANSWER_VALIDATION_GROUNDING_SOURCE_ROLE_MISMATCH)

    return AnswerValidationResult(
        is_valid=not failures,
        failure_codes=tuple(dict.fromkeys(failures)),
        warning_codes=tuple(dict.fromkeys(warnings)),
    )


def _build_claim_frames(
    grounding: tuple[GeneratorSafeGroundingReference, ...],
    projections: tuple,
) -> tuple[AnswerClaimFrame, ...]:
    grounding_by_item_id: dict[str, list[GeneratorSafeGroundingReference]] = {}
    for reference in grounding:
        grounding_by_item_id.setdefault(reference.item_id, []).append(reference)

    claim_frames = []
    visible_index = 0
    for projection in projections:
        if projection.visibility == GENERATOR_SAFE_VISIBILITY_SUPPRESSED:
            continue
        visible_index += 1
        claim_frames.append(
            AnswerClaimFrame(
                claim_id=f"claim:{visible_index}",
                item_id=projection.item_id,
                source_layer_role=projection.source_layer_role,
                authority_tier_code=authority_tier_for_source_role(
                    projection.source_layer_role
                ),
                claim_text=projection.generator_summary_text or "",
                allowed_grounding_reference_ids=tuple(
                    reference.reference_id
                    for reference in grounding_by_item_id.get(projection.item_id, [])
                ),
                required_warning_codes=projection.warnings,
                historical_context_only=(
                    projection.source_layer_role
                    == SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT
                ),
                requires_high_level_only=(
                    projection.visibility == GENERATOR_SAFE_VISIBILITY_DE_IDENTIFIED
                ),
                current_authority_supported=(
                    projection.source_layer_role
                    != SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT
                ),
            )
        )
    return tuple(claim_frames)


def _determine_answer_mode(
    *,
    generation_decision: str,
    authority_outcome: str,
    confirmation_required: bool,
    insufficient_current_authority: bool,
) -> str:
    if generation_decision == GENERATION_DECISION_BLOCKED:
        return ANSWER_MODE_BLOCKED
    if insufficient_current_authority:
        return ANSWER_MODE_INSUFFICIENT_CURRENT_AUTHORITY
    if confirmation_required:
        return ANSWER_MODE_CONFIRMATION_REQUIRED
    if authority_outcome == AUTHORITY_OUTCOME_HISTORICAL_PRECEDENT:
        return ANSWER_MODE_HISTORICAL_DESCRIPTIVE
    if authority_outcome == AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY:
        return ANSWER_MODE_CURRENT_WITH_HISTORICAL_CONTEXT
    return ANSWER_MODE_AUTHORITATIVE_CURRENT


__all__ = [
    "ANSWER_VALIDATION_ANSWER_MODE_MISMATCH",
    "ANSWER_VALIDATION_AUTHORITY_OUTCOME_MISMATCH",
    "ANSWER_VALIDATION_BLOCKED_STATUS_REQUIRED",
    "ANSWER_VALIDATION_BLOCKED_TEXT_FORBIDDEN",
    "ANSWER_VALIDATION_CONFIRMATION_FLAG_MISMATCH",
    "ANSWER_VALIDATION_DEGRADED_FLAG_MISMATCH",
    "ANSWER_VALIDATION_GENERATION_DECISION_MISMATCH",
    "ANSWER_VALIDATION_GROUNDING_REFERENCE_NOT_ALLOWED_FOR_CLAIM",
    "ANSWER_VALIDATION_GROUNDING_SOURCE_ROLE_MISMATCH",
    "ANSWER_VALIDATION_INSUFFICIENT_AUTHORITY_FLAG_MISMATCH",
    "ANSWER_VALIDATION_MATERIAL_DEGRADATION_FLAG_MISMATCH",
    "ANSWER_VALIDATION_MISSING_REQUIRED_WARNING_CODES",
    "ANSWER_VALIDATION_UNKNOWN_CLAIM_ID",
    "ANSWER_VALIDATION_UNKNOWN_GROUNDING_REFERENCE",
    "ANSWER_VALIDATION_UNEXPECTED_BLOCKED_STATUS",
    "answer_generation_may_invoke_model",
    "build_answer_generation_input",
    "validate_answer_result",
]
