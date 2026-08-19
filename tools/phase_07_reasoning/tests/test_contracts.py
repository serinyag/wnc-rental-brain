from __future__ import annotations

import json
import unittest

from tools.phase_07_reasoning.contracts import (
    ANSWER_MODE_BLOCKED,
    ANSWER_RESULT_STATUS_BLOCKED,
    ANSWER_RESULT_STATUS_COMPLETED,
    AUTHORITY_OUTCOME_CURRENT_GUIDANCE,
    AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
    AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
    AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY,
    AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION,
    CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE,
    CONFIDENTIALITY_LEVEL_INTERNAL,
    CONFIDENTIALITY_LEVEL_RESTRICTED,
    CONFLICT_TYPE_A_P4_BEATS_P6,
    CONTAMINATION_ACTION_CONTEXT_ONLY,
    CONTAMINATION_ACTION_UNRESOLVED,
    EXECUTION_STATE_FAILED,
    EXECUTION_STATE_FALLBACK,
    EXECUTION_STATE_NOT_REQUESTED,
    EXECUTION_STATE_SUCCESS,
    FORBIDDEN_INFERENCE_HISTORICAL_PRICE_TO_CURRENT_PRICE,
    GENERATOR_ALLOWED_ACTION_COMPARE,
    GENERATOR_ALLOWED_ACTION_EXPLAIN,
    GENERATOR_ALLOWED_ACTION_EXPRESS_UNCERTAINTY,
    GENERATOR_ALLOWED_ACTION_SYNTHESIZE,
    GENERATION_BOUNDARY_INTERNAL,
    GENERATION_DECISION_ALLOWED,
    GENERATION_DECISION_BLOCKED,
    GENERATOR_FORBIDDEN_ACTION_ERASE_CONFIRMATION_REQUIREMENTS,
    GENERATOR_FORBIDDEN_ACTION_FILL_AUTHORITY_GAPS,
    GENERATOR_FORBIDDEN_ACTION_INDEPENDENT_RETRIEVAL,
    GENERATOR_FORBIDDEN_ACTION_INVENT_DETERMINISTIC_VALUES,
    GENERATOR_FORBIDDEN_ACTION_OVERRIDE_CONFLICTS,
    GENERATOR_FORBIDDEN_ACTION_PROMOTE_PRECEDENT,
    LAYER_ID_PHASE_4,
    LAYER_ID_PHASE_5,
    LAYER_ID_PHASE_6,
    PERSONAL_INFORMATION_STATUS_NO,
    PERSONAL_INFORMATION_STATUS_UNKNOWN,
    PERSONAL_INFORMATION_STATUS_YES,
    PHASE_4_DOMAIN_CAPACITY,
    PHASE_4_DOMAIN_CATERING_SUPPLIER,
    PHASE_4_DOMAIN_PAYMENT,
    PHASE_4_DOMAIN_TECHNICAL_CAPABILITY,
    PHASE_7_CONTEXT_CONTRACT_VERSION,
    QUERY_CLASS_AUTHORITY_VERIFICATION,
    QUERY_CLASS_CURRENT_GUIDANCE,
    QUERY_CLASS_DETERMINISTIC_CURRENT,
    QUERY_CLASS_MIXED_CURRENT_AND_PRECEDENT,
    QUERY_CLASS_PRECEDENT_DISCOVERY,
    QUERY_CLASS_UNRESOLVED_AUTHORITY,
    REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
    REASONING_STATE_NO_APPLICABLE_RULE,
    REASONING_STATE_REQUIRES_CONFIRMATION,
    REASONING_STATE_RESOLVED,
    ROUTING_CONFIDENCE_HIGH,
    ROUTING_CONFIDENCE_LOW,
    ROUTING_CONFIDENCE_MEDIUM,
    SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
    SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
    SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
    AnswerClaimFrame,
    AnswerGenerationInput,
    AnswerResult,
    AnswerValidationResult,
    AuthorityResolution,
    ConfidentialityState,
    ContextPackage,
    ContaminationAnnotation,
    ConflictRecord,
    DegradedRetrievalState,
    ExactIdentity,
    GeneratorPolicy,
    GroundingReference,
    GroundingState,
    LayerExecutionRecord,
    NormalizedResultEnvelope,
    Phase4RoutingIntent,
    Phase5FilterIntent,
    Phase5RoutingIntent,
    Phase6FilterIntent,
    Phase6RoutingIntent,
    Phase7ContractError,
    Phase7RuntimeConfiguration,
    ProvenanceEnvelope,
    QueryContext,
    QueryPlan,
    RetrievalMetadata,
    SensitivityEnvelope,
    StableIdentity,
    UncertaintyState,
    UnresolvedAuthorityRecord,
    authority_priority_for_tier,
    authority_tier_for_source_role,
    phase4_default_sensitivity,
)


def make_provenance(*, code: str, locator: str) -> ProvenanceEnvelope:
    return ProvenanceEnvelope(
        source_codes=(code,),
        source_identifiers={"primary_code": code},
        primary_source_locator=locator,
        additional_locators=(),
        source_link_count=1,
        native_provenance_payload={},
    )


def make_retrieval(*, rank: int = 1, score: float = 1.0) -> RetrievalMetadata:
    return RetrievalMetadata(
        retrieval_mode_requested="hybrid",
        retrieval_mode_used="hybrid",
        fallback_used=False,
        fallback_reason=None,
        rank=rank,
        score=score,
        component_scores={"final_score": score},
        strategy_code="fixture_strategy",
        native_retrieval_payload={},
    )


def make_item(
    *,
    item_id: str,
    source_layer_role: str,
    primary_code: str,
    primary_id: int,
    summary_text: str,
    reasoning_state: str | None = REASONING_STATE_RESOLVED,
    sensitivity: SensitivityEnvelope | None = None,
    retrieval: RetrievalMetadata | None = None,
    layer_payload: dict | None = None,
) -> NormalizedResultEnvelope:
    return NormalizedResultEnvelope(
        item_id=item_id,
        source_layer_role=source_layer_role,
        authority_tier_code=authority_tier_for_source_role(source_layer_role),
        authority_priority=authority_priority_for_tier(authority_tier_for_source_role(source_layer_role)),
        stable_identity=StableIdentity(primary_code=primary_code),
        exact_identity=ExactIdentity(primary_id=primary_id, version_id=primary_id, version_number=1),
        content_kind="fixture_item",
        execution_state=EXECUTION_STATE_SUCCESS,
        reasoning_state=reasoning_state,
        summary_text=summary_text,
        provenance=make_provenance(code=primary_code, locator=f"{primary_code} locator"),
        sensitivity=sensitivity or phase4_default_sensitivity(),
        retrieval=retrieval,
        layer_payload=layer_payload or {"code": primary_code},
    )


def make_not_requested(layer_id: str) -> LayerExecutionRecord:
    return LayerExecutionRecord(
        layer_id=layer_id,
        requested=False,
        execution_state=EXECUTION_STATE_NOT_REQUESTED,
        reasoning_state=None,
        fallback_reason=None,
        error_category=None,
        safe_error_message=None,
        result_count=0,
        normalized_items=(),
    )


def default_generator_policy(*, generation_allowed: bool = True) -> GeneratorPolicy:
    return GeneratorPolicy(
        generation_allowed=generation_allowed,
        allowed_actions=(
            GENERATOR_ALLOWED_ACTION_SYNTHESIZE,
            GENERATOR_ALLOWED_ACTION_EXPLAIN,
            GENERATOR_ALLOWED_ACTION_COMPARE,
            GENERATOR_ALLOWED_ACTION_EXPRESS_UNCERTAINTY,
        ),
        forbidden_actions=(
            GENERATOR_FORBIDDEN_ACTION_INDEPENDENT_RETRIEVAL,
            GENERATOR_FORBIDDEN_ACTION_INVENT_DETERMINISTIC_VALUES,
            GENERATOR_FORBIDDEN_ACTION_PROMOTE_PRECEDENT,
            GENERATOR_FORBIDDEN_ACTION_OVERRIDE_CONFLICTS,
            GENERATOR_FORBIDDEN_ACTION_ERASE_CONFIRMATION_REQUIREMENTS,
            GENERATOR_FORBIDDEN_ACTION_FILL_AUTHORITY_GAPS,
        ),
        required_warnings=(),
        confidentiality_restrictions=(),
        personal_information_restrictions=(),
    )


class Phase7ContractsTests(unittest.TestCase):
    def test_source_role_authority_priority_matches_are_accepted(self) -> None:
        item = make_item(
            item_id="p4-item",
            source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
            primary_code="PAYMENT_CONFIRMATION_MINIMUM_30_PERCENT",
            primary_id=1,
            summary_text="Current confirmation payment rule.",
        )
        self.assertEqual(item.authority_tier_code, "current_deterministic")
        self.assertEqual(item.authority_priority, 1)

    def test_source_role_authority_priority_mismatches_are_rejected(self) -> None:
        with self.assertRaisesRegex(Phase7ContractError, "must map to authority_tier_code=current_deterministic"):
            NormalizedResultEnvelope(
                item_id="bad-item",
                source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
                authority_tier_code="historical_precedent",
                authority_priority=3,
                stable_identity=StableIdentity(primary_code="RULE"),
                exact_identity=ExactIdentity(primary_id=1),
                content_kind="fixture_item",
                execution_state=EXECUTION_STATE_SUCCESS,
                reasoning_state=REASONING_STATE_RESOLVED,
                summary_text="bad",
                provenance=make_provenance(code="RULE", locator="locator"),
                sensitivity=phase4_default_sensitivity(),
                retrieval=None,
                layer_payload={},
            )

    def test_invalid_controlled_vocabulary_values_are_rejected(self) -> None:
        with self.assertRaisesRegex(Phase7ContractError, "query_class must be one of"):
            QueryPlan(
                query_text="Bad query class",
                query_class="bad_query_class",
                routing_confidence=ROUTING_CONFIDENCE_HIGH,
            )
        with self.assertRaisesRegex(Phase7ContractError, "conflict_type_code must be one of"):
            ConflictRecord(
                conflict_type_code="TYPE_Z_UNKNOWN",
                controlling_layer=LAYER_ID_PHASE_4,
                affected_item_ids=("p4-item",),
                severity="low",
                resolution_action="ignore",
            )
        with self.assertRaisesRegex(Phase7ContractError, "execution_state must be one of"):
            LayerExecutionRecord(
                layer_id=LAYER_ID_PHASE_4,
                requested=True,
                execution_state="bad_state",
                result_count=0,
                normalized_items=(),
            )

    def test_query_plan_supports_p4_only_plan_for_p7_eval_001(self) -> None:
        plan = QueryPlan(
            query_text="What minimum payment confirms a booking right now?",
            query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
            routing_confidence=ROUTING_CONFIDENCE_HIGH,
            required_layers=(LAYER_ID_PHASE_4,),
            optional_layers=(),
            phase_4=Phase4RoutingIntent(required=True, domains=(PHASE_4_DOMAIN_PAYMENT,), reason_codes=("current_payment_claim",)),
            phase_5=None,
            phase_6=None,
            ambiguity_flags=(),
            safety_overrides=("force_phase_4_for_current_claim",),
            reason_codes=("p7_eval_001_fixture",),
        )
        self.assertEqual(plan.required_layers, (LAYER_ID_PHASE_4,))

    def test_query_plan_supports_p5_only_and_p6_only_and_mixed_plans(self) -> None:
        p5_only = QueryPlan(
            query_text="How should staff schedule and confirm a site visit?",
            query_class=QUERY_CLASS_CURRENT_GUIDANCE,
            routing_confidence=ROUTING_CONFIDENCE_HIGH,
            required_layers=(LAYER_ID_PHASE_5,),
            phase_5=Phase5RoutingIntent(
                required=True,
                needs_guidance=True,
                query_text="How should staff schedule and confirm a site visit?",
                result_limit=5,
                filters=Phase5FilterIntent(document_code="TPL-008"),
                reason_codes=("site_visit_process",),
            ),
        )
        p6_only = QueryPlan(
            query_text="Have we handled competitor branding before?",
            query_class=QUERY_CLASS_PRECEDENT_DISCOVERY,
            routing_confidence=ROUTING_CONFIDENCE_MEDIUM,
            required_layers=(LAYER_ID_PHASE_6,),
            phase_6=Phase6RoutingIntent(
                required=True,
                query_text="Have we handled competitor branding before?",
                result_limit=5,
                filters=Phase6FilterIntent(case_code="HC-008"),
                reason_codes=("precedent_only",),
            ),
        )
        mixed = QueryPlan(
            query_text="A beauty brand wants strong-smell catering. Have we dealt with this before, and what should we do now?",
            query_class=QUERY_CLASS_MIXED_CURRENT_AND_PRECEDENT,
            routing_confidence=ROUTING_CONFIDENCE_MEDIUM,
            required_layers=(LAYER_ID_PHASE_4, LAYER_ID_PHASE_5, LAYER_ID_PHASE_6),
            phase_4=Phase4RoutingIntent(required=True, domains=(PHASE_4_DOMAIN_CATERING_SUPPLIER,), reason_codes=("current_supplier_constraints",)),
            phase_5=Phase5RoutingIntent(required=True, needs_guidance=True, query_text="strong smell catering current guidance", result_limit=5),
            phase_6=Phase6RoutingIntent(required=True, query_text="strong catering smell historical precedent", result_limit=5),
            safety_overrides=("historical_reference_requires_current_authority_before_prescriptive_answer",),
        )
        self.assertEqual(p5_only.required_layers, (LAYER_ID_PHASE_5,))
        self.assertEqual(p6_only.required_layers, (LAYER_ID_PHASE_6,))
        self.assertEqual(mixed.required_layers, (LAYER_ID_PHASE_4, LAYER_ID_PHASE_5, LAYER_ID_PHASE_6))

    def test_query_plan_supports_unresolved_authority_fixture_and_rejects_missing_required_subsection(self) -> None:
        unresolved = QueryPlan(
            query_text="What is the official security deposit for this custom-scope rental?",
            query_class=QUERY_CLASS_UNRESOLVED_AUTHORITY,
            routing_confidence=ROUTING_CONFIDENCE_LOW,
            required_layers=(LAYER_ID_PHASE_4, LAYER_ID_PHASE_5),
            phase_4=Phase4RoutingIntent(required=True, domains=(PHASE_4_DOMAIN_PAYMENT,), reason_codes=("current_authority_check",)),
            phase_5=Phase5RoutingIntent(required=True, needs_guidance=True, query_text="security deposit custom scope", result_limit=5),
        )
        self.assertEqual(unresolved.query_class, QUERY_CLASS_UNRESOLVED_AUTHORITY)
        with self.assertRaisesRegex(Phase7ContractError, "routing subsection is missing"):
            QueryPlan(
                query_text="Bad plan",
                query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
                routing_confidence=ROUTING_CONFIDENCE_HIGH,
                required_layers=(LAYER_ID_PHASE_4,),
            )

    def test_envelope_accepts_phase4_phase5_and_phase6_shapes(self) -> None:
        phase4_item = make_item(
            item_id="phase4-payment",
            source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
            primary_code="PAYMENT_CONFIRMATION_MINIMUM_30_PERCENT",
            primary_id=1,
            summary_text="Current rule",
            retrieval=None,
        )
        phase5_item = make_item(
            item_id="phase5-guidance",
            source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
            primary_code="TPL-008",
            primary_id=2,
            summary_text="Current site visit guidance",
            sensitivity=SensitivityEnvelope(
                confidentiality_level=CONFIDENTIALITY_LEVEL_INTERNAL,
                personal_information_status=PERSONAL_INFORMATION_STATUS_NO,
                de_identification_required=False,
                generation_allowed=True,
            ),
            retrieval=make_retrieval(),
        )
        phase6_item = make_item(
            item_id="phase6-precedent",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HC-008",
            primary_id=3,
            summary_text="Historical branding precedent",
            sensitivity=SensitivityEnvelope(
                confidentiality_level=CONFIDENTIALITY_LEVEL_RESTRICTED,
                personal_information_status=PERSONAL_INFORMATION_STATUS_UNKNOWN,
                de_identification_required=True,
                generation_allowed=True,
            ),
            retrieval=make_retrieval(),
        )
        self.assertIsNone(phase4_item.retrieval)
        self.assertEqual(phase5_item.retrieval.rank, 1)
        self.assertEqual(phase6_item.sensitivity.confidentiality_level, CONFIDENTIALITY_LEVEL_RESTRICTED)

    def test_execution_and_reasoning_state_combinations_are_representable(self) -> None:
        success_resolved = LayerExecutionRecord(
            layer_id=LAYER_ID_PHASE_4,
            requested=True,
            execution_state=EXECUTION_STATE_SUCCESS,
            reasoning_state=REASONING_STATE_RESOLVED,
            result_count=1,
            normalized_items=(
                make_item(
                    item_id="resolved-item",
                    source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
                    primary_code="CAPACITY_RULE",
                    primary_id=4,
                    summary_text="Resolved capacity",
                ),
            ),
        )
        success_confirmation = LayerExecutionRecord(
            layer_id=LAYER_ID_PHASE_4,
            requested=True,
            execution_state=EXECUTION_STATE_SUCCESS,
            reasoning_state=REASONING_STATE_REQUIRES_CONFIRMATION,
            result_count=1,
            normalized_items=(
                make_item(
                    item_id="confirm-item",
                    source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
                    primary_code="TECH_REQ_CUSTOM_TECH_CONFIRM",
                    primary_id=5,
                    summary_text="Requires confirmation",
                    reasoning_state=REASONING_STATE_REQUIRES_CONFIRMATION,
                ),
            ),
        )
        success_no_rule = LayerExecutionRecord(
            layer_id=LAYER_ID_PHASE_4,
            requested=True,
            execution_state=EXECUTION_STATE_SUCCESS,
            reasoning_state=REASONING_STATE_NO_APPLICABLE_RULE,
            result_count=1,
            normalized_items=(
                make_item(
                    item_id="no-rule-item",
                    source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
                    primary_code="NO_RULE",
                    primary_id=6,
                    summary_text="No applicable rule",
                    reasoning_state=REASONING_STATE_NO_APPLICABLE_RULE,
                ),
            ),
        )
        fallback_no_reasoning = LayerExecutionRecord(
            layer_id=LAYER_ID_PHASE_5,
            requested=True,
            execution_state=EXECUTION_STATE_FALLBACK,
            reasoning_state=None,
            fallback_reason="hybrid_unavailable",
            result_count=1,
            normalized_items=(
                make_item(
                    item_id="fallback-guidance",
                    source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
                    primary_code="CF-007",
                    primary_id=7,
                    summary_text="Fallback guidance result",
                    reasoning_state=None,
                    sensitivity=SensitivityEnvelope(
                        confidentiality_level=CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE,
                        personal_information_status=PERSONAL_INFORMATION_STATUS_NO,
                        de_identification_required=False,
                        generation_allowed=True,
                    ),
                    retrieval=RetrievalMetadata(
                        retrieval_mode_requested="hybrid",
                        retrieval_mode_used="fts_fallback",
                        fallback_used=True,
                        fallback_reason="hybrid_unavailable",
                        strategy_code="fixture",
                    ),
                ),
            ),
        )
        self.assertEqual(success_resolved.reasoning_state, REASONING_STATE_RESOLVED)
        self.assertEqual(success_confirmation.reasoning_state, REASONING_STATE_REQUIRES_CONFIRMATION)
        self.assertEqual(success_no_rule.reasoning_state, REASONING_STATE_NO_APPLICABLE_RULE)
        self.assertIsNone(fallback_no_reasoning.reasoning_state)

        with self.assertRaisesRegex(Phase7ContractError, "must not contain normalized items"):
            LayerExecutionRecord(
                layer_id=LAYER_ID_PHASE_4,
                requested=True,
                execution_state=EXECUTION_STATE_FAILED,
                reasoning_state=None,
                result_count=1,
                normalized_items=(success_resolved.normalized_items[0],),
            )

    def test_non_degraded_state_rejects_degraded_metadata(self) -> None:
        with self.assertRaisesRegex(Phase7ContractError, "non-degraded state must not include degraded-layer metadata"):
            DegradedRetrievalState(
                any_degradation=False,
                per_layer_execution_states={LAYER_ID_PHASE_5: "unavailable"},
            )

    def test_context_package_supports_complete_mixed_fixture_for_p7_eval_019(self) -> None:
        p4_item = make_item(
            item_id="p7-019-p4",
            source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
            primary_code="CATER_EXTERNAL_CATERERS_ALLOWED",
            primary_id=10,
            summary_text="Current supplier rule.",
        )
        p5_item = make_item(
            item_id="p7-019-p5",
            source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
            primary_code="SERV-003",
            primary_id=11,
            summary_text="Current supplier guidance.",
            sensitivity=SensitivityEnvelope(
                confidentiality_level=CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE,
                personal_information_status=PERSONAL_INFORMATION_STATUS_NO,
                de_identification_required=False,
                generation_allowed=True,
            ),
            retrieval=make_retrieval(rank=1, score=0.92),
        )
        p6_item = make_item(
            item_id="p7-019-p6",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HC-004",
            primary_id=12,
            summary_text="Historical smell precedent.",
            sensitivity=SensitivityEnvelope(
                confidentiality_level=CONFIDENTIALITY_LEVEL_RESTRICTED,
                personal_information_status=PERSONAL_INFORMATION_STATUS_UNKNOWN,
                de_identification_required=True,
                generation_allowed=True,
            ),
            retrieval=make_retrieval(rank=1, score=0.88),
        )
        package = ContextPackage(
            query=QueryContext("A beauty brand wants strong-smell catering. Have we dealt with this before, and what should we do now?"),
            routing_plan=QueryPlan(
                query_text="A beauty brand wants strong-smell catering. Have we dealt with this before, and what should we do now?",
                query_class=QUERY_CLASS_MIXED_CURRENT_AND_PRECEDENT,
                routing_confidence=ROUTING_CONFIDENCE_MEDIUM,
                required_layers=(LAYER_ID_PHASE_4, LAYER_ID_PHASE_5, LAYER_ID_PHASE_6),
                phase_4=Phase4RoutingIntent(required=True, domains=(PHASE_4_DOMAIN_CATERING_SUPPLIER,)),
                phase_5=Phase5RoutingIntent(required=True, needs_guidance=True, query_text="strong-smell catering current guidance", result_limit=5),
                phase_6=Phase6RoutingIntent(required=True, query_text="strong-smell catering historical precedent", result_limit=5),
                safety_overrides=("historical_reference_requires_current_authority_before_prescriptive_answer",),
            ),
            layer_execution=(
                LayerExecutionRecord(layer_id=LAYER_ID_PHASE_4, requested=True, execution_state=EXECUTION_STATE_SUCCESS, reasoning_state=REASONING_STATE_RESOLVED, result_count=1, normalized_items=(p4_item,)),
                LayerExecutionRecord(layer_id=LAYER_ID_PHASE_5, requested=True, execution_state=EXECUTION_STATE_SUCCESS, reasoning_state=None, result_count=1, normalized_items=(p5_item,)),
                LayerExecutionRecord(layer_id=LAYER_ID_PHASE_6, requested=True, execution_state=EXECUTION_STATE_SUCCESS, reasoning_state=None, result_count=1, normalized_items=(p6_item,)),
            ),
            phase_4_context=(p4_item,),
            phase_5_context=(p5_item,),
            phase_6_context=(p6_item,),
            authority_resolution=AuthorityResolution(
                overall_outcome_classification=AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY,
                resolved_current_truth_item_ids=("p7-019-p4",),
                current_guidance_item_ids=("p7-019-p5",),
                historical_precedent_item_ids=("p7-019-p6",),
                conflict_records=(
                    ConflictRecord(
                        conflict_type_code=CONFLICT_TYPE_A_P4_BEATS_P6,
                        controlling_layer=LAYER_ID_PHASE_4,
                        affected_item_ids=("p7-019-p4", "p7-019-p6"),
                        severity="medium",
                        resolution_action="current_rule_controls_historical_context",
                    ),
                ),
            ),
            uncertainty_state=UncertaintyState(has_unresolved_authority=False),
            confidentiality_state=ConfidentialityState(
                effective_confidentiality_level=CONFIDENTIALITY_LEVEL_RESTRICTED,
                contributing_item_ids=("p7-019-p4", "p7-019-p5", "p7-019-p6"),
                personal_information_present=False,
                de_identification_required=True,
                generation_allowed=True,
            ),
            degraded_retrieval_state=DegradedRetrievalState(any_degradation=False),
            grounding=GroundingState(
                references=(
                    GroundingReference(reference_id="claim-current", item_id="p7-019-p4", source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE, provenance=p4_item.provenance),
                    GroundingReference(reference_id="claim-guidance", item_id="p7-019-p5", source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE, provenance=p5_item.provenance),
                    GroundingReference(reference_id="claim-precedent", item_id="p7-019-p6", source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT, provenance=p6_item.provenance),
                )
            ),
            generator_policy=default_generator_policy(),
            context_contract_version=PHASE_7_CONTEXT_CONTRACT_VERSION,
        )
        self.assertEqual(package.authority_resolution.overall_outcome_classification, AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY)

    def test_context_package_supports_historical_contamination_fixture_for_p7_eval_025(self) -> None:
        current_item = make_item(
            item_id="p7-025-p5",
            source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
            primary_code="SERV-004",
            primary_id=20,
            summary_text="Current storage guidance exists but no current storage price authority.",
            sensitivity=SensitivityEnvelope(
                confidentiality_level=CONFIDENTIALITY_LEVEL_INTERNAL,
                personal_information_status=PERSONAL_INFORMATION_STATUS_NO,
                de_identification_required=False,
                generation_allowed=True,
            ),
            retrieval=make_retrieval(rank=1, score=0.83),
        )
        historical_item = make_item(
            item_id="p7-025-p6",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HC-003",
            primary_id=21,
            summary_text="Historical EUR 300 storage detail.",
            reasoning_state=REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
            sensitivity=SensitivityEnvelope(
                confidentiality_level=CONFIDENTIALITY_LEVEL_RESTRICTED,
                personal_information_status=PERSONAL_INFORMATION_STATUS_UNKNOWN,
                de_identification_required=True,
                generation_allowed=True,
            ),
            retrieval=make_retrieval(rank=1, score=0.91),
            layer_payload={"historical_value_only": True, "contamination_risk_level": "high"},
        )
        package = ContextPackage(
            query=QueryContext("WineGB paid EUR 300 for storage. Can I quote EUR 300 to this client now?"),
            routing_plan=QueryPlan(
                query_text="WineGB paid EUR 300 for storage. Can I quote EUR 300 to this client now?",
                query_class=QUERY_CLASS_AUTHORITY_VERIFICATION,
                routing_confidence=ROUTING_CONFIDENCE_MEDIUM,
                required_layers=(LAYER_ID_PHASE_5, LAYER_ID_PHASE_6),
                phase_5=Phase5RoutingIntent(required=True, needs_guidance=True, query_text="current storage authority", result_limit=5),
                phase_6=Phase6RoutingIntent(required=True, query_text="historical 300 storage precedent", result_limit=5),
                safety_overrides=("historical_reference_requires_current_authority_before_prescriptive_answer",),
            ),
            layer_execution=(
                make_not_requested(LAYER_ID_PHASE_4),
                LayerExecutionRecord(layer_id=LAYER_ID_PHASE_5, requested=True, execution_state=EXECUTION_STATE_SUCCESS, reasoning_state=None, result_count=1, normalized_items=(current_item,)),
                LayerExecutionRecord(layer_id=LAYER_ID_PHASE_6, requested=True, execution_state=EXECUTION_STATE_SUCCESS, reasoning_state=None, result_count=1, normalized_items=(historical_item,)),
            ),
            phase_4_context=(),
            phase_5_context=(current_item,),
            phase_6_context=(historical_item,),
            authority_resolution=AuthorityResolution(
                overall_outcome_classification=AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
                current_guidance_item_ids=("p7-025-p5",),
                historical_precedent_item_ids=("p7-025-p6",),
                contamination_annotations=(
                    ContaminationAnnotation(
                        forbidden_inference_type=FORBIDDEN_INFERENCE_HISTORICAL_PRICE_TO_CURRENT_PRICE,
                        implicated_historical_item_ids=("p7-025-p6",),
                        current_authority_consulted=True,
                        current_authority_item_ids=("p7-025-p5",),
                        prescriptive_use_allowed=False,
                        action=CONTAMINATION_ACTION_UNRESOLVED,
                    ),
                ),
                unresolved_authority_records=(
                    UnresolvedAuthorityRecord(
                        reasoning_state=REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
                        topic_or_domain="storage_price",
                        controlling_layer=LAYER_ID_PHASE_5,
                        related_current_item_ids=("p7-025-p5",),
                        related_historical_item_ids=("p7-025-p6",),
                        explanation_code="no_current_storage_price_authority",
                    ),
                ),
            ),
            uncertainty_state=UncertaintyState(
                has_unresolved_authority=True,
                unresolved_records=(
                    UnresolvedAuthorityRecord(
                        reasoning_state=REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
                        topic_or_domain="storage_price",
                        controlling_layer=LAYER_ID_PHASE_5,
                        related_current_item_ids=("p7-025-p5",),
                        related_historical_item_ids=("p7-025-p6",),
                        explanation_code="no_current_storage_price_authority",
                    ),
                ),
            ),
            confidentiality_state=ConfidentialityState(
                effective_confidentiality_level=CONFIDENTIALITY_LEVEL_RESTRICTED,
                contributing_item_ids=("p7-025-p5", "p7-025-p6"),
                personal_information_present=False,
                de_identification_required=True,
                generation_allowed=True,
            ),
            degraded_retrieval_state=DegradedRetrievalState(any_degradation=False),
            grounding=GroundingState(
                references=(
                    GroundingReference(reference_id="claim-current-gap", item_id="p7-025-p5", source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE, provenance=current_item.provenance),
                    GroundingReference(reference_id="claim-historical-storage", item_id="p7-025-p6", source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT, provenance=historical_item.provenance),
                )
            ),
            generator_policy=default_generator_policy(),
        )
        self.assertEqual(package.authority_resolution.overall_outcome_classification, AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY)

    def test_context_package_supports_requires_confirmation_fixture_for_p7_eval_035(self) -> None:
        p4_item = make_item(
            item_id="p7-035-p4",
            source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
            primary_code="TECH_REQ_CUSTOM_TECH_CONFIRM",
            primary_id=30,
            summary_text="Current technical requirement needs confirmation.",
            reasoning_state=REASONING_STATE_REQUIRES_CONFIRMATION,
        )
        package = ContextPackage(
            query=QueryContext("Can we support this unusual custom tech rig beyond the standard inventory?"),
            routing_plan=QueryPlan(
                query_text="Can we support this unusual custom tech rig beyond the standard inventory?",
                query_class=QUERY_CLASS_UNRESOLVED_AUTHORITY,
                routing_confidence=ROUTING_CONFIDENCE_MEDIUM,
                required_layers=(LAYER_ID_PHASE_4,),
                phase_4=Phase4RoutingIntent(required=True, domains=(PHASE_4_DOMAIN_TECHNICAL_CAPABILITY,)),
            ),
            layer_execution=(
                LayerExecutionRecord(layer_id=LAYER_ID_PHASE_4, requested=True, execution_state=EXECUTION_STATE_SUCCESS, reasoning_state=REASONING_STATE_REQUIRES_CONFIRMATION, result_count=1, normalized_items=(p4_item,)),
                make_not_requested(LAYER_ID_PHASE_5),
                make_not_requested(LAYER_ID_PHASE_6),
            ),
            phase_4_context=(p4_item,),
            phase_5_context=(),
            phase_6_context=(),
            authority_resolution=AuthorityResolution(
                overall_outcome_classification=AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION,
                resolved_current_truth_item_ids=("p7-035-p4",),
                unresolved_authority_records=(
                    UnresolvedAuthorityRecord(
                        reasoning_state=REASONING_STATE_REQUIRES_CONFIRMATION,
                        topic_or_domain="technical_capability",
                        controlling_layer=LAYER_ID_PHASE_4,
                        requires_confirmation=True,
                        related_current_item_ids=("p7-035-p4",),
                        explanation_code="current_authority_requires_confirmation",
                    ),
                ),
            ),
            uncertainty_state=UncertaintyState(
                has_unresolved_authority=True,
                unresolved_records=(
                    UnresolvedAuthorityRecord(
                        reasoning_state=REASONING_STATE_REQUIRES_CONFIRMATION,
                        topic_or_domain="technical_capability",
                        controlling_layer=LAYER_ID_PHASE_4,
                        requires_confirmation=True,
                        related_current_item_ids=("p7-035-p4",),
                        explanation_code="current_authority_requires_confirmation",
                    ),
                ),
            ),
            confidentiality_state=ConfidentialityState(
                effective_confidentiality_level=CONFIDENTIALITY_LEVEL_INTERNAL,
                contributing_item_ids=("p7-035-p4",),
                personal_information_present=False,
                de_identification_required=False,
                generation_allowed=True,
            ),
            degraded_retrieval_state=DegradedRetrievalState(any_degradation=False),
            grounding=GroundingState(
                references=(GroundingReference(reference_id="claim-confirmation", item_id="p7-035-p4", source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE, provenance=p4_item.provenance),)
            ),
            generator_policy=default_generator_policy(),
        )
        self.assertEqual(package.uncertainty_state.has_unresolved_authority, True)

    def test_context_package_supports_degraded_mode_fixture_for_p7_eval_038(self) -> None:
        p4_item = make_item(
            item_id="p7-038-p4",
            source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
            primary_code="PAYMENT_CONFIRMATION_MINIMUM_30_PERCENT",
            primary_id=40,
            summary_text="Current payment truth survives.",
        )
        package = ContextPackage(
            query=QueryContext("If Phase 5 retrieval is unavailable but a payment explanation is requested, what can still be answered?"),
            routing_plan=QueryPlan(
                query_text="If Phase 5 retrieval is unavailable but a payment explanation is requested, what can still be answered?",
                query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
                routing_confidence=ROUTING_CONFIDENCE_MEDIUM,
                required_layers=(LAYER_ID_PHASE_4, LAYER_ID_PHASE_5),
                phase_4=Phase4RoutingIntent(required=True, domains=(PHASE_4_DOMAIN_PAYMENT,)),
                phase_5=Phase5RoutingIntent(required=True, needs_guidance=True, query_text="payment explanation", result_limit=5),
            ),
            layer_execution=(
                LayerExecutionRecord(layer_id=LAYER_ID_PHASE_4, requested=True, execution_state=EXECUTION_STATE_SUCCESS, reasoning_state=REASONING_STATE_RESOLVED, result_count=1, normalized_items=(p4_item,)),
                LayerExecutionRecord(layer_id=LAYER_ID_PHASE_5, requested=True, execution_state="unavailable", reasoning_state=None, fallback_reason=None, error_category="wrapper_unavailable", safe_error_message="current guidance unavailable", result_count=0, normalized_items=()),
                make_not_requested(LAYER_ID_PHASE_6),
            ),
            phase_4_context=(p4_item,),
            phase_5_context=(),
            phase_6_context=(),
            authority_resolution=AuthorityResolution(
                overall_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                resolved_current_truth_item_ids=("p7-038-p4",),
            ),
            uncertainty_state=UncertaintyState(has_unresolved_authority=False),
            confidentiality_state=ConfidentialityState(
                effective_confidentiality_level=CONFIDENTIALITY_LEVEL_INTERNAL,
                contributing_item_ids=("p7-038-p4",),
                personal_information_present=False,
                de_identification_required=False,
                generation_allowed=True,
            ),
            degraded_retrieval_state=DegradedRetrievalState(
                any_degradation=True,
                affected_layers=(LAYER_ID_PHASE_5,),
                per_layer_execution_states={LAYER_ID_PHASE_4: EXECUTION_STATE_SUCCESS, LAYER_ID_PHASE_5: "unavailable", LAYER_ID_PHASE_6: EXECUTION_STATE_NOT_REQUESTED},
                fallback_reasons={},
                generator_warnings=("phase_5_current_guidance_unavailable",),
            ),
            grounding=GroundingState(
                references=(GroundingReference(reference_id="claim-payment", item_id="p7-038-p4", source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE, provenance=p4_item.provenance),)
            ),
            generator_policy=default_generator_policy(),
        )
        self.assertTrue(package.degraded_retrieval_state.any_degradation)

    def test_context_package_supports_confidentiality_escalation_fixture_for_p7_eval_039(self) -> None:
        p5_item = make_item(
            item_id="p7-039-p5",
            source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
            primary_code="SERV-004",
            primary_id=50,
            summary_text="Current supplier guidance.",
            sensitivity=SensitivityEnvelope(
                confidentiality_level=CONFIDENTIALITY_LEVEL_INTERNAL,
                personal_information_status=PERSONAL_INFORMATION_STATUS_NO,
                de_identification_required=False,
                generation_allowed=True,
            ),
            retrieval=make_retrieval(rank=1, score=0.77),
        )
        p6_item = make_item(
            item_id="p7-039-p6",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HC-003",
            primary_id=51,
            summary_text="Restricted historical storage precedent.",
            sensitivity=SensitivityEnvelope(
                confidentiality_level=CONFIDENTIALITY_LEVEL_RESTRICTED,
                personal_information_status=PERSONAL_INFORMATION_STATUS_YES,
                de_identification_required=True,
                generation_allowed=True,
            ),
            retrieval=make_retrieval(rank=1, score=0.8),
        )
        package = ContextPackage(
            query=QueryContext("A restricted historical storage precedent is relevant to a new pitch. What may be surfaced internally?"),
            routing_plan=QueryPlan(
                query_text="A restricted historical storage precedent is relevant to a new pitch. What may be surfaced internally?",
                query_class=QUERY_CLASS_AUTHORITY_VERIFICATION,
                routing_confidence=ROUTING_CONFIDENCE_LOW,
                required_layers=(LAYER_ID_PHASE_5, LAYER_ID_PHASE_6),
                phase_5=Phase5RoutingIntent(required=True, needs_guidance=True, query_text="current supplier guidance", result_limit=5),
                phase_6=Phase6RoutingIntent(required=True, query_text="restricted storage precedent", result_limit=5),
            ),
            layer_execution=(
                make_not_requested(LAYER_ID_PHASE_4),
                LayerExecutionRecord(layer_id=LAYER_ID_PHASE_5, requested=True, execution_state=EXECUTION_STATE_SUCCESS, reasoning_state=None, result_count=1, normalized_items=(p5_item,)),
                LayerExecutionRecord(layer_id=LAYER_ID_PHASE_6, requested=True, execution_state=EXECUTION_STATE_SUCCESS, reasoning_state=None, result_count=1, normalized_items=(p6_item,)),
            ),
            phase_4_context=(),
            phase_5_context=(p5_item,),
            phase_6_context=(p6_item,),
            authority_resolution=AuthorityResolution(
                overall_outcome_classification=AUTHORITY_OUTCOME_CURRENT_GUIDANCE,
                current_guidance_item_ids=("p7-039-p5",),
                historical_precedent_item_ids=("p7-039-p6",),
                contamination_annotations=(
                    ContaminationAnnotation(
                        forbidden_inference_type=FORBIDDEN_INFERENCE_HISTORICAL_PRICE_TO_CURRENT_PRICE,
                        implicated_historical_item_ids=("p7-039-p6",),
                        current_authority_consulted=True,
                        current_authority_item_ids=("p7-039-p5",),
                        prescriptive_use_allowed=False,
                        action=CONTAMINATION_ACTION_CONTEXT_ONLY,
                    ),
                ),
            ),
            uncertainty_state=UncertaintyState(has_unresolved_authority=False),
            confidentiality_state=ConfidentialityState(
                effective_confidentiality_level=CONFIDENTIALITY_LEVEL_RESTRICTED,
                contributing_item_ids=("p7-039-p5", "p7-039-p6"),
                personal_information_present=True,
                de_identification_required=True,
                generation_allowed=True,
                personal_information_status_summary=PERSONAL_INFORMATION_STATUS_YES,
                suppressed_item_ids=("p7-039-p6",),
                suppression_reasons={"p7-039-p6": "restricted_historical_detail_suppressed"},
            ),
            degraded_retrieval_state=DegradedRetrievalState(any_degradation=False),
            grounding=GroundingState(
                references=(
                    GroundingReference(reference_id="claim-current-guidance", item_id="p7-039-p5", source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE, provenance=p5_item.provenance),
                    GroundingReference(reference_id="claim-restricted-precedent", item_id="p7-039-p6", source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT, provenance=p6_item.provenance),
                )
            ),
            generator_policy=default_generator_policy(),
        )
        self.assertEqual(package.confidentiality_state.effective_confidentiality_level, CONFIDENTIALITY_LEVEL_RESTRICTED)
        self.assertTrue(package.confidentiality_state.personal_information_present)

    def test_context_package_rejects_malformed_cross_references(self) -> None:
        p4_item = make_item(
            item_id="malformed-p4",
            source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
            primary_code="PAYMENT_CONFIRMATION_MINIMUM_30_PERCENT",
            primary_id=60,
            summary_text="Current payment truth.",
        )
        with self.assertRaisesRegex(Phase7ContractError, "grounding reference source_layer_role must match"):
            ContextPackage(
                query=QueryContext("What minimum payment confirms a booking right now?"),
                routing_plan=QueryPlan(
                    query_text="What minimum payment confirms a booking right now?",
                    query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
                    routing_confidence=ROUTING_CONFIDENCE_HIGH,
                    required_layers=(LAYER_ID_PHASE_4,),
                    phase_4=Phase4RoutingIntent(required=True, domains=(PHASE_4_DOMAIN_PAYMENT,)),
                ),
                layer_execution=(
                    LayerExecutionRecord(
                        layer_id=LAYER_ID_PHASE_4,
                        requested=True,
                        execution_state=EXECUTION_STATE_SUCCESS,
                        reasoning_state=REASONING_STATE_RESOLVED,
                        result_count=1,
                        normalized_items=(p4_item,),
                    ),
                    make_not_requested(LAYER_ID_PHASE_5),
                    make_not_requested(LAYER_ID_PHASE_6),
                ),
                phase_4_context=(p4_item,),
                phase_5_context=(),
                phase_6_context=(),
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                    resolved_current_truth_item_ids=("malformed-p4",),
                ),
                uncertainty_state=UncertaintyState(has_unresolved_authority=False),
                confidentiality_state=ConfidentialityState(
                    effective_confidentiality_level=CONFIDENTIALITY_LEVEL_INTERNAL,
                    contributing_item_ids=("malformed-p4",),
                    personal_information_present=False,
                    de_identification_required=False,
                    generation_allowed=True,
                ),
                degraded_retrieval_state=DegradedRetrievalState(any_degradation=False),
                grounding=GroundingState(
                    references=(
                        GroundingReference(
                            reference_id="bad-reference",
                            item_id="malformed-p4",
                            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
                            provenance=p4_item.provenance,
                        ),
                    )
                ),
                generator_policy=default_generator_policy(),
            )

    def test_json_serialization_and_runtime_configuration(self) -> None:
        config = Phase7RuntimeConfiguration()
        payload = config.to_dict()
        self.assertEqual(payload["phase_5_result_limit"], 5)
        self.assertEqual(payload["phase_6_result_limit"], 5)
        self.assertEqual(json.loads(config.to_json())["routing_ambiguity_behavior"], "broaden_current_authority_first")

        ctx = QueryContext("What minimum payment confirms a booking right now?")
        self.assertEqual(json.loads(ctx.to_json())["query_text"], "What minimum payment confirms a booking right now?")

    def test_historical_answer_claim_frame_must_remain_historical_only(self) -> None:
        with self.assertRaisesRegex(Phase7ContractError, "historical answer claim frames must be marked historical_context_only"):
            AnswerClaimFrame(
                claim_id="claim:1",
                item_id="hist-1",
                source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
                authority_tier_code=authority_tier_for_source_role(
                    SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT
                ),
                claim_text="Historical precedent exists.",
                allowed_grounding_reference_ids=("generator_safe:1",),
                required_warning_codes=(),
                historical_context_only=False,
                requires_high_level_only=True,
                current_authority_supported=False,
            )

    def test_blocked_answer_generation_input_must_not_expose_claim_frames(self) -> None:
        with self.assertRaisesRegex(Phase7ContractError, "must not expose claim frames or safe grounding"):
            AnswerGenerationInput(
                query_text="Can I rely on this restricted historical detail?",
                query_class=QUERY_CLASS_PRECEDENT_DISCOVERY,
                authority_outcome=AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
                answer_mode=ANSWER_MODE_BLOCKED,
                generation_boundary=GENERATION_BOUNDARY_INTERNAL,
                generation_decision=GENERATION_DECISION_BLOCKED,
                effective_confidentiality_level=CONFIDENTIALITY_LEVEL_RESTRICTED,
                de_identification_required=True,
                personal_information_status_summary=PERSONAL_INFORMATION_STATUS_NO,
                confirmation_required=False,
                insufficient_current_authority=True,
                degraded_retrieval_state=DegradedRetrievalState(any_degradation=False),
                generator_policy=default_generator_policy(generation_allowed=False),
                claim_frames=(
                    AnswerClaimFrame(
                        claim_id="claim:1",
                        item_id="p6-1",
                        source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
                        authority_tier_code=authority_tier_for_source_role(
                            SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT
                        ),
                        claim_text="Historical precedent exists.",
                        allowed_grounding_reference_ids=(),
                        required_warning_codes=(),
                        historical_context_only=True,
                        requires_high_level_only=True,
                        current_authority_supported=False,
                    ),
                ),
                safe_grounding=(),
                blocked_reason="restricted_context",
            )

    def test_answer_result_requires_text_only_for_completed_status(self) -> None:
        completed = AnswerResult(
            status=ANSWER_RESULT_STATUS_COMPLETED,
            answer_mode=ANSWER_MODE_BLOCKED,
            authority_outcome=AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION,
            generation_decision=GENERATION_DECISION_ALLOWED,
            confirmation_required=True,
            insufficient_current_authority=False,
            degraded_context_present=False,
            materially_affects_answer_completeness=False,
            answer_text="Confirmation is required before relying on this answer.",
            grounding_uses=(),
            warning_codes=("confirmation_required",),
            failure_code=None,
        )
        self.assertEqual(completed.status, ANSWER_RESULT_STATUS_COMPLETED)

        with self.assertRaisesRegex(Phase7ContractError, "blocked or failed answer results require a failure_code"):
            AnswerResult(
                status=ANSWER_RESULT_STATUS_BLOCKED,
                answer_mode=ANSWER_MODE_BLOCKED,
                authority_outcome=AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION,
                generation_decision=GENERATION_DECISION_BLOCKED,
                confirmation_required=True,
                insufficient_current_authority=False,
                degraded_context_present=False,
                materially_affects_answer_completeness=False,
                answer_text=None,
                grounding_uses=(),
                warning_codes=("confirmation_required",),
                failure_code=None,
            )

    def test_answer_validation_result_rejects_valid_with_failure_codes(self) -> None:
        with self.assertRaisesRegex(Phase7ContractError, "must not include failure_codes"):
            AnswerValidationResult(
                is_valid=True,
                failure_codes=("authority_outcome_mismatch",),
                warning_codes=(),
            )


if __name__ == "__main__":
    unittest.main()
