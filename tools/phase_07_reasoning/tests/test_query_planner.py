from __future__ import annotations

import unittest

from tools.phase_07_reasoning.contracts import (
    LAYER_ID_PHASE_4,
    LAYER_ID_PHASE_5,
    LAYER_ID_PHASE_6,
    PHASE_4_DOMAIN_CATERING_SUPPLIER,
    PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS,
    PHASE_4_DOMAIN_PAYMENT,
    PHASE_4_DOMAIN_TECHNICAL_CAPABILITY,
    PHASE_4_DOMAIN_TECHNICAL_INVENTORY,
    QUERY_CLASS_AUTHORITY_VERIFICATION,
    QUERY_CLASS_CURRENT_GUIDANCE,
    QUERY_CLASS_DETERMINISTIC_CURRENT,
    QUERY_CLASS_MIXED_CURRENT_AND_PRECEDENT,
    QUERY_CLASS_PRECEDENT_DISCOVERY,
    QUERY_CLASS_UNRESOLVED_AUTHORITY,
    ROUTING_CONFIDENCE_LOW,
    Phase7ContractError,
)
from tools.phase_07_reasoning.evaluation_scenarios import EVALUATION_SCENARIOS, evaluate_planner
from tools.phase_07_reasoning.query_planner import (
    AMBIGUITY_FLAG_AMBIGUOUS_DEPOSIT_TYPE,
    AMBIGUITY_FLAG_AMBIGUOUS_TECHNICAL,
    AMBIGUITY_FLAG_HISTORICAL_WITH_CURRENT_POLICY,
    SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4,
    SAFETY_OVERRIDE_HISTORICAL_COMMERCIAL_CURRENT_AUTHORITY,
    SAFETY_OVERRIDE_HISTORICAL_CURRENT_AUTHORITY,
    plan_query,
)


class QueryPlannerTests(unittest.TestCase):
    def test_deterministic_current_classification(self) -> None:
        plan = plan_query("What minimum payment confirms a booking right now?")
        self.assertEqual(plan.query_class, QUERY_CLASS_DETERMINISTIC_CURRENT)
        self.assertEqual(plan.required_layers, (LAYER_ID_PHASE_4,))
        self.assertEqual(plan.phase_4.domains, (PHASE_4_DOMAIN_PAYMENT,))

    def test_current_guidance_classification(self) -> None:
        plan = plan_query("How should staff schedule and confirm a site visit?")
        self.assertEqual(plan.query_class, QUERY_CLASS_CURRENT_GUIDANCE)
        self.assertEqual(plan.required_layers, (LAYER_ID_PHASE_5,))

    def test_precedent_discovery_classification(self) -> None:
        plan = plan_query("Have we handled a multi-day venue takeover before?")
        self.assertEqual(plan.query_class, QUERY_CLASS_PRECEDENT_DISCOVERY)
        self.assertEqual(plan.required_layers, (LAYER_ID_PHASE_6,))

    def test_mixed_query_classification(self) -> None:
        plan = plan_query(
            "A beauty brand wants strong-smell catering. Have we dealt with this before, and what should we do now?"
        )
        self.assertEqual(plan.query_class, QUERY_CLASS_MIXED_CURRENT_AND_PRECEDENT)
        self.assertEqual(plan.required_layers, (LAYER_ID_PHASE_4, LAYER_ID_PHASE_5, LAYER_ID_PHASE_6))
        self.assertEqual(
            set(plan.phase_4.domains),
            {PHASE_4_DOMAIN_CATERING_SUPPLIER, PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS},
        )

    def test_historical_current_authority_verification(self) -> None:
        plan = plan_query("A restricted historical storage precedent is relevant to a new pitch. What may be surfaced internally?")
        self.assertEqual(plan.query_class, QUERY_CLASS_AUTHORITY_VERIFICATION)
        self.assertEqual(plan.required_layers, (LAYER_ID_PHASE_5, LAYER_ID_PHASE_6))
        self.assertIn(SAFETY_OVERRIDE_HISTORICAL_CURRENT_AUTHORITY, plan.safety_overrides)

    def test_unresolved_authority_cue(self) -> None:
        plan = plan_query("What is WNC's official collaboration or exposure discount policy today?")
        self.assertEqual(plan.query_class, QUERY_CLASS_UNRESOLVED_AUTHORITY)
        self.assertEqual(plan.required_layers, (LAYER_ID_PHASE_5,))

    def test_multi_domain_phase4_mapping(self) -> None:
        plan = plan_query("Can an external caterer bring high-load coffee machines?")
        self.assertIn(LAYER_ID_PHASE_4, plan.required_layers)
        self.assertEqual(
            set(plan.phase_4.domains),
            {
                PHASE_4_DOMAIN_CATERING_SUPPLIER,
                PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS,
                PHASE_4_DOMAIN_TECHNICAL_CAPABILITY,
            },
        )

    def test_deposit_ambiguity_is_recorded(self) -> None:
        plan = plan_query("What is the official security deposit for this custom-scope rental?")
        self.assertIn(AMBIGUITY_FLAG_AMBIGUOUS_DEPOSIT_TYPE, plan.ambiguity_flags)
        self.assertEqual(plan.routing_confidence, ROUTING_CONFIDENCE_LOW)
        self.assertNotIn(LAYER_ID_PHASE_4, plan.required_layers)

    def test_technical_inventory_vs_capability_ambiguity_is_recorded(self) -> None:
        plan = plan_query("Can we support this unusual custom tech rig beyond the standard inventory?")
        self.assertIn(AMBIGUITY_FLAG_AMBIGUOUS_TECHNICAL, plan.ambiguity_flags)
        self.assertEqual(
            set(plan.phase_4.domains),
            {PHASE_4_DOMAIN_TECHNICAL_CAPABILITY, PHASE_4_DOMAIN_TECHNICAL_INVENTORY},
        )

    def test_safety_augmentation_adds_current_authority_to_historical_price_conversion(self) -> None:
        plan = plan_query("WineGB paid EUR 300 for storage. Can I quote EUR 300 to this client now?")
        self.assertEqual(plan.query_class, QUERY_CLASS_UNRESOLVED_AUTHORITY)
        self.assertEqual(plan.required_layers, (LAYER_ID_PHASE_4, LAYER_ID_PHASE_5, LAYER_ID_PHASE_6))
        self.assertIn(AMBIGUITY_FLAG_HISTORICAL_WITH_CURRENT_POLICY, plan.ambiguity_flags)
        self.assertIn(SAFETY_OVERRIDE_CURRENT_DETERMINISTIC_PHASE4, plan.safety_overrides)
        self.assertIn(SAFETY_OVERRIDE_HISTORICAL_CURRENT_AUTHORITY, plan.safety_overrides)
        self.assertIn(SAFETY_OVERRIDE_HISTORICAL_COMMERCIAL_CURRENT_AUTHORITY, plan.safety_overrides)

    def test_deterministic_repeatability(self) -> None:
        query = "Historical client-operated events existed. Does that override current Supported Rental or Full Production boundaries?"
        first = plan_query(query)
        second = plan_query(query)
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_malformed_query_is_rejected(self) -> None:
        with self.assertRaisesRegex(Phase7ContractError, "query_text must be a non-empty string"):
            plan_query("  ")

    def test_40_scenario_benchmark_meets_readiness_thresholds(self) -> None:
        evaluation = evaluate_planner(plan_query)
        self.assertEqual(len(EVALUATION_SCENARIOS), 40)
        self.assertEqual(evaluation.required_layer_recall, 1.0)
        self.assertEqual(evaluation.exact_required_layer_set_accuracy, 1.0)
        self.assertEqual(evaluation.unnecessary_layer_rate, 0.0)
        self.assertEqual(evaluation.query_class_accuracy, 1.0)
        self.assertEqual(evaluation.phase4_required_domain_recall, 1.0)
        self.assertEqual(evaluation.phase4_exact_domain_set_accuracy, 1.0)
        self.assertEqual(evaluation.safety_override_recall, 1.0)


if __name__ == "__main__":
    unittest.main()
