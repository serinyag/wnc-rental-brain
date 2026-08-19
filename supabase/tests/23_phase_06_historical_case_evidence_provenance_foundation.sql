begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

select plan(30);

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
  to_regclass('public.historical_case_evidence_roles') is not null,
  'historical_case_evidence_roles table exists'
);

select ok(
  to_regclass('public.historical_case_version_source_objects') is not null,
  'historical_case_version_source_objects table exists'
);

select results_eq(
  $sql$
    select role_code
    from public.historical_case_evidence_roles
    order by sort_order, role_code
  $sql$,
  $sql$
    values
      ('curated_case_library_source'::text),
      ('primary_supporting_evidence'::text),
      ('secondary_supporting_evidence'::text),
      ('context_only_support'::text)
  $sql$,
  'approved historical case evidence role codes are seeded'
);

select throws_ok(
  $sql$
    insert into public.historical_case_evidence_roles (
      role_code,
      display_name,
      description
    )
    values (
      'context_only_support',
      'Duplicate Context Role',
      'duplicate historical evidence role should fail'
    );
  $sql$,
  '23505',
  null,
  'duplicate historical evidence role codes are rejected'
);

select lives_ok(
  $sql$
    do $$
    declare
      internal_confidentiality_id bigint;
      restricted_confidentiality_id bigint;
      primary_role_id bigint;
      secondary_role_id bigint;
      context_role_id bigint;
      case_a_id bigint;
      case_b_id bigint;
      case_c_id bigint;
      case_a_version_id bigint;
      case_b_version_id bigint;
      case_c_version_id bigint;
      shared_source_object_id bigint;
      secondary_source_object_id bigint;
      active_source_object_id bigint;
    begin
      select id into internal_confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      select id into restricted_confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'restricted';

      select id into primary_role_id
      from public.historical_case_evidence_roles
      where role_code = 'primary_supporting_evidence';

      select id into secondary_role_id
      from public.historical_case_evidence_roles
      where role_code = 'secondary_supporting_evidence';

      select id into context_role_id
      from public.historical_case_evidence_roles
      where role_code = 'context_only_support';

      insert into public.historical_cases (
        case_code,
        canonical_title
      )
      values
        ('HC-930', 'Historical Evidence Draft Fixture A'),
        ('HC-931', 'Historical Evidence Draft Fixture B'),
        ('HC-932', 'Historical Evidence Immutability Fixture');

      select id into case_a_id from public.historical_cases where case_code = 'HC-930';
      select id into case_b_id from public.historical_cases where case_code = 'HC-931';
      select id into case_c_id from public.historical_cases where case_code = 'HC-932';

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
        (case_a_id, 1, 'draft', 'active', 'full_case', 'strong', 'completed', 'unknown', 'Draft case A narrative', internal_confidentiality_id, false),
        (case_b_id, 1, 'draft', 'limited', 'limited_precedent', 'moderate', 'partial_or_unclear', 'unknown', 'Draft case B narrative', internal_confidentiality_id, true),
        (case_c_id, 1, 'draft', 'active', 'full_case', 'strong', 'completed', 'unknown', 'Draft case C narrative', internal_confidentiality_id, false);

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

      insert into public.knowledge_source_objects (
        origin_type,
        manual_reference_key,
        original_filename
      )
      values
        ('manual_reference', 'MANUAL-HIST-6B-SHARED', 'historical-shared-source.txt'),
        ('manual_reference', 'MANUAL-HIST-6B-SECONDARY', 'historical-secondary-source.txt'),
        ('manual_reference', 'MANUAL-HIST-6B-ACTIVE', 'historical-active-source.txt');

      select id into shared_source_object_id
      from public.knowledge_source_objects
      where manual_reference_key = 'MANUAL-HIST-6B-SHARED';

      select id into secondary_source_object_id
      from public.knowledge_source_objects
      where manual_reference_key = 'MANUAL-HIST-6B-SECONDARY';

      select id into active_source_object_id
      from public.knowledge_source_objects
      where manual_reference_key = 'MANUAL-HIST-6B-ACTIVE';

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
      values
        (
          case_a_version_id,
          shared_source_object_id,
          primary_role_id,
          restricted_confidentiality_id,
          'strong',
          'Case 01 - Curated Narrative Section',
          array['identity', 'date']::text[],
          'Supports case identity and broad timing from the shared historical source.'
        ),
        (
          case_a_version_id,
          shared_source_object_id,
          primary_role_id,
          restricted_confidentiality_id,
          'moderate',
          'Case 01 - Operational Decision Section',
          array['decision', 'lesson']::text[],
          'Distinct locator within the same shared source artifact.'
        ),
        (
          case_a_version_id,
          secondary_source_object_id,
          secondary_role_id,
          internal_confidentiality_id,
          'moderate',
          'Agreement appendix page 2',
          array['context']::text[],
          'Secondary supporting context only.'
        ),
        (
          case_b_version_id,
          shared_source_object_id,
          context_role_id,
          internal_confidentiality_id,
          'limited',
          'Smaller Precedent - ADE Event',
          array['context']::text[],
          'Shared source reused for another case version with a different locator.'
        ),
        (
          case_c_version_id,
          active_source_object_id,
          primary_role_id,
          internal_confidentiality_id,
          'strong',
          'Case C - Primary Evidence',
          array['identity', 'decision']::text[],
          'Evidence prepared while the parent case version is still draft.'
        );
    end
    $$;
  $sql$,
  'draft case versions can link to valid source objects with evidence metadata'
);

select is(
  (
    select count(*)
    from public.historical_case_version_source_objects hcvso
    join public.historical_case_versions hcv
      on hcv.id = hcvso.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-930'
      and hcvso.source_object_id = (
        select id
        from public.knowledge_source_objects
        where manual_reference_key = 'MANUAL-HIST-6B-SHARED'
      )
  ),
  2::bigint,
  'source locator distinguishes multiple case sections within one shared source artifact'
);

select is(
  (
    select count(distinct hcvso.source_object_id)
    from public.historical_case_version_source_objects hcvso
    join public.historical_case_versions hcv
      on hcv.id = hcvso.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-930'
  ),
  2::bigint,
  'one historical case version can reference multiple source objects'
);

select is(
  (
    select count(distinct hcvso.historical_case_version_id)
    from public.historical_case_version_source_objects hcvso
    where hcvso.source_object_id = (
      select id
      from public.knowledge_source_objects
      where manual_reference_key = 'MANUAL-HIST-6B-SHARED'
    )
  ),
  2::bigint,
  'one knowledge_source_object can support multiple historical case versions'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_source_objects (
      historical_case_version_id,
      source_object_id,
      evidence_role_id,
      confidentiality_level_id,
      evidence_strength,
      source_locator,
      supported_claim_dimensions
    )
    select
      999999999,
      kso.id,
      hcer.id,
      kcl.id,
      'strong',
      'Invalid case version reference',
      array['identity']::text[]
    from public.knowledge_source_objects kso
    cross join public.historical_case_evidence_roles hcer
    cross join public.knowledge_confidentiality_levels kcl
    where kso.manual_reference_key = 'MANUAL-HIST-6B-SHARED'
      and hcer.role_code = 'primary_supporting_evidence'
      and kcl.level_code = 'internal';
  $sql$,
  '23503',
  null,
  'historical case evidence associations require a valid historical_case_version'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_source_objects (
      historical_case_version_id,
      source_object_id,
      evidence_role_id,
      confidentiality_level_id,
      evidence_strength,
      source_locator,
      supported_claim_dimensions
    )
    select
      hcv.id,
      999999999,
      hcer.id,
      kcl.id,
      'strong',
      'Invalid source object reference',
      array['identity']::text[]
    from public.historical_case_versions hcv
    cross join public.historical_case_evidence_roles hcer
    cross join public.knowledge_confidentiality_levels kcl
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-930'
      and hcv.version_number = 1
      and hcer.role_code = 'primary_supporting_evidence'
      and kcl.level_code = 'internal';
  $sql$,
  '23503',
  null,
  'historical case evidence associations require a valid source_object_id'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_source_objects (
      historical_case_version_id,
      source_object_id,
      evidence_role_id,
      confidentiality_level_id,
      evidence_strength,
      source_locator,
      supported_claim_dimensions
    )
    select
      hcv.id,
      kso.id,
      999999999,
      kcl.id,
      'strong',
      'Invalid evidence role reference',
      array['identity']::text[]
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join public.knowledge_source_objects kso
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-930'
      and hcv.version_number = 1
      and kso.manual_reference_key = 'MANUAL-HIST-6B-SHARED'
      and kcl.level_code = 'internal';
  $sql$,
  '23503',
  null,
  'historical case evidence associations require a valid evidence_role_id'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_source_objects (
      historical_case_version_id,
      source_object_id,
      evidence_role_id,
      confidentiality_level_id,
      evidence_strength,
      source_locator,
      supported_claim_dimensions
    )
    select
      hcv.id,
      kso.id,
      hcer.id,
      999999999,
      'strong',
      'Invalid confidentiality reference',
      array['identity']::text[]
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join public.knowledge_source_objects kso
    cross join public.historical_case_evidence_roles hcer
    where hc.case_code = 'HC-930'
      and hcv.version_number = 1
      and kso.manual_reference_key = 'MANUAL-HIST-6B-SHARED'
      and hcer.role_code = 'primary_supporting_evidence';
  $sql$,
  '23503',
  null,
  'historical case evidence associations require a valid confidentiality level'
);

select lives_ok(
  $sql$
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
    select
      hcv.id,
      kso.id,
      hcer.id,
      kcl.id,
      'limited',
      'Case 01 - Appendix Locator',
      array['context']::text[],
      'Third distinct locator on the same shared source remains valid.'
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join public.knowledge_source_objects kso
    cross join public.historical_case_evidence_roles hcer
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-930'
      and hcv.version_number = 1
      and kso.manual_reference_key = 'MANUAL-HIST-6B-SHARED'
      and hcer.role_code = 'primary_supporting_evidence'
      and kcl.level_code = 'internal';
  $sql$,
  'same source object and role may be reused on one case version when the locator is different'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_source_objects (
      historical_case_version_id,
      source_object_id,
      evidence_role_id,
      confidentiality_level_id,
      evidence_strength,
      source_locator,
      supported_claim_dimensions
    )
    select
      hcv.id,
      kso.id,
      hcer.id,
      kcl.id,
      'strong',
      'Case 01 - Curated Narrative Section',
      array['identity']::text[]
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join public.knowledge_source_objects kso
    cross join public.historical_case_evidence_roles hcer
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-930'
      and hcv.version_number = 1
      and kso.manual_reference_key = 'MANUAL-HIST-6B-SHARED'
      and hcer.role_code = 'primary_supporting_evidence'
      and kcl.level_code = 'restricted';
  $sql$,
  '23505',
  null,
  'duplicate historical case evidence associations matching the uniqueness key are rejected'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_source_objects (
      historical_case_version_id,
      source_object_id,
      evidence_role_id,
      confidentiality_level_id,
      evidence_strength,
      source_locator,
      supported_claim_dimensions
    )
    select
      hcv.id,
      kso.id,
      hcer.id,
      kcl.id,
      'strong',
      '',
      array['identity']::text[]
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join public.knowledge_source_objects kso
    cross join public.historical_case_evidence_roles hcer
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-930'
      and hcv.version_number = 1
      and kso.manual_reference_key = 'MANUAL-HIST-6B-SHARED'
      and hcer.role_code = 'secondary_supporting_evidence'
      and kcl.level_code = 'internal';
  $sql$,
  '23514',
  null,
  'source_locator is required and may not be empty'
);

select results_eq(
  $sql$
    select supported_claim_dimensions
    from public.historical_case_version_source_objects hcvso
    join public.historical_case_versions hcv
      on hcv.id = hcvso.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-930'
      and hcvso.source_locator = 'Case 01 - Curated Narrative Section'
  $sql$,
  $sql$
    values
      (array['identity', 'date']::text[])
  $sql$,
  'supported_claim_dimensions preserves the governed support dimensions'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_source_objects (
      historical_case_version_id,
      source_object_id,
      evidence_role_id,
      confidentiality_level_id,
      evidence_strength,
      source_locator,
      supported_claim_dimensions
    )
    select
      hcv.id,
      kso.id,
      hcer.id,
      kcl.id,
      'strong',
      'Unknown support dimension locator',
      array['timeline']::text[]
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join public.knowledge_source_objects kso
    cross join public.historical_case_evidence_roles hcer
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-930'
      and hcv.version_number = 1
      and kso.manual_reference_key = 'MANUAL-HIST-6B-SECONDARY'
      and hcer.role_code = 'secondary_supporting_evidence'
      and kcl.level_code = 'internal';
  $sql$,
  '23514',
  null,
  'unrecognized support dimensions are rejected'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_source_objects (
      historical_case_version_id,
      source_object_id,
      evidence_role_id,
      confidentiality_level_id,
      evidence_strength,
      source_locator,
      supported_claim_dimensions
    )
    select
      hcv.id,
      kso.id,
      hcer.id,
      kcl.id,
      'strong',
      'Duplicate support dimension locator',
      array['identity', 'identity']::text[]
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join public.knowledge_source_objects kso
    cross join public.historical_case_evidence_roles hcer
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-930'
      and hcv.version_number = 1
      and kso.manual_reference_key = 'MANUAL-HIST-6B-SECONDARY'
      and hcer.role_code = 'secondary_supporting_evidence'
      and kcl.level_code = 'internal';
  $sql$,
  '23514',
  null,
  'duplicate support dimensions are rejected'
);

select results_eq(
  $sql$
    select case_conf.level_code, evidence_conf.level_code
    from public.historical_case_version_source_objects hcvso
    join public.historical_case_versions hcv
      on hcv.id = hcvso.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    join public.knowledge_confidentiality_levels case_conf
      on case_conf.id = hcv.confidentiality_level_id
    join public.knowledge_confidentiality_levels evidence_conf
      on evidence_conf.id = hcvso.confidentiality_level_id
    where hc.case_code = 'HC-930'
      and hcvso.source_locator = 'Case 01 - Curated Narrative Section'
  $sql$,
  $sql$
    values
      ('internal'::text, 'restricted'::text)
  $sql$,
  'evidence confidentiality may be stricter than the parent case version confidentiality'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_source_objects (
      historical_case_version_id,
      source_object_id,
      evidence_role_id,
      confidentiality_level_id,
      evidence_strength,
      source_locator,
      supported_claim_dimensions
    )
    select
      hcv.id,
      kso.id,
      hcer.id,
      kcl.id,
      'weak',
      'Invalid evidence strength locator',
      array['context']::text[]
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join public.knowledge_source_objects kso
    cross join public.historical_case_evidence_roles hcer
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-930'
      and hcv.version_number = 1
      and kso.manual_reference_key = 'MANUAL-HIST-6B-SECONDARY'
      and hcer.role_code = 'secondary_supporting_evidence'
      and kcl.level_code = 'internal';
  $sql$,
  '23514',
  null,
  'invalid evidence_strength values are rejected'
);

select lives_ok(
  $sql$
    update public.historical_case_version_source_objects hcvso
    set relationship_notes = 'Updated while the parent case version remains draft.'
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hcvso.historical_case_version_id = hcv.id
      and hc.case_code = 'HC-930'
      and hcvso.source_locator = 'Agreement appendix page 2';
  $sql$,
  'draft historical case evidence associations may be edited'
);

select lives_ok(
  $sql$
    update public.historical_case_versions hcv
    set governance_status = 'active'
    from public.historical_cases hc
    where hc.id = hcv.historical_case_id
      and hc.case_code = 'HC-932'
      and hcv.version_number = 1;
  $sql$,
  'a draft case version can be activated after its evidence set is assembled'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_source_objects (
      historical_case_version_id,
      source_object_id,
      evidence_role_id,
      confidentiality_level_id,
      evidence_strength,
      source_locator,
      supported_claim_dimensions
    )
    select
      hcv.id,
      kso.id,
      hcer.id,
      kcl.id,
      'moderate',
      'Attempted post-activation evidence insert',
      array['context']::text[]
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join public.knowledge_source_objects kso
    cross join public.historical_case_evidence_roles hcer
    cross join public.knowledge_confidentiality_levels kcl
    where hc.case_code = 'HC-932'
      and hcv.version_number = 1
      and kso.manual_reference_key = 'MANUAL-HIST-6B-SECONDARY'
      and hcer.role_code = 'secondary_supporting_evidence'
      and kcl.level_code = 'internal';
  $sql$,
  '23514',
  null,
  'active historical case versions cannot receive new evidence associations in place'
);

select throws_ok(
  $sql$
    update public.historical_case_version_source_objects hcvso
    set relationship_notes = 'Attempted update after activation should fail.'
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hcvso.historical_case_version_id = hcv.id
      and hc.case_code = 'HC-932'
      and hcvso.source_locator = 'Case C - Primary Evidence';
  $sql$,
  '23514',
  null,
  'active historical case evidence associations cannot be materially changed'
);

select throws_ok(
  $sql$
    delete from public.historical_case_version_source_objects hcvso
    using public.historical_case_versions hcv,
          public.historical_cases hc
    where hcvso.historical_case_version_id = hcv.id
      and hcv.historical_case_id = hc.id
      and hc.case_code = 'HC-932'
      and hcvso.source_locator = 'Case C - Primary Evidence';
  $sql$,
  '23514',
  null,
  'active historical case evidence associations cannot be silently deleted'
);

select lives_ok(
  $sql$
    do $$
    declare
      internal_confidentiality_id bigint;
      primary_role_id bigint;
      superseded_version_id bigint;
      case_id bigint;
      new_draft_version_id bigint;
      secondary_source_object_id bigint;
    begin
      select hc.id into case_id
      from public.historical_cases hc
      where hc.case_code = 'HC-932';

      select hcv.id into superseded_version_id
      from public.historical_case_versions hcv
      where hcv.historical_case_id = case_id
        and hcv.version_number = 1;

      select id into internal_confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      select id into primary_role_id
      from public.historical_case_evidence_roles
      where role_code = 'primary_supporting_evidence';

      select id into secondary_source_object_id
      from public.knowledge_source_objects
      where manual_reference_key = 'MANUAL-HIST-6B-SECONDARY';

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
        case_id,
        2,
        'draft',
        'active',
        'full_case',
        'strong',
        'completed',
        'unknown',
        'Superseding draft with expanded evidence set.',
        internal_confidentiality_id,
        false,
        superseded_version_id
      )
      returning id into new_draft_version_id;

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
        new_draft_version_id,
        secondary_source_object_id,
        primary_role_id,
        internal_confidentiality_id,
        'moderate',
        'New evidence added on superseding draft version',
        array['context', 'lesson']::text[],
        'New evidence is attached to the new draft version instead of mutating the active snapshot.'
      );
    end
    $$;
  $sql$,
  'new evidence can be attached to a superseding draft case version'
);

select results_eq(
  $sql$
    select c.relname
    from pg_class c
    join pg_namespace n
      on n.oid = c.relnamespace
    where n.nspname = 'public'
      and c.relname in ('historical_case_evidence_roles', 'historical_case_version_source_objects')
      and c.relrowsecurity
    order by c.relname
  $sql$,
  $sql$
    values
      ('historical_case_evidence_roles'::name),
      ('historical_case_version_source_objects'::name)
  $sql$,
  'RLS is enabled on the Phase 6.2B evidence tables'
);

select is(
  (
    select count(*)
    from information_schema.role_table_grants rtg
    where rtg.table_schema = 'public'
      and rtg.table_name in ('historical_case_evidence_roles', 'historical_case_version_source_objects')
      and rtg.grantee in ('anon', 'authenticated', 'service_role')
      and rtg.privilege_type in ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'REFERENCES', 'TRIGGER', 'TRUNCATE')
  ),
  0::bigint,
  'ordinary roles have no direct grants on the Phase 6.2B evidence tables'
);

select throws_ok(
  $sql$
    select public._test_count_as('anon', $query$select * from public.historical_case_evidence_roles$query$);
  $sql$,
  '42501',
  null,
  'anon cannot directly read historical_case_evidence_roles'
);

select throws_ok(
  $sql$
    select public._test_count_as('authenticated', $query$select * from public.historical_case_version_source_objects$query$);
  $sql$,
  '42501',
  null,
  'authenticated cannot directly read historical_case_version_source_objects'
);

select *
from finish();

rollback;
