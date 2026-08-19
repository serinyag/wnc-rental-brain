from __future__ import annotations

import unittest

from tools.phase_08_workflow.contracts import (
    LIFECYCLE_STATE_INQUIRY_ACTIVE,
    OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION,
    OPEN_QUESTION_STATUS_OPEN,
    REQUIREMENT_STATUS_REQUIRED,
    RentalCase,
    OpenQuestion,
    Requirement,
)
from tools.phase_08_workflow.observation_contracts import (
    OBSERVATION_CLAIM_KIND_CHANGE_REQUEST,
    OBSERVATION_CLAIM_KIND_EXCEPTION_REQUEST,
    OBSERVATION_CLAIM_KIND_NEW_INFORMATION,
    OBSERVATION_CLAIM_KIND_REQUIREMENT_EVIDENCE,
    OBSERVATION_DISPOSITION_CASE_ASSOCIATION_REQUIRED,
    OBSERVATION_DISPOSITION_CREATE_CASE_DECISION_CANDIDATE,
    OBSERVATION_DISPOSITION_CREATE_PROPOSED_CHANGE,
    OBSERVATION_DISPOSITION_CREATE_RESCHEDULE_REQUEST,
    OBSERVATION_DISPOSITION_MANUAL_MAPPING_REQUIRED,
    OBSERVATION_DISPOSITION_NO_WORKFLOW_EFFECT,
    OBSERVATION_DISPOSITION_OPEN_QUESTION_ANSWER_CANDIDATE,
    OBSERVATION_DISPOSITION_REJECT_QUARANTINE,
    OBSERVATION_STATUS_UNMAPPED,
    OBSERVATION_TYPE_CASE_DECISION_CANDIDATE,
    OBSERVATION_TYPE_CHANGE_CANDIDATE,
    OBSERVATION_TYPE_FACT_CANDIDATE,
    OBSERVATION_TYPE_REQUEST_CANDIDATE,
    OBSERVATION_TYPE_REQUIREMENT_EVIDENCE_CANDIDATE,
    RentalCaseFact,
)
from tools.phase_08_workflow.observation_repository import InMemoryObservationRepository
from tools.phase_08_workflow.observation_types import (
    CaseAssociationInput,
    InboundSourceRecordInput,
    StructuredObservationCandidate,
    StructuredObservationIngestionRequest,
)
from tools.phase_08_workflow.observations import ingest_structured_observations


def make_case(
    rental_case_id: int = 1,
    *,
    case_revision: int = 0,
    active_event_start: str | None = None,
    active_event_end: str | None = None,
) -> RentalCase:
    return RentalCase(
        rental_case_id=rental_case_id,
        rental_case_uuid=f"case-{rental_case_id}",
        case_reference_code=f"RC-{900 + rental_case_id}",
        lifecycle_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
        case_revision=case_revision,
        rental_type_code="studio_space",
        commercial_summary_status="unknown",
        operational_summary_status="unknown",
        is_active=True,
        active_event_start=active_event_start,
        active_event_end=active_event_end,
        created_at="2026-08-10T10:00:00Z",
        updated_at="2026-08-10T10:00:00Z",
    )


def make_fact(*, rental_case_id: int = 1, fact_id: int = 1, field_code: str, domain_code: str, value_payload: object) -> RentalCaseFact:
    return RentalCaseFact(
        rental_case_fact_id=fact_id,
        rental_case_id=rental_case_id,
        field_code=field_code,
        domain_code=domain_code,
        value_payload=value_payload,
        source_reference=f"fact:{fact_id}",
        established_case_revision=0,
        created_at="2026-08-10T10:00:00Z",
        updated_at="2026-08-10T10:00:00Z",
    )


def make_question(*, rental_case_id: int = 1, question_id: int = 1, question_type: str) -> OpenQuestion:
    return OpenQuestion(
        open_question_id=question_id,
        rental_case_id=rental_case_id,
        question_type=question_type,
        domain_code="event_profile",
        human_question_text="Need confirmation",
        blocking_scope="transition",
        status=OPEN_QUESTION_STATUS_OPEN,
        created_at="2026-08-10T10:00:00Z",
    )


def make_requirement(*, rental_case_id: int = 1, requirement_id: int = 1, requirement_type: str) -> Requirement:
    return Requirement(
        requirement_id=requirement_id,
        rental_case_id=rental_case_id,
        requirement_type=requirement_type,
        domain_code="supplier",
        applicability_basis="fixture",
        status=REQUIREMENT_STATUS_REQUIRED,
        blocking_scope="transition",
        created_at="2026-08-10T10:00:00Z",
    )


def make_repo(
    *,
    rental_cases: tuple[RentalCase, ...],
    facts: dict[int, list[RentalCaseFact]] | None = None,
    questions: dict[int, list[OpenQuestion]] | None = None,
    requirements: dict[int, list[Requirement]] | None = None,
) -> InMemoryObservationRepository:
    return InMemoryObservationRepository(
        rental_cases={case.rental_case_id: case for case in rental_cases},
        rental_case_facts={} if facts is None else facts,
        open_questions={} if questions is None else questions,
        requirements={} if requirements is None else requirements,
        proposed_changes={},
        case_decisions={},
        reschedule_requests={},
        workflow_events={},
        inbound_source_records={},
        inbound_observations={},
        inbound_observation_effects={},
        source_ids_by_dedupe={},
        observation_ids_by_identity={},
        observation_ids_by_source={},
        observation_failure_codes={},
    )


def make_request(
    *,
    dedupe_key: str,
    candidate: StructuredObservationCandidate,
    rental_case_id: int | None = 1,
) -> StructuredObservationIngestionRequest:
    return StructuredObservationIngestionRequest(
        source_record=InboundSourceRecordInput(
            source_system_code="manual_input",
            source_record_type="operator_note",
            occurred_at="2026-08-10T10:00:00Z",
            dedupe_key=dedupe_key,
            source_hash=f"hash:{dedupe_key}",
            external_source_id=f"external:{dedupe_key}",
        ),
        observations=(candidate,),
        case_association=CaseAssociationInput(rental_case_id=rental_case_id),
    )


class ObservationIngestionTests(unittest.TestCase):
    def test_existing_value_change_creates_proposed_change_without_mutating_fact(self) -> None:
        repo = make_repo(
            rental_cases=(make_case(),),
            facts={1: [make_fact(field_code="guest_count", domain_code="event_profile", value_payload=30)]},
        )
        request = make_request(
            dedupe_key="change-guest-count",
            candidate=StructuredObservationCandidate(
                reported_field_code="guest_count",
                observation_type=OBSERVATION_TYPE_CHANGE_CANDIDATE,
                claim_kind=OBSERVATION_CLAIM_KIND_CHANGE_REQUEST,
                candidate_value_payload=60,
                source_evidence_reference="note:guest-count",
            ),
        )

        result = ingest_structured_observations(request=request, repository=repo)

        self.assertEqual(result.observation_results[0].effect.disposition_code, OBSERVATION_DISPOSITION_CREATE_PROPOSED_CHANGE)
        self.assertEqual(repo.proposed_changes[1][0].prior_value_payload, 30)
        self.assertEqual(repo.proposed_changes[1][0].proposed_value_payload, 60)
        self.assertEqual(repo.rental_case_facts[1][0].value_payload, 30)
        self.assertEqual(repo.rental_cases[1].lifecycle_state, LIFECYCLE_STATE_INQUIRY_ACTIVE)

    def test_booking_fee_waiver_stays_proposed_even_at_high_confidence(self) -> None:
        repo = make_repo(rental_cases=(make_case(),))
        request = make_request(
            dedupe_key="booking-fee-waiver",
            candidate=StructuredObservationCandidate(
                reported_field_code="booking_fee_override",
                observation_type=OBSERVATION_TYPE_CASE_DECISION_CANDIDATE,
                claim_kind=OBSERVATION_CLAIM_KIND_EXCEPTION_REQUEST,
                candidate_value_payload={"amount": 0, "currency": "EUR"},
                source_evidence_reference="internal:fee-waiver",
                asserted_by_party_type="operator",
                extraction_confidence=0.999,
            ),
        )

        result = ingest_structured_observations(request=request, repository=repo)

        self.assertEqual(result.observation_results[0].effect.disposition_code, OBSERVATION_DISPOSITION_CREATE_CASE_DECISION_CANDIDATE)
        self.assertEqual(repo.case_decisions[1][0].status, "proposed")
        self.assertEqual(repo.case_decisions[1][0].baseline_reference, "phase4:booking_fee")

    def test_reschedule_request_preserves_current_active_dates(self) -> None:
        repo = make_repo(
            rental_cases=(
                make_case(
                    active_event_start="2026-09-10T12:00:00Z",
                    active_event_end="2026-09-10T18:00:00Z",
                ),
            )
        )
        request = make_request(
            dedupe_key="reschedule-request",
            candidate=StructuredObservationCandidate(
                reported_field_code="active_event_window",
                observation_type=OBSERVATION_TYPE_REQUEST_CANDIDATE,
                claim_kind=OBSERVATION_CLAIM_KIND_CHANGE_REQUEST,
                candidate_value_payload={
                    "active_event_start": "2026-10-03T12:00:00Z",
                    "active_event_end": "2026-10-03T18:00:00Z",
                },
                source_evidence_reference="client:reschedule",
            ),
        )

        result = ingest_structured_observations(request=request, repository=repo)

        self.assertEqual(result.observation_results[0].effect.disposition_code, OBSERVATION_DISPOSITION_CREATE_RESCHEDULE_REQUEST)
        self.assertEqual(repo.reschedule_requests[1][0].requested_date_payload["active_event_start"], "2026-10-03T12:00:00Z")
        self.assertEqual(repo.rental_cases[1].active_event_start, "2026-09-10T12:00:00Z")

    def test_initial_schedule_candidate_without_current_schedule_creates_no_reschedule_request(self) -> None:
        repo = make_repo(rental_cases=(make_case(active_event_start=None, active_event_end=None),))
        request = make_request(
            dedupe_key="initial-schedule",
            candidate=StructuredObservationCandidate(
                reported_field_code="active_event_window",
                observation_type=OBSERVATION_TYPE_REQUEST_CANDIDATE,
                claim_kind=OBSERVATION_CLAIM_KIND_NEW_INFORMATION,
                candidate_value_payload={
                    "active_event_start": "2026-10-03T12:00:00Z",
                    "active_event_end": "2026-10-03T18:00:00Z",
                },
                source_evidence_reference="client:initial-schedule",
            ),
        )

        result = ingest_structured_observations(request=request, repository=repo)

        self.assertEqual(result.observation_results[0].effect.disposition_code, OBSERVATION_DISPOSITION_NO_WORKFLOW_EFFECT)
        self.assertEqual(repo.reschedule_requests.get(1), None)

    def test_incomplete_schedule_candidate_creates_no_reschedule_request(self) -> None:
        repo = make_repo(rental_cases=(make_case(active_event_start=None, active_event_end=None),))
        request = make_request(
            dedupe_key="incomplete-schedule",
            candidate=StructuredObservationCandidate(
                reported_field_code="active_event_window",
                observation_type=OBSERVATION_TYPE_REQUEST_CANDIDATE,
                claim_kind=OBSERVATION_CLAIM_KIND_NEW_INFORMATION,
                candidate_value_payload={
                    "active_event_start": "2026-11-15T00:00:00Z",
                },
                source_evidence_reference="client:partial-schedule",
            ),
        )

        result = ingest_structured_observations(request=request, repository=repo)

        self.assertEqual(result.observation_results[0].effect.disposition_code, OBSERVATION_DISPOSITION_NO_WORKFLOW_EFFECT)
        self.assertEqual(repo.reschedule_requests.get(1), None)

    def test_unknown_field_is_unmapped_and_creates_no_truth_change(self) -> None:
        repo = make_repo(rental_cases=(make_case(),))
        request = make_request(
            dedupe_key="unknown-field",
            candidate=StructuredObservationCandidate(
                reported_field_code="flower_vibe_energy_score",
                observation_type=OBSERVATION_TYPE_FACT_CANDIDATE,
                claim_kind=OBSERVATION_CLAIM_KIND_NEW_INFORMATION,
                candidate_value_payload=9,
                source_evidence_reference="extractor:unknown",
            ),
        )

        result = ingest_structured_observations(request=request, repository=repo)

        self.assertEqual(result.observation_results[0].observation.status, OBSERVATION_STATUS_UNMAPPED)
        self.assertEqual(result.observation_results[0].effect.disposition_code, OBSERVATION_DISPOSITION_MANUAL_MAPPING_REQUIRED)
        self.assertEqual(repo.proposed_changes.get(1), None)

    def test_duplicate_source_delivery_is_idempotent(self) -> None:
        repo = make_repo(
            rental_cases=(make_case(),),
            facts={1: [make_fact(field_code="guest_count", domain_code="event_profile", value_payload=30)]},
        )
        request = make_request(
            dedupe_key="duplicate-source",
            candidate=StructuredObservationCandidate(
                reported_field_code="guest_count",
                observation_type=OBSERVATION_TYPE_CHANGE_CANDIDATE,
                claim_kind=OBSERVATION_CLAIM_KIND_CHANGE_REQUEST,
                candidate_value_payload=60,
                source_evidence_reference="note:duplicate",
            ),
        )

        first_result = ingest_structured_observations(request=request, repository=repo)
        second_result = ingest_structured_observations(request=request, repository=repo)

        self.assertFalse(first_result.duplicate_source)
        self.assertTrue(second_result.duplicate_source)
        self.assertEqual(len(repo.inbound_source_records), 1)
        self.assertEqual(len(repo.proposed_changes[1]), 1)

    def test_ambiguous_case_requires_association(self) -> None:
        repo = make_repo(rental_cases=(make_case(),))
        request = StructuredObservationIngestionRequest(
            source_record=InboundSourceRecordInput(
                source_system_code="manual_input",
                source_record_type="operator_note",
                occurred_at="2026-08-10T10:00:00Z",
                dedupe_key="ambiguous-case",
                source_hash="hash:ambiguous",
            ),
            observations=(
                StructuredObservationCandidate(
                    reported_field_code="guest_count",
                    observation_type=OBSERVATION_TYPE_FACT_CANDIDATE,
                    claim_kind=OBSERVATION_CLAIM_KIND_NEW_INFORMATION,
                    candidate_value_payload=30,
                    source_evidence_reference="note:ambiguous",
                ),
            ),
        )

        result = ingest_structured_observations(request=request, repository=repo)

        self.assertEqual(result.case_association.status, "case_association_required")
        self.assertEqual(result.observation_results[0].effect.disposition_code, OBSERVATION_DISPOSITION_CASE_ASSOCIATION_REQUIRED)

    def test_open_question_answer_candidate_updates_status_without_resolving(self) -> None:
        repo = make_repo(
            rental_cases=(make_case(),),
            questions={1: [make_question(question_type="expected_guest_count")]},
        )
        request = make_request(
            dedupe_key="guest-answer",
            candidate=StructuredObservationCandidate(
                reported_field_code="guest_count",
                observation_type=OBSERVATION_TYPE_FACT_CANDIDATE,
                claim_kind=OBSERVATION_CLAIM_KIND_NEW_INFORMATION,
                candidate_value_payload=30,
                source_evidence_reference="client:guest-count",
            ),
        )

        result = ingest_structured_observations(request=request, repository=repo)

        self.assertEqual(result.observation_results[0].effect.disposition_code, OBSERVATION_DISPOSITION_OPEN_QUESTION_ANSWER_CANDIDATE)
        self.assertEqual(repo.open_questions[1][0].status, OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION)
        self.assertIsNone(repo.open_questions[1][0].resolved_at)

    def test_stale_observation_requires_revalidation(self) -> None:
        repo = make_repo(
            rental_cases=(make_case(case_revision=6),),
            facts={1: [make_fact(field_code="guest_count", domain_code="event_profile", value_payload=30)]},
        )
        request = make_request(
            dedupe_key="stale-observation",
            candidate=StructuredObservationCandidate(
                reported_field_code="guest_count",
                observation_type=OBSERVATION_TYPE_CHANGE_CANDIDATE,
                claim_kind=OBSERVATION_CLAIM_KIND_CHANGE_REQUEST,
                candidate_value_payload=60,
                source_evidence_reference="note:stale",
                observed_against_case_revision=4,
            ),
        )

        result = ingest_structured_observations(request=request, repository=repo)

        self.assertTrue(result.observation_results[0].effect.stale_observation)
        self.assertTrue(result.observation_results[0].effect.revalidation_required)

    def test_requirement_evidence_cross_case_write_is_rejected(self) -> None:
        repo = make_repo(
            rental_cases=(make_case(1), make_case(2)),
            requirements={1: [make_requirement(rental_case_id=2, requirement_id=9, requirement_type="supplier_details_required")]},
        )
        request = make_request(
            dedupe_key="cross-case-requirement",
            candidate=StructuredObservationCandidate(
                reported_field_code="supplier_details",
                observation_type=OBSERVATION_TYPE_REQUIREMENT_EVIDENCE_CANDIDATE,
                claim_kind=OBSERVATION_CLAIM_KIND_REQUIREMENT_EVIDENCE,
                candidate_value_payload={"supplier_name": "Example AV"},
                source_evidence_reference="supplier:details",
            ),
        )

        result = ingest_structured_observations(request=request, repository=repo)

        self.assertEqual(result.observation_results[0].effect.disposition_code, OBSERVATION_DISPOSITION_REJECT_QUARANTINE)
        self.assertIn("cross_case_reference", result.observation_results[0].failure_codes)
