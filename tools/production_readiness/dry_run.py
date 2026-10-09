"""Isolated local synthetic intake load, failure visibility and kill-switch rehearsal."""
import json, time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
import psycopg
from tools.production_readiness.migration_rehearsal import sql, ROOT, OUT, database_seed
from tools.production_readiness.monitor import collect, report
from tools.phase_08_workflow.tests.test_outlook_inbound import adapter, message, CONFIG, Graph
from tools.phase_08_workflow.outlook_inbound import OutlookInboundAdapter
from tools.phase_08_workflow.outlook_inbound_service import sync_page
NAME='wnc_readiness_load'
DSN='postgresql://postgres:postgres@127.0.0.1:54322/'+NAME

def main():
    sql('postgres','create database '+NAME+' template template0;')
    result={'real_provider_calls':0,'real_customer_records':0,'production_changes':0}
    try:
        sql(NAME,'create schema extensions;')
        for p in sorted((ROOT/'supabase/migrations').glob('*.sql')):sql(NAME,'begin;\n'+p.read_text()+'\ncommit;')
        sql(NAME,'begin;\n'+database_seed()+'\ncommit;')
        records=[message('load-'+str(i),'conversation-'+str(i)) for i in range(50)]
        pages=[records[i:i+10] for i in range(0,50,10)]
        def sync(records):
            with psycopg.connect(DSN,autocommit=True) as c: return sync_page(c,adapter(records))
        start=time.monotonic()
        with patch('urllib.request.urlopen',side_effect=AssertionError('Real provider forbidden')):
            # Four concurrent passes of the same 50 messages; mailbox DB lock
            # and provider-message uniqueness must suppress every duplicate.
            with ThreadPoolExecutor(max_workers=4) as pool:
                runs=list(pool.map(sync,pages*4))
            with psycopg.connect(DSN,autocommit=True) as c:
                assert c.execute('select count(*) from public.outlook_inbound_messages').fetchone()[0]==50
                assert c.execute('select count(*) from public.outlook_inbound_conversations').fetchone()[0]==50
                before=c.execute('select version from public.outlook_inbound_checkpoints').fetchone()[0]
                def fail(): raise ValueError('synthetic_checkpoint_failure')
                try:sync_page(c,adapter([message('fault','fault')]),before_checkpoint=fail)
                except ValueError as e: assert str(e)=='synthetic_checkpoint_failure'
                else:raise AssertionError('fault not raised')
                assert c.execute('select version from public.outlook_inbound_checkpoints').fetchone()[0]==before
                assert c.execute('select count(*) from public.outlook_inbound_messages').fetchone()[0]==50
                # Ambiguous authored dates persist quarantine visible to operator.
                sync_page(c,adapter([message('quarantine','quarantine','12 November 2026 or 13 November 2026?')]))
                metrics=collect(c)
                assert metrics['quarantined_observations']>0
                alert=report(metrics,health_ok=True)
                assert any(a['code']=='QUARANTINED_OBSERVATIONS' for a in alert['alerts'])
                graph=Graph([])
                stopped=OutlookInboundAdapter(replace(CONFIG,enabled=False),graph,'fake')
                try:stopped.read_page()
                except ValueError as e:assert str(e)=='inbound_gate_disabled'
                else:raise AssertionError('gate bypass')
                assert not graph.calls
            result.update(status='passed',unique_messages=50,concurrent_workers=4,page_invocations=20,
                suppressed_duplicates=sum(x.get('duplicate',False) for r in runs for x in r['results']),
                checkpoint_failure_rolled_back=True,disabled_gate_provider_calls=0,
                operator_alert=alert,elapsed_seconds=round(time.monotonic()-start,3),
                limit='Local PostgreSQL and fake Graph only; no live quota, AI latency or production throughput certification')
    finally:
        sql('postgres','drop database '+NAME+';')
        result['disposable_database_removed']=True
        (OUT/'dry_run.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
