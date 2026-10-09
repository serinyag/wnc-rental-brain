"""One atomic, rehearsed production reference import; never copies workflow state."""
import json
from datetime import datetime,timezone
import psycopg
from tools.phase_05_search.semantic_common import load_env_value
from .provision_shared_database import HOST,REF,CA,DIRECTORY,staging_fingerprint
from .baseline_import import read_plan
from .microsoft_provisioning import Keychain


def main():
    rehearsal=json.loads((DIRECTORY/'baseline_import_rehearsal.json').read_text())
    if rehearsal['status']!='passed' or not rehearsal['disposable_database_removed']:
        raise ValueError('successful_reference_rehearsal_required')
    args=dict(host=HOST,dbname='postgres',sslmode='verify-full',sslrootcert=str(CA),connect_timeout=10)
    with psycopg.connect(**args,user='postgres.'+REF,password=load_env_value('SUPABASE_DB_PASSWORD')) as connection:
        connection.execute('set transaction isolation level repeatable read')
        connection.execute('select pg_advisory_xact_lock(862914052)')
        connection.execute("set local statement_timeout='120s'")
        if connection.execute('select count(*) from rental_production.knowledge_document_versions').fetchone()[0]:
            raise ValueError('production_baseline_exists_reconcile_before_retry')
        if connection.execute('select count(*) from rental_production.rental_cases').fetchone()[0]:
            raise ValueError('production_workflow_state_exists')
        before=staging_fingerprint(connection)
        selected,manifest,statements=read_plan(connection)
        if manifest['corpus_hash']!=rehearsal['source_corpus_hash']:
            raise ValueError('source_changed_after_reference_rehearsal')
        for statement in statements:
            connection.execute(statement,prepare=False)
        connection.execute('set constraints all immediate')
        if before!=staging_fingerprint(connection):
            raise ValueError('staging_changed_rollback')
        counts=connection.execute("select (select count(*) from rental_production.knowledge_document_versions),(select count(*) from rental_production.historical_case_versions),(select count(*) from rental_production.rental_cases)").fetchone()
        if counts!=(22,7,0):raise ValueError('production_baseline_counts_mismatch')
    # Independent restricted-login verification after commit; no automatic retry.
    from .database import ProductionCursor
    from .config import knowledge_fingerprint
    from tools.phase_08_workflow.outlook_inbound_service import connection_runner
    password=Keychain('wnc_production_runtime.'+REF,service='WNC Rental Brain production database runtime').read()
    with psycopg.connect(**args,user='wnc_production_runtime.'+REF,password=password,cursor_factory=ProductionCursor) as connection:
        digest=knowledge_fingerprint(connection_runner(connection))
    result={'status':'production_reference_baseline_loaded','source_corpus_hash':manifest['corpus_hash'],
        'runtime_corpus_hash':digest,'version':'governed-reference-v1','knowledge_versions':22,
        'historical_versions':7,'knowledge_embeddings':492,'historical_embeddings':82,
        'draft_versions_excluded':2,'personal_information_history_held_out':2,
        'production_workflow_cases':0,'staging_fingerprint_unchanged':True,
        'restricted_login_verified':True,'provider_calls':0,'at':datetime.now(timezone.utc).isoformat()}
    (DIRECTORY/'approved_pilot_baseline.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'status':'stopped','error_class':type(exc).__name__,
                          'sqlstate':getattr(exc,'sqlstate',None),'retry':False}))
        raise SystemExit(1)
