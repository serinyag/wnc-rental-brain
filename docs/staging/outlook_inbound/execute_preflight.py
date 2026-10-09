"""One explicitly human-authorized, read-only hosted Inbox preflight. No retries."""
import json,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from tools.staging_calibration.run_operator_calibration import build_client
OUT=Path(__file__).parent
client=build_client(ROOT/'Staging Authentications.txt',timeout_seconds=180)
health=client.get_health()
assert health['environment']=='staging' and health['status']=='ok'
assert health['providers']=={'asana':'configured_but_disabled','outlook':'configured_draft_only'}
assert health['application']['metrics']['outlook_inbound_gate']=='disabled'
assert health['application']['metrics']['outlook_inbound_preflight_gate']=='enabled'
(OUT/'health_deployed.json').write_text(json.dumps(health,indent=2)+'\n')
with (OUT/'preflight_started.json').open('x') as f:json.dump({'started_at':datetime.now(timezone.utc).isoformat(),'authorization':'Human explicitly authorized bounded staging read-only Graph preflight; no ingestion, send or permission change'},f)
try:
 result=client.request('POST','/api/operator/outlook-inbound/preflight',{})
except Exception as exc:
 (OUT/'preflight_error.json').write_text(json.dumps({'type':type(exc).__name__,'error':str(exc),'diagnostics':getattr(exc,'error_payload',None)},indent=2)+'\n');raise
(OUT/'preflight.json').write_text(json.dumps(result,indent=2)+'\n')
assert result['read_only'] and result['ingested']==0 and not result['checkpoint_persisted']
print(json.dumps(result,indent=2))
