"""Atomic production-only lifecycle provisioning after disposable rehearsal."""
import hashlib,json
from datetime import datetime,timezone
import psycopg
from tools.phase_05_search.semantic_common import load_env_value
from .provision_shared_database import HOST,REF,CA,DIRECTORY,staging_fingerprint

def main():
    rehearsal=json.loads((DIRECTORY/'privacy_split_rehearsal.json').read_text())
    if rehearsal.get('status')!='passed':raise ValueError('privacy_rehearsal_required')
    source=(DIRECTORY.parents[1]/'tools/production_runtime/privacy_lifecycle.sql').read_text()
    with psycopg.connect(host=HOST,port=5432,dbname='postgres',user='postgres.'+REF,
        password=load_env_value('SUPABASE_DB_PASSWORD'),sslmode='verify-full',sslrootcert=str(CA),connect_timeout=10) as c:
        if c.execute("select to_regclass('rental_production.runtime_case_closures')").fetchone()[0] is not None:
            raise ValueError('privacy_component_exists_reconcile_before_retry')
        before=staging_fingerprint(c)
        if c.execute('select count(*) from rental_production.rental_cases').fetchone()[0]!=0:
            raise ValueError('empty_production_cases_required')
        cursor=c.execute(source,prepare=False)
        while cursor.nextset():pass
        if before!=staging_fingerprint(c):raise ValueError('staging_fingerprint_changed_rollback')
        count=c.execute('select count(*) from rental_production.provisioning_migrations').fetchone()[0]
        if count!=49:raise ValueError('canonical_ledger_changed_rollback')
    receipt={'status':'provisioned','checked_at':datetime.now(timezone.utc).isoformat(),
        'component_sha256':hashlib.sha256(source.encode()).hexdigest(),'canonical_migrations':49,
        'staging_fingerprint_unchanged':True,'production_cases':0,'provider_calls':0,
        'raw_body_days_after_closure':180,'structured_calendar_years_after_closure':2,
        'technical_log_days':90,'accounting_documents':'excluded','disposable_rehearsal_passed':True}
    (DIRECTORY/'privacy_lifecycle_provisioning.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))

if __name__=='__main__':
    try:main()
    except Exception as error:
        print(json.dumps({'status':'stopped','error_class':type(error).__name__,'sqlstate':getattr(error,'sqlstate',None),'retry':False}))
        raise SystemExit(1)
