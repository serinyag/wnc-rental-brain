"""Deterministic Outlook transport for provider-free execution through real gates."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .outlook_action_contract import OutlookExecutionInput


@dataclass
class DeterministicOutlookTransport:
    value: OutlookExecutionInput
    occurred_at: str
    mailbox: str = "outlook-fixture@example.test"
    sent: bool = False
    calls: list[tuple[str, str]] = field(default_factory=list)

    def request(self, *, method: str, url: str, headers: Any, body: Any, timeout_seconds: int):
        self.calls.append((method, url))
        message_id = self.value.graph_message_id or f"synthetic-draft-{self.value.draft_revision_id}"
        if method == "POST" and url.endswith("/token"):
            return 200, json.dumps({"access_token": "synthetic-token"}), {}
        if method == "POST" and url.endswith("/messages"):
            return 201, json.dumps({"id": message_id}), {}
        if method == "POST" and url.endswith("/send"):
            self.sent = True
            return 202, "", {}
        if method == "GET":
            return 200, json.dumps({
                "id": message_id, "isDraft": not self.sent, "subject": self.value.subject,
                "body": {"contentType": "text", "content": self.value.body},
                "toRecipients": [{"emailAddress": {"address": self.value.recipient_email}}],
                "ccRecipients": [], "from": {"emailAddress": {"address": self.mailbox}},
                "sender": {"emailAddress": {"address": self.mailbox}},
                "sentDateTime": self.occurred_at if self.sent else None,
            }), {}
        raise ValueError("unsupported_synthetic_outlook_operation")
