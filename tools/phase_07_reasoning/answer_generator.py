from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from .answer_layer import validate_answer_result
from .contracts import (
    ANSWER_MODE_AUTHORITATIVE_CURRENT,
    ANSWER_MODE_BLOCKED,
    ANSWER_MODE_CONFIRMATION_REQUIRED,
    ANSWER_MODE_CURRENT_WITH_HISTORICAL_CONTEXT,
    ANSWER_MODE_HISTORICAL_DESCRIPTIVE,
    ANSWER_MODE_INSUFFICIENT_CURRENT_AUTHORITY,
    ANSWER_RESULT_STATUS_BLOCKED,
    ANSWER_RESULT_STATUS_CODES,
    ANSWER_RESULT_STATUS_COMPLETED,
    ANSWER_RESULT_STATUS_FAILED,
    GENERATION_DECISION_ALLOWED_WITH_RESTRICTIONS,
    GENERATION_DECISION_BLOCKED,
    PHASE_7_ANSWER_CONTRACT_VERSION,
    GeneratorSafeGroundingReference,
    AnswerClaimFrame,
    AnswerGenerationInput,
    AnswerGroundingUse,
    AnswerResult,
    AnswerValidationResult,
    ContractBase,
    Phase7ContractError,
)
from .validation import (
    ensure_bool,
    ensure_json_compatible,
    ensure_non_empty_text,
    ensure_optional_non_empty_text,
    ensure_positive_int,
    ensure_unique_strings,
)


BOUNDED_GENERATOR_REQUEST_CONTRACT_VERSION = 1

RUNTIME_FAILURE_INVALID_GENERATION_INPUT = "invalid_generation_input"
RUNTIME_FAILURE_GENERATION_BLOCKED = "generation_blocked"
RUNTIME_FAILURE_GENERATOR_FAILURE = "generator_failure"
RUNTIME_FAILURE_GENERATOR_TIMEOUT = "generator_timeout"
RUNTIME_FAILURE_MALFORMED_GENERATOR_RESPONSE = "malformed_generator_response"
RUNTIME_FAILURE_ANSWER_VALIDATION_FAILED = "answer_validation_failed"

FORBIDDEN_RESPONSE_FIELDS = (
    "chain_of_thought",
    "reasoning_trace",
    "internal_analysis",
    "hidden_reasoning",
)

RESPONSE_ALLOWED_KEYS = frozenset(
    {
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
    }
)

RESPONSE_REQUIRED_KEYS = frozenset(
    {
        "status",
        "answer_mode",
        "authority_outcome",
        "generation_decision",
        "confirmation_required",
        "insufficient_current_authority",
        "degraded_context_present",
        "materially_affects_answer_completeness",
        "grounding_uses",
        "warning_codes",
    }
)


class BoundedAnswerGenerator(Protocol):
    def generate(self, request: "BoundedAnswerGeneratorRequest") -> object:
        ...


@dataclass(frozen=True)
class BoundedAnswerGeneratorRequest(ContractBase):
    query_text: str
    answer_mode: str
    authority_outcome: str
    generation_decision: str
    confirmation_required: bool
    insufficient_current_authority: bool
    degraded_context_present: bool
    materially_affects_answer_completeness: bool
    immutable_rules: tuple[str, ...] = field(default_factory=tuple)
    authority_hierarchy: tuple[str, ...] = field(default_factory=tuple)
    prohibited_behaviors: tuple[str, ...] = field(default_factory=tuple)
    answer_mode_instruction: str = ""
    restriction_instructions: tuple[str, ...] = field(default_factory=tuple)
    degraded_state_instruction: str | None = None
    claim_frames: tuple[AnswerClaimFrame, ...] = field(default_factory=tuple)
    safe_grounding: tuple[GeneratorSafeGroundingReference, ...] = field(default_factory=tuple)
    required_warning_codes: tuple[str, ...] = field(default_factory=tuple)
    output_schema_fields: tuple[str, ...] = field(default_factory=tuple)
    forbidden_response_fields: tuple[str, ...] = FORBIDDEN_RESPONSE_FIELDS
    answer_contract_version: int = PHASE_7_ANSWER_CONTRACT_VERSION
    request_contract_version: int = BOUNDED_GENERATOR_REQUEST_CONTRACT_VERSION

    def __post_init__(self) -> None:
        ensure_non_empty_text("query_text", self.query_text)
        ensure_non_empty_text("answer_mode_instruction", self.answer_mode_instruction)
        ensure_unique_strings("immutable_rules", self.immutable_rules)
        ensure_unique_strings("authority_hierarchy", self.authority_hierarchy)
        ensure_unique_strings("prohibited_behaviors", self.prohibited_behaviors)
        ensure_unique_strings("restriction_instructions", self.restriction_instructions)
        ensure_optional_non_empty_text(
            "degraded_state_instruction",
            self.degraded_state_instruction,
        )
        ensure_unique_strings(
            "bounded request claim_ids",
            tuple(frame.claim_id for frame in self.claim_frames),
        )
        ensure_unique_strings(
            "bounded request grounding reference_ids",
            tuple(reference.reference_id for reference in self.safe_grounding),
        )
        ensure_unique_strings("required_warning_codes", self.required_warning_codes)
        ensure_unique_strings("output_schema_fields", self.output_schema_fields)
        ensure_unique_strings(
            "forbidden_response_fields",
            self.forbidden_response_fields,
        )
        ensure_bool("confirmation_required", self.confirmation_required)
        ensure_bool(
            "insufficient_current_authority",
            self.insufficient_current_authority,
        )
        ensure_bool("degraded_context_present", self.degraded_context_present)
        ensure_bool(
            "materially_affects_answer_completeness",
            self.materially_affects_answer_completeness,
        )
        ensure_positive_int("answer_contract_version", self.answer_contract_version)
        ensure_positive_int("request_contract_version", self.request_contract_version)


@dataclass(frozen=True)
class BoundedAnswerRuntimeResult(ContractBase):
    runtime_status: str
    generator_called: bool
    failure_code: str | None = None
    failure_details: tuple[str, ...] = field(default_factory=tuple)
    answer_result: AnswerResult | None = None
    answer_validation_result: AnswerValidationResult | None = None
    generator_request: BoundedAnswerGeneratorRequest | None = None
    raw_generator_response: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.runtime_status not in ANSWER_RESULT_STATUS_CODES:
            raise Phase7ContractError(
                error_category="invalid_value",
                safe_message="runtime_status must be a valid answer-result status code.",
            )
        ensure_bool("generator_called", self.generator_called)
        ensure_optional_non_empty_text("failure_code", self.failure_code)
        ensure_unique_strings("failure_details", self.failure_details)
        if self.raw_generator_response is not None:
            ensure_json_compatible("raw_generator_response", self.raw_generator_response)
        if self.runtime_status == ANSWER_RESULT_STATUS_FAILED and self.failure_code is None:
            raise Phase7ContractError(
                error_category="missing_required_field",
                safe_message="failed runtime results require a failure_code.",
            )
        if self.answer_result is not None and self.answer_result.status != self.runtime_status:
            raise Phase7ContractError(
                error_category="invalid_value",
                safe_message=(
                    "runtime_status must match answer_result.status when an answer_result "
                    "is present."
                ),
            )
        if self.answer_result is not None and self.answer_validation_result is None:
            raise Phase7ContractError(
                error_category="missing_required_field",
                safe_message=(
                    "runtime results carrying an answer_result must also include "
                    "answer_validation_result."
                ),
            )
        if (
            self.answer_validation_result is not None
            and not self.answer_validation_result.is_valid
        ):
            raise Phase7ContractError(
                error_category="invalid_value",
                safe_message=(
                    "runtime results must not expose an invalid answer_result across "
                    "the delivery boundary."
                ),
            )


def build_bounded_generator_request(
    answer_generation_input: AnswerGenerationInput,
) -> BoundedAnswerGeneratorRequest:
    validated_input = _validate_answer_generation_input(answer_generation_input)

    restriction_instructions = list(
        validated_input.generator_policy.confidentiality_restrictions
    )
    restriction_instructions.extend(
        validated_input.generator_policy.personal_information_restrictions
    )
    if validated_input.generation_decision == GENERATION_DECISION_ALLOWED_WITH_RESTRICTIONS:
        restriction_instructions.append("respect_allowed_with_restrictions_mode")

    degraded_state_instruction = None
    if validated_input.degraded_retrieval_state.any_degradation:
        degraded_state_instruction = (
            "Surface degraded retrieval state explicitly. Do not imply full completeness "
            "when degraded warnings are present."
        )

    return BoundedAnswerGeneratorRequest(
        query_text=validated_input.query_text,
        answer_mode=validated_input.answer_mode,
        authority_outcome=validated_input.authority_outcome,
        generation_decision=validated_input.generation_decision,
        confirmation_required=validated_input.confirmation_required,
        insufficient_current_authority=validated_input.insufficient_current_authority,
        degraded_context_present=validated_input.degraded_retrieval_state.any_degradation,
        materially_affects_answer_completeness=(
            validated_input.degraded_retrieval_state.materially_affects_answer_completeness
        ),
        immutable_rules=(
            "Use only the supplied claim frames and safe grounding.",
            "Do not retrieve, search, query tools, or use external knowledge.",
            "Do not invent deterministic values or convert history into current policy.",
            "Do not emit chain_of_thought, hidden reasoning, or internal analysis.",
        ),
        authority_hierarchy=(
            "Phase 4 current deterministic truth outranks every other layer.",
            "Phase 5 current governed guidance may explain but not override Phase 4.",
            "Phase 6 historical precedent is historical only and never current policy by itself.",
        ),
        prohibited_behaviors=tuple(validated_input.generator_policy.forbidden_actions),
        answer_mode_instruction=_answer_mode_instruction(validated_input),
        restriction_instructions=tuple(dict.fromkeys(restriction_instructions)),
        degraded_state_instruction=degraded_state_instruction,
        claim_frames=validated_input.claim_frames,
        safe_grounding=validated_input.safe_grounding,
        required_warning_codes=validated_input.required_warning_codes,
        output_schema_fields=(
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
        ),
        answer_contract_version=validated_input.answer_contract_version,
    )


def generate_bounded_answer(
    answer_generation_input: AnswerGenerationInput,
    generator: BoundedAnswerGenerator,
) -> BoundedAnswerRuntimeResult:
    try:
        validated_input = _validate_answer_generation_input(answer_generation_input)
    except Phase7ContractError as exc:
        return BoundedAnswerRuntimeResult(
            runtime_status=ANSWER_RESULT_STATUS_FAILED,
            generator_called=False,
            failure_code=RUNTIME_FAILURE_INVALID_GENERATION_INPUT,
            failure_details=(exc.safe_message,),
            answer_result=None,
            answer_validation_result=None,
            generator_request=None,
            raw_generator_response=None,
        )

    if validated_input.generation_decision == GENERATION_DECISION_BLOCKED:
        blocked_result = _build_failure_answer_result(
            validated_input,
            status=ANSWER_RESULT_STATUS_BLOCKED,
            failure_code=RUNTIME_FAILURE_GENERATION_BLOCKED,
        )
        blocked_validation = validate_answer_result(validated_input, blocked_result)
        return BoundedAnswerRuntimeResult(
            runtime_status=ANSWER_RESULT_STATUS_BLOCKED,
            generator_called=False,
            failure_code=RUNTIME_FAILURE_GENERATION_BLOCKED,
            failure_details=(),
            answer_result=blocked_result,
            answer_validation_result=_require_valid_validation(blocked_validation),
            generator_request=None,
            raw_generator_response=None,
        )

    request = build_bounded_generator_request(validated_input)

    try:
        raw_response = generator.generate(request)
    except TimeoutError as exc:
        return _failure_runtime_result(
            validated_input=validated_input,
            request=request,
            failure_code=RUNTIME_FAILURE_GENERATOR_TIMEOUT,
            failure_details=_safe_exception_details(exc),
        )
    except Phase7ContractError as exc:
        return _failure_runtime_result(
            validated_input=validated_input,
            request=request,
            failure_code=RUNTIME_FAILURE_MALFORMED_GENERATOR_RESPONSE,
            failure_details=(exc.safe_message,),
        )
    except Exception as exc:
        return _failure_runtime_result(
            validated_input=validated_input,
            request=request,
            failure_code=RUNTIME_FAILURE_GENERATOR_FAILURE,
            failure_details=_safe_exception_details(exc),
        )

    raw_response_payload = _normalize_raw_response(raw_response)
    try:
        parsed_result = _parse_generator_response(raw_response)
    except Phase7ContractError as exc:
        return _failure_runtime_result(
            validated_input=validated_input,
            request=request,
            failure_code=RUNTIME_FAILURE_MALFORMED_GENERATOR_RESPONSE,
            failure_details=(exc.safe_message,),
            raw_response_payload=raw_response_payload,
        )

    validation = validate_answer_result(validated_input, parsed_result)
    if not validation.is_valid:
        return _failure_runtime_result(
            validated_input=validated_input,
            request=request,
            failure_code=RUNTIME_FAILURE_ANSWER_VALIDATION_FAILED,
            failure_details=validation.failure_codes,
            raw_response_payload=raw_response_payload,
        )

    return BoundedAnswerRuntimeResult(
        runtime_status=parsed_result.status,
        generator_called=True,
        failure_code=None,
        failure_details=(),
        answer_result=parsed_result,
        answer_validation_result=validation,
        generator_request=request,
        raw_generator_response=raw_response_payload,
    )


def _answer_mode_instruction(answer_generation_input: AnswerGenerationInput) -> str:
    if answer_generation_input.answer_mode == ANSWER_MODE_AUTHORITATIVE_CURRENT:
        return (
            "Provide a bounded current-authority answer using only current deterministic "
            "truth and current governed guidance supplied in the claim frames."
        )
    if answer_generation_input.answer_mode == ANSWER_MODE_CURRENT_WITH_HISTORICAL_CONTEXT:
        return (
            "Keep current authority primary. Historical claim frames may appear only as "
            "explicit historical context."
        )
    if answer_generation_input.answer_mode == ANSWER_MODE_HISTORICAL_DESCRIPTIVE:
        return (
            "Answer descriptively about historical precedent only. Do not imply current "
            "policy or current service availability."
        )
    if answer_generation_input.answer_mode == ANSWER_MODE_CONFIRMATION_REQUIRED:
        return (
            "Answer conservatively and preserve the explicit requirement for confirmation "
            "or manual verification."
        )
    if answer_generation_input.answer_mode == ANSWER_MODE_INSUFFICIENT_CURRENT_AUTHORITY:
        return (
            "State that current authority is insufficient. Historical claim frames may be "
            "mentioned only as historical context, never as current policy."
        )
    if answer_generation_input.answer_mode == ANSWER_MODE_BLOCKED:
        return "Do not synthesize substantive answer content."
    raise Phase7ContractError(
        error_category="invalid_value",
        safe_message="unsupported answer_mode for bounded generator request assembly.",
    )


def _parse_generator_response(raw_response: object) -> AnswerResult:
    if isinstance(raw_response, AnswerResult):
        return raw_response
    if not isinstance(raw_response, dict):
        raise Phase7ContractError(
            error_category="invalid_value",
            safe_message="generator response must be a dict or AnswerResult.",
        )

    forbidden_fields = sorted(
        key for key in raw_response if key in FORBIDDEN_RESPONSE_FIELDS
    )
    if forbidden_fields:
        raise Phase7ContractError(
            error_category="invalid_value",
            safe_message=(
                "generator response included forbidden internal-reasoning fields: "
                + ", ".join(forbidden_fields)
            ),
        )

    unexpected_keys = sorted(set(raw_response) - RESPONSE_ALLOWED_KEYS)
    if unexpected_keys:
        raise Phase7ContractError(
            error_category="invalid_value",
            safe_message=(
                "generator response included unexpected fields: "
                + ", ".join(unexpected_keys)
            ),
        )

    missing_required_keys = sorted(RESPONSE_REQUIRED_KEYS - set(raw_response))
    if missing_required_keys:
        raise Phase7ContractError(
            error_category="missing_required_field",
            safe_message=(
                "generator response omitted required fields: "
                + ", ".join(missing_required_keys)
            ),
        )

    grounding_uses_payload = raw_response.get("grounding_uses", ())
    if not isinstance(grounding_uses_payload, (list, tuple)):
        raise Phase7ContractError(
            error_category="invalid_value",
            safe_message="grounding_uses must be a list or tuple.",
        )
    grounding_uses = tuple(
        _parse_grounding_use(item) for item in grounding_uses_payload
    )

    warning_codes_payload = raw_response.get("warning_codes", ())
    if not isinstance(warning_codes_payload, (list, tuple)):
        raise Phase7ContractError(
            error_category="invalid_value",
            safe_message="warning_codes must be a list or tuple.",
        )

    return AnswerResult(
        status=raw_response["status"],
        answer_mode=raw_response["answer_mode"],
        authority_outcome=raw_response["authority_outcome"],
        generation_decision=raw_response["generation_decision"],
        confirmation_required=raw_response["confirmation_required"],
        insufficient_current_authority=raw_response["insufficient_current_authority"],
        degraded_context_present=raw_response["degraded_context_present"],
        materially_affects_answer_completeness=raw_response[
            "materially_affects_answer_completeness"
        ],
        answer_text=raw_response.get("answer_text"),
        grounding_uses=grounding_uses,
        warning_codes=tuple(warning_codes_payload),
        failure_code=raw_response.get("failure_code"),
        answer_contract_version=raw_response.get("answer_contract_version", 1),
    )


def _parse_grounding_use(payload: object) -> AnswerGroundingUse:
    if isinstance(payload, AnswerGroundingUse):
        return payload
    if not isinstance(payload, dict):
        raise Phase7ContractError(
            error_category="invalid_value",
            safe_message="grounding use entries must be dicts or AnswerGroundingUse.",
        )
    return AnswerGroundingUse(
        claim_id=_required_payload_value(payload, "claim_id"),
        reference_id=_required_payload_value(payload, "reference_id"),
        source_layer_role=_required_payload_value(payload, "source_layer_role"),
    )


def _failure_runtime_result(
    *,
    validated_input: AnswerGenerationInput,
    request: BoundedAnswerGeneratorRequest,
    failure_code: str,
    failure_details: tuple[str, ...] = (),
    raw_response_payload: dict[str, Any] | None = None,
) -> BoundedAnswerRuntimeResult:
    safe_failure_result = _build_failure_answer_result(
        validated_input,
        status=ANSWER_RESULT_STATUS_FAILED,
        failure_code=failure_code,
    )
    safe_failure_validation = _require_valid_validation(
        validate_answer_result(validated_input, safe_failure_result)
    )
    return BoundedAnswerRuntimeResult(
        runtime_status=ANSWER_RESULT_STATUS_FAILED,
        generator_called=True,
        failure_code=failure_code,
        failure_details=failure_details,
        answer_result=safe_failure_result,
        answer_validation_result=safe_failure_validation,
        generator_request=request,
        raw_generator_response=raw_response_payload,
    )


def _build_failure_answer_result(
    answer_generation_input: AnswerGenerationInput,
    *,
    status: str,
    failure_code: str,
) -> AnswerResult:
    return AnswerResult(
        status=status,
        answer_mode=answer_generation_input.answer_mode,
        authority_outcome=answer_generation_input.authority_outcome,
        generation_decision=answer_generation_input.generation_decision,
        confirmation_required=answer_generation_input.confirmation_required,
        insufficient_current_authority=(
            answer_generation_input.insufficient_current_authority
        ),
        degraded_context_present=(
            answer_generation_input.degraded_retrieval_state.any_degradation
        ),
        materially_affects_answer_completeness=(
            answer_generation_input.degraded_retrieval_state.materially_affects_answer_completeness
        ),
        answer_text=None,
        grounding_uses=(),
        warning_codes=answer_generation_input.required_warning_codes,
        failure_code=failure_code,
        answer_contract_version=answer_generation_input.answer_contract_version,
    )


def _require_valid_validation(
    answer_validation_result: AnswerValidationResult,
) -> AnswerValidationResult:
    if not answer_validation_result.is_valid:
        raise Phase7ContractError(
            error_category="invalid_value",
            safe_message="safe failure answer results must validate successfully.",
        )
    return answer_validation_result


def _validate_answer_generation_input(
    answer_generation_input: AnswerGenerationInput,
) -> AnswerGenerationInput:
    if not isinstance(answer_generation_input, AnswerGenerationInput):
        raise Phase7ContractError(
            error_category="invalid_value",
            safe_message="answer generation runtime requires an AnswerGenerationInput instance.",
        )
    return answer_generation_input


def _safe_exception_details(exc: Exception) -> tuple[str, ...]:
    safe_message = getattr(exc, "safe_message", None)
    if isinstance(safe_message, str):
        trimmed = safe_message.strip()
        if trimmed:
            return (trimmed,)
    if isinstance(exc, TimeoutError):
        trimmed = str(exc).strip()
        if trimmed:
            return (trimmed,)
    return ()


def _normalize_raw_response(raw_response: object) -> dict[str, Any] | None:
    if raw_response is None:
        return None
    if isinstance(raw_response, AnswerResult):
        return raw_response.to_dict()
    if isinstance(raw_response, dict):
        ensure_json_compatible("raw_generator_response", raw_response)
        return raw_response
    return {"raw_response_type": type(raw_response).__name__}


def _required_payload_value(payload: dict[str, Any], key: str) -> Any:
    if key not in payload:
        raise Phase7ContractError(
            error_category="missing_required_field",
            safe_message=f"grounding use entry omitted required field: {key}.",
        )
    return payload[key]


__all__ = [
    "BOUNDED_GENERATOR_REQUEST_CONTRACT_VERSION",
    "BoundedAnswerGenerator",
    "BoundedAnswerGeneratorRequest",
    "BoundedAnswerRuntimeResult",
    "RUNTIME_FAILURE_ANSWER_VALIDATION_FAILED",
    "RUNTIME_FAILURE_GENERATION_BLOCKED",
    "RUNTIME_FAILURE_GENERATOR_FAILURE",
    "RUNTIME_FAILURE_GENERATOR_TIMEOUT",
    "RUNTIME_FAILURE_INVALID_GENERATION_INPUT",
    "RUNTIME_FAILURE_MALFORMED_GENERATOR_RESPONSE",
    "build_bounded_generator_request",
    "generate_bounded_answer",
]
