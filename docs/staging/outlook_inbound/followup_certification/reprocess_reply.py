"""One explicit source-3105 remediation using existing governed candidate intake."""
import json,sys
from pathlib import Path
from datetime import datetime,timezone
import psycopg
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from tools.phase_05_search.semantic_common import load_env_value
from tools.staging_calibration.run_operator_calibration import build_client
from tools.phase_08_workflow.outlook_inbound import OutlookInboundConfig
from tools.phase_08_workflow.outlook_inbound_service import reprocess_quarantined_reply
from unittest.mock import patch
P=Path(__file__).parent
before=json.loads((P/'after_followup.json').read_text())
m=next(m for m in before['messages'] if m['source_record_id']==3105)
assert m['rental_case_id']==586 and m['association_basis']=='exact_provider_conversation'
assert load_env_value('SUPABASE_PROJECT_REF')=='mspcopnsbounmdpivkvq'
h=build_client(ROOT/'Staging Authentications.txt',timeout_seconds=180).get_health()
assert h['environment']=='staging' and h['status']=='ok' and h['application']['metrics']['outlook_inbound_gate']=='enabled'
assert h['providers']=={'asana':'configured_but_disabled','outlook':'configured_draft_only'}
config=OutlookInboundConfig('Serinya@whennaturecalls.nl','Serinya@whennaturecalls.nl','2026-10-09T09:02:18Z',('serinya@whennaturecalls.nl',),'SYNTHETIC TEST — WNC Outlook inbound certification',True)
with (P/'reprocessing_started.json').open('x') as f:json.dump({'source_id':3105,'case_id':586,'started_at':datetime.now(timezone.utc).isoformat(),'purpose':'Preserve original quarantine; append governed timing candidate extracted above verified Outlook reply boundary'},f)
with psycopg.connect(host='db.mspcopnsbounmdpivkvq.supabase.co',dbname='postgres',user='postgres',password=load_env_value('SUPABASE_DB_PASSWORD'),sslmode='require',connect_timeout=15,autocommit=True) as c:
 with patch('urllib.request.urlopen',side_effect=AssertionError('Provider HTTP forbidden')):
  r=reprocess_quarantined_reply(c,config,m['message_id'])
  (P/'reprocessing_result.json').write_text(json.dumps(r,indent=2)+'\n')
  repeat=reprocess_quarantined_reply(c,config,m['message_id'])
  assert repeat==r
  (P/'reprocessing_repeat.json').write_text(json.dumps(repeat,indent=2)+'\n')
print(json.dumps(r))
