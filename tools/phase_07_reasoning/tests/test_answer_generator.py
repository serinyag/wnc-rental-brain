from __future__ import annotations

import unittest

from tools.phase_07_reasoning.answer_generator import (
    RUNTIME_FAILURE_ANSWER_VALIDATION_FAILED,
    RUNTIME_FAILURE_GENERATION_BLOCKED,
    RUNTIME_FAILURE_GENERATOR_FAILURE,
    RUNTIME_FAILURE_GENERATOR_TIMEOUT,
    RUNTIME_FAILURE_MALFORMED_GENERATOR_RESPONSE,
    build_bounded_generator_request,
    generate_bounded_answer,
)
from tools.phase_07_reasoning.answer_layer import (
    ANSWER_VALIDATION_CONFIRMATION_FLAG_MISMATCH,
    ANSWER_VALIDATION_DEGRADED_FLAG_MISMATCH,
    ANSWER_VALIDATION_GROUNDING_SOURCE_ROLE_MISMATCH,
    ANSWER_VALIDATION_INSUFFICIENT_AUTHORITY_FLAG_MISMATCH,
    ANSWER_VALIDATION_UNKNOWN_GROUNDING_REFERENCE,
    build_answer_generation_input,
)
from tools.phase_07_reasoning.context_safety import finalize_context_safety
from tools.phase_07_reasoning.contracts import (
    ANSWER_MODE_AUTHORITATIVE_CURRENT,
    ANSWER_MODE_CURRENT_WITH_HISTORICAL_CONTEXT,
    ANSWER_MODE_HISTORICAL_DESCRIPTIVE,
    ANSWER_MODE_INSUFFICIENT_CURRENT_AUTHORITY,
    ANSWER_RESULT_STATUS_BLOCKED,
    ANSWER_RESULT_STATUS_COMPLETED,
    ANSWER_RESULT_STATUS_FAILED,
    AUTHORITY_OUTCOME_CURRENT_GUIDANCE,
    AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
    AUTHORITY_OUTCOME_HISTORICAL_PRECEDENT,
    AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
    AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY,
    AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION,
    EXECUTION_STATE_FALLBACK,
    GENERATION_DECISION_ALLOWED_WITH_RESTRICTIONS,
    PHASE_7_ANSWER_CONTRACT_VERSION,
    QUERY_CLASS_CURRENT_GUIDANCE,
    QUERY_CLASS_DETERMINISTIC_CURRENT,
    QUERY_CLASS_PRECEDENT_DISCOVERY,
    REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
    REASONING_STATE_REQUIRES_CONFIRMATION,
    SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
    SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
    AuthorityResolution,
    DegradedRetrievalState,
    UnresolvedAuthorityRecord,
)
from tools.phase_07_reasoning.tests.test_context_safety import (
    make_item,
    make_package,
)


class RecordingGenerator:
    def __init__(self, response_factory):
        self.response_factory = response_factory
        self.calls = []

    def generate(self, request):
        self.calls.append(request)
        return self.response_factory(request)


class ExceptionGenerator:
    def __init__(self, exc: Exception):
        self.exc = exc
        self.calls = []

    def generate(self, request):
        self.calls.append(request)
        raise self.exc


def make_valid_payload(request, *, answer_text: str = "Bounded answer.") -> dict:
    grounding_uses = ()
    if request.claim_frames and request.safe_grounding:
        claim_frame = request.claim_frames[0]
        grounding = request.safe_grounding[0]
        grounding_uses = (
            {
                "claim_id": claim_frame.claim_id,
                "reference_id": grounding.reference_id,
                "source_layer_role": grounding.source_layer_role,
            },
        )
    return {
        "status": ANSWER_RESULT_STATUS_COMPLETED,
        "answer_mode": request.answer_mode,
        "authority_outcome": request.authority_outcome,
        "generation_decision": request.generation_decision,
        "confirmation_required": request.confirmation_required,
        "insufficient_current_authority": request.insufficient_current_authority,
        "degraded_context_present": request.degraded_context_present,
        "materially_affects_answer_completeness": request.materially_affects_answer_completeness,
        "answer_text": answer_text,
        "grounding_uses": grounding_uses,
        "warning_codes": request.required_warning_codes,
        "failure_code": None,
        "answer_contract_version": PHASE_7_ANSWER_CONTRACT_VERSION,
    }


def finalized_answer_input(*, package):
    return build_answer_generation_input(finalize_context_safety(package))


class AnswerGeneratorRuntimeTests(unittest.TestCase):
    def test_blocked_generation_skips_generator_and_returns_blocked_result(self) -> None:
        p5_item = make_item(
            item_id="p5-blocked",
            source_layer_role="current_governed_knowledge",
            primary_code="GUIDE-BLOCK",
            primary_id=1,
            summary_text="Restricted current guidance.",
            generation_allowed=False,
            generation_restriction_reason="source_generation_prohibited",
        )
        answer_input = finalized_answer_input(
            package=make_package(
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
        generator = RecordingGenerator(make_valid_payload)
        runtime_result = generate_bounded_answer(answer_input, generator)
        self.assertEqual(len(generator.calls), 0)
        self.assertEqual(runtime_result.runtime_status, ANSWER_RESULT_STATUS_BLOCKED)
        self.assertEqual(runtime_result.failure_code, RUNTIME_FAILURE_GENERATION_BLOCKED)
        self.assertTrue(runtime_result.answer_validation_result.is_valid)

    def test_allowed_generation_calls_generator_once_and_validates(self) -> None:
        p4_item = make_item(
            item_id="p4-rule",
            source_layer_role="deterministic_rule",
            primary_code="PAY-001",
            primary_id=2,
            summary_text="Current payment rule.",
        )
        answer_input = finalized_answer_input(
            package=make_package(
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
        )
        generator = RecordingGenerator(make_valid_payload)
        runtime_result = generate_bounded_answer(answer_input, generator)
        self.assertEqual(len(generator.calls), 1)
        self.assertEqual(runtime_result.runtime_status, ANSWER_RESULT_STATUS_COMPLETED)
        self.assertTrue(runtime_result.answer_validation_result.is_valid)
        self.assertEqual(runtime_result.answer_result.answer_mode, ANSWER_MODE_AUTHORITATIVE_CURRENT)

    def test_restricted_generation_builds_least_privilege_request_only(self) -> None:
        p5_item = make_item(
            item_id="p5-current",
            source_layer_role="current_governed_knowledge",
            primary_code="GUIDE-010",
            primary_id=10,
            summary_text="Current guidance is available.",
        )
        p6_item = make_item(
            item_id="p6-precedent",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HIST-010",
            primary_id=11,
            summary_text="Alice historically handled florals for one event.",
            pi_status="yes",
        )
        answer_input = finalized_answer_input(
            package=make_package(
                query_text="Does WNC currently offer florals?",
                query_class=QUERY_CLASS_PRECEDENT_DISCOVERY,
                phase5_items=(p5_item,),
                phase6_items=(p6_item,),
                phase5_requested=True,
                phase5_state="success",
                phase6_requested=True,
                phase6_state="success",
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
                    current_guidance_item_ids=("p5-current",),
                    historical_precedent_item_ids=("p6-precedent",),
                    unresolved_authority_records=(
                        UnresolvedAuthorityRecord(
                            reasoning_state=REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
                            topic_or_domain="florals_service",
                            related_current_item_ids=("p5-current",),
                            related_historical_item_ids=("p6-precedent",),
                        ),
                    ),
                ),
            )
        )
        self.assertEqual(
            answer_input.generation_decision,
            GENERATION_DECISION_ALLOWED_WITH_RESTRICTIONS,
        )
        request = build_bounded_generator_request(answer_input)
        payload = request.to_dict()
        self.assertNotIn("context_package", payload)
        self.assertNotIn("phase_4_context", payload)
        self.assertNotIn("phase_5_context", payload)
        self.assertNotIn("phase_6_context", payload)
        self.assertNotIn("layer_execution", payload)
        self.assertTrue(request.restriction_instructions)
        self.assertIn("respect_allowed_with_restrictions_mode", request.restriction_instructions)
        historical_frame = next(
            frame for frame in request.claim_frames if frame.source_layer_role == SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT
        )
        self.assertTrue(historical_frame.requires_high_level_only)
        self.assertNotEqual(
            historical_frame.claim_text,
            "Alice historically handled florals for one event.",
        )

    def test_historical_only_request_preserves_historical_claim_frames(self) -> None:
        p6_item = make_item(
            item_id="p6-hist",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HIST-200",
            primary_id=20,
            summary_text="Historical precedent from a prior event.",
        )
        answer_input = finalized_answer_input(
            package=make_package(
                query_text="What happened historically?",
                query_class=QUERY_CLASS_PRECEDENT_DISCOVERY,
                phase6_items=(p6_item,),
                phase6_requested=True,
                phase6_state="success",
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_HISTORICAL_PRECEDENT,
                    historical_precedent_item_ids=("p6-hist",),
                ),
            )
        )
        request = build_bounded_generator_request(answer_input)
        self.assertEqual(request.answer_mode, ANSWER_MODE_HISTORICAL_DESCRIPTIVE)
        self.assertTrue(all(frame.historical_context_only for frame in request.claim_frames))

    def test_mixed_current_and_historical_request_preserves_claim_order_and_roles(self) -> None:
        p4_item = make_item(
            item_id="p4-current",
            source_layer_role="deterministic_rule",
            primary_code="RULE-300",
            primary_id=30,
            summary_text="Current deterministic rule.",
        )
        p6_item = make_item(
            item_id="p6-hist",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HIST-300",
            primary_id=31,
            summary_text="Historical precedent from a prior event.",
        )
        answer_input = finalized_answer_input(
            package=make_package(
                query_text="Compare current rule with precedent.",
                query_class=QUERY_CLASS_PRECEDENT_DISCOVERY,
                phase4_items=(p4_item,),
                phase6_items=(p6_item,),
                phase4_requested=True,
                phase4_state="success",
                phase6_requested=True,
                phase6_state="success",
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY,
                    resolved_current_truth_item_ids=("p4-current",),
                    historical_precedent_item_ids=("p6-hist",),
                ),
            )
        )
        request = build_bounded_generator_request(answer_input)
        self.assertEqual(request.answer_mode, ANSWER_MODE_CURRENT_WITH_HISTORICAL_CONTEXT)
        self.assertEqual(
            tuple(frame.source_layer_role for frame in request.claim_frames),
            (SOURCE_LAYER_ROLE_DETERMINISTIC_RULE, SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT),
        )

    def test_generator_exception_returns_failed_result_without_fallback(self) -> None:
        p4_item = make_item(
            item_id="p4-rule",
            source_layer_role="deterministic_rule",
            primary_code="PAY-EXC",
            primary_id=40,
            summary_text="Current payment rule.",
        )
        answer_input = finalized_answer_input(
            package=make_package(
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
        )
        runtime_result = generate_bounded_answer(
            answer_input,
            ExceptionGenerator(RuntimeError("boom")),
        )
        self.assertEqual(runtime_result.runtime_status, ANSWER_RESULT_STATUS_FAILED)
        self.assertEqual(runtime_result.failure_code, RUNTIME_FAILURE_GENERATOR_FAILURE)
        self.assertTrue(runtime_result.answer_validation_result.is_valid)

    def test_generator_timeout_returns_failed_result_without_fallback(self) -> None:
        p4_item = make_item(
            item_id="p4-rule",
            source_layer_role="deterministic_rule",
            primary_code="PAY-TIMEOUT",
            primary_id=41,
            summary_text="Current payment rule.",
        )
        answer_input = finalized_answer_input(
            package=make_package(
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
        )
        runtime_result = generate_bounded_answer(
            answer_input,
            ExceptionGenerator(TimeoutError("slow")),
        )
        self.assertEqual(runtime_result.runtime_status, ANSWER_RESULT_STATUS_FAILED)
        self.assertEqual(runtime_result.failure_code, RUNTIME_FAILURE_GENERATOR_TIMEOUT)

    def test_malformed_generator_response_fails_closed(self) -> None:
        p4_item = make_item(
            item_id="p4-rule",
            source_layer_role="deterministic_rule",
            primary_code="PAY-MALFORMED",
            primary_id=42,
            summary_text="Current payment rule.",
        )
        answer_input = finalized_answer_input(
            package=make_package(
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
        )
        generator = RecordingGenerator(
            lambda request: {
                **make_valid_payload(request),
                "answer_text": None,
            }
        )
        runtime_result = generate_bounded_answer(answer_input, generator)
        self.assertEqual(runtime_result.failure_code, RUNTIME_FAILURE_MALFORMED_GENERATOR_RESPONSE)
        self.assertEqual(runtime_result.runtime_status, ANSWER_RESULT_STATUS_FAILED)

    def test_authority_violating_storage_attack_is_rejected(self) -> None:
        p6_item = make_item(
            item_id="p6-price",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HIST-PRICE",
            primary_id=50,
            summary_text="Historical storage price was EUR300.",
        )
        answer_input = finalized_answer_input(
            package=make_package(
                query_text="What does storage cost now?",
                query_class=QUERY_CLASS_PRECEDENT_DISCOVERY,
                phase6_items=(p6_item,),
                phase6_requested=True,
                phase6_state="success",
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
                    historical_precedent_item_ids=("p6-price",),
                    unresolved_authority_records=(
                        UnresolvedAuthorityRecord(
                            reasoning_state=REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
                            topic_or_domain="storage_pricing",
                            related_current_item_ids=(),
                            related_historical_item_ids=("p6-price",),
                        ),
                    ),
                ),
            )
        )
        generator = RecordingGenerator(
            lambda request: {
                **make_valid_payload(request, answer_text="Storage costs EUR300."),
                "answer_mode": ANSWER_MODE_AUTHORITATIVE_CURRENT,
                "authority_outcome": AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                "insufficient_current_authority": False,
            }
        )
        runtime_result = generate_bounded_answer(answer_input, generator)
        self.assertEqual(runtime_result.failure_code, RUNTIME_FAILURE_ANSWER_VALIDATION_FAILED)
        self.assertIn(
            ANSWER_VALIDATION_INSUFFICIENT_AUTHORITY_FLAG_MISMATCH,
            runtime_result.failure_details,
        )

    def test_unknown_grounding_is_rejected(self) -> None:
        p4_item = make_item(
            item_id="p4-rule",
            source_layer_role="deterministic_rule",
            primary_code="PAY-GROUND",
            primary_id=60,
            summary_text="Current payment rule.",
        )
        answer_input = finalized_answer_input(
            package=make_package(
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
        )
        generator = RecordingGenerator(
            lambda request: {
                **make_valid_payload(request),
                "grounding_uses": (
                    {
                        "claim_id": request.claim_frames[0].claim_id,
                        "reference_id": "internal_provenance:123",
                        "source_layer_role": request.claim_frames[0].source_layer_role,
                    },
                ),
            }
        )
        runtime_result = generate_bounded_answer(answer_input, generator)
        self.assertEqual(runtime_result.failure_code, RUNTIME_FAILURE_ANSWER_VALIDATION_FAILED)
        self.assertIn(
            ANSWER_VALIDATION_UNKNOWN_GROUNDING_REFERENCE,
            runtime_result.failure_details,
        )

    def test_cross_request_grounding_is_rejected(self) -> None:
        first_item = make_item(
            item_id="p4-first",
            source_layer_role="deterministic_rule",
            primary_code="PAY-FIRST",
            primary_id=61,
            summary_text="First current payment rule.",
        )
        second_item = make_item(
            item_id="p4-second",
            source_layer_role="deterministic_rule",
            primary_code="PAY-SECOND",
            primary_id=62,
            summary_text="Second current payment rule.",
        )
        first_input = finalized_answer_input(
            package=make_package(
                query_text="First question?",
                query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
                phase4_items=(first_item,),
                phase4_requested=True,
                phase4_state="success",
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                    resolved_current_truth_item_ids=("p4-first",),
                ),
            )
        )
        second_input = finalized_answer_input(
            package=make_package(
                query_text="Second question?",
                query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
                phase4_items=(second_item,),
                phase4_requested=True,
                phase4_state="success",
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                    resolved_current_truth_item_ids=("p4-second",),
                ),
            )
        )
        foreign_reference_id = build_bounded_generator_request(second_input).safe_grounding[0].reference_id
        generator = RecordingGenerator(
            lambda request: {
                **make_valid_payload(request),
                "grounding_uses": (
                    {
                        "claim_id": request.claim_frames[0].claim_id,
                        "reference_id": foreign_reference_id,
                        "source_layer_role": request.claim_frames[0].source_layer_role,
                    },
                ),
            }
        )
        runtime_result = generate_bounded_answer(first_input, generator)
        self.assertEqual(runtime_result.failure_code, RUNTIME_FAILURE_ANSWER_VALIDATION_FAILED)
        self.assertIn(
            ANSWER_VALIDATION_UNKNOWN_GROUNDING_REFERENCE,
            runtime_result.failure_details,
        )

    def test_historical_grounding_cannot_masquerade_as_current(self) -> None:
        p6_item = make_item(
            item_id="p6-hist",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HIST-GROUND",
            primary_id=70,
            summary_text="Historical precedent from a prior event.",
        )
        answer_input = finalized_answer_input(
            package=make_package(
                query_text="What happened historically?",
                query_class=QUERY_CLASS_PRECEDENT_DISCOVERY,
                phase6_items=(p6_item,),
                phase6_requested=True,
                phase6_state="success",
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_HISTORICAL_PRECEDENT,
                    historical_precedent_item_ids=("p6-hist",),
                ),
            )
        )
        generator = RecordingGenerator(
            lambda request: {
                **make_valid_payload(request),
                "grounding_uses": (
                    {
                        "claim_id": request.claim_frames[0].claim_id,
                        "reference_id": request.safe_grounding[0].reference_id,
                        "source_layer_role": SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
                    },
                ),
            }
        )
        runtime_result = generate_bounded_answer(answer_input, generator)
        self.assertEqual(runtime_result.failure_code, RUNTIME_FAILURE_ANSWER_VALIDATION_FAILED)
        self.assertIn(
            ANSWER_VALIDATION_GROUNDING_SOURCE_ROLE_MISMATCH,
            runtime_result.failure_details,
        )

    def test_confirmation_required_response_cannot_remove_confirmation(self) -> None:
        p5_item = make_item(
            item_id="p5-confirm",
            source_layer_role="current_governed_knowledge",
            primary_code="GUIDE-CONFIRM",
            primary_id=80,
            summary_text="Current guidance exists but must be confirmed.",
        )
        answer_input = finalized_answer_input(
            package=make_package(
                query_text="Can WNC provide this service right now?",
                query_class=QUERY_CLASS_CURRENT_GUIDANCE,
                phase5_items=(p5_item,),
                phase5_requested=True,
                phase5_state="success",
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION,
                    current_guidance_item_ids=("p5-confirm",),
                    unresolved_authority_records=(
                        UnresolvedAuthorityRecord(
                            reasoning_state=REASONING_STATE_REQUIRES_CONFIRMATION,
                            topic_or_domain="service_availability",
                            related_current_item_ids=("p5-confirm",),
                            related_historical_item_ids=(),
                        ),
                    ),
                ),
            )
        )
        generator = RecordingGenerator(
            lambda request: {
                **make_valid_payload(request),
                "confirmation_required": False,
            }
        )
        runtime_result = generate_bounded_answer(answer_input, generator)
        self.assertEqual(runtime_result.failure_code, RUNTIME_FAILURE_ANSWER_VALIDATION_FAILED)
        self.assertIn(
            ANSWER_VALIDATION_CONFIRMATION_FLAG_MISMATCH,
            runtime_result.failure_details,
        )

    def test_degraded_state_instruction_and_validation_are_preserved(self) -> None:
        p5_item = make_item(
            item_id="p5-fallback",
            source_layer_role="current_governed_knowledge",
            primary_code="GUIDE-FALLBACK",
            primary_id=90,
            summary_text="Current guidance is available via fallback.",
        )
        answer_input = finalized_answer_input(
            package=make_package(
                query_text="How should staff handle this now?",
                query_class=QUERY_CLASS_CURRENT_GUIDANCE,
                phase5_items=(p5_item,),
                phase5_requested=True,
                phase5_state=EXECUTION_STATE_FALLBACK,
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_CURRENT_GUIDANCE,
                    current_guidance_item_ids=("p5-fallback",),
                ),
                degraded_retrieval_state=DegradedRetrievalState(
                    any_degradation=True,
                    materially_affects_answer_completeness=True,
                    affected_layers=("phase_5",),
                    per_layer_execution_states={"phase_5": EXECUTION_STATE_FALLBACK},
                    fallback_reasons={"phase_5": "hybrid_unavailable"},
                    generator_warnings=("current_guidance_retrieval_degraded",),
                ),
            )
        )
        request = build_bounded_generator_request(answer_input)
        self.assertIsNotNone(request.degraded_state_instruction)
        generator = RecordingGenerator(
            lambda bounded_request: {
                **make_valid_payload(bounded_request),
                "degraded_context_present": False,
            }
        )
        runtime_result = generate_bounded_answer(answer_input, generator)
        self.assertEqual(runtime_result.failure_code, RUNTIME_FAILURE_ANSWER_VALIDATION_FAILED)
        self.assertIn(
            ANSWER_VALIDATION_DEGRADED_FLAG_MISMATCH,
            runtime_result.failure_details,
        )


if __name__ == "__main__":
    unittest.main()
