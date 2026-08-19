from __future__ import annotations

import unittest

from tools.phase_08_workflow.asana_adapter import AsanaAdapterConfig
from tools.phase_08_workflow.contracts import (
    ACTION_CATEGORY_COMMUNICATION,
    ACTION_CATEGORY_COORDINATION,
    ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
    ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
    APPROVAL_POSTURE_AUTOMATIC_ALLOWED,
    WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
    WorkflowAction,
)
from tools.phase_08_workflow.execution_types import EXECUTION_FAILURE_ADAPTER_FORBIDDEN
from tools.phase_08_workflow.provider_safety import (
    guard_asana_execution_adapter,
    guard_outlook_execution_adapter,
)
from tools.phase_08_workflow.outlook_adapter import OutlookAdapterConfig
from tools.runtime_environment import AppEnvironment, AppRuntimeConfig


def make_email_action(recipient_email: str) -> WorkflowAction:
    return WorkflowAction(
        workflow_action_id=1,
        workflow_action_uuid="action-1",
        rental_case_id=1,
        action_type=ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
        action_category=ACTION_CATEGORY_COMMUNICATION,
        target_adapter_code="email",
        reason_entity_type="open_question",
        reason_entity_reference="open_question:1",
        approval_posture=APPROVAL_POSTURE_AUTOMATIC_ALLOWED,
        status=WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
        semantic_subject_hash="subject:1",
        source_case_revision=0,
        idempotency_key="idem:1",
        structured_payload={
            "recipient_email": recipient_email,
            "recipient_name": "Client",
            "subject": "Need details",
            "body": "Please reply.",
            "body_type": "text",
            "message_mode": "new",
            "open_question_ids": [1],
            "required_field_codes": ["guest_count"],
            "intended_recipient_role": "client",
            "purpose": "resolve_open_question",
            "reason": "Guest count is unresolved.",
        },
        created_at="2026-08-13T10:00:00Z",
        updated_at="2026-08-13T10:00:00Z",
    )


def make_asana_action(project_gid: str) -> WorkflowAction:
    return WorkflowAction(
        workflow_action_id=2,
        workflow_action_uuid="action-2",
        rental_case_id=1,
        action_type=ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
        action_category=ACTION_CATEGORY_COORDINATION,
        target_adapter_code="asana",
        reason_entity_type="review_item",
        reason_entity_reference="review_item:2",
        approval_posture=APPROVAL_POSTURE_AUTOMATIC_ALLOWED,
        status=WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
        semantic_subject_hash="subject:2",
        source_case_revision=0,
        idempotency_key="idem:2",
        structured_payload={
            "task_kind": "follow_up_review",
            "summary": "Review follow-up",
            "reason": "Structured review needed.",
            "task_surface_project_id": project_gid,
        },
        created_at="2026-08-13T10:00:00Z",
        updated_at="2026-08-13T10:00:00Z",
    )


class _PassThroughAdapter:
    def __init__(self, config) -> None:
        self.config = config

    def availability_failure_code(self, *, action: WorkflowAction) -> str | None:
        del action
        return None

    def execute(self, *, action: WorkflowAction, execution_context, idempotency):
        del action, execution_context, idempotency
        return {"ok": True}


class ProviderSafetyTests(unittest.TestCase):
    def test_staging_outlook_guard_rejects_unapproved_recipient(self) -> None:
        runtime = AppRuntimeConfig(
            app_env=AppEnvironment.STAGING,
            app_env_explicit=True,
            database_url="postgresql://staging-db",
            staging_allowed_email_recipients=("approved@example.com",),
        )
        adapter = guard_outlook_execution_adapter(
            _PassThroughAdapter(
                OutlookAdapterConfig(
                    tenant_id="tenant",
                    client_id="client",
                    client_secret="secret",
                    sender_mailbox="sales@example.com",
                )
            ),
            runtime=runtime,
        )

        failure_code = adapter.availability_failure_code(action=make_email_action("blocked@example.com"))

        self.assertEqual(failure_code, EXECUTION_FAILURE_ADAPTER_FORBIDDEN)

    def test_staging_asana_guard_rejects_unapproved_project(self) -> None:
        runtime = AppRuntimeConfig(
            app_env=AppEnvironment.STAGING,
            app_env_explicit=True,
            database_url="postgresql://staging-db",
            staging_allowed_asana_project_gids=("project-123",),
        )
        adapter = guard_asana_execution_adapter(
            _PassThroughAdapter(
                AsanaAdapterConfig(
                    access_token="token",
                    workspace_gid="workspace",
                    default_project_gid="project-123",
                )
            ),
            runtime=runtime,
        )

        failure_code = adapter.availability_failure_code(action=make_asana_action("project-999"))

        self.assertEqual(failure_code, EXECUTION_FAILURE_ADAPTER_FORBIDDEN)


if __name__ == "__main__":
    unittest.main()
