from __future__ import annotations

"""Deterministic resolution and guidance inputs for governed client drafting.

This module deliberately does not execute providers or make business decisions.
It translates already-governed case state into client visibility, operator work,
and a small, authority-filtered factual guidance set.
"""

from dataclasses import dataclass
from typing import Any, Protocol


RESOLUTION_OWNER_CLIENT = "CLIENT"
RESOLUTION_OWNER_WNC_INTERNAL = "WNC_INTERNAL"
RESOLUTION_OWNER_EXTERNAL_PARTY = "EXTERNAL_PARTY"
RESOLUTION_OWNER_GOVERNED_DECISION = "GOVERNED_DECISION"

RESOLUTION_STATUS_REQUIRED = "REQUIRED"
RESOLUTION_STATUS_ACTION_CREATED = "ACTION_CREATED"
RESOLUTION_STATUS_CONTACT_REQUIRED = "CONTACT_REQUIRED"
RESOLUTION_STATUS_CONTACTED_AWAITING_RESPONSE = "CONTACTED_AWAITING_RESPONSE"
RESOLUTION_STATUS_RESOLVED = "RESOLVED"

CLIENT_VISIBILITY_ASK_CLIENT = "ASK_CLIENT"
CLIENT_VISIBILITY_INTERNAL_ONLY = "INTERNAL_ONLY"
CLIENT_VISIBILITY_EXTERNAL_PENDING_VISIBLE = "EXTERNAL_PENDING_VISIBLE"
CLIENT_VISIBILITY_DECISION_PENDING_VISIBLE = "DECISION_PENDING_VISIBLE"

OPERATOR_ANNOTATION_INTERNAL_CONFIRMATION = "INTERNAL_CONFIRMATION"
OPERATOR_ANNOTATION_EXTERNAL_CONTACT = "EXTERNAL_CONTACT"

CLIENT_SAFE_FACTUAL_DOCUMENT_CODES = frozenset({"CF-003", "CF-005", "SERV-003", "SERV-004"})

STYLE_PROFILE = (
    "Use a warm, concise, conversational WNC rental voice.",
    "Open with Hi <first name> when a recipient name is available.",
    "Acknowledge the specific message naturally and vary the opening.",
    "Use plain language, practical next steps, and a complete WNC signoff.",
    "Do not use em dashes or bureaucratic workflow language.",
)


@dataclass(frozen=True)
class ResolutionItem:
    proposition_key: str
    message: str
    resolution_owner: str
    resolution_status: str
    client_visibility: str
    blocking: bool
    workflow_action_id: int | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "proposition_key": self.proposition_key,
            "message": self.message,
            "resolution_owner": self.resolution_owner,
            "resolution_status": self.resolution_status,
            "client_visibility": self.client_visibility,
            "blocking": self.blocking,
            "workflow_action_id": self.workflow_action_id,
        }


@dataclass(frozen=True)
class OperatorAnnotation:
    annotation_type: str
    message: str
    proposition_key: str
    blocking: bool
    workflow_action_id: int | None

    def to_payload(self) -> dict[str, Any]:
        return {
            "type": self.annotation_type,
            "message": self.message,
            "proposition_key": self.proposition_key,
            "blocking": self.blocking,
            "workflow_action_id": self.workflow_action_id,
        }


@dataclass(frozen=True)
class ContextualGuidance:
    topic: str
    client_safe_guidance: str
    source_reference: str

    def to_payload(self) -> dict[str, str]:
        return {
            "topic": self.topic,
            "client_safe_guidance": self.client_safe_guidance,
            "source_reference": self.source_reference,
        }


class ContextualGuidanceSearch(Protocol):
    def search(self, *, topic: str, query_text: str, rental_type_code: str | None) -> tuple[dict[str, Any], ...]: ...


@dataclass(frozen=True)
class Phase5HybridGuidanceSearch:
    """Read-only Phase 5 FTS retrieval; embeddings are intentionally not generated here."""

    result_limit: int = 3

    def search(self, *, topic: str, query_text: str, rental_type_code: str | None) -> tuple[dict[str, Any], ...]:
        del topic
        from tools.phase_05_search.search_hybrid import run_hybrid_search

        rows, _elapsed_ms = run_hybrid_search(
            query_text=query_text,
            result_limit=self.result_limit,
            candidate_pool_limit=10,
            query_embedding=None,
            embedding_model_id=None,
            rental_type_code=rental_type_code,
        )
        return tuple(rows)


def derive_resolution_items(snapshot: Any) -> tuple[ResolutionItem, ...]:
    """Classify only persisted case state; never infer ownership with an LLM."""
    items: list[ResolutionItem] = []
    for question in getattr(snapshot, "open_questions", ()):
        if getattr(question, "status", None) not in {"open", "answered_pending_validation"}:
            continue
        if not str(getattr(question, "requested_from_role", "")).startswith("client"):
            continue
        items.append(
            ResolutionItem(
                proposition_key=f"open_question:{question.open_question_id}",
                message=str(question.human_question_text),
                resolution_owner=RESOLUTION_OWNER_CLIENT,
                resolution_status=RESOLUTION_STATUS_REQUIRED,
                client_visibility=CLIENT_VISIBILITY_ASK_CLIENT,
                blocking=True,
            )
        )
    for decision in getattr(snapshot, "case_decisions", ()):
        if getattr(decision, "status", None) not in {"proposed", "pending_approval"}:
            continue
        items.append(
            ResolutionItem(
                proposition_key=f"case_decision:{getattr(decision, 'case_decision_id', 'pending')}",
                message=_humanize(getattr(decision, "decision_type", "commercial request")),
                resolution_owner=RESOLUTION_OWNER_GOVERNED_DECISION,
                resolution_status=RESOLUTION_STATUS_REQUIRED,
                client_visibility=CLIENT_VISIBILITY_DECISION_PENDING_VISIBLE,
                blocking=True,
            )
        )
    events = tuple(getattr(snapshot, "workflow_events", ()))
    for blocker in getattr(snapshot, "blockers", ()):
        if getattr(blocker, "status", None) != "open":
            continue
        if getattr(blocker, "blocker_type", None) == "missing_client_information":
            continue
        blocker_key = f"blocker:{blocker.blocker_id}"
        is_external = _is_external_blocker(blocker)
        contacted = is_external and _external_contact_recorded(events, blocker_key)
        owner = RESOLUTION_OWNER_EXTERNAL_PARTY if is_external else RESOLUTION_OWNER_WNC_INTERNAL
        status = (
            RESOLUTION_STATUS_CONTACTED_AWAITING_RESPONSE
            if contacted
            else RESOLUTION_STATUS_CONTACT_REQUIRED
            if is_external
            else RESOLUTION_STATUS_REQUIRED
        )
        visibility = (
            CLIENT_VISIBILITY_EXTERNAL_PENDING_VISIBLE
            if contacted
            else CLIENT_VISIBILITY_INTERNAL_ONLY
        )
        items.append(
            ResolutionItem(
                proposition_key=blocker_key,
                message=_operator_message(blocker),
                resolution_owner=owner,
                resolution_status=status,
                client_visibility=visibility,
                blocking=True,
            )
        )
    return tuple(items)


def with_workflow_actions(
    items: tuple[ResolutionItem, ...],
    actions: tuple[Any, ...],
) -> tuple[ResolutionItem, ...]:
    by_key = {
        str(getattr(action, "structured_payload", {}).get("resolution_item_key")): action
        for action in actions
        if getattr(action, "structured_payload", {}).get("resolution_item_key")
    }
    enriched: list[ResolutionItem] = []
    for item in items:
        action = by_key.get(item.proposition_key)
        if action is None:
            enriched.append(item)
            continue
        enriched.append(
            ResolutionItem(
                proposition_key=item.proposition_key,
                message=item.message,
                resolution_owner=item.resolution_owner,
                resolution_status=(
                    RESOLUTION_STATUS_ACTION_CREATED
                    if item.resolution_owner == RESOLUTION_OWNER_WNC_INTERNAL
                    else item.resolution_status
                ),
                client_visibility=item.client_visibility,
                blocking=item.blocking,
                workflow_action_id=int(action.workflow_action_id),
            )
        )
    return tuple(enriched)


def operator_annotations(items: tuple[ResolutionItem, ...]) -> tuple[OperatorAnnotation, ...]:
    annotations: list[OperatorAnnotation] = []
    for item in items:
        if item.client_visibility != CLIENT_VISIBILITY_INTERNAL_ONLY:
            continue
        annotation_type = (
            OPERATOR_ANNOTATION_EXTERNAL_CONTACT
            if item.resolution_owner == RESOLUTION_OWNER_EXTERNAL_PARTY
            else OPERATOR_ANNOTATION_INTERNAL_CONFIRMATION
        )
        annotations.append(
            OperatorAnnotation(
                annotation_type=annotation_type,
                message=item.message,
                proposition_key=item.proposition_key,
                blocking=item.blocking,
                workflow_action_id=item.workflow_action_id,
            )
        )
    return tuple(annotations)


def detect_guidance_topics(snapshot: Any, latest_client_message: str | None) -> tuple[str, ...]:
    facts = {str(getattr(item, "field_code", "")): getattr(item, "value_payload", None) for item in getattr(snapshot, "rental_case_facts", ())}
    text = (latest_client_message or "").lower()
    topics: list[str] = []
    technical = facts.get("technical_requirements")
    if any(word in text for word in ("cater", "buffet", "food", "kitchen")) or facts.get("catering_arrangement"):
        topics.extend(("catering_kitchen", "external_supplier_setup"))
    if any(word in text for word in ("supplier", "florist", "loading", "handover", "delivery")):
        topics.append("external_supplier_setup")
    if technical or any(word in text for word in ("projector", "projection", "audio", "microphone", "hologram", "technical")):
        topics.append("technical_capabilities")
    if facts.get("facilitator_arrangement") or "facilitat" in text:
        topics.append("facilitator_process")
    guests = facts.get("guest_count")
    if facts.get("requested_rental_scope") == "entire_venue" or (isinstance(guests, int) and guests >= 40):
        topics.append("capacity")
    return tuple(dict.fromkeys(topics))


def retrieve_contextual_guidance(
    *,
    search: ContextualGuidanceSearch,
    topics: tuple[str, ...],
    rental_type_code: str | None,
    limit_per_topic: int = 2,
) -> tuple[ContextualGuidance, ...]:
    guidance: list[ContextualGuidance] = []
    for topic in topics:
        accepted = 0
        for row in search.search(topic=topic, query_text=_topic_query(topic), rental_type_code=rental_type_code):
            if accepted >= limit_per_topic or not _is_client_safe_current_guidance(row):
                continue
            text = str(row.get("body_text") or "").strip()
            source = str(row.get("document_code") or "").strip()
            if not text or not source:
                continue
            guidance.append(ContextualGuidance(topic=topic, client_safe_guidance=text, source_reference=source))
            accepted += 1
    return tuple(guidance)


def _is_external_blocker(blocker: Any) -> bool:
    value = " ".join(
        str(getattr(blocker, field, ""))
        for field in ("blocker_type", "resolution_condition_text", "origin_entity_reference")
    ).lower()
    return any(token in value for token in ("facilitator", "caterer", "supplier", "external provider", "external_party"))


def _external_contact_recorded(events: tuple[Any, ...], proposition_key: str) -> bool:
    return any(
        getattr(event, "event_type_code", None) == "external_resolution_contacted"
        and getattr(event, "structured_payload", {}).get("resolution_item_key") == proposition_key
        for event in events
    )


def _operator_message(blocker: Any) -> str:
    text = str(getattr(blocker, "resolution_condition_text", "")).strip().rstrip(".")
    if text:
        return text[0].upper() + text[1:]
    return f"Resolve {_humanize(getattr(blocker, 'blocker_type', 'operational requirement'))}"


def _humanize(value: Any) -> str:
    return str(value).replace("_", " ")


def _topic_query(topic: str) -> str:
    return {
        # Phase 5 FTS uses its own lexical index. Broad topic terms preserve
        # recall here; authority and document filters below remain the safety gate.
        "catering_kitchen": "catering",
        "external_supplier_setup": "supplier",
        "technical_capabilities": "technical",
        "facilitator_process": "facilitator",
        "capacity": "venue",
    }[topic]


def _is_client_safe_current_guidance(row: dict[str, Any]) -> bool:
    return (
        row.get("authority_classification") in {"authoritative", "guidance"}
        and row.get("document_code") in CLIENT_SAFE_FACTUAL_DOCUMENT_CODES
        and row.get("document_code") != "TPL-006"
    )
