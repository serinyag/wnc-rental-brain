begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

select plan(11);

select ok(
  exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'rental_case_reasoning_projections'
      and column_name = 'projection_identity_key'
  ),
  'projection_identity_key column exists on rental_case_reasoning_projections'
);

select ok(
  exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'rental_case_reasoning_projections'
      and column_name = 'workflow_posture'
  ),
  'workflow_posture column exists on rental_case_reasoning_projections'
);

select ok(
  exists (
    select 1
    from pg_indexes
    where schemaname = 'public'
      and tablename = 'rental_case_reasoning_projections'
      and indexname = 'rental_case_reasoning_projections_case_identity_key_unique'
  ),
  'case-scoped unique identity index exists for reasoning projections'
);

insert into public.rental_cases (
  case_reference_code,
  lifecycle_state,
  case_revision,
  rental_type_code,
  commercial_summary_status,
  operational_summary_status,
  is_active
)
values
  ('RC-970', 'inquiry_active', 0, 'studio_space', 'unknown', 'unknown', true),
  ('RC-971', 'inquiry_active', 0, 'studio_space', 'unknown', 'unknown', true);

select lives_ok(
  $sql$
    insert into public.rental_case_reasoning_projections (
      rental_case_id,
      reasoning_purpose,
      phase_7_context_contract_version,
      phase_8_workflow_contract_version,
      source_case_revision,
      authority_outcome_classification,
      projection_identity_key,
      reasoning_state_code,
      workflow_posture,
      effective_confidentiality_level,
      de_identification_required,
      personal_information_present,
      materially_affects_completeness,
      degraded_retrieval_summary
    )
    select
      id,
      'proposal_readiness_review',
      1,
      1,
      0,
      'DETERMINISTIC_CURRENT',
      'p7wf:test-1',
      'resolved',
      'safe_for_deterministic_use',
      'internal',
      false,
      false,
      false,
      '{"any_degradation": false}'::jsonb
    from public.rental_cases
    where case_reference_code = 'RC-970';
  $sql$,
  'reasoning projection accepts new Phase 8.4 workflow-consumption fields'
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
      projection_identity_key,
      degraded_retrieval_summary
    )
    select
      id,
      'proposal_readiness_review',
      1,
      1,
      0,
      'DETERMINISTIC_CURRENT',
      'p7wf:test-1',
      '{}'::jsonb
    from public.rental_cases
    where case_reference_code = 'RC-970';
  $sql$,
  '23505',
  null,
  'projection identity key is unique within a rental case'
);

select lives_ok(
  $sql$
    insert into public.rental_case_reasoning_projections (
      rental_case_id,
      reasoning_purpose,
      phase_7_context_contract_version,
      phase_8_workflow_contract_version,
      source_case_revision,
      authority_outcome_classification,
      projection_identity_key,
      degraded_retrieval_summary
    )
    select
      id,
      'proposal_readiness_review',
      1,
      1,
      0,
      'DETERMINISTIC_CURRENT',
      'p7wf:test-1',
      '{}'::jsonb
    from public.rental_cases
    where case_reference_code = 'RC-971';
  $sql$,
  'projection identity key may repeat across different rental cases'
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
      projection_identity_key,
      reasoning_state_code,
      degraded_retrieval_summary
    )
    select
      id,
      'proposal_readiness_review',
      1,
      1,
      0,
      'DETERMINISTIC_CURRENT',
      'p7wf:bad-state',
      'bad_state',
      '{}'::jsonb
    from public.rental_cases
    where case_reference_code = 'RC-970';
  $sql$,
  '23514',
  null,
  'invalid reasoning_state_code is rejected'
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
      projection_identity_key,
      workflow_posture,
      degraded_retrieval_summary
    )
    select
      id,
      'proposal_readiness_review',
      1,
      1,
      0,
      'DETERMINISTIC_CURRENT',
      'p7wf:bad-posture',
      'bad_posture',
      '{}'::jsonb
    from public.rental_cases
    where case_reference_code = 'RC-970';
  $sql$,
  '23514',
  null,
  'invalid workflow_posture is rejected'
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
      projection_identity_key,
      effective_confidentiality_level,
      degraded_retrieval_summary
    )
    select
      id,
      'proposal_readiness_review',
      1,
      1,
      0,
      'DETERMINISTIC_CURRENT',
      'p7wf:bad-confidentiality',
      'top_secret',
      '{}'::jsonb
    from public.rental_cases
    where case_reference_code = 'RC-970';
  $sql$,
  '23514',
  null,
  'invalid effective_confidentiality_level is rejected'
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
      projection_identity_key,
      degraded_retrieval_summary
    )
    select
      id,
      'proposal_readiness_review',
      1,
      1,
      0,
      'DETERMINISTIC_CURRENT',
      '   ',
      '{}'::jsonb
    from public.rental_cases
    where case_reference_code = 'RC-970';
  $sql$,
  '23514',
  null,
  'blank projection_identity_key is rejected'
);

select row_eq(
  $sql$
    select
      de_identification_required,
      personal_information_present,
      materially_affects_completeness
    from public.rental_case_reasoning_projections
    where projection_identity_key = 'p7wf:test-1'
      and rental_case_id = (
        select id from public.rental_cases where case_reference_code = 'RC-970'
      )
  $sql$,
  row(false, false, false),
  'new boolean workflow-consumption safety fields persist as expected'
);

select * from finish();

rollback;
