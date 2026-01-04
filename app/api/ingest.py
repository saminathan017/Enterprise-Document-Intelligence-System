"""
Document ingestion endpoint.
Handles file upload and indexing.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import json

from app.models.responses import IngestResponse, ErrorResponse
from app.ingestion.pipeline import IngestionPipeline
from app.vectorstore.store import get_vector_store


router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(..., description="Document file to ingest"),
    metadata: Optional[str] = Form(
        default=None,
        description="JSON string of additional metadata"
    )
):
    """
    Ingest a document into the vector store.
    
    Supports: PDF, TXT, MD files
    
    Args:
        file: Uploaded file
        metadata: Optional JSON string with metadata
        
    Returns:
        IngestResponse with ingestion results
    """
    try:
        # Read file content
        content = await file.read()
        
        # Parse metadata if provided
        meta_dict = None
        if metadata:
            try:
                meta_dict = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid JSON in metadata field"
                )
        
        # Initialize pipeline
        vector_store = get_vector_store()
        pipeline = IngestionPipeline(vector_store)
        
        # Ingest document
        result = pipeline.ingest_document(
            content=content,
            filename=file.filename,
            metadata=meta_dict
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Unknown ingestion error")
            )
        
        return IngestResponse(
            success=True,
            filename=result["filename"],
            chunks_created=result["chunks_created"],
            document_id=result["document_id"],
            message=f"Successfully ingested {file.filename} with {result['chunks_created']} chunks"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}"
        )
