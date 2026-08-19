begin;

create extension if not exists pgtap with schema extensions;
set local search_path to private, public, api, extensions;

create temp table phase5_chunk_baseline as
select count(*)::bigint as chunk_count
from private.current_knowledge_chunks;

select plan(41);

select ok(
  exists (
    select 1
    from pg_extension
    where extname = 'vector'
  ),
  'vector extension is installed for historical semantic retrieval'
);

select has_table('private', 'historical_case_embedding_models', 'historical_case_embedding_models exists');
select has_table('private', 'historical_case_embeddings', 'historical_case_embeddings exists');
select has_view('private', 'current_historical_case_embedding_inputs', 'current_historical_case_embedding_inputs exists');
select has_view('private', 'current_historical_case_embedding_coverage', 'current_historical_case_embedding_coverage exists');

select ok(
  to_regprocedure(
    'private.search_historical_case_units_semantic(extensions.vector,integer,bigint,text,text,text,text,text,boolean,text)'
  ) is not null,
  'search_historical_case_units_semantic function exists'
);

select ok(
  to_regclass('private.historical_case_embeddings_model_unit_lookup_idx') is not null,
  'historical_case_embeddings_model_unit_lookup_idx exists'
);

select is(
  (
    select count(*)::integer
    from private.current_historical_case_embedding_inputs
  ),
  112,
  'all 112 eligible production historical units appear in the embedding input surface'
);

select ok(
  (
    select embedding_input_text like 'Case: %'
       and embedding_input_text like '%Unit type: %'
       and embedding_input_text like '%' || search_text || '%'
    from private.current_historical_case_embedding_inputs
    order by case_code, unit_type, search_unit_id
    limit 1
  ),
  'embedding input text keeps deterministic case context plus governed search text'
);

select lives_ok(
  $sql$
    update private.historical_case_embedding_models
    set is_active = false
    where is_retrieval_approved
      and is_active;

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
    values (
      'fixture_provider',
      'fixture-historical-embedding',
      null,
      3,
      'phase_06_semantic_fixture_v1',
      '{"distance_metric":"cosine","input_contract_code":"phase_06_historical_search_unit_embedding_input_v1"}'::jsonb,
      true,
      true
    );

    insert into private.historical_case_embeddings (
      historical_case_search_unit_id,
      embedding_model_id,
      input_content_hash,
      generated_at,
      embedding
    )
    select
      chcei.search_unit_id,
      hcem.id,
      chcei.embedding_input_hash,
      timezone('utc', now()),
      case
        when chcei.case_code = 'HC-003' and chcei.unit_type = 'decision' then '[1,0,0]'::extensions.vector
        when chcei.case_code = 'HC-003' then '[0.95,0.05,0]'::extensions.vector
        when chcei.case_code = 'HC-009' and chcei.unit_type = 'decision' then '[0,1,0]'::extensions.vector
        when chcei.case_code = 'HC-009' then '[0.05,0.95,0]'::extensions.vector
        when chcei.lesson_kind = 'analyst_inference' then '[0,0,1]'::extensions.vector
        when chcei.case_code = 'HC-006' then '[0.2,0.2,0.6]'::extensions.vector
        else '[0.6,0.4,0]'::extensions.vector
      end
    from private.current_historical_case_embedding_inputs chcei
    cross join (
      select id
      from private.historical_case_embedding_models
      where config_fingerprint = 'phase_06_semantic_fixture_v1'
    ) hcem;
  $sql$,
  'historical semantic fixture model and embeddings load successfully'
);

select is(
  (
    select count(*)::integer
    from private.historical_case_embeddings
    where embedding_model_id = (
      select id
      from private.historical_case_embedding_models
      where config_fingerprint = 'phase_06_semantic_fixture_v1'
    )
  ),
  112,
  'fixture load creates one current embedding per eligible historical unit'
);

select throws_ok(
  $sql$
    insert into private.historical_case_embedding_models (
      provider_code,
      model_code,
      model_version,
      embedding_dimensions,
      config_fingerprint,
      configuration_json
    )
    values (
      'fixture_provider',
      'invalid-dimensions',
      null,
      0,
      'phase_06_invalid_dims',
      '{}'::jsonb
    );
  $sql$,
  '23514',
  null,
  'historical embedding models reject non-positive dimensions'
);

select throws_ok(
  $sql$
    insert into private.historical_case_embedding_models (
      provider_code,
      model_code,
      model_version,
      embedding_dimensions,
      config_fingerprint,
      configuration_json
    )
    values (
      'fixture_provider',
      'fixture-historical-embedding',
      null,
      3,
      'phase_06_semantic_fixture_v1',
      '{"distance_metric":"cosine","input_contract_code":"phase_06_historical_search_unit_embedding_input_v1"}'::jsonb
    );
  $sql$,
  '23505',
  null,
  'duplicate historical embedding model configurations are rejected'
);

select throws_ok(
  $sql$
    insert into private.historical_case_embeddings (
      historical_case_search_unit_id,
      embedding_model_id,
      input_content_hash,
      generated_at,
      embedding
    )
    select
      historical_case_search_unit_id,
      embedding_model_id,
      input_content_hash,
      timezone('utc', now()),
      embedding
    from private.historical_case_embeddings
    where embedding_model_id = (
      select id
      from private.historical_case_embedding_models
      where config_fingerprint = 'phase_06_semantic_fixture_v1'
    )
    order by id
    limit 1;
  $sql$,
  '23505',
  null,
  'duplicate historical unit/model/input embeddings are rejected'
);

select throws_ok(
  $sql$
    insert into private.historical_case_embeddings (
      historical_case_search_unit_id,
      embedding_model_id,
      input_content_hash,
      generated_at,
      embedding
    )
    values (
      999999,
      (select id from private.historical_case_embedding_models where config_fingerprint = 'phase_06_semantic_fixture_v1'),
      'missing_unit',
      timezone('utc', now()),
      '[1,0,0]'::extensions.vector
    );
  $sql$,
  '23503',
  null,
  'historical embeddings reject unknown search units'
);

select throws_ok(
  $sql$
    insert into private.historical_case_embeddings (
      historical_case_search_unit_id,
      embedding_model_id,
      input_content_hash,
      generated_at,
      embedding
    )
    select
      search_unit_id,
      999999,
      embedding_input_hash,
      timezone('utc', now()),
      '[1,0,0]'::extensions.vector
    from private.current_historical_case_embedding_inputs
    order by search_unit_id
    limit 1;
  $sql$,
  '23503',
  null,
  'historical embeddings reject unknown models'
);

select throws_ok(
  $sql$
    insert into private.historical_case_embeddings (
      historical_case_search_unit_id,
      embedding_model_id,
      input_content_hash,
      generated_at,
      embedding
    )
    select
      search_unit_id,
      (select id from private.historical_case_embedding_models where config_fingerprint = 'phase_06_semantic_fixture_v1'),
      'wrong_dimensions',
      timezone('utc', now()),
      '[1,0]'::extensions.vector
    from private.current_historical_case_embedding_inputs
    order by search_unit_id
    limit 1;
  $sql$,
  '23514',
  null,
  'historical embedding insert rejects vector dimension mismatches'
);

select results_eq(
  $sql$
    select
      eligible_unit_count,
      current_embedding_count,
      missing_unit_count,
      stale_unit_count
    from private.current_historical_case_embedding_coverage
  $sql$,
  $sql$
    values (112::bigint, 112::bigint, 0::bigint, 0::bigint)
  $sql$,
  'coverage view reports 112 current embeddings with no missing or stale rows'
);

select ok(
  (
    select count(*)
    from private.search_historical_case_units_semantic('[1,0,0]'::extensions.vector, 10)
  ) > 0,
  'a valid historical semantic query returns results'
);

select is(
  (
    select count(*)
    from private.search_historical_case_units_semantic('[1,0,0]'::extensions.vector, 0)
  ),
  1::bigint,
  'historical semantic result limits are clamped to at least one row'
);

select is(
  (
    with first_run as (
      select array_agg(source_key order by cosine_distance, case_code, unit_type, search_unit_id) as ordered_keys
      from private.search_historical_case_units_semantic('[1,0,0]'::extensions.vector, 10)
    ),
    second_run as (
      select array_agg(source_key order by cosine_distance, case_code, unit_type, search_unit_id) as ordered_keys
      from private.search_historical_case_units_semantic('[1,0,0]'::extensions.vector, 10)
    )
    select (first_run.ordered_keys = second_run.ordered_keys)::integer
    from first_run, second_run
  ),
  1,
  'repeated identical historical semantic queries return the same ordered logical result set'
);

select throws_ok(
  $sql$
    select count(*)
    from private.search_historical_case_units_semantic('[1,0]'::extensions.vector, 10);
  $sql$,
  '23514',
  null,
  'query vectors must match the active historical embedding dimensions'
);

select results_eq(
  $sql$
    select distinct source_layer_role
    from private.search_historical_case_units_semantic('[1,0,0]'::extensions.vector, 10)
  $sql$,
  $sql$
    values ('historical_precedent'::text)
  $sql$,
  'historical semantic search only returns results explicitly identified as historical_precedent'
);

select results_eq(
  $sql$
    select distinct case_code
    from private.search_historical_case_units_semantic('[1,0,0]'::extensions.vector, 10, null, 'hc-003')
  $sql$,
  $sql$
    values ('HC-003'::text)
  $sql$,
  'case_code filtering narrows historical semantic results'
);

select results_eq(
  $sql$
    select distinct unit_type
    from private.search_historical_case_units_semantic('[1,0,0]'::extensions.vector, 10, null, null, 'decision')
  $sql$,
  $sql$
    values ('decision'::text)
  $sql$,
  'unit_type filtering narrows historical semantic results'
);

select results_eq(
  $sql$
    select distinct precedent_availability
    from private.search_historical_case_units_semantic('[1,0,0]'::extensions.vector, 10, null, null, null, 'limited')
  $sql$,
  $sql$
    values ('limited'::text)
  $sql$,
  'limited precedents remain semantically searchable by default and via filters'
);

select results_eq(
  $sql$
    select distinct precedent_type
    from private.search_historical_case_units_semantic('[0,1,0]'::extensions.vector, 10, null, null, null, null, 'cautionary_precedent')
  $sql$,
  $sql$
    values ('cautionary_precedent'::text)
  $sql$,
  'precedent_type filtering narrows historical semantic results'
);

select results_eq(
  $sql$
    select distinct lesson_kind
    from private.search_historical_case_units_semantic('[0,0,1]'::extensions.vector, 10, null, null, null, null, null, 'analyst_inference')
  $sql$,
  $sql$
    values ('analyst_inference'::text)
  $sql$,
  'lesson_kind filtering preserves analyst_inference lessons in semantic retrieval'
);

select results_eq(
  $sql$
    select
      case_code,
      unit_type,
      historical_value_only,
      contamination_risk_level,
      current_authority_disposition
    from private.search_historical_case_units_semantic(
      '[1,0,0]'::extensions.vector,
      1,
      null,
      null,
      'decision',
      null,
      null,
      null,
      true,
      'high'
    )
  $sql$,
  $sql$
    values (
      'HC-003'::text,
      'decision'::text,
      true,
      'high'::text,
      'potential_conflict_with_current_knowledge'::text
    )
  $sql$,
  'historical-value-only and high-risk metadata survive historical semantic retrieval'
);

select ok(
  (
    select
      case_code = 'HC-009'
      and precedent_availability = 'limited'
      and source_layer_role = 'historical_precedent'
      and precedent_type = 'cautionary_precedent'
      and current_authority_disposition is not null
    from private.search_historical_case_units_semantic('[0,1,0]'::extensions.vector, 1)
  ),
  'HC-009 compliance and caution results remain historical, limited, and high-risk'
);

select ok(
  (
    select btrim(primary_source_locator) <> ''
       and source_link_count > 0
    from private.search_historical_case_units_semantic(
      '[1,0,0]'::extensions.vector,
      1,
      null,
      null,
      'decision'
    )
  ),
  'historical semantic results retain provenance through primary source locator and source-link count'
);

select ok(
  (
    select effective_confidentiality_level_code is not null
       and case_personal_information_status is not null
       and source_object_personal_information_status is not null
    from private.search_historical_case_units_semantic('[1,0,0]'::extensions.vector, 1)
  ),
  'historical semantic results retain confidentiality and PI metadata'
);

select throws_ok(
  $sql$
    select count(*)
    from private.search_historical_case_units_semantic('[1,0,0]'::extensions.vector, 10, null, null, 'invalid_unit_type');
  $sql$,
  '22023',
  null,
  'unsupported historical semantic filters are rejected safely'
);

select ok(
  (
    select count(*)
    from private.search_historical_case_units_semantic('[0,0,1]'::extensions.vector, 5)
    where lesson_kind = 'analyst_inference'
  ) > 0,
  'analyst-inference lessons are retrievable through semantic search'
);

select is(
  (
    select count(*)
    from private.current_knowledge_chunks
  ),
  (select chunk_count from phase5_chunk_baseline),
  'Phase 5 current_knowledge_chunks remains unchanged by historical semantic retrieval'
);

select ok(
  to_regprocedure('private.search_knowledge_chunks_semantic(extensions.vector,integer,bigint,text,text,text)') is not null,
  'Phase 5 semantic search function remains present and unchanged'
);

select lives_ok(
  $sql$
    delete from private.historical_case_embeddings
    where historical_case_search_unit_id = (
      select search_unit_id
      from private.current_historical_case_embedding_inputs
      where case_code = 'HC-002'
      order by search_unit_id
      limit 1
    )
      and embedding_model_id = (
        select id
        from private.historical_case_embedding_models
        where config_fingerprint = 'phase_06_semantic_fixture_v1'
      );

    insert into private.historical_case_embeddings (
      historical_case_search_unit_id,
      embedding_model_id,
      input_content_hash,
      generated_at,
      embedding
    )
    values (
      (
        select search_unit_id
        from private.current_historical_case_embedding_inputs
        where case_code = 'HC-002'
        order by search_unit_id
        limit 1
      ),
      (
        select id
        from private.historical_case_embedding_models
        where config_fingerprint = 'phase_06_semantic_fixture_v1'
      ),
      'stale_phase_06_fixture_hash',
      timezone('utc', now()),
      '[0.4,0.4,0.2]'::extensions.vector
    );
  $sql$,
  'fixture mutation can create a stale historical embedding without changing governed active content'
);

select results_eq(
  $sql$
    select
      current_embedding_count,
      missing_unit_count,
      stale_unit_count
    from private.current_historical_case_embedding_coverage
  $sql$,
  $sql$
    values (111::bigint, 1::bigint, 1::bigint)
  $sql$,
  'coverage view detects stale and missing embeddings when the current fingerprint no longer matches'
);

select throws_ok(
  $sql$
    set local role anon;
    select count(*) from private.search_historical_case_units_semantic('[1,0,0]'::extensions.vector, 10);
    reset role;
  $sql$,
  '42501',
  null,
  'anon cannot execute the private historical semantic function'
);

select throws_ok(
  $sql$
    set local role authenticated;
    select count(*) from private.search_historical_case_units_semantic('[1,0,0]'::extensions.vector, 10);
    reset role;
  $sql$,
  '42501',
  null,
  'authenticated cannot execute the private historical semantic function'
);

select throws_ok(
  $sql$
    set local role service_role;
    select count(*) from private.search_historical_case_units_semantic('[1,0,0]'::extensions.vector, 10);
    reset role;
  $sql$,
  '42501',
  null,
  'service_role cannot execute the private historical semantic function'
);

select * from finish();

rollback;
