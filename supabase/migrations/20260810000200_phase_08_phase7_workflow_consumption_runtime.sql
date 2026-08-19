alter table public.rental_case_reasoning_projections
  add column if not exists projection_identity_key text,
  add column if not exists reasoning_state_code text,
  add column if not exists workflow_posture text,
  add column if not exists effective_confidentiality_level text,
  add column if not exists de_identification_required boolean not null default false,
  add column if not exists personal_information_present boolean not null default false,
  add column if not exists materially_affects_completeness boolean not null default false;

alter table public.rental_case_reasoning_projections
  drop constraint if exists rental_case_reasoning_projections_projection_identity_key_nonempty,
  add constraint rental_case_reasoning_projections_projection_identity_key_nonempty
    check (projection_identity_key is null or btrim(projection_identity_key) <> ''),
  drop constraint if exists rental_case_reasoning_projections_reasoning_state_code_check,
  add constraint rental_case_reasoning_projections_reasoning_state_code_check
    check (
      reasoning_state_code is null
      or reasoning_state_code in (
        'resolved',
        'requires_confirmation',
        'insufficient_information',
        'no_applicable_rule',
        'manual_review_required',
        'current_status_unknown',
        'insufficient_current_authority'
      )
    ),
  drop constraint if exists rental_case_reasoning_projections_workflow_posture_check,
  add constraint rental_case_reasoning_projections_workflow_posture_check
    check (
      workflow_posture is null
      or workflow_posture in (
        'safe_for_deterministic_use',
        'guidance_only',
        'historical_context_only',
        'review_required',
        'blocked_for_current_decision'
      )
    ),
  drop constraint if exists rental_case_reasoning_projections_effective_confidentiality_level_check,
  add constraint rental_case_reasoning_projections_effective_confidentiality_level_check
    check (
      effective_confidentiality_level is null
      or effective_confidentiality_level in (
        'externally_shareable',
        'internal',
        'commercially_sensitive',
        'restricted'
      )
    );

create unique index if not exists rental_case_reasoning_projections_case_identity_key_unique
  on public.rental_case_reasoning_projections (rental_case_id, projection_identity_key)
  where projection_identity_key is not null;
