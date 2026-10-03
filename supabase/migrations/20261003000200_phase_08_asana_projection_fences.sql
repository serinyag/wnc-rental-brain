-- Reuse the canonical action/attempt journal; do not make Asana a truth store.
create or replace function private.guard_asana_projection_attempt()
returns trigger language plpgsql as $$
declare
  v_action public.workflow_actions%rowtype;
  v_scope jsonb;
begin
  if new.adapter_code <> 'asana_projection' then return new; end if;
  -- Serializes independent actions for the same case, including different
  -- revisions. A crash leaving a started attempt intentionally retains a fence.
  perform 1 from public.rental_cases where id = new.rental_case_id for update;
  select * into strict v_action from public.workflow_actions
    where id = new.workflow_action_id and rental_case_id = new.rental_case_id;
  if v_action.target_adapter_code <> 'asana_projection'
     or v_action.structured_payload->'projection'->>'version' is distinct from 'asana_rental_projection_v1'
     or (v_action.structured_payload->'projection'->>'rental_case_id')::bigint is distinct from new.rental_case_id then
    raise exception 'asana_projection_contract_invalid';
  end if;
  if exists (select 1 from public.workflow_execution_attempts a
    where a.rental_case_id = new.rental_case_id and a.adapter_code = 'asana_projection'
      and (a.status = 'started' or (a.status <> 'succeeded' and not a.retry_eligible))) then
    raise exception 'asana_projection_requires_reconciliation';
  end if;
  select a.structured_payload->'projection' into v_scope
    from public.workflow_execution_attempts e join public.workflow_actions a on a.id = e.workflow_action_id
    where e.rental_case_id = new.rental_case_id and e.adapter_code = 'asana_projection'
    order by e.id limit 1;
  if v_scope is not null and (
      v_scope->>'workspace_gid' is distinct from v_action.structured_payload->'projection'->>'workspace_gid'
      or v_scope->>'project_gid' is distinct from v_action.structured_payload->'projection'->>'project_gid'
      or v_scope->>'case_uuid' is distinct from v_action.structured_payload->'projection'->>'case_uuid') then
    raise exception 'asana_projection_scope_immutable';
  end if;
  return new;
end;
$$;

drop trigger if exists asana_projection_attempt_fence on public.workflow_execution_attempts;
create trigger asana_projection_attempt_fence before insert on public.workflow_execution_attempts
for each row execute function private.guard_asana_projection_attempt();

create or replace function private.guard_asana_projection_action()
returns trigger language plpgsql as $$
begin
  if old.target_adapter_code = 'asana_projection' and (
       new.structured_payload is distinct from old.structured_payload
       or new.action_type is distinct from old.action_type
       or new.target_adapter_code is distinct from old.target_adapter_code
       or new.rental_case_id is distinct from old.rental_case_id
       or new.source_case_revision is distinct from old.source_case_revision
       or new.idempotency_key is distinct from old.idempotency_key
       or new.semantic_subject_hash is distinct from old.semantic_subject_hash) then
    raise exception 'asana_projection_action_immutable';
  end if;
  return new;
end;
$$;
drop trigger if exists asana_projection_action_immutable on public.workflow_actions;
create trigger asana_projection_action_immutable before update on public.workflow_actions
for each row execute function private.guard_asana_projection_action();
revoke all on function private.guard_asana_projection_attempt() from public;
revoke all on function private.guard_asana_projection_action() from public;
