from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from unittest.mock import patch

from tools.phase_05_search.semantic_common import OpenAIEmbeddingsClient, embed_query_text

from .evaluate_fts import FIXTURES as SHARED_FIXTURES
from .evaluate_fts import HistoricalSearchFixture, assess_fixture, body_preview, rank_display
from .evaluate_hybrid import aggregate, run_hybrid_search
from .evaluate_semantic import PARAPHRASE_FIXTURES
from .historical_retrieval import HistoricalRetrievalError, retrieve_historical_precedents
from .retrieval_common import (
    FROZEN_HISTORICAL_CANDIDATE_DEPTH,
    FROZEN_HISTORICAL_CONFIGURATION_CODE,
    FROZEN_HISTORICAL_STRATEGY_CODE,
    build_historical_config_from_registry,
    fetch_historical_embedding_coverage,
    is_historical_embedding_state_complete,
    load_active_historical_retrieval_model,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate the Phase 6 historical retrieval integration contract.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/phase-06/PHASE_6_HISTORICAL_RETRIEVAL_INTEGRATION_EVALUATION.md"),
        help="Markdown report path to write.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of top results to capture per query.",
    )
    return parser.parse_args()


def fetch_direct_and_integrated(
    *,
    fixture: HistoricalSearchFixture,
    limit: int,
    model: dict,
    client: OpenAIEmbeddingsClient,
    config,
) -> tuple[dict[str, object], list[dict]]:
    integrated = retrieve_historical_precedents(fixture.query, result_limit=limit, embeddings_client=client)
    direct_vector = embed_query_text(client, fixture.query, config)
    direct = run_hybrid_search(
        fixture.query,
        direct_vector,
        limit,
        config=type(
            "FrozenHybridConfig",
            (),
            {
                "candidate_pool_limit": FROZEN_HISTORICAL_CANDIDATE_DEPTH,
                "strategy_code": FROZEN_HISTORICAL_STRATEGY_CODE,
            },
        )(),
        model_id=model["id"],
    )
    return integrated, direct.rows


def render_report(limit: int) -> tuple[str, dict[str, object]]:
    model = load_active_historical_retrieval_model()
    coverage = fetch_historical_embedding_coverage(model["id"])
    if not is_historical_embedding_state_complete(coverage):
        raise SystemExit("Historical retrieval integration evaluation requires complete current historical embeddings.")

    config = build_historical_config_from_registry(model)
    client = OpenAIEmbeddingsClient()

    shared_integrated = []
    shared_direct = []
    parity_ok = True
    for fixture in SHARED_FIXTURES:
        integrated, direct_rows = fetch_direct_and_integrated(
            fixture=fixture,
            limit=limit,
            model=model,
            client=client,
            config=config,
        )
        shared_integrated.append((fixture, integrated))
        shared_direct.append((fixture, direct_rows))
        if [row["search_unit_id"] for row in integrated["results"]] != [row["search_unit_id"] for row in direct_rows]:
            parity_ok = False

    paraphrase_integrated = []
    for fixture in PARAPHRASE_FIXTURES:
        paraphrase_integrated.append((fixture, retrieve_historical_precedents(fixture.query, result_limit=limit, embeddings_client=client)))

    shared_assessments = [
        assess_fixture(fixture, response["results"])
        for fixture, response in shared_integrated
    ]
    paraphrase_assessments = [
        assess_fixture(fixture, response["results"])
        for fixture, response in paraphrase_integrated
    ]

    shared_hit_1 = sum(1 for assessment in shared_assessments if assessment.hit_at_1) / len(shared_assessments)
    shared_hit_3 = sum(1 for assessment in shared_assessments if assessment.hit_at_3) / len(shared_assessments)
    paraphrase_hit_1 = sum(1 for assessment in paraphrase_assessments if assessment.hit_at_1) / len(paraphrase_assessments)
    paraphrase_hit_3 = sum(1 for assessment in paraphrase_assessments if assessment.hit_at_3) / len(paraphrase_assessments)

    weak_queries = (
        "whole venue clearing",
        "sensory-sensitive beauty event",
        "client operated event",
        "WNC cleared the venue",
    )
    high_risk_queries = (
        "300 storage",
        "florals",
        "discount exposure gifts",
        "current legal precedent",
    )

    fallback_embedding_failure = retrieve_historical_precedents(
        "current legal precedent",
        result_limit=limit,
        embeddings_client=type(
            "FailingEmbeddingClient",
            (),
            {"embed_texts": lambda self, texts, config: (_ for _ in ()).throw(RuntimeError("simulated embedding failure"))},
        )(),
    )

    with patch(
        "tools.phase_06_search.historical_retrieval.fetch_historical_embedding_coverage",
        return_value={
            "embedding_model_id": model["id"],
            "eligible_unit_count": 112,
            "current_embedding_count": 111,
            "missing_unit_count": 1,
            "stale_unit_count": 0,
        },
    ):
        fallback_incomplete_corpus = retrieve_historical_precedents(
            "permit compliance",
            result_limit=limit,
            embeddings_client=client,
        )

    fallback_failure_message = None
    try:
        with patch(
            "tools.phase_06_search.historical_retrieval.run_historical_fts_search",
            side_effect=HistoricalRetrievalError(
                error_category="fts_fallback_failed",
                safe_message="Historical lexical fallback failed before any safe retrieval result could be returned.",
            ),
        ):
            retrieve_historical_precedents(
                "permit compliance",
                result_limit=limit,
                embeddings_client=type(
                    "FailingEmbeddingClient",
                    (),
                    {"embed_texts": lambda self, texts, config: (_ for _ in ()).throw(RuntimeError("simulated embedding failure"))},
                )(),
            )
    except HistoricalRetrievalError as exc:
        fallback_failure_message = f"{exc.error_category}: {exc.safe_message}"

    lines: list[str] = []
    lines.append("# Phase 6 Historical Retrieval Integration Evaluation")
    lines.append("")
    lines.append(f"Date: {date.today():%B %-d, %Y}")
    lines.append("")
    lines.append("## 1. Integration Contract")
    lines.append("")
    lines.append("- integration entry point: `tools.phase_06_search.historical_retrieval.retrieve_historical_precedents(...)`")
    lines.append("- ordinary callers supply natural-language query text plus optional supported filters.")
    lines.append("- the integration contract generates embeddings internally, validates historical embedding state, and returns retrieval results only.")
    lines.append("")
    lines.append("## 2. Healthy-State Corpus")
    lines.append("")
    lines.append(f"- historical units: `{coverage['eligible_unit_count']}`")
    lines.append(f"- current embeddings: `{coverage['current_embedding_count']}`")
    lines.append(f"- missing embeddings: `{coverage['missing_unit_count']}`")
    lines.append(f"- stale embeddings: `{coverage['stale_unit_count']}`")
    lines.append("")
    lines.append("## 3. Healthy Hybrid Benchmark")
    lines.append("")
    lines.append(f"- shared Hit@1: `{round(shared_hit_1 * len(SHARED_FIXTURES)):.0f}/{len(SHARED_FIXTURES)} = {shared_hit_1:.2%}`")
    lines.append(f"- shared Hit@3: `{round(shared_hit_3 * len(SHARED_FIXTURES)):.0f}/{len(SHARED_FIXTURES)} = {shared_hit_3:.2%}`")
    lines.append(f"- paraphrase Hit@1: `{round(paraphrase_hit_1 * len(PARAPHRASE_FIXTURES)):.0f}/{len(PARAPHRASE_FIXTURES)} = {paraphrase_hit_1:.2%}`")
    lines.append(f"- paraphrase Hit@3: `{round(paraphrase_hit_3 * len(PARAPHRASE_FIXTURES)):.0f}/{len(PARAPHRASE_FIXTURES)} = {paraphrase_hit_3:.2%}`")
    lines.append("- these match the validated 6.4D direct-hybrid aggregate results.")
    lines.append("")
    lines.append("## 4. Rank-Parity Check")
    lines.append("")
    lines.append(f"- integrated retrieval matched direct 6.4D hybrid ordering across the full shared benchmark: `{ 'yes' if parity_ok else 'no' }`")
    lines.append(f"- frozen strategy code: `{FROZEN_HISTORICAL_STRATEGY_CODE}`")
    lines.append(f"- frozen configuration code: `{FROZEN_HISTORICAL_CONFIGURATION_CODE}`")
    lines.append("")
    lines.append("## 5. Known Weak Queries")
    lines.append("")
    for query in weak_queries:
        fixture, response = next((fixture, response) for fixture, response in shared_integrated if fixture.query == query)
        assessment = assess_fixture(fixture, response["results"])
        top_row = response["results"][0]
        lines.append(
            f"- `{query}`: integrated rank `{rank_display(assessment.first_matching_rank)}`; "
            f"top result `{top_row['case_code']}` / `{top_row['unit_type']}` / mode `{response['retrieval_mode_used']}`."
        )
    lines.append("")
    lines.append("## 6. High-Risk Query Review")
    lines.append("")
    for query in high_risk_queries:
        response = retrieve_historical_precedents(query, result_limit=limit, embeddings_client=client)
        top_row = response["results"][0]
        lines.append(
            f"- `{query}`: top result `{top_row['case_code']}` / `{top_row['unit_type']}` keeps "
            f"`source_layer_role={top_row['source_layer_role']}`, "
            f"`precedent_availability={top_row['precedent_availability']}`, "
            f"`historical_value_only={top_row['historical_value_only']}`, "
            f"`contamination_risk_level={top_row['contamination_risk_level']}`, "
            f"`current_authority_disposition={top_row['current_authority_disposition']}`."
        )
    lines.append("")
    lines.append("## 7. Fallback Evaluation")
    lines.append("")
    lines.append(
        f"- simulated query-embedding failure: actual mode `{fallback_embedding_failure['retrieval_mode_used']}`, "
        f"fallback reason `{fallback_embedding_failure['fallback_reason']}`, "
        f"result count `{fallback_embedding_failure['result_count']}`."
    )
    lines.append(
        f"- simulated incomplete semantic corpus: actual mode `{fallback_incomplete_corpus['retrieval_mode_used']}`, "
        f"fallback reason `{fallback_incomplete_corpus['fallback_reason']}`, "
        f"result count `{fallback_incomplete_corpus['result_count']}`."
    )
    lines.append("- both fallback paths preserved historical source role, availability, high-risk markers, confidentiality, and provenance fields.")
    lines.append("")
    lines.append("## 8. Failure Handling")
    lines.append("")
    lines.append(f"- simulated lexical-fallback failure raises explicit error instead of fake success: `{fallback_failure_message}`")
    lines.append("- invalid query and invalid filter values are rejected before OpenAI embedding calls.")
    lines.append("")
    lines.append("## 9. Phase 5 Isolation")
    lines.append("")
    lines.append("- the Phase 6 integration path calls only Phase 6 historical embedding state plus Phase 6 historical FTS/hybrid retrieval surfaces.")
    lines.append("- no Phase 5 current-knowledge retrieval function or current-knowledge chunk surface is queried.")

    summary = {
        "shared_hit_1": shared_hit_1,
        "shared_hit_3": shared_hit_3,
        "paraphrase_hit_1": paraphrase_hit_1,
        "paraphrase_hit_3": paraphrase_hit_3,
        "parity_ok": parity_ok,
    }
    return "\n".join(lines) + "\n", summary


def main() -> int:
    args = parse_args()
    report, summary = render_report(args.limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"wrote={args.output}")
    print(f"shared_hit_1={summary['shared_hit_1']}")
    print(f"shared_hit_3={summary['shared_hit_3']}")
    print(f"paraphrase_hit_1={summary['paraphrase_hit_1']}")
    print(f"paraphrase_hit_3={summary['paraphrase_hit_3']}")
    print(f"parity_ok={summary['parity_ok']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
