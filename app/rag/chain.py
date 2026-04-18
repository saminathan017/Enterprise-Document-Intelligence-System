"""
RAG chain v2 — integrates:
  • Parent-context expansion   (child retrieval → parent generation window)
  • Lost-in-the-middle reorder (best docs at positions 0 and -1)
  • Contextual compression     (strip irrelevant sentences per chunk)
  • CRAG filtering             (drop low-relevance chunks)
  • Chain-of-thought prompt    (reasoning → answer → sources)
  • Cost tracking              (token counting per query)
  • Inline footnote citations  ([^1] … Sources block)
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.rag.prompts import (
    SYSTEM_PROMPT,
    RAG_PROMPT_TEMPLATE,
    WEB_AUGMENTED_PROMPT,
    TABLE_GENERATION_PROMPT,
)
from app.vectorstore.retrieval import Retriever
from app.models.responses import Citation

logger = logging.getLogger(__name__)


# ── Lost-in-the-middle reordering ────────────────────────────────────────────

def _reorder_lost_in_middle(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    LLMs attend most to beginning and end of context.
    Place highest-scoring docs at positions 0 and -1; weakest in the middle.
    """
    if len(docs) <= 2:
        return docs

    docs_sorted = sorted(docs, key=lambda d: d.get("score", 0), reverse=True)
    result: List[Dict[str, Any]] = [None] * len(docs_sorted)  # type: ignore

    left, right = 0, len(docs_sorted) - 1
    for i, doc in enumerate(docs_sorted):
        if i % 2 == 0:
            result[left] = doc
            left += 1
        else:
            result[right] = doc
            right -= 1

    return result


# ── Context formatter ─────────────────────────────────────────────────────────

def _format_context(docs: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for i, doc in enumerate(docs, 1):
        meta    = doc["metadata"]
        source  = meta.get("source", "Unknown")
        chunk   = meta.get("chunk_index", "?")
        score   = doc.get("score", 0)
        is_table = meta.get("is_table", False)
        label   = "TABLE" if is_table else f"chunk {chunk}"
        parts.append(
            f"[^{i}] **{source}** — {label} (relevance {score:.0%})\n\n"
            f"{doc['text']}\n"
        )
    return "\n---\n".join(parts)


# ── Citation extractor ────────────────────────────────────────────────────────

def _extract_citations(docs: List[Dict[str, Any]]) -> List[Citation]:
    citations: List[Citation] = []
    for doc in docs:
        meta    = doc["metadata"]
        # Use child_text for excerpt if parent was expanded
        raw_text = meta.get("child_text") or doc["text"]
        excerpt  = raw_text[:200] + "…" if len(raw_text) > 200 else raw_text
        citations.append(
            Citation(
                source   = meta.get("source", "Unknown"),
                chunk_id = meta.get("chunk_id"),
                score    = doc.get("score", 0),
                excerpt  = excerpt,
            )
        )
    return citations


# ── RAGChain ──────────────────────────────────────────────────────────────────

class RAGChain:
    """
    Full RAG chain with compression, CRAG, reordering, CoT prompting,
    and cost tracking.
    """

    def __init__(
        self,
        retriever: Retriever,
        use_compression: bool = False,
        use_crag: bool = False,
        expand_parents: bool = True,
    ):
        self.retriever       = retriever
        self.expand_parents  = expand_parents
        self._use_compression = use_compression
        self._use_crag        = use_crag

        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.max_tokens,
            openai_api_key=settings.openai_api_key,
        )

        # Lazy-loaded optional components
        self._compressor: Optional[Any] = None
        self._crag_filter: Optional[Any] = None

    # ── Public API ────────────────────────────────────────────────────────────

    def query(
        self,
        query: str,
        top_k: int = None,
        web_results: Optional[str] = None,
        use_table_format: bool = False,
        use_compression: Optional[bool] = None,
        use_crag: Optional[bool] = None,
    ) -> Dict[str, Any]:
        top_k = top_k or settings.top_k_retrieval

        # ── 1. Retrieve ───────────────────────────────────────────────────────
        docs = self.retriever.retrieve_with_scores(query, top_k)

        if not docs:
            return {"answer": "I cannot find any relevant documents to answer this question.", "citations": []}

        # ── 2. CRAG quality filter ────────────────────────────────────────────
        _crag = use_crag if use_crag is not None else self._use_crag
        if _crag:
            docs, _ = self._get_crag().filter(query, docs)

        # ── 3. Parent-context expansion ───────────────────────────────────────
        if self.expand_parents:
            from app.vectorstore.store import get_vector_store
            docs = get_vector_store().expand_to_parents(docs)

        # ── 4. Lost-in-the-middle reorder ─────────────────────────────────────
        docs = _reorder_lost_in_middle(docs)

        # ── 5. Contextual compression ─────────────────────────────────────────
        _compress = use_compression if use_compression is not None else self._use_compression
        if _compress:
            docs = self._get_compressor().compress(query, docs)

        # ── 6. Build prompt ───────────────────────────────────────────────────
        context = _format_context(docs)

        if use_table_format:
            user_prompt = TABLE_GENERATION_PROMPT.format(context=context, query=query)
        elif web_results:
            user_prompt = WEB_AUGMENTED_PROMPT.format(
                context=context, web_results=web_results, query=query
            )
        else:
            user_prompt = RAG_PROMPT_TEMPLATE.format(context=context, query=query)

        # ── 7. Generate ───────────────────────────────────────────────────────
        messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_prompt)]
        response = self.llm.invoke(messages)
        answer   = response.content.strip()

        # ── 8. Citations ──────────────────────────────────────────────────────
        citations = _extract_citations(docs)

        return {
            "answer":        answer,
            "citations":     citations,
            "retrieved_docs": docs,
        }

    # ── Lazy loaders ──────────────────────────────────────────────────────────

    def _get_compressor(self):
        if self._compressor is None:
            from app.rag.contextual_compression import ContextualCompressor
            self._compressor = ContextualCompressor()
        return self._compressor

    def _get_crag(self):
        if self._crag_filter is None:
            from app.rag.crag import CRAGFilter
            self._crag_filter = CRAGFilter()
        return self._crag_filter
