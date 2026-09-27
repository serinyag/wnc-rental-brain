"""Recover one completed generation from a saved read-only snapshot, retaining raw evidence."""
import json,hashlib,sys
from pathlib import Path
from datetime import datetime,timezone
p=Path(__file__).resolve().parent;root=p.parents[3];sys.path.insert(0,str(root))
from tools.staging_uat.run_real_model_governed_drafting_uat import _draft_state,_snapshot_summary
path=p/'cycle2_results.json';data=json.loads(path.read_text())
assert len(data['results'])==13 and sum(len(x['turns']) for x in data['results'])==21
if data.get('capture_recovery'):
 print('Recovery already recorded.');raise SystemExit(0)
case_result=next(x for x in data['results'] if x['rental_case_id']==508)
turn=case_result['turns'][1];assert turn['failure']=='Operator request timed out after 90 seconds.'
records=[x for x in data['request_log'] if '/508' in x['path']]
failed=next(i for i,x in enumerate(records) if x.get('error'))
assert records[failed]['method']=='GET' and records[failed-1]['path'].endswith('/mailbox/generate') and not records[failed-1].get('error')
recovery=json.loads((p/'cycle2_capture_recovery_508.json').read_text());case=recovery['snapshot']['case'];o=case['orchestration_snapshot']
latest_client=next(b['raw_evidence'] for b in case['evidence_bundles'] if b['raw_evidence'] and b['source_record']['sender_actor_type']=='client')
assert latest_client['body']==turn['incoming_message']['body']
events=[e for e in o['workflow_events'] if e['event_type_code']=='governed_client_response_draft_generated' and e['workflow_event_id']>latest_client['workflow_event_id']]
assert len(events)==1;event=events[0];v=event['structured_payload'];assert v['provider_response_status']=='completed'
report={'title':'Provider-free capture recovery from persisted generation event','lines':[f"Draft revision id: {v['draft_revision_id']}",f"Workflow action id: {v['workflow_action_id']}",f"Approval request id: {v['approval_request_id']}"]}
draft=_draft_state(case,{'report':report});r=draft['draft_revision'];assert r['source_case_revision']==3 and r['is_current']
assert draft['approval_request']['status']=='open';assert not o['execution_attempts']
raw=path.read_bytes();backup=p/'cycle2_results_raw.json';assert not backup.exists();backup.write_bytes(raw)
turn['draft']=draft;turn['generation_report']=report;turn['after_generation']=_snapshot_summary(case)
turn['capture_recovery']={'provider_free':True,'generation_event_id':event['workflow_event_id'],'client_message_event_id':latest_client['workflow_event_id'],'captured_at':recovery['captured_at'],'source':'cycle2_capture_recovery_508.json','original_timeout_retained':True}
data['capture_recovery']={'mode':'Offline reporting correction using one provider-free GET; no new generation, approval or execution','raw_results_file':backup.name,'raw_sha256':hashlib.sha256(raw).hexdigest(),'recovered_turn':'UAT-006/2','recorded_at':datetime.now(timezone.utc).isoformat()}
path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
print('Recovered exactly UAT-006 turn 2 from its completed generation event; original timeout retained.')
