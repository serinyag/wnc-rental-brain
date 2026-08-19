from __future__ import annotations

import unittest
from unittest.mock import patch

from tools.phase_06_search.historical_retrieval import (
    HistoricalRetrievalError,
    normalize_filters,
    retrieve_historical_precedents,
)


class FakeEmbeddingsClient:
    def __init__(self, vector: list[float] | Exception | BaseException) -> None:
        self.vector = vector
        self.calls: list[tuple[list[str], object]] = []

    def embed_texts(self, texts, config):  # noqa: ANN001
        self.calls.append((list(texts), config))
        if isinstance(self.vector, BaseException):
            raise self.vector
        return [self.vector]


class HistoricalRetrievalContractTests(unittest.TestCase):
    def test_normalize_filters_rejects_unsupported_enum_values(self) -> None:
        with self.assertRaisesRegex(HistoricalRetrievalError, "unit_type"):
            normalize_filters(unit_type="unknown")
        with self.assertRaisesRegex(HistoricalRetrievalError, "precedent_availability"):
            normalize_filters(precedent_availability="draft")
        with self.assertRaisesRegex(HistoricalRetrievalError, "precedent_type"):
            normalize_filters(precedent_type="other")
        with self.assertRaisesRegex(HistoricalRetrievalError, "lesson_kind"):
            normalize_filters(lesson_kind="source_explicitish")
        with self.assertRaisesRegex(HistoricalRetrievalError, "contamination_risk_level"):
            normalize_filters(contamination_risk_level="critical")

    def test_retrieve_rejects_empty_query(self) -> None:
        with self.assertRaisesRegex(HistoricalRetrievalError, "non-empty query text"):
            retrieve_historical_precedents("   ")

    def test_query_embedding_failure_uses_explicit_fts_fallback(self) -> None:
        fake_model = {
            "id": 7,
            "provider_code": "openai",
            "model_code": "text-embedding-3-small",
            "model_version": None,
            "embedding_dimensions": 3,
            "config_fingerprint": "fixture",
            "configuration_json": {"distance_metric": "cosine", "input_contract_code": "phase_06_historical_search_unit_embedding_input_v1"},
        }
        fake_coverage = {
            "embedding_model_id": 7,
            "eligible_unit_count": 112,
            "current_embedding_count": 112,
            "missing_unit_count": 0,
            "stale_unit_count": 0,
        }
        fallback_rows = [
            {
                "search_unit_id": 1,
                "source_layer_role": "historical_precedent",
                "source_key": "HC-009:decision:1",
                "unit_type": "decision",
                "search_text": "Historical ADE solution is not current legal precedent.",
                "lexical_score": 0.75,
                "historical_case_id": 9,
                "historical_case_version_id": 9,
                "case_code": "HC-009",
                "case_title": "ADE Event: Permit, Alcohol, Sound & Operational Compliance",
                "precedent_type": "cautionary_precedent",
                "precedent_availability": "limited",
                "case_evidence_strength": "high",
                "unit_evidence_strength": "high",
                "actor_type": None,
                "lesson_kind": None,
                "historical_value_only": True,
                "contamination_risk_level": "high",
                "current_authority_disposition": "potential_conflict_with_current_knowledge",
                "case_contains_historical_value_only_content": True,
                "effective_confidentiality_level_id": 1,
                "effective_confidentiality_level_code": "restricted",
                "case_personal_information_status": "not_present",
                "source_object_personal_information_status": "not_present",
                "primary_historical_case_version_source_object_id": 9,
                "primary_source_object_id": 9,
                "primary_source_locator": "ADE Event: Permit, Alcohol, Sound & Operational Compliance",
                "source_link_count": 1,
                "responsibility_id": None,
                "decision_id": 9,
                "lesson_id": None,
                "embedding_model_id": None,
                "provider_code": None,
                "model_code": None,
                "model_version": None,
                "strategy_code": None,
                "came_from_fts": True,
                "came_from_semantic": False,
                "fts_rank": 1,
                "semantic_rank": None,
                "best_component_rank": 1,
                "semantic_similarity_score": None,
                "semantic_cosine_distance": None,
                "rrf_k": None,
                "lexical_weight": None,
                "semantic_weight": None,
                "rrf_fts_score": None,
                "rrf_semantic_score": None,
                "hybrid_score": None,
            }
        ]
        with (
            patch("tools.phase_06_search.historical_retrieval.load_active_historical_retrieval_model", return_value=fake_model),
            patch("tools.phase_06_search.historical_retrieval.fetch_historical_embedding_coverage", return_value=fake_coverage),
            patch("tools.phase_06_search.historical_retrieval.run_historical_fts_search", return_value=(fallback_rows, 4.2)),
        ):
            response = retrieve_historical_precedents(
                "current legal precedent",
                embeddings_client=FakeEmbeddingsClient(RuntimeError("boom")),
            )
        self.assertEqual(response["retrieval_mode_requested"], "hybrid")
        self.assertEqual(response["retrieval_mode_used"], "fts_fallback")
        self.assertTrue(response["fallback_used"])
        self.assertEqual(response["fallback_reason"], "query_embedding_failed")
        self.assertEqual(response["results"][0]["source_layer_role"], "historical_precedent")
        self.assertEqual(response["results"][0]["precedent_availability"], "limited")
        self.assertEqual(response["results"][0]["came_from_fts"], True)
        self.assertEqual(response["results"][0]["came_from_semantic"], False)
        self.assertIsNone(response["results"][0]["hybrid_score"])

    def test_incomplete_embedding_state_uses_fts_fallback_without_embedding_call(self) -> None:
        fake_model = {
            "id": 7,
            "provider_code": "openai",
            "model_code": "text-embedding-3-small",
            "model_version": None,
            "embedding_dimensions": 3,
            "config_fingerprint": "fixture",
            "configuration_json": {"distance_metric": "cosine", "input_contract_code": "phase_06_historical_search_unit_embedding_input_v1"},
        }
        incomplete_coverage = {
            "embedding_model_id": 7,
            "eligible_unit_count": 112,
            "current_embedding_count": 111,
            "missing_unit_count": 1,
            "stale_unit_count": 0,
        }
        fake_client = FakeEmbeddingsClient([0.1, 0.2, 0.3])
        with (
            patch("tools.phase_06_search.historical_retrieval.load_active_historical_retrieval_model", return_value=fake_model),
            patch("tools.phase_06_search.historical_retrieval.fetch_historical_embedding_coverage", return_value=incomplete_coverage),
            patch("tools.phase_06_search.historical_retrieval.run_historical_fts_search", return_value=([], 3.5)),
        ):
            response = retrieve_historical_precedents("permit compliance", embeddings_client=fake_client)
        self.assertEqual(response["retrieval_mode_used"], "fts_fallback")
        self.assertEqual(response["fallback_reason"], "historical_embedding_corpus_incomplete")
        self.assertEqual(fake_client.calls, [])

    def test_fts_fallback_failure_raises_explicit_error(self) -> None:
        fake_model = {
            "id": 7,
            "provider_code": "openai",
            "model_code": "text-embedding-3-small",
            "model_version": None,
            "embedding_dimensions": 3,
            "config_fingerprint": "fixture",
            "configuration_json": {"distance_metric": "cosine", "input_contract_code": "phase_06_historical_search_unit_embedding_input_v1"},
        }
        fake_coverage = {
            "embedding_model_id": 7,
            "eligible_unit_count": 112,
            "current_embedding_count": 112,
            "missing_unit_count": 0,
            "stale_unit_count": 0,
        }
        with (
            patch("tools.phase_06_search.historical_retrieval.load_active_historical_retrieval_model", return_value=fake_model),
            patch("tools.phase_06_search.historical_retrieval.fetch_historical_embedding_coverage", return_value=fake_coverage),
            patch("tools.phase_06_search.historical_retrieval.run_historical_fts_search", side_effect=HistoricalRetrievalError(error_category="fts_fallback_failed", safe_message="failed")),
        ):
            with self.assertRaisesRegex(HistoricalRetrievalError, "failed"):
                retrieve_historical_precedents(
                    "permit compliance",
                    embeddings_client=FakeEmbeddingsClient(RuntimeError("boom")),
                )

    def test_live_hybrid_order_matches_direct_hybrid_and_stays_phase6_only(self) -> None:
        from tools.phase_06_search.retrieval_common import load_active_historical_retrieval_model

        model = load_active_historical_retrieval_model()
        vector = [0.0] * model["embedding_dimensions"]
        vector[0] = 1.0
        fake_client = FakeEmbeddingsClient(vector)

        with patch("tools.phase_06_search.historical_retrieval.run_supabase_query") as query_runner:
            from tools.phase_05_chunking.generate_pilot import run_supabase_query as live_query_runner

            query_runner.side_effect = live_query_runner
            response = retrieve_historical_precedents("current legal precedent", embeddings_client=fake_client)

            executed_sql = "\n".join(call.args[0] for call in query_runner.call_args_list)
            self.assertNotIn("search_knowledge_chunks", executed_sql)
            self.assertNotIn("current_knowledge_chunks", executed_sql)

        from tools.phase_06_search.historical_retrieval import run_historical_hybrid_search

        direct_rows, _ = run_historical_hybrid_search(
            query_text="current legal precedent",
            query_embedding=vector,
            embedding_model_id=model["id"],
            result_limit=response["result_limit_used"],
            filters=normalize_filters(),
        )
        self.assertEqual(response["retrieval_mode_used"], "hybrid")
        self.assertEqual(
            [row["search_unit_id"] for row in response["results"]],
            [row["search_unit_id"] for row in direct_rows],
        )
        self.assertEqual(response["strategy_code"], "historical_rrf_balanced")
        self.assertEqual(response["configuration_code"], "historical_rrf_balanced_d20")


if __name__ == "__main__":
    unittest.main()
