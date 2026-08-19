create unique index if not exists workflow_execution_attempts_succeeded_external_reference_unique_idx
  on public.workflow_execution_attempts (external_reference)
  where status = 'succeeded' and external_reference is not null;


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

  if p_external_reference is not null and p_attempt_status = 'succeeded' and exists (
    select 1
    from public.workflow_execution_attempts conflict
    where conflict.external_reference = p_external_reference
      and conflict.status = 'succeeded'
      and conflict.id <> p_execution_attempt_id
  ) then
    return query
    select p_rental_case_id, p_workflow_action_id, v_case.case_revision, v_action.status, v_action.status,
      '{}'::bigint[], p_execution_attempt_id, v_attempt.status, v_attempt.retry_eligible, p_external_reference,
      'external_reference_conflict'::text;
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
    '{"phase":"8.7A"}'::jsonb
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
