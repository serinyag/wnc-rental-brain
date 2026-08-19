from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from .contracts import LIFECYCLE_STATES, PHASE_8_WORKFLOW_CONTRACT_VERSION
from .validation import (
    Phase8ContractError,
    ensure_allowed_value,
    ensure_bool,
    ensure_json_compatible,
    ensure_non_empty_text,
    ensure_non_negative_int,
    ensure_optional_non_empty_text,
    ensure_optional_non_negative_int,
    ensure_optional_positive_int,
    ensure_positive_int,
    ensure_tuple_of_non_empty_text,
)


LIFECYCLE_FAILURE_CASE_NOT_FOUND = "case_not_found"
LIFECYCLE_FAILURE_INVALID_TARGET_STATE = "invalid_target_state"
LIFECYCLE_FAILURE_TRANSITION_NOT_ALLOWED = "transition_not_allowed"
LIFECYCLE_FAILURE_GUARD_FAILED = "guard_failed"
LIFECYCLE_FAILURE_OPEN_BLOCKER = "open_blocker"
LIFECYCLE_FAILURE_UNSATISFIED_REQUIREMENT = "unsatisfied_requirement"
LIFECYCLE_FAILURE_OPEN_QUESTION_BLOCKS_TRANSITION = "open_question_blocks_transition"
LIFECYCLE_FAILURE_APPROVAL_UNRESOLVED = "approval_unresolved"
LIFECYCLE_FAILURE_MATERIAL_CHANGE_UNRESOLVED = "material_change_unresolved"
LIFECYCLE_FAILURE_MISSING_TRANSITION_EVIDENCE = "missing_transition_evidence"
LIFECYCLE_FAILURE_STALE_CASE_REVISION = "stale_case_revision"
LIFECYCLE_FAILURE_TERMINAL_STATE = "terminal_state"
LIFECYCLE_FAILURE_INVALID_RESUME_TARGET = "invalid_resume_target"
LIFECYCLE_FAILURE_MANUAL_OVERRIDE_REQUIRED = "manual_override_required"
LIFECYCLE_FAILURE_TRANSITION_COMMIT_FAILED = "transition_commit_failed"
LIFECYCLE_FAILURE_CONFLICTING_ACTIVE_CASE_DECISION = "conflicting_active_case_decision"
LIFECYCLE_FAILURE_MISSING_DORMANT_METADATA = "missing_dormant_metadata"
LIFECYCLE_FAILURE_MISSING_PROPOSAL_ARTIFACT = "missing_proposal_artifact"
LIFECYCLE_FAILURE_PROPOSAL_NOT_READY = "proposal_not_ready"
LIFECYCLE_FAILURE_CLIENT_INTENT_MISSING = "client_intent_missing"
LIFECYCLE_FAILURE_READINESS_FAILED = "readiness_failed"
LIFECYCLE_FAILURE_EVENT_START_EVIDENCE_MISSING = "event_start_evidence_missing"
LIFECYCLE_FAILURE_EVENT_COMPLETION_EVIDENCE_MISSING = "event_completion_evidence_missing"
LIFECYCLE_FAILURE_CLOSE_OUT_INCOMPLETE = "close_out_incomplete"

LIFECYCLE_FAILURE_CODES = frozenset(
    {
        LIFECYCLE_FAILURE_CASE_NOT_FOUND,
        LIFECYCLE_FAILURE_INVALID_TARGET_STATE,
        LIFECYCLE_FAILURE_TRANSITION_NOT_ALLOWED,
        LIFECYCLE_FAILURE_GUARD_FAILED,
        LIFECYCLE_FAILURE_OPEN_BLOCKER,
        LIFECYCLE_FAILURE_UNSATISFIED_REQUIREMENT,
        LIFECYCLE_FAILURE_OPEN_QUESTION_BLOCKS_TRANSITION,
        LIFECYCLE_FAILURE_APPROVAL_UNRESOLVED,
        LIFECYCLE_FAILURE_MATERIAL_CHANGE_UNRESOLVED,
        LIFECYCLE_FAILURE_MISSING_TRANSITION_EVIDENCE,
        LIFECYCLE_FAILURE_STALE_CASE_REVISION,
        LIFECYCLE_FAILURE_TERMINAL_STATE,
        LIFECYCLE_FAILURE_INVALID_RESUME_TARGET,
        LIFECYCLE_FAILURE_MANUAL_OVERRIDE_REQUIRED,
        LIFECYCLE_FAILURE_TRANSITION_COMMIT_FAILED,
        LIFECYCLE_FAILURE_CONFLICTING_ACTIVE_CASE_DECISION,
        LIFECYCLE_FAILURE_MISSING_DORMANT_METADATA,
        LIFECYCLE_FAILURE_MISSING_PROPOSAL_ARTIFACT,
        LIFECYCLE_FAILURE_PROPOSAL_NOT_READY,
        LIFECYCLE_FAILURE_CLIENT_INTENT_MISSING,
        LIFECYCLE_FAILURE_READINESS_FAILED,
        LIFECYCLE_FAILURE_EVENT_START_EVIDENCE_MISSING,
        LIFECYCLE_FAILURE_EVENT_COMPLETION_EVIDENCE_MISSING,
        LIFECYCLE_FAILURE_CLOSE_OUT_INCOMPLETE,
    }
)


@dataclass(frozen=True)
class LifecycleFailureCode:
    value: str

    def __post_init__(self) -> None:
        ensure_allowed_value("value", self.value, LIFECYCLE_FAILURE_CODES)


@dataclass(frozen=True)
class GuardResult:
    guard_code: str
    passed: bool
    reason_code: str | None = None
    relevant_case_revision: int | None = None
    blocking_blocker_ids: tuple[int, ...] = ()
    blocking_requirement_ids: tuple[int, ...] = ()
    blocking_open_question_ids: tuple[int, ...] = ()
    blocking_approval_request_ids: tuple[int, ...] = ()
    blocking_proposed_change_ids: tuple[int, ...] = ()
    evidence_event_ids: tuple[int, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ensure_non_empty_text("guard_code", self.guard_code)
        ensure_bool("passed", self.passed)
        if self.reason_code is not None:
            ensure_allowed_value("reason_code", self.reason_code, LIFECYCLE_FAILURE_CODES)
        ensure_optional_non_negative_int("relevant_case_revision", self.relevant_case_revision)
        for field_name, values in (
            ("blocking_blocker_ids", self.blocking_blocker_ids),
            ("blocking_requirement_ids", self.blocking_requirement_ids),
            ("blocking_open_question_ids", self.blocking_open_question_ids),
            ("blocking_approval_request_ids", self.blocking_approval_request_ids),
            ("blocking_proposed_change_ids", self.blocking_proposed_change_ids),
            ("evidence_event_ids", self.evidence_event_ids),
        ):
            if not isinstance(values, tuple):
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"{field_name} must be a tuple of positive integers.",
                )
            for index, value in enumerate(values):
                ensure_positive_int(f"{field_name}[{index}]", value)
        ensure_json_compatible("metadata", self.metadata)


@dataclass(frozen=True)
class TransitionEvaluation:
    rental_case_id: int
    requested_target_state: str
    edge_allowed: bool
    guard_passed: bool
    allowed: bool
    manual_override_required: bool
    contract_version: int = PHASE_8_WORKFLOW_CONTRACT_VERSION
    current_state: str | None = None
    evaluated_case_revision: int | None = None
    reason_codes: tuple[str, ...] = ()
    guard_results: tuple[GuardResult, ...] = ()
    blocking_blocker_ids: tuple[int, ...] = ()
    blocking_requirement_ids: tuple[int, ...] = ()
    blocking_open_question_ids: tuple[int, ...] = ()
    blocking_approval_request_ids: tuple[int, ...] = ()
    blocking_proposed_change_ids: tuple[int, ...] = ()
    evidence_event_ids: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_non_empty_text("requested_target_state", self.requested_target_state)
        ensure_bool("edge_allowed", self.edge_allowed)
        ensure_bool("guard_passed", self.guard_passed)
        ensure_bool("allowed", self.allowed)
        ensure_bool("manual_override_required", self.manual_override_required)
        ensure_positive_int("contract_version", self.contract_version)
        if self.current_state is not None:
            ensure_allowed_value("current_state", self.current_state, LIFECYCLE_STATES)
        if self.evaluated_case_revision is not None:
            ensure_non_negative_int("evaluated_case_revision", self.evaluated_case_revision)
        ensure_tuple_of_non_empty_text("reason_codes", self.reason_codes)
        if not isinstance(self.guard_results, tuple):
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="guard_results must be a tuple of GuardResult values.",
            )
        for index, result in enumerate(self.guard_results):
            if not isinstance(result, GuardResult):
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"guard_results[{index}] must be a GuardResult.",
                )
        for code in self.reason_codes:
            ensure_allowed_value("reason_codes", code, LIFECYCLE_FAILURE_CODES)
        for field_name, values in (
            ("blocking_blocker_ids", self.blocking_blocker_ids),
            ("blocking_requirement_ids", self.blocking_requirement_ids),
            ("blocking_open_question_ids", self.blocking_open_question_ids),
            ("blocking_approval_request_ids", self.blocking_approval_request_ids),
            ("blocking_proposed_change_ids", self.blocking_proposed_change_ids),
            ("evidence_event_ids", self.evidence_event_ids),
        ):
            if not isinstance(values, tuple):
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"{field_name} must be a tuple of positive integers.",
                )
            for index, value in enumerate(values):
                ensure_positive_int(f"{field_name}[{index}]", value)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


@dataclass(frozen=True)
class LifecycleTransitionResult:
    rental_case_id: int
    previous_state: str
    new_state: str
    previous_revision: int
    new_revision: int
    lifecycle_transition_history_id: int
    workflow_event_id: int
    reason_code: str
    actor_reference: str
    source_type: str
    manual_override: bool
    occurred_at: str
    actor_type: str | None = None
    source_reference: str | None = None
    triggering_event_id: int | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_allowed_value("previous_state", self.previous_state, LIFECYCLE_STATES)
        ensure_allowed_value("new_state", self.new_state, LIFECYCLE_STATES)
        ensure_non_negative_int("previous_revision", self.previous_revision)
        ensure_positive_int("new_revision", self.new_revision)
        if self.new_revision != self.previous_revision + 1:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="new_revision must equal previous_revision + 1.",
            )
        ensure_positive_int("lifecycle_transition_history_id", self.lifecycle_transition_history_id)
        ensure_positive_int("workflow_event_id", self.workflow_event_id)
        ensure_non_empty_text("reason_code", self.reason_code)
        ensure_non_empty_text("actor_reference", self.actor_reference)
        ensure_non_empty_text("source_type", self.source_type)
        ensure_bool("manual_override", self.manual_override)
        ensure_non_empty_text("occurred_at", self.occurred_at)
        ensure_optional_non_empty_text("actor_type", self.actor_type)
        ensure_optional_non_empty_text("source_reference", self.source_reference)
        ensure_optional_positive_int("triggering_event_id", self.triggering_event_id)


@dataclass(frozen=True)
class ManualTransitionOverrideRequest:
    rental_case_id: int
    target_state: str
    expected_case_revision: int
    actor_reference: str
    reason_code: str
    audit_note: str
    override_indicator: bool = True
    actor_type: str | None = None
    source_type: str = "manual_override"
    source_reference: str | None = None
    triggering_event_id: int | None = None
    transition_context: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_allowed_value("target_state", self.target_state, LIFECYCLE_STATES)
        ensure_non_negative_int("expected_case_revision", self.expected_case_revision)
        ensure_non_empty_text("actor_reference", self.actor_reference)
        ensure_non_empty_text("reason_code", self.reason_code)
        ensure_non_empty_text("audit_note", self.audit_note)
        ensure_bool("override_indicator", self.override_indicator)
        if not self.override_indicator:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="ManualTransitionOverrideRequest.override_indicator must be true.",
            )
        ensure_optional_non_empty_text("actor_type", self.actor_type)
        ensure_non_empty_text("source_type", self.source_type)
        ensure_optional_non_empty_text("source_reference", self.source_reference)
        ensure_optional_positive_int("triggering_event_id", self.triggering_event_id)
        ensure_json_compatible("transition_context", self.transition_context)


@dataclass(frozen=True)
class LifecycleCaseEvaluation:
    rental_case_id: int
    case_found: bool
    contract_version: int = PHASE_8_WORKFLOW_CONTRACT_VERSION
    current_state: str | None = None
    current_case_revision: int | None = None
    normal_outgoing_transitions: tuple[str, ...] = ()
    eligible_transitions: tuple[str, ...] = ()
    blocked_transitions: tuple[str, ...] = ()
    transition_evaluations: tuple[TransitionEvaluation, ...] = ()
    reason_codes: tuple[str, ...] = ()
    blocker_ids: tuple[int, ...] = ()
    requirement_ids: tuple[int, ...] = ()
    approval_request_ids: tuple[int, ...] = ()
    dormant_resume_target: str | None = None
    terminal_state: bool = False
    readiness_passed: bool | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_bool("case_found", self.case_found)
        ensure_positive_int("contract_version", self.contract_version)
        if self.current_state is not None:
            ensure_allowed_value("current_state", self.current_state, LIFECYCLE_STATES)
        if self.current_case_revision is not None:
            ensure_non_negative_int("current_case_revision", self.current_case_revision)
        ensure_tuple_of_non_empty_text("normal_outgoing_transitions", self.normal_outgoing_transitions)
        ensure_tuple_of_non_empty_text("eligible_transitions", self.eligible_transitions)
        ensure_tuple_of_non_empty_text("blocked_transitions", self.blocked_transitions)
        ensure_tuple_of_non_empty_text("reason_codes", self.reason_codes)
        for field_name, values in (
            ("blocker_ids", self.blocker_ids),
            ("requirement_ids", self.requirement_ids),
            ("approval_request_ids", self.approval_request_ids),
        ):
            if not isinstance(values, tuple):
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"{field_name} must be a tuple of positive integers.",
                )
            for index, value in enumerate(values):
                ensure_positive_int(f"{field_name}[{index}]", value)
        for state_set_name, values in (
            ("normal_outgoing_transitions", self.normal_outgoing_transitions),
            ("eligible_transitions", self.eligible_transitions),
            ("blocked_transitions", self.blocked_transitions),
        ):
            for value in values:
                ensure_allowed_value(state_set_name, value, LIFECYCLE_STATES)
        for code in self.reason_codes:
            ensure_allowed_value("reason_codes", code, LIFECYCLE_FAILURE_CODES)
        if self.dormant_resume_target is not None:
            ensure_allowed_value("dormant_resume_target", self.dormant_resume_target, LIFECYCLE_STATES)
        ensure_bool("terminal_state", self.terminal_state)
        if self.readiness_passed is not None:
            ensure_bool("readiness_passed", self.readiness_passed)
        if not isinstance(self.transition_evaluations, tuple):
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="transition_evaluations must be a tuple of TransitionEvaluation values.",
            )
        for index, evaluation in enumerate(self.transition_evaluations):
            if not isinstance(evaluation, TransitionEvaluation):
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"transition_evaluations[{index}] must be a TransitionEvaluation.",
                )


@dataclass(frozen=True)
class ReadinessReevaluation:
    rental_case_id: int
    case_found: bool
    current_state: str | None
    evaluated_case_revision: int | None
    readiness_passed: bool
    degradation_allowed: bool
    contract_version: int = PHASE_8_WORKFLOW_CONTRACT_VERSION
    degradation_target_state: str | None = None
    reason_codes: tuple[str, ...] = ()
    blocker_ids: tuple[int, ...] = ()
    requirement_ids: tuple[int, ...] = ()
    approval_request_ids: tuple[int, ...] = ()
    evidence_event_ids: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_bool("case_found", self.case_found)
        if self.current_state is not None:
            ensure_allowed_value("current_state", self.current_state, LIFECYCLE_STATES)
        if self.evaluated_case_revision is not None:
            ensure_non_negative_int("evaluated_case_revision", self.evaluated_case_revision)
        ensure_bool("readiness_passed", self.readiness_passed)
        ensure_bool("degradation_allowed", self.degradation_allowed)
        ensure_positive_int("contract_version", self.contract_version)
        if self.degradation_target_state is not None:
            ensure_allowed_value("degradation_target_state", self.degradation_target_state, LIFECYCLE_STATES)
        ensure_tuple_of_non_empty_text("reason_codes", self.reason_codes)
        for code in self.reason_codes:
            ensure_allowed_value("reason_codes", code, LIFECYCLE_FAILURE_CODES)
        for field_name, values in (
            ("blocker_ids", self.blocker_ids),
            ("requirement_ids", self.requirement_ids),
            ("approval_request_ids", self.approval_request_ids),
            ("evidence_event_ids", self.evidence_event_ids),
        ):
            if not isinstance(values, tuple):
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"{field_name} must be a tuple of positive integers.",
                )
            for index, value in enumerate(values):
                ensure_positive_int(f"{field_name}[{index}]", value)


@dataclass(frozen=True)
class LifecycleHistoryValidationResult:
    rental_case_id: int
    valid: bool
    final_state_matches: bool
    final_revision_matches: bool
    illegal_edge_detected: bool
    revision_gap_detected: bool
    chain_break_detected: bool
    contract_version: int = PHASE_8_WORKFLOW_CONTRACT_VERSION
    reason_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_bool("valid", self.valid)
        ensure_bool("final_state_matches", self.final_state_matches)
        ensure_bool("final_revision_matches", self.final_revision_matches)
        ensure_bool("illegal_edge_detected", self.illegal_edge_detected)
        ensure_bool("revision_gap_detected", self.revision_gap_detected)
        ensure_bool("chain_break_detected", self.chain_break_detected)
        ensure_positive_int("contract_version", self.contract_version)
        ensure_tuple_of_non_empty_text("reason_codes", self.reason_codes)
        for code in self.reason_codes:
            ensure_allowed_value("reason_codes", code, LIFECYCLE_FAILURE_CODES)
