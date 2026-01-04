"""Test configuration and fixtures for pytest."""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_document():
    """Sample document for testing."""
    return {
        "text": "This is a sample document for testing. It contains multiple sentences. "
                "We use this to test chunking and retrieval.",
        "metadata": {
            "source": "test_document.pdf",
            "page": 1
        }
    }


@pytest.fixture
def sample_query():
    """Sample query for testing."""
    return "What is this document about?"


@pytest.fixture
def sample_test_case():
    """Sample evaluation test case."""
    return {
        "query": "What is the revenue?",
        "retrieved_docs": ["doc1", "doc2", "doc3"],
        "relevant_docs": ["doc1", "doc2"],
        "generated_answer": "The revenue is $100M.",
        "reference_answer": "Revenue was $100 million.",
        "context": "The company reported revenue of $100M in Q3."
    }
