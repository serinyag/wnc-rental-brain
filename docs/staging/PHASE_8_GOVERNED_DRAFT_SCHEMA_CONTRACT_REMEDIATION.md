# Phase 8 Governed Draft Schema Contract Remediation

## Incident

On 2026-09-07, one controlled synthetic staging generation for RentalCase `369`
reached the workflow-action persistence step and failed closed with:

```text
DATABASE_READ_FAILED
sqlstate: 23514
error_class: CheckViolation
table: public.workflow_actions
```

No draft revision, approval request, Outlook/Graph send, or Asana execution was
created by that failed request.

## Root Cause

The canonical application contract already defined `SEND_INQUIRY_RESPONSE`, but
the closed `workflow_actions_action_type_check` SQL allowlist did not include
it. The governed client-response path correctly attempted to create an
approval-required workflow action and the database rejected it.

After the schema repair, the controlled retry persisted the intended
approval-bound action but failed before draft persistence. The shared
`InquiryResponseDraftContext` still required at least one client question,
which conflicts with valid governed replies such as a complete inquiry
acknowledgement that use a body-only draft.

## Remediation

`20260907000100_phase_08_governed_client_response_action_type.sql` updates only
the `workflow_actions` action-type check constraint to admit
`SEND_INQUIRY_RESPONSE`. It does not change Outlook configuration, approval
posture, execution eligibility, or authority controls.

`44_phase_08_governed_client_response_action_type.sql` proves an
approval-bound action with that type can persist.

The governed-response context now explicitly permits an empty question set;
ordinary inquiry-follow-up drafting remains strict by default.

## Current Status

The migration must be applied to the staging Supabase project before another
controlled synthetic draft attempt. The prior OpenAI provider call was not a
successful end-to-end verification, so no general-drafting success marker is
claimed by this remediation alone.
