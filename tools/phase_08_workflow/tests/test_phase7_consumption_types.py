from __future__ import annotations

import unittest

from tools.phase_07_reasoning.contracts import AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT
from tools.phase_08_workflow.phase7_consumption_types import (
    WORKFLOW_REASONING_EFFECT_CURRENT_TRUTH_AVAILABLE,
    WorkflowReasoningEffect,
)


class Phase7ConsumptionTypesTests(unittest.TestCase):
    def test_workflow_reasoning_effect_allows_zero_source_case_revision(self) -> None:
        effect = WorkflowReasoningEffect(
            effect_type_code=WORKFLOW_REASONING_EFFECT_CURRENT_TRUTH_AVAILABLE,
            rental_case_id=1,
            reasoning_purpose="proposal_readiness_review",
            source_case_revision=0,
            authority_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
            source_projection_identity_key="p7wf:test",
            blocking_relevance=False,
        )
        self.assertEqual(effect.source_case_revision, 0)


if __name__ == "__main__":
    unittest.main()
