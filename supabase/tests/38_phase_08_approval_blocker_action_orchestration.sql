begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

select plan(8);

select ok(
  exists (
    select 1
    from pg_indexes
    where schemaname = 'public'
      and tablename = 'rental_case_blockers'
      and indexname = 'rental_case_blockers_open_semantic_resolution_unique'
  ),
  'open semantic blocker identity index exists'
);

select ok(
  exists (
    select 1
    from pg_indexes
    where schemaname = 'public'
      and tablename = 'rental_case_approval_requests'
      and indexname = 'rental_case_approval_requests_open_semantic_reference_unique'
  ),
  'open semantic approval identity index exists'
);

insert into public.rental_cases (
  case_reference_code,
  lifecycle_state,
  case_revision,
  rental_type_code,
  commercial_summary_status,
  operational_summary_status,
  is_active
)
values
  ('RC-980', 'proposal_in_progress', 0, 'studio_space', 'unknown', 'unknown', true);

select lives_ok(
  $sql$
    insert into public.rental_case_blockers (
      rental_case_id,
      blocker_type,
      blocked_subject_type,
      blocked_subject_reference,
      origin_entity_type,
      origin_entity_reference,
      severity,
      status,
      resolution_condition_text,
      resolution_reference,
      opened_at
    )
    select
      id,
      'missing_client_information',
      'transition',
      'open_question:1',
      'open_question',
      'open_question:1',
      'high',
      'open',
      'Question must be resolved',
      'semantic:blocker:question:1',
      timezone('utc', now())
    from public.rental_cases
    where case_reference_code = 'RC-980';
  $sql$,
  'semantic open blocker may be inserted'
);

select throws_ok(
  $sql$
    insert into public.rental_case_blockers (
      rental_case_id,
      blocker_type,
      blocked_subject_type,
      blocked_subject_reference,
      origin_entity_type,
      origin_entity_reference,
      severity,
      status,
      resolution_condition_text,
      resolution_reference,
      opened_at
    )
    select
      id,
      'missing_client_information',
      'transition',
      'open_question:1',
      'open_question',
      'open_question:1',
      'high',
      'open',
      'Question must be resolved',
      'semantic:blocker:question:1',
      timezone('utc', now())
    from public.rental_cases
    where case_reference_code = 'RC-980';
  $sql$,
  '23505',
  null,
  'duplicate open semantic blocker is rejected'
);

select lives_ok(
  $sql$
    insert into public.rental_case_blockers (
      rental_case_id,
      blocker_type,
      blocked_subject_type,
      blocked_subject_reference,
      origin_entity_type,
      origin_entity_reference,
      severity,
      status,
      resolution_condition_text,
      resolution_reference,
      opened_at,
      resolved_at
    )
    select
      id,
      'missing_client_information',
      'transition',
      'open_question:1',
      'open_question',
      'open_question:1',
      'high',
      'resolved',
      'Question must be resolved',
      'semantic:blocker:question:1',
      timezone('utc', now()),
      timezone('utc', now())
    from public.rental_cases
    where case_reference_code = 'RC-980';
  $sql$,
  'resolved semantic blocker may coexist with prior open-history row'
);

select lives_ok(
  $sql$
    insert into public.rental_case_approval_requests (
      rental_case_id,
      target_entity_type,
      target_entity_reference,
      approval_type,
      reason_text,
      required_approver_reference,
      status,
      created_at
    )
    select
      id,
      'case_decision',
      'case_decision:1',
      'commercial_exception',
      'Approval required',
      'semantic:approval:case_decision:1',
      'open',
      timezone('utc', now())
    from public.rental_cases
    where case_reference_code = 'RC-980';
  $sql$,
  'semantic open approval may be inserted'
);

select throws_ok(
  $sql$
    insert into public.rental_case_approval_requests (
      rental_case_id,
      target_entity_type,
      target_entity_reference,
      approval_type,
      reason_text,
      required_approver_reference,
      status,
      created_at
    )
    select
      id,
      'case_decision',
      'case_decision:1',
      'commercial_exception',
      'Approval required',
      'semantic:approval:case_decision:1',
      'open',
      timezone('utc', now())
    from public.rental_cases
    where case_reference_code = 'RC-980';
  $sql$,
  '23505',
  null,
  'duplicate open semantic approval is rejected'
);

select lives_ok(
  $sql$
    insert into public.rental_case_approval_requests (
      rental_case_id,
      target_entity_type,
      target_entity_reference,
      approval_type,
      reason_text,
      required_approver_reference,
      status,
      created_at,
      decided_at
    )
    select
      id,
      'case_decision',
      'case_decision:1',
      'commercial_exception',
      'Approval required',
      'semantic:approval:case_decision:1',
      'rejected',
      timezone('utc', now()),
      timezone('utc', now())
    from public.rental_cases
    where case_reference_code = 'RC-980';
  $sql$,
  'rejected semantic approval may coexist with prior open-history row'
);

select * from finish();

rollback;
