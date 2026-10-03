"""Prepare one synthetic canonical case and migration; never call Asana.

Intentionally one-shot. Existing marker or any changed protected lineage stops
the transaction. This is test fixture seeding, not an inbound authority path.
"""
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "docs/staging/outlook_recertification"))
import psycopg
from provider_free_fixture import query_runner
from tools.phase_05_search.semantic_common import load_env_value
from tools.staging_calibration.run_operator_calibration import build_client
from tools.phase_08_workflow.test_console_service import TestConsoleService, TestConsoleConfig
from tools.phase_08_workflow.tests.test_asana_projection import synthetic_repo
from tools.phase_08_workflow.asana_projection import prepare_projection
from tools.runtime_environment import AppRuntimeConfig, AppEnvironment

OUT = Path(__file__).parent
PROJECT = "1217642260793817"
WORKSPACE = "1208455784737302"
REFERENCE = "SYNTHETIC-ASANA-OPERATIONAL-20261003"
MIGRATION = ROOT / "supabase/migrations/20261003000200_phase_08_asana_projection_fences.sql"


def main():
    assert not (OUT / "staging_candidate.json").exists(), "Candidate already prepared; inspect before proceeding"
    assert load_env_value("SUPABASE_PROJECT_REF") == "mspcopnsbounmdpivkvq"
    client = build_client(ROOT / "Staging Authentications.txt", timeout_seconds=45)
    health = client.get_health()
    assert health["environment"] == "staging" and health["status"] == "ok"
    assert health["providers"] == {"asana": "configured_but_disabled", "outlook": "configured_draft_only"}
    protected = json.loads((ROOT / "docs/staging/outlook_reconciled_closure/raw_after.json").read_text())
    with psycopg.connect(host="db.mspcopnsbounmdpivkvq.supabase.co", dbname="postgres", user="postgres",
            password=load_env_value("SUPABASE_DB_PASSWORD"), sslmode="require", connect_timeout=15) as conn, \
         patch("urllib.request.urlopen", side_effect=AssertionError("No external providers allowed")):
        def protected_rows():
            return {cid: {table: conn.execute(f"select coalesce(json_agg(row_to_json(r) order by r.id),'[]') from public.{table} r where rental_case_id=%s",
                (int(cid),)).fetchone()[0] for table in tables} for cid, tables in protected.items()}
        assert protected_rows() == protected, "Protected case lineage differs from closed baseline"
        assert not conn.execute("select 1 from public.workflow_events where structured_payload->>'event_reference'=%s", (REFERENCE,)).fetchone()
        attempts_before = conn.execute("select count(*) from public.workflow_execution_attempts").fetchone()[0]
        assert not conn.execute("select 1 from supabase_migrations.schema_migrations where version='20261003000200'").fetchone()
        conn.execute(MIGRATION.read_text())
        conn.execute("insert into supabase_migrations.schema_migrations(version,name,statements) values(%s,%s,%s)",
            ("20261003000200", "phase_08_asana_projection_fences", [MIGRATION.read_text()]))
        service = TestConsoleService(query_runner=query_runner(conn), config=TestConsoleConfig(runtime=AppRuntimeConfig(
            app_env=AppEnvironment.STAGING, staging_allowed_asana_project_gids=(PROJECT,), staging_allow_real_asana=False), allow_real_providers=False))
        report = service.create_test_case(label="SYNTHETIC Asana operational certification",
            client_label="SYNTHETIC TEST — WNC Operations", contact_email=None, event_reference=REFERENCE)
        assert report.success
        cid = conn.execute("select rental_case_id from public.workflow_events where structured_payload->>'event_reference'=%s", (REFERENCE,)).fetchone()[0]
        fixture = synthetic_repo()
        case = fixture.rental_cases[1]
        conn.execute("update public.rental_cases set active_event_start=%s, active_event_end=%s, client_account_ref=%s, rental_type_code=%s where id=%s",
            (case.active_event_start, case.active_event_end, case.client_account_ref, case.rental_type_code, cid))
        for fact in fixture.rental_case_facts[1]:
            conn.execute("""insert into public.rental_case_facts(rental_case_id,field_code,domain_code,value_payload,source_reference,established_case_revision)
                values (%s,%s,%s,%s::jsonb,%s,0)""", (cid, fact.field_code, fact.domain_code, json.dumps(fact.value_payload), REFERENCE))
        for action in fixture.workflow_actions[1]:
            service.orchestration_repository.create_workflow_action(replace(action, rental_case_id=cid,
                idempotency_key=f"{REFERENCE}:{cid}:{action.structured_payload['resolution_item_key']}",
                created_at=service.now(), updated_at=service.now()))
        prepared = prepare_projection(service.orchestration_repository, rental_case_id=cid,
            workspace_gid=WORKSPACE, project_gid=PROJECT, now=service.now())
        plan = prepared.structured_payload["projection"]
        assert conn.execute("select count(*) from public.workflow_execution_attempts").fetchone()[0] == attempts_before
        assert protected_rows() == protected
        result = {"rental_case_id": cid, "workflow_action_id": prepared.workflow_action_id,
            "projection": plan, "canonical_hash": prepared.semantic_subject_hash,
            "provider_mutations": 0, "new_execution_attempts": 0, "protected_cases_unchanged": [424, 584],
            "migration": "20261003000200", "migration_sha256": hashlib.sha256(MIGRATION.read_bytes()).hexdigest()}
    # Only after successful transaction commit.
    (OUT / "staging_candidate.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k:v for k,v in result.items() if k != "projection"}))


if __name__ == "__main__":
    main()
