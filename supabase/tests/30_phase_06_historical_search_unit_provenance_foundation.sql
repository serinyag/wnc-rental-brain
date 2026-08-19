begin;

create extension if not exists pgtap with schema extensions;
set local search_path to private, public, api, extensions;

create temp table phase5_chunk_baseline as
select count(*)::bigint as chunk_count
from private.current_knowledge_chunks;

select plan(26);

select ok(
  to_regclass('private.historical_case_version_processing') is not null,
  'historical_case_version_processing table exists'
);

select ok(
  to_regclass('private.historical_case_search_units') is not null,
  'historical_case_search_units table exists'
);

select ok(
  to_regclass('private.historical_case_unit_sources') is not null,
  'historical_case_unit_sources table exists'
);

select ok(
  to_regclass('private.current_historical_case_search_units') is not null,
  'current_historical_case_search_units view exists'
);

select throws_ok(
  $sql$
    insert into private.historical_case_search_units (
      source_key,
      historical_case_version_id,
      historical_case_id,
      source_layer_role,
      unit_type,
      case_code_snapshot,
      case_title_snapshot,
      precedent_type_snapshot,
      precedent_availability_snapshot,
      case_evidence_strength_snapshot,
      case_contains_historical_value_only_content,
      case_personal_information_status,
      source_object_personal_information_status,
      effective_confidentiality_level_id,
      unit_evidence_strength,
      search_text,
      generation_strategy_code,
      generation_strategy_version,
      generated_at
    )
    select
      'invalid_type_test',
      hcv.id,
      hc.id,
      'historical_precedent',
      'invalid_type',
      hc.case_code,
      hc.canonical_title,
      hcv.precedent_type,
      hcv.precedent_availability,
      hcv.evidence_strength,
      hcv.contains_historical_value_only_content,
      hcv.personal_information_status,
      'yes',
      hcv.confidentiality_level_id,
      hcv.evidence_strength,
      'Invalid unit type test payload',
      'phase_6_governed_search_units',
      '6.4A_v1',
      timezone('utc', now())
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-001'
      and hcv.version_number = 1;
  $sql$,
  '23514',
  null,
  'invalid historical search-unit types are rejected'
);

select results_eq(
  $sql$
    select unit_type
    from private.current_historical_case_search_units
    group by unit_type
    order by unit_type
  $sql$,
  $sql$
    values
      ('case_narrative'::text),
      ('decision'::text),
      ('lesson'::text),
      ('responsibility'::text)
  $sql$,
  'the current historical search surface exposes exactly the four governed unit types'
);

select results_eq(
  $sql$
    select case_code, unit_type, count(*)::bigint
    from private.current_historical_case_search_units
    group by case_code, unit_type
    order by case_code, unit_type
  $sql$,
  $sql$
    values
      ('HC-001'::text, 'case_narrative'::text, 1::bigint),
      ('HC-001'::text, 'decision'::text, 3::bigint),
      ('HC-001'::text, 'lesson'::text, 5::bigint),
      ('HC-001'::text, 'responsibility'::text, 3::bigint),
      ('HC-002'::text, 'case_narrative'::text, 1::bigint),
      ('HC-002'::text, 'decision'::text, 3::bigint),
      ('HC-002'::text, 'lesson'::text, 5::bigint),
      ('HC-002'::text, 'responsibility'::text, 5::bigint),
      ('HC-003'::text, 'case_narrative'::text, 1::bigint),
      ('HC-003'::text, 'decision'::text, 3::bigint),
      ('HC-003'::text, 'lesson'::text, 7::bigint),
      ('HC-003'::text, 'responsibility'::text, 7::bigint),
      ('HC-004'::text, 'case_narrative'::text, 1::bigint),
      ('HC-004'::text, 'decision'::text, 3::bigint),
      ('HC-004'::text, 'lesson'::text, 5::bigint),
      ('HC-004'::text, 'responsibility'::text, 3::bigint),
      ('HC-005'::text, 'case_narrative'::text, 1::bigint),
      ('HC-005'::text, 'decision'::text, 3::bigint),
      ('HC-005'::text, 'lesson'::text, 4::bigint),
      ('HC-005'::text, 'responsibility'::text, 5::bigint),
      ('HC-006'::text, 'case_narrative'::text, 1::bigint),
      ('HC-006'::text, 'decision'::text, 3::bigint),
      ('HC-006'::text, 'lesson'::text, 6::bigint),
      ('HC-006'::text, 'responsibility'::text, 4::bigint),
      ('HC-007'::text, 'case_narrative'::text, 1::bigint),
      ('HC-007'::text, 'decision'::text, 3::bigint),
      ('HC-007'::text, 'lesson'::text, 5::bigint),
      ('HC-007'::text, 'responsibility'::text, 4::bigint),
      ('HC-008'::text, 'case_narrative'::text, 1::bigint),
      ('HC-008'::text, 'decision'::text, 2::bigint),
      ('HC-008'::text, 'lesson'::text, 3::bigint),
      ('HC-008'::text, 'responsibility'::text, 3::bigint),
      ('HC-009'::text, 'case_narrative'::text, 1::bigint),
      ('HC-009'::text, 'decision'::text, 2::bigint),
      ('HC-009'::text, 'lesson'::text, 3::bigint),
      ('HC-009'::text, 'responsibility'::text, 1::bigint)
  $sql$,
  'all nine active production cases materialize the expected unit counts by case and type'
);

select results_eq(
  $sql$
    select unit_type, count(*)::bigint
    from private.current_historical_case_search_units
    group by unit_type
    order by unit_type
  $sql$,
  $sql$
    values
      ('case_narrative'::text, 9::bigint),
      ('decision'::text, 25::bigint),
      ('lesson'::text, 43::bigint),
      ('responsibility'::text, 35::bigint)
  $sql$,
  'production unit totals follow the one-governed-row-per-unit model'
);

select is(
  (
    select count(*)
    from private.current_historical_case_search_units
  ),
  112::bigint,
  'the active production historical corpus materializes 112 current search units'
);

select results_eq(
  $sql$
    select search_unit_generation_status, count(*)::bigint
    from private.historical_case_version_processing
    group by search_unit_generation_status
    order by search_unit_generation_status
  $sql$,
  $sql$
    values
      ('succeeded'::text, 9::bigint)
  $sql$,
  'active production case versions record succeeded search-unit processing state'
);

select is(
  (
    select count(distinct source_key)
    from private.current_historical_case_search_units
  ),
  112::bigint,
  'production historical search units keep a stable one-to-one logical source identity'
);

select results_eq(
  $sql$
    select
      count(*)::bigint as total_units,
      count(*) filter (
        where exists (
          select 1
          from private.historical_case_unit_sources hcus
          where hcus.historical_case_search_unit_id = hcsu.search_unit_id
        )
      )::bigint as units_with_lineage,
      count(*) filter (
        where not exists (
          select 1
          from private.historical_case_unit_sources hcus
          where hcus.historical_case_search_unit_id = hcsu.search_unit_id
        )
      )::bigint as units_missing_lineage
    from private.current_historical_case_search_units hcsu
  $sql$,
  $sql$
    values
      (112::bigint, 112::bigint, 0::bigint)
  $sql$,
  'every production historical search unit has provenance lineage and none are missing lineage'
);

select results_eq(
  $sql$
    select case_code, count(*)::bigint
    from private.current_historical_case_search_units
    where precedent_availability = 'limited'
    group by case_code
    order by case_code
  $sql$,
  $sql$
    values
      ('HC-003'::text, 18::bigint),
      ('HC-004'::text, 12::bigint),
      ('HC-008'::text, 9::bigint),
      ('HC-009'::text, 7::bigint)
  $sql$,
  'limited precedents remain included in the current historical search surface and stay distinguishable by case'
);

select lives_ok(
  $sql$
    do $$
    declare
      internal_confidentiality_id bigint;
      curated_role_id bigint;
      case_id bigint;
      version_id bigint;
      source_object_id bigint;
      fixture_codes text[] := array['HC-960', 'HC-961', 'HC-962', 'HC-963', 'HC-964'];
      fixture_titles text[] := array[
        'Held Availability Fixture',
        'Archived Availability Fixture',
        'Draft Governance Fixture',
        'Superseded Governance Fixture',
        'Retired Governance Fixture'
      ];
      fixture_statuses text[] := array['active', 'active', 'draft', 'superseded', 'retired'];
      fixture_availability text[] := array['held', 'archived', 'active', 'active', 'active'];
      fixture_index integer;
    begin
      select id into internal_confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      select id into curated_role_id
      from public.historical_case_evidence_roles
      where role_code = 'curated_case_library_source';

      for fixture_index in 1 .. array_length(fixture_codes, 1) loop
        insert into public.historical_cases (
          case_code,
          canonical_title
        )
        values (
          fixture_codes[fixture_index],
          fixture_titles[fixture_index]
        )
        returning id into case_id;

        insert into public.historical_case_versions (
          historical_case_id,
          version_number,
          governance_status,
          precedent_availability,
          precedent_type,
          evidence_strength,
          historical_event_status,
          temporal_precision,
          curated_narrative,
          confidentiality_level_id,
          personal_information_status,
          contains_historical_value_only_content,
          activated_at
        )
        values (
          case_id,
          1,
          'draft',
          fixture_availability[fixture_index],
          'full_case',
          'moderate',
          'completed',
          'unknown',
          fixture_titles[fixture_index] || ' narrative',
          internal_confidentiality_id,
          'no',
          false,
          null
        )
        returning id into version_id;

        insert into public.knowledge_source_objects (
          origin_type,
          manual_reference_key,
          personal_information_status
        )
        values (
          'manual_reference',
          'P6-4A-FIXTURE-' || fixture_codes[fixture_index],
          'no'
        )
        returning id into source_object_id;

        insert into public.historical_case_version_source_objects (
          historical_case_version_id,
          source_object_id,
          evidence_role_id,
          confidentiality_level_id,
          evidence_strength,
          source_locator,
          supported_claim_dimensions,
          relationship_notes
        )
        values (
          version_id,
          source_object_id,
          curated_role_id,
          internal_confidentiality_id,
          'moderate',
          fixture_titles[fixture_index] || ' source locator',
          array['identity', 'context']::text[],
          'Fixture lineage for 6.4A exclusion testing.'
        );

        if fixture_statuses[fixture_index] = 'superseded' then
          update public.historical_case_versions
          set governance_status = 'active',
              activated_at = timezone('utc', now())
          where id = version_id;

          update public.historical_case_versions
          set governance_status = 'superseded'
          where id = version_id;
        else
          update public.historical_case_versions
          set governance_status = fixture_statuses[fixture_index],
              activated_at = case
                when fixture_statuses[fixture_index] in ('active', 'retired')
                  then timezone('utc', now())
                else null
              end
          where id = version_id;
        end if;
      end loop;

      perform private.rebuild_current_historical_case_search_units();
    end
    $$;
  $sql$,
  'held, archived, draft, superseded, and retired fixture cases can coexist with a rebuild safely'
);

select is(
  (
    select count(*)
    from private.historical_case_search_units hcsu
    where hcsu.case_code_snapshot in ('HC-960', 'HC-961', 'HC-962', 'HC-963', 'HC-964')
  ),
  0::bigint,
  'held, archived, draft, superseded, and retired fixtures do not materialize current historical search units'
);

select results_eq(
  $sql$
    select
      unit_type,
      precedent_availability,
      historical_value_only,
      contamination_risk_level,
      current_authority_disposition
    from private.current_historical_case_search_units
    where case_code = 'HC-003'
      and search_text = 'External bike-storage / hallway storage was hired for EUR 300 for the day.'
  $sql$,
  $sql$
    values
      ('decision'::text, 'limited'::text, true, 'high'::text, 'potential_conflict_with_current_knowledge'::text)
  $sql$,
  'HC-003 high-risk historical decision units preserve limited availability and contamination metadata'
);

select results_eq(
  $sql$
    select lesson_kind, precedent_availability
    from private.current_historical_case_search_units
    where case_code = 'HC-009'
      and search_text = 'Historical compliance solutions must not be reused without current legal checking.'
  $sql$,
  $sql$
    values
      ('caution_warning'::text, 'limited'::text)
  $sql$,
  'HC-009 caution units preserve caution_warning identity and limited availability'
);

select is(
  (
    select count(*)
    from private.current_historical_case_search_units
    where unit_type = 'lesson'
      and lesson_kind = 'analyst_inference'
  ),
  8::bigint,
  'analyst-inference lesson units remain separately identifiable'
);

select is(
  (
    select count(*)
    from private.historical_case_unit_sources hcus
    join private.historical_case_search_units hcsu
      on hcsu.id = hcus.historical_case_search_unit_id
    join public.historical_case_version_source_objects hcvso
      on hcvso.id = hcus.historical_case_version_source_object_id
    join public.knowledge_source_objects kso
      on kso.id = hcvso.source_object_id
    where hcsu.case_code_snapshot between 'HC-001' and 'HC-009'
      and btrim(hcvso.source_locator) <> ''
  ),
  112::bigint,
  'every production unit lineage resolves through a case-version evidence association to a source object and non-empty source locator'
);

select throws_ok(
  $sql$
    insert into private.historical_case_unit_sources (
      historical_case_search_unit_id,
      historical_case_version_source_object_id,
      is_primary_trace
    )
    values (
      (
        select hcsu.id
        from private.historical_case_search_units hcsu
        where hcsu.case_code_snapshot = 'HC-001'
          and hcsu.unit_type = 'case_narrative'
      ),
      (
        select hcvso.id
        from public.historical_case_version_source_objects hcvso
        join public.historical_case_versions hcv
          on hcv.id = hcvso.historical_case_version_id
        join public.historical_cases hc
          on hc.id = hcv.historical_case_id
        where hc.case_code = 'HC-002'
        limit 1
      ),
      false
    );
  $sql$,
  '23514',
  null,
  'cross-case evidence lineage cannot be attached to a historical search unit'
);

select results_eq(
  $sql$
    select
      case_code,
      unit_type,
      effective_confidentiality_level_code,
      case_personal_information_status,
      source_object_personal_information_status
    from private.current_historical_case_search_units
    where (case_code, unit_type) in (
      ('HC-003'::text, 'case_narrative'::text),
      ('HC-004'::text, 'case_narrative'::text),
      ('HC-008'::text, 'case_narrative'::text)
    )
    order by case_code
  $sql$,
  $sql$
    values
      ('HC-003'::text, 'case_narrative'::text, 'restricted'::text, 'yes'::text, 'yes'::text),
      ('HC-004'::text, 'case_narrative'::text, 'restricted'::text, 'no'::text, 'yes'::text),
      ('HC-008'::text, 'case_narrative'::text, 'commercially_sensitive'::text, 'no'::text, 'yes'::text)
  $sql$,
  'derived units preserve effective confidentiality and separate case-versus-source PI metadata'
);

select is(
  (
    select count(*)
    from private.current_knowledge_chunks
  ),
  (select chunk_count from phase5_chunk_baseline),
  'Phase 5 current_knowledge_chunks remains unchanged by historical search-unit generation'
);

select throws_ok(
  $sql$
    set local role anon;
    select count(*) from private.current_historical_case_search_units;
    reset role;
  $sql$,
  '42501',
  null,
  'anon cannot read private current historical search units directly'
);

select throws_ok(
  $sql$
    set local role authenticated;
    select count(*) from private.current_historical_case_search_units;
    reset role;
  $sql$,
  '42501',
  null,
  'authenticated cannot read private current historical search units directly'
);

select throws_ok(
  $sql$
    set local role service_role;
    select count(*) from private.current_historical_case_search_units;
    reset role;
  $sql$,
  '42501',
  null,
  'service_role cannot read private current historical search units directly'
);

select lives_ok(
  $sql$
    do $$
    declare
      before_unit_identity text;
      after_unit_identity text;
      before_version_digest text;
      after_version_digest text;
      before_source_digest text;
      after_source_digest text;
      before_resp_digest text;
      after_resp_digest text;
      before_dec_digest text;
      after_dec_digest text;
      before_lesson_digest text;
      after_lesson_digest text;
    begin
      select string_agg(source_key || ':' || search_unit_id::text, ',' order by source_key)
      into before_unit_identity
      from private.current_historical_case_search_units;

      select md5(string_agg(concat_ws('|', hcv.id::text, hcv.updated_at::text), ',' order by hcv.id))
      into before_version_digest
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code between 'HC-001' and 'HC-009';

      select md5(string_agg(concat_ws('|', hcvso.id::text, hcvso.updated_at::text), ',' order by hcvso.id))
      into before_source_digest
      from public.historical_case_version_source_objects hcvso
      join public.historical_case_versions hcv
        on hcv.id = hcvso.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code between 'HC-001' and 'HC-009';

      select md5(string_agg(concat_ws('|', hcvr.id::text, hcvr.updated_at::text), ',' order by hcvr.id))
      into before_resp_digest
      from public.historical_case_version_responsibilities hcvr
      join public.historical_case_versions hcv
        on hcv.id = hcvr.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code between 'HC-001' and 'HC-009';

      select md5(string_agg(concat_ws('|', hcvd.id::text, hcvd.updated_at::text), ',' order by hcvd.id))
      into before_dec_digest
      from public.historical_case_version_decisions hcvd
      join public.historical_case_versions hcv
        on hcv.id = hcvd.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code between 'HC-001' and 'HC-009';

      select md5(string_agg(concat_ws('|', hcvl.id::text, hcvl.updated_at::text), ',' order by hcvl.id))
      into before_lesson_digest
      from public.historical_case_version_lessons hcvl
      join public.historical_case_versions hcv
        on hcv.id = hcvl.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code between 'HC-001' and 'HC-009';

      perform private.rebuild_current_historical_case_search_units();

      select string_agg(source_key || ':' || search_unit_id::text, ',' order by source_key)
      into after_unit_identity
      from private.current_historical_case_search_units;

      select md5(string_agg(concat_ws('|', hcv.id::text, hcv.updated_at::text), ',' order by hcv.id))
      into after_version_digest
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code between 'HC-001' and 'HC-009';

      select md5(string_agg(concat_ws('|', hcvso.id::text, hcvso.updated_at::text), ',' order by hcvso.id))
      into after_source_digest
      from public.historical_case_version_source_objects hcvso
      join public.historical_case_versions hcv
        on hcv.id = hcvso.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code between 'HC-001' and 'HC-009';

      select md5(string_agg(concat_ws('|', hcvr.id::text, hcvr.updated_at::text), ',' order by hcvr.id))
      into after_resp_digest
      from public.historical_case_version_responsibilities hcvr
      join public.historical_case_versions hcv
        on hcv.id = hcvr.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code between 'HC-001' and 'HC-009';

      select md5(string_agg(concat_ws('|', hcvd.id::text, hcvd.updated_at::text), ',' order by hcvd.id))
      into after_dec_digest
      from public.historical_case_version_decisions hcvd
      join public.historical_case_versions hcv
        on hcv.id = hcvd.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code between 'HC-001' and 'HC-009';

      select md5(string_agg(concat_ws('|', hcvl.id::text, hcvl.updated_at::text), ',' order by hcvl.id))
      into after_lesson_digest
      from public.historical_case_version_lessons hcvl
      join public.historical_case_versions hcv
        on hcv.id = hcvl.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code between 'HC-001' and 'HC-009';

      if before_unit_identity is distinct from after_unit_identity then
        raise exception 'rebuild changed logical search-unit identity';
      end if;

      if before_version_digest is distinct from after_version_digest
         or before_source_digest is distinct from after_source_digest
         or before_resp_digest is distinct from after_resp_digest
         or before_dec_digest is distinct from after_dec_digest
         or before_lesson_digest is distinct from after_lesson_digest then
        raise exception 'rebuild modified governed historical source tables';
      end if;
    end
    $$;
  $sql$,
  'rebuilding historical search units is idempotent and does not mutate governed historical Phase 6 data'
);

select * from finish();

rollback;
