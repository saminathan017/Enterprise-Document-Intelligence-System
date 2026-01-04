"""
Text chunking utilities for semantic coherence.
Uses recursive character split with overlap for context preservation.
"""

from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import settings


class DocumentChunker:
    """Handles text chunking with overlap for semantic coherence."""
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Size of each chunk (defaults to config)
            chunk_overlap: Overlap between chunks (defaults to config)
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=[
                "\n\n\n",  # Section breaks
                "\n\n",    # Paragraphs
                "\n",      # Lines
                ". ",      # Sentences
                "! ",      # Exclamations
                "? ",      # Questions
                "; ",      # Semicolons
                ", ",      # Commas
                " ",       # Words
                ""         # Characters
            ]
        )
    
    def chunk_document(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Split document into chunks with metadata.
        
        Args:
            text: Full document text
            metadata: Document metadata to attach to each chunk
            
        Returns:
            List of chunk dicts with 'text' and 'metadata' keys
        """
        if not text or not text.strip():
            return []
        
        # Split text into chunks
        chunks = self.splitter.split_text(text)
        
        # Attach metadata to each chunk
        chunk_docs = []
        for i, chunk_text in enumerate(chunks):
            chunk_metadata = {
                **metadata,
                "chunk_index": i,
                "chunk_id": f"{metadata.get('source', 'unknown')}_chunk_{i}",
                "total_chunks": len(chunks)
            }
            
            chunk_docs.append({
                "text": chunk_text,
                "metadata": chunk_metadata
            })
        
        return chunk_docs
    
    def chunk_batch(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Chunk multiple documents.
        
        Args:
            documents: List of dicts with 'text' and 'metadata'
            
        Returns:
            Flattened list of all chunks
        """
        all_chunks = []
        for doc in documents:
            chunks = self.chunk_document(
                text=doc["text"],
                metadata=doc["metadata"]
            )
            all_chunks.extend(chunks)
        
        return all_chunks
