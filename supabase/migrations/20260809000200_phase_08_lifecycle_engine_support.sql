create or replace function private.commit_rental_case_lifecycle_transition(
  p_rental_case_id bigint,
  p_expected_case_revision integer,
  p_expected_current_state text,
  p_target_state text,
  p_transition_reason_code text,
  p_source_type text,
  p_source_reference text default null,
  p_actor_type text default null,
  p_actor_reference text default null,
  p_triggering_event_id bigint default null,
  p_override_applied boolean default false,
  p_transition_event_type_code text default 'lifecycle_transition_committed',
  p_transition_event_payload jsonb default '{}'::jsonb,
  p_dormant_origin_state text default null,
  p_resume_target_state text default null,
  p_dormant_reason_code text default null,
  p_dormant_review_at timestamptz default null
)
returns table (
  rental_case_id bigint,
  previous_state text,
  new_state text,
  previous_revision integer,
  new_revision integer,
  lifecycle_transition_history_id bigint,
  workflow_event_id bigint,
  reason_code text,
  actor_reference text,
  actor_type text,
  source_type text,
  source_reference text,
  triggering_event_id bigint,
  manual_override boolean,
  occurred_at timestamptz
)
language plpgsql
as $$
declare
  v_case public.rental_cases%rowtype;
  v_occurred_at timestamptz := timezone('utc', now());
  v_workflow_event_id bigint;
  v_lifecycle_transition_id bigint;
  v_event_payload jsonb;
begin
  if p_target_state not in (
    'inquiry_active',
    'proposal_in_progress',
    'proposal_pending_client',
    'confirmation_pending',
    'confirmed_pre_event',
    'event_ready',
    'event_in_progress',
    'close_out_in_progress',
    'dormant',
    'closed',
    'closed_lost',
    'cancelled'
  ) then
    raise exception 'invalid_target_state' using errcode = 'P0001';
  end if;

  select *
  into v_case
  from public.rental_cases
  where id = p_rental_case_id
  for update;

  if not found then
    raise exception 'case_not_found' using errcode = 'P0001';
  end if;

  if v_case.case_revision <> p_expected_case_revision then
    raise exception 'stale_case_revision' using errcode = 'P0001';
  end if;

  if v_case.lifecycle_state <> p_expected_current_state then
    raise exception 'current_state_mismatch' using errcode = 'P0001';
  end if;

  update public.rental_cases
  set lifecycle_state = p_target_state,
      case_revision = v_case.case_revision + 1,
      dormant_origin_state = case
        when p_target_state = 'dormant' then coalesce(p_dormant_origin_state, v_case.lifecycle_state)
        else null
      end,
      resume_target_state = case
        when p_target_state = 'dormant' then p_resume_target_state
        else null
      end,
      dormant_reason_code = case
        when p_target_state = 'dormant' then p_dormant_reason_code
        else null
      end,
      dormant_review_at = case
        when p_target_state = 'dormant' then p_dormant_review_at
        else null
      end
  where id = p_rental_case_id;

  v_event_payload := coalesce(p_transition_event_payload, '{}'::jsonb) || jsonb_build_object(
    'previous_state', v_case.lifecycle_state,
    'new_state', p_target_state,
    'previous_revision', v_case.case_revision,
    'new_revision', v_case.case_revision + 1,
    'transition_reason_code', p_transition_reason_code,
    'manual_override', p_override_applied
  );

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
    origin_metadata
  )
  values (
    p_rental_case_id,
    p_transition_event_type_code,
    p_source_type,
    p_source_reference,
    p_actor_type,
    p_actor_reference,
    v_occurred_at,
    v_occurred_at,
    v_event_payload,
    jsonb_build_object(
      'lifecycle_commit', true,
      'manual_override', p_override_applied
    )
  )
  returning id into v_workflow_event_id;

  insert into public.rental_case_lifecycle_transitions (
    rental_case_id,
    from_lifecycle_state,
    to_lifecycle_state,
    triggering_event_id,
    source_type,
    source_reference,
    actor_type,
    actor_reference,
    transition_reason_code,
    override_applied,
    case_revision_before,
    case_revision_after,
    occurred_at
  )
  values (
    p_rental_case_id,
    v_case.lifecycle_state,
    p_target_state,
    p_triggering_event_id,
    p_source_type,
    p_source_reference,
    p_actor_type,
    p_actor_reference,
    p_transition_reason_code,
    p_override_applied,
    v_case.case_revision,
    v_case.case_revision + 1,
    v_occurred_at
  )
  returning id into v_lifecycle_transition_id;

  return query
  select
    p_rental_case_id,
    v_case.lifecycle_state,
    p_target_state,
    v_case.case_revision,
    v_case.case_revision + 1,
    v_lifecycle_transition_id,
    v_workflow_event_id,
    p_transition_reason_code,
    p_actor_reference,
    p_actor_type,
    p_source_type,
    p_source_reference,
    p_triggering_event_id,
    p_override_applied,
    v_occurred_at;
end;
$$;
