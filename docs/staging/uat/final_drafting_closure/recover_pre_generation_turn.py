"""One bounded recovery of a proven pre-generation transport failure.

No case/message reinjection and no repeated accepted/rejected model result.
"""
import sys,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
root=Path('/Users/serinya/Documents/WNC Rental Automation');sys.path.insert(0,str(root))
from tools.staging_uat import run_real_model_governed_drafting_uat as uat
from tools.staging_calibration.run_operator_calibration import build_client
p=Path(__file__).resolve().parent;path=p/'acceptance_results.json';raw=path.read_bytes();result=json.loads(raw)
assert len(result['results'])==13
failed=[(c,t) for c in result['results'] for t in c['turns'] if t.get('failure')]
assert len(failed)==1
case,turn=failed[0];cid=case['rental_case_id'];assert turn['turn_number']==len(case['turns'])
assert turn['failure']=='Operator endpoint returned non-JSON output.'
logs=result['request_log'];case_logs=[x for x in logs if f'/cases/{cid}/' in x['path']]
last_input=max(i for i,x in enumerate(case_logs) if x['path'].endswith('/raw-evidence'))
last=case_logs[last_input:]
assert not any(x['path'].endswith('/generate') for x in last)
errors=[x for x in last if x.get('error')];assert len(errors)==1 and errors[0]['path'].endswith('/inquiry-waiting')
assert sum(x['path'].endswith('/generate') for x in logs)==20
backup=p/'acceptance_results_raw.json';assert not backup.exists(),'Recovery already attempted; do not repeat.'
backup.write_bytes(raw)
audits=json.loads((p/'acceptance_planner_audit.json').read_text());requests=[]
c=build_client(root/'Staging Authentications.txt',timeout_seconds=90)
assert c.config.base_url.rstrip('/')=='https://wnc-rental-brain-staging.onrender.com'
original=c.request
def guarded(method,path,payload=None):
 allowed=(method=='GET' and path in ['/healthz',f'/api/operator/cases/{cid}']) or (method=='POST' and path in [f'/api/operator/cases/{cid}/inquiry-waiting',f'/api/operator/cases/{cid}/reconcile',f'/api/operator/cases/{cid}/mailbox/generate'])
 assert allowed,(method,path)
 requests.append({'method':method,'path':path,'transport_recovery':True})
 (p/'acceptance_transport_recovery.json').write_text(json.dumps({'request_log':requests,'original_result_sha256':hashlib.sha256(raw).hexdigest(),'generation_repeated':False,'stage':'in_progress'},indent=2)+'\n')
 response=original(method,path,payload)
 for event in response.get('case',{}).get('orchestration_snapshot',{}).get('workflow_events',[]):
  data=event.get('structured_payload',{})
  if data.get('editorial_content_plan') and not any(a.get('draft_revision_id')==data.get('draft_revision_id') for a in audits):
   audits.append({'rental_case_id':event['rental_case_id'],'event_type':event['event_type_code'],**data})
 (p/'acceptance_planner_audit.json').write_text(json.dumps(audits,indent=2,ensure_ascii=False)+'\n')
 return response
c.request=guarded
health=c.get_health();assert health['environment']=='staging' and health['status']=='ok'
assert health['providers']=={'outlook':'configured_draft_only','asana':'configured_but_disabled'}
current=c.get_case(rental_case_id=cid)['case']
assert not current['orchestration_snapshot']['execution_attempts']
assert not any(a['rental_case_id']==cid and a['client_generation_payload']['latest_client_message']==turn['incoming_message']['body'] for a in audits)
assert any(b.get('raw_evidence',{}).get('body')==turn['incoming_message']['body'] for b in current['evidence_bundles'] if b.get('raw_evidence'))
for operation in ['waiting','reconcile']:uat._operation(c,operation,cid)
before=c.get_case(rental_case_id=cid)['case']
response=c.generate_governed_client_response_draft(rental_case_id=cid)
after=c.get_case(rental_case_id=cid)['case']
turn['transport_recovery']={'original_failure':turn.pop('failure'),'failed_stage':'inquiry-waiting response decode, before generation','generation_repeated':False}
turn.update(generation_report=response.get('report'),draft=uat._draft_state(after,response),before_generation=uat._snapshot_summary(before),after_generation=uat._snapshot_summary(after))
case.update(final_state=uat._snapshot_summary(after),final_execution_attempts=after['orchestration_snapshot']['execution_attempts'],final_approvals=after['orchestration_snapshot']['approval_requests'])
result['request_log']+=requests
result['transport_recovery']={'turn':f"{case['scenario_id']}/{turn['turn_number']}",'original_results_file':backup.name,'raw_sha256':hashlib.sha256(raw).hexdigest(),'failed_stage':'inquiry-waiting transport response','generation_repeated':False,'case_or_message_reinjected':False}
path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
(p/'acceptance_transport_recovery.json').write_text(json.dumps({'health':health,'request_log':requests,'original_result_sha256':hashlib.sha256(raw).hexdigest(),'generation_repeated':False,'stage':'completed','recovered_revision':turn['draft'].get('draft_revision',{}).get('inquiry_response_draft_revision_id')},indent=2)+'\n')
print('Completed one pre-generation transport recovery; no repeated model call.')
