from __future__ import annotations

import json
import unittest
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch

from tools.runtime_environment import AppEnvironment, AppRuntimeConfig
from tools.phase_08_workflow.contracts import ApprovalRequest
from tools.phase_08_workflow.execution_runtime import ExecutionAdapterRegistry, execute_workflow_action
from tools.phase_08_workflow.execution_types import WorkflowActionExecutionRequest
from tools.phase_08_workflow.inquiry_response_drafting import InquiryResponseDraftRevision
from tools.phase_08_workflow.inquiry_response_drafting import context_hash_payload, content_hash_payload, render_draft_body
from tools.phase_08_workflow.governed_client_response import DeterministicFakeClientResponseProvider
from tools.phase_08_workflow.outlook_action_contract import (
    CONTRACT_VERSION, GOVERNED_PURPOSE, GOVERNED_REASON, OutlookActionIntent, OutlookContractError,
    OutlookExecutionInput, build_governed_outlook_action, reserve_governed_outlook_action,
    validate_outlook_action, exact_approval_target,
    digest,
)
from tools.phase_08_workflow.outlook_adapter import OutlookExecutionAdapter, OutlookAdapterConfig, OutlookDraftSnapshot
from tools.phase_08_workflow.orchestration_runtime import apply_approval_decision, _validate_action_payload
from tools.phase_08_workflow.orchestration_types import ApprovalDecisionInput
from tools.phase_08_workflow.test_console_service import (
    TestConsoleService, TestConsoleConfig, _ProjectedWorkflowActionExecutionAdapter,
    _OutlookHumanEditReconciliationPlan, _OutlookHumanEditGraphRead,
)
from tools.phase_08_workflow.test_console_projection import TestConsoleCaseMetadata
from tools.phase_08_workflow.tests.test_execution_runtime import make_case, make_repo

NOW = "2026-09-13T10:00:00Z"
INTENT = OutlookActionIntent("COMPLETE_INQUIRY_RESPONSE", GOVERNED_PURPOSE, GOVERNED_REASON)


class MemoryDraftService(TestConsoleService):
    """Substitute storage and model only; use the real application builders."""
    def __init__(self):
        self.revisions = {}
        repo = make_repo(make_case(rental_case_id=424, case_revision=3))
        super().__init__(orchestration_repository=repo, observation_repository=SimpleNamespace(),
            client_response_provider=DeterministicFakeClientResponseProvider(),
            contextual_guidance_search=SimpleNamespace(search=lambda **kw: ()),
            config=TestConsoleConfig(runtime=AppRuntimeConfig(app_env=AppEnvironment.STAGING,
                staging_allowed_email_recipients=("client@example.test",))), now=lambda: NOW)

    def _require_case_snapshot(self, case_id): return self.orchestration_repository.load_case_snapshot(case_id)

    def load_case_detail(self, case_id):
        return SimpleNamespace(metadata=self._load_test_case_metadata(case_id),
            orchestration_snapshot=self._require_case_snapshot(case_id), evidence_bundles=(),
            working_proposal=SimpleNamespace(commercial_snapshot=(), feasibility_snapshot=()))

    def _load_test_case_metadata(self, case_id):
        return TestConsoleCaseMetadata(label="Synthetic", client_label="Synthetic", contact_email="client@example.test",
            event_reference="Synthetic", created_by="test", created_at=NOW)

    def _load_current_draft_revision_for_conversation(self, case_id, *, conversation_key):
        return next((r for r in self.revisions.values() if r.is_current and r.rental_case_id == case_id
                     and r.conversation_key == conversation_key), None)

    def _load_draft_revision_by_id(self, case_id, revision_id): return self.revisions.get(revision_id)

    def _create_draft_revision(self, *, context, content, draft_source, created_by_reference, supersedes_draft_revision_id):
        for ident, revision in list(self.revisions.items()):
            self.revisions[ident] = replace(revision, is_current=False)
        ident = 144 + len(self.revisions)
        revision = InquiryResponseDraftRevision(
            inquiry_response_draft_revision_id=ident, inquiry_response_draft_revision_uuid=f"draft-{ident}",
            rental_case_id=context.rental_case_id, workflow_action_id=context.workflow_action_id,
            conversation_key=context.conversation_key, source_case_revision=context.source_case_revision,
            draft_status="draft", draft_source=draft_source, is_current=True, subject=content.subject,
            salutation=content.salutation, intro_text=content.intro_text, question_lines=content.question_lines,
            closing_text=content.closing_text, signoff_text=content.signoff_text, body_text=render_draft_body(content),
            context_payload=context.to_payload(), context_hash=digest(json.loads(context_hash_payload(context))),
            content_hash=digest(json.loads(content_hash_payload(content))), recipient_email=context.recipient_email,
            sender_email=context.sender_email, sender_label=context.sender_label, created_by_reference=created_by_reference,
            created_at=NOW, updated_at=NOW, supersedes_draft_revision_id=supersedes_draft_revision_id)
        self.revisions[ident] = revision
        return revision

    def _bind_approval_request_to_draft_revision(self, *, rental_case_id, draft_revision_id, approval_request_id,
                                                draft_status, updated_at):
        revision = replace(self.revisions[draft_revision_id], approval_request_id=approval_request_id,
                           draft_status=draft_status, updated_at=updated_at)
        self.revisions[draft_revision_id] = revision
        return revision

    def _create_console_event(self, **kwargs):
        return self.orchestration_repository.create_workflow_event(
            **kwargs, source_type="test_console", event_identity_key=f"event:{len(self.orchestration_repository.workflow_events[424])}")


def canonical_fixture(*, path="normal", action_id=587, revision_id=144, case_id=424,
                      case_revision=3, content_hash="content-144", context_hash="context-144",
                      governed_hash="governed-424", recipient="approved@example.test",
                      conversation_key=None, subject="Approved subject", body="Approved body"):
    case = make_case(rental_case_id=case_id, case_revision=case_revision)
    human = path in {"human_edit", "recovery"}
    origin_id = 586 if path == "recovery" else action_id
    conversation_key = conversation_key or f"governed_client_response:{case_id}"
    revision = InquiryResponseDraftRevision(
        inquiry_response_draft_revision_id=revision_id, inquiry_response_draft_revision_uuid="revision-test",
        rental_case_id=case_id, workflow_action_id=origin_id, conversation_key=conversation_key,
        source_case_revision=case_revision, draft_status="send_failed" if path == "recovery" else "needs_approval",
        draft_source="human_edited" if human else "generated", is_current=True,
        subject=subject, body_text=body, salutation="Hello", intro_text="Approved", question_lines=(),
        closing_text="Regards", signoff_text="WNC", context_payload={"operator_annotations": []}, context_hash=context_hash,
        content_hash=content_hash, recipient_email=recipient, sender_email="sender@example.test",
        sender_label="WNC", created_by_reference="test", created_at=NOW, updated_at=NOW,
        approval_request_id=184 if path == "recovery" else None,
    )
    reservation = replace(reserve_governed_outlook_action(
        case=case, intent=INTENT, conversation_key=conversation_key, content_hash=content_hash,
        context_hash=governed_hash, recipient_email=recipient, provenance=path,
        origin_action_id=586 if path == "recovery" else (582 if path == "human_edit" else None),
        graph_message_id="bound-144" if human else None,
        recovery_revision_id=revision_id if path == "recovery" else None, now=NOW,
    ), workflow_action_id=action_id)
    action = build_governed_outlook_action(reservation=reservation, case=case, revision=revision,
        intent=INTENT, governed_context_hash=governed_hash, provenance=path,
        graph_message_id="bound-144" if human else None)
    return case, revision, reservation, action


class SyntheticTransport:
    """No network implementation; exercises the actual adapter HTTP contract."""
    def __init__(self, action, *, changed=False):
        self.action = action
        self.changed = changed
        self.calls = []
        self.sent = False

    def request(self, *, method, url, headers, body, timeout_seconds):
        self.calls.append((method, url))
        if url.endswith("/token"):
            return 200, json.dumps({"access_token": "synthetic-token"}), {}
        if method == "POST" and url.endswith("/messages"):
            return 201, json.dumps({"id": "bound-144"}), {}
        if method == "POST" and url.endswith("/send"):
            self.sent = True
            return 202, "", {}
        if method == "GET":
            p = self.action.structured_payload
            return 200, json.dumps({
                "id": "bound-144", "isDraft": not self.sent,
                "subject": "Changed" if self.changed else p["subject"],
                "body": {"contentType": "text", "content": p["body"]},
                "toRecipients": [{"emailAddress": {"address": p["recipient_email"]}}],
                "ccRecipients": [], "from": {"emailAddress": {"address": "sender@example.test"}},
                "sender": {"emailAddress": {"address": "sender@example.test"}},
                "internetMessageId": "<synthetic@test>", "sentDateTime": NOW if self.sent else None,
            }), {}
        raise AssertionError((method, url))


class OutlookContractTests(unittest.TestCase):
    def test_reconciliation_successor_uses_real_builder_and_preserves_graph_lineage(self):
        service = MemoryDraftService()
        service.generate_governed_client_response_draft(rental_case_id=424, use_deterministic_fixture=True)
        snapshot = service._require_case_snapshot(424)
        action = snapshot.workflow_actions[-1]
        revision = service.revisions[144]
        approval = snapshot.approval_requests[-1]
        prepared = _OutlookHumanEditReconciliationPlan(424, revision, snapshot, action, approval, "trusted-144", ())
        graph_read = _OutlookHumanEditGraphRead(OutlookDraftSnapshot(outcome="found", message_id="trusted-144",
            subject=revision.subject, body=revision.body_text + "\nThank you for your patience.",
            body_content_type="text", to_recipients=(revision.recipient_email,), is_draft=True), "sender@example.test")
        with patch("urllib.request.urlopen", side_effect=AssertionError("Network prohibited")):
            result = service.apply_outlook_reconciliation(prepared, graph_read)
        self.assertTrue(result.success, result.failure_codes)
        successor = service._require_case_snapshot(424).workflow_actions[-1]
        value = validate_outlook_action(successor)
        self.assertNotEqual(successor.workflow_action_id, action.workflow_action_id)
        self.assertEqual(value.draft_revision_id, 145)
        self.assertEqual(value.provenance, "outlook_human_edit")
        self.assertEqual(value.graph_message_id, "trusted-144")
        self.assertEqual(set(successor.structured_payload), set(action.structured_payload))
        self.assertEqual(service._require_case_snapshot(424).approval_requests[-1].status, "open")
        projected = service._project_governed_outlook_execution_action(service._require_case_snapshot(424), action=successor)
        self.assertEqual(projected.structured_payload, successor.structured_payload)

    def test_console_simulation_registry_uses_governance_and_synthetic_transport(self):
        case, revision, reservation, action = canonical_fixture()
        service = TestConsoleService(orchestration_repository=make_repo(case, actions=(action,)),
                                     observation_repository=SimpleNamespace(), now=lambda: NOW)
        checked = []
        def deny(action, context, payload):
            checked.append(action.workflow_action_id)
            return "outlook_send_governance_invalid", "test-denied"
        registry = service._build_execution_registry(action=action, execution_mode="success",
                                                     provider_action=action, outlook_pre_send_validator=deny)
        adapter = registry.resolve("outlook")
        with patch("urllib.request.urlopen", side_effect=AssertionError("Network prohibited")):
            result = adapter.execute(action=action, execution_context=SimpleNamespace(prior_attempts=()), idempotency=None)
        self.assertEqual(result.failure_code, "outlook_send_governance_invalid")
        self.assertEqual(checked, [587])
        self.assertEqual(adapter.delegate.transport.calls, [])

    def test_real_generation_and_deterministic_fixture_share_canonical_builder(self):
        schemas = []
        for deterministic in (False, True):
            service = MemoryDraftService()
            with patch("urllib.request.urlopen", side_effect=AssertionError("Network prohibited")):
                report = service.generate_governed_client_response_draft(rental_case_id=424, use_deterministic_fixture=deterministic)
                self.assertTrue(report.success)
                action = service._require_case_snapshot(424).workflow_actions[-1]
                validate_outlook_action(action)
                self.assertEqual(action.structured_payload["draft_revision_id"], 144)
                schemas.append(set(action.structured_payload))
                repeat = service.generate_governed_client_response_draft(rental_case_id=424, use_deterministic_fixture=deterministic)
                self.assertTrue(repeat.success)
                self.assertEqual(len(service.revisions), 1)
                self.assertEqual(len(service._require_case_snapshot(424).workflow_actions), 1)
        self.assertEqual(schemas[0], schemas[1])

    def test_malformed_inputs_fail_before_attempt_creation(self):
        case, revision, reservation, action = canonical_fixture(path="recovery")
        for field in ("response_intent", "purpose", "reason", "conversation_key", "draft_revision_id",
                      "graph_message_id", "draft_content_hash", "context_hash", "recipient_identity_hash"):
            with self.subTest(field=field):
                payload = dict(action.structured_payload)
                del payload[field]
                malformed = replace(action, status="ready_to_execute", structured_payload=payload)
                repo = make_repo(case, actions=(malformed,))
                result = execute_workflow_action(repo, WorkflowActionExecutionRequest(rental_case_id=424,
                    workflow_action_id=action.workflow_action_id, actor_reference="test"), adapter_registry=ExecutionAdapterRegistry())
                self.assertEqual(result.failure_codes, ("invalid_execution_input",))
                self.assertIsNone(result.execution_attempt_id)
                self.assertEqual(repo.execution_attempts[424], [])
    def test_all_paths_have_identical_executable_schema(self):
        keys = []
        for path in ("normal", "human_edit", "recovery", "deterministic_fixture"):
            case, revision, reservation, action = canonical_fixture(path=path)
            repo = make_repo(case, actions=(reservation,))
            persisted = repo.bind_outlook_action(reservation, action)
            self.assertEqual(persisted, action)
            _validate_action_payload(action.action_type, action.structured_payload)
            validate_outlook_action(action)
            keys.append(set(action.structured_payload))
        self.assertTrue(all(key == keys[0] for key in keys))

    def test_every_required_field_is_rejected_when_missing_or_null(self):
        action = canonical_fixture(path="recovery")[3]
        for key in action.structured_payload:
            for mode in ("missing", "null"):
                with self.subTest(field=key, mode=mode):
                    payload = dict(action.structured_payload)
                    if mode == "null" and payload[key] is None:
                        continue
                    if mode == "missing":
                        del payload[key]
                    else:
                        payload[key] = None
                    with self.assertRaises(OutlookContractError):
                        validate_outlook_action(replace(action, structured_payload=payload))

    def test_identity_is_stable_through_every_lifecycle_status(self):
        action = canonical_fixture()[3]
        for status in ("awaiting_approval", "approved", "ready_to_execute", "executing", "succeeded", "failed"):
            self.assertEqual(validate_outlook_action(replace(action, status=status)).idempotency_key(), action.idempotency_key)
        self.assertEqual(action.idempotency_key, canonical_fixture()[3].idempotency_key)
        for kwargs in ({"revision_id": 145}, {"content_hash": "different"}, {"path": "recovery"}):
            self.assertNotEqual(action.idempotency_key, canonical_fixture(**kwargs)[3].idempotency_key)

    def test_reservations_and_historical_actions_cannot_execute_or_be_rebound(self):
        case, revision, reservation, action = canonical_fixture()
        with self.assertRaises(OutlookContractError):
            validate_outlook_action(reservation)
        repo = make_repo(case, actions=(replace(action, status="failed"),))
        with self.assertRaises(OutlookContractError):
            repo.bind_outlook_action(reservation, action)
        self.assertEqual(repo.load_case_snapshot(424).workflow_actions[0].status, "failed")

    def run_lifecycle(self, path, *, negative=None, unrelated_attempt=False):
        case, revision, reservation, action = canonical_fixture(path=path)
        repo = make_repo(case, actions=(reservation,))
        action = repo.bind_outlook_action(reservation, action)
        if unrelated_attempt:
            from tools.phase_08_workflow.tests.test_outlook_adapter import make_prior_attempt
            repo.execution_attempts[424].append(replace(make_prior_attempt(), rental_case_id=424, workflow_action_id=582))
        if path == "recovery":
            origin = replace(action, workflow_action_id=586, status="failed")
            repo.workflow_actions[424].insert(0, origin)
        service = TestConsoleService(orchestration_repository=repo, observation_repository=SimpleNamespace(),
            config=TestConsoleConfig(runtime=AppRuntimeConfig(app_env=AppEnvironment.STAGING,
                staging_allowed_email_recipients=(revision.recipient_email,))), now=lambda: NOW)
        service._require_case_snapshot = repo.load_case_snapshot
        if path in {"recovery", "human_edit"}:
            repo.create_workflow_event(rental_case_id=424, event_type_code="outlook_human_edit_revision_created",
                source_type="test", source_reference="test", actor_type="system", actor_reference="test",
                occurred_at=NOW, event_identity_key="test-human-edit", structured_payload={
                    "workflow_action_id": revision.workflow_action_id, "draft_revision_id": 144,
                    "graph_message_id": "bound-144"})
        # Build and decide an actual exact approval in the in-memory repository.
        approval = service._replace_draft_approval(rental_case_id=424, workflow_action=action,
                                                   revision=revision, superseded_revision=None)
        result = apply_approval_decision(repo, ApprovalDecisionInput(rental_case_id=424,
            approval_request_id=approval.approval_request_id, decision="approved", expected_case_revision=3,
            actor_reference="test", actor_type="system", decided_at=NOW), now=lambda: NOW)
        self.assertFalse(result.failure_codes)
        revision = replace(revision, draft_status="send_failed" if path == "recovery" else "approved")
        action = repo.load_case_snapshot(424).find_workflow_action(action.workflow_action_id)
        self.assertEqual(action.status, "ready_to_execute")
        current_hash = action.structured_payload["governed_context_hash"]
        if negative == "wrong_revision": revision = replace(revision, inquiry_response_draft_revision_id=145)
        if negative == "stale_context": current_hash = "stale"
        if negative == "recipient_changed": revision = replace(revision, recipient_email="other@example.test")
        if negative == "content_changed": revision = replace(revision, body_text="Different")
        if negative == "blocking_annotation": revision = replace(revision, context_payload={"operator_annotations": [{"blocking": True}]})
        if negative == "old_approval":
            repo.approval_requests[424][0] = replace(repo.approval_requests[424][0],
                target_entity_id=586, target_entity_reference="workflow_action:586:draft_revision:144")
        if negative == "wrong_approval_target_id":
            repo.approval_requests[424][0] = replace(repo.approval_requests[424][0], target_entity_id=586)
        if negative == "historical_action":
            action = replace(action, status="failed")
            repo.workflow_actions[424][-1] = action
        transport = SyntheticTransport(action, changed=negative == "snapshot_changed")
        adapter = OutlookExecutionAdapter(config=OutlookAdapterConfig(tenant_id="test", client_id="test",
            client_secret="test", sender_mailbox="sender@example.test"), transport=transport,
            send_enabled=negative != "send_disabled", pre_send_validator=service._validate_governed_outlook_pre_send)
        request = WorkflowActionExecutionRequest(rental_case_id=424, workflow_action_id=action.workflow_action_id,
                                                 actor_reference="test", started_at=NOW)
        with patch.object(service, "_load_draft_revision_by_id", side_effect=lambda _case, ident: revision if ident == revision.inquiry_response_draft_revision_id else None), patch.object(
            service, "_build_current_governed_draft_contract", side_effect=lambda _case: (
                None, repo.load_case_snapshot(424), SimpleNamespace(context_hash=current_hash))):
            registry = ExecutionAdapterRegistry({"outlook": _ProjectedWorkflowActionExecutionAdapter(adapter, action)})
            with patch("urllib.request.urlopen", side_effect=AssertionError("Network prohibited")):
                result = execute_workflow_action(repo, request, adapter_registry=registry, now=lambda: NOW)
                if negative is None:
                    self.assertFalse(result.failure_codes)
                    self.assertEqual(result.action_status_after, "succeeded")
                    self.assertEqual(result.attempt_status, "succeeded")
                    self.assertTrue(transport.sent)
                    calls = list(transport.calls)
                    replay = execute_workflow_action(repo, request, adapter_registry=registry, now=lambda: NOW)
                    self.assertEqual(replay.failure_codes, ("action_already_succeeded",))
                    self.assertEqual(transport.calls, calls)
                    self.assertEqual(len(repo.list_execution_attempts(rental_case_id=424, workflow_action_id=action.workflow_action_id)), 1)
                else:
                    self.assertTrue(result.failure_codes or result.attempt_status == "failed")
                    self.assertFalse(transport.sent)
                    if negative in {"old_approval", "wrong_approval_target_id", "historical_action"}:
                        self.assertIsNone(result.execution_attempt_id)
                        self.assertEqual(transport.calls, [])
                    elif negative not in {"send_disabled", "snapshot_changed"}:
                        self.assertIsNotNone(result.execution_attempt_id)
                        self.assertEqual(transport.calls, [])
                    else:
                        self.assertIsNotNone(result.execution_attempt_id)
        return result

    def test_normal_full_lifecycle(self): self.run_lifecycle("normal")
    def test_human_edit_full_lifecycle(self): self.run_lifecycle("human_edit")
    def test_recovery_full_lifecycle(self): self.run_lifecycle("recovery")
    def test_unrelated_historical_attempt_cannot_supply_a_new_actions_graph_id(self):
        self.run_lifecycle("normal", unrelated_attempt=True)

    def test_negative_full_lifecycles(self):
        for path in ("normal", "human_edit", "recovery"):
            for negative in ("wrong_revision", "stale_context", "old_approval", "recipient_changed", "content_changed",
                             "historical_action", "send_disabled", "snapshot_changed", "blocking_annotation", "wrong_approval_target_id"):
                with self.subTest(path=path, negative=negative):
                    self.run_lifecycle(path, negative=negative)


if __name__ == "__main__": unittest.main()
