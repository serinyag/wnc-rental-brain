from __future__ import annotations

import argparse
import base64
import binascii
import html
import io
import json
import logging
import hmac
import time
import traceback
from dataclasses import asdict, is_dataclass, replace
from http import HTTPStatus
from socketserver import ThreadingMixIn
from typing import Any, Callable
from urllib.parse import parse_qs
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

from .clock import parse_timestamp
from .test_console_service import (
    STRUCTURED_OBSERVATION_CLAIM_KIND_OPTIONS,
    STRUCTURED_OBSERVATION_TYPE_OPTIONS,
    CaseConsoleSnapshot,
    OperationReport,
    TestCaseSummary,
    TestConsoleClockStatus,
    TestConsoleConfig,
    TestConsoleError,
    TestConsoleService,
)
from .test_console_projection import ProjectionItem, humanize_code

LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local Rental Workflow Test Console.")
    parser.add_argument("--host", default=None, help="Host interface to bind. Defaults to WORKFLOW_TEST_CONSOLE_HOST or 127.0.0.1.")
    parser.add_argument("--port", type=int, default=None, help="Port to bind. Defaults to WORKFLOW_TEST_CONSOLE_PORT or 8765.")
    return parser.parse_args()


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class TestConsoleApp:
    def __init__(self, service: TestConsoleService) -> None:
        self.service = service
        self.config = getattr(service, "config", TestConsoleConfig())

    def __call__(self, environ: dict[str, Any], start_response: Callable[..., Any]) -> list[bytes]:
        started = time.perf_counter()
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/")
        api_request = self._is_operator_api_path(path)
        status = HTTPStatus.OK
        failure_code = "OK"
        try:
            if method == "GET" and path == "/healthz":
                report = self._get_health_report()
                status = report.http_status
                failure_code = "HEALTHCHECK_FAIL" if status is HTTPStatus.SERVICE_UNAVAILABLE else "OK"
                return self._respond_json(start_response, report.to_payload(), status=status)
            if self._requires_authentication(path) and not self._is_authenticated(environ):
                status = HTTPStatus.UNAUTHORIZED
                failure_code = "AUTHENTICATION_REQUIRED"
                if api_request:
                    return self._respond_json_error(
                        start_response,
                        status=status,
                        message="Authentication required.",
                        failure_code=failure_code,
                        www_authenticate=True,
                    )
                return self._respond_unauthorized(start_response)
            if path.startswith("/api/operator/"):
                return self._handle_operator_api(environ, start_response, method, path)
            if path.startswith("/clock/") and not self._clock_controls_enabled():
                status = HTTPStatus.NOT_FOUND
                failure_code = "CLOCK_CONTROLS_DISABLED"
                return self._respond_text(start_response, HTTPStatus.NOT_FOUND, "Not found.")
            if method == "GET" and path in {"/", "/cases"}:
                return self._respond_html(start_response, self._render_index(current_path=path))
            if method == "POST" and path == "/cases":
                return self._respond_html(start_response, self._handle_create_case(environ))
            if method == "POST" and path == "/clock/advance":
                return self._respond_html(start_response, self._handle_clock_advance(environ))
            if method == "POST" and path == "/clock/set":
                return self._respond_html(start_response, self._handle_clock_set(environ))
            if method == "POST" and path == "/clock/reset":
                return self._respond_html(start_response, self._handle_clock_reset(environ))
            if path.startswith("/cases/"):
                return self._handle_case_route(environ, start_response, method, path)
            status = HTTPStatus.NOT_FOUND
            failure_code = "NOT_FOUND"
            return self._respond_text(start_response, HTTPStatus.NOT_FOUND, "Not found.")
        except TestConsoleError as error:
            status = error.status
            failure_code = error.failure_code
            if api_request:
                return self._respond_json_error(
                    start_response,
                    status=error.status,
                    message=str(error),
                    failure_code=error.failure_code,
                )
            return self._respond_html(
                start_response,
                self._render_error(
                    str(error),
                    failure_code=error.failure_code,
                    current_path=self._normalize_render_path(path),
                ),
                status=error.status,
            )
        except Exception:
            status = HTTPStatus.INTERNAL_SERVER_ERROR
            failure_code = "UNEXPECTED_SERVER_ERROR"
            LOGGER.exception("test_console_http_unexpected_error method=%s path=%s", method, path)
            if api_request:
                return self._respond_json_error(
                    start_response,
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                    message="Console request failed.\n\nReason:\nUNEXPECTED_SERVER_ERROR",
                    failure_code=failure_code,
                )
            return self._respond_html(
                start_response,
                self._render_error(
                    "Console request failed.\n\nReason:\nUNEXPECTED_SERVER_ERROR",
                    failure_code=failure_code,
                    current_path=self._normalize_render_path(path),
                ),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
        finally:
            LOGGER.info(
                "test_console_http method=%s path=%s status=%s failure_code=%s duration_ms=%.1f",
                method,
                path,
                status.value,
                failure_code,
                (time.perf_counter() - started) * 1000,
            )

    def _handle_operator_api(
        self,
        environ: dict[str, Any],
        start_response: Callable[..., Any],
        method: str,
        path: str,
    ) -> list[bytes]:
        parts = [part for part in path.split("/") if part]
        if parts[:3] != ["api", "operator", "cases"]:
            return self._respond_json_error(
                start_response,
                status=HTTPStatus.NOT_FOUND,
                message="Not found.",
                failure_code="NOT_FOUND",
            )
        if len(parts) == 3 and method == "GET":
            return self._respond_json(
                start_response,
                {
                    **self._base_operator_payload(),
                    "cases": self._serialize_for_json(self.service.list_test_cases()),
                },
            )
        if len(parts) == 3 and method == "POST":
            payload = self._parse_json(environ)
            report = self.service.create_test_case(
                label=payload.get("label"),
                client_label=payload.get("client_label"),
                contact_email=payload.get("contact_email"),
                event_reference=payload.get("event_reference"),
            )
            created_case = self._find_created_case_summary(report)
            detail = None if created_case is None else self.service.load_case_detail(created_case.rental_case_id)
            return self._respond_json(
                start_response,
                {
                    **self._base_operator_payload(),
                    "ok": report.success,
                    "report": self._serialize_for_json(report),
                    "created_case": self._serialize_for_json(created_case),
                    "case": self._serialize_for_json(detail),
                },
            )
        if len(parts) < 4:
            return self._respond_json_error(
                start_response,
                status=HTTPStatus.NOT_FOUND,
                message="Not found.",
                failure_code="NOT_FOUND",
            )
        try:
            rental_case_id = int(parts[3])
        except ValueError:
            return self._respond_json_error(
                start_response,
                status=HTTPStatus.NOT_FOUND,
                message="Not found.",
                failure_code="NOT_FOUND",
            )
        if len(parts) == 4 and method == "GET":
            return self._respond_json(
                start_response,
                {
                    **self._base_operator_payload(),
                    "case": self._serialize_for_json(self.service.load_case_detail(rental_case_id)),
                },
            )

        if len(parts) == 5 and parts[4] == "inquiry-intake" and method == "POST":
            report = self.service.run_inquiry_intake(rental_case_id=rental_case_id)
            return self._respond_json(start_response, self._operator_case_payload(rental_case_id, report))
        if len(parts) == 5 and parts[4] == "inquiry-waiting" and method == "POST":
            report = self.service.run_inquiry_waiting(rental_case_id=rental_case_id)
            return self._respond_json(start_response, self._operator_case_payload(rental_case_id, report))
        if len(parts) == 5 and parts[4] == "reconcile" and method == "POST":
            report = self.service.run_reconciliation(rental_case_id=rental_case_id)
            return self._respond_json(start_response, self._operator_case_payload(rental_case_id, report))
        if len(parts) == 6 and parts[4] == "followups" and parts[5] == "evaluate" and method == "POST":
            report = self.service.evaluate_followups(rental_case_id=rental_case_id)
            return self._respond_json(start_response, self._operator_case_payload(rental_case_id, report))
        if len(parts) == 5 and parts[4] == "raw-evidence" and method == "POST":
            payload = self._parse_json(environ)
            report = self.service.inject_raw_test_evidence(
                rental_case_id=rental_case_id,
                source_label=payload.get("source_label"),
                sender=payload.get("sender"),
                subject=payload.get("subject"),
                body=payload.get("body"),
                received_at=payload.get("received_at"),
                external_test_reference=payload.get("external_test_reference"),
            )
            return self._respond_json(start_response, self._operator_case_payload(rental_case_id, report))
        if len(parts) == 5 and parts[4] == "structured-observations" and method == "POST":
            payload = self._parse_json(environ)
            report = self.service.inject_structured_test_observation(
                rental_case_id=rental_case_id,
                field_code=self._required_json_field(payload, "field_code"),
                observation_type=self._required_json_field(payload, "observation_type"),
                claim_kind=self._required_json_field(payload, "claim_kind"),
                value_text=self._required_json_field(payload, "value_text"),
                source_excerpt=payload.get("source_excerpt"),
                sender_reference=payload.get("sender_reference"),
                external_test_reference=payload.get("external_test_reference"),
            )
            return self._respond_json(start_response, self._operator_case_payload(rental_case_id, report))
        if len(parts) == 5 and parts[4] == "task-surface-actions" and method == "POST":
            payload = self._parse_json(environ)
            report = self.service.create_task_surface_test_action(
                rental_case_id=rental_case_id,
                summary=self._required_json_field(payload, "summary"),
                reason=self._required_json_field(payload, "reason"),
                task_kind=payload.get("task_kind"),
                project_gid_override=payload.get("project_gid_override"),
                context_lines=payload.get("context_lines"),
                external_test_reference=payload.get("external_test_reference"),
            )
            return self._respond_json(start_response, self._operator_case_payload(rental_case_id, report))
        if len(parts) == 8 and parts[4] == "mailbox" and parts[5] == "actions" and parts[7] == "generate" and method == "POST":
            workflow_action_id = int(parts[6])
            report = self.service.generate_inquiry_response_draft(
                rental_case_id=rental_case_id,
                workflow_action_id=workflow_action_id,
            )
            return self._respond_json(start_response, self._operator_case_payload(rental_case_id, report))
        if len(parts) == 8 and parts[4] == "mailbox" and parts[5] == "drafts" and parts[7] == "edit" and method == "POST":
            draft_revision_id = int(parts[6])
            payload = self._parse_json(environ)
            report = self.service.edit_inquiry_response_draft(
                rental_case_id=rental_case_id,
                draft_revision_id=draft_revision_id,
                subject=self._required_json_field(payload, "subject"),
                salutation=self._required_json_field(payload, "salutation"),
                intro_text=self._required_json_field(payload, "intro_text"),
                closing_text=self._required_json_field(payload, "closing_text"),
                signoff_text=self._required_json_field(payload, "signoff_text"),
                question_prompt_text_by_id=self._parse_question_prompt_payload(payload.get("question_prompt_text_by_id")),
            )
            return self._respond_json(start_response, self._operator_case_payload(rental_case_id, report))
        if len(parts) == 7 and parts[4] == "approvals" and method == "POST":
            approval_request_id = int(parts[5])
            if parts[6] == "approve":
                report = self.service.approve_request(rental_case_id=rental_case_id, approval_request_id=approval_request_id)
            elif parts[6] == "reject":
                report = self.service.reject_request(rental_case_id=rental_case_id, approval_request_id=approval_request_id)
            else:
                return self._respond_json_error(
                    start_response,
                    status=HTTPStatus.NOT_FOUND,
                    message="Not found.",
                    failure_code="NOT_FOUND",
                )
            return self._respond_json(start_response, self._operator_case_payload(rental_case_id, report))
        if len(parts) == 7 and parts[4] == "actions" and parts[6] == "execute" and method == "POST":
            workflow_action_id = int(parts[5])
            payload = self._parse_json(environ)
            report = self.service.execute_action(
                rental_case_id=rental_case_id,
                workflow_action_id=workflow_action_id,
                execution_mode=str(payload.get("execution_mode", "success")),
            )
            return self._respond_json(start_response, self._operator_case_payload(rental_case_id, report))
        return self._respond_json_error(
            start_response,
            status=HTTPStatus.NOT_FOUND,
            message="Not found.",
            failure_code="NOT_FOUND",
        )

    def _handle_case_route(
        self,
        environ: dict[str, Any],
        start_response: Callable[..., Any],
        method: str,
        path: str,
    ) -> list[bytes]:
        parts = [part for part in path.split("/") if part]
        if len(parts) < 2:
            return self._respond_text(start_response, HTTPStatus.NOT_FOUND, "Not found.")
        try:
            rental_case_id = int(parts[1])
        except ValueError:
            return self._respond_text(start_response, HTTPStatus.NOT_FOUND, "Not found.")
        if len(parts) == 2 and method == "GET":
            return self._respond_html(start_response, self._render_case_detail(rental_case_id))
        if len(parts) == 3 and parts[2] == "inquiry-intake" and method == "POST":
            report = self.service.run_inquiry_intake(rental_case_id=rental_case_id)
            return self._respond_html(start_response, self._render_case_detail(rental_case_id, report))
        if len(parts) == 3 and parts[2] == "inquiry-waiting" and method == "POST":
            report = self.service.run_inquiry_waiting(rental_case_id=rental_case_id)
            return self._respond_html(start_response, self._render_case_detail(rental_case_id, report))
        if len(parts) == 3 and parts[2] == "reconcile" and method == "POST":
            report = self.service.run_reconciliation(rental_case_id=rental_case_id)
            return self._respond_html(start_response, self._render_case_detail(rental_case_id, report))
        if len(parts) == 4 and parts[2] == "followups" and parts[3] == "evaluate" and method == "POST":
            report = self.service.evaluate_followups(rental_case_id=rental_case_id)
            return self._respond_html(start_response, self._render_case_detail(rental_case_id, report))
        if len(parts) == 3 and parts[2] == "raw-evidence" and method == "POST":
            form = self._parse_form(environ)
            report = self.service.inject_raw_test_evidence(
                rental_case_id=rental_case_id,
                source_label=form.get("source_label"),
                sender=form.get("sender"),
                subject=form.get("subject"),
                body=form.get("body"),
                received_at=form.get("received_at"),
                external_test_reference=form.get("external_test_reference"),
            )
            return self._respond_html(start_response, self._render_case_detail(rental_case_id, report))
        if len(parts) == 3 and parts[2] == "structured-observations" and method == "POST":
            form = self._parse_form(environ)
            report = self.service.inject_structured_test_observation(
                rental_case_id=rental_case_id,
                field_code=form["field_code"],
                observation_type=form["observation_type"],
                claim_kind=form["claim_kind"],
                value_text=form["value_text"],
                source_excerpt=form.get("source_excerpt"),
                sender_reference=form.get("sender_reference"),
                external_test_reference=form.get("external_test_reference"),
            )
            return self._respond_html(start_response, self._render_case_detail(rental_case_id, report))
        if len(parts) == 6 and parts[2] == "mailbox" and parts[3] == "actions" and parts[5] == "generate" and method == "POST":
            workflow_action_id = int(parts[4])
            report = self.service.generate_inquiry_response_draft(
                rental_case_id=rental_case_id,
                workflow_action_id=workflow_action_id,
            )
            return self._respond_html(start_response, self._render_case_detail(rental_case_id, report))
        if len(parts) == 6 and parts[2] == "mailbox" and parts[3] == "drafts" and parts[5] == "edit" and method == "POST":
            draft_revision_id = int(parts[4])
            form = self._parse_form(environ)
            question_prompt_text_by_id = {
                int(key.removeprefix("question_prompt_")): value
                for key, value in form.items()
                if key.startswith("question_prompt_") and key.removeprefix("question_prompt_").isdigit()
            }
            report = self.service.edit_inquiry_response_draft(
                rental_case_id=rental_case_id,
                draft_revision_id=draft_revision_id,
                subject=form["subject"],
                salutation=form["salutation"],
                intro_text=form["intro_text"],
                closing_text=form["closing_text"],
                signoff_text=form["signoff_text"],
                question_prompt_text_by_id=question_prompt_text_by_id,
            )
            return self._respond_html(start_response, self._render_case_detail(rental_case_id, report))
        if len(parts) == 5 and parts[2] == "approvals" and method == "POST":
            approval_request_id = int(parts[3])
            if parts[4] == "approve":
                report = self.service.approve_request(rental_case_id=rental_case_id, approval_request_id=approval_request_id)
            elif parts[4] == "reject":
                report = self.service.reject_request(rental_case_id=rental_case_id, approval_request_id=approval_request_id)
            else:
                return self._respond_text(start_response, HTTPStatus.NOT_FOUND, "Not found.")
            return self._respond_html(start_response, self._render_case_detail(rental_case_id, report))
        if len(parts) == 5 and parts[2] == "actions" and parts[4] == "execute" and method == "POST":
            workflow_action_id = int(parts[3])
            form = self._parse_form(environ)
            report = self.service.execute_action(
                rental_case_id=rental_case_id,
                workflow_action_id=workflow_action_id,
                execution_mode=form.get("execution_mode", "success"),
            )
            return self._respond_html(start_response, self._render_case_detail(rental_case_id, report))
        return self._respond_text(start_response, HTTPStatus.NOT_FOUND, "Not found.")

    def _handle_create_case(self, environ: dict[str, Any]) -> str:
        form = self._parse_form(environ)
        report = self.service.create_test_case(
            label=form.get("label"),
            client_label=form.get("client_label"),
            contact_email=form.get("contact_email"),
            event_reference=form.get("event_reference"),
        )
        return self._render_index(report, current_path="/cases")

    def _handle_clock_advance(self, environ: dict[str, Any]) -> str:
        form = self._parse_form(environ)
        try:
            hours = int(form.get("hours", "0") or "0")
            days = int(form.get("days", "0") or "0")
        except ValueError as exc:
            raise TestConsoleError("Clock advance values must be integers.") from exc
        status = self.service.advance_test_clock(hours=hours, days=days)
        report = self._clock_report("Test Clock Advanced", status)
        return self._render_with_return_path(form.get("return_path"), report)

    def _handle_clock_set(self, environ: dict[str, Any]) -> str:
        form = self._parse_form(environ)
        status = self.service.set_test_clock(timestamp_value=form.get("timestamp_value"))
        report = self._clock_report("Test Clock Set", status)
        return self._render_with_return_path(form.get("return_path"), report)

    def _handle_clock_reset(self, environ: dict[str, Any]) -> str:
        form = self._parse_form(environ)
        status = self.service.reset_test_clock()
        report = self._clock_report("Test Clock Reset", status)
        return self._render_with_return_path(form.get("return_path"), report)

    def _render_with_return_path(self, return_path: str | None, report: OperationReport | None = None) -> str:
        normalized_path = self._normalize_render_path(return_path or "/")
        if normalized_path in {"/", "/cases"}:
            return self._render_index(report, current_path=normalized_path)
        parts = [part for part in normalized_path.split("/") if part]
        if len(parts) >= 2 and parts[0] == "cases" and parts[1].isdigit():
            return self._render_case_detail(int(parts[1]), report)
        return self._render_index(report, current_path="/")

    def _normalize_render_path(self, path: str) -> str:
        parts = [part for part in path.split("/") if part]
        if not parts:
            return "/"
        if parts[0] != "cases":
            return "/cases" if path == "/cases" else "/"
        if len(parts) >= 2 and parts[1].isdigit():
            return f"/cases/{parts[1]}"
        return "/cases"

    def _clock_report(self, title: str, status: TestConsoleClockStatus) -> OperationReport:
        mode = "simulated" if status.simulated else "real/current"
        lines = [
            f"Clock mode: {mode}",
            f"Current UTC time: {status.current_time}",
        ]
        if status.simulated:
            lines.append(f"Real UTC right now: {status.real_current_time}")
        return OperationReport(title=title, success=True, lines=tuple(lines))

    def _render_index(self, report: OperationReport | None = None, *, current_path: str = "/") -> str:
        cases = self.service.list_test_cases()
        create_form = f"""
<section class="panel">
  <h2>Create Test Rental</h2>
  <form method="post" action="/cases" class="stack">
    <label>Label <input type="text" name="label" placeholder="Autumn studio inquiry"></label>
    <label>Client / company <input type="text" name="client_label" placeholder="Acme Events"></label>
    <label>Test contact email <input type="email" name="contact_email" placeholder="client@example.test"></label>
    <label>Event reference <input type="text" name="event_reference" placeholder="October social"></label>
    <button type="submit">Create Test Rental</button>
  </form>
</section>
"""
        rows = "".join(
            f"""
<tr>
  <td><a href="/cases/{case.rental_case_id}">{h(case.case_reference_code)}</a></td>
  <td>{h(case.display_name)}</td>
  <td>{h(case.client_label or '')}</td>
  <td>{pill(case.lifecycle_state)}</td>
  <td>{case.case_revision}</td>
  <td>{h(case.active_event_start or '')}</td>
  <td>{h(case.last_activity)}</td>
  <td>{case.open_blocker_count}</td>
  <td>{case.open_question_count}</td>
  <td>{case.pending_approval_count}</td>
  <td>{case.executable_action_count}</td>
</tr>
"""
            for case in cases
        )
        cases_table = f"""
<section class="panel">
  <h2>Test RentalCases</h2>
  <table>
    <thead>
      <tr>
        <th>RentalCase</th>
        <th>Display Name</th>
        <th>Client / Company</th>
        <th>Lifecycle</th>
        <th>Revision</th>
        <th>Event Date</th>
        <th>Last Activity</th>
        <th>Blockers</th>
        <th>Questions</th>
        <th>Approvals</th>
        <th>Executable Actions</th>
      </tr>
    </thead>
    <tbody>{rows or '<tr><td colspan="11">No test cases yet.</td></tr>'}</tbody>
  </table>
</section>
"""
        return self._render_layout(
            title="Rental Workflow Test Console",
            body="".join(filter(None, [self._render_report(report), create_form, cases_table])),
            current_path=current_path,
        )

    def _render_case_detail(self, rental_case_id: int, report: OperationReport | None = None) -> str:
        detail = self.service.load_case_detail(rental_case_id)
        snapshot = detail.orchestration_snapshot
        case = snapshot.rental_case
        current_path = f"/cases/{rental_case_id}"
        sections = [
            self._render_report(report),
            f"""
<section class="hero">
  <div>
    <h1>{h(case.case_reference_code)} <span class="muted">{h(detail.metadata.label or '')}</span></h1>
    <p>{pill(case.lifecycle_state)} <span class="muted">rev {case.case_revision}</span></p>
  </div>
  <div class="provider-banner">{''.join(f'<div>{h(line)}</div>' for line in detail.provider_mode_lines)}</div>
</section>
""",
            self._render_working_proposal(detail),
            self._render_case_panel(detail),
            self._render_test_controls(rental_case_id),
            self._render_simulated_outlook_panel(rental_case_id, detail),
            self._render_evidence_panel(detail),
            self._render_simple_table(
                "Case Facts",
                ("Field", "Domain", "Value", "Established Revision", "Source"),
                [
                    (
                        fact.field_code,
                        fact.domain_code,
                        render_value(fact.value_payload),
                        str(fact.established_case_revision),
                        fact.source_reference,
                    )
                    for fact in snapshot.rental_case_facts
                ],
                note="Established/current case facts are distinct from observations.",
            ),
            self._render_simple_table(
                "Open Questions",
                ("Question", "Status", "Scope", "Answer Candidate", "Source"),
                [
                    (
                        question.human_question_text,
                        question.status,
                        question.blocking_scope,
                        render_value(question.proposed_answer_payload),
                        question.source_reference or "",
                    )
                    for question in snapshot.open_questions
                ],
            ),
            self._render_simple_table(
                "Requirements",
                ("Type", "Status", "Scope", "Owner", "Evidence"),
                [
                    (
                        requirement.requirement_type,
                        requirement.status,
                        requirement.blocking_scope,
                        requirement.owner_reference or requirement.owner_role or "",
                        requirement.evidence_reference or "",
                    )
                    for requirement in snapshot.requirements
                ],
            ),
            self._render_simple_table(
                "Blockers",
                ("Type", "Status", "Severity", "Source", "Resolution"),
                [
                    (
                        blocker.blocker_type,
                        blocker.status,
                        blocker.severity,
                        blocker.origin_entity_reference or blocker.origin_entity_type,
                        blocker.resolution_condition_text,
                    )
                    for blocker in snapshot.blockers
                ],
            ),
            self._render_simple_table(
                "Proposed Changes",
                ("Kind", "Status", "Impact", "Proposed Value", "Source"),
                [
                    (
                        change.change_kind,
                        change.status,
                        change.impact_classification or "",
                        render_value(change.proposed_value_payload),
                        change.source_reference or "",
                    )
                    for change in snapshot.proposed_changes
                ],
            ),
            self._render_simple_table(
                "Case Decisions",
                ("Scope", "Status", "Approval Posture", "Effective Value", "Authority"),
                [
                    (
                        decision.scope_description,
                        decision.status,
                        decision.approval_posture,
                        render_value(decision.effective_value_payload),
                        decision.authority_basis,
                    )
                    for decision in snapshot.case_decisions
                ],
            ),
            self._render_approvals_panel(rental_case_id, detail),
            self._render_actions_panel(rental_case_id, detail),
            self._render_simple_table(
                "Execution Attempts",
                ("Attempt", "Action", "Provider", "Outcome", "Started", "Completed", "External Reference", "Failure"),
                [
                    (
                        str(attempt.execution_attempt_id),
                        str(attempt.workflow_action_id),
                        attempt.adapter_code,
                        attempt.status,
                        attempt.started_at,
                        attempt.completed_at or "",
                        attempt.external_reference or "",
                        attempt.failure_code or "",
                    )
                    for attempt in snapshot.execution_attempts
                ],
            ),
            self._render_followups_panel(rental_case_id, detail),
            self._render_reasoning_panel(detail),
            self._render_asana_panel(detail),
            self._render_timeline_panel(detail),
        ]
        return self._render_layout(
            title=f"{case.case_reference_code} - Rental Workflow Test Console",
            body="".join(filter(None, sections)),
            current_path=current_path,
        )

    def _render_case_panel(self, detail: CaseConsoleSnapshot) -> str:
        case = detail.orchestration_snapshot.rental_case
        metadata_rows = "".join(f"<li>{h(line)}</li>" for line in detail.test_metadata_lines)
        return f"""
<section class="panel">
  <h2>Case</h2>
  <div class="grid two">
    <div>
      <ul class="plain">
        <li>RentalCase ID: {case.rental_case_id}</li>
        <li>Lifecycle state: {h(case.lifecycle_state)}</li>
        <li>Revision: {case.case_revision}</li>
        <li>Created at: {h(case.created_at or '')}</li>
        <li>Updated at: {h(case.updated_at or '')}</li>
        <li>Test marker: test_console_case_registered</li>
      </ul>
    </div>
    <div>
      <h3>Test Metadata</h3>
      <ul class="plain">{metadata_rows or '<li>No test metadata stored.</li>'}</ul>
    </div>
  </div>
</section>
"""

    def _render_test_controls(self, rental_case_id: int) -> str:
        field_options = "".join(
            f'<option value="{h(value)}">{h(value)}</option>' for value in (
                "guest_count",
                "active_event_window",
                "requested_rental_scope",
                "event_type",
                "catering_arrangement",
                "facilitator_arrangement",
                "technical_requirements",
                "supplier_details",
                "event_day_contact",
                "layout_requirements",
                "booking_fee_override",
                "proposal_acceptance",
            )
        )
        observation_type_options = "".join(f'<option value="{h(value)}">{h(value)}</option>' for value in STRUCTURED_OBSERVATION_TYPE_OPTIONS)
        claim_kind_options = "".join(f'<option value="{h(value)}">{h(value)}</option>' for value in STRUCTURED_OBSERVATION_CLAIM_KIND_OPTIONS)
        return f"""
<section class="panel">
  <h2>Runtime Controls</h2>
  <div class="grid two">
    <form method="post" action="/cases/{rental_case_id}/inquiry-intake" class="stack">
      <h3>Inquiry Intake</h3>
      <button type="submit">Run Inquiry Intake</button>
    </form>
    <form method="post" action="/cases/{rental_case_id}/inquiry-waiting" class="stack">
      <h3>Inquiry Waiting</h3>
      <button type="submit">Evaluate Inquiry Waiting</button>
    </form>
    <form method="post" action="/cases/{rental_case_id}/reconcile" class="stack">
      <h3>Orchestration</h3>
      <button type="submit">Run Existing Reconciliation</button>
    </form>
    <form method="post" action="/cases/{rental_case_id}/followups/evaluate" class="stack">
      <h3>Follow-Ups</h3>
      <button type="submit">Evaluate Follow-Ups</button>
    </form>
  </div>
  <div class="grid two">
    <form method="post" action="/cases/{rental_case_id}/raw-evidence" class="stack">
      <h3>Inject Raw Test Evidence</h3>
      <label>Source label <input type="text" name="source_label" placeholder="Test inbox paste"></label>
      <label>Sender <input type="email" name="sender" placeholder="client@example.test"></label>
      <label>Subject <input type="text" name="subject" placeholder="October 3 inquiry"></label>
      <label>Body <textarea name="body" rows="6" placeholder="We want October 3 for 45 people."></textarea></label>
      <label>Received time <input type="text" name="received_at" placeholder="2026-08-14T10:00:00Z"></label>
      <label>External test reference <input type="text" name="external_test_reference" placeholder="raw-email-001"></label>
      <button type="submit">Inject Raw Test Evidence</button>
    </form>
    <form method="post" action="/cases/{rental_case_id}/structured-observations" class="stack">
      <h3>Inject Structured Test Observation</h3>
      <label>Field code <select name="field_code">{field_options}</select></label>
      <label>Observation type <select name="observation_type">{observation_type_options}</select></label>
      <label>Claim kind <select name="claim_kind">{claim_kind_options}</select></label>
      <label>Value <textarea name="value_text" rows="4" placeholder='45 or {{"active_event_start":"2026-10-03T12:00:00Z","active_event_end":"2026-10-03T18:00:00Z"}}'></textarea></label>
      <label>Source excerpt <textarea name="source_excerpt" rows="3"></textarea></label>
      <label>Sender reference <input type="text" name="sender_reference" placeholder="test_console:operator"></label>
      <label>External test reference <input type="text" name="external_test_reference" placeholder="structured-obs-001"></label>
      <button type="submit">Inject Structured Test Observation</button>
    </form>
  </div>
</section>
"""

    def _render_simulated_outlook_panel(self, rental_case_id: int, detail: CaseConsoleSnapshot) -> str:
        inbound_rows = []
        for bundle in detail.evidence_bundles:
            if bundle.raw_evidence is None:
                continue
            inbound_rows.append(
                (
                    bundle.raw_evidence.occurred_at,
                    bundle.raw_evidence.sender or "unknown sender",
                    bundle.raw_evidence.subject or "No subject",
                    bundle.raw_evidence.external_test_reference or "",
                )
            )
        thread_cards = []
        for thread in detail.simulated_outlook_threads:
            generate_form = ""
            if thread.can_generate and thread.workflow_action_id is not None:
                generate_form = (
                    f'<form method="post" action="/cases/{rental_case_id}/mailbox/actions/{thread.workflow_action_id}/generate" class="inline">'
                    f'<button type="submit">Generate Draft</button></form>'
                )
            regenerate_form = ""
            if thread.can_regenerate and thread.workflow_action_id is not None:
                regenerate_form = (
                    f'<form method="post" action="/cases/{rental_case_id}/mailbox/actions/{thread.workflow_action_id}/generate" class="inline">'
                    f'<button type="submit">Regenerate Draft</button></form>'
                )
            approval_actions = ""
            if thread.open_approval_request_id is not None:
                approval_actions = (
                    f'<form method="post" action="/cases/{rental_case_id}/approvals/{thread.open_approval_request_id}/approve" class="inline">'
                    f'<button type="submit">Approve Exact Revision</button></form>'
                    f'<form method="post" action="/cases/{rental_case_id}/approvals/{thread.open_approval_request_id}/reject" class="inline">'
                    f'<button type="submit">Reject Draft</button></form>'
                )
            simulate_send = ""
            if thread.can_simulate_send and thread.workflow_action_id is not None:
                simulate_send = (
                    f'<form method="post" action="/cases/{rental_case_id}/actions/{thread.workflow_action_id}/execute" class="inline">'
                    '<select name="execution_mode">'
                    '<option value="success">Fake success</option>'
                    '<option value="retryable_failure">Fake failure</option>'
                    '<option value="permanent_failure">Fake permanent failure</option>'
                    '<option value="ambiguous">Fake ambiguous</option>'
                    '</select>'
                    '<button type="submit">Simulate Send</button></form>'
                )
            status_badge = ""
            if thread.current_display_status:
                status_badge = f"<span class='badge'>{h(thread.current_display_status.replace('_', ' ').upper())}</span>"
            question_list = "".join(f"<li>{h(question)}</li>" for question in thread.question_labels)
            note = f"<p class='note'>{h(thread.status_note)}</p>" if thread.status_note else ""
            draft_preview = ""
            history_rows = []
            if thread.current_revision is not None:
                draft_preview = f"""
<div class="evidence-box">
  <div><strong>To:</strong> {h(thread.current_revision.recipient_email)}</div>
  <div><strong>Subject:</strong> {h(thread.current_revision.subject)}</div>
  <div><strong>Workflow action:</strong> {thread.current_revision.workflow_action_id}</div>
  <div><strong>Approval request:</strong> {thread.current_revision.approval_request_id or ''}</div>
  <pre>{h(thread.current_revision.body_text)}</pre>
</div>
"""
                if thread.can_edit:
                    question_fields = "".join(
                        f'<label>Question {line.open_question_id}'
                        f'<textarea name="question_prompt_{line.open_question_id}" rows="2">{h(line.prompt_text)}</textarea></label>'
                        for line in thread.current_revision.question_lines
                    )
                    draft_preview += f"""
<form method="post" action="/cases/{rental_case_id}/mailbox/drafts/{thread.current_revision.inquiry_response_draft_revision_id}/edit" class="stack">
  <h4>Edit Current Draft</h4>
  <label>Subject <input type="text" name="subject" value="{h(thread.current_revision.subject)}"></label>
  <label>Salutation <input type="text" name="salutation" value="{h(thread.current_revision.salutation)}"></label>
  <label>Intro <textarea name="intro_text" rows="4">{h(thread.current_revision.intro_text)}</textarea></label>
  {question_fields}
  <label>Closing <textarea name="closing_text" rows="3">{h(thread.current_revision.closing_text)}</textarea></label>
  <label>Signoff <textarea name="signoff_text" rows="3">{h(thread.current_revision.signoff_text)}</textarea></label>
  <button type="submit">Save New Revision</button>
</form>
"""
                for revision in thread.draft_history:
                    history_rows.append(
                        (
                            str(revision.inquiry_response_draft_revision_id),
                            revision.draft_source,
                            revision.draft_status,
                            revision.created_at,
                            revision.approved_at or revision.rejected_at or revision.delivered_at or "",
                            "yes" if revision.is_current else "no",
                        )
                    )
            thread_cards.append(
                f"""
<section class="panel">
  <h3>{h(thread.thread_label)} {status_badge}</h3>
  <p class="note">Conversation key: {h(thread.conversation_key)}</p>
  {note}
  <div class="inline">{generate_form}{regenerate_form}{approval_actions}{simulate_send}</div>
  <ul class="plain">{question_list or '<li>No current question coverage loaded.</li>'}</ul>
  {draft_preview or '<p class="note">No draft revision exists yet for this inquiry thread.</p>'}
  {self._render_simple_table("Draft Revision History", ("Revision", "Source", "Status", "Created", "Outcome", "Current"), history_rows) if history_rows else ""}
</section>
"""
            )
        inbound_table = self._render_simple_table(
            "Simulated Inbox",
            ("Received", "Sender", "Subject", "Reference"),
            inbound_rows,
            note="Inbound items are sourced from existing raw test evidence. No real mailbox sync is used in this slice.",
        )
        if not thread_cards:
            thread_cards.append('<section class="panel"><p class="note">No inquiry response draft threads exist yet. Run Inquiry Waiting, then generate a draft from the current communication action.</p></section>')
        return f"<section><h2>Simulated Outlook Mailbox</h2>{inbound_table}{''.join(thread_cards)}</section>"

    def _render_evidence_panel(self, detail: CaseConsoleSnapshot) -> str:
        cards = []
        for bundle in detail.evidence_bundles:
            raw = ""
            if bundle.raw_evidence is not None:
                raw = f"""
<div class="evidence-box">
  <strong>Raw test evidence</strong>
  <div>Source label: {h(bundle.raw_evidence.source_label or '')}</div>
  <div>Sender: {h(bundle.raw_evidence.sender or '')}</div>
  <div>Subject: {h(bundle.raw_evidence.subject or '')}</div>
  <pre>{h(bundle.raw_evidence.body or '')}</pre>
</div>
"""
            observation_rows = "".join(
                f"""
<tr>
  <td>{h(observation.observation_type)}</td>
  <td>{h(observation.source_evidence_reference)}</td>
  <td>{pill(observation.status)}</td>
  <td>{h(effect.disposition_code if effect else '')}</td>
  <td>{h(effect.reason_codes[0] if effect and effect.reason_codes else '')}</td>
  <td>{h(observation.created_at)}</td>
</tr>
"""
                for observation, effect in zip(bundle.observations, bundle.effects, strict=False)
            )
            cards.append(
                f"""
<section class="panel">
  <h3>Source {bundle.source_record.inbound_source_record_id}</h3>
  <p class="note">Observation != active case truth. Source records and observations remain visible as evidence.</p>
  <ul class="plain">
    <li>Source system: {h(bundle.source_record.source_system_code)}</li>
    <li>Record type: {h(bundle.source_record.source_record_type)}</li>
    <li>Dedupe key: {h(bundle.source_record.dedupe_key)}</li>
    <li>Association status: {h(bundle.source_record.association_status)}</li>
    <li>Occurred at: {h(bundle.source_record.occurred_at)}</li>
  </ul>
  {raw}
  <table>
    <thead>
      <tr><th>Observation Type</th><th>Evidence</th><th>Status</th><th>Proposed Effect</th><th>Provenance</th><th>Created</th></tr>
    </thead>
    <tbody>{observation_rows or '<tr><td colspan="6">No structured observations for this source.</td></tr>'}</tbody>
  </table>
</section>
"""
            )
        if detail.evidence_notice:
            fallback = f'<div class="panel">{h(detail.evidence_notice)}</div>'
        else:
            fallback = '<div class="panel">No evidence recorded yet.</div>'
        return f"<section><h2>Observations / Evidence</h2>{''.join(cards) or fallback}</section>"

    def _render_approvals_panel(self, rental_case_id: int, detail: CaseConsoleSnapshot) -> str:
        rows = []
        for approval in detail.orchestration_snapshot.approval_requests:
            actions = ""
            if approval.status == "open":
                actions = (
                    f'<form method="post" action="/cases/{rental_case_id}/approvals/{approval.approval_request_id}/approve" class="inline">'
                    f'<button type="submit">Approve</button></form>'
                    f'<form method="post" action="/cases/{rental_case_id}/approvals/{approval.approval_request_id}/reject" class="inline">'
                    f'<button type="submit">Reject</button></form>'
                )
            rows.append(
                (
                    str(approval.approval_request_id),
                    approval.reason_text,
                    approval.approval_type,
                    approval.status,
                    approval.created_at,
                    approval.decided_at or "",
                    approval.decided_by_reference or "",
                    actions,
                )
            )
        return self._render_simple_table(
            "Approvals",
            ("ID", "Approval Request", "Type", "Status", "Created", "Decided", "Actor", "Action"),
            rows,
            raw_html_columns={7},
        )

    def _render_actions_panel(self, rental_case_id: int, detail: CaseConsoleSnapshot) -> str:
        rows = []
        for action in detail.orchestration_snapshot.workflow_actions:
            actions = ""
            if action.status == "ready_to_execute":
                options = ['<option value="success">Fake success</option>']
                options.append('<option value="retryable_failure">Fake failure</option>')
                options.append('<option value="permanent_failure">Fake permanent failure</option>')
                options.append('<option value="timeout">Fake timeout</option>')
                options.append('<option value="ambiguous">Fake ambiguous</option>')
                if detail.provider_mode_lines and detail.provider_mode_lines[0] == "REAL PROVIDER EXECUTION ENABLED":
                    if action.target_adapter_code in {"email", "task_surface"}:
                        options.append('<option value="real">Real provider</option>')
                actions = (
                    f'<form method="post" action="/cases/{rental_case_id}/actions/{action.workflow_action_id}/execute" class="inline">'
                    f'<select name="execution_mode">{"".join(options)}</select>'
                    f'<button type="submit">Execute</button></form>'
                )
            rows.append(
                (
                    str(action.workflow_action_id),
                    action.action_type,
                    action.status,
                    action.approval_posture,
                    str(action.source_case_revision),
                    action.idempotency_key,
                    action.target_adapter_code,
                    action.updated_at,
                    actions,
                )
            )
        return self._render_simple_table(
            "Workflow Actions",
            ("Action ID", "Action Type", "Status", "Approval Posture", "Case Rev", "Idempotency", "Provider", "Updated", "Execute"),
            rows,
            raw_html_columns={8},
        )

    def _render_followups_panel(self, rental_case_id: int, detail: CaseConsoleSnapshot) -> str:
        button = (
            f'<div class="inline">'
            f'<form method="post" action="/cases/{rental_case_id}/inquiry-waiting" class="inline"><button type="submit">Evaluate Inquiry Waiting</button></form>'
            f'<form method="post" action="/cases/{rental_case_id}/followups/evaluate" class="inline"><button type="submit">Evaluate Follow-Ups</button></form>'
            f"</div>"
        )
        table = self._render_simple_table(
            "Follow-Ups",
            ("Type", "Sequence", "Due", "Status", "Attempt Count", "Next Action", "Missing / Related"),
            [
                (
                    follow_up.reason_code,
                    str(getattr(follow_up, "sequence_number", 1)),
                    follow_up.due_at,
                    follow_up.status,
                    str(follow_up.attempt_count),
                    humanize_code(follow_up.next_action_type) if follow_up.next_action_type else "",
                    ", ".join(
                        value
                        for value in (
                            (
                                ", ".join(
                                    str(label)
                                    for label in follow_up.context_payload.get("question_labels", [])
                                )
                                if isinstance(getattr(follow_up, "context_payload", None), dict)
                                else ""
                            ),
                            follow_up.waiting_for_reference or follow_up.waiting_for_role or "",
                        )
                        if value
                    ),
                )
                for follow_up in detail.orchestration_snapshot.follow_ups
            ],
        )
        return table.replace("</section>", f"{button}</section>")

    def _render_reasoning_panel(self, detail: CaseConsoleSnapshot) -> str:
        rows = [
            (
                projection.reasoning_purpose,
                projection.workflow_posture,
                projection.authority_outcome_classification,
                projection.reasoning_state_code,
                ", ".join(projection.warning_codes),
                ", ".join(projection.unresolved_authority_codes),
            )
            for projection in detail.orchestration_snapshot.reasoning_projections
        ]
        note = "Human-facing answer text is not treated as workflow truth. Only persisted structured state appears elsewhere in the console."
        return self._render_simple_table(
            "Reasoning Projection",
            ("Purpose", "Workflow Posture", "Authority", "Reasoning State", "Warnings", "Unresolved Authority"),
            rows,
            note=note,
        )

    def _render_asana_panel(self, detail: CaseConsoleSnapshot) -> str:
        master_ref = detail.asana_master_task_reference or "No Asana master task linked"
        preview_rows = [(line,) for line in detail.human_work_preview]
        panel = self._render_simple_table(
            "Human Work Preview",
            ("Projected Work",),
            preview_rows,
            note="This is a preview derived from existing structured state, not live Asana subtask state.",
        )
        return f"""
<section class="panel">
  <h2>Asana Master Task</h2>
  <p>{h(master_ref)}</p>
</section>
{panel}
"""

    def _render_timeline_panel(self, detail: CaseConsoleSnapshot) -> str:
        note = detail.timeline_notice
        if note is None and detail.workflow_event_total_count > len(detail.orchestration_snapshot.workflow_events):
            note = (
                f"Showing the most recent {len(detail.orchestration_snapshot.workflow_events)} "
                f"of {detail.workflow_event_total_count} WorkflowEvents."
            )
        rows = [
            (
                event.occurred_at,
                event.event_type_code,
                event.source_type,
                event.source_reference or "",
                event.actor_reference or "",
                render_value(event.structured_payload),
            )
            for event in detail.orchestration_snapshot.workflow_events
        ]
        return self._render_simple_table(
            "WorkflowEvent Timeline",
            ("Occurred", "Event Type", "Source Type", "Source Reference", "Actor", "Payload"),
            rows,
            note=note,
        )

    def _render_working_proposal(self, detail: CaseConsoleSnapshot) -> str:
        proposal = detail.working_proposal
        warning_group = (
            self._render_projection_group("Warnings & Authority", proposal.warnings)
            if proposal.warnings
            else ""
        )
        return f"""
<section class="panel highlight">
  <h2>Living Working Proposal / Case Overview</h2>
  <p class="note">This is a generated read-only projection of structured case truth. It is not a second truth store.</p>
  <div class="grid three">
    {self._render_projection_group("Rental Snapshot", proposal.rental_snapshot)}
    {self._render_projection_group("Commercial Position", proposal.commercial_snapshot)}
    {self._render_projection_group("Feasibility", proposal.feasibility_snapshot)}
    {self._render_projection_group("Missing Client Information", proposal.missing_client_information)}
    {self._render_projection_group("Requirements", proposal.requirements)}
    {self._render_projection_group("Blockers", proposal.blockers)}
    {self._render_projection_group("Approvals", proposal.approvals)}
    {self._render_projection_group("Current Working Scope", proposal.operations)}
    {self._render_projection_group("Proposed Changes", proposal.changes)}
    {self._render_projection_group("Communication & Follow-Up", proposal.communication)}
    {self._render_projection_group("Human Attention / Next Actions", proposal.next_actions)}
    {self._render_projection_group("Freshness / Audit Context", proposal.proposal_freshness)}
    {warning_group}
  </div>
</section>
"""

    def _render_projection_group(self, title: str, items: tuple[ProjectionItem, ...]) -> str:
        rendered_items = []
        for item in items:
            badge = f"<span class='projection-badge projection-badge--{h(item.state)}'>{h(item.state.replace('_', ' '))}</span>"
            detail = f"<p class='projection-detail'>{h(item.detail)}</p>" if item.detail else ""
            source = f"<p class='projection-source'>Source: {h(item.source)}</p>" if item.source else ""
            rendered_items.append(
                f"""
<li class="projection-item projection-item--{h(item.state)}">
  <div class="projection-head">
    <span class="projection-label">{h(item.label)}</span>
    {badge}
  </div>
  <div class="projection-value">{h(item.value)}</div>
  {detail}
  {source}
</li>
""".strip()
            )
        return f"<div class='projection'><h3>{h(title)}</h3><ul class='plain projection-list'>{''.join(rendered_items)}</ul></div>"

    def _render_clock_panel(self, current_path: str) -> str:
        status = self.service.get_clock_status()
        mode_label = "SIMULATED TIME ACTIVE" if status.simulated else "REAL/CURRENT TIME"
        detail_line = (
            f"<p class='note'>Real UTC right now: {h(status.real_current_time)}</p>"
            if status.simulated
            else "<p class='note'>The console is currently using real/current UTC time.</p>"
        )
        if not self._clock_controls_enabled():
            return f"""
<section class="panel highlight">
  <h2>Simulated Time</h2>
  <div class="grid two">
    <div>
      <p><strong>Current UTC:</strong> {h(status.current_time)}</p>
      <p>{pill(mode_label)}</p>
      {detail_line}
      <p class="note">Clock mutation controls are disabled outside the local test environment. This runtime always evaluates against the system clock.</p>
    </div>
    <div class="stack">
      <p class="note">Set/advance/reset controls are unavailable in this environment.</p>
    </div>
  </div>
</section>
"""
        return_path_input = f'<input type="hidden" name="return_path" value="{h(current_path)}">'
        return f"""
<section class="panel highlight">
  <h2>Simulated Time</h2>
  <div class="grid two">
    <div>
      <p><strong>Current UTC:</strong> {h(status.current_time)}</p>
      <p>{pill(mode_label)}</p>
      {detail_line}
      <p class="note">Clock state is local to this test-console process. Advancing time does not rewrite follow-up due dates; it only changes the evaluated current time.</p>
    </div>
    <div class="stack">
      <div class="inline wrap">
        <form method="post" action="/clock/advance" class="inline">
          {return_path_input}
          <input type="hidden" name="hours" value="1">
          <button type="submit">+1 hour</button>
        </form>
        <form method="post" action="/clock/advance" class="inline">
          {return_path_input}
          <input type="hidden" name="days" value="1">
          <button type="submit">+1 day</button>
        </form>
        <form method="post" action="/clock/advance" class="inline">
          {return_path_input}
          <input type="hidden" name="days" value="7">
          <button type="submit">+7 days</button>
        </form>
        <form method="post" action="/clock/reset" class="inline">
          {return_path_input}
          <button type="submit">Reset to real/current</button>
        </form>
      </div>
      <form method="post" action="/clock/set" class="stack">
        {return_path_input}
        <label>Set UTC time <input type="datetime-local" name="timestamp_value" value="{h(_datetime_local_value(status.current_time))}"></label>
        <button type="submit">Set time</button>
      </form>
    </div>
  </div>
</section>
"""

    def _render_simple_table(
        self,
        title: str,
        headers: tuple[str, ...],
        rows: list[tuple[str, ...]] | tuple[tuple[str, ...], ...],
        *,
        note: str | None = None,
        raw_html_columns: set[int] | None = None,
    ) -> str:
        raw_html_columns = raw_html_columns or set()
        head = "".join(f"<th>{h(header)}</th>" for header in headers)
        body = []
        for row in rows:
            cells = []
            for index, cell in enumerate(row):
                cells.append(f"<td>{cell if index in raw_html_columns else h(cell)}</td>")
            body.append("<tr>" + "".join(cells) + "</tr>")
        note_html = f"<p class='note'>{h(note)}</p>" if note else ""
        return f"""
<section class="panel">
  <h2>{h(title)}</h2>
  {note_html}
  <table>
    <thead><tr>{head}</tr></thead>
    <tbody>{''.join(body) or f'<tr><td colspan="{len(headers)}">No records.</td></tr>'}</tbody>
  </table>
</section>
"""

    def _render_report(self, report: OperationReport | None) -> str:
        if report is None:
            return ""
        classes = "report success" if report.success else "report failure"
        lines = "".join(f"<li>{h(line)}</li>" for line in report.lines)
        failures = "".join(f"<li>{h(code)}</li>" for code in report.failure_codes)
        return f"""
<section class="{classes}">
  <h2>{h(report.title)}</h2>
  <ul>{lines}</ul>
  {'<h3>Failure Codes</h3><ul>' + failures + '</ul>' if failures else ''}
</section>
"""

    def _render_error(
        self,
        message: str,
        *,
        failure_code: str | None = None,
        current_path: str = "/",
    ) -> str:
        code_html = f"<p><strong>Failure Code:</strong> {h(failure_code)}</p>" if failure_code else ""
        return self._render_layout(
            title="Rental Workflow Test Console Error",
            body=f"<section class='report failure'><h1>Error</h1>{code_html}<pre>{h(message)}</pre></section>",
            current_path=current_path,
        )

    def _render_layout(self, *, title: str, body: str, current_path: str) -> str:
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{h(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #1a1a1a;
      --muted: #5b5b5b;
      --paper: #f5f2ea;
      --panel: #fffdfa;
      --line: #d7cdbf;
      --accent: #0e6e59;
      --warning: #8a5a00;
      --danger: #9a2d1f;
      --success: #1b6a35;
      --shadow: rgba(34, 27, 17, 0.08);
      font-family: Georgia, "Times New Roman", serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; color: var(--ink); background:
      radial-gradient(circle at top left, rgba(14,110,89,0.08), transparent 28%),
      linear-gradient(180deg, #f8f5ee 0%, var(--paper) 100%);
    }}
    main {{ max-width: 1440px; margin: 0 auto; padding: 24px; }}
    h1, h2, h3 {{ margin: 0 0 12px; }}
    p, li, td, th, label, input, textarea, select, button {{ font-family: "Courier New", monospace; font-size: 14px; }}
    .hero, .panel, .report {{ background: var(--panel); border: 1px solid var(--line); border-radius: 16px; box-shadow: 0 18px 50px var(--shadow); padding: 18px; margin-bottom: 18px; }}
    .hero {{ display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }}
    .provider-banner {{ min-width: 280px; padding: 12px; border-radius: 12px; background: #efe7d7; border: 1px solid var(--line); }}
    .panel.highlight {{ background: linear-gradient(180deg, #fffdfa 0%, #f2efe5 100%); }}
    .grid {{ display: grid; gap: 16px; }}
    .grid.two {{ grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }}
    .grid.three {{ grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }}
    .projection {{ border: 1px solid var(--line); border-radius: 14px; padding: 12px; background: rgba(255,255,255,0.65); }}
    .projection-list {{ list-style: none; padding: 0; display: grid; gap: 10px; }}
    .projection-item {{ border: 1px solid rgba(215, 205, 191, 0.9); border-radius: 12px; padding: 10px; background: rgba(255,255,255,0.78); }}
    .projection-item--blocked {{ border-color: rgba(154, 45, 31, 0.35); background: rgba(154, 45, 31, 0.04); }}
    .projection-item--proposed {{ border-color: rgba(138, 90, 0, 0.35); background: rgba(138, 90, 0, 0.05); }}
    .projection-item--stale {{ border-color: rgba(91, 91, 91, 0.35); background: rgba(91, 91, 91, 0.05); }}
    .projection-head {{ display: flex; justify-content: space-between; gap: 10px; align-items: center; margin-bottom: 4px; }}
    .projection-label {{ font-weight: bold; }}
    .projection-value {{ font-size: 15px; }}
    .projection-detail, .projection-source {{ margin: 6px 0 0; color: var(--muted); }}
    .projection-badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px; border: 1px solid var(--line); font-size: 12px; text-transform: capitalize; background: #f5f0e5; }}
    .projection-badge--current {{ color: var(--success); border-color: rgba(27,106,53,0.25); background: rgba(27,106,53,0.08); }}
    .projection-badge--reference {{ color: var(--accent); border-color: rgba(14,110,89,0.25); background: rgba(14,110,89,0.08); }}
    .projection-badge--proposed {{ color: var(--warning); border-color: rgba(138,90,0,0.25); background: rgba(138,90,0,0.08); }}
    .projection-badge--blocked {{ color: var(--danger); border-color: rgba(154,45,31,0.25); background: rgba(154,45,31,0.08); }}
    .projection-badge--unresolved {{ color: var(--muted); }}
    .projection-badge--stale {{ color: var(--muted); }}
    .projection-badge--none {{ color: var(--muted); }}
    .plain {{ margin: 0; padding-left: 18px; }}
    .stack {{ display: grid; gap: 10px; }}
    .note {{ color: var(--muted); }}
    .muted {{ color: var(--muted); }}
    .report.success {{ border-color: rgba(27,106,53,0.35); }}
    .report.failure {{ border-color: rgba(154,45,31,0.35); }}
    .pill {{ display: inline-block; padding: 4px 10px; border-radius: 999px; border: 1px solid var(--line); background: #f5efe2; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; vertical-align: top; padding: 10px; border-top: 1px solid rgba(215,205,191,0.7); }}
    th {{ color: var(--muted); }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    label {{ display: grid; gap: 4px; color: var(--muted); }}
    input, textarea, select {{ width: 100%; border: 1px solid var(--line); border-radius: 10px; padding: 10px; background: white; color: var(--ink); }}
    button {{ border: 1px solid var(--ink); background: var(--ink); color: white; border-radius: 999px; padding: 10px 14px; cursor: pointer; }}
    button:hover {{ background: var(--accent); border-color: var(--accent); }}
    .inline {{ display: inline-flex; gap: 8px; align-items: center; margin-right: 8px; }}
    .wrap {{ flex-wrap: wrap; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #f8f4eb; border-radius: 10px; padding: 12px; }}
    .evidence-box {{ margin: 12px 0; padding: 12px; border-radius: 12px; background: #f8f4eb; }}
    @media (max-width: 900px) {{
      .hero {{ flex-direction: column; }}
      .provider-banner {{ width: 100%; min-width: 0; }}
    }}
  </style>
</head>
<body>
  <main>{self._render_clock_panel(current_path)}{body}</main>
</body>
</html>"""

    def _clock_controls_enabled(self) -> bool:
        method = getattr(self.service, "clock_controls_enabled", None)
        if callable(method):
            return bool(method())
        return True

    def _get_health_report(self):
        method = getattr(self.service, "get_health_report", None)
        if callable(method):
            return method()
        from .test_console_service import HealthComponentReport, TestConsoleHealthReport

        return TestConsoleHealthReport(
            overall_status="ok",
            environment=self.config.runtime.app_env.value,
            application=HealthComponentReport(status="ok", detail="WSGI application responded."),
            database=HealthComponentReport(status="ok", detail="Health checks are not implemented for this service fixture."),
            phase5=HealthComponentReport(status="ok", detail="Health checks are not implemented for this service fixture."),
            phase6=HealthComponentReport(status="ok", detail="Health checks are not implemented for this service fixture."),
            providers={"outlook": "disabled", "asana": "disabled"},
        )

    def _requires_authentication(self, path: str) -> bool:
        return self.config.runtime.requires_basic_auth() and path != "/healthz"

    def _is_operator_api_path(self, path: str) -> bool:
        return path == "/api/operator/cases" or path.startswith("/api/operator/cases/")

    def _base_operator_payload(self) -> dict[str, Any]:
        return {
            "environment": self.config.runtime.app_env.value,
            "clock": self._serialize_for_json(self.service.get_clock_status()),
            "clock_controls_enabled": self._clock_controls_enabled(),
        }

    def _operator_case_payload(self, rental_case_id: int, report: OperationReport) -> dict[str, Any]:
        return {
            **self._base_operator_payload(),
            "ok": report.success,
            "report": self._serialize_for_json(report),
            "case": self._serialize_for_json(self.service.load_case_detail(rental_case_id)),
        }

    def _find_created_case_summary(self, report: OperationReport) -> TestCaseSummary | None:
        case_reference = next(
            (line.removeprefix("RentalCase: ").strip() for line in report.lines if line.startswith("RentalCase: ")),
            None,
        )
        if not case_reference:
            return None
        for summary in self.service.list_test_cases():
            if summary.case_reference_code == case_reference:
                return summary
        return None

    def _serialize_for_json(self, value: Any) -> Any:
        if value is None:
            return None
        if is_dataclass(value):
            return self._serialize_for_json(asdict(value))
        if isinstance(value, dict):
            return {str(key): self._serialize_for_json(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set, frozenset)):
            return [self._serialize_for_json(item) for item in value]
        return value

    def _is_authenticated(self, environ: dict[str, Any]) -> bool:
        credentials = self.config.runtime.basic_auth_credentials()
        if credentials is None:
            return False
        authorization = environ.get("HTTP_AUTHORIZATION", "")
        if not isinstance(authorization, str):
            return False
        scheme, _, encoded = authorization.partition(" ")
        if scheme.lower() != "basic" or not encoded:
            return False
        try:
            decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError):
            return False
        username, separator, password = decoded.partition(":")
        if not separator:
            return False
        return hmac.compare_digest(username, credentials.username) and hmac.compare_digest(password, credentials.password)

    def _parse_form(self, environ: dict[str, Any]) -> dict[str, str]:
        try:
            size = int(environ.get("CONTENT_LENGTH") or "0")
        except ValueError:
            size = 0
        body = environ["wsgi.input"].read(size) if size > 0 else b""
        parsed = parse_qs(body.decode("utf-8"), keep_blank_values=True)
        return {key: values[-1] for key, values in parsed.items()}

    def _parse_json(self, environ: dict[str, Any]) -> dict[str, Any]:
        try:
            size = int(environ.get("CONTENT_LENGTH") or "0")
        except ValueError:
            size = 0
        raw_body = environ["wsgi.input"].read(size) if size > 0 else b""
        if not raw_body:
            return {}
        try:
            parsed = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TestConsoleError(
                "Request body must be valid JSON.",
                failure_code="INVALID_JSON_REQUEST",
            ) from exc
        if not isinstance(parsed, dict):
            raise TestConsoleError(
                "Request body must decode to a JSON object.",
                failure_code="INVALID_JSON_REQUEST",
            )
        return parsed

    def _required_json_field(self, payload: dict[str, Any], field_name: str) -> str:
        value = payload.get(field_name)
        if not isinstance(value, str):
            raise TestConsoleError(
                f"{field_name} is required.",
                failure_code="INVALID_JSON_REQUEST",
            )
        return value

    def _parse_question_prompt_payload(self, payload: Any) -> dict[int, str]:
        if payload is None:
            return {}
        if not isinstance(payload, dict):
            raise TestConsoleError(
                "question_prompt_text_by_id must be a JSON object.",
                failure_code="INVALID_JSON_REQUEST",
            )
        parsed: dict[int, str] = {}
        for key, value in payload.items():
            try:
                question_id = int(str(key))
            except ValueError as exc:
                raise TestConsoleError(
                    "question_prompt_text_by_id keys must be integer question ids.",
                    failure_code="INVALID_JSON_REQUEST",
                ) from exc
            if not isinstance(value, str):
                raise TestConsoleError(
                    "question_prompt_text_by_id values must be strings.",
                    failure_code="INVALID_JSON_REQUEST",
                )
            parsed[question_id] = value
        return parsed

    def _respond_html(
        self,
        start_response: Callable[..., Any],
        document: str,
        *,
        status: HTTPStatus = HTTPStatus.OK,
    ) -> list[bytes]:
        payload = document.encode("utf-8")
        start_response(
            f"{status.value} {status.phrase}",
            [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(payload)))],
        )
        return [payload]

    def _respond_text(self, start_response: Callable[..., Any], status: HTTPStatus, text: str) -> list[bytes]:
        payload = text.encode("utf-8")
        start_response(
            f"{status.value} {status.phrase}",
            [("Content-Type", "text/plain; charset=utf-8"), ("Content-Length", str(len(payload)))],
        )
        return [payload]

    def _respond_json(
        self,
        start_response: Callable[..., Any],
        payload: dict[str, Any],
        *,
        status: HTTPStatus = HTTPStatus.OK,
    ) -> list[bytes]:
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
        start_response(
            f"{status.value} {status.phrase}",
            [("Content-Type", "application/json; charset=utf-8"), ("Content-Length", str(len(encoded)))],
        )
        return [encoded]

    def _respond_json_error(
        self,
        start_response: Callable[..., Any],
        *,
        status: HTTPStatus,
        message: str,
        failure_code: str,
        www_authenticate: bool = False,
    ) -> list[bytes]:
        payload = {
            "ok": False,
            "error": {
                "message": message,
                "failure_code": failure_code,
                "status": status.value,
            },
        }
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
        headers = [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(encoded))),
        ]
        if www_authenticate:
            headers.append(("WWW-Authenticate", 'Basic realm="WNC Rental Test Console", charset="UTF-8"'))
        start_response(f"{status.value} {status.phrase}", headers)
        return [encoded]

    def _respond_unauthorized(self, start_response: Callable[..., Any]) -> list[bytes]:
        payload = b"Authentication required."
        start_response(
            f"{HTTPStatus.UNAUTHORIZED.value} {HTTPStatus.UNAUTHORIZED.phrase}",
            [
                ("Content-Type", "text/plain; charset=utf-8"),
                ("Content-Length", str(len(payload))),
                ("WWW-Authenticate", 'Basic realm="WNC Rental Test Console", charset="UTF-8"'),
            ],
        )
        return [payload]


def h(value: str) -> str:
    return html.escape(value, quote=True)


def pill(status: str) -> str:
    return f"<span class='pill'>{h(status)}</span>"


def render_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float)):
        return str(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return json_dump(value)


def json_dump(value: Any) -> str:
    buffer = io.StringIO()
    import json

    json.dump(value, buffer, sort_keys=True)
    return buffer.getvalue()


def _datetime_local_value(value: str) -> str:
    return parse_timestamp(value).strftime("%Y-%m-%dT%H:%M")


def build_test_console_app(*, config: TestConsoleConfig | None = None, service: TestConsoleService | None = None) -> TestConsoleApp:
    resolved_config = config
    if resolved_config is None and service is not None:
        candidate = getattr(service, "config", None)
        if isinstance(candidate, TestConsoleConfig):
            resolved_config = candidate
    if resolved_config is None:
        resolved_config = TestConsoleConfig.from_env()
    resolved_config.validate()
    if service is None:
        service = TestConsoleService(config=resolved_config)
    return TestConsoleApp(service)


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    config = TestConsoleConfig.from_env()
    if args.host is not None:
        config = replace(config, host=args.host)
    if args.port is not None:
        config = replace(config, port=args.port)
    config.validate()
    app = build_test_console_app(config=config)
    bind_url = f"http://{config.host}:{config.port}"
    print(f"Rental Workflow Test Console listening on {bind_url}")
    with make_server(
        config.host,
        config.port,
        app,
        server_class=ThreadingWSGIServer,
        handler_class=WSGIRequestHandler,
    ) as server:
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
