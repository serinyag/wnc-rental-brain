from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from .contracts import (
    ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
    ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
    FOLLOW_UP_CADENCE_INQUIRY_COLD_WEEKLY,
    FOLLOW_UP_REASON_INQUIRY_MISSING_INFORMATION,
    FOLLOW_UP_STATUS_CANCELLED,
    FOLLOW_UP_STATUS_COMPLETED,
    FOLLOW_UP_STATUS_ESCALATED,
    FOLLOW_UP_STATUS_SCHEDULED,
    FOLLOW_UP_URGENCY_HIGH,
    FOLLOW_UP_URGENCY_MEDIUM,
    LIFECYCLE_STATE_CANCELLED,
    LIFECYCLE_STATE_CLOSED,
    LIFECYCLE_STATE_CLOSED_LOST,
    LIFECYCLE_STATE_INQUIRY_ACTIVE,
    OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION,
    OPEN_QUESTION_STATUS_OPEN,
    FollowUp,
)
from .execution_types import FollowUpStatusUpdateRequest
from .inquiry_intake import CORE_INQUIRY_FIELD_RULES
from .orchestration_repository import WorkflowOrchestrationCaseSnapshot, WorkflowOrchestrationRepositoryProtocol
from .orchestration_runtime import reconcile_workflow_orchestration
from .validation import (
    ensure_bool,
    ensure_json_compatible,
    ensure_non_empty_text,
    ensure_non_negative_int,
    ensure_optional_non_empty_text,
    ensure_positive_int,
    ensure_tuple_of_non_empty_text,
)


INQUIRY_WAITING_FAILURE_CASE_NOT_FOUND = "case_not_found"
INQUIRY_WAITING_FAILURE_STALE_CASE_REVISION = "stale_case_revision"

TERMINAL_LIFECYCLE_STATES = frozenset(
    {
        LIFECYCLE_STATE_CLOSED,
        LIFECYCLE_STATE_CLOSED_LOST,
        LIFECYCLE_STATE_CANCELLED,
    }
)
TERMINAL_FOLLOW_UP_STATUSES = frozenset({FOLLOW_UP_STATUS_COMPLETED, FOLLOW_UP_STATUS_CANCELLED})
INQUIRY_QUESTION_TYPES = frozenset(rule.question_type for rule in CORE_INQUIRY_FIELD_RULES.values())
QUESTION_TYPE_TO_FIELD_CODE = {
    rule.question_type: rule.inquiry_field_code
    for rule in CORE_INQUIRY_FIELD_RULES.values()
}
FIELD_CODE_LABELS = {
    "requested_schedule": "Requested schedule",
    "guest_count": "Guest count",
    "requested_space": "Requested space",
    "event_type": "Event type",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_timestamp(value: str | None) -> datetime | None:
    if value is None or not value.strip():
        return None
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _hash_material(material: dict[str, Any]) -> str:
    payload = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class InquiryFollowUpPolicy:
    cold_follow_up_delay_days: int = 7
    max_cold_follow_ups: int = 2
    urgent_event_threshold_days: int = 3

    def __post_init__(self) -> None:
        ensure_non_negative_int("cold_follow_up_delay_days", self.cold_follow_up_delay_days)
        ensure_positive_int("max_cold_follow_ups", self.max_cold_follow_ups)
        ensure_positive_int("urgent_event_threshold_days", self.urgent_event_threshold_days)


DEFAULT_INQUIRY_FOLLOW_UP_POLICY = InquiryFollowUpPolicy()


@dataclass(frozen=True)
class InquiryWaitingFollowUpTarget:
    semantic_identity_key: str
    sequence_number: int
    due_at: str
    status: str
    urgency_level: str
    next_action_type: str
    context_payload: dict[str, Any]
    waiting_for_role: str | None = None
    waiting_for_reference: str | None = None
    cadence_policy_code: str = FOLLOW_UP_CADENCE_INQUIRY_COLD_WEEKLY
    attempt_count: int = 0

    def __post_init__(self) -> None:
        ensure_non_empty_text("semantic_identity_key", self.semantic_identity_key)
        ensure_positive_int("sequence_number", self.sequence_number)
        ensure_non_empty_text("due_at", self.due_at)
        ensure_non_empty_text("status", self.status)
        ensure_non_empty_text("urgency_level", self.urgency_level)
        ensure_non_empty_text("next_action_type", self.next_action_type)
        ensure_json_compatible("context_payload", self.context_payload)
        ensure_optional_non_empty_text("waiting_for_role", self.waiting_for_role)
        ensure_optional_non_empty_text("waiting_for_reference", self.waiting_for_reference)
        ensure_non_empty_text("cadence_policy_code", self.cadence_policy_code)
        ensure_non_negative_int("attempt_count", self.attempt_count)


@dataclass(frozen=True)
class InquiryWaitingPlan:
    rental_case_id: int
    evaluated_case_revision: int
    waiting_required: bool
    reason_codes: tuple[str, ...]
    open_question_ids: tuple[int, ...]
    required_field_codes: tuple[str, ...]
    lead_posture: str
    event_proximity: str
    recommended_follow_up_due_at: str | None
    follow_up_type: str | None
    escalation_required: bool
    action_formation_eligible: bool
    cancel_follow_up_ids: tuple[int, ...] = ()
    desired_follow_up: InquiryWaitingFollowUpTarget | None = None
    plan_fingerprint: str = ""

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_non_negative_int("evaluated_case_revision", self.evaluated_case_revision)
        ensure_bool("waiting_required", self.waiting_required)
        ensure_tuple_of_non_empty_text("reason_codes", self.reason_codes)
        ensure_tuple_of_non_empty_text(
            "open_question_ids",
            tuple(str(question_id) for question_id in self.open_question_ids),
        )
        ensure_tuple_of_non_empty_text("required_field_codes", self.required_field_codes)
        ensure_non_empty_text("lead_posture", self.lead_posture)
        ensure_non_empty_text("event_proximity", self.event_proximity)
        ensure_optional_non_empty_text("recommended_follow_up_due_at", self.recommended_follow_up_due_at)
        ensure_optional_non_empty_text("follow_up_type", self.follow_up_type)
        ensure_bool("escalation_required", self.escalation_required)
        ensure_bool("action_formation_eligible", self.action_formation_eligible)
        ensure_tuple_of_non_empty_text(
            "cancel_follow_up_ids",
            tuple(str(follow_up_id) for follow_up_id in self.cancel_follow_up_ids),
        )
        if self.desired_follow_up is not None and not isinstance(self.desired_follow_up, InquiryWaitingFollowUpTarget):
            raise TypeError("desired_follow_up must be an InquiryWaitingFollowUpTarget.")
        ensure_non_empty_text("plan_fingerprint", self.plan_fingerprint)


@dataclass(frozen=True)
class InquiryWaitingCommitResult:
    rental_case_id: int
    case_revision_before: int
    case_revision_after: int
    plan: InquiryWaitingPlan
    created_follow_up_ids: tuple[int, ...] = ()
    updated_follow_up_ids: tuple[int, ...] = ()
    cancelled_follow_up_ids: tuple[int, ...] = ()
    created_action_ids: tuple[int, ...] = ()
    superseded_action_ids: tuple[int, ...] = ()
    audit_event_ids: tuple[int, ...] = ()
    failure_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_non_negative_int("case_revision_before", self.case_revision_before)
        ensure_non_negative_int("case_revision_after", self.case_revision_after)
        ensure_tuple_of_non_empty_text(
            "created_follow_up_ids",
            tuple(str(value) for value in self.created_follow_up_ids),
        )
        ensure_tuple_of_non_empty_text(
            "updated_follow_up_ids",
            tuple(str(value) for value in self.updated_follow_up_ids),
        )
        ensure_tuple_of_non_empty_text(
            "cancelled_follow_up_ids",
            tuple(str(value) for value in self.cancelled_follow_up_ids),
        )
        ensure_tuple_of_non_empty_text(
            "created_action_ids",
            tuple(str(value) for value in self.created_action_ids),
        )
        ensure_tuple_of_non_empty_text(
            "superseded_action_ids",
            tuple(str(value) for value in self.superseded_action_ids),
        )
        ensure_tuple_of_non_empty_text(
            "audit_event_ids",
            tuple(str(value) for value in self.audit_event_ids),
        )
        ensure_tuple_of_non_empty_text("failure_codes", self.failure_codes)


def reconcile_inquiry_waiting(
    repository: WorkflowOrchestrationRepositoryProtocol,
    *,
    rental_case_id: int,
    actor_reference: str,
    actor_type: str | None,
    expected_case_revision: int | None = None,
    now: Callable[[], str] = _utc_now,
    policy: InquiryFollowUpPolicy = DEFAULT_INQUIRY_FOLLOW_UP_POLICY,
) -> InquiryWaitingCommitResult:
    snapshot = repository.load_case_snapshot(rental_case_id)
    if snapshot is None:
        return InquiryWaitingCommitResult(
            rental_case_id=rental_case_id,
            case_revision_before=0,
            case_revision_after=0,
            plan=_empty_plan(rental_case_id),
            failure_codes=(INQUIRY_WAITING_FAILURE_CASE_NOT_FOUND,),
        )
    if expected_case_revision is not None and snapshot.rental_case.case_revision != expected_case_revision:
        return InquiryWaitingCommitResult(
            rental_case_id=rental_case_id,
            case_revision_before=snapshot.rental_case.case_revision,
            case_revision_after=snapshot.rental_case.case_revision,
            plan=_empty_plan(rental_case_id, evaluated_case_revision=snapshot.rental_case.case_revision),
            failure_codes=(INQUIRY_WAITING_FAILURE_STALE_CASE_REVISION,),
        )
    current_time = now()
    plan = evaluate_inquiry_waiting(snapshot, current_time=current_time, policy=policy)
    return apply_inquiry_waiting_plan(
        repository,
        plan,
        actor_reference=actor_reference,
        actor_type=actor_type,
        now=lambda: current_time,
    )


def evaluate_inquiry_waiting(
    snapshot: WorkflowOrchestrationCaseSnapshot,
    *,
    current_time: str,
    policy: InquiryFollowUpPolicy = DEFAULT_INQUIRY_FOLLOW_UP_POLICY,
) -> InquiryWaitingPlan:
    current_dt = _parse_timestamp(current_time)
    if current_dt is None:
        current_dt = _parse_timestamp(_utc_now())
    assert current_dt is not None

    relevant_questions = tuple(_relevant_inquiry_questions(snapshot))
    open_question_ids = tuple(question.open_question_id for question in relevant_questions)
    required_field_codes = tuple(
        dict.fromkeys(
            QUESTION_TYPE_TO_FIELD_CODE.get(question.question_type, question.question_type)
            for question in relevant_questions
        )
    )
    active_follow_ups = _active_inquiry_follow_ups(snapshot)
    current_follow_up = None if not active_follow_ups else active_follow_ups[-1]
    cancel_follow_up_ids = [
        follow_up.follow_up_id
        for follow_up in active_follow_ups[:-1]
    ]

    event_proximity = _event_proximity(snapshot.rental_case.active_event_start, current_dt, policy)
    escalation_required = event_proximity == "urgent"
    waiting_required = (
        snapshot.rental_case.lifecycle_state == LIFECYCLE_STATE_INQUIRY_ACTIVE
        and snapshot.rental_case.lifecycle_state not in TERMINAL_LIFECYCLE_STATES
        and bool(relevant_questions)
    )
    lead_posture = "time_critical_inquiry" if escalation_required else "cold_inquiry"

    desired_follow_up: InquiryWaitingFollowUpTarget | None = None
    recommended_due_at: str | None = None
    follow_up_type: str | None = None
    action_formation_eligible = False

    if not waiting_required:
        cancel_follow_up_ids.extend(follow_up.follow_up_id for follow_up in active_follow_ups)
    else:
        episode_key = _episode_key(snapshot, relevant_questions, current_follow_up=current_follow_up)
        if current_follow_up is not None and _should_advance_follow_up(
            current_follow_up,
            current_dt=current_dt,
            policy=policy,
        ):
            cancel_follow_up_ids.append(current_follow_up.follow_up_id)
            sequence_number = current_follow_up.sequence_number + 1
            due_dt = _next_follow_up_due_at(current_follow_up, current_dt=current_dt, policy=policy)
            attempt_count = 0
            status = FOLLOW_UP_STATUS_ESCALATED if escalation_required else FOLLOW_UP_STATUS_SCHEDULED
        elif current_follow_up is not None:
            sequence_number = current_follow_up.sequence_number
            due_dt = current_dt if escalation_required else (_parse_timestamp(current_follow_up.due_at) or current_dt)
            attempt_count = current_follow_up.attempt_count
            status = FOLLOW_UP_STATUS_ESCALATED if escalation_required else current_follow_up.status
        else:
            sequence_number = 1
            due_dt = current_dt if escalation_required else current_dt + timedelta(days=policy.cold_follow_up_delay_days)
            attempt_count = 0
            status = FOLLOW_UP_STATUS_ESCALATED if escalation_required else FOLLOW_UP_STATUS_SCHEDULED

        follow_up_type = (
            ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM
            if escalation_required
            else ACTION_TYPE_REQUEST_CLIENT_INFORMATION
        )
        recommended_due_at = _format_timestamp(due_dt)
        semantic_identity_key = _follow_up_identity(episode_key, sequence_number)
        context_payload = _context_payload(
            snapshot,
            relevant_questions=relevant_questions,
            episode_key=episode_key,
            sequence_number=sequence_number,
            lead_posture=lead_posture,
            event_proximity=event_proximity,
        )
        desired_follow_up = InquiryWaitingFollowUpTarget(
            semantic_identity_key=semantic_identity_key,
            sequence_number=sequence_number,
            due_at=recommended_due_at,
            status=status,
            urgency_level=FOLLOW_UP_URGENCY_HIGH if escalation_required else FOLLOW_UP_URGENCY_MEDIUM,
            next_action_type=follow_up_type,
            context_payload=context_payload,
            waiting_for_role="client",
            waiting_for_reference=snapshot.rental_case.primary_contact_ref,
            attempt_count=attempt_count,
        )
        action_formation_eligible = escalation_required or due_dt <= current_dt

    reason_codes = (FOLLOW_UP_REASON_INQUIRY_MISSING_INFORMATION,) if waiting_required else ()
    fingerprint = _hash_material(
        {
            "rental_case_id": snapshot.rental_case.rental_case_id,
            "case_revision": snapshot.rental_case.case_revision,
            "waiting_required": waiting_required,
            "open_question_ids": open_question_ids,
            "required_field_codes": required_field_codes,
            "cancel_follow_up_ids": tuple(sorted(set(cancel_follow_up_ids))),
            "desired_follow_up": None
            if desired_follow_up is None
            else {
                "semantic_identity_key": desired_follow_up.semantic_identity_key,
                "sequence_number": desired_follow_up.sequence_number,
                "due_at": desired_follow_up.due_at,
                "status": desired_follow_up.status,
                "next_action_type": desired_follow_up.next_action_type,
            },
        }
    )
    return InquiryWaitingPlan(
        rental_case_id=snapshot.rental_case.rental_case_id,
        evaluated_case_revision=snapshot.rental_case.case_revision,
        waiting_required=waiting_required,
        reason_codes=reason_codes,
        open_question_ids=open_question_ids,
        required_field_codes=required_field_codes,
        lead_posture=lead_posture,
        event_proximity=event_proximity,
        recommended_follow_up_due_at=recommended_due_at,
        follow_up_type=follow_up_type,
        escalation_required=escalation_required,
        action_formation_eligible=action_formation_eligible,
        cancel_follow_up_ids=tuple(dict.fromkeys(cancel_follow_up_ids)),
        desired_follow_up=desired_follow_up,
        plan_fingerprint=fingerprint,
    )


def apply_inquiry_waiting_plan(
    repository: WorkflowOrchestrationRepositoryProtocol,
    plan: InquiryWaitingPlan,
    *,
    actor_reference: str,
    actor_type: str | None,
    now: Callable[[], str] = _utc_now,
) -> InquiryWaitingCommitResult:
    snapshot = repository.load_case_snapshot(plan.rental_case_id)
    if snapshot is None:
        return InquiryWaitingCommitResult(
            rental_case_id=plan.rental_case_id,
            case_revision_before=plan.evaluated_case_revision,
            case_revision_after=plan.evaluated_case_revision,
            plan=plan,
            failure_codes=(INQUIRY_WAITING_FAILURE_CASE_NOT_FOUND,),
        )
    if snapshot.rental_case.case_revision != plan.evaluated_case_revision:
        return InquiryWaitingCommitResult(
            rental_case_id=plan.rental_case_id,
            case_revision_before=snapshot.rental_case.case_revision,
            case_revision_after=snapshot.rental_case.case_revision,
            plan=plan,
            failure_codes=(INQUIRY_WAITING_FAILURE_STALE_CASE_REVISION,),
        )

    timestamp = now()
    created_follow_up_ids: list[int] = []
    updated_follow_up_ids: list[int] = []
    cancelled_follow_up_ids: list[int] = []
    audit_event_ids: list[int] = []
    failure_codes: list[str] = []

    for follow_up_id in plan.cancel_follow_up_ids:
        current_snapshot = repository.load_case_snapshot(plan.rental_case_id)
        current_follow_up = None if current_snapshot is None else current_snapshot.find_follow_up(follow_up_id)
        if current_follow_up is None or current_follow_up.status in TERMINAL_FOLLOW_UP_STATUSES:
            continue
        update_result = repository.commit_follow_up_status_update(
            FollowUpStatusUpdateRequest(
                rental_case_id=plan.rental_case_id,
                follow_up_id=follow_up_id,
                actor_reference=actor_reference,
                actor_type=actor_type,
                target_status=FOLLOW_UP_STATUS_CANCELLED,
                expected_current_status=current_follow_up.status,
                attempt_count_delta=0,
                occurred_at=timestamp,
                completed_at=timestamp,
            )
        )
        audit_event_ids.extend(update_result.audit_event_ids)
        if update_result.failure_codes:
            failure_codes.extend(update_result.failure_codes)
            continue
        cancelled_follow_up_ids.append(follow_up_id)

    if plan.desired_follow_up is not None:
        current_snapshot = repository.load_case_snapshot(plan.rental_case_id)
        existing_follow_up = (
            None
            if current_snapshot is None
            else current_snapshot.find_active_follow_up_by_semantic_identity(plan.desired_follow_up.semantic_identity_key)
        )
        persisted = repository.upsert_follow_up(
            FollowUp(
                follow_up_id=1 if existing_follow_up is None else existing_follow_up.follow_up_id,
                rental_case_id=plan.rental_case_id,
                reason_code=FOLLOW_UP_REASON_INQUIRY_MISSING_INFORMATION,
                due_at=plan.desired_follow_up.due_at,
                urgency_level=plan.desired_follow_up.urgency_level,
                attempt_count=plan.desired_follow_up.attempt_count,
                status=plan.desired_follow_up.status,
                semantic_identity_key=plan.desired_follow_up.semantic_identity_key,
                sequence_number=plan.desired_follow_up.sequence_number,
                waiting_for_role=plan.desired_follow_up.waiting_for_role,
                waiting_for_reference=plan.desired_follow_up.waiting_for_reference,
                cadence_policy_code=plan.desired_follow_up.cadence_policy_code,
                next_action_type=plan.desired_follow_up.next_action_type,
                context_payload=plan.desired_follow_up.context_payload,
                created_at=timestamp if existing_follow_up is None else existing_follow_up.created_at,
                updated_at=timestamp,
                completed_at=None if plan.desired_follow_up.status != FOLLOW_UP_STATUS_CANCELLED else timestamp,
            )
        )
        event_type_code = (
            "inquiry_follow_up_escalated"
            if persisted.status == FOLLOW_UP_STATUS_ESCALATED
            else "inquiry_follow_up_scheduled"
        )
        event = repository.create_workflow_event(
            rental_case_id=plan.rental_case_id,
            event_type_code=event_type_code,
            source_type="inquiry_waiting_runtime",
            source_reference=persisted.semantic_identity_key,
            actor_type=actor_type,
            actor_reference=actor_reference,
            occurred_at=timestamp,
            structured_payload={
                "follow_up_id": persisted.follow_up_id,
                "sequence_number": persisted.sequence_number,
                "due_at": persisted.due_at,
                "open_question_ids": plan.open_question_ids,
                "required_field_codes": plan.required_field_codes,
                "plan_fingerprint": plan.plan_fingerprint,
            },
            event_identity_key=f"inquiry_waiting:follow_up:{persisted.semantic_identity_key}:{plan.plan_fingerprint}",
        )
        audit_event_ids.append(event.workflow_event_id)
        if existing_follow_up is None:
            created_follow_up_ids.append(persisted.follow_up_id)
        else:
            updated_follow_up_ids.append(persisted.follow_up_id)

    reconciliation = reconcile_workflow_orchestration(
        repository,
        rental_case_id=plan.rental_case_id,
        actor_reference=actor_reference,
        actor_type=actor_type or "system",
        now=lambda: timestamp,
    )
    audit_event_ids.extend(reconciliation.audit_event_ids)
    failure_codes.extend(reconciliation.failure_codes)

    final_snapshot = repository.load_case_snapshot(plan.rental_case_id)
    final_revision = plan.evaluated_case_revision if final_snapshot is None else final_snapshot.rental_case.case_revision
    return InquiryWaitingCommitResult(
        rental_case_id=plan.rental_case_id,
        case_revision_before=plan.evaluated_case_revision,
        case_revision_after=final_revision,
        plan=plan,
        created_follow_up_ids=tuple(created_follow_up_ids),
        updated_follow_up_ids=tuple(updated_follow_up_ids),
        cancelled_follow_up_ids=tuple(cancelled_follow_up_ids),
        created_action_ids=reconciliation.created_action_ids,
        superseded_action_ids=reconciliation.superseded_action_ids,
        audit_event_ids=tuple(audit_event_ids),
        failure_codes=tuple(failure_codes),
    )


def _empty_plan(rental_case_id: int, *, evaluated_case_revision: int = 0) -> InquiryWaitingPlan:
    return InquiryWaitingPlan(
        rental_case_id=rental_case_id,
        evaluated_case_revision=evaluated_case_revision,
        waiting_required=False,
        reason_codes=(),
        open_question_ids=(),
        required_field_codes=(),
        lead_posture="cold_inquiry",
        event_proximity="unscheduled",
        recommended_follow_up_due_at=None,
        follow_up_type=None,
        escalation_required=False,
        action_formation_eligible=False,
        plan_fingerprint=_hash_material({"rental_case_id": rental_case_id, "evaluated_case_revision": evaluated_case_revision}),
    )


def _relevant_inquiry_questions(snapshot: WorkflowOrchestrationCaseSnapshot) -> list[Any]:
    return sorted(
        [
            question
            for question in snapshot.open_questions
            if question.status in {OPEN_QUESTION_STATUS_OPEN, OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION}
            and (question.requested_from_role or "").startswith("client")
            and question.question_type in INQUIRY_QUESTION_TYPES
        ],
        key=lambda question: question.open_question_id,
    )


def _active_inquiry_follow_ups(snapshot: WorkflowOrchestrationCaseSnapshot) -> list[FollowUp]:
    return sorted(
        [
            follow_up
            for follow_up in snapshot.follow_ups
            if follow_up.reason_code == FOLLOW_UP_REASON_INQUIRY_MISSING_INFORMATION
            and follow_up.status not in TERMINAL_FOLLOW_UP_STATUSES
        ],
        key=lambda follow_up: (follow_up.sequence_number, follow_up.follow_up_id),
    )


def _event_proximity(active_event_start: str | None, current_dt: datetime, policy: InquiryFollowUpPolicy) -> str:
    event_dt = _parse_timestamp(active_event_start)
    if event_dt is None:
        return "unscheduled"
    if event_dt <= current_dt + timedelta(days=policy.urgent_event_threshold_days):
        return "urgent"
    return "scheduled"


def _episode_key(
    snapshot: WorkflowOrchestrationCaseSnapshot,
    relevant_questions: tuple[Any, ...],
    *,
    current_follow_up: FollowUp | None,
) -> str:
    if current_follow_up is not None:
        payload = current_follow_up.context_payload if isinstance(current_follow_up.context_payload, dict) else {}
        existing_episode_key = payload.get("episode_key")
        if isinstance(existing_episode_key, str) and existing_episode_key.strip():
            return existing_episode_key
    first_created_at = None
    if relevant_questions:
        first_created_at = min(
            (question.created_at for question in relevant_questions if getattr(question, "created_at", None)),
            default=None,
        )
    return f"inquiry_episode:{_hash_material({'case': snapshot.rental_case.rental_case_id, 'started_at': first_created_at, 'question_ids': [question.open_question_id for question in relevant_questions]})}"


def _follow_up_identity(episode_key: str, sequence_number: int) -> str:
    return f"inquiry_follow_up:{_hash_material({'episode_key': episode_key, 'sequence_number': sequence_number})}"


def _context_payload(
    snapshot: WorkflowOrchestrationCaseSnapshot,
    *,
    relevant_questions: tuple[Any, ...],
    episode_key: str,
    sequence_number: int,
    lead_posture: str,
    event_proximity: str,
) -> dict[str, Any]:
    required_field_codes = [
        QUESTION_TYPE_TO_FIELD_CODE.get(question.question_type, question.question_type)
        for question in relevant_questions
    ]
    unique_field_codes = list(dict.fromkeys(required_field_codes))
    field_labels = [FIELD_CODE_LABELS.get(field_code, field_code.replace("_", " ").title()) for field_code in unique_field_codes]
    return {
        "episode_key": episode_key,
        "sequence_number": sequence_number,
        "open_question_ids": [question.open_question_id for question in relevant_questions],
        "required_field_codes": unique_field_codes,
        "question_types": [question.question_type for question in relevant_questions],
        "question_labels": field_labels,
        "question_texts": [question.human_question_text for question in relevant_questions],
        "intended_recipient_role": "client",
        "recipient_reference": snapshot.rental_case.primary_contact_ref,
        "purpose": "request_missing_information",
        "reason": _reason_text(field_labels),
        "lead_posture": lead_posture,
        "event_proximity": event_proximity,
    }


def _reason_text(field_labels: list[str]) -> str:
    if not field_labels:
        return "Core inquiry information remains unresolved."
    if len(field_labels) == 1:
        return f"Client information is still missing for {field_labels[0].lower()}."
    return "Client information is still missing for: " + ", ".join(field_labels) + "."


def _should_advance_follow_up(
    follow_up: FollowUp,
    *,
    current_dt: datetime,
    policy: InquiryFollowUpPolicy,
) -> bool:
    if follow_up.sequence_number >= policy.max_cold_follow_ups:
        return False
    due_dt = _parse_timestamp(follow_up.due_at)
    if due_dt is None:
        return False
    return current_dt >= due_dt + timedelta(days=policy.cold_follow_up_delay_days)


def _next_follow_up_due_at(
    follow_up: FollowUp,
    *,
    current_dt: datetime,
    policy: InquiryFollowUpPolicy,
) -> datetime:
    due_dt = _parse_timestamp(follow_up.due_at)
    if due_dt is None:
        return current_dt + timedelta(days=policy.cold_follow_up_delay_days)
    return due_dt + timedelta(days=policy.cold_follow_up_delay_days)
