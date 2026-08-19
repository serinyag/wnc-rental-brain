from __future__ import annotations

from .contracts import (
    CONFIDENTIALITY_LEVEL_CODES,
    CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE,
    CONFIDENTIALITY_LEVEL_EXTERNALLY_SHAREABLE,
    CONFIDENTIALITY_LEVEL_INTERNAL,
    CONFIDENTIALITY_LEVEL_RESTRICTED,
    PERSONAL_INFORMATION_STATUS_NO,
    PERSONAL_INFORMATION_STATUS_UNKNOWN,
    PERSONAL_INFORMATION_STATUS_YES,
    SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
    AuthorityResolution,
    ConfidentialityState,
    NormalizedResultEnvelope,
)


CONFIDENTIALITY_RANK = {
    CONFIDENTIALITY_LEVEL_EXTERNALLY_SHAREABLE: 0,
    CONFIDENTIALITY_LEVEL_INTERNAL: 1,
    CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE: 2,
    CONFIDENTIALITY_LEVEL_RESTRICTED: 3,
}

SUPPRESSION_REASON_RESTRICTED_HISTORICAL = "restricted_historical_detail_suppressed"
SUPPRESSION_REASON_PI_BEARING = "pi_bearing_detail_suppressed"
SUPPRESSION_REASON_PI_BEARING_RESTRICTED_HISTORICAL = (
    "pi_bearing_restricted_historical_detail_suppressed"
)
SUPPRESSION_REASON_SOURCE_GENERATION_PROHIBITED = "source_generation_prohibited"
GENERATION_RESTRICTION_MATERIAL_SOURCE_BLOCK = (
    "material_context_source_generation_restricted"
)


def finalize_confidentiality_state(
    *,
    authority_resolution: AuthorityResolution,
    phase_4_context: tuple[NormalizedResultEnvelope, ...],
    phase_5_context: tuple[NormalizedResultEnvelope, ...],
    phase_6_context: tuple[NormalizedResultEnvelope, ...],
) -> ConfidentialityState:
    items = phase_4_context + phase_5_context + phase_6_context
    if not items:
        return ConfidentialityState(
            effective_confidentiality_level=CONFIDENTIALITY_LEVEL_INTERNAL,
            contributing_item_ids=(),
            personal_information_present=False,
            de_identification_required=False,
            generation_allowed=True,
            generation_restriction_reason=None,
            suppressed_item_ids=(),
            suppression_reasons={},
        )

    effective_level = max(
        (
            item.sensitivity.confidentiality_level
            for item in items
            if item.sensitivity.confidentiality_level in CONFIDENTIALITY_LEVEL_CODES
        ),
        key=lambda level: CONFIDENTIALITY_RANK[level],
        default=CONFIDENTIALITY_LEVEL_INTERNAL,
    )
    personal_information_present = any(
        item.sensitivity.personal_information_status == PERSONAL_INFORMATION_STATUS_YES
        for item in items
    )
    if personal_information_present:
        personal_information_status_summary = PERSONAL_INFORMATION_STATUS_YES
    elif any(
        item.sensitivity.personal_information_status == PERSONAL_INFORMATION_STATUS_UNKNOWN
        for item in items
    ):
        personal_information_status_summary = PERSONAL_INFORMATION_STATUS_UNKNOWN
    else:
        personal_information_status_summary = PERSONAL_INFORMATION_STATUS_NO
    de_identification_required = any(
        item.sensitivity.de_identification_required for item in items
    )

    suppressed_item_ids: list[str] = []
    suppression_reasons: dict[str, str] = {}
    source_generation_blocked_item_ids: set[str] = set()

    for item in items:
        suppression_reason = _suppression_reason_for_item(item)
        if suppression_reason is None:
            continue
        suppressed_item_ids.append(item.item_id)
        suppression_reasons[item.item_id] = suppression_reason
        if suppression_reason == SUPPRESSION_REASON_SOURCE_GENERATION_PROHIBITED:
            source_generation_blocked_item_ids.add(item.item_id)

    material_item_ids = _material_item_ids(authority_resolution, items)
    generation_allowed = True
    generation_restriction_reason = None
    if material_item_ids and material_item_ids.issubset(source_generation_blocked_item_ids):
        generation_allowed = False
        generation_restriction_reason = GENERATION_RESTRICTION_MATERIAL_SOURCE_BLOCK

    return ConfidentialityState(
        effective_confidentiality_level=effective_level,
        contributing_item_ids=tuple(item.item_id for item in items),
        personal_information_present=personal_information_present,
        de_identification_required=de_identification_required,
        generation_allowed=generation_allowed,
        generation_restriction_reason=generation_restriction_reason,
        personal_information_status_summary=personal_information_status_summary,
        suppressed_item_ids=tuple(dict.fromkeys(suppressed_item_ids)),
        suppression_reasons=suppression_reasons,
    )


def _suppression_reason_for_item(item: NormalizedResultEnvelope) -> str | None:
    if not item.sensitivity.generation_allowed:
        return item.sensitivity.generation_restriction_reason or SUPPRESSION_REASON_SOURCE_GENERATION_PROHIBITED

    is_pi_bearing = (
        item.sensitivity.personal_information_status == PERSONAL_INFORMATION_STATUS_YES
    )
    is_restricted_historical = (
        item.source_layer_role == SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT
        and item.sensitivity.confidentiality_level == CONFIDENTIALITY_LEVEL_RESTRICTED
    )
    if is_pi_bearing and is_restricted_historical:
        return SUPPRESSION_REASON_PI_BEARING_RESTRICTED_HISTORICAL
    if is_pi_bearing:
        return SUPPRESSION_REASON_PI_BEARING
    if is_restricted_historical:
        return SUPPRESSION_REASON_RESTRICTED_HISTORICAL
    return None


def _material_item_ids(
    authority_resolution: AuthorityResolution,
    items: tuple[NormalizedResultEnvelope, ...],
) -> set[str]:
    material_item_ids = set(
        authority_resolution.resolved_current_truth_item_ids
        + authority_resolution.current_guidance_item_ids
        + authority_resolution.historical_precedent_item_ids
    )
    if material_item_ids:
        return material_item_ids
    return {item.item_id for item in items}


__all__ = [
    "GENERATION_RESTRICTION_MATERIAL_SOURCE_BLOCK",
    "SUPPRESSION_REASON_PI_BEARING",
    "SUPPRESSION_REASON_PI_BEARING_RESTRICTED_HISTORICAL",
    "SUPPRESSION_REASON_RESTRICTED_HISTORICAL",
    "SUPPRESSION_REASON_SOURCE_GENERATION_PROHIBITED",
    "finalize_confidentiality_state",
]
