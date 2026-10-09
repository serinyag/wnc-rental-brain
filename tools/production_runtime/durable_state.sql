-- Additional deployment state; canonical migration ledger remains unchanged.
create table rental_production.runtime_provider_controls (
 deployment_id uuid primary key references rental_production.runtime_environment_identity(deployment_id),
 lanes jsonb not null check (jsonb_typeof(lanes)='object'
  and lanes ?& array['outlook_inbound','outlook_send','asana_mutations']
  and lanes - array['outlook_inbound','outlook_send','asana_mutations']='{}'::jsonb
  and jsonb_typeof(lanes->'outlook_inbound')='boolean'
  and jsonb_typeof(lanes->'outlook_send')='boolean'
  and jsonb_typeof(lanes->'asana_mutations')='boolean'),
 lease_expires double precision not null default 0 check(lease_expires>=0)
);
create table rental_production.runtime_operator_registry (
 deployment_id uuid not null references rental_production.runtime_environment_identity(deployment_id),
 object_id uuid not null, enabled boolean not null default false,
 name text not null check(btrim(name)<>''),
 roles jsonb not null check(jsonb_typeof(roles)='array'
  and roles <@ '["OPERATOR","APPROVER","DECISION_AUTHORITY","ADMIN"]'::jsonb),
 primary key(deployment_id,object_id)
);
create table rental_production.runtime_alert_outbox (
 event_id text primary key check(event_id ~ '^[0-9a-f]{64}$'),
 deployment_id uuid not null references rental_production.runtime_environment_identity(deployment_id),
 payload jsonb not null, status text not null default 'pending'
  check(status in ('pending','sending','accepted','ambiguous','failed')),
 created_at timestamptz not null default now(), accepted_at timestamptz,
 receipt jsonb
);
create table rental_production.runtime_monitor_heartbeat (
 deployment_id uuid primary key references rental_production.runtime_environment_identity(deployment_id),
 observed_at timestamptz not null, signals integer not null check(signals>=0)
);
do $$ declare t text; begin
 foreach t in array array['runtime_provider_controls','runtime_operator_registry','runtime_alert_outbox','runtime_monitor_heartbeat'] loop
  execute format('alter table rental_production.%I enable row level security',t);
  execute format('revoke all on rental_production.%I from public,anon,authenticated,service_role,wnc_staging_runtime',t);
  execute format('grant select,insert,update,delete on rental_production.%I to wnc_production_runtime',t);
  execute format('create policy production_runtime_state on rental_production.%I for all to wnc_production_runtime using(true) with check(true)',t);
 end loop;
end $$;
