from __future__ import annotations

from dataclasses import replace
from typing import Any

from .contracts import LIFECYCLE_STATES, RentalCase
from .lifecycle_guards import evaluate_transition_guards
from .lifecycle_repository import LifecycleCaseSnapshot, LifecycleRepositoryProtocol
from .lifecycle_types import (
    GuardResult,
    LifecycleCaseEvaluation,
    LifecycleTransitionResult,
    ManualTransitionOverrideRequest,
    ReadinessReevaluation,
    TransitionEvaluation,
    LIFECYCLE_FAILURE_CASE_NOT_FOUND,
    LIFECYCLE_FAILURE_GUARD_FAILED,
    LIFECYCLE_FAILURE_INVALID_TARGET_STATE,
    LIFECYCLE_FAILURE_MANUAL_OVERRIDE_REQUIRED,
    LIFECYCLE_FAILURE_STALE_CASE_REVISION,
    LIFECYCLE_FAILURE_TERMINAL_STATE,
    LIFECYCLE_FAILURE_TRANSITION_COMMIT_FAILED,
    LIFECYCLE_FAILURE_TRANSITION_NOT_ALLOWED,
)


NORMAL_TRANSITION_GRAPH: dict[str, tuple[str, ...]] = {
    "inquiry_active": ("proposal_in_progress", "dormant", "closed_lost"),
    "proposal_in_progress": ("proposal_pending_client", "dormant", "closed_lost"),
    "proposal_pending_client": ("proposal_in_progress", "confirmation_pending", "dormant", "closed_lost"),
    "confirmation_pending": ("confirmed_pre_event", "proposal_in_progress", "dormant", "closed_lost"),
    "confirmed_pre_event": ("event_ready", "cancelled"),
    "event_ready": ("confirmed_pre_event", "event_in_progress", "cancelled"),
    "event_in_progress": ("close_out_in_progress",),
    "close_out_in_progress": ("closed",),
    "dormant": ("inquiry_active", "proposal_in_progress", "proposal_pending_client", "confirmation_pending", "closed_lost"),
    "closed": (),
    "closed_lost": (),
    "cancelled": (),
}

TERMINAL_STATES = frozenset({"closed", "closed_lost", "cancelled"})
LIFECYCLE_TRANSITION_EVENT_TYPE = "lifecycle_transition_committed"
LIFECYCLE_MANUAL_OVERRIDE_EVENT_TYPE = "lifecycle_manual_override_committed"


class LifecycleTransitionRejected(RuntimeError):
    def __init__(self, evaluation: TransitionEvaluation) -> None:
        self.evaluation = evaluation
        message = ", ".join(evaluation.reason_codes) or "transition rejected"
        super().__init__(message)


def evaluate_transition(
    repository: LifecycleRepositoryProtocol,
    rental_case_id: int,
    requested_target_state: str,
    *,
    transition_context: dict[str, Any] | None = None,
) -> TransitionEvaluation:
    if requested_target_state not in LIFECYCLE_STATES:
        return TransitionEvaluation(
            rental_case_id=rental_case_id,
            current_state=None,
            requested_target_state=requested_target_state,
            evaluated_case_revision=None,
            edge_allowed=False,
            guard_passed=False,
            allowed=False,
            manual_override_required=False,
            reason_codes=(LIFECYCLE_FAILURE_INVALID_TARGET_STATE,),
        )

    snapshot = repository.load_case_snapshot(rental_case_id)
    if snapshot is None:
        return TransitionEvaluation(
            rental_case_id=rental_case_id,
            current_state=None,
            requested_target_state=requested_target_state,
            evaluated_case_revision=None,
            edge_allowed=False,
            guard_passed=False,
            allowed=False,
            manual_override_required=False,
            reason_codes=(LIFECYCLE_FAILURE_CASE_NOT_FOUND,),
        )

    current_state = snapshot.rental_case.lifecycle_state
    if current_state == requested_target_state:
        return TransitionEvaluation(
            rental_case_id=rental_case_id,
            current_state=current_state,
            requested_target_state=requested_target_state,
            evaluated_case_revision=snapshot.rental_case.case_revision,
            edge_allowed=False,
            guard_passed=False,
            allowed=False,
            manual_override_required=False,
            reason_codes=(LIFECYCLE_FAILURE_TRANSITION_NOT_ALLOWED,),
        )

    outgoing = NORMAL_TRANSITION_GRAPH[current_state]
    edge_allowed = requested_target_state in outgoing
    if not edge_allowed:
        terminal = current_state in TERMINAL_STATES
        reasons = (LIFECYCLE_FAILURE_TERMINAL_STATE,) if terminal else (LIFECYCLE_FAILURE_TRANSITION_NOT_ALLOWED,)
        if terminal or requested_target_state in LIFECYCLE_STATES:
            reasons = reasons + (LIFECYCLE_FAILURE_MANUAL_OVERRIDE_REQUIRED,)
        return TransitionEvaluation(
            rental_case_id=rental_case_id,
            current_state=current_state,
            requested_target_state=requested_target_state,
            evaluated_case_revision=snapshot.rental_case.case_revision,
            edge_allowed=False,
            guard_passed=False,
            allowed=False,
            manual_override_required=True,
            reason_codes=reasons,
        )

    guard_results = evaluate_transition_guards(
        snapshot=snapshot,
        target_state=requested_target_state,
        transition_context=transition_context,
    )
    guard_passed = all(result.passed for result in guard_results)
    reason_codes = _reason_codes_from_guards(guard_results)
    return TransitionEvaluation(
        rental_case_id=rental_case_id,
        current_state=current_state,
        requested_target_state=requested_target_state,
        evaluated_case_revision=snapshot.rental_case.case_revision,
        edge_allowed=True,
        guard_passed=guard_passed,
        allowed=guard_passed,
        manual_override_required=False,
        reason_codes=reason_codes,
        guard_results=guard_results,
        blocking_blocker_ids=_aggregate_ids(guard_results, "blocking_blocker_ids"),
        blocking_requirement_ids=_aggregate_ids(guard_results, "blocking_requirement_ids"),
        blocking_open_question_ids=_aggregate_ids(guard_results, "blocking_open_question_ids"),
        blocking_approval_request_ids=_aggregate_ids(guard_results, "blocking_approval_request_ids"),
        blocking_proposed_change_ids=_aggregate_ids(guard_results, "blocking_proposed_change_ids"),
        evidence_event_ids=_aggregate_ids(guard_results, "evidence_event_ids"),
    )


def apply_transition(
    repository: LifecycleRepositoryProtocol,
    rental_case_id: int,
    requested_target_state: str,
    *,
    expected_case_revision: int,
    reason_code: str,
    actor_reference: str,
    actor_type: str | None = None,
    source_type: str = "lifecycle_engine",
    source_reference: str | None = None,
    triggering_event_id: int | None = None,
    transition_context: dict[str, Any] | None = None,
) -> LifecycleTransitionResult:
    evaluation = evaluate_transition(
        repository,
        rental_case_id,
        requested_target_state,
        transition_context=transition_context,
    )
    if not evaluation.allowed:
        raise LifecycleTransitionRejected(evaluation)
    if evaluation.evaluated_case_revision != expected_case_revision:
        raise LifecycleTransitionRejected(
            replace(
                evaluation,
                allowed=False,
                guard_passed=False,
                reason_codes=(LIFECYCLE_FAILURE_STALE_CASE_REVISION,),
            )
        )

    context = transition_context or {}
    try:
        return repository.commit_transition(
            rental_case_id=rental_case_id,
            expected_case_revision=expected_case_revision,
            expected_current_state=evaluation.current_state or "",
            target_state=requested_target_state,
            transition_reason_code=reason_code,
            actor_reference=actor_reference,
            actor_type=actor_type,
            source_type=source_type,
            source_reference=source_reference,
            triggering_event_id=triggering_event_id,
            override_applied=False,
            transition_event_type_code=LIFECYCLE_TRANSITION_EVENT_TYPE,
            transition_event_payload=_build_transition_event_payload(
                evaluation=evaluation,
                reason_code=reason_code,
                transition_context=context,
                manual_override=False,
            ),
            dormant_origin_state=_dormant_origin_state(evaluation),
            resume_target_state=context.get("resume_target_state"),
            dormant_reason_code=context.get("dormant_reason_code"),
            dormant_review_at=context.get("dormant_review_at"),
        )
    except Exception as exc:  # pragma: no cover - exercised through DB tests and targeted mapping tests
        mapped = _map_commit_exception(repository, rental_case_id, requested_target_state, exc)
        if mapped is not None:
            raise LifecycleTransitionRejected(mapped) from exc
        raise LifecycleTransitionRejected(
            replace(
                evaluation,
                allowed=False,
                guard_passed=False,
                reason_codes=(LIFECYCLE_FAILURE_TRANSITION_COMMIT_FAILED,),
            )
        ) from exc


def apply_manual_transition_override(
    repository: LifecycleRepositoryProtocol,
    request: ManualTransitionOverrideRequest,
) -> LifecycleTransitionResult:
    snapshot = repository.load_case_snapshot(request.rental_case_id)
    if snapshot is None:
        evaluation = TransitionEvaluation(
            rental_case_id=request.rental_case_id,
            current_state=None,
            requested_target_state=request.target_state,
            evaluated_case_revision=None,
            edge_allowed=False,
            guard_passed=False,
            allowed=False,
            manual_override_required=False,
            reason_codes=(LIFECYCLE_FAILURE_CASE_NOT_FOUND,),
        )
        raise LifecycleTransitionRejected(evaluation)
    if snapshot.rental_case.case_revision != request.expected_case_revision:
        evaluation = TransitionEvaluation(
            rental_case_id=request.rental_case_id,
            current_state=snapshot.rental_case.lifecycle_state,
            requested_target_state=request.target_state,
            evaluated_case_revision=snapshot.rental_case.case_revision,
            edge_allowed=False,
            guard_passed=False,
            allowed=False,
            manual_override_required=True,
            reason_codes=(LIFECYCLE_FAILURE_STALE_CASE_REVISION,),
        )
        raise LifecycleTransitionRejected(evaluation)

    try:
        return repository.commit_transition(
            rental_case_id=request.rental_case_id,
            expected_case_revision=request.expected_case_revision,
            expected_current_state=snapshot.rental_case.lifecycle_state,
            target_state=request.target_state,
            transition_reason_code=request.reason_code,
            actor_reference=request.actor_reference,
            actor_type=request.actor_type,
            source_type=request.source_type,
            source_reference=request.source_reference,
            triggering_event_id=request.triggering_event_id,
            override_applied=True,
            transition_event_type_code=LIFECYCLE_MANUAL_OVERRIDE_EVENT_TYPE,
            transition_event_payload={
                "audit_note": request.audit_note,
                "transition_context": request.transition_context,
                "manual_override": True,
                "previous_state": snapshot.rental_case.lifecycle_state,
                "new_state": request.target_state,
            },
            dormant_origin_state=snapshot.rental_case.lifecycle_state if request.target_state == "dormant" else None,
            resume_target_state=request.transition_context.get("resume_target_state"),
            dormant_reason_code=request.transition_context.get("dormant_reason_code"),
            dormant_review_at=request.transition_context.get("dormant_review_at"),
        )
    except Exception as exc:  # pragma: no cover - exercised through DB tests and targeted mapping tests
        evaluation = _map_commit_exception(repository, request.rental_case_id, request.target_state, exc)
        if evaluation is not None:
            raise LifecycleTransitionRejected(evaluation) from exc
        raise


def reevaluate_readiness(
    repository: LifecycleRepositoryProtocol,
    rental_case_id: int,
) -> ReadinessReevaluation:
    snapshot = repository.load_case_snapshot(rental_case_id)
    if snapshot is None:
        return ReadinessReevaluation(
            rental_case_id=rental_case_id,
            case_found=False,
            current_state=None,
            evaluated_case_revision=None,
            readiness_passed=False,
            degradation_allowed=False,
            reason_codes=(LIFECYCLE_FAILURE_CASE_NOT_FOUND,),
        )

    if snapshot.rental_case.lifecycle_state == "event_ready":
        degradation_evaluation = evaluate_transition(repository, rental_case_id, "confirmed_pre_event")
        readiness_passed = not degradation_evaluation.allowed
        return ReadinessReevaluation(
            rental_case_id=rental_case_id,
            case_found=True,
            current_state="event_ready",
            evaluated_case_revision=snapshot.rental_case.case_revision,
            readiness_passed=readiness_passed,
            degradation_allowed=degradation_evaluation.allowed,
            degradation_target_state="confirmed_pre_event" if degradation_evaluation.allowed else None,
            reason_codes=degradation_evaluation.reason_codes,
            blocker_ids=degradation_evaluation.blocking_blocker_ids,
            requirement_ids=degradation_evaluation.blocking_requirement_ids,
            approval_request_ids=degradation_evaluation.blocking_approval_request_ids,
            evidence_event_ids=degradation_evaluation.evidence_event_ids,
        )

    readiness_evaluation = evaluate_transition(repository, rental_case_id, "event_ready")
    return ReadinessReevaluation(
        rental_case_id=rental_case_id,
        case_found=True,
        current_state=snapshot.rental_case.lifecycle_state,
        evaluated_case_revision=snapshot.rental_case.case_revision,
        readiness_passed=readiness_evaluation.allowed,
        degradation_allowed=False,
        degradation_target_state=None,
        reason_codes=readiness_evaluation.reason_codes,
        blocker_ids=readiness_evaluation.blocking_blocker_ids,
        requirement_ids=readiness_evaluation.blocking_requirement_ids,
        approval_request_ids=readiness_evaluation.blocking_approval_request_ids,
        evidence_event_ids=readiness_evaluation.evidence_event_ids,
    )


def evaluate_case_state(
    repository: LifecycleRepositoryProtocol,
    rental_case_id: int,
    *,
    transition_contexts: dict[str, dict[str, Any]] | None = None,
) -> LifecycleCaseEvaluation:
    snapshot = repository.load_case_snapshot(rental_case_id)
    if snapshot is None:
        return LifecycleCaseEvaluation(
            rental_case_id=rental_case_id,
            case_found=False,
            reason_codes=(LIFECYCLE_FAILURE_CASE_NOT_FOUND,),
        )

    current_state = snapshot.rental_case.lifecycle_state
    outgoing = NORMAL_TRANSITION_GRAPH[current_state]
    evaluations = tuple(
        evaluate_transition(
            repository,
            rental_case_id,
            target_state,
            transition_context=(transition_contexts or {}).get(target_state),
        )
        for target_state in outgoing
    )
    eligible = tuple(evaluation.requested_target_state for evaluation in evaluations if evaluation.allowed)
    blocked = tuple(evaluation.requested_target_state for evaluation in evaluations if not evaluation.allowed)
    combined_reason_codes = tuple(dict.fromkeys(code for evaluation in evaluations for code in evaluation.reason_codes))
    readiness_passed = None
    if current_state in {"confirmed_pre_event", "event_ready"}:
        readiness_passed = reevaluate_readiness(repository, rental_case_id).readiness_passed
    return LifecycleCaseEvaluation(
        rental_case_id=rental_case_id,
        case_found=True,
        current_state=current_state,
        current_case_revision=snapshot.rental_case.case_revision,
        normal_outgoing_transitions=outgoing,
        eligible_transitions=eligible,
        blocked_transitions=blocked,
        transition_evaluations=evaluations,
        reason_codes=combined_reason_codes,
        blocker_ids=_aggregate_ids(tuple(result for evaluation in evaluations for result in evaluation.guard_results), "blocking_blocker_ids"),
        requirement_ids=_aggregate_ids(tuple(result for evaluation in evaluations for result in evaluation.guard_results), "blocking_requirement_ids"),
        approval_request_ids=_aggregate_ids(tuple(result for evaluation in evaluations for result in evaluation.guard_results), "blocking_approval_request_ids"),
        dormant_resume_target=snapshot.rental_case.resume_target_state,
        terminal_state=current_state in TERMINAL_STATES,
        readiness_passed=readiness_passed,
    )


def _reason_codes_from_guards(guard_results: tuple[GuardResult, ...]) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for result in guard_results:
        if result.reason_code is None:
            continue
        if result.reason_code not in seen:
            seen.add(result.reason_code)
            ordered.append(result.reason_code)
    if ordered:
        return tuple(ordered)
    return ()


def _aggregate_ids(guard_results: tuple[GuardResult, ...], field_name: str) -> tuple[int, ...]:
    ordered: list[int] = []
    seen: set[int] = set()
    for result in guard_results:
        for value in getattr(result, field_name):
            if value not in seen:
                seen.add(value)
                ordered.append(value)
    return tuple(ordered)


def _build_transition_event_payload(
    *,
    evaluation: TransitionEvaluation,
    reason_code: str,
    transition_context: dict[str, Any],
    manual_override: bool,
) -> dict[str, Any]:
    return {
        "previous_state": evaluation.current_state,
        "new_state": evaluation.requested_target_state,
        "previous_revision": evaluation.evaluated_case_revision,
        "new_revision": (evaluation.evaluated_case_revision or 0) + 1,
        "transition_reason_code": reason_code,
        "manual_override": manual_override,
        "blocking_ids": {
            "blockers": evaluation.blocking_blocker_ids,
            "requirements": evaluation.blocking_requirement_ids,
            "open_questions": evaluation.blocking_open_question_ids,
            "approval_requests": evaluation.blocking_approval_request_ids,
            "proposed_changes": evaluation.blocking_proposed_change_ids,
        },
        "evidence_event_ids": evaluation.evidence_event_ids,
        "transition_context": transition_context,
    }


def _dormant_origin_state(evaluation: TransitionEvaluation) -> str | None:
    if evaluation.requested_target_state != "dormant":
        return None
    return evaluation.current_state


def _map_commit_exception(
    repository: LifecycleRepositoryProtocol,
    rental_case_id: int,
    requested_target_state: str,
    exc: Exception,
) -> TransitionEvaluation | None:
    message_parts = [str(exc)]
    for attr in ("stderr", "stdout"):
        value = getattr(exc, attr, None)
        if value:
            message_parts.append(str(value))
    combined = " ".join(message_parts)
    snapshot = repository.load_case_snapshot(rental_case_id)
    current_state = snapshot.rental_case.lifecycle_state if snapshot is not None else None
    current_revision = snapshot.rental_case.case_revision if snapshot is not None else None
    if "stale_case_revision" in combined:
        return TransitionEvaluation(
            rental_case_id=rental_case_id,
            current_state=current_state,
            requested_target_state=requested_target_state,
            evaluated_case_revision=current_revision,
            edge_allowed=False,
            guard_passed=False,
            allowed=False,
            manual_override_required=False,
            reason_codes=(LIFECYCLE_FAILURE_STALE_CASE_REVISION,),
        )
    if "case_not_found" in combined:
        return TransitionEvaluation(
            rental_case_id=rental_case_id,
            current_state=None,
            requested_target_state=requested_target_state,
            evaluated_case_revision=None,
            edge_allowed=False,
            guard_passed=False,
            allowed=False,
            manual_override_required=False,
            reason_codes=(LIFECYCLE_FAILURE_CASE_NOT_FOUND,),
        )
    if "transition_not_allowed" in combined or "current_state_mismatch" in combined:
        return TransitionEvaluation(
            rental_case_id=rental_case_id,
            current_state=current_state,
            requested_target_state=requested_target_state,
            evaluated_case_revision=current_revision,
            edge_allowed=False,
            guard_passed=False,
            allowed=False,
            manual_override_required=False,
            reason_codes=(LIFECYCLE_FAILURE_TRANSITION_NOT_ALLOWED,),
        )
    return None
