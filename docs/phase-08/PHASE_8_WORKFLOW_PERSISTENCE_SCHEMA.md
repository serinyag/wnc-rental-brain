# Phase 8 Workflow Persistence Schema

Canonical reference for the Phase 8.1 workflow persistence model.

## Namespace

Entity tables live in `public`.

Workflow helper functions live in `private`.

This keeps workflow persistence separate from Phase 4 authority storage, Phase 5 knowledge storage, and Phase 6 historical precedent storage while staying aligned with repository conventions for canonical governed entities.

## Helper Functions

### `private.workflow_text_array_values_nonempty(...)`

- Purpose: validate text-array payloads contain only non-empty trimmed strings.
- Used by: reasoning projection arrays.
- Mutability: helper only.

### `private.workflow_text_array_values_allowed(...)`

- Purpose: validate text-array payloads against controlled vocabularies.
- Used by: reasoning projection conflict and contamination code arrays.
- Mutability: helper only.

### `private.workflow_append_only_guard()`

- Purpose: reject updates and deletes on append-only tables.
- Used by: workflow events, lifecycle transitions, execution attempts, reasoning projections, inbound source records, inbound observation effects.
- Mutability: helper only.

## `public.rental_cases`

- Purpose: aggregate root for case-scoped workflow truth.
- Primary key: `id bigint`.
- Stable identifiers: `rental_case_uuid uuid`, `case_reference_code text`.
- Important fields: `lifecycle_state`, `case_revision`, `active_event_start`, `active_event_end`, `rental_type_code`, `service_level_or_type`, `client_account_ref`, `primary_contact_ref`, `commercial_summary_status`, `operational_summary_status`, `is_active`.
- Lifecycle values: `inquiry_active`, `proposal_in_progress`, `proposal_pending_client`, `confirmation_pending`, `confirmed_pre_event`, `event_ready`, `event_in_progress`, `close_out_in_progress`, `dormant`, `closed`, `closed_lost`, `cancelled`.
- FKs: `rental_type_code -> public.rental_types`, current proposal / agreement artifact pointers -> `public.rental_case_artifacts`.
- Uniqueness: `rental_case_uuid`, `case_reference_code`.
- Indexes: `rental_cases_active_lifecycle_state_idx`, `rental_cases_active_event_start_idx`.
- Mutability posture: mutable current-state row with `updated_at` touch trigger.

## `public.rental_case_facts`

- Purpose: governed structured current-scope snapshot support for case facts that are neither global Phase 4 rules nor case decisions.
- Primary key: `id bigint`.
- Important fields: `field_code`, `domain_code`, `value_payload`, `source_reference`, `established_case_revision`.
- FKs: `rental_case_id -> public.rental_cases`.
- Uniqueness: fact UUID; one row per `(rental_case_id, field_code)`.
- Indexes: `rental_case_facts_case_domain_idx`.
- Mutability posture: mutable current-state row with `updated_at` touch trigger.

## `public.workflow_events`

- Purpose: append-only workflow fact/event journal.
- Primary key: `id bigint`.
- Important fields: `workflow_event_uuid`, `rental_case_id`, `event_type_code`, `source_type`, `source_reference`, `actor_type`, `actor_reference`, `occurred_at`, `recorded_at`, `structured_payload`, `event_identity_key`, `origin_metadata`.
- FKs: `rental_case_id -> public.rental_cases`.
- Uniqueness: `workflow_event_uuid`, `(rental_case_id, event_identity_key)`.
- Indexes: `workflow_events_case_occurred_at_idx`.
- Mutability posture: append-only; update and delete blocked by trigger.

## `public.inbound_source_records`

- Purpose: provider-neutral normalized inbound source boundary before structured workflow routing.
- Primary key: `id bigint`.
- Important fields: `source_system_code`, `source_record_type`, `dedupe_key`, `source_hash`, `external_source_id`, `conversation_reference`, `sender_actor_type`, `sender_actor_reference`, `case_reference_hint`, `resolved_rental_case_id`, `association_status`, `association_basis`, `occurred_at`, `received_at`, `source_location_reference`, `confidentiality_posture`, `pi_posture`, `evidence_excerpt`.
- Source-system values: `email`, `manual_input`, `intake_form`, `external_platform`, `call_summary`, `site_visit_summary`, `supplier_communication`, `integration_event`.
- Association-status values: `resolved`, `case_association_required`, `rejected`.
- FKs: optional `resolved_rental_case_id -> public.rental_cases`.
- Uniqueness: source UUID; `(source_system_code, dedupe_key)`.
- Indexes: `inbound_source_records_case_occurred_at_idx`.
- Mutability posture: append-only; update and delete blocked by trigger.

## `public.inbound_observations`

- Purpose: structured candidate observations derived from inbound sources without becoming case truth themselves.
- Primary key: `id bigint`.
- Important fields: `inbound_source_record_id`, `rental_case_id`, `reported_field_code`, `reported_domain_code`, `target_field_code`, `target_domain_code`, `observation_type`, `claim_kind`, `candidate_value_payload`, `source_evidence_reference`, `status`, `observation_identity_key`, `asserted_by_party_type`, `asserted_by_reference`, `source_excerpt`, `observed_against_case_revision`, `extraction_confidence`, `ambiguity_flags`, `supersedes_inbound_observation_id`.
- Observation-type values: `fact_candidate`, `request_candidate`, `change_candidate`, `confirmation_candidate`, `case_decision_candidate`, `requirement_evidence_candidate`, `unknown_or_unmapped`.
- Status values: `candidate`, `validated`, `rejected`, `consumed`, `superseded`, `unmapped`, `quarantined`.
- FKs: `inbound_source_record_id -> public.inbound_source_records`, optional `rental_case_id -> public.rental_cases`, optional `supersedes_inbound_observation_id -> public.inbound_observations`.
- Uniqueness: observation UUID; `(inbound_source_record_id, observation_identity_key)`.
- Indexes: `inbound_observations_case_status_idx`.
- Mutability posture: mutable current-state row with `updated_at` touch trigger so later review can move status without losing the original observation row.

## `public.inbound_observation_effects`

- Purpose: append-only deterministic routing result linking an observation to a safe proposed workflow effect.
- Primary key: `id bigint`.
- Important fields: `inbound_observation_id`, `rental_case_id`, `disposition_code`, `revalidation_required`, `stale_observation`, `reason_codes`, `linked_open_question_id`, `linked_requirement_id`, `linked_proposed_change_id`, `linked_case_decision_id`, `linked_reschedule_request_id`, `workflow_event_id`.
- Disposition values: `no_workflow_effect`, `open_question_answer_candidate`, `create_proposed_change`, `create_case_decision_candidate`, `create_reschedule_request`, `record_confirmation_candidate`, `record_requirement_evidence_candidate`, `manual_mapping_required`, `reject_quarantine`, `case_association_required`.
- FKs: `inbound_observation_id -> public.inbound_observations`, optional same-case links into `rental_case_open_questions`, `rental_case_requirements`, `rental_case_proposed_changes`, `rental_case_decisions`, `rental_case_reschedule_requests`, and `workflow_events`.
- Uniqueness: effect UUID; one effect row per `inbound_observation_id`.
- Indexes: `inbound_observation_effects_case_created_at_idx`.
- Mutability posture: append-only; update and delete blocked by trigger so the original disposition chain remains auditable.

## `public.rental_case_lifecycle_transitions`

- Purpose: append-only lifecycle transition history.
- Primary key: `id bigint`.
- Important fields: `from_lifecycle_state`, `to_lifecycle_state`, `triggering_event_id`, `source_type`, `source_reference`, `actor_type`, `actor_reference`, `transition_reason_code`, `override_applied`, `case_revision_before`, `case_revision_after`, `occurred_at`.
- Status values: same frozen lifecycle-state set as `rental_cases`.
- FKs: `rental_case_id -> public.rental_cases`, `(triggering_event_id, rental_case_id) -> public.workflow_events`.
- Uniqueness: transition UUID, `(id, rental_case_id)` pair for same-case joins.
- Indexes: `rental_case_lifecycle_transitions_case_occurred_at_idx`.
- Mutability posture: append-only; update and delete blocked by trigger.

## `public.rental_case_decisions`

- Purpose: case-specific decision and override persistence without mutating Phase 4.
- Primary key: `id bigint`.
- Important fields: `decision_type`, `domain_code`, `baseline_reference`, `proposed_value_payload`, `effective_value_payload`, `scope_key`, `scope_description`, `evidence_reference`, `authority_basis`, `approval_posture`, `approval_request_id`, `status`, `effective_at`, `supersedes_case_decision_id`.
- Status values: `proposed`, `pending_approval`, `active`, `rejected`, `superseded`, `withdrawn`.
- Approval posture values: `automatic_allowed`, `approval_required`, `human_only`, `blocked`.
- FKs: `rental_case_id -> public.rental_cases`, same-case `supersedes_case_decision_id`, same-case `approval_request_id`.
- Uniqueness: decision UUID; active-scope partial uniqueness on `(rental_case_id, domain_code, scope_key)` where `status = 'active'`.
- Indexes: `rental_case_decisions_active_scope_unique_idx`, `rental_case_decisions_case_status_idx`.
- Mutability posture: mutable current-state row with `updated_at` touch trigger.

## `public.rental_case_requirements`

- Purpose: case-scoped workflow requirements and their status.
- Primary key: `id bigint`.
- Important fields: `requirement_type`, `domain_code`, `applicability_basis`, `owner_role`, `owner_reference`, `due_at`, `status`, `blocking_scope`, `evidence_reference`, `waiver_case_decision_id`, `resolved_at`.
- Status values: `not_applicable`, `required`, `in_progress`, `satisfied`, `waived`, `unresolved`.
- Blocking-scope values: `none`, `action`, `transition`, `readiness`, `commercial_scope`.
- FKs: `rental_case_id -> public.rental_cases`, same-case `waiver_case_decision_id -> public.rental_case_decisions`.
- Indexes: `rental_case_requirements_open_due_idx`.
- Mutability posture: mutable current-state row with `updated_at` touch trigger.

## `public.rental_case_open_questions`

- Purpose: unresolved or superseded workflow questions.
- Primary key: `id bigint`.
- Important fields: `question_type`, `domain_code`, `human_question_text`, `blocking_scope`, `requested_from_role`, `status`, `proposed_answer_payload`, `source_reference`, `supersedes_open_question_id`, `resolved_at`.
- Status values: `open`, `answered_pending_validation`, `resolved`, `closed_not_needed`, `superseded`.
- FKs: `rental_case_id -> public.rental_cases`, same-case `supersedes_open_question_id -> public.rental_case_open_questions`.
- Indexes: `rental_case_open_questions_unresolved_idx`.
- Mutability posture: mutable current-state row with `updated_at` touch trigger.

## `public.rental_case_blockers`

- Purpose: explicit blockers for transitions, actions, readiness, decisions, or artifact refresh.
- Primary key: `id bigint`.
- Important fields: `blocker_type`, `blocked_subject_type`, `blocked_subject_id`, `blocked_subject_reference`, `origin_entity_type`, `origin_entity_id`, `origin_entity_reference`, `severity`, `status`, `resolution_condition_text`, `resolution_reference`, `supersedes_blocker_id`, `resolved_at`.
- Status values: `open`, `resolved`, `superseded`, `cancelled`.
- Severity values: `low`, `medium`, `high`.
- Blocked subject values: `transition`, `action`, `readiness`, `decision`, `artifact_refresh`.
- FKs: `rental_case_id -> public.rental_cases`, same-case `supersedes_blocker_id -> public.rental_case_blockers`.
- Indexes: `rental_case_blockers_open_idx`.
- Mutability posture: mutable current-state row with `updated_at` touch trigger.

## `public.rental_case_proposed_changes`

- Purpose: material changes that must stay proposed until accepted.
- Primary key: `id bigint`.
- Important fields: `change_kind`, `domain_code`, `prior_value_payload`, `proposed_value_payload`, `source_reference`, `detected_at`, `impact_classification`, `affected_domains`, `review_posture`, `status`, `accepted_value_payload`, `accepted_at`, `supersedes_proposed_change_id`.
- Status values: `proposed`, `under_review`, `accepted`, `rejected`, `superseded`, `withdrawn`.
- Impact values: `low_impact`, `material_impact`, `fundamental_scope_change`.
- FKs: `rental_case_id -> public.rental_cases`, same-case `supersedes_proposed_change_id -> public.rental_case_proposed_changes`.
- Indexes: `rental_case_proposed_changes_active_idx`.
- Mutability posture: mutable current-state row with `updated_at` touch trigger.

## `public.rental_case_reschedule_requests`

- Purpose: specialized negotiated date-change state.
- Primary key: `id bigint`.
- Important fields: `current_active_date_snapshot`, `requested_date_payload`, `candidate_dates_payload`, `consequence_summary_payload`, `status`, `urgency_class`, `confirmed_proposed_change_id`, `confirmed_value_payload`, `confirmed_at`, `supersedes_reschedule_request_id`.
- Status values: `proposed`, `evaluating`, `offered`, `awaiting_client_confirmation`, `confirmed`, `rejected`, `withdrawn`, `superseded`.
- Urgency values: `normal`, `urgent_impact`.
- FKs: `rental_case_id -> public.rental_cases`, same-case `confirmed_proposed_change_id -> public.rental_case_proposed_changes`, same-case `supersedes_reschedule_request_id -> public.rental_case_reschedule_requests`.
- Indexes: `rental_case_reschedule_requests_active_idx`.
- Mutability posture: mutable current-state row with `updated_at` touch trigger.

## `public.rental_case_approval_requests`

- Purpose: interface-independent approval truth.
- Primary key: `id bigint`.
- Important fields: `target_entity_type`, `target_entity_id`, `target_entity_reference`, `approval_type`, `reason_text`, `evidence_references`, `required_approver_role`, `required_approver_reference`, `status`, `decision_payload`, `decision_at`, `decided_by_reference`, `decision_notes`, `supersedes_approval_request_id`.
- Status values: `open`, `approved`, `rejected`, `expired`, `cancelled`, `superseded`.
- FKs: `rental_case_id -> public.rental_cases`, same-case `supersedes_approval_request_id -> public.rental_case_approval_requests`.
- Indexes: `rental_case_approval_requests_pending_idx`.
- Mutability posture: mutable current-state row with `updated_at` touch trigger.

## `public.workflow_actions`

- Purpose: structured operational intent prior to execution.
- Primary key: `id bigint`.
- Important fields: `action_type`, `action_category`, `target_adapter_code`, `reason_entity_type`, `reason_entity_id`, `reason_entity_reference`, `structured_payload`, `approval_posture`, `status`, `semantic_subject_hash`, `source_case_revision`, `idempotency_key`, `due_at`, `supersedes_workflow_action_id`.
- Action status values: `proposed`, `awaiting_approval`, `approved`, `ready_to_execute`, `executing`, `succeeded`, `failed`, `cancelled`, `superseded`.
- Approval posture values: `automatic_allowed`, `approval_required`, `human_only`, `blocked`.
- Action taxonomy: constrained to the frozen Phase 8 action taxonomy set.
- FKs: `rental_case_id -> public.rental_cases`, same-case `supersedes_workflow_action_id -> public.workflow_actions`.
- Uniqueness: action UUID; `(rental_case_id, idempotency_key)`; semantic duplicate protection via active executable posture plus stable idempotency material.
- Indexes: `workflow_actions_pending_execution_idx`, `workflow_actions_failed_idx`.
- Mutability posture: mutable current-state row with `updated_at` touch trigger.

## `public.workflow_execution_attempts`

- Purpose: append-only execution history for workflow actions.
- Primary key: `id bigint`.
- Important fields: `workflow_action_id`, `rental_case_id`, `attempt_number`, `adapter_code`, `started_at`, `completed_at`, `external_reference`, `status`, `failure_code`, `retry_eligible`, `response_snapshot`.
- Status values: `started`, `succeeded`, `failed`, `timeout`, `cancelled`.
- FKs: same-case `(workflow_action_id, rental_case_id) -> public.workflow_actions`.
- Uniqueness: execution UUID; `(workflow_action_id, attempt_number)`.
- Indexes: `workflow_execution_attempts_action_started_at_idx`.
- Mutability posture: append-only; update and delete blocked by trigger.

## `public.rental_case_follow_ups`

- Purpose: due and escalatable follow-up state.
- Primary key: `id bigint`.
- Important fields: `reason_code`, `waiting_for_role`, `waiting_for_reference`, `due_at`, `urgency_level`, `cadence_policy_code`, `attempt_count`, `escalate_after`, `status`, `next_action_type`, `completed_at`.
- Status values: `scheduled`, `due`, `overdue`, `escalated`, `completed`, `cancelled`.
- Urgency values: `low`, `medium`, `high`, `urgent`.
- FKs: `rental_case_id -> public.rental_cases`.
- Indexes: `rental_case_follow_ups_due_idx`.
- Mutability posture: mutable current-state row with `updated_at` touch trigger.

## `public.rental_case_milestones`

- Purpose: workflow deadlines and milestones.
- Primary key: `id bigint`.
- Important fields: `milestone_type`, `target_at`, `status`, `basis_reference`, `related_requirement_id`, `related_workflow_action_id`, `supersedes_milestone_id`, `completed_at`.
- Status values: `scheduled`, `reached`, `completed`, `missed`, `superseded`.
- FKs: `rental_case_id -> public.rental_cases`, same-case `related_requirement_id -> public.rental_case_requirements`, same-case `related_workflow_action_id -> public.workflow_actions`, same-case `supersedes_milestone_id -> public.rental_case_milestones`.
- Indexes: `rental_case_milestones_target_idx`.
- Mutability posture: mutable current-state row with `updated_at` touch trigger.

## `public.rental_case_artifacts`

- Purpose: artifact references plus freshness state.
- Primary key: `id bigint`.
- Important fields: `artifact_type`, `storage_reference`, `external_reference`, `derived_from_case_revision`, `relevant_scope_fingerprint`, `freshness_status`, `last_generated_at`, `last_synced_at`, `supersedes_artifact_id`.
- Artifact types: `proposal`, `agreement`, `internal_event_brief`, `readiness_summary`, `staffing_plan`, `supplier_plan`, `task_surface_projection`, `calendar_projection`.
- Freshness values: `current`, `stale`, `refresh_required`, `superseded`.
- FKs: `rental_case_id -> public.rental_cases`, same-case `supersedes_artifact_id -> public.rental_case_artifacts`.
- Indexes: `rental_case_artifacts_freshness_idx`.
- Mutability posture: mutable current-state row with `updated_at` touch trigger.

## `public.rental_case_reasoning_projections`

- Purpose: minimal Phase 7 reasoning provenance for workflow use without storing full ContextPackages.
- Primary key: `id bigint`.
- Important fields: `reasoning_purpose`, `phase_7_context_contract_version`, `phase_8_workflow_contract_version`, `source_case_revision`, `authority_outcome_classification`, `relevant_current_truth_item_ids`, `relevant_guidance_item_ids`, `relevant_historical_item_ids`, `conflict_codes`, `contamination_codes`, `unresolved_authority_codes`, `warning_codes`, `degraded_retrieval_summary`, `grounding_reference_keys`, `created_at`.
- Authority outcomes: `DETERMINISTIC_CURRENT`, `CURRENT_GUIDANCE`, `HISTORICAL_PRECEDENT`, `MIXED_WITH_CURRENT_PRIORITY`, `REQUIRES_CONFIRMATION`, `INSUFFICIENT_CURRENT_AUTHORITY`.
- Conflict codes: Phase 7 frozen conflict code set `TYPE_A` through `TYPE_G`.
- Contamination codes: Phase 7 frozen contamination code set.
- FKs: `rental_case_id -> public.rental_cases`.
- Indexes: `rental_case_reasoning_projections_case_created_at_idx`.
- Mutability posture: append-only; update and delete blocked by trigger.

## RLS and Privilege Posture

RLS is enabled on every new Phase 8 table.

Direct ordinary-role table privileges are revoked for:

- `anon`
- `authenticated`
- `service_role`

Policy definitions are intentionally deferred to a later runtime-access phase.

## Relationship to the Frozen Domain Model

This schema maps the frozen Phase 8.0B domain model directly:

- `RentalCase` remains the aggregate root
- `RentalCaseFact` supports the frozen `RentalCase` current-scope snapshot without creating a second uncontrolled truth layer
- case truth is normalized across decisions, requirements, blockers, approvals, actions, and artifacts
- inbound source records, observations, and effects preserve extraction-as-evidence before any future truth activation
- lifecycle state is explicit but transition legality is not yet runtime-enforced
- external execution history is separated from intent
- generated prose is not stored as canonical workflow truth
- historical and current reasoning provenance stay references, not copied corpora
