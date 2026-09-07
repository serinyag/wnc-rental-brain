from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from tools.phase_08_workflow.governed_client_response import (
    ClientResponseDraft,
    ClientResponseProviderError,
    DeterministicFakeClientResponseProvider,
    OpenAIClientResponseProvider,
    RESPONSE_INTENT_CHANGE_ACKNOWLEDGEMENT,
    RESPONSE_INTENT_COMMUNICATE_RESTRICTION,
    RESPONSE_INTENT_COMPLETE_INQUIRY_RESPONSE,
    RESPONSE_INTENT_DECISION_PENDING,
    RESPONSE_INTENT_PENDING_INTERNAL_CONFIRMATION,
    RESPONSE_INTENT_REQUEST_CLIENT_INFORMATION,
    RESPONSE_INTENT_RESCHEDULE_ACKNOWLEDGEMENT,
    ResponseIntentResolver,
    build_draft_contract,
    validate_client_response_draft,
)


def make_snapshot(**overrides):
    values = {
        "rental_case": SimpleNamespace(rental_case_id=1, case_revision=4),
        "open_questions": (),
        "proposed_changes": (),
        "reschedule_requests": (),
        "case_decisions": (),
        "blockers": (),
        "reasoning_projections": (),
        "rental_case_facts": (),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def client_question(question_id: int = 9):
    return SimpleNamespace(
        open_question_id=question_id,
        human_question_text="What time would you like to begin?",
        requested_from_role="client",
        status="open",
    )


class GovernedClientResponseTests(unittest.TestCase):
    def test_resolver_has_explicit_precedence_for_all_initial_intents(self) -> None:
        cases = (
            (make_snapshot(open_questions=(client_question(),)), RESPONSE_INTENT_REQUEST_CLIENT_INFORMATION),
            (make_snapshot(proposed_changes=(SimpleNamespace(status="proposed"),)), RESPONSE_INTENT_CHANGE_ACKNOWLEDGEMENT),
            (make_snapshot(reschedule_requests=(SimpleNamespace(status="evaluating"),)), RESPONSE_INTENT_RESCHEDULE_ACKNOWLEDGEMENT),
            (make_snapshot(case_decisions=(SimpleNamespace(status="pending_approval"),)), RESPONSE_INTENT_DECISION_PENDING),
            (make_snapshot(reasoning_projections=(SimpleNamespace(degraded_retrieval_summary={"semantic_state_code": "known_no"}),)), RESPONSE_INTENT_COMMUNICATE_RESTRICTION),
            (make_snapshot(blockers=(SimpleNamespace(status="open", blocker_type="confirmation_required"),)), RESPONSE_INTENT_PENDING_INTERNAL_CONFIRMATION),
            (make_snapshot(), RESPONSE_INTENT_COMPLETE_INQUIRY_RESPONSE),
        )
        resolver = ResponseIntentResolver()
        for snapshot, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(resolver.resolve(snapshot).code, expected)

    def test_open_questions_take_precedence_in_compound_case(self) -> None:
        snapshot = make_snapshot(
            open_questions=(client_question(),),
            blockers=(SimpleNamespace(status="open", blocker_type="confirmation_required"),),
            reasoning_projections=(SimpleNamespace(degraded_retrieval_summary={"semantic_state_code": "known_no"}),),
        )
        self.assertEqual(ResponseIntentResolver().resolve(snapshot).code, RESPONSE_INTENT_REQUEST_CLIENT_INFORMATION)

    def test_fake_provider_is_deterministic_and_questions_are_exact(self) -> None:
        contract = build_draft_contract(
            snapshot=make_snapshot(open_questions=(client_question(),)),
            recipient_label="Avery",
            latest_client_message="We would like to hire the space.",
        )
        provider = DeterministicFakeClientResponseProvider()
        first = provider.generate_client_response(contract)
        self.assertEqual(first, provider.generate_client_response(contract))
        self.assertEqual(first.question_ids, (9,))
        self.assertTrue(
            validate_client_response_draft(
                contract=contract,
                draft=first,
                current_case_revision=4,
                current_context_hash=contract.context_hash,
            ).is_valid
        )

    def test_validator_rejects_unsafe_model_assertions_and_stale_contracts(self) -> None:
        contract = build_draft_contract(
            snapshot=make_snapshot(reasoning_projections=(SimpleNamespace(degraded_retrieval_summary={"semantic_state_code": "known_no"}),)),
            recipient_label="Avery",
            latest_client_message=None,
            commercial_snapshot=(("Booking fee", "EUR 75 excl. VAT"),),
        )
        unsafe = ClientResponseDraft(
            subject="Confirmed",
            body="Your venue is confirmed and the fee is EUR 25.",
        )
        result = validate_client_response_draft(
            contract=contract,
            draft=unsafe,
            current_case_revision=5,
            current_context_hash="changed",
        )
        self.assertFalse(result.is_valid)
        self.assertIn("stale_draft_contract", result.failure_codes)
        self.assertIn("unsupported_availability_or_confirmation", result.failure_codes)
        self.assertIn("commercial_assertion_not_allowed", result.failure_codes)

    def test_validator_emits_each_enforced_validation_code(self) -> None:
        clean_contract = build_draft_contract(
            snapshot=make_snapshot(),
            recipient_label="Avery",
            latest_client_message=None,
        )
        question_contract = build_draft_contract(
            snapshot=make_snapshot(open_questions=(client_question(),)),
            recipient_label="Avery",
            latest_client_message=None,
        )
        pending_decision_contract = build_draft_contract(
            snapshot=make_snapshot(case_decisions=(SimpleNamespace(status="pending_approval"),)),
            recipient_label="Avery",
            latest_client_message=None,
        )
        restriction_contract = build_draft_contract(
            snapshot=make_snapshot(
                reasoning_projections=(
                    SimpleNamespace(degraded_retrieval_summary={"semantic_state_code": "known_no"}),
                ),
            ),
            recipient_label="Avery",
            latest_client_message=None,
        )
        commercial_contract = build_draft_contract(
            snapshot=make_snapshot(),
            recipient_label="Avery",
            latest_client_message=None,
            commercial_snapshot=(("Booking fee", "EUR 75 excl. VAT"),),
        )
        cases = (
            (
                "stale contract",
                clean_contract,
                ClientResponseDraft(subject="Hello", body="Thank you."),
                5,
                clean_contract.context_hash,
                "stale_draft_contract",
            ),
            (
                "open questions",
                question_contract,
                ClientResponseDraft(subject="Hello", body="Thank you.", question_ids=()),
                4,
                question_contract.context_hash,
                "open_question_set_mismatch",
            ),
            (
                "availability assertion",
                clean_contract,
                ClientResponseDraft(subject="Hello", body="The venue is available."),
                4,
                clean_contract.context_hash,
                "unsupported_availability_or_confirmation",
            ),
            (
                "pending decision",
                pending_decision_contract,
                ClientResponseDraft(subject="Hello", body="The discount is approved."),
                4,
                pending_decision_contract.context_hash,
                "pending_decision_presented_as_active",
            ),
            (
                "known no contradiction",
                restriction_contract,
                ClientResponseDraft(subject="Hello", body="That arrangement is supported."),
                4,
                restriction_contract.context_hash,
                "known_no_contradiction",
            ),
            (
                "commercial assertion",
                commercial_contract,
                ClientResponseDraft(subject="Hello", body="The fee is EUR 25."),
                4,
                commercial_contract.context_hash,
                "commercial_assertion_not_allowed",
            ),
        )

        for name, contract, draft, revision, context_hash, expected_code in cases:
            with self.subTest(name=name):
                result = validate_client_response_draft(
                    contract=contract,
                    draft=draft,
                    current_case_revision=revision,
                    current_context_hash=context_hash,
                )
                self.assertEqual(result.failure_codes, (expected_code,))

    def test_validator_allows_safe_complete_inquiry_phrasing(self) -> None:
        contract = build_draft_contract(
            snapshot=make_snapshot(),
            recipient_label="Avery",
            latest_client_message=None,
        )
        draft = ClientResponseDraft(
            subject="Your inquiry",
            body="This looks suitable, and we can move this forward. The Studio can accommodate 20 guests.",
        )

        result = validate_client_response_draft(
            contract=contract,
            draft=draft,
            current_case_revision=4,
            current_context_hash=contract.context_hash,
        )

        self.assertTrue(result.is_valid)
        self.assertEqual(result.failure_codes, ())

    def test_validator_treats_currency_tokens_as_literal_values(self) -> None:
        contract = build_draft_contract(
            snapshot=make_snapshot(),
            recipient_label="Avery",
            latest_client_message=None,
            commercial_snapshot=(("Booking fee", "EUR 75 excl. VAT"),),
        )
        draft = ClientResponseDraft(subject="Fee", body="The fee is €75 excluding VAT.")

        result = validate_client_response_draft(
            contract=contract,
            draft=draft,
            current_case_revision=4,
            current_context_hash=contract.context_hash,
        )

        self.assertEqual(result.failure_codes, ("commercial_assertion_not_allowed",))

    def test_known_no_draft_may_state_that_an_arrangement_is_not_supported(self) -> None:
        contract = build_draft_contract(
            snapshot=make_snapshot(reasoning_projections=(SimpleNamespace(degraded_retrieval_summary={"semantic_state_code": "known_no"}),)),
            recipient_label="Avery",
            latest_client_message=None,
            feasibility_snapshot=(("Hard constraint", "Amplified event sound is not supported"),),
        )
        draft = DeterministicFakeClientResponseProvider().generate_client_response(contract)
        self.assertTrue(
            validate_client_response_draft(
                contract=contract,
                draft=draft,
                current_case_revision=4,
                current_context_hash=contract.context_hash,
            ).is_valid
        )

    def test_openai_provider_uses_one_no_tool_structured_request(self) -> None:
        contract = build_draft_contract(snapshot=make_snapshot(), recipient_label="Avery", latest_client_message=None)
        recorded = []

        def transport(payload, _base_url, _headers, _timeout, _ssl_context):
            recorded.append(payload)
            return ({"id": "resp_1", "output": [{"content": [{"text": json.dumps({"subject": "Hello", "body": "Hi Avery,\n\nThank you.\n\nWNC", "question_ids": []})}]}]}, {"x-request-id": "req_1"})

        draft = OpenAIClientResponseProvider(api_key="test-key", model_code="configured-model", transport=transport).generate_client_response(contract)
        self.assertEqual(draft.provider_request_id, "req_1")
        self.assertNotIn("tools", recorded[0])
        self.assertFalse(recorded[0]["store"])
        self.assertTrue(recorded[0]["text"]["format"]["strict"])

    def test_openai_provider_rejects_malformed_structured_output(self) -> None:
        contract = build_draft_contract(snapshot=make_snapshot(), recipient_label="Avery", latest_client_message=None)

        def transport(*_args):
            return ({"output": [{"content": [{"text": "not-json"}]}]}, {})

        provider = OpenAIClientResponseProvider(api_key="test-key", model_code="configured-model", transport=transport)
        with self.assertRaises(ClientResponseProviderError):
            provider.generate_client_response(contract)

    def test_openai_provider_rejects_empty_response_output(self) -> None:
        contract = build_draft_contract(snapshot=make_snapshot(), recipient_label="Avery", latest_client_message=None)

        def transport(*_args):
            return (
                {
                    "id": "resp_incomplete",
                    "status": "incomplete",
                    "incomplete_details": {"reason": "max_output_tokens"},
                    "output": [],
                },
                {"x-request-id": "req_incomplete"},
            )

        provider = OpenAIClientResponseProvider(api_key="test-key", model_code="configured-model", transport=transport)
        with self.assertRaises(ClientResponseProviderError):
            provider.generate_client_response(contract)


if __name__ == "__main__":
    unittest.main()
