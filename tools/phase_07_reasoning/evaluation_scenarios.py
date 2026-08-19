from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .contracts import (
    LAYER_ID_PHASE_4,
    LAYER_ID_PHASE_5,
    LAYER_ID_PHASE_6,
    PHASE_4_DOMAIN_CAPACITY,
    PHASE_4_DOMAIN_CATERING_SUPPLIER,
    PHASE_4_DOMAIN_EXPEDITED_SURCHARGE,
    PHASE_4_DOMAIN_FACILITATOR_REQUIREMENTS,
    PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS,
    PHASE_4_DOMAIN_PAYMENT,
    PHASE_4_DOMAIN_SERVICE_RULES,
    PHASE_4_DOMAIN_SPACE_ACCESS,
    PHASE_4_DOMAIN_TECHNICAL_CAPABILITY,
    PHASE_4_DOMAIN_TECHNICAL_INVENTORY,
    QueryPlan,
)
from .query_planner import (
    SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4,
    SAFETY_OVERRIDE_GUIDANCE_PHASE5,
    SAFETY_OVERRIDE_HISTORICAL_COMMERCIAL_CURRENT_AUTHORITY,
    SAFETY_OVERRIDE_HISTORICAL_CURRENT_AUTHORITY,
)


@dataclass(frozen=True)
class PlannerScenario:
    scenario_id: str
    question: str
    expected_required_layers: tuple[str, ...]
    expected_query_class: str
    expected_phase4_domains: tuple[str, ...] = field(default_factory=tuple)
    forbidden_required_layers: tuple[str, ...] = field(default_factory=tuple)
    expected_safety_overrides: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""


@dataclass(frozen=True)
class PlannerScenarioResult:
    scenario: PlannerScenario
    plan: QueryPlan
    required_layers_match: bool
    query_class_match: bool
    phase4_domain_match: bool
    expected_required_recall: float
    expected_domain_recall: float
    missing_layers: tuple[str, ...]
    extra_layers: tuple[str, ...]
    missing_domains: tuple[str, ...]
    extra_domains: tuple[str, ...]
    missing_safety_overrides: tuple[str, ...]


@dataclass(frozen=True)
class PlannerEvaluation:
    scenario_results: tuple[PlannerScenarioResult, ...]
    required_layer_recall: float
    exact_required_layer_set_accuracy: float
    unnecessary_layer_rate: float
    query_class_accuracy: float
    phase4_required_domain_recall: float
    phase4_exact_domain_set_accuracy: float
    safety_override_recall: float


EXPECTED_RUNTIME_QUERY_CLASSES: dict[str, str] = {
    "P7-EVAL-001": "deterministic_current",
    "P7-EVAL-002": "deterministic_current",
    "P7-EVAL-003": "deterministic_current",
    "P7-EVAL-004": "deterministic_current",
    "P7-EVAL-005": "deterministic_current",
    "P7-EVAL-006": "deterministic_current",
    "P7-EVAL-007": "current_guidance",
    "P7-EVAL-008": "deterministic_current",
    "P7-EVAL-009": "current_guidance",
    "P7-EVAL-010": "current_guidance",
    "P7-EVAL-011": "current_guidance",
    "P7-EVAL-012": "current_guidance",
    "P7-EVAL-013": "current_guidance",
    "P7-EVAL-014": "current_guidance",
    "P7-EVAL-015": "precedent_discovery",
    "P7-EVAL-016": "precedent_discovery",
    "P7-EVAL-017": "precedent_discovery",
    "P7-EVAL-018": "precedent_discovery",
    "P7-EVAL-019": "mixed_current_and_precedent",
    "P7-EVAL-020": "mixed_current_and_precedent",
    "P7-EVAL-021": "mixed_current_and_precedent",
    "P7-EVAL-022": "mixed_current_and_precedent",
    "P7-EVAL-023": "mixed_current_and_precedent",
    "P7-EVAL-024": "unresolved_authority",
    "P7-EVAL-025": "unresolved_authority",
    "P7-EVAL-026": "unresolved_authority",
    "P7-EVAL-027": "unresolved_authority",
    "P7-EVAL-028": "unresolved_authority",
    "P7-EVAL-029": "authority_verification",
    "P7-EVAL-030": "authority_verification",
    "P7-EVAL-031": "authority_verification",
    "P7-EVAL-032": "authority_verification",
    "P7-EVAL-033": "unresolved_authority",
    "P7-EVAL-034": "unresolved_authority",
    "P7-EVAL-035": "unresolved_authority",
    "P7-EVAL-036": "unresolved_authority",
    "P7-EVAL-037": "precedent_discovery",
    "P7-EVAL-038": "deterministic_current",
    "P7-EVAL-039": "authority_verification",
    "P7-EVAL-040": "authority_verification",
}


EVALUATION_SCENARIOS: tuple[PlannerScenario, ...] = (
    PlannerScenario("P7-EVAL-001", "What minimum payment confirms a booking right now?", (LAYER_ID_PHASE_4,), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-001"], (PHASE_4_DOMAIN_PAYMENT,), (LAYER_ID_PHASE_6,), (SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4,)),
    PlannerScenario("P7-EVAL-002", "Does the expedited surcharge apply if the event is within 14 days?", (LAYER_ID_PHASE_4,), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-002"], (PHASE_4_DOMAIN_EXPEDITED_SURCHARGE,), (LAYER_ID_PHASE_6,), (SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4,)),
    PlannerScenario("P7-EVAL-003", "What is the current legal maximum capacity for the entire venue?", (LAYER_ID_PHASE_4,), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-003"], (PHASE_4_DOMAIN_CAPACITY,), (LAYER_ID_PHASE_6,), (SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4,)),
    PlannerScenario("P7-EVAL-004", "What is the current lying-down capacity in the studio?", (LAYER_ID_PHASE_4,), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-004"], (PHASE_4_DOMAIN_CAPACITY,), (LAYER_ID_PHASE_6,), (SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4,)),
    PlannerScenario("P7-EVAL-005", "Is the 1:1 / Podcast Room included in an Entire Venue rental?", (LAYER_ID_PHASE_4,), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-005"], (PHASE_4_DOMAIN_SPACE_ACCESS,), (LAYER_ID_PHASE_6,), (SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4,)),
    PlannerScenario("P7-EVAL-006", "When is the final balance due, and how should we explain it to a client?", (LAYER_ID_PHASE_4, LAYER_ID_PHASE_5), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-006"], (PHASE_4_DOMAIN_PAYMENT,), (), (SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4, SAFETY_OVERRIDE_GUIDANCE_PHASE5)),
    PlannerScenario("P7-EVAL-007", "Can an external caterer work here, and what information do we need from them?", (LAYER_ID_PHASE_4, LAYER_ID_PHASE_5), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-007"], (PHASE_4_DOMAIN_CATERING_SUPPLIER, PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS), (LAYER_ID_PHASE_6,), (SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4, SAFETY_OVERRIDE_GUIDANCE_PHASE5)),
    PlannerScenario("P7-EVAL-008", "How should we explain the catering VAT split on a quote?", (LAYER_ID_PHASE_4, LAYER_ID_PHASE_5), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-008"], (PHASE_4_DOMAIN_CATERING_SUPPLIER,), (LAYER_ID_PHASE_6,), (SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4, SAFETY_OVERRIDE_GUIDANCE_PHASE5)),
    PlannerScenario("P7-EVAL-009", "What does Supported Rental mean right now, and how should we explain it?", (LAYER_ID_PHASE_4, LAYER_ID_PHASE_5), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-009"], (PHASE_4_DOMAIN_SERVICE_RULES,), (LAYER_ID_PHASE_6,), (SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4, SAFETY_OVERRIDE_GUIDANCE_PHASE5)),
    PlannerScenario("P7-EVAL-010", "Can WNC source a facilitator, and what should we tell the client about confirmation?", (LAYER_ID_PHASE_4, LAYER_ID_PHASE_5), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-010"], (PHASE_4_DOMAIN_SERVICE_RULES, PHASE_4_DOMAIN_FACILITATOR_REQUIREMENTS), (LAYER_ID_PHASE_6,), (SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4, SAFETY_OVERRIDE_GUIDANCE_PHASE5)),
    PlannerScenario("P7-EVAL-011", "Should we suggest a site visit before finalizing layout and logistics?", (LAYER_ID_PHASE_5,), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-011"], (), (LAYER_ID_PHASE_4, LAYER_ID_PHASE_6), (SAFETY_OVERRIDE_GUIDANCE_PHASE5,)),
    PlannerScenario("P7-EVAL-012", "How should staff schedule and confirm a site visit?", (LAYER_ID_PHASE_5,), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-012"], (), (LAYER_ID_PHASE_4, LAYER_ID_PHASE_6), (SAFETY_OVERRIDE_GUIDANCE_PHASE5,)),
    PlannerScenario("P7-EVAL-013", "How should full-production scope be framed before pricing is known?", (LAYER_ID_PHASE_5,), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-013"], (), (LAYER_ID_PHASE_4, LAYER_ID_PHASE_6), (SAFETY_OVERRIDE_GUIDANCE_PHASE5,)),
    PlannerScenario("P7-EVAL-014", "What should staff cover in final readiness and handover communication?", (LAYER_ID_PHASE_5,), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-014"], (), (LAYER_ID_PHASE_4, LAYER_ID_PHASE_6), (SAFETY_OVERRIDE_GUIDANCE_PHASE5,)),
    PlannerScenario("P7-EVAL-015", "Have we handled a multi-day venue takeover before?", (LAYER_ID_PHASE_6,), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-015"], (), (LAYER_ID_PHASE_4, LAYER_ID_PHASE_5)),
    PlannerScenario("P7-EVAL-016", "Have we seen heavy electrical equipment in the venue before?", (LAYER_ID_PHASE_6,), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-016"], (), (LAYER_ID_PHASE_4, LAYER_ID_PHASE_5)),
    PlannerScenario("P7-EVAL-017", "Have we dealt with competitor branding restrictions before?", (LAYER_ID_PHASE_6,), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-017"], (), (LAYER_ID_PHASE_4, LAYER_ID_PHASE_5)),
    PlannerScenario("P7-EVAL-018", "Have we handled an ADE-style permit and compliance issue before?", (LAYER_ID_PHASE_6,), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-018"], (), (LAYER_ID_PHASE_4, LAYER_ID_PHASE_5)),
    PlannerScenario("P7-EVAL-019", "A beauty brand wants strong-smell catering. Have we dealt with this before, and what should we do now?", (LAYER_ID_PHASE_4, LAYER_ID_PHASE_5, LAYER_ID_PHASE_6), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-019"], (PHASE_4_DOMAIN_CATERING_SUPPLIER, PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS), (), (SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4, SAFETY_OVERRIDE_GUIDANCE_PHASE5)),
    PlannerScenario("P7-EVAL-020", "A client wants offsite storage because onsite space is limited. Have we done this before, and what is the current position now?", (LAYER_ID_PHASE_4, LAYER_ID_PHASE_5, LAYER_ID_PHASE_6), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-020"], (PHASE_4_DOMAIN_SPACE_ACCESS, PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS, PHASE_4_DOMAIN_CATERING_SUPPLIER), (), (SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4, SAFETY_OVERRIDE_GUIDANCE_PHASE5)),
    PlannerScenario("P7-EVAL-021", "The client wants to run a whole-venue event themselves. What does WNC handle now, and have we done similar before?", (LAYER_ID_PHASE_4, LAYER_ID_PHASE_5, LAYER_ID_PHASE_6), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-021"], (PHASE_4_DOMAIN_SERVICE_RULES, PHASE_4_DOMAIN_FACILITATOR_REQUIREMENTS), (), (SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4, SAFETY_OVERRIDE_GUIDANCE_PHASE5)),
    PlannerScenario("P7-EVAL-022", "The build-up may run late. What are the current boundaries, and have we seen this before?", (LAYER_ID_PHASE_4, LAYER_ID_PHASE_5, LAYER_ID_PHASE_6), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-022"], (PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS,), ()),
    PlannerScenario("P7-EVAL-023", "A client wants to provide their own wine. Who is responsible now, and have we handled that before?", (LAYER_ID_PHASE_4, LAYER_ID_PHASE_5, LAYER_ID_PHASE_6), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-023"], (PHASE_4_DOMAIN_CATERING_SUPPLIER, PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS), (), (SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4, SAFETY_OVERRIDE_GUIDANCE_PHASE5)),
    PlannerScenario("P7-EVAL-024", "The client wants a non-standard technical setup with high electrical load. Can we support it now, and have we seen similar before?", (LAYER_ID_PHASE_4, LAYER_ID_PHASE_5, LAYER_ID_PHASE_6), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-024"], (PHASE_4_DOMAIN_TECHNICAL_CAPABILITY, PHASE_4_DOMAIN_TECHNICAL_INVENTORY), (), (SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4, SAFETY_OVERRIDE_HISTORICAL_CURRENT_AUTHORITY)),
    PlannerScenario("P7-EVAL-025", "WineGB paid EUR 300 for storage. Can I quote EUR 300 to this client now?", (LAYER_ID_PHASE_4, LAYER_ID_PHASE_5, LAYER_ID_PHASE_6), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-025"], (PHASE_4_DOMAIN_SPACE_ACCESS, PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS), (), (SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4, SAFETY_OVERRIDE_HISTORICAL_CURRENT_AUTHORITY, SAFETY_OVERRIDE_HISTORICAL_COMMERCIAL_CURRENT_AUTHORITY)),
    PlannerScenario("P7-EVAL-026", "Haylin handled florals before. Can I offer floral arrangements now?", (LAYER_ID_PHASE_5, LAYER_ID_PHASE_6), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-026"], (), (LAYER_ID_PHASE_4,), (SAFETY_OVERRIDE_HISTORICAL_CURRENT_AUTHORITY, SAFETY_OVERRIDE_HISTORICAL_COMMERCIAL_CURRENT_AUTHORITY)),
    PlannerScenario("P7-EVAL-027", "We did not discount for exposure last time. Is that our official discount policy?", (LAYER_ID_PHASE_5, LAYER_ID_PHASE_6), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-027"], (), (LAYER_ID_PHASE_4,), (SAFETY_OVERRIDE_HISTORICAL_CURRENT_AUTHORITY, SAFETY_OVERRIDE_HISTORICAL_COMMERCIAL_CURRENT_AUTHORITY)),
    PlannerScenario("P7-EVAL-028", "We charged overtime before. What is our current overtime rate?", (LAYER_ID_PHASE_5, LAYER_ID_PHASE_6), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-028"], (), (LAYER_ID_PHASE_4,), (SAFETY_OVERRIDE_HISTORICAL_CURRENT_AUTHORITY, SAFETY_OVERRIDE_HISTORICAL_COMMERCIAL_CURRENT_AUTHORITY)),
    PlannerScenario("P7-EVAL-029", "We handled ADE permits that way before. Can we do the same this year?", (LAYER_ID_PHASE_5, LAYER_ID_PHASE_6), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-029"], (), (LAYER_ID_PHASE_4,), (SAFETY_OVERRIDE_HISTORICAL_CURRENT_AUTHORITY, SAFETY_OVERRIDE_HISTORICAL_COMMERCIAL_CURRENT_AUTHORITY)),
    PlannerScenario("P7-EVAL-030", "A historical grace period looked like setup time. Can a client use the grace period for setup now?", (LAYER_ID_PHASE_4, LAYER_ID_PHASE_6), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-030"], (PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS,), (LAYER_ID_PHASE_5,), (SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4, SAFETY_OVERRIDE_HISTORICAL_CURRENT_AUTHORITY)),
    PlannerScenario("P7-EVAL-031", "Historical storage and clearing used extra rooms. Does that mean Back Office or Storage Room access is allowed now?", (LAYER_ID_PHASE_4, LAYER_ID_PHASE_6), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-031"], (PHASE_4_DOMAIN_SPACE_ACCESS,), (LAYER_ID_PHASE_5,), (SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4, SAFETY_OVERRIDE_HISTORICAL_CURRENT_AUTHORITY)),
    PlannerScenario("P7-EVAL-032", "Historical client-operated events existed. Does that override current Supported Rental or Full Production boundaries?", (LAYER_ID_PHASE_4, LAYER_ID_PHASE_5, LAYER_ID_PHASE_6), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-032"], (PHASE_4_DOMAIN_SERVICE_RULES,), (), (SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4, SAFETY_OVERRIDE_HISTORICAL_CURRENT_AUTHORITY, SAFETY_OVERRIDE_GUIDANCE_PHASE5)),
    PlannerScenario("P7-EVAL-033", "What is the official security deposit for this custom-scope rental?", (LAYER_ID_PHASE_5,), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-033"], (), (LAYER_ID_PHASE_4, LAYER_ID_PHASE_6)),
    PlannerScenario("P7-EVAL-034", "What is WNC's official collaboration or exposure discount policy today?", (LAYER_ID_PHASE_5,), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-034"], (), (LAYER_ID_PHASE_4, LAYER_ID_PHASE_6)),
    PlannerScenario("P7-EVAL-035", "Can we support this unusual custom tech rig beyond the standard inventory?", (LAYER_ID_PHASE_4, LAYER_ID_PHASE_5), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-035"], (PHASE_4_DOMAIN_TECHNICAL_CAPABILITY, PHASE_4_DOMAIN_TECHNICAL_INVENTORY), (LAYER_ID_PHASE_6,), (SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4,)),
    PlannerScenario("P7-EVAL-036", "What is the fixed capacity of the 1:1 / Podcast Room for this event format?", (LAYER_ID_PHASE_4, LAYER_ID_PHASE_5), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-036"], (PHASE_4_DOMAIN_CAPACITY,), (LAYER_ID_PHASE_6,), (SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4,)),
    PlannerScenario("P7-EVAL-037", "If historical semantic retrieval is unavailable for \"whole venue clearing,\" what is acceptable degraded behavior?", (LAYER_ID_PHASE_6,), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-037"], (), (LAYER_ID_PHASE_4,)),
    PlannerScenario("P7-EVAL-038", "If Phase 5 retrieval is unavailable but a payment explanation is requested, what can still be answered?", (LAYER_ID_PHASE_4, LAYER_ID_PHASE_5), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-038"], (PHASE_4_DOMAIN_PAYMENT,), (), (SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4, SAFETY_OVERRIDE_GUIDANCE_PHASE5)),
    PlannerScenario("P7-EVAL-039", "A restricted historical storage precedent is relevant to a new pitch. What may be surfaced internally?", (LAYER_ID_PHASE_5, LAYER_ID_PHASE_6), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-039"], (), (LAYER_ID_PHASE_4,), (SAFETY_OVERRIDE_GUIDANCE_PHASE5, SAFETY_OVERRIDE_HISTORICAL_CURRENT_AUTHORITY)),
    PlannerScenario("P7-EVAL-040", "A PI-bearing historical case detail overlaps with current supplier guidance. What sensitivity boundary should control the combined answer?", (LAYER_ID_PHASE_5, LAYER_ID_PHASE_6), EXPECTED_RUNTIME_QUERY_CLASSES["P7-EVAL-040"], (), (LAYER_ID_PHASE_4,), (SAFETY_OVERRIDE_GUIDANCE_PHASE5, SAFETY_OVERRIDE_HISTORICAL_CURRENT_AUTHORITY)),
)


def evaluate_planner(plan_query_fn: Callable[[str], QueryPlan]) -> PlannerEvaluation:
    scenario_results: list[PlannerScenarioResult] = []
    total_required_layers = 0
    matched_required_layers = 0
    total_domain_expectations = 0
    matched_domains = 0
    exact_layer_matches = 0
    exact_domain_matches = 0
    query_class_matches = 0
    total_extra_layers = 0
    total_planned_layers = 0
    total_expected_safety = 0
    matched_expected_safety = 0

    for scenario in EVALUATION_SCENARIOS:
        plan = plan_query_fn(scenario.question)
        planned_layers = tuple(plan.required_layers)
        expected_layers = scenario.expected_required_layers
        planned_layer_set = set(planned_layers)
        expected_layer_set = set(expected_layers)
        missing_layers = tuple(layer for layer in expected_layers if layer not in planned_layer_set)
        extra_layers = tuple(layer for layer in planned_layers if layer not in expected_layer_set)

        total_required_layers += len(expected_layers)
        matched_required_layers += len(expected_layer_set.intersection(planned_layer_set))
        total_planned_layers += len(planned_layers)
        total_extra_layers += len(extra_layers)
        exact_layer_match = planned_layer_set == expected_layer_set
        if exact_layer_match:
            exact_layer_matches += 1

        planned_domains = tuple(plan.phase_4.domains) if plan.phase_4 is not None else ()
        planned_domain_set = set(planned_domains)
        expected_domain_set = set(scenario.expected_phase4_domains)
        missing_domains = tuple(domain for domain in scenario.expected_phase4_domains if domain not in planned_domain_set)
        extra_domains = tuple(domain for domain in planned_domains if domain not in expected_domain_set)
        total_domain_expectations += len(expected_domain_set)
        matched_domains += len(expected_domain_set.intersection(planned_domain_set))
        exact_domain_match = planned_domain_set == expected_domain_set
        if exact_domain_match:
            exact_domain_matches += 1

        if plan.query_class == scenario.expected_query_class:
            query_class_matches += 1

        missing_safety_overrides = tuple(
            code
            for code in scenario.expected_safety_overrides
            if code not in plan.safety_overrides
        )
        total_expected_safety += len(scenario.expected_safety_overrides)
        matched_expected_safety += len(scenario.expected_safety_overrides) - len(missing_safety_overrides)

        scenario_results.append(
            PlannerScenarioResult(
                scenario=scenario,
                plan=plan,
                required_layers_match=exact_layer_match,
                query_class_match=plan.query_class == scenario.expected_query_class,
                phase4_domain_match=exact_domain_match,
                expected_required_recall=(
                    len(expected_layer_set.intersection(planned_layer_set)) / len(expected_layer_set)
                    if expected_layer_set
                    else 1.0
                ),
                expected_domain_recall=(
                    len(expected_domain_set.intersection(planned_domain_set)) / len(expected_domain_set)
                    if expected_domain_set
                    else 1.0
                ),
                missing_layers=missing_layers,
                extra_layers=extra_layers,
                missing_domains=missing_domains,
                extra_domains=extra_domains,
                missing_safety_overrides=missing_safety_overrides,
            )
        )

    return PlannerEvaluation(
        scenario_results=tuple(scenario_results),
        required_layer_recall=(matched_required_layers / total_required_layers) if total_required_layers else 1.0,
        exact_required_layer_set_accuracy=exact_layer_matches / len(EVALUATION_SCENARIOS),
        unnecessary_layer_rate=(total_extra_layers / total_planned_layers) if total_planned_layers else 0.0,
        query_class_accuracy=query_class_matches / len(EVALUATION_SCENARIOS),
        phase4_required_domain_recall=(matched_domains / total_domain_expectations) if total_domain_expectations else 1.0,
        phase4_exact_domain_set_accuracy=exact_domain_matches / len(EVALUATION_SCENARIOS),
        safety_override_recall=(matched_expected_safety / total_expected_safety) if total_expected_safety else 1.0,
    )


__all__ = [
    "EVALUATION_SCENARIOS",
    "EXPECTED_RUNTIME_QUERY_CLASSES",
    "PlannerEvaluation",
    "PlannerScenario",
    "PlannerScenarioResult",
    "evaluate_planner",
]
