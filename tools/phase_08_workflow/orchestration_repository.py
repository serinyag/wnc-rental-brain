from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Protocol

from tools.phase_05_chunking.generate_pilot import run_supabase_query, sql_text

from .contracts import (
    APPROVAL_REQUEST_STATUS_CANCELLED,
    APPROVAL_REQUEST_STATUS_APPROVED,
    APPROVAL_REQUEST_STATUS_REJECTED,
    ARTIFACT_FRESHNESS_STALE,
    BLOCKER_STATUS_RESOLVED,
    CASE_DECISION_STATUS_ACTIVE,
    CASE_DECISION_STATUS_REJECTED,
    EXECUTION_ATTEMPT_STATUS_STARTED,
    EXECUTION_ATTEMPT_STATUS_SUCCEEDED,
    FOLLOW_UP_STATUS_CANCELLED,
    FOLLOW_UP_STATUS_COMPLETED,
    PROPOSED_CHANGE_STATUS_ACCEPTED,
    PROPOSED_CHANGE_STATUS_REJECTED,
    WORKFLOW_ACTION_STATUS_APPROVED,
    WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
    WORKFLOW_ACTION_STATUS_CANCELLED,
    WORKFLOW_ACTION_STATUS_EXECUTING,
    WORKFLOW_ACTION_STATUS_FAILED,
    WORKFLOW_ACTION_STATUS_PROPOSED,
    WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
    WORKFLOW_ACTION_STATUS_SUCCEEDED,
    WORKFLOW_ACTION_STATUS_SUPERSEDED,
    ApprovalRequest,
    ArtifactReference,
    Blocker,
    CaseDecision,
    ExecutionAttempt,
    FollowUp,
    Milestone,
    OpenQuestion,
    ProposedCaseChange,
    RentalCase,
    Requirement,
    RescheduleRequest,
    WorkflowAction,
    WorkflowEvent,
    WorkflowReasoningProjection,
)
from .lifecycle_repository import (
    SupabaseLifecycleRepository,
    _sql_bool,
    _sql_int,
    _sql_json,
    _sql_timestamptz,
    current_timestamp,
)
from .observation_contracts import RentalCaseFact
from .execution_types import (
    EXECUTION_FAILURE_ACTION_ALREADY_SUCCEEDED,
    EXECUTION_FAILURE_ACTION_NOT_FOUND,
    EXECUTION_FAILURE_ACTION_BLOCKED,
    EXECUTION_FAILURE_ACTION_CANCELLED,
    EXECUTION_FAILURE_ACTION_HUMAN_ONLY,
    EXECUTION_FAILURE_ACTION_NOT_DUE,
    EXECUTION_FAILURE_ACTION_NOT_EXECUTION_READY,
    EXECUTION_FAILURE_ACTION_STALE_REVISION,
    EXECUTION_FAILURE_ACTION_SUPERSEDED,
    EXECUTION_FAILURE_ACTION_ALREADY_EXECUTING,
    EXECUTION_FAILURE_ATTEMPT_NOT_FOUND,
    EXECUTION_FAILURE_CASE_NOT_FOUND,
    EXECUTION_FAILURE_EXECUTION_ALREADY_STARTED,
    EXECUTION_FAILURE_EXECUTION_COMPLETE_FAILED,
    EXECUTION_FAILURE_EXECUTION_START_FAILED,
    EXECUTION_FAILURE_EXTERNAL_REFERENCE_CONFLICT,
    EXECUTION_FAILURE_FOLLOW_UP_NOT_FOUND,
    EXECUTION_FAILURE_FOLLOW_UP_STATE_TRANSITION_INVALID,
    EXECUTION_FAILURE_STALE_CASE_REVISION,
    FollowUpStatusUpdateRequest,
    FollowUpStatusUpdateResult,
    WorkflowActionExecutionCompletionRequest,
    WorkflowActionExecutionRequest,
    WorkflowActionExecutionResult,
    WorkflowActionExecutionStartResult,
)
from .orchestration_types import (
    ApprovalDecisionInput,
    ApprovalDecisionResult,
    CaseDecisionActivationRequest,
    CaseDecisionActivationResult,
    ORCHESTRATION_DECISION_APPROVED,
    ORCHESTRATION_FAILURE_ACTION_BLOCKED,
    ORCHESTRATION_FAILURE_ACTION_STATE_TRANSITION_INVALID,
    ORCHESTRATION_FAILURE_APPROVAL_REQUIRED,
    ORCHESTRATION_FAILURE_APPROVAL_TARGET_INVALID,
    ORCHESTRATION_FAILURE_APPROVAL_TARGET_MISMATCH,
    ORCHESTRATION_FAILURE_CASE_DECISION_ACTIVATION_FAILED,
    ORCHESTRATION_FAILURE_CASE_DECISION_CONFLICT,
    ORCHESTRATION_FAILURE_CASE_DECISION_NOT_ACTIVATABLE,
    ORCHESTRATION_FAILURE_CASE_NOT_FOUND,
    ORCHESTRATION_FAILURE_INVALID_ENTITY_STATUS,
    ORCHESTRATION_FAILURE_PROPOSED_CHANGE_NOT_RESOLVABLE,
    ORCHESTRATION_FAILURE_PROPOSED_CHANGE_RESOLUTION_FAILED,
    ORCHESTRATION_FAILURE_STALE_CASE_REVISION,
    ProposedCaseChangeResolutionInput,
    ProposedCaseChangeResolutionResult,
    WorkflowActionApprovalResult,
)


@dataclass(frozen=True)
class WorkflowOrchestrationCaseSnapshot:
    rental_case: RentalCase
    rental_case_facts: tuple[RentalCaseFact, ...] = ()
    blockers: tuple[Blocker, ...] = ()
    requirements: tuple[Requirement, ...] = ()
    open_questions: tuple[OpenQuestion, ...] = ()
    approval_requests: tuple[ApprovalRequest, ...] = ()
    proposed_changes: tuple[ProposedCaseChange, ...] = ()
    reschedule_requests: tuple[RescheduleRequest, ...] = ()
    case_decisions: tuple[CaseDecision, ...] = ()
    workflow_actions: tuple[WorkflowAction, ...] = ()
    execution_attempts: tuple[ExecutionAttempt, ...] = ()
    follow_ups: tuple[FollowUp, ...] = ()
    milestones: tuple[Milestone, ...] = ()
    artifacts: tuple[ArtifactReference, ...] = ()
    reasoning_projections: tuple[WorkflowReasoningProjection, ...] = ()
    workflow_events: tuple[WorkflowEvent, ...] = ()

    def find_rental_case_fact(self, field_code: str) -> RentalCaseFact | None:
        for fact in self.rental_case_facts:
            if fact.field_code == field_code:
                return fact
        return None

    def find_case_decision(self, case_decision_id: int) -> CaseDecision | None:
        for decision in self.case_decisions:
            if decision.case_decision_id == case_decision_id:
                return decision
        return None

    def find_proposed_change(self, proposed_case_change_id: int) -> ProposedCaseChange | None:
        for change in self.proposed_changes:
            if change.proposed_case_change_id == proposed_case_change_id:
                return change
        return None

    def find_workflow_action(self, workflow_action_id: int) -> WorkflowAction | None:
        for action in self.workflow_actions:
            if action.workflow_action_id == workflow_action_id:
                return action
        return None

    def find_execution_attempt(self, execution_attempt_id: int) -> ExecutionAttempt | None:
        for attempt in self.execution_attempts:
            if attempt.execution_attempt_id == execution_attempt_id:
                return attempt
        return None

    def find_follow_up(self, follow_up_id: int) -> FollowUp | None:
        for follow_up in self.follow_ups:
            if follow_up.follow_up_id == follow_up_id:
                return follow_up
        return None

    def find_active_follow_up_by_semantic_identity(self, semantic_identity_key: str) -> FollowUp | None:
        for follow_up in self.follow_ups:
            if follow_up.semantic_identity_key != semantic_identity_key:
                continue
            if follow_up.status in {FOLLOW_UP_STATUS_COMPLETED, FOLLOW_UP_STATUS_CANCELLED}:
                continue
            return follow_up
        return None

    def find_approval_request(self, approval_request_id: int) -> ApprovalRequest | None:
        for request in self.approval_requests:
            if request.approval_request_id == approval_request_id:
                return request
        return None

    def find_open_blocker_by_semantic_key(self, semantic_issue_key: str) -> Blocker | None:
        for blocker in self.blockers:
            if blocker.status != "open":
                continue
            if blocker.resolution_reference == f"semantic:{semantic_issue_key}":
                return blocker
        return None

    def find_open_approval_by_semantic_key(self, semantic_approval_key: str) -> ApprovalRequest | None:
        for request in self.approval_requests:
            if request.status != "open":
                continue
            if request.required_approver_reference == f"semantic:{semantic_approval_key}":
                return request
        return None

    def find_active_action_by_idempotency_key(self, idempotency_key: str) -> WorkflowAction | None:
        for action in self.workflow_actions:
            if action.idempotency_key != idempotency_key:
                continue
            if action.status in {"succeeded", "failed", "cancelled", "superseded"}:
                continue
            return action
        return None


class WorkflowOrchestrationRepositoryProtocol(Protocol):
    def load_case_snapshot(self, rental_case_id: int) -> WorkflowOrchestrationCaseSnapshot | None: ...

    def list_execution_attempts(
        self,
        *,
        rental_case_id: int,
        workflow_action_id: int | None = None,
    ) -> tuple[ExecutionAttempt, ...]: ...

    def list_ready_to_execute_actions(
        self,
        *,
        rental_case_id: int | None = None,
    ) -> tuple[WorkflowAction, ...]: ...

    def list_follow_ups_for_evaluation(
        self,
        *,
        rental_case_id: int | None = None,
    ) -> tuple[FollowUp, ...]: ...

    def upsert_follow_up(self, follow_up: FollowUp) -> FollowUp: ...

    def create_workflow_event(
        self,
        *,
        rental_case_id: int,
        event_type_code: str,
        source_type: str,
        source_reference: str | None,
        actor_type: str | None,
        actor_reference: str,
        occurred_at: str,
        structured_payload: dict[str, Any],
        event_identity_key: str,
    ) -> WorkflowEvent: ...

    def create_blocker(self, blocker: Blocker) -> Blocker: ...

    def resolve_blocker(self, *, rental_case_id: int, blocker_id: int, resolved_at: str, resolution_reference: str | None) -> Blocker: ...

    def create_approval_request(self, approval_request: ApprovalRequest) -> ApprovalRequest: ...

    def cancel_approval_request(
        self,
        *,
        rental_case_id: int,
        approval_request_id: int,
        decided_at: str,
        decision_notes: str | None,
    ) -> ApprovalRequest: ...

    def decide_approval_request(
        self,
        *,
        rental_case_id: int,
        approval_request_id: int,
        status: str,
        decision_payload: Any,
        decided_at: str,
        decided_by_reference: str,
        decision_notes: str | None,
    ) -> ApprovalRequest: ...

    def create_workflow_action(self, workflow_action: WorkflowAction) -> WorkflowAction: ...

    def start_workflow_action_execution(
        self,
        request: WorkflowActionExecutionRequest,
    ) -> WorkflowActionExecutionStartResult: ...

    def complete_workflow_action_execution(
        self,
        request: WorkflowActionExecutionCompletionRequest,
    ) -> WorkflowActionExecutionResult: ...

    def commit_follow_up_status_update(
        self,
        request: FollowUpStatusUpdateRequest,
    ) -> FollowUpStatusUpdateResult: ...

    def supersede_workflow_action(
        self,
        *,
        rental_case_id: int,
        workflow_action_id: int,
        updated_at: str,
    ) -> WorkflowAction: ...

    def create_requirement(self, requirement: Requirement) -> Requirement: ...

    def activate_case_decision(
        self,
        *,
        rental_case_id: int,
        case_decision_id: int,
        approval_request_id: int | None,
        effective_value_payload: Any,
        effective_at: str,
        expected_case_revision: int,
    ) -> tuple[CaseDecision, RentalCase]: ...

    def reject_case_decision(
        self,
        *,
        rental_case_id: int,
        case_decision_id: int,
        updated_at: str,
    ) -> CaseDecision: ...

    def resolve_proposed_change(
        self,
        *,
        rental_case_id: int,
        proposed_case_change_id: int,
        status: str,
        final_value_payload: Any,
        accepted_at: str | None,
    ) -> ProposedCaseChange: ...

    def upsert_rental_case_fact(
        self,
        *,
        rental_case_id: int,
        field_code: str,
        domain_code: str,
        value_payload: Any,
        source_reference: str,
        established_case_revision: int,
        timestamp: str,
    ) -> RentalCaseFact: ...

    def update_rental_case_schedule(
        self,
        *,
        rental_case_id: int,
        expected_case_revision: int,
        active_event_start: str | None,
        active_event_end: str | None,
        updated_at: str,
    ) -> RentalCase: ...

    def increment_case_revision(
        self,
        *,
        rental_case_id: int,
        expected_case_revision: int,
        updated_at: str,
    ) -> RentalCase: ...

    def update_artifact_freshness(
        self,
        *,
        rental_case_id: int,
        artifact_reference_id: int,
        freshness_status: str,
        updated_at: str,
    ) -> ArtifactReference: ...

    def commit_case_decision_activation(
        self,
        request: CaseDecisionActivationRequest,
    ) -> CaseDecisionActivationResult: ...

    def apply_case_decision_approval(
        self,
        request: ApprovalDecisionInput,
    ) -> ApprovalDecisionResult: ...

    def apply_workflow_action_approval(
        self,
        request: ApprovalDecisionInput,
    ) -> WorkflowActionApprovalResult: ...

    def commit_proposed_case_change_resolution(
        self,
        request: ProposedCaseChangeResolutionInput,
    ) -> ProposedCaseChangeResolutionResult: ...


@dataclass
class InMemoryWorkflowOrchestrationRepository:
    rental_cases: dict[int, RentalCase]
    rental_case_facts: dict[int, list[RentalCaseFact]]
    blockers: dict[int, list[Blocker]]
    requirements: dict[int, list[Requirement]]
    open_questions: dict[int, list[OpenQuestion]]
    approval_requests: dict[int, list[ApprovalRequest]]
    proposed_changes: dict[int, list[ProposedCaseChange]]
    reschedule_requests: dict[int, list[RescheduleRequest]]
    case_decisions: dict[int, list[CaseDecision]]
    workflow_actions: dict[int, list[WorkflowAction]]
    execution_attempts: dict[int, list[ExecutionAttempt]] = field(default_factory=dict)
    follow_ups: dict[int, list[FollowUp]] = field(default_factory=dict)
    milestones: dict[int, list[Milestone]] = field(default_factory=dict)
    artifacts: dict[int, list[ArtifactReference]] = field(default_factory=dict)
    reasoning_projections: dict[int, list[WorkflowReasoningProjection]] = field(default_factory=dict)
    workflow_events: dict[int, list[WorkflowEvent]] = field(default_factory=dict)
    _rental_case_fact_id: int = 10_000
    _blocker_id: int = 20_000
    _requirement_id: int = 30_000
    _approval_request_id: int = 40_000
    _case_decision_id: int = 50_000
    _workflow_action_id: int = 60_000
    _workflow_event_id: int = 70_000
    _execution_attempt_id: int = 80_000
    _follow_up_id: int = 90_000

    def load_case_snapshot(self, rental_case_id: int) -> WorkflowOrchestrationCaseSnapshot | None:
        rental_case = self.rental_cases.get(rental_case_id)
        if rental_case is None:
            return None
        return WorkflowOrchestrationCaseSnapshot(
            rental_case=rental_case,
            rental_case_facts=tuple(self.rental_case_facts.get(rental_case_id, ())),
            blockers=tuple(self.blockers.get(rental_case_id, ())),
            requirements=tuple(self.requirements.get(rental_case_id, ())),
            open_questions=tuple(self.open_questions.get(rental_case_id, ())),
            approval_requests=tuple(self.approval_requests.get(rental_case_id, ())),
            proposed_changes=tuple(self.proposed_changes.get(rental_case_id, ())),
            reschedule_requests=tuple(self.reschedule_requests.get(rental_case_id, ())),
            case_decisions=tuple(self.case_decisions.get(rental_case_id, ())),
            workflow_actions=tuple(self.workflow_actions.get(rental_case_id, ())),
            execution_attempts=tuple(self.execution_attempts.get(rental_case_id, ())),
            follow_ups=tuple(self.follow_ups.get(rental_case_id, ())),
            milestones=tuple(self.milestones.get(rental_case_id, ())),
            artifacts=tuple(self.artifacts.get(rental_case_id, ())),
            reasoning_projections=tuple(self.reasoning_projections.get(rental_case_id, ())),
            workflow_events=tuple(self.workflow_events.get(rental_case_id, ())),
        )

    def list_ready_to_execute_actions(
        self,
        *,
        rental_case_id: int | None = None,
    ) -> tuple[WorkflowAction, ...]:
        if rental_case_id is not None:
            return tuple(
                action
                for action in self.workflow_actions.get(rental_case_id, ())
                if action.status == WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE
            )
        return tuple(
            action
            for actions in self.workflow_actions.values()
            for action in actions
            if action.status == WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE
        )

    def list_execution_attempts(
        self,
        *,
        rental_case_id: int,
        workflow_action_id: int | None = None,
    ) -> tuple[ExecutionAttempt, ...]:
        attempts = tuple(self.execution_attempts.get(rental_case_id, ()))
        if workflow_action_id is None:
            return attempts
        return tuple(
            attempt
            for attempt in attempts
            if attempt.workflow_action_id == workflow_action_id
        )

    def list_follow_ups_for_evaluation(
        self,
        *,
        rental_case_id: int | None = None,
    ) -> tuple[FollowUp, ...]:
        if rental_case_id is not None:
            return tuple(
                follow_up
                for follow_up in self.follow_ups.get(rental_case_id, ())
                if follow_up.status not in {FOLLOW_UP_STATUS_COMPLETED, FOLLOW_UP_STATUS_CANCELLED}
            )
        return tuple(
            follow_up
            for follow_ups in self.follow_ups.values()
            for follow_up in follow_ups
            if follow_up.status not in {FOLLOW_UP_STATUS_COMPLETED, FOLLOW_UP_STATUS_CANCELLED}
        )

    def upsert_follow_up(self, follow_up: FollowUp) -> FollowUp:
        existing_snapshot = self.load_case_snapshot(follow_up.rental_case_id)
        existing = None
        if existing_snapshot is not None and follow_up.semantic_identity_key is not None:
            existing = existing_snapshot.find_active_follow_up_by_semantic_identity(follow_up.semantic_identity_key)
        if existing is not None:
            updated = replace(
                follow_up,
                follow_up_id=existing.follow_up_id,
                created_at=existing.created_at,
            )
            return self._replace_by_id(
                self.follow_ups.setdefault(follow_up.rental_case_id, []),
                existing.follow_up_id,
                "follow_up_id",
                lambda _value: updated,
            )
        self._follow_up_id += 1
        persisted = replace(
            follow_up,
            follow_up_id=self._follow_up_id,
        )
        self.follow_ups.setdefault(follow_up.rental_case_id, []).append(persisted)
        return persisted

    def create_workflow_event(
        self,
        *,
        rental_case_id: int,
        event_type_code: str,
        source_type: str,
        source_reference: str | None,
        actor_type: str | None,
        actor_reference: str,
        occurred_at: str,
        structured_payload: dict[str, Any],
        event_identity_key: str,
    ) -> WorkflowEvent:
        for event in self.workflow_events.get(rental_case_id, ()):
            if event.event_identity_key == event_identity_key:
                return event
        self._workflow_event_id += 1
        event = WorkflowEvent(
            workflow_event_id=self._workflow_event_id,
            workflow_event_uuid=f"workflow-event-{self._workflow_event_id}",
            rental_case_id=rental_case_id,
            event_type_code=event_type_code,
            source_type=source_type,
            source_reference=source_reference,
            actor_type=actor_type,
            actor_reference=actor_reference,
            occurred_at=occurred_at,
            recorded_at=occurred_at,
            structured_payload=structured_payload,
            event_identity_key=event_identity_key,
            origin_metadata={"phase": "8.5"},
        )
        self.workflow_events.setdefault(rental_case_id, []).append(event)
        return event

    def create_blocker(self, blocker: Blocker) -> Blocker:
        existing = self.load_case_snapshot(blocker.rental_case_id)
        if existing is not None and blocker.resolution_reference is not None:
            semantic_key = _semantic_key_from_reference(blocker.resolution_reference)
            if semantic_key is not None:
                open_blocker = existing.find_open_blocker_by_semantic_key(semantic_key)
                if open_blocker is not None:
                    return open_blocker
        self._blocker_id += 1
        persisted = replace(blocker, blocker_id=self._blocker_id)
        self.blockers.setdefault(blocker.rental_case_id, []).append(persisted)
        return persisted

    def resolve_blocker(self, *, rental_case_id: int, blocker_id: int, resolved_at: str, resolution_reference: str | None) -> Blocker:
        return self._replace_by_id(
            self.blockers.setdefault(rental_case_id, []),
            blocker_id,
            "blocker_id",
            lambda value: replace(
                value,
                status=BLOCKER_STATUS_RESOLVED,
                resolved_at=resolved_at,
                resolution_reference=resolution_reference or value.resolution_reference,
            ),
        )

    def create_approval_request(self, approval_request: ApprovalRequest) -> ApprovalRequest:
        existing = self.load_case_snapshot(approval_request.rental_case_id)
        if existing is not None and approval_request.required_approver_reference is not None:
            semantic_key = _semantic_key_from_reference(approval_request.required_approver_reference)
            if semantic_key is not None:
                open_request = existing.find_open_approval_by_semantic_key(semantic_key)
                if open_request is not None:
                    return open_request
        self._approval_request_id += 1
        persisted = replace(approval_request, approval_request_id=self._approval_request_id)
        self.approval_requests.setdefault(approval_request.rental_case_id, []).append(persisted)
        return persisted

    def cancel_approval_request(
        self,
        *,
        rental_case_id: int,
        approval_request_id: int,
        decided_at: str,
        decision_notes: str | None,
    ) -> ApprovalRequest:
        return self._replace_by_id(
            self.approval_requests.setdefault(rental_case_id, []),
            approval_request_id,
            "approval_request_id",
            lambda value: replace(
                value,
                status=APPROVAL_REQUEST_STATUS_CANCELLED,
                decided_at=decided_at,
                decision_notes=decision_notes,
            ),
        )

    def decide_approval_request(
        self,
        *,
        rental_case_id: int,
        approval_request_id: int,
        status: str,
        decision_payload: Any,
        decided_at: str,
        decided_by_reference: str,
        decision_notes: str | None,
    ) -> ApprovalRequest:
        return self._replace_by_id(
            self.approval_requests.setdefault(rental_case_id, []),
            approval_request_id,
            "approval_request_id",
            lambda value: replace(
                value,
                status=status,
                decision_payload=decision_payload,
                decided_at=decided_at,
                decided_by_reference=decided_by_reference,
                decision_notes=decision_notes,
                updated_at=decided_at,
            ),
        )

    def create_workflow_action(self, workflow_action: WorkflowAction) -> WorkflowAction:
        existing_snapshot = self.load_case_snapshot(workflow_action.rental_case_id)
        if existing_snapshot is not None:
            existing = existing_snapshot.find_active_action_by_idempotency_key(workflow_action.idempotency_key)
            if existing is not None:
                return existing
        self._workflow_action_id += 1
        persisted = replace(
            workflow_action,
            workflow_action_id=self._workflow_action_id,
            workflow_action_uuid=f"workflow-action-{self._workflow_action_id}",
        )
        self.workflow_actions.setdefault(workflow_action.rental_case_id, []).append(persisted)
        return persisted

    def start_workflow_action_execution(
        self,
        request: WorkflowActionExecutionRequest,
    ) -> WorkflowActionExecutionStartResult:
        snapshot = self.load_case_snapshot(request.rental_case_id)
        if snapshot is None:
            return WorkflowActionExecutionStartResult(
                rental_case_id=request.rental_case_id,
                workflow_action_id=request.workflow_action_id,
                case_revision=0,
                action_status_before=WORKFLOW_ACTION_STATUS_PROPOSED,
                action_status_after=WORKFLOW_ACTION_STATUS_PROPOSED,
                failure_codes=(EXECUTION_FAILURE_CASE_NOT_FOUND,),
            )
        action = snapshot.find_workflow_action(request.workflow_action_id)
        if action is None:
            return WorkflowActionExecutionStartResult(
                rental_case_id=request.rental_case_id,
                workflow_action_id=request.workflow_action_id,
                case_revision=snapshot.rental_case.case_revision,
                action_status_before=WORKFLOW_ACTION_STATUS_PROPOSED,
                action_status_after=WORKFLOW_ACTION_STATUS_PROPOSED,
                failure_codes=(EXECUTION_FAILURE_ACTION_NOT_FOUND,),
            )
        if action.status == WORKFLOW_ACTION_STATUS_EXECUTING:
            return WorkflowActionExecutionStartResult(
                rental_case_id=request.rental_case_id,
                workflow_action_id=action.workflow_action_id,
                case_revision=snapshot.rental_case.case_revision,
                action_status_before=action.status,
                action_status_after=action.status,
                failure_codes=(EXECUTION_FAILURE_EXECUTION_ALREADY_STARTED,),
            )
        if action.status == WORKFLOW_ACTION_STATUS_SUCCEEDED:
            return WorkflowActionExecutionStartResult(
                rental_case_id=request.rental_case_id,
                workflow_action_id=action.workflow_action_id,
                case_revision=snapshot.rental_case.case_revision,
                action_status_before=action.status,
                action_status_after=action.status,
                failure_codes=(EXECUTION_FAILURE_ACTION_ALREADY_SUCCEEDED,),
            )
        if action.status == WORKFLOW_ACTION_STATUS_CANCELLED:
            return WorkflowActionExecutionStartResult(
                rental_case_id=request.rental_case_id,
                workflow_action_id=action.workflow_action_id,
                case_revision=snapshot.rental_case.case_revision,
                action_status_before=action.status,
                action_status_after=action.status,
                failure_codes=(EXECUTION_FAILURE_ACTION_CANCELLED,),
            )
        if action.status == WORKFLOW_ACTION_STATUS_SUPERSEDED:
            return WorkflowActionExecutionStartResult(
                rental_case_id=request.rental_case_id,
                workflow_action_id=action.workflow_action_id,
                case_revision=snapshot.rental_case.case_revision,
                action_status_before=action.status,
                action_status_after=action.status,
                failure_codes=(EXECUTION_FAILURE_ACTION_SUPERSEDED,),
            )
        if action.source_case_revision != snapshot.rental_case.case_revision:
            return WorkflowActionExecutionStartResult(
                rental_case_id=request.rental_case_id,
                workflow_action_id=action.workflow_action_id,
                case_revision=snapshot.rental_case.case_revision,
                action_status_before=action.status,
                action_status_after=action.status,
                failure_codes=(EXECUTION_FAILURE_ACTION_STALE_REVISION,),
            )
        if action.status != WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE:
            return WorkflowActionExecutionStartResult(
                rental_case_id=request.rental_case_id,
                workflow_action_id=action.workflow_action_id,
                case_revision=snapshot.rental_case.case_revision,
                action_status_before=action.status,
                action_status_after=action.status,
                failure_codes=(EXECUTION_FAILURE_ACTION_NOT_EXECUTION_READY,),
            )

        started_at = request.started_at or current_timestamp()
        updated_action = self._replace_by_id(
            self.workflow_actions.setdefault(request.rental_case_id, []),
            request.workflow_action_id,
            "workflow_action_id",
            lambda value: replace(value, status=WORKFLOW_ACTION_STATUS_EXECUTING, updated_at=started_at),
        )
        self._execution_attempt_id += 1
        attempt_number = (
            len(
                [
                    attempt
                    for attempt in self.execution_attempts.get(request.rental_case_id, ())
                    if attempt.workflow_action_id == updated_action.workflow_action_id
                ]
            )
            + 1
        )
        execution_attempt = ExecutionAttempt(
            execution_attempt_id=self._execution_attempt_id,
            execution_attempt_uuid=f"execution-attempt-{self._execution_attempt_id}",
            workflow_action_id=updated_action.workflow_action_id,
            rental_case_id=request.rental_case_id,
            attempt_number=attempt_number,
            adapter_code=updated_action.target_adapter_code,
            started_at=started_at,
            status=EXECUTION_ATTEMPT_STATUS_STARTED,
            retry_eligible=False,
            response_snapshot={},
        )
        self.execution_attempts.setdefault(request.rental_case_id, []).append(execution_attempt)
        event = self.create_workflow_event(
            rental_case_id=request.rental_case_id,
            event_type_code="workflow_action_execution_started",
            source_type="execution_runtime",
            source_reference=f"workflow_action:{updated_action.workflow_action_id}",
            actor_type=request.actor_type,
            actor_reference=request.actor_reference,
            occurred_at=started_at,
            structured_payload={
                "workflow_action_id": updated_action.workflow_action_id,
                "execution_attempt_id": execution_attempt.execution_attempt_id,
                "attempt_number": attempt_number,
                "adapter_code": updated_action.target_adapter_code,
                "action_status_before": action.status,
                "action_status_after": updated_action.status,
            },
            event_identity_key=f"action_execution_started:{updated_action.workflow_action_id}:{attempt_number}",
        )
        return WorkflowActionExecutionStartResult(
            rental_case_id=request.rental_case_id,
            workflow_action_id=updated_action.workflow_action_id,
            case_revision=snapshot.rental_case.case_revision,
            action_status_before=action.status,
            action_status_after=updated_action.status,
            audit_event_ids=(event.workflow_event_id,),
            execution_attempt_id=execution_attempt.execution_attempt_id,
            attempt_number=attempt_number,
            workflow_action=updated_action,
            execution_attempt=execution_attempt,
        )

    def complete_workflow_action_execution(
        self,
        request: WorkflowActionExecutionCompletionRequest,
    ) -> WorkflowActionExecutionResult:
        snapshot = self.load_case_snapshot(request.rental_case_id)
        if snapshot is None:
            return WorkflowActionExecutionResult(
                rental_case_id=request.rental_case_id,
                workflow_action_id=request.workflow_action_id,
                case_revision=0,
                action_status_before=WORKFLOW_ACTION_STATUS_PROPOSED,
                action_status_after=WORKFLOW_ACTION_STATUS_PROPOSED,
                failure_codes=(EXECUTION_FAILURE_CASE_NOT_FOUND,),
            )
        action = snapshot.find_workflow_action(request.workflow_action_id)
        if action is None:
            return WorkflowActionExecutionResult(
                rental_case_id=request.rental_case_id,
                workflow_action_id=request.workflow_action_id,
                case_revision=snapshot.rental_case.case_revision,
                action_status_before=WORKFLOW_ACTION_STATUS_PROPOSED,
                action_status_after=WORKFLOW_ACTION_STATUS_PROPOSED,
                failure_codes=(EXECUTION_FAILURE_ACTION_NOT_FOUND,),
            )
        attempt = snapshot.find_execution_attempt(request.execution_attempt_id)
        if attempt is None or attempt.workflow_action_id != action.workflow_action_id:
            return WorkflowActionExecutionResult(
                rental_case_id=request.rental_case_id,
                workflow_action_id=request.workflow_action_id,
                case_revision=snapshot.rental_case.case_revision,
                action_status_before=action.status,
                action_status_after=action.status,
                failure_codes=(EXECUTION_FAILURE_ATTEMPT_NOT_FOUND,),
            )
        if attempt.status != EXECUTION_ATTEMPT_STATUS_STARTED:
            return WorkflowActionExecutionResult(
                rental_case_id=request.rental_case_id,
                workflow_action_id=request.workflow_action_id,
                case_revision=snapshot.rental_case.case_revision,
                action_status_before=action.status,
                action_status_after=action.status,
                failure_codes=(EXECUTION_FAILURE_EXECUTION_COMPLETE_FAILED,),
            )
        if action.source_case_revision != snapshot.rental_case.case_revision:
            return WorkflowActionExecutionResult(
                rental_case_id=request.rental_case_id,
                workflow_action_id=request.workflow_action_id,
                case_revision=snapshot.rental_case.case_revision,
                action_status_before=action.status,
                action_status_after=action.status,
                execution_attempt_id=attempt.execution_attempt_id,
                attempt_status=attempt.status,
                failure_codes=(EXECUTION_FAILURE_STALE_CASE_REVISION,),
            )
        conflicting_attempt = _find_conflicting_external_reference_attempt(
            self.execution_attempts,
            external_reference=request.result.external_reference,
            workflow_action_id=request.workflow_action_id,
            execution_attempt_id=request.execution_attempt_id,
            rental_case_id=request.rental_case_id,
        )
        if conflicting_attempt is not None:
            return WorkflowActionExecutionResult(
                rental_case_id=request.rental_case_id,
                workflow_action_id=request.workflow_action_id,
                case_revision=snapshot.rental_case.case_revision,
                action_status_before=action.status,
                action_status_after=action.status,
                execution_attempt_id=attempt.execution_attempt_id,
                attempt_status=attempt.status,
                external_reference=request.result.external_reference,
                failure_codes=(EXECUTION_FAILURE_EXTERNAL_REFERENCE_CONFLICT,),
            )

        completed_at = request.result.completed_at or current_timestamp()
        final_action_status = (
            WORKFLOW_ACTION_STATUS_SUCCEEDED
            if request.result.attempt_status == "succeeded"
            else (
                WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE
                if request.result.retry_eligible
                else WORKFLOW_ACTION_STATUS_FAILED
            )
        )
        updated_action = self._replace_by_id(
            self.workflow_actions.setdefault(request.rental_case_id, []),
            request.workflow_action_id,
            "workflow_action_id",
            lambda value: replace(value, status=final_action_status, updated_at=completed_at),
        )
        updated_attempt = self._replace_by_id(
            self.execution_attempts.setdefault(request.rental_case_id, []),
            request.execution_attempt_id,
            "execution_attempt_id",
            lambda value: replace(
                value,
                status=request.result.attempt_status,
                retry_eligible=request.result.retry_eligible,
                response_snapshot=request.result.response_snapshot,
                completed_at=completed_at,
                external_reference=request.result.external_reference,
                failure_code=request.result.failure_code,
            ),
        )
        event = self.create_workflow_event(
            rental_case_id=request.rental_case_id,
            event_type_code="workflow_action_execution_completed",
            source_type="execution_runtime",
            source_reference=f"workflow_action:{updated_action.workflow_action_id}",
            actor_type=request.actor_type,
            actor_reference=request.actor_reference,
            occurred_at=completed_at,
            structured_payload={
                "workflow_action_id": updated_action.workflow_action_id,
                "execution_attempt_id": updated_attempt.execution_attempt_id,
                "attempt_status": updated_attempt.status,
                "retry_eligible": updated_attempt.retry_eligible,
                "external_reference": updated_attempt.external_reference,
                "failure_code": updated_attempt.failure_code,
                "action_status_before": action.status,
                "action_status_after": updated_action.status,
            },
            event_identity_key=f"action_execution_completed:{updated_action.workflow_action_id}:{updated_attempt.execution_attempt_id}",
        )
        return WorkflowActionExecutionResult(
            rental_case_id=request.rental_case_id,
            workflow_action_id=updated_action.workflow_action_id,
            case_revision=snapshot.rental_case.case_revision,
            action_status_before=action.status,
            action_status_after=updated_action.status,
            audit_event_ids=(event.workflow_event_id,),
            execution_attempt_id=updated_attempt.execution_attempt_id,
            attempt_status=updated_attempt.status,
            retry_eligible=updated_attempt.retry_eligible,
            external_reference=updated_attempt.external_reference,
        )

    def commit_follow_up_status_update(
        self,
        request: FollowUpStatusUpdateRequest,
    ) -> FollowUpStatusUpdateResult:
        snapshot = self.load_case_snapshot(request.rental_case_id)
        if snapshot is None:
            return FollowUpStatusUpdateResult(
                rental_case_id=request.rental_case_id,
                follow_up_id=request.follow_up_id,
                status_before=FOLLOW_UP_STATUS_COMPLETED,
                status_after=FOLLOW_UP_STATUS_COMPLETED,
                attempt_count_before=0,
                attempt_count_after=0,
                failure_codes=(EXECUTION_FAILURE_CASE_NOT_FOUND,),
            )
        follow_up = snapshot.find_follow_up(request.follow_up_id)
        if follow_up is None:
            return FollowUpStatusUpdateResult(
                rental_case_id=request.rental_case_id,
                follow_up_id=request.follow_up_id,
                status_before=FOLLOW_UP_STATUS_COMPLETED,
                status_after=FOLLOW_UP_STATUS_COMPLETED,
                attempt_count_before=0,
                attempt_count_after=0,
                failure_codes=(EXECUTION_FAILURE_FOLLOW_UP_NOT_FOUND,),
            )
        if (
            request.expected_current_status is not None
            and follow_up.status != request.expected_current_status
        ):
            return FollowUpStatusUpdateResult(
                rental_case_id=request.rental_case_id,
                follow_up_id=request.follow_up_id,
                status_before=follow_up.status,
                status_after=follow_up.status,
                attempt_count_before=follow_up.attempt_count,
                attempt_count_after=follow_up.attempt_count,
                failure_codes=(EXECUTION_FAILURE_FOLLOW_UP_STATE_TRANSITION_INVALID,),
            )
        if follow_up.status in {FOLLOW_UP_STATUS_COMPLETED, FOLLOW_UP_STATUS_CANCELLED} and request.target_status not in {
            follow_up.status,
        }:
            return FollowUpStatusUpdateResult(
                rental_case_id=request.rental_case_id,
                follow_up_id=request.follow_up_id,
                status_before=follow_up.status,
                status_after=follow_up.status,
                attempt_count_before=follow_up.attempt_count,
                attempt_count_after=follow_up.attempt_count,
                failure_codes=(EXECUTION_FAILURE_FOLLOW_UP_STATE_TRANSITION_INVALID,),
            )

        occurred_at = request.occurred_at or current_timestamp()
        updated = self._replace_by_id(
            self.follow_ups.setdefault(request.rental_case_id, []),
            request.follow_up_id,
            "follow_up_id",
            lambda value: replace(
                value,
                status=request.target_status,
                attempt_count=value.attempt_count + request.attempt_count_delta,
                updated_at=occurred_at,
                completed_at=request.completed_at if request.target_status in {FOLLOW_UP_STATUS_COMPLETED, FOLLOW_UP_STATUS_CANCELLED} else value.completed_at,
            ),
        )
        event = self.create_workflow_event(
            rental_case_id=request.rental_case_id,
            event_type_code="follow_up_status_updated",
            source_type="execution_runtime",
            source_reference=f"follow_up:{updated.follow_up_id}",
            actor_type=request.actor_type,
            actor_reference=request.actor_reference,
            occurred_at=occurred_at,
            structured_payload={
                "follow_up_id": updated.follow_up_id,
                "status_before": follow_up.status,
                "status_after": updated.status,
                "attempt_count_before": follow_up.attempt_count,
                "attempt_count_after": updated.attempt_count,
            },
            event_identity_key=(
                f"follow_up_status_updated:{updated.follow_up_id}:{follow_up.status}:"
                f"{updated.status}:{updated.attempt_count}"
            ),
        )
        return FollowUpStatusUpdateResult(
            rental_case_id=request.rental_case_id,
            follow_up_id=updated.follow_up_id,
            status_before=follow_up.status,
            status_after=updated.status,
            attempt_count_before=follow_up.attempt_count,
            attempt_count_after=updated.attempt_count,
            audit_event_ids=(event.workflow_event_id,),
            follow_up=updated,
        )

    def supersede_workflow_action(
        self,
        *,
        rental_case_id: int,
        workflow_action_id: int,
        updated_at: str,
    ) -> WorkflowAction:
        return self._replace_by_id(
            self.workflow_actions.setdefault(rental_case_id, []),
            workflow_action_id,
            "workflow_action_id",
            lambda value: replace(
                value,
                status=WORKFLOW_ACTION_STATUS_SUPERSEDED,
                updated_at=updated_at,
            ),
        )

    def create_requirement(self, requirement: Requirement) -> Requirement:
        for existing in self.requirements.get(requirement.rental_case_id, ()):
            if (
                existing.requirement_type == requirement.requirement_type
                and existing.status in {"required", "in_progress", "unresolved"}
            ):
                return existing
        self._requirement_id += 1
        persisted = replace(requirement, requirement_id=self._requirement_id)
        self.requirements.setdefault(requirement.rental_case_id, []).append(persisted)
        return persisted

    def activate_case_decision(
        self,
        *,
        rental_case_id: int,
        case_decision_id: int,
        approval_request_id: int | None,
        effective_value_payload: Any,
        effective_at: str,
        expected_case_revision: int,
    ) -> tuple[CaseDecision, RentalCase]:
        rental_case = self.increment_case_revision(
            rental_case_id=rental_case_id,
            expected_case_revision=expected_case_revision,
            updated_at=effective_at,
        )
        decision = self._replace_by_id(
            self.case_decisions.setdefault(rental_case_id, []),
            case_decision_id,
            "case_decision_id",
            lambda value: replace(
                value,
                status=CASE_DECISION_STATUS_ACTIVE,
                effective_value_payload=effective_value_payload,
                approval_request_id=approval_request_id or value.approval_request_id,
                effective_at=effective_at,
                updated_at=effective_at,
            ),
        )
        return decision, rental_case

    def reject_case_decision(
        self,
        *,
        rental_case_id: int,
        case_decision_id: int,
        updated_at: str,
    ) -> CaseDecision:
        return self._replace_by_id(
            self.case_decisions.setdefault(rental_case_id, []),
            case_decision_id,
            "case_decision_id",
            lambda value: replace(
                value,
                status=CASE_DECISION_STATUS_REJECTED,
                updated_at=updated_at,
            ),
        )

    def resolve_proposed_change(
        self,
        *,
        rental_case_id: int,
        proposed_case_change_id: int,
        status: str,
        final_value_payload: Any,
        accepted_at: str | None,
    ) -> ProposedCaseChange:
        return self._replace_by_id(
            self.proposed_changes.setdefault(rental_case_id, []),
            proposed_case_change_id,
            "proposed_case_change_id",
            lambda value: replace(
                value,
                status=status,
                final_value_payload=final_value_payload if status == PROPOSED_CHANGE_STATUS_ACCEPTED else value.final_value_payload,
                accepted_at=accepted_at if status == PROPOSED_CHANGE_STATUS_ACCEPTED else value.accepted_at,
                updated_at=accepted_at or current_timestamp(),
            ),
        )

    def upsert_rental_case_fact(
        self,
        *,
        rental_case_id: int,
        field_code: str,
        domain_code: str,
        value_payload: Any,
        source_reference: str,
        established_case_revision: int,
        timestamp: str,
    ) -> RentalCaseFact:
        facts = self.rental_case_facts.setdefault(rental_case_id, [])
        for index, fact in enumerate(facts):
            if fact.field_code != field_code:
                continue
            replacement = replace(
                fact,
                domain_code=domain_code,
                value_payload=value_payload,
                source_reference=source_reference,
                established_case_revision=established_case_revision,
                updated_at=timestamp,
            )
            facts[index] = replacement
            return replacement
        self._rental_case_fact_id += 1
        fact = RentalCaseFact(
            rental_case_fact_id=self._rental_case_fact_id,
            rental_case_id=rental_case_id,
            field_code=field_code,
            domain_code=domain_code,
            value_payload=value_payload,
            source_reference=source_reference,
            established_case_revision=established_case_revision,
            created_at=timestamp,
            updated_at=timestamp,
        )
        facts.append(fact)
        return fact

    def update_rental_case_schedule(
        self,
        *,
        rental_case_id: int,
        expected_case_revision: int,
        active_event_start: str | None,
        active_event_end: str | None,
        updated_at: str,
    ) -> RentalCase:
        rental_case = self.rental_cases[rental_case_id]
        if rental_case.case_revision != expected_case_revision:
            raise ValueError("stale_case_revision")
        updated = replace(
            rental_case,
            case_revision=rental_case.case_revision + 1,
            active_event_start=active_event_start,
            active_event_end=active_event_end,
            updated_at=updated_at,
        )
        self.rental_cases[rental_case_id] = updated
        return updated

    def increment_case_revision(
        self,
        *,
        rental_case_id: int,
        expected_case_revision: int,
        updated_at: str,
    ) -> RentalCase:
        rental_case = self.rental_cases[rental_case_id]
        if rental_case.case_revision != expected_case_revision:
            raise ValueError("stale_case_revision")
        updated = replace(
            rental_case,
            case_revision=rental_case.case_revision + 1,
            updated_at=updated_at,
        )
        self.rental_cases[rental_case_id] = updated
        return updated

    def update_artifact_freshness(
        self,
        *,
        rental_case_id: int,
        artifact_reference_id: int,
        freshness_status: str,
        updated_at: str,
    ) -> ArtifactReference:
        return self._replace_by_id(
            self.artifacts.setdefault(rental_case_id, []),
            artifact_reference_id,
            "artifact_reference_id",
            lambda value: replace(
                value,
                freshness_status=freshness_status,
                updated_at=updated_at,
            ),
        )

    def commit_case_decision_activation(
        self,
        request: CaseDecisionActivationRequest,
    ) -> CaseDecisionActivationResult:
        snapshot = self.load_case_snapshot(request.rental_case_id)
        if snapshot is None:
            return CaseDecisionActivationResult(
                rental_case_id=request.rental_case_id,
                case_decision_id=request.case_decision_id,
                approval_request_id=request.approval_request_id,
                previous_case_revision=request.expected_case_revision,
                new_case_revision=request.expected_case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_CASE_NOT_FOUND,),
            )
        if snapshot.rental_case.case_revision != request.expected_case_revision:
            return CaseDecisionActivationResult(
                rental_case_id=request.rental_case_id,
                case_decision_id=request.case_decision_id,
                approval_request_id=request.approval_request_id,
                previous_case_revision=snapshot.rental_case.case_revision,
                new_case_revision=snapshot.rental_case.case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_STALE_CASE_REVISION,),
            )
        approval = snapshot.find_approval_request(request.approval_request_id)
        decision = snapshot.find_case_decision(request.case_decision_id)
        if approval is None or decision is None:
            return CaseDecisionActivationResult(
                rental_case_id=request.rental_case_id,
                case_decision_id=request.case_decision_id,
                approval_request_id=request.approval_request_id,
                previous_case_revision=snapshot.rental_case.case_revision,
                new_case_revision=snapshot.rental_case.case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_APPROVAL_TARGET_INVALID,),
            )
        target_entity_id = approval.target_entity_id
        if target_entity_id is None:
            target_entity_id = _reference_id_from_text(approval.target_entity_reference)
        if approval.target_entity_type != "case_decision":
            return CaseDecisionActivationResult(
                rental_case_id=request.rental_case_id,
                case_decision_id=request.case_decision_id,
                approval_request_id=request.approval_request_id,
                previous_case_revision=snapshot.rental_case.case_revision,
                new_case_revision=snapshot.rental_case.case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_APPROVAL_TARGET_MISMATCH,),
            )
        if target_entity_id is None:
            return CaseDecisionActivationResult(
                rental_case_id=request.rental_case_id,
                case_decision_id=request.case_decision_id,
                approval_request_id=request.approval_request_id,
                previous_case_revision=snapshot.rental_case.case_revision,
                new_case_revision=snapshot.rental_case.case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_APPROVAL_TARGET_INVALID,),
            )
        if target_entity_id != decision.case_decision_id:
            return CaseDecisionActivationResult(
                rental_case_id=request.rental_case_id,
                case_decision_id=request.case_decision_id,
                approval_request_id=request.approval_request_id,
                previous_case_revision=snapshot.rental_case.case_revision,
                new_case_revision=snapshot.rental_case.case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_APPROVAL_TARGET_MISMATCH,),
            )
        if decision.status == CASE_DECISION_STATUS_ACTIVE and approval.status == APPROVAL_REQUEST_STATUS_APPROVED:
            return CaseDecisionActivationResult(
                rental_case_id=request.rental_case_id,
                case_decision_id=request.case_decision_id,
                approval_request_id=request.approval_request_id,
                previous_case_revision=snapshot.rental_case.case_revision,
                new_case_revision=snapshot.rental_case.case_revision,
            )
        if decision.status not in {"proposed", "pending_approval"}:
            return CaseDecisionActivationResult(
                rental_case_id=request.rental_case_id,
                case_decision_id=request.case_decision_id,
                approval_request_id=request.approval_request_id,
                previous_case_revision=snapshot.rental_case.case_revision,
                new_case_revision=snapshot.rental_case.case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_CASE_DECISION_NOT_ACTIVATABLE,),
            )
        conflict = next(
            (
                existing
                for existing in snapshot.case_decisions
                if existing.case_decision_id != decision.case_decision_id
                and existing.scope_key == decision.scope_key
                and existing.status == CASE_DECISION_STATUS_ACTIVE
            ),
            None,
        )
        if conflict is not None:
            return CaseDecisionActivationResult(
                rental_case_id=request.rental_case_id,
                case_decision_id=request.case_decision_id,
                approval_request_id=request.approval_request_id,
                previous_case_revision=snapshot.rental_case.case_revision,
                new_case_revision=snapshot.rental_case.case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_CASE_DECISION_CONFLICT,),
            )

        effective_at = request.effective_at or current_timestamp()
        approval = self.decide_approval_request(
            rental_case_id=request.rental_case_id,
            approval_request_id=request.approval_request_id,
            status=APPROVAL_REQUEST_STATUS_APPROVED,
            decision_payload={"decision": ORCHESTRATION_DECISION_APPROVED},
            decided_at=effective_at,
            decided_by_reference=request.actor_reference,
            decision_notes=None,
        )
        decision, rental_case = self.activate_case_decision(
            rental_case_id=request.rental_case_id,
            case_decision_id=request.case_decision_id,
            approval_request_id=approval.approval_request_id,
            effective_value_payload=request.effective_value_payload,
            effective_at=effective_at,
            expected_case_revision=request.expected_case_revision,
        )
        artifact_ids = self._mark_dependent_artifacts_stale(
            request.rental_case_id,
            rental_case.case_revision,
            effective_at,
        )
        superseded_action_ids = self._supersede_stale_actions(
            request.rental_case_id,
            rental_case.case_revision,
            effective_at,
        )
        workflow_event_ids = (
            self.create_workflow_event(
                rental_case_id=request.rental_case_id,
                event_type_code="approval_decided",
                source_type="orchestration_repository",
                source_reference=request.source_reference or f"approval:{approval.approval_request_id}",
                actor_type=request.actor_type,
                actor_reference=request.actor_reference,
                occurred_at=effective_at,
                structured_payload={
                    "approval_request_id": approval.approval_request_id,
                    "target_entity_type": approval.target_entity_type,
                    "target_entity_id": approval.target_entity_id,
                    "status_before": "open",
                    "status_after": approval.status,
                },
                event_identity_key=f"approval:approved:{approval.approval_request_id}:{request.expected_case_revision}",
            ).workflow_event_id,
            self.create_workflow_event(
                rental_case_id=request.rental_case_id,
                event_type_code="case_decision_activated",
                source_type="orchestration_repository",
                source_reference=request.source_reference or f"case_decision:{decision.case_decision_id}",
                actor_type=request.actor_type,
                actor_reference=request.actor_reference,
                occurred_at=effective_at,
                structured_payload={
                    "case_decision_id": decision.case_decision_id,
                    "approval_request_id": approval.approval_request_id,
                    "case_revision_before": request.expected_case_revision,
                    "case_revision_after": rental_case.case_revision,
                },
                event_identity_key=f"case_decision:activated:{decision.case_decision_id}:{request.expected_case_revision}",
            ).workflow_event_id,
        )
        return CaseDecisionActivationResult(
            rental_case_id=request.rental_case_id,
            case_decision_id=request.case_decision_id,
            approval_request_id=request.approval_request_id,
            previous_case_revision=request.expected_case_revision,
            new_case_revision=rental_case.case_revision,
            workflow_event_ids=workflow_event_ids,
            artifact_freshness_changed_ids=tuple(artifact_ids),
            superseded_action_ids=tuple(superseded_action_ids),
        )

    def apply_case_decision_approval(
        self,
        request: ApprovalDecisionInput,
    ) -> ApprovalDecisionResult:
        snapshot = self.load_case_snapshot(request.rental_case_id)
        if snapshot is None:
            return ApprovalDecisionResult(
                rental_case_id=request.rental_case_id,
                approval_request_id=request.approval_request_id,
                approval_status="open",
                case_revision_before=request.expected_case_revision,
                case_revision_after=request.expected_case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_CASE_NOT_FOUND,),
            )
        if snapshot.rental_case.case_revision != request.expected_case_revision:
            return ApprovalDecisionResult(
                rental_case_id=request.rental_case_id,
                approval_request_id=request.approval_request_id,
                approval_status="open",
                case_revision_before=snapshot.rental_case.case_revision,
                case_revision_after=snapshot.rental_case.case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_STALE_CASE_REVISION,),
            )
        approval = snapshot.find_approval_request(request.approval_request_id)
        target_entity_id = None if approval is None else approval.target_entity_id
        if approval is None and request.approval_request_id > 0:
            return ApprovalDecisionResult(
                rental_case_id=request.rental_case_id,
                approval_request_id=request.approval_request_id,
                approval_status="open",
                case_revision_before=snapshot.rental_case.case_revision,
                case_revision_after=snapshot.rental_case.case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_APPROVAL_TARGET_INVALID,),
            )
        if approval is None or approval.target_entity_type != "case_decision" or target_entity_id is None:
            return ApprovalDecisionResult(
                rental_case_id=request.rental_case_id,
                approval_request_id=request.approval_request_id,
                approval_status="open" if approval is None else approval.status,
                case_revision_before=snapshot.rental_case.case_revision,
                case_revision_after=snapshot.rental_case.case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_APPROVAL_TARGET_INVALID,),
            )
        decision = snapshot.find_case_decision(target_entity_id)
        if decision is None:
            return ApprovalDecisionResult(
                rental_case_id=request.rental_case_id,
                approval_request_id=request.approval_request_id,
                approval_status=approval.status,
                case_revision_before=snapshot.rental_case.case_revision,
                case_revision_after=snapshot.rental_case.case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_APPROVAL_TARGET_INVALID,),
            )
        if approval.status in {APPROVAL_REQUEST_STATUS_APPROVED, APPROVAL_REQUEST_STATUS_REJECTED}:
            if approval.status == APPROVAL_REQUEST_STATUS_APPROVED and request.decision == ORCHESTRATION_DECISION_APPROVED:
                return ApprovalDecisionResult(
                    rental_case_id=request.rental_case_id,
                    approval_request_id=request.approval_request_id,
                    approval_status=approval.status,
                    case_revision_before=snapshot.rental_case.case_revision,
                    case_revision_after=snapshot.rental_case.case_revision,
                    activated_case_decision_id=decision.case_decision_id if decision.status == CASE_DECISION_STATUS_ACTIVE else None,
                )
            if approval.status == APPROVAL_REQUEST_STATUS_REJECTED and request.decision != ORCHESTRATION_DECISION_APPROVED:
                return ApprovalDecisionResult(
                    rental_case_id=request.rental_case_id,
                    approval_request_id=request.approval_request_id,
                    approval_status=approval.status,
                    case_revision_before=snapshot.rental_case.case_revision,
                    case_revision_after=snapshot.rental_case.case_revision,
                    rejected_case_decision_id=decision.case_decision_id if decision.status == CASE_DECISION_STATUS_REJECTED else None,
                )
            return ApprovalDecisionResult(
                rental_case_id=request.rental_case_id,
                approval_request_id=request.approval_request_id,
                approval_status=approval.status,
                case_revision_before=snapshot.rental_case.case_revision,
                case_revision_after=snapshot.rental_case.case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_INVALID_ENTITY_STATUS,),
            )

        decided_at = request.decided_at or current_timestamp()
        if request.decision == ORCHESTRATION_DECISION_APPROVED:
            activation_result = self.commit_case_decision_activation(
                CaseDecisionActivationRequest(
                    rental_case_id=request.rental_case_id,
                    case_decision_id=decision.case_decision_id,
                    approval_request_id=request.approval_request_id,
                    expected_case_revision=request.expected_case_revision,
                    effective_value_payload=decision.proposed_value_payload,
                    actor_reference=request.actor_reference,
                    actor_type=request.actor_type,
                    source_reference=f"approval:{request.approval_request_id}",
                    effective_at=decided_at,
                )
            )
            if activation_result.failure_codes:
                return ApprovalDecisionResult(
                    rental_case_id=request.rental_case_id,
                    approval_request_id=request.approval_request_id,
                    approval_status=approval.status,
                    case_revision_before=activation_result.previous_case_revision,
                    case_revision_after=activation_result.new_case_revision,
                    audit_event_ids=activation_result.workflow_event_ids,
                    artifact_freshness_changed_ids=activation_result.artifact_freshness_changed_ids,
                    superseded_action_ids=activation_result.superseded_action_ids,
                    failure_codes=activation_result.failure_codes,
                )
            resolved_blocker_ids = tuple(
                self._resolve_action_or_decision_blockers(
                    request.rental_case_id,
                    decided_at,
                    origin_entity_type="case_decision",
                    origin_entity_id=decision.case_decision_id,
                )
            )
            return ApprovalDecisionResult(
                rental_case_id=request.rental_case_id,
                approval_request_id=request.approval_request_id,
                approval_status=APPROVAL_REQUEST_STATUS_APPROVED,
                case_revision_before=activation_result.previous_case_revision,
                case_revision_after=activation_result.new_case_revision,
                audit_event_ids=activation_result.workflow_event_ids,
                resolved_blocker_ids=resolved_blocker_ids,
                activated_case_decision_id=decision.case_decision_id,
                artifact_freshness_changed_ids=activation_result.artifact_freshness_changed_ids,
                superseded_action_ids=activation_result.superseded_action_ids,
            )

        approval = self.decide_approval_request(
            rental_case_id=request.rental_case_id,
            approval_request_id=request.approval_request_id,
            status=APPROVAL_REQUEST_STATUS_REJECTED,
            decision_payload=request.decision_payload,
            decided_at=decided_at,
            decided_by_reference=request.actor_reference,
            decision_notes=request.decision_notes,
        )
        decision = self.reject_case_decision(
            rental_case_id=request.rental_case_id,
            case_decision_id=decision.case_decision_id,
            updated_at=decided_at,
        )
        resolved_blocker_ids = tuple(
            self._resolve_action_or_decision_blockers(
                request.rental_case_id,
                decided_at,
                origin_entity_type="case_decision",
                origin_entity_id=decision.case_decision_id,
            )
        )
        audit_event_ids = (
            self.create_workflow_event(
                rental_case_id=request.rental_case_id,
                event_type_code="approval_decided",
                source_type="orchestration_repository",
                source_reference=f"approval:{request.approval_request_id}",
                actor_type=request.actor_type,
                actor_reference=request.actor_reference,
                occurred_at=decided_at,
                structured_payload={
                    "approval_request_id": request.approval_request_id,
                    "target_entity_type": "case_decision",
                    "target_entity_id": decision.case_decision_id,
                    "status_before": "open",
                    "status_after": approval.status,
                },
                event_identity_key=f"approval:rejected:{request.approval_request_id}:{request.expected_case_revision}",
            ).workflow_event_id,
            self.create_workflow_event(
                rental_case_id=request.rental_case_id,
                event_type_code="case_decision_rejected",
                source_type="orchestration_repository",
                source_reference=f"case_decision:{decision.case_decision_id}",
                actor_type=request.actor_type,
                actor_reference=request.actor_reference,
                occurred_at=decided_at,
                structured_payload={
                    "case_decision_id": decision.case_decision_id,
                    "approval_request_id": request.approval_request_id,
                },
                event_identity_key=f"case_decision:rejected:{decision.case_decision_id}:{request.expected_case_revision}",
            ).workflow_event_id,
        )
        return ApprovalDecisionResult(
            rental_case_id=request.rental_case_id,
            approval_request_id=request.approval_request_id,
            approval_status=approval.status,
            case_revision_before=request.expected_case_revision,
            case_revision_after=request.expected_case_revision,
            audit_event_ids=audit_event_ids,
            resolved_blocker_ids=resolved_blocker_ids,
            rejected_case_decision_id=decision.case_decision_id,
        )

    def apply_workflow_action_approval(
        self,
        request: ApprovalDecisionInput,
    ) -> WorkflowActionApprovalResult:
        snapshot = self.load_case_snapshot(request.rental_case_id)
        if snapshot is None:
            return WorkflowActionApprovalResult(
                rental_case_id=request.rental_case_id,
                approval_request_id=request.approval_request_id,
                workflow_action_id=0,
                approval_status="open",
                action_status_before=WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
                action_status_after=WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
                case_revision_before=request.expected_case_revision,
                case_revision_after=request.expected_case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_CASE_NOT_FOUND,),
            )
        if snapshot.rental_case.case_revision != request.expected_case_revision:
            return WorkflowActionApprovalResult(
                rental_case_id=request.rental_case_id,
                approval_request_id=request.approval_request_id,
                workflow_action_id=0,
                approval_status="open",
                action_status_before=WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
                action_status_after=WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
                case_revision_before=snapshot.rental_case.case_revision,
                case_revision_after=snapshot.rental_case.case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_STALE_CASE_REVISION,),
            )
        approval = snapshot.find_approval_request(request.approval_request_id)
        target_entity_id = None if approval is None else approval.target_entity_id
        if approval is None or approval.target_entity_type != "workflow_action" or target_entity_id is None:
            return WorkflowActionApprovalResult(
                rental_case_id=request.rental_case_id,
                approval_request_id=request.approval_request_id,
                workflow_action_id=0,
                approval_status="open" if approval is None else approval.status,
                action_status_before=WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
                action_status_after=WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
                case_revision_before=snapshot.rental_case.case_revision,
                case_revision_after=snapshot.rental_case.case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_APPROVAL_TARGET_INVALID,),
            )
        action = next(
            (candidate for candidate in snapshot.workflow_actions if candidate.workflow_action_id == target_entity_id),
            None,
        )
        if action is None:
            return WorkflowActionApprovalResult(
                rental_case_id=request.rental_case_id,
                approval_request_id=request.approval_request_id,
                workflow_action_id=target_entity_id,
                approval_status=approval.status,
                action_status_before=WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
                action_status_after=WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
                case_revision_before=snapshot.rental_case.case_revision,
                case_revision_after=snapshot.rental_case.case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_APPROVAL_TARGET_INVALID,),
            )
        if approval.status in {APPROVAL_REQUEST_STATUS_APPROVED, APPROVAL_REQUEST_STATUS_REJECTED}:
            if approval.status == APPROVAL_REQUEST_STATUS_APPROVED and request.decision == ORCHESTRATION_DECISION_APPROVED:
                return WorkflowActionApprovalResult(
                    rental_case_id=request.rental_case_id,
                    approval_request_id=request.approval_request_id,
                    workflow_action_id=action.workflow_action_id,
                    approval_status=approval.status,
                    action_status_before=action.status,
                    action_status_after=action.status,
                    case_revision_before=snapshot.rental_case.case_revision,
                    case_revision_after=snapshot.rental_case.case_revision,
                )
            if approval.status == APPROVAL_REQUEST_STATUS_REJECTED and request.decision != ORCHESTRATION_DECISION_APPROVED:
                return WorkflowActionApprovalResult(
                    rental_case_id=request.rental_case_id,
                    approval_request_id=request.approval_request_id,
                    workflow_action_id=action.workflow_action_id,
                    approval_status=approval.status,
                    action_status_before=action.status,
                    action_status_after=action.status,
                    case_revision_before=snapshot.rental_case.case_revision,
                    case_revision_after=snapshot.rental_case.case_revision,
                )
            return WorkflowActionApprovalResult(
                rental_case_id=request.rental_case_id,
                approval_request_id=request.approval_request_id,
                workflow_action_id=action.workflow_action_id,
                approval_status=approval.status,
                action_status_before=action.status,
                action_status_after=action.status,
                case_revision_before=snapshot.rental_case.case_revision,
                case_revision_after=snapshot.rental_case.case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_INVALID_ENTITY_STATUS,),
            )

        if action.approval_posture == "blocked":
            return WorkflowActionApprovalResult(
                rental_case_id=request.rental_case_id,
                approval_request_id=request.approval_request_id,
                workflow_action_id=action.workflow_action_id,
                approval_status=approval.status,
                action_status_before=action.status,
                action_status_after=action.status,
                case_revision_before=snapshot.rental_case.case_revision,
                case_revision_after=snapshot.rental_case.case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_ACTION_BLOCKED,),
            )
        if action.status not in {WORKFLOW_ACTION_STATUS_PROPOSED, WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL}:
            return WorkflowActionApprovalResult(
                rental_case_id=request.rental_case_id,
                approval_request_id=request.approval_request_id,
                workflow_action_id=action.workflow_action_id,
                approval_status=approval.status,
                action_status_before=action.status,
                action_status_after=action.status,
                case_revision_before=snapshot.rental_case.case_revision,
                case_revision_after=snapshot.rental_case.case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_ACTION_STATE_TRANSITION_INVALID,),
            )

        decided_at = request.decided_at or current_timestamp()
        approval_status = (
            APPROVAL_REQUEST_STATUS_APPROVED
            if request.decision == ORCHESTRATION_DECISION_APPROVED
            else APPROVAL_REQUEST_STATUS_REJECTED
        )
        approval = self.decide_approval_request(
            rental_case_id=request.rental_case_id,
            approval_request_id=request.approval_request_id,
            status=approval_status,
            decision_payload=request.decision_payload,
            decided_at=decided_at,
            decided_by_reference=request.actor_reference,
            decision_notes=request.decision_notes,
        )
        action_status_before = action.status
        if request.decision == ORCHESTRATION_DECISION_APPROVED:
            next_status = WORKFLOW_ACTION_STATUS_APPROVED
            action = self._replace_by_id(
                self.workflow_actions.setdefault(request.rental_case_id, []),
                action.workflow_action_id,
                "workflow_action_id",
                lambda value: replace(value, status=next_status, updated_at=decided_at),
            )
            audit_event_ids = [
                self.create_workflow_event(
                    rental_case_id=request.rental_case_id,
                    event_type_code="approval_decided",
                    source_type="orchestration_repository",
                    source_reference=f"approval:{request.approval_request_id}",
                    actor_type=request.actor_type,
                    actor_reference=request.actor_reference,
                    occurred_at=decided_at,
                    structured_payload={
                        "approval_request_id": request.approval_request_id,
                        "target_entity_type": "workflow_action",
                        "target_entity_id": action.workflow_action_id,
                        "status_before": "open",
                        "status_after": approval.status,
                    },
                    event_identity_key=f"approval:action:approved:{request.approval_request_id}:{request.expected_case_revision}",
                ).workflow_event_id,
                self.create_workflow_event(
                    rental_case_id=request.rental_case_id,
                    event_type_code="workflow_action_status_changed",
                    source_type="orchestration_repository",
                    source_reference=f"workflow_action:{action.workflow_action_id}",
                    actor_type=request.actor_type,
                    actor_reference=request.actor_reference,
                    occurred_at=decided_at,
                    structured_payload={
                        "workflow_action_id": action.workflow_action_id,
                        "status_before": action_status_before,
                        "status_after": next_status,
                    },
                    event_identity_key=f"workflow_action:approved:{action.workflow_action_id}:{request.expected_case_revision}",
                ).workflow_event_id,
            ]
            if action.approval_posture == "approval_required":
                action = self._replace_by_id(
                    self.workflow_actions.setdefault(request.rental_case_id, []),
                    action.workflow_action_id,
                    "workflow_action_id",
                    lambda value: replace(value, status=WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE, updated_at=decided_at),
                )
                audit_event_ids.append(
                    self.create_workflow_event(
                        rental_case_id=request.rental_case_id,
                        event_type_code="workflow_action_status_changed",
                        source_type="orchestration_repository",
                        source_reference=f"workflow_action:{action.workflow_action_id}",
                        actor_type=request.actor_type,
                        actor_reference=request.actor_reference,
                        occurred_at=decided_at,
                        structured_payload={
                            "workflow_action_id": action.workflow_action_id,
                            "status_before": WORKFLOW_ACTION_STATUS_APPROVED,
                            "status_after": WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
                        },
                        event_identity_key=f"workflow_action:ready:{action.workflow_action_id}:{request.expected_case_revision}",
                    ).workflow_event_id
                )
            resolved_blocker_ids = tuple(
                self._resolve_action_or_decision_blockers(
                    request.rental_case_id,
                    decided_at,
                    origin_entity_type="workflow_action",
                    origin_entity_id=action.workflow_action_id,
                )
            )
            return WorkflowActionApprovalResult(
                rental_case_id=request.rental_case_id,
                approval_request_id=request.approval_request_id,
                workflow_action_id=action.workflow_action_id,
                approval_status=approval.status,
                action_status_before=action_status_before,
                action_status_after=action.status,
                case_revision_before=snapshot.rental_case.case_revision,
                case_revision_after=snapshot.rental_case.case_revision,
                audit_event_ids=tuple(audit_event_ids),
                resolved_blocker_ids=resolved_blocker_ids,
            )

        action = self._replace_by_id(
            self.workflow_actions.setdefault(request.rental_case_id, []),
            action.workflow_action_id,
            "workflow_action_id",
            lambda value: replace(value, status=WORKFLOW_ACTION_STATUS_CANCELLED, updated_at=decided_at),
        )
        resolved_blocker_ids = tuple(
            self._resolve_action_or_decision_blockers(
                request.rental_case_id,
                decided_at,
                origin_entity_type="workflow_action",
                origin_entity_id=action.workflow_action_id,
            )
        )
        audit_event_ids = (
            self.create_workflow_event(
                rental_case_id=request.rental_case_id,
                event_type_code="approval_decided",
                source_type="orchestration_repository",
                source_reference=f"approval:{request.approval_request_id}",
                actor_type=request.actor_type,
                actor_reference=request.actor_reference,
                occurred_at=decided_at,
                structured_payload={
                    "approval_request_id": request.approval_request_id,
                    "target_entity_type": "workflow_action",
                    "target_entity_id": action.workflow_action_id,
                    "status_before": "open",
                    "status_after": approval.status,
                },
                event_identity_key=f"approval:action:rejected:{request.approval_request_id}:{request.expected_case_revision}",
            ).workflow_event_id,
            self.create_workflow_event(
                rental_case_id=request.rental_case_id,
                event_type_code="workflow_action_status_changed",
                source_type="orchestration_repository",
                source_reference=f"workflow_action:{action.workflow_action_id}",
                actor_type=request.actor_type,
                actor_reference=request.actor_reference,
                occurred_at=decided_at,
                structured_payload={
                    "workflow_action_id": action.workflow_action_id,
                    "status_before": action_status_before,
                    "status_after": WORKFLOW_ACTION_STATUS_CANCELLED,
                },
                event_identity_key=f"workflow_action:cancelled:{action.workflow_action_id}:{request.expected_case_revision}",
            ).workflow_event_id,
        )
        return WorkflowActionApprovalResult(
            rental_case_id=request.rental_case_id,
            approval_request_id=request.approval_request_id,
            workflow_action_id=action.workflow_action_id,
            approval_status=approval.status,
            action_status_before=action_status_before,
            action_status_after=action.status,
            case_revision_before=snapshot.rental_case.case_revision,
            case_revision_after=snapshot.rental_case.case_revision,
            audit_event_ids=audit_event_ids,
            resolved_blocker_ids=resolved_blocker_ids,
        )

    def commit_proposed_case_change_resolution(
        self,
        request: ProposedCaseChangeResolutionInput,
    ) -> ProposedCaseChangeResolutionResult:
        snapshot = self.load_case_snapshot(request.rental_case_id)
        if snapshot is None:
            return ProposedCaseChangeResolutionResult(
                rental_case_id=request.rental_case_id,
                proposed_case_change_id=request.proposed_case_change_id,
                resulting_status="rejected",
                case_revision_before=request.expected_case_revision,
                case_revision_after=request.expected_case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_CASE_NOT_FOUND,),
            )
        if snapshot.rental_case.case_revision != request.expected_case_revision:
            return ProposedCaseChangeResolutionResult(
                rental_case_id=request.rental_case_id,
                proposed_case_change_id=request.proposed_case_change_id,
                resulting_status="rejected",
                case_revision_before=snapshot.rental_case.case_revision,
                case_revision_after=snapshot.rental_case.case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_STALE_CASE_REVISION,),
            )
        change = snapshot.find_proposed_change(request.proposed_case_change_id)
        if change is None:
            return ProposedCaseChangeResolutionResult(
                rental_case_id=request.rental_case_id,
                proposed_case_change_id=request.proposed_case_change_id,
                resulting_status="rejected",
                case_revision_before=snapshot.rental_case.case_revision,
                case_revision_after=snapshot.rental_case.case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_PROPOSED_CHANGE_NOT_RESOLVABLE,),
            )
        if change.status in {PROPOSED_CHANGE_STATUS_ACCEPTED, PROPOSED_CHANGE_STATUS_REJECTED}:
            target_status = "accepted" if change.status == PROPOSED_CHANGE_STATUS_ACCEPTED else "rejected"
            return ProposedCaseChangeResolutionResult(
                rental_case_id=request.rental_case_id,
                proposed_case_change_id=request.proposed_case_change_id,
                resulting_status=target_status,
                case_revision_before=snapshot.rental_case.case_revision,
                case_revision_after=snapshot.rental_case.case_revision,
            )
        decided_at = request.decided_at or current_timestamp()
        audit_event_ids: list[int] = []
        artifact_ids: list[int] = []
        superseded_action_ids: list[int] = []
        updated_fact_id: int | None = None
        case_revision_after = snapshot.rental_case.case_revision
        if request.decision == ORCHESTRATION_DECISION_APPROVED:
            if change.review_posture == "approval_required" and not any(
                approval.status == APPROVAL_REQUEST_STATUS_APPROVED
                and approval.target_entity_type == "proposed_case_change"
                and (
                    approval.target_entity_id == change.proposed_case_change_id
                    or approval.target_entity_reference == f"proposed_change:{change.proposed_case_change_id}"
                )
                for approval in snapshot.approval_requests
            ):
                return ProposedCaseChangeResolutionResult(
                    rental_case_id=request.rental_case_id,
                    proposed_case_change_id=request.proposed_case_change_id,
                    resulting_status="rejected",
                    case_revision_before=snapshot.rental_case.case_revision,
                    case_revision_after=snapshot.rental_case.case_revision,
                    failure_codes=(ORCHESTRATION_FAILURE_APPROVAL_REQUIRED,),
                )
            final_value_payload = request.final_value_payload if request.final_value_payload is not None else change.proposed_value_payload
            if change.change_kind in {"active_event_window", "date_change"}:
                if not isinstance(final_value_payload, dict):
                    return ProposedCaseChangeResolutionResult(
                        rental_case_id=request.rental_case_id,
                        proposed_case_change_id=request.proposed_case_change_id,
                        resulting_status="rejected",
                        case_revision_before=snapshot.rental_case.case_revision,
                        case_revision_after=snapshot.rental_case.case_revision,
                        failure_codes=(ORCHESTRATION_FAILURE_PROPOSED_CHANGE_RESOLUTION_FAILED,),
                    )
                updated_case = self.update_rental_case_schedule(
                    rental_case_id=request.rental_case_id,
                    expected_case_revision=request.expected_case_revision,
                    active_event_start=final_value_payload.get("start"),
                    active_event_end=final_value_payload.get("end"),
                    updated_at=decided_at,
                )
                case_revision_after = updated_case.case_revision
                audit_event_ids.append(
                    self.create_workflow_event(
                        rental_case_id=request.rental_case_id,
                        event_type_code="case_fact_changed",
                        source_type="orchestration_repository",
                        source_reference=change.source_reference or f"proposed_change:{change.proposed_case_change_id}",
                        actor_type=request.actor_type,
                        actor_reference=request.actor_reference,
                        occurred_at=decided_at,
                        structured_payload={
                            "field_code": change.change_kind,
                            "case_revision_before": request.expected_case_revision,
                            "case_revision_after": updated_case.case_revision,
                            "resolution_basis": "accepted_proposed_case_change",
                        },
                        event_identity_key=f"case_fact:schedule:{change.proposed_case_change_id}:{request.expected_case_revision}",
                    ).workflow_event_id
                )
            else:
                updated_case = self.increment_case_revision(
                    rental_case_id=request.rental_case_id,
                    expected_case_revision=request.expected_case_revision,
                    updated_at=decided_at,
                )
                case_revision_after = updated_case.case_revision
                fact = self.upsert_rental_case_fact(
                    rental_case_id=request.rental_case_id,
                    field_code=change.change_kind,
                    domain_code=change.domain_code,
                    value_payload=final_value_payload,
                    source_reference=change.source_reference or f"proposed_change:{change.proposed_case_change_id}",
                    established_case_revision=updated_case.case_revision,
                    timestamp=decided_at,
                )
                updated_fact_id = fact.rental_case_fact_id
                audit_event_ids.append(
                    self.create_workflow_event(
                        rental_case_id=request.rental_case_id,
                        event_type_code="case_fact_changed",
                        source_type="orchestration_repository",
                        source_reference=change.source_reference or f"proposed_change:{change.proposed_case_change_id}",
                        actor_type=request.actor_type,
                        actor_reference=request.actor_reference,
                        occurred_at=decided_at,
                        structured_payload={
                            "field_code": fact.field_code,
                            "rental_case_fact_id": fact.rental_case_fact_id,
                            "case_revision_before": request.expected_case_revision,
                            "case_revision_after": updated_case.case_revision,
                            "resolution_basis": "accepted_proposed_case_change",
                        },
                        event_identity_key=f"case_fact:mutation:{change.proposed_case_change_id}:{request.expected_case_revision}",
                    ).workflow_event_id
                )
            self.resolve_proposed_change(
                rental_case_id=request.rental_case_id,
                proposed_case_change_id=request.proposed_case_change_id,
                status=PROPOSED_CHANGE_STATUS_ACCEPTED,
                final_value_payload=final_value_payload,
                accepted_at=decided_at,
            )
            artifact_ids.extend(self._mark_dependent_artifacts_stale(request.rental_case_id, case_revision_after, decided_at))
            superseded_action_ids.extend(self._supersede_stale_actions(request.rental_case_id, case_revision_after, decided_at))
            audit_event_ids.append(
                self.create_workflow_event(
                    rental_case_id=request.rental_case_id,
                    event_type_code="proposed_case_change_accepted",
                    source_type="orchestration_repository",
                    source_reference=f"proposed_change:{request.proposed_case_change_id}",
                    actor_type=request.actor_type,
                    actor_reference=request.actor_reference,
                    occurred_at=decided_at,
                    structured_payload={
                        "proposed_case_change_id": request.proposed_case_change_id,
                        "case_revision_before": request.expected_case_revision,
                        "case_revision_after": case_revision_after,
                    },
                    event_identity_key=f"proposed_change:accepted:{request.proposed_case_change_id}:{request.expected_case_revision}",
                ).workflow_event_id
            )
            resolved_blockers = self._resolve_action_or_decision_blockers(
                request.rental_case_id,
                decided_at,
                origin_entity_type="proposed_case_change",
                origin_entity_id=request.proposed_case_change_id,
            )
            if resolved_blockers:
                audit_event_ids.append(
                    self.create_workflow_event(
                        rental_case_id=request.rental_case_id,
                        event_type_code="blocker_resolved",
                        source_type="orchestration_repository",
                        source_reference=f"proposed_change:{request.proposed_case_change_id}",
                        actor_type=request.actor_type,
                        actor_reference=request.actor_reference,
                        occurred_at=decided_at,
                        structured_payload={"resolved_blocker_ids": resolved_blockers},
                        event_identity_key=f"blocker:resolved:proposed_change:{request.proposed_case_change_id}:{request.expected_case_revision}",
                    ).workflow_event_id
                )
            return ProposedCaseChangeResolutionResult(
                rental_case_id=request.rental_case_id,
                proposed_case_change_id=request.proposed_case_change_id,
                resulting_status="accepted",
                case_revision_before=request.expected_case_revision,
                case_revision_after=case_revision_after,
                updated_rental_case_fact_id=updated_fact_id,
                audit_event_ids=tuple(audit_event_ids),
                artifact_freshness_changed_ids=tuple(artifact_ids),
                superseded_action_ids=tuple(superseded_action_ids),
            )

        self.resolve_proposed_change(
            rental_case_id=request.rental_case_id,
            proposed_case_change_id=request.proposed_case_change_id,
            status=PROPOSED_CHANGE_STATUS_REJECTED,
            final_value_payload=change.final_value_payload,
            accepted_at=None,
        )
        resolved_blockers = self._resolve_action_or_decision_blockers(
            request.rental_case_id,
            decided_at,
            origin_entity_type="proposed_case_change",
            origin_entity_id=request.proposed_case_change_id,
        )
        audit_event_ids.append(
            self.create_workflow_event(
                rental_case_id=request.rental_case_id,
                event_type_code="proposed_case_change_rejected",
                source_type="orchestration_repository",
                source_reference=f"proposed_change:{request.proposed_case_change_id}",
                actor_type=request.actor_type,
                actor_reference=request.actor_reference,
                occurred_at=decided_at,
                structured_payload={
                    "proposed_case_change_id": request.proposed_case_change_id,
                    "resolved_blocker_ids": resolved_blockers,
                },
                event_identity_key=f"proposed_change:rejected:{request.proposed_case_change_id}:{request.expected_case_revision}",
            ).workflow_event_id
        )
        return ProposedCaseChangeResolutionResult(
            rental_case_id=request.rental_case_id,
            proposed_case_change_id=request.proposed_case_change_id,
            resulting_status="rejected",
            case_revision_before=request.expected_case_revision,
            case_revision_after=request.expected_case_revision,
            audit_event_ids=tuple(audit_event_ids),
        )

    def _replace_by_id(
        self,
        collection: list[Any],
        entity_id: int,
        id_field: str,
        replace_fn: Any,
    ) -> Any:
        for index, value in enumerate(collection):
            if getattr(value, id_field) != entity_id:
                continue
            replacement = replace_fn(value)
            collection[index] = replacement
            return replacement
        raise ValueError(f"{id_field}_not_found")

    def _mark_dependent_artifacts_stale(
        self,
        rental_case_id: int,
        new_case_revision: int,
        updated_at: str,
    ) -> list[int]:
        changed: list[int] = []
        for artifact in self.artifacts.get(rental_case_id, ()):
            if artifact.derived_from_case_revision >= new_case_revision:
                continue
            if artifact.freshness_status not in {"current", "stale"}:
                continue
            target_status = "refresh_required" if artifact.artifact_type in {"proposal", "agreement", "internal_event_brief"} else ARTIFACT_FRESHNESS_STALE
            updated = self.update_artifact_freshness(
                rental_case_id=rental_case_id,
                artifact_reference_id=artifact.artifact_reference_id,
                freshness_status=target_status,
                updated_at=updated_at,
            )
            changed.append(updated.artifact_reference_id)
        return changed

    def _supersede_stale_actions(
        self,
        rental_case_id: int,
        new_case_revision: int,
        updated_at: str,
    ) -> list[int]:
        superseded: list[int] = []
        for action in self.workflow_actions.get(rental_case_id, ()):
            if action.status in {"succeeded", "failed", "cancelled", "superseded"}:
                continue
            if action.source_case_revision >= new_case_revision:
                continue
            updated = self.supersede_workflow_action(
                rental_case_id=rental_case_id,
                workflow_action_id=action.workflow_action_id,
                updated_at=updated_at,
            )
            superseded.append(updated.workflow_action_id)
        return superseded

    def _resolve_action_or_decision_blockers(
        self,
        rental_case_id: int,
        resolved_at: str,
        *,
        origin_entity_type: str,
        origin_entity_id: int,
    ) -> list[int]:
        resolved: list[int] = []
        for blocker in self.blockers.get(rental_case_id, ()):
            if blocker.status != "open":
                continue
            if blocker.origin_entity_type != origin_entity_type:
                continue
            if blocker.origin_entity_id != origin_entity_id:
                continue
            updated = self.resolve_blocker(
                rental_case_id=rental_case_id,
                blocker_id=blocker.blocker_id,
                resolved_at=resolved_at,
                resolution_reference="structured_resolution",
            )
            resolved.append(updated.blocker_id)
        return resolved


@dataclass
class SupabaseWorkflowOrchestrationRepository(SupabaseLifecycleRepository):
    query_runner: Callable[..., Any] = run_supabase_query

    def load_case_snapshot(self, rental_case_id: int) -> WorkflowOrchestrationCaseSnapshot | None:
        return self.load_case_core_snapshot_for_console(
            rental_case_id,
            include_workflow_events=True,
        )

    def load_case_core_snapshot_for_console(
        self,
        rental_case_id: int,
        *,
        include_workflow_events: bool = False,
    ) -> WorkflowOrchestrationCaseSnapshot | None:
        workflow_events_sql = "'[]'::json as workflow_events"
        if include_workflow_events:
            workflow_events_sql = f"""
  (
    select coalesce(json_agg(row_to_json(ev) order by ev.workflow_event_id), '[]'::json)
    from (
      select
        id as workflow_event_id,
        workflow_event_uuid::text as workflow_event_uuid,
        rental_case_id,
        event_type_code,
        source_type,
        occurred_at::text as occurred_at,
        recorded_at::text as recorded_at,
        structured_payload,
        source_reference,
        actor_type,
        actor_reference,
        event_identity_key,
        origin_metadata
      from public.workflow_events
      where rental_case_id = {rental_case_id}
      order by id
    ) ev
  ) as workflow_events
""".strip()
        sql = f"""
select
  (
    select row_to_json(rc)
    from (
      select
        id as rental_case_id,
        rental_case_uuid::text as rental_case_uuid,
        case_reference_code,
        lifecycle_state,
        case_revision,
        rental_type_code,
        commercial_summary_status,
        operational_summary_status,
        is_active,
        active_event_start::text as active_event_start,
        active_event_end::text as active_event_end,
        service_level_or_type,
        client_account_ref,
        primary_contact_ref,
        dormant_origin_state,
        resume_target_state,
        dormant_reason_code,
        dormant_review_at::text as dormant_review_at,
        current_proposal_artifact_id,
        current_agreement_artifact_id,
        created_at::text as created_at,
        updated_at::text as updated_at
      from public.rental_cases
      where id = {rental_case_id}
    ) rc
  ) as rental_case,
  (
    select coalesce(json_agg(row_to_json(f) order by f.rental_case_fact_id), '[]'::json)
    from (
      select
        id as rental_case_fact_id,
        rental_case_id,
        field_code,
        domain_code,
        value_payload,
        source_reference,
        established_case_revision,
        created_at::text as created_at,
        updated_at::text as updated_at
      from public.rental_case_facts
      where rental_case_id = {rental_case_id}
      order by id
    ) f
  ) as rental_case_facts,
  (
    select coalesce(json_agg(row_to_json(b) order by b.blocker_id), '[]'::json)
    from (
      select
        id as blocker_id,
        rental_case_id,
        blocker_type,
        blocked_subject_type,
        origin_entity_type,
        severity,
        status,
        resolution_condition_text,
        opened_at::text as opened_at,
        blocked_subject_id,
        blocked_subject_reference,
        origin_entity_id,
        origin_entity_reference,
        resolution_reference,
        supersedes_blocker_id,
        resolved_at::text as resolved_at
      from public.rental_case_blockers
      where rental_case_id = {rental_case_id}
      order by id
    ) b
  ) as blockers,
  (
    select coalesce(json_agg(row_to_json(r) order by r.requirement_id), '[]'::json)
    from (
      select
        id as requirement_id,
        rental_case_id,
        requirement_type,
        domain_code,
        applicability_basis,
        status,
        blocking_scope,
        created_at::text as created_at,
        owner_role,
        owner_reference,
        due_at::text as due_at,
        evidence_reference,
        waiver_case_decision_id,
        resolved_at::text as resolved_at
      from public.rental_case_requirements
      where rental_case_id = {rental_case_id}
      order by id
    ) r
  ) as requirements,
  (
    select coalesce(json_agg(row_to_json(q) order by q.open_question_id), '[]'::json)
    from (
      select
        id as open_question_id,
        rental_case_id,
        question_type,
        domain_code,
        human_question_text,
        blocking_scope,
        status,
        created_at::text as created_at,
        requested_from_role,
        proposed_answer_payload,
        source_reference,
        supersedes_open_question_id,
        resolved_at::text as resolved_at
      from public.rental_case_open_questions
      where rental_case_id = {rental_case_id}
      order by id
    ) q
  ) as open_questions,
  (
    select coalesce(json_agg(row_to_json(a) order by a.approval_request_id), '[]'::json)
    from (
      select
        id as approval_request_id,
        rental_case_id,
        target_entity_type,
        approval_type,
        reason_text,
        status,
        created_at::text as created_at,
        target_entity_id,
        target_entity_reference,
        evidence_reference_keys,
        required_approver_role,
        required_approver_reference,
        decision_payload,
        decided_at::text as decided_at,
        decided_by_reference,
        decision_notes,
        supersedes_approval_request_id,
        updated_at::text as updated_at
      from public.rental_case_approval_requests
      where rental_case_id = {rental_case_id}
      order by id
    ) a
  ) as approval_requests,
  (
    select coalesce(json_agg(row_to_json(pc) order by pc.proposed_case_change_id), '[]'::json)
    from (
      select
        id as proposed_case_change_id,
        rental_case_id,
        change_kind,
        domain_code,
        proposed_value_payload,
        status,
        detected_at::text as detected_at,
        prior_value_payload,
        source_reference,
        impact_classification,
        affected_domain_codes,
        review_posture,
        final_value_payload,
        supersedes_proposed_change_id,
        accepted_at::text as accepted_at,
        created_at::text as created_at,
        updated_at::text as updated_at
      from public.rental_case_proposed_changes
      where rental_case_id = {rental_case_id}
      order by id
    ) pc
  ) as proposed_changes,
  (
    select coalesce(json_agg(row_to_json(rr) order by rr.reschedule_request_id), '[]'::json)
    from (
      select
        id as reschedule_request_id,
        rental_case_id,
        current_active_date_snapshot,
        requested_date_payload,
        candidate_dates_payload,
        consequence_summary_payload,
        status,
        urgency_class,
        created_at::text as created_at,
        confirmed_proposed_change_id,
        confirmed_at::text as confirmed_at,
        updated_at::text as updated_at
      from public.rental_case_reschedule_requests
      where rental_case_id = {rental_case_id}
      order by id
    ) rr
  ) as reschedule_requests,
  (
    select coalesce(json_agg(row_to_json(cd) order by cd.case_decision_id), '[]'::json)
    from (
      select
        id as case_decision_id,
        rental_case_id,
        decision_type,
        domain_code,
        baseline_reference,
        proposed_value_payload,
        scope_key,
        scope_description,
        authority_basis,
        approval_posture,
        status,
        created_at::text as created_at,
        effective_value_payload,
        evidence_reference,
        approval_request_id,
        effective_at::text as effective_at,
        supersedes_case_decision_id,
        updated_at::text as updated_at
      from public.rental_case_decisions
      where rental_case_id = {rental_case_id}
      order by id
    ) cd
  ) as case_decisions,
  (
    select coalesce(json_agg(row_to_json(wa) order by wa.workflow_action_id), '[]'::json)
    from (
      select
        id as workflow_action_id,
        workflow_action_uuid::text as workflow_action_uuid,
        rental_case_id,
        action_type,
        action_category,
        target_adapter_code,
        reason_entity_type,
        approval_posture,
        status,
        semantic_subject_hash,
        source_case_revision,
        idempotency_key,
        structured_payload,
        reason_entity_id,
        reason_entity_reference,
        target_scope_key,
        due_at::text as due_at,
        supersedes_workflow_action_id,
        created_at::text as created_at,
        updated_at::text as updated_at
      from public.workflow_actions
      where rental_case_id = {rental_case_id}
      order by id
    ) wa
  ) as workflow_actions,
  (
    select coalesce(json_agg(row_to_json(ea) order by ea.workflow_action_id, ea.attempt_number), '[]'::json)
    from (
      select
        id as execution_attempt_id,
        workflow_execution_attempt_uuid::text as execution_attempt_uuid,
        workflow_action_id,
        rental_case_id,
        attempt_number,
        adapter_code,
        started_at::text as started_at,
        status,
        retry_eligible,
        response_snapshot,
        completed_at::text as completed_at,
        external_reference,
        failure_code
      from public.workflow_execution_attempts
      where rental_case_id = {rental_case_id}
      order by workflow_action_id, attempt_number
    ) ea
  ) as execution_attempts,
  (
    select coalesce(json_agg(row_to_json(fu) order by fu.follow_up_id), '[]'::json)
    from (
      select
        id as follow_up_id,
        rental_case_id,
        reason_code,
        due_at::text as due_at,
        urgency_level,
        attempt_count,
        status,
        semantic_identity_key,
        sequence_number,
        waiting_for_role,
        waiting_for_reference,
        cadence_policy_code,
        escalate_after,
        next_action_type,
        context_payload,
        created_at::text as created_at,
        updated_at::text as updated_at,
        completed_at::text as completed_at
      from public.rental_case_follow_ups
      where rental_case_id = {rental_case_id}
      order by id
    ) fu
  ) as follow_ups,
  (
    select coalesce(json_agg(row_to_json(m) order by m.milestone_id), '[]'::json)
    from (
      select
        id as milestone_id,
        rental_case_id,
        milestone_type,
        target_at::text as target_at,
        status,
        basis_reference,
        related_requirement_id,
        related_workflow_action_id,
        supersedes_milestone_id,
        created_at::text as created_at,
        updated_at::text as updated_at,
        completed_at::text as completed_at
      from public.rental_case_milestones
      where rental_case_id = {rental_case_id}
      order by id
    ) m
  ) as milestones,
  (
    select coalesce(json_agg(row_to_json(ar) order by ar.artifact_reference_id), '[]'::json)
    from (
      select
        id as artifact_reference_id,
        rental_case_id,
        artifact_type,
        derived_from_case_revision,
        freshness_status,
        storage_reference,
        external_reference,
        relevant_scope_fingerprint,
        last_generated_at::text as last_generated_at,
        last_synced_at::text as last_synced_at,
        supersedes_artifact_id,
        created_at::text as created_at,
        updated_at::text as updated_at
      from public.rental_case_artifacts
      where rental_case_id = {rental_case_id}
      order by id
    ) ar
  ) as artifacts,
  (
    select coalesce(json_agg(row_to_json(rp) order by rp.reasoning_projection_id), '[]'::json)
    from (
      select
        id as reasoning_projection_id,
        rental_case_id,
        reasoning_purpose,
        phase_7_context_contract_version,
        phase_8_workflow_contract_version,
        source_case_revision,
        authority_outcome_classification,
        projection_identity_key,
        reasoning_state_code,
        workflow_posture,
        effective_confidentiality_level,
        de_identification_required,
        personal_information_present,
        materially_affects_completeness,
        relevant_current_truth_item_ids,
        relevant_guidance_item_ids,
        relevant_historical_item_ids,
        conflict_codes,
        contamination_codes,
        unresolved_authority_codes,
        warning_codes,
        degraded_retrieval_summary,
        grounding_reference_keys,
        created_at::text as created_at
      from public.rental_case_reasoning_projections
      where rental_case_id = {rental_case_id}
      order by id
    ) rp
  ) as reasoning_projections,
  {workflow_events_sql};
""".strip()
        row = self.query_runner(sql, expect_json=True)["rows"][0]
        rental_case_row = row.get("rental_case")
        if rental_case_row is None:
            return None
        return WorkflowOrchestrationCaseSnapshot(
            rental_case=RentalCase(**rental_case_row),
            rental_case_facts=tuple(RentalCaseFact(**fact_row) for fact_row in row["rental_case_facts"]),
            blockers=tuple(Blocker(**blocker_row) for blocker_row in row["blockers"]),
            requirements=tuple(Requirement(**requirement_row) for requirement_row in row["requirements"]),
            open_questions=tuple(OpenQuestion(**question_row) for question_row in row["open_questions"]),
            approval_requests=tuple(_approval_from_row(approval_row) for approval_row in row["approval_requests"]),
            proposed_changes=tuple(_proposed_change_from_row(change_row) for change_row in row["proposed_changes"]),
            reschedule_requests=tuple(
                RescheduleRequest(
                    **{
                        **request_row,
                        "candidate_dates_payload": tuple(request_row["candidate_dates_payload"] or []),
                    }
                )
                for request_row in row["reschedule_requests"]
            ),
            case_decisions=tuple(CaseDecision(**decision_row) for decision_row in row["case_decisions"]),
            workflow_actions=tuple(WorkflowAction(**action_row) for action_row in row["workflow_actions"]),
            execution_attempts=tuple(ExecutionAttempt(**attempt_row) for attempt_row in row["execution_attempts"]),
            follow_ups=tuple(FollowUp(**follow_up_row) for follow_up_row in row["follow_ups"]),
            milestones=tuple(Milestone(**milestone_row) for milestone_row in row["milestones"]),
            artifacts=tuple(ArtifactReference(**artifact_row) for artifact_row in row["artifacts"]),
            reasoning_projections=tuple(
                _reasoning_projection_from_row(projection_row) for projection_row in row["reasoning_projections"]
            ),
            workflow_events=tuple(WorkflowEvent(**event_row) for event_row in row["workflow_events"]),
        )

    def load_workflow_events_for_console(
        self,
        rental_case_id: int,
        *,
        limit: int,
    ) -> tuple[tuple[WorkflowEvent, ...], int]:
        sql = f"""
select
  (
    select count(*)::int
    from public.workflow_events
    where rental_case_id = {rental_case_id}
  ) as workflow_event_total_count,
  (
    select coalesce(json_agg(row_to_json(ev) order by ev.workflow_event_id), '[]'::json)
    from (
      select
        id as workflow_event_id,
        workflow_event_uuid::text as workflow_event_uuid,
        rental_case_id,
        event_type_code,
        source_type,
        occurred_at::text as occurred_at,
        recorded_at::text as recorded_at,
        structured_payload,
        source_reference,
        actor_type,
        actor_reference,
        event_identity_key,
        origin_metadata
      from public.workflow_events
      where rental_case_id = {rental_case_id}
      order by id desc
      limit {limit}
    ) ev
  ) as workflow_events;
""".strip()
        row = self.query_runner(sql, expect_json=True)["rows"][0]
        events = tuple(WorkflowEvent(**event_row) for event_row in row["workflow_events"])
        return events, row["workflow_event_total_count"] or 0

    def list_execution_attempts(
        self,
        *,
        rental_case_id: int,
        workflow_action_id: int | None = None,
    ) -> tuple[ExecutionAttempt, ...]:
        action_clause = "" if workflow_action_id is None else f"and workflow_action_id = {workflow_action_id}"
        sql = f"""
select
  id as execution_attempt_id,
  workflow_execution_attempt_uuid::text as execution_attempt_uuid,
  workflow_action_id,
  rental_case_id,
  attempt_number,
  adapter_code,
  started_at::text as started_at,
  status,
  retry_eligible,
  response_snapshot,
  completed_at::text as completed_at,
  external_reference,
  failure_code
from public.workflow_execution_attempts
where rental_case_id = {rental_case_id}
  {action_clause}
order by workflow_action_id, attempt_number;
""".strip()
        return tuple(ExecutionAttempt(**row) for row in self.query_runner(sql, expect_json=True)["rows"])

    def list_ready_to_execute_actions(
        self,
        *,
        rental_case_id: int | None = None,
    ) -> tuple[WorkflowAction, ...]:
        case_clause = "" if rental_case_id is None else f"and rental_case_id = {rental_case_id}"
        sql = f"""
select
  id as workflow_action_id,
  workflow_action_uuid::text as workflow_action_uuid,
  rental_case_id,
  action_type,
  action_category,
  target_adapter_code,
  reason_entity_type,
  approval_posture,
  status,
  semantic_subject_hash,
  source_case_revision,
  idempotency_key,
  structured_payload,
  reason_entity_id,
  reason_entity_reference,
  target_scope_key,
  due_at::text as due_at,
  supersedes_workflow_action_id,
  created_at::text as created_at,
  updated_at::text as updated_at
from public.workflow_actions
where status = 'ready_to_execute'
  {case_clause}
order by due_at nulls first, id;
""".strip()
        return tuple(WorkflowAction(**row) for row in self.query_runner(sql, expect_json=True)["rows"])

    def list_follow_ups_for_evaluation(
        self,
        *,
        rental_case_id: int | None = None,
    ) -> tuple[FollowUp, ...]:
        case_clause = "" if rental_case_id is None else f"and rental_case_id = {rental_case_id}"
        sql = f"""
select
  id as follow_up_id,
  rental_case_id,
  reason_code,
  due_at::text as due_at,
  urgency_level,
  attempt_count,
  status,
  semantic_identity_key,
  sequence_number,
  waiting_for_role,
  waiting_for_reference,
  cadence_policy_code,
  escalate_after,
  next_action_type,
  context_payload,
  created_at::text as created_at,
  updated_at::text as updated_at,
  completed_at::text as completed_at
from public.rental_case_follow_ups
where status not in ('completed', 'cancelled')
  {case_clause}
order by due_at, id;
""".strip()
        return tuple(FollowUp(**row) for row in self.query_runner(sql, expect_json=True)["rows"])

    def upsert_follow_up(self, follow_up: FollowUp) -> FollowUp:
        sql = f"""
insert into public.rental_case_follow_ups (
  rental_case_id,
  reason_code,
  due_at,
  urgency_level,
  attempt_count,
  status,
  semantic_identity_key,
  sequence_number,
  waiting_for_role,
  waiting_for_reference,
  cadence_policy_code,
  escalate_after,
  next_action_type,
  context_payload,
  created_at,
  updated_at,
  completed_at
)
values (
  {follow_up.rental_case_id},
  {sql_text(follow_up.reason_code)},
  {_sql_timestamptz(follow_up.due_at)},
  {sql_text(follow_up.urgency_level)},
  {follow_up.attempt_count},
  {sql_text(follow_up.status)},
  {sql_text(follow_up.semantic_identity_key)},
  {follow_up.sequence_number},
  {sql_text(follow_up.waiting_for_role)},
  {sql_text(follow_up.waiting_for_reference)},
  {sql_text(follow_up.cadence_policy_code)},
  {_sql_int(follow_up.escalate_after)},
  {sql_text(follow_up.next_action_type)},
  {_sql_any_json(follow_up.context_payload)},
  {_sql_timestamptz(follow_up.created_at)},
  {_sql_timestamptz(follow_up.updated_at)},
  {_sql_timestamptz(follow_up.completed_at)}
)
on conflict (rental_case_id, semantic_identity_key)
where semantic_identity_key is not null
do update
set reason_code = excluded.reason_code,
    due_at = excluded.due_at,
    urgency_level = excluded.urgency_level,
    attempt_count = excluded.attempt_count,
    status = excluded.status,
    sequence_number = excluded.sequence_number,
    waiting_for_role = excluded.waiting_for_role,
    waiting_for_reference = excluded.waiting_for_reference,
    cadence_policy_code = excluded.cadence_policy_code,
    escalate_after = excluded.escalate_after,
    next_action_type = excluded.next_action_type,
    context_payload = excluded.context_payload,
    updated_at = excluded.updated_at,
    completed_at = excluded.completed_at
returning
  id as follow_up_id,
  rental_case_id,
  reason_code,
  due_at::text as due_at,
  urgency_level,
  attempt_count,
  status,
  semantic_identity_key,
  sequence_number,
  waiting_for_role,
  waiting_for_reference,
  cadence_policy_code,
  escalate_after,
  next_action_type,
  context_payload,
  created_at::text as created_at,
  updated_at::text as updated_at,
  completed_at::text as completed_at;
""".strip()
        return FollowUp(**self.query_runner(sql, expect_json=True)["rows"][0])

    def create_workflow_event(
        self,
        *,
        rental_case_id: int,
        event_type_code: str,
        source_type: str,
        source_reference: str | None,
        actor_type: str | None,
        actor_reference: str,
        occurred_at: str,
        structured_payload: dict[str, Any],
        event_identity_key: str,
    ) -> WorkflowEvent:
        sql = f"""
insert into public.workflow_events (
  rental_case_id,
  event_type_code,
  source_type,
  source_reference,
  actor_type,
  actor_reference,
  occurred_at,
  recorded_at,
  structured_payload,
  event_identity_key,
  origin_metadata
)
values (
  {rental_case_id},
  {sql_text(event_type_code)},
  {sql_text(source_type)},
  {sql_text(source_reference)},
  {sql_text(actor_type)},
  {sql_text(actor_reference)},
  {_sql_timestamptz(occurred_at)},
  {_sql_timestamptz(occurred_at)},
  {_sql_json(structured_payload)},
  {sql_text(event_identity_key)},
  {_sql_json({"phase": "8.5r"})}
)
on conflict (rental_case_id, event_identity_key) do nothing
returning
  id as workflow_event_id,
  workflow_event_uuid::text as workflow_event_uuid,
  rental_case_id,
  event_type_code,
  source_type,
  occurred_at::text as occurred_at,
  recorded_at::text as recorded_at,
  structured_payload,
  source_reference,
  actor_type,
  actor_reference,
  event_identity_key,
  origin_metadata;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        if rows:
            return WorkflowEvent(**rows[0])
        select_sql = f"""
select
  id as workflow_event_id,
  workflow_event_uuid::text as workflow_event_uuid,
  rental_case_id,
  event_type_code,
  source_type,
  occurred_at::text as occurred_at,
  recorded_at::text as recorded_at,
  structured_payload,
  source_reference,
  actor_type,
  actor_reference,
  event_identity_key,
  origin_metadata
from public.workflow_events
where rental_case_id = {rental_case_id}
  and event_identity_key = {sql_text(event_identity_key)}
limit 1;
""".strip()
        select_rows = self.query_runner(select_sql, expect_json=True)["rows"]
        if not select_rows:
            raise Phase8ContractError(
                error_category="mutation_failed",
                safe_message="The workflow event could not be created or reloaded.",
            )
        return WorkflowEvent(**select_rows[0])

    def create_blocker(self, blocker: Blocker) -> Blocker:
        existing = self._select_existing_open_blocker(blocker.rental_case_id, blocker.resolution_reference)
        if existing is not None:
            return existing
        sql = f"""
insert into public.rental_case_blockers (
  rental_case_id,
  blocker_type,
  blocked_subject_type,
  blocked_subject_id,
  blocked_subject_reference,
  origin_entity_type,
  origin_entity_id,
  origin_entity_reference,
  severity,
  status,
  resolution_condition_text,
  resolution_reference,
  supersedes_blocker_id,
  opened_at,
  resolved_at
)
values (
  {blocker.rental_case_id},
  {sql_text(blocker.blocker_type)},
  {sql_text(blocker.blocked_subject_type)},
  {_sql_int(blocker.blocked_subject_id)},
  {sql_text(blocker.blocked_subject_reference)},
  {sql_text(blocker.origin_entity_type)},
  {_sql_int(blocker.origin_entity_id)},
  {sql_text(blocker.origin_entity_reference)},
  {sql_text(blocker.severity)},
  {sql_text(blocker.status)},
  {sql_text(blocker.resolution_condition_text)},
  {sql_text(blocker.resolution_reference)},
  {_sql_int(blocker.supersedes_blocker_id)},
  {_sql_timestamptz(blocker.opened_at)},
  {_sql_timestamptz(blocker.resolved_at)}
)
returning
  id as blocker_id,
  rental_case_id,
  blocker_type,
  blocked_subject_type,
  origin_entity_type,
  severity,
  status,
  resolution_condition_text,
  opened_at::text as opened_at,
  blocked_subject_id,
  blocked_subject_reference,
  origin_entity_id,
  origin_entity_reference,
  resolution_reference,
  supersedes_blocker_id,
  resolved_at::text as resolved_at;
""".strip()
        return Blocker(**self.query_runner(sql, expect_json=True)["rows"][0])

    def resolve_blocker(self, *, rental_case_id: int, blocker_id: int, resolved_at: str, resolution_reference: str | None) -> Blocker:
        sql = f"""
update public.rental_case_blockers
set status = 'resolved',
    resolved_at = {_sql_timestamptz(resolved_at)},
    resolution_reference = coalesce({sql_text(resolution_reference)}, resolution_reference)
where id = {blocker_id}
  and rental_case_id = {rental_case_id}
returning
  id as blocker_id,
  rental_case_id,
  blocker_type,
  blocked_subject_type,
  origin_entity_type,
  severity,
  status,
  resolution_condition_text,
  opened_at::text as opened_at,
  blocked_subject_id,
  blocked_subject_reference,
  origin_entity_id,
  origin_entity_reference,
  resolution_reference,
  supersedes_blocker_id,
  resolved_at::text as resolved_at;
""".strip()
        return Blocker(**self.query_runner(sql, expect_json=True)["rows"][0])

    def create_approval_request(self, approval_request: ApprovalRequest) -> ApprovalRequest:
        existing = self._select_existing_open_approval(
            approval_request.rental_case_id,
            approval_request.required_approver_reference,
        )
        if existing is not None:
            return existing
        sql = f"""
insert into public.rental_case_approval_requests (
  rental_case_id,
  target_entity_type,
  target_entity_id,
  target_entity_reference,
  approval_type,
  reason_text,
  evidence_reference_keys,
  required_approver_role,
  required_approver_reference,
  status,
  decision_payload,
  decided_at,
  decided_by_reference,
  decision_notes,
  supersedes_approval_request_id
)
values (
  {approval_request.rental_case_id},
  {sql_text(approval_request.target_entity_type)},
  {_sql_int(approval_request.target_entity_id)},
  {sql_text(approval_request.target_entity_reference)},
  {sql_text(approval_request.approval_type)},
  {sql_text(approval_request.reason_text)},
  {_sql_text_array(approval_request.evidence_reference_keys)},
  {sql_text(approval_request.required_approver_role)},
  {sql_text(approval_request.required_approver_reference)},
  {sql_text(approval_request.status)},
  {_sql_any_json(approval_request.decision_payload)},
  {_sql_timestamptz(approval_request.decided_at)},
  {sql_text(approval_request.decided_by_reference)},
  {sql_text(approval_request.decision_notes)},
  {_sql_int(approval_request.supersedes_approval_request_id)}
)
returning
  id as approval_request_id,
  rental_case_id,
  target_entity_type,
  approval_type,
  reason_text,
  status,
  created_at::text as created_at,
  target_entity_id,
  target_entity_reference,
  evidence_reference_keys,
  required_approver_role,
  required_approver_reference,
  decision_payload,
  decided_at::text as decided_at,
  decided_by_reference,
  decision_notes,
  supersedes_approval_request_id,
  updated_at::text as updated_at;
""".strip()
        return _approval_from_row(self.query_runner(sql, expect_json=True)["rows"][0])

    def cancel_approval_request(
        self,
        *,
        rental_case_id: int,
        approval_request_id: int,
        decided_at: str,
        decision_notes: str | None,
    ) -> ApprovalRequest:
        sql = f"""
update public.rental_case_approval_requests
set status = 'cancelled',
    decided_at = {_sql_timestamptz(decided_at)},
    decision_notes = {sql_text(decision_notes)},
    updated_at = {_sql_timestamptz(decided_at)}
where id = {approval_request_id}
  and rental_case_id = {rental_case_id}
returning
  id as approval_request_id,
  rental_case_id,
  target_entity_type,
  approval_type,
  reason_text,
  status,
  created_at::text as created_at,
  target_entity_id,
  target_entity_reference,
  evidence_reference_keys,
  required_approver_role,
  required_approver_reference,
  decision_payload,
  decided_at::text as decided_at,
  decided_by_reference,
  decision_notes,
  supersedes_approval_request_id,
  updated_at::text as updated_at;
""".strip()
        return _approval_from_row(self.query_runner(sql, expect_json=True)["rows"][0])

    def decide_approval_request(
        self,
        *,
        rental_case_id: int,
        approval_request_id: int,
        status: str,
        decision_payload: Any,
        decided_at: str,
        decided_by_reference: str,
        decision_notes: str | None,
    ) -> ApprovalRequest:
        sql = f"""
update public.rental_case_approval_requests
set status = {sql_text(status)},
    decision_payload = {_sql_any_json(decision_payload)},
    decided_at = {_sql_timestamptz(decided_at)},
    decided_by_reference = {sql_text(decided_by_reference)},
    decision_notes = {sql_text(decision_notes)},
    updated_at = {_sql_timestamptz(decided_at)}
where id = {approval_request_id}
  and rental_case_id = {rental_case_id}
returning
  id as approval_request_id,
  rental_case_id,
  target_entity_type,
  approval_type,
  reason_text,
  status,
  created_at::text as created_at,
  target_entity_id,
  target_entity_reference,
  evidence_reference_keys,
  required_approver_role,
  required_approver_reference,
  decision_payload,
  decided_at::text as decided_at,
  decided_by_reference,
  decision_notes,
  supersedes_approval_request_id,
  updated_at::text as updated_at;
""".strip()
        return _approval_from_row(self.query_runner(sql, expect_json=True)["rows"][0])

    def create_workflow_action(self, workflow_action: WorkflowAction) -> WorkflowAction:
        existing = self._select_existing_active_action(
            workflow_action.rental_case_id,
            workflow_action.idempotency_key,
        )
        if existing is not None:
            return existing
        sql = f"""
insert into public.workflow_actions (
  rental_case_id,
  action_type,
  action_category,
  target_adapter_code,
  reason_entity_type,
  reason_entity_id,
  reason_entity_reference,
  structured_payload,
  approval_posture,
  status,
  semantic_subject_hash,
  source_case_revision,
  target_scope_key,
  idempotency_key,
  due_at,
  supersedes_workflow_action_id
)
values (
  {workflow_action.rental_case_id},
  {sql_text(workflow_action.action_type)},
  {sql_text(workflow_action.action_category)},
  {sql_text(workflow_action.target_adapter_code)},
  {sql_text(workflow_action.reason_entity_type)},
  {_sql_int(workflow_action.reason_entity_id)},
  {sql_text(workflow_action.reason_entity_reference)},
  {_sql_json(workflow_action.structured_payload)},
  {sql_text(workflow_action.approval_posture)},
  {sql_text(workflow_action.status)},
  {sql_text(workflow_action.semantic_subject_hash)},
  {workflow_action.source_case_revision},
  {sql_text(workflow_action.target_scope_key)},
  {sql_text(workflow_action.idempotency_key)},
  {_sql_timestamptz(workflow_action.due_at)},
  {_sql_int(workflow_action.supersedes_workflow_action_id)}
)
returning
  id as workflow_action_id,
  workflow_action_uuid::text as workflow_action_uuid,
  rental_case_id,
  action_type,
  action_category,
  target_adapter_code,
  reason_entity_type,
  approval_posture,
  status,
  semantic_subject_hash,
  source_case_revision,
  idempotency_key,
  structured_payload,
  reason_entity_id,
  reason_entity_reference,
  target_scope_key,
  due_at::text as due_at,
  supersedes_workflow_action_id,
  created_at::text as created_at,
  updated_at::text as updated_at;
""".strip()
        return WorkflowAction(**self.query_runner(sql, expect_json=True)["rows"][0])

    def start_workflow_action_execution(
        self,
        request: WorkflowActionExecutionRequest,
    ) -> WorkflowActionExecutionStartResult:
        sql = f"""
select *
from private.commit_phase8_workflow_action_execution_start(
  p_rental_case_id => {request.rental_case_id},
  p_workflow_action_id => {request.workflow_action_id},
  p_actor_type => {sql_text(request.actor_type)},
  p_actor_reference => {sql_text(request.actor_reference)},
  p_started_at => {_sql_timestamptz(request.started_at)}
);
""".strip()
        row = self.query_runner(sql, expect_json=True)["rows"][0]
        snapshot = self.load_case_snapshot(request.rental_case_id)
        workflow_action = None if snapshot is None else snapshot.find_workflow_action(request.workflow_action_id)
        execution_attempt = None
        if snapshot is not None and row.get("execution_attempt_id"):
            execution_attempt = snapshot.find_execution_attempt(row["execution_attempt_id"])
        return WorkflowActionExecutionStartResult(
            rental_case_id=row["rental_case_id"],
            workflow_action_id=row["workflow_action_id"],
            case_revision=row["case_revision"],
            action_status_before=row["action_status_before"],
            action_status_after=row["action_status_after"],
            audit_event_ids=tuple(row["audit_event_ids"] or []),
            execution_attempt_id=row["execution_attempt_id"],
            attempt_number=row["attempt_number"],
            workflow_action=workflow_action,
            execution_attempt=execution_attempt,
            failure_codes=_failure_codes_from_row(row),
        )

    def complete_workflow_action_execution(
        self,
        request: WorkflowActionExecutionCompletionRequest,
    ) -> WorkflowActionExecutionResult:
        sql = f"""
select *
from private.commit_phase8_workflow_action_execution_complete(
  p_rental_case_id => {request.rental_case_id},
  p_workflow_action_id => {request.workflow_action_id},
  p_execution_attempt_id => {request.execution_attempt_id},
  p_attempt_status => {sql_text(request.result.attempt_status)},
  p_response_snapshot => {_sql_any_json(request.result.response_snapshot)},
  p_retry_eligible => {_sql_bool(request.result.retry_eligible)},
  p_external_reference => {sql_text(request.result.external_reference)},
  p_failure_code => {sql_text(request.result.failure_code)},
  p_actor_type => {sql_text(request.actor_type)},
  p_actor_reference => {sql_text(request.actor_reference)},
  p_completed_at => {_sql_timestamptz(request.result.completed_at)}
);
""".strip()
        row = self.query_runner(sql, expect_json=True)["rows"][0]
        return WorkflowActionExecutionResult(
            rental_case_id=row["rental_case_id"],
            workflow_action_id=row["workflow_action_id"],
            case_revision=row["case_revision"],
            action_status_before=row["action_status_before"],
            action_status_after=row["action_status_after"],
            audit_event_ids=tuple(row["audit_event_ids"] or []),
            execution_attempt_id=row["execution_attempt_id"],
            attempt_status=row["attempt_status"],
            retry_eligible=bool(row["retry_eligible"]),
            external_reference=row["external_reference"],
            failure_codes=_failure_codes_from_row(row),
        )

    def commit_follow_up_status_update(
        self,
        request: FollowUpStatusUpdateRequest,
    ) -> FollowUpStatusUpdateResult:
        sql = f"""
select *
from private.commit_phase8_follow_up_status_update(
  p_rental_case_id => {request.rental_case_id},
  p_follow_up_id => {request.follow_up_id},
  p_target_status => {sql_text(request.target_status)},
  p_actor_type => {sql_text(request.actor_type)},
  p_actor_reference => {sql_text(request.actor_reference)},
  p_expected_current_status => {sql_text(request.expected_current_status)},
  p_attempt_count_delta => {request.attempt_count_delta},
  p_occurred_at => {_sql_timestamptz(request.occurred_at)},
  p_completed_at => {_sql_timestamptz(request.completed_at)}
);
""".strip()
        row = self.query_runner(sql, expect_json=True)["rows"][0]
        return FollowUpStatusUpdateResult(
            rental_case_id=row["rental_case_id"],
            follow_up_id=row["follow_up_id"],
            status_before=row["status_before"],
            status_after=row["status_after"],
            attempt_count_before=row["attempt_count_before"],
            attempt_count_after=row["attempt_count_after"],
            audit_event_ids=tuple(row["audit_event_ids"] or []),
            failure_codes=_failure_codes_from_row(row),
        )

    def supersede_workflow_action(
        self,
        *,
        rental_case_id: int,
        workflow_action_id: int,
        updated_at: str,
    ) -> WorkflowAction:
        sql = f"""
update public.workflow_actions
set status = 'superseded',
    updated_at = {_sql_timestamptz(updated_at)}
where id = {workflow_action_id}
  and rental_case_id = {rental_case_id}
returning
  id as workflow_action_id,
  workflow_action_uuid::text as workflow_action_uuid,
  rental_case_id,
  action_type,
  action_category,
  target_adapter_code,
  reason_entity_type,
  approval_posture,
  status,
  semantic_subject_hash,
  source_case_revision,
  idempotency_key,
  structured_payload,
  reason_entity_id,
  reason_entity_reference,
  target_scope_key,
  due_at::text as due_at,
  supersedes_workflow_action_id,
  created_at::text as created_at,
  updated_at::text as updated_at;
""".strip()
        return WorkflowAction(**self.query_runner(sql, expect_json=True)["rows"][0])

    def create_requirement(self, requirement: Requirement) -> Requirement:
        existing = self._select_existing_requirement(requirement.rental_case_id, requirement.requirement_type)
        if existing is not None:
            return existing
        sql = f"""
insert into public.rental_case_requirements (
  rental_case_id,
  requirement_type,
  domain_code,
  applicability_basis,
  owner_role,
  owner_reference,
  due_at,
  status,
  blocking_scope,
  evidence_reference,
  waiver_case_decision_id,
  resolved_at
)
values (
  {requirement.rental_case_id},
  {sql_text(requirement.requirement_type)},
  {sql_text(requirement.domain_code)},
  {sql_text(requirement.applicability_basis)},
  {sql_text(requirement.owner_role)},
  {sql_text(requirement.owner_reference)},
  {_sql_timestamptz(requirement.due_at)},
  {sql_text(requirement.status)},
  {sql_text(requirement.blocking_scope)},
  {sql_text(requirement.evidence_reference)},
  {_sql_int(requirement.waiver_case_decision_id)},
  {_sql_timestamptz(requirement.resolved_at)}
)
returning
  id as requirement_id,
  rental_case_id,
  requirement_type,
  domain_code,
  applicability_basis,
  status,
  blocking_scope,
  created_at::text as created_at,
  owner_role,
  owner_reference,
  due_at::text as due_at,
  evidence_reference,
  waiver_case_decision_id,
  resolved_at::text as resolved_at;
""".strip()
        return Requirement(**self.query_runner(sql, expect_json=True)["rows"][0])

    def activate_case_decision(
        self,
        *,
        rental_case_id: int,
        case_decision_id: int,
        approval_request_id: int | None,
        effective_value_payload: Any,
        effective_at: str,
        expected_case_revision: int,
    ) -> tuple[CaseDecision, RentalCase]:
        sql = f"""
begin;
update public.rental_cases
set case_revision = case_revision + 1,
    updated_at = {_sql_timestamptz(effective_at)}
where id = {rental_case_id}
  and case_revision = {expected_case_revision};
update public.rental_case_decisions
set status = 'active',
    effective_value_payload = {_sql_any_json(effective_value_payload)},
    approval_request_id = coalesce({_sql_int(approval_request_id)}, approval_request_id),
    effective_at = {_sql_timestamptz(effective_at)},
    updated_at = {_sql_timestamptz(effective_at)}
where id = {case_decision_id}
  and rental_case_id = {rental_case_id};
commit;
""".strip()
        self.query_runner(sql, expect_json=False)
        snapshot = self.load_case_snapshot(rental_case_id)
        if snapshot is None:
            raise ValueError("case_not_found")
        return snapshot.find_case_decision(case_decision_id), snapshot.rental_case

    def reject_case_decision(
        self,
        *,
        rental_case_id: int,
        case_decision_id: int,
        updated_at: str,
    ) -> CaseDecision:
        sql = f"""
update public.rental_case_decisions
set status = 'rejected',
    updated_at = {_sql_timestamptz(updated_at)}
where id = {case_decision_id}
  and rental_case_id = {rental_case_id}
returning
  id as case_decision_id,
  rental_case_id,
  decision_type,
  domain_code,
  baseline_reference,
  proposed_value_payload,
  scope_key,
  scope_description,
  authority_basis,
  approval_posture,
  status,
  created_at::text as created_at,
  effective_value_payload,
  evidence_reference,
  approval_request_id,
  effective_at::text as effective_at,
  supersedes_case_decision_id,
  updated_at::text as updated_at;
""".strip()
        return CaseDecision(**self.query_runner(sql, expect_json=True)["rows"][0])

    def resolve_proposed_change(
        self,
        *,
        rental_case_id: int,
        proposed_case_change_id: int,
        status: str,
        final_value_payload: Any,
        accepted_at: str | None,
    ) -> ProposedCaseChange:
        sql = f"""
update public.rental_case_proposed_changes
set status = {sql_text(status)},
    final_value_payload = case
      when {sql_text(status)} = 'accepted' then {_sql_any_json(final_value_payload)}
      else final_value_payload
    end,
    accepted_at = case
      when {sql_text(status)} = 'accepted' then {_sql_timestamptz(accepted_at)}
      else accepted_at
    end,
    updated_at = coalesce({_sql_timestamptz(accepted_at)}, timezone('utc', now()))
where id = {proposed_case_change_id}
  and rental_case_id = {rental_case_id}
returning
  id as proposed_case_change_id,
  rental_case_id,
  change_kind,
  domain_code,
  proposed_value_payload,
  status,
  detected_at::text as detected_at,
  prior_value_payload,
  source_reference,
  impact_classification,
  affected_domain_codes,
  review_posture,
  final_value_payload,
  supersedes_proposed_change_id,
  accepted_at::text as accepted_at,
  created_at::text as created_at,
  updated_at::text as updated_at;
""".strip()
        return _proposed_change_from_row(self.query_runner(sql, expect_json=True)["rows"][0])

    def upsert_rental_case_fact(
        self,
        *,
        rental_case_id: int,
        field_code: str,
        domain_code: str,
        value_payload: Any,
        source_reference: str,
        established_case_revision: int,
        timestamp: str,
    ) -> RentalCaseFact:
        sql = f"""
insert into public.rental_case_facts (
  rental_case_id,
  field_code,
  domain_code,
  value_payload,
  source_reference,
  established_case_revision,
  created_at,
  updated_at
)
values (
  {rental_case_id},
  {sql_text(field_code)},
  {sql_text(domain_code)},
  {_sql_any_json(value_payload)},
  {sql_text(source_reference)},
  {established_case_revision},
  {_sql_timestamptz(timestamp)},
  {_sql_timestamptz(timestamp)}
)
on conflict (rental_case_id, field_code) do update
set domain_code = excluded.domain_code,
    value_payload = excluded.value_payload,
    source_reference = excluded.source_reference,
    established_case_revision = excluded.established_case_revision,
    updated_at = excluded.updated_at
returning
  id as rental_case_fact_id,
  rental_case_id,
  field_code,
  domain_code,
  value_payload,
  source_reference,
  established_case_revision,
  created_at::text as created_at,
  updated_at::text as updated_at;
""".strip()
        return RentalCaseFact(**self.query_runner(sql, expect_json=True)["rows"][0])

    def update_rental_case_schedule(
        self,
        *,
        rental_case_id: int,
        expected_case_revision: int,
        active_event_start: str | None,
        active_event_end: str | None,
        updated_at: str,
    ) -> RentalCase:
        sql = f"""
update public.rental_cases
set case_revision = case_revision + 1,
    active_event_start = {_sql_timestamptz(active_event_start)},
    active_event_end = {_sql_timestamptz(active_event_end)},
    updated_at = {_sql_timestamptz(updated_at)}
where id = {rental_case_id}
  and case_revision = {expected_case_revision}
returning
  id as rental_case_id,
  rental_case_uuid::text as rental_case_uuid,
  case_reference_code,
  lifecycle_state,
  case_revision,
  rental_type_code,
  commercial_summary_status,
  operational_summary_status,
  is_active,
  active_event_start::text as active_event_start,
  active_event_end::text as active_event_end,
  service_level_or_type,
  client_account_ref,
  primary_contact_ref,
  dormant_origin_state,
  resume_target_state,
  dormant_reason_code,
  dormant_review_at::text as dormant_review_at,
  current_proposal_artifact_id,
  current_agreement_artifact_id,
  created_at::text as created_at,
  updated_at::text as updated_at;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        if not rows:
            raise ValueError("stale_case_revision")
        return RentalCase(**rows[0])

    def increment_case_revision(
        self,
        *,
        rental_case_id: int,
        expected_case_revision: int,
        updated_at: str,
    ) -> RentalCase:
        sql = f"""
update public.rental_cases
set case_revision = case_revision + 1,
    updated_at = {_sql_timestamptz(updated_at)}
where id = {rental_case_id}
  and case_revision = {expected_case_revision}
returning
  id as rental_case_id,
  rental_case_uuid::text as rental_case_uuid,
  case_reference_code,
  lifecycle_state,
  case_revision,
  rental_type_code,
  commercial_summary_status,
  operational_summary_status,
  is_active,
  active_event_start::text as active_event_start,
  active_event_end::text as active_event_end,
  service_level_or_type,
  client_account_ref,
  primary_contact_ref,
  dormant_origin_state,
  resume_target_state,
  dormant_reason_code,
  dormant_review_at::text as dormant_review_at,
  current_proposal_artifact_id,
  current_agreement_artifact_id,
  created_at::text as created_at,
  updated_at::text as updated_at;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        if not rows:
            raise ValueError("stale_case_revision")
        return RentalCase(**rows[0])

    def update_artifact_freshness(
        self,
        *,
        rental_case_id: int,
        artifact_reference_id: int,
        freshness_status: str,
        updated_at: str,
    ) -> ArtifactReference:
        sql = f"""
update public.rental_case_artifacts
set freshness_status = {sql_text(freshness_status)},
    updated_at = {_sql_timestamptz(updated_at)}
where id = {artifact_reference_id}
  and rental_case_id = {rental_case_id}
returning
  id as artifact_reference_id,
  rental_case_id,
  artifact_type,
  derived_from_case_revision,
  freshness_status,
  storage_reference,
  external_reference,
  relevant_scope_fingerprint,
  last_generated_at::text as last_generated_at,
  last_synced_at::text as last_synced_at,
  supersedes_artifact_id,
  created_at::text as created_at,
  updated_at::text as updated_at;
""".strip()
        return ArtifactReference(**self.query_runner(sql, expect_json=True)["rows"][0])

    def commit_case_decision_activation(
        self,
        request: CaseDecisionActivationRequest,
    ) -> CaseDecisionActivationResult:
        snapshot = self.load_case_snapshot(request.rental_case_id)
        if snapshot is None:
            return CaseDecisionActivationResult(
                rental_case_id=request.rental_case_id,
                case_decision_id=request.case_decision_id,
                approval_request_id=request.approval_request_id,
                previous_case_revision=request.expected_case_revision,
                new_case_revision=request.expected_case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_CASE_NOT_FOUND,),
            )
        if snapshot.rental_case.case_revision != request.expected_case_revision:
            return CaseDecisionActivationResult(
                rental_case_id=request.rental_case_id,
                case_decision_id=request.case_decision_id,
                approval_request_id=request.approval_request_id,
                previous_case_revision=snapshot.rental_case.case_revision,
                new_case_revision=snapshot.rental_case.case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_STALE_CASE_REVISION,),
            )
        approval = snapshot.find_approval_request(request.approval_request_id)
        decision = snapshot.find_case_decision(request.case_decision_id)
        if approval is None or decision is None:
            return CaseDecisionActivationResult(
                rental_case_id=request.rental_case_id,
                case_decision_id=request.case_decision_id,
                approval_request_id=request.approval_request_id,
                previous_case_revision=snapshot.rental_case.case_revision,
                new_case_revision=snapshot.rental_case.case_revision,
                failure_codes=(ORCHESTRATION_FAILURE_APPROVAL_TARGET_INVALID,),
            )
        target_entity_id = approval.target_entity_id
        if target_entity_id is None:
            target_entity_id = _reference_id_from_text(approval.target_entity_reference)
        if approval.target_entity_type != "case_decision" or target_entity_id != request.case_decision_id:
            failure_code = (
                ORCHESTRATION_FAILURE_APPROVAL_TARGET_INVALID
                if target_entity_id is None
                else ORCHESTRATION_FAILURE_APPROVAL_TARGET_MISMATCH
            )
            return CaseDecisionActivationResult(
                rental_case_id=request.rental_case_id,
                case_decision_id=request.case_decision_id,
                approval_request_id=request.approval_request_id,
                previous_case_revision=snapshot.rental_case.case_revision,
                new_case_revision=snapshot.rental_case.case_revision,
                failure_codes=(failure_code,),
            )
        sql = f"""
select *
from private.commit_phase8_case_decision_approval(
  p_rental_case_id => {request.rental_case_id},
  p_approval_request_id => {request.approval_request_id},
  p_decision => 'approved',
  p_expected_case_revision => {request.expected_case_revision},
  p_actor_type => {sql_text(request.actor_type)},
  p_actor_reference => {sql_text(request.actor_reference)},
  p_decision_payload => {_sql_any_json({"decision": ORCHESTRATION_DECISION_APPROVED})},
  p_decision_notes => null,
  p_decided_at => {_sql_timestamptz(request.effective_at)}
);
""".strip()
        row = self.query_runner(sql, expect_json=True)["rows"][0]
        return CaseDecisionActivationResult(
            rental_case_id=row["rental_case_id"],
            case_decision_id=row["activated_case_decision_id"] or request.case_decision_id,
            approval_request_id=row["approval_request_id"],
            previous_case_revision=row["case_revision_before"],
            new_case_revision=row["case_revision_after"],
            workflow_event_ids=tuple(row["audit_event_ids"] or []),
            artifact_freshness_changed_ids=tuple(row["artifact_freshness_changed_ids"] or []),
            superseded_action_ids=tuple(row["superseded_action_ids"] or []),
            failure_codes=_failure_codes_from_row(row),
        )

    def apply_case_decision_approval(
        self,
        request: ApprovalDecisionInput,
    ) -> ApprovalDecisionResult:
        sql = f"""
select *
from private.commit_phase8_case_decision_approval(
  p_rental_case_id => {request.rental_case_id},
  p_approval_request_id => {request.approval_request_id},
  p_decision => {sql_text(request.decision)},
  p_expected_case_revision => {request.expected_case_revision},
  p_actor_type => {sql_text(request.actor_type)},
  p_actor_reference => {sql_text(request.actor_reference)},
  p_decision_payload => {_sql_any_json(request.decision_payload)},
  p_decision_notes => {sql_text(request.decision_notes)},
  p_decided_at => {_sql_timestamptz(request.decided_at)}
);
""".strip()
        row = self.query_runner(sql, expect_json=True)["rows"][0]
        return ApprovalDecisionResult(
            rental_case_id=row["rental_case_id"],
            approval_request_id=row["approval_request_id"],
            approval_status=row["approval_status"],
            case_revision_before=row["case_revision_before"],
            case_revision_after=row["case_revision_after"],
            audit_event_ids=tuple(row["audit_event_ids"] or []),
            resolved_blocker_ids=tuple(row["resolved_blocker_ids"] or []),
            activated_case_decision_id=row["activated_case_decision_id"],
            rejected_case_decision_id=row["rejected_case_decision_id"],
            artifact_freshness_changed_ids=tuple(row["artifact_freshness_changed_ids"] or []),
            superseded_action_ids=tuple(row["superseded_action_ids"] or []),
            failure_codes=_failure_codes_from_row(row),
        )

    def apply_workflow_action_approval(
        self,
        request: ApprovalDecisionInput,
    ) -> WorkflowActionApprovalResult:
        sql = f"""
select *
from private.commit_phase8_workflow_action_approval(
  p_rental_case_id => {request.rental_case_id},
  p_approval_request_id => {request.approval_request_id},
  p_decision => {sql_text(request.decision)},
  p_expected_case_revision => {request.expected_case_revision},
  p_actor_type => {sql_text(request.actor_type)},
  p_actor_reference => {sql_text(request.actor_reference)},
  p_decision_payload => {_sql_any_json(request.decision_payload)},
  p_decision_notes => {sql_text(request.decision_notes)},
  p_decided_at => {_sql_timestamptz(request.decided_at)}
);
""".strip()
        row = self.query_runner(sql, expect_json=True)["rows"][0]
        workflow_action_id = row["workflow_action_id"]
        if workflow_action_id in (None, 0):
            snapshot = self.load_case_snapshot(request.rental_case_id)
            approval = None if snapshot is None else snapshot.find_approval_request(request.approval_request_id)
            workflow_action_id = (
                None
                if approval is None
                else approval.target_entity_id or _reference_id_from_text(approval.target_entity_reference)
            )
        return WorkflowActionApprovalResult(
            rental_case_id=row["rental_case_id"],
            approval_request_id=row["approval_request_id"],
            workflow_action_id=workflow_action_id or request.approval_request_id,
            approval_status=row["approval_status"],
            action_status_before=row["action_status_before"],
            action_status_after=row["action_status_after"],
            case_revision_before=row["case_revision_before"],
            case_revision_after=row["case_revision_after"],
            audit_event_ids=tuple(row["audit_event_ids"] or []),
            resolved_blocker_ids=tuple(row["resolved_blocker_ids"] or []),
            failure_codes=_failure_codes_from_row(row),
        )

    def commit_proposed_case_change_resolution(
        self,
        request: ProposedCaseChangeResolutionInput,
    ) -> ProposedCaseChangeResolutionResult:
        sql = f"""
select *
from private.commit_phase8_proposed_case_change_resolution(
  p_rental_case_id => {request.rental_case_id},
  p_proposed_case_change_id => {request.proposed_case_change_id},
  p_decision => {sql_text(request.decision)},
  p_expected_case_revision => {request.expected_case_revision},
  p_actor_type => {sql_text(request.actor_type)},
  p_actor_reference => {sql_text(request.actor_reference)},
  p_final_value_payload => {_sql_any_json(request.final_value_payload)},
  p_decision_notes => {sql_text(request.decision_notes)},
  p_decided_at => {_sql_timestamptz(request.decided_at)}
);
""".strip()
        row = self.query_runner(sql, expect_json=True)["rows"][0]
        return ProposedCaseChangeResolutionResult(
            rental_case_id=row["rental_case_id"],
            proposed_case_change_id=row["proposed_case_change_id"],
            resulting_status=row["resulting_status"],
            case_revision_before=row["case_revision_before"],
            case_revision_after=row["case_revision_after"],
            updated_rental_case_fact_id=row["updated_rental_case_fact_id"],
            audit_event_ids=tuple(row["audit_event_ids"] or []),
            artifact_freshness_changed_ids=tuple(row["artifact_freshness_changed_ids"] or []),
            superseded_action_ids=tuple(row["superseded_action_ids"] or []),
            failure_codes=_failure_codes_from_row(row),
        )

    def _load_rental_case_facts(self, rental_case_id: int) -> tuple[RentalCaseFact, ...]:
        sql = f"""
select
  id as rental_case_fact_id,
  rental_case_id,
  field_code,
  domain_code,
  value_payload,
  source_reference,
  established_case_revision,
  created_at::text as created_at,
  updated_at::text as updated_at
from public.rental_case_facts
where rental_case_id = {rental_case_id}
order by id;
""".strip()
        return tuple(RentalCaseFact(**row) for row in self.query_runner(sql, expect_json=True)["rows"])

    def _load_reschedule_requests(self, rental_case_id: int) -> tuple[RescheduleRequest, ...]:
        sql = f"""
select
  id as reschedule_request_id,
  rental_case_id,
  current_active_date_snapshot,
  requested_date_payload,
  candidate_dates_payload,
  consequence_summary_payload,
  status,
  urgency_class,
  created_at::text as created_at,
  confirmed_proposed_change_id,
  confirmed_at::text as confirmed_at,
  updated_at::text as updated_at
from public.rental_case_reschedule_requests
where rental_case_id = {rental_case_id}
order by id;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        return tuple(
            RescheduleRequest(
                **{
                    **row,
                    "candidate_dates_payload": tuple(row["candidate_dates_payload"] or []),
                }
            )
            for row in rows
        )

    def _load_execution_attempts(self, rental_case_id: int) -> tuple[ExecutionAttempt, ...]:
        sql = f"""
select
  id as execution_attempt_id,
  workflow_execution_attempt_uuid::text as execution_attempt_uuid,
  workflow_action_id,
  rental_case_id,
  attempt_number,
  adapter_code,
  started_at::text as started_at,
  status,
  retry_eligible,
  response_snapshot,
  completed_at::text as completed_at,
  external_reference,
  failure_code
from public.workflow_execution_attempts
where rental_case_id = {rental_case_id}
order by workflow_action_id, attempt_number;
""".strip()
        return tuple(ExecutionAttempt(**row) for row in self.query_runner(sql, expect_json=True)["rows"])

    def _load_follow_ups(self, rental_case_id: int) -> tuple[FollowUp, ...]:
        sql = f"""
select
  id as follow_up_id,
  rental_case_id,
  reason_code,
  due_at::text as due_at,
  urgency_level,
  attempt_count,
  status,
  semantic_identity_key,
  sequence_number,
  waiting_for_role,
  waiting_for_reference,
  cadence_policy_code,
  escalate_after,
  next_action_type,
  context_payload,
  created_at::text as created_at,
  updated_at::text as updated_at,
  completed_at::text as completed_at
from public.rental_case_follow_ups
where rental_case_id = {rental_case_id}
order by id;
""".strip()
        return tuple(FollowUp(**row) for row in self.query_runner(sql, expect_json=True)["rows"])

    def _load_milestones(self, rental_case_id: int) -> tuple[Milestone, ...]:
        sql = f"""
select
  id as milestone_id,
  rental_case_id,
  milestone_type,
  target_at::text as target_at,
  status,
  basis_reference,
  related_requirement_id,
  related_workflow_action_id,
  supersedes_milestone_id,
  created_at::text as created_at,
  updated_at::text as updated_at,
  completed_at::text as completed_at
from public.rental_case_milestones
where rental_case_id = {rental_case_id}
order by id;
""".strip()
        return tuple(Milestone(**row) for row in self.query_runner(sql, expect_json=True)["rows"])

    def _load_reasoning_projections(self, rental_case_id: int) -> tuple[WorkflowReasoningProjection, ...]:
        sql = f"""
select
  id as reasoning_projection_id,
  rental_case_id,
  reasoning_purpose,
  phase_7_context_contract_version,
  phase_8_workflow_contract_version,
  source_case_revision,
  authority_outcome_classification,
  projection_identity_key,
  reasoning_state_code,
  workflow_posture,
  effective_confidentiality_level,
  de_identification_required,
  personal_information_present,
  materially_affects_completeness,
  relevant_current_truth_item_ids,
  relevant_guidance_item_ids,
  relevant_historical_item_ids,
  conflict_codes,
  contamination_codes,
  unresolved_authority_codes,
  warning_codes,
  degraded_retrieval_summary,
  grounding_reference_keys,
  created_at::text as created_at
from public.rental_case_reasoning_projections
where rental_case_id = {rental_case_id}
order by id;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        return tuple(_reasoning_projection_from_row(row) for row in rows)

    def _select_existing_open_blocker(self, rental_case_id: int, resolution_reference: str | None) -> Blocker | None:
        if resolution_reference is None:
            return None
        sql = f"""
select
  id as blocker_id,
  rental_case_id,
  blocker_type,
  blocked_subject_type,
  origin_entity_type,
  severity,
  status,
  resolution_condition_text,
  opened_at::text as opened_at,
  blocked_subject_id,
  blocked_subject_reference,
  origin_entity_id,
  origin_entity_reference,
  resolution_reference,
  supersedes_blocker_id,
  resolved_at::text as resolved_at
from public.rental_case_blockers
where rental_case_id = {rental_case_id}
  and status = 'open'
  and resolution_reference = {sql_text(resolution_reference)}
limit 1;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        return None if not rows else Blocker(**rows[0])

    def _select_existing_open_approval(self, rental_case_id: int, required_approver_reference: str | None) -> ApprovalRequest | None:
        if required_approver_reference is None:
            return None
        sql = f"""
select
  id as approval_request_id,
  rental_case_id,
  target_entity_type,
  approval_type,
  reason_text,
  status,
  created_at::text as created_at,
  target_entity_id,
  target_entity_reference,
  evidence_reference_keys,
  required_approver_role,
  required_approver_reference,
  decision_payload,
  decided_at::text as decided_at,
  decided_by_reference,
  decision_notes,
  supersedes_approval_request_id,
  updated_at::text as updated_at
from public.rental_case_approval_requests
where rental_case_id = {rental_case_id}
  and status = 'open'
  and required_approver_reference = {sql_text(required_approver_reference)}
limit 1;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        return None if not rows else _approval_from_row(rows[0])

    def _select_existing_active_action(self, rental_case_id: int, idempotency_key: str) -> WorkflowAction | None:
        sql = f"""
select
  id as workflow_action_id,
  workflow_action_uuid::text as workflow_action_uuid,
  rental_case_id,
  action_type,
  action_category,
  target_adapter_code,
  reason_entity_type,
  approval_posture,
  status,
  semantic_subject_hash,
  source_case_revision,
  idempotency_key,
  structured_payload,
  reason_entity_id,
  reason_entity_reference,
  target_scope_key,
  due_at::text as due_at,
  supersedes_workflow_action_id,
  created_at::text as created_at,
  updated_at::text as updated_at
from public.workflow_actions
where rental_case_id = {rental_case_id}
  and idempotency_key = {sql_text(idempotency_key)}
  and status not in ('succeeded', 'failed', 'cancelled', 'superseded')
limit 1;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        return None if not rows else WorkflowAction(**rows[0])

    def _select_existing_requirement(self, rental_case_id: int, requirement_type: str) -> Requirement | None:
        sql = f"""
select
  id as requirement_id,
  rental_case_id,
  requirement_type,
  domain_code,
  applicability_basis,
  status,
  blocking_scope,
  created_at::text as created_at,
  owner_role,
  owner_reference,
  due_at::text as due_at,
  evidence_reference,
  waiver_case_decision_id,
  resolved_at::text as resolved_at
from public.rental_case_requirements
where rental_case_id = {rental_case_id}
  and requirement_type = {sql_text(requirement_type)}
  and status in ('required', 'in_progress', 'unresolved')
limit 1;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        return None if not rows else Requirement(**rows[0])


def _semantic_key_from_reference(reference: str | None) -> str | None:
    if reference is None or not reference.startswith("semantic:"):
        return None
    return reference.split("semantic:", 1)[1]


def _approval_from_row(row: dict[str, Any]) -> ApprovalRequest:
    return ApprovalRequest(
        **{
            **row,
            "evidence_reference_keys": tuple(row["evidence_reference_keys"] or []),
        }
    )


def _proposed_change_from_row(row: dict[str, Any]) -> ProposedCaseChange:
    return ProposedCaseChange(
        **{
            **row,
            "affected_domain_codes": tuple(row["affected_domain_codes"] or []),
        }
    )


def _reasoning_projection_from_row(row: dict[str, Any]) -> WorkflowReasoningProjection:
    return WorkflowReasoningProjection(
        **{
            **row,
            "relevant_current_truth_item_ids": tuple(row["relevant_current_truth_item_ids"] or []),
            "relevant_guidance_item_ids": tuple(row["relevant_guidance_item_ids"] or []),
            "relevant_historical_item_ids": tuple(row["relevant_historical_item_ids"] or []),
            "conflict_codes": tuple(row["conflict_codes"] or []),
            "contamination_codes": tuple(row["contamination_codes"] or []),
            "unresolved_authority_codes": tuple(row["unresolved_authority_codes"] or []),
            "warning_codes": tuple(row["warning_codes"] or []),
            "grounding_reference_keys": tuple(row["grounding_reference_keys"] or []),
        }
    )


def _failure_codes_from_row(row: dict[str, Any]) -> tuple[str, ...]:
    failure_code = row.get("failure_code")
    return () if not failure_code else (failure_code,)


def _find_conflicting_external_reference_attempt(
    attempts_by_case: dict[int, list[ExecutionAttempt]],
    *,
    external_reference: str | None,
    workflow_action_id: int,
    execution_attempt_id: int,
    rental_case_id: int,
) -> ExecutionAttempt | None:
    if external_reference is None:
        return None
    for case_id, attempts in attempts_by_case.items():
        for attempt in attempts:
            if attempt.external_reference != external_reference:
                continue
            if attempt.status != EXECUTION_ATTEMPT_STATUS_SUCCEEDED:
                continue
            if (
                case_id == rental_case_id
                and attempt.workflow_action_id == workflow_action_id
                and attempt.execution_attempt_id == execution_attempt_id
            ):
                continue
            return attempt
    return None


def _reference_id_from_text(reference: str | None) -> int | None:
    if reference is None:
        return None
    suffix = reference.rsplit(":", 1)[-1].strip()
    if not suffix.isdigit():
        return None
    return int(suffix)


def _sql_text_array(values: tuple[str, ...]) -> str:
    if not values:
        return "'{}'::text[]"
    serialized = ", ".join(sql_text(value) for value in values)
    return f"array[{serialized}]::text[]"


def _sql_any_json(value: Any) -> str:
    if value is None:
        return "null::jsonb"
    return f"{sql_text(json.dumps(value, sort_keys=True, ensure_ascii=True))}::jsonb"
