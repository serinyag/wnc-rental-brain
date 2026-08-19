from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable

from tools.phase_05_chunking.generate_pilot import run_supabase_query, sql_text

from .contracts import (
    AUTHORITY_TIER_CURRENT_DETERMINISTIC,
    EXECUTION_STATE_FAILED,
    EXECUTION_STATE_NOT_REQUESTED,
    EXECUTION_STATE_NO_RESULTS,
    EXECUTION_STATE_SUCCESS,
    LAYER_ID_PHASE_4,
    PHASE_4_DOMAIN_BOOKING_FEE,
    PHASE_4_DOMAIN_CANCELLATION,
    PHASE_4_DOMAIN_CAPACITY,
    PHASE_4_DOMAIN_CATERING_SUPPLIER,
    PHASE_4_DOMAIN_CODES,
    PHASE_4_DOMAIN_EXPEDITED_SURCHARGE,
    PHASE_4_DOMAIN_FACILITATOR_REQUIREMENTS,
    PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS,
    PHASE_4_DOMAIN_PAYMENT,
    PHASE_4_DOMAIN_SERVICE_RULES,
    PHASE_4_DOMAIN_SPACE_ACCESS,
    PHASE_4_DOMAIN_TECHNICAL_CAPABILITY,
    PHASE_4_DOMAIN_TECHNICAL_INVENTORY,
    ProvenanceEnvelope,
    ExactIdentity,
    LayerExecutionRecord,
    NormalizedResultEnvelope,
    QueryContext,
    QueryPlan,
    REASONING_STATE_INSUFFICIENT_INFORMATION,
    REASONING_STATE_MANUAL_REVIEW_REQUIRED,
    REASONING_STATE_NO_APPLICABLE_RULE,
    REASONING_STATE_REQUIRES_CONFIRMATION,
    REASONING_STATE_RESOLVED,
    SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
    StableIdentity,
    authority_priority_for_tier,
    phase4_default_sensitivity,
)
from .validation import Phase7ContractError, ensure_non_empty_text


QueryRunner = Callable[[str], list[dict[str, Any]]]
ProvenanceRow = dict[str, Any]

CURRENT_DATE_SQL = "current_date"
PAYMENT_STAGES_REQUIRING_LEAD_TIME = frozenset({"confirmation_deadline", "upfront_option"})
RULE_CODE_FIELDS = (
    "rule_code",
    "equipment_code",
    "requirement_code",
    "capability_code",
    "service_level",
    "service_type",
    "catering_arrangement",
    "requirement_type",
    "scope_code",
    "rental_type_code",
    "venue_space_code",
    "source_item_code",
)


class Phase4AdapterError(RuntimeError):
    def __init__(self, *, domain: str, error_category: str, safe_message: str) -> None:
        self.domain = domain
        self.error_category = error_category
        self.safe_message = safe_message
        super().__init__(safe_message)


@dataclass(frozen=True)
class Phase4AdapterConfiguration:
    enrich_provenance: bool = True


@dataclass(frozen=True)
class Phase4Handler:
    domain_code: str
    rpc_names: tuple[str, ...]
    handler: Callable[[dict[str, Any], QueryRunner], tuple[tuple[dict[str, Any], ...], tuple[str, ...]]]


@dataclass(frozen=True)
class DomainFailure:
    domain_code: str
    error_category: str
    safe_message: str


def execute_phase4_plan(
    query_plan: QueryPlan,
    query_context: QueryContext | None = None,
    runtime_configuration: Phase4AdapterConfiguration | None = None,
    query_runner: QueryRunner | None = None,
) -> LayerExecutionRecord:
    if query_context is not None and query_context.query_text != query_plan.query_text:
        raise Phase7ContractError(
            error_category="invalid_value",
            safe_message="query_context.query_text must match query_plan.query_text.",
        )

    phase4_intent = query_plan.phase_4
    if phase4_intent is None or not phase4_intent.required:
        return LayerExecutionRecord(
            layer_id=LAYER_ID_PHASE_4,
            requested=False,
            execution_state=EXECUTION_STATE_NOT_REQUESTED,
            reasoning_state=None,
            fallback_reason=None,
            error_category=None,
            safe_error_message=None,
            result_count=0,
            normalized_items=(),
        )

    config = runtime_configuration or Phase4AdapterConfiguration()
    runner = query_runner or _default_query_runner

    normalized_items: list[NormalizedResultEnvelope] = []
    failures: list[DomainFailure] = []

    for domain_code in phase4_intent.domains:
        handler = PHASE4_ADAPTER_REGISTRY[domain_code]
        domain_inputs = dict(phase4_intent.domain_inputs.get(domain_code, {}))
        try:
            rows, rpc_names = handler.handler(domain_inputs, runner)
            if not rows:
                rows = (
                    _synthetic_row(
                        domain_code=domain_code,
                        rpc_name=rpc_names[-1] if rpc_names else handler.rpc_names[0],
                        reasoning_state=REASONING_STATE_NO_APPLICABLE_RULE,
                        domain_inputs=domain_inputs,
                        summary_text=f"No applicable {domain_code} result matched the supplied structured inputs.",
                    ),
                )
            normalized_items.extend(
                _normalize_rows(
                    domain_code=domain_code,
                    rpc_names=rpc_names,
                    rows=rows,
                )
            )
        except Phase4AdapterError as exc:
            failures.append(
                DomainFailure(
                    domain_code=exc.domain,
                    error_category=exc.error_category,
                    safe_message=exc.safe_message,
                )
            )
        except Exception as exc:  # pragma: no cover - exercised through failure mocks
            failures.append(_coerce_runtime_failure(domain_code=domain_code, exc=exc))

    if config.enrich_provenance and normalized_items:
        normalized_items = _enrich_provenance(normalized_items, runner)

    if normalized_items:
        error_category = None
        safe_error_message = None
        if failures:
            failed_domains = ", ".join(sorted(failure.domain_code for failure in failures))
            error_category = "phase4_partial_domain_failure"
            safe_error_message = f"Phase 4 adapter failed for domain(s): {failed_domains}."
        return LayerExecutionRecord(
            layer_id=LAYER_ID_PHASE_4,
            requested=True,
            execution_state=EXECUTION_STATE_SUCCESS,
            reasoning_state=_aggregate_reasoning_state(normalized_items),
            fallback_reason=None,
            error_category=error_category,
            safe_error_message=safe_error_message,
            result_count=len(normalized_items),
            normalized_items=tuple(normalized_items),
        )

    if failures:
        failed_domains = ", ".join(sorted(failure.domain_code for failure in failures))
        return LayerExecutionRecord(
            layer_id=LAYER_ID_PHASE_4,
            requested=True,
            execution_state=EXECUTION_STATE_FAILED,
            reasoning_state=None,
            fallback_reason=None,
            error_category="phase4_execution_failed",
            safe_error_message=f"Phase 4 adapter failed for domain(s): {failed_domains}.",
            result_count=0,
            normalized_items=(),
        )

    return LayerExecutionRecord(
        layer_id=LAYER_ID_PHASE_4,
        requested=True,
        execution_state=EXECUTION_STATE_NO_RESULTS,
        reasoning_state=None,
        fallback_reason=None,
        error_category=None,
        safe_error_message=None,
        result_count=0,
        normalized_items=(),
    )


def _default_query_runner(sql: str) -> list[dict[str, Any]]:
    return run_supabase_query(sql, expect_json=True)["rows"]


def _coerce_runtime_failure(*, domain_code: str, exc: Exception) -> DomainFailure:
    if isinstance(exc, subprocess.CalledProcessError):
        return DomainFailure(
            domain_code=domain_code,
            error_category="phase4_rpc_execution_failed",
            safe_message=f"Phase 4 RPC execution failed for domain {domain_code}.",
        )
    return DomainFailure(
        domain_code=domain_code,
        error_category="phase4_adapter_execution_failed",
        safe_message=f"Phase 4 adapter execution failed for domain {domain_code}.",
    )


def _normalize_rows(
    *,
    domain_code: str,
    rpc_names: tuple[str, ...],
    rows: tuple[dict[str, Any], ...],
) -> list[NormalizedResultEnvelope]:
    normalized_items: list[NormalizedResultEnvelope] = []
    for index, row in enumerate(rows, start=1):
        rpc_name = row.get("_rpc_name") or (rpc_names[-1] if rpc_names else "api.unknown")
        reasoning_state = _normalize_reasoning_state(row)
        stable_identity = _build_stable_identity(domain_code=domain_code, rpc_name=rpc_name, row=row)
        exact_identity = _build_exact_identity(domain_code=domain_code, rpc_name=rpc_name, row=row)
        provenance = _build_provenance(row)
        row_payload = dict(row)
        row_payload.pop("_summary_text", None)
        row_payload.pop("_reasoning_state", None)
        row_payload["phase_4_domain"] = domain_code
        row_payload["rpc_name"] = rpc_name
        row_payload["source_layer_role"] = SOURCE_LAYER_ROLE_DETERMINISTIC_RULE
        row_payload["authority_tier_code"] = AUTHORITY_TIER_CURRENT_DETERMINISTIC
        row_payload["authority_priority"] = authority_priority_for_tier(AUTHORITY_TIER_CURRENT_DETERMINISTIC)

        item_id = _build_item_id(
            domain_code=domain_code,
            row=row,
            rpc_name=rpc_name,
            index=index,
            reasoning_state=reasoning_state,
        )
        normalized_items.append(
            NormalizedResultEnvelope(
                item_id=item_id,
                source_layer_role=SOURCE_LAYER_ROLE_DETERMINISTIC_RULE,
                authority_tier_code=AUTHORITY_TIER_CURRENT_DETERMINISTIC,
                authority_priority=authority_priority_for_tier(AUTHORITY_TIER_CURRENT_DETERMINISTIC),
                stable_identity=stable_identity,
                exact_identity=exact_identity,
                content_kind="phase4_rule_result",
                execution_state=EXECUTION_STATE_SUCCESS,
                reasoning_state=reasoning_state,
                summary_text=_summary_text(domain_code=domain_code, row=row, reasoning_state=reasoning_state),
                provenance=provenance,
                sensitivity=phase4_default_sensitivity(),
                retrieval=None,
                layer_payload=row_payload,
            )
        )
    return normalized_items


def _summary_text(*, domain_code: str, row: dict[str, Any], reasoning_state: str) -> str | None:
    explanation = row.get("plain_language_explanation") or row.get("conditions_summary") or row.get("_summary_text")
    if isinstance(explanation, str) and explanation.strip():
        return explanation.strip()
    if reasoning_state == REASONING_STATE_NO_APPLICABLE_RULE:
        return f"No applicable {domain_code} result matched the supplied structured inputs."
    if reasoning_state == REASONING_STATE_INSUFFICIENT_INFORMATION:
        return f"Insufficient structured information was supplied to resolve {domain_code}."
    return None


def _build_item_id(
    *,
    domain_code: str,
    row: dict[str, Any],
    rpc_name: str,
    index: int,
    reasoning_state: str,
) -> str:
    if row.get("rule_code"):
        return f"phase4:{domain_code}:{row['rule_code']}:{index}"
    if row.get("equipment_code"):
        return f"phase4:{domain_code}:{row['equipment_code']}:{index}"
    return f"phase4:{domain_code}:{rpc_name.rsplit('.', 1)[-1]}:{reasoning_state}:{index}"


def _build_stable_identity(*, domain_code: str, rpc_name: str, row: dict[str, Any]) -> StableIdentity:
    primary_code = _first_text(row, "rule_code", "equipment_code", "requirement_code", "capability_code", "service_level")
    secondary_code = _first_text(row, "source_item_code", "service_type", "payment_stage", "venue_space_code", "rental_type_code")
    native_identity_payload = {
        "phase_4_domain": domain_code,
        "rpc_name": rpc_name,
    }
    for field_name in RULE_CODE_FIELDS:
        value = row.get(field_name)
        if value is not None:
            native_identity_payload[field_name] = value
    return StableIdentity(
        primary_code=primary_code,
        secondary_code=secondary_code,
        native_identity_payload=native_identity_payload,
    )


def _build_exact_identity(*, domain_code: str, rpc_name: str, row: dict[str, Any]) -> ExactIdentity:
    secondary_id = row.get("id") or row.get("equipment_id")
    native_identity_payload = {
        "phase_4_domain": domain_code,
        "rpc_name": rpc_name,
        "status": row.get("status"),
        "effective_from": row.get("effective_from"),
        "effective_until": row.get("effective_until"),
    }
    if row.get("source_id") is not None:
        native_identity_payload["source_id"] = row.get("source_id")
    return ExactIdentity(
        primary_id=row.get("rule_id"),
        version_number=row.get("rule_version"),
        secondary_id=secondary_id,
        native_identity_payload={key: value for key, value in native_identity_payload.items() if value is not None},
    )


def _build_provenance(row: dict[str, Any]) -> ProvenanceEnvelope:
    direct_primary = _normalize_source_codes(row.get("primary_source_codes"))
    direct_governance = _normalize_source_codes(row.get("governance_source_codes"))
    direct_supporting = _normalize_source_codes(row.get("supporting_source_codes"))
    direct_single_code = _normalize_source_codes(row.get("source_code"))
    source_codes = _unique_strings((*direct_primary, *direct_governance, *direct_supporting, *direct_single_code))

    primary_locator = _clean_text(row.get("source_locator"))
    if primary_locator is None and direct_single_code:
        primary_locator = f"source_code:{direct_single_code[0]}"
    source_identifiers: dict[str, Any] = {
        "primary_source_codes": list(direct_primary),
        "governance_source_codes": list(direct_governance),
        "supporting_source_codes": list(direct_supporting),
    }
    if row.get("source_id") is not None:
        source_identifiers["source_id"] = row["source_id"]
    if row.get("source_title") is not None:
        source_identifiers["source_title"] = row["source_title"]

    native_payload = {
        "direct_primary_source_codes": list(direct_primary),
        "direct_governance_source_codes": list(direct_governance),
        "direct_supporting_source_codes": list(direct_supporting),
    }
    if direct_single_code:
        native_payload["direct_source_code"] = direct_single_code[0]
    return ProvenanceEnvelope(
        source_codes=tuple(source_codes),
        source_identifiers=source_identifiers,
        primary_source_locator=primary_locator,
        additional_locators=(),
        source_link_count=len(source_codes) if source_codes else None,
        native_provenance_payload=native_payload,
    )


def _normalize_reasoning_state(row: dict[str, Any]) -> str:
    explicit = row.get("_reasoning_state")
    if explicit is not None:
        return explicit

    if row.get("manual_review_required") is True or row.get("requires_manual_review") is True:
        return REASONING_STATE_MANUAL_REVIEW_REQUIRED

    statuses = tuple(
        value
        for value in (
            row.get("applicability_status"),
            row.get("capacity_evaluation_status"),
            row.get("quantity_evaluation_status"),
            row.get("support_status"),
            row.get("availability_status"),
            row.get("arrangement_status"),
            row.get("access_status"),
            row.get("outcome"),
        )
        if isinstance(value, str) and value.strip()
    )

    if "manual_review_required" in statuses:
        return REASONING_STATE_MANUAL_REVIEW_REQUIRED
    if "insufficient_information" in statuses:
        return REASONING_STATE_INSUFFICIENT_INFORMATION
    if row.get("requires_confirmation") is True or "requires_confirmation" in statuses:
        return REASONING_STATE_REQUIRES_CONFIRMATION
    if "no_applicable_rule" in statuses or "no_applicable_equipment" in statuses:
        return REASONING_STATE_NO_APPLICABLE_RULE
    return REASONING_STATE_RESOLVED


def _aggregate_reasoning_state(items: list[NormalizedResultEnvelope]) -> str | None:
    if not items:
        return None
    states = [item.reasoning_state for item in items if item.reasoning_state is not None]
    if not states:
        return None
    if all(state == REASONING_STATE_RESOLVED for state in states):
        return REASONING_STATE_RESOLVED
    if REASONING_STATE_MANUAL_REVIEW_REQUIRED in states:
        return REASONING_STATE_MANUAL_REVIEW_REQUIRED
    if REASONING_STATE_REQUIRES_CONFIRMATION in states:
        return REASONING_STATE_REQUIRES_CONFIRMATION
    if len(set(states)) == 1:
        return states[0]
    return None


def _enrich_provenance(
    items: list[NormalizedResultEnvelope],
    runner: QueryRunner,
) -> list[NormalizedResultEnvelope]:
    rule_ids = sorted({item.exact_identity.primary_id for item in items if item.exact_identity.primary_id is not None})
    if not rule_ids:
        return items

    sql = f"""
select
  rsl.rule_id,
  rsl.relation_type,
  sr.id as source_registry_id,
  sr.source_code,
  sr.title,
  sr.source_type,
  sr.authority_level,
  sr.lifecycle_status,
  sr.original_filename,
  sr.relative_source_path,
  sr.effective_date,
  sr.notes
from public.rule_source_links rsl
join public.source_registry sr
  on sr.id = rsl.source_id
where rsl.rule_id in ({", ".join(str(rule_id) for rule_id in rule_ids)})
order by rsl.rule_id, rsl.relation_type, sr.source_code;
""".strip()
    rows = runner(sql)
    rows_by_rule_id: dict[int, list[ProvenanceRow]] = {}
    for row in rows:
        rows_by_rule_id.setdefault(row["rule_id"], []).append(row)

    enriched_items: list[NormalizedResultEnvelope] = []
    for item in items:
        rule_id = item.exact_identity.primary_id
        if rule_id is None:
            enriched_items.append(item)
            continue
        provenance_rows = rows_by_rule_id.get(rule_id, [])
        if not provenance_rows:
            enriched_items.append(item)
            continue

        ordered_rows = sorted(provenance_rows, key=_relation_sort_key)
        locators = _unique_strings(
            tuple(
                _source_locator_from_registry_row(row)
                for row in ordered_rows
                if _source_locator_from_registry_row(row) is not None
            )
        )
        primary_locator = item.provenance.primary_source_locator or (locators[0] if locators else None)
        additional_locators = tuple(locator for locator in locators if locator != primary_locator)
        source_codes = _unique_strings(item.provenance.source_codes + tuple(row["source_code"] for row in ordered_rows))
        source_identifiers = dict(item.provenance.source_identifiers)
        source_identifiers["source_registry_ids"] = [row["source_registry_id"] for row in ordered_rows]
        source_identifiers["deep_source_links"] = len(ordered_rows)

        native_payload = dict(item.provenance.native_provenance_payload)
        native_payload["deep_sources"] = [
            {
                "relation_type": row["relation_type"],
                "source_registry_id": row["source_registry_id"],
                "source_code": row["source_code"],
                "title": row["title"],
                "source_type": row["source_type"],
                "authority_level": row["authority_level"],
                "lifecycle_status": row["lifecycle_status"],
                "original_filename": row["original_filename"],
                "relative_source_path": row["relative_source_path"],
                "effective_date": row["effective_date"],
                "notes": row["notes"],
                "source_locator": _source_locator_from_registry_row(row),
            }
            for row in ordered_rows
        ]

        enriched_items.append(
            NormalizedResultEnvelope(
                item_id=item.item_id,
                source_layer_role=item.source_layer_role,
                authority_tier_code=item.authority_tier_code,
                authority_priority=item.authority_priority,
                stable_identity=item.stable_identity,
                exact_identity=item.exact_identity,
                content_kind=item.content_kind,
                execution_state=item.execution_state,
                reasoning_state=item.reasoning_state,
                summary_text=item.summary_text,
                provenance=ProvenanceEnvelope(
                    source_codes=tuple(source_codes),
                    source_identifiers=source_identifiers,
                    primary_source_locator=primary_locator,
                    additional_locators=additional_locators,
                    source_link_count=len(ordered_rows),
                    native_provenance_payload=native_payload,
                ),
                sensitivity=item.sensitivity,
                retrieval=item.retrieval,
                layer_payload=item.layer_payload,
            )
        )
    return enriched_items


def _source_locator_from_registry_row(row: ProvenanceRow) -> str | None:
    return _clean_text(row.get("relative_source_path")) or _clean_text(row.get("original_filename"))


def _relation_sort_key(row: ProvenanceRow) -> tuple[int, str]:
    relation_type = row.get("relation_type")
    priority = {
        "primary": 0,
        "governance": 1,
        "supporting": 2,
    }.get(relation_type, 3)
    return priority, str(relation_type)


def _synthetic_row(
    *,
    domain_code: str,
    rpc_name: str,
    reasoning_state: str,
    domain_inputs: dict[str, Any],
    summary_text: str,
) -> dict[str, Any]:
    return {
        "_rpc_name": rpc_name,
        "_reasoning_state": reasoning_state,
        "_summary_text": summary_text,
        "phase_4_domain": domain_code,
        "applicability_status": reasoning_state,
        "primary_source_codes": [],
        "governance_source_codes": [],
        "supporting_source_codes": [],
        "input_snapshot": domain_inputs,
    }


def _require_non_empty_text(value: Any, *, field_name: str, domain_code: str) -> str:
    if value is None:
        raise Phase4AdapterError(
            domain=domain_code,
            error_category="insufficient_information",
            safe_message=f"Phase 4 domain {domain_code} requires {field_name}.",
        )
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    ensure_non_empty_text(field_name, value)
    return value


def _coerce_int(value: Any, *, field_name: str, domain_code: str) -> int:
    if value is None or value == "":
        raise Phase4AdapterError(
            domain=domain_code,
            error_category="insufficient_information",
            safe_message=f"Phase 4 domain {domain_code} requires {field_name}.",
        )
    if isinstance(value, bool):
        raise Phase4AdapterError(
            domain=domain_code,
            error_category="invalid_input",
            safe_message=f"Phase 4 domain {domain_code} received an invalid {field_name} value.",
        )
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise Phase4AdapterError(
            domain=domain_code,
            error_category="invalid_input",
            safe_message=f"Phase 4 domain {domain_code} received an invalid {field_name} value.",
        ) from exc


def _coerce_bool(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "t", "1", "yes"}:
            return True
        if normalized in {"false", "f", "0", "no"}:
            return False
    return bool(value)


def _sql_literal(value: Any) -> str:
    if value is None:
        return "null"
    if value == CURRENT_DATE_SQL:
        return CURRENT_DATE_SQL
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return sql_text(value.isoformat())
    if isinstance(value, date):
        return sql_text(value.isoformat())
    return sql_text(str(value))


def _execute_rpc(
    *,
    domain_code: str,
    rpc_name: str,
    args: tuple[Any, ...],
    runner: QueryRunner,
) -> tuple[dict[str, Any], ...]:
    sql = f"select * from {rpc_name}({', '.join(_sql_literal(arg) for arg in args)});"
    try:
        rows = runner(sql)
    except subprocess.CalledProcessError as exc:  # pragma: no cover - covered via mocks
        raise Phase4AdapterError(
            domain=domain_code,
            error_category="phase4_rpc_execution_failed",
            safe_message=f"Phase 4 RPC execution failed for domain {domain_code}.",
        ) from exc
    except RuntimeError as exc:  # pragma: no cover - covered via mocks
        raise Phase4AdapterError(
            domain=domain_code,
            error_category="phase4_rpc_execution_failed",
            safe_message=f"Phase 4 RPC execution failed for domain {domain_code}.",
        ) from exc
    normalized_rows = []
    for row in rows:
        normalized = dict(row)
        normalized["_rpc_name"] = rpc_name
        normalized_rows.append(normalized)
    return tuple(normalized_rows)


def _handle_booking_fee(domain_inputs: dict[str, Any], runner: QueryRunner) -> tuple[tuple[dict[str, Any], ...], tuple[str, ...]]:
    rental_type_code = _pick(domain_inputs, "rental_type_code", "rental_type")
    duration_hours = _pick(domain_inputs, "duration_hours", "booking_duration_hours")
    if rental_type_code is None or duration_hours is None:
        return (
            (
                _synthetic_row(
                    domain_code=PHASE_4_DOMAIN_BOOKING_FEE,
                    rpc_name="api.get_booking_fee_rule",
                    reasoning_state=REASONING_STATE_INSUFFICIENT_INFORMATION,
                    domain_inputs=domain_inputs,
                    summary_text="Booking-fee resolution requires both rental_type_code and duration_hours.",
                ),
            ),
            ("api.get_booking_fee_rule",),
        )
    rows = _execute_rpc(
        domain_code=PHASE_4_DOMAIN_BOOKING_FEE,
        rpc_name="api.get_booking_fee_rule",
        args=(
            _require_non_empty_text(rental_type_code, field_name="rental_type_code", domain_code=PHASE_4_DOMAIN_BOOKING_FEE),
            _coerce_int(duration_hours, field_name="duration_hours", domain_code=PHASE_4_DOMAIN_BOOKING_FEE),
            _pick(domain_inputs, "as_of_date", "effective_date", default=CURRENT_DATE_SQL),
        ),
        runner=runner,
    )
    return rows, ("api.get_booking_fee_rule",)


def _handle_payment(domain_inputs: dict[str, Any], runner: QueryRunner) -> tuple[tuple[dict[str, Any], ...], tuple[str, ...]]:
    payment_stage = _pick(domain_inputs, "payment_stage", "stage")
    payment_plan_option = _pick(domain_inputs, "payment_plan_option", "plan_option")
    booking_lead_time_days = _pick(domain_inputs, "booking_lead_time_days", "lead_time_days")

    if payment_stage in PAYMENT_STAGES_REQUIRING_LEAD_TIME and booking_lead_time_days is None:
        return (
            (
                _synthetic_row(
                    domain_code=PHASE_4_DOMAIN_PAYMENT,
                    rpc_name="api.get_payment_rules",
                    reasoning_state=REASONING_STATE_INSUFFICIENT_INFORMATION,
                    domain_inputs=domain_inputs,
                    summary_text="Payment-stage resolution requires booking_lead_time_days for lead-time-sensitive payment rules.",
                ),
            ),
            ("api.get_payment_rules",),
        )
    if payment_stage == "final_balance" and (payment_plan_option is None or booking_lead_time_days is None):
        return (
            (
                _synthetic_row(
                    domain_code=PHASE_4_DOMAIN_PAYMENT,
                    rpc_name="api.get_payment_rules",
                    reasoning_state=REASONING_STATE_INSUFFICIENT_INFORMATION,
                    domain_inputs=domain_inputs,
                    summary_text="Final-balance payment rules require both payment_plan_option and booking_lead_time_days.",
                ),
            ),
            ("api.get_payment_rules",),
        )

    rows = _execute_rpc(
        domain_code=PHASE_4_DOMAIN_PAYMENT,
        rpc_name="api.get_payment_rules",
        args=(
            payment_stage,
            payment_plan_option,
            None if booking_lead_time_days is None else _coerce_int(
                booking_lead_time_days,
                field_name="booking_lead_time_days",
                domain_code=PHASE_4_DOMAIN_PAYMENT,
            ),
            _pick(domain_inputs, "as_of_date", "effective_date", default=CURRENT_DATE_SQL),
        ),
        runner=runner,
    )
    return rows, ("api.get_payment_rules",)


def _handle_expedited_surcharge(domain_inputs: dict[str, Any], runner: QueryRunner) -> tuple[tuple[dict[str, Any], ...], tuple[str, ...]]:
    rows = _execute_rpc(
        domain_code=PHASE_4_DOMAIN_EXPEDITED_SURCHARGE,
        rpc_name="api.get_expedited_surcharge_rule",
        args=(
            _pick(domain_inputs, "confirmation_date", "booking_confirmation_date", "booking_date"),
            _pick(domain_inputs, "event_date", "event_start_date"),
            _pick(domain_inputs, "as_of_date", "effective_date", default=CURRENT_DATE_SQL),
        ),
        runner=runner,
    )
    return rows, ("api.get_expedited_surcharge_rule",)


def _handle_cancellation(domain_inputs: dict[str, Any], runner: QueryRunner) -> tuple[tuple[dict[str, Any], ...], tuple[str, ...]]:
    scenario = _pick(domain_inputs, "cancellation_scenario", "scenario")
    if scenario is None:
        return (
            (
                _synthetic_row(
                    domain_code=PHASE_4_DOMAIN_CANCELLATION,
                    rpc_name="api.get_cancellation_rules",
                    reasoning_state=REASONING_STATE_INSUFFICIENT_INFORMATION,
                    domain_inputs=domain_inputs,
                    summary_text="Cancellation resolution requires cancellation_scenario.",
                ),
            ),
            ("api.get_cancellation_rules",),
        )
    rows = _execute_rpc(
        domain_code=PHASE_4_DOMAIN_CANCELLATION,
        rpc_name="api.get_cancellation_rules",
        args=(
            _require_non_empty_text(scenario, field_name="cancellation_scenario", domain_code=PHASE_4_DOMAIN_CANCELLATION),
            _pick(domain_inputs, "cancellation_date"),
            _pick(domain_inputs, "event_date", "event_start_date"),
            _pick(domain_inputs, "cost_category", "charge_type"),
            _pick(domain_inputs, "as_of_date", "effective_date", default=CURRENT_DATE_SQL),
        ),
        runner=runner,
    )
    return rows, ("api.get_cancellation_rules",)


def _handle_capacity(domain_inputs: dict[str, Any], runner: QueryRunner) -> tuple[tuple[dict[str, Any], ...], tuple[str, ...]]:
    venue_space_code = _pick(domain_inputs, "venue_space_code")
    rental_type_code = _pick(domain_inputs, "rental_type_code")
    scope_code = _pick(domain_inputs, "scope_code")
    scope_type = _pick(domain_inputs, "scope_type")
    if scope_code is not None and scope_type == "rental_type" and rental_type_code is None:
        rental_type_code = scope_code
    elif scope_code is not None and scope_type == "venue_space" and venue_space_code is None:
        venue_space_code = scope_code
    elif scope_code is not None and venue_space_code is None and rental_type_code is None:
        venue_space_code = scope_code

    configuration_type = _pick(domain_inputs, "configuration_type", "layout_code")
    guest_count = _pick(domain_inputs, "guest_count", "attendee_count")

    if guest_count is None:
        if venue_space_code is None and rental_type_code is None:
            return (
                (
                    _synthetic_row(
                        domain_code=PHASE_4_DOMAIN_CAPACITY,
                        rpc_name="api.get_capacity_rule",
                        reasoning_state=REASONING_STATE_INSUFFICIENT_INFORMATION,
                        domain_inputs=domain_inputs,
                        summary_text="Capacity lookup requires a venue_space_code or rental_type_code.",
                    ),
                ),
                ("api.get_capacity_rule",),
            )
        if venue_space_code is not None and configuration_type is None:
            return (
                (
                    _synthetic_row(
                        domain_code=PHASE_4_DOMAIN_CAPACITY,
                        rpc_name="api.get_capacity_rule",
                        reasoning_state=REASONING_STATE_INSUFFICIENT_INFORMATION,
                        domain_inputs=domain_inputs,
                        summary_text="Venue-space capacity lookups require configuration_type.",
                    ),
                ),
                ("api.get_capacity_rule",),
            )
        rows = _execute_rpc(
            domain_code=PHASE_4_DOMAIN_CAPACITY,
            rpc_name="api.get_capacity_rule",
            args=(
                venue_space_code,
                rental_type_code,
                configuration_type,
                _pick(domain_inputs, "as_of_date", "effective_date", default=CURRENT_DATE_SQL),
            ),
            runner=runner,
        )
        return rows, ("api.get_capacity_rule",)

    rows = _execute_rpc(
        domain_code=PHASE_4_DOMAIN_CAPACITY,
        rpc_name="api.evaluate_capacity",
        args=(
            venue_space_code,
            rental_type_code,
            configuration_type,
            _coerce_int(guest_count, field_name="guest_count", domain_code=PHASE_4_DOMAIN_CAPACITY),
            _pick(domain_inputs, "as_of_date", "effective_date", default=CURRENT_DATE_SQL),
        ),
        runner=runner,
    )
    return rows, ("api.evaluate_capacity",)


def _handle_space_access(domain_inputs: dict[str, Any], runner: QueryRunner) -> tuple[tuple[dict[str, Any], ...], tuple[str, ...]]:
    rental_type_code = _pick(domain_inputs, "rental_type_code", "rental_type")
    venue_space_code = _pick(domain_inputs, "venue_space_code", "space_code")
    evaluate = _coerce_bool(_pick(domain_inputs, "evaluate", "use_evaluation_mode"), default=False)
    mode = _pick(domain_inputs, "mode")
    use_evaluate = evaluate or mode in {"evaluate", "evaluation"}

    if use_evaluate:
        rows = _execute_rpc(
            domain_code=PHASE_4_DOMAIN_SPACE_ACCESS,
            rpc_name="api.evaluate_space_access",
            args=(
                rental_type_code,
                venue_space_code,
                _pick(domain_inputs, "as_of_date", "effective_date", default=CURRENT_DATE_SQL),
            ),
            runner=runner,
        )
        return rows, ("api.evaluate_space_access",)

    if rental_type_code is None or venue_space_code is None:
        return (
            (
                _synthetic_row(
                    domain_code=PHASE_4_DOMAIN_SPACE_ACCESS,
                    rpc_name="api.get_space_access_rule",
                    reasoning_state=REASONING_STATE_INSUFFICIENT_INFORMATION,
                    domain_inputs=domain_inputs,
                    summary_text="Space-access rule lookup requires rental_type_code and venue_space_code.",
                ),
            ),
            ("api.get_space_access_rule",),
        )
    rows = _execute_rpc(
        domain_code=PHASE_4_DOMAIN_SPACE_ACCESS,
        rpc_name="api.get_space_access_rule",
        args=(
            rental_type_code,
            venue_space_code,
            _pick(domain_inputs, "as_of_date", "effective_date", default=CURRENT_DATE_SQL),
        ),
        runner=runner,
    )
    return rows, ("api.get_space_access_rule",)


def _handle_operational_requirements(domain_inputs: dict[str, Any], runner: QueryRunner) -> tuple[tuple[dict[str, Any], ...], tuple[str, ...]]:
    rows = _execute_rpc(
        domain_code=PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS,
        rpc_name="api.get_operational_requirements",
        args=(
            _pick(domain_inputs, "rental_type_code", "rental_type"),
            _pick(domain_inputs, "requirement_type"),
            _pick(domain_inputs, "venue_space_code", "space_code"),
            _coerce_bool(_pick(domain_inputs, "is_multi_day", "multi_day"), default=False),
            _pick(domain_inputs, "context_code"),
            _pick(domain_inputs, "as_of_date", "effective_date", default=CURRENT_DATE_SQL),
        ),
        runner=runner,
    )
    return rows, ("api.get_operational_requirements",)


def _handle_catering_supplier(domain_inputs: dict[str, Any], runner: QueryRunner) -> tuple[tuple[dict[str, Any], ...], tuple[str, ...]]:
    rows = _execute_rpc(
        domain_code=PHASE_4_DOMAIN_CATERING_SUPPLIER,
        rpc_name="api.get_catering_supplier_rules",
        args=(
            _pick(domain_inputs, "catering_arrangement", "arrangement_code"),
            _pick(domain_inputs, "rule_type"),
            _pick(domain_inputs, "context_code"),
            _pick(domain_inputs, "secondary_context_code", "supplier_code"),
            _coerce_bool(_pick(domain_inputs, "alcohol_service", "requires_alcohol"), default=False),
            _pick(domain_inputs, "as_of_date", "effective_date", default=CURRENT_DATE_SQL),
        ),
        runner=runner,
    )
    return rows, ("api.get_catering_supplier_rules",)


def _handle_technical_inventory(domain_inputs: dict[str, Any], runner: QueryRunner) -> tuple[tuple[dict[str, Any], ...], tuple[str, ...]]:
    equipment_code = _pick(domain_inputs, "equipment_code")
    requested_quantity = _pick(domain_inputs, "requested_quantity")
    if requested_quantity is not None:
        if equipment_code is None:
            return (
                (
                    _synthetic_row(
                        domain_code=PHASE_4_DOMAIN_TECHNICAL_INVENTORY,
                        rpc_name="api.evaluate_technical_equipment_quantity",
                        reasoning_state=REASONING_STATE_INSUFFICIENT_INFORMATION,
                        domain_inputs=domain_inputs,
                        summary_text="Technical quantity evaluation requires equipment_code.",
                    ),
                ),
                ("api.evaluate_technical_equipment_quantity",),
            )
        rows = _execute_rpc(
            domain_code=PHASE_4_DOMAIN_TECHNICAL_INVENTORY,
            rpc_name="api.evaluate_technical_equipment_quantity",
            args=(
                _require_non_empty_text(
                    equipment_code,
                    field_name="equipment_code",
                    domain_code=PHASE_4_DOMAIN_TECHNICAL_INVENTORY,
                ),
                _coerce_int(
                    requested_quantity,
                    field_name="requested_quantity",
                    domain_code=PHASE_4_DOMAIN_TECHNICAL_INVENTORY,
                ),
            ),
            runner=runner,
        )
        return rows, ("api.evaluate_technical_equipment_quantity",)

    rows = _execute_rpc(
        domain_code=PHASE_4_DOMAIN_TECHNICAL_INVENTORY,
        rpc_name="api.get_technical_equipment_inventory",
        args=(
            equipment_code,
            _pick(domain_inputs, "equipment_category"),
        ),
        runner=runner,
    )
    return rows, ("api.get_technical_equipment_inventory",)


def _handle_technical_capability(domain_inputs: dict[str, Any], runner: QueryRunner) -> tuple[tuple[dict[str, Any], ...], tuple[str, ...]]:
    requirement_code = _pick(domain_inputs, "requirement_code")
    mode = _pick(domain_inputs, "mode")
    if requirement_code is not None or mode in {"evaluate", "evaluation"}:
        rows = _execute_rpc(
            domain_code=PHASE_4_DOMAIN_TECHNICAL_CAPABILITY,
            rpc_name="api.evaluate_technical_requirement",
            args=(
                requirement_code,
                _pick(domain_inputs, "as_of_date", "effective_date", default=CURRENT_DATE_SQL),
            ),
            runner=runner,
        )
        return rows, ("api.evaluate_technical_requirement",)

    capability_code = _pick(domain_inputs, "capability_code")
    if capability_code is None:
        return (
            (
                _synthetic_row(
                    domain_code=PHASE_4_DOMAIN_TECHNICAL_CAPABILITY,
                    rpc_name="api.get_technical_capability",
                    reasoning_state=REASONING_STATE_INSUFFICIENT_INFORMATION,
                    domain_inputs=domain_inputs,
                    summary_text="Technical capability lookup requires capability_code or requirement_code.",
                ),
            ),
            ("api.get_technical_capability",),
        )
    rows = _execute_rpc(
        domain_code=PHASE_4_DOMAIN_TECHNICAL_CAPABILITY,
        rpc_name="api.get_technical_capability",
        args=(
            _pick(domain_inputs, "rule_type", default="capability_availability"),
            capability_code,
            requirement_code,
            _pick(domain_inputs, "technical_area"),
            _pick(domain_inputs, "as_of_date", "effective_date", default=CURRENT_DATE_SQL),
        ),
        runner=runner,
    )
    return rows, ("api.get_technical_capability",)


def _handle_service_rules(domain_inputs: dict[str, Any], runner: QueryRunner) -> tuple[tuple[dict[str, Any], ...], tuple[str, ...]]:
    rows = _execute_rpc(
        domain_code=PHASE_4_DOMAIN_SERVICE_RULES,
        rpc_name="api.get_service_rules",
        args=(
            _pick(domain_inputs, "service_level"),
            _pick(domain_inputs, "service_type"),
            _pick(domain_inputs, "as_of_date", "effective_date", default=CURRENT_DATE_SQL),
        ),
        runner=runner,
    )
    return rows, ("api.get_service_rules",)


def _handle_facilitator_requirements(domain_inputs: dict[str, Any], runner: QueryRunner) -> tuple[tuple[dict[str, Any], ...], tuple[str, ...]]:
    rows = _execute_rpc(
        domain_code=PHASE_4_DOMAIN_FACILITATOR_REQUIREMENTS,
        rpc_name="api.get_facilitator_requirements",
        args=(
            _pick(domain_inputs, "facilitator_arrangement", "arrangement_code"),
            _pick(domain_inputs, "as_of_date", "effective_date", default=CURRENT_DATE_SQL),
        ),
        runner=runner,
    )
    return rows, ("api.get_facilitator_requirements",)


PHASE4_ADAPTER_REGISTRY: dict[str, Phase4Handler] = {
    PHASE_4_DOMAIN_BOOKING_FEE: Phase4Handler(
        domain_code=PHASE_4_DOMAIN_BOOKING_FEE,
        rpc_names=("api.get_booking_fee_rule",),
        handler=_handle_booking_fee,
    ),
    PHASE_4_DOMAIN_PAYMENT: Phase4Handler(
        domain_code=PHASE_4_DOMAIN_PAYMENT,
        rpc_names=("api.get_payment_rules",),
        handler=_handle_payment,
    ),
    PHASE_4_DOMAIN_EXPEDITED_SURCHARGE: Phase4Handler(
        domain_code=PHASE_4_DOMAIN_EXPEDITED_SURCHARGE,
        rpc_names=("api.get_expedited_surcharge_rule",),
        handler=_handle_expedited_surcharge,
    ),
    PHASE_4_DOMAIN_CANCELLATION: Phase4Handler(
        domain_code=PHASE_4_DOMAIN_CANCELLATION,
        rpc_names=("api.get_cancellation_rules",),
        handler=_handle_cancellation,
    ),
    PHASE_4_DOMAIN_CAPACITY: Phase4Handler(
        domain_code=PHASE_4_DOMAIN_CAPACITY,
        rpc_names=("api.get_capacity_rule", "api.evaluate_capacity"),
        handler=_handle_capacity,
    ),
    PHASE_4_DOMAIN_SPACE_ACCESS: Phase4Handler(
        domain_code=PHASE_4_DOMAIN_SPACE_ACCESS,
        rpc_names=("api.get_space_access_rule", "api.evaluate_space_access"),
        handler=_handle_space_access,
    ),
    PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS: Phase4Handler(
        domain_code=PHASE_4_DOMAIN_OPERATIONAL_REQUIREMENTS,
        rpc_names=("api.get_operational_requirements",),
        handler=_handle_operational_requirements,
    ),
    PHASE_4_DOMAIN_CATERING_SUPPLIER: Phase4Handler(
        domain_code=PHASE_4_DOMAIN_CATERING_SUPPLIER,
        rpc_names=("api.get_catering_supplier_rules",),
        handler=_handle_catering_supplier,
    ),
    PHASE_4_DOMAIN_TECHNICAL_INVENTORY: Phase4Handler(
        domain_code=PHASE_4_DOMAIN_TECHNICAL_INVENTORY,
        rpc_names=("api.get_technical_equipment_inventory", "api.evaluate_technical_equipment_quantity"),
        handler=_handle_technical_inventory,
    ),
    PHASE_4_DOMAIN_TECHNICAL_CAPABILITY: Phase4Handler(
        domain_code=PHASE_4_DOMAIN_TECHNICAL_CAPABILITY,
        rpc_names=("api.get_technical_capability", "api.evaluate_technical_requirement"),
        handler=_handle_technical_capability,
    ),
    PHASE_4_DOMAIN_SERVICE_RULES: Phase4Handler(
        domain_code=PHASE_4_DOMAIN_SERVICE_RULES,
        rpc_names=("api.get_service_rules",),
        handler=_handle_service_rules,
    ),
    PHASE_4_DOMAIN_FACILITATOR_REQUIREMENTS: Phase4Handler(
        domain_code=PHASE_4_DOMAIN_FACILITATOR_REQUIREMENTS,
        rpc_names=("api.get_facilitator_requirements",),
        handler=_handle_facilitator_requirements,
    ),
}


def _pick(payload: dict[str, Any], *field_names: str, default: Any = None) -> Any:
    for field_name in field_names:
        if field_name in payload:
            return payload[field_name]
    return default


def _first_text(payload: dict[str, Any], *field_names: str) -> str | None:
    for field_name in field_names:
        value = _clean_text(payload.get(field_name))
        if value is not None:
            return value
    return None


def _normalize_source_codes(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        cleaned = _clean_text(value)
        return (cleaned,) if cleaned is not None else ()
    return tuple(
        cleaned
        for cleaned in (_clean_text(item) for item in value)
        if cleaned is not None
    )


def _unique_strings(values: tuple[str, ...] | list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "PHASE4_ADAPTER_REGISTRY",
    "Phase4AdapterConfiguration",
    "execute_phase4_plan",
]
