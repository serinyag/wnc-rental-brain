"""Asana case projection using the existing governed execution journal.

A started/ambiguous attempt fences all later case projections. Partial confirmed
bindings survive in the attempt snapshot. Reads report evidence only and never
clear that fence or change business facts.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.parse import urlencode

from .asana_adapter import AsanaAdapterConfig, AsanaTransportProtocol, DEFAULT_ASANA_API_BASE_URL
from .asana_projection import ADAPTER, digest, validate_projection, projection_attempts, prior_bindings
from .execution_types import NormalizedExecutionResult


class ProjectionFailure(Exception):
    def __init__(self, reason, *, ambiguous=False, retry=False):
        self.reason, self.ambiguous, self.retry = reason, ambiguous, retry
        super().__init__(reason)


@dataclass
class AsanaProjectionAdapter:
    config: AsanaAdapterConfig
    transport: AsanaTransportProtocol
    repository: object
    runtime: object

    def _scope(self, *, mutation):
        # This certification rollout cannot execute in local/production or use a
        # caller-controlled API host/project. Tokens are never placed in evidence.
        if self.runtime.is_production:
            contract=self.runtime.production
            if (contract is None or (mutation and not contract.lane("asana_mutations")) or
                self.config.workspace_gid != contract.manifest['asana']['workspace_gid'] or
                self.config.default_project_gid != contract.manifest['asana']['project_gid'] or
                self.config.api_base_url != DEFAULT_ASANA_API_BASE_URL or not self.config.has_credentials()):
                raise ProjectionFailure("production_scope_or_gate_invalid")
            return
        if (not self.runtime.is_staging or (mutation and not self.runtime.staging_allow_real_asana)
                or not self.config.has_credentials() or not self.config.workspace_gid
                or not self.config.default_project_gid
                or not self.runtime.is_asana_project_allowed(self.config.default_project_gid)
                or self.config.api_base_url != DEFAULT_ASANA_API_BASE_URL):
            raise ProjectionFailure("staging_scope_or_gate_invalid")
        for gid in (self.config.workspace_gid, self.config.default_project_gid):
            if not gid.isdecimal():
                raise ProjectionFailure("invalid_provider_identity")

    def availability_failure_code(self, *, action):
        try:
            self._scope(mutation=True)
            snapshot = self.repository.load_case_snapshot(action.rental_case_id)
            validate_projection(action, snapshot, self.config)
            if any(a.status == "started" or (a.status != "succeeded" and not a.retry_eligible)
                   for a in projection_attempts(snapshot)):
                return "adapter_outcome_ambiguous"
            for binding in prior_bindings(snapshot).values():
                self._validate_binding_scope(binding, action.rental_case_id)
        except (ProjectionFailure, ValueError, TypeError, AttributeError):
            return "adapter_forbidden"
        return None

    def _validate_binding_scope(self, binding, case_id):
        if (binding.get("workspace_gid") != self.config.workspace_gid
                or binding.get("project_gid") != self.config.default_project_gid
                or binding.get("rental_case_id") != case_id
                or not str(binding.get("gid", "")).isdecimal()):
            raise ProjectionFailure("binding_scope_conflict")

    def _request(self, method, path, payload=None):
        self._scope(mutation=method != "GET")
        try:
            status, body, _ = self.transport.send_json(method=method,
                url=self.config.api_base_url + path,
                headers={"Authorization": f"Bearer {self.config.authorization_token()}", "Accept": "application/json",
                         "Content-Type": "application/json"},
                payload={} if payload is None else {"data": payload}, timeout_seconds=self.config.timeout_seconds)
        except Exception as exc:
            raise ProjectionFailure("transport_outcome_unknown", ambiguous=method != "GET",
                                    retry=method == "GET") from exc
        if not 200 <= status < 300:
            raise ProjectionFailure(f"provider_http_{status}", ambiguous=method != "GET" and status >= 500,
                                    retry=status == 429 or (method == "GET" and status >= 500))
        try:
            parsed = json.loads(body)
            if not isinstance(parsed, dict) or "data" not in parsed:
                raise ValueError()
            return parsed
        except (ValueError, TypeError) as exc:
            raise ProjectionFailure("provider_response_unverifiable", ambiguous=method != "GET",
                                    retry=method == "GET") from exc

    def _list(self, path):
        records, offsets = [], set()
        params = {"limit": 100, "opt_fields": "gid,name,notes,completed,workspace.gid,projects.gid,parent.gid"}
        # Include completed items: completing a task must not make it disappear
        # from duplicate detection. Never follow provider-supplied URLs.
        if path.startswith("/projects/"):
            params["completed_since"] = "1970-01-01T00:00:00Z"
        for _ in range(100):
            response = self._request("GET", path + "?" + urlencode(params))
            if not isinstance(response["data"], list):
                raise ProjectionFailure("provider_list_malformed")
            records.extend(response["data"])
            next_page = response.get("next_page")
            if not next_page:
                return records
            offset = next_page.get("offset") if isinstance(next_page, dict) else None
            if not isinstance(offset, str) or not offset or offset in offsets:
                raise ProjectionFailure("provider_pagination_inconclusive")
            offsets.add(offset)
            params["offset"] = offset
        raise ProjectionFailure("provider_pagination_limit")

    def _read(self, gid):
        if not isinstance(gid, str) or not gid.isdecimal():
            raise ProjectionFailure("invalid_task_gid")
        return self._request("GET", f"/tasks/{gid}?" + urlencode({
            "opt_fields": "gid,name,notes,completed,workspace.gid,projects.gid,parent.gid"}))["data"]

    def _verify(self, record, expected, *, parent=None):
        if not isinstance(record, dict) or not isinstance(record.get("gid"), str) or not record["gid"].isdecimal():
            raise ProjectionFailure("provider_identity_missing")
        if record.get("workspace", {}).get("gid") != self.config.workspace_gid:
            raise ProjectionFailure("provider_workspace_conflict")
        if parent is None:
            if (record.get("parent") or {"gid": None}).get("gid") is not None:
                raise ProjectionFailure("master_has_parent")
            if self.config.default_project_gid not in [p.get("gid") for p in record.get("projects", [])]:
                raise ProjectionFailure("provider_project_conflict")
        elif (record.get("parent") or {}).get("gid") != parent:
            raise ProjectionFailure("provider_parent_conflict")
        if any(record.get(key) != value for key, value in expected.items()):
            raise ProjectionFailure("human_edit_requires_governed_review")

    @staticmethod
    def _desired(plan):
        desired = {"master": dict(plan["master"])}
        for item in plan["work"]:
            desired[item["key"]] = {"name": item["name"], "notes": item["notes"] + "\n\n" + plan["marker"]
                + " / work " + digest(item["key"])[:12], "completed": item["completed"]}
        return desired

    def execute(self, *, action, execution_context, idempotency):
        bindings, mutations, mutation_requests = {}, 0, 0
        try:
            self._scope(mutation=True)
            snapshot = self.repository.load_case_snapshot(action.rental_case_id)
            plan = validate_projection(action, snapshot, self.config)
            project = self._request("GET", f"/projects/{self.config.default_project_gid}?opt_fields=gid,workspace.gid,archived")["data"]
            if (not isinstance(project, dict) or project.get("gid") != self.config.default_project_gid
                    or project.get("workspace", {}).get("gid") != self.config.workspace_gid
                    or project.get("archived") is not False):
                raise ProjectionFailure("staging_project_verification_failed")
            others = [a for a in projection_attempts(snapshot) if a.execution_attempt_id != idempotency.execution_attempt_id]
            if any(a.status == "started" or (a.status != "succeeded" and not a.retry_eligible) for a in others):
                raise ProjectionFailure("prior_projection_requires_reconciliation", ambiguous=True)
            bindings = prior_bindings(snapshot)
            desired = self._desired(plan)
            desired_members = {m["key"]: w["key"] for w in plan["work"] for m in w["members"]}
            for key, binding in bindings.items():
                if key != "master" and not binding["projected"]["completed"]:
                    if key not in desired or any(desired_members.get(m["key"]) != key for m in binding["members"]):
                        raise ProjectionFailure("open_work_requires_explicit_resolution_before_regrouping")
            # Validate every existing object before making any write. Human edits
            # stop the run; a completion is not evidence of real-world resolution.
            for key, binding in bindings.items():
                self._validate_binding_scope(binding, action.rental_case_id)
                self._verify(self._read(binding["gid"]), binding["projected"],
                             parent=None if key == "master" else bindings["master"]["gid"])
            if "master" not in bindings:
                candidates = self._list(f"/projects/{self.config.default_project_gid}/tasks")
                if any(plan["marker"] in str(t.get("notes", "")).splitlines() for t in candidates):
                    raise ProjectionFailure("unbound_master_requires_reconciliation", ambiguous=True)
            for key, fields in desired.items():
                old = bindings.get(key)
                if old and old["projected"] == fields:
                    if key != "master":
                        old["members"] = next(w["members"] for w in plan["work"] if w["key"] == key)
                    continue
                # Do not create a historical work item that is already resolved.
                if not old and key != "master" and fields["completed"]:
                    continue
                parent = bindings.get("master", {}).get("gid") if key != "master" else None
                if old:
                    method, path, payload = "PUT", f"/tasks/{old['gid']}", fields
                elif key == "master":
                    method, path = "POST", "/tasks"
                    payload = {**fields, "workspace": self.config.workspace_gid,
                               "projects": [self.config.default_project_gid]}
                else:
                    method, path, payload = "POST", f"/tasks/{parent}/subtasks", fields
                validate_projection(action, self.repository.load_case_snapshot(action.rental_case_id), self.config)
                mutation_requests += 1
                response = self._request(method, path, payload)["data"]
                mutations += 1
                gid = response.get("gid") if isinstance(response, dict) else None
                if not isinstance(gid, str) or not gid.isdecimal() or (old and gid != old["gid"]):
                    raise ProjectionFailure("mutation_identity_unverifiable", ambiguous=True)
                # Capture accepted provider identity before bounded verification.
                bindings[key] = {"gid": gid, "rental_case_id": action.rental_case_id,
                    "workspace_gid": self.config.workspace_gid, "project_gid": self.config.default_project_gid,
                    "workflow_action_id": action.workflow_action_id, "execution_attempt_id": idempotency.execution_attempt_id,
                    "semantic_key": key, "projected": fields,
                    "members": next((w["members"] for w in plan["work"] if w["key"] == key), []),
                    "owner": next((w["owner"] for w in plan["work"] if w["key"] == key), None)}
                try:
                    self._verify(self._read(gid), fields, parent=parent)
                except ProjectionFailure as exc:
                    raise ProjectionFailure("mutation_verification_inconclusive", ambiguous=True) from exc
            return NormalizedExecutionResult(adapter_code=ADAPTER, attempt_status="succeeded",
                external_reference=f"asana:projection:{action.rental_case_id}:{idempotency.execution_attempt_id}",
                response_snapshot={"provider": "asana", "bindings": bindings, "confirmed_mutations": mutations,
                                   "mutation_requests": mutation_requests,
                                   "master_task_gid": bindings["master"]["gid"]})
        except (ProjectionFailure, ValueError) as exc:
            ambiguous = isinstance(exc, ProjectionFailure) and exc.ambiguous
            retry = isinstance(exc, ProjectionFailure) and exc.retry and not ambiguous
            return NormalizedExecutionResult(adapter_code=ADAPTER, attempt_status="failed",
                failure_code="adapter_outcome_ambiguous" if ambiguous else "adapter_request_invalid",
                retry_eligible=retry, response_snapshot={"provider": "asana", "reason": str(exc),
                    "bindings": bindings, "confirmed_mutations": mutations, "mutation_requests": mutation_requests,
                    "canonical_truth_changed": False})

    def observe(self, *, action):
        """Read-only evidence for an operator; never import or release a retry fence.

        Exact marker + workspace/project + parent + content are checked. Missing,
        duplicate, moved, or edited candidates cannot be auto-adopted.
        """
        self._scope(mutation=False)
        plan = action.structured_payload["projection"]
        if plan["workspace_gid"] != self.config.workspace_gid or plan["project_gid"] != self.config.default_project_gid:
            raise ProjectionFailure("observation_scope_conflict")
        masters = [t for t in self._list(f"/projects/{self.config.default_project_gid}/tasks")
                   if plan["marker"] in str(t.get("notes", "")).splitlines()]
        if len(masters) != 1:
            return {"status": "inconclusive", "master_candidates": len(masters), "canonical_truth_changed": False}
        master = masters[0]
        observed = {"master": master}
        children = self._list(f"/tasks/{master['gid']}/subtasks")
        differences = []
        for key, expected in self._desired(plan).items():
            candidates = [master] if key == "master" else [t for t in children
                if expected["notes"].splitlines()[-1] in str(t.get("notes", "")).splitlines()]
            if len(candidates) != 1:
                differences.append({"key": key, "reason": "missing_or_duplicate", "count": len(candidates)})
                continue
            observed[key] = candidates[0]
            try:
                self._verify(candidates[0], expected, parent=None if key == "master" else master["gid"])
            except ProjectionFailure as exc:
                differences.append({"key": key, "reason": exc.reason})
        return {"status": "review_required" if differences else "matches_projection",
                "observed": observed, "differences": differences, "canonical_truth_changed": False,
                "retry_fence_released": False}
