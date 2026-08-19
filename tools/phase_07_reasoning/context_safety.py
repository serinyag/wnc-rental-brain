from __future__ import annotations

from .confidentiality_gate import (
    GENERATION_RESTRICTION_MATERIAL_SOURCE_BLOCK,
    SUPPRESSION_REASON_PI_BEARING,
    SUPPRESSION_REASON_PI_BEARING_RESTRICTED_HISTORICAL,
    SUPPRESSION_REASON_RESTRICTED_HISTORICAL,
    SUPPRESSION_REASON_SOURCE_GENERATION_PROHIBITED,
)
from .contracts import (
    CONFIDENTIALITY_LEVEL_CODES,
    CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE,
    CONFIDENTIALITY_LEVEL_EXTERNALLY_SHAREABLE,
    CONFIDENTIALITY_LEVEL_INTERNAL,
    CONFIDENTIALITY_LEVEL_RESTRICTED,
    CONTAMINATION_ACTION_CONTEXT_ONLY,
    EXECUTION_STATE_FAILED,
    EXECUTION_STATE_FALLBACK,
    EXECUTION_STATE_UNAVAILABLE,
    GENERATION_BOUNDARY_INTERNAL,
    GENERATION_DECISION_ALLOWED,
    GENERATION_DECISION_ALLOWED_WITH_RESTRICTIONS,
    GENERATION_DECISION_BLOCKED,
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
    GENERATOR_SAFE_VISIBILITY_DE_IDENTIFIED,
    GENERATOR_SAFE_VISIBILITY_SUPPRESSED,
    GENERATOR_SAFE_VISIBILITY_VISIBLE,
    LAYER_ID_PHASE_4,
    LAYER_ID_PHASE_5,
    LAYER_ID_PHASE_6,
    PERSONAL_INFORMATION_STATUS_NO,
    PERSONAL_INFORMATION_STATUS_UNKNOWN,
    PERSONAL_INFORMATION_STATUS_YES,
    QUERY_CLASS_PRECEDENT_DISCOVERY,
    SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
    SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
    SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
    ConfidentialityState,
    ContextPackage,
    ContextSafetyConfiguration,
    DegradedRetrievalState,
    GeneratorPolicy,
    GeneratorSafeContext,
    GeneratorSafeGroundingReference,
    GeneratorSafeItemProjection,
    NormalizedResultEnvelope,
    Phase7ContractError,
)


GENERATION_RESTRICTION_CONTEXT_SAFETY_FAILED = "context_safety_validation_failed"
GENERATION_RESTRICTION_MATERIAL_CONTEXT_SUPPRESSED = "material_context_not_safely_projectable"
GENERATION_RESTRICTION_NO_VISIBLE_CONTEXT = "no_generator_visible_context"

PROJECTION_WARNING_HISTORICAL_CONTEXT_ONLY = "historical_value_context_only"
PROJECTION_WARNING_PI_STATUS_UNKNOWN = "pi_status_unknown"
PROJECTION_WARNING_PI_DEIDENTIFIED = "pi_deidentified"

CONFIDENTIALITY_RANK = {
    CONFIDENTIALITY_LEVEL_EXTERNALLY_SHAREABLE: 0,
    CONFIDENTIALITY_LEVEL_INTERNAL: 1,
    CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE: 2,
    CONFIDENTIALITY_LEVEL_RESTRICTED: 3,
}


def finalize_context_safety(
    context_package: ContextPackage,
    safety_configuration: ContextSafetyConfiguration | None = None,
) -> ContextPackage:
    configuration = safety_configuration or ContextSafetyConfiguration(
        generation_boundary=GENERATION_BOUNDARY_INTERNAL
    )
    try:
        items = context_package.phase_4_context + context_package.phase_5_context + context_package.phase_6_context
        material_item_ids = _material_item_ids(context_package)
        contamination_by_item_id = _contamination_by_historical_item_id(context_package)
        limited_precedent_item_ids = _limited_precedent_item_ids(context_package)

        projections = tuple(
            _build_projection(
                item=item,
                is_material=item.item_id in material_item_ids,
                contamination_action=contamination_by_item_id.get(item.item_id),
                limited_precedent=item.item_id in limited_precedent_item_ids,
            )
            for item in items
        )
        confidentiality_state = _build_confidentiality_state(
            items=items,
            projections=projections,
        )
        degraded_retrieval_state = _finalize_degraded_retrieval_state(
            context_package=context_package,
        )
        generator_safe_context = _build_generator_safe_context(
            context_package=context_package,
            configuration=configuration,
            projections=projections,
            confidentiality_state=confidentiality_state,
        )
        if generator_safe_context.generation_decision == GENERATION_DECISION_BLOCKED:
            confidentiality_state = ConfidentialityState(
                effective_confidentiality_level=confidentiality_state.effective_confidentiality_level,
                contributing_item_ids=confidentiality_state.contributing_item_ids,
                personal_information_present=confidentiality_state.personal_information_present,
                de_identification_required=confidentiality_state.de_identification_required,
                generation_allowed=False,
                generation_restriction_reason=generator_safe_context.blocked_reason,
                personal_information_status_summary=confidentiality_state.personal_information_status_summary,
                suppressed_item_ids=confidentiality_state.suppressed_item_ids,
                suppression_reasons=confidentiality_state.suppression_reasons,
            )
        generator_policy = _build_generator_policy(
            context_package=context_package,
            projections=projections,
            confidentiality_state=confidentiality_state,
            degraded_retrieval_state=degraded_retrieval_state,
            generator_safe_context=generator_safe_context,
        )
        return ContextPackage(
            query=context_package.query,
            routing_plan=context_package.routing_plan,
            layer_execution=context_package.layer_execution,
            phase_4_context=context_package.phase_4_context,
            phase_5_context=context_package.phase_5_context,
            phase_6_context=context_package.phase_6_context,
            authority_resolution=context_package.authority_resolution,
            uncertainty_state=context_package.uncertainty_state,
            confidentiality_state=confidentiality_state,
            degraded_retrieval_state=degraded_retrieval_state,
            grounding=context_package.grounding,
            generator_policy=generator_policy,
            generator_safe_context=generator_safe_context,
            context_contract_version=context_package.context_contract_version,
        )
    except Phase7ContractError as exc:
        return _fail_closed_context_package(
            context_package=context_package,
            configuration=configuration,
            blocked_reason=GENERATION_RESTRICTION_CONTEXT_SAFETY_FAILED,
            validation_errors=(exc.safe_message,),
        )
    except Exception as exc:  # pragma: no cover - defensive fail-closed path
        return _fail_closed_context_package(
            context_package=context_package,
            configuration=configuration,
            blocked_reason=GENERATION_RESTRICTION_CONTEXT_SAFETY_FAILED,
            validation_errors=(str(exc),),
        )


def _material_item_ids(context_package: ContextPackage) -> set[str]:
    authority_resolution = context_package.authority_resolution
    item_ids = set(
        authority_resolution.resolved_current_truth_item_ids
        + authority_resolution.current_guidance_item_ids
        + authority_resolution.historical_precedent_item_ids
    )
    if item_ids:
        return item_ids
    return {
        item.item_id
        for item in (
            context_package.phase_4_context
            + context_package.phase_5_context
            + context_package.phase_6_context
        )
    }


def _contamination_by_historical_item_id(
    context_package: ContextPackage,
) -> dict[str, str]:
    contamination_by_item_id: dict[str, str] = {}
    for annotation in context_package.authority_resolution.contamination_annotations:
        for item_id in annotation.implicated_historical_item_ids:
            contamination_by_item_id[item_id] = annotation.action
    return contamination_by_item_id


def _limited_precedent_item_ids(context_package: ContextPackage) -> set[str]:
    limited_item_ids: set[str] = set()
    for conflict in context_package.authority_resolution.conflict_records:
        if conflict.conflict_type_code == "TYPE_F_LIMITED_OR_UNKNOWN_PRECEDENT":
            limited_item_ids.update(conflict.affected_item_ids)
    return limited_item_ids


def _build_projection(
    *,
    item: NormalizedResultEnvelope,
    is_material: bool,
    contamination_action: str | None,
    limited_precedent: bool,
) -> GeneratorSafeItemProjection:
    summary_text = item.summary_text or _fallback_summary_text(item)
    safe_source_codes = _safe_source_codes(item)
    safe_primary_locator = _safe_primary_locator(item)
    fields_removed = ["primary_source_locator", "additional_locators", "native_provenance_payload"]
    fields_deidentified: list[str] = []
    warnings: list[str] = []

    if not item.sensitivity.generation_allowed:
        suppression_reason = (
            item.sensitivity.generation_restriction_reason
            or SUPPRESSION_REASON_SOURCE_GENERATION_PROHIBITED
        )
        return GeneratorSafeItemProjection(
            item_id=item.item_id,
            source_layer_role=item.source_layer_role,
            visibility=GENERATOR_SAFE_VISIBILITY_SUPPRESSED,
            generator_summary_text=None,
            safe_source_codes=safe_source_codes,
            safe_primary_locator=safe_primary_locator,
            fields_removed=tuple(dict.fromkeys(fields_removed + ["summary_text"])),
            fields_deidentified=(),
            warnings=(),
            suppression_reason=suppression_reason,
        )

    needs_deidentified_projection = _needs_deidentified_projection(
        item=item,
        contamination_action=contamination_action,
        limited_precedent=limited_precedent,
    )
    if needs_deidentified_projection:
        if not is_material:
            return GeneratorSafeItemProjection(
                item_id=item.item_id,
                source_layer_role=item.source_layer_role,
                visibility=GENERATOR_SAFE_VISIBILITY_SUPPRESSED,
                generator_summary_text=None,
                safe_source_codes=safe_source_codes,
                safe_primary_locator=safe_primary_locator,
                fields_removed=tuple(dict.fromkeys(fields_removed + ["summary_text"])),
                fields_deidentified=(),
                warnings=(),
                suppression_reason=_suppression_reason_for_item(item),
            )
        fields_deidentified.extend(["summary_text"])
        warnings.append(PROJECTION_WARNING_PI_DEIDENTIFIED)
        if contamination_action == CONTAMINATION_ACTION_CONTEXT_ONLY or item.layer_payload.get(
            "historical_value_only"
        ) is True:
            warnings.append(PROJECTION_WARNING_HISTORICAL_CONTEXT_ONLY)
        if item.sensitivity.personal_information_status == PERSONAL_INFORMATION_STATUS_UNKNOWN:
            warnings.append(PROJECTION_WARNING_PI_STATUS_UNKNOWN)
        return GeneratorSafeItemProjection(
            item_id=item.item_id,
            source_layer_role=item.source_layer_role,
            visibility=GENERATOR_SAFE_VISIBILITY_DE_IDENTIFIED,
            generator_summary_text=_deidentified_summary_text(
                item=item,
                contamination_action=contamination_action,
                limited_precedent=limited_precedent,
            ),
            safe_source_codes=safe_source_codes,
            safe_primary_locator=safe_primary_locator,
            fields_removed=tuple(dict.fromkeys(fields_removed)),
            fields_deidentified=tuple(dict.fromkeys(fields_deidentified)),
            warnings=tuple(dict.fromkeys(warnings)),
            suppression_reason=None,
        )

    if item.sensitivity.personal_information_status == PERSONAL_INFORMATION_STATUS_UNKNOWN:
        warnings.append(PROJECTION_WARNING_PI_STATUS_UNKNOWN)
    if contamination_action == CONTAMINATION_ACTION_CONTEXT_ONLY:
        warnings.append(PROJECTION_WARNING_HISTORICAL_CONTEXT_ONLY)

    return GeneratorSafeItemProjection(
        item_id=item.item_id,
        source_layer_role=item.source_layer_role,
        visibility=GENERATOR_SAFE_VISIBILITY_VISIBLE,
        generator_summary_text=summary_text,
        safe_source_codes=safe_source_codes,
        safe_primary_locator=safe_primary_locator,
        fields_removed=tuple(dict.fromkeys(fields_removed)),
        fields_deidentified=(),
        warnings=tuple(dict.fromkeys(warnings)),
        suppression_reason=None,
    )


def _needs_deidentified_projection(
    *,
    item: NormalizedResultEnvelope,
    contamination_action: str | None,
    limited_precedent: bool,
) -> bool:
    if item.source_layer_role == SOURCE_LAYER_ROLE_DETERMINISTIC_RULE:
        return False
    if item.sensitivity.confidentiality_level == CONFIDENTIALITY_LEVEL_RESTRICTED:
        return True
    if item.sensitivity.personal_information_status in {
        PERSONAL_INFORMATION_STATUS_YES,
        PERSONAL_INFORMATION_STATUS_UNKNOWN,
    }:
        return True
    if item.source_layer_role == SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT and (
        contamination_action == CONTAMINATION_ACTION_CONTEXT_ONLY
        or item.layer_payload.get("historical_value_only") is True
        or limited_precedent
    ):
        return True
    return False


def _suppression_reason_for_item(item: NormalizedResultEnvelope) -> str:
    if not item.sensitivity.generation_allowed:
        return (
            item.sensitivity.generation_restriction_reason
            or SUPPRESSION_REASON_SOURCE_GENERATION_PROHIBITED
        )
    is_restricted = item.sensitivity.confidentiality_level == CONFIDENTIALITY_LEVEL_RESTRICTED
    if item.sensitivity.personal_information_status == PERSONAL_INFORMATION_STATUS_YES and is_restricted:
        return SUPPRESSION_REASON_PI_BEARING_RESTRICTED_HISTORICAL
    if item.sensitivity.personal_information_status == PERSONAL_INFORMATION_STATUS_YES:
        return SUPPRESSION_REASON_PI_BEARING
    if is_restricted:
        return SUPPRESSION_REASON_RESTRICTED_HISTORICAL
    return SUPPRESSION_REASON_PI_BEARING


def _fallback_summary_text(item: NormalizedResultEnvelope) -> str:
    code = item.stable_identity.primary_code or item.item_id
    if item.source_layer_role == SOURCE_LAYER_ROLE_DETERMINISTIC_RULE:
        return f"Current deterministic rule {code} is available."
    if item.source_layer_role == SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE:
        return f"Current governed knowledge item {code} is available."
    return f"Historical precedent {code} is available as context."


def _deidentified_summary_text(
    *,
    item: NormalizedResultEnvelope,
    contamination_action: str | None,
    limited_precedent: bool,
) -> str:
    code = item.stable_identity.primary_code or item.item_id
    if item.source_layer_role == SOURCE_LAYER_ROLE_DETERMINISTIC_RULE:
        return _fallback_summary_text(item)
    if item.source_layer_role == SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE:
        return (
            f"Current governed knowledge item {code} may be used only in high-level "
            "internal form with identifying or source-specific detail removed."
        )

    summary = f"Historical precedent {code} may be referenced only in de-identified, high-level form."
    if contamination_action == CONTAMINATION_ACTION_CONTEXT_ONLY or item.layer_payload.get(
        "historical_value_only"
    ) is True:
        summary += " It is context only and not current authority."
    if limited_precedent or item.layer_payload.get("precedent_availability") == "limited":
        summary += " Precedent strength remains limited."
    if item.sensitivity.personal_information_status in {
        PERSONAL_INFORMATION_STATUS_YES,
        PERSONAL_INFORMATION_STATUS_UNKNOWN,
    }:
        summary += " Identifying details were removed."
    if item.sensitivity.confidentiality_level == CONFIDENTIALITY_LEVEL_RESTRICTED:
        summary += " Restricted case-specific detail was omitted."
    return summary


def _safe_source_codes(item: NormalizedResultEnvelope) -> tuple[str, ...]:
    safe_codes: list[str] = []
    for candidate in (
        item.stable_identity.primary_code,
        item.stable_identity.secondary_code,
        *item.provenance.source_codes,
    ):
        if candidate is None:
            continue
        text = candidate.strip()
        if not text:
            continue
        if any(marker in text for marker in ("/", "\\", "@")):
            continue
        safe_codes.append(text)
    return tuple(dict.fromkeys(safe_codes))


def _safe_primary_locator(item: NormalizedResultEnvelope) -> str | None:
    primary_code = item.stable_identity.primary_code
    secondary_code = item.stable_identity.secondary_code
    if item.source_layer_role == SOURCE_LAYER_ROLE_DETERMINISTIC_RULE:
        return primary_code
    if item.source_layer_role == SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE:
        return primary_code
    if primary_code and secondary_code:
        return f"{primary_code}:{secondary_code}"
    return primary_code or secondary_code


def _build_confidentiality_state(
    *,
    items: tuple[NormalizedResultEnvelope, ...],
    projections: tuple[GeneratorSafeItemProjection, ...],
) -> ConfidentialityState:
    item_by_id = {item.item_id: item for item in items}
    visible_projections = tuple(
        projection
        for projection in projections
        if projection.visibility != GENERATOR_SAFE_VISIBILITY_SUPPRESSED
    )
    suppressed_item_ids = tuple(
        projection.item_id
        for projection in projections
        if projection.visibility == GENERATOR_SAFE_VISIBILITY_SUPPRESSED
    )
    suppression_reasons = {
        projection.item_id: projection.suppression_reason
        for projection in projections
        if projection.visibility == GENERATOR_SAFE_VISIBILITY_SUPPRESSED
        and projection.suppression_reason is not None
    }
    eligible_items = tuple(item_by_id[projection.item_id] for projection in visible_projections)
    effective_confidentiality_items = eligible_items or items
    effective_confidentiality_level = max(
        (
            item.sensitivity.confidentiality_level
            for item in effective_confidentiality_items
            if item.sensitivity.confidentiality_level in CONFIDENTIALITY_LEVEL_CODES
        ),
        key=lambda level: CONFIDENTIALITY_RANK[level],
        default=CONFIDENTIALITY_LEVEL_INTERNAL,
    )

    projection_pi_statuses = tuple(
        _projected_pi_status(item_by_id[projection.item_id], projection)
        for projection in visible_projections
    )
    if any(status == PERSONAL_INFORMATION_STATUS_YES for status in projection_pi_statuses):
        pi_status_summary = PERSONAL_INFORMATION_STATUS_YES
    elif any(status == PERSONAL_INFORMATION_STATUS_UNKNOWN for status in projection_pi_statuses):
        pi_status_summary = PERSONAL_INFORMATION_STATUS_UNKNOWN
    else:
        pi_status_summary = PERSONAL_INFORMATION_STATUS_NO

    de_identification_required = any(
        projection.visibility == GENERATOR_SAFE_VISIBILITY_DE_IDENTIFIED
        for projection in projections
    ) or any(status == PERSONAL_INFORMATION_STATUS_UNKNOWN for status in projection_pi_statuses)

    return ConfidentialityState(
        effective_confidentiality_level=effective_confidentiality_level,
        contributing_item_ids=tuple(item.item_id for item in items),
        personal_information_present=pi_status_summary == PERSONAL_INFORMATION_STATUS_YES,
        de_identification_required=de_identification_required,
        generation_allowed=True,
        generation_restriction_reason=None,
        personal_information_status_summary=pi_status_summary,
        suppressed_item_ids=suppressed_item_ids,
        suppression_reasons=suppression_reasons,
    )


def _projected_pi_status(
    item: NormalizedResultEnvelope,
    projection: GeneratorSafeItemProjection,
) -> str:
    if projection.visibility == GENERATOR_SAFE_VISIBILITY_SUPPRESSED:
        return PERSONAL_INFORMATION_STATUS_NO
    if projection.visibility == GENERATOR_SAFE_VISIBILITY_DE_IDENTIFIED:
        return PERSONAL_INFORMATION_STATUS_NO
    if item.source_layer_role == SOURCE_LAYER_ROLE_DETERMINISTIC_RULE:
        return PERSONAL_INFORMATION_STATUS_NO
    return item.sensitivity.personal_information_status


def _finalize_degraded_retrieval_state(
    *,
    context_package: ContextPackage,
) -> DegradedRetrievalState:
    state = context_package.degraded_retrieval_state
    if not state.any_degradation:
        return state
    materially_affects_answer_completeness = any(
        record.requested
        and record.execution_state in {
            EXECUTION_STATE_FALLBACK,
            EXECUTION_STATE_FAILED,
            EXECUTION_STATE_UNAVAILABLE,
        }
        for record in context_package.layer_execution
    )
    warnings = []
    for warning in state.generator_warnings:
        if warning == "phase_5_current_guidance_fallback":
            warnings.append("current_guidance_retrieval_degraded")
        elif warning == "phase_6_historical_retrieval_fallback":
            warnings.append("historical_retrieval_degraded")
        elif warning == "phase_5_current_guidance_unavailable":
            warnings.append("current_guidance_unavailable")
        elif warning == "phase_4_deterministic_layer_failed":
            warnings.append("deterministic_layer_failed")
        else:
            warnings.append(warning)
    return DegradedRetrievalState(
        any_degradation=state.any_degradation,
        materially_affects_answer_completeness=materially_affects_answer_completeness,
        affected_layers=state.affected_layers,
        per_layer_execution_states=state.per_layer_execution_states,
        fallback_reasons=state.fallback_reasons,
        generator_warnings=tuple(dict.fromkeys(warnings)),
    )


def _build_generator_safe_context(
    *,
    context_package: ContextPackage,
    configuration: ContextSafetyConfiguration,
    projections: tuple[GeneratorSafeItemProjection, ...],
    confidentiality_state: ConfidentialityState,
) -> GeneratorSafeContext:
    visible_projections = tuple(
        projection
        for projection in projections
        if projection.visibility != GENERATOR_SAFE_VISIBILITY_SUPPRESSED
    )
    material_item_ids = _material_item_ids(context_package)
    visible_material_item_ids = {
        projection.item_id for projection in visible_projections
    }.intersection(material_item_ids)
    source_restricted_material_item_ids = {
        projection.item_id
        for projection in projections
        if projection.visibility == GENERATOR_SAFE_VISIBILITY_SUPPRESSED
        and projection.suppression_reason == SUPPRESSION_REASON_SOURCE_GENERATION_PROHIBITED
    }.intersection(material_item_ids)

    blocked_reason = confidentiality_state.generation_restriction_reason
    validation_errors: tuple[str, ...] = ()
    if material_item_ids and material_item_ids.issubset(source_restricted_material_item_ids):
        blocked_reason = GENERATION_RESTRICTION_MATERIAL_SOURCE_BLOCK
    elif not visible_projections and not _package_can_answer_without_visible_projections(
        context_package
    ):
        blocked_reason = (
            blocked_reason
            or GENERATION_RESTRICTION_MATERIAL_CONTEXT_SUPPRESSED
        )

    generation_decision = GENERATION_DECISION_ALLOWED
    if blocked_reason is not None:
        generation_decision = GENERATION_DECISION_BLOCKED
    elif _requires_generation_restrictions(
        context_package=context_package,
        projections=projections,
        confidentiality_state=confidentiality_state,
    ):
        generation_decision = GENERATION_DECISION_ALLOWED_WITH_RESTRICTIONS

    grounding = tuple(
        GeneratorSafeGroundingReference(
            reference_id=f"generator_safe:{projection.item_id}",
            item_id=projection.item_id,
            source_layer_role=projection.source_layer_role,
            source_codes=projection.safe_source_codes,
            safe_locator=projection.safe_primary_locator,
        )
        for projection in visible_projections
    )

    return GeneratorSafeContext(
        generation_boundary=configuration.generation_boundary,
        generation_decision=generation_decision,
        projections=projections,
        grounding=grounding,
        blocked_reason=blocked_reason,
        validation_errors=validation_errors,
    )


def _package_can_answer_without_visible_projections(
    context_package: ContextPackage,
) -> bool:
    if context_package.uncertainty_state.has_unresolved_authority:
        return True
    if context_package.degraded_retrieval_state.any_degradation:
        return True
    return False


def _requires_generation_restrictions(
    *,
    context_package: ContextPackage,
    projections: tuple[GeneratorSafeItemProjection, ...],
    confidentiality_state: ConfidentialityState,
) -> bool:
    if confidentiality_state.suppressed_item_ids:
        return True
    if confidentiality_state.de_identification_required:
        return True
    if confidentiality_state.effective_confidentiality_level in {
        CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE,
        CONFIDENTIALITY_LEVEL_RESTRICTED,
    }:
        return True
    if context_package.degraded_retrieval_state.any_degradation:
        return True
    if context_package.uncertainty_state.has_unresolved_authority:
        return True
    if context_package.authority_resolution.contamination_annotations:
        return True
    if any(
        record.conflict_type_code == "TYPE_F_LIMITED_OR_UNKNOWN_PRECEDENT"
        for record in context_package.authority_resolution.conflict_records
    ):
        return True
    return any(
        projection.visibility == GENERATOR_SAFE_VISIBILITY_DE_IDENTIFIED
        for projection in projections
    )


def _build_generator_policy(
    *,
    context_package: ContextPackage,
    projections: tuple[GeneratorSafeItemProjection, ...],
    confidentiality_state: ConfidentialityState,
    degraded_retrieval_state: DegradedRetrievalState,
    generator_safe_context: GeneratorSafeContext,
) -> GeneratorPolicy:
    warnings: list[str] = []
    if any(
        record.reasoning_state == "insufficient_current_authority"
        for record in context_package.authority_resolution.unresolved_authority_records
    ):
        warnings.append("current_authority_insufficient")
    if any(
        record.reasoning_state in {"requires_confirmation", "manual_review_required"}
        for record in context_package.authority_resolution.unresolved_authority_records
    ):
        warnings.append("confirmation_required")
    if context_package.authority_resolution.contamination_annotations:
        warnings.append("historical_value_context_only")
    if any(
        record.conflict_type_code == "TYPE_F_LIMITED_OR_UNKNOWN_PRECEDENT"
        for record in context_package.authority_resolution.conflict_records
    ):
        warnings.append("limited_precedent")
    warnings.extend(degraded_retrieval_state.generator_warnings)
    if confidentiality_state.effective_confidentiality_level == CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE:
        warnings.append("commercially_sensitive_context")
    if any(
        item_id
        for item_id, reason in confidentiality_state.suppression_reasons.items()
        if "restricted" in reason
    ):
        warnings.append("restricted_context_suppressed")
    if any(
        projection.visibility == GENERATOR_SAFE_VISIBILITY_DE_IDENTIFIED
        for projection in projections
    ):
        warnings.append("pi_deidentified")
    if any(
        projection_warning == PROJECTION_WARNING_PI_STATUS_UNKNOWN
        for projection in projections
        for projection_warning in projection.warnings
    ):
        warnings.append("pi_status_unknown")

    confidentiality_restrictions: list[str] = []
    if confidentiality_state.effective_confidentiality_level in {
        CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE,
        CONFIDENTIALITY_LEVEL_RESTRICTED,
    }:
        confidentiality_restrictions.append(
            f"effective_confidentiality_level:{confidentiality_state.effective_confidentiality_level}"
        )
    if confidentiality_state.suppressed_item_ids:
        confidentiality_restrictions.append("suppressed_generator_visible_items")
    if any(
        projection.visibility == GENERATOR_SAFE_VISIBILITY_DE_IDENTIFIED
        and projection.source_layer_role == SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT
        for projection in projections
    ):
        confidentiality_restrictions.append("historical_context_high_level_only")
    if generator_safe_context.blocked_reason is not None:
        confidentiality_restrictions.append(
            f"generation_block_reason:{generator_safe_context.blocked_reason}"
        )

    personal_information_restrictions: list[str] = []
    if confidentiality_state.de_identification_required:
        personal_information_restrictions.append("de_identify_before_generation")
    if any(
        projection.visibility == GENERATOR_SAFE_VISIBILITY_DE_IDENTIFIED
        for projection in projections
    ):
        personal_information_restrictions.append("pi_deidentified")
    if confidentiality_state.personal_information_status_summary == PERSONAL_INFORMATION_STATUS_UNKNOWN:
        personal_information_restrictions.append("pi_status_unknown")

    generation_allowed = (
        generator_safe_context.generation_decision != GENERATION_DECISION_BLOCKED
    )

    return GeneratorPolicy(
        generation_allowed=generation_allowed,
        allowed_actions=(
            (
                GENERATOR_ALLOWED_ACTION_SYNTHESIZE,
                GENERATOR_ALLOWED_ACTION_EXPLAIN,
                GENERATOR_ALLOWED_ACTION_COMPARE,
                GENERATOR_ALLOWED_ACTION_EXPRESS_UNCERTAINTY,
            )
            if generation_allowed
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
        confidentiality_restrictions=tuple(dict.fromkeys(confidentiality_restrictions)),
        personal_information_restrictions=tuple(
            dict.fromkeys(personal_information_restrictions)
        ),
    )


def _fail_closed_context_package(
    *,
    context_package: ContextPackage,
    configuration: ContextSafetyConfiguration,
    blocked_reason: str,
    validation_errors: tuple[str, ...],
) -> ContextPackage:
    items = context_package.phase_4_context + context_package.phase_5_context + context_package.phase_6_context
    projections = tuple(
        GeneratorSafeItemProjection(
            item_id=item.item_id,
            source_layer_role=item.source_layer_role,
            visibility=GENERATOR_SAFE_VISIBILITY_SUPPRESSED,
            generator_summary_text=None,
            safe_source_codes=_safe_source_codes(item),
            safe_primary_locator=_safe_primary_locator(item),
            fields_removed=("summary_text", "primary_source_locator", "additional_locators", "native_provenance_payload"),
            fields_deidentified=(),
            warnings=(),
            suppression_reason=GENERATION_RESTRICTION_CONTEXT_SAFETY_FAILED,
        )
        for item in items
    )
    confidentiality_state = ConfidentialityState(
        effective_confidentiality_level=max(
            (
                item.sensitivity.confidentiality_level
                for item in items
                if item.sensitivity.confidentiality_level in CONFIDENTIALITY_LEVEL_CODES
            ),
            key=lambda level: CONFIDENTIALITY_RANK[level],
            default=CONFIDENTIALITY_LEVEL_RESTRICTED,
        ),
        contributing_item_ids=tuple(item.item_id for item in items),
        personal_information_present=False,
        de_identification_required=False,
        generation_allowed=False,
        generation_restriction_reason=blocked_reason,
        personal_information_status_summary=PERSONAL_INFORMATION_STATUS_NO,
        suppressed_item_ids=tuple(item.item_id for item in items),
        suppression_reasons={
            item.item_id: GENERATION_RESTRICTION_CONTEXT_SAFETY_FAILED for item in items
        },
    )
    degraded_retrieval_state = DegradedRetrievalState(
        any_degradation=context_package.degraded_retrieval_state.any_degradation,
        materially_affects_answer_completeness=(
            context_package.degraded_retrieval_state.any_degradation
            or context_package.degraded_retrieval_state.materially_affects_answer_completeness
        ),
        affected_layers=context_package.degraded_retrieval_state.affected_layers,
        per_layer_execution_states=context_package.degraded_retrieval_state.per_layer_execution_states,
        fallback_reasons=context_package.degraded_retrieval_state.fallback_reasons,
        generator_warnings=context_package.degraded_retrieval_state.generator_warnings,
    )
    generator_safe_context = GeneratorSafeContext(
        generation_boundary=configuration.generation_boundary,
        generation_decision=GENERATION_DECISION_BLOCKED,
        projections=projections,
        grounding=(),
        blocked_reason=blocked_reason,
        validation_errors=validation_errors,
    )
    generator_policy = GeneratorPolicy(
        generation_allowed=False,
        allowed_actions=(),
        forbidden_actions=(
            GENERATOR_FORBIDDEN_ACTION_INDEPENDENT_RETRIEVAL,
            GENERATOR_FORBIDDEN_ACTION_INVENT_DETERMINISTIC_VALUES,
            GENERATOR_FORBIDDEN_ACTION_PROMOTE_PRECEDENT,
            GENERATOR_FORBIDDEN_ACTION_OVERRIDE_CONFLICTS,
            GENERATOR_FORBIDDEN_ACTION_ERASE_CONFIRMATION_REQUIREMENTS,
            GENERATOR_FORBIDDEN_ACTION_FILL_AUTHORITY_GAPS,
        ),
        required_warnings=("generation_blocked_by_confidentiality_gate",),
        confidentiality_restrictions=(
            f"generation_block_reason:{blocked_reason}",
        ),
        personal_information_restrictions=(),
    )
    return ContextPackage(
        query=context_package.query,
        routing_plan=context_package.routing_plan,
        layer_execution=context_package.layer_execution,
        phase_4_context=context_package.phase_4_context,
        phase_5_context=context_package.phase_5_context,
        phase_6_context=context_package.phase_6_context,
        authority_resolution=context_package.authority_resolution,
        uncertainty_state=context_package.uncertainty_state,
        confidentiality_state=confidentiality_state,
        degraded_retrieval_state=degraded_retrieval_state,
        grounding=context_package.grounding,
        generator_policy=generator_policy,
        generator_safe_context=generator_safe_context,
        context_contract_version=context_package.context_contract_version,
    )


__all__ = [
    "GENERATION_RESTRICTION_CONTEXT_SAFETY_FAILED",
    "GENERATION_RESTRICTION_MATERIAL_CONTEXT_SUPPRESSED",
    "GENERATION_RESTRICTION_NO_VISIBLE_CONTEXT",
    "finalize_context_safety",
]
