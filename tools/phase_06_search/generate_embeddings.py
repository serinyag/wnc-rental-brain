from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

import argparse

from tools.phase_05_chunking.generate_pilot import run_supabase_query, sql_text
from tools.phase_05_search.semantic_common import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_EMBEDDING_DIMENSIONS,
    DEFAULT_MODEL_CODE,
    DEFAULT_PROVIDER_CODE,
    EmbeddingGenerationError,
    EmbeddingModelConfig,
    OpenAIEmbeddingsClient,
    batch_items,
    compute_config_fingerprint,
    embed_query_text,  # imported only to keep config parity visible in this module
    validate_embedding_dimensions,
    vector_sql_literal,
)
from tools.runtime_environment import validate_bootstrap_environment


PHASE_06_INPUT_CONTRACT_CODE = "phase_06_historical_search_unit_embedding_input_v1"


@dataclass(frozen=True)
class HistoricalEmbeddingCandidate:
    search_unit_id: int
    source_key: str
    case_code: str
    unit_type: str
    embedding_input_text: str
    embedding_input_hash: str


@dataclass(frozen=True)
class RegisteredHistoricalEmbeddingModel:
    id: int
    provider_code: str
    model_code: str
    model_version: str | None
    embedding_dimensions: int
    config_fingerprint: str
    configuration_json: dict[str, object]
    is_retrieval_approved: bool
    is_active: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate deterministic semantic embeddings for current-search-eligible Phase 6 historical search units."
    )
    parser.add_argument("--provider", default=DEFAULT_PROVIDER_CODE, help="Embedding provider code to register.")
    parser.add_argument("--model", default=DEFAULT_MODEL_CODE, help="Embedding model code to register and call.")
    parser.add_argument("--model-version", default=None, help="Optional model version label for registry provenance.")
    parser.add_argument(
        "--dimensions",
        type=int,
        default=DEFAULT_EMBEDDING_DIMENSIONS,
        help="Expected embedding dimensions to request and validate.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Number of historical search-unit inputs to embed per remote API request.",
    )
    parser.add_argument(
        "--mark-non-approved",
        action="store_true",
        help="Register the model without setting is_retrieval_approved = true.",
    )
    return parser.parse_args()


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_current_candidates() -> list[HistoricalEmbeddingCandidate]:
    sql = """
select
  search_unit_id,
  source_key,
  case_code,
  unit_type,
  embedding_input_text,
  embedding_input_hash
from private.current_historical_case_embedding_inputs
order by case_code, unit_type, search_unit_id;
""".strip()
    payload = run_supabase_query(sql, expect_json=True)
    return [
        HistoricalEmbeddingCandidate(
            search_unit_id=row["search_unit_id"],
            source_key=row["source_key"],
            case_code=row["case_code"],
            unit_type=row["unit_type"],
            embedding_input_text=row["embedding_input_text"],
            embedding_input_hash=row["embedding_input_hash"],
        )
        for row in payload["rows"]
    ]


def ensure_registered_model(config: EmbeddingModelConfig) -> RegisteredHistoricalEmbeddingModel:
    configuration_json = {
        "provider_code": config.provider_code,
        "model_code": config.model_code,
        "model_version": config.model_version,
        "embedding_dimensions": config.embedding_dimensions,
        "distance_metric": config.distance_metric,
        "input_contract_code": config.input_contract_code,
        "encoding_format": config.encoding_format,
        "api_base_url": config.api_base_url,
    }
    fingerprint = compute_config_fingerprint(config)
    insert_sql = f"""
insert into private.historical_case_embedding_models (
  provider_code,
  model_code,
  model_version,
  embedding_dimensions,
  config_fingerprint,
  configuration_json,
  is_retrieval_approved,
  is_active
)
select
  {sql_text(config.provider_code)},
  {sql_text(config.model_code)},
  {sql_text(config.model_version)},
  {config.embedding_dimensions},
  {sql_text(fingerprint)},
  {sql_text(json.dumps(configuration_json, sort_keys=True, ensure_ascii=True))}::jsonb,
  {'true' if config.is_retrieval_approved else 'false'},
  {'true' if config.is_active else 'false'}
where not exists (
  select 1
  from private.historical_case_embedding_models
  where provider_code = {sql_text(config.provider_code)}
    and model_code = {sql_text(config.model_code)}
    and coalesce(model_version, '') = coalesce({sql_text(config.model_version)}, '')
    and config_fingerprint = {sql_text(fingerprint)}
);
""".strip()
    run_supabase_query(insert_sql, expect_json=False)

    update_sql = f"""
update private.historical_case_embedding_models
set configuration_json = {sql_text(json.dumps(configuration_json, sort_keys=True, ensure_ascii=True))}::jsonb,
    is_retrieval_approved = {'true' if config.is_retrieval_approved else 'false'},
    is_active = {'true' if config.is_active else 'false'}
where provider_code = {sql_text(config.provider_code)}
  and model_code = {sql_text(config.model_code)}
  and coalesce(model_version, '') = coalesce({sql_text(config.model_version)}, '')
  and config_fingerprint = {sql_text(fingerprint)};
""".strip()
    run_supabase_query(update_sql, expect_json=False)

    select_sql = f"""
select
  id,
  provider_code,
  model_code,
  model_version,
  embedding_dimensions,
  config_fingerprint,
  configuration_json,
  is_retrieval_approved,
  is_active
from private.historical_case_embedding_models
where provider_code = {sql_text(config.provider_code)}
  and model_code = {sql_text(config.model_code)}
  and coalesce(model_version, '') = coalesce({sql_text(config.model_version)}, '')
  and config_fingerprint = {sql_text(fingerprint)}
order by id
limit 1;
""".strip()
    payload = run_supabase_query(select_sql, expect_json=True)
    row = payload["rows"][0]
    return RegisteredHistoricalEmbeddingModel(
        id=row["id"],
        provider_code=row["provider_code"],
        model_code=row["model_code"],
        model_version=row["model_version"],
        embedding_dimensions=row["embedding_dimensions"],
        config_fingerprint=row["config_fingerprint"],
        configuration_json=row["configuration_json"],
        is_retrieval_approved=row["is_retrieval_approved"],
        is_active=row["is_active"],
    )


def load_existing_embedding_pairs(model_id: int) -> set[tuple[int, str]]:
    sql = f"""
select
  historical_case_search_unit_id,
  input_content_hash
from private.historical_case_embeddings
where embedding_model_id = {model_id};
""".strip()
    payload = run_supabase_query(sql, expect_json=True)
    return {
        (row["historical_case_search_unit_id"], row["input_content_hash"])
        for row in payload["rows"]
    }


def plan_pending_historical_embeddings(
    candidates: list[HistoricalEmbeddingCandidate],
    existing_pairs: set[tuple[int, str]],
) -> tuple[list[HistoricalEmbeddingCandidate], list[HistoricalEmbeddingCandidate]]:
    pending: list[HistoricalEmbeddingCandidate] = []
    skipped: list[HistoricalEmbeddingCandidate] = []
    for candidate in candidates:
        key = (candidate.search_unit_id, candidate.embedding_input_hash)
        if key in existing_pairs:
            skipped.append(candidate)
        else:
            pending.append(candidate)
    return pending, skipped


def embed_candidate_batch(
    client: OpenAIEmbeddingsClient,
    candidates: list[HistoricalEmbeddingCandidate],
    config: EmbeddingModelConfig,
) -> list[list[float]]:
    try:
        rows = client.embed_texts([candidate.embedding_input_text for candidate in candidates], config)
    except Exception as exc:  # pragma: no cover
        raise EmbeddingGenerationError(
            model_code=config.model_code,
            chunk_descriptors=[f"{candidate.source_key}" for candidate in candidates],
            input_hashes=[candidate.embedding_input_hash for candidate in candidates],
            reason=str(exc),
        ) from exc

    for row in rows:
        validate_embedding_dimensions(row, config.embedding_dimensions)
    return rows


def insert_embedding_batch(
    *,
    candidates: list[HistoricalEmbeddingCandidate],
    embeddings: list[list[float]],
    model_id: int,
) -> None:
    generated_at = current_timestamp()
    values_sql: list[str] = []
    for candidate, embedding in zip(candidates, embeddings, strict=True):
        values_sql.append(
            "("
            f"{candidate.search_unit_id}, "
            f"{model_id}, "
            f"{sql_text(candidate.embedding_input_hash)}, "
            f"{sql_text(generated_at)}::timestamptz, "
            f"{vector_sql_literal(embedding)}::extensions.vector"
            ")"
        )

    sql = """
insert into private.historical_case_embeddings (
  historical_case_search_unit_id,
  embedding_model_id,
  input_content_hash,
  generated_at,
  embedding
)
values
""".strip() + "\n" + ",\n".join(values_sql) + """
on conflict (historical_case_search_unit_id, embedding_model_id, input_content_hash) do nothing;
""".strip()
    run_supabase_query(sql, expect_json=False)


def fetch_embedding_coverage(model_id: int) -> dict[str, object]:
    sql = f"""
with matching_embeddings as (
  select distinct chcei.search_unit_id
  from private.current_historical_case_embedding_inputs chcei
  join private.historical_case_embeddings hce
    on hce.historical_case_search_unit_id = chcei.search_unit_id
   and hce.embedding_model_id = {model_id}
   and hce.input_content_hash = chcei.embedding_input_hash
),
stale_units as (
  select distinct chcei.search_unit_id
  from private.current_historical_case_embedding_inputs chcei
  where not exists (
    select 1
    from private.historical_case_embeddings hce_current
    where hce_current.historical_case_search_unit_id = chcei.search_unit_id
      and hce_current.embedding_model_id = {model_id}
      and hce_current.input_content_hash = chcei.embedding_input_hash
  )
    and exists (
      select 1
      from private.historical_case_embeddings hce_stale
      where hce_stale.historical_case_search_unit_id = chcei.search_unit_id
        and hce_stale.embedding_model_id = {model_id}
    )
)
select
  (select count(*) from private.current_historical_case_embedding_inputs)::integer as eligible_units,
  (select count(*) from matching_embeddings)::integer as embedded_units,
  (select count(*) from stale_units)::integer as stale_units;
""".strip()
    payload = run_supabase_query(sql, expect_json=True)
    row = payload["rows"][0]
    row["missing_units"] = row["eligible_units"] - row["embedded_units"]
    row["coverage_percent"] = (
        0.0 if row["eligible_units"] == 0 else round((row["embedded_units"] / row["eligible_units"]) * 100, 2)
    )
    return row


def fetch_incomplete_source_keys(model_id: int) -> dict[str, list[str]]:
    missing_sql = f"""
select chcei.source_key
from private.current_historical_case_embedding_inputs chcei
where not exists (
  select 1
  from private.historical_case_embeddings hce
  where hce.historical_case_search_unit_id = chcei.search_unit_id
    and hce.embedding_model_id = {model_id}
    and hce.input_content_hash = chcei.embedding_input_hash
)
order by chcei.source_key;
""".strip()
    stale_sql = f"""
select distinct chcei.source_key
from private.current_historical_case_embedding_inputs chcei
where not exists (
  select 1
  from private.historical_case_embeddings hce_current
  where hce_current.historical_case_search_unit_id = chcei.search_unit_id
    and hce_current.embedding_model_id = {model_id}
    and hce_current.input_content_hash = chcei.embedding_input_hash
)
  and exists (
    select 1
    from private.historical_case_embeddings hce_stale
    where hce_stale.historical_case_search_unit_id = chcei.search_unit_id
      and hce_stale.embedding_model_id = {model_id}
  )
order by chcei.source_key;
""".strip()
    missing = [row["source_key"] for row in run_supabase_query(missing_sql, expect_json=True)["rows"]]
    stale = [row["source_key"] for row in run_supabase_query(stale_sql, expect_json=True)["rows"]]
    return {"missing_source_keys": missing, "stale_source_keys": stale}


def main() -> int:
    args = parse_args()
    validate_bootstrap_environment(operation_name="Phase 6 embedding generation")
    config = EmbeddingModelConfig(
        provider_code=args.provider,
        model_code=args.model,
        model_version=args.model_version,
        embedding_dimensions=args.dimensions,
        input_contract_code=PHASE_06_INPUT_CONTRACT_CODE,
        is_retrieval_approved=not args.mark_non_approved,
    )

    if config.provider_code != "openai":
        raise SystemExit("Only provider_code='openai' is currently supported by the repository embedding tooling.")

    candidates = load_current_candidates()
    if not candidates:
        raise SystemExit("No current-search-eligible historical units were found. Run the local Supabase reset first.")

    model = ensure_registered_model(config)
    existing_pairs = load_existing_embedding_pairs(model.id)
    pending, skipped = plan_pending_historical_embeddings(candidates, existing_pairs)

    summary: dict[str, object] = {
        "model_id": model.id,
        "provider_code": model.provider_code,
        "model_code": model.model_code,
        "model_version": model.model_version,
        "embedding_dimensions": model.embedding_dimensions,
        "config_fingerprint": model.config_fingerprint,
        "eligible_units": len(candidates),
        "already_current": len(skipped),
        "pending_generation": len(pending),
        "batch_size": args.batch_size,
        "input_contract_code": PHASE_06_INPUT_CONTRACT_CODE,
    }

    _ = embed_query_text  # keep shared semantic helpers imported explicitly for Phase 6 parity

    if pending:
        client = OpenAIEmbeddingsClient()
        for batch in batch_items(pending, args.batch_size):
            embeddings = embed_candidate_batch(client, list(batch), config)
            insert_embedding_batch(candidates=list(batch), embeddings=embeddings, model_id=model.id)

    summary.update(fetch_embedding_coverage(model.id))
    summary.update(fetch_incomplete_source_keys(model.id))
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
