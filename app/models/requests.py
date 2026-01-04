"""
Request models for API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional


class IngestRequest(BaseModel):
    """Request model for document ingestion."""
    
    filename: str = Field(..., description="Name of the file being ingested")
    content: bytes = Field(..., description="File content as bytes")
    metadata: Optional[dict] = Field(
        default=None,
        description="Additional metadata (author, date, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "filename": "quarterly_report.pdf",
                "content": "b'...'",
                "metadata": {"author": "Finance Team", "quarter": "Q3 2024"}
            }
        }


class QueryRequest(BaseModel):
    """Request model for RAG query."""
    
    query: str = Field(..., description="User query", min_length=1)
    session_id: str = Field(..., description="Session identifier for memory")
    use_web: bool = Field(
        default=False,
        description="Enable web-augmented synthesis"
    )
    make_table: bool = Field(
        default=False,
        description="Generate markdown table in response"
    )
    top_k: Optional[int] = Field(
        default=None,
        description="Override number of documents to retrieve"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What were the revenue trends in Q3?",
                "session_id": "session-12345",
                "use_web": False,
                "make_table": True,
                "top_k": 5
            }
        }


class SessionRequest(BaseModel):
    """Request model for session operations."""
    
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID to retrieve; if None, creates new session"
    )
    clear_history: bool = Field(
        default=False,
        description="Clear conversation history for this session"
    )
