from __future__ import annotations

import base64
import io
import json
import unittest
from http import HTTPStatus

from tools.phase_08_workflow.contracts import LIFECYCLE_STATE_INQUIRY_ACTIVE, RentalCase
from tools.phase_08_workflow.orchestration_repository import WorkflowOrchestrationCaseSnapshot
from tools.phase_08_workflow.test_console import TestConsoleApp
from tools.phase_08_workflow.test_console_projection import ProjectionItem, TestConsoleCaseMetadata, WorkingProposalProjection
from tools.phase_08_workflow.test_console_service import (
    CaseConsoleSnapshot,
    HealthComponentReport,
    OperationReport,
    TestCaseSummary,
    TestConsoleClockStatus,
    TestConsoleError,
    TestConsoleHealthReport,
    TestConsoleConfig,
)
from tools.runtime_environment import AppEnvironment, AppRuntimeConfig


class _FakeService:
    def __init__(self, *, config: TestConsoleConfig | None = None) -> None:
        self.config = config or TestConsoleConfig()
        self.clock_status = TestConsoleClockStatus(
            current_time="2026-08-15T10:00:00Z",
            real_current_time="2026-08-15T10:00:00Z",
            simulated=False,
        )

    def list_test_cases(self) -> tuple[TestCaseSummary, ...]:
        return (
            TestCaseSummary(
                rental_case_id=1,
                case_reference_code="RC-9001",
                lifecycle_state="inquiry_active",
                case_revision=0,
                display_name="Autumn Inquiry",
                client_label="Acme Events",
                contact_email="client@example.test",
                event_reference="October social",
                active_event_start="2026-10-03T12:00:00Z",
                last_activity="2026-08-14T10:00:00Z",
                open_blocker_count=0,
                open_question_count=0,
                pending_approval_count=0,
                executable_action_count=0,
            ),
        )

    def create_test_case(self, **kwargs) -> OperationReport:
        del kwargs
        return OperationReport(title="Test Rental Created", success=True, lines=("RentalCase: RC-9002",))

    def load_case_detail(self, rental_case_id: int) -> CaseConsoleSnapshot:
        del rental_case_id
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
            created_at="2026-08-14T09:00:00Z",
            updated_at="2026-08-14T10:00:00Z",
        )
        return CaseConsoleSnapshot(
            metadata=TestConsoleCaseMetadata(
                label="Autumn Inquiry",
                client_label="Acme Events",
                contact_email="client@example.test",
                event_reference="October social",
                created_by="test_console:operator",
            ),
            orchestration_snapshot=WorkflowOrchestrationCaseSnapshot(rental_case=rental_case),
            evidence_bundles=(),
            test_metadata_lines=("Label: Autumn Inquiry", "Client / company: Acme Events"),
            working_proposal=WorkingProposalProjection(
                rental_snapshot=(ProjectionItem(label="Guest count", value="Not provided", state="unresolved"),),
                commercial_snapshot=(ProjectionItem(label="Booking fee baseline", value="Not established", state="unresolved"),),
                feasibility_snapshot=(ProjectionItem(label="Feasibility as requested", value="Not yet evaluated", state="unresolved"),),
                missing_client_information=(ProjectionItem(label="Outstanding client information", value="None", state="none"),),
                requirements=(ProjectionItem(label="Outstanding requirements", value="None", state="none"),),
                blockers=(ProjectionItem(label="Current blockers", value="None", state="none"),),
                approvals=(ProjectionItem(label="Pending approvals", value="None", state="none"),),
                operations=(ProjectionItem(label="Current working scope", value="No structured operational facts are established yet.", state="none"),),
                changes=(ProjectionItem(label="Proposed or pending changes", value="None", state="none"),),
                communication=(ProjectionItem(label="Communication state", value="No communication or follow-up state is established yet.", state="none"),),
                next_actions=(ProjectionItem(label="Needs attention", value="No current structured workflow actions require attention.", state="none"),),
                proposal_freshness=(ProjectionItem(label="Proposal artifact", value="Not yet established", state="unresolved"),),
            ),
            human_work_preview=("No structured human work is currently queued.",),
            asana_master_task_reference=None,
            provider_mode_lines=("REAL PROVIDER EXECUTION DISABLED", "email -> deterministic fake"),
        )

    def run_reconciliation(self, **kwargs) -> OperationReport:
        del kwargs
        return OperationReport(title="Workflow Reconciliation Evaluated", success=False, lines=("Case revision before: 0",), failure_codes=("stale_case_revision",))

    def run_inquiry_waiting(self, **kwargs) -> OperationReport:
        del kwargs
        return OperationReport(title="Inquiry Waiting Evaluated", success=True, lines=("Waiting required: no",))

    def evaluate_followups(self, **kwargs) -> OperationReport:
        del kwargs
        return OperationReport(title="Follow-Ups Evaluated", success=True, lines=("Evaluated follow-ups: 0",))

    def inject_raw_test_evidence(self, **kwargs) -> OperationReport:
        del kwargs
        return OperationReport(title="Raw Test Evidence Recorded", success=True, lines=("Source record id: 1",))

    def inject_structured_test_observation(self, **kwargs) -> OperationReport:
        del kwargs
        return OperationReport(title="Structured Test Observation Injected", success=True, lines=("Observation id: 1",))

    def generate_inquiry_response_draft(self, **kwargs) -> OperationReport:
        del kwargs
        return OperationReport(title="Inquiry Response Draft Generated", success=True, lines=("Draft revision id: 9",))

    def edit_inquiry_response_draft(self, **kwargs) -> OperationReport:
        del kwargs
        return OperationReport(title="Inquiry Response Draft Saved", success=True, lines=("Draft revision id: 10",))

    def approve_request(self, **kwargs) -> OperationReport:
        del kwargs
        return OperationReport(title="Approval Approved", success=True, lines=("Approval status: approved",))

    def reject_request(self, **kwargs) -> OperationReport:
        del kwargs
        return OperationReport(title="Approval Rejected", success=True, lines=("Approval status: rejected",))

    def execute_action(self, **kwargs) -> OperationReport:
        del kwargs
        return OperationReport(title="Workflow Action Evaluated", success=False, lines=("Action status before: ready_to_execute",), failure_codes=("action_stale_revision",))

    def get_clock_status(self) -> TestConsoleClockStatus:
        return self.clock_status

    def clock_controls_enabled(self) -> bool:
        return self.config.runtime.allows_mutable_test_clock()

    def get_health_report(self) -> TestConsoleHealthReport:
        return TestConsoleHealthReport(
            overall_status="warn",
            environment=self.config.runtime.app_env.value,
            application=HealthComponentReport(status="ok", detail="WSGI application responded."),
            database=HealthComponentReport(status="ok", detail="Bounded database query succeeded."),
            phase5=HealthComponentReport(status="warn", detail="Phase 5 is using FTS fallback."),
            phase6=HealthComponentReport(status="ok", detail="Phase 6 embeddings are bootstrapped."),
            providers={"outlook": "disabled", "asana": "configured_but_disabled"},
        )

    def advance_test_clock(self, *, hours: int = 0, days: int = 0) -> TestConsoleClockStatus:
        del hours, days
        self.clock_status = TestConsoleClockStatus(
            current_time="2026-08-22T10:00:00Z",
            real_current_time="2026-08-15T10:00:00Z",
            simulated=True,
        )
        return self.clock_status

    def set_test_clock(self, *, timestamp_value: str | None) -> TestConsoleClockStatus:
        del timestamp_value
        self.clock_status = TestConsoleClockStatus(
            current_time="2026-08-23T14:30:00Z",
            real_current_time="2026-08-15T10:00:00Z",
            simulated=True,
        )
        return self.clock_status

    def reset_test_clock(self) -> TestConsoleClockStatus:
        self.clock_status = TestConsoleClockStatus(
            current_time="2026-08-15T10:00:00Z",
            real_current_time="2026-08-15T10:00:00Z",
            simulated=False,
        )
        return self.clock_status


class _ErrorService(_FakeService):
    def list_test_cases(self) -> tuple[TestCaseSummary, ...]:
        raise TestConsoleError(
            "Console read failed.\n\nReason:\nDATABASE_READ_TIMEOUT",
            failure_code="DATABASE_READ_TIMEOUT",
            status=HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def load_case_detail(self, rental_case_id: int) -> CaseConsoleSnapshot:
        del rental_case_id
        raise TestConsoleError(
            "Console read failed.\n\nReason:\nDATABASE_READ_TIMEOUT",
            failure_code="DATABASE_READ_TIMEOUT",
            status=HTTPStatus.SERVICE_UNAVAILABLE,
        )


def call_app(
    app: TestConsoleApp,
    method: str,
    path: str,
    body: bytes = b"",
    *,
    headers: dict[str, str] | None = None,
) -> tuple[str, str]:
    status, _headers, response = call_app_response(app, method, path, body=body, headers=headers)
    return status, response


def call_app_response(
    app: TestConsoleApp,
    method: str,
    path: str,
    *,
    body: bytes = b"",
    headers: dict[str, str] | None = None,
) -> tuple[str, dict[str, str], str]:
    captured: dict[str, str] = {}
    captured_headers: dict[str, str] = {}

    def start_response(status: str, headers):
        captured["status"] = status
        captured_headers.update({key: value for key, value in headers})

    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
    }
    if headers:
        environ.update(headers)
    response = b"".join(app(environ, start_response)).decode("utf-8")
    return captured["status"], captured_headers, response


def _basic_auth_header(username: str, password: str) -> dict[str, str]:
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return {"HTTP_AUTHORIZATION": f"Basic {token}"}


class TestConsoleAppTests(unittest.TestCase):
    def test_index_renders_case_list_and_create_form(self) -> None:
        app = TestConsoleApp(_FakeService())

        status, body = call_app(app, "GET", "/")

        self.assertEqual(status, "200 OK")
        self.assertIn("Create Test Rental", body)
        self.assertIn("RC-9001", body)
        self.assertIn("Autumn Inquiry", body)
        self.assertIn("Simulated Time", body)
        self.assertIn("REAL/CURRENT TIME", body)

    def test_cases_index_alias_renders_case_list(self) -> None:
        app = TestConsoleApp(_FakeService())

        status, body = call_app(app, "GET", "/cases")

        self.assertEqual(status, "200 OK")
        self.assertIn("Create Test Rental", body)
        self.assertIn("RC-9001", body)

    def test_case_detail_renders_working_proposal_and_empty_sections(self) -> None:
        app = TestConsoleApp(_FakeService())

        status, body = call_app(app, "GET", "/cases/1")

        self.assertEqual(status, "200 OK")
        self.assertIn("Living Working Proposal / Case Overview", body)
        self.assertIn("No evidence recorded yet.", body)
        self.assertIn("REAL PROVIDER EXECUTION DISABLED", body)

    def test_runtime_failure_report_is_rendered_with_failure_code(self) -> None:
        app = TestConsoleApp(_FakeService())

        status, body = call_app(app, "POST", "/cases/1/reconcile", b"")

        self.assertEqual(status, "200 OK")
        self.assertIn("Workflow Reconciliation Evaluated", body)
        self.assertIn("stale_case_revision", body)
        self.assertNotIn("secret-token", body)

    def test_inquiry_waiting_route_renders_report(self) -> None:
        app = TestConsoleApp(_FakeService())

        status, body = call_app(app, "POST", "/cases/1/inquiry-waiting", b"")

        self.assertEqual(status, "200 OK")
        self.assertIn("Inquiry Waiting Evaluated", body)
        self.assertIn("Waiting required: no", body)

    def test_mailbox_generate_route_renders_report(self) -> None:
        app = TestConsoleApp(_FakeService())

        status, body = call_app(app, "POST", "/cases/1/mailbox/actions/44/generate", b"")

        self.assertEqual(status, "200 OK")
        self.assertIn("Inquiry Response Draft Generated", body)
        self.assertIn("Draft revision id: 9", body)

    def test_mailbox_edit_route_renders_report(self) -> None:
        app = TestConsoleApp(_FakeService())

        payload = (
            b"subject=Need+details&salutation=Hi+there%2C&intro_text=Please+share%3A"
            b"&question_prompt_1=How+many+guests%3F&closing_text=Thanks&signoff_text=Warmly"
        )
        status, body = call_app(app, "POST", "/cases/1/mailbox/drafts/9/edit", payload)

        self.assertEqual(status, "200 OK")
        self.assertIn("Inquiry Response Draft Saved", body)
        self.assertIn("Draft revision id: 10", body)

    def test_clock_advance_route_returns_to_case_detail(self) -> None:
        app = TestConsoleApp(_FakeService())

        status, body = call_app(app, "POST", "/clock/advance", b"days=7&return_path=%2Fcases%2F1")

        self.assertEqual(status, "200 OK")
        self.assertIn("Test Clock Advanced", body)
        self.assertIn("Clock mode: simulated", body)
        self.assertIn("Current UTC time: 2026-08-22T10:00:00Z", body)
        self.assertIn("Living Working Proposal / Case Overview", body)

    def test_clock_set_and_reset_routes_render_index(self) -> None:
        service = _FakeService()
        app = TestConsoleApp(service)

        status, body = call_app(app, "POST", "/clock/set", b"timestamp_value=2026-08-23T14%3A30&return_path=%2Fcases")

        self.assertEqual(status, "200 OK")
        self.assertIn("Test Clock Set", body)
        self.assertIn("Current UTC time: 2026-08-23T14:30:00Z", body)
        self.assertIn("Create Test Rental", body)

        status, body = call_app(app, "POST", "/clock/reset", b"return_path=%2Fcases")

        self.assertEqual(status, "200 OK")
        self.assertIn("Test Clock Reset", body)
        self.assertIn("Clock mode: real/current", body)

    def test_healthz_returns_safe_json_without_authentication(self) -> None:
        staging_config = TestConsoleConfig(
            runtime=AppRuntimeConfig(
                app_env=AppEnvironment.STAGING,
                app_env_explicit=True,
                database_url="postgresql://staging-db",
                staging_basic_auth_username="stage-user",
                staging_basic_auth_password="stage-pass",
            )
        )
        app = TestConsoleApp(_FakeService(config=staging_config))

        status, headers, body = call_app_response(app, "GET", "/healthz")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")
        payload = json.loads(body)
        self.assertEqual(payload["environment"], "staging")
        self.assertEqual(payload["status"], "warn")
        self.assertEqual(payload["providers"]["outlook"], "disabled")
        self.assertNotIn("stage-pass", body)

    def test_staging_requires_basic_auth_for_console_routes(self) -> None:
        staging_config = TestConsoleConfig(
            runtime=AppRuntimeConfig(
                app_env=AppEnvironment.STAGING,
                app_env_explicit=True,
                database_url="postgresql://staging-db",
                staging_basic_auth_username="stage-user",
                staging_basic_auth_password="stage-pass",
            )
        )
        app = TestConsoleApp(_FakeService(config=staging_config))

        status, headers, body = call_app_response(app, "GET", "/cases")

        self.assertEqual(status, "401 Unauthorized")
        self.assertEqual(headers["WWW-Authenticate"], 'Basic realm="WNC Rental Test Console", charset="UTF-8"')
        self.assertEqual(body, "Authentication required.")

        status, _headers, body = call_app_response(
            app,
            "GET",
            "/cases",
            headers=_basic_auth_header("stage-user", "stage-pass"),
        )

        self.assertEqual(status, "200 OK")
        self.assertIn("Create Test Rental", body)

    def test_staging_clock_routes_fail_closed(self) -> None:
        staging_config = TestConsoleConfig(
            runtime=AppRuntimeConfig(
                app_env=AppEnvironment.STAGING,
                app_env_explicit=True,
                database_url="postgresql://staging-db",
                staging_basic_auth_username="stage-user",
                staging_basic_auth_password="stage-pass",
            )
        )
        app = TestConsoleApp(_FakeService(config=staging_config))

        status, body = call_app(
            app,
            "POST",
            "/clock/advance",
            b"days=1&return_path=%2Fcases",
            headers=_basic_auth_header("stage-user", "stage-pass"),
        )

        self.assertEqual(status, "404 Not Found")
        self.assertEqual(body, "Not found.")

    def test_staging_clock_panel_is_read_only(self) -> None:
        staging_config = TestConsoleConfig(
            runtime=AppRuntimeConfig(
                app_env=AppEnvironment.STAGING,
                app_env_explicit=True,
                database_url="postgresql://staging-db",
                staging_basic_auth_username="stage-user",
                staging_basic_auth_password="stage-pass",
            )
        )
        app = TestConsoleApp(_FakeService(config=staging_config))

        status, body = call_app(
            app,
            "GET",
            "/cases",
            headers=_basic_auth_header("stage-user", "stage-pass"),
        )

        self.assertEqual(status, "200 OK")
        self.assertIn("Clock mutation controls are disabled outside the local test environment.", body)
        self.assertNotIn('action="/clock/advance"', body)

    def test_index_surfaces_structured_read_failure(self) -> None:
        app = TestConsoleApp(_ErrorService())

        status, body = call_app(app, "GET", "/")

        self.assertEqual(status, "503 Service Unavailable")
        self.assertIn("DATABASE_READ_TIMEOUT", body)
        self.assertNotIn("Traceback", body)

    def test_case_detail_surfaces_structured_read_failure(self) -> None:
        app = TestConsoleApp(_ErrorService())

        status, body = call_app(app, "GET", "/cases/1")

        self.assertEqual(status, "503 Service Unavailable")
        self.assertIn("DATABASE_READ_TIMEOUT", body)
        self.assertNotIn("Traceback", body)


if __name__ == "__main__":
    unittest.main()
