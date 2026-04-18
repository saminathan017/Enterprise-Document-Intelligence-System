"""
RAG Evaluation Framework v2 — production-grade metrics.

Replaces ROUGE/BLEU with:
  • BERTScore          — semantic F1 via contextual embeddings
  • NLI Faithfulness   — cross-encoder/nli-deberta-v3-base entailment check
  • Answer Relevancy   — cosine sim between question and answer embeddings
  • LLM-as-judge       — GPT-4o-mini scores faithfulness/relevancy/completeness
  • Classic retrieval  — Precision@K, Recall@K, MRR, NDCG@K (unchanged)
"""

from __future__ import annotations

import json
import logging
import numpy as np
from collections import defaultdict
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

# ── Optional heavy deps (graceful degradation) ────────────────────────────────

try:
    from bert_score import score as _bert_score
    _BERTSCORE = True
except ImportError:
    _BERTSCORE = False

try:
    from sentence_transformers import CrossEncoder
    _NLI_MODEL: Optional[CrossEncoder] = None
    _NLI_AVAILABLE = True
except ImportError:
    _NLI_AVAILABLE = False
    _NLI_MODEL = None

try:
    from sentence_transformers import SentenceTransformer
    _SIM_MODEL: Optional[SentenceTransformer] = None
    _SIM_AVAILABLE = True
except ImportError:
    _SIM_AVAILABLE = False
    _SIM_MODEL = None


def _get_nli_model() -> Optional[Any]:
    global _NLI_MODEL
    if not _NLI_AVAILABLE:
        return None
    if _NLI_MODEL is None:
        try:
            _NLI_MODEL = CrossEncoder("cross-encoder/nli-deberta-v3-base")
        except Exception as e:
            logger.warning("NLI model load failed: %s", e)
    return _NLI_MODEL


def _get_sim_model() -> Optional[Any]:
    global _SIM_MODEL
    if not _SIM_AVAILABLE:
        return None
    if _SIM_MODEL is None:
        try:
            _SIM_MODEL = SentenceTransformer("BAAI/bge-large-en-v1.5")
        except Exception as e:
            logger.warning("Similarity model load failed: %s", e)
    return _SIM_MODEL


# ── RAGEvaluator ──────────────────────────────────────────────────────────────

class RAGEvaluator:
    """Comprehensive RAG evaluation with semantic and LLM-based metrics."""

    def __init__(self):
        self.results: Dict[str, List] = defaultdict(list)

    # ── Retrieval metrics (unchanged, well-implemented) ───────────────────────

    def precision_at_k(self, retrieved: List[str], relevant: List[str], k: int = 5) -> float:
        if not retrieved or k == 0:
            return 0.0
        hits = sum(1 for d in retrieved[:k] if d in set(relevant))
        return hits / k

    def recall_at_k(self, retrieved: List[str], relevant: List[str], k: int = 5) -> float:
        if not relevant:
            return 0.0
        hits = sum(1 for d in retrieved[:k] if d in set(relevant))
        return hits / len(relevant)

    def mean_reciprocal_rank(self, retrieved: List[str], relevant: List[str]) -> float:
        rel_set = set(relevant)
        for rank, doc in enumerate(retrieved, 1):
            if doc in rel_set:
                return 1.0 / rank
        return 0.0

    def ndcg_at_k(self, retrieved: List[str], relevant: List[str], k: int = 5) -> float:
        if not relevant:
            return 0.0
        rel_set = set(relevant)
        dcg  = sum(1.0 / np.log2(r + 2) for r, d in enumerate(retrieved[:k]) if d in rel_set)
        idcg = sum(1.0 / np.log2(r + 2) for r in range(min(len(relevant), k)))
        return dcg / idcg if idcg > 0 else 0.0

    # ── Generation metrics (upgraded) ─────────────────────────────────────────

    def bert_score(self, generated: str, reference: str, lang: str = "en") -> Dict[str, float]:
        """BERTScore P/R/F1 — semantic match beyond token overlap."""
        if not _BERTSCORE:
            logger.warning("bert-score not installed — using Jaccard fallback")
            sim = self._jaccard(generated, reference)
            return {"precision": sim, "recall": sim, "f1": sim}
        try:
            P, R, F = _bert_score([generated], [reference], lang=lang, verbose=False)
            return {
                "precision": float(P[0]),
                "recall":    float(R[0]),
                "f1":        float(F[0]),
            }
        except Exception as e:
            logger.warning("BERTScore failed: %s", e)
            sim = self._jaccard(generated, reference)
            return {"precision": sim, "recall": sim, "f1": sim}

    def answer_relevancy(self, question: str, answer: str) -> float:
        """
        Cosine similarity between question embedding and answer embedding.
        High score → answer is topically aligned with the question.
        """
        model = _get_sim_model()
        if model is None:
            return self._jaccard(question, answer)
        try:
            embs = model.encode(
                [question, answer],
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return float(np.dot(embs[0], embs[1]))
        except Exception as e:
            logger.warning("Answer relevancy embed failed: %s", e)
            return self._jaccard(question, answer)

    def faithfulness_nli(self, answer: str, context: str) -> float:
        """
        NLI-based faithfulness: fraction of answer sentences entailed by context.
        Uses cross-encoder/nli-deberta-v3-base — 3-class (contradiction/neutral/entailment).
        """
        model = _get_nli_model()
        if model is None:
            return self._token_overlap_faithfulness(answer, context)

        sentences = [s.strip() for s in answer.split(".") if len(s.strip()) > 10]
        if not sentences:
            return 1.0

        ctx_trimmed = context[:1500]
        pairs = [(ctx_trimmed, s) for s in sentences]
        try:
            raw_scores = model.predict(pairs)
            # raw_scores shape: (N, 3) — [contradiction, neutral, entailment]
            entailment_scores = [float(s[2]) for s in raw_scores]
            return float(np.mean(entailment_scores))
        except Exception as e:
            logger.warning("NLI faithfulness failed: %s", e)
            return self._token_overlap_faithfulness(answer, context)

    def llm_judge(
        self,
        query: str,
        context: str,
        answer: str,
        model: str = "gpt-4o-mini",
    ) -> Dict[str, float]:
        """
        GPT-4o-mini judge: faithfulness, answer_relevancy, completeness (0-1 each).
        Returns zeros on failure.
        """
        from openai import OpenAI
        from app.config import settings
        from app.rag.prompts import LLM_JUDGE_PROMPT

        try:
            client = OpenAI(api_key=settings.openai_api_key)
            resp = client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": LLM_JUDGE_PROMPT.format(
                        query=query,
                        context=context[:2000],
                        answer=answer[:1500],
                    ),
                }],
                max_tokens=80,
                temperature=0.0,
            )
            raw = resp.choices[0].message.content or "{}"
            # Strip markdown fences if present
            if "```" in raw:
                raw = raw.split("```")[1].lstrip("json").strip()
            data = json.loads(raw)
            return {
                "faithfulness":      float(data.get("faithfulness", 0)),
                "answer_relevancy":  float(data.get("answer_relevancy", 0)),
                "completeness":      float(data.get("completeness", 0)),
            }
        except Exception as e:
            logger.warning("LLM judge failed: %s", e)
            return {"faithfulness": 0.0, "answer_relevancy": 0.0, "completeness": 0.0}

    # ── Composite RAGAS-style evaluation ──────────────────────────────────────

    def ragas_score(
        self,
        query: str,
        answer: str,
        context: str,
        reference: Optional[str] = None,
        use_llm_judge: bool = True,
    ) -> Dict[str, Any]:
        """
        Unified evaluation combining all metrics.

        Returns a dict with individual scores + aggregate `overall_score`.
        """
        result: Dict[str, Any] = {}

        # Faithfulness (NLI)
        result["faithfulness_nli"] = round(self.faithfulness_nli(answer, context), 4)

        # Answer relevancy
        result["answer_relevancy"] = round(self.answer_relevancy(query, answer), 4)

        # BERTScore vs reference (if provided)
        if reference:
            bs = self.bert_score(answer, reference)
            result["bert_f1"]       = round(bs["f1"], 4)
            result["bert_precision"] = round(bs["precision"], 4)
            result["bert_recall"]    = round(bs["recall"], 4)

        # LLM judge
        if use_llm_judge:
            judge = self.llm_judge(query, context, answer)
            result.update({f"judge_{k}": round(v, 4) for k, v in judge.items()})

        # Aggregate: average the primary signals
        primary = [
            result.get("faithfulness_nli", 0),
            result.get("answer_relevancy", 0),
            result.get("judge_faithfulness", result.get("faithfulness_nli", 0)),
            result.get("judge_answer_relevancy", result.get("answer_relevancy", 0)),
        ]
        result["overall_score"] = round(float(np.mean(primary)), 4)

        return result

    # ── Batch evaluation ──────────────────────────────────────────────────────

    def evaluate_retrieval_batch(self, test_cases: List[Dict[str, Any]], k: int = 5) -> Dict[str, float]:
        metrics: Dict[str, List[float]] = defaultdict(list)
        for case in test_cases:
            r, rel = case["retrieved"], case["relevant"]
            metrics["precision@k"].append(self.precision_at_k(r, rel, k))
            metrics["recall@k"].append(self.recall_at_k(r, rel, k))
            metrics["mrr"].append(self.mean_reciprocal_rank(r, rel))
            metrics["ndcg@k"].append(self.ndcg_at_k(r, rel, k))
        return {m: float(np.mean(v)) for m, v in metrics.items()}

    def evaluate_generation_batch(self, test_cases: List[Dict[str, Any]]) -> Dict[str, float]:
        metrics: Dict[str, List[float]] = defaultdict(list)
        for case in test_cases:
            g, ref, ctx = case["generated"], case.get("reference", ""), case.get("context", "")
            metrics["faithfulness_nli"].append(self.faithfulness_nli(g, ctx))
            metrics["answer_relevancy"].append(self.answer_relevancy(case.get("query", g), g))
            if ref:
                bs = self.bert_score(g, ref)
                metrics["bert_f1"].append(bs["f1"])
        return {m: float(np.mean(v)) for m, v in metrics.items()}

    def generate_report(self, retrieval: Dict[str, float], generation: Dict[str, float]) -> str:
        lines = ["=" * 60, "RAG EVALUATION REPORT v2", "=" * 60, "", "RETRIEVAL:"]
        lines += [f"  {k:25s}: {v:.4f} ({v*100:.1f}%)" for k, v in retrieval.items()]
        lines += ["", "GENERATION:"]
        lines += [f"  {k:25s}: {v:.4f} ({v*100:.1f}%)" for k, v in generation.items()]
        lines += ["", "=" * 60]
        return "\n".join(lines)

    # ── Fallback helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _jaccard(a: str, b: str) -> float:
        t1, t2 = set(a.lower().split()), set(b.lower().split())
        if not t1 or not t2:
            return 0.0
        return len(t1 & t2) / len(t1 | t2)

    @staticmethod
    def _token_overlap_faithfulness(answer: str, context: str) -> float:
        sentences = [s.strip() for s in answer.split(".") if len(s.strip()) > 10]
        if not sentences:
            return 1.0
        ctx_tokens = set(context.lower().split())
        scores = [
            len(set(s.lower().split()) & ctx_tokens) / max(len(s.split()), 1)
            for s in sentences
        ]
        return float(np.mean(scores))

    # ── Legacy compatibility ───────────────────────────────────────────────────

    def rouge_l(self, generated: str, reference: str) -> float:
        """Kept for backward compat — prefer bert_score."""
        bs = self.bert_score(generated, reference)
        return bs["f1"]

    def bleu_score(self, generated: str, reference: str, n: int = 4) -> float:
        """Kept for backward compat — prefer bert_score."""
        return self._jaccard(generated, reference)

    def semantic_similarity(self, text1: str, text2: str) -> float:
        return self.answer_relevancy(text1, text2)

    def faithfulness_score(self, answer: str, context: str, threshold: float = 0.7) -> float:
        return self.faithfulness_nli(answer, context)
