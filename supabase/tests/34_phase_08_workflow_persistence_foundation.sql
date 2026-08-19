begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

select plan(40);

create or replace function public._test_count_as(p_role name, p_sql text)
returns bigint
language plpgsql
as $$
declare
  result bigint;
begin
  execute format('set local role %I', p_role);
  execute format('select count(*) from (%s) q', p_sql) into result;
  execute 'reset role';
  return result;
exception when others then
  begin
    execute 'reset role';
  exception when others then
    null;
  end;
  raise;
end;
$$;

select results_eq(
  $sql$
    with protected_tables(table_name) as (
      values
        ('rental_cases'),
        ('workflow_events'),
        ('rental_case_lifecycle_transitions'),
        ('rental_case_open_questions'),
        ('rental_case_requirements'),
        ('rental_case_blockers'),
        ('rental_case_decisions'),
        ('rental_case_proposed_changes'),
        ('rental_case_reschedule_requests'),
        ('rental_case_approval_requests'),
        ('workflow_actions'),
        ('workflow_execution_attempts'),
        ('rental_case_follow_ups'),
        ('rental_case_milestones'),
        ('rental_case_artifacts'),
        ('rental_case_reasoning_projections')
    )
    select c.relname
    from protected_tables pt
    join pg_class c
      on c.relname = pt.table_name
    join pg_namespace n
      on n.oid = c.relnamespace
    where n.nspname = 'public'
      and c.relrowsecurity
    order by c.relname
  $sql$,
  $sql$
    values
      ('rental_case_approval_requests'::name),
      ('rental_case_artifacts'::name),
      ('rental_case_blockers'::name),
      ('rental_case_decisions'::name),
      ('rental_case_follow_ups'::name),
      ('rental_case_lifecycle_transitions'::name),
      ('rental_case_milestones'::name),
      ('rental_case_open_questions'::name),
      ('rental_case_proposed_changes'::name),
      ('rental_case_reasoning_projections'::name),
      ('rental_case_requirements'::name),
      ('rental_case_reschedule_requests'::name),
      ('rental_cases'::name),
      ('workflow_actions'::name),
      ('workflow_events'::name),
      ('workflow_execution_attempts'::name)
  $sql$,
  'RLS is enabled on all new Phase 8 workflow persistence tables'
);

select is(
  (
    with protected_tables(table_name) as (
      values
        ('rental_cases'),
        ('workflow_events'),
        ('rental_case_lifecycle_transitions'),
        ('rental_case_open_questions'),
        ('rental_case_requirements'),
        ('rental_case_blockers'),
        ('rental_case_decisions'),
        ('rental_case_proposed_changes'),
        ('rental_case_reschedule_requests'),
        ('rental_case_approval_requests'),
        ('workflow_actions'),
        ('workflow_execution_attempts'),
        ('rental_case_follow_ups'),
        ('rental_case_milestones'),
        ('rental_case_artifacts'),
        ('rental_case_reasoning_projections')
    )
    select count(*)
    from information_schema.role_table_grants rtg
    join protected_tables pt
      on pt.table_name = rtg.table_name
    where rtg.table_schema = 'public'
      and rtg.grantee in ('anon', 'authenticated', 'service_role')
      and rtg.privilege_type in ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'REFERENCES', 'TRIGGER', 'TRUNCATE')
  ),
  0::bigint,
  'new Phase 8 base tables grant no direct ordinary-role privileges'
);

select ok(to_regclass('public.rental_cases') is not null, 'rental_cases table exists');
select ok(to_regclass('public.workflow_events') is not null, 'workflow_events table exists');
select ok(to_regclass('public.rental_case_decisions') is not null, 'rental_case_decisions table exists');
select ok(to_regclass('public.workflow_actions') is not null, 'workflow_actions table exists');
select ok(to_regclass('public.workflow_execution_attempts') is not null, 'workflow_execution_attempts table exists');
select ok(to_regclass('public.rental_case_reasoning_projections') is not null, 'rental_case_reasoning_projections table exists');

select lives_ok(
  $sql$
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
    values (
      'RC-900',
      'inquiry_active',
      0,
      'studio_space',
      'studio_rental',
      'client:rc900',
      'contact:rc900',
      'unknown',
      'unknown',
      true
    );
  $sql$,
  'valid rental case can be created'
);

select throws_ok(
  $sql$
    insert into public.rental_cases (
      case_reference_code,
      lifecycle_state,
      case_revision,
      rental_type_code,
      commercial_summary_status,
      operational_summary_status,
      is_active
    )
    values (
      'RC-901',
      'bad_state',
      0,
      'studio_space',
      'unknown',
      'unknown',
      true
    );
  $sql$,
  '23514',
  null,
  'invalid lifecycle state is rejected'
);

select throws_ok(
  $sql$
    insert into public.rental_cases (
      case_reference_code,
      lifecycle_state,
      case_revision,
      rental_type_code,
      commercial_summary_status,
      operational_summary_status,
      is_active
    )
    values (
      'RC-902',
      'inquiry_active',
      -1,
      'studio_space',
      'unknown',
      'unknown',
      true
    );
  $sql$,
  '23514',
  null,
  'negative case revision is rejected'
);

select throws_ok(
  $sql$
    insert into public.rental_cases (
      case_reference_code,
      lifecycle_state,
      case_revision,
      rental_type_code,
      commercial_summary_status,
      operational_summary_status,
      is_active
    )
    values (
      'RC-900',
      'inquiry_active',
      0,
      'studio_space',
      'unknown',
      'unknown',
      true
    );
  $sql$,
  '23505',
  null,
  'case reference code must be unique'
);

select lives_ok(
  $sql$
    do $$
    declare
      case_id bigint;
    begin
      select id into case_id
      from public.rental_cases
      where case_reference_code = 'RC-900';

      insert into public.workflow_events (
        rental_case_id,
        event_type_code,
        source_type,
        source_reference,
        occurred_at,
        recorded_at,
        structured_payload,
        event_identity_key,
        origin_metadata
      )
      values (
        case_id,
        'inquiry_received',
        'synthetic_fixture',
        'message:rc900:1',
        timezone('utc', now()),
        timezone('utc', now()),
        '{"subject":"hello"}'::jsonb,
        'evt:rc900:1',
        '{"fixture":true}'::jsonb
      );
    end
    $$;
  $sql$,
  'workflow event can be created for a valid case'
);

select throws_ok(
  $sql$
    do $$
    declare
      case_id bigint;
    begin
      select id into case_id
      from public.rental_cases
      where case_reference_code = 'RC-900';

      insert into public.workflow_events (
        rental_case_id,
        event_type_code,
        source_type,
        occurred_at,
        recorded_at,
        structured_payload,
        event_identity_key,
        origin_metadata
      )
      values (
        case_id,
        'client_information_received',
        'synthetic_fixture',
        timezone('utc', now()),
        timezone('utc', now()),
        '{"message":"duplicate"}'::jsonb,
        'evt:rc900:1',
        '{"fixture":true}'::jsonb
      );
    end
    $$;
  $sql$,
  '23505',
  null,
  'duplicate event identity key for the same case is rejected'
);

select is(
  (
    select lifecycle_state
    from public.rental_cases
    where case_reference_code = 'RC-900'
  ),
  'inquiry_active',
  'event insertion does not implicitly mutate lifecycle state'
);

select lives_ok(
  $sql$
    do $$
    declare
      case_id bigint;
    begin
      select id into case_id
      from public.rental_cases
      where case_reference_code = 'RC-900';

      insert into public.rental_case_open_questions (
        rental_case_id,
        question_type,
        domain_code,
        human_question_text,
        blocking_scope,
        status
      )
      values (
        case_id,
        'missing_client_detail',
        'commercial',
        'What date do you want?',
        'transition',
        'open'
      );
    end
    $$;
  $sql$,
  'valid open question can be created'
);

select throws_ok(
  $sql$
    do $$
    declare
      case_id bigint;
    begin
      select id into case_id
      from public.rental_cases
      where case_reference_code = 'RC-900';

      insert into public.rental_case_open_questions (
        rental_case_id,
        question_type,
        domain_code,
        human_question_text,
        blocking_scope,
        status
      )
      values (
        case_id,
        'missing_client_detail',
        'commercial',
        'Bad status question',
        'transition',
        'bad_status'
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'invalid open question status is rejected'
);

select lives_ok(
  $sql$
    do $$
    declare
      case_id bigint;
    begin
      select id into case_id
      from public.rental_cases
      where case_reference_code = 'RC-900';

      insert into public.rental_case_requirements (
        rental_case_id,
        requirement_type,
        domain_code,
        applicability_basis,
        status,
        blocking_scope
      )
      values (
        case_id,
        'confirmation_payment_required',
        'commercial',
        'booking confirmation',
        'required',
        'transition'
      );
    end
    $$;
  $sql$,
  'valid requirement can be created'
);

select throws_ok(
  $sql$
    do $$
    declare
      case_id bigint;
    begin
      select id into case_id
      from public.rental_cases
      where case_reference_code = 'RC-900';

      insert into public.rental_case_requirements (
        rental_case_id,
        requirement_type,
        domain_code,
        applicability_basis,
        status,
        blocking_scope
      )
      values (
        case_id,
        'confirmation_payment_required',
        'commercial',
        'booking confirmation',
        'bad_status',
        'transition'
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'invalid requirement status is rejected'
);

select lives_ok(
  $sql$
    do $$
    declare
      case_id bigint;
    begin
      select id into case_id
      from public.rental_cases
      where case_reference_code = 'RC-900';

      insert into public.rental_case_blockers (
        rental_case_id,
        blocker_type,
        blocked_subject_type,
        blocked_subject_reference,
        origin_entity_type,
        origin_entity_reference,
        severity,
        status,
        resolution_condition_text
      )
      values (
        case_id,
        'missing_info',
        'transition',
        'proposal_send',
        'open_question',
        'oq:900',
        'medium',
        'open',
        'Need answer'
      );
    end
    $$;
  $sql$,
  'valid blocker can be created'
);

select throws_ok(
  $sql$
    do $$
    declare
      case_id bigint;
    begin
      select id into case_id
      from public.rental_cases
      where case_reference_code = 'RC-900';

      insert into public.rental_case_blockers (
        rental_case_id,
        blocker_type,
        blocked_subject_type,
        blocked_subject_reference,
        origin_entity_type,
        origin_entity_reference,
        severity,
        status,
        resolution_condition_text
      )
      values (
        case_id,
        'missing_info',
        'transition',
        'proposal_send',
        'open_question',
        'oq:900',
        'medium',
        'bad_status',
        'Need answer'
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'invalid blocker status is rejected'
);

select lives_ok(
  $sql$
    do $$
    declare
      case_id bigint;
    begin
      select id into case_id
      from public.rental_cases
      where case_reference_code = 'RC-900';

      insert into public.rental_case_decisions (
        rental_case_id,
        decision_type,
        domain_code,
        baseline_reference,
        proposed_value_payload,
        effective_value_payload,
        scope_key,
        scope_description,
        authority_basis,
        approval_posture,
        status,
        effective_at
      )
      values (
        case_id,
        'fee_waiver',
        'booking_fee',
        'rule:booking_fee',
        '{"amount":0}'::jsonb,
        '{"amount":0}'::jsonb,
        'booking_fee:confirmation',
        'booking fee override',
        'manager approved',
        'human_only',
        'active',
        timezone('utc', now())
      );
    end
    $$;
  $sql$,
  'active case decision can be created'
);

select throws_ok(
  $sql$
    do $$
    declare
      case_id bigint;
    begin
      select id into case_id
      from public.rental_cases
      where case_reference_code = 'RC-900';

      insert into public.rental_case_decisions (
        rental_case_id,
        decision_type,
        domain_code,
        baseline_reference,
        proposed_value_payload,
        effective_value_payload,
        scope_key,
        scope_description,
        authority_basis,
        approval_posture,
        status,
        effective_at
      )
      values (
        case_id,
        'fee_waiver',
        'booking_fee',
        'rule:booking_fee',
        '{"amount":5}'::jsonb,
        '{"amount":5}'::jsonb,
        'booking_fee:confirmation',
        'conflicting booking fee override',
        'manager approved',
        'human_only',
        'active',
        timezone('utc', now())
      );
    end
    $$;
  $sql$,
  '23505',
  null,
  'conflicting active same-scope case decisions are rejected'
);

select lives_ok(
  $sql$
    do $$
    declare
      case_id bigint;
    begin
      select id into case_id
      from public.rental_cases
      where case_reference_code = 'RC-900';

      insert into public.rental_case_decisions (
        rental_case_id,
        decision_type,
        domain_code,
        baseline_reference,
        proposed_value_payload,
        scope_key,
        scope_description,
        authority_basis,
        approval_posture,
        status
      )
      values (
        case_id,
        'fee_waiver',
        'booking_fee',
        'rule:booking_fee',
        '{"amount":10}'::jsonb,
        'booking_fee:confirmation',
        'historical rejected alternative',
        'not approved',
        'approval_required',
        'rejected'
      );
    end
    $$;
  $sql$,
  'historical rejected case decisions may coexist with active history'
);

select throws_ok(
  $sql$
    do $$
    declare
      case_id bigint;
    begin
      select id into case_id
      from public.rental_cases
      where case_reference_code = 'RC-900';

      insert into public.rental_case_proposed_changes (
        rental_case_id,
        change_kind,
        domain_code,
        proposed_value_payload,
        impact_classification,
        status
      )
      values (
        case_id,
        'date_change',
        'timing',
        '{"start":"2026-09-01T10:00:00Z"}'::jsonb,
        'bad_impact',
        'proposed'
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'invalid change impact classification is rejected'
);

select throws_ok(
  $sql$
    do $$
    declare
      case_id bigint;
    begin
      select id into case_id
      from public.rental_cases
      where case_reference_code = 'RC-900';

      insert into public.rental_case_proposed_changes (
        rental_case_id,
        change_kind,
        domain_code,
        proposed_value_payload,
        impact_classification,
        status
      )
      values (
        case_id,
        'date_change',
        'timing',
        '{"start":"2026-09-01T10:00:00Z"}'::jsonb,
        'material_impact',
        'accepted'
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'accepted proposed change requires final value payload and accepted timestamp'
);

select throws_ok(
  $sql$
    do $$
    declare
      case_id bigint;
    begin
      select id into case_id
      from public.rental_cases
      where case_reference_code = 'RC-900';

      insert into public.rental_case_reschedule_requests (
        rental_case_id,
        current_active_date_snapshot,
        requested_date_payload,
        candidate_dates_payload,
        consequence_summary_payload,
        status,
        urgency_class
      )
      values (
        case_id,
        '{"start":"2026-09-01T10:00:00Z","end":"2026-09-01T12:00:00Z"}'::jsonb,
        '{"start":"2026-09-03T10:00:00Z","end":"2026-09-03T12:00:00Z"}'::jsonb,
        '[]'::jsonb,
        '{}'::jsonb,
        'confirmed',
        'normal'
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'confirmed reschedule request requires linked confirmed change'
);

select throws_ok(
  $sql$
    insert into public.rental_case_approval_requests (
      rental_case_id,
      target_entity_type,
      approval_type,
      reason_text,
      status
    )
    select
      id,
      'case_decision',
      'commercial_exception',
      'approval needed',
      'open'
    from public.rental_cases
    where case_reference_code = 'RC-900';
  $sql$,
  '23514',
  null,
  'approval request requires target entity id or reference'
);

select lives_ok(
  $sql$
    do $$
    declare
      case_id bigint;
    begin
      select id into case_id
      from public.rental_cases
      where case_reference_code = 'RC-900';

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
      values (
        case_id,
        'REQUEST_CLIENT_INFORMATION',
        'communication',
        'email',
        'open_question',
        'oq:900',
        '{"subject":"Need more info"}'::jsonb,
        'approval_required',
        'awaiting_approval',
        'hash:rc900:request-info',
        0,
        'action:rc900:request-info:v1'
      );
    end
    $$;
  $sql$,
  'valid workflow action can be created'
);

select throws_ok(
  $sql$
    do $$
    declare
      case_id bigint;
    begin
      select id into case_id
      from public.rental_cases
      where case_reference_code = 'RC-900';

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
        source_case_revision
      )
      values (
        case_id,
        'REQUEST_CLIENT_INFORMATION',
        'communication',
        'email',
        'open_question',
        'oq:900',
        '{"subject":"Need more info"}'::jsonb,
        'approval_required',
        'awaiting_approval',
        'hash:rc900:request-info:missing-key',
        0
      );
    end
    $$;
  $sql$,
  '23502',
  null,
  'workflow action requires idempotency key'
);

select throws_ok(
  $sql$
    do $$
    declare
      case_id bigint;
    begin
      select id into case_id
      from public.rental_cases
      where case_reference_code = 'RC-900';

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
      values (
        case_id,
        'REQUEST_CLIENT_INFORMATION',
        'communication',
        'email',
        'open_question',
        'oq:900b',
        '{"subject":"Need more info again"}'::jsonb,
        'approval_required',
        'awaiting_approval',
        'hash:rc900:request-info',
        0,
        'action:rc900:request-info:v1'
      );
    end
    $$;
  $sql$,
  '23505',
  null,
  'duplicate idempotency key for the same case is rejected'
);

select lives_ok(
  $sql$
    do $$
    declare
      action_id bigint;
      case_id bigint;
    begin
      select id, rental_case_id
      into action_id, case_id
      from public.workflow_actions
      where idempotency_key = 'action:rc900:request-info:v1';

      insert into public.workflow_execution_attempts (
        workflow_action_id,
        rental_case_id,
        attempt_number,
        adapter_code,
        started_at,
        completed_at,
        status,
        retry_eligible,
        response_snapshot
      )
      values (
        action_id,
        case_id,
        1,
        'email',
        timezone('utc', now()),
        timezone('utc', now()),
        'failed',
        true,
        '{"status":"failed"}'::jsonb
      );
    end
    $$;
  $sql$,
  'valid execution attempt can be created'
);

select throws_ok(
  $sql$
    do $$
    declare
      action_id bigint;
      case_id bigint;
    begin
      select id, rental_case_id
      into action_id, case_id
      from public.workflow_actions
      where idempotency_key = 'action:rc900:request-info:v1';

      insert into public.workflow_execution_attempts (
        workflow_action_id,
        rental_case_id,
        attempt_number,
        adapter_code,
        started_at,
        completed_at,
        status,
        retry_eligible,
        response_snapshot
      )
      values (
        action_id,
        case_id,
        1,
        'email',
        timezone('utc', now()),
        timezone('utc', now()),
        'timeout',
        false,
        '{"status":"timeout"}'::jsonb
      );
    end
    $$;
  $sql$,
  '23505',
  null,
  'duplicate execution attempt number for the same action is rejected'
);

select throws_ok(
  $sql$
    update public.workflow_events
    set event_type_code = 'mutated_event'
    where event_identity_key = 'evt:rc900:1';
  $sql$,
  '23514',
  null,
  'workflow events are append-only on update'
);

select throws_ok(
  $sql$
    delete from public.workflow_execution_attempts
    where attempt_number = 1;
  $sql$,
  '23514',
  null,
  'execution attempts are append-only on delete'
);

select throws_ok(
  $sql$
    insert into public.rental_case_follow_ups (
      rental_case_id,
      reason_code,
      due_at,
      urgency_level,
      attempt_count,
      status
    )
    select
      id,
      'client_reply_wait',
      timezone('utc', now()),
      'urgent',
      0,
      'bad_status'
    from public.rental_cases
    where case_reference_code = 'RC-900';
  $sql$,
  '23514',
  null,
  'invalid follow-up status is rejected'
);

select throws_ok(
  $sql$
    insert into public.rental_case_milestones (
      rental_case_id,
      milestone_type,
      target_at,
      status
    )
    select
      id,
      'proposal_follow_up_due',
      timezone('utc', now()),
      'bad_status'
    from public.rental_cases
    where case_reference_code = 'RC-900';
  $sql$,
  '23514',
  null,
  'invalid milestone status is rejected'
);

select throws_ok(
  $sql$
    insert into public.rental_case_artifacts (
      rental_case_id,
      artifact_type,
      derived_from_case_revision,
      freshness_status
    )
    select
      id,
      'proposal',
      -1,
      'current'
    from public.rental_cases
    where case_reference_code = 'RC-900';
  $sql$,
  '23514',
  null,
  'negative artifact revision is rejected'
);

select throws_ok(
  $sql$
    insert into public.rental_case_reasoning_projections (
      rental_case_id,
      reasoning_purpose,
      phase_7_context_contract_version,
      phase_8_workflow_contract_version,
      source_case_revision,
      authority_outcome_classification,
      conflict_codes,
      degraded_retrieval_summary
    )
    select
      id,
      'proposal_readiness_review',
      1,
      1,
      0,
      'DETERMINISTIC_CURRENT',
      array['TYPE_Z_UNKNOWN']::text[],
      '{}'::jsonb
    from public.rental_cases
    where case_reference_code = 'RC-900';
  $sql$,
  '23514',
  null,
  'invalid reasoning projection conflict code is rejected'
);

select throws_ok(
  $sql$
    delete from public.rental_cases
    where case_reference_code = 'RC-900';
  $sql$,
  '23503',
  null,
  'rental case deletion is restricted when workflow history exists'
);

select * from finish();

rollback;
