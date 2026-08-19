from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from tools.phase_05_chunking.generate_pilot import run_supabase_query, sql_text

from .semantic_common import (
    EmbeddingModelConfig,
    OpenAIEmbeddingsClient,
    SearchAssessment,
    SearchFixture,
    assess_search_results,
    assessment_rank,
    embed_query_text,
    vector_sql_literal,
)


@dataclass(frozen=True)
class TimedRows:
    rows: list[dict]
    elapsed_ms: float


FIXTURES: tuple[SearchFixture, ...] = (
    SearchFixture(
        query="external caterer",
        expected_codes=("SERV-003", "SERV-004"),
        note="Exact governed terminology should remain strong under both lexical and semantic retrieval.",
    ),
    SearchFixture(
        query="can we bring our own catering",
        expected_codes=("SERV-003", "SERV-004", "TPL-006"),
        note="This paraphrase tests whether semantic search improves recall when the user avoids the exact corpus phrasing external caterer.",
    ),
    SearchFixture(
        query="payment within 14 days",
        expected_codes=("GOV-002", "CF-003", "CF-005", "CF-007", "TPL-006"),
        note="This is the known FTS caveat and should be inspected for document-role effects rather than forced into one preferred family.",
    ),
    SearchFixture(
        query="when does the remaining balance need to be paid",
        expected_codes=("CF-005", "CF-007", "TPL-006", "CF-003"),
        note="This paraphrase should prefer current operational payment language if semantic search is helping with meaning over literal phrasing.",
    ),
    SearchFixture(
        query="site visit",
        expected_codes=("TPL-008", "TPL-006", "TPL-009"),
        note="Checklist and communication guidance should dominate ordinary venue-visit phrasing.",
    ),
    SearchFixture(
        query="can we visit the venue beforehand",
        expected_codes=("TPL-008", "TPL-006", "TPL-007"),
        note="This paraphrase checks whether semantic search can recover venue-visit intent when exact site visit vocabulary is absent.",
    ),
    SearchFixture(
        query="setup and breakdown",
        expected_codes=("TPL-009", "CF-007", "TPL-001", "TPL-002", "TPL-003", "TPL-004", "TPL-005"),
        note="Current search still excludes draft OPS-001, so semantic recall must come from other governed active chunk families.",
    ),
    SearchFixture(
        query="projector",
        expected_codes=("OPS-002", "TPL-009", "SERV-001"),
        note="Technical inventory should normally dominate direct equipment nouns.",
    ),
    SearchFixture(
        query="cancellation",
        expected_codes=("CF-007", "TPL-006", "CF-005", "CF-003"),
        note="Chunk retrieval should surface current cancellation guidance even without the deterministic Phase 4 tables.",
    ),
    SearchFixture(
        query="supported rental",
        expected_codes=("SERV-001",),
        note="This is a strong exact governed service term and often remains a lexical win.",
    ),
    SearchFixture(
        query="security deposit",
        expected_codes=("CF-007", "TPL-013", "CF-005", "GOV-002"),
        note="Both active agreement language and active governance decisions are genuinely relevant here.",
    ),
    SearchFixture(
        query="sparkling water",
        expected_codes=("SERV-003",),
        note="A concrete catalogue term should remain straightforward for both search modes.",
    ),
    SearchFixture(
        query="facilitator sourcing",
        expected_codes=("SERV-001", "TPL-006"),
        note="This should reward semantic similarity across services and communication guidance.",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate the Phase 5 semantic search baseline against FTS.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/phase-05/search/phase-05-semantic-search-evaluation.md"),
        help="Markdown report path to write.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of top results to capture per query.",
    )
    return parser.parse_args()


def body_preview(body_text: str, limit: int = 150) -> str:
    compact = " ".join(body_text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def load_active_retrieval_model() -> dict:
    sql = """
select
  id,
  provider_code,
  model_code,
  model_version,
  embedding_dimensions,
  configuration_json
from private.knowledge_embedding_models
where is_retrieval_approved
  and is_active
order by id;
""".strip()
    payload = run_supabase_query(sql, expect_json=True)
    rows = payload["rows"]
    if not rows:
        raise SystemExit("No active retrieval-approved embedding model is registered. Run embedding generation first.")
    if len(rows) > 1:
        raise SystemExit("Multiple active retrieval-approved embedding models are registered. Narrow the registry before evaluation.")
    return rows[0]


def build_config_from_registry(row: dict) -> EmbeddingModelConfig:
    cfg = row["configuration_json"] or {}
    return EmbeddingModelConfig(
        provider_code=row["provider_code"],
        model_code=row["model_code"],
        model_version=row["model_version"],
        embedding_dimensions=row["embedding_dimensions"],
        distance_metric=cfg.get("distance_metric", "cosine"),
        input_contract_code=cfg.get("input_contract_code", "phase_05_chunk_embedding_input_v1"),
        encoding_format=cfg.get("encoding_format", "float"),
        api_base_url=cfg.get("api_base_url", "https://api.openai.com/v1"),
        is_retrieval_approved=True,
        is_active=True,
    )


def fetch_coverage(model_id: int) -> dict[str, int | float]:
    sql = f"""
with current_embeddings as (
  select distinct ckei.chunk_id
  from private.current_knowledge_chunk_embedding_inputs ckei
  join private.knowledge_embeddings ke
    on ke.chunk_id = ckei.chunk_id
   and ke.embedding_model_id = {model_id}
   and ke.input_content_hash = ckei.embedding_input_hash
)
select
  (select count(*) from private.current_knowledge_chunk_embedding_inputs)::integer as eligible_chunks,
  (select count(distinct document_code) from private.current_knowledge_chunk_embedding_inputs)::integer as eligible_documents,
  (select count(*) from current_embeddings)::integer as embedded_chunks;
""".strip()
    payload = run_supabase_query(sql, expect_json=True)
    row = payload["rows"][0]
    row["missing_chunks"] = row["eligible_chunks"] - row["embedded_chunks"]
    row["coverage_percent"] = (
        0.0 if row["eligible_chunks"] == 0 else round((row["embedded_chunks"] / row["eligible_chunks"]) * 100, 2)
    )
    return row


def run_fts_search(query: str, limit: int) -> TimedRows:
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
    started = time.perf_counter()
    payload = run_supabase_query(sql, expect_json=True)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return TimedRows(rows=payload["rows"], elapsed_ms=elapsed_ms)


def run_semantic_search(
    query_vector: list[float],
    limit: int,
    model_id: int,
) -> TimedRows:
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
  question_label,
  body_text,
  similarity_score,
  cosine_distance,
  primary_source_locator,
  primary_category_code,
  embedding_model_id
from private.search_knowledge_chunks_semantic(
  {vector_sql_literal(query_vector)}::extensions.vector,
  {limit},
  {model_id}
);
""".strip()
    started = time.perf_counter()
    payload = run_supabase_query(sql, expect_json=True)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return TimedRows(rows=payload["rows"], elapsed_ms=elapsed_ms)


def compare_assessments(fts: SearchAssessment, semantic: SearchAssessment) -> str:
    if assessment_rank(semantic.status) > assessment_rank(fts.status):
        return "semantic search improves recall for this phrasing"
    if assessment_rank(semantic.status) < assessment_rank(fts.status):
        return "FTS remains stronger for this phrasing"
    return "FTS and semantic search perform similarly for this phrasing"


def render_report(limit: int) -> str:
    model = load_active_retrieval_model()
    config = build_config_from_registry(model)
    if config.provider_code != "openai":
        raise SystemExit(f"Only provider_code='openai' is currently supported by the repository semantic evaluator.")

    coverage = fetch_coverage(model["id"])
    if coverage["embedded_chunks"] == 0:
        raise SystemExit("No current eligible chunks have embeddings for the active retrieval model.")

    client = OpenAIEmbeddingsClient()
    results: list[tuple[SearchFixture, SearchAssessment, SearchAssessment, TimedRows, TimedRows, float]] = []
    for fixture in FIXTURES:
        embedding_started = time.perf_counter()
        query_vector = embed_query_text(client, fixture.query, config)
        embedding_elapsed_ms = (time.perf_counter() - embedding_started) * 1000
        fts_rows = run_fts_search(fixture.query, limit)
        semantic_rows = run_semantic_search(query_vector, limit, model["id"])
        fts_assessment = assess_search_results(fixture, fts_rows.rows)
        semantic_assessment = assess_search_results(fixture, semantic_rows.rows)
        results.append(
            (fixture, fts_assessment, semantic_assessment, fts_rows, semantic_rows, embedding_elapsed_ms)
        )

    strong = [fixture.query for fixture, _, semantic_assessment, _, _, _ in results if semantic_assessment.status == "strong"]
    partial = [fixture.query for fixture, _, semantic_assessment, _, _, _ in results if semantic_assessment.status == "partial"]
    weak = [fixture.query for fixture, _, semantic_assessment, _, _, _ in results if semantic_assessment.status == "weak"]
    misses = [fixture.query for fixture, _, semantic_assessment, _, _, _ in results if semantic_assessment.status == "miss"]

    avg_embedding_ms = round(sum(item[5] for item in results) / len(results), 2)
    avg_fts_ms = round(sum(item[3].elapsed_ms for item in results) / len(results), 2)
    avg_semantic_ms = round(sum(item[4].elapsed_ms for item in results) / len(results), 2)

    lines: list[str] = []
    lines.append("# Phase 5 Semantic Search Evaluation")
    lines.append("")
    lines.append(f"Date: {date.today():%B %-d, %Y}")
    lines.append("")
    lines.append("## Configuration")
    lines.append("")
    lines.append(f"- provider: `{model['provider_code']}`")
    lines.append(f"- model: `{model['model_code']}`")
    lines.append(f"- model version: `{model['model_version'] or '(none recorded)'}`")
    lines.append(f"- embedding dimensions: `{model['embedding_dimensions']}`")
    lines.append(f"- similarity metric: `{config.distance_metric}`")
    lines.append("- vector distance operator: `<=>` (cosine distance)")
    lines.append("- similarity score conversion: `1 - cosine_distance`")
    lines.append(f"- top results captured per query: `{limit}`")
    lines.append("")
    lines.append("## Coverage")
    lines.append("")
    lines.append(f"- eligible searchable documents: `{coverage['eligible_documents']}`")
    lines.append(f"- eligible searchable chunks: `{coverage['eligible_chunks']}`")
    lines.append(f"- chunks with current approved embeddings: `{coverage['embedded_chunks']}`")
    lines.append(f"- chunks missing approved embeddings: `{coverage['missing_chunks']}`")
    lines.append(f"- coverage percent: `{coverage['coverage_percent']}`")
    lines.append("")
    lines.append("## Evaluation Summary")
    lines.append("")
    lines.append(f"- semantic strong: `{len(strong)}`")
    lines.append(f"- semantic partial: `{len(partial)}`")
    lines.append(f"- semantic weak: `{len(weak)}`")
    lines.append(f"- semantic misses: `{len(misses)}`")
    lines.append(f"- average query-embedding time (ms): `{avg_embedding_ms}`")
    lines.append(f"- average FTS search time (ms): `{avg_fts_ms}`")
    lines.append(f"- average exact semantic search time (ms): `{avg_semantic_ms}`")
    if misses:
        lines.append(f"- semantic misses: `{', '.join(misses)}`")
    lines.append("")
    lines.append("## Query Results")
    lines.append("")

    for fixture, fts_assessment, semantic_assessment, fts_rows, semantic_rows, embedding_elapsed_ms in results:
        lines.append(f"### `{fixture.query}`")
        lines.append("")
        lines.append(f"- expected families: `{', '.join(fixture.expected_codes)}`")
        if fixture.note:
            lines.append(f"- fixture note: {fixture.note}")
        lines.append(f"- FTS assessment: `{fts_assessment.status}` - {fts_assessment.explanation}")
        lines.append(f"- semantic assessment: `{semantic_assessment.status}` - {semantic_assessment.explanation}")
        lines.append(f"- comparison: {compare_assessments(fts_assessment, semantic_assessment)}")
        lines.append(f"- query embedding time (ms): `{embedding_elapsed_ms:.2f}`")
        lines.append(f"- FTS search time (ms): `{fts_rows.elapsed_ms:.2f}`")
        lines.append(f"- semantic search time (ms): `{semantic_rows.elapsed_ms:.2f}`")
        lines.append("- FTS top results:")
        if not fts_rows.rows:
            lines.append("  - none")
        else:
            for idx, row in enumerate(fts_rows.rows, start=1):
                section = row["section_heading"] or "(no section heading)"
                lines.append(
                    f"  - `{idx}` `{row['document_code']}` {row['document_title']} | "
                    f"section `{section}` | rank `{row['relevance_score']:.6f}` | preview: {body_preview(row['body_text'])}"
                )
        lines.append("- semantic top results:")
        if not semantic_rows.rows:
            lines.append("  - none")
        else:
            for idx, row in enumerate(semantic_rows.rows, start=1):
                section = row["section_heading"] or "(no section heading)"
                lines.append(
                    f"  - `{idx}` `{row['document_code']}` {row['document_title']} | "
                    f"section `{section}` | similarity `{row['similarity_score']:.6f}` | "
                    f"distance `{row['cosine_distance']:.6f}` | preview: {body_preview(row['body_text'])}"
                )
        lines.append("")

    lines.append("## GOV-002 Check")
    lines.append("")
    gov_case = next(item for item in results if item[0].query == "payment within 14 days")
    gov_fts_top = gov_case[3].rows[0]["document_code"] if gov_case[3].rows else "(none)"
    gov_semantic_top = gov_case[4].rows[0]["document_code"] if gov_case[4].rows else "(none)"
    lines.append(f"- FTS top result for `payment within 14 days`: `{gov_fts_top}`")
    lines.append(f"- semantic top result for `payment within 14 days`: `{gov_semantic_top}`")
    lines.append(
        "- This comparison should be read as retrieval-policy evidence, not as proof that one result family is inherently incorrect."
    )
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    lines.append("- Semantic search is evaluated independently from FTS here; no hybrid scoring was added in this task.")
    lines.append("- Exact vector scan remains practical at the current corpus size, so this baseline isolates semantic quality without ANN approximation effects.")
    lines.append("- FTS can still remain better for precise governed terminology, while semantic search should mainly be judged on paraphrase recovery and meaning-preserving rewrites.")
    lines.append("- Active governance documents such as `GOV-002` may remain semantically relevant even when later application flows choose to prefer client-facing or operational materials.")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    output = render_report(args.limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
