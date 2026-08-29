from __future__ import annotations

import unittest

from tools.phase_08_workflow.contracts import (
    ACTION_CATEGORY_COORDINATION,
    ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
    APPROVAL_POSTURE_APPROVAL_REQUIRED,
    APPROVAL_REQUEST_STATUS_OPEN,
    ARTIFACT_FRESHNESS_STALE,
    ARTIFACT_TYPE_PROPOSAL,
    AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
    BLOCKER_STATUS_OPEN,
    CASE_DECISION_STATUS_ACTIVE,
    CASE_DECISION_STATUS_PROPOSED,
    CASE_DECISION_STATUS_SUPERSEDED,
    FOLLOW_UP_STATUS_DUE,
    FOLLOW_UP_URGENCY_MEDIUM,
    LIFECYCLE_STATE_INQUIRY_ACTIVE,
    PHASE_7_REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
    PROPOSED_CHANGE_STATUS_PROPOSED,
    RESCHEDULE_STATUS_PROPOSED,
    WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
    WORKFLOW_ACTION_STATUS_SUPERSEDED,
    WORKFLOW_REASONING_POSTURE_BLOCKED_FOR_CURRENT_DECISION,
    ApprovalRequest,
    ArtifactReference,
    Blocker,
    CaseDecision,
    FollowUp,
    ProposedCaseChange,
    RentalCase,
    RescheduleRequest,
    WorkflowAction,
    WorkflowReasoningProjection,
)
from tools.phase_08_workflow.observation_contracts import RentalCaseFact
from tools.phase_08_workflow.orchestration_repository import WorkflowOrchestrationCaseSnapshot
from tools.phase_08_workflow.test_console_projection import (
    BookingFeeRuleContext,
    DISPLAY_STATE_BLOCKED,
    DISPLAY_STATE_CURRENT,
    DISPLAY_STATE_NONE,
    DISPLAY_STATE_PROPOSED,
    DISPLAY_STATE_REFERENCE,
    DISPLAY_STATE_STALE,
    DISPLAY_STATE_UNRESOLVED,
    LatestCommunicationContext,
    ObservedFieldCandidate,
    ProjectionItem,
    TestConsoleCaseMetadata,
    build_working_proposal_projection,
)


def make_case(
    *,
    active_event_start: str | None = "2026-10-03T12:00:00Z",
    active_event_end: str | None = "2026-10-03T18:00:00Z",
    rental_type_code: str = "studio_space",
) -> RentalCase:
    return RentalCase(
        rental_case_id=1,
        rental_case_uuid="case-1",
        case_reference_code="RC-9001",
        lifecycle_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
        case_revision=4,
        rental_type_code=rental_type_code,
        commercial_summary_status="unknown",
        operational_summary_status="unknown",
        is_active=True,
        active_event_start=active_event_start,
        active_event_end=active_event_end,
        service_level_or_type="test_rental",
        created_at="2026-08-14T09:00:00Z",
        updated_at="2026-08-14T10:00:00Z",
    )


def make_booking_fee_context(
    *,
    fee_ex_vat: float = 50.0,
    source_state: str = DISPLAY_STATE_CURRENT,
    source_detail: str = "Derived from the current active event window.",
) -> BookingFeeRuleContext:
    return BookingFeeRuleContext(
        rule_code="FEE_STUDIO_1_TO_3_HOUR_BOOKING",
        rental_type_code="studio_space",
        rental_type_name="Studio Space",
        duration_minutes=180,
        fee_ex_vat=fee_ex_vat,
        currency_code="EUR",
        vat_rate=0.21,
        waiver_allowed=True,
        waiver_authority="WNC rental point of contact",
        source_state=source_state,
        source_detail=source_detail,
        source_codes=("COM-001-XLSM", "GOV-002"),
    )


def find_item(items: tuple[ProjectionItem, ...], label: str) -> ProjectionItem:
    for item in items:
        if item.label == label:
            return item
    raise AssertionError(f"Projection item {label!r} not found in {[item.label for item in items]!r}")


class WorkingProposalProjectionTests(unittest.TestCase):
    def test_empty_inquiry_keeps_missing_fields_explicit_without_fabrication(self) -> None:
        projection = build_working_proposal_projection(
            WorkflowOrchestrationCaseSnapshot(
                rental_case=make_case(
                    active_event_start=None,
                    active_event_end=None,
                    rental_type_code="custom_scope",
                )
            ),
            metadata=TestConsoleCaseMetadata(client_label="Acme", label="Empty inquiry"),
        )

        self.assertEqual(find_item(projection.rental_snapshot, "Rental type").value, "Not established")
        self.assertEqual(find_item(projection.rental_snapshot, "Requested spaces").value, "Not established")
        self.assertEqual(find_item(projection.rental_snapshot, "Event date").value, "Not provided")
        self.assertEqual(find_item(projection.rental_snapshot, "Guest count").value, "Not provided")
        self.assertEqual(find_item(projection.blockers, "Current blockers").value, "None")
        self.assertEqual(find_item(projection.approvals, "Pending approvals").value, "None")
        self.assertEqual(find_item(projection.proposal_freshness, "Proposal artifact").value, "Not yet established")

    def test_incomplete_inquiry_metadata_does_not_imply_current_scope(self) -> None:
        projection = build_working_proposal_projection(
            WorkflowOrchestrationCaseSnapshot(
                rental_case=make_case(
                    active_event_start=None,
                    active_event_end=None,
                    rental_type_code="custom_scope",
                )
            ),
            metadata=TestConsoleCaseMetadata(
                client_label="Acme",
                label="Incomplete inquiry",
                event_reference="Interested in the studio sometime in October",
            ),
        )

        self.assertEqual(find_item(projection.rental_snapshot, "Rental type").value, "Not established")
        self.assertEqual(find_item(projection.rental_snapshot, "Requested spaces").value, "Not established")

    def test_explicit_studio_scope_is_displayed(self) -> None:
        projection = build_working_proposal_projection(
            WorkflowOrchestrationCaseSnapshot(rental_case=make_case(rental_type_code="studio_space")),
            metadata=TestConsoleCaseMetadata(label="Studio fixture"),
        )

        self.assertEqual(find_item(projection.rental_snapshot, "Rental type").value, "Studio Space")
        self.assertEqual(find_item(projection.rental_snapshot, "Requested spaces").value, "Studio Space")

    def test_explicit_entire_venue_scope_is_displayed(self) -> None:
        projection = build_working_proposal_projection(
            WorkflowOrchestrationCaseSnapshot(rental_case=make_case(rental_type_code="entire_venue")),
            metadata=TestConsoleCaseMetadata(label="Entire venue fixture"),
        )

        self.assertEqual(find_item(projection.rental_snapshot, "Rental type").value, "Entire Venue")
        self.assertEqual(find_item(projection.rental_snapshot, "Requested spaces").value, "Entire Venue")

    def test_persisted_current_fact_stays_current_and_observed_candidate_stays_separate(self) -> None:
        snapshot = WorkflowOrchestrationCaseSnapshot(
            rental_case=make_case(),
            rental_case_facts=(
                RentalCaseFact(
                    rental_case_fact_id=1,
                    rental_case_id=1,
                    field_code="guest_count",
                    domain_code="event_profile",
                    value_payload=30,
                    source_reference="fact:guest_count",
                    established_case_revision=2,
                    created_at="2026-08-14T09:00:00Z",
                    updated_at="2026-08-14T09:00:00Z",
                ),
            ),
        )
        projection = build_working_proposal_projection(
            snapshot,
            metadata=TestConsoleCaseMetadata(label="Projection Safety"),
            observed_field_candidates=(
                ObservedFieldCandidate(
                    field_code="guest_count",
                    display_label="Guest Count",
                    value_payload=60,
                    observed_at="2026-08-14T09:10:00Z",
                    observation_status="validated",
                    source_record_type="operator_note",
                    source_actor_reference="fixture:operator",
                ),
            ),
        )

        guest_count = find_item(projection.rental_snapshot, "Guest count")
        observed_guest_count = find_item(projection.rental_snapshot, "Observed guest count")
        self.assertEqual(guest_count.value, "30")
        self.assertEqual(guest_count.state, DISPLAY_STATE_CURRENT)
        self.assertEqual(observed_guest_count.value, "60")
        self.assertEqual(observed_guest_count.state, DISPLAY_STATE_PROPOSED)

    def test_proposed_case_change_shows_current_and_proposed_values_separately(self) -> None:
        snapshot = WorkflowOrchestrationCaseSnapshot(
            rental_case=make_case(),
            proposed_changes=(
                ProposedCaseChange(
                    proposed_case_change_id=10,
                    rental_case_id=1,
                    change_kind="guest_count",
                    domain_code="event_profile",
                    prior_value_payload=30,
                    proposed_value_payload=45,
                    source_reference="observation:guest_count",
                    impact_classification="material_impact",
                    affected_domain_codes=("event_profile",),
                    review_posture="human_only",
                    status=PROPOSED_CHANGE_STATUS_PROPOSED,
                    detected_at="2026-08-14T09:10:00Z",
                    created_at="2026-08-14T09:10:00Z",
                    updated_at="2026-08-14T09:10:00Z",
                ),
            ),
        )
        projection = build_working_proposal_projection(snapshot, metadata=TestConsoleCaseMetadata(label="Change"))

        guest_count_change = find_item(projection.changes, "Guest Count")
        self.assertEqual(guest_count_change.value, "45")
        self.assertEqual(guest_count_change.state, DISPLAY_STATE_PROPOSED)
        self.assertIn("Current: 30.", guest_count_change.detail or "")
        self.assertIn("Proposed: 45.", guest_count_change.detail or "")

    def test_reschedule_projects_current_and_proposed_schedule_separately(self) -> None:
        snapshot = WorkflowOrchestrationCaseSnapshot(
            rental_case=make_case(
                active_event_start="2026-10-03T18:00:00Z",
                active_event_end="2026-10-03T22:00:00Z",
            ),
            reschedule_requests=(
                RescheduleRequest(
                    reschedule_request_id=8,
                    rental_case_id=1,
                    current_active_date_snapshot={
                        "active_event_start": "2026-10-03T18:00:00Z",
                        "active_event_end": "2026-10-03T22:00:00Z",
                    },
                    requested_date_payload={
                        "active_event_start": "2026-10-10T18:00:00Z",
                        "active_event_end": "2026-10-10T22:00:00Z",
                    },
                    candidate_dates_payload=(),
                    consequence_summary_payload={},
                    status=RESCHEDULE_STATUS_PROPOSED,
                    urgency_class="normal",
                    created_at="2026-08-14T09:20:00Z",
                ),
            ),
        )
        projection = build_working_proposal_projection(snapshot, metadata=TestConsoleCaseMetadata(label="Reschedule"))

        self.assertEqual(find_item(projection.rental_snapshot, "Event date").value, "2026-10-03")
        self.assertEqual(find_item(projection.rental_snapshot, "Proposed event date").value, "2026-10-10")
        self.assertEqual(find_item(projection.rental_snapshot, "Proposed event date").state, DISPLAY_STATE_PROPOSED)
        self.assertEqual(find_item(projection.changes, "Reschedule request").state, DISPLAY_STATE_PROPOSED)

    def test_pending_booking_fee_waiver_shows_baseline_and_pending_exception(self) -> None:
        snapshot = WorkflowOrchestrationCaseSnapshot(
            rental_case=make_case(),
            case_decisions=(
                CaseDecision(
                    case_decision_id=25,
                    rental_case_id=1,
                    decision_type="booking_fee_override",
                    domain_code="commercial",
                    baseline_reference="phase4:booking_fee",
                    proposed_value_payload={"booking_fee": 0, "currency": "EUR", "reason": "Nonprofit waiver request"},
                    scope_key="booking_fee:default",
                    scope_description="Booking Fee Override",
                    authority_basis="case_specific_exception",
                    approval_posture=APPROVAL_POSTURE_APPROVAL_REQUIRED,
                    status=CASE_DECISION_STATUS_PROPOSED,
                    created_at="2026-08-14T09:00:00Z",
                ),
            ),
            approval_requests=(
                ApprovalRequest(
                    approval_request_id=37,
                    rental_case_id=1,
                    target_entity_type="case_decision",
                    target_entity_reference="case_decision:25",
                    approval_type="commercial_exception",
                    reason_text="Approval required before activating case decision 25.",
                    status=APPROVAL_REQUEST_STATUS_OPEN,
                    created_at="2026-08-14T09:05:00Z",
                ),
            ),
        )
        projection = build_working_proposal_projection(
            snapshot,
            metadata=TestConsoleCaseMetadata(label="Booking Fee Exception"),
            booking_fee_context=make_booking_fee_context(),
        )

        self.assertEqual(find_item(projection.commercial_snapshot, "Booking fee baseline").value, "EUR 50 excl. VAT")
        self.assertEqual(find_item(projection.commercial_snapshot, "Case-specific exception").value, "Pending")
        self.assertIn("Standard baseline remains EUR 50 excl. VAT until approval.", find_item(projection.commercial_snapshot, "Case-specific exception").detail or "")
        self.assertEqual(find_item(projection.commercial_snapshot, "Effective booking fee").value, "EUR 50 excl. VAT")
        self.assertEqual(find_item(projection.approvals, "Approve Booking Fee Override").state, DISPLAY_STATE_BLOCKED)

    def test_active_case_specific_waiver_is_displayed_without_implying_global_truth_change(self) -> None:
        snapshot = WorkflowOrchestrationCaseSnapshot(
            rental_case=make_case(),
            case_decisions=(
                CaseDecision(
                    case_decision_id=1,
                    rental_case_id=1,
                    decision_type="booking_fee_override",
                    domain_code="commercial",
                    baseline_reference="phase4:booking_fee",
                    proposed_value_payload={"booking_fee": 0, "currency": "USD", "reason": "Community waiver"},
                    scope_key="booking_fee:default",
                    scope_description="Booking Fee Override",
                    authority_basis="case_specific_exception",
                    approval_posture=APPROVAL_POSTURE_APPROVAL_REQUIRED,
                    status=CASE_DECISION_STATUS_ACTIVE,
                    created_at="2026-08-14T09:00:00Z",
                    effective_value_payload={"booking_fee": 0, "currency": "USD", "reason": "Community waiver"},
                    evidence_reference="observation:fee_waiver",
                    approval_request_id=7,
                    effective_at="2026-08-14T09:15:00Z",
                    updated_at="2026-08-14T09:15:00Z",
                ),
            ),
        )
        projection = build_working_proposal_projection(
            snapshot,
            metadata=TestConsoleCaseMetadata(label="Booking Fee Exception"),
            booking_fee_context=make_booking_fee_context(),
        )

        self.assertEqual(find_item(projection.commercial_snapshot, "Booking fee baseline").value, "EUR 50 excl. VAT")
        self.assertEqual(find_item(projection.commercial_snapshot, "Case-specific exception").value, "Waived")
        self.assertEqual(find_item(projection.commercial_snapshot, "Effective booking fee").value, "EUR 0")

    def test_booking_fee_baseline_is_unchanged_before_and_after_case_specific_approval(self) -> None:
        pending_projection = build_working_proposal_projection(
            WorkflowOrchestrationCaseSnapshot(
                rental_case=make_case(),
                case_decisions=(
                    CaseDecision(
                        case_decision_id=25,
                        rental_case_id=1,
                        decision_type="booking_fee_override",
                        domain_code="commercial",
                        baseline_reference="phase4:booking_fee",
                        proposed_value_payload={"booking_fee": 0, "currency": "EUR", "reason": "Nonprofit waiver request"},
                        scope_key="booking_fee:default",
                        scope_description="Booking Fee Override",
                        authority_basis="case_specific_exception",
                        approval_posture=APPROVAL_POSTURE_APPROVAL_REQUIRED,
                        status=CASE_DECISION_STATUS_PROPOSED,
                        created_at="2026-08-14T09:00:00Z",
                    ),
                ),
            ),
            metadata=TestConsoleCaseMetadata(label="Pending fee exception"),
            booking_fee_context=make_booking_fee_context(),
        )
        active_projection = build_working_proposal_projection(
            WorkflowOrchestrationCaseSnapshot(
                rental_case=make_case(),
                case_decisions=(
                    CaseDecision(
                        case_decision_id=25,
                        rental_case_id=1,
                        decision_type="booking_fee_override",
                        domain_code="commercial",
                        baseline_reference="phase4:booking_fee",
                        proposed_value_payload={"booking_fee": 0, "currency": "EUR", "reason": "Nonprofit waiver request"},
                        scope_key="booking_fee:default",
                        scope_description="Booking Fee Override",
                        authority_basis="case_specific_exception",
                        approval_posture=APPROVAL_POSTURE_APPROVAL_REQUIRED,
                        status=CASE_DECISION_STATUS_ACTIVE,
                        created_at="2026-08-14T09:00:00Z",
                        effective_value_payload={"booking_fee": 0, "currency": "EUR", "reason": "Nonprofit waiver request"},
                        evidence_reference="observation:fee_waiver",
                        approval_request_id=37,
                        effective_at="2026-08-14T09:15:00Z",
                        updated_at="2026-08-14T09:15:00Z",
                    ),
                ),
            ),
            metadata=TestConsoleCaseMetadata(label="Approved fee exception"),
            booking_fee_context=make_booking_fee_context(),
        )

        self.assertEqual(find_item(pending_projection.commercial_snapshot, "Booking fee baseline").value, "EUR 50 excl. VAT")
        self.assertEqual(find_item(active_projection.commercial_snapshot, "Booking fee baseline").value, "EUR 50 excl. VAT")
        self.assertEqual(find_item(pending_projection.commercial_snapshot, "Effective booking fee").value, "EUR 50 excl. VAT")
        self.assertEqual(find_item(active_projection.commercial_snapshot, "Effective booking fee").value, "EUR 0")

    def test_superseded_booking_fee_override_does_not_determine_effective_value(self) -> None:
        snapshot = WorkflowOrchestrationCaseSnapshot(
            rental_case=make_case(),
            case_decisions=(
                CaseDecision(
                    case_decision_id=1,
                    rental_case_id=1,
                    decision_type="booking_fee_override",
                    domain_code="commercial",
                    baseline_reference="phase4:booking_fee",
                    proposed_value_payload={"booking_fee": 0, "currency": "EUR"},
                    scope_key="booking_fee:default",
                    scope_description="Booking Fee Override",
                    authority_basis="case_specific_exception",
                    approval_posture=APPROVAL_POSTURE_APPROVAL_REQUIRED,
                    status=CASE_DECISION_STATUS_SUPERSEDED,
                    created_at="2026-08-14T09:00:00Z",
                    effective_value_payload={"booking_fee": 0, "currency": "EUR"},
                    evidence_reference="observation:fee_waiver",
                    approval_request_id=7,
                    effective_at="2026-08-14T09:15:00Z",
                    updated_at="2026-08-14T09:15:00Z",
                ),
            ),
        )
        projection = build_working_proposal_projection(
            snapshot,
            metadata=TestConsoleCaseMetadata(label="Superseded fee exception"),
            booking_fee_context=make_booking_fee_context(),
        )

        self.assertEqual(find_item(projection.commercial_snapshot, "Case-specific exceptions").value, "None")
        self.assertEqual(find_item(projection.commercial_snapshot, "Effective booking fee").value, "EUR 50 excl. VAT")

    def test_no_case_exception_uses_governed_baseline(self) -> None:
        projection = build_working_proposal_projection(
            WorkflowOrchestrationCaseSnapshot(rental_case=make_case()),
            metadata=TestConsoleCaseMetadata(label="Baseline only"),
            booking_fee_context=make_booking_fee_context(),
        )

        self.assertEqual(find_item(projection.commercial_snapshot, "Effective booking fee").value, "EUR 50 excl. VAT")

    def test_proposed_schedule_keeps_fee_as_reference_without_effective_commitment(self) -> None:
        projection = build_working_proposal_projection(
            WorkflowOrchestrationCaseSnapshot(rental_case=make_case()),
            metadata=TestConsoleCaseMetadata(label="Proposed schedule"),
            booking_fee_context=make_booking_fee_context(source_state=DISPLAY_STATE_PROPOSED),
        )

        self.assertEqual(find_item(projection.commercial_snapshot, "Booking fee baseline").state, DISPLAY_STATE_REFERENCE)
        self.assertFalse(any(item.label == "Effective booking fee" for item in projection.commercial_snapshot))

    def test_current_working_scope_surfaces_observed_operational_candidates(self) -> None:
        projection = build_working_proposal_projection(
            WorkflowOrchestrationCaseSnapshot(rental_case=make_case()),
            metadata=TestConsoleCaseMetadata(label="Operations"),
            observed_field_candidates=(
                ObservedFieldCandidate(
                    field_code="catering_arrangement",
                    display_label="Catering Arrangement",
                    value_payload="client_external_caterer",
                    observed_at="2026-08-14T09:00:00Z",
                    observation_status="validated",
                    source_record_type="operator_note",
                    source_actor_reference="fixture:operator",
                ),
                ObservedFieldCandidate(
                    field_code="technical_requirements",
                    display_label="Technical Requirements",
                    value_payload=["projection_display", "microphones"],
                    observed_at="2026-08-14T09:01:00Z",
                    observation_status="validated",
                    source_record_type="operator_note",
                    source_actor_reference="fixture:operator",
                ),
            ),
        )

        self.assertEqual(find_item(projection.operations, "Catering Arrangement").value, "Client External Caterer")
        self.assertEqual(find_item(projection.operations, "Catering Arrangement").state, DISPLAY_STATE_PROPOSED)
        self.assertEqual(find_item(projection.operations, "Technical Requirements").value, "Projection Display, Microphones")

    def test_historical_authority_gap_surfaces_warning_without_promoting_historical_value(self) -> None:
        snapshot = WorkflowOrchestrationCaseSnapshot(
            rental_case=make_case(active_event_start=None, active_event_end=None),
            reasoning_projections=(
                WorkflowReasoningProjection(
                    reasoning_projection_id=1,
                    rental_case_id=1,
                    reasoning_purpose="proposal_readiness_review",
                    phase_7_context_contract_version=1,
                    phase_8_workflow_contract_version=1,
                    source_case_revision=4,
                    authority_outcome_classification=AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
                    degraded_retrieval_summary={},
                    created_at="2026-08-14T09:00:00Z",
                    projection_identity_key="projection:1",
                    reasoning_state_code=PHASE_7_REASONING_STATE_INSUFFICIENT_CURRENT_AUTHORITY,
                    workflow_posture=WORKFLOW_REASONING_POSTURE_BLOCKED_FOR_CURRENT_DECISION,
                    unresolved_authority_codes=("storage_price|insufficient_current_authority",),
                    warning_codes=("manual_review_required",),
                    grounding_reference_keys=("rule:storage",),
                ),
            ),
        )
        projection = build_working_proposal_projection(snapshot, metadata=TestConsoleCaseMetadata(label="Authority gap"))

        warning = find_item(projection.warnings, "Current authority warning")
        self.assertEqual(warning.value, "Current authority insufficient")
        self.assertIn("storage_price|insufficient_current_authority", warning.detail or "")
        self.assertNotIn("300", " ".join(item.value for item in projection.commercial_snapshot))

    def test_blocker_approval_and_action_chain_are_projected_together(self) -> None:
        snapshot = WorkflowOrchestrationCaseSnapshot(
            rental_case=make_case(),
            case_decisions=(
                CaseDecision(
                    case_decision_id=25,
                    rental_case_id=1,
                    decision_type="booking_fee_override",
                    domain_code="commercial",
                    baseline_reference="phase4:booking_fee",
                    proposed_value_payload={"booking_fee": 0, "currency": "EUR", "waived": True},
                    scope_key="booking_fee:default",
                    scope_description="Booking Fee Override",
                    authority_basis="case_specific_exception",
                    approval_posture=APPROVAL_POSTURE_APPROVAL_REQUIRED,
                    status=CASE_DECISION_STATUS_PROPOSED,
                    created_at="2026-08-14T09:00:00Z",
                ),
            ),
            approval_requests=(
                ApprovalRequest(
                    approval_request_id=37,
                    rental_case_id=1,
                    target_entity_type="case_decision",
                    target_entity_reference="case_decision:25",
                    approval_type="commercial_exception",
                    reason_text="Approval required before activating case decision 25.",
                    status=APPROVAL_REQUEST_STATUS_OPEN,
                    created_at="2026-08-14T09:05:00Z",
                ),
            ),
            blockers=(
                Blocker(
                    blocker_id=49,
                    rental_case_id=1,
                    blocker_type="case_decision_approval_required",
                    blocked_subject_type="decision",
                    blocked_subject_reference="case_decision:25",
                    origin_entity_type="case_decision",
                    origin_entity_reference="case_decision:25",
                    severity="high",
                    status=BLOCKER_STATUS_OPEN,
                    resolution_condition_text="Approval must be approved or the proposed case decision must be rejected.",
                    opened_at="2026-08-14T09:06:00Z",
                ),
            ),
            workflow_actions=(
                WorkflowAction(
                    workflow_action_id=70,
                    workflow_action_uuid="action-70",
                    rental_case_id=1,
                    action_type=ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
                    action_category=ACTION_CATEGORY_COORDINATION,
                    target_adapter_code="task_surface",
                    reason_entity_type="review_item",
                    reason_entity_reference="case_decision:25",
                    approval_posture="automatic_allowed",
                    status=WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
                    semantic_subject_hash="subject:70",
                    source_case_revision=4,
                    idempotency_key="idem:70",
                    structured_payload={
                        "summary": "Review proposed case decision 25.",
                        "reason": "A case-specific commercial exception requires approval.",
                    },
                    created_at="2026-08-14T09:07:00Z",
                    updated_at="2026-08-14T09:07:00Z",
                ),
            ),
        )
        projection = build_working_proposal_projection(
            snapshot,
            metadata=TestConsoleCaseMetadata(label="Action chain"),
            booking_fee_context=make_booking_fee_context(),
        )

        approval = find_item(projection.approvals, "Approve Booking Fee Override")
        action = find_item(projection.next_actions, "Review proposed case decision 25.")
        blocker = find_item(projection.blockers, "Case Decision Approval Required")
        self.assertIn("Status: Proposed.", approval.detail or "")
        self.assertIn("Related approval: 37 is open.", action.detail or "")
        self.assertIn("Blocked by: Approval must be approved", action.detail or "")
        self.assertEqual(blocker.state, DISPLAY_STATE_BLOCKED)

    def test_superseded_action_is_excluded_from_current_attention(self) -> None:
        snapshot = WorkflowOrchestrationCaseSnapshot(
            rental_case=make_case(),
            workflow_actions=(
                WorkflowAction(
                    workflow_action_id=1,
                    workflow_action_uuid="action-1",
                    rental_case_id=1,
                    action_type=ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
                    action_category=ACTION_CATEGORY_COORDINATION,
                    target_adapter_code="task_surface",
                    reason_entity_type="review_item",
                    reason_entity_reference="case_decision:25",
                    approval_posture="automatic_allowed",
                    status=WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
                    semantic_subject_hash="subject:1",
                    source_case_revision=4,
                    idempotency_key="idem:1",
                    structured_payload={"summary": "Current action", "reason": "Current work."},
                    created_at="2026-08-14T09:07:00Z",
                    updated_at="2026-08-14T09:07:00Z",
                ),
                WorkflowAction(
                    workflow_action_id=2,
                    workflow_action_uuid="action-2",
                    rental_case_id=1,
                    action_type=ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
                    action_category=ACTION_CATEGORY_COORDINATION,
                    target_adapter_code="task_surface",
                    reason_entity_type="review_item",
                    reason_entity_reference="case_decision:25",
                    approval_posture="automatic_allowed",
                    status=WORKFLOW_ACTION_STATUS_SUPERSEDED,
                    semantic_subject_hash="subject:2",
                    source_case_revision=3,
                    idempotency_key="idem:2",
                    structured_payload={"summary": "Old action", "reason": "Superseded work."},
                    supersedes_workflow_action_id=1,
                    created_at="2026-08-13T09:07:00Z",
                    updated_at="2026-08-13T09:07:00Z",
                ),
            ),
        )
        projection = build_working_proposal_projection(snapshot, metadata=TestConsoleCaseMetadata(label="Superseded"))

        self.assertEqual(len(projection.next_actions), 1)
        self.assertEqual(projection.next_actions[0].label, "Current action")
        self.assertNotIn("Old action", [item.label for item in projection.next_actions])

    def test_follow_up_due_is_shown_without_implying_message_sent(self) -> None:
        snapshot = WorkflowOrchestrationCaseSnapshot(
            rental_case=make_case(),
            follow_ups=(
                FollowUp(
                    follow_up_id=1,
                    rental_case_id=1,
                    reason_code="client_follow_up",
                    due_at="2026-08-15T09:00:00Z",
                    urgency_level=FOLLOW_UP_URGENCY_MEDIUM,
                    attempt_count=0,
                    status=FOLLOW_UP_STATUS_DUE,
                    created_at="2026-08-14T09:00:00Z",
                    updated_at="2026-08-14T09:00:00Z",
                ),
            ),
        )
        projection = build_working_proposal_projection(
            snapshot,
            metadata=TestConsoleCaseMetadata(label="Follow-up"),
            latest_communication=LatestCommunicationContext(
                occurred_at="2026-08-14T08:00:00Z",
                sender="client@example.test",
                subject="Checking in",
            ),
        )

        follow_up = find_item(projection.communication, "Follow-up #1: Client Follow Up")
        self.assertEqual(follow_up.value, "Due")
        self.assertEqual(follow_up.state, DISPLAY_STATE_BLOCKED)
        self.assertNotIn("sent", (follow_up.detail or "").lower())

    def test_stale_proposal_artifact_is_visible(self) -> None:
        snapshot = WorkflowOrchestrationCaseSnapshot(
            rental_case=make_case(),
            artifacts=(
                ArtifactReference(
                    artifact_reference_id=1,
                    rental_case_id=1,
                    artifact_type=ARTIFACT_TYPE_PROPOSAL,
                    derived_from_case_revision=1,
                    freshness_status=ARTIFACT_FRESHNESS_STALE,
                    storage_reference="artifact:proposal:1",
                    created_at="2026-08-14T09:00:00Z",
                    updated_at="2026-08-14T10:00:00Z",
                ),
            ),
        )

        projection = build_working_proposal_projection(snapshot, metadata=TestConsoleCaseMetadata())

        proposal_status = find_item(projection.proposal_freshness, "Proposal artifact")
        self.assertEqual(proposal_status.value, "Stale")
        self.assertEqual(proposal_status.state, DISPLAY_STATE_STALE)
        self.assertIn("Current case revision is 4.", proposal_status.detail or "")


if __name__ == "__main__":
    unittest.main()
