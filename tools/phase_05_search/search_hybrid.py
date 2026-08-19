from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from tools.phase_05_chunking.generate_pilot import run_supabase_query, sql_text

from .evaluate_semantic import build_config_from_registry, load_active_retrieval_model
from .hybrid_common import (
    DEFAULT_HYBRID_CANDIDATE_POOL_LIMIT,
    APPROVED_RRF_K,
    bound_candidate_pool_limit,
    bound_result_limit,
    normalize_query_text,
)
from .semantic_common import OpenAIEmbeddingsClient, embed_query_text, vector_sql_literal


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Phase 5 production hybrid retrieval surface.")
    parser.add_argument("query", help="Query text to search.")
    parser.add_argument("--limit", type=int, default=5, help="Final result count to return.")
    parser.add_argument(
        "--candidate-pool-limit",
        type=int,
        default=DEFAULT_HYBRID_CANDIDATE_POOL_LIMIT,
        help="Per-substrate candidate depth used before RRF fusion.",
    )
    parser.add_argument("--document-code", type=str, help="Optional document-code filter.")
    parser.add_argument("--category-code", type=str, help="Optional category-code filter.")
    parser.add_argument("--rental-type-code", type=str, help="Optional rental-type filter.")
    parser.add_argument(
        "--fts-only",
        action="store_true",
        help="Skip query embedding generation and exercise the graceful FTS-only hybrid path.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser.parse_args()


def run_hybrid_search(
    *,
    query_text: str,
    result_limit: int,
    candidate_pool_limit: int,
    query_embedding: list[float] | None,
    embedding_model_id: int | None,
    document_code: str | None = None,
    category_code: str | None = None,
    rental_type_code: str | None = None,
) -> tuple[list[dict], float]:
    embedding_sql = "null"
    embedding_model_id_sql = "null"
    if query_embedding is not None:
        embedding_sql = f"{vector_sql_literal(query_embedding)}::extensions.vector"
        embedding_model_id_sql = str(embedding_model_id)

    sql = f"""
select
  chunk_id,
  document_code,
  document_title,
  document_version_id,
  document_version_number,
  chunk_set_id,
  chunk_ordinal,
  section_heading,
  heading_path,
  question_label,
  body_text,
  content_hash,
  primary_chunk_source_id,
  primary_document_version_source_object_id,
  primary_source_locator,
  primary_category_code,
  authority_classification,
  rental_type_codes,
  embedding_model_id,
  provider_code,
  model_code,
  model_version,
  came_from_fts,
  came_from_semantic,
  fts_rank,
  semantic_rank,
  fts_relevance_score,
  semantic_similarity_score,
  semantic_cosine_distance,
  rrf_k,
  rrf_fts_score,
  rrf_semantic_score,
  rrf_base_score,
  policy_modifier,
  final_score
from private.search_knowledge_chunks_hybrid(
  {sql_text(query_text)},
  {embedding_sql},
  {result_limit},
  {candidate_pool_limit},
  {embedding_model_id_sql},
  {sql_text(document_code)},
  {sql_text(category_code)},
  {sql_text(rental_type_code)}
);
""".strip()
    started = time.perf_counter()
    payload = run_supabase_query(sql, expect_json=True)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return payload["rows"], elapsed_ms


def generate_query_embedding(query_text: str, client: OpenAIEmbeddingsClient, config) -> list[float]:
    normalized_query = normalize_query_text(query_text)
    if normalized_query is None:
        raise ValueError("query text must not be empty")
    return embed_query_text(client, normalized_query, config)


def main() -> int:
    args = parse_args()
    normalized_query = normalize_query_text(args.query)
    result_limit = bound_result_limit(args.limit)
    candidate_pool_limit = bound_candidate_pool_limit(args.candidate_pool_limit, result_limit)

    if normalized_query is None:
        if args.json:
            print(json.dumps({"query": args.query, "results": [], "message": "empty query"}, indent=2))
        else:
            print("Empty query: no results returned.")
        return 0

    model_row = None
    query_embedding = None
    embedding_elapsed_ms = 0.0
    if not args.fts_only:
        model_row = load_active_retrieval_model()
        config = build_config_from_registry(model_row)
        if config.provider_code != "openai":
            raise SystemExit("Only provider_code='openai' is currently supported by the hybrid search tooling.")
        client = OpenAIEmbeddingsClient()
        started = time.perf_counter()
        query_embedding = generate_query_embedding(normalized_query, client, config)
        embedding_elapsed_ms = (time.perf_counter() - started) * 1000

    rows, retrieval_elapsed_ms = run_hybrid_search(
        query_text=normalized_query,
        result_limit=result_limit,
        candidate_pool_limit=candidate_pool_limit,
        query_embedding=query_embedding,
        embedding_model_id=None if model_row is None else model_row["id"],
        document_code=args.document_code,
        category_code=args.category_code,
        rental_type_code=args.rental_type_code,
    )

    if args.json:
        print(
            json.dumps(
                {
                    "query": normalized_query,
                    "rrf_k": APPROVED_RRF_K,
                    "result_limit": result_limit,
                    "candidate_pool_limit": candidate_pool_limit,
                    "embedding_generation_ms": round(embedding_elapsed_ms, 2),
                    "hybrid_retrieval_ms": round(retrieval_elapsed_ms, 2),
                    "results": rows,
                },
                indent=2,
            )
        )
        return 0

    print(f"query={normalized_query}")
    print(f"rrf_k={APPROVED_RRF_K}")
    print(f"result_limit={result_limit}")
    print(f"candidate_pool_limit={candidate_pool_limit}")
    print(f"embedding_generation_ms={embedding_elapsed_ms:.2f}")
    print(f"hybrid_retrieval_ms={retrieval_elapsed_ms:.2f}")
    print(f"results={len(rows)}")
    for index, row in enumerate(rows, start=1):
        section = row["section_heading"] or "(no section heading)"
        print(
            f"{index}. {row['document_code']} #{row['chunk_ordinal']} "
            f"section={section!r} final={row['final_score']:.6f} "
            f"rrf={row['rrf_base_score']:.6f} modifier={row['policy_modifier']:.6f} "
            f"fts_rank={row['fts_rank']} semantic_rank={row['semantic_rank']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
