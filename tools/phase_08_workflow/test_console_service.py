from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass, field, replace
from datetime import datetime
from http import HTTPStatus
from typing import Any, Callable

from tools.phase_05_chunking.generate_pilot import find_local_db_container, run_supabase_query
from tools.phase_07_reasoning.contracts import (
    AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
    AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
    AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION,
    PHASE_7_CONTEXT_CONTRACT_VERSION,
)
from tools.runtime_environment import (
    AppRuntimeConfig,
    RuntimeConfigurationError,
    validate_test_console_startup,
)

from .asana_adapter import AsanaAdapterConfig, build_asana_execution_adapter_from_env
from .clock import CallableClock, Clock, MutableTestClock, SystemClock
from .contracts import (
    ACTION_CATEGORY_COORDINATION,
    ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
    ACTION_TYPE_REQUEST_CLIENT_INFORMATION,
    APPROVAL_POSTURE_AUTOMATIC_ALLOWED,
    APPROVAL_REQUEST_STATUS_OPEN,
    OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION,
    PHASE_7_REASONING_STATE_INSUFFICIENT_INFORMATION,
    PHASE_7_REASONING_STATE_MANUAL_REVIEW_REQUIRED,
    PHASE_7_REASONING_STATE_NO_APPLICABLE_RULE,
    PHASE_7_REASONING_STATE_REQUIRES_CONFIRMATION,
    PHASE_7_REASONING_STATE_RESOLVED,
    PHASE_8_PHASE7_WORKFLOW_CONSUMPTION_CONTRACT_VERSION,
    REASONING_PURPOSE_FEASIBILITY_REVIEW,
    OPEN_QUESTION_STATUS_OPEN,
    WORKFLOW_CONFIDENTIALITY_LEVEL_INTERNAL,
    WORKFLOW_REASONING_POSTURE_REVIEW_REQUIRED,
    WORKFLOW_REASONING_POSTURE_SAFE_FOR_DETERMINISTIC_USE,
    ApprovalRequest,
    WorkflowReasoningProjection,
    WorkflowAction,
    WORKFLOW_ACTION_STATUS_APPROVED,
    WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
    WORKFLOW_ACTION_STATUS_CANCELLED,
    WORKFLOW_ACTION_STATUS_EXECUTING,
    WORKFLOW_ACTION_STATUS_FAILED,
    WORKFLOW_ACTION_STATUS_PROPOSED,
    WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
    WORKFLOW_ACTION_STATUS_SUCCEEDED,
    WORKFLOW_ACTION_STATUS_SUPERSEDED,
)
from .execution_runtime import (
    DeterministicFakeExecutionAdapter,
    ExecutionAdapterRegistry,
    build_default_fake_execution_registry,
    evaluate_due_follow_ups,
    execute_workflow_action,
    fake_permanent_failure_adapter,
    fake_retryable_failure_adapter,
    fake_timeout_adapter,
)
from .execution_types import (
    EXECUTION_ATTEMPT_STATUS_FAILED,
    EXECUTION_ATTEMPT_STATUS_SUCCEEDED,
    EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS,
    FollowUpEvaluationRequest,
    NormalizedExecutionResult,
    WorkflowActionExecutionRequest,
)
from .inquiry_response_drafting import (
    DeterministicInquiryResponseDraftGenerator,
    InquiryResponseDraftContent,
    InquiryResponseDraftContext,
    InquiryResponseDraftRevision,
    InquiryResponseQuestionLine,
    INQUIRY_DRAFT_SOURCE_GENERATED,
    INQUIRY_DRAFT_SOURCE_HUMAN_EDITED,
    INQUIRY_DRAFT_SOURCE_REGENERATED,
    INQUIRY_DRAFT_STATUS_APPROVED,
    INQUIRY_DRAFT_STATUS_DRAFT,
    INQUIRY_DRAFT_STATUS_NEEDS_APPROVAL,
    INQUIRY_DRAFT_STATUS_REJECTED,
    INQUIRY_DRAFT_STATUS_SEND_FAILED,
    INQUIRY_DRAFT_STATUS_SEND_OUTCOME_UNCERTAIN,
    INQUIRY_DRAFT_STATUS_SIMULATED_SENT,
    INQUIRY_DRAFT_STATUS_STALE,
    content_hash_payload,
    context_hash_payload,
    display_status_for_revision,
    render_draft_body,
    validate_draft_content,
)
from .inquiry_intake import (
    INQUIRY_INTAKE_OUTCOME_PROMOTED,
    apply_inquiry_intake,
)
from .inquiry_waiting import InquiryFollowUpPolicy, reconcile_inquiry_waiting
from .lifecycle_repository import _sql_int, _sql_json, _sql_timestamptz, sql_text
from .observation_contracts import (
    InboundObservation,
    InboundObservationEffect,
    InboundSourceRecord,
    OBSERVATION_ASSERTED_BY_CLIENT,
    OBSERVATION_CLAIM_KIND_CHANGE_REQUEST,
    OBSERVATION_CLAIM_KIND_CONFIRMATION,
    OBSERVATION_CLAIM_KIND_EXCEPTION_REQUEST,
    OBSERVATION_CLAIM_KIND_NEW_INFORMATION,
    OBSERVATION_CLAIM_KIND_QUESTION_ANSWER,
    OBSERVATION_CLAIM_KIND_REQUIREMENT_EVIDENCE,
    OBSERVATION_TYPE_CASE_DECISION_CANDIDATE,
    OBSERVATION_TYPE_CHANGE_CANDIDATE,
    OBSERVATION_TYPE_CONFIRMATION_CANDIDATE,
    OBSERVATION_TYPE_FACT_CANDIDATE,
    OBSERVATION_TYPE_REQUEST_CANDIDATE,
    OBSERVATION_TYPE_REQUIREMENT_EVIDENCE_CANDIDATE,
    OBSERVATION_VALUE_TYPE_BOOLEAN,
    OBSERVATION_VALUE_TYPE_ENUM,
    OBSERVATION_VALUE_TYPE_ENUM_ARRAY,
    OBSERVATION_VALUE_TYPE_INTEGER,
    OBSERVATION_VALUE_TYPE_JSON_OBJECT,
)
from .observation_registry import get_field_definition
from .observation_types import (
    CaseAssociationInput,
    CaseAssociationResult,
    InboundSourceRecordInput,
    StructuredObservationCandidate,
    StructuredObservationIngestionRequest,
)
from .observations import ingest_structured_observations
from .orchestration_repository import (
    InMemoryWorkflowOrchestrationRepository,
    SupabaseWorkflowOrchestrationRepository,
    WorkflowOrchestrationCaseSnapshot,
)
from .orchestration_runtime import apply_approval_decision, reconcile_workflow_orchestration
from .orchestration_types import ApprovalDecisionInput, ORCHESTRATION_DECISION_APPROVED, ORCHESTRATION_DECISION_REJECTED
from .outlook_adapter import OutlookAdapterConfig, build_outlook_execution_adapter_from_env
from .phase7_consumption_repository import (
    InMemoryPhase7ConsumptionRepository,
    SupabasePhase7ConsumptionRepository,
)
from .phase7_consumption_types import (
    WORKFLOW_SEMANTIC_STATE_KNOWN_CONDITIONAL,
    WORKFLOW_SEMANTIC_STATE_KNOWN_NO,
    WORKFLOW_SEMANTIC_STATE_KNOWN_YES,
    WORKFLOW_SEMANTIC_STATE_UNKNOWN_INTERNAL,
)
from .provider_safety import guard_asana_execution_adapter, guard_outlook_execution_adapter
from .supabase_observation_repository import SupabaseObservationRepository
from .test_console_projection import (
    BookingFeeRuleContext,
    LatestCommunicationContext,
    ObservedFieldCandidate,
    TestConsoleCaseMetadata,
    WorkingProposalProjection,
    build_human_work_preview,
    build_working_proposal_projection,
    humanize_code,
    infer_asana_master_task_reference,
    summarize_test_metadata,
)
from .validation import Phase8ContractError


TEST_CONSOLE_CASE_REGISTERED_EVENT = "test_console_case_registered"
TEST_CONSOLE_RAW_EVIDENCE_EVENT = "test_console_raw_evidence_recorded"
TEST_CONSOLE_SOURCE_TYPE = "test_console"
TEST_CONSOLE_HOST_ENV = "WORKFLOW_TEST_CONSOLE_HOST"
TEST_CONSOLE_PORT_ENV = "WORKFLOW_TEST_CONSOLE_PORT"
TEST_CONSOLE_ALLOW_REAL_PROVIDERS_ENV = "WORKFLOW_TEST_CONSOLE_ALLOW_REAL_PROVIDERS"
TEST_CONSOLE_ALLOW_NON_LOCAL_BIND_ENV = "WORKFLOW_TEST_CONSOLE_ALLOW_NON_LOCAL_BIND"
TEST_CONSOLE_QUERY_TIMEOUT_ENV = "WORKFLOW_TEST_CONSOLE_QUERY_TIMEOUT_SECONDS"
TEST_CONSOLE_WORKFLOW_EVENT_LIMIT_ENV = "WORKFLOW_TEST_CONSOLE_WORKFLOW_EVENT_LIMIT"
TEST_CONSOLE_INQUIRY_FOLLOW_UP_DELAY_DAYS_ENV = "WORKFLOW_TEST_CONSOLE_INQUIRY_COLD_FOLLOW_UP_DELAY_DAYS"
TEST_CONSOLE_DEFAULT_HOST = "127.0.0.1"
TEST_CONSOLE_DEFAULT_PORT = 8765
TEST_CONSOLE_DEFAULT_QUERY_TIMEOUT_SECONDS = 10.0
TEST_CONSOLE_DEFAULT_WORKFLOW_EVENT_LIMIT = 100
TEST_CONSOLE_DEFAULT_INQUIRY_FOLLOW_UP_DELAY_DAYS = 7
TEST_CONSOLE_DEFAULT_RENTAL_TYPE_CODE = "custom_scope"
TEST_CONSOLE_OPERATOR_REFERENCE = "test_console:operator"
TEST_CONSOLE_OPERATOR_TYPE = "operator"

LOGGER = logging.getLogger(__name__)


class TestConsoleError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        failure_code: str = "TEST_CONSOLE_ERROR",
        status: HTTPStatus = HTTPStatus.BAD_REQUEST,
    ) -> None:
        super().__init__(message)
        self.failure_code = failure_code
        self.status = status


class TestConsoleReadError(TestConsoleError):
    def __init__(self, message: str, *, failure_code: str) -> None:
        super().__init__(message, failure_code=failure_code, status=HTTPStatus.SERVICE_UNAVAILABLE)


@dataclass(frozen=True)
class SyntheticAuthorityIssue:
    domain_code: str
    issue_code: str
    semantic_state_code: str
    authority_outcome_classification: str
    reasoning_state_code: str
    source_label: str
    source_value: Any
    source_snapshot: dict[str, Any]


@dataclass(frozen=True)
class TestConsoleConfig:
    runtime: AppRuntimeConfig = field(default_factory=AppRuntimeConfig.local_default)
    host: str = TEST_CONSOLE_DEFAULT_HOST
    port: int = TEST_CONSOLE_DEFAULT_PORT
    allow_real_providers: bool = False
    allow_non_local_bind: bool = False
    query_timeout_seconds: float = TEST_CONSOLE_DEFAULT_QUERY_TIMEOUT_SECONDS
    workflow_event_limit: int = TEST_CONSOLE_DEFAULT_WORKFLOW_EVENT_LIMIT
    inquiry_cold_follow_up_delay_days: int = TEST_CONSOLE_DEFAULT_INQUIRY_FOLLOW_UP_DELAY_DAYS

    @classmethod
    def from_env(cls) -> TestConsoleConfig:
        return cls(
            runtime=AppRuntimeConfig.from_env(),
            host=os.environ.get(TEST_CONSOLE_HOST_ENV, TEST_CONSOLE_DEFAULT_HOST).strip() or TEST_CONSOLE_DEFAULT_HOST,
            port=int(os.environ.get(TEST_CONSOLE_PORT_ENV, str(TEST_CONSOLE_DEFAULT_PORT))),
            allow_real_providers=_env_flag(TEST_CONSOLE_ALLOW_REAL_PROVIDERS_ENV),
            allow_non_local_bind=_env_flag(TEST_CONSOLE_ALLOW_NON_LOCAL_BIND_ENV),
            query_timeout_seconds=float(
                os.environ.get(
                    TEST_CONSOLE_QUERY_TIMEOUT_ENV,
                    str(TEST_CONSOLE_DEFAULT_QUERY_TIMEOUT_SECONDS),
                )
            ),
            workflow_event_limit=int(
                os.environ.get(
                    TEST_CONSOLE_WORKFLOW_EVENT_LIMIT_ENV,
                    str(TEST_CONSOLE_DEFAULT_WORKFLOW_EVENT_LIMIT),
                )
            ),
            inquiry_cold_follow_up_delay_days=int(
                os.environ.get(
                    TEST_CONSOLE_INQUIRY_FOLLOW_UP_DELAY_DAYS_ENV,
                    str(TEST_CONSOLE_DEFAULT_INQUIRY_FOLLOW_UP_DELAY_DAYS),
                )
            ),
        )

    def validate(self) -> None:
        if self.query_timeout_seconds <= 0:
            raise TestConsoleError(f"{TEST_CONSOLE_QUERY_TIMEOUT_ENV} must be greater than 0.")
        if self.workflow_event_limit <= 0:
            raise TestConsoleError(f"{TEST_CONSOLE_WORKFLOW_EVENT_LIMIT_ENV} must be greater than 0.")
        if self.inquiry_cold_follow_up_delay_days < 0:
            raise TestConsoleError(
                f"{TEST_CONSOLE_INQUIRY_FOLLOW_UP_DELAY_DAYS_ENV} must be greater than or equal to 0."
            )
        try:
            validate_test_console_startup(
                runtime=self.runtime,
                host=self.host,
                allow_non_local_bind=self.allow_non_local_bind,
                allow_real_providers=self.allow_real_providers,
            )
        except RuntimeConfigurationError as exc:
            raise TestConsoleError(str(exc)) from exc

    def inquiry_follow_up_policy(self) -> InquiryFollowUpPolicy:
        return InquiryFollowUpPolicy(
            cold_follow_up_delay_days=self.inquiry_cold_follow_up_delay_days,
        )


@dataclass(frozen=True)
class TestCaseSummary:
    rental_case_id: int
    case_reference_code: str
    lifecycle_state: str
    case_revision: int
    display_name: str
    client_label: str | None
    contact_email: str | None
    event_reference: str | None
    active_event_start: str | None
    last_activity: str
    open_blocker_count: int
    open_question_count: int
    pending_approval_count: int
    executable_action_count: int


@dataclass(frozen=True)
class RawEvidenceRecord:
    workflow_event_id: int
    occurred_at: str
    source_label: str | None
    sender: str | None
    subject: str | None
    body: str | None
    external_test_reference: str | None
    inbound_source_record_id: int | None

    @property
    def summary(self) -> str:
        subject = self.subject or "No subject"
        sender = self.sender or "unknown sender"
        return f"Last known communication: {subject} from {sender}"


@dataclass(frozen=True)
class EvidenceBundle:
    source_record: InboundSourceRecord
    raw_evidence: RawEvidenceRecord | None
    observations: tuple[InboundObservation, ...]
    effects: tuple[InboundObservationEffect | None, ...]


@dataclass(frozen=True)
class CaseConsoleSnapshot:
    metadata: TestConsoleCaseMetadata
    orchestration_snapshot: WorkflowOrchestrationCaseSnapshot
    evidence_bundles: tuple[EvidenceBundle, ...]
    test_metadata_lines: tuple[str, ...]
    working_proposal: WorkingProposalProjection
    human_work_preview: tuple[str, ...]
    asana_master_task_reference: str | None
    provider_mode_lines: tuple[str, ...]
    workflow_event_total_count: int = 0
    workflow_event_limit: int = TEST_CONSOLE_DEFAULT_WORKFLOW_EVENT_LIMIT
    evidence_notice: str | None = None
    timeline_notice: str | None = None
    simulated_outlook_threads: tuple[SimulatedOutlookThread, ...] = ()


@dataclass(frozen=True)
class SimulatedOutlookThread:
    conversation_key: str
    thread_label: str
    workflow_action_id: int | None
    workflow_action_status: str | None
    current_display_status: str | None
    question_labels: tuple[str, ...]
    recipient_email: str | None
    open_approval_request_id: int | None
    current_revision: InquiryResponseDraftRevision | None = None
    draft_history: tuple[InquiryResponseDraftRevision, ...] = ()
    can_generate: bool = False
    can_regenerate: bool = False
    can_edit: bool = False
    can_simulate_send: bool = False
    status_note: str | None = None


@dataclass(frozen=True)
class OperationReport:
    title: str
    success: bool
    lines: tuple[str, ...]
    failure_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class TestConsoleClockStatus:
    current_time: str
    real_current_time: str
    simulated: bool


@dataclass(frozen=True)
class HealthComponentReport:
    status: str
    detail: str
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": self.status,
            "detail": self.detail,
        }
        if self.metrics:
            payload["metrics"] = self.metrics
        return payload


@dataclass(frozen=True)
class TestConsoleHealthReport:
    overall_status: str
    environment: str
    application: HealthComponentReport
    database: HealthComponentReport
    phase5: HealthComponentReport
    phase6: HealthComponentReport
    providers: dict[str, str]

    @property
    def http_status(self) -> HTTPStatus:
        return HTTPStatus.OK if self.overall_status in {"ok", "warn"} else HTTPStatus.SERVICE_UNAVAILABLE

    def to_payload(self) -> dict[str, Any]:
        return {
            "status": self.overall_status,
            "environment": self.environment,
            "application": self.application.to_payload(),
            "database": self.database.to_payload(),
            "phase5": self.phase5.to_payload(),
            "phase6": self.phase6.to_payload(),
            "providers": dict(self.providers),
        }


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _json_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")).hexdigest()


def _generate_case_reference(now: Callable[[], str]) -> str:
    digits = "".join(character for character in now() if character.isdigit())
    return f"RC-{digits[:17]}"


def _ambiguous_fake_adapter(
    adapter_code: str,
    *,
    now: Callable[[], str],
) -> DeterministicFakeExecutionAdapter:
    return DeterministicFakeExecutionAdapter(
        result_factory=lambda _action, _context, _idempotency: NormalizedExecutionResult(
            adapter_code=adapter_code,
            attempt_status=EXECUTION_ATTEMPT_STATUS_FAILED,
            response_snapshot={"provider_mode": "deterministic_fake", "result": "ambiguous"},
            retry_eligible=False,
            failure_code=EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS,
            completed_at=now(),
        )
    )


def _local_provider_lines(allow_real_providers: bool) -> tuple[str, ...]:
    if not allow_real_providers:
        return ("REAL PROVIDER EXECUTION DISABLED", "email -> deterministic fake", "task_surface -> deterministic fake")
    return (
        "REAL PROVIDER EXECUTION ENABLED",
        "email -> Outlook / Microsoft Graph",
        "task_surface -> Asana",
    )


def _build_test_console_query_runner(timeout_seconds: float) -> Callable[..., Any]:
    def runner(sql: str, *, expect_json: bool):
        try:
            return run_supabase_query(sql, expect_json=expect_json, timeout_seconds=timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            raise TestConsoleReadError(
                "Console read failed.\n\nReason:\nDATABASE_READ_TIMEOUT",
                failure_code="DATABASE_READ_TIMEOUT",
            ) from exc
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr or ""
            if "No such container" in stderr:
                find_local_db_container.cache_clear()
            raise TestConsoleReadError(
                "Console read failed.\n\nReason:\nDATABASE_READ_FAILED",
                failure_code="DATABASE_READ_FAILED",
            ) from exc

    return runner


def _format_stage_timings(stage_timings: dict[str, float]) -> str:
    return " ".join(f"{key}_ms={value * 1000:.1f}" for key, value in stage_timings.items())


def _combine_health_statuses(*statuses: str) -> str:
    rank = {"ok": 0, "disabled": 0, "warn": 1, "fail": 2}
    highest = max((rank.get(status, 2) for status in statuses), default=0)
    if highest >= 2:
        return "fail"
    if highest == 1:
        return "warn"
    return "ok"


class TestConsoleService:
    def __init__(
        self,
        *,
        orchestration_repository: SupabaseWorkflowOrchestrationRepository | None = None,
        observation_repository: SupabaseObservationRepository | None = None,
        query_runner: Callable[..., Any] | None = None,
        config: TestConsoleConfig | None = None,
        draft_generator: DeterministicInquiryResponseDraftGenerator | None = None,
        now: Callable[[], str] | None = None,
        clock: Clock | None = None,
    ) -> None:
        self.config = config or TestConsoleConfig.from_env()
        if clock is not None:
            self.clock = clock
        elif now is not None:
            self.clock = CallableClock(now)
        elif self.config.runtime.allows_mutable_test_clock():
            self.clock = MutableTestClock(system_clock=SystemClock())
        else:
            self.clock = SystemClock()
        self.now = self.clock.now
        self.query_runner = query_runner or _build_test_console_query_runner(self.config.query_timeout_seconds)
        self.orchestration_repository = orchestration_repository or SupabaseWorkflowOrchestrationRepository(query_runner=self.query_runner)
        self.observation_repository = observation_repository or SupabaseObservationRepository(query_runner=self.query_runner)
        self.draft_generator = draft_generator or DeterministicInquiryResponseDraftGenerator()

    def clock_controls_enabled(self) -> bool:
        return self.config.runtime.allows_mutable_test_clock()

    def get_clock_status(self) -> TestConsoleClockStatus:
        simulated = isinstance(self.clock, MutableTestClock) and self.clock.is_simulated()
        real_current_time = self.clock.real_time() if isinstance(self.clock, MutableTestClock) else self.now()
        return TestConsoleClockStatus(
            current_time=self.now(),
            real_current_time=real_current_time,
            simulated=simulated,
        )

    def get_health_report(self) -> TestConsoleHealthReport:
        application = HealthComponentReport(
            status="ok",
            detail="WSGI application responded.",
        )
        provider_statuses = self._provider_health_statuses()
        try:
            database = self._load_database_health()
            phase5 = self._load_phase5_health()
            phase6 = self._load_phase6_health()
        except TestConsoleReadError as exc:
            database = HealthComponentReport(
                status="fail",
                detail="Database connectivity check failed.",
                metrics={"failure_code": exc.failure_code},
            )
            phase5 = HealthComponentReport(
                status="fail",
                detail="Skipped because the database health check failed.",
            )
            phase6 = HealthComponentReport(
                status="fail",
                detail="Skipped because the database health check failed.",
            )
        provider_status_values = tuple(provider_statuses.values())
        provider_status = "ok"
        if self.config.allow_real_providers and any(status == "misconfigured" for status in provider_status_values):
            provider_status = "fail"
        overall_status = _combine_health_statuses(
            application.status,
            database.status,
            phase5.status,
            phase6.status,
            provider_status,
        )
        return TestConsoleHealthReport(
            overall_status=overall_status,
            environment=self.config.runtime.app_env.value,
            application=application,
            database=database,
            phase5=phase5,
            phase6=phase6,
            providers=provider_statuses,
        )

    def _load_database_health(self) -> HealthComponentReport:
        sql = "select 1 as ok;"
        row = self.query_runner(sql, expect_json=True)["rows"][0]
        if row.get("ok") != 1:
            return HealthComponentReport(
                status="fail",
                detail="Database connectivity check returned an unexpected result.",
            )
        return HealthComponentReport(
            status="ok",
            detail="Bounded database query succeeded.",
        )

    def _load_phase5_health(self) -> HealthComponentReport:
        sql = """
with current_inputs as (
  select count(*)::integer as eligible_chunks
  from private.current_knowledge_chunk_embedding_inputs
),
active_models as (
  select
    count(*)::integer as active_model_count,
    min(id)::integer as active_model_id
  from private.knowledge_embedding_models
  where is_retrieval_approved
    and is_active
),
matching_embeddings as (
  select count(distinct ckei.chunk_id)::integer as embedded_chunks
  from private.current_knowledge_chunk_embedding_inputs ckei
  cross join active_models am
  join private.knowledge_embeddings ke
    on ke.chunk_id = ckei.chunk_id
   and ke.embedding_model_id = am.active_model_id
   and ke.input_content_hash = ckei.embedding_input_hash
  where am.active_model_id is not null
)
select
  ci.eligible_chunks,
  am.active_model_count,
  am.active_model_id,
  coalesce(me.embedded_chunks, 0)::integer as embedded_chunks
from current_inputs ci
cross join active_models am
left join matching_embeddings me on true;
""".strip()
        row = self.query_runner(sql, expect_json=True)["rows"][0]
        eligible_chunks = int(row["eligible_chunks"])
        active_model_count = int(row["active_model_count"])
        embedded_chunks = int(row["embedded_chunks"])
        metrics: dict[str, Any] = {
            "eligible_chunks": eligible_chunks,
            "active_model_count": active_model_count,
            "embedded_chunks": embedded_chunks,
            "missing_chunks": max(eligible_chunks - embedded_chunks, 0),
        }
        if row.get("active_model_id") is not None:
            metrics["active_model_id"] = int(row["active_model_id"])
        if eligible_chunks <= 0:
            return HealthComponentReport(
                status="fail",
                detail="Phase 5 current knowledge corpus is not bootstrapped.",
                metrics=metrics,
            )
        if active_model_count != 1:
            return HealthComponentReport(
                status="warn",
                detail=(
                    "Phase 5 current corpus is present, but hybrid retrieval is not fully bootstrapped. "
                    "The current runtime falls back to FTS when semantic preflight is unavailable."
                ),
                metrics=metrics,
            )
        if embedded_chunks != eligible_chunks:
            return HealthComponentReport(
                status="warn",
                detail=(
                    "Phase 5 current corpus is present, but embeddings are incomplete for the active retrieval-approved model. "
                    "The current runtime falls back to FTS when semantic preflight is incomplete."
                ),
                metrics=metrics,
            )
        return HealthComponentReport(
            status="ok",
            detail="Phase 5 current corpus and semantic embedding coverage are bootstrapped.",
            metrics=metrics,
        )

    def _load_phase6_health(self) -> HealthComponentReport:
        sql = """
with current_inputs as (
  select count(*)::integer as eligible_units
  from private.current_historical_case_embedding_inputs
),
active_models as (
  select
    count(*)::integer as active_model_count,
    min(id)::integer as active_model_id
  from private.historical_case_embedding_models
  where is_retrieval_approved
    and is_active
),
matching_embeddings as (
  select count(distinct chcei.search_unit_id)::integer as embedded_units
  from private.current_historical_case_embedding_inputs chcei
  cross join active_models am
  join private.historical_case_embeddings hce
    on hce.historical_case_search_unit_id = chcei.search_unit_id
   and hce.embedding_model_id = am.active_model_id
   and hce.input_content_hash = chcei.embedding_input_hash
  where am.active_model_id is not null
),
stale_units as (
  select count(distinct chcei.search_unit_id)::integer as stale_units
  from private.current_historical_case_embedding_inputs chcei
  cross join active_models am
  where am.active_model_id is not null
    and not exists (
      select 1
      from private.historical_case_embeddings hce_current
      where hce_current.historical_case_search_unit_id = chcei.search_unit_id
        and hce_current.embedding_model_id = am.active_model_id
        and hce_current.input_content_hash = chcei.embedding_input_hash
    )
    and exists (
      select 1
      from private.historical_case_embeddings hce_stale
      where hce_stale.historical_case_search_unit_id = chcei.search_unit_id
        and hce_stale.embedding_model_id = am.active_model_id
    )
)
select
  ci.eligible_units,
  am.active_model_count,
  am.active_model_id,
  coalesce(me.embedded_units, 0)::integer as embedded_units,
  coalesce(su.stale_units, 0)::integer as stale_units
from current_inputs ci
cross join active_models am
left join matching_embeddings me on true
left join stale_units su on true;
""".strip()
        row = self.query_runner(sql, expect_json=True)["rows"][0]
        eligible_units = int(row["eligible_units"])
        active_model_count = int(row["active_model_count"])
        embedded_units = int(row["embedded_units"])
        stale_units = int(row["stale_units"])
        missing_units = max(eligible_units - embedded_units, 0)
        metrics: dict[str, Any] = {
            "eligible_units": eligible_units,
            "active_model_count": active_model_count,
            "embedded_units": embedded_units,
            "missing_units": missing_units,
            "stale_units": stale_units,
        }
        if row.get("active_model_id") is not None:
            metrics["active_model_id"] = int(row["active_model_id"])
        if eligible_units <= 0:
            return HealthComponentReport(
                status="fail",
                detail="Phase 6 historical retrieval inputs are not bootstrapped.",
                metrics=metrics,
            )
        if active_model_count != 1:
            return HealthComponentReport(
                status="fail",
                detail="Phase 6 requires exactly one active retrieval-approved historical embedding model.",
                metrics=metrics,
            )
        if missing_units != 0 or stale_units != 0:
            return HealthComponentReport(
                status="fail",
                detail="Phase 6 historical embedding coverage is incomplete for the active retrieval-approved model.",
                metrics=metrics,
            )
        return HealthComponentReport(
            status="ok",
            detail="Phase 6 historical retrieval model and embedding coverage are bootstrapped.",
            metrics=metrics,
        )

    def _provider_health_statuses(self) -> dict[str, str]:
        outlook_config = OutlookAdapterConfig.from_env()
        asana_config = AsanaAdapterConfig.from_env()
        return {
            "outlook": self._resolve_outlook_provider_status(outlook_config),
            "asana": self._resolve_asana_provider_status(asana_config),
        }

    def _resolve_outlook_provider_status(self, config: OutlookAdapterConfig) -> str:
        runtime = self.config.runtime
        allowlist_configured = bool(runtime.staging_allowed_email_recipients or runtime.staging_allowed_email_domains)
        fully_configured = bool(
            config.tenant_id
            and config.client_id
            and config.client_secret
            and config.sender_mailbox
        )
        any_configuration = allowlist_configured or any(
            value is not None
            for value in (
                config.tenant_id,
                config.client_id,
                config.client_secret,
                config.sender_mailbox,
            )
        )
        if not any_configuration:
            return "disabled"
        if not self.config.allow_real_providers:
            return "configured_but_disabled"
        if runtime.is_staging and not allowlist_configured:
            return "misconfigured"
        return "configured" if fully_configured else "misconfigured"

    def _resolve_asana_provider_status(self, config: AsanaAdapterConfig) -> str:
        runtime = self.config.runtime
        allowlist_configured = bool(runtime.staging_allowed_asana_project_gids)
        fully_configured = bool(
            config.access_token
            and config.workspace_gid
            and config.default_project_gid
        )
        any_configuration = allowlist_configured or any(
            value is not None
            for value in (
                config.access_token,
                config.workspace_gid,
                config.default_project_gid,
            )
        )
        if not any_configuration:
            return "disabled"
        if not self.config.allow_real_providers:
            return "configured_but_disabled"
        if runtime.is_staging and not allowlist_configured:
            return "misconfigured"
        return "configured" if fully_configured else "misconfigured"

    def advance_test_clock(self, *, hours: int = 0, days: int = 0) -> TestConsoleClockStatus:
        if not isinstance(self.clock, MutableTestClock):
            raise TestConsoleError("Test clock controls are unavailable for this service instance.")
        try:
            self.clock.advance(hours=hours, days=days)
        except ValueError as exc:
            raise TestConsoleError(str(exc)) from exc
        return self.get_clock_status()

    def set_test_clock(self, *, timestamp_value: str | None) -> TestConsoleClockStatus:
        if not isinstance(self.clock, MutableTestClock):
            raise TestConsoleError("Test clock controls are unavailable for this service instance.")
        normalized_value = _normalize_optional_text(timestamp_value)
        if normalized_value is None:
            raise TestConsoleError("Set time requires a timestamp value.")
        try:
            self.clock.set(normalized_value)
        except ValueError as exc:
            raise TestConsoleError(f"Invalid timestamp value: {normalized_value}") from exc
        return self.get_clock_status()

    def reset_test_clock(self) -> TestConsoleClockStatus:
        if not isinstance(self.clock, MutableTestClock):
            raise TestConsoleError("Test clock controls are unavailable for this service instance.")
        self.clock.reset()
        return self.get_clock_status()

    def list_test_cases(self) -> tuple[TestCaseSummary, ...]:
        started = time.perf_counter()
        sql = f"""
with marker as (
  select distinct on (rental_case_id)
    rental_case_id,
    structured_payload
  from public.workflow_events
  where event_type_code = {sql_text(TEST_CONSOLE_CASE_REGISTERED_EVENT)}
    and source_type = {sql_text(TEST_CONSOLE_SOURCE_TYPE)}
  order by rental_case_id, id asc
)
select
  rc.id as rental_case_id,
  rc.case_reference_code,
  rc.lifecycle_state,
  rc.case_revision,
  rc.active_event_start::text as active_event_start,
  greatest(
    rc.updated_at,
    coalesce(max(we.occurred_at), rc.updated_at)
  )::text as last_activity,
  marker.structured_payload ->> 'label' as display_name,
  marker.structured_payload ->> 'client_label' as client_label,
  marker.structured_payload ->> 'contact_email' as contact_email,
  marker.structured_payload ->> 'event_reference' as event_reference,
  count(distinct b.id) filter (where b.status = 'open') as open_blocker_count,
  count(distinct q.id) filter (where q.status in ('open', 'answered_pending_validation')) as open_question_count,
  count(distinct a.id) filter (where a.status = 'open') as pending_approval_count,
  count(distinct wa.id) filter (where wa.status = 'ready_to_execute') as executable_action_count
from public.rental_cases rc
join marker
  on marker.rental_case_id = rc.id
left join public.workflow_events we
  on we.rental_case_id = rc.id
left join public.rental_case_blockers b
  on b.rental_case_id = rc.id
left join public.rental_case_open_questions q
  on q.rental_case_id = rc.id
left join public.rental_case_approval_requests a
  on a.rental_case_id = rc.id
left join public.workflow_actions wa
  on wa.rental_case_id = rc.id
group by
  rc.id,
  rc.case_reference_code,
  rc.lifecycle_state,
  rc.case_revision,
  rc.active_event_start,
  rc.updated_at,
  marker.structured_payload
order by last_activity desc, rc.id desc;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        cases = tuple(
            TestCaseSummary(
                rental_case_id=row["rental_case_id"],
                case_reference_code=row["case_reference_code"],
                lifecycle_state=row["lifecycle_state"],
                case_revision=row["case_revision"],
                display_name=row["display_name"] or row["case_reference_code"],
                client_label=row["client_label"],
                contact_email=row["contact_email"],
                event_reference=row["event_reference"],
                active_event_start=row["active_event_start"],
                last_activity=row["last_activity"],
                open_blocker_count=row["open_blocker_count"],
                open_question_count=row["open_question_count"],
                pending_approval_count=row["pending_approval_count"],
                executable_action_count=row["executable_action_count"],
            )
            for row in rows
        )
        LOGGER.info(
            "test_console_request route=index query_count=1 case_count=%s total_ms=%.1f",
            len(cases),
            (time.perf_counter() - started) * 1000,
        )
        return cases

    def create_test_case(
        self,
        *,
        label: str | None,
        client_label: str | None,
        contact_email: str | None,
        event_reference: str | None,
    ) -> OperationReport:
        case_reference_code = _generate_case_reference(self.now)
        created_at = self.now()
        payload = {
            "test_case": True,
            "label": _normalize_optional_text(label),
            "client_label": _normalize_optional_text(client_label),
            "contact_email": _normalize_optional_text(contact_email),
            "event_reference": _normalize_optional_text(event_reference),
        }
        event_identity_key = f"test-console:case:{case_reference_code}"
        insert_sql = f"""
with inserted_case as (
  insert into public.rental_cases (
    case_reference_code,
    lifecycle_state,
    case_revision,
    rental_type_code,
    commercial_summary_status,
    operational_summary_status,
    is_active,
    service_level_or_type,
    created_at,
    updated_at
  )
  values (
    {sql_text(case_reference_code)},
    'inquiry_active',
    0,
    {sql_text(TEST_CONSOLE_DEFAULT_RENTAL_TYPE_CODE)},
    'unknown',
    'unknown',
    true,
    {sql_text(_normalize_optional_text(label) or 'test_rental')},
    {_sql_timestamptz(created_at)},
    {_sql_timestamptz(created_at)}
  )
  returning
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
),
inserted_event as (
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
  select
    rental_case_id,
    {sql_text(TEST_CONSOLE_CASE_REGISTERED_EVENT)},
    {sql_text(TEST_CONSOLE_SOURCE_TYPE)},
    {sql_text('test_console:create_case')},
    {sql_text(TEST_CONSOLE_OPERATOR_TYPE)},
    {sql_text(TEST_CONSOLE_OPERATOR_REFERENCE)},
    {_sql_timestamptz(created_at)},
    {_sql_timestamptz(created_at)},
    {_sql_json(payload)},
    {sql_text(event_identity_key)},
    {_sql_json({"phase": "8.8a", "surface": "test_console"})}
  from inserted_case
)
select rental_case_id
from inserted_case;
""".strip()
        self.query_runner(insert_sql, expect_json=False)
        select_sql = f"""
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
        rows = self.query_runner(select_sql, expect_json=True)["rows"]
        if not rows:
            raise TestConsoleError(f"RentalCase {case_reference_code} was created but could not be loaded.")
        row = rows[0]
        return OperationReport(
            title="Test Rental Created",
            success=True,
            lines=(
                f"RentalCase: {row['case_reference_code']}",
                f"Lifecycle state: {row['lifecycle_state']}",
                f"Console label: {_normalize_optional_text(label) or row['case_reference_code']}",
            ),
        )

    def load_case_detail(self, rental_case_id: int) -> CaseConsoleSnapshot:
        stage_timings: dict[str, float] = {}
        started = time.perf_counter()
        metadata = self._timed_stage(stage_timings, "metadata", lambda: self._load_test_case_metadata(rental_case_id))
        snapshot = self._timed_stage(stage_timings, "core", lambda: self._load_console_case_snapshot(rental_case_id))
        if snapshot is None:
            raise TestConsoleError(
                f"RentalCase {rental_case_id} was not found.",
                failure_code="RENTAL_CASE_NOT_FOUND",
                status=HTTPStatus.NOT_FOUND,
            )

        timeline_notice: str | None = None
        workflow_event_total_count = len(snapshot.workflow_events)
        if hasattr(self.orchestration_repository, "load_workflow_events_for_console"):
            try:
                workflow_events, workflow_event_total_count = self._timed_stage(
                    stage_timings,
                    "events",
                    lambda: self.orchestration_repository.load_workflow_events_for_console(
                        rental_case_id,
                        limit=self.config.workflow_event_limit,
                    ),
                )
                snapshot = replace(snapshot, workflow_events=workflow_events)
            except TestConsoleError as error:
                timeline_notice = f"WorkflowEvent timeline temporarily unavailable ({error.failure_code})."
        else:
            stage_timings["events"] = 0.0

        evidence_notice: str | None = None
        try:
            bundles = self._timed_stage(stage_timings, "evidence", lambda: self._load_case_evidence_bundles(rental_case_id))
        except TestConsoleError as error:
            bundles = ()
            evidence_notice = f"Observations / evidence temporarily unavailable ({error.failure_code})."
        draft_threads = self._timed_stage(
            stage_timings,
            "simulated_outlook",
            lambda: self._build_simulated_outlook_threads(
                snapshot,
                metadata=metadata,
            ),
        )

        projection_started = time.perf_counter()
        observed_field_candidates = self._build_observed_field_candidates(tuple(bundles))
        latest_communication = self._build_latest_communication_context(tuple(bundles))
        projection_warnings: list[str] = []
        try:
            booking_fee_context = self._timed_stage(
                stage_timings,
                "commercial_authority",
                lambda: self._load_booking_fee_context(
                    snapshot,
                    observed_field_candidates=observed_field_candidates,
                ),
            )
        except TestConsoleError as error:
            booking_fee_context = None
            projection_warnings.append(f"Commercial authority lookup unavailable ({error.failure_code}).")
        detail = CaseConsoleSnapshot(
            metadata=metadata,
            orchestration_snapshot=snapshot,
            evidence_bundles=tuple(bundles),
            test_metadata_lines=summarize_test_metadata(metadata),
            working_proposal=build_working_proposal_projection(
                snapshot,
                metadata=metadata,
                observed_field_candidates=observed_field_candidates,
                latest_communication=latest_communication,
                booking_fee_context=booking_fee_context,
                additional_warnings=tuple(projection_warnings),
            ),
            human_work_preview=build_human_work_preview(snapshot),
            asana_master_task_reference=infer_asana_master_task_reference(snapshot),
            provider_mode_lines=_local_provider_lines(self.config.allow_real_providers),
            workflow_event_total_count=workflow_event_total_count,
            workflow_event_limit=self.config.workflow_event_limit,
            evidence_notice=evidence_notice,
            timeline_notice=timeline_notice,
            simulated_outlook_threads=draft_threads,
        )
        stage_timings["projection"] = time.perf_counter() - projection_started
        stage_timings["total"] = time.perf_counter() - started
        LOGGER.info(
            "test_console_request route=case_detail rental_case_id=%s %s",
            rental_case_id,
            _format_stage_timings(stage_timings),
        )
        return detail

    def inject_raw_test_evidence(
        self,
        *,
        rental_case_id: int,
        source_label: str | None,
        sender: str | None,
        subject: str | None,
        body: str | None,
        received_at: str | None,
        external_test_reference: str | None,
    ) -> OperationReport:
        metadata = self._load_test_case_metadata(rental_case_id)
        payload = {
            "source_label": _normalize_optional_text(source_label),
            "sender": _normalize_optional_text(sender),
            "subject": _normalize_optional_text(subject),
            "body": body or "",
            "received_at": _normalize_optional_text(received_at) or self.now(),
            "external_test_reference": _normalize_optional_text(external_test_reference),
            "case_reference_code": metadata.event_reference,
        }
        dedupe_key = _normalize_optional_text(external_test_reference) or f"test-evidence:{_json_digest(payload)}"
        source_record = self.observation_repository.create_source_record(
            source_record_input=InboundSourceRecordInput(
                source_system_code="email",
                source_record_type="message",
                occurred_at=payload["received_at"],
                dedupe_key=dedupe_key,
                source_hash=f"sha256:{_json_digest(payload)}",
                external_source_id=_normalize_optional_text(external_test_reference),
                conversation_reference=_normalize_optional_text(subject),
                sender_actor_type=OBSERVATION_ASSERTED_BY_CLIENT,
                sender_actor_reference=_normalize_optional_text(sender),
                received_at=payload["received_at"],
                source_location_reference=_normalize_optional_text(source_label),
                evidence_excerpt=(body or "")[:500] or _normalize_optional_text(subject),
            ),
            case_association=CaseAssociationResult(
                status="resolved",
                rental_case_id=rental_case_id,
                association_basis="test_console_explicit_case",
            ),
            created_at=self.now(),
        )
        self._create_console_event(
            rental_case_id=rental_case_id,
            event_type_code=TEST_CONSOLE_RAW_EVIDENCE_EVENT,
            source_reference=f"inbound_source_record:{source_record.inbound_source_record_id}",
            occurred_at=payload["received_at"],
            structured_payload={**payload, "inbound_source_record_id": source_record.inbound_source_record_id},
            actor_reference=TEST_CONSOLE_OPERATOR_REFERENCE,
            actor_type=TEST_CONSOLE_OPERATOR_TYPE,
        )
        return OperationReport(
            title="Raw Test Evidence Recorded",
            success=True,
            lines=(
                f"Source record id: {source_record.inbound_source_record_id}",
                f"Sender: {source_record.sender_actor_reference or 'unknown'}",
                f"Subject: {subject or 'No subject'}",
            ),
        )

    def inject_structured_test_observation(
        self,
        *,
        rental_case_id: int,
        field_code: str,
        observation_type: str,
        claim_kind: str,
        value_text: str,
        source_excerpt: str | None,
        sender_reference: str | None,
        external_test_reference: str | None,
    ) -> OperationReport:
        self._load_test_case_metadata(rental_case_id)
        field_definition = get_field_definition(field_code)
        if field_definition is None:
            raise TestConsoleError(f"Unknown observation field code: {field_code}")
        try:
            candidate_value = self._parse_observation_value(field_definition.value_type_code, value_text)
            dedupe_payload = {
                "field_code": field_code,
                "observation_type": observation_type,
                "claim_kind": claim_kind,
                "candidate_value": candidate_value,
                "source_excerpt": source_excerpt,
                "sender_reference": sender_reference,
                "external_test_reference": external_test_reference,
                "rental_case_id": rental_case_id,
            }
            now_value = self.now()
            request = StructuredObservationIngestionRequest(
                source_record=InboundSourceRecordInput(
                    source_system_code="manual_input",
                    source_record_type="operator_note",
                    occurred_at=now_value,
                    dedupe_key=_normalize_optional_text(external_test_reference) or f"structured:{_json_digest(dedupe_payload)}",
                    source_hash=f"sha256:{_json_digest(dedupe_payload)}",
                    external_source_id=_normalize_optional_text(external_test_reference),
                    sender_actor_type="operator",
                    sender_actor_reference=_normalize_optional_text(sender_reference) or TEST_CONSOLE_OPERATOR_REFERENCE,
                    received_at=now_value,
                    evidence_excerpt=_normalize_optional_text(source_excerpt),
                ),
                case_association=CaseAssociationInput(rental_case_id=rental_case_id),
                observations=(
                    StructuredObservationCandidate(
                        reported_field_code=field_code,
                        reported_domain_code=field_definition.domain_code,
                        observation_type=observation_type,
                        claim_kind=claim_kind,
                        candidate_value_payload=candidate_value,
                        source_evidence_reference=f"test_console:{field_code}",
                        asserted_by_party_type="operator",
                        asserted_by_reference=_normalize_optional_text(sender_reference) or TEST_CONSOLE_OPERATOR_REFERENCE,
                        source_excerpt=_normalize_optional_text(source_excerpt),
                        observed_against_case_revision=self.orchestration_repository.load_case_snapshot(rental_case_id).rental_case.case_revision,
                        extraction_confidence=1.0,
                    ),
                ),
            )
            result = ingest_structured_observations(
                request=request,
                repository=self.observation_repository,
                now=self.now,
            )
        except Phase8ContractError as exc:
            raise TestConsoleError(exc.safe_message) from exc
        first = result.observation_results[0]
        success = not result.failure_codes
        lines = (
            f"Observation id: {first.observation.inbound_observation_id}",
            f"Disposition: {first.effect.disposition_code}",
            f"Status: {first.observation.status}",
        )
        return OperationReport(
            title="Structured Test Observation Injected",
            success=success,
            lines=lines,
            failure_codes=result.failure_codes,
        )

    def create_task_surface_test_action(
        self,
        *,
        rental_case_id: int,
        summary: str,
        reason: str,
        task_kind: str | None = None,
        project_gid_override: str | None = None,
        context_lines: list[str] | None = None,
        external_test_reference: str | None = None,
    ) -> OperationReport:
        if not self.config.runtime.is_staging:
            raise TestConsoleError(
                "Synthetic task-surface action creation is only available when APP_ENV=staging.",
                failure_code="TASK_SURFACE_STAGING_ONLY",
            )
        snapshot = self._require_case_snapshot(rental_case_id)
        normalized_summary = _normalize_optional_text(summary)
        normalized_reason = _normalize_optional_text(reason)
        normalized_task_kind = _normalize_optional_text(task_kind) or "asana_staging_validation"
        normalized_project_gid = _normalize_optional_text(project_gid_override)
        normalized_reference = _normalize_optional_text(external_test_reference)
        if normalized_summary is None:
            raise TestConsoleError("summary is required.", failure_code="TASK_SURFACE_SUMMARY_REQUIRED")
        if normalized_reason is None:
            raise TestConsoleError("reason is required.", failure_code="TASK_SURFACE_REASON_REQUIRED")
        normalized_context_lines = _normalize_task_surface_context_lines(context_lines)
        dedupe_basis = normalized_reference or _json_digest(
            {
                "rental_case_id": rental_case_id,
                "summary": normalized_summary,
                "reason": normalized_reason,
                "task_kind": normalized_task_kind,
                "project_gid_override": normalized_project_gid,
                "context_lines": normalized_context_lines,
            }
        )
        timestamp = self.now()
        structured_payload: dict[str, Any] = {
            "summary": normalized_summary,
            "reason": normalized_reason,
            "task_kind": normalized_task_kind,
        }
        if normalized_project_gid is not None:
            structured_payload["task_surface_project_id"] = normalized_project_gid
        if normalized_context_lines:
            structured_payload["task_surface_context_lines"] = list(normalized_context_lines)
        workflow_action = self.orchestration_repository.create_workflow_action(
            WorkflowAction(
                workflow_action_id=1,
                workflow_action_uuid="workflow-action",
                rental_case_id=rental_case_id,
                action_type=ACTION_TYPE_CREATE_INTERNAL_TASK_ITEM,
                action_category=ACTION_CATEGORY_COORDINATION,
                target_adapter_code="task_surface",
                reason_entity_type="review_item",
                reason_entity_reference=f"operator_task_surface_test:{dedupe_basis}",
                approval_posture=APPROVAL_POSTURE_AUTOMATIC_ALLOWED,
                status=WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
                semantic_subject_hash=f"task_surface_test:{_json_digest({'case': rental_case_id, 'summary': normalized_summary, 'task_kind': normalized_task_kind, 'project_gid': normalized_project_gid})}",
                source_case_revision=snapshot.rental_case.case_revision,
                idempotency_key=f"task_surface_test:{rental_case_id}:{dedupe_basis}",
                structured_payload=structured_payload,
                created_at=timestamp,
                updated_at=timestamp,
            )
        )
        self._create_console_event(
            rental_case_id=rental_case_id,
            event_type_code="task_surface_test_action_created",
            source_reference=f"workflow_action:{workflow_action.workflow_action_id}",
            occurred_at=timestamp,
            structured_payload={
                "workflow_action_id": workflow_action.workflow_action_id,
                "workflow_action_uuid": workflow_action.workflow_action_uuid,
                "source_case_revision": workflow_action.source_case_revision,
                "target_adapter_code": workflow_action.target_adapter_code,
                "task_kind": normalized_task_kind,
                "summary": normalized_summary,
                "project_gid_override": normalized_project_gid,
                "external_test_reference": normalized_reference,
            },
            actor_reference=TEST_CONSOLE_OPERATOR_REFERENCE,
            actor_type=TEST_CONSOLE_OPERATOR_TYPE,
        )
        return OperationReport(
            title="Task-Surface Test Action Created",
            success=True,
            lines=(
                f"Workflow action id: {workflow_action.workflow_action_id}",
                f"Action status: {workflow_action.status}",
                f"Target adapter: {workflow_action.target_adapter_code}",
                f"Project override: {normalized_project_gid or 'default_project'}",
            ),
        )

    def run_reconciliation(self, *, rental_case_id: int) -> OperationReport:
        snapshot = self._require_case_snapshot(rental_case_id)
        self._synthesize_authority_confirmation_projections(snapshot)
        result = reconcile_workflow_orchestration(
            self.orchestration_repository,
            rental_case_id=rental_case_id,
            actor_reference=TEST_CONSOLE_OPERATOR_REFERENCE,
            actor_type=TEST_CONSOLE_OPERATOR_TYPE,
            now=self.now,
        )
        return OperationReport(
            title="Workflow Reconciliation Evaluated",
            success=not result.failure_codes,
            lines=(
                f"Case revision before: {result.case_revision_before}",
                f"Case revision after: {result.case_revision_after}",
                f"Created actions: {len(result.created_action_ids)}",
                f"Created approvals: {len(result.created_approval_ids)}",
                f"Created blockers: {len(result.created_blocker_ids)}",
                f"Evaluated case revision: {snapshot.rental_case.case_revision}",
            ),
            failure_codes=result.failure_codes,
        )

    def _synthesize_authority_confirmation_projections(
        self,
        snapshot: WorkflowOrchestrationCaseSnapshot,
    ) -> None:
        repository = self._phase7_consumption_repository()
        if repository is None:
            return
        try:
            bundles = self._load_case_evidence_bundles(snapshot.rental_case.rental_case_id)
        except TestConsoleError:
            bundles = ()
        observed_field_candidates = self._build_observed_field_candidates(tuple(bundles))
        issues = self._collect_synthetic_authority_issues(
            snapshot,
            observed_field_candidates=observed_field_candidates,
        )
        if not issues:
            return
        created_at = self.now()
        for issue in issues:
            repository.create_reasoning_projection(
                WorkflowReasoningProjection(
                    reasoning_projection_id=1,
                    rental_case_id=snapshot.rental_case.rental_case_id,
                    reasoning_purpose=REASONING_PURPOSE_FEASIBILITY_REVIEW,
                    phase_7_context_contract_version=PHASE_7_CONTEXT_CONTRACT_VERSION,
                    phase_8_workflow_contract_version=PHASE_8_PHASE7_WORKFLOW_CONSUMPTION_CONTRACT_VERSION,
                    source_case_revision=snapshot.rental_case.case_revision,
                    authority_outcome_classification=issue.authority_outcome_classification,
                    degraded_retrieval_summary={
                        "any_degradation": False,
                        "materially_affects_answer_completeness": False,
                        "affected_layers": [],
                        "per_layer_execution_states": {},
                        "fallback_reasons": {},
                        "generator_warnings": [],
                        "semantic_state_code": issue.semantic_state_code,
                    },
                    created_at=created_at,
                    projection_identity_key=self._synthetic_projection_identity_key(snapshot, issue),
                    reasoning_state_code=issue.reasoning_state_code,
                    workflow_posture=(
                        WORKFLOW_REASONING_POSTURE_SAFE_FOR_DETERMINISTIC_USE
                        if issue.semantic_state_code
                        in {WORKFLOW_SEMANTIC_STATE_KNOWN_YES, WORKFLOW_SEMANTIC_STATE_KNOWN_NO}
                        else WORKFLOW_REASONING_POSTURE_REVIEW_REQUIRED
                    ),
                    effective_confidentiality_level=WORKFLOW_CONFIDENTIALITY_LEVEL_INTERNAL,
                    unresolved_authority_codes=(
                        ()
                        if issue.semantic_state_code
                        in {WORKFLOW_SEMANTIC_STATE_KNOWN_YES, WORKFLOW_SEMANTIC_STATE_KNOWN_NO}
                        else (f"{issue.domain_code}|{issue.reasoning_state_code}",)
                    ),
                    grounding_reference_keys=(f"test_console:{issue.issue_code}",),
                )
            )

    def _phase7_consumption_repository(self) -> InMemoryPhase7ConsumptionRepository | SupabasePhase7ConsumptionRepository | None:
        repository = self.orchestration_repository
        if isinstance(repository, SupabaseWorkflowOrchestrationRepository):
            return SupabasePhase7ConsumptionRepository(query_runner=self.query_runner)
        if not isinstance(repository, InMemoryWorkflowOrchestrationRepository):
            return None
        projection_ids_by_identity: dict[tuple[int, str], int] = {}
        max_projection_id = 90_000
        for rental_case_id, projections in repository.reasoning_projections.items():
            for projection in projections:
                max_projection_id = max(max_projection_id, projection.reasoning_projection_id)
                if projection.projection_identity_key:
                    projection_ids_by_identity[(rental_case_id, projection.projection_identity_key)] = (
                        projection.reasoning_projection_id
                    )
        return InMemoryPhase7ConsumptionRepository(
            rental_cases=repository.rental_cases,
            reasoning_projections=repository.reasoning_projections,
            projection_ids_by_identity=projection_ids_by_identity,
            _reasoning_projection_id=max_projection_id,
        )

    def _collect_synthetic_authority_issues(
        self,
        snapshot: WorkflowOrchestrationCaseSnapshot,
        *,
        observed_field_candidates: tuple[ObservedFieldCandidate, ...],
    ) -> tuple[SyntheticAuthorityIssue, ...]:
        observed_by_field = {candidate.field_code: candidate for candidate in observed_field_candidates}
        issues: list[SyntheticAuthorityIssue] = []
        capacity_issue = self._capacity_authority_issue(snapshot, observed_by_field=observed_by_field)
        if capacity_issue is not None:
            issues.append(capacity_issue)
        technical_issue = self._technical_authority_issue(observed_by_field=observed_by_field)
        if technical_issue is not None:
            issues.append(technical_issue)
        facilitator_issue = self._facilitator_authority_issue(observed_by_field=observed_by_field)
        if facilitator_issue is not None:
            issues.append(facilitator_issue)
        return tuple(issues)

    def _capacity_authority_issue(
        self,
        snapshot: WorkflowOrchestrationCaseSnapshot,
        *,
        observed_by_field: dict[str, ObservedFieldCandidate],
    ) -> SyntheticAuthorityIssue | None:
        rental_type_code = snapshot.rental_case.rental_type_code
        guest_count = self._current_guest_count(snapshot)
        if guest_count is None or rental_type_code not in {"studio_space", "entire_venue", "one_to_one_room"}:
            return None
        as_of_date = self.now()[:10]
        if rental_type_code == "entire_venue":
            row = self._first_row(
                f"""
select applicability_status, capacity_evaluation_status, within_capacity
from api.evaluate_capacity(
  null,
  'entire_venue',
  null,
  {guest_count},
  {sql_text(as_of_date)}::date
)
limit 1;
""".strip()
            )
            return self._capacity_issue_from_row(
                issue_code_prefix="capacity_entire_venue",
                status_row=row,
                source_label="entire_venue_capacity",
                source_value=guest_count,
                source_snapshot={
                    "rental_type_code": rental_type_code,
                    "guest_count": guest_count,
                },
            )
        if rental_type_code == "one_to_one_room":
            row = self._first_row(
                f"""
select applicability_status, capacity_evaluation_status, within_capacity
from api.evaluate_capacity(
  'one_to_one_room',
  null,
  null,
  {guest_count},
  {sql_text(as_of_date)}::date
)
limit 1;
""".strip()
            )
            return self._capacity_issue_from_row(
                issue_code_prefix="capacity_one_to_one",
                status_row=row,
                source_label="one_to_one_capacity",
                source_value=guest_count,
                source_snapshot={
                    "rental_type_code": rental_type_code,
                    "guest_count": guest_count,
                },
            )
        configuration_type = self._layout_configuration_type(snapshot, observed_by_field=observed_by_field)
        row = self._first_row(
            f"""
select applicability_status, capacity_evaluation_status, within_capacity
from api.evaluate_capacity(
  'studio_space',
  null,
  {sql_text(configuration_type)},
  {guest_count},
  {sql_text(as_of_date)}::date
)
limit 1;
""".strip()
        )
        capacity_bounds_row = self._first_row(
            """
select min(max_guests) as min_guests, max(max_guests) as max_guests
from public.current_capacity_rules
where scope_code = 'studio_space'
  and max_guests is not null;
""".strip()
        )
        max_capacity = capacity_bounds_row.get("max_guests") if capacity_bounds_row is not None else None
        min_capacity = capacity_bounds_row.get("min_guests") if capacity_bounds_row is not None else None
        if (
            configuration_type is None
            and isinstance(max_capacity, int)
            and guest_count > max_capacity
        ):
            return self._make_synthetic_authority_issue(
                domain_code="capacity",
                issue_code="capacity_studio_over_published_max",
                semantic_state_code=WORKFLOW_SEMANTIC_STATE_KNOWN_NO,
                authority_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                reasoning_state_code=PHASE_7_REASONING_STATE_RESOLVED,
                source_label="studio_capacity_upper_bound",
                source_value=guest_count,
                source_snapshot={
                    "rental_type_code": rental_type_code,
                    "guest_count": guest_count,
                    "published_max_guests": max_capacity,
                    "configuration_type": None,
                    "capacity_evaluation_status": None if row is None else row.get("capacity_evaluation_status"),
                    "applicability_status": None if row is None else row.get("applicability_status"),
                },
            )
        if configuration_type is None and isinstance(min_capacity, int) and guest_count <= min_capacity:
            return self._make_synthetic_authority_issue(
                domain_code="capacity",
                issue_code="capacity_studio_within_all_published_limits",
                semantic_state_code=WORKFLOW_SEMANTIC_STATE_KNOWN_YES,
                authority_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                reasoning_state_code=PHASE_7_REASONING_STATE_RESOLVED,
                source_label="studio_capacity_lower_bound",
                source_value=guest_count,
                source_snapshot={
                    "rental_type_code": rental_type_code,
                    "guest_count": guest_count,
                    "published_min_guests": min_capacity,
                    "published_max_guests": max_capacity,
                    "configuration_type": None,
                    "capacity_evaluation_status": None if row is None else row.get("capacity_evaluation_status"),
                    "applicability_status": None if row is None else row.get("applicability_status"),
                },
            )
        return self._capacity_issue_from_row(
            issue_code_prefix="capacity_studio",
            status_row=row,
            source_label="studio_capacity_configuration" if configuration_type else "studio_capacity",
            source_value=guest_count,
            source_snapshot={
                "rental_type_code": rental_type_code,
                "guest_count": guest_count,
                "configuration_type": configuration_type,
                "published_max_guests": max_capacity,
            },
        )

    def _technical_authority_issue(
        self,
        *,
        observed_by_field: dict[str, ObservedFieldCandidate],
    ) -> SyntheticAuthorityIssue | None:
        candidate = observed_by_field.get("technical_requirements")
        if candidate is None or not isinstance(candidate.value_payload, list):
            return None
        as_of_date = self.now()[:10]
        triggered: list[dict[str, Any]] = []
        strongest_issue: SyntheticAuthorityIssue | None = None
        for value in candidate.value_payload:
            issue = self._technical_issue_for_requirement(
                observed_requirement=str(value),
                as_of_date=as_of_date,
            )
            if issue is None:
                continue
            triggered.append(
                {
                    "observed_requirement": value,
                    "issue_code": issue.issue_code,
                    "semantic_state_code": issue.semantic_state_code,
                    "authority_outcome_classification": issue.authority_outcome_classification,
                    "reasoning_state_code": issue.reasoning_state_code,
                    "source_snapshot": issue.source_snapshot,
                }
            )
            if strongest_issue is None or self._synthetic_issue_priority(issue) > self._synthetic_issue_priority(strongest_issue):
                strongest_issue = issue
        if strongest_issue is None:
            return None
        return replace(
            strongest_issue,
            issue_code="technical_requirements_summary",
            source_label="technical_requirements",
            source_value=list(candidate.value_payload),
            source_snapshot={"triggered_requirements": triggered},
        )

    def _facilitator_authority_issue(
        self,
        *,
        observed_by_field: dict[str, ObservedFieldCandidate],
    ) -> SyntheticAuthorityIssue | None:
        candidate = observed_by_field.get("facilitator_arrangement")
        if candidate is None or not isinstance(candidate.value_payload, str):
            return None
        if candidate.value_payload not in {"wnc_provided", "custom_experience_design"}:
            return None
        row = self._first_row(
            f"""
select arrangement_status, requires_confirmation, requires_availability_confirmation,
       requires_scope_confirmation, requires_technical_confirmation,
       client_commitment_requires_facilitator_confirmation, manual_review_required
from api.get_facilitator_requirements(
  {sql_text(candidate.value_payload)},
  {sql_text(self.now()[:10])}::date
)
limit 1;
""".strip()
        )
        if row is None:
            return None
        manual_review = bool(row.get("manual_review_required")) or row.get("arrangement_status") == "manual_review_required"
        confirmation_required = (
            bool(row.get("requires_confirmation"))
            or bool(row.get("requires_availability_confirmation"))
            or bool(row.get("client_commitment_requires_facilitator_confirmation"))
            or row.get("arrangement_status") == "conditional"
        )
        if not manual_review and not confirmation_required:
            return None
        return self._make_synthetic_authority_issue(
            domain_code="facilitator",
            issue_code=f"facilitator_{candidate.value_payload}_confirmation",
            semantic_state_code=(
                WORKFLOW_SEMANTIC_STATE_UNKNOWN_INTERNAL
                if manual_review
                else WORKFLOW_SEMANTIC_STATE_KNOWN_CONDITIONAL
            ),
            authority_outcome_classification=(
                AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY
                if manual_review
                else AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION
            ),
            reasoning_state_code=(
                PHASE_7_REASONING_STATE_MANUAL_REVIEW_REQUIRED
                if manual_review
                else PHASE_7_REASONING_STATE_REQUIRES_CONFIRMATION
            ),
            source_label="facilitator_arrangement",
            source_value=candidate.value_payload,
            source_snapshot={
                "arrangement_status": row.get("arrangement_status"),
                "requires_confirmation": bool(row.get("requires_confirmation")),
                "requires_availability_confirmation": bool(row.get("requires_availability_confirmation")),
                "requires_scope_confirmation": bool(row.get("requires_scope_confirmation")),
                "requires_technical_confirmation": bool(row.get("requires_technical_confirmation")),
                "manual_review_required": manual_review,
            },
        )

    def _capacity_issue_from_row(
        self,
        *,
        issue_code_prefix: str,
        status_row: dict[str, Any] | None,
        source_label: str,
        source_value: Any,
        source_snapshot: dict[str, Any],
    ) -> SyntheticAuthorityIssue | None:
        if status_row is None:
            return None
        status = status_row.get("capacity_evaluation_status")
        snapshot = {
            **source_snapshot,
            "capacity_evaluation_status": status,
            "applicability_status": status_row.get("applicability_status"),
            "within_capacity": status_row.get("within_capacity"),
        }
        if status == "within_capacity":
            return self._make_synthetic_authority_issue(
                domain_code="capacity",
                issue_code=f"{issue_code_prefix}_within_capacity",
                semantic_state_code=WORKFLOW_SEMANTIC_STATE_KNOWN_YES,
                authority_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                reasoning_state_code=PHASE_7_REASONING_STATE_RESOLVED,
                source_label=source_label,
                source_value=source_value,
                source_snapshot=snapshot,
            )
        if status in {"exceeds_capacity", "not_event_capacity_space"}:
            return self._make_synthetic_authority_issue(
                domain_code="capacity",
                issue_code=f"{issue_code_prefix}_restriction",
                semantic_state_code=WORKFLOW_SEMANTIC_STATE_KNOWN_NO,
                authority_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                reasoning_state_code=PHASE_7_REASONING_STATE_RESOLVED,
                source_label=source_label,
                source_value=source_value,
                source_snapshot=snapshot,
            )
        if status == "requires_confirmation":
            return self._make_synthetic_authority_issue(
                domain_code="capacity",
                issue_code=f"{issue_code_prefix}_confirmation",
                semantic_state_code=WORKFLOW_SEMANTIC_STATE_UNKNOWN_INTERNAL,
                authority_outcome_classification=AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
                reasoning_state_code=PHASE_7_REASONING_STATE_REQUIRES_CONFIRMATION,
                source_label=source_label,
                source_value=source_value,
                source_snapshot=snapshot,
            )
        if status == "insufficient_information":
            return self._make_synthetic_authority_issue(
                domain_code="capacity",
                issue_code=f"{issue_code_prefix}_insufficient_information",
                semantic_state_code=WORKFLOW_SEMANTIC_STATE_UNKNOWN_INTERNAL,
                authority_outcome_classification=AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
                reasoning_state_code=PHASE_7_REASONING_STATE_INSUFFICIENT_INFORMATION,
                source_label=source_label,
                source_value=source_value,
                source_snapshot=snapshot,
            )
        if status == "no_applicable_rule":
            return self._make_synthetic_authority_issue(
                domain_code="capacity",
                issue_code=f"{issue_code_prefix}_no_applicable_rule",
                semantic_state_code=WORKFLOW_SEMANTIC_STATE_UNKNOWN_INTERNAL,
                authority_outcome_classification=AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
                reasoning_state_code=PHASE_7_REASONING_STATE_NO_APPLICABLE_RULE,
                source_label=source_label,
                source_value=source_value,
                source_snapshot=snapshot,
            )
        return None

    def _technical_issue_for_requirement(
        self,
        *,
        observed_requirement: str,
        as_of_date: str,
    ) -> SyntheticAuthorityIssue | None:
        requirement_code = {
            "projection_display": "basic_projection",
            "audio_playback": "ordinary_audio_playback",
            "microphones": "microphone_use",
            "dj_sound_booth": "dj_audio_setup",
            "enhanced_sound_system": "amplified_event_sound",
            "lighting": "standard_venue_lighting",
            "photo_video_production": "filming",
            "livestream_recording": "dedicated_livestreaming",
            "internet_connectivity": "standard_wifi",
            "power_requirements": "high_load_power",
            "other_technical": "custom_technical_setup",
        }.get(observed_requirement)
        if requirement_code is None:
            return self._make_synthetic_authority_issue(
                domain_code="technical",
                issue_code=f"technical_{observed_requirement}_no_applicable_rule",
                semantic_state_code=WORKFLOW_SEMANTIC_STATE_UNKNOWN_INTERNAL,
                authority_outcome_classification=AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
                reasoning_state_code=PHASE_7_REASONING_STATE_NO_APPLICABLE_RULE,
                source_label="technical_requirement",
                source_value=observed_requirement,
                source_snapshot={
                    "observed_requirement": observed_requirement,
                    "requirement_code": None,
                    "applicability_status": "no_applicable_rule",
                },
            )
        row = self._first_row(
            f"""
select applicability_status, support_status, requires_confirmation
from api.evaluate_technical_requirement(
  {sql_text(requirement_code)},
  {sql_text(as_of_date)}::date
)
limit 1;
""".strip()
        )
        snapshot = {
            "observed_requirement": observed_requirement,
            "requirement_code": requirement_code,
        }
        if row is None:
            return self._make_synthetic_authority_issue(
                domain_code="technical",
                issue_code=f"technical_{observed_requirement}_no_result",
                semantic_state_code=WORKFLOW_SEMANTIC_STATE_UNKNOWN_INTERNAL,
                authority_outcome_classification=AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
                reasoning_state_code=PHASE_7_REASONING_STATE_NO_APPLICABLE_RULE,
                source_label="technical_requirement",
                source_value=observed_requirement,
                source_snapshot=snapshot,
            )
        snapshot.update(
            {
                "applicability_status": row.get("applicability_status"),
                "support_status": row.get("support_status"),
                "requires_confirmation": bool(row.get("requires_confirmation")),
            }
        )
        support_status = row.get("support_status")
        applicability_status = row.get("applicability_status")
        if support_status in {"supported", "standard", "available_on_request"}:
            return self._make_synthetic_authority_issue(
                domain_code="technical",
                issue_code=f"technical_{observed_requirement}_supported",
                semantic_state_code=WORKFLOW_SEMANTIC_STATE_KNOWN_YES,
                authority_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                reasoning_state_code=PHASE_7_REASONING_STATE_RESOLVED,
                source_label="technical_requirement",
                source_value=observed_requirement,
                source_snapshot=snapshot,
            )
        if support_status in {"external_supplier_required", "not_available"}:
            return self._make_synthetic_authority_issue(
                domain_code="technical",
                issue_code=f"technical_{observed_requirement}_restriction",
                semantic_state_code=WORKFLOW_SEMANTIC_STATE_KNOWN_NO,
                authority_outcome_classification=AUTHORITY_OUTCOME_DETERMINISTIC_CURRENT,
                reasoning_state_code=PHASE_7_REASONING_STATE_RESOLVED,
                source_label="technical_requirement",
                source_value=observed_requirement,
                source_snapshot=snapshot,
            )
        if support_status == "requires_confirmation" or bool(row.get("requires_confirmation")):
            return self._make_synthetic_authority_issue(
                domain_code="technical",
                issue_code=f"technical_{observed_requirement}_confirmation",
                semantic_state_code=WORKFLOW_SEMANTIC_STATE_KNOWN_CONDITIONAL,
                authority_outcome_classification=AUTHORITY_OUTCOME_REQUIRES_CONFIRMATION,
                reasoning_state_code=PHASE_7_REASONING_STATE_REQUIRES_CONFIRMATION,
                source_label="technical_requirement",
                source_value=observed_requirement,
                source_snapshot=snapshot,
            )
        if applicability_status == "no_applicable_rule" or support_status is None:
            return self._make_synthetic_authority_issue(
                domain_code="technical",
                issue_code=f"technical_{observed_requirement}_no_applicable_rule",
                semantic_state_code=WORKFLOW_SEMANTIC_STATE_UNKNOWN_INTERNAL,
                authority_outcome_classification=AUTHORITY_OUTCOME_INSUFFICIENT_CURRENT_AUTHORITY,
                reasoning_state_code=PHASE_7_REASONING_STATE_NO_APPLICABLE_RULE,
                source_label="technical_requirement",
                source_value=observed_requirement,
                source_snapshot=snapshot,
            )
        return None

    def _make_synthetic_authority_issue(
        self,
        *,
        domain_code: str,
        issue_code: str,
        semantic_state_code: str,
        authority_outcome_classification: str,
        reasoning_state_code: str,
        source_label: str,
        source_value: Any,
        source_snapshot: dict[str, Any],
    ) -> SyntheticAuthorityIssue:
        return SyntheticAuthorityIssue(
            domain_code=domain_code,
            issue_code=issue_code,
            semantic_state_code=semantic_state_code,
            authority_outcome_classification=authority_outcome_classification,
            reasoning_state_code=reasoning_state_code,
            source_label=source_label,
            source_value=source_value,
            source_snapshot=source_snapshot,
        )

    def _synthetic_issue_priority(self, issue: SyntheticAuthorityIssue) -> int:
        return {
            WORKFLOW_SEMANTIC_STATE_KNOWN_NO: 4,
            WORKFLOW_SEMANTIC_STATE_UNKNOWN_INTERNAL: 3,
            WORKFLOW_SEMANTIC_STATE_KNOWN_CONDITIONAL: 2,
            WORKFLOW_SEMANTIC_STATE_KNOWN_YES: 1,
        }.get(issue.semantic_state_code, 0)

    def _synthetic_projection_identity_key(
        self,
        snapshot: WorkflowOrchestrationCaseSnapshot,
        issue: SyntheticAuthorityIssue,
    ) -> str:
        payload = {
            "rental_case_id": snapshot.rental_case.rental_case_id,
            "source_case_revision": snapshot.rental_case.case_revision,
            "reasoning_purpose": REASONING_PURPOSE_FEASIBILITY_REVIEW,
            "domain_code": issue.domain_code,
            "issue_code": issue.issue_code,
            "semantic_state_code": issue.semantic_state_code,
            "authority_outcome_classification": issue.authority_outcome_classification,
            "reasoning_state_code": issue.reasoning_state_code,
            "source_label": issue.source_label,
            "source_value": issue.source_value,
            "source_snapshot": issue.source_snapshot,
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        ).hexdigest()
        return f"test-console-projection:{digest}"

    def _current_guest_count(self, snapshot: WorkflowOrchestrationCaseSnapshot) -> int | None:
        fact = snapshot.find_rental_case_fact("guest_count")
        value = None if fact is None else fact.value_payload
        return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else None

    def _layout_configuration_type(
        self,
        snapshot: WorkflowOrchestrationCaseSnapshot,
        *,
        observed_by_field: dict[str, ObservedFieldCandidate],
    ) -> str | None:
        fact = snapshot.find_rental_case_fact("layout_requirements")
        payload = None if fact is None else fact.value_payload
        if payload is None:
            candidate = observed_by_field.get("layout_requirements")
            payload = None if candidate is None else candidate.value_payload
        if not isinstance(payload, dict):
            return None
        for key in ("configuration_type", "layout_type", "layout", "setup_type"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _first_row(self, sql: str) -> dict[str, Any] | None:
        rows = self.query_runner(sql, expect_json=True)["rows"]
        if not rows:
            return None
        return rows[0]

    def run_inquiry_waiting(self, *, rental_case_id: int) -> OperationReport:
        snapshot = self._require_case_snapshot(rental_case_id)
        started = time.perf_counter()
        result = reconcile_inquiry_waiting(
            self.orchestration_repository,
            rental_case_id=rental_case_id,
            actor_reference=TEST_CONSOLE_OPERATOR_REFERENCE,
            actor_type=TEST_CONSOLE_OPERATOR_TYPE,
            expected_case_revision=snapshot.rental_case.case_revision,
            now=self.now,
            policy=self.config.inquiry_follow_up_policy(),
        )
        desired_follow_up = result.plan.desired_follow_up
        lines = [
            f"Case revision before: {result.case_revision_before}",
            f"Case revision after: {result.case_revision_after}",
            f"Waiting required: {'yes' if result.plan.waiting_required else 'no'}",
            f"Unresolved inquiry questions: {len(result.plan.open_question_ids)}",
            f"Created follow-ups: {len(result.created_follow_up_ids)}",
            f"Updated follow-ups: {len(result.updated_follow_up_ids)}",
            f"Cancelled follow-ups: {len(result.cancelled_follow_up_ids)}",
            f"Created actions: {len(result.created_action_ids)}",
            f"Superseded actions: {len(result.superseded_action_ids)}",
        ]
        if desired_follow_up is not None:
            lines.extend(
                (
                    f"Follow-up sequence: {desired_follow_up.sequence_number}",
                    f"Recommended due at: {desired_follow_up.due_at}",
                    f"Action formation eligible: {'yes' if result.plan.action_formation_eligible else 'no'}",
                )
            )
        lines.append(f"Runtime ms: {(time.perf_counter() - started) * 1000:.1f}")
        return OperationReport(
            title="Inquiry Waiting Evaluated",
            success=not result.failure_codes,
            lines=tuple(lines),
            failure_codes=result.failure_codes,
        )

    def run_inquiry_intake(self, *, rental_case_id: int) -> OperationReport:
        snapshot = self._require_case_snapshot(rental_case_id)
        started = time.perf_counter()
        result = apply_inquiry_intake(
            self.observation_repository,
            rental_case_id=rental_case_id,
            expected_revision=snapshot.rental_case.case_revision,
            actor_reference=TEST_CONSOLE_OPERATOR_REFERENCE,
            actor_type=TEST_CONSOLE_OPERATOR_TYPE,
            now=self.now,
        )
        promoted_fields = [
            humanize_code(evaluation.inquiry_field_code)
            for evaluation in result.plan.field_evaluations
            if evaluation.outcome_code == INQUIRY_INTAKE_OUTCOME_PROMOTED
        ]
        lines = [
            f"Case revision before: {result.case_revision_before}",
            f"Case revision after: {result.case_revision_after}",
            f"Promoted current fields: {', '.join(promoted_fields) if promoted_fields else '0'}",
            f"Open questions created: {len(result.created_open_question_ids)}",
            f"Open questions resolved: {len(result.resolved_open_question_ids)}",
            f"Proposed changes created: {len(result.created_proposed_change_ids)}",
            f"Reschedule requests created: {len(result.created_reschedule_request_ids)}",
            f"Planned semantic effects: {len(result.plan.effects)}",
            f"Runtime ms: {(time.perf_counter() - started) * 1000:.1f}",
        ]
        return OperationReport(
            title="Inquiry Intake Evaluated",
            success=not result.failure_codes,
            lines=tuple(lines),
            failure_codes=result.failure_codes,
        )

    def generate_inquiry_response_draft(self, *, rental_case_id: int, workflow_action_id: int) -> OperationReport:
        snapshot = self._require_case_snapshot(rental_case_id)
        metadata = self._load_test_case_metadata(rental_case_id)
        action = snapshot.find_workflow_action(workflow_action_id)
        if action is None or action.action_type != ACTION_TYPE_REQUEST_CLIENT_INFORMATION:
            raise TestConsoleError(
                f"WorkflowAction {workflow_action_id} is not a client-information email action for RentalCase {rental_case_id}."
            )
        if self._action_is_stale(snapshot, action):
            raise TestConsoleError(
                "The current inquiry action is stale for the latest case revision. Re-run the workflow and regenerate from the current action.",
                failure_code="DRAFT_ACTION_STALE",
            )
        latest_revision = self._load_current_draft_revision_for_conversation(
            rental_case_id,
            conversation_key=self._draft_conversation_key(action),
        )
        target_action = self._ensure_draft_target_action(snapshot, action)
        snapshot = self._require_case_snapshot(rental_case_id)
        target_action = snapshot.find_workflow_action(target_action.workflow_action_id) or target_action
        context = self._build_inquiry_draft_context(
            snapshot,
            action=target_action,
            metadata=metadata,
        )
        content = self.draft_generator.generate(context)
        validate_draft_content(content=content, required_questions=context.open_questions)
        revision = self._create_draft_revision(
            context=context,
            content=content,
            draft_source=(
                INQUIRY_DRAFT_SOURCE_GENERATED
                if latest_revision is None
                else INQUIRY_DRAFT_SOURCE_REGENERATED
            ),
            created_by_reference=TEST_CONSOLE_OPERATOR_REFERENCE,
            supersedes_draft_revision_id=None if latest_revision is None else latest_revision.inquiry_response_draft_revision_id,
        )
        approval = self._replace_draft_approval(
            rental_case_id=rental_case_id,
            workflow_action=target_action,
            revision=revision,
            superseded_revision=latest_revision,
        )
        revision = self._bind_approval_request_to_draft_revision(
            rental_case_id=rental_case_id,
            draft_revision_id=revision.inquiry_response_draft_revision_id,
            approval_request_id=approval.approval_request_id,
            draft_status=INQUIRY_DRAFT_STATUS_NEEDS_APPROVAL,
            updated_at=self.now(),
        )
        self._create_console_event(
            rental_case_id=rental_case_id,
            event_type_code="inquiry_response_draft_generated",
            source_reference=f"inquiry_response_draft:{revision.inquiry_response_draft_revision_id}",
            occurred_at=self.now(),
            structured_payload={
                "workflow_action_id": target_action.workflow_action_id,
                "draft_revision_id": revision.inquiry_response_draft_revision_id,
                "draft_source": revision.draft_source,
                "approval_request_id": approval.approval_request_id,
            },
            actor_reference=TEST_CONSOLE_OPERATOR_REFERENCE,
            actor_type=TEST_CONSOLE_OPERATOR_TYPE,
        )
        return OperationReport(
            title="Inquiry Response Draft Generated",
            success=True,
            lines=(
                f"Draft revision id: {revision.inquiry_response_draft_revision_id}",
                f"Workflow action id: {target_action.workflow_action_id}",
                f"Approval request id: {approval.approval_request_id}",
            ),
        )

    def edit_inquiry_response_draft(
        self,
        *,
        rental_case_id: int,
        draft_revision_id: int,
        subject: str,
        salutation: str,
        intro_text: str,
        closing_text: str,
        signoff_text: str,
        question_prompt_text_by_id: dict[int, str],
    ) -> OperationReport:
        snapshot = self._require_case_snapshot(rental_case_id)
        metadata = self._load_test_case_metadata(rental_case_id)
        prior_revision = self._load_draft_revision_by_id(rental_case_id, draft_revision_id)
        if prior_revision is None:
            raise TestConsoleError(
                f"Inquiry draft revision {draft_revision_id} was not found for RentalCase {rental_case_id}.",
                failure_code="INQUIRY_DRAFT_NOT_FOUND",
                status=HTTPStatus.NOT_FOUND,
            )
        if not prior_revision.is_current:
            raise TestConsoleError(
                "Only the current draft revision can be edited. Please regenerate from the latest current draft.",
                failure_code="INQUIRY_DRAFT_NOT_CURRENT",
            )
        action = snapshot.find_workflow_action(prior_revision.workflow_action_id)
        if action is None:
            raise TestConsoleError(
                f"WorkflowAction {prior_revision.workflow_action_id} was not found for RentalCase {rental_case_id}.",
                failure_code="WORKFLOW_ACTION_NOT_FOUND",
                status=HTTPStatus.NOT_FOUND,
            )
        display_status = self._draft_display_status(snapshot, prior_revision, action=action)
        if display_status == INQUIRY_DRAFT_STATUS_STALE:
            raise TestConsoleError(
                "The current draft is stale for the latest case truth. Regenerate a fresh draft before editing.",
                failure_code="INQUIRY_DRAFT_STALE",
            )
        target_action = self._ensure_draft_target_action(snapshot, action)
        snapshot = self._require_case_snapshot(rental_case_id)
        target_action = snapshot.find_workflow_action(target_action.workflow_action_id) or target_action
        context = self._build_inquiry_draft_context(
            snapshot,
            action=target_action,
            metadata=metadata,
            covered_question_ids=prior_revision.covered_question_ids,
        )
        content = InquiryResponseDraftContent(
            subject=subject,
            salutation=salutation,
            intro_text=intro_text,
            question_lines=tuple(
                InquiryResponseQuestionLine(
                    open_question_id=line.open_question_id,
                    question_type=line.question_type,
                    human_question_text=line.human_question_text,
                    prompt_text=question_prompt_text_by_id.get(line.open_question_id, "").strip(),
                )
                for line in prior_revision.question_lines
            ),
            closing_text=closing_text,
            signoff_text=signoff_text,
        )
        validate_draft_content(content=content, required_questions=context.open_questions)
        revision = self._create_draft_revision(
            context=context,
            content=content,
            draft_source=INQUIRY_DRAFT_SOURCE_HUMAN_EDITED,
            created_by_reference=TEST_CONSOLE_OPERATOR_REFERENCE,
            supersedes_draft_revision_id=prior_revision.inquiry_response_draft_revision_id,
        )
        approval = self._replace_draft_approval(
            rental_case_id=rental_case_id,
            workflow_action=target_action,
            revision=revision,
            superseded_revision=prior_revision,
        )
        revision = self._bind_approval_request_to_draft_revision(
            rental_case_id=rental_case_id,
            draft_revision_id=revision.inquiry_response_draft_revision_id,
            approval_request_id=approval.approval_request_id,
            draft_status=INQUIRY_DRAFT_STATUS_NEEDS_APPROVAL,
            updated_at=self.now(),
        )
        self._create_console_event(
            rental_case_id=rental_case_id,
            event_type_code="inquiry_response_draft_edited",
            source_reference=f"inquiry_response_draft:{revision.inquiry_response_draft_revision_id}",
            occurred_at=self.now(),
            structured_payload={
                "workflow_action_id": target_action.workflow_action_id,
                "draft_revision_id": revision.inquiry_response_draft_revision_id,
                "supersedes_draft_revision_id": prior_revision.inquiry_response_draft_revision_id,
                "approval_request_id": approval.approval_request_id,
            },
            actor_reference=TEST_CONSOLE_OPERATOR_REFERENCE,
            actor_type=TEST_CONSOLE_OPERATOR_TYPE,
        )
        return OperationReport(
            title="Inquiry Response Draft Saved",
            success=True,
            lines=(
                f"Draft revision id: {revision.inquiry_response_draft_revision_id}",
                f"Supersedes revision: {prior_revision.inquiry_response_draft_revision_id}",
                f"Approval request id: {approval.approval_request_id}",
            ),
        )

    def approve_request(self, *, rental_case_id: int, approval_request_id: int) -> OperationReport:
        return self._decide_approval(rental_case_id=rental_case_id, approval_request_id=approval_request_id, decision=ORCHESTRATION_DECISION_APPROVED)

    def reject_request(self, *, rental_case_id: int, approval_request_id: int) -> OperationReport:
        return self._decide_approval(rental_case_id=rental_case_id, approval_request_id=approval_request_id, decision=ORCHESTRATION_DECISION_REJECTED)

    def execute_action(self, *, rental_case_id: int, workflow_action_id: int, execution_mode: str) -> OperationReport:
        snapshot = self._require_case_snapshot(rental_case_id)
        action = snapshot.find_workflow_action(workflow_action_id)
        if action is None:
            raise TestConsoleError(f"WorkflowAction {workflow_action_id} was not found for RentalCase {rental_case_id}.")
        self._guard_inquiry_draft_execution_ready(snapshot, action=action)
        registry = self._build_execution_registry(action=action, execution_mode=execution_mode)
        result = execute_workflow_action(
            self.orchestration_repository,
            WorkflowActionExecutionRequest(
                rental_case_id=rental_case_id,
                workflow_action_id=workflow_action_id,
                actor_reference=TEST_CONSOLE_OPERATOR_REFERENCE,
                actor_type=TEST_CONSOLE_OPERATOR_TYPE,
                started_at=self.now(),
            ),
            adapter_registry=registry,
            now=self.now,
        )
        lines = [
            f"Action status before: {result.action_status_before}",
            f"Action status after: {result.action_status_after}",
        ]
        if result.execution_attempt_id is not None:
            lines.append(f"Execution attempt id: {result.execution_attempt_id}")
        if result.attempt_status is not None:
            lines.append(f"Attempt status: {result.attempt_status}")
        if result.failure_codes:
            lines.extend(self._failure_detail_lines(snapshot, action, result.failure_codes))
        self._record_draft_execution_outcome(
            rental_case_id=rental_case_id,
            workflow_action=action,
            execution_result=result,
        )
        return OperationReport(
            title="Workflow Action Evaluated",
            success=not result.failure_codes,
            lines=tuple(lines),
            failure_codes=result.failure_codes,
        )

    def evaluate_followups(self, *, rental_case_id: int) -> OperationReport:
        result = evaluate_due_follow_ups(
            self.orchestration_repository,
            FollowUpEvaluationRequest(
                rental_case_id=rental_case_id,
                actor_reference=TEST_CONSOLE_OPERATOR_REFERENCE,
                actor_type=TEST_CONSOLE_OPERATOR_TYPE,
                now=self.now(),
            ),
            now=self.now,
        )
        return OperationReport(
            title="Follow-Ups Evaluated",
            success=not result.failure_codes,
            lines=(
                f"Evaluated follow-ups: {len(result.evaluated_follow_up_ids)}",
                f"Due follow-ups: {len(result.due_follow_up_ids)}",
                f"Overdue follow-ups: {len(result.overdue_follow_up_ids)}",
                f"Created actions: {len(result.created_action_ids)}",
            ),
            failure_codes=result.failure_codes,
        )

    def _build_execution_registry(self, *, action: WorkflowAction, execution_mode: str) -> ExecutionAdapterRegistry:
        registry = build_default_fake_execution_registry(now=self.now)
        if execution_mode == "retryable_failure":
            registry.register(
                action.target_adapter_code,
                fake_retryable_failure_adapter(action.target_adapter_code, now=self.now),
            )
        elif execution_mode == "permanent_failure":
            registry.register(
                action.target_adapter_code,
                fake_permanent_failure_adapter(action.target_adapter_code, now=self.now),
            )
        elif execution_mode == "timeout":
            registry.register(
                action.target_adapter_code,
                fake_timeout_adapter(action.target_adapter_code, now=self.now),
            )
        elif execution_mode == "ambiguous":
            registry.register(
                action.target_adapter_code,
                _ambiguous_fake_adapter(action.target_adapter_code, now=self.now),
            )
        elif execution_mode == "real":
            if not self.config.allow_real_providers:
                raise TestConsoleError(
                    f"Real provider execution is disabled. Set {TEST_CONSOLE_ALLOW_REAL_PROVIDERS_ENV}=true to enable it."
                )
            if action.target_adapter_code == "email":
                registry.register(
                    "email",
                    guard_outlook_execution_adapter(
                        build_outlook_execution_adapter_from_env(),
                        runtime=self.config.runtime,
                    ),
                )
            elif action.target_adapter_code == "task_surface":
                registry.register(
                    "task_surface",
                    guard_asana_execution_adapter(
                        build_asana_execution_adapter_from_env(),
                        runtime=self.config.runtime,
                    ),
                )
            else:
                raise TestConsoleError(
                    f"No real-provider mapping is configured for adapter code {action.target_adapter_code!r}."
                )
        return registry

    def _failure_detail_lines(
        self,
        snapshot: WorkflowOrchestrationCaseSnapshot,
        action: WorkflowAction,
        failure_codes: tuple[str, ...],
    ) -> tuple[str, ...]:
        lines = [f"Reason: {code}" for code in failure_codes]
        if "stale_case_revision" in failure_codes or "action_stale_revision" in failure_codes:
            lines.extend(
                (
                    f"Action revision: {action.source_case_revision}",
                    f"Current case revision: {snapshot.rental_case.case_revision}",
                )
            )
        return tuple(lines)

    def _decide_approval(self, *, rental_case_id: int, approval_request_id: int, decision: str) -> OperationReport:
        snapshot = self._require_case_snapshot(rental_case_id)
        linked_draft = self._load_draft_revision_by_approval_request_id(rental_case_id, approval_request_id)
        linked_action = None
        if linked_draft is not None:
            linked_action = snapshot.find_workflow_action(linked_draft.workflow_action_id)
            current_draft = self._load_current_draft_revision_for_conversation(
                rental_case_id,
                conversation_key=linked_draft.conversation_key,
            )
            draft_is_stale = (
                linked_action is not None
                and self._draft_display_status(snapshot, linked_draft, action=linked_action) == INQUIRY_DRAFT_STATUS_STALE
            )
            if (
                decision == ORCHESTRATION_DECISION_APPROVED
                and (
                    linked_action is None
                    or not linked_draft.is_current
                    or current_draft is None
                    or current_draft.inquiry_response_draft_revision_id != linked_draft.inquiry_response_draft_revision_id
                    or draft_is_stale
                )
            ):
                approval = snapshot.find_approval_request(approval_request_id)
                if approval is not None and approval.status == APPROVAL_REQUEST_STATUS_OPEN:
                    self.orchestration_repository.cancel_approval_request(
                        rental_case_id=rental_case_id,
                        approval_request_id=approval_request_id,
                        decided_at=self.now(),
                        decision_notes="Draft became stale before approval.",
                    )
                return OperationReport(
                    title="Approval Blocked",
                    success=False,
                    lines=(
                        f"Approval request id: {approval_request_id}",
                        f"Draft revision id: {linked_draft.inquiry_response_draft_revision_id}",
                        "The linked draft is no longer the current actionable revision and cannot be approved.",
                    ),
                    failure_codes=(
                        ("inquiry_draft_not_current", "inquiry_draft_stale")
                        if draft_is_stale
                        else ("inquiry_draft_not_current",)
                    ),
                )
        result = apply_approval_decision(
            self.orchestration_repository,
            ApprovalDecisionInput(
                rental_case_id=rental_case_id,
                approval_request_id=approval_request_id,
                decision=decision,
                expected_case_revision=snapshot.rental_case.case_revision,
                actor_reference=TEST_CONSOLE_OPERATOR_REFERENCE,
                actor_type=TEST_CONSOLE_OPERATOR_TYPE,
                decided_at=self.now(),
            ),
            now=self.now,
        )
        if linked_draft is not None and not result.failure_codes:
            self._update_draft_revision_status(
                rental_case_id=rental_case_id,
                draft_revision_id=linked_draft.inquiry_response_draft_revision_id,
                draft_status=(
                    INQUIRY_DRAFT_STATUS_APPROVED
                    if decision == ORCHESTRATION_DECISION_APPROVED
                    else INQUIRY_DRAFT_STATUS_REJECTED
                ),
                approved_at=self.now() if decision == ORCHESTRATION_DECISION_APPROVED else None,
                rejected_at=self.now() if decision == ORCHESTRATION_DECISION_REJECTED else None,
                updated_at=self.now(),
            )
            self._create_console_event(
                rental_case_id=rental_case_id,
                event_type_code=(
                    "inquiry_response_draft_approved"
                    if decision == ORCHESTRATION_DECISION_APPROVED
                    else "inquiry_response_draft_rejected"
                ),
                source_reference=f"inquiry_response_draft:{linked_draft.inquiry_response_draft_revision_id}",
                occurred_at=self.now(),
                structured_payload={
                    "approval_request_id": approval_request_id,
                    "draft_revision_id": linked_draft.inquiry_response_draft_revision_id,
                    "workflow_action_id": linked_draft.workflow_action_id,
                },
                actor_reference=TEST_CONSOLE_OPERATOR_REFERENCE,
                actor_type=TEST_CONSOLE_OPERATOR_TYPE,
            )
        return OperationReport(
            title=f"Approval {decision.title()}d",
            success=not result.failure_codes,
            lines=(
                f"Approval status: {result.approval_status}",
                f"Case revision before: {result.case_revision_before}",
                f"Case revision after: {result.case_revision_after}",
            ),
            failure_codes=result.failure_codes,
        )

    def _build_simulated_outlook_threads(
        self,
        snapshot: WorkflowOrchestrationCaseSnapshot,
        *,
        metadata: TestConsoleCaseMetadata,
    ) -> tuple[SimulatedOutlookThread, ...]:
        revisions = self._list_draft_revisions(snapshot.rental_case.rental_case_id)
        revisions_by_conversation: dict[str, list[InquiryResponseDraftRevision]] = {}
        for revision in revisions:
            revisions_by_conversation.setdefault(revision.conversation_key, []).append(revision)
        actions_by_conversation: dict[str, list[WorkflowAction]] = {}
        for action in snapshot.workflow_actions:
            if action.action_type != ACTION_TYPE_REQUEST_CLIENT_INFORMATION:
                continue
            actions_by_conversation.setdefault(self._draft_conversation_key(action), []).append(action)
        threads: list[SimulatedOutlookThread] = []
        conversation_keys = set(revisions_by_conversation) | set(actions_by_conversation)
        for conversation_key in sorted(conversation_keys, reverse=True):
            conversation_revisions = tuple(
                sorted(
                    revisions_by_conversation.get(conversation_key, ()),
                    key=lambda item: item.created_at,
                    reverse=True,
                )
            )
            action_candidates = sorted(
                actions_by_conversation.get(conversation_key, ()),
                key=lambda item: item.updated_at or item.created_at,
                reverse=True,
            )
            current_revision = next((revision for revision in conversation_revisions if revision.is_current), None)
            current_action = self._pick_preferred_conversation_action(action_candidates, current_revision=current_revision)
            display_status = None
            status_note = None
            question_labels: tuple[str, ...] = ()
            recipient_email = None
            open_approval_request_id = None
            if current_revision is not None:
                display_status = self._draft_display_status(snapshot, current_revision, action=current_action)
                question_labels = tuple(line.human_question_text for line in current_revision.question_lines)
                recipient_email = current_revision.recipient_email
                approval = (
                    None
                    if current_revision.approval_request_id is None
                    else snapshot.find_approval_request(current_revision.approval_request_id)
                )
                if approval is not None and approval.status == APPROVAL_REQUEST_STATUS_OPEN:
                    open_approval_request_id = approval.approval_request_id
                if display_status == INQUIRY_DRAFT_STATUS_STALE:
                    status_note = "Current case revision or unresolved question set changed after this draft was created."
            elif current_action is not None:
                question_labels = tuple(question.human_question_text for question in self._questions_for_action(snapshot, current_action))
                recipient_email = self._simulated_recipient_email(snapshot.rental_case.rental_case_id, metadata)
                if self._action_is_stale(snapshot, current_action):
                    status_note = "The current workflow action is stale and needs to be regenerated from the latest case truth."
            thread_label = (
                current_revision.subject
                if current_revision is not None
                else self._mailbox_thread_label(current_action, question_labels)
            )
            threads.append(
                SimulatedOutlookThread(
                    conversation_key=conversation_key,
                    thread_label=thread_label,
                    workflow_action_id=None if current_action is None else current_action.workflow_action_id,
                    workflow_action_status=None if current_action is None else current_action.status,
                    current_display_status=display_status,
                    question_labels=question_labels,
                    recipient_email=recipient_email,
                    open_approval_request_id=open_approval_request_id,
                    current_revision=current_revision,
                    draft_history=conversation_revisions,
                    can_generate=current_action is not None and current_revision is None and not self._action_is_stale(snapshot, current_action),
                    can_regenerate=current_action is not None and current_revision is not None and display_status != INQUIRY_DRAFT_STATUS_STALE,
                    can_edit=current_action is not None and current_revision is not None and display_status != INQUIRY_DRAFT_STATUS_STALE and current_action.status != WORKFLOW_ACTION_STATUS_EXECUTING,
                    can_simulate_send=current_action is not None and current_revision is not None and display_status == INQUIRY_DRAFT_STATUS_APPROVED and current_action.status == WORKFLOW_ACTION_STATUS_READY_TO_EXECUTE,
                    status_note=status_note,
                )
            )
        return tuple(threads)

    def _list_draft_revisions(self, rental_case_id: int) -> tuple[InquiryResponseDraftRevision, ...]:
        sql = f"""
select
  id as inquiry_response_draft_revision_id,
  inquiry_response_draft_revision_uuid::text as inquiry_response_draft_revision_uuid,
  rental_case_id,
  workflow_action_id,
  conversation_key,
  source_case_revision,
  draft_status,
  draft_source,
  is_current,
  approval_request_id,
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
  supersedes_draft_revision_id,
  delivered_at::text as delivered_at,
  delivery_external_reference,
  delivery_failure_code,
  approved_at::text as approved_at,
  rejected_at::text as rejected_at,
  created_by_reference,
  created_at::text as created_at,
  updated_at::text as updated_at
from public.inquiry_response_draft_revisions
where rental_case_id = {rental_case_id}
order by created_at desc, id desc;
""".strip()
        return tuple(
            InquiryResponseDraftRevision.from_row(row)
            for row in self.query_runner(sql, expect_json=True)["rows"]
        )

    def _load_current_draft_revision_for_conversation(
        self,
        rental_case_id: int,
        *,
        conversation_key: str,
    ) -> InquiryResponseDraftRevision | None:
        sql = f"""
select
  id as inquiry_response_draft_revision_id,
  inquiry_response_draft_revision_uuid::text as inquiry_response_draft_revision_uuid,
  rental_case_id,
  workflow_action_id,
  conversation_key,
  source_case_revision,
  draft_status,
  draft_source,
  is_current,
  approval_request_id,
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
  supersedes_draft_revision_id,
  delivered_at::text as delivered_at,
  delivery_external_reference,
  delivery_failure_code,
  approved_at::text as approved_at,
  rejected_at::text as rejected_at,
  created_by_reference,
  created_at::text as created_at,
  updated_at::text as updated_at
from public.inquiry_response_draft_revisions
where rental_case_id = {rental_case_id}
  and conversation_key = {sql_text(conversation_key)}
  and is_current = true
order by created_at desc, id desc
limit 1;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        if not rows:
            return None
        return InquiryResponseDraftRevision.from_row(rows[0])

    def _load_draft_revision_by_id(
        self,
        rental_case_id: int,
        draft_revision_id: int,
    ) -> InquiryResponseDraftRevision | None:
        sql = f"""
select
  id as inquiry_response_draft_revision_id,
  inquiry_response_draft_revision_uuid::text as inquiry_response_draft_revision_uuid,
  rental_case_id,
  workflow_action_id,
  conversation_key,
  source_case_revision,
  draft_status,
  draft_source,
  is_current,
  approval_request_id,
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
  supersedes_draft_revision_id,
  delivered_at::text as delivered_at,
  delivery_external_reference,
  delivery_failure_code,
  approved_at::text as approved_at,
  rejected_at::text as rejected_at,
  created_by_reference,
  created_at::text as created_at,
  updated_at::text as updated_at
from public.inquiry_response_draft_revisions
where rental_case_id = {rental_case_id}
  and id = {draft_revision_id}
limit 1;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        if not rows:
            return None
        return InquiryResponseDraftRevision.from_row(rows[0])

    def _load_draft_revision_by_approval_request_id(
        self,
        rental_case_id: int,
        approval_request_id: int,
    ) -> InquiryResponseDraftRevision | None:
        sql = f"""
select
  id as inquiry_response_draft_revision_id,
  inquiry_response_draft_revision_uuid::text as inquiry_response_draft_revision_uuid,
  rental_case_id,
  workflow_action_id,
  conversation_key,
  source_case_revision,
  draft_status,
  draft_source,
  is_current,
  approval_request_id,
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
  supersedes_draft_revision_id,
  delivered_at::text as delivered_at,
  delivery_external_reference,
  delivery_failure_code,
  approved_at::text as approved_at,
  rejected_at::text as rejected_at,
  created_by_reference,
  created_at::text as created_at,
  updated_at::text as updated_at
from public.inquiry_response_draft_revisions
where rental_case_id = {rental_case_id}
  and approval_request_id = {approval_request_id}
order by created_at desc, id desc
limit 1;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        if not rows:
            return None
        return InquiryResponseDraftRevision.from_row(rows[0])

    def _ensure_draft_target_action(
        self,
        snapshot: WorkflowOrchestrationCaseSnapshot,
        action: WorkflowAction,
    ) -> WorkflowAction:
        conversation_key = self._draft_conversation_key(action)
        if action.status in {WORKFLOW_ACTION_STATUS_PROPOSED, WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL}:
            return action
        if action.status in {WORKFLOW_ACTION_STATUS_EXECUTING, WORKFLOW_ACTION_STATUS_SUCCEEDED}:
            raise TestConsoleError(
                "This action is already executing or completed. Create a new inquiry action from updated workflow state before drafting again.",
                failure_code="WORKFLOW_ACTION_ALREADY_EXECUTED",
            )
        if action.status == WORKFLOW_ACTION_STATUS_SUPERSEDED:
            current = self._find_active_conversation_action(
                snapshot,
                conversation_key,
                excluded_workflow_action_id=action.workflow_action_id,
            )
            if current is not None and current.workflow_action_id != action.workflow_action_id:
                return current
        timestamp = self.now()
        if action.status not in {WORKFLOW_ACTION_STATUS_CANCELLED, WORKFLOW_ACTION_STATUS_FAILED, WORKFLOW_ACTION_STATUS_SUPERSEDED}:
            self.orchestration_repository.supersede_workflow_action(
                rental_case_id=action.rental_case_id,
                workflow_action_id=action.workflow_action_id,
                updated_at=timestamp,
            )
        successor = self.orchestration_repository.create_workflow_action(
            WorkflowAction(
                workflow_action_id=1,
                workflow_action_uuid="workflow-action",
                rental_case_id=action.rental_case_id,
                action_type=action.action_type,
                action_category=action.action_category,
                target_adapter_code=action.target_adapter_code,
                reason_entity_type=action.reason_entity_type,
                reason_entity_id=action.reason_entity_id,
                reason_entity_reference=action.reason_entity_reference,
                approval_posture=action.approval_posture,
                status=WORKFLOW_ACTION_STATUS_AWAITING_APPROVAL,
                semantic_subject_hash=action.semantic_subject_hash,
                source_case_revision=action.source_case_revision,
                idempotency_key=self._successor_action_idempotency_key(snapshot, action, conversation_key),
                structured_payload=action.structured_payload,
                target_scope_key=action.target_scope_key,
                due_at=action.due_at,
                supersedes_workflow_action_id=action.workflow_action_id,
                created_at=timestamp,
                updated_at=timestamp,
            )
        )
        return successor

    def _build_inquiry_draft_context(
        self,
        snapshot: WorkflowOrchestrationCaseSnapshot,
        *,
        action: WorkflowAction,
        metadata: TestConsoleCaseMetadata,
        covered_question_ids: tuple[int, ...] | None = None,
    ) -> InquiryResponseDraftContext:
        questions = self._questions_for_action(snapshot, action)
        if covered_question_ids is not None:
            questions = tuple(
                question
                for question in questions
                if question.open_question_id in set(covered_question_ids)
            )
        if not questions:
            raise TestConsoleError(
                "The workflow action does not have any current unresolved client questions to draft from.",
                failure_code="NO_CURRENT_OPEN_QUESTIONS",
            )
        current_fact_codes = {
            value
            for value in (action.structured_payload.get("required_field_codes") or [])
            if isinstance(value, str) and value
        }
        current_facts = tuple(
            fact
            for fact in snapshot.rental_case_facts
            if fact.established_case_revision <= snapshot.rental_case.case_revision
            and (
                fact.field_code in current_fact_codes
                or fact.field_code in {"active_event_window", "requested_rental_scope", "event_type"}
            )
        )
        return InquiryResponseDraftContext(
            rental_case_id=snapshot.rental_case.rental_case_id,
            workflow_action_id=action.workflow_action_id,
            conversation_key=self._draft_conversation_key(action),
            source_case_revision=action.source_case_revision,
            contact_label=metadata.client_label,
            recipient_email=self._simulated_recipient_email(snapshot.rental_case.rental_case_id, metadata),
            recipient_label=metadata.client_label,
            sender_email="wnc-rentals-simulated@example.test",
            sender_label="WNC Rentals (Simulated)",
            open_questions=questions,
            current_facts=current_facts,
            metadata_summary_lines=tuple(
                value
                for value in (
                    f"Client: {metadata.client_label}" if metadata.client_label else None,
                    f"Event reference: {metadata.event_reference}" if metadata.event_reference else None,
                )
                if value is not None
            ),
            workflow_action=action,
        )

    def _create_draft_revision(
        self,
        *,
        context: InquiryResponseDraftContext,
        content: InquiryResponseDraftContent,
        draft_source: str,
        created_by_reference: str,
        supersedes_draft_revision_id: int | None,
    ) -> InquiryResponseDraftRevision:
        validate_draft_content(content=content, required_questions=context.open_questions)
        body_text = render_draft_body(content)
        context_hash = _json_digest(json.loads(context_hash_payload(context)))
        content_hash = _json_digest(json.loads(content_hash_payload(content)))
        now_value = self.now()
        sql = f"""
with unset_current as (
  update public.inquiry_response_draft_revisions
  set is_current = false,
      updated_at = {_sql_timestamptz(now_value)}
  where rental_case_id = {context.rental_case_id}
    and conversation_key = {sql_text(context.conversation_key)}
    and is_current = true
  returning 1
)
insert into public.inquiry_response_draft_revisions (
  rental_case_id,
  workflow_action_id,
  conversation_key,
  source_case_revision,
  draft_status,
  draft_source,
  is_current,
  approval_request_id,
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
  created_by_reference,
  supersedes_draft_revision_id,
  created_at,
  updated_at
)
select
  {context.rental_case_id},
  {context.workflow_action_id},
  {sql_text(context.conversation_key)},
  {context.source_case_revision},
  {sql_text(INQUIRY_DRAFT_STATUS_DRAFT)},
  {sql_text(draft_source)},
  true,
  null,
  {sql_text(content.subject)},
  {sql_text(content.salutation)},
  {sql_text(content.intro_text)},
  {_sql_json(content.to_payload()["question_lines"])},
  {sql_text(content.closing_text)},
  {sql_text(content.signoff_text)},
  {sql_text(body_text)},
  {_sql_json(context.to_payload())},
  {sql_text(context_hash)},
  {sql_text(content_hash)},
  {sql_text(context.recipient_email)},
  {sql_text(context.recipient_label)},
  {sql_text(context.sender_email)},
  {sql_text(context.sender_label)},
  {sql_text(created_by_reference)},
  {_sql_int(supersedes_draft_revision_id)},
  {_sql_timestamptz(now_value)},
  {_sql_timestamptz(now_value)}
from (
  select count(*) as current_revision_count
  from unset_current
) as dependency
returning
  id as inquiry_response_draft_revision_id,
  inquiry_response_draft_revision_uuid::text as inquiry_response_draft_revision_uuid,
  rental_case_id,
  workflow_action_id,
  conversation_key,
  source_case_revision,
  draft_status,
  draft_source,
  is_current,
  approval_request_id,
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
  supersedes_draft_revision_id,
  delivered_at::text as delivered_at,
  delivery_external_reference,
  delivery_failure_code,
  approved_at::text as approved_at,
  rejected_at::text as rejected_at,
  created_by_reference,
  created_at::text as created_at,
  updated_at::text as updated_at;
""".strip()
        return InquiryResponseDraftRevision.from_row(self.query_runner(sql, expect_json=True)["rows"][0])

    def _replace_draft_approval(
        self,
        *,
        rental_case_id: int,
        workflow_action: WorkflowAction,
        revision: InquiryResponseDraftRevision,
        superseded_revision: InquiryResponseDraftRevision | None,
    ) -> ApprovalRequest:
        snapshot = self._require_case_snapshot(rental_case_id)
        for approval in snapshot.approval_requests:
            if approval.status != APPROVAL_REQUEST_STATUS_OPEN:
                continue
            if approval.target_entity_type != "workflow_action":
                continue
            if approval.target_entity_id != workflow_action.workflow_action_id:
                continue
            self.orchestration_repository.cancel_approval_request(
                rental_case_id=rental_case_id,
                approval_request_id=approval.approval_request_id,
                decided_at=self.now(),
                decision_notes="Superseded by a newer inquiry response draft revision.",
            )
        if superseded_revision is not None and superseded_revision.approval_request_id is not None:
            approval = snapshot.find_approval_request(superseded_revision.approval_request_id)
            if approval is not None and approval.status == APPROVAL_REQUEST_STATUS_OPEN:
                self.orchestration_repository.cancel_approval_request(
                    rental_case_id=rental_case_id,
                    approval_request_id=approval.approval_request_id,
                    decided_at=self.now(),
                    decision_notes="Superseded by a newer inquiry response draft revision.",
                )
        return self.orchestration_repository.create_approval_request(
            ApprovalRequest(
                approval_request_id=1,
                rental_case_id=rental_case_id,
                target_entity_type="workflow_action",
                target_entity_id=workflow_action.workflow_action_id,
                target_entity_reference=f"workflow_action:{workflow_action.workflow_action_id}:draft_revision:{revision.inquiry_response_draft_revision_id}",
                approval_type="client_communication_send",
                reason_text=f"Approve inquiry response draft revision {revision.inquiry_response_draft_revision_id} before simulated send.",
                evidence_reference_keys=(
                    f"workflow_action:{workflow_action.workflow_action_id}",
                    f"inquiry_response_draft:{revision.inquiry_response_draft_revision_id}",
                ),
                required_approver_role="client_communication_review",
                required_approver_reference=(
                    f"semantic:approval:workflow_action:{workflow_action.workflow_action_id}:"
                    f"draft_revision:{revision.inquiry_response_draft_revision_id}"
                ),
                status=APPROVAL_REQUEST_STATUS_OPEN,
                created_at=self.now(),
            )
        )

    def _bind_approval_request_to_draft_revision(
        self,
        *,
        rental_case_id: int,
        draft_revision_id: int,
        approval_request_id: int,
        draft_status: str,
        updated_at: str,
    ) -> InquiryResponseDraftRevision:
        sql = f"""
update public.inquiry_response_draft_revisions
set approval_request_id = {approval_request_id},
    draft_status = {sql_text(draft_status)},
    updated_at = {_sql_timestamptz(updated_at)}
where rental_case_id = {rental_case_id}
  and id = {draft_revision_id}
returning
  id as inquiry_response_draft_revision_id,
  inquiry_response_draft_revision_uuid::text as inquiry_response_draft_revision_uuid,
  rental_case_id,
  workflow_action_id,
  conversation_key,
  source_case_revision,
  draft_status,
  draft_source,
  is_current,
  approval_request_id,
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
  supersedes_draft_revision_id,
  delivered_at::text as delivered_at,
  delivery_external_reference,
  delivery_failure_code,
  approved_at::text as approved_at,
  rejected_at::text as rejected_at,
  created_by_reference,
  created_at::text as created_at,
  updated_at::text as updated_at;
""".strip()
        return InquiryResponseDraftRevision.from_row(self.query_runner(sql, expect_json=True)["rows"][0])

    def _update_draft_revision_status(
        self,
        *,
        rental_case_id: int,
        draft_revision_id: int,
        draft_status: str,
        updated_at: str,
        approved_at: str | None = None,
        rejected_at: str | None = None,
        delivered_at: str | None = None,
        delivery_external_reference: str | None = None,
        delivery_failure_code: str | None = None,
    ) -> InquiryResponseDraftRevision:
        existing = self._load_draft_revision_by_id(rental_case_id, draft_revision_id)
        if existing is None:
            raise TestConsoleError(
                f"Inquiry draft revision {draft_revision_id} was not found for RentalCase {rental_case_id}.",
                failure_code="INQUIRY_DRAFT_NOT_FOUND",
                status=HTTPStatus.NOT_FOUND,
            )
        approved_at = existing.approved_at if approved_at is None else approved_at
        rejected_at = existing.rejected_at if rejected_at is None else rejected_at
        delivered_at = existing.delivered_at if delivered_at is None else delivered_at
        delivery_external_reference = (
            existing.delivery_external_reference
            if delivery_external_reference is None
            else delivery_external_reference
        )
        delivery_failure_code = existing.delivery_failure_code if delivery_failure_code is None else delivery_failure_code
        sql = f"""
update public.inquiry_response_draft_revisions
set draft_status = {sql_text(draft_status)},
    approved_at = {_sql_timestamptz(approved_at)},
    rejected_at = {_sql_timestamptz(rejected_at)},
    delivered_at = {_sql_timestamptz(delivered_at)},
    delivery_external_reference = {sql_text(delivery_external_reference)},
    delivery_failure_code = {sql_text(delivery_failure_code)},
    updated_at = {_sql_timestamptz(updated_at)}
where rental_case_id = {rental_case_id}
  and id = {draft_revision_id}
returning
  id as inquiry_response_draft_revision_id,
  inquiry_response_draft_revision_uuid::text as inquiry_response_draft_revision_uuid,
  rental_case_id,
  workflow_action_id,
  conversation_key,
  source_case_revision,
  draft_status,
  draft_source,
  is_current,
  approval_request_id,
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
  supersedes_draft_revision_id,
  delivered_at::text as delivered_at,
  delivery_external_reference,
  delivery_failure_code,
  approved_at::text as approved_at,
  rejected_at::text as rejected_at,
  created_by_reference,
  created_at::text as created_at,
  updated_at::text as updated_at;
""".strip()
        return InquiryResponseDraftRevision.from_row(self.query_runner(sql, expect_json=True)["rows"][0])

    def _record_draft_execution_outcome(
        self,
        *,
        rental_case_id: int,
        workflow_action: WorkflowAction,
        execution_result,
    ) -> None:
        if workflow_action.action_type != ACTION_TYPE_REQUEST_CLIENT_INFORMATION:
            return
        if execution_result.execution_attempt_id is None:
            return
        revision = self._load_current_draft_revision_for_conversation(
            rental_case_id,
            conversation_key=self._draft_conversation_key(workflow_action),
        )
        if revision is None or revision.workflow_action_id != workflow_action.workflow_action_id:
            return
        execution_attempt = None
        snapshot = self.orchestration_repository.load_case_snapshot(rental_case_id)
        if snapshot is not None:
            candidate_attempt = snapshot.find_execution_attempt(execution_result.execution_attempt_id)
            if candidate_attempt is not None and candidate_attempt.workflow_action_id == workflow_action.workflow_action_id:
                execution_attempt = candidate_attempt
        adapter_failure_code = None if execution_attempt is None else execution_attempt.failure_code
        delivery_external_reference = execution_result.external_reference
        if delivery_external_reference is None and execution_attempt is not None:
            delivery_external_reference = execution_attempt.external_reference
        if execution_result.attempt_status == EXECUTION_ATTEMPT_STATUS_SUCCEEDED and not execution_result.failure_codes:
            status = INQUIRY_DRAFT_STATUS_SIMULATED_SENT
        elif adapter_failure_code == EXECUTION_FAILURE_ADAPTER_OUTCOME_AMBIGUOUS:
            status = INQUIRY_DRAFT_STATUS_SEND_OUTCOME_UNCERTAIN
        else:
            status = INQUIRY_DRAFT_STATUS_SEND_FAILED
        delivery_failure_code = adapter_failure_code
        if delivery_failure_code is None and execution_result.failure_codes:
            delivery_failure_code = execution_result.failure_codes[0]
        self._update_draft_revision_status(
            rental_case_id=rental_case_id,
            draft_revision_id=revision.inquiry_response_draft_revision_id,
            draft_status=status,
            delivered_at=self.now(),
            delivery_external_reference=delivery_external_reference,
            delivery_failure_code=delivery_failure_code,
            updated_at=self.now(),
        )

    def _guard_inquiry_draft_execution_ready(
        self,
        snapshot: WorkflowOrchestrationCaseSnapshot,
        *,
        action: WorkflowAction,
    ) -> None:
        if action.action_type != ACTION_TYPE_REQUEST_CLIENT_INFORMATION:
            return
        current_revision = self._load_current_draft_revision_for_conversation(
            snapshot.rental_case.rental_case_id,
            conversation_key=self._draft_conversation_key(action),
        )
        if current_revision is None:
            raise TestConsoleError(
                "No current inquiry-response draft exists for this workflow action.",
                failure_code="INQUIRY_DRAFT_REQUIRED",
            )
        if current_revision.workflow_action_id != action.workflow_action_id:
            raise TestConsoleError(
                "The current inquiry-response draft belongs to a newer workflow action and this action can no longer execute.",
                failure_code="INQUIRY_DRAFT_ACTION_MISMATCH",
            )
        display_status = self._draft_display_status(snapshot, current_revision, action=action)
        if display_status == INQUIRY_DRAFT_STATUS_STALE:
            raise TestConsoleError(
                "The current inquiry-response draft is stale and cannot be sent.",
                failure_code="INQUIRY_DRAFT_STALE",
            )
        if current_revision.draft_status != INQUIRY_DRAFT_STATUS_APPROVED:
            raise TestConsoleError(
                "Only the current approved inquiry-response draft can be sent.",
                failure_code="INQUIRY_DRAFT_NOT_APPROVED",
            )
        approval = (
            None
            if current_revision.approval_request_id is None
            else snapshot.find_approval_request(current_revision.approval_request_id)
        )
        if approval is None or approval.status != "approved":
            raise TestConsoleError(
                "The current inquiry-response draft does not have an approved exact-revision approval record.",
                failure_code="INQUIRY_DRAFT_APPROVAL_MISSING",
            )

    def _draft_display_status(
        self,
        snapshot: WorkflowOrchestrationCaseSnapshot,
        revision: InquiryResponseDraftRevision,
        *,
        action: WorkflowAction | None,
    ) -> str:
        current_open_question_ids = tuple(
            question.open_question_id
            for question in self._current_inquiry_questions(snapshot)
        )
        return display_status_for_revision(
            revision,
            current_case_revision=snapshot.rental_case.case_revision,
            current_open_question_ids=current_open_question_ids,
            action_status=None if action is None else action.status,
        )

    def _current_inquiry_questions(
        self,
        snapshot: WorkflowOrchestrationCaseSnapshot,
    ) -> tuple[Any, ...]:
        return tuple(
            sorted(
                (
                    question
                    for question in snapshot.open_questions
                    if question.status in {OPEN_QUESTION_STATUS_OPEN, OPEN_QUESTION_STATUS_ANSWERED_PENDING_VALIDATION}
                    and (question.requested_from_role or "").startswith("client")
                ),
                key=lambda question: question.open_question_id,
            )
        )

    def _questions_for_action(
        self,
        snapshot: WorkflowOrchestrationCaseSnapshot,
        action: WorkflowAction,
    ) -> tuple[Any, ...]:
        open_question_ids = {
            value
            for value in action.structured_payload.get("open_question_ids", [])
            if isinstance(value, int) and value > 0
        }
        questions = tuple(
            question
            for question in self._current_inquiry_questions(snapshot)
            if question.open_question_id in open_question_ids
        )
        return tuple(sorted(questions, key=lambda question: question.open_question_id))

    def _action_is_stale(
        self,
        snapshot: WorkflowOrchestrationCaseSnapshot,
        action: WorkflowAction,
    ) -> bool:
        if action.source_case_revision != snapshot.rental_case.case_revision:
            return True
        current_question_ids = tuple(
            question.open_question_id
            for question in self._current_inquiry_questions(snapshot)
        )
        expected_question_ids = tuple(
            sorted(
                value
                for value in action.structured_payload.get("open_question_ids", [])
                if isinstance(value, int) and value > 0
            )
        )
        return current_question_ids != expected_question_ids

    def _pick_preferred_conversation_action(
        self,
        action_candidates: list[WorkflowAction],
        *,
        current_revision: InquiryResponseDraftRevision | None,
    ) -> WorkflowAction | None:
        if current_revision is not None:
            for action in action_candidates:
                if action.workflow_action_id == current_revision.workflow_action_id:
                    return action
        for action in action_candidates:
            if action.status not in {
                WORKFLOW_ACTION_STATUS_SUPERSEDED,
                WORKFLOW_ACTION_STATUS_SUCCEEDED,
            }:
                return action
        return action_candidates[0] if action_candidates else None

    def _draft_conversation_key(self, action: WorkflowAction) -> str:
        base, _, _ = action.idempotency_key.partition(":successor:")
        return base or action.idempotency_key

    def _find_active_conversation_action(
        self,
        snapshot: WorkflowOrchestrationCaseSnapshot,
        conversation_key: str,
        *,
        excluded_workflow_action_id: int | None = None,
    ) -> WorkflowAction | None:
        action_candidates = sorted(
            (
                action
                for action in snapshot.workflow_actions
                if self._draft_conversation_key(action) == conversation_key
                and action.workflow_action_id != excluded_workflow_action_id
            ),
            key=lambda item: item.updated_at or item.created_at,
            reverse=True,
        )
        for action in action_candidates:
            if action.status in {
                WORKFLOW_ACTION_STATUS_SUPERSEDED,
                WORKFLOW_ACTION_STATUS_SUCCEEDED,
                WORKFLOW_ACTION_STATUS_FAILED,
                WORKFLOW_ACTION_STATUS_CANCELLED,
            }:
                continue
            return action
        return None

    def _successor_action_idempotency_key(
        self,
        snapshot: WorkflowOrchestrationCaseSnapshot,
        action: WorkflowAction,
        conversation_key: str,
    ) -> str:
        related_action_count = sum(
            1
            for candidate in snapshot.workflow_actions
            if self._draft_conversation_key(candidate) == conversation_key
        )
        return f"{conversation_key}:successor:{related_action_count + 1}"

    def _mailbox_thread_label(
        self,
        action: WorkflowAction | None,
        question_labels: tuple[str, ...],
    ) -> str:
        if action is None:
            return "Inquiry response draft"
        if question_labels:
            first_label = question_labels[0]
            if len(question_labels) == 1:
                return f"Missing information: {first_label}"
            return f"Missing information: {first_label} (+{len(question_labels) - 1} more)"
        return f"Inquiry response for action {action.workflow_action_id}"

    def _simulated_recipient_email(
        self,
        rental_case_id: int,
        metadata: TestConsoleCaseMetadata,
    ) -> str:
        contact_email = _normalize_optional_text(metadata.contact_email)
        if contact_email and _is_safe_test_email(contact_email):
            return contact_email
        return f"case-{rental_case_id}@example.test"

    def _timed_stage(
        self,
        stage_timings: dict[str, float],
        stage_name: str,
        loader: Callable[[], Any],
    ) -> Any:
        started = time.perf_counter()
        try:
            return loader()
        finally:
            stage_timings[stage_name] = time.perf_counter() - started

    def _load_console_case_snapshot(self, rental_case_id: int) -> WorkflowOrchestrationCaseSnapshot | None:
        if hasattr(self.orchestration_repository, "load_case_core_snapshot_for_console"):
            return self.orchestration_repository.load_case_core_snapshot_for_console(rental_case_id)
        return self.orchestration_repository.load_case_snapshot(rental_case_id)

    def _load_case_evidence_bundles(self, rental_case_id: int) -> tuple[EvidenceBundle, ...]:
        raw_evidence_by_source = self._load_raw_evidence_by_source(rental_case_id)
        source_records = self._list_case_source_records(rental_case_id)

        if hasattr(self.observation_repository, "list_observations_for_case"):
            observations = self.observation_repository.list_observations_for_case(rental_case_id)
            effects = self.observation_repository.list_effects_for_case(rental_case_id)
            observations_by_source: dict[int, list[InboundObservation]] = {}
            for observation in observations:
                observations_by_source.setdefault(observation.inbound_source_record_id, []).append(observation)
            effect_by_observation_id = {
                effect.inbound_observation_id: effect
                for effect in effects
            }
            return tuple(
                EvidenceBundle(
                    source_record=source_record,
                    raw_evidence=raw_evidence_by_source.get(source_record.inbound_source_record_id),
                    observations=tuple(observations_by_source.get(source_record.inbound_source_record_id, ())),
                    effects=tuple(
                        effect_by_observation_id.get(observation.inbound_observation_id)
                        for observation in observations_by_source.get(source_record.inbound_source_record_id, ())
                    ),
                )
                for source_record in source_records
            )

        bundles: list[EvidenceBundle] = []
        for source_record in source_records:
            observations = self.observation_repository.list_observations_for_source(source_record.inbound_source_record_id)
            effects = tuple(
                self.observation_repository.get_effect_for_observation(observation.inbound_observation_id)
                for observation in observations
            )
            bundles.append(
                EvidenceBundle(
                    source_record=source_record,
                    raw_evidence=raw_evidence_by_source.get(source_record.inbound_source_record_id),
                    observations=observations,
                    effects=effects,
                )
            )
        return tuple(bundles)

    def _build_observed_field_candidates(
        self,
        bundles: tuple[EvidenceBundle, ...],
    ) -> tuple[ObservedFieldCandidate, ...]:
        latest_by_field: dict[str, ObservedFieldCandidate] = {}
        for bundle in bundles:
            for observation, effect in zip(bundle.observations, bundle.effects):
                if observation.status == "superseded":
                    continue
                field_definition = get_field_definition(observation.reported_field_code)
                candidate = ObservedFieldCandidate(
                    field_code=observation.reported_field_code,
                    display_label=field_definition.display_label if field_definition is not None else humanize_code(observation.reported_field_code),
                    value_payload=observation.candidate_value_payload,
                    observed_at=observation.created_at,
                    observation_status=observation.status,
                    source_record_type=bundle.source_record.source_record_type,
                    source_actor_reference=bundle.source_record.sender_actor_reference,
                    source_excerpt=observation.source_excerpt or bundle.source_record.evidence_excerpt,
                    disposition_code=effect.disposition_code if effect is not None else None,
                    reason_codes=effect.reason_codes if effect is not None else (),
                    stale_observation=effect.stale_observation if effect is not None else False,
                    linked_entity_reference=self._effect_link_reference(effect),
                )
                prior = latest_by_field.get(candidate.field_code)
                if prior is None or prior.observed_at <= candidate.observed_at:
                    latest_by_field[candidate.field_code] = candidate
        return tuple(sorted(latest_by_field.values(), key=lambda candidate: candidate.field_code))

    def _build_latest_communication_context(
        self,
        bundles: tuple[EvidenceBundle, ...],
    ) -> LatestCommunicationContext | None:
        latest_raw_evidence = next((bundle.raw_evidence for bundle in bundles if bundle.raw_evidence is not None), None)
        if latest_raw_evidence is None:
            return None
        return LatestCommunicationContext(
            occurred_at=latest_raw_evidence.occurred_at,
            source_label=latest_raw_evidence.source_label,
            sender=latest_raw_evidence.sender,
            subject=latest_raw_evidence.subject,
        )

    def _load_booking_fee_context(
        self,
        snapshot: WorkflowOrchestrationCaseSnapshot,
        *,
        observed_field_candidates: tuple[ObservedFieldCandidate, ...],
    ) -> BookingFeeRuleContext | None:
        rental_type_code = snapshot.rental_case.rental_type_code
        duration_input = self._resolve_booking_fee_duration_input(
            snapshot,
            observed_field_candidates=observed_field_candidates,
        )
        if duration_input is None or not rental_type_code:
            return None
        duration_minutes, source_state, source_detail = duration_input
        as_of_date = self.now()[:10]
        sql = f"""
select
  rule_code,
  rental_type_code,
  rental_type_name,
  fee_ex_vat,
  currency_code,
  vat_rate,
  waiver_allowed,
  waiver_authority,
  primary_source_codes,
  governance_source_codes,
  supporting_source_codes
from api.get_booking_fee_rule(
  {sql_text(rental_type_code)},
  {duration_minutes},
  {sql_text(as_of_date)}::date
)
limit 1;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        if not rows:
            return None
        row = rows[0]
        source_codes = tuple(
            code
            for codes in (
                tuple(row.get("primary_source_codes") or ()),
                tuple(row.get("governance_source_codes") or ()),
                tuple(row.get("supporting_source_codes") or ()),
            )
            for code in codes
        )
        return BookingFeeRuleContext(
            rule_code=row["rule_code"],
            rental_type_code=row["rental_type_code"],
            rental_type_name=row["rental_type_name"],
            duration_minutes=duration_minutes,
            fee_ex_vat=float(row["fee_ex_vat"]),
            currency_code=row["currency_code"],
            vat_rate=float(row["vat_rate"]) if row.get("vat_rate") is not None else None,
            waiver_allowed=bool(row["waiver_allowed"]),
            waiver_authority=row.get("waiver_authority"),
            source_state=source_state,
            source_detail=source_detail,
            source_codes=source_codes,
        )

    def _resolve_booking_fee_duration_input(
        self,
        snapshot: WorkflowOrchestrationCaseSnapshot,
        *,
        observed_field_candidates: tuple[ObservedFieldCandidate, ...],
    ) -> tuple[int, str, str] | None:
        current_duration = self._duration_minutes(
            snapshot.rental_case.active_event_start,
            snapshot.rental_case.active_event_end,
        )
        if current_duration is not None:
            return (
                current_duration,
                "current",
                "Derived from the current active event window.",
            )

        active_reschedule = next(
            (
                request
                for request in sorted(snapshot.reschedule_requests, key=lambda item: item.created_at, reverse=True)
                if request.status in {"proposed", "evaluating", "offered", "awaiting_client_confirmation"}
            ),
            None,
        )
        if active_reschedule is not None:
            duration = self._duration_minutes(
                active_reschedule.requested_date_payload.get("active_event_start"),
                active_reschedule.requested_date_payload.get("active_event_end"),
            )
            if duration is not None:
                return (
                    duration,
                    "proposed",
                    f"Derived from reschedule request {active_reschedule.reschedule_request_id}.",
                )

        active_window_candidate = next(
            (
                candidate
                for candidate in observed_field_candidates
                if candidate.field_code == "active_event_window" and isinstance(candidate.value_payload, dict)
            ),
            None,
        )
        if active_window_candidate is None:
            return None
        duration = self._duration_minutes(
            active_window_candidate.value_payload.get("active_event_start"),
            active_window_candidate.value_payload.get("active_event_end"),
        )
        if duration is None:
            return None
        return (
            duration,
            "proposed",
            "Derived from an observed requested event window that is not yet governed current truth.",
        )

    def _duration_minutes(self, start: str | None, end: str | None) -> int | None:
        if not start or not end:
            return None
        try:
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
        except ValueError:
            return None
        duration_seconds = (end_dt - start_dt).total_seconds()
        if duration_seconds <= 0:
            return None
        return int(duration_seconds // 60)

    def _effect_link_reference(self, effect: InboundObservationEffect | None) -> str | None:
        if effect is None:
            return None
        for prefix, linked_id in (
            ("open_question", effect.linked_open_question_id),
            ("requirement", effect.linked_requirement_id),
            ("proposed_change", effect.linked_proposed_change_id),
            ("case_decision", effect.linked_case_decision_id),
            ("reschedule_request", effect.linked_reschedule_request_id),
        ):
            if linked_id is not None:
                return f"{prefix}:{linked_id}"
        return None

    def _load_test_case_metadata(self, rental_case_id: int) -> TestConsoleCaseMetadata:
        sql = f"""
select
  structured_payload,
  actor_reference,
  occurred_at::text as occurred_at
from public.workflow_events
where rental_case_id = {rental_case_id}
  and event_type_code = {sql_text(TEST_CONSOLE_CASE_REGISTERED_EVENT)}
  and source_type = {sql_text(TEST_CONSOLE_SOURCE_TYPE)}
order by id asc
limit 1;
""".strip()
        rows = self.query_runner(sql, expect_json=True)["rows"]
        if not rows:
            raise TestConsoleError(
                f"RentalCase {rental_case_id} is not marked as a test-console case. Test-only controls are blocked.",
                failure_code="TEST_CONSOLE_CASE_REQUIRED",
            )
        payload = rows[0]["structured_payload"] or {}
        return TestConsoleCaseMetadata(
            label=payload.get("label"),
            client_label=payload.get("client_label"),
            contact_email=payload.get("contact_email"),
            event_reference=payload.get("event_reference"),
            created_by=rows[0]["actor_reference"],
            created_at=rows[0]["occurred_at"],
        )

    def _load_raw_evidence_by_source(self, rental_case_id: int) -> dict[int, RawEvidenceRecord]:
        sql = f"""
select
  id as workflow_event_id,
  occurred_at::text as occurred_at,
  structured_payload
from public.workflow_events
where rental_case_id = {rental_case_id}
  and event_type_code = {sql_text(TEST_CONSOLE_RAW_EVIDENCE_EVENT)}
  and source_type = {sql_text(TEST_CONSOLE_SOURCE_TYPE)}
order by occurred_at desc, id desc;
""".strip()
        result: dict[int, RawEvidenceRecord] = {}
        for row in self.query_runner(sql, expect_json=True)["rows"]:
            payload = row["structured_payload"] or {}
            source_id = payload.get("inbound_source_record_id")
            if source_id is None:
                continue
            result[source_id] = RawEvidenceRecord(
                workflow_event_id=row["workflow_event_id"],
                occurred_at=row["occurred_at"],
                source_label=payload.get("source_label"),
                sender=payload.get("sender"),
                subject=payload.get("subject"),
                body=payload.get("body"),
                external_test_reference=payload.get("external_test_reference"),
                inbound_source_record_id=source_id,
            )
        return result

    def _list_case_source_records(self, rental_case_id: int) -> tuple[InboundSourceRecord, ...]:
        if hasattr(self.observation_repository, "list_source_records_for_case"):
            return self.observation_repository.list_source_records_for_case(rental_case_id)
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
        rows = self.query_runner(sql, expect_json=True)["rows"]
        return tuple(InboundSourceRecord(**row) for row in rows)

    def _create_console_event(
        self,
        *,
        rental_case_id: int,
        event_type_code: str,
        source_reference: str,
        occurred_at: str,
        structured_payload: dict[str, Any],
        actor_reference: str,
        actor_type: str,
    ) -> None:
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
  {sql_text(TEST_CONSOLE_SOURCE_TYPE)},
  {sql_text(source_reference)},
  {sql_text(actor_type)},
  {sql_text(actor_reference)},
  {_sql_timestamptz(occurred_at)},
  {_sql_timestamptz(occurred_at)},
  {_sql_json(structured_payload)},
  {sql_text(f'{event_type_code}:{rental_case_id}:{_json_digest(structured_payload)}')},
  {_sql_json({"phase": "8.8a", "surface": "test_console"})}
)
on conflict (rental_case_id, event_identity_key) do nothing;
""".strip()
        self.query_runner(sql, expect_json=False)

    def _require_case_snapshot(self, rental_case_id: int) -> WorkflowOrchestrationCaseSnapshot:
        self._load_test_case_metadata(rental_case_id)
        snapshot = self.orchestration_repository.load_case_snapshot(rental_case_id)
        if snapshot is None:
            raise TestConsoleError(f"RentalCase {rental_case_id} was not found.")
        return snapshot

    def _parse_observation_value(self, value_type_code: str, raw_value: str) -> Any:
        try:
            if value_type_code == OBSERVATION_VALUE_TYPE_INTEGER:
                return int(raw_value.strip())
            if value_type_code == OBSERVATION_VALUE_TYPE_BOOLEAN:
                normalized = raw_value.strip().lower()
                if normalized in {"true", "1", "yes"}:
                    return True
                if normalized in {"false", "0", "no"}:
                    return False
                raise TestConsoleError("Boolean observation values must be true/false.")
            if value_type_code == OBSERVATION_VALUE_TYPE_JSON_OBJECT:
                parsed = json.loads(raw_value)
                if not isinstance(parsed, dict):
                    raise TestConsoleError("JSON-object observation values must parse to an object.")
                return parsed
            if value_type_code == OBSERVATION_VALUE_TYPE_ENUM_ARRAY:
                parsed = json.loads(raw_value)
                if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
                    raise TestConsoleError("Enum-array observation values must be a JSON array of strings.")
                return parsed
            if value_type_code in {OBSERVATION_VALUE_TYPE_ENUM, "text"}:
                return raw_value.strip()
        except json.JSONDecodeError as exc:
            raise TestConsoleError("Observation value JSON is malformed.") from exc
        except ValueError as exc:
            if value_type_code == OBSERVATION_VALUE_TYPE_INTEGER:
                raise TestConsoleError("Integer observation values must parse to a whole number.") from exc
            raise
        raise TestConsoleError(f"Unsupported observation value type: {value_type_code}")


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def _normalize_task_surface_context_lines(value: list[str] | None) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise TestConsoleError(
            "context_lines must be a JSON array of strings.",
            failure_code="TASK_SURFACE_CONTEXT_LINES_INVALID",
        )
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise TestConsoleError(
                "context_lines must be a JSON array of strings.",
                failure_code="TASK_SURFACE_CONTEXT_LINES_INVALID",
            )
        normalized_item = _normalize_optional_text(item)
        if normalized_item is None:
            raise TestConsoleError(
                "context_lines entries must not be blank.",
                failure_code="TASK_SURFACE_CONTEXT_LINES_INVALID",
            )
        normalized.append(normalized_item)
    return tuple(normalized)


def _is_safe_test_email(value: str) -> bool:
    email = value.strip().lower()
    if "@" not in email:
        return False
    domain = email.split("@", 1)[1]
    if domain.endswith(".test") or domain.endswith(".local"):
        return True
    return domain in {"example.com", "example.org", "example.net"}


STRUCTURED_OBSERVATION_TYPE_OPTIONS = (
    OBSERVATION_TYPE_FACT_CANDIDATE,
    OBSERVATION_TYPE_CHANGE_CANDIDATE,
    OBSERVATION_TYPE_REQUEST_CANDIDATE,
    OBSERVATION_TYPE_CONFIRMATION_CANDIDATE,
    OBSERVATION_TYPE_CASE_DECISION_CANDIDATE,
    OBSERVATION_TYPE_REQUIREMENT_EVIDENCE_CANDIDATE,
)

STRUCTURED_OBSERVATION_CLAIM_KIND_OPTIONS = (
    OBSERVATION_CLAIM_KIND_NEW_INFORMATION,
    OBSERVATION_CLAIM_KIND_CHANGE_REQUEST,
    OBSERVATION_CLAIM_KIND_EXCEPTION_REQUEST,
    OBSERVATION_CLAIM_KIND_CONFIRMATION,
    OBSERVATION_CLAIM_KIND_REQUIREMENT_EVIDENCE,
    OBSERVATION_CLAIM_KIND_QUESTION_ANSWER,
)
