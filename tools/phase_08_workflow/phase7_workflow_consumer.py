from __future__ import annotations

import hashlib
import json
from typing import Any

from tools.phase_07_reasoning.contracts import (
    AUTHORITY_OUTCOME_CURRENT_GUIDANCE,
    AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
    AUTHORITY_OUTCOME_HISTORICAL_PRECEDENT,
    AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
    AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY,
    AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION,
    ContextPackage,
    DegradedRetrievalState,
    GroundingReference,
    PHASE_7_CONTEXT_CONTRACT_VERSION,
    SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
    UnresolvedAuthorityRecord,
)

from .contracts import (
    PHASE_7_REASONING_STATE_CURRENT_STATUS_UNKNOWN,
    PHASE_7_REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
    PHASE_7_REASONING_STATE_INSUFFICIENT_INFORMATION,
    PHASE_7_REASONING_STATE_MANUAL_REVIEW_REQUIRED,
    PHASE_7_REASONING_STATE_NO_APPLICABLE_RULE,
    PHASE_7_REASONING_STATE_REQUIRES_CONFIRMATION,
    PHASE_7_REASONING_STATE_RESOLVED,
    PHASE_8_PHASE7_WORKFLOW_CONSUMPTION_CONTRACT_VERSION,
    REASONING_PURPOSE_CODES,
    WORKFLOW_REASONING_FRESHNESS_CURRENT,
    WORKFLOW_REASONING_FRESHNESS_STALE,
    WORKFLOW_REASONING_FRESHNESS_SUPERSEDED,
    WORKFLOW_REASONING_POSTURE_BLOCKED_FOR_CURRENT_DECISION,
    WORKFLOW_REASONING_POSTURE_GUIDANCE_ONLY,
    WORKFLOW_REASONING_POSTURE_HISTORICAL_CONTEXT_ONLY,
    WORKFLOW_REASONING_POSTURE_REVIEW_REQUIRED,
    WORKFLOW_REASONING_POSTURE_SAFE_FOR_DETERMINISTIC_USE,
    WorkflowReasoningProjection,
)
from .lifecycle_repository import current_timestamp
from .phase7_consumption_repository import (
    Phase7ConsumptionCaseSnapshot,
    Phase7ConsumptionRepositoryProtocol,
)
from .phase7_consumption_types import (
    PHASE7_CONSUMPTION_FAILURE_AUTHORITY_RESOLUTION_MISSING,
    PHASE7_CONSUMPTION_FAILURE_CASE_NOT_FOUND,
    PHASE7_CONSUMPTION_FAILURE_INVALID_CONTEXT_PACKAGE,
    PHASE7_CONSUMPTION_FAILURE_INVALID_GROUNDING,
    PHASE7_CONSUMPTION_FAILURE_INVALID_LAYER_IDENTITY,
    PHASE7_CONSUMPTION_FAILURE_PERSISTENCE_FAILURE,
    PHASE7_CONSUMPTION_FAILURE_STALE_CASE_REVISION,
    PHASE7_CONSUMPTION_FAILURE_UNSUPPORTED_PHASE7_CONTRACT,
    PHASE7_CONSUMPTION_STATUS_FAILED,
    PHASE7_CONSUMPTION_STATUS_CONSUMED,
    PHASE7_CONSUMPTION_STATUS_DUPLICATE,
    Phase7ConsumptionResult,
    WorkflowReasoningEffect,
    WorkflowReasoningPosture,
    WORKFLOW_REASONING_EFFECT_CONFIRMATION_REQUIRED,
    WORKFLOW_REASONING_EFFECT_CONFLICT_PRESENT,
    WORKFLOW_REASONING_EFFECT_CONTAMINATION_WARNING,
    WORKFLOW_REASONING_EFFECT_CURRENT_AUTHORITY_MISSING,
    WORKFLOW_REASONING_EFFECT_CURRENT_GUIDANCE_AVAILABLE,
    WORKFLOW_REASONING_EFFECT_CURRENT_TRUTH_AVAILABLE,
    WORKFLOW_REASONING_EFFECT_DEGRADED_WARNING,
    WORKFLOW_REASONING_EFFECT_DETERMINISTIC_RESTRICTION,
    WORKFLOW_REASONING_EFFECT_HISTORICAL_CONTEXT_AVAILABLE,
    WORKFLOW_REASONING_EFFECT_REQUIREMENT_CANDIDATE,
    WORKFLOW_REASONING_EFFECT_REVIEW_REQUIRED,
    WORKFLOW_SEMANTIC_STATE_KNOWN_CONDITIONAL,
    WORKFLOW_SEMANTIC_STATE_KNOWN_NO,
    WORKFLOW_SEMANTIC_STATE_KNOWN_YES,
    WORKFLOW_SEMANTIC_STATE_UNKNOWN_INTERNAL,
    projection_semantic_state_code,
)
from .validation import Phase8ContractError, ensure_non_negative_int, ensure_positive_int


_REASONING_PRIORITY = {
    PHASE_7_REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY: 6,
    PHASE_7_REASONING_STATE_REQUIRES_CONFIRMATION: 5,
    PHASE_7_REASONING_STATE_MANUAL_REVIEW_REQUIRED: 4,
    PHASE_7_REASONING_STATE_CURRENT_STATUS_UNKNOWN: 3,
    PHASE_7_REASONING_STATE_NO_APPLICABLE_RULE: 2,
    PHASE_7_REASONING_STATE_INSUFFICIENT_INFORMATION: 1,
    PHASE_7_REASONING_STATE_RESOLVED: 0,
}


def consume_phase7_context(
    *,
    rental_case_id: int,
    expected_case_revision: int,
    reasoning_purpose: str,
    context_package: ContextPackage,
    repository: Phase7ConsumptionRepositoryProtocol,
) -> Phase7ConsumptionResult:
    ensure_positive_int("rental_case_id", rental_case_id)
    ensure_non_negative_int("expected_case_revision", expected_case_revision)
    if reasoning_purpose not in REASONING_PURPOSE_CODES:
        raise Phase8ContractError(
            error_category="invalid_value",
            safe_message="reasoning_purpose must be a supported workflow reasoning purpose.",
        )

    validation_failure = _validate_context_package(context_package)
    if validation_failure is not None:
        return Phase7ConsumptionResult(
            status=PHASE7_CONSUMPTION_STATUS_FAILED,
            projection_freshness_status=WORKFLOW_REASONING_FRESHNESS_STALE,
            failure_codes=(validation_failure,),
        )

    snapshot = repository.load_case_snapshot(rental_case_id)
    if snapshot is None:
        return Phase7ConsumptionResult(
            status=PHASE7_CONSUMPTION_STATUS_FAILED,
            projection_freshness_status=WORKFLOW_REASONING_FRESHNESS_STALE,
            failure_codes=(PHASE7_CONSUMPTION_FAILURE_CASE_NOT_FOUND,),
        )
    if snapshot.rental_case.case_revision != expected_case_revision:
        return Phase7ConsumptionResult(
            status=PHASE7_CONSUMPTION_STATUS_FAILED,
            projection_freshness_status=WORKFLOW_REASONING_FRESHNESS_STALE,
            failure_codes=(PHASE7_CONSUMPTION_FAILURE_STALE_CASE_REVISION,),
        )

    authority_outcome = context_package.authority_resolution.overall_outcome_classification
    if authority_outcome is None:
        return Phase7ConsumptionResult(
            status=PHASE7_CONSUMPTION_STATUS_FAILED,
            projection_freshness_status=WORKFLOW_REASONING_FRESHNESS_STALE,
            failure_codes=(PHASE7_CONSUMPTION_FAILURE_AUTHORITY_RESOLUTION_MISSING,),
        )

    reasoning_state_code = _derive_reasoning_state_code(context_package)
    posture = _derive_workflow_posture(context_package, authority_outcome, reasoning_state_code)
    semantic_state_code = _derive_semantic_state_code(context_package)
    identity_key = _projection_identity_key(
        rental_case_id=rental_case_id,
        source_case_revision=expected_case_revision,
        reasoning_purpose=reasoning_purpose,
        context_package=context_package,
        reasoning_state_code=reasoning_state_code,
        posture=posture,
    )

    existing = repository.get_projection_by_identity(
        rental_case_id=rental_case_id,
        projection_identity_key=identity_key,
    )
    if existing is not None:
        return Phase7ConsumptionResult(
            status=PHASE7_CONSUMPTION_STATUS_DUPLICATE,
            projection_freshness_status=_projection_freshness_status(snapshot, existing),
            projection=existing,
            posture=_posture_from_projection(existing),
            workflow_effects=_derive_workflow_effects(existing),
            duplicate_projection=True,
            failure_codes=(),
        )

    projection = WorkflowReasoningProjection(
        reasoning_projection_id=1,
        rental_case_id=rental_case_id,
        reasoning_purpose=reasoning_purpose,
        phase_7_context_contract_version=context_package.context_contract_version,
        phase_8_workflow_contract_version=PHASE_8_PHASE7_WORKFLOW_CONSUMPTION_CONTRACT_VERSION,
        source_case_revision=expected_case_revision,
        authority_outcome_classification=authority_outcome,
        degraded_retrieval_summary=_degraded_summary(
            context_package.degraded_retrieval_state,
            semantic_state_code=semantic_state_code,
        ),
        created_at=current_timestamp(),
        projection_identity_key=identity_key,
        reasoning_state_code=reasoning_state_code,
        workflow_posture=posture.posture_code,
        effective_confidentiality_level=context_package.confidentiality_state.effective_confidentiality_level,
        de_identification_required=context_package.confidentiality_state.de_identification_required,
        personal_information_present=context_package.confidentiality_state.personal_information_present,
        materially_affects_completeness=context_package.degraded_retrieval_state.materially_affects_answer_completeness,
        relevant_current_truth_item_ids=context_package.authority_resolution.resolved_current_truth_item_ids,
        relevant_guidance_item_ids=context_package.authority_resolution.current_guidance_item_ids,
        relevant_historical_item_ids=context_package.authority_resolution.historical_precedent_item_ids,
        conflict_codes=tuple(
            record.conflict_type_code
            for record in context_package.authority_resolution.conflict_records
        ),
        contamination_codes=tuple(
            annotation.forbidden_inference_type
            for annotation in context_package.authority_resolution.contamination_annotations
        ),
        unresolved_authority_codes=tuple(
            _unresolved_code(record)
            for record in context_package.authority_resolution.unresolved_authority_records
        ),
        warning_codes=_warning_codes(context_package),
        grounding_reference_keys=tuple(
            reference.reference_id for reference in context_package.grounding.references
        ),
    )
    try:
        persisted = repository.create_reasoning_projection(projection)
    except Exception as error:
        if isinstance(error, Phase8ContractError):
            raise
        return Phase7ConsumptionResult(
            status=PHASE7_CONSUMPTION_STATUS_FAILED,
            projection_freshness_status=WORKFLOW_REASONING_FRESHNESS_STALE,
            failure_codes=(PHASE7_CONSUMPTION_FAILURE_PERSISTENCE_FAILURE,),
        )

    return Phase7ConsumptionResult(
        status=PHASE7_CONSUMPTION_STATUS_CONSUMED,
        projection_freshness_status=_projection_freshness_status(snapshot, persisted),
        projection=persisted,
        posture=posture,
        workflow_effects=_derive_workflow_effects(persisted),
        duplicate_projection=False,
        failure_codes=(),
    )


def derive_workflow_effects(
    projection: WorkflowReasoningProjection,
) -> tuple[WorkflowReasoningEffect, ...]:
    return _derive_workflow_effects(projection)


def _validate_context_package(context_package: ContextPackage | object) -> str | None:
    if not isinstance(context_package, ContextPackage):
        return PHASE7_CONSUMPTION_FAILURE_INVALID_CONTEXT_PACKAGE
    if context_package.context_contract_version != PHASE_7_CONTEXT_CONTRACT_VERSION:
        return PHASE7_CONSUMPTION_FAILURE_UNSUPPORTED_PHASE7_CONTRACT
    if context_package.authority_resolution.overall_outcome_classification is None:
        return PHASE7_CONSUMPTION_FAILURE_AUTHORITY_RESOLUTION_MISSING
    items_by_id = {
        item.item_id: item
        for item in (
            context_package.phase_4_context
            + context_package.phase_5_context
            + context_package.phase_6_context
        )
    }
    for item_id in context_package.authority_resolution.resolved_current_truth_item_ids:
        item = items_by_id.get(item_id)
        if item is None or item.source_layer_role == SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT:
            return PHASE7_CONSUMPTION_FAILURE_INVALID_LAYER_IDENTITY
    for item_id in context_package.authority_resolution.current_guidance_item_ids:
        item = items_by_id.get(item_id)
        if item is None or item.source_layer_role == SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT:
            return PHASE7_CONSUMPTION_FAILURE_INVALID_LAYER_IDENTITY
    for item_id in context_package.authority_resolution.historical_precedent_item_ids:
        item = items_by_id.get(item_id)
        if item is None or item.source_layer_role != SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT:
            return PHASE7_CONSUMPTION_FAILURE_INVALID_LAYER_IDENTITY
    for reference in context_package.grounding.references:
        if not isinstance(reference, GroundingReference):
            return PHASE7_CONSUMPTION_FAILURE_INVALID_GROUNDING
        item = items_by_id.get(reference.item_id)
        if item is None or item.source_layer_role != reference.source_layer_role:
            return PHASE7_CONSUMPTION_FAILURE_INVALID_GROUNDING
    return None


def _derive_reasoning_state_code(context_package: ContextPackage) -> str:
    candidates: list[str] = []
    candidates.extend(
        record.reasoning_state
        for record in context_package.layer_execution
        if record.reasoning_state is not None
    )
    candidates.extend(
        item.reasoning_state
        for item in (
            context_package.phase_4_context
            + context_package.phase_5_context
            + context_package.phase_6_context
        )
        if item.reasoning_state is not None
    )
    candidates.extend(
        record.reasoning_state
        for record in context_package.authority_resolution.unresolved_authority_records
    )
    if not candidates and not context_package.uncertainty_state.has_unresolved_authority:
        return PHASE_7_REASONING_STATE_RESOLVED
    if not candidates:
        return PHASE_7_REASONING_STATE_MANUAL_REVIEW_REQUIRED
    recognized_candidates = [
        code for code in candidates if code in _REASONING_PRIORITY
    ]
    if not recognized_candidates:
        return PHASE_7_REASONING_STATE_MANUAL_REVIEW_REQUIRED
    return max(recognized_candidates, key=lambda code: _REASONING_PRIORITY[code])


def _derive_semantic_state_code(context_package: ContextPackage) -> str:
    candidates = [
        semantic_state
        for item in _authoritative_items(context_package)
        if (semantic_state := _semantic_state_from_item(item)) is not None
    ]
    if candidates:
        return _dominant_semantic_state(candidates)

    unresolved = context_package.authority_resolution.unresolved_authority_records
    if any(
        record.reasoning_state == PHASE_7_REASONING_STATE_REQUIRES_CONFIRMATION
        for record in unresolved
    ):
        return WORKFLOW_SEMANTIC_STATE_KNOWN_CONDITIONAL
    if unresolved or context_package.authority_resolution.overall_outcome_classification == AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY:
        return WORKFLOW_SEMANTIC_STATE_UNKNOWN_INTERNAL
    if context_package.authority_resolution.overall_outcome_classification == AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION:
        return WORKFLOW_SEMANTIC_STATE_KNOWN_CONDITIONAL
    return WORKFLOW_SEMANTIC_STATE_KNOWN_YES


def _authoritative_items(context_package: ContextPackage) -> tuple[Any, ...]:
    items_by_id = {
        item.item_id: item
        for item in (
            context_package.phase_4_context
            + context_package.phase_5_context
            + context_package.phase_6_context
        )
    }
    ordered_ids = (
        context_package.authority_resolution.resolved_current_truth_item_ids
        + context_package.authority_resolution.current_guidance_item_ids
    )
    return tuple(
        item
        for item_id in ordered_ids
        if (item := items_by_id.get(item_id)) is not None
    )


def _semantic_state_from_item(item: Any) -> str | None:
    reasoning_state = getattr(item, "reasoning_state", None)
    if reasoning_state in {
        PHASE_7_REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
        PHASE_7_REASONING_STATE_CURRENT_STATUS_UNKNOWN,
        PHASE_7_REASONING_STATE_NO_APPLICABLE_RULE,
        PHASE_7_REASONING_STATE_INSUFFICIENT_INFORMATION,
        PHASE_7_REASONING_STATE_MANUAL_REVIEW_REQUIRED,
    }:
        return WORKFLOW_SEMANTIC_STATE_UNKNOWN_INTERNAL
    if reasoning_state == PHASE_7_REASONING_STATE_REQUIRES_CONFIRMATION:
        return WORKFLOW_SEMANTIC_STATE_KNOWN_CONDITIONAL

    payload = getattr(item, "layer_payload", {}) or {}
    status_values = {
        value
        for key, value in payload.items()
        if key.endswith("_status") and isinstance(value, str)
    }
    if "support_status" in payload and isinstance(payload["support_status"], str):
        status_values.add(payload["support_status"])
    if "outcome" in payload and isinstance(payload["outcome"], str):
        status_values.add(payload["outcome"])

    if status_values.intersection(
        {
            "external_supplier_required",
            "not_available",
            "restricted",
            "exceeds_capacity",
            "not_event_capacity_space",
            "insufficient_quantity",
        }
    ):
        return WORKFLOW_SEMANTIC_STATE_KNOWN_NO
    if status_values.intersection({"requires_confirmation", "conditional"}):
        return WORKFLOW_SEMANTIC_STATE_KNOWN_CONDITIONAL
    if status_values.intersection(
        {
            "supported",
            "standard",
            "available_on_request",
            "within_capacity",
            "allowed",
            "available",
            "included",
            "shared",
        }
    ):
        return WORKFLOW_SEMANTIC_STATE_KNOWN_YES

    if any(
        bool(payload.get(flag))
        for flag in (
            "requires_confirmation",
            "requires_availability_confirmation",
            "requires_scope_confirmation",
            "requires_technical_confirmation",
        )
    ):
        return WORKFLOW_SEMANTIC_STATE_KNOWN_CONDITIONAL
    if bool(payload.get("manual_review_required")):
        return WORKFLOW_SEMANTIC_STATE_UNKNOWN_INTERNAL
    if reasoning_state == PHASE_7_REASONING_STATE_RESOLVED:
        return WORKFLOW_SEMANTIC_STATE_KNOWN_YES
    return None


def _dominant_semantic_state(candidates: list[str]) -> str:
    priority = {
        WORKFLOW_SEMANTIC_STATE_KNOWN_NO: 4,
        WORKFLOW_SEMANTIC_STATE_UNKNOWN_INTERNAL: 3,
        WORKFLOW_SEMANTIC_STATE_KNOWN_CONDITIONAL: 2,
        WORKFLOW_SEMANTIC_STATE_KNOWN_YES: 1,
    }
    return max(candidates, key=lambda item: priority.get(item, 0))


def _derive_workflow_posture(
    context_package: ContextPackage,
    authority_outcome: str,
    reasoning_state_code: str,
) -> WorkflowReasoningPosture:
    degraded_material = context_package.degraded_retrieval_state.materially_affects_answer_completeness
    has_conflicts = bool(context_package.authority_resolution.conflict_records)
    unresolved = context_package.authority_resolution.unresolved_authority_records
    confirmation_required = authority_outcome == AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION or any(
        record.requires_confirmation or record.reasoning_state == PHASE_7_REASONING_STATE_REQUIRES_CONFIRMATION
        for record in unresolved
    )
    blocked_current = authority_outcome == AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY or any(
        record.reasoning_state
        in {
            PHASE_7_REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
            PHASE_7_REASONING_STATE_CURRENT_STATUS_UNKNOWN,
            PHASE_7_REASONING_STATE_NO_APPLICABLE_RULE,
        }
        for record in unresolved
    )
    manual_review = degraded_material or has_conflicts or any(
        record.requires_manual_review
        or record.reasoning_state
        in {
            PHASE_7_REASONING_STATE_MANUAL_REVIEW_REQUIRED,
            PHASE_7_REASONING_STATE_INSUFFICIENT_INFORMATION,
        }
        for record in unresolved
    )

    posture_code = WORKFLOW_REASONING_POSTURE_REVIEW_REQUIRED
    deterministic_use_allowed = False
    historical_context_only = False
    review_required = False
    blocked_for_current_decision = False

    if authority_outcome == AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT:
        posture_code = WORKFLOW_REASONING_POSTURE_SAFE_FOR_DETERMINISTIC_USE
        deterministic_use_allowed = True
    elif authority_outcome == AUTHORITY_OUTCOME_CURRENT_GUIDANCE:
        posture_code = WORKFLOW_REASONING_POSTURE_GUIDANCE_ONLY
    elif authority_outcome == AUTHORITY_OUTCOME_HISTORICAL_PRECEDENT:
        posture_code = WORKFLOW_REASONING_POSTURE_HISTORICAL_CONTEXT_ONLY
        historical_context_only = True
    elif authority_outcome == AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY:
        if context_package.authority_resolution.resolved_current_truth_item_ids:
            posture_code = WORKFLOW_REASONING_POSTURE_SAFE_FOR_DETERMINISTIC_USE
            deterministic_use_allowed = True
        else:
            posture_code = WORKFLOW_REASONING_POSTURE_GUIDANCE_ONLY
    elif authority_outcome == AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION:
        posture_code = WORKFLOW_REASONING_POSTURE_REVIEW_REQUIRED
        review_required = True
    elif authority_outcome == AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY:
        posture_code = WORKFLOW_REASONING_POSTURE_BLOCKED_FOR_CURRENT_DECISION
        blocked_for_current_decision = True

    if blocked_current:
        posture_code = WORKFLOW_REASONING_POSTURE_BLOCKED_FOR_CURRENT_DECISION
        deterministic_use_allowed = False
        blocked_for_current_decision = True
        historical_context_only = authority_outcome == AUTHORITY_OUTCOME_HISTORICAL_PRECEDENT
    elif confirmation_required or manual_review:
        if posture_code != WORKFLOW_REASONING_POSTURE_HISTORICAL_CONTEXT_ONLY:
            posture_code = WORKFLOW_REASONING_POSTURE_REVIEW_REQUIRED
        deterministic_use_allowed = False
        review_required = posture_code == WORKFLOW_REASONING_POSTURE_REVIEW_REQUIRED
    elif posture_code == WORKFLOW_REASONING_POSTURE_SAFE_FOR_DETERMINISTIC_USE and degraded_material:
        posture_code = WORKFLOW_REASONING_POSTURE_REVIEW_REQUIRED
        deterministic_use_allowed = False
        review_required = True

    if reasoning_state_code == PHASE_7_REASONING_STATE_RESOLVED and posture_code == WORKFLOW_REASONING_POSTURE_SAFE_FOR_DETERMINISTIC_USE:
        review_required = False
    elif posture_code == WORKFLOW_REASONING_POSTURE_REVIEW_REQUIRED:
        review_required = True

    return WorkflowReasoningPosture(
        posture_code=posture_code,
        authority_outcome_classification=authority_outcome,
        deterministic_use_allowed=deterministic_use_allowed,
        review_required=review_required,
        blocked_for_current_decision=blocked_for_current_decision,
        confirmation_required=confirmation_required,
        historical_context_only=historical_context_only,
        revalidation_required=degraded_material,
    )


def _projection_identity_key(
    *,
    rental_case_id: int,
    source_case_revision: int,
    reasoning_purpose: str,
    context_package: ContextPackage,
    reasoning_state_code: str,
    posture: WorkflowReasoningPosture,
) -> str:
    material = {
        "rental_case_id": rental_case_id,
        "source_case_revision": source_case_revision,
        "reasoning_purpose": reasoning_purpose,
        "phase_7_context_contract_version": context_package.context_contract_version,
        "phase_8_consumption_contract_version": PHASE_8_PHASE7_WORKFLOW_CONSUMPTION_CONTRACT_VERSION,
        "authority_outcome": context_package.authority_resolution.overall_outcome_classification,
        "reasoning_state_code": reasoning_state_code,
        "workflow_posture": posture.posture_code,
        "resolved_current_truth_item_ids": context_package.authority_resolution.resolved_current_truth_item_ids,
        "current_guidance_item_ids": context_package.authority_resolution.current_guidance_item_ids,
        "historical_precedent_item_ids": context_package.authority_resolution.historical_precedent_item_ids,
        "conflict_codes": tuple(
            record.conflict_type_code for record in context_package.authority_resolution.conflict_records
        ),
        "contamination_codes": tuple(
            annotation.forbidden_inference_type
            for annotation in context_package.authority_resolution.contamination_annotations
        ),
        "unresolved_authority_codes": tuple(
            _unresolved_code(record)
            for record in context_package.authority_resolution.unresolved_authority_records
        ),
        "warning_codes": _warning_codes(context_package),
        "grounding_reference_keys": tuple(reference.reference_id for reference in context_package.grounding.references),
        "degraded_retrieval_summary": _degraded_summary(context_package.degraded_retrieval_state),
        "effective_confidentiality_level": context_package.confidentiality_state.effective_confidentiality_level,
        "de_identification_required": context_package.confidentiality_state.de_identification_required,
        "personal_information_present": context_package.confidentiality_state.personal_information_present,
    }
    payload = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"p7wf:{digest}"


def _projection_freshness_status(
    snapshot: Phase7ConsumptionCaseSnapshot,
    projection: WorkflowReasoningProjection,
) -> str:
    newer = any(
        existing.reasoning_projection_id != projection.reasoning_projection_id
        and existing.reasoning_purpose == projection.reasoning_purpose
        and (
            existing.source_case_revision > projection.source_case_revision
            or (
                existing.source_case_revision == projection.source_case_revision
                and existing.created_at > projection.created_at
            )
        )
        for existing in snapshot.reasoning_projections
    )
    if newer:
        return WORKFLOW_REASONING_FRESHNESS_SUPERSEDED
    if snapshot.rental_case.case_revision > projection.source_case_revision:
        return WORKFLOW_REASONING_FRESHNESS_STALE
    return WORKFLOW_REASONING_FRESHNESS_CURRENT


def _posture_from_projection(projection: WorkflowReasoningProjection) -> WorkflowReasoningPosture:
    posture_code = projection.workflow_posture or WORKFLOW_REASONING_POSTURE_REVIEW_REQUIRED
    confirmation_required = (
        projection.authority_outcome_classification == AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION
        or projection.reasoning_state_code == PHASE_7_REASONING_STATE_REQUIRES_CONFIRMATION
        or any(
            code.endswith(f"|{PHASE_7_REASONING_STATE_REQUIRES_CONFIRMATION}")
            for code in projection.unresolved_authority_codes
        )
    )
    return WorkflowReasoningPosture(
        posture_code=posture_code,
        authority_outcome_classification=projection.authority_outcome_classification,
        deterministic_use_allowed=posture_code == WORKFLOW_REASONING_POSTURE_SAFE_FOR_DETERMINISTIC_USE,
        review_required=posture_code == WORKFLOW_REASONING_POSTURE_REVIEW_REQUIRED,
        blocked_for_current_decision=posture_code == WORKFLOW_REASONING_POSTURE_BLOCKED_FOR_CURRENT_DECISION,
        confirmation_required=confirmation_required,
        historical_context_only=posture_code == WORKFLOW_REASONING_POSTURE_HISTORICAL_CONTEXT_ONLY,
        revalidation_required=projection.materially_affects_completeness,
    )


def _derive_workflow_effects(projection: WorkflowReasoningProjection) -> tuple[WorkflowReasoningEffect, ...]:
    effects: list[WorkflowReasoningEffect] = []
    domain_scope_code = _projection_domain_scope_code(projection)
    posture = _posture_from_projection(projection)
    semantic_state_code = projection_semantic_state_code(projection)

    if projection.relevant_current_truth_item_ids:
        effects.append(
            _make_effect(
                projection=projection,
                effect_type_code=WORKFLOW_REASONING_EFFECT_CURRENT_TRUTH_AVAILABLE,
                blocking_relevance=False,
                domain_scope_code=domain_scope_code,
                related_item_ids=projection.relevant_current_truth_item_ids,
            )
        )
    if projection.relevant_guidance_item_ids:
        effects.append(
            _make_effect(
                projection=projection,
                effect_type_code=WORKFLOW_REASONING_EFFECT_CURRENT_GUIDANCE_AVAILABLE,
                blocking_relevance=False,
                domain_scope_code=domain_scope_code,
                related_item_ids=projection.relevant_guidance_item_ids,
            )
        )
    if projection.relevant_historical_item_ids:
        effects.append(
            _make_effect(
                projection=projection,
                effect_type_code=WORKFLOW_REASONING_EFFECT_HISTORICAL_CONTEXT_AVAILABLE,
                blocking_relevance=projection.workflow_posture == WORKFLOW_REASONING_POSTURE_BLOCKED_FOR_CURRENT_DECISION,
                domain_scope_code=domain_scope_code,
                related_item_ids=projection.relevant_historical_item_ids,
                detail_payload={"historical_context_only": True},
            )
        )
    if semantic_state_code == WORKFLOW_SEMANTIC_STATE_KNOWN_NO:
        effects.append(
            _make_effect(
                projection=projection,
                effect_type_code=WORKFLOW_REASONING_EFFECT_DETERMINISTIC_RESTRICTION,
                blocking_relevance=True,
                domain_scope_code=domain_scope_code,
                detail_payload={"semantic_state_code": semantic_state_code},
            )
        )
    if posture.confirmation_required:
        effects.append(
            _make_effect(
                projection=projection,
                effect_type_code=WORKFLOW_REASONING_EFFECT_CONFIRMATION_REQUIRED,
                blocking_relevance=True,
                domain_scope_code=domain_scope_code,
            )
        )
    if projection.authority_outcome_classification == AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY:
        effects.append(
            _make_effect(
                projection=projection,
                effect_type_code=WORKFLOW_REASONING_EFFECT_CURRENT_AUTHORITY_MISSING,
                blocking_relevance=True,
                domain_scope_code=domain_scope_code,
            )
        )
    if posture.review_required or posture.blocked_for_current_decision:
        effects.append(
            _make_effect(
                projection=projection,
                effect_type_code=WORKFLOW_REASONING_EFFECT_REVIEW_REQUIRED,
                blocking_relevance=True,
                domain_scope_code=domain_scope_code,
            )
        )
    if projection.degraded_retrieval_summary.get("any_degradation"):
        effects.append(
            _make_effect(
                projection=projection,
                effect_type_code=WORKFLOW_REASONING_EFFECT_DEGRADED_WARNING,
                blocking_relevance=projection.materially_affects_completeness,
                domain_scope_code=domain_scope_code,
                detail_payload=projection.degraded_retrieval_summary,
            )
        )
    for conflict_code in projection.conflict_codes:
        effects.append(
            _make_effect(
                projection=projection,
                effect_type_code=WORKFLOW_REASONING_EFFECT_CONFLICT_PRESENT,
                blocking_relevance=True,
                domain_scope_code=domain_scope_code,
                related_code=conflict_code,
            )
        )
    for contamination_code in projection.contamination_codes:
        effects.append(
            _make_effect(
                projection=projection,
                effect_type_code=WORKFLOW_REASONING_EFFECT_CONTAMINATION_WARNING,
                blocking_relevance=projection.workflow_posture != WORKFLOW_REASONING_POSTURE_HISTORICAL_CONTEXT_ONLY,
                domain_scope_code=domain_scope_code,
                related_code=contamination_code,
            )
        )
    if projection.reasoning_purpose in {"requirement_detection", "compliance_requirement_review"} and (
        projection.relevant_current_truth_item_ids or projection.relevant_guidance_item_ids
    ):
        effects.append(
            _make_effect(
                projection=projection,
                effect_type_code=WORKFLOW_REASONING_EFFECT_REQUIREMENT_CANDIDATE,
                blocking_relevance=projection.workflow_posture != WORKFLOW_REASONING_POSTURE_SAFE_FOR_DETERMINISTIC_USE,
                domain_scope_code=domain_scope_code,
                related_item_ids=projection.relevant_current_truth_item_ids or projection.relevant_guidance_item_ids,
            )
        )
    return tuple(effects)


def _make_effect(
    *,
    projection: WorkflowReasoningProjection,
    effect_type_code: str,
    blocking_relevance: bool,
    domain_scope_code: str | None,
    related_code: str | None = None,
    related_item_ids: tuple[str, ...] = (),
    detail_payload: dict[str, Any] | None = None,
) -> WorkflowReasoningEffect:
    return WorkflowReasoningEffect(
        effect_type_code=effect_type_code,
        rental_case_id=projection.rental_case_id,
        reasoning_purpose=projection.reasoning_purpose,
        source_case_revision=projection.source_case_revision,
        authority_outcome_classification=projection.authority_outcome_classification,
        source_projection_identity_key=projection.projection_identity_key or "projection",
        blocking_relevance=blocking_relevance,
        domain_scope_code=domain_scope_code,
        related_code=related_code,
        related_item_ids=related_item_ids,
        detail_payload=detail_payload or {},
    )


def _projection_domain_scope_code(projection: WorkflowReasoningProjection) -> str | None:
    for item_id in projection.relevant_current_truth_item_ids + projection.relevant_guidance_item_ids:
        if ":" in item_id:
            return item_id.split(":", 1)[0]
    if projection.relevant_current_truth_item_ids:
        return projection.relevant_current_truth_item_ids[0]
    if projection.relevant_guidance_item_ids:
        return projection.relevant_guidance_item_ids[0]
    if projection.relevant_historical_item_ids:
        return projection.relevant_historical_item_ids[0]
    if projection.unresolved_authority_codes:
        return projection.unresolved_authority_codes[0].split("|", 1)[0]
    return None


def _warning_codes(context_package: ContextPackage) -> tuple[str, ...]:
    warnings = list(context_package.generator_policy.required_warnings)
    warnings.extend(context_package.degraded_retrieval_state.generator_warnings)
    if context_package.confidentiality_state.generation_restriction_reason is not None:
        warnings.append(context_package.confidentiality_state.generation_restriction_reason)
    return tuple(dict.fromkeys(warnings))


def _unresolved_code(record: UnresolvedAuthorityRecord) -> str:
    return f"{record.topic_or_domain}|{record.reasoning_state}"


def _degraded_summary(
    state: DegradedRetrievalState,
    *,
    semantic_state_code: str | None = None,
) -> dict[str, Any]:
    summary = {
        "any_degradation": state.any_degradation,
        "materially_affects_answer_completeness": state.materially_affects_answer_completeness,
        "affected_layers": list(state.affected_layers),
        "per_layer_execution_states": dict(state.per_layer_execution_states),
        "fallback_reasons": dict(state.fallback_reasons),
        "generator_warnings": list(state.generator_warnings),
    }
    if semantic_state_code is not None:
        summary["semantic_state_code"] = semantic_state_code
    return summary
