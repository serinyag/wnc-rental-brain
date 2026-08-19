begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

select plan(71);

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
  to_regclass('public.historical_case_version_responsibilities') is not null,
  'historical_case_version_responsibilities table exists'
);

select ok(
  to_regclass('public.historical_case_version_decisions') is not null,
  'historical_case_version_decisions table exists'
);

select ok(
  to_regclass('public.historical_case_version_lessons') is not null,
  'historical_case_version_lessons table exists'
);

select ok(
  to_regclass('public.historical_case_version_responsibility_sources') is not null,
  'historical_case_version_responsibility_sources table exists'
);

select ok(
  to_regclass('public.historical_case_version_decision_sources') is not null,
  'historical_case_version_decision_sources table exists'
);

select ok(
  to_regclass('public.historical_case_version_lesson_sources') is not null,
  'historical_case_version_lesson_sources table exists'
);

select lives_ok(
  $sql$
    do $$
    declare
      internal_confidentiality_id bigint;
      restricted_confidentiality_id bigint;
      primary_role_id bigint;
      secondary_role_id bigint;
      governance_category_id bigint;
      case_950_id bigint;
      case_951_id bigint;
      case_952_id bigint;
      case_953_id bigint;
      case_954_id bigint;
      case_950_version_id bigint;
      case_951_version_id bigint;
      case_952_version_id bigint;
      case_953_version_id bigint;
      case_954_version_id bigint;
      shared_source_object_id bigint;
      responsibility_source_object_id bigint;
      other_case_source_object_id bigint;
      activation_source_object_id bigint;
      active_source_object_id bigint;
      summary_source_object_id bigint;
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

      select id into governance_category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      insert into public.logical_rules (
        rule_code,
        rule_domain
      )
      values (
        'P6D_RULE_A',
        'testing'
      );

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'P6D-DOC-A',
        'Phase 6.2D Current Guidance Fixture',
        governance_category_id
      );

      insert into public.historical_cases (
        case_code,
        canonical_title
      )
      values
        ('HC-950', 'Historical Statement Draft Fixture'),
        ('HC-951', 'Historical Statement Cross-Version Fixture'),
        ('HC-952', 'Historical Statement Activation Fixture'),
        ('HC-953', 'Historical Statement Immutability Fixture'),
        ('HC-954', 'Historical Statement Summary Fixture');

      select id into case_950_id from public.historical_cases where case_code = 'HC-950';
      select id into case_951_id from public.historical_cases where case_code = 'HC-951';
      select id into case_952_id from public.historical_cases where case_code = 'HC-952';
      select id into case_953_id from public.historical_cases where case_code = 'HC-953';
      select id into case_954_id from public.historical_cases where case_code = 'HC-954';

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
        (case_950_id, 1, 'draft', 'active', 'full_case', 'strong', 'completed', 'unknown', 'Draft fixture for governed statement coverage.', internal_confidentiality_id, false),
        (case_951_id, 1, 'draft', 'limited', 'limited_precedent', 'moderate', 'partial_or_unclear', 'unknown', 'Cross-version fixture for provenance enforcement.', internal_confidentiality_id, false),
        (case_952_id, 1, 'draft', 'active', 'full_case', 'strong', 'completed', 'unknown', 'Activation fixture for provenance enforcement.', internal_confidentiality_id, false),
        (case_953_id, 1, 'draft', 'active', 'full_case', 'strong', 'completed', 'unknown', 'Immutability fixture prepared while still draft.', internal_confidentiality_id, false),
        (case_954_id, 1, 'draft', 'limited', 'cautionary_precedent', 'moderate', 'partial_or_unclear', 'unknown', 'Summary fixture for historical-value aggregation.', restricted_confidentiality_id, false);

      select id into case_950_version_id
      from public.historical_case_versions
      where historical_case_id = case_950_id
        and version_number = 1;

      select id into case_951_version_id
      from public.historical_case_versions
      where historical_case_id = case_951_id
        and version_number = 1;

      select id into case_952_version_id
      from public.historical_case_versions
      where historical_case_id = case_952_id
        and version_number = 1;

      select id into case_953_version_id
      from public.historical_case_versions
      where historical_case_id = case_953_id
        and version_number = 1;

      select id into case_954_version_id
      from public.historical_case_versions
      where historical_case_id = case_954_id
        and version_number = 1;

      insert into public.knowledge_source_objects (
        origin_type,
        manual_reference_key,
        original_filename
      )
      values
        ('manual_reference', 'MANUAL-HIST-6D-SHARED', 'historical-statement-shared.txt'),
        ('manual_reference', 'MANUAL-HIST-6D-RESP', 'historical-statement-responsibility.txt'),
        ('manual_reference', 'MANUAL-HIST-6D-OTHER', 'historical-statement-other-case.txt'),
        ('manual_reference', 'MANUAL-HIST-6D-ACTIVATION', 'historical-statement-activation.txt'),
        ('manual_reference', 'MANUAL-HIST-6D-ACTIVE', 'historical-statement-active.txt'),
        ('manual_reference', 'MANUAL-HIST-6D-SUMMARY', 'historical-statement-summary.txt');

      select id into shared_source_object_id
      from public.knowledge_source_objects
      where manual_reference_key = 'MANUAL-HIST-6D-SHARED';

      select id into responsibility_source_object_id
      from public.knowledge_source_objects
      where manual_reference_key = 'MANUAL-HIST-6D-RESP';

      select id into other_case_source_object_id
      from public.knowledge_source_objects
      where manual_reference_key = 'MANUAL-HIST-6D-OTHER';

      select id into activation_source_object_id
      from public.knowledge_source_objects
      where manual_reference_key = 'MANUAL-HIST-6D-ACTIVATION';

      select id into active_source_object_id
      from public.knowledge_source_objects
      where manual_reference_key = 'MANUAL-HIST-6D-ACTIVE';

      select id into summary_source_object_id
      from public.knowledge_source_objects
      where manual_reference_key = 'MANUAL-HIST-6D-SUMMARY';

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
          case_950_version_id,
          shared_source_object_id,
          primary_role_id,
          restricted_confidentiality_id,
          'strong',
          'Case 950 - Shared Core Evidence',
          array['responsibility', 'decision', 'lesson', 'context']::text[],
          'Shared case-library section supporting multiple governed statement families.'
        ),
        (
          case_950_version_id,
          shared_source_object_id,
          secondary_role_id,
          internal_confidentiality_id,
          'moderate',
          'Case 950 - Decision Appendix',
          array['decision', 'lesson']::text[],
          'Decision-specific appendix for the same draft case version.'
        ),
        (
          case_950_version_id,
          responsibility_source_object_id,
          secondary_role_id,
          internal_confidentiality_id,
          'moderate',
          'Case 950 - Responsibility Ledger',
          array['responsibility', 'context']::text[],
          'Separate responsibility support for the draft case version.'
        ),
        (
          case_951_version_id,
          other_case_source_object_id,
          primary_role_id,
          internal_confidentiality_id,
          'strong',
          'Case 951 - Shared Core Evidence',
          array['responsibility', 'decision', 'lesson']::text[],
          'Distinct evidence attached to a different historical case version.'
        ),
        (
          case_952_version_id,
          activation_source_object_id,
          primary_role_id,
          internal_confidentiality_id,
          'strong',
          'Case 952 - Decision Evidence',
          array['decision']::text[],
          'Decision evidence reserved for the activation validation fixture.'
        ),
        (
          case_953_version_id,
          active_source_object_id,
          primary_role_id,
          internal_confidentiality_id,
          'strong',
          'Case 953 - Full Evidence',
          array['responsibility', 'decision', 'lesson']::text[],
          'Single shared evidence association used before the immutability fixture activates.'
        ),
        (
          case_954_version_id,
          summary_source_object_id,
          primary_role_id,
          restricted_confidentiality_id,
          'moderate',
          'Case 954 - Summary Evidence',
          array['responsibility', 'decision', 'lesson']::text[],
          'Source association used to exercise historical-value summary behavior.'
        );
    end
    $$;
  $sql$,
  'Phase 6.2D fixtures can be created with governed case versions and supporting evidence associations'
);

select lives_ok(
  $sql$
    do $$
    declare
      target_historical_case_version_id bigint;
    begin
      select hcv.id into target_historical_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-950'
        and hcv.version_number = 1;

      insert into public.historical_case_version_responsibilities (
        historical_case_version_id,
        actor_type,
        responsibility_statement,
        evidence_strength,
        historical_value_only,
        contamination_risk_level,
        current_authority_disposition
      )
      values
        (target_historical_case_version_id, 'wnc', 'WNC cleared agreed venue areas before handover.', 'strong', false, 'medium', 'check_phase_4'),
        (target_historical_case_version_id, 'wnc', 'WNC coordinated agreed setup support before guest arrival.', 'moderate', false, 'low', 'no_current_rule_implication'),
        (target_historical_case_version_id, 'client', 'Client operated guest-facing event activity after handover.', 'strong', false, 'medium', 'check_phase_4'),
        (target_historical_case_version_id, 'external_supplier', 'External caterer handled food service during the event window.', 'moderate', false, 'medium', 'check_phase_5');
    end
    $$;
  $sql$,
  'valid WNC, client, and external-supplier responsibility statements are accepted on a draft case version'
);

select is(
  (
    select count(*)
    from public.historical_case_version_responsibilities hcvr
    join public.historical_case_versions hcv
      on hcv.id = hcvr.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-950'
      and hcvr.actor_type = 'wnc'
  ),
  2::bigint,
  'valid WNC responsibility statements are accepted and multiple responsibilities per actor are allowed'
);

select is(
  (
    select count(*)
    from public.historical_case_version_responsibilities hcvr
    join public.historical_case_versions hcv
      on hcv.id = hcvr.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-950'
      and hcvr.actor_type = 'client'
  ),
  1::bigint,
  'valid client responsibility statements are accepted'
);

select is(
  (
    select count(*)
    from public.historical_case_version_responsibilities hcvr
    join public.historical_case_versions hcv
      on hcv.id = hcvr.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-950'
      and hcvr.actor_type = 'external_supplier'
  ),
  1::bigint,
  'valid external-supplier responsibility statements are accepted'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_responsibilities (
      historical_case_version_id,
      actor_type,
      responsibility_statement,
      evidence_strength,
      historical_value_only,
      contamination_risk_level,
      current_authority_disposition
    )
    select
      hcv.id,
      'supplier_contact',
      'Invalid actor type should fail.',
      'moderate',
      false,
      'medium',
      'check_phase_5'
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-950'
      and hcv.version_number = 1;
  $sql$,
  '23514',
  null,
  'invalid responsibility actor types are rejected'
);

select is(
  (
    select count(*)
    from public.historical_case_version_responsibilities hcvr
    join public.historical_case_versions hcv
      on hcv.id = hcvr.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-950'
      and hcvr.actor_type = 'wnc'
        and hcvr.evidence_strength in ('strong', 'moderate')
  ),
  2::bigint,
  'multiple responsibilities per actor are preserved on the same draft case version'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_responsibilities (
      historical_case_version_id,
      actor_type,
      responsibility_statement,
      evidence_strength,
      historical_value_only,
      contamination_risk_level,
      current_authority_disposition
    )
    values (
      999999999,
      'wnc',
      'Missing parent case version should fail.',
      'strong',
      false,
      'low',
      'no_current_rule_implication'
    );
  $sql$,
  '23503',
  null,
  'responsibility statements must belong to a valid historical case version'
);

select lives_ok(
  $sql$
    do $$
    declare
      target_historical_case_version_id bigint;
    begin
      select hcv.id into target_historical_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-950'
        and hcv.version_number = 1;

      insert into public.historical_case_version_decisions (
        historical_case_version_id,
        decision_statement,
        historical_context,
        evidence_strength,
        historical_value_only,
        contamination_risk_level,
        current_authority_disposition
      )
      values
        (target_historical_case_version_id, 'Decision disposition phase 4', 'Responsibility boundary decision.', 'strong', false, 'medium', 'check_phase_4'),
        (target_historical_case_version_id, 'Decision disposition phase 5', 'Supplier coordination decision.', 'moderate', false, 'medium', 'check_phase_5'),
        (target_historical_case_version_id, 'Decision disposition both phases', 'Cross-domain decision.', 'moderate', false, 'high', 'check_phase_4_and_5'),
        (target_historical_case_version_id, 'Decision disposition conflict', 'Historically useful but potentially conflicting decision.', 'limited', true, 'high', 'potential_conflict_with_current_knowledge'),
        (target_historical_case_version_id, 'Decision disposition unknown', 'Unclear current-status routing.', 'limited', true, 'medium', 'current_status_unknown'),
        (target_historical_case_version_id, 'Decision disposition none', 'Event-specific decision with no current-rule implication.', 'strong', false, 'low', 'no_current_rule_implication');
    end
    $$;
  $sql$,
  'decisions can be created on a draft case version with valid contamination metadata'
);

select is(
  (
    select historical_value_only
    from public.historical_case_version_decisions hcvd
    join public.historical_case_versions hcv
      on hcv.id = hcvd.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-950'
      and hcvd.decision_statement = 'Decision disposition conflict'
  ),
  true,
  'historical_value_only persists on decision statements'
);

select results_eq(
  $sql$
    select distinct contamination_risk_level
    from public.historical_case_version_decisions hcvd
    join public.historical_case_versions hcv
      on hcv.id = hcvd.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-950'
      and hcvd.decision_statement like 'Decision disposition %'
    order by contamination_risk_level
  $sql$,
  $sql$
    values
      ('high'::text),
      ('low'::text),
      ('medium'::text)
  $sql$,
  'valid contamination risk levels are accepted on decision statements'
);

select results_eq(
  $sql$
    select current_authority_disposition
    from public.historical_case_version_decisions hcvd
    join public.historical_case_versions hcv
      on hcv.id = hcvd.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-950'
      and hcvd.decision_statement like 'Decision disposition %'
    order by current_authority_disposition
  $sql$,
  $sql$
    values
      ('check_phase_4'::text),
      ('check_phase_4_and_5'::text),
      ('check_phase_5'::text),
      ('current_status_unknown'::text),
      ('no_current_rule_implication'::text),
      ('potential_conflict_with_current_knowledge'::text)
  $sql$,
  'all approved current-authority dispositions are accepted on decision statements'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_decisions (
      historical_case_version_id,
      decision_statement,
      evidence_strength,
      historical_value_only,
      contamination_risk_level,
      current_authority_disposition
    )
    select
      hcv.id,
      'Invalid contamination risk',
      'strong',
      false,
      'critical',
      'check_phase_4'
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-950'
      and hcv.version_number = 1;
  $sql$,
  '23514',
  null,
  'invalid contamination risk levels are rejected on decision statements'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_decisions (
      historical_case_version_id,
      decision_statement,
      evidence_strength,
      historical_value_only,
      contamination_risk_level,
      current_authority_disposition
    )
    select
      hcv.id,
      'Invalid disposition',
      'strong',
      false,
      'medium',
      'check_phase_6'
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-950'
      and hcv.version_number = 1;
  $sql$,
  '23514',
  null,
  'invalid current-authority dispositions are rejected on decision statements'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_decisions (
      historical_case_version_id,
      decision_statement,
      evidence_strength,
      historical_value_only,
      contamination_risk_level,
      current_authority_disposition
    )
    select
      hcv.id,
      'Contradictory contamination metadata',
      'strong',
      true,
      'high',
      'no_current_rule_implication'
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-950'
      and hcv.version_number = 1;
  $sql$,
  '23514',
  null,
  'cross-field contamination validation rejects high-risk statements marked as having no current-rule implication'
);

select lives_ok(
  $sql$
    do $$
    declare
      target_historical_case_version_id bigint;
    begin
      select hcv.id into target_historical_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-950'
        and hcv.version_number = 1;

      insert into public.historical_case_version_lessons (
        historical_case_version_id,
        lesson_kind,
        lesson_statement,
        evidence_strength,
        historical_value_only,
        contamination_risk_level,
        current_authority_disposition
      )
      values
        (target_historical_case_version_id, 'source_explicit', 'Lesson kind source explicit.', 'strong', false, 'medium', 'check_phase_5'),
        (target_historical_case_version_id, 'curated_lesson', 'Lesson kind curated lesson.', 'moderate', false, 'medium', 'check_phase_4_and_5'),
        (target_historical_case_version_id, 'analyst_inference', 'Lesson kind analyst inference.', 'limited', false, 'medium', 'current_status_unknown'),
        (target_historical_case_version_id, 'caution_warning', 'Lesson kind caution warning.', 'strong', true, 'high', 'potential_conflict_with_current_knowledge');
    end
    $$;
  $sql$,
  'all four approved lesson kinds are accepted on draft case versions'
);

select results_eq(
  $sql$
    select lesson_kind
    from public.historical_case_version_lessons hcvl
    join public.historical_case_versions hcv
      on hcv.id = hcvl.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-950'
      and hcvl.lesson_statement like 'Lesson kind %'
    order by lesson_kind
  $sql$,
  $sql$
    values
      ('analyst_inference'::text),
      ('caution_warning'::text),
      ('curated_lesson'::text),
      ('source_explicit'::text)
  $sql$,
  'all approved lesson kinds persist distinctly'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_lessons (
      historical_case_version_id,
      lesson_kind,
      lesson_statement,
      evidence_strength,
      historical_value_only,
      contamination_risk_level,
      current_authority_disposition
    )
    select
      hcv.id,
      'warning',
      'Invalid lesson kind should fail.',
      'strong',
      false,
      'medium',
      'check_phase_5'
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-950'
      and hcv.version_number = 1;
  $sql$,
  '23514',
  null,
  'invalid lesson kinds are rejected'
);

select is(
  (
    select count(*)
    from public.historical_case_version_lessons hcvl
    join public.historical_case_versions hcv
      on hcv.id = hcvl.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-950'
      and hcvl.lesson_kind = 'analyst_inference'
      and hcvl.lesson_statement = 'Lesson kind analyst inference.'
  ),
  1::bigint,
  'analyst inference remains explicitly typed on lesson rows'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_lessons (
      historical_case_version_id,
      lesson_kind,
      lesson_statement,
      evidence_strength,
      historical_value_only,
      contamination_risk_level,
      current_authority_disposition
    )
    select
      hcv.id,
      'caution_warning',
      'Invalid lesson contamination metadata should fail.',
      'moderate',
      true,
      'high',
      'no_current_rule_implication'
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-950'
      and hcv.version_number = 1;
  $sql$,
  '23514',
  null,
  'lesson contamination controls reject contradictory high-risk no-current-implication combinations'
);

select lives_ok(
  $sql$
    insert into public.historical_case_version_responsibility_sources (
      historical_case_version_id,
      responsibility_id,
      historical_case_version_source_object_id
    )
    select
      hcv.id,
      hcvr.id,
      hcvso.id
    from public.historical_case_version_responsibilities hcvr
    join public.historical_case_versions hcv
      on hcv.id = hcvr.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    join public.historical_case_version_source_objects hcvso
      on hcvso.historical_case_version_id = hcv.id
     and hcvso.source_locator = 'Case 950 - Shared Core Evidence'
    where hc.case_code = 'HC-950'
      and hcvr.responsibility_statement = 'WNC cleared agreed venue areas before handover.';
  $sql$,
  'a responsibility statement can link to a version-scoped evidence association'
);

select lives_ok(
  $sql$
    do $$
    declare
      target_historical_case_version_id bigint;
      decision_id bigint;
      primary_source_id bigint;
      secondary_source_id bigint;
    begin
      select hcv.id into target_historical_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-950'
        and hcv.version_number = 1;

      select hcvd.id into decision_id
      from public.historical_case_version_decisions hcvd
      where hcvd.historical_case_version_id = target_historical_case_version_id
        and hcvd.decision_statement = 'Decision disposition phase 5';

      select hcvso.id into primary_source_id
      from public.historical_case_version_source_objects hcvso
      where hcvso.historical_case_version_id = target_historical_case_version_id
        and hcvso.source_locator = 'Case 950 - Shared Core Evidence';

      select hcvso.id into secondary_source_id
      from public.historical_case_version_source_objects hcvso
      where hcvso.historical_case_version_id = target_historical_case_version_id
        and hcvso.source_locator = 'Case 950 - Decision Appendix';

      insert into public.historical_case_version_decision_sources (
        historical_case_version_id,
        decision_id,
        historical_case_version_source_object_id
      )
      values
        (target_historical_case_version_id, decision_id, primary_source_id),
        (target_historical_case_version_id, decision_id, secondary_source_id);
    end
    $$;
  $sql$,
  'a decision statement can link to multiple version-scoped evidence associations'
);

select lives_ok(
  $sql$
    insert into public.historical_case_version_lesson_sources (
      historical_case_version_id,
      lesson_id,
      historical_case_version_source_object_id
    )
    select
      hcv.id,
      hcvl.id,
      hcvso.id
    from public.historical_case_version_lessons hcvl
    join public.historical_case_versions hcv
      on hcv.id = hcvl.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    join public.historical_case_version_source_objects hcvso
      on hcvso.historical_case_version_id = hcv.id
     and hcvso.source_locator = 'Case 950 - Shared Core Evidence'
    where hc.case_code = 'HC-950'
      and hcvl.lesson_statement = 'Lesson kind source explicit.';
  $sql$,
  'a lesson statement can link to a version-scoped evidence association'
);

select is(
  (
    select count(*)
    from public.historical_case_version_decision_sources hcvds
    join public.historical_case_version_decisions hcvd
      on hcvd.id = hcvds.decision_id
    join public.historical_case_versions hcv
      on hcv.id = hcvds.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-950'
      and hcvd.decision_statement = 'Decision disposition phase 5'
  ),
  2::bigint,
  'multiple evidence associations can support one decision statement'
);

select is(
  (
    select
      (
        select count(*)
        from public.historical_case_version_responsibility_sources hcvrs
        where hcvrs.historical_case_version_source_object_id = hcvso.id
      )
      +
      (
        select count(*)
        from public.historical_case_version_decision_sources hcvds
        where hcvds.historical_case_version_source_object_id = hcvso.id
      )
      +
      (
        select count(*)
        from public.historical_case_version_lesson_sources hcvls
        where hcvls.historical_case_version_source_object_id = hcvso.id
      )
    from public.historical_case_version_source_objects hcvso
    join public.historical_case_versions hcv
      on hcv.id = hcvso.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-950'
      and hcvso.source_locator = 'Case 950 - Shared Core Evidence'
  ),
  3::bigint,
  'one evidence association may support statements across responsibility, decision, and lesson families'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_responsibility_sources (
      historical_case_version_id,
      responsibility_id,
      historical_case_version_source_object_id
    )
    select
      hcv.id,
      hcvr.id,
      hcvso.id
    from public.historical_case_version_responsibilities hcvr
    join public.historical_case_versions hcv
      on hcv.id = hcvr.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    join public.historical_case_version_source_objects hcvso
      on hcvso.historical_case_version_id = hcv.id
     and hcvso.source_locator = 'Case 950 - Shared Core Evidence'
    where hc.case_code = 'HC-950'
      and hcvr.responsibility_statement = 'WNC cleared agreed venue areas before handover.';
  $sql$,
  '23505',
  null,
  'duplicate responsibility evidence links are rejected'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_responsibility_sources (
      historical_case_version_id,
      responsibility_id,
      historical_case_version_source_object_id
    )
    select
      hcv.id,
      hcvr.id,
      hcvso.id
    from public.historical_case_version_responsibilities hcvr
    join public.historical_case_versions hcv
      on hcv.id = hcvr.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join lateral (
      select hcvso.id
      from public.historical_case_version_source_objects hcvso
      join public.historical_case_versions cross_hcv
        on cross_hcv.id = hcvso.historical_case_version_id
      join public.historical_cases cross_hc
        on cross_hc.id = cross_hcv.historical_case_id
      where cross_hc.case_code = 'HC-951'
        and hcvso.source_locator = 'Case 951 - Shared Core Evidence'
    ) hcvso
    where hc.case_code = 'HC-950'
      and hcvr.responsibility_statement = 'Client operated guest-facing event activity after handover.';
  $sql$,
  '23503',
  null,
  'statement evidence links cannot point to evidence associations from another historical case version'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_responsibility_sources (
      historical_case_version_id,
      responsibility_id,
      historical_case_version_source_object_id
    )
    select
      hcv.id,
      hcvr.id,
      hcvso.id
    from public.historical_case_version_responsibilities hcvr
    join public.historical_case_versions hcv
      on hcv.id = hcvr.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    join public.historical_case_version_source_objects hcvso
      on hcvso.historical_case_version_id = hcv.id
     and hcvso.source_locator = 'Case 950 - Decision Appendix'
    where hc.case_code = 'HC-950'
      and hcvr.responsibility_statement = 'External caterer handled food service during the event window.';
  $sql$,
  '23514',
  null,
  'statement evidence links must use a source association that supports the matching claim dimension'
);

select is(
  (
    select count(*)
    from public.historical_case_version_decisions hcvd
    join public.historical_case_versions hcv
      on hcv.id = hcvd.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-952'
  ),
  0::bigint,
  'activation fixture starts with no governed statements'
);

select throws_ok(
  $sql$
    do $$
    declare
      target_historical_case_version_id bigint;
    begin
      select hcv.id into target_historical_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-952'
        and hcv.version_number = 1;

      insert into public.historical_case_version_decisions (
        historical_case_version_id,
        decision_statement,
        evidence_strength,
        historical_value_only,
        contamination_risk_level,
        current_authority_disposition
      )
      values (
        target_historical_case_version_id,
        'Activation fixture decision without provenance',
        'strong',
        false,
        'medium',
        'check_phase_5'
      );

      update public.historical_case_versions
      set governance_status = 'active'
      where id = target_historical_case_version_id;
    end
    $$;
  $sql$,
  '23514',
  null,
  'activation fails when a governed statement lacks supporting provenance'
);

select lives_ok(
  $sql$
    do $$
    declare
      target_historical_case_version_id bigint;
      decision_id bigint;
      source_association_id bigint;
      knowledge_document_id bigint;
      relationship_type_id bigint;
    begin
      select hcv.id into target_historical_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-952'
        and hcv.version_number = 1;

      insert into public.historical_case_version_decisions (
        historical_case_version_id,
        decision_statement,
        evidence_strength,
        historical_value_only,
        contamination_risk_level,
        current_authority_disposition
      )
      values (
        target_historical_case_version_id,
        'Activation fixture decision without provenance',
        'strong',
        false,
        'medium',
        'check_phase_5'
      )
      returning id into decision_id;

      select hcvso.id into source_association_id
      from public.historical_case_version_source_objects hcvso
      where hcvso.historical_case_version_id = target_historical_case_version_id
        and hcvso.source_locator = 'Case 952 - Decision Evidence';

      insert into public.historical_case_version_decision_sources (
        historical_case_version_id,
        decision_id,
        historical_case_version_source_object_id
      )
      values (
        target_historical_case_version_id,
        decision_id,
        source_association_id
      );

      select kd.id into knowledge_document_id
      from public.knowledge_documents kd
      where kd.document_code = 'P6D-DOC-A';

      select hckrt.id into relationship_type_id
      from public.historical_case_knowledge_relationship_types hckrt
      where hckrt.relationship_code = 'current_guidance_to_consult';

      insert into public.historical_case_version_knowledge_documents (
        historical_case_version_id,
        knowledge_document_id,
        relationship_type_id
      )
      values (
        target_historical_case_version_id,
        knowledge_document_id,
        relationship_type_id
      );

      update public.historical_case_versions
      set governance_status = 'active'
      where id = target_historical_case_version_id;
    end
    $$;
  $sql$,
  'activation succeeds once required statement provenance has been added'
);

select is(
  (
    select contains_historical_value_only_content
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-954'
      and hcv.version_number = 1
  ),
  false,
  'summary fixture starts with no historical-value-only statements and a false summary flag'
);

select lives_ok(
  $sql$
    do $$
    declare
      target_historical_case_version_id bigint;
      decision_id bigint;
      source_association_id bigint;
    begin
      select hcv.id into target_historical_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-954'
        and hcv.version_number = 1;

      insert into public.historical_case_version_decisions (
        historical_case_version_id,
        decision_statement,
        evidence_strength,
        historical_value_only,
        contamination_risk_level,
        current_authority_disposition
      )
      values (
        target_historical_case_version_id,
        'Summary fixture historical-value decision',
        'moderate',
        true,
        'high',
        'potential_conflict_with_current_knowledge'
      )
      returning id into decision_id;

      select hcvso.id into source_association_id
      from public.historical_case_version_source_objects hcvso
      where hcvso.historical_case_version_id = target_historical_case_version_id
        and hcvso.source_locator = 'Case 954 - Summary Evidence';

      insert into public.historical_case_version_decision_sources (
        historical_case_version_id,
        decision_id,
        historical_case_version_source_object_id
      )
      values (
        target_historical_case_version_id,
        decision_id,
        source_association_id
      );
    end
    $$;
  $sql$,
  'a historical-value-only decision can be added to the summary fixture'
);

select is(
  (
    select contains_historical_value_only_content
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-954'
      and hcv.version_number = 1
  ),
  true,
  'a historical-value-only decision makes the case-version summary flag true'
);

select lives_ok(
  $sql$
    delete from public.historical_case_version_decisions hcvd
    using public.historical_case_versions hcv,
          public.historical_cases hc
    where hcvd.historical_case_version_id = hcv.id
      and hcv.historical_case_id = hc.id
      and hc.case_code = 'HC-954'
      and hcvd.decision_statement = 'Summary fixture historical-value decision';
  $sql$,
  'the historical-value-only decision can be removed while the case version is still draft'
);

select is(
  (
    select contains_historical_value_only_content
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-954'
      and hcv.version_number = 1
  ),
  false,
  'removing the last historical-value-only decision returns the summary flag to false'
);

select lives_ok(
  $sql$
    do $$
    declare
      target_historical_case_version_id bigint;
      lesson_id bigint;
      source_association_id bigint;
    begin
      select hcv.id into target_historical_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-954'
        and hcv.version_number = 1;

      insert into public.historical_case_version_lessons (
        historical_case_version_id,
        lesson_kind,
        lesson_statement,
        evidence_strength,
        historical_value_only,
        contamination_risk_level,
        current_authority_disposition
      )
      values (
        target_historical_case_version_id,
        'caution_warning',
        'Summary fixture historical-value lesson',
        'moderate',
        true,
        'high',
        'potential_conflict_with_current_knowledge'
      )
      returning id into lesson_id;

      select hcvso.id into source_association_id
      from public.historical_case_version_source_objects hcvso
      where hcvso.historical_case_version_id = target_historical_case_version_id
        and hcvso.source_locator = 'Case 954 - Summary Evidence';

      insert into public.historical_case_version_lesson_sources (
        historical_case_version_id,
        lesson_id,
        historical_case_version_source_object_id
      )
      values (
        target_historical_case_version_id,
        lesson_id,
        source_association_id
      );
    end
    $$;
  $sql$,
  'a historical-value-only lesson can be added to the summary fixture'
);

select is(
  (
    select contains_historical_value_only_content
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-954'
      and hcv.version_number = 1
  ),
  true,
  'a historical-value-only lesson also drives the case-version summary flag to true'
);

select lives_ok(
  $sql$
    delete from public.historical_case_version_lessons hcvl
    using public.historical_case_versions hcv,
          public.historical_cases hc
    where hcvl.historical_case_version_id = hcv.id
      and hcv.historical_case_id = hc.id
      and hc.case_code = 'HC-954'
      and hcvl.lesson_statement = 'Summary fixture historical-value lesson';
  $sql$,
  'the historical-value-only lesson can be removed while the case version is still draft'
);

select is(
  (
    select contains_historical_value_only_content
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-954'
      and hcv.version_number = 1
  ),
  false,
  'removing the last historical-value-only lesson returns the summary flag to false'
);

select lives_ok(
  $sql$
    do $$
    declare
      target_historical_case_version_id bigint;
      responsibility_id bigint;
      source_association_id bigint;
    begin
      select hcv.id into target_historical_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-954'
        and hcv.version_number = 1;

      insert into public.historical_case_version_responsibilities (
        historical_case_version_id,
        actor_type,
        responsibility_statement,
        evidence_strength,
        historical_value_only,
        contamination_risk_level,
        current_authority_disposition
      )
      values (
        target_historical_case_version_id,
        'wnc',
        'Summary fixture historical-value responsibility',
        'moderate',
        true,
        'medium',
        'check_phase_4'
      )
      returning id into responsibility_id;

      select hcvso.id into source_association_id
      from public.historical_case_version_source_objects hcvso
      where hcvso.historical_case_version_id = target_historical_case_version_id
        and hcvso.source_locator = 'Case 954 - Summary Evidence';

      insert into public.historical_case_version_responsibility_sources (
        historical_case_version_id,
        responsibility_id,
        historical_case_version_source_object_id
      )
      values (
        target_historical_case_version_id,
        responsibility_id,
        source_association_id
      );
    end
    $$;
  $sql$,
  'a historical-value-only responsibility can be added to the summary fixture'
);

select is(
  (
    select contains_historical_value_only_content
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-954'
      and hcv.version_number = 1
  ),
  true,
  'a historical-value-only responsibility also drives the case-version summary flag to true'
);

select lives_ok(
  $sql$
    update public.historical_case_versions hcv
    set
      curated_narrative = 'Summary fixture narrative updated while historical-value responsibility remains.',
      contains_historical_value_only_content = false
    from public.historical_cases hc
    where hc.id = hcv.historical_case_id
      and hc.case_code = 'HC-954'
      and hcv.version_number = 1;
  $sql$,
  'the parent case version can still be updated while draft even if a contradictory summary value is attempted'
);

select is(
  (
    select contains_historical_value_only_content
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-954'
      and hcv.version_number = 1
  ),
  true,
  'summary drift is corrected so the parent summary cannot silently contradict historical-value child statements'
);

select lives_ok(
  $sql$
    delete from public.historical_case_version_responsibilities hcvr
    using public.historical_case_versions hcv,
          public.historical_cases hc
    where hcvr.historical_case_version_id = hcv.id
      and hcv.historical_case_id = hc.id
      and hc.case_code = 'HC-954'
      and hcvr.responsibility_statement = 'Summary fixture historical-value responsibility';
  $sql$,
  'the historical-value-only responsibility can be removed while the case version is still draft'
);

select is(
  (
    select contains_historical_value_only_content
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-954'
      and hcv.version_number = 1
  ),
  false,
  'removing the last historical-value-only responsibility returns the summary flag to false'
);

select lives_ok(
  $sql$
    update public.historical_case_version_responsibilities hcvr
    set responsibility_statement = 'WNC cleared agreed venue areas and coordinated the final handover.'
    from public.historical_case_versions hcv,
         public.historical_cases hc
    where hcv.id = hcvr.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and hc.case_code = 'HC-950'
      and hcvr.responsibility_statement = 'WNC cleared agreed venue areas before handover.';
  $sql$,
  'draft responsibility statements can be updated before activation'
);

select lives_ok(
  $sql$
    do $$
    declare
      target_historical_case_version_id bigint;
    begin
      select hcv.id into target_historical_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-950'
        and hcv.version_number = 1;

      insert into public.historical_case_version_decisions (
        historical_case_version_id,
        decision_statement,
        evidence_strength,
        historical_value_only,
        contamination_risk_level,
        current_authority_disposition
      )
      values (
        target_historical_case_version_id,
        'Temporary draft decision for delete test',
        'limited',
        false,
        'low',
        'no_current_rule_implication'
      );

      delete from public.historical_case_version_decisions
      where historical_case_version_id = target_historical_case_version_id
        and decision_statement = 'Temporary draft decision for delete test';
    end
    $$;
  $sql$,
  'draft decision statements can be deleted before activation'
);

select lives_ok(
  $sql$
    do $$
    declare
      target_historical_case_version_id bigint;
    begin
      select hcv.id into target_historical_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-950'
        and hcv.version_number = 1;

      insert into public.historical_case_version_lessons (
        historical_case_version_id,
        lesson_kind,
        lesson_statement,
        evidence_strength,
        historical_value_only,
        contamination_risk_level,
        current_authority_disposition
      )
      values (
        target_historical_case_version_id,
        'curated_lesson',
        'Temporary draft lesson for delete test',
        'limited',
        false,
        'low',
        'no_current_rule_implication'
      );

      delete from public.historical_case_version_lessons
      where historical_case_version_id = target_historical_case_version_id
        and lesson_statement = 'Temporary draft lesson for delete test';
    end
    $$;
  $sql$,
  'draft lesson statements can be deleted before activation'
);

select lives_ok(
  $sql$
    do $$
    declare
      target_historical_case_version_id bigint;
      responsibility_id bigint;
      decision_id bigint;
      lesson_id bigint;
      source_association_id bigint;
      logical_rule_relationship_type_id bigint;
      knowledge_relationship_type_id bigint;
    begin
      select hcv.id into target_historical_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-953'
        and hcv.version_number = 1;

      insert into public.historical_case_version_responsibilities (
        historical_case_version_id,
        actor_type,
        responsibility_statement,
        evidence_strength,
        historical_value_only,
        contamination_risk_level,
        current_authority_disposition
      )
      values (
        target_historical_case_version_id,
        'wnc',
        'Active fixture responsibility',
        'strong',
        false,
        'medium',
        'check_phase_4'
      )
      returning id into responsibility_id;

      insert into public.historical_case_version_decisions (
        historical_case_version_id,
        decision_statement,
        evidence_strength,
        historical_value_only,
        contamination_risk_level,
        current_authority_disposition
      )
      values (
        target_historical_case_version_id,
        'Active fixture decision',
        'strong',
        false,
        'medium',
        'check_phase_5'
      )
      returning id into decision_id;

      insert into public.historical_case_version_lessons (
        historical_case_version_id,
        lesson_kind,
        lesson_statement,
        evidence_strength,
        historical_value_only,
        contamination_risk_level,
        current_authority_disposition
      )
      values (
        target_historical_case_version_id,
        'source_explicit',
        'Active fixture lesson',
        'strong',
        false,
        'medium',
        'check_phase_4_and_5'
      )
      returning id into lesson_id;

      select hcvso.id into source_association_id
      from public.historical_case_version_source_objects hcvso
      where hcvso.historical_case_version_id = target_historical_case_version_id
        and hcvso.source_locator = 'Case 953 - Full Evidence';

      insert into public.historical_case_version_responsibility_sources (
        historical_case_version_id,
        responsibility_id,
        historical_case_version_source_object_id
      )
      values (
        target_historical_case_version_id,
        responsibility_id,
        source_association_id
      );

      insert into public.historical_case_version_decision_sources (
        historical_case_version_id,
        decision_id,
        historical_case_version_source_object_id
      )
      values (
        target_historical_case_version_id,
        decision_id,
        source_association_id
      );

      insert into public.historical_case_version_lesson_sources (
        historical_case_version_id,
        lesson_id,
        historical_case_version_source_object_id
      )
      values (
        target_historical_case_version_id,
        lesson_id,
        source_association_id
      );

      select hcrrt.id into logical_rule_relationship_type_id
      from public.historical_case_rule_relationship_types hcrrt
      where hcrrt.relationship_code = 'relevant_to';

      insert into public.historical_case_version_logical_rules (
        historical_case_version_id,
        rule_code,
        relationship_type_id
      )
      values (
        target_historical_case_version_id,
        'P6D_RULE_A',
        logical_rule_relationship_type_id
      );

      select hckrt.id into knowledge_relationship_type_id
      from public.historical_case_knowledge_relationship_types hckrt
      where hckrt.relationship_code = 'current_guidance_to_consult';

      insert into public.historical_case_version_knowledge_documents (
        historical_case_version_id,
        knowledge_document_id,
        relationship_type_id
      )
      select
        target_historical_case_version_id,
        kd.id,
        knowledge_relationship_type_id
      from public.knowledge_documents kd
      where kd.document_code = 'P6D-DOC-A';

      update public.historical_case_versions
      set governance_status = 'active'
      where id = target_historical_case_version_id;
    end
    $$;
  $sql$,
  'a complete governed statement snapshot can be activated once all required evidence links exist'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_responsibilities (
      historical_case_version_id,
      actor_type,
      responsibility_statement,
      evidence_strength,
      historical_value_only,
      contamination_risk_level,
      current_authority_disposition
    )
    select
      hcv.id,
      'client',
      'Active fixture insert should fail.',
      'strong',
      false,
      'medium',
      'check_phase_4'
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-953'
      and hcv.version_number = 1;
  $sql$,
  '23514',
  null,
  'active case versions block new responsibility inserts'
);

select throws_ok(
  $sql$
    update public.historical_case_version_responsibilities hcvr
    set responsibility_statement = 'Active fixture responsibility edited in place'
    from public.historical_case_versions hcv,
         public.historical_cases hc
    where hcv.id = hcvr.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and hc.case_code = 'HC-953'
      and hcvr.responsibility_statement = 'Active fixture responsibility';
  $sql$,
  '23514',
  null,
  'active case versions block responsibility updates'
);

select throws_ok(
  $sql$
    delete from public.historical_case_version_responsibilities hcvr
    using public.historical_case_versions hcv,
          public.historical_cases hc
    where hcv.id = hcvr.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and hc.case_code = 'HC-953'
      and hcvr.responsibility_statement = 'Active fixture responsibility';
  $sql$,
  '23514',
  null,
  'active case versions block responsibility deletes'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_decisions (
      historical_case_version_id,
      decision_statement,
      evidence_strength,
      historical_value_only,
      contamination_risk_level,
      current_authority_disposition
    )
    select
      hcv.id,
      'Active fixture decision insert should fail.',
      'strong',
      false,
      'medium',
      'check_phase_5'
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-953'
      and hcv.version_number = 1;
  $sql$,
  '23514',
  null,
  'active case versions block new decision inserts'
);

select throws_ok(
  $sql$
    update public.historical_case_version_decisions hcvd
    set decision_statement = 'Active fixture decision edited in place'
    from public.historical_case_versions hcv,
         public.historical_cases hc
    where hcv.id = hcvd.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and hc.case_code = 'HC-953'
      and hcvd.decision_statement = 'Active fixture decision';
  $sql$,
  '23514',
  null,
  'active case versions block decision updates'
);

select throws_ok(
  $sql$
    delete from public.historical_case_version_decisions hcvd
    using public.historical_case_versions hcv,
          public.historical_cases hc
    where hcv.id = hcvd.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and hc.case_code = 'HC-953'
      and hcvd.decision_statement = 'Active fixture decision';
  $sql$,
  '23514',
  null,
  'active case versions block decision deletes'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_lessons (
      historical_case_version_id,
      lesson_kind,
      lesson_statement,
      evidence_strength,
      historical_value_only,
      contamination_risk_level,
      current_authority_disposition
    )
    select
      hcv.id,
      'curated_lesson',
      'Active fixture lesson insert should fail.',
      'strong',
      false,
      'medium',
      'check_phase_4_and_5'
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-953'
      and hcv.version_number = 1;
  $sql$,
  '23514',
  null,
  'active case versions block new lesson inserts'
);

select throws_ok(
  $sql$
    update public.historical_case_version_lessons hcvl
    set lesson_statement = 'Active fixture lesson edited in place'
    from public.historical_case_versions hcv,
         public.historical_cases hc
    where hcv.id = hcvl.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and hc.case_code = 'HC-953'
      and hcvl.lesson_statement = 'Active fixture lesson';
  $sql$,
  '23514',
  null,
  'active case versions block lesson updates'
);

select throws_ok(
  $sql$
    delete from public.historical_case_version_lessons hcvl
    using public.historical_case_versions hcv,
          public.historical_cases hc
    where hcv.id = hcvl.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and hc.case_code = 'HC-953'
      and hcvl.lesson_statement = 'Active fixture lesson';
  $sql$,
  '23514',
  null,
  'active case versions block lesson deletes'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_decision_sources (
      historical_case_version_id,
      decision_id,
      historical_case_version_source_object_id
    )
    select
      hcv.id,
      hcvd.id,
      hcvso.id
    from public.historical_case_version_decisions hcvd
    join public.historical_case_versions hcv
      on hcv.id = hcvd.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    join public.historical_case_version_source_objects hcvso
      on hcvso.historical_case_version_id = hcv.id
     and hcvso.source_locator = 'Case 953 - Full Evidence'
    where hc.case_code = 'HC-953'
      and hcvd.decision_statement = 'Active fixture decision';
  $sql$,
  '23514',
  null,
  'active case versions block new statement evidence links'
);

select throws_ok(
  $sql$
    delete from public.historical_case_version_lesson_sources hcvls
    using public.historical_case_version_lessons hcvl,
          public.historical_case_versions hcv,
          public.historical_cases hc
    where hcvl.id = hcvls.lesson_id
      and hcv.id = hcvls.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and hc.case_code = 'HC-953'
      and hcvl.lesson_statement = 'Active fixture lesson';
  $sql$,
  '23514',
  null,
  'active case versions block statement evidence link deletes'
);

select results_eq(
  $sql$
    select c.relname
    from pg_class c
    join pg_namespace n
      on n.oid = c.relnamespace
    where n.nspname = 'public'
      and c.relname in (
        'historical_case_version_responsibilities',
        'historical_case_version_decisions',
        'historical_case_version_lessons',
        'historical_case_version_responsibility_sources',
        'historical_case_version_decision_sources',
        'historical_case_version_lesson_sources'
      )
      and c.relrowsecurity
    order by c.relname
  $sql$,
  $sql$
    values
      ('historical_case_version_decision_sources'::name),
      ('historical_case_version_decisions'::name),
      ('historical_case_version_lesson_sources'::name),
      ('historical_case_version_lessons'::name),
      ('historical_case_version_responsibilities'::name),
      ('historical_case_version_responsibility_sources'::name)
  $sql$,
  'RLS is enabled on all Phase 6.2D statement and statement-provenance tables'
);

select is(
  (
    select count(*)
    from information_schema.role_table_grants rtg
    where rtg.table_schema = 'public'
      and rtg.table_name in (
        'historical_case_version_responsibilities',
        'historical_case_version_decisions',
        'historical_case_version_lessons',
        'historical_case_version_responsibility_sources',
        'historical_case_version_decision_sources',
        'historical_case_version_lesson_sources'
      )
      and rtg.grantee in ('anon', 'authenticated', 'service_role')
      and rtg.privilege_type in ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'REFERENCES', 'TRIGGER', 'TRUNCATE')
  ),
  0::bigint,
  'ordinary roles have no direct grants on the Phase 6.2D statement tables'
);

select throws_ok(
  $sql$
    select public._test_count_as('anon', $query$select * from public.historical_case_version_responsibilities$query$);
  $sql$,
  '42501',
  null,
  'anon cannot directly read historical_case_version_responsibilities'
);

select throws_ok(
  $sql$
    select public._test_count_as('authenticated', $query$select * from public.historical_case_version_responsibility_sources$query$);
  $sql$,
  '42501',
  null,
  'authenticated cannot directly read historical_case_version_responsibility_sources'
);

select *
from finish();

rollback;
