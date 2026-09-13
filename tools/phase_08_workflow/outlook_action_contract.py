"""One provider-free contract for governed Outlook communication actions.

An action reservation exists only to satisfy the draft's action foreign key. It
cannot execute or receive approval. Binding a persisted revision converts that
reservation exactly once, before approval, into a complete immutable contract.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, fields, replace
from typing import Any

from .contracts import (
    ACTION_CATEGORY_COMMUNICATION, ACTION_TYPE_SEND_INQUIRY_RESPONSE,
    APPROVAL_POSTURE_APPROVAL_REQUIRED, WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
    RentalCase, WorkflowAction,
)
from .governed_client_response import RESPONSE_INTENTS

CONTRACT_VERSION = "governed_outlook_v1"
RESERVATION_VERSION = "governed_outlook_reservation_v1"
GOVERNED_PURPOSE = "governed_client_response_draft"
GOVERNED_REASON = "operator_requested_governed_client_response"


class OutlookContractError(ValueError):
    def __init__(self, field: str):
        self.field = field
        super().__init__(f"outlook_action_contract_invalid:{field}")


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def recipient_identity_hash(recipient_email: str) -> str:
    return digest({"recipient_email": recipient_email.strip().casefold()})


def exact_approval_target(action_id: int, revision_id: int) -> str:
    return f"workflow_action:{action_id}:draft_revision:{revision_id}"


@dataclass(frozen=True)
class OutlookActionIntent:
    response_intent: str
    purpose: str
    reason: str

    def __post_init__(self) -> None:
        for name in ("response_intent", "purpose", "reason"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise OutlookContractError(name)
        if self.response_intent not in RESPONSE_INTENTS:
            raise OutlookContractError("response_intent")

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> OutlookActionIntent:
        return cls(*(payload.get(name) for name in ("response_intent", "purpose", "reason")))


@dataclass(frozen=True)
class OutlookExecutionInput:
    contract_version: str
    action_type: str
    provider_type: str
    rental_case_id: int
    source_case_revision: int
    response_intent: str
    purpose: str
    reason: str
    conversation_key: str
    draft_revision_id: int
    draft_origin_workflow_action_id: int
    draft_content_hash: str
    context_hash: str
    governed_context_hash: str
    recipient_email: str
    recipient_identity_hash: str
    recipient_reference: str
    subject: str
    body: str
    body_type: str
    message_mode: str
    graph_message_id: str | None
    approval_target: str
    provenance: str
    plan_identity: str
    recovery_draft_revision_id: int | None
    recovery_origin_workflow_action_id: int | None
    recovery_predecessor_action_id: int | None

    def __post_init__(self) -> None:
        nullable = {"graph_message_id", "recovery_draft_revision_id", "recovery_origin_workflow_action_id", "recovery_predecessor_action_id"}
        integers = {"rental_case_id", "source_case_revision", "draft_revision_id", "draft_origin_workflow_action_id"}
        for item in fields(self):
            value = getattr(self, item.name)
            if item.name in nullable:
                continue
            if item.name in integers:
                if type(value) is not int or value < (0 if item.name == "source_case_revision" else 1):
                    raise OutlookContractError(item.name)
            elif not isinstance(value, str) or not value.strip():
                raise OutlookContractError(item.name)
        OutlookActionIntent(self.response_intent, self.purpose, self.reason)
        for name, expected in (("contract_version", CONTRACT_VERSION), ("action_type", ACTION_TYPE_SEND_INQUIRY_RESPONSE),
                               ("provider_type", "microsoft_graph_outlook"), ("body_type", "text")):
            if getattr(self, name) != expected:
                raise OutlookContractError(name)
        if self.recipient_identity_hash != recipient_identity_hash(self.recipient_email):
            raise OutlookContractError("recipient_identity_hash")
        if self.recipient_reference != f"inquiry_response_draft:{self.draft_revision_id}":
            raise OutlookContractError("recipient_reference")
        if self.message_mode == "existing_draft":
            if not isinstance(self.graph_message_id, str) or not self.graph_message_id.strip():
                raise OutlookContractError("graph_message_id")
        elif self.message_mode != "new" or self.graph_message_id is not None:
            raise OutlookContractError("message_mode")
        recovery = self.recovery_draft_revision_id is not None or self.recovery_origin_workflow_action_id is not None
        if recovery and (type(self.recovery_draft_revision_id) is not int
                         or type(self.recovery_origin_workflow_action_id) is not int
                         or self.recovery_draft_revision_id != self.draft_revision_id
                         or self.recovery_origin_workflow_action_id != self.draft_origin_workflow_action_id):
            raise OutlookContractError("recovery_binding")
        if self.recovery_predecessor_action_id is not None and (
                not recovery or type(self.recovery_predecessor_action_id) is not int or self.recovery_predecessor_action_id <= 0):
            raise OutlookContractError("recovery_predecessor_action_id")
        # Use the adapter's parser as well, including its unsupported-recipient rules.
        from .outlook_adapter import OutlookActionInputError, _parse_outlook_email_payload
        try:
            _parse_outlook_email_payload(self.to_payload())
        except OutlookActionInputError as exc:
            raise OutlookContractError(exc.reason) from exc

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> OutlookExecutionInput:
        expected = {item.name for item in fields(cls)}
        missing = expected - payload.keys()
        if missing:
            raise OutlookContractError(",".join(sorted(missing)))
        # Reject unknown transport controls instead of discarding them in projection.
        if payload.keys() - expected:
            raise OutlookContractError("unexpected_fields:" + ",".join(sorted(payload.keys() - expected)))
        return cls(**payload)

    def idempotency_key(self) -> str:
        return f"{CONTRACT_VERSION}:{digest(self.to_identity())}"

    def to_identity(self) -> dict[str, Any]:
        # Every immutable input participates, including intent and transport
        # content. The approval target contains the allocated action ID and is
        # separately checked against that ID; lifecycle state never participates.
        return {name: value for name, value in self.to_payload().items() if name != "approval_target"}


def validate_outlook_action(action: WorkflowAction) -> OutlookExecutionInput:
    value = OutlookExecutionInput.from_payload(action.structured_payload)
    for name, expected in (("action_type", value.action_type), ("target_adapter_code", "outlook"),
                           ("action_category", ACTION_CATEGORY_COMMUNICATION),
                           ("reason_entity_type", "rental_case"), ("reason_entity_reference", value.conversation_key),
                           ("rental_case_id", value.rental_case_id), ("source_case_revision", value.source_case_revision),
                           ("approval_posture", APPROVAL_POSTURE_APPROVAL_REQUIRED),
                           ("semantic_subject_hash", value.governed_context_hash),
                           ("idempotency_key", value.idempotency_key())):
        if getattr(action, name) != expected:
            raise OutlookContractError(name)
    if value.approval_target != exact_approval_target(action.workflow_action_id, value.draft_revision_id):
        raise OutlookContractError("approval_target")
    if value.recovery_origin_workflow_action_id is not None:
        if action.supersedes_workflow_action_id != value.recovery_origin_workflow_action_id:
            raise OutlookContractError("recovery_binding")
    elif value.draft_origin_workflow_action_id != action.workflow_action_id:
        raise OutlookContractError("draft_origin_workflow_action_id")
    return value


def validate_outlook_action_creation(action: WorkflowAction) -> None:
    if action.action_type != ACTION_TYPE_SEND_INQUIRY_RESPONSE and action.target_adapter_code != "outlook":
        return
    if action.structured_payload.get("contract_version") != RESERVATION_VERSION:
        validate_outlook_action(action)
        # The repository allocates IDs on insert. A full action already carries
        # its allocated exact approval target, so it must be persisted by the
        # one-time bind operation instead of receiving another ID here.
        raise OutlookContractError("reservation_required_before_binding")
    plan = action.structured_payload
    # Reconstruct the reservation using the sole factory; hand-built subsets fail.
    from types import SimpleNamespace
    try:
        expected = reserve_governed_outlook_action(
            case=SimpleNamespace(rental_case_id=action.rental_case_id, case_revision=action.source_case_revision),
            intent=OutlookActionIntent.from_payload(plan), conversation_key=plan["conversation_key"],
            content_hash=plan["draft_content_hash"], context_hash=plan["context_hash"],
            recipient_email=plan["recipient_email"], provenance=plan["provenance"],
            origin_action_id=plan["origin_action_id"], graph_message_id=plan["graph_message_id"],
            recovery_revision_id=plan["recovery_revision_id"], now=action.created_at,
            recovery_predecessor_action_id=plan["recovery_predecessor_action_id"],
        )
    except KeyError as exc:
        raise OutlookContractError(str(exc)) from exc
    if replace(action, workflow_action_id=1, workflow_action_uuid="workflow-action", updated_at=action.created_at) != expected:
        raise OutlookContractError("reservation")


def reserve_governed_outlook_action(*, case: RentalCase, intent: OutlookActionIntent,
                                   conversation_key: str, content_hash: str, context_hash: str,
                                   recipient_email: str, provenance: str, now: str,
                                   origin_action_id: int | None = None,
                                   graph_message_id: str | None = None,
                                   recovery_revision_id: int | None = None,
                                   recovery_predecessor_action_id: int | None = None) -> WorkflowAction:
    plan = {**asdict(intent), "conversation_key": conversation_key, "draft_content_hash": content_hash,
            "context_hash": context_hash, "recipient_email": recipient_email,
            "recipient_identity_hash": recipient_identity_hash(recipient_email), "provenance": provenance,
            "origin_action_id": origin_action_id, "graph_message_id": graph_message_id,
            "recovery_revision_id": recovery_revision_id, "case_revision": case.case_revision,
            "recovery_predecessor_action_id": recovery_predecessor_action_id}
    for name in ("conversation_key", "draft_content_hash", "context_hash", "recipient_email", "provenance"):
        if not isinstance(plan[name], str) or not plan[name].strip():
            raise OutlookContractError(name)
    identity = f"{RESERVATION_VERSION}:{case.rental_case_id}:{digest({**plan, 'recipient_email': recipient_email.strip().casefold()})}"
    return WorkflowAction(
        workflow_action_id=1, workflow_action_uuid="workflow-action", rental_case_id=case.rental_case_id,
        action_type=ACTION_TYPE_SEND_INQUIRY_RESPONSE, action_category=ACTION_CATEGORY_COMMUNICATION,
        target_adapter_code="outlook", reason_entity_type="rental_case", reason_entity_reference=conversation_key,
        approval_posture=APPROVAL_POSTURE_APPROVAL_REQUIRED, status=WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
        semantic_subject_hash=context_hash, source_case_revision=case.case_revision, idempotency_key=identity,
        structured_payload={"contract_version": RESERVATION_VERSION, "plan_identity": identity, **plan},
        supersedes_workflow_action_id=origin_action_id, created_at=now, updated_at=now,
    )


def build_governed_outlook_action(*, reservation: WorkflowAction, case: RentalCase, revision: Any,
                                  intent: OutlookActionIntent, governed_context_hash: str,
                                  provenance: str, graph_message_id: str | None) -> WorkflowAction:
    if (reservation.structured_payload.get("contract_version") != RESERVATION_VERSION
            or reservation.status != WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL):
        raise OutlookContractError("reservation")
    if intent != OutlookActionIntent.from_payload(reservation.structured_payload):
        raise OutlookContractError("intent")
    if provenance != reservation.structured_payload["provenance"] or graph_message_id != reservation.structured_payload["graph_message_id"]:
        raise OutlookContractError("provenance")
    if revision.rental_case_id != case.rental_case_id or revision.source_case_revision != case.case_revision:
        raise OutlookContractError("source_case_revision")
    if not revision.is_current:
        raise OutlookContractError("draft_revision_id")
    recovery = reservation.structured_payload["recovery_revision_id"] is not None
    if (revision.conversation_key != reservation.structured_payload["conversation_key"]
            or revision.content_hash != reservation.structured_payload["draft_content_hash"]
            or revision.recipient_email != reservation.structured_payload["recipient_email"]
            or governed_context_hash != reservation.semantic_subject_hash):
        raise OutlookContractError("reservation_draft_binding")
    value = OutlookExecutionInput(
        contract_version=CONTRACT_VERSION, action_type=ACTION_TYPE_SEND_INQUIRY_RESPONSE,
        provider_type="microsoft_graph_outlook", rental_case_id=case.rental_case_id,
        source_case_revision=case.case_revision, **asdict(intent), conversation_key=revision.conversation_key,
        draft_revision_id=revision.inquiry_response_draft_revision_id,
        draft_origin_workflow_action_id=revision.workflow_action_id,
        draft_content_hash=revision.content_hash, context_hash=revision.context_hash,
        governed_context_hash=governed_context_hash, recipient_email=revision.recipient_email,
        recipient_identity_hash=recipient_identity_hash(revision.recipient_email),
        recipient_reference=f"inquiry_response_draft:{revision.inquiry_response_draft_revision_id}",
        subject=revision.subject, body=revision.body_text, body_type="text",
        message_mode="existing_draft" if graph_message_id is not None or revision.draft_source == "human_edited" else "new",
        graph_message_id=graph_message_id,
        approval_target=exact_approval_target(reservation.workflow_action_id, revision.inquiry_response_draft_revision_id),
        provenance=provenance, plan_identity=reservation.structured_payload["plan_identity"],
        recovery_draft_revision_id=revision.inquiry_response_draft_revision_id if recovery else None,
        recovery_origin_workflow_action_id=revision.workflow_action_id if recovery else None,
        recovery_predecessor_action_id=reservation.structured_payload["recovery_predecessor_action_id"],
    )
    action = replace(reservation, structured_payload=value.to_payload(), idempotency_key=value.idempotency_key())
    validate_outlook_action(action)
    return action
