"""
Unit tests for document chunking.
Tests chunking logic and overlap.
"""

import pytest
from app.ingestion.chunker import DocumentChunker


class TestDocumentChunker:
    """Test document chunking functionality."""
    
    def test_chunker_initialization(self):
        """Test chunker initializes with correct parameters."""
        chunker = DocumentChunker(chunk_size=1000, chunk_overlap=300)
        
        assert chunker.chunk_size == 1000
        assert chunker.chunk_overlap == 300
    
    def test_chunk_document_creates_chunks(self):
        """Test that documents are split into chunks."""
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
        
        text = "This is a test document. " * 50  # Long text
        metadata = {"source": "test.pdf"}
        
        chunks = chunker.chunk_document(text, metadata)
        
        assert len(chunks) > 1, "Long text should create multiple chunks"
        
        # Each chunk should have text and metadata
        for chunk in chunks:
            assert "text" in chunk
            assert "metadata" in chunk
            assert chunk["metadata"]["source"] == "test.pdf"
    
    def test_chunk_metadata_includes_index(self):
        """Test that chunks include chunk_index in metadata."""
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
        
        text = "This is a test. " * 50
        metadata = {"source": "test.pdf"}
        
        chunks = chunker.chunk_document(text, metadata)
        
        for i, chunk in enumerate(chunks):
            assert chunk["metadata"]["chunk_index"] == i
            assert "chunk_id" in chunk["metadata"]
            assert "total_chunks" in chunk["metadata"]
    
    def test_empty_text_returns_empty_list(self):
        """Test that empty text returns no chunks."""
        chunker = DocumentChunker()
        
        chunks = chunker.chunk_document("", {"source": "test.pdf"})
        assert len(chunks) == 0
        
        chunks = chunker.chunk_document("   ", {"source": "test.pdf"})
        assert len(chunks) == 0
    
    def test_chunk_size_respected(self):
        """Test that chunks respect maximum size."""
        chunk_size = 100
        chunker = DocumentChunker(chunk_size=chunk_size, chunk_overlap=20)
        
        text = "word " * 200  # Create long text
        metadata = {"source": "test.pdf"}
        
        chunks = chunker.chunk_document(text, metadata)
        
        for chunk in chunks:
            # Chunks should be approximately chunk_size (may vary slightly)
            assert len(chunk["text"]) <= chunk_size * 1.5, \
                f"Chunk too large: {len(chunk['text'])} chars"
    
    def test_batch_chunking(self):
        """Test chunking multiple documents."""
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
        
        documents = [
            {"text": "Document 1 text. " * 20, "metadata": {"source": "doc1.pdf"}},
            {"text": "Document 2 text. " * 20, "metadata": {"source": "doc2.pdf"}}
        ]
        
        all_chunks = chunker.chunk_batch(documents)
        
        assert len(all_chunks) > 0
        
        # Should have chunks from both documents
        sources = {chunk["metadata"]["source"] for chunk in all_chunks}
        assert "doc1.pdf" in sources
        assert "doc2.pdf" in sources


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
