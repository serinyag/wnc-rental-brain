from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .contracts import CHANGE_IMPACT_CODES, PHASE_8_WORKFLOW_CONTRACT_VERSION, RESCHEDULE_URGENCY_CODES
from .observation_contracts import (
    InboundObservation,
    InboundObservationEffect,
    InboundSourceRecord,
    OBSERVATION_ASSERTED_BY_CODES,
    OBSERVATION_CLAIM_KIND_CODES,
    OBSERVATION_DISPOSITION_CODES,
    OBSERVATION_STATUS_CODES,
    OBSERVATION_TYPE_CODES,
    SOURCE_ASSOCIATION_STATUS_CODES,
    SOURCE_RECORD_TYPE_CODES,
    SOURCE_SYSTEM_CODES,
)
from .validation import (
    Phase8ContractError,
    ensure_at_least_one_present,
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


OBSERVATION_FAILURE_SOURCE_DUPLICATE = "source_duplicate"
OBSERVATION_FAILURE_OBSERVATION_DUPLICATE = "observation_duplicate"
OBSERVATION_FAILURE_CASE_ASSOCIATION_REQUIRED = "case_association_required"
OBSERVATION_FAILURE_CASE_NOT_FOUND = "case_not_found"
OBSERVATION_FAILURE_UNKNOWN_FIELD = "unknown_field"
OBSERVATION_FAILURE_INVALID_VALUE_TYPE = "invalid_value_type"
OBSERVATION_FAILURE_CROSS_CASE_REFERENCE = "cross_case_reference"
OBSERVATION_FAILURE_INVALID_OBSERVATION_TYPE = "invalid_observation_type"
OBSERVATION_FAILURE_STALE_OBSERVATION = "stale_observation"
OBSERVATION_FAILURE_MANUAL_MAPPING_REQUIRED = "manual_mapping_required"
OBSERVATION_FAILURE_UNSUPPORTED_DISPOSITION = "unsupported_disposition"
OBSERVATION_FAILURE_PERSISTENCE_FAILURE = "persistence_failure"

OBSERVATION_FAILURE_CODES = frozenset(
    {
        OBSERVATION_FAILURE_SOURCE_DUPLICATE,
        OBSERVATION_FAILURE_OBSERVATION_DUPLICATE,
        OBSERVATION_FAILURE_CASE_ASSOCIATION_REQUIRED,
        OBSERVATION_FAILURE_CASE_NOT_FOUND,
        OBSERVATION_FAILURE_UNKNOWN_FIELD,
        OBSERVATION_FAILURE_INVALID_VALUE_TYPE,
        OBSERVATION_FAILURE_CROSS_CASE_REFERENCE,
        OBSERVATION_FAILURE_INVALID_OBSERVATION_TYPE,
        OBSERVATION_FAILURE_STALE_OBSERVATION,
        OBSERVATION_FAILURE_MANUAL_MAPPING_REQUIRED,
        OBSERVATION_FAILURE_UNSUPPORTED_DISPOSITION,
        OBSERVATION_FAILURE_PERSISTENCE_FAILURE,
    }
)


def _ensure_optional_confidence(field_name: str, value: float | int | None) -> None:
    if value is None:
        return
    if not isinstance(value, (int, float)) or value < 0 or value > 1:
        raise Phase8ContractError(
            error_category="invalid_value",
            safe_message=f"{field_name} must be between 0 and 1 when provided.",
        )


@dataclass(frozen=True)
class InboundSourceRecordInput:
    source_system_code: str
    source_record_type: str
    occurred_at: str
    dedupe_key: str
    source_hash: str
    external_source_id: str | None = None
    conversation_reference: str | None = None
    sender_actor_type: str | None = None
    sender_actor_reference: str | None = None
    case_reference_hint: str | None = None
    received_at: str | None = None
    source_location_reference: str | None = None
    confidentiality_posture: str | None = None
    pi_posture: str | None = None
    evidence_excerpt: str | None = None

    def __post_init__(self) -> None:
        if self.source_system_code not in SOURCE_SYSTEM_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="source_system_code must be one of the supported provider-neutral source systems.",
            )
        if self.source_record_type not in SOURCE_RECORD_TYPE_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="source_record_type must be one of the supported provider-neutral record types.",
            )
        ensure_non_empty_text("occurred_at", self.occurred_at)
        ensure_non_empty_text("dedupe_key", self.dedupe_key)
        ensure_non_empty_text("source_hash", self.source_hash)
        ensure_optional_non_empty_text("external_source_id", self.external_source_id)
        ensure_optional_non_empty_text("conversation_reference", self.conversation_reference)
        if self.sender_actor_type is not None and self.sender_actor_type not in OBSERVATION_ASSERTED_BY_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="sender_actor_type must be a supported asserted-by party type when provided.",
            )
        ensure_optional_non_empty_text("sender_actor_reference", self.sender_actor_reference)
        ensure_optional_non_empty_text("case_reference_hint", self.case_reference_hint)
        ensure_optional_non_empty_text("received_at", self.received_at)
        ensure_optional_non_empty_text("source_location_reference", self.source_location_reference)
        ensure_optional_non_empty_text("confidentiality_posture", self.confidentiality_posture)
        ensure_optional_non_empty_text("pi_posture", self.pi_posture)
        ensure_optional_non_empty_text("evidence_excerpt", self.evidence_excerpt)
        if self.evidence_excerpt is not None and len(self.evidence_excerpt) > 500:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="evidence_excerpt may not exceed 500 characters.",
            )
        ensure_at_least_one_present("source_identity", (self.external_source_id, self.source_hash))


@dataclass(frozen=True)
class CaseAssociationInput:
    rental_case_id: int | None = None
    case_reference_code: str | None = None
    association_basis_hint: str | None = None

    def __post_init__(self) -> None:
        ensure_optional_positive_int("rental_case_id", self.rental_case_id)
        ensure_optional_non_empty_text("case_reference_code", self.case_reference_code)
        ensure_optional_non_empty_text("association_basis_hint", self.association_basis_hint)


@dataclass(frozen=True)
class StructuredObservationCandidate:
    reported_field_code: str
    observation_type: str
    claim_kind: str
    candidate_value_payload: Any
    source_evidence_reference: str
    reported_domain_code: str | None = None
    asserted_by_party_type: str | None = None
    asserted_by_reference: str | None = None
    source_excerpt: str | None = None
    extraction_confidence: float | None = None
    ambiguity_flags: tuple[str, ...] = ()
    observed_against_case_revision: int | None = None
    impact_classification: str | None = None
    requested_urgency_class: str | None = None

    def __post_init__(self) -> None:
        ensure_non_empty_text("reported_field_code", self.reported_field_code)
        if self.observation_type not in OBSERVATION_TYPE_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="observation_type must be one of the supported observation types.",
            )
        if self.claim_kind not in OBSERVATION_CLAIM_KIND_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="claim_kind must be one of the supported observation claim kinds.",
            )
        ensure_json_compatible("candidate_value_payload", self.candidate_value_payload)
        ensure_non_empty_text("source_evidence_reference", self.source_evidence_reference)
        ensure_optional_non_empty_text("reported_domain_code", self.reported_domain_code)
        if self.asserted_by_party_type is not None and self.asserted_by_party_type not in OBSERVATION_ASSERTED_BY_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="asserted_by_party_type must be a supported party type when provided.",
            )
        ensure_optional_non_empty_text("asserted_by_reference", self.asserted_by_reference)
        ensure_optional_non_empty_text("source_excerpt", self.source_excerpt)
        if self.source_excerpt is not None and len(self.source_excerpt) > 500:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="source_excerpt may not exceed 500 characters.",
            )
        _ensure_optional_confidence("extraction_confidence", self.extraction_confidence)
        ensure_tuple_of_non_empty_text("ambiguity_flags", self.ambiguity_flags)
        ensure_optional_non_negative_int("observed_against_case_revision", self.observed_against_case_revision)
        if self.impact_classification is not None and self.impact_classification not in CHANGE_IMPACT_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="impact_classification must be a supported change impact when provided.",
            )
        if self.requested_urgency_class is not None and self.requested_urgency_class not in RESCHEDULE_URGENCY_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="requested_urgency_class must be a supported reschedule urgency when provided.",
            )


@dataclass(frozen=True)
class StructuredObservationIngestionRequest:
    source_record: InboundSourceRecordInput
    observations: tuple[StructuredObservationCandidate, ...]
    case_association: CaseAssociationInput = field(default_factory=CaseAssociationInput)

    def __post_init__(self) -> None:
        if not isinstance(self.source_record, InboundSourceRecordInput):
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="source_record must be an InboundSourceRecordInput.",
            )
        if not isinstance(self.observations, tuple) or not self.observations:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="observations must be a non-empty tuple of StructuredObservationCandidate values.",
            )
        for index, candidate in enumerate(self.observations):
            if not isinstance(candidate, StructuredObservationCandidate):
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"observations[{index}] must be a StructuredObservationCandidate.",
                )
        if not isinstance(self.case_association, CaseAssociationInput):
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="case_association must be a CaseAssociationInput.",
            )


@dataclass(frozen=True)
class CaseAssociationResult:
    status: str
    failure_codes: tuple[str, ...] = ()
    rental_case_id: int | None = None
    case_reference_code: str | None = None
    observed_case_revision: int | None = None
    association_basis: str | None = None

    def __post_init__(self) -> None:
        if self.status not in SOURCE_ASSOCIATION_STATUS_CODES:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="status must be one of the supported source association statuses.",
            )
        ensure_tuple_of_non_empty_text("failure_codes", self.failure_codes)
        for code in self.failure_codes:
            if code not in OBSERVATION_FAILURE_CODES:
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"failure_codes contains unsupported code: {code}.",
                )
        ensure_optional_positive_int("rental_case_id", self.rental_case_id)
        ensure_optional_non_empty_text("case_reference_code", self.case_reference_code)
        ensure_optional_non_negative_int("observed_case_revision", self.observed_case_revision)
        ensure_optional_non_empty_text("association_basis", self.association_basis)
        if self.status == "resolved" and self.rental_case_id is None:
            raise Phase8ContractError(
                error_category="missing_value",
                safe_message="resolved case associations require rental_case_id.",
            )


@dataclass(frozen=True)
class ObservationDispositionResult:
    observation: InboundObservation
    effect: InboundObservationEffect
    failure_codes: tuple[str, ...] = ()
    linked_proposed_change_id: int | None = None
    linked_case_decision_id: int | None = None
    linked_reschedule_request_id: int | None = None
    linked_open_question_id: int | None = None
    linked_requirement_id: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.observation, InboundObservation):
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="observation must be an InboundObservation.",
            )
        if not isinstance(self.effect, InboundObservationEffect):
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="effect must be an InboundObservationEffect.",
            )
        ensure_tuple_of_non_empty_text("failure_codes", self.failure_codes)
        for code in self.failure_codes:
            if code not in OBSERVATION_FAILURE_CODES:
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"failure_codes contains unsupported code: {code}.",
                )
        ensure_optional_positive_int("linked_proposed_change_id", self.linked_proposed_change_id)
        ensure_optional_positive_int("linked_case_decision_id", self.linked_case_decision_id)
        ensure_optional_positive_int("linked_reschedule_request_id", self.linked_reschedule_request_id)
        ensure_optional_positive_int("linked_open_question_id", self.linked_open_question_id)
        ensure_optional_positive_int("linked_requirement_id", self.linked_requirement_id)


@dataclass(frozen=True)
class ObservationIngestionResult:
    contract_version: int = PHASE_8_WORKFLOW_CONTRACT_VERSION
    duplicate_source: bool = False
    source_record: InboundSourceRecord | None = None
    case_association: CaseAssociationResult | None = None
    observation_results: tuple[ObservationDispositionResult, ...] = ()
    failure_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ensure_positive_int("contract_version", self.contract_version)
        ensure_bool("duplicate_source", self.duplicate_source)
        if self.source_record is not None and not isinstance(self.source_record, InboundSourceRecord):
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="source_record must be an InboundSourceRecord when provided.",
            )
        if self.case_association is not None and not isinstance(self.case_association, CaseAssociationResult):
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="case_association must be a CaseAssociationResult when provided.",
            )
        if not isinstance(self.observation_results, tuple):
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="observation_results must be a tuple of ObservationDispositionResult values.",
            )
        for index, result in enumerate(self.observation_results):
            if not isinstance(result, ObservationDispositionResult):
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"observation_results[{index}] must be an ObservationDispositionResult.",
                )
        ensure_tuple_of_non_empty_text("failure_codes", self.failure_codes)
        for code in self.failure_codes:
            if code not in OBSERVATION_FAILURE_CODES:
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"failure_codes contains unsupported code: {code}.",
                )
