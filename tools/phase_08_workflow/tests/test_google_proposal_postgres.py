"""Roll-back-only normal repository and database fence proofs on localhost."""
from unittest.mock import patch, Mock

import pytest

from tools.phase_08_workflow.tests.test_asana_projection_postgres import pg, ROOT
from tools.phase_08_workflow.tests.test_google_proposal import FakeGoogle, harness
from tools.phase_08_workflow.google_proposal import prepare_projection, ADAPTER, binding
from tools.phase_08_workflow.google_proposal_adapter import GoogleProposalAdapter
from tools.phase_08_workflow.execution_runtime import execute_workflow_action, ExecutionAdapterRegistry
from tools.phase_08_workflow.execution_types import WorkflowActionExecutionRequest
from tools.phase_08_workflow.test_console_service import TestConsoleService, TestConsoleConfig


@pytest.fixture
def google_pg(pg):
    conn, repo, cid, *_ = pg
    conn.execute((ROOT/'supabase/migrations/20261010000100_google_proposal_projection_fences.sql').read_text())
    _, provider, local = harness()
    adapter = GoogleProposalAdapter(local.config, provider, repo, local.runtime)
    def prepare():
        return prepare_projection(repo, rental_case_id=cid, folder_id=adapter.config.folder_id,
                                  provider_identity=adapter.config.provider_identity)
    def execute(action):
        return execute_workflow_action(repo, WorkflowActionExecutionRequest(cid, action.workflow_action_id, 'synthetic_operator'),
            adapter_registry=ExecutionAdapterRegistry({ADAPTER: adapter}))
    return conn, repo, cid, provider, adapter, prepare, execute


def test_postgres_document_binding_survives_service_restart_update_and_replay(google_pg):
    conn, repo, cid, provider, adapter, prepare, execute = google_pg
    assert execute(prepare()).action_status_after == 'succeeded'
    conn.execute('update public.rental_cases set case_revision=case_revision+1 where id=%s', (cid,))
    conn.execute("update public.rental_case_facts set value_payload='30'::jsonb where rental_case_id=%s and field_code='guest_count'", (cid,))
    assert execute(prepare()).action_status_after == 'succeeded'
    assert execute(prepare()).already_succeeded_idempotently
    assert binding(repo.load_case_snapshot(cid))['document_id'] == 'doc_001'
    assert provider.mutations == [('create', 'doc_001'), ('update', 'doc_001')]


def test_postgres_concurrent_projection_fenced_and_action_immutable(google_pg):
    conn, repo, cid, provider, adapter, prepare, execute = google_pg
    action = prepare()
    with pytest.raises(Exception, match='google_proposal_action_immutable'), conn.transaction():
        conn.execute("update public.workflow_actions set structured_payload='{}'::jsonb where id=%s", (action.workflow_action_id,))
    assert repo.start_workflow_action_execution(WorkflowActionExecutionRequest(cid, action.workflow_action_id, 'operator')).execution_attempt_id
    conn.execute('update public.rental_cases set case_revision=case_revision+1 where id=%s', (cid,))
    newer = prepare()
    with pytest.raises(Exception, match='google_proposal_requires_reconciliation'), conn.transaction():
        repo.start_workflow_action_execution(WorkflowActionExecutionRequest(cid, newer.workflow_action_id, 'operator'))
    assert not provider.mutations


def test_postgres_folder_and_oauth_application_identity_are_immutable(google_pg):
    conn, repo, cid, provider, adapter, prepare, execute = google_pg
    assert execute(prepare()).action_status_after == 'succeeded'
    conn.execute('update public.rental_cases set case_revision=case_revision+1 where id=%s', (cid,))
    other = prepare_projection(repo, rental_case_id=cid, folder_id='other_folder', provider_identity=adapter.config.provider_identity)
    with pytest.raises(Exception, match='google_proposal_scope_immutable'), conn.transaction():
        repo.start_workflow_action_execution(WorkflowActionExecutionRequest(cid, other.workflow_action_id, 'operator'))
    assert len(provider.documents) == 1


def test_postgres_service_registry_execute_and_observation_audit(google_pg):
    conn, repo, cid, provider, adapter, prepare, execute = google_pg
    service = TestConsoleService(query_runner=repo.query_runner,
        config=TestConsoleConfig(runtime=adapter.runtime, allow_real_providers=True))
    with patch.object(service, '_load_test_case_metadata', return_value=None), \
         patch('tools.phase_08_workflow.google_proposal_adapter.GoogleProposalConfig.from_env', return_value=adapter.config), \
         patch('tools.phase_08_workflow.google_proposal_adapter.GoogleTransport', return_value=provider):
        prepared = service.prepare_google_proposal(rental_case_id=cid)
        assert not prepared['provider_called']
        result = service.execute_action(rental_case_id=cid, workflow_action_id=prepared['workflow_action_id'], execution_mode='real')
        assert result.success, result
        assert service.observe_google_proposal(rental_case_id=cid, workflow_action_id=prepared['workflow_action_id'])['status'] == 'MATCHES_PROJECTION'
    assert conn.execute("select count(*) from public.workflow_events where rental_case_id=%s and event_type_code='google_proposal_observed'", (cid,)).fetchone()[0] == 1


def test_http_google_routes_require_staging_authentication():
    from tools.phase_08_workflow.tests.test_test_console_app import _FakeService, call_app, _basic_auth_header
    from tools.phase_08_workflow.test_console import TestConsoleApp
    from tools.runtime_environment import AppRuntimeConfig, AppEnvironment
    service = _FakeService(config=TestConsoleConfig(runtime=AppRuntimeConfig(app_env=AppEnvironment.STAGING,
        staging_basic_auth_username='operator', staging_basic_auth_password='test-password')))
    service.prepare_google_proposal = Mock(return_value={'provider_called': False})
    service.observe_google_proposal = Mock(return_value={'business_truth_changed': False})
    app = TestConsoleApp(service)
    for path, method in (('/api/operator/cases/1/google-proposal', service.prepare_google_proposal),
                         ('/api/operator/cases/1/actions/2/observe-google', service.observe_google_proposal)):
        assert call_app(app, 'POST', path)[0] == '401 Unauthorized'
        method.assert_not_called()
        assert call_app(app, 'POST', path, headers=_basic_auth_header('operator', 'test-password'))[0] == '200 OK'
        method.assert_called_once()
