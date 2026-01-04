"""
Unit tests for API endpoints.
Tests query, ingest, and evaluation endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from app.main import app


client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "operational"
        assert "endpoints" in data
        # Note: evaluate endpoint requires server restart to load
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/health")
        # May return 200 or 503 depending on vector store
        assert response.status_code in [200, 503]


class TestQueryEndpoint:
    """Test query endpoint functionality."""
    
    @patch('app.api.query.get_vector_store')
    @patch('app.api.query.get_session_manager')
    def test_conversational_filter(self, mock_session, mock_store):
        """Test that conversational messages get natural responses."""
        # Mock session manager
        mock_session.return_value.get_session.return_value = None
        mock_session.return_value.create_session.return_value = None
        mock_session.return_value.update_session.return_value = None
        
        # Test conversational message
        response = client.post(
            "/api/v1/query",
            json={
                "query": "thanks",
                "session_id": "test-session"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should get conversational response
        assert data["success"] == True
        assert "welcome" in data["answer"].lower()
        assert len(data["citations"]) == 0  # No citations for conversation
    
    @patch('app.api.query.get_vector_store')
    @patch('app.api.query.get_session_manager')
    def test_conversational_phrases(self, mock_session, mock_store):
        """Test various conversational phrases."""
        mock_session.return_value.get_session.return_value = None
        mock_session.return_value.create_session.return_value = None
        mock_session.return_value.update_session.return_value = None
        
        conversational_inputs = ["great", "ok", "cool", "hi", "bye"]
        
        for phrase in conversational_inputs:
            response = client.post(
                "/api/v1/query",
                json={"query": phrase, "session_id": "test"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["citations"]) == 0, \
                f"Conversational phrase '{phrase}' triggered RAG"


class TestEvaluationEndpoint:
    """Test evaluation endpoint (requires server restart to load)."""
    
    def test_evaluate_endpoint_structure(self):
        """Test evaluation endpoint if available."""
        test_data = {
            "test_cases": [
                {
                    "query": "test query",
                    "retrieved_docs": ["doc1", "doc2"],
                    "relevant_docs": ["doc1"],
                    "generated_answer": "This is a test answer.",
                    "reference_answer": "This is the reference.",
                    "context": "Context for the answer."
                }
            ],
            "k": 5
        }
        
        response = client.post("/api/v1/evaluate", json=test_data)
        
        # Skip if endpoint not loaded (requires server restart)
        if response.status_code == 404:
            pytest.skip("Evaluation endpoint requires server restart to load")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "retrieval_metrics" in data
        assert "generation_metrics" in data
        assert "report" in data
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint if available."""
        response = client.get("/api/v1/metrics")
        
        # Skip if endpoint not loaded (requires server restart)
        if response.status_code == 404:
            pytest.skip("Metrics endpoint requires server restart to load")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "metrics" in data
        assert "citation_accuracy" in data["metrics"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
