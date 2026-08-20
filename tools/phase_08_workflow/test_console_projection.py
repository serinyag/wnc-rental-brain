from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .contracts import (
    APPROVAL_REQUEST_STATUS_OPEN,
    APPROVAL_REQUEST_STATUS_SUPERSEDED,
    ARTIFACT_FRESHNESS_CURRENT,
    ARTIFACT_FRESHNESS_STALE,
    ARTIFACT_TYPE_PROPOSAL,
    BLOCKER_STATUS_OPEN,
    CASE_DECISION_STATUS_ACTIVE,
    CASE_DECISION_STATUS_PENDING_APPROVAL,
    CASE_DECISION_STATUS_PROPOSED,
    CASE_DECISION_STATUS_SUPERSEDED,
    FOLLOW_UP_STATUS_CANCELLED,
    FOLLOW_UP_STATUS_COMPLETED,
    OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION,
    OPEN_QUESTION_STATUS_OPEN,
    PROPOSED_CHANGE_STATUS_ACCEPTED,
    PROPOSED_CHANGE_STATUS_PROPOSED,
    PROPOSED_CHANGE_STATUS_SUPERSEDED,
    PROPOSED_CHANGE_STATUS_UNDER_REVIEW,
    REQUIREMENT_STATUS_IN_PROGRESS,
    REQUIREMENT_STATUS_REQUIRED,
    REQUIREMENT_STATUS_UNRESOLVED,
    RESCHEDULE_STATUS_AWAITING_CLIENT_CONFIRMATION,
    RESCHEDULE_STATUS_CONFIRMED,
    RESCHEDULE_STATUS_EVALUATING,
    RESCHEDULE_STATUS_OFFERED,
    RESCHEDULE_STATUS_PROPOSED,
    RESCHEDULE_STATUS_SUPERSEDED,
    WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
    WORKFLOW_ACTION_STATUS_EXECUTING,
    WORKFLOW_ACTION_STATUS_PROPOSED,
    WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
    WORKFLOW_ACTION_STATUS_SUPERSEDED,
)
from .observation_contracts import RentalCaseFact
from .observation_registry import get_field_definition
from .orchestration_repository import WorkflowOrchestrationCaseSnapshot


DISPLAY_STATE_CURRENT = "current"
DISPLAY_STATE_PROPOSED = "proposed"
DISPLAY_STATE_UNRESOLVED = "unresolved"
DISPLAY_STATE_BLOCKED = "blocked"
DISPLAY_STATE_STALE = "stale"
DISPLAY_STATE_REFERENCE = "reference"
DISPLAY_STATE_NONE = "none"

UNKNOWN_VALUE = "Unknown"
NONE_VALUE = "None"
NOT_PROVIDED_VALUE = "Not provided"
NOT_ESTABLISHED_VALUE = "Not established"
NOT_YET_CONFIRMED_VALUE = "Not yet confirmed"
NOT_YET_EVALUATED_VALUE = "Not yet evaluated"
PENDING_VALUE = "Pending"

ACTION_CURRENT_STATUSES = frozenset(
    {
        WORKFLOW_ACTION_STATUS_PROPOSED,
        WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
        WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
        WORKFLOW_ACTION_STATUS_EXECUTING,
    }
)
RESCHEDULE_ACTIVE_STATUSES = frozenset(
    {
        RESCHEDULE_STATUS_PROPOSED,
        RESCHEDULE_STATUS_EVALUATING,
        RESCHEDULE_STATUS_OFFERED,
        RESCHEDULE_STATUS_AWAITING_CLIENT_CONFIRMATION,
    }
)
SPECIFIC_RENTAL_TYPE_LABELS = {
    "studio_space": "Studio Space",
    "entire_venue": "Entire Venue",
}


@dataclass(frozen=True)
class TestConsoleCaseMetadata:
    label: str | None = None
    client_label: str | None = None
    contact_email: str | None = None
    event_reference: str | None = None
    created_by: str | None = None
    created_at: str | None = None


@dataclass(frozen=True)
class ProjectionItem:
    label: str
    value: str
    state: str = DISPLAY_STATE_CURRENT
    detail: str | None = None
    source: str | None = None

    def __str__(self) -> str:
        return f"{self.label}: {self.value}"


@dataclass(frozen=True)
class WorkingProposalProjection:
    rental_snapshot: tuple[ProjectionItem, ...]
    commercial_snapshot: tuple[ProjectionItem, ...]
    feasibility_snapshot: tuple[ProjectionItem, ...]
    missing_client_information: tuple[ProjectionItem, ...]
    requirements: tuple[ProjectionItem, ...]
    blockers: tuple[ProjectionItem, ...]
    approvals: tuple[ProjectionItem, ...]
    operations: tuple[ProjectionItem, ...]
    changes: tuple[ProjectionItem, ...]
    communication: tuple[ProjectionItem, ...]
    next_actions: tuple[ProjectionItem, ...]
    proposal_freshness: tuple[ProjectionItem, ...]
    warnings: tuple[ProjectionItem, ...] = ()


@dataclass(frozen=True)
class ObservedFieldCandidate:
    field_code: str
    display_label: str
    value_payload: Any
    observed_at: str
    observation_status: str
    source_record_type: str | None = None
    source_actor_reference: str | None = None
    source_excerpt: str | None = None
    disposition_code: str | None = None
    reason_codes: tuple[str, ...] = ()
    stale_observation: bool = False
    linked_entity_reference: str | None = None


@dataclass(frozen=True)
class LatestCommunicationContext:
    occurred_at: str | None = None
    source_label: str | None = None
    sender: str | None = None
    subject: str | None = None


@dataclass(frozen=True)
class BookingFeeRuleContext:
    rule_code: str
    rental_type_code: str
    rental_type_name: str
    duration_minutes: int
    fee_ex_vat: float
    currency_code: str
    vat_rate: float | None
    waiver_allowed: bool
    waiver_authority: str | None
    source_state: str
    source_detail: str
    source_codes: tuple[str, ...] = ()


def build_working_proposal_projection(
    snapshot: WorkflowOrchestrationCaseSnapshot,
    *,
    metadata: TestConsoleCaseMetadata,
    observed_field_candidates: tuple[ObservedFieldCandidate, ...] = (),
    latest_communication: LatestCommunicationContext | None = None,
    booking_fee_context: BookingFeeRuleContext | None = None,
    additional_warnings: tuple[str, ...] = (),
) -> WorkingProposalProjection:
    observed_by_field = _observed_candidates_by_field(observed_field_candidates)
    return WorkingProposalProjection(
        rental_snapshot=_build_rental_snapshot(snapshot, metadata, observed_by_field),
        commercial_snapshot=_build_commercial_snapshot(snapshot, booking_fee_context),
        feasibility_snapshot=_build_feasibility_snapshot(snapshot),
        missing_client_information=_build_missing_information(snapshot),
        requirements=_build_requirement_lines(snapshot),
        blockers=_build_blocker_lines(snapshot),
        approvals=_build_approval_lines(snapshot, booking_fee_context),
        operations=_build_operations_snapshot(snapshot, observed_by_field),
        changes=_build_change_lines(snapshot, observed_by_field, booking_fee_context),
        communication=_build_communication_lines(snapshot, latest_communication=latest_communication),
        next_actions=_build_next_action_lines(snapshot, booking_fee_context),
        proposal_freshness=_build_proposal_freshness(snapshot),
        warnings=_build_warning_lines(snapshot, additional_warnings),
    )


def build_human_work_preview(snapshot: WorkflowOrchestrationCaseSnapshot) -> tuple[str, ...]:
    lines: list[str] = []
    for blocker in snapshot.blockers:
        if blocker.status != BLOCKER_STATUS_OPEN:
            continue
        lines.append(f"Resolve blocker: {blocker.resolution_condition_text}")
    for question in snapshot.open_questions:
        if question.status not in {OPEN_QUESTION_STATUS_OPEN, OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION}:
            continue
        lines.append(f"Resolve question: {question.human_question_text}")
    for requirement in snapshot.requirements:
        if requirement.status not in {REQUIREMENT_STATUS_REQUIRED, REQUIREMENT_STATUS_IN_PROGRESS, REQUIREMENT_STATUS_UNRESOLVED}:
            continue
        lines.append(f"Requirement follow-up: {humanize_code(requirement.requirement_type)}")
    for approval in snapshot.approval_requests:
        if approval.status != APPROVAL_REQUEST_STATUS_OPEN:
            continue
        lines.append(f"Approval needed: {approval.reason_text}")
    for action in snapshot.workflow_actions:
        if action.status not in ACTION_CURRENT_STATUSES:
            continue
        summary = action.structured_payload.get("summary") or _action_label(action)
        lines.append(f"Workflow action: {summary} [{humanize_code(action.status)}]")
    for follow_up in snapshot.follow_ups:
        if follow_up.status in {FOLLOW_UP_STATUS_COMPLETED, FOLLOW_UP_STATUS_CANCELLED}:
            continue
        lines.append(f"Follow-up: {humanize_code(follow_up.reason_code)} [{humanize_code(follow_up.status)}]")
    return tuple(lines) if lines else ("No structured human work is currently queued.",)


def infer_asana_master_task_reference(snapshot: WorkflowOrchestrationCaseSnapshot) -> str | None:
    for artifact in snapshot.artifacts:
        if artifact.external_reference and artifact.external_reference.startswith("asana:"):
            return artifact.external_reference
        if artifact.artifact_type == "task_surface_projection" and artifact.storage_reference and artifact.storage_reference.startswith("asana:"):
            return artifact.storage_reference
    for attempt in reversed(snapshot.execution_attempts):
        if attempt.external_reference and attempt.external_reference.startswith("asana:"):
            return attempt.external_reference
    return None


def humanize_code(value: str | None) -> str:
    if not value:
        return UNKNOWN_VALUE
    return value.replace("_", " ").replace("-", " ").title()


def summarize_test_metadata(metadata: TestConsoleCaseMetadata) -> tuple[str, ...]:
    return tuple(
        line
        for line in (
            f"Label: {metadata.label}" if metadata.label else None,
            f"Client / company: {metadata.client_label}" if metadata.client_label else None,
            f"Test contact email: {metadata.contact_email}" if metadata.contact_email else None,
            f"Event reference: {metadata.event_reference}" if metadata.event_reference else None,
            f"Created by: {metadata.created_by}" if metadata.created_by else None,
        )
        if line is not None
    )


def _build_rental_snapshot(
    snapshot: WorkflowOrchestrationCaseSnapshot,
    metadata: TestConsoleCaseMetadata,
    observed_by_field: dict[str, ObservedFieldCandidate],
) -> tuple[ProjectionItem, ...]:
    rental_type_label = _current_rental_type_label(snapshot.rental_case.rental_type_code)
    requested_space_label = _requested_space_label(snapshot.rental_case.rental_type_code)
    requested_space_candidate = observed_by_field.get("requested_rental_scope")
    items: list[ProjectionItem] = [
        _item(
            "Client / company",
            metadata.client_label or snapshot.rental_case.client_account_ref or UNKNOWN_VALUE,
            state=DISPLAY_STATE_CURRENT if (metadata.client_label or snapshot.rental_case.client_account_ref) else DISPLAY_STATE_UNRESOLVED,
        ),
        _item(
            "Working scope label",
            metadata.label or snapshot.rental_case.service_level_or_type or UNKNOWN_VALUE,
            state=DISPLAY_STATE_CURRENT if (metadata.label or snapshot.rental_case.service_level_or_type) else DISPLAY_STATE_UNRESOLVED,
        ),
        _item(
            "Rental type",
            rental_type_label or NOT_ESTABLISHED_VALUE,
            state=DISPLAY_STATE_CURRENT if rental_type_label else DISPLAY_STATE_UNRESOLVED,
        ),
        _item(
            "Requested spaces",
            requested_space_label or NOT_ESTABLISHED_VALUE,
            state=DISPLAY_STATE_CURRENT if requested_space_label else DISPLAY_STATE_UNRESOLVED,
        ),
        _item(
            "Lifecycle status",
            humanize_code(snapshot.rental_case.lifecycle_state),
            state=DISPLAY_STATE_CURRENT,
        ),
    ]
    if metadata.event_reference:
        items.append(
            _item(
                "Inquiry reference",
                metadata.event_reference,
                state=DISPLAY_STATE_REFERENCE,
            )
        )
    if requested_space_candidate is not None:
        items.append(
            _item(
                "Observed requested space",
                _render_value(requested_space_candidate.value_payload, field_code="requested_rental_scope"),
                state=_candidate_state(requested_space_candidate),
                source=_candidate_source(requested_space_candidate),
            )
        )

    current_start = snapshot.rental_case.active_event_start
    current_end = snapshot.rental_case.active_event_end
    active_window_candidate = observed_by_field.get("active_event_window")
    active_reschedule = _latest_reschedule(snapshot, include_confirmed=False)

    if current_start:
        items.append(_item("Event date", _format_date(current_start), state=DISPLAY_STATE_CURRENT))
        items.append(_item("Event time", _format_window(current_start, current_end), state=DISPLAY_STATE_CURRENT))
    else:
        unresolved_value = NOT_YET_CONFIRMED_VALUE if (active_reschedule or active_window_candidate) else NOT_PROVIDED_VALUE
        items.append(_item("Event date", unresolved_value, state=DISPLAY_STATE_UNRESOLVED))
        items.append(_item("Event time", unresolved_value, state=DISPLAY_STATE_UNRESOLVED))

    if active_reschedule is not None:
        requested_start = active_reschedule.requested_date_payload.get("active_event_start")
        requested_end = active_reschedule.requested_date_payload.get("active_event_end")
        items.append(
            _item(
                "Proposed event date",
                _format_date(requested_start),
                state=DISPLAY_STATE_PROPOSED,
                detail=f"Reschedule status: {humanize_code(active_reschedule.status)}.",
                source=f"reschedule_request:{active_reschedule.reschedule_request_id}",
            )
        )
        items.append(
            _item(
                "Proposed event time",
                _format_window(requested_start, requested_end),
                state=DISPLAY_STATE_PROPOSED,
                source=f"reschedule_request:{active_reschedule.reschedule_request_id}",
            )
        )
    elif active_window_candidate is not None:
        candidate_payload = active_window_candidate.value_payload if isinstance(active_window_candidate.value_payload, dict) else {}
        items.append(
            _item(
                "Observed requested date",
                _format_date(candidate_payload.get("active_event_start")),
                state=_candidate_state(active_window_candidate),
                source=_candidate_source(active_window_candidate),
            )
        )
        items.append(
            _item(
                "Observed requested time",
                _format_window(candidate_payload.get("active_event_start"), candidate_payload.get("active_event_end")),
                state=_candidate_state(active_window_candidate),
                source=_candidate_source(active_window_candidate),
            )
        )

    guest_fact = snapshot.find_rental_case_fact("guest_count")
    guest_candidate = observed_by_field.get("guest_count")
    if guest_fact is not None:
        items.append(_item("Guest count", _render_fact_payload(guest_fact), state=DISPLAY_STATE_CURRENT))
        if guest_candidate is not None:
            items.append(
                _item(
                    "Observed guest count",
                    _render_value(guest_candidate.value_payload, field_code="guest_count"),
                    state=_candidate_state(guest_candidate),
                    source=_candidate_source(guest_candidate),
                )
            )
    else:
        guest_value = NOT_YET_CONFIRMED_VALUE if guest_candidate is not None else NOT_PROVIDED_VALUE
        items.append(_item("Guest count", guest_value, state=DISPLAY_STATE_UNRESOLVED))
        if guest_candidate is not None:
            items.append(
                _item(
                    "Observed guest count",
                    _render_value(guest_candidate.value_payload, field_code="guest_count"),
                    state=_candidate_state(guest_candidate),
                    source=_candidate_source(guest_candidate),
                )
            )

    event_type_fact = snapshot.find_rental_case_fact("event_type")
    event_type_candidate = observed_by_field.get("event_type")
    if event_type_fact is not None:
        items.append(_item("Event type", _render_fact_payload(event_type_fact), state=DISPLAY_STATE_CURRENT))
        if event_type_candidate is not None:
            items.append(
                _item(
                    "Observed event type",
                    _render_value(event_type_candidate.value_payload, field_code="event_type"),
                    state=_candidate_state(event_type_candidate),
                    source=_candidate_source(event_type_candidate),
                )
            )
    else:
        event_type_value = NOT_YET_CONFIRMED_VALUE if event_type_candidate is not None else NOT_ESTABLISHED_VALUE
        items.append(_item("Event type", event_type_value, state=DISPLAY_STATE_UNRESOLVED))
        if event_type_candidate is not None:
            items.append(
                _item(
                    "Observed event type",
                    _render_value(event_type_candidate.value_payload, field_code="event_type"),
                    state=_candidate_state(event_type_candidate),
                    source=_candidate_source(event_type_candidate),
                )
            )
    return tuple(items)


def _build_commercial_snapshot(
    snapshot: WorkflowOrchestrationCaseSnapshot,
    booking_fee_context: BookingFeeRuleContext | None,
) -> tuple[ProjectionItem, ...]:
    items: list[ProjectionItem] = []
    baseline_line = _booking_fee_baseline_line(booking_fee_context)
    if baseline_line is not None:
        items.append(baseline_line)
        if booking_fee_context is not None and booking_fee_context.vat_rate is not None:
            items.append(
                _item(
                    "VAT",
                    _format_percent(booking_fee_context.vat_rate),
                    state=DISPLAY_STATE_REFERENCE,
                    detail=booking_fee_context.source_detail,
                    source=_source_code_text(booking_fee_context.source_codes),
                )
            )
    else:
        items.append(
            _item(
                "Booking fee baseline",
                NOT_ESTABLISHED_VALUE,
                state=DISPLAY_STATE_UNRESOLVED,
                detail="Current booking-fee authority cannot be established from the current structured schedule scope.",
            )
        )
        items.append(_item("VAT", NOT_ESTABLISHED_VALUE, state=DISPLAY_STATE_UNRESOLVED))

    active_decisions = [decision for decision in snapshot.case_decisions if decision.status == CASE_DECISION_STATUS_ACTIVE]
    pending_decisions = [
        decision
        for decision in snapshot.case_decisions
        if decision.status in {CASE_DECISION_STATUS_PROPOSED, CASE_DECISION_STATUS_PENDING_APPROVAL}
    ]

    if active_decisions:
        for decision in active_decisions:
            items.append(
                _item(
                    "Case-specific exception",
                    _decision_effective_value(decision, booking_fee_context=booking_fee_context),
                    state=DISPLAY_STATE_CURRENT,
                    detail=f"{decision.scope_description}. Authority basis: {humanize_code(decision.authority_basis)}.",
                    source=_decision_source(decision),
                )
            )
    elif pending_decisions:
        for decision in pending_decisions:
            items.append(
                _item(
                    "Case-specific exception",
                    PENDING_VALUE,
                    state=DISPLAY_STATE_PROPOSED,
                    detail=_decision_pending_detail(decision, booking_fee_context=booking_fee_context),
                    source=_decision_source(decision),
                )
            )
    else:
        items.append(_item("Case-specific exceptions", NONE_VALUE, state=DISPLAY_STATE_NONE))

    effective_booking_fee = _effective_booking_fee_line(snapshot, booking_fee_context)
    if effective_booking_fee is not None:
        items.append(effective_booking_fee)

    unresolved_commercial_changes = [
        change
        for change in snapshot.proposed_changes
        if change.domain_code == "commercial"
        and change.status in {PROPOSED_CHANGE_STATUS_PROPOSED, PROPOSED_CHANGE_STATUS_UNDER_REVIEW}
    ]
    items.append(
        _item(
            "Unresolved commercial items",
            str(len(unresolved_commercial_changes)),
            state=DISPLAY_STATE_PROPOSED if unresolved_commercial_changes else DISPLAY_STATE_NONE,
        )
    )
    return tuple(items)


def _build_feasibility_snapshot(snapshot: WorkflowOrchestrationCaseSnapshot) -> tuple[ProjectionItem, ...]:
    open_questions = [
        question
        for question in snapshot.open_questions
        if question.status in {OPEN_QUESTION_STATUS_OPEN, OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION}
    ]
    confirmation_blockers = [
        blocker
        for blocker in snapshot.blockers
        if blocker.status == BLOCKER_STATUS_OPEN
        and blocker.blocker_type in {"confirmation_required", "current_authority_missing"}
    ]
    confirmation_required = bool(open_questions or confirmation_blockers)
    items = [
        _item(
            "Feasibility as requested",
            "Requires confirmation" if confirmation_blockers else NOT_YET_EVALUATED_VALUE,
            state=DISPLAY_STATE_UNRESOLVED,
        ),
        _item("Supported alternative", NOT_ESTABLISHED_VALUE, state=DISPLAY_STATE_UNRESOLVED),
        _item(
            "Confirmation still required",
            "Yes" if confirmation_required else "No",
            state=DISPLAY_STATE_UNRESOLVED if confirmation_required else DISPLAY_STATE_NONE,
        ),
    ]
    open_readiness_blockers = [blocker for blocker in snapshot.blockers if blocker.status == BLOCKER_STATUS_OPEN]
    items.append(
        _item(
            "Hard constraint",
            open_readiness_blockers[0].resolution_condition_text if open_readiness_blockers else NONE_VALUE,
            state=DISPLAY_STATE_BLOCKED if open_readiness_blockers else DISPLAY_STATE_NONE,
            source=_blocker_reference(open_readiness_blockers[0]) if open_readiness_blockers else None,
        )
    )
    return tuple(items)


def _build_missing_information(snapshot: WorkflowOrchestrationCaseSnapshot) -> tuple[ProjectionItem, ...]:
    items = [
        _item(
            question.human_question_text,
            humanize_code(question.status),
            state=DISPLAY_STATE_BLOCKED if question.blocking_scope != "none" else DISPLAY_STATE_UNRESOLVED,
            detail=_question_detail(question),
            source=question.source_reference,
        )
        for question in snapshot.open_questions
        if question.status in {OPEN_QUESTION_STATUS_OPEN, OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION}
    ]
    if items:
        return tuple(items)
    return (_item("Outstanding client information", NONE_VALUE, state=DISPLAY_STATE_NONE),)


def _build_requirement_lines(snapshot: WorkflowOrchestrationCaseSnapshot) -> tuple[ProjectionItem, ...]:
    items = [
        _item(
            _field_label(requirement.requirement_type),
            humanize_code(requirement.status),
            state=DISPLAY_STATE_BLOCKED if requirement.blocking_scope != "none" else DISPLAY_STATE_CURRENT,
            detail=_requirement_detail(requirement),
            source=requirement.evidence_reference,
        )
        for requirement in snapshot.requirements
        if requirement.status in {REQUIREMENT_STATUS_REQUIRED, REQUIREMENT_STATUS_IN_PROGRESS, REQUIREMENT_STATUS_UNRESOLVED}
    ]
    if items:
        return tuple(items)
    return (_item("Outstanding requirements", NONE_VALUE, state=DISPLAY_STATE_NONE),)


def _build_blocker_lines(snapshot: WorkflowOrchestrationCaseSnapshot) -> tuple[ProjectionItem, ...]:
    items = [
        _item(
            humanize_code(blocker.blocker_type),
            humanize_code(blocker.severity),
            state=DISPLAY_STATE_BLOCKED,
            detail=blocker.resolution_condition_text,
            source=_blocker_reference(blocker),
        )
        for blocker in snapshot.blockers
        if blocker.status == BLOCKER_STATUS_OPEN
    ]
    if items:
        return tuple(items)
    return (_item("Current blockers", NONE_VALUE, state=DISPLAY_STATE_NONE),)


def _build_approval_lines(
    snapshot: WorkflowOrchestrationCaseSnapshot,
    booking_fee_context: BookingFeeRuleContext | None,
) -> tuple[ProjectionItem, ...]:
    items = []
    for approval in snapshot.approval_requests:
        if approval.status != APPROVAL_REQUEST_STATUS_OPEN:
            continue
        label = _approval_label(snapshot, approval)
        detail = _approval_detail(snapshot, approval, booking_fee_context)
        source = approval.target_entity_reference or (str(approval.target_entity_id) if approval.target_entity_id is not None else None)
        items.append(
            _item(
                label,
                humanize_code(approval.status),
                state=DISPLAY_STATE_BLOCKED,
                detail=detail,
                source=source,
            )
        )
    if items:
        return tuple(items)
    return (_item("Pending approvals", NONE_VALUE, state=DISPLAY_STATE_NONE),)


def _build_operations_snapshot(
    snapshot: WorkflowOrchestrationCaseSnapshot,
    observed_by_field: dict[str, ObservedFieldCandidate],
) -> tuple[ProjectionItem, ...]:
    items: list[ProjectionItem] = []
    for field_code in (
        "catering_arrangement",
        "facilitator_arrangement",
        "technical_requirements",
        "supplier_details",
        "layout_requirements",
        "event_day_contact",
    ):
        fact = snapshot.find_rental_case_fact(field_code)
        if fact is not None:
            items.append(
                _item(
                    _field_label(field_code),
                    _render_fact_payload(fact),
                    state=DISPLAY_STATE_CURRENT,
                    source=fact.source_reference,
                )
            )
            continue
        candidate = observed_by_field.get(field_code)
        if candidate is None:
            continue
        items.append(
            _item(
                _field_label(field_code),
                _render_value(candidate.value_payload, field_code=field_code),
                state=_candidate_state(candidate),
                detail="Observed candidate; not yet promoted into governed current truth.",
                source=_candidate_source(candidate),
            )
        )
    if items:
        return tuple(items)
    return (_item("Current working scope", "No structured operational facts are established yet.", state=DISPLAY_STATE_NONE),)


def _build_change_lines(
    snapshot: WorkflowOrchestrationCaseSnapshot,
    observed_by_field: dict[str, ObservedFieldCandidate],
    booking_fee_context: BookingFeeRuleContext | None,
) -> tuple[ProjectionItem, ...]:
    items: list[ProjectionItem] = []
    for change in snapshot.proposed_changes:
        if change.status in {PROPOSED_CHANGE_STATUS_PROPOSED, PROPOSED_CHANGE_STATUS_UNDER_REVIEW}:
            items.append(
                _item(
                    _field_label(change.change_kind),
                    _render_value(change.proposed_value_payload, field_code=change.change_kind),
                    state=DISPLAY_STATE_PROPOSED,
                    detail=_proposed_change_detail(change),
                    source=change.source_reference,
                )
            )
        elif change.status == PROPOSED_CHANGE_STATUS_ACCEPTED:
            items.append(
                _item(
                    _field_label(change.change_kind),
                    _render_value(change.final_value_payload, field_code=change.change_kind),
                    state=DISPLAY_STATE_REFERENCE,
                    detail=_proposed_change_detail(change),
                    source=change.source_reference,
                )
            )
        elif change.status == PROPOSED_CHANGE_STATUS_SUPERSEDED:
            items.append(
                _item(
                    _field_label(change.change_kind),
                    _render_value(change.proposed_value_payload, field_code=change.change_kind),
                    state=DISPLAY_STATE_STALE,
                    detail=_proposed_change_detail(change),
                    source=change.source_reference,
                )
            )

    for request in snapshot.reschedule_requests:
        if request.status in RESCHEDULE_ACTIVE_STATUSES:
            items.append(
                _item(
                    "Reschedule request",
                    _format_schedule_payload(request.requested_date_payload),
                    state=DISPLAY_STATE_PROPOSED,
                    detail=(
                        f"Current active schedule: {_format_schedule_payload(request.current_active_date_snapshot)}. "
                        f"Status: {humanize_code(request.status)}."
                    ),
                    source=f"reschedule_request:{request.reschedule_request_id}",
                )
            )
        elif request.status == RESCHEDULE_STATUS_CONFIRMED:
            items.append(
                _item(
                    "Reschedule request",
                    _format_schedule_payload(request.requested_date_payload),
                    state=DISPLAY_STATE_REFERENCE,
                    detail=f"Confirmed at {request.confirmed_at or UNKNOWN_VALUE}.",
                    source=f"reschedule_request:{request.reschedule_request_id}",
                )
            )
        elif request.status == RESCHEDULE_STATUS_SUPERSEDED:
            items.append(
                _item(
                    "Reschedule request",
                    _format_schedule_payload(request.requested_date_payload),
                    state=DISPLAY_STATE_STALE,
                    detail="This request has been superseded.",
                    source=f"reschedule_request:{request.reschedule_request_id}",
                )
            )

    for decision in snapshot.case_decisions:
        if decision.status in {CASE_DECISION_STATUS_PROPOSED, CASE_DECISION_STATUS_PENDING_APPROVAL}:
            items.append(
                _item(
                    decision.scope_description,
                    humanize_code(decision.status),
                    state=DISPLAY_STATE_PROPOSED,
                    detail=_decision_pending_detail(decision, booking_fee_context=booking_fee_context),
                    source=_decision_source(decision),
                )
            )
        elif decision.status == CASE_DECISION_STATUS_SUPERSEDED:
            items.append(
                _item(
                    decision.scope_description,
                    humanize_code(decision.status),
                    state=DISPLAY_STATE_STALE,
                    detail=_decision_pending_detail(decision, booking_fee_context=booking_fee_context),
                    source=_decision_source(decision),
                )
            )
    if items:
        return tuple(items)
    return (_item("Proposed or pending changes", NONE_VALUE, state=DISPLAY_STATE_NONE),)


def _build_communication_lines(
    snapshot: WorkflowOrchestrationCaseSnapshot,
    *,
    latest_communication: LatestCommunicationContext | None,
) -> tuple[ProjectionItem, ...]:
    items: list[ProjectionItem] = []
    if latest_communication is not None and (
        latest_communication.sender or latest_communication.subject or latest_communication.occurred_at
    ):
        items.append(
            _item(
                "Last inbound communication",
                latest_communication.subject or "No subject",
                state=DISPLAY_STATE_REFERENCE,
                detail=(
                    f"From {latest_communication.sender or 'unknown sender'}"
                    f"{' via ' + latest_communication.source_label if latest_communication.source_label else ''}"
                    f"{' on ' + _format_timestamp(latest_communication.occurred_at) if latest_communication.occurred_at else ''}."
                ),
            )
        )

    communication_actions = [
        action
        for action in snapshot.workflow_actions
        if action.action_category == "communication" and action.status in ACTION_CURRENT_STATUSES
    ]
    if communication_actions:
        latest_action = communication_actions[-1]
        items.append(
            _item(
                "Latest outbound workflow action",
                _action_label(latest_action),
                state=_action_state(latest_action),
                detail=_action_context_detail(snapshot, latest_action, booking_fee_context=None),
                source=latest_action.reason_entity_reference or latest_action.target_scope_key,
            )
        )

    active_follow_ups = [
        follow_up
        for follow_up in snapshot.follow_ups
        if follow_up.status not in {FOLLOW_UP_STATUS_COMPLETED, FOLLOW_UP_STATUS_CANCELLED}
    ]
    for follow_up in active_follow_ups:
        sequence_number = getattr(follow_up, "sequence_number", 1)
        items.append(
            _item(
                f"Follow-up #{sequence_number}: {humanize_code(follow_up.reason_code)}",
                humanize_code(follow_up.status),
                state=DISPLAY_STATE_PROPOSED if follow_up.status == "scheduled" else DISPLAY_STATE_BLOCKED,
                detail=_follow_up_detail(follow_up),
                source=follow_up.waiting_for_reference or follow_up.waiting_for_role,
            )
        )
    if items:
        return tuple(items)
    return (_item("Communication state", "No communication or follow-up state is established yet.", state=DISPLAY_STATE_NONE),)


def _build_next_action_lines(
    snapshot: WorkflowOrchestrationCaseSnapshot,
    booking_fee_context: BookingFeeRuleContext | None,
) -> tuple[ProjectionItem, ...]:
    items = []
    for action in snapshot.workflow_actions:
        if action.status not in ACTION_CURRENT_STATUSES:
            continue
        items.append(
            _item(
                _action_label(action),
                humanize_code(action.status),
                state=_action_state(action),
                detail=_action_context_detail(snapshot, action, booking_fee_context),
                source=action.reason_entity_reference or action.target_scope_key,
            )
        )
    if items:
        return tuple(items)
    return (_item("Needs attention", "No current structured workflow actions require attention.", state=DISPLAY_STATE_NONE),)


def _build_proposal_freshness(snapshot: WorkflowOrchestrationCaseSnapshot) -> tuple[ProjectionItem, ...]:
    items = []
    for artifact in snapshot.artifacts:
        if artifact.artifact_type != ARTIFACT_TYPE_PROPOSAL:
            continue
        state = DISPLAY_STATE_CURRENT
        if artifact.freshness_status in {ARTIFACT_FRESHNESS_STALE, "refresh_required", "superseded"}:
            state = DISPLAY_STATE_STALE
        detail = f"Derived from case revision {artifact.derived_from_case_revision}."
        if snapshot.rental_case.case_revision != artifact.derived_from_case_revision:
            detail += f" Current case revision is {snapshot.rental_case.case_revision}."
        items.append(
            _item(
                "Proposal artifact",
                humanize_code(artifact.freshness_status),
                state=state,
                detail=detail,
                source=artifact.storage_reference or artifact.external_reference,
            )
        )
    if items:
        return tuple(items)
    return (_item("Proposal artifact", "Not yet established", state=DISPLAY_STATE_UNRESOLVED),)


def _build_warning_lines(
    snapshot: WorkflowOrchestrationCaseSnapshot,
    additional_warnings: tuple[str, ...],
) -> tuple[ProjectionItem, ...]:
    items: list[ProjectionItem] = []
    for projection in snapshot.reasoning_projections:
        if projection.authority_outcome_classification != "deterministic_current" or projection.unresolved_authority_codes:
            unresolved = ", ".join(projection.unresolved_authority_codes) or humanize_code(projection.authority_outcome_classification)
            items.append(
                _item(
                    "Current authority warning",
                    "Current authority insufficient" if projection.unresolved_authority_codes else humanize_code(projection.authority_outcome_classification),
                    state=DISPLAY_STATE_BLOCKED,
                    detail=unresolved,
                    source=projection.projection_identity_key,
                )
            )
        for warning_code in projection.warning_codes:
            items.append(
                _item(
                    "Reasoning warning",
                    humanize_code(warning_code),
                    state=DISPLAY_STATE_REFERENCE,
                    source=projection.projection_identity_key,
                )
            )
        for conflict_code in projection.conflict_codes:
            items.append(
                _item(
                    "Conflict warning",
                    humanize_code(conflict_code),
                    state=DISPLAY_STATE_BLOCKED,
                    source=projection.projection_identity_key,
                )
            )
        for contamination_code in projection.contamination_codes:
            items.append(
                _item(
                    "Contamination warning",
                    humanize_code(contamination_code),
                    state=DISPLAY_STATE_BLOCKED,
                    source=projection.projection_identity_key,
                )
            )
    for warning in additional_warnings:
        items.append(_item("Projection warning", warning, state=DISPLAY_STATE_REFERENCE))
    return tuple(items)


def _observed_candidates_by_field(candidates: tuple[ObservedFieldCandidate, ...]) -> dict[str, ObservedFieldCandidate]:
    latest: dict[str, ObservedFieldCandidate] = {}
    for candidate in sorted(candidates, key=lambda item: item.observed_at):
        latest[candidate.field_code] = candidate
    return latest


def _approval_label(snapshot: WorkflowOrchestrationCaseSnapshot, approval) -> str:
    reference = approval.target_entity_reference or ""
    parsed = _parse_reference(reference)
    if parsed and parsed[0] == "case_decision":
        decision = snapshot.find_case_decision(parsed[1])
        if decision is not None:
            return f"Approve {decision.scope_description}"
    return humanize_code(approval.approval_type)


def _approval_detail(
    snapshot: WorkflowOrchestrationCaseSnapshot,
    approval,
    booking_fee_context: BookingFeeRuleContext | None,
) -> str:
    parts = [approval.reason_text]
    reference = approval.target_entity_reference or ""
    parsed = _parse_reference(reference)
    if parsed and parsed[0] == "case_decision":
        decision = snapshot.find_case_decision(parsed[1])
        if decision is not None:
            parts.append(_decision_pending_detail(decision, booking_fee_context=booking_fee_context))
    return " ".join(part for part in parts if part)


def _decision_pending_detail(decision, booking_fee_context: BookingFeeRuleContext | None = None) -> str:
    parts = [f"Status: {humanize_code(decision.status)}.", f"Scope: {decision.scope_description}."]
    proposed_value = _render_value(decision.proposed_value_payload, field_code=decision.decision_type)
    if proposed_value != UNKNOWN_VALUE:
        parts.append(f"Proposed value: {proposed_value}.")
    if booking_fee_context is not None and decision.baseline_reference.startswith("phase4:booking_fee"):
        parts.append(f"Standard baseline remains {_format_money(booking_fee_context.fee_ex_vat, booking_fee_context.currency_code)} excl. VAT until approval.")
    return " ".join(parts)


def _decision_effective_value(decision, booking_fee_context: BookingFeeRuleContext | None = None) -> str:
    payload = decision.effective_value_payload
    if _is_booking_fee_decision(decision):
        amount = _booking_fee_payload_amount(payload)
        if amount == 0:
            return "Waived"
        if amount is not None:
            return _format_money(amount, _booking_fee_currency(payload, booking_fee_context))
    if isinstance(payload, dict) and payload.get("waived"):
        return "Waived"
    return _render_value(payload, field_code=decision.decision_type)


def _decision_source(decision) -> str | None:
    if decision.approval_request_id is not None:
        return f"approval_request:{decision.approval_request_id}"
    return decision.evidence_reference


def _effective_booking_fee_line(
    snapshot: WorkflowOrchestrationCaseSnapshot,
    booking_fee_context: BookingFeeRuleContext | None,
) -> ProjectionItem | None:
    active_decision = _active_booking_fee_decision(snapshot)
    if active_decision is not None:
        return _item(
            "Effective booking fee",
            _render_effective_booking_fee_value(active_decision.effective_value_payload, booking_fee_context),
            state=DISPLAY_STATE_CURRENT,
            detail="A case-specific approved exception is active for this RentalCase.",
            source=_decision_source(active_decision),
        )
    if booking_fee_context is not None:
        return _item(
            "Effective booking fee",
            f"{_format_money(booking_fee_context.fee_ex_vat, booking_fee_context.currency_code)} excl. VAT",
            state=DISPLAY_STATE_REFERENCE if booking_fee_context.source_state != DISPLAY_STATE_CURRENT else DISPLAY_STATE_CURRENT,
            detail=f"No approved case-specific booking-fee exception is active. {booking_fee_context.source_detail}",
            source=_source_code_text(booking_fee_context.source_codes),
        )
    return None


def _booking_fee_baseline_line(booking_fee_context: BookingFeeRuleContext | None) -> ProjectionItem | None:
    if booking_fee_context is None:
        return None
    return _item(
        "Booking fee baseline",
        f"{_format_money(booking_fee_context.fee_ex_vat, booking_fee_context.currency_code)} excl. VAT",
        state=DISPLAY_STATE_REFERENCE if booking_fee_context.source_state != DISPLAY_STATE_CURRENT else DISPLAY_STATE_CURRENT,
        detail=booking_fee_context.source_detail,
        source=_source_code_text(booking_fee_context.source_codes),
    )


def _is_booking_fee_decision(decision) -> bool:
    return decision.baseline_reference.startswith("phase4:booking_fee")


def _active_booking_fee_decision(snapshot: WorkflowOrchestrationCaseSnapshot):
    for decision in snapshot.case_decisions:
        if decision.status == CASE_DECISION_STATUS_ACTIVE and _is_booking_fee_decision(decision):
            return decision
    return None


def _booking_fee_payload_amount(payload: Any) -> float | None:
    if not isinstance(payload, dict):
        return None
    raw_amount = payload.get("booking_fee")
    if raw_amount is None:
        return None
    try:
        return float(raw_amount)
    except (TypeError, ValueError):
        return None


def _booking_fee_currency(payload: Any, booking_fee_context: BookingFeeRuleContext | None) -> str:
    if isinstance(payload, dict):
        currency = payload.get("currency")
        if isinstance(currency, str) and currency.strip():
            return currency.strip()
    if booking_fee_context is not None:
        return booking_fee_context.currency_code
    return "EUR"


def _render_effective_booking_fee_value(payload: Any, booking_fee_context: BookingFeeRuleContext | None) -> str:
    amount = _booking_fee_payload_amount(payload)
    if amount is not None:
        currency = booking_fee_context.currency_code if (amount == 0 and booking_fee_context is not None) else _booking_fee_currency(payload, booking_fee_context)
        return _format_money(amount, currency)
    if isinstance(payload, dict) and payload.get("waived"):
        currency = booking_fee_context.currency_code if booking_fee_context is not None else _booking_fee_currency(payload, booking_fee_context)
        return _format_money(0, currency)
    return _render_value(payload, field_code="booking_fee_override")


def _candidate_state(candidate: ObservedFieldCandidate) -> str:
    return DISPLAY_STATE_STALE if candidate.stale_observation else DISPLAY_STATE_PROPOSED


def _candidate_source(candidate: ObservedFieldCandidate) -> str | None:
    parts = [candidate.source_record_type, candidate.source_actor_reference]
    rendered = " / ".join(part for part in parts if part)
    return rendered or candidate.linked_entity_reference


def _action_label(action) -> str:
    return action.structured_payload.get("summary") or humanize_code(action.action_type)


def _action_state(action) -> str:
    if action.status == WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL:
        return DISPLAY_STATE_BLOCKED
    if action.status in {WORKFLOW_ACTION_STATUS_PROPOSED, WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE}:
        return DISPLAY_STATE_CURRENT
    if action.status == WORKFLOW_ACTION_STATUS_EXECUTING:
        return DISPLAY_STATE_REFERENCE
    return DISPLAY_STATE_STALE


def _action_context_detail(
    snapshot: WorkflowOrchestrationCaseSnapshot,
    action,
    booking_fee_context: BookingFeeRuleContext | None,
) -> str:
    parts = []
    reason = action.structured_payload.get("reason")
    if reason:
        parts.append(f"Why: {reason}")
    else:
        parts.append("Why: Not explicitly linked.")

    reference = action.reason_entity_reference
    parsed = _parse_reference(reference)
    if parsed and parsed[0] == "case_decision":
        decision = snapshot.find_case_decision(parsed[1])
        if decision is not None:
            parts.append(_decision_pending_detail(decision, booking_fee_context=booking_fee_context))
        related_approval = next(
            (
                approval
                for approval in snapshot.approval_requests
                if approval.status == APPROVAL_REQUEST_STATUS_OPEN and approval.target_entity_reference == reference
            ),
            None,
        )
        if related_approval is not None:
            parts.append(f"Related approval: {related_approval.approval_request_id} is open.")
        related_blocker = next(
            (
                blocker
                for blocker in snapshot.blockers
                if blocker.status == BLOCKER_STATUS_OPEN and blocker.blocked_subject_reference == reference
            ),
            None,
        )
        if related_blocker is not None:
            parts.append(f"Blocked by: {related_blocker.resolution_condition_text}")
    elif parsed and parsed[0] == "reschedule_request":
        request = next(
            (
                reschedule_request
                for reschedule_request in snapshot.reschedule_requests
                if reschedule_request.reschedule_request_id == parsed[1]
            ),
            None,
        )
        if request is not None:
            parts.append(
                f"Requested schedule: {_format_schedule_payload(request.requested_date_payload)} "
                f"[{humanize_code(request.status)}]."
            )
    if action.due_at:
        parts.append(f"Due: {_format_timestamp(action.due_at)}.")
    return " ".join(parts)


def _follow_up_detail(follow_up) -> str:
    detail = [
        f"Sequence: {getattr(follow_up, 'sequence_number', 1)}.",
        f"Due: {_format_timestamp(follow_up.due_at)}.",
        f"Urgency: {humanize_code(follow_up.urgency_level)}.",
    ]
    if follow_up.waiting_for_role or follow_up.waiting_for_reference:
        detail.append(f"Waiting for: {follow_up.waiting_for_reference or humanize_code(follow_up.waiting_for_role)}.")
    if follow_up.next_action_type:
        detail.append(f"Next action type: {humanize_code(follow_up.next_action_type)}.")
    if isinstance(getattr(follow_up, "context_payload", None), dict):
        question_labels = follow_up.context_payload.get("question_labels") or ()
        if question_labels:
            detail.append(f"Missing: {', '.join(str(label) for label in question_labels)}.")
    return " ".join(detail)


def _question_detail(question) -> str:
    parts = [f"Scope: {humanize_code(question.blocking_scope)}."]
    if question.requested_from_role:
        parts.append(f"Requested from: {humanize_code(question.requested_from_role)}.")
    if question.proposed_answer_payload is not None:
        parts.append(f"Candidate answer: {_render_value(question.proposed_answer_payload)}.")
    return " ".join(parts)


def _requirement_detail(requirement) -> str:
    parts = [f"Scope: {humanize_code(requirement.blocking_scope)}."]
    if requirement.owner_reference or requirement.owner_role:
        parts.append(f"Owner: {requirement.owner_reference or humanize_code(requirement.owner_role)}.")
    if requirement.due_at:
        parts.append(f"Due: {_format_timestamp(requirement.due_at)}.")
    return " ".join(parts)


def _proposed_change_detail(change) -> str:
    parts = [f"Status: {humanize_code(change.status)}."]
    if change.prior_value_payload is not None:
        parts.append(f"Current: {_render_value(change.prior_value_payload, field_code=change.change_kind)}.")
    parts.append(f"Proposed: {_render_value(change.proposed_value_payload, field_code=change.change_kind)}.")
    if change.impact_classification:
        parts.append(f"Impact: {humanize_code(change.impact_classification)}.")
    if change.review_posture:
        parts.append(f"Review posture: {humanize_code(change.review_posture)}.")
    if change.final_value_payload is not None:
        parts.append(f"Final value: {_render_value(change.final_value_payload, field_code=change.change_kind)}.")
    return " ".join(parts)


def _latest_reschedule(snapshot: WorkflowOrchestrationCaseSnapshot, *, include_confirmed: bool) -> Any | None:
    candidates = []
    for request in snapshot.reschedule_requests:
        if request.status in RESCHEDULE_ACTIVE_STATUSES:
            candidates.append(request)
        elif include_confirmed and request.status == RESCHEDULE_STATUS_CONFIRMED:
            candidates.append(request)
    if not candidates:
        return None
    return sorted(candidates, key=lambda request: request.created_at)[-1]


def _current_rental_type_label(rental_type_code: str | None) -> str | None:
    if rental_type_code is None:
        return None
    return SPECIFIC_RENTAL_TYPE_LABELS.get(rental_type_code)


def _requested_space_label(rental_type_code: str | None) -> str | None:
    return _current_rental_type_label(rental_type_code)


def _field_label(field_code: str) -> str:
    definition = get_field_definition(field_code)
    if definition is not None:
        return definition.display_label
    return humanize_code(field_code)


def _blocker_reference(blocker) -> str | None:
    return blocker.blocked_subject_reference or blocker.origin_entity_reference


def _parse_reference(reference: str | None) -> tuple[str, int] | None:
    if not reference or ":" not in reference:
        return None
    entity_type, raw_id = reference.split(":", 1)
    if not raw_id.isdigit():
        return None
    return entity_type, int(raw_id)


def _item(
    label: str,
    value: str,
    *,
    state: str,
    detail: str | None = None,
    source: str | None = None,
) -> ProjectionItem:
    return ProjectionItem(label=label, value=value, state=state, detail=detail, source=source)


def _render_fact_payload(fact: RentalCaseFact) -> str:
    return _render_value(fact.value_payload, field_code=fact.field_code)


def _render_value(value: Any, *, field_code: str | None = None) -> str:
    if value is None:
        return UNKNOWN_VALUE
    if field_code == "requested_rental_scope" and isinstance(value, str):
        return humanize_code(value)
    if field_code == "event_type" and isinstance(value, str):
        return humanize_code(value)
    if field_code == "event_day_contact" and isinstance(value, dict):
        name = value.get("name")
        phone = value.get("phone")
        if name and phone:
            return f"{name} ({phone})"
        if name:
            return str(name)
    if field_code == "layout_requirements" and isinstance(value, dict):
        parts = []
        layout_style = value.get("layout_style")
        if layout_style:
            parts.append(f"{humanize_code(layout_style)} layout")
        for key, item in value.items():
            if key == "layout_style":
                continue
            if item is True:
                parts.append(humanize_code(key))
            elif item not in {False, None, ""}:
                parts.append(f"{humanize_code(key)}={_render_value(item)}")
        return ", ".join(parts) or UNKNOWN_VALUE
    if field_code == "technical_requirements" and isinstance(value, list):
        return ", ".join(humanize_code(str(item)) for item in value) or UNKNOWN_VALUE
    if field_code == "catering_arrangement" and isinstance(value, str):
        return humanize_code(value)
    if field_code == "facilitator_arrangement" and isinstance(value, str):
        return humanize_code(value)
    if field_code == "booking_fee_override" and isinstance(value, dict):
        currency = value.get("currency")
        amount = value.get("booking_fee")
        reason = value.get("reason")
        parts = []
        if amount is not None and currency:
            parts.append(_format_money(float(amount), currency))
        elif amount is not None:
            parts.append(str(amount))
        if reason:
            parts.append(str(reason))
        return " | ".join(parts) or UNKNOWN_VALUE
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return _format_number(value)
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        rendered_items = [humanize_code(item) if isinstance(item, str) else _render_value(item) for item in value]
        return ", ".join(rendered_items) or UNKNOWN_VALUE
    if isinstance(value, dict):
        return ", ".join(f"{humanize_code(str(key))}={_render_value(item)}" for key, item in value.items()) or UNKNOWN_VALUE
    return str(value)


def _format_number(value: float) -> str:
    return str(int(value)) if value.is_integer() else f"{value:.2f}".rstrip("0").rstrip(".")


def _format_money(amount: float, currency_code: str) -> str:
    return f"{currency_code} {_format_number(amount)}"


def _format_percent(value: float) -> str:
    return f"{_format_number(value * 100)}%"


def _format_date(value: str | None) -> str:
    if value is None:
        return NOT_ESTABLISHED_VALUE
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return value


def _format_timestamp(value: str | None) -> str:
    if value is None:
        return UNKNOWN_VALUE
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return value


def _format_window(start: str | None, end: str | None) -> str:
    if start is None:
        return NOT_ESTABLISHED_VALUE
    try:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        if end is None:
            return start_dt.strftime("%H:%M")
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
        return f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
    except ValueError:
        return f"{start or UNKNOWN_VALUE} - {end or UNKNOWN_VALUE}"


def _format_schedule_payload(payload: dict[str, Any] | None) -> str:
    if not payload:
        return NOT_ESTABLISHED_VALUE
    start = payload.get("active_event_start")
    end = payload.get("active_event_end")
    date_text = _format_date(start)
    time_text = _format_window(start, end)
    if date_text == NOT_ESTABLISHED_VALUE and time_text == NOT_ESTABLISHED_VALUE:
        return NOT_ESTABLISHED_VALUE
    return f"{date_text} | {time_text}"


def _source_code_text(source_codes: tuple[str, ...]) -> str | None:
    return ", ".join(source_codes) if source_codes else None
