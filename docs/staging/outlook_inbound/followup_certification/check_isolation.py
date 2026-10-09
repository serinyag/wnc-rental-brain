"""Read-only staging isolation verification; no provider calls."""
import json,sys
from pathlib import Path
import psycopg
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from tools.phase_05_search.semantic_common import load_env_value
assert load_env_value('SUPABASE_PROJECT_REF')=='mspcopnsbounmdpivkvq'
baseline=json.loads((ROOT/'docs/staging/outlook_reconciled_closure/raw_after.json').read_text())
baseline['585']=json.loads((ROOT/'docs/staging/outlook_inbound/protected_asana_before.json').read_text())
with psycopg.connect(host='db.mspcopnsbounmdpivkvq.supabase.co',dbname='postgres',user='postgres',password=load_env_value('SUPABASE_DB_PASSWORD'),sslmode='require',connect_timeout=15) as conn:
 conn.execute('set transaction isolation level repeatable read, read only')
 for cid,tables in baseline.items():
  for table,rows in tables.items():
   actual=conn.execute(f"select coalesce(json_agg(row_to_json(r) order by r.id),'[]') from public.{table} r where rental_case_id=%s",(int(cid),)).fetchone()[0]
   assert actual==rows,(cid,table,'protected lineage changed')
 counts={t:conn.execute('select count(*) from public.'+t).fetchone()[0] for t in ('outlook_inbound_messages','outlook_inbound_conversations','outlook_inbound_checkpoints','outlook_inbound_sync_events')}
result={'inbound_counts':counts,'protected_cases_unchanged':[424,584,585]}
(Path(__file__).parent/'isolation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
