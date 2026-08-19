from __future__ import annotations

import subprocess
import unittest
from unittest.mock import patch

from tools.runtime_environment import AppEnvironment, AppRuntimeConfig
from tools.phase_08_workflow.contracts import (
    ACTION_CATEGORY_COMMUNICATION,
    ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
    APPROVAL_POSTURE_AUTOMATIC_ALLOWED,
    EXECUTION_ATTEMPT_STATUS_SUCCEEDED,
    FOLLOW_UP_STATUS_SCHEDULED,
    FOLLOW_UP_URGENCY_MEDIUM,
    LIFECYCLE_STATE_INQUIRY_ACTIVE,
    ExecutionAttempt,
    FollowUp,
    RentalCase,
    WorkflowAction,
    WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
)
from tools.phase_08_workflow.asana_adapter import AsanaAdapterConfig
from tools.phase_08_workflow.outlook_adapter import OutlookAdapterConfig
from tools.phase_08_workflow.observation_contracts import InboundObservation, InboundObservationEffect, InboundSourceRecord
from tools.phase_08_workflow.observation_repository import InMemoryObservationRepository
from tools.phase_08_workflow.orchestration_repository import InMemoryWorkflowOrchestrationRepository, WorkflowOrchestrationCaseSnapshot
from tools.phase_08_workflow.test_console_projection import TestConsoleCaseMetadata
from tools.phase_08_workflow.test_console_service import (
    HealthComponentReport,
    TEST_CONSOLE_ALLOW_REAL_PROVIDERS_ENV,
    TEST_CONSOLE_DEFAULT_WORKFLOW_EVENT_LIMIT,
    TEST_CONSOLE_DEFAULT_RENTAL_TYPE_CODE,
    TestConsoleHealthReport,
    TestConsoleConfig,
    TestConsoleError,
    TestConsoleReadError,
    TestConsoleService,
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
    def test_config_defaults_to_local_only_and_fake_providers(self) -> None:
        config = TestConsoleConfig()
        self.assertEqual(config.host, "127.0.0.1")
        self.assertEqual(config.port, 8765)
        self.assertFalse(config.allow_real_providers)
        self.assertFalse(config.allow_non_local_bind)

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
