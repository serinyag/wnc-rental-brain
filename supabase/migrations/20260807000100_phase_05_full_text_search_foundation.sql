alter table private.knowledge_chunks
  add column if not exists search_vector tsvector
  generated always as (
    setweight(to_tsvector('english'::regconfig, coalesce(document_title_snapshot, '')), 'A')
    || setweight(to_tsvector('english'::regconfig, coalesce(section_heading, '')), 'B')
    || setweight(to_tsvector('english'::regconfig, coalesce(heading_path, '')), 'B')
    || setweight(to_tsvector('english'::regconfig, coalesce(question_label, '')), 'B')
    || setweight(to_tsvector('english'::regconfig, coalesce(body_text, '')), 'D')
  ) stored;

create index if not exists knowledge_chunks_search_vector_gin_idx
  on private.knowledge_chunks
  using gin (search_vector);

create or replace view private.current_knowledge_chunks as
with rental_type_codes as (
  select
    kdvrt.document_version_id,
    array_agg(distinct rt.rental_type_code order by rt.rental_type_code) as rental_type_codes
  from public.knowledge_document_version_rental_types kdvrt
  join public.rental_types rt
    on rt.id = kdvrt.rental_type_id
  group by kdvrt.document_version_id
)
select
  kc.id as chunk_id,
  kc.chunk_set_id,
  kcs.document_version_id,
  kdv.version_number as document_version_number,
  kd.document_code,
  kd.canonical_title as document_title,
  kcat.category_code as primary_category_code,
  kc.chunk_ordinal,
  kc.section_heading,
  kc.heading_path,
  kc.question_label,
  kc.document_title_snapshot,
  kc.body_text,
  kc.content_hash,
  kc.token_count,
  kc.search_vector,
  pcs.chunk_source_id as primary_chunk_source_id,
  pcs.document_version_source_object_id as primary_document_version_source_object_id,
  pcs.source_locator as primary_source_locator,
  psrc.chunk_source_count,
  rtc.rental_type_codes
from private.knowledge_chunks kc
join private.knowledge_chunk_sets kcs
  on kcs.id = kc.chunk_set_id
join public.knowledge_document_versions kdv
  on kdv.id = kcs.document_version_id
join public.knowledge_documents kd
  on kd.id = kdv.document_id
join public.knowledge_categories kcat
  on kcat.id = kd.primary_category_id
join public.knowledge_document_corpus_states kdcs
  on kdcs.document_id = kd.id
 and kdcs.is_current
join lateral (
  select
    ksrc.id as chunk_source_id,
    ksrc.document_version_source_object_id,
    ksrc.source_locator
  from private.knowledge_chunk_sources ksrc
  where ksrc.chunk_id = kc.id
  order by ksrc.is_primary_trace desc, ksrc.id
  limit 1
) pcs on true
join lateral (
  select count(*)::bigint as chunk_source_count
  from private.knowledge_chunk_sources ksrc_count
  where ksrc_count.chunk_id = kc.id
) psrc on true
left join rental_type_codes rtc
  on rtc.document_version_id = kdv.id
where kdcs.corpus_status = 'include'
  and kdv.governance_status = 'active'
  and (kdv.effective_from is null or kdv.effective_from <= current_date)
  and (kdv.effective_until is null or kdv.effective_until >= current_date)
  and kcs.generation_status = 'current';

create or replace function private.search_knowledge_chunks(
  p_query_text text,
  p_result_limit integer default 10,
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
  relevance_score real,
  content_hash text,
  primary_chunk_source_id bigint,
  primary_document_version_source_object_id bigint,
  primary_source_locator text,
  primary_category_code text,
  rental_type_codes text[]
)
language sql
stable
security invoker
set search_path = pg_catalog, private, public
as $$
with normalized as (
  select
    nullif(btrim(regexp_replace(coalesce(p_query_text, ''), '\s+', ' ', 'g')), '') as query_text,
    least(greatest(coalesce(p_result_limit, 10), 1), 50) as result_limit
),
parsed as (
  select
    query_text,
    result_limit,
    case
      when query_text is not null then websearch_to_tsquery('english'::regconfig, query_text)
      else null
    end as ts_query
  from normalized
),
eligible_query as (
  select
    query_text,
    result_limit,
    ts_query
  from parsed
  where query_text is not null
    and numnode(ts_query) > 0
)
select
  ckc.chunk_id,
  ckc.document_code,
  ckc.document_title,
  ckc.document_version_id,
  ckc.document_version_number,
  ckc.chunk_set_id,
  ckc.chunk_ordinal,
  ckc.section_heading,
  ckc.heading_path,
  ckc.question_label,
  ckc.body_text,
  ts_rank_cd(ckc.search_vector, eq.ts_query) as relevance_score,
  ckc.content_hash,
  ckc.primary_chunk_source_id,
  ckc.primary_document_version_source_object_id,
  ckc.primary_source_locator,
  ckc.primary_category_code,
  ckc.rental_type_codes
from eligible_query eq
join private.current_knowledge_chunks ckc
  on ckc.search_vector @@ eq.ts_query
where (p_document_code is null or ckc.document_code = p_document_code)
  and (p_category_code is null or ckc.primary_category_code = p_category_code)
  and (
    p_rental_type_code is null
    or p_rental_type_code = any(coalesce(ckc.rental_type_codes, array[]::text[]))
  )
order by relevance_score desc, ckc.document_code, ckc.chunk_ordinal
limit (
  select coalesce(eq_limit.result_limit, 0)
  from eligible_query eq_limit
  limit 1
);
$$;

revoke all on table private.current_knowledge_chunks from public, anon, authenticated, service_role;
revoke execute on function private.search_knowledge_chunks(text, integer, text, text, text)
  from public, anon, authenticated, service_role;
