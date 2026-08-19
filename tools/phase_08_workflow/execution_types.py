from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import (
    EXECUTION_ATTEMPT_STATUS_CANCELLED,
    EXECUTION_ATTEMPT_STATUS_CODES,
    EXECUTION_ATTEMPT_STATUS_FAILED,
    EXECUTION_ATTEMPT_STATUS_STARTED,
    EXECUTION_ATTEMPT_STATUS_SUCCEEDED,
    EXECUTION_ATTEMPT_STATUS_TIMEOUT,
    FOLLOW_UP_STATUS_CODES,
    WORKFLOW_ACTION_STATUS_CODES,
    ExecutionAttempt,
    FollowUp,
    WorkflowAction,
)
from .orchestration_types import WorkflowOrchestrationResult
from .validation import (
    Phase8ContractError,
    ensure_bool,
    ensure_json_compatible,
    ensure_non_empty_text,
    ensure_non_negative_int,
    ensure_optional_non_empty_text,
    ensure_optional_positive_int,
    ensure_positive_int,
    ensure_tuple_of_non_empty_text,
    ensure_tuple_of_positive_ints,
)


PHASE_8_EXECUTION_CONTRACT_VERSION = 1
PHASE_8_EXECUTION_CONTRACT_LABEL = "phase8_execution_v1"

EXECUTION_FAILURE_CASE_NOT_FOUND = "case_not_found"
EXECUTION_FAILURE_ACTION_NOT_FOUND = "action_not_found"
EXECUTION_FAILURE_ATTEMPT_NOT_FOUND = "attempt_not_found"
EXECUTION_FAILURE_INVALID_EXECUTION_INPUT = "invalid_execution_input"
EXECUTION_FAILURE_ACTION_NOT_EXECUTION_READY = "action_not_execution_ready"
EXECUTION_FAILURE_ACTION_ALREADY_EXECUTING = "action_already_executing"
EXECUTION_FAILURE_ACTION_ALREADY_SUCCEEDED = "action_already_succeeded"
EXECUTION_FAILURE_ACTION_SUPERSEDED = "action_superseded"
EXECUTION_FAILURE_ACTION_CANCELLED = "action_cancelled"
EXECUTION_FAILURE_ACTION_STALE_REVISION = "action_stale_revision"
EXECUTION_FAILURE_ACTION_NOT_DUE = "action_not_due"
EXECUTION_FAILURE_APPROVAL_REQUIRED = "approval_required"
EXECUTION_FAILURE_ACTION_HUMAN_ONLY = "action_human_only"
EXECUTION_FAILURE_ACTION_BLOCKED = "action_blocked"
EXECUTION_FAILURE_ADAPTER_UNAVAILABLE = "adapter_unavailable"
EXECUTION_FAILURE_ADAPTER_CONFIGURATION_INVALID = "adapter_configuration_invalid"
EXECUTION_FAILURE_ADAPTER_AUTHENTICATION_FAILED = "adapter_authentication_failed"
EXECUTION_FAILURE_ADAPTER_FORBIDDEN = "adapter_forbidden"
EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID = "adapter_request_invalid"
EXECUTION_FAILURE_ADAPTER_RESOURCE_NOT_FOUND = "adapter_resource_not_found"
EXECUTION_FAILURE_ADAPTER_RATE_LIMITED = "adapter_rate_limited"
EXECUTION_FAILURE_ADAPTER_SERVER_ERROR = "adapter_server_error"
EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS = "adapter_outcome_ambiguous"
EXECUTION_FAILURE_ADAPTER_RESULT_MALFORMED = "adapter_result_malformed"
EXECUTION_FAILURE_ADAPTER_EXCEPTION = "adapter_exception"
EXECUTION_FAILURE_EXECUTION_ALREADY_STARTED = "execution_already_started"
EXECUTION_FAILURE_EXECUTION_START_FAILED = "execution_start_failed"
EXECUTION_FAILURE_EXECUTION_COMPLETE_FAILED = "execution_complete_failed"
EXECUTION_FAILURE_EXTERNAL_REFERENCE_CONFLICT = "external_reference_conflict"
EXECUTION_FAILURE_STALE_CASE_REVISION = "stale_case_revision"
EXECUTION_FAILURE_FOLLOW_UP_NOT_FOUND = "follow_up_not_found"
EXECUTION_FAILURE_FOLLOW_UP_STATE_TRANSITION_INVALID = "follow_up_state_transition_invalid"

EXECUTION_FAILURE_CODES = frozenset(
    {
        EXECUTION_FAILURE_CASE_NOT_FOUND,
        EXECUTION_FAILURE_ACTION_NOT_FOUND,
        EXECUTION_FAILURE_ATTEMPT_NOT_FOUND,
        EXECUTION_FAILURE_INVALID_EXECUTION_INPUT,
        EXECUTION_FAILURE_ACTION_NOT_EXECUTION_READY,
        EXECUTION_FAILURE_ACTION_ALREADY_EXECUTING,
        EXECUTION_FAILURE_ACTION_ALREADY_SUCCEEDED,
        EXECUTION_FAILURE_ACTION_SUPERSEDED,
        EXECUTION_FAILURE_ACTION_CANCELLED,
        EXECUTION_FAILURE_ACTION_STALE_REVISION,
        EXECUTION_FAILURE_ACTION_NOT_DUE,
        EXECUTION_FAILURE_APPROVAL_REQUIRED,
        EXECUTION_FAILURE_ACTION_HUMAN_ONLY,
        EXECUTION_FAILURE_ACTION_BLOCKED,
        EXECUTION_FAILURE_ADAPTER_UNAVAILABLE,
        EXECUTION_FAILURE_ADAPTER_CONFIGURATION_INVALID,
        EXECUTION_FAILURE_ADAPTER_AUTHENTICATION_FAILED,
        EXECUTION_FAILURE_ADAPTER_FORBIDDEN,
        EXECUTION_FAILURE_ADAPTER_REQUEST_INVALID,
        EXECUTION_FAILURE_ADAPTER_RESOURCE_NOT_FOUND,
        EXECUTION_FAILURE_ADAPTER_RATE_LIMITED,
        EXECUTION_FAILURE_ADAPTER_SERVER_ERROR,
        EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS,
        EXECUTION_FAILURE_ADAPTER_RESULT_MALFORMED,
        EXECUTION_FAILURE_ADAPTER_EXCEPTION,
        EXECUTION_FAILURE_EXECUTION_ALREADY_STARTED,
        EXECUTION_FAILURE_EXECUTION_START_FAILED,
        EXECUTION_FAILURE_EXECUTION_COMPLETE_FAILED,
        EXECUTION_FAILURE_EXTERNAL_REFERENCE_CONFLICT,
        EXECUTION_FAILURE_STALE_CASE_REVISION,
        EXECUTION_FAILURE_FOLLOW_UP_NOT_FOUND,
        EXECUTION_FAILURE_FOLLOW_UP_STATE_TRANSITION_INVALID,
    }
)

TERMINAL_EXECUTION_ATTEMPT_STATUSES = frozenset(
    {
        EXECUTION_ATTEMPT_STATUS_SUCCEEDED,
        EXECUTION_ATTEMPT_STATUS_FAILED,
        EXECUTION_ATTEMPT_STATUS_TIMEOUT,
        EXECUTION_ATTEMPT_STATUS_CANCELLED,
    }
)


@dataclass(frozen=True)
class ExecutionIdempotencyContext:
    workflow_action_id: int
    execution_attempt_id: int
    attempt_number: int
    semantic_idempotency_key: str

    def __post_init__(self) -> None:
        ensure_positive_int("workflow_action_id", self.workflow_action_id)
        ensure_positive_int("execution_attempt_id", self.execution_attempt_id)
        ensure_positive_int("attempt_number", self.attempt_number)
        ensure_non_empty_text("semantic_idempotency_key", self.semantic_idempotency_key)


@dataclass(frozen=True)
class ExecutionContext:
    rental_case_id: int
    workflow_action_id: int
    current_case_revision: int
    actor_reference: str
    case_reference_code: str | None = None
    actor_type: str | None = None
    started_at: str | None = None
    prior_attempts: tuple[ExecutionAttempt, ...] = ()

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_positive_int("workflow_action_id", self.workflow_action_id)
        ensure_non_negative_int("current_case_revision", self.current_case_revision)
        ensure_non_empty_text("actor_reference", self.actor_reference)
        ensure_optional_non_empty_text("case_reference_code", self.case_reference_code)
        ensure_optional_non_empty_text("actor_type", self.actor_type)
        ensure_optional_non_empty_text("started_at", self.started_at)
        if not isinstance(self.prior_attempts, tuple):
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="prior_attempts must be a tuple of ExecutionAttempt records.",
            )
        for index, attempt in enumerate(self.prior_attempts):
            if not isinstance(attempt, ExecutionAttempt):
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"prior_attempts[{index}] must be an ExecutionAttempt.",
                )


@dataclass(frozen=True)
class NormalizedExecutionResult:
    adapter_code: str
    attempt_status: str
    response_snapshot: Any
    retry_eligible: bool = False
    external_reference: str | None = None
    failure_code: str | None = None
    completed_at: str | None = None

    def __post_init__(self) -> None:
        ensure_non_empty_text("adapter_code", self.adapter_code)
        if self.attempt_status not in TERMINAL_EXECUTION_ATTEMPT_STATUSES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="attempt_status must be a terminal ExecutionAttempt status.",
            )
        ensure_json_compatible("response_snapshot", self.response_snapshot)
        ensure_bool("retry_eligible", self.retry_eligible)
        ensure_optional_non_empty_text("external_reference", self.external_reference)
        ensure_optional_non_empty_text("failure_code", self.failure_code)
        ensure_optional_non_empty_text("completed_at", self.completed_at)
        if self.attempt_status == EXECUTION_ATTEMPT_STATUS_SUCCEEDED:
            if self.failure_code is not None:
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message="successful normalized execution results cannot include failure_code.",
                )
            if self.retry_eligible:
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message="successful normalized execution results cannot be retry eligible.",
                )


@dataclass(frozen=True)
class WorkflowActionExecutionRequest:
    rental_case_id: int
    workflow_action_id: int
    actor_reference: str
    actor_type: str | None = None
    started_at: str | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_positive_int("workflow_action_id", self.workflow_action_id)
        ensure_non_empty_text("actor_reference", self.actor_reference)
        ensure_optional_non_empty_text("actor_type", self.actor_type)
        ensure_optional_non_empty_text("started_at", self.started_at)


@dataclass(frozen=True)
class WorkflowActionExecutionStartResult:
    rental_case_id: int
    workflow_action_id: int
    case_revision: int
    action_status_before: str
    action_status_after: str
    audit_event_ids: tuple[int, ...] = ()
    execution_attempt_id: int | None = None
    attempt_number: int | None = None
    workflow_action: WorkflowAction | None = None
    execution_attempt: ExecutionAttempt | None = None
    failure_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_positive_int("workflow_action_id", self.workflow_action_id)
        ensure_non_negative_int("case_revision", self.case_revision)
        if self.action_status_before not in WORKFLOW_ACTION_STATUS_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="action_status_before must be a supported WorkflowAction status.",
            )
        if self.action_status_after not in WORKFLOW_ACTION_STATUS_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="action_status_after must be a supported WorkflowAction status.",
            )
        ensure_tuple_of_positive_ints("audit_event_ids", self.audit_event_ids)
        ensure_optional_positive_int("execution_attempt_id", self.execution_attempt_id)
        ensure_optional_positive_int("attempt_number", self.attempt_number)
        ensure_tuple_of_non_empty_text("failure_codes", self.failure_codes)


@dataclass(frozen=True)
class WorkflowActionExecutionCompletionRequest:
    rental_case_id: int
    workflow_action_id: int
    execution_attempt_id: int
    actor_reference: str
    result: NormalizedExecutionResult
    actor_type: str | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_positive_int("workflow_action_id", self.workflow_action_id)
        ensure_positive_int("execution_attempt_id", self.execution_attempt_id)
        ensure_non_empty_text("actor_reference", self.actor_reference)
        ensure_optional_non_empty_text("actor_type", self.actor_type)


@dataclass(frozen=True)
class WorkflowActionExecutionResult:
    rental_case_id: int
    workflow_action_id: int
    case_revision: int
    action_status_before: str
    action_status_after: str
    audit_event_ids: tuple[int, ...] = ()
    execution_attempt_id: int | None = None
    attempt_status: str | None = None
    retry_eligible: bool = False
    external_reference: str | None = None
    updated_follow_up_id: int | None = None
    follow_up_status_before: str | None = None
    follow_up_status_after: str | None = None
    follow_up_attempt_count_after: int | None = None
    failure_codes: tuple[str, ...] = ()
    already_succeeded_idempotently: bool = False
    reconciliation_result: WorkflowOrchestrationResult | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_positive_int("workflow_action_id", self.workflow_action_id)
        ensure_non_negative_int("case_revision", self.case_revision)
        if self.action_status_before not in WORKFLOW_ACTION_STATUS_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="action_status_before must be a supported WorkflowAction status.",
            )
        if self.action_status_after not in WORKFLOW_ACTION_STATUS_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="action_status_after must be a supported WorkflowAction status.",
            )
        ensure_tuple_of_positive_ints("audit_event_ids", self.audit_event_ids)
        ensure_optional_positive_int("execution_attempt_id", self.execution_attempt_id)
        if self.attempt_status is not None and self.attempt_status not in EXECUTION_ATTEMPT_STATUS_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="attempt_status must be a supported ExecutionAttempt status.",
            )
        ensure_bool("retry_eligible", self.retry_eligible)
        ensure_optional_non_empty_text("external_reference", self.external_reference)
        ensure_optional_positive_int("updated_follow_up_id", self.updated_follow_up_id)
        if self.follow_up_status_before is not None and self.follow_up_status_before not in FOLLOW_UP_STATUS_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="follow_up_status_before must be a supported FollowUp status.",
            )
        if self.follow_up_status_after is not None and self.follow_up_status_after not in FOLLOW_UP_STATUS_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="follow_up_status_after must be a supported FollowUp status.",
            )
        ensure_optional_positive_int("follow_up_attempt_count_after", self.follow_up_attempt_count_after)
        ensure_tuple_of_non_empty_text("failure_codes", self.failure_codes)
        ensure_bool("already_succeeded_idempotently", self.already_succeeded_idempotently)


@dataclass(frozen=True)
class FollowUpStatusUpdateRequest:
    rental_case_id: int
    follow_up_id: int
    actor_reference: str
    target_status: str
    actor_type: str | None = None
    expected_current_status: str | None = None
    attempt_count_delta: int = 0
    occurred_at: str | None = None
    completed_at: str | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_positive_int("follow_up_id", self.follow_up_id)
        ensure_non_empty_text("actor_reference", self.actor_reference)
        ensure_optional_non_empty_text("actor_type", self.actor_type)
        if self.target_status not in FOLLOW_UP_STATUS_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="target_status must be a supported FollowUp status.",
            )
        if self.expected_current_status is not None and self.expected_current_status not in FOLLOW_UP_STATUS_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="expected_current_status must be a supported FollowUp status.",
            )
        ensure_non_negative_int("attempt_count_delta", self.attempt_count_delta)
        ensure_optional_non_empty_text("occurred_at", self.occurred_at)
        ensure_optional_non_empty_text("completed_at", self.completed_at)


@dataclass(frozen=True)
class FollowUpStatusUpdateResult:
    rental_case_id: int
    follow_up_id: int
    status_before: str
    status_after: str
    attempt_count_before: int
    attempt_count_after: int
    audit_event_ids: tuple[int, ...] = ()
    follow_up: FollowUp | None = None
    failure_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_positive_int("follow_up_id", self.follow_up_id)
        if self.status_before not in FOLLOW_UP_STATUS_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="status_before must be a supported FollowUp status.",
            )
        if self.status_after not in FOLLOW_UP_STATUS_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="status_after must be a supported FollowUp status.",
            )
        ensure_non_negative_int("attempt_count_before", self.attempt_count_before)
        ensure_non_negative_int("attempt_count_after", self.attempt_count_after)
        ensure_tuple_of_positive_ints("audit_event_ids", self.audit_event_ids)
        ensure_tuple_of_non_empty_text("failure_codes", self.failure_codes)


@dataclass(frozen=True)
class FollowUpEvaluationRequest:
    actor_reference: str
    rental_case_id: int | None = None
    actor_type: str | None = None
    now: str | None = None

    def __post_init__(self) -> None:
        ensure_non_empty_text("actor_reference", self.actor_reference)
        ensure_optional_positive_int("rental_case_id", self.rental_case_id)
        ensure_optional_non_empty_text("actor_type", self.actor_type)
        ensure_optional_non_empty_text("now", self.now)


@dataclass(frozen=True)
class FollowUpEvaluationResult:
    evaluated_follow_up_ids: tuple[int, ...] = ()
    updated_follow_up_ids: tuple[int, ...] = ()
    due_follow_up_ids: tuple[int, ...] = ()
    overdue_follow_up_ids: tuple[int, ...] = ()
    escalated_follow_up_ids: tuple[int, ...] = ()
    completed_follow_up_ids: tuple[int, ...] = ()
    audit_event_ids: tuple[int, ...] = ()
    reconciled_case_ids: tuple[int, ...] = ()
    created_action_ids: tuple[int, ...] = ()
    created_approval_ids: tuple[int, ...] = ()
    created_blocker_ids: tuple[int, ...] = ()
    failure_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "evaluated_follow_up_ids",
            "updated_follow_up_ids",
            "due_follow_up_ids",
            "overdue_follow_up_ids",
            "escalated_follow_up_ids",
            "completed_follow_up_ids",
            "audit_event_ids",
            "reconciled_case_ids",
            "created_action_ids",
            "created_approval_ids",
            "created_blocker_ids",
        ):
            ensure_tuple_of_positive_ints(field_name, getattr(self, field_name))
        ensure_tuple_of_non_empty_text("failure_codes", self.failure_codes)
