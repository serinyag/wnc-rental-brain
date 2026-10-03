import json,sys,hashlib
from pathlib import Path
from datetime import datetime,timezone
root=Path('/Users/serinya/Documents/WNC Rental Automation');sys.path.insert(0,str(root))
from tools.staging_calibration.run_operator_calibration import build_client
p=root/'docs/staging/uat/required_realization';slug=sys.argv[1];r=json.loads((p/f'{slug}_results.json').read_text())
c=build_client(root/'Staging Authentications.txt',timeout_seconds=90)
assert c.config.base_url.rstrip('/')=='https://wnc-rental-brain-staging.onrender.com'
h=c.get_health();assert h['environment']=='staging' and h['status']=='ok';assert h['providers']=={'outlook':'configured_draft_only','asana':'configured_but_disabled'}
snapshots=[]
for case in r['results']:
 cid=case['rental_case_id'];assert isinstance(cid,int) and cid>=425
 data=c.get_case(rental_case_id=cid);snapshots.append({'scenario_id':case['scenario_id'],'rental_case_id':cid,'snapshot':data})
(p/f'{slug}_final_snapshots.json').write_text(json.dumps({'checked_at':datetime.now(timezone.utc).isoformat(),'health':h,'cases':snapshots},ensure_ascii=False,indent=2)+'\n')
m=json.loads((p/'frozen_manifest.json').read_text())
for f,digest in m['file_sha256'].items():assert hashlib.sha256((root/f).read_bytes()).hexdigest()==digest,f
print('Provider-free final snapshots saved; health/gates and frozen file hashes pass.')
