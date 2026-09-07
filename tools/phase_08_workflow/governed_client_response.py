from __future__ import annotations

"""Bounded client-response drafting contracts for Phase 8.

The contract builder receives only persisted, governed case state. Providers may
phrase that state, but cannot retrieve, decide, or mutate workflow truth.
"""

import hashlib
import json
import os
import re
import uuid
from dataclasses import dataclass
from typing import Any, Protocol

from tools.phase_07_reasoning.openai_answer_generator import (
    DEFAULT_OPENAI_API_BASE_URL,
    OpenAIAnswerProviderError,
    OpenAITransport,
    call_openai_responses,
)


RESPONSE_INTENT_COMPLETE_INQUIRY_RESPONSE = "COMPLETE_INQUIRY_RESPONSE"
RESPONSE_INTENT_REQUEST_CLIENT_INFORMATION = "REQUEST_CLIENT_INFORMATION"
RESPONSE_INTENT_PENDING_INTERNAL_CONFIRMATION = "PENDING_INTERNAL_CONFIRMATION"
RESPONSE_INTENT_COMMUNICATE_RESTRICTION = "COMMUNICATE_RESTRICTION"
RESPONSE_INTENT_DECISION_PENDING = "DECISION_PENDING"
RESPONSE_INTENT_CHANGE_ACKNOWLEDGEMENT = "CHANGE_ACKNOWLEDGEMENT"
RESPONSE_INTENT_RESCHEDULE_ACKNOWLEDGEMENT = "RESCHEDULE_ACKNOWLEDGEMENT"

RESPONSE_INTENTS = frozenset(
    {
        RESPONSE_INTENT_COMPLETE_INQUIRY_RESPONSE,
        RESPONSE_INTENT_REQUEST_CLIENT_INFORMATION,
        RESPONSE_INTENT_PENDING_INTERNAL_CONFIRMATION,
        RESPONSE_INTENT_COMMUNICATE_RESTRICTION,
        RESPONSE_INTENT_DECISION_PENDING,
        RESPONSE_INTENT_CHANGE_ACKNOWLEDGEMENT,
        RESPONSE_INTENT_RESCHEDULE_ACKNOWLEDGEMENT,
    }
)

CLIENT_DRAFT_PROVIDER_ENV = "CLIENT_DRAFT_PROVIDER"
CLIENT_DRAFT_MODEL_ENV = "CLIENT_DRAFT_MODEL"
CLIENT_DRAFT_TIMEOUT_SECONDS_ENV = "CLIENT_DRAFT_TIMEOUT_SECONDS"


class ClientResponseProviderError(RuntimeError):
    """A safe provider failure that never changes case truth."""


@dataclass(frozen=True)
class ResponseIntent:
    code: str
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.code not in RESPONSE_INTENTS:
            raise ValueError("unsupported response intent")


@dataclass(frozen=True)
class DraftContract:
    response_intent: ResponseIntent
    rental_case_id: int
    source_case_revision: int
    context_hash: str
    recipient_label: str
    latest_client_message: str
    confirmed_case_facts: tuple[str, ...]
    allowed_client_assertions: tuple[str, ...]
    known_restrictions: tuple[str, ...]
    pending_internal_confirmations: tuple[str, ...]
    open_client_questions: tuple[tuple[int, str], ...]
    pending_decisions: tuple[str, ...]
    change_or_reschedule_state: tuple[str, ...]
    forbidden_claims: tuple[str, ...]
    style_guidance: tuple[str, ...]

    def to_provider_payload(self) -> dict[str, Any]:
        return {
            "response_intent": self.response_intent.code,
            "recipient_label": self.recipient_label,
            "latest_client_message": self.latest_client_message,
            "confirmed_case_facts": list(self.confirmed_case_facts),
            "allowed_client_assertions": list(self.allowed_client_assertions),
            "known_restrictions": list(self.known_restrictions),
            "pending_internal_confirmations": list(self.pending_internal_confirmations),
            "open_client_questions": [
                {"open_question_id": question_id, "question": question}
                for question_id, question in self.open_client_questions
            ],
            "pending_decisions": list(self.pending_decisions),
            "change_or_reschedule_state": list(self.change_or_reschedule_state),
            "forbidden_claims": list(self.forbidden_claims),
            "style_guidance": list(self.style_guidance),
        }


@dataclass(frozen=True)
class ClientResponseDraft:
    subject: str
    body: str
    question_ids: tuple[int, ...] = ()
    provider_code: str = "deterministic_fake"
    model_code: str | None = None
    provider_request_id: str | None = None

    def __post_init__(self) -> None:
        if not self.subject.strip() or not self.body.strip():
            raise ValueError("client response draft subject and body are required")
        if len(set(self.question_ids)) != len(self.question_ids):
            raise ValueError("client response draft question_ids must be unique")


@dataclass(frozen=True)
class DraftValidationResult:
    is_valid: bool
    failure_codes: tuple[str, ...]


class GovernedClientResponseProvider(Protocol):
    def generate_client_response(self, contract: DraftContract) -> ClientResponseDraft: ...


class ResponseIntentResolver:
    """Application-side precedence for client communication intent."""

    def resolve(self, snapshot: Any) -> ResponseIntent:
        client_questions = tuple(
            question
            for question in getattr(snapshot, "open_questions", ())
            if getattr(question, "status", None) in {"open", "answered_pending_validation"}
            and str(getattr(question, "requested_from_role", "")).startswith("client")
        )
        if client_questions:
            return ResponseIntent(RESPONSE_INTENT_REQUEST_CLIENT_INFORMATION, ("open_client_questions",))

        changes = tuple(
            change for change in getattr(snapshot, "proposed_changes", ())
            if getattr(change, "status", None) not in {"cancelled", "superseded", "closed", "accepted", "rejected"}
        )
        if changes:
            return ResponseIntent(RESPONSE_INTENT_CHANGE_ACKNOWLEDGEMENT, ("proposed_case_change_pending",))

        reschedules = tuple(
            item for item in getattr(snapshot, "reschedule_requests", ())
            if getattr(item, "status", None) not in {"cancelled", "superseded", "closed", "accepted", "rejected"}
        )
        if reschedules:
            return ResponseIntent(RESPONSE_INTENT_RESCHEDULE_ACKNOWLEDGEMENT, ("reschedule_pending",))

        decisions = tuple(
            item for item in getattr(snapshot, "case_decisions", ())
            if getattr(item, "status", None) in {"proposed", "pending_approval"}
        )
        if decisions:
            return ResponseIntent(RESPONSE_INTENT_DECISION_PENDING, ("case_decision_pending",))

        semantic_states = _semantic_states(snapshot)
        if "known_no" in semantic_states:
            return ResponseIntent(RESPONSE_INTENT_COMMUNICATE_RESTRICTION, ("known_no",))

        blockers = tuple(
            blocker for blocker in getattr(snapshot, "blockers", ())
            if getattr(blocker, "status", None) == "open"
            and getattr(blocker, "blocker_type", None) != "missing_client_information"
        )
        if blockers or "known_conditional" in semantic_states or "unknown_internal" in semantic_states:
            return ResponseIntent(RESPONSE_INTENT_PENDING_INTERNAL_CONFIRMATION, ("internal_confirmation_pending",))

        return ResponseIntent(RESPONSE_INTENT_COMPLETE_INQUIRY_RESPONSE, ("actionable_inquiry",))


def build_draft_contract(
    *,
    snapshot: Any,
    recipient_label: str | None,
    latest_client_message: str | None,
    commercial_snapshot: tuple[tuple[str, str], ...] = (),
    feasibility_snapshot: tuple[tuple[str, str], ...] = (),
) -> DraftContract:
    intent = ResponseIntentResolver().resolve(snapshot)
    rental_case = snapshot.rental_case
    facts = tuple(
        f"{getattr(fact, 'field_code')}: {_format_value(getattr(fact, 'value_payload', None))}"
        for fact in getattr(snapshot, "rental_case_facts", ())
    )
    allowed = tuple(
        f"{label}: {value}"
        for label, value in commercial_snapshot
        if value and value not in {"None", "Not established"}
    )
    restrictions = tuple(
        f"{label}: {value}"
        for label, value in feasibility_snapshot
        if value and value not in {"None", "No", "Not established", "Not yet evaluated"}
    )
    pending_internal = tuple(
        _humanize(getattr(blocker, "blocker_type", "internal confirmation"))
        for blocker in getattr(snapshot, "blockers", ())
        if getattr(blocker, "status", None) == "open"
        and getattr(blocker, "blocker_type", None) != "missing_client_information"
    )
    questions = tuple(
        sorted(
            (
                (int(question.open_question_id), str(question.human_question_text))
                for question in getattr(snapshot, "open_questions", ())
                if getattr(question, "status", None) in {"open", "answered_pending_validation"}
                and str(getattr(question, "requested_from_role", "")).startswith("client")
            ),
            key=lambda item: item[0],
        )
    )
    pending_decisions = tuple(
        _humanize(getattr(item, "decision_type", "commercial decision"))
        for item in getattr(snapshot, "case_decisions", ())
        if getattr(item, "status", None) in {"proposed", "pending_approval"}
    )
    changes = tuple(
        _humanize(getattr(item, "change_kind", "requested change"))
        for item in getattr(snapshot, "proposed_changes", ())
        if getattr(item, "status", None) not in {"cancelled", "superseded", "closed", "accepted", "rejected"}
    ) + tuple(
        "requested reschedule is awaiting review"
        for item in getattr(snapshot, "reschedule_requests", ())
        if getattr(item, "status", None) not in {"cancelled", "superseded", "closed", "accepted", "rejected"}
    )
    forbidden = [
        "Do not confirm venue availability or booking.",
        "Do not describe a pending internal confirmation as completed.",
        "Do not describe a pending decision or fee adjustment as approved.",
        "Do not use historical precedent as current policy.",
    ]
    if intent.code == RESPONSE_INTENT_COMMUNICATE_RESTRICTION:
        forbidden.append("Do not represent a known restriction as supported.")
    context_payload = {
        "intent": intent.code,
        "case_revision": rental_case.case_revision,
        "facts": facts,
        "allowed": allowed,
        "restrictions": restrictions,
        "pending": pending_internal,
        "questions": questions,
        "decisions": pending_decisions,
        "changes": changes,
    }
    context_hash = hashlib.sha256(json.dumps(context_payload, sort_keys=True, ensure_ascii=True).encode("utf-8")).hexdigest()
    return DraftContract(
        response_intent=intent,
        rental_case_id=int(rental_case.rental_case_id),
        source_case_revision=int(rental_case.case_revision),
        context_hash=context_hash,
        recipient_label=(recipient_label or "there").strip() or "there",
        latest_client_message=(latest_client_message or "").strip(),
        confirmed_case_facts=facts,
        allowed_client_assertions=allowed,
        known_restrictions=restrictions,
        pending_internal_confirmations=pending_internal,
        open_client_questions=questions,
        pending_decisions=pending_decisions,
        change_or_reschedule_state=changes,
        forbidden_claims=tuple(forbidden),
        style_guidance=(
            "Write one warm, concise, professional email.",
            "Use only supplied assertions and do not mention internal systems or workflow terms.",
            "Ask only the supplied open client questions and make the next step clear.",
        ),
    )


class DeterministicFakeClientResponseProvider:
    """Test-only provider that makes no network request."""

    def generate_client_response(self, contract: DraftContract) -> ClientResponseDraft:
        greeting = f"Hi {contract.recipient_label},"
        if contract.response_intent.code == RESPONSE_INTENT_REQUEST_CLIENT_INFORMATION:
            questions = "\n".join(f"- {question}" for _, question in contract.open_client_questions)
            body = f"{greeting}\n\nThanks for getting in touch. To help us advise on the next steps, could you let us know:\n{questions}\n\nWarmly,\nWNC"
            return ClientResponseDraft("A few details for your inquiry", body, tuple(item[0] for item in contract.open_client_questions))
        if contract.response_intent.code == RESPONSE_INTENT_COMMUNICATE_RESTRICTION:
            detail = contract.known_restrictions[0] if contract.known_restrictions else "The requested arrangement is not supported under the current conditions."
            return ClientResponseDraft("Your WNC inquiry", f"{greeting}\n\nThank you for your inquiry. {detail}\n\nWarmly,\nWNC")
        if contract.response_intent.code == RESPONSE_INTENT_PENDING_INTERNAL_CONFIRMATION:
            detail = contract.pending_internal_confirmations[0] if contract.pending_internal_confirmations else "We are checking the remaining details internally."
            return ClientResponseDraft("Your WNC inquiry", f"{greeting}\n\nThank you for your inquiry. We are checking {detail} and will come back to you once that review is complete.\n\nWarmly,\nWNC")
        if contract.response_intent.code == RESPONSE_INTENT_DECISION_PENDING:
            detail = contract.pending_decisions[0] if contract.pending_decisions else "Your request"
            return ClientResponseDraft("Your WNC inquiry", f"{greeting}\n\nThank you for your inquiry. {detail} has been noted and is not yet confirmed.\n\nWarmly,\nWNC")
        if contract.response_intent.code in {RESPONSE_INTENT_CHANGE_ACKNOWLEDGEMENT, RESPONSE_INTENT_RESCHEDULE_ACKNOWLEDGEMENT}:
            detail = contract.change_or_reschedule_state[0] if contract.change_or_reschedule_state else "your updated request"
            return ClientResponseDraft("Your updated WNC inquiry", f"{greeting}\n\nThanks for the update. We have noted {detail} and will review it before confirming any arrangements.\n\nWarmly,\nWNC")
        assertions = "\n".join(contract.allowed_client_assertions[:2]) or "We have the details needed to review your inquiry."
        return ClientResponseDraft("Your WNC inquiry", f"{greeting}\n\nThank you for your inquiry. {assertions}\n\nWe will be in touch with the next steps.\n\nWarmly,\nWNC")


class OpenAIClientResponseProvider:
    """One no-tool OpenAI Responses API call using the Phase 7 transport seam."""

    def __init__(self, *, api_key: str, model_code: str, timeout_seconds: int = 60, transport: OpenAITransport | None = None) -> None:
        if not api_key.strip() or not model_code.strip():
            raise ValueError("OpenAI client response provider requires API key and model")
        self.api_key = api_key.strip()
        self.model_code = model_code.strip()
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    def generate_client_response(self, contract: DraftContract) -> ClientResponseDraft:
        request_id = f"phase8-client-draft-{uuid.uuid4().hex}"
        payload = {
            "model": self.model_code,
            "store": False,
            "input": [
                {"role": "system", "content": _provider_system_prompt()},
                {"role": "user", "content": json.dumps(contract.to_provider_payload(), sort_keys=True, ensure_ascii=True)},
            ],
            "text": {"format": {"type": "json_schema", "name": "client_response_draft", "strict": True, "schema": _provider_schema()}},
            "max_output_tokens": 900,
            "metadata": {"phase": "8", "contract": "governed_client_response_v1", "client_request_id": request_id},
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "X-Client-Request-Id": request_id}
        try:
            response, response_headers = call_openai_responses(payload, DEFAULT_OPENAI_API_BASE_URL, headers, self.timeout_seconds, transport=self.transport)
        except TimeoutError:
            raise
        except OpenAIAnswerProviderError as exc:
            raise ClientResponseProviderError(exc.safe_message) from exc
        try:
            text = _extract_openai_client_draft_text(response)
            parsed = json.loads(text)
            return ClientResponseDraft(
                subject=str(parsed["subject"]), body=str(parsed["body"]),
                question_ids=tuple(int(item) for item in parsed["question_ids"]), provider_code="openai",
                model_code=self.model_code, provider_request_id=response_headers.get("x-request-id") or response.get("id"),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ClientResponseProviderError("OpenAI returned malformed structured client-draft output.") from exc


def build_client_response_provider_from_env() -> GovernedClientResponseProvider:
    provider = os.environ.get(CLIENT_DRAFT_PROVIDER_ENV, "deterministic_fake").strip().lower()
    if provider in {"", "deterministic_fake", "fake"}:
        return DeterministicFakeClientResponseProvider()
    if provider != "openai":
        raise ClientResponseProviderError("Unsupported client-draft provider configuration.")
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    model = os.environ.get(CLIENT_DRAFT_MODEL_ENV, "").strip()
    if not api_key or not model:
        raise ClientResponseProviderError("Client-draft OpenAI provider is not configured.")
    timeout = int(os.environ.get(CLIENT_DRAFT_TIMEOUT_SECONDS_ENV, "60"))
    return OpenAIClientResponseProvider(api_key=api_key, model_code=model, timeout_seconds=timeout)


def validate_client_response_draft(*, contract: DraftContract, draft: ClientResponseDraft, current_case_revision: int, current_context_hash: str) -> DraftValidationResult:
    failures: list[str] = []
    if current_case_revision != contract.source_case_revision or current_context_hash != contract.context_hash:
        failures.append("stale_draft_contract")
    expected_questions = tuple(question_id for question_id, _ in contract.open_client_questions)
    if tuple(draft.question_ids) != expected_questions:
        failures.append("open_question_set_mismatch")
    body = draft.body.lower()
    if re.search(r"\b(?:booking|venue|date).{0,24}\b(?:confirmed|available)\b", body):
        failures.append("unsupported_availability_or_confirmation")
    if contract.response_intent.code == RESPONSE_INTENT_DECISION_PENDING and re.search(r"\b(?:waiver|discount|adjustment).{0,20}\b(?:approved|confirmed)\b", body):
        failures.append("pending_decision_presented_as_active")
    if contract.response_intent.code == RESPONSE_INTENT_COMMUNICATE_RESTRICTION and re.search(
        r"(?<!not )\b(?:supported|available|can provide)\b",
        body,
    ):
        failures.append("known_no_contradiction")
    allowed_fees = {match.group(0).lower() for assertion in contract.allowed_client_assertions for match in re.finditer(r"(?:EUR|€)\s?\d+(?:[.,]\d+)?", assertion, flags=re.IGNORECASE)}
    asserted_fees = {match.group(0).lower() for match in re.finditer(r"(?:EUR|€)\s?\d+(?:[.,]\d+)?", draft.body, flags=re.IGNORECASE)}
    if not asserted_fees.issubset(allowed_fees):
        failures.append("commercial_assertion_not_allowed")
    return DraftValidationResult(is_valid=not failures, failure_codes=tuple(failures))


def _semantic_states(snapshot: Any) -> tuple[str, ...]:
    states: list[str] = []
    for projection in getattr(snapshot, "reasoning_projections", ()):
        payload = getattr(projection, "degraded_retrieval_summary", None)
        if isinstance(payload, dict) and payload.get("semantic_state_code"):
            states.append(str(payload["semantic_state_code"]))
    return tuple(states)


def _format_value(value: Any) -> str:
    return json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else str(value)


def _humanize(value: Any) -> str:
    return str(value).replace("_", " ")


def _provider_system_prompt() -> str:
    return (
        "You draft client email prose for the WNC Rental Brain. Use only the supplied contract. "
        "Do not retrieve facts, make commitments, expose internal terms, or add assertions. "
        "Return JSON only."
    )


def _extract_openai_client_draft_text(response: dict[str, Any]) -> str:
    if response.get("status") not in {None, "completed"}:
        raise ClientResponseProviderError("OpenAI client-draft response did not complete.")
    output = response.get("output")
    if not isinstance(output, list):
        raise ClientResponseProviderError("OpenAI returned malformed structured client-draft output.")
    for item in output:
        if not isinstance(item, dict) or item.get("type") not in {None, "message"}:
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for content_item in content:
            if not isinstance(content_item, dict) or content_item.get("type") not in {None, "output_text"}:
                continue
            text = content_item.get("text")
            if isinstance(text, str):
                return text
    raise ClientResponseProviderError("OpenAI response did not contain a structured client draft.")


def _provider_schema() -> dict[str, Any]:
    return {
        "type": "object", "additionalProperties": False,
        "properties": {
            "subject": {"type": "string"}, "body": {"type": "string"},
            "question_ids": {"type": "array", "items": {"type": "integer"}},
        },
        "required": ["subject", "body", "question_ids"],
    }
