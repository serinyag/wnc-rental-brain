begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

select plan(43);

create or replace function public._test_count_as(p_role name, p_sql text)
returns bigint
language plpgsql
as $$
declare
  result bigint;
begin
  execute format('set local role %I', p_role);
  execute format('select count(*) from (%s) q', p_sql) into result;
  execute 'reset role';
  return result;
exception when others then
  begin
    execute 'reset role';
  exception when others then
    null;
  end;
  raise;
end;
$$;

select ok(
  to_regclass('public.historical_precedent_topics') is not null,
  'historical_precedent_topics table exists'
);

select ok(
  to_regclass('public.historical_case_version_topics') is not null,
  'historical_case_version_topics table exists'
);

select ok(
  to_regclass('public.historical_case_version_rental_types') is not null,
  'historical_case_version_rental_types table exists'
);

select ok(
  to_regclass('public.historical_case_version_spaces') is not null,
  'historical_case_version_spaces table exists'
);

select results_eq(
  $sql$
    select topic_code
    from public.historical_precedent_topics
    order by sort_order, topic_code
  $sql$,
  $sql$
    values
      ('venue_clearing'::text),
      ('storage'::text),
      ('offsite_storage'::text),
      ('responsibility_boundaries'::text),
      ('client_operated_events'::text),
      ('production_coordination'::text),
      ('technical_assessment'::text),
      ('electrical_load'::text),
      ('catering_supplier_coordination'::text),
      ('alcohol_beverage_boundaries'::text),
      ('production_access'::text),
      ('overtime'::text),
      ('materials_cleanup_damage'::text),
      ('branding_restrictions'::text),
      ('class_schedule_interaction'::text),
      ('permits_compliance'::text)
  $sql$,
  'expected historical precedent topic codes are seeded'
);

select throws_ok(
  $sql$
    insert into public.historical_precedent_topics (
      topic_code,
      display_name,
      description
    )
    values (
      'storage',
      'Duplicate Storage',
      'duplicate topic code should fail'
    );
  $sql$,
  '23505',
  null,
  'topic code uniqueness is enforced'
);

select lives_ok(
  $sql$
    do $$
    declare
      internal_confidentiality_id bigint;
      case_a_id bigint;
      case_b_id bigint;
      case_c_id bigint;
      case_a_version_id bigint;
      case_b_version_id bigint;
      case_c_version_id bigint;
      storage_topic_id bigint;
      venue_clearing_topic_id bigint;
      production_coordination_topic_id bigint;
      studio_rental_type_id bigint;
      entire_venue_rental_type_id bigint;
      custom_scope_rental_type_id bigint;
      studio_space_id bigint;
      retail_area_id bigint;
      storage_room_id bigint;
    begin
      select id into internal_confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      select id into storage_topic_id
      from public.historical_precedent_topics
      where topic_code = 'storage';

      select id into venue_clearing_topic_id
      from public.historical_precedent_topics
      where topic_code = 'venue_clearing';

      select id into production_coordination_topic_id
      from public.historical_precedent_topics
      where topic_code = 'production_coordination';

      select id into studio_rental_type_id
      from public.rental_types
      where rental_type_code = 'studio_space';

      select id into entire_venue_rental_type_id
      from public.rental_types
      where rental_type_code = 'entire_venue';

      select id into custom_scope_rental_type_id
      from public.rental_types
      where rental_type_code = 'custom_scope';

      select id into studio_space_id
      from public.venue_spaces
      where space_code = 'studio_space';

      select id into retail_area_id
      from public.venue_spaces
      where space_code = 'retail_area';

      select id into storage_room_id
      from public.venue_spaces
      where space_code = 'storage_room';

      insert into public.historical_cases (
        case_code,
        canonical_title
      )
      values
        ('HC-940', 'Classification Draft Fixture A'),
        ('HC-941', 'Classification Draft Fixture B'),
        ('HC-942', 'Classification Immutability Fixture');

      select id into case_a_id from public.historical_cases where case_code = 'HC-940';
      select id into case_b_id from public.historical_cases where case_code = 'HC-941';
      select id into case_c_id from public.historical_cases where case_code = 'HC-942';

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
        contains_historical_value_only_content
      )
      values
        (case_a_id, 1, 'draft', 'active', 'full_case', 'strong', 'completed', 'unknown', 'Classification draft case A', internal_confidentiality_id, false),
        (case_b_id, 1, 'draft', 'limited', 'limited_precedent', 'moderate', 'partial_or_unclear', 'unknown', 'Classification draft case B', internal_confidentiality_id, true),
        (case_c_id, 1, 'draft', 'active', 'full_case', 'strong', 'completed', 'unknown', 'Classification draft case C', internal_confidentiality_id, false);

      select id into case_a_version_id
      from public.historical_case_versions
      where historical_case_id = case_a_id
        and version_number = 1;

      select id into case_b_version_id
      from public.historical_case_versions
      where historical_case_id = case_b_id
        and version_number = 1;

      select id into case_c_version_id
      from public.historical_case_versions
      where historical_case_id = case_c_id
        and version_number = 1;

      insert into public.historical_case_version_topics (
        historical_case_version_id,
        topic_id,
        topic_relevance
      )
      values
        (case_a_version_id, storage_topic_id, 'primary'),
        (case_a_version_id, venue_clearing_topic_id, 'secondary'),
        (case_b_version_id, storage_topic_id, 'secondary'),
        (case_c_version_id, production_coordination_topic_id, 'primary');

      insert into public.historical_case_version_rental_types (
        historical_case_version_id,
        rental_type_id
      )
      values
        (case_a_version_id, custom_scope_rental_type_id),
        (case_a_version_id, entire_venue_rental_type_id),
        (case_c_version_id, studio_rental_type_id);

      insert into public.historical_case_version_spaces (
        historical_case_version_id,
        venue_space_id
      )
      values
        (case_a_version_id, studio_space_id),
        (case_a_version_id, retail_area_id),
        (case_c_version_id, storage_room_id);
    end
    $$;
  $sql$,
  'draft historical case versions can receive initial topic, rental-type, and space classifications'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_topics (
      historical_case_version_id,
      topic_id,
      topic_relevance
    )
    select
      hcv.id,
      999999999,
      'primary'
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-940'
      and hcv.version_number = 1;
  $sql$,
  '23503',
  null,
  'invalid topic references are rejected'
);

select is(
  (
    select count(*)
    from public.historical_case_version_topics hcvt
    join public.historical_case_versions hcv
      on hcv.id = hcvt.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-940'
  ),
  2::bigint,
  'draft case version can receive multiple topics'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_topics (
      historical_case_version_id,
      topic_id,
      topic_relevance
    )
    select
      hcv.id,
      hpt.id,
      'secondary'
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join public.historical_precedent_topics hpt
    where hc.case_code = 'HC-940'
      and hcv.version_number = 1
      and hpt.topic_code = 'storage';
  $sql$,
  '23505',
  null,
  'duplicate topic links are rejected'
);

select is(
  (
    select count(distinct hcvt.historical_case_version_id)
    from public.historical_case_version_topics hcvt
    join public.historical_precedent_topics hpt
      on hpt.id = hcvt.topic_id
    join public.historical_case_versions hcv
      on hcv.id = hcvt.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hpt.topic_code = 'storage'
      and hc.case_code in ('HC-940', 'HC-941')
  ),
  2::bigint,
  'same topic may be used by multiple fixture case versions'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_topics (
      historical_case_version_id,
      topic_id,
      topic_relevance
    )
    select
      hcv.id,
      hpt.id,
      'tertiary'
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join public.historical_precedent_topics hpt
    where hc.case_code = 'HC-940'
      and hcv.version_number = 1
      and hpt.topic_code = 'permits_compliance';
  $sql$,
  '23514',
  null,
  'invalid topic relevance is rejected'
);

select results_eq(
  $sql$
    select hcvt.topic_relevance
    from public.historical_case_version_topics hcvt
    join public.historical_case_versions hcv
      on hcv.id = hcvt.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    join public.historical_precedent_topics hpt
      on hpt.id = hcvt.topic_id
    where hc.case_code = 'HC-940'
      and hpt.topic_code = 'storage'
  $sql$,
  $sql$
    values
      ('primary'::text)
  $sql$,
  'valid topic relevance values are accepted'
);

select is(
  (
    select count(*)
    from public.historical_case_version_rental_types hcvrt
    join public.historical_case_versions hcv
      on hcv.id = hcvrt.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-940'
  ),
  2::bigint,
  'draft case version can link to multiple existing canonical rental types'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_rental_types (
      historical_case_version_id,
      rental_type_id
    )
    select
      hcv.id,
      hcvrt.rental_type_id
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    join public.historical_case_version_rental_types hcvrt
      on hcvrt.historical_case_version_id = hcv.id
    where hc.case_code = 'HC-940'
      and hcv.version_number = 1
    limit 1;
  $sql$,
  '23505',
  null,
  'duplicate rental-type links are rejected'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_rental_types (
      historical_case_version_id,
      rental_type_id
    )
    select
      hcv.id,
      999999999
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-940'
      and hcv.version_number = 1;
  $sql$,
  '23503',
  null,
  'invalid rental-type references are rejected'
);

select is(
  (
    select count(*)
    from public.historical_case_version_spaces hcvs
    join public.historical_case_versions hcv
      on hcv.id = hcvs.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-940'
  ),
  2::bigint,
  'draft case version can link to multiple existing canonical venue spaces'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_spaces (
      historical_case_version_id,
      venue_space_id
    )
    select
      hcv.id,
      hcvs.venue_space_id
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    join public.historical_case_version_spaces hcvs
      on hcvs.historical_case_version_id = hcv.id
    where hc.case_code = 'HC-940'
      and hcv.version_number = 1
    limit 1;
  $sql$,
  '23505',
  null,
  'duplicate space links are rejected'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_spaces (
      historical_case_version_id,
      venue_space_id
    )
    select
      hcv.id,
      999999999
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-940'
      and hcv.version_number = 1;
  $sql$,
  '23503',
  null,
  'invalid venue-space references are rejected'
);

select ok(
  exists (
    select 1
    from pg_constraint c
    where c.conrelid = 'public.historical_case_version_rental_types'::regclass
      and c.confrelid = 'public.rental_types'::regclass
      and c.contype = 'f'
  ),
  'Phase 6 rental-type classification reuses canonical public.rental_types'
);

select ok(
  exists (
    select 1
    from pg_constraint c
    where c.conrelid = 'public.historical_case_version_spaces'::regclass
      and c.confrelid = 'public.venue_spaces'::regclass
      and c.contype = 'f'
  ),
  'Phase 6 space classification reuses canonical public.venue_spaces'
);

select ok(
  to_regclass('public.historical_rental_types') is null,
  'no duplicate Phase 6 rental-type lookup table is created'
);

select ok(
  to_regclass('public.historical_venue_spaces') is null,
  'no duplicate Phase 6 venue-space lookup table is created'
);

select lives_ok(
  $sql$
    update public.historical_case_version_topics hcvt
    set topic_relevance = 'primary'
    from public.historical_case_versions hcv,
         public.historical_cases hc,
         public.historical_precedent_topics hpt
    where hcvt.historical_case_version_id = hcv.id
      and hc.id = hcv.historical_case_id
      and hpt.id = hcvt.topic_id
      and hc.case_code = 'HC-940'
      and hpt.topic_code = 'venue_clearing';
  $sql$,
  'draft topic links may be updated'
);

select lives_ok(
  $sql$
    update public.historical_case_version_rental_types hcvrt
    set rental_type_id = (
      select id
      from public.rental_types
      where rental_type_code = 'studio_space'
    )
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hcvrt.historical_case_version_id = hcv.id
      and hc.case_code = 'HC-940'
      and hcvrt.rental_type_id = (
        select id
        from public.rental_types
        where rental_type_code = 'entire_venue'
      );
  $sql$,
  'draft rental-type links may be updated'
);

select lives_ok(
  $sql$
    update public.historical_case_version_spaces hcvs
    set venue_space_id = (
      select id
      from public.venue_spaces
      where space_code = 'conversation_pit'
    )
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hcvs.historical_case_version_id = hcv.id
      and hc.case_code = 'HC-940'
      and hcvs.venue_space_id = (
        select id
        from public.venue_spaces
        where space_code = 'retail_area'
      );
  $sql$,
  'draft space links may be updated'
);

select lives_ok(
  $sql$
    delete from public.historical_case_version_topics hcvt
    using public.historical_case_versions hcv,
          public.historical_cases hc,
          public.historical_precedent_topics hpt
    where hcvt.historical_case_version_id = hcv.id
      and hcv.historical_case_id = hc.id
      and hcvt.topic_id = hpt.id
      and hc.case_code = 'HC-940'
      and hpt.topic_code = 'venue_clearing';
  $sql$,
  'draft topic links may be deleted'
);

select lives_ok(
  $sql$
    delete from public.historical_case_version_rental_types hcvrt
    using public.historical_case_versions hcv,
          public.historical_cases hc
    where hcvrt.historical_case_version_id = hcv.id
      and hcv.historical_case_id = hc.id
      and hc.case_code = 'HC-940'
      and hcvrt.rental_type_id = (
        select id
        from public.rental_types
        where rental_type_code = 'custom_scope'
      );
  $sql$,
  'draft rental-type links may be deleted'
);

select lives_ok(
  $sql$
    delete from public.historical_case_version_spaces hcvs
    using public.historical_case_versions hcv,
          public.historical_cases hc
    where hcvs.historical_case_version_id = hcv.id
      and hcv.historical_case_id = hc.id
      and hc.case_code = 'HC-940'
      and hcvs.venue_space_id = (
        select id
        from public.venue_spaces
        where space_code = 'conversation_pit'
      );
  $sql$,
  'draft space links may be deleted'
);

select lives_ok(
  $sql$
    update public.historical_case_versions hcv
    set governance_status = 'active'
    from public.historical_cases hc
    where hc.id = hcv.historical_case_id
      and hc.case_code = 'HC-942'
      and hcv.version_number = 1;
  $sql$,
  'classification fixtures can be activated after draft classification is assembled'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_topics (
      historical_case_version_id,
      topic_id,
      topic_relevance
    )
    select
      hcv.id,
      hpt.id,
      'secondary'
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join public.historical_precedent_topics hpt
    where hc.case_code = 'HC-942'
      and hcv.version_number = 1
      and hpt.topic_code = 'overtime';
  $sql$,
  '23514',
  null,
  'active case versions cannot receive new topic links in place'
);

select throws_ok(
  $sql$
    update public.historical_case_version_topics hcvt
    set topic_relevance = 'secondary'
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hcvt.historical_case_version_id = hcv.id
      and hc.case_code = 'HC-942';
  $sql$,
  '23514',
  null,
  'active topic links cannot be materially updated'
);

select throws_ok(
  $sql$
    delete from public.historical_case_version_topics hcvt
    using public.historical_case_versions hcv,
          public.historical_cases hc
    where hcvt.historical_case_version_id = hcv.id
      and hcv.historical_case_id = hc.id
      and hc.case_code = 'HC-942';
  $sql$,
  '23514',
  null,
  'active topic links cannot be deleted'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_rental_types (
      historical_case_version_id,
      rental_type_id
    )
    select
      hcv.id,
      rt.id
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join public.rental_types rt
    where hc.case_code = 'HC-942'
      and hcv.version_number = 1
      and rt.rental_type_code = 'custom_scope';
  $sql$,
  '23514',
  null,
  'active case versions cannot receive new rental-type links in place'
);

select throws_ok(
  $sql$
    update public.historical_case_version_rental_types hcvrt
    set rental_type_id = (
      select id
      from public.rental_types
      where rental_type_code = 'entire_venue'
    )
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hcvrt.historical_case_version_id = hcv.id
      and hc.case_code = 'HC-942';
  $sql$,
  '23514',
  null,
  'active rental-type links cannot be materially updated'
);

select throws_ok(
  $sql$
    delete from public.historical_case_version_rental_types hcvrt
    using public.historical_case_versions hcv,
          public.historical_cases hc
    where hcvrt.historical_case_version_id = hcv.id
      and hcv.historical_case_id = hc.id
      and hc.case_code = 'HC-942';
  $sql$,
  '23514',
  null,
  'active rental-type links cannot be deleted'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_spaces (
      historical_case_version_id,
      venue_space_id
    )
    select
      hcv.id,
      vs.id
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join public.venue_spaces vs
    where hc.case_code = 'HC-942'
      and hcv.version_number = 1
      and vs.space_code = 'retail_area';
  $sql$,
  '23514',
  null,
  'active case versions cannot receive new space links in place'
);

select throws_ok(
  $sql$
    update public.historical_case_version_spaces hcvs
    set venue_space_id = (
      select id
      from public.venue_spaces
      where space_code = 'studio_space'
    )
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hcvs.historical_case_version_id = hcv.id
      and hc.case_code = 'HC-942';
  $sql$,
  '23514',
  null,
  'active space links cannot be materially updated'
);

select throws_ok(
  $sql$
    delete from public.historical_case_version_spaces hcvs
    using public.historical_case_versions hcv,
          public.historical_cases hc
    where hcvs.historical_case_version_id = hcv.id
      and hcv.historical_case_id = hc.id
      and hc.case_code = 'HC-942';
  $sql$,
  '23514',
  null,
  'active space links cannot be deleted'
);

select results_eq(
  $sql$
    select c.relname
    from pg_class c
    join pg_namespace n
      on n.oid = c.relnamespace
    where n.nspname = 'public'
      and c.relname in (
        'historical_precedent_topics',
        'historical_case_version_topics',
        'historical_case_version_rental_types',
        'historical_case_version_spaces'
      )
      and c.relrowsecurity
    order by c.relname
  $sql$,
  $sql$
    values
      ('historical_case_version_rental_types'::name),
      ('historical_case_version_spaces'::name),
      ('historical_case_version_topics'::name),
      ('historical_precedent_topics'::name)
  $sql$,
  'RLS is enabled on the Phase 6.2C classification tables'
);

select is(
  (
    select count(*)
    from information_schema.role_table_grants rtg
    where rtg.table_schema = 'public'
      and rtg.table_name in (
        'historical_precedent_topics',
        'historical_case_version_topics',
        'historical_case_version_rental_types',
        'historical_case_version_spaces'
      )
      and rtg.grantee in ('anon', 'authenticated', 'service_role')
      and rtg.privilege_type in ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'REFERENCES', 'TRIGGER', 'TRUNCATE')
  ),
  0::bigint,
  'ordinary roles have no direct grants on the Phase 6.2C classification tables'
);

select throws_ok(
  $sql$
    select public._test_count_as('anon', $query$select * from public.historical_precedent_topics$query$);
  $sql$,
  '42501',
  null,
  'anon cannot directly read historical_precedent_topics'
);

select throws_ok(
  $sql$
    select public._test_count_as('authenticated', $query$select * from public.historical_case_version_topics$query$);
  $sql$,
  '42501',
  null,
  'authenticated cannot directly read historical_case_version_topics'
);

select *
from finish();

rollback;
