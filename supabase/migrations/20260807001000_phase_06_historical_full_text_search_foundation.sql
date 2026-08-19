alter table private.historical_case_search_units
  add column if not exists search_vector tsvector
  generated always as (
    setweight(to_tsvector('english'::regconfig, coalesce(case_title_snapshot, '')), 'A')
    || setweight(to_tsvector('english'::regconfig, coalesce(case_code_snapshot, '')), 'B')
    || setweight(to_tsvector('english'::regconfig, coalesce(search_text, '')), 'B')
    || setweight(to_tsvector('english'::regconfig, coalesce(unit_type, '')), 'C')
    || setweight(to_tsvector('english'::regconfig, coalesce(actor_type, '')), 'C')
    || setweight(to_tsvector('english'::regconfig, coalesce(lesson_kind, '')), 'C')
  ) stored;

create index if not exists historical_case_search_units_search_vector_gin_idx
  on private.historical_case_search_units
  using gin (search_vector);

create or replace function private.search_historical_case_units(
  p_query_text text,
  p_result_limit integer default 10,
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
  lexical_score real,
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
  lesson_id bigint
)
language plpgsql
stable
security invoker
set search_path = pg_catalog, private, public
as $$
declare
  normalized_query_text text;
  normalized_case_code text;
  normalized_unit_type text;
  normalized_precedent_availability text;
  normalized_precedent_type text;
  normalized_lesson_kind text;
  normalized_contamination_risk_level text;
  normalized_result_limit integer;
  parsed_query tsquery;
begin
  normalized_query_text := nullif(
    btrim(regexp_replace(coalesce(p_query_text, ''), '\s+', ' ', 'g')),
    ''
  );
  normalized_case_code := nullif(upper(btrim(coalesce(p_case_code, ''))), '');
  normalized_unit_type := nullif(lower(btrim(coalesce(p_unit_type, ''))), '');
  normalized_precedent_availability := nullif(lower(btrim(coalesce(p_precedent_availability, ''))), '');
  normalized_precedent_type := nullif(lower(btrim(coalesce(p_precedent_type, ''))), '');
  normalized_lesson_kind := nullif(lower(btrim(coalesce(p_lesson_kind, ''))), '');
  normalized_contamination_risk_level := nullif(lower(btrim(coalesce(p_contamination_risk_level, ''))), '');
  normalized_result_limit := least(greatest(coalesce(p_result_limit, 10), 1), 50);

  if normalized_unit_type is not null
     and normalized_unit_type not in ('case_narrative', 'responsibility', 'decision', 'lesson') then
    raise exception 'unsupported historical unit_type filter: %', normalized_unit_type
      using errcode = '22023';
  end if;

  if normalized_precedent_availability is not null
     and normalized_precedent_availability not in ('active', 'limited') then
    raise exception 'unsupported historical precedent_availability filter: %', normalized_precedent_availability
      using errcode = '22023';
  end if;

  if normalized_precedent_type is not null
     and normalized_precedent_type not in ('full_case', 'limited_precedent', 'cautionary_precedent') then
    raise exception 'unsupported historical precedent_type filter: %', normalized_precedent_type
      using errcode = '22023';
  end if;

  if normalized_lesson_kind is not null
     and normalized_lesson_kind not in ('source_explicit', 'curated_lesson', 'analyst_inference', 'caution_warning') then
    raise exception 'unsupported historical lesson_kind filter: %', normalized_lesson_kind
      using errcode = '22023';
  end if;

  if normalized_contamination_risk_level is not null
     and normalized_contamination_risk_level not in ('low', 'medium', 'high') then
    raise exception 'unsupported historical contamination_risk_level filter: %', normalized_contamination_risk_level
      using errcode = '22023';
  end if;

  if normalized_query_text is null then
    return;
  end if;

  parsed_query := websearch_to_tsquery('english'::regconfig, normalized_query_text);

  if numnode(parsed_query) = 0 then
    return;
  end if;

  return query
  select
    chcsu.search_unit_id,
    chcsu.source_layer_role,
    chcsu.source_key,
    chcsu.unit_type,
    chcsu.search_text,
    ts_rank_cd(hcsu.search_vector, parsed_query, 2) as lexical_score,
    chcsu.historical_case_id,
    chcsu.historical_case_version_id,
    chcsu.case_code,
    chcsu.case_title,
    chcsu.precedent_type,
    chcsu.precedent_availability,
    chcsu.case_evidence_strength,
    chcsu.unit_evidence_strength,
    chcsu.actor_type,
    chcsu.lesson_kind,
    chcsu.historical_value_only,
    chcsu.contamination_risk_level,
    chcsu.current_authority_disposition,
    chcsu.case_contains_historical_value_only_content,
    chcsu.effective_confidentiality_level_id,
    chcsu.effective_confidentiality_level_code,
    chcsu.case_personal_information_status,
    chcsu.source_object_personal_information_status,
    chcsu.primary_historical_case_version_source_object_id,
    chcsu.primary_source_object_id,
    chcsu.primary_source_locator,
    chcsu.source_link_count,
    chcsu.responsibility_id,
    chcsu.decision_id,
    chcsu.lesson_id
  from private.current_historical_case_search_units chcsu
  join private.historical_case_search_units hcsu
    on hcsu.id = chcsu.search_unit_id
  where hcsu.search_vector @@ parsed_query
    and (normalized_case_code is null or chcsu.case_code = normalized_case_code)
    and (normalized_unit_type is null or chcsu.unit_type = normalized_unit_type)
    and (
      normalized_precedent_availability is null
      or chcsu.precedent_availability = normalized_precedent_availability
    )
    and (
      normalized_precedent_type is null
      or chcsu.precedent_type = normalized_precedent_type
    )
    and (
      normalized_lesson_kind is null
      or chcsu.lesson_kind = normalized_lesson_kind
    )
    and (
      p_historical_value_only is null
      or chcsu.historical_value_only = p_historical_value_only
    )
    and (
      normalized_contamination_risk_level is null
      or chcsu.contamination_risk_level = normalized_contamination_risk_level
    )
  order by
    lexical_score desc,
    chcsu.case_code,
    chcsu.unit_type,
    chcsu.search_unit_id
  limit normalized_result_limit;
end;
$$;

revoke execute on function private.search_historical_case_units(
  text,
  integer,
  text,
  text,
  text,
  text,
  text,
  boolean,
  text
)
from public, anon, authenticated, service_role;
