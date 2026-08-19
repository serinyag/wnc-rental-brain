from __future__ import annotations

from dataclasses import dataclass


APPROVED_RRF_K = 20
DEFAULT_HYBRID_RESULT_LIMIT = 10
DEFAULT_HYBRID_CANDIDATE_POOL_LIMIT = 10
MAX_HYBRID_RESULT_LIMIT = 50
MAX_HYBRID_CANDIDATE_POOL_LIMIT = 50

CATEGORY_POLICY_MODIFIERS: dict[str, float] = {
    "operational_procedure": 0.011,
    "communication_guidance": 0.009,
    "service_supplier_guidance": 0.007,
    "technical_venue_reference": 0.007,
    "client_facing_controlled_document": 0.005,
    "proposal_guidance": 0.001,
    "governance_canonical": -0.010,
}


@dataclass(frozen=True)
class HybridCandidate:
    chunk_id: int
    document_code: str
    document_title: str
    document_version_id: int
    document_version_number: int
    chunk_set_id: int
    chunk_ordinal: int
    section_heading: str | None
    heading_path: str | None
    question_label: str | None
    body_text: str
    content_hash: str
    primary_chunk_source_id: int | None
    primary_document_version_source_object_id: int | None
    primary_source_locator: str | None
    primary_category_code: str
    authority_classification: str | None
    rental_type_codes: tuple[str, ...]
    fts_rank: int | None = None
    semantic_rank: int | None = None
    fts_relevance_score: float | None = None
    semantic_similarity_score: float | None = None
    semantic_cosine_distance: float | None = None


@dataclass(frozen=True)
class HybridRankedResult:
    chunk_id: int
    document_code: str
    chunk_ordinal: int
    came_from_fts: bool
    came_from_semantic: bool
    fts_rank: int | None
    semantic_rank: int | None
    rrf_fts_score: float
    rrf_semantic_score: float
    rrf_base_score: float
    policy_modifier: float
    final_score: float


def merge_candidate_rows(
    fts_candidates: list[HybridCandidate],
    semantic_candidates: list[HybridCandidate],
) -> list[HybridCandidate]:
    merged: dict[int, HybridCandidate] = {candidate.chunk_id: candidate for candidate in fts_candidates}
    for semantic_candidate in semantic_candidates:
        existing = merged.get(semantic_candidate.chunk_id)
        if existing is None:
            merged[semantic_candidate.chunk_id] = semantic_candidate
            continue
        merged[semantic_candidate.chunk_id] = HybridCandidate(
            chunk_id=existing.chunk_id,
            document_code=existing.document_code,
            document_title=existing.document_title,
            document_version_id=existing.document_version_id,
            document_version_number=existing.document_version_number,
            chunk_set_id=existing.chunk_set_id,
            chunk_ordinal=existing.chunk_ordinal,
            section_heading=existing.section_heading,
            heading_path=existing.heading_path,
            question_label=existing.question_label,
            body_text=existing.body_text,
            content_hash=existing.content_hash,
            primary_chunk_source_id=existing.primary_chunk_source_id,
            primary_document_version_source_object_id=existing.primary_document_version_source_object_id,
            primary_source_locator=existing.primary_source_locator,
            primary_category_code=existing.primary_category_code,
            authority_classification=existing.authority_classification,
            rental_type_codes=existing.rental_type_codes,
            fts_rank=existing.fts_rank,
            semantic_rank=semantic_candidate.semantic_rank,
            fts_relevance_score=existing.fts_relevance_score,
            semantic_similarity_score=semantic_candidate.semantic_similarity_score,
            semantic_cosine_distance=semantic_candidate.semantic_cosine_distance,
        )
    return list(merged.values())


def normalize_query_text(value: str | None) -> str | None:
    if value is None:
        return None
    compact = " ".join(value.split())
    return compact or None


def bound_result_limit(value: int | None) -> int:
    if value is None:
        return DEFAULT_HYBRID_RESULT_LIMIT
    return min(max(value, 1), MAX_HYBRID_RESULT_LIMIT)


def bound_candidate_pool_limit(candidate_pool_limit: int | None, result_limit: int) -> int:
    default_value = max(result_limit, DEFAULT_HYBRID_CANDIDATE_POOL_LIMIT)
    if candidate_pool_limit is None:
        return default_value
    return min(max(candidate_pool_limit, result_limit), MAX_HYBRID_CANDIDATE_POOL_LIMIT)


def compute_rrf_score(rank: int | None, rrf_k: int = APPROVED_RRF_K) -> float:
    if rank is None or rank <= 0 or rrf_k <= 0:
        return 0.0
    return 1.0 / float(rrf_k + rank)


def policy_modifier_for_category(category_code: str | None) -> float:
    if category_code is None:
        return 0.0
    return CATEGORY_POLICY_MODIFIERS.get(category_code, 0.0)


def merge_hybrid_candidates(
    candidates: list[HybridCandidate],
    *,
    result_limit: int,
    rrf_k: int = APPROVED_RRF_K,
) -> list[HybridRankedResult]:
    ranked: list[HybridRankedResult] = []
    for candidate in candidates:
        rrf_fts_score = compute_rrf_score(candidate.fts_rank, rrf_k)
        rrf_semantic_score = compute_rrf_score(candidate.semantic_rank, rrf_k)
        rrf_base_score = rrf_fts_score + rrf_semantic_score
        policy_modifier = policy_modifier_for_category(candidate.primary_category_code)
        ranked.append(
            HybridRankedResult(
                chunk_id=candidate.chunk_id,
                document_code=candidate.document_code,
                chunk_ordinal=candidate.chunk_ordinal,
                came_from_fts=candidate.fts_rank is not None,
                came_from_semantic=candidate.semantic_rank is not None,
                fts_rank=candidate.fts_rank,
                semantic_rank=candidate.semantic_rank,
                rrf_fts_score=rrf_fts_score,
                rrf_semantic_score=rrf_semantic_score,
                rrf_base_score=rrf_base_score,
                policy_modifier=policy_modifier,
                final_score=rrf_base_score + policy_modifier,
            )
        )

    return sorted(
        ranked,
        key=lambda item: (-item.final_score, item.document_code, item.chunk_ordinal),
    )[:result_limit]
