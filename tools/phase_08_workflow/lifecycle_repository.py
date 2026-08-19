from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any, Callable, Protocol

from tools.phase_05_chunking.generate_pilot import run_supabase_query, sql_text

from .contracts import (
    ApprovalRequest,
    ArtifactReference,
    Blocker,
    CaseDecision,
    LifecycleTransition,
    OpenQuestion,
    ProposedCaseChange,
    RentalCase,
    Requirement,
    WorkflowAction,
    WorkflowEvent,
)
from .lifecycle_types import LifecycleTransitionResult


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class LifecycleCaseSnapshot:
    rental_case: RentalCase
    blockers: tuple[Blocker, ...] = ()
    requirements: tuple[Requirement, ...] = ()
    open_questions: tuple[OpenQuestion, ...] = ()
    approval_requests: tuple[ApprovalRequest, ...] = ()
    proposed_changes: tuple[ProposedCaseChange, ...] = ()
    case_decisions: tuple[CaseDecision, ...] = ()
    workflow_actions: tuple[WorkflowAction, ...] = ()
    workflow_events: tuple[WorkflowEvent, ...] = ()
    artifacts: tuple[ArtifactReference, ...] = ()
    lifecycle_transitions: tuple[LifecycleTransition, ...] = ()


class LifecycleRepositoryProtocol(Protocol):
    def load_case_snapshot(self, rental_case_id: int) -> LifecycleCaseSnapshot | None: ...

    def commit_transition(
        self,
        *,
        rental_case_id: int,
        expected_case_revision: int,
        expected_current_state: str,
        target_state: str,
        transition_reason_code: str,
        actor_reference: str,
        actor_type: str | None,
        source_type: str,
        source_reference: str | None,
        triggering_event_id: int | None,
        override_applied: bool,
        transition_event_type_code: str,
        transition_event_payload: dict[str, Any],
        dormant_origin_state: str | None,
        resume_target_state: str | None,
        dormant_reason_code: str | None,
        dormant_review_at: str | None,
    ) -> LifecycleTransitionResult: ...


@dataclass
class InMemoryLifecycleRepository:
    rental_cases: dict[int, RentalCase]
    blockers: dict[int, list[Blocker]]
    requirements: dict[int, list[Requirement]]
    open_questions: dict[int, list[OpenQuestion]]
    approval_requests: dict[int, list[ApprovalRequest]]
    proposed_changes: dict[int, list[ProposedCaseChange]]
    case_decisions: dict[int, list[CaseDecision]]
    workflow_actions: dict[int, list[WorkflowAction]]
    workflow_events: dict[int, list[WorkflowEvent]]
    artifacts: dict[int, list[ArtifactReference]]
    lifecycle_transitions: dict[int, list[LifecycleTransition]]
    _workflow_event_id: int = 10_000
    _lifecycle_transition_id: int = 20_000

    def load_case_snapshot(self, rental_case_id: int) -> LifecycleCaseSnapshot | None:
        rental_case = self.rental_cases.get(rental_case_id)
        if rental_case is None:
            return None
        return LifecycleCaseSnapshot(
            rental_case=rental_case,
            blockers=tuple(self.blockers.get(rental_case_id, ())),
            requirements=tuple(self.requirements.get(rental_case_id, ())),
            open_questions=tuple(self.open_questions.get(rental_case_id, ())),
            approval_requests=tuple(self.approval_requests.get(rental_case_id, ())),
            proposed_changes=tuple(self.proposed_changes.get(rental_case_id, ())),
            case_decisions=tuple(self.case_decisions.get(rental_case_id, ())),
            workflow_actions=tuple(self.workflow_actions.get(rental_case_id, ())),
            workflow_events=tuple(self.workflow_events.get(rental_case_id, ())),
            artifacts=tuple(self.artifacts.get(rental_case_id, ())),
            lifecycle_transitions=tuple(self.lifecycle_transitions.get(rental_case_id, ())),
        )

    def commit_transition(
        self,
        *,
        rental_case_id: int,
        expected_case_revision: int,
        expected_current_state: str,
        target_state: str,
        transition_reason_code: str,
        actor_reference: str,
        actor_type: str | None,
        source_type: str,
        source_reference: str | None,
        triggering_event_id: int | None,
        override_applied: bool,
        transition_event_type_code: str,
        transition_event_payload: dict[str, Any],
        dormant_origin_state: str | None,
        resume_target_state: str | None,
        dormant_reason_code: str | None,
        dormant_review_at: str | None,
    ) -> LifecycleTransitionResult:
        rental_case = self.rental_cases[rental_case_id]
        if rental_case.case_revision != expected_case_revision:
            raise ValueError("stale_case_revision")
        if rental_case.lifecycle_state != expected_current_state:
            raise ValueError("transition_not_allowed")

        occurred_at = current_timestamp()
        previous_revision = rental_case.case_revision
        new_revision = previous_revision + 1
        new_case = replace(
            rental_case,
            lifecycle_state=target_state,
            case_revision=new_revision,
            dormant_origin_state=dormant_origin_state if target_state == "dormant" else None,
            resume_target_state=resume_target_state if target_state == "dormant" else None,
            dormant_reason_code=dormant_reason_code if target_state == "dormant" else None,
            dormant_review_at=dormant_review_at if target_state == "dormant" else None,
            updated_at=occurred_at,
        )
        self.rental_cases[rental_case_id] = new_case

        self._workflow_event_id += 1
        workflow_event_id = self._workflow_event_id
        workflow_event = WorkflowEvent(
            workflow_event_id=workflow_event_id,
            workflow_event_uuid=f"workflow-event-{workflow_event_id}",
            rental_case_id=rental_case_id,
            event_type_code=transition_event_type_code,
            source_type=source_type,
            source_reference=source_reference,
            actor_type=actor_type,
            actor_reference=actor_reference,
            occurred_at=occurred_at,
            recorded_at=occurred_at,
            structured_payload=transition_event_payload,
        )
        self.workflow_events.setdefault(rental_case_id, []).append(workflow_event)

        self._lifecycle_transition_id += 1
        lifecycle_transition_id = self._lifecycle_transition_id
        lifecycle_transition = LifecycleTransition(
            lifecycle_transition_id=lifecycle_transition_id,
            rental_case_id=rental_case_id,
            from_lifecycle_state=expected_current_state,
            to_lifecycle_state=target_state,
            triggering_event_id=triggering_event_id,
            source_type=source_type,
            source_reference=source_reference,
            actor_type=actor_type,
            actor_reference=actor_reference,
            transition_reason_code=transition_reason_code,
            override_applied=override_applied,
            case_revision_before=previous_revision,
            case_revision_after=new_revision,
            occurred_at=occurred_at,
        )
        self.lifecycle_transitions.setdefault(rental_case_id, []).append(lifecycle_transition)

        return LifecycleTransitionResult(
            rental_case_id=rental_case_id,
            previous_state=expected_current_state,
            new_state=target_state,
            previous_revision=previous_revision,
            new_revision=new_revision,
            lifecycle_transition_history_id=lifecycle_transition_id,
            workflow_event_id=workflow_event_id,
            reason_code=transition_reason_code,
            actor_reference=actor_reference,
            actor_type=actor_type,
            source_type=source_type,
            source_reference=source_reference,
            manual_override=override_applied,
            triggering_event_id=triggering_event_id,
            occurred_at=occurred_at,
        )


@dataclass
class SupabaseLifecycleRepository:
    query_runner: Callable[..., Any] = run_supabase_query

    def load_case_snapshot(self, rental_case_id: int) -> LifecycleCaseSnapshot | None:
        rental_case = self._load_rental_case(rental_case_id)
        if rental_case is None:
            return None
        return LifecycleCaseSnapshot(
            rental_case=rental_case,
            blockers=self._load_blockers(rental_case_id),
            requirements=self._load_requirements(rental_case_id),
            open_questions=self._load_open_questions(rental_case_id),
            approval_requests=self._load_approval_requests(rental_case_id),
            proposed_changes=self._load_proposed_changes(rental_case_id),
            case_decisions=self._load_case_decisions(rental_case_id),
            workflow_actions=self._load_workflow_actions(rental_case_id),
            workflow_events=self._load_workflow_events(rental_case_id),
            artifacts=self._load_artifacts(rental_case_id),
            lifecycle_transitions=self._load_lifecycle_transitions(rental_case_id),
        )

    def commit_transition(
        self,
        *,
        rental_case_id: int,
        expected_case_revision: int,
        expected_current_state: str,
        target_state: str,
        transition_reason_code: str,
        actor_reference: str,
        actor_type: str | None,
        source_type: str,
        source_reference: str | None,
        triggering_event_id: int | None,
        override_applied: bool,
        transition_event_type_code: str,
        transition_event_payload: dict[str, Any],
        dormant_origin_state: str | None,
        resume_target_state: str | None,
        dormant_reason_code: str | None,
        dormant_review_at: str | None,
    ) -> LifecycleTransitionResult:
        sql = f"""
select *
from private.commit_rental_case_lifecycle_transition(
  p_rental_case_id => {rental_case_id},
  p_expected_case_revision => {expected_case_revision},
  p_expected_current_state => {sql_text(expected_current_state)},
  p_target_state => {sql_text(target_state)},
  p_transition_reason_code => {sql_text(transition_reason_code)},
  p_source_type => {sql_text(source_type)},
  p_source_reference => {sql_text(source_reference)},
  p_actor_type => {sql_text(actor_type)},
  p_actor_reference => {sql_text(actor_reference)},
  p_triggering_event_id => {_sql_int(triggering_event_id)},
  p_override_applied => {_sql_bool(override_applied)},
  p_transition_event_type_code => {sql_text(transition_event_type_code)},
  p_transition_event_payload => {_sql_json(transition_event_payload)},
  p_dormant_origin_state => {sql_text(dormant_origin_state)},
  p_resume_target_state => {sql_text(resume_target_state)},
  p_dormant_reason_code => {sql_text(dormant_reason_code)},
  p_dormant_review_at => {_sql_timestamptz(dormant_review_at)}
);
""".strip()
        row = self.query_runner(sql, expect_json=True)["rows"][0]
        return LifecycleTransitionResult(
            rental_case_id=row["rental_case_id"],
            previous_state=row["previous_state"],
            new_state=row["new_state"],
            previous_revision=row["previous_revision"],
            new_revision=row["new_revision"],
            lifecycle_transition_history_id=row["lifecycle_transition_history_id"],
            workflow_event_id=row["workflow_event_id"],
            reason_code=row["reason_code"],
            actor_reference=row["actor_reference"],
            actor_type=row["actor_type"],
            source_type=row["source_type"],
            source_reference=row["source_reference"],
            manual_override=row["manual_override"],
            triggering_event_id=row["triggering_event_id"],
            occurred_at=row["occurred_at"],
        )

    def _load_rental_case(self, rental_case_id: int) -> RentalCase | None:
        sql = f"""
select
  id as rental_case_id,
  rental_case_uuid::text as rental_case_uuid,
  case_reference_code,
  lifecycle_state,
  case_revision,
  rental_type_code,
  commercial_summary_status,
  operational_summary_status,
  is_active,
  active_event_start::text as active_event_start,
  active_event_end::text as active_event_end,
  service_level_or_type,
  client_account_ref,
  primary_contact_ref,
  dormant_origin_state,
  resume_target_state,
  dormant_reason_code,
  dormant_review_at::text as dormant_review_at,
  current_proposal_artifact_id,
  current_agreement_artifact_id,
  created_at::text as created_at,
  updated_at::text as updated_at
from public.rental_cases
where id = {rental_case_id};
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        if not rows:
            return None
        return RentalCase(**rows[0])

    def _load_blockers(self, rental_case_id: int) -> tuple[Blocker, ...]:
        sql = f"""
select
  id as blocker_id,
  rental_case_id,
  blocker_type,
  blocked_subject_type,
  origin_entity_type,
  severity,
  status,
  resolution_condition_text,
  opened_at::text as opened_at,
  blocked_subject_id,
  blocked_subject_reference,
  origin_entity_id,
  origin_entity_reference,
  resolution_reference,
  supersedes_blocker_id,
  resolved_at::text as resolved_at
from public.rental_case_blockers
where rental_case_id = {rental_case_id}
order by id;
""".strip()
        return tuple(Blocker(**row) for row in self.query_runner(sql, expect_json=True)["rows"])

    def _load_requirements(self, rental_case_id: int) -> tuple[Requirement, ...]:
        sql = f"""
select
  id as requirement_id,
  rental_case_id,
  requirement_type,
  domain_code,
  applicability_basis,
  status,
  blocking_scope,
  created_at::text as created_at,
  owner_role,
  owner_reference,
  due_at::text as due_at,
  evidence_reference,
  waiver_case_decision_id,
  resolved_at::text as resolved_at
from public.rental_case_requirements
where rental_case_id = {rental_case_id}
order by id;
""".strip()
        return tuple(Requirement(**row) for row in self.query_runner(sql, expect_json=True)["rows"])

    def _load_open_questions(self, rental_case_id: int) -> tuple[OpenQuestion, ...]:
        sql = f"""
select
  id as open_question_id,
  rental_case_id,
  question_type,
  domain_code,
  human_question_text,
  blocking_scope,
  status,
  created_at::text as created_at,
  requested_from_role,
  proposed_answer_payload,
  source_reference,
  supersedes_open_question_id,
  resolved_at::text as resolved_at
from public.rental_case_open_questions
where rental_case_id = {rental_case_id}
order by id;
""".strip()
        return tuple(OpenQuestion(**row) for row in self.query_runner(sql, expect_json=True)["rows"])

    def _load_approval_requests(self, rental_case_id: int) -> tuple[ApprovalRequest, ...]:
        sql = f"""
select
  id as approval_request_id,
  rental_case_id,
  target_entity_type,
  approval_type,
  reason_text,
  status,
  created_at::text as created_at,
  target_entity_id,
  target_entity_reference,
  evidence_reference_keys,
  required_approver_role,
  required_approver_reference,
  decision_payload,
  decided_at::text as decided_at,
  decided_by_reference,
  decision_notes,
  supersedes_approval_request_id,
  updated_at::text as updated_at
from public.rental_case_approval_requests
where rental_case_id = {rental_case_id}
order by id;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        return tuple(
            ApprovalRequest(
                **{
                    **row,
                    "evidence_reference_keys": tuple(row["evidence_reference_keys"] or []),
                }
            )
            for row in rows
        )

    def _load_proposed_changes(self, rental_case_id: int) -> tuple[ProposedCaseChange, ...]:
        sql = f"""
select
  id as proposed_case_change_id,
  rental_case_id,
  change_kind,
  domain_code,
  proposed_value_payload,
  status,
  detected_at::text as detected_at,
  prior_value_payload,
  source_reference,
  impact_classification,
  affected_domain_codes,
  review_posture,
  final_value_payload,
  supersedes_proposed_change_id,
  accepted_at::text as accepted_at,
  created_at::text as created_at,
  updated_at::text as updated_at
from public.rental_case_proposed_changes
where rental_case_id = {rental_case_id}
order by id;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        return tuple(
            ProposedCaseChange(
                **{
                    **row,
                    "affected_domain_codes": tuple(row["affected_domain_codes"] or []),
                }
            )
            for row in rows
        )

    def _load_case_decisions(self, rental_case_id: int) -> tuple[CaseDecision, ...]:
        sql = f"""
select
  id as case_decision_id,
  rental_case_id,
  decision_type,
  domain_code,
  baseline_reference,
  proposed_value_payload,
  scope_key,
  scope_description,
  authority_basis,
  approval_posture,
  status,
  created_at::text as created_at,
  effective_value_payload,
  evidence_reference,
  approval_request_id,
  effective_at::text as effective_at,
  supersedes_case_decision_id,
  updated_at::text as updated_at
from public.rental_case_decisions
where rental_case_id = {rental_case_id}
order by id;
""".strip()
        return tuple(CaseDecision(**row) for row in self.query_runner(sql, expect_json=True)["rows"])

    def _load_workflow_actions(self, rental_case_id: int) -> tuple[WorkflowAction, ...]:
        sql = f"""
select
  id as workflow_action_id,
  workflow_action_uuid::text as workflow_action_uuid,
  rental_case_id,
  action_type,
  action_category,
  target_adapter_code,
  reason_entity_type,
  approval_posture,
  status,
  semantic_subject_hash,
  source_case_revision,
  idempotency_key,
  structured_payload,
  reason_entity_id,
  reason_entity_reference,
  target_scope_key,
  due_at::text as due_at,
  supersedes_workflow_action_id,
  created_at::text as created_at,
  updated_at::text as updated_at
from public.workflow_actions
where rental_case_id = {rental_case_id}
order by id;
""".strip()
        return tuple(WorkflowAction(**row) for row in self.query_runner(sql, expect_json=True)["rows"])

    def _load_workflow_events(self, rental_case_id: int) -> tuple[WorkflowEvent, ...]:
        sql = f"""
select
  id as workflow_event_id,
  workflow_event_uuid::text as workflow_event_uuid,
  rental_case_id,
  event_type_code,
  source_type,
  occurred_at::text as occurred_at,
  recorded_at::text as recorded_at,
  structured_payload,
  source_reference,
  actor_type,
  actor_reference,
  event_identity_key,
  origin_metadata
from public.workflow_events
where rental_case_id = {rental_case_id}
order by id;
""".strip()
        return tuple(WorkflowEvent(**row) for row in self.query_runner(sql, expect_json=True)["rows"])

    def _load_artifacts(self, rental_case_id: int) -> tuple[ArtifactReference, ...]:
        sql = f"""
select
  id as artifact_reference_id,
  rental_case_id,
  artifact_type,
  derived_from_case_revision,
  freshness_status,
  storage_reference,
  external_reference,
  relevant_scope_fingerprint,
  last_generated_at::text as last_generated_at,
  last_synced_at::text as last_synced_at,
  supersedes_artifact_id,
  created_at::text as created_at,
  updated_at::text as updated_at
from public.rental_case_artifacts
where rental_case_id = {rental_case_id}
order by id;
""".strip()
        return tuple(ArtifactReference(**row) for row in self.query_runner(sql, expect_json=True)["rows"])

    def _load_lifecycle_transitions(self, rental_case_id: int) -> tuple[LifecycleTransition, ...]:
        sql = f"""
select
  id as lifecycle_transition_id,
  rental_case_id,
  to_lifecycle_state,
  transition_reason_code,
  case_revision_before,
  case_revision_after,
  occurred_at::text as occurred_at,
  from_lifecycle_state,
  triggering_event_id,
  source_type,
  source_reference,
  actor_type,
  actor_reference,
  override_applied
from public.rental_case_lifecycle_transitions
where rental_case_id = {rental_case_id}
order by id;
""".strip()
        return tuple(LifecycleTransition(**row) for row in self.query_runner(sql, expect_json=True)["rows"])


def _sql_bool(value: bool) -> str:
    return "true" if value else "false"


def _sql_int(value: int | None) -> str:
    return "null" if value is None else str(value)


def _sql_json(value: dict[str, Any] | None) -> str:
    if value is None:
        return "null::jsonb"
    return f"{sql_text(json.dumps(value, sort_keys=True, ensure_ascii=True))}::jsonb"


def _sql_timestamptz(value: str | None) -> str:
    if value is None:
        return "null::timestamptz"
    return f"{sql_text(value)}::timestamptz"

