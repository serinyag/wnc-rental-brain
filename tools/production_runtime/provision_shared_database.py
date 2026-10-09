"""Provision the authorized free shared database without touching staging state."""
import json, secrets
from datetime import datetime, timezone
from pathlib import Path
import psycopg
from psycopg import sql
from tools.phase_05_search.semantic_common import load_env_value
from .schema_provisioning import bootstrap_sql, ROOT
from .microsoft_provisioning import Keychain
from .database import CA
REF='mspcopnsbounmdpivkvq'
HOST='aws-0-eu-central-1.pooler.supabase.com'
DIRECTORY=ROOT/'docs/production_provisioning'


def staging_fingerprint(connection):
    query="""select md5(string_agg(v,chr(10) order by v)) from (
select 'object:'||nspname||'.'||relname||':'||pg_get_userbyid(relowner)||':'||coalesce(relacl::text,'') v from pg_class join pg_namespace n on n.oid=relnamespace where nspname in ('public','private','api')
union all select 'function:'||pg_get_functiondef(p.oid) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where nspname in ('public','private','api') and p.prokind='f'
union all select 'migration:'||row_to_json(m)::text from supabase_migrations.schema_migrations m
union all select 'case:'||row_to_json(c)::text from public.rental_cases c
union all select 'action:'||row_to_json(a)::text from public.workflow_actions a
union all select 'attempt:'||row_to_json(a)::text from public.workflow_execution_attempts a
union all select 'event:'||row_to_json(e)::text from public.workflow_events e
union all select 'checkpoint:'||row_to_json(c)::text from public.outlook_inbound_checkpoints c
) q"""
    return connection.execute(query).fetchone()[0]


def main():
    decisions=json.loads((DIRECTORY/'authoritative_decisions.json').read_text())
    statement,receipts=bootstrap_sql(decisions['deployment_id'])
    keychain=Keychain('wnc_production_runtime.'+REF,service='WNC Rental Brain production database runtime')
    password=keychain.read()
    if password is None:
        password=secrets.token_urlsafe(48)
        keychain.add(password)
    admin_password=load_env_value('SUPABASE_DB_PASSWORD')
    connection_args=dict(host=HOST,port=5432,dbname='postgres',sslmode='verify-full',sslrootcert=str(CA),connect_timeout=10)
    with psycopg.connect(**connection_args,user='postgres.'+REF,password=admin_password,autocommit=True) as connection:
        # Refuse existing schemas; unknown previous outcomes must be reconciled.
        if connection.execute("select count(*) from pg_namespace where nspname like 'rental_production%'").fetchone()[0]:
            raise RuntimeError('production_namespaces_exist_reconcile_before_retry')
        with connection.transaction():
            connection.execute('set transaction isolation level repeatable read')
            before=staging_fingerprint(connection)
            cursor=connection.execute(statement,prepare=False)
            while cursor.nextset(): pass
            connection.execute(sql.SQL('alter role wnc_production_runtime login password {}').format(sql.Literal(password)))
            after=staging_fingerprint(connection)
            if before!=after:raise RuntimeError('staging_integrity_changed_rollback')
            if connection.execute('select count(*) from rental_production.rental_cases').fetchone()[0]!=0:raise RuntimeError('production_cases_not_empty_rollback')
    # Actual restricted login, not SET ROLE through an administrator session.
    with psycopg.connect(**connection_args,user='wnc_production_runtime.'+REF,password=password,autocommit=True) as connection:
        ledger=connection.execute('select count(*) from rental_production.provisioning_migrations').fetchone()[0]
        identity=connection.execute('select deployment_id::text,environment from rental_production.runtime_environment_identity').fetchone()
        if ledger!=49 or identity!=(decisions['deployment_id'],'production'):raise RuntimeError('production_post_commit_verification_failed_no_retry')
        for query in ('select count(*) from public.rental_cases','create table rental_production.forbidden(x int)','delete from rental_production.rule_catalogue where false'):
            try:connection.execute(query)
            except psycopg.errors.InsufficientPrivilege:pass
            else:raise RuntimeError('production_role_boundary_failed_no_retry')
    result={'status':'namespaces_provisioned','architecture':'shared_project_schemas_v1','project_ref':REF,'deployment_id':decisions['deployment_id'],'verified_tls':True,'canonical_migrations':49,'migrations':receipts,'staging_fingerprint_unchanged':True,'production_cases':0,'restricted_login_verified':True,'production_role_staging_read_denied':True,'runtime_ddl_denied':True,'knowledge_mutation_denied':True,'staging_admin_isolation_pending':True,'provider_calls':0,'provider_gates':{'outlook_inbound':False,'outlook_send':False,'asana_mutations':False},'at':datetime.now(timezone.utc).isoformat()}
    (DIRECTORY/'shared_database_provisioning.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='migrations'}))

if __name__=='__main__':
    try:main()
    except Exception as exc:
        # PostgreSQL errors can contain statements/data. Only stable class/state
        # may leave the process. Reconcile namespace presence before any retry.
        print(json.dumps({'status':'stopped','error_class':type(exc).__name__,'sqlstate':getattr(exc,'sqlstate',None),'retry':False}))
        raise SystemExit(1)
