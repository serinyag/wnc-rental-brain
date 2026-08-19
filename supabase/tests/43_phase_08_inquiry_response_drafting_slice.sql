begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

select plan(11);

select ok(
  to_regclass('public.inquiry_response_draft_revisions') is not null,
  'inquiry_response_draft_revisions table exists'
);

select ok(
  exists (
    select 1
    from pg_indexes
    where schemaname = 'public'
      and tablename = 'inquiry_response_draft_revisions'
      and indexname = 'uq_inquiry_response_drafts_current_conversation'
  ),
  'current inquiry draft uniqueness per case conversation exists'
);

select ok(
  exists (
    select 1
    from pg_indexes
    where schemaname = 'public'
      and tablename = 'inquiry_response_draft_revisions'
      and indexname = 'uq_inquiry_response_drafts_current_approval'
  ),
  'approval-to-draft uniqueness exists'
);

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
values
  ('RC-1201', 'inquiry_active', 0, 'custom_scope', 'studio_rental', 'unknown', 'unknown', true),
  ('RC-1202', 'inquiry_active', 0, 'custom_scope', 'studio_rental', 'unknown', 'unknown', true);

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
  idempotency_key,
  created_at,
  updated_at
)
select
  id,
  'REQUEST_CLIENT_INFORMATION',
  'communication',
  'email',
  'open_question',
  case
    when case_reference_code = 'RC-1201' then 'open_question:1201'
    else 'open_question:1202'
  end,
  '{"fixture":true}'::jsonb,
  'approval_required',
  'awaiting_approval',
  case
    when case_reference_code = 'RC-1201' then 'subject:1201'
    else 'subject:1202'
  end,
  0,
  case
    when case_reference_code = 'RC-1201' then 'thread:1201'
    else 'thread:1202'
  end,
  timezone('utc', now()),
  timezone('utc', now())
from public.rental_cases
where case_reference_code in ('RC-1201', 'RC-1202');

select lives_ok(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-1201'
    ),
    target_action as (
      select id
      from public.workflow_actions
      where rental_case_id = (select id from target_case)
    )
    insert into public.inquiry_response_draft_revisions (
      rental_case_id,
      workflow_action_id,
      conversation_key,
      source_case_revision,
      draft_status,
      draft_source,
      is_current,
      subject,
      salutation,
      intro_text,
      question_lines,
      closing_text,
      signoff_text,
      body_text,
      context_payload,
      context_hash,
      content_hash,
      recipient_email,
      recipient_label,
      sender_email,
      sender_label,
      sender_display_name,
      created_by_reference,
      created_at,
      updated_at
    )
    select
      (select id from target_case),
      (select id from target_action),
      'thread:1201',
      0,
      'needs_approval',
      'generated',
      true,
      'Need two details',
      'Hi Acme,',
      'Please confirm:',
      '[{"open_question_id":1201,"question_type":"guest_count","human_question_text":"How many guests?","prompt_text":"How many guests?"}]'::jsonb,
      'Thanks.',
      'Warmly, WNC',
      'Hi Acme,\n\nPlease confirm:\n\n- How many guests?\n\nThanks.\n\nWarmly, WNC',
      '{"fixture":true}'::jsonb,
      'ctx:1201:v1',
      'content:1201:v1',
      'client1201@example.test',
      'Acme 1201',
      'ops@example.test',
      'WNC Rentals',
      'WNC Rentals',
      'test:fixture',
      timezone('utc', now()),
      timezone('utc', now());
  $sql$,
  'valid inquiry-response draft revision can be inserted'
);

select lives_ok(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-1201'
    ),
    target_draft as (
      select id, workflow_action_id
      from public.inquiry_response_draft_revisions
      where rental_case_id = (select id from target_case)
        and conversation_key = 'thread:1201'
    ),
    inserted_approval as (
      insert into public.rental_case_approval_requests (
        rental_case_id,
        target_entity_type,
        target_entity_id,
        target_entity_reference,
        approval_type,
        reason_text,
        required_approver_reference,
        status,
        created_at,
        updated_at
      )
      select
        (select id from target_case),
        'workflow_action',
        workflow_action_id,
        format('workflow_action:%s:draft_revision:%s', workflow_action_id, id),
        'client_communication_send',
        'Approve draft revision 1201.',
        format('semantic:approval:workflow_action:%s:draft_revision:%s', workflow_action_id, id),
        'open',
        timezone('utc', now()),
        timezone('utc', now())
      from target_draft
      returning id
    )
    update public.inquiry_response_draft_revisions
    set approval_request_id = (select id from inserted_approval),
        updated_at = timezone('utc', now())
    where id = (select id from target_draft);
  $sql$,
  'exact workflow-action approval can be bound to the draft revision'
);

select throws_ok(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-1201'
    ),
    target_action as (
      select id
      from public.workflow_actions
      where rental_case_id = (select id from target_case)
    )
    insert into public.inquiry_response_draft_revisions (
      rental_case_id,
      workflow_action_id,
      conversation_key,
      source_case_revision,
      draft_status,
      draft_source,
      is_current,
      subject,
      salutation,
      intro_text,
      question_lines,
      closing_text,
      signoff_text,
      body_text,
      context_payload,
      context_hash,
      content_hash,
      recipient_email,
      sender_email,
      sender_label,
      created_by_reference
    )
    select
      (select id from target_case),
      (select id from target_action),
      'thread:1201',
      0,
      'needs_approval',
      'regenerated',
      true,
      'Need two more details',
      'Hi Acme,',
      'Please confirm again:',
      '[{"open_question_id":1202,"question_type":"event_type","human_question_text":"What type of event?","prompt_text":"What type of event?"}]'::jsonb,
      'Thanks.',
      'Warmly, WNC',
      'Hi Acme,\n\nPlease confirm again.',
      '{"fixture":true}'::jsonb,
      'ctx:1201:v2',
      'content:1201:v2',
      'client1201@example.test',
      'ops@example.test',
      'WNC Rentals',
      'test:fixture';
  $sql$,
  '23505',
  null,
  'second current draft for the same conversation is rejected'
);

select throws_ok(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-1201'
    ),
    other_action as (
      select id
      from public.workflow_actions
      where rental_case_id = (
        select id
        from public.rental_cases
        where case_reference_code = 'RC-1202'
      )
    )
    insert into public.inquiry_response_draft_revisions (
      rental_case_id,
      workflow_action_id,
      conversation_key,
      source_case_revision,
      draft_status,
      draft_source,
      is_current,
      subject,
      salutation,
      intro_text,
      question_lines,
      closing_text,
      signoff_text,
      body_text,
      context_payload,
      context_hash,
      content_hash,
      recipient_email,
      sender_email,
      sender_label,
      created_by_reference
    )
    select
      (select id from target_case),
      (select id from other_action),
      'thread:1201-cross-action',
      0,
      'needs_approval',
      'generated',
      true,
      'Wrong action case',
      'Hi Acme,',
      'Please confirm:',
      '[{"open_question_id":1203,"question_type":"guest_count","human_question_text":"How many guests?","prompt_text":"How many guests?"}]'::jsonb,
      'Thanks.',
      'Warmly, WNC',
      'Hi Acme,\n\nPlease confirm.',
      '{"fixture":true}'::jsonb,
      'ctx:1201:xcase-action',
      'content:1201:xcase-action',
      'client1201@example.test',
      'ops@example.test',
      'WNC Rentals',
      'test:fixture';
  $sql$,
  '23514',
  null,
  'draft revision cannot point at a workflow action from another case'
);

with target_case as (
  select id
  from public.rental_cases
  where case_reference_code = 'RC-1201'
),
target_action as (
  select id
  from public.workflow_actions
  where rental_case_id = (select id from target_case)
)
insert into public.inquiry_response_draft_revisions (
  rental_case_id,
  workflow_action_id,
  conversation_key,
  source_case_revision,
  draft_status,
  draft_source,
  is_current,
  subject,
  salutation,
  intro_text,
  question_lines,
  closing_text,
  signoff_text,
  body_text,
  context_payload,
  context_hash,
  content_hash,
  recipient_email,
  sender_email,
  sender_label,
  created_by_reference
)
select
  (select id from target_case),
  (select id from target_action),
  'thread:1201-cross-approval',
  0,
  'needs_approval',
  'generated',
  true,
  'Approval mismatch',
  'Hi Acme,',
  'Please confirm:',
  '[{"open_question_id":1204,"question_type":"event_type","human_question_text":"What type of event?","prompt_text":"What type of event?"}]'::jsonb,
  'Thanks.',
  'Warmly, WNC',
  'Hi Acme,\n\nPlease confirm.',
  '{"fixture":true}'::jsonb,
  'ctx:1201:xcase-approval',
  'content:1201:xcase-approval',
  'client1201@example.test',
  'ops@example.test',
  'WNC Rentals',
  'test:fixture';

select throws_ok(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-1201'
    ),
    other_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-1202'
    ),
    other_action as (
      select id
      from public.workflow_actions
      where rental_case_id = (select id from other_case)
    ),
    target_draft as (
      select id
      from public.inquiry_response_draft_revisions
      where rental_case_id = (select id from target_case)
        and conversation_key = 'thread:1201-cross-approval'
    ),
    inserted_approval as (
      insert into public.rental_case_approval_requests (
        rental_case_id,
        target_entity_type,
        target_entity_id,
        target_entity_reference,
        approval_type,
        reason_text,
        required_approver_reference,
        status,
        created_at,
        updated_at
      )
      select
        (select id from other_case),
        'workflow_action',
        (select id from other_action),
        format('workflow_action:%s:draft_revision:%s', (select id from other_action), (select id from target_draft)),
        'client_communication_send',
        'Cross-case approval mismatch.',
        'semantic:approval:cross-case',
        'open',
        timezone('utc', now()),
        timezone('utc', now())
      returning id
    )
    update public.inquiry_response_draft_revisions
    set approval_request_id = (select id from inserted_approval),
        updated_at = timezone('utc', now())
    where rental_case_id = (select id from target_case)
      and conversation_key = 'thread:1201-cross-approval';
  $sql$,
  '23514',
  null,
  'draft revision cannot bind an approval request from another case'
);

with target_case as (
  select id
  from public.rental_cases
  where case_reference_code = 'RC-1201'
),
target_action as (
  select id
  from public.workflow_actions
  where rental_case_id = (select id from target_case)
)
insert into public.inquiry_response_draft_revisions (
  rental_case_id,
  workflow_action_id,
  conversation_key,
  source_case_revision,
  draft_status,
  draft_source,
  is_current,
  subject,
  salutation,
  intro_text,
  question_lines,
  closing_text,
  signoff_text,
  body_text,
  context_payload,
  context_hash,
  content_hash,
  recipient_email,
  sender_email,
  sender_label,
  created_by_reference
)
select
  (select id from target_case),
  (select id from target_action),
  'thread:1201-bad-reference',
  0,
  'needs_approval',
  'generated',
  true,
  'Wrong reference',
  'Hi Acme,',
  'Please confirm:',
  '[{"open_question_id":1205,"question_type":"event_type","human_question_text":"What type of event?","prompt_text":"What type of event?"}]'::jsonb,
  'Thanks.',
  'Warmly, WNC',
  'Hi Acme,\n\nPlease confirm.',
  '{"fixture":true}'::jsonb,
  'ctx:1201:bad-reference',
  'content:1201:bad-reference',
  'client1201@example.test',
  'ops@example.test',
  'WNC Rentals',
  'test:fixture';

select throws_ok(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-1201'
    ),
    target_draft as (
      select id, workflow_action_id
      from public.inquiry_response_draft_revisions
      where rental_case_id = (select id from target_case)
        and conversation_key = 'thread:1201-bad-reference'
    ),
    inserted_approval as (
      insert into public.rental_case_approval_requests (
        rental_case_id,
        target_entity_type,
        target_entity_id,
        target_entity_reference,
        approval_type,
        reason_text,
        required_approver_reference,
        status,
        created_at,
        updated_at
      )
      select
        (select id from target_case),
        'workflow_action',
        workflow_action_id,
        format('workflow_action:%s:draft_revision:%s', workflow_action_id, 999999),
        'client_communication_send',
        'Wrong draft reference.',
        'semantic:approval:wrong-draft-reference',
        'open',
        timezone('utc', now()),
        timezone('utc', now())
      from target_draft
      returning id
    )
    update public.inquiry_response_draft_revisions
    set approval_request_id = (select id from inserted_approval),
        updated_at = timezone('utc', now())
    where rental_case_id = (select id from target_case)
      and conversation_key = 'thread:1201-bad-reference';
  $sql$,
  '23514',
  null,
  'approval target reference must match the exact draft revision id'
);

select throws_ok(
  $sql$
    update public.inquiry_response_draft_revisions
    set subject = 'Mutated subject',
        updated_at = timezone('utc', now())
    where conversation_key = 'thread:1201';
  $sql$,
  '23514',
  null,
  'draft content rows are immutable after insert'
);

select throws_ok(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-1201'
    ),
    target_action as (
      select id
      from public.workflow_actions
      where rental_case_id = (select id from target_case)
    ),
    prior_draft as (
      select id
      from public.inquiry_response_draft_revisions
      where rental_case_id = (select id from target_case)
        and conversation_key = 'thread:1201'
    )
    insert into public.inquiry_response_draft_revisions (
      rental_case_id,
      workflow_action_id,
      conversation_key,
      source_case_revision,
      draft_status,
      draft_source,
      is_current,
      subject,
      salutation,
      intro_text,
      question_lines,
      closing_text,
      signoff_text,
      body_text,
      context_payload,
      context_hash,
      content_hash,
      recipient_email,
      sender_email,
      sender_label,
      supersedes_draft_revision_id,
      created_by_reference
    )
    select
      (select id from target_case),
      (select id from target_action),
      'thread:1201-other-conversation',
      0,
      'needs_approval',
      'regenerated',
      true,
      'Wrong supersedes conversation',
      'Hi Acme,',
      'Please confirm:',
      '[{"open_question_id":1206,"question_type":"event_type","human_question_text":"What type of event?","prompt_text":"What type of event?"}]'::jsonb,
      'Thanks.',
      'Warmly, WNC',
      'Hi Acme,\n\nPlease confirm.',
      '{"fixture":true}'::jsonb,
      'ctx:1201:wrong-supersedes',
      'content:1201:wrong-supersedes',
      'client1201@example.test',
      'ops@example.test',
      'WNC Rentals',
      (select id from prior_draft),
      'test:fixture';
  $sql$,
  '23514',
  null,
  'superseded draft links must stay within the same conversation'
);

select * from finish();

rollback;
