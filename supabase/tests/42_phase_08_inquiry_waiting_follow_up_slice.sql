begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

select plan(7);

select ok(
  exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'rental_case_follow_ups'
      and column_name = 'semantic_identity_key'
  ),
  'follow-ups expose semantic_identity_key'
);

select ok(
  exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'rental_case_follow_ups'
      and column_name = 'sequence_number'
  ),
  'follow-ups expose sequence_number'
);

select ok(
  exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'rental_case_follow_ups'
      and column_name = 'context_payload'
  ),
  'follow-ups expose context_payload'
);

insert into public.rental_cases (
  case_reference_code,
  lifecycle_state,
  case_revision,
  rental_type_code,
  service_level_or_type,
  client_account_ref,
  primary_contact_ref,
  commercial_summary_status,
  operational_summary_status,
  is_active
)
values (
  'RC-1102',
  'inquiry_active',
  0,
  'custom_scope',
  'studio_rental',
  'client:1102',
  'contact:1102',
  'unknown',
  'unknown',
  true
);

select lives_ok(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-1102'
    )
    insert into public.rental_case_follow_ups (
      rental_case_id,
      reason_code,
      due_at,
      urgency_level,
      attempt_count,
      status,
      semantic_identity_key,
      sequence_number,
      waiting_for_role,
      waiting_for_reference,
      cadence_policy_code,
      next_action_type,
      context_payload,
      created_at,
      updated_at
    )
    select
      id,
      'inquiry_missing_information',
      timezone('utc', now()),
      'medium',
      0,
      'scheduled',
      'inquiry_follow_up:test-seq-1',
      1,
      'client',
      'contact:1102',
      'inquiry_cold_weekly',
      'REQUEST_CLIENT_INFORMATION',
      '{"open_question_ids":[1,2],"required_field_codes":["guest_count","event_type"]}'::jsonb,
      timezone('utc', now()),
      timezone('utc', now())
    from target_case;
  $sql$,
  'semantic inquiry follow-up row can be inserted'
);

select results_eq(
  $sql$
    select sequence_number, jsonb_typeof(context_payload)
    from public.rental_case_follow_ups
    where semantic_identity_key = 'inquiry_follow_up:test-seq-1'
  $sql$,
  $sql$
    values (1, 'object'::text)
  $sql$,
  'sequence_number and object context payload persist as expected'
);

select throws_ok(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-1102'
    )
    insert into public.rental_case_follow_ups (
      rental_case_id,
      reason_code,
      due_at,
      urgency_level,
      attempt_count,
      status,
      semantic_identity_key,
      sequence_number,
      waiting_for_role,
      waiting_for_reference,
      cadence_policy_code,
      next_action_type,
      context_payload,
      created_at,
      updated_at
    )
    select
      id,
      'inquiry_missing_information',
      timezone('utc', now()),
      'medium',
      0,
      'scheduled',
      'inquiry_follow_up:test-seq-1',
      1,
      'client',
      'contact:1102',
      'inquiry_cold_weekly',
      'REQUEST_CLIENT_INFORMATION',
      '{"open_question_ids":[1,2]}'::jsonb,
      timezone('utc', now()),
      timezone('utc', now())
    from target_case;
  $sql$,
  '23505',
  null,
  'duplicate semantic inquiry follow-up is rejected'
);

select lives_ok(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-1102'
    )
    insert into public.rental_case_follow_ups (
      rental_case_id,
      reason_code,
      due_at,
      urgency_level,
      attempt_count,
      status,
      semantic_identity_key,
      sequence_number,
      waiting_for_role,
      waiting_for_reference,
      cadence_policy_code,
      next_action_type,
      context_payload,
      created_at,
      updated_at
    )
    select
      id,
      'inquiry_missing_information',
      timezone('utc', now()),
      'medium',
      0,
      'scheduled',
      'inquiry_follow_up:test-seq-2',
      2,
      'client',
      'contact:1102',
      'inquiry_cold_weekly',
      'REQUEST_CLIENT_INFORMATION',
      '{"open_question_ids":[3,4]}'::jsonb,
      timezone('utc', now()),
      timezone('utc', now())
    from target_case;
  $sql$,
  'second semantic inquiry follow-up sequence can be inserted'
);

select * from finish();
rollback;
