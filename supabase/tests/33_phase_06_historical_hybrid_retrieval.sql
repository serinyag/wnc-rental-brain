begin;

create extension if not exists pgtap with schema extensions;
set local search_path to private, public, api, extensions;

create temp table phase5_chunk_baseline as
select count(*)::bigint as chunk_count
from private.current_knowledge_chunks;

select plan(32);

select has_function(
  'private',
  'historical_hybrid_rrf_score',
  array['integer', 'integer'],
  'historical_hybrid_rrf_score helper exists'
);

select has_function(
  'private',
  'search_historical_case_units_hybrid',
  array['text', 'extensions.vector', 'integer', 'integer', 'bigint', 'text', 'text', 'text', 'text', 'text', 'text', 'boolean', 'text'],
  'private historical hybrid retrieval function exists'
);

select is(
  private.historical_hybrid_rrf_score(1, 20)::numeric(12,9),
  (1::numeric / 21::numeric)::numeric(12,9),
  'historical RRF helper uses the approved reciprocal-rank formula'
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
      'fixture-historical-hybrid-embedding',
      null,
      3,
      'phase_06_hybrid_fixture_v1',
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
        when chcei.case_code = 'HC-003' then '[0.97,0.03,0]'::extensions.vector
        when chcei.case_code = 'HC-009' and chcei.unit_type = 'decision' then '[0,1,0]'::extensions.vector
        when chcei.case_code = 'HC-009' then '[0.03,0.97,0]'::extensions.vector
        when chcei.lesson_kind = 'analyst_inference' then '[0,0,1]'::extensions.vector
        when chcei.case_code = 'HC-001' then '[0.85,0.05,0.10]'::extensions.vector
        when chcei.case_code = 'HC-006' then '[0.60,0.10,0.30]'::extensions.vector
        else '[0.40,0.40,0.20]'::extensions.vector
      end
    from private.current_historical_case_embedding_inputs chcei
    cross join (
      select id
      from private.historical_case_embedding_models
      where config_fingerprint = 'phase_06_hybrid_fixture_v1'
    ) hcem;
  $sql$,
  'historical hybrid fixture model and embeddings load successfully'
);

select ok(
  (
    select count(*)
    from private.search_historical_case_units_hybrid(
      'external storage',
      '[1,0,0]'::extensions.vector,
      10,
      10
    )
  ) > 0,
  'a valid historical hybrid query returns results'
);

select is(
  (
    select count(*)
    from private.search_historical_case_units_hybrid(
      'external storage',
      '[1,0,0]'::extensions.vector,
      0,
      10
    )
  ),
  1::bigint,
  'historical hybrid result limits are clamped to at least one row'
);

select is(
  (
    with first_run as (
      select array_agg(source_key order by hybrid_score desc, best_component_rank, case_code, unit_type, search_unit_id) as ordered_keys
      from private.search_historical_case_units_hybrid(
        'external storage',
        '[1,0,0]'::extensions.vector,
        10,
        10
      )
    ),
    second_run as (
      select array_agg(source_key order by hybrid_score desc, best_component_rank, case_code, unit_type, search_unit_id) as ordered_keys
      from private.search_historical_case_units_hybrid(
        'external storage',
        '[1,0,0]'::extensions.vector,
        10,
        10
      )
    )
    select (first_run.ordered_keys = second_run.ordered_keys)::integer
    from first_run, second_run
  ),
  1,
  'repeated identical historical hybrid queries return the same ordered logical result set'
);

select ok(
  (
    with hybrid_rows as (
      select search_unit_id
      from private.search_historical_case_units_hybrid(
        'external storage',
        '[1,0,0]'::extensions.vector,
        10,
        10
      )
    )
    select count(*) = count(distinct search_unit_id)
    from hybrid_rows
  ),
  'duplicate search units are removed during historical hybrid fusion'
);

select ok(
  (
    select
      came_from_fts
      and came_from_semantic
      and fts_rank is not null
      and semantic_rank is not null
      and hybrid_score = rrf_fts_score + rrf_semantic_score
    from private.search_historical_case_units_hybrid(
      'external storage',
      '[1,0,0]'::extensions.vector,
      10,
      10
    )
    where case_code = 'HC-003'
      and unit_type = 'decision'
    limit 1
  ),
  'a candidate present in both historical lists receives both RRF contributions'
);

select ok(
  (
    select exists (
      select 1
      from private.search_historical_case_units_hybrid(
        'current legal precedent',
        '[1,0,0]'::extensions.vector,
        5,
        1
      )
      where case_code = 'HC-009'
        and came_from_fts
        and not came_from_semantic
    )
  ),
  'FTS-only historical candidates survive hybrid fusion'
);

select ok(
  (
    select exists (
      select 1
      from private.search_historical_case_units_hybrid(
        'current legal precedent',
        '[1,0,0]'::extensions.vector,
        5,
        1
      )
      where case_code = 'HC-003'
        and not came_from_fts
        and came_from_semantic
    )
  ),
  'semantic-only historical candidates survive hybrid fusion'
);

select ok(
  (
    select bool_and(
      hybrid_score is not null
      and (fts_rank is not null or semantic_rank is not null)
      and lexical_weight is not null
      and semantic_weight is not null
      and rrf_k = 20
    )
    from private.search_historical_case_units_hybrid(
      'external storage',
      '[1,0,0]'::extensions.vector,
      10,
      10
    )
  ),
  'hybrid results expose explainable component ranks and score diagnostics'
);

select results_eq(
  $sql$
    select distinct source_layer_role
    from private.search_historical_case_units_hybrid(
      'external storage',
      '[1,0,0]'::extensions.vector,
      10,
      10
    )
  $sql$,
  $sql$
    values ('historical_precedent'::text)
  $sql$,
  'historical hybrid retrieval returns only explicit historical_precedent rows'
);

select results_eq(
  $sql$
    select distinct case_code
    from private.search_historical_case_units_hybrid(
      'external storage',
      '[1,0,0]'::extensions.vector,
      10,
      10,
      null,
      'historical_rrf_balanced',
      'hc-003'
    )
  $sql$,
  $sql$
    values ('HC-003'::text)
  $sql$,
  'case_code filtering preserves parity in hybrid retrieval'
);

select results_eq(
  $sql$
    select distinct unit_type
    from private.search_historical_case_units_hybrid(
      'external storage',
      '[1,0,0]'::extensions.vector,
      10,
      10,
      null,
      'historical_rrf_balanced',
      null,
      'decision'
    )
  $sql$,
  $sql$
    values ('decision'::text)
  $sql$,
  'unit_type filtering preserves parity in hybrid retrieval'
);

select results_eq(
  $sql$
    select distinct precedent_availability
    from private.search_historical_case_units_hybrid(
      'floral arrangement support',
      '[1,0,0]'::extensions.vector,
      10,
      10,
      null,
      'historical_rrf_balanced',
      null,
      null,
      'limited'
    )
  $sql$,
  $sql$
    values ('limited'::text)
  $sql$,
  'precedent_availability filtering preserves parity in hybrid retrieval'
);

select results_eq(
  $sql$
    select distinct precedent_type
    from private.search_historical_case_units_hybrid(
      'current legal precedent',
      '[0,1,0]'::extensions.vector,
      10,
      10,
      null,
      'historical_rrf_balanced',
      null,
      null,
      null,
      'cautionary_precedent'
    )
  $sql$,
  $sql$
    values ('cautionary_precedent'::text)
  $sql$,
  'precedent_type filtering preserves parity in hybrid retrieval'
);

select results_eq(
  $sql$
    select distinct lesson_kind
    from private.search_historical_case_units_hybrid(
      'semantic only analyst lesson',
      '[0,0,1]'::extensions.vector,
      10,
      10,
      null,
      'historical_rrf_balanced',
      null,
      null,
      null,
      null,
      'analyst_inference'
    )
  $sql$,
  $sql$
    values ('analyst_inference'::text)
  $sql$,
  'lesson_kind filtering preserves analyst_inference rows in hybrid retrieval'
);

select results_eq(
  $sql$
    select
      case_code,
      unit_type,
      historical_value_only,
      contamination_risk_level,
      current_authority_disposition
    from private.search_historical_case_units_hybrid(
      '300 storage',
      '[1,0,0]'::extensions.vector,
      1,
      10,
      null,
      'historical_rrf_balanced',
      'hc-003',
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
  'historical-value-only and high-risk metadata survive hybrid retrieval'
);

select results_eq(
  $sql$
    select
      case_code,
      precedent_availability,
      source_layer_role
    from private.search_historical_case_units_hybrid(
      'current legal precedent',
      '[0,1,0]'::extensions.vector,
      1,
      10
    )
  $sql$,
  $sql$
    values (
      'HC-009'::text,
      'limited'::text,
      'historical_precedent'::text
    )
  $sql$,
  'HC-009 compliance and caution results remain limited and historical under hybrid retrieval'
);

select ok(
  (
    select btrim(primary_source_locator) <> ''
       and source_link_count > 0
    from private.search_historical_case_units_hybrid(
      'external storage',
      '[1,0,0]'::extensions.vector,
      1,
      10
    )
  ),
  'historical hybrid results retain provenance through primary source locator and source-link count'
);

select ok(
  (
    select effective_confidentiality_level_code is not null
       and case_personal_information_status is not null
       and source_object_personal_information_status is not null
    from private.search_historical_case_units_hybrid(
      'external storage',
      '[1,0,0]'::extensions.vector,
      1,
      10
    )
  ),
  'historical hybrid results retain confidentiality and PI metadata'
);

select ok(
  (
    select count(*) > 0
    from private.search_historical_case_units_hybrid(
      'floral arrangement support',
      '[1,0,0]'::extensions.vector,
      10,
      10
    )
    where precedent_availability = 'limited'
  ),
  'limited precedents remain searchable by default in hybrid retrieval'
);

select ok(
  (
    select count(*) > 0
    from private.search_historical_case_units_hybrid(
      'semantic only analyst lesson',
      '[0,0,1]'::extensions.vector,
      10,
      10
    )
    where lesson_kind = 'analyst_inference'
  ),
  'analyst-inference metadata remains searchable in hybrid retrieval'
);

select throws_ok(
  $sql$
    select count(*)
    from private.search_historical_case_units_hybrid(
      'external storage',
      '[1,0,0]'::extensions.vector,
      10,
      10,
      null,
      'invalid_strategy'
    );
  $sql$,
  '22023',
  null,
  'unsupported historical hybrid strategy codes are rejected safely'
);

select throws_ok(
  $sql$
    select count(*)
    from private.search_historical_case_units_hybrid(
      'external storage',
      '[1,0]'::extensions.vector,
      10,
      10
    );
  $sql$,
  '23514',
  null,
  'query vectors must match the active historical embedding dimensions in hybrid retrieval'
);

select is(
  (
    select count(*)
    from private.current_knowledge_chunks
  ),
  (select chunk_count from phase5_chunk_baseline),
  'Phase 5 current_knowledge_chunks remains unchanged by historical hybrid retrieval'
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
        where config_fingerprint = 'phase_06_hybrid_fixture_v1'
      );
  $sql$,
  'fixture mutation can create incomplete historical semantic state for hybrid precondition coverage'
);

select throws_ok(
  $sql$
    select count(*)
    from private.search_historical_case_units_hybrid(
      'external storage',
      '[1,0,0]'::extensions.vector,
      10,
      10
    );
  $sql$,
  'P0001',
  null,
  'hybrid retrieval refuses to run when the historical embedding set is incomplete'
);

select throws_ok(
  $sql$
    set local role anon;
    select count(*)
    from private.search_historical_case_units_hybrid(
      'external storage',
      '[1,0,0]'::extensions.vector,
      10,
      10
    );
    reset role;
  $sql$,
  '42501',
  null,
  'anon cannot execute the private historical hybrid function'
);

select throws_ok(
  $sql$
    set local role authenticated;
    select count(*)
    from private.search_historical_case_units_hybrid(
      'external storage',
      '[1,0,0]'::extensions.vector,
      10,
      10
    );
    reset role;
  $sql$,
  '42501',
  null,
  'authenticated cannot execute the private historical hybrid function'
);

select throws_ok(
  $sql$
    set local role service_role;
    select count(*)
    from private.search_historical_case_units_hybrid(
      'external storage',
      '[1,0,0]'::extensions.vector,
      10,
      10
    );
    reset role;
  $sql$,
  '42501',
  null,
  'service_role cannot execute the private historical hybrid function'
);

select * from finish();

rollback;
