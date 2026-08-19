from __future__ import annotations

import unittest

from tools.phase_08_workflow.observation_contracts import (
    OBSERVATION_TARGET_KIND_CASE_DECISION,
    OBSERVATION_TARGET_KIND_RENTAL_CASE_FACT,
)
from tools.phase_08_workflow.observation_registry import (
    CATERING_ARRANGEMENT_VALUES,
    TECHNICAL_REQUIREMENT_VALUES,
    get_field_definition,
)


class ObservationRegistryTests(unittest.TestCase):
    def test_guest_count_and_booking_fee_registry_entries_are_governed(self) -> None:
        guest_count = get_field_definition("guest_count")
        booking_fee_override = get_field_definition("booking_fee_override")

        self.assertIsNotNone(guest_count)
        self.assertEqual(guest_count.canonical_target_kind, OBSERVATION_TARGET_KIND_RENTAL_CASE_FACT)
        self.assertEqual(guest_count.domain_code, "event_profile")

        self.assertIsNotNone(booking_fee_override)
        self.assertEqual(booking_fee_override.canonical_target_kind, OBSERVATION_TARGET_KIND_CASE_DECISION)
        self.assertEqual(booking_fee_override.canonical_target_reference, "phase4:booking_fee")

    def test_registry_exposes_controlled_enum_values(self) -> None:
        catering = get_field_definition("catering_arrangement")
        technical = get_field_definition("technical_requirements")

        self.assertEqual(set(catering.allowed_enum_values), set(CATERING_ARRANGEMENT_VALUES))
        self.assertEqual(set(technical.allowed_enum_values), set(TECHNICAL_REQUIREMENT_VALUES))

    def test_unknown_field_returns_none(self) -> None:
        self.assertIsNone(get_field_definition("flower_vibe_energy_score"))
