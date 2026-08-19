from __future__ import annotations

import argparse
import importlib
import json
import math
import subprocess
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from tools.phase_05_search.semantic_common import load_env_value
from tools.runtime_environment import AppRuntimeConfig, RuntimeConfigurationError, validate_bootstrap_environment

from .chunking import (
    CHUNKING_STRATEGY_CODE,
    CHUNKING_STRATEGY_VERSION,
    generate_pilot_results,
    pilot_document_map,
    repo_root,
    serialize_results,
)


@dataclass(frozen=True)
class PilotChunkLogicalRuleLink:
    section_heading: str
    rule_code: str
    relationship_type_code: str
    notes: str | None = None


PILOT_CHUNK_LOGICAL_RULE_LINKS: dict[str, tuple[PilotChunkLogicalRuleLink, ...]] = {
    "OPS-001": (
        PilotChunkLogicalRuleLink(
            section_heading="Full rental timeline",
            rule_code="OPER_SETUP_START_AT_BOOKED_TIME",
            relationship_type_code="operational_context_for",
        ),
        PilotChunkLogicalRuleLink(
            section_heading="Deliveries and collections",
            rule_code="OPER_SUPPLIER_ACCESS_APPROVED_TIMES_ONLY",
            relationship_type_code="operational_context_for",
        ),
        PilotChunkLogicalRuleLink(
            section_heading="Appointment-only visits",
            rule_code="OPER_EARLY_OPERATIONAL_ACCESS_REQUIRES_APPROVAL",
            relationship_type_code="operational_context_for",
        ),
        PilotChunkLogicalRuleLink(
            section_heading="Cleaning and reset",
            rule_code="OPER_PROFESSIONAL_CLEANING_MANUAL_REVIEW",
            relationship_type_code="operational_context_for",
        ),
    ),
    "SERV-001": (
        PilotChunkLogicalRuleLink(
            section_heading="Venue Only",
            rule_code="SERVICE_LEVEL_VENUE_ONLY",
            relationship_type_code="governed_by",
        ),
        PilotChunkLogicalRuleLink(
            section_heading="Supported Rental",
            rule_code="SERVICE_LEVEL_SUPPORTED_RENTAL",
            relationship_type_code="governed_by",
        ),
        PilotChunkLogicalRuleLink(
            section_heading="Full Production",
            rule_code="SERVICE_LEVEL_FULL_PRODUCTION",
            relationship_type_code="governed_by",
        ),
        PilotChunkLogicalRuleLink(
            section_heading="Event Manager",
            rule_code="SERVICE_ITEM_EVENT_MANAGER",
            relationship_type_code="governed_by",
        ),
        PilotChunkLogicalRuleLink(
            section_heading="Facilitator Sourcing",
            rule_code="SERVICE_ITEM_FACILITATOR_SOURCING",
            relationship_type_code="governed_by",
        ),
        PilotChunkLogicalRuleLink(
            section_heading="Facilitator Sourcing",
            rule_code="FACILITATOR_WNC_PROVIDED_CONFIRMATION_REQUIRED",
            relationship_type_code="governed_by",
        ),
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate or load the Phase 5 semantic chunking pilot.")
    parser.add_argument("--write-json", type=Path, help="Write the generated pilot payload to JSON.")
    parser.add_argument("--load-db", action="store_true", help="Load the pilot chunk data into the local Supabase database.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = generate_pilot_results()

    if args.write_json:
        args.write_json.parent.mkdir(parents=True, exist_ok=True)
        args.write_json.write_text(serialize_results(results) + "\n", encoding="utf-8")

    if args.load_db:
        validate_bootstrap_environment(operation_name="Phase 5 pilot DB load")
        load_pilot_into_local_db(results)

    print_summary(results)
    return 0


def print_summary(results) -> None:
    total_chunks = sum(len(result.chunks) for result in results)
    print(f"pilot_documents={len(results)}")
    print(f"total_chunks={total_chunks}")
    for result in results:
        print(
            f"{result.document_code}"
            f" parser={result.parser_version}"
            f" chunks={len(result.chunks)}"
            f" path={result.relative_path}"
        )


def load_pilot_into_local_db(results) -> None:
    metadata = fetch_pilot_db_metadata()
    for result in results:
        meta = metadata[result.document_code]
        current = fetch_current_chunk_set(result, meta["document_version_id"])
        if current and current["content_hashes"] == [chunk.content_hash for chunk in result.chunks]:
            sync_chunk_rule_links(result, current["id"])
            mark_processing_succeeded(meta["document_version_id"])
            continue
        load_document_result(result, meta)


def fetch_pilot_db_metadata() -> dict[str, dict]:
    codes = sorted(pilot_document_map().keys())
    code_list = ", ".join(f"'{code}'" for code in codes)
    sql = f"""
select
  kd.document_code,
  kd.canonical_title,
  kdv.id as document_version_id,
  kdvso.id as document_version_source_object_id,
  coalesce(kso.repository_relative_path, kso.manual_reference_key, kso.external_uri, concat(kso.storage_bucket, '/', kso.storage_object_key)) as source_locator
from public.knowledge_documents kd
join public.knowledge_document_versions kdv
  on kdv.document_id = kd.id
join public.knowledge_document_version_source_objects kdvso
  on kdvso.document_version_id = kdv.id
join public.knowledge_source_objects kso
  on kso.id = kdvso.source_object_id
where kd.document_code in ({code_list})
  and kdvso.is_preferred_extraction_source
  and kdvso.source_usage_disposition = 'eligible_for_extraction'
order by kd.document_code;
""".strip()
    payload = run_supabase_query(sql, expect_json=True)
    rows = payload["rows"]
    return {
        row["document_code"]: {
            "canonical_title": row["canonical_title"],
            "document_version_id": row["document_version_id"],
            "document_version_source_object_id": row["document_version_source_object_id"],
            "source_locator": row["source_locator"],
        }
        for row in rows
    }


def fetch_current_chunk_set(result, document_version_id: int) -> dict | None:
    sql = f"""
select
  kcs.id,
  array_agg(kc.content_hash order by kc.chunk_ordinal) as content_hashes
from private.knowledge_chunk_sets kcs
join private.knowledge_chunks kc
  on kc.chunk_set_id = kcs.id
where kcs.document_version_id = {document_version_id}
  and kcs.generation_status = 'current'
  and kcs.chunking_strategy_code = '{CHUNKING_STRATEGY_CODE}'
  and kcs.chunking_strategy_version = '{CHUNKING_STRATEGY_VERSION}'
  and kcs.parser_version = '{result.parser_version}'
group by kcs.id;
""".strip()
    payload = run_supabase_query(sql, expect_json=True)
    if not payload["rows"]:
        return None
    row = payload["rows"][0]
    return {
        "id": row["id"],
        "content_hashes": row["content_hashes"],
    }


def mark_processing_succeeded(document_version_id: int) -> None:
    sql = f"""
insert into private.knowledge_document_version_processing (
  document_version_id,
  extraction_status,
  chunking_status,
  indexing_status,
  last_attempted_at,
  last_succeeded_at,
  retry_count,
  last_error_code,
  last_error_message
)
values (
  {document_version_id},
  'succeeded',
  'succeeded',
  'not_applicable',
  timezone('utc', now()),
  timezone('utc', now()),
  0,
  null,
  null
)
on conflict (document_version_id) do update
set extraction_status = 'succeeded',
    chunking_status = 'succeeded',
    indexing_status = 'not_applicable',
    last_attempted_at = timezone('utc', now()),
    last_succeeded_at = timezone('utc', now()),
    last_error_code = null,
    last_error_message = null;
""".strip()
    run_supabase_query(sql, expect_json=False)


def load_document_result(result, meta: dict) -> None:
    try:
        run_supabase_query(build_load_sql(result, meta), expect_json=False)
        current = fetch_current_chunk_set(result, meta["document_version_id"])
        if current is None:
            raise RuntimeError(
                f"Pilot load succeeded for {result.document_code}, but no current chunk set was found for parser {result.parser_version}."
            )
        sync_chunk_rule_links(result, current["id"])
    except subprocess.CalledProcessError as exc:
        error_message = exc.stderr.strip() or exc.stdout.strip() or "unknown chunk loader failure"
        failure_sql = build_failure_sql(meta["document_version_id"], "pilot_generation_failed", error_message)
        run_supabase_query(failure_sql, expect_json=False)
        raise RuntimeError(
            f"Pilot load failed for {result.document_code}: {error_message}"
        ) from exc
    except Exception as exc:
        failure_sql = build_failure_sql(meta["document_version_id"], "pilot_generation_failed", str(exc))
        run_supabase_query(failure_sql, expect_json=False)
        raise


def build_load_sql(result, meta: dict) -> str:
    document_version_id = meta["document_version_id"]
    source_link_id = meta["document_version_source_object_id"]
    chunk_value_rows = []
    for chunk in result.chunks:
        chunk_value_rows.append(
            "("
            f"{chunk.chunk_ordinal}, "
            f"{sql_text(chunk.section_heading)}, "
            f"{sql_text(chunk.heading_path)}, "
            f"{sql_text(chunk.question_label)}, "
            f"{sql_text(chunk.document_title_snapshot)}, "
            f"{sql_text(chunk.body_text)}, "
            f"{sql_text(chunk.content_hash)}, "
            f"{chunk.token_count}, "
            f"{sql_text(chunk.source_locator)}"
            ")"
        )
    chunk_values_sql = ",\n      ".join(chunk_value_rows)
    return f"""
begin;

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
  {document_version_id},
  'ready',
  'ready',
  'not_applicable',
  null,
  0,
  null,
  null
)
on conflict (document_version_id) do nothing;

update private.knowledge_document_version_processing
set extraction_status = 'in_progress',
    chunking_status = 'in_progress',
    indexing_status = 'not_applicable',
    last_attempted_at = timezone('utc', now()),
    last_succeeded_at = null,
    last_error_code = null,
    last_error_message = null
where document_version_id = {document_version_id};

update private.knowledge_chunk_sets
set generation_status = 'superseded'
where document_version_id = {document_version_id}
  and generation_status = 'current';

with inserted_chunk_set as (
  insert into private.knowledge_chunk_sets (
    document_version_id,
    chunking_strategy_code,
    chunking_strategy_version,
    parser_version,
    generation_status,
    generated_at
  )
  values (
    {document_version_id},
    '{CHUNKING_STRATEGY_CODE}',
    '{CHUNKING_STRATEGY_VERSION}',
    '{result.parser_version}',
    'current',
    timezone('utc', now())
  )
  returning id
),
inserted_chunk_set_source as (
  insert into private.knowledge_chunk_set_sources (
    chunk_set_id,
    document_version_source_object_id,
    source_usage_role
  )
  select
    inserted_chunk_set.id,
    {source_link_id},
    'primary_extraction'
  from inserted_chunk_set
  returning chunk_set_id
),
chunk_input (
  chunk_ordinal,
  section_heading,
  heading_path,
  question_label,
  document_title_snapshot,
  body_text,
  content_hash,
  token_count,
  source_locator
) as (
  values
      {chunk_values_sql}
),
inserted_chunks as (
  insert into private.knowledge_chunks (
    chunk_set_id,
    chunk_ordinal,
    section_heading,
    heading_path,
    question_label,
    document_title_snapshot,
    body_text,
    content_hash,
    token_count
  )
  select
    inserted_chunk_set_source.chunk_set_id,
    chunk_input.chunk_ordinal,
    chunk_input.section_heading,
    chunk_input.heading_path,
    chunk_input.question_label,
    chunk_input.document_title_snapshot,
    chunk_input.body_text,
    chunk_input.content_hash,
    chunk_input.token_count
  from inserted_chunk_set_source
  cross join chunk_input
  returning id, chunk_ordinal
)
insert into private.knowledge_chunk_sources (
  chunk_id,
  document_version_source_object_id,
  source_locator,
  is_primary_trace
)
select
  inserted_chunks.id,
  {source_link_id},
  chunk_input.source_locator,
  true
from inserted_chunks
join chunk_input
  on chunk_input.chunk_ordinal = inserted_chunks.chunk_ordinal;

update private.knowledge_document_version_processing
set extraction_status = 'succeeded',
    chunking_status = 'succeeded',
    indexing_status = 'not_applicable',
    last_succeeded_at = timezone('utc', now()),
    retry_count = 0,
    last_error_code = null,
    last_error_message = null
where document_version_id = {document_version_id};

commit;
""".strip()


def build_failure_sql(document_version_id: int, error_code: str, error_message: str) -> str:
    return f"""
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
  {document_version_id},
  'failed',
  'failed',
  'not_applicable',
  timezone('utc', now()),
  1,
  {sql_text(error_code)},
  {sql_text(error_message)}
)
on conflict (document_version_id) do update
set extraction_status = 'failed',
    chunking_status = 'failed',
    indexing_status = 'not_applicable',
    last_attempted_at = timezone('utc', now()),
    last_succeeded_at = null,
    retry_count = private.knowledge_document_version_processing.retry_count + 1,
    last_error_code = excluded.last_error_code,
    last_error_message = excluded.last_error_message;
""".strip()


def sync_chunk_rule_links(result, chunk_set_id: int) -> None:
    run_supabase_query(build_chunk_rule_sync_sql(result, chunk_set_id), expect_json=False)


def build_chunk_rule_sync_sql(result, chunk_set_id: int) -> str:
    logical_links = PILOT_CHUNK_LOGICAL_RULE_LINKS.get(result.document_code, ())
    logical_values_sql = ",\n      ".join(
        "("
        f"{sql_text(link.section_heading)}, "
        f"{sql_text(link.rule_code)}, "
        f"{sql_text(link.relationship_type_code)}, "
        f"{sql_text(link.notes)}"
        ")"
        for link in logical_links
    )
    logical_insert_sql = ""
    if logical_values_sql:
        logical_insert_sql = f"""
with logical_input (
  section_heading,
  rule_code,
  relationship_type_code,
  notes
) as (
  values
      {logical_values_sql}
),
desired_logical_links as (
  select
    kc.id as chunk_id,
    logical_input.rule_code,
    krrt.id as relationship_type_id,
    logical_input.notes
  from logical_input
  join private.knowledge_chunks kc
    on kc.chunk_set_id = {chunk_set_id}
   and kc.section_heading = logical_input.section_heading
  join public.knowledge_rule_relationship_types krrt
    on krrt.relationship_type_code = logical_input.relationship_type_code
),
deleted_logical_links as (
  delete from private.knowledge_chunk_logical_rules kclr
  where kclr.chunk_id in (
    select id
    from private.knowledge_chunks
    where chunk_set_id = {chunk_set_id}
  )
    and not exists (
      select 1
      from desired_logical_links dll
      where dll.chunk_id = kclr.chunk_id
        and dll.rule_code = kclr.rule_code
        and dll.relationship_type_id = kclr.relationship_type_id
    )
  returning 1
)
insert into private.knowledge_chunk_logical_rules (
  chunk_id,
  rule_code,
  relationship_type_id,
  notes
)
select
  dll.chunk_id,
  dll.rule_code,
  dll.relationship_type_id,
  dll.notes
from desired_logical_links dll
on conflict (chunk_id, rule_code, relationship_type_id) do update
set notes = excluded.notes;
""".strip()
    else:
        logical_insert_sql = f"""
delete from private.knowledge_chunk_logical_rules
where chunk_id in (
  select id
  from private.knowledge_chunks
  where chunk_set_id = {chunk_set_id}
);
""".strip()

    exact_sync_sql = f"""
delete from private.knowledge_chunk_rule_versions
where chunk_id in (
  select id
  from private.knowledge_chunks
  where chunk_set_id = {chunk_set_id}
);
""".strip()
    return "\n\n".join([logical_insert_sql, exact_sync_sql])


def sql_text(value: str | None) -> str:
    if value is None:
        return "null"
    return "'" + value.replace("'", "''") + "'"


def _starts_with_data_modifying_statement(sql: str) -> bool:
    stripped = sql.lstrip()
    if not stripped:
        return False
    first_token = stripped.split(None, 1)[0].lower()
    return first_token in {"insert", "update", "delete"}


def _starts_with_common_table_expression(sql: str) -> bool:
    stripped = sql.lstrip()
    if not stripped:
        return False
    first_token = stripped.split(None, 1)[0].lower()
    return first_token == "with"


def _skip_sql_whitespace(sql: str, index: int) -> int:
    length = len(sql)
    while index < length:
        if sql[index].isspace():
            index += 1
            continue
        if sql.startswith("--", index):
            line_end = sql.find("\n", index + 2)
            return length if line_end == -1 else _skip_sql_whitespace(sql, line_end + 1)
        if sql.startswith("/*", index):
            block_end = sql.find("*/", index + 2)
            if block_end == -1:
                raise ValueError("Unterminated SQL block comment.")
            index = block_end + 2
            continue
        break
    return index


def _consume_sql_identifier(sql: str, index: int) -> int:
    index = _skip_sql_whitespace(sql, index)
    if index >= len(sql):
        raise ValueError("Expected SQL identifier.")
    if sql[index] == '"':
        index += 1
        while index < len(sql):
            if sql[index] == '"':
                if index + 1 < len(sql) and sql[index + 1] == '"':
                    index += 2
                    continue
                return index + 1
            index += 1
        raise ValueError("Unterminated quoted SQL identifier.")
    if not (sql[index].isalpha() or sql[index] == "_"):
        raise ValueError("Expected SQL identifier.")
    index += 1
    while index < len(sql) and (sql[index].isalnum() or sql[index] in {"_", ".", "$"}):
        index += 1
    return index


def _consume_balanced_parenthesized_sql(sql: str, index: int) -> int:
    if index >= len(sql) or sql[index] != "(":
        raise ValueError("Expected parenthesized SQL expression.")
    depth = 0
    length = len(sql)
    while index < length:
        if sql.startswith("--", index):
            line_end = sql.find("\n", index + 2)
            if line_end == -1:
                return length
            index = line_end + 1
            continue
        if sql.startswith("/*", index):
            block_end = sql.find("*/", index + 2)
            if block_end == -1:
                raise ValueError("Unterminated SQL block comment.")
            index = block_end + 2
            continue
        character = sql[index]
        if character == "'":
            index += 1
            while index < length:
                if sql[index] == "'":
                    if index + 1 < length and sql[index + 1] == "'":
                        index += 2
                        continue
                    index += 1
                    break
                index += 1
            continue
        if character == '"':
            index += 1
            while index < length:
                if sql[index] == '"':
                    if index + 1 < length and sql[index + 1] == '"':
                        index += 2
                        continue
                    index += 1
                    break
                index += 1
            continue
        if character == "$":
            tag_end = sql.find("$", index + 1)
            if tag_end != -1:
                tag = sql[index : tag_end + 1]
                close_index = sql.find(tag, tag_end + 1)
                if close_index != -1:
                    index = close_index + len(tag)
                    continue
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    raise ValueError("Unterminated parenthesized SQL expression.")


def _consume_sql_keyword(sql: str, index: int, keyword: str) -> int:
    end = _consume_sql_identifier(sql, index)
    token = sql[index:end].strip().lower()
    if token != keyword:
        raise ValueError(f"Expected SQL keyword {keyword!r}, found {token!r}.")
    return end


def _split_top_level_with_query(sql: str) -> tuple[str, str]:
    normalized = sql.strip()
    index = _skip_sql_whitespace(normalized, 0)
    index = _consume_sql_keyword(normalized, index, "with")
    lookahead = _skip_sql_whitespace(normalized, index)
    try:
        recursive_end = _consume_sql_identifier(normalized, lookahead)
    except ValueError:
        recursive_end = lookahead
    else:
        if normalized[lookahead:recursive_end].lower() == "recursive":
            index = recursive_end
    while True:
        index = _consume_sql_identifier(normalized, index)
        index = _skip_sql_whitespace(normalized, index)
        if index < len(normalized) and normalized[index] == "(":
            index = _consume_balanced_parenthesized_sql(normalized, index)
        index = _skip_sql_whitespace(normalized, index)
        index = _consume_sql_keyword(normalized, index, "as")
        index = _skip_sql_whitespace(normalized, index)
        materialized_start = index
        try:
            token_end = _consume_sql_identifier(normalized, index)
        except ValueError:
            token_end = index
        else:
            token = normalized[index:token_end].lower()
            if token == "materialized":
                index = token_end
            elif token == "not":
                next_start = _skip_sql_whitespace(normalized, token_end)
                next_end = _consume_sql_keyword(normalized, next_start, "materialized")
                index = next_end
            else:
                index = materialized_start
        index = _skip_sql_whitespace(normalized, index)
        index = _consume_balanced_parenthesized_sql(normalized, index)
        index = _skip_sql_whitespace(normalized, index)
        if index < len(normalized) and normalized[index] == ",":
            index += 1
            continue
        break
    cte_clause = normalized[:index].rstrip()
    main_statement = normalized[index:].lstrip()
    if not main_statement:
        raise ValueError("WITH query is missing a main statement.")
    return cte_clause, main_statement


def _wrap_supabase_json_query(sql: str) -> str:
    normalized_sql = sql.strip().rstrip(";")
    if _starts_with_data_modifying_statement(normalized_sql):
        return (
            "with __query_result as (\n"
            f"{normalized_sql}\n"
            ")\n"
            "select coalesce(json_agg(row_to_json(__query_result)), '[]'::json)::text\n"
            "from __query_result;"
        )
    if _starts_with_common_table_expression(normalized_sql):
        cte_clause, main_statement = _split_top_level_with_query(normalized_sql)
        return (
            f"{cte_clause},\n"
            "__query_result as (\n"
            f"{main_statement}\n"
            ")\n"
            "select coalesce(json_agg(row_to_json(__query_result)), '[]'::json)::text\n"
            "from __query_result;"
        )
    return (
        "select coalesce(json_agg(row_to_json(t)), '[]'::json)::text\n"
        f"from (\n{normalized_sql}\n) as t;"
    )


DATABASE_URL_ENV = "DATABASE_URL"
_DIRECT_POSTGRES_CMD = ["direct_postgres", "execute"]


def direct_postgres_is_configured() -> bool:
    return _load_database_url() is not None


def _load_database_url() -> str | None:
    return load_env_value(DATABASE_URL_ENV)


def _direct_postgres_connect(database_url: str, *, timeout_seconds: float | None):
    try:
        psycopg = importlib.import_module("psycopg")
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised by focused tests
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=_DIRECT_POSTGRES_CMD,
            stderr="Direct PostgreSQL transport requires psycopg to be installed.",
        ) from exc

    connect_kwargs: dict[str, object] = {
        "autocommit": True,
    }
    if timeout_seconds is not None:
        connect_kwargs["connect_timeout"] = max(1, int(math.ceil(timeout_seconds)))
        connect_kwargs["options"] = f"-c statement_timeout={max(1, int(timeout_seconds * 1000))}"
    return psycopg.connect(database_url, **connect_kwargs)


def _drain_cursor_results(cursor) -> None:
    while True:
        try:
            has_more = cursor.nextset()
        except Exception:
            return
        if not has_more:
            return


def _direct_transport_timeout(exc: Exception, *, timeout_seconds: float | None) -> subprocess.TimeoutExpired | None:
    if timeout_seconds is None:
        return None
    sqlstate = getattr(exc, "sqlstate", None)
    message = str(exc).lower()
    if sqlstate == "57014" or "statement timeout" in message or "canceling statement due to statement timeout" in message:
        return subprocess.TimeoutExpired(cmd=_DIRECT_POSTGRES_CMD, timeout=timeout_seconds)
    return None


def _raise_direct_transport_failure(
    exc: Exception,
    *,
    timeout_seconds: float | None,
    database_url: str,
) -> None:
    timeout_error = _direct_transport_timeout(exc, timeout_seconds=timeout_seconds)
    if timeout_error is not None:
        raise timeout_error from exc
    safe_message = str(exc).replace(database_url, "[redacted]")
    raise subprocess.CalledProcessError(
        returncode=1,
        cmd=_DIRECT_POSTGRES_CMD,
        stderr=f"Direct PostgreSQL query failed: {safe_message}",
    ) from exc


def _run_direct_postgres_query(
    sql: str,
    *,
    expect_json: bool,
    database_url: str,
    timeout_seconds: float | None,
):
    statement = _wrap_supabase_json_query(sql) if expect_json else sql
    try:
        with _direct_postgres_connect(database_url, timeout_seconds=timeout_seconds) as connection:
            with connection.cursor() as cursor:
                cursor.execute(statement)
                if not expect_json:
                    _drain_cursor_results(cursor)
                    return None

                row = cursor.fetchone()
                payload = "[]"
                if row is not None and row:
                    payload = row[0] or "[]"
                _drain_cursor_results(cursor)
    except subprocess.CalledProcessError:
        raise
    except Exception as exc:  # pragma: no cover - integration-tested with a live DB
        _raise_direct_transport_failure(
            exc,
            timeout_seconds=timeout_seconds,
            database_url=database_url,
        )

    parsed = json.loads(payload)
    if isinstance(parsed, list):
        return {"rows": parsed}
    return parsed


def _run_local_docker_query(sql: str, *, expect_json: bool, timeout_seconds: float | None = None):
    container_name = find_local_db_container()
    if not expect_json:
        subprocess.run(
            [
                "docker",
                "exec",
                "-i",
                container_name,
                "psql",
                "-v",
                "ON_ERROR_STOP=1",
                "-U",
                "postgres",
                "-d",
                "postgres",
                "-X",
                "-f",
                "-",
            ],
            cwd=repo_root(),
            text=True,
            input=sql,
            capture_output=True,
            check=True,
            timeout=timeout_seconds,
        )
        return None

    wrapped_sql = _wrap_supabase_json_query(sql)
    completed = subprocess.run(
        [
            "docker",
            "exec",
            "-i",
            container_name,
            "psql",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            "postgres",
            "-d",
            "postgres",
            "-X",
            "-A",
            "-t",
            "-q",
            "-f",
            "-",
        ],
        cwd=repo_root(),
        text=True,
        input=wrapped_sql,
        capture_output=True,
        check=True,
        timeout=timeout_seconds,
    )
    stdout_lines = [line for line in completed.stdout.splitlines() if line.strip()]
    payload = stdout_lines[-1] if stdout_lines else "[]"
    parsed = json.loads(payload)
    if isinstance(parsed, list):
        return {"rows": parsed}
    return parsed


def run_supabase_query(sql: str, *, expect_json: bool, timeout_seconds: float | None = None):
    database_url = _load_database_url()
    if database_url is not None:
        return _run_direct_postgres_query(
            sql,
            expect_json=expect_json,
            database_url=database_url,
            timeout_seconds=timeout_seconds,
        )
    runtime = AppRuntimeConfig.from_env()
    if not runtime.allows_docker_db_fallback():
        raise RuntimeConfigurationError(
            f"DATABASE_URL is required when APP_ENV={runtime.app_env.value}; Docker DB fallback is local-only."
        )
    return _run_local_docker_query(sql, expect_json=expect_json, timeout_seconds=timeout_seconds)


@lru_cache(maxsize=1)
def find_local_db_container() -> str:
    completed = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}"],
        cwd=repo_root(),
        text=True,
        capture_output=True,
        check=True,
    )
    for line in completed.stdout.splitlines():
        if line.startswith("supabase_db_"):
            return line.strip()
    raise RuntimeError("Could not find a running local Supabase database container.")


if __name__ == "__main__":
    sys.exit(main())
