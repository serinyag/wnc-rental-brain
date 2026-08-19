create or replace function private.historical_hybrid_rrf_score(
  p_rank integer,
  p_rrf_k integer default 20
)
returns double precision
language sql
immutable
as $$
select case
  when p_rank is null or p_rank <= 0 then 0::double precision
  when p_rrf_k <= 0 then 0::double precision
  else 1::double precision / (p_rrf_k + p_rank)::double precision
end;
$$;

create or replace function private.search_historical_case_units_hybrid(
  p_query_text text,
  p_query_embedding extensions.vector,
  p_result_limit integer default 10,
  p_candidate_pool_limit integer default 20,
  p_embedding_model_id bigint default null,
  p_strategy_code text default 'historical_rrf_balanced',
  p_case_code text default null,
  p_unit_type text default null,
  p_precedent_availability text default null,
  p_precedent_type text default null,
  p_lesson_kind text default null,
  p_historical_value_only boolean default null,
  p_contamination_risk_level text default null
)
returns table (
  search_unit_id bigint,
  source_layer_role text,
  source_key text,
  unit_type text,
  search_text text,
  historical_case_id bigint,
  historical_case_version_id bigint,
  case_code text,
  case_title text,
  precedent_type text,
  precedent_availability text,
  case_evidence_strength text,
  unit_evidence_strength text,
  actor_type text,
  lesson_kind text,
  historical_value_only boolean,
  contamination_risk_level text,
  current_authority_disposition text,
  case_contains_historical_value_only_content boolean,
  effective_confidentiality_level_id bigint,
  effective_confidentiality_level_code text,
  case_personal_information_status text,
  source_object_personal_information_status text,
  primary_historical_case_version_source_object_id bigint,
  primary_source_object_id bigint,
  primary_source_locator text,
  source_link_count bigint,
  responsibility_id bigint,
  decision_id bigint,
  lesson_id bigint,
  embedding_model_id bigint,
  provider_code text,
  model_code text,
  model_version text,
  strategy_code text,
  came_from_fts boolean,
  came_from_semantic boolean,
  fts_rank integer,
  semantic_rank integer,
  best_component_rank integer,
  lexical_score real,
  semantic_similarity_score double precision,
  semantic_cosine_distance double precision,
  rrf_k integer,
  lexical_weight double precision,
  semantic_weight double precision,
  rrf_fts_score double precision,
  rrf_semantic_score double precision,
  hybrid_score double precision
)
language plpgsql
stable
security invoker
set search_path = pg_catalog, private, public, extensions
as $$
declare
  normalized_query_text text;
  bounded_result_limit integer;
  bounded_candidate_pool_limit integer;
  normalized_strategy_code text;
  resolved_embedding_model_id bigint;
  resolved_embedding_dimensions integer;
  resolved_provider_code text;
  resolved_model_code text;
  resolved_model_version text;
  actual_query_dimensions integer;
  approved_model_count integer;
  lexical_weight_value double precision;
  semantic_weight_value double precision;
  approved_rrf_k integer;
  eligible_unit_count integer;
  current_embedding_count integer;
  stale_unit_count integer;
begin
  normalized_query_text := nullif(
    btrim(regexp_replace(coalesce(p_query_text, ''), '\s+', ' ', 'g')),
    ''
  );

  if normalized_query_text is null then
    return;
  end if;

  if p_query_embedding is null then
    raise exception 'query embedding is required for historical hybrid retrieval'
      using errcode = '22004';
  end if;

  normalized_strategy_code := nullif(lower(btrim(coalesce(p_strategy_code, ''))), '');
  if normalized_strategy_code is null then
    normalized_strategy_code := 'historical_rrf_balanced';
  end if;

  case normalized_strategy_code
    when 'historical_rrf_balanced' then
      approved_rrf_k := 20;
      lexical_weight_value := 1.0;
      semantic_weight_value := 1.0;
    when 'historical_rrf_lexical_125' then
      approved_rrf_k := 20;
      lexical_weight_value := 1.25;
      semantic_weight_value := 1.0;
    when 'historical_rrf_semantic_125' then
      approved_rrf_k := 20;
      lexical_weight_value := 1.0;
      semantic_weight_value := 1.25;
    else
      raise exception 'unsupported historical hybrid strategy_code: %', normalized_strategy_code
        using errcode = '22023';
  end case;

  bounded_result_limit := least(greatest(coalesce(p_result_limit, 10), 1), 50);

  if p_embedding_model_id is null then
    select count(*)
    into approved_model_count
    from private.historical_case_embedding_models hcem
    where hcem.is_retrieval_approved
      and hcem.is_active;

    if approved_model_count = 0 then
      raise exception 'no active retrieval-approved historical embedding model is registered'
        using errcode = 'P0001';
    end if;

    if approved_model_count > 1 then
      raise exception 'multiple active retrieval-approved historical embedding models are registered'
        using errcode = 'P0001';
    end if;

    select
      hcem.id,
      hcem.embedding_dimensions,
      hcem.provider_code,
      hcem.model_code,
      hcem.model_version
    into
      resolved_embedding_model_id,
      resolved_embedding_dimensions,
      resolved_provider_code,
      resolved_model_code,
      resolved_model_version
    from private.historical_case_embedding_models hcem
    where hcem.is_retrieval_approved
      and hcem.is_active;
  else
    select
      hcem.id,
      hcem.embedding_dimensions,
      hcem.provider_code,
      hcem.model_code,
      hcem.model_version
    into
      resolved_embedding_model_id,
      resolved_embedding_dimensions,
      resolved_provider_code,
      resolved_model_code,
      resolved_model_version
    from private.historical_case_embedding_models hcem
    where hcem.id = p_embedding_model_id
      and hcem.is_retrieval_approved
      and hcem.is_active;

    if resolved_embedding_model_id is null then
      raise exception 'historical embedding model % is not an active retrieval-approved model',
        p_embedding_model_id
        using errcode = '23503';
    end if;
  end if;

  actual_query_dimensions := extensions.vector_dims(p_query_embedding);
  if actual_query_dimensions <> resolved_embedding_dimensions then
    raise exception 'query embedding dimensions % do not match historical embedding model % dimensions %',
      actual_query_dimensions,
      resolved_embedding_model_id,
      resolved_embedding_dimensions
      using errcode = '23514';
  end if;

  with eligible_inputs as (
    select
      chcei.search_unit_id,
      chcei.embedding_input_hash
    from private.current_historical_case_embedding_inputs chcei
  ),
  current_matches as (
    select distinct ei.search_unit_id
    from eligible_inputs ei
    join private.historical_case_embeddings hce
      on hce.historical_case_search_unit_id = ei.search_unit_id
     and hce.embedding_model_id = resolved_embedding_model_id
     and hce.input_content_hash = ei.embedding_input_hash
  ),
  stale_units as (
    select distinct ei.search_unit_id
    from eligible_inputs ei
    where not exists (
      select 1
      from private.historical_case_embeddings hce_current
      where hce_current.historical_case_search_unit_id = ei.search_unit_id
        and hce_current.embedding_model_id = resolved_embedding_model_id
        and hce_current.input_content_hash = ei.embedding_input_hash
    )
      and exists (
        select 1
        from private.historical_case_embeddings hce_stale
        where hce_stale.historical_case_search_unit_id = ei.search_unit_id
          and hce_stale.embedding_model_id = resolved_embedding_model_id
      )
  )
  select
    (select count(*)::integer from eligible_inputs),
    (select count(*)::integer from current_matches),
    (select count(*)::integer from stale_units)
  into
    eligible_unit_count,
    current_embedding_count,
    stale_unit_count;

  if current_embedding_count <> eligible_unit_count or stale_unit_count <> 0 then
    raise exception
      'historical hybrid retrieval requires complete current embeddings for model % (eligible %, current %, stale %)',
      resolved_embedding_model_id,
      eligible_unit_count,
      current_embedding_count,
      stale_unit_count
      using errcode = 'P0001';
  end if;

  bounded_candidate_pool_limit := least(
    greatest(coalesce(p_candidate_pool_limit, 20), bounded_result_limit),
    greatest(eligible_unit_count, bounded_result_limit)
  );

  return query
  with fts_candidates as (
    select
      fts.search_unit_id,
      fts.source_layer_role,
      fts.source_key,
      fts.unit_type,
      fts.search_text,
      fts.lexical_score,
      fts.historical_case_id,
      fts.historical_case_version_id,
      fts.case_code,
      fts.case_title,
      fts.precedent_type,
      fts.precedent_availability,
      fts.case_evidence_strength,
      fts.unit_evidence_strength,
      fts.actor_type,
      fts.lesson_kind,
      fts.historical_value_only,
      fts.contamination_risk_level,
      fts.current_authority_disposition,
      fts.case_contains_historical_value_only_content,
      fts.effective_confidentiality_level_id,
      fts.effective_confidentiality_level_code,
      fts.case_personal_information_status,
      fts.source_object_personal_information_status,
      fts.primary_historical_case_version_source_object_id,
      fts.primary_source_object_id,
      fts.primary_source_locator,
      fts.source_link_count,
      fts.responsibility_id,
      fts.decision_id,
      fts.lesson_id,
      row_number() over (
        order by fts.lexical_score desc, fts.case_code, fts.unit_type, fts.search_unit_id
      )::integer as fts_rank
    from private.search_historical_case_units(
      normalized_query_text,
      bounded_candidate_pool_limit,
      p_case_code,
      p_unit_type,
      p_precedent_availability,
      p_precedent_type,
      p_lesson_kind,
      p_historical_value_only,
      p_contamination_risk_level
    ) fts
  ),
  semantic_candidates as (
    select
      sem.search_unit_id,
      sem.source_layer_role,
      sem.source_key,
      sem.unit_type,
      sem.search_text,
      sem.similarity_score,
      sem.cosine_distance,
      sem.input_content_hash,
      sem.historical_case_id,
      sem.historical_case_version_id,
      sem.case_code,
      sem.case_title,
      sem.precedent_type,
      sem.precedent_availability,
      sem.case_evidence_strength,
      sem.unit_evidence_strength,
      sem.actor_type,
      sem.lesson_kind,
      sem.historical_value_only,
      sem.contamination_risk_level,
      sem.current_authority_disposition,
      sem.case_contains_historical_value_only_content,
      sem.effective_confidentiality_level_id,
      sem.effective_confidentiality_level_code,
      sem.case_personal_information_status,
      sem.source_object_personal_information_status,
      sem.primary_historical_case_version_source_object_id,
      sem.primary_source_object_id,
      sem.primary_source_locator,
      sem.source_link_count,
      sem.responsibility_id,
      sem.decision_id,
      sem.lesson_id,
      row_number() over (
        order by sem.cosine_distance asc, sem.case_code, sem.unit_type, sem.search_unit_id
      )::integer as semantic_rank
    from private.search_historical_case_units_semantic(
      p_query_embedding,
      bounded_candidate_pool_limit,
      resolved_embedding_model_id,
      p_case_code,
      p_unit_type,
      p_precedent_availability,
      p_precedent_type,
      p_lesson_kind,
      p_historical_value_only,
      p_contamination_risk_level
    ) sem
  ),
  merged as (
    select
      coalesce(fts.search_unit_id, sem.search_unit_id) as search_unit_id,
      coalesce(fts.source_layer_role, sem.source_layer_role) as source_layer_role,
      coalesce(fts.source_key, sem.source_key) as source_key,
      coalesce(fts.unit_type, sem.unit_type) as unit_type,
      coalesce(fts.search_text, sem.search_text) as search_text,
      coalesce(fts.historical_case_id, sem.historical_case_id) as historical_case_id,
      coalesce(fts.historical_case_version_id, sem.historical_case_version_id) as historical_case_version_id,
      coalesce(fts.case_code, sem.case_code) as case_code,
      coalesce(fts.case_title, sem.case_title) as case_title,
      coalesce(fts.precedent_type, sem.precedent_type) as precedent_type,
      coalesce(fts.precedent_availability, sem.precedent_availability) as precedent_availability,
      coalesce(fts.case_evidence_strength, sem.case_evidence_strength) as case_evidence_strength,
      coalesce(fts.unit_evidence_strength, sem.unit_evidence_strength) as unit_evidence_strength,
      coalesce(fts.actor_type, sem.actor_type) as actor_type,
      coalesce(fts.lesson_kind, sem.lesson_kind) as lesson_kind,
      coalesce(fts.historical_value_only, sem.historical_value_only) as historical_value_only,
      coalesce(fts.contamination_risk_level, sem.contamination_risk_level) as contamination_risk_level,
      coalesce(fts.current_authority_disposition, sem.current_authority_disposition) as current_authority_disposition,
      coalesce(fts.case_contains_historical_value_only_content, sem.case_contains_historical_value_only_content) as case_contains_historical_value_only_content,
      coalesce(fts.effective_confidentiality_level_id, sem.effective_confidentiality_level_id) as effective_confidentiality_level_id,
      coalesce(fts.effective_confidentiality_level_code, sem.effective_confidentiality_level_code) as effective_confidentiality_level_code,
      coalesce(fts.case_personal_information_status, sem.case_personal_information_status) as case_personal_information_status,
      coalesce(fts.source_object_personal_information_status, sem.source_object_personal_information_status) as source_object_personal_information_status,
      coalesce(fts.primary_historical_case_version_source_object_id, sem.primary_historical_case_version_source_object_id) as primary_historical_case_version_source_object_id,
      coalesce(fts.primary_source_object_id, sem.primary_source_object_id) as primary_source_object_id,
      coalesce(fts.primary_source_locator, sem.primary_source_locator) as primary_source_locator,
      coalesce(fts.source_link_count, sem.source_link_count) as source_link_count,
      coalesce(fts.responsibility_id, sem.responsibility_id) as responsibility_id,
      coalesce(fts.decision_id, sem.decision_id) as decision_id,
      coalesce(fts.lesson_id, sem.lesson_id) as lesson_id,
      fts.fts_rank,
      sem.semantic_rank,
      fts.lexical_score,
      sem.similarity_score as semantic_similarity_score,
      sem.cosine_distance as semantic_cosine_distance
    from fts_candidates fts
    full outer join semantic_candidates sem
      on sem.search_unit_id = fts.search_unit_id
  ),
  scored as (
    select
      merged.search_unit_id,
      merged.source_layer_role,
      merged.source_key,
      merged.unit_type,
      merged.search_text,
      merged.historical_case_id,
      merged.historical_case_version_id,
      merged.case_code,
      merged.case_title,
      merged.precedent_type,
      merged.precedent_availability,
      merged.case_evidence_strength,
      merged.unit_evidence_strength,
      merged.actor_type,
      merged.lesson_kind,
      merged.historical_value_only,
      merged.contamination_risk_level,
      merged.current_authority_disposition,
      merged.case_contains_historical_value_only_content,
      merged.effective_confidentiality_level_id,
      merged.effective_confidentiality_level_code,
      merged.case_personal_information_status,
      merged.source_object_personal_information_status,
      merged.primary_historical_case_version_source_object_id,
      merged.primary_source_object_id,
      merged.primary_source_locator,
      merged.source_link_count,
      merged.responsibility_id,
      merged.decision_id,
      merged.lesson_id,
      resolved_embedding_model_id as embedding_model_id,
      resolved_provider_code as provider_code,
      resolved_model_code as model_code,
      resolved_model_version as model_version,
      normalized_strategy_code as strategy_code,
      (merged.fts_rank is not null) as came_from_fts,
      (merged.semantic_rank is not null) as came_from_semantic,
      merged.fts_rank,
      merged.semantic_rank,
      least(
        coalesce(merged.fts_rank, 2147483647),
        coalesce(merged.semantic_rank, 2147483647)
      )::integer as best_component_rank,
      merged.lexical_score,
      merged.semantic_similarity_score,
      merged.semantic_cosine_distance,
      approved_rrf_k as rrf_k,
      lexical_weight_value as lexical_weight,
      semantic_weight_value as semantic_weight,
      lexical_weight_value * private.historical_hybrid_rrf_score(merged.fts_rank, approved_rrf_k) as rrf_fts_score,
      semantic_weight_value * private.historical_hybrid_rrf_score(merged.semantic_rank, approved_rrf_k) as rrf_semantic_score
    from merged
  )
  select
    scored.search_unit_id,
    scored.source_layer_role,
    scored.source_key,
    scored.unit_type,
    scored.search_text,
    scored.historical_case_id,
    scored.historical_case_version_id,
    scored.case_code,
    scored.case_title,
    scored.precedent_type,
    scored.precedent_availability,
    scored.case_evidence_strength,
    scored.unit_evidence_strength,
    scored.actor_type,
    scored.lesson_kind,
    scored.historical_value_only,
    scored.contamination_risk_level,
    scored.current_authority_disposition,
    scored.case_contains_historical_value_only_content,
    scored.effective_confidentiality_level_id,
    scored.effective_confidentiality_level_code,
    scored.case_personal_information_status,
    scored.source_object_personal_information_status,
    scored.primary_historical_case_version_source_object_id,
    scored.primary_source_object_id,
    scored.primary_source_locator,
    scored.source_link_count,
    scored.responsibility_id,
    scored.decision_id,
    scored.lesson_id,
    scored.embedding_model_id,
    scored.provider_code,
    scored.model_code,
    scored.model_version,
    scored.strategy_code,
    scored.came_from_fts,
    scored.came_from_semantic,
    scored.fts_rank,
    scored.semantic_rank,
    scored.best_component_rank,
    scored.lexical_score,
    scored.semantic_similarity_score,
    scored.semantic_cosine_distance,
    scored.rrf_k,
    scored.lexical_weight,
    scored.semantic_weight,
    scored.rrf_fts_score,
    scored.rrf_semantic_score,
    scored.rrf_fts_score + scored.rrf_semantic_score as hybrid_score
  from scored
  order by
    hybrid_score desc,
    scored.best_component_rank asc,
    scored.case_code,
    scored.unit_type,
    scored.search_unit_id
  limit bounded_result_limit;
end;
$$;

revoke execute on function private.historical_hybrid_rrf_score(integer, integer)
  from public, anon, authenticated, service_role;
revoke execute on function private.search_historical_case_units_hybrid(
  text,
  extensions.vector,
  integer,
  integer,
  bigint,
  text,
  text,
  text,
  text,
  text,
  text,
  boolean,
  text
)
  from public, anon, authenticated, service_role;
