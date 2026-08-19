from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .evaluate_retrieval_policy import FIXTURES as ORIGINAL_FIXTURES
from .evaluate_retrieval_policy import ResultRow, RetrievalFixture, SectionMatcher, result_status
from .evaluate_semantic import (
    build_config_from_registry,
    fetch_coverage,
    load_active_retrieval_model,
    run_fts_search,
    run_semantic_search,
)
from .hybrid_common import APPROVED_RRF_K, DEFAULT_HYBRID_CANDIDATE_POOL_LIMIT
from .search_hybrid import run_hybrid_search
from .semantic_common import OpenAIEmbeddingsClient, embed_query_text


@dataclass(frozen=True)
class TimedResultRows:
    rows: list[ResultRow]
    embedding_ms: float
    retrieval_ms: float


@dataclass(frozen=True)
class MetricSummary:
    label: str
    queries: int
    hit_at_1: int
    hit_at_3: int
    preferred_before_secondary: int
    relevant_at_5: float


HOLDOUT_FIXTURES: tuple[RetrievalFixture, ...] = (
    RetrievalFixture(
        query="venue walkthrough before the event",
        preferred=(SectionMatcher("TPL-008"),),
        acceptable=(
            SectionMatcher("CF-005", ("access", "appointment-only")),
            SectionMatcher("CF-003", ("access", "appointment-only")),
        ),
        note="Operational site-visit guidance should still beat generic access language on a new paraphrase.",
    ),
    RetrievalFixture(
        query="outside supplier details",
        preferred=(
            SectionMatcher("TPL-006", ("external supplier information request",)),
            SectionMatcher("SERV-004", ("external caterer",)),
        ),
        acceptable=(
            SectionMatcher("SERV-003", ("external caterer", "external caterers")),
            SectionMatcher("CF-007", ("catering, suppliers and facilitators",)),
        ),
        note="Supplier-information phrasing should recover the operational request template rather than only adjacent supplier context.",
    ),
    RetrievalFixture(
        query="event manager support",
        preferred=(SectionMatcher("SERV-001", ("event manager",)),),
        acceptable=(SectionMatcher("SERV-001", ("supported rental",)),),
        note="A held-out service query should remain strongly anchored to the service catalogue.",
    ),
    RetrievalFixture(
        query="balance payment reminder",
        preferred=(SectionMatcher("TPL-006", ("balance payment reminder", "final balance reminder")),),
        acceptable=(
            SectionMatcher("CF-005", ("payment terms",)),
            SectionMatcher("CF-007", ("payment plan", "fees, payment and security deposit")),
            SectionMatcher("CF-003", ("payments via storefront",)),
        ),
        note="Held-out payment phrasing should preserve the template-first ordering for direct reminder language.",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate the production Phase 5 hybrid retrieval surface.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/phase-05/search/phase-05-hybrid-retrieval-evaluation.md"),
        help="Markdown report path to write.",
    )
    parser.add_argument("--limit", type=int, default=5, help="Top results to capture per query.")
    parser.add_argument(
        "--candidate-pool-limit",
        type=int,
        default=DEFAULT_HYBRID_CANDIDATE_POOL_LIMIT,
        help="Per-substrate candidate depth used by the production hybrid function.",
    )
    return parser.parse_args()


def convert_fts_rows(query: str, rows: list[dict]) -> list[ResultRow]:
    return [
        ResultRow(
            query=query,
            source="fts",
            rank=index,
            document_code=row["document_code"],
            document_title=row["document_title"],
            section_heading=row["section_heading"] or "(no section heading)",
            score_label="rank",
            score_value=float(row["relevance_score"]),
            preview=row["body_text"],
            chunk_id=row["chunk_id"],
        )
        for index, row in enumerate(rows, start=1)
    ]


def convert_semantic_rows(query: str, rows: list[dict]) -> list[ResultRow]:
    return [
        ResultRow(
            query=query,
            source="semantic",
            rank=index,
            document_code=row["document_code"],
            document_title=row["document_title"],
            section_heading=row["section_heading"] or "(no section heading)",
            score_label="similarity",
            score_value=float(row["similarity_score"]),
            preview=row["body_text"],
            chunk_id=row["chunk_id"],
        )
        for index, row in enumerate(rows, start=1)
    ]


def convert_hybrid_rows(query: str, rows: list[dict]) -> list[ResultRow]:
    return [
        ResultRow(
            query=query,
            source="hybrid",
            rank=index,
            document_code=row["document_code"],
            document_title=row["document_title"],
            section_heading=row["section_heading"] or "(no section heading)",
            score_label="final_score",
            score_value=float(row["final_score"]),
            preview=row["body_text"],
            chunk_id=row["chunk_id"],
        )
        for index, row in enumerate(rows, start=1)
    ]


def compute_metrics(fixtures: tuple[RetrievalFixture, ...], results_by_query: dict[str, list[ResultRow]], label: str) -> MetricSummary:
    hit_at_1 = 0
    hit_at_3 = 0
    preferred_before_secondary = 0
    relevant_at_5_total = 0.0

    for fixture in fixtures:
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

    return MetricSummary(
        label=label,
        queries=len(fixtures),
        hit_at_1=hit_at_1,
        hit_at_3=hit_at_3,
        preferred_before_secondary=preferred_before_secondary,
        relevant_at_5=round(relevant_at_5_total / len(fixtures), 3),
    )


def run_fixture_set(
    fixtures: tuple[RetrievalFixture, ...],
    *,
    limit: int,
    candidate_pool_limit: int,
) -> tuple[dict[str, list[ResultRow]], dict[str, list[ResultRow]], dict[str, list[ResultRow]], dict[str, float]]:
    model = load_active_retrieval_model()
    config = build_config_from_registry(model)
    client = OpenAIEmbeddingsClient()

    fts_results: dict[str, list[ResultRow]] = {}
    semantic_results: dict[str, list[ResultRow]] = {}
    hybrid_results: dict[str, list[ResultRow]] = {}
    timings = {
        "embedding_ms": 0.0,
        "fts_ms": 0.0,
        "semantic_ms": 0.0,
        "hybrid_ms": 0.0,
    }

    for fixture in fixtures:
        fts = run_fts_search(fixture.query, limit)
        started = time.perf_counter()
        query_vector = embed_query_text(client, fixture.query, config)
        embedding_ms = (time.perf_counter() - started) * 1000
        semantic = run_semantic_search(query_vector, limit, model["id"])
        hybrid_rows, hybrid_ms = run_hybrid_search(
            query_text=fixture.query,
            result_limit=limit,
            candidate_pool_limit=candidate_pool_limit,
            query_embedding=query_vector,
            embedding_model_id=model["id"],
        )

        fts_results[fixture.query] = convert_fts_rows(fixture.query, fts.rows)
        semantic_results[fixture.query] = convert_semantic_rows(fixture.query, semantic.rows)
        hybrid_results[fixture.query] = convert_hybrid_rows(fixture.query, hybrid_rows)

        timings["embedding_ms"] += embedding_ms
        timings["fts_ms"] += fts.elapsed_ms
        timings["semantic_ms"] += semantic.elapsed_ms
        timings["hybrid_ms"] += hybrid_ms

    query_count = len(fixtures)
    for key in timings:
        timings[key] = round(timings[key] / query_count, 2)

    return fts_results, semantic_results, hybrid_results, timings


def render_metric_table(metrics: list[MetricSummary]) -> list[str]:
    lines = [
        "| Retrieval Layer | Hit@1 | Hit@3 | Preferred Before Secondary | Relevant@5 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for metric in metrics:
        lines.append(
            f"| {metric.label} | {metric.hit_at_1}/{metric.queries} | {metric.hit_at_3}/{metric.queries} | "
            f"{metric.preferred_before_secondary}/{metric.queries} | {metric.relevant_at_5:.3f} |"
        )
    return lines


def append_result_block(lines: list[str], label: str, rows: list[ResultRow]) -> None:
    lines.append(f"- {label}:")
    if not rows:
        lines.append("  - none")
        return
    for row in rows[:3]:
        lines.append(
            f"  - `{row.rank}` `{row.document_code}` | section `{row.section_heading}` | "
            f"{row.score_label} `{row.score_value:.6f}`"
        )


def render_report(limit: int, candidate_pool_limit: int) -> str:
    coverage = fetch_coverage(load_active_retrieval_model()["id"])

    original_fts, original_semantic, original_hybrid, original_timings = run_fixture_set(
        ORIGINAL_FIXTURES,
        limit=limit,
        candidate_pool_limit=candidate_pool_limit,
    )
    holdout_fts, holdout_semantic, holdout_hybrid, holdout_timings = run_fixture_set(
        HOLDOUT_FIXTURES,
        limit=limit,
        candidate_pool_limit=candidate_pool_limit,
    )

    original_metrics = [
        compute_metrics(ORIGINAL_FIXTURES, original_fts, "FTS"),
        compute_metrics(ORIGINAL_FIXTURES, original_semantic, "Semantic"),
        compute_metrics(ORIGINAL_FIXTURES, original_hybrid, "Hybrid"),
    ]
    holdout_metrics = [
        compute_metrics(HOLDOUT_FIXTURES, holdout_fts, "FTS"),
        compute_metrics(HOLDOUT_FIXTURES, holdout_semantic, "Semantic"),
        compute_metrics(HOLDOUT_FIXTURES, holdout_hybrid, "Hybrid"),
    ]

    lines: list[str] = []
    lines.append("# Phase 5 Hybrid Retrieval Evaluation")
    lines.append("")
    lines.append(f"Date: {date.today():%B %-d, %Y}")
    lines.append("")
    lines.append("## Approved Policy Specification")
    lines.append("")
    lines.append(f"- retrieval policy: `rrf_policy_weighted`")
    lines.append(f"- RRF parameter: `k = {APPROVED_RRF_K}`")
    lines.append(f"- final result limit: `{limit}`")
    lines.append(f"- per-substrate candidate depth: `{candidate_pool_limit}`")
    lines.append("- governed category modifiers:")
    lines.append("  - `operational_procedure`: `+0.011`")
    lines.append("  - `communication_guidance`: `+0.009`")
    lines.append("  - `service_supplier_guidance`: `+0.007`")
    lines.append("  - `technical_venue_reference`: `+0.007`")
    lines.append("  - `client_facing_controlled_document`: `+0.005`")
    lines.append("  - `proposal_guidance`: `+0.001`")
    lines.append("  - `governance_canonical`: `-0.010`")
    lines.append("")
    lines.append("## Eligible Corpus")
    lines.append("")
    lines.append(f"- current eligible documents: `{coverage['eligible_documents']}`")
    lines.append(f"- current eligible chunks: `{coverage['eligible_chunks']}`")
    lines.append(f"- current approved embeddings: `{coverage['embedded_chunks']}`")
    lines.append(f"- embedding coverage: `{coverage['coverage_percent']}`%")
    lines.append("")
    lines.append("## Original 13-Query Fixture Metrics")
    lines.append("")
    lines.extend(render_metric_table(original_metrics))
    lines.append("")
    lines.append("## Holdout Metrics")
    lines.append("")
    lines.extend(render_metric_table(holdout_metrics))
    lines.append("")
    lines.append("## Diagnostic Query Results")
    lines.append("")
    for fixture in (
        next(item for item in ORIGINAL_FIXTURES if item.query == "payment within 14 days"),
        next(item for item in ORIGINAL_FIXTURES if item.query == "can we bring our own catering"),
        next(item for item in ORIGINAL_FIXTURES if item.query == "can we visit the venue beforehand"),
        next(item for item in ORIGINAL_FIXTURES if item.query == "security deposit"),
        next(item for item in ORIGINAL_FIXTURES if item.query == "when does the remaining balance need to be paid"),
    ):
        lines.append(f"### `{fixture.query}`")
        lines.append("")
        lines.append(f"- fixture note: {fixture.note}")
        append_result_block(lines, "FTS", original_fts[fixture.query])
        append_result_block(lines, "Semantic", original_semantic[fixture.query])
        append_result_block(lines, "Hybrid", original_hybrid[fixture.query])
        lines.append("")
    lines.append("## Holdout Query Results")
    lines.append("")
    for fixture in HOLDOUT_FIXTURES:
        lines.append(f"### `{fixture.query}`")
        lines.append("")
        lines.append(f"- fixture note: {fixture.note}")
        append_result_block(lines, "FTS", holdout_fts[fixture.query])
        append_result_block(lines, "Semantic", holdout_semantic[fixture.query])
        append_result_block(lines, "Hybrid", holdout_hybrid[fixture.query])
        lines.append("")
    lines.append("## Performance Observations")
    lines.append("")
    lines.append(f"- original-fixture average query embedding time: `{original_timings['embedding_ms']}` ms")
    lines.append(f"- original-fixture average FTS retrieval time: `{original_timings['fts_ms']}` ms")
    lines.append(f"- original-fixture average semantic retrieval time: `{original_timings['semantic_ms']}` ms")
    lines.append(f"- original-fixture average hybrid retrieval time: `{original_timings['hybrid_ms']}` ms")
    lines.append(f"- holdout average query embedding time: `{holdout_timings['embedding_ms']}` ms")
    lines.append(f"- holdout average FTS retrieval time: `{holdout_timings['fts_ms']}` ms")
    lines.append(f"- holdout average semantic retrieval time: `{holdout_timings['semantic_ms']}` ms")
    lines.append(f"- holdout average hybrid retrieval time: `{holdout_timings['hybrid_ms']}` ms")
    lines.append("")
    lines.append("## Known Residual Quirks")
    lines.append("")
    lines.append("- `when does the remaining balance need to be paid` should keep the correct primary result. Secondary ordering may still place `TPL-013` above `CF-007`, which remains the approved non-blocking quirk from 5.6A.")
    lines.append("- The hybrid surface degrades predictably to FTS-only for a given query if no query embedding is supplied, while still keeping category modifiers and current-governance eligibility intact.")
    lines.append("- Missing chunk embeddings do not remove eligible chunks from FTS retrieval because semantic ranking is additive rather than a mandatory eligibility gate.")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    output = render_report(args.limit, args.candidate_pool_limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
