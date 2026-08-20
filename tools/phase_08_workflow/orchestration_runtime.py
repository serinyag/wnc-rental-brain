from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Callable

from .contracts import (
    ACTION_CATEGORY_APPROVAL,
    ACTION_CATEGORY_COMMUNICATION,
    ACTION_CATEGORY_COMPLIANCE,
    ACTION_CATEGORY_COORDINATION,
    ACTION_CATEGORY_FOLLOW_UP,
    ACTION_CATEGORY_INTERNAL_CONTROL,
    ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
    ACTION_TYPE_ESCALATE_COMPLIANCE_REVIEW,
    ACTION_TYPE_MARK_ARTIFACT_REFRESH_REQUIRED,
    ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
    ACTION_TYPE_SCHEDULE_FOLLOW_UP_REVIEW,
    APPROVAL_POSTURE_APPROVAL_REQUIRED,
    APPROVAL_POSTURE_AUTOMATIC_ALLOWED,
    APPROVAL_POSTURE_BLOCKED,
    APPROVAL_POSTURE_HUMAN_ONLY,
    APPROVAL_REQUEST_STATUS_APPROVED,
    APPROVAL_REQUEST_STATUS_OPEN,
    APPROVAL_REQUEST_STATUS_REJECTED,
    ARTIFACT_FRESHNESS_CURRENT,
    ARTIFACT_FRESHNESS_REFRESH_REQUIRED,
    ARTIFACT_FRESHNESS_STALE,
    ARTIFACT_TYPE_AGREEMENT,
    ARTIFACT_TYPE_CALENDAR_PROJECTION,
    ARTIFACT_TYPE_INTERNAL_EVENT_BRIEF,
    ARTIFACT_TYPE_PROPOSAL,
    ARTIFACT_TYPE_TASK_SURFACE_PROJECTION,
    BLOCKED_SUBJECT_TYPE_ACTION,
    BLOCKED_SUBJECT_TYPE_DECISION,
    BLOCKED_SUBJECT_TYPE_READINESS,
    BLOCKED_SUBJECT_TYPE_TRANSITION,
    BLOCKER_STATUS_OPEN,
    CASE_DECISION_STATUS_ACTIVE,
    CASE_DECISION_STATUS_PENDING_APPROVAL,
    CASE_DECISION_STATUS_PROPOSED,
    CHANGE_IMPACT_FUNDAMENTAL,
    CHANGE_IMPACT_MATERIAL,
    FOLLOW_UP_REASON_INQUIRY_MISSING_INFORMATION,
    FOLLOW_UP_STATUS_DUE,
    FOLLOW_UP_STATUS_ESCALATED,
    FOLLOW_UP_STATUS_OVERDUE,
    FOLLOW_UP_STATUS_SCHEDULED,
    OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION,
    OPEN_QUESTION_STATUS_OPEN,
    PROPOSED_CHANGE_STATUS_ACCEPTED,
    PROPOSED_CHANGE_STATUS_PROPOSED,
    PROPOSED_CHANGE_STATUS_REJECTED,
    PROPOSED_CHANGE_STATUS_UNDER_REVIEW,
    REQUIREMENT_STATUS_IN_PROGRESS,
    REQUIREMENT_STATUS_REQUIRED,
    REQUIREMENT_STATUS_UNRESOLVED,
    RESCHEDULE_STATUS_AWAITING_CLIENT_CONFIRMATION,
    RESCHEDULE_STATUS_EVALUATING,
    RESCHEDULE_STATUS_OFFERED,
    RESCHEDULE_STATUS_PROPOSED,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
    WORKFLOW_ACTION_STATUS_APPROVED,
    WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
    WORKFLOW_ACTION_STATUS_PROPOSED,
    WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
    ApprovalRequest,
    ArtifactReference,
    Blocker,
    CaseDecision,
    Requirement,
    WorkflowAction,
)
from .observation_contracts import RentalCaseFact
from .orchestration_repository import (
    InMemoryWorkflowOrchestrationRepository,
    WorkflowOrchestrationCaseSnapshot,
    WorkflowOrchestrationRepositoryProtocol,
)
from .orchestration_types import (
    ApprovalDecisionInput,
    ApprovalDecisionResult,
    ApprovalPlanChange,
    ArtifactFreshnessPlanChange,
    BlockerPlanChange,
    CaseDecisionActivationRequest,
    CaseFactMutationRequest,
    CaseFactMutationResult,
    ORCHESTRATION_DECISION_APPROVED,
    ORCHESTRATION_DECISION_REJECTED,
    ORCHESTRATION_FAILURE_ACTION_PAYLOAD_INVALID,
    ORCHESTRATION_FAILURE_APPROVAL_REQUIRED,
    ORCHESTRATION_FAILURE_APPROVAL_TARGET_INVALID,
    ORCHESTRATION_FAILURE_CASE_DECISION_CONFLICT,
    ORCHESTRATION_FAILURE_CASE_DECISION_NOT_ACTIVATABLE,
    ORCHESTRATION_FAILURE_CASE_NOT_FOUND,
    ORCHESTRATION_FAILURE_COMMIT_FAILED,
    ORCHESTRATION_FAILURE_INVALID_ENTITY_STATUS,
    ORCHESTRATION_FAILURE_PROPOSED_CHANGE_NOT_RESOLVABLE,
    ORCHESTRATION_FAILURE_STALE_CASE_REVISION,
    ORCHESTRATION_FAILURE_UNSUPPORTED_REQUIREMENT_MAPPING,
    ProposedCaseChangeResolutionInput,
    ProposedCaseChangeResolutionResult,
    RequirementPlanChange,
    WorkflowActionApprovalResult,
    WorkflowActionPlanChange,
    WorkflowOrchestrationContext,
    WorkflowOrchestrationPlan,
    WorkflowOrchestrationResult,
)
from .phase7_consumption_types import (
    WORKFLOW_REASONING_EFFECT_CONFIRMATION_REQUIRED,
    WORKFLOW_REASONING_EFFECT_CURRENT_AUTHORITY_MISSING,
    WORKFLOW_REASONING_EFFECT_DETERMINISTIC_RESTRICTION,
    WORKFLOW_REASONING_EFFECT_REQUIREMENT_CANDIDATE,
    WORKFLOW_REASONING_EFFECT_REVIEW_REQUIRED,
    WorkflowReasoningEffect,
)
from .phase7_workflow_consumer import derive_workflow_effects


RULE_MISSING_CLIENT_INFORMATION = "RULE_MISSING_CLIENT_INFORMATION"
RULE_INTERNAL_CONFIRMATION_REQUEST = "RULE_INTERNAL_CONFIRMATION_REQUEST"
RULE_AUTHORITY_GAP_BLOCK = "RULE_AUTHORITY_GAP_BLOCK"
RULE_CONFIRMATION_REQUIRED_BLOCK = "RULE_CONFIRMATION_REQUIRED_BLOCK"
RULE_DETERMINISTIC_RESTRICTION = "RULE_DETERMINISTIC_RESTRICTION"
RULE_CASE_DECISION_APPROVAL = "RULE_CASE_DECISION_APPROVAL"
RULE_CASE_DECISION_CONFLICT = "RULE_CASE_DECISION_CONFLICT"
RULE_PROPOSED_CHANGE_REVIEW = "RULE_PROPOSED_CHANGE_REVIEW"
RULE_RESCHEDULE_REVIEW = "RULE_RESCHEDULE_REVIEW"
RULE_DUE_FOLLOW_UP = "RULE_DUE_FOLLOW_UP"
RULE_COMPLIANCE_REQUIREMENT = "RULE_COMPLIANCE_REQUIREMENT"
RULE_ARTIFACT_REFRESH = "RULE_ARTIFACT_REFRESH"

MANAGED_BLOCKER_PREFIXES = (
    "blocker:question:",
    "blocker:authority:",
    "blocker:decision:",
    "blocker:change:",
    "blocker:conflict:",
)
MANAGED_APPROVAL_PREFIXES = ("approval:case_decision:", "approval:proposed_change:")
MANAGED_ACTION_TYPES = frozenset(
    {
        ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
        ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
        ACTION_TYPE_ESCALATE_COMPLIANCE_REVIEW,
        ACTION_TYPE_MARK_ARTIFACT_REFRESH_REQUIRED,
        ACTION_TYPE_SCHEDULE_FOLLOW_UP_REVIEW,
    }
)
REFRESHABLE_ARTIFACT_TYPES = frozenset(
    {
        ARTIFACT_TYPE_PROPOSAL,
        ARTIFACT_TYPE_AGREEMENT,
        ARTIFACT_TYPE_INTERNAL_EVENT_BRIEF,
        ARTIFACT_TYPE_TASK_SURFACE_PROJECTION,
        ARTIFACT_TYPE_CALENDAR_PROJECTION,
    }
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_workflow_orchestration_context(
    snapshot: WorkflowOrchestrationCaseSnapshot,
) -> WorkflowOrchestrationContext:
    current_projection_set = tuple(
        projection
        for projection in snapshot.reasoning_projections
        if projection.source_case_revision == snapshot.rental_case.case_revision
    )
    reasoning_effects = tuple(
        effect
        for projection in current_projection_set
        for effect in derive_workflow_effects(projection)
    )
    return WorkflowOrchestrationContext(
        rental_case_id=snapshot.rental_case.rental_case_id,
        evaluated_case_revision=snapshot.rental_case.case_revision,
        lifecycle_state=snapshot.rental_case.lifecycle_state,
        rental_case_facts=snapshot.rental_case_facts,
        blockers=snapshot.blockers,
        requirements=snapshot.requirements,
        open_questions=snapshot.open_questions,
        approval_requests=snapshot.approval_requests,
        proposed_changes=snapshot.proposed_changes,
        reschedule_requests=snapshot.reschedule_requests,
        case_decisions=snapshot.case_decisions,
        workflow_actions=snapshot.workflow_actions,
        follow_ups=snapshot.follow_ups,
        milestones=snapshot.milestones,
        artifacts=snapshot.artifacts,
        reasoning_projections=current_projection_set,
        reasoning_effects=reasoning_effects,
    )


def evaluate_workflow_orchestration(
    context: WorkflowOrchestrationContext,
    *,
    now: str | None = None,
) -> WorkflowOrchestrationPlan:
    current_time = now or _utc_now()
    blocker_changes: list[BlockerPlanChange] = []
    approval_changes: list[ApprovalPlanChange] = []
    action_changes: list[WorkflowActionPlanChange] = []
    requirement_changes: list[RequirementPlanChange] = []
    artifact_changes: list[ArtifactFreshnessPlanChange] = []
    evidence_keys: list[str] = []
    policy_codes: list[str] = []
    rule_codes: list[str] = []

    _apply_open_question_rules(
        context,
        blocker_changes,
        action_changes,
        evidence_keys,
        policy_codes,
        rule_codes,
    )
    _apply_reasoning_effect_rules(
        context,
        blocker_changes,
        action_changes,
        requirement_changes,
        evidence_keys,
        policy_codes,
        rule_codes,
    )
    _apply_case_decision_rules(
        context,
        blocker_changes,
        approval_changes,
        action_changes,
        evidence_keys,
        policy_codes,
        rule_codes,
    )
    _apply_proposed_change_rules(
        context,
        blocker_changes,
        approval_changes,
        action_changes,
        evidence_keys,
        policy_codes,
        rule_codes,
    )
    _apply_reschedule_rules(
        context,
        action_changes,
        evidence_keys,
        policy_codes,
        rule_codes,
    )
    _apply_follow_up_rules(
        context,
        action_changes,
        evidence_keys,
        policy_codes,
        rule_codes,
        current_time,
    )
    _apply_artifact_refresh_rules(
        context,
        artifact_changes,
        action_changes,
        policy_codes,
        rule_codes,
    )

    blocker_semantics = {change.semantic_issue_key for change in blocker_changes}
    approval_semantics = {change.semantic_approval_key for change in approval_changes}
    action_idempotency_keys = {change.idempotency_key for change in action_changes}

    blockers_to_resolve = tuple(
        _semantic_key_from_reference(blocker.resolution_reference)
        for blocker in context.blockers
        if blocker.status == BLOCKER_STATUS_OPEN
        and _semantic_key_from_reference(blocker.resolution_reference) is not None
        and _semantic_key_from_reference(blocker.resolution_reference) not in blocker_semantics
        and _is_managed_blocker_reference(blocker.resolution_reference)
    )
    approvals_to_cancel = tuple(
        _semantic_key_from_reference(approval.required_approver_reference)
        for approval in context.approval_requests
        if approval.status == APPROVAL_REQUEST_STATUS_OPEN
        and _semantic_key_from_reference(approval.required_approver_reference) is not None
        and _semantic_key_from_reference(approval.required_approver_reference) not in approval_semantics
        and _is_managed_approval_reference(approval.required_approver_reference)
    )
    actions_to_supersede = tuple(
        action.idempotency_key
        for action in context.workflow_actions
        if action.action_type in MANAGED_ACTION_TYPES
        and action.status not in {"succeeded", "failed", "cancelled", "superseded"}
        and action.idempotency_key not in action_idempotency_keys
    )

    plan_material = {
        "rental_case_id": context.rental_case_id,
        "evaluated_case_revision": context.evaluated_case_revision,
        "blockers": [change.semantic_issue_key for change in blocker_changes],
        "approvals": [change.semantic_approval_key for change in approval_changes],
        "actions": [change.idempotency_key for change in action_changes],
        "requirements": [change.requirement_type for change in requirement_changes],
        "artifacts": [change.artifact_reference_id for change in artifact_changes],
        "rule_codes": rule_codes,
    }
    plan_fingerprint = _hash_material(plan_material)
    return WorkflowOrchestrationPlan(
        rental_case_id=context.rental_case_id,
        evaluated_case_revision=context.evaluated_case_revision,
        proposed_blocker_creations=tuple(blocker_changes),
        blocker_semantic_keys_to_resolve=tuple(dict.fromkeys(blockers_to_resolve)),
        proposed_approval_creations=tuple(approval_changes),
        approval_semantic_keys_to_cancel=tuple(dict.fromkeys(approvals_to_cancel)),
        proposed_action_creations=tuple(action_changes),
        action_idempotency_keys_to_supersede=tuple(dict.fromkeys(actions_to_supersede)),
        proposed_requirement_creations=tuple(requirement_changes),
        artifact_freshness_updates=tuple(artifact_changes),
        evidence_reference_keys=tuple(dict.fromkeys(evidence_keys)),
        policy_codes=tuple(dict.fromkeys(policy_codes)),
        rule_codes=tuple(dict.fromkeys(rule_codes)),
        plan_fingerprint=plan_fingerprint,
    )


def apply_workflow_orchestration_plan(
    repository: WorkflowOrchestrationRepositoryProtocol,
    plan: WorkflowOrchestrationPlan,
    *,
    actor_reference: str,
    actor_type: str | None = "system",
    now: Callable[[], str] = _utc_now,
    loaded_snapshot: WorkflowOrchestrationCaseSnapshot | None = None,
) -> WorkflowOrchestrationResult:
    snapshot = loaded_snapshot or repository.load_case_snapshot(plan.rental_case_id)
    if snapshot is None:
        return WorkflowOrchestrationResult(
            rental_case_id=plan.rental_case_id,
            case_revision_before=plan.evaluated_case_revision,
            case_revision_after=plan.evaluated_case_revision,
            failure_codes=(ORCHESTRATION_FAILURE_CASE_NOT_FOUND,),
        )
    if snapshot.rental_case.case_revision != plan.evaluated_case_revision:
        return WorkflowOrchestrationResult(
            rental_case_id=plan.rental_case_id,
            case_revision_before=snapshot.rental_case.case_revision,
            case_revision_after=snapshot.rental_case.case_revision,
            failure_codes=(ORCHESTRATION_FAILURE_STALE_CASE_REVISION,),
        )

    timestamp = now()
    created_blocker_ids: list[int] = []
    resolved_blocker_ids: list[int] = []
    created_approval_ids: list[int] = []
    updated_approval_ids: list[int] = []
    created_action_ids: list[int] = []
    superseded_action_ids: list[int] = []
    created_requirement_ids: list[int] = []
    artifact_changed_ids: list[int] = []
    audit_event_ids: list[int] = []
    known_requirement_ids = {requirement.requirement_id for requirement in snapshot.requirements}
    known_open_blocker_keys = {
        blocker.resolution_reference.removeprefix("semantic:")
        for blocker in snapshot.blockers
        if blocker.status == BLOCKER_STATUS_OPEN
        and blocker.resolution_reference.startswith("semantic:")
    }
    known_open_approval_keys = {
        approval.required_approver_reference.removeprefix("semantic:")
        for approval in snapshot.approval_requests
        if approval.status == APPROVAL_REQUEST_STATUS_OPEN
        and approval.required_approver_reference is not None
        and approval.required_approver_reference.startswith("semantic:")
    }
    known_active_action_keys = {
        action.idempotency_key
        for action in snapshot.workflow_actions
        if snapshot.find_active_action_by_idempotency_key(action.idempotency_key) is not None
    }

    try:
        for change in plan.proposed_action_creations:
            _validate_action_payload(change.action_type, change.structured_payload)

        for change in plan.proposed_requirement_creations:
            requirement = repository.create_requirement(
                Requirement(
                    requirement_id=1,
                    rental_case_id=plan.rental_case_id,
                    requirement_type=change.requirement_type,
                    domain_code=change.domain_code,
                    applicability_basis=change.applicability_basis,
                    status=REQUIREMENT_STATUS_REQUIRED,
                    blocking_scope=change.blocking_scope,
                    created_at=timestamp,
                    owner_role=change.owner_role,
                    owner_reference=change.owner_reference,
                    due_at=change.due_at,
                    evidence_reference=change.evidence_reference,
                )
            )
            if (
                requirement.requirement_id not in created_requirement_ids
                and requirement.requirement_id not in known_requirement_ids
            ):
                created_requirement_ids.append(requirement.requirement_id)
                known_requirement_ids.add(requirement.requirement_id)
                audit_event_ids.append(
                    repository.create_workflow_event(
                        rental_case_id=plan.rental_case_id,
                        event_type_code="requirement_created",
                        source_type="orchestration_runtime",
                        source_reference=change.rule_code,
                        actor_type=actor_type,
                        actor_reference=actor_reference,
                        occurred_at=timestamp,
                        structured_payload={
                            "requirement_id": requirement.requirement_id,
                            "requirement_type": requirement.requirement_type,
                            "rule_code": change.rule_code,
                        },
                        event_identity_key=f"orchestration:requirement:create:{requirement.requirement_id}:{plan.evaluated_case_revision}",
                    ).workflow_event_id
                )

        for change in plan.proposed_blocker_creations:
            blocker = repository.create_blocker(
                Blocker(
                    blocker_id=1,
                    rental_case_id=plan.rental_case_id,
                    blocker_type=change.blocker_type,
                    blocked_subject_type=change.blocked_subject_type,
                    blocked_subject_id=change.blocked_subject_id,
                    blocked_subject_reference=change.blocked_subject_reference,
                    origin_entity_type=change.origin_entity_type,
                    origin_entity_id=change.origin_entity_id,
                    origin_entity_reference=change.origin_entity_reference,
                    severity=change.severity,
                    status=BLOCKER_STATUS_OPEN,
                    resolution_condition_text=change.resolution_condition_text,
                    resolution_reference=f"semantic:{change.semantic_issue_key}",
                    opened_at=timestamp,
                )
            )
            if change.semantic_issue_key not in known_open_blocker_keys and blocker.blocker_id not in created_blocker_ids:
                created_blocker_ids.append(blocker.blocker_id)
                known_open_blocker_keys.add(change.semantic_issue_key)
                audit_event_ids.append(
                    repository.create_workflow_event(
                        rental_case_id=plan.rental_case_id,
                        event_type_code="orchestration_blocker_created",
                        source_type="orchestration_runtime",
                        source_reference=change.rule_code,
                        actor_type=actor_type,
                        actor_reference=actor_reference,
                        occurred_at=timestamp,
                        structured_payload={
                            "semantic_issue_key": change.semantic_issue_key,
                            "rule_code": change.rule_code,
                        },
                        event_identity_key=f"orchestration:blocker:create:{change.semantic_issue_key}:{plan.evaluated_case_revision}",
                    ).workflow_event_id
                )

        for change in plan.proposed_approval_creations:
            approval = repository.create_approval_request(
                ApprovalRequest(
                    approval_request_id=1,
                    rental_case_id=plan.rental_case_id,
                    target_entity_type=change.target_entity_type,
                    target_entity_id=change.target_entity_id,
                    target_entity_reference=change.target_entity_reference,
                    approval_type=change.approval_type,
                    reason_text=change.reason_text,
                    evidence_reference_keys=change.evidence_reference_keys,
                    required_approver_role=change.required_approver_role,
                    required_approver_reference=f"semantic:{change.semantic_approval_key}",
                    status=APPROVAL_REQUEST_STATUS_OPEN,
                    created_at=timestamp,
                )
            )
            if change.semantic_approval_key not in known_open_approval_keys and approval.approval_request_id not in created_approval_ids:
                created_approval_ids.append(approval.approval_request_id)
                known_open_approval_keys.add(change.semantic_approval_key)
                audit_event_ids.append(
                    repository.create_workflow_event(
                        rental_case_id=plan.rental_case_id,
                        event_type_code="approval_request_created",
                        source_type="orchestration_runtime",
                        source_reference=change.rule_code,
                        actor_type=actor_type,
                        actor_reference=actor_reference,
                        occurred_at=timestamp,
                        structured_payload={
                            "approval_request_id": approval.approval_request_id,
                            "target_entity_type": approval.target_entity_type,
                            "target_entity_id": approval.target_entity_id,
                            "rule_code": change.rule_code,
                        },
                        event_identity_key=f"orchestration:approval:create:{approval.approval_request_id}:{plan.evaluated_case_revision}",
                    ).workflow_event_id
                )

        for change in plan.proposed_action_creations:
            status = _initial_action_status(change.approval_posture)
            action = repository.create_workflow_action(
                WorkflowAction(
                    workflow_action_id=1,
                    workflow_action_uuid="workflow-action",
                    rental_case_id=plan.rental_case_id,
                    action_type=change.action_type,
                    action_category=change.action_category,
                    target_adapter_code=change.target_adapter_code,
                    reason_entity_type=change.reason_entity_type,
                    reason_entity_id=change.reason_entity_id,
                    reason_entity_reference=change.reason_entity_reference,
                    approval_posture=change.approval_posture,
                    status=status,
                    semantic_subject_hash=change.semantic_subject_hash,
                    source_case_revision=change.source_case_revision,
                    idempotency_key=change.idempotency_key,
                    structured_payload=change.structured_payload,
                    target_scope_key=change.target_scope_key,
                    due_at=change.due_at,
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )
            if change.idempotency_key not in known_active_action_keys and action.workflow_action_id not in created_action_ids:
                created_action_ids.append(action.workflow_action_id)
                known_active_action_keys.add(change.idempotency_key)
                audit_event_ids.append(
                    repository.create_workflow_event(
                        rental_case_id=plan.rental_case_id,
                        event_type_code="workflow_action_created",
                        source_type="orchestration_runtime",
                        source_reference=change.rule_code,
                        actor_type=actor_type,
                        actor_reference=actor_reference,
                        occurred_at=timestamp,
                        structured_payload={
                            "workflow_action_id": action.workflow_action_id,
                            "action_type": action.action_type,
                            "approval_posture": action.approval_posture,
                            "status": action.status,
                            "rule_code": change.rule_code,
                        },
                        event_identity_key=f"orchestration:action:create:{action.workflow_action_id}:{plan.evaluated_case_revision}",
                    ).workflow_event_id
                )

        if (
            plan.blocker_semantic_keys_to_resolve
            or plan.approval_semantic_keys_to_cancel
            or plan.action_idempotency_keys_to_supersede
        ):
            refreshed_snapshot = repository.load_case_snapshot(plan.rental_case_id)
            if refreshed_snapshot is None:
                raise ValueError("case_not_found")

            for semantic_key in plan.blocker_semantic_keys_to_resolve:
                blocker = refreshed_snapshot.find_open_blocker_by_semantic_key(semantic_key)
                if blocker is None:
                    continue
                repository.resolve_blocker(
                    rental_case_id=plan.rental_case_id,
                    blocker_id=blocker.blocker_id,
                    resolved_at=timestamp,
                    resolution_reference=f"resolved:{semantic_key}",
                )
                resolved_blocker_ids.append(blocker.blocker_id)
                audit_event_ids.append(
                    repository.create_workflow_event(
                        rental_case_id=plan.rental_case_id,
                        event_type_code="blocker_resolved",
                        source_type="orchestration_runtime",
                        source_reference=semantic_key,
                        actor_type=actor_type,
                        actor_reference=actor_reference,
                        occurred_at=timestamp,
                        structured_payload={
                            "blocker_id": blocker.blocker_id,
                            "resolution_reference": f"resolved:{semantic_key}",
                        },
                        event_identity_key=f"orchestration:blocker:resolved:{blocker.blocker_id}:{plan.evaluated_case_revision}",
                    ).workflow_event_id
                )

            for semantic_key in plan.approval_semantic_keys_to_cancel:
                approval = refreshed_snapshot.find_open_approval_by_semantic_key(semantic_key)
                if approval is None:
                    continue
                repository.cancel_approval_request(
                    rental_case_id=plan.rental_case_id,
                    approval_request_id=approval.approval_request_id,
                    decided_at=timestamp,
                    decision_notes="Cancelled by orchestration reconciliation.",
                )
                updated_approval_ids.append(approval.approval_request_id)
                audit_event_ids.append(
                    repository.create_workflow_event(
                        rental_case_id=plan.rental_case_id,
                        event_type_code="approval_request_cancelled",
                        source_type="orchestration_runtime",
                        source_reference=semantic_key,
                        actor_type=actor_type,
                        actor_reference=actor_reference,
                        occurred_at=timestamp,
                        structured_payload={
                            "approval_request_id": approval.approval_request_id,
                            "status_after": "cancelled",
                        },
                        event_identity_key=f"orchestration:approval:cancel:{approval.approval_request_id}:{plan.evaluated_case_revision}",
                    ).workflow_event_id
                )

            for idempotency_key in plan.action_idempotency_keys_to_supersede:
                action = refreshed_snapshot.find_active_action_by_idempotency_key(idempotency_key)
                if action is None:
                    continue
                repository.supersede_workflow_action(
                    rental_case_id=plan.rental_case_id,
                    workflow_action_id=action.workflow_action_id,
                    updated_at=timestamp,
                )
                superseded_action_ids.append(action.workflow_action_id)
                audit_event_ids.append(
                    repository.create_workflow_event(
                        rental_case_id=plan.rental_case_id,
                        event_type_code="workflow_action_superseded",
                        source_type="orchestration_runtime",
                        source_reference=idempotency_key,
                        actor_type=actor_type,
                        actor_reference=actor_reference,
                        occurred_at=timestamp,
                        structured_payload={
                            "workflow_action_id": action.workflow_action_id,
                            "idempotency_key": idempotency_key,
                        },
                        event_identity_key=f"orchestration:action:supersede:{action.workflow_action_id}:{plan.evaluated_case_revision}",
                    ).workflow_event_id
                )

        for change in plan.artifact_freshness_updates:
            artifact = repository.update_artifact_freshness(
                rental_case_id=plan.rental_case_id,
                artifact_reference_id=change.artifact_reference_id,
                freshness_status=change.target_freshness_status,
                updated_at=timestamp,
            )
            artifact_changed_ids.append(artifact.artifact_reference_id)
            audit_event_ids.append(
                repository.create_workflow_event(
                    rental_case_id=plan.rental_case_id,
                    event_type_code="artifact_freshness_changed",
                    source_type="orchestration_runtime",
                    source_reference=change.reason_code,
                    actor_type=actor_type,
                    actor_reference=actor_reference,
                    occurred_at=timestamp,
                    structured_payload={
                        "artifact_reference_id": artifact.artifact_reference_id,
                        "freshness_status": change.target_freshness_status,
                        "reason_code": change.reason_code,
                    },
                    event_identity_key=f"orchestration:artifact:freshness:{artifact.artifact_reference_id}:{plan.evaluated_case_revision}",
                ).workflow_event_id
            )
    except Exception:
        return WorkflowOrchestrationResult(
            rental_case_id=plan.rental_case_id,
            case_revision_before=snapshot.rental_case.case_revision,
            case_revision_after=snapshot.rental_case.case_revision,
            created_blocker_ids=tuple(created_blocker_ids),
            resolved_blocker_ids=tuple(resolved_blocker_ids),
            created_approval_ids=tuple(created_approval_ids),
            updated_approval_ids=tuple(updated_approval_ids),
            created_action_ids=tuple(created_action_ids),
            superseded_action_ids=tuple(superseded_action_ids),
            created_requirement_ids=tuple(created_requirement_ids),
            artifact_freshness_changed_ids=tuple(artifact_changed_ids),
            audit_event_ids=tuple(audit_event_ids),
            failure_codes=(ORCHESTRATION_FAILURE_COMMIT_FAILED,),
        )

    final_snapshot = repository.load_case_snapshot(plan.rental_case_id)
    final_revision = plan.evaluated_case_revision if final_snapshot is None else final_snapshot.rental_case.case_revision
    return WorkflowOrchestrationResult(
        rental_case_id=plan.rental_case_id,
        case_revision_before=plan.evaluated_case_revision,
        case_revision_after=final_revision,
        created_blocker_ids=tuple(created_blocker_ids),
        resolved_blocker_ids=tuple(resolved_blocker_ids),
        created_approval_ids=tuple(created_approval_ids),
        updated_approval_ids=tuple(updated_approval_ids),
        created_action_ids=tuple(created_action_ids),
        superseded_action_ids=tuple(superseded_action_ids),
        created_requirement_ids=tuple(created_requirement_ids),
        artifact_freshness_changed_ids=tuple(artifact_changed_ids),
        audit_event_ids=tuple(audit_event_ids),
    )


def reconcile_workflow_orchestration(
    repository: WorkflowOrchestrationRepositoryProtocol,
    *,
    rental_case_id: int,
    actor_reference: str,
    actor_type: str | None = "system",
    now: Callable[[], str] = _utc_now,
) -> WorkflowOrchestrationResult:
    snapshot = repository.load_case_snapshot(rental_case_id)
    if snapshot is None:
        return WorkflowOrchestrationResult(
            rental_case_id=rental_case_id,
            case_revision_before=0,
            case_revision_after=0,
            failure_codes=(ORCHESTRATION_FAILURE_CASE_NOT_FOUND,),
        )
    context = build_workflow_orchestration_context(snapshot)
    plan = evaluate_workflow_orchestration(context, now=now())
    return apply_workflow_orchestration_plan(
        repository,
        plan,
        actor_reference=actor_reference,
        actor_type=actor_type,
        now=now,
        loaded_snapshot=snapshot,
    )


def apply_approval_decision(
    repository: WorkflowOrchestrationRepositoryProtocol,
    request: ApprovalDecisionInput,
    *,
    now: Callable[[], str] = _utc_now,
) -> ApprovalDecisionResult:
    snapshot = repository.load_case_snapshot(request.rental_case_id)
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
    if approval is None:
        return ApprovalDecisionResult(
            rental_case_id=request.rental_case_id,
            approval_request_id=request.approval_request_id,
            approval_status="open",
            case_revision_before=snapshot.rental_case.case_revision,
            case_revision_after=snapshot.rental_case.case_revision,
            failure_codes=(ORCHESTRATION_FAILURE_APPROVAL_TARGET_INVALID,),
        )

    if approval.target_entity_type == "case_decision":
        return repository.apply_case_decision_approval(request)
    if approval.target_entity_type == "workflow_action":
        return _approval_result_from_action_result(apply_workflow_action_approval(repository, request, now=now))

    target_entity_id = approval.target_entity_id or _parse_id_reference(approval.target_entity_reference)
    if approval.target_entity_type != "proposed_case_change":
        return ApprovalDecisionResult(
            rental_case_id=request.rental_case_id,
            approval_request_id=request.approval_request_id,
            approval_status=approval.status,
            case_revision_before=snapshot.rental_case.case_revision,
            case_revision_after=snapshot.rental_case.case_revision,
            failure_codes=(ORCHESTRATION_FAILURE_APPROVAL_TARGET_INVALID,),
        )
    if target_entity_id is None or snapshot.find_proposed_change(target_entity_id) is None:
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
            )
        if approval.status == APPROVAL_REQUEST_STATUS_REJECTED and request.decision == ORCHESTRATION_DECISION_REJECTED:
            return ApprovalDecisionResult(
                rental_case_id=request.rental_case_id,
                approval_request_id=request.approval_request_id,
                approval_status=approval.status,
                case_revision_before=snapshot.rental_case.case_revision,
                case_revision_after=snapshot.rental_case.case_revision,
            )
        return ApprovalDecisionResult(
            rental_case_id=request.rental_case_id,
            approval_request_id=request.approval_request_id,
            approval_status=approval.status,
            case_revision_before=snapshot.rental_case.case_revision,
            case_revision_after=snapshot.rental_case.case_revision,
            failure_codes=(ORCHESTRATION_FAILURE_INVALID_ENTITY_STATUS,),
        )

    decided_at = request.decided_at or now()
    status = (
        APPROVAL_REQUEST_STATUS_APPROVED
        if request.decision == ORCHESTRATION_DECISION_APPROVED
        else APPROVAL_REQUEST_STATUS_REJECTED
    )
    approval = repository.decide_approval_request(
        rental_case_id=request.rental_case_id,
        approval_request_id=request.approval_request_id,
        status=status,
        decision_payload=request.decision_payload,
        decided_at=decided_at,
        decided_by_reference=request.actor_reference,
        decision_notes=request.decision_notes,
    )
    audit_event_id = repository.create_workflow_event(
        rental_case_id=request.rental_case_id,
        event_type_code="approval_decided",
        source_type="orchestration_runtime",
        source_reference=f"approval:{request.approval_request_id}",
        actor_type=request.actor_type,
        actor_reference=request.actor_reference,
        occurred_at=decided_at,
        structured_payload={
            "approval_request_id": request.approval_request_id,
            "decision": request.decision,
            "target_entity_type": approval.target_entity_type,
            "target_entity_id": approval.target_entity_id,
        },
        event_identity_key=f"approval:decision:{request.approval_request_id}:{request.decision}:{request.expected_case_revision}",
    ).workflow_event_id

    return ApprovalDecisionResult(
        rental_case_id=request.rental_case_id,
        approval_request_id=request.approval_request_id,
        approval_status=approval.status,
        case_revision_before=snapshot.rental_case.case_revision,
        case_revision_after=snapshot.rental_case.case_revision,
        audit_event_ids=(audit_event_id,),
    )


def apply_workflow_action_approval(
    repository: WorkflowOrchestrationRepositoryProtocol,
    request: ApprovalDecisionInput,
    *,
    now: Callable[[], str] = _utc_now,
) -> WorkflowActionApprovalResult:
    if request.decided_at is None:
        request = ApprovalDecisionInput(
            rental_case_id=request.rental_case_id,
            approval_request_id=request.approval_request_id,
            decision=request.decision,
            expected_case_revision=request.expected_case_revision,
            actor_reference=request.actor_reference,
            actor_type=request.actor_type,
            decision_payload=request.decision_payload,
            decision_notes=request.decision_notes,
            decided_at=now(),
        )
    return repository.apply_workflow_action_approval(request)


def accept_proposed_case_change(
    repository: WorkflowOrchestrationRepositoryProtocol,
    request: ProposedCaseChangeResolutionInput,
    *,
    now: Callable[[], str] = _utc_now,
) -> ProposedCaseChangeResolutionResult:
    if request.decided_at is None:
        request = ProposedCaseChangeResolutionInput(
            rental_case_id=request.rental_case_id,
            proposed_case_change_id=request.proposed_case_change_id,
            decision=request.decision,
            expected_case_revision=request.expected_case_revision,
            actor_reference=request.actor_reference,
            actor_type=request.actor_type,
            final_value_payload=request.final_value_payload,
            decision_notes=request.decision_notes,
            decided_at=now(),
        )
    return repository.commit_proposed_case_change_resolution(request)


def apply_case_fact_mutation(
    repository: WorkflowOrchestrationRepositoryProtocol,
    request: CaseFactMutationRequest,
    *,
    now: Callable[[], str] = _utc_now,
) -> CaseFactMutationResult | None:
    snapshot = repository.load_case_snapshot(request.rental_case_id)
    if snapshot is None or snapshot.rental_case.case_revision != request.expected_case_revision:
        return None
    timestamp = now()
    if request.field_code in {"active_event_window", "date_change"}:
        payload = request.new_value_payload
        if not isinstance(payload, dict):
            return None
        updated_case = repository.update_rental_case_schedule(
            rental_case_id=request.rental_case_id,
            expected_case_revision=request.expected_case_revision,
            active_event_start=payload.get("start"),
            active_event_end=payload.get("end"),
            updated_at=timestamp,
        )
        event = repository.create_workflow_event(
            rental_case_id=request.rental_case_id,
            event_type_code="rental_case_schedule_mutated",
            source_type="case_fact_mutation_service",
            source_reference=request.source_reference,
            actor_type=request.actor_type,
            actor_reference=request.actor_reference,
            occurred_at=timestamp,
            structured_payload={
                "field_code": request.field_code,
                "resolution_basis": request.resolution_basis,
            },
            event_identity_key=f"case_fact:schedule:{request.field_code}:{request.expected_case_revision}",
        )
        return CaseFactMutationResult(
            rental_case_id=request.rental_case_id,
            previous_case_revision=request.expected_case_revision,
            new_case_revision=updated_case.case_revision,
            workflow_event_id=event.workflow_event_id,
            rental_case_fact_id=None,
        )

    updated_case = repository.increment_case_revision(
        rental_case_id=request.rental_case_id,
        expected_case_revision=request.expected_case_revision,
        updated_at=timestamp,
    )
    fact = repository.upsert_rental_case_fact(
        rental_case_id=request.rental_case_id,
        field_code=request.field_code,
        domain_code=request.domain_code,
        value_payload=request.new_value_payload,
        source_reference=request.source_reference,
        established_case_revision=updated_case.case_revision,
        timestamp=timestamp,
    )
    event = repository.create_workflow_event(
        rental_case_id=request.rental_case_id,
        event_type_code="rental_case_fact_mutated",
        source_type="case_fact_mutation_service",
        source_reference=request.source_reference,
        actor_type=request.actor_type,
        actor_reference=request.actor_reference,
        occurred_at=timestamp,
        structured_payload={
            "field_code": request.field_code,
            "domain_code": request.domain_code,
            "resolution_basis": request.resolution_basis,
        },
        event_identity_key=f"case_fact:mutation:{request.field_code}:{request.expected_case_revision}",
    )
    return CaseFactMutationResult(
        rental_case_id=request.rental_case_id,
        previous_case_revision=request.expected_case_revision,
        new_case_revision=updated_case.case_revision,
        workflow_event_id=event.workflow_event_id,
        rental_case_fact_id=fact.rental_case_fact_id,
    )


def _apply_open_question_rules(
    context: WorkflowOrchestrationContext,
    blocker_changes: list[BlockerPlanChange],
    action_changes: list[WorkflowActionPlanChange],
    evidence_keys: list[str],
    policy_codes: list[str],
    rule_codes: list[str],
) -> None:
    for question in context.open_questions:
        if question.status not in {OPEN_QUESTION_STATUS_OPEN, OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION}:
            continue
        semantic_key = f"blocker:question:{question.open_question_id}"
        blocker_changes.append(
            BlockerPlanChange(
                semantic_issue_key=semantic_key,
                blocker_type="missing_client_information"
                if (question.requested_from_role or "").startswith("client")
                else "internal_confirmation_required",
                blocked_subject_type=_blocked_subject_type_for_scope(question.blocking_scope),
                blocked_subject_reference=f"open_question:{question.open_question_id}",
                origin_entity_type="open_question",
                origin_entity_id=question.open_question_id,
                origin_entity_reference=f"open_question:{question.open_question_id}",
                severity=SEVERITY_HIGH
                if question.blocking_scope in {"transition", "readiness"}
                else SEVERITY_MEDIUM,
                resolution_condition_text=f"Open question {question.open_question_id} must be resolved.",
                rule_code=RULE_MISSING_CLIENT_INFORMATION,
                evidence_reference_keys=(question.source_reference or f"open_question:{question.open_question_id}",),
            )
        )
        evidence_keys.append(question.source_reference or f"open_question:{question.open_question_id}")
        if (question.requested_from_role or "").startswith("client"):
            policy_codes.append("POLICY_INFORMATION_REQUEST_ROUTING")
            rule_codes.append(RULE_MISSING_CLIENT_INFORMATION)
        else:
            action_changes.append(
                _make_action_change(
                    action_type=ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
                    action_category=ACTION_CATEGORY_COORDINATION,
                    target_adapter_code="internal",
                    reason_entity_type="open_question",
                    reason_entity_id=question.open_question_id,
                    reason_entity_reference=f"open_question:{question.open_question_id}",
                    approval_posture=APPROVAL_POSTURE_AUTOMATIC_ALLOWED,
                    source_case_revision=context.evaluated_case_revision,
                    structured_payload={
                        "task_kind": "internal_confirmation",
                        "open_question_ids": [question.open_question_id],
                        "summary": question.human_question_text,
                        "reason": "Internal resolution required.",
                    },
                    rule_code=RULE_INTERNAL_CONFIRMATION_REQUEST,
                )
            )
            policy_codes.append("POLICY_INFORMATION_REQUEST_ROUTING")
            rule_codes.append(RULE_MISSING_CLIENT_INFORMATION)


def _apply_reasoning_effect_rules(
    context: WorkflowOrchestrationContext,
    blocker_changes: list[BlockerPlanChange],
    action_changes: list[WorkflowActionPlanChange],
    requirement_changes: list[RequirementPlanChange],
    evidence_keys: list[str],
    policy_codes: list[str],
    rule_codes: list[str],
) -> None:
    for effect in context.reasoning_effects:
        evidence_keys.append(effect.source_projection_identity_key)
        if effect.effect_type_code == WORKFLOW_REASONING_EFFECT_CURRENT_AUTHORITY_MISSING:
            semantic_key = f"blocker:authority:missing:{effect.source_projection_identity_key}"
            blocker_changes.append(
                BlockerPlanChange(
                    semantic_issue_key=semantic_key,
                    blocker_type="current_authority_missing",
                    blocked_subject_type=_blocked_subject_type_for_reasoning_purpose(effect.reasoning_purpose),
                    blocked_subject_reference=f"reasoning_projection:{effect.source_projection_identity_key}",
                    origin_entity_type="reasoning_projection",
                    origin_entity_reference=f"reasoning_projection:{effect.source_projection_identity_key}",
                    severity=SEVERITY_HIGH,
                    resolution_condition_text="Current authority must be resolved before consequential workflow commitment.",
                    rule_code=RULE_AUTHORITY_GAP_BLOCK,
                    evidence_reference_keys=(effect.source_projection_identity_key,),
                )
            )
            action_changes.append(
                _make_internal_review_action(
                    reason_reference=f"reasoning_projection:{effect.source_projection_identity_key}",
                    source_case_revision=context.evaluated_case_revision,
                    task_kind="authority_review",
                    summary="Current authority is missing for the requested workflow scope.",
                    rule_code=RULE_AUTHORITY_GAP_BLOCK,
                )
            )
            policy_codes.append("POLICY_FAIL_CLOSED_ON_CURRENT_AUTHORITY_GAP")
            rule_codes.append(RULE_AUTHORITY_GAP_BLOCK)
        elif effect.effect_type_code == WORKFLOW_REASONING_EFFECT_CONFIRMATION_REQUIRED:
            semantic_key = f"blocker:authority:confirmation:{effect.source_projection_identity_key}"
            blocker_changes.append(
                BlockerPlanChange(
                    semantic_issue_key=semantic_key,
                    blocker_type="confirmation_required",
                    blocked_subject_type=_blocked_subject_type_for_reasoning_purpose(effect.reasoning_purpose),
                    blocked_subject_reference=f"reasoning_projection:{effect.source_projection_identity_key}",
                    origin_entity_type="reasoning_projection",
                    origin_entity_reference=f"reasoning_projection:{effect.source_projection_identity_key}",
                    severity=SEVERITY_MEDIUM,
                    resolution_condition_text="Structured confirmation or review must be completed before commitment.",
                    rule_code=RULE_CONFIRMATION_REQUIRED_BLOCK,
                    evidence_reference_keys=(effect.source_projection_identity_key,),
                )
            )
            if effect.reasoning_purpose == "compliance_requirement_review":
                action_changes.append(
                    _make_action_change(
                        action_type=ACTION_TYPE_ESCALATE_COMPLIANCE_REVIEW,
                        action_category=ACTION_CATEGORY_COMPLIANCE,
                        target_adapter_code="internal",
                        reason_entity_type="reasoning_projection",
                        reason_entity_reference=f"reasoning_projection:{effect.source_projection_identity_key}",
                        approval_posture=APPROVAL_POSTURE_HUMAN_ONLY,
                        source_case_revision=context.evaluated_case_revision,
                        structured_payload={
                            "task_kind": "compliance_confirmation_review",
                            "reasoning_projection_identity_key": effect.source_projection_identity_key,
                            "reason": "Current compliance confirmation is still required.",
                        },
                        rule_code=RULE_CONFIRMATION_REQUIRED_BLOCK,
                    )
                )
            else:
                action_changes.append(
                    _make_internal_review_action(
                        reason_reference=f"reasoning_projection:{effect.source_projection_identity_key}",
                        source_case_revision=context.evaluated_case_revision,
                        task_kind="confirmation_review",
                        summary="Structured confirmation is required before progressing.",
                        rule_code=RULE_CONFIRMATION_REQUIRED_BLOCK,
                    )
            )
            policy_codes.append("POLICY_CONFIRMATION_REQUIRED")
            rule_codes.append(RULE_CONFIRMATION_REQUIRED_BLOCK)
        elif effect.effect_type_code == WORKFLOW_REASONING_EFFECT_DETERMINISTIC_RESTRICTION:
            semantic_key = f"blocker:authority:restriction:{effect.source_projection_identity_key}"
            blocker_changes.append(
                BlockerPlanChange(
                    semantic_issue_key=semantic_key,
                    blocker_type="deterministic_restriction",
                    blocked_subject_type=_blocked_subject_type_for_reasoning_purpose(effect.reasoning_purpose),
                    blocked_subject_reference=f"reasoning_projection:{effect.source_projection_identity_key}",
                    origin_entity_type="reasoning_projection",
                    origin_entity_reference=f"reasoning_projection:{effect.source_projection_identity_key}",
                    severity=SEVERITY_HIGH,
                    resolution_condition_text="Current governed policy does not support the requested commitment as stated.",
                    rule_code=RULE_DETERMINISTIC_RESTRICTION,
                    evidence_reference_keys=(effect.source_projection_identity_key,),
                )
            )
            policy_codes.append("POLICY_CURRENT_GOVERNED_RESTRICTION")
            rule_codes.append(RULE_DETERMINISTIC_RESTRICTION)
        elif effect.effect_type_code == WORKFLOW_REASONING_EFFECT_REQUIREMENT_CANDIDATE:
            mapping = _map_requirement_candidate(effect)
            if mapping is None:
                continue
            requirement_changes.append(mapping)
            action_changes.append(
                _make_action_change(
                    action_type=ACTION_TYPE_ESCALATE_COMPLIANCE_REVIEW,
                    action_category=ACTION_CATEGORY_COMPLIANCE,
                    target_adapter_code="internal",
                    reason_entity_type="reasoning_projection",
                    reason_entity_reference=f"reasoning_projection:{effect.source_projection_identity_key}",
                    approval_posture=APPROVAL_POSTURE_HUMAN_ONLY,
                    source_case_revision=context.evaluated_case_revision,
                structured_payload={
                    "task_kind": "requirement_review",
                    "requirement_type": mapping.requirement_type,
                    "domain_code": mapping.domain_code,
                    "reasoning_projection_identity_key": effect.source_projection_identity_key,
                    "reason": "Governed compliance requirement candidate requires human review.",
                },
                rule_code=RULE_COMPLIANCE_REQUIREMENT,
            )
            )
            policy_codes.append("POLICY_GOVERNED_REQUIREMENT_MAPPING")
            rule_codes.append(RULE_COMPLIANCE_REQUIREMENT)


def _apply_case_decision_rules(
    context: WorkflowOrchestrationContext,
    blocker_changes: list[BlockerPlanChange],
    approval_changes: list[ApprovalPlanChange],
    action_changes: list[WorkflowActionPlanChange],
    evidence_keys: list[str],
    policy_codes: list[str],
    rule_codes: list[str],
) -> None:
    active_by_scope: dict[str, list[CaseDecision]] = {}
    for decision in context.case_decisions:
        if decision.status == CASE_DECISION_STATUS_ACTIVE:
            active_by_scope.setdefault(decision.scope_key, []).append(decision)
    for scope_key, decisions in active_by_scope.items():
        if len(decisions) < 2:
            continue
        blocker_changes.append(
            BlockerPlanChange(
                semantic_issue_key=f"blocker:conflict:case_decision:{scope_key}",
                blocker_type="case_decision_conflict",
                blocked_subject_type=BLOCKED_SUBJECT_TYPE_DECISION,
                blocked_subject_reference=f"case_decision_scope:{scope_key}",
                origin_entity_type="case_decision",
                origin_entity_reference=f"case_decision_scope:{scope_key}",
                severity=SEVERITY_HIGH,
                resolution_condition_text="Only one active case decision may remain in the same scope.",
                rule_code=RULE_CASE_DECISION_CONFLICT,
                evidence_reference_keys=tuple(f"case_decision:{decision.case_decision_id}" for decision in decisions),
            )
        )
        rule_codes.append(RULE_CASE_DECISION_CONFLICT)
        policy_codes.append("POLICY_SINGLE_ACTIVE_CASE_DECISION_SCOPE")

    for decision in context.case_decisions:
        if decision.status not in {CASE_DECISION_STATUS_PROPOSED, CASE_DECISION_STATUS_PENDING_APPROVAL}:
            continue
        evidence_keys.append(decision.evidence_reference or f"case_decision:{decision.case_decision_id}")
        if decision.approval_posture == APPROVAL_POSTURE_APPROVAL_REQUIRED:
            approval_key = f"approval:case_decision:{decision.case_decision_id}"
            approval_changes.append(
                ApprovalPlanChange(
                    semantic_approval_key=approval_key,
                    target_entity_type="case_decision",
                    target_entity_id=decision.case_decision_id,
                    target_entity_reference=f"case_decision:{decision.case_decision_id}",
                    approval_type="commercial_exception"
                    if "commercial" in decision.domain_code or "fee" in decision.domain_code
                    else "operational_exception",
                    reason_text=f"Approval required before activating case decision {decision.case_decision_id}.",
                    evidence_reference_keys=(decision.baseline_reference, decision.evidence_reference or f"case_decision:{decision.case_decision_id}"),
                    required_approver_role="management_review",
                    rule_code=RULE_CASE_DECISION_APPROVAL,
                )
            )
            blocker_changes.append(
                BlockerPlanChange(
                    semantic_issue_key=f"blocker:decision:approval:{decision.case_decision_id}",
                    blocker_type="case_decision_approval_required",
                    blocked_subject_type=BLOCKED_SUBJECT_TYPE_DECISION,
                    blocked_subject_id=decision.case_decision_id,
                    blocked_subject_reference=f"case_decision:{decision.case_decision_id}",
                    origin_entity_type="case_decision",
                    origin_entity_id=decision.case_decision_id,
                    origin_entity_reference=f"case_decision:{decision.case_decision_id}",
                    severity=SEVERITY_HIGH,
                    resolution_condition_text="Approval must be approved or the proposed case decision must be rejected.",
                    rule_code=RULE_CASE_DECISION_APPROVAL,
                    evidence_reference_keys=(decision.baseline_reference,),
                )
            )
            action_changes.append(
                _make_internal_review_action(
                    reason_reference=f"case_decision:{decision.case_decision_id}",
                    source_case_revision=context.evaluated_case_revision,
                    task_kind="case_decision_review",
                    summary=f"Review proposed case decision {decision.case_decision_id}.",
                    rule_code=RULE_CASE_DECISION_APPROVAL,
                )
            )
            policy_codes.append("POLICY_RISK_BASED_APPROVAL")
            rule_codes.append(RULE_CASE_DECISION_APPROVAL)


def _apply_proposed_change_rules(
    context: WorkflowOrchestrationContext,
    blocker_changes: list[BlockerPlanChange],
    approval_changes: list[ApprovalPlanChange],
    action_changes: list[WorkflowActionPlanChange],
    evidence_keys: list[str],
    policy_codes: list[str],
    rule_codes: list[str],
) -> None:
    for change in context.proposed_changes:
        if change.status not in {PROPOSED_CHANGE_STATUS_PROPOSED, PROPOSED_CHANGE_STATUS_UNDER_REVIEW}:
            continue
        evidence_keys.append(change.source_reference or f"proposed_change:{change.proposed_case_change_id}")
        if change.review_posture == APPROVAL_POSTURE_APPROVAL_REQUIRED:
            approval_changes.append(
                ApprovalPlanChange(
                    semantic_approval_key=f"approval:proposed_change:{change.proposed_case_change_id}",
                    target_entity_type="proposed_case_change",
                    target_entity_id=change.proposed_case_change_id,
                    target_entity_reference=f"proposed_change:{change.proposed_case_change_id}",
                    approval_type="case_change_review",
                    reason_text=f"Approval required before accepting proposed change {change.proposed_case_change_id}.",
                    evidence_reference_keys=(change.source_reference or f"proposed_change:{change.proposed_case_change_id}",),
                    required_approver_role="management_review",
                    rule_code=RULE_PROPOSED_CHANGE_REVIEW,
                )
            )
            policy_codes.append("POLICY_RISK_BASED_APPROVAL")
        if change.impact_classification in {CHANGE_IMPACT_MATERIAL, CHANGE_IMPACT_FUNDAMENTAL}:
            blocker_changes.append(
                BlockerPlanChange(
                    semantic_issue_key=f"blocker:change:review:{change.proposed_case_change_id}",
                    blocker_type="proposed_change_review_required",
                    blocked_subject_type=BLOCKED_SUBJECT_TYPE_ACTION,
                    blocked_subject_reference=f"proposed_change:{change.proposed_case_change_id}",
                    origin_entity_type="proposed_case_change",
                    origin_entity_id=change.proposed_case_change_id,
                    origin_entity_reference=f"proposed_change:{change.proposed_case_change_id}",
                    severity=SEVERITY_HIGH
                    if change.impact_classification == CHANGE_IMPACT_FUNDAMENTAL
                    else SEVERITY_MEDIUM,
                    resolution_condition_text="The proposed change must be accepted, rejected, or superseded.",
                    rule_code=RULE_PROPOSED_CHANGE_REVIEW,
                    evidence_reference_keys=(change.source_reference or f"proposed_change:{change.proposed_case_change_id}",),
                )
            )
        action_changes.append(
            _make_internal_review_action(
                reason_reference=f"proposed_change:{change.proposed_case_change_id}",
                source_case_revision=context.evaluated_case_revision,
                task_kind="proposed_change_review",
                summary=f"Review proposed change {change.proposed_case_change_id} ({change.impact_classification or 'unknown_impact'}).",
                rule_code=RULE_PROPOSED_CHANGE_REVIEW,
            )
        )
        rule_codes.append(RULE_PROPOSED_CHANGE_REVIEW)


def _apply_reschedule_rules(
    context: WorkflowOrchestrationContext,
    action_changes: list[WorkflowActionPlanChange],
    evidence_keys: list[str],
    policy_codes: list[str],
    rule_codes: list[str],
) -> None:
    for request in context.reschedule_requests:
        if request.status not in {
            RESCHEDULE_STATUS_PROPOSED,
            RESCHEDULE_STATUS_EVALUATING,
            RESCHEDULE_STATUS_OFFERED,
            RESCHEDULE_STATUS_AWAITING_CLIENT_CONFIRMATION,
        }:
            continue
        evidence_keys.append(f"reschedule_request:{request.reschedule_request_id}")
        action_changes.append(
            _make_action_change(
                action_type=ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
                action_category=ACTION_CATEGORY_COORDINATION,
                target_adapter_code="internal",
                reason_entity_type="reschedule_request",
                reason_entity_id=request.reschedule_request_id,
                reason_entity_reference=f"reschedule_request:{request.reschedule_request_id}",
                approval_posture=APPROVAL_POSTURE_AUTOMATIC_ALLOWED,
                source_case_revision=context.evaluated_case_revision,
                structured_payload={
                    "task_kind": "reschedule_review",
                    "reschedule_request_id": request.reschedule_request_id,
                    "status": request.status,
                    "summary": f"Review reschedule request {request.reschedule_request_id}.",
                    "reason": "Structured reschedule review is required before any downstream action.",
                },
                rule_code=RULE_RESCHEDULE_REVIEW,
            )
        )
        rule_codes.append(RULE_RESCHEDULE_REVIEW)
        policy_codes.append("POLICY_NEGOTIATED_RESCHEDULE_WORKFLOW")


def _apply_follow_up_rules(
    context: WorkflowOrchestrationContext,
    action_changes: list[WorkflowActionPlanChange],
    evidence_keys: list[str],
    policy_codes: list[str],
    rule_codes: list[str],
    now: str,
) -> None:
    now_dt = _parse_timestamp(now)
    for follow_up in context.follow_ups:
        if follow_up.status not in {
            FOLLOW_UP_STATUS_SCHEDULED,
            FOLLOW_UP_STATUS_DUE,
            FOLLOW_UP_STATUS_OVERDUE,
            FOLLOW_UP_STATUS_ESCALATED,
        }:
            continue
        due_dt = _parse_timestamp(follow_up.due_at)
        if follow_up.status == FOLLOW_UP_STATUS_SCHEDULED and due_dt is not None and due_dt > now_dt:
            continue
        evidence_keys.append(f"follow_up:{follow_up.follow_up_id}")
        action_type = follow_up.next_action_type or ACTION_TYPE_SCHEDULE_FOLLOW_UP_REVIEW
        structured_payload = _follow_up_action_payload(context, follow_up, action_type=action_type)
        if structured_payload is None:
            continue
        action_changes.append(
            _make_action_change(
                action_type=action_type,
                action_category=_action_category_for_follow_up_action(action_type),
                target_adapter_code="internal",
                reason_entity_type="follow_up",
                reason_entity_id=follow_up.follow_up_id,
                reason_entity_reference=f"follow_up:{follow_up.follow_up_id}",
                approval_posture=_approval_posture_for_follow_up_action(action_type),
                source_case_revision=context.evaluated_case_revision,
                structured_payload=structured_payload,
                due_at=follow_up.due_at,
                rule_code=RULE_DUE_FOLLOW_UP,
            )
        )
        rule_codes.append(RULE_DUE_FOLLOW_UP)
        policy_codes.append("POLICY_ADAPTIVE_FOLLOW_UP")


def _apply_artifact_refresh_rules(
    context: WorkflowOrchestrationContext,
    artifact_changes: list[ArtifactFreshnessPlanChange],
    action_changes: list[WorkflowActionPlanChange],
    policy_codes: list[str],
    rule_codes: list[str],
) -> None:
    stale_artifacts = [
        artifact
        for artifact in context.artifacts
        if artifact.artifact_type in REFRESHABLE_ARTIFACT_TYPES
        and artifact.freshness_status == ARTIFACT_FRESHNESS_CURRENT
        and artifact.derived_from_case_revision < context.evaluated_case_revision
    ]
    if not stale_artifacts:
        return
    for artifact in stale_artifacts:
        artifact_changes.append(
            ArtifactFreshnessPlanChange(
                artifact_reference_id=artifact.artifact_reference_id,
                target_freshness_status=ARTIFACT_FRESHNESS_REFRESH_REQUIRED,
                reason_code="case_revision_advanced",
            )
        )
    action_changes.append(
        _make_action_change(
            action_type=ACTION_TYPE_MARK_ARTIFACT_REFRESH_REQUIRED,
            action_category=ACTION_CATEGORY_INTERNAL_CONTROL,
            target_adapter_code="internal",
            reason_entity_type="artifact_set",
            reason_entity_reference=f"case_artifacts:{context.rental_case_id}",
            approval_posture=APPROVAL_POSTURE_AUTOMATIC_ALLOWED,
            source_case_revision=context.evaluated_case_revision,
            structured_payload={
                "artifact_reference_ids": [artifact.artifact_reference_id for artifact in stale_artifacts],
                "reason": "Current artifact projections were derived from an older case revision.",
            },
            rule_code=RULE_ARTIFACT_REFRESH,
        )
    )
    rule_codes.append(RULE_ARTIFACT_REFRESH)
    policy_codes.append("POLICY_ARTIFACT_FRESHNESS_REEVALUATION")


def _make_internal_review_action(
    *,
    reason_reference: str,
    source_case_revision: int,
    task_kind: str,
    summary: str,
    rule_code: str,
) -> WorkflowActionPlanChange:
    return _make_action_change(
        action_type=ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
        action_category=ACTION_CATEGORY_COORDINATION,
        target_adapter_code="internal",
        reason_entity_type="review_item",
        reason_entity_reference=reason_reference,
        approval_posture=APPROVAL_POSTURE_AUTOMATIC_ALLOWED,
        source_case_revision=source_case_revision,
        structured_payload={
            "task_kind": task_kind,
            "summary": summary,
            "reason": summary,
        },
        rule_code=rule_code,
    )


def _make_action_change(
    *,
    action_type: str,
    action_category: str,
    target_adapter_code: str,
    reason_entity_type: str,
    approval_posture: str,
    source_case_revision: int,
    structured_payload: dict[str, Any],
    reason_entity_id: int | None = None,
    reason_entity_reference: str | None = None,
    target_scope_key: str | None = None,
    due_at: str | None = None,
    rule_code: str | None = None,
) -> WorkflowActionPlanChange:
    material = {
        "reason_entity_type": reason_entity_type,
        "reason_entity_id": reason_entity_id,
        "reason_entity_reference": reason_entity_reference,
        "target_scope_key": target_scope_key,
        "structured_payload": structured_payload,
    }
    digest = _hash_material(material)
    return WorkflowActionPlanChange(
        action_type=action_type,
        action_category=action_category,
        target_adapter_code=target_adapter_code,
        reason_entity_type=reason_entity_type,
        reason_entity_id=reason_entity_id,
        reason_entity_reference=reason_entity_reference,
        approval_posture=approval_posture,
        semantic_subject_hash=digest,
        source_case_revision=source_case_revision,
        idempotency_key=f"action:{action_type}:{digest}:{source_case_revision}",
        structured_payload=structured_payload,
        target_scope_key=target_scope_key,
        due_at=due_at,
        rule_code=rule_code,
    )


def _blocked_subject_type_for_scope(blocking_scope: str) -> str:
    if blocking_scope == "transition":
        return BLOCKED_SUBJECT_TYPE_TRANSITION
    if blocking_scope == "readiness":
        return BLOCKED_SUBJECT_TYPE_READINESS
    return BLOCKED_SUBJECT_TYPE_ACTION


def _blocked_subject_type_for_reasoning_purpose(reasoning_purpose: str) -> str:
    if reasoning_purpose in {"proposal_readiness_review", "event_readiness_review"}:
        return BLOCKED_SUBJECT_TYPE_READINESS
    if reasoning_purpose in {"case_decision_baseline", "commercial_rule_review"}:
        return BLOCKED_SUBJECT_TYPE_DECISION
    return BLOCKED_SUBJECT_TYPE_ACTION


def _initial_action_status(approval_posture: str) -> str:
    if approval_posture == APPROVAL_POSTURE_AUTOMATIC_ALLOWED:
        return WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE
    if approval_posture in {APPROVAL_POSTURE_APPROVAL_REQUIRED, APPROVAL_POSTURE_HUMAN_ONLY}:
        return WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL
    return WORKFLOW_ACTION_STATUS_PROPOSED


def _map_requirement_candidate(effect: WorkflowReasoningEffect) -> RequirementPlanChange | None:
    material = " ".join(
        value.lower()
        for value in (
            effect.domain_scope_code,
            effect.related_code,
            " ".join(effect.related_item_ids),
        )
        if value
    )
    if "permit" in material:
        return RequirementPlanChange(
            requirement_type="permit_review_required",
            domain_code="compliance",
            applicability_basis="phase7_requirement_candidate_permit",
            blocking_scope="readiness",
            evidence_reference=effect.source_projection_identity_key,
            owner_role="case_handler",
            rule_code=RULE_COMPLIANCE_REQUIREMENT,
        )
    if "sound" in material or "noise" in material:
        return RequirementPlanChange(
            requirement_type="sound_compliance_review_required",
            domain_code="compliance",
            applicability_basis="phase7_requirement_candidate_sound",
            blocking_scope="readiness",
            evidence_reference=effect.source_projection_identity_key,
            owner_role="case_handler",
            rule_code=RULE_COMPLIANCE_REQUIREMENT,
        )
    if "insurance" in material:
        return RequirementPlanChange(
            requirement_type="insurance_confirmation_required",
            domain_code="compliance",
            applicability_basis="phase7_requirement_candidate_insurance",
            blocking_scope="readiness",
            evidence_reference=effect.source_projection_identity_key,
            owner_role="case_handler",
            rule_code=RULE_COMPLIANCE_REQUIREMENT,
        )
    return None


def _mark_dependent_artifacts_stale(
    repository: WorkflowOrchestrationRepositoryProtocol,
    rental_case_id: int,
    new_case_revision: int,
    updated_at: str,
) -> list[int]:
    snapshot = repository.load_case_snapshot(rental_case_id)
    if snapshot is None:
        return []
    changed: list[int] = []
    for artifact in snapshot.artifacts:
        if artifact.artifact_type not in REFRESHABLE_ARTIFACT_TYPES:
            continue
        if artifact.derived_from_case_revision >= new_case_revision:
            continue
        if artifact.freshness_status not in {ARTIFACT_FRESHNESS_CURRENT, ARTIFACT_FRESHNESS_STALE}:
            continue
        target_status = (
            ARTIFACT_FRESHNESS_REFRESH_REQUIRED
            if artifact.artifact_type in {ARTIFACT_TYPE_PROPOSAL, ARTIFACT_TYPE_AGREEMENT, ARTIFACT_TYPE_INTERNAL_EVENT_BRIEF}
            else ARTIFACT_FRESHNESS_STALE
        )
        repository.update_artifact_freshness(
            rental_case_id=rental_case_id,
            artifact_reference_id=artifact.artifact_reference_id,
            freshness_status=target_status,
            updated_at=updated_at,
        )
        changed.append(artifact.artifact_reference_id)
    return changed


def _supersede_stale_actions(
    repository: WorkflowOrchestrationRepositoryProtocol,
    rental_case_id: int,
    new_case_revision: int,
    updated_at: str,
) -> list[int]:
    snapshot = repository.load_case_snapshot(rental_case_id)
    if snapshot is None:
        return []
    superseded: list[int] = []
    for action in snapshot.workflow_actions:
        if action.status in {"succeeded", "failed", "cancelled", "superseded"}:
            continue
        if action.source_case_revision >= new_case_revision:
            continue
        repository.supersede_workflow_action(
            rental_case_id=rental_case_id,
            workflow_action_id=action.workflow_action_id,
            updated_at=updated_at,
        )
        superseded.append(action.workflow_action_id)
    return superseded


def _resolve_related_blockers(
    repository: WorkflowOrchestrationRepositoryProtocol,
    rental_case_id: int,
    resolved_at: str,
    predicate: Callable[[Blocker], bool],
) -> list[int]:
    snapshot = repository.load_case_snapshot(rental_case_id)
    if snapshot is None:
        return []
    resolved: list[int] = []
    for blocker in snapshot.blockers:
        if blocker.status != BLOCKER_STATUS_OPEN:
            continue
        if not predicate(blocker):
            continue
        repository.resolve_blocker(
            rental_case_id=rental_case_id,
            blocker_id=blocker.blocker_id,
            resolved_at=resolved_at,
            resolution_reference="structured_resolution",
        )
        resolved.append(blocker.blocker_id)
    return resolved


def _approval_result_from_action_result(
    result: WorkflowActionApprovalResult,
) -> ApprovalDecisionResult:
    return ApprovalDecisionResult(
        rental_case_id=result.rental_case_id,
        approval_request_id=result.approval_request_id,
        approval_status=result.approval_status,
        case_revision_before=result.case_revision_before,
        case_revision_after=result.case_revision_after,
        audit_event_ids=result.audit_event_ids,
        resolved_blocker_ids=result.resolved_blocker_ids,
        failure_codes=result.failure_codes,
    )


def _has_approved_change_request(
    snapshot: WorkflowOrchestrationCaseSnapshot,
    proposed_case_change_id: int,
) -> bool:
    for approval in snapshot.approval_requests:
        if approval.status != APPROVAL_REQUEST_STATUS_APPROVED:
            continue
        if approval.target_entity_type != "proposed_case_change":
            continue
        if approval.target_entity_id == proposed_case_change_id or approval.target_entity_reference == f"proposed_change:{proposed_case_change_id}":
            return True
    return False


def _parse_id_reference(reference: str | None) -> int | None:
    if reference is None or ":" not in reference:
        return None
    _, raw_id = reference.rsplit(":", 1)
    return int(raw_id) if raw_id.isdigit() else None


def _validate_action_payload(action_type: str, payload: dict[str, Any]) -> None:
    required_keys = {
        ACTION_TYPE_REQUEST_CLIENT_INFORMATION: {"open_question_ids", "required_field_codes", "intended_recipient_role", "purpose", "reason"},
        ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM: {"task_kind", "summary", "reason"},
        ACTION_TYPE_ESCALATE_COMPLIANCE_REVIEW: {"task_kind", "reason"},
        ACTION_TYPE_MARK_ARTIFACT_REFRESH_REQUIRED: {"artifact_reference_ids", "reason"},
        ACTION_TYPE_SCHEDULE_FOLLOW_UP_REVIEW: {"follow_up_id", "reason_code", "due_at"},
    }
    expected = required_keys.get(action_type)
    if expected is None:
        raise ValueError(ORCHESTRATION_FAILURE_ACTION_PAYLOAD_INVALID)
    missing = tuple(sorted(expected.difference(payload.keys())))
    if missing:
        raise ValueError(ORCHESTRATION_FAILURE_ACTION_PAYLOAD_INVALID)


def _action_category_for_follow_up_action(action_type: str) -> str:
    if action_type == ACTION_TYPE_SCHEDULE_FOLLOW_UP_REVIEW:
        return ACTION_CATEGORY_FOLLOW_UP
    if action_type == ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM:
        return ACTION_CATEGORY_COORDINATION
    return ACTION_CATEGORY_COMMUNICATION


def _approval_posture_for_follow_up_action(action_type: str) -> str:
    if action_type in {ACTION_TYPE_SCHEDULE_FOLLOW_UP_REVIEW, ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM}:
        return APPROVAL_POSTURE_AUTOMATIC_ALLOWED
    return APPROVAL_POSTURE_APPROVAL_REQUIRED


def _follow_up_action_payload(
    context: WorkflowOrchestrationContext,
    follow_up,
    *,
    action_type: str,
) -> dict[str, Any] | None:
    if follow_up.reason_code == FOLLOW_UP_REASON_INQUIRY_MISSING_INFORMATION:
        payload = _inquiry_follow_up_payload(context, follow_up, action_type=action_type)
        return payload
    if action_type == ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM:
        return {
            "task_kind": "follow_up_review",
            "follow_up_id": follow_up.follow_up_id,
            "summary": f"Review follow-up {follow_up.follow_up_id}.",
            "reason": f"Follow-up {follow_up.reason_code} is current for review.",
        }
    return {
        "follow_up_id": follow_up.follow_up_id,
        "reason_code": follow_up.reason_code,
        "due_at": follow_up.due_at,
    }


def _inquiry_follow_up_payload(
    context: WorkflowOrchestrationContext,
    follow_up,
    *,
    action_type: str,
) -> dict[str, Any] | None:
    payload = follow_up.context_payload if isinstance(follow_up.context_payload, dict) else {}
    open_question_ids = payload.get("open_question_ids")
    if isinstance(open_question_ids, list):
        filtered_ids = {
            value
            for value in open_question_ids
            if isinstance(value, int) and value > 0
        }
    else:
        filtered_ids = set()
    relevant_questions = [
        question
        for question in context.open_questions
        if question.status == OPEN_QUESTION_STATUS_OPEN
        and (
            not filtered_ids
            or question.open_question_id in filtered_ids
        )
    ]
    if not relevant_questions:
        return None
    required_field_codes = payload.get("required_field_codes")
    if not isinstance(required_field_codes, list) or not required_field_codes:
        required_field_codes = list(
            dict.fromkeys(question.question_type for question in relevant_questions)
        )
    reason_text = payload.get("reason")
    if not isinstance(reason_text, str) or not reason_text.strip():
        reason_text = f"{len(relevant_questions)} inquiry fields remain unresolved."
    if action_type == ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM:
        return {
            "task_kind": "inquiry_follow_up_escalation",
            "follow_up_id": follow_up.follow_up_id,
            "summary": f"Escalate inquiry follow-up #{follow_up.sequence_number}.",
            "reason": reason_text,
            "open_question_ids": [question.open_question_id for question in relevant_questions],
            "required_field_codes": required_field_codes,
        }
    return {
        "follow_up_id": follow_up.follow_up_id,
        "reason_code": follow_up.reason_code,
        "due_at": follow_up.due_at,
        "sequence_number": follow_up.sequence_number,
        "open_question_ids": [question.open_question_id for question in relevant_questions],
        "required_field_codes": required_field_codes,
        "intended_recipient_role": payload.get("intended_recipient_role") or follow_up.waiting_for_role or "client",
        "recipient_reference": payload.get("recipient_reference") or follow_up.waiting_for_reference,
        "purpose": payload.get("purpose") or "request_missing_information",
        "summary": payload.get("summary") or f"Prepare client information request for follow-up #{follow_up.sequence_number}.",
        "reason": reason_text,
        "question_texts": [question.human_question_text for question in relevant_questions],
    }


def _is_managed_blocker_reference(reference: str | None) -> bool:
    semantic_key = _semantic_key_from_reference(reference)
    if semantic_key is None:
        return False
    return semantic_key.startswith(MANAGED_BLOCKER_PREFIXES)


def _is_managed_approval_reference(reference: str | None) -> bool:
    semantic_key = _semantic_key_from_reference(reference)
    if semantic_key is None:
        return False
    return semantic_key.startswith(MANAGED_APPROVAL_PREFIXES)


def _semantic_key_from_reference(reference: str | None) -> str | None:
    if reference is None or not reference.startswith("semantic:"):
        return None
    return reference.split("semantic:", 1)[1]


def _hash_material(material: dict[str, Any]) -> str:
    payload = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _parse_timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
