create or replace function private.hybrid_retrieval_rrf_score(
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

create or replace function private.hybrid_retrieval_policy_modifier(
  p_primary_category_code text
)
returns double precision
language sql
immutable
as $$
select case p_primary_category_code
  when 'operational_procedure' then 0.011::double precision
  when 'communication_guidance' then 0.009::double precision
  when 'service_supplier_guidance' then 0.007::double precision
  when 'technical_venue_reference' then 0.007::double precision
  when 'client_facing_controlled_document' then 0.005::double precision
  when 'proposal_guidance' then 0.001::double precision
  when 'governance_canonical' then (-0.010)::double precision
  else 0::double precision
end;
$$;

create or replace function private.search_knowledge_chunks_hybrid(
  p_query_text text,
  p_query_embedding extensions.vector default null,
  p_result_limit integer default 10,
  p_candidate_pool_limit integer default 10,
  p_embedding_model_id bigint default null,
  p_document_code text default null,
  p_category_code text default null,
  p_rental_type_code text default null
)
returns table (
  chunk_id bigint,
  document_code text,
  document_title text,
  document_version_id bigint,
  document_version_number integer,
  chunk_set_id bigint,
  chunk_ordinal integer,
  section_heading text,
  heading_path text,
  question_label text,
  body_text text,
  content_hash text,
  primary_chunk_source_id bigint,
  primary_document_version_source_object_id bigint,
  primary_source_locator text,
  primary_category_code text,
  authority_classification text,
  rental_type_codes text[],
  embedding_model_id bigint,
  provider_code text,
  model_code text,
  model_version text,
  came_from_fts boolean,
  came_from_semantic boolean,
  fts_rank integer,
  semantic_rank integer,
  fts_relevance_score real,
  semantic_similarity_score double precision,
  semantic_cosine_distance double precision,
  rrf_k integer,
  rrf_fts_score double precision,
  rrf_semantic_score double precision,
  rrf_base_score double precision,
  policy_modifier double precision,
  final_score double precision
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
  approved_rrf_k constant integer := 20;
begin
  normalized_query_text := nullif(btrim(regexp_replace(coalesce(p_query_text, ''), '\s+', ' ', 'g')), '');

  if normalized_query_text is null then
    return;
  end if;

  bounded_result_limit := least(greatest(coalesce(p_result_limit, 10), 1), 50);
  bounded_candidate_pool_limit := least(
    greatest(coalesce(p_candidate_pool_limit, greatest(bounded_result_limit, 10)), bounded_result_limit),
    50
  );

  if p_query_embedding is null then
    return query
    with fts_candidates as (
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
        fts.relevance_score,
        fts.content_hash,
        fts.primary_chunk_source_id,
        fts.primary_document_version_source_object_id,
        fts.primary_source_locator,
        fts.primary_category_code,
        fts.rental_type_codes,
        row_number() over (
          order by fts.relevance_score desc, fts.document_code, fts.chunk_ordinal
        )::integer as fts_rank
      from private.search_knowledge_chunks(
        normalized_query_text,
        bounded_candidate_pool_limit,
        p_document_code,
        p_category_code,
        p_rental_type_code
      ) fts
    ),
    scored as (
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
        null::bigint as embedding_model_id,
        null::text as provider_code,
        null::text as model_code,
        null::text as model_version,
        true as came_from_fts,
        false as came_from_semantic,
        fts.fts_rank,
        null::integer as semantic_rank,
        fts.relevance_score as fts_relevance_score,
        null::double precision as semantic_similarity_score,
        null::double precision as semantic_cosine_distance,
        approved_rrf_k as rrf_k,
        private.hybrid_retrieval_rrf_score(fts.fts_rank, approved_rrf_k) as rrf_fts_score,
        0::double precision as rrf_semantic_score,
        private.hybrid_retrieval_rrf_score(fts.fts_rank, approved_rrf_k) as rrf_base_score,
        private.hybrid_retrieval_policy_modifier(fts.primary_category_code) as policy_modifier
      from fts_candidates fts
      join public.knowledge_document_versions kdv
        on kdv.id = fts.document_version_id
    )
    select
      scored.chunk_id,
      scored.document_code,
      scored.document_title,
      scored.document_version_id,
      scored.document_version_number,
      scored.chunk_set_id,
      scored.chunk_ordinal,
      scored.section_heading,
      scored.heading_path,
      scored.question_label,
      scored.body_text,
      scored.content_hash,
      scored.primary_chunk_source_id,
      scored.primary_document_version_source_object_id,
      scored.primary_source_locator,
      scored.primary_category_code,
      scored.authority_classification,
      scored.rental_type_codes,
      scored.embedding_model_id,
      scored.provider_code,
      scored.model_code,
      scored.model_version,
      scored.came_from_fts,
      scored.came_from_semantic,
      scored.fts_rank,
      scored.semantic_rank,
      scored.fts_relevance_score,
      scored.semantic_similarity_score,
      scored.semantic_cosine_distance,
      scored.rrf_k,
      scored.rrf_fts_score,
      scored.rrf_semantic_score,
      scored.rrf_base_score,
      scored.policy_modifier,
      scored.rrf_base_score + scored.policy_modifier as final_score
    from scored
    order by
      final_score desc,
      scored.document_code,
      scored.chunk_ordinal
    limit bounded_result_limit;

    return;
  end if;

  return query
  with fts_candidates as (
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
      fts.relevance_score,
      fts.content_hash,
      fts.primary_chunk_source_id,
      fts.primary_document_version_source_object_id,
      fts.primary_source_locator,
      fts.primary_category_code,
      fts.rental_type_codes,
      row_number() over (
        order by fts.relevance_score desc, fts.document_code, fts.chunk_ordinal
      )::integer as fts_rank
    from private.search_knowledge_chunks(
      normalized_query_text,
      bounded_candidate_pool_limit,
      p_document_code,
      p_category_code,
      p_rental_type_code
    ) fts
  ),
  semantic_candidates as (
    select
      sem.chunk_id,
      sem.document_code,
      sem.document_title,
      sem.document_version_id,
      sem.document_version_number,
      sem.chunk_set_id,
      sem.chunk_ordinal,
      sem.section_heading,
      sem.heading_path,
      sem.question_label,
      sem.body_text,
      sem.similarity_score,
      sem.cosine_distance,
      sem.content_hash,
      sem.input_content_hash,
      sem.embedding_model_id,
      sem.provider_code,
      sem.model_code,
      sem.model_version,
      sem.primary_chunk_source_id,
      sem.primary_document_version_source_object_id,
      sem.primary_source_locator,
      sem.primary_category_code,
      sem.rental_type_codes,
      row_number() over (
        order by sem.cosine_distance asc, sem.document_code, sem.chunk_ordinal
      )::integer as semantic_rank
    from private.search_knowledge_chunks_semantic(
      p_query_embedding,
      bounded_candidate_pool_limit,
      p_embedding_model_id,
      p_document_code,
      p_category_code,
      p_rental_type_code
    ) sem
  ),
  merged as (
    select
      coalesce(fts.chunk_id, sem.chunk_id) as chunk_id,
      coalesce(fts.document_code, sem.document_code) as document_code,
      coalesce(fts.document_title, sem.document_title) as document_title,
      coalesce(fts.document_version_id, sem.document_version_id) as document_version_id,
      coalesce(fts.document_version_number, sem.document_version_number) as document_version_number,
      coalesce(fts.chunk_set_id, sem.chunk_set_id) as chunk_set_id,
      coalesce(fts.chunk_ordinal, sem.chunk_ordinal) as chunk_ordinal,
      coalesce(fts.section_heading, sem.section_heading) as section_heading,
      coalesce(fts.heading_path, sem.heading_path) as heading_path,
      coalesce(fts.question_label, sem.question_label) as question_label,
      coalesce(fts.body_text, sem.body_text) as body_text,
      coalesce(fts.content_hash, sem.content_hash) as content_hash,
      coalesce(fts.primary_chunk_source_id, sem.primary_chunk_source_id) as primary_chunk_source_id,
      coalesce(fts.primary_document_version_source_object_id, sem.primary_document_version_source_object_id) as primary_document_version_source_object_id,
      coalesce(fts.primary_source_locator, sem.primary_source_locator) as primary_source_locator,
      coalesce(fts.primary_category_code, sem.primary_category_code) as primary_category_code,
      coalesce(fts.rental_type_codes, sem.rental_type_codes) as rental_type_codes,
      sem.embedding_model_id,
      sem.provider_code,
      sem.model_code,
      sem.model_version,
      fts.fts_rank,
      sem.semantic_rank,
      fts.relevance_score as fts_relevance_score,
      sem.similarity_score as semantic_similarity_score,
      sem.cosine_distance as semantic_cosine_distance
    from fts_candidates fts
    full outer join semantic_candidates sem
      on sem.chunk_id = fts.chunk_id
  ),
  scored as (
    select
      merged.chunk_id,
      merged.document_code,
      merged.document_title,
      merged.document_version_id,
      merged.document_version_number,
      merged.chunk_set_id,
      merged.chunk_ordinal,
      merged.section_heading,
      merged.heading_path,
      merged.question_label,
      merged.body_text,
      merged.content_hash,
      merged.primary_chunk_source_id,
      merged.primary_document_version_source_object_id,
      merged.primary_source_locator,
      merged.primary_category_code,
      kdv.authority_classification,
      merged.rental_type_codes,
      merged.embedding_model_id,
      merged.provider_code,
      merged.model_code,
      merged.model_version,
      (merged.fts_rank is not null) as came_from_fts,
      (merged.semantic_rank is not null) as came_from_semantic,
      merged.fts_rank,
      merged.semantic_rank,
      merged.fts_relevance_score,
      merged.semantic_similarity_score,
      merged.semantic_cosine_distance,
      approved_rrf_k as rrf_k,
      private.hybrid_retrieval_rrf_score(merged.fts_rank, approved_rrf_k) as rrf_fts_score,
      private.hybrid_retrieval_rrf_score(merged.semantic_rank, approved_rrf_k) as rrf_semantic_score,
      private.hybrid_retrieval_policy_modifier(merged.primary_category_code) as policy_modifier
    from merged
    join public.knowledge_document_versions kdv
      on kdv.id = merged.document_version_id
  )
  select
    scored.chunk_id,
    scored.document_code,
    scored.document_title,
    scored.document_version_id,
    scored.document_version_number,
    scored.chunk_set_id,
    scored.chunk_ordinal,
    scored.section_heading,
    scored.heading_path,
    scored.question_label,
    scored.body_text,
    scored.content_hash,
    scored.primary_chunk_source_id,
    scored.primary_document_version_source_object_id,
    scored.primary_source_locator,
    scored.primary_category_code,
    scored.authority_classification,
    scored.rental_type_codes,
    scored.embedding_model_id,
    scored.provider_code,
    scored.model_code,
    scored.model_version,
    scored.came_from_fts,
    scored.came_from_semantic,
    scored.fts_rank,
    scored.semantic_rank,
    scored.fts_relevance_score,
    scored.semantic_similarity_score,
    scored.semantic_cosine_distance,
    scored.rrf_k,
    scored.rrf_fts_score,
    scored.rrf_semantic_score,
    scored.rrf_fts_score + scored.rrf_semantic_score as rrf_base_score,
    scored.policy_modifier,
    scored.rrf_fts_score + scored.rrf_semantic_score + scored.policy_modifier as final_score
  from scored
  order by
    final_score desc,
    scored.document_code,
    scored.chunk_ordinal
  limit bounded_result_limit;
end;
$$;

revoke execute on function private.hybrid_retrieval_rrf_score(integer, integer)
  from public, anon, authenticated, service_role;
revoke execute on function private.hybrid_retrieval_policy_modifier(text)
  from public, anon, authenticated, service_role;
revoke execute on function private.search_knowledge_chunks_hybrid(text, extensions.vector, integer, integer, bigint, text, text, text)
  from public, anon, authenticated, service_role;
