from __future__ import annotations

from dataclasses import replace
import unittest

from tools.phase_08_workflow.contracts import (
    ACTION_CATEGORY_COMMUNICATION,
    ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
    APPROVAL_REQUEST_STATUS_CANCELLED,
    APPROVAL_REQUEST_STATUS_OPEN,
    APPROVAL_POSTURE_APPROVAL_REQUIRED,
    OPEN_QUESTION_STATUS_OPEN,
    ApprovalRequest,
    OpenQuestion,
    RentalCase,
    WorkflowAction,
    WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
    WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
    WORKFLOW_ACTION_STATUS_SUPERSEDED,
)
from tools.phase_08_workflow.inquiry_response_drafting import (
    DeterministicInquiryResponseDraftGenerator,
    InquiryResponseDraftContent,
    InquiryResponseDraftContext,
    InquiryResponseDraftRevision,
    InquiryResponseQuestionLine,
    INQUIRY_DRAFT_SOURCE_GENERATED,
    INQUIRY_DRAFT_STATUS_APPROVED,
    INQUIRY_DRAFT_STATUS_NEEDS_APPROVAL,
    INQUIRY_DRAFT_STATUS_SEND_OUTCOME_UNCERTAIN,
    INQUIRY_DRAFT_STATUS_STALE,
    display_status_for_revision,
    render_draft_body,
    validate_draft_content,
)
from tools.phase_08_workflow.observation_contracts import RentalCaseFact
from tools.phase_08_workflow.orchestration_repository import InMemoryWorkflowOrchestrationRepository
from tools.phase_08_workflow.test_console_service import TestConsoleConfig, TestConsoleError, TestConsoleService
from tools.phase_08_workflow.test_console_projection import TestConsoleCaseMetadata


def make_case(*, case_revision: int = 0) -> RentalCase:
    return RentalCase(
        rental_case_id=1,
        rental_case_uuid="case-1",
        case_reference_code="RC-9001",
        lifecycle_state="inquiry_active",
        case_revision=case_revision,
        rental_type_code="custom_scope",
        commercial_summary_status="unknown",
        operational_summary_status="unknown",
        is_active=True,
        service_level_or_type="test_rental",
        created_at="2026-08-15T10:00:00Z",
        updated_at="2026-08-15T10:00:00Z",
    )


def make_open_question(question_id: int, text: str) -> OpenQuestion:
    return OpenQuestion(
        open_question_id=question_id,
        rental_case_id=1,
        question_type=f"question_{question_id}",
        domain_code="qualification",
        human_question_text=text,
        blocking_scope="action",
        status=OPEN_QUESTION_STATUS_OPEN,
        created_at="2026-08-15T10:00:00Z",
        requested_from_role="client",
    )


def make_action(*, workflow_action_id: int = 1, status: str = WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL) -> WorkflowAction:
    return WorkflowAction(
        workflow_action_id=workflow_action_id,
        workflow_action_uuid=f"workflow-action-{workflow_action_id}",
        rental_case_id=1,
        action_type=ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
        action_category=ACTION_CATEGORY_COMMUNICATION,
        target_adapter_code="email",
        reason_entity_type="follow_up",
        reason_entity_id=1,
        reason_entity_reference="follow_up:1",
        approval_posture=APPROVAL_POSTURE_APPROVAL_REQUIRED,
        status=status,
        semantic_subject_hash="semantic:questions:1-2",
        source_case_revision=0,
        idempotency_key="action:REQUEST_CLIENT_INFORMATION:questions:1-2:0",
        structured_payload={
            "open_question_ids": [1, 2],
            "required_field_codes": ["guest_count", "event_type"],
            "intended_recipient_role": "client",
            "purpose": "request_missing_information",
            "reason": "Two inquiry fields remain unresolved.",
        },
        created_at="2026-08-15T10:00:00Z",
        updated_at="2026-08-15T10:00:00Z",
    )


class _DraftOnlyService(TestConsoleService):
    def __init__(self, repo: InMemoryWorkflowOrchestrationRepository) -> None:
        super().__init__(
            orchestration_repository=repo,
            observation_repository=object(),  # type: ignore[arg-type]
            query_runner=lambda *_args, **_kwargs: {"rows": []},
            config=TestConsoleConfig(),
            now=lambda: "2026-08-15T10:00:00Z",
        )
        self._draft_id = 100
        self._drafts: dict[int, InquiryResponseDraftRevision] = {}

    def _load_test_case_metadata(self, rental_case_id: int) -> TestConsoleCaseMetadata:
        del rental_case_id
        return TestConsoleCaseMetadata(
            label="Fixture rental",
            client_label="Acme Events",
            contact_email="client@example.test",
            event_reference="October social",
            created_by="test_console:operator",
            created_at="2026-08-15T10:00:00Z",
        )

    def _list_draft_revisions(self, rental_case_id: int) -> tuple[InquiryResponseDraftRevision, ...]:
        return tuple(
            revision
            for revision in sorted(self._drafts.values(), key=lambda item: item.created_at, reverse=True)
            if revision.rental_case_id == rental_case_id
        )

    def _load_current_draft_revision_for_conversation(
        self,
        rental_case_id: int,
        *,
        conversation_key: str,
    ) -> InquiryResponseDraftRevision | None:
        for revision in self._drafts.values():
            if revision.rental_case_id == rental_case_id and revision.conversation_key == conversation_key and revision.is_current:
                return revision
        return None

    def _load_draft_revision_by_id(
        self,
        rental_case_id: int,
        draft_revision_id: int,
    ) -> InquiryResponseDraftRevision | None:
        revision = self._drafts.get(draft_revision_id)
        if revision is None or revision.rental_case_id != rental_case_id:
            return None
        return revision

    def _load_draft_revision_by_approval_request_id(
        self,
        rental_case_id: int,
        approval_request_id: int,
    ) -> InquiryResponseDraftRevision | None:
        for revision in self._drafts.values():
            if revision.rental_case_id == rental_case_id and revision.approval_request_id == approval_request_id:
                return revision
        return None

    def _create_draft_revision(
        self,
        *,
        context: InquiryResponseDraftContext,
        content: InquiryResponseDraftContent,
        draft_source: str,
        created_by_reference: str,
        supersedes_draft_revision_id: int | None,
    ) -> InquiryResponseDraftRevision:
        validate_draft_content(content=content, required_questions=context.open_questions)
        for revision_id, revision in tuple(self._drafts.items()):
            if revision.rental_case_id == context.rental_case_id and revision.conversation_key == context.conversation_key and revision.is_current:
                self._drafts[revision_id] = InquiryResponseDraftRevision(
                    **{
                        **revision.__dict__,
                        "is_current": False,
                    }
                )
        self._draft_id += 1
        revision = InquiryResponseDraftRevision(
            inquiry_response_draft_revision_id=self._draft_id,
            inquiry_response_draft_revision_uuid=f"draft-{self._draft_id}",
            rental_case_id=context.rental_case_id,
            workflow_action_id=context.workflow_action_id,
            conversation_key=context.conversation_key,
            source_case_revision=context.source_case_revision,
            draft_status=INQUIRY_DRAFT_STATUS_NEEDS_APPROVAL,
            draft_source=draft_source,
            is_current=True,
            approval_request_id=None,
            subject=content.subject,
            salutation=content.salutation,
            intro_text=content.intro_text,
            question_lines=content.question_lines,
            closing_text=content.closing_text,
            signoff_text=content.signoff_text,
            body_text=render_draft_body(content),
            context_payload=context.to_payload(),
            context_hash=f"context:{self._draft_id}",
            content_hash=f"content:{self._draft_id}",
            recipient_email=context.recipient_email,
            recipient_label=context.recipient_label,
            sender_email=context.sender_email,
            sender_label=context.sender_label,
            sender_display_name=context.sender_label,
            supersedes_draft_revision_id=supersedes_draft_revision_id,
            delivered_at=None,
            delivery_external_reference=None,
            delivery_failure_code=None,
            approved_at=None,
            rejected_at=None,
            created_by_reference=created_by_reference,
            created_at="2026-08-15T10:00:00Z",
            updated_at="2026-08-15T10:00:00Z",
        )
        self._drafts[revision.inquiry_response_draft_revision_id] = revision
        return revision

    def _bind_approval_request_to_draft_revision(
        self,
        *,
        rental_case_id: int,
        draft_revision_id: int,
        approval_request_id: int,
        draft_status: str,
        updated_at: str,
    ) -> InquiryResponseDraftRevision:
        revision = self._drafts[draft_revision_id]
        updated = InquiryResponseDraftRevision(
            **{
                **revision.__dict__,
                "approval_request_id": approval_request_id,
                "draft_status": draft_status,
                "updated_at": updated_at,
            }
        )
        self._drafts[draft_revision_id] = updated
        return updated

    def _update_draft_revision_status(
        self,
        *,
        rental_case_id: int,
        draft_revision_id: int,
        draft_status: str,
        updated_at: str,
        approved_at: str | None = None,
        rejected_at: str | None = None,
        delivered_at: str | None = None,
        delivery_external_reference: str | None = None,
        delivery_failure_code: str | None = None,
    ) -> InquiryResponseDraftRevision:
        revision = self._drafts[draft_revision_id]
        if revision.rental_case_id != rental_case_id:
            raise AssertionError("draft rental_case_id mismatch")
        updated = InquiryResponseDraftRevision(
            **{
                **revision.__dict__,
                "draft_status": draft_status,
                "approved_at": revision.approved_at if approved_at is None else approved_at,
                "rejected_at": revision.rejected_at if rejected_at is None else rejected_at,
                "delivered_at": revision.delivered_at if delivered_at is None else delivered_at,
                "delivery_external_reference": (
                    revision.delivery_external_reference
                    if delivery_external_reference is None
                    else delivery_external_reference
                ),
                "delivery_failure_code": revision.delivery_failure_code if delivery_failure_code is None else delivery_failure_code,
                "updated_at": updated_at,
            }
        )
        self._drafts[draft_revision_id] = updated
        return updated

    def _create_console_event(self, **kwargs) -> None:
        del kwargs


class InquiryResponseDraftingContractTests(unittest.TestCase):
    def test_generator_covers_exact_open_question_set(self) -> None:
        context = InquiryResponseDraftContext(
            rental_case_id=1,
            workflow_action_id=7,
            conversation_key="conversation:1",
            source_case_revision=0,
            contact_label="Acme Events",
            recipient_email="client@example.test",
            recipient_label="Acme Events",
            sender_email="wnc-rentals-simulated@example.test",
            sender_label="WNC Rentals (Simulated)",
            open_questions=(
                make_open_question(1, "How many guests are you expecting?"),
                make_open_question(2, "What type of event are you planning?"),
            ),
            current_facts=(
                RentalCaseFact(
                    rental_case_fact_id=1,
                    rental_case_id=1,
                    field_code="requested_rental_scope",
                    domain_code="qualification",
                    value_payload="studio_space",
                    source_reference="test",
                    established_case_revision=0,
                    created_at="2026-08-15T10:00:00Z",
                    updated_at="2026-08-15T10:00:00Z",
                ),
            ),
        )

        content = DeterministicInquiryResponseDraftGenerator().generate(context)

        self.assertEqual(content.covered_question_ids, (1, 2))
        self.assertIn("How many guests", render_draft_body(content))
        self.assertIn("What type of event", render_draft_body(content))

    def test_validation_rejects_missing_question_coverage(self) -> None:
        questions = (
            make_open_question(1, "How many guests are you expecting?"),
            make_open_question(2, "What type of event are you planning?"),
        )
        content = InquiryResponseDraftContent(
            subject="Missing details",
            salutation="Hi there,",
            intro_text="Please share:",
            question_lines=(
                InquiryResponseQuestionLine(
                    open_question_id=1,
                    question_type="question_1",
                    human_question_text=questions[0].human_question_text,
                    prompt_text=questions[0].human_question_text,
                ),
            ),
            closing_text="Thanks.",
            signoff_text="Warmly,\nWNC",
        )

        with self.assertRaises(ValueError):
            validate_draft_content(content=content, required_questions=questions)

    def test_display_status_becomes_stale_when_case_revision_changes(self) -> None:
        revision = InquiryResponseDraftRevision(
            inquiry_response_draft_revision_id=100,
            inquiry_response_draft_revision_uuid="draft-100",
            rental_case_id=1,
            workflow_action_id=1,
            conversation_key="conversation:1",
            source_case_revision=0,
            draft_status=INQUIRY_DRAFT_STATUS_APPROVED,
            draft_source=INQUIRY_DRAFT_SOURCE_GENERATED,
            is_current=True,
            approval_request_id=55,
            subject="Need a few details",
            salutation="Hi there,",
            intro_text="Please share:",
            question_lines=(
                InquiryResponseQuestionLine(
                    open_question_id=1,
                    question_type="question_1",
                    human_question_text="How many guests are you expecting?",
                    prompt_text="How many guests are you expecting?",
                ),
            ),
            closing_text="Thanks.",
            signoff_text="Warmly,\nWNC",
            body_text="Hi there,\n\nPlease share:\n\n- How many guests are you expecting?\n\nThanks.\n\nWarmly,\nWNC",
            context_payload={"fixture": True},
            context_hash="ctx",
            content_hash="content",
            recipient_email="client@example.test",
            recipient_label="Acme Events",
            sender_email="wnc-rentals-simulated@example.test",
            sender_label="WNC Rentals (Simulated)",
            sender_display_name="WNC Rentals (Simulated)",
            created_by_reference="test_console:operator",
            created_at="2026-08-15T10:00:00Z",
            updated_at="2026-08-15T10:00:00Z",
        )

        status = display_status_for_revision(
            revision,
            current_case_revision=1,
            current_open_question_ids=(1,),
            action_status=WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
        )

        self.assertEqual(status, INQUIRY_DRAFT_STATUS_STALE)


class InquiryResponseDraftingServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = InMemoryWorkflowOrchestrationRepository(
            rental_cases={1: make_case()},
            rental_case_facts={1: []},
            blockers={1: []},
            requirements={1: []},
            open_questions={
                1: [
                    make_open_question(1, "How many guests are you expecting?"),
                    make_open_question(2, "What type of event are you planning?"),
                ]
            },
            approval_requests={1: []},
            proposed_changes={1: []},
            reschedule_requests={1: []},
            case_decisions={1: []},
            workflow_actions={1: [make_action()]},
            execution_attempts={1: []},
            follow_ups={1: []},
            milestones={1: []},
            artifacts={1: []},
            reasoning_projections={1: []},
            workflow_events={1: []},
        )
        self.service = _DraftOnlyService(self.repo)

    def test_edit_after_approval_creates_new_revision_and_successor_action(self) -> None:
        report = self.service.generate_inquiry_response_draft(rental_case_id=1, workflow_action_id=1)
        self.assertTrue(report.success)
        first_revision = next(iter(self.service._drafts.values()))
        first_approval_id = first_revision.approval_request_id
        self.assertIsNotNone(first_approval_id)

        approval_report = self.service.approve_request(rental_case_id=1, approval_request_id=first_approval_id)
        self.assertTrue(approval_report.success)
        approved_revision = self.service._drafts[first_revision.inquiry_response_draft_revision_id]
        self.assertEqual(approved_revision.draft_status, INQUIRY_DRAFT_STATUS_APPROVED)

        edit_report = self.service.edit_inquiry_response_draft(
            rental_case_id=1,
            draft_revision_id=first_revision.inquiry_response_draft_revision_id,
            subject="Need two quick details",
            salutation="Hi Acme Events,",
            intro_text="Before we can move forward, could you please confirm:",
            closing_text="Thanks so much.",
            signoff_text="Warmly,\nWNC",
            question_prompt_text_by_id={
                1: "How many guests are you expecting?",
                2: "What type of event are you planning?",
            },
        )
        self.assertTrue(edit_report.success)

        current_revision = next(revision for revision in self.service._drafts.values() if revision.is_current)
        self.assertNotEqual(current_revision.inquiry_response_draft_revision_id, first_revision.inquiry_response_draft_revision_id)
        self.assertNotEqual(current_revision.workflow_action_id, first_revision.workflow_action_id)
        self.assertNotEqual(current_revision.approval_request_id, first_approval_id)

        snapshot = self.repo.load_case_snapshot(1)
        assert snapshot is not None
        original_action = snapshot.find_workflow_action(1)
        successor_action = snapshot.find_workflow_action(current_revision.workflow_action_id)
        assert original_action is not None
        assert successor_action is not None
        self.assertEqual(original_action.status, WORKFLOW_ACTION_STATUS_SUPERSEDED)
        self.assertEqual(successor_action.status, WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL)
        self.assertEqual(current_revision.conversation_key, first_revision.conversation_key)
        self.assertNotEqual(successor_action.idempotency_key, original_action.idempotency_key)
        self.assertTrue(successor_action.idempotency_key.startswith(f"{original_action.idempotency_key}:successor:"))

    def test_stale_draft_cannot_be_approved(self) -> None:
        report = self.service.generate_inquiry_response_draft(rental_case_id=1, workflow_action_id=1)
        self.assertTrue(report.success)
        current_revision = next(revision for revision in self.service._drafts.values() if revision.is_current)
        approval_request_id = current_revision.approval_request_id
        assert approval_request_id is not None

        self.repo.increment_case_revision(
            rental_case_id=1,
            expected_case_revision=0,
            updated_at="2026-08-15T11:00:00Z",
        )

        approval_report = self.service.approve_request(rental_case_id=1, approval_request_id=approval_request_id)

        self.assertFalse(approval_report.success)
        self.assertIn("inquiry_draft_not_current", approval_report.failure_codes)
        self.assertIn("inquiry_draft_stale", approval_report.failure_codes)
        snapshot = self.repo.load_case_snapshot(1)
        assert snapshot is not None
        approval = snapshot.find_approval_request(approval_request_id)
        assert approval is not None
        self.assertEqual(approval.status, "cancelled")

    def test_superseded_open_approval_cannot_be_approved(self) -> None:
        first_report = self.service.generate_inquiry_response_draft(rental_case_id=1, workflow_action_id=1)
        self.assertTrue(first_report.success)
        first_revision = next(revision for revision in self.service._drafts.values() if revision.is_current)
        first_approval_id = first_revision.approval_request_id
        assert first_approval_id is not None

        second_report = self.service.generate_inquiry_response_draft(rental_case_id=1, workflow_action_id=1)
        self.assertTrue(second_report.success)
        current_revision = next(revision for revision in self.service._drafts.values() if revision.is_current)
        self.assertNotEqual(
            current_revision.inquiry_response_draft_revision_id,
            first_revision.inquiry_response_draft_revision_id,
        )

        approvals = []
        for approval in self.repo.approval_requests[1]:
            if approval.approval_request_id == first_approval_id:
                approvals.append(
                    replace(
                        approval,
                        status=APPROVAL_REQUEST_STATUS_OPEN,
                        decided_at=None,
                        decision_notes=None,
                    )
                )
            else:
                approvals.append(approval)
        self.repo.approval_requests[1] = approvals

        approval_report = self.service.approve_request(rental_case_id=1, approval_request_id=first_approval_id)

        self.assertFalse(approval_report.success)
        self.assertIn("inquiry_draft_not_current", approval_report.failure_codes)
        snapshot = self.repo.load_case_snapshot(1)
        assert snapshot is not None
        original_approval = snapshot.find_approval_request(first_approval_id)
        assert original_approval is not None
        self.assertEqual(original_approval.status, APPROVAL_REQUEST_STATUS_CANCELLED)
        current_approval = snapshot.find_approval_request(current_revision.approval_request_id)
        assert current_approval is not None
        self.assertEqual(current_approval.status, APPROVAL_REQUEST_STATUS_OPEN)
        action = snapshot.find_workflow_action(current_revision.workflow_action_id)
        assert action is not None
        self.assertEqual(action.status, WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL)

    def test_execute_requires_current_approved_draft_revision(self) -> None:
        report = self.service.generate_inquiry_response_draft(rental_case_id=1, workflow_action_id=1)
        self.assertTrue(report.success)

        with self.assertRaises(TestConsoleError) as error:
            self.service.execute_action(rental_case_id=1, workflow_action_id=1, execution_mode="default")

        self.assertEqual(error.exception.failure_code, "INQUIRY_DRAFT_NOT_APPROVED")

    def test_execute_rejects_superseded_action_when_newer_draft_exists(self) -> None:
        report = self.service.generate_inquiry_response_draft(rental_case_id=1, workflow_action_id=1)
        self.assertTrue(report.success)
        first_revision = next(revision for revision in self.service._drafts.values() if revision.is_current)
        first_approval_id = first_revision.approval_request_id
        assert first_approval_id is not None

        approval_report = self.service.approve_request(rental_case_id=1, approval_request_id=first_approval_id)
        self.assertTrue(approval_report.success)

        edit_report = self.service.edit_inquiry_response_draft(
            rental_case_id=1,
            draft_revision_id=first_revision.inquiry_response_draft_revision_id,
            subject="Need two quick details",
            salutation="Hi Acme Events,",
            intro_text="Before we can move forward, could you please confirm:",
            closing_text="Thanks so much.",
            signoff_text="Warmly,\nWNC",
            question_prompt_text_by_id={
                1: "How many guests are you expecting?",
                2: "What type of event are you planning?",
            },
        )
        self.assertTrue(edit_report.success)

        with self.assertRaises(TestConsoleError) as error:
            self.service.execute_action(rental_case_id=1, workflow_action_id=1, execution_mode="default")

        self.assertEqual(error.exception.failure_code, "INQUIRY_DRAFT_ACTION_MISMATCH")

    def test_execute_ambiguous_marks_current_draft_as_uncertain(self) -> None:
        report = self.service.generate_inquiry_response_draft(rental_case_id=1, workflow_action_id=1)
        self.assertTrue(report.success)
        current_revision = next(revision for revision in self.service._drafts.values() if revision.is_current)
        approval_request_id = current_revision.approval_request_id
        assert approval_request_id is not None

        approval_report = self.service.approve_request(rental_case_id=1, approval_request_id=approval_request_id)
        self.assertTrue(approval_report.success)

        execution_report = self.service.execute_action(rental_case_id=1, workflow_action_id=1, execution_mode="ambiguous")

        self.assertTrue(execution_report.success)
        updated_revision = self.service._drafts[current_revision.inquiry_response_draft_revision_id]
        self.assertEqual(updated_revision.draft_status, INQUIRY_DRAFT_STATUS_SEND_OUTCOME_UNCERTAIN)
        self.assertEqual(updated_revision.delivery_failure_code, "adapter_outcome_ambiguous")


if __name__ == "__main__":
    unittest.main()
