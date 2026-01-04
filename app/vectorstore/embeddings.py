"""
Embedding generation using Sentence Transformers.
Local embeddings for cost efficiency and speed.
"""

from typing import List
from sentence_transformers import SentenceTransformer
from app.config import settings


class EmbeddingGenerator:
    """Generates embeddings using local Sentence Transformer model."""
    
    def __init__(
        self,
        model_name: str = None,
        device: str = None
    ):
        """
        Initialize embedding generator.
        
        Args:
            model_name: Sentence transformer model name
            device: Device to run on ('cpu', 'cuda', or 'mps')
        """
        self.model_name = model_name or settings.embedding_model
        self.device = device or settings.embedding_device
        
        # Load model (will cache after first load)
        self.model = SentenceTransformer(self.model_name, device=self.device)
        
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (each is a list of floats)
        """
        if not texts:
            return []
        
        # Generate embeddings (batch processing for efficiency)
        embeddings = self.model.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True  # Ensure L2 normalization for cosine similarity
        )
        
        # Convert numpy arrays to lists for serialization
        return [emb.tolist() for emb in embeddings]
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a single query.
        
        Args:
            query: Query text
            
        Returns:
            Embedding vector as list of floats
        """
        embedding = self.model.encode(
            query,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True  # Ensure L2 normalization
        )
        return embedding.tolist()
    
    def get_embedding_dimension(self) -> int:
        """Return the dimension of the embedding vectors."""
        return self.model.get_sentence_embedding_dimension()


# Global singleton instance
_embedding_generator = None


def get_embedding_generator() -> EmbeddingGenerator:
    """Get or create global embedding generator instance."""
    global _embedding_generator
    if _embedding_generator is None:
        _embedding_generator = EmbeddingGenerator()
    return _embedding_generator
