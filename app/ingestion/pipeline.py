"""
End-to-end document ingestion pipeline.
Orchestrates: load → chunk → embed → index.
"""

from typing import Dict, Any
import hashlib
from datetime import datetime

from app.ingestion.loaders import DocumentLoaderFactory
from app.ingestion.chunker import DocumentChunker
from app.vectorstore.store import VectorStore


class IngestionPipeline:
    """Orchestrates document ingestion workflow."""
    
    def __init__(self, vector_store: VectorStore):
        """
        Initialize pipeline.
        
        Args:
            vector_store: VectorStore instance for indexing
        """
        self.vector_store = vector_store
        self.chunker = DocumentChunker()
        self.loader_factory = DocumentLoaderFactory()
    
    def ingest_document(
        self,
        content: bytes,
        filename: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Full ingestion pipeline for a single document.
        
        Args:
            content: File content as bytes
            filename: Original filename
            metadata: Optional additional metadata
            
        Returns:
            Dict with ingestion results (document_id, chunks_created, etc.)
        """
        # Step 1: Load document
        loader = self.loader_factory.get_loader(filename)
        doc_data = loader.load(content, filename, metadata)
        
        # Generate unique document ID
        doc_id = self._generate_doc_id(content, filename)
        doc_data["metadata"]["document_id"] = doc_id
        doc_data["metadata"]["ingested_at"] = datetime.utcnow().isoformat()
        
        # Step 2: Chunk document
        chunks = self.chunker.chunk_document(
            text=doc_data["text"],
            metadata=doc_data["metadata"]
        )
        
        if not chunks:
            return {
                "success": False,
                "document_id": doc_id,
                "chunks_created": 0,
                "error": "No text could be extracted from document"
            }
        
        # Step 3: Index chunks in vector store
        chunk_ids = self.vector_store.add_documents(chunks)
        
        return {
            "success": True,
            "document_id": doc_id,
            "filename": filename,
            "chunks_created": len(chunks),
            "chunk_ids": chunk_ids,
            "metadata": doc_data["metadata"]
        }
    
    def _generate_doc_id(self, content: bytes, filename: str) -> str:
        """
        Generate unique document ID based on content hash.
        
        Args:
            content: File content
            filename: Filename
            
        Returns:
            Unique document ID
        """
        content_hash = hashlib.sha256(content).hexdigest()[:16]
        return f"{filename}_{content_hash}"
    
    def get_document_count(self) -> int:
        """Get total number of documents in the vector store."""
        return self.vector_store.get_document_count()
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete document and all its chunks from vector store.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            True if deleted successfully
        """
        return self.vector_store.delete_by_metadata("document_id", document_id)
