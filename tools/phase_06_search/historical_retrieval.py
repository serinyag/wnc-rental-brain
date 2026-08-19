from __future__ import annotations

import argparse
import json
import subprocess
import time
from dataclasses import dataclass

from tools.phase_05_chunking.generate_pilot import run_supabase_query, sql_text
from tools.phase_05_search.hybrid_common import MAX_HYBRID_RESULT_LIMIT, bound_result_limit, normalize_query_text
from tools.phase_05_search.semantic_common import OpenAIEmbeddingsClient, embed_query_text, vector_sql_literal

from .retrieval_common import (
    ALLOWED_HISTORICAL_CONTAMINATION_LEVELS,
    ALLOWED_HISTORICAL_LESSON_KINDS,
    ALLOWED_HISTORICAL_PRECEDENT_AVAILABILITIES,
    ALLOWED_HISTORICAL_PRECEDENT_TYPES,
    ALLOWED_HISTORICAL_UNIT_TYPES,
    FROZEN_HISTORICAL_CANDIDATE_DEPTH,
    FROZEN_HISTORICAL_CONFIGURATION_CODE,
    FROZEN_HISTORICAL_LEXICAL_WEIGHT,
    FROZEN_HISTORICAL_RRF_K,
    FROZEN_HISTORICAL_SEMANTIC_WEIGHT,
    FROZEN_HISTORICAL_STRATEGY_CODE,
    build_historical_config_from_registry,
    fetch_historical_embedding_coverage,
    is_historical_embedding_state_complete,
    load_active_historical_retrieval_model,
)


SUPPORTED_RETRIEVAL_MODE_REQUESTED = "hybrid"
SUPPORTED_RETRIEVAL_MODE_HYBRID = "hybrid"
SUPPORTED_RETRIEVAL_MODE_FTS_FALLBACK = "fts_fallback"


@dataclass(frozen=True)
class HistoricalRetrievalFilters:
    case_code: str | None = None
    unit_type: str | None = None
    precedent_availability: str | None = None
    precedent_type: str | None = None
    lesson_kind: str | None = None
    historical_value_only: bool | None = None
    contamination_risk_level: str | None = None


class HistoricalRetrievalError(RuntimeError):
    def __init__(self, *, error_category: str, safe_message: str) -> None:
        self.error_category = error_category
        self.safe_message = safe_message
        super().__init__(safe_message)

    def to_dict(self) -> dict[str, str]:
        return {
            "error_category": self.error_category,
            "message": self.safe_message,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Phase 6 historical retrieval integration contract.")
    parser.add_argument("query", help="Natural-language historical precedent query.")
    parser.add_argument("--limit", type=int, default=5, help=f"Maximum number of results to return (1-{MAX_HYBRID_RESULT_LIMIT}).")
    parser.add_argument("--case-code", type=str, help="Optional historical case-code filter.")
    parser.add_argument("--unit-type", type=str, help="Optional unit-type filter.")
    parser.add_argument("--precedent-availability", type=str, help="Optional precedent-availability filter.")
    parser.add_argument("--precedent-type", type=str, help="Optional precedent-type filter.")
    parser.add_argument("--lesson-kind", type=str, help="Optional lesson-kind filter.")
    parser.add_argument(
        "--historical-value-only",
        choices=("true", "false"),
        help="Optional historical-value-only filter.",
    )
    parser.add_argument("--contamination-risk-level", type=str, help="Optional contamination-risk filter.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser.parse_args()


def normalize_optional_text_filter(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def normalize_bool_filter(value: bool | str | None) -> bool | None:
    if value is None or isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized == "":
        return None
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise HistoricalRetrievalError(
        error_category="invalid_filter",
        safe_message="historical_value_only must be true or false when supplied.",
    )


def normalize_filters(
    *,
    case_code: str | None = None,
    unit_type: str | None = None,
    precedent_availability: str | None = None,
    precedent_type: str | None = None,
    lesson_kind: str | None = None,
    historical_value_only: bool | str | None = None,
    contamination_risk_level: str | None = None,
) -> HistoricalRetrievalFilters:
    normalized_case_code = normalize_optional_text_filter(case_code)
    if normalized_case_code is not None:
        normalized_case_code = normalized_case_code.upper()

    normalized_unit_type = normalize_optional_text_filter(unit_type)
    if normalized_unit_type is not None:
        normalized_unit_type = normalized_unit_type.lower()
        if normalized_unit_type not in ALLOWED_HISTORICAL_UNIT_TYPES:
            raise HistoricalRetrievalError(
                error_category="invalid_filter",
                safe_message=f"Unsupported historical unit_type filter: {normalized_unit_type}.",
            )

    normalized_precedent_availability = normalize_optional_text_filter(precedent_availability)
    if normalized_precedent_availability is not None:
        normalized_precedent_availability = normalized_precedent_availability.lower()
        if normalized_precedent_availability not in ALLOWED_HISTORICAL_PRECEDENT_AVAILABILITIES:
            raise HistoricalRetrievalError(
                error_category="invalid_filter",
                safe_message=f"Unsupported historical precedent_availability filter: {normalized_precedent_availability}.",
            )

    normalized_precedent_type = normalize_optional_text_filter(precedent_type)
    if normalized_precedent_type is not None:
        normalized_precedent_type = normalized_precedent_type.lower()
        if normalized_precedent_type not in ALLOWED_HISTORICAL_PRECEDENT_TYPES:
            raise HistoricalRetrievalError(
                error_category="invalid_filter",
                safe_message=f"Unsupported historical precedent_type filter: {normalized_precedent_type}.",
            )

    normalized_lesson_kind = normalize_optional_text_filter(lesson_kind)
    if normalized_lesson_kind is not None:
        normalized_lesson_kind = normalized_lesson_kind.lower()
        if normalized_lesson_kind not in ALLOWED_HISTORICAL_LESSON_KINDS:
            raise HistoricalRetrievalError(
                error_category="invalid_filter",
                safe_message=f"Unsupported historical lesson_kind filter: {normalized_lesson_kind}.",
            )

    normalized_contamination_risk_level = normalize_optional_text_filter(contamination_risk_level)
    if normalized_contamination_risk_level is not None:
        normalized_contamination_risk_level = normalized_contamination_risk_level.lower()
        if normalized_contamination_risk_level not in ALLOWED_HISTORICAL_CONTAMINATION_LEVELS:
            raise HistoricalRetrievalError(
                error_category="invalid_filter",
                safe_message=f"Unsupported historical contamination_risk_level filter: {normalized_contamination_risk_level}.",
            )

    return HistoricalRetrievalFilters(
        case_code=normalized_case_code,
        unit_type=normalized_unit_type,
        precedent_availability=normalized_precedent_availability,
        precedent_type=normalized_precedent_type,
        lesson_kind=normalized_lesson_kind,
        historical_value_only=normalize_bool_filter(historical_value_only),
        contamination_risk_level=normalized_contamination_risk_level,
    )


def serialize_embedding_model(row: dict | None) -> dict[str, object] | None:
    if row is None:
        return None
    return {
        "embedding_model_id": row["id"],
        "provider_code": row["provider_code"],
        "model_code": row["model_code"],
        "model_version": row["model_version"],
        "embedding_dimensions": row["embedding_dimensions"],
        "config_fingerprint": row.get("config_fingerprint"),
    }


def serialize_embedding_state(coverage: dict | None) -> dict[str, object] | None:
    if coverage is None:
        return None
    return {
        "embedding_model_id": coverage["embedding_model_id"],
        "eligible_unit_count": coverage["eligible_unit_count"],
        "current_embedding_count": coverage["current_embedding_count"],
        "missing_unit_count": coverage["missing_unit_count"],
        "stale_unit_count": coverage["stale_unit_count"],
        "is_complete": is_historical_embedding_state_complete(coverage),
    }


def normalize_fts_result_row(row: dict, index: int) -> dict[str, object]:
    return {
        "search_unit_id": row["search_unit_id"],
        "source_layer_role": row["source_layer_role"],
        "source_key": row["source_key"],
        "unit_type": row["unit_type"],
        "search_text": row["search_text"],
        "historical_case_id": row["historical_case_id"],
        "historical_case_version_id": row["historical_case_version_id"],
        "case_code": row["case_code"],
        "case_title": row["case_title"],
        "precedent_type": row["precedent_type"],
        "precedent_availability": row["precedent_availability"],
        "case_evidence_strength": row["case_evidence_strength"],
        "unit_evidence_strength": row["unit_evidence_strength"],
        "actor_type": row["actor_type"],
        "lesson_kind": row["lesson_kind"],
        "historical_value_only": row["historical_value_only"],
        "contamination_risk_level": row["contamination_risk_level"],
        "current_authority_disposition": row["current_authority_disposition"],
        "case_contains_historical_value_only_content": row["case_contains_historical_value_only_content"],
        "effective_confidentiality_level_id": row["effective_confidentiality_level_id"],
        "effective_confidentiality_level_code": row["effective_confidentiality_level_code"],
        "case_personal_information_status": row["case_personal_information_status"],
        "source_object_personal_information_status": row["source_object_personal_information_status"],
        "primary_historical_case_version_source_object_id": row["primary_historical_case_version_source_object_id"],
        "primary_source_object_id": row["primary_source_object_id"],
        "primary_source_locator": row["primary_source_locator"],
        "source_link_count": row["source_link_count"],
        "responsibility_id": row["responsibility_id"],
        "decision_id": row["decision_id"],
        "lesson_id": row["lesson_id"],
        "embedding_model_id": None,
        "provider_code": None,
        "model_code": None,
        "model_version": None,
        "strategy_code": None,
        "came_from_fts": True,
        "came_from_semantic": False,
        "fts_rank": index,
        "semantic_rank": None,
        "best_component_rank": index,
        "lexical_score": row["lexical_score"],
        "semantic_similarity_score": None,
        "semantic_cosine_distance": None,
        "rrf_k": None,
        "lexical_weight": None,
        "semantic_weight": None,
        "rrf_fts_score": None,
        "rrf_semantic_score": None,
        "hybrid_score": None,
    }


def run_historical_fts_search(
    *,
    query_text: str,
    result_limit: int,
    filters: HistoricalRetrievalFilters,
) -> tuple[list[dict], float]:
    sql = f"""
select
  search_unit_id,
  source_layer_role,
  source_key,
  unit_type,
  search_text,
  lexical_score,
  historical_case_id,
  historical_case_version_id,
  case_code,
  case_title,
  precedent_type,
  precedent_availability,
  case_evidence_strength,
  unit_evidence_strength,
  actor_type,
  lesson_kind,
  historical_value_only,
  contamination_risk_level,
  current_authority_disposition,
  case_contains_historical_value_only_content,
  effective_confidentiality_level_id,
  effective_confidentiality_level_code,
  case_personal_information_status,
  source_object_personal_information_status,
  primary_historical_case_version_source_object_id,
  primary_source_object_id,
  primary_source_locator,
  source_link_count,
  responsibility_id,
  decision_id,
  lesson_id
from private.search_historical_case_units(
  {sql_text(query_text)},
  {result_limit},
  {sql_text(filters.case_code)},
  {sql_text(filters.unit_type)},
  {sql_text(filters.precedent_availability)},
  {sql_text(filters.precedent_type)},
  {sql_text(filters.lesson_kind)},
  {'null' if filters.historical_value_only is None else ('true' if filters.historical_value_only else 'false')},
  {sql_text(filters.contamination_risk_level)}
);
""".strip()
    started = time.perf_counter()
    payload = run_supabase_query(sql, expect_json=True)
    elapsed_ms = (time.perf_counter() - started) * 1000
    rows = [normalize_fts_result_row(row, index) for index, row in enumerate(payload["rows"], start=1)]
    return rows, elapsed_ms


def run_historical_hybrid_search(
    *,
    query_text: str,
    query_embedding: list[float],
    embedding_model_id: int,
    result_limit: int,
    filters: HistoricalRetrievalFilters,
) -> tuple[list[dict], float]:
    sql = f"""
select
  search_unit_id,
  source_layer_role,
  source_key,
  unit_type,
  search_text,
  historical_case_id,
  historical_case_version_id,
  case_code,
  case_title,
  precedent_type,
  precedent_availability,
  case_evidence_strength,
  unit_evidence_strength,
  actor_type,
  lesson_kind,
  historical_value_only,
  contamination_risk_level,
  current_authority_disposition,
  case_contains_historical_value_only_content,
  effective_confidentiality_level_id,
  effective_confidentiality_level_code,
  case_personal_information_status,
  source_object_personal_information_status,
  primary_historical_case_version_source_object_id,
  primary_source_object_id,
  primary_source_locator,
  source_link_count,
  responsibility_id,
  decision_id,
  lesson_id,
  embedding_model_id,
  provider_code,
  model_code,
  model_version,
  strategy_code,
  came_from_fts,
  came_from_semantic,
  fts_rank,
  semantic_rank,
  best_component_rank,
  lexical_score,
  semantic_similarity_score,
  semantic_cosine_distance,
  rrf_k,
  lexical_weight,
  semantic_weight,
  rrf_fts_score,
  rrf_semantic_score,
  hybrid_score
from private.search_historical_case_units_hybrid(
  {sql_text(query_text)},
  {vector_sql_literal(query_embedding)}::extensions.vector,
  {result_limit},
  {FROZEN_HISTORICAL_CANDIDATE_DEPTH},
  {embedding_model_id},
  {sql_text(FROZEN_HISTORICAL_STRATEGY_CODE)},
  {sql_text(filters.case_code)},
  {sql_text(filters.unit_type)},
  {sql_text(filters.precedent_availability)},
  {sql_text(filters.precedent_type)},
  {sql_text(filters.lesson_kind)},
  {'null' if filters.historical_value_only is None else ('true' if filters.historical_value_only else 'false')},
  {sql_text(filters.contamination_risk_level)}
);
""".strip()
    started = time.perf_counter()
    payload = run_supabase_query(sql, expect_json=True)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return payload["rows"], elapsed_ms


def execute_fts_fallback(
    *,
    query_text: str,
    result_limit: int,
    filters: HistoricalRetrievalFilters,
    embedding_model_row: dict | None,
    coverage: dict | None,
    fallback_reason: str,
    total_started: float,
    embedding_elapsed_ms: float | None = None,
) -> dict[str, object]:
    try:
        rows, retrieval_elapsed_ms = run_historical_fts_search(
            query_text=query_text,
            result_limit=result_limit,
            filters=filters,
        )
    except subprocess.CalledProcessError as exc:
        raise HistoricalRetrievalError(
            error_category="fts_fallback_failed",
            safe_message="Historical lexical fallback failed before any safe retrieval result could be returned.",
        ) from exc

    return {
        "query_text": query_text,
        "retrieval_mode_requested": SUPPORTED_RETRIEVAL_MODE_REQUESTED,
        "retrieval_mode_used": SUPPORTED_RETRIEVAL_MODE_FTS_FALLBACK,
        "fallback_used": True,
        "fallback_reason": fallback_reason,
        "strategy_code": FROZEN_HISTORICAL_STRATEGY_CODE,
        "configuration_code": FROZEN_HISTORICAL_CONFIGURATION_CODE,
        "result_limit_requested": result_limit,
        "result_limit_used": result_limit,
        "candidate_pool_limit": None,
        "embedding_model": serialize_embedding_model(embedding_model_row),
        "historical_embedding_state": serialize_embedding_state(coverage),
        "result_count": len(rows),
        "timing_ms": {
            "embedding_generation": None if embedding_elapsed_ms is None else round(embedding_elapsed_ms, 2),
            "retrieval": round(retrieval_elapsed_ms, 2),
            "total": round((time.perf_counter() - total_started) * 1000, 2),
        },
        "results": rows,
    }


def retrieve_historical_precedents(
    query_text: str,
    *,
    result_limit: int | None = 5,
    case_code: str | None = None,
    unit_type: str | None = None,
    precedent_availability: str | None = None,
    precedent_type: str | None = None,
    lesson_kind: str | None = None,
    historical_value_only: bool | str | None = None,
    contamination_risk_level: str | None = None,
    embeddings_client: OpenAIEmbeddingsClient | None = None,
) -> dict[str, object]:
    total_started = time.perf_counter()
    normalized_query = normalize_query_text(query_text)
    if normalized_query is None:
        raise HistoricalRetrievalError(
            error_category="invalid_query",
            safe_message="Historical retrieval requires a non-empty query text.",
        )

    effective_limit = bound_result_limit(result_limit)
    filters = normalize_filters(
        case_code=case_code,
        unit_type=unit_type,
        precedent_availability=precedent_availability,
        precedent_type=precedent_type,
        lesson_kind=lesson_kind,
        historical_value_only=historical_value_only,
        contamination_risk_level=contamination_risk_level,
    )

    embedding_model_row: dict | None = None
    coverage: dict | None = None
    config = None
    try:
        embedding_model_row = load_active_historical_retrieval_model()
        coverage = fetch_historical_embedding_coverage(embedding_model_row["id"])
        config = build_historical_config_from_registry(embedding_model_row)
    except subprocess.CalledProcessError as exc:
        raise HistoricalRetrievalError(
            error_category="database_unavailable",
            safe_message="Historical retrieval could not reach the local database.",
        ) from exc
    except SystemExit:
        return execute_fts_fallback(
            query_text=normalized_query,
            result_limit=effective_limit,
            filters=filters,
            embedding_model_row=embedding_model_row,
            coverage=coverage,
            fallback_reason="embedding_model_resolution_failed",
            total_started=total_started,
        )

    if not is_historical_embedding_state_complete(coverage):
        return execute_fts_fallback(
            query_text=normalized_query,
            result_limit=effective_limit,
            filters=filters,
            embedding_model_row=embedding_model_row,
            coverage=coverage,
            fallback_reason="historical_embedding_corpus_incomplete",
            total_started=total_started,
        )

    try:
        client = embeddings_client or OpenAIEmbeddingsClient()
        embedding_started = time.perf_counter()
        query_embedding = embed_query_text(client, normalized_query, config)
        embedding_elapsed_ms = (time.perf_counter() - embedding_started) * 1000
    except SystemExit:
        return execute_fts_fallback(
            query_text=normalized_query,
            result_limit=effective_limit,
            filters=filters,
            embedding_model_row=embedding_model_row,
            coverage=coverage,
            fallback_reason="embedding_configuration_missing",
            total_started=total_started,
        )
    except Exception:
        return execute_fts_fallback(
            query_text=normalized_query,
            result_limit=effective_limit,
            filters=filters,
            embedding_model_row=embedding_model_row,
            coverage=coverage,
            fallback_reason="query_embedding_failed",
            total_started=total_started,
        )

    try:
        rows, retrieval_elapsed_ms = run_historical_hybrid_search(
            query_text=normalized_query,
            query_embedding=query_embedding,
            embedding_model_id=embedding_model_row["id"],
            result_limit=effective_limit,
            filters=filters,
        )
    except subprocess.CalledProcessError as exc:
        raise HistoricalRetrievalError(
            error_category="hybrid_function_failed",
            safe_message="Historical hybrid retrieval failed before any safe result set could be returned.",
        ) from exc

    return {
        "query_text": normalized_query,
        "retrieval_mode_requested": SUPPORTED_RETRIEVAL_MODE_REQUESTED,
        "retrieval_mode_used": SUPPORTED_RETRIEVAL_MODE_HYBRID,
        "fallback_used": False,
        "fallback_reason": None,
        "strategy_code": FROZEN_HISTORICAL_STRATEGY_CODE,
        "configuration_code": FROZEN_HISTORICAL_CONFIGURATION_CODE,
        "result_limit_requested": effective_limit,
        "result_limit_used": effective_limit,
        "candidate_pool_limit": FROZEN_HISTORICAL_CANDIDATE_DEPTH,
        "embedding_model": serialize_embedding_model(embedding_model_row),
        "historical_embedding_state": serialize_embedding_state(coverage),
        "result_count": len(rows),
        "timing_ms": {
            "embedding_generation": round(embedding_elapsed_ms, 2),
            "retrieval": round(retrieval_elapsed_ms, 2),
            "total": round((time.perf_counter() - total_started) * 1000, 2),
        },
        "results": rows,
    }


def main() -> int:
    args = parse_args()
    try:
        response = retrieve_historical_precedents(
            args.query,
            result_limit=args.limit,
            case_code=args.case_code,
            unit_type=args.unit_type,
            precedent_availability=args.precedent_availability,
            precedent_type=args.precedent_type,
            lesson_kind=args.lesson_kind,
            historical_value_only=args.historical_value_only,
            contamination_risk_level=args.contamination_risk_level,
        )
    except HistoricalRetrievalError as exc:
        if args.json:
            print(json.dumps({"query_text": args.query, "error": exc.to_dict()}, indent=2))
        else:
            print(f"{exc.error_category}: {exc.safe_message}")
        return 1

    if args.json:
        print(json.dumps(response, indent=2))
        return 0

    print(f"query_text={response['query_text']}")
    print(f"retrieval_mode_requested={response['retrieval_mode_requested']}")
    print(f"retrieval_mode_used={response['retrieval_mode_used']}")
    print(f"fallback_used={response['fallback_used']}")
    print(f"fallback_reason={response['fallback_reason']}")
    print(f"strategy_code={response['strategy_code']}")
    print(f"configuration_code={response['configuration_code']}")
    print(f"result_count={response['result_count']}")
    print(f"timing_ms={response['timing_ms']}")
    for index, row in enumerate(response["results"], start=1):
        print(
            f"{index}. {row['case_code']} / {row['unit_type']} "
            f"availability={row['precedent_availability']} "
            f"hybrid_score={row['hybrid_score']} lexical_score={row['lexical_score']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
