"""Real Phase 8 orchestration with a stateful, network-free Asana transport."""
import copy
import json
from dataclasses import replace
from urllib.parse import urlparse, parse_qs
from unittest.mock import patch

import pytest

from tools.runtime_environment import AppRuntimeConfig, AppEnvironment
from tools.phase_08_workflow.asana_adapter import AsanaAdapterConfig, AsanaAmbiguousTransportError
from tools.phase_08_workflow.asana_projection import prepare_projection, build_projection, ADAPTER
from tools.phase_08_workflow.asana_projection_adapter import AsanaProjectionAdapter
from tools.phase_08_workflow.execution_runtime import execute_workflow_action, ExecutionAdapterRegistry
from tools.phase_08_workflow.execution_types import WorkflowActionExecutionRequest
from tools.phase_08_workflow.observation_contracts import RentalCaseFact
from tools.phase_08_workflow.tests.test_asana_adapter import make_case, make_repo, make_asana_action

NOW = "2026-10-03T12:00:00Z"


class FakeAsana:
    def __init__(self):
        self.tasks, self.calls = {}, []
        self.next_failure = None
        self.page_size = 100

    def send_json(self, *, method, url, headers, payload, timeout_seconds):
        parsed = urlparse(url)
        path = parsed.path.removeprefix("/api/1.0")
        self.calls.append({"method": method, "path": path, "payload": copy.deepcopy(payload)})
        failure = self.next_failure if method != "GET" else None
        self.next_failure = None if failure else self.next_failure
        if failure in {429, 400, 503}:
            return failure, json.dumps({"errors": []}), {}
        data = payload.get("data", {})
        if method == "POST":
            gid = str(1000 + len(self.tasks))
            parent = path.split("/")[2] if path.endswith("/subtasks") else None
            task = {**copy.deepcopy(data), "gid": gid, "workspace": {"gid": "111"},
                    "projects": [{"gid": "222"}] if parent is None else [],
                    "parent": {"gid": parent} if parent else None}
            self.tasks[gid] = task
            if failure == "timeout_after_accept":
                raise AsanaAmbiguousTransportError("timeout")
            if failure == "invalid_json_after_accept":
                return 201, "{", {}
            return 201, json.dumps({"data": task}), {}
        if method == "PUT":
            task = self.tasks[path.split("/")[2]]
            task.update(copy.deepcopy(data))
            return 200, json.dumps({"data": task}), {}
        if path == "/projects/222":
            return 200, json.dumps({"data": {"gid": "222", "workspace": {"gid": "111"}, "archived": False}}), {}
        if path.startswith("/projects/") or path.endswith("/subtasks"):
            parent = path.split("/")[2] if path.endswith("/subtasks") else None
            tasks = [t for t in self.tasks.values() if (t.get("parent") or {}).get("gid") == parent]
            offset = int(parse_qs(parsed.query).get("offset", ["0"])[0])
            page = tasks[offset:offset + self.page_size]
            after = offset + self.page_size
            return 200, json.dumps({"data": page, "next_page": {"offset": str(after)} if after < len(tasks) else None}), {}
        return 200, json.dumps({"data": self.tasks[path.split("/")[2]]}), {}

    @property
    def mutations(self):
        return [c for c in self.calls if c["method"] != "GET"]


def work_action(aid, key, summary, owner="WNC_INTERNAL", group=None, status="required"):
    p = {"resolution_item_key": key, "summary": summary, "resolution_owner": owner, "resolution_status": status}
    if group:
        p.update(resolution_group_key=group, resolution_group_title="Confirm supplier logistics")
    return make_asana_action(aid, target_adapter_code="task_surface", structured_payload=p)


def synthetic_repo():
    case = replace(make_case(), client_account_ref="SYNTHETIC TEST — WNC Operations",
                   active_event_start="2026-11-12T14:00:00+01:00", active_event_end="2026-11-12T18:00:00+01:00")
    repo = make_repo(case, actions=())
    for action in (
        work_action(1, "venue", "Confirm studio availability for the requested time"),
        work_action(2, "supplier:handover", "Confirm handover arrangements", "EXTERNAL_PARTY", "supplier-logistics"),
        work_action(3, "supplier:loading", "Confirm the loading route", "EXTERNAL_PARTY", "supplier-logistics"),
        work_action(4, "supplier:arrival", "Confirm supplier arrival timing", "EXTERNAL_PARTY", "supplier-logistics"),
        work_action(5, "fee-review", "Review the requested fee adjustment", "GOVERNED_DECISION"),
        work_action(6, "client-layout", "Confirm the preferred room layout", "CLIENT"),
    ):
        repo.create_workflow_action(action)
    for index, (field, value) in enumerate((("event_type", "team workshop"), ("requested_rental_scope", "studio_space"), ("guest_count", 24)), 1):
        repo.rental_case_facts[1].append(RentalCaseFact(index, 1, field, "event_profile", value,
            "synthetic_governed_fixture", 0, NOW, NOW))
    return repo


def harness(repo=None):
    repo = repo or synthetic_repo()
    transport = FakeAsana()
    runtime = AppRuntimeConfig(app_env=AppEnvironment.STAGING, staging_allowed_asana_project_gids=("222",), staging_allow_real_asana=True)
    adapter = AsanaProjectionAdapter(AsanaAdapterConfig("fake-token", "111", "222"), transport, repo, runtime)
    return repo, transport, adapter


def prepare(repo):
    return prepare_projection(repo, rental_case_id=1, workspace_gid="111", project_gid="222", now=NOW)


def execute(repo, adapter, action):
    return execute_workflow_action(repo, WorkflowActionExecutionRequest(1, action.workflow_action_id, "synthetic_operator"),
        adapter_registry=ExecutionAdapterRegistry({ADAPTER: adapter}), now=lambda: NOW)


@pytest.fixture(autouse=True)
def no_network():
    with patch("urllib.request.urlopen", side_effect=AssertionError("Live network prohibited")):
        yield


def test_fresh_case_one_master_grouped_work_canonical_bindings_and_replay():
    repo, transport, adapter = harness()
    action = prepare(repo)
    result = execute(repo, adapter, action)
    assert result.action_status_after == "succeeded", result
    assert len(transport.tasks) == 4  # master + venue + supplier group + decision
    assert len([t for t in transport.tasks.values() if t["parent"] is None]) == 1
    attempts = repo.load_case_snapshot(1).execution_attempts
    bindings = attempts[0].response_snapshot["bindings"]
    assert all(b["project_gid"] == "222" and b["workspace_gid"] == "111" and b["rental_case_id"] == 1 for b in bindings.values())
    assert len(bindings["group:EXTERNAL_PARTY:supplier-logistics"]["members"]) == 3
    assert bindings["item:fee-review"]["owner"] == "GOVERNED_DECISION"
    assert prepare(repo).workflow_action_id == action.workflow_action_id
    assert execute(repo, adapter, action).already_succeeded_idempotently
    assert len(transport.mutations) == 4 and len(repo.execution_attempts[1]) == 1
    assert adapter.observe(action=action)["status"] == "matches_projection"


def update_case(repo):
    repo.rental_cases[1] = replace(repo.rental_cases[1], case_revision=1)
    repo.rental_case_facts[1] = [replace(f, value_payload=30, established_case_revision=1) if f.field_code == "guest_count" else f
                               for f in repo.rental_case_facts[1]]
    closed = replace(work_action(20, "venue", "Confirm studio availability for the requested time", status="resolved"),
                     idempotency_key="resolved:venue:1", source_case_revision=1)
    new = replace(work_action(21, "technical", "Confirm projector and microphone availability"),
                  idempotency_key="technical:1", source_case_revision=1)
    repo.create_workflow_action(closed)
    repo.create_workflow_action(new)


def test_update_reuses_master_adds_once_and_completes_without_deleting_history():
    repo, transport, adapter = harness()
    execute(repo, adapter, prepare(repo))
    before = copy.deepcopy(transport.tasks)
    update_case(repo)
    updated = prepare(repo)
    assert execute(repo, adapter, updated).action_status_after == "succeeded"
    assert len(transport.tasks) == 5
    assert "Guests: 30" in transport.tasks["1000"]["notes"]
    venue_gid = next(gid for gid, task in before.items() if task["name"].startswith("Confirm studio"))
    assert transport.tasks[venue_gid]["completed"] is True
    assert all(gid in transport.tasks for gid in before)
    count = len(transport.mutations)
    assert execute(repo, adapter, prepare(repo)).already_succeeded_idempotently
    assert len(transport.mutations) == count
    assert len(repo.execution_attempts[1]) == 2


@pytest.mark.parametrize("failure", ["timeout_after_accept", "invalid_json_after_accept", 503])
def test_ambiguous_create_fences_new_revisions_and_read_never_retries(failure):
    repo, transport, adapter = harness()
    action = prepare(repo)
    transport.next_failure = failure
    result = execute(repo, adapter, action)
    assert result.action_status_after == "failed"
    assert repo.execution_attempts[1][-1].failure_code == "adapter_outcome_ambiguous"
    assert not result.retry_eligible
    mutation_count = len(transport.mutations)
    update_case(repo)
    assert execute(repo, adapter, prepare(repo)).failure_codes == ("adapter_outcome_ambiguous",)
    evidence = adapter.observe(action=action)
    assert evidence["canonical_truth_changed"] is False
    assert len(transport.mutations) == mutation_count
    assert len(repo.execution_attempts[1]) == 1
    assert evidence["status"] == ("inconclusive" if failure == 503 else "review_required")


def test_rate_limit_before_confirmation_is_retry_safe():
    repo, transport, adapter = harness()
    action = prepare(repo)
    transport.next_failure = 429
    assert execute(repo, adapter, action).retry_eligible
    assert not transport.tasks
    assert execute(repo, adapter, action).action_status_after == "succeeded"
    assert len(transport.tasks) == 4


@pytest.mark.parametrize("field,value", [("completed", True), ("name", "Operator renamed task"), ("notes", "Price approved; venue available")])
def test_human_edits_are_evidence_and_never_business_truth(field, value):
    repo, transport, adapter = harness()
    action = prepare(repo)
    execute(repo, adapter, action)
    before = copy.deepcopy((repo.rental_cases, repo.rental_case_facts, repo.case_decisions, repo.requirements))
    transport.tasks["1001"][field] = value
    evidence = adapter.observe(action=action)
    assert evidence["status"] == "review_required"
    assert (repo.rental_cases, repo.rental_case_facts, repo.case_decisions, repo.requirements) == before
    update_case(repo)
    count = len(transport.mutations)
    assert execute(repo, adapter, prepare(repo)).action_status_after == "failed"
    assert len(transport.mutations) == count


@pytest.mark.parametrize("runtime_change,config_change", [
    ({"staging_allow_real_asana": False}, {}), ({"app_env": AppEnvironment.PRODUCTION}, {}),
    ({"app_env": AppEnvironment.LOCAL}, {}), ({"staging_allowed_asana_project_gids": ("999",)}, {}),
    ({}, {"workspace_gid": "999"}), ({}, {"default_project_gid": "999"}),
    ({}, {"api_base_url": "https://example.test"}), ({}, {"access_token": None}),
])
def test_provider_scope_gate_blocks_before_attempt_or_network(runtime_change, config_change):
    repo, transport, adapter = harness()
    action = prepare(repo)
    adapter.runtime = replace(adapter.runtime, **runtime_change)
    adapter.config = replace(adapter.config, **config_change)
    assert execute(repo, adapter, action).failure_codes
    assert not transport.calls and not repo.execution_attempts[1]


def test_contract_tampering_and_stale_state_fail_closed():
    repo, transport, adapter = harness()
    action = prepare(repo)
    tampered = copy.deepcopy(action.structured_payload)
    tampered["projection"]["master"]["name"] = "Injected name"
    repo.workflow_actions[1][-1] = replace(action, structured_payload=tampered)
    assert execute(repo, adapter, repo.workflow_actions[1][-1]).failure_codes
    assert not transport.calls


def test_missing_items_are_not_silently_closed_and_groups_preserve_ownership():
    repo = synthetic_repo()
    plan = build_projection(repo.load_case_snapshot(1), workspace_gid="111", project_gid="222")
    assert len(plan["work"]) == 3
    assert all(w["owner"] != "CLIENT" for w in plan["work"])
    assert "Client to answer: Confirm the preferred room layout" in plan["master"]["notes"]
    assert all("Workflow Action" not in w["notes"] and "Idempotency" not in w["notes"] for w in plan["work"])
    assert plan["custom_fields"] == {}


def test_reconciliation_paginated_duplicate_and_scope_detection():
    repo, transport, adapter = harness()
    action = prepare(repo)
    execute(repo, adapter, action)
    transport.page_size = 1
    assert adapter.observe(action=action)["status"] == "matches_projection"
    transport.tasks["1000"]["workspace"] = {"gid": "999"}
    assert adapter.observe(action=action)["status"] == "review_required"
    transport.tasks["2000"] = {**copy.deepcopy(transport.tasks["1000"]), "gid": "2000"}
    assert adapter.observe(action=action)["master_candidates"] == 2


def test_started_attempt_survives_crash_and_fences_other_action():
    repo, transport, adapter = harness()
    action = prepare(repo)
    started = repo.start_workflow_action_execution(WorkflowActionExecutionRequest(1, action.workflow_action_id, "operator"))
    assert started.execution_attempt_id
    update_case(repo)
    assert execute(repo, adapter, prepare(repo)).failure_codes == ("adapter_outcome_ambiguous",)
    assert not transport.calls


def test_partial_rate_limit_resumes_using_confirmed_master_without_duplicates():
    repo, transport, adapter = harness()
    original = transport.send_json
    def fail_child(**kwargs):
        if kwargs["method"] == "POST" and "/subtasks" in kwargs["url"]:
            transport.next_failure = 429
            transport.send_json = original
        return original(**kwargs)
    transport.send_json = fail_child
    action = prepare(repo)
    assert execute(repo, adapter, action).retry_eligible
    assert len(transport.tasks) == 1
    assert repo.execution_attempts[1][-1].response_snapshot["bindings"]["master"]["gid"] == "1000"
    assert execute(repo, adapter, action).action_status_after == "succeeded"
    assert len(transport.tasks) == 4
    assert len([c for c in transport.mutations if c["path"] == "/tasks"]) == 1


def test_unresolved_group_removal_cannot_duplicate_or_hide_work():
    repo, transport, adapter = harness()
    execute(repo, adapter, prepare(repo))
    repo.workflow_actions[1] = [a for a in repo.workflow_actions[1] if a.structured_payload.get("resolution_item_key") != "supplier:arrival"]
    repo.rental_cases[1] = replace(repo.rental_cases[1], case_revision=1)
    count = len(transport.mutations)
    assert execute(repo, adapter, prepare(repo)).action_status_after == "failed"
    assert len(transport.mutations) == count


def test_provider_confirmation_then_persistence_failure_retains_crash_fence():
    repo, transport, adapter = harness()
    with patch.object(repo, "complete_workflow_action_execution", side_effect=RuntimeError("database unavailable")):
        with pytest.raises(RuntimeError, match="database unavailable"):
            execute(repo, adapter, prepare(repo))
    assert len(transport.tasks) == 4
    assert repo.execution_attempts[1][-1].status == "started"
    update_case(repo)
    assert execute(repo, adapter, prepare(repo)).failure_codes == ("adapter_outcome_ambiguous",)
    assert len(transport.mutations) == 4


def test_wrong_provider_project_workspace_is_blocked_before_mutation():
    repo, transport, adapter = harness()
    original = transport.send_json
    def wrong_scope(**kwargs):
        if "/projects/222?" in kwargs["url"]:
            return 200, json.dumps({"data": {"gid": "222", "workspace": {"gid": "999"}, "archived": False}}), {}
        return original(**kwargs)
    transport.send_json = wrong_scope
    assert execute(repo, adapter, prepare(repo)).action_status_after == "failed"
    assert not transport.mutations
