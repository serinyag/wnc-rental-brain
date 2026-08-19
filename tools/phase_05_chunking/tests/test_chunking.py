from __future__ import annotations

import unittest

from tools.phase_05_chunking.chunking import generate_pilot_results


class SemanticChunkingPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.results = {result.document_code: result for result in generate_pilot_results()}

    def test_ops_manual_preserves_expected_sections(self) -> None:
        ops = self.results["OPS-001"]
        headings = [chunk.section_heading for chunk in ops.chunks]
        self.assertIn("1. How to use this manual", headings)
        self.assertIn("General access rules", headings)
        self.assertIn("Room restrictions", headings)

    def test_unrelated_ops_headings_do_not_merge(self) -> None:
        ops = self.results["OPS-001"]
        alcohol = next(chunk for chunk in ops.chunks if chunk.section_heading == "Alcohol")
        sound = next(chunk for chunk in ops.chunks if chunk.section_heading == "Sound and amplified music")
        self.assertIn("Whether alcohol will be present", alcohol.body_text)
        self.assertNotIn("DJs", alcohol.body_text)
        self.assertIn("DJs", sound.body_text)
        self.assertNotIn("Whether alcohol will be present", sound.body_text)

    def test_email_template_chunk_stays_intact(self) -> None:
        email_library = self.results["TPL-006"]
        deposit_chunk = next(
            chunk
            for chunk in email_library.chunks
            if chunk.section_heading == "Deposit / Confirmation Payment Request"
        )
        self.assertIn("INTERNAL GUIDANCE", deposit_chunk.body_text)
        self.assertIn("CLIENT-FACING TEMPLATE", deposit_chunk.body_text)
        self.assertIn("minimum 30% confirmation deposit", deposit_chunk.body_text)
        self.assertIn("Payment of the confirmation deposit confirms acceptance", deposit_chunk.body_text)
        self.assertLess(
            deposit_chunk.body_text.index("INTERNAL GUIDANCE"),
            deposit_chunk.body_text.index("CLIENT-FACING TEMPLATE"),
        )

    def test_ops_wall_and_beam_use_remains_independent_short_chunk(self) -> None:
        ops = self.results["OPS-001"]
        wall_and_beam = next(chunk for chunk in ops.chunks if chunk.section_heading == "Wall and beam use")
        self.assertEqual(
            wall_and_beam.body_text,
            "Spot testing: photograph the area before and after where damage risk is material.",
        )
        self.assertLess(wall_and_beam.token_count, 20)
        self.assertNotIn("Do not drag furniture across floors", wall_and_beam.body_text)
        self.assertNotIn("No furniture, build-up, decoration", wall_and_beam.body_text)

    def test_checklist_sections_remain_distinct(self) -> None:
        checklist = self.results["TPL-007"]
        headings = [chunk.section_heading for chunk in checklist.chunks]
        self.assertIn("Space & layout", headings)
        self.assertIn("Food, beverage & experience", headings)
        self.assertIn("Production, technical & branding", headings)
        self.assertIn("Commercial & decision process", headings)
        self.assertNotIn("2. Site visit — if applicable", headings)

    def test_checklist_source_locators_are_deterministic(self) -> None:
        checklist = self.results["TPL-007"]
        locator = next(
            chunk.source_locator
            for chunk in checklist.chunks
            if chunk.section_heading == "Commercial & decision process"
        )
        self.assertEqual(
            locator,
            "Checklist section: 1. Discovery: understand the event > Commercial & decision process",
        )

    def test_shared_file_parser_keeps_tpl_007_logical_scope(self) -> None:
        checklist = self.results["TPL-007"]
        combined_text = "\n".join(chunk.body_text for chunk in checklist.chunks)
        self.assertNotIn("Site visit", combined_text)
        self.assertIn("Event objective:", combined_text)

    def test_service_catalogue_rows_become_structured_chunks(self) -> None:
        services = self.results["SERV-001"]
        venue_only = next(chunk for chunk in services.chunks if chunk.section_heading == "Venue Only")
        self.assertIn("Service code: venue_only", venue_only.body_text)
        self.assertIn("Guest management; event hosting; supplier management", venue_only.body_text)
        self.assertEqual(
            venue_only.source_locator,
            'Worksheet "Services catalogue", row 5, service code venue_only',
        )

    def test_service_catalogue_facilitator_chunk_excludes_deferred_catalogue_reference(self) -> None:
        services = self.results["SERV-001"]
        facilitator = next(chunk for chunk in services.chunks if chunk.section_heading == "Facilitator Sourcing")
        self.assertIn("Facilitator recommendations; availability checks; briefing", facilitator.body_text)
        self.assertIn("guaranteed availability before confirmation", facilitator.body_text)
        self.assertNotIn("Facilitators & Rental Experiences catalogue", facilitator.body_text)

    def test_regeneration_is_deterministic(self) -> None:
        first = generate_pilot_results()
        second = generate_pilot_results()
        first_hashes = {
            result.document_code: [chunk.content_hash for chunk in result.chunks]
            for result in first
        }
        second_hashes = {
            result.document_code: [chunk.content_hash for chunk in result.chunks]
            for result in second
        }
        self.assertEqual(first_hashes, second_hashes)


if __name__ == "__main__":
    unittest.main()
