from __future__ import annotations

from dataclasses import replace
import unittest

from tools.phase_07_reasoning.context_safety import finalize_context_safety
from tools.phase_07_reasoning.contracts import (
    AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
    AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
    AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION,
    CONFIDENTIALITY_LEVEL_RESTRICTED,
    PERSONAL_INFORMATION_STATUS_YES,
    QUERY_CLASS_CURRENT_GUIDANCE,
    QUERY_CLASS_DETERMINISTIC_CURRENT,
    QUERY_CLASS_UNRESOLVED_AUTHORITY,
    SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
    SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
    SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
    AuthorityResolution,
    UncertaintyState,
    UnresolvedAuthorityRecord,
)
from tools.phase_07_reasoning.tests.test_context_safety import make_item, make_package
from tools.phase_08_workflow.contracts import (
    LIFECYCLE_STATE_INQUIRY_ACTIVE,
    RentalCase,
    WORKFLOW_REASONING_POSTURE_BLOCKED_FOR_CURRENT_DECISION,
    WORKFLOW_REASONING_POSTURE_REVIEW_REQUIRED,
    WORKFLOW_REASONING_POSTURE_SAFE_FOR_DETERMINISTIC_USE,
)
from tools.phase_08_workflow.phase7_consumption_repository import (
    InMemoryPhase7ConsumptionRepository,
)
from tools.phase_08_workflow.phase7_consumption_types import (
    PHASE7_CONSUMPTION_FAILURE_INVALID_LAYER_IDENTITY,
    PHASE7_CONSUMPTION_FAILURE_STALE_CASE_REVISION,
    PHASE7_CONSUMPTION_FAILURE_UNSUPPORTED_PHASE7_CONTRACT,
    PHASE7_CONSUMPTION_STATUS_CONSUMED,
    PHASE7_CONSUMPTION_STATUS_DUPLICATE,
    PHASE7_CONSUMPTION_STATUS_FAILED,
    WORKFLOW_REASONING_EFFECT_CONFIRMATION_REQUIRED,
    WORKFLOW_REASONING_EFFECT_CURRENT_AUTHORITY_MISSING,
    WORKFLOW_REASONING_EFFECT_CURRENT_TRUTH_AVAILABLE,
    WORKFLOW_REASONING_EFFECT_REVIEW_REQUIRED,
)
from tools.phase_08_workflow.phase7_workflow_consumer import consume_phase7_context


def make_case(*, rental_case_id: int = 1, case_revision: int = 0) -> RentalCase:
    return RentalCase(
        rental_case_id=rental_case_id,
        rental_case_uuid=f"case-{rental_case_id}",
        case_reference_code=f"RC-{900 + rental_case_id}",
        lifecycle_state=LIFECYCLE_STATE_INQUIRY_ACTIVE,
        case_revision=case_revision,
        rental_type_code="studio_space",
        commercial_summary_status="unknown",
        operational_summary_status="unknown",
        is_active=True,
    )


def make_repository(*, rental_case_id: int = 1, case_revision: int = 0) -> InMemoryPhase7ConsumptionRepository:
    return InMemoryPhase7ConsumptionRepository(
        rental_cases={rental_case_id: make_case(rental_case_id=rental_case_id, case_revision=case_revision)},
        reasoning_projections={},
        projection_ids_by_identity={},
    )


class Phase7WorkflowConsumerTests(unittest.TestCase):
    def test_consumes_deterministic_current_into_safe_projection(self) -> None:
        repository = make_repository(case_revision=3)
        phase4_item = make_item(
            item_id="rule:booking_fee",
            source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
            primary_code="RULE-BOOKING-FEE",
            primary_id=1,
            summary_text="Booking fee is required.",
        )
        package = make_package(
            query_text="Is the booking fee required?",
            query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
            phase4_items=(phase4_item,),
            phase4_requested=True,
            phase4_state="success",
            authority_resolution=AuthorityResolution(
                overall_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                resolved_current_truth_item_ids=("rule:booking_fee",),
            ),
        )

        result = consume_phase7_context(
            rental_case_id=1,
            expected_case_revision=3,
            reasoning_purpose="proposal_readiness_review",
            context_package=package,
            repository=repository,
        )

        self.assertEqual(result.status, PHASE7_CONSUMPTION_STATUS_CONSUMED)
        self.assertEqual(result.posture.posture_code, WORKFLOW_REASONING_POSTURE_SAFE_FOR_DETERMINISTIC_USE)
        self.assertEqual(result.projection.reasoning_state_code, "resolved")
        self.assertEqual(result.projection.relevant_current_truth_item_ids, ("rule:booking_fee",))
        self.assertIn(
            WORKFLOW_REASONING_EFFECT_CURRENT_TRUTH_AVAILABLE,
            {effect.effect_type_code for effect in result.workflow_effects},
        )
        self.assertEqual(len(repository.reasoning_projections[1]), 1)

    def test_duplicate_consumption_is_idempotent(self) -> None:
        repository = make_repository(case_revision=1)
        phase4_item = make_item(
            item_id="rule:access",
            source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
            primary_code="RULE-ACCESS",
            primary_id=2,
            summary_text="Current access rule.",
        )
        package = make_package(
            query_text="What is the access rule?",
            query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
            phase4_items=(phase4_item,),
            phase4_requested=True,
            phase4_state="success",
            authority_resolution=AuthorityResolution(
                overall_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                resolved_current_truth_item_ids=("rule:access",),
            ),
        )

        first = consume_phase7_context(
            rental_case_id=1,
            expected_case_revision=1,
            reasoning_purpose="case_decision_baseline",
            context_package=package,
            repository=repository,
        )
        second = consume_phase7_context(
            rental_case_id=1,
            expected_case_revision=1,
            reasoning_purpose="case_decision_baseline",
            context_package=package,
            repository=repository,
        )

        self.assertEqual(first.status, PHASE7_CONSUMPTION_STATUS_CONSUMED)
        self.assertEqual(second.status, PHASE7_CONSUMPTION_STATUS_DUPLICATE)
        self.assertTrue(second.duplicate_projection)
        self.assertEqual(first.projection.reasoning_projection_id, second.projection.reasoning_projection_id)
        self.assertEqual(len(repository.reasoning_projections[1]), 1)

    def test_requires_confirmation_becomes_review_posture_and_effect(self) -> None:
        repository = make_repository(case_revision=2)
        phase5_item = make_item(
            item_id="guidance:confirmation",
            source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
            primary_code="GUIDE-CONFIRM",
            primary_id=3,
            summary_text="Confirmation is required before committing.",
        )
        package = make_package(
            query_text="Can we confirm this now?",
            query_class=QUERY_CLASS_CURRENT_GUIDANCE,
            phase5_items=(phase5_item,),
            phase5_requested=True,
            phase5_state="success",
            authority_resolution=AuthorityResolution(
                overall_outcome_classification=AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION,
                current_guidance_item_ids=("guidance:confirmation",),
                unresolved_authority_records=(
                    UnresolvedAuthorityRecord(
                        reasoning_state="requires_confirmation",
                        topic_or_domain="confirmation",
                        explanation_code="requires_confirmation",
                    ),
                ),
            ),
            uncertainty_state=UncertaintyState(
                True,
                unresolved_records=(
                    UnresolvedAuthorityRecord(
                        reasoning_state="requires_confirmation",
                        topic_or_domain="confirmation",
                        explanation_code="requires_confirmation",
                    ),
                ),
            ),
        )

        result = consume_phase7_context(
            rental_case_id=1,
            expected_case_revision=2,
            reasoning_purpose="proposal_readiness_review",
            context_package=package,
            repository=repository,
        )

        self.assertEqual(result.status, PHASE7_CONSUMPTION_STATUS_CONSUMED)
        self.assertEqual(result.posture.posture_code, WORKFLOW_REASONING_POSTURE_REVIEW_REQUIRED)
        self.assertTrue(result.posture.confirmation_required)
        effect_codes = {effect.effect_type_code for effect in result.workflow_effects}
        self.assertIn(WORKFLOW_REASONING_EFFECT_CONFIRMATION_REQUIRED, effect_codes)
        self.assertIn(WORKFLOW_REASONING_EFFECT_REVIEW_REQUIRED, effect_codes)

    def test_insufficient_current_authority_blocks_current_decision(self) -> None:
        repository = make_repository(case_revision=4)
        unresolved = UnresolvedAuthorityRecord(
            reasoning_state="insufficient_current_authority",
            topic_or_domain="pricing",
            explanation_code="current_policy_missing",
        )
        package = make_package(
            query_text="What is the current price?",
            query_class=QUERY_CLASS_UNRESOLVED_AUTHORITY,
            authority_resolution=AuthorityResolution(
                overall_outcome_classification=AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
                unresolved_authority_records=(unresolved,),
            ),
            uncertainty_state=UncertaintyState(True, unresolved_records=(unresolved,)),
        )

        result = consume_phase7_context(
            rental_case_id=1,
            expected_case_revision=4,
            reasoning_purpose="commercial_rule_review",
            context_package=package,
            repository=repository,
        )

        self.assertEqual(result.status, PHASE7_CONSUMPTION_STATUS_CONSUMED)
        self.assertEqual(result.posture.posture_code, WORKFLOW_REASONING_POSTURE_BLOCKED_FOR_CURRENT_DECISION)
        effect_codes = {effect.effect_type_code for effect in result.workflow_effects}
        self.assertIn(WORKFLOW_REASONING_EFFECT_CURRENT_AUTHORITY_MISSING, effect_codes)
        self.assertIn(WORKFLOW_REASONING_EFFECT_REVIEW_REQUIRED, effect_codes)

    def test_context_safety_confidentiality_fields_carry_into_projection(self) -> None:
        repository = make_repository(case_revision=5)
        historical_item = make_item(
            item_id="history:pi",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HC-PI",
            primary_id=4,
            summary_text="Named contact arranged a restricted exception.",
            confidentiality_level=CONFIDENTIALITY_LEVEL_RESTRICTED,
            pi_status=PERSONAL_INFORMATION_STATUS_YES,
            de_identification_required=True,
        )
        safe_package = finalize_context_safety(
            make_package(
                query_text="What precedent exists?",
                query_class=QUERY_CLASS_CURRENT_GUIDANCE,
                phase6_items=(historical_item,),
                phase6_requested=True,
                phase6_state="success",
                authority_resolution=AuthorityResolution(
                    overall_outcome_classification=AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION,
                    historical_precedent_item_ids=("history:pi",),
                    unresolved_authority_records=(
                        UnresolvedAuthorityRecord(
                            reasoning_state="requires_confirmation",
                            topic_or_domain="exception",
                            explanation_code="historical_only_confirmation_required",
                        ),
                    ),
                ),
                uncertainty_state=UncertaintyState(
                    True,
                    unresolved_records=(
                        UnresolvedAuthorityRecord(
                            reasoning_state="requires_confirmation",
                            topic_or_domain="exception",
                            explanation_code="historical_only_confirmation_required",
                        ),
                    ),
                ),
            )
        )

        result = consume_phase7_context(
            rental_case_id=1,
            expected_case_revision=5,
            reasoning_purpose="compliance_requirement_review",
            context_package=safe_package,
            repository=repository,
        )

        self.assertEqual(result.status, PHASE7_CONSUMPTION_STATUS_CONSUMED)
        self.assertEqual(result.projection.effective_confidentiality_level, "restricted")
        self.assertTrue(result.projection.de_identification_required)
        self.assertFalse(result.projection.personal_information_present)

    def test_invalid_historical_item_as_current_truth_fails_closed(self) -> None:
        repository = make_repository(case_revision=1)
        historical_item = make_item(
            item_id="history:price",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HC-PRICE",
            primary_id=5,
            summary_text="Historical price only.",
        )
        package = make_package(
            query_text="What is the price now?",
            query_class=QUERY_CLASS_CURRENT_GUIDANCE,
            phase6_items=(historical_item,),
            phase6_requested=True,
            phase6_state="success",
            authority_resolution=AuthorityResolution(
                overall_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                resolved_current_truth_item_ids=("history:price",),
            ),
        )

        result = consume_phase7_context(
            rental_case_id=1,
            expected_case_revision=1,
            reasoning_purpose="commercial_rule_review",
            context_package=package,
            repository=repository,
        )

        self.assertEqual(result.status, PHASE7_CONSUMPTION_STATUS_FAILED)
        self.assertEqual(result.failure_codes, (PHASE7_CONSUMPTION_FAILURE_INVALID_LAYER_IDENTITY,))

    def test_case_revision_and_phase7_contract_mismatches_fail_closed(self) -> None:
        repository = make_repository(case_revision=2)
        package = make_package(
            query_text="Revision check",
            query_class=QUERY_CLASS_DETERMINISTIC_CURRENT,
            authority_resolution=AuthorityResolution(
                overall_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
            ),
        )

        stale_result = consume_phase7_context(
            rental_case_id=1,
            expected_case_revision=1,
            reasoning_purpose="feasibility_review",
            context_package=package,
            repository=repository,
        )
        bad_version_result = consume_phase7_context(
            rental_case_id=1,
            expected_case_revision=2,
            reasoning_purpose="feasibility_review",
            context_package=replace(package, context_contract_version=99),
            repository=repository,
        )

        self.assertEqual(stale_result.status, PHASE7_CONSUMPTION_STATUS_FAILED)
        self.assertEqual(stale_result.failure_codes, (PHASE7_CONSUMPTION_FAILURE_STALE_CASE_REVISION,))
        self.assertEqual(bad_version_result.status, PHASE7_CONSUMPTION_STATUS_FAILED)
        self.assertEqual(
            bad_version_result.failure_codes,
            (PHASE7_CONSUMPTION_FAILURE_UNSUPPORTED_PHASE7_CONTRACT,),
        )


if __name__ == "__main__":
    unittest.main()
