from __future__ import annotations

from typing import Callable

from .authority_resolver import resolve_authority
from .contracts import (
    CONFIDENTIALITY_LEVEL_CODES,
    CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE,
    CONFIDENTIALITY_LEVEL_EXTERNALLY_SHAREABLE,
    CONFIDENTIALITY_LEVEL_INTERNAL,
    CONFIDENTIALITY_LEVEL_RESTRICTED,
    ContextSafetyConfiguration,
    EXECUTION_STATE_FAILED,
    EXECUTION_STATE_FALLBACK,
    EXECUTION_STATE_NOT_REQUESTED,
    EXECUTION_STATE_UNAVAILABLE,
    GENERATOR_ALLOWED_ACTION_COMPARE,
    GENERATOR_ALLOWED_ACTION_EXPLAIN,
    GENERATOR_ALLOWED_ACTION_EXPRESS_UNCERTAINTY,
    GENERATOR_ALLOWED_ACTION_SYNTHESIZE,
    GENERATOR_FORBIDDEN_ACTION_ERASE_CONFIRMATION_REQUIREMENTS,
    GENERATOR_FORBIDDEN_ACTION_FILL_AUTHORITY_GAPS,
    GENERATOR_FORBIDDEN_ACTION_INDEPENDENT_RETRIEVAL,
    GENERATOR_FORBIDDEN_ACTION_INVENT_DETERMINISTIC_VALUES,
    GENERATOR_FORBIDDEN_ACTION_OVERRIDE_CONFLICTS,
    GENERATOR_FORBIDDEN_ACTION_PROMOTE_PRECEDENT,
    LAYER_ID_PHASE_4,
    LAYER_ID_PHASE_5,
    LAYER_ID_PHASE_6,
    LayerExecutionRecord,
    ContextPackage,
    ConfidentialityState,
    DegradedRetrievalState,
    GeneratorPolicy,
    GroundingReference,
    GroundingState,
    Phase7RuntimeConfiguration,
    QueryContext,
    QueryPlan,
    PERSONAL_INFORMATION_STATUS_NO,
    PERSONAL_INFORMATION_STATUS_UNKNOWN,
    PERSONAL_INFORMATION_STATUS_YES,
    UncertaintyState,
)
from .contamination_gate import detect_contamination_annotations
from .context_safety import finalize_context_safety
from .phase4_adapter import execute_phase4_plan
from .phase5_wrapper import execute_phase5_plan
from .phase6_adapter import execute_phase6_plan
from .query_planner import plan_query


PlannerFunction = Callable[..., QueryPlan]
Phase4Executor = Callable[..., LayerExecutionRecord]
Phase5Executor = Callable[..., LayerExecutionRecord]
Phase6Executor = Callable[..., LayerExecutionRecord]


def build_context_package(
    query_text: str,
    query_context: QueryContext | None = None,
    runtime_configuration: Phase7RuntimeConfiguration | None = None,
    safety_configuration: ContextSafetyConfiguration | None = None,
    finalize_safety: bool = True,
    planner_fn: PlannerFunction | None = None,
    phase4_executor: Phase4Executor | None = None,
    phase5_executor: Phase5Executor | None = None,
    phase6_executor: Phase6Executor | None = None,
) -> ContextPackage:
    config = runtime_configuration or Phase7RuntimeConfiguration()
    context = query_context or QueryContext(query_text=query_text)
    planner = planner_fn or plan_query
    query_plan = planner(query_text, query_context=context, runtime_configuration=config)

    phase4_record = _execute_or_not_requested(
        layer_id=LAYER_ID_PHASE_4,
        required=bool(query_plan.phase_4 and query_plan.phase_4.required),
        executor=phase4_executor or execute_phase4_plan,
        query_plan=query_plan,
        query_context=context,
        runtime_configuration=config,
    )
    phase5_record = _execute_or_not_requested(
        layer_id=LAYER_ID_PHASE_5,
        required=bool(query_plan.phase_5 and query_plan.phase_5.required),
        executor=phase5_executor or execute_phase5_plan,
        query_plan=query_plan,
        query_context=context,
        runtime_configuration=config,
    )
    phase6_record = _execute_or_not_requested(
        layer_id=LAYER_ID_PHASE_6,
        required=bool(query_plan.phase_6 and query_plan.phase_6.required),
        executor=phase6_executor or execute_phase6_plan,
        query_plan=query_plan,
        query_context=context,
        runtime_configuration=config,
    )

    contamination_annotations = detect_contamination_annotations(
        query_plan,
        phase4_record,
        phase5_record,
        phase6_record,
    )
    authority_resolution = resolve_authority(
        query_plan,
        phase4_record,
        phase5_record,
        phase6_record,
        contamination_annotations=contamination_annotations,
    )

    phase4_context = tuple(phase4_record.normalized_items)
    phase5_context = tuple(phase5_record.normalized_items)
    phase6_context = tuple(phase6_record.normalized_items)

    uncertainty_state = _build_uncertainty_state(authority_resolution)
    confidentiality_state = _build_provisional_confidentiality_state(
        phase4_context,
        phase5_context,
        phase6_context,
    )
    degraded_retrieval_state = _build_degraded_retrieval_state(
        query_plan,
        phase4_record,
        phase5_record,
        phase6_record,
    )
    grounding = _build_grounding_state(phase4_context, phase5_context, phase6_context)
    generator_policy = _build_provisional_generator_policy(
        authority_resolution=authority_resolution,
        confidentiality_state=confidentiality_state,
        degraded_retrieval_state=degraded_retrieval_state,
    )

    package = ContextPackage(
        query=context,
        routing_plan=query_plan,
        layer_execution=(phase4_record, phase5_record, phase6_record),
        phase_4_context=phase4_context,
        phase_5_context=phase5_context,
        phase_6_context=phase6_context,
        authority_resolution=authority_resolution,
        uncertainty_state=uncertainty_state,
        confidentiality_state=confidentiality_state,
        degraded_retrieval_state=degraded_retrieval_state,
        grounding=grounding,
        generator_policy=generator_policy,
        generator_safe_context=None,
        context_contract_version=config.contract_version,
    )
    if not finalize_safety:
        return package
    return finalize_context_safety(
        package,
        safety_configuration=safety_configuration,
    )


def _execute_or_not_requested(
    *,
    layer_id: str,
    required: bool,
    executor: Callable[..., LayerExecutionRecord],
    query_plan: QueryPlan,
    query_context: QueryContext,
    runtime_configuration: Phase7RuntimeConfiguration,
) -> LayerExecutionRecord:
    if not required:
        return LayerExecutionRecord(
            layer_id=layer_id,
            requested=False,
            execution_state=EXECUTION_STATE_NOT_REQUESTED,
            reasoning_state=None,
            fallback_reason=None,
            error_category=None,
            safe_error_message=None,
            result_count=0,
            normalized_items=(),
        )
    if layer_id == LAYER_ID_PHASE_4:
        return executor(
            query_plan,
            query_context=query_context,
        )
    return executor(
        query_plan,
        query_context=query_context,
        runtime_configuration=runtime_configuration,
    )


def _build_uncertainty_state(authority_resolution) -> UncertaintyState:
    records = authority_resolution.unresolved_authority_records
    notes: list[str] = []
    if records:
        notes.append("authority_resolution_contains_explicit_unresolved_records")
    return UncertaintyState(
        has_unresolved_authority=bool(records),
        unresolved_records=records,
        notes=tuple(notes),
    )


def _build_provisional_confidentiality_state(*contexts) -> ConfidentialityState:
    items = tuple(item for context in contexts for item in context)
    if not items:
        return ConfidentialityState(
            effective_confidentiality_level=CONFIDENTIALITY_LEVEL_INTERNAL,
            contributing_item_ids=(),
            personal_information_present=False,
            de_identification_required=False,
            generation_allowed=True,
            generation_restriction_reason=None,
            personal_information_status_summary=PERSONAL_INFORMATION_STATUS_NO,
            suppressed_item_ids=(),
            suppression_reasons={},
        )

    rank = {
        CONFIDENTIALITY_LEVEL_EXTERNALLY_SHAREABLE: 0,
        CONFIDENTIALITY_LEVEL_INTERNAL: 1,
        CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE: 2,
        CONFIDENTIALITY_LEVEL_RESTRICTED: 3,
    }
    effective_level = max(
        (
            item.sensitivity.confidentiality_level
            for item in items
            if item.sensitivity.confidentiality_level in CONFIDENTIALITY_LEVEL_CODES
        ),
        key=lambda code: rank[code],
        default=CONFIDENTIALITY_LEVEL_INTERNAL,
    )
    raw_pi_statuses = tuple(
        item.sensitivity.personal_information_status for item in items
    )
    if any(status == PERSONAL_INFORMATION_STATUS_YES for status in raw_pi_statuses):
        pi_status_summary = PERSONAL_INFORMATION_STATUS_YES
    elif any(status == PERSONAL_INFORMATION_STATUS_UNKNOWN for status in raw_pi_statuses):
        pi_status_summary = PERSONAL_INFORMATION_STATUS_UNKNOWN
    else:
        pi_status_summary = PERSONAL_INFORMATION_STATUS_NO
    return ConfidentialityState(
        effective_confidentiality_level=effective_level,
        contributing_item_ids=tuple(item.item_id for item in items),
        personal_information_present=pi_status_summary == PERSONAL_INFORMATION_STATUS_YES,
        de_identification_required=pi_status_summary != PERSONAL_INFORMATION_STATUS_NO,
        generation_allowed=True,
        generation_restriction_reason=None,
        personal_information_status_summary=pi_status_summary,
        suppressed_item_ids=(),
        suppression_reasons={},
    )


def _build_degraded_retrieval_state(
    query_plan: QueryPlan,
    phase4_record: LayerExecutionRecord,
    phase5_record: LayerExecutionRecord,
    phase6_record: LayerExecutionRecord,
) -> DegradedRetrievalState:
    records = (phase4_record, phase5_record, phase6_record)
    affected_layers = tuple(
        record.layer_id
        for record in records
        if record.execution_state in {EXECUTION_STATE_FALLBACK, EXECUTION_STATE_FAILED, EXECUTION_STATE_UNAVAILABLE}
    )
    if not affected_layers:
        return DegradedRetrievalState(
            any_degradation=False,
            materially_affects_answer_completeness=False,
        )

    fallback_reasons = {
        record.layer_id: record.fallback_reason
        for record in records
        if record.fallback_reason is not None
    }
    warnings: list[str] = []
    if phase5_record.execution_state in {EXECUTION_STATE_FAILED, EXECUTION_STATE_UNAVAILABLE}:
        warnings.append("phase_5_current_guidance_unavailable")
    if phase4_record.execution_state in {EXECUTION_STATE_FAILED, EXECUTION_STATE_UNAVAILABLE}:
        warnings.append("phase_4_deterministic_layer_failed")
    if phase6_record.execution_state == EXECUTION_STATE_FALLBACK:
        warnings.append("phase_6_historical_retrieval_fallback")
    if phase5_record.execution_state == EXECUTION_STATE_FALLBACK:
        warnings.append("phase_5_current_guidance_fallback")
    return DegradedRetrievalState(
        any_degradation=True,
        materially_affects_answer_completeness=True,
        affected_layers=affected_layers,
        per_layer_execution_states={record.layer_id: record.execution_state for record in records},
        fallback_reasons=fallback_reasons,
        generator_warnings=tuple(warnings),
    )


def _build_grounding_state(*contexts) -> GroundingState:
    references: list[GroundingReference] = []
    index = 1
    for context in contexts:
        for item in context:
            references.append(
                GroundingReference(
                    reference_id=f"grounding:{index}",
                    item_id=item.item_id,
                    source_layer_role=item.source_layer_role,
                    provenance=item.provenance,
                )
            )
            index += 1
    return GroundingState(references=tuple(references))


def _build_provisional_generator_policy(
    *,
    authority_resolution,
    confidentiality_state: ConfidentialityState,
    degraded_retrieval_state: DegradedRetrievalState,
) -> GeneratorPolicy:
    warnings: list[str] = []
    if any(
        record.reasoning_state == "insufficient_current_authority"
        for record in authority_resolution.unresolved_authority_records
    ):
        warnings.append("current_authority_insufficient")
    if any(
        record.reasoning_state in {"requires_confirmation", "manual_review_required"}
        for record in authority_resolution.unresolved_authority_records
    ):
        warnings.append("confirmation_required")
    if authority_resolution.contamination_annotations:
        warnings.append("historical_value_context_only")
    if any(record.conflict_type_code == "TYPE_F_LIMITED_OR_UNKNOWN_PRECEDENT" for record in authority_resolution.conflict_records):
        warnings.append("limited_precedent")
    if "phase_5_current_guidance_unavailable" in degraded_retrieval_state.generator_warnings:
        warnings.append("current_guidance_unavailable")
    if "phase_4_deterministic_layer_failed" in degraded_retrieval_state.generator_warnings:
        warnings.append("deterministic_layer_failed")
    if "phase_6_historical_retrieval_fallback" in degraded_retrieval_state.generator_warnings:
        warnings.append("historical_retrieval_fallback")
    if "phase_5_current_guidance_fallback" in degraded_retrieval_state.generator_warnings:
        warnings.append("current_guidance_fallback")
    if confidentiality_state.de_identification_required:
        warnings.append("de_identification_required")
    if confidentiality_state.suppressed_item_ids:
        warnings.append("sensitive_detail_suppressed")
    if not confidentiality_state.generation_allowed:
        warnings.append("generation_blocked_by_confidentiality_gate")

    confidentiality_restrictions: list[str] = []
    if confidentiality_state.effective_confidentiality_level in {
        CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE,
        CONFIDENTIALITY_LEVEL_RESTRICTED,
    }:
        confidentiality_restrictions.append(
            f"effective_confidentiality_level:{confidentiality_state.effective_confidentiality_level}"
        )
    if confidentiality_state.suppressed_item_ids:
        confidentiality_restrictions.append("sensitive_detail_suppressed")
    if any(
        "restricted_historical" in reason
        for reason in confidentiality_state.suppression_reasons.values()
    ):
        confidentiality_restrictions.append("historical_context_high_level_only")
    if confidentiality_state.generation_restriction_reason is not None:
        confidentiality_restrictions.append(
            f"generation_block_reason:{confidentiality_state.generation_restriction_reason}"
        )
    personal_information_restrictions: list[str] = []
    if confidentiality_state.personal_information_present:
        personal_information_restrictions.append("personal_information_present")
    if confidentiality_state.de_identification_required:
        personal_information_restrictions.append("de_identify_before_generation")
    if any(
        reason.startswith("pi_bearing")
        for reason in confidentiality_state.suppression_reasons.values()
    ):
        personal_information_restrictions.append("pi_bearing_detail_suppressed")

    return GeneratorPolicy(
        generation_allowed=confidentiality_state.generation_allowed,
        allowed_actions=(
            (
                GENERATOR_ALLOWED_ACTION_SYNTHESIZE,
                GENERATOR_ALLOWED_ACTION_EXPLAIN,
                GENERATOR_ALLOWED_ACTION_COMPARE,
                GENERATOR_ALLOWED_ACTION_EXPRESS_UNCERTAINTY,
            )
            if confidentiality_state.generation_allowed
            else ()
        ),
        forbidden_actions=(
            GENERATOR_FORBIDDEN_ACTION_INDEPENDENT_RETRIEVAL,
            GENERATOR_FORBIDDEN_ACTION_INVENT_DETERMINISTIC_VALUES,
            GENERATOR_FORBIDDEN_ACTION_PROMOTE_PRECEDENT,
            GENERATOR_FORBIDDEN_ACTION_OVERRIDE_CONFLICTS,
            GENERATOR_FORBIDDEN_ACTION_ERASE_CONFIRMATION_REQUIREMENTS,
            GENERATOR_FORBIDDEN_ACTION_FILL_AUTHORITY_GAPS,
        ),
        required_warnings=tuple(dict.fromkeys(warnings)),
        confidentiality_restrictions=tuple(confidentiality_restrictions),
        personal_information_restrictions=tuple(personal_information_restrictions),
    )


__all__ = ["build_context_package"]
