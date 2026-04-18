"""
ChromaDB vector store + BM25 sparse index → Reciprocal Rank Fusion hybrid search.

Hybrid strategy:
  1. Dense retrieval  — ChromaDB cosine similarity (BGE-large-en-v1.5)
  2. Sparse retrieval — BM25 (rank_bm25) on raw chunk tokens
  3. RRF fusion       — combines both ranked lists, k=60

Parent-context expansion:
  After RRF, each hit is expanded to its parent_text for richer generation context
  while the original child chunk is kept for citation scoring.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from pathlib import Path

from app.config import settings
from app.vectorstore.embeddings import get_embedding_generator

try:
    from rank_bm25 import BM25Okapi
    _BM25_AVAILABLE = True
except ImportError:
    _BM25_AVAILABLE = False


# ── Reciprocal Rank Fusion ─────────────────────────────────────────────────────

def _rrf(rankings: List[List[str]], k: int = 60) -> Dict[str, float]:
    """
    Standard RRF: score(d) = Σ  1 / (k + rank(d))
    Returns dict of doc_id → fused score (higher is better).
    """
    scores: Dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] += 1.0 / (k + rank + 1)
    return scores


# ── BM25 index ────────────────────────────────────────────────────────────────

class _BM25Index:
    """Lightweight in-process BM25 index rebuilt whenever new docs are added."""

    def __init__(self):
        self._ids:    List[str]       = []
        self._texts:  List[List[str]] = []   # tokenised
        self._model:  Optional[BM25Okapi] = None
        self._dirty = True

    def add(self, doc_id: str, text: str) -> None:
        self._ids.append(doc_id)
        self._texts.append(text.lower().split())
        self._dirty = True

    def _rebuild(self) -> None:
        if self._texts and _BM25_AVAILABLE:
            self._model = BM25Okapi(self._texts)
        self._dirty = False

    def query(self, query: str, top_k: int) -> List[str]:
        if not self._ids or not _BM25_AVAILABLE:
            return []
        if self._dirty:
            self._rebuild()
        if self._model is None:
            return []
        tokens = query.lower().split()
        scores = self._model.get_scores(tokens)
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [self._ids[i] for i in ranked[:top_k]]

    def rebuild_from(self, ids: List[str], texts: List[str]) -> None:
        self._ids = list(ids)
        self._texts = [t.lower().split() for t in texts]
        self._dirty = True


# ── VectorStore ────────────────────────────────────────────────────────────────

class VectorStore:
    """
    ChromaDB + BM25 hybrid vector store with RRF fusion and parent expansion.
    """

    def __init__(
        self,
        persist_directory: Path = None,
        collection_name: str = None,
    ):
        self.persist_directory = persist_directory or settings.chroma_persist_dir
        self.collection_name   = collection_name   or settings.collection_name
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
        )
        self.embedding_generator = get_embedding_generator()
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        self._bm25 = _BM25Index()
        self._bm25_synced = False

    # ── Write ─────────────────────────────────────────────────────────────────

    def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        if not documents:
            return []

        texts     = [d["text"]     for d in documents]
        metadatas = [d["metadata"] for d in documents]

        # Sanitise metadata values — ChromaDB rejects None
        clean_metas = []
        for meta in metadatas:
            clean: Dict[str, Any] = {}
            for k, v in meta.items():
                if v is None:
                    clean[k] = ""
                elif isinstance(v, (str, int, float, bool)):
                    clean[k] = v
                else:
                    clean[k] = str(v)
            clean_metas.append(clean)

        embeddings = self.embedding_generator.embed_texts(texts)
        ids = [m.get("chunk_id", f"doc_{i}") for i, m in enumerate(clean_metas)]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=clean_metas,
        )

        # Update BM25 index
        for doc_id, text in zip(ids, texts):
            self._bm25.add(doc_id, text)

        return ids

    # ── Read ──────────────────────────────────────────────────────────────────

    def query(
        self,
        query_text: str,
        top_k: int = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
        use_hybrid: bool = True,
    ) -> Dict[str, Any]:
        """
        Hybrid dense + sparse search with RRF.
        Falls back to dense-only if BM25 unavailable.
        """
        top_k = top_k or settings.top_k_retrieval
        fetch_k = min(top_k * 4, max(20, top_k * 4))  # over-fetch for fusion

        # ── Dense retrieval ──────────────────────────────────────────────────
        q_emb = self.embedding_generator.embed_query(query_text)
        dense_res = self.collection.query(
            query_embeddings=[q_emb],
            n_results=fetch_k,
            where=filter_metadata,
            include=["documents", "metadatas", "distances"],
        )
        dense_ids    = dense_res["ids"][0]     if dense_res["ids"]     else []
        dense_docs   = dense_res["documents"][0] if dense_res["documents"] else []
        dense_metas  = dense_res["metadatas"][0] if dense_res["metadatas"] else []
        dense_dists  = dense_res["distances"][0]  if dense_res["distances"]  else []

        # Build id → record map
        record_map: Dict[str, Dict[str, Any]] = {}
        for doc_id, doc, meta, dist in zip(dense_ids, dense_docs, dense_metas, dense_dists):
            score = self._dist_to_score(dist)
            record_map[doc_id] = {"text": doc, "metadata": meta, "score": score, "id": doc_id}

        if not use_hybrid or not _BM25_AVAILABLE:
            # Dense-only — score already calibrated
            ranked = sorted(record_map.values(), key=lambda x: x["score"], reverse=True)
            return self._unpack(ranked[:top_k])

        # ── Sparse retrieval (BM25) ──────────────────────────────────────────
        self._ensure_bm25_synced()
        sparse_ids = self._bm25.query(query_text, fetch_k)

        # Fetch any BM25 hits not already in record_map
        missing_ids = [i for i in sparse_ids if i not in record_map]
        if missing_ids:
            extra = self.collection.get(
                ids=missing_ids,
                include=["documents", "metadatas"],
            )
            for doc_id, doc, meta in zip(
                extra["ids"], extra["documents"], extra["metadatas"]
            ):
                record_map[doc_id] = {
                    "text": doc, "metadata": meta,
                    "score": 0.3,  # BM25-only hit baseline score
                    "id": doc_id,
                }

        # ── RRF fusion ───────────────────────────────────────────────────────
        fused = _rrf([dense_ids, sparse_ids])
        ranked = sorted(
            record_map.values(),
            key=lambda r: fused.get(r["id"], 0.0),
            reverse=True,
        )[:top_k]

        # Replace score with fused score (normalised 0-1)
        max_fused = max((fused.get(r["id"], 0) for r in ranked), default=1.0)
        for r in ranked:
            r["score"] = round(fused.get(r["id"], 0) / max(max_fused, 1e-9), 4)

        return self._unpack(ranked)

    # ── Parent context expansion ───────────────────────────────────────────────

    def expand_to_parents(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Replace doc text with parent_text where available.
        Keeps original child text in metadata["child_text"] for citations.
        """
        expanded = []
        for doc in docs:
            parent_text = doc["metadata"].get("parent_text")
            if parent_text and parent_text != doc["text"]:
                doc = dict(doc)
                doc["metadata"] = dict(doc["metadata"])
                doc["metadata"]["child_text"] = doc["text"]
                doc["text"] = parent_text
            expanded.append(doc)
        return expanded

    # ── Utility ───────────────────────────────────────────────────────────────

    def get_document_count(self) -> int:
        return self.collection.count()

    def delete_by_metadata(self, key: str, value: Any) -> bool:
        try:
            self.collection.delete(where={key: value})
            return True
        except Exception:
            return False

    def reset_collection(self) -> None:
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self._bm25 = _BM25Index()

    # ── Internals ─────────────────────────────────────────────────────────────

    def _ensure_bm25_synced(self) -> None:
        if self._bm25_synced:
            return
        try:
            result = self.collection.get(include=["documents"])
            if result["ids"]:
                self._bm25.rebuild_from(result["ids"], result["documents"])
        except Exception:
            pass
        self._bm25_synced = True

    @staticmethod
    def _dist_to_score(distance: float) -> float:
        """Convert ChromaDB cosine distance [0,2] → similarity score [0,1]."""
        raw = math.exp(-(distance ** 2) / 4.0) ** 0.2
        if raw > 0.70:
            raw = 0.70 + (raw - 0.70) * 4.0
        elif raw > 0.50:
            raw = 0.50 + (raw - 0.50) * 2.5
        elif raw > 0.30:
            raw = 0.30 + (raw - 0.30) * 2.0
        return round(min(0.99, max(0.01, raw)), 4)

    @staticmethod
    def _unpack(docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "documents": [d["text"]     for d in docs],
            "metadatas": [d["metadata"] for d in docs],
            "distances": [1.0 - d["score"] for d in docs],
            "ids":       [d["id"]       for d in docs],
        }


# ── Singleton ─────────────────────────────────────────────────────────────────

_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
