"""Atomic empty production namespaces; no staging data or ledger mutations."""
import json
from pathlib import Path
from .schema_isolation import SCHEMAS, ROLES, migration_receipt
ROOT = Path(__file__).resolve().parents[2]


def bootstrap_sql(deployment_id):
    # IDs come from the authorized, persisted deployment decision.
    from uuid import UUID
    deployment_id = str(UUID(deployment_id))
    paths = sorted((ROOT/'supabase/migrations').glob('*.sql'))
    assert len(paths)==49 and len({p.name.split('_')[0] for p in paths})==49
    parts=["select pg_advisory_xact_lock(862914052);", "set local lock_timeout='5s';", "set local statement_timeout='120s';"]
    for role in ROLES.values():
        parts.append(f'create role {role} nologin noinherit nosuperuser nocreatedb nocreaterole nobypassrls;')
    parts.append('create schema rental_production;')
    receipts=[]
    for p in paths:
        receipt,compiled=migration_receipt(p.name,p.read_text())
        # Canonical files may wrap themselves in BEGIN/COMMIT. The isolated
        # provisioning operation owns the single outer transaction instead.
        parts.append(compiled);receipts.append(receipt)
    parts.append('''
create table rental_production.provisioning_migrations (
 filename text primary key, source_sha256 text not null, compiled_sha256 text not null,
 applied_at timestamptz not null default now());
alter table rental_production.provisioning_migrations enable row level security;
''')
    for r in receipts:
        parts.append("insert into rental_production.provisioning_migrations values ('%s','%s','%s',now());" % (r['file'],r['source_sha256'],r['compiled_sha256']))
    parts.append("insert into rental_production.runtime_environment_identity(deployment_id,environment) values ('%s','production');" % deployment_id)
    # Runtime can read the approved corpus and write only workflow state.
    parts.append('''
grant usage on schema rental_production,rental_production_private,rental_production_api,extensions to wnc_production_runtime;
grant select on all tables in schema rental_production,rental_production_private to wnc_production_runtime;
grant usage,select on all sequences in schema rental_production to wnc_production_runtime;
grant select on all sequences in schema rental_production_private to wnc_production_runtime;
do $$ begin execute format('grant wnc_production_lifecycle_executor to %I',current_user); end $$;
grant execute on all functions in schema rental_production,rental_production_private,rental_production_api to wnc_production_runtime;
do $$ begin execute format('revoke wnc_production_lifecycle_executor from %I',current_user); end $$;
do $$ declare t record; mutable boolean; begin
 for t in select c.relname,n.nspname from pg_class c join pg_namespace n on n.oid=c.relnamespace
  where n.nspname in ('rental_production','rental_production_private') and c.relkind in ('r','p') loop
  execute format('create policy production_runtime_read on %I.%I for select to wnc_production_runtime using(true)',t.nspname,t.relname);
  mutable:=t.nspname='rental_production' and (t.relname like 'rental_case%' or t.relname='rental_cases' or t.relname like 'workflow_%' or t.relname like 'outlook_inbound_%' or t.relname like 'inbound_%' or t.relname like 'inquiry_response_%' or t.relname='case_data_lifecycle_holds');
  if mutable then
   execute format('grant insert,update,delete on %I.%I to wnc_production_runtime',t.nspname,t.relname);
   execute format('create policy production_runtime_write on %I.%I for all to wnc_production_runtime using(true) with check(true)',t.nspname,t.relname);
  end if;
 end loop;
end $$;
revoke all on schema rental_production,rental_production_private,rental_production_api from public,anon,authenticated,service_role;
revoke all on all tables in schema rental_production,rental_production_private from public,anon,authenticated,service_role;
do $$ begin execute format('grant wnc_production_lifecycle_executor to %I',current_user); end $$;
revoke all on all functions in schema rental_production,rental_production_private,rental_production_api from public,anon,authenticated,service_role;
do $$ begin execute format('revoke wnc_production_lifecycle_executor from %I',current_user); end $$;
''')
    return '\n'.join(parts),receipts
