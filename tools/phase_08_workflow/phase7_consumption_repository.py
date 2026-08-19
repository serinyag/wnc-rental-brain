from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Protocol

from tools.phase_05_chunking.generate_pilot import run_supabase_query, sql_text

from .contracts import RentalCase, WorkflowReasoningProjection
from .lifecycle_repository import current_timestamp


@dataclass(frozen=True)
class Phase7ConsumptionCaseSnapshot:
    rental_case: RentalCase
    reasoning_projections: tuple[WorkflowReasoningProjection, ...] = ()


class Phase7ConsumptionRepositoryProtocol(Protocol):
    def load_case_snapshot(self, rental_case_id: int) -> Phase7ConsumptionCaseSnapshot | None: ...

    def get_projection_by_identity(
        self,
        *,
        rental_case_id: int,
        projection_identity_key: str,
    ) -> WorkflowReasoningProjection | None: ...

    def list_reasoning_projections(
        self,
        *,
        rental_case_id: int,
        reasoning_purpose: str | None = None,
    ) -> tuple[WorkflowReasoningProjection, ...]: ...

    def create_reasoning_projection(self, projection: WorkflowReasoningProjection) -> WorkflowReasoningProjection: ...


@dataclass
class InMemoryPhase7ConsumptionRepository:
    rental_cases: dict[int, RentalCase]
    reasoning_projections: dict[int, list[WorkflowReasoningProjection]]
    projection_ids_by_identity: dict[tuple[int, str], int]
    _reasoning_projection_id: int = 90_000

    def load_case_snapshot(self, rental_case_id: int) -> Phase7ConsumptionCaseSnapshot | None:
        rental_case = self.rental_cases.get(rental_case_id)
        if rental_case is None:
            return None
        return Phase7ConsumptionCaseSnapshot(
            rental_case=rental_case,
            reasoning_projections=tuple(self.reasoning_projections.get(rental_case_id, ())),
        )

    def get_projection_by_identity(
        self,
        *,
        rental_case_id: int,
        projection_identity_key: str,
    ) -> WorkflowReasoningProjection | None:
        projection_id = self.projection_ids_by_identity.get((rental_case_id, projection_identity_key))
        if projection_id is None:
            return None
        for projection in self.reasoning_projections.get(rental_case_id, ()):
            if projection.reasoning_projection_id == projection_id:
                return projection
        return None

    def list_reasoning_projections(
        self,
        *,
        rental_case_id: int,
        reasoning_purpose: str | None = None,
    ) -> tuple[WorkflowReasoningProjection, ...]:
        projections = tuple(self.reasoning_projections.get(rental_case_id, ()))
        if reasoning_purpose is None:
            return projections
        return tuple(
            projection
            for projection in projections
            if projection.reasoning_purpose == reasoning_purpose
        )

    def create_reasoning_projection(self, projection: WorkflowReasoningProjection) -> WorkflowReasoningProjection:
        if projection.projection_identity_key is not None:
            existing = self.get_projection_by_identity(
                rental_case_id=projection.rental_case_id,
                projection_identity_key=projection.projection_identity_key,
            )
            if existing is not None:
                return existing

        self._reasoning_projection_id += 1
        persisted = WorkflowReasoningProjection(
            reasoning_projection_id=self._reasoning_projection_id,
            rental_case_id=projection.rental_case_id,
            reasoning_purpose=projection.reasoning_purpose,
            phase_7_context_contract_version=projection.phase_7_context_contract_version,
            phase_8_workflow_contract_version=projection.phase_8_workflow_contract_version,
            source_case_revision=projection.source_case_revision,
            authority_outcome_classification=projection.authority_outcome_classification,
            degraded_retrieval_summary=projection.degraded_retrieval_summary,
            created_at=projection.created_at,
            projection_identity_key=projection.projection_identity_key,
            reasoning_state_code=projection.reasoning_state_code,
            workflow_posture=projection.workflow_posture,
            effective_confidentiality_level=projection.effective_confidentiality_level,
            de_identification_required=projection.de_identification_required,
            personal_information_present=projection.personal_information_present,
            materially_affects_completeness=projection.materially_affects_completeness,
            relevant_current_truth_item_ids=projection.relevant_current_truth_item_ids,
            relevant_guidance_item_ids=projection.relevant_guidance_item_ids,
            relevant_historical_item_ids=projection.relevant_historical_item_ids,
            conflict_codes=projection.conflict_codes,
            contamination_codes=projection.contamination_codes,
            unresolved_authority_codes=projection.unresolved_authority_codes,
            warning_codes=projection.warning_codes,
            grounding_reference_keys=projection.grounding_reference_keys,
        )
        self.reasoning_projections.setdefault(persisted.rental_case_id, []).append(persisted)
        if persisted.projection_identity_key is not None:
            self.projection_ids_by_identity[(persisted.rental_case_id, persisted.projection_identity_key)] = (
                persisted.reasoning_projection_id
            )
        return persisted


@dataclass
class SupabasePhase7ConsumptionRepository:
    query_runner: Callable[..., Any] = run_supabase_query

    def load_case_snapshot(self, rental_case_id: int) -> Phase7ConsumptionCaseSnapshot | None:
        rental_case = self._load_rental_case(rental_case_id)
        if rental_case is None:
            return None
        return Phase7ConsumptionCaseSnapshot(
            rental_case=rental_case,
            reasoning_projections=self.list_reasoning_projections(rental_case_id=rental_case_id),
        )

    def get_projection_by_identity(
        self,
        *,
        rental_case_id: int,
        projection_identity_key: str,
    ) -> WorkflowReasoningProjection | None:
        sql = f"""
select
  id as reasoning_projection_id,
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
  relevant_current_truth_item_ids,
  relevant_guidance_item_ids,
  relevant_historical_item_ids,
  conflict_codes,
  contamination_codes,
  unresolved_authority_codes,
  warning_codes,
  degraded_retrieval_summary,
  grounding_reference_keys,
  created_at::text as created_at
from public.rental_case_reasoning_projections
where rental_case_id = {rental_case_id}
  and projection_identity_key = {sql_text(projection_identity_key)}
order by id desc
limit 1;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        if not rows:
            return None
        return _projection_from_row(rows[0])

    def list_reasoning_projections(
        self,
        *,
        rental_case_id: int,
        reasoning_purpose: str | None = None,
    ) -> tuple[WorkflowReasoningProjection, ...]:
        purpose_clause = ""
        if reasoning_purpose is not None:
            purpose_clause = f"and reasoning_purpose = {sql_text(reasoning_purpose)}"
        sql = f"""
select
  id as reasoning_projection_id,
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
  relevant_current_truth_item_ids,
  relevant_guidance_item_ids,
  relevant_historical_item_ids,
  conflict_codes,
  contamination_codes,
  unresolved_authority_codes,
  warning_codes,
  degraded_retrieval_summary,
  grounding_reference_keys,
  created_at::text as created_at
from public.rental_case_reasoning_projections
where rental_case_id = {rental_case_id}
  {purpose_clause}
order by created_at desc, id desc;
""".strip()
        return tuple(
            _projection_from_row(row)
            for row in self.query_runner(sql, expect_json=True)["rows"]
        )

    def create_reasoning_projection(self, projection: WorkflowReasoningProjection) -> WorkflowReasoningProjection:
        if projection.projection_identity_key is not None:
            existing = self.get_projection_by_identity(
                rental_case_id=projection.rental_case_id,
                projection_identity_key=projection.projection_identity_key,
            )
            if existing is not None:
                return existing

        sql = f"""
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
  relevant_current_truth_item_ids,
  relevant_guidance_item_ids,
  relevant_historical_item_ids,
  conflict_codes,
  contamination_codes,
  unresolved_authority_codes,
  warning_codes,
  degraded_retrieval_summary,
  grounding_reference_keys
)
values (
  {projection.rental_case_id},
  {sql_text(projection.reasoning_purpose)},
  {projection.phase_7_context_contract_version},
  {projection.phase_8_workflow_contract_version},
  {projection.source_case_revision},
  {sql_text(projection.authority_outcome_classification)},
  {sql_text(projection.projection_identity_key)},
  {sql_text(projection.reasoning_state_code)},
  {sql_text(projection.workflow_posture)},
  {sql_text(projection.effective_confidentiality_level)},
  {'true' if projection.de_identification_required else 'false'},
  {'true' if projection.personal_information_present else 'false'},
  {'true' if projection.materially_affects_completeness else 'false'},
  {_sql_text_array(projection.relevant_current_truth_item_ids)},
  {_sql_text_array(projection.relevant_guidance_item_ids)},
  {_sql_text_array(projection.relevant_historical_item_ids)},
  {_sql_text_array(projection.conflict_codes)},
  {_sql_text_array(projection.contamination_codes)},
  {_sql_text_array(projection.unresolved_authority_codes)},
  {_sql_text_array(projection.warning_codes)},
  {sql_text(json.dumps(projection.degraded_retrieval_summary, sort_keys=True, ensure_ascii=True))}::jsonb,
  {_sql_text_array(projection.grounding_reference_keys)}
)
returning
  id as reasoning_projection_id,
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
  relevant_current_truth_item_ids,
  relevant_guidance_item_ids,
  relevant_historical_item_ids,
  conflict_codes,
  contamination_codes,
  unresolved_authority_codes,
  warning_codes,
  degraded_retrieval_summary,
  grounding_reference_keys,
  created_at::text as created_at;
""".strip()
        row = self.query_runner(sql, expect_json=True)["rows"][0]
        return _projection_from_row(row)

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


def _projection_from_row(row: dict[str, Any]) -> WorkflowReasoningProjection:
    return WorkflowReasoningProjection(
        reasoning_projection_id=row["reasoning_projection_id"],
        rental_case_id=row["rental_case_id"],
        reasoning_purpose=row["reasoning_purpose"],
        phase_7_context_contract_version=row["phase_7_context_contract_version"],
        phase_8_workflow_contract_version=row["phase_8_workflow_contract_version"],
        source_case_revision=row["source_case_revision"],
        authority_outcome_classification=row["authority_outcome_classification"],
        degraded_retrieval_summary=row["degraded_retrieval_summary"],
        created_at=row["created_at"],
        projection_identity_key=row.get("projection_identity_key"),
        reasoning_state_code=row.get("reasoning_state_code"),
        workflow_posture=row.get("workflow_posture"),
        effective_confidentiality_level=row.get("effective_confidentiality_level"),
        de_identification_required=row.get("de_identification_required", False),
        personal_information_present=row.get("personal_information_present", False),
        materially_affects_completeness=row.get("materially_affects_completeness", False),
        relevant_current_truth_item_ids=tuple(row.get("relevant_current_truth_item_ids", ())),
        relevant_guidance_item_ids=tuple(row.get("relevant_guidance_item_ids", ())),
        relevant_historical_item_ids=tuple(row.get("relevant_historical_item_ids", ())),
        conflict_codes=tuple(row.get("conflict_codes", ())),
        contamination_codes=tuple(row.get("contamination_codes", ())),
        unresolved_authority_codes=tuple(row.get("unresolved_authority_codes", ())),
        warning_codes=tuple(row.get("warning_codes", ())),
        grounding_reference_keys=tuple(row.get("grounding_reference_keys", ())),
    )


def _sql_text_array(values: tuple[str, ...]) -> str:
    escaped = ", ".join(sql_text(value) for value in values)
    return f"array[{escaped}]::text[]"
