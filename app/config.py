"""
Centralized configuration management using Pydantic Settings.
Loads from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")
    
    # Server Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_reload: bool = Field(default=False, description="Auto-reload on changes")
    
    # Vector Database
    chroma_persist_dir: Path = Field(
        default=Path("./data/chroma_db"),
        description="ChromaDB persistence directory"
    )
    collection_name: str = Field(
        default="enterprise_docs",
        description="ChromaDB collection name"
    )
    
    # Embeddings
    embedding_model: str = Field(
        default="BAAI/bge-large-en-v1.5",
        description="Sentence transformer model (BGE query-prefix optimized)"
    )
    embedding_device: str = Field(default="cpu", description="Device for embeddings")
    embedding_dim: int = Field(default=1024, description="Embedding dimension for BAAI/bge-large-en-v1.5")
    
    # LLM Configuration
    llm_model: str = Field(
        default="gpt-4-turbo-preview",
        description="OpenAI model for final generation"
    )
    helper_model: str = Field(
        default="gpt-4o-mini",
        description="Fast/cheap model for HyDE, CRAG, compression, KG extraction"
    )
    ocr_model: str = Field(
        default="gpt-4o",
        description="Vision-capable model for scanned PDF OCR"
    )
    llm_temperature: float = Field(default=0.1, description="LLM temperature")
    max_tokens: int = Field(default=2000, description="Max tokens in response")
    
    # RAG Configuration
    chunk_size: int = Field(default=1000, description="Text chunk size (optimized for tables)")
    chunk_overlap: int = Field(default=300, description="Chunk overlap (30% for table continuity)")
    top_k_retrieval: int = Field(default=5, description="Number of docs to retrieve")
    
    # Session Management
    session_persist_dir: Path = Field(
        default=Path("./data/sessions"),
        description="Session persistence directory"
    )
    session_timeout_minutes: int = Field(
        default=60,
        description="Session timeout in minutes"
    )
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json/text)")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
