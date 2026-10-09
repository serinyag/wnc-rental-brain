"""Bounded, read-only Graph Inbox transport. Never follows an untrusted origin."""
import json
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote, urlencode, urlsplit, unquote, parse_qs

from .inbound_email import InboundEmailEnvelope, evidence_hash, normalize_body

class InboundCursorScopeError(ValueError):
    def __init__(self, actual, expected):
        super().__init__('inbound_cursor_scope_forbidden')
        # Preserve resource identity for operator reconciliation; never retain
        # opaque delta/skip tokens, credentials or arbitrary query values.
        self.diagnostics = {
            'expected_origin': expected.scheme + '://' + expected.netloc,
            'expected_path': expected.path[:2048],
            'returned_origin': actual.scheme + '://' + (actual.hostname or ''),
            'returned_path': actual.path[:2048],
            'query_parameter_names': sorted(parse_qs(actual.query))[:20],
            'cursor_values_redacted': True,
        }


GRAPH = 'https://graph.microsoft.com/v1.0'
SELECT = 'id,internetMessageId,conversationId,receivedDateTime,from,toRecipients,ccRecipients,subject,hasAttachments,internetMessageHeaders,isDraft'


@dataclass(frozen=True)
class OutlookInboundConfig:
    mailbox: str
    allowed_mailbox: str
    since: str
    allowed_senders: tuple[str, ...]
    new_enquiry_subject: str
    enabled: bool = False
    environment: str = 'staging'
    page_size: int = 10
    production_contract: object | None = None

    def validate(self):
        if self.environment not in ('staging','production') or not self.allowed_mailbox or self.mailbox.casefold() != self.allowed_mailbox.casefold():
            raise ValueError('inbound_staging_mailbox_scope_forbidden')
        if self.environment=='production':
            if self.production_contract is None or self.mailbox.casefold()!=self.production_contract.manifest['outlook']['mailbox'].casefold():
                raise ValueError('production_inbound_identity_invalid')
        if not 1 <= self.page_size <= 25: raise ValueError('invalid_page_bound')
        if datetime.fromisoformat(self.since.replace('Z', '+00:00')).tzinfo is None: raise ValueError('initial_window_requires_timezone')
        if self.environment=='production' and not self.allowed_senders:
            if self.enabled or self.production_contract.lane('outlook_inbound'):raise ValueError('production_pilot_sender_scope_missing')
        elif not self.allowed_senders or (self.environment=='staging' and not self.new_enquiry_subject): raise ValueError('synthetic_scope_required')


class OutlookInboundAdapter:
    def __init__(self, config, transport, access_token):
        config.validate()
        self.config, self.transport, self.access_token = config, transport, access_token
        self.base = GRAPH + '/users/' + quote(config.mailbox, safe='')
        self.delta_path = self.base + '/mailFolders/inbox/messages/delta'

    def initial_cursor(self):
        return self.delta_path + '?' + urlencode({'$select': SELECT, '$filter': 'receivedDateTime ge ' + self.config.since})

    def validate_cursor(self, url):
        a, b = urlsplit(url), urlsplit(self.delta_path)
        # Graph returns the Inbox key using OData key syntax in delta links.
        # Accept only this exact equivalent resource, never a generic path
        # prefix or arbitrary user/folder alias. Preserve opaque query bytes.
        allowed_paths = {unquote(b.path), unquote(urlsplit(self.base).path) + "/mailFolders('inbox')/messages/delta"}
        if a.scheme != b.scheme or a.netloc != b.netloc or unquote(a.path) not in allowed_paths or a.fragment or a.username:
            raise InboundCursorScopeError(a, b)
        return url

    def _get(self, url):
        self.config.validate()
        if not self.config.enabled or (self.config.environment=='production' and not self.config.production_contract.lane('outlook_inbound')): raise ValueError('inbound_gate_disabled')
        # Redirects must be rejected by the real transport as well as cursor URLs.
        status, body, _ = self.transport.request(method='GET', url=url,
            headers={'Authorization': 'Bearer ' + self.access_token, 'Accept': 'application/json',
                     'Prefer': 'IdType="ImmutableId", odata.maxpagesize=' + str(self.config.page_size)},
            body=None, timeout_seconds=30)
        if status != 200: raise ValueError('inbound_provider_http_' + str(status))
        result = json.loads(body)
        if not isinstance(result, dict): raise ValueError('inbound_response_invalid')
        return result

    def read_page(self, cursor=None):
        page = self._get(self.validate_cursor(cursor or self.initial_cursor()))
        records = page.get('value')
        if not isinstance(records, list) or len(records) > self.config.page_size: raise ValueError('inbound_page_bound_or_shape_invalid')
        links = [page[k] for k in ('@odata.nextLink', '@odata.deltaLink') if k in page]
        if len(links) != 1: raise ValueError('inbound_checkpoint_uncertain')
        next_cursor = self.validate_cursor(links[0])
        return records, next_cursor, 'ready' if '@odata.deltaLink' in page else 'paging'

    def read_message(self, message_id):
        return self._get(self.base + '/messages/' + quote(message_id, safe='') + '?' +
            urlencode({'$select':SELECT + ',body'}))

    def envelope(self, message):
        if not isinstance(message, dict) or message.get('isDraft') is not False: raise ValueError('inbound_message_shape_invalid')
        def address(item):
            value = item['emailAddress']['address']
            if not isinstance(value, str) or '@' not in value: raise ValueError('invalid_address')
            return value.casefold()
        body = message['body']; raw = body['content']; kind = body['contentType'].lower()
        if not isinstance(raw, str) or len(raw.encode()) > 1_000_000: raise ValueError('inbound_body_bound')
        refs = tuple(h['value'] for h in message.get('internetMessageHeaders', []) if h.get('name','').lower() in ('in-reply-to','references') and h.get('value'))
        attachments = ()
        if message['hasAttachments']:
            page = self._get(self.base + '/messages/' + quote(message['id'], safe='') + '/attachments?' +
                urlencode({'$select':'id,name,contentType,size,isInline','$top':20}))
            values = page.get('value')
            if not isinstance(values, list) or len(values) > 20 or page.get('@odata.nextLink'):
                raise ValueError('attachment_metadata_requires_review')
            if any(not isinstance(v,dict) or not v.get('id') or 'contentBytes' in v for v in values):
                raise ValueError('attachment_metadata_invalid')
            attachments = tuple({k:v[k] for k in ('id','name','contentType','size','isInline') if k in v} for v in values)
        return InboundEmailEnvelope('outlook', self.config.mailbox.casefold(), message['id'], message['conversationId'],
            message.get('internetMessageId'), message['receivedDateTime'], address(message['from']),
            tuple(address(x) for x in message['toRecipients']), tuple(address(x) for x in message.get('ccRecipients', [])),
            message['subject'], kind, raw, normalize_body(kind, raw), bool(message['hasAttachments']), attachments, refs, evidence_hash(message))
