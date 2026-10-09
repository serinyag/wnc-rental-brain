-- Production deployment component, separate from the 49 canonical migrations.
-- Closure has its own clock; later edits cannot silently extend retention.
create table rental_production.runtime_case_closures (
 rental_case_id bigint primary key references rental_production.rental_cases(id),
 closed_at timestamptz not null,
 recorded_at timestamptz not null default now()
);
create table rental_production.runtime_lifecycle_journal (
 id uuid primary key, deployment_id uuid not null references rental_production.runtime_environment_identity(deployment_id),
 payload jsonb not null, recorded_at timestamptz not null default now()
);
create table rental_production.runtime_raw_body_dispositions (
 rental_case_id bigint primary key references rental_production.rental_cases(id),
 actor_reference text not null, policy_version text not null,
 content_digest text not null, recorded_at timestamptz not null default now()
);
do $$ declare t text; begin
 foreach t in array array['runtime_case_closures','runtime_lifecycle_journal','runtime_raw_body_dispositions'] loop
  execute format('alter table rental_production.%I enable row level security',t);
  execute format('revoke all on rental_production.%I from public,anon,authenticated,service_role,wnc_staging_runtime',t);
  execute format('grant select on rental_production.%I to wnc_production_runtime,wnc_production_lifecycle_executor',t);
  execute format('create policy production_lifecycle_read on rental_production.%I for select to wnc_production_runtime,wnc_production_lifecycle_executor using(true)',t);
 end loop;
end $$;
grant insert on rental_production.runtime_lifecycle_journal to wnc_production_runtime;
create policy production_lifecycle_journal_insert on rental_production.runtime_lifecycle_journal for insert to wnc_production_runtime with check(true);
grant insert,update,delete on rental_production.runtime_case_closures to wnc_production_lifecycle_executor;
create policy production_closure_write on rental_production.runtime_case_closures for all to wnc_production_lifecycle_executor using(true) with check(true);
grant insert on rental_production.runtime_raw_body_dispositions to wnc_production_lifecycle_executor;
create policy production_raw_disposition_insert on rental_production.runtime_raw_body_dispositions for insert to wnc_production_lifecycle_executor with check(true);
grant update on rental_production.runtime_raw_body_dispositions,rental_production.runtime_lifecycle_journal to wnc_production_lifecycle_executor;
create policy production_raw_disposition_redact on rental_production.runtime_raw_body_dispositions for update to wnc_production_lifecycle_executor using(true) with check(true);
create policy production_journal_redact on rental_production.runtime_lifecycle_journal for update to wnc_production_lifecycle_executor using(true) with check(true);
grant wnc_production_lifecycle_executor to postgres;
grant create on schema rental_production_private,rental_production to wnc_production_lifecycle_executor;
-- The original routine's mutable updated_at clock is replaced by the fixed
-- calendar closure check in the only runtime-callable wrapper below.
do $$ declare body text; old_clause text:='or c.updated_at>now()-make_interval(days=>p_days)'; begin
 body=pg_get_functiondef('rental_production.anonymize_closed_rental_case(bigint,text,text,text,integer)'::regprocedure);
 if strpos(body,old_clause)=0 then raise exception 'canonical_lifecycle_clock_shape_changed'; end if;
 execute replace(body,old_clause,'');
end $$;
create function rental_production_private.record_runtime_case_closure()
returns trigger language plpgsql security definer set search_path=pg_catalog,rental_production as $$
begin
 if old.is_active and not new.is_active then
  insert into rental_production.runtime_case_closures(rental_case_id,closed_at) values(new.id,now())
  on conflict(rental_case_id) do update set closed_at=excluded.closed_at,recorded_at=now();
 elsif not old.is_active and new.is_active then
  delete from rental_production.runtime_case_closures where rental_case_id=new.id;
 end if;
 return new;
end $$;
alter function rental_production_private.record_runtime_case_closure() owner to wnc_production_lifecycle_executor;
revoke all on function rental_production_private.record_runtime_case_closure() from public;
create trigger runtime_case_closure after update of is_active on rental_production.rental_cases for each row execute function rental_production_private.record_runtime_case_closure();
create function rental_production.purge_closed_case_raw_bodies(p_case bigint,p_actor text,p_policy text)
returns text language plpgsql security definer set search_path=pg_catalog,rental_production,extensions as $$
declare closed timestamptz; fingerprint text;
begin
 if p_actor !~ '^entra:[0-9a-f-]{36}:[0-9a-f-]{36}$' or p_actor is null or p_policy<>'WNC_PILOT_RETENTION_20261009' or p_policy is null then raise exception 'approved_lifecycle_authority_required'; end if;
 perform 1 from rental_production.rental_cases where id=p_case and not is_active for update;
 if not found then raise exception 'case_lifecycle_hold'; end if;
 select closed_at into closed from rental_production.runtime_case_closures where rental_case_id=p_case;
 if closed is null or closed+interval '180 days'>now()
  or exists(select 1 from rental_production.case_data_lifecycle_holds where rental_case_id=p_case)
  or exists(select 1 from rental_production.workflow_actions where rental_case_id=p_case and status not in ('succeeded','cancelled','superseded'))
  or exists(select 1 from rental_production.workflow_execution_attempts where rental_case_id=p_case and (status='started' or (status<>'succeeded' and not retry_eligible)))
  or exists(select 1 from rental_production.rental_case_approval_requests where rental_case_id=p_case and status='open')
 then raise exception 'case_lifecycle_hold'; end if;
 select content_digest into fingerprint from rental_production.runtime_raw_body_dispositions where rental_case_id=p_case;
 if found then return fingerprint; end if;
 select encode(digest(coalesce(string_agg(source_hash,'|' order by mailbox,message_id),''),'sha256'),'hex') into fingerprint from rental_production.outlook_inbound_messages where rental_case_id=p_case;
 -- IDs, source hashes, structured facts, drafts, and attempt bindings survive.
 update rental_production.outlook_inbound_messages set raw_provider_payload=raw_provider_payload-array['body','bodyPreview','uniqueBody'],
  envelope=envelope-array['raw_body','normalized_body'] where rental_case_id=p_case;
 update rental_production.workflow_events set structured_payload=structured_payload-'body' where rental_case_id=p_case and event_type_code='outlook_inbound_evidence_recorded';
 update rental_production.inbound_source_records set evidence_excerpt='[expired raw email excerpt]' where resolved_rental_case_id=p_case and source_system_code='email';
 update rental_production.inbound_observations set source_excerpt='[expired raw email excerpt]' where rental_case_id=p_case and inbound_source_record_id in (select id from rental_production.inbound_source_records where resolved_rental_case_id=p_case and source_system_code='email');
 insert into rental_production.runtime_raw_body_dispositions values(p_case,p_actor,p_policy,fingerprint,now());
 return fingerprint;
end $$;
alter function rental_production.purge_closed_case_raw_bodies(bigint,text,text) owner to wnc_production_lifecycle_executor;
revoke all on function rental_production.purge_closed_case_raw_bodies(bigint,text,text) from public,anon,authenticated,service_role,wnc_staging_runtime;
grant execute on function rental_production.purge_closed_case_raw_bodies(bigint,text,text) to wnc_production_runtime;
create function rental_production.anonymize_case_at_calendar_expiry(p_case bigint,p_actor text,p_policy text,p_request text)
returns uuid language plpgsql security definer set search_path=pg_catalog,rental_production as $$
declare closed timestamptz; receipt uuid;
begin
 if p_policy<>'WNC_PILOT_RETENTION_20261009' or p_policy is null then raise exception 'approved_lifecycle_authority_required'; end if;
 select closed_at into closed from rental_production.runtime_case_closures where rental_case_id=p_case;
 if closed is null or closed+interval '2 years'>now() then raise exception 'case_lifecycle_hold'; end if;
 receipt=rental_production.anonymize_closed_rental_case(p_case,p_actor,p_policy,p_request,1);
 update rental_production.runtime_raw_body_dispositions set actor_reference='[redacted]' where rental_case_id=p_case;
 update rental_production.runtime_lifecycle_journal set payload=jsonb_build_object('case_id',p_case,'disposition','expired','lifecycle_receipt',receipt)
  where payload->>'case_id'=p_case::text;
 return receipt;
end $$;
alter function rental_production.anonymize_case_at_calendar_expiry(bigint,text,text,text) owner to wnc_production_lifecycle_executor;
revoke all on function rental_production.anonymize_case_at_calendar_expiry(bigint,text,text,text) from public,anon,authenticated,service_role,wnc_staging_runtime;
grant execute on function rental_production.anonymize_case_at_calendar_expiry(bigint,text,text,text) to wnc_production_runtime;
revoke execute on function rental_production.anonymize_closed_rental_case(bigint,text,text,text,integer) from wnc_production_runtime;
revoke create on schema rental_production_private,rental_production from wnc_production_lifecycle_executor;
revoke wnc_production_lifecycle_executor from postgres;
