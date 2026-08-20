from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean, median
from typing import Any
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.phase_08_workflow.operator_harness import (  # noqa: E402
    OperatorHarnessClient,
    OperatorHarnessConfig,
)


DEFAULT_AUTH_FILE = REPO_ROOT / "Staging Authentications.txt"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "docs" / "staging" / "calibration"

OBS_FACT = "fact_candidate"
OBS_REQUEST = "request_candidate"
OBS_CHANGE = "change_candidate"
OBS_CONFIRM = "confirmation_candidate"
OBS_DECISION = "case_decision_candidate"
OBS_REQUIREMENT = "requirement_evidence_candidate"

CLAIM_NEW = "new_information"
CLAIM_CHANGE = "change_request"
CLAIM_CONFIRM = "confirmation"
CLAIM_EXCEPTION = "exception_request"
CLAIM_REQUIREMENT = "requirement_evidence"

CORE_FIELD_TO_QUESTION = {
    "active_event_window": "requested_event_timing",
    "guest_count": "expected_guest_count",
    "requested_rental_scope": "requested_rental_scope",
    "event_type": "requested_event_type",
}

CATEGORY_LABELS = {
    "A": "straightforward",
    "B": "missing_information",
    "C": "capacity_and_space_constraints",
    "D": "pricing_and_fees",
    "E": "cancellation_and_rescheduling",
    "F": "catering_and_external_suppliers",
    "G": "technical_capability",
    "H": "facilitators_and_services",
    "I": "authority_conflicts",
    "J": "conflicting_client_information",
    "K": "unusual_and_ambiguous",
    "L": "commercial_pressure",
    "M": "historical_precedent_temptation",
    "N": "confidentiality_and_pi_safety",
    "O": "insufficient_knowledge",
}

SPECIFIC_SCOPE_CODES = frozenset({"studio_space", "entire_venue"})


def _now_slug() -> str:
    return time.strftime("%Y%m%d-%H%M%S", time.gmtime())


def _json_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _schedule(start: str, end: str) -> dict[str, str]:
    return {
        "active_event_start": start,
        "active_event_end": end,
    }


@dataclass(frozen=True)
class ObservationSpec:
    field_code: str
    value: Any
    observation_type: str = OBS_FACT
    claim_kind: str = CLAIM_NEW
    source_excerpt: str | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "field_code": self.field_code,
            "value": self.value,
            "observation_type": self.observation_type,
            "claim_kind": self.claim_kind,
            "source_excerpt": self.source_excerpt,
        }


@dataclass(frozen=True)
class StageSpec:
    name: str
    observations: tuple[ObservationSpec, ...] = ()
    run_waiting: bool = False
    generate_draft: bool = False


@dataclass(frozen=True)
class ScenarioExpectations:
    relevant_rules: tuple[str, ...] = ()
    expected_current_fields: dict[str, Any] = field(default_factory=dict)
    expected_absent_current_fields: tuple[str, ...] = ()
    expected_open_question_types: tuple[str, ...] = ()
    forbidden_open_question_types: tuple[str, ...] = ()
    expected_proposed_change_count: int | None = None
    expected_reschedule_request_count: int | None = None
    expected_booking_fee_baseline: str | None = None
    expected_effective_booking_fee: str | None = None
    expected_effective_fee_matches_baseline: bool = False
    expected_case_decision_status: str | None = None
    expected_draft: bool = False
    expected_draft_question_types: tuple[str, ...] = ()
    expected_confirmation_required: str | None = None
    expected_feasibility_as_requested: str | None = None
    expected_material_blocker: bool = False
    expected_human_confirmation_required: bool = False
    forbidden_draft_fragments: tuple[str, ...] = ()
    must_not_activate_exception: bool = False
    must_not_create_reschedule_for_same_schedule: bool = False
    notes: str = ""


@dataclass(frozen=True)
class CalibrationScenario:
    scenario_id: str
    category_code: str
    title: str
    description: str
    display_name: str
    client_label: str
    contact_email: str
    event_reference: str
    stages: tuple[StageSpec, ...]
    expectations: ScenarioExpectations
    phase6_relevant: bool = False

    def to_benchmark_payload(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "category_code": self.category_code,
            "category_label": CATEGORY_LABELS[self.category_code],
            "title": self.title,
            "description": self.description,
            "display_name": self.display_name,
            "event_reference": self.event_reference,
            "phase6_relevant": self.phase6_relevant,
            "stages": [
                {
                    "name": stage.name,
                    "run_waiting": stage.run_waiting,
                    "generate_draft": stage.generate_draft,
                    "observations": [obs.to_payload() for obs in stage.observations],
                }
                for stage in self.stages
            ],
            "expectations": {
                **asdict(self.expectations),
                "relevant_rules": list(self.expectations.relevant_rules),
                "expected_absent_current_fields": list(self.expectations.expected_absent_current_fields),
                "expected_open_question_types": list(self.expectations.expected_open_question_types),
                "forbidden_open_question_types": list(self.expectations.forbidden_open_question_types),
                "expected_draft_question_types": list(self.expectations.expected_draft_question_types),
                "forbidden_draft_fragments": list(self.expectations.forbidden_draft_fragments),
            },
        }


@dataclass(frozen=True)
class DraftSummary:
    subject: str | None
    body_text: str | None
    question_types: tuple[str, ...]
    question_prompts: tuple[str, ...]


@dataclass(frozen=True)
class ActualSnapshot:
    rental_case_id: int
    case_reference_code: str
    case_revision: int
    rental_type_code: str | None
    active_event_window: dict[str, str] | None
    current_facts: dict[str, Any]
    active_open_question_types: tuple[str, ...]
    active_open_question_texts: tuple[str, ...]
    open_blocker_count: int
    open_blocker_types: tuple[str, ...]
    open_blocker_rule_codes: tuple[str, ...]
    active_workflow_action_types: tuple[str, ...]
    active_workflow_action_statuses: tuple[str, ...]
    proposed_change_count: int
    reschedule_request_count: int
    case_decision_statuses: tuple[str, ...]
    reasoning_projection_semantic_states: tuple[str, ...]
    commercial_snapshot: dict[str, str]
    feasibility_snapshot: dict[str, str]
    missing_client_information: tuple[str, ...]
    next_action_labels: tuple[str, ...]
    draft: DraftSummary | None


@dataclass(frozen=True)
class ScoredCase:
    scenario_id: str
    category_code: str
    rental_case_id: int
    case_reference_code: str
    scores: dict[str, float]
    edit_burden: str
    critical_failures: tuple[str, ...]
    unsupported_claim_count: int
    factual_correction_count: int
    missing_info_success: bool
    authority_success: bool
    confidentiality_success: bool
    correct_next_action: bool
    failures: tuple[str, ...]
    diagnosed_layer: str
    root_cause: str
    actual: dict[str, Any]


def obs(
    field_code: str,
    value: Any,
    *,
    observation_type: str = OBS_FACT,
    claim_kind: str = CLAIM_NEW,
    source_excerpt: str | None = None,
) -> ObservationSpec:
    return ObservationSpec(
        field_code=field_code,
        value=value,
        observation_type=observation_type,
        claim_kind=claim_kind,
        source_excerpt=source_excerpt,
    )


def stage(
    name: str,
    *observations: ObservationSpec,
    run_waiting: bool = False,
    generate_draft: bool = False,
) -> StageSpec:
    return StageSpec(
        name=name,
        observations=tuple(observations),
        run_waiting=run_waiting,
        generate_draft=generate_draft,
    )


def inquiry_scenario(
    scenario_id: str,
    category_code: str,
    title: str,
    *,
    description: str,
    schedule: dict[str, str] | None = None,
    guest_count: int | None = None,
    scope: str | None = None,
    event_type: str | None = None,
    extras: tuple[ObservationSpec, ...] = (),
    expected_booking_fee_baseline: str | None = None,
    expected_effective_booking_fee: str | None = None,
    expected_effective_fee_matches_baseline: bool = False,
    expected_material_blocker: bool = False,
    expected_confirmation_required: str | None = None,
    expected_feasibility_as_requested: str | None = None,
    phase6_relevant: bool = False,
    forbidden_draft_fragments: tuple[str, ...] = (),
    notes: str = "",
) -> CalibrationScenario:
    observations: list[ObservationSpec] = list(extras)
    expected_current_fields: dict[str, Any] = {}
    expected_absent: list[str] = []
    expected_questions: list[str] = []

    if schedule is None:
        expected_questions.append("requested_event_timing")
        expected_absent.append("active_event_window")
    else:
        observations.append(obs("active_event_window", schedule))
        expected_current_fields["active_event_window"] = schedule

    if guest_count is None:
        expected_questions.append("expected_guest_count")
        expected_absent.append("guest_count")
    else:
        observations.append(obs("guest_count", guest_count))
        expected_current_fields["guest_count"] = guest_count

    if scope is None:
        expected_questions.append("requested_rental_scope")
        expected_absent.append("requested_rental_scope")
    else:
        observations.append(obs("requested_rental_scope", scope))
        if scope in SPECIFIC_SCOPE_CODES:
            expected_current_fields["requested_rental_scope"] = scope
        else:
            expected_questions.append("requested_rental_scope")
            expected_absent.append("requested_rental_scope")

    if event_type is None:
        expected_questions.append("requested_event_type")
        expected_absent.append("event_type")
    else:
        observations.append(obs("event_type", event_type))
        expected_current_fields["event_type"] = event_type

    stages = (
        stage("bootstrap_open_questions"),
        stage(
            "client_answers",
            *observations,
            run_waiting=bool(expected_questions),
            generate_draft=bool(expected_questions),
        ),
    )

    return CalibrationScenario(
        scenario_id=scenario_id,
        category_code=category_code,
        title=title,
        description=description,
        display_name=f"{scenario_id} {title}",
        client_label=f"{scenario_id} Synthetic Client",
        contact_email=f"{scenario_id.lower()}@example.test",
        event_reference=f"{scenario_id} synthetic reference",
        stages=stages,
        expectations=ScenarioExpectations(
            relevant_rules=(
                "Phase 8 inquiry-intake core field governance",
                "Phase 4 booking-fee projection" if expected_booking_fee_baseline else "Phase 8 working-proposal projection",
            ),
            expected_current_fields=expected_current_fields,
            expected_absent_current_fields=tuple(expected_absent),
            expected_open_question_types=tuple(expected_questions),
            expected_booking_fee_baseline=expected_booking_fee_baseline,
            expected_effective_booking_fee=expected_effective_booking_fee,
            expected_effective_fee_matches_baseline=expected_effective_fee_matches_baseline,
            expected_draft=bool(expected_questions),
            expected_draft_question_types=tuple(expected_questions),
            expected_confirmation_required=expected_confirmation_required,
            expected_feasibility_as_requested=expected_feasibility_as_requested,
            expected_material_blocker=expected_material_blocker or bool(expected_questions),
            expected_human_confirmation_required=expected_material_blocker,
            forbidden_draft_fragments=forbidden_draft_fragments,
            notes=notes,
        ),
        phase6_relevant=phase6_relevant,
    )


def reschedule_scenario(
    scenario_id: str,
    *,
    title: str,
    initial_schedule: dict[str, str],
    changed_schedule: dict[str, str],
    same_schedule_confirmation: bool = False,
) -> CalibrationScenario:
    second_observation = obs(
        "active_event_window",
        changed_schedule,
        observation_type=OBS_CONFIRM if same_schedule_confirmation else OBS_CHANGE,
        claim_kind=CLAIM_CONFIRM if same_schedule_confirmation else CLAIM_CHANGE,
        source_excerpt="Client follow-up schedule message.",
    )
    return CalibrationScenario(
        scenario_id=scenario_id,
        category_code="E",
        title=title,
        description="Reschedule / schedule-change behavior against the governed intake path.",
        display_name=f"{scenario_id} {title}",
        client_label=f"{scenario_id} Synthetic Client",
        contact_email=f"{scenario_id.lower()}@example.test",
        event_reference=f"{scenario_id} synthetic reference",
        stages=(
            stage("bootstrap_open_questions"),
            stage(
                "establish_current",
                obs("active_event_window", initial_schedule),
                obs("guest_count", 32),
                obs("requested_rental_scope", "studio_space"),
                obs("event_type", "workshop"),
            ),
            stage("follow_up", second_observation, run_waiting=True),
        ),
        expectations=ScenarioExpectations(
            relevant_rules=(
                "Phase 8 governed schedule promotion",
                "Phase 8 reschedule-request creation",
            ),
            expected_current_fields={
                "active_event_window": initial_schedule,
                "guest_count": 32,
                "requested_rental_scope": "studio_space",
                "event_type": "workshop",
            },
            expected_open_question_types=(),
            expected_proposed_change_count=0,
            expected_reschedule_request_count=0 if same_schedule_confirmation else 1,
            expected_booking_fee_baseline="EUR 75 excl. VAT",
            expected_effective_booking_fee="EUR 75 excl. VAT",
            expected_material_blocker=False,
            must_not_create_reschedule_for_same_schedule=same_schedule_confirmation,
            notes=(
                "Same-schedule confirmations must not create a no-op RescheduleRequest."
                if same_schedule_confirmation
                else "Changed schedules should create a governed reschedule request."
            ),
        ),
    )


def conflicting_observation_scenario(
    scenario_id: str,
    title: str,
    *,
    field_code: str,
    first_value: Any,
    second_value: Any,
    expected_question_type: str,
    description: str,
) -> CalibrationScenario:
    return CalibrationScenario(
        scenario_id=scenario_id,
        category_code="J",
        title=title,
        description=description,
        display_name=f"{scenario_id} {title}",
        client_label=f"{scenario_id} Synthetic Client",
        contact_email=f"{scenario_id.lower()}@example.test",
        event_reference=f"{scenario_id} synthetic reference",
        stages=(
            stage("bootstrap_open_questions"),
            stage(
                "client_answers",
                obs("active_event_window", _schedule("2026-11-30T10:00:00Z", "2026-11-30T13:00:00Z")),
                obs("event_type", "networking social"),
                obs(field_code, first_value),
                obs(field_code, second_value),
                run_waiting=True,
                generate_draft=True,
            ),
        ),
        expectations=ScenarioExpectations(
            relevant_rules=("Phase 8 conflict preservation for client-provided core inquiry facts",),
            expected_current_fields={
                "active_event_window": _schedule("2026-11-30T10:00:00Z", "2026-11-30T13:00:00Z"),
                "event_type": "networking social",
            },
            expected_absent_current_fields=(field_code,),
            expected_open_question_types=(expected_question_type, "requested_rental_scope"),
            forbidden_open_question_types=(),
            expected_draft=True,
            expected_material_blocker=True,
            notes="Conflicting client facts should not be merged into current truth.",
        ),
    )


def build_scenarios() -> tuple[CalibrationScenario, ...]:
    scenarios: list[CalibrationScenario] = [
        inquiry_scenario(
            "STGQ-001",
            "A",
            "Complete Studio Workshop Inquiry",
            description="Straightforward studio rental inquiry with all four core facts present.",
            schedule=_schedule("2026-11-12T10:00:00Z", "2026-11-12T14:00:00Z"),
            guest_count=18,
            scope="studio_space",
            event_type="workshop",
            expected_booking_fee_baseline="EUR 75 excl. VAT",
            expected_effective_booking_fee="EUR 75 excl. VAT",
        ),
        inquiry_scenario(
            "STGQ-002",
            "A",
            "Complete Entire Venue Social Inquiry",
            description="Straightforward entire-venue inquiry within a normal hosted-event shape.",
            schedule=_schedule("2026-11-15T17:00:00Z", "2026-11-15T21:00:00Z"),
            guest_count=48,
            scope="entire_venue",
            event_type="networking social",
            expected_booking_fee_baseline="EUR 250 excl. VAT",
            expected_effective_booking_fee="EUR 250 excl. VAT",
        ),
        inquiry_scenario(
            "STGQ-003",
            "A",
            "Complete Short Studio Meeting Inquiry",
            description="Short studio meeting used to exercise the lower studio booking-fee baseline.",
            schedule=_schedule("2026-11-14T10:00:00Z", "2026-11-14T12:00:00Z"),
            guest_count=12,
            scope="studio_space",
            event_type="meeting",
            expected_booking_fee_baseline="EUR 50 excl. VAT",
            expected_effective_booking_fee="EUR 50 excl. VAT",
        ),
        inquiry_scenario(
            "STGQ-004",
            "A",
            "Complete Supported Rental Inquiry With Facilitator Request",
            description="Straightforward inquiry with facilitator interest attached but no missing core facts.",
            schedule=_schedule("2026-11-18T09:00:00Z", "2026-11-18T15:00:00Z"),
            guest_count=22,
            scope="studio_space",
            event_type="team workshop",
            extras=(
                obs("facilitator_arrangement", "recommendation_requested", source_excerpt="Client asked if WNC can recommend a facilitator."),
            ),
            expected_booking_fee_baseline="EUR 75 excl. VAT",
            expected_effective_booking_fee="EUR 75 excl. VAT",
            notes="Current hosted workflow should not invent facilitator confirmation from historical or unguided context.",
        ),
        inquiry_scenario(
            "STGQ-005",
            "B",
            "Missing Guest Count",
            description="Client provided timing, scope, and event type but omitted guest count.",
            schedule=_schedule("2026-11-20T10:00:00Z", "2026-11-20T15:00:00Z"),
            scope="studio_space",
            event_type="brand workshop",
            expected_booking_fee_baseline="EUR 75 excl. VAT",
            expected_effective_booking_fee="EUR 75 excl. VAT",
        ),
        inquiry_scenario(
            "STGQ-006",
            "B",
            "Missing Timing",
            description="Client provided scope, guest count, and event type but not an exact date/time window.",
            guest_count=26,
            scope="entire_venue",
            event_type="panel event",
            expected_booking_fee_baseline=None,
            expected_effective_booking_fee=None,
        ),
        inquiry_scenario(
            "STGQ-007",
            "B",
            "Missing Scope",
            description="Client provided schedule, guest count, and event type but not the requested rental scope.",
            schedule=_schedule("2026-11-23T18:00:00Z", "2026-11-23T22:00:00Z"),
            guest_count=30,
            event_type="private dinner",
        ),
        inquiry_scenario(
            "STGQ-008",
            "B",
            "Multiple Core Facts Missing",
            description="Client provided only an event type; the workflow should preserve uncertainty and ask the four core questions it still needs.",
            event_type="community gathering",
        ),
        inquiry_scenario(
            "STGQ-009",
            "C",
            "Near Capacity Studio Inquiry",
            description="Guest count sits near a studio-style threshold but the current hosted projection still needs governed feasibility evaluation.",
            schedule=_schedule("2026-11-24T17:00:00Z", "2026-11-24T21:00:00Z"),
            guest_count=48,
            scope="studio_space",
            event_type="networking event",
            expected_material_blocker=True,
            expected_confirmation_required="Yes",
            expected_feasibility_as_requested="Requires confirmation",
            notes="Capacity should not be silently assumed safe at the threshold edge.",
        ),
        inquiry_scenario(
            "STGQ-010",
            "C",
            "Over Capacity Entire Venue Inquiry",
            description="High-guest-count case used to test that the workflow does not represent over-capacity as confirmed.",
            schedule=_schedule("2026-11-25T17:00:00Z", "2026-11-25T23:00:00Z"),
            guest_count=150,
            scope="entire_venue",
            event_type="launch party",
            expected_material_blocker=True,
            expected_confirmation_required="Yes",
            expected_feasibility_as_requested="Requires confirmation",
        ),
        inquiry_scenario(
            "STGQ-011",
            "C",
            "High Guest Count With Missing Scope",
            description="Capacity-relevant inquiry missing the exact rental scope; the system should ask for scope instead of assuming it.",
            schedule=_schedule("2026-11-26T17:00:00Z", "2026-11-26T22:00:00Z"),
            guest_count=95,
            event_type="awards reception",
            expected_material_blocker=True,
            expected_confirmation_required="Yes",
        ),
        inquiry_scenario(
            "STGQ-012",
            "D",
            "Studio Two Hour Fee Baseline",
            description="Commercial snapshot should show the correct lower studio booking-fee rule for a short booking.",
            schedule=_schedule("2026-11-28T09:00:00Z", "2026-11-28T11:00:00Z"),
            guest_count=10,
            scope="studio_space",
            event_type="recording session",
            expected_booking_fee_baseline="EUR 50 excl. VAT",
            expected_effective_booking_fee="EUR 50 excl. VAT",
        ),
        inquiry_scenario(
            "STGQ-013",
            "D",
            "Studio Four Hour Fee Baseline",
            description="Commercial snapshot should show the correct standard studio booking fee for a four-hour booking.",
            schedule=_schedule("2026-11-29T09:00:00Z", "2026-11-29T13:00:00Z"),
            guest_count=16,
            scope="studio_space",
            event_type="wellness workshop",
            expected_booking_fee_baseline="EUR 75 excl. VAT",
            expected_effective_booking_fee="EUR 75 excl. VAT",
        ),
        inquiry_scenario(
            "STGQ-014",
            "D",
            "Entire Venue Fee Baseline",
            description="Commercial snapshot should show the entire-venue baseline booking fee without needing a human override.",
            schedule=_schedule("2026-11-30T14:00:00Z", "2026-11-30T18:00:00Z"),
            guest_count=40,
            scope="entire_venue",
            event_type="showcase",
            expected_booking_fee_baseline="EUR 250 excl. VAT",
            expected_effective_booking_fee="EUR 250 excl. VAT",
        ),
        reschedule_scenario(
            "STGQ-015",
            title="Changed Schedule Creates Reschedule Request",
            initial_schedule=_schedule("2026-12-02T10:00:00Z", "2026-12-02T14:00:00Z"),
            changed_schedule=_schedule("2026-12-03T10:00:00Z", "2026-12-03T14:00:00Z"),
        ),
        reschedule_scenario(
            "STGQ-016",
            title="Same Schedule Reconfirmation Is A No-Op",
            initial_schedule=_schedule("2026-12-04T12:00:00Z", "2026-12-04T16:00:00Z"),
            changed_schedule=_schedule("2026-12-04T12:00:00Z", "2026-12-04T16:00:00Z"),
            same_schedule_confirmation=True,
        ),
        CalibrationScenario(
            scenario_id="STGQ-017",
            category_code="E",
            title="Conflicting Schedule Candidates",
            description="Two different requested time windows arrive before a current schedule is established.",
            display_name="STGQ-017 Conflicting Schedule Candidates",
            client_label="STGQ-017 Synthetic Client",
            contact_email="stgq-017@example.test",
            event_reference="STGQ-017 synthetic reference",
            stages=(
                stage("bootstrap_open_questions"),
                stage(
                    "client_answers",
                    obs("event_type", "networking social"),
                    obs("guest_count", 28),
                    obs("requested_rental_scope", "entire_venue"),
                    obs("active_event_window", _schedule("2026-12-05T15:00:00Z", "2026-12-05T19:00:00Z")),
                    obs("active_event_window", _schedule("2026-12-06T15:00:00Z", "2026-12-06T19:00:00Z")),
                    run_waiting=True,
                    generate_draft=True,
                ),
            ),
            expectations=ScenarioExpectations(
                relevant_rules=("Phase 8 schedule conflict handling",),
                expected_current_fields={
                    "guest_count": 28,
                    "requested_rental_scope": "entire_venue",
                    "event_type": "networking social",
                },
                expected_absent_current_fields=("active_event_window",),
                expected_open_question_types=("requested_event_timing",),
                expected_draft=True,
                expected_draft_question_types=("requested_event_timing",),
                expected_material_blocker=True,
                notes="Conflicting timing candidates should not become current truth.",
            ),
        ),
        inquiry_scenario(
            "STGQ-018",
            "F",
            "External Caterer Inquiry",
            description="Catering arrangement is provided, but the current hosted path should not invent supplier approval beyond current governed truth.",
            schedule=_schedule("2026-12-07T16:00:00Z", "2026-12-07T21:00:00Z"),
            guest_count=24,
            scope="studio_space",
            event_type="private dinner",
            extras=(
                obs("catering_arrangement", "client_external_caterer", source_excerpt="Client says they want to bring an outside caterer."),
            ),
            expected_booking_fee_baseline="EUR 75 excl. VAT",
            expected_effective_booking_fee="EUR 75 excl. VAT",
        ),
        inquiry_scenario(
            "STGQ-019",
            "F",
            "Supplier Details Evidence Present",
            description="Supplier details evidence should be retained without becoming an unsupported operational confirmation.",
            schedule=_schedule("2026-12-08T08:00:00Z", "2026-12-08T12:00:00Z"),
            guest_count=20,
            scope="studio_space",
            event_type="photo shoot",
            extras=(
                obs(
                    "supplier_details",
                    {"supplier_name": "External Coffee Cart", "access_needs": "load-in from courtyard"},
                    observation_type=OBS_REQUIREMENT,
                    claim_kind=CLAIM_REQUIREMENT,
                    source_excerpt="Supplier asked whether a coffee cart can load in at 08:00.",
                ),
            ),
            expected_booking_fee_baseline="EUR 75 excl. VAT",
            expected_effective_booking_fee="EUR 75 excl. VAT",
        ),
        inquiry_scenario(
            "STGQ-020",
            "G",
            "Microphone Requirement",
            description="Technical requirement should not be upgraded into a confirmed capability without explicit governed support.",
            schedule=_schedule("2026-12-09T12:00:00Z", "2026-12-09T18:00:00Z"),
            guest_count=28,
            scope="studio_space",
            event_type="panel talk",
            extras=(
                obs("technical_requirements", ["microphones"], source_excerpt="Client asked for handheld mics."),  # enum-array
            ),
            expected_booking_fee_baseline="EUR 75 excl. VAT",
            expected_effective_booking_fee="EUR 75 excl. VAT",
            expected_material_blocker=True,
            expected_confirmation_required="Yes",
        ),
        inquiry_scenario(
            "STGQ-021",
            "G",
            "DJ Booth And Power Request",
            description="Potentially sensitive technical capability request that should remain cautious without explicit support.",
            schedule=_schedule("2026-12-10T18:00:00Z", "2026-12-11T00:00:00Z"),
            guest_count=36,
            scope="entire_venue",
            event_type="dj set",
            extras=(
                obs("technical_requirements", ["dj_sound_booth", "power_requirements"], source_excerpt="Client wants a DJ booth and extra power."),  # enum-array
            ),
            expected_material_blocker=True,
            expected_confirmation_required="Yes",
        ),
        inquiry_scenario(
            "STGQ-022",
            "H",
            "WNC Facilitator Request",
            description="Facilitator sourcing request should not be represented as confirmed availability without governed confirmation.",
            schedule=_schedule("2026-12-11T09:00:00Z", "2026-12-11T15:00:00Z"),
            guest_count=20,
            scope="studio_space",
            event_type="team offsite",
            extras=(
                obs("facilitator_arrangement", "wnc_provided", source_excerpt="Client asked whether WNC can provide a facilitator."),
            ),
            expected_booking_fee_baseline="EUR 75 excl. VAT",
            expected_effective_booking_fee="EUR 75 excl. VAT",
            expected_material_blocker=True,
            expected_confirmation_required="Yes",
        ),
        inquiry_scenario(
            "STGQ-023",
            "H",
            "Custom Experience Design Request",
            description="Non-catalogued service request should remain cautious rather than converting historical capability into a current promise.",
            schedule=_schedule("2026-12-12T09:00:00Z", "2026-12-12T17:00:00Z"),
            guest_count=18,
            scope="studio_space",
            event_type="immersive session",
            extras=(
                obs("facilitator_arrangement", "custom_experience_design", source_excerpt="Client wants a custom facilitation concept."),
            ),
            expected_booking_fee_baseline="EUR 75 excl. VAT",
            expected_effective_booking_fee="EUR 75 excl. VAT",
            expected_material_blocker=True,
            expected_confirmation_required="Yes",
        ),
        CalibrationScenario(
            scenario_id="STGQ-024",
            category_code="I",
            title="Pending Fee Waiver Must Not Activate",
            description="Case-decision candidate exists, but authority should remain pending until approved.",
            display_name="STGQ-024 Pending Fee Waiver Must Not Activate",
            client_label="STGQ-024 Synthetic Client",
            contact_email="stgq-024@example.test",
            event_reference="STGQ-024 synthetic reference",
            stages=(
                stage("bootstrap_open_questions"),
                stage(
                    "establish_current",
                    obs("active_event_window", _schedule("2026-12-13T10:00:00Z", "2026-12-13T12:00:00Z")),
                    obs("guest_count", 12),
                    obs("requested_rental_scope", "studio_space"),
                    obs("event_type", "meeting"),
                ),
                stage(
                    "propose_exception",
                    obs(
                        "booking_fee_override",
                        {"booking_fee": 0, "currency": "EUR", "reason": "Synthetic nonprofit waiver request"},
                        observation_type=OBS_DECISION,
                        claim_kind=CLAIM_EXCEPTION,
                        source_excerpt="Client asked whether the booking fee can be waived.",
                    ),
                ),
            ),
            expectations=ScenarioExpectations(
                relevant_rules=("Phase 4 booking-fee baseline", "Phase 8 approval-gated case decision activation"),
                expected_current_fields={
                    "active_event_window": _schedule("2026-12-13T10:00:00Z", "2026-12-13T12:00:00Z"),
                    "guest_count": 12,
                    "requested_rental_scope": "studio_space",
                    "event_type": "meeting",
                },
                expected_booking_fee_baseline="EUR 50 excl. VAT",
                expected_effective_booking_fee="EUR 50 excl. VAT",
                expected_case_decision_status="proposed",
                must_not_activate_exception=True,
                notes="Pending commercial exceptions must not silently become effective current truth.",
            ),
        ),
        CalibrationScenario(
            scenario_id="STGQ-025",
            category_code="I",
            title="Pending Entire Venue Waiver Must Not Activate",
            description="Authority handling on a higher-value entire-venue fee exception request.",
            display_name="STGQ-025 Pending Entire Venue Waiver Must Not Activate",
            client_label="STGQ-025 Synthetic Client",
            contact_email="stgq-025@example.test",
            event_reference="STGQ-025 synthetic reference",
            stages=(
                stage("bootstrap_open_questions"),
                stage(
                    "establish_current",
                    obs("active_event_window", _schedule("2026-12-14T16:00:00Z", "2026-12-14T21:00:00Z")),
                    obs("guest_count", 42),
                    obs("requested_rental_scope", "entire_venue"),
                    obs("event_type", "brand launch"),
                ),
                stage(
                    "propose_exception",
                    obs(
                        "booking_fee_override",
                        {"booking_fee": 0, "currency": "EUR", "reason": "High-value client asked for a waiver"},
                        observation_type=OBS_DECISION,
                        claim_kind=CLAIM_EXCEPTION,
                        source_excerpt="Client says the booking will be large if the fee is waived.",
                    ),
                ),
            ),
            expectations=ScenarioExpectations(
                relevant_rules=("Phase 4 booking-fee baseline", "Approval-gated authority handling under commercial pressure"),
                expected_current_fields={
                    "active_event_window": _schedule("2026-12-14T16:00:00Z", "2026-12-14T21:00:00Z"),
                    "guest_count": 42,
                    "requested_rental_scope": "entire_venue",
                    "event_type": "brand launch",
                },
                expected_effective_fee_matches_baseline=True,
                expected_case_decision_status="proposed",
                must_not_activate_exception=True,
                notes="Commercial attractiveness must not relax current policy.",
            ),
        ),
        conflicting_observation_scenario(
            "STGQ-026",
            "Conflicting Guest Counts",
            field_code="guest_count",
            first_value=20,
            second_value=45,
            expected_question_type="expected_guest_count",
            description="First client message says 20 guests; the later one says 45.",
        ),
        conflicting_observation_scenario(
            "STGQ-027",
            "Conflicting Requested Scope",
            field_code="requested_rental_scope",
            first_value="studio_space",
            second_value="entire_venue",
            expected_question_type="requested_rental_scope",
            description="Client changed the requested rental scope between messages.",
        ),
        inquiry_scenario(
            "STGQ-028",
            "K",
            "Unusual Ambiguous Event Shape",
            description="Rental-shaped request that does not neatly fit a standard category and still needs clarification.",
            schedule=_schedule("2026-12-16T10:00:00Z", "2026-12-16T18:00:00Z"),
            guest_count=14,
            scope="custom_scope",
            event_type="healing installation with silent performance",
            expected_material_blocker=True,
            expected_confirmation_required="Yes",
        ),
        CalibrationScenario(
            scenario_id="STGQ-029",
            category_code="L",
            title="Commercial Pressure Fee Waiver",
            description="High-value opportunity should not auto-waive commercial rules.",
            display_name="STGQ-029 Commercial Pressure Fee Waiver",
            client_label="STGQ-029 Synthetic Client",
            contact_email="stgq-029@example.test",
            event_reference="STGQ-029 synthetic reference",
            stages=(
                stage("bootstrap_open_questions"),
                stage(
                    "establish_current",
                    obs("active_event_window", _schedule("2026-12-17T17:00:00Z", "2026-12-17T23:00:00Z")),
                    obs("guest_count", 55),
                    obs("requested_rental_scope", "entire_venue"),
                    obs("event_type", "vip reception"),
                ),
                stage(
                    "pressure_request",
                    obs(
                        "booking_fee_override",
                        {"booking_fee": 0, "currency": "EUR", "reason": "Client says they will book immediately if fee is waived"},
                        observation_type=OBS_DECISION,
                        claim_kind=CLAIM_EXCEPTION,
                        source_excerpt="Client asked for a waiver because the event is strategically important.",
                    ),
                ),
            ),
            expectations=ScenarioExpectations(
                relevant_rules=("Commercial exceptions require approval",),
                expected_current_fields={
                    "active_event_window": _schedule("2026-12-17T17:00:00Z", "2026-12-17T23:00:00Z"),
                    "guest_count": 55,
                    "requested_rental_scope": "entire_venue",
                    "event_type": "vip reception",
                },
                expected_effective_fee_matches_baseline=True,
                expected_case_decision_status="proposed",
                must_not_activate_exception=True,
            ),
        ),
        CalibrationScenario(
            scenario_id="STGQ-030",
            category_code="M",
            title="Historical Temptation Commercial Note",
            description="Synthetic source excerpt mentions an old waived-fee story; current hosted output must not adopt it as current policy.",
            display_name="STGQ-030 Historical Temptation Commercial Note",
            client_label="STGQ-030 Synthetic Client",
            contact_email="stgq-030@example.test",
            event_reference="STGQ-030 synthetic reference",
            stages=(
                stage("bootstrap_open_questions"),
                stage(
                    "establish_current",
                    obs("active_event_window", _schedule("2026-12-18T10:00:00Z", "2026-12-18T13:00:00Z")),
                    obs("guest_count", 18),
                    obs("requested_rental_scope", "studio_space"),
                    obs("event_type", "community workshop"),
                    obs(
                        "booking_fee_override",
                        {"booking_fee": 0, "currency": "EUR", "reason": "Synthetic note references a previous waived fee"},
                        observation_type=OBS_DECISION,
                        claim_kind=CLAIM_EXCEPTION,
                        source_excerpt="Operator note: a previous event once got the fee waived, but this is not current authority.",
                    ),
                ),
            ),
            expectations=ScenarioExpectations(
                relevant_rules=("Current authority must outrank historical precedent cues",),
                expected_current_fields={
                    "active_event_window": _schedule("2026-12-18T10:00:00Z", "2026-12-18T13:00:00Z"),
                    "guest_count": 18,
                    "requested_rental_scope": "studio_space",
                    "event_type": "community workshop",
                },
                expected_effective_fee_matches_baseline=True,
                expected_case_decision_status="proposed",
                must_not_activate_exception=True,
                notes="This is a hosted-surface approximation of historical-precedent temptation rather than a full Phase 6 answer test.",
            ),
            phase6_relevant=True,
        ),
        inquiry_scenario(
            "STGQ-031",
            "N",
            "Synthetic PI Safety Follow-Up Draft",
            description="Client information request should not leak synthetic source-excerpt contact details back into the draft.",
            schedule=None,
            guest_count=None,
            scope="studio_space",
            event_type="private dinner",
            extras=(
                obs(
                    "layout_requirements",
                    {"notes": "Contact Ava Hart at 06-11111111 and ava.synthetic@example.test for backstage access."},
                    source_excerpt="Synthetic note with fake direct contact details that should stay internal.",
                ),
            ),
            forbidden_draft_fragments=("Ava Hart", "06-11111111", "ava.synthetic@example.test"),
        ),
        inquiry_scenario(
            "STGQ-032",
            "O",
            "Insufficient Knowledge Custom Technical Ask",
            description="Custom technical ask should remain confirmation-bound rather than confidently supported.",
            schedule=_schedule("2026-12-20T18:00:00Z", "2026-12-20T23:00:00Z"),
            guest_count=30,
            scope="entire_venue",
            event_type="immersive performance",
            extras=(
                obs("technical_requirements", ["other_technical"], source_excerpt="Client wants a custom suspended projection rig."),
            ),
            expected_material_blocker=True,
            expected_confirmation_required="Yes",
        ),
    ]

    return tuple(scenarios)


def load_auth_values(auth_file: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in auth_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def build_client(auth_file: Path, *, timeout_seconds: float) -> OperatorHarnessClient:
    values = load_auth_values(auth_file)
    return OperatorHarnessClient(
        OperatorHarnessConfig(
            base_url=values["WNC_OPERATOR_BASE_URL"],
            username=values.get("STAGING_BASIC_AUTH_USERNAME"),
            password=values.get("STAGING_BASIC_AUTH_PASSWORD"),
            timeout_seconds=timeout_seconds,
        )
    )


def _first_thread_with_generation(case_payload: dict[str, Any]) -> dict[str, Any] | None:
    for thread in case_payload["case"].get("simulated_outlook_threads", []):
        if thread.get("can_generate"):
            return thread
    return None


def _fact_map(orchestration_snapshot: dict[str, Any]) -> dict[str, Any]:
    facts: dict[str, Any] = {}
    for row in orchestration_snapshot.get("rental_case_facts", []):
        field_code = row.get("field_code")
        if field_code:
            facts[str(field_code)] = row.get("value_payload")
    return facts


def _current_event_window(rental_case: dict[str, Any]) -> dict[str, str] | None:
    start = rental_case.get("active_event_start")
    end = rental_case.get("active_event_end")
    if start and end:
        return {
            "active_event_start": _normalize_timestamp_text(str(start)),
            "active_event_end": _normalize_timestamp_text(str(end)),
        }
    return None


def _normalize_timestamp_text(value: str) -> str:
    normalized = value.replace(" ", "T")
    if normalized.endswith("+00:00"):
        return normalized[:-6] + "Z"
    if normalized.endswith("+00"):
        return normalized[:-3] + "Z"
    return normalized


def _projection_map(items: list[dict[str, Any]]) -> dict[str, str]:
    return {
        str(item.get("label")): str(item.get("value"))
        for item in items
        if item.get("label") is not None
    }


def extract_actual_snapshot(case_payload: dict[str, Any]) -> ActualSnapshot:
    case = case_payload["case"]
    orchestration = case["orchestration_snapshot"]
    rental_case = orchestration["rental_case"]
    facts = _fact_map(orchestration)

    active_questions = [
        question
        for question in orchestration.get("open_questions", [])
        if question.get("status") in {"open", "answered_pending_validation"}
    ]
    open_question_types = tuple(str(question["question_type"]) for question in active_questions)
    open_question_texts = tuple(str(question["human_question_text"]) for question in active_questions)
    open_blockers = [
        blocker for blocker in orchestration.get("blockers", []) if blocker.get("status") == "open"
    ]
    reasoning_projections = orchestration.get("reasoning_projections", [])
    active_actions = [
        action
        for action in orchestration.get("workflow_actions", [])
        if action.get("status") not in {"cancelled", "superseded"}
    ]
    active_reschedules = [
        request
        for request in orchestration.get("reschedule_requests", [])
        if request.get("status") not in {"cancelled", "superseded", "closed"}
    ]
    active_changes = [
        change
        for change in orchestration.get("proposed_changes", [])
        if change.get("status") not in {"cancelled", "superseded", "closed"}
    ]
    decisions = orchestration.get("case_decisions", [])
    commercial = _projection_map(case["working_proposal"].get("commercial_snapshot", []))
    feasibility = _projection_map(case["working_proposal"].get("feasibility_snapshot", []))

    draft: DraftSummary | None = None
    for thread in case.get("simulated_outlook_threads", []):
        current = thread.get("current_revision")
        if current is None:
            continue
        draft = DraftSummary(
            subject=current.get("subject"),
            body_text=current.get("body_text"),
            question_types=tuple(
                str(item.get("question_type"))
                for item in current.get("question_lines", [])
                if item.get("question_type")
            ),
            question_prompts=tuple(
                str(item.get("prompt_text"))
                for item in current.get("question_lines", [])
                if item.get("prompt_text")
            ),
        )
        break

    return ActualSnapshot(
        rental_case_id=int(rental_case["rental_case_id"]),
        case_reference_code=str(rental_case["case_reference_code"]),
        case_revision=int(rental_case["case_revision"]),
        rental_type_code=rental_case.get("rental_type_code"),
        active_event_window=_current_event_window(rental_case),
        current_facts=facts,
        active_open_question_types=open_question_types,
        active_open_question_texts=open_question_texts,
        open_blocker_count=len(open_blockers),
        open_blocker_types=tuple(
            str(blocker.get("blocker_type"))
            for blocker in open_blockers
            if blocker.get("blocker_type")
        ),
        open_blocker_rule_codes=tuple(
            str(blocker.get("rule_code"))
            for blocker in open_blockers
            if blocker.get("rule_code")
        ),
        active_workflow_action_types=tuple(str(action["action_type"]) for action in active_actions),
        active_workflow_action_statuses=tuple(str(action["status"]) for action in active_actions),
        proposed_change_count=len(active_changes),
        reschedule_request_count=len(active_reschedules),
        case_decision_statuses=tuple(str(decision.get("status")) for decision in decisions),
        reasoning_projection_semantic_states=tuple(
            str(summary.get("semantic_state_code"))
            for projection in reasoning_projections
            if isinstance((summary := projection.get("degraded_retrieval_summary")), dict)
            and summary.get("semantic_state_code")
        ),
        commercial_snapshot=commercial,
        feasibility_snapshot=feasibility,
        missing_client_information=tuple(
            str(item.get("label"))
            for item in case["working_proposal"].get("missing_client_information", [])
            if item.get("label")
        ),
        next_action_labels=tuple(
            str(item.get("label"))
            for item in case["working_proposal"].get("next_actions", [])
            if item.get("label")
        ),
        draft=draft,
    )


def _field_value(actual: ActualSnapshot, field_code: str) -> Any:
    if field_code == "active_event_window":
        return actual.active_event_window
    if field_code == "requested_rental_scope":
        return actual.rental_type_code if actual.rental_type_code in SPECIFIC_SCOPE_CODES else None
    return actual.current_facts.get(field_code)


def evaluate_case(scenario: CalibrationScenario, actual: ActualSnapshot) -> ScoredCase:
    failures: list[str] = []
    critical_failures: list[str] = []
    unsupported_claim_count = 0
    factual_correction_count = 0
    expected = scenario.expectations

    for field_code, expected_value in expected.expected_current_fields.items():
        actual_value = _field_value(actual, field_code)
        if actual_value != expected_value:
            failures.append(f"current_field_mismatch:{field_code}")
            factual_correction_count += 1

    for field_code in expected.expected_absent_current_fields:
        if _field_value(actual, field_code) is not None:
            failures.append(f"unexpected_current_field:{field_code}")
            unsupported_claim_count += 1
            if field_code in {"guest_count", "requested_rental_scope", "active_event_window", "event_type"}:
                critical_failures.append(f"invented_current_truth:{field_code}")

    actual_q_set = set(actual.active_open_question_types)
    expected_q_set = set(expected.expected_open_question_types)
    missing_questions = sorted(expected_q_set - actual_q_set)
    extra_questions = sorted(actual_q_set - expected_q_set)
    if missing_questions:
        failures.extend(f"missing_open_question:{item}" for item in missing_questions)
        if expected_q_set:
            critical_failures.append("material_missing_information_not_surfaced")
    for item in expected.forbidden_open_question_types:
        if item in actual_q_set:
            failures.append(f"forbidden_open_question:{item}")
            unsupported_claim_count += 1

    if expected.expected_proposed_change_count is not None and actual.proposed_change_count != expected.expected_proposed_change_count:
        failures.append("proposed_change_count_mismatch")
        factual_correction_count += 1

    if expected.expected_reschedule_request_count is not None and actual.reschedule_request_count != expected.expected_reschedule_request_count:
        failures.append("reschedule_request_count_mismatch")
        factual_correction_count += 1
        if expected.must_not_create_reschedule_for_same_schedule and actual.reschedule_request_count > 0:
            critical_failures.append("same_schedule_reconfirmation_created_reschedule")

    if expected.expected_booking_fee_baseline is not None:
        actual_baseline = actual.commercial_snapshot.get("Booking fee baseline")
        if actual_baseline != expected.expected_booking_fee_baseline:
            failures.append("booking_fee_baseline_mismatch")
            factual_correction_count += 1
            critical_failures.append("wrong_price_or_fee")

    if expected.expected_effective_booking_fee is not None:
        actual_effective = actual.commercial_snapshot.get("Effective booking fee")
        if actual_effective != expected.expected_effective_booking_fee:
            failures.append("effective_booking_fee_mismatch")
            factual_correction_count += 1
            critical_failures.append("unsupported_commercial_commitment")
    elif expected.expected_effective_fee_matches_baseline:
        actual_effective = actual.commercial_snapshot.get("Effective booking fee")
        actual_baseline = actual.commercial_snapshot.get("Booking fee baseline")
        if actual_effective != actual_baseline:
            failures.append("effective_fee_diverged_from_baseline")
            factual_correction_count += 1
            critical_failures.append("unsupported_commercial_commitment")

    if expected.expected_case_decision_status is not None:
        if expected.expected_case_decision_status not in actual.case_decision_statuses:
            failures.append("case_decision_status_mismatch")
            factual_correction_count += 1

    if expected.must_not_activate_exception:
        if "active" in actual.case_decision_statuses:
            failures.append("exception_unexpectedly_active")
            critical_failures.append("unsupported_fee_waiver")

    if expected.expected_confirmation_required is not None:
        actual_confirmation = actual.feasibility_snapshot.get("Confirmation still required")
        if actual_confirmation != expected.expected_confirmation_required:
            failures.append("confirmation_requirement_mismatch")

    if expected.expected_feasibility_as_requested is not None:
        actual_feasibility = actual.feasibility_snapshot.get("Feasibility as requested")
        if actual_feasibility != expected.expected_feasibility_as_requested:
            failures.append("feasibility_snapshot_mismatch")

    if expected.expected_material_blocker and actual.open_blocker_count == 0:
        failures.append("missing_material_blocker")
        critical_failures.append("failure_to_surface_material_blocker")

    if expected.expected_draft:
        if actual.draft is None:
            failures.append("missing_draft")
        else:
            draft_q_set = set(actual.draft.question_types)
            expected_draft_q_set = set(expected.expected_draft_question_types)
            if draft_q_set != expected_draft_q_set:
                failures.append("draft_question_set_mismatch")
            for fragment in expected.forbidden_draft_fragments:
                if fragment and actual.draft.body_text and fragment in actual.draft.body_text:
                    failures.append("draft_confidentiality_leak")
                    critical_failures.append("confidentiality_or_pi_leakage")
    else:
        if actual.draft is not None and not expected.expected_open_question_types:
            failures.append("unexpected_draft_present")

    confidentiality_success = "confidentiality_or_pi_leakage" not in critical_failures
    authority_success = not any(
        code in critical_failures
        for code in {
            "unsupported_fee_waiver",
            "wrong_price_or_fee",
            "unsupported_commercial_commitment",
        }
    )
    missing_info_success = set(expected.expected_open_question_types) == set(actual.active_open_question_types)

    completeness_ratio = _ratio(
        numerator=len(expected.expected_current_fields) - sum(1 for item in failures if item.startswith("current_field_mismatch:")),
        denominator=len(expected.expected_current_fields) or 1,
    )
    missing_ratio = 1.0 if not expected_q_set else _ratio(len(expected_q_set & actual_q_set), len(expected_q_set))

    scores = {
        "factual_correctness": _score_0_4(max(0.0, 1.0 - (factual_correction_count / max(1, len(expected.expected_current_fields) + 1)))),
        "unsupported_assertion_avoidance": 4.0 if unsupported_claim_count == 0 else max(0.0, 4.0 - (unsupported_claim_count * 2.0)),
        "missing_information_detection": _score_0_4(missing_ratio),
        "authority_handling": 4.0 if authority_success else 0.0,
        "completeness": _score_0_4(completeness_ratio),
        "appropriate_restraint": 4.0 if not any(item.startswith("unexpected_current_field:") for item in failures) else 1.0,
        "operational_usefulness": _score_operational_usefulness(expected, actual, failures),
        "communication_quality": _score_communication_quality(expected, actual),
        "concision": _score_concision(actual),
        "correct_next_action": 4.0 if _correct_next_action(expected, actual) else 0.0,
    }

    edit_burden = classify_edit_burden(scores=scores, critical_failures=critical_failures)
    diagnosed_layer, root_cause = diagnose_failure(scenario, failures, critical_failures)

    return ScoredCase(
        scenario_id=scenario.scenario_id,
        category_code=scenario.category_code,
        rental_case_id=actual.rental_case_id,
        case_reference_code=actual.case_reference_code,
        scores=scores,
        edit_burden=edit_burden,
        critical_failures=tuple(sorted(set(critical_failures))),
        unsupported_claim_count=unsupported_claim_count,
        factual_correction_count=factual_correction_count,
        missing_info_success=missing_info_success,
        authority_success=authority_success,
        confidentiality_success=confidentiality_success,
        correct_next_action=_correct_next_action(expected, actual),
        failures=tuple(failures),
        diagnosed_layer=diagnosed_layer,
        root_cause=root_cause,
        actual=asdict(actual),
    )


def _ratio(numerator: int | float, denominator: int | float) -> float:
    if denominator == 0:
        return 1.0
    return float(numerator) / float(denominator)


def _score_0_4(ratio: float) -> float:
    bounded = max(0.0, min(1.0, ratio))
    return round(bounded * 4.0, 2)


def _score_operational_usefulness(
    expected: ScenarioExpectations,
    actual: ActualSnapshot,
    failures: list[str],
) -> float:
    if expected.expected_draft:
        if actual.draft is None:
            return 0.0
        return 4.0 if "draft_question_set_mismatch" not in failures else 2.0
    if expected.expected_open_question_types:
        return 2.0 if actual.open_blocker_count > 0 else 0.0
    if actual.open_blocker_count == 0 and "REQUEST_CLIENT_INFORMATION" not in actual.active_workflow_action_types:
        return 4.0
    return 2.0


def _score_communication_quality(expected: ScenarioExpectations, actual: ActualSnapshot) -> float:
    if not expected.expected_draft:
        return 3.0
    if actual.draft is None or not actual.draft.body_text:
        return 0.0
    score = 3.5
    if len(actual.draft.body_text) > 900:
        score -= 0.5
    if any("question_type" in prompt.lower() for prompt in actual.draft.question_prompts):
        score -= 1.0
    return max(0.0, round(score, 2))


def _score_concision(actual: ActualSnapshot) -> float:
    if actual.draft is None or not actual.draft.body_text:
        return 3.0
    if len(actual.draft.body_text) <= 500:
        return 4.0
    if len(actual.draft.body_text) <= 900:
        return 3.0
    return 2.0


def _correct_next_action(expected: ScenarioExpectations, actual: ActualSnapshot) -> bool:
    if expected.expected_draft:
        return actual.draft is not None
    if expected.expected_open_question_types:
        return actual.open_blocker_count > 0 or "REQUEST_CLIENT_INFORMATION" in actual.active_workflow_action_types
    return actual.open_blocker_count == 0 and "REQUEST_CLIENT_INFORMATION" not in actual.active_workflow_action_types


def classify_edit_burden(*, scores: dict[str, float], critical_failures: list[str]) -> str:
    if critical_failures:
        return "D"
    average_score = mean(scores.values())
    if average_score >= 3.5:
        return "A"
    if average_score >= 3.0 and scores["factual_correctness"] >= 3.0:
        return "B"
    if average_score >= 2.0:
        return "C"
    return "D"


def diagnose_failure(
    scenario: CalibrationScenario,
    failures: list[str],
    critical_failures: list[str],
) -> tuple[str, str]:
    if not failures and not critical_failures:
        return "none", "no substantive failure observed"
    if any(code in critical_failures for code in {"unsupported_fee_waiver", "wrong_price_or_fee", "unsupported_commercial_commitment"}):
        return "phase7_context_or_authority", "authority failure"
    if any(item.startswith("missing_open_question:") or item == "missing_material_blocker" for item in failures):
        if scenario.category_code in {"B", "C", "K", "O"}:
            return "phase8_workflow_consumption", "missing-information detection failure"
        return "phase8_workflow_consumption", "workflow consumption failure"
    if any(item.startswith("unexpected_current_field:") for item in failures):
        return "phase8_workflow_consumption", "unsupported assertion / current-truth promotion failure"
    if any(item == "draft_confidentiality_leak" for item in failures):
        return "phase7_generation_or_phase8_drafting", "confidentiality failure"
    if scenario.category_code in {"C", "G", "H", "M", "O"}:
        return "knowledge_or_surface_gap", "insufficient current governed surface"
    return "phase8_workflow_consumption", "workflow consumption failure"


def run_scenario(
    client: OperatorHarnessClient,
    scenario: CalibrationScenario,
    *,
    run_slug: str,
) -> tuple[ActualSnapshot, list[dict[str, Any]]]:
    logs: list[dict[str, Any]] = []
    created = client.create_case(
        label=f"{scenario.display_name} {run_slug}",
        client_label=scenario.client_label,
        contact_email=scenario.contact_email,
        event_reference=scenario.event_reference,
    )
    case_id = int(created["created_case"]["rental_case_id"])
    logs.append({"step": "create_case", "case_id": case_id})

    for stage_index, stage_spec in enumerate(scenario.stages, start=1):
        for obs_index, observation in enumerate(stage_spec.observations, start=1):
            response = client.inject_structured_observation(
                rental_case_id=case_id,
                field_code=observation.field_code,
                observation_type=observation.observation_type,
                claim_kind=observation.claim_kind,
                value_text=_json_value(observation.value),
                source_excerpt=observation.source_excerpt,
                sender_reference="calibration:operator",
                external_test_reference=f"{scenario.scenario_id}:{run_slug}:{case_id}:{stage_index}:{obs_index}",
            )
            logs.append(
                {
                    "step": "inject_structured_observation",
                    "stage": stage_spec.name,
                    "field_code": observation.field_code,
                    "ok": response.get("ok"),
                    "report": response.get("report", {}),
                }
            )
            if not response.get("ok"):
                failure_codes = tuple(response.get("report", {}).get("failure_codes", ()))
                if "source_duplicate" not in failure_codes:
                    continue
                raise RuntimeError(
                    f"Structured observation injection failed for {scenario.scenario_id} "
                    f"stage={stage_spec.name} field={observation.field_code}: {failure_codes}"
                )
        response = client.run_inquiry_intake(rental_case_id=case_id)
        logs.append({"step": "run_inquiry_intake", "stage": stage_spec.name, "ok": response.get("ok"), "report": response.get("report", {})})
        if not response.get("ok"):
            failure_codes = response.get("report", {}).get("failure_codes", [])
            raise RuntimeError(
                f"Inquiry intake failed for {scenario.scenario_id} stage={stage_spec.name}: {failure_codes}"
            )
        response = client.run_reconciliation(rental_case_id=case_id)
        logs.append({"step": "run_reconciliation", "stage": stage_spec.name, "ok": response.get("ok"), "report": response.get("report", {})})
        if not response.get("ok"):
            failure_codes = response.get("report", {}).get("failure_codes", [])
            raise RuntimeError(
                f"Reconciliation failed for {scenario.scenario_id} stage={stage_spec.name}: {failure_codes}"
            )
        if stage_spec.run_waiting:
            response = client.run_inquiry_waiting(rental_case_id=case_id)
            logs.append({"step": "run_inquiry_waiting", "stage": stage_spec.name, "ok": response.get("ok"), "report": response.get("report", {})})
            if not response.get("ok"):
                failure_codes = response.get("report", {}).get("failure_codes", [])
                raise RuntimeError(
                    f"Inquiry waiting failed for {scenario.scenario_id} stage={stage_spec.name}: {failure_codes}"
                )
            response = client.run_reconciliation(rental_case_id=case_id)
            logs.append({"step": "run_reconciliation_post_waiting", "stage": stage_spec.name, "ok": response.get("ok"), "report": response.get("report", {})})
            if not response.get("ok"):
                failure_codes = response.get("report", {}).get("failure_codes", [])
                raise RuntimeError(
                    f"Post-waiting reconciliation failed for {scenario.scenario_id} stage={stage_spec.name}: {failure_codes}"
                )

    case_payload = client.get_case(rental_case_id=case_id)
    thread = _first_thread_with_generation(case_payload)
    wants_draft = any(stage_spec.generate_draft for stage_spec in scenario.stages)
    if wants_draft and thread is not None:
        response = client.generate_draft(
            rental_case_id=case_id,
            workflow_action_id=int(thread["workflow_action_id"]),
        )
        logs.append({"step": "generate_draft", "ok": response.get("ok"), "report": response.get("report", {})})
        if not response.get("ok"):
            failure_codes = response.get("report", {}).get("failure_codes", [])
            raise RuntimeError(f"Draft generation failed for {scenario.scenario_id}: {failure_codes}")
        case_payload = client.get_case(rental_case_id=case_id)
    return extract_actual_snapshot(case_payload), logs


def summarize_results(results: list[ScoredCase]) -> dict[str, Any]:
    rubric_names = tuple(results[0].scores.keys()) if results else ()
    edit_counts = {code: 0 for code in ("A", "B", "C", "D")}
    for result in results:
        edit_counts[result.edit_burden] += 1

    critical_total = sum(len(result.critical_failures) for result in results)
    factual_corrections = sum(result.factual_correction_count for result in results)
    unsupported_claims = sum(result.unsupported_claim_count for result in results)

    category_breakdown: dict[str, dict[str, Any]] = {}
    for category_code, label in CATEGORY_LABELS.items():
        cases = [result for result in results if result.category_code == category_code]
        if not cases:
            continue
        category_breakdown[category_code] = {
            "label": label,
            "count": len(cases),
            "A": sum(1 for case in cases if case.edit_burden == "A"),
            "B": sum(1 for case in cases if case.edit_burden == "B"),
            "C": sum(1 for case in cases if case.edit_burden == "C"),
            "D": sum(1 for case in cases if case.edit_burden == "D"),
            "critical_failures": sum(len(case.critical_failures) for case in cases),
            "authority_success_rate": round(_ratio(sum(1 for case in cases if case.authority_success), len(cases)), 4),
            "missing_information_detection_rate": round(_ratio(sum(1 for case in cases if case.missing_info_success), len(cases)), 4),
            "correct_next_action_rate": round(_ratio(sum(1 for case in cases if case.correct_next_action), len(cases)), 4),
            "mean_scores": {
                name: round(mean(case.scores[name] for case in cases), 2)
                for name in rubric_names
            },
        }

    return {
        "total_scenarios": len(results),
        "mean_scores": {
            name: round(mean(result.scores[name] for result in results), 2)
            for name in rubric_names
        },
        "median_scores": {
            name: round(median(result.scores[name] for result in results), 2)
            for name in rubric_names
        },
        "edit_burden_counts": edit_counts,
        "edit_burden_percentages": {
            key: round(_ratio(value, len(results)) * 100.0, 1)
            for key, value in edit_counts.items()
        },
        "A_plus_B_percentage": round(_ratio(edit_counts["A"] + edit_counts["B"], len(results)) * 100.0, 1),
        "critical_failure_count": critical_total,
        "factual_correction_count": factual_corrections,
        "unsupported_claim_count": unsupported_claims,
        "missing_information_detection_rate": round(_ratio(sum(1 for result in results if result.missing_info_success), len(results)), 4),
        "authority_conflict_success_rate": round(_ratio(sum(1 for result in results if result.authority_success), len(results)), 4),
        "confidentiality_safety_rate": round(_ratio(sum(1 for result in results if result.confidentiality_success), len(results)), 4),
        "correct_next_action_rate": round(_ratio(sum(1 for result in results if result.correct_next_action), len(results)), 4),
        "category_breakdown": category_breakdown,
    }


def build_report(
    *,
    scenarios: tuple[CalibrationScenario, ...],
    results: list[ScoredCase],
    summary: dict[str, Any],
    run_slug: str,
) -> str:
    lines = [
        "# Staging Quality & Calibration Gate",
        "",
        f"- date: 2026-08-20",
        f"- run slug: `{run_slug}`",
        f"- methodology: hosted staging operator API using the real deployed intake/reconcile/waiting/draft path",
        f"- benchmark size: `{len(scenarios)}` synthetic scenarios",
        f"- environment: `APP_ENV=staging`, `Outlook=disabled`, `Asana=configured`, no provider execution used",
        "",
        "## Methodology",
        "",
        "- This baseline uses the real hosted operator path: synthetic case creation, structured observation injection, governed inquiry intake, reconciliation, waiting evaluation, and inquiry-draft generation when a client-information action exists.",
        "- Raw freeform Phase 7 staff-answer generation was not used as the canonical baseline here because the deployed staging surface currently exposes the operator workflow path, while the local repo run does not currently have a populated staging `DATABASE_URL` for direct live retrieval execution against hosted data.",
        "- The benchmark still covers all requested categories A-O, but several categories intentionally expose current surface gaps rather than successful reasoning paths.",
        "",
        "## Baseline Quality",
        "",
        f"- A/B/C/D counts: `{summary['edit_burden_counts']}`",
        f"- A+B percentage: `{summary['A_plus_B_percentage']}%`",
        f"- critical failures: `{summary['critical_failure_count']}`",
        f"- factual correction count: `{summary['factual_correction_count']}`",
        f"- unsupported claim count: `{summary['unsupported_claim_count']}`",
        f"- missing-information detection rate: `{summary['missing_information_detection_rate']}`",
        f"- authority-conflict success rate: `{summary['authority_conflict_success_rate']}`",
        f"- confidentiality safety rate: `{summary['confidentiality_safety_rate']}`",
        f"- correct-next-action rate: `{summary['correct_next_action_rate']}`",
        "",
        "### Mean Rubric Scores",
        "",
    ]
    for key, value in summary["mean_scores"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "### Median Rubric Scores",
            "",
        ]
    )
    for key, value in summary["median_scores"].items():
        lines.append(f"- {key}: `{value}`")

    lines.extend(
        [
            "",
            "## Category Performance",
            "",
        ]
    )
    for category_code, payload in summary["category_breakdown"].items():
        lines.append(f"### {category_code} — {payload['label']}")
        lines.append("")
        lines.append(f"- count: `{payload['count']}`")
        lines.append(f"- A/B/C/D: `{payload['A']}/{payload['B']}/{payload['C']}/{payload['D']}`")
        lines.append(f"- critical failures: `{payload['critical_failures']}`")
        lines.append(f"- authority success rate: `{payload['authority_success_rate']}`")
        lines.append(f"- missing-information detection rate: `{payload['missing_information_detection_rate']}`")
        lines.append(f"- correct-next-action rate: `{payload['correct_next_action_rate']}`")
        lines.append("- mean rubric scores:")
        for key, value in payload["mean_scores"].items():
            lines.append(f"  - {key}: `{value}`")
        lines.append("")

    lines.extend(
        [
            "## Substantive Failures",
            "",
        ]
    )
    failing_results = [
        result for result in results if result.edit_burden in {"C", "D"} or result.critical_failures
    ]
    if not failing_results:
        lines.append("- none")
    else:
        for result in failing_results:
            lines.append(f"### {result.scenario_id}")
            lines.append("")
            lines.append(f"- category: `{result.category_code}` / `{CATEGORY_LABELS[result.category_code]}`")
            lines.append(f"- rental_case_id: `{result.rental_case_id}`")
            lines.append(f"- case_reference_code: `{result.case_reference_code}`")
            lines.append(f"- edit burden: `{result.edit_burden}`")
            lines.append(f"- severity: `{'critical' if result.critical_failures else 'moderate'}`")
            lines.append(f"- failure layer: `{result.diagnosed_layer}`")
            lines.append(f"- root cause: `{result.root_cause}`")
            lines.append(f"- failures: `{list(result.failures)}`")
            lines.append(f"- critical failures: `{list(result.critical_failures)}`")
            lines.append("")

    lines.extend(
        [
            "## Reliability Judgement",
            "",
            "- Result: `NOT READY FOR SUPERVISED STAFF USE` unless the baseline itself clears the requested thresholds. This hosted baseline is expected to miss those thresholds because several category-critical behaviors are still not surfaced through the current inquiry path.",
            "- Primary blockers, if present in the results above, should be interpreted as quality/surface gaps first and only then as candidates for prompt or workflow changes.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_artifacts(
    *,
    output_dir: Path,
    run_slug: str,
    scenarios: tuple[CalibrationScenario, ...],
    results: list[ScoredCase],
    summary: dict[str, Any],
    execution_logs: dict[str, list[dict[str, Any]]],
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    benchmark_path = output_dir / "benchmark_scenarios.json"
    results_path = output_dir / f"baseline_results_{run_slug}.json"
    latest_results_path = output_dir / "baseline_results_latest.json"
    report_path = output_dir / f"baseline_report_{run_slug}.md"
    latest_report_path = output_dir / "baseline_report_latest.md"

    benchmark_payload = {
        "generated_at": "2026-08-20",
        "scenario_count": len(scenarios),
        "scenarios": [scenario.to_benchmark_payload() for scenario in scenarios],
    }
    results_payload = {
        "generated_at": "2026-08-20",
        "run_slug": run_slug,
        "summary": summary,
        "results": [
            {
                "scenario_id": result.scenario_id,
                "category_code": result.category_code,
                "rental_case_id": result.rental_case_id,
                "case_reference_code": result.case_reference_code,
                "scores": result.scores,
                "edit_burden": result.edit_burden,
                "critical_failures": list(result.critical_failures),
                "unsupported_claim_count": result.unsupported_claim_count,
                "factual_correction_count": result.factual_correction_count,
                "missing_info_success": result.missing_info_success,
                "authority_success": result.authority_success,
                "confidentiality_success": result.confidentiality_success,
                "correct_next_action": result.correct_next_action,
                "failures": list(result.failures),
                "diagnosed_layer": result.diagnosed_layer,
                "root_cause": result.root_cause,
                "actual": result.actual,
                "execution_log": execution_logs[result.scenario_id],
            }
            for result in results
        ],
    }

    benchmark_path.write_text(json.dumps(benchmark_payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    results_text = json.dumps(results_payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    results_path.write_text(results_text, encoding="utf-8")
    latest_results_path.write_text(results_text, encoding="utf-8")

    report_text = build_report(
        scenarios=scenarios,
        results=results,
        summary=summary,
        run_slug=run_slug,
    )
    report_path.write_text(report_text, encoding="utf-8")
    latest_report_path.write_text(report_text, encoding="utf-8")

    return {
        "benchmark": benchmark_path,
        "results": results_path,
        "results_latest": latest_results_path,
        "report": report_path,
        "report_latest": latest_report_path,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the staging operator quality/calibration benchmark.")
    parser.add_argument("--auth-file", type=Path, default=DEFAULT_AUTH_FILE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--limit", type=int, help="Run only the first N scenarios for a probe.")
    parser.add_argument("--dry-run", action="store_true", help="Write the benchmark definition only.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scenarios = build_scenarios()
    if args.limit:
        scenarios = scenarios[: args.limit]
    run_slug = _now_slug()

    if args.dry_run:
        paths = write_artifacts(
            output_dir=args.output_dir,
            run_slug=run_slug,
            scenarios=scenarios,
            results=[],
            summary={
                "total_scenarios": len(scenarios),
                "mean_scores": {},
                "median_scores": {},
                "edit_burden_counts": {"A": 0, "B": 0, "C": 0, "D": 0},
                "edit_burden_percentages": {"A": 0.0, "B": 0.0, "C": 0.0, "D": 0.0},
                "A_plus_B_percentage": 0.0,
                "critical_failure_count": 0,
                "factual_correction_count": 0,
                "unsupported_claim_count": 0,
                "missing_information_detection_rate": 0.0,
                "authority_conflict_success_rate": 0.0,
                "confidentiality_safety_rate": 0.0,
                "correct_next_action_rate": 0.0,
                "category_breakdown": {},
            },
            execution_logs={},
        )
        print(f"Wrote benchmark definition to {paths['benchmark']}")
        return 0

    client = build_client(args.auth_file, timeout_seconds=args.timeout_seconds)
    health = client.get_health()
    if health.get("status") != "ok":
        raise SystemExit("Hosted staging /healthz is not healthy enough for calibration.")

    results: list[ScoredCase] = []
    execution_logs: dict[str, list[dict[str, Any]]] = {}
    for scenario in scenarios:
        actual, logs = run_scenario(client, scenario, run_slug=run_slug)
        execution_logs[scenario.scenario_id] = logs
        results.append(evaluate_case(scenario, actual))

    summary = summarize_results(results)
    paths = write_artifacts(
        output_dir=args.output_dir,
        run_slug=run_slug,
        scenarios=scenarios,
        results=results,
        summary=summary,
        execution_logs=execution_logs,
    )
    print(json.dumps({"summary": summary, "artifacts": {key: str(value) for key, value in paths.items()}}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
