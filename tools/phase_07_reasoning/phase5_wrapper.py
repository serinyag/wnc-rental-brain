from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from typing import Any, Callable

from tools.phase_05_chunking.generate_pilot import run_supabase_query, sql_text
from tools.phase_05_search.hybrid_common import (
    APPROVED_RRF_K,
    DEFAULT_HYBRID_CANDIDATE_POOL_LIMIT,
    bound_candidate_pool_limit,
    bound_result_limit,
    normalize_query_text,
)
from tools.phase_05_search.search_hybrid import run_hybrid_search
from tools.phase_05_search.semantic_common import (
    EmbeddingModelConfig,
    OpenAIEmbeddingsClient,
    embed_query_text,
)

from .contracts import (
    AUTHORITY_TIER_CURRENT_GOVERNED,
    CONFIDENTIALITY_LEVEL_INTERNAL,
    CONFIDENTIALITY_LEVEL_RESTRICTED,
    EXECUTION_STATE_FAILED,
    EXECUTION_STATE_FALLBACK,
    EXECUTION_STATE_NOT_REQUESTED,
    EXECUTION_STATE_NO_RESULTS,
    EXECUTION_STATE_SUCCESS,
    EXECUTION_STATE_UNAVAILABLE,
    LAYER_ID_PHASE_5,
    PERSONAL_INFORMATION_STATUS_UNKNOWN,
    PERSONAL_INFORMATION_STATUS_YES,
    ExactIdentity,
    LayerExecutionRecord,
    NormalizedResultEnvelope,
    Phase7RuntimeConfiguration,
    ProvenanceEnvelope,
    QueryContext,
    QueryPlan,
    RetrievalMetadata,
    SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
    SensitivityEnvelope,
    StableIdentity,
    authority_priority_for_tier,
)
from .validation import Phase7ContractError


PHASE5_RETRIEVAL_MODE_REQUESTED_HYBRID = "hybrid"
PHASE5_RETRIEVAL_MODE_USED_HYBRID = "hybrid"
PHASE5_RETRIEVAL_MODE_USED_FTS_FALLBACK = "fts_fallback"
PHASE5_RETRIEVAL_STRATEGY_HYBRID = "rrf_policy_weighted"
PHASE5_RETRIEVAL_STRATEGY_FTS_FALLBACK = "fts_fallback"

FALLBACK_REASON_EMBEDDING_MODEL_RESOLUTION_FAILED = "embedding_model_resolution_failed"
FALLBACK_REASON_EMBEDDING_CONFIGURATION_MISSING = "embedding_configuration_missing"
FALLBACK_REASON_CURRENT_KNOWLEDGE_EMBEDDING_CORPUS_INCOMPLETE = "current_knowledge_embedding_corpus_incomplete"
FALLBACK_REASON_QUERY_EMBEDDING_FAILED = "query_embedding_failed"
FALLBACK_REASON_HYBRID_RETRIEVAL_FAILED = "hybrid_retrieval_failed"

QueryRunner = Callable[[str], list[dict[str, Any]]]
HybridSearchRunner = Callable[..., tuple[list[dict[str, Any]], float]]
FtsSearchRunner = Callable[..., tuple[list[dict[str, Any]], float]]
ModelResolver = Callable[[QueryRunner], dict[str, Any]]
CoverageResolver = Callable[[int, QueryRunner], dict[str, Any]]
ConfigBuilder = Callable[[dict[str, Any]], EmbeddingModelConfig]
EmbeddingClientFactory = Callable[[], Any]
QueryEmbedder = Callable[[Any, str, EmbeddingModelConfig], list[float]]
MetadataLoader = Callable[[tuple[dict[str, Any], ...], QueryRunner], dict[int, dict[str, Any]]]
RelationshipLoader = Callable[[tuple[dict[str, Any], ...], QueryRunner], dict[int, list[dict[str, Any]]]]


class Phase5PreflightError(RuntimeError):
    def __init__(self, *, reason_code: str, safe_message: str) -> None:
        self.reason_code = reason_code
        self.safe_message = safe_message
        super().__init__(safe_message)


class Phase5ExecutionError(RuntimeError):
    def __init__(self, *, execution_state: str, error_category: str, safe_message: str) -> None:
        self.execution_state = execution_state
        self.error_category = error_category
        self.safe_message = safe_message
        super().__init__(safe_message)


@dataclass(frozen=True)
class Phase5WrapperConfiguration:
    execute_when_optional: bool = False


def execute_phase5_plan(
    query_plan: QueryPlan,
    query_context: QueryContext | None = None,
    runtime_configuration: Phase7RuntimeConfiguration | None = None,
    wrapper_configuration: Phase5WrapperConfiguration | None = None,
    query_runner: QueryRunner | None = None,
    hybrid_search_runner: HybridSearchRunner | None = None,
    fts_search_runner: FtsSearchRunner | None = None,
    embedding_model_resolver: ModelResolver | None = None,
    embedding_coverage_resolver: CoverageResolver | None = None,
    embedding_config_builder: ConfigBuilder | None = None,
    embedding_client_factory: EmbeddingClientFactory | None = None,
    query_embedder: QueryEmbedder | None = None,
    metadata_loader: MetadataLoader | None = None,
    relationship_loader: RelationshipLoader | None = None,
) -> LayerExecutionRecord:
    if query_context is not None and query_context.query_text != query_plan.query_text:
        raise Phase7ContractError(
            error_category="invalid_value",
            safe_message="query_context.query_text must match query_plan.query_text.",
        )

    phase5_intent = query_plan.phase_5
    config = runtime_configuration or Phase7RuntimeConfiguration()
    wrapper_config = wrapper_configuration or Phase5WrapperConfiguration()

    if phase5_intent is None or (not phase5_intent.required and not wrapper_config.execute_when_optional):
        return LayerExecutionRecord(
            layer_id=LAYER_ID_PHASE_5,
            requested=False,
            execution_state=EXECUTION_STATE_NOT_REQUESTED,
            reasoning_state=None,
            fallback_reason=None,
            error_category=None,
            safe_error_message=None,
            result_count=0,
            normalized_items=(),
        )

    runner = query_runner or _default_query_runner
    hybrid_runner = hybrid_search_runner or run_hybrid_search
    fts_runner = fts_search_runner or _run_phase5_fts_search
    model_resolver = embedding_model_resolver or _resolve_active_phase5_model
    coverage_resolver = embedding_coverage_resolver or _load_phase5_embedding_coverage
    config_builder = embedding_config_builder or _build_embedding_config_from_row
    client_factory = embedding_client_factory or OpenAIEmbeddingsClient
    embedder = query_embedder or embed_query_text
    enrich_metadata = metadata_loader or _load_phase5_metadata
    load_relationships = relationship_loader or _load_phase5_rule_relationships

    requested_query_text = phase5_intent.query_text or query_plan.query_text
    normalized_query_text = normalize_query_text(requested_query_text)
    if normalized_query_text is None:
        return LayerExecutionRecord(
            layer_id=LAYER_ID_PHASE_5,
            requested=True,
            execution_state=EXECUTION_STATE_FAILED,
            reasoning_state=None,
            fallback_reason=None,
            error_category="phase5_query_validation_failed",
            safe_error_message="Phase 5 requires a non-empty current-guidance query.",
            result_count=0,
            normalized_items=(),
        )

    result_limit = bound_result_limit(config.phase_5_result_limit)
    candidate_pool_limit = bound_candidate_pool_limit(DEFAULT_HYBRID_CANDIDATE_POOL_LIMIT, result_limit)
    filters = phase5_intent.filters

    fallback_reason: str | None = None
    rows: list[dict[str, Any]]
    retrieval_elapsed_ms = 0.0
    retrieval_mode_used = PHASE5_RETRIEVAL_MODE_USED_HYBRID
    layer_execution_state = EXECUTION_STATE_SUCCESS

    try:
        model_row = model_resolver(runner)
        model_config = config_builder(model_row)
        coverage = coverage_resolver(model_row["id"], runner)
        if not coverage["is_complete"]:
            raise Phase5PreflightError(
                reason_code=FALLBACK_REASON_CURRENT_KNOWLEDGE_EMBEDDING_CORPUS_INCOMPLETE,
                safe_message="Phase 5 semantic retrieval is not fully current for the active knowledge corpus.",
            )

        try:
            client = client_factory()
            query_embedding = embedder(client, normalized_query_text, model_config)
        except (Exception, SystemExit) as exc:
            raise Phase5PreflightError(
                reason_code=FALLBACK_REASON_QUERY_EMBEDDING_FAILED,
                safe_message="Phase 5 query embedding generation failed.",
            ) from exc

        try:
            rows, retrieval_elapsed_ms = hybrid_runner(
                query_text=normalized_query_text,
                result_limit=result_limit,
                candidate_pool_limit=candidate_pool_limit,
                query_embedding=query_embedding,
                embedding_model_id=model_row["id"],
                document_code=filters.document_code,
                category_code=filters.category_code,
                rental_type_code=filters.rental_type_code,
            )
        except Exception as exc:
            raise Phase5PreflightError(
                reason_code=FALLBACK_REASON_HYBRID_RETRIEVAL_FAILED,
                safe_message="Phase 5 hybrid retrieval failed.",
            ) from exc
    except Phase5PreflightError as exc:
        fallback_reason = exc.reason_code
        retrieval_mode_used = PHASE5_RETRIEVAL_MODE_USED_FTS_FALLBACK
        layer_execution_state = EXECUTION_STATE_FALLBACK
        try:
            rows, retrieval_elapsed_ms = fts_runner(
                query_text=normalized_query_text,
                result_limit=result_limit,
                document_code=filters.document_code,
                category_code=filters.category_code,
                rental_type_code=filters.rental_type_code,
                query_runner=runner,
            )
        except Phase5ExecutionError as fallback_exc:
            return LayerExecutionRecord(
                layer_id=LAYER_ID_PHASE_5,
                requested=True,
                execution_state=fallback_exc.execution_state,
                reasoning_state=None,
                fallback_reason=fallback_reason,
                error_category=fallback_exc.error_category,
                safe_error_message=fallback_exc.safe_message,
                result_count=0,
                normalized_items=(),
            )
        except Exception as fallback_exc:  # pragma: no cover - integration safety
            return LayerExecutionRecord(
                layer_id=LAYER_ID_PHASE_5,
                requested=True,
                execution_state=EXECUTION_STATE_FAILED,
                reasoning_state=None,
                fallback_reason=fallback_reason,
                error_category="phase5_fts_fallback_failed",
                safe_error_message="Phase 5 lexical fallback failed.",
                result_count=0,
                normalized_items=(),
            )

    if not rows:
        return LayerExecutionRecord(
            layer_id=LAYER_ID_PHASE_5,
            requested=True,
            execution_state=EXECUTION_STATE_NO_RESULTS,
            reasoning_state=None,
            fallback_reason=fallback_reason,
            error_category=None,
            safe_error_message=None,
            result_count=0,
            normalized_items=(),
        )

    rows_tuple = tuple(rows)
    warning_codes: list[str] = []
    warning_messages: list[str] = []

    try:
        metadata_by_chunk_id = enrich_metadata(rows_tuple, runner)
    except Exception:
        metadata_by_chunk_id = {
            row["chunk_id"]: _conservative_metadata_for_row(row)
            for row in rows_tuple
        }
        warning_codes.append("phase5_sensitivity_enrichment_failed")
        warning_messages.append(
            "Phase 5 sensitivity metadata could not be fully resolved; conservative restricted defaults were applied."
        )

    try:
        relationships_by_chunk_id = load_relationships(rows_tuple, runner)
    except Exception:
        relationships_by_chunk_id = {row["chunk_id"]: [] for row in rows_tuple}
        warning_codes.append("phase5_rule_relationship_enrichment_failed")
        warning_messages.append("Phase 5 rule-relationship enrichment failed for one or more retrieved chunks.")

    normalized_items = tuple(
        _normalize_phase5_row(
            row=row,
            rank=index,
            retrieval_elapsed_ms=retrieval_elapsed_ms,
            retrieval_mode_used=retrieval_mode_used,
            fallback_reason=fallback_reason,
            execution_state=layer_execution_state,
            metadata=metadata_by_chunk_id.get(row["chunk_id"], _conservative_metadata_for_row(row)),
            relationships=relationships_by_chunk_id.get(row["chunk_id"], []),
        )
        for index, row in enumerate(rows_tuple, start=1)
    )

    return LayerExecutionRecord(
        layer_id=LAYER_ID_PHASE_5,
        requested=True,
        execution_state=layer_execution_state,
        reasoning_state=None,
        fallback_reason=fallback_reason,
        error_category=";".join(warning_codes) if warning_codes else None,
        safe_error_message=" ".join(warning_messages) if warning_messages else None,
        result_count=len(normalized_items),
        normalized_items=normalized_items,
    )


def _default_query_runner(sql: str) -> list[dict[str, Any]]:
    return run_supabase_query(sql, expect_json=True)["rows"]


def _resolve_active_phase5_model(query_runner: QueryRunner) -> dict[str, Any]:
    sql = """
select
  id,
  provider_code,
  model_code,
  model_version,
  embedding_dimensions,
  configuration_json
from private.knowledge_embedding_models
where is_retrieval_approved
  and is_active
order by id;
""".strip()
    rows = query_runner(sql)
    if not rows:
        raise Phase5PreflightError(
            reason_code=FALLBACK_REASON_EMBEDDING_MODEL_RESOLUTION_FAILED,
            safe_message="No active retrieval-approved Phase 5 embedding model is registered.",
        )
    if len(rows) > 1:
        raise Phase5PreflightError(
            reason_code=FALLBACK_REASON_EMBEDDING_MODEL_RESOLUTION_FAILED,
            safe_message="Multiple active retrieval-approved Phase 5 embedding models are registered.",
        )
    return rows[0]


def _build_embedding_config_from_row(row: dict[str, Any]) -> EmbeddingModelConfig:
    configuration_json = row.get("configuration_json")
    if configuration_json is None or not isinstance(configuration_json, dict):
        raise Phase5PreflightError(
            reason_code=FALLBACK_REASON_EMBEDDING_CONFIGURATION_MISSING,
            safe_message="Phase 5 embedding model configuration is missing or invalid.",
        )
    try:
        return EmbeddingModelConfig(
            provider_code=row["provider_code"],
            model_code=row["model_code"],
            model_version=row["model_version"],
            embedding_dimensions=row["embedding_dimensions"],
            distance_metric=configuration_json.get("distance_metric", "cosine"),
            input_contract_code=configuration_json.get("input_contract_code", "phase_05_chunk_embedding_input_v1"),
            encoding_format=configuration_json.get("encoding_format", "float"),
            api_base_url=configuration_json.get("api_base_url", "https://api.openai.com/v1"),
            is_retrieval_approved=True,
            is_active=True,
        )
    except Exception as exc:
        raise Phase5PreflightError(
            reason_code=FALLBACK_REASON_EMBEDDING_CONFIGURATION_MISSING,
            safe_message="Phase 5 embedding model configuration could not be constructed.",
        ) from exc


def _load_phase5_embedding_coverage(model_id: int, query_runner: QueryRunner) -> dict[str, Any]:
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
    rows = query_runner(sql)
    if not rows:
        raise Phase5PreflightError(
            reason_code=FALLBACK_REASON_CURRENT_KNOWLEDGE_EMBEDDING_CORPUS_INCOMPLETE,
            safe_message="Phase 5 embedding coverage could not be resolved for the active knowledge corpus.",
        )
    row = rows[0]
    eligible_chunks = row["eligible_chunks"]
    embedded_chunks = row["embedded_chunks"]
    missing_chunks = eligible_chunks - embedded_chunks
    return {
        "eligible_chunks": eligible_chunks,
        "embedded_chunks": embedded_chunks,
        "missing_chunks": missing_chunks,
        "is_complete": eligible_chunks > 0 and missing_chunks == 0,
    }


def _run_phase5_fts_search(
    *,
    query_text: str,
    result_limit: int,
    document_code: str | None,
    category_code: str | None,
    rental_type_code: str | None,
    query_runner: QueryRunner,
) -> tuple[list[dict[str, Any]], float]:
    sql = f"""
select
  fts.chunk_id,
  fts.document_code,
  fts.document_title,
  fts.document_version_id,
  fts.document_version_number,
  fts.chunk_set_id,
  fts.chunk_ordinal,
  fts.section_heading,
  fts.heading_path,
  fts.question_label,
  fts.body_text,
  fts.content_hash,
  fts.primary_chunk_source_id,
  fts.primary_document_version_source_object_id,
  fts.primary_source_locator,
  fts.primary_category_code,
  kdv.authority_classification,
  fts.rental_type_codes,
  row_number() over (
    order by fts.relevance_score desc, fts.document_code, fts.chunk_ordinal
  )::integer as fts_rank,
  fts.relevance_score as fts_relevance_score
from private.search_knowledge_chunks(
  {sql_text(query_text)},
  {result_limit},
  {sql_text(document_code)},
  {sql_text(category_code)},
  {sql_text(rental_type_code)}
) fts
join public.knowledge_document_versions kdv
  on kdv.id = fts.document_version_id
order by fts_rank;
""".strip()
    started = time.perf_counter()
    try:
        rows = query_runner(sql)
    except subprocess.CalledProcessError as exc:  # pragma: no cover - integration safety
        raise Phase5ExecutionError(
            execution_state=EXECUTION_STATE_FAILED,
            error_category="phase5_fts_execution_failed",
            safe_message="Phase 5 lexical fallback failed.",
        ) from exc
    elapsed_ms = (time.perf_counter() - started) * 1000
    return rows, elapsed_ms


def _load_phase5_metadata(rows: tuple[dict[str, Any], ...], query_runner: QueryRunner) -> dict[int, dict[str, Any]]:
    chunk_ids = ", ".join(str(row["chunk_id"]) for row in rows)
    sql = f"""
with selected_chunks as (
  select unnest(array[{chunk_ids}]::bigint[]) as chunk_id
),
chunk_source_meta as (
  select
    kcs.chunk_id,
    count(*)::integer as chunk_source_count,
    array_agg(distinct sr.source_code order by sr.source_code)
      filter (where sr.source_code is not null) as source_codes,
    array_agg(
      distinct coalesce(
        kcs.source_locator,
        kso.repository_relative_path,
        kso.manual_reference_key,
        kso.external_uri,
        concat(kso.storage_bucket, '/', kso.storage_object_key),
        kso.original_filename
      )
      order by coalesce(
        kcs.source_locator,
        kso.repository_relative_path,
        kso.manual_reference_key,
        kso.external_uri,
        concat(kso.storage_bucket, '/', kso.storage_object_key),
        kso.original_filename
      )
    ) filter (
      where coalesce(
        kcs.source_locator,
        kso.repository_relative_path,
        kso.manual_reference_key,
        kso.external_uri,
        concat(kso.storage_bucket, '/', kso.storage_object_key),
        kso.original_filename
      ) is not null
    ) as source_locators,
    private.strictest_personal_information_status(
      array_agg(distinct kso.personal_information_status)
    ) as source_object_personal_information_status,
    json_agg(
      json_build_object(
        'chunk_source_id', kcs.id,
        'document_version_source_object_id', kcs.document_version_source_object_id,
        'source_object_id', kso.id,
        'source_registry_id', kso.source_registry_id,
        'source_code', sr.source_code,
        'source_locator', coalesce(
          kcs.source_locator,
          kso.repository_relative_path,
          kso.manual_reference_key,
          kso.external_uri,
          concat(kso.storage_bucket, '/', kso.storage_object_key),
          kso.original_filename
        ),
        'repository_relative_path', kso.repository_relative_path,
        'manual_reference_key', kso.manual_reference_key,
        'external_uri', kso.external_uri,
        'original_filename', kso.original_filename,
        'origin_type', kso.origin_type,
        'personal_information_status', kso.personal_information_status,
        'is_primary_trace', kcs.is_primary_trace
      )
      order by kcs.is_primary_trace desc, kcs.id
    ) as source_traces
  from private.knowledge_chunk_sources kcs
  join public.knowledge_document_version_source_objects kdvso
    on kdvso.id = kcs.document_version_source_object_id
  join public.knowledge_source_objects kso
    on kso.id = kdvso.source_object_id
  left join public.source_registry sr
    on sr.id = kso.source_registry_id
  where kcs.chunk_id in (select chunk_id from selected_chunks)
  group by kcs.chunk_id
)
select
  ckc.chunk_id,
  ckc.document_version_id,
  ckc.document_code,
  ckc.primary_chunk_source_id,
  ckc.primary_document_version_source_object_id,
  ckc.primary_source_locator,
  ckc.chunk_source_count,
  kdv.confidentiality_level_id,
  kcl.level_code as confidentiality_level_code,
  csm.source_object_personal_information_status,
  csm.source_codes,
  csm.source_locators,
  csm.source_traces,
  pso.source_object_id as primary_source_object_id,
  pkso.source_registry_id as primary_source_registry_id,
  psr.source_code as primary_source_code,
  pkso.repository_relative_path as primary_repository_relative_path,
  pkso.manual_reference_key as primary_manual_reference_key,
  pkso.external_uri as primary_external_uri,
  pkso.original_filename as primary_original_filename
from selected_chunks sc
join private.current_knowledge_chunks ckc
  on ckc.chunk_id = sc.chunk_id
join public.knowledge_document_versions kdv
  on kdv.id = ckc.document_version_id
left join public.knowledge_confidentiality_levels kcl
  on kcl.id = kdv.confidentiality_level_id
left join chunk_source_meta csm
  on csm.chunk_id = sc.chunk_id
left join public.knowledge_document_version_source_objects pso
  on pso.id = ckc.primary_document_version_source_object_id
left join public.knowledge_source_objects pkso
  on pkso.id = pso.source_object_id
left join public.source_registry psr
  on psr.id = pkso.source_registry_id
order by ckc.chunk_id;
""".strip()
    return {
        row["chunk_id"]: row
        for row in query_runner(sql)
    }


def _load_phase5_rule_relationships(
    rows: tuple[dict[str, Any], ...],
    query_runner: QueryRunner,
) -> dict[int, list[dict[str, Any]]]:
    chunk_ids = ", ".join(str(row["chunk_id"]) for row in rows)
    document_version_ids = ", ".join(str(row["document_version_id"]) for row in rows)
    sql = f"""
with selected_chunks as (
  select unnest(array[{chunk_ids}]::bigint[]) as chunk_id
),
selected_versions as (
  select unnest(array[{document_version_ids}]::bigint[]) as document_version_id
),
chunk_logical as (
  select
    kclr.chunk_id,
    'chunk'::text as relationship_scope,
    'logical_rule'::text as relationship_family,
    kclr.id as relationship_id,
    kclr.rule_code,
    null::bigint as rule_version_id,
    krrt.relationship_type_code,
    krrt.target_kind,
    kclr.notes
  from private.knowledge_chunk_logical_rules kclr
  join public.knowledge_rule_relationship_types krrt
    on krrt.id = kclr.relationship_type_id
  where kclr.chunk_id in (select chunk_id from selected_chunks)
),
chunk_exact as (
  select
    kcrv.chunk_id,
    'chunk'::text as relationship_scope,
    'rule_version'::text as relationship_family,
    kcrv.id as relationship_id,
    rc.rule_code,
    kcrv.rule_version_id,
    krrt.relationship_type_code,
    krrt.target_kind,
    kcrv.notes
  from private.knowledge_chunk_rule_versions kcrv
  join public.knowledge_rule_relationship_types krrt
    on krrt.id = kcrv.relationship_type_id
  join public.rule_catalogue rc
    on rc.id = kcrv.rule_version_id
  where kcrv.chunk_id in (select chunk_id from selected_chunks)
),
document_logical as (
  select
    ckc.chunk_id,
    'document_version'::text as relationship_scope,
    'logical_rule'::text as relationship_family,
    kdvlr.id as relationship_id,
    kdvlr.rule_code,
    null::bigint as rule_version_id,
    krrt.relationship_type_code,
    krrt.target_kind,
    kdvlr.notes
  from private.current_knowledge_chunks ckc
  join public.knowledge_document_version_logical_rules kdvlr
    on kdvlr.document_version_id = ckc.document_version_id
  join public.knowledge_rule_relationship_types krrt
    on krrt.id = kdvlr.relationship_type_id
  where ckc.chunk_id in (select chunk_id from selected_chunks)
    and ckc.document_version_id in (select document_version_id from selected_versions)
),
document_exact as (
  select
    ckc.chunk_id,
    'document_version'::text as relationship_scope,
    'rule_version'::text as relationship_family,
    kdvrv.id as relationship_id,
    rc.rule_code,
    kdvrv.rule_version_id,
    krrt.relationship_type_code,
    krrt.target_kind,
    kdvrv.notes
  from private.current_knowledge_chunks ckc
  join public.knowledge_document_version_rule_versions kdvrv
    on kdvrv.document_version_id = ckc.document_version_id
  join public.knowledge_rule_relationship_types krrt
    on krrt.id = kdvrv.relationship_type_id
  join public.rule_catalogue rc
    on rc.id = kdvrv.rule_version_id
  where ckc.chunk_id in (select chunk_id from selected_chunks)
    and ckc.document_version_id in (select document_version_id from selected_versions)
)
select *
from (
  select * from chunk_logical
  union all
  select * from chunk_exact
  union all
  select * from document_logical
  union all
  select * from document_exact
) relationships
order by chunk_id, relationship_scope, relationship_family, relationship_id;
""".strip()
    relationships_by_chunk_id: dict[int, list[dict[str, Any]]] = {row["chunk_id"]: [] for row in rows}
    for relationship in query_runner(sql):
        relationships_by_chunk_id.setdefault(relationship["chunk_id"], []).append(relationship)
    return relationships_by_chunk_id


def _normalize_phase5_row(
    *,
    row: dict[str, Any],
    rank: int,
    retrieval_elapsed_ms: float,
    retrieval_mode_used: str,
    fallback_reason: str | None,
    execution_state: str,
    metadata: dict[str, Any],
    relationships: list[dict[str, Any]],
) -> NormalizedResultEnvelope:
    provenance = _build_phase5_provenance(row, metadata)
    sensitivity = _build_phase5_sensitivity(metadata)
    retrieval = _build_phase5_retrieval_metadata(
        row=row,
        rank=rank,
        retrieval_mode_used=retrieval_mode_used,
        fallback_reason=fallback_reason,
        retrieval_elapsed_ms=retrieval_elapsed_ms,
    )

    layer_payload = dict(row)
    layer_payload["phase_4_rule_relationships"] = relationships
    layer_payload["phase5_confidentiality_level_code"] = metadata["confidentiality_level_code"]
    layer_payload["phase5_source_object_personal_information_status"] = metadata["source_object_personal_information_status"]
    layer_payload["phase5_source_traces"] = metadata["source_traces"]
    layer_payload["source_layer_role"] = SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE
    layer_payload["authority_tier_code"] = AUTHORITY_TIER_CURRENT_GOVERNED
    layer_payload["authority_priority"] = authority_priority_for_tier(AUTHORITY_TIER_CURRENT_GOVERNED)

    return NormalizedResultEnvelope(
        item_id=f"phase5:{row['document_code']}:{row['chunk_id']}",
        source_layer_role=SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
        authority_tier_code=AUTHORITY_TIER_CURRENT_GOVERNED,
        authority_priority=authority_priority_for_tier(AUTHORITY_TIER_CURRENT_GOVERNED),
        stable_identity=StableIdentity(
            primary_code=row["document_code"],
            secondary_code=None,
            native_identity_payload={
                "chunk_id": row["chunk_id"],
                "chunk_ordinal": row["chunk_ordinal"],
                "content_hash": row["content_hash"],
            },
        ),
        exact_identity=ExactIdentity(
            primary_id=row["document_version_id"],
            version_id=row["document_version_id"],
            version_number=row["document_version_number"],
            secondary_id=row["chunk_id"],
            native_identity_payload={
                "chunk_set_id": row["chunk_set_id"],
                "primary_chunk_source_id": row.get("primary_chunk_source_id"),
                "primary_document_version_source_object_id": row.get("primary_document_version_source_object_id"),
            },
        ),
        content_kind="phase5_current_governed_chunk",
        execution_state=execution_state,
        reasoning_state=None,
        summary_text=row["body_text"],
        provenance=provenance,
        sensitivity=sensitivity,
        retrieval=retrieval,
        layer_payload=layer_payload,
    )


def _build_phase5_retrieval_metadata(
    *,
    row: dict[str, Any],
    rank: int,
    retrieval_mode_used: str,
    fallback_reason: str | None,
    retrieval_elapsed_ms: float,
) -> RetrievalMetadata:
    component_scores: dict[str, float] = {}
    final_score = row.get("final_score")
    if final_score is not None:
        component_scores["final_score"] = float(final_score)
    if row.get("rrf_base_score") is not None:
        component_scores["rrf_base_score"] = float(row["rrf_base_score"])
    if row.get("policy_modifier") is not None:
        component_scores["policy_modifier"] = float(row["policy_modifier"])
    if row.get("fts_relevance_score") is not None:
        component_scores["fts_relevance_score"] = float(row["fts_relevance_score"])
    if row.get("semantic_similarity_score") is not None:
        component_scores["semantic_similarity_score"] = float(row["semantic_similarity_score"])
    component_scores["retrieval_elapsed_ms"] = float(round(retrieval_elapsed_ms, 2))

    strategy_code = (
        PHASE5_RETRIEVAL_STRATEGY_HYBRID
        if retrieval_mode_used == PHASE5_RETRIEVAL_MODE_USED_HYBRID
        else PHASE5_RETRIEVAL_STRATEGY_FTS_FALLBACK
    )

    score = None
    if retrieval_mode_used == PHASE5_RETRIEVAL_MODE_USED_HYBRID and final_score is not None:
        score = float(final_score)
    elif row.get("fts_relevance_score") is not None:
        score = float(row["fts_relevance_score"])

    return RetrievalMetadata(
        retrieval_mode_requested=PHASE5_RETRIEVAL_MODE_REQUESTED_HYBRID,
        retrieval_mode_used=retrieval_mode_used,
        fallback_used=retrieval_mode_used == PHASE5_RETRIEVAL_MODE_USED_FTS_FALLBACK,
        fallback_reason=fallback_reason if retrieval_mode_used == PHASE5_RETRIEVAL_MODE_USED_FTS_FALLBACK else None,
        rank=rank,
        score=score,
        component_scores=component_scores,
        strategy_code=strategy_code,
        native_retrieval_payload={
            "fts_rank": row.get("fts_rank"),
            "semantic_rank": row.get("semantic_rank"),
            "rrf_k": row.get("rrf_k", APPROVED_RRF_K if retrieval_mode_used == PHASE5_RETRIEVAL_MODE_USED_HYBRID else None),
            "came_from_fts": row.get("came_from_fts", True),
            "came_from_semantic": row.get("came_from_semantic", False),
            "embedding_model_id": row.get("embedding_model_id"),
            "provider_code": row.get("provider_code"),
            "model_code": row.get("model_code"),
            "model_version": row.get("model_version"),
        },
    )


def _build_phase5_provenance(row: dict[str, Any], metadata: dict[str, Any]) -> ProvenanceEnvelope:
    source_codes = tuple(_normalize_string_list(metadata.get("source_codes")))
    locators = _normalize_string_list(metadata.get("source_locators"))
    primary_locator = _clean_text(row.get("primary_source_locator")) or (locators[0] if locators else None)
    additional_locators = tuple(locator for locator in locators if locator != primary_locator)
    source_identifiers = {
        "primary_chunk_source_id": row.get("primary_chunk_source_id"),
        "primary_document_version_source_object_id": row.get("primary_document_version_source_object_id"),
        "primary_source_object_id": metadata.get("primary_source_object_id"),
        "primary_source_registry_id": metadata.get("primary_source_registry_id"),
        "document_version_id": row.get("document_version_id"),
        "chunk_id": row.get("chunk_id"),
    }
    return ProvenanceEnvelope(
        source_codes=source_codes,
        source_identifiers={key: value for key, value in source_identifiers.items() if value is not None},
        primary_source_locator=primary_locator,
        additional_locators=additional_locators,
        source_link_count=metadata.get("chunk_source_count"),
        native_provenance_payload={
            "primary_source_code": metadata.get("primary_source_code"),
            "primary_repository_relative_path": metadata.get("primary_repository_relative_path"),
            "primary_manual_reference_key": metadata.get("primary_manual_reference_key"),
            "primary_external_uri": metadata.get("primary_external_uri"),
            "primary_original_filename": metadata.get("primary_original_filename"),
            "source_traces": metadata.get("source_traces", []),
        },
    )


def _build_phase5_sensitivity(metadata: dict[str, Any]) -> SensitivityEnvelope:
    confidentiality_level = metadata.get("confidentiality_level_code") or CONFIDENTIALITY_LEVEL_INTERNAL
    pi_status = metadata.get("source_object_personal_information_status") or PERSONAL_INFORMATION_STATUS_UNKNOWN
    native_payload = {}
    if metadata.get("sensitivity_warning") is not None:
        native_payload["warning"] = metadata["sensitivity_warning"]
    return SensitivityEnvelope(
        confidentiality_level=confidentiality_level,
        personal_information_status=pi_status,
        de_identification_required=pi_status == PERSONAL_INFORMATION_STATUS_YES,
        generation_allowed=True,
        generation_restriction_reason=None,
        native_sensitivity_payload=native_payload,
    )


def _conservative_metadata_for_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "chunk_id": row["chunk_id"],
        "chunk_source_count": 1 if row.get("primary_chunk_source_id") is not None else 0,
        "confidentiality_level_code": CONFIDENTIALITY_LEVEL_RESTRICTED,
        "source_object_personal_information_status": PERSONAL_INFORMATION_STATUS_UNKNOWN,
        "source_codes": [],
        "source_locators": [_clean_text(row.get("primary_source_locator"))] if _clean_text(row.get("primary_source_locator")) else [],
        "source_traces": [],
        "primary_source_object_id": None,
        "primary_source_registry_id": None,
        "primary_source_code": None,
        "primary_repository_relative_path": None,
        "primary_manual_reference_key": None,
        "primary_external_uri": None,
        "primary_original_filename": None,
        "sensitivity_warning": "conservative_restricted_default_applied",
    }


def _normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        cleaned = _clean_text(value)
        return [cleaned] if cleaned is not None else []
    values: list[str] = []
    for item in value:
        cleaned = _clean_text(item)
        if cleaned is not None and cleaned not in values:
            values.append(cleaned)
    return values


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "Phase5ExecutionError",
    "Phase5WrapperConfiguration",
    "execute_phase5_plan",
]
