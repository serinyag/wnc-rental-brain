"""Deterministic, outbound-only rental projection from persisted governed state.

The existing action/attempt journal is the binding store. No provider value is
used here to establish a fact, resolve an obligation, or confirm a booking.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .contracts import WorkflowAction

ADAPTER = "asana_projection"
VERSION = "asana_rental_projection_v1"
DEPARTMENT_VERSION = "asana_rental_projection_departments_v2"
NUANCED_VERSION = "asana_rental_projection_nuanced_v3"
DEPARTMENTS = ("Admin", "Logistics", "Experience", "Post-event")
OWNERS = {"CLIENT", "WNC_INTERNAL", "EXTERNAL_PARTY", "GOVERNED_DECISION"}
RESOLVED = {"resolved", "completed", "cancelled", "superseded"}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _text(value, fallback="Not yet provided"):
    if value is None:
        return fallback
    if not isinstance(value, (str, int)) or isinstance(value, bool):
        raise ValueError("Asana summary requires a scalar governed value")
    result = str(value).strip()
    if len(result) > 600 or "\n" in result:
        raise ValueError("Asana summary text must be concise and single-line")
    return result or fallback


def _timing(value):
    if not value:
        return "Date to be confirmed"
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Governed event timing requires timezone provenance")
    return parsed.astimezone(ZoneInfo("Europe/Amsterdam")).strftime("%d %B %Y, %H:%M %Z")


def _build_flat_projection(snapshot, *, workspace_gid, project_gid, enforce_limits=True):
    """Read existing facts and resolution actions; omission never means resolved.

    Explicit resolution_group_key/title permit same-owner grouping. Each member
    keeps its semantic identity and source WorkflowAction in the canonical plan.
    """
    case = snapshot.rental_case
    from .operational_resolution import resolved_keys
    governed_resolved = resolved_keys(snapshot)
    facts = {f.field_code: f.value_payload for f in snapshot.rental_case_facts}
    metadata = next((e.structured_payload for e in snapshot.workflow_events
                     if e.event_type_code == "test_console_case_registered"), {})
    client = _text(metadata.get("client_label") or case.client_account_ref, "Client not yet identified")
    event = _text(facts.get("event_type"), "Rental inquiry").replace("_", " ")
    date = _timing(case.active_event_start)
    timing = date + (f" to {_timing(case.active_event_end)}" if case.active_event_end else "")
    scope = _text(facts.get("requested_rental_scope") or (case.rental_type_code if case.rental_type_code != "custom_scope" else None), "Scope to be confirmed").replace("_", " ")
    guests = _text(facts.get("guest_count"))
    latest = {}
    for action in sorted(snapshot.workflow_actions, key=lambda a: (a.source_case_revision, a.workflow_action_id)):
        p = action.structured_payload
        if action.target_adapter_code == ADAPTER or not p.get("resolution_item_key"):
            continue
        owner = p.get("resolution_owner")
        if owner not in OWNERS:
            raise ValueError("Unknown resolution ownership; projection blocked")
        latest[p["resolution_item_key"]] = action
    groups = {}
    client_items = []
    blocker_states = {f"blocker:{b.blocker_id}": b.status for b in snapshot.blockers}
    current_availability_key = f"availability:{case.active_event_start}:{case.active_event_end}"
    for key, action in sorted(latest.items()):
        p = action.structured_payload
        owner = p["resolution_owner"]
        closed = (key in governed_resolved if p.get("governed_resolution_event_id")
                  else p.get("resolution_status") in RESOLVED)
        # Historical bindings stay visible and keep their provider identity.
        # A changed window retires its old check; a resolved canonical blocker
        # retires its derived work even if an older action payload says REQUIRED.
        retired = ((key.startswith("availability:") and case.active_event_start
                    and case.active_event_end and key != current_availability_key)
                   or blocker_states.get(key) in RESOLVED)
        closed = closed or retired
        summary = _text(p.get("summary"))
        if owner == "CLIENT":
            if not closed:
                client_items.append(summary)
            continue
        group = p.get("resolution_group_key")
        identity = f"group:{owner}:{group}" if group else f"item:{key}"
        title = _text(p.get("resolution_group_title")) if group else summary
        item = groups.setdefault(identity, {"key": identity, "name": title, "owner": owner, "members": []})
        if item["name"] != title or item["owner"] != owner:
            raise ValueError("Conflicting governed group identity")
        item["members"].append({"key": key, "workflow_action_id": action.workflow_action_id,
                                "summary": summary, "resolved": closed, "retired": bool(retired)})
    other_open = []
    for question in snapshot.open_questions:
        if question.status == "open":
            if question.requested_from_role in {None, "client", "CLIENT"}:
                client_items.append(_text(question.human_question_text))
            else:
                other_open.append("Confirm with " + _text(question.requested_from_role).replace("_", " ") + ": " + _text(question.human_question_text))
    for requirement in snapshot.requirements:
        if requirement.status in {"required", "unresolved", "in_progress"}:
            other_open.append("Check " + requirement.requirement_type.replace("_", " ") + ".")
    for change in snapshot.proposed_changes:
        if change.status in {"proposed", "under_review"}:
            label = change.change_kind.replace("_", " ")
            if isinstance(change.proposed_value_payload, (str, int)):
                label += ": " + _text(change.proposed_value_payload)
            other_open.append("Requested change awaiting review — " + label + ".")
    for decision in snapshot.case_decisions:
        if decision.status in {"proposed", "pending_approval"}:
            other_open.append("Decision awaiting governed review — " + _text(decision.scope_description) + ".")
    for blocker in snapshot.blockers:
        if blocker.status == "open" and blocker.origin_entity_type not in {"open_question", "requirement", "case_decision", "workflow_action"}:
            other_open.append(_text(blocker.resolution_condition_text))
    other_open = list(dict.fromkeys(other_open))
    client_items = list(dict.fromkeys(client_items))
    work = []
    owner_labels = {"WNC_INTERNAL": "WNC internal check", "EXTERNAL_PARTY": "WNC follow-up with external party",
                    "GOVERNED_DECISION": "WNC governed decision review"}
    for key, item in sorted(groups.items()):
        item["completed"] = all(m["resolved"] for m in item["members"])
        item["notes"] = owner_labels[item["owner"]] + "\n\n" + "\n".join(
            ("Retired: " if m["retired"] else "Done: " if m["resolved"] else "To do: ") + m["summary"] for m in item["members"])
        item["notes"] += "\n\nRecord the outcome for governed review before treating it as confirmed."
        work.append(item)
    opened = [w for w in work if not w["completed"]]
    closed_case = case.lifecycle_state in {"closed", "closed_lost", "cancelled"}
    if closed_case:
        stage = "Closed / cancelled"
    elif any(w["owner"] == "GOVERNED_DECISION" for w in opened):
        stage = "Decision required"
    elif any(w["owner"] == "WNC_INTERNAL" for w in opened):
        stage = "Internal checks"
    elif opened:
        stage = "Waiting on external party"
    elif other_open:
        stage = "Internal checks"
    elif client_items:
        stage = "Needs client info"
    else:
        stage = {"proposal_pending_client": "Awaiting client", "confirmed_pre_event": "Confirmed / progressing",
                 "event_ready": "Confirmed / progressing", "event_in_progress": "Confirmed / progressing",
                 "inquiry_active": "New inquiry"}.get(case.lifecycle_state, "Ready for client response")
    open_lines = [f"- {owner_labels[w['owner']]}: {w['name']}" for w in opened]
    open_lines += [f"- Client to answer: {q}" for q in client_items]
    open_lines += [f"- {line}" for line in other_open]
    communication = "Client response is waiting on internal work." if opened or other_open else (
        "Client information is still needed." if client_items else "Review the next client response in WNC Rental Brain.")
    marker = "WNC reference: " + case.case_reference_code + " / " + digest(case.rental_case_uuid)[:12]
    notes = (f"CLIENT\n{client}\n\nEVENT\n{event}\nRequested timing: {timing}\n"
             f"Requested venue / scope: {scope}\nGuests: {guests}\n\nCURRENT STATUS\n{stage}\n"
             f"{communication}\n\nOPEN ITEMS\n" + ("\n".join(open_lines) or "No unresolved operational items.")
             + "\n\nNEXT ACTIONS\n" + ("Complete the checks below and record their outcomes for review." if opened or other_open
                 else "Review the case and prepare the next appropriate client response.")
             + "\n\nOUTLOOK\nNo verified conversation link is available for this case.\n\n" + marker)
    value = {"version": VERSION, "rental_case_id": case.rental_case_id,
             "case_uuid": case.rental_case_uuid, "case_revision": case.case_revision,
             "workspace_gid": str(workspace_gid), "project_gid": str(project_gid),
             "master": {"name": f"{client} — {event} — {date.split(',')[0]}",
                        "notes": notes, "completed": closed_case}, "work": work, "custom_fields": {}, "marker": marker}
    if enforce_limits and (len(notes) > 10000 or len(work) > 25):
        raise ValueError("Projection needs operator review: too much work for a concise task")
    return value


def build_projection(snapshot, *, workspace_gid, project_gid, version=VERSION, application_origin=None):
    value = _build_flat_projection(snapshot, workspace_gid=workspace_gid, project_gid=project_gid)
    if version == VERSION:
        return value  # Preserve the exact certified plans and their replay keys.
    if version not in {DEPARTMENT_VERSION, NUANCED_VERSION}:
        raise ValueError("Unknown Asana projection version")
    # Keep the action/attempt envelope and its database fence at v1. The optional
    # layout has its own version and participates in the complete content hash.
    value["layout_version"] = version
    categories = {name: [] for name in DEPARTMENTS}
    actions = {a.workflow_action_id: a for a in snapshot.workflow_actions}
    for item in value["work"]:
        explicit = {actions[m["workflow_action_id"]].structured_payload.get("resolution_department")
                    for m in item["members"]} - {None}
        if len(explicit) > 1 or explicit - set(DEPARTMENTS):
            raise ValueError("Conflicting operational department; review required")
        keys = " ".join([item["key"], *(m["key"] for m in item["members"])]).lower()
        if version == NUANCED_VERSION:
            # Real governed blockers have opaque keys (blocker:123). Their
            # canonical action title supplies the operational category.
            keys += " " + item["name"].lower()
        department = next(iter(explicit), None)
        if department is None and version == NUANCED_VERSION:
            # Existing provider hierarchy stays bound. Improved inference is
            # for new work; moving an existing task needs explicit migration.
            existing_parent = prior_bindings(snapshot).get(item["key"], {}).get("parent_key")
            department = next((name for name in DEPARTMENTS
                if existing_parent == "department:" + name.lower()), None)
        if department is None:
            department = ("Post-event" if any(k in keys for k in ("post-event", "post_event", "debrief")) else
                          "Experience" if any(k in keys for k in ("catering", "facilitator", "hospitality")) else
                          "Logistics" if any(k in keys for k in ("technical", "tech", "logistics", "staff", "layout", "loading", "handover")) else "Admin")
        item["parent_key"] = "department:" + department.lower()
        categories[department].append(item)
    work = []
    for name, items in categories.items():
        if version == NUANCED_VERSION and not items:
            continue
        work.append({"key": "department:" + name.lower(), "name": name, "owner": "WNC_INTERNAL",
                     "parent_key": "master", "kind": "department", "members": [],
                     "completed": bool(items) and all(i["completed"] for i in items),
                     "notes": "Operational work for this rental.\n" +
                     ("Open each subtask to review its evidence and next action." if items else
                      "No applicable governed work is recorded yet. This category is not confirmed complete.")})
        work.extend(items)
    value["work"] = work
    from .google_proposal import binding as proposal_binding, proposal_send_block
    proposal = proposal_binding(snapshot)
    if proposal:
        import re
        document_id = proposal.get('document_id', '')
        if not re.fullmatch(r'[A-Za-z0-9_-]{3,200}', document_id):
            raise ValueError('Invalid proposal document binding')
        status = 'Current' if proposal_send_block(snapshot) is None else 'Needs review / synchronization'
        value['master']['notes'] += ('\n\nRENTAL PROPOSAL\nhttps://docs.google.com/document/d/'
            + document_id + '/edit\nStatus: ' + status + '\nNext action: Review confirmed details and remaining TBC items.')
    if application_origin:
        from urllib.parse import urlsplit
        parsed = urlsplit(application_origin)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
            raise ValueError("Live details require the trusted HTTPS application origin")
        value["master"]["notes"] += "\n\nLIVE DETAILS / WORKING PROPOSAL\n" + application_origin + f"/cases/{snapshot.rental_case.rental_case_id}/live-proposal"
    if len(value["work"]) > 29 or len(value["master"]["notes"]) > 10000:
        raise ValueError("Projection needs operator review: too much work")
    return value


def prepare_projection(repository, *, rental_case_id, workspace_gid, project_gid, now=None, version=VERSION, application_origin=None):
    snapshot = repository.load_case_snapshot(rental_case_id)
    if snapshot is None:
        raise ValueError("Case not found")
    value = build_projection(snapshot, workspace_gid=workspace_gid, project_gid=project_gid, version=version, application_origin=application_origin)
    key = f"{VERSION}:{rental_case_id}:{digest(value)}"
    timestamp = now or datetime.now(timezone.utc).isoformat()
    action = WorkflowAction(workflow_action_id=1, workflow_action_uuid="pending",
        rental_case_id=rental_case_id, action_type="CREATE_INTERNAL_TASK_ITEM", action_category="coordination",
        target_adapter_code=ADAPTER, reason_entity_type="rental_case", reason_entity_id=rental_case_id,
        approval_posture="automatic_allowed",
        status="ready_to_execute", semantic_subject_hash=digest(value),
        source_case_revision=snapshot.rental_case.case_revision, idempotency_key=key,
        structured_payload={"task_kind": VERSION, "summary": value["master"]["name"],
                            "reason": "Project governed rental operations", "projection": value},
        created_at=timestamp, updated_at=timestamp)
    return repository.create_workflow_action(action)


def validate_projection(action, snapshot, config, *, application_origin=None):
    if action.structured_payload.get("task_kind") != VERSION:
        raise ValueError("Unknown Asana action envelope")
    version = action.structured_payload.get("projection", {}).get("layout_version", VERSION)
    expected = build_projection(snapshot, workspace_gid=config.workspace_gid, project_gid=config.default_project_gid,
                                version=version, application_origin=application_origin)
    if (action.target_adapter_code != ADAPTER or action.action_type != "CREATE_INTERNAL_TASK_ITEM"
            or action.structured_payload.get("projection") != expected
            or action.semantic_subject_hash != digest(expected)
            or action.idempotency_key != f"{VERSION}:{action.rental_case_id}:{digest(expected)}"):
        raise ValueError("Canonical Asana projection mismatch")
    return expected


def projection_attempts(snapshot):
    return sorted((a for a in snapshot.execution_attempts if a.adapter_code == ADAPTER),
                  key=lambda a: a.execution_attempt_id)


def prior_bindings(snapshot):
    bindings = {}
    for attempt in projection_attempts(snapshot):
        if isinstance(attempt.response_snapshot, dict):
            bindings.update(deepcopy(attempt.response_snapshot.get("bindings", {})))
    return bindings
