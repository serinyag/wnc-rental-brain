from __future__ import annotations

import inspect
import unittest

from tools.phase_08_workflow.contracts import (
    ACTION_CATEGORY_COMMUNICATION,
    ACTION_TYPE_SEND_PROPOSAL_MESSAGE,
    APPROVAL_REQUEST_STATUS_OPEN,
    ARTIFACT_FRESHNESS_CURRENT,
    ARTIFACT_TYPE_PROPOSAL,
    BLOCKER_STATUS_OPEN,
    BLOCKING_SCOPE_ACTION,
    BLOCKING_SCOPE_READINESS,
    BLOCKING_SCOPE_TRANSITION,
    CHANGE_IMPACT_LOW,
    CHANGE_IMPACT_MATERIAL,
    FOLLOW_UP_STATUS_SCHEDULED,
    LIFECYCLE_STATE_CANCELLED,
    LIFECYCLE_STATE_CLOSE_OUT_IN_PROGRESS,
    LIFECYCLE_STATE_CLOSED,
    LIFECYCLE_STATE_CLOSED_LOST,
    LIFECYCLE_STATE_CONFIRMATION_PENDING,
    LIFECYCLE_STATE_CONFIRMED_PRE_EVENT,
    LIFECYCLE_STATE_DORMANT,
    LIFECYCLE_STATE_EVENT_IN_PROGRESS,
    LIFECYCLE_STATE_EVENT_READY,
    LIFECYCLE_STATE_INQUIRY_ACTIVE,
    LIFECYCLE_STATE_PROPOSAL_IN_PROGRESS,
    LIFECYCLE_STATE_PROPOSAL_PENDING_CLIENT,
    OPEN_QUESTION_STATUS_OPEN,
    PROPOSED_CHANGE_STATUS_PROPOSED,
    REQUIREMENT_STATUS_IN_PROGRESS,
    REQUIREMENT_STATUS_NOT_APPLICABLE,
    REQUIREMENT_STATUS_REQUIRED,
    REQUIREMENT_STATUS_SATISFIED,
    REQUIREMENT_STATUS_UNRESOLVED,
    REQUIREMENT_STATUS_WAIVED,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
    ApprovalRequest,
    ArtifactReference,
    Blocker,
    LifecycleTransition,
    OpenQuestion,
    ProposedCaseChange,
    RentalCase,
    Requirement,
    WorkflowAction,
    WorkflowEvent,
)
from tools.phase_08_workflow.lifecycle_engine import (
    NORMAL_TRANSITION_GRAPH,
    TERMINAL_STATES,
    LifecycleTransitionRejected,
    apply_manual_transition_override,
    apply_transition,
    evaluate_case_state,
    evaluate_transition,
    reevaluate_readiness,
)
from tools.phase_08_workflow.lifecycle_repository import InMemoryLifecycleRepository
from tools.phase_08_workflow.lifecycle_types import ManualTransitionOverrideRequest


def make_case(
    lifecycle_state: str,
    *,
    case_revision: int = 0,
    rental_case_id: int = 1,
    client_account_ref: str | None = "client:1",
    primary_contact_ref: str | None = "contact:1",
    current_proposal_artifact_id: int | None = None,
    resume_target_state: str | None = None,
) -> RentalCase:
    return RentalCase(
        rental_case_id=rental_case_id,
        rental_case_uuid=f"case-{rental_case_id}",
        case_reference_code=f"RC-{900 + rental_case_id}",
        lifecycle_state=lifecycle_state,
        case_revision=case_revision,
        rental_type_code="studio_space",
        commercial_summary_status="unknown",
        operational_summary_status="unknown",
        is_active=True,
        service_level_or_type="studio_rental",
        client_account_ref=client_account_ref,
        primary_contact_ref=primary_contact_ref,
        current_proposal_artifact_id=current_proposal_artifact_id,
        resume_target_state=resume_target_state,
        created_at="2026-08-09T10:00:00Z",
        updated_at="2026-08-09T10:00:00Z",
    )


def make_repo(
    rental_case: RentalCase,
    *,
    blockers=(),
    requirements=(),
    questions=(),
    approvals=(),
    changes=(),
    decisions=(),
    actions=(),
    events=(),
    artifacts=(),
    transitions=(),
) -> InMemoryLifecycleRepository:
    rental_case_id = rental_case.rental_case_id
    return InMemoryLifecycleRepository(
        rental_cases={rental_case_id: rental_case},
        blockers={rental_case_id: list(blockers)},
        requirements={rental_case_id: list(requirements)},
        open_questions={rental_case_id: list(questions)},
        approval_requests={rental_case_id: list(approvals)},
        proposed_changes={rental_case_id: list(changes)},
        case_decisions={rental_case_id: list(decisions)},
        workflow_actions={rental_case_id: list(actions)},
        workflow_events={rental_case_id: list(events)},
        artifacts={rental_case_id: list(artifacts)},
        lifecycle_transitions={rental_case_id: list(transitions)},
    )


def make_blocker(blocker_id: int, *, reference: str, blocked_subject_type: str = "transition", status: str = BLOCKER_STATUS_OPEN) -> Blocker:
    return Blocker(
        blocker_id=blocker_id,
        rental_case_id=1,
        blocker_type="material_issue",
        blocked_subject_type=blocked_subject_type,
        blocked_subject_reference=reference,
        origin_entity_type="test_fixture",
        origin_entity_reference=f"origin:{blocker_id}",
        severity=SEVERITY_HIGH if reference == "proposal_pending_client" else SEVERITY_MEDIUM,
        status=status,
        resolution_condition_text="Resolve the issue",
        opened_at="2026-08-09T10:00:00Z",
    )


def make_question(question_id: int, *, blocking_scope: str) -> OpenQuestion:
    return OpenQuestion(
        open_question_id=question_id,
        rental_case_id=1,
        question_type="missing_detail",
        domain_code="operations",
        human_question_text="Need one more detail",
        blocking_scope=blocking_scope,
        status=OPEN_QUESTION_STATUS_OPEN,
        created_at="2026-08-09T10:00:00Z",
    )


def make_requirement(requirement_id: int, *, status: str, blocking_scope: str) -> Requirement:
    return Requirement(
        requirement_id=requirement_id,
        rental_case_id=1,
        requirement_type="confirmation_requirement",
        domain_code="commercial",
        applicability_basis="booking_confirmation",
        status=status,
        blocking_scope=blocking_scope,
        created_at="2026-08-09T10:00:00Z",
    )


def make_approval(approval_request_id: int, *, target_entity_reference: str, approval_type: str = "commercial_exception") -> ApprovalRequest:
    return ApprovalRequest(
        approval_request_id=approval_request_id,
        rental_case_id=1,
        target_entity_type="lifecycle_gate",
        target_entity_reference=target_entity_reference,
        approval_type=approval_type,
        reason_text="Needs review",
        status=APPROVAL_REQUEST_STATUS_OPEN,
        created_at="2026-08-09T10:00:00Z",
    )


def make_change(change_id: int, *, impact: str, status: str = PROPOSED_CHANGE_STATUS_PROPOSED) -> ProposedCaseChange:
    return ProposedCaseChange(
        proposed_case_change_id=change_id,
        rental_case_id=1,
        change_kind="scope_change",
        domain_code="commercial",
        proposed_value_payload={"scope": "expanded"},
        status=status,
        detected_at="2026-08-09T10:00:00Z",
        impact_classification=impact,
    )


def make_event(event_id: int, event_type_code: str, payload: dict[str, object]) -> WorkflowEvent:
    return WorkflowEvent(
        workflow_event_id=event_id,
        workflow_event_uuid=f"event-{event_id}",
        rental_case_id=1,
        event_type_code=event_type_code,
        source_type="fixture",
        occurred_at="2026-08-09T10:00:00Z",
        recorded_at="2026-08-09T10:00:00Z",
        structured_payload=payload,
    )


def make_action(action_id: int, *, action_type: str, status: str) -> WorkflowAction:
    return WorkflowAction(
        workflow_action_id=action_id,
        workflow_action_uuid=f"action-{action_id}",
        rental_case_id=1,
        action_type=action_type,
        action_category=ACTION_CATEGORY_COMMUNICATION,
        target_adapter_code="email",
        reason_entity_type="fixture",
        reason_entity_reference=f"reason:{action_id}",
        approval_posture="approval_required",
        status=status,
        semantic_subject_hash=f"hash:{action_id}",
        source_case_revision=0,
        idempotency_key=f"idem:{action_id}",
        structured_payload={"fixture": True},
    )


def make_artifact(artifact_id: int, *, freshness_status: str = ARTIFACT_FRESHNESS_CURRENT) -> ArtifactReference:
    return ArtifactReference(
        artifact_reference_id=artifact_id,
        rental_case_id=1,
        artifact_type=ARTIFACT_TYPE_PROPOSAL,
        derived_from_case_revision=0,
        freshness_status=freshness_status,
        storage_reference=f"artifact:{artifact_id}",
    )


class LifecycleEngineTests(unittest.TestCase):
    def test_frozen_transition_graph_is_exhaustive_across_all_state_pairs(self) -> None:
        states = tuple(NORMAL_TRANSITION_GRAPH.keys())
        for current_state in states:
            repo = make_repo(make_case(current_state))
            for target_state in states:
                evaluation = evaluate_transition(repo, 1, target_state)
                expected_edge = target_state in NORMAL_TRANSITION_GRAPH[current_state]
                if target_state == current_state:
                    expected_edge = False
                self.assertEqual(
                    evaluation.edge_allowed,
                    expected_edge,
                    msg=f"{current_state} -> {target_state}",
                )

    def test_proposal_ready_threshold_allows_non_material_open_question(self) -> None:
        repo = make_repo(
            make_case(LIFECYCLE_STATE_PROPOSAL_IN_PROGRESS, current_proposal_artifact_id=11),
            questions=(make_question(1, blocking_scope=BLOCKING_SCOPE_ACTION),),
            artifacts=(make_artifact(11),),
            events=(make_event(9, "proposal_sent", {"proposal_dispatched": True}),),
        )
        evaluation = evaluate_transition(repo, 1, LIFECYCLE_STATE_PROPOSAL_PENDING_CLIENT)
        self.assertTrue(evaluation.allowed)

    def test_proposal_ready_threshold_rejects_material_blocker(self) -> None:
        repo = make_repo(
            make_case(LIFECYCLE_STATE_PROPOSAL_IN_PROGRESS, current_proposal_artifact_id=11),
            blockers=(make_blocker(2, reference="proposal_pending_client"),),
            artifacts=(make_artifact(11),),
            events=(make_event(9, "proposal_sent", {"proposal_dispatched": True}),),
        )
        evaluation = evaluate_transition(repo, 1, LIFECYCLE_STATE_PROPOSAL_PENDING_CLIENT)
        self.assertFalse(evaluation.allowed)
        self.assertIn(2, evaluation.blocking_blocker_ids)

    def test_proposal_ready_threshold_rejects_material_question(self) -> None:
        repo = make_repo(
            make_case(LIFECYCLE_STATE_PROPOSAL_IN_PROGRESS, current_proposal_artifact_id=11),
            questions=(make_question(3, blocking_scope=BLOCKING_SCOPE_TRANSITION),),
            artifacts=(make_artifact(11),),
            events=(make_event(9, "proposal_sent", {"proposal_dispatched": True}),),
        )
        evaluation = evaluate_transition(repo, 1, LIFECYCLE_STATE_PROPOSAL_PENDING_CLIENT)
        self.assertFalse(evaluation.allowed)
        self.assertIn(3, evaluation.blocking_open_question_ids)

    def test_relevant_proposal_approval_blocks_but_unrelated_approval_does_not(self) -> None:
        base_repo = make_repo(
            make_case(LIFECYCLE_STATE_PROPOSAL_IN_PROGRESS, current_proposal_artifact_id=11),
            artifacts=(make_artifact(11),),
            events=(make_event(9, "proposal_sent", {"proposal_dispatched": True}),),
        )
        relevant = make_repo(
            base_repo.rental_cases[1],
            artifacts=base_repo.artifacts[1],
            events=base_repo.workflow_events[1],
            approvals=(make_approval(5, target_entity_reference="lifecycle:proposal_pending_client"),),
        )
        unrelated = make_repo(
            base_repo.rental_cases[1],
            artifacts=base_repo.artifacts[1],
            events=base_repo.workflow_events[1],
            approvals=(make_approval(6, target_entity_reference="lifecycle:event_ready"),),
        )
        self.assertFalse(evaluate_transition(relevant, 1, LIFECYCLE_STATE_PROPOSAL_PENDING_CLIENT).allowed)
        self.assertTrue(evaluate_transition(unrelated, 1, LIFECYCLE_STATE_PROPOSAL_PENDING_CLIENT).allowed)

    def test_confirmation_pending_requires_structured_client_intent(self) -> None:
        repo_without_intent = make_repo(make_case(LIFECYCLE_STATE_PROPOSAL_PENDING_CLIENT))
        blocked = evaluate_transition(repo_without_intent, 1, LIFECYCLE_STATE_CONFIRMATION_PENDING)
        self.assertFalse(blocked.allowed)

        repo_with_freeform_event = make_repo(
            make_case(LIFECYCLE_STATE_PROPOSAL_PENDING_CLIENT),
            events=(make_event(1, "client_message_received", {"message": "yes"}),),
        )
        self.assertFalse(evaluate_transition(repo_with_freeform_event, 1, LIFECYCLE_STATE_CONFIRMATION_PENDING).allowed)

        repo_with_intent = make_repo(
            make_case(LIFECYCLE_STATE_PROPOSAL_PENDING_CLIENT),
            events=(make_event(2, "client_booking_intent_recorded", {"intent_to_book": True}),),
        )
        self.assertTrue(evaluate_transition(repo_with_intent, 1, LIFECYCLE_STATE_CONFIRMATION_PENDING).allowed)

    def test_confirmation_gate_respects_requirement_status_and_scope(self) -> None:
        for status in (REQUIREMENT_STATUS_REQUIRED, REQUIREMENT_STATUS_IN_PROGRESS, REQUIREMENT_STATUS_UNRESOLVED):
            repo = make_repo(
                make_case(LIFECYCLE_STATE_CONFIRMATION_PENDING),
                requirements=(make_requirement(1, status=status, blocking_scope=BLOCKING_SCOPE_TRANSITION),),
            )
            self.assertFalse(evaluate_transition(repo, 1, LIFECYCLE_STATE_CONFIRMED_PRE_EVENT).allowed)

        for status in (REQUIREMENT_STATUS_SATISFIED, REQUIREMENT_STATUS_WAIVED, REQUIREMENT_STATUS_NOT_APPLICABLE):
            repo = make_repo(
                make_case(LIFECYCLE_STATE_CONFIRMATION_PENDING),
                requirements=(make_requirement(1, status=status, blocking_scope=BLOCKING_SCOPE_TRANSITION),),
            )
            self.assertTrue(evaluate_transition(repo, 1, LIFECYCLE_STATE_CONFIRMED_PRE_EVENT).allowed)

        repo_non_confirmation_scope = make_repo(
            make_case(LIFECYCLE_STATE_CONFIRMATION_PENDING),
            requirements=(make_requirement(2, status=REQUIREMENT_STATUS_REQUIRED, blocking_scope=BLOCKING_SCOPE_READINESS),),
        )
        self.assertTrue(evaluate_transition(repo_non_confirmation_scope, 1, LIFECYCLE_STATE_CONFIRMED_PRE_EVENT).allowed)

    def test_event_ready_gate_is_materiality_and_scope_aware(self) -> None:
        passing_repo = make_repo(
            make_case(LIFECYCLE_STATE_CONFIRMED_PRE_EVENT),
            questions=(make_question(1, blocking_scope=BLOCKING_SCOPE_ACTION),),
        )
        self.assertTrue(evaluate_transition(passing_repo, 1, LIFECYCLE_STATE_EVENT_READY).allowed)

        blocker_repo = make_repo(
            make_case(LIFECYCLE_STATE_CONFIRMED_PRE_EVENT),
            blockers=(make_blocker(1, reference="lifecycle:event_ready", blocked_subject_type="readiness"),),
        )
        self.assertFalse(evaluate_transition(blocker_repo, 1, LIFECYCLE_STATE_EVENT_READY).allowed)

        requirement_repo = make_repo(
            make_case(LIFECYCLE_STATE_CONFIRMED_PRE_EVENT),
            requirements=(make_requirement(2, status=REQUIREMENT_STATUS_REQUIRED, blocking_scope=BLOCKING_SCOPE_READINESS),),
        )
        self.assertFalse(evaluate_transition(requirement_repo, 1, LIFECYCLE_STATE_EVENT_READY).allowed)

        change_repo = make_repo(
            make_case(LIFECYCLE_STATE_CONFIRMED_PRE_EVENT),
            changes=(make_change(3, impact=CHANGE_IMPACT_MATERIAL),),
        )
        self.assertFalse(evaluate_transition(change_repo, 1, LIFECYCLE_STATE_EVENT_READY).allowed)

    def test_readiness_degradation_requires_explicit_follow_up_transition(self) -> None:
        event_ready_repo = make_repo(
            make_case(LIFECYCLE_STATE_EVENT_READY),
            blockers=(make_blocker(8, reference="lifecycle:event_ready", blocked_subject_type="readiness"),),
        )
        reeval = reevaluate_readiness(event_ready_repo, 1)
        self.assertFalse(reeval.readiness_passed)
        self.assertTrue(reeval.degradation_allowed)
        self.assertEqual(reeval.degradation_target_state, LIFECYCLE_STATE_CONFIRMED_PRE_EVENT)
        self.assertEqual(event_ready_repo.rental_cases[1].lifecycle_state, LIFECYCLE_STATE_EVENT_READY)

        restored_repo = make_repo(make_case(LIFECYCLE_STATE_CONFIRMED_PRE_EVENT))
        self.assertTrue(evaluate_transition(restored_repo, 1, LIFECYCLE_STATE_EVENT_READY).allowed)

    def test_event_start_and_completion_require_structured_evidence(self) -> None:
        ready_case = make_case(LIFECYCLE_STATE_EVENT_READY)
        blocked_start = evaluate_transition(make_repo(ready_case), 1, LIFECYCLE_STATE_EVENT_IN_PROGRESS)
        self.assertFalse(blocked_start.allowed)

        passed_start = evaluate_transition(
            make_repo(ready_case, events=(make_event(4, "event_started", {"started": True}),)),
            1,
            LIFECYCLE_STATE_EVENT_IN_PROGRESS,
        )
        self.assertTrue(passed_start.allowed)

        in_progress_case = make_case(LIFECYCLE_STATE_EVENT_IN_PROGRESS, case_revision=1)
        blocked_completion = evaluate_transition(make_repo(in_progress_case), 1, LIFECYCLE_STATE_CLOSE_OUT_IN_PROGRESS)
        self.assertFalse(blocked_completion.allowed)
        passed_completion = evaluate_transition(
            make_repo(in_progress_case, events=(make_event(5, "event_completed", {"completed": True}),)),
            1,
            LIFECYCLE_STATE_CLOSE_OUT_IN_PROGRESS,
        )
        self.assertTrue(passed_completion.allowed)
        self.assertFalse(evaluate_transition(make_repo(in_progress_case), 1, LIFECYCLE_STATE_CLOSED).edge_allowed)

    def test_dormancy_and_resume_are_deterministic(self) -> None:
        inquiry_repo = make_repo(make_case(LIFECYCLE_STATE_INQUIRY_ACTIVE))
        dormancy_eval = evaluate_transition(
            inquiry_repo,
            1,
            LIFECYCLE_STATE_DORMANT,
            transition_context={"resume_target_state": LIFECYCLE_STATE_PROPOSAL_PENDING_CLIENT, "dormant_reason_code": "waiting_for_client"},
        )
        self.assertTrue(dormancy_eval.allowed)

        confirmed_repo = make_repo(make_case(LIFECYCLE_STATE_CONFIRMED_PRE_EVENT))
        self.assertFalse(evaluate_transition(confirmed_repo, 1, LIFECYCLE_STATE_DORMANT).edge_allowed)

        dormant_repo = make_repo(make_case(LIFECYCLE_STATE_DORMANT, resume_target_state=LIFECYCLE_STATE_PROPOSAL_PENDING_CLIENT))
        self.assertTrue(evaluate_transition(dormant_repo, 1, LIFECYCLE_STATE_PROPOSAL_PENDING_CLIENT).allowed)
        self.assertFalse(evaluate_transition(dormant_repo, 1, LIFECYCLE_STATE_INQUIRY_ACTIVE).allowed)

        missing_resume_repo = make_repo(make_case(LIFECYCLE_STATE_DORMANT, resume_target_state=None))
        self.assertFalse(evaluate_transition(missing_resume_repo, 1, LIFECYCLE_STATE_PROPOSAL_PENDING_CLIENT).allowed)

    def test_closed_lost_and_cancelled_are_not_interchangeable(self) -> None:
        pre_confirmation_repo = make_repo(make_case(LIFECYCLE_STATE_CONFIRMATION_PENDING))
        self.assertTrue(evaluate_transition(pre_confirmation_repo, 1, LIFECYCLE_STATE_CLOSED_LOST).edge_allowed)

        confirmed_repo = make_repo(make_case(LIFECYCLE_STATE_CONFIRMED_PRE_EVENT))
        self.assertFalse(evaluate_transition(confirmed_repo, 1, LIFECYCLE_STATE_CLOSED_LOST).edge_allowed)
        self.assertTrue(evaluate_transition(confirmed_repo, 1, LIFECYCLE_STATE_CANCELLED).edge_allowed)

    def test_terminal_states_have_no_normal_outbound_transitions(self) -> None:
        all_states = tuple(NORMAL_TRANSITION_GRAPH.keys())
        for current_state in TERMINAL_STATES:
            repo = make_repo(make_case(current_state))
            for target_state in all_states:
                if target_state == current_state:
                    continue
                evaluation = evaluate_transition(repo, 1, target_state)
                self.assertFalse(evaluation.edge_allowed, msg=f"{current_state} -> {target_state}")

    def test_apply_transition_increments_revision_once_and_records_audit_rows(self) -> None:
        repo = make_repo(
            make_case(LIFECYCLE_STATE_EVENT_READY, current_proposal_artifact_id=None),
            events=(make_event(7, "event_started", {"started": True}),),
        )
        result = apply_transition(
            repo,
            1,
            LIFECYCLE_STATE_EVENT_IN_PROGRESS,
            expected_case_revision=0,
            reason_code="event_started",
            actor_reference="operator:1",
        )
        self.assertEqual(result.previous_revision, 0)
        self.assertEqual(result.new_revision, 1)
        self.assertEqual(repo.rental_cases[1].lifecycle_state, LIFECYCLE_STATE_EVENT_IN_PROGRESS)
        self.assertEqual(repo.rental_cases[1].case_revision, 1)
        self.assertEqual(len(repo.lifecycle_transitions[1]), 1)
        self.assertEqual(len(repo.workflow_events[1]), 2)

    def test_stale_revision_rejection_mutates_nothing(self) -> None:
        repo = make_repo(
            make_case(LIFECYCLE_STATE_EVENT_READY, case_revision=4),
            events=(make_event(10, "event_started", {"started": True}),),
        )
        with self.assertRaises(LifecycleTransitionRejected) as cm:
            apply_transition(
                repo,
                1,
                LIFECYCLE_STATE_EVENT_IN_PROGRESS,
                expected_case_revision=3,
                reason_code="event_started",
                actor_reference="operator:2",
            )
        self.assertIn("stale_case_revision", cm.exception.evaluation.reason_codes)
        self.assertEqual(repo.rental_cases[1].case_revision, 4)
        self.assertEqual(repo.rental_cases[1].lifecycle_state, LIFECYCLE_STATE_EVENT_READY)
        self.assertEqual(len(repo.lifecycle_transitions[1]), 0)
        self.assertEqual(len(repo.workflow_events[1]), 1)

    def test_manual_override_allows_terminal_reopen_and_manual_close(self) -> None:
        closed_lost_repo = make_repo(make_case(LIFECYCLE_STATE_CLOSED_LOST))
        with self.assertRaises(LifecycleTransitionRejected):
            apply_transition(
                closed_lost_repo,
                1,
                LIFECYCLE_STATE_INQUIRY_ACTIVE,
                expected_case_revision=0,
                reason_code="reopen",
                actor_reference="operator:3",
            )
        reopen_result = apply_manual_transition_override(
            closed_lost_repo,
            ManualTransitionOverrideRequest(
                rental_case_id=1,
                target_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
                expected_case_revision=0,
                actor_reference="operator:3",
                reason_code="manual_reopen",
                audit_note="Reopened after client re-engaged.",
            ),
        )
        self.assertTrue(reopen_result.manual_override)
        self.assertEqual(closed_lost_repo.rental_cases[1].lifecycle_state, LIFECYCLE_STATE_INQUIRY_ACTIVE)

        close_repo = make_repo(
            make_case(LIFECYCLE_STATE_CLOSE_OUT_IN_PROGRESS),
            requirements=(make_requirement(99, status=REQUIREMENT_STATUS_REQUIRED, blocking_scope=BLOCKING_SCOPE_TRANSITION),),
        )
        with self.assertRaises(LifecycleTransitionRejected):
            apply_transition(
                close_repo,
                1,
                LIFECYCLE_STATE_CLOSED,
                expected_case_revision=0,
                reason_code="close_out_complete",
                actor_reference="operator:4",
            )
        close_result = apply_manual_transition_override(
            close_repo,
            ManualTransitionOverrideRequest(
                rental_case_id=1,
                target_state=LIFECYCLE_STATE_CLOSED,
                expected_case_revision=0,
                actor_reference="operator:4",
                reason_code="manual_close",
                audit_note="Manual close with acknowledged residual admin work.",
            ),
        )
        self.assertEqual(close_result.new_state, LIFECYCLE_STATE_CLOSED)
        self.assertEqual(len(close_repo.requirements[1]), 1)

    def test_evaluate_case_state_reports_outgoing_and_no_recommended_next_state(self) -> None:
        repo = make_repo(make_case(LIFECYCLE_STATE_INQUIRY_ACTIVE))
        case_eval = evaluate_case_state(
            repo,
            1,
            transition_contexts={"dormant": {"resume_target_state": LIFECYCLE_STATE_INQUIRY_ACTIVE, "dormant_reason_code": "client_waiting"}},
        )
        self.assertEqual(case_eval.normal_outgoing_transitions, NORMAL_TRANSITION_GRAPH[LIFECYCLE_STATE_INQUIRY_ACTIVE])
        self.assertIn(LIFECYCLE_STATE_PROPOSAL_IN_PROGRESS, case_eval.eligible_transitions)
        self.assertFalse(hasattr(case_eval, "recommended_next_state"))

    def test_no_phase7_or_llm_deps_exist_in_lifecycle_modules(self) -> None:
        import tools.phase_08_workflow.lifecycle_engine as lifecycle_engine_module
        import tools.phase_08_workflow.lifecycle_guards as lifecycle_guards_module
        import tools.phase_08_workflow.lifecycle_replay as lifecycle_replay_module

        for module in (lifecycle_engine_module, lifecycle_guards_module, lifecycle_replay_module):
            source = inspect.getsource(module)
            self.assertNotIn("phase_07_reasoning", source)
            self.assertNotIn("OpenAI", source)
            self.assertNotIn("answer_text", source)


if __name__ == "__main__":
    unittest.main()
