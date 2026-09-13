"""Optional local-Postgres round trip; every change rolls back."""
import os
import unittest
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlparse

from tools.phase_08_workflow.outlook_action_contract import build_governed_outlook_action, validate_outlook_action, OutlookContractError
from tools.phase_08_workflow.orchestration_repository import SupabaseWorkflowOrchestrationRepository
from tools.phase_08_workflow.tests.test_outlook_action_contract import canonical_fixture, INTENT


@unittest.skipUnless(os.environ.get("WNC_TEST_POSTGRES_DSN"), "requires explicitly selected local Postgres")
class OutlookRepositoryDatabaseTests(unittest.TestCase):
    def test_reservation_binding_and_identity_uniqueness_in_postgres(self):
        import psycopg
        from psycopg.rows import dict_row
        dsn = os.environ["WNC_TEST_POSTGRES_DSN"]
        self.assertIn(urlparse(dsn).hostname, {"localhost", "127.0.0.1", "::1"})
        root = Path(__file__).resolve().parents[3]
        with psycopg.connect(dsn, row_factory=dict_row) as conn, conn.transaction(force_rollback=True):
            for name in ("20260907000100_phase_08_governed_client_response_action_type.sql",
                         "20260913000100_phase_08_outlook_canonical_plan_identity.sql"):
                conn.execute((root / "supabase" / "migrations" / name).read_text())
            case_id = conn.execute("""insert into public.rental_cases
                (case_reference_code,lifecycle_state,case_revision,rental_type_code)
                values ('RC-998877665544','inquiry_active',3,'studio_space') returning id""").fetchone()["id"]
            def runner(sql, *, expect_json):
                result = conn.execute(sql)
                return {"rows": result.fetchall()} if expect_json else None
            repo = SupabaseWorkflowOrchestrationRepository(query_runner=runner)
            case, revision, reservation, _ = canonical_fixture(case_id=case_id)
            reservation = repo.create_workflow_action(reservation)
            revision = replace(revision, workflow_action_id=reservation.workflow_action_id)
            action = build_governed_outlook_action(reservation=reservation, case=case, revision=revision,
                intent=INTENT, governed_context_hash="governed-424", provenance="normal", graph_message_id=None)
            bound = repo.bind_outlook_action(reservation, action)
            validate_outlook_action(bound)
            self.assertEqual(bound.structured_payload, action.structured_payload)
            # A stale construction snapshot cannot insert a second reservation.
            self.assertEqual(repo.create_workflow_action(reservation).workflow_action_id, bound.workflow_action_id)
            with conn.transaction(force_rollback=True):
                with self.assertRaises(psycopg.errors.UniqueViolation):
                    conn.execute("""insert into public.workflow_actions
                        (rental_case_id,action_type,action_category,target_adapter_code,reason_entity_type,reason_entity_reference,
                         structured_payload,approval_posture,status,semantic_subject_hash,source_case_revision,idempotency_key)
                        select rental_case_id,action_type,action_category,target_adapter_code,reason_entity_type,reason_entity_reference,
                               structured_payload,approval_posture,status,semantic_subject_hash,source_case_revision,'duplicate-plan-test'
                        from public.workflow_actions where id=%s""", (bound.workflow_action_id,))
            changed = build_governed_outlook_action(reservation=reservation, case=case,
                revision=replace(revision, body_text="Different body"), intent=INTENT,
                governed_context_hash="governed-424", provenance="normal", graph_message_id=None)
            with self.assertRaises(OutlookContractError):
                repo.bind_outlook_action(reservation, changed)
            self.assertEqual(repo.create_workflow_action(reservation).structured_payload, bound.structured_payload)
