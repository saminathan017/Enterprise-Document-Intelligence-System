"""
RAG Evaluation Metrics Framework

Comprehensive evaluation for Retrieval-Augmented Generation systems.
Includes retrieval metrics, generation metrics, and faithfulness detection.
"""

from typing import List, Dict, Any, Tuple
import numpy as np
from collections import defaultdict


class RAGEvaluator:
    """Comprehensive RAG evaluation with industry-standard metrics."""
    
    def __init__(self):
        self.results = defaultdict(list)
    
    # ==================== RETRIEVAL METRICS ====================
    
    def precision_at_k(
        self, 
        retrieved_docs: List[str], 
        relevant_docs: List[str], 
        k: int = 5
    ) -> float:
        """
        Precision@K: What fraction of top-K retrieved docs are relevant?
        
        Args:
            retrieved_docs: List of retrieved document IDs
            relevant_docs: List of ground truth relevant document IDs
            k: Number of top documents to consider
            
        Returns:
            Precision@K score (0.0 to 1.0)
        """
        if not retrieved_docs or k == 0:
            return 0.0
        
        top_k = retrieved_docs[:k]
        relevant_set = set(relevant_docs)
        
        num_relevant = sum(1 for doc in top_k if doc in relevant_set)
        return num_relevant / k
    
    def recall_at_k(
        self, 
        retrieved_docs: List[str], 
        relevant_docs: List[str], 
        k: int = 5
    ) -> float:
        """
        Recall@K: What fraction of relevant docs are in top-K?
        
        Args:
            retrieved_docs: List of retrieved document IDs
            relevant_docs: List of ground truth relevant document IDs
            k: Number of top documents to consider
            
        Returns:
            Recall@K score (0.0 to 1.0)
        """
        if not relevant_docs:
            return 0.0
        
        top_k = retrieved_docs[:k]
        relevant_set = set(relevant_docs)
        
        num_relevant = sum(1 for doc in top_k if doc in relevant_set)
        return num_relevant / len(relevant_docs)
    
    def mean_reciprocal_rank(
        self, 
        retrieved_docs: List[str], 
        relevant_docs: List[str]
    ) -> float:
        """
        MRR: Average of reciprocal ranks of first relevant document.
        
        Args:
            retrieved_docs: List of retrieved document IDs
            relevant_docs: List of ground truth relevant document IDs
            
        Returns:
            MRR score (0.0 to 1.0)
        """
        relevant_set = set(relevant_docs)
        
        for rank, doc in enumerate(retrieved_docs, 1):
            if doc in relevant_set:
                return 1.0 / rank
        
        return 0.0
    
    def ndcg_at_k(
        self, 
        retrieved_docs: List[str], 
        relevant_docs: List[str],
        k: int = 5
    ) -> float:
        """
        NDCG@K: Normalized Discounted Cumulative Gain.
        Accounts for position of relevant documents.
        
        Args:
            retrieved_docs: List of retrieved document IDs
            relevant_docs: List of ground truth relevant document IDs
            k: Number of top documents to consider
            
        Returns:
            NDCG@K score (0.0 to 1.0)
        """
        if not relevant_docs:
            return 0.0
        
        relevant_set = set(relevant_docs)
        top_k = retrieved_docs[:k]
        
        # DCG: sum of (relevance / log2(rank+1))
        dcg = sum(
            1.0 / np.log2(rank + 2)  # +2 because rank starts at 0
            for rank, doc in enumerate(top_k)
            if doc in relevant_set
        )
        
        # IDCG: best possible DCG
        idcg = sum(
            1.0 / np.log2(rank + 2)
            for rank in range(min(len(relevant_docs), k))
        )
        
        return dcg / idcg if idcg > 0 else 0.0
    
    # ==================== GENERATION METRICS ====================
    
    def rouge_l(self, generated: str, reference: str) -> float:
        """
        ROUGE-L: Longest Common Subsequence based metric.
        
        Args:
            generated: Generated answer
            reference: Reference answer
            
        Returns:
            ROUGE-L F1 score (0.0 to 1.0)
        """
        gen_tokens = generated.lower().split()
        ref_tokens = reference.lower().split()
        
        if not gen_tokens or not ref_tokens:
            return 0.0
        
        # Compute LCS length
        lcs_length = self._lcs_length(gen_tokens, ref_tokens)
        
        # Precision and Recall
        precision = lcs_length / len(gen_tokens) if gen_tokens else 0.0
        recall = lcs_length / len(ref_tokens) if ref_tokens else 0.0
        
        # F1 score
        if precision + recall == 0:
            return 0.0
        
        f1 = 2 * (precision * recall) / (precision + recall)
        return f1
    
    def _lcs_length(self, seq1: List[str], seq2: List[str]) -> int:
        """Compute length of longest common subsequence."""
        m, n = len(seq1), len(seq2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i-1] == seq2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]
    
    def bleu_score(self, generated: str, reference: str, n: int = 4) -> float:
        """
        BLEU: Bilingual Evaluation Understudy score.
        
        Args:
            generated: Generated answer
            reference: Reference answer
            n: Maximum n-gram size (default: 4)
            
        Returns:
            BLEU score (0.0 to 1.0)
        """
        gen_tokens = generated.lower().split()
        ref_tokens = reference.lower().split()
        
        if not gen_tokens or not ref_tokens:
            return 0.0
        
        # Brevity penalty
        bp = min(1.0, np.exp(1 - len(ref_tokens) / len(gen_tokens)))
        
        # Compute n-gram precisions
        precisions = []
        for i in range(1, n + 1):
            gen_ngrams = self._get_ngrams(gen_tokens, i)
            ref_ngrams = self._get_ngrams(ref_tokens, i)
            
            if not gen_ngrams:
                precisions.append(0.0)
                continue
            
            matches = sum(
                min(gen_ngrams[ng], ref_ngrams.get(ng, 0))
                for ng in gen_ngrams
            )
            
            precision = matches / sum(gen_ngrams.values())
            precisions.append(precision)
        
        # Geometric mean of precisions
        if any(p == 0 for p in precisions):
            return 0.0
        
        geo_mean = np.exp(np.mean([np.log(p) for p in precisions]))
        return bp * geo_mean
    
    def _get_ngrams(self, tokens: List[str], n: int) -> Dict[Tuple, int]:
        """Extract n-grams from token list."""
        ngrams = defaultdict(int)
        for i in range(len(tokens) - n + 1):
            ngram = tuple(tokens[i:i+n])
            ngrams[ngram] += 1
        return ngrams
    
    def semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Semantic similarity using simple token overlap.
        For production, use sentence transformers.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Jaccard similarity (0.0 to 1.0)
        """
        tokens1 = set(text1.lower().split())
        tokens2 = set(text2.lower().split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2
        
        return len(intersection) / len(union)
    
    # ==================== FAITHFULNESS DETECTION ====================
    
    def faithfulness_score(
        self, 
        answer: str, 
        context: str,
        threshold: float = 0.7
    ) -> float:
        """
        Faithfulness: Is the answer grounded in the context?
        Simple implementation using token overlap.
        
        Args:
            answer: Generated answer
            context: Retrieved context
            threshold: Minimum overlap for faithfulness
            
        Returns:
            Faithfulness score (0.0 to 1.0)
        """
        # Extract claims from answer (simplified: sentences)
        claims = [s.strip() for s in answer.split('.') if s.strip()]
        
        if not claims:
            return 1.0
        
        # Check each claim against context
        faithful_claims = 0
        for claim in claims:
            overlap = self.semantic_similarity(claim, context)
            if overlap >= threshold:
                faithful_claims += 1
        
        return faithful_claims / len(claims)
    
    # ==================== BATCH EVALUATION ====================
    
    def evaluate_retrieval_batch(
        self,
        test_cases: List[Dict[str, Any]],
        k: int = 5
    ) -> Dict[str, float]:
        """
        Evaluate retrieval on a batch of test cases.
        
        Args:
            test_cases: List of dicts with 'retrieved' and 'relevant' keys
            k: Number of top documents to consider
            
        Returns:
            Dict of average metrics
        """
        metrics = {
            'precision@k': [],
            'recall@k': [],
            'mrr': [],
            'ndcg@k': []
        }
        
        for case in test_cases:
            retrieved = case['retrieved']
            relevant = case['relevant']
            
            metrics['precision@k'].append(
                self.precision_at_k(retrieved, relevant, k)
            )
            metrics['recall@k'].append(
                self.recall_at_k(retrieved, relevant, k)
            )
            metrics['mrr'].append(
                self.mean_reciprocal_rank(retrieved, relevant)
            )
            metrics['ndcg@k'].append(
                self.ndcg_at_k(retrieved, relevant, k)
            )
        
        # Return averages
        return {
            metric: np.mean(scores)
            for metric, scores in metrics.items()
        }
    
    def evaluate_generation_batch(
        self,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Evaluate generation on a batch of test cases.
        
        Args:
            test_cases: List of dicts with 'generated', 'reference', 'context'
            
        Returns:
            Dict of average metrics
        """
        metrics = {
            'rouge_l': [],
            'bleu': [],
            'semantic_sim': [],
            'faithfulness': []
        }
        
        for case in test_cases:
            generated = case['generated']
            reference = case['reference']
            context = case.get('context', '')
            
            metrics['rouge_l'].append(
                self.rouge_l(generated, reference)
            )
            metrics['bleu'].append(
                self.bleu_score(generated, reference)
            )
            metrics['semantic_sim'].append(
                self.semantic_similarity(generated, reference)
            )
            metrics['faithfulness'].append(
                self.faithfulness_score(generated, context)
            )
        
        # Return averages
        return {
            metric: np.mean(scores)
            for metric, scores in metrics.items()
        }
    
    def generate_report(
        self,
        retrieval_metrics: Dict[str, float],
        generation_metrics: Dict[str, float]
    ) -> str:
        """Generate a formatted evaluation report."""
        report = []
        report.append("=" * 60)
        report.append("RAG EVALUATION REPORT")
        report.append("=" * 60)
        report.append("")
        
        report.append("RETRIEVAL METRICS:")
        report.append("-" * 60)
        for metric, score in retrieval_metrics.items():
            report.append(f"  {metric:20s}: {score:.4f} ({score*100:.2f}%)")
        report.append("")
        
        report.append("GENERATION METRICS:")
        report.append("-" * 60)
        for metric, score in generation_metrics.items():
            report.append(f"  {metric:20s}: {score:.4f} ({score*100:.2f}%)")
        report.append("")
        
        report.append("=" * 60)
        return "\n".join(report)
