"""Staging-only Google adapter with durable ambiguity and manual-edit fences."""
from __future__ import annotations

import copy
import json
import re
import ssl
import certifi
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from tools.phase_05_search.semantic_common import load_env_value
from .asana_projection import digest
from .execution_types import NormalizedExecutionResult
from .google_proposal import ADAPTER, VERSION, attempts, binding, render_template, validate_projection

DOC_MIME = 'application/vnd.google-apps.document'
ID = re.compile(r'^[A-Za-z0-9_-]{3,200}$')


class GoogleFailure(Exception):
    def __init__(self, reason, *, ambiguous=False):
        self.reason, self.ambiguous = reason, ambiguous
        super().__init__(reason)


@dataclass(frozen=True)
class GoogleProposalConfig:
    client_id: str
    client_secret: str
    refresh_token: str
    folder_id: str

    @property
    def provider_identity(self):
        return 'staging:' + digest(self.client_id)

    @classmethod
    def from_env(cls):
        return cls(*(load_env_value(name) or '' for name in (
            'STAGING_GOOGLE_CLIENT_ID', 'STAGING_GOOGLE_CLIENT_SECRET',
            'STAGING_GOOGLE_REFRESH_TOKEN', 'STAGING_GOOGLE_PROPOSAL_FOLDER_ID')))


class GoogleTransport:
    """Fixed Google endpoints, no credential logging and no mutation retries."""
    def __init__(self, config):
        self.config = config
        self._token = None

    def _http(self, method, url, raw=None, content_type='application/json', auth=True):
        headers = {'Accept': 'application/json', 'Content-Type': content_type}
        if auth: headers['Authorization'] = 'Bearer ' + self.token()
        try:
            with urlopen(Request(url, data=raw, headers=headers, method=method), timeout=45,
                    context=ssl.create_default_context(cafile=certifi.where())) as response:
                data = response.read(8_000_001)
        except HTTPError as exc:
            raise GoogleFailure(f'google_http_{exc.code}', ambiguous=method != 'GET' and exc.code >= 500) from None
        except Exception:
            raise GoogleFailure('google_transport_unknown', ambiguous=method != 'GET') from None
        try:
            if len(data) > 8_000_000: raise ValueError()
            result = json.loads(data)
            if not isinstance(result, dict): raise ValueError()
            return result
        except (ValueError, TypeError):
            raise GoogleFailure('google_response_unverifiable', ambiguous=method != 'GET') from None

    def token(self):
        if not self._token:
            response = self._http('POST', 'https://oauth2.googleapis.com/token',
                urlencode({'client_id': self.config.client_id, 'client_secret': self.config.client_secret,
                    'refresh_token': self.config.refresh_token, 'grant_type': 'refresh_token'}).encode(),
                'application/x-www-form-urlencoded', auth=False)
            scopes = set(response.get('scope', '').split())
            if scopes != {'https://www.googleapis.com/auth/drive.file'} or not response.get('access_token'):
                raise GoogleFailure('google_scope_not_drive_file_only')
            self._token = response['access_token']
        return self._token

    def metadata(self, file_id):
        if not ID.fullmatch(file_id): raise GoogleFailure('invalid_google_identity')
        return self._http('GET', 'https://www.googleapis.com/drive/v3/files/'+file_id+'?'+urlencode({
            'fields': 'id,mimeType,parents,appProperties,trashed,version'}))

    def find(self, proposal_identity):
        q = "trashed = false and appProperties has { key='wnc_proposal_identity' and value='"+proposal_identity+"' }"
        files, page = [], None
        for _ in range(20):
            params = {'q': q, 'fields': 'files(id,mimeType,parents,appProperties,trashed,version),nextPageToken', 'pageSize': 100}
            if page: params['pageToken'] = page
            response = self._http('GET', 'https://www.googleapis.com/drive/v3/files?'+urlencode(params))
            files.extend(response.get('files', []))
            page = response.get('nextPageToken')
            if not page: return files
        raise GoogleFailure('google_identity_search_incomplete')

    def get(self, document_id):
        if not ID.fullmatch(document_id): raise GoogleFailure('invalid_google_identity')
        return self._http('GET', 'https://docs.googleapis.com/v1/documents/'+document_id+'?includeTabsContent=true')

    def create(self, plan, docx):
        metadata = {'name': plan['title'], 'mimeType': DOC_MIME, 'parents': [plan['folder_id']],
            'appProperties': {'wnc_proposal_identity': plan['proposal_identity'],
                'wnc_provider_identity': plan['provider_identity'], 'wnc_environment': 'staging'}}
        boundary = 'wnc_proposal_multipart_v1'
        raw = (('--'+boundary+'\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n').encode()
            +json.dumps(metadata).encode()+('\r\n--'+boundary+'\r\nContent-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document\r\n\r\n').encode()
            +docx+('\r\n--'+boundary+'--\r\n').encode())
        return self._http('POST', 'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id',
                          raw, 'multipart/related; boundary='+boundary)

    def update(self, document_id, requests, revision):
        return self._http('POST', 'https://docs.googleapis.com/v1/documents/'+document_id+':batchUpdate',
            json.dumps({'requests': requests, 'writeControl': {'requiredRevisionId': revision}}).encode())


def paragraphs(document):
    """Flatten native paragraphs, preserving Docs' UTF-16 character indices."""
    result = []
    def walk(content):
        for item in content:
            if 'paragraph' in item:
                elements = item['paragraph'].get('elements', [])
                if any(set(e) - {'startIndex', 'endIndex', 'textRun'} for e in elements):
                    raise GoogleFailure('unsupported_document_content')
                text = ''.join(e.get('textRun', {}).get('content', '') for e in elements)
                if not text.endswith('\n'): raise GoogleFailure('unsupported_document_paragraph')
                result.append((item['startIndex'], item['endIndex']-1, text[:-1]))
            elif 'table' in item:
                for row in item['table']['tableRows']:
                    for cell in row['tableCells']: walk(cell['content'])
    tabs = document.get('tabs', [])
    if tabs:
        if len(tabs) != 1 or tabs[0].get('childTabs') or 'documentTab' not in tabs[0]:
            raise GoogleFailure('document_tabs_require_review')
        walk(tabs[0]['documentTab'].get('body', {}).get('content', []))
    else:
        walk(document.get('body', {}).get('content', []))
    return result


def fingerprint(document):
    # Revision itself is volatile. Body, styles, headers, footers and suggestions
    # remain included so formatting-only human changes are also detected.
    return digest({k: v for k, v in document.items() if k not in {'documentId', 'revisionId'}})


@dataclass
class GoogleProposalAdapter:
    config: GoogleProposalConfig
    transport: object
    repository: object
    runtime: object

    def _scope(self, mutation=False):
        if (not self.runtime.is_staging or not all((self.config.client_id, self.config.client_secret,
                self.config.refresh_token, self.config.folder_id))
                or self.config.folder_id not in self.runtime.staging_allowed_google_folder_ids
                or not ID.fullmatch(self.config.folder_id)
                or mutation and not self.runtime.staging_allow_real_google):
            raise GoogleFailure('google_staging_scope_or_gate_invalid')

    def _plan(self, action):
        snapshot = self.repository.load_case_snapshot(action.rental_case_id)
        return snapshot, validate_projection(action, snapshot, self.config)

    def availability_failure_code(self, *, action):
        try:
            self._scope(True)
            snapshot, _ = self._plan(action)
            if any(a.status == 'started' or (a.status != 'succeeded' and not a.retry_eligible) for a in attempts(snapshot)):
                return 'adapter_outcome_ambiguous'
        except (GoogleFailure, ValueError, AttributeError, KeyError):
            return 'adapter_forbidden'
        return None

    def _verify_identity(self, metadata, plan):
        if (not ID.fullmatch(metadata.get('id', '')) or metadata.get('mimeType') != DOC_MIME
                or metadata.get('trashed') or metadata.get('parents') != [plan['folder_id']]
                or metadata.get('appProperties', {}).get('wnc_proposal_identity') != plan['proposal_identity']
                or metadata.get('appProperties', {}).get('wnc_provider_identity') != plan['provider_identity']
                or metadata.get('appProperties', {}).get('wnc_environment') != 'staging'):
            raise GoogleFailure('google_binding_conflict')

    def _locate(self, plan, existing):
        matches = self.transport.find(plan['proposal_identity'])
        if len(matches) > 1: raise GoogleFailure('google_duplicate_identity', ambiguous=True)
        if not matches: raise GoogleFailure('google_document_missing')
        self._verify_identity(matches[0], plan)
        if existing and (existing.get('document_id') != matches[0]['id']
                or existing.get('provider_identity') != plan['provider_identity']
                or existing.get('proposal_identity') != plan['proposal_identity']
                or existing.get('rental_case_id') != plan['rental_case_id']):
            raise GoogleFailure('google_binding_conflict')
        return matches[0]

    def execute(self, *, action, execution_context, idempotency):
        existing = None
        mutation_started = False
        mutations = 0
        try:
            self._scope(True)
            snapshot, plan = self._plan(action)
            existing = copy.deepcopy(binding(snapshot))
            if any(a.execution_attempt_id != idempotency.execution_attempt_id and
                    (a.status == 'started' or (a.status != 'succeeded' and not a.retry_eligible)) for a in attempts(snapshot)):
                raise GoogleFailure('google_requires_reconciliation', ambiguous=True)
            folder = self.transport.metadata(plan['folder_id'])
            if (folder.get('id') != plan['folder_id'] or folder.get('mimeType') != 'application/vnd.google-apps.folder'
                    or folder.get('trashed') or folder.get('appProperties', {}).get('wnc_environment') != 'staging'):
                raise GoogleFailure('google_staging_folder_invalid')
            docx, desired = render_template(plan)
            if not existing:
                # An orphan from an ambiguous request requires explicit review;
                # never bind by title and never blindly make a second document.
                matches = self.transport.find(plan['proposal_identity'])
                if matches: raise GoogleFailure('google_unbound_identity_requires_review', ambiguous=True)
                self._plan(action)  # Last canonical read immediately before mutation.
                mutation_started = True
                mutations += 1
                created = self.transport.create(plan, docx)
                if not ID.fullmatch(created.get('id', '')):
                    raise GoogleFailure('google_create_unverifiable', ambiguous=True)
                existing = {'rental_case_id': plan['rental_case_id'], 'proposal_identity': plan['proposal_identity'],
                    'provider_identity': plan['provider_identity'], 'folder_id': plan['folder_id'],
                    'file_id': created['id'], 'document_id': created['id'], 'template': plan['template']}
                self._locate(plan, existing)
                document = self.transport.get(existing['document_id'])
            else:
                self._locate(plan, existing)
                document = self.transport.get(existing['document_id'])
                if document.get('documentId') != existing['document_id'] or fingerprint(document) != existing.get('document_fingerprint'):
                    raise GoogleFailure('google_manual_drift_review_required')
                actual = paragraphs(document)
                if len(actual) != len(desired): raise GoogleFailure('google_layout_requires_review')
                requests = []
                tab_id = document.get('tabs', [{}])[0].get('tabProperties', {}).get('tabId')
                tab_scope = {'tabId': tab_id} if tab_id else {}
                for (start, end, before), after in reversed(list(zip(actual, desired))):
                    if before == after: continue
                    if end > start: requests.append({'deleteContentRange': {'range': {'startIndex': start, 'endIndex': end, **tab_scope}}})
                    if after: requests.append({'insertText': {'location': {'index': start, **tab_scope}, 'text': after}})
                if requests:
                    if not document.get('revisionId'): raise GoogleFailure('google_revision_missing')
                    self._plan(action)
                    mutation_started = True
                    mutations += 1
                    updated = self.transport.update(existing['document_id'], requests, document['revisionId'])
                    document = self.transport.get(existing['document_id'])
                    if document.get('revisionId') != updated.get('writeControl', {}).get('requiredRevisionId'):
                        raise GoogleFailure('google_post_write_revision_unverifiable', ambiguous=True)
            if document.get('documentId') != existing['document_id'] or [p[2] for p in paragraphs(document)] != desired:
                raise GoogleFailure('google_content_verification_failed', ambiguous=mutation_started)
            existing.update(projection_hash=plan['projection_hash'], source_case_revision=plan['source_case_revision'],
                document_fingerprint=fingerprint(document), provider_revision=document.get('revisionId'),
                last_synchronized_at=datetime.now(timezone.utc).isoformat())
            return NormalizedExecutionResult(adapter_code=ADAPTER, attempt_status='succeeded',
                external_reference=f'google:proposal:{action.rental_case_id}:{idempotency.execution_attempt_id}', response_snapshot={'binding': existing,
                    'status': 'MATCHES_PROJECTION', 'mutation_requests': mutations, 'business_truth_changed': False})
        except Exception as exc:
            reason = exc.reason if isinstance(exc, GoogleFailure) else 'google_projection_invalid'
            ambiguous = mutation_started or isinstance(exc, GoogleFailure) and exc.ambiguous
            return NormalizedExecutionResult(adapter_code=ADAPTER, attempt_status='failed', retry_eligible=False,
                failure_code='adapter_outcome_ambiguous' if ambiguous else 'adapter_forbidden',
                response_snapshot={'binding': existing, 'status': 'AMBIGUOUS' if ambiguous else 'DRIFT_DETECTED',
                    'reason': reason, 'mutation_requests': mutations, 'business_truth_changed': False})

    def observe(self, *, action):
        """Read-only evidence, including safe discovery after an ambiguous create.

        Discovery deliberately does not clear the journal fence or rebind a file.
        """
        try:
            self._scope()
            snapshot, plan = self._plan(action)
            existing = binding(snapshot)
            metadata = self._locate(plan, existing)
            document = self.transport.get(metadata['id'])
            _, desired = render_template(plan)
            matches = (document.get('documentId') == metadata['id'] and
                [p[2] for p in paragraphs(document)] == desired and existing is not None and
                fingerprint(document) == existing.get('document_fingerprint') and
                existing.get('projection_hash') == plan['projection_hash'])
            return {'status': 'MATCHES_PROJECTION' if matches else 'DRIFT_DETECTED' if existing else 'AMBIGUOUS',
                'document_id': metadata['id'], 'business_truth_changed': False, 'rebound': False}
        except GoogleFailure as exc:
            return {'status': 'MISSING' if exc.reason in {'google_document_missing', 'google_http_404'} else
                    'AMBIGUOUS' if exc.ambiguous else 'DRIFT_DETECTED', 'reason': exc.reason,
                    'business_truth_changed': False, 'rebound': False}
        except (ValueError, AttributeError, KeyError):
            return {'status': 'DRIFT_DETECTED', 'reason': 'proposal_stale_or_invalid', 'business_truth_changed': False}
