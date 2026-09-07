from __future__ import annotations

import unittest
from types import SimpleNamespace

from tools.phase_08_workflow.context_aware_drafting import (
    CLIENT_VISIBILITY_EXTERNAL_PENDING_VISIBLE,
    CLIENT_VISIBILITY_INTERNAL_ONLY,
    RESOLUTION_OWNER_EXTERNAL_PARTY,
    RESOLUTION_OWNER_WNC_INTERNAL,
    RESOLUTION_STATUS_CONTACT_REQUIRED,
    RESOLUTION_STATUS_CONTACTED_AWAITING_RESPONSE,
    ResolutionItem,
    derive_resolution_items,
    detect_guidance_topics,
    operator_annotations,
    retrieve_contextual_guidance,
    with_workflow_actions,
)
from tools.phase_08_workflow.governed_client_response import (
    ClientResponseDraft,
    build_draft_contract,
    validate_client_response_draft,
)


def snapshot(**overrides):
    values = {
        "rental_case": SimpleNamespace(rental_case_id=8, case_revision=2, rental_type_code="studio_space"),
        "open_questions": (),
        "case_decisions": (),
        "blockers": (),
        "workflow_events": (),
        "rental_case_facts": (),
        "proposed_changes": (),
        "reschedule_requests": (),
        "reasoning_projections": (),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def blocker(blocker_id: int, blocker_type: str, text: str):
    return SimpleNamespace(
        blocker_id=blocker_id,
        blocker_type=blocker_type,
        resolution_condition_text=text,
        origin_entity_reference="case",
        status="open",
    )


class _Search:
    def __init__(self, rows):
        self.rows = rows

    def search(self, **_kwargs):
        return tuple(self.rows)


class ContextAwareDraftingTests(unittest.TestCase):
    def test_client_owned_question_is_the_only_client_ask(self) -> None:
        case = snapshot(
            open_questions=(SimpleNamespace(open_question_id=1, human_question_text="What time works for you?", requested_from_role="client", status="open"),),
            blockers=(blocker(2, "availability_confirmation", "Confirm Studio availability"),),
        )
        items = derive_resolution_items(case)
        self.assertEqual(items[0].resolution_owner, "CLIENT")
        self.assertEqual(items[0].client_visibility, "ASK_CLIENT")
        self.assertEqual(operator_annotations(items)[0].message, "Confirm Studio availability")

    def test_wnc_internal_item_creates_annotation_and_is_action_idempotent(self) -> None:
        item = derive_resolution_items(snapshot(blockers=(blocker(2, "availability_confirmation", "Confirm Studio availability"),)))[0]
        action = SimpleNamespace(workflow_action_id=44, structured_payload={"resolution_item_key": item.proposition_key})
        enriched = with_workflow_actions((item,), (action,))
        self.assertEqual(enriched[0].resolution_owner, RESOLUTION_OWNER_WNC_INTERNAL)
        self.assertEqual(enriched[0].resolution_status, "ACTION_CREATED")
        self.assertEqual(enriched[0].workflow_action_id, 44)
        self.assertEqual(len(with_workflow_actions((item,), (action,))), 1)

    def test_external_contact_required_is_not_presented_as_contacted(self) -> None:
        item = derive_resolution_items(snapshot(blockers=(blocker(3, "facilitator_confirmation", "Contact facilitator"),)))[0]
        self.assertEqual(item.resolution_owner, RESOLUTION_OWNER_EXTERNAL_PARTY)
        self.assertEqual(item.resolution_status, RESOLUTION_STATUS_CONTACT_REQUIRED)
        contract = build_draft_contract(snapshot=snapshot(), recipient_label="Avery", latest_client_message=None, resolution_items=(item,))
        result = validate_client_response_draft(
            contract=contract,
            draft=ClientResponseDraft("Update", "Hi Avery,\n\nWe've reached out to the facilitator.\n\nBest,\nWNC Rentals"),
            current_case_revision=2,
            current_context_hash=contract.context_hash,
        )
        self.assertIn("external_contact_not_recorded", result.failure_codes)

    def test_contacted_external_party_may_be_visible(self) -> None:
        event = SimpleNamespace(event_type_code="external_resolution_contacted", structured_payload={"resolution_item_key": "blocker:3"})
        item = derive_resolution_items(snapshot(blockers=(blocker(3, "facilitator_confirmation", "Contact facilitator"),), workflow_events=(event,)))[0]
        self.assertEqual(item.resolution_status, RESOLUTION_STATUS_CONTACTED_AWAITING_RESPONSE)
        self.assertEqual(item.client_visibility, CLIENT_VISIBILITY_EXTERNAL_PENDING_VISIBLE)

    def test_task_creation_alone_does_not_change_external_contact_status(self) -> None:
        item = derive_resolution_items(snapshot(blockers=(blocker(3, "supplier_confirmation", "Contact supplier"),)))[0]
        enriched = with_workflow_actions((item,), (SimpleNamespace(workflow_action_id=9, structured_payload={"resolution_item_key": item.proposition_key}),))
        self.assertEqual(enriched[0].resolution_status, RESOLUTION_STATUS_CONTACT_REQUIRED)

    def test_catering_topics_and_current_authoritative_guidance_are_selected(self) -> None:
        case = snapshot(rental_case_facts=(SimpleNamespace(field_code="catering_arrangement", value_payload="client_external_caterer"),))
        self.assertIn("catering_kitchen", detect_guidance_topics(case, "We will bring a buffet."))
        guidance = retrieve_contextual_guidance(
            search=_Search((
                {"document_code": "SERV-003", "authority_classification": "authoritative", "body_text": "Kitchen guidance."},
                {"document_code": "TPL-006", "authority_classification": "authoritative", "body_text": "Old price."},
                {"document_code": "SERV-003", "authority_classification": "reference_only", "body_text": "Ignore."},
            )),
            topics=("catering_kitchen",),
            rental_type_code="studio_space",
        )
        self.assertEqual([(item.topic, item.client_safe_guidance) for item in guidance], [("catering_kitchen", "Kitchen guidance.")])

    def test_irrelevant_topics_are_not_requested(self) -> None:
        self.assertEqual(detect_guidance_topics(snapshot(), "A simple team workshop."), ())

    def test_historical_and_style_material_do_not_become_factual_guidance(self) -> None:
        guidance = retrieve_contextual_guidance(
            search=_Search((
                {"document_code": "TPL-006", "authority_classification": "guidance", "body_text": "Historical concession."},
                {"document_code": "CF-003", "authority_classification": "reference_only", "body_text": "Historical precedent."},
            )),
            topics=("capacity",),
            rental_type_code="studio_space",
        )
        self.assertEqual(guidance, ())

    def test_compound_case_preserves_separate_client_and_internal_items(self) -> None:
        case = snapshot(
            open_questions=(SimpleNamespace(open_question_id=1, human_question_text="What time works for you?", requested_from_role="client", status="open"),),
            blockers=(blocker(2, "availability_confirmation", "Confirm Studio availability"),),
            case_decisions=(SimpleNamespace(case_decision_id=3, decision_type="fee_adjustment", status="pending_approval"),),
        )
        items = derive_resolution_items(case)
        self.assertEqual({item.resolution_owner for item in items}, {"CLIENT", "WNC_INTERNAL", "GOVERNED_DECISION"})
        self.assertEqual([item.message for item in operator_annotations(items)], ["Confirm Studio availability"])

    def test_validator_rejects_em_dash_and_dangling_signoff(self) -> None:
        contract = build_draft_contract(snapshot=snapshot(), recipient_label="Avery", latest_client_message=None)
        result = validate_client_response_draft(
            contract=contract,
            draft=ClientResponseDraft("Avery — update", "Hi Avery,\n\nThanks.\n\nBest regards,"),
            current_case_revision=2,
            current_context_hash=contract.context_hash,
        )
        self.assertEqual(result.failure_codes, ("em_dash_not_allowed", "dangling_signoff"))

    def test_internal_annotations_are_not_sent_to_provider_payload(self) -> None:
        item = ResolutionItem("blocker:2", "Confirm Studio availability", RESOLUTION_OWNER_WNC_INTERNAL, "REQUIRED", CLIENT_VISIBILITY_INTERNAL_ONLY, True)
        contract = build_draft_contract(snapshot=snapshot(), recipient_label="Avery", latest_client_message=None, resolution_items=(item,))
        self.assertEqual(contract.to_provider_payload()["resolution_items"], [])
        self.assertEqual(contract.operator_annotations[0].message, "Confirm Studio availability")


if __name__ == "__main__":
    unittest.main()
