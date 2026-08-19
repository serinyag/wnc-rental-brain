from __future__ import annotations

import argparse
import base64
import json
import os
import socket
import ssl
import sys
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import certifi


DEFAULT_BASE_URL_ENV = "WNC_OPERATOR_BASE_URL"
DEFAULT_USERNAME_ENV = "STAGING_BASIC_AUTH_USERNAME"
DEFAULT_PASSWORD_ENV = "STAGING_BASIC_AUTH_PASSWORD"


class OperatorHarnessError(RuntimeError):
    pass


@dataclass(frozen=True)
class OperatorHarnessConfig:
    base_url: str
    username: str | None
    password: str | None
    timeout_seconds: float = 30.0


class OperatorHarnessClient:
    def __init__(
        self,
        config: OperatorHarnessConfig,
        *,
        opener: Callable[..., Any] = urlopen,
        ssl_context: ssl.SSLContext | None = None,
    ) -> None:
        self.config = config
        self.opener = opener
        self.ssl_context = ssl_context or ssl.create_default_context(cafile=certifi.where())

    def get_health(self) -> dict[str, Any]:
        return self.request("GET", "/healthz")

    def list_cases(self) -> dict[str, Any]:
        return self.request("GET", "/api/operator/cases")

    def create_case(
        self,
        *,
        label: str | None,
        client_label: str | None,
        contact_email: str | None,
        event_reference: str | None,
    ) -> dict[str, Any]:
        return self.request(
            "POST",
            "/api/operator/cases",
            {
                "label": label,
                "client_label": client_label,
                "contact_email": contact_email,
                "event_reference": event_reference,
            },
        )

    def get_case(self, *, rental_case_id: int) -> dict[str, Any]:
        return self.request("GET", f"/api/operator/cases/{rental_case_id}")

    def run_inquiry_intake(self, *, rental_case_id: int) -> dict[str, Any]:
        return self.request("POST", f"/api/operator/cases/{rental_case_id}/inquiry-intake", {})

    def run_inquiry_waiting(self, *, rental_case_id: int) -> dict[str, Any]:
        return self.request("POST", f"/api/operator/cases/{rental_case_id}/inquiry-waiting", {})

    def run_reconciliation(self, *, rental_case_id: int) -> dict[str, Any]:
        return self.request("POST", f"/api/operator/cases/{rental_case_id}/reconcile", {})

    def evaluate_followups(self, *, rental_case_id: int) -> dict[str, Any]:
        return self.request("POST", f"/api/operator/cases/{rental_case_id}/followups/evaluate", {})

    def inject_raw_evidence(
        self,
        *,
        rental_case_id: int,
        source_label: str | None,
        sender: str | None,
        subject: str | None,
        body: str | None,
        received_at: str | None,
        external_test_reference: str | None,
    ) -> dict[str, Any]:
        return self.request(
            "POST",
            f"/api/operator/cases/{rental_case_id}/raw-evidence",
            {
                "source_label": source_label,
                "sender": sender,
                "subject": subject,
                "body": body,
                "received_at": received_at,
                "external_test_reference": external_test_reference,
            },
        )

    def inject_structured_observation(
        self,
        *,
        rental_case_id: int,
        field_code: str,
        observation_type: str,
        claim_kind: str,
        value_text: str,
        source_excerpt: str | None,
        sender_reference: str | None,
        external_test_reference: str | None,
    ) -> dict[str, Any]:
        return self.request(
            "POST",
            f"/api/operator/cases/{rental_case_id}/structured-observations",
            {
                "field_code": field_code,
                "observation_type": observation_type,
                "claim_kind": claim_kind,
                "value_text": value_text,
                "source_excerpt": source_excerpt,
                "sender_reference": sender_reference,
                "external_test_reference": external_test_reference,
            },
        )

    def generate_draft(self, *, rental_case_id: int, workflow_action_id: int) -> dict[str, Any]:
        return self.request(
            "POST",
            f"/api/operator/cases/{rental_case_id}/mailbox/actions/{workflow_action_id}/generate",
            {},
        )

    def edit_draft(
        self,
        *,
        rental_case_id: int,
        draft_revision_id: int,
        subject: str,
        salutation: str,
        intro_text: str,
        closing_text: str,
        signoff_text: str,
        question_prompt_text_by_id: dict[int, str],
    ) -> dict[str, Any]:
        return self.request(
            "POST",
            f"/api/operator/cases/{rental_case_id}/mailbox/drafts/{draft_revision_id}/edit",
            {
                "subject": subject,
                "salutation": salutation,
                "intro_text": intro_text,
                "closing_text": closing_text,
                "signoff_text": signoff_text,
                "question_prompt_text_by_id": {str(key): value for key, value in question_prompt_text_by_id.items()},
            },
        )

    def approve(self, *, rental_case_id: int, approval_request_id: int) -> dict[str, Any]:
        return self.request("POST", f"/api/operator/cases/{rental_case_id}/approvals/{approval_request_id}/approve", {})

    def reject(self, *, rental_case_id: int, approval_request_id: int) -> dict[str, Any]:
        return self.request("POST", f"/api/operator/cases/{rental_case_id}/approvals/{approval_request_id}/reject", {})

    def execute_action(
        self,
        *,
        rental_case_id: int,
        workflow_action_id: int,
        execution_mode: str,
    ) -> dict[str, Any]:
        return self.request(
            "POST",
            f"/api/operator/cases/{rental_case_id}/actions/{workflow_action_id}/execute",
            {"execution_mode": execution_mode},
        )

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        request = self._build_request(method, path, payload)
        try:
            with self.opener(request, timeout=self.config.timeout_seconds, context=self.ssl_context) as response:
                response_body = response.read().decode("utf-8")
        except HTTPError as exc:
            response_body = exc.read().decode("utf-8", errors="replace")
            raise OperatorHarnessError(self._format_http_error(exc.code, response_body)) from exc
        except (TimeoutError, socket.timeout) as exc:
            raise OperatorHarnessError(
                f"Operator request timed out after {self.config.timeout_seconds:g} seconds."
            ) from exc
        except URLError as exc:
            raise OperatorHarnessError(f"Operator request failed: {exc.reason}") from exc
        try:
            return json.loads(response_body) if response_body else {}
        except json.JSONDecodeError as exc:
            raise OperatorHarnessError("Operator endpoint returned non-JSON output.") from exc

    def _build_request(self, method: str, path: str, payload: dict[str, Any] | None) -> Request:
        headers = {"Accept": "application/json"}
        body = None
        if payload is not None:
            headers["Content-Type"] = "application/json; charset=utf-8"
            body = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
        authorization = _basic_auth_header_value(self.config.username, self.config.password)
        if authorization is not None:
            headers["Authorization"] = authorization
        return Request(
            _join_url(self.config.base_url, path),
            data=body,
            headers=headers,
            method=method.upper(),
        )

    def _format_http_error(self, status_code: int, response_body: str) -> str:
        try:
            payload = json.loads(response_body)
        except json.JSONDecodeError:
            return f"Operator request failed with HTTP {status_code}: {response_body.strip() or 'no response body'}"
        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict):
                failure_code = error.get("failure_code", "UNKNOWN")
                message = error.get("message", "Operator request failed.")
                return f"Operator request failed with HTTP {status_code}: {failure_code}: {message}"
        return f"Operator request failed with HTTP {status_code}."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Drive the WNC staging operator API over HTTP.")
    parser.add_argument("--base-url", default=os.environ.get(DEFAULT_BASE_URL_ENV), help=f"Operator base URL. Defaults to ${DEFAULT_BASE_URL_ENV}.")
    parser.add_argument(
        "--username-env",
        default=DEFAULT_USERNAME_ENV,
        help=f"Environment variable containing the staging Basic Auth username. Defaults to {DEFAULT_USERNAME_ENV}.",
    )
    parser.add_argument(
        "--password-env",
        default=DEFAULT_PASSWORD_ENV,
        help=f"Environment variable containing the staging Basic Auth password. Defaults to {DEFAULT_PASSWORD_ENV}.",
    )
    parser.add_argument("--timeout-seconds", type=float, default=30.0, help="HTTP timeout in seconds.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("health", help="Fetch /healthz.")
    subparsers.add_parser("list-cases", help="List cases through the operator API.")

    create_case = subparsers.add_parser("create-case", help="Create a synthetic case.")
    create_case.add_argument("--label")
    create_case.add_argument("--client-label")
    create_case.add_argument("--contact-email")
    create_case.add_argument("--event-reference")

    get_case = subparsers.add_parser("get-case", help="Fetch one case snapshot.")
    get_case.add_argument("--case-id", type=int, required=True)

    raw = subparsers.add_parser("inject-raw-evidence", help="Inject raw test evidence.")
    raw.add_argument("--case-id", type=int, required=True)
    raw.add_argument("--source-label")
    raw.add_argument("--sender")
    raw.add_argument("--subject")
    raw.add_argument("--body")
    raw.add_argument("--received-at")
    raw.add_argument("--external-test-reference")

    structured = subparsers.add_parser("inject-structured-observation", help="Inject one structured observation.")
    structured.add_argument("--case-id", type=int, required=True)
    structured.add_argument("--field-code", required=True)
    structured.add_argument("--observation-type", required=True)
    structured.add_argument("--claim-kind", required=True)
    structured.add_argument("--value-text", required=True)
    structured.add_argument("--source-excerpt")
    structured.add_argument("--sender-reference")
    structured.add_argument("--external-test-reference")

    for command_name, help_text in (
        ("run-inquiry-intake", "Run Inquiry Intake."),
        ("run-inquiry-waiting", "Run Inquiry Waiting."),
        ("run-reconciliation", "Run reconciliation."),
        ("evaluate-followups", "Evaluate follow-ups."),
    ):
        subparser = subparsers.add_parser(command_name, help=help_text)
        subparser.add_argument("--case-id", type=int, required=True)

    generate = subparsers.add_parser("generate-draft", help="Generate a draft for a workflow action.")
    generate.add_argument("--case-id", type=int, required=True)
    generate.add_argument("--workflow-action-id", type=int, required=True)

    edit = subparsers.add_parser("edit-draft", help="Save a human-edited draft revision.")
    edit.add_argument("--case-id", type=int, required=True)
    edit.add_argument("--draft-revision-id", type=int, required=True)
    edit.add_argument("--subject", required=True)
    edit.add_argument("--salutation", required=True)
    edit.add_argument("--intro-text", required=True)
    edit.add_argument("--closing-text", required=True)
    edit.add_argument("--signoff-text", required=True)
    edit.add_argument(
        "--question-prompt",
        action="append",
        default=[],
        metavar="OPEN_QUESTION_ID=TEXT",
        help="Question prompt override for a specific open question id. Repeat as needed.",
    )

    for command_name, help_text in (
        ("approve", "Approve an approval request."),
        ("reject", "Reject an approval request."),
    ):
        subparser = subparsers.add_parser(command_name, help=help_text)
        subparser.add_argument("--case-id", type=int, required=True)
        subparser.add_argument("--approval-request-id", type=int, required=True)

    execute = subparsers.add_parser("execute-action", help="Execute a workflow action.")
    execute.add_argument("--case-id", type=int, required=True)
    execute.add_argument("--workflow-action-id", type=int, required=True)
    execute.add_argument("--execution-mode", default="success")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.base_url:
        parser.error(f"--base-url is required or set ${DEFAULT_BASE_URL_ENV}.")
    username = os.environ.get(args.username_env)
    password = os.environ.get(args.password_env)
    client = OperatorHarnessClient(
        OperatorHarnessConfig(
            base_url=args.base_url,
            username=username,
            password=password,
            timeout_seconds=args.timeout_seconds,
        )
    )
    try:
        result = _dispatch_command(client, args)
    except OperatorHarnessError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
    return 0


def _dispatch_command(client: OperatorHarnessClient, args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "health":
        return client.get_health()
    if args.command == "list-cases":
        return client.list_cases()
    if args.command == "create-case":
        return client.create_case(
            label=args.label,
            client_label=args.client_label,
            contact_email=args.contact_email,
            event_reference=args.event_reference,
        )
    if args.command == "get-case":
        return client.get_case(rental_case_id=args.case_id)
    if args.command == "inject-raw-evidence":
        return client.inject_raw_evidence(
            rental_case_id=args.case_id,
            source_label=args.source_label,
            sender=args.sender,
            subject=args.subject,
            body=args.body,
            received_at=args.received_at,
            external_test_reference=args.external_test_reference,
        )
    if args.command == "inject-structured-observation":
        return client.inject_structured_observation(
            rental_case_id=args.case_id,
            field_code=args.field_code,
            observation_type=args.observation_type,
            claim_kind=args.claim_kind,
            value_text=args.value_text,
            source_excerpt=args.source_excerpt,
            sender_reference=args.sender_reference,
            external_test_reference=args.external_test_reference,
        )
    if args.command == "run-inquiry-intake":
        return client.run_inquiry_intake(rental_case_id=args.case_id)
    if args.command == "run-inquiry-waiting":
        return client.run_inquiry_waiting(rental_case_id=args.case_id)
    if args.command == "run-reconciliation":
        return client.run_reconciliation(rental_case_id=args.case_id)
    if args.command == "evaluate-followups":
        return client.evaluate_followups(rental_case_id=args.case_id)
    if args.command == "generate-draft":
        return client.generate_draft(rental_case_id=args.case_id, workflow_action_id=args.workflow_action_id)
    if args.command == "edit-draft":
        return client.edit_draft(
            rental_case_id=args.case_id,
            draft_revision_id=args.draft_revision_id,
            subject=args.subject,
            salutation=args.salutation,
            intro_text=args.intro_text,
            closing_text=args.closing_text,
            signoff_text=args.signoff_text,
            question_prompt_text_by_id=_parse_question_prompts(args.question_prompt),
        )
    if args.command == "approve":
        return client.approve(rental_case_id=args.case_id, approval_request_id=args.approval_request_id)
    if args.command == "reject":
        return client.reject(rental_case_id=args.case_id, approval_request_id=args.approval_request_id)
    if args.command == "execute-action":
        return client.execute_action(
            rental_case_id=args.case_id,
            workflow_action_id=args.workflow_action_id,
            execution_mode=args.execution_mode,
        )
    raise OperatorHarnessError(f"Unsupported command: {args.command}")


def _parse_question_prompts(items: list[str]) -> dict[int, str]:
    prompts: dict[int, str] = {}
    for item in items:
        question_id_text, separator, prompt_text = item.partition("=")
        if not separator:
            raise OperatorHarnessError(
                f"Invalid --question-prompt value {item!r}. Expected OPEN_QUESTION_ID=TEXT."
            )
        try:
            question_id = int(question_id_text)
        except ValueError as exc:
            raise OperatorHarnessError(
                f"Invalid question id {question_id_text!r} in --question-prompt."
            ) from exc
        prompts[question_id] = prompt_text
    return prompts


def _basic_auth_header_value(username: str | None, password: str | None) -> str | None:
    if username is None and password is None:
        return None
    if not username or not password:
        raise OperatorHarnessError("Both staging Basic Auth username and password env vars must be set.")
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def _join_url(base_url: str, path: str) -> str:
    normalized_base = base_url.rstrip("/")
    normalized_path = path if path.startswith("/") else f"/{path}"
    return f"{normalized_base}{normalized_path}"


if __name__ == "__main__":
    raise SystemExit(main())
