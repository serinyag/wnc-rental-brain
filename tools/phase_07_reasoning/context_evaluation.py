from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from tools.phase_06_search.historical_retrieval import retrieve_historical_precedents

from .context_assembler import build_context_package
from .contracts import (
    CONFIDENTIALITY_LEVEL_RESTRICTED,
    EXECUTION_STATE_FALLBACK,
    PERSONAL_INFORMATION_STATUS_YES,
    EXECUTION_STATE_SUCCESS,
    LAYER_ID_PHASE_4,
    LAYER_ID_PHASE_5,
    LAYER_ID_PHASE_6,
    QUERY_CLASS_PRECEDENT_DISCOVERY,
    LayerExecutionRecord,
    NormalizedResultEnvelope,
    Phase4RoutingIntent,
    QueryPlan,
    SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
)
from .evaluation_scenarios import EVALUATION_SCENARIOS, PlannerScenario
from .phase5_wrapper import execute_phase5_plan
from .phase6_adapter import execute_phase6_plan
from .query_planner import plan_query


@dataclass(frozen=True)
class ContextScenarioFixture:
    expected_outcome: str
    expected_conflict_codes: tuple[str, ...] = field(default_factory=tuple)
    expected_contamination_types: tuple[str, ...] = field(default_factory=tuple)
    expected_unresolved_states: tuple[str, ...] = field(default_factory=tuple)
    expected_effective_confidentiality: str | None = None
    expected_pi_status_summary: str | None = None
    expected_de_identification_applied: bool | None = None
    expected_min_suppressed_item_count: int | None = None
    expected_generation_decision: str | None = None
    expected_warning_codes: tuple[str, ...] = field(default_factory=tuple)
    phase4_domain_inputs: dict[str, dict[str, object]] = field(default_factory=dict)
    force_phase5_unavailable: bool = False
    force_phase6_fallback: bool = False


@dataclass(frozen=True)
class ContextScenarioResult:
    scenario: PlannerScenario
    query_plan: QueryPlan
    package: object
    expected_outcome: str
    actual_outcome: str | None
    conflict_codes: tuple[str, ...]
    contamination_types: tuple[str, ...]
    unresolved_states: tuple[str, ...]
    effective_confidentiality: str
    pi_status_summary: str
    de_identification_applied: bool
    suppressed_item_count: int
    generation_decision: str | None
    generator_warnings: tuple[str, ...]
    degraded_state: bool
    generator_visible_grounding_valid: bool
    phase4_state: str
    phase5_state: str
    phase6_state: str
    pass_result: bool


@dataclass(frozen=True)
class ContextEvaluation:
    scenario_results: tuple[ContextScenarioResult, ...]
    outcome_accuracy: float
    conflict_code_recall: float
    contamination_annotation_recall: float
    unresolved_state_accuracy: float
    required_layer_context_inclusion: float
    historical_gap_filling_violations: int
    phase4_authority_violations: int
    provenance_completeness: float
    effective_confidentiality_accuracy: float
    strictest_wins_accuracy: float
    pi_aggregation_accuracy: float
    de_identification_decision_accuracy: float
    required_suppression_accuracy: float
    unsafe_generator_visible_item_count: int
    generation_decision_accuracy: float
    degraded_warning_accuracy: float
    generator_visible_grounding_validity: float
    pi_leakage_count: int
    sensitive_provenance_leakage_count: int


CONTEXT_SCENARIO_FIXTURES: dict[str, ContextScenarioFixture] = {
    "P7-EVAL-001": ContextScenarioFixture(
        expected_outcome="DETERMINISTIC_CURRENT",
        expected_effective_confidentiality="internal",
        expected_pi_status_summary="no",
        expected_de_identification_applied=False,
        expected_generation_decision="allowed",
        phase4_domain_inputs={"payment": {"payment_stage": "confirmation_requirement", "as_of_date": "2026-08-03"}},
    ),
    "P7-EVAL-002": ContextScenarioFixture(
        expected_outcome="DETERMINISTIC_CURRENT",
        phase4_domain_inputs={"expedited_surcharge": {"confirmation_date": "2026-08-19", "event_date": "2026-09-02", "as_of_date": "2026-08-03"}},
    ),
    "P7-EVAL-003": ContextScenarioFixture(
        expected_outcome="DETERMINISTIC_CURRENT",
        phase4_domain_inputs={"capacity": {"scope_type": "rental_type", "scope_code": "entire_venue", "as_of_date": "2026-08-05"}},
    ),
    "P7-EVAL-004": ContextScenarioFixture(
        expected_outcome="DETERMINISTIC_CURRENT",
        phase4_domain_inputs={"capacity": {"scope_type": "venue_space", "scope_code": "studio_space", "configuration_type": "lying_down", "as_of_date": "2026-08-05"}},
    ),
    "P7-EVAL-005": ContextScenarioFixture(
        expected_outcome="DETERMINISTIC_CURRENT",
        phase4_domain_inputs={"space_access": {"mode": "evaluate", "rental_type_code": "entire_venue", "venue_space_code": "one_to_one_room", "as_of_date": "2026-08-05"}},
    ),
    "P7-EVAL-006": ContextScenarioFixture(
        expected_outcome="DETERMINISTIC_CURRENT",
        phase4_domain_inputs={"payment": {"payment_stage": "final_balance", "payment_plan_option": "upfront_30", "booking_lead_time_days": 15, "as_of_date": "2026-08-03"}},
    ),
    "P7-EVAL-007": ContextScenarioFixture(
        expected_outcome="CURRENT_GUIDANCE",
        phase4_domain_inputs={
            "catering_supplier": {
                "catering_arrangement": "external_caterer",
                "rule_type": "arrangement_policy",
                "alcohol_service": False,
                "as_of_date": "2026-08-05",
            },
            "operational_requirements": {
                "rental_type_code": "entire_venue",
                "requirement_type": "grace_period",
                "multi_day": False,
                "as_of_date": "2026-08-05",
            },
        },
    ),
    "P7-EVAL-008": ContextScenarioFixture(
        expected_outcome="DETERMINISTIC_CURRENT",
        phase4_domain_inputs={"catering_supplier": {"rule_type": "vat_classification", "secondary_context_code": "food_or_beverage_products", "alcohol_service": False, "as_of_date": "2026-08-05"}},
    ),
    "P7-EVAL-009": ContextScenarioFixture(
        expected_outcome="CURRENT_GUIDANCE",
        phase4_domain_inputs={"service_rules": {"service_level": "supported_rental", "as_of_date": "2026-08-05"}},
    ),
    "P7-EVAL-010": ContextScenarioFixture(
        expected_outcome="REQUIRES_CONFIRMATION",
        expected_conflict_codes=("TYPE_D_P4_REQUIRES_CONFIRMATION",),
        expected_unresolved_states=("requires_confirmation",),
        phase4_domain_inputs={
            "service_rules": {"service_level": "supported_rental", "as_of_date": "2026-08-05"},
            "facilitator_requirements": {"facilitator_arrangement": "wnc_provided", "as_of_date": "2026-08-05"},
        },
    ),
    "P7-EVAL-011": ContextScenarioFixture(expected_outcome="CURRENT_GUIDANCE"),
    "P7-EVAL-012": ContextScenarioFixture(expected_outcome="CURRENT_GUIDANCE"),
    "P7-EVAL-013": ContextScenarioFixture(expected_outcome="CURRENT_GUIDANCE"),
    "P7-EVAL-014": ContextScenarioFixture(expected_outcome="CURRENT_GUIDANCE"),
    "P7-EVAL-015": ContextScenarioFixture(expected_outcome="HISTORICAL_PRECEDENT"),
    "P7-EVAL-016": ContextScenarioFixture(expected_outcome="HISTORICAL_PRECEDENT"),
    "P7-EVAL-017": ContextScenarioFixture(expected_outcome="HISTORICAL_PRECEDENT"),
    "P7-EVAL-018": ContextScenarioFixture(expected_outcome="HISTORICAL_PRECEDENT"),
    "P7-EVAL-019": ContextScenarioFixture(
        expected_outcome="MIXED_WITH_CURRENT_PRIORITY",
        phase4_domain_inputs={
            "catering_supplier": {"catering_arrangement": "external_caterer", "rule_type": "arrangement_policy", "alcohol_service": False, "as_of_date": "2026-08-05"},
            "operational_requirements": {"rental_type_code": "studio_space", "requirement_type": "grace_period", "multi_day": False, "as_of_date": "2026-08-05"},
        },
    ),
    "P7-EVAL-020": ContextScenarioFixture(
        expected_outcome="MIXED_WITH_CURRENT_PRIORITY",
        phase4_domain_inputs={
            "space_access": {"mode": "evaluate", "rental_type_code": "studio_space", "venue_space_code": "storage_room", "as_of_date": "2026-08-05"},
            "operational_requirements": {"rental_type_code": "studio_space", "requirement_type": "setup_start", "multi_day": False, "as_of_date": "2026-08-05"},
            "catering_supplier": {"catering_arrangement": "external_caterer", "rule_type": "arrangement_policy", "alcohol_service": False, "as_of_date": "2026-08-05"},
        },
    ),
    "P7-EVAL-021": ContextScenarioFixture(
        expected_outcome="MIXED_WITH_CURRENT_PRIORITY",
        phase4_domain_inputs={
            "service_rules": {"service_level": "supported_rental", "as_of_date": "2026-08-05"},
            "facilitator_requirements": {"facilitator_arrangement": "none", "as_of_date": "2026-08-05"},
        },
    ),
    "P7-EVAL-022": ContextScenarioFixture(
        expected_outcome="MIXED_WITH_CURRENT_PRIORITY",
        phase4_domain_inputs={"operational_requirements": {"rental_type_code": "studio_space", "requirement_type": "setup_start", "multi_day": False, "as_of_date": "2026-08-05"}},
    ),
    "P7-EVAL-023": ContextScenarioFixture(
        expected_outcome="MIXED_WITH_CURRENT_PRIORITY",
        phase4_domain_inputs={
            "catering_supplier": {"catering_arrangement": "external_caterer", "rule_type": "arrangement_policy", "alcohol_service": True, "as_of_date": "2026-08-05"},
            "operational_requirements": {"rental_type_code": "studio_space", "requirement_type": "grace_period", "multi_day": False, "as_of_date": "2026-08-05"},
        },
    ),
    "P7-EVAL-024": ContextScenarioFixture(
        expected_outcome="REQUIRES_CONFIRMATION",
        expected_conflict_codes=("TYPE_D_P4_REQUIRES_CONFIRMATION",),
        expected_unresolved_states=("requires_confirmation",),
        phase4_domain_inputs={
            "technical_capability": {"requirement_code": "custom_technical_setup", "as_of_date": "2026-08-05"},
            "technical_inventory": {"equipment_code": "basic_projector", "requested_quantity": 2},
        },
    ),
    "P7-EVAL-025": ContextScenarioFixture(
        expected_outcome="INSUFFICIENT_CURRENT_AUTHORITY",
        expected_conflict_codes=("TYPE_C_P6_EXISTS_BUT_CURRENT_MISSING",),
        expected_contamination_types=("historical_price_to_current_price",),
        expected_unresolved_states=("insufficient_current_authority",),
        expected_effective_confidentiality="restricted",
        expected_de_identification_applied=True,
        expected_generation_decision="allowed_with_restrictions",
        expected_warning_codes=("current_authority_insufficient", "historical_value_context_only"),
        phase4_domain_inputs={
            "space_access": {"mode": "evaluate", "rental_type_code": "studio_space", "venue_space_code": "storage_room", "as_of_date": "2026-08-05"},
            "operational_requirements": {"rental_type_code": "studio_space", "requirement_type": "setup_start", "multi_day": False, "as_of_date": "2026-08-05"},
            "catering_supplier": {"catering_arrangement": "external_caterer", "rule_type": "arrangement_policy", "alcohol_service": False, "as_of_date": "2026-08-05"},
        },
    ),
    "P7-EVAL-026": ContextScenarioFixture(
        expected_outcome="INSUFFICIENT_CURRENT_AUTHORITY",
        expected_conflict_codes=("TYPE_C_P6_EXISTS_BUT_CURRENT_MISSING",),
        expected_contamination_types=("historical_person_capability_to_current_service",),
        expected_unresolved_states=("insufficient_current_authority",),
        expected_effective_confidentiality="restricted",
        expected_de_identification_applied=True,
        expected_generation_decision="allowed_with_restrictions",
    ),
    "P7-EVAL-027": ContextScenarioFixture(
        expected_outcome="INSUFFICIENT_CURRENT_AUTHORITY",
        expected_conflict_codes=("TYPE_C_P6_EXISTS_BUT_CURRENT_MISSING",),
        expected_contamination_types=("historical_concession_to_current_policy",),
        expected_unresolved_states=("insufficient_current_authority",),
    ),
    "P7-EVAL-028": ContextScenarioFixture(
        expected_outcome="INSUFFICIENT_CURRENT_AUTHORITY",
        expected_conflict_codes=("TYPE_C_P6_EXISTS_BUT_CURRENT_MISSING",),
        expected_contamination_types=("historical_overtime_handling_to_current_rate",),
        expected_unresolved_states=("insufficient_current_authority",),
    ),
    "P7-EVAL-029": ContextScenarioFixture(
        expected_outcome="REQUIRES_CONFIRMATION",
        expected_contamination_types=("historical_legal_solution_to_current_guidance",),
        expected_unresolved_states=("requires_confirmation",),
        expected_de_identification_applied=True,
        expected_generation_decision="allowed_with_restrictions",
    ),
    "P7-EVAL-030": ContextScenarioFixture(
        expected_outcome="DETERMINISTIC_CURRENT",
        expected_conflict_codes=("TYPE_A_P4_BEATS_P6",),
        phase4_domain_inputs={"operational_requirements": {"rental_type_code": "studio_space", "requirement_type": "setup_start", "multi_day": False, "as_of_date": "2026-08-05"}},
    ),
    "P7-EVAL-031": ContextScenarioFixture(
        expected_outcome="DETERMINISTIC_CURRENT",
        expected_conflict_codes=("TYPE_A_P4_BEATS_P6",),
        expected_contamination_types=("historical_room_use_to_current_access_right",),
        phase4_domain_inputs={"space_access": {"mode": "evaluate", "rental_type_code": "studio_space", "venue_space_code": "back_office", "as_of_date": "2026-08-05"}},
    ),
    "P7-EVAL-032": ContextScenarioFixture(
        expected_outcome="MIXED_WITH_CURRENT_PRIORITY",
        expected_conflict_codes=("TYPE_B_P5_BEATS_P6",),
        phase4_domain_inputs={"service_rules": {"service_level": "supported_rental", "as_of_date": "2026-08-05"}},
    ),
    "P7-EVAL-033": ContextScenarioFixture(
        expected_outcome="INSUFFICIENT_CURRENT_AUTHORITY",
        expected_unresolved_states=("insufficient_current_authority",),
    ),
    "P7-EVAL-034": ContextScenarioFixture(
        expected_outcome="INSUFFICIENT_CURRENT_AUTHORITY",
        expected_unresolved_states=("insufficient_current_authority",),
    ),
    "P7-EVAL-035": ContextScenarioFixture(
        expected_outcome="REQUIRES_CONFIRMATION",
        expected_conflict_codes=("TYPE_D_P4_REQUIRES_CONFIRMATION",),
        expected_unresolved_states=("requires_confirmation",),
        phase4_domain_inputs={
            "technical_capability": {"requirement_code": "custom_technical_setup", "as_of_date": "2026-08-05"},
            "technical_inventory": {"equipment_code": "basic_projector", "requested_quantity": 2},
        },
    ),
    "P7-EVAL-036": ContextScenarioFixture(
        expected_outcome="REQUIRES_CONFIRMATION",
        expected_conflict_codes=("TYPE_D_P4_REQUIRES_CONFIRMATION",),
        expected_unresolved_states=("requires_confirmation",),
        phase4_domain_inputs={"capacity": {"scope_type": "venue_space", "scope_code": "one_to_one_room", "guest_count": 6, "as_of_date": "2026-08-05"}},
    ),
    "P7-EVAL-037": ContextScenarioFixture(
        expected_outcome="HISTORICAL_PRECEDENT",
        force_phase6_fallback=True,
        expected_generation_decision="allowed_with_restrictions",
        expected_warning_codes=("historical_retrieval_degraded",),
    ),
    "P7-EVAL-038": ContextScenarioFixture(
        expected_outcome="DETERMINISTIC_CURRENT",
        expected_conflict_codes=("TYPE_E_P5_FAILURE_P4_SURVIVES",),
        expected_generation_decision="allowed_with_restrictions",
        expected_warning_codes=("current_guidance_unavailable",),
        phase4_domain_inputs={"payment": {"payment_stage": "confirmation_requirement", "as_of_date": "2026-08-03"}},
        force_phase5_unavailable=True,
    ),
    "P7-EVAL-039": ContextScenarioFixture(
        expected_outcome="MIXED_WITH_CURRENT_PRIORITY",
        expected_conflict_codes=("TYPE_G_CONFIDENTIALITY_ESCALATION",),
        expected_effective_confidentiality="restricted",
        expected_de_identification_applied=True,
        expected_generation_decision="allowed_with_restrictions",
        expected_warning_codes=("pi_deidentified",),
    ),
    "P7-EVAL-040": ContextScenarioFixture(
        expected_outcome="MIXED_WITH_CURRENT_PRIORITY",
        expected_conflict_codes=("TYPE_G_CONFIDENTIALITY_ESCALATION",),
        expected_effective_confidentiality="restricted",
        expected_de_identification_applied=True,
        expected_generation_decision="allowed_with_restrictions",
        expected_warning_codes=("pi_deidentified",),
    ),
}


def evaluate_context_authority(
    build_context_package_fn: Callable[..., object] = build_context_package,
) -> ContextEvaluation:
    scenario_results: list[ContextScenarioResult] = []
    expected_conflicts = 0
    matched_conflicts = 0
    expected_contaminations = 0
    matched_contaminations = 0
    expected_unresolved = 0
    matched_unresolved = 0
    required_layer_inclusions = 0
    required_layer_total = 0
    provenance_items = 0
    provenance_complete = 0
    historical_gap_filling_violations = 0
    phase4_authority_violations = 0
    expected_effective_confidentiality = 0
    matched_effective_confidentiality = 0
    expected_pi_states = 0
    matched_pi_states = 0
    expected_deidentification = 0
    matched_deidentification = 0
    expected_suppression = 0
    matched_suppression = 0
    expected_generation_decisions = 0
    matched_generation_decisions = 0
    expected_warning_total = 0
    matched_warning_total = 0
    generator_visible_grounding_valid_total = 0
    generator_visible_grounding_valid_matched = 0
    unsafe_generator_visible_item_count = 0
    pi_leakage_count = 0
    sensitive_provenance_leakage_count = 0

    for scenario in EVALUATION_SCENARIOS:
        fixture = CONTEXT_SCENARIO_FIXTURES[scenario.scenario_id]
        planner_fn = _planner_for_fixture(scenario, fixture)
        phase5_executor = _phase5_executor_for_fixture(fixture)
        phase6_executor = _phase6_executor_for_fixture(scenario, fixture)
        package = build_context_package_fn(
            scenario.question,
            planner_fn=planner_fn,
            phase5_executor=phase5_executor,
            phase6_executor=phase6_executor,
        )
        actual_outcome = package.authority_resolution.overall_outcome_classification
        conflict_codes = tuple(record.conflict_type_code for record in package.authority_resolution.conflict_records)
        contamination_types = tuple(annotation.forbidden_inference_type for annotation in package.authority_resolution.contamination_annotations)
        unresolved_states = tuple(record.reasoning_state for record in package.authority_resolution.unresolved_authority_records)
        effective_confidentiality = package.confidentiality_state.effective_confidentiality_level
        pi_status_summary = package.confidentiality_state.personal_information_status_summary
        de_identification_applied = bool(
            package.generator_safe_context
            and any(
                projection.visibility == "de_identified"
                for projection in package.generator_safe_context.projections
            )
        )
        suppressed_item_count = len(package.confidentiality_state.suppressed_item_ids)
        generation_decision = (
            package.generator_safe_context.generation_decision
            if package.generator_safe_context is not None
            else None
        )
        generator_warnings = tuple(package.generator_policy.required_warnings)
        degraded_state = package.degraded_retrieval_state.any_degradation
        generator_visible_grounding_valid = _generator_visible_grounding_is_valid(package)
        unsafe_generator_visible_item_count += _unsafe_generator_visible_item_count(package)
        pi_leakage_count += _pi_leakage_count(package)
        sensitive_provenance_leakage_count += _sensitive_provenance_leakage_count(package)

        expected_conflicts += len(fixture.expected_conflict_codes)
        matched_conflicts += sum(1 for code in fixture.expected_conflict_codes if code in conflict_codes)
        expected_contaminations += len(fixture.expected_contamination_types)
        matched_contaminations += sum(1 for code in fixture.expected_contamination_types if code in contamination_types)
        expected_unresolved += len(fixture.expected_unresolved_states)
        matched_unresolved += sum(1 for state in fixture.expected_unresolved_states if state in unresolved_states)
        if fixture.expected_effective_confidentiality is not None:
            expected_effective_confidentiality += 1
            matched_effective_confidentiality += int(
                fixture.expected_effective_confidentiality == effective_confidentiality
            )
        if fixture.expected_pi_status_summary is not None:
            expected_pi_states += 1
            matched_pi_states += int(
                fixture.expected_pi_status_summary == pi_status_summary
            )
        if fixture.expected_de_identification_applied is not None:
            expected_deidentification += 1
            matched_deidentification += int(
                fixture.expected_de_identification_applied == de_identification_applied
            )
        if fixture.expected_min_suppressed_item_count is not None:
            expected_suppression += 1
            matched_suppression += int(
                suppressed_item_count >= fixture.expected_min_suppressed_item_count
            )
        if fixture.expected_generation_decision is not None:
            expected_generation_decisions += 1
            matched_generation_decisions += int(
                fixture.expected_generation_decision == generation_decision
            )
        expected_warning_total += len(fixture.expected_warning_codes)
        matched_warning_total += sum(
            1 for warning in fixture.expected_warning_codes if warning in generator_warnings
        )
        generator_visible_grounding_valid_total += 1
        generator_visible_grounding_valid_matched += int(generator_visible_grounding_valid)

        requested_layers = set(package.routing_plan.required_layers)
        contexts_by_layer = {
            LAYER_ID_PHASE_4: package.phase_4_context,
            LAYER_ID_PHASE_5: package.phase_5_context,
            LAYER_ID_PHASE_6: package.phase_6_context,
        }
        layer_states = {
            record.layer_id: record.execution_state
            for record in package.layer_execution
        }
        for layer_id in requested_layers:
            required_layer_total += 1
            record = next(record for record in package.layer_execution if record.layer_id == layer_id)
            if record.normalized_items == contexts_by_layer[layer_id]:
                required_layer_inclusions += 1

        for item in package.phase_4_context + package.phase_5_context + package.phase_6_context:
            provenance_items += 1
            if item.provenance.source_codes and item.provenance.primary_source_locator is not None:
                provenance_complete += 1

        if scenario.scenario_id in {"P7-EVAL-025", "P7-EVAL-026", "P7-EVAL-027", "P7-EVAL-028"} and actual_outcome != "INSUFFICIENT_CURRENT_AUTHORITY":
            historical_gap_filling_violations += 1
        if scenario.scenario_id in {"P7-EVAL-030", "P7-EVAL-031"} and actual_outcome == "HISTORICAL_PRECEDENT":
            phase4_authority_violations += 1

        pass_result = (
            actual_outcome == fixture.expected_outcome
            and all(code in conflict_codes for code in fixture.expected_conflict_codes)
            and all(code in contamination_types for code in fixture.expected_contamination_types)
            and all(state in unresolved_states for state in fixture.expected_unresolved_states)
            and (
                fixture.expected_effective_confidentiality is None
                or fixture.expected_effective_confidentiality == effective_confidentiality
            )
            and (
                fixture.expected_pi_status_summary is None
                or fixture.expected_pi_status_summary == pi_status_summary
            )
            and (
                fixture.expected_de_identification_applied is None
                or fixture.expected_de_identification_applied == de_identification_applied
            )
            and (
                fixture.expected_min_suppressed_item_count is None
                or suppressed_item_count >= fixture.expected_min_suppressed_item_count
            )
            and (
                fixture.expected_generation_decision is None
                or fixture.expected_generation_decision == generation_decision
            )
            and all(warning in generator_warnings for warning in fixture.expected_warning_codes)
            and generator_visible_grounding_valid
        )
        scenario_results.append(
            ContextScenarioResult(
                scenario=scenario,
                query_plan=package.routing_plan,
                package=package,
                expected_outcome=fixture.expected_outcome,
                actual_outcome=actual_outcome,
                conflict_codes=conflict_codes,
                contamination_types=contamination_types,
                unresolved_states=unresolved_states,
                effective_confidentiality=effective_confidentiality,
                pi_status_summary=pi_status_summary,
                de_identification_applied=de_identification_applied,
                suppressed_item_count=suppressed_item_count,
                generation_decision=generation_decision,
                generator_warnings=generator_warnings,
                degraded_state=degraded_state,
                generator_visible_grounding_valid=generator_visible_grounding_valid,
                phase4_state=layer_states[LAYER_ID_PHASE_4],
                phase5_state=layer_states[LAYER_ID_PHASE_5],
                phase6_state=layer_states[LAYER_ID_PHASE_6],
                pass_result=pass_result,
            )
        )

    return ContextEvaluation(
        scenario_results=tuple(scenario_results),
        outcome_accuracy=sum(1 for result in scenario_results if result.actual_outcome == result.expected_outcome) / len(scenario_results),
        conflict_code_recall=(matched_conflicts / expected_conflicts) if expected_conflicts else 1.0,
        contamination_annotation_recall=(matched_contaminations / expected_contaminations) if expected_contaminations else 1.0,
        unresolved_state_accuracy=(matched_unresolved / expected_unresolved) if expected_unresolved else 1.0,
        required_layer_context_inclusion=(required_layer_inclusions / required_layer_total) if required_layer_total else 1.0,
        historical_gap_filling_violations=historical_gap_filling_violations,
        phase4_authority_violations=phase4_authority_violations,
        provenance_completeness=(provenance_complete / provenance_items) if provenance_items else 1.0,
        effective_confidentiality_accuracy=(
            matched_effective_confidentiality / expected_effective_confidentiality
            if expected_effective_confidentiality
            else 1.0
        ),
        strictest_wins_accuracy=(
            matched_effective_confidentiality / expected_effective_confidentiality
            if expected_effective_confidentiality
            else 1.0
        ),
        pi_aggregation_accuracy=(
            matched_pi_states / expected_pi_states if expected_pi_states else 1.0
        ),
        de_identification_decision_accuracy=(
            matched_deidentification / expected_deidentification
            if expected_deidentification
            else 1.0
        ),
        required_suppression_accuracy=(
            matched_suppression / expected_suppression
            if expected_suppression
            else 1.0
        ),
        unsafe_generator_visible_item_count=unsafe_generator_visible_item_count,
        generation_decision_accuracy=(
            matched_generation_decisions / expected_generation_decisions
            if expected_generation_decisions
            else 1.0
        ),
        degraded_warning_accuracy=(
            matched_warning_total / expected_warning_total
            if expected_warning_total
            else 1.0
        ),
        generator_visible_grounding_validity=(
            generator_visible_grounding_valid_matched / generator_visible_grounding_valid_total
            if generator_visible_grounding_valid_total
            else 1.0
        ),
        pi_leakage_count=pi_leakage_count,
        sensitive_provenance_leakage_count=sensitive_provenance_leakage_count,
    )


def _planner_for_fixture(
    scenario: PlannerScenario,
    fixture: ContextScenarioFixture,
) -> Callable[..., QueryPlan]:
    def planner_fn(query_text: str, query_context=None, runtime_configuration=None) -> QueryPlan:
        plan = plan_query(query_text, query_context=query_context, runtime_configuration=runtime_configuration)
        if fixture.phase4_domain_inputs and plan.phase_4 is not None:
            domain_inputs = {
                domain: inputs
                for domain, inputs in fixture.phase4_domain_inputs.items()
                if domain in plan.phase_4.domains
            }
            plan = QueryPlan(
                query_text=plan.query_text,
                query_class=plan.query_class,
                routing_confidence=plan.routing_confidence,
                ambiguity_flags=plan.ambiguity_flags,
                required_layers=plan.required_layers,
                optional_layers=plan.optional_layers,
                phase_4=Phase4RoutingIntent(
                    required=plan.phase_4.required,
                    domains=plan.phase_4.domains,
                    domain_inputs=domain_inputs,
                    reason_codes=plan.phase_4.reason_codes,
                ),
                phase_5=plan.phase_5,
                phase_6=plan.phase_6,
                safety_overrides=plan.safety_overrides,
                reason_codes=plan.reason_codes,
            )
        return plan

    return planner_fn


def _phase5_executor_for_fixture(
    fixture: ContextScenarioFixture,
) -> Callable[..., LayerExecutionRecord] | None:
    if not fixture.force_phase5_unavailable:
        return None

    def executor(query_plan, query_context=None, runtime_configuration=None):
        return LayerExecutionRecord(
            layer_id=LAYER_ID_PHASE_5,
            requested=True,
            execution_state="unavailable",
            reasoning_state=None,
            fallback_reason=None,
            error_category="phase5_unavailable_forced",
            safe_error_message="Forced Phase 5 outage for benchmark scenario.",
            result_count=0,
            normalized_items=(),
        )

    return executor


def _phase6_executor_for_fixture(
    scenario: PlannerScenario,
    fixture: ContextScenarioFixture,
) -> Callable[..., LayerExecutionRecord] | None:
    if not fixture.force_phase6_fallback:
        return None

    def retrieval_fn(_query_text: str, **_kwargs):
        rows = retrieve_historical_precedents("whole venue clearing", result_limit=5)["results"][:3]
        return {
            "query_text": "whole venue clearing",
            "retrieval_mode_requested": "hybrid",
            "retrieval_mode_used": "fts_fallback",
            "fallback_used": True,
            "fallback_reason": "historical_embedding_corpus_incomplete",
            "strategy_code": "historical_rrf_balanced",
            "configuration_code": "historical_rrf_balanced_d20",
            "result_limit_requested": 5,
            "result_limit_used": 5,
            "candidate_pool_limit": None,
            "embedding_model": None,
            "historical_embedding_state": None,
            "result_count": len(rows),
            "timing_ms": {"embedding_generation": None, "retrieval": 1.0, "total": 1.0},
            "results": rows,
        }

    def executor(query_plan, query_context=None, runtime_configuration=None):
        return execute_phase6_plan(
            query_plan,
            query_context=query_context,
            runtime_configuration=runtime_configuration,
            historical_retrieval_fn=retrieval_fn,
        )

    return executor


def _generator_visible_grounding_is_valid(package) -> bool:
    generator_safe_context = package.generator_safe_context
    if generator_safe_context is None:
        return False
    visible_item_ids = {
        projection.item_id
        for projection in generator_safe_context.projections
        if projection.visibility != "suppressed"
    }
    return all(
        reference.item_id in visible_item_ids
        for reference in generator_safe_context.grounding
    )


def _unsafe_generator_visible_item_count(package) -> int:
    generator_safe_context = package.generator_safe_context
    if generator_safe_context is None:
        return 0
    known_items = {
        item.item_id: item
        for item in (
            package.phase_4_context + package.phase_5_context + package.phase_6_context
        )
    }
    unsafe_count = 0
    for projection in generator_safe_context.projections:
        if projection.visibility == "suppressed":
            continue
        item = known_items[projection.item_id]
        if (
            item.source_layer_role == SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT
            and item.sensitivity.confidentiality_level == CONFIDENTIALITY_LEVEL_RESTRICTED
            and item.summary_text is not None
            and projection.generator_summary_text == item.summary_text
        ):
            unsafe_count += 1
    return unsafe_count


def _pi_leakage_count(package) -> int:
    generator_safe_context = package.generator_safe_context
    if generator_safe_context is None:
        return 0
    known_items = {
        item.item_id: item
        for item in (
            package.phase_4_context + package.phase_5_context + package.phase_6_context
        )
    }
    leakage_count = 0
    for projection in generator_safe_context.projections:
        if projection.visibility == "suppressed":
            continue
        item = known_items[projection.item_id]
        if (
            item.sensitivity.personal_information_status == PERSONAL_INFORMATION_STATUS_YES
            and projection.visibility == "visible"
        ):
            leakage_count += 1
    return leakage_count


def _sensitive_provenance_leakage_count(package) -> int:
    generator_safe_context = package.generator_safe_context
    if generator_safe_context is None:
        return 0
    known_items = {
        item.item_id: item
        for item in (
            package.phase_4_context + package.phase_5_context + package.phase_6_context
        )
    }
    leakage_count = 0
    for reference in generator_safe_context.grounding:
        item = known_items[reference.item_id]
        raw_locator = item.provenance.primary_source_locator
        if raw_locator is None or reference.safe_locator is None:
            continue
        if reference.safe_locator == raw_locator and (
            item.sensitivity.confidentiality_level == CONFIDENTIALITY_LEVEL_RESTRICTED
            or item.sensitivity.personal_information_status == PERSONAL_INFORMATION_STATUS_YES
        ):
            leakage_count += 1
    return leakage_count


__all__ = [
    "CONTEXT_SCENARIO_FIXTURES",
    "ContextEvaluation",
    "ContextScenarioFixture",
    "ContextScenarioResult",
    "evaluate_context_authority",
]
