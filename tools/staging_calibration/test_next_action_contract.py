from __future__ import annotations

from types import SimpleNamespace
import unittest

from tools.staging_calibration.run_operator_calibration import (
    ScenarioExpectations,
    _correct_next_action,
)


def _actual(*, blockers: tuple[str, ...] = (), actions: tuple[str, ...] = (), questions: tuple[str, ...] = (), decisions: tuple[str, ...] = ()) -> SimpleNamespace:
    return SimpleNamespace(
        open_blocker_types=blockers,
        active_workflow_action_types=actions,
        active_open_question_types=questions,
        case_decision_statuses=decisions,
    )


class StateToActionContractTests(unittest.TestCase):
    def test_semantic_state_actions_are_domain_independent(self) -> None:
        cases = (
            ("technical known_yes", "none", _actual()),
            ("capacity known_no", "restriction_or_alternative_needed", _actual(blockers=("deterministic_restriction",))),
            ("supplier known_conditional", "internal_confirmation", _actual(blockers=("confirmation_required",), actions=("CREATE_INTERNAL_TASK_ITEM",))),
            ("facilitator unknown_internal", "internal_confirmation_without_client_question", _actual(blockers=("current_authority_missing",), actions=("CREATE_INTERNAL_TASK_ITEM",))),
            ("timing missing_client_fact", "ask_client", _actual(actions=("REQUEST_CLIENT_INFORMATION",), questions=("requested_event_timing",))),
            ("commercial approval path", "approval_gated_only", _actual(blockers=("case_decision_approval_required",), actions=("CREATE_INTERNAL_TASK_ITEM",), decisions=("proposed",))),
        )

        for label, action, actual in cases:
            with self.subTest(label=label):
                self.assertTrue(_correct_next_action(ScenarioExpectations(expected_next_action=action), actual))

    def test_internal_unknown_cannot_be_scored_as_a_client_follow_up(self) -> None:
        actual = _actual(
            blockers=("current_authority_missing",),
            actions=("REQUEST_CLIENT_INFORMATION",),
            questions=("supplier_details",),
        )

        self.assertFalse(
            _correct_next_action(
                ScenarioExpectations(expected_next_action="internal_confirmation"),
                actual,
            )
        )
