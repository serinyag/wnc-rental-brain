from __future__ import annotations

import unittest
from dataclasses import replace

from tools.phase_08_workflow.contracts import LIFECYCLE_STATE_INQUIRY_ACTIVE, OpenQuestion, RentalCase
from tools.phase_08_workflow.inquiry_intake import apply_inquiry_intake, evaluate_inquiry_intake
from tools.phase_08_workflow.observation_contracts import (
    OBSERVATION_CLAIM_KIND_CHANGE_REQUEST,
    OBSERVATION_CLAIM_KIND_NEW_INFORMATION,
    OBSERVATION_TYPE_FACT_CANDIDATE,
    OBSERVATION_TYPE_REQUEST_CANDIDATE,
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
    rental_type_code: str = "custom_scope",
    active_event_start: str | None = None,
    active_event_end: str | None = None,
) -> RentalCase:
    return RentalCase(
        rental_case_id=rental_case_id,
        rental_case_uuid=f"case-{rental_case_id}",
        case_reference_code=f"RC-{900 + rental_case_id}",
        lifecycle_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
        case_revision=case_revision,
        rental_type_code=rental_type_code,
        commercial_summary_status="unknown",
        operational_summary_status="unknown",
        is_active=True,
        active_event_start=active_event_start,
        active_event_end=active_event_end,
        service_level_or_type="fixture",
        created_at="2026-08-14T09:00:00Z",
        updated_at="2026-08-14T09:00:00Z",
    )


def make_fact(
    *,
    rental_case_id: int = 1,
    fact_id: int = 1,
    field_code: str,
    value_payload: object,
    domain_code: str = "event_profile",
) -> RentalCaseFact:
    return RentalCaseFact(
        rental_case_fact_id=fact_id,
        rental_case_id=rental_case_id,
        field_code=field_code,
        domain_code=domain_code,
        value_payload=value_payload,
        source_reference=f"fact:{fact_id}",
        established_case_revision=0,
        created_at="2026-08-14T09:00:00Z",
        updated_at="2026-08-14T09:00:00Z",
    )


def make_repo(
    *,
    rental_cases: tuple[RentalCase, ...],
    facts: dict[int, list[RentalCaseFact]] | None = None,
    questions: dict[int, list[OpenQuestion]] | None = None,
) -> InMemoryObservationRepository:
    return InMemoryObservationRepository(
        rental_cases={case.rental_case_id: case for case in rental_cases},
        rental_case_facts={} if facts is None else facts,
        open_questions={} if questions is None else questions,
        requirements={},
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


def ingest_candidate(
    repo: InMemoryObservationRepository,
    *,
    rental_case_id: int = 1,
    dedupe_key: str,
    reported_field_code: str,
    observation_type: str,
    claim_kind: str,
    candidate_value_payload: object,
) -> None:
    ingest_structured_observations(
        request=StructuredObservationIngestionRequest(
            source_record=InboundSourceRecordInput(
                source_system_code="manual_input",
                source_record_type="operator_note",
                occurred_at="2026-08-14T09:00:00Z",
                dedupe_key=dedupe_key,
                source_hash=f"hash:{dedupe_key}",
                external_source_id=f"ext:{dedupe_key}",
            ),
            case_association=CaseAssociationInput(rental_case_id=rental_case_id),
            observations=(
                StructuredObservationCandidate(
                    reported_field_code=reported_field_code,
                    observation_type=observation_type,
                    claim_kind=claim_kind,
                    candidate_value_payload=candidate_value_payload,
                    source_evidence_reference=f"fixture:{dedupe_key}",
                    asserted_by_party_type="operator",
                    asserted_by_reference="fixture:operator",
                    extraction_confidence=1.0,
                ),
            ),
        ),
        repository=repo,
        now=lambda: "2026-08-14T09:00:00Z",
    )


class InquiryIntakeTests(unittest.TestCase):
    def test_complete_initial_inquiry_promotes_all_four_core_fields(self) -> None:
        repo = make_repo(rental_cases=(make_case(),))
        ingest_candidate(
            repo,
            dedupe_key="complete-schedule",
            reported_field_code="active_event_window",
            observation_type=OBSERVATION_TYPE_REQUEST_CANDIDATE,
            claim_kind=OBSERVATION_CLAIM_KIND_NEW_INFORMATION,
            candidate_value_payload={
                "active_event_start": "2026-10-03T18:00:00Z",
                "active_event_end": "2026-10-03T22:00:00Z",
            },
        )
        ingest_candidate(
            repo,
            dedupe_key="complete-guests",
            reported_field_code="guest_count",
            observation_type=OBSERVATION_TYPE_FACT_CANDIDATE,
            claim_kind=OBSERVATION_CLAIM_KIND_NEW_INFORMATION,
            candidate_value_payload=35,
        )
        ingest_candidate(
            repo,
            dedupe_key="complete-scope",
            reported_field_code="requested_rental_scope",
            observation_type=OBSERVATION_TYPE_FACT_CANDIDATE,
            claim_kind=OBSERVATION_CLAIM_KIND_NEW_INFORMATION,
            candidate_value_payload="entire_venue",
        )
        ingest_candidate(
            repo,
            dedupe_key="complete-event-type",
            reported_field_code="event_type",
            observation_type=OBSERVATION_TYPE_FACT_CANDIDATE,
            claim_kind=OBSERVATION_CLAIM_KIND_NEW_INFORMATION,
            candidate_value_payload="brand_activation",
        )

        result = apply_inquiry_intake(
            repo,
            rental_case_id=1,
            actor_reference="fixture:operator",
            actor_type="operator",
            now=lambda: "2026-08-14T10:00:00Z",
        )

        self.assertFalse(result.failure_codes)
        self.assertEqual(result.case_revision_before, 0)
        self.assertEqual(result.case_revision_after, 1)
        self.assertEqual(repo.rental_cases[1].rental_type_code, "entire_venue")
        self.assertEqual(repo.rental_cases[1].active_event_start, "2026-10-03T18:00:00Z")
        self.assertEqual(repo.rental_cases[1].active_event_end, "2026-10-03T22:00:00Z")
        self.assertEqual(repo.rental_case_facts[1][0].field_code, "guest_count")
        self.assertEqual(repo.rental_case_facts[1][0].value_payload, 35)
        event_type_fact = next(fact for fact in repo.rental_case_facts[1] if fact.field_code == "event_type")
        self.assertEqual(event_type_fact.value_payload, "brand_activation")
        self.assertEqual(repo.open_questions.get(1, []), [])

    def test_empty_inquiry_creates_four_idempotent_open_questions(self) -> None:
        repo = make_repo(rental_cases=(make_case(),))

        first = apply_inquiry_intake(
            repo,
            rental_case_id=1,
            actor_reference="fixture:operator",
            actor_type="operator",
            now=lambda: "2026-08-14T10:00:00Z",
        )
        second = apply_inquiry_intake(
            repo,
            rental_case_id=1,
            actor_reference="fixture:operator",
            actor_type="operator",
            now=lambda: "2026-08-14T10:05:00Z",
        )

        self.assertFalse(first.failure_codes)
        self.assertEqual(len(repo.open_questions[1]), 4)
        self.assertEqual(first.case_revision_after, 1)
        self.assertEqual(second.case_revision_before, 1)
        self.assertEqual(second.case_revision_after, 1)
        self.assertEqual(len(repo.open_questions[1]), 4)

    def test_partial_inquiry_promotes_known_fields_and_questions_unresolved_fields(self) -> None:
        repo = make_repo(rental_cases=(make_case(),))
        ingest_candidate(
            repo,
            dedupe_key="partial-date",
            reported_field_code="active_event_window",
            observation_type=OBSERVATION_TYPE_REQUEST_CANDIDATE,
            claim_kind=OBSERVATION_CLAIM_KIND_NEW_INFORMATION,
            candidate_value_payload={"active_event_start": "2026-11-15T18:00:00Z"},
        )
        ingest_candidate(
            repo,
            dedupe_key="partial-guests",
            reported_field_code="guest_count",
            observation_type=OBSERVATION_TYPE_FACT_CANDIDATE,
            claim_kind=OBSERVATION_CLAIM_KIND_NEW_INFORMATION,
            candidate_value_payload=25,
        )
        ingest_candidate(
            repo,
            dedupe_key="partial-event-type",
            reported_field_code="event_type",
            observation_type=OBSERVATION_TYPE_FACT_CANDIDATE,
            claim_kind=OBSERVATION_CLAIM_KIND_NEW_INFORMATION,
            candidate_value_payload="corporate_networking",
        )

        result = apply_inquiry_intake(
            repo,
            rental_case_id=1,
            actor_reference="fixture:operator",
            actor_type="operator",
            now=lambda: "2026-08-14T10:00:00Z",
        )

        self.assertFalse(result.failure_codes)
        guest_fact = next(fact for fact in repo.rental_case_facts[1] if fact.field_code == "guest_count")
        event_type_fact = next(fact for fact in repo.rental_case_facts[1] if fact.field_code == "event_type")
        self.assertEqual(guest_fact.value_payload, 25)
        self.assertEqual(event_type_fact.value_payload, "corporate_networking")
        question_types = {question.question_type for question in repo.open_questions[1]}
        self.assertIn("requested_event_timing", question_types)
        self.assertIn("requested_rental_scope", question_types)
        self.assertNotIn("expected_guest_count", question_types)
        self.assertNotIn("requested_event_type", question_types)

    def test_later_valid_guest_value_resolves_open_question(self) -> None:
        repo = make_repo(rental_cases=(make_case(),))
        apply_inquiry_intake(
            repo,
            rental_case_id=1,
            actor_reference="fixture:operator",
            actor_type="operator",
            now=lambda: "2026-08-14T10:00:00Z",
        )
        ingest_candidate(
            repo,
            dedupe_key="resolve-guest-count",
            reported_field_code="guest_count",
            observation_type=OBSERVATION_TYPE_FACT_CANDIDATE,
            claim_kind=OBSERVATION_CLAIM_KIND_NEW_INFORMATION,
            candidate_value_payload=35,
        )

        result = apply_inquiry_intake(
            repo,
            rental_case_id=1,
            actor_reference="fixture:operator",
            actor_type="operator",
            now=lambda: "2026-08-14T10:05:00Z",
        )

        self.assertFalse(result.failure_codes)
        guest_fact = next(fact for fact in repo.rental_case_facts[1] if fact.field_code == "guest_count")
        self.assertEqual(guest_fact.value_payload, 35)
        guest_question = next(question for question in repo.open_questions[1] if question.question_type == "expected_guest_count")
        self.assertEqual(guest_question.status, "resolved")
        self.assertIsNotNone(guest_question.resolved_at)

    def test_conflicting_initial_guest_count_creates_question_without_promoting_current(self) -> None:
        repo = make_repo(rental_cases=(make_case(),))
        ingest_candidate(
            repo,
            dedupe_key="conflict-35",
            reported_field_code="guest_count",
            observation_type=OBSERVATION_TYPE_FACT_CANDIDATE,
            claim_kind=OBSERVATION_CLAIM_KIND_NEW_INFORMATION,
            candidate_value_payload=35,
        )
        ingest_candidate(
            repo,
            dedupe_key="conflict-60",
            reported_field_code="guest_count",
            observation_type=OBSERVATION_TYPE_FACT_CANDIDATE,
            claim_kind=OBSERVATION_CLAIM_KIND_NEW_INFORMATION,
            candidate_value_payload=60,
        )

        result = apply_inquiry_intake(
            repo,
            rental_case_id=1,
            actor_reference="fixture:operator",
            actor_type="operator",
            now=lambda: "2026-08-14T10:00:00Z",
        )

        self.assertFalse(result.failure_codes)
        self.assertEqual(repo.rental_case_facts.get(1, []), [])
        self.assertTrue(any(question.question_type == "expected_guest_count" for question in repo.open_questions[1]))

    def test_existing_scope_change_creates_governed_proposed_change(self) -> None:
        repo = make_repo(rental_cases=(make_case(rental_type_code="studio_space"),))
        ingest_candidate(
            repo,
            dedupe_key="scope-change",
            reported_field_code="requested_rental_scope",
            observation_type=OBSERVATION_TYPE_REQUEST_CANDIDATE,
            claim_kind=OBSERVATION_CLAIM_KIND_CHANGE_REQUEST,
            candidate_value_payload="entire_venue",
        )

        result = apply_inquiry_intake(
            repo,
            rental_case_id=1,
            actor_reference="fixture:operator",
            actor_type="operator",
            now=lambda: "2026-08-14T10:00:00Z",
        )

        self.assertFalse(result.failure_codes)
        self.assertEqual(repo.rental_cases[1].rental_type_code, "studio_space")
        self.assertEqual(len(repo.proposed_changes[1]), 1)
        self.assertEqual(repo.proposed_changes[1][0].change_kind, "requested_rental_scope")
        self.assertEqual(repo.proposed_changes[1][0].proposed_value_payload, "entire_venue")

    def test_existing_event_type_change_creates_governed_proposed_change(self) -> None:
        repo = make_repo(
            rental_cases=(make_case(),),
            facts={
                1: [
                    make_fact(
                        field_code="event_type",
                        value_payload="photo_shoot",
                    )
                ]
            },
        )
        ingest_candidate(
            repo,
            dedupe_key="event-type-change",
            reported_field_code="event_type",
            observation_type=OBSERVATION_TYPE_FACT_CANDIDATE,
            claim_kind=OBSERVATION_CLAIM_KIND_CHANGE_REQUEST,
            candidate_value_payload="brand_activation",
        )

        result = apply_inquiry_intake(
            repo,
            rental_case_id=1,
            actor_reference="fixture:operator",
            actor_type="operator",
            now=lambda: "2026-08-14T10:00:00Z",
        )

        self.assertFalse(result.failure_codes)
        event_type_fact = next(fact for fact in repo.rental_case_facts[1] if fact.field_code == "event_type")
        self.assertEqual(event_type_fact.value_payload, "photo_shoot")
        self.assertEqual(len(repo.proposed_changes[1]), 1)
        self.assertEqual(repo.proposed_changes[1][0].change_kind, "event_type")
        self.assertEqual(repo.proposed_changes[1][0].proposed_value_payload, "brand_activation")

    def test_existing_schedule_change_reuses_existing_reschedule_without_duplicate_second_run(self) -> None:
        repo = make_repo(
            rental_cases=(
                make_case(
                    rental_type_code="studio_space",
                    active_event_start="2026-10-03T18:00:00Z",
                    active_event_end="2026-10-03T22:00:00Z",
                ),
            )
        )
        ingest_candidate(
            repo,
            dedupe_key="schedule-change",
            reported_field_code="active_event_window",
            observation_type=OBSERVATION_TYPE_REQUEST_CANDIDATE,
            claim_kind=OBSERVATION_CLAIM_KIND_CHANGE_REQUEST,
            candidate_value_payload={
                "active_event_start": "2026-10-10T18:00:00Z",
                "active_event_end": "2026-10-10T22:00:00Z",
            },
        )

        result = apply_inquiry_intake(
            repo,
            rental_case_id=1,
            actor_reference="fixture:operator",
            actor_type="operator",
            now=lambda: "2026-08-14T10:00:00Z",
        )
        repeat = apply_inquiry_intake(
            repo,
            rental_case_id=1,
            actor_reference="fixture:operator",
            actor_type="operator",
            now=lambda: "2026-08-14T10:05:00Z",
        )

        self.assertFalse(result.failure_codes)
        self.assertEqual(repo.rental_cases[1].case_revision, 1)
        self.assertEqual(len(repo.reschedule_requests[1]), 1)

    def test_existing_schedule_in_database_format_does_not_create_noop_reschedule(self) -> None:
        repo = make_repo(
            rental_cases=(
                make_case(
                    rental_type_code="studio_space",
                    active_event_start="2026-10-03 18:00:00+00",
                    active_event_end="2026-10-03 22:00:00+00",
                ),
            )
            ,
            facts={
                1: [
                    make_fact(field_code="guest_count", value_payload=35),
                    make_fact(field_code="event_type", value_payload="brand_activation"),
                ]
            },
        )
        ingest_candidate(
            repo,
            dedupe_key="matching-schedule-db-format",
            reported_field_code="active_event_window",
            observation_type=OBSERVATION_TYPE_REQUEST_CANDIDATE,
            claim_kind=OBSERVATION_CLAIM_KIND_NEW_INFORMATION,
            candidate_value_payload={
                "active_event_start": "2026-10-03T18:00:00Z",
                "active_event_end": "2026-10-03T22:00:00Z",
            },
        )

        result = apply_inquiry_intake(
            repo,
            rental_case_id=1,
            actor_reference="fixture:operator",
            actor_type="operator",
            now=lambda: "2026-08-14T10:00:00Z",
        )

        self.assertFalse(result.failure_codes)
        self.assertEqual(result.case_revision_before, 0)
        self.assertEqual(result.case_revision_after, 0)
        self.assertEqual(repo.reschedule_requests.get(1, []), [])

    def test_stale_plan_commit_is_rejected(self) -> None:
        repo = make_repo(rental_cases=(make_case(),))
        ingest_candidate(
            repo,
            dedupe_key="stale-guest-count",
            reported_field_code="guest_count",
            observation_type=OBSERVATION_TYPE_FACT_CANDIDATE,
            claim_kind=OBSERVATION_CLAIM_KIND_NEW_INFORMATION,
            candidate_value_payload=45,
        )
        snapshot = repo.load_case_snapshot(1)
        self.assertIsNotNone(snapshot)
        plan = evaluate_inquiry_intake(
            snapshot=snapshot,
            observations=repo.list_observations_for_case(1),
            effects=repo.list_effects_for_case(1),
            expected_revision=0,
        )
        repo.rental_cases[1] = replace(repo.rental_cases[1], case_revision=1, updated_at="2026-08-14T09:30:00Z")

        result = repo.commit_inquiry_intake_plan(
            plan,
            actor_reference="fixture:operator",
            actor_type="operator",
            applied_at="2026-08-14T10:00:00Z",
        )

        self.assertEqual(result.failure_codes, ("stale_case_revision",))
        self.assertEqual(repo.rental_case_facts.get(1, []), [])

    def test_cross_case_observation_cannot_mutate_a_different_case(self) -> None:
        repo = make_repo(rental_cases=(make_case(rental_case_id=1), make_case(rental_case_id=2)))
        ingest_candidate(
            repo,
            rental_case_id=1,
            dedupe_key="case-one-guest-count",
            reported_field_code="guest_count",
            observation_type=OBSERVATION_TYPE_FACT_CANDIDATE,
            claim_kind=OBSERVATION_CLAIM_KIND_NEW_INFORMATION,
            candidate_value_payload=35,
        )

        result = apply_inquiry_intake(
            repo,
            rental_case_id=2,
            actor_reference="fixture:operator",
            actor_type="operator",
            now=lambda: "2026-08-14T10:00:00Z",
        )

        self.assertFalse(result.failure_codes)
        self.assertEqual(repo.rental_case_facts.get(2, []), [])
        self.assertEqual(len(repo.open_questions[2]), 4)
        self.assertEqual(repo.rental_case_facts.get(1, []), [])
        self.assertEqual(repo.rental_cases[1].case_revision, 0)


if __name__ == "__main__":
    unittest.main()
