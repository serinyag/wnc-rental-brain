begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

select plan(1);

insert into public.rental_cases (
  case_reference_code,
  lifecycle_state,
  case_revision,
  rental_type_code,
  service_level_or_type,
  commercial_summary_status,
  operational_summary_status,
  is_active
)
values (
  'RC-1301',
  'inquiry_active',
  1,
  'studio_space',
  'studio_rental',
  'unknown',
  'unknown',
  true
);

select lives_ok(
  $sql$
    insert into public.workflow_actions (
      rental_case_id,
      action_type,
      action_category,
      target_adapter_code,
      reason_entity_type,
      reason_entity_reference,
      structured_payload,
      approval_posture,
      status,
      semantic_subject_hash,
      source_case_revision,
      idempotency_key
    )
    select
      id,
      'SEND_INQUIRY_RESPONSE',
      'communication',
      'outlook',
      'rental_case',
      'governed_client_response:1301',
      '{"purpose":"governed_client_response_draft"}'::jsonb,
      'approval_required',
      'awaiting_approval',
      'governed-client-response:1301',
      1,
      'governed_client_response:1301:successor:fixture'
    from public.rental_cases
    where case_reference_code = 'RC-1301';
  $sql$,
  'approval-bound governed client-response action is accepted by the workflow action type constraint'
);

select * from finish();

rollback;
