begin;

create extension if not exists pgtap with schema extensions;
set local search_path to private, public, api, extensions;

create temp table phase5_chunk_baseline as
select count(*)::bigint as chunk_count
from private.current_knowledge_chunks;

select plan(31);

select ok(
  exists (
    select 1
    from information_schema.columns
    where table_schema = 'private'
      and table_name = 'historical_case_search_units'
      and column_name = 'search_vector'
  ),
  'historical_case_search_units.search_vector exists'
);

select ok(
  to_regclass('private.historical_case_search_units_search_vector_gin_idx') is not null,
  'historical_case_search_units_search_vector_gin_idx exists'
);

select ok(
  to_regprocedure(
    'private.search_historical_case_units(text,integer,text,text,text,text,text,boolean,text)'
  ) is not null,
  'search_historical_case_units function exists'
);

select is(
  (
    select count(*)
    from private.historical_case_search_units hcsu
    join private.current_historical_case_search_units chcsu
      on chcsu.search_unit_id = hcsu.id
    where hcsu.search_vector is not null
      and hcsu.search_vector::text <> ''
  ),
  112::bigint,
  'all 112 eligible production historical search units are FTS-ready'
);

select ok(
  (
    select count(*)
    from private.search_historical_case_units('external storage', 10)
  ) > 0,
  'a valid lexical historical query returns results'
);

select is(
  (
    select count(*)
    from private.search_historical_case_units('', 10)
  ),
  0::bigint,
  'empty historical queries return zero results'
);

select is(
  (
    select count(*)
    from private.search_historical_case_units('   ', 10)
  ),
  0::bigint,
  'whitespace-only historical queries return zero results'
);

select is(
  (
    select count(*)
    from private.search_historical_case_units(null, 10)
  ),
  0::bigint,
  'null historical queries return zero results'
);

select is(
  (
    select count(*)
    from private.search_historical_case_units('storage', 0)
  ),
  1::bigint,
  'historical result limits are clamped to at least one row'
);

select is(
  (
    with first_run as (
      select array_agg(source_key order by lexical_score desc, case_code, unit_type, search_unit_id) as ordered_keys
      from private.search_historical_case_units('storage', 10)
    ),
    second_run as (
      select array_agg(source_key order by lexical_score desc, case_code, unit_type, search_unit_id) as ordered_keys
      from private.search_historical_case_units('storage', 10)
    )
    select (first_run.ordered_keys = second_run.ordered_keys)::integer
    from first_run, second_run
  ),
  1,
  'repeated identical historical queries return the same ordered logical result set'
);

select results_eq(
  $sql$
    select distinct source_layer_role
    from private.search_historical_case_units('storage', 10)
  $sql$,
  $sql$
    values ('historical_precedent'::text)
  $sql$,
  'historical FTS only returns results explicitly identified as historical_precedent'
);

select results_eq(
  $sql$
    select case_code, unit_type
    from private.search_historical_case_units('A useful precedent for full white-box handover', 1)
  $sql$,
  $sql$
    values ('HC-001'::text, 'case_narrative'::text)
  $sql$,
  'case_narrative units are lexically searchable'
);

select results_eq(
  $sql$
    select case_code, unit_type
    from private.search_historical_case_units('The client provided the wine for the reception.', 1)
  $sql$,
  $sql$
    values ('HC-005'::text, 'responsibility'::text)
  $sql$,
  'responsibility units are lexically searchable'
);

select results_eq(
  $sql$
    select case_code, unit_type
    from private.search_historical_case_units('additional WNC staffing or overtime should apply', 1)
  $sql$,
  $sql$
    values ('HC-006'::text, 'decision'::text)
  $sql$,
  'decision units are lexically searchable'
);

select results_eq(
  $sql$
    select case_code, unit_type
    from private.search_historical_case_units('grace period does not equal setup time', 1)
  $sql$,
  $sql$
    values ('HC-007'::text, 'lesson'::text)
  $sql$,
  'lesson units are lexically searchable'
);

select results_eq(
  $sql$
    select case_code, precedent_availability
    from private.search_historical_case_units('floral arrangement support', 1)
  $sql$,
  $sql$
    values ('HC-003'::text, 'limited'::text)
  $sql$,
  'limited precedents are included by default in historical lexical search'
);

select is(
  (
    select count(*)
    from private.search_historical_case_units(
      'floral arrangement support',
      10,
      null,
      null,
      'active'
    )
  ),
  0::bigint,
  'precedent_availability filter can exclude limited historical precedents'
);

select results_eq(
  $sql$
    select distinct case_code
    from private.search_historical_case_units('storage', 10, 'hc-003')
  $sql$,
  $sql$
    values ('HC-003'::text)
  $sql$,
  'case_code filtering narrows historical results'
);

select results_eq(
  $sql$
    select distinct unit_type
    from private.search_historical_case_units('storage', 10, null, 'decision')
  $sql$,
  $sql$
    values ('decision'::text)
  $sql$,
  'unit_type filtering narrows historical results'
);

select results_eq(
  $sql$
    select distinct precedent_type
    from private.search_historical_case_units(
      'current legal precedent',
      10,
      null,
      null,
      null,
      'cautionary_precedent'
    )
  $sql$,
  $sql$
    values ('cautionary_precedent'::text)
  $sql$,
  'precedent_type filtering narrows historical results'
);

select results_eq(
  $sql$
    select distinct lesson_kind
    from private.search_historical_case_units(
      'Later modelling may need',
      10,
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
  'lesson_kind filtering preserves analyst_inference lessons'
);

select results_eq(
  $sql$
    select
      case_code,
      unit_type,
      historical_value_only,
      contamination_risk_level,
      current_authority_disposition
    from private.search_historical_case_units(
      '300 storage',
      1,
      null,
      null,
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
  'historical-value-only and high-risk metadata survive historical FTS'
);

select results_eq(
  $sql$
    select distinct contamination_risk_level
    from private.search_historical_case_units(
      'fake snow',
      10,
      null,
      null,
      null,
      null,
      null,
      null,
      'high'
    )
  $sql$,
  $sql$
    values ('high'::text)
  $sql$,
  'contamination_risk_level filtering narrows historical results'
);

select results_eq(
  $sql$
    select
      case_code,
      precedent_availability,
      lesson_kind,
      historical_value_only,
      contamination_risk_level
    from private.search_historical_case_units('current legal precedent', 1)
  $sql$,
  $sql$
    values (
      'HC-009'::text,
      'limited'::text,
      null::text,
      true,
      'high'::text
    )
  $sql$,
  'HC-009 cautionary precedent remains searchable with limited and high-risk metadata visible'
);

select ok(
  (
    select btrim(primary_source_locator) <> ''
    from private.search_historical_case_units('external storage', 1)
  ),
  'historical FTS results retain a non-empty primary source locator'
);

select ok(
  (
    select effective_confidentiality_level_code is not null
       and case_personal_information_status is not null
       and source_object_personal_information_status is not null
    from private.search_historical_case_units('unbranded equipment', 1)
  ),
  'historical FTS results retain confidentiality and PI metadata'
);

select throws_ok(
  $sql$
    select count(*)
    from private.search_historical_case_units('storage', 10, null, 'invalid_unit_type');
  $sql$,
  '22023',
  null,
  'unsupported historical filters are rejected safely'
);

select is(
  (
    select count(*)
    from private.current_knowledge_chunks
  ),
  (select chunk_count from phase5_chunk_baseline),
  'Phase 5 current_knowledge_chunks remains unchanged by historical FTS'
);

select throws_ok(
  $sql$
    set local role anon;
    select count(*) from private.search_historical_case_units('storage', 10);
    reset role;
  $sql$,
  '42501',
  null,
  'anon cannot execute the private historical FTS function'
);

select throws_ok(
  $sql$
    set local role authenticated;
    select count(*) from private.search_historical_case_units('storage', 10);
    reset role;
  $sql$,
  '42501',
  null,
  'authenticated cannot execute the private historical FTS function'
);

select throws_ok(
  $sql$
    set local role service_role;
    select count(*) from private.search_historical_case_units('storage', 10);
    reset role;
  $sql$,
  '42501',
  null,
  'service_role cannot execute the private historical FTS function'
);

select * from finish();

rollback;
