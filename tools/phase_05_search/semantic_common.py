from __future__ import annotations

import hashlib
import json
import os
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol, Sequence, TypeVar

import certifi


DEFAULT_PROVIDER_CODE = "openai"
DEFAULT_MODEL_CODE = "text-embedding-3-small"
DEFAULT_MODEL_VERSION: str | None = None
DEFAULT_EMBEDDING_DIMENSIONS = 1536
DEFAULT_DISTANCE_METRIC = "cosine"
DEFAULT_INPUT_CONTRACT_CODE = "phase_05_chunk_embedding_input_v1"
DEFAULT_ENCODING_FORMAT = "float"
DEFAULT_API_BASE_URL = "https://api.openai.com/v1"
DEFAULT_BATCH_SIZE = 32
T = TypeVar("T")


@dataclass(frozen=True)
class EmbeddingModelConfig:
    provider_code: str = DEFAULT_PROVIDER_CODE
    model_code: str = DEFAULT_MODEL_CODE
    model_version: str | None = DEFAULT_MODEL_VERSION
    embedding_dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS
    distance_metric: str = DEFAULT_DISTANCE_METRIC
    input_contract_code: str = DEFAULT_INPUT_CONTRACT_CODE
    encoding_format: str = DEFAULT_ENCODING_FORMAT
    api_base_url: str = DEFAULT_API_BASE_URL
    is_retrieval_approved: bool = True
    is_active: bool = True


@dataclass(frozen=True)
class ChunkEmbeddingCandidate:
    chunk_id: int
    document_code: str
    chunk_ordinal: int
    embedding_input_text: str
    embedding_input_hash: str


@dataclass(frozen=True)
class SearchFixture:
    query: str
    expected_codes: tuple[str, ...]
    discouraged_codes: tuple[str, ...] = ()
    note: str = ""


@dataclass(frozen=True)
class SearchAssessment:
    status: str
    explanation: str


class EmbeddingClient(Protocol):
    def embed_texts(self, texts: Sequence[str], config: EmbeddingModelConfig) -> list[list[float]]:
        ...


class EmbeddingGenerationError(RuntimeError):
    def __init__(
        self,
        *,
        model_code: str,
        chunk_descriptors: Sequence[str],
        input_hashes: Sequence[str],
        reason: str,
    ) -> None:
        self.model_code = model_code
        self.chunk_descriptors = tuple(chunk_descriptors)
        self.input_hashes = tuple(input_hashes)
        self.reason = reason
        super().__init__(
            f"Embedding generation failed for model {model_code} on "
            f"{', '.join(self.chunk_descriptors)} ({reason})"
        )


def load_env_value(name: str) -> str | None:
    direct_value = os.environ.get(name)
    if direct_value is not None:
        trimmed = direct_value.strip()
        return trimmed or None

    candidate_dirs: list[Path] = []
    for root in (Path.cwd(), *Path.cwd().parents, Path(__file__).resolve().parent):
        if root not in candidate_dirs:
            candidate_dirs.append(root)

    for directory in candidate_dirs:
        for filename in (".env.local", ".env"):
            candidate_path = directory / filename
            if not candidate_path.is_file():
                continue

            for raw_line in candidate_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                if line.startswith("export "):
                    line = line[len("export ") :].lstrip()

                key, value = line.split("=", 1)
                if key.strip() != name:
                    continue

                normalized = value.strip()
                if not normalized:
                    return None
                if normalized[0] == normalized[-1] and normalized[0] in {"'", '"'} and len(normalized) >= 2:
                    normalized = normalized[1:-1]
                return normalized or None

    return None


class OpenAIEmbeddingsClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        timeout_seconds: int = 60,
    ) -> None:
        raw_api_key = api_key or load_env_value("OPENAI_API_KEY")
        if raw_api_key is None:
            self.api_key = None
        else:
            # API keys never contain whitespace. If a pasted shell command accidentally
            # appends a newline plus more text, keep only the first token.
            self.api_key = raw_api_key.strip().split()[0] if raw_api_key.strip() else None
        if not self.api_key:
            raise SystemExit(
                "OPENAI_API_KEY is required for live embedding generation and semantic evaluation."
            )
        self.timeout_seconds = timeout_seconds
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())

    def embed_texts(self, texts: Sequence[str], config: EmbeddingModelConfig) -> list[list[float]]:
        if not texts:
            return []

        payload = {
            "model": config.model_code,
            "input": list(texts),
            "encoding_format": config.encoding_format,
            "dimensions": config.embedding_dimensions,
        }
        request = urllib.request.Request(
            url=f"{config.api_base_url.rstrip('/')}/embeddings",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds, context=self.ssl_context) as response:
                parsed = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code == 401:
                raise RuntimeError(
                    "HTTP 401: OpenAI rejected the supplied API key. "
                    "Verify OPENAI_API_KEY in the current shell and make sure it is a real active key."
                ) from exc
            if exc.code == 429 and "credit_balance_exhausted" in body:
                raise RuntimeError(
                    "HTTP 429: OpenAI reported insufficient quota for this API key or organization. "
                    "Add credits or use a key tied to an organization with available billing, then rerun embedding generation."
                ) from exc
            raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
        except ssl.SSLError as exc:
            raise RuntimeError(
                f"SSL verification failed while calling the embedding API: {exc}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(str(exc.reason)) from exc

        rows = parsed.get("data", [])
        ordered: list[list[float] | None] = [None] * len(rows)
        for row in rows:
            ordered[row["index"]] = row["embedding"]

        if len(ordered) != len(texts) or any(item is None for item in ordered):
            raise RuntimeError("Embedding API response did not include one embedding per input in stable order.")

        return [item for item in ordered if item is not None]


def normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def build_embedding_input(
    document_title: str,
    heading_path: str | None,
    section_heading: str | None,
    question_label: str | None,
    body_text: str,
) -> str:
    parts = [f"Document: {document_title}"]
    section_value = normalize_optional_text(heading_path) or normalize_optional_text(section_heading)
    if section_value is not None:
        parts.append(f"Section: {section_value}")
    question_value = normalize_optional_text(question_label)
    if question_value is not None:
        parts.append(f"Question: {question_value}")
    parts.append(body_text)
    return "\n\n".join(parts)


def compute_content_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def build_model_configuration_json(config: EmbeddingModelConfig) -> dict[str, object]:
    return {
        "provider_code": config.provider_code,
        "model_code": config.model_code,
        "model_version": config.model_version,
        "embedding_dimensions": config.embedding_dimensions,
        "distance_metric": config.distance_metric,
        "input_contract_code": config.input_contract_code,
        "encoding_format": config.encoding_format,
        "api_base_url": config.api_base_url,
    }


def compute_config_fingerprint(config: EmbeddingModelConfig) -> str:
    canonical = json.dumps(
        build_model_configuration_json(config),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.md5(canonical.encode("utf-8")).hexdigest()


def validate_embedding_dimensions(vector: Sequence[float], expected_dimensions: int) -> None:
    if len(vector) != expected_dimensions:
        raise ValueError(
            f"Embedding dimensions {len(vector)} do not match expected dimensions {expected_dimensions}."
        )


def batch_items(items: Sequence[T], batch_size: int) -> Iterable[Sequence[T]]:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


def plan_pending_chunk_embeddings(
    candidates: Sequence[ChunkEmbeddingCandidate],
    existing_pairs: set[tuple[int, str]],
) -> tuple[list[ChunkEmbeddingCandidate], list[ChunkEmbeddingCandidate]]:
    pending: list[ChunkEmbeddingCandidate] = []
    skipped: list[ChunkEmbeddingCandidate] = []
    for candidate in candidates:
        key = (candidate.chunk_id, candidate.embedding_input_hash)
        if key in existing_pairs:
            skipped.append(candidate)
        else:
            pending.append(candidate)
    return pending, skipped


def vector_sql_literal(values: Sequence[float]) -> str:
    return "'[" + ",".join(format(value, ".15g") for value in values) + "]'"


def embed_query_text(
    client: EmbeddingClient,
    query_text: str,
    config: EmbeddingModelConfig,
) -> list[float]:
    rows = client.embed_texts([query_text], config)
    if len(rows) != 1:
        raise RuntimeError("Expected exactly one query embedding.")
    validate_embedding_dimensions(rows[0], config.embedding_dimensions)
    return rows[0]


def embed_candidate_batch(
    client: EmbeddingClient,
    candidates: Sequence[ChunkEmbeddingCandidate],
    config: EmbeddingModelConfig,
) -> list[list[float]]:
    try:
        rows = client.embed_texts([candidate.embedding_input_text for candidate in candidates], config)
    except Exception as exc:  # pragma: no cover - exercised via unit tests with a fake client
        raise EmbeddingGenerationError(
            model_code=config.model_code,
            chunk_descriptors=[f"{candidate.document_code}#{candidate.chunk_ordinal}" for candidate in candidates],
            input_hashes=[candidate.embedding_input_hash for candidate in candidates],
            reason=str(exc),
        ) from exc

    for row in rows:
        validate_embedding_dimensions(row, config.embedding_dimensions)
    return rows


def assess_search_results(fixture: SearchFixture, rows: Sequence[dict]) -> SearchAssessment:
    if not rows:
        return SearchAssessment("miss", "No ranked results were returned.")

    top_code = rows[0]["document_code"]
    top_three_codes = [row["document_code"] for row in rows[:3]]
    all_codes = [row["document_code"] for row in rows]

    if top_code in fixture.discouraged_codes:
        return SearchAssessment("weak", f"Top result {top_code} is explicitly discouraged for this query.")
    if top_code in fixture.expected_codes:
        return SearchAssessment("strong", f"Top result {top_code} is in the expected document family.")
    if any(code in fixture.expected_codes for code in top_three_codes):
        expected_hits = ", ".join(code for code in top_three_codes if code in fixture.expected_codes)
        return SearchAssessment("partial", f"Expected code(s) {expected_hits} appear in the top three, but not at rank one.")
    if any(code in fixture.expected_codes for code in all_codes):
        expected_hits = ", ".join(code for code in all_codes if code in fixture.expected_codes)
        return SearchAssessment("weak", f"Expected code(s) {expected_hits} appear lower in the result list.")
    return SearchAssessment("miss", "No expected document family appeared in the captured result window.")


def assessment_rank(status: str) -> int:
    return {"miss": 0, "weak": 1, "partial": 2, "strong": 3}[status]
