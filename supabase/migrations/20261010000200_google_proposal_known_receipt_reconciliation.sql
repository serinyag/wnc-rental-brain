-- Google projection bindings live in the normal immutable action/attempt journal.
-- No external document content is allowed into rental_case_facts by this path.
create or replace function private.guard_google_proposal_attempt()
returns trigger language plpgsql as $$
declare
  v_action public.workflow_actions%rowtype;
  v_scope jsonb;
begin
  if new.adapter_code <> 'google_proposal' then return new; end if;
  perform 1 from public.rental_cases where id = new.rental_case_id for update;
  select * into strict v_action from public.workflow_actions
    where id = new.workflow_action_id and rental_case_id = new.rental_case_id;
  if v_action.target_adapter_code <> 'google_proposal'
     or v_action.structured_payload->'projection'->>'version' is distinct from 'google_proposal_v1'
     or (v_action.structured_payload->'projection'->>'rental_case_id')::bigint is distinct from new.rental_case_id then
    raise exception 'google_proposal_contract_invalid';
  end if;
  if exists (select 1 from public.workflow_execution_attempts a
    where a.rental_case_id = new.rental_case_id and a.adapter_code = 'google_proposal'
      and (a.status = 'started' or (a.status <> 'succeeded' and not a.retry_eligible
        and not exists (select 1 from public.workflow_events e
          where e.rental_case_id=a.rental_case_id and e.event_type_code='google_proposal_reconciled'
            and e.structured_payload->>'execution_attempt_id'=a.id::text
            and e.structured_payload->>'workflow_action_id'=a.workflow_action_id::text
            and e.structured_payload->>'status'='MATCHES_PROJECTION')))) then
    raise exception 'google_proposal_requires_reconciliation';
  end if;
  select a.structured_payload->'projection' into v_scope
    from public.workflow_execution_attempts e join public.workflow_actions a on a.id = e.workflow_action_id
    where e.rental_case_id = new.rental_case_id and e.adapter_code = 'google_proposal'
    order by e.id limit 1;
  if v_scope is not null and (
      v_scope->>'folder_id' is distinct from v_action.structured_payload->'projection'->>'folder_id'
      or v_scope->>'provider_identity' is distinct from v_action.structured_payload->'projection'->>'provider_identity'
      or v_scope->>'proposal_identity' is distinct from v_action.structured_payload->'projection'->>'proposal_identity') then
    raise exception 'google_proposal_scope_immutable';
  end if;
  return new;
end;
$$;

-- Only normal, explicitly scoped reconciliation may acknowledge a known receipt.
create or replace function private.guard_google_proposal_reconciliation()
returns trigger language plpgsql as $$
declare
  a public.workflow_execution_attempts%rowtype;
  w public.workflow_actions%rowtype;
  b jsonb;
  original jsonb;
  k text;
  current_revision bigint;
begin
  if TG_OP <> 'INSERT' then
    if old.event_type_code='google_proposal_reconciled' or (TG_OP='UPDATE' and new.event_type_code='google_proposal_reconciled') then
      raise exception 'google_reconciliation_immutable';
    end if;
    if TG_OP='DELETE' then return old; end if;
    return new;
  end if;
  if new.event_type_code <> 'google_proposal_reconciled' then return new; end if;
  select case_revision into strict current_revision from public.rental_cases where id=new.rental_case_id for update;
  select * into strict a from public.workflow_execution_attempts
    where id=(new.structured_payload->>'execution_attempt_id')::bigint and rental_case_id=new.rental_case_id;
  select * into strict w from public.workflow_actions where id=a.workflow_action_id and rental_case_id=new.rental_case_id;
  b=new.structured_payload->'binding'; original=a.response_snapshot->'binding';
  if a.adapter_code <> 'google_proposal' or a.status <> 'failed' or a.retry_eligible
      or original is null or b is null or new.actor_type <> 'operator'
      or coalesce(a.response_snapshot->>'reason','') not in ('google_content_verification_failed','google_post_write_revision_unverifiable','google_http_503','google_transport_unknown')
      or new.structured_payload->>'workflow_action_id' is distinct from w.id::text
      or new.structured_payload->>'status' is distinct from 'MATCHES_PROJECTION'
      or new.structured_payload->>'provider_mutations' is distinct from '0'
      or new.structured_payload->>'business_truth_changed' is distinct from 'false'
      or b->>'source_case_revision' is distinct from current_revision::text
      or b->>'source_case_revision' is distinct from w.source_case_revision::text
      or b->>'projection_hash' is distinct from w.structured_payload->'projection'->>'projection_hash'
      or coalesce(b->>'document_fingerprint','') !~ '^[a-f0-9]{64}$'
      or coalesce(b->>'provider_revision','')='' then
    raise exception 'google_reconciliation_contract_invalid';
  end if;
  foreach k in array array['rental_case_id','document_id','file_id','folder_id','provider_identity','proposal_identity'] loop
    if b->>k is distinct from original->>k then raise exception 'google_reconciliation_binding_conflict'; end if;
  end loop;
  if exists (select 1 from public.workflow_execution_attempts where rental_case_id=new.rental_case_id
      and adapter_code='google_proposal' and status='started') then raise exception 'google_reconciliation_inflight'; end if;
  return new;
end;
$$;
create trigger google_proposal_reconciliation_fence before insert or update or delete on public.workflow_events
for each row execute function private.guard_google_proposal_reconciliation();
revoke all on function private.guard_google_proposal_reconciliation() from public;
