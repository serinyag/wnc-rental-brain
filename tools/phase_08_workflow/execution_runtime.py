from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Callable, Protocol

from .contracts import (
    APPROVAL_POSTURE_BLOCKED,
    APPROVAL_POSTURE_HUMAN_ONLY,
    EXECUTION_ATTEMPT_STATUS_FAILED,
    EXECUTION_ATTEMPT_STATUS_SUCCEEDED,
    FOLLOW_UP_STATUS_CANCELLED,
    FOLLOW_UP_STATUS_COMPLETED,
    FOLLOW_UP_STATUS_DUE,
    FOLLOW_UP_STATUS_ESCALATED,
    FOLLOW_UP_STATUS_OVERDUE,
    FOLLOW_UP_STATUS_SCHEDULED,
    WORKFLOW_ACTION_STATUS_CANCELLED,
    WORKFLOW_ACTION_STATUS_EXECUTING,
    WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
    WORKFLOW_ACTION_STATUS_SUCCEEDED,
    WORKFLOW_ACTION_STATUS_SUPERSEDED,
    FollowUp,
    WorkflowAction,
)
from .execution_types import (
    EXECUTION_FAILURE_ACTION_ALREADY_SUCCEEDED,
    EXECUTION_FAILURE_ACTION_BLOCKED,
    EXECUTION_FAILURE_ACTION_CANCELLED,
    EXECUTION_FAILURE_ACTION_HUMAN_ONLY,
    EXECUTION_FAILURE_ACTION_NOT_DUE,
    EXECUTION_FAILURE_ACTION_NOT_EXECUTION_READY,
    EXECUTION_FAILURE_ACTION_STALE_REVISION,
    EXECUTION_FAILURE_ACTION_SUPERSEDED,
    EXECUTION_FAILURE_ACTION_ALREADY_EXECUTING,
    EXECUTION_FAILURE_ADAPTER_EXCEPTION,
    EXECUTION_FAILURE_ADAPTER_RESULT_MALFORMED,
    EXECUTION_FAILURE_ADAPTER_UNAVAILABLE,
    EXECUTION_FAILURE_CASE_NOT_FOUND,
    EXECUTION_FAILURE_INVALID_EXECUTION_INPUT,
    ExecutionContext,
    ExecutionIdempotencyContext,
    FollowUpEvaluationRequest,
    FollowUpEvaluationResult,
    FollowUpStatusUpdateRequest,
    NormalizedExecutionResult,
    WorkflowActionExecutionCompletionRequest,
    WorkflowActionExecutionRequest,
    WorkflowActionExecutionResult,
)
from .orchestration_repository import (
    WorkflowOrchestrationCaseSnapshot,
    WorkflowOrchestrationRepositoryProtocol,
)
from .orchestration_runtime import reconcile_workflow_orchestration, _validate_action_payload


class ExecutionAdapterProtocol(Protocol):
    def availability_failure_code(self, *, action: WorkflowAction) -> str | None: ...

    def execute(
        self,
        *,
        action: WorkflowAction,
        execution_context: ExecutionContext,
        idempotency: ExecutionIdempotencyContext,
    ) -> Any: ...


@dataclass
class ExecutionAdapterRegistry:
    adapters: dict[str, ExecutionAdapterProtocol] = field(default_factory=dict)

    def register(self, adapter_code: str, adapter: ExecutionAdapterProtocol) -> None:
        self.adapters[adapter_code] = adapter

    def resolve(self, adapter_code: str) -> ExecutionAdapterProtocol | None:
        return self.adapters.get(adapter_code)


@dataclass
class DeterministicFakeExecutionAdapter:
    result_factory: Callable[[WorkflowAction, ExecutionContext, ExecutionIdempotencyContext], Any]
    invocations: list[dict[str, Any]] = field(default_factory=list)

    def availability_failure_code(self, *, action: WorkflowAction) -> str | None:
        del action
        return None

    def execute(
        self,
        *,
        action: WorkflowAction,
        execution_context: ExecutionContext,
        idempotency: ExecutionIdempotencyContext,
    ) -> Any:
        self.invocations.append(
            {
                "workflow_action_id": action.workflow_action_id,
                "rental_case_id": action.rental_case_id,
                "adapter_code": action.target_adapter_code,
                "execution_attempt_id": idempotency.execution_attempt_id,
                "attempt_number": idempotency.attempt_number,
                "semantic_idempotency_key": idempotency.semantic_idempotency_key,
            }
        )
        return self.result_factory(action, execution_context, idempotency)


def _parse_timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_default_fake_execution_registry(
    *,
    now: Callable[[], str] = _utc_now,
) -> ExecutionAdapterRegistry:
    registry = ExecutionAdapterRegistry()
    for adapter_code in ("internal", "email", "task_surface", "calendar", "payment", "document"):
        registry.register(adapter_code, fake_success_adapter(adapter_code, now=now))
    return registry


def fake_success_adapter(
    adapter_code: str,
    *,
    now: Callable[[], str] = _utc_now,
) -> DeterministicFakeExecutionAdapter:
    return DeterministicFakeExecutionAdapter(
        result_factory=lambda action, _context, idempotency: NormalizedExecutionResult(
            adapter_code=adapter_code,
            attempt_status=EXECUTION_ATTEMPT_STATUS_SUCCEEDED,
            response_snapshot={
                "provider_mode": "deterministic_fake",
                "workflow_action_id": action.workflow_action_id,
                "attempt_number": idempotency.attempt_number,
            },
            external_reference=f"fake:{adapter_code}:{action.workflow_action_id}:{idempotency.attempt_number}",
            completed_at=now(),
        )
    )


def fake_retryable_failure_adapter(
    adapter_code: str,
    *,
    failure_code: str = "fake_retryable_failure",
    now: Callable[[], str] = _utc_now,
) -> DeterministicFakeExecutionAdapter:
    return DeterministicFakeExecutionAdapter(
        result_factory=lambda action, _context, idempotency: NormalizedExecutionResult(
            adapter_code=adapter_code,
            attempt_status=EXECUTION_ATTEMPT_STATUS_FAILED,
            response_snapshot={
                "provider_mode": "deterministic_fake",
                "workflow_action_id": action.workflow_action_id,
                "attempt_number": idempotency.attempt_number,
                "result": "retryable_failure",
            },
            retry_eligible=True,
            failure_code=failure_code,
            completed_at=now(),
        )
    )


def fake_permanent_failure_adapter(
    adapter_code: str,
    *,
    failure_code: str = "fake_permanent_failure",
    now: Callable[[], str] = _utc_now,
) -> DeterministicFakeExecutionAdapter:
    return DeterministicFakeExecutionAdapter(
        result_factory=lambda action, _context, idempotency: NormalizedExecutionResult(
            adapter_code=adapter_code,
            attempt_status=EXECUTION_ATTEMPT_STATUS_FAILED,
            response_snapshot={
                "provider_mode": "deterministic_fake",
                "workflow_action_id": action.workflow_action_id,
                "attempt_number": idempotency.attempt_number,
                "result": "permanent_failure",
            },
            retry_eligible=False,
            failure_code=failure_code,
            completed_at=now(),
        )
    )


def fake_timeout_adapter(
    adapter_code: str,
    *,
    failure_code: str = "fake_timeout",
    now: Callable[[], str] = _utc_now,
) -> DeterministicFakeExecutionAdapter:
    return DeterministicFakeExecutionAdapter(
        result_factory=lambda action, _context, idempotency: NormalizedExecutionResult(
            adapter_code=adapter_code,
            attempt_status="timeout",
            response_snapshot={
                "provider_mode": "deterministic_fake",
                "workflow_action_id": action.workflow_action_id,
                "attempt_number": idempotency.attempt_number,
                "result": "timeout",
            },
            retry_eligible=True,
            failure_code=failure_code,
            completed_at=now(),
        )
    )


def fake_malformed_adapter(adapter_code: str) -> DeterministicFakeExecutionAdapter:
    return DeterministicFakeExecutionAdapter(
        result_factory=lambda action, _context, idempotency: {
            "adapter_code": adapter_code,
            "workflow_action_id": action.workflow_action_id,
            "attempt_number": idempotency.attempt_number,
            "result": "malformed",
        }
    )


def fake_exception_adapter(
    adapter_code: str,
    *,
    exception_factory: Callable[[], Exception] | None = None,
) -> DeterministicFakeExecutionAdapter:
    def _raise(_action: WorkflowAction, _context: ExecutionContext, _idempotency: ExecutionIdempotencyContext) -> Any:
        exception = RuntimeError("deterministic_fake_adapter_exception")
        if exception_factory is not None:
            exception = exception_factory()
        raise exception

    return DeterministicFakeExecutionAdapter(result_factory=_raise)


def execute_workflow_action(
    repository: WorkflowOrchestrationRepositoryProtocol,
    request: WorkflowActionExecutionRequest,
    *,
    adapter_registry: ExecutionAdapterRegistry | None = None,
    now: Callable[[], str] = _utc_now,
) -> WorkflowActionExecutionResult:
    snapshot = repository.load_case_snapshot(request.rental_case_id)
    if snapshot is None:
        return _execution_failure_result(
            rental_case_id=request.rental_case_id,
            workflow_action_id=request.workflow_action_id,
            case_revision=0,
            failure_code=EXECUTION_FAILURE_CASE_NOT_FOUND,
        )
    action = snapshot.find_workflow_action(request.workflow_action_id)
    if action is None:
        return _execution_failure_result(
            rental_case_id=request.rental_case_id,
            workflow_action_id=request.workflow_action_id,
            case_revision=snapshot.rental_case.case_revision,
            failure_code=EXECUTION_FAILURE_INVALID_EXECUTION_INPUT,
        )
    preflight_failure = _preflight_execution_failure(snapshot, action, now=now)
    if preflight_failure is not None:
        return _execution_failure_result(
            rental_case_id=action.rental_case_id,
            workflow_action_id=action.workflow_action_id,
            case_revision=snapshot.rental_case.case_revision,
            action_status=action.status,
            failure_code=preflight_failure,
            already_succeeded_idempotently=preflight_failure == EXECUTION_FAILURE_ACTION_ALREADY_SUCCEEDED,
        )
    try:
        _validate_action_payload(action.action_type, action.structured_payload)
    except ValueError:
        return _execution_failure_result(
            rental_case_id=action.rental_case_id,
            workflow_action_id=action.workflow_action_id,
            case_revision=snapshot.rental_case.case_revision,
            action_status=action.status,
            failure_code=EXECUTION_FAILURE_INVALID_EXECUTION_INPUT,
        )

    registry = adapter_registry or build_default_fake_execution_registry(now=now)
    adapter = registry.resolve(action.target_adapter_code)
    if adapter is None:
        return _execution_failure_result(
            rental_case_id=action.rental_case_id,
            workflow_action_id=action.workflow_action_id,
            case_revision=snapshot.rental_case.case_revision,
            action_status=action.status,
            failure_code=EXECUTION_FAILURE_ADAPTER_UNAVAILABLE,
        )
    availability_failure = adapter.availability_failure_code(action=action)
    if availability_failure is not None:
        return _execution_failure_result(
            rental_case_id=action.rental_case_id,
            workflow_action_id=action.workflow_action_id,
            case_revision=snapshot.rental_case.case_revision,
            action_status=action.status,
            failure_code=availability_failure,
        )

    started_at = request.started_at or now()
    start_result = repository.start_workflow_action_execution(
        replace(request, started_at=started_at)
    )
    if start_result.failure_codes:
        return WorkflowActionExecutionResult(
            rental_case_id=start_result.rental_case_id,
            workflow_action_id=start_result.workflow_action_id,
            case_revision=start_result.case_revision,
            action_status_before=start_result.action_status_before,
            action_status_after=start_result.action_status_after,
            audit_event_ids=start_result.audit_event_ids,
            execution_attempt_id=start_result.execution_attempt_id,
            failure_codes=start_result.failure_codes,
        )
    if start_result.execution_attempt_id is None or start_result.attempt_number is None:
        return _execution_failure_result(
            rental_case_id=action.rental_case_id,
            workflow_action_id=action.workflow_action_id,
            case_revision=snapshot.rental_case.case_revision,
            action_status=WORKFLOW_ACTION_STATUS_EXECUTING,
            failure_code=EXECUTION_FAILURE_INVALID_EXECUTION_INPUT,
        )

    execution_context = ExecutionContext(
        rental_case_id=request.rental_case_id,
        workflow_action_id=action.workflow_action_id,
        current_case_revision=snapshot.rental_case.case_revision,
        actor_reference=request.actor_reference,
        case_reference_code=snapshot.rental_case.case_reference_code,
        actor_type=request.actor_type,
        started_at=started_at,
        prior_attempts=tuple(
            sorted(
                snapshot.execution_attempts,
                key=lambda attempt: (attempt.attempt_number, attempt.execution_attempt_id),
            )
        ),
    )
    idempotency = ExecutionIdempotencyContext(
        workflow_action_id=action.workflow_action_id,
        execution_attempt_id=start_result.execution_attempt_id,
        attempt_number=start_result.attempt_number,
        semantic_idempotency_key=action.idempotency_key,
    )
    raw_result = _invoke_adapter(
        adapter,
        action=action,
        execution_context=execution_context,
        idempotency=idempotency,
        now=now,
    )
    normalized_result = _normalize_execution_result(
        raw_result,
        adapter_code=action.target_adapter_code,
        fallback_completed_at=now(),
    )
    completion_result = repository.complete_workflow_action_execution(
        WorkflowActionExecutionCompletionRequest(
            rental_case_id=request.rental_case_id,
            workflow_action_id=action.workflow_action_id,
            execution_attempt_id=start_result.execution_attempt_id,
            actor_reference=request.actor_reference,
            actor_type=request.actor_type,
            result=normalized_result,
        )
    )
    if completion_result.failure_codes:
        return completion_result

    follow_up_result = _maybe_update_follow_up_after_execution(
        repository,
        action=action,
        actor_reference=request.actor_reference,
        actor_type=request.actor_type,
        normalized_result=normalized_result,
        now=now,
    )
    reconciliation_result = None
    if not (
        completion_result.retry_eligible
        and completion_result.action_status_after == WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE
    ):
        reconciliation_result = reconcile_workflow_orchestration(
            repository,
            rental_case_id=request.rental_case_id,
            actor_reference=request.actor_reference,
            actor_type=request.actor_type or "system",
            now=lambda: normalized_result.completed_at or now(),
        )
    return replace(
        completion_result,
        updated_follow_up_id=None if follow_up_result is None else follow_up_result.follow_up_id,
        follow_up_status_before=None if follow_up_result is None else follow_up_result.status_before,
        follow_up_status_after=None if follow_up_result is None else follow_up_result.status_after,
        follow_up_attempt_count_after=None if follow_up_result is None else follow_up_result.attempt_count_after,
        reconciliation_result=reconciliation_result,
    )


def execute_ready_workflow_actions(
    repository: WorkflowOrchestrationRepositoryProtocol,
    *,
    rental_case_id: int | None = None,
    actor_reference: str,
    actor_type: str | None = "system",
    adapter_registry: ExecutionAdapterRegistry | None = None,
    now: Callable[[], str] = _utc_now,
) -> tuple[WorkflowActionExecutionResult, ...]:
    return tuple(
        execute_workflow_action(
            repository,
            WorkflowActionExecutionRequest(
                rental_case_id=action.rental_case_id,
                workflow_action_id=action.workflow_action_id,
                actor_reference=actor_reference,
                actor_type=actor_type,
            ),
            adapter_registry=adapter_registry,
            now=now,
        )
        for action in repository.list_ready_to_execute_actions(rental_case_id=rental_case_id)
    )


def evaluate_due_follow_ups(
    repository: WorkflowOrchestrationRepositoryProtocol,
    request: FollowUpEvaluationRequest,
    *,
    now: Callable[[], str] = _utc_now,
) -> FollowUpEvaluationResult:
    current_time = request.now or now()
    current_dt = _parse_timestamp(current_time)
    follow_ups = repository.list_follow_ups_for_evaluation(rental_case_id=request.rental_case_id)
    evaluated_ids: list[int] = []
    updated_ids: list[int] = []
    due_ids: list[int] = []
    overdue_ids: list[int] = []
    escalated_ids: list[int] = []
    completed_ids: list[int] = []
    audit_event_ids: list[int] = []
    reconciled_case_ids: list[int] = []
    created_action_ids: list[int] = []
    created_approval_ids: list[int] = []
    created_blocker_ids: list[int] = []
    failure_codes: list[str] = []
    cases_to_reconcile: set[int] = set()

    for follow_up in follow_ups:
        evaluated_ids.append(follow_up.follow_up_id)
        target_status = _target_follow_up_status(follow_up, current_dt=current_dt)
        final_status = follow_up.status
        if target_status is not None and target_status != follow_up.status:
            update_result = repository.commit_follow_up_status_update(
                FollowUpStatusUpdateRequest(
                    rental_case_id=follow_up.rental_case_id,
                    follow_up_id=follow_up.follow_up_id,
                    actor_reference=request.actor_reference,
                    actor_type=request.actor_type,
                    target_status=target_status,
                    expected_current_status=follow_up.status,
                    occurred_at=current_time,
                )
            )
            audit_event_ids.extend(update_result.audit_event_ids)
            if update_result.failure_codes:
                failure_codes.extend(update_result.failure_codes)
                continue
            updated_ids.append(follow_up.follow_up_id)
            final_status = update_result.status_after
        if final_status == FOLLOW_UP_STATUS_DUE:
            due_ids.append(follow_up.follow_up_id)
            cases_to_reconcile.add(follow_up.rental_case_id)
        elif final_status == FOLLOW_UP_STATUS_OVERDUE:
            overdue_ids.append(follow_up.follow_up_id)
            cases_to_reconcile.add(follow_up.rental_case_id)
        elif final_status == FOLLOW_UP_STATUS_ESCALATED:
            escalated_ids.append(follow_up.follow_up_id)
            cases_to_reconcile.add(follow_up.rental_case_id)
        elif final_status == FOLLOW_UP_STATUS_COMPLETED:
            completed_ids.append(follow_up.follow_up_id)

    for rental_case_id in sorted(cases_to_reconcile):
        reconciliation = reconcile_workflow_orchestration(
            repository,
            rental_case_id=rental_case_id,
            actor_reference=request.actor_reference,
            actor_type=request.actor_type or "system",
            now=lambda: current_time,
        )
        audit_event_ids.extend(reconciliation.audit_event_ids)
        created_action_ids.extend(reconciliation.created_action_ids)
        created_approval_ids.extend(reconciliation.created_approval_ids)
        created_blocker_ids.extend(reconciliation.created_blocker_ids)
        if not reconciliation.failure_codes:
            reconciled_case_ids.append(rental_case_id)
        else:
            failure_codes.extend(reconciliation.failure_codes)

    return FollowUpEvaluationResult(
        evaluated_follow_up_ids=tuple(evaluated_ids),
        updated_follow_up_ids=tuple(updated_ids),
        due_follow_up_ids=tuple(due_ids),
        overdue_follow_up_ids=tuple(overdue_ids),
        escalated_follow_up_ids=tuple(escalated_ids),
        completed_follow_up_ids=tuple(completed_ids),
        audit_event_ids=tuple(audit_event_ids),
        reconciled_case_ids=tuple(reconciled_case_ids),
        created_action_ids=tuple(created_action_ids),
        created_approval_ids=tuple(created_approval_ids),
        created_blocker_ids=tuple(created_blocker_ids),
        failure_codes=tuple(failure_codes),
    )


def _preflight_execution_failure(
    snapshot: WorkflowOrchestrationCaseSnapshot,
    action: WorkflowAction,
    *,
    now: Callable[[], str],
) -> str | None:
    if action.status == WORKFLOW_ACTION_STATUS_SUCCEEDED:
        return EXECUTION_FAILURE_ACTION_ALREADY_SUCCEEDED
    if action.approval_posture == APPROVAL_POSTURE_HUMAN_ONLY:
        return EXECUTION_FAILURE_ACTION_HUMAN_ONLY
    if action.approval_posture == APPROVAL_POSTURE_BLOCKED:
        return EXECUTION_FAILURE_ACTION_BLOCKED
    if action.status == WORKFLOW_ACTION_STATUS_CANCELLED:
        return EXECUTION_FAILURE_ACTION_CANCELLED
    if action.status == WORKFLOW_ACTION_STATUS_SUPERSEDED:
        return EXECUTION_FAILURE_ACTION_SUPERSEDED
    if action.status == WORKFLOW_ACTION_STATUS_EXECUTING:
        return EXECUTION_FAILURE_ACTION_ALREADY_EXECUTING
    if action.source_case_revision != snapshot.rental_case.case_revision:
        return EXECUTION_FAILURE_ACTION_STALE_REVISION
    due_dt = _parse_timestamp(action.due_at)
    if due_dt is not None and due_dt > _parse_timestamp(now()):
        return EXECUTION_FAILURE_ACTION_NOT_DUE
    if action.status != WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE:
        return EXECUTION_FAILURE_ACTION_NOT_EXECUTION_READY
    return None


def _invoke_adapter(
    adapter: ExecutionAdapterProtocol,
    *,
    action: WorkflowAction,
    execution_context: ExecutionContext,
    idempotency: ExecutionIdempotencyContext,
    now: Callable[[], str],
) -> Any:
    try:
        return adapter.execute(
            action=action,
            execution_context=execution_context,
            idempotency=idempotency,
        )
    except Exception as exc:
        return NormalizedExecutionResult(
            adapter_code=action.target_adapter_code,
            attempt_status=EXECUTION_ATTEMPT_STATUS_FAILED,
            response_snapshot={
                "error_type": type(exc).__name__,
                "message": str(exc),
            },
            retry_eligible=True,
            failure_code=EXECUTION_FAILURE_ADAPTER_EXCEPTION,
            completed_at=now(),
        )


def _normalize_execution_result(
    raw_result: Any,
    *,
    adapter_code: str,
    fallback_completed_at: str,
) -> NormalizedExecutionResult:
    if isinstance(raw_result, NormalizedExecutionResult):
        if raw_result.adapter_code != adapter_code:
            return NormalizedExecutionResult(
                adapter_code=adapter_code,
                attempt_status=EXECUTION_ATTEMPT_STATUS_FAILED,
                response_snapshot={
                    "reason": "adapter_code_mismatch",
                    "received_adapter_code": raw_result.adapter_code,
                },
                retry_eligible=False,
                failure_code=EXECUTION_FAILURE_ADAPTER_RESULT_MALFORMED,
                completed_at=fallback_completed_at,
            )
        if raw_result.completed_at is None:
            return replace(raw_result, completed_at=fallback_completed_at)
        return raw_result
    return NormalizedExecutionResult(
        adapter_code=adapter_code,
        attempt_status=EXECUTION_ATTEMPT_STATUS_FAILED,
        response_snapshot={
            "reason": "unexpected_adapter_result_type",
            "result_type": type(raw_result).__name__,
        },
        retry_eligible=False,
        failure_code=EXECUTION_FAILURE_ADAPTER_RESULT_MALFORMED,
        completed_at=fallback_completed_at,
    )


def _maybe_update_follow_up_after_execution(
    repository: WorkflowOrchestrationRepositoryProtocol,
    *,
    action: WorkflowAction,
    actor_reference: str,
    actor_type: str | None,
    normalized_result: NormalizedExecutionResult,
    now: Callable[[], str],
):
    follow_up_id = _follow_up_id_from_action(action)
    if follow_up_id is None:
        return None
    snapshot = repository.load_case_snapshot(action.rental_case_id)
    if snapshot is None:
        return None
    follow_up = snapshot.find_follow_up(follow_up_id)
    if follow_up is None:
        return None
    if follow_up.status in {FOLLOW_UP_STATUS_COMPLETED, FOLLOW_UP_STATUS_CANCELLED}:
        return None
    completed_at = normalized_result.completed_at or now()
    target_status = (
        FOLLOW_UP_STATUS_COMPLETED
        if normalized_result.attempt_status == EXECUTION_ATTEMPT_STATUS_SUCCEEDED
        else _post_attempt_follow_up_status(follow_up)
    )
    return repository.commit_follow_up_status_update(
        FollowUpStatusUpdateRequest(
            rental_case_id=follow_up.rental_case_id,
            follow_up_id=follow_up.follow_up_id,
            actor_reference=actor_reference,
            actor_type=actor_type,
            target_status=target_status,
            expected_current_status=follow_up.status,
            attempt_count_delta=1,
            occurred_at=completed_at,
            completed_at=completed_at if target_status == FOLLOW_UP_STATUS_COMPLETED else None,
        )
    )


def _follow_up_id_from_action(action: WorkflowAction) -> int | None:
    if action.reason_entity_type == "follow_up" and action.reason_entity_id is not None:
        return action.reason_entity_id
    follow_up_id = action.structured_payload.get("follow_up_id")
    return follow_up_id if isinstance(follow_up_id, int) and follow_up_id > 0 else None


def _post_attempt_follow_up_status(follow_up: FollowUp) -> str:
    next_attempt_count = follow_up.attempt_count + 1
    if follow_up.escalate_after is not None and next_attempt_count >= follow_up.escalate_after:
        return FOLLOW_UP_STATUS_ESCALATED
    return FOLLOW_UP_STATUS_OVERDUE


def _target_follow_up_status(
    follow_up: FollowUp,
    *,
    current_dt: datetime,
) -> str | None:
    if follow_up.status in {FOLLOW_UP_STATUS_COMPLETED, FOLLOW_UP_STATUS_CANCELLED}:
        return None
    due_dt = _parse_timestamp(follow_up.due_at)
    if due_dt is None or due_dt > current_dt:
        return None
    if follow_up.status == FOLLOW_UP_STATUS_ESCALATED:
        return FOLLOW_UP_STATUS_ESCALATED
    if follow_up.escalate_after is not None and follow_up.attempt_count >= follow_up.escalate_after:
        return FOLLOW_UP_STATUS_ESCALATED
    if follow_up.attempt_count > 0 or follow_up.status == FOLLOW_UP_STATUS_OVERDUE:
        return FOLLOW_UP_STATUS_OVERDUE
    return FOLLOW_UP_STATUS_DUE


def _execution_failure_result(
    *,
    rental_case_id: int,
    workflow_action_id: int,
    case_revision: int,
    failure_code: str,
    action_status: str = WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
    already_succeeded_idempotently: bool = False,
) -> WorkflowActionExecutionResult:
    return WorkflowActionExecutionResult(
        rental_case_id=rental_case_id,
        workflow_action_id=workflow_action_id,
        case_revision=case_revision,
        action_status_before=action_status,
        action_status_after=action_status,
        failure_codes=(failure_code,),
        already_succeeded_idempotently=already_succeeded_idempotently,
    )
