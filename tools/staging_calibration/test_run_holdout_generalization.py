from __future__ import annotations

import unittest
import json
import hashlib
from pathlib import Path

from tools.staging_calibration.run_holdout_generalization import _classify_system_state, validate_holdout_schema
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

    def test_original_holdout2_is_archived_byte_for_byte(self) -> None:
        root = Path(__file__).resolve().parents[2]
        original = root / "docs/staging/calibration/holdout2_scenarios.json"
        archive = root / "docs/staging/calibration/holdout2_scenarios_original_v1.json"
        self.assertEqual(archive.read_bytes(), original.read_bytes())
        self.assertEqual(
            hashlib.sha256(archive.read_bytes()).hexdigest(),
            "a2f99889c36d8853fc2feb5c370e08b4e2171510898dd7a0c0323a72ac2034c8",
        )

    def test_adjudicated_holdout2_schema_is_compatible_without_hosted_execution(self) -> None:
        root = Path(__file__).resolve().parents[2]
        payload = json.loads((root / "docs/staging/calibration/holdout2_scenarios_adjudicated_v2.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_holdout_schema(payload), [])

    def test_adjudicated_gold_and_waiting_stage_corrections_are_present(self) -> None:
        root = Path(__file__).resolve().parents[2]
        payload = json.loads((root / "docs/staging/calibration/holdout2_scenarios_adjudicated_v2.json").read_text(encoding="utf-8"))
        scenarios = {item["scenario_id"]: item for item in payload["scenarios"]}
        self.assertEqual(scenarios["HOLD2-001"]["expected_state"], "known_conditional")
        self.assertEqual(scenarios["HOLD2-005"]["expected_state"], "known_no")
        self.assertEqual(scenarios["HOLD2-007"]["expected_state"], "known_conditional")
        catering = next(item for item in scenarios["HOLD2-002"]["material_propositions"] if item["proposition"] == "catering:external_caterer")
        self.assertEqual(catering["evaluation_evidence"], "isolated_case_outcome")
        for scenario_id in ("HOLD2-009", "HOLD2-010", "HOLD2-011"):
            self.assertTrue(any(stage["run_waiting"] for stage in scenarios[scenario_id]["stages"]))

    def test_unknown_frozen_action_label_fails_schema_validation(self) -> None:
        payload = {
            "scenario_count": 1,
            "scenarios": [
                {
                    "scenario_id": "HOLD2-X",
                    "expected_state": "known_yes",
                    "expected_next_action": "anything_goes",
                    "expected_system_assertions": {},
                    "material_propositions": [],
                }
            ],
        }
        self.assertIn("unsupported", " ".join(validate_holdout_schema(payload)).lower())

    def test_client_action_requires_waiting_stage(self) -> None:
        payload = {
            "scenario_count": 1,
            "scenarios": [
                {
                    "scenario_id": "HOLD2-X",
                    "expected_state": "missing_client_fact",
                    "expected_next_action": "ask_client",
                    "expected_system_assertions": {},
                    "material_propositions": [],
                    "stages": [{"run_waiting": False}],
                }
            ],
        }
        self.assertIn("run_waiting", " ".join(validate_holdout_schema(payload)))


if __name__ == "__main__":
    unittest.main()
