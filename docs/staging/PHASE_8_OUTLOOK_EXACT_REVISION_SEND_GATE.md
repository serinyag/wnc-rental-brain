# Outlook Exact-Revision Send Gate

## Purpose

This staging safeguard prepares a governed Outlook draft for a later, explicitly
authorized send. It does not enable sending and does not approve a draft.

## Required Send Boundary

The normal governed Outlook execution path for a reconciled human edit uses the
existing immutable Graph message ID. It never creates a replacement draft. Before
the adapter can call `/send`, it requires all of the following:

- the current draft revision is approved by an ApprovalRequest targeted exactly at
  the current WorkflowAction and DraftRevision;
- current case revision and governed context hash still match the approved revision;
- no blocking operator annotation exists and the recipient remains staging-allowlisted;
- the append-only human-edit reconciliation event supplies one bound Graph message ID;
- one Graph GET confirms that same message is still a draft in the configured
  mailbox, with canonical subject, body, recipient, and no CC changes;
- the final transport-boundary switch permits sending.

Any mismatch returns a typed failed execution attempt and stops before `/send`.
`outlook_draft_changed_after_approval` specifically means a human or provider
change invalidated the approved content.

## Current Staging Posture

Keep these values in staging until a separate explicit send authorization:

```ini
WORKFLOW_TEST_CONSOLE_ALLOW_REAL_PROVIDERS=true
STAGING_ALLOW_REAL_OUTLOOK=true
STAGING_ALLOW_REAL_OUTLOOK_SEND=false
STAGING_ALLOW_REAL_ASANA=false
```

`GET /api/operator/cases/{case_id}/actions/{workflow_action_id}/outlook-send-readiness`
is provider-free. It reports whether the current exact approval is still required;
it performs zero Graph operations and cannot send an email.
