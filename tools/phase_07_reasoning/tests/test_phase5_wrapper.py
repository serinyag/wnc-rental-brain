from __future__ import annotations

import inspect
import json
import unittest

from tools.phase_05_search.semantic_common import EmbeddingModelConfig
from tools.phase_07_reasoning.contracts import (
    AUTHORITY_TIER_CURRENT_GOVERNED,
    CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE,
    CONFIDENTIALITY_LEVEL_EXTERNALLY_SHAREABLE,
    CONFIDENTIALITY_LEVEL_RESTRICTED,
    EXECUTION_STATE_FAILED,
    EXECUTION_STATE_FALLBACK,
    EXECUTION_STATE_NOT_REQUESTED,
    EXECUTION_STATE_NO_RESULTS,
    EXECUTION_STATE_SUCCESS,
    EXECUTION_STATE_UNAVAILABLE,
    LAYER_ID_PHASE_5,
    PERSONAL_INFORMATION_STATUS_UNKNOWN,
    PERSONAL_INFORMATION_STATUS_YES,
    QUERY_CLASS_CURRENT_GUIDANCE,
    ROUTING_CONFIDENCE_HIGH,
    Phase5FilterIntent,
    Phase5RoutingIntent,
    Phase7RuntimeConfiguration,
    QueryPlan,
    SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE,
)
from tools.phase_07_reasoning.phase5_wrapper import (
    FALLBACK_REASON_EMBEDDING_MODEL_RESOLUTION_FAILED,
    FALLBACK_REASON_QUERY_EMBEDDING_FAILED,
    PHASE5_RETRIEVAL_MODE_USED_FTS_FALLBACK,
    PHASE5_RETRIEVAL_MODE_USED_HYBRID,
    Phase5ExecutionError,
    Phase5PreflightError,
    Phase5WrapperConfiguration,
    execute_phase5_plan,
)


def make_plan(
    *,
    query_text: str = "How should staff schedule and confirm a site visit?",
    phase5_query_text: str | None = None,
    required: bool = True,
    result_limit: int | None = 1,
    filters: Phase5FilterIntent | None = None,
) -> QueryPlan:
    return QueryPlan(
        query_text=query_text,
        query_class=QUERY_CLASS_CURRENT_GUIDANCE,
        routing_confidence=ROUTING_CONFIDENCE_HIGH,
        required_layers=(LAYER_ID_PHASE_5,) if required else (),
        phase_5=Phase5RoutingIntent(
            required=required,
            needs_guidance=required,
            query_text=phase5_query_text or query_text,
            result_limit=result_limit,
            filters=filters or Phase5FilterIntent(),
            reason_codes=("phase5_wrapper_test",),
        ),
    )


def make_hybrid_row(*, chunk_id: int = 659, document_code: str = "TPL-008") -> dict:
    return {
        "chunk_id": chunk_id,
        "document_code": document_code,
        "document_title": "Site Visit Checklist",
        "document_version_id": 81,
        "document_version_number": 3,
        "chunk_set_id": 41,
        "chunk_ordinal": 2,
        "section_heading": "2. Site visit - if applicable",
        "heading_path": "Site visit > Scheduling",
        "question_label": None,
        "body_text": "Offer a site visit when layout, access, or logistics still need confirmation.",
        "content_hash": "abc123",
        "primary_chunk_source_id": 901,
        "primary_document_version_source_object_id": 902,
        "primary_source_locator": "docs/current/TPL-008.md#site-visit",
        "primary_category_code": "template",
        "authority_classification": "current_governed",
        "rental_type_codes": ["entire_venue"],
        "embedding_model_id": 13,
        "provider_code": "openai",
        "model_code": "text-embedding-3-small",
        "model_version": None,
        "came_from_fts": True,
        "came_from_semantic": True,
        "fts_rank": 1,
        "semantic_rank": 1,
        "fts_relevance_score": 0.88,
        "semantic_similarity_score": 0.92,
        "semantic_cosine_distance": 0.08,
        "rrf_k": 20,
        "rrf_fts_score": 0.5,
        "rrf_semantic_score": 0.5,
        "rrf_base_score": 1.0,
        "policy_modifier": 1.1,
        "final_score": 1.1,
    }


def make_fts_row(*, chunk_id: int = 579, document_code: str = "SERV-004") -> dict:
    return {
        "chunk_id": chunk_id,
        "document_code": document_code,
        "document_title": "Catering Requirements",
        "document_version_id": 55,
        "document_version_number": 2,
        "chunk_set_id": 22,
        "chunk_ordinal": 1,
        "section_heading": "External caterer requirements",
        "heading_path": "Requirements",
        "question_label": None,
        "body_text": "Collect menu, setup, and cleanup details from the external caterer before confirming logistics.",
        "content_hash": "fts123",
        "primary_chunk_source_id": 701,
        "primary_document_version_source_object_id": 702,
        "primary_source_locator": "docs/current/SERV-004.md#external-caterer-requirements",
        "primary_category_code": "service_policy",
        "authority_classification": "current_governed",
        "rental_type_codes": ["entire_venue"],
        "fts_rank": 1,
        "fts_relevance_score": 0.77,
    }


def make_metadata(
    *,
    chunk_id: int,
    confidentiality_level_code: str = CONFIDENTIALITY_LEVEL_COMMERCIALLY_SENSITIVE,
    pi_status: str = PERSONAL_INFORMATION_STATUS_YES,
) -> dict:
    return {
        "chunk_id": chunk_id,
        "document_version_id": 81,
        "document_code": "TPL-008",
        "primary_chunk_source_id": 901,
        "primary_document_version_source_object_id": 902,
        "primary_source_locator": "docs/current/TPL-008.md#site-visit",
        "chunk_source_count": 2,
        "confidentiality_level_code": confidentiality_level_code,
        "source_object_personal_information_status": pi_status,
        "source_codes": ["repo", "manual"],
        "source_locators": ["docs/current/TPL-008.md#site-visit", "ops/runbook#site-visits"],
        "source_traces": [
            {
                "chunk_source_id": 901,
                "document_version_source_object_id": 902,
                "source_object_id": 903,
                "source_registry_id": 904,
                "source_code": "repo",
                "source_locator": "docs/current/TPL-008.md#site-visit",
                "origin_type": "repository_file",
                "personal_information_status": pi_status,
                "is_primary_trace": True,
            }
        ],
        "primary_source_object_id": 903,
        "primary_source_registry_id": 904,
        "primary_source_code": "repo",
        "primary_repository_relative_path": "docs/current/TPL-008.md",
        "primary_manual_reference_key": None,
        "primary_external_uri": None,
        "primary_original_filename": "TPL-008.md",
    }


def make_relationships(chunk_id: int) -> dict[int, list[dict]]:
    return {
        chunk_id: [
            {
                "chunk_id": chunk_id,
                "relationship_scope": "chunk",
                "relationship_family": "logical_rule",
                "relationship_id": 1,
                "rule_code": "OPER_SITE_VISIT_CONFIRMATION",
                "rule_version_id": None,
                "relationship_type_code": "explains",
                "target_kind": "logical_rule",
                "notes": "Precise chunk-level explanation.",
            },
            {
                "chunk_id": chunk_id,
                "relationship_scope": "document_version",
                "relationship_family": "rule_version",
                "relationship_id": 2,
                "rule_code": "OPER_SETUP_START_AT_BOOKED_TIME",
                "rule_version_id": 3002,
                "relationship_type_code": "operational_context_for",
                "target_kind": "rule_version",
                "notes": "Broader document context.",
            },
        ]
    }


class Phase5WrapperTests(unittest.TestCase):
    def test_not_requested_behavior_skips_retrieval(self) -> None:
        plan = make_plan(required=False)
        calls: list[str] = []

        def unexpected_model_resolver(_query_runner):
            calls.append("model")
            raise AssertionError("model resolver should not be called")

        record = execute_phase5_plan(
            plan,
            embedding_model_resolver=unexpected_model_resolver,
        )

        self.assertFalse(record.requested)
        self.assertEqual(record.execution_state, EXECUTION_STATE_NOT_REQUESTED)
        self.assertEqual(record.result_count, 0)
        self.assertEqual(calls, [])

    def test_healthy_hybrid_normalizes_results_and_uses_runtime_limit_and_filters(self) -> None:
        filters = Phase5FilterIntent(document_code="TPL-008", category_code="template", rental_type_code="entire_venue")
        plan = make_plan(
            query_text="generic plan query",
            phase5_query_text="specific phase 5 query",
            result_limit=1,
            filters=filters,
        )
        runtime_config = Phase7RuntimeConfiguration(phase_5_result_limit=3)
        observed: dict[str, object] = {}

        def model_resolver(_query_runner):
            return {
                "id": 13,
                "provider_code": "openai",
                "model_code": "text-embedding-3-small",
                "model_version": None,
                "embedding_dimensions": 1536,
                "configuration_json": {
                    "distance_metric": "cosine",
                    "input_contract_code": "phase_05_chunk_embedding_input_v1",
                    "encoding_format": "float",
                    "api_base_url": "https://api.openai.com/v1",
                },
            }

        def coverage_resolver(model_id, _query_runner):
            self.assertEqual(model_id, 13)
            return {
                "eligible_chunks": 492,
                "embedded_chunks": 492,
                "missing_chunks": 0,
                "is_complete": True,
            }

        def embedder(client, query_text, config):
            observed["client"] = client
            observed["query_text"] = query_text
            observed["config"] = config
            return [0.1, 0.2, 0.3]

        def hybrid_runner(**kwargs):
            observed["hybrid_kwargs"] = kwargs
            return [make_hybrid_row()], 12.34

        def metadata_loader(rows, _query_runner):
            self.assertEqual(rows[0]["chunk_id"], 659)
            return {659: make_metadata(chunk_id=659, confidentiality_level_code=CONFIDENTIALITY_LEVEL_EXTERNALLY_SHAREABLE)}

        def relationship_loader(rows, _query_runner):
            self.assertEqual(rows[0]["document_code"], "TPL-008")
            return make_relationships(659)

        record = execute_phase5_plan(
            plan,
            runtime_configuration=runtime_config,
            query_runner=lambda _sql: [],
            embedding_model_resolver=model_resolver,
            embedding_coverage_resolver=coverage_resolver,
            embedding_client_factory=lambda: object(),
            query_embedder=embedder,
            hybrid_search_runner=hybrid_runner,
            metadata_loader=metadata_loader,
            relationship_loader=relationship_loader,
        )

        self.assertEqual(record.execution_state, EXECUTION_STATE_SUCCESS)
        self.assertEqual(record.result_count, 1)
        item = record.normalized_items[0]
        self.assertEqual(item.source_layer_role, SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE)
        self.assertEqual(item.authority_tier_code, AUTHORITY_TIER_CURRENT_GOVERNED)
        self.assertEqual(item.authority_priority, 2)
        self.assertEqual(item.execution_state, EXECUTION_STATE_SUCCESS)
        self.assertIsNone(item.reasoning_state)
        self.assertEqual(item.summary_text, make_hybrid_row()["body_text"])
        self.assertEqual(item.stable_identity.primary_code, "TPL-008")
        self.assertEqual(item.exact_identity.primary_id, 81)
        self.assertEqual(item.exact_identity.secondary_id, 659)
        self.assertEqual(item.retrieval.retrieval_mode_used, PHASE5_RETRIEVAL_MODE_USED_HYBRID)
        self.assertFalse(item.retrieval.fallback_used)
        self.assertEqual(item.retrieval.rank, 1)
        self.assertAlmostEqual(item.retrieval.score, 1.1)
        self.assertEqual(item.sensitivity.confidentiality_level, CONFIDENTIALITY_LEVEL_EXTERNALLY_SHAREABLE)
        self.assertEqual(item.sensitivity.personal_information_status, PERSONAL_INFORMATION_STATUS_YES)
        self.assertTrue(item.sensitivity.de_identification_required)
        self.assertEqual(item.provenance.source_codes, ("repo", "manual"))
        self.assertEqual(item.provenance.source_link_count, 2)
        self.assertEqual(item.layer_payload["authority_classification"], "current_governed")
        self.assertEqual(len(item.layer_payload["phase_4_rule_relationships"]), 2)
        self.assertEqual(observed["query_text"], "specific phase 5 query")
        self.assertIsInstance(observed["config"], EmbeddingModelConfig)
        self.assertEqual(
            observed["hybrid_kwargs"],
            {
                "query_text": "specific phase 5 query",
                "result_limit": 3,
                "candidate_pool_limit": 10,
                "query_embedding": [0.1, 0.2, 0.3],
                "embedding_model_id": 13,
                "document_code": "TPL-008",
                "category_code": "template",
                "rental_type_code": "entire_venue",
            },
        )

    def test_model_resolution_failure_uses_fts_fallback(self) -> None:
        plan = make_plan()

        def model_resolver(_query_runner):
            raise Phase5PreflightError(
                reason_code=FALLBACK_REASON_EMBEDDING_MODEL_RESOLUTION_FAILED,
                safe_message="No active retrieval-approved model.",
            )

        record = execute_phase5_plan(
            plan,
            query_runner=lambda _sql: [],
            embedding_model_resolver=model_resolver,
            fts_search_runner=lambda **_kwargs: ([make_fts_row()], 4.5),
            metadata_loader=lambda rows, _query_runner: {rows[0]["chunk_id"]: make_metadata(chunk_id=rows[0]["chunk_id"])},
            relationship_loader=lambda rows, _query_runner: make_relationships(rows[0]["chunk_id"]),
        )

        self.assertEqual(record.execution_state, EXECUTION_STATE_FALLBACK)
        self.assertEqual(record.fallback_reason, FALLBACK_REASON_EMBEDDING_MODEL_RESOLUTION_FAILED)
        self.assertEqual(record.result_count, 1)
        item = record.normalized_items[0]
        self.assertEqual(item.execution_state, EXECUTION_STATE_FALLBACK)
        self.assertEqual(item.retrieval.retrieval_mode_used, PHASE5_RETRIEVAL_MODE_USED_FTS_FALLBACK)
        self.assertTrue(item.retrieval.fallback_used)
        self.assertEqual(item.retrieval.fallback_reason, FALLBACK_REASON_EMBEDDING_MODEL_RESOLUTION_FAILED)
        self.assertAlmostEqual(item.retrieval.score, 0.77)
        self.assertIsNone(item.retrieval.native_retrieval_payload["semantic_rank"])

    def test_query_embedding_failure_uses_fts_fallback(self) -> None:
        plan = make_plan()

        def model_resolver(_query_runner):
            return {
                "id": 13,
                "provider_code": "openai",
                "model_code": "text-embedding-3-small",
                "model_version": None,
                "embedding_dimensions": 1536,
                "configuration_json": {},
            }

        def coverage_resolver(_model_id, _query_runner):
            return {
                "eligible_chunks": 492,
                "embedded_chunks": 492,
                "missing_chunks": 0,
                "is_complete": True,
            }

        def bad_embedder(_client, _query_text, _config):
            raise RuntimeError("boom")

        record = execute_phase5_plan(
            plan,
            query_runner=lambda _sql: [],
            embedding_model_resolver=model_resolver,
            embedding_coverage_resolver=coverage_resolver,
            embedding_client_factory=lambda: object(),
            query_embedder=bad_embedder,
            fts_search_runner=lambda **_kwargs: ([make_fts_row()], 6.0),
            metadata_loader=lambda rows, _query_runner: {rows[0]["chunk_id"]: make_metadata(chunk_id=rows[0]["chunk_id"])},
            relationship_loader=lambda rows, _query_runner: make_relationships(rows[0]["chunk_id"]),
        )

        self.assertEqual(record.execution_state, EXECUTION_STATE_FALLBACK)
        self.assertEqual(record.fallback_reason, FALLBACK_REASON_QUERY_EMBEDDING_FAILED)

    def test_no_results_is_distinct_from_failure(self) -> None:
        plan = make_plan()

        record = execute_phase5_plan(
            plan,
            query_runner=lambda _sql: [],
            embedding_model_resolver=lambda _query_runner: {
                "id": 13,
                "provider_code": "openai",
                "model_code": "text-embedding-3-small",
                "model_version": None,
                "embedding_dimensions": 1536,
                "configuration_json": {},
            },
            embedding_coverage_resolver=lambda _model_id, _query_runner: {
                "eligible_chunks": 492,
                "embedded_chunks": 492,
                "missing_chunks": 0,
                "is_complete": True,
            },
            embedding_client_factory=lambda: object(),
            query_embedder=lambda _client, _query_text, _config: [0.1],
            hybrid_search_runner=lambda **_kwargs: ([], 3.0),
        )

        self.assertEqual(record.execution_state, EXECUTION_STATE_NO_RESULTS)
        self.assertEqual(record.result_count, 0)
        self.assertEqual(record.normalized_items, ())

    def test_total_failure_can_surface_unavailable(self) -> None:
        plan = make_plan()

        def model_resolver(_query_runner):
            raise Phase5PreflightError(
                reason_code=FALLBACK_REASON_EMBEDDING_MODEL_RESOLUTION_FAILED,
                safe_message="No model",
            )

        def unavailable_fts(**_kwargs):
            raise Phase5ExecutionError(
                execution_state=EXECUTION_STATE_UNAVAILABLE,
                error_category="phase5_fts_unavailable",
                safe_message="Lexical fallback is unavailable.",
            )

        record = execute_phase5_plan(
            plan,
            query_runner=lambda _sql: [],
            embedding_model_resolver=model_resolver,
            fts_search_runner=unavailable_fts,
        )

        self.assertEqual(record.execution_state, EXECUTION_STATE_UNAVAILABLE)
        self.assertEqual(record.result_count, 0)
        self.assertEqual(record.fallback_reason, FALLBACK_REASON_EMBEDDING_MODEL_RESOLUTION_FAILED)

    def test_metadata_enrichment_failure_applies_conservative_restricted_defaults(self) -> None:
        plan = make_plan()

        record = execute_phase5_plan(
            plan,
            query_runner=lambda _sql: [],
            embedding_model_resolver=lambda _query_runner: {
                "id": 13,
                "provider_code": "openai",
                "model_code": "text-embedding-3-small",
                "model_version": None,
                "embedding_dimensions": 1536,
                "configuration_json": {},
            },
            embedding_coverage_resolver=lambda _model_id, _query_runner: {
                "eligible_chunks": 492,
                "embedded_chunks": 492,
                "missing_chunks": 0,
                "is_complete": True,
            },
            embedding_client_factory=lambda: object(),
            query_embedder=lambda _client, _query_text, _config: [0.1],
            hybrid_search_runner=lambda **_kwargs: ([make_hybrid_row()], 2.0),
            metadata_loader=lambda _rows, _query_runner: (_ for _ in ()).throw(RuntimeError("metadata failed")),
            relationship_loader=lambda rows, _query_runner: make_relationships(rows[0]["chunk_id"]),
        )

        self.assertEqual(record.execution_state, EXECUTION_STATE_SUCCESS)
        self.assertEqual(record.error_category, "phase5_sensitivity_enrichment_failed")
        item = record.normalized_items[0]
        self.assertEqual(item.sensitivity.confidentiality_level, CONFIDENTIALITY_LEVEL_RESTRICTED)
        self.assertEqual(item.sensitivity.personal_information_status, PERSONAL_INFORMATION_STATUS_UNKNOWN)
        self.assertEqual(
            item.sensitivity.native_sensitivity_payload["warning"],
            "conservative_restricted_default_applied",
        )

    def test_json_serialization_preserves_wrapper_payload(self) -> None:
        plan = make_plan()

        record = execute_phase5_plan(
            plan,
            query_runner=lambda _sql: [],
            embedding_model_resolver=lambda _query_runner: {
                "id": 13,
                "provider_code": "openai",
                "model_code": "text-embedding-3-small",
                "model_version": None,
                "embedding_dimensions": 1536,
                "configuration_json": {},
            },
            embedding_coverage_resolver=lambda _model_id, _query_runner: {
                "eligible_chunks": 492,
                "embedded_chunks": 492,
                "missing_chunks": 0,
                "is_complete": True,
            },
            embedding_client_factory=lambda: object(),
            query_embedder=lambda _client, _query_text, _config: [0.1],
            hybrid_search_runner=lambda **_kwargs: ([make_hybrid_row()], 5.0),
            metadata_loader=lambda rows, _query_runner: {rows[0]["chunk_id"]: make_metadata(chunk_id=rows[0]["chunk_id"])},
            relationship_loader=lambda rows, _query_runner: make_relationships(rows[0]["chunk_id"]),
        )

        serialized = json.loads(record.to_json())
        self.assertEqual(serialized["layer_id"], LAYER_ID_PHASE_5)
        self.assertEqual(serialized["normalized_items"][0]["source_layer_role"], SOURCE_LAYER_ROLE_CURRENT_GOVERNED_KNOWLEDGE)
        self.assertIn("phase_4_rule_relationships", serialized["normalized_items"][0]["layer_payload"])

    def test_wrapper_configuration_can_force_optional_execution(self) -> None:
        plan = make_plan(required=False)

        forced_plan = QueryPlan(
            query_text=plan.query_text,
            query_class=plan.query_class,
            routing_confidence=plan.routing_confidence,
            required_layers=(),
            phase_5=Phase5RoutingIntent(
                required=False,
                needs_guidance=False,
                query_text=plan.query_text,
                result_limit=1,
                filters=Phase5FilterIntent(),
                reason_codes=("optional",),
            ),
        )

        record = execute_phase5_plan(
            forced_plan,
            wrapper_configuration=Phase5WrapperConfiguration(execute_when_optional=True),
            query_runner=lambda _sql: [],
            embedding_model_resolver=lambda _query_runner: {
                "id": 13,
                "provider_code": "openai",
                "model_code": "text-embedding-3-small",
                "model_version": None,
                "embedding_dimensions": 1536,
                "configuration_json": {},
            },
            embedding_coverage_resolver=lambda _model_id, _query_runner: {
                "eligible_chunks": 492,
                "embedded_chunks": 492,
                "missing_chunks": 0,
                "is_complete": True,
            },
            embedding_client_factory=lambda: object(),
            query_embedder=lambda _client, _query_text, _config: [0.1],
            hybrid_search_runner=lambda **_kwargs: ([make_hybrid_row()], 1.0),
            metadata_loader=lambda rows, _query_runner: {rows[0]["chunk_id"]: make_metadata(chunk_id=rows[0]["chunk_id"])},
            relationship_loader=lambda rows, _query_runner: make_relationships(rows[0]["chunk_id"]),
        )

        self.assertTrue(record.requested)
        self.assertEqual(record.execution_state, EXECUTION_STATE_SUCCESS)

    def test_wrapper_has_no_phase6_execution_dependency(self) -> None:
        source = inspect.getsource(execute_phase5_plan)
        self.assertNotIn("retrieve_historical_precedents", source)
        self.assertNotIn("phase_06_search", inspect.getsource(__import__("tools.phase_07_reasoning.phase5_wrapper", fromlist=["*"])))


if __name__ == "__main__":
    unittest.main()
