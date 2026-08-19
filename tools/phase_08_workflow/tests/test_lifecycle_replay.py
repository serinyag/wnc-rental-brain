from __future__ import annotations

import unittest

from tools.phase_08_workflow.contracts import RentalCase, LifecycleTransition
from tools.phase_08_workflow.lifecycle_replay import validate_lifecycle_history


def make_case(state: str, revision: int) -> RentalCase:
    return RentalCase(
        rental_case_id=1,
        rental_case_uuid="case-1",
        case_reference_code="RC-901",
        lifecycle_state=state,
        case_revision=revision,
        rental_type_code="studio_space",
        commercial_summary_status="unknown",
        operational_summary_status="unknown",
        is_active=True,
    )


def make_transition(
    transition_id: int,
    from_state: str | None,
    to_state: str,
    revision_before: int,
    revision_after: int,
    *,
    override_applied: bool = False,
) -> LifecycleTransition:
    return LifecycleTransition(
        lifecycle_transition_id=transition_id,
        rental_case_id=1,
        from_lifecycle_state=from_state,
        to_lifecycle_state=to_state,
        transition_reason_code="fixture",
        case_revision_before=revision_before,
        case_revision_after=revision_after,
        occurred_at="2026-08-09T10:00:00Z",
        override_applied=override_applied,
    )


class LifecycleReplayTests(unittest.TestCase):
    def test_valid_history_replays_cleanly(self) -> None:
        rental_case = make_case("confirmation_pending", 3)
        transitions = (
            make_transition(1, "inquiry_active", "proposal_in_progress", 0, 1),
            make_transition(2, "proposal_in_progress", "proposal_pending_client", 1, 2),
            make_transition(3, "proposal_pending_client", "confirmation_pending", 2, 3),
        )
        result = validate_lifecycle_history(rental_case, transitions)
        self.assertTrue(result.valid)

    def test_illegal_edge_is_detected(self) -> None:
        rental_case = make_case("confirmed_pre_event", 1)
        transitions = (make_transition(1, "inquiry_active", "confirmed_pre_event", 0, 1),)
        result = validate_lifecycle_history(rental_case, transitions)
        self.assertFalse(result.valid)
        self.assertTrue(result.illegal_edge_detected)

    def test_revision_gap_and_chain_break_are_detected(self) -> None:
        rental_case = make_case("proposal_pending_client", 3)
        transitions = (
            make_transition(1, "inquiry_active", "proposal_in_progress", 0, 1),
            make_transition(2, "confirmation_pending", "proposal_pending_client", 2, 3),
        )
        result = validate_lifecycle_history(rental_case, transitions)
        self.assertFalse(result.valid)
        self.assertTrue(result.revision_gap_detected)
        self.assertTrue(result.chain_break_detected)

    def test_final_state_and_revision_mismatch_are_detected(self) -> None:
        rental_case = make_case("proposal_pending_client", 2)
        transitions = (make_transition(1, "inquiry_active", "proposal_in_progress", 0, 1),)
        result = validate_lifecycle_history(rental_case, transitions)
        self.assertFalse(result.valid)
        self.assertFalse(result.final_state_matches)
        self.assertFalse(result.final_revision_matches)

    def test_override_allows_otherwise_illegal_edge(self) -> None:
        rental_case = make_case("confirmed_pre_event", 1)
        transitions = (make_transition(1, "inquiry_active", "confirmed_pre_event", 0, 1, override_applied=True),)
        result = validate_lifecycle_history(rental_case, transitions)
        self.assertTrue(result.valid)


if __name__ == "__main__":
    unittest.main()
