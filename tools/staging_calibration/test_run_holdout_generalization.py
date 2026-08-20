from __future__ import annotations

import unittest

from tools.staging_calibration.run_holdout_generalization import _classify_system_state
from tools.staging_calibration.run_operator_calibration import ScoredCase


def _scored_case(actual: dict[str, object]) -> ScoredCase:
    return ScoredCase(
        scenario_id="HOLD-X",
        category_code="HOLD",
        rental_case_id=1,
        case_reference_code="RC-TEST",
        scores={},
        edit_burden="A",
        critical_failures=(),
        unsupported_claim_count=0,
        factual_correction_count=0,
        missing_info_success=True,
        authority_success=True,
        confidentiality_success=True,
        correct_next_action=True,
        failures=(),
        diagnosed_layer="test",
        root_cause="test",
        actual=actual,
    )


class HoldoutGeneralizationClassificationTests(unittest.TestCase):
    def test_open_questions_take_priority_as_missing_client_fact(self) -> None:
        result = _scored_case(
            {
                "active_open_question_types": ("guest_count",),
                "reasoning_projection_semantic_states": ("known_no",),
                "open_blocker_count": 1,
                "case_decision_statuses": (),
                "commercial_snapshot": {},
                "feasibility_snapshot": {"Confirmation still required": "Yes", "Hard constraint": ""},
            }
        )

        self.assertEqual(_classify_system_state(result), "missing_client_fact")

    def test_known_no_projection_beats_generic_blocker_inference(self) -> None:
        result = _scored_case(
            {
                "active_open_question_types": (),
                "reasoning_projection_semantic_states": ("known_no",),
                "open_blocker_count": 1,
                "case_decision_statuses": (),
                "commercial_snapshot": {},
                "feasibility_snapshot": {"Confirmation still required": "No", "Hard constraint": ""},
            }
        )

        self.assertEqual(_classify_system_state(result), "known_no")

    def test_exception_approval_path_is_treated_as_known_no(self) -> None:
        result = _scored_case(
            {
                "active_open_question_types": (),
                "reasoning_projection_semantic_states": (),
                "open_blocker_count": 1,
                "case_decision_statuses": ("proposed",),
                "commercial_snapshot": {"Case-specific exception": "Pending"},
                "feasibility_snapshot": {
                    "Confirmation still required": "No",
                    "Hard constraint": "Approval must be approved or the proposed case decision must be rejected.",
                },
            }
        )

        self.assertEqual(_classify_system_state(result), "known_no")

    def test_known_conditional_projection_surfaces_as_conditional(self) -> None:
        result = _scored_case(
            {
                "active_open_question_types": (),
                "reasoning_projection_semantic_states": ("known_conditional",),
                "open_blocker_count": 1,
                "case_decision_statuses": (),
                "commercial_snapshot": {},
                "feasibility_snapshot": {"Confirmation still required": "Yes", "Hard constraint": ""},
            }
        )

        self.assertEqual(_classify_system_state(result), "known_conditional")


if __name__ == "__main__":
    unittest.main()
