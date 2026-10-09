"""Provider-free shared-project migration rehearsal in a disposable local DB."""
import hashlib
import json
from pathlib import Path
import subprocess
from .schema_isolation import SCHEMAS, ROLES, migration_receipt

ROOT = Path(__file__).resolve().parents[2]
CONTAINER = 'supabase_db_wnc_rental_brain'
DATABASE = 'wnc_shared_schema_rehearsal'


def sql(statement, database=DATABASE):
    r = subprocess.run(['docker','exec','-i',CONTAINER,'psql','-X','-q','-v','ON_ERROR_STOP=1','-U','postgres','-d',database,'-At'], input=statement.encode(), capture_output=True)
    if r.returncode:
        raise RuntimeError(r.stderr.decode()[-1800:])
    return r.stdout.decode().strip()


def fingerprint():
    return sql("""select md5(string_agg(nspname||'.'||relname||':'||pg_get_userbyid(relowner)||':'||coalesce(relacl::text,''),chr(10) order by nspname,relname)) from pg_class join pg_namespace n on n.oid=relnamespace where nspname in ('public','private','api');""")


def main():
    paths = sorted((ROOT/'supabase/migrations').glob('*.sql'))
    assert len(paths) == 49 and len({p.name.split('_')[0] for p in paths}) == 49
    if DATABASE in sql('select datname from pg_database;', 'postgres').splitlines():
        raise RuntimeError('disposable_database_exists_inspect_before_retry')
    created_roles = []
    result = {'cloud_changes':0,'provider_calls':0,'migrations':[]}
    sql('create database '+DATABASE+';', 'postgres')
    try:
        sql('create schema extensions;')
        for p in paths:
            sql('begin;\n'+p.read_text()+'\ncommit;')
        before = fingerprint()
        from .schema_provisioning import bootstrap_sql
        statement, receipts = bootstrap_sql('b0fa5fbf-779f-4d1f-8e8f-2a3276fa4f06')
        created_roles = list(ROLES.values())
        sql('begin;\n'+statement+'\ncommit;')
        result['migrations'] = receipts
        after = fingerprint()
        assert before == after, 'staging_schema_privileges_or_objects_changed'
        # Production runtime has no membership in a platform-wide service role.
        sql('grant wnc_production_runtime to postgres;')
        allowed = sql('set role wnc_production_runtime; select count(*) from rental_production.rental_cases;')
        assert allowed == '0'
        try:
            sql('set role wnc_production_runtime; select count(*) from public.rental_cases;')
        except RuntimeError as exc:
            assert 'permission denied' in str(exc)
        else:
            raise AssertionError('production_role_can_read_staging')
        for role in ('anon','authenticated','service_role'):
            sql('grant '+role+' to postgres;')
            try:
                sql('set role '+role+'; select count(*) from rental_production.rental_cases;')
            except RuntimeError as exc:
                assert 'permission denied' in str(exc)
            else:
                raise AssertionError('platform_role_can_read_production:'+role)
        try:
            sql('set role wnc_production_runtime; create table rental_production.forbidden(x int);')
        except RuntimeError as exc:
            assert 'permission denied' in str(exc)
        else:
            raise AssertionError('runtime_can_create_objects')
        from .staging_role import STAGING_ROLE_SQL
        sql(STAGING_ROLE_SQL)
        created_roles.append('wnc_staging_runtime')
        sql('grant wnc_staging_runtime to postgres;')
        assert sql('set role wnc_staging_runtime; select count(*) from public.rental_cases;')=='0'
        try:
            sql('set role wnc_staging_runtime; select count(*) from rental_production.rental_cases;')
        except RuntimeError as exc:
            assert 'permission denied' in str(exc)
        else:
            raise AssertionError('restricted_staging_role_can_read_production')
        result['restricted_staging_role_production_read_denied']=True
        result['platform_roles_production_read_denied']=True
        result['production_runtime_ddl_denied']=True
        result['separate_ledger_rows']=sql('select count(*) from rental_production.provisioning_migrations;')
        assert result['separate_ledger_rows']=='49'
        result.update(status='passed',canonical_migration_count=len(paths),staging_fingerprint_unchanged=True,empty_production_cases=True,production_role_staging_read_denied=True)
    finally:
        sql('drop database '+DATABASE+';', 'postgres')
        for role in reversed(created_roles):
            sql('drop role '+role+';', 'postgres')
        result['disposable_database_removed'] = True
        out = ROOT/'docs/production_provisioning/shared_schema_rehearsal.json'
        out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='migrations'}))


if __name__ == '__main__':
    main()
