from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone

from tools.phase_05_chunking.generate_pilot import run_supabase_query, sql_text
from tools.runtime_environment import validate_bootstrap_environment

from .semantic_common import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_EMBEDDING_DIMENSIONS,
    DEFAULT_MODEL_CODE,
    DEFAULT_PROVIDER_CODE,
    ChunkEmbeddingCandidate,
    EmbeddingModelConfig,
    OpenAIEmbeddingsClient,
    batch_items,
    compute_config_fingerprint,
    embed_candidate_batch,
    plan_pending_chunk_embeddings,
    vector_sql_literal,
)


@dataclass(frozen=True)
class RegisteredEmbeddingModel:
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
        description="Generate deterministic semantic embeddings for current-search-eligible Phase 5 chunks."
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
        help="Number of chunk inputs to embed per remote API request.",
    )
    parser.add_argument(
        "--mark-non-approved",
        action="store_true",
        help="Register the model without setting is_retrieval_approved = true.",
    )
    return parser.parse_args()


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_current_candidates() -> list[ChunkEmbeddingCandidate]:
    sql = """
select
  chunk_id,
  document_code,
  chunk_ordinal,
  embedding_input_text,
  embedding_input_hash
from private.current_knowledge_chunk_embedding_inputs
order by document_code, chunk_ordinal;
""".strip()
    payload = run_supabase_query(sql, expect_json=True)
    rows = payload["rows"]
    return [
        ChunkEmbeddingCandidate(
            chunk_id=row["chunk_id"],
            document_code=row["document_code"],
            chunk_ordinal=row["chunk_ordinal"],
            embedding_input_text=row["embedding_input_text"],
            embedding_input_hash=row["embedding_input_hash"],
        )
        for row in rows
    ]


def ensure_registered_model(config: EmbeddingModelConfig) -> RegisteredEmbeddingModel:
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
insert into private.knowledge_embedding_models (
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
  from private.knowledge_embedding_models
  where provider_code = {sql_text(config.provider_code)}
    and model_code = {sql_text(config.model_code)}
    and coalesce(model_version, '') = coalesce({sql_text(config.model_version)}, '')
    and config_fingerprint = {sql_text(fingerprint)}
);
""".strip()
    run_supabase_query(insert_sql, expect_json=False)

    update_sql = f"""
update private.knowledge_embedding_models
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
from private.knowledge_embedding_models
where provider_code = {sql_text(config.provider_code)}
  and model_code = {sql_text(config.model_code)}
  and coalesce(model_version, '') = coalesce({sql_text(config.model_version)}, '')
  and config_fingerprint = {sql_text(fingerprint)}
order by id
limit 1;
""".strip()
    payload = run_supabase_query(select_sql, expect_json=True)
    row = payload["rows"][0]
    return RegisteredEmbeddingModel(
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
  chunk_id,
  input_content_hash
from private.knowledge_embeddings
where embedding_model_id = {model_id};
""".strip()
    payload = run_supabase_query(sql, expect_json=True)
    return {
        (row["chunk_id"], row["input_content_hash"])
        for row in payload["rows"]
    }


def insert_embedding_batch(
    *,
    candidates: list[ChunkEmbeddingCandidate],
    embeddings: list[list[float]],
    model_id: int,
) -> None:
    generated_at = current_timestamp()
    values_sql = []
    for candidate, embedding in zip(candidates, embeddings, strict=True):
        values_sql.append(
            "("
            f"{candidate.chunk_id}, "
            f"{model_id}, "
            f"{sql_text(candidate.embedding_input_hash)}, "
            f"{sql_text(generated_at)}::timestamptz, "
            f"{vector_sql_literal(embedding)}::extensions.vector"
            ")"
        )

    sql = """
insert into private.knowledge_embeddings (
  chunk_id,
  embedding_model_id,
  input_content_hash,
  generated_at,
  embedding
)
values
""".strip() + "\n" + ",\n".join(values_sql) + """
on conflict (chunk_id, embedding_model_id, input_content_hash) do nothing;
""".strip()
    run_supabase_query(sql, expect_json=False)


def fetch_embedding_coverage(model_id: int) -> dict[str, int]:
    sql = f"""
with current_embeddings as (
  select distinct ckei.chunk_id
  from private.current_knowledge_chunk_embedding_inputs ckei
  join private.knowledge_embeddings ke
    on ke.chunk_id = ckei.chunk_id
   and ke.embedding_model_id = {model_id}
   and ke.input_content_hash = ckei.embedding_input_hash
)
select
  (select count(*) from private.current_knowledge_chunk_embedding_inputs)::integer as eligible_chunks,
  (select count(*) from current_embeddings)::integer as embedded_chunks;
""".strip()
    payload = run_supabase_query(sql, expect_json=True)
    row = payload["rows"][0]
    row["missing_chunks"] = row["eligible_chunks"] - row["embedded_chunks"]
    row["coverage_percent"] = (
        0.0 if row["eligible_chunks"] == 0 else round((row["embedded_chunks"] / row["eligible_chunks"]) * 100, 2)
    )
    return row


def main() -> int:
    args = parse_args()
    validate_bootstrap_environment(operation_name="Phase 5 embedding generation")
    config = EmbeddingModelConfig(
        provider_code=args.provider,
        model_code=args.model,
        model_version=args.model_version,
        embedding_dimensions=args.dimensions,
        is_retrieval_approved=not args.mark_non_approved,
    )

    if config.provider_code != "openai":
        raise SystemExit(f"Only provider_code='openai' is currently supported by the repository embedding tooling.")

    candidates = load_current_candidates()
    if not candidates:
        raise SystemExit("No current-search-eligible chunks were found. Run bulk chunk generation before embeddings.")

    model = ensure_registered_model(config)
    existing_pairs = load_existing_embedding_pairs(model.id)
    pending, skipped = plan_pending_chunk_embeddings(candidates, existing_pairs)

    summary = {
        "model_id": model.id,
        "provider_code": model.provider_code,
        "model_code": model.model_code,
        "model_version": model.model_version,
        "embedding_dimensions": model.embedding_dimensions,
        "config_fingerprint": model.config_fingerprint,
        "eligible_chunks": len(candidates),
        "already_current": len(skipped),
        "pending_generation": len(pending),
        "batch_size": args.batch_size,
    }

    if pending:
        client = OpenAIEmbeddingsClient()
        for batch in batch_items(pending, args.batch_size):
            embeddings = embed_candidate_batch(client, list(batch), config)
            insert_embedding_batch(candidates=list(batch), embeddings=embeddings, model_id=model.id)

    summary.update(fetch_embedding_coverage(model.id))
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
