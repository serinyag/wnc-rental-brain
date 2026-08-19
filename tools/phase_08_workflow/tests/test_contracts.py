from __future__ import annotations

import unittest

from tools.phase_08_workflow.contracts import (
    ACTION_CATEGORY_COMMUNICATION,
    ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
    APPROVAL_POSTURE_APPROVAL_REQUIRED,
    APPROVAL_POSTURE_HUMAN_ONLY,
    APPROVAL_REQUEST_STATUS_OPEN,
    ARTIFACT_FRESHNESS_CURRENT,
    ARTIFACT_TYPE_PROPOSAL,
    AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
    BLOCKED_SUBJECT_TYPE_TRANSITION,
    BLOCKER_STATUS_OPEN,
    BLOCKING_SCOPE_TRANSITION,
    CASE_DECISION_STATUS_ACTIVE,
    CASE_DECISION_STATUS_PROPOSED,
    CHANGE_IMPACT_MATERIAL,
    EXECUTION_ATTEMPT_STATUS_FAILED,
    FOLLOW_UP_STATUS_SCHEDULED,
    FOLLOW_UP_URGENCY_MEDIUM,
    LIFECYCLE_STATE_INQUIRY_ACTIVE,
    MILESTONE_STATUS_COMPLETED,
    OPEN_QUESTION_STATUS_OPEN,
    PHASE_8_WORKFLOW_CONTRACT_VERSION,
    PROPOSED_CHANGE_STATUS_ACCEPTED,
    REQUIREMENT_STATUS_REQUIRED,
    RESCHEDULE_STATUS_CONFIRMED,
    RESCHEDULE_URGENCY_NORMAL,
    SEVERITY_MEDIUM,
    WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
    ApprovalPosture,
    ApprovalRequest,
    ArtifactReference,
    Blocker,
    CaseDecision,
    ChangeImpact,
    ExecutionAttempt,
    FollowUp,
    LifecycleState,
    LifecycleTransition,
    Milestone,
    OpenQuestion,
    Phase8ContractError,
    ProposedCaseChange,
    RentalCase,
    Requirement,
    RescheduleRequest,
    WorkflowAction,
    WorkflowActionStatus,
    WorkflowEvent,
    WorkflowReasoningProjection,
)


class Phase8ContractsTests(unittest.TestCase):
    def test_frozen_enum_wrappers_accept_valid_values(self) -> None:
        self.assertEqual(LifecycleState(LIFECYCLE_STATE_INQUIRY_ACTIVE).value, LIFECYCLE_STATE_INQUIRY_ACTIVE)
        self.assertEqual(ChangeImpact(CHANGE_IMPACT_MATERIAL).value, CHANGE_IMPACT_MATERIAL)
        self.assertEqual(ApprovalPosture(APPROVAL_POSTURE_HUMAN_ONLY).value, APPROVAL_POSTURE_HUMAN_ONLY)
        self.assertEqual(WorkflowActionStatus(WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL).value, WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL)

    def test_invalid_enum_wrapper_values_are_rejected(self) -> None:
        with self.assertRaisesRegex(Phase8ContractError, "must be one of"):
            LifecycleState("bad_state")
        with self.assertRaisesRegex(Phase8ContractError, "must be one of"):
            ChangeImpact("bad_impact")
        with self.assertRaisesRegex(Phase8ContractError, "must be one of"):
            ApprovalPosture("bad_posture")
        with self.assertRaisesRegex(Phase8ContractError, "must be one of"):
            WorkflowActionStatus("bad_status")

    def test_rental_case_requires_valid_lifecycle_and_nonnegative_revision(self) -> None:
        case = RentalCase(
            rental_case_id=1,
            rental_case_uuid="uuid-1",
            case_reference_code="RC-900",
            lifecycle_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
            case_revision=0,
            rental_type_code="studio_space",
            commercial_summary_status="unknown",
            operational_summary_status="unknown",
            is_active=True,
        )
        self.assertEqual(case.lifecycle_state, LIFECYCLE_STATE_INQUIRY_ACTIVE)

        with self.assertRaisesRegex(Phase8ContractError, "non-negative integer"):
            RentalCase(
                rental_case_id=1,
                rental_case_uuid="uuid-1",
                case_reference_code="RC-901",
                lifecycle_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
                case_revision=-1,
                rental_type_code="studio_space",
                commercial_summary_status="unknown",
                operational_summary_status="unknown",
                is_active=True,
            )

    def test_lifecycle_transition_requires_monotonic_revision_order(self) -> None:
        with self.assertRaisesRegex(Phase8ContractError, "greater than or equal"):
            LifecycleTransition(
                lifecycle_transition_id=1,
                rental_case_id=1,
                from_lifecycle_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
                to_lifecycle_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
                transition_reason_code="nope",
                case_revision_before=2,
                case_revision_after=1,
                occurred_at="2026-08-09T10:00:00Z",
            )

    def test_workflow_event_accepts_json_payloads_only(self) -> None:
        event = WorkflowEvent(
            workflow_event_id=1,
            workflow_event_uuid="event-uuid",
            rental_case_id=1,
            event_type_code="inquiry_received",
            source_type="synthetic_fixture",
            occurred_at="2026-08-09T10:00:00Z",
            recorded_at="2026-08-09T10:00:01Z",
            structured_payload={"subject": "hello"},
        )
        self.assertEqual(event.structured_payload["subject"], "hello")

    def test_open_question_and_requirement_validate_controlled_statuses(self) -> None:
        OpenQuestion(
            open_question_id=1,
            rental_case_id=1,
            question_type="missing_date",
            domain_code="timing",
            human_question_text="What date do you want?",
            blocking_scope=BLOCKING_SCOPE_TRANSITION,
            status=OPEN_QUESTION_STATUS_OPEN,
            created_at="2026-08-09T10:00:00Z",
        )
        Requirement(
            requirement_id=1,
            rental_case_id=1,
            requirement_type="confirmation_payment_required",
            domain_code="commercial",
            applicability_basis="booking confirmation",
            status=REQUIREMENT_STATUS_REQUIRED,
            blocking_scope=BLOCKING_SCOPE_TRANSITION,
            created_at="2026-08-09T10:00:00Z",
        )
        with self.assertRaisesRegex(Phase8ContractError, "must be one of"):
            OpenQuestion(
                open_question_id=1,
                rental_case_id=1,
                question_type="missing_date",
                domain_code="timing",
                human_question_text="What date do you want?",
                blocking_scope=BLOCKING_SCOPE_TRANSITION,
                status="bad_status",
                created_at="2026-08-09T10:00:00Z",
            )

    def test_blocker_requires_subject_and_origin_references(self) -> None:
        with self.assertRaisesRegex(Phase8ContractError, "must include at least one non-null reference"):
            Blocker(
                blocker_id=1,
                rental_case_id=1,
                blocker_type="missing_info",
                blocked_subject_type=BLOCKED_SUBJECT_TYPE_TRANSITION,
                origin_entity_type="open_question",
                severity=SEVERITY_MEDIUM,
                status=BLOCKER_STATUS_OPEN,
                resolution_condition_text="Need answer",
                opened_at="2026-08-09T10:00:00Z",
            )

    def test_active_case_decision_requires_effective_fields_and_approval_reference_when_needed(self) -> None:
        with self.assertRaisesRegex(Phase8ContractError, "require effective_at and effective_value_payload"):
            CaseDecision(
                case_decision_id=1,
                rental_case_id=1,
                decision_type="fee_waiver",
                domain_code="booking_fee",
                baseline_reference="rule:booking_fee",
                proposed_value_payload={"amount": 0},
                scope_key="booking_fee:confirmation",
                scope_description="booking fee override",
                authority_basis="manager approved",
                approval_posture=APPROVAL_POSTURE_HUMAN_ONLY,
                status=CASE_DECISION_STATUS_ACTIVE,
                created_at="2026-08-09T10:00:00Z",
            )

        with self.assertRaisesRegex(Phase8ContractError, "must include approval_request_id"):
            CaseDecision(
                case_decision_id=2,
                rental_case_id=1,
                decision_type="fee_waiver",
                domain_code="booking_fee",
                baseline_reference="rule:booking_fee",
                proposed_value_payload={"amount": 0},
                effective_value_payload={"amount": 0},
                scope_key="booking_fee:confirmation",
                scope_description="booking fee override",
                authority_basis="manager approved",
                approval_posture=APPROVAL_POSTURE_APPROVAL_REQUIRED,
                status=CASE_DECISION_STATUS_ACTIVE,
                created_at="2026-08-09T10:00:00Z",
                effective_at="2026-08-09T10:05:00Z",
            )

        decision = CaseDecision(
            case_decision_id=3,
            rental_case_id=1,
            decision_type="fee_waiver",
            domain_code="booking_fee",
            baseline_reference="rule:booking_fee",
            proposed_value_payload={"amount": 0},
            effective_value_payload={"amount": 0},
            scope_key="booking_fee:confirmation",
            scope_description="booking fee override",
            authority_basis="manager approved",
            approval_posture=APPROVAL_POSTURE_HUMAN_ONLY,
            status=CASE_DECISION_STATUS_ACTIVE,
            created_at="2026-08-09T10:00:00Z",
            effective_at="2026-08-09T10:05:00Z",
        )
        self.assertEqual(decision.status, CASE_DECISION_STATUS_ACTIVE)

    def test_proposed_case_change_and_reschedule_request_require_confirmation_fields(self) -> None:
        with self.assertRaisesRegex(Phase8ContractError, "require final_value_payload and accepted_at"):
            ProposedCaseChange(
                proposed_case_change_id=1,
                rental_case_id=1,
                change_kind="date_change",
                domain_code="timing",
                proposed_value_payload={"start": "2026-09-01T10:00:00Z"},
                status=PROPOSED_CHANGE_STATUS_ACCEPTED,
                detected_at="2026-08-09T10:00:00Z",
            )

        with self.assertRaisesRegex(Phase8ContractError, "require confirmed_proposed_change_id and confirmed_at"):
            RescheduleRequest(
                reschedule_request_id=1,
                rental_case_id=1,
                current_active_date_snapshot={"start": "2026-09-01T10:00:00Z"},
                requested_date_payload={"start": "2026-09-03T10:00:00Z"},
                candidate_dates_payload=(),
                consequence_summary_payload={},
                status=RESCHEDULE_STATUS_CONFIRMED,
                urgency_class=RESCHEDULE_URGENCY_NORMAL,
                created_at="2026-08-09T10:00:00Z",
            )

    def test_approval_request_requires_target_reference(self) -> None:
        with self.assertRaisesRegex(Phase8ContractError, "must include at least one non-null reference"):
            ApprovalRequest(
                approval_request_id=1,
                rental_case_id=1,
                target_entity_type="case_decision",
                approval_type="commercial_exception",
                reason_text="Needs approval",
                status=APPROVAL_REQUEST_STATUS_OPEN,
                created_at="2026-08-09T10:00:00Z",
            )

    def test_workflow_action_requires_idempotency_and_reason_reference(self) -> None:
        with self.assertRaisesRegex(Phase8ContractError, "must include at least one non-null reference"):
            WorkflowAction(
                workflow_action_id=1,
                workflow_action_uuid="action-uuid",
                rental_case_id=1,
                action_type=ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
                action_category=ACTION_CATEGORY_COMMUNICATION,
                target_adapter_code="email",
                reason_entity_type="open_question",
                approval_posture=APPROVAL_POSTURE_APPROVAL_REQUIRED,
                status=WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
                semantic_subject_hash="hash",
                source_case_revision=0,
                idempotency_key="key",
            )

        with self.assertRaisesRegex(Phase8ContractError, "non-empty string"):
            WorkflowAction(
                workflow_action_id=1,
                workflow_action_uuid="action-uuid",
                rental_case_id=1,
                action_type=ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
                action_category=ACTION_CATEGORY_COMMUNICATION,
                target_adapter_code="email",
                reason_entity_type="open_question",
                reason_entity_reference="oq:1",
                approval_posture=APPROVAL_POSTURE_APPROVAL_REQUIRED,
                status=WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
                semantic_subject_hash="hash",
                source_case_revision=0,
                idempotency_key="",
            )

    def test_execution_attempt_requires_completion_for_terminal_status(self) -> None:
        with self.assertRaisesRegex(Phase8ContractError, "require completed_at"):
            ExecutionAttempt(
                execution_attempt_id=1,
                execution_attempt_uuid="attempt-uuid",
                workflow_action_id=1,
                rental_case_id=1,
                attempt_number=1,
                adapter_code="email",
                started_at="2026-08-09T10:00:00Z",
                status=EXECUTION_ATTEMPT_STATUS_FAILED,
                retry_eligible=True,
                response_snapshot={"status": "failed"},
            )

    def test_follow_up_milestone_and_artifact_validation_work(self) -> None:
        FollowUp(
            follow_up_id=1,
            rental_case_id=1,
            reason_code="client_reply_wait",
            due_at="2026-08-10T10:00:00Z",
            urgency_level=FOLLOW_UP_URGENCY_MEDIUM,
            attempt_count=0,
            status=FOLLOW_UP_STATUS_SCHEDULED,
        )
        Milestone(
            milestone_id=1,
            rental_case_id=1,
            milestone_type="proposal_follow_up_due",
            target_at="2026-08-10T10:00:00Z",
            status=MILESTONE_STATUS_COMPLETED,
            completed_at="2026-08-10T10:05:00Z",
        )
        with self.assertRaisesRegex(Phase8ContractError, "non-negative integer"):
            ArtifactReference(
                artifact_reference_id=1,
                rental_case_id=1,
                artifact_type=ARTIFACT_TYPE_PROPOSAL,
                derived_from_case_revision=-1,
                freshness_status=ARTIFACT_FRESHNESS_CURRENT,
            )

    def test_reasoning_projection_validates_phase_7_code_sets(self) -> None:
        projection = WorkflowReasoningProjection(
            reasoning_projection_id=1,
            rental_case_id=1,
            reasoning_purpose="proposal_readiness_review",
            phase_7_context_contract_version=1,
            phase_8_workflow_contract_version=PHASE_8_WORKFLOW_CONTRACT_VERSION,
            source_case_revision=0,
            authority_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
            degraded_retrieval_summary={},
            created_at="2026-08-09T10:00:00Z",
            relevant_current_truth_item_ids=("RULE-1",),
            conflict_codes=(),
            contamination_codes=(),
            unresolved_authority_codes=("UNRESOLVED-1",),
            warning_codes=("WARN-1",),
            grounding_reference_keys=("SRC-1",),
        )
        self.assertEqual(projection.authority_outcome_classification, AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT)

        with self.assertRaisesRegex(Phase8ContractError, "must be one of"):
            WorkflowReasoningProjection(
                reasoning_projection_id=2,
                rental_case_id=1,
                reasoning_purpose="proposal_readiness_review",
                phase_7_context_contract_version=1,
                phase_8_workflow_contract_version=PHASE_8_WORKFLOW_CONTRACT_VERSION,
                source_case_revision=0,
                authority_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                degraded_retrieval_summary={},
                created_at="2026-08-09T10:00:00Z",
                conflict_codes=("TYPE_Z_UNKNOWN",),
                unresolved_authority_codes=("UNRESOLVED-1",),
                warning_codes=("WARN-1",),
            )


if __name__ == "__main__":
    unittest.main()
