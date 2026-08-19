from __future__ import annotations

import re
from typing import Iterable

from .contamination_gate import detect_contamination_annotations
from .contracts import (
    AUTHORITY_OUTCOME_CURRENT_GUIDANCE,
    AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
    AUTHORITY_OUTCOME_HISTORICAL_PRECEDENT,
    AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
    AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY,
    AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION,
    CONFLICT_TYPE_A_P4_BEATS_P6,
    CONFLICT_TYPE_B_P5_BEATS_P6,
    CONFLICT_TYPE_C_P6_EXISTS_BUT_CURRENT_MISSING,
    CONFLICT_TYPE_D_P4_REQUIRES_CONFIRMATION,
    CONFLICT_TYPE_E_P5_FAILURE_P4_SURVIVES,
    CONFLICT_TYPE_F_LIMITED_OR_UNKNOWN_PRECEDENT,
    CONFLICT_TYPE_G_CONFIDENTIALITY_ESCALATION,
    EXECUTION_STATE_FAILED,
    EXECUTION_STATE_FALLBACK,
    EXECUTION_STATE_SUCCESS,
    EXECUTION_STATE_NO_RESULTS,
    EXECUTION_STATE_UNAVAILABLE,
    FORBIDDEN_INFERENCE_HISTORICAL_CONCESSION_TO_CURRENT_POLICY,
    FORBIDDEN_INFERENCE_HISTORICAL_LEGAL_SOLUTION_TO_CURRENT_GUIDANCE,
    FORBIDDEN_INFERENCE_HISTORICAL_OVERTIME_HANDLING_TO_CURRENT_RATE,
    FORBIDDEN_INFERENCE_HISTORICAL_PERSON_CAPABILITY_TO_CURRENT_SERVICE,
    FORBIDDEN_INFERENCE_HISTORICAL_PRICE_TO_CURRENT_PRICE,
    FORBIDDEN_INFERENCE_HISTORICAL_ROOM_USE_TO_CURRENT_ACCESS_RIGHT,
    LAYER_ID_PHASE_4,
    LAYER_ID_PHASE_5,
    LAYER_ID_PHASE_6,
    QUERY_CLASS_AUTHORITY_VERIFICATION,
    QUERY_CLASS_CURRENT_GUIDANCE,
    QUERY_CLASS_DETERMINISTIC_CURRENT,
    QUERY_CLASS_MIXED_CURRENT_AND_PRECEDENT,
    QUERY_CLASS_PRECEDENT_DISCOVERY,
    QUERY_CLASS_UNRESOLVED_AUTHORITY,
    REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
    REASONING_STATE_INSUFFICIENT_INFORMATION,
    REASONING_STATE_MANUAL_REVIEW_REQUIRED,
    REASONING_STATE_NO_APPLICABLE_RULE,
    REASONING_STATE_REQUIRES_CONFIRMATION,
    REASONING_STATE_RESOLVED,
    REASONING_STATE_CURRENT_STATUS_UNKNOWN,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    AuthorityResolution,
    ConflictRecord,
    ContaminationAnnotation,
    LayerExecutionRecord,
    NormalizedResultEnvelope,
    QueryPlan,
    UnresolvedAuthorityRecord,
)


def resolve_authority(
    query_plan: QueryPlan,
    phase4_execution: LayerExecutionRecord,
    phase5_execution: LayerExecutionRecord,
    phase6_execution: LayerExecutionRecord,
    contamination_annotations: tuple[ContaminationAnnotation, ...] | None = None,
) -> AuthorityResolution:
    annotations = contamination_annotations or detect_contamination_annotations(
        query_plan,
        phase4_execution,
        phase5_execution,
        phase6_execution,
    )

    phase4_items = tuple(phase4_execution.normalized_items)
    phase5_items = tuple(phase5_execution.normalized_items)
    phase6_items = tuple(phase6_execution.normalized_items)
    controlling_phase4 = _phase4_controlling_truth_items(query_plan, phase4_items)

    usable_phase5 = tuple(
        phase5_items
        if phase5_execution.execution_state in {EXECUTION_STATE_SUCCESS, EXECUTION_STATE_FALLBACK}
        else ()
    )
    usable_phase6 = tuple(
        phase6_items
        if phase6_execution.execution_state in {EXECUTION_STATE_SUCCESS, EXECUTION_STATE_FALLBACK}
        else ()
    )

    unresolved_records = _build_unresolved_authority_records(
        query_plan=query_plan,
        phase4_execution=phase4_execution,
        phase5_execution=phase5_execution,
        phase6_execution=phase6_execution,
        contamination_annotations=annotations,
    )
    conflict_records = _build_conflict_records(
        query_plan=query_plan,
        phase4_execution=phase4_execution,
        phase5_execution=phase5_execution,
        phase6_execution=phase6_execution,
        contamination_annotations=annotations,
        unresolved_records=unresolved_records,
    )

    outcome = _classify_overall_outcome(
        query_plan=query_plan,
        phase4_execution=phase4_execution,
        phase5_execution=phase5_execution,
        phase6_execution=phase6_execution,
        contamination_annotations=annotations,
        unresolved_records=unresolved_records,
    )

    return AuthorityResolution(
        overall_outcome_classification=outcome,
        resolved_current_truth_item_ids=tuple(item.item_id for item in controlling_phase4),
        current_guidance_item_ids=tuple(item.item_id for item in usable_phase5),
        historical_precedent_item_ids=tuple(item.item_id for item in usable_phase6),
        conflict_records=tuple(conflict_records),
        contamination_annotations=tuple(annotations),
        unresolved_authority_records=tuple(unresolved_records),
    )


def _build_unresolved_authority_records(
    *,
    query_plan: QueryPlan,
    phase4_execution: LayerExecutionRecord,
    phase5_execution: LayerExecutionRecord,
    phase6_execution: LayerExecutionRecord,
    contamination_annotations: tuple[ContaminationAnnotation, ...],
) -> list[UnresolvedAuthorityRecord]:
    records: list[UnresolvedAuthorityRecord] = []
    phase4_items = tuple(phase4_execution.normalized_items)
    phase5_items = tuple(phase5_execution.normalized_items)
    phase6_items = tuple(phase6_execution.normalized_items)
    normalized_query = _normalize(query_plan.query_text)

    for item in phase4_items:
        if item.reasoning_state == REASONING_STATE_REQUIRES_CONFIRMATION and _phase4_confirmation_is_material(
            query_plan,
            item,
        ):
            records.append(
                UnresolvedAuthorityRecord(
                    reasoning_state=REASONING_STATE_REQUIRES_CONFIRMATION,
                    topic_or_domain=_topic_for_item(item),
                    controlling_layer=LAYER_ID_PHASE_4,
                    requires_confirmation=True,
                    related_current_item_ids=(item.item_id,),
                    explanation_code="phase4_requires_confirmation",
                    notes="current_deterministic_authority_requires_confirmation",
                )
            )
        elif item.reasoning_state == REASONING_STATE_MANUAL_REVIEW_REQUIRED:
            records.append(
                UnresolvedAuthorityRecord(
                    reasoning_state=REASONING_STATE_MANUAL_REVIEW_REQUIRED,
                    topic_or_domain=_topic_for_item(item),
                    controlling_layer=LAYER_ID_PHASE_4,
                    requires_manual_review=True,
                    related_current_item_ids=(item.item_id,),
                    explanation_code="phase4_manual_review_required",
                    notes="current_deterministic_authority_requires_manual_review",
                )
            )
        elif item.reasoning_state == REASONING_STATE_INSUFFICIENT_INFORMATION:
            records.append(
                UnresolvedAuthorityRecord(
                    reasoning_state=REASONING_STATE_INSUFFICIENT_INFORMATION,
                    topic_or_domain=_topic_for_item(item),
                    controlling_layer=LAYER_ID_PHASE_4,
                    related_current_item_ids=(item.item_id,),
                    explanation_code="phase4_insufficient_information",
                    notes="additional_structured_inputs_required_for_phase4_resolution",
                )
            )
        elif item.reasoning_state == REASONING_STATE_NO_APPLICABLE_RULE:
            records.append(
                UnresolvedAuthorityRecord(
                    reasoning_state=REASONING_STATE_NO_APPLICABLE_RULE,
                    topic_or_domain=_topic_for_item(item),
                    controlling_layer=LAYER_ID_PHASE_4,
                    related_current_item_ids=(item.item_id,),
                    explanation_code="phase4_no_applicable_rule",
                    notes="no_current_deterministic_rule_resolved_for_requested_scope",
                )
            )

    if phase5_execution.requested and phase5_execution.execution_state == EXECUTION_STATE_NO_RESULTS:
        records.append(
            UnresolvedAuthorityRecord(
                reasoning_state=REASONING_STATE_NO_APPLICABLE_RULE,
                topic_or_domain="phase5_current_guidance",
                controlling_layer=LAYER_ID_PHASE_5,
                related_current_item_ids=(),
                explanation_code="phase5_no_results",
                notes="current_guidance_requested_but_no_governed_guidance_chunk_was_returned",
            )
        )

    if query_plan.query_class == QUERY_CLASS_UNRESOLVED_AUTHORITY and _current_authority_missing(
        phase4_execution,
        phase5_execution,
    ):
        records.append(
            UnresolvedAuthorityRecord(
                reasoning_state=REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
                topic_or_domain=_topic_from_query(query_plan.query_text),
                controlling_layer=None,
                related_current_item_ids=tuple(item.item_id for item in phase4_items + phase5_items),
                related_historical_item_ids=tuple(item.item_id for item in phase6_items[:3]),
                explanation_code="current_authority_missing",
                notes="current_prescriptive_claim_cannot_be_resolved_from_available_current_authority",
            )
        )

    if _contains_reason_code(query_plan, "security_deposit_unresolved_cue"):
        records.append(
            UnresolvedAuthorityRecord(
                reasoning_state=REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
                topic_or_domain="security_deposit",
                controlling_layer=None,
                explanation_code="security_deposit_current_authority_unresolved",
                notes="approved_deterministic_security_deposit_policy_is_not_available",
            )
        )
    if _contains_reason_code(query_plan, "discount_policy_unresolved_cue"):
        records.append(
            UnresolvedAuthorityRecord(
                reasoning_state=REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
                topic_or_domain="discount_policy",
                controlling_layer=None,
                explanation_code="discount_policy_current_authority_unresolved",
                related_historical_item_ids=tuple(item.item_id for item in phase6_items[:3]),
                notes="historical_discount_examples_do_not_create_current_discount_policy",
            )
        )
    if _contains_reason_code(query_plan, "overtime_rate_unresolved_cue"):
        records.append(
            UnresolvedAuthorityRecord(
                reasoning_state=REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
                topic_or_domain="overtime_rate",
                controlling_layer=None,
                explanation_code="overtime_rate_current_authority_unresolved",
                related_historical_item_ids=tuple(item.item_id for item in phase6_items[:3]),
                notes="historical_overtime_handling_does_not_establish_current_rate",
            )
        )

    for item in phase6_items[:3]:
        if item.layer_payload.get("current_authority_disposition") == "current_status_unknown":
            records.append(
                UnresolvedAuthorityRecord(
                    reasoning_state=REASONING_STATE_CURRENT_STATUS_UNKNOWN,
                    topic_or_domain=_topic_from_query(query_plan.query_text),
                    controlling_layer=LAYER_ID_PHASE_6,
                    related_historical_item_ids=(item.item_id,),
                    explanation_code="historical_current_status_unknown",
                    notes="historical_precedent_itself_marks_current_status_unknown",
                )
            )

    for annotation in contamination_annotations:
        if annotation.action == "unresolved" or _annotation_requires_current_authority_gap(annotation):
            records.append(
                UnresolvedAuthorityRecord(
                    reasoning_state=REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
                    topic_or_domain=_topic_from_query(query_plan.query_text),
                    controlling_layer=None,
                    related_current_item_ids=annotation.current_authority_item_ids,
                    related_historical_item_ids=annotation.implicated_historical_item_ids,
                    explanation_code=f"contamination_{annotation.forbidden_inference_type}",
                    notes="historical_precedent_cannot_fill_current_authority_gap",
                )
            )
        elif annotation.action == "requires_confirmation":
            records.append(
                UnresolvedAuthorityRecord(
                    reasoning_state=REASONING_STATE_REQUIRES_CONFIRMATION,
                    topic_or_domain=_topic_from_query(query_plan.query_text),
                    controlling_layer=None,
                    requires_confirmation=True,
                    related_current_item_ids=annotation.current_authority_item_ids,
                    related_historical_item_ids=annotation.implicated_historical_item_ids,
                    explanation_code=f"contamination_{annotation.forbidden_inference_type}",
                    notes="historical_precedent_requires_current_verification_before_prescriptive_use",
                )
            )

    return _dedupe_unresolved_records(records)


def _build_conflict_records(
    *,
    query_plan: QueryPlan,
    phase4_execution: LayerExecutionRecord,
    phase5_execution: LayerExecutionRecord,
    phase6_execution: LayerExecutionRecord,
    contamination_annotations: tuple[ContaminationAnnotation, ...],
    unresolved_records: list[UnresolvedAuthorityRecord],
) -> list[ConflictRecord]:
    conflicts: list[ConflictRecord] = []
    normalized_query = _normalize(query_plan.query_text)
    phase4_items = tuple(phase4_execution.normalized_items)
    phase5_items = tuple(phase5_execution.normalized_items)
    phase6_items = tuple(phase6_execution.normalized_items)
    controlling_phase4_ids = tuple(
        item.item_id for item in _phase4_controlling_truth_items(query_plan, phase4_items)
    )

    phase5_ids = tuple(item.item_id for item in phase5_items)
    limited_or_unknown_ids = tuple(
        item.item_id
        for item in phase6_items[:3]
        if item.layer_payload.get("precedent_availability") == "limited"
        or item.layer_payload.get("current_authority_disposition") == "current_status_unknown"
    )

    if controlling_phase4_ids and phase5_execution.requested and phase5_execution.execution_state in {
        EXECUTION_STATE_FAILED,
        EXECUTION_STATE_UNAVAILABLE,
    }:
        conflicts.append(
            ConflictRecord(
                conflict_type_code=CONFLICT_TYPE_E_P5_FAILURE_P4_SURVIVES,
                controlling_layer=LAYER_ID_PHASE_4,
                affected_item_ids=controlling_phase4_ids,
                severity=SEVERITY_MEDIUM,
                resolution_action="phase_4_deterministic_truth_retained_despite_phase_5_failure",
                notes="current_guidance_layer_failed_but_phase4_still_controls_resolved_current_truth",
            )
        )

    confirmation_item_ids = tuple(
        item.item_id
        for item in phase4_items
        if item.reasoning_state == REASONING_STATE_REQUIRES_CONFIRMATION
        and _phase4_confirmation_is_material(query_plan, item)
    )
    if confirmation_item_ids:
        conflicts.append(
            ConflictRecord(
                conflict_type_code=CONFLICT_TYPE_D_P4_REQUIRES_CONFIRMATION,
                controlling_layer=LAYER_ID_PHASE_4,
                affected_item_ids=confirmation_item_ids,
                severity=SEVERITY_HIGH,
                resolution_action="current_confirmation_required_before_prescriptive_answer",
                notes="phase4_explicitly_requires_confirmation_for_material_current_claim",
            )
        )

    if phase6_items and controlling_phase4_ids and (
        query_plan.query_class == QUERY_CLASS_AUTHORITY_VERIFICATION
        and _matches_any(normalized_query, (" grace period ", " setup ", " back office ", " storage room ", " access "))
    ):
        conflicts.append(
            ConflictRecord(
                conflict_type_code=CONFLICT_TYPE_A_P4_BEATS_P6,
                controlling_layer=LAYER_ID_PHASE_4,
                affected_item_ids=controlling_phase4_ids + tuple(item.item_id for item in phase6_items[:3]),
                severity=SEVERITY_HIGH,
                resolution_action="current_deterministic_rule_wins_over_historical_precedent",
                notes="phase4_controls_current_entitlement_even_when_historical_practice_suggests_otherwise",
            )
        )

    if phase6_items and phase5_ids and (
        query_plan.query_class == QUERY_CLASS_AUTHORITY_VERIFICATION
        or _matches_any(
            normalized_query,
            (
                " override ",
                " what does wnc handle now ",
                " supported rental ",
                " full production ",
                " can we do the same ",
            ),
        )
    ):
        conflicts.append(
            ConflictRecord(
                conflict_type_code=CONFLICT_TYPE_B_P5_BEATS_P6,
                controlling_layer=LAYER_ID_PHASE_5,
                affected_item_ids=phase5_ids[:3] + tuple(item.item_id for item in phase6_items[:3]),
                severity=SEVERITY_MEDIUM,
                resolution_action="current_governed_guidance_wins_over_historical_precedent_for_present_process_or_scope",
                notes="phase5_current_governed_knowledge_controls_current_guidance_even_when_history_is_relevant",
            )
        )

    if phase6_items and _has_missing_current_authority_record(unresolved_records):
        conflicts.append(
            ConflictRecord(
                conflict_type_code=CONFLICT_TYPE_C_P6_EXISTS_BUT_CURRENT_MISSING,
                controlling_layer=LAYER_ID_PHASE_6,
                affected_item_ids=tuple(item.item_id for item in phase6_items[:3]),
                severity=SEVERITY_HIGH,
                resolution_action="history_retained_as_context_but_cannot_fill_current_authority_gap",
                notes="historical_precedent_exists_without_sufficient_current_authority_for_prescriptive_use",
            )
        )

    if limited_or_unknown_ids:
        conflicts.append(
            ConflictRecord(
                conflict_type_code=CONFLICT_TYPE_F_LIMITED_OR_UNKNOWN_PRECEDENT,
                controlling_layer=LAYER_ID_PHASE_6,
                affected_item_ids=limited_or_unknown_ids,
                severity=SEVERITY_MEDIUM,
                resolution_action="preserve_precedent_with_limitation_warning",
                notes="historical_precedent_is_limited_or_marks_current_status_unknown",
            )
        )

    confidentiality_conflict = _confidentiality_conflict_record(phase4_items, phase5_items, phase6_items)
    if confidentiality_conflict is not None:
        conflicts.append(confidentiality_conflict)

    return _dedupe_conflicts(conflicts)


def _classify_overall_outcome(
    *,
    query_plan: QueryPlan,
    phase4_execution: LayerExecutionRecord,
    phase5_execution: LayerExecutionRecord,
    phase6_execution: LayerExecutionRecord,
    contamination_annotations: tuple[ContaminationAnnotation, ...],
    unresolved_records: list[UnresolvedAuthorityRecord],
) -> str:
    phase4_items = tuple(phase4_execution.normalized_items)
    phase5_items = tuple(phase5_execution.normalized_items)
    phase6_items = tuple(phase6_execution.normalized_items)
    controlling_phase4 = _phase4_controlling_truth_items(query_plan, phase4_items)
    has_confirmation_stop = any(
        record.reasoning_state in {REASONING_STATE_REQUIRES_CONFIRMATION, REASONING_STATE_MANUAL_REVIEW_REQUIRED}
        for record in unresolved_records
    )

    if query_plan.query_class == QUERY_CLASS_PRECEDENT_DISCOVERY:
        return AUTHORITY_OUTCOME_HISTORICAL_PRECEDENT

    if query_plan.query_class == QUERY_CLASS_CURRENT_GUIDANCE:
        if has_confirmation_stop:
            return AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION
        if phase5_items:
            return AUTHORITY_OUTCOME_CURRENT_GUIDANCE
        if controlling_phase4:
            return AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT
        if _has_missing_current_authority_record(unresolved_records):
            return AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY
        return AUTHORITY_OUTCOME_CURRENT_GUIDANCE

    if query_plan.query_class == QUERY_CLASS_DETERMINISTIC_CURRENT:
        if has_confirmation_stop:
            return AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION
        if controlling_phase4:
            return AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT
        if _has_missing_current_authority_record(unresolved_records):
            return AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY
        return AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT

    if query_plan.query_class == QUERY_CLASS_MIXED_CURRENT_AND_PRECEDENT:
        if _has_missing_current_authority_record(unresolved_records):
            return AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY
        if has_confirmation_stop:
            return AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION
        if phase6_items and (phase5_items or controlling_phase4):
            return AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY
        if phase5_items:
            return AUTHORITY_OUTCOME_CURRENT_GUIDANCE
        if controlling_phase4:
            return AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT
        return AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY

    if query_plan.query_class == QUERY_CLASS_AUTHORITY_VERIFICATION:
        if any(
            annotation.forbidden_inference_type == FORBIDDEN_INFERENCE_HISTORICAL_LEGAL_SOLUTION_TO_CURRENT_GUIDANCE
            and annotation.action == "requires_confirmation"
            for annotation in contamination_annotations
        ):
            return AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION
        if _has_missing_current_authority_record(unresolved_records):
            return AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY
        if has_confirmation_stop:
            return AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION
        if phase6_items and phase5_items and not any(
            item.item_id for item in controlling_phase4
        ):
            return AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY
        if controlling_phase4:
            if phase6_items and phase5_items:
                return AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY
            return AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT
        return AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY

    if query_plan.query_class == QUERY_CLASS_UNRESOLVED_AUTHORITY:
        if _has_missing_current_authority_record(unresolved_records):
            return AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY
        if has_confirmation_stop:
            return AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION
        if phase6_items and phase5_items:
            return AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY
        if phase5_items:
            return AUTHORITY_OUTCOME_CURRENT_GUIDANCE
        return AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY

    return AUTHORITY_OUTCOME_CURRENT_GUIDANCE


def _current_authority_missing(
    phase4_execution: LayerExecutionRecord,
    phase5_execution: LayerExecutionRecord,
) -> bool:
    if any(item.reasoning_state == REASONING_STATE_RESOLVED for item in phase4_execution.normalized_items):
        return False
    if phase5_execution.normalized_items:
        return False
    if phase4_execution.execution_state in {EXECUTION_STATE_FAILED, EXECUTION_STATE_UNAVAILABLE}:
        return True
    if phase5_execution.execution_state in {EXECUTION_STATE_FAILED, EXECUTION_STATE_UNAVAILABLE}:
        return True
    return True


def _has_missing_current_authority_record(records: Iterable[UnresolvedAuthorityRecord]) -> bool:
    return any(record.reasoning_state == REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY for record in records)


def _confidentiality_conflict_record(
    phase4_items: tuple[NormalizedResultEnvelope, ...],
    phase5_items: tuple[NormalizedResultEnvelope, ...],
    phase6_items: tuple[NormalizedResultEnvelope, ...],
) -> ConflictRecord | None:
    items = tuple(phase4_items + phase5_items + phase6_items)
    if not items:
        return None
    distinct_confidentiality = {item.sensitivity.confidentiality_level for item in items}
    pi_bearing_items = tuple(
        item.item_id
        for item in items
        if item.sensitivity.personal_information_status == "yes"
    )
    if len(distinct_confidentiality) <= 1 and not pi_bearing_items:
        return None
    affected_ids = tuple(item.item_id for item in items if item.source_layer_role != "deterministic_rule") or tuple(
        item.item_id for item in items
    )
    controlling_layer = _strictest_layer(items)
    return ConflictRecord(
        conflict_type_code=CONFLICT_TYPE_G_CONFIDENTIALITY_ESCALATION,
        controlling_layer=controlling_layer,
        affected_item_ids=affected_ids,
        severity=SEVERITY_MEDIUM if not pi_bearing_items else SEVERITY_HIGH,
        resolution_action="defer_final_confidentiality_merge_to_7_2g",
        notes="included_items_have_mixed_confidentiality_or_personal_information_signals",
    )


def _strictest_layer(items: tuple[NormalizedResultEnvelope, ...]) -> str:
    rank = {"externally_shareable": 0, "internal": 1, "commercially_sensitive": 2, "restricted": 3}
    strictest = max(items, key=lambda item: (rank[item.sensitivity.confidentiality_level], -item.authority_priority))
    if strictest.source_layer_role == "deterministic_rule":
        return LAYER_ID_PHASE_4
    if strictest.source_layer_role == "current_governed_knowledge":
        return LAYER_ID_PHASE_5
    return LAYER_ID_PHASE_6


def _dedupe_conflicts(conflicts: list[ConflictRecord]) -> list[ConflictRecord]:
    deduped: list[ConflictRecord] = []
    seen: set[tuple[str, str, tuple[str, ...]]] = set()
    for conflict in conflicts:
        key = (conflict.conflict_type_code, conflict.controlling_layer, conflict.affected_item_ids)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(conflict)
    return deduped


def _dedupe_unresolved_records(records: list[UnresolvedAuthorityRecord]) -> list[UnresolvedAuthorityRecord]:
    deduped: list[UnresolvedAuthorityRecord] = []
    seen: set[tuple[str, str, str | None, tuple[str, ...], tuple[str, ...]]] = set()
    for record in records:
        key = (
            record.reasoning_state,
            record.topic_or_domain,
            record.controlling_layer,
            record.related_current_item_ids,
            record.related_historical_item_ids,
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(record)
    return deduped


def _contains_reason_code(query_plan: QueryPlan, code: str) -> bool:
    candidates = tuple(query_plan.reason_codes)
    if query_plan.phase_4 is not None:
        candidates += tuple(query_plan.phase_4.reason_codes)
    if query_plan.phase_5 is not None:
        candidates += tuple(query_plan.phase_5.reason_codes)
    if query_plan.phase_6 is not None:
        candidates += tuple(query_plan.phase_6.reason_codes)
    return code in candidates


def _phase4_confirmation_is_material(
    query_plan: QueryPlan,
    item: NormalizedResultEnvelope,
) -> bool:
    domain = item.layer_payload.get("phase_4_domain")
    if domain == "space_access":
        return False
    if domain != "service_rules":
        return True
    if query_plan.query_class == QUERY_CLASS_DETERMINISTIC_CURRENT:
        return True
    normalized_query = _normalize(query_plan.query_text)
    if _matches_any(
        normalized_query,
        (" can we support ", " can wnc ", " availability ", " confirm ", " can i offer "),
    ):
        return True
    return False


def _topic_for_item(item: NormalizedResultEnvelope) -> str:
    return str(item.layer_payload.get("phase_4_domain") or item.content_kind)


def _topic_from_query(query_text: str) -> str:
    normalized = _normalize(query_text)
    if _matches_any(normalized, (" price ", " quote ", " rate ", " charge ")):
        return "pricing"
    if _matches_any(normalized, (" floral ", " florals ", " service ")):
        return "service_scope"
    if _matches_any(normalized, (" permit ", " compliance ", " legal ", " ade ")):
        return "compliance"
    if _matches_any(normalized, (" overtime ", " late build ", " build up ")):
        return "overtime"
    if _matches_any(normalized, (" back office ", " storage room ", " access ")):
        return "space_access"
    if _matches_any(normalized, (" facilitator ", " tech ", " capacity ")):
        return "confirmation_bound_scope"
    return "current_authority"


def _normalize(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    return f" {normalized} "


def _matches_any(normalized_query: str, patterns: tuple[str, ...]) -> bool:
    return any(pattern in normalized_query for pattern in patterns)


def _annotation_requires_current_authority_gap(annotation: ContaminationAnnotation) -> bool:
    return annotation.forbidden_inference_type in {
        FORBIDDEN_INFERENCE_HISTORICAL_PRICE_TO_CURRENT_PRICE,
        FORBIDDEN_INFERENCE_HISTORICAL_PERSON_CAPABILITY_TO_CURRENT_SERVICE,
        FORBIDDEN_INFERENCE_HISTORICAL_CONCESSION_TO_CURRENT_POLICY,
        FORBIDDEN_INFERENCE_HISTORICAL_OVERTIME_HANDLING_TO_CURRENT_RATE,
    }


def _phase4_controlling_truth_items(
    query_plan: QueryPlan,
    phase4_items: tuple[NormalizedResultEnvelope, ...],
) -> tuple[NormalizedResultEnvelope, ...]:
    controlling: list[NormalizedResultEnvelope] = [
        item for item in phase4_items if item.reasoning_state == REASONING_STATE_RESOLVED
    ]
    normalized_query = _normalize(query_plan.query_text)
    for item in phase4_items:
        if item.reasoning_state != REASONING_STATE_REQUIRES_CONFIRMATION:
            continue
        if item.layer_payload.get("phase_4_domain") != "space_access":
            continue
        if item.layer_payload.get("access_status") not in {"restricted", "included"}:
            continue
        if not _matches_any(
            normalized_query,
            (" access ", " allowed ", " back office ", " storage room ", " extra rooms ", " offsite storage "),
        ):
            continue
        controlling.append(item)
    return tuple(controlling)


__all__ = ["resolve_authority"]
