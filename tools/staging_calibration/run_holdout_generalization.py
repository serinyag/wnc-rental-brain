from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from tools.staging_calibration.run_operator_calibration import (
    CATEGORY_LABELS,
    OBS_CHANGE,
    OBS_CONFIRM,
    OBS_DECISION,
    OBS_FACT,
    OBS_REQUIREMENT,
    CLAIM_CHANGE,
    CLAIM_CONFIRM,
    CLAIM_EXCEPTION,
    CLAIM_NEW,
    CLAIM_REQUIREMENT,
    CalibrationScenario,
    DraftSummary,
    ObservationSpec,
    OperatorHarnessClient,
    ScenarioExpectations,
    ScoredCase,
    StageSpec,
    build_client,
    evaluate_case,
    extract_actual_snapshot,
    run_scenario,
    summarize_results,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AUTH_FILE = REPO_ROOT / "Staging Authentications.txt"
DEFAULT_HOLDOUT_FILE = REPO_ROOT / "docs" / "staging" / "calibration" / "holdout_scenarios.json"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "docs" / "staging" / "calibration"

OBSERVATION_TYPE_MAP = {
    "fact_candidate": OBS_FACT,
    "change_candidate": OBS_CHANGE,
    "confirmation_candidate": OBS_CONFIRM,
    "case_decision_candidate": OBS_DECISION,
    "requirement_evidence_candidate": OBS_REQUIREMENT,
}

CLAIM_KIND_MAP = {
    "new_information": CLAIM_NEW,
    "change_request": CLAIM_CHANGE,
    "confirmation": CLAIM_CONFIRM,
    "exception_request": CLAIM_EXCEPTION,
    "requirement_evidence": CLAIM_REQUIREMENT,
}


def _load_holdout_definition(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _observation_from_payload(payload: dict[str, Any]) -> ObservationSpec:
    return ObservationSpec(
        field_code=payload["field_code"],
        value=payload["value"],
        observation_type=OBSERVATION_TYPE_MAP[payload["observation_type"]],
        claim_kind=CLAIM_KIND_MAP[payload["claim_kind"]],
        source_excerpt=payload.get("source_excerpt"),
    )


def _stage_from_payload(payload: dict[str, Any]) -> StageSpec:
    return StageSpec(
        name=payload["name"],
        observations=tuple(_observation_from_payload(item) for item in payload.get("observations", [])),
        run_waiting=bool(payload.get("run_waiting", False)),
        generate_draft=bool(payload.get("generate_draft", False)),
    )


def _expectations_from_payload(payload: dict[str, Any]) -> ScenarioExpectations:
    system = payload["expected_system_assertions"]
    return ScenarioExpectations(
        relevant_rules=tuple(payload["relevant_rules"]),
        expected_current_fields=dict(payload["known_facts"]),
        expected_absent_current_fields=tuple(payload.get("expected_absent_current_fields", ())),
        expected_open_question_types=tuple(system.get("expected_open_question_types", ())),
        forbidden_open_question_types=tuple(system.get("forbidden_open_question_types", ())),
        expected_proposed_change_count=system.get("expected_proposed_change_count"),
        expected_reschedule_request_count=system.get("expected_reschedule_request_count"),
        expected_booking_fee_baseline=system.get("expected_booking_fee_baseline"),
        expected_effective_booking_fee=system.get("expected_effective_booking_fee"),
        expected_effective_fee_matches_baseline=bool(system.get("expected_effective_fee_matches_baseline", False)),
        expected_case_decision_status=system.get("expected_case_decision_status"),
        expected_draft=bool(system.get("expected_draft", False)),
        expected_draft_question_types=tuple(system.get("expected_draft_question_types", system.get("expected_open_question_types", ()))),
        expected_confirmation_required=system.get("expected_confirmation_required"),
        expected_feasibility_as_requested=system.get("expected_feasibility_as_requested"),
        expected_material_blocker=bool(system.get("expected_material_blocker", False)),
        expected_human_confirmation_required=bool(system.get("expected_material_blocker", False)),
        forbidden_draft_fragments=tuple(payload.get("statements_that_must_not_appear", ())),
        must_not_activate_exception=bool(system.get("must_not_activate_exception", False)),
        must_not_create_reschedule_for_same_schedule=bool(system.get("must_not_create_reschedule_for_same_schedule", False)),
        notes=" | ".join(
            part
            for part in (
                f"expected_state={payload['expected_state']}",
                f"coverage={payload['coverage_label']}",
                f"next_action={payload.get('expected_next_action', 'unspecified')}",
                payload.get("description", ""),
            )
            if part
        ),
    )


def _scenario_from_payload(payload: dict[str, Any]) -> CalibrationScenario:
    return CalibrationScenario(
        scenario_id=payload["scenario_id"],
        category_code="HOLD",
        title=payload["title"],
        description=payload["description"],
        display_name=f"{payload['scenario_id']} {payload['title']}",
        client_label=f"{payload['scenario_id']} Synthetic Holdout Client",
        contact_email=f"{payload['scenario_id'].lower()}@example.test",
        event_reference=f"{payload['scenario_id']} holdout reference",
        stages=tuple(_stage_from_payload(stage_payload) for stage_payload in payload["stages"]),
        expectations=_expectations_from_payload(payload),
        phase6_relevant=bool(payload.get("phase6_relevant", False)),
    )


def _classify_system_state(result: ScoredCase) -> str:
    actual = result.actual
    semantic_states = tuple(actual.get("reasoning_projection_semantic_states", ()))
    if actual["active_open_question_types"]:
        return "missing_client_fact"
    if "known_no" in semantic_states:
        return "known_no"
    if _is_exception_approval_only_path(actual):
        return "known_no"
    if "unknown_internal" in semantic_states:
        return "unknown_internal"
    if "known_conditional" in semantic_states:
        return "known_conditional"
    if actual["open_blocker_count"] > 0 or actual["feasibility_snapshot"].get("Confirmation still required") == "Yes":
        return "unknown_internal"
    return "known_yes"


def _is_exception_approval_only_path(actual: dict[str, Any]) -> bool:
    hard_constraint = str(actual.get("feasibility_snapshot", {}).get("Hard constraint", ""))
    commercial = actual.get("commercial_snapshot", {})
    case_specific_exception = commercial.get("Case-specific exception") or commercial.get("Case-specific exceptions")
    return (
        actual.get("feasibility_snapshot", {}).get("Confirmation still required") == "No"
        and "Approval must be approved" in hard_constraint
        and any(status in {"proposed", "pending_approval"} for status in actual.get("case_decision_statuses", ()))
        and str(case_specific_exception).strip().lower() == "pending"
    )


def _semantic_match(expected_state: str, system_state: str) -> bool:
    return expected_state == system_state


def _holdout_critical_failures(payload: dict[str, Any], result: ScoredCase, system_state: str) -> list[str]:
    failures: list[str] = []
    expected_state = payload["expected_state"]
    actual = result.actual
    forbidden_phrases = tuple(payload.get("statements_that_must_not_appear", ()))

    if expected_state == "known_yes" and actual["open_blocker_count"] > 0:
        failures.append("over_cautious_blocker_on_known_yes")
    if expected_state == "missing_client_fact" and not actual["active_open_question_types"]:
        failures.append("failed_to_ask_for_missing_client_fact")
    if expected_state == "unknown_internal" and actual["active_open_question_types"]:
        failures.append("asked_client_for_internal_unknown")
    if expected_state == "known_no" and system_state in {"unknown_internal", "known_conditional"}:
        failures.append("deterministic_no_degraded_into_confirmation")
    if expected_state in {"known_no", "unknown_internal"} and actual["open_blocker_count"] == 0:
        failures.append("failed_to_surface_material_blocker")
    if expected_state == "known_no" and system_state == "known_yes":
        failures.append("false_confirmation_on_known_no")

    draft = actual.get("draft")
    if isinstance(draft, dict):
        body_text = draft.get("body_text") or ""
        for fragment in forbidden_phrases:
            if fragment and fragment in body_text:
                failures.append(f"forbidden_fragment_in_draft:{fragment}")

    return failures


def _render_semantic_matrix(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Holdout | Expected State | System State | Match |",
        "| ------- | -------------- | ------------ | ----- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['scenario_id']} | {row['expected_state']} | {row['system_state']} | {'yes' if row['match'] else 'no'} |"
        )
    return "\n".join(lines)


def _build_report(
    *,
    run_slug: str,
    holdout_definition: dict[str, Any],
    scored_results: list[ScoredCase],
    summary: dict[str, Any],
    semantic_rows: list[dict[str, Any]],
    extra_failures: dict[str, list[str]],
) -> str:
    lines = [
        "# Holdout Generalization Validation",
        "",
        f"- date: 2026-08-20",
        f"- run slug: `{run_slug}`",
        f"- methodology: hosted staging operator API using the same real deployed intake/reconcile/waiting/draft path as calibration",
        f"- holdout version: `{holdout_definition['version']}`",
        f"- holdout size: `{holdout_definition['scenario_count']}`",
        f"- environment: `APP_ENV=staging`, `Outlook=disabled`, `Asana=configured`, no provider execution used",
        "",
        "## Summary",
        "",
        f"- A/B/C/D counts: `{summary['edit_burden_counts']}`",
        f"- A+B percentage: `{summary['A_plus_B_percentage']}%`",
        f"- critical failures from baseline rubric: `{summary['critical_failure_count']}`",
        f"- unsupported claim count: `{summary['unsupported_claim_count']}`",
        f"- missing-information detection rate: `{summary['missing_information_detection_rate']}`",
        f"- authority-conflict success rate: `{summary['authority_conflict_success_rate']}`",
        f"- confidentiality safety rate: `{summary['confidentiality_safety_rate']}`",
        f"- correct-next-action rate: `{summary['correct_next_action_rate']}`",
        "",
        "## Semantic Uncertainty Matrix",
        "",
        _render_semantic_matrix(semantic_rows),
        "",
        "## Holdout Findings",
        "",
    ]

    for payload in holdout_definition["scenarios"]:
        result = next(item for item in scored_results if item.scenario_id == payload["scenario_id"])
        lines.extend(
            [
                f"### {payload['scenario_id']} — {payload['title']}",
                "",
                f"- coverage: `{payload['coverage_label']}`",
                f"- expected state: `{payload['expected_state']}`",
                f"- system state: `{next(row['system_state'] for row in semantic_rows if row['scenario_id'] == payload['scenario_id'])}`",
                f"- edit burden: `{result.edit_burden}`",
                f"- failures: `{list(result.failures)}`",
                f"- extra holdout failures: `{extra_failures[payload['scenario_id']]}`",
                f"- critical failures: `{list(result.critical_failures)}`",
                f"- facts: `{result.actual['current_facts']}`",
                f"- feasibility: `{result.actual['feasibility_snapshot']}`",
                f"- open questions: `{list(result.actual['active_open_question_types'])}`",
                f"- actions: `{list(result.actual['active_workflow_action_types'])}`",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the frozen holdout generalization validation against hosted staging.")
    parser.add_argument("--auth-file", type=Path, default=DEFAULT_AUTH_FILE)
    parser.add_argument("--holdout-file", type=Path, default=DEFAULT_HOLDOUT_FILE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--timeout-seconds", type=float, default=45.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    holdout_definition = _load_holdout_definition(args.holdout_file)
    frozen_scenarios = tuple(_scenario_from_payload(payload) for payload in holdout_definition["scenarios"])

    client: OperatorHarnessClient = build_client(args.auth_file, timeout_seconds=args.timeout_seconds)
    health = client.get_health()
    if health.get("status") != "ok":
        raise SystemExit("Hosted staging /healthz is not healthy enough for holdout validation.")

    run_slug = "holdout-" + time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    scored_results: list[ScoredCase] = []
    semantic_rows: list[dict[str, Any]] = []
    execution_logs: dict[str, list[dict[str, Any]]] = {}
    extra_failures: dict[str, list[str]] = {}

    for payload, scenario in zip(holdout_definition["scenarios"], frozen_scenarios, strict=True):
        actual, logs = run_scenario(client, scenario, run_slug=run_slug)
        execution_logs[scenario.scenario_id] = logs
        scored = evaluate_case(scenario, actual)
        scored_results.append(scored)
        system_state = _classify_system_state(scored)
        semantic_rows.append(
            {
                "scenario_id": scenario.scenario_id,
                "expected_state": payload["expected_state"],
                "system_state": system_state,
                "match": _semantic_match(payload["expected_state"], system_state),
            }
        )
        extra_failures[scenario.scenario_id] = _holdout_critical_failures(payload, scored, system_state)

    summary = summarize_results(scored_results)

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / f"holdout_results_{run_slug}.json"
    latest_results_path = output_dir / "holdout_results_latest.json"
    report_path = output_dir / f"holdout_report_{run_slug}.md"
    latest_report_path = output_dir / "holdout_report_latest.md"

    results_payload = {
        "generated_at": "2026-08-20",
        "run_slug": run_slug,
        "holdout_version": holdout_definition["version"],
        "summary": summary,
        "semantic_matrix": semantic_rows,
        "results": [
            {
                "scenario_id": result.scenario_id,
                "coverage_label": next(item["coverage_label"] for item in holdout_definition["scenarios"] if item["scenario_id"] == result.scenario_id),
                "expected_state": next(item["expected_state"] for item in holdout_definition["scenarios"] if item["scenario_id"] == result.scenario_id),
                "system_state": next(item["system_state"] for item in semantic_rows if item["scenario_id"] == result.scenario_id),
                "state_match": next(item["match"] for item in semantic_rows if item["scenario_id"] == result.scenario_id),
                "scores": result.scores,
                "edit_burden": result.edit_burden,
                "critical_failures": list(result.critical_failures),
                "holdout_extra_failures": extra_failures[result.scenario_id],
                "failures": list(result.failures),
                "diagnosed_layer": result.diagnosed_layer,
                "root_cause": result.root_cause,
                "actual": result.actual,
                "execution_log": execution_logs[result.scenario_id],
            }
            for result in scored_results
        ],
    }

    results_text = json.dumps(results_payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    results_path.write_text(results_text, encoding="utf-8")
    latest_results_path.write_text(results_text, encoding="utf-8")

    report_text = _build_report(
        run_slug=run_slug,
        holdout_definition=holdout_definition,
        scored_results=scored_results,
        summary=summary,
        semantic_rows=semantic_rows,
        extra_failures=extra_failures,
    )
    report_path.write_text(report_text, encoding="utf-8")
    latest_report_path.write_text(report_text, encoding="utf-8")

    print(
        json.dumps(
            {
                "artifacts": {
                    "results": str(results_path),
                    "results_latest": str(latest_results_path),
                    "report": str(report_path),
                    "report_latest": str(latest_report_path),
                },
                "summary": summary,
                "semantic_matrix": semantic_rows,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
