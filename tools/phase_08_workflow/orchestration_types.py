from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from .contracts import (
    APPROVAL_POSTURE_CODES,
    APPROVAL_REQUEST_STATUS_APPROVED,
    APPROVAL_REQUEST_STATUS_CODES,
    APPROVAL_REQUEST_STATUS_REJECTED,
    ARTIFACT_FRESHNESS_CODES,
    BLOCKED_SUBJECT_TYPE_CODES,
    BLOCKER_STATUS_CODES,
    BLOCKING_SCOPE_CODES,
    REQUIREMENT_STATUS_CODES,
    REASONING_PURPOSE_CODES,
    SEVERITY_CODES,
    WORKFLOW_ACTION_STATUS_CODES,
    WORKFLOW_ACTION_TYPES,
)
from .observation_contracts import RentalCaseFact
from .phase7_consumption_types import WorkflowReasoningEffect
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
)


PHASE_8_ORCHESTRATION_CONTRACT_VERSION = 1
PHASE_8_ORCHESTRATION_CONTRACT_LABEL = "phase8_orchestration_v1"

ORCHESTRATION_FAILURE_CASE_NOT_FOUND = "case_not_found"
ORCHESTRATION_FAILURE_STALE_CASE_REVISION = "stale_case_revision"
ORCHESTRATION_FAILURE_INVALID_ORCHESTRATION_INPUT = "invalid_orchestration_input"
ORCHESTRATION_FAILURE_CROSS_CASE_REFERENCE = "cross_case_reference"
ORCHESTRATION_FAILURE_INVALID_ENTITY_STATUS = "invalid_entity_status"
ORCHESTRATION_FAILURE_UNKNOWN_ACTION_TYPE = "unknown_action_type"
ORCHESTRATION_FAILURE_APPROVAL_REQUIRED = "approval_required"
ORCHESTRATION_FAILURE_APPROVAL_NOT_RESOLVED = "approval_not_resolved"
ORCHESTRATION_FAILURE_APPROVAL_TARGET_INVALID = "approval_target_invalid"
ORCHESTRATION_FAILURE_APPROVAL_TARGET_MISMATCH = "approval_target_mismatch"
ORCHESTRATION_FAILURE_CASE_DECISION_CONFLICT = "case_decision_conflict"
ORCHESTRATION_FAILURE_CASE_DECISION_NOT_ACTIVATABLE = "case_decision_not_activatable"
ORCHESTRATION_FAILURE_CASE_DECISION_ACTIVATION_FAILED = "case_decision_activation_failed"
ORCHESTRATION_FAILURE_PROPOSED_CHANGE_NOT_RESOLVABLE = "proposed_change_not_resolvable"
ORCHESTRATION_FAILURE_PROPOSED_CHANGE_RESOLUTION_FAILED = "proposed_change_resolution_failed"
ORCHESTRATION_FAILURE_BLOCKER_RESOLUTION_CONDITION_NOT_MET = "blocker_resolution_condition_not_met"
ORCHESTRATION_FAILURE_ACTION_DUPLICATE = "action_duplicate"
ORCHESTRATION_FAILURE_ACTION_PAYLOAD_INVALID = "action_payload_invalid"
ORCHESTRATION_FAILURE_ACTION_STATE_TRANSITION_INVALID = "action_state_transition_invalid"
ORCHESTRATION_FAILURE_ACTION_BLOCKED = "action_blocked"
ORCHESTRATION_FAILURE_UNSUPPORTED_REQUIREMENT_MAPPING = "unsupported_requirement_mapping"
ORCHESTRATION_FAILURE_COMMIT_FAILED = "orchestration_commit_failed"

ORCHESTRATION_FAILURE_CODES = frozenset(
    {
        ORCHESTRATION_FAILURE_CASE_NOT_FOUND,
        ORCHESTRATION_FAILURE_STALE_CASE_REVISION,
        ORCHESTRATION_FAILURE_INVALID_ORCHESTRATION_INPUT,
        ORCHESTRATION_FAILURE_CROSS_CASE_REFERENCE,
        ORCHESTRATION_FAILURE_INVALID_ENTITY_STATUS,
        ORCHESTRATION_FAILURE_UNKNOWN_ACTION_TYPE,
        ORCHESTRATION_FAILURE_APPROVAL_REQUIRED,
        ORCHESTRATION_FAILURE_APPROVAL_NOT_RESOLVED,
        ORCHESTRATION_FAILURE_APPROVAL_TARGET_INVALID,
        ORCHESTRATION_FAILURE_APPROVAL_TARGET_MISMATCH,
        ORCHESTRATION_FAILURE_CASE_DECISION_CONFLICT,
        ORCHESTRATION_FAILURE_CASE_DECISION_NOT_ACTIVATABLE,
        ORCHESTRATION_FAILURE_CASE_DECISION_ACTIVATION_FAILED,
        ORCHESTRATION_FAILURE_PROPOSED_CHANGE_NOT_RESOLVABLE,
        ORCHESTRATION_FAILURE_PROPOSED_CHANGE_RESOLUTION_FAILED,
        ORCHESTRATION_FAILURE_BLOCKER_RESOLUTION_CONDITION_NOT_MET,
        ORCHESTRATION_FAILURE_ACTION_DUPLICATE,
        ORCHESTRATION_FAILURE_ACTION_PAYLOAD_INVALID,
        ORCHESTRATION_FAILURE_ACTION_STATE_TRANSITION_INVALID,
        ORCHESTRATION_FAILURE_ACTION_BLOCKED,
        ORCHESTRATION_FAILURE_UNSUPPORTED_REQUIREMENT_MAPPING,
        ORCHESTRATION_FAILURE_COMMIT_FAILED,
    }
)

ORCHESTRATION_DECISION_APPROVED = "approved"
ORCHESTRATION_DECISION_REJECTED = "rejected"

ORCHESTRATION_DECISION_CODES = frozenset(
    {ORCHESTRATION_DECISION_APPROVED, ORCHESTRATION_DECISION_REJECTED}
)


@dataclass(frozen=True)
class WorkflowOrchestrationContext:
    rental_case_id: int
    evaluated_case_revision: int
    lifecycle_state: str
    rental_case_facts: tuple[RentalCaseFact, ...] = ()
    blockers: tuple[Any, ...] = ()
    requirements: tuple[Any, ...] = ()
    open_questions: tuple[Any, ...] = ()
    approval_requests: tuple[Any, ...] = ()
    proposed_changes: tuple[Any, ...] = ()
    reschedule_requests: tuple[Any, ...] = ()
    case_decisions: tuple[Any, ...] = ()
    workflow_actions: tuple[Any, ...] = ()
    follow_ups: tuple[Any, ...] = ()
    milestones: tuple[Any, ...] = ()
    artifacts: tuple[Any, ...] = ()
    reasoning_projections: tuple[Any, ...] = ()
    reasoning_effects: tuple[WorkflowReasoningEffect, ...] = ()

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_non_negative_int("evaluated_case_revision", self.evaluated_case_revision)
        ensure_non_empty_text("lifecycle_state", self.lifecycle_state)
        if not isinstance(self.reasoning_effects, tuple):
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="reasoning_effects must be a tuple.",
            )
        for index, effect in enumerate(self.reasoning_effects):
            if not isinstance(effect, WorkflowReasoningEffect):
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"reasoning_effects[{index}] must be a WorkflowReasoningEffect.",
                )


@dataclass(frozen=True)
class BlockerPlanChange:
    semantic_issue_key: str
    blocker_type: str
    blocked_subject_type: str
    origin_entity_type: str
    severity: str
    resolution_condition_text: str
    blocked_subject_id: int | None = None
    blocked_subject_reference: str | None = None
    origin_entity_id: int | None = None
    origin_entity_reference: str | None = None
    resolution_reference: str | None = None
    rule_code: str | None = None
    evidence_reference_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ensure_non_empty_text("semantic_issue_key", self.semantic_issue_key)
        ensure_non_empty_text("blocker_type", self.blocker_type)
        if self.blocked_subject_type not in BLOCKED_SUBJECT_TYPE_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="blocked_subject_type must be a supported blocker subject type.",
            )
        ensure_optional_positive_int("blocked_subject_id", self.blocked_subject_id)
        ensure_optional_non_empty_text("blocked_subject_reference", self.blocked_subject_reference)
        ensure_non_empty_text("origin_entity_type", self.origin_entity_type)
        ensure_optional_positive_int("origin_entity_id", self.origin_entity_id)
        ensure_optional_non_empty_text("origin_entity_reference", self.origin_entity_reference)
        if self.severity not in SEVERITY_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="severity must be a supported blocker severity.",
            )
        ensure_non_empty_text("resolution_condition_text", self.resolution_condition_text)
        ensure_optional_non_empty_text("resolution_reference", self.resolution_reference)
        ensure_optional_non_empty_text("rule_code", self.rule_code)
        ensure_tuple_of_non_empty_text("evidence_reference_keys", self.evidence_reference_keys)
        if self.blocked_subject_id is None and self.blocked_subject_reference is None:
            raise Phase8ContractError(
                error_category="missing_value",
                safe_message="Blocker plan changes require a blocked subject id or reference.",
            )
        if self.origin_entity_id is None and self.origin_entity_reference is None:
            raise Phase8ContractError(
                error_category="missing_value",
                safe_message="Blocker plan changes require an origin entity id or reference.",
            )


@dataclass(frozen=True)
class ApprovalPlanChange:
    semantic_approval_key: str
    target_entity_type: str
    approval_type: str
    reason_text: str
    target_entity_id: int | None = None
    target_entity_reference: str | None = None
    evidence_reference_keys: tuple[str, ...] = ()
    required_approver_role: str | None = None
    required_approver_reference: str | None = None
    rule_code: str | None = None

    def __post_init__(self) -> None:
        ensure_non_empty_text("semantic_approval_key", self.semantic_approval_key)
        ensure_non_empty_text("target_entity_type", self.target_entity_type)
        ensure_non_empty_text("approval_type", self.approval_type)
        ensure_non_empty_text("reason_text", self.reason_text)
        ensure_optional_positive_int("target_entity_id", self.target_entity_id)
        ensure_optional_non_empty_text("target_entity_reference", self.target_entity_reference)
        ensure_tuple_of_non_empty_text("evidence_reference_keys", self.evidence_reference_keys)
        ensure_optional_non_empty_text("required_approver_role", self.required_approver_role)
        ensure_optional_non_empty_text("required_approver_reference", self.required_approver_reference)
        ensure_optional_non_empty_text("rule_code", self.rule_code)
        if self.target_entity_id is None and self.target_entity_reference is None:
            raise Phase8ContractError(
                error_category="missing_value",
                safe_message="Approval plan changes require a target entity id or reference.",
            )


@dataclass(frozen=True)
class WorkflowActionPlanChange:
    action_type: str
    action_category: str
    target_adapter_code: str
    reason_entity_type: str
    approval_posture: str
    semantic_subject_hash: str
    source_case_revision: int
    idempotency_key: str
    structured_payload: dict[str, Any]
    reason_entity_id: int | None = None
    reason_entity_reference: str | None = None
    target_scope_key: str | None = None
    due_at: str | None = None
    rule_code: str | None = None

    def __post_init__(self) -> None:
        if self.action_type not in WORKFLOW_ACTION_TYPES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="action_type must be a supported workflow action type.",
            )
        ensure_non_empty_text("action_category", self.action_category)
        ensure_non_empty_text("target_adapter_code", self.target_adapter_code)
        ensure_non_empty_text("reason_entity_type", self.reason_entity_type)
        if self.approval_posture not in APPROVAL_POSTURE_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="approval_posture must be a supported approval posture.",
            )
        ensure_non_empty_text("semantic_subject_hash", self.semantic_subject_hash)
        ensure_non_negative_int("source_case_revision", self.source_case_revision)
        ensure_non_empty_text("idempotency_key", self.idempotency_key)
        ensure_json_compatible("structured_payload", self.structured_payload)
        ensure_optional_positive_int("reason_entity_id", self.reason_entity_id)
        ensure_optional_non_empty_text("reason_entity_reference", self.reason_entity_reference)
        ensure_optional_non_empty_text("target_scope_key", self.target_scope_key)
        ensure_optional_non_empty_text("due_at", self.due_at)
        ensure_optional_non_empty_text("rule_code", self.rule_code)
        if self.reason_entity_id is None and self.reason_entity_reference is None:
            raise Phase8ContractError(
                error_category="missing_value",
                safe_message="WorkflowAction plan changes require a reason entity id or reference.",
            )


@dataclass(frozen=True)
class RequirementPlanChange:
    requirement_type: str
    domain_code: str
    applicability_basis: str
    blocking_scope: str
    evidence_reference: str | None = None
    owner_role: str | None = None
    owner_reference: str | None = None
    due_at: str | None = None
    rule_code: str | None = None

    def __post_init__(self) -> None:
        ensure_non_empty_text("requirement_type", self.requirement_type)
        ensure_non_empty_text("domain_code", self.domain_code)
        ensure_non_empty_text("applicability_basis", self.applicability_basis)
        if self.blocking_scope not in BLOCKING_SCOPE_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="blocking_scope must be a supported workflow blocking scope.",
            )
        ensure_optional_non_empty_text("evidence_reference", self.evidence_reference)
        ensure_optional_non_empty_text("owner_role", self.owner_role)
        ensure_optional_non_empty_text("owner_reference", self.owner_reference)
        ensure_optional_non_empty_text("due_at", self.due_at)
        ensure_optional_non_empty_text("rule_code", self.rule_code)


@dataclass(frozen=True)
class ArtifactFreshnessPlanChange:
    artifact_reference_id: int
    target_freshness_status: str
    reason_code: str

    def __post_init__(self) -> None:
        ensure_positive_int("artifact_reference_id", self.artifact_reference_id)
        if self.target_freshness_status not in ARTIFACT_FRESHNESS_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="target_freshness_status must be a supported artifact freshness code.",
            )
        ensure_non_empty_text("reason_code", self.reason_code)


@dataclass(frozen=True)
class WorkflowOrchestrationPlan:
    rental_case_id: int
    evaluated_case_revision: int
    proposed_blocker_creations: tuple[BlockerPlanChange, ...] = ()
    blocker_semantic_keys_to_resolve: tuple[str, ...] = ()
    proposed_approval_creations: tuple[ApprovalPlanChange, ...] = ()
    approval_semantic_keys_to_cancel: tuple[str, ...] = ()
    proposed_action_creations: tuple[WorkflowActionPlanChange, ...] = ()
    action_idempotency_keys_to_supersede: tuple[str, ...] = ()
    proposed_requirement_creations: tuple[RequirementPlanChange, ...] = ()
    artifact_freshness_updates: tuple[ArtifactFreshnessPlanChange, ...] = ()
    evidence_reference_keys: tuple[str, ...] = ()
    policy_codes: tuple[str, ...] = ()
    rule_codes: tuple[str, ...] = ()
    plan_fingerprint: str = ""
    contract_label: str = PHASE_8_ORCHESTRATION_CONTRACT_LABEL

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_non_negative_int("evaluated_case_revision", self.evaluated_case_revision)
        for index, change in enumerate(self.proposed_blocker_creations):
            if not isinstance(change, BlockerPlanChange):
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"proposed_blocker_creations[{index}] must be a BlockerPlanChange.",
                )
        ensure_tuple_of_non_empty_text("blocker_semantic_keys_to_resolve", self.blocker_semantic_keys_to_resolve)
        for index, change in enumerate(self.proposed_approval_creations):
            if not isinstance(change, ApprovalPlanChange):
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"proposed_approval_creations[{index}] must be an ApprovalPlanChange.",
                )
        ensure_tuple_of_non_empty_text("approval_semantic_keys_to_cancel", self.approval_semantic_keys_to_cancel)
        for index, change in enumerate(self.proposed_action_creations):
            if not isinstance(change, WorkflowActionPlanChange):
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"proposed_action_creations[{index}] must be a WorkflowActionPlanChange.",
                )
        ensure_tuple_of_non_empty_text("action_idempotency_keys_to_supersede", self.action_idempotency_keys_to_supersede)
        for index, change in enumerate(self.proposed_requirement_creations):
            if not isinstance(change, RequirementPlanChange):
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"proposed_requirement_creations[{index}] must be a RequirementPlanChange.",
                )
        for index, change in enumerate(self.artifact_freshness_updates):
            if not isinstance(change, ArtifactFreshnessPlanChange):
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"artifact_freshness_updates[{index}] must be an ArtifactFreshnessPlanChange.",
                )
        ensure_tuple_of_non_empty_text("evidence_reference_keys", self.evidence_reference_keys)
        ensure_tuple_of_non_empty_text("policy_codes", self.policy_codes)
        ensure_tuple_of_non_empty_text("rule_codes", self.rule_codes)
        ensure_non_empty_text("plan_fingerprint", self.plan_fingerprint)
        ensure_non_empty_text("contract_label", self.contract_label)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


@dataclass(frozen=True)
class WorkflowOrchestrationResult:
    rental_case_id: int
    case_revision_before: int
    case_revision_after: int
    created_blocker_ids: tuple[int, ...] = ()
    resolved_blocker_ids: tuple[int, ...] = ()
    created_approval_ids: tuple[int, ...] = ()
    updated_approval_ids: tuple[int, ...] = ()
    created_action_ids: tuple[int, ...] = ()
    superseded_action_ids: tuple[int, ...] = ()
    created_requirement_ids: tuple[int, ...] = ()
    activated_case_decision_ids: tuple[int, ...] = ()
    rejected_case_decision_ids: tuple[int, ...] = ()
    accepted_proposed_change_ids: tuple[int, ...] = ()
    rejected_proposed_change_ids: tuple[int, ...] = ()
    artifact_freshness_changed_ids: tuple[int, ...] = ()
    audit_event_ids: tuple[int, ...] = ()
    warning_codes: tuple[str, ...] = ()
    failure_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_non_negative_int("case_revision_before", self.case_revision_before)
        ensure_non_negative_int("case_revision_after", self.case_revision_after)
        for field_name in (
            "created_blocker_ids",
            "resolved_blocker_ids",
            "created_approval_ids",
            "updated_approval_ids",
            "created_action_ids",
            "superseded_action_ids",
            "created_requirement_ids",
            "activated_case_decision_ids",
            "rejected_case_decision_ids",
            "accepted_proposed_change_ids",
            "rejected_proposed_change_ids",
            "artifact_freshness_changed_ids",
            "audit_event_ids",
        ):
            values = getattr(self, field_name)
            if not isinstance(values, tuple):
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"{field_name} must be a tuple.",
                )
            for value in values:
                ensure_positive_int(field_name, value)
        ensure_tuple_of_non_empty_text("warning_codes", self.warning_codes)
        ensure_tuple_of_non_empty_text("failure_codes", self.failure_codes)
        for code in self.failure_codes:
            if code not in ORCHESTRATION_FAILURE_CODES:
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"failure_codes contains unsupported code: {code}.",
                )


@dataclass(frozen=True)
class ApprovalDecisionInput:
    rental_case_id: int
    approval_request_id: int
    decision: str
    expected_case_revision: int
    actor_reference: str
    actor_type: str | None = None
    decision_payload: Any = None
    decision_notes: str | None = None
    decided_at: str | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_positive_int("approval_request_id", self.approval_request_id)
        if self.decision not in ORCHESTRATION_DECISION_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="decision must be approved or rejected.",
            )
        ensure_non_negative_int("expected_case_revision", self.expected_case_revision)
        ensure_non_empty_text("actor_reference", self.actor_reference)
        ensure_optional_non_empty_text("actor_type", self.actor_type)
        ensure_json_compatible("decision_payload", self.decision_payload)
        ensure_optional_non_empty_text("decision_notes", self.decision_notes)
        ensure_optional_non_empty_text("decided_at", self.decided_at)


@dataclass(frozen=True)
class ApprovalDecisionResult:
    rental_case_id: int
    approval_request_id: int
    approval_status: str
    case_revision_before: int
    case_revision_after: int
    audit_event_ids: tuple[int, ...] = ()
    resolved_blocker_ids: tuple[int, ...] = ()
    activated_case_decision_id: int | None = None
    rejected_case_decision_id: int | None = None
    artifact_freshness_changed_ids: tuple[int, ...] = ()
    superseded_action_ids: tuple[int, ...] = ()
    failure_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_positive_int("approval_request_id", self.approval_request_id)
        if self.approval_status not in APPROVAL_REQUEST_STATUS_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="approval_status must be a supported approval request status.",
            )
        ensure_non_negative_int("case_revision_before", self.case_revision_before)
        ensure_non_negative_int("case_revision_after", self.case_revision_after)
        for field_name in ("audit_event_ids", "resolved_blocker_ids", "artifact_freshness_changed_ids", "superseded_action_ids"):
            ensure_tuple_of_positive_ints(field_name, getattr(self, field_name))
        ensure_optional_positive_int("activated_case_decision_id", self.activated_case_decision_id)
        ensure_optional_positive_int("rejected_case_decision_id", self.rejected_case_decision_id)
        ensure_tuple_of_non_empty_text("failure_codes", self.failure_codes)


@dataclass(frozen=True)
class CaseDecisionActivationRequest:
    rental_case_id: int
    case_decision_id: int
    approval_request_id: int
    expected_case_revision: int
    effective_value_payload: Any
    actor_reference: str
    actor_type: str | None = None
    source_reference: str | None = None
    effective_at: str | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_positive_int("case_decision_id", self.case_decision_id)
        ensure_positive_int("approval_request_id", self.approval_request_id)
        ensure_non_negative_int("expected_case_revision", self.expected_case_revision)
        ensure_json_compatible("effective_value_payload", self.effective_value_payload)
        ensure_non_empty_text("actor_reference", self.actor_reference)
        ensure_optional_non_empty_text("actor_type", self.actor_type)
        ensure_optional_non_empty_text("source_reference", self.source_reference)
        ensure_optional_non_empty_text("effective_at", self.effective_at)


@dataclass(frozen=True)
class CaseDecisionActivationResult:
    rental_case_id: int
    case_decision_id: int
    approval_request_id: int
    previous_case_revision: int
    new_case_revision: int
    workflow_event_ids: tuple[int, ...] = ()
    artifact_freshness_changed_ids: tuple[int, ...] = ()
    superseded_action_ids: tuple[int, ...] = ()
    failure_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_positive_int("case_decision_id", self.case_decision_id)
        ensure_positive_int("approval_request_id", self.approval_request_id)
        ensure_non_negative_int("previous_case_revision", self.previous_case_revision)
        ensure_non_negative_int("new_case_revision", self.new_case_revision)
        ensure_tuple_of_positive_ints("workflow_event_ids", self.workflow_event_ids)
        ensure_tuple_of_positive_ints("artifact_freshness_changed_ids", self.artifact_freshness_changed_ids)
        ensure_tuple_of_positive_ints("superseded_action_ids", self.superseded_action_ids)
        ensure_tuple_of_non_empty_text("failure_codes", self.failure_codes)


@dataclass(frozen=True)
class ProposedCaseChangeResolutionInput:
    rental_case_id: int
    proposed_case_change_id: int
    decision: str
    expected_case_revision: int
    actor_reference: str
    actor_type: str | None = None
    final_value_payload: Any = None
    decision_notes: str | None = None
    decided_at: str | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_positive_int("proposed_case_change_id", self.proposed_case_change_id)
        if self.decision not in ORCHESTRATION_DECISION_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="decision must be approved or rejected.",
            )
        ensure_non_negative_int("expected_case_revision", self.expected_case_revision)
        ensure_non_empty_text("actor_reference", self.actor_reference)
        ensure_optional_non_empty_text("actor_type", self.actor_type)
        ensure_json_compatible("final_value_payload", self.final_value_payload)
        ensure_optional_non_empty_text("decision_notes", self.decision_notes)
        ensure_optional_non_empty_text("decided_at", self.decided_at)


@dataclass(frozen=True)
class ProposedCaseChangeResolutionResult:
    rental_case_id: int
    proposed_case_change_id: int
    resulting_status: str
    case_revision_before: int
    case_revision_after: int
    updated_rental_case_fact_id: int | None = None
    audit_event_ids: tuple[int, ...] = ()
    artifact_freshness_changed_ids: tuple[int, ...] = ()
    superseded_action_ids: tuple[int, ...] = ()
    failure_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_positive_int("proposed_case_change_id", self.proposed_case_change_id)
        if self.resulting_status not in REQUIREMENT_STATUS_CODES | frozenset({"accepted", "rejected"}):
            # limited to accepted/rejected outputs, but keep the safe message compact
            if self.resulting_status not in {"accepted", "rejected"}:
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message="resulting_status must be accepted or rejected.",
                )
        ensure_non_negative_int("case_revision_before", self.case_revision_before)
        ensure_non_negative_int("case_revision_after", self.case_revision_after)
        ensure_optional_positive_int("updated_rental_case_fact_id", self.updated_rental_case_fact_id)
        ensure_tuple_of_positive_ints("audit_event_ids", self.audit_event_ids)
        ensure_tuple_of_positive_ints("artifact_freshness_changed_ids", self.artifact_freshness_changed_ids)
        ensure_tuple_of_positive_ints("superseded_action_ids", self.superseded_action_ids)
        ensure_tuple_of_non_empty_text("failure_codes", self.failure_codes)


@dataclass(frozen=True)
class WorkflowActionApprovalResult:
    rental_case_id: int
    approval_request_id: int
    workflow_action_id: int
    approval_status: str
    action_status_before: str
    action_status_after: str
    case_revision_before: int
    case_revision_after: int
    audit_event_ids: tuple[int, ...] = ()
    resolved_blocker_ids: tuple[int, ...] = ()
    failure_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_positive_int("approval_request_id", self.approval_request_id)
        ensure_positive_int("workflow_action_id", self.workflow_action_id)
        if self.approval_status not in APPROVAL_REQUEST_STATUS_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="approval_status must be a supported approval request status.",
            )
        if self.action_status_before not in WORKFLOW_ACTION_STATUS_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="action_status_before must be a supported workflow action status.",
            )
        if self.action_status_after not in WORKFLOW_ACTION_STATUS_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="action_status_after must be a supported workflow action status.",
            )
        ensure_non_negative_int("case_revision_before", self.case_revision_before)
        ensure_non_negative_int("case_revision_after", self.case_revision_after)
        ensure_tuple_of_positive_ints("audit_event_ids", self.audit_event_ids)
        ensure_tuple_of_positive_ints("resolved_blocker_ids", self.resolved_blocker_ids)
        ensure_tuple_of_non_empty_text("failure_codes", self.failure_codes)


@dataclass(frozen=True)
class CaseFactMutationRequest:
    rental_case_id: int
    expected_case_revision: int
    field_code: str
    domain_code: str
    new_value_payload: Any
    source_reference: str
    resolution_basis: str
    actor_reference: str
    actor_type: str | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_non_negative_int("expected_case_revision", self.expected_case_revision)
        ensure_non_empty_text("field_code", self.field_code)
        ensure_non_empty_text("domain_code", self.domain_code)
        ensure_json_compatible("new_value_payload", self.new_value_payload)
        ensure_non_empty_text("source_reference", self.source_reference)
        ensure_non_empty_text("resolution_basis", self.resolution_basis)
        ensure_non_empty_text("actor_reference", self.actor_reference)
        ensure_optional_non_empty_text("actor_type", self.actor_type)


@dataclass(frozen=True)
class CaseFactMutationResult:
    rental_case_id: int
    previous_case_revision: int
    new_case_revision: int
    workflow_event_id: int
    rental_case_fact_id: int | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_non_negative_int("previous_case_revision", self.previous_case_revision)
        ensure_non_negative_int("new_case_revision", self.new_case_revision)
        ensure_positive_int("workflow_event_id", self.workflow_event_id)
        ensure_optional_positive_int("rental_case_fact_id", self.rental_case_fact_id)


def ensure_tuple_of_positive_ints(field_name: str, values: tuple[int, ...]) -> None:
    if not isinstance(values, tuple):
        raise Phase8ContractError(
            error_category="invalid_value",
            safe_message=f"{field_name} must be a tuple of positive integers.",
        )
    for value in values:
        ensure_positive_int(field_name, value)
