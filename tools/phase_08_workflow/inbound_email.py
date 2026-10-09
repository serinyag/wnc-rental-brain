"""Provider-neutral immutable email evidence. No business authority or execution."""
from dataclasses import dataclass, asdict
from hashlib import sha256
from html.parser import HTMLParser
from datetime import datetime
import json
import re


def evidence_hash(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.links, self.hidden = [], [], 0
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'): self.hidden += 1
        if tag in ('p', 'div', 'br', 'li', 'tr', 'h1', 'h2'): self.parts.append('\n')
        if tag == 'a': self.links.append(dict(attrs).get('href', ''))
    def handle_endtag(self, tag):
        if tag in ('script', 'style'): self.hidden = max(0, self.hidden - 1)
        if tag in ('p', 'div', 'li', 'tr', 'h1', 'h2'): self.parts.append('\n')
        if tag == 'a' and self.links:
            link = self.links.pop()
            if link.startswith(('https://', 'http://', 'mailto:')): self.parts.append(' (' + link + ')')
    def handle_data(self, data):
        if not self.hidden: self.parts.append(data)


def normalize_body(body_type, raw):
    if body_type == 'text': return raw.replace('\r\n', '\n')
    if body_type != 'html': raise ValueError('unsupported_body_type')
    parser = _Text(); parser.feed(raw); parser.close()
    return '\n'.join(re.sub(r'[\t \xa0]+', ' ', line).strip() for line in ''.join(parser.parts).splitlines()).strip()


@dataclass(frozen=True)
class InboundEmailEnvelope:
    provider: str
    mailbox: str
    provider_message_id: str
    provider_conversation_id: str
    internet_message_id: str | None
    received_at: str
    from_address: str
    to_addresses: tuple[str, ...]
    cc_addresses: tuple[str, ...]
    subject: str
    body_type: str
    raw_body: str
    normalized_body: str
    has_attachments: bool
    attachment_metadata: tuple[dict, ...]
    reply_references: tuple[str, ...]
    provider_metadata_hash: str

    def __post_init__(self):
        for field in ('provider', 'mailbox', 'provider_message_id', 'provider_conversation_id', 'from_address'):
            if not isinstance(getattr(self, field), str) or not getattr(self, field).strip(): raise ValueError('missing_' + field)
        if datetime.fromisoformat(self.received_at.replace('Z', '+00:00')).tzinfo is None: raise ValueError('received_timestamp_requires_timezone')
        if self.normalized_body != normalize_body(self.body_type, self.raw_body): raise ValueError('normalization_mismatch')

    @property
    def identity(self):
        return evidence_hash([self.provider, self.mailbox.casefold(), self.provider_message_id])

    def payload(self):
        return asdict(self)
