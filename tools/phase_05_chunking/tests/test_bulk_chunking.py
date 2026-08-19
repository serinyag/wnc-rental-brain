from __future__ import annotations

import unittest

from tools.phase_05_chunking.bulk_chunking import generate_bulk_results
from tools.phase_05_chunking.generate_pilot import build_failure_sql, build_load_sql
from tools.phase_05_chunking.generate_bulk import determine_bulk_coverage, generation_target_codes


class BulkSemanticChunkingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.results = {result.document_code: result for result in generate_bulk_results()}
        cls.coverage = {record.document_code: record for record in determine_bulk_coverage()}

    def test_bulk_coverage_preserves_intentional_eligibility_boundaries(self) -> None:
        self.assertEqual(self.coverage["CF-001"].chunking_disposition, "NO_SAFE_PARSER")
        self.assertEqual(self.coverage["GOV-003"].chunking_disposition, "NOT_CURRENT")
        self.assertEqual(self.coverage["OPS-001"].chunking_disposition, "ALREADY_PILOTED")
        self.assertIn("TPL-008", generation_target_codes(list(self.coverage.values())))
        self.assertNotIn("GOV-003", generation_target_codes(list(self.coverage.values())))

    def test_agreement_parser_preserves_preface_and_schedule_tables(self) -> None:
        agreement = self.results["CF-007"]
        self.assertEqual(agreement.chunks[0].section_heading, "Agreement overview")
        combined_text = "\n".join(chunk.body_text for chunk in agreement.chunks)
        self.assertIn("Agreement ID:", combined_text)
        self.assertIn("Schedule 1", combined_text)
        self.assertIn("Schedule 2", combined_text)

    def test_numbered_template_parser_keeps_subsections_and_tables_together(self) -> None:
        proposal = self.results["TPL-004"]
        supplier_chunk = next(
            chunk
            for chunk in proposal.chunks
            if chunk.section_heading == "2A. Suppliers / Production Items"
        )
        self.assertEqual(
            supplier_chunk.heading_path,
            "2. Current Scope > 2A. Suppliers / Production Items",
        )
        self.assertIn("[Supplier / item] — [quote / status / client approved?]", supplier_chunk.body_text)

    def test_numbered_checklist_parser_splits_shared_discovery_and_site_visit_files(self) -> None:
        site_visit = self.results["TPL-008"]
        headings = [chunk.section_heading for chunk in site_visit.chunks]
        self.assertEqual(headings[0], "2. Site visit — if applicable")
        self.assertIn("Technical & installations", headings)
        combined_text = "\n".join(chunk.body_text for chunk in site_visit.chunks)
        self.assertNotIn("Event objective:", combined_text)

    def test_handover_and_final_readiness_stay_logically_separate(self) -> None:
        handover = self.results["TPL-009"]
        readiness = self.results["TPL-010"]
        handover_headings = [chunk.section_heading for chunk in handover.chunks]
        self.assertIn("6. Open Issues / Watch-Outs", handover_headings)
        self.assertNotIn("5. Final Readiness — complete before event", handover_headings)
        self.assertEqual([chunk.section_heading for chunk in readiness.chunks], ["5. Final Readiness — complete before event"])
        self.assertIn("Deposit / payment status complete for this stage", readiness.chunks[0].body_text)
        self.assertNotIn("Open issue:", readiness.chunks[0].body_text)

    def test_linear_checklist_parser_preserves_closeout_sections(self) -> None:
        checklist = self.results["TPL-013"]
        self.assertEqual(
            [chunk.section_heading for chunk in checklist.chunks],
            ["Checklist overview", "Close-out", "Final notes"],
        )
        self.assertIn("Post-event inspection complete", checklist.chunks[1].body_text)
        self.assertIn("Lesson worth recording", checklist.chunks[2].body_text)

    def test_governance_inventory_parser_creates_record_rows_without_header_chunks(self) -> None:
        inventory = self.results["GOV-001"]
        headings = [chunk.section_heading for chunk in inventory.chunks]
        self.assertIn("GOV-003 — WNC Rental Data Dictionary", headings)
        self.assertIn("Overview", headings)
        self.assertIn("Controlled lists", headings)
        self.assertNotIn("Source ID — Document name", headings)

    def test_policy_decision_parser_includes_open_decisions_without_header_chunks(self) -> None:
        decisions = self.results["GOV-002"]
        headings = [chunk.section_heading for chunk in decisions.chunks]
        self.assertIn("DEC-001 — Rental confirmation", headings)
        self.assertIn("OPEN-001 — Booking-fee waiver criteria", headings)
        self.assertNotIn("Decision ID — Topic", headings)
        open_decision = next(chunk for chunk in decisions.chunks if chunk.section_heading == "OPEN-001 — Booking-fee waiver criteria")
        self.assertIn("Status: Open", open_decision.body_text)

    def test_technical_inventory_parser_stays_out_of_shared_capacity_sheet(self) -> None:
        inventory = self.results["OPS-002"]
        headings = [chunk.section_heading for chunk in inventory.chunks]
        self.assertIn("SP-001 — Studio Space", headings)
        self.assertIn("TC-033 — Floor care", headings)
        self.assertNotIn("Space ID — Canonical space", headings)
        self.assertTrue(all('Worksheet "Sheet1"' not in chunk.source_locator for chunk in inventory.chunks))

    def test_capacity_rules_parser_uses_shared_workbook_without_field_drift(self) -> None:
        rules = self.results["OPS-003"]
        access_chunk = next(chunk for chunk in rules.chunks if chunk.section_heading == "ACC-001 — Studio Space rental")
        cap_chunk = next(chunk for chunk in rules.chunks if chunk.section_heading == "CAP-007 — 1:1 / Podcast Room")
        self.assertTrue(all('Worksheet "Sheet1"' in chunk.source_locator for chunk in rules.chunks))
        self.assertIn("Access ID: ACC-001", access_chunk.body_text)
        self.assertIn("Status: must_confirm", cap_chunk.body_text)
        self.assertIn("Notes: Do not publish a guest number until a layout is agreed.", cap_chunk.body_text)

    def test_catering_catalogue_parser_excludes_external_supplier_sheet(self) -> None:
        catalogue = self.results["SERV-003"]
        headings = [chunk.section_heading for chunk in catalogue.chunks]
        self.assertIn("CB-001 — Amelie", headings)
        self.assertIn("CBR-001 — Kitchen suitability", headings)
        self.assertIn("Controlled lists", headings)
        self.assertNotIn("Catalogue ID — Supplier", headings)
        self.assertTrue(
            all('External supplier requirements' not in chunk.source_locator for chunk in catalogue.chunks)
        )

    def test_external_supplier_parser_stays_scoped_to_shared_supplier_sheet(self) -> None:
        suppliers = self.results["SERV-004"]
        headings = [chunk.section_heading for chunk in suppliers.chunks]
        self.assertEqual(headings[0], "External supplier requirements overview")
        self.assertIn("SUP-TPL-001 — External caterer: TEMPLATE", headings)
        self.assertIn("SUP-001 — Amelie", headings)
        self.assertNotIn("Supplier ID — Supplier / company", headings)

    def test_bulk_generation_is_deterministic(self) -> None:
        first = generate_bulk_results()
        second = generate_bulk_results()
        first_hashes = {
            result.document_code: [chunk.content_hash for chunk in result.chunks]
            for result in first
        }
        second_hashes = {
            result.document_code: [chunk.content_hash for chunk in result.chunks]
            for result in second
        }
        self.assertEqual(first_hashes, second_hashes)

    def test_loader_sql_clears_previous_success_timestamp_when_reprocessing(self) -> None:
        result = self.results["CF-005"]
        load_sql = build_load_sql(
            result,
            {
                "document_version_id": 3,
                "document_version_source_object_id": 7,
            },
        )
        self.assertIn("last_succeeded_at = null,", load_sql)

        failure_sql = build_failure_sql(3, "pilot_generation_failed", "example")
        self.assertIn("last_succeeded_at = null,", failure_sql)


if __name__ == "__main__":
    unittest.main()
