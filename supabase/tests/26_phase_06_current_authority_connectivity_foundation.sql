begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

select plan(70);

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
  to_regclass('public.historical_case_rule_relationship_types') is not null,
  'historical_case_rule_relationship_types table exists'
);

select ok(
  to_regclass('public.historical_case_version_logical_rules') is not null,
  'historical_case_version_logical_rules table exists'
);

select ok(
  to_regclass('public.historical_case_version_rule_versions') is not null,
  'historical_case_version_rule_versions table exists'
);

select ok(
  to_regclass('public.historical_case_knowledge_relationship_types') is not null,
  'historical_case_knowledge_relationship_types table exists'
);

select ok(
  to_regclass('public.historical_case_version_knowledge_documents') is not null,
  'historical_case_version_knowledge_documents table exists'
);

select ok(
  to_regclass('public.historical_case_version_knowledge_document_versions') is not null,
  'historical_case_version_knowledge_document_versions table exists'
);

select lives_ok(
  $sql$
    do $$
    declare
      internal_confidentiality_id bigint;
      primary_role_id bigint;
      governance_category_id bigint;
      case_960_id bigint;
      case_961_id bigint;
      case_962_id bigint;
      case_963_id bigint;
      case_964_id bigint;
      case_965_id bigint;
      case_966_id bigint;
      case_967_id bigint;
      case_968_id bigint;
      case_969_id bigint;
      case_960_version_id bigint;
      case_961_version_id bigint;
      case_962_version_id bigint;
      case_963_version_id bigint;
      case_964_version_id bigint;
      case_965_version_id bigint;
      case_966_version_id bigint;
      case_967_version_id bigint;
      case_968_version_id bigint;
      case_969_version_id bigint;
      source_association_id bigint;
      responsibility_id bigint;
      decision_id bigint;
      lesson_id bigint;
    begin
      select id into internal_confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      select id into primary_role_id
      from public.historical_case_evidence_roles
      where role_code = 'primary_supporting_evidence';

      select id into governance_category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      insert into public.logical_rules (
        rule_code,
        rule_domain
      )
      values
        ('P6E_RULE_A', 'testing'),
        ('P6E_RULE_B', 'testing'),
        ('P6E_RULE_C', 'testing'),
        ('P6E_RULE_D', 'testing');

      insert into public.rule_catalogue (
        rule_code,
        rule_domain,
        rule_kind,
        rule_version,
        status,
        plain_language_explanation
      )
      values
        ('P6E_RULE_A', 'testing', 'hard_rule', 1, 'draft', 'P6E rule A version 1'),
        ('P6E_RULE_B', 'testing', 'hard_rule', 1, 'draft', 'P6E rule B version 1'),
        ('P6E_RULE_C', 'testing', 'hard_rule', 1, 'draft', 'P6E rule C version 1'),
        ('P6E_RULE_D', 'testing', 'hard_rule', 1, 'draft', 'P6E rule D version 1');

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values
        ('P6E-DOC-A', 'P6E Current Guidance A', governance_category_id),
        ('P6E-DOC-B', 'P6E Current Guidance B', governance_category_id),
        ('P6E-DOC-C', 'P6E Current Guidance C', governance_category_id);

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      select
        kd.id,
        1,
        'draft',
        'guidance',
        internal_confidentiality_id
      from public.knowledge_documents kd
      where kd.document_code in ('P6E-DOC-A', 'P6E-DOC-B', 'P6E-DOC-C');

      insert into public.historical_cases (
        case_code,
        canonical_title
      )
      values
        ('HC-960', 'Phase 6.2E Relationship Fixture A'),
        ('HC-961', 'Phase 6.2E Relationship Fixture B'),
        ('HC-962', 'Phase 6.2E Phase 4 Activation Fixture'),
        ('HC-963', 'Phase 6.2E Phase 5 Activation Fixture'),
        ('HC-964', 'Phase 6.2E Both-Layers Activation Fixture'),
        ('HC-965', 'Phase 6.2E No-Implication Activation Fixture'),
        ('HC-966', 'Phase 6.2E Current Status Unknown Fixture'),
        ('HC-967', 'Phase 6.2E Potential Conflict Fixture'),
        ('HC-968', 'Phase 6.2E Active Immutability Fixture'),
        ('HC-969', 'Phase 6.2E Draft Mutability Fixture');

      select id into case_960_id from public.historical_cases where case_code = 'HC-960';
      select id into case_961_id from public.historical_cases where case_code = 'HC-961';
      select id into case_962_id from public.historical_cases where case_code = 'HC-962';
      select id into case_963_id from public.historical_cases where case_code = 'HC-963';
      select id into case_964_id from public.historical_cases where case_code = 'HC-964';
      select id into case_965_id from public.historical_cases where case_code = 'HC-965';
      select id into case_966_id from public.historical_cases where case_code = 'HC-966';
      select id into case_967_id from public.historical_cases where case_code = 'HC-967';
      select id into case_968_id from public.historical_cases where case_code = 'HC-968';
      select id into case_969_id from public.historical_cases where case_code = 'HC-969';

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
        (case_960_id, 1, 'draft', 'active', 'full_case', 'strong', 'completed', 'unknown', 'Relationship fixture A.', internal_confidentiality_id, false),
        (case_961_id, 1, 'draft', 'active', 'full_case', 'strong', 'completed', 'unknown', 'Relationship fixture B.', internal_confidentiality_id, false),
        (case_962_id, 1, 'draft', 'active', 'full_case', 'strong', 'completed', 'unknown', 'Phase 4 activation fixture.', internal_confidentiality_id, false),
        (case_963_id, 1, 'draft', 'active', 'full_case', 'strong', 'completed', 'unknown', 'Phase 5 activation fixture.', internal_confidentiality_id, false),
        (case_964_id, 1, 'draft', 'active', 'full_case', 'strong', 'completed', 'unknown', 'Both-layers activation fixture.', internal_confidentiality_id, false),
        (case_965_id, 1, 'draft', 'active', 'limited_precedent', 'moderate', 'completed', 'unknown', 'No implication activation fixture.', internal_confidentiality_id, false),
        (case_966_id, 1, 'draft', 'active', 'limited_precedent', 'moderate', 'partial_or_unclear', 'unknown', 'Current status unknown fixture.', internal_confidentiality_id, false),
        (case_967_id, 1, 'draft', 'active', 'cautionary_precedent', 'moderate', 'completed', 'unknown', 'Potential conflict fixture.', internal_confidentiality_id, false),
        (case_968_id, 1, 'draft', 'active', 'full_case', 'strong', 'completed', 'unknown', 'Active immutability fixture.', internal_confidentiality_id, false),
        (case_969_id, 1, 'draft', 'active', 'full_case', 'strong', 'completed', 'unknown', 'Draft mutability fixture.', internal_confidentiality_id, false);

      select id into case_960_version_id from public.historical_case_versions where historical_case_id = case_960_id and version_number = 1;
      select id into case_961_version_id from public.historical_case_versions where historical_case_id = case_961_id and version_number = 1;
      select id into case_962_version_id from public.historical_case_versions where historical_case_id = case_962_id and version_number = 1;
      select id into case_963_version_id from public.historical_case_versions where historical_case_id = case_963_id and version_number = 1;
      select id into case_964_version_id from public.historical_case_versions where historical_case_id = case_964_id and version_number = 1;
      select id into case_965_version_id from public.historical_case_versions where historical_case_id = case_965_id and version_number = 1;
      select id into case_966_version_id from public.historical_case_versions where historical_case_id = case_966_id and version_number = 1;
      select id into case_967_version_id from public.historical_case_versions where historical_case_id = case_967_id and version_number = 1;
      select id into case_968_version_id from public.historical_case_versions where historical_case_id = case_968_id and version_number = 1;
      select id into case_969_version_id from public.historical_case_versions where historical_case_id = case_969_id and version_number = 1;

      insert into public.knowledge_source_objects (
        origin_type,
        manual_reference_key,
        original_filename
      )
      values
        ('manual_reference', 'P6E-HC-962', 'p6e-hc-962.txt'),
        ('manual_reference', 'P6E-HC-963', 'p6e-hc-963.txt'),
        ('manual_reference', 'P6E-HC-964', 'p6e-hc-964.txt'),
        ('manual_reference', 'P6E-HC-965', 'p6e-hc-965.txt'),
        ('manual_reference', 'P6E-HC-966', 'p6e-hc-966.txt'),
        ('manual_reference', 'P6E-HC-967', 'p6e-hc-967.txt');

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
        fixture.case_version_id,
        kso.id,
        primary_role_id,
        internal_confidentiality_id,
        fixture.evidence_strength,
        fixture.source_locator,
        fixture.supported_claim_dimensions,
        fixture.relationship_notes
      from (
        values
          (case_962_version_id, 'P6E-HC-962', 'strong', 'HC-962 responsibility source', array['responsibility']::text[], 'Supports the Phase 4 responsibility fixture.'),
          (case_963_version_id, 'P6E-HC-963', 'strong', 'HC-963 decision source', array['decision']::text[], 'Supports the Phase 5 decision fixture.'),
          (case_964_version_id, 'P6E-HC-964', 'strong', 'HC-964 lesson source', array['lesson']::text[], 'Supports the both-layers lesson fixture.'),
          (case_965_version_id, 'P6E-HC-965', 'moderate', 'HC-965 responsibility source', array['responsibility']::text[], 'Supports the no-implication responsibility fixture.'),
          (case_966_version_id, 'P6E-HC-966', 'moderate', 'HC-966 lesson source', array['lesson']::text[], 'Supports the current-status-unknown lesson fixture.'),
          (case_967_version_id, 'P6E-HC-967', 'moderate', 'HC-967 decision source', array['decision']::text[], 'Supports the potential-conflict decision fixture.')
      ) as fixture(case_version_id, manual_reference_key, evidence_strength, source_locator, supported_claim_dimensions, relationship_notes)
      join public.knowledge_source_objects kso
        on kso.manual_reference_key = fixture.manual_reference_key;

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
        (case_962_version_id, 'wnc', 'HC-962 requires checking current Phase 4 authority.', 'strong', false, 'medium', 'check_phase_4'),
        (case_965_version_id, 'client', 'HC-965 is event-specific and has no current-rule implication.', 'moderate', false, 'low', 'no_current_rule_implication');

      insert into public.historical_case_version_decisions (
        historical_case_version_id,
        decision_statement,
        evidence_strength,
        historical_value_only,
        contamination_risk_level,
        current_authority_disposition
      )
      values
        (case_963_version_id, 'HC-963 requires checking current Phase 5 guidance.', 'strong', false, 'medium', 'check_phase_5'),
        (case_967_version_id, 'HC-967 may conflict with current knowledge if reused directly.', 'moderate', false, 'high', 'potential_conflict_with_current_knowledge');

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
        (case_964_version_id, 'curated_lesson', 'HC-964 requires checking both Phase 4 and Phase 5.', 'strong', false, 'medium', 'check_phase_4_and_5'),
        (case_966_version_id, 'analyst_inference', 'HC-966 has unresolved current status.', 'moderate', false, 'medium', 'current_status_unknown');

      select id into responsibility_id
      from public.historical_case_version_responsibilities
      where historical_case_version_id = case_962_version_id;

      select hcvso.id into source_association_id
      from public.historical_case_version_source_objects hcvso
      where hcvso.historical_case_version_id = case_962_version_id;

      insert into public.historical_case_version_responsibility_sources (
        historical_case_version_id,
        responsibility_id,
        historical_case_version_source_object_id
      )
      values (
        case_962_version_id,
        responsibility_id,
        source_association_id
      );

      select id into responsibility_id
      from public.historical_case_version_responsibilities
      where historical_case_version_id = case_965_version_id;

      select hcvso.id into source_association_id
      from public.historical_case_version_source_objects hcvso
      where hcvso.historical_case_version_id = case_965_version_id;

      insert into public.historical_case_version_responsibility_sources (
        historical_case_version_id,
        responsibility_id,
        historical_case_version_source_object_id
      )
      values (
        case_965_version_id,
        responsibility_id,
        source_association_id
      );

      select id into decision_id
      from public.historical_case_version_decisions
      where historical_case_version_id = case_963_version_id;

      select hcvso.id into source_association_id
      from public.historical_case_version_source_objects hcvso
      where hcvso.historical_case_version_id = case_963_version_id;

      insert into public.historical_case_version_decision_sources (
        historical_case_version_id,
        decision_id,
        historical_case_version_source_object_id
      )
      values (
        case_963_version_id,
        decision_id,
        source_association_id
      );

      select id into decision_id
      from public.historical_case_version_decisions
      where historical_case_version_id = case_967_version_id;

      select hcvso.id into source_association_id
      from public.historical_case_version_source_objects hcvso
      where hcvso.historical_case_version_id = case_967_version_id;

      insert into public.historical_case_version_decision_sources (
        historical_case_version_id,
        decision_id,
        historical_case_version_source_object_id
      )
      values (
        case_967_version_id,
        decision_id,
        source_association_id
      );

      select id into lesson_id
      from public.historical_case_version_lessons
      where historical_case_version_id = case_964_version_id;

      select hcvso.id into source_association_id
      from public.historical_case_version_source_objects hcvso
      where hcvso.historical_case_version_id = case_964_version_id;

      insert into public.historical_case_version_lesson_sources (
        historical_case_version_id,
        lesson_id,
        historical_case_version_source_object_id
      )
      values (
        case_964_version_id,
        lesson_id,
        source_association_id
      );

      select id into lesson_id
      from public.historical_case_version_lessons
      where historical_case_version_id = case_966_version_id;

      select hcvso.id into source_association_id
      from public.historical_case_version_source_objects hcvso
      where hcvso.historical_case_version_id = case_966_version_id;

      insert into public.historical_case_version_lesson_sources (
        historical_case_version_id,
        lesson_id,
        historical_case_version_source_object_id
      )
      values (
        case_966_version_id,
        lesson_id,
        source_association_id
      );
    end
    $$;
  $sql$,
  'Phase 6.2E fixtures can be created with Phase 4 and Phase 5 targets plus activation-ready statement provenance'
);

select results_eq(
  $sql$
    select relationship_code
    from public.historical_case_rule_relationship_types
    order by sort_order, relationship_code
  $sql$,
  $sql$
    values
      ('relevant_to'::text),
      ('illustrates'::text),
      ('historical_precedent_for'::text),
      ('encountered_issue_related_to'::text)
  $sql$,
  'expected non-authoritative Phase 4 relationship vocabulary is seeded'
);

select throws_ok(
  $sql$
    insert into public.historical_case_rule_relationship_types (
      relationship_code,
      display_name,
      description
    )
    values (
      'relevant_to',
      'Duplicate Relevant To',
      'duplicate code should fail'
    );
  $sql$,
  '23505',
  null,
  'Phase 4 relationship codes are unique'
);

select is(
  (
    select count(*)
    from public.historical_case_rule_relationship_types hcrrt
    where hcrrt.relationship_code in (
      'defines',
      'governs',
      'overrides',
      'authoritative_source_for',
      'replaces',
      'sets_value_for'
    )
  ),
  0::bigint,
  'no authoritative Phase 4 relationship semantics are seeded'
);

select results_eq(
  $sql$
    select relationship_code
    from public.historical_case_knowledge_relationship_types
    order by sort_order, relationship_code
  $sql$,
  $sql$
    values
      ('current_guidance_to_consult'::text),
      ('current_context_relevant_to_case'::text),
      ('current_authority_supersedes_historical_practice'::text),
      ('current_document_for_interpretation'::text)
  $sql$,
  'expected Phase 5 relationship vocabulary is seeded'
);

select throws_ok(
  $sql$
    insert into public.historical_case_knowledge_relationship_types (
      relationship_code,
      display_name,
      description
    )
    values (
      'current_guidance_to_consult',
      'Duplicate Guidance',
      'duplicate code should fail'
    );
  $sql$,
  '23505',
  null,
  'Phase 5 relationship codes are unique'
);

select lives_ok(
  $sql$
    insert into public.historical_case_version_logical_rules (
      historical_case_version_id,
      rule_code,
      relationship_type_id,
      relationship_note
    )
    select
      hcv.id,
      'P6E_RULE_A',
      hcrrt.id,
      'Draft logical-rule relationship for case A.'
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join public.historical_case_rule_relationship_types hcrrt
    where hc.case_code = 'HC-960'
      and hcv.version_number = 1
      and hcrrt.relationship_code = 'relevant_to';
  $sql$,
  'draft case version can link to a valid logical rule'
);

select lives_ok(
  $sql$
    insert into public.historical_case_version_logical_rules (
      historical_case_version_id,
      rule_code,
      relationship_type_id,
      relationship_note
    )
    select
      hcv.id,
      'P6E_RULE_B',
      hcrrt.id,
      'Second logical-rule relationship for case A.'
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join public.historical_case_rule_relationship_types hcrrt
    where hc.case_code = 'HC-960'
      and hcv.version_number = 1
      and hcrrt.relationship_code = 'illustrates';
  $sql$,
  'many logical rules per case version are allowed'
);

select lives_ok(
  $sql$
    insert into public.historical_case_version_logical_rules (
      historical_case_version_id,
      rule_code,
      relationship_type_id,
      relationship_note
    )
    select
      hcv.id,
      'P6E_RULE_A',
      hcrrt.id,
      'Case B also relates to rule A.'
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join public.historical_case_rule_relationship_types hcrrt
    where hc.case_code = 'HC-961'
      and hcv.version_number = 1
      and hcrrt.relationship_code = 'historical_precedent_for';
  $sql$,
  'one logical rule may relate to many historical case versions'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_logical_rules (
      historical_case_version_id,
      rule_code,
      relationship_type_id
    )
    select
      hcv.id,
      'P6E_RULE_A',
      hcrrt.id
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join public.historical_case_rule_relationship_types hcrrt
    where hc.case_code = 'HC-960'
      and hcv.version_number = 1
      and hcrrt.relationship_code = 'relevant_to';
  $sql$,
  '23505',
  null,
  'duplicate semantic logical-rule links are rejected'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_logical_rules (
      historical_case_version_id,
      rule_code,
      relationship_type_id
    )
    select
      hcv.id,
      'P6E_RULE_MISSING',
      hcrrt.id
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join public.historical_case_rule_relationship_types hcrrt
    where hc.case_code = 'HC-960'
      and hcv.version_number = 1
      and hcrrt.relationship_code = 'relevant_to';
  $sql$,
  '23503',
  null,
  'invalid logical rule codes are rejected'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_logical_rules (
      historical_case_version_id,
      rule_code,
      relationship_type_id
    )
    select
      hcv.id,
      'P6E_RULE_A',
      999999999
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-960'
      and hcv.version_number = 1;
  $sql$,
  '23503',
  null,
  'invalid Phase 4 relationship references are rejected'
);

select throws_ok(
  $sql$
    do $$
    declare
      target_case_version_id bigint;
      target_rule_version_id bigint;
      relationship_type_id bigint;
    begin
      select hcv.id into target_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-960'
        and hcv.version_number = 1;

      select rc.id into target_rule_version_id
      from public.rule_catalogue rc
      where rc.rule_code = 'P6E_RULE_C'
        and rc.rule_version = 1;

      select hcrrt.id into relationship_type_id
      from public.historical_case_rule_relationship_types hcrrt
      where hcrrt.relationship_code = 'illustrates';

      insert into public.historical_case_version_rule_versions (
        historical_case_version_id,
        rule_version_id,
        relationship_type_id
      )
      values (
        target_case_version_id,
        target_rule_version_id,
        relationship_type_id
      );

      set constraints all immediate;
    end
    $$;
  $sql$,
  '23514',
  null,
  'exact rule-version links cannot float without a stable logical-rule parent link'
);

select lives_ok(
  $sql$
    do $$
    declare
      target_case_version_id bigint;
      target_rule_version_id bigint;
      relationship_type_id bigint;
    begin
      select hcv.id into target_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-960'
        and hcv.version_number = 1;

      select hcrrt.id into relationship_type_id
      from public.historical_case_rule_relationship_types hcrrt
      where hcrrt.relationship_code = 'historical_precedent_for';

      insert into public.historical_case_version_logical_rules (
        historical_case_version_id,
        rule_code,
        relationship_type_id,
        relationship_note
      )
      values (
        target_case_version_id,
        'P6E_RULE_C',
        relationship_type_id,
        'Stable parent for exact rule-version relationship.'
      );

      select rc.id into target_rule_version_id
      from public.rule_catalogue rc
      where rc.rule_code = 'P6E_RULE_C'
        and rc.rule_version = 1;

      insert into public.historical_case_version_rule_versions (
        historical_case_version_id,
        rule_version_id,
        relationship_type_id,
        relationship_note
      )
      values (
        target_case_version_id,
        target_rule_version_id,
        relationship_type_id,
        'Exact Phase 4 rule-version relationship for case A.'
      );
    end
    $$;
  $sql$,
  'valid exact Phase 4 rule-version relationships are accepted when the stable parent link exists'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_rule_versions (
      historical_case_version_id,
      rule_version_id,
      relationship_type_id
    )
    select
      hcv.id,
      999999999,
      hcrrt.id
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join public.historical_case_rule_relationship_types hcrrt
    where hc.case_code = 'HC-960'
      and hcv.version_number = 1
      and hcrrt.relationship_code = 'relevant_to';
  $sql$,
  '23503',
  null,
  'invalid exact rule-version ids are rejected'
);

select lives_ok(
  $sql$
    insert into public.historical_case_version_knowledge_documents (
      historical_case_version_id,
      knowledge_document_id,
      relationship_type_id,
      relationship_note
    )
    select
      hcv.id,
      kd.id,
      hckrt.id,
      'Stable knowledge-document relationship for case A.'
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    join public.knowledge_documents kd
      on kd.document_code = 'P6E-DOC-A'
    cross join public.historical_case_knowledge_relationship_types hckrt
    where hc.case_code = 'HC-960'
      and hcv.version_number = 1
      and hckrt.relationship_code = 'current_guidance_to_consult';
  $sql$,
  'draft case version can link to a valid current knowledge document'
);

select lives_ok(
  $sql$
    insert into public.historical_case_version_knowledge_documents (
      historical_case_version_id,
      knowledge_document_id,
      relationship_type_id,
      relationship_note
    )
    select
      hcv.id,
      kd.id,
      hckrt.id,
      'Second current knowledge document for case A.'
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    join public.knowledge_documents kd
      on kd.document_code = 'P6E-DOC-B'
    cross join public.historical_case_knowledge_relationship_types hckrt
    where hc.case_code = 'HC-960'
      and hcv.version_number = 1
      and hckrt.relationship_code = 'current_document_for_interpretation';
  $sql$,
  'multiple current knowledge documents may relate to one case version'
);

select lives_ok(
  $sql$
    insert into public.historical_case_version_knowledge_documents (
      historical_case_version_id,
      knowledge_document_id,
      relationship_type_id,
      relationship_note
    )
    select
      hcv.id,
      kd.id,
      hckrt.id,
      'Case B also relates to current document A.'
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    join public.knowledge_documents kd
      on kd.document_code = 'P6E-DOC-A'
    cross join public.historical_case_knowledge_relationship_types hckrt
    where hc.case_code = 'HC-961'
      and hcv.version_number = 1
      and hckrt.relationship_code = 'current_context_relevant_to_case';
  $sql$,
  'one current knowledge document may relate to many case versions'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_knowledge_documents (
      historical_case_version_id,
      knowledge_document_id,
      relationship_type_id
    )
    select
      hcv.id,
      kd.id,
      hckrt.id
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    join public.knowledge_documents kd
      on kd.document_code = 'P6E-DOC-A'
    cross join public.historical_case_knowledge_relationship_types hckrt
    where hc.case_code = 'HC-960'
      and hcv.version_number = 1
      and hckrt.relationship_code = 'current_guidance_to_consult';
  $sql$,
  '23505',
  null,
  'duplicate semantic stable knowledge-document links are rejected'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_knowledge_documents (
      historical_case_version_id,
      knowledge_document_id,
      relationship_type_id
    )
    select
      hcv.id,
      999999999,
      hckrt.id
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join public.historical_case_knowledge_relationship_types hckrt
    where hc.case_code = 'HC-960'
      and hcv.version_number = 1
      and hckrt.relationship_code = 'current_guidance_to_consult';
  $sql$,
  '23503',
  null,
  'invalid stable knowledge document references are rejected'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_knowledge_documents (
      historical_case_version_id,
      knowledge_document_id,
      relationship_type_id
    )
    select
      hcv.id,
      kd.id,
      999999999
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    join public.knowledge_documents kd
      on kd.document_code = 'P6E-DOC-A'
    where hc.case_code = 'HC-960'
      and hcv.version_number = 1;
  $sql$,
  '23503',
  null,
  'invalid Phase 5 relationship references are rejected'
);

select throws_ok(
  $sql$
    do $$
    declare
      target_case_version_id bigint;
      target_document_version_id bigint;
      relationship_type_id bigint;
    begin
      select hcv.id into target_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-960'
        and hcv.version_number = 1;

      select kdv.id into target_document_version_id
      from public.knowledge_document_versions kdv
      join public.knowledge_documents kd
        on kd.id = kdv.document_id
      where kd.document_code = 'P6E-DOC-C'
        and kdv.version_number = 1;

      select hckrt.id into relationship_type_id
      from public.historical_case_knowledge_relationship_types hckrt
      where hckrt.relationship_code = 'current_document_for_interpretation';

      insert into public.historical_case_version_knowledge_document_versions (
        historical_case_version_id,
        knowledge_document_version_id,
        relationship_type_id
      )
      values (
        target_case_version_id,
        target_document_version_id,
        relationship_type_id
      );

      set constraints all immediate;
    end
    $$;
  $sql$,
  '23514',
  null,
  'exact knowledge-document-version links cannot float without a stable parent document link'
);

select lives_ok(
  $sql$
    do $$
    declare
      target_case_version_id bigint;
      target_document_version_id bigint;
      relationship_type_id bigint;
    begin
      select hcv.id into target_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-960'
        and hcv.version_number = 1;

      select hckrt.id into relationship_type_id
      from public.historical_case_knowledge_relationship_types hckrt
      where hckrt.relationship_code = 'current_authority_supersedes_historical_practice';

      insert into public.historical_case_version_knowledge_documents (
        historical_case_version_id,
        knowledge_document_id,
        relationship_type_id,
        relationship_note
      )
      select
        target_case_version_id,
        kd.id,
        relationship_type_id,
        'Stable parent for exact current knowledge version.'
      from public.knowledge_documents kd
      where kd.document_code = 'P6E-DOC-C';

      select kdv.id into target_document_version_id
      from public.knowledge_document_versions kdv
      join public.knowledge_documents kd
        on kd.id = kdv.document_id
      where kd.document_code = 'P6E-DOC-C'
        and kdv.version_number = 1;

      insert into public.historical_case_version_knowledge_document_versions (
        historical_case_version_id,
        knowledge_document_version_id,
        relationship_type_id,
        relationship_note
      )
      values (
        target_case_version_id,
        target_document_version_id,
        relationship_type_id,
        'Exact Phase 5 document-version relationship for case A.'
      );
    end
    $$;
  $sql$,
  'valid exact current knowledge document-version relationships are accepted when the stable parent link exists'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_knowledge_document_versions (
      historical_case_version_id,
      knowledge_document_version_id,
      relationship_type_id
    )
    select
      hcv.id,
      999999999,
      hckrt.id
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join public.historical_case_knowledge_relationship_types hckrt
    where hc.case_code = 'HC-960'
      and hcv.version_number = 1
      and hckrt.relationship_code = 'current_document_for_interpretation';
  $sql$,
  '23503',
  null,
  'invalid current knowledge document-version ids are rejected'
);

select lives_ok(
  $sql$
    do $$
    declare
      target_case_version_id bigint;
      logical_relationship_type_id bigint;
      exact_rule_relationship_type_id bigint;
      knowledge_relationship_type_id bigint;
      exact_document_relationship_type_id bigint;
      rule_a_version_id bigint;
      doc_a_id bigint;
      doc_a_version_id bigint;
      rule_b_id bigint;
      doc_b_id bigint;
      doc_b_version_id bigint;
    begin
      select hcv.id into target_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-969'
        and hcv.version_number = 1;

      select id into logical_relationship_type_id
      from public.historical_case_rule_relationship_types
      where relationship_code = 'relevant_to';

      select id into exact_rule_relationship_type_id
      from public.historical_case_rule_relationship_types
      where relationship_code = 'illustrates';

      select id into knowledge_relationship_type_id
      from public.historical_case_knowledge_relationship_types
      where relationship_code = 'current_guidance_to_consult';

      select id into exact_document_relationship_type_id
      from public.historical_case_knowledge_relationship_types
      where relationship_code = 'current_document_for_interpretation';

      select rc.id into rule_a_version_id
      from public.rule_catalogue rc
      where rc.rule_code = 'P6E_RULE_A'
        and rc.rule_version = 1;

      select kd.id into doc_a_id
      from public.knowledge_documents kd
      where kd.document_code = 'P6E-DOC-A';

      select kdv.id into doc_a_version_id
      from public.knowledge_document_versions kdv
      join public.knowledge_documents kd
        on kd.id = kdv.document_id
      where kd.document_code = 'P6E-DOC-A'
        and kdv.version_number = 1;

      select kd.id into doc_b_id
      from public.knowledge_documents kd
      where kd.document_code = 'P6E-DOC-B';

      select kdv.id into doc_b_version_id
      from public.knowledge_document_versions kdv
      join public.knowledge_documents kd
        on kd.id = kdv.document_id
      where kd.document_code = 'P6E-DOC-B'
        and kdv.version_number = 1;

      insert into public.historical_case_version_logical_rules (
        historical_case_version_id,
        rule_code,
        relationship_type_id,
        relationship_note
      )
      values
        (target_case_version_id, 'P6E_RULE_A', logical_relationship_type_id, 'Draft mutability logical rule A'),
        (target_case_version_id, 'P6E_RULE_B', logical_relationship_type_id, 'Draft mutability logical rule B');

      insert into public.historical_case_version_rule_versions (
        historical_case_version_id,
        rule_version_id,
        relationship_type_id,
        relationship_note
      )
      values (
        target_case_version_id,
        rule_a_version_id,
        exact_rule_relationship_type_id,
        'Draft mutability exact rule version'
      );

      insert into public.historical_case_version_knowledge_documents (
        historical_case_version_id,
        knowledge_document_id,
        relationship_type_id,
        relationship_note
      )
      values
        (target_case_version_id, doc_a_id, knowledge_relationship_type_id, 'Draft mutability stable doc A'),
        (target_case_version_id, doc_b_id, knowledge_relationship_type_id, 'Draft mutability stable doc B');

      insert into public.historical_case_version_knowledge_document_versions (
        historical_case_version_id,
        knowledge_document_version_id,
        relationship_type_id,
        relationship_note
      )
      values
        (target_case_version_id, doc_a_version_id, exact_document_relationship_type_id, 'Draft mutability exact doc version A'),
        (target_case_version_id, doc_b_version_id, exact_document_relationship_type_id, 'Draft mutability exact doc version B');
    end
    $$;
  $sql$,
  'draft mutability fixture can receive all four relationship association families'
);

select lives_ok(
  $sql$
    update public.historical_case_version_logical_rules hcvlr
    set relationship_note = 'Draft logical relationship updated before activation.'
    from public.historical_case_versions hcv,
         public.historical_cases hc
    where hcv.id = hcvlr.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and hc.case_code = 'HC-969'
      and hcvlr.rule_code = 'P6E_RULE_A';
  $sql$,
  'draft logical-rule relationships may be updated'
);

select lives_ok(
  $sql$
    delete from public.historical_case_version_logical_rules hcvlr
    using public.historical_case_versions hcv,
          public.historical_cases hc
    where hcv.id = hcvlr.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and hc.case_code = 'HC-969'
      and hcvlr.rule_code = 'P6E_RULE_B';
  $sql$,
  'draft logical-rule relationships may be deleted'
);

select lives_ok(
  $sql$
    update public.historical_case_version_rule_versions hcvrv
    set relationship_note = 'Draft exact rule-version relationship updated before activation.'
    from public.historical_case_versions hcv,
         public.historical_cases hc,
         public.rule_catalogue rc
    where hcv.id = hcvrv.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and rc.id = hcvrv.rule_version_id
      and hc.case_code = 'HC-969'
      and rc.rule_code = 'P6E_RULE_A';
  $sql$,
  'draft exact rule-version relationships may be updated'
);

select lives_ok(
  $sql$
    delete from public.historical_case_version_rule_versions hcvrv
    using public.historical_case_versions hcv,
          public.historical_cases hc,
          public.rule_catalogue rc
    where hcv.id = hcvrv.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and rc.id = hcvrv.rule_version_id
      and hc.case_code = 'HC-969'
      and rc.rule_code = 'P6E_RULE_A';
  $sql$,
  'draft exact rule-version relationships may be deleted'
);

select lives_ok(
  $sql$
    update public.historical_case_version_knowledge_documents hcvkd
    set relationship_note = 'Draft stable knowledge-document relationship updated before activation.'
    from public.historical_case_versions hcv,
         public.historical_cases hc,
         public.knowledge_documents kd
    where hcv.id = hcvkd.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and kd.id = hcvkd.knowledge_document_id
      and hc.case_code = 'HC-969'
      and kd.document_code = 'P6E-DOC-A';
  $sql$,
  'draft stable knowledge-document relationships may be updated'
);

select lives_ok(
  $sql$
    delete from public.historical_case_version_knowledge_documents hcvkd
    using public.historical_case_versions hcv,
          public.historical_cases hc,
          public.knowledge_documents kd
    where hcv.id = hcvkd.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and kd.id = hcvkd.knowledge_document_id
      and hc.case_code = 'HC-969'
      and kd.document_code = 'P6E-DOC-B';
  $sql$,
  'draft stable knowledge-document relationships may be deleted'
);

select lives_ok(
  $sql$
    update public.historical_case_version_knowledge_document_versions hcvkdv
    set relationship_note = 'Draft exact knowledge-document-version relationship updated before activation.'
    from public.historical_case_versions hcv,
         public.historical_cases hc,
         public.knowledge_document_versions kdv,
         public.knowledge_documents kd
    where hcv.id = hcvkdv.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and kdv.id = hcvkdv.knowledge_document_version_id
      and kd.id = kdv.document_id
      and hc.case_code = 'HC-969'
      and kd.document_code = 'P6E-DOC-A';
  $sql$,
  'draft exact knowledge-document-version relationships may be updated'
);

select lives_ok(
  $sql$
    delete from public.historical_case_version_knowledge_document_versions hcvkdv
    using public.historical_case_versions hcv,
          public.historical_cases hc,
          public.knowledge_document_versions kdv,
          public.knowledge_documents kd
    where hcv.id = hcvkdv.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and kdv.id = hcvkdv.knowledge_document_version_id
      and kd.id = kdv.document_id
      and hc.case_code = 'HC-969'
      and kd.document_code = 'P6E-DOC-B';
  $sql$,
  'draft exact knowledge-document-version relationships may be deleted'
);

select throws_ok(
  $sql$
    update public.historical_case_versions hcv
    set governance_status = 'active'
    from public.historical_cases hc
    where hc.id = hcv.historical_case_id
      and hc.case_code = 'HC-962'
      and hcv.version_number = 1;
  $sql$,
  '23514',
  null,
  'activation fails when a responsibility requires Phase 4 connectivity and no Phase 4 relationship exists'
);

select lives_ok(
  $sql$
    do $$
    declare
      target_case_version_id bigint;
      relationship_type_id bigint;
    begin
      select hcv.id into target_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-962'
        and hcv.version_number = 1;

      select hcrrt.id into relationship_type_id
      from public.historical_case_rule_relationship_types hcrrt
      where hcrrt.relationship_code = 'relevant_to';

      insert into public.historical_case_version_logical_rules (
        historical_case_version_id,
        rule_code,
        relationship_type_id
      )
      values (
        target_case_version_id,
        'P6E_RULE_C',
        relationship_type_id
      );

      update public.historical_case_versions
      set governance_status = 'active'
      where id = target_case_version_id;
    end
    $$;
  $sql$,
  'activation succeeds once required Phase 4 connectivity has been added for a responsibility statement'
);

select throws_ok(
  $sql$
    update public.historical_case_versions hcv
    set governance_status = 'active'
    from public.historical_cases hc
    where hc.id = hcv.historical_case_id
      and hc.case_code = 'HC-963'
      and hcv.version_number = 1;
  $sql$,
  '23514',
  null,
  'activation fails when a decision requires Phase 5 connectivity and no Phase 5 relationship exists'
);

select lives_ok(
  $sql$
    do $$
    declare
      target_case_version_id bigint;
      target_document_id bigint;
      relationship_type_id bigint;
    begin
      select hcv.id into target_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-963'
        and hcv.version_number = 1;

      select kd.id into target_document_id
      from public.knowledge_documents kd
      where kd.document_code = 'P6E-DOC-C';

      select hckrt.id into relationship_type_id
      from public.historical_case_knowledge_relationship_types hckrt
      where hckrt.relationship_code = 'current_guidance_to_consult';

      insert into public.historical_case_version_knowledge_documents (
        historical_case_version_id,
        knowledge_document_id,
        relationship_type_id
      )
      values (
        target_case_version_id,
        target_document_id,
        relationship_type_id
      );

      update public.historical_case_versions
      set governance_status = 'active'
      where id = target_case_version_id;
    end
    $$;
  $sql$,
  'activation succeeds once required Phase 5 connectivity has been added for a decision statement'
);

select throws_ok(
  $sql$
    do $$
    declare
      target_case_version_id bigint;
      relationship_type_id bigint;
    begin
      select hcv.id into target_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-964'
        and hcv.version_number = 1;

      select hcrrt.id into relationship_type_id
      from public.historical_case_rule_relationship_types hcrrt
      where hcrrt.relationship_code = 'relevant_to';

      insert into public.historical_case_version_logical_rules (
        historical_case_version_id,
        rule_code,
        relationship_type_id
      )
      values (
        target_case_version_id,
        'P6E_RULE_D',
        relationship_type_id
      );

      update public.historical_case_versions
      set governance_status = 'active'
      where id = target_case_version_id;
    end
    $$;
  $sql$,
  '23514',
  null,
  'activation fails when a lesson requires both layers and only Phase 4 connectivity exists'
);

select throws_ok(
  $sql$
    do $$
    declare
      target_case_version_id bigint;
      target_document_id bigint;
      relationship_type_id bigint;
    begin
      select hcv.id into target_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-964'
        and hcv.version_number = 1;

      select kd.id into target_document_id
      from public.knowledge_documents kd
      where kd.document_code = 'P6E-DOC-B';

      select hckrt.id into relationship_type_id
      from public.historical_case_knowledge_relationship_types hckrt
      where hckrt.relationship_code = 'current_guidance_to_consult';

      insert into public.historical_case_version_knowledge_documents (
        historical_case_version_id,
        knowledge_document_id,
        relationship_type_id
      )
      values (
        target_case_version_id,
        target_document_id,
        relationship_type_id
      );

      update public.historical_case_versions
      set governance_status = 'active'
      where id = target_case_version_id;
    end
    $$;
  $sql$,
  '23514',
  null,
  'activation fails when a lesson requires both layers and only Phase 5 connectivity exists'
);

select lives_ok(
  $sql$
    do $$
    declare
      target_case_version_id bigint;
      phase_4_relationship_type_id bigint;
      phase_5_relationship_type_id bigint;
      target_document_id bigint;
    begin
      select hcv.id into target_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-964'
        and hcv.version_number = 1;

      select hcrrt.id into phase_4_relationship_type_id
      from public.historical_case_rule_relationship_types hcrrt
      where hcrrt.relationship_code = 'relevant_to';

      select hckrt.id into phase_5_relationship_type_id
      from public.historical_case_knowledge_relationship_types hckrt
      where hckrt.relationship_code = 'current_guidance_to_consult';

      select kd.id into target_document_id
      from public.knowledge_documents kd
      where kd.document_code = 'P6E-DOC-B';

      insert into public.historical_case_version_logical_rules (
        historical_case_version_id,
        rule_code,
        relationship_type_id
      )
      values (
        target_case_version_id,
        'P6E_RULE_D',
        phase_4_relationship_type_id
      );

      insert into public.historical_case_version_knowledge_documents (
        historical_case_version_id,
        knowledge_document_id,
        relationship_type_id
      )
      values (
        target_case_version_id,
        target_document_id,
        phase_5_relationship_type_id
      );

      update public.historical_case_versions
      set governance_status = 'active'
      where id = target_case_version_id;
    end
    $$;
  $sql$,
  'activation succeeds when both Phase 4 and Phase 5 connectivity exist for a both-layers lesson'
);

select lives_ok(
  $sql$
    update public.historical_case_versions hcv
    set governance_status = 'active'
    from public.historical_cases hc
    where hc.id = hcv.historical_case_id
      and hc.case_code = 'HC-965'
      and hcv.version_number = 1;
  $sql$,
  'no_current_rule_implication does not require any current-authority links for activation'
);

select throws_ok(
  $sql$
    update public.historical_case_versions hcv
    set governance_status = 'active'
    from public.historical_cases hc
    where hc.id = hcv.historical_case_id
      and hc.case_code = 'HC-966'
      and hcv.version_number = 1;
  $sql$,
  '23514',
  null,
  'current_status_unknown cannot activate while precedent_availability remains normal active precedence'
);

select lives_ok(
  $sql$
    update public.historical_case_versions hcv
    set
      precedent_availability = 'limited',
      governance_status = 'active'
    from public.historical_cases hc
    where hc.id = hcv.historical_case_id
      and hc.case_code = 'HC-966'
      and hcv.version_number = 1;
  $sql$,
  'current_status_unknown can activate once precedent_availability is limited'
);

select throws_ok(
  $sql$
    update public.historical_case_versions hcv
    set governance_status = 'active'
    from public.historical_cases hc
    where hc.id = hcv.historical_case_id
      and hc.case_code = 'HC-967'
      and hcv.version_number = 1;
  $sql$,
  '23514',
  null,
  'potential_conflict_with_current_knowledge cannot activate without any current-authority connectivity'
);

select throws_ok(
  $sql$
    do $$
    declare
      target_case_version_id bigint;
      target_document_id bigint;
      relationship_type_id bigint;
    begin
      select hcv.id into target_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-967'
        and hcv.version_number = 1;

      select kd.id into target_document_id
      from public.knowledge_documents kd
      where kd.document_code = 'P6E-DOC-A';

      select hckrt.id into relationship_type_id
      from public.historical_case_knowledge_relationship_types hckrt
      where hckrt.relationship_code = 'current_authority_supersedes_historical_practice';

      insert into public.historical_case_version_knowledge_documents (
        historical_case_version_id,
        knowledge_document_id,
        relationship_type_id
      )
      values (
        target_case_version_id,
        target_document_id,
        relationship_type_id
      );

      update public.historical_case_versions
      set governance_status = 'active'
      where id = target_case_version_id;
    end
    $$;
  $sql$,
  '23514',
  null,
  'potential_conflict_with_current_knowledge still fails activation when historical-value-only marking is absent'
);

select lives_ok(
  $sql$
    do $$
    declare
      target_case_version_id bigint;
      target_document_id bigint;
      relationship_type_id bigint;
    begin
      select hcv.id into target_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-967'
        and hcv.version_number = 1;

      select kd.id into target_document_id
      from public.knowledge_documents kd
      where kd.document_code = 'P6E-DOC-A';

      select hckrt.id into relationship_type_id
      from public.historical_case_knowledge_relationship_types hckrt
      where hckrt.relationship_code = 'current_authority_supersedes_historical_practice';

      insert into public.historical_case_version_knowledge_documents (
        historical_case_version_id,
        knowledge_document_id,
        relationship_type_id
      )
      values (
        target_case_version_id,
        target_document_id,
        relationship_type_id
      );

      update public.historical_case_version_decisions
      set historical_value_only = true
      where historical_case_version_id = target_case_version_id
        and decision_statement = 'HC-967 may conflict with current knowledge if reused directly.';

      update public.historical_case_versions
      set governance_status = 'active'
      where id = target_case_version_id;
    end
    $$;
  $sql$,
  'potential_conflict_with_current_knowledge can activate once current-authority connectivity exists and historical-value-only marking is explicit'
);

select lives_ok(
  $sql$
    do $$
    declare
      target_case_version_id bigint;
      phase_4_relationship_type_id bigint;
      phase_5_relationship_type_id bigint;
      target_rule_version_id bigint;
      target_document_id bigint;
      target_document_version_id bigint;
      logical_rule_id bigint;
    begin
      select hcv.id into target_case_version_id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-968'
        and hcv.version_number = 1;

      select hcrrt.id into phase_4_relationship_type_id
      from public.historical_case_rule_relationship_types hcrrt
      where hcrrt.relationship_code = 'relevant_to';

      select hckrt.id into phase_5_relationship_type_id
      from public.historical_case_knowledge_relationship_types hckrt
      where hckrt.relationship_code = 'current_guidance_to_consult';

      select rc.id into target_rule_version_id
      from public.rule_catalogue rc
      where rc.rule_code = 'P6E_RULE_A'
        and rc.rule_version = 1;

      select kd.id into target_document_id
      from public.knowledge_documents kd
      where kd.document_code = 'P6E-DOC-A';

      select kdv.id into target_document_version_id
      from public.knowledge_document_versions kdv
      join public.knowledge_documents kd
        on kd.id = kdv.document_id
      where kd.document_code = 'P6E-DOC-A'
        and kdv.version_number = 1;

      insert into public.historical_case_version_logical_rules (
        historical_case_version_id,
        rule_code,
        relationship_type_id,
        relationship_note
      )
      values (
        target_case_version_id,
        'P6E_RULE_A',
        phase_4_relationship_type_id,
        'Active immutability logical rule.'
      );

      insert into public.historical_case_version_rule_versions (
        historical_case_version_id,
        rule_version_id,
        relationship_type_id,
        relationship_note
      )
      values (
        target_case_version_id,
        target_rule_version_id,
        phase_4_relationship_type_id,
        'Active immutability exact rule version.'
      );

      insert into public.historical_case_version_knowledge_documents (
        historical_case_version_id,
        knowledge_document_id,
        relationship_type_id,
        relationship_note
      )
      values (
        target_case_version_id,
        target_document_id,
        phase_5_relationship_type_id,
        'Active immutability stable knowledge document.'
      );

      insert into public.historical_case_version_knowledge_document_versions (
        historical_case_version_id,
        knowledge_document_version_id,
        relationship_type_id,
        relationship_note
      )
      values (
        target_case_version_id,
        target_document_version_id,
        phase_5_relationship_type_id,
        'Active immutability exact knowledge document version.'
      );

      update public.historical_case_versions
      set governance_status = 'active'
      where id = target_case_version_id;
    end
    $$;
  $sql$,
  'an active case version can carry a complete current-authority connectivity snapshot before immutability locks it'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_logical_rules (
      historical_case_version_id,
      rule_code,
      relationship_type_id
    )
    select
      hcv.id,
      'P6E_RULE_B',
      hcrrt.id
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    cross join public.historical_case_rule_relationship_types hcrrt
    where hc.case_code = 'HC-968'
      and hcv.version_number = 1
      and hcrrt.relationship_code = 'illustrates';
  $sql$,
  '23514',
  null,
  'non-draft case versions block logical-rule relationship inserts'
);

select throws_ok(
  $sql$
    update public.historical_case_version_logical_rules hcvlr
    set relationship_note = 'edited after activation'
    from public.historical_case_versions hcv,
         public.historical_cases hc
    where hcv.id = hcvlr.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and hc.case_code = 'HC-968'
      and hcvlr.rule_code = 'P6E_RULE_A';
  $sql$,
  '23514',
  null,
  'non-draft case versions block logical-rule relationship updates'
);

select throws_ok(
  $sql$
    delete from public.historical_case_version_logical_rules hcvlr
    using public.historical_case_versions hcv,
          public.historical_cases hc
    where hcv.id = hcvlr.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and hc.case_code = 'HC-968'
      and hcvlr.rule_code = 'P6E_RULE_A';
  $sql$,
  '23514',
  null,
  'non-draft case versions block logical-rule relationship deletes'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_rule_versions (
      historical_case_version_id,
      rule_version_id,
      relationship_type_id
    )
    select
      hcv.id,
      rc.id,
      hcrrt.id
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    join public.rule_catalogue rc
      on rc.rule_code = 'P6E_RULE_B'
     and rc.rule_version = 1
    cross join public.historical_case_rule_relationship_types hcrrt
    where hc.case_code = 'HC-968'
      and hcv.version_number = 1
      and hcrrt.relationship_code = 'illustrates';
  $sql$,
  '23514',
  null,
  'non-draft case versions block exact rule-version relationship inserts'
);

select throws_ok(
  $sql$
    update public.historical_case_version_rule_versions hcvrv
    set relationship_note = 'edited after activation'
    from public.historical_case_versions hcv,
         public.historical_cases hc,
         public.rule_catalogue rc
    where hcv.id = hcvrv.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and rc.id = hcvrv.rule_version_id
      and hc.case_code = 'HC-968'
      and rc.rule_code = 'P6E_RULE_A';
  $sql$,
  '23514',
  null,
  'non-draft case versions block exact rule-version relationship updates'
);

select throws_ok(
  $sql$
    delete from public.historical_case_version_rule_versions hcvrv
    using public.historical_case_versions hcv,
          public.historical_cases hc,
          public.rule_catalogue rc
    where hcv.id = hcvrv.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and rc.id = hcvrv.rule_version_id
      and hc.case_code = 'HC-968'
      and rc.rule_code = 'P6E_RULE_A';
  $sql$,
  '23514',
  null,
  'non-draft case versions block exact rule-version relationship deletes'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_knowledge_documents (
      historical_case_version_id,
      knowledge_document_id,
      relationship_type_id
    )
    select
      hcv.id,
      kd.id,
      hckrt.id
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    join public.knowledge_documents kd
      on kd.document_code = 'P6E-DOC-B'
    cross join public.historical_case_knowledge_relationship_types hckrt
    where hc.case_code = 'HC-968'
      and hcv.version_number = 1
      and hckrt.relationship_code = 'current_context_relevant_to_case';
  $sql$,
  '23514',
  null,
  'non-draft case versions block stable knowledge-document relationship inserts'
);

select throws_ok(
  $sql$
    update public.historical_case_version_knowledge_documents hcvkd
    set relationship_note = 'edited after activation'
    from public.historical_case_versions hcv,
         public.historical_cases hc,
         public.knowledge_documents kd
    where hcv.id = hcvkd.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and kd.id = hcvkd.knowledge_document_id
      and hc.case_code = 'HC-968'
      and kd.document_code = 'P6E-DOC-A';
  $sql$,
  '23514',
  null,
  'non-draft case versions block stable knowledge-document relationship updates'
);

select throws_ok(
  $sql$
    delete from public.historical_case_version_knowledge_documents hcvkd
    using public.historical_case_versions hcv,
          public.historical_cases hc,
          public.knowledge_documents kd
    where hcv.id = hcvkd.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and kd.id = hcvkd.knowledge_document_id
      and hc.case_code = 'HC-968'
      and kd.document_code = 'P6E-DOC-A';
  $sql$,
  '23514',
  null,
  'non-draft case versions block stable knowledge-document relationship deletes'
);

select throws_ok(
  $sql$
    insert into public.historical_case_version_knowledge_document_versions (
      historical_case_version_id,
      knowledge_document_version_id,
      relationship_type_id
    )
    select
      hcv.id,
      kdv.id,
      hckrt.id
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    join public.knowledge_document_versions kdv
      on kdv.version_number = 1
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
     and kd.document_code = 'P6E-DOC-B'
    cross join public.historical_case_knowledge_relationship_types hckrt
    where hc.case_code = 'HC-968'
      and hcv.version_number = 1
      and hckrt.relationship_code = 'current_context_relevant_to_case';
  $sql$,
  '23514',
  null,
  'non-draft case versions block exact knowledge-document-version relationship inserts'
);

select throws_ok(
  $sql$
    update public.historical_case_version_knowledge_document_versions hcvkdv
    set relationship_note = 'edited after activation'
    from public.historical_case_versions hcv,
         public.historical_cases hc,
         public.knowledge_document_versions kdv,
         public.knowledge_documents kd
    where hcv.id = hcvkdv.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and kdv.id = hcvkdv.knowledge_document_version_id
      and kd.id = kdv.document_id
      and hc.case_code = 'HC-968'
      and kd.document_code = 'P6E-DOC-A';
  $sql$,
  '23514',
  null,
  'non-draft case versions block exact knowledge-document-version relationship updates'
);

select throws_ok(
  $sql$
    delete from public.historical_case_version_knowledge_document_versions hcvkdv
    using public.historical_case_versions hcv,
          public.historical_cases hc,
          public.knowledge_document_versions kdv,
          public.knowledge_documents kd
    where hcv.id = hcvkdv.historical_case_version_id
      and hc.id = hcv.historical_case_id
      and kdv.id = hcvkdv.knowledge_document_version_id
      and kd.id = kdv.document_id
      and hc.case_code = 'HC-968'
      and kd.document_code = 'P6E-DOC-A';
  $sql$,
  '23514',
  null,
  'non-draft case versions block exact knowledge-document-version relationship deletes'
);

select lives_ok(
  $sql$
    do $$
    declare
      logical_rule_count_before bigint;
      rule_catalogue_count_before bigint;
      knowledge_document_count_before bigint;
      knowledge_document_version_count_before bigint;
      logical_rule_count_after bigint;
      rule_catalogue_count_after bigint;
      knowledge_document_count_after bigint;
      knowledge_document_version_count_after bigint;
    begin
      select count(*) into logical_rule_count_before from public.logical_rules;
      select count(*) into rule_catalogue_count_before from public.rule_catalogue;
      select count(*) into knowledge_document_count_before from public.knowledge_documents;
      select count(*) into knowledge_document_version_count_before from public.knowledge_document_versions;

      delete from public.historical_case_version_logical_rules hcvlr
      using public.historical_case_versions hcv,
            public.historical_cases hc
      where hcv.id = hcvlr.historical_case_version_id
        and hc.id = hcv.historical_case_id
        and hc.case_code = 'HC-969';

      delete from public.historical_case_version_knowledge_documents hcvkd
      using public.historical_case_versions hcv,
            public.historical_cases hc
      where hcv.id = hcvkd.historical_case_version_id
        and hc.id = hcv.historical_case_id
        and hc.case_code = 'HC-969';

      select count(*) into logical_rule_count_after from public.logical_rules;
      select count(*) into rule_catalogue_count_after from public.rule_catalogue;
      select count(*) into knowledge_document_count_after from public.knowledge_documents;
      select count(*) into knowledge_document_version_count_after from public.knowledge_document_versions;

      if logical_rule_count_before <> logical_rule_count_after
         or rule_catalogue_count_before <> rule_catalogue_count_after
         or knowledge_document_count_before <> knowledge_document_count_after
         or knowledge_document_version_count_before <> knowledge_document_version_count_after then
        raise exception 'Phase 4 or Phase 5 target rows changed when Phase 6 relationships were deleted';
      end if;
    end
    $$;
  $sql$,
  'creating and deleting Phase 6 relationships does not mutate Phase 4 or Phase 5 target rows'
);

select results_eq(
  $sql$
    select c.relname
    from pg_class c
    join pg_namespace n
      on n.oid = c.relnamespace
    where n.nspname = 'public'
      and c.relname in (
        'historical_case_rule_relationship_types',
        'historical_case_version_logical_rules',
        'historical_case_version_rule_versions',
        'historical_case_knowledge_relationship_types',
        'historical_case_version_knowledge_documents',
        'historical_case_version_knowledge_document_versions'
      )
      and c.relrowsecurity
    order by c.relname
  $sql$,
  $sql$
    values
      ('historical_case_knowledge_relationship_types'::name),
      ('historical_case_rule_relationship_types'::name),
      ('historical_case_version_knowledge_document_versions'::name),
      ('historical_case_version_knowledge_documents'::name),
      ('historical_case_version_logical_rules'::name),
      ('historical_case_version_rule_versions'::name)
  $sql$,
  'RLS is enabled on all Phase 6.2E relationship tables'
);

select is(
  (
    select count(*)
    from information_schema.role_table_grants rtg
    where rtg.table_schema = 'public'
      and rtg.table_name in (
        'historical_case_rule_relationship_types',
        'historical_case_version_logical_rules',
        'historical_case_version_rule_versions',
        'historical_case_knowledge_relationship_types',
        'historical_case_version_knowledge_documents',
        'historical_case_version_knowledge_document_versions'
      )
      and rtg.grantee in ('anon', 'authenticated', 'service_role')
      and rtg.privilege_type in ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'REFERENCES', 'TRIGGER', 'TRUNCATE')
  ),
  0::bigint,
  'ordinary roles have no direct grants on the Phase 6.2E relationship tables'
);

select throws_ok(
  $sql$
    select public._test_count_as('anon', $query$select * from public.historical_case_rule_relationship_types$query$);
  $sql$,
  '42501',
  null,
  'anon cannot directly read historical_case_rule_relationship_types'
);

select throws_ok(
  $sql$
    select public._test_count_as('authenticated', $query$select * from public.historical_case_version_knowledge_documents$query$);
  $sql$,
  '42501',
  null,
  'authenticated cannot directly read historical_case_version_knowledge_documents'
);

select *
from finish();

rollback;
