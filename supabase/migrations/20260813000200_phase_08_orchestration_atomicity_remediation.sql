create or replace function private.phase8_reference_id(p_reference text)
returns bigint
language sql
immutable
as $$
  select nullif(substring(coalesce(p_reference, '') from '([0-9]+)$'), '')::bigint;
$$;


create or replace function private.commit_phase8_case_decision_approval(
  p_rental_case_id bigint,
  p_approval_request_id bigint,
  p_decision text,
  p_expected_case_revision integer,
  p_actor_type text default null,
  p_actor_reference text default null,
  p_decision_payload jsonb default null,
  p_decision_notes text default null,
  p_decided_at timestamptz default null
)
returns table (
  rental_case_id bigint,
  approval_request_id bigint,
  approval_status text,
  case_revision_before integer,
  case_revision_after integer,
  audit_event_ids bigint[],
  resolved_blocker_ids bigint[],
  activated_case_decision_id bigint,
  rejected_case_decision_id bigint,
  artifact_freshness_changed_ids bigint[],
  superseded_action_ids bigint[],
  failure_code text
)
language plpgsql
as $$
#variable_conflict use_column
declare
  v_case public.rental_cases%rowtype;
  v_approval public.rental_case_approval_requests%rowtype;
  v_decision_record public.rental_case_decisions%rowtype;
  v_decided_at timestamptz := coalesce(p_decided_at, timezone('utc', now()));
  v_target_entity_id bigint;
  v_artifact_ids bigint[] := '{}'::bigint[];
  v_superseded_action_ids bigint[] := '{}'::bigint[];
  v_resolved_blocker_ids bigint[] := '{}'::bigint[];
  v_audit_event_ids bigint[] := '{}'::bigint[];
  v_event_id bigint;
  v_new_case_revision integer;
begin
  if p_decision not in ('approved', 'rejected') then
    return query
    select p_rental_case_id, p_approval_request_id, 'open'::text, p_expected_case_revision, p_expected_case_revision,
      '{}'::bigint[], '{}'::bigint[], null::bigint, null::bigint, '{}'::bigint[], '{}'::bigint[],
      'invalid_orchestration_input'::text;
    return;
  end if;

  select *
  into v_case
  from public.rental_cases
  where id = p_rental_case_id
  for update;

  if not found then
    return query
    select p_rental_case_id, p_approval_request_id, 'open'::text, p_expected_case_revision, p_expected_case_revision,
      '{}'::bigint[], '{}'::bigint[], null::bigint, null::bigint, '{}'::bigint[], '{}'::bigint[],
      'case_not_found'::text;
    return;
  end if;

  if v_case.case_revision <> p_expected_case_revision then
    return query
    select p_rental_case_id, p_approval_request_id, 'open'::text, v_case.case_revision, v_case.case_revision,
      '{}'::bigint[], '{}'::bigint[], null::bigint, null::bigint, '{}'::bigint[], '{}'::bigint[],
      'stale_case_revision'::text;
    return;
  end if;

  select *
  into v_approval
  from public.rental_case_approval_requests
  where id = p_approval_request_id
    and rental_case_id = p_rental_case_id
  for update;

  if not found then
    return query
    select p_rental_case_id, p_approval_request_id, 'open'::text, v_case.case_revision, v_case.case_revision,
      '{}'::bigint[], '{}'::bigint[], null::bigint, null::bigint, '{}'::bigint[], '{}'::bigint[],
      'approval_target_invalid'::text;
    return;
  end if;

  if v_approval.target_entity_type <> 'case_decision' then
    return query
    select p_rental_case_id, p_approval_request_id, v_approval.status, v_case.case_revision, v_case.case_revision,
      '{}'::bigint[], '{}'::bigint[], null::bigint, null::bigint, '{}'::bigint[], '{}'::bigint[],
      'approval_target_mismatch'::text;
    return;
  end if;

  v_target_entity_id := coalesce(v_approval.target_entity_id, private.phase8_reference_id(v_approval.target_entity_reference));
  if v_target_entity_id is null then
    return query
    select p_rental_case_id, p_approval_request_id, v_approval.status, v_case.case_revision, v_case.case_revision,
      '{}'::bigint[], '{}'::bigint[], null::bigint, null::bigint, '{}'::bigint[], '{}'::bigint[],
      'approval_target_invalid'::text;
    return;
  end if;

  select *
  into v_decision_record
  from public.rental_case_decisions
  where id = v_target_entity_id
    and rental_case_id = p_rental_case_id
  for update;

  if not found then
    return query
    select p_rental_case_id, p_approval_request_id, v_approval.status, v_case.case_revision, v_case.case_revision,
      '{}'::bigint[], '{}'::bigint[], null::bigint, null::bigint, '{}'::bigint[], '{}'::bigint[],
      'approval_target_invalid'::text;
    return;
  end if;

  if v_approval.status in ('approved', 'rejected') then
    if (v_approval.status = 'approved' and p_decision = 'approved')
       or (v_approval.status = 'rejected' and p_decision = 'rejected') then
      return query
      select
        p_rental_case_id,
        p_approval_request_id,
        v_approval.status,
        v_case.case_revision,
        v_case.case_revision,
        '{}'::bigint[],
        '{}'::bigint[],
        case when v_decision_record.status = 'active' then v_decision_record.id else null end,
        case when v_decision_record.status = 'rejected' then v_decision_record.id else null end,
        '{}'::bigint[],
        '{}'::bigint[],
        null::text;
      return;
    end if;
    return query
    select p_rental_case_id, p_approval_request_id, v_approval.status, v_case.case_revision, v_case.case_revision,
      '{}'::bigint[], '{}'::bigint[], null::bigint, null::bigint, '{}'::bigint[], '{}'::bigint[],
      'invalid_entity_status'::text;
    return;
  end if;

  if p_decision = 'approved' then
    if v_decision_record.status not in ('proposed', 'pending_approval') then
      return query
      select p_rental_case_id, p_approval_request_id, v_approval.status, v_case.case_revision, v_case.case_revision,
        '{}'::bigint[], '{}'::bigint[], null::bigint, null::bigint, '{}'::bigint[], '{}'::bigint[],
        'case_decision_not_activatable'::text;
      return;
    end if;

    if exists (
      select 1
      from public.rental_case_decisions conflict
      where conflict.rental_case_id = p_rental_case_id
        and conflict.domain_code = v_decision_record.domain_code
        and conflict.scope_key = v_decision_record.scope_key
        and conflict.status = 'active'
        and conflict.id <> v_decision_record.id
    ) then
      return query
      select p_rental_case_id, p_approval_request_id, v_approval.status, v_case.case_revision, v_case.case_revision,
        '{}'::bigint[], '{}'::bigint[], null::bigint, null::bigint, '{}'::bigint[], '{}'::bigint[],
        'case_decision_conflict'::text;
      return;
    end if;

    update public.rental_case_approval_requests
    set status = 'approved',
        decision_payload = coalesce(p_decision_payload, '{"decision":"approved"}'::jsonb),
        decided_at = v_decided_at,
        decided_by_reference = p_actor_reference,
        decision_notes = p_decision_notes,
        updated_at = v_decided_at
    where id = p_approval_request_id
      and rental_case_id = p_rental_case_id;

    update public.rental_case_decisions
    set status = 'active',
        effective_value_payload = proposed_value_payload,
        approval_request_id = p_approval_request_id,
        effective_at = v_decided_at,
        updated_at = v_decided_at
    where id = v_decision_record.id
      and rental_case_id = p_rental_case_id;

    update public.rental_cases
    set case_revision = case_revision + 1,
        updated_at = v_decided_at
    where id = p_rental_case_id;

    v_new_case_revision := v_case.case_revision + 1;

    with updated_artifacts as (
      update public.rental_case_artifacts
      set freshness_status = case
            when artifact_type in ('proposal', 'agreement', 'internal_event_brief') then 'refresh_required'
            else 'stale'
          end,
          updated_at = v_decided_at
      where rental_case_id = p_rental_case_id
        and artifact_type in (
          'proposal',
          'agreement',
          'internal_event_brief',
          'task_surface_projection',
          'calendar_projection'
        )
        and freshness_status in ('current', 'stale')
        and derived_from_case_revision < v_new_case_revision
      returning id
    )
    select coalesce(array_agg(id order by id), '{}'::bigint[])
    into v_artifact_ids
    from updated_artifacts;

    with updated_actions as (
      update public.workflow_actions
      set status = 'superseded',
          updated_at = v_decided_at
      where rental_case_id = p_rental_case_id
        and status not in ('succeeded', 'failed', 'cancelled', 'superseded')
        and source_case_revision < v_new_case_revision
      returning id
    )
    select coalesce(array_agg(id order by id), '{}'::bigint[])
    into v_superseded_action_ids
    from updated_actions;

    with resolved_blockers as (
      update public.rental_case_blockers
      set status = 'resolved',
          resolved_at = v_decided_at,
          resolution_reference = coalesce(resolution_reference, 'structured_resolution')
      where rental_case_id = p_rental_case_id
        and status = 'open'
        and origin_entity_type = 'case_decision'
        and (
          origin_entity_id = v_decision_record.id
          or origin_entity_reference = concat('case_decision:', v_decision_record.id)
        )
      returning id
    )
    select coalesce(array_agg(id order by id), '{}'::bigint[])
    into v_resolved_blocker_ids
    from resolved_blockers;

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
      'approval_decided',
      'phase8_atomic_commit',
      concat('approval:', p_approval_request_id),
      p_actor_type,
      p_actor_reference,
      v_decided_at,
      v_decided_at,
      jsonb_build_object(
        'approval_request_id', p_approval_request_id,
        'target_entity_type', 'case_decision',
        'target_entity_id', v_decision_record.id,
        'status_before', 'open',
        'status_after', 'approved'
      ),
      concat('phase8:approval:approved:', p_approval_request_id, ':', p_expected_case_revision),
      jsonb_build_object('phase', '8.5r')
    )
    returning id into v_event_id;
    v_audit_event_ids := array_append(v_audit_event_ids, v_event_id);

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
      'case_decision_activated',
      'phase8_atomic_commit',
      concat('case_decision:', v_decision_record.id),
      p_actor_type,
      p_actor_reference,
      v_decided_at,
      v_decided_at,
      jsonb_build_object(
        'case_decision_id', v_decision_record.id,
        'approval_request_id', p_approval_request_id,
        'case_revision_before', v_case.case_revision,
        'case_revision_after', v_new_case_revision
      ),
      concat('phase8:case_decision:activated:', v_decision_record.id, ':', p_expected_case_revision),
      jsonb_build_object('phase', '8.5r')
    )
    returning id into v_event_id;
    v_audit_event_ids := array_append(v_audit_event_ids, v_event_id);

    if coalesce(array_length(v_artifact_ids, 1), 0) > 0 then
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
        'artifact_freshness_changed',
        'phase8_atomic_commit',
        concat('case_decision:', v_decision_record.id),
        p_actor_type,
        p_actor_reference,
        v_decided_at,
        v_decided_at,
        jsonb_build_object('artifact_reference_ids', v_artifact_ids),
        concat('phase8:artifacts:case_decision:', v_decision_record.id, ':', p_expected_case_revision),
        jsonb_build_object('phase', '8.5r')
      )
      returning id into v_event_id;
      v_audit_event_ids := array_append(v_audit_event_ids, v_event_id);
    end if;

    if coalesce(array_length(v_superseded_action_ids, 1), 0) > 0 then
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
        'workflow_action_superseded',
        'phase8_atomic_commit',
        concat('case_decision:', v_decision_record.id),
        p_actor_type,
        p_actor_reference,
        v_decided_at,
        v_decided_at,
        jsonb_build_object('workflow_action_ids', v_superseded_action_ids),
        concat('phase8:actions:superseded:case_decision:', v_decision_record.id, ':', p_expected_case_revision),
        jsonb_build_object('phase', '8.5r')
      )
      returning id into v_event_id;
      v_audit_event_ids := array_append(v_audit_event_ids, v_event_id);
    end if;

    if coalesce(array_length(v_resolved_blocker_ids, 1), 0) > 0 then
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
        'blocker_resolved',
        'phase8_atomic_commit',
        concat('case_decision:', v_decision_record.id),
        p_actor_type,
        p_actor_reference,
        v_decided_at,
        v_decided_at,
        jsonb_build_object('blocker_ids', v_resolved_blocker_ids),
        concat('phase8:blockers:resolved:case_decision:', v_decision_record.id, ':', p_expected_case_revision),
        jsonb_build_object('phase', '8.5r')
      )
      returning id into v_event_id;
      v_audit_event_ids := array_append(v_audit_event_ids, v_event_id);
    end if;

    return query
    select
      p_rental_case_id,
      p_approval_request_id,
      'approved'::text,
      v_case.case_revision,
      v_new_case_revision,
      v_audit_event_ids,
      v_resolved_blocker_ids,
      v_decision_record.id,
      null::bigint,
      v_artifact_ids,
      v_superseded_action_ids,
      null::text;
    return;
  end if;

  update public.rental_case_approval_requests
  set status = 'rejected',
      decision_payload = p_decision_payload,
      decided_at = v_decided_at,
      decided_by_reference = p_actor_reference,
      decision_notes = p_decision_notes,
      updated_at = v_decided_at
  where id = p_approval_request_id
    and rental_case_id = p_rental_case_id;

  update public.rental_case_decisions
  set status = 'rejected',
      updated_at = v_decided_at
  where id = v_decision_record.id
    and rental_case_id = p_rental_case_id;

  with resolved_blockers as (
    update public.rental_case_blockers
    set status = 'resolved',
        resolved_at = v_decided_at,
        resolution_reference = coalesce(resolution_reference, 'structured_resolution')
    where rental_case_id = p_rental_case_id
      and status = 'open'
      and origin_entity_type = 'case_decision'
      and (
        origin_entity_id = v_decision_record.id
        or origin_entity_reference = concat('case_decision:', v_decision_record.id)
      )
    returning id
  )
  select coalesce(array_agg(id order by id), '{}'::bigint[])
  into v_resolved_blocker_ids
  from resolved_blockers;

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
    'approval_decided',
    'phase8_atomic_commit',
    concat('approval:', p_approval_request_id),
    p_actor_type,
    p_actor_reference,
    v_decided_at,
    v_decided_at,
    jsonb_build_object(
      'approval_request_id', p_approval_request_id,
      'target_entity_type', 'case_decision',
      'target_entity_id', v_decision_record.id,
      'status_before', 'open',
      'status_after', 'rejected'
    ),
    concat('phase8:approval:rejected:', p_approval_request_id, ':', p_expected_case_revision),
    jsonb_build_object('phase', '8.5r')
  )
  returning id into v_event_id;
  v_audit_event_ids := array_append(v_audit_event_ids, v_event_id);

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
    'case_decision_rejected',
    'phase8_atomic_commit',
    concat('case_decision:', v_decision_record.id),
    p_actor_type,
    p_actor_reference,
    v_decided_at,
    v_decided_at,
    jsonb_build_object(
      'case_decision_id', v_decision_record.id,
      'approval_request_id', p_approval_request_id
    ),
    concat('phase8:case_decision:rejected:', v_decision_record.id, ':', p_expected_case_revision),
    jsonb_build_object('phase', '8.5r')
  )
  returning id into v_event_id;
  v_audit_event_ids := array_append(v_audit_event_ids, v_event_id);

  if coalesce(array_length(v_resolved_blocker_ids, 1), 0) > 0 then
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
      'blocker_resolved',
      'phase8_atomic_commit',
      concat('case_decision:', v_decision_record.id),
      p_actor_type,
      p_actor_reference,
      v_decided_at,
      v_decided_at,
      jsonb_build_object('blocker_ids', v_resolved_blocker_ids),
      concat('phase8:blockers:resolved:case_decision:rejected:', v_decision_record.id, ':', p_expected_case_revision),
      jsonb_build_object('phase', '8.5r')
    )
    returning id into v_event_id;
    v_audit_event_ids := array_append(v_audit_event_ids, v_event_id);
  end if;

  return query
  select
    p_rental_case_id,
    p_approval_request_id,
    'rejected'::text,
    v_case.case_revision,
    v_case.case_revision,
    v_audit_event_ids,
    v_resolved_blocker_ids,
    null::bigint,
    v_decision_record.id,
    '{}'::bigint[],
    '{}'::bigint[],
    null::text;
end;
$$;


create or replace function private.commit_phase8_workflow_action_approval(
  p_rental_case_id bigint,
  p_approval_request_id bigint,
  p_decision text,
  p_expected_case_revision integer,
  p_actor_type text default null,
  p_actor_reference text default null,
  p_decision_payload jsonb default null,
  p_decision_notes text default null,
  p_decided_at timestamptz default null
)
returns table (
  rental_case_id bigint,
  approval_request_id bigint,
  workflow_action_id bigint,
  approval_status text,
  action_status_before text,
  action_status_after text,
  case_revision_before integer,
  case_revision_after integer,
  audit_event_ids bigint[],
  resolved_blocker_ids bigint[],
  failure_code text
)
language plpgsql
as $$
#variable_conflict use_column
declare
  v_case public.rental_cases%rowtype;
  v_approval public.rental_case_approval_requests%rowtype;
  v_action public.workflow_actions%rowtype;
  v_decided_at timestamptz := coalesce(p_decided_at, timezone('utc', now()));
  v_target_entity_id bigint;
  v_resolved_blocker_ids bigint[] := '{}'::bigint[];
  v_audit_event_ids bigint[] := '{}'::bigint[];
  v_event_id bigint;
  v_action_status_after text;
begin
  if p_decision not in ('approved', 'rejected') then
    return query
    select p_rental_case_id, p_approval_request_id, 0::bigint, 'open'::text, 'awaiting_approval'::text, 'awaiting_approval'::text,
      p_expected_case_revision, p_expected_case_revision, '{}'::bigint[], '{}'::bigint[], 'invalid_orchestration_input'::text;
    return;
  end if;

  select *
  into v_case
  from public.rental_cases
  where id = p_rental_case_id
  for update;

  if not found then
    return query
    select p_rental_case_id, p_approval_request_id, 0::bigint, 'open'::text, 'awaiting_approval'::text, 'awaiting_approval'::text,
      p_expected_case_revision, p_expected_case_revision, '{}'::bigint[], '{}'::bigint[], 'case_not_found'::text;
    return;
  end if;

  if v_case.case_revision <> p_expected_case_revision then
    return query
    select p_rental_case_id, p_approval_request_id, 0::bigint, 'open'::text, 'awaiting_approval'::text, 'awaiting_approval'::text,
      v_case.case_revision, v_case.case_revision, '{}'::bigint[], '{}'::bigint[], 'stale_case_revision'::text;
    return;
  end if;

  select *
  into v_approval
  from public.rental_case_approval_requests
  where id = p_approval_request_id
    and rental_case_id = p_rental_case_id
  for update;

  if not found then
    return query
    select p_rental_case_id, p_approval_request_id, 0::bigint, 'open'::text, 'awaiting_approval'::text, 'awaiting_approval'::text,
      v_case.case_revision, v_case.case_revision, '{}'::bigint[], '{}'::bigint[], 'approval_target_invalid'::text;
    return;
  end if;

  if v_approval.target_entity_type <> 'workflow_action' then
    return query
    select p_rental_case_id, p_approval_request_id, 0::bigint, v_approval.status, 'awaiting_approval'::text, 'awaiting_approval'::text,
      v_case.case_revision, v_case.case_revision, '{}'::bigint[], '{}'::bigint[], 'approval_target_mismatch'::text;
    return;
  end if;

  v_target_entity_id := coalesce(v_approval.target_entity_id, private.phase8_reference_id(v_approval.target_entity_reference));
  if v_target_entity_id is null then
    return query
    select p_rental_case_id, p_approval_request_id, 0::bigint, v_approval.status, 'awaiting_approval'::text, 'awaiting_approval'::text,
      v_case.case_revision, v_case.case_revision, '{}'::bigint[], '{}'::bigint[], 'approval_target_invalid'::text;
    return;
  end if;

  select *
  into v_action
  from public.workflow_actions
  where id = v_target_entity_id
    and rental_case_id = p_rental_case_id
  for update;

  if not found then
    return query
    select p_rental_case_id, p_approval_request_id, v_target_entity_id, v_approval.status, 'awaiting_approval'::text, 'awaiting_approval'::text,
      v_case.case_revision, v_case.case_revision, '{}'::bigint[], '{}'::bigint[], 'approval_target_invalid'::text;
    return;
  end if;

  if v_approval.status in ('approved', 'rejected') then
    if (v_approval.status = 'approved' and p_decision = 'approved')
       or (v_approval.status = 'rejected' and p_decision = 'rejected') then
      return query
      select p_rental_case_id, p_approval_request_id, v_action.id, v_approval.status, v_action.status, v_action.status,
        v_case.case_revision, v_case.case_revision, '{}'::bigint[], '{}'::bigint[], null::text;
      return;
    end if;
    return query
    select p_rental_case_id, p_approval_request_id, v_action.id, v_approval.status, v_action.status, v_action.status,
      v_case.case_revision, v_case.case_revision, '{}'::bigint[], '{}'::bigint[], 'invalid_entity_status'::text;
    return;
  end if;

  if v_action.approval_posture = 'blocked' then
    return query
    select p_rental_case_id, p_approval_request_id, v_action.id, v_approval.status, v_action.status, v_action.status,
      v_case.case_revision, v_case.case_revision, '{}'::bigint[], '{}'::bigint[], 'action_blocked'::text;
    return;
  end if;

  if v_action.status not in ('proposed', 'awaiting_approval') then
    return query
    select p_rental_case_id, p_approval_request_id, v_action.id, v_approval.status, v_action.status, v_action.status,
      v_case.case_revision, v_case.case_revision, '{}'::bigint[], '{}'::bigint[], 'action_state_transition_invalid'::text;
    return;
  end if;

  if p_decision = 'approved' then
    update public.rental_case_approval_requests
    set status = 'approved',
        decision_payload = coalesce(p_decision_payload, '{"decision":"approved"}'::jsonb),
        decided_at = v_decided_at,
        decided_by_reference = p_actor_reference,
        decision_notes = p_decision_notes,
        updated_at = v_decided_at
    where id = p_approval_request_id
      and rental_case_id = p_rental_case_id;

    update public.workflow_actions
    set status = 'approved',
        updated_at = v_decided_at
    where id = v_action.id
      and rental_case_id = p_rental_case_id;

    v_action_status_after := 'approved';
    if v_action.approval_posture in ('approval_required', 'automatic_allowed') then
      update public.workflow_actions
      set status = 'ready_to_execute',
          updated_at = v_decided_at
      where id = v_action.id
        and rental_case_id = p_rental_case_id;
      v_action_status_after := 'ready_to_execute';
    end if;
  else
    update public.rental_case_approval_requests
    set status = 'rejected',
        decision_payload = p_decision_payload,
        decided_at = v_decided_at,
        decided_by_reference = p_actor_reference,
        decision_notes = p_decision_notes,
        updated_at = v_decided_at
    where id = p_approval_request_id
      and rental_case_id = p_rental_case_id;

    update public.workflow_actions
    set status = 'cancelled',
        updated_at = v_decided_at
    where id = v_action.id
      and rental_case_id = p_rental_case_id;
    v_action_status_after := 'cancelled';
  end if;

  with resolved_blockers as (
    update public.rental_case_blockers
    set status = 'resolved',
        resolved_at = v_decided_at,
        resolution_reference = coalesce(resolution_reference, 'structured_resolution')
    where rental_case_id = p_rental_case_id
      and status = 'open'
      and origin_entity_type = 'workflow_action'
      and (
        origin_entity_id = v_action.id
        or origin_entity_reference = concat('workflow_action:', v_action.id)
      )
    returning id
  )
  select coalesce(array_agg(id order by id), '{}'::bigint[])
  into v_resolved_blocker_ids
  from resolved_blockers;

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
    'approval_decided',
    'phase8_atomic_commit',
    concat('approval:', p_approval_request_id),
    p_actor_type,
    p_actor_reference,
    v_decided_at,
    v_decided_at,
    jsonb_build_object(
      'approval_request_id', p_approval_request_id,
      'target_entity_type', 'workflow_action',
      'target_entity_id', v_action.id,
      'status_before', 'open',
      'status_after', case when p_decision = 'approved' then 'approved' else 'rejected' end
    ),
    concat('phase8:approval:workflow_action:', p_approval_request_id, ':', p_decision, ':', p_expected_case_revision),
    jsonb_build_object('phase', '8.5r')
  )
  returning id into v_event_id;
  v_audit_event_ids := array_append(v_audit_event_ids, v_event_id);

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
    'workflow_action_status_changed',
    'phase8_atomic_commit',
    concat('workflow_action:', v_action.id),
    p_actor_type,
    p_actor_reference,
    v_decided_at,
    v_decided_at,
    jsonb_build_object(
      'workflow_action_id', v_action.id,
      'status_before', v_action.status,
      'status_after', case when p_decision = 'approved' then 'approved' else 'cancelled' end
    ),
    concat('phase8:workflow_action:status1:', v_action.id, ':', p_expected_case_revision, ':', p_decision),
    jsonb_build_object('phase', '8.5r')
  )
  returning id into v_event_id;
  v_audit_event_ids := array_append(v_audit_event_ids, v_event_id);

  if p_decision = 'approved' and v_action_status_after = 'ready_to_execute' then
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
      'workflow_action_status_changed',
      'phase8_atomic_commit',
      concat('workflow_action:', v_action.id),
      p_actor_type,
      p_actor_reference,
      v_decided_at,
      v_decided_at,
      jsonb_build_object(
        'workflow_action_id', v_action.id,
        'status_before', 'approved',
        'status_after', 'ready_to_execute'
      ),
      concat('phase8:workflow_action:status2:', v_action.id, ':', p_expected_case_revision),
      jsonb_build_object('phase', '8.5r')
    )
    returning id into v_event_id;
    v_audit_event_ids := array_append(v_audit_event_ids, v_event_id);
  end if;

  if coalesce(array_length(v_resolved_blocker_ids, 1), 0) > 0 then
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
      'blocker_resolved',
      'phase8_atomic_commit',
      concat('workflow_action:', v_action.id),
      p_actor_type,
      p_actor_reference,
      v_decided_at,
      v_decided_at,
      jsonb_build_object('blocker_ids', v_resolved_blocker_ids),
      concat('phase8:blockers:workflow_action:', v_action.id, ':', p_expected_case_revision),
      jsonb_build_object('phase', '8.5r')
    )
    returning id into v_event_id;
    v_audit_event_ids := array_append(v_audit_event_ids, v_event_id);
  end if;

  return query
  select
    p_rental_case_id,
    p_approval_request_id,
    v_action.id,
    case when p_decision = 'approved' then 'approved' else 'rejected' end,
    v_action.status,
    v_action_status_after,
    v_case.case_revision,
    v_case.case_revision,
    v_audit_event_ids,
    v_resolved_blocker_ids,
    null::text;
end;
$$;


create or replace function private.commit_phase8_proposed_case_change_resolution(
  p_rental_case_id bigint,
  p_proposed_case_change_id bigint,
  p_decision text,
  p_expected_case_revision integer,
  p_actor_type text default null,
  p_actor_reference text default null,
  p_final_value_payload jsonb default null,
  p_decision_notes text default null,
  p_decided_at timestamptz default null
)
returns table (
  rental_case_id bigint,
  proposed_case_change_id bigint,
  resulting_status text,
  case_revision_before integer,
  case_revision_after integer,
  updated_rental_case_fact_id bigint,
  audit_event_ids bigint[],
  artifact_freshness_changed_ids bigint[],
  superseded_action_ids bigint[],
  failure_code text
)
language plpgsql
as $$
#variable_conflict use_column
declare
  v_case public.rental_cases%rowtype;
  v_change public.rental_case_proposed_changes%rowtype;
  v_decided_at timestamptz := coalesce(p_decided_at, timezone('utc', now()));
  v_final_value_payload jsonb;
  v_artifact_ids bigint[] := '{}'::bigint[];
  v_superseded_action_ids bigint[] := '{}'::bigint[];
  v_audit_event_ids bigint[] := '{}'::bigint[];
  v_event_id bigint;
  v_fact_id bigint;
  v_new_case_revision integer;
  v_resolved_blocker_ids bigint[] := '{}'::bigint[];
begin
  if p_decision not in ('approved', 'rejected') then
    return query
    select p_rental_case_id, p_proposed_case_change_id, 'rejected'::text, p_expected_case_revision, p_expected_case_revision,
      null::bigint, '{}'::bigint[], '{}'::bigint[], '{}'::bigint[], 'invalid_orchestration_input'::text;
    return;
  end if;

  select *
  into v_case
  from public.rental_cases
  where id = p_rental_case_id
  for update;

  if not found then
    return query
    select p_rental_case_id, p_proposed_case_change_id, 'rejected'::text, p_expected_case_revision, p_expected_case_revision,
      null::bigint, '{}'::bigint[], '{}'::bigint[], '{}'::bigint[], 'case_not_found'::text;
    return;
  end if;

  if v_case.case_revision <> p_expected_case_revision then
    return query
    select p_rental_case_id, p_proposed_case_change_id, 'rejected'::text, v_case.case_revision, v_case.case_revision,
      null::bigint, '{}'::bigint[], '{}'::bigint[], '{}'::bigint[], 'stale_case_revision'::text;
    return;
  end if;

  select *
  into v_change
  from public.rental_case_proposed_changes
  where id = p_proposed_case_change_id
    and rental_case_id = p_rental_case_id
  for update;

  if not found then
    return query
    select p_rental_case_id, p_proposed_case_change_id, 'rejected'::text, v_case.case_revision, v_case.case_revision,
      null::bigint, '{}'::bigint[], '{}'::bigint[], '{}'::bigint[], 'proposed_change_not_resolvable'::text;
    return;
  end if;

  if v_change.status in ('accepted', 'rejected') then
    if (v_change.status = 'accepted' and p_decision = 'approved')
       or (v_change.status = 'rejected' and p_decision = 'rejected') then
      return query
      select p_rental_case_id, p_proposed_case_change_id,
        case when v_change.status = 'accepted' then 'accepted' else 'rejected' end,
        v_case.case_revision, v_case.case_revision, null::bigint, '{}'::bigint[], '{}'::bigint[], '{}'::bigint[], null::text;
      return;
    end if;
    return query
    select p_rental_case_id, p_proposed_case_change_id, 'rejected'::text, v_case.case_revision, v_case.case_revision,
      null::bigint, '{}'::bigint[], '{}'::bigint[], '{}'::bigint[], 'invalid_entity_status'::text;
    return;
  end if;

  if p_decision = 'approved' then
    if v_change.review_posture = 'approval_required' and not exists (
      select 1
      from public.rental_case_approval_requests approval
      where approval.rental_case_id = p_rental_case_id
        and approval.status = 'approved'
        and approval.target_entity_type = 'proposed_case_change'
        and coalesce(approval.target_entity_id, private.phase8_reference_id(approval.target_entity_reference)) = p_proposed_case_change_id
    ) then
      return query
      select p_rental_case_id, p_proposed_case_change_id, 'rejected'::text, v_case.case_revision, v_case.case_revision,
        null::bigint, '{}'::bigint[], '{}'::bigint[], '{}'::bigint[], 'approval_required'::text;
      return;
    end if;

    v_final_value_payload := coalesce(p_final_value_payload, v_change.proposed_value_payload);

    if v_change.change_kind in ('active_event_window', 'date_change') then
      if jsonb_typeof(v_final_value_payload) <> 'object' then
        return query
        select p_rental_case_id, p_proposed_case_change_id, 'rejected'::text, v_case.case_revision, v_case.case_revision,
          null::bigint, '{}'::bigint[], '{}'::bigint[], '{}'::bigint[], 'proposed_change_resolution_failed'::text;
        return;
      end if;

      update public.rental_cases
      set case_revision = case_revision + 1,
          active_event_start = nullif(v_final_value_payload ->> 'start', '')::timestamptz,
          active_event_end = nullif(v_final_value_payload ->> 'end', '')::timestamptz,
          updated_at = v_decided_at
      where id = p_rental_case_id;
      v_new_case_revision := v_case.case_revision + 1;
    else
      update public.rental_cases
      set case_revision = case_revision + 1,
          updated_at = v_decided_at
      where id = p_rental_case_id;
      v_new_case_revision := v_case.case_revision + 1;

      insert into public.rental_case_facts (
        rental_case_id,
        field_code,
        domain_code,
        value_payload,
        source_reference,
        established_case_revision,
        created_at,
        updated_at
      )
      values (
        p_rental_case_id,
        v_change.change_kind,
        v_change.domain_code,
        v_final_value_payload,
        coalesce(v_change.source_reference, concat('proposed_change:', p_proposed_case_change_id)),
        v_new_case_revision,
        v_decided_at,
        v_decided_at
      )
      on conflict (rental_case_id, field_code) do update
      set domain_code = excluded.domain_code,
          value_payload = excluded.value_payload,
          source_reference = excluded.source_reference,
          established_case_revision = excluded.established_case_revision,
          updated_at = excluded.updated_at
      returning id into v_fact_id;
    end if;

    update public.rental_case_proposed_changes
    set status = 'accepted',
        final_value_payload = v_final_value_payload,
        accepted_at = v_decided_at,
        updated_at = v_decided_at
    where id = p_proposed_case_change_id
      and rental_case_id = p_rental_case_id;

    with updated_artifacts as (
      update public.rental_case_artifacts
      set freshness_status = case
            when artifact_type in ('proposal', 'agreement', 'internal_event_brief') then 'refresh_required'
            else 'stale'
          end,
          updated_at = v_decided_at
      where rental_case_id = p_rental_case_id
        and artifact_type in (
          'proposal',
          'agreement',
          'internal_event_brief',
          'task_surface_projection',
          'calendar_projection'
        )
        and freshness_status in ('current', 'stale')
        and derived_from_case_revision < v_new_case_revision
      returning id
    )
    select coalesce(array_agg(id order by id), '{}'::bigint[])
    into v_artifact_ids
    from updated_artifacts;

    with updated_actions as (
      update public.workflow_actions
      set status = 'superseded',
          updated_at = v_decided_at
      where rental_case_id = p_rental_case_id
        and status not in ('succeeded', 'failed', 'cancelled', 'superseded')
        and source_case_revision < v_new_case_revision
      returning id
    )
    select coalesce(array_agg(id order by id), '{}'::bigint[])
    into v_superseded_action_ids
    from updated_actions;

    with resolved_blockers as (
      update public.rental_case_blockers
      set status = 'resolved',
          resolved_at = v_decided_at,
          resolution_reference = coalesce(resolution_reference, 'structured_resolution')
      where rental_case_id = p_rental_case_id
        and status = 'open'
        and origin_entity_type = 'proposed_case_change'
        and (
          origin_entity_id = p_proposed_case_change_id
          or origin_entity_reference = concat('proposed_change:', p_proposed_case_change_id)
        )
      returning id
    )
    select coalesce(array_agg(id order by id), '{}'::bigint[])
    into v_resolved_blocker_ids
    from resolved_blockers;

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
      'case_fact_changed',
      'phase8_atomic_commit',
      concat('proposed_change:', p_proposed_case_change_id),
      p_actor_type,
      p_actor_reference,
      v_decided_at,
      v_decided_at,
      jsonb_build_object(
        'field_code', v_change.change_kind,
        'rental_case_fact_id', v_fact_id,
        'case_revision_before', v_case.case_revision,
        'case_revision_after', v_new_case_revision
      ),
      concat('phase8:case_fact:changed:', p_proposed_case_change_id, ':', p_expected_case_revision),
      jsonb_build_object('phase', '8.5r')
    )
    returning id into v_event_id;
    v_audit_event_ids := array_append(v_audit_event_ids, v_event_id);

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
      'proposed_case_change_accepted',
      'phase8_atomic_commit',
      concat('proposed_change:', p_proposed_case_change_id),
      p_actor_type,
      p_actor_reference,
      v_decided_at,
      v_decided_at,
      jsonb_build_object(
        'proposed_case_change_id', p_proposed_case_change_id,
        'case_revision_before', v_case.case_revision,
        'case_revision_after', v_new_case_revision
      ),
      concat('phase8:proposed_change:accepted:', p_proposed_case_change_id, ':', p_expected_case_revision),
      jsonb_build_object('phase', '8.5r')
    )
    returning id into v_event_id;
    v_audit_event_ids := array_append(v_audit_event_ids, v_event_id);

    if coalesce(array_length(v_artifact_ids, 1), 0) > 0 then
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
        'artifact_freshness_changed',
        'phase8_atomic_commit',
        concat('proposed_change:', p_proposed_case_change_id),
        p_actor_type,
        p_actor_reference,
        v_decided_at,
        v_decided_at,
        jsonb_build_object('artifact_reference_ids', v_artifact_ids),
        concat('phase8:artifacts:proposed_change:', p_proposed_case_change_id, ':', p_expected_case_revision),
        jsonb_build_object('phase', '8.5r')
      )
      returning id into v_event_id;
      v_audit_event_ids := array_append(v_audit_event_ids, v_event_id);
    end if;

    if coalesce(array_length(v_superseded_action_ids, 1), 0) > 0 then
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
        'workflow_action_superseded',
        'phase8_atomic_commit',
        concat('proposed_change:', p_proposed_case_change_id),
        p_actor_type,
        p_actor_reference,
        v_decided_at,
        v_decided_at,
        jsonb_build_object('workflow_action_ids', v_superseded_action_ids),
        concat('phase8:actions:superseded:proposed_change:', p_proposed_case_change_id, ':', p_expected_case_revision),
        jsonb_build_object('phase', '8.5r')
      )
      returning id into v_event_id;
      v_audit_event_ids := array_append(v_audit_event_ids, v_event_id);
    end if;

    if coalesce(array_length(v_resolved_blocker_ids, 1), 0) > 0 then
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
        'blocker_resolved',
        'phase8_atomic_commit',
        concat('proposed_change:', p_proposed_case_change_id),
        p_actor_type,
        p_actor_reference,
        v_decided_at,
        v_decided_at,
        jsonb_build_object('blocker_ids', v_resolved_blocker_ids),
        concat('phase8:blockers:proposed_change:', p_proposed_case_change_id, ':', p_expected_case_revision),
        jsonb_build_object('phase', '8.5r')
      )
      returning id into v_event_id;
      v_audit_event_ids := array_append(v_audit_event_ids, v_event_id);
    end if;

    return query
    select p_rental_case_id, p_proposed_case_change_id, 'accepted'::text, v_case.case_revision, v_new_case_revision,
      v_fact_id, v_audit_event_ids, v_artifact_ids, v_superseded_action_ids, null::text;
    return;
  end if;

  update public.rental_case_proposed_changes
  set status = 'rejected',
      updated_at = v_decided_at
  where id = p_proposed_case_change_id
    and rental_case_id = p_rental_case_id;

  with resolved_blockers as (
    update public.rental_case_blockers
    set status = 'resolved',
        resolved_at = v_decided_at,
        resolution_reference = coalesce(resolution_reference, 'structured_resolution')
    where rental_case_id = p_rental_case_id
      and status = 'open'
      and origin_entity_type = 'proposed_case_change'
      and (
        origin_entity_id = p_proposed_case_change_id
        or origin_entity_reference = concat('proposed_change:', p_proposed_case_change_id)
      )
    returning id
  )
  select coalesce(array_agg(id order by id), '{}'::bigint[])
  into v_resolved_blocker_ids
  from resolved_blockers;

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
    'proposed_case_change_rejected',
    'phase8_atomic_commit',
    concat('proposed_change:', p_proposed_case_change_id),
    p_actor_type,
    p_actor_reference,
    v_decided_at,
    v_decided_at,
    jsonb_build_object(
      'proposed_case_change_id', p_proposed_case_change_id,
      'decision_notes', p_decision_notes,
      'resolved_blocker_ids', v_resolved_blocker_ids
    ),
    concat('phase8:proposed_change:rejected:', p_proposed_case_change_id, ':', p_expected_case_revision),
    jsonb_build_object('phase', '8.5r')
  )
  returning id into v_event_id;
  v_audit_event_ids := array_append(v_audit_event_ids, v_event_id);

  return query
  select p_rental_case_id, p_proposed_case_change_id, 'rejected'::text, v_case.case_revision, v_case.case_revision,
    null::bigint, v_audit_event_ids, '{}'::bigint[], '{}'::bigint[], null::text;
end;
$$;


create index if not exists workflow_actions_ready_to_execute_idx
  on public.workflow_actions (rental_case_id, due_at, id)
  where status = 'ready_to_execute';
