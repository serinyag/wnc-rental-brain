"""Local PostgreSQL persistence/fence tests; fixtures and DDL roll back."""
import json
import os
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import pytest

from tools.phase_05_chunking.generate_pilot import _wrap_supabase_json_query, _drain_cursor_results
from tools.phase_08_workflow.orchestration_repository import SupabaseWorkflowOrchestrationRepository
from tools.phase_08_workflow.asana_projection import prepare_projection
from tools.phase_08_workflow.execution_runtime import execute_workflow_action, ExecutionAdapterRegistry
from tools.phase_08_workflow.execution_types import WorkflowActionExecutionRequest
from tools.phase_08_workflow.tests.test_asana_projection import harness, synthetic_repo, NOW, ADAPTER

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def pg():
    dsn = os.environ.get("WNC_TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("requires explicitly selected local PostgreSQL")
    assert urlparse(dsn).hostname in {"127.0.0.1", "localhost", "::1"}
    import psycopg
    from unittest.mock import patch
    with psycopg.connect(dsn) as conn, conn.transaction(force_rollback=True), patch("urllib.request.urlopen", side_effect=AssertionError("No providers")):
        conn.execute((ROOT / "supabase/migrations/20261003000200_phase_08_asana_projection_fences.sql").read_text())
        def runner(sql, *, expect_json):
            cur = conn.execute(_wrap_supabase_json_query(sql) if expect_json else sql)
            value = json.loads(cur.fetchone()[0] or "[]") if expect_json else None
            _drain_cursor_results(cur)
            return {"rows": value} if expect_json else None
        repo = SupabaseWorkflowOrchestrationRepository(query_runner=runner)
        fixture = synthetic_repo()
        c = fixture.rental_cases[1]
        cid = conn.execute("""insert into public.rental_cases(case_reference_code,lifecycle_state,rental_type_code,
             client_account_ref,active_event_start,active_event_end) values (%s,%s,%s,%s,%s,%s) returning id""",
            ("RC-" + str(uuid4().int)[:20], c.lifecycle_state, c.rental_type_code, c.client_account_ref,
             c.active_event_start, c.active_event_end)).fetchone()[0]
        for a in fixture.workflow_actions[1]:
            repo.create_workflow_action(replace(a, rental_case_id=cid))
        for f in fixture.rental_case_facts[1]:
            conn.execute("""insert into public.rental_case_facts(rental_case_id,field_code,domain_code,value_payload,
                source_reference,established_case_revision) values (%s,%s,%s,%s::jsonb,%s,0)""",
                (cid, f.field_code, f.domain_code, json.dumps(f.value_payload), f.source_reference))
        _, transport, adapter = harness(repo)
        def prep():
            return prepare_projection(repo, rental_case_id=cid, workspace_gid="111", project_gid="222", now=NOW)
        def run(action):
            return execute_workflow_action(repo, WorkflowActionExecutionRequest(cid, action.workflow_action_id, "synthetic_operator"),
                adapter_registry=ExecutionAdapterRegistry({ADAPTER: adapter}), now=lambda: NOW)
        yield conn, repo, cid, transport, adapter, prep, run


def test_postgres_create_update_and_replay_persist_bindings(pg):
    conn, repo, cid, transport, adapter, prep, run = pg
    action = prep()
    assert run(action).action_status_after == "succeeded"
    assert run(prep()).already_succeeded_idempotently
    conn.execute("update public.rental_cases set case_revision=case_revision+1 where id=%s", (cid,))
    conn.execute("update public.rental_case_facts set value_payload='30'::jsonb where rental_case_id=%s and field_code='guest_count'", (cid,))
    assert run(prep()).action_status_after == "succeeded"
    snap = repo.load_case_snapshot(cid)
    assert len([a for a in snap.execution_attempts if a.adapter_code == ADAPTER]) == 2
    assert snap.execution_attempts[-1].response_snapshot["bindings"]["master"]["gid"] == "1000"
    assert len(transport.tasks) == 4
    assert "Guests: 30" in transport.tasks["1000"]["notes"]


def test_postgres_attempt_fence_blocks_second_started_action(pg):
    conn, repo, cid, transport, adapter, prep, run = pg
    action = prep()
    assert repo.start_workflow_action_execution(WorkflowActionExecutionRequest(cid, action.workflow_action_id, "operator")).execution_attempt_id
    conn.execute("update public.rental_cases set case_revision=case_revision+1 where id=%s", (cid,))
    next_action = prep()
    with pytest.raises(Exception, match="asana_projection_requires_reconciliation"), conn.transaction():
        repo.start_workflow_action_execution(WorkflowActionExecutionRequest(cid, next_action.workflow_action_id, "operator"))
    assert len(repo.load_case_snapshot(cid).execution_attempts) == 1
    assert not transport.calls


def test_postgres_immutable_contract_and_scope(pg):
    conn, repo, cid, transport, adapter, prep, run = pg
    action = prep()
    with pytest.raises(Exception, match="asana_projection_action_immutable"), conn.transaction():
        conn.execute("update public.workflow_actions set structured_payload='{}'::jsonb where id=%s", (action.workflow_action_id,))
    assert run(action).action_status_after == "succeeded"
    conn.execute("update public.rental_cases set case_revision=case_revision+1 where id=%s", (cid,))
    other = prepare_projection(repo, rental_case_id=cid, workspace_gid="111", project_gid="333", now=NOW)
    with pytest.raises(Exception, match="asana_projection_scope_immutable"), conn.transaction():
        repo.start_workflow_action_execution(WorkflowActionExecutionRequest(cid, other.workflow_action_id, "operator"))


def test_postgres_ambiguous_outcome_is_not_retried(pg):
    conn, repo, cid, transport, adapter, prep, run = pg
    action = prep()
    transport.next_failure = "timeout_after_accept"
    assert run(action).action_status_after == "failed"
    assert repo.load_case_snapshot(cid).execution_attempts[-1].failure_code == "adapter_outcome_ambiguous"
    conn.execute("update public.rental_cases set case_revision=case_revision+1 where id=%s", (cid,))
    assert run(prep()).failure_codes == ("adapter_outcome_ambiguous",)
    assert len(transport.tasks) == 1
    assert adapter.observe(action=action)["status"] == "review_required"
    assert len(repo.load_case_snapshot(cid).execution_attempts) == 1


def test_service_prepare_real_execution_mapping_and_observation_audit(pg):
    from unittest.mock import patch
    from tools.phase_08_workflow.test_console_service import TestConsoleService, TestConsoleConfig
    conn, repo, cid, transport, adapter, prep, run = pg
    service = TestConsoleService(query_runner=repo.query_runner,
        config=TestConsoleConfig(runtime=adapter.runtime, allow_real_providers=True))
    with patch.object(service, "_load_test_case_metadata", return_value=None), \
         patch("tools.phase_08_workflow.asana_adapter.AsanaAdapterConfig.from_env", return_value=adapter.config), \
         patch("tools.phase_08_workflow.asana_adapter.UrllibAsanaTransport", return_value=transport):
        prepared = service.prepare_asana_rental_projection(rental_case_id=cid)
        assert prepared["provider_called"] is False and not transport.calls
        action_id = prepared["workflow_action_id"]
        result = service.execute_action(rental_case_id=cid, workflow_action_id=action_id, execution_mode="real")
        assert result.success, result
        observation = service.observe_asana_rental_projection(rental_case_id=cid, workflow_action_id=action_id)
        assert observation["status"] == "matches_projection"
        assert conn.execute("select count(*) from public.workflow_events where rental_case_id=%s and event_type_code='asana_projection_observed'", (cid,)).fetchone()[0] == 1


def test_http_projection_routes_require_staging_authentication():
    from unittest.mock import Mock
    from tools.phase_08_workflow.tests.test_test_console_app import _FakeService, call_app, _basic_auth_header
    from tools.phase_08_workflow.test_console import TestConsoleApp
    from tools.phase_08_workflow.test_console_service import TestConsoleConfig
    from tools.runtime_environment import AppRuntimeConfig, AppEnvironment
    service = _FakeService(config=TestConsoleConfig(runtime=AppRuntimeConfig(app_env=AppEnvironment.STAGING,
        staging_basic_auth_username="operator", staging_basic_auth_password="test-password")))
    service.prepare_asana_rental_projection = Mock(return_value={"provider_called": False})
    service.observe_asana_rental_projection = Mock(return_value={"canonical_truth_changed": False})
    app = TestConsoleApp(service)
    for path, method in (("/api/operator/cases/1/asana-projection", service.prepare_asana_rental_projection),
                         ("/api/operator/cases/1/actions/2/observe-asana", service.observe_asana_rental_projection)):
        assert call_app(app, "POST", path)[0] == "401 Unauthorized"
        method.assert_not_called()
        assert call_app(app, "POST", path, headers=_basic_auth_header("operator", "test-password"))[0] == "200 OK"
        method.assert_called_once()
