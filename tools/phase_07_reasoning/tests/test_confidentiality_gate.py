from __future__ import annotations

import unittest

from tools.phase_07_reasoning.confidentiality_gate import (
    SUPPRESSION_REASON_PI_BEARING_RESTRICTED_HISTORICAL,
    SUPPRESSION_REASON_RESTRICTED_HISTORICAL,
    finalize_confidentiality_state,
)
from tools.phase_07_reasoning.contracts import (
    AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY,
    EXECUTION_STATE_SUCCESS,
    ExactIdentity,
    ProvenanceEnvelope,
    RetrievalMetadata,
    SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
    SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
    SensitivityEnvelope,
    StableIdentity,
    AuthorityResolution,
    NormalizedResultEnvelope,
    authority_priority_for_tier,
    authority_tier_for_source_role,
)


def make_item(
    *,
    item_id: str,
    source_layer_role: str,
    primary_code: str,
    primary_id: int,
    confidentiality_level: str,
    pi_status: str,
    de_identification_required: bool,
) -> NormalizedResultEnvelope:
    retrieval = RetrievalMetadata(
        retrieval_mode_requested="hybrid",
        retrieval_mode_used="hybrid",
        fallback_used=False,
        fallback_reason=None,
        rank=1,
        score=1.0,
        component_scores={},
        strategy_code="fixture",
        native_retrieval_payload={},
    )
    return NormalizedResultEnvelope(
        item_id=item_id,
        source_layer_role=source_layer_role,
        authority_tier_code=authority_tier_for_source_role(source_layer_role),
        authority_priority=authority_priority_for_tier(authority_tier_for_source_role(source_layer_role)),
        stable_identity=StableIdentity(primary_code=primary_code),
        exact_identity=ExactIdentity(primary_id=primary_id, version_id=primary_id),
        content_kind="fixture_item",
        execution_state=EXECUTION_STATE_SUCCESS,
        reasoning_state=None,
        summary_text=f"{primary_code} summary",
        provenance=ProvenanceEnvelope(
            source_codes=(primary_code,),
            source_identifiers={"primary_code": primary_code},
            primary_source_locator=f"{primary_code} locator",
            additional_locators=(),
            source_link_count=1,
            native_provenance_payload={},
        ),
        sensitivity=SensitivityEnvelope(
            confidentiality_level=confidentiality_level,
            personal_information_status=pi_status,
            de_identification_required=de_identification_required,
            generation_allowed=True,
            generation_restriction_reason=None,
            native_sensitivity_payload={},
        ),
        retrieval=retrieval,
        layer_payload={},
    )


class ConfidentialityGateTests(unittest.TestCase):
    def test_restricted_historical_detail_is_suppressed_but_generation_can_continue(self) -> None:
        current_item = make_item(
            item_id="p5-current",
            source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
            primary_code="SERV-004",
            primary_id=1,
            confidentiality_level="internal",
            pi_status="no",
            de_identification_required=False,
        )
        historical_item = make_item(
            item_id="p6-historical",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HC-003",
            primary_id=2,
            confidentiality_level="restricted",
            pi_status="no",
            de_identification_required=False,
        )

        state = finalize_confidentiality_state(
            authority_resolution=AuthorityResolution(
                overall_outcome_classification=AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY,
                current_guidance_item_ids=("p5-current",),
                historical_precedent_item_ids=("p6-historical",),
            ),
            phase_4_context=(),
            phase_5_context=(current_item,),
            phase_6_context=(historical_item,),
        )

        self.assertEqual(state.effective_confidentiality_level, "restricted")
        self.assertTrue(state.generation_allowed)
        self.assertEqual(state.suppressed_item_ids, ("p6-historical",))
        self.assertEqual(
            state.suppression_reasons["p6-historical"],
            SUPPRESSION_REASON_RESTRICTED_HISTORICAL,
        )

    def test_pi_bearing_restricted_historical_detail_uses_more_specific_suppression_reason(self) -> None:
        current_item = make_item(
            item_id="p5-current",
            source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
            primary_code="SERV-001",
            primary_id=3,
            confidentiality_level="commercially_sensitive",
            pi_status="no",
            de_identification_required=False,
        )
        historical_item = make_item(
            item_id="p6-pi",
            source_layer_role=SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
            primary_code="HC-001",
            primary_id=4,
            confidentiality_level="restricted",
            pi_status="yes",
            de_identification_required=True,
        )

        state = finalize_confidentiality_state(
            authority_resolution=AuthorityResolution(
                overall_outcome_classification=AUTHORITY_OUTCOME_MIXED_WITH_CURRENT_PRIORITY,
                current_guidance_item_ids=("p5-current",),
                historical_precedent_item_ids=("p6-pi",),
            ),
            phase_4_context=(),
            phase_5_context=(current_item,),
            phase_6_context=(historical_item,),
        )

        self.assertTrue(state.personal_information_present)
        self.assertTrue(state.de_identification_required)
        self.assertEqual(state.suppressed_item_ids, ("p6-pi",))
        self.assertEqual(
            state.suppression_reasons["p6-pi"],
            SUPPRESSION_REASON_PI_BEARING_RESTRICTED_HISTORICAL,
        )


if __name__ == "__main__":
    unittest.main()
