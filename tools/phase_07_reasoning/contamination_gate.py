from __future__ import annotations

import re
from typing import Iterable

from .contracts import (
    CONTAMINATION_ACTION_CONTEXT_ONLY,
    CONTAMINATION_ACTION_REQUIRES_CONFIRMATION,
    CONTAMINATION_ACTION_UNRESOLVED,
    FORBIDDEN_INFERENCE_HISTORICAL_CONCESSION_TO_CURRENT_POLICY,
    FORBIDDEN_INFERENCE_HISTORICAL_LEGAL_SOLUTION_TO_CURRENT_GUIDANCE,
    FORBIDDEN_INFERENCE_HISTORICAL_OVERTIME_HANDLING_TO_CURRENT_RATE,
    FORBIDDEN_INFERENCE_HISTORICAL_PERSON_CAPABILITY_TO_CURRENT_SERVICE,
    FORBIDDEN_INFERENCE_HISTORICAL_PRICE_TO_CURRENT_PRICE,
    FORBIDDEN_INFERENCE_HISTORICAL_ROOM_USE_TO_CURRENT_ACCESS_RIGHT,
    QUERY_CLASS_AUTHORITY_VERIFICATION,
    QUERY_CLASS_MIXED_CURRENT_AND_PRECEDENT,
    QUERY_CLASS_UNRESOLVED_AUTHORITY,
    ContaminationAnnotation,
    LayerExecutionRecord,
    NormalizedResultEnvelope,
    QueryPlan,
)


CURRENT_POLICY_QUERY_CLASSES = frozenset(
    {
        QUERY_CLASS_AUTHORITY_VERIFICATION,
        QUERY_CLASS_MIXED_CURRENT_AND_PRECEDENT,
        QUERY_CLASS_UNRESOLVED_AUTHORITY,
    }
)


def detect_contamination_annotations(
    query_plan: QueryPlan,
    phase4_execution: LayerExecutionRecord,
    phase5_execution: LayerExecutionRecord,
    phase6_execution: LayerExecutionRecord,
) -> tuple[ContaminationAnnotation, ...]:
    phase6_items = tuple(phase6_execution.normalized_items)
    if not phase6_items:
        return ()

    current_authority_items = tuple(phase4_execution.normalized_items + phase5_execution.normalized_items)
    current_authority_item_ids = tuple(item.item_id for item in current_authority_items)
    current_authority_consulted = (
        phase4_execution.requested
        or phase5_execution.requested
        or bool(current_authority_item_ids)
    )

    normalized_query = _normalize(query_plan.query_text)
    if query_plan.query_class not in CURRENT_POLICY_QUERY_CLASSES:
        return ()

    annotations: list[ContaminationAnnotation] = []

    if _matches_any(normalized_query, (" quote ", " price ", " paid ", " charge ", " rate ")) and _matches_any(
        normalized_query,
        (" storage ", " fee ", " price ", " quote ", " charge "),
    ):
        annotations.append(
            _annotation(
                forbidden_inference_type=FORBIDDEN_INFERENCE_HISTORICAL_PRICE_TO_CURRENT_PRICE,
                historical_items=_relevant_historical_items(
                    phase6_items,
                    prefer_historical_value_only=True,
                ),
                current_authority_consulted=current_authority_consulted,
                current_authority_item_ids=current_authority_item_ids,
                prescriptive_use_allowed=False,
                action=(
                    CONTAMINATION_ACTION_CONTEXT_ONLY
                    if current_authority_item_ids
                    else CONTAMINATION_ACTION_UNRESOLVED
                ),
                notes="historical_price_cannot_establish_current_price",
            )
        )

    if _matches_any(normalized_query, (" handled ", " capability ", " offer ", " provide ")) and _matches_any(
        normalized_query,
        (" floral ", " florals ", " service ", " arrangements "),
    ):
        annotations.append(
            _annotation(
                forbidden_inference_type=FORBIDDEN_INFERENCE_HISTORICAL_PERSON_CAPABILITY_TO_CURRENT_SERVICE,
                historical_items=_relevant_historical_items(phase6_items),
                current_authority_consulted=current_authority_consulted,
                current_authority_item_ids=current_authority_item_ids,
                prescriptive_use_allowed=False,
                action=(
                    CONTAMINATION_ACTION_CONTEXT_ONLY
                    if current_authority_item_ids
                    else CONTAMINATION_ACTION_UNRESOLVED
                ),
                notes="historical_person_capability_does_not_establish_current_service_scope",
            )
        )

    if _matches_any(normalized_query, (" discount ", " exposure ", " policy ", " concession ")) and _matches_any(
        normalized_query,
        (" official ", " policy ", " today ", " now ", " current "),
    ):
        annotations.append(
            _annotation(
                forbidden_inference_type=FORBIDDEN_INFERENCE_HISTORICAL_CONCESSION_TO_CURRENT_POLICY,
                historical_items=_relevant_historical_items(
                    phase6_items,
                    prefer_historical_value_only=True,
                ),
                current_authority_consulted=current_authority_consulted,
                current_authority_item_ids=current_authority_item_ids,
                prescriptive_use_allowed=False,
                action=(
                    CONTAMINATION_ACTION_CONTEXT_ONLY
                    if current_authority_item_ids
                    else CONTAMINATION_ACTION_UNRESOLVED
                ),
                notes="historical_concessions_do_not_create_current_discount_policy",
            )
        )

    if _matches_any(normalized_query, (" permit ", " permits ", " compliance ", " legal ", " ade ", " same this year ")) and _matches_any(
        normalized_query,
        (" can we ", " do the same ", " now ", " this year ", " guidance "),
    ):
        annotations.append(
            _annotation(
                forbidden_inference_type=FORBIDDEN_INFERENCE_HISTORICAL_LEGAL_SOLUTION_TO_CURRENT_GUIDANCE,
                historical_items=_relevant_historical_items(phase6_items),
                current_authority_consulted=current_authority_consulted,
                current_authority_item_ids=current_authority_item_ids,
                prescriptive_use_allowed=False,
                action=(
                    CONTAMINATION_ACTION_REQUIRES_CONFIRMATION
                    if current_authority_consulted
                    else CONTAMINATION_ACTION_UNRESOLVED
                ),
                notes="historical_legal_solution_requires_current_verification",
            )
        )

    if _matches_any(normalized_query, (" overtime ", " late build ", " build up ", " run late ")) and _matches_any(
        normalized_query,
        (" rate ", " charge ", " quote ", " price ", " cost "),
    ):
        annotations.append(
            _annotation(
                forbidden_inference_type=FORBIDDEN_INFERENCE_HISTORICAL_OVERTIME_HANDLING_TO_CURRENT_RATE,
                historical_items=_relevant_historical_items(
                    phase6_items,
                    prefer_historical_value_only=True,
                ),
                current_authority_consulted=current_authority_consulted,
                current_authority_item_ids=current_authority_item_ids,
                prescriptive_use_allowed=False,
                action=(
                    CONTAMINATION_ACTION_CONTEXT_ONLY
                    if current_authority_item_ids
                    else CONTAMINATION_ACTION_UNRESOLVED
                ),
                notes="historical_overtime_handling_does_not_create_current_rate_authority",
            )
        )

    if _matches_any(
        normalized_query,
        (
            " back office ",
            " storage room ",
            " extra room ",
            " room access ",
            " access is allowed ",
            " included now ",
        ),
    ):
        annotations.append(
            _annotation(
                forbidden_inference_type=FORBIDDEN_INFERENCE_HISTORICAL_ROOM_USE_TO_CURRENT_ACCESS_RIGHT,
                historical_items=_relevant_historical_items(phase6_items),
                current_authority_consulted=current_authority_consulted,
                current_authority_item_ids=current_authority_item_ids,
                prescriptive_use_allowed=False,
                action=(
                    CONTAMINATION_ACTION_CONTEXT_ONLY
                    if current_authority_item_ids
                    else CONTAMINATION_ACTION_UNRESOLVED
                ),
                notes="historical_room_use_does_not_establish_current_access_right",
            )
        )

    return tuple(_dedupe_annotations(annotations))


def _annotation(
    *,
    forbidden_inference_type: str,
    historical_items: tuple[NormalizedResultEnvelope, ...],
    current_authority_consulted: bool,
    current_authority_item_ids: tuple[str, ...],
    prescriptive_use_allowed: bool,
    action: str,
    notes: str,
) -> ContaminationAnnotation:
    return ContaminationAnnotation(
        forbidden_inference_type=forbidden_inference_type,
        implicated_historical_item_ids=tuple(item.item_id for item in historical_items),
        current_authority_consulted=current_authority_consulted,
        current_authority_item_ids=current_authority_item_ids,
        prescriptive_use_allowed=prescriptive_use_allowed,
        action=action,
        notes=notes,
    )


def _relevant_historical_items(
    items: tuple[NormalizedResultEnvelope, ...],
    *,
    prefer_historical_value_only: bool = False,
) -> tuple[NormalizedResultEnvelope, ...]:
    ranked_items = list(items[:3])
    if prefer_historical_value_only:
        high_risk = [
            item
            for item in items
            if item.layer_payload.get("historical_value_only") is True
        ]
        if high_risk:
            ranked_items = high_risk[:3]
    if not ranked_items:
        return ()
    return tuple(ranked_items)


def _dedupe_annotations(
    annotations: Iterable[ContaminationAnnotation],
) -> list[ContaminationAnnotation]:
    deduped: list[ContaminationAnnotation] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for annotation in annotations:
        key = (
            annotation.forbidden_inference_type,
            annotation.implicated_historical_item_ids,
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(annotation)
    return deduped


def _normalize(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    return f" {normalized} "


def _matches_any(normalized_query: str, patterns: tuple[str, ...]) -> bool:
    return any(pattern in normalized_query for pattern in patterns)


__all__ = ["detect_contamination_annotations"]
