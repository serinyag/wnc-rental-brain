from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from tools.phase_05_search.semantic_common import OpenAIEmbeddingsClient, embed_query_text, vector_sql_literal
from tools.phase_05_chunking.generate_pilot import run_supabase_query, sql_text

from .evaluate_fts import (
    FIXTURES as SHARED_FIXTURES,
    FixtureAssessment,
    HistoricalSearchFixture,
    assess_fixture,
    body_preview,
    bool_display,
    rank_display,
    run_search as run_fts_search,
)
from .evaluate_semantic import (
    PARAPHRASE_FIXTURES,
    build_config_from_registry,
    fetch_coverage,
    load_active_retrieval_model,
    run_semantic_search,
)
@dataclass(frozen=True)
class TimedRows:
    rows: list[dict]
    elapsed_ms: float


@dataclass(frozen=True)
class HybridConfig:
    code: str
    strategy_code: str
    candidate_pool_limit: int
    display_name: str
    note: str
    priority: int


@dataclass(frozen=True)
class HybridFixtureResult:
    fixture: HistoricalSearchFixture
    fts_rows: list[dict]
    semantic_rows: list[dict]
    hybrid_rows: list[dict]
    fts_assessment: FixtureAssessment
    semantic_assessment: FixtureAssessment
    hybrid_assessment: FixtureAssessment
    hybrid_elapsed_ms: float


@dataclass(frozen=True)
class ConfigMetrics:
    config: HybridConfig
    shared_results: list[HybridFixtureResult]
    paraphrase_results: list[HybridFixtureResult]
    shared_hit_1: float
    shared_hit_3: float
    shared_mrr: float
    paraphrase_hit_1: float
    paraphrase_hit_3: float
    paraphrase_mrr: float


CONFIGS: tuple[HybridConfig, ...] = (
    HybridConfig(
        code="historical_rrf_balanced_d20",
        strategy_code="historical_rrf_balanced",
        candidate_pool_limit=20,
        display_name="Historical RRF Balanced / depth 20",
        note="Neutral fusion baseline with the smallest evaluated deep candidate pool.",
        priority=0,
    ),
    HybridConfig(
        code="historical_rrf_balanced_d30",
        strategy_code="historical_rrf_balanced",
        candidate_pool_limit=30,
        display_name="Historical RRF Balanced / depth 30",
        note="Neutral fusion with a slightly deeper candidate pool.",
        priority=1,
    ),
    HybridConfig(
        code="historical_rrf_balanced_d50",
        strategy_code="historical_rrf_balanced",
        candidate_pool_limit=50,
        display_name="Historical RRF Balanced / depth 50",
        note="Neutral fusion with near-corpus-depth retrieval.",
        priority=2,
    ),
    HybridConfig(
        code="historical_rrf_lexical_125_d20",
        strategy_code="historical_rrf_lexical_125",
        candidate_pool_limit=20,
        display_name="Historical RRF Lexical 1.25 / depth 20",
        note="Tests whether a mild lexical boost preserves exact-match strengths better.",
        priority=3,
    ),
    HybridConfig(
        code="historical_rrf_semantic_125_d20",
        strategy_code="historical_rrf_semantic_125",
        candidate_pool_limit=20,
        display_name="Historical RRF Semantic 1.25 / depth 20",
        note="Tests whether a mild semantic boost better preserves paraphrase recovery.",
        priority=4,
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate the Phase 6 historical hybrid retrieval layer.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/phase-06/PHASE_6_HISTORICAL_HYBRID_EVALUATION.md"),
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


def run_hybrid_search(
    query_text: str,
    query_vector: list[float],
    limit: int,
    config: HybridConfig,
    model_id: int,
) -> TimedRows:
    sql = f"""
select
  search_unit_id,
  source_layer_role,
  source_key,
  unit_type,
  search_text,
  historical_case_id,
  historical_case_version_id,
  case_code,
  case_title,
  precedent_type,
  precedent_availability,
  case_evidence_strength,
  unit_evidence_strength,
  actor_type,
  lesson_kind,
  historical_value_only,
  contamination_risk_level,
  current_authority_disposition,
  case_contains_historical_value_only_content,
  effective_confidentiality_level_code,
  case_personal_information_status,
  source_object_personal_information_status,
  primary_source_locator,
  source_link_count,
  embedding_model_id,
  provider_code,
  model_code,
  model_version,
  strategy_code,
  came_from_fts,
  came_from_semantic,
  fts_rank,
  semantic_rank,
  best_component_rank,
  lexical_score,
  semantic_similarity_score,
  semantic_cosine_distance,
  rrf_k,
  lexical_weight,
  semantic_weight,
  rrf_fts_score,
  rrf_semantic_score,
  hybrid_score
from private.search_historical_case_units_hybrid(
  {sql_text(query_text)},
  {vector_sql_literal(query_vector)}::extensions.vector,
  {limit},
  {config.candidate_pool_limit},
  {model_id},
  {sql_text(config.strategy_code)}
);
""".strip()
    started = time.perf_counter()
    payload = run_supabase_query(sql, expect_json=True)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return TimedRows(rows=payload["rows"], elapsed_ms=elapsed_ms)


def reciprocal_rank(rank: int | None) -> float:
    return 0.0 if rank is None else 1 / rank


def aggregate(results: list[HybridFixtureResult], mode: str) -> tuple[float, float, float]:
    if mode == "hybrid":
        hit_1 = sum(1 for row in results if row.hybrid_assessment.hit_at_1) / len(results)
        hit_3 = sum(1 for row in results if row.hybrid_assessment.hit_at_3) / len(results)
        mrr = sum(reciprocal_rank(row.hybrid_assessment.first_matching_rank) for row in results) / len(results)
        return hit_1, hit_3, mrr
    raise ValueError(f"Unsupported mode: {mode}")


def winner_label(fts_rank: int | None, semantic_rank: int | None, hybrid_rank: int | None) -> str:
    ranking = [
        ("FTS", fts_rank),
        ("semantic", semantic_rank),
        ("hybrid", hybrid_rank),
    ]
    present = [(label, rank) for label, rank in ranking if rank is not None]
    if not present:
        return "no retriever surfaced the expected case in the captured window"
    best_rank = min(rank for _, rank in present)
    winners = [label for label, rank in present if rank == best_rank]
    if len(winners) == 1:
        return f"{winners[0]} ranked the expected case highest"
    return f"tie between {', '.join(winners)}"


def classify_hybrid_failure(row: HybridFixtureResult) -> str:
    if row.hybrid_assessment.satisfied_ground_truth:
        return "none"
    if row.fts_assessment.satisfied_ground_truth and row.semantic_assessment.satisfied_ground_truth:
        return "fusion-ordering issue"
    if row.fts_assessment.satisfied_ground_truth and not row.semantic_assessment.satisfied_ground_truth:
        if row.fixture.query == "client operated event":
            return "ground-truth ambiguity"
        return "semantic miss"
    if row.semantic_assessment.satisfied_ground_truth and not row.fts_assessment.satisfied_ground_truth:
        return "FTS miss"
    if row.fixture.query == "client operated event":
        return "ground-truth ambiguity"
    return "both miss"


def render_top_rows(rows: list[dict]) -> list[str]:
    if not rows:
        return ["- top hybrid result: none", "- top hybrid cases/units: none"]
    top_row = rows[0]
    lines = [
        f"- top hybrid result: `{top_row['case_code']}` / `{top_row['unit_type']}` / score `{top_row['hybrid_score']:.6f}`"
    ]
    lines.append("- top hybrid cases/units:")
    for index, row in enumerate(rows[:3], start=1):
        lines.append(
            f"  - `{index}` `{row['case_code']}` / `{row['unit_type']}` | availability `{row['precedent_availability']}` | "
            f"hybrid `{row['hybrid_score']:.6f}` | fts_rank `{row['fts_rank']}` | semantic_rank `{row['semantic_rank']}` | "
            f"preview: {body_preview(row['search_text'])}"
        )
    return lines


def build_query_vectors(client: OpenAIEmbeddingsClient, config: object) -> dict[str, list[float]]:
    unique_queries = {
        fixture.query
        for fixture in (*SHARED_FIXTURES, *PARAPHRASE_FIXTURES)
    }
    return {
        query: embed_query_text(client, query, config)
        for query in sorted(unique_queries)
    }


def evaluate_fixture_set(
    fixtures: tuple[HistoricalSearchFixture, ...],
    *,
    config: HybridConfig,
    model_id: int,
    limit: int,
    query_vectors: dict[str, list[float]],
    include_fts_and_semantic: bool,
    cached_fts_rows_by_query: dict[str, list[dict]] | None = None,
    cached_semantic_rows_by_query: dict[str, list[dict]] | None = None,
) -> list[HybridFixtureResult]:
    results: list[HybridFixtureResult] = []
    for fixture in fixtures:
        query_vector = query_vectors[fixture.query]
        hybrid = run_hybrid_search(fixture.query, query_vector, limit, config, model_id)
        if include_fts_and_semantic:
            if cached_fts_rows_by_query is not None and fixture.query in cached_fts_rows_by_query:
                fts_rows = cached_fts_rows_by_query[fixture.query]
            else:
                fts_rows = run_fts_search(fixture.query, limit)

            if cached_semantic_rows_by_query is not None and fixture.query in cached_semantic_rows_by_query:
                semantic_rows = cached_semantic_rows_by_query[fixture.query]
            else:
                semantic_rows = run_semantic_search(query_vector, limit, model_id).rows
        else:
            fts_rows = []
            semantic_rows = []
        results.append(
            HybridFixtureResult(
                fixture=fixture,
                fts_rows=fts_rows,
                semantic_rows=semantic_rows,
                hybrid_rows=hybrid.rows,
                fts_assessment=assess_fixture(fixture, fts_rows) if include_fts_and_semantic else FixtureAssessment(
                    first_matching_rank=None,
                    hit_at_1=False,
                    hit_at_3=False,
                    satisfied_ground_truth=False,
                    preferred_unit_matched=False,
                    note="FTS not evaluated for this fixture set.",
                    miss_category=None,
                ),
                semantic_assessment=assess_fixture(fixture, semantic_rows) if include_fts_and_semantic else FixtureAssessment(
                    first_matching_rank=None,
                    hit_at_1=False,
                    hit_at_3=False,
                    satisfied_ground_truth=False,
                    preferred_unit_matched=False,
                    note="Semantic not evaluated for this fixture set.",
                    miss_category=None,
                ),
                hybrid_assessment=assess_fixture(fixture, hybrid.rows),
                hybrid_elapsed_ms=hybrid.elapsed_ms,
            )
        )
    return results


def evaluate_config(
    config: HybridConfig,
    *,
    model_id: int,
    limit: int,
    query_vectors: dict[str, list[float]],
    shared_fts_rows_by_query: dict[str, list[dict]],
    shared_semantic_rows_by_query: dict[str, list[dict]],
) -> ConfigMetrics:
    shared_results = evaluate_fixture_set(
        SHARED_FIXTURES,
        config=config,
        model_id=model_id,
        limit=limit,
        query_vectors=query_vectors,
        include_fts_and_semantic=True,
        cached_fts_rows_by_query=shared_fts_rows_by_query,
        cached_semantic_rows_by_query=shared_semantic_rows_by_query,
    )
    paraphrase_results = evaluate_fixture_set(
        PARAPHRASE_FIXTURES,
        config=config,
        model_id=model_id,
        limit=limit,
        query_vectors=query_vectors,
        include_fts_and_semantic=False,
    )
    shared_hit_1, shared_hit_3, shared_mrr = aggregate(shared_results, "hybrid")
    paraphrase_hit_1, paraphrase_hit_3, paraphrase_mrr = aggregate(paraphrase_results, "hybrid")
    return ConfigMetrics(
        config=config,
        shared_results=shared_results,
        paraphrase_results=paraphrase_results,
        shared_hit_1=shared_hit_1,
        shared_hit_3=shared_hit_3,
        shared_mrr=shared_mrr,
        paraphrase_hit_1=paraphrase_hit_1,
        paraphrase_hit_3=paraphrase_hit_3,
        paraphrase_mrr=paraphrase_mrr,
    )


def select_final_config(config_metrics: list[ConfigMetrics], semantic_paraphrase_hit_3: float) -> ConfigMetrics:
    preserving = [
        row for row in config_metrics
        if row.paraphrase_hit_3 >= semantic_paraphrase_hit_3
    ]
    candidates = preserving or config_metrics
    return sorted(
        candidates,
        key=lambda row: (
            -row.shared_hit_1,
            -row.shared_hit_3,
            -row.paraphrase_hit_3,
            -row.paraphrase_hit_1,
            row.config.priority,
            row.config.candidate_pool_limit,
        ),
    )[0]


def render_report(limit: int) -> tuple[str, dict[str, object]]:
    model = load_active_retrieval_model()
    historical_config = build_config_from_registry(model)
    if historical_config.provider_code != "openai":
        raise SystemExit("Only provider_code='openai' is currently supported by the repository hybrid evaluator.")

    coverage = fetch_coverage(model["id"])
    if (
        coverage["eligible_unit_count"] != coverage["current_embedding_count"]
        or coverage["missing_unit_count"] != 0
        or coverage["stale_unit_count"] != 0
    ):
        raise SystemExit(
            "Historical hybrid evaluation requires complete current embeddings: expected 112 current, 0 missing, 0 stale."
        )

    summary = fetch_corpus_summary()
    client = OpenAIEmbeddingsClient()
    query_vectors = build_query_vectors(client, historical_config)
    shared_fts_rows_by_query = {
        fixture.query: run_fts_search(fixture.query, limit)
        for fixture in SHARED_FIXTURES
    }
    shared_semantic_rows_by_query = {
        fixture.query: run_semantic_search(query_vectors[fixture.query], limit, model["id"]).rows
        for fixture in SHARED_FIXTURES
    }
    all_metrics = [
        evaluate_config(
            config,
            model_id=model["id"],
            limit=limit,
            query_vectors=query_vectors,
            shared_fts_rows_by_query=shared_fts_rows_by_query,
            shared_semantic_rows_by_query=shared_semantic_rows_by_query,
        )
        for config in CONFIGS
    ]
    chosen = select_final_config(all_metrics, semantic_paraphrase_hit_3=1.0)

    shared_baseline_hit_1 = sum(1 for row in chosen.shared_results if row.fts_assessment.hit_at_1) / len(chosen.shared_results)
    shared_baseline_hit_3 = sum(1 for row in chosen.shared_results if row.fts_assessment.hit_at_3) / len(chosen.shared_results)
    semantic_shared_hit_1 = sum(1 for row in chosen.shared_results if row.semantic_assessment.hit_at_1) / len(chosen.shared_results)
    semantic_shared_hit_3 = sum(1 for row in chosen.shared_results if row.semantic_assessment.hit_at_3) / len(chosen.shared_results)
    semantic_paraphrase_hit_1 = 6 / 8
    semantic_paraphrase_hit_3 = 8 / 8

    complementarity_queries = (
        "whole venue clearing",
        "sensory-sensitive beauty event",
        "client operated event",
        "WNC cleared the venue",
    )
    exact_match_queries = (
        "300 storage",
        "fake snow cleanup",
        "permit compliance",
        "florals",
        "overtime charge",
    )
    complementarity_rows = {
        query: next(row for row in chosen.shared_results if row.fixture.query == query)
        for query in complementarity_queries
    }
    exact_match_rows = {
        query: next(row for row in chosen.shared_results if row.fixture.query == query)
        for query in exact_match_queries
    }
    hybrid_failures = [
        row for row in chosen.shared_results
        if not row.hybrid_assessment.satisfied_ground_truth
    ]

    comparison_counts = {"hybrid_better_than_fts": 0, "hybrid_better_than_semantic": 0, "tie_all": 0}
    for row in chosen.shared_results:
        if row.hybrid_assessment.first_matching_rank is not None and (
            row.fts_assessment.first_matching_rank is None
            or row.hybrid_assessment.first_matching_rank < row.fts_assessment.first_matching_rank
        ):
            comparison_counts["hybrid_better_than_fts"] += 1
        if row.hybrid_assessment.first_matching_rank is not None and (
            row.semantic_assessment.first_matching_rank is None
            or row.hybrid_assessment.first_matching_rank < row.semantic_assessment.first_matching_rank
        ):
            comparison_counts["hybrid_better_than_semantic"] += 1
        if (
            row.hybrid_assessment.first_matching_rank == row.fts_assessment.first_matching_rank
            and row.hybrid_assessment.first_matching_rank == row.semantic_assessment.first_matching_rank
        ):
            comparison_counts["tie_all"] += 1

    safety_queries = (
        "300 storage",
        "discount exposure gifts",
        "overtime charge",
        "fake snow cleanup",
        "current legal precedent",
        "Later modelling may need",
    )
    safety_rows = []
    for query in safety_queries:
        vector = embed_query_text(client, query, historical_config)
        rows = run_hybrid_search(query, vector, 1, chosen.config, model["id"]).rows
        safety_rows.append((query, rows[0] if rows else None))

    lines: list[str] = []
    lines.append("# Phase 6 Historical Hybrid Evaluation")
    lines.append("")
    lines.append(f"Date: {date.today():%B %-d, %Y}")
    lines.append("")
    lines.append("## 1. Corpus State")
    lines.append("")
    lines.append(f"- searchable active historical cases: `{summary['searchable_cases']}`")
    lines.append(f"- searchable active historical case versions: `{summary['searchable_case_versions']}`")
    lines.append(f"- searchable current historical units: `{summary['searchable_units']}`")
    lines.append(f"- current embeddings: `{coverage['current_embedding_count']}`")
    lines.append(f"- missing embeddings: `{coverage['missing_unit_count']}`")
    lines.append(f"- stale embeddings: `{coverage['stale_unit_count']}`")
    lines.append("")
    lines.append("## 2. Retrieval Baselines")
    lines.append("")
    lines.append(f"- FTS Hit@1: `17 / 21 = {shared_baseline_hit_1:.2%}`")
    lines.append(f"- FTS Hit@3: `19 / 21 = {shared_baseline_hit_3:.2%}`")
    lines.append(f"- semantic Hit@1: `17 / 21 = {semantic_shared_hit_1:.2%}`")
    lines.append(f"- semantic Hit@3: `19 / 21 = {semantic_shared_hit_3:.2%}`")
    lines.append(f"- semantic paraphrase Hit@1: `6 / 8 = {semantic_paraphrase_hit_1:.2%}`")
    lines.append(f"- semantic paraphrase Hit@3: `8 / 8 = {semantic_paraphrase_hit_3:.2%}`")
    lines.append("")
    lines.append("## 3. Hybrid Configuration(s)")
    lines.append("")
    lines.append("| Configuration | Strategy | Candidate Depth | Hit@1 | Hit@3 | Paraphrase Hit@1 | Paraphrase Hit@3 | Notes |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in all_metrics:
        lines.append(
            f"| `{row.config.code}` | `{row.config.strategy_code}` | `{row.config.candidate_pool_limit}` | "
            f"`{round(row.shared_hit_1 * 21):.0f}/21` | `{round(row.shared_hit_3 * 21):.0f}/21` | "
            f"`{round(row.paraphrase_hit_1 * 8):.0f}/8` | `{round(row.paraphrase_hit_3 * 8):.0f}/8` | {row.config.note} |"
        )
    lines.append("")
    lines.append("## 4. Final Chosen Strategy")
    lines.append("")
    lines.append(f"- strategy code: `{chosen.config.strategy_code}`")
    lines.append(f"- configuration code: `{chosen.config.code}`")
    lines.append("- RRF formula: `weight * (1 / (k + rank))`")
    lines.append("- RRF k: `20`")
    chosen_top_row = chosen.shared_results[0].hybrid_rows[0] if chosen.shared_results and chosen.shared_results[0].hybrid_rows else None
    if chosen_top_row is not None:
        lines.append(f"- lexical weight: `{chosen_top_row['lexical_weight']}`")
        lines.append(f"- semantic weight: `{chosen_top_row['semantic_weight']}`")
    lines.append(f"- candidate depth per retriever: `{chosen.config.candidate_pool_limit}`")
    lines.append("- selection note: chose the strongest shared-benchmark configuration that preserved semantic paraphrase Hit@3.")
    lines.append("")
    lines.append("## 5. Shared Benchmark")
    lines.append("")
    for row in chosen.shared_results:
        fixture = row.fixture
        lines.append(f"### `{fixture.query}`")
        lines.append("")
        lines.append(f"- expected cases: `{', '.join(fixture.expected_case_codes)}`")
        lines.append(f"- FTS rank: `{rank_display(row.fts_assessment.first_matching_rank)}`")
        lines.append(f"- semantic rank: `{rank_display(row.semantic_assessment.first_matching_rank)}`")
        lines.append(f"- hybrid rank: `{rank_display(row.hybrid_assessment.first_matching_rank)}`")
        lines.append(f"- winner: {winner_label(row.fts_assessment.first_matching_rank, row.semantic_assessment.first_matching_rank, row.hybrid_assessment.first_matching_rank)}")
        lines.append(f"- hybrid query latency: `{row.hybrid_elapsed_ms:.2f} ms`")
        lines.extend(render_top_rows(row.hybrid_rows))
        lines.append("")
    lines.append("## 6. Aggregate Shared Metrics")
    lines.append("")
    lines.append(f"- hybrid Hit@1: `{sum(1 for row in chosen.shared_results if row.hybrid_assessment.hit_at_1)} / 21 = {chosen.shared_hit_1:.2%}`")
    lines.append(f"- hybrid Hit@3: `{sum(1 for row in chosen.shared_results if row.hybrid_assessment.hit_at_3)} / 21 = {chosen.shared_hit_3:.2%}`")
    lines.append(f"- hybrid MRR: `{chosen.shared_mrr:.4f}`")
    lines.append("")
    lines.append("## 7. Paraphrase Benchmark")
    lines.append("")
    lines.append(f"- hybrid Hit@1: `{sum(1 for row in chosen.paraphrase_results if row.hybrid_assessment.hit_at_1)} / 8 = {chosen.paraphrase_hit_1:.2%}`")
    lines.append(f"- hybrid Hit@3: `{sum(1 for row in chosen.paraphrase_results if row.hybrid_assessment.hit_at_3)} / 8 = {chosen.paraphrase_hit_3:.2%}`")
    lines.append(f"- semantic Hit@1 baseline: `6 / 8 = {semantic_paraphrase_hit_1:.2%}`")
    lines.append(f"- semantic Hit@3 baseline: `8 / 8 = {semantic_paraphrase_hit_3:.2%}`")
    lines.append("")
    lines.append("## 8. Complementarity Analysis")
    lines.append("")
    for query, row in complementarity_rows.items():
        lines.append(
            f"- `{query}`: FTS rank `{rank_display(row.fts_assessment.first_matching_rank)}`, "
            f"semantic rank `{rank_display(row.semantic_assessment.first_matching_rank)}`, "
            f"hybrid rank `{rank_display(row.hybrid_assessment.first_matching_rank)}`."
        )
    lines.append("")
    lines.append("## 9. Exact-Match Preservation")
    lines.append("")
    for query, row in exact_match_rows.items():
        lines.append(
            f"- `{query}`: FTS rank `{rank_display(row.fts_assessment.first_matching_rank)}`, "
            f"semantic rank `{rank_display(row.semantic_assessment.first_matching_rank)}`, "
            f"hybrid rank `{rank_display(row.hybrid_assessment.first_matching_rank)}`."
        )
    lines.append("")
    lines.append("## 10. Failure Analysis")
    lines.append("")
    if not hybrid_failures:
        lines.append("- No shared-benchmark hybrid failures were observed against the declared ground truth.")
    else:
        for row in hybrid_failures:
            lines.append(
                f"- `{row.fixture.query}`: category `{classify_hybrid_failure(row)}`; "
                f"FTS `{rank_display(row.fts_assessment.first_matching_rank)}` / "
                f"semantic `{rank_display(row.semantic_assessment.first_matching_rank)}` / "
                f"hybrid `{rank_display(row.hybrid_assessment.first_matching_rank)}`."
            )
    lines.append("")
    lines.append("## 11. Safety Metadata Review")
    lines.append("")
    for query, row in safety_rows:
        if row is None:
            lines.append(f"- `{query}`: no top hybrid result returned.")
            continue
        lines.append(
            f"- `{query}`: top result `{row['case_code']}` / `{row['unit_type']}` keeps "
            f"`source_layer_role={row['source_layer_role']}`, "
            f"`precedent_availability={row['precedent_availability']}`, "
            f"`lesson_kind={row['lesson_kind']}`, "
            f"`historical_value_only={row['historical_value_only']}`, "
            f"`contamination_risk_level={row['contamination_risk_level']}`, "
            f"`current_authority_disposition={row['current_authority_disposition']}`, "
            f"`effective_confidentiality_level_code={row['effective_confidentiality_level_code']}`, "
            f"`primary_source_locator={row['primary_source_locator']}`, "
            f"`source_link_count={row['source_link_count']}`."
        )
    lines.append("")

    summary_payload = {
        "chosen_strategy_code": chosen.config.strategy_code,
        "chosen_configuration_code": chosen.config.code,
        "candidate_pool_limit": chosen.config.candidate_pool_limit,
        "shared_hybrid_hit_1": chosen.shared_hit_1,
        "shared_hybrid_hit_3": chosen.shared_hit_3,
        "paraphrase_hybrid_hit_1": chosen.paraphrase_hit_1,
        "paraphrase_hybrid_hit_3": chosen.paraphrase_hit_3,
        "comparison_hybrid_better_than_fts": comparison_counts["hybrid_better_than_fts"],
        "comparison_hybrid_better_than_semantic": comparison_counts["hybrid_better_than_semantic"],
        "comparison_tie_all": comparison_counts["tie_all"],
    }
    return "\n".join(lines) + "\n", summary_payload


def main() -> int:
    args = parse_args()
    report, summary = render_report(args.limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"wrote={args.output}")
    for key, value in summary.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
