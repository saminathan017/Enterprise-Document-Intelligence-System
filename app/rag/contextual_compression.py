"""
Contextual compression — strip each retrieved chunk down to only the sentences
that are relevant to the query, cutting noise before it reaches the LLM.

Uses a fast GPT-4o-mini call per chunk (cheap, ~200 tokens each).
Chunks that score as IRRELEVANT are dropped entirely.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any

from openai import OpenAI
from app.config import settings
from app.rag.prompts import COMPRESSION_PROMPT

logger = logging.getLogger(__name__)

_MAX_PASSAGE_CHARS = 1800  # keep API calls cheap


class ContextualCompressor:
    """
    LLM-powered per-chunk compression.

    Usage:
        compressor = ContextualCompressor()
        compressed_docs = compressor.compress(query, retrieved_docs)
    """

    def __init__(self, model: str | None = None):
        self._model = model or settings.helper_model
        self._client = OpenAI(api_key=settings.openai_api_key)

    def compress(
        self,
        query: str,
        docs: List[Dict[str, Any]],
        min_keep: int = 2,
    ) -> List[Dict[str, Any]]:
        """
        Compress each doc to its relevant excerpt.

        Args:
            query:    User question
            docs:     Retrieved document dicts (text, metadata, score, id)
            min_keep: Always keep at least this many docs (even if low quality)

        Returns:
            Filtered + compressed list, preserving original metadata/scores.
        """
        compressed: List[Dict[str, Any]] = []

        for doc in docs:
            passage = doc["text"][:_MAX_PASSAGE_CHARS]
            excerpt = self._extract_relevant(query, passage)

            if excerpt.strip().upper() == "IRRELEVANT":
                logger.debug("Compression dropped chunk %s", doc.get("id", "?"))
                continue

            updated = dict(doc)
            updated["metadata"] = dict(doc["metadata"])
            updated["metadata"]["original_text"] = doc["text"]
            updated["text"] = excerpt.strip()
            compressed.append(updated)

        # Safety: always return at least min_keep docs
        if len(compressed) < min_keep and docs:
            existing_ids = {d.get("id") for d in compressed}
            for doc in docs:
                if doc.get("id") not in existing_ids:
                    compressed.append(doc)
                if len(compressed) >= min_keep:
                    break

        return compressed

    def _extract_relevant(self, query: str, passage: str) -> str:
        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "user",
                        "content": COMPRESSION_PROMPT.format(
                            query=query, passage=passage
                        ),
                    }
                ],
                max_tokens=600,
                temperature=0.0,
            )
            return resp.choices[0].message.content or passage
        except Exception as exc:
            logger.warning("Compression failed for chunk: %s", exc)
            return passage  # fall back to full passage
