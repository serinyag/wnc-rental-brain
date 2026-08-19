begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

select plan(12);

select ok(
  exists (
    select 1
    from pg_proc proc
    join pg_namespace namespace
      on namespace.oid = proc.pronamespace
    where namespace.nspname = 'private'
      and proc.proname = 'commit_phase8_workflow_action_execution_start'
  ),
  'workflow-action execution start helper exists'
);

select ok(
  exists (
    select 1
    from pg_proc proc
    join pg_namespace namespace
      on namespace.oid = proc.pronamespace
    where namespace.nspname = 'private'
      and proc.proname = 'commit_phase8_workflow_action_execution_complete'
  ),
  'workflow-action execution completion helper exists'
);

select ok(
  exists (
    select 1
    from pg_proc proc
    join pg_namespace namespace
      on namespace.oid = proc.pronamespace
    where namespace.nspname = 'private'
      and proc.proname = 'commit_phase8_follow_up_status_update'
  ),
  'follow-up status update helper exists'
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
  (
    'RC-989',
    'proposal_in_progress',
    0,
    'studio_space',
    'studio_rental',
    'client:989',
    'contact:989',
    'unknown',
    'unknown',
    true
  ),
  (
    'RC-990',
    'proposal_in_progress',
    0,
    'studio_space',
    'studio_rental',
    'client:990',
    'contact:990',
    'unknown',
    'unknown',
    true
  ),
  (
    'RC-991',
    'proposal_in_progress',
    0,
    'studio_space',
    'studio_rental',
    'client:991',
    'contact:991',
    'unknown',
    'unknown',
    true
  ),
  (
    'RC-992',
    'proposal_in_progress',
    0,
    'studio_space',
    'studio_rental',
    'client:992',
    'contact:992',
    'unknown',
    'unknown',
    true
  );

with target_case as (
  select id
  from public.rental_cases
  where case_reference_code = 'RC-989'
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
  'internal',
  'review_item',
  'review_item:989',
  '{"task_kind":"follow_up_review","summary":"Review overdue follow-up.","reason":"The case needs structured human review."}'::jsonb,
  'automatic_allowed',
  'ready_to_execute',
  'subject:989',
  0,
  'idem:989',
  timezone('utc', now()),
  timezone('utc', now())
from target_case;

with target_case as (
  select id
  from public.rental_cases
  where case_reference_code = 'RC-990'
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
  'REQUEST_CLIENT_INFORMATION',
  'communication',
  'email',
  'open_question',
  'open_question:990',
  '{"open_question_ids":[990],"required_field_codes":["guest_count"],"intended_recipient_role":"client","purpose":"Collect missing event details.","reason":"Guest count is still unresolved."}'::jsonb,
  'human_only',
  'ready_to_execute',
  'subject:990',
  0,
  'idem:990',
  timezone('utc', now()),
  timezone('utc', now())
from target_case;

with target_case as (
  select id
  from public.rental_cases
  where case_reference_code = 'RC-992'
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
  'REQUEST_CLIENT_INFORMATION',
  'communication',
  'email',
  'open_question',
  'open_question:992',
  '{"open_question_ids":[992],"required_field_codes":["guest_count"],"intended_recipient_role":"client","purpose":"Collect missing event details.","reason":"Guest count is still unresolved."}'::jsonb,
  'automatic_allowed',
  'ready_to_execute',
  'subject:992',
  0,
  'idem:992',
  timezone('utc', now()),
  timezone('utc', now())
from target_case;

with target_case as (
  select id
  from public.rental_cases
  where case_reference_code = 'RC-991'
)
insert into public.rental_case_follow_ups (
  rental_case_id,
  reason_code,
  waiting_for_role,
  waiting_for_reference,
  due_at,
  urgency_level,
  cadence_policy_code,
  attempt_count,
  escalate_after,
  status,
  next_action_type,
  created_at,
  updated_at,
  completed_at
)
select
  id,
  'proposal_response',
  'client',
  'contact:991',
  '2026-08-12T10:00:00Z'::timestamptz,
  'medium',
  'weekly',
  0,
  2,
  'scheduled',
  'SCHEDULE_FOLLOW_UP_REVIEW',
  timezone('utc', now()),
  timezone('utc', now()),
  null
from target_case
union all
select
  id,
  'proposal_response',
  'client',
  'contact:991',
  '2026-08-05T10:00:00Z'::timestamptz,
  'medium',
  'weekly',
  1,
  2,
  'completed',
  'SCHEDULE_FOLLOW_UP_REVIEW',
  timezone('utc', now()),
  timezone('utc', now()),
  timezone('utc', now())
from target_case
union all
select
  id,
  'proposal_response',
  'client',
  'contact:991',
  '2026-08-01T10:00:00Z'::timestamptz,
  'medium',
  'weekly',
  1,
  2,
  'cancelled',
  'SCHEDULE_FOLLOW_UP_REVIEW',
  timezone('utc', now()),
  timezone('utc', now()),
  timezone('utc', now())
from target_case;

select results_eq(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-989'
    ),
    target_action as (
      select id
      from public.workflow_actions
      where rental_case_id = (select id from target_case)
    )
    select
      action_status_before,
      action_status_after,
      attempt_number,
      cardinality(audit_event_ids),
      failure_code is null
    from private.commit_phase8_workflow_action_execution_start(
      p_rental_case_id => (select id from target_case),
      p_workflow_action_id => (select id from target_action),
      p_actor_type => 'system',
      p_actor_reference => 'system:test',
      p_started_at => '2026-08-13T12:00:00Z'::timestamptz
    )
  $sql$,
  $sql$
    values (
      'ready_to_execute'::text,
      'executing'::text,
      1::integer,
      1::integer,
      true
    )
  $sql$,
  'execution start atomically creates a started attempt and moves the action to executing'
);

select results_eq(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-989'
    ),
    target_action as (
      select id
      from public.workflow_actions
      where rental_case_id = (select id from target_case)
    ),
    target_attempt as (
      select id
      from public.workflow_execution_attempts
      where workflow_action_id = (select id from target_action)
    )
    select
      action_status_before,
      action_status_after,
      attempt_status,
      retry_eligible,
      cardinality(audit_event_ids),
      failure_code is null
    from private.commit_phase8_workflow_action_execution_complete(
      p_rental_case_id => (select id from target_case),
      p_workflow_action_id => (select id from target_action),
      p_execution_attempt_id => (select id from target_attempt),
      p_attempt_status => 'succeeded',
      p_response_snapshot => '{"provider_mode":"deterministic_fake","result":"success"}'::jsonb,
      p_retry_eligible => false,
      p_external_reference => 'fake:internal:989:1',
      p_failure_code => null,
      p_actor_type => 'system',
      p_actor_reference => 'system:test',
      p_completed_at => '2026-08-13T12:01:00Z'::timestamptz
    )
  $sql$,
  $sql$
    values (
      'executing'::text,
      'succeeded'::text,
      'succeeded'::text,
      false,
      1::integer,
      true
    )
  $sql$,
  'execution completion atomically finalizes the attempt and marks the action succeeded'
);

select results_eq(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-989'
    )
    select
      action.status,
      attempt.status,
      attempt.external_reference,
      attempt.completed_at is not null,
      (
        select count(*)
        from public.rental_case_lifecycle_transitions transition_history
        where transition_history.rental_case_id = action.rental_case_id
      )::bigint
    from public.workflow_actions action
    join public.workflow_execution_attempts attempt
      on attempt.workflow_action_id = action.id
    where action.rental_case_id = (select id from target_case)
  $sql$,
  $sql$
    values (
      'succeeded'::text,
      'succeeded'::text,
      'fake:internal:989:1'::text,
      true,
      0::bigint
    )
  $sql$,
  'execution helpers mutate only execution records and do not create lifecycle transitions'
);

select results_eq(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-992'
    ),
    target_action as (
      select id
      from public.workflow_actions
      where rental_case_id = (select id from target_case)
    ),
    started as (
      select *
      from private.commit_phase8_workflow_action_execution_start(
        p_rental_case_id => (select id from target_case),
        p_workflow_action_id => (select id from target_action),
        p_actor_type => 'system',
        p_actor_reference => 'system:test',
        p_started_at => '2026-08-13T12:10:00Z'::timestamptz
      )
    )
    select
      completed.action_status_after,
      completed.attempt_status,
      completed.retry_eligible,
      (
        select status
        from public.workflow_actions
        where id = (select id from target_action)
      )
    from private.commit_phase8_workflow_action_execution_complete(
      p_rental_case_id => (select id from target_case),
      p_workflow_action_id => (select id from target_action),
      p_execution_attempt_id => (select execution_attempt_id from started),
      p_attempt_status => 'failed',
      p_response_snapshot => '{"provider_mode":"deterministic_fake","result":"retryable_failure"}'::jsonb,
      p_retry_eligible => true,
      p_external_reference => null,
      p_failure_code => 'fake_retryable_failure',
      p_actor_type => 'system',
      p_actor_reference => 'system:test',
      p_completed_at => '2026-08-13T12:11:00Z'::timestamptz
    ) completed
  $sql$,
  $sql$
    values (
      'ready_to_execute'::text,
      'failed'::text,
      true,
      'ready_to_execute'::text
    )
  $sql$,
  'retry-eligible failures preserve the same action and return it to ready_to_execute'
);

select results_eq(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-990'
    ),
    target_action as (
      select id
      from public.workflow_actions
      where rental_case_id = (select id from target_case)
    )
    select
      failure_code,
      (
        select count(*)
        from public.workflow_execution_attempts attempt
        where attempt.workflow_action_id = (select id from target_action)
      )::bigint
    from private.commit_phase8_workflow_action_execution_start(
      p_rental_case_id => (select id from target_case),
      p_workflow_action_id => (select id from target_action),
      p_actor_type => 'system',
      p_actor_reference => 'system:test',
      p_started_at => '2026-08-13T12:20:00Z'::timestamptz
    )
  $sql$,
  $sql$
    values (
      'action_human_only'::text,
      0::bigint
    )
  $sql$,
  'human-only actions are rejected before any execution attempt is created'
);

select results_eq(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-991'
    ),
    target_follow_up as (
      select id
      from public.rental_case_follow_ups
      where rental_case_id = (select id from target_case)
        and status = 'scheduled'
      order by id
      limit 1
    )
    select
      status_before,
      status_after,
      attempt_count_before,
      attempt_count_after,
      cardinality(audit_event_ids),
      failure_code is null
    from private.commit_phase8_follow_up_status_update(
      p_rental_case_id => (select id from target_case),
      p_follow_up_id => (select id from target_follow_up),
      p_target_status => 'due',
      p_actor_type => 'system',
      p_actor_reference => 'system:test',
      p_expected_current_status => 'scheduled',
      p_attempt_count_delta => 0,
      p_occurred_at => '2026-08-13T12:30:00Z'::timestamptz,
      p_completed_at => null
    )
  $sql$,
  $sql$
    values (
      'scheduled'::text,
      'due'::text,
      0::integer,
      0::integer,
      1::integer,
      true
    )
  $sql$,
  'follow-up status update marks due work atomically and emits audit coverage'
);

select results_eq(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-991'
    ),
    completed_follow_up as (
      select id
      from public.rental_case_follow_ups
      where rental_case_id = (select id from target_case)
        and status = 'completed'
      order by id
      limit 1
    )
    select
      failure_code,
      status_before,
      status_after
    from private.commit_phase8_follow_up_status_update(
      p_rental_case_id => (select id from target_case),
      p_follow_up_id => (select id from completed_follow_up),
      p_target_status => 'due',
      p_actor_type => 'system',
      p_actor_reference => 'system:test',
      p_expected_current_status => 'completed',
      p_attempt_count_delta => 0,
      p_occurred_at => '2026-08-13T12:31:00Z'::timestamptz,
      p_completed_at => null
    )
  $sql$,
  $sql$
    values (
      'follow_up_state_transition_invalid'::text,
      'completed'::text,
      'completed'::text
    )
  $sql$,
  'completed follow-ups cannot be reactivated into due work'
);

select results_eq(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-991'
    )
    select array_agg(status order by id)
    from public.rental_case_follow_ups
    where rental_case_id = (select id from target_case)
      and status not in ('completed', 'cancelled')
  $sql$,
  $sql$
    values (array['due']::text[])
  $sql$,
  'due-work querying excludes completed and cancelled follow-ups'
);

select results_eq(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-989'
    ),
    target_action as (
      select id
      from public.workflow_actions
      where rental_case_id = (select id from target_case)
    ),
    target_attempt as (
      select id
      from public.workflow_execution_attempts
      where workflow_action_id = (select id from target_action)
    )
    select failure_code
    from private.commit_phase8_workflow_action_execution_complete(
      p_rental_case_id => (select id from target_case),
      p_workflow_action_id => (select id from target_action),
      p_execution_attempt_id => (select id from target_attempt),
      p_attempt_status => 'failed',
      p_response_snapshot => '{"provider_mode":"deterministic_fake","result":"duplicate_completion"}'::jsonb,
      p_retry_eligible => false,
      p_external_reference => null,
      p_failure_code => 'duplicate_completion',
      p_actor_type => 'system',
      p_actor_reference => 'system:test',
      p_completed_at => '2026-08-13T12:40:00Z'::timestamptz
    )
  $sql$,
  $sql$
    values ('execution_complete_failed'::text)
  $sql$,
  'terminal execution attempts cannot be completed a second time'
);

select * from finish();
rollback;
