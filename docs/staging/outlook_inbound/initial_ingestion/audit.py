"""Read-only snapshots of synthetic inbound lineage; never log cursor tokens."""
import json,sys
from pathlib import Path
import psycopg
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from tools.phase_05_search.semantic_common import load_env_value
from tools.phase_08_workflow.inbound_email import evidence_hash
assert load_env_value('SUPABASE_PROJECT_REF')=='mspcopnsbounmdpivkvq'
with psycopg.connect(host='db.mspcopnsbounmdpivkvq.supabase.co',dbname='postgres',user='postgres',password=load_env_value('SUPABASE_DB_PASSWORD'),sslmode='require',connect_timeout=15) as c:
 c.execute('set transaction isolation level repeatable read, read only')
 def rows(sql,args=()):return c.execute('select coalesce(json_agg(row_to_json(r)),\'[]\') from ('+sql+') r',args).fetchone()[0]
 messages=rows('select * from public.outlook_inbound_messages order by retrieved_at')
 for m in messages:
  assert evidence_hash(m['raw_provider_payload'])==m['source_hash']
  assert m['mailbox']=='serinya@whennaturecalls.nl'
 caseids=list({m['rental_case_id'] for m in messages if m['rental_case_id']})
 sourceids=[m['source_record_id'] for m in messages]
 d={'messages':messages,'conversations':rows('select * from public.outlook_inbound_conversations'),
 'checkpoints':rows('select mailbox,folder,initial_since,version,status,last_successful_sync_at from public.outlook_inbound_checkpoints'),
 'sync_events':rows('select * from public.outlook_inbound_sync_events order by id'),
 'cases':rows('select * from public.rental_cases where id=any(%s) order by id',(caseids,)),
 'sources':rows('select * from public.inbound_source_records where id=any(%s) order by id',(sourceids,)),
 'totals':{t:c.execute('select count(*) from public.'+t).fetchone()[0] for t in ('rental_cases','inbound_source_records','inbound_observations','workflow_execution_attempts')}}
 for t in ('inbound_observations','workflow_events','rental_case_facts','workflow_actions'):
  d[t]=rows('select * from public.'+t+' where rental_case_id=any(%s) order by id',(caseids,))
 p=Path(__file__).parent/(sys.argv[1]+'.json')
 with p.open('x') as f:json.dump(d,f,indent=2)
 print(json.dumps({'file':str(p),'messages':len(messages),'cases':caseids,'sources':sourceids,'observations':len(d['inbound_observations']),'facts':len(d['rental_case_facts']),'totals':d['totals'],'checkpoints':d['checkpoints']},indent=2))
