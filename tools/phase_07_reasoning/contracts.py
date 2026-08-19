from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from .validation import (
    Phase7ContractError,
    ensure_allowed_value,
    ensure_bool,
    ensure_json_compatible,
    ensure_non_empty_text,
    ensure_non_negative_int,
    ensure_optional_non_empty_text,
    ensure_positive_int,
    ensure_unique_strings,
)


PHASE_7_CONTEXT_CONTRACT_VERSION = 1
PHASE_7_ANSWER_CONTRACT_VERSION = 1
DEFAULT_PHASE_5_RESULT_LIMIT = 5
DEFAULT_PHASE_6_RESULT_LIMIT = 5

QUERY_CLASS_DETERMINISTIC_CURRENT = "deterministic_current"
QUERY_CLASS_CURRENT_GUIDANCE = "current_guidance"
QUERY_CLASS_PRECEDENT_DISCOVERY = "precedent_discovery"
QUERY_CLASS_MIXED_CURRENT_AND_PRECEDENT = "mixed_current_and_precedent"
QUERY_CLASS_AUTHORITY_VERIFICATION = "authority_verification"
QUERY_CLASS_UNRESOLVED_AUTHORITY = "unresolved_authority"

QUERY_CLASSES = frozenset(
    {
        QUERY_CLASS_DETERMINISTIC_CURRENT,
        QUERY_CLASS_CURRENT_GUIDANCE,
        QUERY_CLASS_PRECEDENT_DISCOVERY,
        QUERY_CLASS_MIXED_CURRENT_AND_PRECEDENT,
        QUERY_CLASS_AUTHORITY_VERIFICATION,
        QUERY_CLASS_UNRESOLVED_AUTHORITY,
    }
)

SOURCE_LAYER_ROLE_DETERMINISTIC_RULE = "deterministic_rule"
SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE = "current_governed_knowledge"
SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT = "historical_precedent"

SOURCE_LAYER_ROLES = frozenset(
    {
        SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
        SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
        SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
    }
)

AUTHORITY_TIER_CURRENT_DETERMINISTIC = "current_deterministic"
AUTHORITY_TIER_CURRENT_GOVERNED = "current_governed"
AUTHORITY_TIER_HISTORICAL_PRECEDENT = "historical_precedent"

AUTHORITY_TIER_CODES = frozenset(
    {
        AUTHORITY_TIER_CURRENT_DETERMINISTIC,
        AUTHORITY_TIER_CURRENT_GOVERNED,
        AUTHORITY_TIER_HISTORICAL_PRECEDENT,
    }
)

AUTHORITY_PRIORITY_BY_TIER = {
    AUTHORITY_TIER_CURRENT_DETERMINISTIC: 1,
    AUTHORITY_TIER_CURRENT_GOVERNED: 2,
    AUTHORITY_TIER_HISTORICAL_PRECEDENT: 3,
}

AUTHORITY_TIER_BY_SOURCE_ROLE = {
    SOURCE_LAYER_ROLE_DETERMINISTIC_RULE: AUTHORITY_TIER_CURRENT_DETERMINISTIC,
    SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE: AUTHORITY_TIER_CURRENT_GOVERNED,
    SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT: AUTHORITY_TIER_HISTORICAL_PRECEDENT,
}

LAYER_ID_PHASE_4 = "phase_4"
LAYER_ID_PHASE_5 = "phase_5"
LAYER_ID_PHASE_6 = "phase_6"

LAYER_IDS = frozenset({LAYER_ID_PHASE_4, LAYER_ID_PHASE_5, LAYER_ID_PHASE_6})

EXECUTION_STATE_NOT_REQUESTED = "not_requested"
EXECUTION_STATE_SUCCESS = "success"
EXECUTION_STATE_FALLBACK = "fallback"
EXECUTION_STATE_UNAVAILABLE = "unavailable"
EXECUTION_STATE_FAILED = "failed"
EXECUTION_STATE_NO_RESULTS = "no_results"

EXECUTION_STATES = frozenset(
    {
        EXECUTION_STATE_NOT_REQUESTED,
        EXECUTION_STATE_SUCCESS,
        EXECUTION_STATE_FALLBACK,
        EXECUTION_STATE_UNAVAILABLE,
        EXECUTION_STATE_FAILED,
        EXECUTION_STATE_NO_RESULTS,
    }
)

REASONING_STATE_RESOLVED = "resolved"
REASONING_STATE_REQUIRES_CONFIRMATION = "requires_confirmation"
REASONING_STATE_INSUFFICIENT_INFORMATION = "insufficient_information"
REASONING_STATE_NO_APPLICABLE_RULE = "no_applicable_rule"
REASONING_STATE_MANUAL_REVIEW_REQUIRED = "manual_review_required"
REASONING_STATE_CURRENT_STATUS_UNKNOWN = "current_status_unknown"
REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY = "insufficient_current_authority"

REASONING_STATES = frozenset(
    {
        REASONING_STATE_RESOLVED,
        REASONING_STATE_REQUIRES_CONFIRMATION,
        REASONING_STATE_INSUFFICIENT_INFORMATION,
        REASONING_STATE_NO_APPLICABLE_RULE,
        REASONING_STATE_MANUAL_REVIEW_REQUIRED,
        REASONING_STATE_CURRENT_STATUS_UNKNOWN,
        REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
    }
)

AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT = "DETERMINISTIC_CURRENT"
AUTHORITY_OUTCOME_CURRENT_GUIDANCE = "CURRENT_GUIDANCE"
AUTHORITY_OUTCOME_HISTORICAL_PRECEDENT = "HISTORICAL_PRECEDENT"
AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY = "MIXED_WITH_CURRENT_PRIORITY"
AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION = "REQUIRES_CONFIRMATION"
AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY = "INSUFFICIENT_CURRENT_AUTHORITY"

AUTHORITY_OUTCOME_CODES = frozenset(
    {
        AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
        AUTHORITY_OUTCOME_CURRENT_GUIDANCE,
        AUTHORITY_OUTCOME_HISTORICAL_PRECEDENT,
        AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY,
        AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION,
        AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
    }
)

CONFLICT_TYPE_A_P4_BEATS_P6 = "TYPE_A_P4_BEATS_P6"
CONFLICT_TYPE_B_P5_BEATS_P6 = "TYPE_B_P5_BEATS_P6"
CONFLICT_TYPE_C_P6_EXISTS_BUT_CURRENT_MISSING = "TYPE_C_P6_EXISTS_BUT_CURRENT_MISSING"
CONFLICT_TYPE_D_P4_REQUIRES_CONFIRMATION = "TYPE_D_P4_REQUIRES_CONFIRMATION"
CONFLICT_TYPE_E_P5_FAILURE_P4_SURVIVES = "TYPE_E_P5_FAILURE_P4_SURVIVES"
CONFLICT_TYPE_F_LIMITED_OR_UNKNOWN_PRECEDENT = "TYPE_F_LIMITED_OR_UNKNOWN_PRECEDENT"
CONFLICT_TYPE_G_CONFIDENTIALITY_ESCALATION = "TYPE_G_CONFIDENTIALITY_ESCALATION"

CONFLICT_TYPE_CODES = frozenset(
    {
        CONFLICT_TYPE_A_P4_BEATS_P6,
        CONFLICT_TYPE_B_P5_BEATS_P6,
        CONFLICT_TYPE_C_P6_EXISTS_BUT_CURRENT_MISSING,
        CONFLICT_TYPE_D_P4_REQUIRES_CONFIRMATION,
        CONFLICT_TYPE_E_P5_FAILURE_P4_SURVIVES,
        CONFLICT_TYPE_F_LIMITED_OR_UNKNOWN_PRECEDENT,
        CONFLICT_TYPE_G_CONFIDENTIALITY_ESCALATION,
    }
)

FORBIDDEN_INFERENCE_HISTORICAL_PRICE_TO_CURRENT_PRICE = "historical_price_to_current_price"
FORBIDDEN_INFERENCE_HISTORICAL_PERSON_CAPABILITY_TO_CURRENT_SERVICE = "historical_person_capability_to_current_service"
FORBIDDEN_INFERENCE_HISTORICAL_CONCESSION_TO_CURRENT_POLICY = "historical_concession_to_current_policy"
FORBIDDEN_INFERENCE_HISTORICAL_LEGAL_SOLUTION_TO_CURRENT_GUIDANCE = "historical_legal_solution_to_current_guidance"
FORBIDDEN_INFERENCE_HISTORICAL_OVERTIME_HANDLING_TO_CURRENT_RATE = "historical_overtime_handling_to_current_rate"
FORBIDDEN_INFERENCE_HISTORICAL_ROOM_USE_TO_CURRENT_ACCESS_RIGHT = "historical_room_use_to_current_access_right"

FORBIDDEN_INFERENCE_TYPE_CODES = frozenset(
    {
        FORBIDDEN_INFERENCE_HISTORICAL_PRICE_TO_CURRENT_PRICE,
        FORBIDDEN_INFERENCE_HISTORICAL_PERSON_CAPABILITY_TO_CURRENT_SERVICE,
        FORBIDDEN_INFERENCE_HISTORICAL_CONCESSION_TO_CURRENT_POLICY,
        FORBIDDEN_INFERENCE_HISTORICAL_LEGAL_SOLUTION_TO_CURRENT_GUIDANCE,
        FORBIDDEN_INFERENCE_HISTORICAL_OVERTIME_HANDLING_TO_CURRENT_RATE,
        FORBIDDEN_INFERENCE_HISTORICAL_ROOM_USE_TO_CURRENT_ACCESS_RIGHT,
    }
)

ROUTING_CONFIDENCE_HIGH = "high"
ROUTING_CONFIDENCE_MEDIUM = "medium"
ROUTING_CONFIDENCE_LOW = "low"

ROUTING_CONFIDENCE_CODES = frozenset(
    {ROUTING_CONFIDENCE_HIGH, ROUTING_CONFIDENCE_MEDIUM, ROUTING_CONFIDENCE_LOW}
)

PHASE_4_DOMAIN_BOOKING_FEE = "booking_fee"
PHASE_4_DOMAIN_PAYMENT = "payment"
PHASE_4_DOMAIN_EXPEDITED_SURCHARGE = "expedited_surcharge"
PHASE_4_DOMAIN_CANCELLATION = "cancellation"
PHASE_4_DOMAIN_CAPACITY = "capacity"
PHASE_4_DOMAIN_SPACE_ACCESS = "space_access"
PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS = "operational_requirements"
PHASE_4_DOMAIN_CATERING_SUPPLIER = "catering_supplier"
PHASE_4_DOMAIN_TECHNICAL_INVENTORY = "technical_inventory"
PHASE_4_DOMAIN_TECHNICAL_CAPABILITY = "technical_capability"
PHASE_4_DOMAIN_SERVICE_RULES = "service_rules"
PHASE_4_DOMAIN_FACILITATOR_REQUIREMENTS = "facilitator_requirements"

PHASE_4_DOMAIN_CODES = frozenset(
    {
        PHASE_4_DOMAIN_BOOKING_FEE,
        PHASE_4_DOMAIN_PAYMENT,
        PHASE_4_DOMAIN_EXPEDITED_SURCHARGE,
        PHASE_4_DOMAIN_CANCELLATION,
        PHASE_4_DOMAIN_CAPACITY,
        PHASE_4_DOMAIN_SPACE_ACCESS,
        PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS,
        PHASE_4_DOMAIN_CATERING_SUPPLIER,
        PHASE_4_DOMAIN_TECHNICAL_INVENTORY,
        PHASE_4_DOMAIN_TECHNICAL_CAPABILITY,
        PHASE_4_DOMAIN_SERVICE_RULES,
        PHASE_4_DOMAIN_FACILITATOR_REQUIREMENTS,
    }
)

CONFIDENTIALITY_LEVEL_EXTERNALLY_SHAREABLE = "externally_shareable"
CONFIDENTIALITY_LEVEL_INTERNAL = "internal"
CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE = "commercially_sensitive"
CONFIDENTIALITY_LEVEL_RESTRICTED = "restricted"

CONFIDENTIALITY_LEVEL_CODES = frozenset(
    {
        CONFIDENTIALITY_LEVEL_EXTERNALLY_SHAREABLE,
        CONFIDENTIALITY_LEVEL_INTERNAL,
        CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE,
        CONFIDENTIALITY_LEVEL_RESTRICTED,
    }
)

PERSONAL_INFORMATION_STATUS_YES = "yes"
PERSONAL_INFORMATION_STATUS_NO = "no"
PERSONAL_INFORMATION_STATUS_UNKNOWN = "unknown"

PERSONAL_INFORMATION_STATUS_CODES = frozenset(
    {
        PERSONAL_INFORMATION_STATUS_YES,
        PERSONAL_INFORMATION_STATUS_NO,
        PERSONAL_INFORMATION_STATUS_UNKNOWN,
    }
)

SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"

SEVERITY_CODES = frozenset({SEVERITY_LOW, SEVERITY_MEDIUM, SEVERITY_HIGH})

CONTAMINATION_ACTION_BLOCKED = "blocked"
CONTAMINATION_ACTION_CONTEXT_ONLY = "context_only"
CONTAMINATION_ACTION_REQUIRES_CONFIRMATION = "requires_confirmation"
CONTAMINATION_ACTION_UNRESOLVED = "unresolved"

CONTAMINATION_ACTION_CODES = frozenset(
    {
        CONTAMINATION_ACTION_BLOCKED,
        CONTAMINATION_ACTION_CONTEXT_ONLY,
        CONTAMINATION_ACTION_REQUIRES_CONFIRMATION,
        CONTAMINATION_ACTION_UNRESOLVED,
    }
)

GENERATION_BOUNDARY_INTERNAL = "internal_generation"

GENERATION_BOUNDARY_CODES = frozenset({GENERATION_BOUNDARY_INTERNAL})

GENERATION_DECISION_ALLOWED = "allowed"
GENERATION_DECISION_ALLOWED_WITH_RESTRICTIONS = "allowed_with_restrictions"
GENERATION_DECISION_BLOCKED = "blocked"

GENERATION_DECISION_CODES = frozenset(
    {
        GENERATION_DECISION_ALLOWED,
        GENERATION_DECISION_ALLOWED_WITH_RESTRICTIONS,
        GENERATION_DECISION_BLOCKED,
    }
)

GENERATOR_SAFE_VISIBILITY_VISIBLE = "visible"
GENERATOR_SAFE_VISIBILITY_DE_IDENTIFIED = "de_identified"
GENERATOR_SAFE_VISIBILITY_SUPPRESSED = "suppressed"

GENERATOR_SAFE_VISIBILITY_CODES = frozenset(
    {
        GENERATOR_SAFE_VISIBILITY_VISIBLE,
        GENERATOR_SAFE_VISIBILITY_DE_IDENTIFIED,
        GENERATOR_SAFE_VISIBILITY_SUPPRESSED,
    }
)

GENERATOR_ALLOWED_ACTION_SYNTHESIZE = "synthesize"
GENERATOR_ALLOWED_ACTION_EXPLAIN = "explain"
GENERATOR_ALLOWED_ACTION_COMPARE = "compare"
GENERATOR_ALLOWED_ACTION_EXPRESS_UNCERTAINTY = "express_uncertainty"

GENERATOR_ALLOWED_ACTIONS = frozenset(
    {
        GENERATOR_ALLOWED_ACTION_SYNTHESIZE,
        GENERATOR_ALLOWED_ACTION_EXPLAIN,
        GENERATOR_ALLOWED_ACTION_COMPARE,
        GENERATOR_ALLOWED_ACTION_EXPRESS_UNCERTAINTY,
    }
)

GENERATOR_FORBIDDEN_ACTION_INDEPENDENT_RETRIEVAL = "independent_retrieval"
GENERATOR_FORBIDDEN_ACTION_INVENT_DETERMINISTIC_VALUES = "invent_deterministic_values"
GENERATOR_FORBIDDEN_ACTION_PROMOTE_PRECEDENT = "promote_precedent"
GENERATOR_FORBIDDEN_ACTION_OVERRIDE_CONFLICTS = "override_conflicts"
GENERATOR_FORBIDDEN_ACTION_ERASE_CONFIRMATION_REQUIREMENTS = "erase_confirmation_requirements"
GENERATOR_FORBIDDEN_ACTION_FILL_AUTHORITY_GAPS = "fill_authority_gaps"

GENERATOR_FORBIDDEN_ACTIONS = frozenset(
    {
        GENERATOR_FORBIDDEN_ACTION_INDEPENDENT_RETRIEVAL,
        GENERATOR_FORBIDDEN_ACTION_INVENT_DETERMINISTIC_VALUES,
        GENERATOR_FORBIDDEN_ACTION_PROMOTE_PRECEDENT,
        GENERATOR_FORBIDDEN_ACTION_OVERRIDE_CONFLICTS,
        GENERATOR_FORBIDDEN_ACTION_ERASE_CONFIRMATION_REQUIREMENTS,
        GENERATOR_FORBIDDEN_ACTION_FILL_AUTHORITY_GAPS,
    }
)

ANSWER_MODE_AUTHORITATIVE_CURRENT = "authoritative_current"
ANSWER_MODE_CURRENT_WITH_HISTORICAL_CONTEXT = "current_with_historical_context"
ANSWER_MODE_HISTORICAL_DESCRIPTIVE = "historical_descriptive"
ANSWER_MODE_CONFIRMATION_REQUIRED = "confirmation_required"
ANSWER_MODE_INSUFFICIENT_CURRENT_AUTHORITY = "insufficient_current_authority"
ANSWER_MODE_BLOCKED = "blocked"

ANSWER_MODE_CODES = frozenset(
    {
        ANSWER_MODE_AUTHORITATIVE_CURRENT,
        ANSWER_MODE_CURRENT_WITH_HISTORICAL_CONTEXT,
        ANSWER_MODE_HISTORICAL_DESCRIPTIVE,
        ANSWER_MODE_CONFIRMATION_REQUIRED,
        ANSWER_MODE_INSUFFICIENT_CURRENT_AUTHORITY,
        ANSWER_MODE_BLOCKED,
    }
)

ANSWER_RESULT_STATUS_COMPLETED = "completed"
ANSWER_RESULT_STATUS_BLOCKED = "blocked"
ANSWER_RESULT_STATUS_FAILED = "failed"

ANSWER_RESULT_STATUS_CODES = frozenset(
    {
        ANSWER_RESULT_STATUS_COMPLETED,
        ANSWER_RESULT_STATUS_BLOCKED,
        ANSWER_RESULT_STATUS_FAILED,
    }
)

ROUTING_AMBIGUITY_BEHAVIOR_BROADEN_CURRENT_AUTHORITY_FIRST = "broaden_current_authority_first"
ROUTING_AMBIGUITY_BEHAVIOR_CODES = frozenset({ROUTING_AMBIGUITY_BEHAVIOR_BROADEN_CURRENT_AUTHORITY_FIRST})


def authority_tier_for_source_role(source_layer_role: str) -> str:
    ensure_allowed_value("source_layer_role", source_layer_role, SOURCE_LAYER_ROLES)
    return AUTHORITY_TIER_BY_SOURCE_ROLE[source_layer_role]


def authority_priority_for_tier(authority_tier_code: str) -> int:
    ensure_allowed_value("authority_tier_code", authority_tier_code, AUTHORITY_TIER_CODES)
    return AUTHORITY_PRIORITY_BY_TIER[authority_tier_code]


def phase4_default_sensitivity() -> SensitivityEnvelope:
    return SensitivityEnvelope(
        confidentiality_level=CONFIDENTIALITY_LEVEL_INTERNAL,
        personal_information_status=PERSONAL_INFORMATION_STATUS_UNKNOWN,
        de_identification_required=False,
        generation_allowed=True,
        generation_restriction_reason=None,
        native_sensitivity_payload={},
    )


@dataclass(frozen=True)
class ContractBase:
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=True)


@dataclass(frozen=True)
class QueryContext(ContractBase):
    query_text: str

    def __post_init__(self) -> None:
        ensure_non_empty_text("query_text", self.query_text)


@dataclass(frozen=True)
class Phase4RoutingIntent(ContractBase):
    required: bool
    domains: tuple[str, ...]
    domain_inputs: dict[str, dict[str, Any]] = field(default_factory=dict)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        ensure_bool("required", self.required)
        ensure_unique_strings("domains", self.domains)
        for domain in self.domains:
            ensure_allowed_value("phase_4 domain", domain, PHASE_4_DOMAIN_CODES)
        if self.required and not self.domains:
            raise Phase7ContractError(
                error_category="missing_required_field",
                safe_message="phase_4 required plans must include at least one domain.",
            )
        for domain, payload in self.domain_inputs.items():
            ensure_allowed_value("domain_inputs key", domain, PHASE_4_DOMAIN_CODES)
            if domain not in self.domains:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=f"phase_4 domain_inputs may only reference declared domains: {domain}.",
                )
            ensure_json_compatible(f"domain_inputs.{domain}", payload)
        for reason_code in self.reason_codes:
            ensure_non_empty_text("reason_code", reason_code)


@dataclass(frozen=True)
class Phase5FilterIntent(ContractBase):
    document_code: str | None = None
    category_code: str | None = None
    rental_type_code: str | None = None

    def __post_init__(self) -> None:
        ensure_optional_non_empty_text("document_code", self.document_code)
        ensure_optional_non_empty_text("category_code", self.category_code)
        ensure_optional_non_empty_text("rental_type_code", self.rental_type_code)


@dataclass(frozen=True)
class Phase5RoutingIntent(ContractBase):
    required: bool
    needs_guidance: bool
    query_text: str | None
    result_limit: int | None = None
    filters: Phase5FilterIntent = field(default_factory=Phase5FilterIntent)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        ensure_bool("required", self.required)
        ensure_bool("needs_guidance", self.needs_guidance)
        if self.required or self.needs_guidance:
            ensure_optional_non_empty_text("query_text", self.query_text)
            if self.query_text is None:
                raise Phase7ContractError(
                    error_category="missing_required_field",
                    safe_message="phase_5 intent requires query_text when guidance is requested.",
                )
        elif self.query_text is not None:
            ensure_non_empty_text("query_text", self.query_text)
        if self.result_limit is not None:
            ensure_positive_int("result_limit", self.result_limit)
        for reason_code in self.reason_codes:
            ensure_non_empty_text("reason_code", reason_code)


@dataclass(frozen=True)
class Phase6FilterIntent(ContractBase):
    case_code: str | None = None
    unit_type: str | None = None
    precedent_availability: str | None = None
    precedent_type: str | None = None
    lesson_kind: str | None = None
    historical_value_only: bool | None = None
    contamination_risk_level: str | None = None

    def __post_init__(self) -> None:
        ensure_optional_non_empty_text("case_code", self.case_code)
        ensure_optional_non_empty_text("unit_type", self.unit_type)
        ensure_optional_non_empty_text("precedent_availability", self.precedent_availability)
        ensure_optional_non_empty_text("precedent_type", self.precedent_type)
        ensure_optional_non_empty_text("lesson_kind", self.lesson_kind)
        if self.historical_value_only is not None:
            ensure_bool("historical_value_only", self.historical_value_only)
        ensure_optional_non_empty_text("contamination_risk_level", self.contamination_risk_level)


@dataclass(frozen=True)
class Phase6RoutingIntent(ContractBase):
    required: bool
    query_text: str | None
    result_limit: int | None = None
    filters: Phase6FilterIntent = field(default_factory=Phase6FilterIntent)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        ensure_bool("required", self.required)
        if self.required:
            ensure_optional_non_empty_text("query_text", self.query_text)
            if self.query_text is None:
                raise Phase7ContractError(
                    error_category="missing_required_field",
                    safe_message="phase_6 required intent must include query_text.",
                )
        elif self.query_text is not None:
            ensure_non_empty_text("query_text", self.query_text)
        if self.result_limit is not None:
            ensure_positive_int("result_limit", self.result_limit)
        for reason_code in self.reason_codes:
            ensure_non_empty_text("reason_code", reason_code)


@dataclass(frozen=True)
class QueryPlan(ContractBase):
    query_text: str
    query_class: str
    routing_confidence: str
    ambiguity_flags: tuple[str, ...] = field(default_factory=tuple)
    required_layers: tuple[str, ...] = field(default_factory=tuple)
    optional_layers: tuple[str, ...] = field(default_factory=tuple)
    phase_4: Phase4RoutingIntent | None = None
    phase_5: Phase5RoutingIntent | None = None
    phase_6: Phase6RoutingIntent | None = None
    safety_overrides: tuple[str, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        ensure_non_empty_text("query_text", self.query_text)
        ensure_allowed_value("query_class", self.query_class, QUERY_CLASSES)
        ensure_allowed_value("routing_confidence", self.routing_confidence, ROUTING_CONFIDENCE_CODES)
        ensure_unique_strings("required_layers", self.required_layers)
        ensure_unique_strings("optional_layers", self.optional_layers)
        for layer_id in self.required_layers:
            ensure_allowed_value("required_layers", layer_id, LAYER_IDS)
        for layer_id in self.optional_layers:
            ensure_allowed_value("optional_layers", layer_id, LAYER_IDS)
        if set(self.required_layers).intersection(self.optional_layers):
            raise Phase7ContractError(
                error_category="invalid_value",
                safe_message="required_layers and optional_layers must be disjoint.",
            )
        for flag in self.ambiguity_flags:
            ensure_non_empty_text("ambiguity_flag", flag)
        for override in self.safety_overrides:
            ensure_non_empty_text("safety_override", override)
        for reason_code in self.reason_codes:
            ensure_non_empty_text("reason_code", reason_code)

        self._validate_layer_intent(LAYER_ID_PHASE_4, self.phase_4)
        self._validate_layer_intent(LAYER_ID_PHASE_5, self.phase_5)
        self._validate_layer_intent(LAYER_ID_PHASE_6, self.phase_6)

    def _validate_layer_intent(self, layer_id: str, intent: object | None) -> None:
        is_required = layer_id in self.required_layers
        is_optional = layer_id in self.optional_layers
        if is_required or is_optional:
            if intent is None:
                raise Phase7ContractError(
                    error_category="missing_required_field",
                    safe_message=f"{layer_id} is declared in the query plan but its routing subsection is missing.",
                )
            if not getattr(intent, "required", False) and is_required:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=f"{layer_id} required layer must have required=True in its routing subsection.",
                )
            if getattr(intent, "required", False) and is_optional:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=f"{layer_id} optional layer must not set required=True.",
                )
        elif intent is not None and getattr(intent, "required", False):
            raise Phase7ContractError(
                error_category="invalid_value",
                safe_message=f"{layer_id} routing subsection cannot be required when the layer is absent from required_layers.",
            )


@dataclass(frozen=True)
class StableIdentity(ContractBase):
    primary_code: str | None = None
    secondary_code: str | None = None
    native_identity_payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ensure_optional_non_empty_text("primary_code", self.primary_code)
        ensure_optional_non_empty_text("secondary_code", self.secondary_code)
        ensure_json_compatible("native_identity_payload", self.native_identity_payload)
        if self.primary_code is None and self.secondary_code is None and not self.native_identity_payload:
            raise Phase7ContractError(
                error_category="missing_required_field",
                safe_message="stable_identity must provide at least one code or native identity field.",
            )


@dataclass(frozen=True)
class ExactIdentity(ContractBase):
    primary_id: int | None = None
    version_id: int | None = None
    version_number: int | None = None
    secondary_id: int | str | None = None
    native_identity_payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.primary_id is not None:
            ensure_positive_int("primary_id", self.primary_id)
        if self.version_id is not None:
            ensure_positive_int("version_id", self.version_id)
        if self.version_number is not None:
            ensure_positive_int("version_number", self.version_number)
        if isinstance(self.secondary_id, int):
            ensure_positive_int("secondary_id", self.secondary_id)
        elif self.secondary_id is not None:
            ensure_non_empty_text("secondary_id", self.secondary_id)
        ensure_json_compatible("native_identity_payload", self.native_identity_payload)
        if (
            self.primary_id is None
            and self.version_id is None
            and self.version_number is None
            and self.secondary_id is None
            and not self.native_identity_payload
        ):
            raise Phase7ContractError(
                error_category="missing_required_field",
                safe_message="exact_identity must provide at least one exact identifier field.",
            )


@dataclass(frozen=True)
class ProvenanceEnvelope(ContractBase):
    source_codes: tuple[str, ...] = field(default_factory=tuple)
    source_identifiers: dict[str, Any] = field(default_factory=dict)
    primary_source_locator: str | None = None
    additional_locators: tuple[str, ...] = field(default_factory=tuple)
    source_link_count: int | None = None
    native_provenance_payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ensure_unique_strings("source_codes", self.source_codes)
        for source_code in self.source_codes:
            ensure_non_empty_text("source_code", source_code)
        ensure_json_compatible("source_identifiers", self.source_identifiers)
        ensure_optional_non_empty_text("primary_source_locator", self.primary_source_locator)
        ensure_unique_strings("additional_locators", self.additional_locators)
        for locator in self.additional_locators:
            ensure_non_empty_text("additional_locator", locator)
        if self.source_link_count is not None:
            ensure_non_negative_int("source_link_count", self.source_link_count)
        ensure_json_compatible("native_provenance_payload", self.native_provenance_payload)


@dataclass(frozen=True)
class SensitivityEnvelope(ContractBase):
    confidentiality_level: str
    personal_information_status: str
    de_identification_required: bool
    generation_allowed: bool
    generation_restriction_reason: str | None = None
    native_sensitivity_payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ensure_allowed_value("confidentiality_level", self.confidentiality_level, CONFIDENTIALITY_LEVEL_CODES)
        ensure_allowed_value(
            "personal_information_status",
            self.personal_information_status,
            PERSONAL_INFORMATION_STATUS_CODES,
        )
        ensure_bool("de_identification_required", self.de_identification_required)
        ensure_bool("generation_allowed", self.generation_allowed)
        ensure_optional_non_empty_text("generation_restriction_reason", self.generation_restriction_reason)
        if not self.generation_allowed and self.generation_restriction_reason is None:
            raise Phase7ContractError(
                error_category="missing_required_field",
                safe_message="generation_restriction_reason is required when generation_allowed is false.",
            )
        ensure_json_compatible("native_sensitivity_payload", self.native_sensitivity_payload)


@dataclass(frozen=True)
class RetrievalMetadata(ContractBase):
    retrieval_mode_requested: str | None = None
    retrieval_mode_used: str | None = None
    fallback_used: bool | None = None
    fallback_reason: str | None = None
    rank: int | None = None
    score: float | None = None
    component_scores: dict[str, float] = field(default_factory=dict)
    strategy_code: str | None = None
    native_retrieval_payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ensure_optional_non_empty_text("retrieval_mode_requested", self.retrieval_mode_requested)
        ensure_optional_non_empty_text("retrieval_mode_used", self.retrieval_mode_used)
        if self.fallback_used is not None:
            ensure_bool("fallback_used", self.fallback_used)
        ensure_optional_non_empty_text("fallback_reason", self.fallback_reason)
        if self.rank is not None:
            ensure_positive_int("rank", self.rank)
        if self.score is not None and not isinstance(self.score, (int, float)):
            raise Phase7ContractError(
                error_category="invalid_value",
                safe_message="score must be numeric when supplied.",
            )
        for name, component_score in self.component_scores.items():
            ensure_non_empty_text("component_score key", name)
            if not isinstance(component_score, (int, float)):
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=f"component score {name} must be numeric.",
                )
        ensure_optional_non_empty_text("strategy_code", self.strategy_code)
        ensure_json_compatible("native_retrieval_payload", self.native_retrieval_payload)


@dataclass(frozen=True)
class NormalizedResultEnvelope(ContractBase):
    item_id: str
    source_layer_role: str
    authority_tier_code: str
    authority_priority: int
    stable_identity: StableIdentity
    exact_identity: ExactIdentity
    content_kind: str
    execution_state: str
    reasoning_state: str | None
    summary_text: str | None
    provenance: ProvenanceEnvelope
    sensitivity: SensitivityEnvelope
    retrieval: RetrievalMetadata | None = None
    layer_payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ensure_non_empty_text("item_id", self.item_id)
        ensure_allowed_value("source_layer_role", self.source_layer_role, SOURCE_LAYER_ROLES)
        ensure_allowed_value("authority_tier_code", self.authority_tier_code, AUTHORITY_TIER_CODES)
        ensure_positive_int("authority_priority", self.authority_priority)
        ensure_non_empty_text("content_kind", self.content_kind)
        ensure_allowed_value("execution_state", self.execution_state, EXECUTION_STATES)
        if self.reasoning_state is not None:
            ensure_allowed_value("reasoning_state", self.reasoning_state, REASONING_STATES)
        ensure_optional_non_empty_text("summary_text", self.summary_text)
        ensure_json_compatible("layer_payload", self.layer_payload)
        self._validate_authority_consistency()
        self._validate_execution_state()
        self._validate_retrieval_consistency()

    def _validate_authority_consistency(self) -> None:
        expected_tier = AUTHORITY_TIER_BY_SOURCE_ROLE[self.source_layer_role]
        expected_priority = AUTHORITY_PRIORITY_BY_TIER[expected_tier]
        if self.authority_tier_code != expected_tier:
            raise Phase7ContractError(
                error_category="inconsistent_authority",
                safe_message=(
                    f"{self.source_layer_role} must map to authority_tier_code={expected_tier}, "
                    f"not {self.authority_tier_code}."
                ),
            )
        if self.authority_priority != expected_priority:
            raise Phase7ContractError(
                error_category="inconsistent_authority",
                safe_message=(
                    f"{self.source_layer_role} must map to authority_priority={expected_priority}, "
                    f"not {self.authority_priority}."
                ),
            )

    def _validate_execution_state(self) -> None:
        if self.execution_state not in {EXECUTION_STATE_SUCCESS, EXECUTION_STATE_FALLBACK}:
            raise Phase7ContractError(
                error_category="invalid_value",
                safe_message="normalized result items may only use execution_state success or fallback.",
            )

    def _validate_retrieval_consistency(self) -> None:
        if self.source_layer_role == SOURCE_LAYER_ROLE_DETERMINISTIC_RULE and self.retrieval is not None:
            if self.retrieval.rank is not None or self.retrieval.score is not None:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message="deterministic_rule items must not carry ranked retrieval metadata.",
                )


@dataclass(frozen=True)
class LayerExecutionRecord(ContractBase):
    layer_id: str
    requested: bool
    execution_state: str
    reasoning_state: str | None = None
    fallback_reason: str | None = None
    error_category: str | None = None
    safe_error_message: str | None = None
    result_count: int = 0
    normalized_items: tuple[NormalizedResultEnvelope, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        ensure_allowed_value("layer_id", self.layer_id, LAYER_IDS)
        ensure_bool("requested", self.requested)
        ensure_allowed_value("execution_state", self.execution_state, EXECUTION_STATES)
        if self.reasoning_state is not None:
            ensure_allowed_value("reasoning_state", self.reasoning_state, REASONING_STATES)
        ensure_optional_non_empty_text("fallback_reason", self.fallback_reason)
        ensure_optional_non_empty_text("error_category", self.error_category)
        ensure_optional_non_empty_text("safe_error_message", self.safe_error_message)
        ensure_non_negative_int("result_count", self.result_count)
        if self.result_count != len(self.normalized_items):
            raise Phase7ContractError(
                error_category="invalid_value",
                safe_message="result_count must equal the number of normalized_items.",
            )
        self._validate_requested_state()
        self._validate_item_states()
        self._validate_layer_item_roles()

    def _validate_requested_state(self) -> None:
        if not self.requested and self.execution_state != EXECUTION_STATE_NOT_REQUESTED:
            raise Phase7ContractError(
                error_category="invalid_value",
                safe_message="execution_state must be not_requested when requested is false.",
            )
        if self.requested and self.execution_state == EXECUTION_STATE_NOT_REQUESTED:
            raise Phase7ContractError(
                error_category="invalid_value",
                safe_message="requested layers cannot use execution_state not_requested.",
            )

    def _validate_item_states(self) -> None:
        if self.execution_state in {EXECUTION_STATE_NOT_REQUESTED, EXECUTION_STATE_UNAVAILABLE, EXECUTION_STATE_FAILED, EXECUTION_STATE_NO_RESULTS}:
            if self.normalized_items:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=f"{self.execution_state} layer execution records must not contain normalized items.",
                )
        if self.execution_state == EXECUTION_STATE_FAILED and self.reasoning_state is not None:
            raise Phase7ContractError(
                error_category="invalid_value",
                safe_message="failed layer executions must not report a reasoning_state.",
            )

    def _validate_layer_item_roles(self) -> None:
        expected_role = {
            LAYER_ID_PHASE_4: SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
            LAYER_ID_PHASE_5: SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
            LAYER_ID_PHASE_6: SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
        }[self.layer_id]
        for item in self.normalized_items:
            if item.source_layer_role != expected_role:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=f"{self.layer_id} execution records may only contain {expected_role} items.",
                )


@dataclass(frozen=True)
class ConflictRecord(ContractBase):
    conflict_type_code: str
    controlling_layer: str
    affected_item_ids: tuple[str, ...]
    severity: str
    resolution_action: str
    notes: str | None = None

    def __post_init__(self) -> None:
        ensure_allowed_value("conflict_type_code", self.conflict_type_code, CONFLICT_TYPE_CODES)
        ensure_allowed_value("controlling_layer", self.controlling_layer, LAYER_IDS)
        ensure_unique_strings("affected_item_ids", self.affected_item_ids)
        for item_id in self.affected_item_ids:
            ensure_non_empty_text("affected_item_id", item_id)
        ensure_allowed_value("severity", self.severity, SEVERITY_CODES)
        ensure_non_empty_text("resolution_action", self.resolution_action)
        ensure_optional_non_empty_text("notes", self.notes)


@dataclass(frozen=True)
class ContaminationAnnotation(ContractBase):
    forbidden_inference_type: str
    implicated_historical_item_ids: tuple[str, ...]
    current_authority_consulted: bool
    current_authority_item_ids: tuple[str, ...]
    prescriptive_use_allowed: bool
    action: str
    notes: str | None = None

    def __post_init__(self) -> None:
        ensure_allowed_value("forbidden_inference_type", self.forbidden_inference_type, FORBIDDEN_INFERENCE_TYPE_CODES)
        ensure_unique_strings("implicated_historical_item_ids", self.implicated_historical_item_ids)
        for item_id in self.implicated_historical_item_ids:
            ensure_non_empty_text("implicated_historical_item_id", item_id)
        ensure_bool("current_authority_consulted", self.current_authority_consulted)
        ensure_unique_strings("current_authority_item_ids", self.current_authority_item_ids)
        for item_id in self.current_authority_item_ids:
            ensure_non_empty_text("current_authority_item_id", item_id)
        ensure_bool("prescriptive_use_allowed", self.prescriptive_use_allowed)
        ensure_allowed_value("action", self.action, CONTAMINATION_ACTION_CODES)
        ensure_optional_non_empty_text("notes", self.notes)
        if self.current_authority_consulted is False and self.current_authority_item_ids:
            raise Phase7ContractError(
                error_category="invalid_value",
                safe_message="current_authority_item_ids require current_authority_consulted=true.",
            )


@dataclass(frozen=True)
class UnresolvedAuthorityRecord(ContractBase):
    reasoning_state: str
    topic_or_domain: str
    controlling_layer: str | None = None
    requires_confirmation: bool = False
    requires_manual_review: bool = False
    related_current_item_ids: tuple[str, ...] = field(default_factory=tuple)
    related_historical_item_ids: tuple[str, ...] = field(default_factory=tuple)
    explanation_code: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        ensure_allowed_value(
            "reasoning_state",
            self.reasoning_state,
            {
                REASONING_STATE_REQUIRES_CONFIRMATION,
                REASONING_STATE_MANUAL_REVIEW_REQUIRED,
                REASONING_STATE_INSUFFICIENT_INFORMATION,
                REASONING_STATE_NO_APPLICABLE_RULE,
                REASONING_STATE_CURRENT_STATUS_UNKNOWN,
                REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
            },
        )
        ensure_non_empty_text("topic_or_domain", self.topic_or_domain)
        if self.controlling_layer is not None:
            ensure_allowed_value("controlling_layer", self.controlling_layer, LAYER_IDS)
        ensure_bool("requires_confirmation", self.requires_confirmation)
        ensure_bool("requires_manual_review", self.requires_manual_review)
        ensure_unique_strings("related_current_item_ids", self.related_current_item_ids)
        ensure_unique_strings("related_historical_item_ids", self.related_historical_item_ids)
        for item_id in self.related_current_item_ids:
            ensure_non_empty_text("related_current_item_id", item_id)
        for item_id in self.related_historical_item_ids:
            ensure_non_empty_text("related_historical_item_id", item_id)
        ensure_optional_non_empty_text("explanation_code", self.explanation_code)
        ensure_optional_non_empty_text("notes", self.notes)


@dataclass(frozen=True)
class DegradedRetrievalState(ContractBase):
    any_degradation: bool
    materially_affects_answer_completeness: bool = False
    affected_layers: tuple[str, ...] = field(default_factory=tuple)
    per_layer_execution_states: dict[str, str] = field(default_factory=dict)
    fallback_reasons: dict[str, str] = field(default_factory=dict)
    generator_warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        ensure_bool("any_degradation", self.any_degradation)
        ensure_bool(
            "materially_affects_answer_completeness",
            self.materially_affects_answer_completeness,
        )
        ensure_unique_strings("affected_layers", self.affected_layers)
        for layer_id in self.affected_layers:
            ensure_allowed_value("affected_layer", layer_id, LAYER_IDS)
        for layer_id, execution_state in self.per_layer_execution_states.items():
            ensure_allowed_value("per_layer_execution_states key", layer_id, LAYER_IDS)
            ensure_allowed_value("per_layer_execution_states value", execution_state, EXECUTION_STATES)
        for layer_id, reason in self.fallback_reasons.items():
            ensure_allowed_value("fallback_reasons key", layer_id, LAYER_IDS)
            ensure_non_empty_text("fallback_reason", reason)
        for warning in self.generator_warnings:
            ensure_non_empty_text("generator_warning", warning)
        if not self.any_degradation and (
            self.affected_layers
            or self.per_layer_execution_states
            or self.fallback_reasons
            or self.generator_warnings
        ):
            raise Phase7ContractError(
                error_category="invalid_value",
                safe_message="non-degraded state must not include degraded-layer metadata.",
            )
        if self.any_degradation and not self.affected_layers:
            raise Phase7ContractError(
                error_category="missing_required_field",
                safe_message="degraded retrieval state must name affected layers when any_degradation is true.",
            )


@dataclass(frozen=True)
class ConfidentialityState(ContractBase):
    effective_confidentiality_level: str
    contributing_item_ids: tuple[str, ...]
    personal_information_present: bool
    de_identification_required: bool
    generation_allowed: bool
    generation_restriction_reason: str | None = None
    personal_information_status_summary: str = PERSONAL_INFORMATION_STATUS_NO
    suppressed_item_ids: tuple[str, ...] = field(default_factory=tuple)
    suppression_reasons: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ensure_allowed_value(
            "effective_confidentiality_level",
            self.effective_confidentiality_level,
            CONFIDENTIALITY_LEVEL_CODES,
        )
        ensure_unique_strings("contributing_item_ids", self.contributing_item_ids)
        for item_id in self.contributing_item_ids:
            ensure_non_empty_text("contributing_item_id", item_id)
        ensure_allowed_value(
            "personal_information_status_summary",
            self.personal_information_status_summary,
            PERSONAL_INFORMATION_STATUS_CODES,
        )
        ensure_bool("personal_information_present", self.personal_information_present)
        ensure_bool("de_identification_required", self.de_identification_required)
        ensure_bool("generation_allowed", self.generation_allowed)
        ensure_optional_non_empty_text("generation_restriction_reason", self.generation_restriction_reason)
        ensure_unique_strings("suppressed_item_ids", self.suppressed_item_ids)
        for item_id in self.suppressed_item_ids:
            ensure_non_empty_text("suppressed_item_id", item_id)
        for item_id, reason in self.suppression_reasons.items():
            ensure_non_empty_text("suppression_reasons key", item_id)
            ensure_non_empty_text("suppression reason", reason)
        if not self.generation_allowed and self.generation_restriction_reason is None:
            raise Phase7ContractError(
                error_category="missing_required_field",
                safe_message="generation_restriction_reason is required when generation_allowed is false.",
            )
        if (
            self.personal_information_present
            != (self.personal_information_status_summary == PERSONAL_INFORMATION_STATUS_YES)
        ):
            raise Phase7ContractError(
                error_category="invalid_value",
                safe_message=(
                    "personal_information_present must match "
                    "personal_information_status_summary == 'yes'."
                ),
            )


@dataclass(frozen=True)
class GeneratorSafeGroundingReference(ContractBase):
    reference_id: str
    item_id: str
    source_layer_role: str
    source_codes: tuple[str, ...] = field(default_factory=tuple)
    safe_locator: str | None = None

    def __post_init__(self) -> None:
        ensure_non_empty_text("reference_id", self.reference_id)
        ensure_non_empty_text("item_id", self.item_id)
        ensure_allowed_value("source_layer_role", self.source_layer_role, SOURCE_LAYER_ROLES)
        ensure_unique_strings("source_codes", self.source_codes)
        for source_code in self.source_codes:
            ensure_non_empty_text("source_code", source_code)
        ensure_optional_non_empty_text("safe_locator", self.safe_locator)


@dataclass(frozen=True)
class GeneratorSafeItemProjection(ContractBase):
    item_id: str
    source_layer_role: str
    visibility: str
    generator_summary_text: str | None = None
    safe_source_codes: tuple[str, ...] = field(default_factory=tuple)
    safe_primary_locator: str | None = None
    fields_removed: tuple[str, ...] = field(default_factory=tuple)
    fields_deidentified: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    suppression_reason: str | None = None

    def __post_init__(self) -> None:
        ensure_non_empty_text("item_id", self.item_id)
        ensure_allowed_value("source_layer_role", self.source_layer_role, SOURCE_LAYER_ROLES)
        ensure_allowed_value("visibility", self.visibility, GENERATOR_SAFE_VISIBILITY_CODES)
        ensure_optional_non_empty_text("generator_summary_text", self.generator_summary_text)
        ensure_unique_strings("safe_source_codes", self.safe_source_codes)
        for source_code in self.safe_source_codes:
            ensure_non_empty_text("safe_source_code", source_code)
        ensure_optional_non_empty_text("safe_primary_locator", self.safe_primary_locator)
        ensure_unique_strings("fields_removed", self.fields_removed)
        ensure_unique_strings("fields_deidentified", self.fields_deidentified)
        ensure_unique_strings("warnings", self.warnings)
        for field_name in self.fields_removed:
            ensure_non_empty_text("fields_removed", field_name)
        for field_name in self.fields_deidentified:
            ensure_non_empty_text("fields_deidentified", field_name)
        for warning in self.warnings:
            ensure_non_empty_text("projection_warning", warning)
        ensure_optional_non_empty_text("suppression_reason", self.suppression_reason)
        if self.visibility == GENERATOR_SAFE_VISIBILITY_SUPPRESSED:
            if self.suppression_reason is None:
                raise Phase7ContractError(
                    error_category="missing_required_field",
                    safe_message="suppressed projections require a suppression_reason.",
                )
            if self.generator_summary_text is not None:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message="suppressed projections must not include generator_summary_text.",
                )
        elif self.generator_summary_text is None:
            raise Phase7ContractError(
                error_category="missing_required_field",
                safe_message="visible generator-safe projections require generator_summary_text.",
            )


@dataclass(frozen=True)
class GeneratorSafeContext(ContractBase):
    generation_boundary: str
    generation_decision: str
    projections: tuple[GeneratorSafeItemProjection, ...] = field(default_factory=tuple)
    grounding: tuple[GeneratorSafeGroundingReference, ...] = field(default_factory=tuple)
    blocked_reason: str | None = None
    validation_errors: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        ensure_allowed_value(
            "generation_boundary",
            self.generation_boundary,
            GENERATION_BOUNDARY_CODES,
        )
        ensure_allowed_value(
            "generation_decision",
            self.generation_decision,
            GENERATION_DECISION_CODES,
        )
        ensure_unique_strings(
            "generator_safe projection item_ids",
            tuple(projection.item_id for projection in self.projections),
        )
        ensure_unique_strings(
            "generator_safe grounding reference_ids",
            tuple(reference.reference_id for reference in self.grounding),
        )
        ensure_optional_non_empty_text("blocked_reason", self.blocked_reason)
        ensure_unique_strings("validation_errors", self.validation_errors)
        for error in self.validation_errors:
            ensure_non_empty_text("validation_error", error)
        if self.generation_decision == GENERATION_DECISION_BLOCKED and self.blocked_reason is None:
            raise Phase7ContractError(
                error_category="missing_required_field",
                safe_message="blocked generator-safe contexts require a blocked_reason.",
            )


@dataclass(frozen=True)
class AuthorityResolution(ContractBase):
    overall_outcome_classification: str | None = None
    resolved_current_truth_item_ids: tuple[str, ...] = field(default_factory=tuple)
    current_guidance_item_ids: tuple[str, ...] = field(default_factory=tuple)
    historical_precedent_item_ids: tuple[str, ...] = field(default_factory=tuple)
    conflict_records: tuple[ConflictRecord, ...] = field(default_factory=tuple)
    contamination_annotations: tuple[ContaminationAnnotation, ...] = field(default_factory=tuple)
    unresolved_authority_records: tuple[UnresolvedAuthorityRecord, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.overall_outcome_classification is not None:
            ensure_allowed_value(
                "overall_outcome_classification",
                self.overall_outcome_classification,
                AUTHORITY_OUTCOME_CODES,
            )
        ensure_unique_strings("resolved_current_truth_item_ids", self.resolved_current_truth_item_ids)
        ensure_unique_strings("current_guidance_item_ids", self.current_guidance_item_ids)
        ensure_unique_strings("historical_precedent_item_ids", self.historical_precedent_item_ids)
        for item_id in (
            self.resolved_current_truth_item_ids
            + self.current_guidance_item_ids
            + self.historical_precedent_item_ids
        ):
            ensure_non_empty_text("authority_resolution item_id", item_id)


@dataclass(frozen=True)
class GroundingReference(ContractBase):
    reference_id: str
    item_id: str
    source_layer_role: str
    provenance: ProvenanceEnvelope

    def __post_init__(self) -> None:
        ensure_non_empty_text("reference_id", self.reference_id)
        ensure_non_empty_text("item_id", self.item_id)
        ensure_allowed_value("source_layer_role", self.source_layer_role, SOURCE_LAYER_ROLES)


@dataclass(frozen=True)
class GroundingState(ContractBase):
    references: tuple[GroundingReference, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        ensure_unique_strings("grounding reference_ids", tuple(reference.reference_id for reference in self.references))


@dataclass(frozen=True)
class GeneratorPolicy(ContractBase):
    generation_allowed: bool
    allowed_actions: tuple[str, ...] = field(default_factory=tuple)
    forbidden_actions: tuple[str, ...] = field(default_factory=tuple)
    required_warnings: tuple[str, ...] = field(default_factory=tuple)
    confidentiality_restrictions: tuple[str, ...] = field(default_factory=tuple)
    personal_information_restrictions: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        ensure_bool("generation_allowed", self.generation_allowed)
        ensure_unique_strings("allowed_actions", self.allowed_actions)
        ensure_unique_strings("forbidden_actions", self.forbidden_actions)
        for action in self.allowed_actions:
            ensure_allowed_value("allowed_action", action, GENERATOR_ALLOWED_ACTIONS)
        for action in self.forbidden_actions:
            ensure_allowed_value("forbidden_action", action, GENERATOR_FORBIDDEN_ACTIONS)
        for warning in self.required_warnings:
            ensure_non_empty_text("required_warning", warning)
        for restriction in self.confidentiality_restrictions:
            ensure_non_empty_text("confidentiality_restriction", restriction)
        for restriction in self.personal_information_restrictions:
            ensure_non_empty_text("personal_information_restriction", restriction)


@dataclass(frozen=True)
class UncertaintyState(ContractBase):
    has_unresolved_authority: bool
    unresolved_records: tuple[UnresolvedAuthorityRecord, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        ensure_bool("has_unresolved_authority", self.has_unresolved_authority)
        for note in self.notes:
            ensure_non_empty_text("uncertainty note", note)
        if self.has_unresolved_authority != bool(self.unresolved_records):
            raise Phase7ContractError(
                error_category="invalid_value",
                safe_message="has_unresolved_authority must match the presence of unresolved_records.",
            )


@dataclass(frozen=True)
class Phase7RuntimeConfiguration(ContractBase):
    contract_version: int = PHASE_7_CONTEXT_CONTRACT_VERSION
    phase_5_result_limit: int = DEFAULT_PHASE_5_RESULT_LIMIT
    phase_6_result_limit: int = DEFAULT_PHASE_6_RESULT_LIMIT
    routing_ambiguity_behavior: str = ROUTING_AMBIGUITY_BEHAVIOR_BROADEN_CURRENT_AUTHORITY_FIRST
    enable_current_claim_phase4_override: bool = True
    enable_historical_prescriptive_current_authority_override: bool = True

    def __post_init__(self) -> None:
        ensure_positive_int("contract_version", self.contract_version)
        ensure_positive_int("phase_5_result_limit", self.phase_5_result_limit)
        ensure_positive_int("phase_6_result_limit", self.phase_6_result_limit)
        ensure_allowed_value(
            "routing_ambiguity_behavior",
            self.routing_ambiguity_behavior,
            ROUTING_AMBIGUITY_BEHAVIOR_CODES,
        )
        ensure_bool("enable_current_claim_phase4_override", self.enable_current_claim_phase4_override)
        ensure_bool(
            "enable_historical_prescriptive_current_authority_override",
            self.enable_historical_prescriptive_current_authority_override,
        )


@dataclass(frozen=True)
class ContextSafetyConfiguration(ContractBase):
    generation_boundary: str = GENERATION_BOUNDARY_INTERNAL

    def __post_init__(self) -> None:
        ensure_allowed_value(
            "generation_boundary",
            self.generation_boundary,
            GENERATION_BOUNDARY_CODES,
        )


@dataclass(frozen=True)
class ContextPackage(ContractBase):
    query: QueryContext
    routing_plan: QueryPlan
    layer_execution: tuple[LayerExecutionRecord, ...]
    phase_4_context: tuple[NormalizedResultEnvelope, ...]
    phase_5_context: tuple[NormalizedResultEnvelope, ...]
    phase_6_context: tuple[NormalizedResultEnvelope, ...]
    authority_resolution: AuthorityResolution
    uncertainty_state: UncertaintyState
    confidentiality_state: ConfidentialityState
    degraded_retrieval_state: DegradedRetrievalState
    grounding: GroundingState
    generator_policy: GeneratorPolicy
    generator_safe_context: GeneratorSafeContext | None = None
    context_contract_version: int = PHASE_7_CONTEXT_CONTRACT_VERSION

    def __post_init__(self) -> None:
        ensure_positive_int("context_contract_version", self.context_contract_version)
        if self.query.query_text != self.routing_plan.query_text:
            raise Phase7ContractError(
                error_category="invalid_value",
                safe_message="query.query_text must match routing_plan.query_text.",
            )
        self._validate_layer_execution_uniqueness()
        self._validate_context_roles()
        self._validate_item_ids()
        self._validate_layer_context_alignment()
        self._validate_authority_references()
        self._validate_confidentiality_references()
        self._validate_grounding_references()
        self._validate_generator_safe_context()

    def _validate_layer_execution_uniqueness(self) -> None:
        layer_ids = tuple(record.layer_id for record in self.layer_execution)
        ensure_unique_strings("layer_execution layer_ids", layer_ids)
        for required_layer in LAYER_IDS:
            if required_layer not in layer_ids:
                raise Phase7ContractError(
                    error_category="missing_required_field",
                    safe_message=f"context package must include a layer_execution record for {required_layer}.",
                )

    def _validate_context_roles(self) -> None:
        for item in self.phase_4_context:
            if item.source_layer_role != SOURCE_LAYER_ROLE_DETERMINISTIC_RULE:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message="phase_4_context may only contain deterministic_rule items.",
                )
        for item in self.phase_5_context:
            if item.source_layer_role != SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message="phase_5_context may only contain current_governed_knowledge items.",
                )
        for item in self.phase_6_context:
            if item.source_layer_role != SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message="phase_6_context may only contain historical_precedent items.",
                )

    def _validate_item_ids(self) -> None:
        all_item_ids = tuple(
            item.item_id
            for item in self.phase_4_context + self.phase_5_context + self.phase_6_context
        )
        ensure_unique_strings("context item_ids", all_item_ids)

    def _known_items_by_id(self) -> dict[str, NormalizedResultEnvelope]:
        return {
            item.item_id: item
            for item in self.phase_4_context + self.phase_5_context + self.phase_6_context
        }

    def _validate_layer_context_alignment(self) -> None:
        expected_by_layer = {
            LAYER_ID_PHASE_4: tuple(item.item_id for item in self.phase_4_context),
            LAYER_ID_PHASE_5: tuple(item.item_id for item in self.phase_5_context),
            LAYER_ID_PHASE_6: tuple(item.item_id for item in self.phase_6_context),
        }
        for record in self.layer_execution:
            actual_item_ids = tuple(item.item_id for item in record.normalized_items)
            if actual_item_ids != expected_by_layer[record.layer_id]:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=f"{record.layer_id} context items must match the corresponding layer_execution normalized_items.",
                )

    def _validate_authority_references(self) -> None:
        known_items = self._known_items_by_id()
        known_item_ids = set(known_items)
        for item_id in (
            self.authority_resolution.resolved_current_truth_item_ids
            + self.authority_resolution.current_guidance_item_ids
            + self.authority_resolution.historical_precedent_item_ids
        ):
            if item_id not in known_item_ids:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=f"authority_resolution references unknown item_id: {item_id}.",
                )
        for record in self.authority_resolution.conflict_records:
            for item_id in record.affected_item_ids:
                if item_id not in known_item_ids:
                    raise Phase7ContractError(
                        error_category="invalid_value",
                        safe_message=f"conflict record references unknown item_id: {item_id}.",
                    )
        for annotation in self.authority_resolution.contamination_annotations:
            for item_id in annotation.implicated_historical_item_ids:
                item = known_items.get(item_id)
                if item is None:
                    raise Phase7ContractError(
                        error_category="invalid_value",
                        safe_message=f"contamination annotation references unknown historical item_id: {item_id}.",
                    )
                if item.source_layer_role != SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT:
                    raise Phase7ContractError(
                        error_category="invalid_value",
                        safe_message="contamination annotations may only implicate historical_precedent items.",
                    )
            for item_id in annotation.current_authority_item_ids:
                item = known_items.get(item_id)
                if item is None:
                    raise Phase7ContractError(
                        error_category="invalid_value",
                        safe_message=f"contamination annotation references unknown current-authority item_id: {item_id}.",
                    )
                if item.source_layer_role == SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT:
                    raise Phase7ContractError(
                        error_category="invalid_value",
                        safe_message="current_authority_item_ids may not point to historical_precedent items.",
                    )
        for record in self.authority_resolution.unresolved_authority_records:
            for item_id in record.related_current_item_ids:
                item = known_items.get(item_id)
                if item is None:
                    raise Phase7ContractError(
                        error_category="invalid_value",
                        safe_message=f"unresolved authority record references unknown current item_id: {item_id}.",
                    )
                if item.source_layer_role == SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT:
                    raise Phase7ContractError(
                        error_category="invalid_value",
                        safe_message="related_current_item_ids may not point to historical_precedent items.",
                    )
            for item_id in record.related_historical_item_ids:
                item = known_items.get(item_id)
                if item is None:
                    raise Phase7ContractError(
                        error_category="invalid_value",
                        safe_message=f"unresolved authority record references unknown historical item_id: {item_id}.",
                    )
                if item.source_layer_role != SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT:
                    raise Phase7ContractError(
                        error_category="invalid_value",
                        safe_message="related_historical_item_ids must point to historical_precedent items.",
                    )

    def _validate_confidentiality_references(self) -> None:
        known_item_ids = set(self._known_items_by_id())
        for item_id in self.confidentiality_state.contributing_item_ids:
            if item_id not in known_item_ids:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=f"confidentiality_state references unknown contributing item_id: {item_id}.",
                )
        for item_id in self.confidentiality_state.suppressed_item_ids:
            if item_id not in known_item_ids:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=f"confidentiality_state references unknown suppressed item_id: {item_id}.",
                )
        for item_id in self.confidentiality_state.suppression_reasons:
            if item_id not in self.confidentiality_state.suppressed_item_ids:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message="suppression_reasons keys must also appear in suppressed_item_ids.",
                )

    def _validate_grounding_references(self) -> None:
        known_items = self._known_items_by_id()
        for reference in self.grounding.references:
            item = known_items.get(reference.item_id)
            if item is None:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=f"grounding reference points to unknown item_id: {reference.item_id}.",
                )
            if reference.source_layer_role != item.source_layer_role:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message="grounding reference source_layer_role must match the referenced item.",
                )

    def _validate_generator_safe_context(self) -> None:
        if self.generator_safe_context is None:
            return

        known_items = self._known_items_by_id()
        projection_by_item_id = {
            projection.item_id: projection
            for projection in self.generator_safe_context.projections
        }
        visible_projection_item_ids = {
            projection.item_id
            for projection in self.generator_safe_context.projections
            if projection.visibility != GENERATOR_SAFE_VISIBILITY_SUPPRESSED
        }

        for projection in self.generator_safe_context.projections:
            item = known_items.get(projection.item_id)
            if item is None:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=(
                        "generator_safe_context references unknown projection item_id: "
                        f"{projection.item_id}."
                    ),
                )
            if projection.source_layer_role != item.source_layer_role:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=(
                        "generator-safe projection source_layer_role must match the "
                        "referenced item."
                    ),
                )

        for item_id in self.confidentiality_state.suppressed_item_ids:
            projection = projection_by_item_id.get(item_id)
            if projection is None:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=(
                        "suppressed confidentiality items must appear in "
                        "generator_safe_context projections."
                    ),
                )
            if projection.visibility != GENERATOR_SAFE_VISIBILITY_SUPPRESSED:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=(
                        "suppressed confidentiality items must have suppressed "
                        "generator-safe projections."
                    ),
                )

        for reference in self.generator_safe_context.grounding:
            item = known_items.get(reference.item_id)
            if item is None:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=(
                        "generator_safe_context grounding references unknown item_id: "
                        f"{reference.item_id}."
                    ),
                )
            if reference.source_layer_role != item.source_layer_role:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=(
                        "generator-safe grounding source_layer_role must match the "
                        "referenced item."
                    ),
                )
            if reference.item_id not in visible_projection_item_ids:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=(
                        "generator-safe grounding may reference only generator-visible "
                        "item projections."
                    ),
                )

        context_blocked = (
            self.generator_safe_context.generation_decision
            == GENERATION_DECISION_BLOCKED
        )
        if self.generator_policy.generation_allowed == context_blocked:
            raise Phase7ContractError(
                error_category="invalid_value",
                safe_message=(
                    "generator_policy.generation_allowed must agree with the "
                    "generator_safe_context generation_decision."
                ),
            )
        if self.confidentiality_state.generation_allowed != self.generator_policy.generation_allowed:
            raise Phase7ContractError(
                error_category="invalid_value",
                safe_message=(
                    "confidentiality_state.generation_allowed must match "
                    "generator_policy.generation_allowed."
                ),
            )


@dataclass(frozen=True)
class AnswerClaimFrame(ContractBase):
    claim_id: str
    item_id: str
    source_layer_role: str
    authority_tier_code: str
    claim_text: str
    allowed_grounding_reference_ids: tuple[str, ...] = field(default_factory=tuple)
    required_warning_codes: tuple[str, ...] = field(default_factory=tuple)
    historical_context_only: bool = False
    requires_high_level_only: bool = False
    current_authority_supported: bool = True

    def __post_init__(self) -> None:
        ensure_non_empty_text("claim_id", self.claim_id)
        ensure_non_empty_text("item_id", self.item_id)
        ensure_allowed_value("source_layer_role", self.source_layer_role, SOURCE_LAYER_ROLES)
        ensure_allowed_value("authority_tier_code", self.authority_tier_code, AUTHORITY_TIER_CODES)
        ensure_non_empty_text("claim_text", self.claim_text)
        ensure_unique_strings(
            "allowed_grounding_reference_ids",
            self.allowed_grounding_reference_ids,
        )
        ensure_unique_strings(
            "required_warning_codes",
            self.required_warning_codes,
        )
        ensure_bool("historical_context_only", self.historical_context_only)
        ensure_bool("requires_high_level_only", self.requires_high_level_only)
        ensure_bool("current_authority_supported", self.current_authority_supported)
        expected_tier = authority_tier_for_source_role(self.source_layer_role)
        if self.authority_tier_code != expected_tier:
            raise Phase7ContractError(
                error_category="invalid_value",
                safe_message=(
                    "answer claim frame authority_tier_code must match the "
                    "source_layer_role."
                ),
            )
        if self.source_layer_role == SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT:
            if not self.historical_context_only:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=(
                        "historical answer claim frames must be marked "
                        "historical_context_only."
                    ),
                )
            if self.current_authority_supported:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=(
                        "historical answer claim frames must not assert "
                        "current_authority_supported."
                    ),
                )
        else:
            if self.historical_context_only:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=(
                        "current-authority answer claim frames may not be marked "
                        "historical_context_only."
                    ),
                )
            if not self.current_authority_supported:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=(
                        "current-authority answer claim frames must preserve "
                        "current_authority_supported."
                    ),
                )


@dataclass(frozen=True)
class AnswerGenerationInput(ContractBase):
    query_text: str
    query_class: str
    authority_outcome: str
    answer_mode: str
    generation_boundary: str
    generation_decision: str
    effective_confidentiality_level: str
    de_identification_required: bool
    personal_information_status_summary: str
    confirmation_required: bool
    insufficient_current_authority: bool
    degraded_retrieval_state: DegradedRetrievalState
    generator_policy: GeneratorPolicy
    claim_frames: tuple[AnswerClaimFrame, ...] = field(default_factory=tuple)
    safe_grounding: tuple[GeneratorSafeGroundingReference, ...] = field(default_factory=tuple)
    blocked_reason: str | None = None
    required_warning_codes: tuple[str, ...] = field(default_factory=tuple)
    context_contract_version: int = PHASE_7_CONTEXT_CONTRACT_VERSION
    answer_contract_version: int = PHASE_7_ANSWER_CONTRACT_VERSION

    def __post_init__(self) -> None:
        ensure_non_empty_text("query_text", self.query_text)
        ensure_allowed_value("query_class", self.query_class, QUERY_CLASSES)
        ensure_allowed_value("authority_outcome", self.authority_outcome, AUTHORITY_OUTCOME_CODES)
        ensure_allowed_value("answer_mode", self.answer_mode, ANSWER_MODE_CODES)
        ensure_allowed_value(
            "generation_boundary",
            self.generation_boundary,
            GENERATION_BOUNDARY_CODES,
        )
        ensure_allowed_value(
            "generation_decision",
            self.generation_decision,
            GENERATION_DECISION_CODES,
        )
        ensure_allowed_value(
            "effective_confidentiality_level",
            self.effective_confidentiality_level,
            CONFIDENTIALITY_LEVEL_CODES,
        )
        ensure_bool("de_identification_required", self.de_identification_required)
        ensure_allowed_value(
            "personal_information_status_summary",
            self.personal_information_status_summary,
            PERSONAL_INFORMATION_STATUS_CODES,
        )
        ensure_bool("confirmation_required", self.confirmation_required)
        ensure_bool(
            "insufficient_current_authority",
            self.insufficient_current_authority,
        )
        ensure_optional_non_empty_text("blocked_reason", self.blocked_reason)
        ensure_unique_strings(
            "answer_generation_input claim_ids",
            tuple(frame.claim_id for frame in self.claim_frames),
        )
        ensure_unique_strings(
            "answer_generation_input item_ids",
            tuple(frame.item_id for frame in self.claim_frames),
        )
        ensure_unique_strings(
            "answer_generation_input grounding reference_ids",
            tuple(reference.reference_id for reference in self.safe_grounding),
        )
        ensure_unique_strings("required_warning_codes", self.required_warning_codes)
        ensure_positive_int("context_contract_version", self.context_contract_version)
        ensure_positive_int("answer_contract_version", self.answer_contract_version)

        known_grounding_ids = {
            reference.reference_id for reference in self.safe_grounding
        }
        for frame in self.claim_frames:
            for reference_id in frame.allowed_grounding_reference_ids:
                if reference_id not in known_grounding_ids:
                    raise Phase7ContractError(
                        error_category="invalid_value",
                        safe_message=(
                            "answer claim frames may reference only grounding IDs "
                            "present in safe_grounding."
                        ),
                    )

        if self.generation_decision == GENERATION_DECISION_BLOCKED:
            if self.answer_mode != ANSWER_MODE_BLOCKED:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=(
                        "blocked answer-generation input must use answer_mode=blocked."
                    ),
                )
            if self.blocked_reason is None:
                raise Phase7ContractError(
                    error_category="missing_required_field",
                    safe_message=(
                        "blocked answer-generation input requires a blocked_reason."
                    ),
                )
            if self.claim_frames or self.safe_grounding:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=(
                        "blocked answer-generation input must not expose claim frames "
                        "or safe grounding."
                    ),
                )
        elif self.answer_mode == ANSWER_MODE_BLOCKED:
            raise Phase7ContractError(
                error_category="invalid_value",
                safe_message=(
                    "answer_mode=blocked is valid only when generation_decision is blocked."
                ),
            )


@dataclass(frozen=True)
class AnswerGroundingUse(ContractBase):
    claim_id: str
    reference_id: str
    source_layer_role: str

    def __post_init__(self) -> None:
        ensure_non_empty_text("claim_id", self.claim_id)
        ensure_non_empty_text("reference_id", self.reference_id)
        ensure_allowed_value("source_layer_role", self.source_layer_role, SOURCE_LAYER_ROLES)


@dataclass(frozen=True)
class AnswerResult(ContractBase):
    status: str
    answer_mode: str
    authority_outcome: str
    generation_decision: str
    confirmation_required: bool
    insufficient_current_authority: bool
    degraded_context_present: bool
    materially_affects_answer_completeness: bool
    answer_text: str | None = None
    grounding_uses: tuple[AnswerGroundingUse, ...] = field(default_factory=tuple)
    warning_codes: tuple[str, ...] = field(default_factory=tuple)
    failure_code: str | None = None
    answer_contract_version: int = PHASE_7_ANSWER_CONTRACT_VERSION

    def __post_init__(self) -> None:
        ensure_allowed_value("status", self.status, ANSWER_RESULT_STATUS_CODES)
        ensure_allowed_value("answer_mode", self.answer_mode, ANSWER_MODE_CODES)
        ensure_allowed_value("authority_outcome", self.authority_outcome, AUTHORITY_OUTCOME_CODES)
        ensure_allowed_value(
            "generation_decision",
            self.generation_decision,
            GENERATION_DECISION_CODES,
        )
        ensure_bool("confirmation_required", self.confirmation_required)
        ensure_bool(
            "insufficient_current_authority",
            self.insufficient_current_authority,
        )
        ensure_bool("degraded_context_present", self.degraded_context_present)
        ensure_bool(
            "materially_affects_answer_completeness",
            self.materially_affects_answer_completeness,
        )
        ensure_optional_non_empty_text("answer_text", self.answer_text)
        ensure_unique_strings(
            "answer_result grounding references",
            tuple(use.reference_id for use in self.grounding_uses),
        )
        ensure_unique_strings("answer_result warning_codes", self.warning_codes)
        ensure_optional_non_empty_text("failure_code", self.failure_code)
        ensure_positive_int("answer_contract_version", self.answer_contract_version)
        if self.status == ANSWER_RESULT_STATUS_COMPLETED and self.answer_text is None:
            raise Phase7ContractError(
                error_category="missing_required_field",
                safe_message="completed answer results require answer_text.",
            )
        if self.status != ANSWER_RESULT_STATUS_COMPLETED and self.answer_text is not None:
            raise Phase7ContractError(
                error_category="invalid_value",
                safe_message=(
                    "non-completed answer results must not include answer_text."
                ),
            )
        if self.status != ANSWER_RESULT_STATUS_COMPLETED and self.failure_code is None:
            raise Phase7ContractError(
                error_category="missing_required_field",
                safe_message=(
                    "blocked or failed answer results require a failure_code."
                ),
            )


@dataclass(frozen=True)
class AnswerValidationResult(ContractBase):
    is_valid: bool
    failure_codes: tuple[str, ...] = field(default_factory=tuple)
    warning_codes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        ensure_bool("is_valid", self.is_valid)
        ensure_unique_strings("failure_codes", self.failure_codes)
        ensure_unique_strings("warning_codes", self.warning_codes)
        if self.is_valid and self.failure_codes:
            raise Phase7ContractError(
                error_category="invalid_value",
                safe_message="valid answer validation results must not include failure_codes.",
            )


__all__ = [
    "ANSWER_MODE_AUTHORITATIVE_CURRENT",
    "ANSWER_MODE_BLOCKED",
    "ANSWER_MODE_CODES",
    "ANSWER_MODE_CONFIRMATION_REQUIRED",
    "ANSWER_MODE_CURRENT_WITH_HISTORICAL_CONTEXT",
    "ANSWER_MODE_HISTORICAL_DESCRIPTIVE",
    "ANSWER_MODE_INSUFFICIENT_CURRENT_AUTHORITY",
    "ANSWER_RESULT_STATUS_BLOCKED",
    "ANSWER_RESULT_STATUS_CODES",
    "ANSWER_RESULT_STATUS_COMPLETED",
    "ANSWER_RESULT_STATUS_FAILED",
    "AnswerClaimFrame",
    "AnswerGenerationInput",
    "AnswerGroundingUse",
    "AnswerResult",
    "AnswerValidationResult",
    "AUTHORITY_OUTCOME_CODES",
    "AUTHORITY_OUTCOME_CURRENT_GUIDANCE",
    "AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT",
    "AUTHORITY_OUTCOME_HISTORICAL_PRECEDENT",
    "AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY",
    "AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY",
    "AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION",
    "AUTHORITY_PRIORITY_BY_TIER",
    "AUTHORITY_TIER_BY_SOURCE_ROLE",
    "AUTHORITY_TIER_CODES",
    "AUTHORITY_TIER_CURRENT_DETERMINISTIC",
    "AUTHORITY_TIER_CURRENT_GOVERNED",
    "AUTHORITY_TIER_HISTORICAL_PRECEDENT",
    "AuthorityResolution",
    "CONFIDENTIALITY_LEVEL_CODES",
    "CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE",
    "CONFIDENTIALITY_LEVEL_INTERNAL",
    "CONFIDENTIALITY_LEVEL_RESTRICTED",
    "CONFLICT_TYPE_A_P4_BEATS_P6",
    "CONFLICT_TYPE_B_P5_BEATS_P6",
    "CONFLICT_TYPE_C_P6_EXISTS_BUT_CURRENT_MISSING",
    "CONFLICT_TYPE_CODES",
    "CONFLICT_TYPE_D_P4_REQUIRES_CONFIRMATION",
    "CONFLICT_TYPE_E_P5_FAILURE_P4_SURVIVES",
    "CONFLICT_TYPE_F_LIMITED_OR_UNKNOWN_PRECEDENT",
    "CONFLICT_TYPE_G_CONFIDENTIALITY_ESCALATION",
    "CONTAMINATION_ACTION_BLOCKED",
    "CONTAMINATION_ACTION_CODES",
    "CONTAMINATION_ACTION_CONTEXT_ONLY",
    "CONTAMINATION_ACTION_REQUIRES_CONFIRMATION",
    "CONTAMINATION_ACTION_UNRESOLVED",
    "ContaminationAnnotation",
    "ConflictRecord",
    "ConfidentialityState",
    "ContextPackage",
    "ContextSafetyConfiguration",
    "DEFAULT_PHASE_5_RESULT_LIMIT",
    "DEFAULT_PHASE_6_RESULT_LIMIT",
    "DegradedRetrievalState",
    "EXECUTION_STATE_FAILED",
    "EXECUTION_STATE_FALLBACK",
    "EXECUTION_STATE_NOT_REQUESTED",
    "EXECUTION_STATE_NO_RESULTS",
    "EXECUTION_STATE_SUCCESS",
    "EXECUTION_STATE_UNAVAILABLE",
    "EXECUTION_STATES",
    "ExactIdentity",
    "FORBIDDEN_INFERENCE_HISTORICAL_CONCESSION_TO_CURRENT_POLICY",
    "FORBIDDEN_INFERENCE_HISTORICAL_LEGAL_SOLUTION_TO_CURRENT_GUIDANCE",
    "FORBIDDEN_INFERENCE_HISTORICAL_OVERTIME_HANDLING_TO_CURRENT_RATE",
    "FORBIDDEN_INFERENCE_HISTORICAL_PERSON_CAPABILITY_TO_CURRENT_SERVICE",
    "FORBIDDEN_INFERENCE_HISTORICAL_PRICE_TO_CURRENT_PRICE",
    "FORBIDDEN_INFERENCE_HISTORICAL_ROOM_USE_TO_CURRENT_ACCESS_RIGHT",
    "FORBIDDEN_INFERENCE_TYPE_CODES",
    "GENERATOR_ALLOWED_ACTIONS",
    "GENERATOR_ALLOWED_ACTION_COMPARE",
    "GENERATOR_ALLOWED_ACTION_EXPLAIN",
    "GENERATOR_ALLOWED_ACTION_EXPRESS_UNCERTAINTY",
    "GENERATOR_ALLOWED_ACTION_SYNTHESIZE",
    "GENERATION_BOUNDARY_CODES",
    "GENERATION_BOUNDARY_INTERNAL",
    "GENERATION_DECISION_ALLOWED",
    "GENERATION_DECISION_ALLOWED_WITH_RESTRICTIONS",
    "GENERATION_DECISION_BLOCKED",
    "GENERATION_DECISION_CODES",
    "GENERATOR_FORBIDDEN_ACTIONS",
    "GENERATOR_FORBIDDEN_ACTION_ERASE_CONFIRMATION_REQUIREMENTS",
    "GENERATOR_FORBIDDEN_ACTION_FILL_AUTHORITY_GAPS",
    "GENERATOR_FORBIDDEN_ACTION_INDEPENDENT_RETRIEVAL",
    "GENERATOR_FORBIDDEN_ACTION_INVENT_DETERMINISTIC_VALUES",
    "GENERATOR_FORBIDDEN_ACTION_OVERRIDE_CONFLICTS",
    "GENERATOR_FORBIDDEN_ACTION_PROMOTE_PRECEDENT",
    "GENERATOR_SAFE_VISIBILITY_CODES",
    "GENERATOR_SAFE_VISIBILITY_DE_IDENTIFIED",
    "GENERATOR_SAFE_VISIBILITY_SUPPRESSED",
    "GENERATOR_SAFE_VISIBILITY_VISIBLE",
    "GeneratorPolicy",
    "GeneratorSafeContext",
    "GeneratorSafeGroundingReference",
    "GeneratorSafeItemProjection",
    "GroundingReference",
    "GroundingState",
    "LAYER_ID_PHASE_4",
    "LAYER_ID_PHASE_5",
    "LAYER_ID_PHASE_6",
    "LAYER_IDS",
    "LayerExecutionRecord",
    "NormalizedResultEnvelope",
    "PERSONAL_INFORMATION_STATUS_CODES",
    "PERSONAL_INFORMATION_STATUS_NO",
    "PERSONAL_INFORMATION_STATUS_UNKNOWN",
    "PERSONAL_INFORMATION_STATUS_YES",
    "PHASE_4_DOMAIN_BOOKING_FEE",
    "PHASE_4_DOMAIN_CANCELLATION",
    "PHASE_4_DOMAIN_CAPACITY",
    "PHASE_4_DOMAIN_CATERING_SUPPLIER",
    "PHASE_4_DOMAIN_CODES",
    "PHASE_4_DOMAIN_EXPEDITED_SURCHARGE",
    "PHASE_4_DOMAIN_FACILITATOR_REQUIREMENTS",
    "PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS",
    "PHASE_4_DOMAIN_PAYMENT",
    "PHASE_4_DOMAIN_SERVICE_RULES",
    "PHASE_4_DOMAIN_SPACE_ACCESS",
    "PHASE_4_DOMAIN_TECHNICAL_CAPABILITY",
    "PHASE_4_DOMAIN_TECHNICAL_INVENTORY",
    "PHASE_7_ANSWER_CONTRACT_VERSION",
    "PHASE_7_CONTEXT_CONTRACT_VERSION",
    "Phase4RoutingIntent",
    "Phase5FilterIntent",
    "Phase5RoutingIntent",
    "Phase6FilterIntent",
    "Phase6RoutingIntent",
    "Phase7ContractError",
    "Phase7RuntimeConfiguration",
    "ProvenanceEnvelope",
    "QUERY_CLASS_AUTHORITY_VERIFICATION",
    "QUERY_CLASS_CURRENT_GUIDANCE",
    "QUERY_CLASS_DETERMINISTIC_CURRENT",
    "QUERY_CLASS_MIXED_CURRENT_AND_PRECEDENT",
    "QUERY_CLASS_PRECEDENT_DISCOVERY",
    "QUERY_CLASS_UNRESOLVED_AUTHORITY",
    "QUERY_CLASSES",
    "QueryContext",
    "QueryPlan",
    "REASONING_STATE_CURRENT_STATUS_UNKNOWN",
    "REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY",
    "REASONING_STATE_INSUFFICIENT_INFORMATION",
    "REASONING_STATE_MANUAL_REVIEW_REQUIRED",
    "REASONING_STATE_NO_APPLICABLE_RULE",
    "REASONING_STATE_REQUIRES_CONFIRMATION",
    "REASONING_STATE_RESOLVED",
    "REASONING_STATES",
    "ROUTING_AMBIGUITY_BEHAVIOR_BROADEN_CURRENT_AUTHORITY_FIRST",
    "ROUTING_CONFIDENCE_CODES",
    "ROUTING_CONFIDENCE_HIGH",
    "ROUTING_CONFIDENCE_LOW",
    "ROUTING_CONFIDENCE_MEDIUM",
    "RetrievalMetadata",
    "SEVERITY_CODES",
    "SEVERITY_HIGH",
    "SEVERITY_LOW",
    "SEVERITY_MEDIUM",
    "SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE",
    "SOURCE_LAYER_ROLE_DETERMINISTIC_RULE",
    "SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT",
    "SOURCE_LAYER_ROLES",
    "SensitivityEnvelope",
    "StableIdentity",
    "UncertaintyState",
    "UnresolvedAuthorityRecord",
    "authority_priority_for_tier",
    "authority_tier_for_source_role",
    "phase4_default_sensitivity",
]
