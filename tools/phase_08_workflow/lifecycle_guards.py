from __future__ import annotations

from typing import Any

from .contracts import (
    ACTION_TYPE_SEND_PROPOSAL_MESSAGE,
    APPROVAL_REQUEST_STATUS_OPEN,
    ARTIFACT_FRESHNESS_CURRENT,
    ARTIFACT_FRESHNESS_REFRESH_REQUIRED,
    ARTIFACT_FRESHNESS_STALE,
    ARTIFACT_TYPE_INTERNAL_EVENT_BRIEF,
    ARTIFACT_TYPE_PROPOSAL,
    ARTIFACT_TYPE_READINESS_SUMMARY,
    ARTIFACT_TYPE_STAFFING_PLAN,
    ARTIFACT_TYPE_SUPPLIER_PLAN,
    BLOCKER_STATUS_OPEN,
    BLOCKING_SCOPE_COMMERCIAL_SCOPE,
    BLOCKING_SCOPE_NONE,
    BLOCKING_SCOPE_READINESS,
    BLOCKING_SCOPE_TRANSITION,
    CASE_DECISION_STATUS_ACTIVE,
    CHANGE_IMPACT_FUNDAMENTAL,
    CHANGE_IMPACT_MATERIAL,
    FOLLOW_UP_STATUS_CANCELLED,
    OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION,
    OPEN_QUESTION_STATUS_OPEN,
    PROPOSED_CHANGE_STATUS_PROPOSED,
    PROPOSED_CHANGE_STATUS_UNDER_REVIEW,
    REQUIREMENT_STATUS_IN_PROGRESS,
    REQUIREMENT_STATUS_NOT_APPLICABLE,
    REQUIREMENT_STATUS_REQUIRED,
    REQUIREMENT_STATUS_SATISFIED,
    REQUIREMENT_STATUS_UNRESOLVED,
    REQUIREMENT_STATUS_WAIVED,
)
from .lifecycle_repository import LifecycleCaseSnapshot
from .lifecycle_types import (
    GuardResult,
    LIFECYCLE_FAILURE_APPROVAL_UNRESOLVED,
    LIFECYCLE_FAILURE_CLIENT_INTENT_MISSING,
    LIFECYCLE_FAILURE_CONFLICTING_ACTIVE_CASE_DECISION,
    LIFECYCLE_FAILURE_EVENT_COMPLETION_EVIDENCE_MISSING,
    LIFECYCLE_FAILURE_EVENT_START_EVIDENCE_MISSING,
    LIFECYCLE_FAILURE_GUARD_FAILED,
    LIFECYCLE_FAILURE_INVALID_RESUME_TARGET,
    LIFECYCLE_FAILURE_MATERIAL_CHANGE_UNRESOLVED,
    LIFECYCLE_FAILURE_MISSING_DORMANT_METADATA,
    LIFECYCLE_FAILURE_MISSING_PROPOSAL_ARTIFACT,
    LIFECYCLE_FAILURE_MISSING_TRANSITION_EVIDENCE,
    LIFECYCLE_FAILURE_OPEN_BLOCKER,
    LIFECYCLE_FAILURE_OPEN_QUESTION_BLOCKS_TRANSITION,
    LIFECYCLE_FAILURE_PROPOSAL_NOT_READY,
    LIFECYCLE_FAILURE_READINESS_FAILED,
    LIFECYCLE_FAILURE_UNSATISFIED_REQUIREMENT,
)


CLIENT_INTENT_EVENT_TYPES = frozenset(
    {
        "client_booking_intent_recorded",
        "client_proposal_accepted",
        "operator_booking_intent_recorded",
    }
)
EVENT_STARTED_EVENT_TYPES = frozenset({"event_started", "manual_event_start_recorded"})
EVENT_COMPLETED_EVENT_TYPES = frozenset({"event_completed", "manual_event_completion_recorded"})
PROPOSAL_EVIDENCE_EVENT_TYPES = frozenset({"proposal_sent", "proposal_pending_client_recorded"})
PROPOSAL_REWORK_EVENT_TYPES = frozenset({"proposal_revision_requested", "client_scope_change_recorded"})

UNRESOLVED_REQUIREMENT_STATUSES = frozenset(
    {
        REQUIREMENT_STATUS_REQUIRED,
        REQUIREMENT_STATUS_IN_PROGRESS,
        REQUIREMENT_STATUS_UNRESOLVED,
    }
)
RESOLVED_REQUIREMENT_STATUSES = frozenset(
    {
        REQUIREMENT_STATUS_NOT_APPLICABLE,
        REQUIREMENT_STATUS_SATISFIED,
        REQUIREMENT_STATUS_WAIVED,
    }
)
UNRESOLVED_QUESTION_STATUSES = frozenset({OPEN_QUESTION_STATUS_OPEN, OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION})
UNRESOLVED_CHANGE_STATUSES = frozenset({PROPOSED_CHANGE_STATUS_PROPOSED, PROPOSED_CHANGE_STATUS_UNDER_REVIEW})
MATERIAL_CHANGE_IMPACTS = frozenset({CHANGE_IMPACT_MATERIAL, CHANGE_IMPACT_FUNDAMENTAL})
READINESS_ARTIFACT_TYPES = frozenset(
    {
        ARTIFACT_TYPE_INTERNAL_EVENT_BRIEF,
        ARTIFACT_TYPE_READINESS_SUMMARY,
        ARTIFACT_TYPE_STAFFING_PLAN,
        ARTIFACT_TYPE_SUPPLIER_PLAN,
    }
)
PROPOSAL_RELEVANT_APPROVAL_TYPES = frozenset({"commercial_exception", "proposal_send_approval", "proposal_change_approval"})
READINESS_RELEVANT_APPROVAL_TYPES = frozenset({"readiness_exception", "compliance_review", "operational_exception"})


def evaluate_transition_guards(
    *,
    snapshot: LifecycleCaseSnapshot,
    target_state: str,
    transition_context: dict[str, Any] | None,
) -> tuple[GuardResult, ...]:
    context = transition_context or {}
    current_state = snapshot.rental_case.lifecycle_state
    guard_results: list[GuardResult] = [_guard_no_conflicting_active_case_decisions(snapshot)]

    if current_state == "dormant":
        if target_state == "closed_lost":
            return tuple(guard_results)
        guard_results.append(_guard_dormant_resume(snapshot, target_state))
        return tuple(guard_results)

    if target_state == "proposal_in_progress":
        if current_state == "proposal_pending_client":
            guard_results.append(_guard_reopen_proposal_work(snapshot))
        elif current_state == "confirmation_pending":
            guard_results.append(_guard_confirmation_rework(snapshot))
        else:
            guard_results.append(_guard_minimum_proposal_work_eligibility(snapshot))
    elif target_state == "proposal_pending_client":
        guard_results.extend(_guard_proposal_pending_client(snapshot))
    elif target_state == "confirmation_pending":
        guard_results.extend(_guard_confirmation_pending(snapshot))
    elif target_state == "confirmed_pre_event":
        if current_state == "event_ready":
            guard_results.append(_guard_event_ready_degradation(snapshot))
        else:
            guard_results.extend(_guard_confirmed_pre_event(snapshot))
    elif target_state == "event_ready":
        guard_results.extend(_guard_event_ready(snapshot))
    elif target_state == "event_in_progress":
        guard_results.append(_guard_event_started(snapshot))
    elif target_state == "close_out_in_progress":
        guard_results.append(_guard_event_completed(snapshot))
    elif target_state == "closed":
        guard_results.extend(_guard_close_out(snapshot))
    elif target_state == "dormant":
        guard_results.append(_guard_dormancy(snapshot, context))

    return tuple(guard_results)


def _guard_no_conflicting_active_case_decisions(snapshot: LifecycleCaseSnapshot) -> GuardResult:
    active_by_scope: dict[tuple[str, str], int] = {}
    for decision in snapshot.case_decisions:
        if decision.status != CASE_DECISION_STATUS_ACTIVE:
            continue
        scope = (decision.domain_code, decision.scope_key)
        active_by_scope[scope] = active_by_scope.get(scope, 0) + 1
    conflicts = [scope for scope, count in active_by_scope.items() if count > 1]
    if conflicts:
        return GuardResult(
            guard_code="no_conflicting_active_case_decisions",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_CONFLICTING_ACTIVE_CASE_DECISION,
            relevant_case_revision=snapshot.rental_case.case_revision,
            metadata={"conflicting_scopes": [f"{domain}:{scope}" for domain, scope in conflicts]},
        )
    return GuardResult(
        guard_code="no_conflicting_active_case_decisions",
        passed=True,
        relevant_case_revision=snapshot.rental_case.case_revision,
    )


def _guard_minimum_proposal_work_eligibility(snapshot: LifecycleCaseSnapshot) -> GuardResult:
    blocking_ids = tuple(
        blocker.blocker_id
        for blocker in snapshot.blockers
        if blocker.status == BLOCKER_STATUS_OPEN
        and blocker.blocked_subject_type == "transition"
        and _reference_targets_state(blocker.blocked_subject_reference, "proposal_in_progress")
    )
    if blocking_ids:
        return GuardResult(
            guard_code="minimum_proposal_work_eligibility",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_OPEN_BLOCKER,
            relevant_case_revision=snapshot.rental_case.case_revision,
            blocking_blocker_ids=blocking_ids,
        )
    if not (snapshot.rental_case.client_account_ref or snapshot.rental_case.primary_contact_ref):
        return GuardResult(
            guard_code="minimum_proposal_work_eligibility",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_GUARD_FAILED,
            relevant_case_revision=snapshot.rental_case.case_revision,
            metadata={"missing_fields": ["client_account_ref_or_primary_contact_ref"]},
        )
    return GuardResult(
        guard_code="minimum_proposal_work_eligibility",
        passed=True,
        relevant_case_revision=snapshot.rental_case.case_revision,
    )


def _guard_reopen_proposal_work(snapshot: LifecycleCaseSnapshot) -> GuardResult:
    relevant_change_ids = tuple(
        change.proposed_case_change_id
        for change in snapshot.proposed_changes
        if change.status in UNRESOLVED_CHANGE_STATUSES
    )
    relevant_event_ids = tuple(
        event.workflow_event_id
        for event in snapshot.workflow_events
        if event.event_type_code in PROPOSAL_REWORK_EVENT_TYPES
        and _payload_truthy(event.structured_payload, "rework_requested")
    )
    if not relevant_change_ids and not relevant_event_ids:
        return GuardResult(
            guard_code="proposal_rework_requested",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_MISSING_TRANSITION_EVIDENCE,
            relevant_case_revision=snapshot.rental_case.case_revision,
        )
    return GuardResult(
        guard_code="proposal_rework_requested",
        passed=True,
        relevant_case_revision=snapshot.rental_case.case_revision,
        blocking_proposed_change_ids=relevant_change_ids,
        evidence_event_ids=relevant_event_ids,
    )


def _guard_confirmation_rework(snapshot: LifecycleCaseSnapshot) -> GuardResult:
    material_change_ids = _material_change_ids(snapshot)
    if not material_change_ids:
        return GuardResult(
            guard_code="confirmation_rework_required",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_MATERIAL_CHANGE_UNRESOLVED,
            relevant_case_revision=snapshot.rental_case.case_revision,
        )
    return GuardResult(
        guard_code="confirmation_rework_required",
        passed=True,
        relevant_case_revision=snapshot.rental_case.case_revision,
        blocking_proposed_change_ids=material_change_ids,
    )


def _guard_proposal_pending_client(snapshot: LifecycleCaseSnapshot) -> tuple[GuardResult, ...]:
    return (
        _guard_transition_blockers(snapshot, "proposal_pending_client"),
        _guard_transition_open_questions(snapshot, "proposal_pending_client"),
        _guard_transition_requirements(snapshot, "proposal_pending_client"),
        _guard_relevant_approvals(snapshot, "proposal_pending_client"),
        _guard_material_changes(snapshot, "proposal_pending_client"),
        _guard_proposal_artifact_and_evidence(snapshot),
    )


def _guard_confirmation_pending(snapshot: LifecycleCaseSnapshot) -> tuple[GuardResult, ...]:
    return (
        _guard_transition_blockers(snapshot, "confirmation_pending"),
        _guard_transition_open_questions(snapshot, "confirmation_pending"),
        _guard_relevant_approvals(snapshot, "confirmation_pending"),
        _guard_material_changes(snapshot, "confirmation_pending"),
        _guard_client_intent(snapshot),
    )


def _guard_confirmed_pre_event(snapshot: LifecycleCaseSnapshot) -> tuple[GuardResult, ...]:
    return (
        _guard_transition_blockers(snapshot, "confirmed_pre_event"),
        _guard_confirmation_requirements(snapshot),
        _guard_relevant_approvals(snapshot, "confirmed_pre_event"),
        _guard_material_changes(snapshot, "confirmed_pre_event"),
    )


def _guard_event_ready(snapshot: LifecycleCaseSnapshot) -> tuple[GuardResult, ...]:
    return (
        _guard_readiness_blockers(snapshot),
        _guard_readiness_requirements(snapshot),
        _guard_readiness_questions(snapshot),
        _guard_relevant_approvals(snapshot, "event_ready"),
        _guard_material_changes(snapshot, "event_ready"),
        _guard_readiness_artifacts(snapshot),
    )


def _guard_event_ready_degradation(snapshot: LifecycleCaseSnapshot) -> GuardResult:
    readiness_results = _guard_event_ready(snapshot)
    readiness_passed = all(result.passed for result in readiness_results)
    if readiness_passed:
        return GuardResult(
            guard_code="event_ready_degradation_required",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_GUARD_FAILED,
            relevant_case_revision=snapshot.rental_case.case_revision,
            metadata={"reason": "readiness_still_holds"},
        )
    return GuardResult(
        guard_code="event_ready_degradation_required",
        passed=True,
        reason_code=LIFECYCLE_FAILURE_READINESS_FAILED,
        relevant_case_revision=snapshot.rental_case.case_revision,
        blocking_blocker_ids=_aggregate_ids(readiness_results, "blocking_blocker_ids"),
        blocking_requirement_ids=_aggregate_ids(readiness_results, "blocking_requirement_ids"),
        blocking_open_question_ids=_aggregate_ids(readiness_results, "blocking_open_question_ids"),
        blocking_approval_request_ids=_aggregate_ids(readiness_results, "blocking_approval_request_ids"),
        blocking_proposed_change_ids=_aggregate_ids(readiness_results, "blocking_proposed_change_ids"),
        evidence_event_ids=_aggregate_ids(readiness_results, "evidence_event_ids"),
    )


def _guard_event_started(snapshot: LifecycleCaseSnapshot) -> GuardResult:
    evidence_ids = tuple(
        event.workflow_event_id
        for event in snapshot.workflow_events
        if event.event_type_code in EVENT_STARTED_EVENT_TYPES and _payload_truthy(event.structured_payload, "started")
    )
    if not evidence_ids:
        return GuardResult(
            guard_code="event_started_evidence",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_EVENT_START_EVIDENCE_MISSING,
            relevant_case_revision=snapshot.rental_case.case_revision,
        )
    return GuardResult(
        guard_code="event_started_evidence",
        passed=True,
        relevant_case_revision=snapshot.rental_case.case_revision,
        evidence_event_ids=evidence_ids,
    )


def _guard_event_completed(snapshot: LifecycleCaseSnapshot) -> GuardResult:
    evidence_ids = tuple(
        event.workflow_event_id
        for event in snapshot.workflow_events
        if event.event_type_code in EVENT_COMPLETED_EVENT_TYPES and _payload_truthy(event.structured_payload, "completed")
    )
    if not evidence_ids:
        return GuardResult(
            guard_code="event_completed_evidence",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_EVENT_COMPLETION_EVIDENCE_MISSING,
            relevant_case_revision=snapshot.rental_case.case_revision,
        )
    return GuardResult(
        guard_code="event_completed_evidence",
        passed=True,
        relevant_case_revision=snapshot.rental_case.case_revision,
        evidence_event_ids=evidence_ids,
    )


def _guard_close_out(snapshot: LifecycleCaseSnapshot) -> tuple[GuardResult, ...]:
    return (
        _guard_transition_blockers(snapshot, "closed"),
        _guard_transition_requirements(snapshot, "closed"),
        _guard_relevant_approvals(snapshot, "closed"),
    )


def _guard_dormancy(snapshot: LifecycleCaseSnapshot, context: dict[str, Any]) -> GuardResult:
    resume_target_state = context.get("resume_target_state")
    dormant_reason_code = context.get("dormant_reason_code")
    if not resume_target_state or not dormant_reason_code:
        return GuardResult(
            guard_code="dormancy_metadata_present",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_MISSING_DORMANT_METADATA,
            relevant_case_revision=snapshot.rental_case.case_revision,
        )
    if resume_target_state not in {
        "inquiry_active",
        "proposal_in_progress",
        "proposal_pending_client",
        "confirmation_pending",
    }:
        return GuardResult(
            guard_code="dormancy_resume_target_valid",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_INVALID_RESUME_TARGET,
            relevant_case_revision=snapshot.rental_case.case_revision,
            metadata={"resume_target_state": resume_target_state},
        )
    return GuardResult(
        guard_code="dormancy_metadata_present",
        passed=True,
        relevant_case_revision=snapshot.rental_case.case_revision,
        metadata={"resume_target_state": resume_target_state},
    )


def _guard_dormant_resume(snapshot: LifecycleCaseSnapshot, target_state: str) -> GuardResult:
    resume_target = snapshot.rental_case.resume_target_state
    if not resume_target:
        return GuardResult(
            guard_code="dormant_resume_target_matches",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_INVALID_RESUME_TARGET,
            relevant_case_revision=snapshot.rental_case.case_revision,
        )
    if resume_target != target_state:
        return GuardResult(
            guard_code="dormant_resume_target_matches",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_INVALID_RESUME_TARGET,
            relevant_case_revision=snapshot.rental_case.case_revision,
            metadata={"resume_target_state": resume_target},
        )
    return GuardResult(
        guard_code="dormant_resume_target_matches",
        passed=True,
        relevant_case_revision=snapshot.rental_case.case_revision,
        metadata={"resume_target_state": resume_target},
    )


def _guard_transition_blockers(snapshot: LifecycleCaseSnapshot, target_state: str) -> GuardResult:
    blocking_ids = tuple(
        blocker.blocker_id
        for blocker in snapshot.blockers
        if blocker.status == BLOCKER_STATUS_OPEN and _blocker_applies_to_transition(blocker, target_state)
    )
    if blocking_ids:
        return GuardResult(
            guard_code=f"{target_state}_blockers_clear",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_OPEN_BLOCKER,
            relevant_case_revision=snapshot.rental_case.case_revision,
            blocking_blocker_ids=blocking_ids,
        )
    return GuardResult(
        guard_code=f"{target_state}_blockers_clear",
        passed=True,
        relevant_case_revision=snapshot.rental_case.case_revision,
    )


def _guard_transition_open_questions(snapshot: LifecycleCaseSnapshot, target_state: str) -> GuardResult:
    blocking_ids = tuple(
        question.open_question_id
        for question in snapshot.open_questions
        if question.status in UNRESOLVED_QUESTION_STATUSES and _question_scope_blocks_transition(question.blocking_scope, target_state)
    )
    if blocking_ids:
        return GuardResult(
            guard_code=f"{target_state}_questions_clear",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_OPEN_QUESTION_BLOCKS_TRANSITION,
            relevant_case_revision=snapshot.rental_case.case_revision,
            blocking_open_question_ids=blocking_ids,
        )
    return GuardResult(
        guard_code=f"{target_state}_questions_clear",
        passed=True,
        relevant_case_revision=snapshot.rental_case.case_revision,
    )


def _guard_transition_requirements(snapshot: LifecycleCaseSnapshot, target_state: str) -> GuardResult:
    blocking_ids = tuple(
        requirement.requirement_id
        for requirement in snapshot.requirements
        if requirement.status in UNRESOLVED_REQUIREMENT_STATUSES and _requirement_scope_blocks_transition(requirement.blocking_scope, target_state)
    )
    if blocking_ids:
        return GuardResult(
            guard_code=f"{target_state}_requirements_clear",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_UNSATISFIED_REQUIREMENT,
            relevant_case_revision=snapshot.rental_case.case_revision,
            blocking_requirement_ids=blocking_ids,
        )
    return GuardResult(
        guard_code=f"{target_state}_requirements_clear",
        passed=True,
        relevant_case_revision=snapshot.rental_case.case_revision,
    )


def _guard_relevant_approvals(snapshot: LifecycleCaseSnapshot, target_state: str) -> GuardResult:
    blocking_ids = tuple(
        approval.approval_request_id
        for approval in snapshot.approval_requests
        if approval.status == APPROVAL_REQUEST_STATUS_OPEN and _approval_applies_to_transition(snapshot, approval, target_state)
    )
    if blocking_ids:
        return GuardResult(
            guard_code=f"{target_state}_approvals_resolved",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_APPROVAL_UNRESOLVED,
            relevant_case_revision=snapshot.rental_case.case_revision,
            blocking_approval_request_ids=blocking_ids,
        )
    return GuardResult(
        guard_code=f"{target_state}_approvals_resolved",
        passed=True,
        relevant_case_revision=snapshot.rental_case.case_revision,
    )


def _guard_material_changes(snapshot: LifecycleCaseSnapshot, target_state: str) -> GuardResult:
    blocking_ids = tuple(
        change.proposed_case_change_id
        for change in snapshot.proposed_changes
        if change.status in UNRESOLVED_CHANGE_STATUSES
        and change.impact_classification in MATERIAL_CHANGE_IMPACTS
        and _change_applies_to_transition(change.review_posture, target_state)
    )
    if blocking_ids:
        return GuardResult(
            guard_code=f"{target_state}_material_changes_resolved",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_MATERIAL_CHANGE_UNRESOLVED,
            relevant_case_revision=snapshot.rental_case.case_revision,
            blocking_proposed_change_ids=blocking_ids,
        )
    return GuardResult(
        guard_code=f"{target_state}_material_changes_resolved",
        passed=True,
        relevant_case_revision=snapshot.rental_case.case_revision,
    )


def _guard_proposal_artifact_and_evidence(snapshot: LifecycleCaseSnapshot) -> GuardResult:
    proposal_artifact = _current_proposal_artifact(snapshot)
    if proposal_artifact is None:
        return GuardResult(
            guard_code="proposal_artifact_present",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_MISSING_PROPOSAL_ARTIFACT,
            relevant_case_revision=snapshot.rental_case.case_revision,
        )
    if proposal_artifact.freshness_status in {ARTIFACT_FRESHNESS_STALE, ARTIFACT_FRESHNESS_REFRESH_REQUIRED}:
        return GuardResult(
            guard_code="proposal_artifact_present",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_PROPOSAL_NOT_READY,
            relevant_case_revision=snapshot.rental_case.case_revision,
            metadata={"artifact_reference_id": proposal_artifact.artifact_reference_id, "freshness_status": proposal_artifact.freshness_status},
        )
    evidence_event_ids = tuple(
        event.workflow_event_id
        for event in snapshot.workflow_events
        if event.event_type_code in PROPOSAL_EVIDENCE_EVENT_TYPES and _payload_truthy(event.structured_payload, "proposal_dispatched")
    )
    action_based_evidence = any(
        action.action_type == ACTION_TYPE_SEND_PROPOSAL_MESSAGE and action.status == "succeeded"
        for action in snapshot.workflow_actions
    )
    if not evidence_event_ids and not action_based_evidence:
        return GuardResult(
            guard_code="proposal_dispatch_evidence",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_MISSING_TRANSITION_EVIDENCE,
            relevant_case_revision=snapshot.rental_case.case_revision,
            metadata={"artifact_reference_id": proposal_artifact.artifact_reference_id},
        )
    return GuardResult(
        guard_code="proposal_dispatch_evidence",
        passed=True,
        relevant_case_revision=snapshot.rental_case.case_revision,
        evidence_event_ids=evidence_event_ids,
        metadata={"artifact_reference_id": proposal_artifact.artifact_reference_id, "workflow_action_evidence": action_based_evidence},
    )


def _guard_client_intent(snapshot: LifecycleCaseSnapshot) -> GuardResult:
    evidence_ids = tuple(
        event.workflow_event_id
        for event in snapshot.workflow_events
        if event.event_type_code in CLIENT_INTENT_EVENT_TYPES and _payload_truthy(event.structured_payload, "intent_to_book")
    )
    if not evidence_ids:
        return GuardResult(
            guard_code="client_intent_evidence",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_CLIENT_INTENT_MISSING,
            relevant_case_revision=snapshot.rental_case.case_revision,
        )
    return GuardResult(
        guard_code="client_intent_evidence",
        passed=True,
        relevant_case_revision=snapshot.rental_case.case_revision,
        evidence_event_ids=evidence_ids,
    )


def _guard_confirmation_requirements(snapshot: LifecycleCaseSnapshot) -> GuardResult:
    blocking_ids = tuple(
        requirement.requirement_id
        for requirement in snapshot.requirements
        if requirement.status in UNRESOLVED_REQUIREMENT_STATUSES
        and requirement.blocking_scope in {BLOCKING_SCOPE_TRANSITION, BLOCKING_SCOPE_COMMERCIAL_SCOPE}
    )
    if blocking_ids:
        return GuardResult(
            guard_code="confirmation_requirements_satisfied",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_UNSATISFIED_REQUIREMENT,
            relevant_case_revision=snapshot.rental_case.case_revision,
            blocking_requirement_ids=blocking_ids,
        )
    return GuardResult(
        guard_code="confirmation_requirements_satisfied",
        passed=True,
        relevant_case_revision=snapshot.rental_case.case_revision,
    )


def _guard_readiness_blockers(snapshot: LifecycleCaseSnapshot) -> GuardResult:
    blocking_ids = tuple(
        blocker.blocker_id
        for blocker in snapshot.blockers
        if blocker.status == BLOCKER_STATUS_OPEN
        and (
            blocker.blocked_subject_type == "readiness"
            or _reference_targets_state(blocker.blocked_subject_reference, "event_ready")
        )
    )
    if blocking_ids:
        return GuardResult(
            guard_code="readiness_blockers_clear",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_OPEN_BLOCKER,
            relevant_case_revision=snapshot.rental_case.case_revision,
            blocking_blocker_ids=blocking_ids,
        )
    return GuardResult(
        guard_code="readiness_blockers_clear",
        passed=True,
        relevant_case_revision=snapshot.rental_case.case_revision,
    )


def _guard_readiness_requirements(snapshot: LifecycleCaseSnapshot) -> GuardResult:
    blocking_ids = tuple(
        requirement.requirement_id
        for requirement in snapshot.requirements
        if requirement.status in UNRESOLVED_REQUIREMENT_STATUSES
        and requirement.blocking_scope in {BLOCKING_SCOPE_READINESS, BLOCKING_SCOPE_TRANSITION}
    )
    if blocking_ids:
        return GuardResult(
            guard_code="readiness_requirements_satisfied",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_UNSATISFIED_REQUIREMENT,
            relevant_case_revision=snapshot.rental_case.case_revision,
            blocking_requirement_ids=blocking_ids,
        )
    return GuardResult(
        guard_code="readiness_requirements_satisfied",
        passed=True,
        relevant_case_revision=snapshot.rental_case.case_revision,
    )


def _guard_readiness_questions(snapshot: LifecycleCaseSnapshot) -> GuardResult:
    blocking_ids = tuple(
        question.open_question_id
        for question in snapshot.open_questions
        if question.status in UNRESOLVED_QUESTION_STATUSES
        and question.blocking_scope in {BLOCKING_SCOPE_READINESS, BLOCKING_SCOPE_TRANSITION}
    )
    if blocking_ids:
        return GuardResult(
            guard_code="readiness_questions_clear",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_OPEN_QUESTION_BLOCKS_TRANSITION,
            relevant_case_revision=snapshot.rental_case.case_revision,
            blocking_open_question_ids=blocking_ids,
        )
    return GuardResult(
        guard_code="readiness_questions_clear",
        passed=True,
        relevant_case_revision=snapshot.rental_case.case_revision,
    )


def _guard_readiness_artifacts(snapshot: LifecycleCaseSnapshot) -> GuardResult:
    stale_artifact_ids = tuple(
        artifact.artifact_reference_id
        for artifact in snapshot.artifacts
        if artifact.artifact_type in READINESS_ARTIFACT_TYPES
        and artifact.freshness_status in {ARTIFACT_FRESHNESS_STALE, ARTIFACT_FRESHNESS_REFRESH_REQUIRED}
    )
    if stale_artifact_ids:
        return GuardResult(
            guard_code="readiness_artifacts_current",
            passed=False,
            reason_code=LIFECYCLE_FAILURE_READINESS_FAILED,
            relevant_case_revision=snapshot.rental_case.case_revision,
            metadata={"stale_artifact_ids": stale_artifact_ids},
        )
    return GuardResult(
        guard_code="readiness_artifacts_current",
        passed=True,
        relevant_case_revision=snapshot.rental_case.case_revision,
    )


def _question_scope_blocks_transition(blocking_scope: str, target_state: str) -> bool:
    if blocking_scope == BLOCKING_SCOPE_NONE:
        return False
    if target_state == "event_ready":
        return blocking_scope in {BLOCKING_SCOPE_READINESS, BLOCKING_SCOPE_TRANSITION}
    if target_state in {"proposal_pending_client", "confirmation_pending", "confirmed_pre_event", "closed"}:
        return blocking_scope in {BLOCKING_SCOPE_TRANSITION, BLOCKING_SCOPE_COMMERCIAL_SCOPE}
    return blocking_scope == BLOCKING_SCOPE_TRANSITION


def _requirement_scope_blocks_transition(blocking_scope: str, target_state: str) -> bool:
    if blocking_scope == BLOCKING_SCOPE_NONE:
        return False
    if target_state == "event_ready":
        return blocking_scope in {BLOCKING_SCOPE_READINESS, BLOCKING_SCOPE_TRANSITION}
    if target_state in {"proposal_pending_client", "confirmation_pending", "confirmed_pre_event", "closed"}:
        return blocking_scope in {BLOCKING_SCOPE_TRANSITION, BLOCKING_SCOPE_COMMERCIAL_SCOPE}
    return blocking_scope == BLOCKING_SCOPE_TRANSITION


def _approval_applies_to_transition(snapshot: LifecycleCaseSnapshot, approval: ApprovalRequest, target_state: str) -> bool:
    if approval.target_entity_reference in {target_state, f"lifecycle:{target_state}"}:
        return True
    if approval.target_entity_reference is not None:
        return False
    if target_state == "proposal_pending_client" and approval.approval_type in PROPOSAL_RELEVANT_APPROVAL_TYPES:
        return True
    if target_state == "event_ready" and approval.approval_type in READINESS_RELEVANT_APPROVAL_TYPES:
        return True
    if approval.target_entity_type == "proposed_change" and approval.target_entity_id is not None:
        return approval.target_entity_id in {change.proposed_case_change_id for change in snapshot.proposed_changes if change.status in UNRESOLVED_CHANGE_STATUSES}
    if approval.target_entity_type == "case_decision" and approval.target_entity_id is not None:
        return approval.target_entity_id in {decision.case_decision_id for decision in snapshot.case_decisions}
    if approval.target_entity_type == "workflow_action" and approval.target_entity_id is not None:
        return approval.target_entity_id in {action.workflow_action_id for action in snapshot.workflow_actions}
    return False


def _change_applies_to_transition(review_posture: str | None, target_state: str) -> bool:
    if target_state in {"proposal_pending_client", "confirmation_pending", "confirmed_pre_event", "event_ready"}:
        return True
    if target_state == "proposal_in_progress":
        return review_posture is not None
    return False


def _blocker_applies_to_transition(blocker: Any, target_state: str) -> bool:
    if blocker.blocked_subject_type == "readiness":
        return target_state == "event_ready"
    if blocker.blocked_subject_type != "transition":
        return False
    return _reference_targets_state(blocker.blocked_subject_reference, target_state)


def _reference_targets_state(reference: str | None, target_state: str) -> bool:
    if reference is None:
        return False
    return reference in {target_state, f"lifecycle:{target_state}", "any_transition"}


def _payload_truthy(payload: dict[str, Any], key: str) -> bool:
    return isinstance(payload, dict) and payload.get(key) is True


def _current_proposal_artifact(snapshot: LifecycleCaseSnapshot):
    if snapshot.rental_case.current_proposal_artifact_id is not None:
        for artifact in snapshot.artifacts:
            if artifact.artifact_reference_id == snapshot.rental_case.current_proposal_artifact_id:
                return artifact
    for artifact in snapshot.artifacts:
        if artifact.artifact_type == ARTIFACT_TYPE_PROPOSAL and artifact.freshness_status == ARTIFACT_FRESHNESS_CURRENT:
            return artifact
    return None


def _material_change_ids(snapshot: LifecycleCaseSnapshot) -> tuple[int, ...]:
    return tuple(
        change.proposed_case_change_id
        for change in snapshot.proposed_changes
        if change.status in UNRESOLVED_CHANGE_STATUSES and change.impact_classification in MATERIAL_CHANGE_IMPACTS
    )


def _aggregate_ids(results: tuple[GuardResult, ...], field_name: str) -> tuple[int, ...]:
    ordered: list[int] = []
    seen: set[int] = set()
    for result in results:
        for value in getattr(result, field_name):
            if value not in seen:
                seen.add(value)
                ordered.append(value)
    return tuple(ordered)
