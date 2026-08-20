from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Callable, Protocol

from .contracts import (
    BLOCKING_SCOPE_TRANSITION,
    OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION,
    OPEN_QUESTION_STATUS_OPEN,
    OPEN_QUESTION_STATUS_RESOLVED,
    PROPOSED_CHANGE_STATUS_PROPOSED,
    PROPOSED_CHANGE_STATUS_UNDER_REVIEW,
    RESCHEDULE_STATUS_AWAITING_CLIENT_CONFIRMATION,
    RESCHEDULE_STATUS_EVALUATING,
    RESCHEDULE_STATUS_OFFERED,
    RESCHEDULE_STATUS_PROPOSED,
)
from .observation_contracts import InboundObservation, InboundObservationEffect
from .validation import (
    Phase8ContractError,
    ensure_json_compatible,
    ensure_non_empty_text,
    ensure_non_negative_int,
    ensure_optional_non_empty_text,
    ensure_optional_positive_int,
    ensure_positive_int,
    ensure_tuple_of_non_empty_text,
)

if TYPE_CHECKING:
    from .observation_repository import ObservationCaseSnapshot


INQUIRY_INTAKE_FAILURE_CASE_NOT_FOUND = "case_not_found"
INQUIRY_INTAKE_FAILURE_STALE_CASE_REVISION = "stale_case_revision"

INQUIRY_INTAKE_EFFECT_PROMOTE_CURRENT_VALUE = "promote_current_value"
INQUIRY_INTAKE_EFFECT_CREATE_OPEN_QUESTION = "create_open_question"
INQUIRY_INTAKE_EFFECT_RESOLVE_OPEN_QUESTION = "resolve_open_question"
INQUIRY_INTAKE_EFFECT_CREATE_PROPOSED_CHANGE = "create_proposed_change"
INQUIRY_INTAKE_EFFECT_CREATE_RESCHEDULE_REQUEST = "create_reschedule_request"
INQUIRY_INTAKE_EFFECT_NO_CHANGE = "no_change"

INQUIRY_INTAKE_OUTCOME_PROMOTED = "promoted"
INQUIRY_INTAKE_OUTCOME_OPEN_QUESTION_CREATED = "open_question_created"
INQUIRY_INTAKE_OUTCOME_OPEN_QUESTION_PRESERVED = "open_question_preserved"
INQUIRY_INTAKE_OUTCOME_OPEN_QUESTION_RESOLVED = "open_question_resolved"
INQUIRY_INTAKE_OUTCOME_PROPOSED_CHANGE = "proposed_change_created"
INQUIRY_INTAKE_OUTCOME_RESCHEDULE_REQUEST = "reschedule_request_created"
INQUIRY_INTAKE_OUTCOME_CONFLICT = "conflict_requires_clarification"
INQUIRY_INTAKE_OUTCOME_NO_CHANGE = "no_change"

INQUIRY_FIELD_REQUESTED_SCHEDULE = "requested_schedule"
INQUIRY_FIELD_GUEST_COUNT = "guest_count"
INQUIRY_FIELD_REQUESTED_SPACE = "requested_space"
INQUIRY_FIELD_EVENT_TYPE = "event_type"

SPECIFIC_RENTAL_SCOPE_CODES = frozenset({"studio_space", "entire_venue"})
ACTIVE_CHANGE_STATUSES = frozenset({PROPOSED_CHANGE_STATUS_PROPOSED, PROPOSED_CHANGE_STATUS_UNDER_REVIEW})
ACTIVE_RESCHEDULE_STATUSES = frozenset(
    {
        RESCHEDULE_STATUS_PROPOSED,
        RESCHEDULE_STATUS_EVALUATING,
        RESCHEDULE_STATUS_OFFERED,
        RESCHEDULE_STATUS_AWAITING_CLIENT_CONFIRMATION,
    }
)


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class InquiryFieldRule:
    inquiry_field_code: str
    observation_field_code: str
    domain_code: str
    question_type: str
    human_question_text: str
    change_kind: str
    blocking_scope: str = BLOCKING_SCOPE_TRANSITION


CORE_INQUIRY_FIELD_RULES = {
    INQUIRY_FIELD_REQUESTED_SCHEDULE: InquiryFieldRule(
        inquiry_field_code=INQUIRY_FIELD_REQUESTED_SCHEDULE,
        observation_field_code="active_event_window",
        domain_code="timing",
        question_type="requested_event_timing",
        human_question_text="What date and time is the client requesting for the event?",
        change_kind="active_event_window",
    ),
    INQUIRY_FIELD_GUEST_COUNT: InquiryFieldRule(
        inquiry_field_code=INQUIRY_FIELD_GUEST_COUNT,
        observation_field_code="guest_count",
        domain_code="event_profile",
        question_type="expected_guest_count",
        human_question_text="How many guests are expected?",
        change_kind="guest_count",
    ),
    INQUIRY_FIELD_REQUESTED_SPACE: InquiryFieldRule(
        inquiry_field_code=INQUIRY_FIELD_REQUESTED_SPACE,
        observation_field_code="requested_rental_scope",
        domain_code="event_profile",
        question_type="requested_rental_scope",
        human_question_text="Which space or rental scope is the client requesting?",
        change_kind="requested_rental_scope",
    ),
    INQUIRY_FIELD_EVENT_TYPE: InquiryFieldRule(
        inquiry_field_code=INQUIRY_FIELD_EVENT_TYPE,
        observation_field_code="event_type",
        domain_code="event_profile",
        question_type="requested_event_type",
        human_question_text="What type of event is the client planning?",
        change_kind="event_type",
    ),
}


@dataclass(frozen=True)
class InquiryIntakeFieldEvaluation:
    inquiry_field_code: str
    outcome_code: str
    reason_code: str
    source_observation_ids: tuple[int, ...] = ()
    current_value: Any = None
    selected_value: Any = None
    linked_open_question_id: int | None = None

    def __post_init__(self) -> None:
        ensure_non_empty_text("inquiry_field_code", self.inquiry_field_code)
        ensure_non_empty_text("outcome_code", self.outcome_code)
        ensure_non_empty_text("reason_code", self.reason_code)
        ensure_tuple_of_non_empty_text(
            "source_observation_ids",
            tuple(str(observation_id) for observation_id in self.source_observation_ids),
        )
        ensure_json_compatible("current_value", self.current_value)
        ensure_json_compatible("selected_value", self.selected_value)
        ensure_optional_positive_int("linked_open_question_id", self.linked_open_question_id)


@dataclass(frozen=True)
class InquiryIntakePlannedEffect:
    effect_code: str
    inquiry_field_code: str
    domain_code: str
    expected_case_revision: int
    idempotency_key: str
    reason_code: str
    source_observation_ids: tuple[int, ...] = ()
    source_observation_references: tuple[str, ...] = ()
    current_value: Any = None
    proposed_value: Any = None
    open_question_id: int | None = None
    open_question_type: str | None = None
    human_question_text: str | None = None
    blocking_scope: str | None = None

    def __post_init__(self) -> None:
        ensure_non_empty_text("effect_code", self.effect_code)
        ensure_non_empty_text("inquiry_field_code", self.inquiry_field_code)
        ensure_non_empty_text("domain_code", self.domain_code)
        ensure_non_negative_int("expected_case_revision", self.expected_case_revision)
        ensure_non_empty_text("idempotency_key", self.idempotency_key)
        ensure_non_empty_text("reason_code", self.reason_code)
        ensure_tuple_of_non_empty_text(
            "source_observation_ids",
            tuple(str(observation_id) for observation_id in self.source_observation_ids),
        )
        ensure_tuple_of_non_empty_text("source_observation_references", self.source_observation_references)
        ensure_json_compatible("current_value", self.current_value)
        ensure_json_compatible("proposed_value", self.proposed_value)
        ensure_optional_positive_int("open_question_id", self.open_question_id)
        ensure_optional_non_empty_text("open_question_type", self.open_question_type)
        ensure_optional_non_empty_text("human_question_text", self.human_question_text)
        ensure_optional_non_empty_text("blocking_scope", self.blocking_scope)


@dataclass(frozen=True)
class InquiryIntakePlan:
    rental_case_id: int
    evaluated_case_revision: int
    eligible_observation_ids: tuple[int, ...]
    field_evaluations: tuple[InquiryIntakeFieldEvaluation, ...]
    effects: tuple[InquiryIntakePlannedEffect, ...]

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_non_negative_int("evaluated_case_revision", self.evaluated_case_revision)
        ensure_tuple_of_non_empty_text(
            "eligible_observation_ids",
            tuple(str(observation_id) for observation_id in self.eligible_observation_ids),
        )

    @property
    def has_effects(self) -> bool:
        return bool(self.effects)


@dataclass(frozen=True)
class InquiryIntakeCommitResult:
    rental_case_id: int
    case_revision_before: int
    case_revision_after: int
    plan: InquiryIntakePlan
    applied_effects: tuple[InquiryIntakePlannedEffect, ...]
    created_open_question_ids: tuple[int, ...] = ()
    resolved_open_question_ids: tuple[int, ...] = ()
    created_proposed_change_ids: tuple[int, ...] = ()
    created_reschedule_request_ids: tuple[int, ...] = ()
    failure_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_non_negative_int("case_revision_before", self.case_revision_before)
        ensure_non_negative_int("case_revision_after", self.case_revision_after)
        ensure_tuple_of_non_empty_text("failure_codes", self.failure_codes)


class InquiryIntakeRepositoryProtocol(Protocol):
    def load_case_snapshot(self, rental_case_id: int) -> ObservationCaseSnapshot | None: ...

    def list_observations_for_case(self, rental_case_id: int) -> tuple[InboundObservation, ...]: ...

    def list_effects_for_case(self, rental_case_id: int) -> tuple[InboundObservationEffect, ...]: ...

    def commit_inquiry_intake_plan(
        self,
        plan: InquiryIntakePlan,
        *,
        actor_reference: str,
        actor_type: str | None,
        applied_at: str,
    ) -> InquiryIntakeCommitResult: ...


@dataclass(frozen=True)
class _NormalizedObservation:
    inbound_observation_id: int
    source_evidence_reference: str
    created_at: str
    value: Any


def apply_inquiry_intake(
    repository: InquiryIntakeRepositoryProtocol,
    *,
    rental_case_id: int,
    expected_revision: int | None = None,
    actor_reference: str,
    actor_type: str | None,
    now: Callable[[], str] = current_timestamp,
) -> InquiryIntakeCommitResult:
    snapshot = repository.load_case_snapshot(rental_case_id)
    if snapshot is None:
        return InquiryIntakeCommitResult(
            rental_case_id=rental_case_id,
            case_revision_before=0,
            case_revision_after=0,
            plan=InquiryIntakePlan(
                rental_case_id=rental_case_id,
                evaluated_case_revision=0,
                eligible_observation_ids=(),
                field_evaluations=(),
                effects=(),
            ),
            applied_effects=(),
            failure_codes=(INQUIRY_INTAKE_FAILURE_CASE_NOT_FOUND,),
        )
    if expected_revision is not None and snapshot.rental_case.case_revision != expected_revision:
        return InquiryIntakeCommitResult(
            rental_case_id=rental_case_id,
            case_revision_before=snapshot.rental_case.case_revision,
            case_revision_after=snapshot.rental_case.case_revision,
            plan=InquiryIntakePlan(
                rental_case_id=rental_case_id,
                evaluated_case_revision=snapshot.rental_case.case_revision,
                eligible_observation_ids=(),
                field_evaluations=(),
                effects=(),
            ),
            applied_effects=(),
            failure_codes=(INQUIRY_INTAKE_FAILURE_STALE_CASE_REVISION,),
        )
    observations = repository.list_observations_for_case(rental_case_id)
    effects = repository.list_effects_for_case(rental_case_id)
    plan = evaluate_inquiry_intake(
        snapshot=snapshot,
        observations=observations,
        effects=effects,
        expected_revision=expected_revision,
    )
    if not plan.has_effects:
        return InquiryIntakeCommitResult(
            rental_case_id=rental_case_id,
            case_revision_before=snapshot.rental_case.case_revision,
            case_revision_after=snapshot.rental_case.case_revision,
            plan=plan,
            applied_effects=(),
        )
    return repository.commit_inquiry_intake_plan(
        plan,
        actor_reference=actor_reference,
        actor_type=actor_type,
        applied_at=now(),
    )


def evaluate_inquiry_intake(
    *,
    snapshot: ObservationCaseSnapshot,
    observations: tuple[InboundObservation, ...],
    effects: tuple[InboundObservationEffect, ...],
    expected_revision: int | None = None,
) -> InquiryIntakePlan:
    if expected_revision is not None and snapshot.rental_case.case_revision != expected_revision:
        raise Phase8ContractError(
            error_category="invalid_value",
            safe_message="expected_revision must match the current case revision during evaluation.",
        )

    effect_by_observation_id = {effect.inbound_observation_id: effect for effect in effects}
    eligible = tuple(
        observation
        for observation in observations
        if _is_eligible_observation(observation, effect_by_observation_id.get(observation.inbound_observation_id))
    )
    field_evaluations: list[InquiryIntakeFieldEvaluation] = []
    planned_effects: list[InquiryIntakePlannedEffect] = []

    for inquiry_field_code, rule in CORE_INQUIRY_FIELD_RULES.items():
        current_value = _current_value(snapshot, inquiry_field_code)
        current_is_established = current_value is not None
        active_question = _active_question(snapshot, rule.question_type)
        candidates = [observation for observation in eligible if observation.reported_field_code == rule.observation_field_code]
        normalized = _normalize_candidates(inquiry_field_code, candidates)
        distinct_values = _distinct_values(normalized)

        if current_is_established:
            if active_question is not None:
                planned_effects.append(
                    _planned_effect(
                        effect_code=INQUIRY_INTAKE_EFFECT_RESOLVE_OPEN_QUESTION,
                        inquiry_field_code=inquiry_field_code,
                        domain_code=rule.domain_code,
                        expected_case_revision=snapshot.rental_case.case_revision,
                        reason_code="current_value_established",
                        current_value=current_value,
                        open_question_id=active_question.open_question_id,
                        open_question_type=rule.question_type,
                    )
                )
            changed_values = [value for value in distinct_values if not _same_value(current_value, value.value)]
            if not changed_values:
                field_evaluations.append(
                    InquiryIntakeFieldEvaluation(
                        inquiry_field_code=inquiry_field_code,
                        outcome_code=(
                            INQUIRY_INTAKE_OUTCOME_OPEN_QUESTION_RESOLVED
                            if active_question is not None
                            else INQUIRY_INTAKE_OUTCOME_NO_CHANGE
                        ),
                        reason_code="matches_current_value",
                        source_observation_ids=tuple(item.inbound_observation_id for item in normalized),
                        current_value=current_value,
                        selected_value=current_value,
                        linked_open_question_id=None if active_question is None else active_question.open_question_id,
                    )
                )
                continue
            if len(changed_values) == 1:
                selected = changed_values[0]
                already_recorded = (
                    _has_matching_reschedule_request(snapshot, current_value=current_value, proposed_value=selected.value)
                    if inquiry_field_code == INQUIRY_FIELD_REQUESTED_SCHEDULE
                    else _has_matching_proposed_change(
                        snapshot,
                        change_kind=rule.change_kind,
                        current_value=current_value,
                        proposed_value=selected.value,
                    )
                )
                if already_recorded:
                    field_evaluations.append(
                        InquiryIntakeFieldEvaluation(
                            inquiry_field_code=inquiry_field_code,
                            outcome_code=INQUIRY_INTAKE_OUTCOME_NO_CHANGE,
                            reason_code="matching_governed_change_already_exists",
                            source_observation_ids=tuple(
                                observation.inbound_observation_id for observation in selected.observations
                            ),
                            current_value=current_value,
                            selected_value=selected.value,
                            linked_open_question_id=None
                            if active_question is None
                            else active_question.open_question_id,
                        )
                    )
                    continue
                effect_code = (
                    INQUIRY_INTAKE_EFFECT_CREATE_RESCHEDULE_REQUEST
                    if inquiry_field_code == INQUIRY_FIELD_REQUESTED_SCHEDULE
                    else INQUIRY_INTAKE_EFFECT_CREATE_PROPOSED_CHANGE
                )
                planned_effects.append(
                    _planned_effect(
                        effect_code=effect_code,
                        inquiry_field_code=inquiry_field_code,
                        domain_code=rule.domain_code,
                        expected_case_revision=snapshot.rental_case.case_revision,
                        reason_code="existing_value_changed",
                        source_observations=selected.observations,
                        current_value=current_value,
                        proposed_value=selected.value,
                    )
                )
                field_evaluations.append(
                    InquiryIntakeFieldEvaluation(
                        inquiry_field_code=inquiry_field_code,
                        outcome_code=(
                            INQUIRY_INTAKE_OUTCOME_RESCHEDULE_REQUEST
                            if inquiry_field_code == INQUIRY_FIELD_REQUESTED_SCHEDULE
                            else INQUIRY_INTAKE_OUTCOME_PROPOSED_CHANGE
                        ),
                        reason_code="existing_value_changed",
                        source_observation_ids=tuple(observation.inbound_observation_id for observation in selected.observations),
                        current_value=current_value,
                        selected_value=selected.value,
                        linked_open_question_id=None if active_question is None else active_question.open_question_id,
                    )
                )
                continue
            field_evaluations.append(
                InquiryIntakeFieldEvaluation(
                    inquiry_field_code=inquiry_field_code,
                    outcome_code=INQUIRY_INTAKE_OUTCOME_NO_CHANGE,
                    reason_code="conflicting_change_candidates",
                    source_observation_ids=tuple(item.inbound_observation_id for item in normalized),
                    current_value=current_value,
                    selected_value=current_value,
                    linked_open_question_id=None if active_question is None else active_question.open_question_id,
                )
            )
            continue

        if len(distinct_values) == 1:
            selected = distinct_values[0]
            planned_effects.append(
                _planned_effect(
                    effect_code=INQUIRY_INTAKE_EFFECT_PROMOTE_CURRENT_VALUE,
                    inquiry_field_code=inquiry_field_code,
                    domain_code=rule.domain_code,
                    expected_case_revision=snapshot.rental_case.case_revision,
                    reason_code="initial_current_value_established",
                    source_observations=selected.observations,
                    proposed_value=selected.value,
                )
            )
            if active_question is not None:
                planned_effects.append(
                    _planned_effect(
                        effect_code=INQUIRY_INTAKE_EFFECT_RESOLVE_OPEN_QUESTION,
                        inquiry_field_code=inquiry_field_code,
                        domain_code=rule.domain_code,
                        expected_case_revision=snapshot.rental_case.case_revision,
                        reason_code="resolved_by_promoted_value",
                        source_observations=selected.observations,
                        proposed_value=selected.value,
                        open_question_id=active_question.open_question_id,
                        open_question_type=rule.question_type,
                    )
                )
            field_evaluations.append(
                InquiryIntakeFieldEvaluation(
                    inquiry_field_code=inquiry_field_code,
                    outcome_code=INQUIRY_INTAKE_OUTCOME_PROMOTED,
                    reason_code="initial_current_value_established",
                    source_observation_ids=tuple(observation.inbound_observation_id for observation in selected.observations),
                    selected_value=selected.value,
                    linked_open_question_id=None if active_question is None else active_question.open_question_id,
                )
            )
            continue

        if active_question is None:
            question_reason = "missing_core_field"
            if len(distinct_values) > 1:
                question_reason = "conflicting_observations"
            elif normalized:
                question_reason = "incomplete_or_ambiguous_value"
            planned_effects.append(
                _planned_effect(
                    effect_code=INQUIRY_INTAKE_EFFECT_CREATE_OPEN_QUESTION,
                    inquiry_field_code=inquiry_field_code,
                    domain_code=rule.domain_code,
                    expected_case_revision=snapshot.rental_case.case_revision,
                    reason_code=question_reason,
                    source_observations=tuple(observation for item in distinct_values for observation in item.observations)
                    or tuple(observation for observation in normalized),
                    open_question_type=rule.question_type,
                    human_question_text=rule.human_question_text,
                    blocking_scope=rule.blocking_scope,
                )
            )
        field_evaluations.append(
            InquiryIntakeFieldEvaluation(
                inquiry_field_code=inquiry_field_code,
                outcome_code=(
                    INQUIRY_INTAKE_OUTCOME_CONFLICT
                    if len(distinct_values) > 1
                    else (
                        INQUIRY_INTAKE_OUTCOME_OPEN_QUESTION_CREATED
                        if active_question is None
                        else INQUIRY_INTAKE_OUTCOME_OPEN_QUESTION_PRESERVED
                    )
                ),
                reason_code=(
                    "conflicting_observations"
                    if len(distinct_values) > 1
                    else ("missing_core_field" if not normalized else "incomplete_or_ambiguous_value")
                ),
                source_observation_ids=tuple(observation.inbound_observation_id for observation in normalized),
                linked_open_question_id=None if active_question is None else active_question.open_question_id,
            )
        )

    return InquiryIntakePlan(
        rental_case_id=snapshot.rental_case.rental_case_id,
        evaluated_case_revision=snapshot.rental_case.case_revision,
        eligible_observation_ids=tuple(observation.inbound_observation_id for observation in eligible),
        field_evaluations=tuple(field_evaluations),
        effects=tuple(_dedupe_effects(planned_effects)),
    )


def _dedupe_effects(effects: list[InquiryIntakePlannedEffect]) -> tuple[InquiryIntakePlannedEffect, ...]:
    seen: set[str] = set()
    ordered: list[InquiryIntakePlannedEffect] = []
    for effect in effects:
        if effect.idempotency_key in seen:
            continue
        seen.add(effect.idempotency_key)
        ordered.append(effect)
    return tuple(ordered)


def _is_eligible_observation(
    observation: InboundObservation,
    effect: InboundObservationEffect | None,
) -> bool:
    if observation.rental_case_id is None:
        return False
    if observation.status != "validated":
        return False
    if effect is None:
        return False
    if effect.disposition_code in {"reject_quarantine", "manual_mapping_required", "case_association_required"}:
        return False
    return True


def _current_value(snapshot: ObservationCaseSnapshot, inquiry_field_code: str) -> Any:
    if inquiry_field_code == INQUIRY_FIELD_REQUESTED_SCHEDULE:
        if snapshot.rental_case.active_event_start and snapshot.rental_case.active_event_end:
            normalized_start = _normalize_iso_timestamp(snapshot.rental_case.active_event_start)
            normalized_end = _normalize_iso_timestamp(snapshot.rental_case.active_event_end)
            if normalized_start is None or normalized_end is None:
                return None
            return {
                "active_event_start": normalized_start,
                "active_event_end": normalized_end,
            }
        return None
    if inquiry_field_code == INQUIRY_FIELD_GUEST_COUNT:
        fact = snapshot.find_fact("guest_count")
        return None if fact is None else fact.value_payload
    if inquiry_field_code == INQUIRY_FIELD_REQUESTED_SPACE:
        return (
            snapshot.rental_case.rental_type_code
            if snapshot.rental_case.rental_type_code in SPECIFIC_RENTAL_SCOPE_CODES
            else None
        )
    if inquiry_field_code == INQUIRY_FIELD_EVENT_TYPE:
        fact = snapshot.find_fact("event_type")
        if fact is None or not isinstance(fact.value_payload, str) or not fact.value_payload.strip():
            return None
        return fact.value_payload.strip()
    raise AssertionError(f"Unsupported inquiry field: {inquiry_field_code}")


def _active_question(snapshot: ObservationCaseSnapshot, question_type: str):
    for question in snapshot.open_questions:
        if question.question_type != question_type:
            continue
        if question.status not in {OPEN_QUESTION_STATUS_OPEN, OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION}:
            continue
        return question
    return None


@dataclass(frozen=True)
class _DistinctValue:
    value: Any
    observations: tuple[_NormalizedObservation, ...]


def _normalize_candidates(
    inquiry_field_code: str,
    observations: list[InboundObservation],
) -> tuple[_NormalizedObservation, ...]:
    normalized: list[_NormalizedObservation] = []
    for observation in observations:
        value = _normalize_observation_value(inquiry_field_code, observation.candidate_value_payload)
        if value is None:
            continue
        normalized.append(
            _NormalizedObservation(
                inbound_observation_id=observation.inbound_observation_id,
                source_evidence_reference=observation.source_evidence_reference,
                created_at=observation.created_at,
                value=value,
            )
        )
    return tuple(normalized)


def _normalize_observation_value(inquiry_field_code: str, payload: Any) -> Any | None:
    if inquiry_field_code == INQUIRY_FIELD_REQUESTED_SCHEDULE:
        if not isinstance(payload, dict):
            return None
        raw_start = payload.get("active_event_start")
        raw_end = payload.get("active_event_end")
        if not isinstance(raw_start, str) or not raw_start.strip() or not isinstance(raw_end, str) or not raw_end.strip():
            return None
        start_value = _normalize_iso_timestamp(raw_start)
        end_value = _normalize_iso_timestamp(raw_end)
        if start_value is None or end_value is None:
            return None
        if end_value < start_value:
            return None
        return {"active_event_start": start_value, "active_event_end": end_value}
    if inquiry_field_code == INQUIRY_FIELD_GUEST_COUNT:
        if not isinstance(payload, int) or isinstance(payload, bool) or payload <= 0:
            return None
        return payload
    if inquiry_field_code == INQUIRY_FIELD_REQUESTED_SPACE:
        if not isinstance(payload, str):
            return None
        value = payload.strip()
        if value not in SPECIFIC_RENTAL_SCOPE_CODES:
            return None
        return value
    if inquiry_field_code == INQUIRY_FIELD_EVENT_TYPE:
        if not isinstance(payload, str):
            return None
        value = payload.strip()
        return value or None
    raise AssertionError(f"Unsupported inquiry field: {inquiry_field_code}")


def _normalize_iso_timestamp(value: str) -> str | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.isoformat().replace("+00:00", "Z")


def _distinct_values(normalized: tuple[_NormalizedObservation, ...]) -> tuple[_DistinctValue, ...]:
    grouped: dict[str, list[_NormalizedObservation]] = {}
    value_by_key: dict[str, Any] = {}
    for observation in normalized:
        key = _json_key(observation.value)
        grouped.setdefault(key, []).append(observation)
        value_by_key[key] = observation.value
    ordered = []
    for key, items in grouped.items():
        ordered.append(
            _DistinctValue(
                value=value_by_key[key],
                observations=tuple(sorted(items, key=lambda item: (item.created_at, item.inbound_observation_id))),
            )
        )
    return tuple(sorted(ordered, key=lambda item: item.observations[-1].created_at if item.observations else ""))


def _planned_effect(
    *,
    effect_code: str,
    inquiry_field_code: str,
    domain_code: str,
    expected_case_revision: int,
    reason_code: str,
    source_observations: tuple[_NormalizedObservation, ...] = (),
    current_value: Any = None,
    proposed_value: Any = None,
    open_question_id: int | None = None,
    open_question_type: str | None = None,
    human_question_text: str | None = None,
    blocking_scope: str | None = None,
) -> InquiryIntakePlannedEffect:
    source_ids = tuple(observation.inbound_observation_id for observation in source_observations)
    source_references = tuple(observation.source_evidence_reference for observation in source_observations)
    effect_identity = {
        "effect_code": effect_code,
        "field_code": inquiry_field_code,
        "reason_code": reason_code,
        "source_ids": list(source_ids),
        "current_value": current_value,
        "proposed_value": proposed_value,
        "open_question_id": open_question_id,
        "open_question_type": open_question_type,
    }
    digest = hashlib.sha256(
        json.dumps(effect_identity, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    return InquiryIntakePlannedEffect(
        effect_code=effect_code,
        inquiry_field_code=inquiry_field_code,
        domain_code=domain_code,
        expected_case_revision=expected_case_revision,
        idempotency_key=f"inquiry-intake:{inquiry_field_code}:{effect_code}:{digest}",
        reason_code=reason_code,
        source_observation_ids=source_ids,
        source_observation_references=source_references,
        current_value=current_value,
        proposed_value=proposed_value,
        open_question_id=open_question_id,
        open_question_type=open_question_type,
        human_question_text=human_question_text,
        blocking_scope=blocking_scope,
    )


def _same_value(left: Any, right: Any) -> bool:
    return _json_key(left) == _json_key(right)


def _json_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _has_matching_proposed_change(
    snapshot: ObservationCaseSnapshot,
    *,
    change_kind: str,
    current_value: Any,
    proposed_value: Any,
) -> bool:
    for change in snapshot.proposed_changes:
        if change.change_kind != change_kind or change.status not in ACTIVE_CHANGE_STATUSES:
            continue
        if _same_value(change.prior_value_payload, current_value) and _same_value(change.proposed_value_payload, proposed_value):
            return True
    return False


def _has_matching_reschedule_request(
    snapshot: ObservationCaseSnapshot,
    *,
    current_value: Any,
    proposed_value: Any,
) -> bool:
    for request in snapshot.reschedule_requests:
        if request.status not in ACTIVE_RESCHEDULE_STATUSES:
            continue
        if _same_value(request.current_active_date_snapshot, current_value) and _same_value(
            request.requested_date_payload,
            proposed_value,
        ):
            return True
    return False
