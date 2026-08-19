from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any, Protocol

from .contracts import (
    CASE_DECISION_STATUS_PROPOSED,
    OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION,
    OPEN_QUESTION_STATUS_OPEN,
    OPEN_QUESTION_STATUS_RESOLVED,
    PROPOSED_CHANGE_STATUS_PROPOSED,
    REQUIREMENT_STATUS_IN_PROGRESS,
    RESCHEDULE_STATUS_PROPOSED,
    CaseDecision,
    OpenQuestion,
    ProposedCaseChange,
    RentalCase,
    Requirement,
    RescheduleRequest,
    WorkflowEvent,
)
from .inquiry_intake import (
    ACTIVE_CHANGE_STATUSES,
    ACTIVE_RESCHEDULE_STATUSES,
    CORE_INQUIRY_FIELD_RULES,
    INQUIRY_FIELD_EVENT_TYPE,
    INQUIRY_FIELD_GUEST_COUNT,
    INQUIRY_FIELD_REQUESTED_SCHEDULE,
    INQUIRY_FIELD_REQUESTED_SPACE,
    INQUIRY_INTAKE_EFFECT_CREATE_OPEN_QUESTION,
    INQUIRY_INTAKE_EFFECT_CREATE_PROPOSED_CHANGE,
    INQUIRY_INTAKE_EFFECT_CREATE_RESCHEDULE_REQUEST,
    INQUIRY_INTAKE_EFFECT_PROMOTE_CURRENT_VALUE,
    INQUIRY_INTAKE_EFFECT_RESOLVE_OPEN_QUESTION,
    InquiryIntakeCommitResult,
    InquiryIntakePlan,
)
from .observation_contracts import (
    InboundObservation,
    InboundObservationEffect,
    InboundSourceRecord,
    RentalCaseFact,
)
from .observation_types import CaseAssociationResult, InboundSourceRecordInput
from .validation import Phase8ContractError


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ObservationCaseSnapshot:
    rental_case: RentalCase
    rental_case_facts: tuple[RentalCaseFact, ...] = ()
    open_questions: tuple[OpenQuestion, ...] = ()
    requirements: tuple[Requirement, ...] = ()
    proposed_changes: tuple[ProposedCaseChange, ...] = ()
    case_decisions: tuple[CaseDecision, ...] = ()
    reschedule_requests: tuple[RescheduleRequest, ...] = ()
    workflow_events: tuple[WorkflowEvent, ...] = ()

    def find_fact(self, field_code: str) -> RentalCaseFact | None:
        for fact in self.rental_case_facts:
            if fact.field_code == field_code:
                return fact
        return None

    def find_open_question(self, question_types: tuple[str, ...]) -> OpenQuestion | None:
        for question in self.open_questions:
            if question.question_type in question_types and question.status == "open":
                return question
        return None

    def find_requirement(self, requirement_types: tuple[str, ...]) -> Requirement | None:
        for requirement in self.requirements:
            if (
                requirement.requirement_type in requirement_types
                and requirement.status in {"required", "in_progress", "unresolved"}
            ):
                return requirement
        return None


class ObservationRepositoryProtocol(Protocol):
    def load_case_snapshot(self, rental_case_id: int) -> ObservationCaseSnapshot | None: ...

    def get_case_by_reference(self, case_reference_code: str) -> RentalCase | None: ...

    def get_source_by_dedupe(self, *, source_system_code: str, dedupe_key: str) -> InboundSourceRecord | None: ...

    def get_observation_by_identity(
        self,
        *,
        inbound_source_record_id: int,
        observation_identity_key: str,
    ) -> InboundObservation | None: ...

    def list_observations_for_source(self, inbound_source_record_id: int) -> tuple[InboundObservation, ...]: ...

    def get_effect_for_observation(self, inbound_observation_id: int) -> InboundObservationEffect | None: ...

    def get_failure_codes_for_observation(self, inbound_observation_id: int) -> tuple[str, ...]: ...

    def create_source_record(
        self,
        *,
        source_record_input: InboundSourceRecordInput,
        case_association: CaseAssociationResult,
        created_at: str,
    ) -> InboundSourceRecord: ...

    def create_observation(
        self,
        *,
        inbound_source_record_id: int,
        rental_case_id: int | None,
        reported_field_code: str,
        reported_domain_code: str | None,
        target_field_code: str | None,
        target_domain_code: str | None,
        observation_type: str,
        claim_kind: str,
        candidate_value_payload: Any,
        source_evidence_reference: str,
        status: str,
        observation_identity_key: str,
        asserted_by_party_type: str | None,
        asserted_by_reference: str | None,
        source_excerpt: str | None,
        observed_against_case_revision: int | None,
        extraction_confidence: float | None,
        ambiguity_flags: tuple[str, ...],
        created_at: str,
    ) -> InboundObservation: ...

    def create_workflow_event(
        self,
        *,
        rental_case_id: int,
        event_type_code: str = "inbound_observation_recorded",
        source_type: str,
        source_reference: str,
        actor_type: str | None,
        actor_reference: str | None,
        occurred_at: str,
        structured_payload: dict[str, Any],
        event_identity_key: str,
    ) -> WorkflowEvent: ...

    def update_open_question_answer_candidate(
        self,
        *,
        rental_case_id: int,
        open_question_id: int,
        proposed_answer_payload: Any,
        source_reference: str,
    ) -> OpenQuestion: ...

    def attach_requirement_evidence(
        self,
        *,
        rental_case_id: int,
        requirement_id: int,
        evidence_reference: str,
    ) -> Requirement: ...

    def create_proposed_change(
        self,
        *,
        rental_case_id: int,
        change_kind: str,
        domain_code: str,
        prior_value_payload: Any,
        proposed_value_payload: Any,
        source_reference: str,
        detected_at: str,
        impact_classification: str | None,
        affected_domain_codes: tuple[str, ...],
        review_posture: str | None,
    ) -> ProposedCaseChange: ...

    def create_case_decision_candidate(
        self,
        *,
        rental_case_id: int,
        decision_type: str,
        domain_code: str,
        baseline_reference: str,
        proposed_value_payload: Any,
        scope_key: str,
        scope_description: str,
        authority_basis: str,
        approval_posture: str,
        evidence_reference: str,
        created_at: str,
    ) -> CaseDecision: ...

    def create_reschedule_request(
        self,
        *,
        rental_case_id: int,
        current_active_date_snapshot: dict[str, Any],
        requested_date_payload: dict[str, Any],
        consequence_summary_payload: dict[str, Any],
        urgency_class: str,
        created_at: str,
    ) -> RescheduleRequest: ...

    def create_effect(
        self,
        *,
        inbound_observation_id: int,
        rental_case_id: int | None,
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
        workflow_event_id: int | None = None,
    ) -> InboundObservationEffect: ...


@dataclass
class InMemoryObservationRepository:
    rental_cases: dict[int, RentalCase]
    rental_case_facts: dict[int, list[RentalCaseFact]]
    open_questions: dict[int, list[OpenQuestion]]
    requirements: dict[int, list[Requirement]]
    proposed_changes: dict[int, list[ProposedCaseChange]]
    case_decisions: dict[int, list[CaseDecision]]
    reschedule_requests: dict[int, list[RescheduleRequest]]
    workflow_events: dict[int, list[WorkflowEvent]]
    inbound_source_records: dict[int, InboundSourceRecord]
    inbound_observations: dict[int, InboundObservation]
    inbound_observation_effects: dict[int, InboundObservationEffect]
    source_ids_by_dedupe: dict[tuple[str, str], int]
    observation_ids_by_identity: dict[tuple[int, str], int]
    observation_ids_by_source: dict[int, list[int]]
    observation_failure_codes: dict[int, tuple[str, ...]]
    _rental_case_fact_id: int = 10_000
    _open_question_id: int = 15_000
    _workflow_event_id: int = 20_000
    _inbound_source_record_id: int = 30_000
    _inbound_observation_id: int = 40_000
    _inbound_observation_effect_id: int = 50_000
    _proposed_change_id: int = 60_000
    _case_decision_id: int = 70_000
    _reschedule_request_id: int = 80_000

    def load_case_snapshot(self, rental_case_id: int) -> ObservationCaseSnapshot | None:
        rental_case = self.rental_cases.get(rental_case_id)
        if rental_case is None:
            return None
        return ObservationCaseSnapshot(
            rental_case=rental_case,
            rental_case_facts=tuple(self.rental_case_facts.get(rental_case_id, ())),
            open_questions=tuple(self.open_questions.get(rental_case_id, ())),
            requirements=tuple(self.requirements.get(rental_case_id, ())),
            proposed_changes=tuple(self.proposed_changes.get(rental_case_id, ())),
            case_decisions=tuple(self.case_decisions.get(rental_case_id, ())),
            reschedule_requests=tuple(self.reschedule_requests.get(rental_case_id, ())),
            workflow_events=tuple(self.workflow_events.get(rental_case_id, ())),
        )

    def get_case_by_reference(self, case_reference_code: str) -> RentalCase | None:
        for rental_case in self.rental_cases.values():
            if rental_case.case_reference_code == case_reference_code:
                return rental_case
        return None

    def get_source_by_dedupe(self, *, source_system_code: str, dedupe_key: str) -> InboundSourceRecord | None:
        source_id = self.source_ids_by_dedupe.get((source_system_code, dedupe_key))
        if source_id is None:
            return None
        return self.inbound_source_records[source_id]

    def get_observation_by_identity(
        self,
        *,
        inbound_source_record_id: int,
        observation_identity_key: str,
    ) -> InboundObservation | None:
        observation_id = self.observation_ids_by_identity.get((inbound_source_record_id, observation_identity_key))
        if observation_id is None:
            return None
        return self.inbound_observations[observation_id]

    def list_observations_for_source(self, inbound_source_record_id: int) -> tuple[InboundObservation, ...]:
        return tuple(
            self.inbound_observations[observation_id]
            for observation_id in self.observation_ids_by_source.get(inbound_source_record_id, ())
        )

    def list_observations_for_case(self, rental_case_id: int) -> tuple[InboundObservation, ...]:
        return tuple(
            observation
            for observation in self.inbound_observations.values()
            if observation.rental_case_id == rental_case_id
        )

    def get_effect_for_observation(self, inbound_observation_id: int) -> InboundObservationEffect | None:
        return self.inbound_observation_effects.get(inbound_observation_id)

    def list_effects_for_case(self, rental_case_id: int) -> tuple[InboundObservationEffect, ...]:
        return tuple(
            effect
            for observation_id, effect in self.inbound_observation_effects.items()
            if self.inbound_observations.get(observation_id) is not None
            and self.inbound_observations[observation_id].rental_case_id == rental_case_id
        )

    def get_failure_codes_for_observation(self, inbound_observation_id: int) -> tuple[str, ...]:
        return self.observation_failure_codes.get(inbound_observation_id, ())

    def create_source_record(
        self,
        *,
        source_record_input: InboundSourceRecordInput,
        case_association: CaseAssociationResult,
        created_at: str,
    ) -> InboundSourceRecord:
        dedupe_identity = (source_record_input.source_system_code, source_record_input.dedupe_key)
        existing = self.source_ids_by_dedupe.get(dedupe_identity)
        if existing is not None:
            return self.inbound_source_records[existing]

        self._inbound_source_record_id += 1
        source_record = InboundSourceRecord(
            inbound_source_record_id=self._inbound_source_record_id,
            source_system_code=source_record_input.source_system_code,
            source_record_type=source_record_input.source_record_type,
            dedupe_key=source_record_input.dedupe_key,
            source_hash=source_record_input.source_hash,
            occurred_at=source_record_input.occurred_at,
            association_status=case_association.status,
            created_at=created_at,
            external_source_id=source_record_input.external_source_id,
            conversation_reference=source_record_input.conversation_reference,
            sender_actor_type=source_record_input.sender_actor_type,
            sender_actor_reference=source_record_input.sender_actor_reference,
            case_reference_hint=source_record_input.case_reference_hint or case_association.case_reference_code,
            resolved_rental_case_id=case_association.rental_case_id,
            association_basis=case_association.association_basis,
            received_at=source_record_input.received_at,
            source_location_reference=source_record_input.source_location_reference,
            confidentiality_posture=source_record_input.confidentiality_posture,
            pi_posture=source_record_input.pi_posture,
            evidence_excerpt=source_record_input.evidence_excerpt,
        )
        self.inbound_source_records[source_record.inbound_source_record_id] = source_record
        self.source_ids_by_dedupe[dedupe_identity] = source_record.inbound_source_record_id
        return source_record

    def create_observation(
        self,
        *,
        inbound_source_record_id: int,
        rental_case_id: int | None,
        reported_field_code: str,
        reported_domain_code: str | None,
        target_field_code: str | None,
        target_domain_code: str | None,
        observation_type: str,
        claim_kind: str,
        candidate_value_payload: Any,
        source_evidence_reference: str,
        status: str,
        observation_identity_key: str,
        asserted_by_party_type: str | None,
        asserted_by_reference: str | None,
        source_excerpt: str | None,
        observed_against_case_revision: int | None,
        extraction_confidence: float | None,
        ambiguity_flags: tuple[str, ...],
        created_at: str,
    ) -> InboundObservation:
        existing = self.get_observation_by_identity(
            inbound_source_record_id=inbound_source_record_id,
            observation_identity_key=observation_identity_key,
        )
        if existing is not None:
            return existing

        self._inbound_observation_id += 1
        observation = InboundObservation(
            inbound_observation_id=self._inbound_observation_id,
            inbound_source_record_id=inbound_source_record_id,
            reported_field_code=reported_field_code,
            reported_domain_code=reported_domain_code,
            target_field_code=target_field_code,
            target_domain_code=target_domain_code,
            rental_case_id=rental_case_id,
            observation_type=observation_type,
            claim_kind=claim_kind,
            candidate_value_payload=candidate_value_payload,
            source_evidence_reference=source_evidence_reference,
            status=status,
            observation_identity_key=observation_identity_key,
            asserted_by_party_type=asserted_by_party_type,
            asserted_by_reference=asserted_by_reference,
            source_excerpt=source_excerpt,
            observed_against_case_revision=observed_against_case_revision,
            extraction_confidence=extraction_confidence,
            ambiguity_flags=ambiguity_flags,
            created_at=created_at,
            updated_at=created_at,
        )
        self.inbound_observations[observation.inbound_observation_id] = observation
        self.observation_ids_by_identity[(inbound_source_record_id, observation_identity_key)] = observation.inbound_observation_id
        self.observation_ids_by_source.setdefault(inbound_source_record_id, []).append(observation.inbound_observation_id)
        return observation

    def create_workflow_event(
        self,
        *,
        rental_case_id: int,
        event_type_code: str = "inbound_observation_recorded",
        source_type: str,
        source_reference: str,
        actor_type: str | None,
        actor_reference: str | None,
        occurred_at: str,
        structured_payload: dict[str, Any],
        event_identity_key: str,
    ) -> WorkflowEvent:
        for workflow_event in self.workflow_events.get(rental_case_id, ()):
            if workflow_event.event_identity_key == event_identity_key:
                return workflow_event

        self._workflow_event_id += 1
        workflow_event = WorkflowEvent(
            workflow_event_id=self._workflow_event_id,
            workflow_event_uuid=f"workflow-event-{self._workflow_event_id}",
            rental_case_id=rental_case_id,
            event_type_code=event_type_code,
            source_type=source_type,
            source_reference=source_reference,
            actor_type=actor_type,
            actor_reference=actor_reference,
            occurred_at=occurred_at,
            recorded_at=occurred_at,
            structured_payload=structured_payload,
            event_identity_key=event_identity_key,
            origin_metadata={"phase": "8.3"},
        )
        self.workflow_events.setdefault(rental_case_id, []).append(workflow_event)
        return workflow_event

    def update_open_question_answer_candidate(
        self,
        *,
        rental_case_id: int,
        open_question_id: int,
        proposed_answer_payload: Any,
        source_reference: str,
    ) -> OpenQuestion:
        question = self._replace_case_record(
            collection=self.open_questions.setdefault(rental_case_id, []),
            entity_id=open_question_id,
            expected_case_id=rental_case_id,
            replace_fn=lambda value: replace(
                value,
                status=OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION,
                proposed_answer_payload=proposed_answer_payload,
                source_reference=source_reference,
                resolved_at=None,
            ),
        )
        return question

    def attach_requirement_evidence(
        self,
        *,
        rental_case_id: int,
        requirement_id: int,
        evidence_reference: str,
    ) -> Requirement:
        requirement = self._replace_case_record(
            collection=self.requirements.setdefault(rental_case_id, []),
            entity_id=requirement_id,
            expected_case_id=rental_case_id,
            replace_fn=lambda value: replace(
                value,
                evidence_reference=evidence_reference,
                status=REQUIREMENT_STATUS_IN_PROGRESS if value.status == "required" else value.status,
            ),
        )
        return requirement

    def create_proposed_change(
        self,
        *,
        rental_case_id: int,
        change_kind: str,
        domain_code: str,
        prior_value_payload: Any,
        proposed_value_payload: Any,
        source_reference: str,
        detected_at: str,
        impact_classification: str | None,
        affected_domain_codes: tuple[str, ...],
        review_posture: str | None,
    ) -> ProposedCaseChange:
        self._proposed_change_id += 1
        proposed_change = ProposedCaseChange(
            proposed_case_change_id=self._proposed_change_id,
            rental_case_id=rental_case_id,
            change_kind=change_kind,
            domain_code=domain_code,
            prior_value_payload=prior_value_payload,
            proposed_value_payload=proposed_value_payload,
            source_reference=source_reference,
            detected_at=detected_at,
            impact_classification=impact_classification,
            affected_domain_codes=affected_domain_codes,
            review_posture=review_posture,
            status=PROPOSED_CHANGE_STATUS_PROPOSED,
            created_at=detected_at,
            updated_at=detected_at,
        )
        self.proposed_changes.setdefault(rental_case_id, []).append(proposed_change)
        return proposed_change

    def create_case_decision_candidate(
        self,
        *,
        rental_case_id: int,
        decision_type: str,
        domain_code: str,
        baseline_reference: str,
        proposed_value_payload: Any,
        scope_key: str,
        scope_description: str,
        authority_basis: str,
        approval_posture: str,
        evidence_reference: str,
        created_at: str,
    ) -> CaseDecision:
        self._case_decision_id += 1
        decision = CaseDecision(
            case_decision_id=self._case_decision_id,
            rental_case_id=rental_case_id,
            decision_type=decision_type,
            domain_code=domain_code,
            baseline_reference=baseline_reference,
            proposed_value_payload=proposed_value_payload,
            scope_key=scope_key,
            scope_description=scope_description,
            authority_basis=authority_basis,
            approval_posture=approval_posture,
            status=CASE_DECISION_STATUS_PROPOSED,
            created_at=created_at,
            evidence_reference=evidence_reference,
            updated_at=created_at,
        )
        self.case_decisions.setdefault(rental_case_id, []).append(decision)
        return decision

    def create_reschedule_request(
        self,
        *,
        rental_case_id: int,
        current_active_date_snapshot: dict[str, Any],
        requested_date_payload: dict[str, Any],
        consequence_summary_payload: dict[str, Any],
        urgency_class: str,
        created_at: str,
    ) -> RescheduleRequest:
        self._reschedule_request_id += 1
        reschedule_request = RescheduleRequest(
            reschedule_request_id=self._reschedule_request_id,
            rental_case_id=rental_case_id,
            current_active_date_snapshot=current_active_date_snapshot,
            requested_date_payload=requested_date_payload,
            candidate_dates_payload=(),
            consequence_summary_payload=consequence_summary_payload,
            status=RESCHEDULE_STATUS_PROPOSED,
            urgency_class=urgency_class,
            created_at=created_at,
            updated_at=created_at,
        )
        self.reschedule_requests.setdefault(rental_case_id, []).append(reschedule_request)
        return reschedule_request

    def create_effect(
        self,
        *,
        inbound_observation_id: int,
        rental_case_id: int | None,
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
        workflow_event_id: int | None = None,
    ) -> InboundObservationEffect:
        existing = self.inbound_observation_effects.get(inbound_observation_id)
        if existing is not None:
            return existing

        self._inbound_observation_effect_id += 1
        effect = InboundObservationEffect(
            inbound_observation_effect_id=self._inbound_observation_effect_id,
            inbound_observation_id=inbound_observation_id,
            rental_case_id=rental_case_id,
            disposition_code=disposition_code,
            revalidation_required=revalidation_required,
            stale_observation=stale_observation,
            reason_codes=reason_codes,
            created_at=created_at,
            linked_open_question_id=linked_open_question_id,
            linked_requirement_id=linked_requirement_id,
            linked_proposed_change_id=linked_proposed_change_id,
            linked_case_decision_id=linked_case_decision_id,
            linked_reschedule_request_id=linked_reschedule_request_id,
            workflow_event_id=workflow_event_id,
        )
        self.inbound_observation_effects[inbound_observation_id] = effect
        self.observation_failure_codes[inbound_observation_id] = failure_codes
        return effect

    def upsert_rental_case_fact(
        self,
        *,
        rental_case_id: int,
        field_code: str,
        domain_code: str,
        value_payload: Any,
        source_reference: str,
        established_case_revision: int,
        timestamp: str,
    ) -> RentalCaseFact:
        facts = self.rental_case_facts.setdefault(rental_case_id, [])
        for index, fact in enumerate(facts):
            if fact.field_code != field_code:
                continue
            replacement = replace(
                fact,
                domain_code=domain_code,
                value_payload=value_payload,
                source_reference=source_reference,
                established_case_revision=established_case_revision,
                updated_at=timestamp,
            )
            facts[index] = replacement
            return replacement
        self._rental_case_fact_id += 1
        fact = RentalCaseFact(
            rental_case_fact_id=self._rental_case_fact_id,
            rental_case_id=rental_case_id,
            field_code=field_code,
            domain_code=domain_code,
            value_payload=value_payload,
            source_reference=source_reference,
            established_case_revision=established_case_revision,
            created_at=timestamp,
            updated_at=timestamp,
        )
        facts.append(fact)
        return fact

    def commit_inquiry_intake_plan(
        self,
        plan: InquiryIntakePlan,
        *,
        actor_reference: str,
        actor_type: str | None,
        applied_at: str,
    ) -> InquiryIntakeCommitResult:
        snapshot = self.load_case_snapshot(plan.rental_case_id)
        if snapshot is None:
            return InquiryIntakeCommitResult(
                rental_case_id=plan.rental_case_id,
                case_revision_before=0,
                case_revision_after=0,
                plan=plan,
                applied_effects=(),
                failure_codes=("case_not_found",),
            )
        if snapshot.rental_case.case_revision != plan.evaluated_case_revision:
            return InquiryIntakeCommitResult(
                rental_case_id=plan.rental_case_id,
                case_revision_before=snapshot.rental_case.case_revision,
                case_revision_after=snapshot.rental_case.case_revision,
                plan=plan,
                applied_effects=(),
                failure_codes=("stale_case_revision",),
            )
        if not plan.effects:
            return InquiryIntakeCommitResult(
                rental_case_id=plan.rental_case_id,
                case_revision_before=snapshot.rental_case.case_revision,
                case_revision_after=snapshot.rental_case.case_revision,
                plan=plan,
                applied_effects=(),
            )

        created_open_question_ids: list[int] = []
        resolved_open_question_ids: list[int] = []
        created_proposed_change_ids: list[int] = []
        created_reschedule_request_ids: list[int] = []

        case_before = snapshot.rental_case
        promoted_schedule = next(
            (
                effect
                for effect in plan.effects
                if effect.effect_code == INQUIRY_INTAKE_EFFECT_PROMOTE_CURRENT_VALUE
                and effect.inquiry_field_code == INQUIRY_FIELD_REQUESTED_SCHEDULE
            ),
            None,
        )
        promoted_scope = next(
            (
                effect
                for effect in plan.effects
                if effect.effect_code == INQUIRY_INTAKE_EFFECT_PROMOTE_CURRENT_VALUE
                and effect.inquiry_field_code == INQUIRY_FIELD_REQUESTED_SPACE
            ),
            None,
        )
        updated_case = replace(
            case_before,
            case_revision=case_before.case_revision + 1,
            active_event_start=(
                promoted_schedule.proposed_value.get("active_event_start")
                if promoted_schedule is not None and isinstance(promoted_schedule.proposed_value, dict)
                else case_before.active_event_start
            ),
            active_event_end=(
                promoted_schedule.proposed_value.get("active_event_end")
                if promoted_schedule is not None and isinstance(promoted_schedule.proposed_value, dict)
                else case_before.active_event_end
            ),
            rental_type_code=(
                str(promoted_scope.proposed_value)
                if promoted_scope is not None and isinstance(promoted_scope.proposed_value, str)
                else case_before.rental_type_code
            ),
            updated_at=applied_at,
        )
        self.rental_cases[plan.rental_case_id] = updated_case

        for effect in plan.effects:
            if effect.effect_code == INQUIRY_INTAKE_EFFECT_PROMOTE_CURRENT_VALUE:
                if effect.inquiry_field_code == INQUIRY_FIELD_GUEST_COUNT:
                    self.upsert_rental_case_fact(
                        rental_case_id=plan.rental_case_id,
                        field_code="guest_count",
                        domain_code=effect.domain_code,
                        value_payload=effect.proposed_value,
                        source_reference=_primary_observation_reference(effect),
                        established_case_revision=updated_case.case_revision,
                        timestamp=applied_at,
                    )
                elif effect.inquiry_field_code == INQUIRY_FIELD_EVENT_TYPE:
                    self.upsert_rental_case_fact(
                        rental_case_id=plan.rental_case_id,
                        field_code="event_type",
                        domain_code=effect.domain_code,
                        value_payload=effect.proposed_value,
                        source_reference=_primary_observation_reference(effect),
                        established_case_revision=updated_case.case_revision,
                        timestamp=applied_at,
                    )
                self._create_inquiry_workflow_event(
                    effect,
                    rental_case_id=plan.rental_case_id,
                    actor_reference=actor_reference,
                    actor_type=actor_type,
                    occurred_at=applied_at,
                    case_revision=updated_case.case_revision,
                )
                continue

            if effect.effect_code == INQUIRY_INTAKE_EFFECT_CREATE_OPEN_QUESTION:
                question = self._create_or_reuse_open_question(
                    rental_case_id=plan.rental_case_id,
                    question_type=effect.open_question_type or CORE_INQUIRY_FIELD_RULES[effect.inquiry_field_code].question_type,
                    domain_code=effect.domain_code,
                    human_question_text=effect.human_question_text
                    or CORE_INQUIRY_FIELD_RULES[effect.inquiry_field_code].human_question_text,
                    blocking_scope=effect.blocking_scope or BLOCKING_SCOPE_TRANSITION,
                    source_reference=_primary_observation_reference(effect),
                    created_at=applied_at,
                )
                created_open_question_ids.append(question.open_question_id)
                self._create_inquiry_workflow_event(
                    effect,
                    rental_case_id=plan.rental_case_id,
                    actor_reference=actor_reference,
                    actor_type=actor_type,
                    occurred_at=applied_at,
                    case_revision=updated_case.case_revision,
                    linked_entity_id=question.open_question_id,
                )
                continue

            if effect.effect_code == INQUIRY_INTAKE_EFFECT_RESOLVE_OPEN_QUESTION and effect.open_question_id is not None:
                resolved_question = self._resolve_open_question(
                    rental_case_id=plan.rental_case_id,
                    open_question_id=effect.open_question_id,
                    source_reference=_primary_observation_reference(effect),
                    resolved_at=applied_at,
                )
                resolved_open_question_ids.append(resolved_question.open_question_id)
                self._create_inquiry_workflow_event(
                    effect,
                    rental_case_id=plan.rental_case_id,
                    actor_reference=actor_reference,
                    actor_type=actor_type,
                    occurred_at=applied_at,
                    case_revision=updated_case.case_revision,
                    linked_entity_id=resolved_question.open_question_id,
                )
                continue

            if effect.effect_code == INQUIRY_INTAKE_EFFECT_CREATE_PROPOSED_CHANGE:
                change = self._create_or_reuse_proposed_change(
                    rental_case_id=plan.rental_case_id,
                    change_kind=CORE_INQUIRY_FIELD_RULES[effect.inquiry_field_code].change_kind,
                    domain_code=effect.domain_code,
                    prior_value_payload=effect.current_value,
                    proposed_value_payload=effect.proposed_value,
                    source_reference=_primary_observation_reference(effect),
                    detected_at=applied_at,
                )
                created_proposed_change_ids.append(change.proposed_case_change_id)
                self._create_inquiry_workflow_event(
                    effect,
                    rental_case_id=plan.rental_case_id,
                    actor_reference=actor_reference,
                    actor_type=actor_type,
                    occurred_at=applied_at,
                    case_revision=updated_case.case_revision,
                    linked_entity_id=change.proposed_case_change_id,
                )
                continue

            if effect.effect_code == INQUIRY_INTAKE_EFFECT_CREATE_RESCHEDULE_REQUEST:
                request = self._create_or_reuse_reschedule_request(
                    rental_case_id=plan.rental_case_id,
                    current_active_date_snapshot=effect.current_value if isinstance(effect.current_value, dict) else {},
                    requested_date_payload=effect.proposed_value if isinstance(effect.proposed_value, dict) else {},
                    created_at=applied_at,
                )
                created_reschedule_request_ids.append(request.reschedule_request_id)
                self._create_inquiry_workflow_event(
                    effect,
                    rental_case_id=plan.rental_case_id,
                    actor_reference=actor_reference,
                    actor_type=actor_type,
                    occurred_at=applied_at,
                    case_revision=updated_case.case_revision,
                    linked_entity_id=request.reschedule_request_id,
                )
                continue

        return InquiryIntakeCommitResult(
            rental_case_id=plan.rental_case_id,
            case_revision_before=case_before.case_revision,
            case_revision_after=updated_case.case_revision,
            plan=plan,
            applied_effects=plan.effects,
            created_open_question_ids=tuple(created_open_question_ids),
            resolved_open_question_ids=tuple(resolved_open_question_ids),
            created_proposed_change_ids=tuple(created_proposed_change_ids),
            created_reschedule_request_ids=tuple(created_reschedule_request_ids),
        )

    def _replace_case_record(
        self,
        *,
        collection: list[Any],
        entity_id: int,
        expected_case_id: int,
        replace_fn: Any,
    ) -> Any:
        for index, value in enumerate(collection):
            actual_case_id = getattr(value, "rental_case_id", None)
            actual_entity_id = getattr(
                value,
                "open_question_id",
                getattr(value, "requirement_id", None),
            )
            if actual_entity_id != entity_id:
                continue
            if actual_case_id != expected_case_id:
                raise ValueError("cross_case_reference")
            replacement = replace_fn(value)
            collection[index] = replacement
            return replacement
        raise Phase8ContractError(
            error_category="missing_value",
            safe_message="The requested workflow entity could not be found for the resolved rental case.",
        )

    def _create_or_reuse_open_question(
        self,
        *,
        rental_case_id: int,
        question_type: str,
        domain_code: str,
        human_question_text: str,
        blocking_scope: str,
        source_reference: str,
        created_at: str,
    ) -> OpenQuestion:
        for question in self.open_questions.get(rental_case_id, ()):
            if question.question_type != question_type:
                continue
            if question.status not in {OPEN_QUESTION_STATUS_OPEN, OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION}:
                continue
            return question
        self._open_question_id += 1
        question = OpenQuestion(
            open_question_id=self._open_question_id,
            rental_case_id=rental_case_id,
            question_type=question_type,
            domain_code=domain_code,
            human_question_text=human_question_text,
            blocking_scope=blocking_scope,
            status=OPEN_QUESTION_STATUS_OPEN,
            created_at=created_at,
            requested_from_role="client",
            source_reference=source_reference,
        )
        self.open_questions.setdefault(rental_case_id, []).append(question)
        return question

    def _resolve_open_question(
        self,
        *,
        rental_case_id: int,
        open_question_id: int,
        source_reference: str,
        resolved_at: str,
    ) -> OpenQuestion:
        return self._replace_case_record(
            collection=self.open_questions.setdefault(rental_case_id, []),
            entity_id=open_question_id,
            expected_case_id=rental_case_id,
            replace_fn=lambda value: value
            if value.status == OPEN_QUESTION_STATUS_RESOLVED
            else replace(
                value,
                status=OPEN_QUESTION_STATUS_RESOLVED,
                source_reference=source_reference,
                resolved_at=resolved_at,
                proposed_answer_payload=value.proposed_answer_payload,
            ),
        )

    def _create_or_reuse_proposed_change(
        self,
        *,
        rental_case_id: int,
        change_kind: str,
        domain_code: str,
        prior_value_payload: Any,
        proposed_value_payload: Any,
        source_reference: str,
        detected_at: str,
    ) -> ProposedCaseChange:
        for change in self.proposed_changes.get(rental_case_id, ()):
            if change.change_kind != change_kind or change.status not in ACTIVE_CHANGE_STATUSES:
                continue
            if change.prior_value_payload == prior_value_payload and change.proposed_value_payload == proposed_value_payload:
                return change
        return self.create_proposed_change(
            rental_case_id=rental_case_id,
            change_kind=change_kind,
            domain_code=domain_code,
            prior_value_payload=prior_value_payload,
            proposed_value_payload=proposed_value_payload,
            source_reference=source_reference,
            detected_at=detected_at,
            impact_classification=None,
            affected_domain_codes=(domain_code,),
            review_posture=None,
        )

    def _create_or_reuse_reschedule_request(
        self,
        *,
        rental_case_id: int,
        current_active_date_snapshot: dict[str, Any],
        requested_date_payload: dict[str, Any],
        created_at: str,
    ) -> RescheduleRequest:
        for request in self.reschedule_requests.get(rental_case_id, ()):
            if request.status not in ACTIVE_RESCHEDULE_STATUSES:
                continue
            if (
                request.current_active_date_snapshot == current_active_date_snapshot
                and request.requested_date_payload == requested_date_payload
            ):
                return request
        return self.create_reschedule_request(
            rental_case_id=rental_case_id,
            current_active_date_snapshot=current_active_date_snapshot,
            requested_date_payload=requested_date_payload,
            consequence_summary_payload={"source": "inquiry_intake"},
            urgency_class="normal",
            created_at=created_at,
        )

    def _create_inquiry_workflow_event(
        self,
        effect,
        *,
        rental_case_id: int,
        actor_reference: str,
        actor_type: str | None,
        occurred_at: str,
        case_revision: int,
        linked_entity_id: int | None = None,
    ) -> WorkflowEvent:
        event_type_code = {
            INQUIRY_INTAKE_EFFECT_PROMOTE_CURRENT_VALUE: "case_fact_promoted_from_observation",
            INQUIRY_INTAKE_EFFECT_CREATE_OPEN_QUESTION: "inquiry_open_question_created",
            INQUIRY_INTAKE_EFFECT_RESOLVE_OPEN_QUESTION: "inquiry_open_question_resolved",
            INQUIRY_INTAKE_EFFECT_CREATE_PROPOSED_CHANGE: "inquiry_change_proposed",
            INQUIRY_INTAKE_EFFECT_CREATE_RESCHEDULE_REQUEST: "inquiry_reschedule_requested",
        }[effect.effect_code]
        payload = {
            "field_code": effect.inquiry_field_code,
            "effect_code": effect.effect_code,
            "reason_code": effect.reason_code,
            "source_observation_ids": list(effect.source_observation_ids),
            "current_value": effect.current_value,
            "proposed_value": effect.proposed_value,
            "case_revision": case_revision,
        }
        if linked_entity_id is not None:
            payload["linked_entity_id"] = linked_entity_id
        return self.create_workflow_event(
            rental_case_id=rental_case_id,
            event_type_code=event_type_code,
            source_type="inquiry_intake_runtime",
            source_reference=_primary_observation_reference(effect),
            actor_type=actor_type,
            actor_reference=actor_reference,
            occurred_at=occurred_at,
            structured_payload=payload,
            event_identity_key=effect.idempotency_key,
        )


def _primary_observation_reference(effect) -> str:
    if effect.source_observation_ids:
        return f"inbound_observation:{effect.source_observation_ids[-1]}"
    return f"inquiry_intake:{effect.inquiry_field_code}"
