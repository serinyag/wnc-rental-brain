create or replace function private.workflow_execution_attempt_update_guard()
returns trigger
language plpgsql
as $$
begin
  if old.id <> new.id
     or old.workflow_execution_attempt_uuid <> new.workflow_execution_attempt_uuid
     or old.workflow_action_id <> new.workflow_action_id
     or old.rental_case_id <> new.rental_case_id
     or old.attempt_number <> new.attempt_number
     or old.adapter_code <> new.adapter_code
     or old.started_at <> new.started_at
     or old.created_at <> new.created_at then
    raise exception 'workflow_execution_attempts immutable columns cannot change during completion'
      using errcode = '23514';
  end if;

  if old.status <> 'started' then
    raise exception 'workflow_execution_attempts can only transition from started once'
      using errcode = '23514';
  end if;

  if new.status not in ('succeeded', 'failed', 'timeout', 'cancelled') then
    raise exception 'workflow_execution_attempts completion requires a terminal status'
      using errcode = '23514';
  end if;

  if new.completed_at is null then
    raise exception 'workflow_execution_attempts completion requires completed_at'
      using errcode = '23514';
  end if;

  return new;
end;
$$;

drop trigger if exists trg_workflow_execution_attempts_append_only_update on public.workflow_execution_attempts;
create trigger trg_workflow_execution_attempts_append_only_update
before update on public.workflow_execution_attempts
for each row
execute function private.workflow_execution_attempt_update_guard();


create or replace function private.commit_phase8_workflow_action_execution_start(
  p_rental_case_id bigint,
  p_workflow_action_id bigint,
  p_actor_type text default null,
  p_actor_reference text default null,
  p_started_at timestamptz default null
)
returns table (
  rental_case_id bigint,
  workflow_action_id bigint,
  case_revision integer,
  action_status_before text,
  action_status_after text,
  audit_event_ids bigint[],
  execution_attempt_id bigint,
  attempt_number integer,
  failure_code text
)
language plpgsql
as $$
#variable_conflict use_column
declare
  v_case public.rental_cases%rowtype;
  v_action public.workflow_actions%rowtype;
  v_started_at timestamptz := coalesce(p_started_at, timezone('utc', now()));
  v_execution_attempt_id bigint;
  v_attempt_number integer;
  v_event_id bigint;
begin
  select *
  into v_case
  from public.rental_cases
  where id = p_rental_case_id
  for update;

  if not found then
    return query
    select
      p_rental_case_id,
      p_workflow_action_id,
      0::integer,
      'proposed'::text,
      'proposed'::text,
      '{}'::bigint[],
      null::bigint,
      null::integer,
      'case_not_found'::text;
    return;
  end if;

  select *
  into v_action
  from public.workflow_actions
  where id = p_workflow_action_id
    and rental_case_id = p_rental_case_id
  for update;

  if not found then
    return query
    select
      p_rental_case_id,
      p_workflow_action_id,
      v_case.case_revision,
      'proposed'::text,
      'proposed'::text,
      '{}'::bigint[],
      null::bigint,
      null::integer,
      'action_not_found'::text;
    return;
  end if;

  if v_action.approval_posture = 'human_only' then
    return query
    select p_rental_case_id, p_workflow_action_id, v_case.case_revision, v_action.status, v_action.status,
      '{}'::bigint[], null::bigint, null::integer, 'action_human_only'::text;
    return;
  end if;

  if v_action.approval_posture = 'blocked' then
    return query
    select p_rental_case_id, p_workflow_action_id, v_case.case_revision, v_action.status, v_action.status,
      '{}'::bigint[], null::bigint, null::integer, 'action_blocked'::text;
    return;
  end if;

  if v_action.status = 'executing' then
    return query
    select p_rental_case_id, p_workflow_action_id, v_case.case_revision, v_action.status, v_action.status,
      '{}'::bigint[], null::bigint, null::integer, 'execution_already_started'::text;
    return;
  end if;

  if v_action.status = 'succeeded' then
    return query
    select p_rental_case_id, p_workflow_action_id, v_case.case_revision, v_action.status, v_action.status,
      '{}'::bigint[], null::bigint, null::integer, 'action_already_succeeded'::text;
    return;
  end if;

  if v_action.status = 'cancelled' then
    return query
    select p_rental_case_id, p_workflow_action_id, v_case.case_revision, v_action.status, v_action.status,
      '{}'::bigint[], null::bigint, null::integer, 'action_cancelled'::text;
    return;
  end if;

  if v_action.status = 'superseded' then
    return query
    select p_rental_case_id, p_workflow_action_id, v_case.case_revision, v_action.status, v_action.status,
      '{}'::bigint[], null::bigint, null::integer, 'action_superseded'::text;
    return;
  end if;

  if v_action.source_case_revision <> v_case.case_revision then
    return query
    select p_rental_case_id, p_workflow_action_id, v_case.case_revision, v_action.status, v_action.status,
      '{}'::bigint[], null::bigint, null::integer, 'action_stale_revision'::text;
    return;
  end if;

  if v_action.due_at is not null and v_action.due_at > v_started_at then
    return query
    select p_rental_case_id, p_workflow_action_id, v_case.case_revision, v_action.status, v_action.status,
      '{}'::bigint[], null::bigint, null::integer, 'action_not_due'::text;
    return;
  end if;

  if v_action.status <> 'ready_to_execute' then
    return query
    select p_rental_case_id, p_workflow_action_id, v_case.case_revision, v_action.status, v_action.status,
      '{}'::bigint[], null::bigint, null::integer, 'action_not_execution_ready'::text;
    return;
  end if;

  select coalesce(max(attempt_number), 0) + 1
  into v_attempt_number
  from public.workflow_execution_attempts
  where workflow_action_id = p_workflow_action_id;

  insert into public.workflow_execution_attempts (
    workflow_action_id,
    rental_case_id,
    attempt_number,
    adapter_code,
    started_at,
    status,
    retry_eligible,
    response_snapshot
  )
  values (
    p_workflow_action_id,
    p_rental_case_id,
    v_attempt_number,
    v_action.target_adapter_code,
    v_started_at,
    'started',
    false,
    '{}'::jsonb
  )
  returning id into v_execution_attempt_id;

  update public.workflow_actions
  set status = 'executing',
      updated_at = v_started_at
  where id = p_workflow_action_id
    and rental_case_id = p_rental_case_id;

  insert into public.workflow_events (
    rental_case_id,
    event_type_code,
    source_type,
    source_reference,
    actor_type,
    actor_reference,
    occurred_at,
    recorded_at,
    structured_payload,
    event_identity_key,
    origin_metadata
  )
  values (
    p_rental_case_id,
    'workflow_action_execution_started',
    'execution_runtime',
    concat('workflow_action:', p_workflow_action_id),
    p_actor_type,
    p_actor_reference,
    v_started_at,
    v_started_at,
    jsonb_build_object(
      'workflow_action_id', p_workflow_action_id,
      'execution_attempt_id', v_execution_attempt_id,
      'attempt_number', v_attempt_number,
      'adapter_code', v_action.target_adapter_code,
      'action_status_before', v_action.status,
      'action_status_after', 'executing'
    ),
    concat('action_execution_started:', p_workflow_action_id, ':', v_attempt_number),
    '{"phase":"8.6"}'::jsonb
  )
  returning id into v_event_id;

  return query
  select
    p_rental_case_id,
    p_workflow_action_id,
    v_case.case_revision,
    v_action.status,
    'executing'::text,
    array[v_event_id]::bigint[],
    v_execution_attempt_id,
    v_attempt_number,
    null::text;
end;
$$;


create or replace function private.commit_phase8_workflow_action_execution_complete(
  p_rental_case_id bigint,
  p_workflow_action_id bigint,
  p_execution_attempt_id bigint,
  p_attempt_status text,
  p_response_snapshot jsonb,
  p_retry_eligible boolean,
  p_external_reference text default null,
  p_failure_code text default null,
  p_actor_type text default null,
  p_actor_reference text default null,
  p_completed_at timestamptz default null
)
returns table (
  rental_case_id bigint,
  workflow_action_id bigint,
  case_revision integer,
  action_status_before text,
  action_status_after text,
  audit_event_ids bigint[],
  execution_attempt_id bigint,
  attempt_status text,
  retry_eligible boolean,
  external_reference text,
  failure_code text
)
language plpgsql
as $$
#variable_conflict use_column
declare
  v_case public.rental_cases%rowtype;
  v_action public.workflow_actions%rowtype;
  v_attempt public.workflow_execution_attempts%rowtype;
  v_completed_at timestamptz := coalesce(p_completed_at, timezone('utc', now()));
  v_action_status_after text;
  v_event_id bigint;
begin
  if p_attempt_status not in ('succeeded', 'failed', 'timeout', 'cancelled') then
    return query
    select p_rental_case_id, p_workflow_action_id, 0::integer, 'proposed'::text, 'proposed'::text,
      '{}'::bigint[], p_execution_attempt_id, p_attempt_status, coalesce(p_retry_eligible, false), p_external_reference,
      'invalid_execution_input'::text;
    return;
  end if;

  if jsonb_typeof(coalesce(p_response_snapshot, '{}'::jsonb)) not in ('object', 'array') then
    return query
    select p_rental_case_id, p_workflow_action_id, 0::integer, 'proposed'::text, 'proposed'::text,
      '{}'::bigint[], p_execution_attempt_id, p_attempt_status, coalesce(p_retry_eligible, false), p_external_reference,
      'invalid_execution_input'::text;
    return;
  end if;

  select *
  into v_case
  from public.rental_cases
  where id = p_rental_case_id
  for update;

  if not found then
    return query
    select p_rental_case_id, p_workflow_action_id, 0::integer, 'proposed'::text, 'proposed'::text,
      '{}'::bigint[], p_execution_attempt_id, p_attempt_status, coalesce(p_retry_eligible, false), p_external_reference,
      'case_not_found'::text;
    return;
  end if;

  select *
  into v_action
  from public.workflow_actions
  where id = p_workflow_action_id
    and rental_case_id = p_rental_case_id
  for update;

  if not found then
    return query
    select p_rental_case_id, p_workflow_action_id, v_case.case_revision, 'proposed'::text, 'proposed'::text,
      '{}'::bigint[], p_execution_attempt_id, p_attempt_status, coalesce(p_retry_eligible, false), p_external_reference,
      'action_not_found'::text;
    return;
  end if;

  select *
  into v_attempt
  from public.workflow_execution_attempts
  where id = p_execution_attempt_id
    and workflow_action_id = p_workflow_action_id
    and rental_case_id = p_rental_case_id
  for update;

  if not found then
    return query
    select p_rental_case_id, p_workflow_action_id, v_case.case_revision, v_action.status, v_action.status,
      '{}'::bigint[], p_execution_attempt_id, p_attempt_status, coalesce(p_retry_eligible, false), p_external_reference,
      'attempt_not_found'::text;
    return;
  end if;

  if v_attempt.status <> 'started' or v_action.status <> 'executing' then
    return query
    select p_rental_case_id, p_workflow_action_id, v_case.case_revision, v_action.status, v_action.status,
      '{}'::bigint[], p_execution_attempt_id, v_attempt.status, v_attempt.retry_eligible, v_attempt.external_reference,
      'execution_complete_failed'::text;
    return;
  end if;

  v_action_status_after := case
    when p_attempt_status = 'succeeded' then 'succeeded'
    when coalesce(p_retry_eligible, false) then 'ready_to_execute'
    else 'failed'
  end;

  update public.workflow_execution_attempts
  set status = p_attempt_status,
      retry_eligible = coalesce(p_retry_eligible, false),
      response_snapshot = coalesce(p_response_snapshot, '{}'::jsonb),
      completed_at = v_completed_at,
      external_reference = p_external_reference,
      failure_code = p_failure_code
  where id = p_execution_attempt_id;

  update public.workflow_actions
  set status = v_action_status_after,
      updated_at = v_completed_at
  where id = p_workflow_action_id
    and rental_case_id = p_rental_case_id;

  insert into public.workflow_events (
    rental_case_id,
    event_type_code,
    source_type,
    source_reference,
    actor_type,
    actor_reference,
    occurred_at,
    recorded_at,
    structured_payload,
    event_identity_key,
    origin_metadata
  )
  values (
    p_rental_case_id,
    'workflow_action_execution_completed',
    'execution_runtime',
    concat('workflow_action:', p_workflow_action_id),
    p_actor_type,
    p_actor_reference,
    v_completed_at,
    v_completed_at,
    jsonb_build_object(
      'workflow_action_id', p_workflow_action_id,
      'execution_attempt_id', p_execution_attempt_id,
      'attempt_status', p_attempt_status,
      'retry_eligible', coalesce(p_retry_eligible, false),
      'external_reference', p_external_reference,
      'failure_code', p_failure_code,
      'action_status_before', v_action.status,
      'action_status_after', v_action_status_after
    ),
    concat('action_execution_completed:', p_workflow_action_id, ':', p_execution_attempt_id),
    '{"phase":"8.6"}'::jsonb
  )
  returning id into v_event_id;

  return query
  select
    p_rental_case_id,
    p_workflow_action_id,
    v_case.case_revision,
    v_action.status,
    v_action_status_after,
    array[v_event_id]::bigint[],
    p_execution_attempt_id,
    p_attempt_status,
    coalesce(p_retry_eligible, false),
    p_external_reference,
    null::text;
end;
$$;


create or replace function private.commit_phase8_follow_up_status_update(
  p_rental_case_id bigint,
  p_follow_up_id bigint,
  p_target_status text,
  p_actor_type text default null,
  p_actor_reference text default null,
  p_expected_current_status text default null,
  p_attempt_count_delta integer default 0,
  p_occurred_at timestamptz default null,
  p_completed_at timestamptz default null
)
returns table (
  rental_case_id bigint,
  follow_up_id bigint,
  status_before text,
  status_after text,
  attempt_count_before integer,
  attempt_count_after integer,
  audit_event_ids bigint[],
  failure_code text
)
language plpgsql
as $$
#variable_conflict use_column
declare
  v_case public.rental_cases%rowtype;
  v_follow_up public.rental_case_follow_ups%rowtype;
  v_occurred_at timestamptz := coalesce(p_occurred_at, timezone('utc', now()));
  v_event_id bigint;
begin
  if p_target_status not in ('scheduled', 'due', 'overdue', 'escalated', 'completed', 'cancelled') then
    return query
    select p_rental_case_id, p_follow_up_id, 'completed'::text, 'completed'::text, 0::integer, 0::integer,
      '{}'::bigint[], 'invalid_execution_input'::text;
    return;
  end if;

  if p_attempt_count_delta < 0 then
    return query
    select p_rental_case_id, p_follow_up_id, 'completed'::text, 'completed'::text, 0::integer, 0::integer,
      '{}'::bigint[], 'invalid_execution_input'::text;
    return;
  end if;

  select *
  into v_case
  from public.rental_cases
  where id = p_rental_case_id
  for update;

  if not found then
    return query
    select p_rental_case_id, p_follow_up_id, 'completed'::text, 'completed'::text, 0::integer, 0::integer,
      '{}'::bigint[], 'case_not_found'::text;
    return;
  end if;

  select *
  into v_follow_up
  from public.rental_case_follow_ups
  where id = p_follow_up_id
    and rental_case_id = p_rental_case_id
  for update;

  if not found then
    return query
    select p_rental_case_id, p_follow_up_id, 'completed'::text, 'completed'::text, 0::integer, 0::integer,
      '{}'::bigint[], 'follow_up_not_found'::text;
    return;
  end if;

  if p_expected_current_status is not null and v_follow_up.status <> p_expected_current_status then
    return query
    select p_rental_case_id, p_follow_up_id, v_follow_up.status, v_follow_up.status, v_follow_up.attempt_count,
      v_follow_up.attempt_count, '{}'::bigint[], 'follow_up_state_transition_invalid'::text;
    return;
  end if;

  if v_follow_up.status in ('completed', 'cancelled') and p_target_status <> v_follow_up.status then
    return query
    select p_rental_case_id, p_follow_up_id, v_follow_up.status, v_follow_up.status, v_follow_up.attempt_count,
      v_follow_up.attempt_count, '{}'::bigint[], 'follow_up_state_transition_invalid'::text;
    return;
  end if;

  update public.rental_case_follow_ups
  set status = p_target_status,
      attempt_count = attempt_count + p_attempt_count_delta,
      completed_at = case
        when p_target_status in ('completed', 'cancelled') then coalesce(p_completed_at, v_occurred_at)
        else completed_at
      end,
      updated_at = v_occurred_at
  where id = p_follow_up_id
    and rental_case_id = p_rental_case_id;

  insert into public.workflow_events (
    rental_case_id,
    event_type_code,
    source_type,
    source_reference,
    actor_type,
    actor_reference,
    occurred_at,
    recorded_at,
    structured_payload,
    event_identity_key,
    origin_metadata
  )
  values (
    p_rental_case_id,
    'follow_up_status_updated',
    'execution_runtime',
    concat('follow_up:', p_follow_up_id),
    p_actor_type,
    p_actor_reference,
    v_occurred_at,
    v_occurred_at,
    jsonb_build_object(
      'follow_up_id', p_follow_up_id,
      'status_before', v_follow_up.status,
      'status_after', p_target_status,
      'attempt_count_before', v_follow_up.attempt_count,
      'attempt_count_after', v_follow_up.attempt_count + p_attempt_count_delta
    ),
    concat(
      'follow_up_status_updated:',
      p_follow_up_id,
      ':',
      v_follow_up.status,
      ':',
      p_target_status,
      ':',
      v_follow_up.attempt_count + p_attempt_count_delta
    ),
    '{"phase":"8.6"}'::jsonb
  )
  returning id into v_event_id;

  return query
  select
    p_rental_case_id,
    p_follow_up_id,
    v_follow_up.status,
    p_target_status,
    v_follow_up.attempt_count,
    v_follow_up.attempt_count + p_attempt_count_delta,
    array[v_event_id]::bigint[],
    null::text;
end;
$$;
