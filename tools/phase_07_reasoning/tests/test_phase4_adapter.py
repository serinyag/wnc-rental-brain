from __future__ import annotations

import json
import subprocess
import unittest

from tools.phase_07_reasoning.contracts import (
    CONFIDENTIALITY_LEVEL_INTERNAL,
    EXECUTION_STATE_FAILED,
    EXECUTION_STATE_NOT_REQUESTED,
    EXECUTION_STATE_SUCCESS,
    LAYER_ID_PHASE_4,
    PERSONAL_INFORMATION_STATUS_UNKNOWN,
    PHASE_4_DOMAIN_BOOKING_FEE,
    PHASE_4_DOMAIN_CAPACITY,
    PHASE_4_DOMAIN_CATERING_SUPPLIER,
    PHASE_4_DOMAIN_CODES,
    PHASE_4_DOMAIN_EXPEDITED_SURCHARGE,
    PHASE_4_DOMAIN_FACILITATOR_REQUIREMENTS,
    PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS,
    PHASE_4_DOMAIN_PAYMENT,
    PHASE_4_DOMAIN_SERVICE_RULES,
    PHASE_4_DOMAIN_SPACE_ACCESS,
    PHASE_4_DOMAIN_TECHNICAL_CAPABILITY,
    PHASE_4_DOMAIN_TECHNICAL_INVENTORY,
    Phase4RoutingIntent,
    QueryPlan,
    REASONING_STATE_INSUFFICIENT_INFORMATION,
    REASONING_STATE_NO_APPLICABLE_RULE,
    REASONING_STATE_REQUIRES_CONFIRMATION,
    REASONING_STATE_RESOLVED,
    SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
)
from tools.phase_07_reasoning.phase4_adapter import PHASE4_ADAPTER_REGISTRY, execute_phase4_plan


def make_plan(
    *,
    query_text: str,
    domains: tuple[str, ...],
    domain_inputs: dict[str, dict] | None = None,
    required: bool = True,
) -> QueryPlan:
    return QueryPlan(
        query_text=query_text,
        query_class="deterministic_current",
        routing_confidence="high",
        required_layers=(LAYER_ID_PHASE_4,) if required else (),
        phase_4=Phase4RoutingIntent(
            required=required,
            domains=domains,
            domain_inputs=domain_inputs or {},
        ),
    )


def domain_items(record, domain_code: str) -> list:
    return [item for item in record.normalized_items if item.layer_payload["phase_4_domain"] == domain_code]


class Phase4AdapterTests(unittest.TestCase):
    def test_registry_covers_all_frozen_domains(self) -> None:
        self.assertEqual(set(PHASE4_ADAPTER_REGISTRY), set(PHASE_4_DOMAIN_CODES))

    def test_not_requested_behavior(self) -> None:
        plan = QueryPlan(
            query_text="No phase 4 requested.",
            query_class="current_guidance",
            routing_confidence="high",
            required_layers=(),
            phase_4=Phase4RoutingIntent(required=False, domains=(), domain_inputs={}),
        )
        record = execute_phase4_plan(plan)
        self.assertFalse(record.requested)
        self.assertEqual(record.execution_state, EXECUTION_STATE_NOT_REQUESTED)
        self.assertEqual(record.result_count, 0)

    def test_payment_confirmation_rule_is_normalized_with_provenance(self) -> None:
        plan = make_plan(
            query_text="What minimum payment confirms a booking right now?",
            domains=(PHASE_4_DOMAIN_PAYMENT,),
            domain_inputs={
                PHASE_4_DOMAIN_PAYMENT: {
                    "payment_stage": "confirmation_requirement",
                    "as_of_date": "2026-08-03",
                }
            },
        )
        record = execute_phase4_plan(plan)
        self.assertEqual(record.execution_state, EXECUTION_STATE_SUCCESS)
        self.assertEqual(record.reasoning_state, REASONING_STATE_RESOLVED)
        self.assertEqual(record.result_count, 1)
        item = record.normalized_items[0]
        self.assertEqual(item.stable_identity.primary_code, "PAYMENT_CONFIRMATION_MINIMUM_30_PERCENT")
        self.assertEqual(item.layer_payload["percentage_due"], 30.0)
        self.assertTrue(item.layer_payload["required_for_confirmation"])
        self.assertEqual(item.source_layer_role, SOURCE_LAYER_ROLE_DETERMINISTIC_RULE)
        self.assertEqual(item.provenance.source_link_count, 3)
        self.assertIn("source_registry_ids", item.provenance.source_identifiers)
        self.assertIn("deep_sources", item.provenance.native_provenance_payload)

    def test_multi_domain_execution_preserves_domain_traceability(self) -> None:
        plan = make_plan(
            query_text="Can an external caterer work here, and what are the current grace-period boundaries?",
            domains=(PHASE_4_DOMAIN_CATERING_SUPPLIER, PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS),
            domain_inputs={
                PHASE_4_DOMAIN_CATERING_SUPPLIER: {
                    "catering_arrangement": "external_caterer",
                    "rule_type": "arrangement_policy",
                    "alcohol_service": False,
                    "as_of_date": "2026-08-05",
                },
                PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS: {
                    "rental_type_code": "entire_venue",
                    "requirement_type": "grace_period",
                    "multi_day": False,
                    "as_of_date": "2026-08-05",
                },
            },
        )
        record = execute_phase4_plan(plan)
        self.assertEqual(record.execution_state, EXECUTION_STATE_SUCCESS)
        self.assertEqual(record.result_count, 2)
        self.assertEqual({item.layer_payload["phase_4_domain"] for item in record.normalized_items}, set(plan.phase_4.domains))
        self.assertEqual(domain_items(record, PHASE_4_DOMAIN_CATERING_SUPPLIER)[0].stable_identity.primary_code, "CATER_EXTERNAL_CATERER_ALLOWED")
        self.assertEqual(domain_items(record, PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS)[0].stable_identity.primary_code, "OPER_ENTIRE_VENUE_GRACE_PERIOD")

    def test_evaluation_scenarios_match_live_phase4_rules(self) -> None:
        scenario_fixtures = (
            (
                "P7-EVAL-001",
                make_plan(
                    query_text="What minimum payment confirms a booking right now?",
                    domains=(PHASE_4_DOMAIN_PAYMENT,),
                    domain_inputs={PHASE_4_DOMAIN_PAYMENT: {"payment_stage": "confirmation_requirement", "as_of_date": "2026-08-03"}},
                ),
                {"PAYMENT_CONFIRMATION_MINIMUM_30_PERCENT"},
                lambda item: self.assertEqual(item.layer_payload["percentage_due"], 30.0),
                REASONING_STATE_RESOLVED,
            ),
            (
                "P7-EVAL-002",
                make_plan(
                    query_text="Does the expedited surcharge apply if the event is within 14 days?",
                    domains=(PHASE_4_DOMAIN_EXPEDITED_SURCHARGE,),
                    domain_inputs={PHASE_4_DOMAIN_EXPEDITED_SURCHARGE: {"confirmation_date": "2026-08-19", "event_date": "2026-09-02", "as_of_date": "2026-08-03"}},
                ),
                {"EXPEDITED_SURCHARGE_WITHIN_14_DAYS"},
                lambda item: self.assertTrue(item.layer_payload["applies"]),
                REASONING_STATE_RESOLVED,
            ),
            (
                "P7-EVAL-003",
                make_plan(
                    query_text="What is the current legal maximum capacity for the entire venue?",
                    domains=(PHASE_4_DOMAIN_CAPACITY,),
                    domain_inputs={PHASE_4_DOMAIN_CAPACITY: {"scope_type": "rental_type", "scope_code": "entire_venue", "as_of_date": "2026-08-05"}},
                ),
                {"CAPACITY_ENTIRE_VENUE_LEGAL_MAXIMUM"},
                lambda item: self.assertEqual(item.layer_payload["max_guests"], 110),
                REASONING_STATE_RESOLVED,
            ),
            (
                "P7-EVAL-004",
                make_plan(
                    query_text="What is the current lying-down capacity in the studio?",
                    domains=(PHASE_4_DOMAIN_CAPACITY,),
                    domain_inputs={PHASE_4_DOMAIN_CAPACITY: {"scope_type": "venue_space", "scope_code": "studio_space", "configuration_type": "lying_down", "as_of_date": "2026-08-05"}},
                ),
                {"CAPACITY_STUDIO_LYING_DOWN"},
                lambda item: self.assertEqual(item.layer_payload["max_guests"], 25),
                REASONING_STATE_RESOLVED,
            ),
            (
                "P7-EVAL-005",
                make_plan(
                    query_text="Is the 1:1 / Podcast Room included in an Entire Venue rental?",
                    domains=(PHASE_4_DOMAIN_SPACE_ACCESS,),
                    domain_inputs={PHASE_4_DOMAIN_SPACE_ACCESS: {"mode": "evaluate", "rental_type_code": "entire_venue", "venue_space_code": "one_to_one_room", "as_of_date": "2026-08-05"}},
                ),
                {"ACCESS_ENTIRE_VENUE_ONE_TO_ONE_INCLUDED"},
                lambda item: self.assertEqual(item.layer_payload["access_status"], "included"),
                REASONING_STATE_RESOLVED,
            ),
            (
                "P7-EVAL-006",
                make_plan(
                    query_text="When is the final balance due?",
                    domains=(PHASE_4_DOMAIN_PAYMENT,),
                    domain_inputs={PHASE_4_DOMAIN_PAYMENT: {"payment_stage": "final_balance", "payment_plan_option": "upfront_30", "booking_lead_time_days": 15, "as_of_date": "2026-08-03"}},
                ),
                {"PAYMENT_FINAL_BALANCE_70_PERCENT_14_DAYS"},
                lambda item: self.assertEqual(item.layer_payload["deadline_value"], 14),
                REASONING_STATE_RESOLVED,
            ),
            (
                "P7-EVAL-007",
                make_plan(
                    query_text="Can an external caterer work here right now?",
                    domains=(PHASE_4_DOMAIN_CATERING_SUPPLIER,),
                    domain_inputs={PHASE_4_DOMAIN_CATERING_SUPPLIER: {"catering_arrangement": "external_caterer", "rule_type": "arrangement_policy", "alcohol_service": False, "as_of_date": "2026-08-05"}},
                ),
                {"CATER_EXTERNAL_CATERER_ALLOWED"},
                lambda item: self.assertEqual(item.layer_payload["outcome"], "allowed"),
                REASONING_STATE_RESOLVED,
            ),
            (
                "P7-EVAL-010",
                make_plan(
                    query_text="Can WNC source a facilitator?",
                    domains=(PHASE_4_DOMAIN_FACILITATOR_REQUIREMENTS,),
                    domain_inputs={PHASE_4_DOMAIN_FACILITATOR_REQUIREMENTS: {"facilitator_arrangement": "wnc_provided", "as_of_date": "2026-08-05"}},
                ),
                {"FACILITATOR_WNC_PROVIDED_CONFIRMATION_REQUIRED"},
                lambda item: self.assertTrue(item.layer_payload["requires_availability_confirmation"]),
                REASONING_STATE_REQUIRES_CONFIRMATION,
            ),
            (
                "P7-EVAL-024",
                make_plan(
                    query_text="The client wants a non-standard technical setup with high electrical load.",
                    domains=(PHASE_4_DOMAIN_TECHNICAL_CAPABILITY,),
                    domain_inputs={PHASE_4_DOMAIN_TECHNICAL_CAPABILITY: {"requirement_code": "custom_technical_setup", "as_of_date": "2026-08-05"}},
                ),
                {"TECH_REQ_CUSTOM_TECH_CONFIRM"},
                lambda item: self.assertEqual(item.layer_payload["support_status"], "requires_confirmation"),
                REASONING_STATE_REQUIRES_CONFIRMATION,
            ),
            (
                "P7-EVAL-030",
                make_plan(
                    query_text="Can a client use setup time now?",
                    domains=(PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS,),
                    domain_inputs={PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS: {"rental_type_code": "studio_space", "requirement_type": "setup_start", "multi_day": False, "as_of_date": "2026-08-05"}},
                ),
                {"OPER_SETUP_START_AT_BOOKED_TIME"},
                lambda item: self.assertEqual(item.layer_payload["timing_reference"], "booked_start_time"),
                REASONING_STATE_RESOLVED,
            ),
            (
                "P7-EVAL-031",
                make_plan(
                    query_text="Is the Back Office allowed now?",
                    domains=(PHASE_4_DOMAIN_SPACE_ACCESS,),
                    domain_inputs={PHASE_4_DOMAIN_SPACE_ACCESS: {"mode": "evaluate", "rental_type_code": "studio_space", "venue_space_code": "back_office", "as_of_date": "2026-08-05"}},
                ),
                {"ACCESS_STUDIO_BACK_OFFICE_RESTRICTED"},
                lambda item: self.assertEqual(item.layer_payload["applicability_status"], "restricted"),
                REASONING_STATE_REQUIRES_CONFIRMATION,
            ),
            (
                "P7-EVAL-035",
                make_plan(
                    query_text="Can we support this unusual custom tech rig beyond the standard inventory?",
                    domains=(PHASE_4_DOMAIN_TECHNICAL_CAPABILITY,),
                    domain_inputs={PHASE_4_DOMAIN_TECHNICAL_CAPABILITY: {"requirement_code": "custom_technical_setup", "as_of_date": "2026-08-05"}},
                ),
                {"TECH_REQ_CUSTOM_TECH_CONFIRM"},
                lambda item: self.assertTrue(item.layer_payload["client_may_self_organise"]),
                REASONING_STATE_REQUIRES_CONFIRMATION,
            ),
            (
                "P7-EVAL-036",
                make_plan(
                    query_text="What is the fixed capacity of the 1:1 / Podcast Room for this event format?",
                    domains=(PHASE_4_DOMAIN_CAPACITY,),
                    domain_inputs={PHASE_4_DOMAIN_CAPACITY: {"scope_type": "venue_space", "scope_code": "one_to_one_room", "guest_count": 6, "as_of_date": "2026-08-05"}},
                ),
                set(),
                lambda item: self.assertEqual(item.layer_payload["capacity_evaluation_status"], "requires_confirmation"),
                REASONING_STATE_REQUIRES_CONFIRMATION,
            ),
        )

        for scenario_id, plan, expected_codes, extra_assertion, expected_reasoning_state in scenario_fixtures:
            with self.subTest(scenario_id=scenario_id):
                record = execute_phase4_plan(plan)
                self.assertEqual(record.execution_state, EXECUTION_STATE_SUCCESS)
                self.assertTrue(record.normalized_items)
                codes = {item.stable_identity.primary_code for item in record.normalized_items if item.stable_identity.primary_code}
                if expected_codes:
                    self.assertTrue(expected_codes.issubset(codes))
                for item in record.normalized_items:
                    extra_assertion(item)
                    self.assertEqual(item.reasoning_state, expected_reasoning_state)

    def test_technical_inventory_quantity_preserves_resolved_insufficient_quantity(self) -> None:
        plan = make_plan(
            query_text="Do we have two basic projectors?",
            domains=(PHASE_4_DOMAIN_TECHNICAL_INVENTORY,),
            domain_inputs={PHASE_4_DOMAIN_TECHNICAL_INVENTORY: {"equipment_code": "basic_projector", "requested_quantity": 2}},
        )
        record = execute_phase4_plan(plan)
        item = record.normalized_items[0]
        self.assertEqual(item.layer_payload["quantity_evaluation_status"], "insufficient_quantity")
        self.assertEqual(item.reasoning_state, REASONING_STATE_RESOLVED)
        self.assertEqual(item.provenance.primary_source_locator, "source_code:OPS-002")

    def test_no_applicable_rule_is_distinct_from_failure(self) -> None:
        plan = make_plan(
            query_text="Is there an allowance rule for an external caterer?",
            domains=(PHASE_4_DOMAIN_CATERING_SUPPLIER,),
            domain_inputs={PHASE_4_DOMAIN_CATERING_SUPPLIER: {"catering_arrangement": "external_caterer", "rule_type": "allowance", "alcohol_service": False, "as_of_date": "2026-08-05"}},
        )
        record = execute_phase4_plan(plan)
        self.assertEqual(record.execution_state, EXECUTION_STATE_SUCCESS)
        self.assertEqual(record.normalized_items[0].reasoning_state, REASONING_STATE_NO_APPLICABLE_RULE)
        self.assertIsNone(record.normalized_items[0].exact_identity.primary_id)

    def test_insufficient_information_is_normalized_without_guessing(self) -> None:
        plan = make_plan(
            query_text="When is the confirmation deadline?",
            domains=(PHASE_4_DOMAIN_PAYMENT,),
            domain_inputs={PHASE_4_DOMAIN_PAYMENT: {"payment_stage": "confirmation_deadline", "as_of_date": "2026-08-03"}},
        )
        record = execute_phase4_plan(plan)
        item = record.normalized_items[0]
        self.assertEqual(record.execution_state, EXECUTION_STATE_SUCCESS)
        self.assertEqual(item.reasoning_state, REASONING_STATE_INSUFFICIENT_INFORMATION)
        self.assertEqual(item.layer_payload["input_snapshot"]["payment_stage"], "confirmation_deadline")

    def test_failure_is_reported_without_fake_results(self) -> None:
        def failing_runner(sql: str):
            raise subprocess.CalledProcessError(returncode=1, cmd=["psql"], stderr="sensitive detail")

        plan = make_plan(
            query_text="What minimum payment confirms a booking right now?",
            domains=(PHASE_4_DOMAIN_PAYMENT,),
            domain_inputs={PHASE_4_DOMAIN_PAYMENT: {"payment_stage": "confirmation_requirement", "as_of_date": "2026-08-03"}},
        )
        record = execute_phase4_plan(plan, query_runner=failing_runner)
        self.assertEqual(record.execution_state, EXECUTION_STATE_FAILED)
        self.assertEqual(record.result_count, 0)
        self.assertEqual(record.error_category, "phase4_execution_failed")
        self.assertIn("payment", record.safe_error_message)

    def test_sensitivity_defaults_and_json_serialization_are_stable(self) -> None:
        plan = make_plan(
            query_text="What does Supported Rental mean right now?",
            domains=(PHASE_4_DOMAIN_SERVICE_RULES,),
            domain_inputs={PHASE_4_DOMAIN_SERVICE_RULES: {"service_level": "supported_rental", "as_of_date": "2026-08-05"}},
        )
        record = execute_phase4_plan(plan)
        item = record.normalized_items[0]
        self.assertEqual(item.sensitivity.confidentiality_level, CONFIDENTIALITY_LEVEL_INTERNAL)
        self.assertEqual(item.sensitivity.personal_information_status, PERSONAL_INFORMATION_STATUS_UNKNOWN)
        payload = json.loads(record.to_json())
        self.assertEqual(payload["layer_id"], LAYER_ID_PHASE_4)
        self.assertEqual(payload["normalized_items"][0]["authority_tier_code"], "current_deterministic")

    def test_booking_fee_and_inventory_items_stay_json_serializable(self) -> None:
        plan = make_plan(
            query_text="What booking fee applies and what yoga mats exist?",
            domains=(PHASE_4_DOMAIN_BOOKING_FEE, PHASE_4_DOMAIN_TECHNICAL_INVENTORY),
            domain_inputs={
                PHASE_4_DOMAIN_BOOKING_FEE: {"rental_type_code": "studio_space", "duration_hours": 2, "as_of_date": "2026-08-03"},
                PHASE_4_DOMAIN_TECHNICAL_INVENTORY: {"equipment_code": "yoga_mats"},
            },
        )
        record = execute_phase4_plan(plan)
        self.assertEqual(record.execution_state, EXECUTION_STATE_SUCCESS)
        self.assertEqual(record.result_count, 2)
        self.assertEqual(domain_items(record, PHASE_4_DOMAIN_BOOKING_FEE)[0].stable_identity.primary_code, "FEE_STUDIO_1_TO_3_HOUR_BOOKING")
        inventory_item = domain_items(record, PHASE_4_DOMAIN_TECHNICAL_INVENTORY)[0]
        self.assertEqual(inventory_item.stable_identity.primary_code, "yoga_mats")
        self.assertEqual(inventory_item.layer_payload["quantity_numeric"], 30)
        self.assertTrue(json.loads(record.to_json())["normalized_items"])


if __name__ == "__main__":
    unittest.main()
