"""Apply only the inbound schema to the explicitly pinned staging database."""
import json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
import psycopg
from tools.phase_05_search.semantic_common import load_env_value
from tools.staging_calibration.run_operator_calibration import build_client
OUT=Path(__file__).parent
assert not (OUT/'migration.json').exists()
assert load_env_value('SUPABASE_PROJECT_REF')=='mspcopnsbounmdpivkvq'
health=build_client(ROOT/'Staging Authentications.txt',timeout_seconds=120).get_health()
assert health['environment']=='staging' and health['providers']=={'asana':'configured_but_disabled','outlook':'configured_draft_only'}
(OUT/'health_before.json').write_text(json.dumps(health,indent=2)+'\n')
protected=json.loads((ROOT/'docs/staging/outlook_reconciled_closure/raw_after.json').read_text())
migration=ROOT/'supabase/migrations/20261009000300_phase_08_outlook_inbound.sql'
with psycopg.connect(host='db.mspcopnsbounmdpivkvq.supabase.co',dbname='postgres',user='postgres',password=load_env_value('SUPABASE_DB_PASSWORD'),sslmode='require',connect_timeout=15) as c:
 def rows(t,cid):return c.execute(f"select coalesce(json_agg(row_to_json(r) order by r.id),'[]') from public.{t} r where rental_case_id=%s",(cid,)).fetchone()[0]
 assert {cid:{t:rows(t,int(cid)) for t in ts} for cid,ts in protected.items()}==protected
 asana={t:rows(t,585) for t in ('workflow_actions','workflow_execution_attempts','workflow_events','rental_case_facts')}
 assert not c.execute("select 1 from supabase_migrations.schema_migrations where version='20261009000100'").fetchone()
 c.execute(migration.read_text())
 c.execute('insert into supabase_migrations.schema_migrations(version,name,statements) values(%s,%s,%s)',('20261009000100','phase_08_outlook_inbound',[migration.read_text()]))
 assert {cid:{t:rows(t,int(cid)) for t in ts} for cid,ts in protected.items()}==protected
 assert {t:rows(t,585) for t in asana}==asana
 counts={t:c.execute('select count(*) from public.'+t).fetchone()[0] for t in ('outlook_inbound_messages','outlook_inbound_conversations','outlook_inbound_checkpoints','outlook_inbound_sync_events')}
 assert not any(counts.values())
(OUT/'protected_asana_before.json').write_text(json.dumps(asana,indent=2)+'\n')
(OUT/'migration.json').write_text(json.dumps({'version':'20261009000100','sha256':hashlib.sha256(migration.read_bytes()).hexdigest(),'protected_cases_unchanged':[424,584,585],'inbound_counts':counts},indent=2)+'\n')
print('Inbound staging migration applied; zero inbound objects; protected cases unchanged.')
