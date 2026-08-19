from __future__ import annotations

import unittest

from tools.phase_07_reasoning.context_safety import finalize_context_safety
from tools.phase_07_reasoning.contracts import (
    AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
    AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
    AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY,
    AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION,
    CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE,
    CONFIDENTIALITY_LEVEL_EXTERNALLY_SHAREABLE,
    CONFIDENTIALITY_LEVEL_INTERNAL,
    CONFIDENTIALITY_LEVEL_RESTRICTED,
    EXECUTION_STATE_FAILED,
    EXECUTION_STATE_FALLBACK,
    EXECUTION_STATE_NOT_REQUESTED,
    EXECUTION_STATE_SUCCESS,
    EXECUTION_STATE_UNAVAILABLE,
    GENERATION_DECISION_ALLOWED_WITH_RESTRICTIONS,
    GENERATION_DECISION_BLOCKED,
    LAYER_ID_PHASE_4,
    LAYER_ID_PHASE_5,
    LAYER_ID_PHASE_6,
    PERSONAL_INFORMATION_STATUS_NO,
    PERSONAL_INFORMATION_STATUS_UNKNOWN,
    PERSONAL_INFORMATION_STATUS_YES,
    QUERY_CLASS_CURRENT_GUIDANCE,
    QUERY_CLASS_DETERMINISTIC_CURRENT,
    QUERY_CLASS_PRECEDENT_DISCOVERY,
    QUERY_CLASS_UNRESOLVED_AUTHORITY,
    ROUTING_CONFIDENCE_HIGH,
    SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
    SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
    SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
    AuthorityResolution,
    ConfidentialityState,
    ContextPackage,
    DegradedRetrievalState,
    ExactIdentity,
    GeneratorPolicy,
    GroundingReference,
    GroundingState,
    LayerExecutionRecord,
    NormalizedResultEnvelope,
    Phase4RoutingIntent,
    Phase5RoutingIntent,
    Phase6RoutingIntent,
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


def make_item(
    *,
    item_id: str,
    source_layer_role: str,
    primary_code: str,
    primary_id: int,
    summary_text: str,
    confidentiality_level: str = CONFIDENTIALITY_LEVEL_INTERNAL,
    pi_status: str = PERSONAL_INFORMATION_STATUS_NO,
    de_identification_required: bool = False,
    generation_allowed: bool = True,
    generation_restriction_reason: str | None = None,
    primary_source_locator: str | None = None,
    reasoning_state: str | None = None,
    layer_payload: dict | None = None,
) -> NormalizedResultEnvelope:
    sensitivity = (
        phase4_default_sensitivity()
        if source_layer_role == SOURCE_LAYER_ROLE_DETERMINISTIC_RULE
        else SensitivityEnvelope(
            confidentiality_level=confidentiality_level,
            personal_information_status=pi_status,
            de_identification_required=de_identification_required,
            generation_allowed=generation_allowed,
            generation_restriction_reason=generation_restriction_reason,
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
        authority_priority=authority_priority_for_tier(
            authority_tier_for_source_role(source_layer_role)
        ),
        stable_identity=StableIdentity(primary_code=primary_code),
        exact_identity=ExactIdentity(primary_id=primary_id, version_id=primary_id),
        content_kind="fixture_item",
        execution_state=EXECUTION_STATE_SUCCESS,
        reasoning_state=reasoning_state,
        summary_text=summary_text,
        provenance=ProvenanceEnvelope(
            source_codes=(primary_code,),
            source_identifiers={"primary_code": primary_code},
            primary_source_locator=primary_source_locator or f"{primary_code} locator",
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


def make_not_requested(layer_id: str) -> LayerExecutionRecord:
    return make_record(
        layer_id,
        requested=False,
        execution_state=EXECUTION_STATE_NOT_REQUESTED,
    )


def make_package(
    *,
    query_text: str,
    query_class: str,
    phase4_items: tuple[NormalizedResultEnvelope, ...] = (),
    phase5_items: tuple[NormalizedResultEnvelope, ...] = (),
    phase6_items: tuple[NormalizedResultEnvelope, ...] = (),
    phase4_state: str = EXECUTION_STATE_NOT_REQUESTED,
    phase5_state: str = EXECUTION_STATE_NOT_REQUESTED,
    phase6_state: str = EXECUTION_STATE_NOT_REQUESTED,
    phase4_requested: bool = False,
    phase5_requested: bool = False,
    phase6_requested: bool = False,
    authority_resolution: AuthorityResolution | None = None,
    uncertainty_state: UncertaintyState | None = None,
    degraded_retrieval_state: DegradedRetrievalState | None = None,
) -> ContextPackage:
    required_layers = tuple(
        layer_id
        for layer_id, requested in (
            (LAYER_ID_PHASE_4, phase4_requested),
            (LAYER_ID_PHASE_5, phase5_requested),
            (LAYER_ID_PHASE_6, phase6_requested),
        )
        if requested
    )
    plan = QueryPlan(
        query_text=query_text,
        query_class=query_class,
        routing_confidence=ROUTING_CONFIDENCE_HIGH,
        required_layers=required_layers,
        phase_4=(
            Phase4RoutingIntent(required=True, domains=("payment",))
            if phase4_requested
            else None
        ),
        phase_5=(
            Phase5RoutingIntent(required=True, needs_guidance=True, query_text=query_text)
            if phase5_requested
            else None
        ),
        phase_6=(
            Phase6RoutingIntent(required=True, query_text=query_text)
            if phase6_requested
            else None
        ),
    )
    layer_execution = (
        make_record(
            LAYER_ID_PHASE_4,
            requested=phase4_requested,
            execution_state=phase4_state,
            items=phase4_items,
        )
        if phase4_requested
        else make_not_requested(LAYER_ID_PHASE_4),
        make_record(
            LAYER_ID_PHASE_5,
            requested=phase5_requested,
            execution_state=phase5_state,
            items=phase5_items,
            fallback_reason=(
                "hybrid_unavailable"
                if phase5_state == EXECUTION_STATE_FALLBACK
                else None
            ),
        )
        if phase5_requested
        else make_not_requested(LAYER_ID_PHASE_5),
        make_record(
            LAYER_ID_PHASE_6,
            requested=phase6_requested,
            execution_state=phase6_state,
            items=phase6_items,
            fallback_reason=(
                "historical_embedding_corpus_incomplete"
                if phase6_state == EXECUTION_STATE_FALLBACK
                else None
            ),
        )
        if phase6_requested
        else make_not_requested(LAYER_ID_PHASE_6),
    )
    all_items = phase4_items + phase5_items + phase6_items
    provisional_confidentiality = ConfidentialityState(
        effective_confidentiality_level=(
            all_items[0].sensitivity.confidentiality_level
            if all_items
            else CONFIDENTIALITY_LEVEL_INTERNAL
        ),
        contributing_item_ids=tuple(item.item_id for item in all_items),
        personal_information_present=False,
        de_identification_required=False,
        generation_allowed=True,
        generation_restriction_reason=None,
        personal_information_status_summary=PERSONAL_INFORMATION_STATUS_NO,
        suppressed_item_ids=(),
        suppression_reasons={},
    )
    provisional_policy = GeneratorPolicy(
        generation_allowed=True,
        allowed_actions=("synthesize", "explain", "compare", "express_uncertainty"),
        forbidden_actions=(
            "independent_retrieval",
            "invent_deterministic_values",
            "promote_precedent",
            "override_conflicts",
            "erase_confirmation_requirements",
            "fill_authority_gaps",
        ),
        required_warnings=(),
        confidentiality_restrictions=(),
        personal_information_restrictions=(),
    )
    return ContextPackage(
        query=QueryContext(query_text),
        routing_plan=plan,
        layer_execution=layer_execution,
        phase_4_context=phase4_items,
        phase_5_context=phase5_items,
        phase_6_context=phase6_items,
        authority_resolution=authority_resolution or AuthorityResolution(),
        uncertainty_state=uncertainty_state or UncertaintyState(False),
        confidentiality_state=provisional_confidentiality,
        degraded_retrieval_state=degraded_retrieval_state
        or DegradedRetrievalState(any_degradation=False, materially_affects_answer_completeness=False),
        grounding=GroundingState(
            references=tuple(
                GroundingReference(
                    reference_id=f"grounding:{index}",
                    item_id=item.item_id,
                    source_layer_role=item.source_layer_role,
                    provenance=item.provenance,
                )
                for index, item in enumerate(all_items, start=1)
            )
        ),
        generator_policy=provisional_policy,
        generator_safe_context=None,
    )


class ContextSafetyTests(unittest.TestCase):
    def test_confidentiality_ordering_matrix(self) -> None:
        cases = (
            (CONFIDENTIALITY_LEVEL_INTERNAL, CONFIDENTIALITY_LEVEL_EXTERNALLY_SHAREABLE, None, CONFIDENTIALITY_LEVEL_INTERNAL),
            (CONFIDENTIALITY_LEVEL_INTERNAL, CONFIDENTIALITY_LEVEL_INTERNAL, CONFIDENTIALITY_LEVEL_INTERNAL, CONFIDENTIALITY_LEVEL_INTERNAL),
            (CONFIDENTIALITY_LEVEL_INTERNAL, CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE, CONFIDENTIALITY_LEVEL_INTERNAL, CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE),
            (CONFIDENTIALITY_LEVEL_INTERNAL, CONFIDENTIALITY_LEVEL_EXTERNALLY_SHAREABLE, CONFIDENTIALITY_LEVEL_RESTRICTED, CONFIDENTIALITY_LEVEL_RESTRICTED),
            (CONFIDENTIALITY_LEVEL_INTERNAL, CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE, CONFIDENTIALITY_LEVEL_RESTRICTED, CONFIDENTIALITY_LEVEL_RESTRICTED),
        )
        for phase4_level, phase5_level, phase6_level, expected in cases:
            with self.subTest(expected=expected):
                p4_item = make_item(
                    item_id="p4",
                    source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
                    primary_code="RULE-1",
                    primary_id=1,
                    summary_text="Current rule.",
                )
                p5_item = make_item(
                    item_id="p5",
                    source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
                    primary_code="DOC-1",
                    primary_id=2,
                    summary_text="Current guidance.",
                    confidentiality_level=phase5_level,
                )
                phase6_items = ()
                authority = AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY,
                    resolved_current_truth_item_ids=("p4",),
                    current_guidance_item_ids=("p5",),
                )
                if phase6_level is not None:
                    p6_item = make_item(
                        item_id="p6",
                        source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
                        primary_code="HC-001",
                        primary_id=3,
                        summary_text="Historical precedent.",
                        confidentiality_level=phase6_level,
                    )
                    phase6_items = (p6_item,)
                    authority = AuthorityResolution(
                        overall_outcome_classification=AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY,
                        resolved_current_truth_item_ids=("p4",),
                        current_guidance_item_ids=("p5",),
                        historical_precedent_item_ids=("p6",),
                    )
                package = finalize_context_safety(
                    make_package(
                        query_text="Combined safety test",
                        query_class=QUERY_CLASS_CURRENT_GUIDANCE,
                        phase4_items=(p4_item,),
                        phase5_items=(p5_item,),
                        phase6_items=phase6_items,
                        phase4_requested=True,
                        phase5_requested=True,
                        phase6_requested=bool(phase6_items),
                        phase4_state=EXECUTION_STATE_SUCCESS,
                        phase5_state=EXECUTION_STATE_SUCCESS,
                        phase6_state=EXECUTION_STATE_SUCCESS if phase6_items else EXECUTION_STATE_NOT_REQUESTED,
                        authority_resolution=authority,
                    )
                )
                self.assertEqual(
                    package.confidentiality_state.effective_confidentiality_level,
                    expected,
                )

    def test_restricted_historical_precedent_is_deidentified_with_safe_grounding(self) -> None:
        current_item = make_item(
            item_id="p5-current",
            source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
            primary_code="SERV-004",
            primary_id=10,
            summary_text="Current supplier guidance.",
        )
        historical_item = make_item(
            item_id="p6-historical",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HC-003",
            primary_id=11,
            summary_text="WineGB paid EUR 300 for storage.",
            confidentiality_level=CONFIDENTIALITY_LEVEL_RESTRICTED,
            primary_source_locator="Case 03: WineGB Trade & Press Showcase",
            layer_payload={"historical_value_only": True, "precedent_availability": "limited"},
        )
        package = finalize_context_safety(
            make_package(
                query_text="What may be surfaced internally?",
                query_class=QUERY_CLASS_CURRENT_GUIDANCE,
                phase5_items=(current_item,),
                phase6_items=(historical_item,),
                phase5_requested=True,
                phase6_requested=True,
                phase5_state=EXECUTION_STATE_SUCCESS,
                phase6_state=EXECUTION_STATE_SUCCESS,
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY,
                    current_guidance_item_ids=("p5-current",),
                    historical_precedent_item_ids=("p6-historical",),
                ),
            )
        )
        projection = next(
            projection
            for projection in package.generator_safe_context.projections
            if projection.item_id == "p6-historical"
        )
        self.assertEqual(projection.visibility, "de_identified")
        self.assertNotIn("WineGB", projection.generator_summary_text)
        self.assertNotIn("EUR 300", projection.generator_summary_text)
        safe_grounding = next(
            reference
            for reference in package.generator_safe_context.grounding
            if reference.item_id == "p6-historical"
        )
        self.assertNotEqual(safe_grounding.safe_locator, historical_item.provenance.primary_source_locator)
        self.assertNotIn("WineGB", safe_grounding.safe_locator or "")

    def test_pi_bearing_historical_detail_is_deidentified_and_warned(self) -> None:
        historical_item = make_item(
            item_id="p6-pi",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HC-001",
            primary_id=12,
            summary_text="Named staff member handled the client request.",
            confidentiality_level=CONFIDENTIALITY_LEVEL_RESTRICTED,
            pi_status=PERSONAL_INFORMATION_STATUS_YES,
            de_identification_required=True,
            primary_source_locator="Case 01: Named Client Launch",
        )
        package = finalize_context_safety(
            make_package(
                query_text="Sensitivity boundary?",
                query_class=QUERY_CLASS_PRECEDENT_DISCOVERY,
                phase6_items=(historical_item,),
                phase6_requested=True,
                phase6_state=EXECUTION_STATE_SUCCESS,
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY,
                    historical_precedent_item_ids=("p6-pi",),
                ),
            )
        )
        self.assertIn("pi_deidentified", package.generator_policy.required_warnings)
        self.assertFalse(package.confidentiality_state.personal_information_present)
        self.assertTrue(package.confidentiality_state.de_identification_required)

    def test_source_generation_restricted_material_blocks_generation(self) -> None:
        blocked_item = make_item(
            item_id="p5-blocked",
            source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
            primary_code="SERV-BLOCKED",
            primary_id=20,
            summary_text="Blocked source.",
            confidentiality_level=CONFIDENTIALITY_LEVEL_RESTRICTED,
            generation_allowed=False,
            generation_restriction_reason="source_generation_prohibited",
        )
        package = finalize_context_safety(
            make_package(
                query_text="Blocked source",
                query_class=QUERY_CLASS_CURRENT_GUIDANCE,
                phase5_items=(blocked_item,),
                phase5_requested=True,
                phase5_state=EXECUTION_STATE_SUCCESS,
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY,
                    current_guidance_item_ids=("p5-blocked",),
                ),
            )
        )
        self.assertFalse(package.generator_policy.generation_allowed)
        self.assertEqual(
            package.generator_safe_context.generation_decision,
            GENERATION_DECISION_BLOCKED,
        )
        self.assertEqual(
            package.generator_safe_context.blocked_reason,
            "material_context_source_generation_restricted",
        )

    def test_insufficient_current_authority_still_allows_generation(self) -> None:
        package = finalize_context_safety(
            make_package(
                query_text="Official policy missing",
                query_class=QUERY_CLASS_UNRESOLVED_AUTHORITY,
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
                    unresolved_authority_records=(
                        UnresolvedAuthorityRecord(
                            reasoning_state="insufficient_current_authority",
                            topic_or_domain="discount_policy",
                            explanation_code="current_policy_missing",
                        ),
                    ),
                ),
                uncertainty_state=UncertaintyState(
                    True,
                    unresolved_records=(
                        UnresolvedAuthorityRecord(
                            reasoning_state="insufficient_current_authority",
                            topic_or_domain="discount_policy",
                            explanation_code="current_policy_missing",
                        ),
                    ),
                ),
            )
        )
        self.assertTrue(package.generator_policy.generation_allowed)
        self.assertEqual(
            package.generator_safe_context.generation_decision,
            GENERATION_DECISION_ALLOWED_WITH_RESTRICTIONS,
        )
        self.assertIn("current_authority_insufficient", package.generator_policy.required_warnings)

    def test_requires_confirmation_still_allows_generation(self) -> None:
        package = finalize_context_safety(
            make_package(
                query_text="Requires confirmation",
                query_class=QUERY_CLASS_UNRESOLVED_AUTHORITY,
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION,
                    unresolved_authority_records=(
                        UnresolvedAuthorityRecord(
                            reasoning_state="requires_confirmation",
                            topic_or_domain="technical_capability",
                            requires_confirmation=True,
                            explanation_code="phase4_requires_confirmation",
                        ),
                    ),
                ),
                uncertainty_state=UncertaintyState(
                    True,
                    unresolved_records=(
                        UnresolvedAuthorityRecord(
                            reasoning_state="requires_confirmation",
                            topic_or_domain="technical_capability",
                            requires_confirmation=True,
                            explanation_code="phase4_requires_confirmation",
                        ),
                    ),
                ),
            )
        )
        self.assertTrue(package.generator_policy.generation_allowed)
        self.assertIn("confirmation_required", package.generator_policy.required_warnings)

    def test_phase5_fallback_warning_preserved(self) -> None:
        guidance_item = make_item(
            item_id="p5-guidance",
            source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
            primary_code="DOC-5",
            primary_id=30,
            summary_text="Fallback current guidance.",
        )
        package = finalize_context_safety(
            make_package(
                query_text="Fallback guidance",
                query_class=QUERY_CLASS_CURRENT_GUIDANCE,
                phase5_items=(guidance_item,),
                phase5_requested=True,
                phase5_state=EXECUTION_STATE_FALLBACK,
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY,
                    current_guidance_item_ids=("p5-guidance",),
                ),
                degraded_retrieval_state=DegradedRetrievalState(
                    any_degradation=True,
                    materially_affects_answer_completeness=True,
                    affected_layers=(LAYER_ID_PHASE_5,),
                    per_layer_execution_states={LAYER_ID_PHASE_5: EXECUTION_STATE_FALLBACK},
                    fallback_reasons={LAYER_ID_PHASE_5: "hybrid_unavailable"},
                    generator_warnings=("phase_5_current_guidance_fallback",),
                ),
            )
        )
        self.assertIn("current_guidance_retrieval_degraded", package.generator_policy.required_warnings)

    def test_phase6_fallback_warning_preserved(self) -> None:
        historical_item = make_item(
            item_id="p6-precedent",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HC-006",
            primary_id=31,
            summary_text="Fallback historical precedent.",
            confidentiality_level=CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE,
        )
        package = finalize_context_safety(
            make_package(
                query_text="Fallback historical",
                query_class=QUERY_CLASS_PRECEDENT_DISCOVERY,
                phase6_items=(historical_item,),
                phase6_requested=True,
                phase6_state=EXECUTION_STATE_FALLBACK,
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY,
                    historical_precedent_item_ids=("p6-precedent",),
                ),
                degraded_retrieval_state=DegradedRetrievalState(
                    any_degradation=True,
                    materially_affects_answer_completeness=True,
                    affected_layers=(LAYER_ID_PHASE_6,),
                    per_layer_execution_states={LAYER_ID_PHASE_6: EXECUTION_STATE_FALLBACK},
                    fallback_reasons={LAYER_ID_PHASE_6: "historical_embedding_corpus_incomplete"},
                    generator_warnings=("phase_6_historical_retrieval_fallback",),
                ),
            )
        )
        self.assertIn("historical_retrieval_degraded", package.generator_policy.required_warnings)

    def test_phase5_unavailable_p4_survives(self) -> None:
        p4_item = make_item(
            item_id="p4-rule",
            source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
            primary_code="PAYMENT_CONFIRMATION_MINIMUM_30_PERCENT",
            primary_id=40,
            summary_text="Current payment rule.",
        )
        package = finalize_context_safety(
            make_package(
                query_text="Payment explanation unavailable",
                query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
                phase4_items=(p4_item,),
                phase4_requested=True,
                phase4_state=EXECUTION_STATE_SUCCESS,
                phase5_requested=True,
                phase5_state=EXECUTION_STATE_UNAVAILABLE,
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                    resolved_current_truth_item_ids=("p4-rule",),
                ),
                degraded_retrieval_state=DegradedRetrievalState(
                    any_degradation=True,
                    materially_affects_answer_completeness=True,
                    affected_layers=(LAYER_ID_PHASE_5,),
                    per_layer_execution_states={
                        LAYER_ID_PHASE_4: EXECUTION_STATE_SUCCESS,
                        LAYER_ID_PHASE_5: EXECUTION_STATE_UNAVAILABLE,
                    },
                    fallback_reasons={},
                    generator_warnings=("phase_5_current_guidance_unavailable",),
                ),
            )
        )
        self.assertTrue(package.generator_policy.generation_allowed)
        self.assertIn("current_guidance_unavailable", package.generator_policy.required_warnings)

    def test_phase4_failed_still_allows_uncertainty_answer(self) -> None:
        package = finalize_context_safety(
            make_package(
                query_text="Deterministic layer down",
                query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
                phase4_requested=True,
                phase4_state=EXECUTION_STATE_FAILED,
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
                    unresolved_authority_records=(
                        UnresolvedAuthorityRecord(
                            reasoning_state="insufficient_current_authority",
                            topic_or_domain="payment",
                            explanation_code="phase4_unavailable",
                        ),
                    ),
                ),
                uncertainty_state=UncertaintyState(
                    True,
                    unresolved_records=(
                        UnresolvedAuthorityRecord(
                            reasoning_state="insufficient_current_authority",
                            topic_or_domain="payment",
                            explanation_code="phase4_unavailable",
                        ),
                    ),
                ),
                degraded_retrieval_state=DegradedRetrievalState(
                    any_degradation=True,
                    materially_affects_answer_completeness=True,
                    affected_layers=(LAYER_ID_PHASE_4,),
                    per_layer_execution_states={LAYER_ID_PHASE_4: EXECUTION_STATE_FAILED},
                    fallback_reasons={},
                    generator_warnings=("phase_4_deterministic_layer_failed",),
                ),
            )
        )
        self.assertTrue(package.generator_policy.generation_allowed)
        self.assertEqual(
            package.generator_safe_context.generation_decision,
            GENERATION_DECISION_ALLOWED_WITH_RESTRICTIONS,
        )
        self.assertIn("deterministic_layer_failed", package.generator_policy.required_warnings)

    def test_authority_resolution_is_not_mutated(self) -> None:
        p4_item = make_item(
            item_id="p4-rule",
            source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
            primary_code="RULE-KEEP",
            primary_id=50,
            summary_text="Keep authority untouched.",
        )
        original_authority = AuthorityResolution(
            overall_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
            resolved_current_truth_item_ids=("p4-rule",),
        )
        package = make_package(
            query_text="No mutation",
            query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
            phase4_items=(p4_item,),
            phase4_requested=True,
            phase4_state=EXECUTION_STATE_SUCCESS,
            authority_resolution=original_authority,
        )
        finalized = finalize_context_safety(package)
        self.assertEqual(finalized.authority_resolution.to_dict(), original_authority.to_dict())


if __name__ == "__main__":
    unittest.main()
