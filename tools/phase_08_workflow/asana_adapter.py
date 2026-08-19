from __future__ import annotations

import json
import socket
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping, Protocol

import certifi

from tools.phase_05_search.semantic_common import load_env_value

from .contracts import (
    ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
    EXECUTION_ATTEMPT_STATUS_FAILED,
    EXECUTION_ATTEMPT_STATUS_SUCCEEDED,
    WorkflowAction,
)
from .execution_types import (
    EXECUTION_FAILURE_ADAPTER_AUTHENTICATION_FAILED,
    EXECUTION_FAILURE_ADAPTER_CONFIGURATION_INVALID,
    EXECUTION_FAILURE_ADAPTER_FORBIDDEN,
    EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS,
    EXECUTION_FAILURE_ADAPTER_RATE_LIMITED,
    EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID,
    EXECUTION_FAILURE_ADAPTER_RESOURCE_NOT_FOUND,
    EXECUTION_FAILURE_ADAPTER_RESULT_MALFORMED,
    EXECUTION_FAILURE_ADAPTER_SERVER_ERROR,
    ExecutionContext,
    ExecutionIdempotencyContext,
    NormalizedExecutionResult,
)


DEFAULT_ASANA_API_BASE_URL = "https://app.asana.com/api/1.0"
DEFAULT_ASANA_TIMEOUT_SECONDS = 30


class AsanaTransportProtocol(Protocol):
    def send_json(
        self,
        *,
        method: str,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, Any],
        timeout_seconds: int,
    ) -> tuple[int, str, Mapping[str, str]]: ...


@dataclass(frozen=True)
class AsanaAdapterConfig:
    access_token: str | None
    workspace_gid: str | None
    default_project_gid: str | None
    api_base_url: str = DEFAULT_ASANA_API_BASE_URL
    timeout_seconds: int = DEFAULT_ASANA_TIMEOUT_SECONDS

    @classmethod
    def from_env(cls) -> AsanaAdapterConfig:
        timeout_seconds = _parse_timeout_seconds(load_env_value("ASANA_TIMEOUT_SECONDS"))
        return cls(
            access_token=_normalize_optional_text(load_env_value("ASANA_ACCESS_TOKEN")),
            workspace_gid=_normalize_optional_text(load_env_value("ASANA_WORKSPACE_GID")),
            default_project_gid=_normalize_optional_text(load_env_value("ASANA_DEFAULT_PROJECT_GID")),
            api_base_url=_normalize_optional_text(load_env_value("ASANA_API_BASE_URL")) or DEFAULT_ASANA_API_BASE_URL,
            timeout_seconds=timeout_seconds,
        )

    def availability_failure_code(self, *, action: WorkflowAction) -> str | None:
        if action.action_type != ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM:
            return EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID
        if not self.access_token or not self.workspace_gid:
            return EXECUTION_FAILURE_ADAPTER_CONFIGURATION_INVALID
        if _resolve_project_gid(action, default_project_gid=self.default_project_gid) is None:
            return EXECUTION_FAILURE_ADAPTER_CONFIGURATION_INVALID
        return None


class UrllibAsanaTransport:
    def __init__(self) -> None:
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())

    def send_json(
        self,
        *,
        method: str,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, Any],
        timeout_seconds: int,
    ) -> tuple[int, str, Mapping[str, str]]:
        request = urllib.request.Request(
            url=url,
            data=json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8"),
            headers=dict(headers),
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds, context=self.ssl_context) as response:
                return (
                    response.status,
                    response.read().decode("utf-8"),
                    dict(response.headers.items()),
                )
        except urllib.error.HTTPError as exc:
            return (
                exc.code,
                exc.read().decode("utf-8", errors="replace"),
                dict(exc.headers.items()),
            )
        except TimeoutError as exc:
            raise AsanaAmbiguousTransportError("timeout") from exc
        except socket.timeout as exc:
            raise AsanaAmbiguousTransportError("timeout") from exc
        except ssl.SSLError as exc:
            raise AsanaAmbiguousTransportError("ssl_error") from exc
        except urllib.error.URLError as exc:
            raise AsanaAmbiguousTransportError(_reason_code_from_url_error(exc)) from exc


@dataclass
class AsanaExecutionAdapter:
    config: AsanaAdapterConfig
    transport: AsanaTransportProtocol

    def availability_failure_code(self, *, action: WorkflowAction) -> str | None:
        return self.config.availability_failure_code(action=action)

    def execute(
        self,
        *,
        action: WorkflowAction,
        execution_context: ExecutionContext,
        idempotency: ExecutionIdempotencyContext,
    ) -> NormalizedExecutionResult:
        del idempotency
        try:
            payload = _build_asana_task_payload(
                action=action,
                execution_context=execution_context,
                workspace_gid=self.config.workspace_gid,
                default_project_gid=self.config.default_project_gid,
            )
        except AsanaActionInputError as exc:
            return NormalizedExecutionResult(
                adapter_code="asana",
                attempt_status=EXECUTION_ATTEMPT_STATUS_FAILED,
                response_snapshot={"provider": "asana", "reason": exc.reason},
                retry_eligible=False,
                failure_code=exc.failure_code,
            )

        try:
            status_code, body_text, response_headers = self.transport.send_json(
                method="POST",
                url=f"{self.config.api_base_url.rstrip('/')}/tasks",
                headers={
                    "Authorization": f"Bearer {self.config.access_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                payload={"data": payload},
                timeout_seconds=self.config.timeout_seconds,
            )
        except AsanaAmbiguousTransportError as exc:
            return NormalizedExecutionResult(
                adapter_code="asana",
                attempt_status=EXECUTION_ATTEMPT_STATUS_FAILED,
                response_snapshot={
                    "provider": "asana",
                    "reason": "ambiguous_transport_failure",
                    "transport_error": exc.reason_code,
                },
                retry_eligible=False,
                failure_code=EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS,
            )

        try:
            parsed = json.loads(body_text) if body_text.strip() else {}
        except json.JSONDecodeError:
            return NormalizedExecutionResult(
                adapter_code="asana",
                attempt_status=EXECUTION_ATTEMPT_STATUS_FAILED,
                response_snapshot={
                    "provider": "asana",
                    "http_status": status_code,
                    "reason": "invalid_json",
                },
                retry_eligible=False,
                failure_code=EXECUTION_FAILURE_ADAPTER_RESULT_MALFORMED,
            )

        if 200 <= status_code < 300:
            task_payload = parsed.get("data")
            task_gid = task_payload.get("gid") if isinstance(task_payload, dict) else None
            if not isinstance(task_gid, str) or not task_gid.strip():
                return NormalizedExecutionResult(
                    adapter_code="asana",
                    attempt_status=EXECUTION_ATTEMPT_STATUS_FAILED,
                    response_snapshot={
                        "provider": "asana",
                        "http_status": status_code,
                        "reason": "missing_task_gid",
                    },
                    retry_eligible=False,
                    failure_code=EXECUTION_FAILURE_ADAPTER_RESULT_MALFORMED,
                )
            return NormalizedExecutionResult(
                adapter_code="asana",
                attempt_status=EXECUTION_ATTEMPT_STATUS_SUCCEEDED,
                response_snapshot={
                    "provider": "asana",
                    "http_status": status_code,
                    "task_gid": task_gid,
                },
                external_reference=f"asana:task:{task_gid.strip()}",
            )

        retry_after_seconds = _parse_retry_after_seconds(response_headers)
        error_messages = _extract_error_messages(parsed)
        failure_code, retry_eligible = _classify_asana_failure(status_code=status_code)
        snapshot: dict[str, Any] = {
            "provider": "asana",
            "http_status": status_code,
            "error_messages": error_messages,
        }
        if retry_after_seconds is not None:
            snapshot["retry_after_seconds"] = retry_after_seconds
        return NormalizedExecutionResult(
            adapter_code="asana",
            attempt_status=EXECUTION_ATTEMPT_STATUS_FAILED,
            response_snapshot=snapshot,
            retry_eligible=retry_eligible,
            failure_code=failure_code,
        )


def build_asana_execution_adapter_from_env(
    *,
    transport: AsanaTransportProtocol | None = None,
) -> AsanaExecutionAdapter:
    return AsanaExecutionAdapter(
        config=AsanaAdapterConfig.from_env(),
        transport=transport or UrllibAsanaTransport(),
    )


@dataclass(frozen=True)
class AsanaActionInputError(RuntimeError):
    failure_code: str
    reason: str


@dataclass(frozen=True)
class AsanaAmbiguousTransportError(RuntimeError):
    reason_code: str


def _build_asana_task_payload(
    *,
    action: WorkflowAction,
    execution_context: ExecutionContext,
    workspace_gid: str | None,
    default_project_gid: str | None,
) -> dict[str, Any]:
    payload = action.structured_payload
    summary = _require_non_empty_string(payload.get("summary"), field_name="summary")
    reason = _require_non_empty_string(payload.get("reason"), field_name="reason")
    task_kind = _require_non_empty_string(payload.get("task_kind"), field_name="task_kind")
    project_gid = _resolve_project_gid(action, default_project_gid=default_project_gid)
    if project_gid is None:
        raise AsanaActionInputError(
            failure_code=EXECUTION_FAILURE_ADAPTER_CONFIGURATION_INVALID,
            reason="missing_project_gid",
        )
    if workspace_gid is None:
        raise AsanaActionInputError(
            failure_code=EXECUTION_FAILURE_ADAPTER_CONFIGURATION_INVALID,
            reason="missing_workspace_gid",
        )

    section_gid = _optional_non_empty_string(payload.get("task_surface_section_id"), field_name="task_surface_section_id")
    assignee_gid = _optional_non_empty_string(payload.get("task_surface_assignee_id"), field_name="task_surface_assignee_id")
    due_on = _optional_non_empty_string(payload.get("task_surface_due_on"), field_name="task_surface_due_on")
    context_lines = _normalize_context_lines(payload.get("task_surface_context_lines"))

    task_payload: dict[str, Any] = {
        "name": summary,
        "notes": _build_task_notes(
            reason=reason,
            context_lines=context_lines,
            case_reference_code=execution_context.case_reference_code,
            rental_case_id=execution_context.rental_case_id,
            workflow_action_id=action.workflow_action_id,
            workflow_action_uuid=action.workflow_action_uuid,
            action_type=action.action_type,
            task_kind=task_kind,
            idempotency_key=action.idempotency_key,
        ),
        "workspace": workspace_gid,
    }
    if section_gid is not None:
        task_payload["memberships"] = [{"project": project_gid, "section": section_gid}]
    else:
        task_payload["projects"] = [project_gid]
    if assignee_gid is not None:
        task_payload["assignee"] = assignee_gid
    if due_on is not None:
        task_payload["due_on"] = due_on
    elif action.due_at is not None:
        if "T" in action.due_at:
            task_payload["due_at"] = action.due_at
        else:
            task_payload["due_on"] = action.due_at
    return task_payload


def _build_task_notes(
    *,
    reason: str,
    context_lines: tuple[str, ...],
    case_reference_code: str | None,
    rental_case_id: int,
    workflow_action_id: int,
    workflow_action_uuid: str,
    action_type: str,
    task_kind: str,
    idempotency_key: str,
) -> str:
    note_lines = [reason]
    if context_lines:
        note_lines.extend(("", "Context:"))
        note_lines.extend(f"- {line}" for line in context_lines)
    note_lines.extend(
        (
            "",
            f"Rental Case: {case_reference_code or rental_case_id}",
            f"Rental Case ID: {rental_case_id}",
            f"Workflow Action ID: {workflow_action_id}",
            f"Workflow Action UUID: {workflow_action_uuid}",
            f"Action Type: {action_type}",
            f"Task Kind: {task_kind}",
            f"Semantic Idempotency Key: {idempotency_key}",
        )
    )
    return "\n".join(note_lines)


def _normalize_context_lines(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise AsanaActionInputError(
            failure_code=EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID,
            reason="task_surface_context_lines_must_be_list",
        )
    normalized: list[str] = []
    for item in value:
        normalized.append(_require_non_empty_string(item, field_name="task_surface_context_lines"))
    return tuple(normalized)


def _resolve_project_gid(action: WorkflowAction, *, default_project_gid: str | None) -> str | None:
    payload_project_gid = _optional_non_empty_string(
        action.structured_payload.get("task_surface_project_id"),
        field_name="task_surface_project_id",
    )
    return payload_project_gid or default_project_gid


def _classify_asana_failure(*, status_code: int) -> tuple[str, bool]:
    if status_code == 400:
        return EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID, False
    if status_code == 401:
        return EXECUTION_FAILURE_ADAPTER_AUTHENTICATION_FAILED, False
    if status_code == 403:
        return EXECUTION_FAILURE_ADAPTER_FORBIDDEN, False
    if status_code == 404:
        return EXECUTION_FAILURE_ADAPTER_RESOURCE_NOT_FOUND, False
    if status_code == 429:
        return EXECUTION_FAILURE_ADAPTER_RATE_LIMITED, True
    if status_code >= 500:
        return EXECUTION_FAILURE_ADAPTER_SERVER_ERROR, True
    return EXECUTION_FAILURE_ADAPTER_RESULT_MALFORMED, False


def _extract_error_messages(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return []
    errors = payload.get("errors")
    if not isinstance(errors, list):
        return []
    messages: list[str] = []
    for error in errors:
        if not isinstance(error, dict):
            continue
        message = error.get("message")
        if isinstance(message, str) and message.strip():
            messages.append(message.strip())
    return messages


def _parse_retry_after_seconds(headers: Mapping[str, str]) -> int | None:
    for key, value in headers.items():
        if key.lower() != "retry-after":
            continue
        try:
            retry_after = int(value)
        except ValueError:
            return None
        return retry_after if retry_after >= 0 else None
    return None


def _parse_timeout_seconds(value: str | None) -> int:
    if value is None:
        return DEFAULT_ASANA_TIMEOUT_SECONDS
    try:
        parsed = int(value)
    except ValueError:
        return DEFAULT_ASANA_TIMEOUT_SECONDS
    return parsed if parsed > 0 else DEFAULT_ASANA_TIMEOUT_SECONDS


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def _optional_non_empty_string(value: Any, *, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_non_empty_string(value, field_name=field_name)


def _require_non_empty_string(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise AsanaActionInputError(
            failure_code=EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID,
            reason=f"{field_name}_must_be_string",
        )
    normalized = value.strip()
    if not normalized:
        raise AsanaActionInputError(
            failure_code=EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID,
            reason=f"{field_name}_must_be_non_empty",
        )
    return normalized


def _reason_code_from_url_error(exc: urllib.error.URLError) -> str:
    reason = exc.reason
    if isinstance(reason, (TimeoutError, socket.timeout)):
        return "timeout"
    if isinstance(reason, ssl.SSLError):
        return "ssl_error"
    return "connection_error"
