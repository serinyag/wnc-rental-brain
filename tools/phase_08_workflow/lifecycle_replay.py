from __future__ import annotations

from .contracts import LifecycleTransition, RentalCase
from .lifecycle_engine import NORMAL_TRANSITION_GRAPH
from .lifecycle_types import (
    LifecycleHistoryValidationResult,
    LIFECYCLE_FAILURE_GUARD_FAILED,
    LIFECYCLE_FAILURE_TRANSITION_NOT_ALLOWED,
)


def validate_lifecycle_history(
    rental_case: RentalCase,
    transitions: tuple[LifecycleTransition, ...] | list[LifecycleTransition],
) -> LifecycleHistoryValidationResult:
    ordered = tuple(sorted(transitions, key=lambda item: (item.case_revision_before, item.case_revision_after, item.lifecycle_transition_id)))
    if not ordered:
        return LifecycleHistoryValidationResult(
            rental_case_id=rental_case.rental_case_id,
            valid=(rental_case.case_revision == 0),
            final_state_matches=True,
            final_revision_matches=(rental_case.case_revision == 0),
            illegal_edge_detected=False,
            revision_gap_detected=False,
            chain_break_detected=False,
            reason_codes=() if rental_case.case_revision == 0 else (LIFECYCLE_FAILURE_GUARD_FAILED,),
        )

    illegal_edge_detected = False
    revision_gap_detected = False
    chain_break_detected = False
    reason_codes: list[str] = []

    previous_transition: LifecycleTransition | None = None
    for transition in ordered:
        if transition.from_lifecycle_state is None:
            chain_break_detected = True
        if transition.case_revision_after != transition.case_revision_before + 1:
            revision_gap_detected = True
        if previous_transition is not None:
            if transition.case_revision_before != previous_transition.case_revision_after:
                revision_gap_detected = True
            if transition.from_lifecycle_state != previous_transition.to_lifecycle_state:
                chain_break_detected = True
        if (
            transition.from_lifecycle_state is not None
            and not transition.override_applied
            and transition.to_lifecycle_state not in NORMAL_TRANSITION_GRAPH.get(transition.from_lifecycle_state, ())
        ):
            illegal_edge_detected = True
        previous_transition = transition

    final_transition = ordered[-1]
    final_state_matches = final_transition.to_lifecycle_state == rental_case.lifecycle_state
    final_revision_matches = final_transition.case_revision_after == rental_case.case_revision

    if illegal_edge_detected:
        reason_codes.append(LIFECYCLE_FAILURE_TRANSITION_NOT_ALLOWED)
    if revision_gap_detected or chain_break_detected or not final_state_matches or not final_revision_matches:
        reason_codes.append(LIFECYCLE_FAILURE_GUARD_FAILED)

    return LifecycleHistoryValidationResult(
        rental_case_id=rental_case.rental_case_id,
        valid=not any((illegal_edge_detected, revision_gap_detected, chain_break_detected, not final_state_matches, not final_revision_matches)),
        final_state_matches=final_state_matches,
        final_revision_matches=final_revision_matches,
        illegal_edge_detected=illegal_edge_detected,
        revision_gap_detected=revision_gap_detected,
        chain_break_detected=chain_break_detected,
        reason_codes=tuple(dict.fromkeys(reason_codes)),
    )
