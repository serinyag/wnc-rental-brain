from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from tools.phase_05_chunking.generate_pilot import run_supabase_query, sql_text


@dataclass(frozen=True)
class SearchFixture:
    query: str
    expected_codes: tuple[str, ...]
    discouraged_codes: tuple[str, ...] = ()
    note: str = ""


@dataclass(frozen=True)
class SearchAssessment:
    status: str
    explanation: str


FIXTURES: tuple[SearchFixture, ...] = (
    SearchFixture(
        query="external caterer",
        expected_codes=("SERV-003", "SERV-004"),
        note="Supplier and catering guidance should dominate this exact operational term.",
    ),
    SearchFixture(
        query="payment within 14 days",
        expected_codes=("CF-003", "CF-005", "CF-007", "TPL-006"),
        note="Current payment timing language appears across client-facing terms, the agreement template, and related communication guidance.",
    ),
    SearchFixture(
        query="site visit",
        expected_codes=("TPL-008", "TPL-006", "TPL-009"),
        note="Checklist and communication guidance should outrank unrelated corpora.",
    ),
    SearchFixture(
        query="setup and breakdown",
        expected_codes=("TPL-009", "CF-007", "TPL-001", "TPL-002", "TPL-003", "TPL-004", "TPL-005"),
        note="Current searchable knowledge cannot rely on OPS-001 because the preserved pilot remains draft and is excluded by the eligibility surface.",
    ),
    SearchFixture(
        query="projector",
        expected_codes=("OPS-002", "TPL-009", "SERV-001"),
        note="Technical inventory should normally dominate named venue-equipment queries.",
    ),
    SearchFixture(
        query="client cancellation",
        expected_codes=("CF-003", "CF-005", "TPL-006", "CF-007"),
        note="Chunk search does not include the Phase 4 deterministic cancellation tables, so current chunked guidance is the relevant baseline.",
    ),
    SearchFixture(
        query="supported rental",
        expected_codes=("SERV-001",),
        note="This is an exact current service-catalogue term.",
    ),
    SearchFixture(
        query="security deposit",
        expected_codes=("CF-007", "TPL-013", "CF-005"),
        note="Agreement, close-out, and full-venue terms are the most likely current chunk families.",
    ),
    SearchFixture(
        query="sparkling water",
        expected_codes=("SERV-003",),
        note="Beverage catalogue guidance should win this exact product query.",
    ),
    SearchFixture(
        query="facilitator sourcing",
        expected_codes=("SERV-001", "TPL-006"),
        note="Service catalogue and communication guidance both contain current facilitator wording.",
    ),
    SearchFixture(
        query="Can we bring an external caterer?",
        expected_codes=("SERV-003", "SERV-004"),
        note="This is a natural-language query intended to show the English web-search parser baseline.",
    ),
    SearchFixture(
        query="payment due within 14 days",
        expected_codes=("CF-003", "CF-005", "CF-007", "TPL-006"),
        note="Natural phrasing should still find current payment-timing language without embeddings.",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate the Phase 5 full-text search baseline on the current chunk corpus.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/phase-05/search/phase-05-fts-evaluation.md"),
        help="Markdown report path to write.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of top results to capture per query.",
    )
    return parser.parse_args()


def fetch_searchable_corpus_summary() -> dict[str, int]:
    sql = """
select
  count(*)::integer as searchable_chunks,
  count(distinct chunk_set_id)::integer as searchable_chunk_sets,
  count(distinct document_code)::integer as searchable_documents
from private.current_knowledge_chunks;
""".strip()
    payload = run_supabase_query(sql, expect_json=True)
    row = payload["rows"][0]
    if row["searchable_chunks"] == 0:
        raise SystemExit("No searchable current chunks were found. Run bulk chunk generation before evaluating FTS.")
    return row


def run_search(query: str, limit: int) -> list[dict]:
    sql = f"""
select
  chunk_id,
  document_code,
  document_title,
  document_version_id,
  document_version_number,
  chunk_ordinal,
  section_heading,
  heading_path,
  body_text,
  relevance_score,
  primary_source_locator,
  primary_category_code
from private.search_knowledge_chunks(
  {sql_text(query)},
  {limit}
);
""".strip()
    payload = run_supabase_query(sql, expect_json=True)
    return payload["rows"]


def assess_fixture(fixture: SearchFixture, rows: list[dict]) -> SearchAssessment:
    if not rows:
        return SearchAssessment("miss", "No ranked results were returned.")

    top_code = rows[0]["document_code"]
    top_three_codes = [row["document_code"] for row in rows[:3]]
    all_codes = [row["document_code"] for row in rows]

    if top_code in fixture.discouraged_codes:
        return SearchAssessment("weak", f"Top result {top_code} is explicitly discouraged for this query.")
    if top_code in fixture.expected_codes:
        return SearchAssessment("strong", f"Top result {top_code} is in the expected document family.")
    if any(code in fixture.expected_codes for code in top_three_codes):
        expected_hits = ", ".join(code for code in top_three_codes if code in fixture.expected_codes)
        return SearchAssessment("partial", f"Expected code(s) {expected_hits} appear in the top three, but not at rank one.")
    if any(code in fixture.expected_codes for code in all_codes):
        expected_hits = ", ".join(code for code in all_codes if code in fixture.expected_codes)
        return SearchAssessment("weak", f"Expected code(s) {expected_hits} appear lower in the result list.")
    return SearchAssessment("miss", "No expected document family appeared in the captured result window.")


def body_preview(body_text: str, limit: int = 150) -> str:
    compact = " ".join(body_text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def render_report(limit: int) -> str:
    summary = fetch_searchable_corpus_summary()
    report_rows: list[tuple[SearchFixture, SearchAssessment, list[dict]]] = []
    for fixture in FIXTURES:
        rows = run_search(fixture.query, limit)
        report_rows.append((fixture, assess_fixture(fixture, rows), rows))

    strong = [fixture.query for fixture, assessment, _ in report_rows if assessment.status == "strong"]
    partial = [fixture.query for fixture, assessment, _ in report_rows if assessment.status == "partial"]
    weak = [fixture.query for fixture, assessment, _ in report_rows if assessment.status == "weak"]
    misses = [fixture.query for fixture, assessment, _ in report_rows if assessment.status == "miss"]

    lines: list[str] = []
    lines.append("# Phase 5 FTS Evaluation")
    lines.append("")
    lines.append(f"Date: {date.today():%B %-d, %Y}")
    lines.append("")
    lines.append("## Configuration")
    lines.append("")
    lines.append("- PostgreSQL text-search configuration: `english`")
    lines.append("- query parser: `websearch_to_tsquery`")
    lines.append("- ranking function: `ts_rank_cd`")
    lines.append("- weighting:")
    lines.append("  - `A`: document title snapshot")
    lines.append("  - `B`: section heading, heading path, question label")
    lines.append("  - `D`: body text")
    lines.append("- searchable corpus surface: `private.current_knowledge_chunks`")
    lines.append("")
    lines.append("## Searchable Corpus")
    lines.append("")
    lines.append(f"- searchable current documents: `{summary['searchable_documents']}`")
    lines.append(f"- searchable current chunk sets: `{summary['searchable_chunk_sets']}`")
    lines.append(f"- searchable current chunks: `{summary['searchable_chunks']}`")
    lines.append(f"- top results captured per query: `{limit}`")
    lines.append("")
    lines.append("## Evaluation Summary")
    lines.append("")
    lines.append(f"- strong: `{len(strong)}`")
    lines.append(f"- partial: `{len(partial)}`")
    lines.append(f"- weak: `{len(weak)}`")
    lines.append(f"- misses: `{len(misses)}`")
    if strong:
        lines.append(f"- obvious successes: `{', '.join(strong)}`")
    if partial or weak:
        lines.append(f"- weak ranking cases: `{', '.join(partial + weak)}`")
    if misses:
        lines.append(f"- misses: `{', '.join(misses)}`")
    lines.append("")
    lines.append("## Query Results")
    lines.append("")

    for fixture, assessment, rows in report_rows:
        lines.append(f"### `{fixture.query}`")
        lines.append("")
        lines.append(f"- expected families: `{', '.join(fixture.expected_codes)}`")
        if fixture.note:
            lines.append(f"- fixture note: {fixture.note}")
        lines.append(f"- expected result assessment: `{assessment.status}`")
        lines.append(f"- assessment detail: {assessment.explanation}")
        if not rows:
            lines.append("- top results: none")
            lines.append("")
            continue
        lines.append("- top results:")
        for idx, row in enumerate(rows, start=1):
            section = row["section_heading"] or "(no section heading)"
            preview = body_preview(row["body_text"])
            lines.append(
                f"  - `{idx}` `{row['document_code']}` {row['document_title']} | "
                f"section `{section}` | rank `{row['relevance_score']:.6f}` | preview: {preview}"
            )
        lines.append("")

    lines.append("## Baseline Findings")
    lines.append("")
    lines.append("- FTS handles exact governed terminology, named services, concrete equipment nouns, and repeated operational phrases well.")
    lines.append("- Natural-language phrasing is usable because `websearch_to_tsquery` tolerates ordinary questions better than raw `to_tsquery` syntax.")
    lines.append("- Search quality is still bounded by the governed current chunk surface. For example, preserved draft chunk sets such as `OPS-001` remain intentionally excluded from current search even though they contain useful operational prose.")
    lines.append("- Queries that depend on synonymy, policy inference, or cross-document reasoning still show the expected semantic gap that later embedding work can evaluate against this baseline.")
    lines.append("")
    lines.append("## Likely Semantic-Search Follow-Ups")
    lines.append("")
    lines.append("- paraphrases that do not reuse governed vocabulary directly")
    lines.append("- policy questions that require combining multiple chunks across document families")
    lines.append("- requests whose best answer lives in current deterministic Phase 4 rule tables rather than in chunked narrative knowledge")
    lines.append("- nuanced operational questions where relevant evidence is split between checklists, catalogues, and client-facing terms")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    markdown = render_report(args.limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markdown, encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
