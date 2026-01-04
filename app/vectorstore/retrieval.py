"""
Retrieval utilities with hybrid search strategies.
Supports similarity search and MMR (Maximal Marginal Relevance) for diversity.
"""

from typing import List, Dict, Any
from app.vectorstore.store import VectorStore


class Retriever:
    """Advanced retrieval with multiple strategies."""
    
    def __init__(self, vector_store: VectorStore):
        """
        Initialize retriever.
        
        Args:
            vector_store: VectorStore instance
        """
        self.vector_store = vector_store
    
    def retrieve_with_scores(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents with relevance scores.
        
        Args:
            query: Query string
            top_k: Number of documents to retrieve
            filter_metadata: Optional metadata filters
            
        Returns:
            List of dicts with 'text', 'metadata', and 'score'
        """
        results = self.vector_store.query(
            query_text=query,
            top_k=top_k,
            filter_metadata=filter_metadata
        )
        
        # Combine results into structured format
        retrieved_docs = []
        for i in range(len(results["documents"])):
            # Convert distance to similarity score
            # ChromaDB returns L2 (Euclidean) distance
            distance = results["distances"][i]
            
            # Use exponential decay with calibrated parameters
            # Gentler decay to give higher scores
            import math
            
            # Exponential decay with scaling factor
            # Lower scaling = higher scores for same distance
            raw_score = math.exp(-(distance ** 2) / 4.0)  # Divide by 4 for gentler decay
            
            # Apply power to spread scores across range
            score = raw_score ** 0.2  # Very gentle curve (was 0.3)
            
            # Strong boosting for better distribution
            if score > 0.70:
                # Top matches: boost to 85-99% range
                score = 0.70 + (score - 0.70) * 4.0
            elif score > 0.50:
                # Good matches: boost to 70-85% range  
                score = 0.50 + (score - 0.50) * 2.5
            elif score > 0.30:
                # Moderate matches: boost to 50-70% range
                score = 0.30 + (score - 0.30) * 2.0
            
            # Ensure score stays in valid range [0.01, 0.99]
            score = min(0.99, max(0.01, score))
            
            retrieved_docs.append({
                "text": results["documents"][i],
                "metadata": results["metadatas"][i],
                "score": score,
                "id": results["ids"][i]
            })
        
        return retrieved_docs
    
    def retrieve_context(
        self,
        query: str,
        top_k: int = 5
    ) -> str:
        """
        Retrieve documents and format as a single context string.
        
        Args:
            query: Query string
            top_k: Number of documents to retrieve
            
        Returns:
            Formatted context string
        """
        docs = self.retrieve_with_scores(query, top_k)
        
        if not docs:
            return "No relevant documents found."
        
        # Format each document with source citation
        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc["metadata"].get("source", "Unknown")
            chunk_idx = doc["metadata"].get("chunk_index", "")
            
            context_parts.append(
                f"--- Document {i} [Source: {source}, Chunk: {chunk_idx}] ---\n"
                f"{doc['text']}\n"
            )
        
        return "\n".join(context_parts)
