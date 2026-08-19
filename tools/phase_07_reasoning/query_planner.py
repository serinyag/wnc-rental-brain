from __future__ import annotations

import re
from dataclasses import dataclass

from .contracts import (
    DEFAULT_PHASE_5_RESULT_LIMIT,
    DEFAULT_PHASE_6_RESULT_LIMIT,
    LAYER_ID_PHASE_4,
    LAYER_ID_PHASE_5,
    LAYER_ID_PHASE_6,
    PHASE_4_DOMAIN_BOOKING_FEE,
    PHASE_4_DOMAIN_CANCELLATION,
    PHASE_4_DOMAIN_CAPACITY,
    PHASE_4_DOMAIN_CATERING_SUPPLIER,
    PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS,
    PHASE_4_DOMAIN_PAYMENT,
    PHASE_4_DOMAIN_SERVICE_RULES,
    PHASE_4_DOMAIN_SPACE_ACCESS,
    PHASE_4_DOMAIN_TECHNICAL_CAPABILITY,
    PHASE_4_DOMAIN_TECHNICAL_INVENTORY,
    PHASE_4_DOMAIN_FACILITATOR_REQUIREMENTS,
    PHASE_4_DOMAIN_EXPEDITED_SURCHARGE,
    QUERY_CLASS_AUTHORITY_VERIFICATION,
    QUERY_CLASS_CURRENT_GUIDANCE,
    QUERY_CLASS_DETERMINISTIC_CURRENT,
    QUERY_CLASS_MIXED_CURRENT_AND_PRECEDENT,
    QUERY_CLASS_PRECEDENT_DISCOVERY,
    QUERY_CLASS_UNRESOLVED_AUTHORITY,
    ROUTING_CONFIDENCE_HIGH,
    ROUTING_CONFIDENCE_LOW,
    ROUTING_CONFIDENCE_MEDIUM,
    Phase4RoutingIntent,
    Phase5RoutingIntent,
    Phase6RoutingIntent,
    Phase7RuntimeConfiguration,
    QueryContext,
    QueryPlan,
)
from .validation import Phase7ContractError, ensure_non_empty_text


SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4 = "current_deterministic_claim_requires_phase_4"
SAFETY_OVERRIDE_HISTORICAL_CURRENT_AUTHORITY = (
    "historical_reference_requires_current_authority_before_prescriptive_answer"
)
SAFETY_OVERRIDE_HISTORICAL_COMMERCIAL_CURRENT_AUTHORITY = (
    "historical_commercial_claim_requires_current_authority"
)
SAFETY_OVERRIDE_GUIDANCE_PHASE5 = "current_guidance_request_requires_phase_5"

AMBIGUITY_FLAG_AMBIGUOUS_DEPOSIT_TYPE = "ambiguous_deposit_type"
AMBIGUITY_FLAG_AMBIGUOUS_CURRENT_VS_HISTORICAL = "ambiguous_current_vs_historical_intent"
AMBIGUITY_FLAG_AMBIGUOUS_TECHNICAL = "ambiguous_technical_inventory_vs_capability"
AMBIGUITY_FLAG_INSUFFICIENT_DOMAIN_CONTEXT = "insufficient_domain_context"
AMBIGUITY_FLAG_MIXED_GUIDANCE_AND_DETERMINISTIC = "mixed_guidance_and_deterministic_claim"
AMBIGUITY_FLAG_HISTORICAL_WITH_CURRENT_POLICY = "historical_reference_with_current_policy_request"

REASON_CODE_PRECEDENT_DISCOVERY = "precedent_discovery_request"
REASON_CODE_CURRENT_PROCESS_GUIDANCE = "current_process_guidance_request"
REASON_CODE_CURRENT_PAYMENT = "current_payment_request"
REASON_CODE_CURRENT_CAPACITY = "current_capacity_request"
REASON_CODE_CURRENT_ACCESS = "current_access_request"
REASON_CODE_CURRENT_CANCELLATION = "current_cancellation_request"
REASON_CODE_CURRENT_EXPEDITED = "current_expedited_surcharge_request"
REASON_CODE_CURRENT_OPERATIONAL = "current_operational_requirements_request"
REASON_CODE_CURRENT_SUPPLIER = "current_supplier_policy_request"
REASON_CODE_CURRENT_TECH_CAPABILITY = "technical_capability_request"
REASON_CODE_CURRENT_TECH_INVENTORY = "technical_inventory_request"
REASON_CODE_CURRENT_SERVICE_RULES = "current_service_scope_request"
REASON_CODE_CURRENT_FACILITATOR = "current_facilitator_requirement_request"
REASON_CODE_CURRENT_CONFIDENTIALITY = "current_confidentiality_guidance_request"
REASON_CODE_HISTORICAL_REQUIRES_CURRENT = "historical_reference_requires_current_authority"
REASON_CODE_DISCOUNT_UNRESOLVED = "discount_policy_unresolved_cue"
REASON_CODE_OVERTIME_UNRESOLVED = "overtime_rate_unresolved_cue"
REASON_CODE_SECURITY_DEPOSIT_UNRESOLVED = "security_deposit_unresolved_cue"
REASON_CODE_CUSTOM_TECH_CONFIRMATION = "custom_technical_confirmation_cue"
REASON_CODE_CAPACITY_CONFIRMATION = "capacity_confirmation_cue"
REASON_CODE_HISTORICAL_CAPABILITY = "historical_capability_requires_current_authority"
REASON_CODE_COMPLIANCE_VERIFICATION = "historical_compliance_requires_current_verification"


def plan_query(
    query_text: str,
    query_context: QueryContext | None = None,
    runtime_configuration: Phase7RuntimeConfiguration | None = None,
) -> QueryPlan:
    if query_context is not None:
        ensure_non_empty_text("query_context.query_text", query_context.query_text)
        if query_context.query_text != query_text:
            raise Phase7ContractError(
                error_category="invalid_value",
                safe_message="query_text must match query_context.query_text when both are supplied.",
            )
    ensure_non_empty_text("query_text", query_text)
    config = runtime_configuration or Phase7RuntimeConfiguration()
    signals = _analyze_query(query_text)
    return _build_plan(query_text=query_text, signals=signals, config=config)


@dataclass(frozen=True)
class QuerySignals:
    normalized_query: str
    phase4_domains: tuple[str, ...]
    has_guidance_intent: bool
    has_precedent_intent: bool
    has_current_intent: bool
    has_current_policy_request: bool
    has_historical_reference: bool
    has_historical_current_verification: bool
    has_historical_commercial_risk: bool
    is_unresolved_pattern: bool
    wants_confidentiality_guidance: bool
    wants_explanation: bool
    wants_process: bool
    wants_current_deterministic_claim: bool
    ambiguity_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]


def _build_plan(
    *,
    query_text: str,
    signals: QuerySignals,
    config: Phase7RuntimeConfiguration,
) -> QueryPlan:
    required_layers: list[str] = []
    optional_layers: list[str] = []
    safety_overrides: list[str] = []
    ambiguity_flags = list(signals.ambiguity_flags)
    reason_codes = list(signals.reason_codes)

    phase4_required = False
    phase5_required = False
    phase6_required = False

    if signals.has_historical_reference and signals.has_current_policy_request:
        ambiguity_flags = _append_unique(
            ambiguity_flags,
            AMBIGUITY_FLAG_HISTORICAL_WITH_CURRENT_POLICY,
        )

    if signals.wants_current_deterministic_claim and signals.wants_explanation:
        ambiguity_flags = _append_unique(
            ambiguity_flags,
            AMBIGUITY_FLAG_MIXED_GUIDANCE_AND_DETERMINISTIC,
        )

    if config.enable_current_claim_phase4_override and signals.wants_current_deterministic_claim:
        if signals.phase4_domains:
            phase4_required = True
            safety_overrides = _append_unique(
                safety_overrides,
                SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4,
            )

    if signals.has_guidance_intent or signals.wants_confidentiality_guidance:
        phase5_required = True
        safety_overrides = _append_unique(
            safety_overrides,
            SAFETY_OVERRIDE_GUIDANCE_PHASE5,
        )

    if signals.has_precedent_intent or signals.has_historical_reference:
        phase6_required = True

    query_class = _classify_query(signals)

    if query_class == QUERY_CLASS_DETERMINISTIC_CURRENT and signals.wants_explanation:
        phase5_required = True
    if query_class == QUERY_CLASS_CURRENT_GUIDANCE and signals.phase4_domains and signals.wants_current_deterministic_claim:
        phase4_required = True
    if query_class == QUERY_CLASS_MIXED_CURRENT_AND_PRECEDENT:
        phase6_required = True
        if signals.phase4_domains and signals.wants_current_deterministic_claim:
            phase4_required = True
        phase5_required = True
    if query_class == QUERY_CLASS_AUTHORITY_VERIFICATION:
        phase6_required = True
        safety_overrides = _append_unique(
            safety_overrides,
            SAFETY_OVERRIDE_HISTORICAL_CURRENT_AUTHORITY,
        )
        reason_codes = _append_unique(
            reason_codes,
            REASON_CODE_HISTORICAL_REQUIRES_CURRENT,
        )
        if signals.phase4_domains and signals.wants_current_deterministic_claim:
            phase4_required = True
        if (
            not phase4_required
            or signals.has_historical_commercial_risk
            or signals.wants_confidentiality_guidance
            or PHASE_4_DOMAIN_SERVICE_RULES in signals.phase4_domains
            or PHASE_4_DOMAIN_CATERING_SUPPLIER in signals.phase4_domains
            or PHASE_4_DOMAIN_FACILITATOR_REQUIREMENTS in signals.phase4_domains
        ):
            phase5_required = True
    if query_class == QUERY_CLASS_UNRESOLVED_AUTHORITY:
        safety_overrides = _append_unique(
            safety_overrides,
            SAFETY_OVERRIDE_HISTORICAL_CURRENT_AUTHORITY,
        ) if signals.has_historical_current_verification else safety_overrides
        if signals.phase4_domains and (
            signals.wants_current_deterministic_claim
            or PHASE_4_DOMAIN_TECHNICAL_CAPABILITY in signals.phase4_domains
            or PHASE_4_DOMAIN_CAPACITY in signals.phase4_domains
        ):
            phase4_required = True
        phase5_required = True
        if signals.has_historical_reference:
            phase6_required = True

    if signals.has_historical_commercial_risk:
        safety_overrides = _append_unique(
            safety_overrides,
            SAFETY_OVERRIDE_HISTORICAL_COMMERCIAL_CURRENT_AUTHORITY,
        )
        reason_codes = _append_unique(
            reason_codes,
            REASON_CODE_HISTORICAL_REQUIRES_CURRENT,
        )
        if config.enable_historical_prescriptive_current_authority_override:
            if signals.phase4_domains and signals.wants_current_deterministic_claim:
                phase4_required = True
            else:
                phase5_required = True
            if signals.has_historical_reference:
                phase6_required = True

    if (
        config.routing_ambiguity_behavior == "broaden_current_authority_first"
        and _routing_confidence(signals, phase4_required, phase5_required, phase6_required) == ROUTING_CONFIDENCE_LOW
        and signals.has_current_policy_request
    ):
        if signals.phase4_domains and signals.wants_current_deterministic_claim:
            phase4_required = True
        else:
            phase5_required = True

    if phase5_required and query_class in {
        QUERY_CLASS_CURRENT_GUIDANCE,
        QUERY_CLASS_MIXED_CURRENT_AND_PRECEDENT,
        QUERY_CLASS_AUTHORITY_VERIFICATION,
    }:
        safety_overrides = _append_unique(
            safety_overrides,
            SAFETY_OVERRIDE_GUIDANCE_PHASE5,
        )

    if phase4_required:
        required_layers.append(LAYER_ID_PHASE_4)
    if phase5_required:
        required_layers.append(LAYER_ID_PHASE_5)
    if phase6_required:
        required_layers.append(LAYER_ID_PHASE_6)

    if not required_layers:
        phase5_required = True
        required_layers.append(LAYER_ID_PHASE_5)
        ambiguity_flags = _append_unique(
            ambiguity_flags,
            AMBIGUITY_FLAG_INSUFFICIENT_DOMAIN_CONTEXT,
        )

    confidence = _routing_confidence(signals, phase4_required, phase5_required, phase6_required)

    phase4_intent = None
    if phase4_required or LAYER_ID_PHASE_4 in optional_layers:
        phase4_intent = Phase4RoutingIntent(
            required=phase4_required,
            domains=signals.phase4_domains,
            reason_codes=tuple(_phase4_reason_codes(signals.phase4_domains)),
        )
    phase5_intent = None
    if phase5_required or LAYER_ID_PHASE_5 in optional_layers:
        phase5_intent = Phase5RoutingIntent(
            required=phase5_required,
            needs_guidance=True,
            query_text=query_text,
            result_limit=config.phase_5_result_limit or DEFAULT_PHASE_5_RESULT_LIMIT,
            reason_codes=tuple(_phase5_reason_codes(signals)),
        )
    phase6_intent = None
    if phase6_required or LAYER_ID_PHASE_6 in optional_layers:
        phase6_intent = Phase6RoutingIntent(
            required=phase6_required,
            query_text=query_text,
            result_limit=config.phase_6_result_limit or DEFAULT_PHASE_6_RESULT_LIMIT,
            reason_codes=tuple(_phase6_reason_codes(signals)),
        )

    return QueryPlan(
        query_text=query_text,
        query_class=query_class,
        routing_confidence=confidence,
        ambiguity_flags=tuple(ambiguity_flags),
        required_layers=tuple(required_layers),
        optional_layers=tuple(optional_layers),
        phase_4=phase4_intent,
        phase_5=phase5_intent,
        phase_6=phase6_intent,
        safety_overrides=tuple(safety_overrides),
        reason_codes=tuple(reason_codes),
    )


def _classify_query(signals: QuerySignals) -> str:
    if signals.has_historical_current_verification:
        if signals.is_unresolved_pattern:
            return QUERY_CLASS_UNRESOLVED_AUTHORITY
        return QUERY_CLASS_AUTHORITY_VERIFICATION
    if signals.is_unresolved_pattern:
        return QUERY_CLASS_UNRESOLVED_AUTHORITY
    if signals.has_precedent_intent and (signals.has_current_policy_request or signals.has_guidance_intent):
        return QUERY_CLASS_MIXED_CURRENT_AND_PRECEDENT
    if signals.has_precedent_intent:
        return QUERY_CLASS_PRECEDENT_DISCOVERY
    if signals.has_guidance_intent:
        deterministic_priority_domains = {
            PHASE_4_DOMAIN_PAYMENT,
            PHASE_4_DOMAIN_EXPEDITED_SURCHARGE,
            PHASE_4_DOMAIN_CANCELLATION,
            PHASE_4_DOMAIN_CAPACITY,
            PHASE_4_DOMAIN_SPACE_ACCESS,
        }
        if " vat " in signals.normalized_query or (
            signals.wants_current_deterministic_claim
            and set(signals.phase4_domains).intersection(deterministic_priority_domains)
        ):
            return QUERY_CLASS_DETERMINISTIC_CURRENT
        return QUERY_CLASS_CURRENT_GUIDANCE
    if signals.wants_current_deterministic_claim:
        return QUERY_CLASS_DETERMINISTIC_CURRENT
    return QUERY_CLASS_CURRENT_GUIDANCE


def _routing_confidence(
    signals: QuerySignals,
    phase4_required: bool,
    phase5_required: bool,
    phase6_required: bool,
) -> str:
    if AMBIGUITY_FLAG_AMBIGUOUS_DEPOSIT_TYPE in signals.ambiguity_flags:
        return ROUTING_CONFIDENCE_LOW
    if AMBIGUITY_FLAG_INSUFFICIENT_DOMAIN_CONTEXT in signals.ambiguity_flags:
        return ROUTING_CONFIDENCE_LOW
    if signals.is_unresolved_pattern and not signals.phase4_domains and not phase5_required:
        return ROUTING_CONFIDENCE_LOW
    if (
        len(signals.phase4_domains) > 2
        or AMBIGUITY_FLAG_MIXED_GUIDANCE_AND_DETERMINISTIC in signals.ambiguity_flags
        or AMBIGUITY_FLAG_HISTORICAL_WITH_CURRENT_POLICY in signals.ambiguity_flags
        or phase4_required + phase5_required + phase6_required > 1
    ):
        return ROUTING_CONFIDENCE_MEDIUM
    return ROUTING_CONFIDENCE_HIGH


def _phase4_reason_codes(domains: tuple[str, ...]) -> list[str]:
    codes: list[str] = []
    for domain in domains:
        if domain == PHASE_4_DOMAIN_PAYMENT:
            codes.append(REASON_CODE_CURRENT_PAYMENT)
        elif domain == PHASE_4_DOMAIN_CAPACITY:
            codes.append(REASON_CODE_CURRENT_CAPACITY)
        elif domain == PHASE_4_DOMAIN_SPACE_ACCESS:
            codes.append(REASON_CODE_CURRENT_ACCESS)
        elif domain == PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS:
            codes.append(REASON_CODE_CURRENT_OPERATIONAL)
        elif domain == PHASE_4_DOMAIN_CATERING_SUPPLIER:
            codes.append(REASON_CODE_CURRENT_SUPPLIER)
        elif domain == PHASE_4_DOMAIN_TECHNICAL_CAPABILITY:
            codes.append(REASON_CODE_CURRENT_TECH_CAPABILITY)
        elif domain == PHASE_4_DOMAIN_TECHNICAL_INVENTORY:
            codes.append(REASON_CODE_CURRENT_TECH_INVENTORY)
        elif domain == PHASE_4_DOMAIN_SERVICE_RULES:
            codes.append(REASON_CODE_CURRENT_SERVICE_RULES)
        elif domain == PHASE_4_DOMAIN_FACILITATOR_REQUIREMENTS:
            codes.append(REASON_CODE_CURRENT_FACILITATOR)
        elif domain == PHASE_4_DOMAIN_CANCELLATION:
            codes.append(REASON_CODE_CURRENT_CANCELLATION)
        elif domain == PHASE_4_DOMAIN_EXPEDITED_SURCHARGE:
            codes.append(REASON_CODE_CURRENT_EXPEDITED)
    return codes


def _phase5_reason_codes(signals: QuerySignals) -> list[str]:
    codes: list[str] = []
    if signals.has_guidance_intent or signals.wants_process:
        codes.append(REASON_CODE_CURRENT_PROCESS_GUIDANCE)
    if signals.wants_confidentiality_guidance:
        codes.append(REASON_CODE_CURRENT_CONFIDENTIALITY)
    if PHASE_4_DOMAIN_CATERING_SUPPLIER in signals.phase4_domains:
        codes.append(REASON_CODE_CURRENT_SUPPLIER)
    if PHASE_4_DOMAIN_SERVICE_RULES in signals.phase4_domains:
        codes.append(REASON_CODE_CURRENT_SERVICE_RULES)
    if PHASE_4_DOMAIN_FACILITATOR_REQUIREMENTS in signals.phase4_domains:
        codes.append(REASON_CODE_CURRENT_FACILITATOR)
    return _dedupe_preserve(codes)


def _phase6_reason_codes(signals: QuerySignals) -> list[str]:
    codes: list[str] = []
    if signals.has_precedent_intent or signals.has_historical_reference:
        codes.append(REASON_CODE_PRECEDENT_DISCOVERY)
    if signals.has_historical_current_verification:
        codes.append(REASON_CODE_HISTORICAL_REQUIRES_CURRENT)
    if signals.is_unresolved_pattern and "discount" in signals.normalized_query:
        codes.append(REASON_CODE_DISCOUNT_UNRESOLVED)
    return _dedupe_preserve(codes)


def _analyze_query(query_text: str) -> QuerySignals:
    normalized = _normalize(query_text)
    ambiguity_flags: list[str] = []
    reason_codes: list[str] = []
    phase4_domains: list[str] = []
    historical_before_context = " before " in normalized and _matches_any(
        normalized,
        ("handled", "dealt", "seen", "done", "paid", "charged", "existed"),
    )

    has_historical_reference = _matches_any(
        normalized,
        (
            "last time",
            "historical",
            "previous",
            "have we done this",
            "have we handled",
            "have we seen",
            "have we dealt",
            "what happened last time",
            "precedent",
            "old case",
            "paid ",
            "charged ",
            "existed",
        ),
    ) or historical_before_context
    has_precedent_intent = _matches_any(
        normalized,
        (
            "have we done this before",
            "handled something similar",
            "have we handled",
            "historical example",
            "what happened last time",
            "have we seen this",
            "precedent",
            "have we dealt with",
            "have we done similar",
            "have we seen",
        ),
    ) or historical_before_context
    has_guidance_intent = _matches_any(
        normalized,
        (
            "how should we explain",
            "what should staff tell",
            "what information do we need",
            "what should we ask",
            "what should we cover",
            "what is the process",
            "what should we prepare",
            "checklist",
            "site visit",
            "handover",
            "communication",
            "what should we do now",
            "what should we tell the client",
            "what may be surfaced internally",
            "what sensitivity boundary should control",
            "how should full-production scope be framed",
            "should we suggest",
            "explanation is requested",
            "payment explanation",
        ),
    )
    wants_explanation = _matches_any(
        normalized,
        ("explain", "what should we tell", "what should we do now", "what may be surfaced", "framed"),
    )
    wants_process = _matches_any(
        normalized,
        ("process", "checklist", "site visit", "handover", "communication", "schedule and confirm"),
    )
    has_current_policy_request = _matches_any(
        normalized,
        (
            " right now",
            " current ",
            " today",
            " official ",
            " now?",
            " now ",
            "this year",
            "still allowed",
            "still official",
            "what should we do now",
            "what applies now",
            "what is the current position now",
            "can i quote",
            "can i offer",
            "can we offer",
            "can we support",
            "is that our official",
            "what is our current",
            "what is wnc's official",
            "what may be surfaced internally",
            "overlaps with current",
        ),
    )
    has_current_intent = has_current_policy_request or _matches_any(
        normalized,
        (
            "what is",
            "when is",
            "does ",
            "is ",
            "can ",
            "who is responsible now",
            "what does",
        ),
    )

    security_deposit_context = _matches_any(normalized, ("security deposit", "damage deposit"))
    payment_context = _matches_any(
        normalized,
        (
            "minimum payment",
            "payment",
            "final balance",
            "balance due",
            "due date",
            "confirms a booking",
            "booking right now",
            "payment schedule",
            "payment timing",
        ),
    )
    deposit_mentioned = "deposit" in normalized
    if deposit_mentioned and security_deposit_context:
        ambiguity_flags = _append_unique(
            ambiguity_flags,
            AMBIGUITY_FLAG_AMBIGUOUS_DEPOSIT_TYPE,
        )
        reason_codes = _append_unique(
            reason_codes,
            REASON_CODE_SECURITY_DEPOSIT_UNRESOLVED,
        )
    elif payment_context:
        phase4_domains = _append_unique(phase4_domains, PHASE_4_DOMAIN_PAYMENT)
        reason_codes = _append_unique(reason_codes, REASON_CODE_CURRENT_PAYMENT)

    if _matches_any(normalized, ("booking fee", "booking charge", "booking confirmation fee")):
        phase4_domains = _append_unique(phase4_domains, PHASE_4_DOMAIN_BOOKING_FEE)
    if _matches_any(normalized, ("expedited surcharge", "short-notice surcharge", "within 14 days", "rush booking", "urgent booking")):
        phase4_domains = _append_unique(phase4_domains, PHASE_4_DOMAIN_EXPEDITED_SURCHARGE)
        reason_codes = _append_unique(reason_codes, REASON_CODE_CURRENT_EXPEDITED)
    if _matches_any(normalized, ("cancellation", "cancel rental", "refundable", "refund after cancellation", "cancellation window", "cancellation fee")):
        phase4_domains = _append_unique(phase4_domains, PHASE_4_DOMAIN_CANCELLATION)
        reason_codes = _append_unique(reason_codes, REASON_CODE_CURRENT_CANCELLATION)
    if _matches_any(normalized, ("capacity", "maximum guests", "how many people", "seated", "standing", "lying-down", "movement", "room capacity", "legal maximum", "fixed capacity")):
        phase4_domains = _append_unique(phase4_domains, PHASE_4_DOMAIN_CAPACITY)
        reason_codes = _append_unique(reason_codes, REASON_CODE_CURRENT_CAPACITY)
    access_room_reference = _matches_any(
        normalized,
        ("included room", "access", "back office", "storage room", "retail", "bathrooms", "room entitlement", "extra rooms"),
    )
    named_room_reference = _matches_any(normalized, ("podcast room", "1:1"))
    if access_room_reference or (named_room_reference and PHASE_4_DOMAIN_CAPACITY not in phase4_domains):
        phase4_domains = _append_unique(phase4_domains, PHASE_4_DOMAIN_SPACE_ACCESS)
        reason_codes = _append_unique(reason_codes, REASON_CODE_CURRENT_ACCESS)
    if _matches_any(normalized, ("setup", "build-up", "breakdown", "grace period", "early access", "deliveries", "cleaning", "clearing", "waste", "reset", "supplier timing", "storage", "onsite space", "offsite storage")) and not (
        access_room_reference and _matches_any(normalized, ("back office", "storage room", "extra rooms"))
    ):
        phase4_domains = _append_unique(phase4_domains, PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS)
        reason_codes = _append_unique(reason_codes, REASON_CODE_CURRENT_OPERATIONAL)
    if _matches_any(normalized, ("caterer", "catering", "food", "drinks", "beverages", "barista", "supplier", "external supplier", "catering vat", "client-provided wine", "own wine", "provide their own wine")):
        phase4_domains = _append_unique(phase4_domains, PHASE_4_DOMAIN_CATERING_SUPPLIER)
        reason_codes = _append_unique(reason_codes, REASON_CODE_CURRENT_SUPPLIER)
    if _matches_any(normalized, ("do we have", "quantity available", "projector", "sonos", "extension cable", "mats", "cushions", "equipment inventory", "standard inventory", "inventory", "technical setup")):
        phase4_domains = _append_unique(phase4_domains, PHASE_4_DOMAIN_TECHNICAL_INVENTORY)
        reason_codes = _append_unique(reason_codes, REASON_CODE_CURRENT_TECH_INVENTORY)
    if _matches_any(normalized, ("can the venue support", "high electrical load", "high-load", "coffee machines", "microphone", "dj", "amplified sound", "custom tech", "livestream", "filming", "projection capability", "non-standard technical", "non-standard rig", "custom tech rig", "support this unusual")):
        phase4_domains = _append_unique(phase4_domains, PHASE_4_DOMAIN_TECHNICAL_CAPABILITY)
        reason_codes = _append_unique(reason_codes, REASON_CODE_CURRENT_TECH_CAPABILITY)
    if _matches_any(normalized, ("venue only", "supported rental", "full production", "production coordination", "event management", "service scope", "what wnc handles", "run a whole-venue event themselves", "run a whole venue event themselves", "can wnc source")):
        phase4_domains = _append_unique(phase4_domains, PHASE_4_DOMAIN_SERVICE_RULES)
        reason_codes = _append_unique(reason_codes, REASON_CODE_CURRENT_SERVICE_RULES)
    if _matches_any(normalized, ("facilitator", "teacher", "wellness session leader", "wnc-provided facilitator", "facilitator confirmation")):
        phase4_domains = _append_unique(phase4_domains, PHASE_4_DOMAIN_FACILITATOR_REQUIREMENTS)
        reason_codes = _append_unique(reason_codes, REASON_CODE_CURRENT_FACILITATOR)

    if "offsite storage" in normalized:
        phase4_domains = _append_unique(phase4_domains, PHASE_4_DOMAIN_SPACE_ACCESS)
        phase4_domains = _append_unique(phase4_domains, PHASE_4_DOMAIN_CATERING_SUPPLIER)
    if "storage" in normalized and "quote" in normalized:
        phase4_domains = _append_unique(phase4_domains, PHASE_4_DOMAIN_SPACE_ACCESS)
    if "external caterer" in normalized or "strong-smell catering" in normalized or "own wine" in normalized or "provide their own wine" in normalized:
        phase4_domains = _append_unique(phase4_domains, PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS)
    if "run a whole-venue event themselves" in normalized or "run a whole venue event themselves" in normalized:
        phase4_domains = _append_unique(phase4_domains, PHASE_4_DOMAIN_FACILITATOR_REQUIREMENTS)
    if "technical setup" in normalized and PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS in phase4_domains and not _matches_any(
        normalized,
        ("build-up", "breakdown", "grace period", "early access", "deliveries", "cleaning", "clearing", "storage"),
    ):
        phase4_domains = [domain for domain in phase4_domains if domain != PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS]

    wants_confidentiality_guidance = _matches_any(
        normalized,
        ("surfaced internally", "pi-bearing", "sensitivity boundary", "restricted historical"),
    )

    if (
        PHASE_4_DOMAIN_TECHNICAL_INVENTORY in phase4_domains
        and PHASE_4_DOMAIN_TECHNICAL_CAPABILITY in phase4_domains
    ):
        ambiguity_flags = _append_unique(
            ambiguity_flags,
            AMBIGUITY_FLAG_AMBIGUOUS_TECHNICAL,
        )

    has_historical_commercial_risk = has_current_policy_request and _matches_any(
        normalized,
        (
            "quote",
            "price",
            "eur ",
            "discount",
            "exposure",
            "gift",
            "overtime",
            "permits",
            "compliance",
            "offer floral",
            "offer floral arrangements",
        ),
    ) and has_historical_reference

    has_historical_current_verification = has_historical_reference and _matches_any(
        normalized,
        (
            "applies now",
            "quote",
            "official",
            "offer",
            "reused",
            "reuse",
            "still allowed",
            "can we do the same",
            "can a client use",
            "can the client use",
            "can we support it now",
            "does that mean",
            "override current",
            "what is our current",
            "what is wnc's official",
            "what may be surfaced internally",
            "overlaps with current",
        ),
    )
    if has_historical_reference and has_current_intent and not has_historical_current_verification:
        ambiguity_flags = _append_unique(
            ambiguity_flags,
            AMBIGUITY_FLAG_AMBIGUOUS_CURRENT_VS_HISTORICAL,
        )

    is_unresolved_pattern = _matches_any(
        normalized,
        (
            "security deposit",
            "collaboration",
            "exposure discount",
            "discount policy",
            "official discount policy",
            "overtime rate",
            "offer floral arrangements",
            "can i offer floral",
            "custom tech rig",
            "high electrical load",
            "non-standard technical",
            "support this unusual custom tech",
            "fixed capacity",
            "event format",
            "quote eur",
            "can i quote",
        ),
    )
    if "discount" in normalized:
        reason_codes = _append_unique(reason_codes, REASON_CODE_DISCOUNT_UNRESOLVED)
    if "overtime" in normalized:
        reason_codes = _append_unique(reason_codes, REASON_CODE_OVERTIME_UNRESOLVED)
    if "custom tech" in normalized or "technical" in normalized or "high electrical load" in normalized:
        if "custom tech" in normalized or "high electrical load" in normalized:
            reason_codes = _append_unique(reason_codes, REASON_CODE_CUSTOM_TECH_CONFIRMATION)
    if "fixed capacity" in normalized or "event format" in normalized:
        reason_codes = _append_unique(reason_codes, REASON_CODE_CAPACITY_CONFIRMATION)
    if "floral" in normalized:
        reason_codes = _append_unique(reason_codes, REASON_CODE_HISTORICAL_CAPABILITY)
    if "permit" in normalized or "compliance" in normalized:
        reason_codes = _append_unique(reason_codes, REASON_CODE_COMPLIANCE_VERIFICATION)

    wants_current_deterministic_claim = bool(
        phase4_domains
        and (
            has_current_intent
            or " vat " in normalized
            or " final balance " in normalized
            or " due " in normalized
            or "payment explanation" in normalized
        )
        and not wants_confidentiality_guidance
    )
    if "acceptable degraded behavior" in normalized or "historical semantic retrieval is unavailable" in normalized:
        phase4_domains = []
        wants_current_deterministic_claim = False
        has_guidance_intent = False
        has_current_policy_request = False
        has_current_intent = False
        has_precedent_intent = True
        has_historical_current_verification = False
        has_historical_commercial_risk = False
        ambiguity_flags = [
            flag for flag in ambiguity_flags
            if flag != AMBIGUITY_FLAG_AMBIGUOUS_CURRENT_VS_HISTORICAL
        ]
    if security_deposit_context:
        wants_current_deterministic_claim = False
    if not phase4_domains and has_current_policy_request and not has_guidance_intent:
        ambiguity_flags = _append_unique(
            ambiguity_flags,
            AMBIGUITY_FLAG_INSUFFICIENT_DOMAIN_CONTEXT,
        )

    return QuerySignals(
        normalized_query=normalized,
        phase4_domains=tuple(phase4_domains),
        has_guidance_intent=has_guidance_intent,
        has_precedent_intent=has_precedent_intent,
        has_current_intent=has_current_intent,
        has_current_policy_request=has_current_policy_request,
        has_historical_reference=has_historical_reference,
        has_historical_current_verification=has_historical_current_verification,
        has_historical_commercial_risk=has_historical_commercial_risk,
        is_unresolved_pattern=is_unresolved_pattern,
        wants_confidentiality_guidance=wants_confidentiality_guidance,
        wants_explanation=wants_explanation,
        wants_process=wants_process,
        wants_current_deterministic_claim=wants_current_deterministic_claim,
        ambiguity_flags=tuple(ambiguity_flags),
        reason_codes=tuple(reason_codes),
    )


def _normalize(text: str) -> str:
    normalized = text.casefold()
    normalized = re.sub(r"[^a-z0-9:/?'\- ]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return f" {normalized} "


def _matches_any(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)


def _append_unique(values: list[str], value: str) -> list[str]:
    if value not in values:
        values.append(value)
    return values


def _dedupe_preserve(values: list[str]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        if value not in deduped:
            deduped.append(value)
    return deduped


__all__ = [
    "AMBIGUITY_FLAG_AMBIGUOUS_CURRENT_VS_HISTORICAL",
    "AMBIGUITY_FLAG_AMBIGUOUS_DEPOSIT_TYPE",
    "AMBIGUITY_FLAG_AMBIGUOUS_TECHNICAL",
    "AMBIGUITY_FLAG_HISTORICAL_WITH_CURRENT_POLICY",
    "AMBIGUITY_FLAG_INSUFFICIENT_DOMAIN_CONTEXT",
    "AMBIGUITY_FLAG_MIXED_GUIDANCE_AND_DETERMINISTIC",
    "REASON_CODE_PRECEDENT_DISCOVERY",
    "SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4",
    "SAFETY_OVERRIDE_GUIDANCE_PHASE5",
    "SAFETY_OVERRIDE_HISTORICAL_COMMERCIAL_CURRENT_AUTHORITY",
    "SAFETY_OVERRIDE_HISTORICAL_CURRENT_AUTHORITY",
    "plan_query",
]
