from __future__ import annotations

from typing import Any, Callable

from tools.phase_06_search.historical_retrieval import (
    HistoricalRetrievalError,
    retrieve_historical_precedents,
)

from .contracts import (
    AUTHORITY_TIER_HISTORICAL_PRECEDENT,
    CONFIDENTIALITY_LEVEL_RESTRICTED,
    EXECUTION_STATE_FAILED,
    EXECUTION_STATE_FALLBACK,
    EXECUTION_STATE_NOT_REQUESTED,
    EXECUTION_STATE_NO_RESULTS,
    EXECUTION_STATE_SUCCESS,
    EXECUTION_STATE_UNAVAILABLE,
    LAYER_ID_PHASE_6,
    PERSONAL_INFORMATION_STATUS_NO,
    PERSONAL_INFORMATION_STATUS_UNKNOWN,
    PERSONAL_INFORMATION_STATUS_YES,
    ExactIdentity,
    LayerExecutionRecord,
    NormalizedResultEnvelope,
    Phase7RuntimeConfiguration,
    ProvenanceEnvelope,
    QueryContext,
    QueryPlan,
    RetrievalMetadata,
    SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
    SensitivityEnvelope,
    StableIdentity,
    authority_priority_for_tier,
)
from .validation import Phase7ContractError


HistoricalRetrievalFunction = Callable[..., dict[str, Any]]

HISTORICAL_RETRIEVAL_MODE_HYBRID = "hybrid"
HISTORICAL_RETRIEVAL_MODE_FTS_FALLBACK = "fts_fallback"

PHASE6_CONTENT_KIND_BY_UNIT_TYPE = {
    "case_narrative": "phase6_historical_case_narrative",
    "responsibility": "phase6_historical_responsibility",
    "decision": "phase6_historical_decision",
    "lesson": "phase6_historical_lesson",
}


def execute_phase6_plan(
    query_plan: QueryPlan,
    query_context: QueryContext | None = None,
    runtime_configuration: Phase7RuntimeConfiguration | None = None,
    historical_retrieval_fn: HistoricalRetrievalFunction | None = None,
) -> LayerExecutionRecord:
    if query_context is not None and query_context.query_text != query_plan.query_text:
        raise Phase7ContractError(
            error_category="invalid_value",
            safe_message="query_context.query_text must match query_plan.query_text.",
        )

    phase6_intent = query_plan.phase_6
    if phase6_intent is None or not phase6_intent.required:
        return LayerExecutionRecord(
            layer_id=LAYER_ID_PHASE_6,
            requested=False,
            execution_state=EXECUTION_STATE_NOT_REQUESTED,
            reasoning_state=None,
            fallback_reason=None,
            error_category=None,
            safe_error_message=None,
            result_count=0,
            normalized_items=(),
        )

    config = runtime_configuration or Phase7RuntimeConfiguration()
    retrieval_fn = historical_retrieval_fn or retrieve_historical_precedents
    query_text = phase6_intent.query_text or query_plan.query_text
    filters = phase6_intent.filters

    try:
        response = retrieval_fn(
            query_text,
            result_limit=config.phase_6_result_limit,
            case_code=filters.case_code,
            unit_type=filters.unit_type,
            precedent_availability=filters.precedent_availability,
            precedent_type=filters.precedent_type,
            lesson_kind=filters.lesson_kind,
            historical_value_only=filters.historical_value_only,
            contamination_risk_level=filters.contamination_risk_level,
        )
    except HistoricalRetrievalError as exc:
        return LayerExecutionRecord(
            layer_id=LAYER_ID_PHASE_6,
            requested=True,
            execution_state=_map_error_category_to_execution_state(exc.error_category),
            reasoning_state=None,
            fallback_reason=None,
            error_category=exc.error_category,
            safe_error_message=exc.safe_message,
            result_count=0,
            normalized_items=(),
        )

    rows = tuple(response.get("results", ()))
    fallback_reason = _clean_text(response.get("fallback_reason"))
    layer_execution_state = _derive_layer_execution_state(response)

    if not rows:
        return LayerExecutionRecord(
            layer_id=LAYER_ID_PHASE_6,
            requested=True,
            execution_state=EXECUTION_STATE_NO_RESULTS,
            reasoning_state=None,
            fallback_reason=fallback_reason,
            error_category=None,
            safe_error_message=None,
            result_count=0,
            normalized_items=(),
        )

    normalized_items = tuple(
        _normalize_phase6_row(
            row=row,
            rank=index,
            response=response,
            execution_state=layer_execution_state,
        )
        for index, row in enumerate(rows, start=1)
    )

    return LayerExecutionRecord(
        layer_id=LAYER_ID_PHASE_6,
        requested=True,
        execution_state=layer_execution_state,
        reasoning_state=None,
        fallback_reason=fallback_reason,
        error_category=None,
        safe_error_message=None,
        result_count=len(normalized_items),
        normalized_items=normalized_items,
    )


def _map_error_category_to_execution_state(error_category: str) -> str:
    if error_category == "database_unavailable":
        return EXECUTION_STATE_UNAVAILABLE
    return EXECUTION_STATE_FAILED


def _derive_layer_execution_state(response: dict[str, Any]) -> str:
    retrieval_mode_used = _clean_text(response.get("retrieval_mode_used"))
    fallback_used = bool(response.get("fallback_used"))
    if fallback_used or retrieval_mode_used == HISTORICAL_RETRIEVAL_MODE_FTS_FALLBACK:
        return EXECUTION_STATE_FALLBACK
    return EXECUTION_STATE_SUCCESS


def _normalize_phase6_row(
    *,
    row: dict[str, Any],
    rank: int,
    response: dict[str, Any],
    execution_state: str,
) -> NormalizedResultEnvelope:
    authority_priority = authority_priority_for_tier(AUTHORITY_TIER_HISTORICAL_PRECEDENT)
    stable_identity = StableIdentity(
        primary_code=_clean_text(row.get("case_code")),
        secondary_code=_clean_text(row.get("source_key")),
        native_identity_payload={
            "unit_type": row.get("unit_type"),
            "case_title": row.get("case_title"),
            "precedent_type": row.get("precedent_type"),
        },
    )
    exact_identity = ExactIdentity(
        primary_id=_coerce_positive_int(row.get("historical_case_id")),
        version_id=_coerce_positive_int(row.get("historical_case_version_id")),
        version_number=None,
        secondary_id=_coerce_positive_int(row.get("search_unit_id")),
        native_identity_payload=_compact_dict(
            {
                "responsibility_id": row.get("responsibility_id"),
                "decision_id": row.get("decision_id"),
                "lesson_id": row.get("lesson_id"),
                "primary_historical_case_version_source_object_id": row.get(
                    "primary_historical_case_version_source_object_id"
                ),
                "primary_source_object_id": row.get("primary_source_object_id"),
            }
        ),
    )
    provenance = _build_phase6_provenance(row)
    sensitivity = _build_phase6_sensitivity(row)
    retrieval = _build_phase6_retrieval_metadata(
        row=row,
        rank=rank,
        response=response,
    )

    layer_payload = dict(row)
    layer_payload["phase6_retrieval_mode_requested"] = response.get("retrieval_mode_requested")
    layer_payload["phase6_retrieval_mode_used"] = response.get("retrieval_mode_used")
    layer_payload["phase6_fallback_used"] = response.get("fallback_used")
    layer_payload["phase6_fallback_reason"] = response.get("fallback_reason")
    layer_payload["phase6_strategy_code"] = response.get("strategy_code")
    layer_payload["phase6_configuration_code"] = response.get("configuration_code")
    layer_payload["phase6_embedding_model"] = response.get("embedding_model")
    layer_payload["phase6_historical_embedding_state"] = response.get("historical_embedding_state")
    layer_payload["source_layer_role"] = SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT
    layer_payload["authority_tier_code"] = AUTHORITY_TIER_HISTORICAL_PRECEDENT
    layer_payload["authority_priority"] = authority_priority

    return NormalizedResultEnvelope(
        item_id=_build_item_id(row),
        source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
        authority_tier_code=AUTHORITY_TIER_HISTORICAL_PRECEDENT,
        authority_priority=authority_priority,
        stable_identity=stable_identity,
        exact_identity=exact_identity,
        content_kind=_phase6_content_kind(row),
        execution_state=execution_state,
        reasoning_state=None,
        summary_text=_clean_text(row.get("search_text")),
        provenance=provenance,
        sensitivity=sensitivity,
        retrieval=retrieval,
        layer_payload=layer_payload,
    )


def _build_item_id(row: dict[str, Any]) -> str:
    case_code = _clean_text(row.get("case_code")) or "unknown_case"
    source_key = _clean_text(row.get("source_key"))
    if source_key is not None:
        return f"phase6:{case_code}:{source_key}"
    search_unit_id = row.get("search_unit_id")
    return f"phase6:{case_code}:{search_unit_id}"


def _phase6_content_kind(row: dict[str, Any]) -> str:
    unit_type = _clean_text(row.get("unit_type"))
    if unit_type is None:
        return "phase6_historical_precedent"
    return PHASE6_CONTENT_KIND_BY_UNIT_TYPE.get(unit_type, f"phase6_historical_{unit_type}")


def _build_phase6_provenance(row: dict[str, Any]) -> ProvenanceEnvelope:
    case_code = _clean_text(row.get("case_code"))
    source_key = _clean_text(row.get("source_key"))
    source_codes = tuple(code for code in (case_code, source_key) if code is not None)
    source_identifiers = _compact_dict(
        {
            "historical_case_id": row.get("historical_case_id"),
            "historical_case_version_id": row.get("historical_case_version_id"),
            "search_unit_id": row.get("search_unit_id"),
            "responsibility_id": row.get("responsibility_id"),
            "decision_id": row.get("decision_id"),
            "lesson_id": row.get("lesson_id"),
            "primary_historical_case_version_source_object_id": row.get(
                "primary_historical_case_version_source_object_id"
            ),
            "primary_source_object_id": row.get("primary_source_object_id"),
        }
    )
    return ProvenanceEnvelope(
        source_codes=source_codes,
        source_identifiers=source_identifiers,
        primary_source_locator=_clean_text(row.get("primary_source_locator")),
        additional_locators=(),
        source_link_count=_coerce_non_negative_int(row.get("source_link_count")),
        native_provenance_payload=_compact_dict(
            {
                "case_title": row.get("case_title"),
                "unit_type": row.get("unit_type"),
                "precedent_type": row.get("precedent_type"),
                "precedent_availability": row.get("precedent_availability"),
                "source_layer_role": row.get("source_layer_role"),
            }
        ),
    )


def _build_phase6_sensitivity(row: dict[str, Any]) -> SensitivityEnvelope:
    pi_status = _normalize_personal_information_status(
        row.get("source_object_personal_information_status")
        or row.get("case_personal_information_status")
    )
    confidentiality_level = _clean_text(row.get("effective_confidentiality_level_code")) or CONFIDENTIALITY_LEVEL_RESTRICTED
    return SensitivityEnvelope(
        confidentiality_level=confidentiality_level,
        personal_information_status=pi_status,
        de_identification_required=pi_status == PERSONAL_INFORMATION_STATUS_YES,
        generation_allowed=True,
        generation_restriction_reason=None,
        native_sensitivity_payload=_compact_dict(
            {
                "effective_confidentiality_level_id": row.get("effective_confidentiality_level_id"),
                "case_personal_information_status": row.get("case_personal_information_status"),
                "source_object_personal_information_status": row.get("source_object_personal_information_status"),
            }
        ),
    )


def _build_phase6_retrieval_metadata(
    *,
    row: dict[str, Any],
    rank: int,
    response: dict[str, Any],
) -> RetrievalMetadata:
    component_scores = _compact_float_dict(
        {
            "hybrid_score": row.get("hybrid_score"),
            "lexical_score": row.get("lexical_score"),
            "semantic_similarity_score": row.get("semantic_similarity_score"),
            "semantic_cosine_distance": row.get("semantic_cosine_distance"),
            "rrf_fts_score": row.get("rrf_fts_score"),
            "rrf_semantic_score": row.get("rrf_semantic_score"),
        }
    )
    timing_ms = response.get("timing_ms")
    if isinstance(timing_ms, dict):
        component_scores.update(
            _compact_float_dict(
                {
                    "embedding_generation_ms": timing_ms.get("embedding_generation"),
                    "retrieval_elapsed_ms": timing_ms.get("retrieval"),
                    "total_elapsed_ms": timing_ms.get("total"),
                }
            )
        )

    return RetrievalMetadata(
        retrieval_mode_requested=_clean_text(response.get("retrieval_mode_requested")),
        retrieval_mode_used=_clean_text(response.get("retrieval_mode_used")),
        fallback_used=bool(response.get("fallback_used")),
        fallback_reason=_clean_text(response.get("fallback_reason")),
        rank=rank,
        score=_select_result_score(row),
        component_scores=component_scores,
        strategy_code=_clean_text(row.get("strategy_code")) or _clean_text(response.get("strategy_code")),
        native_retrieval_payload={
            "configuration_code": response.get("configuration_code"),
            "result_limit_requested": response.get("result_limit_requested"),
            "result_limit_used": response.get("result_limit_used"),
            "candidate_pool_limit": response.get("candidate_pool_limit"),
            "embedding_model": response.get("embedding_model"),
            "historical_embedding_state": response.get("historical_embedding_state"),
            "embedding_model_id": row.get("embedding_model_id"),
            "provider_code": row.get("provider_code"),
            "model_code": row.get("model_code"),
            "model_version": row.get("model_version"),
            "came_from_fts": row.get("came_from_fts"),
            "came_from_semantic": row.get("came_from_semantic"),
            "fts_rank": row.get("fts_rank"),
            "semantic_rank": row.get("semantic_rank"),
            "best_component_rank": row.get("best_component_rank"),
            "rrf_k": row.get("rrf_k"),
            "lexical_weight": row.get("lexical_weight"),
            "semantic_weight": row.get("semantic_weight"),
        },
    )


def _select_result_score(row: dict[str, Any]) -> float | None:
    for key in ("hybrid_score", "lexical_score", "semantic_similarity_score"):
        value = row.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return None


def _normalize_personal_information_status(value: Any) -> str:
    normalized = _clean_text(value)
    if normalized is None:
        return PERSONAL_INFORMATION_STATUS_UNKNOWN
    lowered = normalized.lower()
    if lowered in {PERSONAL_INFORMATION_STATUS_YES, "present", "true"}:
        return PERSONAL_INFORMATION_STATUS_YES
    if lowered in {PERSONAL_INFORMATION_STATUS_NO, "not_present", "false"}:
        return PERSONAL_INFORMATION_STATUS_NO
    return PERSONAL_INFORMATION_STATUS_UNKNOWN


def _coerce_positive_int(value: Any) -> int | None:
    if isinstance(value, int) and value > 0:
        return value
    return None


def _coerce_non_negative_int(value: Any) -> int | None:
    if isinstance(value, int) and value >= 0:
        return value
    return None


def _compact_dict(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def _compact_float_dict(values: dict[str, Any]) -> dict[str, float]:
    compacted: dict[str, float] = {}
    for key, value in values.items():
        if isinstance(value, (int, float)):
            compacted[key] = float(value)
    return compacted


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = ["execute_phase6_plan"]
