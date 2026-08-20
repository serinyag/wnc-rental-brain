from __future__ import annotations

from dataclasses import replace
import unittest

from tools.phase_08_workflow.contracts import (
    ACTION_CATEGORY_COMMUNICATION,
    ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
    ACTION_TYPE_ESCALATE_COMPLIANCE_REVIEW,
    ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
    APPROVAL_POSTURE_APPROVAL_REQUIRED,
    APPROVAL_POSTURE_HUMAN_ONLY,
    APPROVAL_REQUEST_STATUS_OPEN,
    ARTIFACT_FRESHNESS_CURRENT,
    ARTIFACT_FRESHNESS_REFRESH_REQUIRED,
    ARTIFACT_TYPE_PROPOSAL,
    CASE_DECISION_STATUS_ACTIVE,
    CASE_DECISION_STATUS_PROPOSED,
    LIFECYCLE_STATE_PROPOSAL_IN_PROGRESS,
    OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION,
    OPEN_QUESTION_STATUS_OPEN,
    PROPOSED_CHANGE_STATUS_PROPOSED,
    RESCHEDULE_STATUS_PROPOSED,
    SEVERITY_HIGH,
    ApprovalRequest,
    ArtifactReference,
    CaseDecision,
    OpenQuestion,
    ProposedCaseChange,
    RentalCase,
    RescheduleRequest,
    WorkflowAction,
    WorkflowReasoningProjection,
    WORKFLOW_ACTION_STATUS_APPROVED,
    WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
    WORKFLOW_ACTION_STATUS_CANCELLED,
    WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
    WORKFLOW_REASONING_POSTURE_BLOCKED_FOR_CURRENT_DECISION,
    WORKFLOW_REASONING_POSTURE_GUIDANCE_ONLY,
)
from tools.phase_08_workflow.observation_contracts import RentalCaseFact
from tools.phase_08_workflow.orchestration_repository import InMemoryWorkflowOrchestrationRepository
from tools.phase_08_workflow.orchestration_runtime import (
    apply_approval_decision,
    accept_proposed_case_change,
    build_workflow_orchestration_context,
    evaluate_workflow_orchestration,
    reconcile_workflow_orchestration,
)
from tools.phase_08_workflow.orchestration_types import (
    ApprovalDecisionInput,
    ORCHESTRATION_DECISION_APPROVED,
    ORCHESTRATION_DECISION_REJECTED,
    ORCHESTRATION_FAILURE_CASE_DECISION_CONFLICT,
    ProposedCaseChangeResolutionInput,
)


def make_case(*, case_revision: int = 0, rental_case_id: int = 1) -> RentalCase:
    return RentalCase(
        rental_case_id=rental_case_id,
        rental_case_uuid=f"case-{rental_case_id}",
        case_reference_code=f"RC-{900 + rental_case_id}",
        lifecycle_state=LIFECYCLE_STATE_PROPOSAL_IN_PROGRESS,
        case_revision=case_revision,
        rental_type_code="studio_space",
        commercial_summary_status="unknown",
        operational_summary_status="unknown",
        is_active=True,
        service_level_or_type="studio_rental",
        client_account_ref="client:1",
        primary_contact_ref="contact:1",
        created_at="2026-08-13T10:00:00Z",
        updated_at="2026-08-13T10:00:00Z",
    )


def make_repo(
    rental_case: RentalCase,
    *,
    facts=(),
    blockers=(),
    requirements=(),
    questions=(),
    approvals=(),
    changes=(),
    reschedules=(),
    decisions=(),
    actions=(),
    follow_ups=(),
    milestones=(),
    artifacts=(),
    projections=(),
    events=(),
) -> InMemoryWorkflowOrchestrationRepository:
    rental_case_id = rental_case.rental_case_id
    return InMemoryWorkflowOrchestrationRepository(
        rental_cases={rental_case_id: rental_case},
        rental_case_facts={rental_case_id: list(facts)},
        blockers={rental_case_id: list(blockers)},
        requirements={rental_case_id: list(requirements)},
        open_questions={rental_case_id: list(questions)},
        approval_requests={rental_case_id: list(approvals)},
        proposed_changes={rental_case_id: list(changes)},
        reschedule_requests={rental_case_id: list(reschedules)},
        case_decisions={rental_case_id: list(decisions)},
        workflow_actions={rental_case_id: list(actions)},
        follow_ups={rental_case_id: list(follow_ups)},
        milestones={rental_case_id: list(milestones)},
        artifacts={rental_case_id: list(artifacts)},
        reasoning_projections={rental_case_id: list(projections)},
        workflow_events={rental_case_id: list(events)},
    )


def make_question(
    question_id: int,
    *,
    requested_from_role: str = "client",
    status: str = OPEN_QUESTION_STATUS_OPEN,
) -> OpenQuestion:
    return OpenQuestion(
        open_question_id=question_id,
        rental_case_id=1,
        question_type="expected_guest_count",
        domain_code="operations",
        human_question_text="What is the expected guest count?",
        requested_from_role=requested_from_role,
        blocking_scope="transition",
        status=status,
        created_at="2026-08-13T10:00:00Z",
    )


def make_artifact(artifact_id: int, *, revision: int = 0) -> ArtifactReference:
    return ArtifactReference(
        artifact_reference_id=artifact_id,
        rental_case_id=1,
        artifact_type=ARTIFACT_TYPE_PROPOSAL,
        derived_from_case_revision=revision,
        freshness_status=ARTIFACT_FRESHNESS_CURRENT,
        storage_reference=f"artifact:{artifact_id}",
        created_at="2026-08-13T10:00:00Z",
        updated_at="2026-08-13T10:00:00Z",
    )


def make_decision(
    decision_id: int,
    *,
    status: str = CASE_DECISION_STATUS_PROPOSED,
    scope_key: str = "booking_fee:default",
) -> CaseDecision:
    kwargs = {}
    if status == CASE_DECISION_STATUS_ACTIVE:
        kwargs = {
            "effective_value_payload": {"booking_fee": 0, "waived": True},
            "effective_at": "2026-08-13T10:05:00Z",
            "approval_request_id": 999,
        }
    return CaseDecision(
        case_decision_id=decision_id,
        rental_case_id=1,
        decision_type="booking_fee_waiver",
        domain_code="booking_fee",
        baseline_reference="phase4:booking_fee:50",
        proposed_value_payload={"booking_fee": 0, "waived": True},
        scope_key=scope_key,
        scope_description="booking fee exception",
        authority_basis="case_specific_exception",
        approval_posture=APPROVAL_POSTURE_APPROVAL_REQUIRED,
        status=status,
        created_at="2026-08-13T10:00:00Z",
        evidence_reference="observation:waiver_request",
        **kwargs,
    )


def make_projection(
    *,
    projection_id: int,
    reasoning_purpose: str,
    authority_outcome: str,
    reasoning_state_code: str,
    workflow_posture: str,
    relevant_current_truth_item_ids=(),
    relevant_guidance_item_ids=(),
    unresolved_authority_codes=(),
) -> WorkflowReasoningProjection:
    return WorkflowReasoningProjection(
        reasoning_projection_id=projection_id,
        rental_case_id=1,
        reasoning_purpose=reasoning_purpose,
        phase_7_context_contract_version=1,
        phase_8_workflow_contract_version=1,
        source_case_revision=0,
        authority_outcome_classification=authority_outcome,
        degraded_retrieval_summary={"any_degradation": False},
        created_at="2026-08-13T10:00:00Z",
        projection_identity_key=f"p7wf:{projection_id}",
        reasoning_state_code=reasoning_state_code,
        workflow_posture=workflow_posture,
        effective_confidentiality_level="internal",
        relevant_current_truth_item_ids=relevant_current_truth_item_ids,
        relevant_guidance_item_ids=relevant_guidance_item_ids,
        unresolved_authority_codes=unresolved_authority_codes,
        warning_codes=(),
        grounding_reference_keys=("grounding:1",),
    )


def make_action(
    action_id: int,
    *,
    approval_posture: str = APPROVAL_POSTURE_APPROVAL_REQUIRED,
    status: str = WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
) -> WorkflowAction:
    return WorkflowAction(
        workflow_action_id=action_id,
        workflow_action_uuid=f"action-{action_id}",
        rental_case_id=1,
        action_type=ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
        action_category=ACTION_CATEGORY_COMMUNICATION,
        target_adapter_code="email",
        reason_entity_type="open_question",
        reason_entity_reference=f"open_question:{action_id}",
        approval_posture=approval_posture,
        status=status,
        semantic_subject_hash=f"subject:{action_id}",
        source_case_revision=0,
        idempotency_key=f"idem:{action_id}",
        structured_payload={"question_id": action_id},
        created_at="2026-08-13T10:00:00Z",
        updated_at="2026-08-13T10:00:00Z",
    )


def make_action_approval(approval_request_id: int, *, action_id: int) -> ApprovalRequest:
    return ApprovalRequest(
        approval_request_id=approval_request_id,
        rental_case_id=1,
        target_entity_type="workflow_action",
        target_entity_id=action_id,
        target_entity_reference=f"workflow_action:{action_id}",
        approval_type="workflow_action_release",
        reason_text="Action requires approval before release.",
        status=APPROVAL_REQUEST_STATUS_OPEN,
        created_at="2026-08-13T10:00:00Z",
        updated_at="2026-08-13T10:00:00Z",
    )


class OrchestrationRuntimeTests(unittest.TestCase):
    def test_missing_client_information_is_idempotent(self) -> None:
        repo = make_repo(make_case(), questions=(make_question(1),))
        context = build_workflow_orchestration_context(repo.load_case_snapshot(1))
        plan = evaluate_workflow_orchestration(context, now="2026-08-13T10:00:00Z")
        self.assertEqual(len(plan.proposed_blocker_creations), 1)
        self.assertEqual(len(plan.proposed_action_creations), 0)

        first = reconcile_workflow_orchestration(repo, rental_case_id=1, actor_reference="system:orchestration")
        second = reconcile_workflow_orchestration(repo, rental_case_id=1, actor_reference="system:orchestration")

        self.assertEqual(len(first.created_blocker_ids), 1)
        self.assertEqual(first.created_action_ids, ())
        self.assertEqual(second.created_blocker_ids, ())

    def test_answered_pending_validation_still_blocks_transition(self) -> None:
        repo = make_repo(
            make_case(),
            questions=(
                make_question(
                    1,
                    status=OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION,
                ),
            ),
        )

        result = reconcile_workflow_orchestration(repo, rental_case_id=1, actor_reference="system:orchestration")
        snapshot = repo.load_case_snapshot(1)

        self.assertEqual(len(result.created_blocker_ids), 1)
        self.assertEqual(result.created_action_ids, ())
        self.assertEqual(len(snapshot.blockers), 1)
        self.assertEqual(repo.rental_cases[1].case_revision, 0)

    def test_resolved_question_resolves_blocker_without_emitting_client_action(self) -> None:
        repo = make_repo(make_case(), questions=(make_question(1),))
        first = reconcile_workflow_orchestration(repo, rental_case_id=1, actor_reference="system:orchestration")
        self.assertEqual(first.created_action_ids, ())

        repo.open_questions[1][0] = replace(
            repo.open_questions[1][0],
            status="resolved",
            resolved_at="2026-08-13T11:00:00Z",
        )
        second = reconcile_workflow_orchestration(repo, rental_case_id=1, actor_reference="system:orchestration")

        self.assertEqual(len(second.resolved_blocker_ids), 1)
        self.assertEqual(second.superseded_action_ids, ())
        self.assertEqual(repo.rental_cases[1].lifecycle_state, LIFECYCLE_STATE_PROPOSAL_IN_PROGRESS)

    def test_booking_fee_waiver_requires_approval_then_activates_case_decision(self) -> None:
        repo = make_repo(
            make_case(),
            decisions=(make_decision(1),),
            artifacts=(make_artifact(11),),
        )
        reconcile = reconcile_workflow_orchestration(repo, rental_case_id=1, actor_reference="system:orchestration")
        self.assertEqual(len(reconcile.created_approval_ids), 1)
        self.assertEqual(repo.case_decisions[1][0].status, CASE_DECISION_STATUS_PROPOSED)
        self.assertEqual(repo.rental_cases[1].case_revision, 0)

        approval_result = apply_approval_decision(
            repo,
            ApprovalDecisionInput(
                rental_case_id=1,
                approval_request_id=reconcile.created_approval_ids[0],
                decision=ORCHESTRATION_DECISION_APPROVED,
                expected_case_revision=0,
                actor_reference="manager:1",
            ),
        )

        self.assertEqual(repo.case_decisions[1][0].status, CASE_DECISION_STATUS_ACTIVE)
        self.assertEqual(repo.case_decisions[1][0].effective_value_payload["booking_fee"], 0)
        self.assertEqual(repo.rental_cases[1].case_revision, 1)
        self.assertEqual(repo.artifacts[1][0].freshness_status, ARTIFACT_FRESHNESS_REFRESH_REQUIRED)
        self.assertEqual(approval_result.activated_case_decision_id, 1)

    def test_rejected_waiver_keeps_baseline_and_rejects_case_decision(self) -> None:
        repo = make_repo(make_case(), decisions=(make_decision(1),))
        reconcile = reconcile_workflow_orchestration(repo, rental_case_id=1, actor_reference="system:orchestration")
        approval_result = apply_approval_decision(
            repo,
            ApprovalDecisionInput(
                rental_case_id=1,
                approval_request_id=reconcile.created_approval_ids[0],
                decision=ORCHESTRATION_DECISION_REJECTED,
                expected_case_revision=0,
                actor_reference="manager:1",
            ),
        )
        self.assertEqual(repo.case_decisions[1][0].status, "rejected")
        self.assertEqual(repo.rental_cases[1].case_revision, 0)
        self.assertEqual(approval_result.rejected_case_decision_id, 1)

    def test_workflow_action_approval_advances_to_ready_to_execute(self) -> None:
        repo = make_repo(
            make_case(),
            approvals=(make_action_approval(501, action_id=101),),
            actions=(make_action(101),),
        )

        result = apply_approval_decision(
            repo,
            ApprovalDecisionInput(
                rental_case_id=1,
                approval_request_id=501,
                decision=ORCHESTRATION_DECISION_APPROVED,
                expected_case_revision=0,
                actor_reference="manager:1",
            ),
        )

        self.assertEqual(repo.approval_requests[1][0].status, "approved")
        self.assertEqual(repo.workflow_actions[1][0].status, WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE)
        self.assertEqual(result.approval_status, "approved")
        self.assertEqual(len(result.audit_event_ids), 3)

    def test_human_only_workflow_action_approval_stops_at_approved(self) -> None:
        repo = make_repo(
            make_case(),
            approvals=(make_action_approval(502, action_id=102),),
            actions=(make_action(102, approval_posture=APPROVAL_POSTURE_HUMAN_ONLY),),
        )

        result = apply_approval_decision(
            repo,
            ApprovalDecisionInput(
                rental_case_id=1,
                approval_request_id=502,
                decision=ORCHESTRATION_DECISION_APPROVED,
                expected_case_revision=0,
                actor_reference="manager:1",
            ),
        )

        self.assertEqual(repo.approval_requests[1][0].status, "approved")
        self.assertEqual(repo.workflow_actions[1][0].status, WORKFLOW_ACTION_STATUS_APPROVED)
        self.assertEqual(result.approval_status, "approved")
        self.assertEqual(len(result.audit_event_ids), 2)

    def test_rejected_workflow_action_approval_cancels_action(self) -> None:
        repo = make_repo(
            make_case(),
            approvals=(make_action_approval(503, action_id=103),),
            actions=(make_action(103),),
        )

        result = apply_approval_decision(
            repo,
            ApprovalDecisionInput(
                rental_case_id=1,
                approval_request_id=503,
                decision=ORCHESTRATION_DECISION_REJECTED,
                expected_case_revision=0,
                actor_reference="manager:1",
            ),
        )

        self.assertEqual(repo.approval_requests[1][0].status, "rejected")
        self.assertEqual(repo.workflow_actions[1][0].status, WORKFLOW_ACTION_STATUS_CANCELLED)
        self.assertEqual(result.approval_status, "rejected")
        self.assertEqual(len(result.audit_event_ids), 2)

    def test_replayed_workflow_action_approval_is_idempotent(self) -> None:
        repo = make_repo(
            make_case(),
            approvals=(make_action_approval(504, action_id=104),),
            actions=(make_action(104),),
        )

        first = apply_approval_decision(
            repo,
            ApprovalDecisionInput(
                rental_case_id=1,
                approval_request_id=504,
                decision=ORCHESTRATION_DECISION_APPROVED,
                expected_case_revision=0,
                actor_reference="manager:1",
            ),
        )
        second = apply_approval_decision(
            repo,
            ApprovalDecisionInput(
                rental_case_id=1,
                approval_request_id=504,
                decision=ORCHESTRATION_DECISION_APPROVED,
                expected_case_revision=0,
                actor_reference="manager:1",
            ),
        )

        self.assertEqual(repo.workflow_actions[1][0].status, WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE)
        self.assertEqual(first.approval_status, "approved")
        self.assertEqual(second.approval_status, "approved")
        self.assertEqual(second.audit_event_ids, ())

    def test_case_decision_conflict_fails_closed(self) -> None:
        repo = make_repo(
            make_case(),
            decisions=(make_decision(1, status=CASE_DECISION_STATUS_ACTIVE), make_decision(2)),
        )
        reconcile = reconcile_workflow_orchestration(repo, rental_case_id=1, actor_reference="system:orchestration")
        approval_result = apply_approval_decision(
            repo,
            ApprovalDecisionInput(
                rental_case_id=1,
                approval_request_id=reconcile.created_approval_ids[0],
                decision=ORCHESTRATION_DECISION_APPROVED,
                expected_case_revision=0,
                actor_reference="manager:1",
            ),
        )
        self.assertIn(ORCHESTRATION_FAILURE_CASE_DECISION_CONFLICT, approval_result.failure_codes)
        self.assertEqual(repo.approval_requests[1][0].status, "open")
        self.assertEqual(repo.rental_cases[1].case_revision, 0)

    def test_historical_gap_does_not_create_price_truth(self) -> None:
        repo = make_repo(
            make_case(),
            projections=(
                make_projection(
                    projection_id=1,
                    reasoning_purpose="commercial_rule_review",
                    authority_outcome="INSUFFICIENT_CURRENT_AUTHORITY",
                    reasoning_state_code="insufficient_current_authority",
                    workflow_posture=WORKFLOW_REASONING_POSTURE_BLOCKED_FOR_CURRENT_DECISION,
                    unresolved_authority_codes=("price|insufficient_current_authority",),
                ),
            ),
        )
        result = reconcile_workflow_orchestration(repo, rental_case_id=1, actor_reference="system:orchestration")
        self.assertEqual(len(result.created_blocker_ids), 1)
        self.assertEqual(len(result.created_action_ids), 1)
        self.assertEqual(repo.workflow_actions[1][0].action_type, ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM)
        self.assertEqual(repo.rental_case_facts[1], [])
        self.assertEqual(repo.case_decisions[1], [])

    def test_accepting_proposed_change_mutates_case_fact_once(self) -> None:
        change = ProposedCaseChange(
            proposed_case_change_id=1,
            rental_case_id=1,
            change_kind="guest_count",
            domain_code="operations",
            prior_value_payload=20,
            proposed_value_payload=30,
            status=PROPOSED_CHANGE_STATUS_PROPOSED,
            detected_at="2026-08-13T10:00:00Z",
            source_reference="observation:guest_count",
            impact_classification="material_impact",
            review_posture="automatic_allowed",
            created_at="2026-08-13T10:00:00Z",
            updated_at="2026-08-13T10:00:00Z",
        )
        fact = RentalCaseFact(
            rental_case_fact_id=1,
            rental_case_id=1,
            field_code="guest_count",
            domain_code="operations",
            value_payload=20,
            source_reference="source:initial",
            established_case_revision=0,
            created_at="2026-08-13T10:00:00Z",
            updated_at="2026-08-13T10:00:00Z",
        )
        repo = make_repo(make_case(), facts=(fact,), changes=(change,), artifacts=(make_artifact(11),))
        result = accept_proposed_case_change(
            repo,
            ProposedCaseChangeResolutionInput(
                rental_case_id=1,
                proposed_case_change_id=1,
                decision=ORCHESTRATION_DECISION_APPROVED,
                expected_case_revision=0,
                actor_reference="operator:1",
            ),
        )
        self.assertEqual(result.case_revision_after, 1)
        self.assertEqual(repo.rental_case_facts[1][0].value_payload, 30)
        self.assertEqual(repo.proposed_changes[1][0].status, "accepted")
        self.assertEqual(repo.artifacts[1][0].freshness_status, ARTIFACT_FRESHNESS_REFRESH_REQUIRED)

    def test_reschedule_request_creates_internal_review_intent(self) -> None:
        reschedule = RescheduleRequest(
            reschedule_request_id=1,
            rental_case_id=1,
            current_active_date_snapshot={"start": "2026-09-01T10:00:00Z"},
            requested_date_payload={"start": "2026-09-03T10:00:00Z"},
            candidate_dates_payload=(),
            consequence_summary_payload={},
            status=RESCHEDULE_STATUS_PROPOSED,
            urgency_class="normal",
            created_at="2026-08-13T10:00:00Z",
            updated_at="2026-08-13T10:00:00Z",
        )
        repo = make_repo(make_case(), reschedules=(reschedule,))
        result = reconcile_workflow_orchestration(repo, rental_case_id=1, actor_reference="system:orchestration")
        self.assertEqual(len(result.created_action_ids), 1)
        self.assertEqual(repo.workflow_actions[1][0].action_type, ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM)

    def test_compliance_requirement_candidate_creates_governed_requirement_and_action(self) -> None:
        repo = make_repo(
            make_case(),
            projections=(
                make_projection(
                    projection_id=2,
                    reasoning_purpose="compliance_requirement_review",
                    authority_outcome="CURRENT_GUIDANCE",
                    reasoning_state_code="resolved",
                    workflow_posture=WORKFLOW_REASONING_POSTURE_GUIDANCE_ONLY,
                    relevant_guidance_item_ids=("permit:ade",),
                ),
            ),
        )
        result = reconcile_workflow_orchestration(repo, rental_case_id=1, actor_reference="system:orchestration")
        self.assertEqual(len(result.created_requirement_ids), 1)
        self.assertEqual(repo.requirements[1][0].requirement_type, "permit_review_required")
        self.assertEqual(repo.workflow_actions[1][0].action_type, ACTION_TYPE_ESCALATE_COMPLIANCE_REVIEW)


if __name__ == "__main__":
    unittest.main()
