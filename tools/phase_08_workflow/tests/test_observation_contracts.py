from __future__ import annotations

import unittest

from tools.phase_08_workflow.observation_contracts import (
    InboundObservation,
    InboundObservationEffect,
    InboundSourceRecord,
    OBSERVATION_DISPOSITION_CREATE_PROPOSED_CHANGE,
    OBSERVATION_STATUS_VALIDATED,
    OBSERVATION_TYPE_FACT_CANDIDATE,
    SOURCE_ASSOCIATION_STATUS_RESOLVED,
)
from tools.phase_08_workflow.validation import Phase8ContractError


class ObservationContractsTests(unittest.TestCase):
    def test_resolved_source_requires_case_id(self) -> None:
        with self.assertRaisesRegex(Phase8ContractError, "resolved inbound sources require resolved_rental_case_id"):
            InboundSourceRecord(
                inbound_source_record_id=1,
                source_system_code="email",
                source_record_type="message",
                dedupe_key="email:1",
                source_hash="hash-1",
                occurred_at="2026-08-10T10:00:00Z",
                association_status=SOURCE_ASSOCIATION_STATUS_RESOLVED,
                created_at="2026-08-10T10:00:00Z",
            )

    def test_observation_confidence_must_be_bounded(self) -> None:
        with self.assertRaisesRegex(Phase8ContractError, "must be between 0 and 1"):
            InboundObservation(
                inbound_observation_id=1,
                inbound_source_record_id=1,
                reported_field_code="guest_count",
                observation_type=OBSERVATION_TYPE_FACT_CANDIDATE,
                claim_kind="new_information",
                candidate_value_payload=30,
                source_evidence_reference="msg:1#line:3",
                status=OBSERVATION_STATUS_VALIDATED,
                observation_identity_key="obs-1",
                created_at="2026-08-10T10:00:00Z",
                extraction_confidence=1.2,
            )

    def test_effect_requires_linked_target_for_proposed_change_disposition(self) -> None:
        with self.assertRaisesRegex(Phase8ContractError, "require a linked target entity id"):
            InboundObservationEffect(
                inbound_observation_effect_id=1,
                inbound_observation_id=1,
                rental_case_id=1,
                disposition_code=OBSERVATION_DISPOSITION_CREATE_PROPOSED_CHANGE,
                revalidation_required=True,
                stale_observation=False,
                reason_codes=("existing_value_changed",),
                created_at="2026-08-10T10:00:00Z",
            )
