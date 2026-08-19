from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from tools.phase_05_chunking.generate_pilot import run_supabase_query

from .evaluate_semantic import (
    FIXTURES as LIVE_FIXTURES,
    build_config_from_registry,
    load_active_retrieval_model,
    run_fts_search,
    run_semantic_search,
)
from .semantic_common import (
    OpenAIEmbeddingsClient,
    assessment_rank,
    assess_search_results,
    embed_query_text,
)


@dataclass(frozen=True)
class ResultRow:
    query: str
    source: str
    rank: int
    document_code: str
    document_title: str
    section_heading: str
    score_label: str
    score_value: float
    preview: str
    chunk_id: int | None = None

    @property
    def candidate_key(self) -> tuple[str, str]:
        return (self.document_code, self.section_heading)


@dataclass(frozen=True)
class SectionMatcher:
    document_code: str
    section_fragments: tuple[str, ...] = ()

    def matches(self, row: ResultRow) -> bool:
        if row.document_code != self.document_code:
            return False
        if not self.section_fragments:
            return True
        section = row.section_heading.lower()
        return any(fragment.lower() in section for fragment in self.section_fragments)


@dataclass(frozen=True)
class RetrievalFixture:
    query: str
    preferred: tuple[SectionMatcher, ...]
    acceptable: tuple[SectionMatcher, ...]
    note: str


@dataclass(frozen=True)
class PolicyConfig:
    policy_code: str
    display_name: str
    strategy: str
    rrf_k: int = 20
    category_modifiers: tuple[tuple[str, float], ...] = ()
    document_rule_link_boost: float = 0.0
    chunk_rule_link_boost: float = 0.0


@dataclass(frozen=True)
class PolicyMetrics:
    policy_code: str
    display_name: str
    queries: int
    hit_at_1: int
    hit_at_3: int
    preferred_before_secondary: int
    relevant_at_5: float


@dataclass(frozen=True)
class CaseSummary:
    top_code: str | None
    top_section: str | None
    top_status: str
    preferred_in_top_3: bool


@dataclass(frozen=True)
class DocumentMetadata:
    document_code: str
    category_code: str
    authority_classification: str
    document_rule_links: int
    chunk_rule_links: int


REPORT_SECTION_RE = re.compile(r"^### `(.+?)`$")
RESULT_LINE_RE = re.compile(
    r"^  - `(?P<rank>\d+)` `(?P<document_code>[^`]+)` (?P<document_title>.+?) \| "
    r"section `(?P<section_heading>.+?)` \| (?P<score_label>rank|similarity) `(?P<score_value>[-0-9.]+)`"
)


FIXTURES: tuple[RetrievalFixture, ...] = (
    RetrievalFixture(
        query="external caterer",
        preferred=(
            SectionMatcher("SERV-003", ("external caterer", "external caterers")),
            SectionMatcher("SERV-004", ("external caterer",)),
        ),
        acceptable=(SectionMatcher("TPL-006", ("external supplier information request",)),),
        note="Exact external-catering guidance should rank above adjacent supplier context.",
    ),
    RetrievalFixture(
        query="can we bring our own catering",
        preferred=(
            SectionMatcher("SERV-003", ("external caterer", "external caterers")),
            SectionMatcher("SERV-004", ("external caterer",)),
            SectionMatcher("TPL-006", ("external supplier information request",)),
        ),
        acceptable=(SectionMatcher("CF-007", ("catering, suppliers and facilitators",)),),
        note="Explicit external-catering guidance should outrank adjacent kitchen or general supplier clauses.",
    ),
    RetrievalFixture(
        query="payment within 14 days",
        preferred=(
            SectionMatcher("CF-003", ("short-notice bookings",)),
            SectionMatcher("CF-005", ("payment terms",)),
            SectionMatcher("CF-007", ("fees, payment and security deposit", "payment plan")),
            SectionMatcher("TPL-006", ("balance payment reminder", "final balance reminder")),
        ),
        acceptable=(
            SectionMatcher("GOV-002", ("confirmation payment for bookings within 14 days", "confirmation payment for bookings under 30 days")),
        ),
        note="Operational payment sources should rank above governance history while keeping governance visible.",
    ),
    RetrievalFixture(
        query="when does the remaining balance need to be paid",
        preferred=(
            SectionMatcher("TPL-006", ("balance payment reminder",)),
            SectionMatcher("CF-005", ("payment terms",)),
            SectionMatcher("CF-007", ("payment plan", "fees, payment and security deposit")),
            SectionMatcher("CF-003", ("payments via storefront",)),
        ),
        acceptable=(SectionMatcher("GOV-002", ("remaining balance deadline",)),),
        note="Paraphrase retrieval should recover direct operational balance guidance.",
    ),
    RetrievalFixture(
        query="site visit",
        preferred=(
            SectionMatcher("TPL-008"),
            SectionMatcher("TPL-006", ("site visit",)),
            SectionMatcher("TPL-009", ("space & set-up", "access & operations")),
        ),
        acceptable=(SectionMatcher("GOV-002", ("site-visit requirement",)),),
        note="Operational site-visit guidance should dominate generic governance context.",
    ),
    RetrievalFixture(
        query="can we visit the venue beforehand",
        preferred=(
            SectionMatcher("TPL-008"),
            SectionMatcher("TPL-006", ("site visit",)),
            SectionMatcher("TPL-007", ("site visit",)),
        ),
        acceptable=(
            SectionMatcher("CF-005", ("access", "appointment-only")),
            SectionMatcher("CF-003", ("appointment-only", "access")),
        ),
        note="Specific site-visit guidance should outrank broader access clauses for this procedural paraphrase.",
    ),
    RetrievalFixture(
        query="setup and breakdown",
        preferred=(
            SectionMatcher("CF-007", ("build-up and breakdown",)),
            SectionMatcher("TPL-009", ("space & set-up", "access & operations")),
            SectionMatcher("SERV-001", ("set-up support", "breakdown and reset support")),
        ),
        acceptable=(
            SectionMatcher("CF-003", ("access",)),
            SectionMatcher("TPL-001"),
            SectionMatcher("TPL-002"),
            SectionMatcher("TPL-003"),
            SectionMatcher("TPL-004"),
            SectionMatcher("TPL-005"),
        ),
        note="Direct operational set-up/breakdown guidance should rank above general adjacent planning text.",
    ),
    RetrievalFixture(
        query="projector",
        preferred=(
            SectionMatcher("OPS-002", ("projection",)),
        ),
        acceptable=(
            SectionMatcher("SERV-001", ("technical coordination",)),
            SectionMatcher("CF-007", ("technical and installation requirements",)),
        ),
        note="Technical inventory should dominate direct equipment nouns.",
    ),
    RetrievalFixture(
        query="cancellation",
        preferred=(
            SectionMatcher("TPL-006", ("cancellation response",)),
            SectionMatcher("CF-007", ("cancellation",)),
            SectionMatcher("CF-005", ("cancellation policy",)),
            SectionMatcher("CF-003", ("cancellation policy",)),
        ),
        acceptable=(SectionMatcher("GOV-002", ("cancellation",)),),
        note="Current cancellation guidance should rank above governance-history context.",
    ),
    RetrievalFixture(
        query="supported rental",
        preferred=(SectionMatcher("SERV-001", ("supported rental",)),),
        acceptable=(),
        note="The exact supported-rental service definition should remain first.",
    ),
    RetrievalFixture(
        query="security deposit",
        preferred=(
            SectionMatcher("CF-007", ("security deposit and inspection",)),
            SectionMatcher("CF-005", ("security deposit",)),
            SectionMatcher("CF-003", ("security deposit",)),
        ),
        acceptable=(
            SectionMatcher("GOV-002", ("security deposit",)),
            SectionMatcher("TPL-013"),
        ),
        note="Direct client-facing deposit clauses should outrank governance summaries.",
    ),
    RetrievalFixture(
        query="sparkling water",
        preferred=(SectionMatcher("SERV-003", ("sparkling water",)),),
        acceptable=(),
        note="Concrete beverage catalogue terminology should remain straightforward.",
    ),
    RetrievalFixture(
        query="facilitator sourcing",
        preferred=(
            SectionMatcher("SERV-001", ("facilitator sourcing",)),
            SectionMatcher("TPL-006", ("facilitator confirmation",)),
        ),
        acceptable=(SectionMatcher("CF-007", ("catering, suppliers and facilitators",)),),
        note="Direct facilitator-sourcing guidance should rank above adjacent supplier context.",
    ),
)


POLICIES: tuple[PolicyConfig, ...] = (
    PolicyConfig(
        policy_code="fts_first_append_semantic",
        display_name="FTS-first Append Semantic",
        strategy="fts_first_append_semantic",
    ),
    PolicyConfig(
        policy_code="semantic_first_append_fts",
        display_name="Semantic-first Append FTS",
        strategy="semantic_first_append_fts",
    ),
    PolicyConfig(
        policy_code="rrf_unweighted",
        display_name="RRF Unweighted",
        strategy="rrf",
        rrf_k=20,
    ),
    PolicyConfig(
        policy_code="rrf_policy_weighted",
        display_name="RRF With Governed Policy Modifiers",
        strategy="rrf",
        rrf_k=20,
        category_modifiers=(
            ("operational_procedure", 0.011),
            ("communication_guidance", 0.009),
            ("service_supplier_guidance", 0.007),
            ("technical_venue_reference", 0.007),
            ("client_facing_controlled_document", 0.005),
            ("proposal_guidance", 0.001),
            ("governance_canonical", -0.010),
        ),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate deterministic retrieval-policy candidates for Phase 5.")
    parser.add_argument(
        "--semantic-report",
        type=Path,
        default=Path("docs/phase-05/search/phase-05-semantic-search-evaluation.md"),
        help="Semantic evaluation report to parse when running in report mode.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/phase-05/search/phase-05-retrieval-policy-evaluation.md"),
        help="Markdown report path to write.",
    )
    parser.add_argument(
        "--mode",
        choices=("report", "live"),
        default="report",
        help="Use the approved semantic report or execute live FTS + semantic retrieval.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum top results to compare.",
    )
    return parser.parse_args()


def parse_report_results(report_path: Path) -> dict[str, dict[str, list[ResultRow]]]:
    text = report_path.read_text(encoding="utf-8")
    current_query: str | None = None
    current_source: str | None = None
    parsed: dict[str, dict[str, list[ResultRow]]] = {}

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        query_match = REPORT_SECTION_RE.match(line)
        if query_match:
            current_query = query_match.group(1)
            parsed[current_query] = {"fts": [], "semantic": []}
            current_source = None
            continue
        if current_query is None:
            continue
        if line == "- FTS top results:":
            current_source = "fts"
            continue
        if line == "- semantic top results:":
            current_source = "semantic"
            continue
        if current_source is None or line.strip() == "- none":
            continue
        match = RESULT_LINE_RE.match(line)
        if not match:
            continue
        parsed[current_query][current_source].append(
            ResultRow(
                query=current_query,
                source=current_source,
                rank=int(match.group("rank")),
                document_code=match.group("document_code"),
                document_title=match.group("document_title"),
                section_heading=match.group("section_heading"),
                score_label=match.group("score_label"),
                score_value=float(match.group("score_value")),
                preview="",
            )
        )
    return parsed


def load_live_results(limit: int) -> dict[str, dict[str, list[ResultRow]]]:
    model = load_active_retrieval_model()
    config = build_config_from_registry(model)
    client = OpenAIEmbeddingsClient()
    parsed: dict[str, dict[str, list[ResultRow]]] = {}
    for fixture in LIVE_FIXTURES:
        fts_rows = run_fts_search(fixture.query, limit).rows
        query_vector = embed_query_text(client, fixture.query, config)
        semantic_rows = run_semantic_search(query_vector, limit, model["id"]).rows
        parsed[fixture.query] = {
            "fts": [
                ResultRow(
                    query=fixture.query,
                    source="fts",
                    rank=index,
                    document_code=row["document_code"],
                    document_title=row["document_title"],
                    section_heading=row["section_heading"] or "(no section heading)",
                    score_label="rank",
                    score_value=float(row["relevance_score"]),
                    preview=row["body_text"],
                    chunk_id=row.get("chunk_id"),
                )
                for index, row in enumerate(fts_rows, start=1)
            ],
            "semantic": [
                ResultRow(
                    query=fixture.query,
                    source="semantic",
                    rank=index,
                    document_code=row["document_code"],
                    document_title=row["document_title"],
                    section_heading=row["section_heading"] or "(no section heading)",
                    score_label="similarity",
                    score_value=float(row["similarity_score"]),
                    preview=row["body_text"],
                    chunk_id=row.get("chunk_id"),
                )
                for index, row in enumerate(semantic_rows, start=1)
            ],
        }
    return parsed


def load_document_metadata(document_codes: set[str]) -> dict[str, DocumentMetadata]:
    quoted_codes = ", ".join("'" + code.replace("'", "''") + "'" for code in sorted(document_codes))
    sql = f"""
with doc_rule_counts as (
  select
    kd.document_code,
    count(distinct kdvlr.rule_code)::integer as document_rule_links
  from public.knowledge_documents kd
  join public.knowledge_document_versions kdv
    on kdv.document_id = kd.id
  left join public.knowledge_document_version_logical_rules kdvlr
    on kdvlr.document_version_id = kdv.id
  group by kd.document_code
),
chunk_rule_counts as (
  select
    ckc.document_code,
    count(distinct kclr.rule_code)::integer as chunk_rule_links
  from private.current_knowledge_chunks ckc
  left join private.knowledge_chunk_logical_rules kclr
    on kclr.chunk_id = ckc.chunk_id
  group by ckc.document_code
)
select
  kd.document_code,
  kcat.category_code,
  kdv.authority_classification,
  coalesce(drc.document_rule_links, 0) as document_rule_links,
  coalesce(crc.chunk_rule_links, 0) as chunk_rule_links
from public.knowledge_documents kd
join public.knowledge_categories kcat
  on kcat.id = kd.primary_category_id
join public.knowledge_document_versions kdv
  on kdv.document_id = kd.id
left join doc_rule_counts drc
  on drc.document_code = kd.document_code
left join chunk_rule_counts crc
  on crc.document_code = kd.document_code
where kd.document_code in ({quoted_codes})
order by kd.document_code;
""".strip()
    rows = run_supabase_query(sql, expect_json=True)["rows"]
    return {
        row["document_code"]: DocumentMetadata(
            document_code=row["document_code"],
            category_code=row["category_code"],
            authority_classification=row["authority_classification"],
            document_rule_links=row["document_rule_links"],
            chunk_rule_links=row["chunk_rule_links"],
        )
        for row in rows
    }


def dedupe_rows(rows: list[ResultRow]) -> list[ResultRow]:
    seen: set[tuple[str, str]] = set()
    deduped: list[ResultRow] = []
    for row in rows:
        if row.candidate_key in seen:
            continue
        seen.add(row.candidate_key)
        deduped.append(row)
    return deduped


def apply_policy(
    policy: PolicyConfig,
    fts_rows: list[ResultRow],
    semantic_rows: list[ResultRow],
    metadata: dict[str, DocumentMetadata],
    limit: int,
) -> list[ResultRow]:
    if policy.strategy == "fts_first_append_semantic":
        return dedupe_rows(fts_rows + semantic_rows)[:limit]
    if policy.strategy == "semantic_first_append_fts":
        return dedupe_rows(semantic_rows + fts_rows)[:limit]

    scored: dict[tuple[str, str], tuple[ResultRow, float]] = {}
    rrf_k = policy.rrf_k
    category_modifier_map = dict(policy.category_modifiers)

    def add_row(row: ResultRow, reciprocal_rank: int) -> None:
        base_score = 1.0 / (rrf_k + reciprocal_rank)
        meta = metadata[row.document_code]
        modifier = category_modifier_map.get(meta.category_code, 0.0)
        if policy.document_rule_link_boost and meta.document_rule_links > 0:
            modifier += policy.document_rule_link_boost
        if policy.chunk_rule_link_boost and meta.chunk_rule_links > 0:
            modifier += policy.chunk_rule_link_boost
        total = base_score + modifier
        existing = scored.get(row.candidate_key)
        if existing is None:
            scored[row.candidate_key] = (row, total)
        else:
            scored[row.candidate_key] = (existing[0], existing[1] + total)

    for row in fts_rows:
        add_row(row, row.rank)
    for row in semantic_rows:
        add_row(row, row.rank)

    ordered = sorted(
        ((value[0], value[1]) for value in scored.values()),
        key=lambda item: (
            -item[1],
            item[0].document_code,
            item[0].section_heading,
        ),
    )
    result: list[ResultRow] = []
    for index, (row, score) in enumerate(ordered[:limit], start=1):
        result.append(
            ResultRow(
                query=row.query,
                source=policy.policy_code,
                rank=index,
                document_code=row.document_code,
                document_title=row.document_title,
                section_heading=row.section_heading,
                score_label="policy_score",
                score_value=score,
                preview=row.preview,
                chunk_id=row.chunk_id,
            )
        )
    return result


def result_status(row: ResultRow, fixture: RetrievalFixture) -> str:
    if any(matcher.matches(row) for matcher in fixture.preferred):
        return "preferred"
    if any(matcher.matches(row) for matcher in fixture.acceptable):
        return "acceptable"
    return "irrelevant"


def compute_metrics(policy: PolicyConfig, results_by_query: dict[str, list[ResultRow]]) -> PolicyMetrics:
    hit_at_1 = 0
    hit_at_3 = 0
    preferred_before_secondary = 0
    relevant_at_5_total = 0.0

    for fixture in FIXTURES:
        rows = results_by_query[fixture.query]
        statuses = [result_status(row, fixture) for row in rows[:5]]
        if statuses and statuses[0] == "preferred":
            hit_at_1 += 1
        if "preferred" in statuses[:3]:
            hit_at_3 += 1
        relevant_at_5_total += sum(1 for status in statuses if status in {"preferred", "acceptable"}) / 5.0

        first_preferred = next((idx for idx, status in enumerate(statuses, start=1) if status == "preferred"), None)
        first_acceptable = next((idx for idx, status in enumerate(statuses, start=1) if status == "acceptable"), None)
        if first_preferred is not None and (first_acceptable is None or first_preferred < first_acceptable):
            preferred_before_secondary += 1

    return PolicyMetrics(
        policy_code=policy.policy_code,
        display_name=policy.display_name,
        queries=len(FIXTURES),
        hit_at_1=hit_at_1,
        hit_at_3=hit_at_3,
        preferred_before_secondary=preferred_before_secondary,
        relevant_at_5=round(relevant_at_5_total / len(FIXTURES), 3),
    )


def compute_baseline_metrics(
    source: str,
    display_name: str,
    raw_results: dict[str, dict[str, list[ResultRow]]],
) -> PolicyMetrics:
    results_by_query = {fixture.query: raw_results[fixture.query][source] for fixture in FIXTURES}
    pseudo_policy = PolicyConfig(policy_code=source, display_name=display_name, strategy="fts_first_append_semantic")
    return compute_metrics(pseudo_policy, results_by_query)


def policy_case_summary(rows: list[ResultRow], fixture: RetrievalFixture) -> CaseSummary:
    top = rows[0] if rows else None
    statuses = [result_status(row, fixture) for row in rows[:3]]
    return CaseSummary(
        top_code=None if top is None else top.document_code,
        top_section=None if top is None else top.section_heading,
        top_status="none" if top is None else result_status(top, fixture),
        preferred_in_top_3="preferred" in statuses,
    )


def choose_recommendation(metrics: list[PolicyMetrics]) -> str:
    preferred_order = sorted(
        metrics,
        key=lambda item: (item.hit_at_1, item.hit_at_3, item.preferred_before_secondary, item.relevant_at_5),
        reverse=True,
    )
    if len(preferred_order) < 2:
        return preferred_order[0].policy_code
    leader = preferred_order[0]
    runner_up = preferred_order[1]
    if (
        leader.hit_at_1 == runner_up.hit_at_1
        and leader.hit_at_3 == runner_up.hit_at_3
        and leader.preferred_before_secondary == runner_up.preferred_before_secondary
        and leader.relevant_at_5 == runner_up.relevant_at_5
    ):
        return "RETRIEVAL_POLICY_REQUIRES_FURTHER_REVIEW"
    return leader.policy_code


def render_markdown(
    *,
    mode: str,
    raw_results: dict[str, dict[str, list[ResultRow]]],
    policy_results: dict[str, dict[str, list[ResultRow]]],
    baseline_metrics: list[PolicyMetrics],
    metrics: list[PolicyMetrics],
    recommendation: str,
) -> str:
    def append_row_block(lines: list[str], rows: list[ResultRow]) -> None:
        if not rows:
            lines.append("  - none")
            return
        for row in rows:
            lines.append(
                f"  - `{row.rank}` `{row.document_code}` | section `{row.section_heading}` | "
                f"{row.score_label} `{row.score_value:.6f}`"
            )

    baseline_metrics_by_code = {item.policy_code: item for item in baseline_metrics}
    metrics_by_code = {item.policy_code: item for item in metrics}
    recommendation_name = recommendation
    for policy in POLICIES:
        if policy.policy_code == recommendation:
            recommendation_name = policy.display_name
            break

    lines: list[str] = []
    lines.append("# Phase 5 Retrieval Policy Evaluation")
    lines.append("")
    lines.append(f"Date: {date.today():%B %-d, %Y}")
    lines.append("")
    lines.append("## Evaluation Mode")
    lines.append("")
    lines.append(f"- mode: `{mode}`")
    lines.append("- retrieval evidence source: approved Phase 5 FTS + semantic comparison results")
    lines.append("- evaluation fixture count: `13`")
    lines.append("")
    lines.append("## Candidate Strategies")
    lines.append("")
    for policy in POLICIES:
        lines.append(f"- `{policy.policy_code}`: {policy.display_name}")
    lines.append("")
    lines.append("## Baseline Substrates")
    lines.append("")
    lines.append("| Retrieval Layer | Hit@1 | Hit@3 | Preferred Before Secondary | Relevant@5 |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    for baseline in baseline_metrics:
        lines.append(
            f"| {baseline.display_name} | {baseline.hit_at_1}/{baseline.queries} | "
            f"{baseline.hit_at_3}/{baseline.queries} | {baseline.preferred_before_secondary}/{baseline.queries} | "
            f"{baseline.relevant_at_5:.3f} |"
        )
    lines.append("")
    lines.append("## Metrics")
    lines.append("")
    lines.append("| Policy | Hit@1 | Hit@3 | Preferred Before Secondary | Relevant@5 |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    for policy in POLICIES:
        metric = metrics_by_code[policy.policy_code]
        lines.append(
            f"| {policy.display_name} | {metric.hit_at_1}/{metric.queries} | {metric.hit_at_3}/{metric.queries} | "
            f"{metric.preferred_before_secondary}/{metric.queries} | {metric.relevant_at_5:.3f} |"
        )
    lines.append("")
    lines.append("## Known Cases")
    lines.append("")
    for query in (
        "payment within 14 days",
        "can we bring our own catering",
        "can we visit the venue beforehand",
        "security deposit",
    ):
        fixture = next(item for item in FIXTURES if item.query == query)
        lines.append(f"### `{query}`")
        lines.append("")
        lines.append(f"- fixture note: {fixture.note}")
        for baseline_code, baseline_name in (("fts", "FTS"), ("semantic", "Semantic")):
            summary = policy_case_summary(raw_results[query][baseline_code], fixture)
            lines.append(
                f"- {baseline_name}: top `{summary.top_code}` / `{summary.top_section}` "
                f"status `{summary.top_status}` | preferred in top 3: `{summary.preferred_in_top_3}`"
            )
        for policy in POLICIES:
            summary = policy_case_summary(policy_results[policy.policy_code][query], fixture)
            lines.append(
                f"- {policy.display_name}: top `{summary.top_code}` / `{summary.top_section}` "
                f"status `{summary.top_status}` | preferred in top 3: `{summary.preferred_in_top_3}`"
            )
        lines.append("")
    lines.append("## Recommendation")
    lines.append("")
    if recommendation == "RETRIEVAL_POLICY_REQUIRES_FURTHER_REVIEW":
        lines.append("- result: `RETRIEVAL_POLICY_REQUIRES_FURTHER_REVIEW`")
    else:
        lines.append(f"- recommended policy: `{recommendation_name}`")
        lines.append(f"- policy code: `{recommendation}`")
    lines.append("")
    lines.append("## Diagnostic Query Snapshots")
    lines.append("")
    for query in ("payment within 14 days", "when does the remaining balance need to be paid", "can we visit the venue beforehand"):
        lines.append(f"### `{query}`")
        lines.append("")
        lines.append("- FTS:")
        append_row_block(lines, raw_results[query]["fts"][:3])
        lines.append("- Semantic:")
        append_row_block(lines, raw_results[query]["semantic"][:3])
        for policy in POLICIES:
            lines.append(f"- {policy.display_name}:")
            append_row_block(lines, policy_results[policy.policy_code][query][:3])
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    if args.mode == "live":
        raw_results = load_live_results(args.limit)
    else:
        raw_results = parse_report_results(args.semantic_report)

    all_codes = {
        row.document_code
        for per_query in raw_results.values()
        for rows in per_query.values()
        for row in rows
    }
    metadata = load_document_metadata(all_codes)
    baseline_metrics = [
        compute_baseline_metrics("fts", "FTS", raw_results),
        compute_baseline_metrics("semantic", "Semantic", raw_results),
    ]

    policy_results: dict[str, dict[str, list[ResultRow]]] = {}
    metrics: list[PolicyMetrics] = []
    for policy in POLICIES:
        per_query: dict[str, list[ResultRow]] = {}
        for fixture in FIXTURES:
            fts_rows = raw_results[fixture.query]["fts"]
            semantic_rows = raw_results[fixture.query]["semantic"]
            per_query[fixture.query] = apply_policy(policy, fts_rows, semantic_rows, metadata, args.limit)
        policy_results[policy.policy_code] = per_query
        metrics.append(compute_metrics(policy, per_query))

    recommendation = choose_recommendation(metrics)
    output = render_markdown(
        mode=args.mode,
        raw_results=raw_results,
        policy_results=policy_results,
        baseline_metrics=baseline_metrics,
        metrics=metrics,
        recommendation=recommendation,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    print(f"Wrote {args.output}")
    print(f"Recommendation: {recommendation}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
