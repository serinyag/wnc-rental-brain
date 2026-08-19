from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from .validation import (
    Phase8ContractError,
    ensure_allowed_value,
    ensure_at_least_one_present,
    ensure_bool,
    ensure_json_compatible,
    ensure_non_empty_text,
    ensure_non_negative_int,
    ensure_optional_non_empty_text,
    ensure_optional_positive_int,
    ensure_positive_int,
    ensure_tuple_of_non_empty_text,
)


PHASE_8_WORKFLOW_CONTRACT_VERSION = 1
PHASE_8_PHASE7_WORKFLOW_CONSUMPTION_CONTRACT_VERSION = 1
PHASE_8_PHASE7_WORKFLOW_CONSUMPTION_CONTRACT_LABEL = "phase8_phase7_workflow_consumption_v1"

REASONING_PURPOSE_FEASIBILITY_REVIEW = "feasibility_review"
REASONING_PURPOSE_PROPOSAL_READINESS_REVIEW = "proposal_readiness_review"
REASONING_PURPOSE_COMMERCIAL_RULE_REVIEW = "commercial_rule_review"
REASONING_PURPOSE_REQUIREMENT_DETECTION = "requirement_detection"
REASONING_PURPOSE_CHANGE_IMPACT_REVIEW = "change_impact_review"
REASONING_PURPOSE_RESCHEDULE_CONSEQUENCE_REVIEW = "reschedule_consequence_review"
REASONING_PURPOSE_EVENT_READINESS_REVIEW = "event_readiness_review"
REASONING_PURPOSE_COMPLIANCE_REQUIREMENT_REVIEW = "compliance_requirement_review"
REASONING_PURPOSE_CASE_DECISION_BASELINE = "case_decision_baseline"

REASONING_PURPOSE_CODES = frozenset(
    {
        REASONING_PURPOSE_FEASIBILITY_REVIEW,
        REASONING_PURPOSE_PROPOSAL_READINESS_REVIEW,
        REASONING_PURPOSE_COMMERCIAL_RULE_REVIEW,
        REASONING_PURPOSE_REQUIREMENT_DETECTION,
        REASONING_PURPOSE_CHANGE_IMPACT_REVIEW,
        REASONING_PURPOSE_RESCHEDULE_CONSEQUENCE_REVIEW,
        REASONING_PURPOSE_EVENT_READINESS_REVIEW,
        REASONING_PURPOSE_COMPLIANCE_REQUIREMENT_REVIEW,
        REASONING_PURPOSE_CASE_DECISION_BASELINE,
    }
)

PHASE_7_REASONING_STATE_RESOLVED = "resolved"
PHASE_7_REASONING_STATE_REQUIRES_CONFIRMATION = "requires_confirmation"
PHASE_7_REASONING_STATE_INSUFFICIENT_INFORMATION = "insufficient_information"
PHASE_7_REASONING_STATE_NO_APPLICABLE_RULE = "no_applicable_rule"
PHASE_7_REASONING_STATE_MANUAL_REVIEW_REQUIRED = "manual_review_required"
PHASE_7_REASONING_STATE_CURRENT_STATUS_UNKNOWN = "current_status_unknown"
PHASE_7_REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY = "insufficient_current_authority"

PHASE_7_REASONING_STATE_CODES = frozenset(
    {
        PHASE_7_REASONING_STATE_RESOLVED,
        PHASE_7_REASONING_STATE_REQUIRES_CONFIRMATION,
        PHASE_7_REASONING_STATE_INSUFFICIENT_INFORMATION,
        PHASE_7_REASONING_STATE_NO_APPLICABLE_RULE,
        PHASE_7_REASONING_STATE_MANUAL_REVIEW_REQUIRED,
        PHASE_7_REASONING_STATE_CURRENT_STATUS_UNKNOWN,
        PHASE_7_REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
    }
)

WORKFLOW_REASONING_POSTURE_SAFE_FOR_DETERMINISTIC_USE = "safe_for_deterministic_use"
WORKFLOW_REASONING_POSTURE_GUIDANCE_ONLY = "guidance_only"
WORKFLOW_REASONING_POSTURE_HISTORICAL_CONTEXT_ONLY = "historical_context_only"
WORKFLOW_REASONING_POSTURE_REVIEW_REQUIRED = "review_required"
WORKFLOW_REASONING_POSTURE_BLOCKED_FOR_CURRENT_DECISION = "blocked_for_current_decision"

WORKFLOW_REASONING_POSTURE_CODES = frozenset(
    {
        WORKFLOW_REASONING_POSTURE_SAFE_FOR_DETERMINISTIC_USE,
        WORKFLOW_REASONING_POSTURE_GUIDANCE_ONLY,
        WORKFLOW_REASONING_POSTURE_HISTORICAL_CONTEXT_ONLY,
        WORKFLOW_REASONING_POSTURE_REVIEW_REQUIRED,
        WORKFLOW_REASONING_POSTURE_BLOCKED_FOR_CURRENT_DECISION,
    }
)

WORKFLOW_REASONING_FRESHNESS_CURRENT = "current"
WORKFLOW_REASONING_FRESHNESS_STALE = "stale"
WORKFLOW_REASONING_FRESHNESS_SUPERSEDED = "superseded"

WORKFLOW_REASONING_FRESHNESS_CODES = frozenset(
    {
        WORKFLOW_REASONING_FRESHNESS_CURRENT,
        WORKFLOW_REASONING_FRESHNESS_STALE,
        WORKFLOW_REASONING_FRESHNESS_SUPERSEDED,
    }
)

WORKFLOW_CONFIDENTIALITY_LEVEL_EXTERNALLY_SHAREABLE = "externally_shareable"
WORKFLOW_CONFIDENTIALITY_LEVEL_INTERNAL = "internal"
WORKFLOW_CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE = "commercially_sensitive"
WORKFLOW_CONFIDENTIALITY_LEVEL_RESTRICTED = "restricted"

WORKFLOW_CONFIDENTIALITY_LEVEL_CODES = frozenset(
    {
        WORKFLOW_CONFIDENTIALITY_LEVEL_EXTERNALLY_SHAREABLE,
        WORKFLOW_CONFIDENTIALITY_LEVEL_INTERNAL,
        WORKFLOW_CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE,
        WORKFLOW_CONFIDENTIALITY_LEVEL_RESTRICTED,
    }
)

LIFECYCLE_STATE_INQUIRY_ACTIVE = "inquiry_active"
LIFECYCLE_STATE_PROPOSAL_IN_PROGRESS = "proposal_in_progress"
LIFECYCLE_STATE_PROPOSAL_PENDING_CLIENT = "proposal_pending_client"
LIFECYCLE_STATE_CONFIRMATION_PENDING = "confirmation_pending"
LIFECYCLE_STATE_CONFIRMED_PRE_EVENT = "confirmed_pre_event"
LIFECYCLE_STATE_EVENT_READY = "event_ready"
LIFECYCLE_STATE_EVENT_IN_PROGRESS = "event_in_progress"
LIFECYCLE_STATE_CLOSE_OUT_IN_PROGRESS = "close_out_in_progress"
LIFECYCLE_STATE_DORMANT = "dormant"
LIFECYCLE_STATE_CLOSED = "closed"
LIFECYCLE_STATE_CLOSED_LOST = "closed_lost"
LIFECYCLE_STATE_CANCELLED = "cancelled"

LIFECYCLE_STATES = frozenset(
    {
        LIFECYCLE_STATE_INQUIRY_ACTIVE,
        LIFECYCLE_STATE_PROPOSAL_IN_PROGRESS,
        LIFECYCLE_STATE_PROPOSAL_PENDING_CLIENT,
        LIFECYCLE_STATE_CONFIRMATION_PENDING,
        LIFECYCLE_STATE_CONFIRMED_PRE_EVENT,
        LIFECYCLE_STATE_EVENT_READY,
        LIFECYCLE_STATE_EVENT_IN_PROGRESS,
        LIFECYCLE_STATE_CLOSE_OUT_IN_PROGRESS,
        LIFECYCLE_STATE_DORMANT,
        LIFECYCLE_STATE_CLOSED,
        LIFECYCLE_STATE_CLOSED_LOST,
        LIFECYCLE_STATE_CANCELLED,
    }
)

BLOCKING_SCOPE_NONE = "none"
BLOCKING_SCOPE_ACTION = "action"
BLOCKING_SCOPE_TRANSITION = "transition"
BLOCKING_SCOPE_READINESS = "readiness"
BLOCKING_SCOPE_COMMERCIAL_SCOPE = "commercial_scope"

BLOCKING_SCOPE_CODES = frozenset(
    {
        BLOCKING_SCOPE_NONE,
        BLOCKING_SCOPE_ACTION,
        BLOCKING_SCOPE_TRANSITION,
        BLOCKING_SCOPE_READINESS,
        BLOCKING_SCOPE_COMMERCIAL_SCOPE,
    }
)

OPEN_QUESTION_STATUS_OPEN = "open"
OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION = "answered_pending_validation"
OPEN_QUESTION_STATUS_RESOLVED = "resolved"
OPEN_QUESTION_STATUS_CLOSED_NOT_NEEDED = "closed_not_needed"
OPEN_QUESTION_STATUS_SUPERSEDED = "superseded"

OPEN_QUESTION_STATUS_CODES = frozenset(
    {
        OPEN_QUESTION_STATUS_OPEN,
        OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION,
        OPEN_QUESTION_STATUS_RESOLVED,
        OPEN_QUESTION_STATUS_CLOSED_NOT_NEEDED,
        OPEN_QUESTION_STATUS_SUPERSEDED,
    }
)

REQUIREMENT_STATUS_NOT_APPLICABLE = "not_applicable"
REQUIREMENT_STATUS_REQUIRED = "required"
REQUIREMENT_STATUS_IN_PROGRESS = "in_progress"
REQUIREMENT_STATUS_SATISFIED = "satisfied"
REQUIREMENT_STATUS_WAIVED = "waived"
REQUIREMENT_STATUS_UNRESOLVED = "unresolved"

REQUIREMENT_STATUS_CODES = frozenset(
    {
        REQUIREMENT_STATUS_NOT_APPLICABLE,
        REQUIREMENT_STATUS_REQUIRED,
        REQUIREMENT_STATUS_IN_PROGRESS,
        REQUIREMENT_STATUS_SATISFIED,
        REQUIREMENT_STATUS_WAIVED,
        REQUIREMENT_STATUS_UNRESOLVED,
    }
)

BLOCKER_STATUS_OPEN = "open"
BLOCKER_STATUS_RESOLVED = "resolved"
BLOCKER_STATUS_SUPERSEDED = "superseded"
BLOCKER_STATUS_CANCELLED = "cancelled"

BLOCKER_STATUS_CODES = frozenset(
    {
        BLOCKER_STATUS_OPEN,
        BLOCKER_STATUS_RESOLVED,
        BLOCKER_STATUS_SUPERSEDED,
        BLOCKER_STATUS_CANCELLED,
    }
)

BLOCKED_SUBJECT_TYPE_TRANSITION = "transition"
BLOCKED_SUBJECT_TYPE_ACTION = "action"
BLOCKED_SUBJECT_TYPE_READINESS = "readiness"
BLOCKED_SUBJECT_TYPE_DECISION = "decision"
BLOCKED_SUBJECT_TYPE_ARTIFACT_REFRESH = "artifact_refresh"

BLOCKED_SUBJECT_TYPE_CODES = frozenset(
    {
        BLOCKED_SUBJECT_TYPE_TRANSITION,
        BLOCKED_SUBJECT_TYPE_ACTION,
        BLOCKED_SUBJECT_TYPE_READINESS,
        BLOCKED_SUBJECT_TYPE_DECISION,
        BLOCKED_SUBJECT_TYPE_ARTIFACT_REFRESH,
    }
)

SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"

SEVERITY_CODES = frozenset({SEVERITY_LOW, SEVERITY_MEDIUM, SEVERITY_HIGH})

CASE_DECISION_STATUS_PROPOSED = "proposed"
CASE_DECISION_STATUS_PENDING_APPROVAL = "pending_approval"
CASE_DECISION_STATUS_ACTIVE = "active"
CASE_DECISION_STATUS_REJECTED = "rejected"
CASE_DECISION_STATUS_SUPERSEDED = "superseded"
CASE_DECISION_STATUS_WITHDRAWN = "withdrawn"

CASE_DECISION_STATUS_CODES = frozenset(
    {
        CASE_DECISION_STATUS_PROPOSED,
        CASE_DECISION_STATUS_PENDING_APPROVAL,
        CASE_DECISION_STATUS_ACTIVE,
        CASE_DECISION_STATUS_REJECTED,
        CASE_DECISION_STATUS_SUPERSEDED,
        CASE_DECISION_STATUS_WITHDRAWN,
    }
)

APPROVAL_POSTURE_AUTOMATIC_ALLOWED = "automatic_allowed"
APPROVAL_POSTURE_APPROVAL_REQUIRED = "approval_required"
APPROVAL_POSTURE_HUMAN_ONLY = "human_only"
APPROVAL_POSTURE_BLOCKED = "blocked"

APPROVAL_POSTURE_CODES = frozenset(
    {
        APPROVAL_POSTURE_AUTOMATIC_ALLOWED,
        APPROVAL_POSTURE_APPROVAL_REQUIRED,
        APPROVAL_POSTURE_HUMAN_ONLY,
        APPROVAL_POSTURE_BLOCKED,
    }
)

CHANGE_IMPACT_LOW = "low_impact"
CHANGE_IMPACT_MATERIAL = "material_impact"
CHANGE_IMPACT_FUNDAMENTAL = "fundamental_scope_change"

CHANGE_IMPACT_CODES = frozenset(
    {
        CHANGE_IMPACT_LOW,
        CHANGE_IMPACT_MATERIAL,
        CHANGE_IMPACT_FUNDAMENTAL,
    }
)

PROPOSED_CHANGE_STATUS_PROPOSED = "proposed"
PROPOSED_CHANGE_STATUS_UNDER_REVIEW = "under_review"
PROPOSED_CHANGE_STATUS_ACCEPTED = "accepted"
PROPOSED_CHANGE_STATUS_REJECTED = "rejected"
PROPOSED_CHANGE_STATUS_SUPERSEDED = "superseded"
PROPOSED_CHANGE_STATUS_WITHDRAWN = "withdrawn"

PROPOSED_CHANGE_STATUS_CODES = frozenset(
    {
        PROPOSED_CHANGE_STATUS_PROPOSED,
        PROPOSED_CHANGE_STATUS_UNDER_REVIEW,
        PROPOSED_CHANGE_STATUS_ACCEPTED,
        PROPOSED_CHANGE_STATUS_REJECTED,
        PROPOSED_CHANGE_STATUS_SUPERSEDED,
        PROPOSED_CHANGE_STATUS_WITHDRAWN,
    }
)

RESCHEDULE_STATUS_PROPOSED = "proposed"
RESCHEDULE_STATUS_EVALUATING = "evaluating"
RESCHEDULE_STATUS_OFFERED = "offered"
RESCHEDULE_STATUS_AWAITING_CLIENT_CONFIRMATION = "awaiting_client_confirmation"
RESCHEDULE_STATUS_CONFIRMED = "confirmed"
RESCHEDULE_STATUS_REJECTED = "rejected"
RESCHEDULE_STATUS_WITHDRAWN = "withdrawn"
RESCHEDULE_STATUS_SUPERSEDED = "superseded"

RESCHEDULE_STATUS_CODES = frozenset(
    {
        RESCHEDULE_STATUS_PROPOSED,
        RESCHEDULE_STATUS_EVALUATING,
        RESCHEDULE_STATUS_OFFERED,
        RESCHEDULE_STATUS_AWAITING_CLIENT_CONFIRMATION,
        RESCHEDULE_STATUS_CONFIRMED,
        RESCHEDULE_STATUS_REJECTED,
        RESCHEDULE_STATUS_WITHDRAWN,
        RESCHEDULE_STATUS_SUPERSEDED,
    }
)

RESCHEDULE_URGENCY_NORMAL = "normal"
RESCHEDULE_URGENCY_URGENT_IMPACT = "urgent_impact"

RESCHEDULE_URGENCY_CODES = frozenset(
    {RESCHEDULE_URGENCY_NORMAL, RESCHEDULE_URGENCY_URGENT_IMPACT}
)

APPROVAL_REQUEST_STATUS_OPEN = "open"
APPROVAL_REQUEST_STATUS_APPROVED = "approved"
APPROVAL_REQUEST_STATUS_REJECTED = "rejected"
APPROVAL_REQUEST_STATUS_EXPIRED = "expired"
APPROVAL_REQUEST_STATUS_CANCELLED = "cancelled"
APPROVAL_REQUEST_STATUS_SUPERSEDED = "superseded"

APPROVAL_REQUEST_STATUS_CODES = frozenset(
    {
        APPROVAL_REQUEST_STATUS_OPEN,
        APPROVAL_REQUEST_STATUS_APPROVED,
        APPROVAL_REQUEST_STATUS_REJECTED,
        APPROVAL_REQUEST_STATUS_EXPIRED,
        APPROVAL_REQUEST_STATUS_CANCELLED,
        APPROVAL_REQUEST_STATUS_SUPERSEDED,
    }
)

ACTION_CATEGORY_COMMUNICATION = "communication"
ACTION_CATEGORY_DOCUMENT = "document"
ACTION_CATEGORY_COMMERCIAL = "commercial"
ACTION_CATEGORY_COORDINATION = "coordination"
ACTION_CATEGORY_COMPLIANCE = "compliance"
ACTION_CATEGORY_APPROVAL = "approval"
ACTION_CATEGORY_FOLLOW_UP = "follow_up"
ACTION_CATEGORY_SYNC = "sync"
ACTION_CATEGORY_INTERNAL_CONTROL = "internal_control"

ACTION_CATEGORY_CODES = frozenset(
    {
        ACTION_CATEGORY_COMMUNICATION,
        ACTION_CATEGORY_DOCUMENT,
        ACTION_CATEGORY_COMMERCIAL,
        ACTION_CATEGORY_COORDINATION,
        ACTION_CATEGORY_COMPLIANCE,
        ACTION_CATEGORY_APPROVAL,
        ACTION_CATEGORY_FOLLOW_UP,
        ACTION_CATEGORY_SYNC,
        ACTION_CATEGORY_INTERNAL_CONTROL,
    }
)

ACTION_TYPE_REQUEST_CLIENT_INFORMATION = "REQUEST_CLIENT_INFORMATION"
ACTION_TYPE_SEND_DISCOVERY_CALL_INVITE = "SEND_DISCOVERY_CALL_INVITE"
ACTION_TYPE_SEND_SITE_VISIT_PROPOSAL = "SEND_SITE_VISIT_PROPOSAL"
ACTION_TYPE_SEND_PROPOSAL_MESSAGE = "SEND_PROPOSAL_MESSAGE"
ACTION_TYPE_SEND_PROPOSAL_FOLLOW_UP = "SEND_PROPOSAL_FOLLOW_UP"
ACTION_TYPE_REQUEST_CONFIRMATION_PAYMENT = "REQUEST_CONFIRMATION_PAYMENT"
ACTION_TYPE_REQUEST_SIGNED_AGREEMENT = "REQUEST_SIGNED_AGREEMENT"
ACTION_TYPE_REQUEST_FINAL_EVENT_INFORMATION = "REQUEST_FINAL_EVENT_INFORMATION"
ACTION_TYPE_REQUEST_SUPPLIER_INFORMATION = "REQUEST_SUPPLIER_INFORMATION"
ACTION_TYPE_ESCALATE_COMPLIANCE_REVIEW = "ESCALATE_COMPLIANCE_REVIEW"
ACTION_TYPE_REQUEST_EXCEPTION_APPROVAL = "REQUEST_EXCEPTION_APPROVAL"
ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM = "CREATE_INTERNAL_TASK_ITEM"
ACTION_TYPE_CREATE_CALENDAR_HOLD = "CREATE_CALENDAR_HOLD"
ACTION_TYPE_CREATE_PAYMENT_REQUEST = "CREATE_PAYMENT_REQUEST"
ACTION_TYPE_DRAFT_PROPOSAL_ARTIFACT = "DRAFT_PROPOSAL_ARTIFACT"
ACTION_TYPE_DRAFT_AGREEMENT_ARTIFACT = "DRAFT_AGREEMENT_ARTIFACT"
ACTION_TYPE_DRAFT_INTERNAL_EVENT_BRIEF = "DRAFT_INTERNAL_EVENT_BRIEF"
ACTION_TYPE_SYNC_ARTIFACT_PROJECTION = "SYNC_ARTIFACT_PROJECTION"
ACTION_TYPE_MARK_ARTIFACT_REFRESH_REQUIRED = "MARK_ARTIFACT_REFRESH_REQUIRED"
ACTION_TYPE_SCHEDULE_FOLLOW_UP_REVIEW = "SCHEDULE_FOLLOW_UP_REVIEW"
ACTION_TYPE_ESCALATE_DORMANT_CASE_REVIEW = "ESCALATE_DORMANT_CASE_REVIEW"
ACTION_TYPE_SUPERSEDE_STALE_ACTIONS = "SUPERSEDE_STALE_ACTIONS"
ACTION_TYPE_RECORD_MANUAL_CLOSE_PACKET = "RECORD_MANUAL_CLOSE_PACKET"

WORKFLOW_ACTION_TYPES = frozenset(
    {
        ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
        ACTION_TYPE_SEND_DISCOVERY_CALL_INVITE,
        ACTION_TYPE_SEND_SITE_VISIT_PROPOSAL,
        ACTION_TYPE_SEND_PROPOSAL_MESSAGE,
        ACTION_TYPE_SEND_PROPOSAL_FOLLOW_UP,
        ACTION_TYPE_REQUEST_CONFIRMATION_PAYMENT,
        ACTION_TYPE_REQUEST_SIGNED_AGREEMENT,
        ACTION_TYPE_REQUEST_FINAL_EVENT_INFORMATION,
        ACTION_TYPE_REQUEST_SUPPLIER_INFORMATION,
        ACTION_TYPE_ESCALATE_COMPLIANCE_REVIEW,
        ACTION_TYPE_REQUEST_EXCEPTION_APPROVAL,
        ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
        ACTION_TYPE_CREATE_CALENDAR_HOLD,
        ACTION_TYPE_CREATE_PAYMENT_REQUEST,
        ACTION_TYPE_DRAFT_PROPOSAL_ARTIFACT,
        ACTION_TYPE_DRAFT_AGREEMENT_ARTIFACT,
        ACTION_TYPE_DRAFT_INTERNAL_EVENT_BRIEF,
        ACTION_TYPE_SYNC_ARTIFACT_PROJECTION,
        ACTION_TYPE_MARK_ARTIFACT_REFRESH_REQUIRED,
        ACTION_TYPE_SCHEDULE_FOLLOW_UP_REVIEW,
        ACTION_TYPE_ESCALATE_DORMANT_CASE_REVIEW,
        ACTION_TYPE_SUPERSEDE_STALE_ACTIONS,
        ACTION_TYPE_RECORD_MANUAL_CLOSE_PACKET,
    }
)

WORKFLOW_ACTION_STATUS_PROPOSED = "proposed"
WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL = "awaiting_approval"
WORKFLOW_ACTION_STATUS_APPROVED = "approved"
WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE = "ready_to_execute"
WORKFLOW_ACTION_STATUS_EXECUTING = "executing"
WORKFLOW_ACTION_STATUS_SUCCEEDED = "succeeded"
WORKFLOW_ACTION_STATUS_FAILED = "failed"
WORKFLOW_ACTION_STATUS_CANCELLED = "cancelled"
WORKFLOW_ACTION_STATUS_SUPERSEDED = "superseded"

WORKFLOW_ACTION_STATUS_CODES = frozenset(
    {
        WORKFLOW_ACTION_STATUS_PROPOSED,
        WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
        WORKFLOW_ACTION_STATUS_APPROVED,
        WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
        WORKFLOW_ACTION_STATUS_EXECUTING,
        WORKFLOW_ACTION_STATUS_SUCCEEDED,
        WORKFLOW_ACTION_STATUS_FAILED,
        WORKFLOW_ACTION_STATUS_CANCELLED,
        WORKFLOW_ACTION_STATUS_SUPERSEDED,
    }
)

EXECUTION_ATTEMPT_STATUS_STARTED = "started"
EXECUTION_ATTEMPT_STATUS_SUCCEEDED = "succeeded"
EXECUTION_ATTEMPT_STATUS_FAILED = "failed"
EXECUTION_ATTEMPT_STATUS_TIMEOUT = "timeout"
EXECUTION_ATTEMPT_STATUS_CANCELLED = "cancelled"

EXECUTION_ATTEMPT_STATUS_CODES = frozenset(
    {
        EXECUTION_ATTEMPT_STATUS_STARTED,
        EXECUTION_ATTEMPT_STATUS_SUCCEEDED,
        EXECUTION_ATTEMPT_STATUS_FAILED,
        EXECUTION_ATTEMPT_STATUS_TIMEOUT,
        EXECUTION_ATTEMPT_STATUS_CANCELLED,
    }
)

FOLLOW_UP_STATUS_SCHEDULED = "scheduled"
FOLLOW_UP_STATUS_DUE = "due"
FOLLOW_UP_STATUS_OVERDUE = "overdue"
FOLLOW_UP_STATUS_ESCALATED = "escalated"
FOLLOW_UP_STATUS_COMPLETED = "completed"
FOLLOW_UP_STATUS_CANCELLED = "cancelled"

FOLLOW_UP_REASON_INQUIRY_MISSING_INFORMATION = "inquiry_missing_information"
FOLLOW_UP_CADENCE_INQUIRY_COLD_WEEKLY = "inquiry_cold_weekly"

FOLLOW_UP_STATUS_CODES = frozenset(
    {
        FOLLOW_UP_STATUS_SCHEDULED,
        FOLLOW_UP_STATUS_DUE,
        FOLLOW_UP_STATUS_OVERDUE,
        FOLLOW_UP_STATUS_ESCALATED,
        FOLLOW_UP_STATUS_COMPLETED,
        FOLLOW_UP_STATUS_CANCELLED,
    }
)

FOLLOW_UP_URGENCY_LOW = "low"
FOLLOW_UP_URGENCY_MEDIUM = "medium"
FOLLOW_UP_URGENCY_HIGH = "high"
FOLLOW_UP_URGENCY_URGENT = "urgent"

FOLLOW_UP_URGENCY_CODES = frozenset(
    {
        FOLLOW_UP_URGENCY_LOW,
        FOLLOW_UP_URGENCY_MEDIUM,
        FOLLOW_UP_URGENCY_HIGH,
        FOLLOW_UP_URGENCY_URGENT,
    }
)

MILESTONE_STATUS_SCHEDULED = "scheduled"
MILESTONE_STATUS_REACHED = "reached"
MILESTONE_STATUS_COMPLETED = "completed"
MILESTONE_STATUS_MISSED = "missed"
MILESTONE_STATUS_SUPERSEDED = "superseded"

MILESTONE_STATUS_CODES = frozenset(
    {
        MILESTONE_STATUS_SCHEDULED,
        MILESTONE_STATUS_REACHED,
        MILESTONE_STATUS_COMPLETED,
        MILESTONE_STATUS_MISSED,
        MILESTONE_STATUS_SUPERSEDED,
    }
)

ARTIFACT_FRESHNESS_CURRENT = "current"
ARTIFACT_FRESHNESS_STALE = "stale"
ARTIFACT_FRESHNESS_REFRESH_REQUIRED = "refresh_required"
ARTIFACT_FRESHNESS_SUPERSEDED = "superseded"

ARTIFACT_FRESHNESS_CODES = frozenset(
    {
        ARTIFACT_FRESHNESS_CURRENT,
        ARTIFACT_FRESHNESS_STALE,
        ARTIFACT_FRESHNESS_REFRESH_REQUIRED,
        ARTIFACT_FRESHNESS_SUPERSEDED,
    }
)

ARTIFACT_TYPE_PROPOSAL = "proposal"
ARTIFACT_TYPE_AGREEMENT = "agreement"
ARTIFACT_TYPE_INTERNAL_EVENT_BRIEF = "internal_event_brief"
ARTIFACT_TYPE_READINESS_SUMMARY = "readiness_summary"
ARTIFACT_TYPE_STAFFING_PLAN = "staffing_plan"
ARTIFACT_TYPE_SUPPLIER_PLAN = "supplier_plan"
ARTIFACT_TYPE_TASK_SURFACE_PROJECTION = "task_surface_projection"
ARTIFACT_TYPE_CALENDAR_PROJECTION = "calendar_projection"

ARTIFACT_TYPE_CODES = frozenset(
    {
        ARTIFACT_TYPE_PROPOSAL,
        ARTIFACT_TYPE_AGREEMENT,
        ARTIFACT_TYPE_INTERNAL_EVENT_BRIEF,
        ARTIFACT_TYPE_READINESS_SUMMARY,
        ARTIFACT_TYPE_STAFFING_PLAN,
        ARTIFACT_TYPE_SUPPLIER_PLAN,
        ARTIFACT_TYPE_TASK_SURFACE_PROJECTION,
        ARTIFACT_TYPE_CALENDAR_PROJECTION,
    }
)

AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT = "DETERMINISTIC_CURRENT"
AUTHORITY_OUTCOME_CURRENT_GUIDANCE = "CURRENT_GUIDANCE"
AUTHORITY_OUTCOME_HISTORICAL_PRECEDENT = "HISTORICAL_PRECEDENT"
AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY = "MIXED_WITH_CURRENT_PRIORITY"
AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION = "REQUIRES_CONFIRMATION"
AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY = "INSUFFICIENT_CURRENT_AUTHORITY"

AUTHORITY_OUTCOME_CODES = frozenset(
    {
        AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
        AUTHORITY_OUTCOME_CURRENT_GUIDANCE,
        AUTHORITY_OUTCOME_HISTORICAL_PRECEDENT,
        AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY,
        AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION,
        AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
    }
)

CONFLICT_TYPE_A_P4_BEATS_P6 = "TYPE_A_P4_BEATS_P6"
CONFLICT_TYPE_B_P5_BEATS_P6 = "TYPE_B_P5_BEATS_P6"
CONFLICT_TYPE_C_P6_EXISTS_BUT_CURRENT_MISSING = "TYPE_C_P6_EXISTS_BUT_CURRENT_MISSING"
CONFLICT_TYPE_D_P4_REQUIRES_CONFIRMATION = "TYPE_D_P4_REQUIRES_CONFIRMATION"
CONFLICT_TYPE_E_P5_FAILURE_P4_SURVIVES = "TYPE_E_P5_FAILURE_P4_SURVIVES"
CONFLICT_TYPE_F_LIMITED_OR_UNKNOWN_PRECEDENT = "TYPE_F_LIMITED_OR_UNKNOWN_PRECEDENT"
CONFLICT_TYPE_G_CONFIDENTIALITY_ESCALATION = "TYPE_G_CONFIDENTIALITY_ESCALATION"

CONFLICT_TYPE_CODES = frozenset(
    {
        CONFLICT_TYPE_A_P4_BEATS_P6,
        CONFLICT_TYPE_B_P5_BEATS_P6,
        CONFLICT_TYPE_C_P6_EXISTS_BUT_CURRENT_MISSING,
        CONFLICT_TYPE_D_P4_REQUIRES_CONFIRMATION,
        CONFLICT_TYPE_E_P5_FAILURE_P4_SURVIVES,
        CONFLICT_TYPE_F_LIMITED_OR_UNKNOWN_PRECEDENT,
        CONFLICT_TYPE_G_CONFIDENTIALITY_ESCALATION,
    }
)

CONTAMINATION_CODE_HISTORICAL_PRICE_TO_CURRENT_PRICE = "historical_price_to_current_price"
CONTAMINATION_CODE_HISTORICAL_PERSON_CAPABILITY_TO_CURRENT_SERVICE = "historical_person_capability_to_current_service"
CONTAMINATION_CODE_HISTORICAL_CONCESSION_TO_CURRENT_POLICY = "historical_concession_to_current_policy"
CONTAMINATION_CODE_HISTORICAL_LEGAL_SOLUTION_TO_CURRENT_GUIDANCE = "historical_legal_solution_to_current_guidance"
CONTAMINATION_CODE_HISTORICAL_OVERTIME_HANDLING_TO_CURRENT_RATE = "historical_overtime_handling_to_current_rate"
CONTAMINATION_CODE_HISTORICAL_ROOM_USE_TO_CURRENT_ACCESS_RIGHT = "historical_room_use_to_current_access_right"

CONTAMINATION_CODE_CODES = frozenset(
    {
        CONTAMINATION_CODE_HISTORICAL_PRICE_TO_CURRENT_PRICE,
        CONTAMINATION_CODE_HISTORICAL_PERSON_CAPABILITY_TO_CURRENT_SERVICE,
        CONTAMINATION_CODE_HISTORICAL_CONCESSION_TO_CURRENT_POLICY,
        CONTAMINATION_CODE_HISTORICAL_LEGAL_SOLUTION_TO_CURRENT_GUIDANCE,
        CONTAMINATION_CODE_HISTORICAL_OVERTIME_HANDLING_TO_CURRENT_RATE,
        CONTAMINATION_CODE_HISTORICAL_ROOM_USE_TO_CURRENT_ACCESS_RIGHT,
    }
)


@dataclass(frozen=True)
class LifecycleState:
    value: str

    def __post_init__(self) -> None:
        ensure_allowed_value("value", self.value, LIFECYCLE_STATES)


@dataclass(frozen=True)
class ChangeImpact:
    value: str

    def __post_init__(self) -> None:
        ensure_allowed_value("value", self.value, CHANGE_IMPACT_CODES)


@dataclass(frozen=True)
class ApprovalPosture:
    value: str

    def __post_init__(self) -> None:
        ensure_allowed_value("value", self.value, APPROVAL_POSTURE_CODES)


@dataclass(frozen=True)
class WorkflowActionStatus:
    value: str

    def __post_init__(self) -> None:
        ensure_allowed_value("value", self.value, WORKFLOW_ACTION_STATUS_CODES)


@dataclass(frozen=True)
class RentalCase:
    rental_case_id: int
    rental_case_uuid: str
    case_reference_code: str
    lifecycle_state: str
    case_revision: int
    rental_type_code: str
    commercial_summary_status: str
    operational_summary_status: str
    is_active: bool
    active_event_start: str | None = None
    active_event_end: str | None = None
    service_level_or_type: str | None = None
    client_account_ref: str | None = None
    primary_contact_ref: str | None = None
    dormant_origin_state: str | None = None
    resume_target_state: str | None = None
    dormant_reason_code: str | None = None
    dormant_review_at: str | None = None
    current_proposal_artifact_id: int | None = None
    current_agreement_artifact_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_non_empty_text("rental_case_uuid", self.rental_case_uuid)
        ensure_non_empty_text("case_reference_code", self.case_reference_code)
        ensure_allowed_value("lifecycle_state", self.lifecycle_state, LIFECYCLE_STATES)
        ensure_non_negative_int("case_revision", self.case_revision)
        ensure_non_empty_text("rental_type_code", self.rental_type_code)
        ensure_non_empty_text("commercial_summary_status", self.commercial_summary_status)
        ensure_non_empty_text("operational_summary_status", self.operational_summary_status)
        ensure_bool("is_active", self.is_active)
        ensure_optional_non_empty_text("active_event_start", self.active_event_start)
        ensure_optional_non_empty_text("active_event_end", self.active_event_end)
        ensure_optional_non_empty_text("service_level_or_type", self.service_level_or_type)
        ensure_optional_non_empty_text("client_account_ref", self.client_account_ref)
        ensure_optional_non_empty_text("primary_contact_ref", self.primary_contact_ref)
        if self.dormant_origin_state is not None:
            ensure_allowed_value("dormant_origin_state", self.dormant_origin_state, LIFECYCLE_STATES)
        if self.resume_target_state is not None:
            ensure_allowed_value("resume_target_state", self.resume_target_state, LIFECYCLE_STATES)
        ensure_optional_non_empty_text("dormant_reason_code", self.dormant_reason_code)
        ensure_optional_non_empty_text("dormant_review_at", self.dormant_review_at)
        ensure_optional_positive_int("current_proposal_artifact_id", self.current_proposal_artifact_id)
        ensure_optional_positive_int("current_agreement_artifact_id", self.current_agreement_artifact_id)
        ensure_optional_non_empty_text("created_at", self.created_at)
        ensure_optional_non_empty_text("updated_at", self.updated_at)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


@dataclass(frozen=True)
class LifecycleTransition:
    lifecycle_transition_id: int
    rental_case_id: int
    to_lifecycle_state: str
    transition_reason_code: str
    case_revision_before: int
    case_revision_after: int
    occurred_at: str
    from_lifecycle_state: str | None = None
    triggering_event_id: int | None = None
    source_type: str | None = None
    source_reference: str | None = None
    actor_type: str | None = None
    actor_reference: str | None = None
    override_applied: bool = False

    def __post_init__(self) -> None:
        ensure_positive_int("lifecycle_transition_id", self.lifecycle_transition_id)
        ensure_positive_int("rental_case_id", self.rental_case_id)
        if self.from_lifecycle_state is not None:
            ensure_allowed_value("from_lifecycle_state", self.from_lifecycle_state, LIFECYCLE_STATES)
        ensure_allowed_value("to_lifecycle_state", self.to_lifecycle_state, LIFECYCLE_STATES)
        ensure_non_empty_text("transition_reason_code", self.transition_reason_code)
        ensure_non_negative_int("case_revision_before", self.case_revision_before)
        ensure_non_negative_int("case_revision_after", self.case_revision_after)
        if self.case_revision_after < self.case_revision_before:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="case_revision_after must be greater than or equal to case_revision_before.",
            )
        ensure_non_empty_text("occurred_at", self.occurred_at)
        ensure_optional_positive_int("triggering_event_id", self.triggering_event_id)
        ensure_optional_non_empty_text("source_type", self.source_type)
        ensure_optional_non_empty_text("source_reference", self.source_reference)
        ensure_optional_non_empty_text("actor_type", self.actor_type)
        ensure_optional_non_empty_text("actor_reference", self.actor_reference)
        ensure_bool("override_applied", self.override_applied)


@dataclass(frozen=True)
class WorkflowEvent:
    workflow_event_id: int
    workflow_event_uuid: str
    rental_case_id: int
    event_type_code: str
    source_type: str
    occurred_at: str
    recorded_at: str
    structured_payload: dict[str, Any]
    source_reference: str | None = None
    actor_type: str | None = None
    actor_reference: str | None = None
    event_identity_key: str | None = None
    origin_metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ensure_positive_int("workflow_event_id", self.workflow_event_id)
        ensure_non_empty_text("workflow_event_uuid", self.workflow_event_uuid)
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_non_empty_text("event_type_code", self.event_type_code)
        ensure_non_empty_text("source_type", self.source_type)
        ensure_non_empty_text("occurred_at", self.occurred_at)
        ensure_non_empty_text("recorded_at", self.recorded_at)
        ensure_json_compatible("structured_payload", self.structured_payload)
        ensure_optional_non_empty_text("source_reference", self.source_reference)
        ensure_optional_non_empty_text("actor_type", self.actor_type)
        ensure_optional_non_empty_text("actor_reference", self.actor_reference)
        ensure_optional_non_empty_text("event_identity_key", self.event_identity_key)
        ensure_json_compatible("origin_metadata", self.origin_metadata)


@dataclass(frozen=True)
class OpenQuestion:
    open_question_id: int
    rental_case_id: int
    question_type: str
    domain_code: str
    human_question_text: str
    blocking_scope: str
    status: str
    created_at: str
    requested_from_role: str | None = None
    proposed_answer_payload: Any = None
    source_reference: str | None = None
    supersedes_open_question_id: int | None = None
    resolved_at: str | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("open_question_id", self.open_question_id)
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_non_empty_text("question_type", self.question_type)
        ensure_non_empty_text("domain_code", self.domain_code)
        ensure_non_empty_text("human_question_text", self.human_question_text)
        ensure_allowed_value("blocking_scope", self.blocking_scope, BLOCKING_SCOPE_CODES)
        ensure_allowed_value("status", self.status, OPEN_QUESTION_STATUS_CODES)
        ensure_non_empty_text("created_at", self.created_at)
        ensure_optional_non_empty_text("requested_from_role", self.requested_from_role)
        ensure_json_compatible("proposed_answer_payload", self.proposed_answer_payload)
        ensure_optional_non_empty_text("source_reference", self.source_reference)
        ensure_optional_positive_int("supersedes_open_question_id", self.supersedes_open_question_id)
        ensure_optional_non_empty_text("resolved_at", self.resolved_at)


@dataclass(frozen=True)
class Requirement:
    requirement_id: int
    rental_case_id: int
    requirement_type: str
    domain_code: str
    applicability_basis: str
    status: str
    blocking_scope: str
    created_at: str
    owner_role: str | None = None
    owner_reference: str | None = None
    due_at: str | None = None
    evidence_reference: str | None = None
    waiver_case_decision_id: int | None = None
    resolved_at: str | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("requirement_id", self.requirement_id)
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_non_empty_text("requirement_type", self.requirement_type)
        ensure_non_empty_text("domain_code", self.domain_code)
        ensure_non_empty_text("applicability_basis", self.applicability_basis)
        ensure_allowed_value("status", self.status, REQUIREMENT_STATUS_CODES)
        ensure_allowed_value("blocking_scope", self.blocking_scope, BLOCKING_SCOPE_CODES)
        ensure_non_empty_text("created_at", self.created_at)
        ensure_optional_non_empty_text("owner_role", self.owner_role)
        ensure_optional_non_empty_text("owner_reference", self.owner_reference)
        ensure_optional_non_empty_text("due_at", self.due_at)
        ensure_optional_non_empty_text("evidence_reference", self.evidence_reference)
        ensure_optional_positive_int("waiver_case_decision_id", self.waiver_case_decision_id)
        ensure_optional_non_empty_text("resolved_at", self.resolved_at)


@dataclass(frozen=True)
class Blocker:
    blocker_id: int
    rental_case_id: int
    blocker_type: str
    blocked_subject_type: str
    origin_entity_type: str
    severity: str
    status: str
    resolution_condition_text: str
    opened_at: str
    blocked_subject_id: int | None = None
    blocked_subject_reference: str | None = None
    origin_entity_id: int | None = None
    origin_entity_reference: str | None = None
    resolution_reference: str | None = None
    supersedes_blocker_id: int | None = None
    resolved_at: str | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("blocker_id", self.blocker_id)
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_non_empty_text("blocker_type", self.blocker_type)
        ensure_allowed_value("blocked_subject_type", self.blocked_subject_type, BLOCKED_SUBJECT_TYPE_CODES)
        ensure_at_least_one_present("blocked_subject", (self.blocked_subject_id, self.blocked_subject_reference))
        ensure_non_empty_text("origin_entity_type", self.origin_entity_type)
        ensure_at_least_one_present("origin_entity", (self.origin_entity_id, self.origin_entity_reference))
        ensure_allowed_value("severity", self.severity, SEVERITY_CODES)
        ensure_allowed_value("status", self.status, BLOCKER_STATUS_CODES)
        ensure_non_empty_text("resolution_condition_text", self.resolution_condition_text)
        ensure_non_empty_text("opened_at", self.opened_at)
        ensure_optional_positive_int("blocked_subject_id", self.blocked_subject_id)
        ensure_optional_non_empty_text("blocked_subject_reference", self.blocked_subject_reference)
        ensure_optional_positive_int("origin_entity_id", self.origin_entity_id)
        ensure_optional_non_empty_text("origin_entity_reference", self.origin_entity_reference)
        ensure_optional_non_empty_text("resolution_reference", self.resolution_reference)
        ensure_optional_positive_int("supersedes_blocker_id", self.supersedes_blocker_id)
        ensure_optional_non_empty_text("resolved_at", self.resolved_at)


@dataclass(frozen=True)
class CaseDecision:
    case_decision_id: int
    rental_case_id: int
    decision_type: str
    domain_code: str
    baseline_reference: str
    proposed_value_payload: Any
    scope_key: str
    scope_description: str
    authority_basis: str
    approval_posture: str
    status: str
    created_at: str
    effective_value_payload: Any = None
    evidence_reference: str | None = None
    approval_request_id: int | None = None
    effective_at: str | None = None
    supersedes_case_decision_id: int | None = None
    updated_at: str | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("case_decision_id", self.case_decision_id)
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_non_empty_text("decision_type", self.decision_type)
        ensure_non_empty_text("domain_code", self.domain_code)
        ensure_non_empty_text("baseline_reference", self.baseline_reference)
        ensure_json_compatible("proposed_value_payload", self.proposed_value_payload)
        ensure_non_empty_text("scope_key", self.scope_key)
        ensure_non_empty_text("scope_description", self.scope_description)
        ensure_non_empty_text("authority_basis", self.authority_basis)
        ensure_allowed_value("approval_posture", self.approval_posture, APPROVAL_POSTURE_CODES)
        ensure_allowed_value("status", self.status, CASE_DECISION_STATUS_CODES)
        ensure_non_empty_text("created_at", self.created_at)
        ensure_json_compatible("effective_value_payload", self.effective_value_payload)
        ensure_optional_non_empty_text("evidence_reference", self.evidence_reference)
        ensure_optional_positive_int("approval_request_id", self.approval_request_id)
        ensure_optional_non_empty_text("effective_at", self.effective_at)
        ensure_optional_positive_int("supersedes_case_decision_id", self.supersedes_case_decision_id)
        ensure_optional_non_empty_text("updated_at", self.updated_at)
        if self.status == CASE_DECISION_STATUS_ACTIVE:
            if self.effective_at is None or self.effective_value_payload is None:
                raise Phase8ContractError(
                    error_category="missing_value",
                    safe_message="active CaseDecision records require effective_at and effective_value_payload.",
                )
            if self.approval_posture == APPROVAL_POSTURE_BLOCKED:
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message="active CaseDecision records cannot use approval_posture=blocked.",
                )
            if self.approval_posture == APPROVAL_POSTURE_APPROVAL_REQUIRED and self.approval_request_id is None:
                raise Phase8ContractError(
                    error_category="missing_value",
                    safe_message="active CaseDecision records with approval_required posture must include approval_request_id.",
                )


@dataclass(frozen=True)
class ProposedCaseChange:
    proposed_case_change_id: int
    rental_case_id: int
    change_kind: str
    domain_code: str
    proposed_value_payload: Any
    status: str
    detected_at: str
    prior_value_payload: Any = None
    source_reference: str | None = None
    impact_classification: str | None = None
    affected_domain_codes: tuple[str, ...] = ()
    review_posture: str | None = None
    final_value_payload: Any = None
    supersedes_proposed_change_id: int | None = None
    accepted_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("proposed_case_change_id", self.proposed_case_change_id)
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_non_empty_text("change_kind", self.change_kind)
        ensure_non_empty_text("domain_code", self.domain_code)
        ensure_json_compatible("proposed_value_payload", self.proposed_value_payload)
        ensure_allowed_value("status", self.status, PROPOSED_CHANGE_STATUS_CODES)
        ensure_non_empty_text("detected_at", self.detected_at)
        ensure_json_compatible("prior_value_payload", self.prior_value_payload)
        ensure_optional_non_empty_text("source_reference", self.source_reference)
        if self.impact_classification is not None:
            ensure_allowed_value("impact_classification", self.impact_classification, CHANGE_IMPACT_CODES)
        ensure_tuple_of_non_empty_text("affected_domain_codes", self.affected_domain_codes)
        if self.review_posture is not None:
            ensure_allowed_value("review_posture", self.review_posture, APPROVAL_POSTURE_CODES)
        ensure_json_compatible("final_value_payload", self.final_value_payload)
        ensure_optional_positive_int("supersedes_proposed_change_id", self.supersedes_proposed_change_id)
        ensure_optional_non_empty_text("accepted_at", self.accepted_at)
        ensure_optional_non_empty_text("created_at", self.created_at)
        ensure_optional_non_empty_text("updated_at", self.updated_at)
        if self.status == PROPOSED_CHANGE_STATUS_ACCEPTED and (self.final_value_payload is None or self.accepted_at is None):
            raise Phase8ContractError(
                error_category="missing_value",
                safe_message="accepted ProposedCaseChange records require final_value_payload and accepted_at.",
            )


@dataclass(frozen=True)
class RescheduleRequest:
    reschedule_request_id: int
    rental_case_id: int
    current_active_date_snapshot: dict[str, Any]
    requested_date_payload: dict[str, Any]
    candidate_dates_payload: tuple[dict[str, Any], ...]
    consequence_summary_payload: dict[str, Any]
    status: str
    urgency_class: str
    created_at: str
    confirmed_proposed_change_id: int | None = None
    confirmed_at: str | None = None
    updated_at: str | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("reschedule_request_id", self.reschedule_request_id)
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_json_compatible("current_active_date_snapshot", self.current_active_date_snapshot)
        ensure_json_compatible("requested_date_payload", self.requested_date_payload)
        ensure_json_compatible("candidate_dates_payload", self.candidate_dates_payload)
        ensure_json_compatible("consequence_summary_payload", self.consequence_summary_payload)
        ensure_allowed_value("status", self.status, RESCHEDULE_STATUS_CODES)
        ensure_allowed_value("urgency_class", self.urgency_class, RESCHEDULE_URGENCY_CODES)
        ensure_non_empty_text("created_at", self.created_at)
        ensure_optional_positive_int("confirmed_proposed_change_id", self.confirmed_proposed_change_id)
        ensure_optional_non_empty_text("confirmed_at", self.confirmed_at)
        ensure_optional_non_empty_text("updated_at", self.updated_at)
        if self.status == RESCHEDULE_STATUS_CONFIRMED and (
            self.confirmed_proposed_change_id is None or self.confirmed_at is None
        ):
            raise Phase8ContractError(
                error_category="missing_value",
                safe_message="confirmed RescheduleRequest records require confirmed_proposed_change_id and confirmed_at.",
            )


@dataclass(frozen=True)
class ApprovalRequest:
    approval_request_id: int
    rental_case_id: int
    target_entity_type: str
    approval_type: str
    reason_text: str
    status: str
    created_at: str
    target_entity_id: int | None = None
    target_entity_reference: str | None = None
    evidence_reference_keys: tuple[str, ...] = ()
    required_approver_role: str | None = None
    required_approver_reference: str | None = None
    decision_payload: Any = None
    decided_at: str | None = None
    decided_by_reference: str | None = None
    decision_notes: str | None = None
    supersedes_approval_request_id: int | None = None
    updated_at: str | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("approval_request_id", self.approval_request_id)
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_non_empty_text("target_entity_type", self.target_entity_type)
        ensure_at_least_one_present("target_entity", (self.target_entity_id, self.target_entity_reference))
        ensure_non_empty_text("approval_type", self.approval_type)
        ensure_non_empty_text("reason_text", self.reason_text)
        ensure_allowed_value("status", self.status, APPROVAL_REQUEST_STATUS_CODES)
        ensure_non_empty_text("created_at", self.created_at)
        ensure_optional_positive_int("target_entity_id", self.target_entity_id)
        ensure_optional_non_empty_text("target_entity_reference", self.target_entity_reference)
        ensure_tuple_of_non_empty_text("evidence_reference_keys", self.evidence_reference_keys)
        ensure_optional_non_empty_text("required_approver_role", self.required_approver_role)
        ensure_optional_non_empty_text("required_approver_reference", self.required_approver_reference)
        ensure_json_compatible("decision_payload", self.decision_payload)
        ensure_optional_non_empty_text("decided_at", self.decided_at)
        ensure_optional_non_empty_text("decided_by_reference", self.decided_by_reference)
        ensure_optional_non_empty_text("decision_notes", self.decision_notes)
        ensure_optional_positive_int("supersedes_approval_request_id", self.supersedes_approval_request_id)
        ensure_optional_non_empty_text("updated_at", self.updated_at)
        if self.status in {APPROVAL_REQUEST_STATUS_APPROVED, APPROVAL_REQUEST_STATUS_REJECTED} and self.decided_at is None:
            raise Phase8ContractError(
                error_category="missing_value",
                safe_message="approved and rejected ApprovalRequest records require decided_at.",
            )


@dataclass(frozen=True)
class WorkflowAction:
    workflow_action_id: int
    workflow_action_uuid: str
    rental_case_id: int
    action_type: str
    action_category: str
    target_adapter_code: str
    reason_entity_type: str
    approval_posture: str
    status: str
    semantic_subject_hash: str
    source_case_revision: int
    idempotency_key: str
    structured_payload: dict[str, Any] = field(default_factory=dict)
    reason_entity_id: int | None = None
    reason_entity_reference: str | None = None
    target_scope_key: str | None = None
    due_at: str | None = None
    supersedes_workflow_action_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("workflow_action_id", self.workflow_action_id)
        ensure_non_empty_text("workflow_action_uuid", self.workflow_action_uuid)
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_allowed_value("action_type", self.action_type, WORKFLOW_ACTION_TYPES)
        ensure_allowed_value("action_category", self.action_category, ACTION_CATEGORY_CODES)
        ensure_non_empty_text("target_adapter_code", self.target_adapter_code)
        ensure_non_empty_text("reason_entity_type", self.reason_entity_type)
        ensure_at_least_one_present("reason_entity", (self.reason_entity_id, self.reason_entity_reference))
        ensure_allowed_value("approval_posture", self.approval_posture, APPROVAL_POSTURE_CODES)
        ensure_allowed_value("status", self.status, WORKFLOW_ACTION_STATUS_CODES)
        ensure_non_empty_text("semantic_subject_hash", self.semantic_subject_hash)
        ensure_non_negative_int("source_case_revision", self.source_case_revision)
        ensure_non_empty_text("idempotency_key", self.idempotency_key)
        ensure_json_compatible("structured_payload", self.structured_payload)
        ensure_optional_positive_int("reason_entity_id", self.reason_entity_id)
        ensure_optional_non_empty_text("reason_entity_reference", self.reason_entity_reference)
        ensure_optional_non_empty_text("target_scope_key", self.target_scope_key)
        ensure_optional_non_empty_text("due_at", self.due_at)
        ensure_optional_positive_int("supersedes_workflow_action_id", self.supersedes_workflow_action_id)
        ensure_optional_non_empty_text("created_at", self.created_at)
        ensure_optional_non_empty_text("updated_at", self.updated_at)


@dataclass(frozen=True)
class ExecutionAttempt:
    execution_attempt_id: int
    execution_attempt_uuid: str
    workflow_action_id: int
    rental_case_id: int
    attempt_number: int
    adapter_code: str
    started_at: str
    status: str
    retry_eligible: bool
    response_snapshot: Any
    completed_at: str | None = None
    external_reference: str | None = None
    failure_code: str | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("execution_attempt_id", self.execution_attempt_id)
        ensure_non_empty_text("execution_attempt_uuid", self.execution_attempt_uuid)
        ensure_positive_int("workflow_action_id", self.workflow_action_id)
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_positive_int("attempt_number", self.attempt_number)
        ensure_non_empty_text("adapter_code", self.adapter_code)
        ensure_non_empty_text("started_at", self.started_at)
        ensure_allowed_value("status", self.status, EXECUTION_ATTEMPT_STATUS_CODES)
        ensure_bool("retry_eligible", self.retry_eligible)
        ensure_json_compatible("response_snapshot", self.response_snapshot)
        ensure_optional_non_empty_text("completed_at", self.completed_at)
        ensure_optional_non_empty_text("external_reference", self.external_reference)
        ensure_optional_non_empty_text("failure_code", self.failure_code)
        if self.status != EXECUTION_ATTEMPT_STATUS_STARTED and self.completed_at is None:
            raise Phase8ContractError(
                error_category="missing_value",
                safe_message="terminal ExecutionAttempt records require completed_at.",
            )


@dataclass(frozen=True)
class FollowUp:
    follow_up_id: int
    rental_case_id: int
    reason_code: str
    due_at: str
    urgency_level: str
    attempt_count: int
    status: str
    semantic_identity_key: str | None = None
    sequence_number: int = 1
    waiting_for_role: str | None = None
    waiting_for_reference: str | None = None
    cadence_policy_code: str | None = None
    escalate_after: int | None = None
    next_action_type: str | None = None
    context_payload: dict[str, Any] = field(default_factory=dict)
    created_at: str | None = None
    updated_at: str | None = None
    completed_at: str | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("follow_up_id", self.follow_up_id)
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_non_empty_text("reason_code", self.reason_code)
        ensure_non_empty_text("due_at", self.due_at)
        ensure_allowed_value("urgency_level", self.urgency_level, FOLLOW_UP_URGENCY_CODES)
        ensure_non_negative_int("attempt_count", self.attempt_count)
        ensure_allowed_value("status", self.status, FOLLOW_UP_STATUS_CODES)
        ensure_optional_non_empty_text("semantic_identity_key", self.semantic_identity_key)
        ensure_positive_int("sequence_number", self.sequence_number)
        ensure_optional_non_empty_text("waiting_for_role", self.waiting_for_role)
        ensure_optional_non_empty_text("waiting_for_reference", self.waiting_for_reference)
        ensure_optional_non_empty_text("cadence_policy_code", self.cadence_policy_code)
        ensure_optional_positive_int("escalate_after", self.escalate_after)
        if self.next_action_type is not None:
            ensure_allowed_value("next_action_type", self.next_action_type, WORKFLOW_ACTION_TYPES)
        ensure_json_compatible("context_payload", self.context_payload)
        ensure_optional_non_empty_text("created_at", self.created_at)
        ensure_optional_non_empty_text("updated_at", self.updated_at)
        ensure_optional_non_empty_text("completed_at", self.completed_at)


@dataclass(frozen=True)
class Milestone:
    milestone_id: int
    rental_case_id: int
    milestone_type: str
    target_at: str
    status: str
    related_requirement_id: int | None = None
    related_workflow_action_id: int | None = None
    basis_reference: str | None = None
    supersedes_milestone_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None
    completed_at: str | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("milestone_id", self.milestone_id)
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_non_empty_text("milestone_type", self.milestone_type)
        ensure_non_empty_text("target_at", self.target_at)
        ensure_allowed_value("status", self.status, MILESTONE_STATUS_CODES)
        ensure_optional_positive_int("related_requirement_id", self.related_requirement_id)
        ensure_optional_positive_int("related_workflow_action_id", self.related_workflow_action_id)
        ensure_optional_non_empty_text("basis_reference", self.basis_reference)
        ensure_optional_positive_int("supersedes_milestone_id", self.supersedes_milestone_id)
        ensure_optional_non_empty_text("created_at", self.created_at)
        ensure_optional_non_empty_text("updated_at", self.updated_at)
        ensure_optional_non_empty_text("completed_at", self.completed_at)
        if self.status in {MILESTONE_STATUS_COMPLETED, MILESTONE_STATUS_MISSED, MILESTONE_STATUS_SUPERSEDED} and self.completed_at is None:
            raise Phase8ContractError(
                error_category="missing_value",
                safe_message="completed, missed, and superseded Milestone records require completed_at.",
            )


@dataclass(frozen=True)
class ArtifactReference:
    artifact_reference_id: int
    rental_case_id: int
    artifact_type: str
    derived_from_case_revision: int
    freshness_status: str
    storage_reference: str | None = None
    external_reference: str | None = None
    relevant_scope_fingerprint: str | None = None
    last_generated_at: str | None = None
    last_synced_at: str | None = None
    supersedes_artifact_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("artifact_reference_id", self.artifact_reference_id)
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_allowed_value("artifact_type", self.artifact_type, ARTIFACT_TYPE_CODES)
        ensure_non_negative_int("derived_from_case_revision", self.derived_from_case_revision)
        ensure_allowed_value("freshness_status", self.freshness_status, ARTIFACT_FRESHNESS_CODES)
        ensure_optional_non_empty_text("storage_reference", self.storage_reference)
        ensure_optional_non_empty_text("external_reference", self.external_reference)
        ensure_optional_non_empty_text("relevant_scope_fingerprint", self.relevant_scope_fingerprint)
        ensure_optional_non_empty_text("last_generated_at", self.last_generated_at)
        ensure_optional_non_empty_text("last_synced_at", self.last_synced_at)
        ensure_optional_positive_int("supersedes_artifact_id", self.supersedes_artifact_id)
        ensure_optional_non_empty_text("created_at", self.created_at)
        ensure_optional_non_empty_text("updated_at", self.updated_at)


@dataclass(frozen=True)
class WorkflowReasoningProjection:
    reasoning_projection_id: int
    rental_case_id: int
    reasoning_purpose: str
    phase_7_context_contract_version: int
    phase_8_workflow_contract_version: int
    source_case_revision: int
    authority_outcome_classification: str
    degraded_retrieval_summary: dict[str, Any]
    created_at: str
    projection_identity_key: str | None = None
    reasoning_state_code: str | None = None
    workflow_posture: str | None = None
    effective_confidentiality_level: str | None = None
    de_identification_required: bool = False
    personal_information_present: bool = False
    materially_affects_completeness: bool = False
    relevant_current_truth_item_ids: tuple[str, ...] = ()
    relevant_guidance_item_ids: tuple[str, ...] = ()
    relevant_historical_item_ids: tuple[str, ...] = ()
    conflict_codes: tuple[str, ...] = ()
    contamination_codes: tuple[str, ...] = ()
    unresolved_authority_codes: tuple[str, ...] = ()
    warning_codes: tuple[str, ...] = ()
    grounding_reference_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ensure_positive_int("reasoning_projection_id", self.reasoning_projection_id)
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_non_empty_text("reasoning_purpose", self.reasoning_purpose)
        ensure_positive_int("phase_7_context_contract_version", self.phase_7_context_contract_version)
        ensure_positive_int("phase_8_workflow_contract_version", self.phase_8_workflow_contract_version)
        ensure_non_negative_int("source_case_revision", self.source_case_revision)
        ensure_allowed_value("authority_outcome_classification", self.authority_outcome_classification, AUTHORITY_OUTCOME_CODES)
        ensure_json_compatible("degraded_retrieval_summary", self.degraded_retrieval_summary)
        ensure_non_empty_text("created_at", self.created_at)
        ensure_optional_non_empty_text("projection_identity_key", self.projection_identity_key)
        if self.reasoning_state_code is not None:
            ensure_allowed_value("reasoning_state_code", self.reasoning_state_code, PHASE_7_REASONING_STATE_CODES)
        if self.workflow_posture is not None:
            ensure_allowed_value("workflow_posture", self.workflow_posture, WORKFLOW_REASONING_POSTURE_CODES)
        if self.effective_confidentiality_level is not None:
            ensure_allowed_value(
                "effective_confidentiality_level",
                self.effective_confidentiality_level,
                WORKFLOW_CONFIDENTIALITY_LEVEL_CODES,
            )
        ensure_bool("de_identification_required", self.de_identification_required)
        ensure_bool("personal_information_present", self.personal_information_present)
        ensure_bool("materially_affects_completeness", self.materially_affects_completeness)
        ensure_tuple_of_non_empty_text("relevant_current_truth_item_ids", self.relevant_current_truth_item_ids)
        ensure_tuple_of_non_empty_text("relevant_guidance_item_ids", self.relevant_guidance_item_ids)
        ensure_tuple_of_non_empty_text("relevant_historical_item_ids", self.relevant_historical_item_ids)
        ensure_tuple_of_non_empty_text("unresolved_authority_codes", self.unresolved_authority_codes)
        ensure_tuple_of_non_empty_text("warning_codes", self.warning_codes)
        ensure_tuple_of_non_empty_text("grounding_reference_keys", self.grounding_reference_keys)
        for code in self.conflict_codes:
            ensure_allowed_value("conflict_codes", code, CONFLICT_TYPE_CODES)
        for code in self.contamination_codes:
            ensure_allowed_value("contamination_codes", code, CONTAMINATION_CODE_CODES)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)
