from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Protocol

from .contracts import OpenQuestion, WorkflowAction
from .observation_contracts import RentalCaseFact
from .validation import (
    Phase8ContractError,
    ensure_allowed_value,
    ensure_bool,
    ensure_json_compatible,
    ensure_non_empty_text,
    ensure_optional_non_empty_text,
    ensure_optional_positive_int,
    ensure_positive_int,
    ensure_tuple_of_non_empty_text,
    ensure_tuple_of_positive_ints,
)


INQUIRY_DRAFT_STATUS_DRAFT = "draft"
INQUIRY_DRAFT_STATUS_NEEDS_APPROVAL = "needs_approval"
INQUIRY_DRAFT_STATUS_APPROVED = "approved"
INQUIRY_DRAFT_STATUS_REJECTED = "rejected"
INQUIRY_DRAFT_STATUS_SIMULATED_SENT = "simulated_sent"
INQUIRY_DRAFT_STATUS_SEND_FAILED = "send_failed"
INQUIRY_DRAFT_STATUS_SEND_OUTCOME_UNCERTAIN = "send_outcome_uncertain"
INQUIRY_DRAFT_STATUS_STALE = "stale"

INQUIRY_DRAFT_PERSISTED_STATUSES = frozenset(
    {
        INQUIRY_DRAFT_STATUS_DRAFT,
        INQUIRY_DRAFT_STATUS_NEEDS_APPROVAL,
        INQUIRY_DRAFT_STATUS_APPROVED,
        INQUIRY_DRAFT_STATUS_REJECTED,
        INQUIRY_DRAFT_STATUS_SIMULATED_SENT,
        INQUIRY_DRAFT_STATUS_SEND_FAILED,
        INQUIRY_DRAFT_STATUS_SEND_OUTCOME_UNCERTAIN,
    }
)

INQUIRY_DRAFT_SOURCE_GENERATED = "generated"
INQUIRY_DRAFT_SOURCE_REGENERATED = "regenerated"
INQUIRY_DRAFT_SOURCE_HUMAN_EDITED = "human_edited"

INQUIRY_DRAFT_SOURCE_CODES = frozenset(
    {
        INQUIRY_DRAFT_SOURCE_GENERATED,
        INQUIRY_DRAFT_SOURCE_REGENERATED,
        INQUIRY_DRAFT_SOURCE_HUMAN_EDITED,
    }
)

GUIDANCE_REFERENCE_WF_003 = "WF-003"
GUIDANCE_REFERENCE_WF_004 = "WF-004"
DEFAULT_GUIDANCE_REFERENCES = (GUIDANCE_REFERENCE_WF_003, GUIDANCE_REFERENCE_WF_004)


@dataclass(frozen=True)
class InquiryResponseQuestionLine:
    open_question_id: int
    question_type: str
    human_question_text: str
    prompt_text: str

    def __post_init__(self) -> None:
        ensure_positive_int("open_question_id", self.open_question_id)
        ensure_non_empty_text("question_type", self.question_type)
        ensure_non_empty_text("human_question_text", self.human_question_text)
        ensure_non_empty_text("prompt_text", self.prompt_text)


@dataclass(frozen=True)
class InquiryResponseDraftContent:
    subject: str
    salutation: str
    intro_text: str
    question_lines: tuple[InquiryResponseQuestionLine, ...]
    closing_text: str
    signoff_text: str

    def __post_init__(self) -> None:
        ensure_non_empty_text("subject", self.subject)
        ensure_non_empty_text("salutation", self.salutation)
        ensure_non_empty_text("intro_text", self.intro_text)
        if not isinstance(self.question_lines, tuple) or not self.question_lines:
            raise Phase8ContractError(
                error_category="missing_value",
                safe_message="question_lines must contain at least one inquiry question.",
            )
        for index, line in enumerate(self.question_lines):
            if not isinstance(line, InquiryResponseQuestionLine):
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"question_lines[{index}] must be an InquiryResponseQuestionLine.",
                )
        ensure_non_empty_text("closing_text", self.closing_text)
        ensure_non_empty_text("signoff_text", self.signoff_text)

    @property
    def covered_question_ids(self) -> tuple[int, ...]:
        return tuple(line.open_question_id for line in self.question_lines)

    def to_payload(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "salutation": self.salutation,
            "intro_text": self.intro_text,
            "question_lines": [
                {
                    "open_question_id": line.open_question_id,
                    "question_type": line.question_type,
                    "human_question_text": line.human_question_text,
                    "prompt_text": line.prompt_text,
                }
                for line in self.question_lines
            ],
            "closing_text": self.closing_text,
            "signoff_text": self.signoff_text,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> InquiryResponseDraftContent:
        if not isinstance(payload, dict):
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="draft content payload must be an object.",
            )
        question_lines_payload = payload.get("question_lines")
        if not isinstance(question_lines_payload, list):
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message="draft content payload must include question_lines.",
            )
        return cls(
            subject=str(payload.get("subject") or ""),
            salutation=str(payload.get("salutation") or ""),
            intro_text=str(payload.get("intro_text") or ""),
            question_lines=tuple(
                InquiryResponseQuestionLine(
                    open_question_id=int(line.get("open_question_id")),
                    question_type=str(line.get("question_type") or ""),
                    human_question_text=str(line.get("human_question_text") or ""),
                    prompt_text=str(line.get("prompt_text") or ""),
                )
                for line in question_lines_payload
                if isinstance(line, dict)
            ),
            closing_text=str(payload.get("closing_text") or ""),
            signoff_text=str(payload.get("signoff_text") or ""),
        )


@dataclass(frozen=True)
class InquiryResponseDraftContext:
    rental_case_id: int
    workflow_action_id: int
    conversation_key: str
    source_case_revision: int
    contact_label: str | None
    recipient_email: str
    recipient_label: str | None
    sender_email: str
    sender_label: str
    open_questions: tuple[OpenQuestion, ...]
    current_facts: tuple[RentalCaseFact, ...] = ()
    guidance_references: tuple[str, ...] = DEFAULT_GUIDANCE_REFERENCES
    workflow_action: WorkflowAction | None = None
    metadata_summary_lines: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_positive_int("workflow_action_id", self.workflow_action_id)
        ensure_non_empty_text("conversation_key", self.conversation_key)
        ensure_non_empty_text("recipient_email", self.recipient_email)
        ensure_non_empty_text("sender_email", self.sender_email)
        ensure_non_empty_text("sender_label", self.sender_label)
        ensure_tuple_of_non_empty_text("guidance_references", self.guidance_references)
        ensure_tuple_of_non_empty_text("metadata_summary_lines", self.metadata_summary_lines)
        if not isinstance(self.open_questions, tuple) or not self.open_questions:
            raise Phase8ContractError(
                error_category="missing_value",
                safe_message="open_questions must contain at least one unresolved client question.",
            )
        for index, question in enumerate(self.open_questions):
            if not isinstance(question, OpenQuestion):
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"open_questions[{index}] must be an OpenQuestion.",
                )
        for index, fact in enumerate(self.current_facts):
            if not isinstance(fact, RentalCaseFact):
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"current_facts[{index}] must be a RentalCaseFact.",
                )

    @property
    def covered_question_ids(self) -> tuple[int, ...]:
        return tuple(question.open_question_id for question in self.open_questions)

    def to_payload(self) -> dict[str, Any]:
        return {
            "rental_case_id": self.rental_case_id,
            "workflow_action_id": self.workflow_action_id,
            "conversation_key": self.conversation_key,
            "source_case_revision": self.source_case_revision,
            "contact_label": self.contact_label,
            "recipient_email": self.recipient_email,
            "recipient_label": self.recipient_label,
            "sender_email": self.sender_email,
            "sender_label": self.sender_label,
            "guidance_references": list(self.guidance_references),
            "metadata_summary_lines": list(self.metadata_summary_lines),
            "open_questions": [
                {
                    "open_question_id": question.open_question_id,
                    "question_type": question.question_type,
                    "human_question_text": question.human_question_text,
                }
                for question in self.open_questions
            ],
            "current_facts": [
                {
                    "field_code": fact.field_code,
                    "domain_code": fact.domain_code,
                    "value_payload": fact.value_payload,
                }
                for fact in self.current_facts
            ],
        }


@dataclass(frozen=True)
class InquiryResponseDraftRevision:
    inquiry_response_draft_revision_id: int
    inquiry_response_draft_revision_uuid: str
    rental_case_id: int
    workflow_action_id: int
    conversation_key: str
    source_case_revision: int
    draft_status: str
    draft_source: str
    is_current: bool
    subject: str
    salutation: str
    intro_text: str
    question_lines: tuple[InquiryResponseQuestionLine, ...]
    closing_text: str
    signoff_text: str
    body_text: str
    context_payload: dict[str, Any]
    context_hash: str
    content_hash: str
    recipient_email: str
    sender_email: str
    sender_label: str
    created_by_reference: str
    created_at: str
    updated_at: str
    recipient_label: str | None = None
    approval_request_id: int | None = None
    sender_display_name: str | None = None
    supersedes_draft_revision_id: int | None = None
    delivered_at: str | None = None
    delivery_external_reference: str | None = None
    delivery_failure_code: str | None = None
    approved_at: str | None = None
    rejected_at: str | None = None

    def __post_init__(self) -> None:
        ensure_positive_int("inquiry_response_draft_revision_id", self.inquiry_response_draft_revision_id)
        ensure_non_empty_text("inquiry_response_draft_revision_uuid", self.inquiry_response_draft_revision_uuid)
        ensure_positive_int("rental_case_id", self.rental_case_id)
        ensure_positive_int("workflow_action_id", self.workflow_action_id)
        ensure_non_empty_text("conversation_key", self.conversation_key)
        ensure_allowed_value("draft_status", self.draft_status, INQUIRY_DRAFT_PERSISTED_STATUSES)
        ensure_allowed_value("draft_source", self.draft_source, INQUIRY_DRAFT_SOURCE_CODES)
        ensure_bool("is_current", self.is_current)
        ensure_non_empty_text("subject", self.subject)
        ensure_non_empty_text("salutation", self.salutation)
        ensure_non_empty_text("intro_text", self.intro_text)
        if not isinstance(self.question_lines, tuple) or not self.question_lines:
            raise Phase8ContractError(
                error_category="missing_value",
                safe_message="question_lines must contain at least one inquiry question.",
            )
        ensure_non_empty_text("closing_text", self.closing_text)
        ensure_non_empty_text("signoff_text", self.signoff_text)
        ensure_non_empty_text("body_text", self.body_text)
        ensure_json_compatible("context_payload", self.context_payload)
        ensure_non_empty_text("context_hash", self.context_hash)
        ensure_non_empty_text("content_hash", self.content_hash)
        ensure_non_empty_text("recipient_email", self.recipient_email)
        ensure_non_empty_text("sender_email", self.sender_email)
        ensure_non_empty_text("sender_label", self.sender_label)
        ensure_non_empty_text("created_by_reference", self.created_by_reference)
        ensure_non_empty_text("created_at", self.created_at)
        ensure_non_empty_text("updated_at", self.updated_at)
        ensure_optional_non_empty_text("recipient_label", self.recipient_label)
        ensure_optional_positive_int("approval_request_id", self.approval_request_id)
        ensure_optional_non_empty_text("sender_display_name", self.sender_display_name)
        ensure_optional_positive_int("supersedes_draft_revision_id", self.supersedes_draft_revision_id)
        ensure_optional_non_empty_text("delivered_at", self.delivered_at)
        ensure_optional_non_empty_text("delivery_external_reference", self.delivery_external_reference)
        ensure_optional_non_empty_text("delivery_failure_code", self.delivery_failure_code)
        ensure_optional_non_empty_text("approved_at", self.approved_at)
        ensure_optional_non_empty_text("rejected_at", self.rejected_at)

    @property
    def covered_question_ids(self) -> tuple[int, ...]:
        return tuple(line.open_question_id for line in self.question_lines)

    @property
    def content(self) -> InquiryResponseDraftContent:
        return InquiryResponseDraftContent(
            subject=self.subject,
            salutation=self.salutation,
            intro_text=self.intro_text,
            question_lines=self.question_lines,
            closing_text=self.closing_text,
            signoff_text=self.signoff_text,
        )

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> InquiryResponseDraftRevision:
        question_lines_payload = row.get("question_lines") or []
        return cls(
            inquiry_response_draft_revision_id=row["inquiry_response_draft_revision_id"],
            inquiry_response_draft_revision_uuid=row["inquiry_response_draft_revision_uuid"],
            rental_case_id=row["rental_case_id"],
            workflow_action_id=row["workflow_action_id"],
            conversation_key=row["conversation_key"],
            source_case_revision=row["source_case_revision"],
            draft_status=row["draft_status"],
            draft_source=row["draft_source"],
            is_current=bool(row["is_current"]),
            subject=row["subject"],
            salutation=row["salutation"],
            intro_text=row["intro_text"],
            question_lines=tuple(
                InquiryResponseQuestionLine(
                    open_question_id=item["open_question_id"],
                    question_type=item["question_type"],
                    human_question_text=item["human_question_text"],
                    prompt_text=item["prompt_text"],
                )
                for item in question_lines_payload
            ),
            closing_text=row["closing_text"],
            signoff_text=row["signoff_text"],
            body_text=row["body_text"],
            context_payload=row.get("context_payload") or {},
            context_hash=row["context_hash"],
            content_hash=row["content_hash"],
            recipient_email=row["recipient_email"],
            sender_email=row["sender_email"],
            sender_label=row["sender_label"],
            created_by_reference=row["created_by_reference"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            recipient_label=row.get("recipient_label"),
            approval_request_id=row.get("approval_request_id"),
            sender_display_name=row.get("sender_display_name"),
            supersedes_draft_revision_id=row.get("supersedes_draft_revision_id"),
            delivered_at=row.get("delivered_at"),
            delivery_external_reference=row.get("delivery_external_reference"),
            delivery_failure_code=row.get("delivery_failure_code"),
            approved_at=row.get("approved_at"),
            rejected_at=row.get("rejected_at"),
        )


class InquiryResponseDraftGenerator(Protocol):
    def generate(self, context: InquiryResponseDraftContext) -> InquiryResponseDraftContent: ...


@dataclass
class DeterministicInquiryResponseDraftGenerator:
    sender_signoff: str = "Warmly,\nWNC"

    def generate(self, context: InquiryResponseDraftContext) -> InquiryResponseDraftContent:
        subject = _build_subject(context)
        salutation = _build_salutation(context)
        intro_text = _build_intro_text(context)
        closing_text = _build_closing_text()
        signoff_text = self.sender_signoff
        return InquiryResponseDraftContent(
            subject=subject,
            salutation=salutation,
            intro_text=intro_text,
            question_lines=tuple(
                InquiryResponseQuestionLine(
                    open_question_id=question.open_question_id,
                    question_type=question.question_type,
                    human_question_text=question.human_question_text,
                    prompt_text=question.human_question_text,
                )
                for question in context.open_questions
            ),
            closing_text=closing_text,
            signoff_text=signoff_text,
        )


def render_draft_body(content: InquiryResponseDraftContent) -> str:
    lines = [content.salutation, "", content.intro_text, ""]
    for line in content.question_lines:
        lines.append(f"- {line.prompt_text}")
    lines.extend(("", content.closing_text, "", content.signoff_text))
    return "\n".join(lines).strip()


def validate_draft_content(
    *,
    content: InquiryResponseDraftContent,
    required_questions: tuple[OpenQuestion, ...],
) -> tuple[int, ...]:
    required_question_ids = tuple(question.open_question_id for question in required_questions)
    ensure_tuple_of_positive_ints("required_question_ids", required_question_ids)
    if content.covered_question_ids != required_question_ids:
        raise Phase8ContractError(
            error_category="invalid_value",
            safe_message="draft content must cover exactly the current unresolved inquiry question set.",
        )
    body_text = render_draft_body(content)
    ensure_non_empty_text("body_text", body_text)
    for index, line in enumerate(content.question_lines):
        if not line.prompt_text.strip():
            raise Phase8ContractError(
                error_category="invalid_value",
                safe_message=f"question_lines[{index}] must include client-facing prompt text.",
            )
    return required_question_ids


def content_hash_payload(content: InquiryResponseDraftContent) -> str:
    return json.dumps(content.to_payload(), sort_keys=True, ensure_ascii=True)


def context_hash_payload(context: InquiryResponseDraftContext) -> str:
    return json.dumps(context.to_payload(), sort_keys=True, ensure_ascii=True)


def display_status_for_revision(
    revision: InquiryResponseDraftRevision,
    *,
    current_case_revision: int,
    current_open_question_ids: tuple[int, ...],
    action_status: str | None,
) -> str:
    if revision.is_current:
        if revision.source_case_revision != current_case_revision:
            return INQUIRY_DRAFT_STATUS_STALE
        if revision.covered_question_ids != current_open_question_ids:
            return INQUIRY_DRAFT_STATUS_STALE
        if action_status in {"superseded", "cancelled"} and revision.draft_status not in {
            INQUIRY_DRAFT_STATUS_REJECTED,
            INQUIRY_DRAFT_STATUS_SIMULATED_SENT,
            INQUIRY_DRAFT_STATUS_SEND_FAILED,
            INQUIRY_DRAFT_STATUS_SEND_OUTCOME_UNCERTAIN,
        }:
            return INQUIRY_DRAFT_STATUS_STALE
    return revision.draft_status


def _build_subject(context: InquiryResponseDraftContext) -> str:
    if len(context.open_questions) == 1:
        return "One quick detail for your rental inquiry"
    return "A few details we need for your rental inquiry"


def _build_salutation(context: InquiryResponseDraftContext) -> str:
    if context.contact_label:
        return f"Hi {context.contact_label},"
    return "Hi there,"


def _build_intro_text(context: InquiryResponseDraftContext) -> str:
    fact_summary = _summarize_current_facts(context.current_facts)
    if fact_summary:
        return (
            "Thanks for your inquiry. Based on what we have so far, "
            f"{fact_summary}. To help us move this forward, could you please share:"
        )
    return "Thanks for your inquiry. To help us move this forward, could you please share:"


def _build_closing_text() -> str:
    return "Once we have these details, we can review the next step with the right context."


def _summarize_current_facts(current_facts: tuple[RentalCaseFact, ...]) -> str:
    parts: list[str] = []
    for fact in current_facts:
        if fact.field_code == "active_event_window" and isinstance(fact.value_payload, dict):
            start = fact.value_payload.get("active_event_start")
            end = fact.value_payload.get("active_event_end")
            if start and end:
                parts.append(f"we currently have your requested event window as {start} to {end}")
        elif fact.field_code == "requested_rental_scope" and isinstance(fact.value_payload, str):
            parts.append(f"we currently have the requested scope as {fact.value_payload}")
        elif fact.field_code == "event_type" and isinstance(fact.value_payload, str):
            parts.append(f"we currently have the event type as {fact.value_payload}")
        elif fact.field_code == "guest_count" and isinstance(fact.value_payload, int):
            parts.append(f"we currently have the guest count as {fact.value_payload}")
    return "; ".join(parts)
