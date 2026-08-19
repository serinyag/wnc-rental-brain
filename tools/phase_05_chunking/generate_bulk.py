from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from tools.runtime_environment import validate_bootstrap_environment

from .bulk_chunking import bulk_document_map, generate_bulk_results
from .chunking import repo_root, serialize_results
from .generate_pilot import (
    CHUNKING_STRATEGY_CODE,
    CHUNKING_STRATEGY_VERSION,
    fetch_current_chunk_set,
    load_document_result,
    mark_processing_succeeded,
    run_supabase_query,
    sql_text,
)


@dataclass(frozen=True)
class BulkCoverageRecord:
    document_code: str
    canonical_title: str
    corpus_status: str
    governance_status: str
    source_locator: str | None
    source_role: str | None
    source_usage_disposition: str | None
    source_origin_type: str | None
    source_available: bool
    parser_selected: str | None
    parser_version: str | None
    chunking_disposition: str
    reason: str
    current_chunk_set_id: int | None
    current_chunk_count: int
    current_parser_version: str | None
    document_version_id: int
    document_version_source_object_id: int | None


ACTIVE_PILOT_CODES = {"SERV-001", "TPL-006", "TPL-007"}
PRESERVED_NON_ACTIVE_PILOT_CODES = {"OPS-001"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate or load the Phase 5 bulk semantic chunk corpus.")
    parser.add_argument("--write-json", type=Path, help="Write the generated eligible bulk payload to JSON.")
    parser.add_argument("--load-db", action="store_true", help="Load all eligible bulk chunk data into the local Supabase database.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    coverage = determine_bulk_coverage()
    target_codes = generation_target_codes(coverage)
    results = generate_bulk_results(target_codes)

    if args.write_json:
        args.write_json.parent.mkdir(parents=True, exist_ok=True)
        args.write_json.write_text(serialize_results(results) + "\n", encoding="utf-8")

    if args.load_db:
        validate_bootstrap_environment(operation_name="Phase 5 bulk DB load")
        load_bulk_into_local_db(results, coverage)

    print_summary(coverage, results)
    return 0


def determine_bulk_coverage() -> list[BulkCoverageRecord]:
    sql = """
with preferred_sources as (
  select
    kd.document_code,
    kdv.id as document_version_id,
    kdvso.id as document_version_source_object_id,
    kso.origin_type,
    coalesce(kso.repository_relative_path, kso.manual_reference_key, kso.external_uri, concat(kso.storage_bucket, '/', kso.storage_object_key)) as source_locator,
    ksor.role_code as source_role,
    kdvso.source_usage_disposition,
    row_number() over (
      partition by kd.document_code
      order by
        kdvso.is_preferred_extraction_source desc,
        case when kdvso.source_usage_disposition = 'eligible_for_extraction' then 0 else 1 end,
        kdvso.id
    ) as source_rank
  from public.knowledge_documents kd
  join public.knowledge_document_versions kdv
    on kdv.document_id = kd.id
  left join public.knowledge_document_version_source_objects kdvso
    on kdvso.document_version_id = kdv.id
  left join public.knowledge_source_objects kso
    on kso.id = kdvso.source_object_id
  left join public.knowledge_source_object_roles ksor
    on ksor.id = kdvso.source_object_role_id
),
current_chunk_sets as (
  select
    kd.document_code,
    kcs.id as current_chunk_set_id,
    kcs.parser_version as current_parser_version,
    count(kc.id) as current_chunk_count,
    row_number() over (
      partition by kd.document_code
      order by kcs.id desc
    ) as chunk_rank
  from public.knowledge_documents kd
  join public.knowledge_document_versions kdv
    on kdv.document_id = kd.id
  join private.knowledge_chunk_sets kcs
    on kcs.document_version_id = kdv.id
   and kcs.generation_status = 'current'
  left join private.knowledge_chunks kc
    on kc.chunk_set_id = kcs.id
  group by kd.document_code, kcs.id, kcs.parser_version
)
select
  kd.document_code,
  kd.canonical_title,
  kdcs.corpus_status,
  kdv.governance_status,
  ps.document_version_id,
  ps.document_version_source_object_id,
  ps.origin_type,
  ps.source_locator,
  ps.source_role,
  ps.source_usage_disposition,
  ccs.current_chunk_set_id,
  ccs.current_chunk_count,
  ccs.current_parser_version
from public.knowledge_documents kd
join public.knowledge_document_versions kdv
  on kdv.document_id = kd.id
join public.knowledge_document_corpus_states kdcs
  on kdcs.document_id = kd.id
 and kdcs.is_current
left join preferred_sources ps
  on ps.document_code = kd.document_code
 and ps.source_rank = 1
left join current_chunk_sets ccs
  on ccs.document_code = kd.document_code
 and ccs.chunk_rank = 1
order by kd.document_code;
""".strip()
    payload = run_supabase_query(sql, expect_json=True)
    config_map = bulk_document_map()
    root = repo_root()
    records: list[BulkCoverageRecord] = []
    for row in payload["rows"]:
        config = config_map.get(row["document_code"])
        source_locator = row["source_locator"]
        origin_type = row["origin_type"]
        source_available = False
        if origin_type == "repository_file" and source_locator:
            source_available = (root / source_locator).exists()

        disposition = "READY_TO_CHUNK"
        reason = "Active included document with an eligible local source and a deterministic parser."

        if row["document_code"] in PRESERVED_NON_ACTIVE_PILOT_CODES:
            disposition = "ALREADY_PILOTED"
            if row["current_chunk_set_id"] is not None:
                reason = "Approved pilot current chunk set is preserved even though governance status remains draft."
            else:
                reason = "Approved 5.3B pilot output is preserved for clean-environment reloads even though governance status remains draft."
        elif row["document_code"] in ACTIVE_PILOT_CODES and row["current_chunk_set_id"] is not None:
            disposition = "ALREADY_PILOTED"
            reason = "Approved 5.3B pilot current chunk set already exists and will be preserved unless output changes."
        elif row["corpus_status"] != "include":
            disposition = "EXCLUDED"
            reason = f"Current corpus status is {row['corpus_status']}, so the document is not part of the active chunkable set."
        elif row["governance_status"] != "active":
            disposition = "NOT_CURRENT"
            reason = f"Governance status is {row['governance_status']}, so the document is not an active bulk-chunking candidate."
        elif row["source_usage_disposition"] != "eligible_for_extraction":
            disposition = "EXCLUDED"
            reason = "Preferred source representation is not eligible for extraction."
        elif not source_locator:
            disposition = "PROVENANCE_REVIEW_REQUIRED"
            reason = "No sufficiently resolved extraction source locator is available for deterministic chunking."
        elif origin_type != "repository_file":
            disposition = "NO_SAFE_PARSER"
            reason = "Current eligible source is not a repository-backed text/workbook artifact supported by the approved deterministic parsers."
        elif not source_available:
            disposition = "SOURCE_UNAVAILABLE"
            reason = "Preferred extraction source is registered but not accessible in the local repository."
        elif config is None:
            disposition = "NO_SAFE_PARSER"
            reason = "No approved deterministic parser is configured for this active source structure."
            if row["document_code"] == "CF-001":
                reason = (
                    "Current eligible source is a PNG export with unresolved lookbook master/provenance drift, "
                    "so no safe deterministic chunk parser is approved."
                )

        records.append(
            BulkCoverageRecord(
                document_code=row["document_code"],
                canonical_title=row["canonical_title"],
                corpus_status=row["corpus_status"],
                governance_status=row["governance_status"],
                source_locator=source_locator,
                source_role=row["source_role"],
                source_usage_disposition=row["source_usage_disposition"],
                source_origin_type=origin_type,
                source_available=source_available,
                parser_selected=config.parser_kind if config else None,
                parser_version=config.parser_version if config else None,
                chunking_disposition=disposition,
                reason=reason,
                current_chunk_set_id=row["current_chunk_set_id"],
                current_chunk_count=row["current_chunk_count"] or 0,
                current_parser_version=row["current_parser_version"],
                document_version_id=row["document_version_id"],
                document_version_source_object_id=row["document_version_source_object_id"],
            )
        )
    return records


def generation_target_codes(coverage: list[BulkCoverageRecord]) -> list[str]:
    target_codes: list[str] = []
    for record in coverage:
        if record.chunking_disposition == "ALREADY_PILOTED":
            target_codes.append(record.document_code)
            continue
        if record.governance_status != "active":
            continue
        if record.chunking_disposition == "READY_TO_CHUNK":
            target_codes.append(record.document_code)
    return target_codes


def load_bulk_into_local_db(results, coverage: list[BulkCoverageRecord]) -> None:
    metadata = {
        record.document_code: {
            "canonical_title": record.canonical_title,
            "document_version_id": record.document_version_id,
            "document_version_source_object_id": record.document_version_source_object_id,
            "source_locator": record.source_locator,
        }
        for record in coverage
        if record.document_version_source_object_id is not None
    }
    for result in results:
        meta = metadata[result.document_code]
        current = fetch_current_chunk_set(result, meta["document_version_id"])
        if current and current["content_hashes"] == [chunk.content_hash for chunk in result.chunks]:
            mark_processing_succeeded(meta["document_version_id"])
            continue
        load_document_result(result, meta)

    for record in coverage:
        if record.document_code in generation_target_codes(coverage):
            continue
        if record.document_code in PRESERVED_NON_ACTIVE_PILOT_CODES and record.current_chunk_set_id is not None:
            continue
        mark_processing_not_applicable(record)


def mark_processing_not_applicable(record: BulkCoverageRecord) -> None:
    sql = f"""
insert into private.knowledge_document_version_processing (
  document_version_id,
  extraction_status,
  chunking_status,
  indexing_status,
  last_attempted_at,
  retry_count,
  last_error_code,
  last_error_message
)
values (
  {record.document_version_id},
  'not_applicable',
  'not_applicable',
  'not_applicable',
  timezone('utc', now()),
  0,
  {sql_text(record.chunking_disposition.lower())},
  {sql_text(record.reason)}
)
on conflict (document_version_id) do update
set extraction_status = 'not_applicable',
    chunking_status = 'not_applicable',
    indexing_status = 'not_applicable',
    last_attempted_at = timezone('utc', now()),
    retry_count = 0,
    last_error_code = excluded.last_error_code,
    last_error_message = excluded.last_error_message;
""".strip()
    run_supabase_query(sql, expect_json=False)


def print_summary(coverage: list[BulkCoverageRecord], results) -> None:
    summary = {
        "eligible_active_documents": sum(
            1
            for record in coverage
            if record.governance_status == "active"
            and record.chunking_disposition in {"READY_TO_CHUNK", "ALREADY_PILOTED"}
        ),
        "bulk_generation_targets": len(generation_target_codes(coverage)),
        "ready_to_chunk": sum(1 for record in coverage if record.chunking_disposition == "READY_TO_CHUNK"),
        "already_piloted": sum(1 for record in coverage if record.chunking_disposition == "ALREADY_PILOTED"),
        "source_unavailable": sum(1 for record in coverage if record.chunking_disposition == "SOURCE_UNAVAILABLE"),
        "no_safe_parser": sum(1 for record in coverage if record.chunking_disposition == "NO_SAFE_PARSER"),
        "not_current": sum(1 for record in coverage if record.chunking_disposition == "NOT_CURRENT"),
        "bulk_results_generated": len(results),
        "generated_chunk_total": sum(len(result.chunks) for result in results),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    for result in results:
        print(
            f"{result.document_code}"
            f" parser={result.parser_version}"
            f" chunks={len(result.chunks)}"
            f" path={result.relative_path}"
        )


if __name__ == "__main__":
    sys.exit(main())
