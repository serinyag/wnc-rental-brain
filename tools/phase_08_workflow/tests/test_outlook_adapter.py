from __future__ import annotations

import json
import unittest

from tools.phase_08_workflow.contracts import (
    ACTION_CATEGORY_COMMUNICATION,
    ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
    ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
    APPROVAL_POSTURE_AUTOMATIC_ALLOWED,
    EXECUTION_ATTEMPT_STATUS_FAILED,
    LIFECYCLE_STATE_PROPOSAL_IN_PROGRESS,
    WORKFLOW_ACTION_STATUS_FAILED,
    WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
    WORKFLOW_ACTION_STATUS_SUCCEEDED,
    ExecutionAttempt,
    RentalCase,
    WorkflowAction,
)
from tools.phase_08_workflow.execution_runtime import ExecutionAdapterRegistry, execute_workflow_action
from tools.phase_08_workflow.execution_types import (
    EXECUTION_FAILURE_INVALID_EXECUTION_INPUT,
    EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS,
    EXECUTION_FAILURE_ADAPTER_RATE_LIMITED,
    EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID,
    ExecutionContext,
    ExecutionIdempotencyContext,
    WorkflowActionExecutionRequest,
)
from tools.phase_08_workflow.orchestration_repository import InMemoryWorkflowOrchestrationRepository
from tools.phase_08_workflow.outlook_adapter import (
    OutlookAdapterConfig,
    OutlookAmbiguousTransportError,
    OutlookExecutionAdapter,
    _build_create_draft_payload,
    _parse_outlook_email_payload,
)


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


def make_email_action(
    action_id: int,
    *,
    rental_case_id: int = 1,
    action_type: str = ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
    structured_payload: dict[str, object] | None = None,
    status: str = WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
) -> WorkflowAction:
    payload: dict[str, object] = {
        "open_question_ids": [action_id],
        "required_field_codes": ["guest_count"],
        "intended_recipient_role": "client",
        "purpose": "resolve_open_question",
        "reason": "Guest count is still unresolved.",
        "recipient_email": "client@example.com",
        "recipient_name": "Client Contact",
        "recipient_reference": "contact:1",
        "subject": "Need your event details",
        "body": "Please confirm the final guest count.",
        "body_type": "text",
        "message_mode": "new",
    }
    if structured_payload is not None:
        payload.update(structured_payload)
    return WorkflowAction(
        workflow_action_id=action_id,
        workflow_action_uuid=f"action-{action_id}",
        rental_case_id=rental_case_id,
        action_type=action_type,
        action_category=ACTION_CATEGORY_COMMUNICATION,
        target_adapter_code="email",
        reason_entity_type="open_question",
        reason_entity_reference=f"open_question:{action_id}",
        approval_posture=APPROVAL_POSTURE_AUTOMATIC_ALLOWED,
        status=status,
        semantic_subject_hash=f"subject:{action_id}",
        source_case_revision=0,
        idempotency_key=f"idem:{action_id}",
        structured_payload=payload,
        created_at="2026-08-13T10:00:00Z",
        updated_at="2026-08-13T10:00:00Z",
    )


def make_repo(
    rental_case: RentalCase,
    *,
    actions=(),
    attempts=(),
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
        follow_ups={rental_case_id: []},
        milestones={rental_case_id: []},
        artifacts={rental_case_id: []},
        reasoning_projections={rental_case_id: []},
        workflow_events={rental_case_id: []},
    )


def make_execution_context(
    *,
    prior_attempts: tuple[ExecutionAttempt, ...] = (),
) -> ExecutionContext:
    return ExecutionContext(
        rental_case_id=1,
        workflow_action_id=1,
        current_case_revision=0,
        actor_reference="system:test",
        case_reference_code="RC-901",
        actor_type="system",
        started_at="2026-08-13T12:00:00Z",
        prior_attempts=prior_attempts,
    )


def make_idempotency() -> ExecutionIdempotencyContext:
    return ExecutionIdempotencyContext(
        workflow_action_id=1,
        execution_attempt_id=101,
        attempt_number=1,
        semantic_idempotency_key="idem:1",
    )


def make_prior_attempt(
    *,
    execution_attempt_id: int = 55,
    attempt_number: int = 1,
    external_reference: str = "outlook:message:immutable-1",
    failure_code: str | None = None,
    retry_eligible: bool = False,
    response_snapshot: dict[str, object] | None = None,
) -> ExecutionAttempt:
    return ExecutionAttempt(
        execution_attempt_id=execution_attempt_id,
        execution_attempt_uuid=f"attempt-{execution_attempt_id}",
        workflow_action_id=1,
        rental_case_id=1,
        attempt_number=attempt_number,
        adapter_code="email",
        started_at="2026-08-13T12:00:00Z",
        status=EXECUTION_ATTEMPT_STATUS_FAILED,
        retry_eligible=retry_eligible,
        response_snapshot=response_snapshot or {"provider": "microsoft_graph_outlook", "stage": "send_draft"},
        completed_at="2026-08-13T12:01:00Z",
        external_reference=external_reference,
        failure_code=failure_code,
    )


class StubOutlookTransport:
    def __init__(self, *steps: object) -> None:
        self.steps = list(steps)
        self.requests: list[dict[str, object]] = []

    def request(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        body: bytes | None,
        timeout_seconds: int,
    ) -> tuple[int, str, dict[str, str]]:
        self.requests.append(
            {
                "method": method,
                "url": url,
                "headers": dict(headers),
                "body": body.decode("utf-8") if body is not None else None,
                "timeout_seconds": timeout_seconds,
            }
        )
        if not self.steps:
            raise AssertionError("StubOutlookTransport has no remaining steps.")
        step = self.steps.pop(0)
        if isinstance(step, Exception):
            raise step
        if not isinstance(step, tuple) or len(step) != 3:
            raise AssertionError("Transport steps must be (status_code, body_text, headers) tuples.")
        status_code, body_text, response_headers = step
        return status_code, body_text, response_headers


class OutlookAdapterTests(unittest.TestCase):
    def make_adapter(self, transport: StubOutlookTransport) -> OutlookExecutionAdapter:
        return OutlookExecutionAdapter(
            config=OutlookAdapterConfig(
                tenant_id="tenant-123",
                client_id="client-456",
                client_secret="secret-789",
                sender_mailbox="sales@wnc.example",
                graph_base_url="https://graph.microsoft.com/v1.0",
                authority_base_url="https://login.microsoftonline.com",
                timeout_seconds=15,
            ),
            transport=transport,
        )

    def test_build_create_draft_payload_maps_supported_fields(self) -> None:
        payload = _parse_outlook_email_payload(make_email_action(1).structured_payload)

        draft_payload = _build_create_draft_payload(payload)

        self.assertEqual(
            draft_payload,
            {
                "subject": "Need your event details",
                "body": {
                    "contentType": "Text",
                    "content": "Please confirm the final guest count.",
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": "client@example.com",
                            "name": "Client Contact",
                        }
                    }
                ],
            },
        )

    def test_availability_rejects_reply_mode_in_this_phase(self) -> None:
        adapter = self.make_adapter(StubOutlookTransport())
        action = make_email_action(
            1,
            structured_payload={
                "message_mode": "reply",
                "source_message_reference": "outlook:message:abc",
            },
        )

        failure = adapter.availability_failure_code(action=action)

        self.assertEqual(failure, EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID)

    def test_execute_successfully_creates_sends_and_verifies_message(self) -> None:
        transport = StubOutlookTransport(
            (200, json.dumps({"access_token": "token-123", "token_type": "Bearer"}), {}),
            (201, json.dumps({"id": "immutable-1", "isDraft": True}), {}),
            (202, "", {}),
            (200, json.dumps({"id": "immutable-1", "isDraft": False, "sentDateTime": "2026-08-13T12:05:00Z"}), {}),
        )
        adapter = self.make_adapter(transport)

        result = adapter.execute(
            action=make_email_action(1),
            execution_context=make_execution_context(),
            idempotency=make_idempotency(),
        )

        self.assertEqual(result.attempt_status, "succeeded")
        self.assertEqual(result.external_reference, "outlook:message:immutable-1")
        self.assertEqual(len(transport.requests), 4)
        self.assertIn("grant_type=client_credentials", transport.requests[0]["body"])
        self.assertIn("/users/sales%40wnc.example/messages", transport.requests[1]["url"])
        self.assertEqual(transport.requests[1]["headers"]["Prefer"], 'IdType="ImmutableId"')
        self.assertEqual(transport.requests[2]["method"], "POST")
        self.assertIn("/messages/immutable-1/send", transport.requests[2]["url"])

    def test_execute_rejects_unsupported_attachments_without_provider_calls(self) -> None:
        transport = StubOutlookTransport()
        adapter = self.make_adapter(transport)
        action = make_email_action(
            1,
            structured_payload={"attachments": [{"name": "proposal.pdf"}]},
        )

        result = adapter.execute(
            action=action,
            execution_context=make_execution_context(),
            idempotency=make_idempotency(),
        )

        self.assertEqual(result.failure_code, EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID)
        self.assertEqual(transport.requests, [])

    def test_execute_returns_ambiguous_after_send_transport_failure_with_draft_reference(self) -> None:
        transport = StubOutlookTransport(
            (200, json.dumps({"access_token": "token-123", "token_type": "Bearer"}), {}),
            (201, json.dumps({"id": "immutable-1", "isDraft": True}), {}),
            OutlookAmbiguousTransportError("timeout"),
        )
        adapter = self.make_adapter(transport)

        result = adapter.execute(
            action=make_email_action(1),
            execution_context=make_execution_context(),
            idempotency=make_idempotency(),
        )

        self.assertEqual(result.failure_code, EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS)
        self.assertEqual(result.external_reference, "outlook:message:immutable-1")
        self.assertEqual(result.response_snapshot["stage"], "send_draft")

    def test_execute_reuses_existing_draft_id_on_retryable_send_retry(self) -> None:
        transport = StubOutlookTransport(
            (200, json.dumps({"access_token": "token-123", "token_type": "Bearer"}), {}),
            (202, "", {}),
            (200, json.dumps({"id": "immutable-1", "isDraft": False, "sentDateTime": "2026-08-13T12:05:00Z"}), {}),
        )
        adapter = self.make_adapter(transport)

        result = adapter.execute(
            action=make_email_action(1),
            execution_context=make_execution_context(
                prior_attempts=(
                    make_prior_attempt(
                        retry_eligible=True,
                        failure_code=EXECUTION_FAILURE_ADAPTER_RATE_LIMITED,
                    ),
                )
            ),
            idempotency=make_idempotency(),
        )

        self.assertEqual(result.attempt_status, "succeeded")
        self.assertEqual(len(transport.requests), 3)
        self.assertEqual(transport.requests[1]["method"], "POST")
        self.assertIn("/messages/immutable-1/send", transport.requests[1]["url"])
        self.assertIsNone(transport.requests[1]["body"])

    def test_execute_blocks_retry_after_prior_ambiguous_send(self) -> None:
        transport = StubOutlookTransport()
        adapter = self.make_adapter(transport)

        result = adapter.execute(
            action=make_email_action(1),
            execution_context=make_execution_context(
                prior_attempts=(
                    make_prior_attempt(
                        failure_code=EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS,
                    ),
                )
            ),
            idempotency=make_idempotency(),
        )

        self.assertEqual(result.failure_code, EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS)
        self.assertEqual(result.external_reference, "outlook:message:immutable-1")
        self.assertEqual(transport.requests, [])

    def test_runtime_persists_external_reference_for_ambiguous_send(self) -> None:
        repo = make_repo(make_case(), actions=(make_email_action(1),))
        transport = StubOutlookTransport(
            (200, json.dumps({"access_token": "token-123", "token_type": "Bearer"}), {}),
            (201, json.dumps({"id": "immutable-1", "isDraft": True}), {}),
            OutlookAmbiguousTransportError("timeout"),
        )
        registry = ExecutionAdapterRegistry({"email": self.make_adapter(transport)})

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

        self.assertEqual(result.action_status_after, WORKFLOW_ACTION_STATUS_FAILED)
        attempts = repo.list_execution_attempts(rental_case_id=1, workflow_action_id=1)
        self.assertEqual(attempts[0].external_reference, "outlook:message:immutable-1")
        self.assertEqual(attempts[0].failure_code, EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS)

    def test_runtime_retryable_send_failure_reuses_same_draft_identity(self) -> None:
        repo = make_repo(make_case(), actions=(make_email_action(1),))
        first_transport = StubOutlookTransport(
            (200, json.dumps({"access_token": "token-123", "token_type": "Bearer"}), {}),
            (201, json.dumps({"id": "immutable-1", "isDraft": True}), {}),
            (429, json.dumps({"error": {"code": "TooManyRequests"}}), {"Retry-After": "2"}),
        )
        first_registry = ExecutionAdapterRegistry({"email": self.make_adapter(first_transport)})

        first_result = execute_workflow_action(
            repo,
            WorkflowActionExecutionRequest(
                rental_case_id=1,
                workflow_action_id=1,
                actor_reference="system:test",
            ),
            adapter_registry=first_registry,
            now=lambda: "2026-08-13T12:00:00Z",
        )

        self.assertTrue(first_result.retry_eligible)
        self.assertEqual(first_result.action_status_after, WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE)
        self.assertEqual(first_result.external_reference, "outlook:message:immutable-1")

        second_transport = StubOutlookTransport(
            (200, json.dumps({"access_token": "token-123", "token_type": "Bearer"}), {}),
            (202, "", {}),
            (200, json.dumps({"id": "immutable-1", "isDraft": False, "sentDateTime": "2026-08-13T12:05:00Z"}), {}),
        )
        second_registry = ExecutionAdapterRegistry({"email": self.make_adapter(second_transport)})

        second_result = execute_workflow_action(
            repo,
            WorkflowActionExecutionRequest(
                rental_case_id=1,
                workflow_action_id=1,
                actor_reference="system:test",
            ),
            adapter_registry=second_registry,
            now=lambda: "2026-08-13T12:06:00Z",
        )

        self.assertEqual(second_result.action_status_after, WORKFLOW_ACTION_STATUS_SUCCEEDED)
        self.assertEqual(len(second_transport.requests), 3)
        self.assertIn("/messages/immutable-1/send", second_transport.requests[1]["url"])

    def test_unsupported_action_type_fails_preflight_without_transport_use(self) -> None:
        repo = make_repo(
            make_case(),
            actions=(
                make_email_action(
                    1,
                    action_type=ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
                ),
            ),
        )
        transport = StubOutlookTransport()
        registry = ExecutionAdapterRegistry({"email": self.make_adapter(transport)})

        result = execute_workflow_action(
            repo,
            WorkflowActionExecutionRequest(
                rental_case_id=1,
                workflow_action_id=1,
                actor_reference="system:test",
            ),
            adapter_registry=registry,
        )

        self.assertEqual(result.failure_codes, (EXECUTION_FAILURE_INVALID_EXECUTION_INPUT,))
        self.assertEqual(transport.requests, [])


if __name__ == "__main__":
    unittest.main()
