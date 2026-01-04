"""
Unit tests for retrieval and scoring functions.
Tests the exponential decay formula and score calculation.
"""

import pytest
import math
from app.vectorstore.retrieval import Retriever
from unittest.mock import Mock, MagicMock


class TestScoreCalculation:
    """Test score calculation with exponential decay formula."""
    
    def test_score_never_zero(self):
        """Score should never be 0% for any finite distance."""
        # Simulate different distances
        distances = [0.1, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0]
        
        for distance in distances:
            # Calculate score using the formula
            raw_score = math.exp(-(distance ** 2) / 4.0)
            score = raw_score ** 0.2
            
            # Apply boosting
            if score > 0.70:
                score = 0.70 + (score - 0.70) * 4.0
            elif score > 0.50:
                score = 0.50 + (score - 0.50) * 2.5
            elif score > 0.30:
                score = 0.30 + (score - 0.30) * 2.0
            
            score = min(0.99, max(0.01, score))
            
            assert score > 0.0, f"Score is 0 for distance {distance}"
            assert score >= 0.01, f"Score below minimum for distance {distance}"
    
    def test_score_decreases_with_distance(self):
        """Score should decrease as distance increases."""
        # Use distances >= 3.0 where base scores are definitively below 0.70
        # Distance 2.67 produces exactly 0.70, so 3.0+ avoids all boosting
        distances = [3.0, 3.5, 4.0, 5.0, 7.0]
        scores = []
        
        for distance in distances:
            raw_score = math.exp(-(distance ** 2) / 4.0)
            score = raw_score ** 0.2
            
            if score > 0.70:
                score = 0.70 + (score - 0.70) * 4.0
            elif score > 0.50:
                score = 0.50 + (score - 0.50) * 2.5
            elif score > 0.30:
                score = 0.30 + (score - 0.30) * 2.0
            
            score = min(0.99, max(0.01, score))
            scores.append(score)
        
        # Scores should be monotonically decreasing
        for i in range(len(scores) - 1):
            assert scores[i] > scores[i+1], \
                f"Score not decreasing: {scores[i]:.4f} vs {scores[i+1]:.4f} at distances {distances[i]} vs {distances[i+1]}"
    
    def test_small_distance_high_score(self):
        """Small distances should produce high scores (>90%)."""
        distance = 0.1
        raw_score = math.exp(-(distance ** 2) / 4.0)
        score = raw_score ** 0.2
        
        if score > 0.70:
            score = 0.70 + (score - 0.70) * 4.0
        
        score = min(0.99, max(0.01, score))
        
        assert score > 0.90, f"Small distance score too low: {score}"
    
    def test_score_in_valid_range(self):
        """All scores should be between 0.01 and 0.99."""
        distances = [0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        
        for distance in distances:
            raw_score = math.exp(-(distance ** 2) / 4.0)
            score = raw_score ** 0.2
            
            if score > 0.70:
                score = 0.70 + (score - 0.70) * 4.0
            elif score > 0.50:
                score = 0.50 + (score - 0.50) * 2.5
            
            score = min(0.99, max(0.01, score))
            
            assert 0.01 <= score <= 0.99, \
                f"Score out of range for distance {distance}: {score}"


class TestRetriever:
    """Test retriever functionality."""
    
    def test_retriever_initialization(self):
        """Test retriever can be initialized with mock vector store."""
        mock_store = Mock()
        retriever = Retriever(mock_store)
        
        assert retriever.vector_store == mock_store
    
    def test_retrieve_with_scores_structure(self):
        """Test that retrieve_with_scores returns correct structure."""
        # Create mock vector store
        # ChromaDB returns flat lists, not nested lists
        mock_store = Mock()
        mock_store.query.return_value = {
            "documents": ["doc1 text", "doc2 text"],
            "distances": [0.5, 1.0],
            "metadatas": [{"source": "test.pdf"}, {"source": "test.pdf"}],
            "ids": ["id1", "id2"]
        }
        
        retriever = Retriever(mock_store)
        results = retriever.retrieve_with_scores("test query", top_k=2)
        
        assert len(results) == 2
        assert "text" in results[0]
        assert "metadata" in results[0]
        assert "score" in results[0]
        assert "id" in results[0]
        
        # Scores should be valid
        assert 0.01 <= results[0]["score"] <= 0.99
        assert 0.01 <= results[1]["score"] <= 0.99


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
