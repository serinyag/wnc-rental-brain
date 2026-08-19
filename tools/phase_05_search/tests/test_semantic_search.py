from __future__ import annotations

import unittest

from tools.phase_05_search.semantic_common import (
    ChunkEmbeddingCandidate,
    EmbeddingGenerationError,
    EmbeddingModelConfig,
    OpenAIEmbeddingsClient,
    SearchFixture,
    assess_search_results,
    build_embedding_input,
    compute_config_fingerprint,
    compute_content_hash,
    embed_candidate_batch,
    embed_query_text,
    plan_pending_chunk_embeddings,
    validate_embedding_dimensions,
)


class FakeEmbeddingClient:
    def __init__(self, rows: list[list[float]] | Exception) -> None:
        self.rows_or_error = rows

    def embed_texts(self, texts, config):  # noqa: ANN001
        if isinstance(self.rows_or_error, Exception):
            raise self.rows_or_error
        return self.rows_or_error


class SemanticSearchHelpersTests(unittest.TestCase):
    def test_embedding_input_prefers_heading_path_and_preserves_template_labels(self) -> None:
        rendered = build_embedding_input(
            "WNC Rental Email Template Library",
            "External Supplier Information Request",
            "Ignored fallback section",
            "What details should we request?",
            "INTERNAL GUIDANCE\n...\n\nCLIENT-FACING TEMPLATE\n...",
        )
        self.assertIn("Document: WNC Rental Email Template Library", rendered)
        self.assertIn("Section: External Supplier Information Request", rendered)
        self.assertIn("Question: What details should we request?", rendered)
        self.assertIn("INTERNAL GUIDANCE", rendered)
        self.assertIn("CLIENT-FACING TEMPLATE", rendered)
        self.assertNotIn("Ignored fallback section", rendered)

    def test_content_hash_is_deterministic_and_changes_with_input(self) -> None:
        first = compute_content_hash("semantic baseline")
        second = compute_content_hash("semantic baseline")
        third = compute_content_hash("semantic baseline updated")
        self.assertEqual(first, second)
        self.assertNotEqual(first, third)

    def test_config_fingerprint_is_stable_for_identical_model_config(self) -> None:
        left = EmbeddingModelConfig()
        right = EmbeddingModelConfig()
        changed = EmbeddingModelConfig(embedding_dimensions=3072)
        self.assertEqual(compute_config_fingerprint(left), compute_config_fingerprint(right))
        self.assertNotEqual(compute_config_fingerprint(left), compute_config_fingerprint(changed))

    def test_pending_plan_skips_unchanged_existing_embeddings(self) -> None:
        candidates = [
            ChunkEmbeddingCandidate(1, "SERV-003", 1, "A", "hash_a"),
            ChunkEmbeddingCandidate(2, "TPL-006", 1, "B", "hash_b"),
        ]
        pending, skipped = plan_pending_chunk_embeddings(candidates, {(1, "hash_a")})
        self.assertEqual([candidate.chunk_id for candidate in pending], [2])
        self.assertEqual([candidate.chunk_id for candidate in skipped], [1])

    def test_dimension_validation_rejects_mismatch(self) -> None:
        validate_embedding_dimensions([0.1, 0.2, 0.3], 3)
        with self.assertRaisesRegex(ValueError, "do not match expected dimensions"):
            validate_embedding_dimensions([0.1, 0.2], 3)

    def test_embed_query_text_uses_same_dimension_validation(self) -> None:
        config = EmbeddingModelConfig(embedding_dimensions=3)
        vector = embed_query_text(FakeEmbeddingClient([[0.1, 0.2, 0.3]]), "external caterer", config)
        self.assertEqual(vector, [0.1, 0.2, 0.3])

    def test_openai_client_trims_surrounding_api_key_whitespace(self) -> None:
        client = OpenAIEmbeddingsClient(api_key="  sk-test-key\n", timeout_seconds=1)
        self.assertEqual(client.api_key, "sk-test-key")
        self.assertIsNotNone(client.ssl_context)

    def test_openai_client_discards_accidentally_appended_shell_text(self) -> None:
        client = OpenAIEmbeddingsClient(api_key="sk-test-key\npython3 -m tools.phase_05_search.evaluate_semantic", timeout_seconds=1)
        self.assertEqual(client.api_key, "sk-test-key")

    def test_embed_candidate_batch_wraps_failures_with_context(self) -> None:
        config = EmbeddingModelConfig(embedding_dimensions=3)
        candidates = [
            ChunkEmbeddingCandidate(1, "SERV-003", 1, "external caterer", "hash_a"),
            ChunkEmbeddingCandidate(2, "TPL-006", 2, "remaining balance", "hash_b"),
        ]
        with self.assertRaises(EmbeddingGenerationError) as ctx:
            embed_candidate_batch(FakeEmbeddingClient(RuntimeError("boom")), candidates, config)
        self.assertIn("SERV-003#1", str(ctx.exception))
        self.assertIn("TPL-006#2", str(ctx.exception))
        self.assertIn(config.model_code, str(ctx.exception))

    def test_embed_candidate_batch_rejects_dimension_mismatch(self) -> None:
        config = EmbeddingModelConfig(embedding_dimensions=3)
        candidates = [ChunkEmbeddingCandidate(1, "SERV-003", 1, "external caterer", "hash_a")]
        with self.assertRaisesRegex(ValueError, "do not match expected dimensions"):
            embed_candidate_batch(FakeEmbeddingClient([[0.1, 0.2]]), candidates, config)

    def test_assess_search_results_marks_expected_top_result_strong(self) -> None:
        fixture = SearchFixture(query="projector", expected_codes=("OPS-002", "SERV-001"))
        rows = [{"document_code": "OPS-002"}, {"document_code": "SERV-001"}]
        assessment = assess_search_results(fixture, rows)
        self.assertEqual(assessment.status, "strong")

    def test_assess_search_results_marks_missing_expected_family_as_miss(self) -> None:
        fixture = SearchFixture(query="sparkling water", expected_codes=("SERV-003",))
        rows = [{"document_code": "CF-007"}, {"document_code": "GOV-002"}]
        assessment = assess_search_results(fixture, rows)
        self.assertEqual(assessment.status, "miss")


if __name__ == "__main__":
    unittest.main()
