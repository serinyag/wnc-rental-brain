begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

select plan(12);

select ok(
  to_regproc('private.commit_rental_case_lifecycle_transition') is not null,
  'lifecycle transition commit helper exists'
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
  dormant_origin_state,
  resume_target_state,
  dormant_reason_code,
  dormant_review_at,
  is_active
)
values
  (
    'RC-950',
    'inquiry_active',
    0,
    'studio_space',
    'studio_rental',
    'client:950',
    'contact:950',
    'unknown',
    'unknown',
    null,
    null,
    null,
    null,
    true
  ),
  (
    'RC-951',
    'proposal_pending_client',
    2,
    'studio_space',
    'studio_rental',
    'client:951',
    'contact:951',
    'unknown',
    'unknown',
    null,
    null,
    null,
    null,
    true
  ),
  (
    'RC-952',
    'dormant',
    3,
    'studio_space',
    'studio_rental',
    'client:952',
    'contact:952',
    'unknown',
    'unknown',
    'proposal_pending_client',
    'confirmation_pending',
    'waiting_for_client',
    '2026-08-20T12:00:00Z'::timestamptz,
    true
  ),
  (
    'RC-953',
    'confirmation_pending',
    1,
    'studio_space',
    'studio_rental',
    'client:953',
    'contact:953',
    'unknown',
    'unknown',
    null,
    null,
    null,
    null,
    true
  ),
  (
    'RC-954',
    'inquiry_active',
    0,
    'studio_space',
    'studio_rental',
    'client:954',
    'contact:954',
    'unknown',
    'unknown',
    null,
    null,
    null,
    null,
    true
  );

select results_eq(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-950'
    )
    select
      previous_state,
      new_state,
      previous_revision,
      new_revision,
      manual_override,
      actor_reference,
      source_type
    from private.commit_rental_case_lifecycle_transition(
      (select id from target_case),
      0,
      'inquiry_active',
      'proposal_in_progress',
      'proposal_started',
      'phase8_db_test',
      'fixture:standard',
      'operator',
      'operator:1',
      null,
      false,
      'lifecycle_transition_committed',
      '{"fixture":true}'::jsonb,
      null,
      null,
      null,
      null
    )
  $sql$,
  $sql$
    values (
      'inquiry_active'::text,
      'proposal_in_progress'::text,
      0::integer,
      1::integer,
      false,
      'operator:1'::text,
      'phase8_db_test'::text
    )
  $sql$,
  'standard lifecycle commit returns the expected audit row'
);

select results_eq(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-950'
    )
    select
      rc.lifecycle_state,
      rc.case_revision,
      (
        select count(*)
        from public.workflow_events we
        where we.rental_case_id = rc.id
      )::bigint as workflow_event_count,
      (
        select count(*)
        from public.rental_case_lifecycle_transitions lt
        where lt.rental_case_id = rc.id
      )::bigint as transition_count
    from public.rental_cases rc
    where rc.id = (select id from target_case)
  $sql$,
  $sql$
    values (
      'proposal_in_progress'::text,
      1::integer,
      1::bigint,
      1::bigint
    )
  $sql$,
  'standard lifecycle commit mutates the case exactly once and writes one event plus one transition'
);

select lives_ok(
  $sql$
    do $$
    declare
      case_id bigint;
    begin
      select id
      into case_id
      from public.rental_cases
      where case_reference_code = 'RC-951';

      perform *
      from private.commit_rental_case_lifecycle_transition(
        case_id,
        2,
        'proposal_pending_client',
        'dormant',
        'waiting_for_client',
        'phase8_db_test',
        'fixture:dormant',
        'operator',
        'operator:2',
        null,
        false,
        'lifecycle_transition_committed',
        '{"fixture":"dormant"}'::jsonb,
        'proposal_pending_client',
        'confirmation_pending',
        'waiting_for_client',
        '2026-08-25T09:00:00Z'::timestamptz
      );
    end
    $$;
  $sql$,
  'dormant lifecycle helper call succeeds'
);

select results_eq(
  $sql$
    select
      rc.lifecycle_state,
      rc.case_revision,
      rc.dormant_origin_state,
      rc.resume_target_state,
      rc.dormant_reason_code,
      rc.dormant_review_at
    from public.rental_cases rc
    where rc.case_reference_code = 'RC-951'
  $sql$,
  $sql$
    values (
      'dormant'::text,
      3::integer,
      'proposal_pending_client'::text,
      'confirmation_pending'::text,
      'waiting_for_client'::text,
      '2026-08-25 09:00:00+00'::timestamptz
    )
  $sql$,
  'dormant transitions persist dormant metadata on the case row'
);

select lives_ok(
  $sql$
    do $$
    declare
      case_id bigint;
    begin
      select id
      into case_id
      from public.rental_cases
      where case_reference_code = 'RC-952';

      perform *
      from private.commit_rental_case_lifecycle_transition(
        case_id,
        3,
        'dormant',
        'confirmation_pending',
        'resume_case',
        'phase8_db_test',
        'fixture:resume',
        'operator',
        'operator:3',
        null,
        false,
        'lifecycle_transition_committed',
        '{"fixture":"resume"}'::jsonb,
        null,
        null,
        null,
        null
      );
    end
    $$;
  $sql$,
  'resume lifecycle helper call succeeds'
);

select results_eq(
  $sql$
    select
      rc.lifecycle_state,
      rc.case_revision,
      rc.dormant_origin_state,
      rc.resume_target_state,
      rc.dormant_reason_code,
      rc.dormant_review_at is null
    from public.rental_cases rc
    where rc.case_reference_code = 'RC-952'
  $sql$,
  $sql$
    values (
      'confirmation_pending'::text,
      4::integer,
      null::text,
      null::text,
      null::text,
      true
    )
  $sql$,
  'non-dormant transitions clear dormant metadata after resume'
);

select throws_ok(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-953'
    )
    select *
    from private.commit_rental_case_lifecycle_transition(
      (select id from target_case),
      0,
      'confirmation_pending',
      'confirmed_pre_event',
      'confirm_booking',
      'phase8_db_test'
    );
  $sql$,
  'P0001',
  'stale_case_revision',
  'helper rejects stale case revision writes'
);

select throws_ok(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-953'
    )
    select *
    from private.commit_rental_case_lifecycle_transition(
      (select id from target_case),
      1,
      'proposal_pending_client',
      'confirmed_pre_event',
      'confirm_booking',
      'phase8_db_test'
    );
  $sql$,
  'P0001',
  'current_state_mismatch',
  'helper rejects mismatched expected current state'
);

select results_eq(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-953'
    )
    select
      previous_state,
      new_state,
      previous_revision,
      new_revision,
      manual_override,
      source_type
    from private.commit_rental_case_lifecycle_transition(
      (select id from target_case),
      1,
      'confirmation_pending',
      'closed_lost',
      'manual_close_out',
      'manual_override',
      'fixture:override',
      'operator',
      'operator:4',
      null,
      true,
      'lifecycle_manual_override_committed',
      '{"audit_note":"manually closed"}'::jsonb,
      null,
      null,
      null,
      null
    )
  $sql$,
  $sql$
    values (
      'confirmation_pending'::text,
      'closed_lost'::text,
      1::integer,
      2::integer,
      true,
      'manual_override'::text
    )
  $sql$,
  'manual override commits are recorded with override metadata'
);

select throws_ok(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-954'
    )
    select *
    from private.commit_rental_case_lifecycle_transition(
      (select id from target_case),
      0,
      'inquiry_active',
      'proposal_in_progress',
      'proposal_started',
      'phase8_db_test',
      'fixture:rollback',
      'operator',
      'operator:5',
      999999,
      false,
      'lifecycle_transition_committed',
      '{"fixture":"rollback"}'::jsonb,
      null,
      null,
      null,
      null
    );
  $sql$,
  '23503',
  null,
  'late lifecycle-history FK failures abort the helper transaction'
);

select results_eq(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-954'
    )
    select
      rc.lifecycle_state,
      rc.case_revision,
      (
        select count(*)
        from public.workflow_events we
        where we.rental_case_id = rc.id
      )::bigint as workflow_event_count,
      (
        select count(*)
        from public.rental_case_lifecycle_transitions lt
        where lt.rental_case_id = rc.id
      )::bigint as transition_count
    from public.rental_cases rc
    where rc.id = (select id from target_case)
  $sql$,
  $sql$
    values (
      'inquiry_active'::text,
      0::integer,
      0::bigint,
      0::bigint
    )
  $sql$,
  'helper rollback leaves case state and audit tables unchanged after failure'
);

select * from finish();
rollback;
