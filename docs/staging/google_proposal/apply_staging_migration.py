"""Pinned staging DDL only; no case actions or provider executions."""
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from docs.staging.case586_integrated.common import client
from tools.phase_05_search.semantic_common import load_env_value
from tools.phase_08_workflow.outlook_inbound_runtime import validate_staging_database
import psycopg
def connect():
    assert load_env_value("SUPABASE_PROJECT_REF")=="mspcopnsbounmdpivkvq"
    route="postgresql://postgres.mspcopnsbounmdpivkvq@aws-0-eu-central-1.pooler.supabase.com:5432/postgres"
    validate_staging_database(route)
    return psycopg.connect(route,password=load_env_value("SUPABASE_DB_PASSWORD"),sslmode="require",connect_timeout=15)
OUT=Path(__file__).parent
health=client().get_health()
assert health['environment']=='staging'
assert health['providers']['outlook'] in {'configured_draft_only','configured_but_disabled'}
assert health['providers']['asana']=='configured_but_disabled'
(OUT/'health_before.json').write_text(json.dumps(health,indent=2)+'\n')
migration=ROOT/'supabase/migrations/20261010000100_google_proposal_projection_fences.sql'
version='20261010000100'
with connect() as conn:
    assert conn.execute('select current_database()').fetchone()[0]=='postgres'
    def counts():
        return {table:conn.execute('select count(*) from public.'+table).fetchone()[0]
            for table in ('rental_cases','rental_case_facts','workflow_actions','workflow_events','workflow_execution_attempts')}
    before=counts()
    if not conn.execute('select 1 from supabase_migrations.schema_migrations where version=%s',(version,)).fetchone():
        conn.execute(migration.read_text())
        conn.execute('insert into supabase_migrations.schema_migrations(version,name,statements) values(%s,%s,%s)',
            (version,'google_proposal_projection_fences',[migration.read_text()]))
    assert counts()==before
    assert conn.execute("select count(*) from pg_trigger where tgname in ('google_proposal_attempt_fence','google_proposal_action_immutable') and tgenabled='O'").fetchone()[0]==2
    assert conn.execute("select count(*) from public.workflow_actions where target_adapter_code='google_proposal'").fetchone()[0]==0
(OUT/'migration.json').write_text(json.dumps({'environment':'staging','project_ref':'mspcopnsbounmdpivkvq',
    'version':version,'sha256':hashlib.sha256(migration.read_bytes()).hexdigest(),
    'canonical_row_counts_unchanged':True,'google_actions':0,'google_provider_calls':0},indent=2)+'\n')
print('Staging projection fences installed. Canonical row counts unchanged; zero Google actions.')
