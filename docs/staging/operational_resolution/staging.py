"""Bounded case 586 proof. No provider execution; staging DB is pinned."""
import sys,json
from pathlib import Path
from dataclasses import asdict
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'docs/staging/case586_integrated'))
from common import connect,service,client
from tools.phase_08_workflow.operational_resolution import obligation,submit,current_resolutions,resolved_keys,client_results
from tools.phase_08_workflow.context_aware_drafting import derive_resolution_items
OUT=Path(__file__).parent

def save(name,data):
    with (OUT/(name+'.json')).open('x') as f:json.dump(data,f,indent=2,default=str)

def protected(conn):
    baselines=json.loads((ROOT/'docs/staging/outlook_reconciled_closure/raw_after.json').read_text())
    baselines['585']=json.loads((ROOT/'docs/staging/outlook_inbound/protected_asana_before.json').read_text())
    for cid,tables in baselines.items():
        for table,expected in tables.items():
            actual=conn.execute(f"select coalesce(json_agg(row_to_json(r) order by r.id),'[]') from public.{table} r where rental_case_id=%s",(int(cid),)).fetchone()[0]
            assert actual==expected,(cid,table)
    return [424,584,585]

if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='before':
        save('health_before',client().request('GET','/healthz'))
        with connect() as conn:
            conn.execute('set transaction read only')
            s=service(conn);d=s.load_case_detail(586);snap=d.orchestration_snapshot
            assert snap.rental_case.case_revision==3
            assert not snap.execution_attempts
            observed=s._build_observed_field_candidates(d.evidence_bundles)
            contracts={}
            for aid in (1633,1634):
                a=next(a for a in snap.workflow_actions if a.workflow_action_id==aid)
                contracts[aid]=obligation(snap,a,observed_fields=observed)
            save('before',{'snapshot':asdict(snap),'contracts':contracts,'protected':protected(conn)})
            print(json.dumps({'revision':3,'contracts':contracts,'protected':[424,584,585]},indent=2))
    elif mode=='migrate':
        with connect() as conn:
            protected(conn)
            conn.execute((ROOT/'supabase/migrations/20261009000100_phase_08_operational_resolution.sql').read_text())
        save('migration',{'migration':'20261009000100_phase_08_operational_resolution.sql','production':False})
        print('Staging authority migration applied; no case truth changed.')
