"""
ChromaDB vector store wrapper.
Handles CRUD operations with persistent storage.
"""

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from pathlib import Path

from app.config import settings
from app.vectorstore.embeddings import get_embedding_generator


class VectorStore:
    """ChromaDB wrapper for document storage and retrieval."""
    
    def __init__(
        self,
        persist_directory: Path = None,
        collection_name: str = None
    ):
        """
        Initialize vector store.
        
        Args:
            persist_directory: Directory for persistent storage
            collection_name: Name of the collection
        """
        self.persist_directory = persist_directory or settings.chroma_persist_dir
        self.collection_name = collection_name or settings.collection_name
        
        # Ensure persist directory exists
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get embedding generator
        self.embedding_generator = get_embedding_generator()
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Enterprise document collection"}
        )
    
    def add_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of dicts with 'text' and 'metadata' keys
            
        Returns:
            List of document IDs
        """
        if not documents:
            return []
        
        # Extract texts and metadata
        texts = [doc["text"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        
        # Generate embeddings
        embeddings = self.embedding_generator.embed_texts(texts)
        
        # Generate IDs using chunk_id from metadata
        ids = [
            meta.get("chunk_id", f"doc_{i}")
            for i, meta in enumerate(metadatas)
        ]
        
        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        
        return ids
    
    def query(
        self,
        query_text: str,
        top_k: int = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query the vector store for similar documents.
        
        Args:
            query_text: Query string
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            Dict with 'documents', 'metadatas', 'distances', 'ids'
        """
        top_k = top_k or settings.top_k_retrieval
        
        # Generate query embedding
        query_embedding = self.embedding_generator.embed_query(query_text)
        
        # Query collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata,
            include=["documents", "metadatas", "distances"]
        )
        
        # Unpack results (ChromaDB returns lists of lists)
        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "ids": results["ids"][0] if results["ids"] else []
        }
    
    def get_document_count(self) -> int:
        """Get total number of documents in collection."""
        return self.collection.count()
    
    def delete_by_metadata(self, key: str, value: Any) -> bool:
        """
        Delete documents matching metadata filter.
        
        Args:
            key: Metadata key
            value: Metadata value to match
            
        Returns:
            True if deletion successful
        """
        try:
            self.collection.delete(
                where={key: value}
            )
            return True
        except Exception:
            return False
    
    def reset_collection(self):
        """Delete all documents and recreate collection."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "Enterprise document collection"}
        )


# Global singleton instance
_vector_store = None


def get_vector_store() -> VectorStore:
    """Get or create global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
