-- Phase 8's governed client-draft workflow persists an approval-bound action
-- before it can create an immutable draft revision. Keep the DB allowlist in
-- sync with the canonical application action-type contract.
alter table public.workflow_actions
  drop constraint if exists workflow_actions_action_type_check;

alter table public.workflow_actions
  add constraint workflow_actions_action_type_check
  check (
    action_type in (
      'REQUEST_CLIENT_INFORMATION',
      'SEND_INQUIRY_RESPONSE',
      'SEND_DISCOVERY_CALL_INVITE',
      'SEND_SITE_VISIT_PROPOSAL',
      'SEND_PROPOSAL_MESSAGE',
      'SEND_PROPOSAL_FOLLOW_UP',
      'REQUEST_CONFIRMATION_PAYMENT',
      'REQUEST_SIGNED_AGREEMENT',
      'REQUEST_FINAL_EVENT_INFORMATION',
      'REQUEST_SUPPLIER_INFORMATION',
      'ESCALATE_COMPLIANCE_REVIEW',
      'REQUEST_EXCEPTION_APPROVAL',
      'CREATE_INTERNAL_TASK_ITEM',
      'CREATE_CALENDAR_HOLD',
      'CREATE_PAYMENT_REQUEST',
      'DRAFT_PROPOSAL_ARTIFACT',
      'DRAFT_AGREEMENT_ARTIFACT',
      'DRAFT_INTERNAL_EVENT_BRIEF',
      'SYNC_ARTIFACT_PROJECTION',
      'MARK_ARTIFACT_REFRESH_REQUIRED',
      'SCHEDULE_FOLLOW_UP_REVIEW',
      'ESCALATE_DORMANT_CASE_REVIEW',
      'SUPERSEDE_STALE_ACTIONS',
      'RECORD_MANUAL_CLOSE_PACKET'
    )
  );
