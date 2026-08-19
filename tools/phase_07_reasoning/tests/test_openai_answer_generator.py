from __future__ import annotations

import json
import unittest
from unittest import mock

from tools.phase_07_reasoning.answer_generator import (
    RUNTIME_FAILURE_GENERATOR_FAILURE,
    RUNTIME_FAILURE_GENERATOR_TIMEOUT,
    RUNTIME_FAILURE_MALFORMED_GENERATOR_RESPONSE,
    build_bounded_generator_request,
    generate_bounded_answer,
)
from tools.phase_07_reasoning.answer_layer import build_answer_generation_input
from tools.phase_07_reasoning.context_safety import finalize_context_safety
from tools.phase_07_reasoning.contracts import (
    ANSWER_RESULT_STATUS_COMPLETED,
    AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
    AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
    QUERY_CLASS_DETERMINISTIC_CURRENT,
    QUERY_CLASS_PRECEDENT_DISCOVERY,
    REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
    SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
    AuthorityResolution,
    UnresolvedAuthorityRecord,
)
from tools.phase_07_reasoning.openai_answer_generator import (
    OpenAIAnswerGenerator,
    OpenAIAnswerGeneratorConfig,
    OpenAIAnswerModelUnavailableError,
    OpenAIAnswerProviderError,
)
from tools.phase_07_reasoning.tests.test_context_safety import (
    make_item,
    make_package,
)


class RecordingTransport:
    def __init__(self, response_factory):
        self.response_factory = response_factory
        self.calls = []

    def __call__(self, payload, api_base_url, headers, timeout_seconds, ssl_context):
        self.calls.append(
            {
                "payload": payload,
                "api_base_url": api_base_url,
                "headers": headers,
                "timeout_seconds": timeout_seconds,
            }
        )
        return self.response_factory(payload)


def finalized_answer_input(*, package):
    return build_answer_generation_input(finalize_context_safety(package))


def make_success_provider_response(request, *, answer_text: str = "Bounded answer.") -> dict:
    grounding_uses = []
    if request.claim_frames and request.safe_grounding:
        claim_frame = request.claim_frames[0]
        grounding = request.safe_grounding[0]
        grounding_uses.append(
            {
                "claim_id": claim_frame.claim_id,
                "reference_id": grounding.reference_id,
                "source_layer_role": grounding.source_layer_role,
            }
        )
    payload = {
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
        "warning_codes": list(request.required_warning_codes),
        "failure_code": None,
        "answer_contract_version": 1,
    }
    return {
        "id": "resp_test_123",
        "model": "gpt-5.6",
        "usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
        "output": [
            {
                "type": "message",
                "status": "completed",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": json.dumps(payload),
                    }
                ],
            }
        ],
    }


class OpenAIAnswerGeneratorTests(unittest.TestCase):
    def test_missing_api_key_raises_system_exit(self) -> None:
        with mock.patch(
            "tools.phase_07_reasoning.openai_answer_generator.load_env_value",
            return_value=None,
        ):
            with self.assertRaises(SystemExit):
                OpenAIAnswerGenerator()

    def test_invalid_configuration_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            OpenAIAnswerGeneratorConfig(model_code="  ")

    def test_provider_request_contains_no_tools_and_no_raw_restricted_material(self) -> None:
        current_item = make_item(
            item_id="p5-current",
            source_layer_role="current_governed_knowledge",
            primary_code="GUIDE-200",
            primary_id=200,
            summary_text="Current current-guidance summary.",
        )
        historical_item = make_item(
            item_id="p6-private",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HIST-PRIVATE",
            primary_id=201,
            summary_text="Haylin historically coordinated floral arrangements for Aurora.",
            confidentiality_level="restricted",
            pi_status="yes",
            primary_source_locator="private/case-notes.md:17",
        )
        answer_input = finalized_answer_input(
            package=make_package(
                query_text="Do we currently offer florals?",
                query_class=QUERY_CLASS_PRECEDENT_DISCOVERY,
                phase5_items=(current_item,),
                phase6_items=(historical_item,),
                phase5_requested=True,
                phase5_state="success",
                phase6_requested=True,
                phase6_state="success",
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
                    current_guidance_item_ids=("p5-current",),
                    historical_precedent_item_ids=("p6-private",),
                    unresolved_authority_records=(
                        UnresolvedAuthorityRecord(
                            reasoning_state=REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
                            topic_or_domain="florals",
                            related_current_item_ids=("p5-current",),
                            related_historical_item_ids=("p6-private",),
                        ),
                    ),
                ),
            )
        )
        bounded_request = build_bounded_generator_request(answer_input)
        generator = OpenAIAnswerGenerator(api_key="sk-test-secret")
        payload = generator.build_provider_request(
            bounded_request,
            client_request_id="phase7-answer-test",
        )
        payload_json = json.dumps(payload, sort_keys=True, ensure_ascii=True)

        self.assertNotIn("tools", payload)
        self.assertIn(
            "Treat the supplied generator-safe context as the complete factual universe for this answer.",
            payload["input"][0]["content"],
        )
        self.assertNotIn("Haylin historically coordinated floral arrangements for Aurora.", payload_json)
        self.assertNotIn("Haylin", payload_json)
        self.assertNotIn("private/case-notes.md:17", payload_json)
        self.assertNotIn("ContextPackage", payload_json)
        self.assertNotIn("phase_4_context", payload_json)
        self.assertNotIn("phase_5_context", payload_json)
        self.assertNotIn("phase_6_context", payload_json)
        self.assertNotIn("layer_execution", payload_json)
        self.assertNotIn("sk-test-secret", payload_json)

    def test_runtime_maps_provider_exception_to_generator_failure(self) -> None:
        answer_input = finalized_answer_input(
            package=make_package(
                query_text="What confirms a booking?",
                query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
                phase4_items=(
                    make_item(
                        item_id="p4-rule",
                        source_layer_role="deterministic_rule",
                        primary_code="PAY-001",
                        primary_id=1,
                        summary_text="Current payment rule.",
                    ),
                ),
                phase4_requested=True,
                phase4_state="success",
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                    resolved_current_truth_item_ids=("p4-rule",),
                ),
            )
        )
        transport = RecordingTransport(
            lambda _payload: (_ for _ in ()).throw(
                OpenAIAnswerProviderError("HTTP 401: OpenAI rejected the supplied API key for answer generation.")
            )
        )
        generator = OpenAIAnswerGenerator(
            api_key="sk-test",
            transport=transport,
        )
        runtime_result = generate_bounded_answer(answer_input, generator)
        self.assertEqual(runtime_result.failure_code, RUNTIME_FAILURE_GENERATOR_FAILURE)
        self.assertEqual(
            runtime_result.failure_details,
            ("HTTP 401: OpenAI rejected the supplied API key for answer generation.",),
        )

    def test_runtime_maps_timeout_to_generator_timeout(self) -> None:
        answer_input = finalized_answer_input(
            package=make_package(
                query_text="What confirms a booking?",
                query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
                phase4_items=(
                    make_item(
                        item_id="p4-rule",
                        source_layer_role="deterministic_rule",
                        primary_code="PAY-001",
                        primary_id=1,
                        summary_text="Current payment rule.",
                    ),
                ),
                phase4_requested=True,
                phase4_state="success",
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                    resolved_current_truth_item_ids=("p4-rule",),
                ),
            )
        )
        transport = RecordingTransport(
            lambda _payload: (_ for _ in ()).throw(
                TimeoutError("OpenAI answer generation timed out.")
            )
        )
        generator = OpenAIAnswerGenerator(api_key="sk-test", transport=transport)
        runtime_result = generate_bounded_answer(answer_input, generator)
        self.assertEqual(runtime_result.failure_code, RUNTIME_FAILURE_GENERATOR_TIMEOUT)
        self.assertEqual(
            runtime_result.failure_details,
            ("OpenAI answer generation timed out.",),
        )

    def test_runtime_maps_malformed_structured_response_to_malformed(self) -> None:
        answer_input = finalized_answer_input(
            package=make_package(
                query_text="What confirms a booking?",
                query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
                phase4_items=(
                    make_item(
                        item_id="p4-rule",
                        source_layer_role="deterministic_rule",
                        primary_code="PAY-001",
                        primary_id=1,
                        summary_text="Current payment rule.",
                    ),
                ),
                phase4_requested=True,
                phase4_state="success",
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                    resolved_current_truth_item_ids=("p4-rule",),
                ),
            )
        )
        transport = RecordingTransport(
            lambda _payload: (
                {
                    "id": "resp_bad",
                    "model": "gpt-5.6",
                    "output": [
                        {
                            "type": "message",
                            "role": "assistant",
                            "status": "completed",
                            "content": [{"type": "output_text", "text": "not-json"}],
                        }
                    ],
                },
                {"x-request-id": "req_bad"},
            )
        )
        generator = OpenAIAnswerGenerator(api_key="sk-test", transport=transport)
        runtime_result = generate_bounded_answer(answer_input, generator)
        self.assertEqual(runtime_result.failure_code, RUNTIME_FAILURE_MALFORMED_GENERATOR_RESPONSE)

    def test_runtime_maps_schema_mismatch_to_malformed(self) -> None:
        answer_input = finalized_answer_input(
            package=make_package(
                query_text="What confirms a booking?",
                query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
                phase4_items=(
                    make_item(
                        item_id="p4-rule",
                        source_layer_role="deterministic_rule",
                        primary_code="PAY-001",
                        primary_id=1,
                        summary_text="Current payment rule.",
                    ),
                ),
                phase4_requested=True,
                phase4_state="success",
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                    resolved_current_truth_item_ids=("p4-rule",),
                ),
            )
        )
        transport = RecordingTransport(
            lambda _payload: (
                {
                    "id": "resp_bad",
                    "model": "gpt-5.6",
                    "output": [
                        {
                            "type": "message",
                            "role": "assistant",
                            "status": "completed",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": json.dumps({"status": "completed"}),
                                }
                            ],
                        }
                    ],
                },
                {"x-request-id": "req_bad"},
            )
        )
        generator = OpenAIAnswerGenerator(api_key="sk-test", transport=transport)
        runtime_result = generate_bounded_answer(answer_input, generator)
        self.assertEqual(runtime_result.failure_code, RUNTIME_FAILURE_MALFORMED_GENERATOR_RESPONSE)

    def test_runtime_maps_empty_provider_response_to_malformed(self) -> None:
        answer_input = finalized_answer_input(
            package=make_package(
                query_text="What confirms a booking?",
                query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
                phase4_items=(
                    make_item(
                        item_id="p4-rule",
                        source_layer_role="deterministic_rule",
                        primary_code="PAY-001",
                        primary_id=1,
                        summary_text="Current payment rule.",
                    ),
                ),
                phase4_requested=True,
                phase4_state="success",
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                    resolved_current_truth_item_ids=("p4-rule",),
                ),
            )
        )
        transport = RecordingTransport(lambda _payload: ({}, {"x-request-id": "req_empty"}))
        generator = OpenAIAnswerGenerator(api_key="sk-test", transport=transport)
        runtime_result = generate_bounded_answer(answer_input, generator)
        self.assertEqual(runtime_result.failure_code, RUNTIME_FAILURE_MALFORMED_GENERATOR_RESPONSE)

    def test_unavailable_model_fails_explicitly_without_fallback(self) -> None:
        answer_input = finalized_answer_input(
            package=make_package(
                query_text="What confirms a booking?",
                query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
                phase4_items=(
                    make_item(
                        item_id="p4-rule",
                        source_layer_role="deterministic_rule",
                        primary_code="PAY-001",
                        primary_id=1,
                        summary_text="Current payment rule.",
                    ),
                ),
                phase4_requested=True,
                phase4_state="success",
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                    resolved_current_truth_item_ids=("p4-rule",),
                ),
            )
        )
        transport = RecordingTransport(
            lambda _payload: (_ for _ in ()).throw(
                OpenAIAnswerModelUnavailableError(
                    "Configured OpenAI answer model is unavailable."
                )
            )
        )
        generator = OpenAIAnswerGenerator(
            api_key="sk-test",
            config=OpenAIAnswerGeneratorConfig(model_code="gpt-does-not-exist"),
            transport=transport,
        )
        runtime_result = generate_bounded_answer(answer_input, generator)
        self.assertEqual(runtime_result.failure_code, RUNTIME_FAILURE_GENERATOR_FAILURE)
        self.assertEqual(
            runtime_result.failure_details,
            ("Configured OpenAI answer model is unavailable.",),
        )
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(transport.calls[0]["payload"]["model"], "gpt-does-not-exist")

    def test_successful_generation_captures_response_metadata(self) -> None:
        answer_input = finalized_answer_input(
            package=make_package(
                query_text="What confirms a booking?",
                query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
                phase4_items=(
                    make_item(
                        item_id="p4-rule",
                        source_layer_role="deterministic_rule",
                        primary_code="PAY-001",
                        primary_id=1,
                        summary_text="Current payment rule.",
                    ),
                ),
                phase4_requested=True,
                phase4_state="success",
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                    resolved_current_truth_item_ids=("p4-rule",),
                ),
            )
        )
        bounded_request = build_bounded_generator_request(answer_input)
        transport = RecordingTransport(
            lambda _payload: (
                make_success_provider_response(bounded_request),
                {"x-request-id": "req_ok"},
            )
        )
        generator = OpenAIAnswerGenerator(api_key="sk-test", transport=transport)
        runtime_result = generate_bounded_answer(answer_input, generator)
        self.assertEqual(runtime_result.runtime_status, ANSWER_RESULT_STATUS_COMPLETED)
        self.assertEqual(generator.last_response_metadata["provider"], "openai")
        self.assertEqual(generator.last_response_metadata["provider_request_id"], "req_ok")
        self.assertEqual(generator.last_response_metadata["input_tokens"], 100)
        self.assertEqual(generator.last_response_metadata["output_tokens"], 50)


if __name__ == "__main__":
    unittest.main()
