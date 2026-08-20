from __future__ import annotations

from dataclasses import replace
import unittest

from tools.phase_08_workflow.contracts import (
    ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
    ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
    FOLLOW_UP_REASON_INQUIRY_MISSING_INFORMATION,
    OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION,
    FOLLOW_UP_STATUS_CANCELLED,
    FOLLOW_UP_STATUS_ESCALATED,
    FOLLOW_UP_STATUS_SCHEDULED,
    LIFECYCLE_STATE_CLOSED_LOST,
    LIFECYCLE_STATE_INQUIRY_ACTIVE,
    OPEN_QUESTION_STATUS_OPEN,
    FollowUp,
    OpenQuestion,
    RentalCase,
)
from tools.phase_08_workflow.execution_runtime import build_default_fake_execution_registry, execute_workflow_action
from tools.phase_08_workflow.execution_types import EXECUTION_FAILURE_ACTION_SUPERSEDED, WorkflowActionExecutionRequest
from tools.phase_08_workflow.inquiry_intake import CORE_INQUIRY_FIELD_RULES
from tools.phase_08_workflow.inquiry_waiting import INQUIRY_WAITING_FAILURE_STALE_CASE_REVISION, reconcile_inquiry_waiting
from tools.phase_08_workflow.orchestration_repository import InMemoryWorkflowOrchestrationRepository


QUESTION_FIXTURES = (
    ("requested_schedule", 1),
    ("guest_count", 2),
    ("requested_space", 3),
    ("event_type", 4),
)


def make_case(*, active_event_start: str | None = None) -> RentalCase:
    return RentalCase(
        rental_case_id=1,
        rental_case_uuid="case-1",
        case_reference_code="RC-1101",
        lifecycle_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
        case_revision=0,
        rental_type_code="custom_scope",
        commercial_summary_status="unknown",
        operational_summary_status="unknown",
        is_active=True,
        service_level_or_type="studio_rental",
        client_account_ref="client:1",
        primary_contact_ref="contact:1",
        active_event_start=active_event_start,
        created_at="2026-08-14T09:00:00Z",
        updated_at="2026-08-14T09:00:00Z",
    )


def make_open_question(field_code: str, question_id: int, *, status: str = OPEN_QUESTION_STATUS_OPEN) -> OpenQuestion:
    rule = CORE_INQUIRY_FIELD_RULES[field_code]
    return OpenQuestion(
        open_question_id=question_id,
        rental_case_id=1,
        question_type=rule.question_type,
        domain_code=rule.domain_code,
        human_question_text=rule.human_question_text,
        blocking_scope="transition",
        status=status,
        created_at="2026-08-14T09:00:00Z",
        requested_from_role="client",
        source_reference=f"open_question:{question_id}",
    )


def make_repo(*, questions=(), active_event_start: str | None = None) -> InMemoryWorkflowOrchestrationRepository:
    rental_case = make_case(active_event_start=active_event_start)
    return InMemoryWorkflowOrchestrationRepository(
        rental_cases={1: rental_case},
        rental_case_facts={1: []},
        blockers={1: []},
        requirements={1: []},
        open_questions={1: list(questions)},
        approval_requests={1: []},
        proposed_changes={1: []},
        reschedule_requests={1: []},
        case_decisions={1: []},
        workflow_actions={1: []},
        execution_attempts={1: []},
        follow_ups={1: []},
        milestones={1: []},
        artifacts={1: []},
        reasoning_projections={1: []},
        workflow_events={1: []},
    )


def resolve_questions(repo: InMemoryWorkflowOrchestrationRepository, *question_ids: int) -> None:
    updates = []
    for question in repo.open_questions[1]:
        if question.open_question_id in question_ids:
            updates.append(
                replace(
                    question,
                    status="resolved",
                    resolved_at="2026-08-21T10:00:00Z",
                )
            )
        else:
            updates.append(question)
    repo.open_questions[1] = updates


class InquiryWaitingTests(unittest.TestCase):
    def test_complete_inquiry_does_not_create_follow_up_or_action(self) -> None:
        repo = make_repo()

        result = reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-14T10:00:00Z",
        )

        self.assertFalse(result.plan.waiting_required)
        self.assertEqual(result.created_follow_up_ids, ())
        self.assertEqual(result.created_action_ids, ())
        self.assertEqual(repo.load_case_snapshot(1).follow_ups, ())

    def test_incomplete_inquiry_creates_single_scheduled_follow_up(self) -> None:
        repo = make_repo(questions=tuple(make_open_question(field_code, question_id) for field_code, question_id in QUESTION_FIXTURES))

        result = reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-14T10:00:00Z",
        )

        snapshot = repo.load_case_snapshot(1)
        self.assertTrue(result.plan.waiting_required)
        self.assertEqual(len(result.created_follow_up_ids), 1)
        self.assertEqual(result.created_action_ids, ())
        self.assertEqual(len(snapshot.follow_ups), 1)
        follow_up = snapshot.follow_ups[0]
        self.assertEqual(follow_up.reason_code, FOLLOW_UP_REASON_INQUIRY_MISSING_INFORMATION)
        self.assertEqual(follow_up.status, FOLLOW_UP_STATUS_SCHEDULED)
        self.assertEqual(follow_up.sequence_number, 1)
        self.assertEqual(follow_up.context_payload["open_question_ids"], [1, 2, 3, 4])

    def test_answered_pending_validation_question_still_requires_follow_up(self) -> None:
        repo = make_repo(
            questions=(
                make_open_question(
                    "requested_space",
                    3,
                    status=OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION,
                ),
            )
        )

        result = reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-14T10:00:00Z",
        )

        self.assertTrue(result.plan.waiting_required)
        self.assertEqual(result.plan.open_question_ids, (3,))

    def test_repeated_waiting_evaluation_is_idempotent(self) -> None:
        repo = make_repo(questions=tuple(make_open_question(field_code, question_id) for field_code, question_id in QUESTION_FIXTURES))

        first = reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-14T10:00:00Z",
        )
        second = reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-14T10:00:00Z",
        )

        self.assertEqual(len(first.created_follow_up_ids), 1)
        self.assertEqual(second.created_follow_up_ids, ())
        self.assertEqual(len(repo.load_case_snapshot(1).follow_ups), 1)

    def test_before_due_waiting_does_not_create_action(self) -> None:
        repo = make_repo(questions=tuple(make_open_question(field_code, question_id) for field_code, question_id in QUESTION_FIXTURES))
        reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-14T10:00:00Z",
        )

        result = reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-21T09:59:00Z",
        )

        snapshot = repo.load_case_snapshot(1)
        self.assertEqual(result.created_action_ids, ())
        self.assertEqual(snapshot.follow_ups[0].status, FOLLOW_UP_STATUS_SCHEDULED)
        self.assertEqual(snapshot.workflow_actions, ())

    def test_due_waiting_creates_single_client_information_action(self) -> None:
        repo = make_repo(questions=tuple(make_open_question(field_code, question_id) for field_code, question_id in QUESTION_FIXTURES))
        reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-14T10:00:00Z",
        )

        result = reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-21T10:00:00Z",
        )

        snapshot = repo.load_case_snapshot(1)
        self.assertEqual(len(snapshot.follow_ups), 1)
        self.assertEqual(len(result.created_action_ids), 1)
        self.assertEqual(len(snapshot.workflow_actions), 1)
        action = snapshot.workflow_actions[0]
        self.assertEqual(action.action_type, ACTION_TYPE_REQUEST_CLIENT_INFORMATION)
        self.assertEqual(action.structured_payload["open_question_ids"], [1, 2, 3, 4])

    def test_repeated_due_waiting_does_not_duplicate_action(self) -> None:
        repo = make_repo(questions=tuple(make_open_question(field_code, question_id) for field_code, question_id in QUESTION_FIXTURES))
        reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-14T10:00:00Z",
        )
        reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-21T10:00:00Z",
        )

        result = reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-21T10:05:00Z",
        )

        self.assertEqual(result.created_action_ids, ())
        self.assertEqual(len(repo.load_case_snapshot(1).workflow_actions), 1)

    def test_full_response_before_due_cancels_scheduled_follow_up(self) -> None:
        repo = make_repo(questions=tuple(make_open_question(field_code, question_id) for field_code, question_id in QUESTION_FIXTURES))
        reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-14T10:00:00Z",
        )

        resolve_questions(repo, 1, 2, 3, 4)
        result = reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-20T12:00:00Z",
        )

        snapshot = repo.load_case_snapshot(1)
        self.assertEqual(result.created_action_ids, ())
        self.assertEqual(len(result.cancelled_follow_up_ids), 1)
        self.assertEqual(snapshot.follow_ups[0].status, FOLLOW_UP_STATUS_CANCELLED)

    def test_partial_response_before_due_refreshes_follow_up_context_without_action(self) -> None:
        repo = make_repo(questions=tuple(make_open_question(field_code, question_id) for field_code, question_id in QUESTION_FIXTURES))
        reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-14T10:00:00Z",
        )

        resolve_questions(repo, 2, 4)
        result = reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-20T12:00:00Z",
        )

        snapshot = repo.load_case_snapshot(1)
        self.assertEqual(result.created_action_ids, ())
        self.assertEqual(snapshot.follow_ups[0].status, FOLLOW_UP_STATUS_SCHEDULED)
        self.assertEqual(snapshot.follow_ups[0].context_payload["open_question_ids"], [1, 3])
        self.assertEqual(snapshot.workflow_actions, ())

    def test_full_response_cancels_follow_up_and_supersedes_old_action(self) -> None:
        repo = make_repo(questions=tuple(make_open_question(field_code, question_id) for field_code, question_id in QUESTION_FIXTURES))
        reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-14T10:00:00Z",
        )
        reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-21T10:00:00Z",
        )
        original_action_id = repo.load_case_snapshot(1).workflow_actions[0].workflow_action_id

        resolve_questions(repo, 1, 2, 3, 4)
        result = reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-21T10:30:00Z",
        )

        snapshot = repo.load_case_snapshot(1)
        self.assertEqual(len(result.cancelled_follow_up_ids), 1)
        self.assertEqual(len(result.superseded_action_ids), 1)
        self.assertEqual(snapshot.follow_ups[0].status, FOLLOW_UP_STATUS_CANCELLED)
        self.assertEqual(snapshot.workflow_actions[0].status, "superseded")

        execution = execute_workflow_action(
            repo,
            WorkflowActionExecutionRequest(
                rental_case_id=1,
                workflow_action_id=original_action_id,
                actor_reference="system:test",
            ),
            adapter_registry=build_default_fake_execution_registry(),
        )
        self.assertEqual(execution.failure_codes, (EXECUTION_FAILURE_ACTION_SUPERSEDED,))

    def test_partial_response_refreshes_context_and_supersedes_old_action(self) -> None:
        repo = make_repo(questions=tuple(make_open_question(field_code, question_id) for field_code, question_id in QUESTION_FIXTURES))
        reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-14T10:00:00Z",
        )
        reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-21T10:00:00Z",
        )

        resolve_questions(repo, 2, 4)
        result = reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-21T11:00:00Z",
        )

        snapshot = repo.load_case_snapshot(1)
        active_actions = [action for action in snapshot.workflow_actions if action.status not in {"superseded", "cancelled", "failed", "succeeded"}]
        self.assertEqual(len(result.created_action_ids), 1)
        self.assertEqual(len(result.superseded_action_ids), 1)
        self.assertEqual(snapshot.follow_ups[0].context_payload["open_question_ids"], [1, 3])
        self.assertEqual(active_actions[0].structured_payload["open_question_ids"], [1, 3])

    def test_second_follow_up_sequence_advances_without_duplicates(self) -> None:
        repo = make_repo(questions=tuple(make_open_question(field_code, question_id) for field_code, question_id in QUESTION_FIXTURES))
        reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-14T10:00:00Z",
        )

        result = reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-28T10:00:00Z",
        )

        snapshot = repo.load_case_snapshot(1)
        active_follow_ups = [follow_up for follow_up in snapshot.follow_ups if follow_up.status != FOLLOW_UP_STATUS_CANCELLED]
        self.assertEqual(len(result.cancelled_follow_up_ids), 1)
        self.assertEqual(len(result.created_follow_up_ids), 1)
        self.assertEqual(len(active_follow_ups), 1)
        self.assertEqual(active_follow_ups[0].sequence_number, 2)

    def test_time_critical_inquiry_escalates_to_internal_task(self) -> None:
        repo = make_repo(
            questions=(make_open_question("guest_count", 2),),
            active_event_start="2026-08-16T12:00:00Z",
        )

        result = reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-14T10:00:00Z",
        )

        snapshot = repo.load_case_snapshot(1)
        self.assertTrue(result.plan.escalation_required)
        self.assertEqual(snapshot.follow_ups[0].status, FOLLOW_UP_STATUS_ESCALATED)
        self.assertEqual(snapshot.workflow_actions[0].action_type, ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM)

    def test_stale_case_revision_is_rejected(self) -> None:
        repo = make_repo(questions=(make_open_question("guest_count", 2),))

        result = reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            expected_case_revision=99,
            now=lambda: "2026-08-14T10:00:00Z",
        )

        self.assertEqual(result.failure_codes, (INQUIRY_WAITING_FAILURE_STALE_CASE_REVISION,))
        self.assertEqual(repo.load_case_snapshot(1).follow_ups, ())

    def test_terminal_case_does_not_create_inquiry_follow_up(self) -> None:
        repo = make_repo(questions=(make_open_question("guest_count", 2),))
        repo.rental_cases[1] = replace(repo.rental_cases[1], lifecycle_state=LIFECYCLE_STATE_CLOSED_LOST)

        result = reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-14T10:00:00Z",
        )

        self.assertFalse(result.plan.waiting_required)
        self.assertEqual(result.created_follow_up_ids, ())
        self.assertEqual(repo.load_case_snapshot(1).follow_ups, ())

    def test_case_scoped_waiting_does_not_mutate_other_cases(self) -> None:
        repo = make_repo(questions=(make_open_question("guest_count", 2),))
        repo.rental_cases[2] = replace(make_case(), rental_case_id=2, rental_case_uuid="case-2", case_reference_code="RC-1102")
        repo.open_questions[2] = []
        repo.rental_case_facts[2] = []
        repo.blockers[2] = []
        repo.requirements[2] = []
        repo.approval_requests[2] = []
        repo.proposed_changes[2] = []
        repo.reschedule_requests[2] = []
        repo.case_decisions[2] = []
        repo.workflow_actions[2] = []
        repo.execution_attempts[2] = []
        repo.follow_ups[2] = [
            FollowUp(
                follow_up_id=200,
                rental_case_id=2,
                reason_code="proposal_response",
                due_at="2026-08-20T10:00:00Z",
                urgency_level="medium",
                attempt_count=0,
                status=FOLLOW_UP_STATUS_SCHEDULED,
                created_at="2026-08-14T09:00:00Z",
                updated_at="2026-08-14T09:00:00Z",
            )
        ]
        repo.milestones[2] = []
        repo.artifacts[2] = []
        repo.reasoning_projections[2] = []
        repo.workflow_events[2] = []

        reconcile_inquiry_waiting(
            repo,
            rental_case_id=1,
            actor_reference="system:test",
            actor_type="system",
            now=lambda: "2026-08-14T10:00:00Z",
        )

        other_snapshot = repo.load_case_snapshot(2)
        self.assertEqual(len(other_snapshot.follow_ups), 1)
        self.assertEqual(other_snapshot.follow_ups[0].follow_up_id, 200)
        self.assertEqual(other_snapshot.workflow_actions, ())


if __name__ == "__main__":
    unittest.main()
