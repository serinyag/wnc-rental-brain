from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .contracts import (
    AUTHORITY_OUTCOME_CODES,
    PHASE_8_PHASE7_WORKFLOW_CONSUMPTION_CONTRACT_LABEL,
    REASONING_PURPOSE_CODES,
    WORKFLOW_REASONING_FRESHNESS_CODES,
    WORKFLOW_REASONING_POSTURE_CODES,
    WorkflowReasoningProjection,
)
from .validation import (
    Phase8ContractError,
    ensure_bool,
    ensure_json_compatible,
    ensure_non_negative_int,
    ensure_non_empty_text,
    ensure_optional_non_empty_text,
    ensure_positive_int,
    ensure_tuple_of_non_empty_text,
)


WORKFLOW_REASONING_EFFECT_CURRENT_TRUTH_AVAILABLE = "current_truth_available"
WORKFLOW_REASONING_EFFECT_CURRENT_GUIDANCE_AVAILABLE = "current_guidance_available"
WORKFLOW_REASONING_EFFECT_HISTORICAL_CONTEXT_AVAILABLE = "historical_context_available"
WORKFLOW_REASONING_EFFECT_CONFIRMATION_REQUIRED = "confirmation_required"
WORKFLOW_REASONING_EFFECT_CURRENT_AUTHORITY_MISSING = "current_authority_missing"
WORKFLOW_REASONING_EFFECT_REVIEW_REQUIRED = "review_required"
WORKFLOW_REASONING_EFFECT_DEGRADED_WARNING = "degraded_warning"
WORKFLOW_REASONING_EFFECT_CONFLICT_PRESENT = "conflict_present"
WORKFLOW_REASONING_EFFECT_CONTAMINATION_WARNING = "contamination_warning"
WORKFLOW_REASONING_EFFECT_REQUIREMENT_CANDIDATE = "requirement_candidate"
WORKFLOW_REASONING_EFFECT_DETERMINISTIC_RESTRICTION = "deterministic_restriction"

WORKFLOW_REASONING_EFFECT_CODES = frozenset(
    {
        WORKFLOW_REASONING_EFFECT_CURRENT_TRUTH_AVAILABLE,
        WORKFLOW_REASONING_EFFECT_CURRENT_GUIDANCE_AVAILABLE,
        WORKFLOW_REASONING_EFFECT_HISTORICAL_CONTEXT_AVAILABLE,
        WORKFLOW_REASONING_EFFECT_CONFIRMATION_REQUIRED,
        WORKFLOW_REASONING_EFFECT_CURRENT_AUTHORITY_MISSING,
        WORKFLOW_REASONING_EFFECT_REVIEW_REQUIRED,
        WORKFLOW_REASONING_EFFECT_DEGRADED_WARNING,
        WORKFLOW_REASONING_EFFECT_CONFLICT_PRESENT,
        WORKFLOW_REASONING_EFFECT_CONTAMINATION_WARNING,
        WORKFLOW_REASONING_EFFECT_REQUIREMENT_CANDIDATE,
        WORKFLOW_REASONING_EFFECT_DETERMINISTIC_RESTRICTION,
    }
)

WORKFLOW_SEMANTIC_STATE_KNOWN_YES = "known_yes"
WORKFLOW_SEMANTIC_STATE_KNOWN_NO = "known_no"
WORKFLOW_SEMANTIC_STATE_KNOWN_CONDITIONAL = "known_conditional"
WORKFLOW_SEMANTIC_STATE_UNKNOWN_INTERNAL = "unknown_internal"
WORKFLOW_SEMANTIC_STATE_MISSING_CLIENT_FACT = "missing_client_fact"

WORKFLOW_SEMANTIC_STATE_CODES = frozenset(
    {
        WORKFLOW_SEMANTIC_STATE_KNOWN_YES,
        WORKFLOW_SEMANTIC_STATE_KNOWN_NO,
        WORKFLOW_SEMANTIC_STATE_KNOWN_CONDITIONAL,
        WORKFLOW_SEMANTIC_STATE_UNKNOWN_INTERNAL,
        WORKFLOW_SEMANTIC_STATE_MISSING_CLIENT_FACT,
    }
)

PHASE7_CONSUMPTION_STATUS_CONSUMED = "consumed"
PHASE7_CONSUMPTION_STATUS_DUPLICATE = "duplicate"
PHASE7_CONSUMPTION_STATUS_FAILED = "failed"

PHASE7_CONSUMPTION_STATUS_CODES = frozenset(
    {
        PHASE7_CONSUMPTION_STATUS_CONSUMED,
        PHASE7_CONSUMPTION_STATUS_DUPLICATE,
        PHASE7_CONSUMPTION_STATUS_FAILED,
    }
)

PHASE7_CONSUMPTION_FAILURE_CASE_NOT_FOUND = "case_not_found"
PHASE7_CONSUMPTION_FAILURE_STALE_CASE_REVISION = "stale_case_revision"
PHASE7_CONSUMPTION_FAILURE_UNSUPPORTED_PHASE7_CONTRACT = "unsupported_phase7_contract"
PHASE7_CONSUMPTION_FAILURE_INVALID_CONTEXT_PACKAGE = "invalid_context_package"
PHASE7_CONSUMPTION_FAILURE_AUTHORITY_RESOLUTION_MISSING = "authority_resolution_missing"
PHASE7_CONSUMPTION_FAILURE_INVALID_LAYER_IDENTITY = "invalid_layer_identity"
PHASE7_CONSUMPTION_FAILURE_INVALID_GROUNDING = "invalid_grounding"
PHASE7_CONSUMPTION_FAILURE_PROJECTION_CONFLICT = "projection_conflict"
PHASE7_CONSUMPTION_FAILURE_PERSISTENCE_FAILURE = "persistence_failure"

PHASE7_CONSUMPTION_FAILURE_CODES = frozenset(
    {
        PHASE7_CONSUMPTION_FAILURE_CASE_NOT_FOUND,
        PHASE7_CONSUMPTION_FAILURE_STALE_CASE_REVISION,
        PHASE7_CONSUMPTION_FAILURE_UNSUPPORTED_PHASE7_CONTRACT,
        PHASE7_CONSUMPTION_FAILURE_INVALID_CONTEXT_PACKAGE,
        PHASE7_CONSUMPTION_FAILURE_AUTHORITY_RESOLUTION_MISSING,
        PHASE7_CONSUMPTION_FAILURE_INVALID_LAYER_IDENTITY,
        PHASE7_CONSUMPTION_FAILURE_INVALID_GROUNDING,
        PHASE7_CONSUMPTION_FAILURE_PROJECTION_CONFLICT,
        PHASE7_CONSUMPTION_FAILURE_PERSISTENCE_FAILURE,
    }
)


@dataclass(frozen=True)
class WorkflowReasoningPosture:
    posture_code: str
    authority_outcome_classification: str
    deterministic_use_allowed: bool
    review_required: bool
    blocked_for_current_decision: bool
    confirmation_required: bool
    historical_context_only: bool
    revalidation_required: bool = False

    def __post_init__(self) -> None:
        if self.posture_code not in WORKFLOW_REASONING_POSTURE_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="posture_code must be one of the supported workflow reasoning postures.",
            )
        if self.authority_outcome_classification not in AUTHORITY_OUTCOME_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="authority_outcome_classification must be a supported Phase 7 authority outcome.",
            )
        ensure_bool("deterministic_use_allowed", self.deterministic_use_allowed)
        ensure_bool("review_required", self.review_required)
        ensure_bool("blocked_for_current_decision", self.blocked_for_current_decision)
        ensure_bool("confirmation_required", self.confirmation_required)
        ensure_bool("historical_context_only", self.historical_context_only)
        ensure_bool("revalidation_required", self.revalidation_required)


@dataclass(frozen=True)
class WorkflowReasoningEffect:
    effect_type_code: str
    rental_case_id: int
    reasoning_purpose: str
    source_case_revision: int
    authority_outcome_classification: str
    source_projection_identity_key: str
    blocking_relevance: bool
    domain_scope_code: str | None = None
    related_code: str | None = None
    related_item_ids: tuple[str, ...] = ()
    detail_payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.effect_type_code not in WORKFLOW_REASONING_EFFECT_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="effect_type_code must be one of the supported workflow reasoning effect types.",
            )
        ensure_positive_int("rental_case_id", self.rental_case_id)
        if self.reasoning_purpose not in REASONING_PURPOSE_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="reasoning_purpose must be a supported workflow reasoning purpose.",
            )
        ensure_non_negative_int("source_case_revision", self.source_case_revision)
        if self.authority_outcome_classification not in AUTHORITY_OUTCOME_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="authority_outcome_classification must be a supported Phase 7 authority outcome.",
            )
        ensure_non_empty_text("source_projection_identity_key", self.source_projection_identity_key)
        ensure_bool("blocking_relevance", self.blocking_relevance)
        ensure_optional_non_empty_text("domain_scope_code", self.domain_scope_code)
        ensure_optional_non_empty_text("related_code", self.related_code)
        ensure_tuple_of_non_empty_text("related_item_ids", self.related_item_ids)
        ensure_json_compatible("detail_payload", self.detail_payload)


@dataclass(frozen=True)
class Phase7ConsumptionResult:
    status: str
    projection_freshness_status: str
    projection: WorkflowReasoningProjection | None = None
    posture: WorkflowReasoningPosture | None = None
    workflow_effects: tuple[WorkflowReasoningEffect, ...] = ()
    duplicate_projection: bool = False
    failure_codes: tuple[str, ...] = ()
    phase_8_consumption_contract_label: str = PHASE_8_PHASE7_WORKFLOW_CONSUMPTION_CONTRACT_LABEL

    def __post_init__(self) -> None:
        if self.status not in PHASE7_CONSUMPTION_STATUS_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="status must be one of the supported Phase 8 consumption result states.",
            )
        if self.projection_freshness_status not in WORKFLOW_REASONING_FRESHNESS_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="projection_freshness_status must be a supported workflow reasoning freshness code.",
            )
        if self.projection is not None and not isinstance(self.projection, WorkflowReasoningProjection):
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="projection must be a WorkflowReasoningProjection when provided.",
            )
        if self.posture is not None and not isinstance(self.posture, WorkflowReasoningPosture):
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="posture must be a WorkflowReasoningPosture when provided.",
            )
        if not isinstance(self.workflow_effects, tuple):
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="workflow_effects must be a tuple of WorkflowReasoningEffect values.",
            )
        for index, effect in enumerate(self.workflow_effects):
            if not isinstance(effect, WorkflowReasoningEffect):
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"workflow_effects[{index}] must be a WorkflowReasoningEffect.",
                )
        ensure_bool("duplicate_projection", self.duplicate_projection)
        ensure_tuple_of_non_empty_text("failure_codes", self.failure_codes)
        for code in self.failure_codes:
            if code not in PHASE7_CONSUMPTION_FAILURE_CODES:
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"failure_codes contains unsupported code: {code}.",
                )
        ensure_non_empty_text(
            "phase_8_consumption_contract_label",
            self.phase_8_consumption_contract_label,
        )
        if self.status in {PHASE7_CONSUMPTION_STATUS_CONSUMED, PHASE7_CONSUMPTION_STATUS_DUPLICATE}:
            if self.projection is None or self.posture is None:
                raise Phase8ContractError(
                    error_category="missing_value",
                    safe_message="successful consumption results require projection and posture.",
                )


def projection_semantic_state_code(projection: WorkflowReasoningProjection) -> str:
    semantic_state = projection.degraded_retrieval_summary.get("semantic_state_code")
    if semantic_state in WORKFLOW_SEMANTIC_STATE_CODES:
        return semantic_state

    if projection.reasoning_state_code == "requires_confirmation":
        return WORKFLOW_SEMANTIC_STATE_KNOWN_CONDITIONAL
    if projection.reasoning_state_code in {
        "insufficient_information",
        "no_applicable_rule",
        "manual_review_required",
        "current_status_unknown",
        "insufficient_current_authority",
    }:
        return WORKFLOW_SEMANTIC_STATE_UNKNOWN_INTERNAL
    return WORKFLOW_SEMANTIC_STATE_KNOWN_YES
