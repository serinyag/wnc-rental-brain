from __future__ import annotations

import subprocess
import unittest
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch

from tools.runtime_environment import AppEnvironment, AppRuntimeConfig
from tools.phase_08_workflow.contracts import (
    ACTION_CATEGORY_COORDINATION,
    ACTION_CATEGORY_COMMUNICATION,
    ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
    ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
    ACTION_TYPE_SEND_INQUIRY_RESPONSE,
    APPROVAL_POSTURE_AUTOMATIC_ALLOWED,
    EXECUTION_ATTEMPT_STATUS_FAILED,
    EXECUTION_ATTEMPT_STATUS_SUCCEEDED,
    FOLLOW_UP_STATUS_SCHEDULED,
    FOLLOW_UP_URGENCY_MEDIUM,
    LIFECYCLE_STATE_INQUIRY_ACTIVE,
    OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION,
    ExecutionAttempt,
    FollowUp,
    OpenQuestion,
    RentalCase,
    WorkflowAction,
    WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
)
from tools.phase_08_workflow.asana_adapter import AsanaAdapterConfig
from tools.phase_08_workflow.execution_types import NormalizedExecutionResult
from tools.phase_08_workflow.governed_client_response import ClientResponseProviderError, DeterministicFakeClientResponseProvider
from tools.phase_08_workflow.outlook_adapter import OutlookAdapterConfig
from tools.phase_08_workflow.observation_contracts import InboundObservation, InboundObservationEffect, InboundSourceRecord
from tools.phase_08_workflow.observation_repository import InMemoryObservationRepository
from tools.phase_08_workflow.orchestration_repository import InMemoryWorkflowOrchestrationRepository, WorkflowOrchestrationCaseSnapshot
from tools.phase_08_workflow.test_console_projection import TestConsoleCaseMetadata
from tools.phase_08_workflow.test_console_service import (
    TEST_CONSOLE_INQUIRY_FOLLOW_UP_DELAY_DAYS_ENV,
    HealthComponentReport,
    TEST_CONSOLE_ALLOW_REAL_PROVIDERS_ENV,
    TEST_CONSOLE_DEFAULT_WORKFLOW_EVENT_LIMIT,
    TEST_CONSOLE_DEFAULT_RENTAL_TYPE_CODE,
    TestConsoleHealthReport,
    TestConsoleConfig,
    TestConsoleError,
    TestConsoleReadError,
    TestConsoleService,
    _ProjectedWorkflowActionExecutionAdapter,
)


class _DummyRepository:
    def load_case_snapshot(self, rental_case_id: int):  # pragma: no cover - defensive only
        del rental_case_id
        return None


class _MetadataService(TestConsoleService):
    def _load_test_case_metadata(self, rental_case_id: int) -> TestConsoleCaseMetadata:
        del rental_case_id
        return TestConsoleCaseMetadata(
            label="Fixture rental",
            client_label="Acme Events",
            contact_email="client@example.test",
            event_reference="October social",
            created_by="test_console:operator",
            created_at="2026-08-14T09:00:00Z",
        )


class _PostProviderReadRepository:
    def __init__(self, snapshot: WorkflowOrchestrationCaseSnapshot, calls: list[str]) -> None:
        self.snapshot = snapshot
        self.calls = calls

    def load_case_snapshot(self, rental_case_id: int) -> WorkflowOrchestrationCaseSnapshot:
        self.calls.append(f"snapshot:{rental_case_id}")
        return self.snapshot


class _PostProviderReadService(_MetadataService):
    def __init__(self, *, calls: list[str], **kwargs) -> None:
        super().__init__(**kwargs)
        self.calls = calls

    def _load_test_case_metadata(self, rental_case_id: int) -> TestConsoleCaseMetadata:
        self.calls.append(f"metadata:{rental_case_id}")
        return super()._load_test_case_metadata(rental_case_id)


class _LifecycleAwareClientResponseProvider:
    def __init__(self, calls: list[str]) -> None:
        self.calls = calls
        self.fake_provider = DeterministicFakeClientResponseProvider()

    def generate_client_response(self, contract):
        if self.calls != ["initial_reads_closed"]:
            raise AssertionError("provider was called before the initial read boundary completed")
        self.calls.append("provider_called")
        return self.fake_provider.generate_client_response(contract)


class _FailingClientResponseProvider:
    def generate_client_response(self, _contract):
        raise ClientResponseProviderError(
            "OpenAI request failed.",
            failure_category="OPENAI_REQUEST_REJECTED",
            diagnostics={"http_status": 400, "provider_error_code": "invalid_request_error"},
        )


class _GovernedClientResponseLifecycleService(_MetadataService):
    def __init__(self, *, snapshot: WorkflowOrchestrationCaseSnapshot, calls: list[str]) -> None:
        self.snapshot = snapshot
        self.calls = calls
        super().__init__(
            orchestration_repository=_DummyRepository(),
            observation_repository=_DummyRepository(),
            client_response_provider=_LifecycleAwareClientResponseProvider(calls),
            config=TestConsoleConfig(),
        )

    def load_case_detail(self, rental_case_id: int):
        self.calls.append("initial_reads_closed")
        return SimpleNamespace(
            metadata=self._load_test_case_metadata(rental_case_id),
            orchestration_snapshot=self.snapshot,
            evidence_bundles=(),
            working_proposal=SimpleNamespace(commercial_snapshot=(), feasibility_snapshot=()),
        )

    def _require_case_snapshot(self, rental_case_id: int) -> WorkflowOrchestrationCaseSnapshot:
        del rental_case_id
        if self.calls != ["initial_reads_closed", "provider_called"]:
            raise AssertionError("post-provider state was not loaded after generation")
        self.calls.append("fresh_authoritative_reread")
        return self.snapshot

    def _ensure_governed_client_response_action(self, _snapshot, *, response_intent: str, context_hash: str):
        del response_intent, context_hash
        return make_action()

    def _load_current_draft_revision_for_conversation(self, *_args, **_kwargs):
        return None

    def _build_governed_client_response_context(self, *_args, **_kwargs):
        return SimpleNamespace()

    def _create_draft_revision(self, **_kwargs):
        self.calls.append("draft_persisted")
        return SimpleNamespace(inquiry_response_draft_revision_id=101)

    def _replace_draft_approval(self, **_kwargs):
        self.calls.append("approval_created")
        return SimpleNamespace(approval_request_id=202)

    def _bind_approval_request_to_draft_revision(self, **_kwargs):
        self.calls.append("draft_bound_to_approval")
        return SimpleNamespace(inquiry_response_draft_revision_id=101)

    def _create_console_event(self, **_kwargs) -> None:
        self.calls.append("event_recorded")


class _BatchedOrchestrationRepository:
    def __init__(self, snapshot: WorkflowOrchestrationCaseSnapshot, events):
        self.snapshot = snapshot
        self.events = events
        self.core_calls = 0
        self.event_calls = 0

    def load_case_core_snapshot_for_console(self, rental_case_id: int) -> WorkflowOrchestrationCaseSnapshot:
        self.core_calls += 1
        self.last_case_id = rental_case_id
        return self.snapshot

    def load_workflow_events_for_console(self, rental_case_id: int, *, limit: int):
        self.event_calls += 1
        self.last_event_case_id = rental_case_id
        self.last_event_limit = limit
        return self.events, 135

    def load_case_snapshot(self, rental_case_id: int):  # pragma: no cover - defensive only
        del rental_case_id
        raise AssertionError("legacy snapshot loader should not be used when the batched loader is available")


class _BatchedObservationRepository:
    def __init__(self, source_records, observations, effects):
        self.source_records = source_records
        self.observations = observations
        self.effects = effects
        self.source_calls = 0
        self.observation_calls = 0
        self.effect_calls = 0

    def list_source_records_for_case(self, rental_case_id: int):
        self.source_calls += 1
        self.last_source_case_id = rental_case_id
        return self.source_records

    def list_observations_for_case(self, rental_case_id: int):
        self.observation_calls += 1
        self.last_observation_case_id = rental_case_id
        return self.observations

    def list_effects_for_case(self, rental_case_id: int):
        self.effect_calls += 1
        self.last_effect_case_id = rental_case_id
        return self.effects

    def list_observations_for_source(self, inbound_source_record_id: int):  # pragma: no cover - defensive only
        del inbound_source_record_id
        raise AssertionError("legacy per-source observation reads should not be used when batched reads are available")

    def get_effect_for_observation(self, inbound_observation_id: int):  # pragma: no cover - defensive only
        del inbound_observation_id
        raise AssertionError("legacy per-observation effect reads should not be used when batched reads are available")


def make_action(*, target_adapter_code: str = "email") -> WorkflowAction:
    return WorkflowAction(
        workflow_action_id=1,
        workflow_action_uuid="action-1",
        rental_case_id=1,
        action_type=ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
        action_category=ACTION_CATEGORY_COMMUNICATION,
        target_adapter_code=target_adapter_code,
        reason_entity_type="open_question",
        reason_entity_reference="open_question:1",
        approval_posture=APPROVAL_POSTURE_AUTOMATIC_ALLOWED,
        status=WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
        semantic_subject_hash="subject:1",
        source_case_revision=0,
        idempotency_key="idem:1",
        structured_payload={
            "open_question_ids": [1],
            "required_field_codes": ["guest_count"],
            "intended_recipient_role": "client",
            "purpose": "Collect missing details.",
            "reason": "Guest count is unresolved.",
        },
        created_at="2026-08-14T09:00:00Z",
        updated_at="2026-08-14T09:00:00Z",
    )


class TestConsoleServiceSafetyTests(unittest.TestCase):
    def test_governed_client_response_fake_provider_uses_fresh_post_provider_state_before_persistence(self) -> None:
        rental_case = RentalCase(
            rental_case_id=1,
            rental_case_uuid="case-1",
            case_reference_code="RC-9001",
            lifecycle_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
            case_revision=3,
            rental_type_code="studio_space",
            commercial_summary_status="unknown",
            operational_summary_status="unknown",
            is_active=True,
        )
        calls: list[str] = []
        service = _GovernedClientResponseLifecycleService(
            snapshot=WorkflowOrchestrationCaseSnapshot(rental_case=rental_case),
            calls=calls,
        )

        report = service.generate_governed_client_response_draft(rental_case_id=1)

        self.assertTrue(report.success)
        self.assertEqual(
            calls,
            [
                "initial_reads_closed",
                "provider_called",
                "fresh_authoritative_reread",
                "draft_persisted",
                "approval_created",
                "draft_bound_to_approval",
                "event_recorded",
            ],
        )
        self.assertIn("Draft revision id: 101", report.lines)
        self.assertIn("Approval request id: 202", report.lines)

    def test_governed_client_response_provider_failure_exposes_safe_diagnostics(self) -> None:
        rental_case = RentalCase(
            rental_case_id=1,
            rental_case_uuid="case-1",
            case_reference_code="RC-9001",
            lifecycle_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
            case_revision=3,
            rental_type_code="studio_space",
            commercial_summary_status="unknown",
            operational_summary_status="unknown",
            is_active=True,
        )
        service = TestConsoleService(
            orchestration_repository=_DummyRepository(),
            observation_repository=_DummyRepository(),
            client_response_provider=_FailingClientResponseProvider(),
            config=TestConsoleConfig(),
        )
        detail = SimpleNamespace(
            metadata=_MetadataService(
                orchestration_repository=_DummyRepository(),
                observation_repository=_DummyRepository(),
            )._load_test_case_metadata(1),
            orchestration_snapshot=WorkflowOrchestrationCaseSnapshot(rental_case=rental_case),
            evidence_bundles=(),
            working_proposal=SimpleNamespace(commercial_snapshot=(), feasibility_snapshot=()),
        )

        with patch.object(service, "load_case_detail", return_value=detail), self.assertRaises(TestConsoleError) as error:
            service.generate_governed_client_response_draft(rental_case_id=1)

        self.assertEqual(error.exception.failure_code, "CLIENT_RESPONSE_PROVIDER_FAILURE")
        self.assertEqual(error.exception.diagnostics["failure_category"], "OPENAI_REQUEST_REJECTED")
        self.assertEqual(error.exception.diagnostics["http_status"], 400)

    def test_deterministic_client_response_fixture_is_staging_only_and_uses_no_configured_provider(self) -> None:
        service = TestConsoleService(
            orchestration_repository=_DummyRepository(),
            observation_repository=_DummyRepository(),
            client_response_provider=_FailingClientResponseProvider(),
            config=TestConsoleConfig(
                runtime=AppRuntimeConfig(app_env=AppEnvironment.STAGING, app_env_explicit=True),
            ),
        )

        provider = service._client_response_provider_for_request(use_deterministic_fixture=True)

        self.assertIsInstance(provider, DeterministicFakeClientResponseProvider)

        service.config = TestConsoleConfig()
        with self.assertRaises(TestConsoleError) as error:
            service._client_response_provider_for_request(use_deterministic_fixture=True)
        self.assertEqual(error.exception.failure_code, "CLIENT_RESPONSE_FIXTURE_STAGING_ONLY")

    def test_pending_commercial_decision_does_not_trigger_generic_capacity_inference(self) -> None:
        service = TestConsoleService(
            orchestration_repository=_DummyRepository(),
            observation_repository=_DummyRepository(),
            config=TestConsoleConfig(),
        )
        snapshot = SimpleNamespace(
            case_decisions=(
                SimpleNamespace(status="proposed", domain_code="commercial"),
            )
        )

        self.assertTrue(service._has_pending_commercial_case_decision(snapshot))

    def test_config_defaults_to_local_only_and_fake_providers(self) -> None:
        config = TestConsoleConfig()
        self.assertEqual(config.host, "127.0.0.1")
        self.assertEqual(config.port, 8765)
        self.assertFalse(config.allow_real_providers)
        self.assertFalse(config.allow_non_local_bind)
        self.assertEqual(config.inquiry_cold_follow_up_delay_days, 7)

    def test_non_local_bind_requires_explicit_override(self) -> None:
        with self.assertRaises(TestConsoleError):
            TestConsoleConfig(host="0.0.0.0").validate()

        with self.assertRaises(TestConsoleError):
            TestConsoleConfig(host="0.0.0.0", allow_non_local_bind=True).validate()

        TestConsoleConfig(
            runtime=AppRuntimeConfig(app_env=AppEnvironment.LOCAL, app_env_explicit=True),
            host="0.0.0.0",
            allow_non_local_bind=True,
        ).validate()

    def test_real_provider_mode_is_blocked_by_default(self) -> None:
        service = TestConsoleService(
            orchestration_repository=_DummyRepository(),
            observation_repository=_DummyRepository(),
            config=TestConsoleConfig(),
        )

        with self.assertRaisesRegex(TestConsoleError, TEST_CONSOLE_ALLOW_REAL_PROVIDERS_ENV):
            service._build_execution_registry(action=make_action(), execution_mode="real")

    def test_staging_outlook_real_mode_requires_provider_authorization(self) -> None:
        service = TestConsoleService(
            orchestration_repository=_DummyRepository(),
            observation_repository=_DummyRepository(),
            config=TestConsoleConfig(
                runtime=AppRuntimeConfig(
                    app_env=AppEnvironment.STAGING,
                    app_env_explicit=True,
                    database_url="postgresql://staging-db",
                    staging_basic_auth_username="stage-user",
                    staging_basic_auth_password="stage-pass",
                    staging_allowed_email_recipients=("approved@example.com",),
                ),
                allow_real_providers=True,
            ),
        )

        with self.assertRaisesRegex(TestConsoleError, "STAGING_ALLOW_REAL_OUTLOOK"):
            service._build_execution_registry(action=make_action(), execution_mode="real")

    def test_staging_asana_real_mode_requires_provider_authorization(self) -> None:
        service = TestConsoleService(
            orchestration_repository=_DummyRepository(),
            observation_repository=_DummyRepository(),
            config=TestConsoleConfig(
                runtime=AppRuntimeConfig(
                    app_env=AppEnvironment.STAGING,
                    app_env_explicit=True,
                    database_url="postgresql://staging-db",
                    staging_basic_auth_username="stage-user",
                    staging_basic_auth_password="stage-pass",
                    staging_allowed_asana_project_gids=("project-123",),
                ),
                allow_real_providers=True,
            ),
        )

        with self.assertRaisesRegex(TestConsoleError, "STAGING_ALLOW_REAL_ASANA"):
            service._build_execution_registry(
                action=make_action(target_adapter_code="task_surface"),
                execution_mode="real",
            )

    def test_real_provider_registry_supports_governed_outlook_action_code(self) -> None:
        service = TestConsoleService(
            orchestration_repository=_DummyRepository(),
            observation_repository=_DummyRepository(),
            config=TestConsoleConfig(
                runtime=AppRuntimeConfig(
                    app_env=AppEnvironment.STAGING,
                    app_env_explicit=True,
                    database_url="postgresql://staging-db",
                    staging_basic_auth_username="stage-user",
                    staging_basic_auth_password="stage-pass",
                    staging_allowed_email_recipients=("approved@example.com",),
                    staging_allow_real_outlook=True,
                    staging_allow_real_outlook_send=False,
                ),
                allow_real_providers=True,
            ),
        )

        with patch(
            "tools.phase_08_workflow.test_console_service.build_outlook_execution_adapter_from_env",
            return_value=object(),
        ) as build_adapter:
            registry = service._build_execution_registry(
                action=make_action(target_adapter_code="outlook"),
                execution_mode="real",
            )

        self.assertIsNotNone(registry.resolve("outlook"))
        build_adapter.assert_called_once_with(send_enabled=False)

    def test_projected_outlook_adapter_preserves_provider_outcome_under_canonical_action_code(self) -> None:
        provider_result = NormalizedExecutionResult(
            adapter_code="email",
            attempt_status=EXECUTION_ATTEMPT_STATUS_FAILED,
            response_snapshot={"stage": "draft_created_send_disabled"},
            external_reference="outlook:message:immutable-id",
            failure_code="adapter_forbidden",
        )
        adapter = _ProjectedWorkflowActionExecutionAdapter(
            delegate=SimpleNamespace(execute=lambda **_kwargs: provider_result),
            projected_action=make_action(target_adapter_code="outlook"),
        )

        result = adapter.execute(
            action=make_action(target_adapter_code="outlook"),
            execution_context=SimpleNamespace(),
            idempotency=SimpleNamespace(),
        )

        self.assertEqual(result.adapter_code, "outlook")
        self.assertEqual(result.external_reference, "outlook:message:immutable-id")
        self.assertEqual(result.response_snapshot["stage"], "draft_created_send_disabled")

    def test_governed_outlook_execution_projects_the_current_approved_draft(self) -> None:
        service = TestConsoleService(
            orchestration_repository=_DummyRepository(),
            observation_repository=_DummyRepository(),
            config=TestConsoleConfig(),
        )
        action = replace(
            make_action(target_adapter_code="outlook"),
            action_type=ACTION_TYPE_SEND_INQUIRY_RESPONSE,
            source_case_revision=3,
            structured_payload={
                "response_intent": "COMPLETE_INQUIRY_RESPONSE",
                "context_hash": "context-123",
                "purpose": "governed_client_response_draft",
                "reason": "operator_requested_governed_client_response",
            },
        )
        revision = SimpleNamespace(
            inquiry_response_draft_revision_id=41,
            workflow_action_id=action.workflow_action_id,
            source_case_revision=3,
            recipient_email="approved@example.com",
            recipient_label="Synthetic Client",
            subject="Synthetic inquiry response",
            body_text="This is a governed synthetic draft.",
        )
        snapshot = SimpleNamespace(rental_case=SimpleNamespace(rental_case_id=1))

        with patch.object(service, "_load_current_draft_revision_for_conversation", return_value=revision):
            projected = service._project_governed_outlook_execution_action(snapshot, action=action)

        self.assertEqual(action.structured_payload["context_hash"], "context-123")
        self.assertEqual(projected.structured_payload["recipient_email"], "approved@example.com")
        self.assertEqual(projected.structured_payload["recipient_name"], "Synthetic Client")
        self.assertEqual(projected.structured_payload["subject"], "Synthetic inquiry response")
        self.assertEqual(projected.structured_payload["body"], "This is a governed synthetic draft.")
        self.assertEqual(projected.structured_payload["message_mode"], "new")

    def test_staging_uses_an_explicitly_allowlisted_synthetic_recipient(self) -> None:
        service = TestConsoleService(
            orchestration_repository=_DummyRepository(),
            observation_repository=_DummyRepository(),
            config=TestConsoleConfig(
                runtime=AppRuntimeConfig(
                    app_env=AppEnvironment.STAGING,
                    app_env_explicit=True,
                    database_url="postgresql://staging-db",
                    staging_basic_auth_username="stage-user",
                    staging_basic_auth_password="stage-pass",
                    staging_allowed_email_recipients=("approved@example.com",),
                ),
            ),
        )
        metadata = TestConsoleCaseMetadata(
            label="Synthetic rental",
            client_label="Synthetic Client",
            contact_email="approved@example.com",
            event_reference="Synthetic event",
            created_by="test_console:operator",
            created_at="2026-08-14T09:00:00Z",
        )

        self.assertEqual(service._simulated_recipient_email(17, metadata), "approved@example.com")

    def test_provider_health_reports_draft_only_outlook_and_disabled_asana(self) -> None:
        service = TestConsoleService(
            orchestration_repository=_DummyRepository(),
            observation_repository=_DummyRepository(),
            config=TestConsoleConfig(
                runtime=AppRuntimeConfig(
                    app_env=AppEnvironment.STAGING,
                    app_env_explicit=True,
                    database_url="postgresql://staging-db",
                    staging_basic_auth_username="stage-user",
                    staging_basic_auth_password="stage-pass",
                    staging_allowed_email_recipients=("approved@example.com",),
                    staging_allowed_asana_project_gids=("project-123",),
                    staging_allow_real_outlook=True,
                    staging_allow_real_outlook_send=False,
                    staging_allow_real_asana=False,
                ),
                allow_real_providers=True,
            ),
        )

        with patch(
            "tools.phase_08_workflow.test_console_service.OutlookAdapterConfig.from_env",
            return_value=OutlookAdapterConfig("tenant", "client", "secret", "sales@example.com"),
        ), patch(
            "tools.phase_08_workflow.test_console_service.AsanaAdapterConfig.from_env",
            return_value=AsanaAdapterConfig("token", "workspace", "project-123"),
        ):
            providers = service._provider_health_statuses()

        self.assertEqual(providers["outlook"], "configured_draft_only")
        self.assertEqual(providers["asana"], "configured_but_disabled")

    def test_default_clock_can_advance_and_reset(self) -> None:
        service = TestConsoleService(
            orchestration_repository=_DummyRepository(),
            observation_repository=_DummyRepository(),
            config=TestConsoleConfig(),
        )

        initial = service.get_clock_status()
        advanced = service.advance_test_clock(days=7)
        reset = service.reset_test_clock()

        self.assertFalse(initial.simulated)
        self.assertTrue(advanced.simulated)
        self.assertNotEqual(advanced.current_time, initial.current_time)
        self.assertFalse(reset.simulated)

    def test_staging_clock_uses_system_clock_and_disables_controls(self) -> None:
        service = TestConsoleService(
            orchestration_repository=_DummyRepository(),
            observation_repository=_DummyRepository(),
            config=TestConsoleConfig(
                runtime=AppRuntimeConfig(
                    app_env=AppEnvironment.STAGING,
                    app_env_explicit=True,
                    database_url="postgresql://staging-db",
                    staging_basic_auth_username="stage-user",
                    staging_basic_auth_password="stage-pass",
                )
            ),
        )

        status = service.get_clock_status()

        self.assertFalse(service.clock_controls_enabled())
        self.assertFalse(status.simulated)

    def test_health_report_uses_warn_for_phase5_fallback_and_ok_for_phase6(self) -> None:
        def query_runner(sql: str, *, expect_json: bool):
            self.assertTrue(expect_json)
            if sql == "select 1 as ok;":
                return {"rows": [{"ok": 1}]}
            if "current_knowledge_chunk_embedding_inputs" in sql and "knowledge_embedding_models" in sql:
                return {
                    "rows": [
                        {
                            "eligible_chunks": 112,
                            "active_model_count": 0,
                            "active_model_id": None,
                            "embedded_chunks": 0,
                        }
                    ]
                }
            if "current_historical_case_embedding_inputs" in sql and "historical_case_embedding_models" in sql:
                return {
                    "rows": [
                        {
                            "eligible_units": 12,
                            "active_model_count": 1,
                            "active_model_id": 7,
                            "embedded_units": 12,
                            "stale_units": 0,
                        }
                    ]
                }
            raise AssertionError(f"Unexpected health SQL: {sql}")

        service = TestConsoleService(
            orchestration_repository=_DummyRepository(),
            observation_repository=_DummyRepository(),
            config=TestConsoleConfig(),
            query_runner=query_runner,
        )

        with patch(
            "tools.phase_08_workflow.test_console_service.OutlookAdapterConfig.from_env",
            return_value=OutlookAdapterConfig(
                tenant_id=None,
                client_id=None,
                client_secret=None,
                sender_mailbox=None,
            ),
        ), patch(
            "tools.phase_08_workflow.test_console_service.AsanaAdapterConfig.from_env",
            return_value=AsanaAdapterConfig(
                access_token=None,
                workspace_gid=None,
                default_project_gid=None,
            ),
        ):
            report = service.get_health_report()

        self.assertIsInstance(report, TestConsoleHealthReport)
        self.assertEqual(report.overall_status, "warn")
        self.assertEqual(report.database.status, "ok")
        self.assertEqual(report.phase5.status, "warn")
        self.assertEqual(report.phase6.status, "ok")
        self.assertEqual(report.providers["outlook"], "disabled")
        self.assertEqual(report.providers["asana"], "disabled")

    def test_health_report_supports_real_asana_only_staging_posture(self) -> None:
        def query_runner(sql: str, *, expect_json: bool):
            self.assertTrue(expect_json)
            if sql == "select 1 as ok;":
                return {"rows": [{"ok": 1}]}
            if "current_knowledge_chunk_embedding_inputs" in sql and "knowledge_embedding_models" in sql:
                return {
                    "rows": [
                        {
                            "eligible_chunks": 112,
                            "active_model_count": 0,
                            "active_model_id": None,
                            "embedded_chunks": 0,
                        }
                    ]
                }
            if "current_historical_case_embedding_inputs" in sql and "historical_case_embedding_models" in sql:
                return {
                    "rows": [
                        {
                            "eligible_units": 12,
                            "active_model_count": 1,
                            "active_model_id": 7,
                            "embedded_units": 12,
                            "stale_units": 0,
                        }
                    ]
                }
            raise AssertionError(f"Unexpected health SQL: {sql}")

        service = TestConsoleService(
            orchestration_repository=_DummyRepository(),
            observation_repository=_DummyRepository(),
            config=TestConsoleConfig(
                runtime=AppRuntimeConfig(
                    app_env=AppEnvironment.STAGING,
                    app_env_explicit=True,
                    database_url="postgresql://staging-db",
                    staging_basic_auth_username="stage-user",
                    staging_basic_auth_password="stage-pass",
                    staging_allowed_asana_project_gids=("project-123",),
                    staging_allow_real_asana=True,
                ),
                allow_real_providers=True,
            ),
            query_runner=query_runner,
        )

        with patch(
            "tools.phase_08_workflow.test_console_service.OutlookAdapterConfig.from_env",
            return_value=OutlookAdapterConfig(
                tenant_id=None,
                client_id=None,
                client_secret=None,
                sender_mailbox=None,
            ),
        ), patch(
            "tools.phase_08_workflow.test_console_service.AsanaAdapterConfig.from_env",
            return_value=AsanaAdapterConfig(
                access_token="token",
                workspace_gid="workspace-123",
                default_project_gid="project-123",
            ),
        ):
            report = service.get_health_report()

        self.assertEqual(report.overall_status, "warn")
        self.assertEqual(report.providers["outlook"], "disabled")
        self.assertEqual(report.providers["asana"], "configured")

    def test_set_test_clock_accepts_datetime_local_input(self) -> None:
        service = TestConsoleService(
            orchestration_repository=_DummyRepository(),
            observation_repository=_DummyRepository(),
            config=TestConsoleConfig(),
        )

        status = service.set_test_clock(timestamp_value="2026-08-23T14:30")

        self.assertTrue(status.simulated)
        self.assertEqual(status.current_time, "2026-08-23T14:30:00Z")

    def test_structured_observation_value_parsing_is_strict(self) -> None:
        service = TestConsoleService(
            orchestration_repository=_DummyRepository(),
            observation_repository=_DummyRepository(),
            config=TestConsoleConfig(),
        )

        self.assertEqual(service._parse_observation_value("integer", "45"), 45)
        self.assertEqual(
            service._parse_observation_value("json_object", '{"active_event_start":"2026-10-03T12:00:00Z"}'),
            {"active_event_start": "2026-10-03T12:00:00Z"},
        )
        self.assertEqual(
            service._parse_observation_value("enum_array", '["projection_display","lighting"]'),
            ["projection_display", "lighting"],
        )
        with self.assertRaises(TestConsoleError):
            service._parse_observation_value("boolean", "maybe")
        with self.assertRaises(TestConsoleError):
            service._parse_observation_value("integer", "forty five")
        with self.assertRaises(TestConsoleError):
            service._parse_observation_value("json_object", '{"active_event_start"')

    def test_negative_inquiry_follow_up_delay_is_rejected(self) -> None:
        with self.assertRaisesRegex(TestConsoleError, TEST_CONSOLE_INQUIRY_FOLLOW_UP_DELAY_DAYS_ENV):
            TestConsoleConfig(inquiry_cold_follow_up_delay_days=-1).validate()

    def test_zero_day_inquiry_follow_up_can_create_immediate_client_action(self) -> None:
        rental_case = RentalCase(
            rental_case_id=1,
            rental_case_uuid="case-1",
            case_reference_code="RC-9001",
            lifecycle_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
            case_revision=0,
            rental_type_code="custom_scope",
            commercial_summary_status="unknown",
            operational_summary_status="unknown",
            is_active=True,
            service_level_or_type="studio_rental",
            primary_contact_ref="contact:1",
            created_at="2026-08-14T09:00:00Z",
            updated_at="2026-08-14T09:00:00Z",
        )
        question = OpenQuestion(
            open_question_id=1,
            rental_case_id=1,
            question_type="requested_event_timing",
            domain_code="event_profile",
            human_question_text="What date and time is the client requesting for the event?",
            blocking_scope="transition",
            status="open",
            created_at="2026-08-14T09:00:00Z",
            requested_from_role="client",
            source_reference="open_question:1",
        )
        orchestration_repository = InMemoryWorkflowOrchestrationRepository(
            rental_cases={1: rental_case},
            rental_case_facts={1: []},
            blockers={1: []},
            requirements={1: []},
            open_questions={1: [question]},
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
        service = _MetadataService(
            orchestration_repository=orchestration_repository,
            observation_repository=_DummyRepository(),
            config=TestConsoleConfig(inquiry_cold_follow_up_delay_days=0),
            now=lambda: "2026-08-19T09:43:36Z",
        )

        report = service.run_inquiry_waiting(rental_case_id=1)
        snapshot = orchestration_repository.load_case_snapshot(1)

        self.assertIn("Created actions: 1", report.lines)
        self.assertIn("Action formation eligible: yes", report.lines)
        self.assertEqual(len(snapshot.follow_ups), 1)
        self.assertEqual(len(snapshot.workflow_actions), 1)
        self.assertEqual(snapshot.workflow_actions[0].action_type, ACTION_TYPE_REQUEST_CLIENT_INFORMATION)

    def test_run_reconciliation_creates_capacity_restriction_for_studio_over_max(self) -> None:
        rental_case = RentalCase(
            rental_case_id=1,
            rental_case_uuid="case-1",
            case_reference_code="RC-9001",
            lifecycle_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
            case_revision=0,
            rental_type_code="studio_space",
            commercial_summary_status="unknown",
            operational_summary_status="unknown",
            is_active=True,
            service_level_or_type="studio_rental",
            created_at="2026-08-14T09:00:00Z",
            updated_at="2026-08-14T09:00:00Z",
        )
        orchestration_repository = InMemoryWorkflowOrchestrationRepository(
            rental_cases={1: rental_case},
            rental_case_facts={1: []},
            blockers={1: []},
            requirements={1: []},
            open_questions={1: []},
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
        orchestration_repository.upsert_rental_case_fact(
            rental_case_id=1,
            field_code="guest_count",
            domain_code="event_profile",
            value_payload=48,
            source_reference="fact:guest_count",
            established_case_revision=0,
            timestamp="2026-08-14T09:00:00Z",
        )
        service = _MetadataService(
            orchestration_repository=orchestration_repository,
            observation_repository=InMemoryObservationRepository(
                rental_cases={1: rental_case},
                rental_case_facts={1: []},
                open_questions={1: []},
                requirements={1: []},
                proposed_changes={1: []},
                case_decisions={1: []},
                reschedule_requests={1: []},
                workflow_events={1: []},
                inbound_source_records={},
                inbound_observations={},
                inbound_observation_effects={},
                source_ids_by_dedupe={},
                observation_ids_by_identity={},
                observation_ids_by_source={},
                observation_failure_codes={},
            ),
            config=TestConsoleConfig(),
            now=lambda: "2026-08-20T10:00:00Z",
            query_runner=lambda sql, *, expect_json: {"rows": [{"min_guests": 20, "max_guests": 40}]} if "max(max_guests)" in sql else {"rows": []},
        )

        report = service.run_reconciliation(rental_case_id=1)
        snapshot = orchestration_repository.load_case_snapshot(1)

        self.assertTrue(report.success)
        self.assertEqual(len(snapshot.reasoning_projections), 1)
        self.assertEqual(len(snapshot.blockers), 1)
        self.assertEqual(snapshot.blockers[0].blocker_type, "deterministic_restriction")
        self.assertEqual(len(snapshot.workflow_actions), 0)

    def test_run_reconciliation_creates_technical_restriction_blocker(self) -> None:
        rental_case = RentalCase(
            rental_case_id=1,
            rental_case_uuid="case-1",
            case_reference_code="RC-9001",
            lifecycle_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
            case_revision=0,
            rental_type_code="studio_space",
            commercial_summary_status="unknown",
            operational_summary_status="unknown",
            is_active=True,
            service_level_or_type="studio_rental",
            created_at="2026-08-14T09:00:00Z",
            updated_at="2026-08-14T09:00:00Z",
        )
        source_record = InboundSourceRecord(
            inbound_source_record_id=30,
            source_system_code="manual_input",
            source_record_type="operator_note",
            dedupe_key="src:30",
            source_hash="sha256:30",
            occurred_at="2026-08-14T09:00:00Z",
            association_status="resolved",
            created_at="2026-08-14T09:00:00Z",
            resolved_rental_case_id=1,
        )
        observation = InboundObservation(
            inbound_observation_id=40,
            inbound_source_record_id=30,
            reported_field_code="technical_requirements",
            observation_type="fact_candidate",
            claim_kind="new_information",
            candidate_value_payload=["microphones"],
            source_evidence_reference="fixture:technical",
            status="validated",
            observation_identity_key="obs:40",
            created_at="2026-08-14T09:00:00Z",
            rental_case_id=1,
        )
        effect = InboundObservationEffect(
            inbound_observation_effect_id=50,
            inbound_observation_id=40,
            rental_case_id=1,
            disposition_code="no_workflow_effect",
            revalidation_required=False,
            stale_observation=False,
            reason_codes=("fixture",),
            created_at="2026-08-14T09:00:00Z",
        )
        service = _MetadataService(
            orchestration_repository=InMemoryWorkflowOrchestrationRepository(
                rental_cases={1: rental_case},
                rental_case_facts={1: []},
                blockers={1: []},
                requirements={1: []},
                open_questions={1: []},
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
            ),
            observation_repository=_BatchedObservationRepository((source_record,), (observation,), (effect,)),
            config=TestConsoleConfig(),
            now=lambda: "2026-08-20T10:00:00Z",
            query_runner=lambda sql, *, expect_json: (
                {"rows": [{"applicability_status": "applies", "support_status": "external_supplier_required", "requires_confirmation": False}]}
                if "api.evaluate_technical_requirement" in sql
                else {"rows": []}
            ),
        )
        service._load_raw_evidence_by_source = lambda rental_case_id: {30: None}  # type: ignore[method-assign]

        report = service.run_reconciliation(rental_case_id=1)
        snapshot = service.orchestration_repository.load_case_snapshot(1)

        self.assertTrue(report.success)
        self.assertEqual(len(snapshot.reasoning_projections), 1)
        self.assertEqual(len(snapshot.blockers), 1)
        self.assertEqual(snapshot.blockers[0].blocker_type, "deterministic_restriction")
        self.assertEqual(len(snapshot.workflow_actions), 0)

    def test_run_reconciliation_creates_internal_review_for_unknown_technical_requirement(self) -> None:
        rental_case = RentalCase(
            rental_case_id=1,
            rental_case_uuid="case-1",
            case_reference_code="RC-9001",
            lifecycle_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
            case_revision=0,
            rental_type_code="studio_space",
            commercial_summary_status="unknown",
            operational_summary_status="unknown",
            is_active=True,
            service_level_or_type="studio_rental",
            created_at="2026-08-14T09:00:00Z",
            updated_at="2026-08-14T09:00:00Z",
        )
        source_record = InboundSourceRecord(
            inbound_source_record_id=31,
            source_system_code="manual_input",
            source_record_type="operator_note",
            dedupe_key="src:31",
            source_hash="sha256:31",
            occurred_at="2026-08-14T09:00:00Z",
            association_status="resolved",
            created_at="2026-08-14T09:00:00Z",
            resolved_rental_case_id=1,
        )
        observation = InboundObservation(
            inbound_observation_id=41,
            inbound_source_record_id=31,
            reported_field_code="technical_requirements",
            observation_type="fact_candidate",
            claim_kind="new_information",
            candidate_value_payload=["acoustic_noise"],
            source_evidence_reference="fixture:technical",
            status="validated",
            observation_identity_key="obs:41",
            created_at="2026-08-14T09:00:00Z",
            rental_case_id=1,
        )
        effect = InboundObservationEffect(
            inbound_observation_effect_id=51,
            inbound_observation_id=41,
            rental_case_id=1,
            disposition_code="no_workflow_effect",
            revalidation_required=False,
            stale_observation=False,
            reason_codes=("fixture",),
            created_at="2026-08-14T09:00:00Z",
        )
        service = _MetadataService(
            orchestration_repository=InMemoryWorkflowOrchestrationRepository(
                rental_cases={1: rental_case},
                rental_case_facts={1: []},
                blockers={1: []},
                requirements={1: []},
                open_questions={1: []},
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
            ),
            observation_repository=_BatchedObservationRepository((source_record,), (observation,), (effect,)),
            config=TestConsoleConfig(),
            now=lambda: "2026-08-20T10:00:00Z",
            query_runner=lambda sql, *, expect_json: {"rows": []},
        )
        service._load_raw_evidence_by_source = lambda rental_case_id: {31: None}  # type: ignore[method-assign]

        report = service.run_reconciliation(rental_case_id=1)
        snapshot = service.orchestration_repository.load_case_snapshot(1)

        self.assertTrue(report.success)
        self.assertEqual(len(snapshot.reasoning_projections), 1)
        self.assertEqual(len(snapshot.blockers), 1)
        self.assertEqual(snapshot.blockers[0].blocker_type, "current_authority_missing")
        self.assertEqual(len(snapshot.workflow_actions), 1)

    def test_current_inquiry_questions_include_answered_pending_validation(self) -> None:
        service = TestConsoleService(
            orchestration_repository=_DummyRepository(),
            observation_repository=_DummyRepository(),
            config=TestConsoleConfig(),
        )
        snapshot = WorkflowOrchestrationCaseSnapshot(
            rental_case=RentalCase(
                rental_case_id=1,
                rental_case_uuid="case-1",
                case_reference_code="RC-9001",
                lifecycle_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
                case_revision=0,
                rental_type_code="custom_scope",
                commercial_summary_status="unknown",
                operational_summary_status="unknown",
                is_active=True,
                created_at="2026-08-14T09:00:00Z",
                updated_at="2026-08-14T09:00:00Z",
            ),
            open_questions=(
                OpenQuestion(
                    open_question_id=1,
                    rental_case_id=1,
                    question_type="requested_rental_scope",
                    domain_code="event_profile",
                    human_question_text="Which space or rental scope is the client requesting?",
                    blocking_scope="transition",
                    status=OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION,
                    created_at="2026-08-14T09:00:00Z",
                    requested_from_role="client",
                    proposed_answer_payload="custom_scope",
                    source_reference="open_question:1",
                ),
            ),
        )

        questions = service._current_inquiry_questions(snapshot)

        self.assertEqual([question.open_question_id for question in questions], [1])

    def test_staging_operator_can_create_task_surface_test_action(self) -> None:
        rental_case = RentalCase(
            rental_case_id=1,
            rental_case_uuid="case-1",
            case_reference_code="RC-9001",
            lifecycle_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
            case_revision=3,
            rental_type_code="custom_scope",
            commercial_summary_status="unknown",
            operational_summary_status="unknown",
            is_active=True,
            service_level_or_type="studio_rental",
            created_at="2026-08-14T09:00:00Z",
            updated_at="2026-08-14T09:00:00Z",
        )
        orchestration_repository = InMemoryWorkflowOrchestrationRepository(
            rental_cases={1: rental_case},
            rental_case_facts={1: []},
            blockers={1: []},
            requirements={1: []},
            open_questions={1: []},
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
        service = _MetadataService(
            orchestration_repository=orchestration_repository,
            observation_repository=_DummyRepository(),
            config=TestConsoleConfig(
                runtime=AppRuntimeConfig(
                    app_env=AppEnvironment.STAGING,
                    app_env_explicit=True,
                    database_url="postgresql://staging-db",
                    staging_basic_auth_username="stage-user",
                    staging_basic_auth_password="stage-pass",
                )
            ),
            now=lambda: "2026-08-19T14:15:00Z",
            query_runner=lambda sql, *, expect_json: {} if not expect_json else {"rows": []},
        )

        report = service.create_task_surface_test_action(
            rental_case_id=1,
            summary="[STAGING TEST] WNC Rental Brain Asana Adapter Validation",
            reason="Synthetic staging validation only. No client action is required.",
            task_kind="asana_staging_validation",
            project_gid_override="project-override-123",
            context_lines=["Synthetic staging task.", "Safe to delete after validation."],
            external_test_reference="s6-asana-test-001",
        )

        snapshot = orchestration_repository.load_case_snapshot(1)
        self.assertEqual(report.title, "Task-Surface Test Action Created")
        self.assertEqual(len(snapshot.workflow_actions), 1)
        action = snapshot.workflow_actions[0]
        self.assertEqual(action.action_type, ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM)
        self.assertEqual(action.action_category, ACTION_CATEGORY_COORDINATION)
        self.assertEqual(action.target_adapter_code, "task_surface")
        self.assertEqual(action.status, WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE)
        self.assertEqual(action.source_case_revision, 3)
        self.assertEqual(action.structured_payload["summary"], "[STAGING TEST] WNC Rental Brain Asana Adapter Validation")
        self.assertEqual(action.structured_payload["task_surface_project_id"], "project-override-123")
        self.assertEqual(
            action.structured_payload["task_surface_context_lines"],
            ["Synthetic staging task.", "Safe to delete after validation."],
        )

    def test_task_surface_test_action_creation_requires_staging(self) -> None:
        rental_case = RentalCase(
            rental_case_id=1,
            rental_case_uuid="case-1",
            case_reference_code="RC-9001",
            lifecycle_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
            case_revision=0,
            rental_type_code="custom_scope",
            commercial_summary_status="unknown",
            operational_summary_status="unknown",
            is_active=True,
            service_level_or_type="studio_rental",
            created_at="2026-08-14T09:00:00Z",
            updated_at="2026-08-14T09:00:00Z",
        )
        orchestration_repository = InMemoryWorkflowOrchestrationRepository(
            rental_cases={1: rental_case},
            rental_case_facts={1: []},
            blockers={1: []},
            requirements={1: []},
            open_questions={1: []},
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
        service = _MetadataService(
            orchestration_repository=orchestration_repository,
            observation_repository=_DummyRepository(),
            config=TestConsoleConfig(),
        )

        with self.assertRaisesRegex(TestConsoleError, "APP_ENV=staging"):
            service.create_task_surface_test_action(
                rental_case_id=1,
                summary="Synthetic task",
                reason="Synthetic only.",
            )

    def test_invalid_structured_observation_operator_input_returns_test_console_error(self) -> None:
        rental_case = RentalCase(
            rental_case_id=1,
            rental_case_uuid="case-1",
            case_reference_code="RC-9001",
            lifecycle_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
            case_revision=0,
            rental_type_code="custom_scope",
            commercial_summary_status="unknown",
            operational_summary_status="unknown",
            is_active=True,
            service_level_or_type="studio_rental",
            created_at="2026-08-14T09:00:00Z",
            updated_at="2026-08-14T09:00:00Z",
        )
        orchestration_repository = InMemoryWorkflowOrchestrationRepository(
            rental_cases={1: rental_case},
            rental_case_facts={1: []},
            blockers={1: []},
            requirements={1: []},
            open_questions={1: []},
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
        observation_repository = InMemoryObservationRepository(
            rental_cases={1: rental_case},
            rental_case_facts={1: []},
            open_questions={1: []},
            requirements={1: []},
            proposed_changes={1: []},
            case_decisions={1: []},
            reschedule_requests={1: []},
            workflow_events={1: []},
            inbound_source_records={},
            inbound_observations={},
            inbound_observation_effects={},
            source_ids_by_dedupe={},
            observation_ids_by_identity={},
            observation_ids_by_source={},
            observation_failure_codes={},
        )
        service = _MetadataService(
            orchestration_repository=orchestration_repository,
            observation_repository=observation_repository,
            config=TestConsoleConfig(),
        )

        with self.assertRaisesRegex(TestConsoleError, "observation_type must be one of"):
            service.inject_structured_test_observation(
                rental_case_id=1,
                field_code="guest_count",
                observation_type="assertion",
                claim_kind="new_information",
                value_text="25",
                source_excerpt="25 guests expected",
                sender_reference="fixture:test",
                external_test_reference="bad-observation-type",
            )

    def test_load_case_detail_uses_batched_console_readers_when_available(self) -> None:
        rental_case = RentalCase(
            rental_case_id=1,
            rental_case_uuid="case-1",
            case_reference_code="RC-9001",
            lifecycle_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
            case_revision=0,
            rental_type_code="studio_space",
            commercial_summary_status="unknown",
            operational_summary_status="unknown",
            is_active=True,
            service_level_or_type="studio_rental",
            created_at="2026-08-14T09:00:00Z",
            updated_at="2026-08-14T09:00:00Z",
        )
        event = {
            "workflow_event_id": 7,
            "workflow_event_uuid": "event-7",
            "rental_case_id": 1,
            "event_type_code": "fixture_event",
            "source_type": "fixture",
            "occurred_at": "2026-08-14T09:00:00Z",
            "recorded_at": "2026-08-14T09:00:00Z",
            "structured_payload": {"fixture": True},
            "source_reference": "fixture:1",
            "actor_type": "operator",
            "actor_reference": "fixture:operator",
            "event_identity_key": "fixture:1",
            "origin_metadata": {"fixture": True},
        }
        snapshot = WorkflowOrchestrationCaseSnapshot(rental_case=rental_case)
        orchestration_repository = _BatchedOrchestrationRepository(snapshot, (type("Event", (), event)(),))

        source_record = InboundSourceRecord(
            inbound_source_record_id=30,
            source_system_code="manual_input",
            source_record_type="operator_note",
            dedupe_key="src:30",
            source_hash="sha256:30",
            occurred_at="2026-08-14T09:00:00Z",
            association_status="resolved",
            created_at="2026-08-14T09:00:00Z",
            resolved_rental_case_id=1,
        )
        observation = InboundObservation(
            inbound_observation_id=40,
            inbound_source_record_id=30,
            reported_field_code="guest_count",
            observation_type="fact_candidate",
            claim_kind="new_information",
            candidate_value_payload=35,
            source_evidence_reference="fixture:guest_count",
            status="validated",
            observation_identity_key="obs:40",
            created_at="2026-08-14T09:00:00Z",
            rental_case_id=1,
        )
        effect = InboundObservationEffect(
            inbound_observation_effect_id=50,
            inbound_observation_id=40,
            rental_case_id=1,
            disposition_code="no_workflow_effect",
            revalidation_required=False,
            stale_observation=False,
            reason_codes=("fixture",),
            created_at="2026-08-14T09:00:00Z",
        )
        observation_repository = _BatchedObservationRepository((source_record,), (observation,), (effect,))
        service = _MetadataService(
            orchestration_repository=orchestration_repository,
            observation_repository=observation_repository,
            config=TestConsoleConfig(),
            query_runner=lambda *_args, **_kwargs: {"rows": []},
        )
        service._load_raw_evidence_by_source = lambda rental_case_id: {30: None}  # type: ignore[method-assign]

        detail = service.load_case_detail(1)

        self.assertEqual(orchestration_repository.core_calls, 1)
        self.assertEqual(orchestration_repository.event_calls, 1)
        self.assertEqual(orchestration_repository.last_event_limit, TEST_CONSOLE_DEFAULT_WORKFLOW_EVENT_LIMIT)
        self.assertEqual(observation_repository.source_calls, 1)
        self.assertEqual(observation_repository.observation_calls, 1)
        self.assertEqual(observation_repository.effect_calls, 1)
        self.assertEqual(detail.workflow_event_total_count, 135)
        self.assertEqual(len(detail.orchestration_snapshot.workflow_events), 1)
        self.assertEqual(len(detail.evidence_bundles), 1)
        self.assertEqual(detail.evidence_bundles[0].observations[0].inbound_observation_id, 40)
        self.assertEqual(detail.evidence_bundles[0].effects[0].inbound_observation_effect_id, 50)

    def test_repeated_case_detail_reads_do_not_mutate_in_memory_workflow_state(self) -> None:
        rental_case = RentalCase(
            rental_case_id=1,
            rental_case_uuid="case-1",
            case_reference_code="RC-9001",
            lifecycle_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
            case_revision=0,
            rental_type_code="studio_space",
            commercial_summary_status="unknown",
            operational_summary_status="unknown",
            is_active=True,
            service_level_or_type="studio_rental",
            created_at="2026-08-14T09:00:00Z",
            updated_at="2026-08-14T09:00:00Z",
        )
        action = make_action()
        attempt = ExecutionAttempt(
            execution_attempt_id=1,
            execution_attempt_uuid="attempt-1",
            workflow_action_id=1,
            rental_case_id=1,
            attempt_number=1,
            adapter_code="email",
            started_at="2026-08-14T09:00:00Z",
            status=EXECUTION_ATTEMPT_STATUS_SUCCEEDED,
            retry_eligible=False,
            response_snapshot={"provider_mode": "deterministic_fake"},
            completed_at="2026-08-14T09:01:00Z",
        )
        follow_up = FollowUp(
            follow_up_id=1,
            rental_case_id=1,
            reason_code="client_follow_up",
            due_at="2026-08-15T09:00:00Z",
            urgency_level=FOLLOW_UP_URGENCY_MEDIUM,
            attempt_count=0,
            status=FOLLOW_UP_STATUS_SCHEDULED,
            created_at="2026-08-14T09:00:00Z",
            updated_at="2026-08-14T09:00:00Z",
        )
        orchestration_repository = InMemoryWorkflowOrchestrationRepository(
            rental_cases={1: rental_case},
            rental_case_facts={1: []},
            blockers={1: []},
            requirements={1: []},
            open_questions={1: []},
            approval_requests={1: []},
            proposed_changes={1: []},
            reschedule_requests={1: []},
            case_decisions={1: []},
            workflow_actions={1: [action]},
            execution_attempts={1: [attempt]},
            follow_ups={1: [follow_up]},
            milestones={1: []},
            artifacts={1: []},
            reasoning_projections={1: []},
            workflow_events={1: []},
        )
        observation_repository = InMemoryObservationRepository(
            rental_cases={1: rental_case},
            rental_case_facts={1: []},
            open_questions={1: []},
            requirements={1: []},
            proposed_changes={1: []},
            case_decisions={1: []},
            reschedule_requests={1: []},
            workflow_events={1: []},
            inbound_source_records={},
            inbound_observations={},
            inbound_observation_effects={},
            source_ids_by_dedupe={},
            observation_ids_by_identity={},
            observation_ids_by_source={},
            observation_failure_codes={},
        )
        service = _MetadataService(
            orchestration_repository=orchestration_repository,
            observation_repository=observation_repository,
            config=TestConsoleConfig(),
            query_runner=lambda *_args, **_kwargs: {"rows": []},
        )

        snapshot_before = orchestration_repository.load_case_snapshot(1)
        for _ in range(10):
            detail = service.load_case_detail(1)
            self.assertEqual(detail.orchestration_snapshot.rental_case.case_revision, 0)
        snapshot_after = orchestration_repository.load_case_snapshot(1)

        self.assertEqual(snapshot_before, snapshot_after)

    def test_default_query_runner_normalizes_timeout_failures(self) -> None:
        timeout = subprocess.TimeoutExpired(cmd=["docker", "exec"], timeout=1.0)
        with patch("tools.phase_08_workflow.test_console_service.run_supabase_query", side_effect=timeout):
            service = TestConsoleService(
                orchestration_repository=_DummyRepository(),
                observation_repository=_DummyRepository(),
                config=TestConsoleConfig(),
            )

            with self.assertRaises(TestConsoleReadError) as captured:
                service.list_test_cases()

        self.assertEqual(captured.exception.failure_code, "DATABASE_READ_TIMEOUT")
        self.assertEqual(captured.exception.diagnostics["operation"], "test_console_database_query")
        self.assertEqual(captured.exception.diagnostics["error_class"], "TimeoutExpired")

    def test_default_query_runner_preserves_safe_database_failure_diagnostics(self) -> None:
        class _DatabaseError(Exception):
            sqlstate = "42703"

        failure = subprocess.CalledProcessError(
            returncode=1,
            cmd=["direct_postgres", "execute"],
            stderr="Direct PostgreSQL query failed.",
        )
        failure.__cause__ = _DatabaseError("column does not exist")
        with patch("tools.phase_08_workflow.test_console_service.run_supabase_query", side_effect=failure):
            service = TestConsoleService(
                orchestration_repository=_DummyRepository(),
                observation_repository=_DummyRepository(),
                config=TestConsoleConfig(),
            )

            with self.assertRaises(TestConsoleReadError) as captured:
                service.list_test_cases()

        diagnostics = captured.exception.diagnostics
        self.assertEqual(diagnostics["operation"], "test_console_database_query")
        self.assertEqual(diagnostics["error_class"], "_DatabaseError")
        self.assertEqual(diagnostics["sqlstate"], "42703")
        self.assertEqual(len(diagnostics["query_fingerprint"]), 16)
        self.assertIn("public.workflow_events", diagnostics["tables"])
        self.assertNotIn("Direct PostgreSQL query failed.", diagnostics.values())

    def test_post_provider_reread_inspection_uses_only_metadata_then_snapshot(self) -> None:
        rental_case = RentalCase(
            rental_case_id=1,
            rental_case_uuid="case-1",
            case_reference_code="RC-9001",
            lifecycle_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
            case_revision=3,
            rental_type_code="studio_space",
            commercial_summary_status="unknown",
            operational_summary_status="unknown",
            is_active=True,
        )
        calls: list[str] = []
        service = _PostProviderReadService(
            calls=calls,
            orchestration_repository=_PostProviderReadRepository(
                WorkflowOrchestrationCaseSnapshot(rental_case=rental_case),
                calls,
            ),
            observation_repository=_DummyRepository(),
            client_response_provider=object(),
            config=TestConsoleConfig(),
        )

        report = service.inspect_governed_client_response_reread(rental_case_id=1)

        self.assertTrue(report.success)
        self.assertEqual(calls, ["metadata:1", "snapshot:1"])
        self.assertIn("Read mode: provider-free", report.lines)
        self.assertIn("Case revision: 3", report.lines)

    def test_page_load_does_not_build_real_provider_adapters(self) -> None:
        rental_case = RentalCase(
            rental_case_id=1,
            rental_case_uuid="case-1",
            case_reference_code="RC-9001",
            lifecycle_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
            case_revision=0,
            rental_type_code="studio_space",
            commercial_summary_status="unknown",
            operational_summary_status="unknown",
            is_active=True,
            service_level_or_type="studio_rental",
            created_at="2026-08-14T09:00:00Z",
            updated_at="2026-08-14T09:00:00Z",
        )
        orchestration_repository = InMemoryWorkflowOrchestrationRepository(
            rental_cases={1: rental_case},
            rental_case_facts={1: []},
            blockers={1: []},
            requirements={1: []},
            open_questions={1: []},
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
        observation_repository = InMemoryObservationRepository(
            rental_cases={1: rental_case},
            rental_case_facts={1: []},
            open_questions={1: []},
            requirements={1: []},
            proposed_changes={1: []},
            case_decisions={1: []},
            reschedule_requests={1: []},
            workflow_events={1: []},
            inbound_source_records={},
            inbound_observations={},
            inbound_observation_effects={},
            source_ids_by_dedupe={},
            observation_ids_by_identity={},
            observation_ids_by_source={},
            observation_failure_codes={},
        )
        service = _MetadataService(
            orchestration_repository=orchestration_repository,
            observation_repository=observation_repository,
            config=TestConsoleConfig(),
            query_runner=lambda *_args, **_kwargs: {"rows": []},
        )

        with patch(
            "tools.phase_08_workflow.test_console_service.build_outlook_execution_adapter_from_env",
            side_effect=AssertionError("Outlook adapter should not be built on page load"),
        ), patch(
            "tools.phase_08_workflow.test_console_service.build_asana_execution_adapter_from_env",
            side_effect=AssertionError("Asana adapter should not be built on page load"),
        ):
            service.load_case_detail(1)

    def test_create_test_case_uses_non_specific_rental_type_default(self) -> None:
        queries: list[tuple[str, bool]] = []

        def query_runner(sql: str, *, expect_json: bool):
            queries.append((sql, expect_json))
            if expect_json:
                return {"rows": [{"case_reference_code": "RC-9002", "lifecycle_state": "inquiry_active"}]}
            return {}

        service = TestConsoleService(
            orchestration_repository=_DummyRepository(),
            observation_repository=_DummyRepository(),
            config=TestConsoleConfig(),
            query_runner=query_runner,
        )

        report = service.create_test_case(
            label="Fixture rental",
            client_label="Acme Events",
            contact_email="client@example.test",
            event_reference="October social",
        )

        self.assertTrue(report.success)
        self.assertEqual(report.title, "Test Rental Created")
        self.assertEqual(len(queries), 2)
        self.assertIn(f"'{TEST_CONSOLE_DEFAULT_RENTAL_TYPE_CODE}'", queries[0][0])
        self.assertNotIn("'studio_space'", queries[0][0])


if __name__ == "__main__":
    unittest.main()
