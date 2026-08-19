from __future__ import annotations

import unittest

from tools.phase_07_reasoning.contracts import (
    EXECUTION_STATE_SUCCESS,
    LAYER_ID_PHASE_4,
    LAYER_ID_PHASE_5,
    LAYER_ID_PHASE_6,
    PERSONAL_INFORMATION_STATUS_YES,
    QUERY_CLASS_AUTHORITY_VERIFICATION,
    QUERY_CLASS_UNRESOLVED_AUTHORITY,
    ROUTING_CONFIDENCE_HIGH,
    ExactIdentity,
    LayerExecutionRecord,
    NormalizedResultEnvelope,
    Phase4RoutingIntent,
    Phase5RoutingIntent,
    Phase6RoutingIntent,
    ProvenanceEnvelope,
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
from tools.phase_07_reasoning.contamination_gate import detect_contamination_annotations


def make_item(
    *,
    item_id: str,
    source_layer_role: str,
    primary_code: str,
    primary_id: int,
    summary_text: str,
    layer_payload: dict | None = None,
) -> NormalizedResultEnvelope:
    sensitivity = (
        phase4_default_sensitivity()
        if source_layer_role == SOURCE_LAYER_ROLE_DETERMINISTIC_RULE
        else SensitivityEnvelope(
            confidentiality_level="restricted",
            personal_information_status=PERSONAL_INFORMATION_STATUS_YES,
            de_identification_required=True,
            generation_allowed=True,
            generation_restriction_reason=None,
            native_sensitivity_payload={},
        )
    )
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
        reasoning_state="resolved" if source_layer_role == SOURCE_LAYER_ROLE_DETERMINISTIC_RULE else None,
        summary_text=summary_text,
        provenance=ProvenanceEnvelope(
            source_codes=(primary_code,),
            source_identifiers={"primary_code": primary_code},
            primary_source_locator=f"{primary_code} locator",
            additional_locators=(),
            source_link_count=1,
            native_provenance_payload={},
        ),
        sensitivity=sensitivity,
        retrieval=retrieval,
        layer_payload=layer_payload or {},
    )


def make_record(layer_id: str, items: tuple[NormalizedResultEnvelope, ...]) -> LayerExecutionRecord:
    return LayerExecutionRecord(
        layer_id=layer_id,
        requested=True,
        execution_state=EXECUTION_STATE_SUCCESS,
        reasoning_state="resolved" if layer_id == LAYER_ID_PHASE_4 else None,
        fallback_reason=None,
        error_category=None,
        safe_error_message=None,
        result_count=len(items),
        normalized_items=items,
    )


class ContaminationGateTests(unittest.TestCase):
    def test_all_six_forbidden_inference_patterns_are_detected(self) -> None:
        cases = (
            (
                "WineGB paid EUR 300 for storage. Can I quote EUR 300 to this client now?",
                "historical_price_to_current_price",
                {"historical_value_only": True},
            ),
            (
                "Haylin handled florals before. Can I offer floral arrangements now?",
                "historical_person_capability_to_current_service",
                {},
            ),
            (
                "We did not discount for exposure last time. Is that our official discount policy?",
                "historical_concession_to_current_policy",
                {"historical_value_only": True},
            ),
            (
                "We handled ADE permits that way before. Can we do the same this year?",
                "historical_legal_solution_to_current_guidance",
                {},
            ),
            (
                "We charged overtime before. What is our current overtime rate?",
                "historical_overtime_handling_to_current_rate",
                {"historical_value_only": True},
            ),
            (
                "Historical storage and clearing used extra rooms. Does that mean Back Office or Storage Room access is allowed now?",
                "historical_room_use_to_current_access_right",
                {},
            ),
        )

        for index, (question, expected_type, payload) in enumerate(cases, start=1):
            with self.subTest(expected_type=expected_type):
                plan = QueryPlan(
                    query_text=question,
                    query_class=QUERY_CLASS_UNRESOLVED_AUTHORITY,
                    routing_confidence=ROUTING_CONFIDENCE_HIGH,
                    required_layers=(LAYER_ID_PHASE_5, LAYER_ID_PHASE_6),
                    phase_5=Phase5RoutingIntent(required=True, needs_guidance=True, query_text=question),
                    phase_6=Phase6RoutingIntent(required=True, query_text=question),
                )
                p5_record = make_record(
                    LAYER_ID_PHASE_5,
                    (
                        make_item(
                            item_id=f"p5-{index}",
                            source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
                            primary_code="DOC",
                            primary_id=index,
                            summary_text="Current guidance.",
                        ),
                    ),
                )
                p6_record = make_record(
                    LAYER_ID_PHASE_6,
                    (
                        make_item(
                            item_id=f"p6-{index}",
                            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
                            primary_code="HC-001",
                            primary_id=index,
                            summary_text="Historical precedent.",
                            layer_payload=payload,
                        ),
                    ),
                )
                annotations = detect_contamination_annotations(
                    plan,
                    LayerExecutionRecord(layer_id=LAYER_ID_PHASE_4, requested=False, execution_state="not_requested", result_count=0),
                    p5_record,
                    p6_record,
                )
                self.assertEqual(len(annotations), 1)
                self.assertEqual(annotations[0].forbidden_inference_type, expected_type)
                self.assertFalse(annotations[0].prescriptive_use_allowed)

    def test_pure_precedent_query_does_not_trigger_contamination(self) -> None:
        question = "Have we handled an ADE-style permit and compliance issue before?"
        plan = QueryPlan(
            query_text=question,
            query_class="precedent_discovery",
            routing_confidence=ROUTING_CONFIDENCE_HIGH,
            required_layers=(LAYER_ID_PHASE_6,),
            phase_6=Phase6RoutingIntent(required=True, query_text=question),
        )
        p6_record = make_record(
            LAYER_ID_PHASE_6,
            (
                make_item(
                    item_id="p6-1",
                    source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
                    primary_code="HC-009",
                    primary_id=9,
                    summary_text="Historical permit precedent.",
                    layer_payload={"historical_value_only": True},
                ),
            ),
        )
        annotations = detect_contamination_annotations(
            plan,
            LayerExecutionRecord(layer_id=LAYER_ID_PHASE_4, requested=False, execution_state="not_requested", result_count=0),
            LayerExecutionRecord(layer_id=LAYER_ID_PHASE_5, requested=False, execution_state="not_requested", result_count=0),
            p6_record,
        )
        self.assertEqual(annotations, ())

    def test_late_buildup_boundary_question_does_not_trigger_overtime_rate_contamination(self) -> None:
        question = "The build-up may run late. What are the current boundaries, and have we seen this before?"
        plan = QueryPlan(
            query_text=question,
            query_class="mixed_current_and_precedent",
            routing_confidence=ROUTING_CONFIDENCE_HIGH,
            required_layers=(LAYER_ID_PHASE_4, LAYER_ID_PHASE_5, LAYER_ID_PHASE_6),
            phase_4=Phase4RoutingIntent(required=True, domains=("operational_requirements",)),
            phase_5=Phase5RoutingIntent(required=True, needs_guidance=True, query_text=question),
            phase_6=Phase6RoutingIntent(required=True, query_text=question),
        )
        p4_record = make_record(
            LAYER_ID_PHASE_4,
            (
                make_item(
                    item_id="p4-setup",
                    source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
                    primary_code="OPER_SETUP_START_AT_BOOKED_TIME",
                    primary_id=22,
                    summary_text="Setup begins at the booked start time.",
                    layer_payload={"phase_4_domain": "operational_requirements"},
                ),
            ),
        )
        p5_record = make_record(
            LAYER_ID_PHASE_5,
            (
                make_item(
                    item_id="p5-handover",
                    source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
                    primary_code="CF-005",
                    primary_id=5,
                    summary_text="Current handover guidance.",
                ),
            ),
        )
        p6_record = make_record(
            LAYER_ID_PHASE_6,
            (
                make_item(
                    item_id="p6-late-build",
                    source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
                    primary_code="HC-006",
                    primary_id=6,
                    summary_text="Historical late build-up risk.",
                    layer_payload={"historical_value_only": True},
                ),
            ),
        )
        annotations = detect_contamination_annotations(
            plan,
            p4_record,
            p5_record,
            p6_record,
        )
        self.assertEqual(annotations, ())


if __name__ == "__main__":
    unittest.main()
