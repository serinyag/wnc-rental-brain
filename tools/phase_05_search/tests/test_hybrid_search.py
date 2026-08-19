from __future__ import annotations

import unittest

from tools.phase_05_search.hybrid_common import (
    APPROVED_RRF_K,
    HybridCandidate,
    bound_candidate_pool_limit,
    bound_result_limit,
    compute_rrf_score,
    merge_candidate_rows,
    merge_hybrid_candidates,
    normalize_query_text,
    policy_modifier_for_category,
)
from tools.phase_05_search.search_hybrid import generate_query_embedding
from tools.phase_05_search.semantic_common import EmbeddingModelConfig


class FakeEmbeddingClient:
    def __init__(self, rows: list[list[float]]) -> None:
        self.rows = rows
        self.calls: list[tuple[list[str], EmbeddingModelConfig]] = []

    def embed_texts(self, texts, config):  # noqa: ANN001
        self.calls.append((list(texts), config))
        return self.rows


def make_candidate(
    *,
    chunk_id: int,
    document_code: str,
    chunk_ordinal: int,
    category_code: str,
    fts_rank: int | None = None,
    semantic_rank: int | None = None,
) -> HybridCandidate:
    return HybridCandidate(
        chunk_id=chunk_id,
        document_code=document_code,
        document_title=document_code,
        document_version_id=1,
        document_version_number=1,
        chunk_set_id=1,
        chunk_ordinal=chunk_ordinal,
        section_heading="Section",
        heading_path="Section",
        question_label=None,
        body_text="Body",
        content_hash=f"hash-{chunk_id}",
        primary_chunk_source_id=1,
        primary_document_version_source_object_id=1,
        primary_source_locator="fixture",
        primary_category_code=category_code,
        authority_classification="authoritative",
        rental_type_codes=("studio_space",),
        fts_rank=fts_rank,
        semantic_rank=semantic_rank,
        fts_relevance_score=0.5 if fts_rank is not None else None,
        semantic_similarity_score=0.5 if semantic_rank is not None else None,
        semantic_cosine_distance=0.5 if semantic_rank is not None else None,
    )


class HybridSearchHelpersTests(unittest.TestCase):
    def test_normalize_query_text_handles_empty_and_whitespace(self) -> None:
        self.assertIsNone(normalize_query_text(None))
        self.assertIsNone(normalize_query_text("   "))
        self.assertEqual(normalize_query_text(" payment   within   14 days "), "payment within 14 days")

    def test_result_limit_and_candidate_pool_bounds_are_deterministic(self) -> None:
        self.assertEqual(bound_result_limit(None), 10)
        self.assertEqual(bound_result_limit(0), 1)
        self.assertEqual(bound_result_limit(500), 50)
        self.assertEqual(bound_candidate_pool_limit(None, 5), 10)
        self.assertEqual(bound_candidate_pool_limit(3, 5), 5)
        self.assertEqual(bound_candidate_pool_limit(80, 5), 50)

    def test_compute_rrf_score_uses_approved_constant(self) -> None:
        self.assertAlmostEqual(compute_rrf_score(1), 1 / (APPROVED_RRF_K + 1))
        self.assertEqual(compute_rrf_score(None), 0.0)
        self.assertEqual(compute_rrf_score(0), 0.0)

    def test_policy_modifier_applies_approved_category_weights(self) -> None:
        self.assertEqual(policy_modifier_for_category("operational_procedure"), 0.011)
        self.assertEqual(policy_modifier_for_category("governance_canonical"), -0.010)
        self.assertEqual(policy_modifier_for_category("unknown_category"), 0.0)

    def test_merge_candidate_rows_combines_duplicate_chunk_ids(self) -> None:
        merged = merge_candidate_rows(
            [make_candidate(chunk_id=1, document_code="CF-003", chunk_ordinal=1, category_code="client_facing_controlled_document", fts_rank=1)],
            [make_candidate(chunk_id=1, document_code="CF-003", chunk_ordinal=1, category_code="client_facing_controlled_document", semantic_rank=2)],
        )
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].fts_rank, 1)
        self.assertEqual(merged[0].semantic_rank, 2)

    def test_merge_hybrid_candidates_keeps_fts_only_candidates(self) -> None:
        ranked = merge_hybrid_candidates(
            [make_candidate(chunk_id=1, document_code="CF-003", chunk_ordinal=1, category_code="client_facing_controlled_document", fts_rank=1)],
            result_limit=5,
        )
        self.assertEqual(len(ranked), 1)
        self.assertTrue(ranked[0].came_from_fts)
        self.assertFalse(ranked[0].came_from_semantic)

    def test_merge_hybrid_candidates_keeps_semantic_only_candidates(self) -> None:
        ranked = merge_hybrid_candidates(
            [make_candidate(chunk_id=2, document_code="TPL-008", chunk_ordinal=1, category_code="operational_procedure", semantic_rank=1)],
            result_limit=5,
        )
        self.assertEqual(len(ranked), 1)
        self.assertFalse(ranked[0].came_from_fts)
        self.assertTrue(ranked[0].came_from_semantic)

    def test_merge_hybrid_candidates_adds_both_rrf_contributions(self) -> None:
        merged = merge_candidate_rows(
            [make_candidate(chunk_id=1, document_code="CF-003", chunk_ordinal=1, category_code="client_facing_controlled_document", fts_rank=1)],
            [make_candidate(chunk_id=1, document_code="CF-003", chunk_ordinal=1, category_code="client_facing_controlled_document", semantic_rank=2)],
        )
        ranked = merge_hybrid_candidates(merged, result_limit=5)
        expected = (1 / 21) + (1 / 22) + 0.005
        self.assertAlmostEqual(ranked[0].final_score, expected)

    def test_merge_hybrid_candidates_uses_final_score_then_tie_breaker(self) -> None:
        ranked = merge_hybrid_candidates(
            [
                make_candidate(chunk_id=1, document_code="CF-003", chunk_ordinal=2, category_code="client_facing_controlled_document", fts_rank=1),
                make_candidate(chunk_id=2, document_code="CF-003", chunk_ordinal=1, category_code="client_facing_controlled_document", fts_rank=1),
            ],
            result_limit=5,
        )
        self.assertEqual([row.chunk_id for row in ranked], [2, 1])

    def test_merge_hybrid_candidates_prefers_operational_guidance_over_governance_when_relevance_is_close(self) -> None:
        ranked = merge_hybrid_candidates(
            [
                make_candidate(chunk_id=1, document_code="GOV-002", chunk_ordinal=1, category_code="governance_canonical", fts_rank=1, semantic_rank=1),
                make_candidate(chunk_id=2, document_code="CF-003", chunk_ordinal=1, category_code="client_facing_controlled_document", fts_rank=2, semantic_rank=2),
            ],
            result_limit=5,
        )
        self.assertEqual(ranked[0].document_code, "CF-003")

    def test_generate_query_embedding_normalizes_input_before_embedding(self) -> None:
        config = EmbeddingModelConfig(embedding_dimensions=3)
        client = FakeEmbeddingClient([[0.1, 0.2, 0.3]])
        vector = generate_query_embedding("  venue   walkthrough  ", client, config)
        self.assertEqual(vector, [0.1, 0.2, 0.3])
        self.assertEqual(client.calls[0][0], ["venue walkthrough"])

    def test_generate_query_embedding_rejects_empty_query(self) -> None:
        config = EmbeddingModelConfig(embedding_dimensions=3)
        client = FakeEmbeddingClient([[0.1, 0.2, 0.3]])
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            generate_query_embedding("   ", client, config)


if __name__ == "__main__":
    unittest.main()
