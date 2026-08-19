from __future__ import annotations

import unittest

from tools.phase_07_reasoning.answer_layer import (
    ANSWER_VALIDATION_BLOCKED_STATUS_REQUIRED,
    ANSWER_VALIDATION_BLOCKED_TEXT_FORBIDDEN,
    ANSWER_VALIDATION_MISSING_REQUIRED_WARNING_CODES,
    ANSWER_VALIDATION_UNKNOWN_GROUNDING_REFERENCE,
    answer_generation_may_invoke_model,
    build_answer_generation_input,
    validate_answer_result,
)
from tools.phase_07_reasoning.context_safety import finalize_context_safety
from tools.phase_07_reasoning.contracts import (
    ANSWER_MODE_BLOCKED,
    ANSWER_MODE_CONFIRMATION_REQUIRED,
    ANSWER_MODE_CURRENT_WITH_HISTORICAL_CONTEXT,
    ANSWER_MODE_INSUFFICIENT_CURRENT_AUTHORITY,
    ANSWER_RESULT_STATUS_COMPLETED,
    AUTHORITY_OUTCOME_CURRENT_GUIDANCE,
    AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
    AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
    AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY,
    AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION,
    GENERATION_DECISION_BLOCKED,
    QUERY_CLASS_CURRENT_GUIDANCE,
    QUERY_CLASS_DETERMINISTIC_CURRENT,
    QUERY_CLASS_PRECEDENT_DISCOVERY,
    REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
    REASONING_STATE_REQUIRES_CONFIRMATION,
    SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
    AnswerGroundingUse,
    AnswerResult,
    AuthorityResolution,
    Phase7ContractError,
    UnresolvedAuthorityRecord,
)
from tools.phase_07_reasoning.tests.test_context_safety import (
    make_item,
    make_package,
)


class AnswerLayerTests(unittest.TestCase):
    def test_answer_generation_input_requires_finalized_safe_context(self) -> None:
        p4_item = make_item(
            item_id="p4-rule",
            source_layer_role="deterministic_rule",
            primary_code="PAY-001",
            primary_id=1,
            summary_text="Current payment rule.",
        )
        package = make_package(
            query_text="What confirms a booking?",
            query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
            phase4_items=(p4_item,),
            phase4_requested=True,
            phase4_state="success",
            authority_resolution=AuthorityResolution(
                overall_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                resolved_current_truth_item_ids=("p4-rule",),
            ),
        )
        with self.assertRaisesRegex(Phase7ContractError, "generator_safe_context"):
            build_answer_generation_input(package)

    def test_suppressed_material_does_not_cross_generator_boundary(self) -> None:
        p5_item = make_item(
            item_id="p5-visible",
            source_layer_role="current_governed_knowledge",
            primary_code="GUIDE-001",
            primary_id=2,
            summary_text="Current guidance remains available.",
        )
        p6_item = make_item(
            item_id="p6-suppressed",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HIST-001",
            primary_id=3,
            summary_text="Restricted historical storage detail.",
            generation_allowed=False,
            generation_restriction_reason="restricted_source_generation",
        )
        package = finalize_context_safety(
            make_package(
                query_text="What does current guidance say about storage?",
                query_class=QUERY_CLASS_CURRENT_GUIDANCE,
                phase5_items=(p5_item,),
                phase6_items=(p6_item,),
                phase5_requested=True,
                phase5_state="success",
                phase6_requested=True,
                phase6_state="success",
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_CURRENT_GUIDANCE,
                    current_guidance_item_ids=("p5-visible",),
                    historical_precedent_item_ids=("p6-suppressed",),
                ),
            )
        )
        answer_input = build_answer_generation_input(package)
        self.assertEqual(tuple(frame.item_id for frame in answer_input.claim_frames), ("p5-visible",))
        self.assertEqual(
            tuple(reference.item_id for reference in answer_input.safe_grounding),
            ("p5-visible",),
        )

    def test_mixed_answer_mode_and_claim_roles_preserve_historical_boundary(self) -> None:
        p4_item = make_item(
            item_id="p4-rule",
            source_layer_role="deterministic_rule",
            primary_code="RULE-001",
            primary_id=10,
            summary_text="Current deterministic rule.",
        )
        p5_item = make_item(
            item_id="p5-guide",
            source_layer_role="current_governed_knowledge",
            primary_code="GUIDE-010",
            primary_id=11,
            summary_text="Current guidance note.",
        )
        p6_item = make_item(
            item_id="p6-historical",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HIST-010",
            primary_id=12,
            summary_text="Historical precedent from a prior event.",
        )
        answer_input = build_answer_generation_input(
            finalize_context_safety(
                make_package(
                    query_text="How does current guidance compare with prior precedent?",
                    query_class=QUERY_CLASS_PRECEDENT_DISCOVERY,
                    phase4_items=(p4_item,),
                    phase5_items=(p5_item,),
                    phase6_items=(p6_item,),
                    phase4_requested=True,
                    phase4_state="success",
                    phase5_requested=True,
                    phase5_state="success",
                    phase6_requested=True,
                    phase6_state="success",
                    authority_resolution=AuthorityResolution(
                        overall_outcome_classification=AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY,
                        resolved_current_truth_item_ids=("p4-rule",),
                        current_guidance_item_ids=("p5-guide",),
                        historical_precedent_item_ids=("p6-historical",),
                    ),
                )
            )
        )
        self.assertEqual(
            answer_input.answer_mode,
            ANSWER_MODE_CURRENT_WITH_HISTORICAL_CONTEXT,
        )
        historical_frames = [
            frame
            for frame in answer_input.claim_frames
            if frame.source_layer_role == SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT
        ]
        self.assertEqual(len(historical_frames), 1)
        self.assertTrue(historical_frames[0].historical_context_only)
        self.assertFalse(historical_frames[0].current_authority_supported)

    def test_insufficient_current_authority_survives_into_answer_input(self) -> None:
        p6_item = make_item(
            item_id="p6-only",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HIST-100",
            primary_id=100,
            summary_text="Historical storage precedent exists.",
        )
        answer_input = build_answer_generation_input(
            finalize_context_safety(
                make_package(
                    query_text="What does storage cost now?",
                    query_class=QUERY_CLASS_PRECEDENT_DISCOVERY,
                    phase6_items=(p6_item,),
                    phase6_requested=True,
                    phase6_state="success",
                    authority_resolution=AuthorityResolution(
                        overall_outcome_classification=AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
                        historical_precedent_item_ids=("p6-only",),
                        unresolved_authority_records=(
                            UnresolvedAuthorityRecord(
                                reasoning_state=REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
                                topic_or_domain="storage_pricing",
                                related_current_item_ids=(),
                                related_historical_item_ids=("p6-only",),
                            ),
                        ),
                    ),
                )
            )
        )
        self.assertEqual(
            answer_input.answer_mode,
            ANSWER_MODE_INSUFFICIENT_CURRENT_AUTHORITY,
        )
        self.assertTrue(answer_input.insufficient_current_authority)
        self.assertTrue(answer_generation_may_invoke_model(answer_input))

    def test_confirmation_required_survives_into_answer_input(self) -> None:
        p5_item = make_item(
            item_id="p5-uncertain",
            source_layer_role="current_governed_knowledge",
            primary_code="GUIDE-200",
            primary_id=200,
            summary_text="Current guidance exists but must be confirmed.",
        )
        answer_input = build_answer_generation_input(
            finalize_context_safety(
                make_package(
                    query_text="Can WNC provide this service right now?",
                    query_class=QUERY_CLASS_CURRENT_GUIDANCE,
                    phase5_items=(p5_item,),
                    phase5_requested=True,
                    phase5_state="success",
                    authority_resolution=AuthorityResolution(
                        overall_outcome_classification=AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION,
                        current_guidance_item_ids=("p5-uncertain",),
                        unresolved_authority_records=(
                            UnresolvedAuthorityRecord(
                                reasoning_state=REASONING_STATE_REQUIRES_CONFIRMATION,
                                topic_or_domain="service_availability",
                                related_current_item_ids=("p5-uncertain",),
                                related_historical_item_ids=(),
                            ),
                        ),
                    ),
                )
            )
        )
        self.assertEqual(answer_input.answer_mode, ANSWER_MODE_CONFIRMATION_REQUIRED)
        self.assertTrue(answer_input.confirmation_required)

    def test_blocked_input_cannot_invoke_model(self) -> None:
        p5_item = make_item(
            item_id="p5-blocked",
            source_layer_role="current_governed_knowledge",
            primary_code="GUIDE-300",
            primary_id=300,
            summary_text="Restricted current guidance.",
            generation_allowed=False,
            generation_restriction_reason="source_generation_prohibited",
        )
        answer_input = build_answer_generation_input(
            finalize_context_safety(
                make_package(
                    query_text="Tell me the restricted detail.",
                    query_class=QUERY_CLASS_CURRENT_GUIDANCE,
                    phase5_items=(p5_item,),
                    phase5_requested=True,
                    phase5_state="success",
                    authority_resolution=AuthorityResolution(
                        overall_outcome_classification=AUTHORITY_OUTCOME_CURRENT_GUIDANCE,
                        current_guidance_item_ids=("p5-blocked",),
                    ),
                )
            )
        )
        self.assertEqual(answer_input.generation_decision, GENERATION_DECISION_BLOCKED)
        self.assertEqual(answer_input.answer_mode, ANSWER_MODE_BLOCKED)
        self.assertFalse(answer_generation_may_invoke_model(answer_input))
        self.assertEqual(answer_input.claim_frames, ())
        self.assertEqual(answer_input.safe_grounding, ())

    def test_validate_answer_result_accepts_permitted_grounding(self) -> None:
        p4_item = make_item(
            item_id="p4-answerable",
            source_layer_role="deterministic_rule",
            primary_code="PAY-500",
            primary_id=500,
            summary_text="A current payment rule is available.",
        )
        answer_input = build_answer_generation_input(
            finalize_context_safety(
                make_package(
                    query_text="What confirms a booking?",
                    query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
                    phase4_items=(p4_item,),
                    phase4_requested=True,
                    phase4_state="success",
                    authority_resolution=AuthorityResolution(
                        overall_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                        resolved_current_truth_item_ids=("p4-answerable",),
                    ),
                )
            )
        )
        grounding = answer_input.safe_grounding[0]
        claim_frame = answer_input.claim_frames[0]
        answer_result = AnswerResult(
            status=ANSWER_RESULT_STATUS_COMPLETED,
            answer_mode=answer_input.answer_mode,
            authority_outcome=answer_input.authority_outcome,
            generation_decision=answer_input.generation_decision,
            confirmation_required=answer_input.confirmation_required,
            insufficient_current_authority=answer_input.insufficient_current_authority,
            degraded_context_present=answer_input.degraded_retrieval_state.any_degradation,
            materially_affects_answer_completeness=(
                answer_input.degraded_retrieval_state.materially_affects_answer_completeness
            ),
            answer_text="The current booking confirmation rule is grounded in the finalized safe context.",
            grounding_uses=(
                AnswerGroundingUse(
                    claim_id=claim_frame.claim_id,
                    reference_id=grounding.reference_id,
                    source_layer_role=grounding.source_layer_role,
                ),
            ),
            warning_codes=answer_input.required_warning_codes,
            failure_code=None,
        )
        validation = validate_answer_result(answer_input, answer_result)
        self.assertTrue(validation.is_valid)

    def test_validate_answer_result_rejects_unknown_grounding_reference(self) -> None:
        p4_item = make_item(
            item_id="p4-answerable",
            source_layer_role="deterministic_rule",
            primary_code="PAY-501",
            primary_id=501,
            summary_text="A current payment rule is available.",
        )
        answer_input = build_answer_generation_input(
            finalize_context_safety(
                make_package(
                    query_text="What confirms a booking?",
                    query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
                    phase4_items=(p4_item,),
                    phase4_requested=True,
                    phase4_state="success",
                    authority_resolution=AuthorityResolution(
                        overall_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                        resolved_current_truth_item_ids=("p4-answerable",),
                    ),
                )
            )
        )
        claim_frame = answer_input.claim_frames[0]
        answer_result = AnswerResult(
            status=ANSWER_RESULT_STATUS_COMPLETED,
            answer_mode=answer_input.answer_mode,
            authority_outcome=answer_input.authority_outcome,
            generation_decision=answer_input.generation_decision,
            confirmation_required=answer_input.confirmation_required,
            insufficient_current_authority=answer_input.insufficient_current_authority,
            degraded_context_present=answer_input.degraded_retrieval_state.any_degradation,
            materially_affects_answer_completeness=(
                answer_input.degraded_retrieval_state.materially_affects_answer_completeness
            ),
            answer_text="The answer cites an invalid grounding reference.",
            grounding_uses=(
                AnswerGroundingUse(
                    claim_id=claim_frame.claim_id,
                    reference_id="generator_safe:999",
                    source_layer_role=claim_frame.source_layer_role,
                ),
            ),
            warning_codes=answer_input.required_warning_codes,
            failure_code=None,
        )
        validation = validate_answer_result(answer_input, answer_result)
        self.assertIn(
            ANSWER_VALIDATION_UNKNOWN_GROUNDING_REFERENCE,
            validation.failure_codes,
        )

    def test_validate_answer_result_requires_warning_preservation(self) -> None:
        p5_item = make_item(
            item_id="p5-uncertain",
            source_layer_role="current_governed_knowledge",
            primary_code="GUIDE-201",
            primary_id=201,
            summary_text="Current guidance exists but must be confirmed.",
        )
        answer_input = build_answer_generation_input(
            finalize_context_safety(
                make_package(
                    query_text="Can WNC provide this service right now?",
                    query_class=QUERY_CLASS_CURRENT_GUIDANCE,
                    phase5_items=(p5_item,),
                    phase5_requested=True,
                    phase5_state="success",
                    authority_resolution=AuthorityResolution(
                        overall_outcome_classification=AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION,
                        current_guidance_item_ids=("p5-uncertain",),
                        unresolved_authority_records=(
                            UnresolvedAuthorityRecord(
                                reasoning_state=REASONING_STATE_REQUIRES_CONFIRMATION,
                                topic_or_domain="service_availability",
                                related_current_item_ids=("p5-uncertain",),
                                related_historical_item_ids=(),
                            ),
                        ),
                    ),
                )
            )
        )
        answer_result = AnswerResult(
            status=ANSWER_RESULT_STATUS_COMPLETED,
            answer_mode=answer_input.answer_mode,
            authority_outcome=answer_input.authority_outcome,
            generation_decision=answer_input.generation_decision,
            confirmation_required=answer_input.confirmation_required,
            insufficient_current_authority=answer_input.insufficient_current_authority,
            degraded_context_present=answer_input.degraded_retrieval_state.any_degradation,
            materially_affects_answer_completeness=(
                answer_input.degraded_retrieval_state.materially_affects_answer_completeness
            ),
            answer_text="Confirmation is needed.",
            grounding_uses=(),
            warning_codes=(),
            failure_code=None,
        )
        validation = validate_answer_result(answer_input, answer_result)
        self.assertIn(
            ANSWER_VALIDATION_MISSING_REQUIRED_WARNING_CODES,
            validation.failure_codes,
        )

    def test_validate_answer_result_rejects_completed_answer_for_blocked_input(self) -> None:
        p5_item = make_item(
            item_id="p5-blocked",
            source_layer_role="current_governed_knowledge",
            primary_code="GUIDE-301",
            primary_id=301,
            summary_text="Restricted current guidance.",
            generation_allowed=False,
            generation_restriction_reason="source_generation_prohibited",
        )
        answer_input = build_answer_generation_input(
            finalize_context_safety(
                make_package(
                    query_text="Tell me the restricted detail.",
                    query_class=QUERY_CLASS_CURRENT_GUIDANCE,
                    phase5_items=(p5_item,),
                    phase5_requested=True,
                    phase5_state="success",
                    authority_resolution=AuthorityResolution(
                        overall_outcome_classification=AUTHORITY_OUTCOME_CURRENT_GUIDANCE,
                        current_guidance_item_ids=("p5-blocked",),
                    ),
                )
            )
        )
        answer_result = AnswerResult(
            status=ANSWER_RESULT_STATUS_COMPLETED,
            answer_mode=answer_input.answer_mode,
            authority_outcome=answer_input.authority_outcome,
            generation_decision=answer_input.generation_decision,
            confirmation_required=answer_input.confirmation_required,
            insufficient_current_authority=answer_input.insufficient_current_authority,
            degraded_context_present=answer_input.degraded_retrieval_state.any_degradation,
            materially_affects_answer_completeness=(
                answer_input.degraded_retrieval_state.materially_affects_answer_completeness
            ),
            answer_text="A blocked answer should never be completed.",
            grounding_uses=(),
            warning_codes=answer_input.required_warning_codes,
            failure_code=None,
        )
        validation = validate_answer_result(answer_input, answer_result)
        self.assertIn(
            ANSWER_VALIDATION_BLOCKED_STATUS_REQUIRED,
            validation.failure_codes,
        )
        self.assertIn(
            ANSWER_VALIDATION_BLOCKED_TEXT_FORBIDDEN,
            validation.failure_codes,
        )


if __name__ == "__main__":
    unittest.main()
