from __future__ import annotations

import json
import unittest

from tools.phase_08_workflow.asana_adapter import (
    AsanaAdapterConfig,
    AsanaAmbiguousTransportError,
    AsanaExecutionAdapter,
    _build_asana_task_payload,
)
from tools.phase_08_workflow.contracts import (
    ACTION_CATEGORY_COMMUNICATION,
    ACTION_CATEGORY_COORDINATION,
    ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
    ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
    APPROVAL_POSTURE_APPROVAL_REQUIRED,
    APPROVAL_POSTURE_AUTOMATIC_ALLOWED,
    APPROVAL_POSTURE_BLOCKED,
    APPROVAL_POSTURE_HUMAN_ONLY,
    EXECUTION_ATTEMPT_STATUS_SUCCEEDED,
    LIFECYCLE_STATE_PROPOSAL_IN_PROGRESS,
    WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
    WORKFLOW_ACTION_STATUS_CANCELLED,
    WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
    WORKFLOW_ACTION_STATUS_SUCCEEDED,
    WORKFLOW_ACTION_STATUS_SUPERSEDED,
    RentalCase,
    WorkflowAction,
)
from tools.phase_08_workflow.execution_runtime import ExecutionAdapterRegistry, execute_workflow_action
from tools.phase_08_workflow.execution_types import (
    EXECUTION_FAILURE_ACTION_ALREADY_SUCCEEDED,
    EXECUTION_FAILURE_ACTION_BLOCKED,
    EXECUTION_FAILURE_ACTION_HUMAN_ONLY,
    EXECUTION_FAILURE_ACTION_NOT_EXECUTION_READY,
    EXECUTION_FAILURE_ACTION_STALE_REVISION,
    EXECUTION_FAILURE_ACTION_SUPERSEDED,
    EXECUTION_FAILURE_ADAPTER_AUTHENTICATION_FAILED,
    EXECUTION_FAILURE_ADAPTER_CONFIGURATION_INVALID,
    EXECUTION_FAILURE_ADAPTER_FORBIDDEN,
    EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS,
    EXECUTION_FAILURE_ADAPTER_RATE_LIMITED,
    EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID,
    EXECUTION_FAILURE_ADAPTER_RESOURCE_NOT_FOUND,
    EXECUTION_FAILURE_ADAPTER_RESULT_MALFORMED,
    EXECUTION_FAILURE_ADAPTER_SERVER_ERROR,
    EXECUTION_FAILURE_EXTERNAL_REFERENCE_CONFLICT,
    ExecutionContext,
    ExecutionIdempotencyContext,
    WorkflowActionExecutionRequest,
)
from tools.phase_08_workflow.orchestration_repository import InMemoryWorkflowOrchestrationRepository


def make_case(*, rental_case_id: int = 1, case_revision: int = 0) -> RentalCase:
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
        client_account_ref=f"client:{rental_case_id}",
        primary_contact_ref=f"contact:{rental_case_id}",
        created_at="2026-08-13T10:00:00Z",
        updated_at="2026-08-13T10:00:00Z",
    )


def make_repo(*cases: RentalCase, actions: tuple[WorkflowAction, ...]) -> InMemoryWorkflowOrchestrationRepository:
    return InMemoryWorkflowOrchestrationRepository(
        rental_cases={case.rental_case_id: case for case in cases},
        rental_case_facts={case.rental_case_id: [] for case in cases},
        blockers={case.rental_case_id: [] for case in cases},
        requirements={case.rental_case_id: [] for case in cases},
        open_questions={case.rental_case_id: [] for case in cases},
        approval_requests={case.rental_case_id: [] for case in cases},
        proposed_changes={case.rental_case_id: [] for case in cases},
        reschedule_requests={case.rental_case_id: [] for case in cases},
        case_decisions={case.rental_case_id: [] for case in cases},
        workflow_actions={
            case.rental_case_id: [action for action in actions if action.rental_case_id == case.rental_case_id]
            for case in cases
        },
        execution_attempts={case.rental_case_id: [] for case in cases},
        follow_ups={case.rental_case_id: [] for case in cases},
        milestones={case.rental_case_id: [] for case in cases},
        artifacts={case.rental_case_id: [] for case in cases},
        reasoning_projections={case.rental_case_id: [] for case in cases},
        workflow_events={case.rental_case_id: [] for case in cases},
    )


def make_asana_action(
    action_id: int,
    *,
    rental_case_id: int = 1,
    status: str = WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
    approval_posture: str = APPROVAL_POSTURE_AUTOMATIC_ALLOWED,
    source_case_revision: int = 0,
    target_adapter_code: str = "asana",
    structured_payload: dict[str, object] | None = None,
) -> WorkflowAction:
    payload = {
        "task_kind": "follow_up_review",
        "summary": "Review overdue follow-up.",
        "reason": "The case needs structured human review.",
    }
    if structured_payload is not None:
        payload.update(structured_payload)
    return WorkflowAction(
        workflow_action_id=action_id,
        workflow_action_uuid=f"action-{action_id}",
        rental_case_id=rental_case_id,
        action_type=ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
        action_category=ACTION_CATEGORY_COORDINATION,
        target_adapter_code=target_adapter_code,
        reason_entity_type="review_item",
        reason_entity_reference=f"review_item:{action_id}",
        approval_posture=approval_posture,
        status=status,
        semantic_subject_hash=f"subject:{action_id}",
        source_case_revision=source_case_revision,
        idempotency_key=f"idem:{action_id}",
        structured_payload=payload,
        created_at="2026-08-13T10:00:00Z",
        updated_at="2026-08-13T10:00:00Z",
    )


def make_client_action(
    action_id: int,
    *,
    rental_case_id: int = 1,
    approval_posture: str = APPROVAL_POSTURE_HUMAN_ONLY,
) -> WorkflowAction:
    return WorkflowAction(
        workflow_action_id=action_id,
        workflow_action_uuid=f"action-{action_id}",
        rental_case_id=rental_case_id,
        action_type=ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
        action_category=ACTION_CATEGORY_COMMUNICATION,
        target_adapter_code="asana",
        reason_entity_type="open_question",
        reason_entity_reference=f"open_question:{action_id}",
        approval_posture=approval_posture,
        status=WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
        semantic_subject_hash=f"subject:{action_id}",
        source_case_revision=0,
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


def make_execution_context() -> ExecutionContext:
    return ExecutionContext(
        rental_case_id=1,
        workflow_action_id=1,
        current_case_revision=0,
        actor_reference="system:test",
        case_reference_code="RC-901",
        actor_type="system",
        started_at="2026-08-13T12:00:00Z",
    )


def make_idempotency() -> ExecutionIdempotencyContext:
    return ExecutionIdempotencyContext(
        workflow_action_id=1,
        execution_attempt_id=101,
        attempt_number=1,
        semantic_idempotency_key="idem:1",
    )


class StubAsanaTransport:
    def __init__(
        self,
        *,
        response: tuple[int, str, dict[str, str]] | None = None,
        exception: Exception | None = None,
    ) -> None:
        self.response = response
        self.exception = exception
        self.requests: list[dict[str, object]] = []

    def send_json(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        payload: dict[str, object],
        timeout_seconds: int,
    ) -> tuple[int, str, dict[str, str]]:
        self.requests.append(
            {
                "method": method,
                "url": url,
                "headers": dict(headers),
                "payload": payload,
                "timeout_seconds": timeout_seconds,
            }
        )
        if self.exception is not None:
            raise self.exception
        if self.response is None:
            raise AssertionError("StubAsanaTransport requires a response or exception.")
        return self.response


class AsanaAdapterTests(unittest.TestCase):
    def test_build_task_payload_maps_supported_fields_only(self) -> None:
        action = make_asana_action(
            1,
            structured_payload={
                "task_surface_project_id": "project-321",
                "task_surface_section_id": "section-654",
                "task_surface_assignee_id": "user-777",
                "task_surface_due_on": "2026-08-20",
                "task_surface_context_lines": ["Need policy review", "Check booking fee exception"],
            },
        )

        payload = _build_asana_task_payload(
            action=action,
            execution_context=make_execution_context(),
            workspace_gid="workspace-123",
            default_project_gid="default-project",
        )

        self.assertEqual(
            payload,
            {
                "name": "Review overdue follow-up.",
                "notes": (
                    "The case needs structured human review.\n\n"
                    "Context:\n"
                    "- Need policy review\n"
                    "- Check booking fee exception\n\n"
                    "Rental Case: RC-901\n"
                    "Rental Case ID: 1\n"
                    "Workflow Action ID: 1\n"
                    "Workflow Action UUID: action-1\n"
                    "Action Type: CREATE_INTERNAL_TASK_ITEM\n"
                    "Task Kind: follow_up_review\n"
                    "Semantic Idempotency Key: idem:1"
                ),
                "workspace": "workspace-123",
                "memberships": [{"project": "project-321", "section": "section-654"}],
                "assignee": "user-777",
                "due_on": "2026-08-20",
            },
        )

    def test_build_task_payload_rejects_invalid_context_lines(self) -> None:
        action = make_asana_action(1, structured_payload={"task_surface_context_lines": "not-a-list"})

        with self.assertRaises(Exception) as cm:
            _build_asana_task_payload(
                action=action,
                execution_context=make_execution_context(),
                workspace_gid="workspace-123",
                default_project_gid="default-project",
            )
        self.assertEqual(getattr(cm.exception, "reason", None), "task_surface_context_lines_must_be_list")

    def test_config_availability_requires_supported_action_and_configuration(self) -> None:
        config = AsanaAdapterConfig(
            access_token=None,
            workspace_gid="workspace-123",
            default_project_gid="project-321",
        )
        self.assertEqual(
            config.availability_failure_code(action=make_asana_action(1)),
            EXECUTION_FAILURE_ADAPTER_CONFIGURATION_INVALID,
        )
        self.assertEqual(
            AsanaAdapterConfig(
                access_token="token",
                workspace_gid="workspace-123",
                default_project_gid="project-321",
            ).availability_failure_code(action=make_client_action(9, approval_posture=APPROVAL_POSTURE_AUTOMATIC_ALLOWED)),
            EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID,
        )

    def test_execute_success_returns_verified_task_gid(self) -> None:
        transport = StubAsanaTransport(
            response=(201, json.dumps({"data": {"gid": "task-789"}}), {"Content-Type": "application/json"})
        )
        adapter = AsanaExecutionAdapter(
            config=AsanaAdapterConfig(
                access_token="secret-token",
                workspace_gid="workspace-123",
                default_project_gid="project-321",
            ),
            transport=transport,
        )

        result = adapter.execute(
            action=make_asana_action(1),
            execution_context=make_execution_context(),
            idempotency=make_idempotency(),
        )

        self.assertEqual(result.attempt_status, EXECUTION_ATTEMPT_STATUS_SUCCEEDED)
        self.assertEqual(result.external_reference, "asana:task:task-789")
        request = transport.requests[0]
        self.assertEqual(request["method"], "POST")
        self.assertEqual(request["url"], "https://app.asana.com/api/1.0/tasks")
        self.assertEqual(request["payload"], {"data": _build_asana_task_payload(
            action=make_asana_action(1),
            execution_context=make_execution_context(),
            workspace_gid="workspace-123",
            default_project_gid="project-321",
        )})
        self.assertNotIn("secret-token", json.dumps(result.response_snapshot, sort_keys=True))

    def test_execute_success_missing_gid_fails(self) -> None:
        adapter = AsanaExecutionAdapter(
            config=AsanaAdapterConfig(
                access_token="token",
                workspace_gid="workspace-123",
                default_project_gid="project-321",
            ),
            transport=StubAsanaTransport(
                response=(201, json.dumps({"data": {"name": "Task without gid"}}), {"Content-Type": "application/json"})
            ),
        )

        result = adapter.execute(
            action=make_asana_action(1),
            execution_context=make_execution_context(),
            idempotency=make_idempotency(),
        )

        self.assertEqual(result.failure_code, EXECUTION_FAILURE_ADAPTER_RESULT_MALFORMED)
        self.assertFalse(result.retry_eligible)

    def test_execute_invalid_json_fails(self) -> None:
        adapter = AsanaExecutionAdapter(
            config=AsanaAdapterConfig(
                access_token="token",
                workspace_gid="workspace-123",
                default_project_gid="project-321",
            ),
            transport=StubAsanaTransport(response=(201, "{not-json", {"Content-Type": "application/json"})),
        )

        result = adapter.execute(
            action=make_asana_action(1),
            execution_context=make_execution_context(),
            idempotency=make_idempotency(),
        )

        self.assertEqual(result.failure_code, EXECUTION_FAILURE_ADAPTER_RESULT_MALFORMED)

    def test_execute_http_failures_are_classified(self) -> None:
        scenarios = (
            (400, EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID, False),
            (401, EXECUTION_FAILURE_ADAPTER_AUTHENTICATION_FAILED, False),
            (403, EXECUTION_FAILURE_ADAPTER_FORBIDDEN, False),
            (404, EXECUTION_FAILURE_ADAPTER_RESOURCE_NOT_FOUND, False),
            (429, EXECUTION_FAILURE_ADAPTER_RATE_LIMITED, True),
            (500, EXECUTION_FAILURE_ADAPTER_SERVER_ERROR, True),
        )
        for status_code, expected_failure_code, expected_retry_eligible in scenarios:
            with self.subTest(status_code=status_code):
                adapter = AsanaExecutionAdapter(
                    config=AsanaAdapterConfig(
                        access_token="token-value",
                        workspace_gid="workspace-123",
                        default_project_gid="project-321",
                    ),
                    transport=StubAsanaTransport(
                        response=(
                            status_code,
                            json.dumps({"errors": [{"message": f"provider-status-{status_code}"}]}),
                            {"Retry-After": "42"} if status_code == 429 else {},
                        )
                    ),
                )

                result = adapter.execute(
                    action=make_asana_action(1),
                    execution_context=make_execution_context(),
                    idempotency=make_idempotency(),
                )

                self.assertEqual(result.failure_code, expected_failure_code)
                self.assertEqual(result.retry_eligible, expected_retry_eligible)
                self.assertNotIn("token-value", json.dumps(result.response_snapshot, sort_keys=True))

    def test_execute_http_failures_preserve_task_surface_alias(self) -> None:
        adapter = AsanaExecutionAdapter(
            config=AsanaAdapterConfig(
                access_token="token-value",
                workspace_gid="workspace-123",
                default_project_gid="project-321",
            ),
            transport=StubAsanaTransport(
                response=(403, json.dumps({"errors": [{"message": "forbidden"}]}), {})
            ),
        )

        result = adapter.execute(
            action=make_asana_action(1, target_adapter_code="task_surface"),
            execution_context=make_execution_context(),
            idempotency=make_idempotency(),
        )

        self.assertEqual(result.adapter_code, "task_surface")
        self.assertEqual(result.failure_code, EXECUTION_FAILURE_ADAPTER_FORBIDDEN)

    def test_execute_timeout_is_ambiguous_and_not_retryable(self) -> None:
        adapter = AsanaExecutionAdapter(
            config=AsanaAdapterConfig(
                access_token="token",
                workspace_gid="workspace-123",
                default_project_gid="project-321",
            ),
            transport=StubAsanaTransport(exception=AsanaAmbiguousTransportError("timeout")),
        )

        result = adapter.execute(
            action=make_asana_action(1),
            execution_context=make_execution_context(),
            idempotency=make_idempotency(),
        )

        self.assertEqual(result.failure_code, EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS)
        self.assertFalse(result.retry_eligible)
        self.assertEqual(result.response_snapshot["reason"], "ambiguous_transport_failure")

    def test_runtime_preflight_rejects_missing_asana_config_before_attempt_creation(self) -> None:
        repo = make_repo(make_case(), actions=(make_asana_action(1),))
        adapter = AsanaExecutionAdapter(
            config=AsanaAdapterConfig(
                access_token=None,
                workspace_gid="workspace-123",
                default_project_gid="project-321",
            ),
            transport=StubAsanaTransport(response=(201, json.dumps({"data": {"gid": "task-1"}}), {})),
        )

        result = execute_workflow_action(
            repo,
            WorkflowActionExecutionRequest(
                rental_case_id=1,
                workflow_action_id=1,
                actor_reference="system:test",
            ),
            adapter_registry=ExecutionAdapterRegistry({"asana": adapter}),
        )

        self.assertEqual(result.failure_codes, (EXECUTION_FAILURE_ADAPTER_CONFIGURATION_INVALID,))
        self.assertEqual(repo.list_execution_attempts(rental_case_id=1, workflow_action_id=1), ())
        self.assertEqual(len(adapter.transport.requests), 0)

    def test_runtime_non_ready_action_never_invokes_asana(self) -> None:
        adapter = AsanaExecutionAdapter(
            config=AsanaAdapterConfig(
                access_token="token",
                workspace_gid="workspace-123",
                default_project_gid="project-321",
            ),
            transport=StubAsanaTransport(response=(201, json.dumps({"data": {"gid": "task-1"}}), {})),
        )
        scenarios = (
            (
                make_asana_action(
                    2,
                    status=WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
                    approval_posture=APPROVAL_POSTURE_APPROVAL_REQUIRED,
                ),
                EXECUTION_FAILURE_ACTION_NOT_EXECUTION_READY,
            ),
            (
                make_asana_action(3, approval_posture=APPROVAL_POSTURE_BLOCKED),
                EXECUTION_FAILURE_ACTION_BLOCKED,
            ),
            (
                make_asana_action(4, status=WORKFLOW_ACTION_STATUS_SUPERSEDED),
                EXECUTION_FAILURE_ACTION_SUPERSEDED,
            ),
            (
                make_asana_action(5, status=WORKFLOW_ACTION_STATUS_CANCELLED),
                "action_cancelled",
            ),
            (
                make_asana_action(6, source_case_revision=99),
                EXECUTION_FAILURE_ACTION_STALE_REVISION,
            ),
        )
        for action, expected_failure in scenarios:
            with self.subTest(action_id=action.workflow_action_id):
                repo = make_repo(make_case(), actions=(action,))
                result = execute_workflow_action(
                    repo,
                    WorkflowActionExecutionRequest(
                        rental_case_id=1,
                        workflow_action_id=action.workflow_action_id,
                        actor_reference="system:test",
                    ),
                    adapter_registry=ExecutionAdapterRegistry({"asana": adapter}),
                )
                self.assertEqual(result.failure_codes, (expected_failure,))
                self.assertEqual(repo.list_execution_attempts(rental_case_id=1, workflow_action_id=action.workflow_action_id), ())
        self.assertEqual(len(adapter.transport.requests), 0)

    def test_runtime_human_only_non_task_action_never_invokes_asana(self) -> None:
        repo = make_repo(make_case(), actions=(make_client_action(10),))
        adapter = AsanaExecutionAdapter(
            config=AsanaAdapterConfig(
                access_token="token",
                workspace_gid="workspace-123",
                default_project_gid="project-321",
            ),
            transport=StubAsanaTransport(response=(201, json.dumps({"data": {"gid": "task-1"}}), {})),
        )

        result = execute_workflow_action(
            repo,
            WorkflowActionExecutionRequest(
                rental_case_id=1,
                workflow_action_id=10,
                actor_reference="system:test",
            ),
            adapter_registry=ExecutionAdapterRegistry({"asana": adapter}),
        )

        self.assertEqual(result.failure_codes, (EXECUTION_FAILURE_ACTION_HUMAN_ONLY,))
        self.assertEqual(repo.list_execution_attempts(rental_case_id=1, workflow_action_id=10), ())
        self.assertEqual(len(adapter.transport.requests), 0)

    def test_runtime_verified_success_is_idempotent_on_repeat_execution(self) -> None:
        transport = StubAsanaTransport(
            response=(201, json.dumps({"data": {"gid": "task-abc"}}), {"Content-Type": "application/json"})
        )
        adapter = AsanaExecutionAdapter(
            config=AsanaAdapterConfig(
                access_token="token",
                workspace_gid="workspace-123",
                default_project_gid="project-321",
            ),
            transport=transport,
        )
        repo = make_repo(make_case(), actions=(make_asana_action(11),))

        first = execute_workflow_action(
            repo,
            WorkflowActionExecutionRequest(
                rental_case_id=1,
                workflow_action_id=11,
                actor_reference="system:test",
            ),
            adapter_registry=ExecutionAdapterRegistry({"asana": adapter}),
        )
        second = execute_workflow_action(
            repo,
            WorkflowActionExecutionRequest(
                rental_case_id=1,
                workflow_action_id=11,
                actor_reference="system:test",
            ),
            adapter_registry=ExecutionAdapterRegistry({"asana": adapter}),
        )

        self.assertEqual(first.action_status_after, WORKFLOW_ACTION_STATUS_SUCCEEDED)
        self.assertEqual(second.failure_codes, (EXECUTION_FAILURE_ACTION_ALREADY_SUCCEEDED,))
        self.assertTrue(second.already_succeeded_idempotently)
        self.assertEqual(len(transport.requests), 1)
        attempts = repo.list_execution_attempts(rental_case_id=1, workflow_action_id=11)
        self.assertEqual(attempts[0].external_reference, "asana:task:task-abc")

    def test_runtime_task_surface_alias_succeeds_with_asana_adapter(self) -> None:
        transport = StubAsanaTransport(
            response=(201, json.dumps({"data": {"gid": "task-task-surface"}}), {"Content-Type": "application/json"})
        )
        adapter = AsanaExecutionAdapter(
            config=AsanaAdapterConfig(
                access_token="token",
                workspace_gid="workspace-123",
                default_project_gid="project-321",
            ),
            transport=transport,
        )
        repo = make_repo(make_case(), actions=(make_asana_action(12, target_adapter_code="task_surface"),))

        result = execute_workflow_action(
            repo,
            WorkflowActionExecutionRequest(
                rental_case_id=1,
                workflow_action_id=12,
                actor_reference="system:test",
            ),
            adapter_registry=ExecutionAdapterRegistry({"task_surface": adapter}),
        )

        self.assertEqual(result.action_status_after, WORKFLOW_ACTION_STATUS_SUCCEEDED)
        attempts = repo.list_execution_attempts(rental_case_id=1, workflow_action_id=12)
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0].status, EXECUTION_ATTEMPT_STATUS_SUCCEEDED)
        self.assertEqual(attempts[0].external_reference, "asana:task:task-task-surface")

    def test_runtime_external_reference_conflict_is_rejected(self) -> None:
        case_one = make_case(rental_case_id=1)
        case_two = make_case(rental_case_id=2)
        transport = StubAsanaTransport(
            response=(201, json.dumps({"data": {"gid": "task-shared"}}), {"Content-Type": "application/json"})
        )
        adapter = AsanaExecutionAdapter(
            config=AsanaAdapterConfig(
                access_token="token",
                workspace_gid="workspace-123",
                default_project_gid="project-321",
            ),
            transport=transport,
        )
        repo = make_repo(
            case_one,
            case_two,
            actions=(
                make_asana_action(21, rental_case_id=1),
                make_asana_action(22, rental_case_id=2),
            ),
        )

        first = execute_workflow_action(
            repo,
            WorkflowActionExecutionRequest(
                rental_case_id=1,
                workflow_action_id=21,
                actor_reference="system:test",
            ),
            adapter_registry=ExecutionAdapterRegistry({"asana": adapter}),
        )
        second = execute_workflow_action(
            repo,
            WorkflowActionExecutionRequest(
                rental_case_id=2,
                workflow_action_id=22,
                actor_reference="system:test",
            ),
            adapter_registry=ExecutionAdapterRegistry({"asana": adapter}),
        )

        self.assertEqual(first.attempt_status, EXECUTION_ATTEMPT_STATUS_SUCCEEDED)
        self.assertEqual(second.failure_codes, (EXECUTION_FAILURE_EXTERNAL_REFERENCE_CONFLICT,))
        self.assertEqual(repo.load_case_snapshot(2).find_workflow_action(22).status, "executing")


if __name__ == "__main__":
    unittest.main()
