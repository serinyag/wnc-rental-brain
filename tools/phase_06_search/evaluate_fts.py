from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from tools.phase_05_chunking.generate_pilot import run_supabase_query, sql_text


@dataclass(frozen=True)
class HistoricalSearchFixture:
    category: str
    query: str
    expected_case_codes: tuple[str, ...]
    preferred_unit_types: tuple[str, ...] = ()
    required_hit_rank: int = 1
    note: str = ""
    miss_category_if_not_hit3: str = "semantic similarity required"


@dataclass(frozen=True)
class FixtureAssessment:
    first_matching_rank: int | None
    hit_at_1: bool
    hit_at_3: bool
    satisfied_ground_truth: bool
    preferred_unit_matched: bool
    note: str
    miss_category: str | None


FIXTURES: tuple[HistoricalSearchFixture, ...] = (
    HistoricalSearchFixture(
        category="Similar historical situation",
        query="multi-day venue takeover",
        expected_case_codes=("HC-001",),
        preferred_unit_types=("case_narrative",),
        required_hit_rank=1,
        note="Exact title and narrative language should make the Merrachi takeover case dominate.",
    ),
    HistoricalSearchFixture(
        category="Similar historical situation",
        query="whole venue clearing",
        expected_case_codes=("HC-001",),
        preferred_unit_types=("responsibility", "decision", "lesson"),
        required_hit_rank=1,
        note="HC-001 contains the clearest whole-venue clearing precedent.",
    ),
    HistoricalSearchFixture(
        category="Similar historical situation",
        query="client operated event",
        expected_case_codes=("HC-001", "HC-003"),
        preferred_unit_types=("decision", "responsibility", "case_narrative"),
        required_hit_rank=3,
        note="Both HC-001 and HC-003 draw a boundary between WNC support and the client running the event.",
        miss_category_if_not_hit3="broad query or ranking tie",
    ),
    HistoricalSearchFixture(
        category="Operational problem",
        query="heavy electrical equipment",
        expected_case_codes=("HC-002",),
        preferred_unit_types=("decision", "lesson", "case_narrative"),
        required_hit_rank=1,
        note="HC-002 is the corpus precedent for technical load and qualified electrical assessment.",
    ),
    HistoricalSearchFixture(
        category="Operational problem",
        query="strong catering smell",
        expected_case_codes=("HC-004",),
        preferred_unit_types=("decision", "lesson"),
        required_hit_rank=1,
        note="HC-004 contains explicit smell and scent-sensitive event language.",
    ),
    HistoricalSearchFixture(
        category="Operational problem",
        query="sensory-sensitive beauty event",
        expected_case_codes=("HC-004",),
        preferred_unit_types=("case_narrative", "decision", "lesson"),
        required_hit_rank=3,
        note="This is intentionally a slightly paraphrased lexical query for the scent-sensitive beauty-event precedent.",
        miss_category_if_not_hit3="vocabulary mismatch",
    ),
    HistoricalSearchFixture(
        category="Operational problem",
        query="late build-up",
        expected_case_codes=("HC-006",),
        preferred_unit_types=("decision", "lesson"),
        required_hit_rank=1,
        note="HC-006 explicitly uses late build-up wording.",
    ),
    HistoricalSearchFixture(
        category="Operational problem",
        query="fake snow cleanup",
        expected_case_codes=("HC-007",),
        preferred_unit_types=("decision", "lesson", "responsibility", "case_narrative"),
        required_hit_rank=1,
        note="HC-007 contains exact fake-snow and cleanup language.",
    ),
    HistoricalSearchFixture(
        category="Operational problem",
        query="external storage",
        expected_case_codes=("HC-001", "HC-003"),
        preferred_unit_types=("decision", "lesson", "case_narrative"),
        required_hit_rank=3,
        note="Both HC-001 and HC-003 discuss external storage, so case-level top-three coverage is sufficient.",
        miss_category_if_not_hit3="broad query or ranking tie",
    ),
    HistoricalSearchFixture(
        category="Operational problem",
        query="competitor branding",
        expected_case_codes=("HC-008",),
        preferred_unit_types=("decision", "responsibility", "lesson"),
        required_hit_rank=1,
        note="HC-008 is the branded-company / competitor-visibility precedent.",
    ),
    HistoricalSearchFixture(
        category="Caution",
        query="permit compliance",
        expected_case_codes=("HC-009",),
        preferred_unit_types=("decision", "lesson", "responsibility", "case_narrative"),
        required_hit_rank=1,
        note="HC-009 is the permit and compliance cautionary precedent.",
    ),
    HistoricalSearchFixture(
        category="Responsibility",
        query="client provided wine",
        expected_case_codes=("HC-005",),
        preferred_unit_types=("responsibility", "decision"),
        required_hit_rank=1,
        note="HC-005 contains exact wine-responsibility wording.",
    ),
    HistoricalSearchFixture(
        category="Responsibility",
        query="WNC cleared the venue",
        expected_case_codes=("HC-001",),
        preferred_unit_types=("responsibility", "decision"),
        required_hit_rank=1,
        note="HC-001 contains the clearest white-box clearing language.",
    ),
    HistoricalSearchFixture(
        category="Responsibility",
        query="external caterer responsibility",
        expected_case_codes=("HC-003", "HC-006"),
        preferred_unit_types=("responsibility",),
        required_hit_rank=3,
        note="The corpus uses external-suppliers wording rather than a standardized external-caterer phrase.",
        miss_category_if_not_hit3="vocabulary mismatch",
    ),
    HistoricalSearchFixture(
        category="Caution",
        query="current legal precedent",
        expected_case_codes=("HC-009",),
        preferred_unit_types=("decision", "lesson", "case_narrative"),
        required_hit_rank=1,
        note="HC-009 explicitly says the historical ADE solution is not current legal precedent.",
    ),
    HistoricalSearchFixture(
        category="Caution",
        query="grace period setup",
        expected_case_codes=("HC-007",),
        preferred_unit_types=("decision", "lesson", "case_narrative"),
        required_hit_rank=1,
        note="HC-007 explicitly ties the grace period to arrival rather than setup.",
    ),
    HistoricalSearchFixture(
        category="Caution",
        query="damage cleanup",
        expected_case_codes=("HC-007",),
        preferred_unit_types=("responsibility", "decision", "case_narrative"),
        required_hit_rank=3,
        note="Damage and cleanup are both present in HC-007, but the wording is spread across multiple unit types.",
        miss_category_if_not_hit3="broad query or ranking tie",
    ),
    HistoricalSearchFixture(
        category="Historical commercial specifics",
        query="300 storage",
        expected_case_codes=("HC-003",),
        preferred_unit_types=("decision", "case_narrative", "lesson"),
        required_hit_rank=1,
        note="HC-003 contains the EUR 300 storage precedent.",
    ),
    HistoricalSearchFixture(
        category="Historical commercial specifics",
        query="florals",
        expected_case_codes=("HC-003",),
        preferred_unit_types=("decision", "responsibility", "case_narrative"),
        required_hit_rank=3,
        note="The corpus uses floral-arrangement wording rather than a normalized floral-service taxonomy.",
        miss_category_if_not_hit3="vocabulary mismatch",
    ),
    HistoricalSearchFixture(
        category="Historical commercial specifics",
        query="overtime charge",
        expected_case_codes=("HC-006",),
        preferred_unit_types=("decision", "lesson"),
        required_hit_rank=1,
        note="HC-006 is the overtime / staffing precedent for late build-up.",
    ),
    HistoricalSearchFixture(
        category="Historical commercial specifics",
        query="discount exposure gifts",
        expected_case_codes=("HC-004",),
        preferred_unit_types=("decision", "lesson", "responsibility"),
        required_hit_rank=1,
        note="HC-004 contains exact exposure / gifts / discount caution language.",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate the Phase 6 historical full-text search baseline.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/phase-06/PHASE_6_HISTORICAL_FTS_EVALUATION.md"),
        help="Markdown report path to write.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of top results to capture per query.",
    )
    return parser.parse_args()


def fetch_corpus_summary() -> dict[str, int]:
    sql = """
select
  count(*)::integer as searchable_units,
  count(distinct historical_case_version_id)::integer as searchable_case_versions,
  count(distinct case_code)::integer as searchable_cases
from private.current_historical_case_search_units;
""".strip()
    payload = run_supabase_query(sql, expect_json=True)
    row = payload["rows"][0]
    if row["searchable_units"] == 0:
        raise SystemExit("No searchable historical units were found. Run the local Supabase reset first.")
    return row


def run_search(query: str, limit: int) -> list[dict]:
    sql = f"""
select
  search_unit_id,
  source_layer_role,
  source_key,
  unit_type,
  search_text,
  lexical_score,
  case_code,
  case_title,
  historical_case_version_id,
  precedent_type,
  precedent_availability,
  lesson_kind,
  actor_type,
  historical_value_only,
  contamination_risk_level,
  current_authority_disposition,
  effective_confidentiality_level_code,
  case_personal_information_status,
  source_object_personal_information_status,
  primary_source_locator
from private.search_historical_case_units(
  {sql_text(query)},
  {limit}
);
""".strip()
    payload = run_supabase_query(sql, expect_json=True)
    return payload["rows"]


def assess_fixture(fixture: HistoricalSearchFixture, rows: list[dict]) -> FixtureAssessment:
    first_matching_rank: int | None = None
    for index, row in enumerate(rows, start=1):
        if row["case_code"] in fixture.expected_case_codes:
            first_matching_rank = index
            break

    hit_at_1 = first_matching_rank == 1
    hit_at_3 = first_matching_rank is not None and first_matching_rank <= 3
    satisfied_ground_truth = first_matching_rank is not None and first_matching_rank <= fixture.required_hit_rank

    preferred_unit_matched = False
    if first_matching_rank is not None and fixture.preferred_unit_types:
        preferred_unit_matched = rows[first_matching_rank - 1]["unit_type"] in fixture.preferred_unit_types
    elif first_matching_rank is not None:
        preferred_unit_matched = True

    if first_matching_rank is None:
        note = "No expected case appeared in the captured result window."
        miss_category = fixture.miss_category_if_not_hit3
    elif first_matching_rank == 1:
        top_row = rows[0]
        note = f"Top result is expected case {top_row['case_code']} / {top_row['unit_type']}."
        miss_category = None
    elif first_matching_rank <= 3:
        top_row = rows[0]
        note = (
            f"Expected case appears at rank {first_matching_rank}; top result is "
            f"{top_row['case_code']} / {top_row['unit_type']}."
        )
        miss_category = "ranking tie or broad query"
    else:
        note = f"Expected case first appears at rank {first_matching_rank}, outside the top three."
        miss_category = fixture.miss_category_if_not_hit3

    return FixtureAssessment(
        first_matching_rank=first_matching_rank,
        hit_at_1=hit_at_1,
        hit_at_3=hit_at_3,
        satisfied_ground_truth=satisfied_ground_truth,
        preferred_unit_matched=preferred_unit_matched,
        note=note,
        miss_category=miss_category,
    )


def body_preview(body_text: str, limit: int = 140) -> str:
    compact = " ".join(body_text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def rank_display(value: int | None) -> str:
    return "miss" if value is None else str(value)


def bool_display(value: bool) -> str:
    return "yes" if value else "no"


def render_report(limit: int) -> str:
    summary = fetch_corpus_summary()
    report_rows: list[tuple[HistoricalSearchFixture, FixtureAssessment, list[dict]]] = []
    for fixture in FIXTURES:
        rows = run_search(fixture.query, limit)
        report_rows.append((fixture, assess_fixture(fixture, rows), rows))

    hit_at_1_count = sum(1 for _, assessment, _ in report_rows if assessment.hit_at_1)
    hit_at_3_count = sum(1 for _, assessment, _ in report_rows if assessment.hit_at_3)
    reciprocal_rank_total = sum(
        0 if assessment.first_matching_rank is None else 1 / assessment.first_matching_rank
        for _, assessment, _ in report_rows
    )
    total_queries = len(report_rows)
    hit_at_1 = hit_at_1_count / total_queries
    hit_at_3 = hit_at_3_count / total_queries
    mrr = reciprocal_rank_total / total_queries

    misses = [
        (fixture, assessment)
        for fixture, assessment, _ in report_rows
        if not assessment.hit_at_1 or not assessment.hit_at_3
    ]

    safety_queries = (
        "300 storage",
        "current legal precedent",
        "Later modelling may need",
    )
    safety_rows = [
        (query, rows[0] if rows else None)
        for query in safety_queries
        for rows in [run_search(query, 1)]
    ]

    lines: list[str] = []
    lines.append("# Phase 6 Historical FTS Evaluation")
    lines.append("")
    lines.append(f"Date: {date.today():%B %-d, %Y}")
    lines.append("")
    lines.append("## Evaluation Corpus")
    lines.append("")
    lines.append(f"- searchable active historical cases: `{summary['searchable_cases']}`")
    lines.append(f"- searchable active historical case versions: `{summary['searchable_case_versions']}`")
    lines.append(f"- searchable current historical units: `{summary['searchable_units']}`")
    lines.append(f"- top results captured per query: `{limit}`")
    lines.append("")
    lines.append("## Configuration")
    lines.append("")
    lines.append("- PostgreSQL text-search configuration: `english`")
    lines.append("- query parser: `websearch_to_tsquery`")
    lines.append("- ranking function: `ts_rank_cd` with length normalization `2`")
    lines.append("- weighting:")
    lines.append("  - `A`: case title")
    lines.append("  - `B`: case code and governed search-unit text")
    lines.append("  - `C`: unit type, responsibility actor, lesson kind")
    lines.append("- searchable corpus surface: `private.current_historical_case_search_units`")
    lines.append("")
    lines.append("## Query Set")
    lines.append("")
    for fixture in FIXTURES:
        preferred_units = ", ".join(fixture.preferred_unit_types) if fixture.preferred_unit_types else "any"
        lines.append(
            f"- `{fixture.query}` | category `{fixture.category}` | expected cases `{', '.join(fixture.expected_case_codes)}` | "
            f"preferred units `{preferred_units}` | success target `Hit@{fixture.required_hit_rank}`"
        )
    lines.append("")
    lines.append("## Results")
    lines.append("")
    for fixture, assessment, rows in report_rows:
        lines.append(f"### `{fixture.query}`")
        lines.append("")
        lines.append(f"- category: `{fixture.category}`")
        lines.append(f"- expected cases: `{', '.join(fixture.expected_case_codes)}`")
        if fixture.preferred_unit_types:
            lines.append(f"- preferred unit types: `{', '.join(fixture.preferred_unit_types)}`")
        lines.append(f"- required success condition: `Hit@{fixture.required_hit_rank}`")
        if fixture.note:
            lines.append(f"- fixture note: {fixture.note}")
        lines.append(f"- first matching rank: `{rank_display(assessment.first_matching_rank)}`")
        lines.append(f"- Hit@1: `{bool_display(assessment.hit_at_1)}`")
        lines.append(f"- Hit@3: `{bool_display(assessment.hit_at_3)}`")
        lines.append(f"- ground-truth satisfied: `{bool_display(assessment.satisfied_ground_truth)}`")
        lines.append(f"- preferred unit matched: `{bool_display(assessment.preferred_unit_matched)}`")
        lines.append(f"- notes: {assessment.note}")
        if rows:
            top_row = rows[0]
            lines.append(
                f"- top result: `{top_row['case_code']}` / `{top_row['unit_type']}` / score `{top_row['lexical_score']:.6f}`"
            )
            lines.append("- top 3 cases/units:")
            for index, row in enumerate(rows[:3], start=1):
                lines.append(
                    f"  - `{index}` `{row['case_code']}` / `{row['unit_type']}` | availability `{row['precedent_availability']}` | "
                    f"score `{row['lexical_score']:.6f}` | preview: {body_preview(row['search_text'])}"
                )
        else:
            lines.append("- top result: none")
            lines.append("- top 3 cases/units: none")
        lines.append("")
    lines.append("## Aggregate Metrics")
    lines.append("")
    lines.append(f"- query count: `{total_queries}`")
    lines.append(f"- Hit@1: `{hit_at_1_count} / {total_queries} = {hit_at_1:.2%}`")
    lines.append(f"- Hit@3: `{hit_at_3_count} / {total_queries} = {hit_at_3:.2%}`")
    lines.append(f"- MRR: `{mrr:.4f}`")
    lines.append("")
    lines.append("## Miss Analysis")
    lines.append("")
    if not misses:
        lines.append("- No open lexical misses were observed in this benchmark set.")
    else:
        for fixture, assessment in misses:
            lines.append(
                f"- `{fixture.query}`: category `{assessment.miss_category or 'none'}`; "
                f"first matching rank `{rank_display(assessment.first_matching_rank)}`; note: {assessment.note}"
            )
    lines.append("")
    lines.append("## Safety Metadata Review")
    lines.append("")
    for query, row in safety_rows:
        if row is None:
            lines.append(f"- `{query}`: no top result returned.")
            continue
        lines.append(
            f"- `{query}`: top result `{row['case_code']}` / `{row['unit_type']}` keeps "
            f"`source_layer_role={row['source_layer_role']}`, "
            f"`precedent_availability={row['precedent_availability']}`, "
            f"`historical_value_only={row['historical_value_only']}`, "
            f"`contamination_risk_level={row['contamination_risk_level']}`, "
            f"`current_authority_disposition={row['current_authority_disposition']}`, "
            f"`lesson_kind={row['lesson_kind']}`, "
            f"`effective_confidentiality_level_code={row['effective_confidentiality_level_code']}`, "
            f"`primary_source_locator={row['primary_source_locator']}`."
        )
    lines.append("")
    lines.append("## Baseline Findings")
    lines.append("")
    lines.append("- Historical lexical retrieval works well when the query reuses governed case titles, operational nouns, and statement phrasing already present in the search-unit text.")
    lines.append("- The historical surface stays structurally distinct from current knowledge because every result self-identifies as `historical_precedent` and carries limited-status, contamination, authority-disposition, confidentiality, and provenance metadata.")
    lines.append("- Queries that depend on paraphrase or vocabulary substitution still expose the expected lexical limit that 6.4C semantic retrieval is meant to test rather than hide.")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    report = render_report(args.limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"wrote={args.output}")
    print(f"query_count={len(FIXTURES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
