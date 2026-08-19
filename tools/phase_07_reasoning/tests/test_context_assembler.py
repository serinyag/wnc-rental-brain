from __future__ import annotations

import json
import unittest

from tools.phase_07_reasoning.context_assembler import build_context_package
from tools.phase_07_reasoning.contracts import (
    EXECUTION_STATE_FAILED,
    EXECUTION_STATE_NOT_REQUESTED,
    EXECUTION_STATE_SUCCESS,
    EXECUTION_STATE_UNAVAILABLE,
    LAYER_ID_PHASE_4,
    LAYER_ID_PHASE_5,
    LAYER_ID_PHASE_6,
    QUERY_CLASS_DETERMINISTIC_CURRENT,
    QUERY_CLASS_MIXED_CURRENT_AND_PRECEDENT,
    ROUTING_CONFIDENCE_HIGH,
    ExactIdentity,
    LayerExecutionRecord,
    NormalizedResultEnvelope,
    Phase4RoutingIntent,
    Phase5RoutingIntent,
    Phase6RoutingIntent,
    Phase7RuntimeConfiguration,
    ProvenanceEnvelope,
    QueryContext,
    QueryPlan,
    RetrievalMetadata,
    SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
    SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
    SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
    SensitivityEnvelope,
    StableIdentity,
    authority_priority_for_tier,
    authority_tier_for_source_role,
    phase4_default_sensitivity,
)


def make_item(
    *,
    item_id: str,
    source_layer_role: str,
    primary_code: str,
    primary_id: int,
    reasoning_state: str | None,
    sensitivity: SensitivityEnvelope | None = None,
    layer_payload: dict | None = None,
) -> NormalizedResultEnvelope:
    retrieval = None
    if source_layer_role != SOURCE_LAYER_ROLE_DETERMINISTIC_RULE:
        retrieval = RetrievalMetadata(
            retrieval_mode_requested="hybrid",
            retrieval_mode_used="hybrid",
            fallback_used=False,
            fallback_reason=None,
            rank=1,
            score=1.0,
            component_scores={},
            strategy_code="fixture",
            native_retrieval_payload={},
        )
    return NormalizedResultEnvelope(
        item_id=item_id,
        source_layer_role=source_layer_role,
        authority_tier_code=authority_tier_for_source_role(source_layer_role),
        authority_priority=authority_priority_for_tier(authority_tier_for_source_role(source_layer_role)),
        stable_identity=StableIdentity(primary_code=primary_code),
        exact_identity=ExactIdentity(primary_id=primary_id, version_id=primary_id),
        content_kind="fixture_item",
        execution_state=EXECUTION_STATE_SUCCESS,
        reasoning_state=reasoning_state,
        summary_text=f"{primary_code} summary",
        provenance=ProvenanceEnvelope(
            source_codes=(primary_code,),
            source_identifiers={"primary_code": primary_code},
            primary_source_locator=f"{primary_code} locator",
            additional_locators=(),
            source_link_count=1,
            native_provenance_payload={},
        ),
        sensitivity=sensitivity or phase4_default_sensitivity(),
        retrieval=retrieval,
        layer_payload=layer_payload or {},
    )


def make_record(
    layer_id: str,
    *,
    requested: bool = True,
    execution_state: str = EXECUTION_STATE_SUCCESS,
    reasoning_state: str | None = None,
    items: tuple[NormalizedResultEnvelope, ...] = (),
    fallback_reason: str | None = None,
) -> LayerExecutionRecord:
    return LayerExecutionRecord(
        layer_id=layer_id,
        requested=requested,
        execution_state=execution_state,
        reasoning_state=reasoning_state,
        fallback_reason=fallback_reason,
        error_category=None,
        safe_error_message=None,
        result_count=len(items),
        normalized_items=items,
    )


class ContextAssemblerTests(unittest.TestCase):
    def test_selective_execution_skips_unrequested_layers(self) -> None:
        question = "What minimum payment confirms a booking right now?"
        plan = QueryPlan(
            query_text=question,
            query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
            routing_confidence=ROUTING_CONFIDENCE_HIGH,
            required_layers=(LAYER_ID_PHASE_4,),
            phase_4=Phase4RoutingIntent(required=True, domains=("payment",)),
        )
        calls: list[str] = []

        def planner_fn(query_text, query_context=None, runtime_configuration=None):
            self.assertEqual(query_text, question)
            self.assertEqual(query_context.query_text, question)
            return plan

        def phase4_executor(*_args, **_kwargs):
            calls.append("phase4")
            return make_record(
                LAYER_ID_PHASE_4,
                items=(
                    make_item(
                        item_id="p4-payment",
                        source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
                        primary_code="PAYMENT_CONFIRMATION_MINIMUM_30_PERCENT",
                        primary_id=1,
                        reasoning_state="resolved",
                        layer_payload={"phase_4_domain": "payment"},
                    ),
                ),
                reasoning_state="resolved",
            )

        def unexpected_phase5(*_args, **_kwargs):
            raise AssertionError("phase 5 should not execute")

        def unexpected_phase6(*_args, **_kwargs):
            raise AssertionError("phase 6 should not execute")

        package = build_context_package(
            question,
            planner_fn=planner_fn,
            phase4_executor=phase4_executor,
            phase5_executor=unexpected_phase5,
            phase6_executor=unexpected_phase6,
        )

        self.assertEqual(calls, ["phase4"])
        self.assertEqual(package.layer_execution[1].execution_state, EXECUTION_STATE_NOT_REQUESTED)
        self.assertEqual(package.layer_execution[2].execution_state, EXECUTION_STATE_NOT_REQUESTED)
        self.assertEqual(package.authority_resolution.overall_outcome_classification, "DETERMINISTIC_CURRENT")

    def test_context_package_validates_cross_references_and_serializes(self) -> None:
        question = "The client wants to run a whole-venue event themselves. What does WNC handle now, and have we done similar before?"
        plan = QueryPlan(
            query_text=question,
            query_class=QUERY_CLASS_MIXED_CURRENT_AND_PRECEDENT,
            routing_confidence=ROUTING_CONFIDENCE_HIGH,
            required_layers=(LAYER_ID_PHASE_4, LAYER_ID_PHASE_5, LAYER_ID_PHASE_6),
            phase_4=Phase4RoutingIntent(required=True, domains=("service_rules",)),
            phase_5=Phase5RoutingIntent(required=True, needs_guidance=True, query_text=question),
            phase_6=Phase6RoutingIntent(required=True, query_text=question),
        )
        p4_item = make_item(
            item_id="p4-service",
            source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
            primary_code="SERVICE_LEVEL_SUPPORTED_RENTAL",
            primary_id=2,
            reasoning_state="resolved",
            layer_payload={"phase_4_domain": "service_rules"},
        )
        p5_item = make_item(
            item_id="p5-guidance",
            source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
            primary_code="SERV-001",
            primary_id=3,
            reasoning_state=None,
            sensitivity=SensitivityEnvelope(
                confidentiality_level="commercially_sensitive",
                personal_information_status="no",
                de_identification_required=False,
                generation_allowed=True,
                generation_restriction_reason=None,
                native_sensitivity_payload={},
            ),
        )
        p6_item = make_item(
            item_id="p6-precedent",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HC-006",
            primary_id=6,
            reasoning_state=None,
            sensitivity=SensitivityEnvelope(
                confidentiality_level="restricted",
                personal_information_status="yes",
                de_identification_required=True,
                generation_allowed=True,
                generation_restriction_reason=None,
                native_sensitivity_payload={},
            ),
            layer_payload={"precedent_availability": "active"},
        )

        package = build_context_package(
            question,
            query_context=QueryContext(query_text=question),
            planner_fn=lambda *_args, **_kwargs: plan,
            phase4_executor=lambda *_args, **_kwargs: make_record(LAYER_ID_PHASE_4, items=(p4_item,), reasoning_state="resolved"),
            phase5_executor=lambda *_args, **_kwargs: make_record(LAYER_ID_PHASE_5, items=(p5_item,)),
            phase6_executor=lambda *_args, **_kwargs: make_record(LAYER_ID_PHASE_6, items=(p6_item,)),
            runtime_configuration=Phase7RuntimeConfiguration(),
        )

        self.assertEqual(package.authority_resolution.overall_outcome_classification, "MIXED_WITH_CURRENT_PRIORITY")
        self.assertEqual(package.confidentiality_state.effective_confidentiality_level, "restricted")
        self.assertFalse(package.confidentiality_state.personal_information_present)
        self.assertTrue(package.confidentiality_state.de_identification_required)
        self.assertEqual(package.confidentiality_state.personal_information_status_summary, "no")
        self.assertEqual(package.confidentiality_state.suppressed_item_ids, ())
        self.assertEqual(len(package.grounding.references), 3)
        self.assertIn("pi_deidentified", package.generator_policy.required_warnings)
        self.assertIn("historical_context_high_level_only", package.generator_policy.confidentiality_restrictions)
        self.assertIn("de_identify_before_generation", package.generator_policy.personal_information_restrictions)
        self.assertIsNotNone(package.generator_safe_context)
        historical_projection = next(
            projection
            for projection in package.generator_safe_context.projections
            if projection.item_id == "p6-precedent"
        )
        self.assertEqual(historical_projection.visibility, "de_identified")

        serialized = json.loads(package.to_json())
        self.assertEqual(serialized["routing_plan"]["query_text"], question)
        self.assertEqual(serialized["phase_6_context"][0]["item_id"], "p6-precedent")
        self.assertEqual(serialized["grounding"]["references"][2]["item_id"], "p6-precedent")

    def test_degraded_layer_state_survives_into_context_package(self) -> None:
        question = "If Phase 5 retrieval is unavailable but a payment explanation is requested, what can still be answered?"
        plan = QueryPlan(
            query_text=question,
            query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
            routing_confidence=ROUTING_CONFIDENCE_HIGH,
            required_layers=(LAYER_ID_PHASE_4, LAYER_ID_PHASE_5),
            phase_4=Phase4RoutingIntent(required=True, domains=("payment",)),
            phase_5=Phase5RoutingIntent(required=True, needs_guidance=True, query_text=question),
        )
        p4_item = make_item(
            item_id="p4-payment",
            source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
            primary_code="PAYMENT_CONFIRMATION_MINIMUM_30_PERCENT",
            primary_id=4,
            reasoning_state="resolved",
            layer_payload={"phase_4_domain": "payment"},
        )
        package = build_context_package(
            question,
            planner_fn=lambda *_args, **_kwargs: plan,
            phase4_executor=lambda *_args, **_kwargs: make_record(LAYER_ID_PHASE_4, items=(p4_item,), reasoning_state="resolved"),
            phase5_executor=lambda *_args, **_kwargs: make_record(
                LAYER_ID_PHASE_5,
                execution_state=EXECUTION_STATE_UNAVAILABLE,
            ),
            phase6_executor=lambda *_args, **_kwargs: make_record(
                LAYER_ID_PHASE_6,
                requested=False,
                execution_state=EXECUTION_STATE_NOT_REQUESTED,
            ),
        )
        self.assertTrue(package.degraded_retrieval_state.any_degradation)
        self.assertIn(LAYER_ID_PHASE_5, package.degraded_retrieval_state.affected_layers)
        self.assertIn("current_guidance_unavailable", package.degraded_retrieval_state.generator_warnings)
        self.assertTrue(any(conflict.conflict_type_code == "TYPE_E_P5_FAILURE_P4_SURVIVES" for conflict in package.authority_resolution.conflict_records))

    def test_source_generation_restriction_blocks_generator_when_material_context_is_suppressed(self) -> None:
        question = "What should we say from this blocked source?"
        plan = QueryPlan(
            query_text=question,
            query_class=QUERY_CLASS_MIXED_CURRENT_AND_PRECEDENT,
            routing_confidence=ROUTING_CONFIDENCE_HIGH,
            required_layers=(LAYER_ID_PHASE_5,),
            phase_5=Phase5RoutingIntent(required=True, needs_guidance=True, query_text=question),
        )
        blocked_item = make_item(
            item_id="p5-blocked",
            source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
            primary_code="SERV-BLOCKED",
            primary_id=77,
            reasoning_state=None,
            sensitivity=SensitivityEnvelope(
                confidentiality_level="restricted",
                personal_information_status="no",
                de_identification_required=False,
                generation_allowed=False,
                generation_restriction_reason="source_generation_prohibited",
                native_sensitivity_payload={},
            ),
        )

        package = build_context_package(
            question,
            planner_fn=lambda *_args, **_kwargs: plan,
            phase4_executor=lambda *_args, **_kwargs: make_record(
                LAYER_ID_PHASE_4,
                requested=False,
                execution_state=EXECUTION_STATE_NOT_REQUESTED,
            ),
            phase5_executor=lambda *_args, **_kwargs: make_record(LAYER_ID_PHASE_5, items=(blocked_item,)),
            phase6_executor=lambda *_args, **_kwargs: make_record(
                LAYER_ID_PHASE_6,
                requested=False,
                execution_state=EXECUTION_STATE_NOT_REQUESTED,
            ),
        )

        self.assertFalse(package.confidentiality_state.generation_allowed)
        self.assertEqual(
            package.confidentiality_state.generation_restriction_reason,
            "material_context_source_generation_restricted",
        )
        self.assertEqual(package.confidentiality_state.suppressed_item_ids, ("p5-blocked",))
        self.assertFalse(package.generator_policy.generation_allowed)
        self.assertEqual(package.generator_policy.allowed_actions, ())
        self.assertIn(
            "generation_block_reason:material_context_source_generation_restricted",
            package.generator_policy.confidentiality_restrictions,
        )


if __name__ == "__main__":
    unittest.main()
