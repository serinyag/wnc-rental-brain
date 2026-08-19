begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

select plan(10);

select ok(
  exists (
    select 1
    from pg_proc proc
    join pg_namespace namespace
      on namespace.oid = proc.pronamespace
    where namespace.nspname = 'private'
      and proc.proname = 'commit_phase8_case_decision_approval'
  ),
  'case-decision approval commit helper exists'
);

select ok(
  exists (
    select 1
    from pg_proc proc
    join pg_namespace namespace
      on namespace.oid = proc.pronamespace
    where namespace.nspname = 'private'
      and proc.proname = 'commit_phase8_workflow_action_approval'
  ),
  'workflow-action approval commit helper exists'
);

select ok(
  exists (
    select 1
    from pg_proc proc
    join pg_namespace namespace
      on namespace.oid = proc.pronamespace
    where namespace.nspname = 'private'
      and proc.proname = 'commit_phase8_proposed_case_change_resolution'
  ),
  'proposed-case-change resolution commit helper exists'
);

insert into public.rental_cases (
  case_reference_code,
  lifecycle_state,
  case_revision,
  rental_type_code,
  service_level_or_type,
  client_account_ref,
  primary_contact_ref,
  commercial_summary_status,
  operational_summary_status,
  is_active
)
values
  (
    'RC-986',
    'proposal_in_progress',
    0,
    'studio_space',
    'studio_rental',
    'client:986',
    'contact:986',
    'unknown',
    'unknown',
    true
  ),
  (
    'RC-987',
    'proposal_in_progress',
    0,
    'studio_space',
    'studio_rental',
    'client:987',
    'contact:987',
    'unknown',
    'unknown',
    true
  ),
  (
    'RC-988',
    'proposal_in_progress',
    0,
    'studio_space',
    'studio_rental',
    'client:988',
    'contact:988',
    'unknown',
    'unknown',
    true
  );

with target_case as (
  select id
  from public.rental_cases
  where case_reference_code = 'RC-986'
),
inserted_decision as (
  insert into public.rental_case_decisions (
    rental_case_id,
    decision_type,
    domain_code,
    baseline_reference,
    proposed_value_payload,
    scope_key,
    scope_description,
    evidence_reference,
    authority_basis,
    approval_posture,
    status,
    created_at,
    updated_at
  )
  select
    id,
    'booking_fee_waiver',
    'booking_fee',
    'phase4:booking_fee:50',
    '{"booking_fee":0,"waived":true}'::jsonb,
    'booking_fee:default',
    'booking fee exception',
    'observation:waiver_request',
    'case_specific_exception',
    'approval_required',
    'proposed',
    timezone('utc', now()),
    timezone('utc', now())
  from target_case
  returning id, rental_case_id
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
    rental_case_id,
    'case_decision',
    id,
    concat('case_decision:', id),
    'commercial_exception',
    'Approval required for booking fee waiver.',
    'manager:986',
    'open',
    timezone('utc', now()),
    timezone('utc', now())
  from inserted_decision
  returning id, rental_case_id
)
insert into public.rental_case_artifacts (
  rental_case_id,
  artifact_type,
  storage_reference,
  derived_from_case_revision,
  freshness_status,
  created_at,
  updated_at
)
select
  id,
  'proposal',
  'artifact:proposal:986',
  0,
  'current',
  timezone('utc', now()),
  timezone('utc', now())
from target_case;

with target_case as (
  select id
  from public.rental_cases
  where case_reference_code = 'RC-986'
)
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
  'open_question:986',
  '{"fixture":true}'::jsonb,
  'approval_required',
  'awaiting_approval',
  'subject:986',
  0,
  'idem:986',
  timezone('utc', now()),
  timezone('utc', now())
from target_case;

with target_case as (
  select id
  from public.rental_cases
  where case_reference_code = 'RC-986'
),
target_decision as (
  select id
  from public.rental_case_decisions
  where rental_case_id = (select id from target_case)
)
insert into public.rental_case_blockers (
  rental_case_id,
  blocker_type,
  blocked_subject_type,
  blocked_subject_reference,
  origin_entity_type,
  origin_entity_id,
  origin_entity_reference,
  severity,
  status,
  resolution_condition_text,
  opened_at,
  created_at,
  updated_at
)
select
  tc.id,
  'approval_pending_case_decision',
  'decision',
  'case_decision:986',
  'case_decision',
  td.id,
  concat('case_decision:', td.id),
  'high',
  'open',
  'Decision must be approved or rejected.',
  timezone('utc', now()),
  timezone('utc', now()),
  timezone('utc', now())
from target_case tc
cross join target_decision td;

select results_eq(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-986'
    ),
    target_approval as (
      select id
      from public.rental_case_approval_requests
      where rental_case_id = (select id from target_case)
    )
    select
      approval_status,
      case_revision_before,
      case_revision_after,
      cardinality(audit_event_ids),
      cardinality(resolved_blocker_ids),
      cardinality(artifact_freshness_changed_ids),
      cardinality(superseded_action_ids),
      activated_case_decision_id is not null,
      failure_code is null
    from private.commit_phase8_case_decision_approval(
      p_rental_case_id => (select id from target_case),
      p_approval_request_id => (select id from target_approval),
      p_decision => 'approved',
      p_expected_case_revision => 0,
      p_actor_type => 'operator',
      p_actor_reference => 'operator:986',
      p_decision_payload => '{"decision":"approved"}'::jsonb,
      p_decision_notes => null,
      p_decided_at => '2026-08-13T12:00:00Z'::timestamptz
    )
  $sql$,
  $sql$
    values (
      'approved'::text,
      0::integer,
      1::integer,
      5::integer,
      1::integer,
      1::integer,
      1::integer,
      true,
      true
    )
  $sql$,
  'case-decision approval atomically activates the decision and emits full audit coverage'
);

select results_eq(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-986'
    )
    select
      rc.case_revision,
      decision.status,
      approval.status,
      artifact.freshness_status,
      action.status,
      blocker.status,
      (
        select count(*)
        from public.rental_case_lifecycle_transitions transition_history
        where transition_history.rental_case_id = rc.id
      )::bigint,
      (
        select count(*)
        from public.workflow_execution_attempts attempt
        where attempt.rental_case_id = rc.id
      )::bigint
    from public.rental_cases rc
    join public.rental_case_decisions decision
      on decision.rental_case_id = rc.id
    join public.rental_case_approval_requests approval
      on approval.rental_case_id = rc.id
    join public.rental_case_artifacts artifact
      on artifact.rental_case_id = rc.id
    join public.workflow_actions action
      on action.rental_case_id = rc.id
    join public.rental_case_blockers blocker
      on blocker.rental_case_id = rc.id
    where rc.id = (select id from target_case)
  $sql$,
  $sql$
    values (
      1::integer,
      'active'::text,
      'approved'::text,
      'refresh_required'::text,
      'superseded'::text,
      'resolved'::text,
      0::bigint,
      0::bigint
    )
  $sql$,
  'case-decision approval mutates only orchestration records and does not execute actions'
);

select results_eq(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-986'
    ),
    target_approval as (
      select id
      from public.rental_case_approval_requests
      where rental_case_id = (select id from target_case)
    )
    select
      failure_code,
      case_revision_before,
      case_revision_after
    from private.commit_phase8_case_decision_approval(
      p_rental_case_id => (select id from target_case),
      p_approval_request_id => (select id from target_approval),
      p_decision => 'approved',
      p_expected_case_revision => 0,
      p_actor_type => 'operator',
      p_actor_reference => 'operator:986',
      p_decision_payload => '{"decision":"approved"}'::jsonb,
      p_decision_notes => null,
      p_decided_at => '2026-08-13T12:05:00Z'::timestamptz
    )
  $sql$,
  $sql$
    values (
      'stale_case_revision'::text,
      1::integer,
      1::integer
    )
  $sql$,
  'stale case-decision approval fails closed without partial mutation'
);

with target_case as (
  select id
  from public.rental_cases
  where case_reference_code = 'RC-987'
),
inserted_action as (
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
    'open_question:987',
    '{"fixture":true}'::jsonb,
    'approval_required',
    'awaiting_approval',
    'subject:987',
    0,
    'idem:987',
    timezone('utc', now()),
    timezone('utc', now())
  from target_case
  returning id, rental_case_id
)
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
  rental_case_id,
  'workflow_action',
  id,
  concat('workflow_action:', id),
  'workflow_action_release',
  'Action release requires approval.',
  'manager:987',
  'open',
  timezone('utc', now()),
  timezone('utc', now())
from inserted_action;

with target_case as (
  select id
  from public.rental_cases
  where case_reference_code = 'RC-987'
),
target_action as (
  select id
  from public.workflow_actions
  where rental_case_id = (select id from target_case)
)
insert into public.rental_case_blockers (
  rental_case_id,
  blocker_type,
  blocked_subject_type,
  blocked_subject_id,
  blocked_subject_reference,
  origin_entity_type,
  origin_entity_id,
  origin_entity_reference,
  severity,
  status,
  resolution_condition_text,
  opened_at,
  created_at,
  updated_at
)
select
  tc.id,
  'approval_pending_workflow_action',
  'action',
  ta.id,
  concat('workflow_action:', ta.id),
  'workflow_action',
  ta.id,
  concat('workflow_action:', ta.id),
  'high',
  'open',
  'Action must be approved or rejected.',
  timezone('utc', now()),
  timezone('utc', now()),
  timezone('utc', now())
from target_case tc
cross join target_action ta;

select results_eq(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-987'
    ),
    target_approval as (
      select id
      from public.rental_case_approval_requests
      where rental_case_id = (select id from target_case)
    )
    select
      approval_status,
      action_status_before,
      action_status_after,
      cardinality(audit_event_ids),
      cardinality(resolved_blocker_ids),
      failure_code is null
    from private.commit_phase8_workflow_action_approval(
      p_rental_case_id => (select id from target_case),
      p_approval_request_id => (select id from target_approval),
      p_decision => 'approved',
      p_expected_case_revision => 0,
      p_actor_type => 'operator',
      p_actor_reference => 'operator:987',
      p_decision_payload => '{"decision":"approved"}'::jsonb,
      p_decision_notes => null,
      p_decided_at => '2026-08-13T12:10:00Z'::timestamptz
    )
  $sql$,
  $sql$
    values (
      'approved'::text,
      'awaiting_approval'::text,
      'ready_to_execute'::text,
      4::integer,
      1::integer,
      true
    )
  $sql$,
  'workflow-action approval advances state without executing the action'
);

select results_eq(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-987'
    )
    select
      action.status,
      approval.status,
      blocker.status,
      (
        select count(*)
        from public.workflow_execution_attempts attempt
        where attempt.rental_case_id = rc.id
      )::bigint
    from public.rental_cases rc
    join public.workflow_actions action
      on action.rental_case_id = rc.id
    join public.rental_case_approval_requests approval
      on approval.rental_case_id = rc.id
    join public.rental_case_blockers blocker
      on blocker.rental_case_id = rc.id
    where rc.id = (select id from target_case)
  $sql$,
  $sql$
    values (
      'ready_to_execute'::text,
      'approved'::text,
      'resolved'::text,
      0::bigint
    )
  $sql$,
  'workflow-action approval leaves execution attempts untouched while exposing ready state'
);

with target_case as (
  select id
  from public.rental_cases
  where case_reference_code = 'RC-988'
)
insert into public.rental_case_facts (
  rental_case_id,
  field_code,
  domain_code,
  value_payload,
  source_reference,
  established_case_revision,
  created_at,
  updated_at
)
select
  id,
  'guest_count',
  'operations',
  '20'::jsonb,
  'source:initial:988',
  0,
  timezone('utc', now()),
  timezone('utc', now())
from target_case;

with target_case as (
  select id
  from public.rental_cases
  where case_reference_code = 'RC-988'
)
insert into public.rental_case_proposed_changes (
  rental_case_id,
  change_kind,
  domain_code,
  prior_value_payload,
  proposed_value_payload,
  source_reference,
  detected_at,
  impact_classification,
  review_posture,
  status,
  created_at,
  updated_at
)
select
  id,
  'guest_count',
  'operations',
  '20'::jsonb,
  '30'::jsonb,
  'observation:guest_count:988',
  timezone('utc', now()),
  'material_impact',
  'automatic_allowed',
  'proposed',
  timezone('utc', now()),
  timezone('utc', now())
from target_case;

with target_case as (
  select id
  from public.rental_cases
  where case_reference_code = 'RC-988'
)
insert into public.rental_case_artifacts (
  rental_case_id,
  artifact_type,
  storage_reference,
  derived_from_case_revision,
  freshness_status,
  created_at,
  updated_at
)
select
  id,
  'proposal',
  'artifact:proposal:988',
  0,
  'current',
  timezone('utc', now()),
  timezone('utc', now())
from target_case;

with target_case as (
  select id
  from public.rental_cases
  where case_reference_code = 'RC-988'
)
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
  'open_question:988',
  '{"fixture":true}'::jsonb,
  'approval_required',
  'awaiting_approval',
  'subject:988',
  0,
  'idem:988',
  timezone('utc', now()),
  timezone('utc', now())
from target_case;

with target_case as (
  select id
  from public.rental_cases
  where case_reference_code = 'RC-988'
),
target_change as (
  select id
  from public.rental_case_proposed_changes
  where rental_case_id = (select id from target_case)
)
insert into public.rental_case_blockers (
  rental_case_id,
  blocker_type,
  blocked_subject_type,
  blocked_subject_reference,
  origin_entity_type,
  origin_entity_id,
  origin_entity_reference,
  severity,
  status,
  resolution_condition_text,
  opened_at,
  created_at,
  updated_at
)
select
  tc.id,
  'change_review_pending',
  'transition',
  'proposed_change:988',
  'proposed_case_change',
  pc.id,
  concat('proposed_change:', pc.id),
  'high',
  'open',
  'Change must be accepted or rejected.',
  timezone('utc', now()),
  timezone('utc', now()),
  timezone('utc', now())
from target_case tc
cross join target_change pc;

select results_eq(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-988'
    ),
    target_change as (
      select id
      from public.rental_case_proposed_changes
      where rental_case_id = (select id from target_case)
    )
    select
      resulting_status,
      case_revision_before,
      case_revision_after,
      updated_rental_case_fact_id is not null,
      cardinality(audit_event_ids),
      cardinality(artifact_freshness_changed_ids),
      cardinality(superseded_action_ids),
      failure_code is null
    from private.commit_phase8_proposed_case_change_resolution(
      p_rental_case_id => (select id from target_case),
      p_proposed_case_change_id => (select id from target_change),
      p_decision => 'approved',
      p_expected_case_revision => 0,
      p_actor_type => 'operator',
      p_actor_reference => 'operator:988',
      p_final_value_payload => null,
      p_decision_notes => null,
      p_decided_at => '2026-08-13T12:15:00Z'::timestamptz
    )
  $sql$,
  $sql$
    values (
      'accepted'::text,
      0::integer,
      1::integer,
      true,
      5::integer,
      1::integer,
      1::integer,
      true
    )
  $sql$,
  'proposed-change acceptance atomically updates case truth, freshness, and audit state'
);

select results_eq(
  $sql$
    with target_case as (
      select id
      from public.rental_cases
      where case_reference_code = 'RC-988'
    )
    select
      rc.case_revision,
      change.status,
      fact.value_payload,
      fact.established_case_revision,
      artifact.freshness_status,
      action.status,
      blocker.status,
      (
        select count(*)
        from public.rental_case_lifecycle_transitions transition_history
        where transition_history.rental_case_id = rc.id
      )::bigint
    from public.rental_cases rc
    join public.rental_case_proposed_changes change
      on change.rental_case_id = rc.id
    join public.rental_case_facts fact
      on fact.rental_case_id = rc.id
     and fact.field_code = 'guest_count'
    join public.rental_case_artifacts artifact
      on artifact.rental_case_id = rc.id
    join public.workflow_actions action
      on action.rental_case_id = rc.id
    join public.rental_case_blockers blocker
      on blocker.rental_case_id = rc.id
    where rc.id = (select id from target_case)
  $sql$,
  $sql$
    values (
      1::integer,
      'accepted'::text,
      '30'::jsonb,
      1::integer,
      'refresh_required'::text,
      'superseded'::text,
      'resolved'::text,
      0::bigint
    )
  $sql$,
  'proposed-change acceptance updates canonical fact state without mutating lifecycle history'
);

select * from finish();

rollback;
