"""Real PostgreSQL persistence and application flow; local DB, rollback, fake HTTP."""
import sys,json
from pathlib import Path
from dataclasses import asdict
from unittest.mock import patch
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root))
import psycopg
from provider_free_fixture import service_for,create_candidate,SyntheticProvider
from tools.phase_08_workflow.outlook_action_contract import validate_outlook_action
from tools.phase_08_workflow.test_console_service import TestConsoleError
from tools.phase_08_workflow.execution_runtime import execute_workflow_action
from tools.phase_08_workflow.execution_types import WorkflowActionExecutionRequest
p=Path(__file__).resolve().parent
with psycopg.connect('postgresql://postgres:postgres@127.0.0.1:54322/postgres') as conn, conn.transaction(force_rollback=True), patch('urllib.request.urlopen',side_effect=AssertionError('HTTP prohibited')):
 for name in ('20260829000100_phase_08_general_governed_client_response_drafting.sql','20260907000100_phase_08_governed_client_response_action_type.sql','20260913000100_phase_08_outlook_canonical_plan_identity.sql'):
  conn.execute((root/'supabase/migrations'/name).read_text())
 service=service_for(conn);cid=create_candidate(service)
 with patch('tools.phase_08_workflow.test_console_service.DeterministicFakeClientResponseProvider',SyntheticProvider):
  report=service.generate_governed_client_response_draft(rental_case_id=cid,use_deterministic_fixture=True)
 assert report.success
 revision=service._list_draft_revisions(cid)[0];aid=revision.workflow_action_id;apid=revision.approval_request_id
 readiness=service.inspect_governed_outlook_send_readiness(rental_case_id=cid,workflow_action_id=aid);assert readiness.success
 assert service.approve_request(rental_case_id=cid,approval_request_id=apid).success
 snapshot=service._require_case_snapshot(cid);action=snapshot.find_workflow_action(aid)
 assert action.status=='ready_to_execute'
 canonical=validate_outlook_action(action)
 projected=service._project_governed_outlook_execution_action(snapshot,action=action)
 assert projected.structured_payload==canonical.to_payload()
 assert service.execute_action(rental_case_id=cid,workflow_action_id=aid,execution_mode='success').success
 snapshot=service._require_case_snapshot(cid);attempt=snapshot.execution_attempts[0]
 assert len(snapshot.execution_attempts)==1 and attempt.status=='succeeded' and attempt.external_reference
 assert snapshot.find_workflow_action(aid).status=='succeeded'
 try:service.execute_action(rental_case_id=cid,workflow_action_id=aid,execution_mode='success')
 except TestConsoleError as e:replay=e.failure_code
 else:raise AssertionError('Application replay was not blocked')
 # Independently prove the shared execution runtime's replay guard too.
 registry=service._build_execution_registry(action=action,execution_mode='success',provider_action=projected,outlook_pre_send_validator=service._validate_governed_outlook_pre_send)
 replay_runtime=execute_workflow_action(service.orchestration_repository,WorkflowActionExecutionRequest(rental_case_id=cid,workflow_action_id=aid,actor_reference='synthetic-test',started_at=service.now()),adapter_registry=registry,now=service.now)
 assert replay_runtime.failure_codes==('action_already_succeeded',)
 assert not registry.resolve('outlook').delegate.transport.calls
 assert len(service._require_case_snapshot(cid).execution_attempts)==1
 (p/'database_simulation.json').write_text(json.dumps({'environment':'local PostgreSQL with staging fixture runtime','transaction':'rolled back','generated_through_normal_service':True,'readiness':asdict(readiness),'canonical':canonical.to_payload(),'execution_attempt':asdict(attempt),'application_replay':replay,'runtime_replay':replay_runtime.failure_codes,'attempt_count':1,'real_provider_calls':0},indent=2,default=str)+'\n')
print('Local PostgreSQL full lifecycle PASS; success persisted, replay blocked; transaction rolled back.')
