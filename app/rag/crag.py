"""
Corrective RAG (CRAG) — scores each retrieved document for relevance and
decides whether to use it, discard it, or fall back to web search.

Decision logic:
  score >= HIGH_THRESHOLD  → CORRECT   (use as-is)
  score >= LOW_THRESHOLD   → AMBIGUOUS (use with lower weight)
  score <  LOW_THRESHOLD   → INCORRECT (discard)

If fewer than min_correct docs survive → trigger web fallback.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Tuple

from openai import OpenAI
from app.config import settings
from app.rag.prompts import CRAG_RELEVANCE_PROMPT

logger = logging.getLogger(__name__)

HIGH_THRESHOLD = 0.7
LOW_THRESHOLD  = 0.4


class CRAGFilter:
    """
    Relevance-based document filter.

    Usage:
        filt = CRAGFilter()
        filtered, needs_web = filt.filter(query, docs)
    """

    def __init__(self, model: str | None = None):
        self._model  = model or settings.helper_model
        self._client = OpenAI(api_key=settings.openai_api_key)

    def filter(
        self,
        query: str,
        docs: List[Dict[str, Any]],
        min_correct: int = 2,
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Score and filter docs.

        Returns:
            (filtered_docs, needs_web_fallback)
        """
        scored = [(doc, self._score(query, doc["text"][:600])) for doc in docs]
        scored.sort(key=lambda x: x[1], reverse=True)

        correct:   List[Dict[str, Any]] = []
        ambiguous: List[Dict[str, Any]] = []

        for doc, score in scored:
            doc = dict(doc)
            doc["crag_score"] = round(score, 3)
            if score >= HIGH_THRESHOLD:
                correct.append(doc)
            elif score >= LOW_THRESHOLD:
                ambiguous.append(doc)
            # below LOW_THRESHOLD → dropped

        # If not enough high-quality docs, pad with ambiguous ones
        result = correct + ambiguous
        needs_web = len(correct) < min_correct

        if not result:
            # Nothing passed — return originals rather than empty
            result = [dict(d) for d in docs]
            needs_web = True

        return result, needs_web

    def _score(self, query: str, passage: str) -> float:
        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "user",
                        "content": CRAG_RELEVANCE_PROMPT.format(
                            query=query, passage=passage
                        ),
                    }
                ],
                max_tokens=8,
                temperature=0.0,
            )
            raw = (resp.choices[0].message.content or "0").strip()
            return float(raw.split()[0])
        except Exception:
            return 0.5  # neutral on failure
