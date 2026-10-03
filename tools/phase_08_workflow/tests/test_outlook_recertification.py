"""Current application lifecycle with only storage/model/HTTP transport substituted."""
from dataclasses import replace
from unittest.mock import patch
import pytest
from tools.phase_08_workflow.tests.test_outlook_action_contract import MemoryDraftService, NOW
from tools.phase_08_workflow.governed_client_response import ClientResponseDraft
from tools.phase_08_workflow.outlook_action_contract import validate_outlook_action
from tools.phase_08_workflow.outlook_adapter import OutlookDraftSnapshot
from tools.phase_08_workflow.test_console_service import (
    TestConsoleError, _OutlookHumanEditReconciliationPlan, _OutlookHumanEditGraphRead)


class SyntheticDrafter:
    def generate_client_response(self, contract):
        return ClientResponseDraft('SYNTHETIC Outlook certification',
            'Hi Synthetic,\n\nThis is a synthetic Outlook execution certification test. No rental booking is being made.')


class LifecycleService(MemoryDraftService):
    def __init__(self):
        super().__init__()
        self.client_response_provider = SyntheticDrafter()
        self.query_runner = lambda *a, **k: (_ for _ in ()).throw(AssertionError('Unexpected storage SQL'))
        self.transports = []

    def _list_draft_revisions(self, case_id):
        return tuple(self.revisions.values())

    def _load_draft_revision_by_approval_request_id(self, case_id, approval_id):
        return next((r for r in self.revisions.values() if r.approval_request_id == approval_id), None)

    def _update_draft_revision_status(self, *, rental_case_id, draft_revision_id, **values):
        revision = replace(self.revisions[draft_revision_id], **{k:v for k,v in values.items() if v is not None})
        self.revisions[draft_revision_id] = revision
        return revision

    def _build_execution_registry(self, **kwargs):
        registry = super()._build_execution_registry(**kwargs)
        self.transports.append(registry.resolve('outlook').delegate.transport)
        return registry


def generated_service():
    service = LifecycleService()
    report = service.generate_governed_client_response_draft(rental_case_id=424)
    assert report.success
    return service


def current(service):
    snap = service._require_case_snapshot(424)
    rev = next(r for r in service.revisions.values() if r.is_current)
    action = snap.find_workflow_action(rev.workflow_action_id)
    approval = snap.find_approval_request(rev.approval_request_id)
    return snap, rev, action, approval


def approve_execute_replay(service):
    snap, rev, action, approval = current(service)
    readiness = service.inspect_governed_outlook_send_readiness(rental_case_id=424, workflow_action_id=action.workflow_action_id)
    assert readiness.success and 'Recipient allowlist: pass' in readiness.lines
    assert 'Send gate: disabled' in readiness.lines
    assert approval.status == 'open' and action.status == 'awaiting_approval'
    assert service.approve_request(rental_case_id=424, approval_request_id=approval.approval_request_id).success
    snap, rev, action, approval = current(service)
    assert approval.status == 'approved' and action.status == 'ready_to_execute'
    value = validate_outlook_action(action)
    projected = service._project_governed_outlook_execution_action(snap, action=action)
    assert projected.structured_payload == value.to_payload()
    assert service.execute_action(rental_case_id=424, workflow_action_id=action.workflow_action_id, execution_mode='success').success
    snap, delivered, action, approval = current(service)
    assert delivered.draft_status == 'simulated_sent' and action.status == 'succeeded'
    assert len(snap.execution_attempts) == 1 and snap.execution_attempts[0].status == 'succeeded'
    calls = list(service.transports[-1].calls)
    assert sum(url.endswith('/send') for _,url in calls) == 1
    with pytest.raises(TestConsoleError):
        service.execute_action(rental_case_id=424, workflow_action_id=action.workflow_action_id, execution_mode='success')
    assert service.transports[-1].calls == calls
    assert len(service._require_case_snapshot(424).execution_attempts) == 1
    return {'action_status':'succeeded','draft_status':delivered.draft_status,'attempts':1,'fake_send_calls':1,'replay':'blocked','projection':'lossless','readiness':readiness.lines}


def test_fresh_generation_through_application_approval_execution_and_replay():
    with patch('urllib.request.urlopen', side_effect=AssertionError('Network prohibited')):
        approve_execute_replay(generated_service())


def test_human_edit_successor_through_same_full_lifecycle():
    with patch('urllib.request.urlopen', side_effect=AssertionError('Network prohibited')):
        service = generated_service()
        snap, original, action, approval = current(service)
        assert service.approve_request(rental_case_id=424, approval_request_id=approval.approval_request_id).success
        snap, original, action, approval = current(service)
        prepared = _OutlookHumanEditReconciliationPlan(424, original, snap, action, approval, 'synthetic-bound-id', ())
        read = _OutlookHumanEditGraphRead(OutlookDraftSnapshot(outcome='found', message_id='synthetic-bound-id',
            subject=original.subject, body=original.body_text+'\nHuman-reviewed synthetic text.', body_content_type='text',
            to_recipients=(original.recipient_email,), is_draft=True), 'sender@example.test')
        result = service.apply_outlook_reconciliation(prepared, read)
        assert result.success
        snap, successor, successor_action, successor_approval = current(service)
        assert not service.revisions[original.inquiry_response_draft_revision_id].is_current
        assert service.revisions[original.inquiry_response_draft_revision_id].body_text == original.body_text
        assert successor.content_hash != original.content_hash
        assert successor.supersedes_draft_revision_id == original.inquiry_response_draft_revision_id
        assert successor_approval.status == 'open' and successor_approval.target_entity_reference != approval.target_entity_reference
        value = validate_outlook_action(successor_action)
        assert value.provenance == 'outlook_human_edit' and value.graph_message_id == 'synthetic-bound-id'
        with pytest.raises(TestConsoleError):
            service.execute_action(rental_case_id=424, workflow_action_id=action.workflow_action_id, execution_mode='success')
        with pytest.raises(TestConsoleError):
            service.execute_action(rental_case_id=424, workflow_action_id=successor_action.workflow_action_id, execution_mode='success')
        assert not snap.execution_attempts
        approve_execute_replay(service)
