"""One synthetic staging candidate through unchanged application builders; never approve/execute."""
import sys,json,hashlib,subprocess
from pathlib import Path
from dataclasses import asdict,fields
from unittest.mock import patch
import xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root))
import psycopg
from provider_free_fixture import service_for,create_candidate,SyntheticProvider,RECIPIENT,SUBJECT,BODY
from tools.phase_05_search.semantic_common import load_env_value
from tools.phase_08_workflow.outlook_action_contract import validate_outlook_action,OutlookExecutionInput
from tools.staging_calibration.run_operator_calibration import build_client
p=Path(__file__).resolve().parent
for name in ['focused','phase8','full']:
 suite=ET.parse(p/(name+'.xml')).getroot()[0]
 assert all(int(suite.attrib[k])==0 for k in ['failures','errors','skipped'])
assert json.loads((p/'database_simulation.json').read_text())['runtime_replay']==['action_already_succeeded']
m=json.loads((p/'baseline_manifest.json').read_text())
for f,h in m['file_sha256'].items():assert hashlib.sha256((root/f).read_bytes()).hexdigest()==h
client=build_client(root/'Staging Authentications.txt',timeout_seconds=90)
assert client.config.base_url.rstrip('/')=='https://wnc-rental-brain-staging.onrender.com'
health=client.get_health()
assert health['status']=='ok' and health['environment']=='staging'
assert health['providers']=={'outlook':'configured_draft_only','asana':'configured_but_disabled'}
linked=json.loads((root/'supabase/.temp/linked-project.json').read_text())
assert linked['ref']=='mspcopnsbounmdpivkvq' and linked['name']=='wnc-rental-brain-staging'
assert load_env_value('SUPABASE_PROJECT_REF')==linked['ref']
# Refuse automatic reruns that could create another candidate.
with (p/'candidate_preparation_started.json').open('x') as f:json.dump({'staging_project':linked['ref'],'accepted_commit':m['accepted_implementation']},f)
def history(conn):
 return {table:conn.execute(f"select coalesce(json_agg(row_to_json(r) order by r.id),'[]') from public.{table} r where rental_case_id=424").fetchone()[0]
         for table in ['workflow_actions','rental_case_approval_requests','workflow_execution_attempts','inquiry_response_draft_revisions']}
with psycopg.connect(host='db.mspcopnsbounmdpivkvq.supabase.co',port=5432,dbname='postgres',user='postgres',password=load_env_value('SUPABASE_DB_PASSWORD'),sslmode='require',connect_timeout=15) as conn:
 before=history(conn)
 assert conn.execute('select case_reference_code from public.rental_cases where id=583').fetchone()
 # Only model output is substituted. Real application validation, immutable
 # revision storage, canonical builder and exact approval creation are unchanged.
 with patch('urllib.request.urlopen',side_effect=AssertionError('HTTP providers prohibited')):
  service=service_for(conn);cid=create_candidate(service)
  with patch('tools.phase_08_workflow.test_console_service.DeterministicFakeClientResponseProvider',SyntheticProvider):
   report=service.generate_governed_client_response_draft(rental_case_id=cid,use_deterministic_fixture=True)
  assert report.success
  revisions=service._list_draft_revisions(cid);assert len(revisions)==1
  rev=revisions[0];assert rev.is_current and rev.draft_status=='needs_approval'
  snap=service._require_case_snapshot(cid);assert not snap.execution_attempts
  actions=[a for a in snap.workflow_actions if a.target_adapter_code=='outlook'];assert len(actions)==1
  action=actions[0];value=validate_outlook_action(action)
  assert action.status=='awaiting_approval' and value.draft_revision_id==rev.inquiry_response_draft_revision_id
  approval=snap.find_approval_request(rev.approval_request_id)
  assert approval.status=='open' and approval.target_entity_reference==value.approval_target
  assert rev.subject==SUBJECT and rev.body_text==BODY and rev.recipient_email==RECIPIENT
  assert value.provenance=='deterministic_fixture' and value.graph_message_id is None and value.message_mode=='new'
  assert set(action.structured_payload)=={f.name for f in fields(OutlookExecutionInput)}
  readiness=service.inspect_governed_outlook_send_readiness(rental_case_id=cid,workflow_action_id=action.workflow_action_id)
  assert readiness.success
  assert service._project_governed_outlook_execution_action(snap,action=action).structured_payload==action.structured_payload
  assert conn.execute('select count(*) from public.workflow_actions where idempotency_key=%s',(action.idempotency_key,)).fetchone()[0]==1
  assert conn.execute("select count(*) from public.workflow_actions where structured_payload->>'plan_identity'=%s",(value.plan_identity,)).fetchone()[0]==1
  after=history(conn);assert before==after
  result={'case_id':cid,'revision':asdict(rev),'action':asdict(action),'approval':asdict(approval),'canonical_fields':value.to_payload(),
          'local_readiness':asdict(readiness),'historical_rows_unchanged':True,'zero_attempts':True,'idempotency_collision':False,
          'method':'Unchanged deployed application source and real staging PostgreSQL repository, explicit deterministic synthetic model fixture; no governance substitution; hosted readiness revalidated separately.',
          'provider_calls':0}
 (p/'historical_database_rows_before.json').write_text(json.dumps(before,indent=2,default=str)+'\n')
 (p/'historical_database_rows_after.json').write_text(json.dumps(after,indent=2,default=str)+'\n')
 # Exiting commits the single new lineage; the historical rows were only read.
(p/'fresh_candidate.json').write_text(json.dumps(result,indent=2,default=str)+'\n')
print('Fresh candidate committed:',cid,rev.inquiry_response_draft_revision_id,action.workflow_action_id,approval.approval_request_id)
# Real hosted endpoint checks deployed configuration, including its actual allowlist.
hosted=client.inspect_governed_outlook_send_readiness(rental_case_id=cid,workflow_action_id=action.workflow_action_id)
(p/'hosted_readiness.json').write_text(json.dumps(hosted,indent=2)+'\n')
print('Hosted readiness:',json.dumps(hosted.get('report',{})))
(p/'fresh_final_snapshot.json').write_text(json.dumps(client.get_case(rental_case_id=cid),indent=2)+'\n')
(p/'historical_after.json').write_text(json.dumps(client.get_case(rental_case_id=424),indent=2)+'\n')
(p/'health_after.json').write_text(json.dumps(client.get_health(),indent=2)+'\n')
