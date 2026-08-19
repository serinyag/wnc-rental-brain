begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

select plan(5);

select ok(
  exists (
    select 1
    from pg_indexes
    where schemaname = 'public'
      and indexname like 'workflow_execution_attempts_succeeded_external_reference_unique%'
  ),
  'successful external references are protected by a unique index'
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
values
  ('RC-1501', 'proposal_in_progress', 0, 'studio_space', 'studio_rental', 'client:1501', 'contact:1501', 'unknown', 'unknown', true),
  ('RC-1502', 'proposal_in_progress', 0, 'studio_space', 'studio_rental', 'client:1502', 'contact:1502', 'unknown', 'unknown', true);

with cases as (
  select id, case_reference_code
  from public.rental_cases
  where case_reference_code in ('RC-1501', 'RC-1502')
)
insert into public.workflow_actions (
  rental_case_id,
  action_type,
  action_category,
  target_adapter_code,
  reason_entity_type,
  reason_entity_reference,
  structured_payload,
  approval_posture,
  status,
  semantic_subject_hash,
  source_case_revision,
  idempotency_key,
  created_at,
  updated_at
)
select
  id,
  'CREATE_INTERNAL_TASK_ITEM',
  'coordination',
  'asana',
  'review_item',
  concat('review_item:', case_reference_code),
  '{"task_kind":"follow_up_review","summary":"Review overdue follow-up.","reason":"The case needs structured human review."}'::jsonb,
  'automatic_allowed',
  'ready_to_execute',
  concat('subject:', case_reference_code),
  0,
  concat('idem:', case_reference_code),
  timezone('utc', now()),
  timezone('utc', now())
from cases;

with first_start as (
  select *
  from private.commit_phase8_workflow_action_execution_start(
    p_rental_case_id => (select id from public.rental_cases where case_reference_code = 'RC-1501'),
    p_workflow_action_id => (select id from public.workflow_actions where idempotency_key = 'idem:RC-1501'),
    p_actor_type => 'system',
    p_actor_reference => 'system:test',
    p_started_at => '2026-08-13T12:00:00Z'::timestamptz
  )
),
first_complete as (
  select *
  from private.commit_phase8_workflow_action_execution_complete(
    p_rental_case_id => (select id from public.rental_cases where case_reference_code = 'RC-1501'),
    p_workflow_action_id => (select id from public.workflow_actions where idempotency_key = 'idem:RC-1501'),
    p_execution_attempt_id => (select execution_attempt_id from first_start),
    p_attempt_status => 'succeeded',
    p_response_snapshot => '{"provider":"asana","task_gid":"task-shared"}'::jsonb,
    p_retry_eligible => false,
    p_external_reference => 'asana:task:task-shared',
    p_failure_code => null,
    p_actor_type => 'system',
    p_actor_reference => 'system:test',
    p_completed_at => '2026-08-13T12:01:00Z'::timestamptz
  )
)
select is(
  (select attempt_status from first_complete),
  'succeeded',
  'first completion with an external task reference succeeds'
);

with second_start as (
  select *
  from private.commit_phase8_workflow_action_execution_start(
    p_rental_case_id => (select id from public.rental_cases where case_reference_code = 'RC-1502'),
    p_workflow_action_id => (select id from public.workflow_actions where idempotency_key = 'idem:RC-1502'),
    p_actor_type => 'system',
    p_actor_reference => 'system:test',
    p_started_at => '2026-08-13T12:02:00Z'::timestamptz
  )
),
second_complete as (
  select *
  from private.commit_phase8_workflow_action_execution_complete(
    p_rental_case_id => (select id from public.rental_cases where case_reference_code = 'RC-1502'),
    p_workflow_action_id => (select id from public.workflow_actions where idempotency_key = 'idem:RC-1502'),
    p_execution_attempt_id => (select execution_attempt_id from second_start),
    p_attempt_status => 'succeeded',
    p_response_snapshot => '{"provider":"asana","task_gid":"task-shared"}'::jsonb,
    p_retry_eligible => false,
    p_external_reference => 'asana:task:task-shared',
    p_failure_code => null,
    p_actor_type => 'system',
    p_actor_reference => 'system:test',
    p_completed_at => '2026-08-13T12:03:00Z'::timestamptz
  )
)
select is(
  (select failure_code from second_complete),
  'external_reference_conflict',
  'duplicate successful external references are rejected deterministically'
);

select is(
  (
    select status
    from public.workflow_execution_attempts
    where workflow_action_id = (select id from public.workflow_actions where idempotency_key = 'idem:RC-1502')
    order by id desc
    limit 1
  ),
  'started',
  'conflicted completion leaves the second execution attempt unclaimed as success'
);

select is(
  (
    select status
    from public.workflow_actions
    where idempotency_key = 'idem:RC-1502'
  ),
  'executing',
  'conflicted completion does not mutate the second workflow action to success'
);

select * from finish();
rollback;
