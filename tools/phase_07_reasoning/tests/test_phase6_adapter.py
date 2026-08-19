from __future__ import annotations

import json
import unittest

from tools.phase_06_search.historical_retrieval import HistoricalRetrievalError
from tools.phase_07_reasoning.contracts import (
    AUTHORITY_TIER_HISTORICAL_PRECEDENT,
    EXECUTION_STATE_FAILED,
    EXECUTION_STATE_FALLBACK,
    EXECUTION_STATE_NOT_REQUESTED,
    EXECUTION_STATE_NO_RESULTS,
    EXECUTION_STATE_SUCCESS,
    EXECUTION_STATE_UNAVAILABLE,
    LAYER_ID_PHASE_6,
    PERSONAL_INFORMATION_STATUS_NO,
    PERSONAL_INFORMATION_STATUS_UNKNOWN,
    PERSONAL_INFORMATION_STATUS_YES,
    QUERY_CLASS_PRECEDENT_DISCOVERY,
    ROUTING_CONFIDENCE_HIGH,
    Phase6FilterIntent,
    Phase6RoutingIntent,
    Phase7RuntimeConfiguration,
    QueryPlan,
    SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT,
)
from tools.phase_07_reasoning.phase6_adapter import execute_phase6_plan


def make_plan(
    *,
    query_text: str = "Have we handled a similar floral issue before?",
    phase6_query_text: str | None = None,
    required: bool = True,
    result_limit: int | None = 1,
    filters: Phase6FilterIntent | None = None,
) -> QueryPlan:
    return QueryPlan(
        query_text=query_text,
        query_class=QUERY_CLASS_PRECEDENT_DISCOVERY,
        routing_confidence=ROUTING_CONFIDENCE_HIGH,
        required_layers=(LAYER_ID_PHASE_6,) if required else (),
        phase_6=Phase6RoutingIntent(
            required=required,
            query_text=phase6_query_text or query_text,
            result_limit=result_limit,
            filters=filters or Phase6FilterIntent(),
            reason_codes=("phase6_adapter_test",),
        ),
    )


def make_hybrid_row(
    *,
    search_unit_id: int = 37,
    source_key: str = "decision:9",
    case_code: str = "HC-003",
    unit_type: str = "decision",
) -> dict:
    return {
        "search_unit_id": search_unit_id,
        "source_layer_role": "historical_precedent",
        "source_key": source_key,
        "unit_type": unit_type,
        "search_text": "We reduced floral scope after storage overruns and documented the client-approval path.",
        "historical_case_id": 3,
        "historical_case_version_id": 3,
        "case_code": case_code,
        "case_title": "Case 03: WineGB Trade & Press Showcase",
        "precedent_type": "full_case",
        "precedent_availability": "limited",
        "case_evidence_strength": "strong",
        "unit_evidence_strength": "strong",
        "actor_type": "internal_staff",
        "lesson_kind": None,
        "historical_value_only": True,
        "contamination_risk_level": "high",
        "current_authority_disposition": "current_status_unknown",
        "case_contains_historical_value_only_content": True,
        "effective_confidentiality_level_id": 4,
        "effective_confidentiality_level_code": "restricted",
        "case_personal_information_status": "yes",
        "source_object_personal_information_status": "yes",
        "primary_historical_case_version_source_object_id": 81,
        "primary_source_object_id": 91,
        "primary_source_locator": "Case 03: WineGB Trade & Press Showcase",
        "source_link_count": 1,
        "responsibility_id": None,
        "decision_id": 9,
        "lesson_id": None,
        "embedding_model_id": 13,
        "provider_code": "openai",
        "model_code": "text-embedding-3-small",
        "model_version": None,
        "strategy_code": "historical_rrf_balanced",
        "came_from_fts": True,
        "came_from_semantic": True,
        "fts_rank": 1,
        "semantic_rank": 2,
        "best_component_rank": 1,
        "lexical_score": 0.0285714,
        "semantic_similarity_score": 0.325849168355586,
        "semantic_cosine_distance": 0.674150831644414,
        "rrf_k": 20,
        "lexical_weight": 1.0,
        "semantic_weight": 1.0,
        "rrf_fts_score": 0.05,
        "rrf_semantic_score": 0.0452380952380952,
        "hybrid_score": 0.0952380952380952,
    }


def make_narrative_row() -> dict:
    row = make_hybrid_row(
        search_unit_id=27,
        source_key="case_narrative:3",
        unit_type="case_narrative",
    )
    row["historical_value_only"] = None
    row["contamination_risk_level"] = None
    row["current_authority_disposition"] = None
    row["lesson_kind"] = None
    row["decision_id"] = None
    return row


def make_response(*, rows: list[dict], retrieval_mode_used: str = "hybrid", fallback_reason: str | None = None) -> dict:
    return {
        "query_text": "Have we handled a similar floral issue before?",
        "retrieval_mode_requested": "hybrid",
        "retrieval_mode_used": retrieval_mode_used,
        "fallback_used": retrieval_mode_used == "fts_fallback",
        "fallback_reason": fallback_reason,
        "strategy_code": "historical_rrf_balanced",
        "configuration_code": "historical_rrf_balanced_d20",
        "result_limit_requested": 3,
        "result_limit_used": 3,
        "candidate_pool_limit": None if retrieval_mode_used == "fts_fallback" else 20,
        "embedding_model": {
            "embedding_model_id": 13,
            "provider_code": "openai",
            "model_code": "text-embedding-3-small",
            "model_version": None,
            "embedding_dimensions": 1536,
            "config_fingerprint": "cfg-1",
        },
        "historical_embedding_state": {
            "embedding_model_id": 13,
            "eligible_unit_count": 112,
            "current_embedding_count": 112,
            "missing_unit_count": 0,
            "stale_unit_count": 0,
            "is_complete": True,
        },
        "result_count": len(rows),
        "timing_ms": {
            "embedding_generation": None if retrieval_mode_used == "fts_fallback" else 12.34,
            "retrieval": 23.45,
            "total": 36.79,
        },
        "results": rows,
    }


class Phase6AdapterTests(unittest.TestCase):
    def test_not_requested_behavior_skips_retrieval(self) -> None:
        plan = make_plan(required=False)
        calls: list[str] = []

        def unexpected_retrieval(*_args, **_kwargs):
            calls.append("retrieval")
            raise AssertionError("historical retrieval should not be called")

        record = execute_phase6_plan(
            plan,
            historical_retrieval_fn=unexpected_retrieval,
        )

        self.assertFalse(record.requested)
        self.assertEqual(record.execution_state, EXECUTION_STATE_NOT_REQUESTED)
        self.assertEqual(record.result_count, 0)
        self.assertEqual(calls, [])

    def test_healthy_hybrid_normalizes_results_and_uses_runtime_limit_and_filters(self) -> None:
        filters = Phase6FilterIntent(
            case_code="hc-003",
            unit_type="decision",
            precedent_availability="limited",
            precedent_type="full_case",
            lesson_kind=None,
            historical_value_only=True,
            contamination_risk_level="high",
        )
        plan = make_plan(
            query_text="generic query",
            phase6_query_text="specific historical query",
            result_limit=1,
            filters=filters,
        )
        runtime_config = Phase7RuntimeConfiguration(phase_6_result_limit=3)
        observed: dict[str, object] = {}

        def retrieval_fn(query_text, **kwargs):
            observed["query_text"] = query_text
            observed["kwargs"] = kwargs
            return make_response(rows=[make_hybrid_row(), make_narrative_row()])

        record = execute_phase6_plan(
            plan,
            runtime_configuration=runtime_config,
            historical_retrieval_fn=retrieval_fn,
        )

        self.assertTrue(record.requested)
        self.assertEqual(record.execution_state, EXECUTION_STATE_SUCCESS)
        self.assertEqual(record.result_count, 2)
        item = record.normalized_items[0]
        self.assertEqual(item.source_layer_role, SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT)
        self.assertEqual(item.authority_tier_code, AUTHORITY_TIER_HISTORICAL_PRECEDENT)
        self.assertEqual(item.authority_priority, 3)
        self.assertEqual(item.execution_state, EXECUTION_STATE_SUCCESS)
        self.assertEqual(item.summary_text, make_hybrid_row()["search_text"])
        self.assertEqual(item.stable_identity.primary_code, "HC-003")
        self.assertEqual(item.stable_identity.secondary_code, "decision:9")
        self.assertEqual(item.exact_identity.primary_id, 3)
        self.assertEqual(item.exact_identity.secondary_id, 37)
        self.assertEqual(item.content_kind, "phase6_historical_decision")
        self.assertEqual(item.retrieval.retrieval_mode_used, "hybrid")
        self.assertFalse(item.retrieval.fallback_used)
        self.assertEqual(item.retrieval.rank, 1)
        self.assertAlmostEqual(item.retrieval.score, 0.0952380952380952)
        self.assertEqual(item.sensitivity.personal_information_status, PERSONAL_INFORMATION_STATUS_YES)
        self.assertTrue(item.sensitivity.de_identification_required)
        self.assertEqual(item.provenance.source_codes, ("HC-003", "decision:9"))
        self.assertEqual(item.provenance.source_link_count, 1)
        self.assertEqual(item.layer_payload["phase6_configuration_code"], "historical_rrf_balanced_d20")
        self.assertEqual(item.layer_payload["historical_value_only"], True)

        narrative_item = record.normalized_items[1]
        self.assertEqual(narrative_item.content_kind, "phase6_historical_case_narrative")
        self.assertIsNone(narrative_item.layer_payload["historical_value_only"])
        self.assertIsNone(narrative_item.layer_payload["contamination_risk_level"])
        self.assertIsNone(narrative_item.layer_payload["current_authority_disposition"])

        self.assertEqual(observed["query_text"], "specific historical query")
        self.assertEqual(
            observed["kwargs"],
            {
                "result_limit": 3,
                "case_code": "hc-003",
                "unit_type": "decision",
                "precedent_availability": "limited",
                "precedent_type": "full_case",
                "lesson_kind": None,
                "historical_value_only": True,
                "contamination_risk_level": "high",
            },
        )

    def test_fallback_mode_preserves_degraded_labeling_and_metadata(self) -> None:
        plan = make_plan()

        def retrieval_fn(_query_text, **_kwargs):
            row = make_hybrid_row()
            row["embedding_model_id"] = None
            row["provider_code"] = None
            row["model_code"] = None
            row["strategy_code"] = None
            row["came_from_semantic"] = False
            row["semantic_rank"] = None
            row["semantic_similarity_score"] = None
            row["semantic_cosine_distance"] = None
            row["rrf_k"] = None
            row["hybrid_score"] = None
            row["lexical_score"] = 0.031
            return make_response(
                rows=[row],
                retrieval_mode_used="fts_fallback",
                fallback_reason="embedding_model_resolution_failed",
            )

        record = execute_phase6_plan(
            plan,
            historical_retrieval_fn=retrieval_fn,
        )

        self.assertEqual(record.execution_state, EXECUTION_STATE_FALLBACK)
        self.assertEqual(record.fallback_reason, "embedding_model_resolution_failed")
        item = record.normalized_items[0]
        self.assertEqual(item.execution_state, EXECUTION_STATE_FALLBACK)
        self.assertEqual(item.retrieval.retrieval_mode_used, "fts_fallback")
        self.assertTrue(item.retrieval.fallback_used)
        self.assertEqual(item.retrieval.fallback_reason, "embedding_model_resolution_failed")
        self.assertAlmostEqual(item.retrieval.score, 0.031)
        self.assertIsNone(item.retrieval.native_retrieval_payload["semantic_rank"])

    def test_no_results_is_distinct_from_failure(self) -> None:
        plan = make_plan()

        record = execute_phase6_plan(
            plan,
            historical_retrieval_fn=lambda _query_text, **_kwargs: make_response(rows=[]),
        )

        self.assertEqual(record.execution_state, EXECUTION_STATE_NO_RESULTS)
        self.assertEqual(record.result_count, 0)
        self.assertEqual(record.normalized_items, ())

    def test_database_unavailable_maps_to_unavailable(self) -> None:
        plan = make_plan()

        def retrieval_fn(_query_text, **_kwargs):
            raise HistoricalRetrievalError(
                error_category="database_unavailable",
                safe_message="Historical retrieval could not reach the local database.",
            )

        record = execute_phase6_plan(
            plan,
            historical_retrieval_fn=retrieval_fn,
        )

        self.assertEqual(record.execution_state, EXECUTION_STATE_UNAVAILABLE)
        self.assertEqual(record.error_category, "database_unavailable")
        self.assertEqual(record.result_count, 0)

    def test_non_database_retrieval_error_maps_to_failed(self) -> None:
        plan = make_plan()

        def retrieval_fn(_query_text, **_kwargs):
            raise HistoricalRetrievalError(
                error_category="hybrid_function_failed",
                safe_message="Historical hybrid retrieval failed before any safe result set could be returned.",
            )

        record = execute_phase6_plan(
            plan,
            historical_retrieval_fn=retrieval_fn,
        )

        self.assertEqual(record.execution_state, EXECUTION_STATE_FAILED)
        self.assertEqual(record.error_category, "hybrid_function_failed")
        self.assertEqual(record.result_count, 0)

    def test_personal_information_status_falls_back_to_unknown(self) -> None:
        plan = make_plan()

        def retrieval_fn(_query_text, **_kwargs):
            row = make_hybrid_row()
            row["source_object_personal_information_status"] = None
            row["case_personal_information_status"] = "mystery_value"
            return make_response(rows=[row])

        record = execute_phase6_plan(
            plan,
            historical_retrieval_fn=retrieval_fn,
        )

        item = record.normalized_items[0]
        self.assertEqual(item.sensitivity.personal_information_status, PERSONAL_INFORMATION_STATUS_UNKNOWN)
        self.assertFalse(item.sensitivity.de_identification_required)

    def test_personal_information_status_maps_not_present_to_no(self) -> None:
        plan = make_plan()

        def retrieval_fn(_query_text, **_kwargs):
            row = make_hybrid_row()
            row["source_object_personal_information_status"] = "not_present"
            row["case_personal_information_status"] = "yes"
            return make_response(rows=[row])

        record = execute_phase6_plan(
            plan,
            historical_retrieval_fn=retrieval_fn,
        )

        item = record.normalized_items[0]
        self.assertEqual(item.sensitivity.personal_information_status, PERSONAL_INFORMATION_STATUS_NO)
        self.assertFalse(item.sensitivity.de_identification_required)

    def test_json_serialization_preserves_historical_payload(self) -> None:
        plan = make_plan()

        record = execute_phase6_plan(
            plan,
            historical_retrieval_fn=lambda _query_text, **_kwargs: make_response(rows=[make_hybrid_row()]),
        )

        serialized = json.loads(record.to_json())
        self.assertEqual(serialized["layer_id"], LAYER_ID_PHASE_6)
        self.assertEqual(serialized["normalized_items"][0]["source_layer_role"], SOURCE_LAYER_ROLE_HISTORICAL_PRECEDENT)
        self.assertEqual(
            serialized["normalized_items"][0]["layer_payload"]["phase6_configuration_code"],
            "historical_rrf_balanced_d20",
        )


if __name__ == "__main__":
    unittest.main()
