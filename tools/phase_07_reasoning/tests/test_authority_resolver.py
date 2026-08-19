from __future__ import annotations

import unittest

from tools.phase_07_reasoning.authority_resolver import resolve_authority
from tools.phase_07_reasoning.contracts import (
    EXECUTION_STATE_FAILED,
    EXECUTION_STATE_NOT_REQUESTED,
    EXECUTION_STATE_SUCCESS,
    EXECUTION_STATE_UNAVAILABLE,
    LAYER_ID_PHASE_4,
    LAYER_ID_PHASE_5,
    LAYER_ID_PHASE_6,
    QUERY_CLASS_AUTHORITY_VERIFICATION,
    QUERY_CLASS_CURRENT_GUIDANCE,
    QUERY_CLASS_DETERMINISTIC_CURRENT,
    QUERY_CLASS_MIXED_CURRENT_AND_PRECEDENT,
    QUERY_CLASS_PRECEDENT_DISCOVERY,
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


def make_item(
    *,
    item_id: str,
    source_layer_role: str,
    primary_code: str,
    primary_id: int,
    reasoning_state: str | None,
    layer_payload: dict | None = None,
) -> NormalizedResultEnvelope:
    sensitivity = (
        phase4_default_sensitivity()
        if source_layer_role == SOURCE_LAYER_ROLE_DETERMINISTIC_RULE
        else SensitivityEnvelope(
            confidentiality_level="restricted",
            personal_information_status="yes",
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
        sensitivity=sensitivity,
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


class AuthorityResolverTests(unittest.TestCase):
    def test_p4_only_resolved_query_returns_deterministic_current(self) -> None:
        plan = QueryPlan(
            query_text="What minimum payment confirms a booking right now?",
            query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
            routing_confidence=ROUTING_CONFIDENCE_HIGH,
            required_layers=(LAYER_ID_PHASE_4,),
            phase_4=Phase4RoutingIntent(required=True, domains=("payment",)),
        )
        p4_item = make_item(
            item_id="p4-payment",
            source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
            primary_code="PAYMENT_CONFIRMATION_MINIMUM_30_PERCENT",
            primary_id=1,
            reasoning_state="resolved",
            layer_payload={"phase_4_domain": "payment"},
        )
        resolution = resolve_authority(
            plan,
            make_record(LAYER_ID_PHASE_4, items=(p4_item,), reasoning_state="resolved"),
            make_record(LAYER_ID_PHASE_5, requested=False, execution_state=EXECUTION_STATE_NOT_REQUESTED),
            make_record(LAYER_ID_PHASE_6, requested=False, execution_state=EXECUTION_STATE_NOT_REQUESTED),
        )
        self.assertEqual(resolution.overall_outcome_classification, "DETERMINISTIC_CURRENT")
        self.assertEqual(resolution.resolved_current_truth_item_ids, ("p4-payment",))

    def test_p5_only_guidance_query_returns_current_guidance(self) -> None:
        question = "How should staff schedule and confirm a site visit?"
        plan = QueryPlan(
            query_text=question,
            query_class=QUERY_CLASS_CURRENT_GUIDANCE,
            routing_confidence=ROUTING_CONFIDENCE_HIGH,
            required_layers=(LAYER_ID_PHASE_5,),
            phase_5=Phase5RoutingIntent(required=True, needs_guidance=True, query_text=question),
        )
        p5_item = make_item(
            item_id="p5-site",
            source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
            primary_code="TPL-008",
            primary_id=8,
            reasoning_state=None,
        )
        resolution = resolve_authority(
            plan,
            make_record(LAYER_ID_PHASE_4, requested=False, execution_state=EXECUTION_STATE_NOT_REQUESTED),
            make_record(LAYER_ID_PHASE_5, items=(p5_item,)),
            make_record(LAYER_ID_PHASE_6, requested=False, execution_state=EXECUTION_STATE_NOT_REQUESTED),
        )
        self.assertEqual(resolution.overall_outcome_classification, "CURRENT_GUIDANCE")
        self.assertEqual(resolution.current_guidance_item_ids, ("p5-site",))

    def test_p6_only_precedent_query_returns_historical_precedent(self) -> None:
        question = "Have we handled a multi-day venue takeover before?"
        plan = QueryPlan(
            query_text=question,
            query_class=QUERY_CLASS_PRECEDENT_DISCOVERY,
            routing_confidence=ROUTING_CONFIDENCE_HIGH,
            required_layers=(LAYER_ID_PHASE_6,),
            phase_6=Phase6RoutingIntent(required=True, query_text=question),
        )
        p6_item = make_item(
            item_id="p6-hc1",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HC-001",
            primary_id=1,
            reasoning_state=None,
            layer_payload={"precedent_availability": "active"},
        )
        resolution = resolve_authority(
            plan,
            make_record(LAYER_ID_PHASE_4, requested=False, execution_state=EXECUTION_STATE_NOT_REQUESTED),
            make_record(LAYER_ID_PHASE_5, requested=False, execution_state=EXECUTION_STATE_NOT_REQUESTED),
            make_record(LAYER_ID_PHASE_6, items=(p6_item,)),
        )
        self.assertEqual(resolution.overall_outcome_classification, "HISTORICAL_PRECEDENT")
        self.assertEqual(resolution.historical_precedent_item_ids, ("p6-hc1",))

    def test_confirmation_bound_phase4_result_controls_overall_outcome(self) -> None:
        question = "Can WNC source a facilitator, and what should we tell the client about confirmation?"
        plan = QueryPlan(
            query_text=question,
            query_class=QUERY_CLASS_CURRENT_GUIDANCE,
            routing_confidence=ROUTING_CONFIDENCE_HIGH,
            required_layers=(LAYER_ID_PHASE_4, LAYER_ID_PHASE_5),
            phase_4=Phase4RoutingIntent(required=True, domains=("facilitator_requirements",)),
            phase_5=Phase5RoutingIntent(required=True, needs_guidance=True, query_text=question),
        )
        p4_item = make_item(
            item_id="p4-facilitator",
            source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
            primary_code="FACILITATOR_WNC_PROVIDED_CONFIRMATION_REQUIRED",
            primary_id=10,
            reasoning_state="requires_confirmation",
            layer_payload={"phase_4_domain": "facilitator_requirements"},
        )
        resolution = resolve_authority(
            plan,
            make_record(LAYER_ID_PHASE_4, items=(p4_item,), reasoning_state="requires_confirmation"),
            make_record(LAYER_ID_PHASE_5, items=(
                make_item(
                    item_id="p5-facilitator",
                    source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
                    primary_code="SERV-001",
                    primary_id=11,
                    reasoning_state=None,
                ),
            )),
            make_record(LAYER_ID_PHASE_6, requested=False, execution_state=EXECUTION_STATE_NOT_REQUESTED),
        )
        self.assertEqual(resolution.overall_outcome_classification, "REQUIRES_CONFIRMATION")
        self.assertTrue(any(record.requires_confirmation for record in resolution.unresolved_authority_records))
        self.assertTrue(any(conflict.conflict_type_code == "TYPE_D_P4_REQUIRES_CONFIRMATION" for conflict in resolution.conflict_records))

    def test_historical_gap_filling_is_blocked_when_current_authority_is_missing(self) -> None:
        question = "WineGB paid EUR 300 for storage. Can I quote EUR 300 to this client now?"
        plan = QueryPlan(
            query_text=question,
            query_class=QUERY_CLASS_UNRESOLVED_AUTHORITY,
            routing_confidence=ROUTING_CONFIDENCE_HIGH,
            required_layers=(LAYER_ID_PHASE_5, LAYER_ID_PHASE_6),
            phase_5=Phase5RoutingIntent(required=True, needs_guidance=True, query_text=question),
            phase_6=Phase6RoutingIntent(required=True, query_text=question),
        )
        p6_item = make_item(
            item_id="p6-storage",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HC-003",
            primary_id=3,
            reasoning_state=None,
            layer_payload={
                "historical_value_only": True,
                "precedent_availability": "limited",
                "current_authority_disposition": "current_status_unknown",
            },
        )
        resolution = resolve_authority(
            plan,
            make_record(LAYER_ID_PHASE_4, requested=False, execution_state=EXECUTION_STATE_NOT_REQUESTED),
            make_record(LAYER_ID_PHASE_5, items=()),
            make_record(LAYER_ID_PHASE_6, items=(p6_item,)),
        )
        self.assertEqual(resolution.overall_outcome_classification, "INSUFFICIENT_CURRENT_AUTHORITY")
        self.assertTrue(any(conflict.conflict_type_code == "TYPE_C_P6_EXISTS_BUT_CURRENT_MISSING" for conflict in resolution.conflict_records))
        self.assertTrue(any(annotation.forbidden_inference_type == "historical_price_to_current_price" for annotation in resolution.contamination_annotations))

    def test_phase4_beats_phase6_conflict_is_emitted_for_current_access_claim(self) -> None:
        question = "Historical storage and clearing used extra rooms. Does that mean Back Office or Storage Room access is allowed now?"
        plan = QueryPlan(
            query_text=question,
            query_class=QUERY_CLASS_AUTHORITY_VERIFICATION,
            routing_confidence=ROUTING_CONFIDENCE_HIGH,
            required_layers=(LAYER_ID_PHASE_4, LAYER_ID_PHASE_6),
            phase_4=Phase4RoutingIntent(required=True, domains=("space_access",)),
            phase_6=Phase6RoutingIntent(required=True, query_text=question),
        )
        p4_item = make_item(
            item_id="p4-access",
            source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
            primary_code="ACCESS_STUDIO_BACK_OFFICE_RESTRICTED",
            primary_id=31,
            reasoning_state="resolved",
            layer_payload={"phase_4_domain": "space_access"},
        )
        p6_item = make_item(
            item_id="p6-access",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HC-001",
            primary_id=1,
            reasoning_state=None,
            layer_payload={"precedent_availability": "active"},
        )
        resolution = resolve_authority(
            plan,
            make_record(LAYER_ID_PHASE_4, items=(p4_item,), reasoning_state="resolved"),
            make_record(LAYER_ID_PHASE_5, requested=False, execution_state=EXECUTION_STATE_NOT_REQUESTED),
            make_record(LAYER_ID_PHASE_6, items=(p6_item,)),
        )
        self.assertEqual(resolution.overall_outcome_classification, "DETERMINISTIC_CURRENT")
        self.assertTrue(any(conflict.conflict_type_code == "TYPE_A_P4_BEATS_P6" for conflict in resolution.conflict_records))
        self.assertTrue(any(annotation.forbidden_inference_type == "historical_room_use_to_current_access_right" for annotation in resolution.contamination_annotations))

    def test_space_access_restriction_counts_as_current_truth_without_confirmation_stop(self) -> None:
        question = "Historical storage and clearing used extra rooms. Does that mean Back Office or Storage Room access is allowed now?"
        plan = QueryPlan(
            query_text=question,
            query_class=QUERY_CLASS_AUTHORITY_VERIFICATION,
            routing_confidence=ROUTING_CONFIDENCE_HIGH,
            required_layers=(LAYER_ID_PHASE_4, LAYER_ID_PHASE_6),
            phase_4=Phase4RoutingIntent(required=True, domains=("space_access",)),
            phase_6=Phase6RoutingIntent(required=True, query_text=question),
        )
        p4_item = make_item(
            item_id="p4-access-restricted",
            source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
            primary_code="ACCESS_STUDIO_BACK_OFFICE_RESTRICTED",
            primary_id=33,
            reasoning_state="requires_confirmation",
            layer_payload={
                "phase_4_domain": "space_access",
                "access_status": "restricted",
            },
        )
        p6_item = make_item(
            item_id="p6-access-history",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HC-003",
            primary_id=3,
            reasoning_state=None,
            layer_payload={"precedent_availability": "active"},
        )
        resolution = resolve_authority(
            plan,
            make_record(LAYER_ID_PHASE_4, items=(p4_item,), reasoning_state="requires_confirmation"),
            make_record(LAYER_ID_PHASE_5, requested=False, execution_state=EXECUTION_STATE_NOT_REQUESTED),
            make_record(LAYER_ID_PHASE_6, items=(p6_item,)),
        )
        self.assertEqual(resolution.overall_outcome_classification, "DETERMINISTIC_CURRENT")
        self.assertEqual(resolution.resolved_current_truth_item_ids, ("p4-access-restricted",))
        self.assertFalse(any(conflict.conflict_type_code == "TYPE_D_P4_REQUIRES_CONFIRMATION" for conflict in resolution.conflict_records))
        self.assertTrue(any(conflict.conflict_type_code == "TYPE_A_P4_BEATS_P6" for conflict in resolution.conflict_records))

    def test_phase5_beats_phase6_conflict_is_emitted_for_service_boundary_claim(self) -> None:
        question = "Historical client-operated events existed. Does that override current Supported Rental or Full Production boundaries?"
        plan = QueryPlan(
            query_text=question,
            query_class=QUERY_CLASS_AUTHORITY_VERIFICATION,
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
            primary_id=32,
            reasoning_state="resolved",
            layer_payload={"phase_4_domain": "service_rules"},
        )
        p5_item = make_item(
            item_id="p5-service",
            source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
            primary_code="SERV-001",
            primary_id=101,
            reasoning_state=None,
        )
        p6_item = make_item(
            item_id="p6-service",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HC-006",
            primary_id=6,
            reasoning_state=None,
            layer_payload={"precedent_availability": "active"},
        )
        resolution = resolve_authority(
            plan,
            make_record(LAYER_ID_PHASE_4, items=(p4_item,), reasoning_state="resolved"),
            make_record(LAYER_ID_PHASE_5, items=(p5_item,)),
            make_record(LAYER_ID_PHASE_6, items=(p6_item,)),
        )
        self.assertEqual(resolution.overall_outcome_classification, "MIXED_WITH_CURRENT_PRIORITY")
        self.assertTrue(any(conflict.conflict_type_code == "TYPE_B_P5_BEATS_P6" for conflict in resolution.conflict_records))

    def test_phase5_unavailable_does_not_remove_phase4_truth(self) -> None:
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
            primary_id=38,
            reasoning_state="resolved",
            layer_payload={"phase_4_domain": "payment"},
        )
        resolution = resolve_authority(
            plan,
            make_record(LAYER_ID_PHASE_4, items=(p4_item,), reasoning_state="resolved"),
            make_record(LAYER_ID_PHASE_5, execution_state=EXECUTION_STATE_UNAVAILABLE),
            make_record(LAYER_ID_PHASE_6, requested=False, execution_state=EXECUTION_STATE_NOT_REQUESTED),
        )
        self.assertEqual(resolution.overall_outcome_classification, "DETERMINISTIC_CURRENT")
        self.assertTrue(any(conflict.conflict_type_code == "TYPE_E_P5_FAILURE_P4_SURVIVES" for conflict in resolution.conflict_records))

    def test_limited_or_unknown_precedent_is_preserved_as_conflict_signal(self) -> None:
        question = "Have we handled this before, and what should we do now?"
        plan = QueryPlan(
            query_text=question,
            query_class=QUERY_CLASS_MIXED_CURRENT_AND_PRECEDENT,
            routing_confidence=ROUTING_CONFIDENCE_HIGH,
            required_layers=(LAYER_ID_PHASE_5, LAYER_ID_PHASE_6),
            phase_5=Phase5RoutingIntent(required=True, needs_guidance=True, query_text=question),
            phase_6=Phase6RoutingIntent(required=True, query_text=question),
        )
        p5_item = make_item(
            item_id="p5-guidance",
            source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
            primary_code="SERV-004",
            primary_id=55,
            reasoning_state=None,
        )
        p6_item = make_item(
            item_id="p6-limited",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HC-009",
            primary_id=9,
            reasoning_state=None,
            layer_payload={"precedent_availability": "limited", "current_authority_disposition": "current_status_unknown"},
        )
        resolution = resolve_authority(
            plan,
            make_record(LAYER_ID_PHASE_4, requested=False, execution_state=EXECUTION_STATE_NOT_REQUESTED),
            make_record(LAYER_ID_PHASE_5, items=(p5_item,)),
            make_record(LAYER_ID_PHASE_6, items=(p6_item,)),
        )
        self.assertTrue(any(conflict.conflict_type_code == "TYPE_F_LIMITED_OR_UNKNOWN_PRECEDENT" for conflict in resolution.conflict_records))


if __name__ == "__main__":
    unittest.main()
