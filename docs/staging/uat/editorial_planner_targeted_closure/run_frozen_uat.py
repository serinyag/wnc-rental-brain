import sys,json,time,hashlib
from pathlib import Path
from datetime import datetime,timezone
from dataclasses import asdict
ROOT=Path('/Users/serinya/Documents/WNC Rental Automation')
sys.path.insert(0,str(ROOT))
from tools.staging_uat import run_real_model_governed_drafting_uat as uat
from tools.staging_calibration.run_operator_calibration import build_client
client=build_client(ROOT/'Staging Authentications.txt',timeout_seconds=90)
assert client.config.base_url.rstrip('/')=='https://wnc-rental-brain-staging.onrender.com'
original=client.request
requests=[]
audits={}
audit_path=ROOT/'docs/staging/uat/editorial_planner_targeted_closure'/f'{sys.argv[1]}_planner_audit.json'
def guarded(method,path,payload=None):
 allowed_get=path=='/healthz' or (path.startswith('/api/operator/cases/') and path.rsplit('/',1)[-1].isdigit())
 allowed_post=path=='/api/operator/cases' or (path.startswith('/api/operator/cases/') and path.rsplit('/',1)[-1] in {'inquiry-intake','inquiry-waiting','reconcile','raw-evidence','structured-observations','generate'})
 assert (method=='GET' and allowed_get) or (method=='POST' and allowed_post),(method,path)
 requests.append({'method':method,'path':path})
 try:
  response=original(method,path,payload)
  case=response.get('case',{})
  for event in case.get('orchestration_snapshot',{}).get('workflow_events',[]):
   data=event.get('structured_payload',{})
   if data.get('editorial_content_plan'):
    audits[str(event['workflow_event_id'])]={'rental_case_id':event['rental_case_id'],'event_type':event['event_type_code'],**data}
  if audits:audit_path.write_text(json.dumps(list(audits.values()),indent=2,ensure_ascii=False)+'\n')
  return response
 except Exception as exc:
  requests[-1]['error']=str(exc)
  requests[-1]['diagnostics']=getattr(exc,'error_payload',{})
  raise
client.request=guarded
health=client.get_health()
assert health['environment']=='staging' and health['status']=='ok'
assert health['providers']=={'outlook':'configured_draft_only','asana':'configured_but_disabled'}
scenarios=uat.scenarios()
manifest=json.loads((ROOT/'docs/staging/uat/autonomous_remediation/frozen_manifest.json').read_text())
assert hashlib.sha256(json.dumps([asdict(s) for s in scenarios],sort_keys=True).encode()).hexdigest()==manifest['scenario_sha256']
run_slug='editorial-targeted-closure-'+sys.argv[1]+'-'+time.strftime('%Y%m%d-%H%M%S',time.gmtime())
path=ROOT/'docs/staging/uat/editorial_planner_targeted_closure'/f'{sys.argv[1]}_results.json'
result={'generated_at':datetime.now(timezone.utc).isoformat(),'run_slug':run_slug,'baseline':{'git_commit':uat._commit(),'render_commit':sys.argv[2],'provider':uat.REAL_PROVIDER,'model':uat.REAL_MODEL,'health':health,'scenario_count':13,'synthetic_only':True,'approval_or_execution_calls':0},'results':[],'request_log':requests}
for scenario in scenarios:
 print('RUN',scenario.scenario_id,flush=True)
 item=uat._run_scenario(client,scenario,run_slug)
 result['results'].append(item)
 path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
 print('DONE',scenario.scenario_id,[(t['turn_number'],bool(t.get('draft',{}).get('draft_revision')),t.get('failure')) for t in item['turns']],item['failures'],flush=True)
print('RESULT',path,flush=True)
