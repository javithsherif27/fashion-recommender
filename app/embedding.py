from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol

import numpy as np

from app import config
from app.text_utils import expand_query_text, tokenize


class Embedder(Protocol):
    backend: str
    model_name: str
    dimensions: int

    def encode(self, texts: list[str], *, is_query: bool = False) -> np.ndarray:
        ...


def _normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


@dataclass(slots=True)
class HashingEmbedder:
    dimensions: int = 768
    backend: str = "hashing"
    model_name: str = "local-fashion-hashing-v1"

    def encode(self, texts: list[str], *, is_query: bool = False) -> np.ndarray:
        matrix = np.zeros((len(texts), self.dimensions), dtype=np.float32)
        for row_index, original in enumerate(texts):
            text = expand_query_text(original) if is_query else original
            tokens = tokenize(text)
            features: list[tuple[str, float]] = [(token, 1.0) for token in tokens]
            features.extend(
                (f"{left}_{right}", 1.35)
                for left, right in zip(tokens, tokens[1:], strict=False)
            )
            for feature, weight in features:
                digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
                value = int.from_bytes(digest, "little")
                col = value % self.dimensions
                sign = 1.0 if ((value >> 9) & 1) else -1.0
                matrix[row_index, col] += sign * weight
        return _normalize(matrix)


class SentenceTransformerEmbedder:
    backend = "sentence-transformers"

    def __init__(self, model_name: str = config.LOCAL_EMBEDDING_MODEL) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self._model = SentenceTransformer(model_name)
        dimensions = self._model.get_sentence_embedding_dimension()
        self.dimensions = int(dimensions or 384)

    def encode(self, texts: list[str], *, is_query: bool = False) -> np.ndarray:
        prepared = [expand_query_text(text) if is_query else text for text in texts]
        vectors = self._model.encode(
            prepared,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype=np.float32)


def create_embedder(backend: str | None = None) -> Embedder:
    selected = (backend or config.EMBEDDING_BACKEND or "auto").lower()
    if selected in {"hash", "hashing", "local"}:
        return HashingEmbedder()
    if selected in {"sentence-transformers", "sentence_transformers", "semantic"}:
        return SentenceTransformerEmbedder()
    if selected != "auto":
        raise ValueError(f"Unsupported embedding backend: {selected}")
    try:
        return SentenceTransformerEmbedder()
    except Exception:
        return HashingEmbedder()

