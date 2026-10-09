"""Prepare a restricted staging credential for the shared-project boundary."""
import json,os,secrets,tempfile
from datetime import datetime,timezone
from urllib.parse import quote
import psycopg
from psycopg import sql
from .staging_role import STAGING_ROLE_SQL
from .provision_shared_database import REF,HOST,DIRECTORY,CA
from .microsoft_provisioning import Keychain
from tools.phase_05_search.semantic_common import load_env_value

def main():
    keychain=Keychain('wnc_staging_runtime.'+REF,service='WNC Rental Brain staging database runtime')
    password=keychain.read()
    if password is None:
        password=secrets.token_urlsafe(48);keychain.add(password)
    kwargs=dict(host=HOST,port=5432,dbname='postgres',sslmode='verify-full',sslrootcert=str(CA),connect_timeout=10)
    with psycopg.connect(**kwargs,user='postgres.'+REF,password=load_env_value('SUPABASE_DB_PASSWORD')) as conn:
        if conn.execute("select count(*) from pg_roles where rolname='wnc_staging_runtime'").fetchone()[0]:raise RuntimeError('staging_role_exists_reconcile_before_retry')
        cur=conn.execute(STAGING_ROLE_SQL,prepare=False)
        while cur.nextset():pass
        conn.execute(sql.SQL('alter role wnc_staging_runtime login password {}').format(sql.Literal(password)))
    with psycopg.connect(**kwargs,user='wnc_staging_runtime.'+REF,password=password,autocommit=True) as conn:
        cases=conn.execute('select count(*) from public.rental_cases').fetchone()[0]
        for query in ('select count(*) from rental_production.rental_cases','create table public.forbidden(x int)'):
            try:conn.execute(query)
            except psycopg.errors.InsufficientPrivilege:pass
            else:raise RuntimeError('staging_role_boundary_failed_no_retry')
    fd,path=tempfile.mkstemp(prefix='wnc-render-staging-',suffix='.env')
    # Temporary 0600 file is uploaded through Render's normal Choose a file UI,
    # then removed. Never print content, paste a secret, or copy old provider keys.
    with os.fdopen(fd,'w') as handle:
        handle.write('DATABASE_URL=postgresql://wnc_staging_runtime.'+REF+':'+quote(password,safe='')+'@'+HOST+':5432/postgres\n')
        handle.write('PGSSLMODE=verify-full\nPGSSLROOTCERT=/etc/secrets/supabase-prod-ca-2021.crt\n')
        for key in ['STAGING_ALLOW_REAL_OUTLOOK_INBOUND','STAGING_ALLOW_REAL_OUTLOOK_SEND','STAGING_ALLOW_REAL_ASANA','STAGING_ALLOW_REAL_OUTLOOK']:
            handle.write(key+'=false\n')
    result={'status':'restricted_role_prepared','staging_case_count':cases,'restricted_login_verified':True,'production_read_denied':True,'ddl_denied':True,'render_connection_updated':False,'temporary_import_file':path,'at':datetime.now(timezone.utc).isoformat()}
    (DIRECTORY/'staging_role_provisioning.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'status':'stopped','error_class':type(exc).__name__,'sqlstate':getattr(exc,'sqlstate',None),'retry':False}))
        raise SystemExit(1)
