from __future__ import annotations

import json
import socket
import ssl
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Mapping

import certifi

from tools.phase_05_search.semantic_common import load_env_value

from .answer_generator import BoundedAnswerGeneratorRequest
from .contracts import Phase7ContractError


DEFAULT_OPENAI_API_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_ANSWER_MODEL = "gpt-5.6"
DEFAULT_OPENAI_ANSWER_TIMEOUT_SECONDS = 60
DEFAULT_OPENAI_ANSWER_MAX_OUTPUT_TOKENS = 1500
DEFAULT_OPENAI_ANSWER_TEMPERATURE: float | None = None


TransportResult = tuple[dict[str, Any], dict[str, str]]
OpenAITransport = Callable[[dict[str, Any], str, dict[str, str], int, ssl.SSLContext], TransportResult]


@dataclass(frozen=True)
class OpenAIAnswerGeneratorConfig:
    model_code: str = DEFAULT_OPENAI_ANSWER_MODEL
    api_base_url: str = DEFAULT_OPENAI_API_BASE_URL
    timeout_seconds: int = DEFAULT_OPENAI_ANSWER_TIMEOUT_SECONDS
    max_output_tokens: int = DEFAULT_OPENAI_ANSWER_MAX_OUTPUT_TOKENS
    temperature: float | None = DEFAULT_OPENAI_ANSWER_TEMPERATURE

    def __post_init__(self) -> None:
        if not isinstance(self.model_code, str) or not self.model_code.strip():
            raise ValueError("model_code must be a non-empty string.")
        if not isinstance(self.api_base_url, str) or not self.api_base_url.strip():
            raise ValueError("api_base_url must be a non-empty string.")
        if not isinstance(self.timeout_seconds, int) or self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be a positive integer.")
        if not isinstance(self.max_output_tokens, int) or self.max_output_tokens <= 0:
            raise ValueError("max_output_tokens must be a positive integer.")
        if self.temperature is not None and not isinstance(self.temperature, (int, float)):
            raise ValueError("temperature must be numeric when supplied.")


class OpenAIAnswerProviderError(RuntimeError):
    def __init__(self, safe_message: str) -> None:
        self.safe_message = safe_message
        super().__init__(safe_message)


class OpenAIAnswerModelUnavailableError(OpenAIAnswerProviderError):
    pass


@dataclass(frozen=True)
class OpenAIAnswerResponseMetadata:
    provider: str
    model: str
    response_id: str | None
    provider_request_id: str | None
    client_request_id: str
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    latency_ms: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "response_id": self.response_id,
            "provider_request_id": self.provider_request_id,
            "client_request_id": self.client_request_id,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": self.latency_ms,
        }


class OpenAIAnswerGenerator:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        config: OpenAIAnswerGeneratorConfig | None = None,
        transport: OpenAITransport | None = None,
    ) -> None:
        raw_api_key = api_key or load_env_value("OPENAI_API_KEY")
        cleaned_api_key = None
        if raw_api_key is not None:
            stripped = raw_api_key.strip()
            cleaned_api_key = stripped.split()[0] if stripped else None
        if not cleaned_api_key:
            raise SystemExit(
                "OPENAI_API_KEY is required for live answer generation and evaluation."
            )

        configured_model = load_env_value("OPENAI_ANSWER_MODEL")
        base_config = config or OpenAIAnswerGeneratorConfig(
            model_code=configured_model or DEFAULT_OPENAI_ANSWER_MODEL
        )

        self.api_key = cleaned_api_key
        self.config = base_config
        self.transport = transport or _default_openai_transport
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.call_count = 0
        self.last_request_payload: dict[str, Any] | None = None
        self.last_request_json: str | None = None
        self.last_response_payload: dict[str, Any] | None = None
        self.last_response_metadata: dict[str, Any] | None = None

    def build_provider_request(
        self,
        request: BoundedAnswerGeneratorRequest,
        *,
        client_request_id: str | None = None,
    ) -> dict[str, Any]:
        actual_request_id = client_request_id or f"phase7-answer-{uuid.uuid4().hex}"
        payload = {
            "model": self.config.model_code,
            "store": False,
            "input": [
                {
                    "role": "system",
                    "content": _system_prompt(request),
                },
                {
                    "role": "user",
                    "content": _user_prompt(request),
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "phase7_answer_result",
                    "description": "Structured bounded answer result for the Phase 7 answer layer.",
                    "strict": True,
                    "schema": _answer_result_schema(),
                }
            },
            "max_output_tokens": self.config.max_output_tokens,
            "metadata": {
                "phase": "7.3c",
                "contract": "bounded_answer_generator_request_v1",
                "client_request_id": actual_request_id,
            },
        }
        if self.config.temperature is not None:
            payload["temperature"] = self.config.temperature
        return payload

    def generate(self, request: BoundedAnswerGeneratorRequest) -> object:
        client_request_id = f"phase7-answer-{uuid.uuid4().hex}"
        payload = self.build_provider_request(request, client_request_id=client_request_id)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Client-Request-Id": client_request_id,
        }

        self.call_count += 1
        self.last_request_payload = payload
        self.last_request_json = json.dumps(payload, sort_keys=True, ensure_ascii=True)

        start = time.perf_counter()
        response_json, response_headers = self.transport(
            payload,
            self.config.api_base_url,
            headers,
            self.config.timeout_seconds,
            self.ssl_context,
        )
        latency_ms = max(1, int((time.perf_counter() - start) * 1000))

        self.last_response_payload = response_json
        self.last_response_metadata = _build_response_metadata(
            response_json=response_json,
            response_headers=response_headers,
            configured_model=self.config.model_code,
            client_request_id=client_request_id,
            latency_ms=latency_ms,
        ).to_dict()

        return _extract_structured_output(response_json)


def _default_openai_transport(
    payload: dict[str, Any],
    api_base_url: str,
    headers: dict[str, str],
    timeout_seconds: int,
    ssl_context: ssl.SSLContext,
) -> TransportResult:
    request = urllib.request.Request(
        url=f"{api_base_url.rstrip('/')}/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout_seconds,
            context=ssl_context,
        ) as response:
            body = response.read().decode("utf-8")
            parsed = json.loads(body)
            normalized_headers = {
                key.lower(): value
                for key, value in response.headers.items()
            }
            return parsed, normalized_headers
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        lowered_body = body.lower()
        if exc.code == 401:
            raise OpenAIAnswerProviderError(
                "HTTP 401: OpenAI rejected the supplied API key for answer generation."
            ) from exc
        if exc.code in {400, 404} and (
            "model" in lowered_body
            and ("not found" in lowered_body or "does not exist" in lowered_body or "unavailable" in lowered_body)
        ):
            raise OpenAIAnswerModelUnavailableError(
                "Configured OpenAI answer model is unavailable."
            ) from exc
        if exc.code == 429 and "credit_balance_exhausted" in lowered_body:
            raise OpenAIAnswerProviderError(
                "HTTP 429: OpenAI reported insufficient quota for answer generation."
            ) from exc
        raise OpenAIAnswerProviderError(
            f"HTTP {exc.code}: OpenAI answer generation request failed."
        ) from exc
    except socket.timeout as exc:
        raise TimeoutError("OpenAI answer generation timed out.") from exc
    except ssl.SSLError as exc:
        raise OpenAIAnswerProviderError(
            f"SSL verification failed while calling OpenAI answer generation: {exc}"
        ) from exc
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, socket.timeout):
            raise TimeoutError("OpenAI answer generation timed out.") from exc
        raise OpenAIAnswerProviderError(
            f"OpenAI answer generation transport failed: {exc.reason}"
        ) from exc


def _system_prompt(request: BoundedAnswerGeneratorRequest) -> str:
    rules = "\n".join(f"- {rule}" for rule in request.immutable_rules)
    hierarchy = "\n".join(f"- {rule}" for rule in request.authority_hierarchy)
    prohibited = "\n".join(f"- {rule}" for rule in request.prohibited_behaviors)
    restriction_lines = "\n".join(
        f"- {instruction}" for instruction in request.restriction_instructions
    ) or "- none"
    degraded_instruction = request.degraded_state_instruction or "No degraded-state warning is required."
    return (
        "You are the bounded synthesis backend for the WNC Rental Brain answer layer.\n"
        "Treat the supplied generator-safe context as the complete factual universe for this answer.\n"
        "Use outside knowledge only for ordinary wording and connective phrasing, never to supply missing WNC facts.\n"
        "Return only JSON matching the provided schema.\n"
        "Echo the supplied request-state metadata exactly; do not reinterpret authority, answer mode, warnings, or degraded-state flags.\n"
        "When historical claim frames are used in answer_text, introduce that material with the literal label 'Historical context:'.\n"
        "Keep answer_text concise, direct, and non-repetitive.\n"
        "Never mention suppressed, removed, hidden, or internal-only context.\n"
        "\n"
        "Immutable rules:\n"
        f"{rules}\n"
        "\n"
        "Authority hierarchy:\n"
        f"{hierarchy}\n"
        "\n"
        "Prohibited behaviors:\n"
        f"{prohibited}\n"
        "\n"
        "Restriction instructions:\n"
        f"{restriction_lines}\n"
        "\n"
        f"Degraded-state instruction:\n- {degraded_instruction}"
    )


def _user_prompt(request: BoundedAnswerGeneratorRequest) -> str:
    request_payload = {
        "query_text": request.query_text,
        "required_response_metadata": {
            "status": "completed",
            "answer_mode": request.answer_mode,
            "authority_outcome": request.authority_outcome,
            "generation_decision": request.generation_decision,
            "confirmation_required": request.confirmation_required,
            "insufficient_current_authority": request.insufficient_current_authority,
            "degraded_context_present": request.degraded_context_present,
            "materially_affects_answer_completeness": request.materially_affects_answer_completeness,
            "warning_codes": list(request.required_warning_codes),
            "failure_code": None,
            "answer_contract_version": request.answer_contract_version,
        },
        "answer_mode": request.answer_mode,
        "authority_outcome": request.authority_outcome,
        "generation_decision": request.generation_decision,
        "confirmation_required": request.confirmation_required,
        "insufficient_current_authority": request.insufficient_current_authority,
        "degraded_context_present": request.degraded_context_present,
        "materially_affects_answer_completeness": request.materially_affects_answer_completeness,
        "answer_mode_instruction": request.answer_mode_instruction,
        "claim_frames": [frame.to_dict() for frame in request.claim_frames],
        "safe_grounding": [reference.to_dict() for reference in request.safe_grounding],
        "required_warning_codes": list(request.required_warning_codes),
    }
    return (
        "Synthesize the answer result using only this bounded request data.\n"
        + json.dumps(request_payload, indent=2, ensure_ascii=True, sort_keys=True)
    )


def _answer_result_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "status": {
                "type": "string",
                "enum": ["completed", "blocked", "failed"],
            },
            "answer_mode": {
                "type": "string",
                "enum": [
                    "authoritative_current",
                    "current_with_historical_context",
                    "historical_descriptive",
                    "confirmation_required",
                    "insufficient_current_authority",
                    "blocked",
                ],
            },
            "authority_outcome": {
                "type": "string",
                "enum": [
                    "DETERMINISTIC_CURRENT",
                    "CURRENT_GUIDANCE",
                    "HISTORICAL_PRECEDENT",
                    "MIXED_WITH_CURRENT_PRIORITY",
                    "REQUIRES_CONFIRMATION",
                    "INSUFFICIENT_CURRENT_AUTHORITY",
                ],
            },
            "generation_decision": {
                "type": "string",
                "enum": ["allowed", "allowed_with_restrictions", "blocked"],
            },
            "confirmation_required": {"type": "boolean"},
            "insufficient_current_authority": {"type": "boolean"},
            "degraded_context_present": {"type": "boolean"},
            "materially_affects_answer_completeness": {"type": "boolean"},
            "answer_text": {
                "type": ["string", "null"],
            },
            "grounding_uses": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "claim_id": {"type": "string"},
                        "reference_id": {"type": "string"},
                        "source_layer_role": {
                            "type": "string",
                            "enum": [
                                "deterministic_rule",
                                "current_governed_knowledge",
                                "historical_precedent",
                            ],
                        },
                    },
                    "required": ["claim_id", "reference_id", "source_layer_role"],
                },
            },
            "warning_codes": {
                "type": "array",
                "items": {"type": "string"},
            },
            "failure_code": {
                "type": ["string", "null"],
            },
            "answer_contract_version": {
                "type": "integer",
                "enum": [1],
            },
        },
        "required": [
            "status",
            "answer_mode",
            "authority_outcome",
            "generation_decision",
            "confirmation_required",
            "insufficient_current_authority",
            "degraded_context_present",
            "materially_affects_answer_completeness",
            "answer_text",
            "grounding_uses",
            "warning_codes",
            "failure_code",
            "answer_contract_version",
        ],
    }


def _extract_structured_output(response_json: Mapping[str, Any]) -> dict[str, Any]:
    if not response_json:
        raise Phase7ContractError(
            error_category="invalid_value",
            safe_message="OpenAI answer generation returned an empty response payload.",
        )

    output_text = response_json.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return _parse_response_text(output_text)

    output_items = response_json.get("output")
    if not isinstance(output_items, list):
        raise Phase7ContractError(
            error_category="invalid_value",
            safe_message="OpenAI answer generation response did not include output items.",
        )

    for output_item in output_items:
        if not isinstance(output_item, dict):
            continue
        if output_item.get("type") != "message":
            continue
        content_items = output_item.get("content")
        if not isinstance(content_items, list):
            continue
        for content_item in content_items:
            if not isinstance(content_item, dict):
                continue
            if content_item.get("type") == "output_text":
                text = content_item.get("text")
                if isinstance(text, str) and text.strip():
                    return _parse_response_text(text)

    raise Phase7ContractError(
        error_category="invalid_value",
        safe_message="OpenAI answer generation response did not contain structured output text.",
    )


def _parse_response_text(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise Phase7ContractError(
            error_category="invalid_value",
            safe_message="OpenAI structured answer payload was not valid JSON.",
        ) from exc
    if not isinstance(parsed, dict):
        raise Phase7ContractError(
            error_category="invalid_value",
            safe_message="OpenAI structured answer payload must decode to an object.",
        )
    return parsed


def _build_response_metadata(
    *,
    response_json: Mapping[str, Any],
    response_headers: Mapping[str, str],
    configured_model: str,
    client_request_id: str,
    latency_ms: int,
) -> OpenAIAnswerResponseMetadata:
    usage = response_json.get("usage")
    usage_dict = usage if isinstance(usage, dict) else {}
    return OpenAIAnswerResponseMetadata(
        provider="openai",
        model=str(response_json.get("model") or configured_model),
        response_id=_as_optional_str(response_json.get("id")),
        provider_request_id=(
            response_headers.get("x-request-id")
            or response_headers.get("openai-request-id")
        ),
        client_request_id=client_request_id,
        input_tokens=_as_optional_int(usage_dict.get("input_tokens")),
        output_tokens=_as_optional_int(usage_dict.get("output_tokens")),
        total_tokens=_as_optional_int(usage_dict.get("total_tokens")),
        latency_ms=latency_ms,
    )


def _as_optional_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    return None


def _as_optional_str(value: object) -> str | None:
    if isinstance(value, str):
        trimmed = value.strip()
        return trimmed or None
    return None


__all__ = [
    "DEFAULT_OPENAI_ANSWER_MODEL",
    "OpenAIAnswerGenerator",
    "OpenAIAnswerGeneratorConfig",
    "OpenAIAnswerModelUnavailableError",
    "OpenAIAnswerProviderError",
    "OpenAIAnswerResponseMetadata",
]
