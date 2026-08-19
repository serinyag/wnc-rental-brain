begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

select plan(24);

select ok(to_regclass('public.rental_case_facts') is not null, 'rental_case_facts table exists');
select ok(to_regclass('public.inbound_source_records') is not null, 'inbound_source_records table exists');
select ok(to_regclass('public.inbound_observations') is not null, 'inbound_observations table exists');
select ok(to_regclass('public.inbound_observation_effects') is not null, 'inbound_observation_effects table exists');

select results_eq(
  $sql$
    select c.relname
    from pg_class c
    join pg_namespace n
      on n.oid = c.relnamespace
    where n.nspname = 'public'
      and c.relname in (
        'rental_case_facts',
        'inbound_source_records',
        'inbound_observations',
        'inbound_observation_effects'
      )
      and c.relrowsecurity
    order by c.relname
  $sql$,
  $sql$
    values
      ('inbound_observation_effects'::name),
      ('inbound_observations'::name),
      ('inbound_source_records'::name),
      ('rental_case_facts'::name)
  $sql$,
  'RLS is enabled on inbound observation foundation tables'
);

select is(
  (
    select count(*)
    from information_schema.role_table_grants
    where table_schema = 'public'
      and table_name in (
        'rental_case_facts',
        'inbound_source_records',
        'inbound_observations',
        'inbound_observation_effects'
      )
      and grantee in ('anon', 'authenticated', 'service_role')
      and privilege_type in ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'REFERENCES', 'TRIGGER', 'TRUNCATE')
  ),
  0::bigint,
  'new inbound observation tables grant no ordinary-role table privileges'
);

select lives_ok(
  $sql$
    insert into public.rental_cases (
      case_reference_code,
      lifecycle_state,
      case_revision,
      rental_type_code,
      commercial_summary_status,
      operational_summary_status,
      is_active
    )
    values (
      'RC-900',
      'inquiry_active',
      0,
      'studio_space',
      'unknown',
      'unknown',
      true
    );
  $sql$,
  'fixture rental case can be created for inbound observation tests'
);

select lives_ok(
  $sql$
    insert into public.rental_case_facts (
      rental_case_id,
      field_code,
      domain_code,
      value_payload,
      source_reference,
      established_case_revision
    )
    select
      id,
      'guest_count',
      'event_profile',
      '30'::jsonb,
      'fixture:fact:1',
      0
    from public.rental_cases
    where case_reference_code = 'RC-900';
  $sql$,
  'governed rental case facts can be inserted for current scope snapshot support'
);

select throws_ok(
  $sql$
    insert into public.rental_case_facts (
      rental_case_id,
      field_code,
      domain_code,
      value_payload,
      source_reference,
      established_case_revision
    )
    select
      id,
      'guest_count',
      'event_profile',
      '60'::jsonb,
      'fixture:fact:2',
      1
    from public.rental_cases
    where case_reference_code = 'RC-900';
  $sql$,
  '23505',
  null,
  'one current rental_case_fact row is allowed per case field'
);

select lives_ok(
  $sql$
    insert into public.inbound_source_records (
      source_system_code,
      source_record_type,
      dedupe_key,
      source_hash,
      association_status,
      association_basis,
      occurred_at
    )
    values (
      'email',
      'message',
      'src:1',
      'hash:src:1',
      'case_association_required',
      'fixture',
      timezone('utc', now())
    );
  $sql$,
  'provider-neutral inbound source records can be stored without a resolved case'
);

select throws_ok(
  $sql$
    insert into public.inbound_source_records (
      source_system_code,
      source_record_type,
      dedupe_key,
      source_hash,
      association_status,
      occurred_at
    )
    values (
      'email',
      'message',
      'src:2',
      'hash:src:2',
      'resolved',
      timezone('utc', now())
    );
  $sql$,
  '23514',
  null,
  'resolved inbound source records require a resolved rental case id'
);

select throws_ok(
  $sql$
    insert into public.inbound_source_records (
      source_system_code,
      source_record_type,
      dedupe_key,
      source_hash,
      resolved_rental_case_id,
      association_status,
      occurred_at
    )
    select
      'email',
      'message',
      'src:3',
      'hash:src:3',
      id,
      'case_association_required',
      timezone('utc', now())
    from public.rental_cases
    where case_reference_code = 'RC-900';
  $sql$,
  '23514',
  null,
  'non-resolved inbound sources may not carry a resolved rental case id'
);

select throws_ok(
  $sql$
    insert into public.inbound_source_records (
      source_system_code,
      source_record_type,
      dedupe_key,
      source_hash,
      association_status,
      occurred_at
    )
    values (
      'email',
      'message',
      'src:1',
      'hash:src:1:duplicate',
      'case_association_required',
      timezone('utc', now())
    );
  $sql$,
  '23505',
  null,
  'source dedupe key uniqueness prevents duplicate semantic source rows'
);

select lives_ok(
  $sql$
    insert into public.inbound_observations (
      inbound_source_record_id,
      rental_case_id,
      reported_field_code,
      reported_domain_code,
      target_field_code,
      target_domain_code,
      observation_type,
      claim_kind,
      candidate_value_payload,
      source_evidence_reference,
      status,
      observation_identity_key,
      extraction_confidence,
      observed_against_case_revision
    )
    select
      s.id,
      c.id,
      'guest_count',
      'event_profile',
      'guest_count',
      'event_profile',
      'change_candidate',
      'change_request',
      '60'::jsonb,
      'msg:1#line:3',
      'validated',
      'obs:guest-count:60',
      0.99,
      0
    from public.inbound_source_records s
    cross join public.rental_cases c
    where s.dedupe_key = 'src:1'
      and c.case_reference_code = 'RC-900';
  $sql$,
  'inbound observations can be stored as structured candidate evidence'
);

select throws_ok(
  $sql$
    insert into public.inbound_observations (
      inbound_source_record_id,
      reported_field_code,
      observation_type,
      claim_kind,
      candidate_value_payload,
      source_evidence_reference,
      status,
      observation_identity_key,
      extraction_confidence
    )
    select
      id,
      'guest_count',
      'fact_candidate',
      'new_information',
      '30'::jsonb,
      'msg:1#line:4',
      'validated',
      'obs:bad-confidence',
      1.2
    from public.inbound_source_records
    where dedupe_key = 'src:1';
  $sql$,
  '23514',
  null,
  'observation confidence is constrained to the closed interval from 0 to 1'
);

select throws_ok(
  $sql$
    insert into public.inbound_observations (
      inbound_source_record_id,
      reported_field_code,
      target_field_code,
      observation_type,
      claim_kind,
      candidate_value_payload,
      source_evidence_reference,
      status,
      observation_identity_key
    )
    select
      id,
      'guest_count',
      'guest_count',
      'fact_candidate',
      'new_information',
      '30'::jsonb,
      'msg:1#line:5',
      'validated',
      'obs:bad-target-pair'
    from public.inbound_source_records
    where dedupe_key = 'src:1';
  $sql$,
  '23514',
  null,
  'target field and target domain must be set together or not at all'
);

select throws_ok(
  $sql$
    insert into public.inbound_observations (
      inbound_source_record_id,
      rental_case_id,
      reported_field_code,
      reported_domain_code,
      target_field_code,
      target_domain_code,
      observation_type,
      claim_kind,
      candidate_value_payload,
      source_evidence_reference,
      status,
      observation_identity_key
    )
    select
      s.id,
      c.id,
      'guest_count',
      'event_profile',
      'guest_count',
      'event_profile',
      'change_candidate',
      'change_request',
      '60'::jsonb,
      'msg:1#line:6',
      'validated',
      'obs:guest-count:60'
    from public.inbound_source_records s
    cross join public.rental_cases c
    where s.dedupe_key = 'src:1'
      and c.case_reference_code = 'RC-900';
  $sql$,
  '23505',
  null,
  'observation identity is unique per inbound source record'
);

select lives_ok(
  $sql$
    insert into public.rental_case_open_questions (
      rental_case_id,
      question_type,
      domain_code,
      human_question_text,
      blocking_scope,
      status
    )
    select
      id,
      'expected_guest_count',
      'event_profile',
      'How many guests are expected?',
      'transition',
      'open'
    from public.rental_cases
    where case_reference_code = 'RC-900';

    insert into public.rental_case_proposed_changes (
      rental_case_id,
      change_kind,
      domain_code,
      prior_value_payload,
      proposed_value_payload,
      source_reference,
      detected_at,
      impact_classification,
      affected_domain_codes,
      review_posture,
      status
    )
    select
      id,
      'guest_count',
      'event_profile',
      '30'::jsonb,
      '60'::jsonb,
      'inbound_observation:1',
      timezone('utc', now()),
      'material_impact',
      array['event_profile']::text[],
      'human_only',
      'proposed'
    from public.rental_cases
    where case_reference_code = 'RC-900';
  $sql$,
  'supporting workflow rows can be created for same-case effect linkage checks'
);

select lives_ok(
  $sql$
    insert into public.inbound_observation_effects (
      inbound_observation_id,
      rental_case_id,
      disposition_code,
      revalidation_required,
      stale_observation,
      reason_codes,
      linked_proposed_change_id
    )
    select
      o.id,
      c.id,
      'create_proposed_change',
      true,
      false,
      array['existing_value_changed']::text[],
      p.id
    from public.inbound_observations o
    join public.rental_cases c
      on c.case_reference_code = 'RC-900'
    join public.rental_case_proposed_changes p
      on p.rental_case_id = c.id
     and p.change_kind = 'guest_count'
    where o.observation_identity_key = 'obs:guest-count:60';
  $sql$,
  'observation effects can link to same-case proposed changes'
);

select throws_ok(
  $sql$
    insert into public.inbound_source_records (
      source_system_code,
      source_record_type,
      dedupe_key,
      source_hash,
      association_status,
      occurred_at
    )
    values (
      'manual_input',
      'operator_note',
      'src:cross-case',
      'hash:src:cross-case',
      'case_association_required',
      timezone('utc', now())
    );

    insert into public.inbound_observations (
      inbound_source_record_id,
      rental_case_id,
      reported_field_code,
      reported_domain_code,
      target_field_code,
      target_domain_code,
      observation_type,
      claim_kind,
      candidate_value_payload,
      source_evidence_reference,
      status,
      observation_identity_key
    )
    select
      s.id,
      c.id,
      'guest_count',
      'event_profile',
      'guest_count',
      'event_profile',
      'change_candidate',
      'change_request',
      '75'::jsonb,
      'msg:cross-case#line:1',
      'validated',
      'obs:cross-case'
    from public.inbound_source_records s
    cross join public.rental_cases c
    where s.dedupe_key = 'src:cross-case'
      and c.case_reference_code = 'RC-900';

    insert into public.rental_cases (
      case_reference_code,
      lifecycle_state,
      case_revision,
      rental_type_code,
      commercial_summary_status,
      operational_summary_status,
      is_active
    )
    values (
      'RC-901',
      'inquiry_active',
      0,
      'studio_space',
      'unknown',
      'unknown',
      true
    );

    insert into public.rental_case_proposed_changes (
      rental_case_id,
      change_kind,
      domain_code,
      proposed_value_payload,
      detected_at,
      status
    )
    select
      id,
      'guest_count',
      'event_profile',
      '75'::jsonb,
      timezone('utc', now()),
      'proposed'
    from public.rental_cases
    where case_reference_code = 'RC-901';

    insert into public.inbound_observation_effects (
      inbound_observation_id,
      rental_case_id,
      disposition_code,
      revalidation_required,
      stale_observation,
      reason_codes,
      linked_proposed_change_id
    )
    select
      o.id,
      c.id,
      'create_proposed_change',
      true,
      false,
      array['cross_case_attempt']::text[],
      p.id
    from public.inbound_observations o
    join public.rental_cases c
      on c.case_reference_code = 'RC-900'
    join public.rental_case_proposed_changes p
      on p.rental_case_id = (
        select id from public.rental_cases where case_reference_code = 'RC-901'
      )
    where o.observation_identity_key = 'obs:cross-case';
  $sql$,
  '23503',
  null,
  'cross-case effect links are rejected by same-case foreign keys'
);

select throws_ok(
  $sql$
    insert into public.inbound_observation_effects (
      inbound_observation_id,
      rental_case_id,
      disposition_code,
      revalidation_required,
      stale_observation,
      reason_codes
    )
    select
      id,
      rental_case_id,
      'create_proposed_change',
      true,
      false,
      array['missing_target']::text[]
    from public.inbound_observations
    where observation_identity_key = 'obs:guest-count:60';
  $sql$,
  '23514',
  null,
  'proposed-change dispositions require a linked proposed change id'
);

select throws_ok(
  $sql$
    update public.inbound_source_records
    set association_basis = 'mutated'
    where dedupe_key = 'src:1';
  $sql$,
  '23514',
  null,
  'inbound source records are append-only on update'
);

select throws_ok(
  $sql$
    delete from public.inbound_observation_effects
    where disposition_code = 'create_proposed_change';
  $sql$,
  '23514',
  null,
  'inbound observation effects are append-only on delete'
);

select is(
  (
    select lifecycle_state
    from public.rental_cases
    where case_reference_code = 'RC-900'
  ),
  'inquiry_active'::text,
  'observation persistence does not mutate lifecycle state'
);

select * from finish();

rollback;
