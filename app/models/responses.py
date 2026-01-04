"""
Response models for API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class Citation(BaseModel):
    """Citation for a retrieved document."""
    
    source: str = Field(..., description="Source document filename")
    chunk_id: Optional[str] = Field(None, description="Chunk identifier")
    score: float = Field(..., description="Relevance score", ge=0.0, le=1.0)
    excerpt: Optional[str] = Field(None, description="Relevant excerpt")


class IngestResponse(BaseModel):
    """Response model for document ingestion."""
    
    success: bool = Field(..., description="Whether ingestion succeeded")
    filename: str = Field(..., description="Ingested filename")
    chunks_created: int = Field(..., description="Number of chunks created")
    document_id: str = Field(..., description="Unique document identifier")
    message: str = Field(..., description="Human-readable status message")


class QueryResponse(BaseModel):
    """Response model for RAG query."""
    
    success: bool = Field(..., description="Whether query succeeded")
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer with citations")
    citations: List[Citation] = Field(..., description="Source citations")
    session_id: str = Field(..., description="Session identifier")
    used_web: bool = Field(default=False, description="Whether web tool was used")
    used_table: bool = Field(default=False, description="Whether table tool was used")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "query": "What were Q3 revenue trends?",
                "answer": "Revenue increased 15% YoY... [Source: q3_report.pdf]",
                "citations": [
                    {
                        "source": "q3_report.pdf",
                        "chunk_id": "chunk-5",
                        "score": 0.89,
                        "excerpt": "Q3 revenue reached $2.3M..."
                    }
                ],
                "session_id": "session-12345",
                "used_web": False,
                "used_table": True,
                "processing_time_ms": 1250
            }
        }


class SessionResponse(BaseModel):
    """Response model for session operations."""
    
    session_id: str = Field(..., description="Session identifier")
    created_at: datetime = Field(..., description="Session creation timestamp")
    message_count: int = Field(..., description="Number of messages in history")
    last_activity: datetime = Field(..., description="Last activity timestamp")


class ErrorResponse(BaseModel):
    """Error response model."""
    
    success: bool = Field(default=False, description="Always False for errors")
    error_type: str = Field(..., description="Error category")
    error_message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error context"
    )
