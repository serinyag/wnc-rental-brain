from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from .contracts import APPROVAL_POSTURE_CODES, CHANGE_IMPACT_CODES, PHASE_8_WORKFLOW_CONTRACT_VERSION
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


SOURCE_SYSTEM_EMAIL = "email"
SOURCE_SYSTEM_MANUAL_INPUT = "manual_input"
SOURCE_SYSTEM_INTAKE_FORM = "intake_form"
SOURCE_SYSTEM_EXTERNAL_PLATFORM = "external_platform"
SOURCE_SYSTEM_CALL_SUMMARY = "call_summary"
SOURCE_SYSTEM_SITE_VISIT_SUMMARY = "site_visit_summary"
SOURCE_SYSTEM_SUPPLIER_COMMUNICATION = "supplier_communication"
SOURCE_SYSTEM_INTEGRATION_EVENT = "integration_event"

SOURCE_SYSTEM_CODES = frozenset(
    {
        SOURCE_SYSTEM_EMAIL,
        SOURCE_SYSTEM_MANUAL_INPUT,
        SOURCE_SYSTEM_INTAKE_FORM,
        SOURCE_SYSTEM_EXTERNAL_PLATFORM,
        SOURCE_SYSTEM_CALL_SUMMARY,
        SOURCE_SYSTEM_SITE_VISIT_SUMMARY,
        SOURCE_SYSTEM_SUPPLIER_COMMUNICATION,
        SOURCE_SYSTEM_INTEGRATION_EVENT,
    }
)

SOURCE_RECORD_TYPE_MESSAGE = "message"
SOURCE_RECORD_TYPE_FORM_SUBMISSION = "form_submission"
SOURCE_RECORD_TYPE_OPERATOR_NOTE = "operator_note"
SOURCE_RECORD_TYPE_CALL_SUMMARY = "call_summary"
SOURCE_RECORD_TYPE_SITE_VISIT_SUMMARY = "site_visit_summary"
SOURCE_RECORD_TYPE_PLATFORM_EVENT = "platform_event"
SOURCE_RECORD_TYPE_SUPPLIER_MESSAGE = "supplier_message"
SOURCE_RECORD_TYPE_INTEGRATION_EVENT = "integration_event"

SOURCE_RECORD_TYPE_CODES = frozenset(
    {
        SOURCE_RECORD_TYPE_MESSAGE,
        SOURCE_RECORD_TYPE_FORM_SUBMISSION,
        SOURCE_RECORD_TYPE_OPERATOR_NOTE,
        SOURCE_RECORD_TYPE_CALL_SUMMARY,
        SOURCE_RECORD_TYPE_SITE_VISIT_SUMMARY,
        SOURCE_RECORD_TYPE_PLATFORM_EVENT,
        SOURCE_RECORD_TYPE_SUPPLIER_MESSAGE,
        SOURCE_RECORD_TYPE_INTEGRATION_EVENT,
    }
)

SOURCE_ASSOCIATION_STATUS_RESOLVED = "resolved"
SOURCE_ASSOCIATION_STATUS_CASE_ASSOCIATION_REQUIRED = "case_association_required"
SOURCE_ASSOCIATION_STATUS_REJECTED = "rejected"

SOURCE_ASSOCIATION_STATUS_CODES = frozenset(
    {
        SOURCE_ASSOCIATION_STATUS_RESOLVED,
        SOURCE_ASSOCIATION_STATUS_CASE_ASSOCIATION_REQUIRED,
        SOURCE_ASSOCIATION_STATUS_REJECTED,
    }
)

OBSERVATION_TYPE_FACT_CANDIDATE = "fact_candidate"
OBSERVATION_TYPE_REQUEST_CANDIDATE = "request_candidate"
OBSERVATION_TYPE_CHANGE_CANDIDATE = "change_candidate"
OBSERVATION_TYPE_CONFIRMATION_CANDIDATE = "confirmation_candidate"
OBSERVATION_TYPE_CASE_DECISION_CANDIDATE = "case_decision_candidate"
OBSERVATION_TYPE_REQUIREMENT_EVIDENCE_CANDIDATE = "requirement_evidence_candidate"
OBSERVATION_TYPE_UNKNOWN_OR_UNMAPPED = "unknown_or_unmapped"

OBSERVATION_TYPE_CODES = frozenset(
    {
        OBSERVATION_TYPE_FACT_CANDIDATE,
        OBSERVATION_TYPE_REQUEST_CANDIDATE,
        OBSERVATION_TYPE_CHANGE_CANDIDATE,
        OBSERVATION_TYPE_CONFIRMATION_CANDIDATE,
        OBSERVATION_TYPE_CASE_DECISION_CANDIDATE,
        OBSERVATION_TYPE_REQUIREMENT_EVIDENCE_CANDIDATE,
        OBSERVATION_TYPE_UNKNOWN_OR_UNMAPPED,
    }
)

OBSERVATION_STATUS_CANDIDATE = "candidate"
OBSERVATION_STATUS_VALIDATED = "validated"
OBSERVATION_STATUS_REJECTED = "rejected"
OBSERVATION_STATUS_CONSUMED = "consumed"
OBSERVATION_STATUS_SUPERSEDED = "superseded"
OBSERVATION_STATUS_UNMAPPED = "unmapped"
OBSERVATION_STATUS_QUARANTINED = "quarantined"

OBSERVATION_STATUS_CODES = frozenset(
    {
        OBSERVATION_STATUS_CANDIDATE,
        OBSERVATION_STATUS_VALIDATED,
        OBSERVATION_STATUS_REJECTED,
        OBSERVATION_STATUS_CONSUMED,
        OBSERVATION_STATUS_SUPERSEDED,
        OBSERVATION_STATUS_UNMAPPED,
        OBSERVATION_STATUS_QUARANTINED,
    }
)

OBSERVATION_CLAIM_KIND_NEW_INFORMATION = "new_information"
OBSERVATION_CLAIM_KIND_CHANGE_REQUEST = "change_request"
OBSERVATION_CLAIM_KIND_EXCEPTION_REQUEST = "exception_request"
OBSERVATION_CLAIM_KIND_CONFIRMATION = "confirmation"
OBSERVATION_CLAIM_KIND_REQUIREMENT_EVIDENCE = "requirement_evidence"
OBSERVATION_CLAIM_KIND_QUESTION_ANSWER = "question_answer"
OBSERVATION_CLAIM_KIND_UNKNOWN = "unknown"

OBSERVATION_CLAIM_KIND_CODES = frozenset(
    {
        OBSERVATION_CLAIM_KIND_NEW_INFORMATION,
        OBSERVATION_CLAIM_KIND_CHANGE_REQUEST,
        OBSERVATION_CLAIM_KIND_EXCEPTION_REQUEST,
        OBSERVATION_CLAIM_KIND_CONFIRMATION,
        OBSERVATION_CLAIM_KIND_REQUIREMENT_EVIDENCE,
        OBSERVATION_CLAIM_KIND_QUESTION_ANSWER,
        OBSERVATION_CLAIM_KIND_UNKNOWN,
    }
)

OBSERVATION_ASSERTED_BY_CLIENT = "client"
OBSERVATION_ASSERTED_BY_WNC = "wnc"
OBSERVATION_ASSERTED_BY_EXTERNAL_SUPPLIER = "external_supplier"
OBSERVATION_ASSERTED_BY_OPERATOR = "operator"
OBSERVATION_ASSERTED_BY_SYSTEM = "system"
OBSERVATION_ASSERTED_BY_UNKNOWN = "unknown"

OBSERVATION_ASSERTED_BY_CODES = frozenset(
    {
        OBSERVATION_ASSERTED_BY_CLIENT,
        OBSERVATION_ASSERTED_BY_WNC,
        OBSERVATION_ASSERTED_BY_EXTERNAL_SUPPLIER,
        OBSERVATION_ASSERTED_BY_OPERATOR,
        OBSERVATION_ASSERTED_BY_SYSTEM,
        OBSERVATION_ASSERTED_BY_UNKNOWN,
    }
)

OBSERVATION_VALUE_TYPE_INTEGER = "integer"
OBSERVATION_VALUE_TYPE_TEXT = "text"
OBSERVATION_VALUE_TYPE_BOOLEAN = "boolean"
OBSERVATION_VALUE_TYPE_JSON_OBJECT = "json_object"
OBSERVATION_VALUE_TYPE_ENUM = "enum"
OBSERVATION_VALUE_TYPE_ENUM_ARRAY = "enum_array"

OBSERVATION_VALUE_TYPE_CODES = frozenset(
    {
        OBSERVATION_VALUE_TYPE_INTEGER,
        OBSERVATION_VALUE_TYPE_TEXT,
        OBSERVATION_VALUE_TYPE_BOOLEAN,
        OBSERVATION_VALUE_TYPE_JSON_OBJECT,
        OBSERVATION_VALUE_TYPE_ENUM,
        OBSERVATION_VALUE_TYPE_ENUM_ARRAY,
    }
)

OBSERVATION_TARGET_KIND_RENTAL_CASE_FACT = "rental_case_fact"
OBSERVATION_TARGET_KIND_RENTAL_CASE_SCHEDULE = "rental_case_schedule"
OBSERVATION_TARGET_KIND_CASE_DECISION = "case_decision"
OBSERVATION_TARGET_KIND_REQUIREMENT_EVIDENCE = "requirement_evidence"
OBSERVATION_TARGET_KIND_CONFIRMATION_EVIDENCE = "confirmation_evidence"

OBSERVATION_TARGET_KIND_CODES = frozenset(
    {
        OBSERVATION_TARGET_KIND_RENTAL_CASE_FACT,
        OBSERVATION_TARGET_KIND_RENTAL_CASE_SCHEDULE,
        OBSERVATION_TARGET_KIND_CASE_DECISION,
        OBSERVATION_TARGET_KIND_REQUIREMENT_EVIDENCE,
        OBSERVATION_TARGET_KIND_CONFIRMATION_EVIDENCE,
    }
)

OBSERVATION_DISPOSITION_NO_WORKFLOW_EFFECT = "no_workflow_effect"
OBSERVATION_DISPOSITION_OPEN_QUESTION_ANSWER_CANDIDATE = "open_question_answer_candidate"
OBSERVATION_DISPOSITION_CREATE_PROPOSED_CHANGE = "create_proposed_change"
OBSERVATION_DISPOSITION_CREATE_CASE_DECISION_CANDIDATE = "create_case_decision_candidate"
OBSERVATION_DISPOSITION_CREATE_RESCHEDULE_REQUEST = "create_reschedule_request"
OBSERVATION_DISPOSITION_RECORD_CONFIRMATION_CANDIDATE = "record_confirmation_candidate"
OBSERVATION_DISPOSITION_RECORD_REQUIREMENT_EVIDENCE_CANDIDATE = "record_requirement_evidence_candidate"
OBSERVATION_DISPOSITION_MANUAL_MAPPING_REQUIRED = "manual_mapping_required"
OBSERVATION_DISPOSITION_REJECT_QUARANTINE = "reject_quarantine"
OBSERVATION_DISPOSITION_CASE_ASSOCIATION_REQUIRED = "case_association_required"

OBSERVATION_DISPOSITION_CODES = frozenset(
    {
        OBSERVATION_DISPOSITION_NO_WORKFLOW_EFFECT,
        OBSERVATION_DISPOSITION_OPEN_QUESTION_ANSWER_CANDIDATE,
        OBSERVATION_DISPOSITION_CREATE_PROPOSED_CHANGE,
        OBSERVATION_DISPOSITION_CREATE_CASE_DECISION_CANDIDATE,
        OBSERVATION_DISPOSITION_CREATE_RESCHEDULE_REQUEST,
        OBSERVATION_DISPOSITION_RECORD_CONFIRMATION_CANDIDATE,
        OBSERVATION_DISPOSITION_RECORD_REQUIREMENT_EVIDENCE_CANDIDATE,
        OBSERVATION_DISPOSITION_MANUAL_MAPPING_REQUIRED,
        OBSERVATION_DISPOSITION_REJECT_QUARANTINE,
        OBSERVATION_DISPOSITION_CASE_ASSOCIATION_REQUIRED,
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
class ObservationFieldDefinition:
    field_code: str
    domain_code: str
    display_label: str
    value_type_code: str
    allowed_observation_types: tuple[str, ...]
    materiality_default: str | None
    client_input_allowed: bool
    human_validation_required: bool
    canonical_target_kind: str
    canonical_target_reference: str | None = None
    allowed_enum_values: tuple[str, ...] = ()
    related_open_question_types: tuple[str, ...] = ()
    related_requirement_types: tuple[str, ...] = ()
    default_review_posture: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        ensure_non_empty_text("field_code", self.field_code)
        ensure_non_empty_text("domain_code", self.domain_code)
        ensure_non_empty_text("display_label", self.display_label)
        ensure_allowed_value("value_type_code", self.value_type_code, OBSERVATION_VALUE_TYPE_CODES)
        ensure_tuple_of_non_empty_text("allowed_observation_types", self.allowed_observation_types)
        for code in self.allowed_observation_types:
            ensure_allowed_value("allowed_observation_types", code, OBSERVATION_TYPE_CODES)
        if self.materiality_default is not None:
            ensure_allowed_value("materiality_default", self.materiality_default, CHANGE_IMPACT_CODES)
        ensure_bool("client_input_allowed", self.client_input_allowed)
        ensure_bool("human_validation_required", self.human_validation_required)
        ensure_allowed_value("canonical_target_kind", self.canonical_target_kind, OBSERVATION_TARGET_KIND_CODES)
        ensure_optional_non_empty_text("canonical_target_reference", self.canonical_target_reference)
        ensure_tuple_of_non_empty_text("allowed_enum_values", self.allowed_enum_values)
        ensure_tuple_of_non_empty_text("related_open_question_types", self.related_open_question_types)
        ensure_tuple_of_non_empty_text("related_requirement_types", self.related_requirement_types)
        if self.default_review_posture is not None:
            ensure_allowed_value("default_review_posture", self.default_review_posture, APPROVAL_POSTURE_CODES)
        ensure_optional_non_empty_text("notes", self.notes)


@dataclass(frozen=True)
class RentalCaseFact:
    rental_case_fact_id: int
    rental_case_id: int
    field_code: str
    domain_code: str
    value_payload: Any
    source_reference: str
    established_case_revision: int
    created_at: str
    updated_at: str

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_fact_id", self.rental_case_fact_id)
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_non_empty_text("field_code", self.field_code)
        ensure_non_empty_text("domain_code", self.domain_code)
        ensure_json_compatible("value_payload", self.value_payload)
        ensure_non_empty_text("source_reference", self.source_reference)
        ensure_non_negative_int("established_case_revision", self.established_case_revision)
        ensure_non_empty_text("created_at", self.created_at)
        ensure_non_empty_text("updated_at", self.updated_at)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


@dataclass(frozen=True)
class InboundSourceRecord:
    inbound_source_record_id: int
    source_system_code: str
    source_record_type: str
    dedupe_key: str
    source_hash: str
    occurred_at: str
    association_status: str
    created_at: str
    external_source_id: str | None = None
    conversation_reference: str | None = None
    sender_actor_type: str | None = None
    sender_actor_reference: str | None = None
    case_reference_hint: str | None = None
    resolved_rental_case_id: int | None = None
    association_basis: str | None = None
    received_at: str | None = None
    source_location_reference: str | None = None
    confidentiality_posture: str | None = None
    pi_posture: str | None = None
    evidence_excerpt: str | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("inbound_source_record_id", self.inbound_source_record_id)
        ensure_allowed_value("source_system_code", self.source_system_code, SOURCE_SYSTEM_CODES)
        ensure_allowed_value("source_record_type", self.source_record_type, SOURCE_RECORD_TYPE_CODES)
        ensure_non_empty_text("dedupe_key", self.dedupe_key)
        ensure_non_empty_text("source_hash", self.source_hash)
        ensure_non_empty_text("occurred_at", self.occurred_at)
        ensure_allowed_value("association_status", self.association_status, SOURCE_ASSOCIATION_STATUS_CODES)
        ensure_non_empty_text("created_at", self.created_at)
        ensure_optional_non_empty_text("external_source_id", self.external_source_id)
        ensure_optional_non_empty_text("conversation_reference", self.conversation_reference)
        if self.sender_actor_type is not None:
            ensure_allowed_value("sender_actor_type", self.sender_actor_type, OBSERVATION_ASSERTED_BY_CODES)
        ensure_optional_non_empty_text("sender_actor_reference", self.sender_actor_reference)
        ensure_optional_non_empty_text("case_reference_hint", self.case_reference_hint)
        ensure_optional_positive_int("resolved_rental_case_id", self.resolved_rental_case_id)
        ensure_optional_non_empty_text("association_basis", self.association_basis)
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
        if self.association_status == SOURCE_ASSOCIATION_STATUS_RESOLVED and self.resolved_rental_case_id is None:
            raise Phase8ContractError(
                error_category="missing_value",
                safe_message="resolved inbound sources require resolved_rental_case_id.",
            )
        if self.association_status != SOURCE_ASSOCIATION_STATUS_RESOLVED and self.resolved_rental_case_id is not None:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="non-resolved inbound sources may not include resolved_rental_case_id.",
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


@dataclass(frozen=True)
class InboundObservation:
    inbound_observation_id: int
    inbound_source_record_id: int
    reported_field_code: str
    observation_type: str
    claim_kind: str
    candidate_value_payload: Any
    source_evidence_reference: str
    status: str
    observation_identity_key: str
    created_at: str
    reported_domain_code: str | None = None
    target_field_code: str | None = None
    target_domain_code: str | None = None
    rental_case_id: int | None = None
    asserted_by_party_type: str | None = None
    asserted_by_reference: str | None = None
    source_excerpt: str | None = None
    observed_against_case_revision: int | None = None
    extraction_confidence: float | None = None
    ambiguity_flags: tuple[str, ...] = ()
    supersedes_inbound_observation_id: int | None = None
    updated_at: str | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("inbound_observation_id", self.inbound_observation_id)
        ensure_positive_int("inbound_source_record_id", self.inbound_source_record_id)
        ensure_non_empty_text("reported_field_code", self.reported_field_code)
        ensure_allowed_value("observation_type", self.observation_type, OBSERVATION_TYPE_CODES)
        ensure_allowed_value("claim_kind", self.claim_kind, OBSERVATION_CLAIM_KIND_CODES)
        ensure_json_compatible("candidate_value_payload", self.candidate_value_payload)
        ensure_non_empty_text("source_evidence_reference", self.source_evidence_reference)
        ensure_allowed_value("status", self.status, OBSERVATION_STATUS_CODES)
        ensure_non_empty_text("observation_identity_key", self.observation_identity_key)
        ensure_non_empty_text("created_at", self.created_at)
        ensure_optional_non_empty_text("reported_domain_code", self.reported_domain_code)
        ensure_optional_non_empty_text("target_field_code", self.target_field_code)
        ensure_optional_non_empty_text("target_domain_code", self.target_domain_code)
        if (self.target_field_code is None) != (self.target_domain_code is None):
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="target_field_code and target_domain_code must both be set or both be null.",
            )
        ensure_optional_positive_int("rental_case_id", self.rental_case_id)
        if self.asserted_by_party_type is not None:
            ensure_allowed_value("asserted_by_party_type", self.asserted_by_party_type, OBSERVATION_ASSERTED_BY_CODES)
        ensure_optional_non_empty_text("asserted_by_reference", self.asserted_by_reference)
        ensure_optional_non_empty_text("source_excerpt", self.source_excerpt)
        if self.source_excerpt is not None and len(self.source_excerpt) > 500:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="source_excerpt may not exceed 500 characters.",
            )
        ensure_optional_non_negative_int("observed_against_case_revision", self.observed_against_case_revision)
        _ensure_optional_confidence("extraction_confidence", self.extraction_confidence)
        ensure_tuple_of_non_empty_text("ambiguity_flags", self.ambiguity_flags)
        ensure_optional_positive_int("supersedes_inbound_observation_id", self.supersedes_inbound_observation_id)
        ensure_optional_non_empty_text("updated_at", self.updated_at)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


@dataclass(frozen=True)
class InboundObservationEffect:
    inbound_observation_effect_id: int
    inbound_observation_id: int
    rental_case_id: int | None
    disposition_code: str
    revalidation_required: bool
    stale_observation: bool
    reason_codes: tuple[str, ...]
    created_at: str
    linked_open_question_id: int | None = None
    linked_requirement_id: int | None = None
    linked_proposed_change_id: int | None = None
    linked_case_decision_id: int | None = None
    linked_reschedule_request_id: int | None = None
    workflow_event_id: int | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("inbound_observation_effect_id", self.inbound_observation_effect_id)
        ensure_positive_int("inbound_observation_id", self.inbound_observation_id)
        ensure_optional_positive_int("rental_case_id", self.rental_case_id)
        ensure_allowed_value("disposition_code", self.disposition_code, OBSERVATION_DISPOSITION_CODES)
        ensure_bool("revalidation_required", self.revalidation_required)
        ensure_bool("stale_observation", self.stale_observation)
        ensure_tuple_of_non_empty_text("reason_codes", self.reason_codes)
        ensure_non_empty_text("created_at", self.created_at)
        ensure_optional_positive_int("linked_open_question_id", self.linked_open_question_id)
        ensure_optional_positive_int("linked_requirement_id", self.linked_requirement_id)
        ensure_optional_positive_int("linked_proposed_change_id", self.linked_proposed_change_id)
        ensure_optional_positive_int("linked_case_decision_id", self.linked_case_decision_id)
        ensure_optional_positive_int("linked_reschedule_request_id", self.linked_reschedule_request_id)
        ensure_optional_positive_int("workflow_event_id", self.workflow_event_id)
        link_count = sum(
            1
            for value in (
                self.linked_open_question_id,
                self.linked_requirement_id,
                self.linked_proposed_change_id,
                self.linked_case_decision_id,
                self.linked_reschedule_request_id,
            )
            if value is not None
        )
        if link_count > 1:
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="InboundObservationEffect may reference at most one workflow target entity.",
            )
        required_target_field = {
            OBSERVATION_DISPOSITION_OPEN_QUESTION_ANSWER_CANDIDATE: self.linked_open_question_id,
            OBSERVATION_DISPOSITION_CREATE_PROPOSED_CHANGE: self.linked_proposed_change_id,
            OBSERVATION_DISPOSITION_CREATE_CASE_DECISION_CANDIDATE: self.linked_case_decision_id,
            OBSERVATION_DISPOSITION_CREATE_RESCHEDULE_REQUEST: self.linked_reschedule_request_id,
            OBSERVATION_DISPOSITION_RECORD_REQUIREMENT_EVIDENCE_CANDIDATE: self.linked_requirement_id,
        }.get(self.disposition_code)
        if self.disposition_code in {
            OBSERVATION_DISPOSITION_OPEN_QUESTION_ANSWER_CANDIDATE,
            OBSERVATION_DISPOSITION_CREATE_PROPOSED_CHANGE,
            OBSERVATION_DISPOSITION_CREATE_CASE_DECISION_CANDIDATE,
            OBSERVATION_DISPOSITION_CREATE_RESCHEDULE_REQUEST,
            OBSERVATION_DISPOSITION_RECORD_REQUIREMENT_EVIDENCE_CANDIDATE,
        } and required_target_field is None:
            raise Phase8ContractError(
                error_category="missing_value",
                safe_message=f"{self.disposition_code} effects require a linked target entity id.",
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)
