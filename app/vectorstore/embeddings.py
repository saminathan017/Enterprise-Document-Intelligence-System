"""
Embedding generation — BAAI/bge-large-en-v1.5 (1024-dim, SOTA retrieval)
with in-process LRU cache to eliminate redundant model calls.
"""

from __future__ import annotations

import hashlib
from collections import OrderedDict
from typing import List, Optional

from sentence_transformers import SentenceTransformer
from app.config import settings


# ── LRU embedding cache ──────────────────────────────────────────────────────

class _EmbeddingCache:
    """Thread-unsafe but fast in-process LRU cache for embeddings."""

    def __init__(self, max_size: int = 8192):
        self._store: OrderedDict[str, List[float]] = OrderedDict()
        self._max = max_size

    @staticmethod
    def _key(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:24]

    def get(self, text: str) -> Optional[List[float]]:
        k = self._key(text)
        if k in self._store:
            self._store.move_to_end(k)
            return self._store[k]
        return None

    def set(self, text: str, emb: List[float]) -> None:
        k = self._key(text)
        self._store[k] = emb
        self._store.move_to_end(k)
        if len(self._store) > self._max:
            self._store.popitem(last=False)

    @property
    def size(self) -> int:
        return len(self._store)


_cache = _EmbeddingCache()


# ── BGE query prefix detection ────────────────────────────────────────────────

_BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

def _is_bge(model_name: str) -> bool:
    return "bge" in model_name.lower()


# ── Embedding generator ───────────────────────────────────────────────────────

class EmbeddingGenerator:
    """
    Generates embeddings with BAAI/bge-large-en-v1.5 (default).

    Key improvements vs old all-MiniLM-L6-v2:
    - 1024 dimensions (vs 384) → richer semantic space
    - BGE-specific query prefix for asymmetric retrieval
    - In-process LRU cache — repeated queries never hit the model
    """

    def __init__(self, model_name: str = None, device: str = None):
        self.model_name = model_name or settings.embedding_model
        self.device = device or settings.embedding_device
        self.model = SentenceTransformer(self.model_name, device=self.device)
        self._is_bge = _is_bge(self.model_name)

    # ── Public API ────────────────────────────────────────────────────────────

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Batch-embed document texts (no query prefix)."""
        if not texts:
            return []

        results: List[Optional[List[float]]] = [None] * len(texts)
        uncached_indices: List[int] = []
        uncached_texts: List[str] = []

        for i, t in enumerate(texts):
            cached = _cache.get(t)
            if cached is not None:
                results[i] = cached
            else:
                uncached_indices.append(i)
                uncached_texts.append(t)

        if uncached_texts:
            embeddings = self.model.encode(
                uncached_texts,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,
                batch_size=64,
            )
            for idx, emb in zip(uncached_indices, embeddings):
                vec = emb.tolist()
                _cache.set(texts[idx], vec)
                results[idx] = vec

        return results  # type: ignore[return-value]

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query, applying BGE prefix when applicable."""
        prefixed = f"{_BGE_QUERY_PREFIX}{query}" if self._is_bge else query
        cached = _cache.get(prefixed)
        if cached is not None:
            return cached

        emb = self.model.encode(
            prefixed,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        vec = emb.tolist()
        _cache.set(prefixed, vec)
        return vec

    def get_embedding_dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()

    @property
    def cache_size(self) -> int:
        return _cache.size


# ── Singleton ─────────────────────────────────────────────────────────────────

_embedding_generator: Optional[EmbeddingGenerator] = None


def get_embedding_generator() -> EmbeddingGenerator:
    global _embedding_generator
    if _embedding_generator is None:
        _embedding_generator = EmbeddingGenerator()
    return _embedding_generator
