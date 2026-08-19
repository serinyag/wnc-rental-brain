from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from tools.phase_05_chunking.generate_pilot import run_supabase_query

from .contracts import CaseDecision, OpenQuestion, ProposedCaseChange, RentalCase, Requirement, RescheduleRequest, WorkflowEvent
from .inquiry_intake import (
    ACTIVE_CHANGE_STATUSES,
    ACTIVE_RESCHEDULE_STATUSES,
    CORE_INQUIRY_FIELD_RULES,
    INQUIRY_FIELD_EVENT_TYPE,
    INQUIRY_FIELD_GUEST_COUNT,
    INQUIRY_FIELD_REQUESTED_SCHEDULE,
    INQUIRY_FIELD_REQUESTED_SPACE,
    INQUIRY_INTAKE_EFFECT_CREATE_OPEN_QUESTION,
    INQUIRY_INTAKE_EFFECT_CREATE_PROPOSED_CHANGE,
    INQUIRY_INTAKE_EFFECT_CREATE_RESCHEDULE_REQUEST,
    INQUIRY_INTAKE_EFFECT_PROMOTE_CURRENT_VALUE,
    INQUIRY_INTAKE_EFFECT_RESOLVE_OPEN_QUESTION,
    InquiryIntakeCommitResult,
    InquiryIntakePlan,
)
from .lifecycle_repository import _sql_json, _sql_timestamptz, current_timestamp, sql_text
from .observation_contracts import InboundObservation, InboundObservationEffect, InboundSourceRecord, RentalCaseFact
from .observation_repository import ObservationCaseSnapshot, ObservationRepositoryProtocol
from .observation_types import CaseAssociationResult, InboundSourceRecordInput
from .orchestration_repository import SupabaseWorkflowOrchestrationRepository, _proposed_change_from_row
from .validation import Phase8ContractError


def _normalize_text_tuple(value: list[str] | tuple[str, ...] | None) -> tuple[str, ...]:
    return tuple(value or [])


def _sql_text_array(values: tuple[str, ...]) -> str:
    if not values:
        return "'{}'::text[]"
    return "array[" + ", ".join(sql_text(value) for value in values) + "]"


def _source_record_from_row(row: dict[str, Any]) -> InboundSourceRecord:
    return InboundSourceRecord(**row)


def _observation_from_row(row: dict[str, Any]) -> InboundObservation:
    return InboundObservation(
        **{
            **row,
            "ambiguity_flags": _normalize_text_tuple(row.get("ambiguity_flags")),
        }
    )


def _effect_from_row(row: dict[str, Any]) -> InboundObservationEffect:
    return InboundObservationEffect(
        **{
            **row,
            "reason_codes": _normalize_text_tuple(row.get("reason_codes")),
        }
    )


@dataclass
class SupabaseObservationRepository(SupabaseWorkflowOrchestrationRepository, ObservationRepositoryProtocol):
    query_runner: Callable[..., Any] = run_supabase_query

    def load_case_snapshot(self, rental_case_id: int) -> ObservationCaseSnapshot | None:
        snapshot = self.load_case_core_snapshot_for_console(
            rental_case_id,
            include_workflow_events=True,
        )
        if snapshot is None:
            return None
        return ObservationCaseSnapshot(
            rental_case=snapshot.rental_case,
            rental_case_facts=snapshot.rental_case_facts,
            open_questions=snapshot.open_questions,
            requirements=snapshot.requirements,
            proposed_changes=snapshot.proposed_changes,
            case_decisions=snapshot.case_decisions,
            reschedule_requests=snapshot.reschedule_requests,
            workflow_events=snapshot.workflow_events,
        )

    def get_case_by_reference(self, case_reference_code: str) -> RentalCase | None:
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
where case_reference_code = {sql_text(case_reference_code)}
limit 1;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        return None if not rows else RentalCase(**rows[0])

    def get_source_by_dedupe(self, *, source_system_code: str, dedupe_key: str) -> InboundSourceRecord | None:
        sql = f"""
select
  id as inbound_source_record_id,
  source_system_code,
  source_record_type,
  dedupe_key,
  source_hash,
  occurred_at::text as occurred_at,
  association_status,
  created_at::text as created_at,
  external_source_id,
  conversation_reference,
  sender_actor_type,
  sender_actor_reference,
  case_reference_hint,
  resolved_rental_case_id,
  association_basis,
  received_at::text as received_at,
  source_location_reference,
  confidentiality_posture,
  pi_posture,
  evidence_excerpt
from public.inbound_source_records
where source_system_code = {sql_text(source_system_code)}
  and dedupe_key = {sql_text(dedupe_key)}
limit 1;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        return None if not rows else _source_record_from_row(rows[0])

    def list_source_records_for_case(self, rental_case_id: int) -> tuple[InboundSourceRecord, ...]:
        sql = f"""
select
  id as inbound_source_record_id,
  source_system_code,
  source_record_type,
  dedupe_key,
  source_hash,
  occurred_at::text as occurred_at,
  association_status,
  created_at::text as created_at,
  external_source_id,
  conversation_reference,
  sender_actor_type,
  sender_actor_reference,
  case_reference_hint,
  resolved_rental_case_id,
  association_basis,
  received_at::text as received_at,
  source_location_reference,
  confidentiality_posture,
  pi_posture,
  evidence_excerpt
from public.inbound_source_records
where resolved_rental_case_id = {rental_case_id}
order by occurred_at desc, id desc;
""".strip()
        return tuple(_source_record_from_row(row) for row in self.query_runner(sql, expect_json=True)["rows"])

    def list_observations_for_case(self, rental_case_id: int) -> tuple[InboundObservation, ...]:
        sql = f"""
select
  id as inbound_observation_id,
  inbound_source_record_id,
  reported_field_code,
  reported_domain_code,
  target_field_code,
  target_domain_code,
  rental_case_id,
  observation_type,
  claim_kind,
  candidate_value_payload,
  source_evidence_reference,
  status,
  observation_identity_key,
  asserted_by_party_type,
  asserted_by_reference,
  source_excerpt,
  observed_against_case_revision,
  extraction_confidence,
  ambiguity_flags,
  supersedes_inbound_observation_id,
  created_at::text as created_at,
  updated_at::text as updated_at
from public.inbound_observations
where rental_case_id = {rental_case_id}
order by inbound_source_record_id, id;
""".strip()
        return tuple(_observation_from_row(row) for row in self.query_runner(sql, expect_json=True)["rows"])

    def list_effects_for_case(self, rental_case_id: int) -> tuple[InboundObservationEffect, ...]:
        sql = f"""
select
  ioe.id as inbound_observation_effect_id,
  ioe.inbound_observation_id,
  ioe.rental_case_id,
  ioe.disposition_code,
  ioe.revalidation_required,
  ioe.stale_observation,
  ioe.reason_codes,
  ioe.linked_open_question_id,
  ioe.linked_requirement_id,
  ioe.linked_proposed_change_id,
  ioe.linked_case_decision_id,
  ioe.linked_reschedule_request_id,
  ioe.workflow_event_id,
  ioe.created_at::text as created_at
from public.inbound_observation_effects ioe
join public.inbound_observations io
  on io.id = ioe.inbound_observation_id
where io.rental_case_id = {rental_case_id}
order by ioe.inbound_observation_id;
""".strip()
        return tuple(_effect_from_row(row) for row in self.query_runner(sql, expect_json=True)["rows"])

    def get_observation_by_identity(
        self,
        *,
        inbound_source_record_id: int,
        observation_identity_key: str,
    ) -> InboundObservation | None:
        sql = f"""
select
  id as inbound_observation_id,
  inbound_source_record_id,
  reported_field_code,
  reported_domain_code,
  target_field_code,
  target_domain_code,
  rental_case_id,
  observation_type,
  claim_kind,
  candidate_value_payload,
  source_evidence_reference,
  status,
  observation_identity_key,
  asserted_by_party_type,
  asserted_by_reference,
  source_excerpt,
  observed_against_case_revision,
  extraction_confidence,
  ambiguity_flags,
  supersedes_inbound_observation_id,
  created_at::text as created_at,
  updated_at::text as updated_at
from public.inbound_observations
where inbound_source_record_id = {inbound_source_record_id}
  and observation_identity_key = {sql_text(observation_identity_key)}
limit 1;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        return None if not rows else _observation_from_row(rows[0])

    def list_observations_for_source(self, inbound_source_record_id: int) -> tuple[InboundObservation, ...]:
        sql = f"""
select
  id as inbound_observation_id,
  inbound_source_record_id,
  reported_field_code,
  reported_domain_code,
  target_field_code,
  target_domain_code,
  rental_case_id,
  observation_type,
  claim_kind,
  candidate_value_payload,
  source_evidence_reference,
  status,
  observation_identity_key,
  asserted_by_party_type,
  asserted_by_reference,
  source_excerpt,
  observed_against_case_revision,
  extraction_confidence,
  ambiguity_flags,
  supersedes_inbound_observation_id,
  created_at::text as created_at,
  updated_at::text as updated_at
from public.inbound_observations
where inbound_source_record_id = {inbound_source_record_id}
order by id;
""".strip()
        return tuple(_observation_from_row(row) for row in self.query_runner(sql, expect_json=True)["rows"])

    def get_effect_for_observation(self, inbound_observation_id: int) -> InboundObservationEffect | None:
        sql = f"""
select
  id as inbound_observation_effect_id,
  inbound_observation_id,
  rental_case_id,
  disposition_code,
  revalidation_required,
  stale_observation,
  reason_codes,
  linked_open_question_id,
  linked_requirement_id,
  linked_proposed_change_id,
  linked_case_decision_id,
  linked_reschedule_request_id,
  workflow_event_id,
  created_at::text as created_at
from public.inbound_observation_effects
where inbound_observation_id = {inbound_observation_id}
limit 1;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        return None if not rows else _effect_from_row(rows[0])

    def get_failure_codes_for_observation(self, inbound_observation_id: int) -> tuple[str, ...]:
        sql = f"""
select
  coalesce(
    array(
      select jsonb_array_elements_text(coalesce(we.structured_payload -> 'failure_codes', '[]'::jsonb))
    ),
    '{{}}'::text[]
  ) as failure_codes
from public.inbound_observation_effects ioe
left join public.workflow_events we
  on we.id = ioe.workflow_event_id
 and we.rental_case_id = ioe.rental_case_id
where ioe.inbound_observation_id = {inbound_observation_id}
limit 1;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        if not rows:
            return ()
        return _normalize_text_tuple(rows[0].get("failure_codes"))

    def create_source_record(
        self,
        *,
        source_record_input: InboundSourceRecordInput,
        case_association: CaseAssociationResult,
        created_at: str,
    ) -> InboundSourceRecord:
        sql = f"""
insert into public.inbound_source_records (
  source_system_code,
  source_record_type,
  dedupe_key,
  source_hash,
  external_source_id,
  conversation_reference,
  sender_actor_type,
  sender_actor_reference,
  case_reference_hint,
  resolved_rental_case_id,
  association_status,
  association_basis,
  occurred_at,
  received_at,
  source_location_reference,
  confidentiality_posture,
  pi_posture,
  evidence_excerpt,
  created_at
)
values (
  {sql_text(source_record_input.source_system_code)},
  {sql_text(source_record_input.source_record_type)},
  {sql_text(source_record_input.dedupe_key)},
  {sql_text(source_record_input.source_hash)},
  {sql_text(source_record_input.external_source_id)},
  {sql_text(source_record_input.conversation_reference)},
  {sql_text(source_record_input.sender_actor_type)},
  {sql_text(source_record_input.sender_actor_reference)},
  {sql_text(source_record_input.case_reference_hint or case_association.case_reference_code)},
  {case_association.rental_case_id if case_association.rental_case_id is not None else 'null'},
  {sql_text(case_association.status)},
  {sql_text(case_association.association_basis)},
  {_sql_timestamptz(source_record_input.occurred_at)},
  {_sql_timestamptz(source_record_input.received_at)},
  {sql_text(source_record_input.source_location_reference)},
  {sql_text(source_record_input.confidentiality_posture)},
  {sql_text(source_record_input.pi_posture)},
  {sql_text(source_record_input.evidence_excerpt)},
  {_sql_timestamptz(created_at)}
)
on conflict (source_system_code, dedupe_key) do nothing
returning
  id as inbound_source_record_id,
  source_system_code,
  source_record_type,
  dedupe_key,
  source_hash,
  occurred_at::text as occurred_at,
  association_status,
  created_at::text as created_at,
  external_source_id,
  conversation_reference,
  sender_actor_type,
  sender_actor_reference,
  case_reference_hint,
  resolved_rental_case_id,
  association_basis,
  received_at::text as received_at,
  source_location_reference,
  confidentiality_posture,
  pi_posture,
  evidence_excerpt;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        if rows:
            return _source_record_from_row(rows[0])
        existing = self.get_source_by_dedupe(
            source_system_code=source_record_input.source_system_code,
            dedupe_key=source_record_input.dedupe_key,
        )
        if existing is None:
            raise Phase8ContractError(
                error_category="mutation_failed",
                safe_message="The inbound source record could not be created or reloaded.",
            )
        return existing

    def create_observation(
        self,
        *,
        inbound_source_record_id: int,
        rental_case_id: int | None,
        reported_field_code: str,
        reported_domain_code: str | None,
        target_field_code: str | None,
        target_domain_code: str | None,
        observation_type: str,
        claim_kind: str,
        candidate_value_payload: Any,
        source_evidence_reference: str,
        status: str,
        observation_identity_key: str,
        asserted_by_party_type: str | None,
        asserted_by_reference: str | None,
        source_excerpt: str | None,
        observed_against_case_revision: int | None,
        extraction_confidence: float | None,
        ambiguity_flags: tuple[str, ...],
        created_at: str,
    ) -> InboundObservation:
        sql = f"""
insert into public.inbound_observations (
  inbound_source_record_id,
  rental_case_id,
  reported_field_code,
  reported_domain_code,
  target_field_code,
  target_domain_code,
  observation_type,
  claim_kind,
  candidate_value_payload,
  source_evidence_reference,
  status,
  observation_identity_key,
  asserted_by_party_type,
  asserted_by_reference,
  source_excerpt,
  observed_against_case_revision,
  extraction_confidence,
  ambiguity_flags,
  created_at,
  updated_at
)
values (
  {inbound_source_record_id},
  {rental_case_id if rental_case_id is not None else 'null'},
  {sql_text(reported_field_code)},
  {sql_text(reported_domain_code)},
  {sql_text(target_field_code)},
  {sql_text(target_domain_code)},
  {sql_text(observation_type)},
  {sql_text(claim_kind)},
  {_sql_json(candidate_value_payload)},
  {sql_text(source_evidence_reference)},
  {sql_text(status)},
  {sql_text(observation_identity_key)},
  {sql_text(asserted_by_party_type)},
  {sql_text(asserted_by_reference)},
  {sql_text(source_excerpt)},
  {observed_against_case_revision if observed_against_case_revision is not None else 'null'},
  {extraction_confidence if extraction_confidence is not None else 'null'},
  {_sql_text_array(ambiguity_flags)},
  {_sql_timestamptz(created_at)},
  {_sql_timestamptz(created_at)}
)
on conflict (inbound_source_record_id, observation_identity_key) do nothing
returning
  id as inbound_observation_id,
  inbound_source_record_id,
  reported_field_code,
  reported_domain_code,
  target_field_code,
  target_domain_code,
  rental_case_id,
  observation_type,
  claim_kind,
  candidate_value_payload,
  source_evidence_reference,
  status,
  observation_identity_key,
  asserted_by_party_type,
  asserted_by_reference,
  source_excerpt,
  observed_against_case_revision,
  extraction_confidence,
  ambiguity_flags,
  supersedes_inbound_observation_id,
  created_at::text as created_at,
  updated_at::text as updated_at;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        if rows:
            return _observation_from_row(rows[0])
        existing = self.get_observation_by_identity(
            inbound_source_record_id=inbound_source_record_id,
            observation_identity_key=observation_identity_key,
        )
        if existing is None:
            raise Phase8ContractError(
                error_category="mutation_failed",
                safe_message="The inbound observation could not be created or reloaded.",
            )
        return existing

    def create_workflow_event(
        self,
        *,
        rental_case_id: int,
        event_type_code: str = "inbound_observation_recorded",
        source_type: str,
        source_reference: str,
        actor_type: str | None,
        actor_reference: str | None,
        occurred_at: str,
        structured_payload: dict[str, Any],
        event_identity_key: str,
    ) -> WorkflowEvent:
        sql = f"""
insert into public.workflow_events (
  rental_case_id,
  event_type_code,
  source_type,
  source_reference,
  actor_type,
  actor_reference,
  occurred_at,
  recorded_at,
  structured_payload,
  event_identity_key,
  origin_metadata
)
values (
  {rental_case_id},
  {sql_text(event_type_code)},
  {sql_text(source_type)},
  {sql_text(source_reference)},
  {sql_text(actor_type)},
  {sql_text(actor_reference)},
  {_sql_timestamptz(occurred_at)},
  {_sql_timestamptz(occurred_at)},
  {_sql_json(structured_payload)},
  {sql_text(event_identity_key)},
  {_sql_json({"phase": "8.3"})}
)
on conflict (rental_case_id, event_identity_key) do nothing
returning
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
  origin_metadata;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        if rows:
            return WorkflowEvent(**rows[0])
        select_sql = f"""
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
  and event_identity_key = {sql_text(event_identity_key)}
limit 1;
""".strip()
        select_rows = self.query_runner(select_sql, expect_json=True)["rows"]
        if not select_rows:
            raise Phase8ContractError(
                error_category="mutation_failed",
                safe_message="The workflow event could not be created or reloaded.",
            )
        return WorkflowEvent(**select_rows[0])

    def commit_inquiry_intake_plan(
        self,
        plan: InquiryIntakePlan,
        *,
        actor_reference: str,
        actor_type: str | None,
        applied_at: str,
    ) -> InquiryIntakeCommitResult:
        snapshot = self.load_case_snapshot(plan.rental_case_id)
        if snapshot is None:
            return InquiryIntakeCommitResult(
                rental_case_id=plan.rental_case_id,
                case_revision_before=0,
                case_revision_after=0,
                plan=plan,
                applied_effects=(),
                failure_codes=("case_not_found",),
            )
        if snapshot.rental_case.case_revision != plan.evaluated_case_revision:
            return InquiryIntakeCommitResult(
                rental_case_id=plan.rental_case_id,
                case_revision_before=snapshot.rental_case.case_revision,
                case_revision_after=snapshot.rental_case.case_revision,
                plan=plan,
                applied_effects=(),
                failure_codes=("stale_case_revision",),
            )
        if not plan.effects:
            return InquiryIntakeCommitResult(
                rental_case_id=plan.rental_case_id,
                case_revision_before=snapshot.rental_case.case_revision,
                case_revision_after=snapshot.rental_case.case_revision,
                plan=plan,
                applied_effects=(),
            )

        promoted_schedule = next(
            (
                effect
                for effect in plan.effects
                if effect.effect_code == INQUIRY_INTAKE_EFFECT_PROMOTE_CURRENT_VALUE
                and effect.inquiry_field_code == INQUIRY_FIELD_REQUESTED_SCHEDULE
            ),
            None,
        )
        promoted_scope = next(
            (
                effect
                for effect in plan.effects
                if effect.effect_code == INQUIRY_INTAKE_EFFECT_PROMOTE_CURRENT_VALUE
                and effect.inquiry_field_code == INQUIRY_FIELD_REQUESTED_SPACE
            ),
            None,
        )
        next_revision = plan.evaluated_case_revision + 1
        schedule_start = (
            promoted_schedule.proposed_value.get("active_event_start")
            if promoted_schedule is not None and isinstance(promoted_schedule.proposed_value, dict)
            else snapshot.rental_case.active_event_start
        )
        schedule_end = (
            promoted_schedule.proposed_value.get("active_event_end")
            if promoted_schedule is not None and isinstance(promoted_schedule.proposed_value, dict)
            else snapshot.rental_case.active_event_end
        )
        rental_type_code = (
            str(promoted_scope.proposed_value)
            if promoted_scope is not None and isinstance(promoted_scope.proposed_value, str)
            else snapshot.rental_case.rental_type_code
        )

        fact_sql = "\n".join(
            self._render_inquiry_fact_sql(effect=effect, rental_case_id=plan.rental_case_id, applied_at=applied_at)
            for effect in plan.effects
            if effect.effect_code == INQUIRY_INTAKE_EFFECT_PROMOTE_CURRENT_VALUE
            and effect.inquiry_field_code in {INQUIRY_FIELD_GUEST_COUNT, INQUIRY_FIELD_EVENT_TYPE}
        )
        question_create_sql = "\n".join(
            self._render_inquiry_open_question_create_sql(
                effect=effect,
                rental_case_id=plan.rental_case_id,
                applied_at=applied_at,
            )
            for effect in plan.effects
            if effect.effect_code == INQUIRY_INTAKE_EFFECT_CREATE_OPEN_QUESTION
        )
        question_resolve_sql = "\n".join(
            self._render_inquiry_open_question_resolve_sql(
                effect=effect,
                rental_case_id=plan.rental_case_id,
                applied_at=applied_at,
            )
            for effect in plan.effects
            if effect.effect_code == INQUIRY_INTAKE_EFFECT_RESOLVE_OPEN_QUESTION and effect.open_question_id is not None
        )
        change_sql = "\n".join(
            self._render_inquiry_change_sql(
                effect=effect,
                rental_case_id=plan.rental_case_id,
                applied_at=applied_at,
            )
            for effect in plan.effects
            if effect.effect_code == INQUIRY_INTAKE_EFFECT_CREATE_PROPOSED_CHANGE
        )
        reschedule_sql = "\n".join(
            self._render_inquiry_reschedule_sql(
                effect=effect,
                rental_case_id=plan.rental_case_id,
                applied_at=applied_at,
            )
            for effect in plan.effects
            if effect.effect_code == INQUIRY_INTAKE_EFFECT_CREATE_RESCHEDULE_REQUEST
        )
        event_sql = "\n".join(
            self._render_inquiry_event_sql(
                effect=effect,
                rental_case_id=plan.rental_case_id,
                actor_reference=actor_reference,
                actor_type=actor_type,
                applied_at=applied_at,
                case_revision=next_revision,
            )
            for effect in plan.effects
        )
        sql = f"""
do $$
begin
  update public.rental_cases
  set case_revision = case_revision + 1,
      active_event_start = {_sql_timestamptz(schedule_start)},
      active_event_end = {_sql_timestamptz(schedule_end)},
      rental_type_code = {sql_text(rental_type_code)},
      updated_at = {_sql_timestamptz(applied_at)}
  where id = {plan.rental_case_id}
    and case_revision = {plan.evaluated_case_revision};
  if not found then
    return;
  end if;
  {fact_sql}
  {question_create_sql}
  {question_resolve_sql}
  {change_sql}
  {reschedule_sql}
  {event_sql}
end $$;
""".strip()
        self.query_runner(sql, expect_json=False)

        post_snapshot = self.load_case_snapshot(plan.rental_case_id)
        if post_snapshot is None:
            return InquiryIntakeCommitResult(
                rental_case_id=plan.rental_case_id,
                case_revision_before=snapshot.rental_case.case_revision,
                case_revision_after=snapshot.rental_case.case_revision,
                plan=plan,
                applied_effects=(),
                failure_codes=("case_not_found",),
            )
        if post_snapshot.rental_case.case_revision == snapshot.rental_case.case_revision:
            return InquiryIntakeCommitResult(
                rental_case_id=plan.rental_case_id,
                case_revision_before=snapshot.rental_case.case_revision,
                case_revision_after=post_snapshot.rental_case.case_revision,
                plan=plan,
                applied_effects=(),
                failure_codes=("stale_case_revision",),
            )
        return InquiryIntakeCommitResult(
            rental_case_id=plan.rental_case_id,
            case_revision_before=snapshot.rental_case.case_revision,
            case_revision_after=post_snapshot.rental_case.case_revision,
            plan=plan,
            applied_effects=plan.effects,
            created_open_question_ids=tuple(self._lookup_open_question_ids(post_snapshot, plan)),
            resolved_open_question_ids=tuple(self._lookup_resolved_question_ids(plan)),
            created_proposed_change_ids=tuple(self._lookup_proposed_change_ids(post_snapshot, plan)),
            created_reschedule_request_ids=tuple(self._lookup_reschedule_ids(post_snapshot, plan)),
        )

    def update_open_question_answer_candidate(
        self,
        *,
        rental_case_id: int,
        open_question_id: int,
        proposed_answer_payload: Any,
        source_reference: str,
    ) -> OpenQuestion:
        sql = f"""
update public.rental_case_open_questions
set status = 'answered_pending_validation',
    proposed_answer_payload = {_sql_json(proposed_answer_payload)},
    source_reference = {sql_text(source_reference)},
    resolved_at = null
where id = {open_question_id}
  and rental_case_id = {rental_case_id}
returning
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
  resolved_at::text as resolved_at;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        if rows:
            return OpenQuestion(**rows[0])
        self._raise_missing_or_cross_case(
            table_name="public.rental_case_open_questions",
            entity_id_field="id",
            entity_id=open_question_id,
            expected_case_id=rental_case_id,
        )
        raise AssertionError("unreachable")

    def attach_requirement_evidence(
        self,
        *,
        rental_case_id: int,
        requirement_id: int,
        evidence_reference: str,
    ) -> Requirement:
        sql = f"""
update public.rental_case_requirements
set evidence_reference = {sql_text(evidence_reference)},
    status = case when status = 'required' then 'in_progress' else status end
where id = {requirement_id}
  and rental_case_id = {rental_case_id}
returning
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
  resolved_at::text as resolved_at;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        if rows:
            return Requirement(**rows[0])
        self._raise_missing_or_cross_case(
            table_name="public.rental_case_requirements",
            entity_id_field="id",
            entity_id=requirement_id,
            expected_case_id=rental_case_id,
        )
        raise AssertionError("unreachable")

    def create_proposed_change(
        self,
        *,
        rental_case_id: int,
        change_kind: str,
        domain_code: str,
        prior_value_payload: Any,
        proposed_value_payload: Any,
        source_reference: str,
        detected_at: str,
        impact_classification: str | None,
        affected_domain_codes: tuple[str, ...],
        review_posture: str | None,
    ) -> ProposedCaseChange:
        sql = f"""
insert into public.rental_case_proposed_changes (
  rental_case_id,
  change_kind,
  domain_code,
  prior_value_payload,
  proposed_value_payload,
  source_reference,
  impact_classification,
  affected_domain_codes,
  review_posture,
  status,
  detected_at,
  created_at,
  updated_at
)
values (
  {rental_case_id},
  {sql_text(change_kind)},
  {sql_text(domain_code)},
  {_sql_json(prior_value_payload)},
  {_sql_json(proposed_value_payload)},
  {sql_text(source_reference)},
  {sql_text(impact_classification)},
  {_sql_text_array(affected_domain_codes)},
  {sql_text(review_posture)},
  'proposed',
  {_sql_timestamptz(detected_at)},
  {_sql_timestamptz(detected_at)},
  {_sql_timestamptz(detected_at)}
)
returning
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
  updated_at::text as updated_at;
""".strip()
        return _proposed_change_from_row(self.query_runner(sql, expect_json=True)["rows"][0])

    def create_case_decision_candidate(
        self,
        *,
        rental_case_id: int,
        decision_type: str,
        domain_code: str,
        baseline_reference: str,
        proposed_value_payload: Any,
        scope_key: str,
        scope_description: str,
        authority_basis: str,
        approval_posture: str,
        evidence_reference: str,
        created_at: str,
    ) -> CaseDecision:
        sql = f"""
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
  status,
  created_at,
  evidence_reference,
  updated_at
)
values (
  {rental_case_id},
  {sql_text(decision_type)},
  {sql_text(domain_code)},
  {sql_text(baseline_reference)},
  {_sql_json(proposed_value_payload)},
  {sql_text(scope_key)},
  {sql_text(scope_description)},
  {sql_text(authority_basis)},
  {sql_text(approval_posture)},
  'proposed',
  {_sql_timestamptz(created_at)},
  {sql_text(evidence_reference)},
  {_sql_timestamptz(created_at)}
)
returning
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
  updated_at::text as updated_at;
""".strip()
        return CaseDecision(**self.query_runner(sql, expect_json=True)["rows"][0])

    def create_reschedule_request(
        self,
        *,
        rental_case_id: int,
        current_active_date_snapshot: dict[str, Any],
        requested_date_payload: dict[str, Any],
        consequence_summary_payload: dict[str, Any],
        urgency_class: str,
        created_at: str,
    ) -> RescheduleRequest:
        sql = f"""
insert into public.rental_case_reschedule_requests (
  rental_case_id,
  current_active_date_snapshot,
  requested_date_payload,
  candidate_dates_payload,
  consequence_summary_payload,
  status,
  urgency_class,
  created_at,
  updated_at
)
values (
  {rental_case_id},
  {_sql_json(current_active_date_snapshot)},
  {_sql_json(requested_date_payload)},
  '[]'::jsonb,
  {_sql_json(consequence_summary_payload)},
  'proposed',
  {sql_text(urgency_class)},
  {_sql_timestamptz(created_at)},
  {_sql_timestamptz(created_at)}
)
returning
  id as reschedule_request_id,
  rental_case_id,
  current_active_date_snapshot,
  requested_date_payload,
  candidate_dates_payload,
  consequence_summary_payload,
  status,
  urgency_class,
  created_at::text as created_at,
  confirmed_proposed_change_id,
  confirmed_at::text as confirmed_at,
  updated_at::text as updated_at;
""".strip()
        row = self.query_runner(sql, expect_json=True)["rows"][0]
        return RescheduleRequest(**{**row, "candidate_dates_payload": tuple(row["candidate_dates_payload"] or [])})

    def create_effect(
        self,
        *,
        inbound_observation_id: int,
        rental_case_id: int | None,
        disposition_code: str,
        revalidation_required: bool,
        stale_observation: bool,
        reason_codes: tuple[str, ...],
        failure_codes: tuple[str, ...],
        created_at: str,
        linked_open_question_id: int | None = None,
        linked_requirement_id: int | None = None,
        linked_proposed_change_id: int | None = None,
        linked_case_decision_id: int | None = None,
        linked_reschedule_request_id: int | None = None,
        workflow_event_id: int | None = None,
    ) -> InboundObservationEffect:
        del failure_codes
        sql = f"""
insert into public.inbound_observation_effects (
  inbound_observation_id,
  rental_case_id,
  disposition_code,
  revalidation_required,
  stale_observation,
  reason_codes,
  linked_open_question_id,
  linked_requirement_id,
  linked_proposed_change_id,
  linked_case_decision_id,
  linked_reschedule_request_id,
  workflow_event_id,
  created_at
)
values (
  {inbound_observation_id},
  {rental_case_id if rental_case_id is not None else 'null'},
  {sql_text(disposition_code)},
  {'true' if revalidation_required else 'false'},
  {'true' if stale_observation else 'false'},
  {_sql_text_array(reason_codes)},
  {linked_open_question_id if linked_open_question_id is not None else 'null'},
  {linked_requirement_id if linked_requirement_id is not None else 'null'},
  {linked_proposed_change_id if linked_proposed_change_id is not None else 'null'},
  {linked_case_decision_id if linked_case_decision_id is not None else 'null'},
  {linked_reschedule_request_id if linked_reschedule_request_id is not None else 'null'},
  {workflow_event_id if workflow_event_id is not None else 'null'},
  {_sql_timestamptz(created_at)}
)
on conflict (inbound_observation_id) do nothing
returning
  id as inbound_observation_effect_id,
  inbound_observation_id,
  rental_case_id,
  disposition_code,
  revalidation_required,
  stale_observation,
  reason_codes,
  linked_open_question_id,
  linked_requirement_id,
  linked_proposed_change_id,
  linked_case_decision_id,
  linked_reschedule_request_id,
  workflow_event_id,
  created_at::text as created_at;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        if rows:
            return _effect_from_row(rows[0])
        existing = self.get_effect_for_observation(inbound_observation_id)
        if existing is None:
            raise Phase8ContractError(
                error_category="mutation_failed",
                safe_message="The observation effect could not be created or reloaded.",
            )
        return existing

    def _raise_missing_or_cross_case(
        self,
        *,
        table_name: str,
        entity_id_field: str,
        entity_id: int,
        expected_case_id: int,
    ) -> None:
        sql = f"""
select rental_case_id
from {table_name}
where {entity_id_field} = {entity_id}
limit 1;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        if not rows:
            raise Phase8ContractError(
                error_category="missing_value",
                safe_message="The requested workflow entity could not be found for the resolved rental case.",
            )
        actual_case_id = rows[0]["rental_case_id"]
        if actual_case_id != expected_case_id:
            raise ValueError("cross_case_reference")
        raise Phase8ContractError(
            error_category="missing_value",
            safe_message="The requested workflow entity could not be found for the resolved rental case.",
        )

    def _render_inquiry_fact_sql(self, *, effect, rental_case_id: int, applied_at: str) -> str:
        field_code = "guest_count" if effect.inquiry_field_code == INQUIRY_FIELD_GUEST_COUNT else "event_type"
        return f"""
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
  values (
    {rental_case_id},
    {sql_text(field_code)},
    {sql_text(effect.domain_code)},
    {_sql_json(effect.proposed_value)},
    {sql_text(_primary_observation_reference(effect))},
    {effect.expected_case_revision + 1},
    {_sql_timestamptz(applied_at)},
    {_sql_timestamptz(applied_at)}
  )
  on conflict (rental_case_id, field_code) do update
  set domain_code = excluded.domain_code,
      value_payload = excluded.value_payload,
      source_reference = excluded.source_reference,
      established_case_revision = excluded.established_case_revision,
      updated_at = excluded.updated_at;
""".strip()

    def _render_inquiry_open_question_create_sql(self, *, effect, rental_case_id: int, applied_at: str) -> str:
        question_type = effect.open_question_type or CORE_INQUIRY_FIELD_RULES[effect.inquiry_field_code].question_type
        question_text = effect.human_question_text or CORE_INQUIRY_FIELD_RULES[effect.inquiry_field_code].human_question_text
        blocking_scope = effect.blocking_scope or CORE_INQUIRY_FIELD_RULES[effect.inquiry_field_code].blocking_scope
        return f"""
  insert into public.rental_case_open_questions (
    rental_case_id,
    question_type,
    domain_code,
    human_question_text,
    blocking_scope,
    requested_from_role,
    status,
    source_reference,
    created_at,
    updated_at
  )
  select
    {rental_case_id},
    {sql_text(question_type)},
    {sql_text(effect.domain_code)},
    {sql_text(question_text)},
    {sql_text(blocking_scope)},
    'client',
    'open',
    {sql_text(_primary_observation_reference(effect))},
    {_sql_timestamptz(applied_at)},
    {_sql_timestamptz(applied_at)}
  where not exists (
    select 1
    from public.rental_case_open_questions
    where rental_case_id = {rental_case_id}
      and question_type = {sql_text(question_type)}
      and status in ('open', 'answered_pending_validation')
  );
""".strip()

    def _render_inquiry_open_question_resolve_sql(self, *, effect, rental_case_id: int, applied_at: str) -> str:
        return f"""
  update public.rental_case_open_questions
  set status = 'resolved',
      source_reference = {sql_text(_primary_observation_reference(effect))},
      resolved_at = {_sql_timestamptz(applied_at)},
      updated_at = {_sql_timestamptz(applied_at)}
  where id = {effect.open_question_id}
    and rental_case_id = {rental_case_id}
    and status in ('open', 'answered_pending_validation');
""".strip()

    def _render_inquiry_change_sql(self, *, effect, rental_case_id: int, applied_at: str) -> str:
        change_kind = CORE_INQUIRY_FIELD_RULES[effect.inquiry_field_code].change_kind
        return f"""
  insert into public.rental_case_proposed_changes (
    rental_case_id,
    change_kind,
    domain_code,
    prior_value_payload,
    proposed_value_payload,
    source_reference,
    impact_classification,
    affected_domain_codes,
    review_posture,
    status,
    detected_at,
    created_at,
    updated_at
  )
  select
    {rental_case_id},
    {sql_text(change_kind)},
    {sql_text(effect.domain_code)},
    {_sql_json(effect.current_value)},
    {_sql_json(effect.proposed_value)},
    {sql_text(_primary_observation_reference(effect))},
    null,
    array[{sql_text(effect.domain_code)}],
    null,
    'proposed',
    {_sql_timestamptz(applied_at)},
    {_sql_timestamptz(applied_at)},
    {_sql_timestamptz(applied_at)}
  where not exists (
    select 1
    from public.rental_case_proposed_changes
    where rental_case_id = {rental_case_id}
      and change_kind = {sql_text(change_kind)}
      and status in ('proposed', 'under_review')
      and prior_value_payload is not distinct from {_sql_json(effect.current_value)}
      and proposed_value_payload = {_sql_json(effect.proposed_value)}
  );
""".strip()

    def _render_inquiry_reschedule_sql(self, *, effect, rental_case_id: int, applied_at: str) -> str:
        return f"""
  insert into public.rental_case_reschedule_requests (
    rental_case_id,
    current_active_date_snapshot,
    requested_date_payload,
    candidate_dates_payload,
    consequence_summary_payload,
    status,
    urgency_class,
    created_at,
    updated_at
  )
  select
    {rental_case_id},
    {_sql_json(effect.current_value)},
    {_sql_json(effect.proposed_value)},
    '[]'::jsonb,
    {_sql_json({"source": "inquiry_intake"})},
    'proposed',
    'normal',
    {_sql_timestamptz(applied_at)},
    {_sql_timestamptz(applied_at)}
  where not exists (
    select 1
    from public.rental_case_reschedule_requests
    where rental_case_id = {rental_case_id}
      and status in ('proposed', 'evaluating', 'offered', 'awaiting_client_confirmation')
      and current_active_date_snapshot = {_sql_json(effect.current_value)}
      and requested_date_payload = {_sql_json(effect.proposed_value)}
  );
""".strip()

    def _render_inquiry_event_sql(
        self,
        *,
        effect,
        rental_case_id: int,
        actor_reference: str,
        actor_type: str | None,
        applied_at: str,
        case_revision: int,
    ) -> str:
        event_type_code = {
            INQUIRY_INTAKE_EFFECT_PROMOTE_CURRENT_VALUE: "case_fact_promoted_from_observation",
            INQUIRY_INTAKE_EFFECT_CREATE_OPEN_QUESTION: "inquiry_open_question_created",
            INQUIRY_INTAKE_EFFECT_RESOLVE_OPEN_QUESTION: "inquiry_open_question_resolved",
            INQUIRY_INTAKE_EFFECT_CREATE_PROPOSED_CHANGE: "inquiry_change_proposed",
            INQUIRY_INTAKE_EFFECT_CREATE_RESCHEDULE_REQUEST: "inquiry_reschedule_requested",
        }[effect.effect_code]
        payload = {
            "field_code": effect.inquiry_field_code,
            "effect_code": effect.effect_code,
            "reason_code": effect.reason_code,
            "source_observation_ids": list(effect.source_observation_ids),
            "current_value": effect.current_value,
            "proposed_value": effect.proposed_value,
            "case_revision": case_revision,
        }
        return f"""
  insert into public.workflow_events (
    rental_case_id,
    event_type_code,
    source_type,
    source_reference,
    actor_type,
    actor_reference,
    occurred_at,
    recorded_at,
    structured_payload,
    event_identity_key,
    origin_metadata
  )
  values (
    {rental_case_id},
    {sql_text(event_type_code)},
    'inquiry_intake_runtime',
    {sql_text(_primary_observation_reference(effect))},
    {sql_text(actor_type)},
    {sql_text(actor_reference)},
    {_sql_timestamptz(applied_at)},
    {_sql_timestamptz(applied_at)},
    {_sql_json(payload)},
    {sql_text(effect.idempotency_key)},
    {_sql_json({"phase": "8.8b"})}
  )
  on conflict (rental_case_id, event_identity_key) do nothing;
""".strip()

    def _lookup_open_question_ids(self, snapshot: ObservationCaseSnapshot, plan: InquiryIntakePlan) -> list[int]:
        question_ids: list[int] = []
        for effect in plan.effects:
            if effect.effect_code != INQUIRY_INTAKE_EFFECT_CREATE_OPEN_QUESTION:
                continue
            question_type = effect.open_question_type or CORE_INQUIRY_FIELD_RULES[effect.inquiry_field_code].question_type
            for question in snapshot.open_questions:
                if question.question_type == question_type and question.status in {'open', 'answered_pending_validation'}:
                    question_ids.append(question.open_question_id)
                    break
        return question_ids

    def _lookup_resolved_question_ids(self, plan: InquiryIntakePlan) -> list[int]:
        return [
            effect.open_question_id
            for effect in plan.effects
            if effect.effect_code == INQUIRY_INTAKE_EFFECT_RESOLVE_OPEN_QUESTION and effect.open_question_id is not None
        ]

    def _lookup_proposed_change_ids(self, snapshot: ObservationCaseSnapshot, plan: InquiryIntakePlan) -> list[int]:
        change_ids: list[int] = []
        for effect in plan.effects:
            if effect.effect_code != INQUIRY_INTAKE_EFFECT_CREATE_PROPOSED_CHANGE:
                continue
            change_kind = CORE_INQUIRY_FIELD_RULES[effect.inquiry_field_code].change_kind
            for change in snapshot.proposed_changes:
                if change.change_kind != change_kind or change.status not in ACTIVE_CHANGE_STATUSES:
                    continue
                if change.prior_value_payload == effect.current_value and change.proposed_value_payload == effect.proposed_value:
                    change_ids.append(change.proposed_case_change_id)
                    break
        return change_ids

    def _lookup_reschedule_ids(self, snapshot: ObservationCaseSnapshot, plan: InquiryIntakePlan) -> list[int]:
        request_ids: list[int] = []
        for effect in plan.effects:
            if effect.effect_code != INQUIRY_INTAKE_EFFECT_CREATE_RESCHEDULE_REQUEST:
                continue
            for request in snapshot.reschedule_requests:
                if request.status not in ACTIVE_RESCHEDULE_STATUSES:
                    continue
                if request.current_active_date_snapshot == effect.current_value and request.requested_date_payload == effect.proposed_value:
                    request_ids.append(request.reschedule_request_id)
                    break
        return request_ids


def _primary_observation_reference(effect) -> str:
    if effect.source_observation_ids:
        return f"inbound_observation:{effect.source_observation_ids[-1]}"
    return f"inquiry_intake:{effect.inquiry_field_code}"
