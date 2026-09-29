"""Resume only frozen cases whose initial CREATE failed before any turn ran.

No accepted draft is regenerated. Keep the original result bytes and errors.
This is transport recovery within the existing deployed pass, not a new model
iteration or implementation pass.
"""
import json,sys,hashlib
from pathlib import Path
from dataclasses import asdict
root=Path('/Users/serinya/Documents/WNC Rental Automation');sys.path.insert(0,str(root))
from tools.staging_uat import run_real_model_governed_drafting_uat as uat
from tools.staging_calibration.run_operator_calibration import build_client
p=Path(__file__).resolve().parent;slug=sys.argv[1];path=p/f'{slug}_results.json'
raw=path.read_bytes();result=json.loads(raw);assert len(result['results'])==13
assert not (p/f'{slug}_results_raw.json').exists(),'Recovery already started; inspect saved evidence before resuming.'
failed=[case for case in result['results'] if not case['turns'] and case['failures']]
assert failed and all(not case.get('rental_case_id') and all(x['stage']=='case_setup' for x in case['failures']) for case in failed)
assert all('HTTP 502' in x['reason'] for case in failed for x in case['failures'])
assert sum(x['method']=='POST' and x['path'].endswith('/generate') for x in result['request_log'])==sum(len(c['turns']) for c in result['results']), 'Inspect any uncertain generation before recovery'
scenarios=uat.scenarios();manifest=json.loads((p/'frozen_manifest.json').read_text())
assert hashlib.sha256(json.dumps([asdict(s) for s in scenarios],sort_keys=True).encode()).hexdigest()==manifest['scenario_sha256']
(p/f'{slug}_results_raw.json').write_bytes(raw)
client=build_client(root/'Staging Authentications.txt',timeout_seconds=90)
assert client.config.base_url.rstrip('/')=='https://wnc-rental-brain-staging.onrender.com'
original=client.request;logs=[];audit_path=p/f'{slug}_planner_audit.json';audits=json.loads(audit_path.read_text())
def guarded(method,path,payload=None):
 allowed_get=path=='/healthz' or (path.startswith('/api/operator/cases/') and path.rsplit('/',1)[-1].isdigit())
 allowed_post=path=='/api/operator/cases' or (path.startswith('/api/operator/cases/') and path.rsplit('/',1)[-1] in {'inquiry-intake','inquiry-waiting','reconcile','raw-evidence','structured-observations','generate'})
 assert (method=='GET' and allowed_get) or (method=='POST' and allowed_post)
 logs.append({'method':method,'path':path,'transport_recovery':True})
 response=original(method,path,payload)
 for event in response.get('case',{}).get('orchestration_snapshot',{}).get('workflow_events',[]):
  data=event.get('structured_payload',{})
  if data.get('editorial_content_plan') and not any(a.get('draft_revision_id')==data.get('draft_revision_id') for a in audits):
   audits.append({'rental_case_id':event['rental_case_id'],'event_type':event['event_type_code'],**data})
 audit_path.write_text(json.dumps(audits,indent=2,ensure_ascii=False)+'\n')
 return response
client.request=guarded
h=client.get_health();assert h['environment']=='staging' and h['status']=='ok'
assert h['providers']=={'outlook':'configured_draft_only','asana':'configured_but_disabled'}
recovered=[]
for case in failed:
 scenario=next(s for s in scenarios if s.scenario_id==case['scenario_id'])
 print('RECOVER UNRUN',scenario.scenario_id,flush=True)
 item=uat._run_scenario(client,scenario,result['run_slug']+'-transport-recovery')
 recovered.append(item);(p/f'{slug}_transport_recovery.json').write_text(json.dumps({'health':h,'results':recovered,'request_log':logs},indent=2,ensure_ascii=False)+'\n')
 assert len(item['turns'])==len(scenario.turns) and all(t.get('draft',{}).get('draft_revision') for t in item['turns'])
 item['transport_recovery']={'initial_failure':'HTTP 502 during case creation; no turn or generation ran','raw_results_sha256':hashlib.sha256(raw).hexdigest(),'repeated_generation':False,'possible_orphan_setup_case':'Original create outcome was unknown; it received no client turns or generation requests. No records were deleted.'}
 result['results'][result['results'].index(case)]=item
result['request_log']+=logs
result['transport_recovery']={'original_results_file':f'{slug}_results_raw.json','raw_sha256':hashlib.sha256(raw).hexdigest(),'recovered_scenarios':[c['scenario_id'] for c in recovered]}
path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print('Recovered',len(recovered),'previously unrun cases without repeating any accepted generation.',flush=True)
