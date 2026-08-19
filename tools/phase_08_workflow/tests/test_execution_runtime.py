from __future__ import annotations

import unittest

from tools.phase_08_workflow.contracts import (
    ACTION_CATEGORY_COMMUNICATION,
    ACTION_CATEGORY_COORDINATION,
    ACTION_CATEGORY_FOLLOW_UP,
    ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
    ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
    ACTION_TYPE_SCHEDULE_FOLLOW_UP_REVIEW,
    APPROVAL_POSTURE_AUTOMATIC_ALLOWED,
    APPROVAL_POSTURE_HUMAN_ONLY,
    FOLLOW_UP_STATUS_CANCELLED,
    FOLLOW_UP_STATUS_COMPLETED,
    FOLLOW_UP_STATUS_DUE,
    FOLLOW_UP_STATUS_ESCALATED,
    FOLLOW_UP_STATUS_OVERDUE,
    FOLLOW_UP_STATUS_SCHEDULED,
    FOLLOW_UP_URGENCY_MEDIUM,
    LIFECYCLE_STATE_PROPOSAL_IN_PROGRESS,
    WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
    WORKFLOW_ACTION_STATUS_SUCCEEDED,
    FollowUp,
    RentalCase,
    WorkflowAction,
)
from tools.phase_08_workflow.execution_runtime import (
    ExecutionAdapterRegistry,
    build_default_fake_execution_registry,
    evaluate_due_follow_ups,
    execute_workflow_action,
    fake_exception_adapter,
    fake_malformed_adapter,
    fake_retryable_failure_adapter,
    fake_success_adapter,
)
from tools.phase_08_workflow.execution_types import (
    EXECUTION_FAILURE_ACTION_ALREADY_SUCCEEDED,
    EXECUTION_FAILURE_ACTION_HUMAN_ONLY,
    EXECUTION_FAILURE_ADAPTER_RESULT_MALFORMED,
    EXECUTION_FAILURE_ADAPTER_UNAVAILABLE,
    FollowUpEvaluationRequest,
    WorkflowActionExecutionRequest,
)
from tools.phase_08_workflow.orchestration_repository import InMemoryWorkflowOrchestrationRepository


def make_case(*, case_revision: int = 0, rental_case_id: int = 1) -> RentalCase:
    return RentalCase(
        rental_case_id=rental_case_id,
        rental_case_uuid=f"case-{rental_case_id}",
        case_reference_code=f"RC-{900 + rental_case_id}",
        lifecycle_state=LIFECYCLE_STATE_PROPOSAL_IN_PROGRESS,
        case_revision=case_revision,
        rental_type_code="studio_space",
        commercial_summary_status="unknown",
        operational_summary_status="unknown",
        is_active=True,
        service_level_or_type="studio_rental",
        client_account_ref="client:1",
        primary_contact_ref="contact:1",
        created_at="2026-08-13T10:00:00Z",
        updated_at="2026-08-13T10:00:00Z",
    )


def make_repo(
    rental_case: RentalCase,
    *,
    actions=(),
    attempts=(),
    follow_ups=(),
) -> InMemoryWorkflowOrchestrationRepository:
    rental_case_id = rental_case.rental_case_id
    return InMemoryWorkflowOrchestrationRepository(
        rental_cases={rental_case_id: rental_case},
        rental_case_facts={rental_case_id: []},
        blockers={rental_case_id: []},
        requirements={rental_case_id: []},
        open_questions={rental_case_id: []},
        approval_requests={rental_case_id: []},
        proposed_changes={rental_case_id: []},
        reschedule_requests={rental_case_id: []},
        case_decisions={rental_case_id: []},
        workflow_actions={rental_case_id: list(actions)},
        execution_attempts={rental_case_id: list(attempts)},
        follow_ups={rental_case_id: list(follow_ups)},
        milestones={rental_case_id: []},
        artifacts={rental_case_id: []},
        reasoning_projections={rental_case_id: []},
        workflow_events={rental_case_id: []},
    )


def make_client_action(
    action_id: int,
    *,
    status: str = WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
    approval_posture: str = APPROVAL_POSTURE_AUTOMATIC_ALLOWED,
    target_adapter_code: str = "email",
    source_case_revision: int = 0,
) -> WorkflowAction:
    return WorkflowAction(
        workflow_action_id=action_id,
        workflow_action_uuid=f"action-{action_id}",
        rental_case_id=1,
        action_type=ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
        action_category=ACTION_CATEGORY_COMMUNICATION,
        target_adapter_code=target_adapter_code,
        reason_entity_type="open_question",
        reason_entity_reference=f"open_question:{action_id}",
        approval_posture=approval_posture,
        status=status,
        semantic_subject_hash=f"subject:{action_id}",
        source_case_revision=source_case_revision,
        idempotency_key=f"idem:{action_id}",
        structured_payload={
            "open_question_ids": [action_id],
            "required_field_codes": ["guest_count"],
            "intended_recipient_role": "client",
            "purpose": "Collect missing event details.",
            "reason": "Guest count is still unresolved.",
        },
        created_at="2026-08-13T10:00:00Z",
        updated_at="2026-08-13T10:00:00Z",
    )


def make_internal_action(
    action_id: int,
    *,
    target_adapter_code: str = "internal",
    status: str = WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
) -> WorkflowAction:
    return WorkflowAction(
        workflow_action_id=action_id,
        workflow_action_uuid=f"action-{action_id}",
        rental_case_id=1,
        action_type=ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
        action_category=ACTION_CATEGORY_COORDINATION,
        target_adapter_code=target_adapter_code,
        reason_entity_type="review_item",
        reason_entity_reference=f"review_item:{action_id}",
        approval_posture=APPROVAL_POSTURE_AUTOMATIC_ALLOWED,
        status=status,
        semantic_subject_hash=f"subject:{action_id}",
        source_case_revision=0,
        idempotency_key=f"idem:{action_id}",
        structured_payload={
            "task_kind": "follow_up_review",
            "summary": "Review overdue follow-up.",
            "reason": "The case needs structured human review.",
        },
        created_at="2026-08-13T10:00:00Z",
        updated_at="2026-08-13T10:00:00Z",
    )


def make_follow_up_action(action_id: int, follow_up_id: int) -> WorkflowAction:
    return WorkflowAction(
        workflow_action_id=action_id,
        workflow_action_uuid=f"action-{action_id}",
        rental_case_id=1,
        action_type=ACTION_TYPE_SCHEDULE_FOLLOW_UP_REVIEW,
        action_category=ACTION_CATEGORY_FOLLOW_UP,
        target_adapter_code="internal",
        reason_entity_type="follow_up",
        reason_entity_id=follow_up_id,
        reason_entity_reference=f"follow_up:{follow_up_id}",
        approval_posture=APPROVAL_POSTURE_AUTOMATIC_ALLOWED,
        status=WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
        semantic_subject_hash=f"subject:{action_id}",
        source_case_revision=0,
        idempotency_key=f"idem:{action_id}",
        structured_payload={
            "follow_up_id": follow_up_id,
            "reason_code": "proposal_response",
            "due_at": "2026-08-12T10:00:00Z",
        },
        created_at="2026-08-13T10:00:00Z",
        updated_at="2026-08-13T10:00:00Z",
    )


def make_follow_up(
    follow_up_id: int,
    *,
    status: str = FOLLOW_UP_STATUS_SCHEDULED,
    due_at: str = "2026-08-12T10:00:00Z",
    attempt_count: int = 0,
    escalate_after: int | None = None,
) -> FollowUp:
    return FollowUp(
        follow_up_id=follow_up_id,
        rental_case_id=1,
        reason_code="proposal_response",
        due_at=due_at,
        urgency_level=FOLLOW_UP_URGENCY_MEDIUM,
        attempt_count=attempt_count,
        status=status,
        waiting_for_role="client",
        waiting_for_reference="contact:1",
        cadence_policy_code="weekly",
        escalate_after=escalate_after,
        next_action_type=ACTION_TYPE_SCHEDULE_FOLLOW_UP_REVIEW,
        created_at="2026-08-13T10:00:00Z",
        updated_at="2026-08-13T10:00:00Z",
    )


class ExecutionRuntimeTests(unittest.TestCase):
    def test_executes_ready_action_through_fake_adapter(self) -> None:
        repo = make_repo(make_case(), actions=(make_client_action(1),))
        registry = build_default_fake_execution_registry()

        result = execute_workflow_action(
            repo,
            WorkflowActionExecutionRequest(
                rental_case_id=1,
                workflow_action_id=1,
                actor_reference="system:test",
            ),
            adapter_registry=registry,
            now=lambda: "2026-08-13T12:00:00Z",
        )

        self.assertEqual(result.action_status_after, WORKFLOW_ACTION_STATUS_SUCCEEDED)
        self.assertEqual(result.attempt_status, "succeeded")
        self.assertIsNotNone(result.execution_attempt_id)
        self.assertEqual(repo.load_case_snapshot(1).find_workflow_action(1).status, WORKFLOW_ACTION_STATUS_SUCCEEDED)
        attempts = repo.list_execution_attempts(rental_case_id=1, workflow_action_id=1)
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0].status, "succeeded")

    def test_default_fake_registry_uses_injected_now(self) -> None:
        repo = make_repo(make_case(), actions=(make_client_action(8),))

        execute_workflow_action(
            repo,
            WorkflowActionExecutionRequest(
                rental_case_id=1,
                workflow_action_id=8,
                actor_reference="system:test",
            ),
            now=lambda: "2026-08-13T12:34:56Z",
        )

        attempts = repo.list_execution_attempts(rental_case_id=1, workflow_action_id=8)
        self.assertEqual(attempts[0].completed_at, "2026-08-13T12:34:56Z")

    def test_human_only_action_never_invokes_adapter(self) -> None:
        repo = make_repo(
            make_case(),
            actions=(make_client_action(2, approval_posture=APPROVAL_POSTURE_HUMAN_ONLY),),
        )
        adapter = fake_success_adapter("email")
        registry = ExecutionAdapterRegistry({"email": adapter})

        result = execute_workflow_action(
            repo,
            WorkflowActionExecutionRequest(
                rental_case_id=1,
                workflow_action_id=2,
                actor_reference="system:test",
            ),
            adapter_registry=registry,
        )

        self.assertEqual(result.failure_codes, (EXECUTION_FAILURE_ACTION_HUMAN_ONLY,))
        self.assertEqual(adapter.invocations, [])
        self.assertEqual(repo.list_execution_attempts(rental_case_id=1, workflow_action_id=2), ())

    def test_retryable_failure_returns_action_to_ready_to_execute(self) -> None:
        repo = make_repo(make_case(), actions=(make_client_action(3),))
        retry_registry = ExecutionAdapterRegistry({"email": fake_retryable_failure_adapter("email")})

        first = execute_workflow_action(
            repo,
            WorkflowActionExecutionRequest(
                rental_case_id=1,
                workflow_action_id=3,
                actor_reference="system:test",
            ),
            adapter_registry=retry_registry,
        )
        self.assertEqual(first.action_status_after, WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE)
        self.assertEqual(first.attempt_status, "failed")
        self.assertTrue(first.retry_eligible)

        second = execute_workflow_action(
            repo,
            WorkflowActionExecutionRequest(
                rental_case_id=1,
                workflow_action_id=3,
                actor_reference="system:test",
            ),
            adapter_registry=ExecutionAdapterRegistry({"email": fake_success_adapter("email")}),
        )
        attempts = repo.list_execution_attempts(rental_case_id=1, workflow_action_id=3)
        self.assertEqual(len(attempts), 2)
        self.assertEqual(tuple(attempt.attempt_number for attempt in attempts), (1, 2))
        self.assertEqual(second.action_status_after, WORKFLOW_ACTION_STATUS_SUCCEEDED)

    def test_unavailable_adapter_rejects_before_attempt_creation(self) -> None:
        repo = make_repo(make_case(), actions=(make_internal_action(4, target_adapter_code="fax"),))

        result = execute_workflow_action(
            repo,
            WorkflowActionExecutionRequest(
                rental_case_id=1,
                workflow_action_id=4,
                actor_reference="system:test",
            ),
            adapter_registry=build_default_fake_execution_registry(),
        )

        self.assertEqual(result.failure_codes, (EXECUTION_FAILURE_ADAPTER_UNAVAILABLE,))
        self.assertEqual(repo.list_execution_attempts(rental_case_id=1, workflow_action_id=4), ())

    def test_malformed_adapter_result_never_becomes_success(self) -> None:
        repo = make_repo(make_case(), actions=(make_internal_action(5),))
        registry = ExecutionAdapterRegistry({"internal": fake_malformed_adapter("internal")})

        result = execute_workflow_action(
            repo,
            WorkflowActionExecutionRequest(
                rental_case_id=1,
                workflow_action_id=5,
                actor_reference="system:test",
            ),
            adapter_registry=registry,
            now=lambda: "2026-08-13T12:00:00Z",
        )

        attempts = repo.list_execution_attempts(rental_case_id=1, workflow_action_id=5)
        self.assertEqual(result.attempt_status, "failed")
        self.assertEqual(result.action_status_after, "failed")
        self.assertEqual(attempts[0].failure_code, EXECUTION_FAILURE_ADAPTER_RESULT_MALFORMED)

    def test_adapter_exception_does_not_count_as_success(self) -> None:
        repo = make_repo(make_case(), actions=(make_internal_action(6),))
        registry = ExecutionAdapterRegistry({"internal": fake_exception_adapter("internal")})

        result = execute_workflow_action(
            repo,
            WorkflowActionExecutionRequest(
                rental_case_id=1,
                workflow_action_id=6,
                actor_reference="system:test",
            ),
            adapter_registry=registry,
        )

        attempts = repo.list_execution_attempts(rental_case_id=1, workflow_action_id=6)
        self.assertEqual(result.attempt_status, "failed")
        self.assertEqual(result.action_status_after, WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE)
        self.assertTrue(attempts[0].retry_eligible)

    def test_already_succeeded_action_is_idempotent_no_op(self) -> None:
        repo = make_repo(
            make_case(),
            actions=(make_client_action(7, status=WORKFLOW_ACTION_STATUS_SUCCEEDED),),
        )
        adapter = fake_success_adapter("email")
        registry = ExecutionAdapterRegistry({"email": adapter})

        result = execute_workflow_action(
            repo,
            WorkflowActionExecutionRequest(
                rental_case_id=1,
                workflow_action_id=7,
                actor_reference="system:test",
            ),
            adapter_registry=registry,
        )

        self.assertEqual(result.failure_codes, (EXECUTION_FAILURE_ACTION_ALREADY_SUCCEEDED,))
        self.assertTrue(result.already_succeeded_idempotently)
        self.assertEqual(adapter.invocations, [])
        self.assertEqual(repo.list_execution_attempts(rental_case_id=1, workflow_action_id=7), ())

    def test_due_follow_up_routes_into_orchestration_without_execution(self) -> None:
        repo = make_repo(make_case(), follow_ups=(make_follow_up(11),))

        first = evaluate_due_follow_ups(
            repo,
            FollowUpEvaluationRequest(
                rental_case_id=1,
                actor_reference="system:test",
                now="2026-08-13T12:00:00Z",
            ),
        )
        second = evaluate_due_follow_ups(
            repo,
            FollowUpEvaluationRequest(
                rental_case_id=1,
                actor_reference="system:test",
                now="2026-08-13T12:05:00Z",
            ),
        )

        snapshot = repo.load_case_snapshot(1)
        self.assertEqual(first.updated_follow_up_ids, (11,))
        self.assertEqual(first.due_follow_up_ids, (11,))
        self.assertEqual(len(first.created_action_ids), 1)
        self.assertEqual(len(snapshot.workflow_actions), 1)
        self.assertEqual(repo.list_execution_attempts(rental_case_id=1), ())
        self.assertEqual(second.created_action_ids, ())
        self.assertEqual(len(repo.load_case_snapshot(1).workflow_actions), 1)

    def test_due_follow_up_reuses_snapshot_loads_during_reconciliation(self) -> None:
        repo = make_repo(make_case(), follow_ups=(make_follow_up(12),))
        original_load_case_snapshot = repo.load_case_snapshot
        load_case_snapshot_call_count = 0

        def counted_load_case_snapshot(rental_case_id: int):
            nonlocal load_case_snapshot_call_count
            load_case_snapshot_call_count += 1
            return original_load_case_snapshot(rental_case_id)

        repo.load_case_snapshot = counted_load_case_snapshot  # type: ignore[assignment]

        result = evaluate_due_follow_ups(
            repo,
            FollowUpEvaluationRequest(
                rental_case_id=1,
                actor_reference="system:test",
                now="2026-08-13T12:00:00Z",
            ),
        )

        self.assertEqual(result.failure_codes, ())
        self.assertEqual(len(result.created_action_ids), 1)
        self.assertLessEqual(load_case_snapshot_call_count, 4)

    def test_terminal_follow_ups_are_not_reactivated(self) -> None:
        repo = make_repo(
            make_case(),
            follow_ups=(
                make_follow_up(21, status=FOLLOW_UP_STATUS_COMPLETED),
                make_follow_up(22, status=FOLLOW_UP_STATUS_CANCELLED),
            ),
        )

        result = evaluate_due_follow_ups(
            repo,
            FollowUpEvaluationRequest(
                rental_case_id=1,
                actor_reference="system:test",
                now="2026-08-13T12:00:00Z",
            ),
        )

        self.assertEqual(result.updated_follow_up_ids, ())
        self.assertEqual(result.created_action_ids, ())
        self.assertEqual(repo.load_case_snapshot(1).workflow_actions, ())

    def test_follow_up_execution_success_marks_follow_up_completed(self) -> None:
        repo = make_repo(
            make_case(),
            actions=(make_follow_up_action(31, 31),),
            follow_ups=(make_follow_up(31, status=FOLLOW_UP_STATUS_DUE),),
        )

        result = execute_workflow_action(
            repo,
            WorkflowActionExecutionRequest(
                rental_case_id=1,
                workflow_action_id=31,
                actor_reference="system:test",
            ),
            adapter_registry=ExecutionAdapterRegistry({"internal": fake_success_adapter("internal")}),
            now=lambda: "2026-08-13T12:00:00Z",
        )

        snapshot = repo.load_case_snapshot(1)
        follow_up = snapshot.find_follow_up(31)
        self.assertEqual(result.action_status_after, WORKFLOW_ACTION_STATUS_SUCCEEDED)
        self.assertEqual(follow_up.status, FOLLOW_UP_STATUS_COMPLETED)
        self.assertEqual(follow_up.attempt_count, 1)

    def test_overdue_follow_up_can_escalate(self) -> None:
        repo = make_repo(
            make_case(),
            follow_ups=(make_follow_up(41, attempt_count=1, escalate_after=1),),
        )

        result = evaluate_due_follow_ups(
            repo,
            FollowUpEvaluationRequest(
                rental_case_id=1,
                actor_reference="system:test",
                now="2026-08-13T12:00:00Z",
            ),
        )

        self.assertEqual(result.escalated_follow_up_ids, (41,))
        self.assertEqual(repo.load_case_snapshot(1).find_follow_up(41).status, FOLLOW_UP_STATUS_ESCALATED)

    def test_attempted_follow_up_without_escalation_becomes_overdue(self) -> None:
        repo = make_repo(
            make_case(),
            follow_ups=(make_follow_up(42, attempt_count=1, escalate_after=3),),
        )

        result = evaluate_due_follow_ups(
            repo,
            FollowUpEvaluationRequest(
                rental_case_id=1,
                actor_reference="system:test",
                now="2026-08-13T12:00:00Z",
            ),
        )

        self.assertEqual(result.overdue_follow_up_ids, (42,))
        self.assertEqual(repo.load_case_snapshot(1).find_follow_up(42).status, FOLLOW_UP_STATUS_OVERDUE)


if __name__ == "__main__":
    unittest.main()
