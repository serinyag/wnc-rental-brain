from __future__ import annotations

import json
import re
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping, Protocol

import certifi

from tools.phase_05_search.semantic_common import load_env_value

from .contracts import (
    ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
    ACTION_TYPE_REQUEST_CONFIRMATION_PAYMENT,
    ACTION_TYPE_REQUEST_FINAL_EVENT_INFORMATION,
    ACTION_TYPE_REQUEST_SIGNED_AGREEMENT,
    ACTION_TYPE_REQUEST_SUPPLIER_INFORMATION,
    ACTION_TYPE_SEND_DISCOVERY_CALL_INVITE,
    ACTION_TYPE_SEND_PROPOSAL_FOLLOW_UP,
    ACTION_TYPE_SEND_PROPOSAL_MESSAGE,
    ACTION_TYPE_SEND_SITE_VISIT_PROPOSAL,
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


DEFAULT_MICROSOFT_GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
DEFAULT_MICROSOFT_AUTHORITY_BASE_URL = "https://login.microsoftonline.com"
DEFAULT_OUTLOOK_TIMEOUT_SECONDS = 30
OUTLOOK_PROVIDER_NAME = "microsoft_graph_outlook"
OUTLOOK_EXTERNAL_REFERENCE_PREFIX = "outlook:message:"
OUTLOOK_IMMUTABLE_ID_HEADER = 'IdType="ImmutableId"'
OUTLOOK_SUPPORTED_MESSAGE_MODE_NEW = "new"

OUTLOOK_SUPPORTED_ACTION_TYPES = frozenset(
    {
        ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
        ACTION_TYPE_SEND_DISCOVERY_CALL_INVITE,
        ACTION_TYPE_SEND_SITE_VISIT_PROPOSAL,
        ACTION_TYPE_SEND_PROPOSAL_MESSAGE,
        ACTION_TYPE_SEND_PROPOSAL_FOLLOW_UP,
        ACTION_TYPE_REQUEST_CONFIRMATION_PAYMENT,
        ACTION_TYPE_REQUEST_SIGNED_AGREEMENT,
        ACTION_TYPE_REQUEST_FINAL_EVENT_INFORMATION,
        ACTION_TYPE_REQUEST_SUPPLIER_INFORMATION,
    }
)

EMAIL_ADDRESS_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
)


class OutlookTransportProtocol(Protocol):
    def request(
        self,
        *,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout_seconds: int,
    ) -> tuple[int, str, Mapping[str, str]]: ...


@dataclass(frozen=True)
class OutlookAdapterConfig:
    tenant_id: str | None
    client_id: str | None
    client_secret: str | None
    sender_mailbox: str | None
    graph_base_url: str = DEFAULT_MICROSOFT_GRAPH_BASE_URL
    authority_base_url: str = DEFAULT_MICROSOFT_AUTHORITY_BASE_URL
    timeout_seconds: int = DEFAULT_OUTLOOK_TIMEOUT_SECONDS

    @classmethod
    def from_env(cls) -> OutlookAdapterConfig:
        timeout_seconds = _parse_timeout_seconds(load_env_value("OUTLOOK_TIMEOUT_SECONDS"))
        return cls(
            tenant_id=_normalize_optional_text(load_env_value("MICROSOFT_TENANT_ID")),
            client_id=_normalize_optional_text(load_env_value("MICROSOFT_CLIENT_ID")),
            client_secret=_normalize_optional_text(load_env_value("MICROSOFT_CLIENT_SECRET")),
            sender_mailbox=_normalize_optional_text(load_env_value("OUTLOOK_SENDER_MAILBOX")),
            graph_base_url=_normalize_optional_text(load_env_value("MICROSOFT_GRAPH_BASE_URL"))
            or DEFAULT_MICROSOFT_GRAPH_BASE_URL,
            authority_base_url=_normalize_optional_text(load_env_value("MICROSOFT_AUTHORITY_BASE_URL"))
            or DEFAULT_MICROSOFT_AUTHORITY_BASE_URL,
            timeout_seconds=timeout_seconds,
        )

    def availability_failure_code(self, *, action: WorkflowAction) -> str | None:
        if action.action_type not in OUTLOOK_SUPPORTED_ACTION_TYPES:
            return EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID
        if not self.tenant_id or not self.client_id or not self.client_secret or not self.sender_mailbox:
            return EXECUTION_FAILURE_ADAPTER_CONFIGURATION_INVALID
        if not _is_valid_email_address(self.sender_mailbox):
            return EXECUTION_FAILURE_ADAPTER_CONFIGURATION_INVALID
        try:
            _parse_outlook_email_payload(action.structured_payload)
        except OutlookActionInputError:
            return EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID
        return None


class UrllibOutlookTransport:
    def __init__(self) -> None:
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())

    def request(
        self,
        *,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout_seconds: int,
    ) -> tuple[int, str, Mapping[str, str]]:
        request = urllib.request.Request(
            url=url,
            data=body,
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
            raise OutlookAmbiguousTransportError("timeout") from exc
        except socket.timeout as exc:
            raise OutlookAmbiguousTransportError("timeout") from exc
        except ssl.SSLError as exc:
            raise OutlookAmbiguousTransportError("ssl_error") from exc
        except urllib.error.URLError as exc:
            raise OutlookAmbiguousTransportError(_reason_code_from_url_error(exc)) from exc


@dataclass(frozen=True)
class OutlookEmailPayload:
    recipient_email: str
    recipient_name: str | None
    recipient_reference: str | None
    subject: str
    body: str
    body_type: str
    message_mode: str

    @property
    def graph_body_type(self) -> str:
        return "HTML" if self.body_type == "html" else "Text"


@dataclass
class OutlookExecutionAdapter:
    config: OutlookAdapterConfig
    transport: OutlookTransportProtocol

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
            email_payload = _parse_outlook_email_payload(action.structured_payload)
        except OutlookActionInputError as exc:
            return _failed_result(
                failure_code=exc.failure_code,
                reason=exc.reason,
            )

        retry_state = _resolve_retry_state(execution_context.prior_attempts)
        if retry_state.failure_code is not None:
            return _failed_result(
                failure_code=retry_state.failure_code,
                reason=retry_state.reason,
                external_reference=retry_state.external_reference,
                stage=retry_state.stage,
            )

        token_result = self._acquire_access_token()
        if token_result.result is not None:
            return token_result.result
        access_token = token_result.access_token
        if access_token is None:
            return _failed_result(
                failure_code=EXECUTION_FAILURE_ADAPTER_RESULT_MALFORMED,
                reason="missing_access_token",
                stage="token",
            )

        message_id = retry_state.message_id
        if message_id is None:
            draft_result = self._create_draft(
                access_token=access_token,
                email_payload=email_payload,
            )
            if draft_result.result is not None:
                return draft_result.result
            message_id = draft_result.message_id
            if message_id is None:
                return _failed_result(
                    failure_code=EXECUTION_FAILURE_ADAPTER_RESULT_MALFORMED,
                    reason="missing_message_id",
                    stage="create_draft",
                )

        external_reference = _external_reference_for_message_id(message_id)
        send_result = self._send_draft(
            access_token=access_token,
            message_id=message_id,
            external_reference=external_reference,
        )
        if send_result is not None:
            return send_result

        return self._verify_sent_message(
            access_token=access_token,
            message_id=message_id,
            external_reference=external_reference,
        )

    def _acquire_access_token(self) -> _AccessTokenResult:
        payload = urllib.parse.urlencode(
            {
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "scope": "https://graph.microsoft.com/.default",
                "grant_type": "client_credentials",
            }
        ).encode("utf-8")
        try:
            status_code, body_text, response_headers = self.transport.request(
                method="POST",
                url=(
                    f"{self.config.authority_base_url.rstrip('/')}/"
                    f"{urllib.parse.quote(self.config.tenant_id or '', safe='')}/oauth2/v2.0/token"
                ),
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                },
                body=payload,
                timeout_seconds=self.config.timeout_seconds,
            )
        except OutlookAmbiguousTransportError as exc:
            return _AccessTokenResult(
                result=_failed_result(
                    failure_code=EXECUTION_FAILURE_ADAPTER_SERVER_ERROR,
                    reason="token_transport_error",
                    retry_eligible=True,
                    stage="token",
                    transport_error=exc.reason_code,
                )
            )

        parsed, invalid_json = _load_json(body_text)
        if invalid_json:
            if 200 <= status_code < 300:
                return _AccessTokenResult(
                    result=_failed_result(
                        failure_code=EXECUTION_FAILURE_ADAPTER_RESULT_MALFORMED,
                        reason="invalid_token_json",
                        stage="token",
                    )
                )
            failure_code, retry_eligible = _classify_http_failure(status_code=status_code)
            return _AccessTokenResult(
                result=_failed_result(
                    failure_code=failure_code,
                    reason="invalid_token_error_json",
                    retry_eligible=retry_eligible,
                    stage="token",
                    http_status=status_code,
                    retry_after_seconds=_parse_retry_after_seconds(response_headers),
                )
            )

        if 200 <= status_code < 300:
            access_token = parsed.get("access_token") if isinstance(parsed, dict) else None
            token_type = parsed.get("token_type") if isinstance(parsed, dict) else None
            if not isinstance(access_token, str) or not access_token.strip():
                return _AccessTokenResult(
                    result=_failed_result(
                        failure_code=EXECUTION_FAILURE_ADAPTER_RESULT_MALFORMED,
                        reason="missing_access_token",
                        stage="token",
                    )
                )
            if isinstance(token_type, str) and token_type.lower() != "bearer":
                return _AccessTokenResult(
                    result=_failed_result(
                        failure_code=EXECUTION_FAILURE_ADAPTER_RESULT_MALFORMED,
                        reason="unsupported_token_type",
                        stage="token",
                    )
                )
            return _AccessTokenResult(access_token=access_token.strip())

        failure_code, retry_eligible = _classify_token_failure(status_code=status_code)
        return _AccessTokenResult(
            result=_failed_result(
                failure_code=failure_code,
                reason="token_request_failed",
                retry_eligible=retry_eligible,
                stage="token",
                http_status=status_code,
                provider_error_code=_extract_provider_error_code(parsed),
                retry_after_seconds=_parse_retry_after_seconds(response_headers),
            )
        )

    def _create_draft(
        self,
        *,
        access_token: str,
        email_payload: OutlookEmailPayload,
    ) -> _DraftResult:
        try:
            status_code, body_text, response_headers = self.transport.request(
                method="POST",
                url=f"{self.config.graph_base_url.rstrip('/')}/users/{urllib.parse.quote(self.config.sender_mailbox or '', safe='')}/messages",
                headers=_graph_json_headers(access_token),
                body=json.dumps(
                    _build_create_draft_payload(email_payload),
                    sort_keys=True,
                    ensure_ascii=True,
                ).encode("utf-8"),
                timeout_seconds=self.config.timeout_seconds,
            )
        except OutlookAmbiguousTransportError as exc:
            return _DraftResult(
                result=_failed_result(
                    failure_code=EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS,
                    reason="create_draft_transport_error",
                    stage="create_draft",
                    transport_error=exc.reason_code,
                )
            )

        parsed, invalid_json = _load_json(body_text)
        if invalid_json:
            if 200 <= status_code < 300:
                return _DraftResult(
                    result=_failed_result(
                        failure_code=EXECUTION_FAILURE_ADAPTER_RESULT_MALFORMED,
                        reason="invalid_create_draft_json",
                        stage="create_draft",
                        http_status=status_code,
                    )
                )
            failure_code, retry_eligible = _classify_http_failure(status_code=status_code)
            return _DraftResult(
                result=_failed_result(
                    failure_code=failure_code,
                    reason="invalid_create_draft_error_json",
                    retry_eligible=retry_eligible,
                    stage="create_draft",
                    http_status=status_code,
                    retry_after_seconds=_parse_retry_after_seconds(response_headers),
                )
            )

        if 200 <= status_code < 300:
            message_id = parsed.get("id") if isinstance(parsed, dict) else None
            is_draft = parsed.get("isDraft") if isinstance(parsed, dict) else None
            if not isinstance(message_id, str) or not message_id.strip():
                return _DraftResult(
                    result=_failed_result(
                        failure_code=EXECUTION_FAILURE_ADAPTER_RESULT_MALFORMED,
                        reason="missing_message_id",
                        stage="create_draft",
                        http_status=status_code,
                    )
                )
            if is_draft is not None and is_draft is not True:
                return _DraftResult(
                    result=_failed_result(
                        failure_code=EXECUTION_FAILURE_ADAPTER_RESULT_MALFORMED,
                        reason="provider_returned_non_draft_message",
                        stage="create_draft",
                        http_status=status_code,
                    )
                )
            return _DraftResult(message_id=message_id.strip())

        failure_code, retry_eligible = _classify_http_failure(status_code=status_code)
        return _DraftResult(
            result=_failed_result(
                failure_code=failure_code,
                reason="create_draft_failed",
                retry_eligible=retry_eligible,
                stage="create_draft",
                http_status=status_code,
                provider_error_code=_extract_provider_error_code(parsed),
                retry_after_seconds=_parse_retry_after_seconds(response_headers),
            )
        )

    def _send_draft(
        self,
        *,
        access_token: str,
        message_id: str,
        external_reference: str,
    ) -> NormalizedExecutionResult | None:
        try:
            status_code, body_text, response_headers = self.transport.request(
                method="POST",
                url=(
                    f"{self.config.graph_base_url.rstrip('/')}/users/"
                    f"{urllib.parse.quote(self.config.sender_mailbox or '', safe='')}/messages/"
                    f"{urllib.parse.quote(message_id, safe='')}/send"
                ),
                headers=_graph_json_headers(access_token),
                body=None,
                timeout_seconds=self.config.timeout_seconds,
            )
        except OutlookAmbiguousTransportError as exc:
            return _failed_result(
                failure_code=EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS,
                reason="send_draft_transport_error",
                stage="send_draft",
                transport_error=exc.reason_code,
                external_reference=external_reference,
            )

        if 200 <= status_code < 300:
            return None

        parsed, invalid_json = _load_json(body_text)
        failure_code, retry_eligible = _classify_http_failure(status_code=status_code)
        return _failed_result(
            failure_code=failure_code,
            reason="send_draft_failed" if not invalid_json else "invalid_send_draft_error_json",
            retry_eligible=retry_eligible,
            stage="send_draft",
            http_status=status_code,
            provider_error_code=None if invalid_json else _extract_provider_error_code(parsed),
            retry_after_seconds=_parse_retry_after_seconds(response_headers),
            external_reference=external_reference,
        )

    def _verify_sent_message(
        self,
        *,
        access_token: str,
        message_id: str,
        external_reference: str,
    ) -> NormalizedExecutionResult:
        try:
            status_code, body_text, _response_headers = self.transport.request(
                method="GET",
                url=(
                    f"{self.config.graph_base_url.rstrip('/')}/users/"
                    f"{urllib.parse.quote(self.config.sender_mailbox or '', safe='')}/messages/"
                    f"{urllib.parse.quote(message_id, safe='')}?$select=id,isDraft,sentDateTime"
                ),
                headers=_graph_json_headers(access_token),
                body=None,
                timeout_seconds=self.config.timeout_seconds,
            )
        except OutlookAmbiguousTransportError as exc:
            return _failed_result(
                failure_code=EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS,
                reason="verify_sent_message_transport_error",
                stage="verify_sent_message",
                transport_error=exc.reason_code,
                external_reference=external_reference,
            )

        parsed, invalid_json = _load_json(body_text)
        if invalid_json:
            return _failed_result(
                failure_code=EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS,
                reason="invalid_verify_sent_json",
                stage="verify_sent_message",
                http_status=status_code,
                external_reference=external_reference,
            )

        if 200 <= status_code < 300:
            message_id_result = parsed.get("id") if isinstance(parsed, dict) else None
            is_draft = parsed.get("isDraft") if isinstance(parsed, dict) else None
            sent_at = parsed.get("sentDateTime") if isinstance(parsed, dict) else None
            if (
                isinstance(message_id_result, str)
                and message_id_result.strip() == message_id
                and is_draft is False
                and isinstance(sent_at, str)
                and sent_at.strip()
            ):
                return NormalizedExecutionResult(
                    adapter_code="email",
                    attempt_status=EXECUTION_ATTEMPT_STATUS_SUCCEEDED,
                    response_snapshot={
                        "provider": OUTLOOK_PROVIDER_NAME,
                        "stage": "verify_sent_message",
                        "message_id": message_id,
                        "sent_at": sent_at.strip(),
                    },
                    external_reference=external_reference,
                )
            return _failed_result(
                failure_code=EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS,
                reason="send_verification_inconclusive",
                stage="verify_sent_message",
                http_status=status_code,
                external_reference=external_reference,
            )

        return _failed_result(
            failure_code=EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS,
            reason="verify_sent_message_failed",
            stage="verify_sent_message",
            http_status=status_code,
            provider_error_code=_extract_provider_error_code(parsed),
            external_reference=external_reference,
        )


def build_outlook_execution_adapter_from_env(
    *,
    transport: OutlookTransportProtocol | None = None,
) -> OutlookExecutionAdapter:
    return OutlookExecutionAdapter(
        config=OutlookAdapterConfig.from_env(),
        transport=transport or UrllibOutlookTransport(),
    )


@dataclass(frozen=True)
class OutlookActionInputError(RuntimeError):
    failure_code: str
    reason: str


@dataclass(frozen=True)
class OutlookAmbiguousTransportError(RuntimeError):
    reason_code: str


@dataclass(frozen=True)
class _AccessTokenResult:
    access_token: str | None = None
    result: NormalizedExecutionResult | None = None


@dataclass(frozen=True)
class _DraftResult:
    message_id: str | None = None
    result: NormalizedExecutionResult | None = None


@dataclass(frozen=True)
class _RetryState:
    message_id: str | None = None
    external_reference: str | None = None
    failure_code: str | None = None
    reason: str | None = None
    stage: str | None = None


def _parse_outlook_email_payload(payload: Mapping[str, Any]) -> OutlookEmailPayload:
    recipient_email = _require_non_empty_string(payload.get("recipient_email"), field_name="recipient_email")
    if not _is_valid_email_address(recipient_email):
        raise OutlookActionInputError(
            failure_code=EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID,
            reason="invalid_recipient_email",
        )
    recipient_name = _optional_non_empty_string(payload.get("recipient_name"), field_name="recipient_name")
    recipient_reference = _optional_non_empty_string(
        payload.get("recipient_reference"),
        field_name="recipient_reference",
    )
    subject = _require_non_empty_string(payload.get("subject"), field_name="subject")
    body = _require_non_empty_string(payload.get("body"), field_name="body")
    body_type = _require_non_empty_string(payload.get("body_type"), field_name="body_type").lower()
    if body_type not in {"text", "html"}:
        raise OutlookActionInputError(
            failure_code=EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID,
            reason="unsupported_body_type",
        )
    message_mode = _require_non_empty_string(payload.get("message_mode"), field_name="message_mode").lower()
    if message_mode != OUTLOOK_SUPPORTED_MESSAGE_MODE_NEW:
        raise OutlookActionInputError(
            failure_code=EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID,
            reason="reply_mode_not_supported_in_phase_8_7b",
        )
    if _optional_non_empty_string(payload.get("source_message_reference"), field_name="source_message_reference") is not None:
        raise OutlookActionInputError(
            failure_code=EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID,
            reason="source_message_reference_requires_reply_support",
        )
    if payload.get("to_recipients") is not None:
        raise OutlookActionInputError(
            failure_code=EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID,
            reason="multiple_to_recipients_not_supported",
        )
    if payload.get("cc_recipients") is not None:
        raise OutlookActionInputError(
            failure_code=EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID,
            reason="cc_not_supported",
        )
    if payload.get("bcc_recipients") is not None:
        raise OutlookActionInputError(
            failure_code=EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID,
            reason="bcc_not_supported",
        )
    attachments = payload.get("attachments")
    if attachments not in (None, (), [], {}):
        raise OutlookActionInputError(
            failure_code=EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID,
            reason="attachments_not_supported",
        )
    return OutlookEmailPayload(
        recipient_email=recipient_email,
        recipient_name=recipient_name,
        recipient_reference=recipient_reference,
        subject=subject,
        body=body,
        body_type=body_type,
        message_mode=message_mode,
    )


def _build_create_draft_payload(email_payload: OutlookEmailPayload) -> dict[str, Any]:
    email_address: dict[str, str] = {"address": email_payload.recipient_email}
    if email_payload.recipient_name is not None:
        email_address["name"] = email_payload.recipient_name
    return {
        "subject": email_payload.subject,
        "body": {
            "contentType": email_payload.graph_body_type,
            "content": email_payload.body,
        },
        "toRecipients": [{"emailAddress": email_address}],
    }


def _resolve_retry_state(prior_attempts: tuple[Any, ...]) -> _RetryState:
    outlook_attempts = [
        attempt
        for attempt in prior_attempts
        if isinstance(attempt.external_reference, str)
        and attempt.external_reference.startswith(OUTLOOK_EXTERNAL_REFERENCE_PREFIX)
    ]
    if not outlook_attempts:
        return _RetryState()

    distinct_references = tuple(
        dict.fromkeys(
            attempt.external_reference.strip()
            for attempt in sorted(outlook_attempts, key=lambda attempt: attempt.attempt_number)
            if isinstance(attempt.external_reference, str) and attempt.external_reference.strip()
        )
    )
    if len(distinct_references) != 1:
        return _RetryState(
            failure_code=EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS,
            reason="multiple_provider_message_identities_for_same_action",
            stage="retry_preflight",
        )

    external_reference = distinct_references[0]
    message_id = _message_id_from_external_reference(external_reference)
    latest_attempt = max(outlook_attempts, key=lambda attempt: attempt.attempt_number)
    if latest_attempt.failure_code == EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS:
        return _RetryState(
            message_id=message_id,
            external_reference=external_reference,
            failure_code=EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS,
            reason="prior_outlook_attempt_requires_manual_reconciliation",
            stage="retry_preflight",
        )
    return _RetryState(
        message_id=message_id,
        external_reference=external_reference,
    )


def _graph_json_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": OUTLOOK_IMMUTABLE_ID_HEADER,
    }


def _classify_token_failure(status_code: int) -> tuple[str, bool]:
    if status_code in {400, 401}:
        return EXECUTION_FAILURE_ADAPTER_AUTHENTICATION_FAILED, False
    if status_code == 403:
        return EXECUTION_FAILURE_ADAPTER_FORBIDDEN, False
    return _classify_http_failure(status_code=status_code)


def _classify_http_failure(*, status_code: int) -> tuple[str, bool]:
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
    if 500 <= status_code <= 599:
        return EXECUTION_FAILURE_ADAPTER_SERVER_ERROR, True
    return EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID, False


def _failed_result(
    *,
    failure_code: str,
    reason: str,
    retry_eligible: bool = False,
    stage: str | None = None,
    http_status: int | None = None,
    provider_error_code: str | None = None,
    retry_after_seconds: int | None = None,
    transport_error: str | None = None,
    external_reference: str | None = None,
) -> NormalizedExecutionResult:
    snapshot: dict[str, Any] = {
        "provider": OUTLOOK_PROVIDER_NAME,
        "reason": reason,
    }
    if stage is not None:
        snapshot["stage"] = stage
    if http_status is not None:
        snapshot["http_status"] = http_status
    if provider_error_code is not None:
        snapshot["provider_error_code"] = provider_error_code
    if retry_after_seconds is not None:
        snapshot["retry_after_seconds"] = retry_after_seconds
    if transport_error is not None:
        snapshot["transport_error"] = transport_error
    return NormalizedExecutionResult(
        adapter_code="email",
        attempt_status=EXECUTION_ATTEMPT_STATUS_FAILED,
        response_snapshot=snapshot,
        retry_eligible=retry_eligible,
        external_reference=external_reference,
        failure_code=failure_code,
    )


def _external_reference_for_message_id(message_id: str) -> str:
    return f"{OUTLOOK_EXTERNAL_REFERENCE_PREFIX}{message_id.strip()}"


def _message_id_from_external_reference(external_reference: str) -> str | None:
    if not external_reference.startswith(OUTLOOK_EXTERNAL_REFERENCE_PREFIX):
        return None
    suffix = external_reference[len(OUTLOOK_EXTERNAL_REFERENCE_PREFIX) :].strip()
    return suffix or None


def _extract_provider_error_code(parsed: Any) -> str | None:
    if not isinstance(parsed, dict):
        return None
    error_payload = parsed.get("error")
    if isinstance(error_payload, dict):
        code = error_payload.get("code")
        if isinstance(code, str) and code.strip():
            return code.strip()
    error_code = parsed.get("error")
    if isinstance(error_code, str) and error_code.strip():
        return error_code.strip()
    return None


def _load_json(body_text: str) -> tuple[Any, bool]:
    if not body_text.strip():
        return {}, False
    try:
        return json.loads(body_text), False
    except json.JSONDecodeError:
        return {}, True


def _parse_retry_after_seconds(headers: Mapping[str, str]) -> int | None:
    raw_value = headers.get("Retry-After") or headers.get("retry-after")
    if raw_value is None:
        return None
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _parse_timeout_seconds(raw_value: str | None) -> int:
    if raw_value is None:
        return DEFAULT_OUTLOOK_TIMEOUT_SECONDS
    try:
        parsed = int(raw_value)
    except ValueError:
        return DEFAULT_OUTLOOK_TIMEOUT_SECONDS
    return parsed if parsed > 0 else DEFAULT_OUTLOOK_TIMEOUT_SECONDS


def _require_non_empty_string(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OutlookActionInputError(
            failure_code=EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID,
            reason=f"missing_or_invalid_{field_name}",
        )
    return value.strip()


def _optional_non_empty_string(value: Any, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise OutlookActionInputError(
            failure_code=EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID,
            reason=f"invalid_{field_name}",
        )
    trimmed = value.strip()
    if not trimmed:
        raise OutlookActionInputError(
            failure_code=EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID,
            reason=f"invalid_{field_name}",
        )
    return trimmed


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def _is_valid_email_address(value: str) -> bool:
    return bool(EMAIL_ADDRESS_PATTERN.match(value.strip()))


def _reason_code_from_url_error(error: urllib.error.URLError) -> str:
    reason = error.reason
    if isinstance(reason, TimeoutError):
        return "timeout"
    if isinstance(reason, ssl.SSLError):
        return "ssl_error"
    if isinstance(reason, OSError):
        return reason.__class__.__name__.lower()
    return str(reason) if reason else "url_error"
