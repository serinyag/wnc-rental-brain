"""One normal-path staging Inbox page; stop for reconciliation on any error."""
import json,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from tools.staging_calibration.run_operator_calibration import build_client
c=build_client(ROOT/'Staging Authentications.txt',timeout_seconds=180)
h=c.get_health()
assert h['environment']=='staging' and h['status']=='ok'
assert h['providers']=={'asana':'configured_but_disabled','outlook':'configured_draft_only'}
assert h['application']['metrics']['outlook_inbound_gate']=='enabled'
assert h['application']['metrics']['outlook_inbound_preflight_gate']=='disabled'
p=Path(__file__).parent/('sync_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'.json')
with p.open('x') as f:json.dump({'status':'started','authorization':'Autonomous synthetic inbound certification; human confirmed same-conversation follow-up sent'},f)
try:r=c.request('POST','/api/operator/outlook-inbound/sync',{})
except Exception as e:
 r={'status':'uncertain_or_stopped','error':str(e),'details':getattr(e,'error_payload',None)}
 p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));raise SystemExit(1)
p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
