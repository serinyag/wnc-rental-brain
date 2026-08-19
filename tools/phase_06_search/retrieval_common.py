from __future__ import annotations

from tools.phase_05_chunking.generate_pilot import run_supabase_query
from tools.phase_05_search.semantic_common import EmbeddingModelConfig


FROZEN_HISTORICAL_STRATEGY_CODE = "historical_rrf_balanced"
FROZEN_HISTORICAL_CONFIGURATION_CODE = "historical_rrf_balanced_d20"
FROZEN_HISTORICAL_RRF_K = 20
FROZEN_HISTORICAL_LEXICAL_WEIGHT = 1.0
FROZEN_HISTORICAL_SEMANTIC_WEIGHT = 1.0
FROZEN_HISTORICAL_CANDIDATE_DEPTH = 20

ALLOWED_HISTORICAL_UNIT_TYPES = frozenset(
    {
        "case_narrative",
        "responsibility",
        "decision",
        "lesson",
    }
)
ALLOWED_HISTORICAL_PRECEDENT_AVAILABILITIES = frozenset({"active", "limited"})
ALLOWED_HISTORICAL_PRECEDENT_TYPES = frozenset(
    {
        "full_case",
        "limited_precedent",
        "cautionary_precedent",
    }
)
ALLOWED_HISTORICAL_LESSON_KINDS = frozenset(
    {
        "source_explicit",
        "curated_lesson",
        "analyst_inference",
        "caution_warning",
    }
)
ALLOWED_HISTORICAL_CONTAMINATION_LEVELS = frozenset({"low", "medium", "high"})


def load_active_historical_retrieval_model(query_runner=run_supabase_query) -> dict:
    sql = """
select
  id,
  provider_code,
  model_code,
  model_version,
  embedding_dimensions,
  config_fingerprint,
  configuration_json
from private.historical_case_embedding_models
where is_retrieval_approved
  and is_active
order by id;
""".strip()
    payload = query_runner(sql, expect_json=True)
    rows = payload["rows"]
    if not rows:
        raise SystemExit("No active retrieval-approved historical embedding model is registered. Run embedding generation first.")
    if len(rows) > 1:
        raise SystemExit("Multiple active retrieval-approved historical embedding models are registered. Narrow the registry before retrieval.")
    return rows[0]


def build_historical_config_from_registry(row: dict) -> EmbeddingModelConfig:
    cfg = row["configuration_json"] or {}
    return EmbeddingModelConfig(
        provider_code=row["provider_code"],
        model_code=row["model_code"],
        model_version=row["model_version"],
        embedding_dimensions=row["embedding_dimensions"],
        distance_metric=cfg.get("distance_metric", "cosine"),
        input_contract_code=cfg.get("input_contract_code", "phase_06_historical_search_unit_embedding_input_v1"),
        encoding_format=cfg.get("encoding_format", "float"),
        api_base_url=cfg.get("api_base_url", "https://api.openai.com/v1"),
        is_retrieval_approved=True,
        is_active=True,
    )


def fetch_historical_embedding_coverage(model_id: int, query_runner=run_supabase_query) -> dict:
    sql = f"""
select
  embedding_model_id,
  provider_code,
  model_code,
  model_version,
  embedding_dimensions,
  config_fingerprint,
  eligible_unit_count,
  current_embedding_count,
  missing_unit_count,
  stale_unit_count
from private.current_historical_case_embedding_coverage
where embedding_model_id = {model_id};
""".strip()
    payload = query_runner(sql, expect_json=True)
    rows = payload["rows"]
    if not rows:
        raise SystemExit("Historical embedding coverage is unavailable for the active model.")
    return rows[0]


def is_historical_embedding_state_complete(coverage: dict) -> bool:
    return (
        coverage["eligible_unit_count"] == coverage["current_embedding_count"]
        and coverage["missing_unit_count"] == 0
        and coverage["stale_unit_count"] == 0
    )
