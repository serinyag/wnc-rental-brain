"""Normal Phase 8 execution proofs with a stateful, provider-free Google fake."""
import copy
import io
from dataclasses import replace
from unittest.mock import patch
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest

from tools.runtime_environment import AppRuntimeConfig, AppEnvironment
from tools.phase_08_workflow.google_proposal import (
    ADAPTER, build_projection, binding, prepare_projection, proposal_send_block, render_template, W)
from tools.phase_08_workflow.google_proposal_adapter import (
    GoogleProposalAdapter, GoogleProposalConfig, GoogleTransport, GoogleFailure, DOC_MIME, paragraphs)
from tools.phase_08_workflow.execution_runtime import execute_workflow_action, ExecutionAdapterRegistry
from tools.phase_08_workflow.execution_types import WorkflowActionExecutionRequest
from tools.phase_08_workflow.tests.test_asana_projection import synthetic_repo, NOW, update_case
from tools.phase_08_workflow.tests.test_working_proposal import add_fact
from tools.phase_08_workflow.asana_projection import build_projection as asana, NUANCED_VERSION
from tools.phase_08_workflow.contracts import CaseDecision, ApprovalRequest


def native(texts, doc_id='doc_001', revision='revision_1'):
    index = 1
    content = []
    for text in texts:
        end = index + len((text+'\n').encode('utf-16-le'))//2
        content.append({'startIndex': index, 'endIndex': end, 'paragraph': {'paragraphStyle': {'namedStyleType': 'NORMAL_TEXT'},
            'elements': [{'startIndex': index, 'endIndex': end, 'textRun': {'content': text+'\n', 'textStyle': {}}}]}})
        index = end
    return {'documentId': doc_id, 'revisionId': revision, 'body': {'content': content}, 'documentStyle': {'background': {}}}


class FakeGoogle:
    def __init__(self):
        self.files = {}; self.documents = {}; self.mutations = []; self.failure = None; self.before_write = None

    def metadata(self, file_id):
        if file_id == 'folder_001':
            return {'id': file_id, 'mimeType': 'application/vnd.google-apps.folder', 'appProperties': {'wnc_environment': 'staging'}}
        return copy.deepcopy(self.files[file_id])

    def find(self, proposal_identity):
        return [copy.deepcopy(m) for m in self.files.values()
                if m['appProperties']['wnc_proposal_identity'] == proposal_identity]

    def get(self, doc_id):
        if doc_id not in self.documents: raise GoogleFailure('google_http_404')
        return copy.deepcopy(self.documents[doc_id])

    def create(self, plan, docx):
        with ZipFile(io.BytesIO(docx)) as archive:
            tree = ET.fromstring(archive.read('word/document.xml'))
        texts = [''.join(n.text or '' for n in p.iter(W+'t')) for p in tree.iter(W+'p')]
        doc_id = f'doc_{len(self.documents)+1:03}'
        self.documents[doc_id] = native(texts, doc_id)
        self.files[doc_id] = {'id': doc_id, 'mimeType': DOC_MIME, 'parents': [plan['folder_id']], 'appProperties': {
            'wnc_proposal_identity': plan['proposal_identity'], 'wnc_provider_identity': plan['provider_identity'],
            'wnc_environment': 'staging'}}
        self.mutations.append(('create', doc_id))
        if self.failure == 'timeout_create': raise GoogleFailure('timeout', ambiguous=True)
        return {'id': doc_id}

    def update(self, doc_id, requests, revision):
        if self.before_write: self.before_write()
        doc = self.documents[doc_id]
        if revision != doc['revisionId']: raise GoogleFailure('google_http_400')
        if self.failure == 'update_failure': raise GoogleFailure('google_http_503', ambiguous=True)
        # Apply native UTF-16 requests against paragraph indices, preserving the
        # terminal newline exactly as the Docs API requires.
        texts = [p[2] for p in paragraphs(doc)]
        indexed = paragraphs(doc)
        for request in requests:
            if 'deleteContentRange' in request:
                r = request['deleteContentRange']['range']; start = r['startIndex']
                i = next(i for i,p in enumerate(indexed) if p[0] == start)
                texts[i] = ''
            else:
                r = request['insertText']; start = r['location']['index']
                i = next(i for i,p in enumerate(indexed) if p[0] == start)
                texts[i] = r['text']
        number = int(doc['revisionId'].split('_')[-1])+1
        self.documents[doc_id] = native(texts, doc_id, f'revision_{number}')
        self.mutations.append(('update', doc_id))
        return {'documentId': doc_id, 'writeControl': {'requiredRevisionId': f'revision_{number}'}}


@pytest.fixture(autouse=True)
def no_network():
    with patch('urllib.request.urlopen', side_effect=AssertionError('Network prohibited')), \
         patch('tools.phase_08_workflow.google_proposal_adapter.urlopen', side_effect=AssertionError('Network prohibited')):
        yield


def harness():
    repo = synthetic_repo(); provider = FakeGoogle()
    config = GoogleProposalConfig('fake-staging-client', 'fake-secret', 'fake-refresh', 'folder_001')
    runtime = AppRuntimeConfig(app_env=AppEnvironment.STAGING, staging_allow_real_google=True,
        staging_allowed_google_folder_ids=('folder_001',))
    return repo, provider, GoogleProposalAdapter(config, provider, repo, runtime)


def prepare(repo, adapter):
    return prepare_projection(repo, rental_case_id=1, folder_id=adapter.config.folder_id,
        provider_identity=adapter.config.provider_identity, now=NOW)


def execute(repo, adapter, action=None):
    action = action or prepare(repo, adapter)
    return execute_workflow_action(repo, WorkflowActionExecutionRequest(1, action.workflow_action_id, 'synthetic_operator'),
        adapter_registry=ExecutionAdapterRegistry({ADAPTER: adapter}), now=lambda: NOW)


def test_one_document_persisted_through_normal_execution_and_replay_across_restart():
    repo, provider, adapter = harness(); action = prepare(repo, adapter)
    assert execute(repo, adapter, action).action_status_after == 'succeeded'
    b = binding(repo.load_case_snapshot(1))
    assert b['document_id'] == b['file_id'] == 'doc_001'
    assert b['source_case_revision'] == 0 and b['last_synchronized_at'] and len(b['projection_hash']) == 64
    restarted = GoogleProposalAdapter(adapter.config, provider, repo, adapter.runtime)
    assert execute(repo, restarted, prepare(repo, restarted)).already_succeeded_idempotently
    assert provider.mutations == [('create', 'doc_001')]
    assert restarted.observe(action=action)['status'] == 'MATCHES_PROJECTION'


@pytest.mark.parametrize('field,value', [('guest_count', 30), ('event_schedule', {'date': '2026-11-13'}),
    ('requested_rental_scope', 'entire_venue'), ('catering_arrangement', 'wnc_vendor'),
    ('technical_requirements', ['microphones']), ('production_scope', 'full_production')])
def test_changed_public_scope_updates_same_document(field, value):
    repo, provider, adapter = harness(); assert execute(repo, adapter).action_status_after == 'succeeded'
    repo.rental_cases[1] = replace(repo.rental_cases[1], case_revision=1)
    add_fact(repo, field, value, 1)
    action = prepare(repo, adapter)
    result = execute(repo, adapter, action)
    assert result.action_status_after == 'succeeded', result
    assert provider.mutations == [('create', 'doc_001'), ('update', 'doc_001')]
    assert binding(repo.load_case_snapshot(1))['source_case_revision'] == 1
    assert adapter.observe(action=action)['status'] == 'MATCHES_PROJECTION'
    assert execute(repo, adapter, action).already_succeeded_idempotently


def test_unrelated_case_revision_requires_new_journal_record_but_no_provider_write():
    repo, provider, adapter = harness(); execute(repo, adapter)
    repo.rental_cases[1] = replace(repo.rental_cases[1], case_revision=1)
    assert execute(repo, adapter).action_status_after == 'succeeded'
    assert provider.mutations == [('create', 'doc_001')]
    assert binding(repo.load_case_snapshot(1))['source_case_revision'] == 1


def test_requested_facts_and_example_template_confirmations_are_never_authority():
    repo, _, adapter = harness(); add_fact(repo, 'financial_summary', {'price': 999999})
    add_fact(repo, 'internal_reasoning', 'SECRET INTERNAL TRACE')
    plan = build_projection(repo.load_case_snapshot(1), folder_id='folder_001', provider_identity=adapter.config.provider_identity)
    _, text = render_template(plan)
    content = '\n'.join(text)
    assert '999999' not in content and 'SECRET INTERNAL TRACE' not in content
    assert '24 (TBC)' in content and 'Pricing and applicable fees: TBC' in content
    assert 'catering]\nConfirmed' not in content and '21%' not in content


def commercial(repo, adapter, status='approved', amount=100):
    d = CaseDecision(50, 1, 'booking_fee_override', 'commercial', 'governed_booking_fee',
        {'booking_fee': amount, 'currency': 'EUR'}, 'booking_fee', 'Booking fee', 'case_specific_exception',
        'approval_required', 'active', NOW, effective_value_payload={'booking_fee': amount, 'currency': 'EUR'},
        evidence_reference='operator:approved', approval_request_id=51, effective_at=NOW)
    a = ApprovalRequest(51, 1, 'case_decision', 'commercial_review', 'Review fee', status, NOW,
        target_entity_id=50, decided_at=NOW if status == 'approved' else None)
    repo.case_decisions[1] = [d]; repo.approval_requests[1] = [a]


def test_approved_commercial_change_updates_same_document_pending_price_excluded():
    repo, provider, adapter = harness(); execute(repo, adapter)
    commercial(repo, adapter, 'open', 777)
    plan = prepare(repo, adapter).structured_payload['projection']
    assert '777' not in plan['sections']['Financial Summary']
    repo.rental_cases[1] = replace(repo.rental_cases[1], case_revision=1)
    commercial(repo, adapter, amount=125)
    assert execute(repo, adapter).action_status_after == 'succeeded'
    assert '125' in '\n'.join(p[2] for p in paragraphs(provider.get('doc_001')))
    assert len(provider.documents) == 1


def test_stale_prepared_revision_never_creates_document():
    repo, provider, adapter = harness(); action = prepare(repo, adapter); update_case(repo)
    assert execute(repo, adapter, action).action_status_after != 'succeeded'
    assert not provider.mutations


def test_case_changed_during_provider_reads_is_checked_before_write():
    repo, provider, adapter = harness(); action = prepare(repo, adapter)
    original = provider.find
    def read(identity):
        result = original(identity); update_case(repo); return result
    provider.find = read
    assert execute(repo, adapter, action).action_status_after != 'succeeded'
    assert not provider.mutations


def test_ambiguous_create_fences_later_revisions_and_observation_discovers_without_rebinding():
    repo, provider, adapter = harness(); provider.failure = 'timeout_create'
    action = prepare(repo, adapter); result = execute(repo, adapter, action)
    assert repo.load_case_snapshot(1).execution_attempts[-1].failure_code == 'adapter_outcome_ambiguous' and not result.retry_eligible
    assert adapter.observe(action=action)['document_id'] == 'doc_001'
    assert adapter.observe(action=action)['status'] == 'AMBIGUOUS'
    update_case(repo); execute(repo, adapter)
    assert provider.mutations == [('create', 'doc_001')]
    assert binding(repo.load_case_snapshot(1)) is None


@pytest.mark.parametrize('kind', ['text', 'format', 'missing', 'wrong_case', 'wrong_folder', 'duplicate'])
def test_reconciliation_preserves_provider_drift_and_never_imports_truth(kind):
    repo, provider, adapter = harness(); action = prepare(repo, adapter); execute(repo, adapter, action)
    before = copy.deepcopy(repo.rental_case_facts)
    if kind == 'text': provider.documents['doc_001']['body']['content'][0]['paragraph']['elements'][0]['textRun']['content'] = 'Edited price\n'
    if kind == 'format': provider.documents['doc_001']['documentStyle']['background'] = {'color': 'red'}
    if kind == 'missing': provider.files.clear(); provider.documents.clear()
    if kind == 'wrong_case': provider.files['doc_001']['appProperties']['wnc_proposal_identity'] = 'another_case'
    if kind == 'wrong_folder': provider.files['doc_001']['parents'] = ['live_folder']
    if kind == 'duplicate': provider.files['doc_002'] = {**copy.deepcopy(provider.files['doc_001']), 'id': 'doc_002'}
    evidence = adapter.observe(action=action)
    assert evidence['status'] != 'MATCHES_PROJECTION' and not evidence['business_truth_changed']
    repo.rental_cases[1] = replace(repo.rental_cases[1], case_revision=1)
    assert execute(repo, adapter).action_status_after == 'failed'
    assert provider.mutations == [('create', 'doc_001')]
    assert repo.rental_case_facts == before and proposal_send_block(repo.load_case_snapshot(1))


def test_update_failure_keeps_original_binding_and_blocks_send_and_replay():
    repo, provider, adapter = harness(); execute(repo, adapter); update_case(repo)
    provider.failure = 'update_failure'; result = execute(repo, adapter)
    assert repo.load_case_snapshot(1).execution_attempts[-1].failure_code == 'adapter_outcome_ambiguous'
    assert binding(repo.load_case_snapshot(1))['document_id'] == 'doc_001'
    assert proposal_send_block(repo.load_case_snapshot(1))
    assert execute(repo, adapter).action_status_after == 'failed'
    assert len(provider.documents) == 1


def test_human_edit_between_read_and_update_is_blocked_by_provider_revision():
    repo, provider, adapter = harness(); execute(repo, adapter); update_case(repo)
    def edit(): provider.documents['doc_001']['revisionId'] = 'revision_99'
    provider.before_write = edit
    assert execute(repo, adapter).action_status_after == 'failed'
    assert provider.mutations == [('create', 'doc_001')]


@pytest.mark.parametrize('environment,enabled,folders', [('production', True, ('folder_001',)),
    ('local', True, ('folder_001',)), ('staging', False, ('folder_001',)), ('staging', True, ('other_folder',))])
def test_production_identity_and_disabled_gate_cannot_execute(environment, enabled, folders):
    repo, provider, adapter = harness()
    adapter.runtime = AppRuntimeConfig(app_env=AppEnvironment(environment), staging_allow_real_google=enabled,
        staging_allowed_google_folder_ids=folders)
    assert execute(repo, adapter).action_status_after != 'succeeded'
    assert not provider.mutations


def test_asana_references_verified_document_naturally():
    repo, _, adapter = harness(); execute(repo, adapter)
    result = asana(repo.load_case_snapshot(1), workspace_gid='111', project_gid='222', version=NUANCED_VERSION)
    notes = result['master']['notes']
    assert 'https://docs.google.com/document/d/doc_001/edit' in notes
    assert 'Status: Current' in notes and 'provider_identity' not in notes
    update_case(repo)
    result = asana(repo.load_case_snapshot(1), workspace_gid='111', project_gid='222', version=NUANCED_VERSION)
    assert 'Needs review / synchronization' in result['master']['notes']


@pytest.mark.parametrize('scope', ['studio_space','entire_venue','production_coordination','full_production','custom_scope'])
def test_existing_word_templates_render_with_seven_sections_and_no_example_content(scope):
    repo, _, adapter = harness(); add_fact(repo, 'requested_rental_scope', scope)
    plan = prepare(repo, adapter).structured_payload['projection']; _, lines = render_template(plan)
    assert sum(line.startswith(tuple(str(i)+'. ' for i in range(1,8))) for line in lines) == 7
    assert not any('[Action]' in line or '€[ ]' in line for line in lines)


def test_google_transport_uses_verified_tls_and_never_retries_unknown_mutation():
    import ssl
    repo, _, adapter = harness()
    transport = GoogleTransport(adapter.config)
    with patch('tools.phase_08_workflow.google_proposal_adapter.urlopen', return_value=io.BytesIO(b'{}')) as request:
        assert transport._http('GET', 'https://docs.googleapis.com/v1/documents/synthetic', auth=False) == {}
        context = request.call_args.kwargs['context']
        assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
    with patch('tools.phase_08_workflow.google_proposal_adapter.urlopen', side_effect=TimeoutError()) as request:
        with pytest.raises(GoogleFailure) as result:
            transport._http('POST', 'https://www.googleapis.com/upload/drive/v3/files', auth=False)
        assert result.value.ambiguous and request.call_count == 1
