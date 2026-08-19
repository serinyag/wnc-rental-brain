from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Callable

from .contracts import CHANGE_IMPACT_MATERIAL, RESCHEDULE_URGENCY_NORMAL
from .observation_contracts import (
    InboundObservation,
    InboundObservationEffect,
    InboundSourceRecord,
    OBSERVATION_CLAIM_KIND_CHANGE_REQUEST,
    OBSERVATION_DISPOSITION_CASE_ASSOCIATION_REQUIRED,
    OBSERVATION_DISPOSITION_CREATE_CASE_DECISION_CANDIDATE,
    OBSERVATION_DISPOSITION_CREATE_PROPOSED_CHANGE,
    OBSERVATION_DISPOSITION_CREATE_RESCHEDULE_REQUEST,
    OBSERVATION_DISPOSITION_MANUAL_MAPPING_REQUIRED,
    OBSERVATION_DISPOSITION_NO_WORKFLOW_EFFECT,
    OBSERVATION_DISPOSITION_OPEN_QUESTION_ANSWER_CANDIDATE,
    OBSERVATION_DISPOSITION_RECORD_CONFIRMATION_CANDIDATE,
    OBSERVATION_DISPOSITION_RECORD_REQUIREMENT_EVIDENCE_CANDIDATE,
    OBSERVATION_DISPOSITION_REJECT_QUARANTINE,
    OBSERVATION_STATUS_CANDIDATE,
    OBSERVATION_STATUS_QUARANTINED,
    OBSERVATION_STATUS_UNMAPPED,
    OBSERVATION_STATUS_VALIDATED,
    OBSERVATION_TARGET_KIND_CASE_DECISION,
    OBSERVATION_TARGET_KIND_CONFIRMATION_EVIDENCE,
    OBSERVATION_TARGET_KIND_RENTAL_CASE_FACT,
    OBSERVATION_TARGET_KIND_RENTAL_CASE_SCHEDULE,
    OBSERVATION_TARGET_KIND_REQUIREMENT_EVIDENCE,
    OBSERVATION_TYPE_CHANGE_CANDIDATE,
    OBSERVATION_TYPE_CONFIRMATION_CANDIDATE,
    OBSERVATION_TYPE_REQUEST_CANDIDATE,
    SOURCE_ASSOCIATION_STATUS_CASE_ASSOCIATION_REQUIRED,
    SOURCE_ASSOCIATION_STATUS_RESOLVED,
    ObservationFieldDefinition,
)
from .observation_registry import get_field_definition
from .observation_repository import (
    ObservationCaseSnapshot,
    ObservationRepositoryProtocol,
    current_timestamp,
)
from .observation_types import (
    OBSERVATION_FAILURE_CASE_ASSOCIATION_REQUIRED,
    OBSERVATION_FAILURE_CASE_NOT_FOUND,
    OBSERVATION_FAILURE_CROSS_CASE_REFERENCE,
    OBSERVATION_FAILURE_INVALID_OBSERVATION_TYPE,
    OBSERVATION_FAILURE_INVALID_VALUE_TYPE,
    OBSERVATION_FAILURE_MANUAL_MAPPING_REQUIRED,
    OBSERVATION_FAILURE_OBSERVATION_DUPLICATE,
    OBSERVATION_FAILURE_SOURCE_DUPLICATE,
    OBSERVATION_FAILURE_STALE_OBSERVATION,
    OBSERVATION_FAILURE_UNKNOWN_FIELD,
    CaseAssociationInput,
    CaseAssociationResult,
    ObservationDispositionResult,
    ObservationIngestionResult,
    StructuredObservationCandidate,
    StructuredObservationIngestionRequest,
)
from .validation import Phase8ContractError


def ingest_structured_observations(
    *,
    request: StructuredObservationIngestionRequest,
    repository: ObservationRepositoryProtocol,
    now: Callable[[], str] = current_timestamp,
) -> ObservationIngestionResult:
    existing_source = repository.get_source_by_dedupe(
        source_system_code=request.source_record.source_system_code,
        dedupe_key=request.source_record.dedupe_key,
    )
    if existing_source is not None:
        return ObservationIngestionResult(
            duplicate_source=True,
            source_record=existing_source,
            case_association=_build_case_association_from_source(existing_source, repository),
            observation_results=_rebuild_results_for_source(existing_source, repository),
            failure_codes=(OBSERVATION_FAILURE_SOURCE_DUPLICATE,),
        )

    case_association, case_snapshot = _resolve_case_association(request.case_association, repository)
    created_at = now()
    source_record = repository.create_source_record(
        source_record_input=request.source_record,
        case_association=case_association,
        created_at=created_at,
    )

    observation_results = []
    for candidate in request.observations:
        observation_results.append(
            _ingest_one_candidate(
                candidate=candidate,
                source_record=source_record,
                case_association=case_association,
                case_snapshot=case_snapshot,
                repository=repository,
                created_at=created_at,
            )
        )

    failure_codes = tuple(
        dict.fromkeys(
            code
            for result in observation_results
            for code in result.failure_codes
        )
    )
    return ObservationIngestionResult(
        duplicate_source=False,
        source_record=source_record,
        case_association=case_association,
        observation_results=tuple(observation_results),
        failure_codes=failure_codes,
    )


def _ingest_one_candidate(
    *,
    candidate: StructuredObservationCandidate,
    source_record: InboundSourceRecord,
    case_association: CaseAssociationResult,
    case_snapshot: ObservationCaseSnapshot | None,
    repository: ObservationRepositoryProtocol,
    created_at: str,
) -> ObservationDispositionResult:
    field_definition = get_field_definition(candidate.reported_field_code)
    observation_status = OBSERVATION_STATUS_VALIDATED
    failure_codes: tuple[str, ...] = ()
    reported_domain_code = candidate.reported_domain_code
    target_field_code: str | None = None
    target_domain_code: str | None = None

    if field_definition is None:
        observation_status = OBSERVATION_STATUS_UNMAPPED
        failure_codes = (OBSERVATION_FAILURE_UNKNOWN_FIELD, OBSERVATION_FAILURE_MANUAL_MAPPING_REQUIRED)
    else:
        reported_domain_code = reported_domain_code or field_definition.domain_code
        target_field_code = field_definition.field_code
        target_domain_code = field_definition.domain_code
        failure_codes = _validate_candidate(candidate, field_definition)
        if OBSERVATION_FAILURE_UNKNOWN_FIELD in failure_codes or OBSERVATION_FAILURE_MANUAL_MAPPING_REQUIRED in failure_codes:
            observation_status = OBSERVATION_STATUS_UNMAPPED
        elif failure_codes:
            observation_status = OBSERVATION_STATUS_QUARANTINED

    observation_identity_key = _observation_identity_key(candidate)
    existing_observation = repository.get_observation_by_identity(
        inbound_source_record_id=source_record.inbound_source_record_id,
        observation_identity_key=observation_identity_key,
    )
    if existing_observation is not None:
        existing_effect = repository.get_effect_for_observation(existing_observation.inbound_observation_id)
        if existing_effect is None:
            raise Phase8ContractError(
                error_category="missing_value",
                safe_message="Existing observation rows must have a persisted routing effect.",
            )
        return _build_result(
            observation=existing_observation,
            effect=existing_effect,
            repository=repository,
            extra_failure_codes=(OBSERVATION_FAILURE_OBSERVATION_DUPLICATE,),
        )

    observation = repository.create_observation(
        inbound_source_record_id=source_record.inbound_source_record_id,
        rental_case_id=case_association.rental_case_id,
        reported_field_code=candidate.reported_field_code,
        reported_domain_code=reported_domain_code,
        target_field_code=target_field_code,
        target_domain_code=target_domain_code,
        observation_type=candidate.observation_type,
        claim_kind=candidate.claim_kind,
        candidate_value_payload=candidate.candidate_value_payload,
        source_evidence_reference=candidate.source_evidence_reference,
        status=observation_status if case_association.status == SOURCE_ASSOCIATION_STATUS_RESOLVED else OBSERVATION_STATUS_CANDIDATE,
        observation_identity_key=observation_identity_key,
        asserted_by_party_type=candidate.asserted_by_party_type,
        asserted_by_reference=candidate.asserted_by_reference,
        source_excerpt=candidate.source_excerpt,
        observed_against_case_revision=candidate.observed_against_case_revision,
        extraction_confidence=candidate.extraction_confidence,
        ambiguity_flags=candidate.ambiguity_flags,
        created_at=created_at,
    )

    effect = _route_observation(
        observation=observation,
        candidate=candidate,
        source_record=source_record,
        case_association=case_association,
        case_snapshot=case_snapshot,
        field_definition=field_definition,
        observation_failure_codes=failure_codes,
        repository=repository,
        created_at=created_at,
    )
    return _build_result(observation=observation, effect=effect, repository=repository)


def _route_observation(
    *,
    observation: InboundObservation,
    candidate: StructuredObservationCandidate,
    source_record: InboundSourceRecord,
    case_association: CaseAssociationResult,
    case_snapshot: ObservationCaseSnapshot | None,
    field_definition: ObservationFieldDefinition | None,
    observation_failure_codes: tuple[str, ...],
    repository: ObservationRepositoryProtocol,
    created_at: str,
) -> InboundObservationEffect:
    if case_association.status != SOURCE_ASSOCIATION_STATUS_RESOLVED or case_snapshot is None:
        return repository.create_effect(
            inbound_observation_id=observation.inbound_observation_id,
            rental_case_id=None,
            disposition_code=OBSERVATION_DISPOSITION_CASE_ASSOCIATION_REQUIRED,
            revalidation_required=True,
            stale_observation=False,
            reason_codes=("case_association_required",),
            failure_codes=(OBSERVATION_FAILURE_CASE_ASSOCIATION_REQUIRED,),
            created_at=created_at,
        )

    if field_definition is None:
        return _create_effect_with_event(
            observation=observation,
            source_record=source_record,
            repository=repository,
            disposition_code=OBSERVATION_DISPOSITION_MANUAL_MAPPING_REQUIRED,
            revalidation_required=True,
            stale_observation=False,
            reason_codes=("unknown_field", "manual_mapping_required"),
            failure_codes=observation_failure_codes,
            created_at=created_at,
        )

    stale_observation = (
        observation.observed_against_case_revision is not None
        and observation.observed_against_case_revision < case_snapshot.rental_case.case_revision
    )
    revalidation_required = (
        stale_observation
        or field_definition.human_validation_required
        or observation.extraction_confidence is None
        or observation.extraction_confidence < 0.85
    )

    failure_codes = observation_failure_codes
    if stale_observation and OBSERVATION_FAILURE_STALE_OBSERVATION not in failure_codes:
        failure_codes = failure_codes + (OBSERVATION_FAILURE_STALE_OBSERVATION,)

    if observation_failure_codes:
        return _create_effect_with_event(
            observation=observation,
            source_record=source_record,
            repository=repository,
            disposition_code=(
                OBSERVATION_DISPOSITION_MANUAL_MAPPING_REQUIRED
                if OBSERVATION_FAILURE_MANUAL_MAPPING_REQUIRED in observation_failure_codes
                else OBSERVATION_DISPOSITION_REJECT_QUARANTINE
            ),
            revalidation_required=True,
            stale_observation=stale_observation,
            reason_codes=tuple(dict.fromkeys(observation_failure_codes)),
            failure_codes=failure_codes,
            created_at=created_at,
        )

    if field_definition.canonical_target_kind == OBSERVATION_TARGET_KIND_CASE_DECISION:
        decision = repository.create_case_decision_candidate(
            rental_case_id=case_snapshot.rental_case.rental_case_id,
            decision_type=field_definition.field_code,
            domain_code=field_definition.domain_code,
            baseline_reference=field_definition.canonical_target_reference or field_definition.field_code,
            proposed_value_payload=observation.candidate_value_payload,
            scope_key=f"{field_definition.field_code}:{case_snapshot.rental_case.rental_case_id}",
            scope_description=field_definition.display_label,
            authority_basis=_authority_basis(observation, source_record),
            approval_posture=field_definition.default_review_posture or "approval_required",
            evidence_reference=_observation_reference(observation.inbound_observation_id),
            created_at=created_at,
        )
        return _create_effect_with_event(
            observation=observation,
            source_record=source_record,
            repository=repository,
            disposition_code=OBSERVATION_DISPOSITION_CREATE_CASE_DECISION_CANDIDATE,
            revalidation_required=revalidation_required,
            stale_observation=stale_observation,
            reason_codes=("proposed_decision_candidate",) + _stale_reason(stale_observation),
            failure_codes=failure_codes,
            created_at=created_at,
            linked_case_decision_id=decision.case_decision_id,
        )

    if field_definition.canonical_target_kind == OBSERVATION_TARGET_KIND_RENTAL_CASE_SCHEDULE:
        current_snapshot = _current_active_date_snapshot(case_snapshot)
        candidate_schedule = _validated_schedule_payload(observation.candidate_value_payload)
        current_schedule_established = _schedule_snapshot_is_established(current_snapshot)
        if candidate_schedule is None:
            return _create_effect_with_event(
                observation=observation,
                source_record=source_record,
                repository=repository,
                disposition_code=OBSERVATION_DISPOSITION_NO_WORKFLOW_EFFECT,
                revalidation_required=True,
                stale_observation=stale_observation,
                reason_codes=("incomplete_schedule_candidate", "no_direct_truth_mutation") + _stale_reason(stale_observation),
                failure_codes=failure_codes,
                created_at=created_at,
            )
        if not current_schedule_established:
            return _create_effect_with_event(
                observation=observation,
                source_record=source_record,
                repository=repository,
                disposition_code=OBSERVATION_DISPOSITION_NO_WORKFLOW_EFFECT,
                revalidation_required=True,
                stale_observation=stale_observation,
                reason_codes=("schedule_candidate_pending_inquiry_intake", "no_direct_truth_mutation") + _stale_reason(stale_observation),
                failure_codes=failure_codes,
                created_at=created_at,
            )
        if _values_differ(current_snapshot, candidate_schedule):
            reschedule_request = repository.create_reschedule_request(
                rental_case_id=case_snapshot.rental_case.rental_case_id,
                current_active_date_snapshot=current_snapshot,
                requested_date_payload=candidate_schedule,
                consequence_summary_payload={
                    "source_observation_id": observation.inbound_observation_id,
                    "field_code": field_definition.field_code,
                },
                urgency_class=candidate.requested_urgency_class or RESCHEDULE_URGENCY_NORMAL,
                created_at=created_at,
            )
            return _create_effect_with_event(
                observation=observation,
                source_record=source_record,
                repository=repository,
                disposition_code=OBSERVATION_DISPOSITION_CREATE_RESCHEDULE_REQUEST,
                revalidation_required=True,
                stale_observation=stale_observation,
                reason_codes=("reschedule_candidate",) + _stale_reason(stale_observation),
                failure_codes=failure_codes,
                created_at=created_at,
                linked_reschedule_request_id=reschedule_request.reschedule_request_id,
            )
        disposition = (
            OBSERVATION_DISPOSITION_RECORD_CONFIRMATION_CANDIDATE
            if observation.observation_type == OBSERVATION_TYPE_CONFIRMATION_CANDIDATE
            else OBSERVATION_DISPOSITION_NO_WORKFLOW_EFFECT
        )
        reason_codes = ("no_schedule_change_detected",)
        if disposition == OBSERVATION_DISPOSITION_RECORD_CONFIRMATION_CANDIDATE:
            reason_codes = ("confirmation_candidate",)
        return _create_effect_with_event(
            observation=observation,
            source_record=source_record,
            repository=repository,
            disposition_code=disposition,
            revalidation_required=revalidation_required,
            stale_observation=stale_observation,
            reason_codes=reason_codes + _stale_reason(stale_observation),
            failure_codes=failure_codes,
            created_at=created_at,
        )

    if field_definition.canonical_target_kind == OBSERVATION_TARGET_KIND_REQUIREMENT_EVIDENCE:
        requirement = case_snapshot.find_requirement(field_definition.related_requirement_types)
        if requirement is None:
            return _create_effect_with_event(
                observation=observation,
                source_record=source_record,
                repository=repository,
                disposition_code=OBSERVATION_DISPOSITION_MANUAL_MAPPING_REQUIRED,
                revalidation_required=True,
                stale_observation=stale_observation,
                reason_codes=("manual_mapping_required", "requirement_not_found") + _stale_reason(stale_observation),
                failure_codes=(OBSERVATION_FAILURE_MANUAL_MAPPING_REQUIRED,) + _stale_failure(stale_observation),
                created_at=created_at,
            )
        try:
            repository.attach_requirement_evidence(
                rental_case_id=case_snapshot.rental_case.rental_case_id,
                requirement_id=requirement.requirement_id,
                evidence_reference=_observation_reference(observation.inbound_observation_id),
            )
        except ValueError as error:
            if str(error) != "cross_case_reference":
                raise
            return _create_effect_with_event(
                observation=observation,
                source_record=source_record,
                repository=repository,
                disposition_code=OBSERVATION_DISPOSITION_REJECT_QUARANTINE,
                revalidation_required=True,
                stale_observation=stale_observation,
                reason_codes=("cross_case_reference",),
                failure_codes=(OBSERVATION_FAILURE_CROSS_CASE_REFERENCE,),
                created_at=created_at,
            )
        return _create_effect_with_event(
            observation=observation,
            source_record=source_record,
            repository=repository,
            disposition_code=OBSERVATION_DISPOSITION_RECORD_REQUIREMENT_EVIDENCE_CANDIDATE,
            revalidation_required=revalidation_required,
            stale_observation=stale_observation,
            reason_codes=("requirement_evidence_candidate",) + _stale_reason(stale_observation),
            failure_codes=failure_codes,
            created_at=created_at,
            linked_requirement_id=requirement.requirement_id,
        )

    if field_definition.canonical_target_kind == OBSERVATION_TARGET_KIND_CONFIRMATION_EVIDENCE:
        return _create_effect_with_event(
            observation=observation,
            source_record=source_record,
            repository=repository,
            disposition_code=OBSERVATION_DISPOSITION_RECORD_CONFIRMATION_CANDIDATE,
            revalidation_required=revalidation_required,
            stale_observation=stale_observation,
            reason_codes=("confirmation_candidate",) + _stale_reason(stale_observation),
            failure_codes=failure_codes,
            created_at=created_at,
        )

    prior_fact = case_snapshot.find_fact(field_definition.field_code)
    related_question = case_snapshot.find_open_question(field_definition.related_open_question_types)
    if prior_fact is None:
        if related_question is not None:
            repository.update_open_question_answer_candidate(
                rental_case_id=case_snapshot.rental_case.rental_case_id,
                open_question_id=related_question.open_question_id,
                proposed_answer_payload=observation.candidate_value_payload,
                source_reference=_observation_reference(observation.inbound_observation_id),
            )
            return _create_effect_with_event(
                observation=observation,
                source_record=source_record,
                repository=repository,
                disposition_code=OBSERVATION_DISPOSITION_OPEN_QUESTION_ANSWER_CANDIDATE,
                revalidation_required=True,
                stale_observation=stale_observation,
                reason_codes=("question_answer_candidate", "new_information_candidate") + _stale_reason(stale_observation),
                failure_codes=failure_codes,
                created_at=created_at,
                linked_open_question_id=related_question.open_question_id,
            )
        if observation.observation_type == OBSERVATION_TYPE_CONFIRMATION_CANDIDATE:
            return _create_effect_with_event(
                observation=observation,
                source_record=source_record,
                repository=repository,
                disposition_code=OBSERVATION_DISPOSITION_RECORD_CONFIRMATION_CANDIDATE,
                revalidation_required=True,
                stale_observation=stale_observation,
                reason_codes=("confirmation_candidate", "new_information_candidate") + _stale_reason(stale_observation),
                failure_codes=failure_codes,
                created_at=created_at,
            )
        return _create_effect_with_event(
            observation=observation,
            source_record=source_record,
            repository=repository,
            disposition_code=OBSERVATION_DISPOSITION_NO_WORKFLOW_EFFECT,
            revalidation_required=True,
            stale_observation=stale_observation,
            reason_codes=("new_information_candidate", "no_direct_truth_mutation") + _stale_reason(stale_observation),
            failure_codes=failure_codes,
            created_at=created_at,
        )

    if not _values_differ(prior_fact.value_payload, observation.candidate_value_payload):
        if related_question is not None:
            repository.update_open_question_answer_candidate(
                rental_case_id=case_snapshot.rental_case.rental_case_id,
                open_question_id=related_question.open_question_id,
                proposed_answer_payload=observation.candidate_value_payload,
                source_reference=_observation_reference(observation.inbound_observation_id),
            )
            return _create_effect_with_event(
                observation=observation,
                source_record=source_record,
                repository=repository,
                disposition_code=OBSERVATION_DISPOSITION_OPEN_QUESTION_ANSWER_CANDIDATE,
                revalidation_required=True,
                stale_observation=stale_observation,
                reason_codes=("question_answer_candidate", "matches_existing_value") + _stale_reason(stale_observation),
                failure_codes=failure_codes,
                created_at=created_at,
                linked_open_question_id=related_question.open_question_id,
            )
        if observation.observation_type == OBSERVATION_TYPE_CONFIRMATION_CANDIDATE:
            return _create_effect_with_event(
                observation=observation,
                source_record=source_record,
                repository=repository,
                disposition_code=OBSERVATION_DISPOSITION_RECORD_CONFIRMATION_CANDIDATE,
                revalidation_required=revalidation_required,
                stale_observation=stale_observation,
                reason_codes=("confirmation_candidate", "matches_existing_value") + _stale_reason(stale_observation),
                failure_codes=failure_codes,
                created_at=created_at,
            )
        return _create_effect_with_event(
            observation=observation,
            source_record=source_record,
            repository=repository,
            disposition_code=OBSERVATION_DISPOSITION_NO_WORKFLOW_EFFECT,
            revalidation_required=revalidation_required,
            stale_observation=stale_observation,
            reason_codes=("no_change_detected",) + _stale_reason(stale_observation),
            failure_codes=failure_codes,
            created_at=created_at,
        )

    impact_classification = candidate.impact_classification or field_definition.materiality_default or CHANGE_IMPACT_MATERIAL
    proposed_change = repository.create_proposed_change(
        rental_case_id=case_snapshot.rental_case.rental_case_id,
        change_kind=field_definition.field_code,
        domain_code=field_definition.domain_code,
        prior_value_payload=prior_fact.value_payload,
        proposed_value_payload=observation.candidate_value_payload,
        source_reference=_observation_reference(observation.inbound_observation_id),
        detected_at=created_at,
        impact_classification=impact_classification,
        affected_domain_codes=(field_definition.domain_code,),
        review_posture=field_definition.default_review_posture,
    )
    return _create_effect_with_event(
        observation=observation,
        source_record=source_record,
        repository=repository,
        disposition_code=OBSERVATION_DISPOSITION_CREATE_PROPOSED_CHANGE,
        revalidation_required=True,
        stale_observation=stale_observation,
        reason_codes=("existing_value_changed", impact_classification) + _stale_reason(stale_observation),
        failure_codes=failure_codes,
        created_at=created_at,
        linked_proposed_change_id=proposed_change.proposed_case_change_id,
    )


def _resolve_case_association(
    case_association: CaseAssociationInput,
    repository: ObservationRepositoryProtocol,
) -> tuple[CaseAssociationResult, ObservationCaseSnapshot | None]:
    if case_association.rental_case_id is not None:
        snapshot = repository.load_case_snapshot(case_association.rental_case_id)
        if snapshot is None:
            return (
                CaseAssociationResult(
                    status=SOURCE_ASSOCIATION_STATUS_CASE_ASSOCIATION_REQUIRED,
                    failure_codes=(OBSERVATION_FAILURE_CASE_NOT_FOUND,),
                    association_basis=case_association.association_basis_hint or "explicit_rental_case_id_not_found",
                ),
                None,
            )
        return (
            CaseAssociationResult(
                status=SOURCE_ASSOCIATION_STATUS_RESOLVED,
                rental_case_id=snapshot.rental_case.rental_case_id,
                case_reference_code=snapshot.rental_case.case_reference_code,
                observed_case_revision=snapshot.rental_case.case_revision,
                association_basis=case_association.association_basis_hint or "explicit_rental_case_id",
            ),
            snapshot,
        )

    if case_association.case_reference_code is not None:
        rental_case = repository.get_case_by_reference(case_association.case_reference_code)
        if rental_case is None:
            return (
                CaseAssociationResult(
                    status=SOURCE_ASSOCIATION_STATUS_CASE_ASSOCIATION_REQUIRED,
                    failure_codes=(OBSERVATION_FAILURE_CASE_NOT_FOUND,),
                    case_reference_code=case_association.case_reference_code,
                    association_basis=case_association.association_basis_hint or "explicit_case_reference_not_found",
                ),
                None,
            )
        snapshot = repository.load_case_snapshot(rental_case.rental_case_id)
        if snapshot is None:
            return (
                CaseAssociationResult(
                    status=SOURCE_ASSOCIATION_STATUS_CASE_ASSOCIATION_REQUIRED,
                    failure_codes=(OBSERVATION_FAILURE_CASE_NOT_FOUND,),
                    case_reference_code=case_association.case_reference_code,
                    association_basis=case_association.association_basis_hint or "explicit_case_reference_not_found",
                ),
                None,
            )
        return (
            CaseAssociationResult(
                status=SOURCE_ASSOCIATION_STATUS_RESOLVED,
                rental_case_id=snapshot.rental_case.rental_case_id,
                case_reference_code=snapshot.rental_case.case_reference_code,
                observed_case_revision=snapshot.rental_case.case_revision,
                association_basis=case_association.association_basis_hint or "explicit_case_reference_code",
            ),
            snapshot,
        )

    return (
        CaseAssociationResult(
            status=SOURCE_ASSOCIATION_STATUS_CASE_ASSOCIATION_REQUIRED,
            failure_codes=(OBSERVATION_FAILURE_CASE_ASSOCIATION_REQUIRED,),
            association_basis=case_association.association_basis_hint or "deterministic_association_missing",
        ),
        None,
    )


def _validate_candidate(
    candidate: StructuredObservationCandidate,
    field_definition: ObservationFieldDefinition,
) -> tuple[str, ...]:
    failure_codes: list[str] = []
    if candidate.reported_domain_code is not None and candidate.reported_domain_code != field_definition.domain_code:
        failure_codes.append(OBSERVATION_FAILURE_MANUAL_MAPPING_REQUIRED)
    if candidate.observation_type not in field_definition.allowed_observation_types:
        failure_codes.append(OBSERVATION_FAILURE_INVALID_OBSERVATION_TYPE)
    if candidate.asserted_by_party_type == "client" and not field_definition.client_input_allowed:
        failure_codes.append(OBSERVATION_FAILURE_MANUAL_MAPPING_REQUIRED)
    if not _value_matches_definition(candidate.candidate_value_payload, field_definition):
        failure_codes.append(OBSERVATION_FAILURE_INVALID_VALUE_TYPE)
    return tuple(dict.fromkeys(failure_codes))


def _value_matches_definition(value: Any, field_definition: ObservationFieldDefinition) -> bool:
    value_type = field_definition.value_type_code
    if value_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if value_type == "text":
        return isinstance(value, str) and value.strip() != ""
    if value_type == "boolean":
        return isinstance(value, bool)
    if value_type == "json_object":
        return isinstance(value, dict)
    if value_type == "enum":
        return isinstance(value, str) and value in field_definition.allowed_enum_values
    if value_type == "enum_array":
        return (
            isinstance(value, list)
            and all(isinstance(item, str) and item in field_definition.allowed_enum_values for item in value)
        )
    return False


def _create_effect_with_event(
    *,
    observation: InboundObservation,
    source_record: InboundSourceRecord,
    repository: ObservationRepositoryProtocol,
    disposition_code: str,
    revalidation_required: bool,
    stale_observation: bool,
    reason_codes: tuple[str, ...],
    failure_codes: tuple[str, ...],
    created_at: str,
    linked_open_question_id: int | None = None,
    linked_requirement_id: int | None = None,
    linked_proposed_change_id: int | None = None,
    linked_case_decision_id: int | None = None,
    linked_reschedule_request_id: int | None = None,
) -> InboundObservationEffect:
    workflow_event = None
    if observation.rental_case_id is not None:
        workflow_event = repository.create_workflow_event(
            rental_case_id=observation.rental_case_id,
            source_type="inbound_observation",
            source_reference=_source_reference(source_record.inbound_source_record_id),
            actor_type=observation.asserted_by_party_type or source_record.sender_actor_type,
            actor_reference=observation.asserted_by_reference or source_record.sender_actor_reference,
            occurred_at=created_at,
            structured_payload={
                "inbound_source_record_id": source_record.inbound_source_record_id,
                "inbound_observation_id": observation.inbound_observation_id,
                "disposition_code": disposition_code,
                "stale_observation": stale_observation,
                "revalidation_required": revalidation_required,
                "reason_codes": list(reason_codes),
                "failure_codes": list(failure_codes),
                "linked_open_question_id": linked_open_question_id,
                "linked_requirement_id": linked_requirement_id,
                "linked_proposed_change_id": linked_proposed_change_id,
                "linked_case_decision_id": linked_case_decision_id,
                "linked_reschedule_request_id": linked_reschedule_request_id,
            },
            event_identity_key=f"inbound-observation:{source_record.inbound_source_record_id}:{observation.observation_identity_key}",
        )

    return repository.create_effect(
        inbound_observation_id=observation.inbound_observation_id,
        rental_case_id=observation.rental_case_id,
        disposition_code=disposition_code,
        revalidation_required=revalidation_required,
        stale_observation=stale_observation,
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        failure_codes=tuple(dict.fromkeys(failure_codes)),
        created_at=created_at,
        linked_open_question_id=linked_open_question_id,
        linked_requirement_id=linked_requirement_id,
        linked_proposed_change_id=linked_proposed_change_id,
        linked_case_decision_id=linked_case_decision_id,
        linked_reschedule_request_id=linked_reschedule_request_id,
        workflow_event_id=None if workflow_event is None else workflow_event.workflow_event_id,
    )


def _build_result(
    *,
    observation: InboundObservation,
    effect: InboundObservationEffect,
    repository: ObservationRepositoryProtocol,
    extra_failure_codes: tuple[str, ...] = (),
) -> ObservationDispositionResult:
    failure_codes = tuple(
        dict.fromkeys(
            repository.get_failure_codes_for_observation(observation.inbound_observation_id) + extra_failure_codes
        )
    )
    return ObservationDispositionResult(
        observation=observation,
        effect=effect,
        failure_codes=failure_codes,
        linked_proposed_change_id=effect.linked_proposed_change_id,
        linked_case_decision_id=effect.linked_case_decision_id,
        linked_reschedule_request_id=effect.linked_reschedule_request_id,
        linked_open_question_id=effect.linked_open_question_id,
        linked_requirement_id=effect.linked_requirement_id,
    )


def _rebuild_results_for_source(
    source_record: InboundSourceRecord,
    repository: ObservationRepositoryProtocol,
) -> tuple[ObservationDispositionResult, ...]:
    results = []
    for observation in repository.list_observations_for_source(source_record.inbound_source_record_id):
        effect = repository.get_effect_for_observation(observation.inbound_observation_id)
        if effect is None:
            raise Phase8ContractError(
                error_category="missing_value",
                safe_message="Persisted inbound observations must retain an effect row for replay-safe idempotency.",
            )
        results.append(_build_result(observation=observation, effect=effect, repository=repository))
    return tuple(results)


def _build_case_association_from_source(
    source_record: InboundSourceRecord,
    repository: ObservationRepositoryProtocol,
) -> CaseAssociationResult:
    observed_case_revision = None
    if source_record.resolved_rental_case_id is not None:
        snapshot = repository.load_case_snapshot(source_record.resolved_rental_case_id)
        if snapshot is not None:
            observed_case_revision = snapshot.rental_case.case_revision
    return CaseAssociationResult(
        status=source_record.association_status,
        rental_case_id=source_record.resolved_rental_case_id,
        case_reference_code=source_record.case_reference_hint,
        observed_case_revision=observed_case_revision,
        association_basis=source_record.association_basis,
    )


def _current_active_date_snapshot(case_snapshot: ObservationCaseSnapshot) -> dict[str, Any]:
    return {
        "active_event_start": case_snapshot.rental_case.active_event_start,
        "active_event_end": case_snapshot.rental_case.active_event_end,
    }


def _ensure_object_payload(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise Phase8ContractError(
            error_category="invalid_value",
            safe_message="Structured schedule observations must use an object payload.",
        )
    return value


def _validated_schedule_payload(value: Any) -> dict[str, Any] | None:
    payload = _ensure_object_payload(value)
    start = payload.get("active_event_start")
    end = payload.get("active_event_end")
    if not isinstance(start, str) or not start.strip() or not isinstance(end, str) or not end.strip():
        return None
    normalized_start = _normalize_iso_timestamp(start)
    normalized_end = _normalize_iso_timestamp(end)
    if normalized_start is None or normalized_end is None:
        return None
    if normalized_end < normalized_start:
        return None
    return {
        "active_event_start": normalized_start,
        "active_event_end": normalized_end,
    }


def _normalize_iso_timestamp(value: str) -> str | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.isoformat().replace("+00:00", "Z")


def _schedule_snapshot_is_established(snapshot: dict[str, Any]) -> bool:
    start = snapshot.get("active_event_start")
    end = snapshot.get("active_event_end")
    return isinstance(start, str) and start.strip() != "" and isinstance(end, str) and end.strip() != ""


def _authority_basis(observation: InboundObservation, source_record: InboundSourceRecord) -> str:
    actor_type = observation.asserted_by_party_type or source_record.sender_actor_type or "unknown"
    actor_reference = observation.asserted_by_reference or source_record.sender_actor_reference or "unknown"
    return f"observation:{actor_type}:{actor_reference}"


def _source_reference(inbound_source_record_id: int) -> str:
    return f"inbound_source_record:{inbound_source_record_id}"


def _observation_reference(inbound_observation_id: int) -> str:
    return f"inbound_observation:{inbound_observation_id}"


def _observation_identity_key(candidate: StructuredObservationCandidate) -> str:
    payload = json.dumps(candidate.candidate_value_payload, sort_keys=True, separators=(",", ":"))
    ambiguity = ",".join(candidate.ambiguity_flags)
    return (
        f"{candidate.reported_field_code}|{candidate.observation_type}|{candidate.claim_kind}|"
        f"{candidate.source_evidence_reference}|{payload}|{ambiguity}"
    )


def _values_differ(left: Any, right: Any) -> bool:
    return json.dumps(left, sort_keys=True, separators=(",", ":")) != json.dumps(
        right,
        sort_keys=True,
        separators=(",", ":"),
    )


def _stale_reason(stale_observation: bool) -> tuple[str, ...]:
    return ("stale_observation",) if stale_observation else ()


def _stale_failure(stale_observation: bool) -> tuple[str, ...]:
    return (OBSERVATION_FAILURE_STALE_OBSERVATION,) if stale_observation else ()
