begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

select plan(44);

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
  to_regclass('public.historical_cases') is not null,
  'historical_cases table exists'
);

select ok(
  to_regclass('public.historical_case_aliases') is not null,
  'historical_case_aliases table exists'
);

select ok(
  to_regclass('public.historical_case_versions') is not null,
  'historical_case_versions table exists'
);

select lives_ok(
  $sql$
    insert into public.historical_cases (
      case_code,
      canonical_title
    )
    values (
      'HC-900',
      'Stable Identity Test Case'
    );
  $sql$,
  'valid historical case identity can be created'
);

select is(
  (
    select count(*)
    from public.historical_cases
    where case_code = 'HC-900'
  ),
  1::bigint,
  'case_code HC-900 exists once'
);

select throws_ok(
  $sql$
    insert into public.historical_cases (
      case_code,
      canonical_title
    )
    values (
      'HC-900',
      'Duplicate Stable Identity Test Case'
    );
  $sql$,
  '23505',
  null,
  'case_code must be unique'
);

select throws_ok(
  $sql$
    insert into public.historical_cases (
      case_code,
      canonical_title
    )
    values (
      'BAD-CASE-CODE',
      'Malformed Case Code'
    );
  $sql$,
  '23514',
  null,
  'malformed case_code values are rejected'
);

select lives_ok(
  $sql$
    do $$
    declare
      historical_case_id bigint;
    begin
      select id into historical_case_id
      from public.historical_cases
      where case_code = 'HC-900';

      insert into public.historical_case_aliases (
        historical_case_id,
        alias_text,
        alias_type
      )
      values
        (historical_case_id, 'British Embassy', 'client'),
        (historical_case_id, 'GreenTech', 'brand');
    end
    $$;
  $sql$,
  'multiple aliases can belong to one historical case'
);

select throws_ok(
  $sql$
    do $$
    declare
      historical_case_id bigint;
    begin
      select id into historical_case_id
      from public.historical_cases
      where case_code = 'HC-900';

      insert into public.historical_case_aliases (
        historical_case_id,
        alias_text,
        alias_type
      )
      values (
        historical_case_id,
        '  british   embassy  ',
        'other'
      );
    end
    $$;
  $sql$,
  '23505',
  null,
  'normalized duplicate aliases for the same case are rejected'
);

select lives_ok(
  $sql$
    do $$
    declare
      case_a_id bigint;
    begin
      insert into public.historical_cases (
        case_code,
        canonical_title
      )
      values (
        'HC-901',
        'Multiple Version Test Case'
      )
      returning id into case_a_id;

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
        contains_historical_value_only_content
      )
      select
        case_a_id,
        v.version_number,
        'draft',
        'active',
        'full_case',
        'strong',
        'completed',
        'unknown',
        v.curated_narrative,
        kcl.id,
        'unknown',
        false
      from (
        values
          (1, 'Draft narrative version one'),
          (2, 'Draft narrative version two')
      ) as v(version_number, curated_narrative)
      cross join public.knowledge_confidentiality_levels kcl
      where kcl.level_code = 'internal';
    end
    $$;
  $sql$,
  'one historical case can have multiple versions'
);

select is(
  (
    select count(*)
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-901'
  ),
  2::bigint,
  'two versions exist for the same historical case'
);

select throws_ok(
  $sql$
    do $$
    declare
      case_a_id bigint;
      confidentiality_id bigint;
    begin
      select id into case_a_id
      from public.historical_cases
      where case_code = 'HC-901';

      select id into confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

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
      values (
        case_a_id,
        1,
        'draft',
        'active',
        'full_case',
        'strong',
        'completed',
        'unknown',
        'Duplicate version number',
        confidentiality_id,
        false
      );
    end
    $$;
  $sql$,
  '23505',
  null,
  'version_number must be unique within one case'
);

select lives_ok(
  $sql$
    do $$
    declare
      case_b_id bigint;
      confidentiality_id bigint;
    begin
      insert into public.historical_cases (
        case_code,
        canonical_title
      )
      values (
        'HC-902',
        'Independent Version Number Test Case'
      )
      returning id into case_b_id;

      select id into confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

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
      values (
        case_b_id,
        1,
        'draft',
        'active',
        'full_case',
        'strong',
        'completed',
        'unknown',
        'Version number one may repeat on a different case',
        confidentiality_id,
        false
      );
    end
    $$;
  $sql$,
  'another historical case may independently use the same version number'
);

select throws_ok(
  $sql$
    do $$
    declare
      case_a_id bigint;
      case_b_id bigint;
      case_b_version_id bigint;
      confidentiality_id bigint;
    begin
      select id into case_a_id
      from public.historical_cases
      where case_code = 'HC-901';

      select id into case_b_id
      from public.historical_cases
      where case_code = 'HC-902';

      select id into case_b_version_id
      from public.historical_case_versions
      where historical_case_id = case_b_id
        and version_number = 1;

      select id into confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

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
        contains_historical_value_only_content,
        supersedes_version_id
      )
      values (
        case_a_id,
        3,
        'draft',
        'active',
        'full_case',
        'strong',
        'completed',
        'unknown',
        'Cross-case supersession should fail',
        confidentiality_id,
        false,
        case_b_version_id
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'supersedes_version_id must belong to the same historical case'
);

select throws_ok(
  $sql$
    do $$
    declare
      version_id bigint;
    begin
      insert into public.historical_cases (
        case_code,
        canonical_title
      )
      values (
        'HC-903',
        'Self Supersession Test Case'
      );

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
      select
        hc.id,
        1,
        'draft',
        'active',
        'full_case',
        'strong',
        'completed',
        'unknown',
        'Self supersession should fail',
        kcl.id,
        false
      from public.historical_cases hc
      cross join public.knowledge_confidentiality_levels kcl
      where hc.case_code = 'HC-903'
        and kcl.level_code = 'internal'
      returning id into version_id;

      update public.historical_case_versions
      set supersedes_version_id = version_id
      where id = version_id;
    end
    $$;
  $sql$,
  '23514',
  null,
  'self-supersession is rejected'
);

select throws_ok(
  $sql$
    do $$
    declare
      case_id bigint;
      confidentiality_id bigint;
    begin
      insert into public.historical_cases (
        case_code,
        canonical_title
      )
      values (
        'HC-904',
        'One Active Version Constraint Test Case'
      )
      returning id into case_id;

      select id into confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

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
      values (
        case_id,
        1,
        'active',
        'active',
        'full_case',
        'strong',
        'completed',
        'unknown',
        'First active version',
        confidentiality_id,
        false
      );

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
      values (
        case_id,
        2,
        'active',
        'limited',
        'limited_precedent',
        'moderate',
        'partial_or_unclear',
        'unknown',
        'Second active version should fail',
        confidentiality_id,
        true
      );
    end
    $$;
  $sql$,
  '23505',
  null,
  'at most one active version may exist per historical case'
);

select lives_ok(
  $sql$
    do $$
    declare
      case_id bigint;
      confidentiality_id bigint;
    begin
      select id into confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      insert into public.historical_cases (case_code, canonical_title) values ('HC-905', 'Governance Status Draft');
      insert into public.historical_cases (case_code, canonical_title) values ('HC-906', 'Governance Status Active');
      insert into public.historical_cases (case_code, canonical_title) values ('HC-907', 'Governance Status Superseded');
      insert into public.historical_cases (case_code, canonical_title) values ('HC-908', 'Governance Status Retired');

      select id into case_id from public.historical_cases where case_code = 'HC-905';
      insert into public.historical_case_versions (
        historical_case_id, version_number, governance_status, precedent_availability, precedent_type,
        evidence_strength, historical_event_status, temporal_precision, curated_narrative,
        confidentiality_level_id, contains_historical_value_only_content
      ) values (
        case_id, 1, 'draft', 'active', 'full_case',
        'strong', 'completed', 'unknown', 'Draft governance status accepted',
        confidentiality_id, false
      );

      select id into case_id from public.historical_cases where case_code = 'HC-906';
      insert into public.historical_case_versions (
        historical_case_id, version_number, governance_status, precedent_availability, precedent_type,
        evidence_strength, historical_event_status, temporal_precision, curated_narrative,
        confidentiality_level_id, contains_historical_value_only_content
      ) values (
        case_id, 1, 'active', 'active', 'full_case',
        'strong', 'completed', 'unknown', 'Active governance status accepted',
        confidentiality_id, false
      );

      select id into case_id from public.historical_cases where case_code = 'HC-907';
      insert into public.historical_case_versions (
        historical_case_id, version_number, governance_status, precedent_availability, precedent_type,
        evidence_strength, historical_event_status, temporal_precision, curated_narrative,
        confidentiality_level_id, contains_historical_value_only_content, activated_at
      ) values (
        case_id, 1, 'superseded', 'held', 'limited_precedent',
        'moderate', 'partial_or_unclear', 'unknown', 'Superseded governance status accepted',
        confidentiality_id, true, timezone('utc', now())
      );

      select id into case_id from public.historical_cases where case_code = 'HC-908';
      insert into public.historical_case_versions (
        historical_case_id, version_number, governance_status, precedent_availability, precedent_type,
        evidence_strength, historical_event_status, temporal_precision, curated_narrative,
        confidentiality_level_id, contains_historical_value_only_content
      ) values (
        case_id, 1, 'retired', 'archived', 'cautionary_precedent',
        'limited', 'cancelled', 'unknown', 'Retired governance status accepted',
        confidentiality_id, true
      );
    end
    $$;
  $sql$,
  'valid governance_status values are accepted'
);

select throws_ok(
  $sql$
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
    select
      hc.id,
      99,
      'approved',
      'active',
      'full_case',
      'strong',
      'completed',
      'unknown',
      'Invalid governance status should fail',
      kcl.id,
      false
    from public.historical_cases hc
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-900'
      and kcl.level_code = 'internal';
  $sql$,
  '23514',
  null,
  'invalid governance_status is rejected'
);

select lives_ok(
  $sql$
    insert into public.historical_case_versions (
      historical_case_id, version_number, governance_status, precedent_availability, precedent_type,
      evidence_strength, historical_event_status, temporal_precision, curated_narrative,
      confidentiality_level_id, contains_historical_value_only_content
    )
    select
      hc.id, 2, 'draft', 'limited', 'limited_precedent',
      'moderate', 'postponed', 'unknown', 'Valid precedent availability accepted',
      kcl.id, false
    from public.historical_cases hc
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-902'
      and kcl.level_code = 'internal';
  $sql$,
  'valid precedent_availability values are accepted'
);

select throws_ok(
  $sql$
    insert into public.historical_case_versions (
      historical_case_id, version_number, governance_status, precedent_availability, precedent_type,
      evidence_strength, historical_event_status, temporal_precision, curated_narrative,
      confidentiality_level_id, contains_historical_value_only_content
    )
    select
      hc.id, 3, 'draft', 'paused', 'full_case',
      'strong', 'completed', 'unknown', 'Invalid precedent availability should fail',
      kcl.id, false
    from public.historical_cases hc
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-902'
      and kcl.level_code = 'internal';
  $sql$,
  '23514',
  null,
  'invalid precedent_availability is rejected'
);

select lives_ok(
  $sql$
    insert into public.historical_case_versions (
      historical_case_id, version_number, governance_status, precedent_availability, precedent_type,
      evidence_strength, historical_event_status, temporal_precision, curated_narrative,
      confidentiality_level_id, contains_historical_value_only_content
    )
    select
      hc.id, 2, 'draft', 'held', 'cautionary_precedent',
      'limited', 'planning_only', 'unknown', 'Valid precedent type accepted',
      kcl.id, true
    from public.historical_cases hc
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-903'
      and kcl.level_code = 'internal';
  $sql$,
  'valid precedent_type values are accepted'
);

select throws_ok(
  $sql$
    insert into public.historical_case_versions (
      historical_case_id, version_number, governance_status, precedent_availability, precedent_type,
      evidence_strength, historical_event_status, temporal_precision, curated_narrative,
      confidentiality_level_id, contains_historical_value_only_content
    )
    select
      hc.id, 100, 'draft', 'active', 'deep_case',
      'strong', 'completed', 'unknown', 'Invalid precedent type should fail',
      kcl.id, false
    from public.historical_cases hc
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-900'
      and kcl.level_code = 'internal';
  $sql$,
  '23514',
  null,
  'invalid precedent_type is rejected'
);

select lives_ok(
  $sql$
    insert into public.historical_case_versions (
      historical_case_id, version_number, governance_status, precedent_availability, precedent_type,
      evidence_strength, historical_event_status, temporal_precision, curated_narrative,
      confidentiality_level_id, contains_historical_value_only_content
    )
    select
      hc.id, 101, 'draft', 'active', 'full_case',
      'limited', 'partial_or_unclear', 'unknown', 'Valid evidence strength accepted',
      kcl.id, true
    from public.historical_cases hc
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-900'
      and kcl.level_code = 'internal';
  $sql$,
  'valid evidence_strength values are accepted'
);

select throws_ok(
  $sql$
    insert into public.historical_case_versions (
      historical_case_id, version_number, governance_status, precedent_availability, precedent_type,
      evidence_strength, historical_event_status, temporal_precision, curated_narrative,
      confidentiality_level_id, contains_historical_value_only_content
    )
    select
      hc.id, 102, 'draft', 'active', 'full_case',
      'weak', 'completed', 'unknown', 'Invalid evidence strength should fail',
      kcl.id, false
    from public.historical_cases hc
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-900'
      and kcl.level_code = 'internal';
  $sql$,
  '23514',
  null,
  'invalid evidence_strength is rejected'
);

select lives_ok(
  $sql$
    insert into public.historical_case_versions (
      historical_case_id, version_number, governance_status, precedent_availability, precedent_type,
      evidence_strength, historical_event_status, temporal_precision, curated_narrative,
      confidentiality_level_id, contains_historical_value_only_content
    )
    select
      hc.id, 103, 'draft', 'active', 'full_case',
      'strong', 'cancelled', 'unknown', 'Valid historical event status accepted',
      kcl.id, false
    from public.historical_cases hc
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-900'
      and kcl.level_code = 'internal';
  $sql$,
  'valid historical_event_status values are accepted'
);

select throws_ok(
  $sql$
    insert into public.historical_case_versions (
      historical_case_id, version_number, governance_status, precedent_availability, precedent_type,
      evidence_strength, historical_event_status, temporal_precision, curated_narrative,
      confidentiality_level_id, contains_historical_value_only_content
    )
    select
      hc.id, 104, 'draft', 'active', 'full_case',
      'strong', 'in_progress', 'unknown', 'Invalid historical event status should fail',
      kcl.id, false
    from public.historical_cases hc
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-900'
      and kcl.level_code = 'internal';
  $sql$,
  '23514',
  null,
  'invalid historical_event_status is rejected'
);

select lives_ok(
  $sql$
    insert into public.historical_case_versions (
      historical_case_id, version_number, governance_status, precedent_availability, precedent_type,
      evidence_strength, historical_event_status, temporal_precision, curated_narrative,
      confidentiality_level_id, contains_historical_value_only_content
    )
    select
      hc.id, 105, 'draft', 'active', 'full_case',
      'strong', 'completed', 'unknown', 'Unknown date accepted',
      kcl.id, false
    from public.historical_cases hc
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-900'
      and kcl.level_code = 'internal';
  $sql$,
  'unknown temporal precision is accepted without dates'
);

select lives_ok(
  $sql$
    insert into public.historical_case_versions (
      historical_case_id, version_number, governance_status, precedent_availability, precedent_type,
      evidence_strength, historical_event_status, temporal_precision, event_date_start, event_date_end,
      curated_narrative, confidentiality_level_id, contains_historical_value_only_content
    )
    select
      hc.id, 106, 'draft', 'active', 'full_case',
      'strong', 'completed', 'exact', date '2024-05-12', date '2024-05-12',
      'Exact date accepted', kcl.id, false
    from public.historical_cases hc
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-900'
      and kcl.level_code = 'internal';
  $sql$,
  'exact temporal precision is accepted'
);

select lives_ok(
  $sql$
    insert into public.historical_case_versions (
      historical_case_id, version_number, governance_status, precedent_availability, precedent_type,
      evidence_strength, historical_event_status, temporal_precision, event_date_start, event_date_end,
      curated_narrative, confidentiality_level_id, contains_historical_value_only_content
    )
    select
      hc.id, 107, 'draft', 'active', 'full_case',
      'strong', 'completed', 'month', date '2024-05-01', date '2024-05-31',
      'Month precision accepted', kcl.id, false
    from public.historical_cases hc
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-900'
      and kcl.level_code = 'internal';
  $sql$,
  'month temporal precision is accepted'
);

select lives_ok(
  $sql$
    insert into public.historical_case_versions (
      historical_case_id, version_number, governance_status, precedent_availability, precedent_type,
      evidence_strength, historical_event_status, temporal_precision, event_date_start, event_date_end,
      curated_narrative, confidentiality_level_id, contains_historical_value_only_content
    )
    select
      hc.id, 108, 'draft', 'active', 'full_case',
      'strong', 'completed', 'year', date '2024-01-01', date '2024-12-31',
      'Year precision accepted', kcl.id, false
    from public.historical_cases hc
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-900'
      and kcl.level_code = 'internal';
  $sql$,
  'year temporal precision is accepted'
);

select throws_ok(
  $sql$
    insert into public.historical_case_versions (
      historical_case_id, version_number, governance_status, precedent_availability, precedent_type,
      evidence_strength, historical_event_status, temporal_precision, event_date_start, event_date_end,
      curated_narrative, confidentiality_level_id, contains_historical_value_only_content
    )
    select
      hc.id, 109, 'draft', 'active', 'full_case',
      'strong', 'completed', 'exact', date '2024-05-12', date '2024-05-13',
      'Contradictory exact precision should fail', kcl.id, false
    from public.historical_cases hc
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-900'
      and kcl.level_code = 'internal';
  $sql$,
  '23514',
  null,
  'contradictory exact temporal combinations are rejected'
);

select throws_ok(
  $sql$
    insert into public.historical_case_versions (
      historical_case_id, version_number, governance_status, precedent_availability, precedent_type,
      evidence_strength, historical_event_status, temporal_precision, event_date_start, event_date_end,
      curated_narrative, confidentiality_level_id, contains_historical_value_only_content
    )
    select
      hc.id, 110, 'draft', 'active', 'full_case',
      'strong', 'completed', 'month', date '2024-05-02', date '2024-05-31',
      'Contradictory month precision should fail', kcl.id, false
    from public.historical_cases hc
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-900'
      and kcl.level_code = 'internal';
  $sql$,
  '23514',
  null,
  'contradictory month temporal combinations are rejected'
);

select lives_ok(
  $sql$
    do $$
    declare
      case_id bigint;
      confidentiality_id bigint;
    begin
      insert into public.historical_cases (
        case_code,
        canonical_title
      )
      values (
        'HC-909',
        'Confidentiality and PI Test Case'
      )
      returning id into case_id;

      select id into confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'restricted';

      insert into public.historical_case_versions (
        historical_case_id, version_number, governance_status, precedent_availability, precedent_type,
        evidence_strength, historical_event_status, temporal_precision, curated_narrative,
        confidentiality_level_id, personal_information_status, contains_historical_value_only_content
      )
      values
        (case_id, 1, 'draft', 'active', 'full_case', 'strong', 'completed', 'unknown', 'PI yes accepted', confidentiality_id, 'yes', true),
        (case_id, 2, 'draft', 'held', 'limited_precedent', 'moderate', 'partial_or_unclear', 'unknown', 'PI no accepted', confidentiality_id, 'no', false),
        (case_id, 3, 'draft', 'archived', 'cautionary_precedent', 'limited', 'cancelled', 'unknown', 'PI unknown accepted', confidentiality_id, 'unknown', true);
    end
    $$;
  $sql$,
  'valid confidentiality references and PI values are accepted'
);

select throws_ok(
  $sql$
    insert into public.historical_case_versions (
      historical_case_id, version_number, governance_status, precedent_availability, precedent_type,
      evidence_strength, historical_event_status, temporal_precision, curated_narrative,
      confidentiality_level_id, contains_historical_value_only_content
    )
    select
      hc.id, 4, 'draft', 'active', 'full_case',
      'strong', 'completed', 'unknown', 'Invalid confidentiality reference should fail',
      999999999, false
    from public.historical_cases hc
    where hc.case_code = 'HC-909';
  $sql$,
  '23503',
  null,
  'invalid confidentiality references are rejected'
);

select throws_ok(
  $sql$
    insert into public.historical_case_versions (
      historical_case_id, version_number, governance_status, precedent_availability, precedent_type,
      evidence_strength, historical_event_status, temporal_precision, curated_narrative,
      confidentiality_level_id, personal_information_status, contains_historical_value_only_content
    )
    select
      hc.id, 4, 'draft', 'active', 'full_case',
      'strong', 'completed', 'unknown', 'Invalid PI status should fail',
      kcl.id, 'maybe', false
    from public.historical_cases hc
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-909'
      and kcl.level_code = 'restricted';
  $sql$,
  '23514',
  null,
  'invalid PI values are rejected'
);

select is(
  (
    select contains_historical_value_only_content
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-909'
      and hcv.version_number = 1
  ),
  true,
  'historical value summary flag persists correctly'
);

select lives_ok(
  $sql$
    do $$
    begin
      update public.historical_case_versions hcv
      set
        curated_narrative = 'Draft narrative updated before activation',
        evidence_strength = 'moderate'
      from public.historical_cases hc
      where hc.id = hcv.historical_case_id
        and hc.case_code = 'HC-901'
        and hcv.version_number = 1;
    end
    $$;
  $sql$,
  'draft versions may be edited before activation'
);

select throws_ok(
  $sql$
    do $$
    begin
      update public.historical_case_versions hcv
      set curated_narrative = 'Active version rewrite should fail'
      from public.historical_cases hc
      where hc.id = hcv.historical_case_id
        and hc.case_code = 'HC-906'
        and hcv.version_number = 1;
    end
    $$;
  $sql$,
  '23514',
  null,
  'active versions may not be materially rewritten'
);

select lives_ok(
  $sql$
    do $$
    begin
      update public.historical_case_versions hcv
      set governance_status = 'superseded'
      from public.historical_cases hc
      where hc.id = hcv.historical_case_id
        and hc.case_code = 'HC-906'
        and hcv.version_number = 1;
    end
    $$;
  $sql$,
  'an active version may be marked superseded without being deleted'
);

select lives_ok(
  $sql$
    do $$
    declare
      case_id bigint;
      superseded_version_id bigint;
      confidentiality_id bigint;
    begin
      select hc.id into case_id
      from public.historical_cases hc
      where hc.case_code = 'HC-906';

      select hcv.id into superseded_version_id
      from public.historical_case_versions hcv
      where hcv.historical_case_id = case_id
        and hcv.version_number = 1;

      select id into confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      insert into public.historical_case_versions (
        historical_case_id, version_number, governance_status, precedent_availability, precedent_type,
        evidence_strength, historical_event_status, temporal_precision, event_date_start, event_date_end,
        curated_narrative, confidentiality_level_id, contains_historical_value_only_content, supersedes_version_id
      )
      values (
        case_id, 2, 'active', 'limited', 'limited_precedent',
        'moderate', 'partial_or_unclear', 'approximate', date '2024-05-10', date '2024-05-14',
        'New active version supersedes prior version', confidentiality_id, true, superseded_version_id
      );
    end
    $$;
  $sql$,
  'a new version can supersede the previous version'
);

select results_eq(
  $sql$
    select c.relname
    from pg_class c
    join pg_namespace n
      on n.oid = c.relnamespace
    where n.nspname = 'public'
      and c.relname in ('historical_cases', 'historical_case_aliases', 'historical_case_versions')
      and c.relrowsecurity
    order by c.relname
  $sql$,
  $sql$
    values
      ('historical_case_aliases'::name),
      ('historical_case_versions'::name),
      ('historical_cases'::name)
  $sql$,
  'RLS is enabled on the three Phase 6 governance tables'
);

select is(
  (
    select count(*)
    from information_schema.role_table_grants rtg
    where rtg.table_schema = 'public'
      and rtg.table_name in ('historical_cases', 'historical_case_aliases', 'historical_case_versions')
      and rtg.grantee in ('anon', 'authenticated', 'service_role')
      and rtg.privilege_type in ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'REFERENCES', 'TRIGGER', 'TRUNCATE')
  ),
  0::bigint,
  'ordinary roles have no direct grants on the Phase 6 governance tables'
);

select throws_ok(
  $sql$
    select public._test_count_as('anon', $query$select * from public.historical_cases$query$);
  $sql$,
  '42501',
  null,
  'anon cannot directly read historical_cases'
);

select throws_ok(
  $sql$
    select public._test_count_as('authenticated', $query$select * from public.historical_case_versions$query$);
  $sql$,
  '42501',
  null,
  'authenticated cannot directly read historical_case_versions'
);

select *
from finish();

rollback;
