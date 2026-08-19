from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from tools.phase_05_chunking.generate_pilot import run_supabase_query
from tools.phase_05_search.semantic_common import (
    EmbeddingModelConfig,
    OpenAIEmbeddingsClient,
    embed_query_text,
    vector_sql_literal,
)

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


@dataclass(frozen=True)
class TimedRows:
    rows: list[dict]
    elapsed_ms: float


@dataclass(frozen=True)
class EvaluatedFixture:
    fixture: HistoricalSearchFixture
    fts_rows: list[dict]
    semantic_rows: list[dict]
    fts_assessment: FixtureAssessment
    semantic_assessment: FixtureAssessment
    query_elapsed_ms: float


PARAPHRASE_FIXTURES: tuple[HistoricalSearchFixture, ...] = (
    HistoricalSearchFixture(
        category="Semantic paraphrase",
        query="customer wanted the venue stripped back for several days",
        expected_case_codes=("HC-001",),
        preferred_unit_types=("case_narrative", "decision", "responsibility"),
        required_hit_rank=3,
        note="Paraphrases the whole-venue clearing and handover scenario without repeating the corpus wording.",
    ),
    HistoricalSearchFixture(
        category="Semantic paraphrase",
        query="event where smell could interfere with the brand experience",
        expected_case_codes=("HC-004",),
        preferred_unit_types=("decision", "lesson", "case_narrative"),
        required_hit_rank=3,
        note="Targets the scent-sensitive beauty-event precedent using brand-experience phrasing rather than smell wording.",
    ),
    HistoricalSearchFixture(
        category="Semantic paraphrase",
        query="production setup needed specialist electrical review",
        expected_case_codes=("HC-002",),
        preferred_unit_types=("decision", "lesson", "case_narrative"),
        required_hit_rank=3,
        note="Paraphrases the technical-load and qualified electrical-assessment precedent.",
    ),
    HistoricalSearchFixture(
        category="Semantic paraphrase",
        query="event setup ran later than agreed",
        expected_case_codes=("HC-006",),
        preferred_unit_types=("decision", "lesson", "case_narrative"),
        required_hit_rank=3,
        note="Targets the late build-up and overtime precedent without using exact build-up wording.",
    ),
    HistoricalSearchFixture(
        category="Semantic paraphrase",
        query="agency used a messy decorative material",
        expected_case_codes=("HC-007",),
        preferred_unit_types=("decision", "lesson", "responsibility", "case_narrative"),
        required_hit_rank=3,
        note="Paraphrases the fake-snow cleanup precedent with broader decorative-material wording.",
    ),
    HistoricalSearchFixture(
        category="Semantic paraphrase",
        query="client was worried about competitor logos being visible",
        expected_case_codes=("HC-008",),
        preferred_unit_types=("decision", "responsibility", "lesson"),
        required_hit_rank=3,
        note="Targets the branded-competitor visibility precedent using logo visibility language.",
    ),
    HistoricalSearchFixture(
        category="Semantic paraphrase",
        query="unusual event needed regulatory checks before approving it",
        expected_case_codes=("HC-009",),
        preferred_unit_types=("decision", "lesson", "responsibility", "case_narrative"),
        required_hit_rank=3,
        note="Paraphrases the permit and compliance cautionary precedent without repeating permit wording.",
    ),
    HistoricalSearchFixture(
        category="Semantic paraphrase",
        query="did we ever charge for offsite storage because the venue had no room",
        expected_case_codes=("HC-003", "HC-001"),
        preferred_unit_types=("decision", "lesson", "case_narrative"),
        required_hit_rank=3,
        note="Targets the historical offsite-storage precedents while preserving the risky historical-value boundary.",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate the Phase 6 historical semantic retrieval foundation.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/phase-06/PHASE_6_HISTORICAL_SEMANTIC_EVALUATION.md"),
        help="Markdown report path to write.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of top results to capture per query.",
    )
    return parser.parse_args()


def load_active_retrieval_model() -> dict:
    sql = """
select
  id,
  provider_code,
  model_code,
  model_version,
  embedding_dimensions,
  configuration_json
from private.historical_case_embedding_models
where is_retrieval_approved
  and is_active
order by id;
""".strip()
    payload = run_supabase_query(sql, expect_json=True)
    rows = payload["rows"]
    if not rows:
        raise SystemExit("No active retrieval-approved historical embedding model is registered. Run embedding generation first.")
    if len(rows) > 1:
        raise SystemExit("Multiple active retrieval-approved historical embedding models are registered. Narrow the registry before evaluation.")
    return rows[0]


def build_config_from_registry(row: dict) -> EmbeddingModelConfig:
    cfg = row["configuration_json"] or {}
    return EmbeddingModelConfig(
        provider_code=row["provider_code"],
        model_code=row["model_code"],
        model_version=row["model_version"],
        embedding_dimensions=row["embedding_dimensions"],
        distance_metric=cfg.get("distance_metric", "cosine"),
        input_contract_code=cfg.get("input_contract_code", "phase_06_historical_search_unit_embedding_input_v1"),
        encoding_format=cfg.get("encoding_format", "float"),
        api_base_url=cfg.get("api_base_url", "https://api.openai.com/v1"),
        is_retrieval_approved=True,
        is_active=True,
    )


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


def fetch_coverage(model_id: int) -> dict[str, object]:
    sql = f"""
select
  embedding_model_id,
  provider_code,
  model_code,
  model_version,
  embedding_dimensions,
  config_fingerprint,
  eligible_unit_count,
  current_embedding_count,
  missing_unit_count,
  stale_unit_count
from private.current_historical_case_embedding_coverage
where embedding_model_id = {model_id};
""".strip()
    payload = run_supabase_query(sql, expect_json=True)
    rows = payload["rows"]
    if not rows:
        raise SystemExit("Historical embedding coverage is unavailable for the active model.")
    return rows[0]


def run_semantic_search(
    query_vector: list[float],
    limit: int,
    model_id: int,
) -> TimedRows:
    sql = f"""
select
  search_unit_id,
  source_layer_role,
  source_key,
  unit_type,
  search_text,
  similarity_score,
  cosine_distance,
  input_content_hash,
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
  model_version
from private.search_historical_case_units_semantic(
  {vector_sql_literal(query_vector)}::extensions.vector,
  {limit},
  {model_id}
);
""".strip()
    started = time.perf_counter()
    payload = run_supabase_query(sql, expect_json=True)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return TimedRows(rows=payload["rows"], elapsed_ms=elapsed_ms)


def compare_modes(fts_rank: int | None, semantic_rank: int | None) -> str:
    if fts_rank is None and semantic_rank is None:
        return "neither retrieval mode surfaced the expected case in the captured window"
    if fts_rank is None:
        return "semantic search recovered a lexical miss"
    if semantic_rank is None:
        return "FTS recovered the expected case while semantic search missed it"
    if semantic_rank < fts_rank:
        return "semantic search ranked the expected case higher"
    if semantic_rank > fts_rank:
        return "FTS ranked the expected case higher"
    return "FTS and semantic search produced the same expected-case rank"


def classify_semantic_gap(fixture: HistoricalSearchFixture, rows: list[dict], assessment: FixtureAssessment) -> str:
    if assessment.satisfied_ground_truth:
        return "none"
    if not rows:
        return "insufficient semantic distinction"
    top_row = rows[0]
    if assessment.first_matching_rank is not None and top_row["unit_type"] == "case_narrative":
        return "narrative dominating statement"
    if fixture.query in {"client operated event", "external storage"}:
        return "ground-truth ambiguity"
    if fixture.query in {"whole venue clearing", "sensory-sensitive beauty event", "florals"}:
        return "statement wording"
    if assessment.first_matching_rank is None and len({row['case_code'] for row in rows[:3]}) > 1:
        return "corpus ambiguity"
    return "overly broad embedding similarity"


def render_top_rows(rows: list[dict], score_field: str) -> list[str]:
    if not rows:
        return ["- top semantic result: none", "- top semantic cases/units: none"]

    top_row = rows[0]
    lines = [
        f"- top semantic result: `{top_row['case_code']}` / `{top_row['unit_type']}` / score `{top_row[score_field]:.6f}`"
    ]
    lines.append("- top semantic cases/units:")
    for index, row in enumerate(rows[:3], start=1):
        lines.append(
            f"  - `{index}` `{row['case_code']}` / `{row['unit_type']}` | availability `{row['precedent_availability']}` | "
            f"score `{row[score_field]:.6f}` | preview: {body_preview(row['search_text'])}"
        )
    return lines


def evaluate_fixture_set(
    fixtures: tuple[HistoricalSearchFixture, ...],
    *,
    client: OpenAIEmbeddingsClient,
    config: EmbeddingModelConfig,
    limit: int,
    model_id: int,
    include_fts: bool,
) -> list[EvaluatedFixture]:
    evaluated: list[EvaluatedFixture] = []
    for fixture in fixtures:
        fts_rows = run_fts_search(fixture.query, limit) if include_fts else []
        query_vector = embed_query_text(client, fixture.query, config)
        semantic = run_semantic_search(query_vector, limit, model_id)
        evaluated.append(
            EvaluatedFixture(
                fixture=fixture,
                fts_rows=fts_rows,
                semantic_rows=semantic.rows,
                fts_assessment=assess_fixture(fixture, fts_rows) if include_fts else FixtureAssessment(
                    first_matching_rank=None,
                    hit_at_1=False,
                    hit_at_3=False,
                    satisfied_ground_truth=False,
                    preferred_unit_matched=False,
                    note="FTS not evaluated for this fixture set.",
                    miss_category=None,
                ),
                semantic_assessment=assess_fixture(fixture, semantic.rows),
                query_elapsed_ms=semantic.elapsed_ms,
            )
        )
    return evaluated


def aggregate_metrics(rows: list[EvaluatedFixture], *, semantic_only: bool) -> dict[str, object]:
    semantic_hit_1_count = sum(1 for row in rows if row.semantic_assessment.hit_at_1)
    semantic_hit_3_count = sum(1 for row in rows if row.semantic_assessment.hit_at_3)
    semantic_rr_total = sum(
        0 if row.semantic_assessment.first_matching_rank is None else 1 / row.semantic_assessment.first_matching_rank
        for row in rows
    )
    total = len(rows)
    result: dict[str, object] = {
        "query_count": total,
        "semantic_hit_1_count": semantic_hit_1_count,
        "semantic_hit_3_count": semantic_hit_3_count,
        "semantic_hit_1": semantic_hit_1_count / total,
        "semantic_hit_3": semantic_hit_3_count / total,
        "semantic_mrr": semantic_rr_total / total,
    }
    if not semantic_only:
        fts_hit_1_count = sum(1 for row in rows if row.fts_assessment.hit_at_1)
        fts_hit_3_count = sum(1 for row in rows if row.fts_assessment.hit_at_3)
        result.update(
            {
                "fts_hit_1_count": fts_hit_1_count,
                "fts_hit_3_count": fts_hit_3_count,
                "fts_hit_1": fts_hit_1_count / total,
                "fts_hit_3": fts_hit_3_count / total,
            }
        )
    return result


def render_report(limit: int) -> tuple[str, dict[str, object]]:
    model = load_active_retrieval_model()
    config = build_config_from_registry(model)
    if config.provider_code != "openai":
        raise SystemExit("Only provider_code='openai' is currently supported by the repository semantic evaluator.")

    coverage = fetch_coverage(model["id"])
    if coverage["current_embedding_count"] == 0:
        raise SystemExit("The active historical embedding model has zero current embeddings. Run embedding generation first.")

    summary = fetch_corpus_summary()
    client = OpenAIEmbeddingsClient()
    shared_rows = evaluate_fixture_set(
        SHARED_FIXTURES,
        client=client,
        config=config,
        limit=limit,
        model_id=model["id"],
        include_fts=True,
    )
    paraphrase_rows = evaluate_fixture_set(
        PARAPHRASE_FIXTURES,
        client=client,
        config=config,
        limit=limit,
        model_id=model["id"],
        include_fts=False,
    )

    shared_metrics = aggregate_metrics(shared_rows, semantic_only=False)
    paraphrase_metrics = aggregate_metrics(paraphrase_rows, semantic_only=True)

    comparison_counts = {"semantic_better": 0, "fts_better": 0, "tie": 0}
    for row in shared_rows:
        relation = compare_modes(
            row.fts_assessment.first_matching_rank,
            row.semantic_assessment.first_matching_rank,
        )
        if relation == "semantic search ranked the expected case higher" or relation == "semantic search recovered a lexical miss":
            comparison_counts["semantic_better"] += 1
        elif relation == "FTS ranked the expected case higher" or relation == "FTS recovered the expected case while semantic search missed it":
            comparison_counts["fts_better"] += 1
        else:
            comparison_counts["tie"] += 1

    lexical_focus = {
        query: next(row for row in shared_rows if row.fixture.query == query)
        for query in (
            "whole venue clearing",
            "sensory-sensitive beauty event",
            "client operated event",
            "WNC cleared the venue",
        )
    }

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
        query_vector = embed_query_text(client, query, config)
        rows = run_semantic_search(query_vector, 1, model["id"]).rows
        safety_rows.append((query, rows[0] if rows else None))

    semantic_failures = [
        row for row in shared_rows if not row.semantic_assessment.satisfied_ground_truth
    ]

    lines: list[str] = []
    lines.append("# Phase 6 Historical Semantic Evaluation")
    lines.append("")
    lines.append(f"Date: {date.today():%B %-d, %Y}")
    lines.append("")
    lines.append("## 1. Model")
    lines.append("")
    lines.append(f"- provider: `{model['provider_code']}`")
    lines.append(f"- model code: `{model['model_code']}`")
    lines.append(f"- model version: `{model['model_version']}`")
    lines.append(f"- dimensions: `{model['embedding_dimensions']}`")
    lines.append("- similarity metric: `cosine`")
    lines.append("- embedding input format:")
    lines.append("  - `Case: <case_title>`")
    lines.append("  - `Case code: <case_code>` when present")
    lines.append("  - `Unit type: <unit_type>` when present")
    lines.append("  - `Actor type: <actor_type>` when present")
    lines.append("  - `Lesson kind: <lesson_kind>` when present")
    lines.append("  - governed historical `search_text` body")
    lines.append("")
    lines.append("## 2. Corpus")
    lines.append("")
    lines.append(f"- searchable active historical cases: `{summary['searchable_cases']}`")
    lines.append(f"- searchable active historical case versions: `{summary['searchable_case_versions']}`")
    lines.append(f"- searchable current historical units: `{summary['searchable_units']}`")
    lines.append(f"- embedding completeness: `{coverage['current_embedding_count']} / {coverage['eligible_unit_count']}`")
    lines.append(f"- missing embeddings: `{coverage['missing_unit_count']}`")
    lines.append(f"- stale embeddings: `{coverage['stale_unit_count']}`")
    lines.append(f"- top results captured per query: `{limit}`")
    lines.append("")
    lines.append("## 3. Shared 21-Query Benchmark")
    lines.append("")
    for row in shared_rows:
        fixture = row.fixture
        semantic = row.semantic_assessment
        fts = row.fts_assessment
        lines.append(f"### `{fixture.query}`")
        lines.append("")
        lines.append(f"- category: `{fixture.category}`")
        lines.append(f"- expected cases: `{', '.join(fixture.expected_case_codes)}`")
        if fixture.preferred_unit_types:
            lines.append(f"- preferred unit types: `{', '.join(fixture.preferred_unit_types)}`")
        lines.append(f"- required success condition: `Hit@{fixture.required_hit_rank}`")
        if fixture.note:
            lines.append(f"- fixture note: {fixture.note}")
        lines.append(f"- FTS rank: `{rank_display(fts.first_matching_rank)}`")
        lines.append(f"- semantic rank: `{rank_display(semantic.first_matching_rank)}`")
        lines.append(f"- semantic Hit@1: `{bool_display(semantic.hit_at_1)}`")
        lines.append(f"- semantic Hit@3: `{bool_display(semantic.hit_at_3)}`")
        lines.append(f"- semantic ground-truth satisfied: `{bool_display(semantic.satisfied_ground_truth)}`")
        lines.append(f"- comparison: {compare_modes(fts.first_matching_rank, semantic.first_matching_rank)}")
        lines.append(f"- semantic query latency: `{row.query_elapsed_ms:.2f} ms`")
        lines.extend(render_top_rows(row.semantic_rows, "similarity_score"))
        lines.append("")
    lines.append("## 4. Semantic Paraphrase Benchmark")
    lines.append("")
    for row in paraphrase_rows:
        fixture = row.fixture
        semantic = row.semantic_assessment
        lines.append(f"### `{fixture.query}`")
        lines.append("")
        lines.append(f"- expected cases: `{', '.join(fixture.expected_case_codes)}`")
        if fixture.preferred_unit_types:
            lines.append(f"- preferred unit types: `{', '.join(fixture.preferred_unit_types)}`")
        lines.append(f"- required success condition: `Hit@{fixture.required_hit_rank}`")
        if fixture.note:
            lines.append(f"- fixture note: {fixture.note}")
        lines.append(f"- semantic rank: `{rank_display(semantic.first_matching_rank)}`")
        lines.append(f"- semantic Hit@1: `{bool_display(semantic.hit_at_1)}`")
        lines.append(f"- semantic Hit@3: `{bool_display(semantic.hit_at_3)}`")
        lines.append(f"- semantic ground-truth satisfied: `{bool_display(semantic.satisfied_ground_truth)}`")
        lines.append(f"- semantic query latency: `{row.query_elapsed_ms:.2f} ms`")
        lines.extend(render_top_rows(row.semantic_rows, "similarity_score"))
        lines.append("")
    lines.append("## 5. Aggregate Metrics")
    lines.append("")
    lines.append("### Shared benchmark")
    lines.append("")
    lines.append(
        f"- semantic Hit@1: `{shared_metrics['semantic_hit_1_count']} / {shared_metrics['query_count']} = {shared_metrics['semantic_hit_1']:.2%}`"
    )
    lines.append(
        f"- semantic Hit@3: `{shared_metrics['semantic_hit_3_count']} / {shared_metrics['query_count']} = {shared_metrics['semantic_hit_3']:.2%}`"
    )
    lines.append(f"- semantic MRR: `{shared_metrics['semantic_mrr']:.4f}`")
    lines.append(
        f"- FTS Hit@1: `{shared_metrics['fts_hit_1_count']} / {shared_metrics['query_count']} = {shared_metrics['fts_hit_1']:.2%}`"
    )
    lines.append(
        f"- FTS Hit@3: `{shared_metrics['fts_hit_3_count']} / {shared_metrics['query_count']} = {shared_metrics['fts_hit_3']:.2%}`"
    )
    lines.append("")
    lines.append("### Paraphrase benchmark")
    lines.append("")
    lines.append(
        f"- semantic Hit@1: `{paraphrase_metrics['semantic_hit_1_count']} / {paraphrase_metrics['query_count']} = {paraphrase_metrics['semantic_hit_1']:.2%}`"
    )
    lines.append(
        f"- semantic Hit@3: `{paraphrase_metrics['semantic_hit_3_count']} / {paraphrase_metrics['query_count']} = {paraphrase_metrics['semantic_hit_3']:.2%}`"
    )
    lines.append(f"- semantic MRR: `{paraphrase_metrics['semantic_mrr']:.4f}`")
    lines.append("")
    lines.append("## 6. Lexical Miss Recovery")
    lines.append("")
    for query, row in lexical_focus.items():
        lines.append(
            f"- `{query}`: FTS rank `{rank_display(row.fts_assessment.first_matching_rank)}` vs semantic rank "
            f"`{rank_display(row.semantic_assessment.first_matching_rank)}`; {compare_modes(row.fts_assessment.first_matching_rank, row.semantic_assessment.first_matching_rank)}."
        )
    lines.append("")
    lines.append("## 7. Semantic Failure Analysis")
    lines.append("")
    if not semantic_failures:
        lines.append("- No shared-benchmark semantic failures were observed against the declared ground truth.")
    else:
        for row in semantic_failures:
            lines.append(
                f"- `{row.fixture.query}`: category `{classify_semantic_gap(row.fixture, row.semantic_rows, row.semantic_assessment)}`; "
                f"semantic rank `{rank_display(row.semantic_assessment.first_matching_rank)}`; note: {row.semantic_assessment.note}"
            )
    lines.append("")
    lines.append("## 8. Safety Metadata Review")
    lines.append("")
    for query, row in safety_rows:
        if row is None:
            lines.append(f"- `{query}`: no top semantic result returned.")
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
    lines.append("## Comparison Summary")
    lines.append("")
    lines.append(f"- semantic better on shared benchmark queries: `{comparison_counts['semantic_better']}`")
    lines.append(f"- FTS better on shared benchmark queries: `{comparison_counts['fts_better']}`")
    lines.append(f"- ties on shared benchmark queries: `{comparison_counts['tie']}`")
    lines.append("")

    summary_payload = {
        "model_code": model["model_code"],
        "embedding_dimensions": model["embedding_dimensions"],
        "eligible_units": coverage["eligible_unit_count"],
        "current_embeddings": coverage["current_embedding_count"],
        "missing_embeddings": coverage["missing_unit_count"],
        "stale_embeddings": coverage["stale_unit_count"],
        "shared_semantic_hit_1": shared_metrics["semantic_hit_1"],
        "shared_semantic_hit_3": shared_metrics["semantic_hit_3"],
        "shared_fts_hit_1": shared_metrics["fts_hit_1"],
        "shared_fts_hit_3": shared_metrics["fts_hit_3"],
        "paraphrase_semantic_hit_1": paraphrase_metrics["semantic_hit_1"],
        "paraphrase_semantic_hit_3": paraphrase_metrics["semantic_hit_3"],
        "shared_query_count": shared_metrics["query_count"],
        "paraphrase_query_count": paraphrase_metrics["query_count"],
        "semantic_better_count": comparison_counts["semantic_better"],
        "fts_better_count": comparison_counts["fts_better"],
        "tie_count": comparison_counts["tie"],
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
