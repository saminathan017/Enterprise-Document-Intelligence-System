"""
FastAPI application entry point.
Main server with route registration and middleware.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api import ingest, query, session, evaluate


# Create FastAPI app
app = FastAPI(
    title="Enterprise AI Analyst API",
    description=(
        "Production-ready AI system for document ingestion, RAG with citations, "
        "agentic tools (web synthesis, table generation), and session memory. "
        "Designed for enterprise business intelligence and analysis."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(ingest.router, prefix="/api/v1", tags=["Ingestion"])
app.include_router(query.router, prefix="/api/v1", tags=["Query"])
app.include_router(session.router, prefix="/api/v1", tags=["Session"])
app.include_router(evaluate.router, prefix="/api/v1", tags=["Evaluation"])


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Enterprise AI Analyst API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "ingest": "/api/v1/ingest",
            "query": "/api/v1/query",
            "session": "/api/v1/session",
            "evaluate": "/api/v1/evaluate",
            "metrics": "/api/v1/metrics"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    from app.vectorstore.store import get_vector_store
    
    try:
        vector_store = get_vector_store()
        doc_count = vector_store.get_document_count()
        
        return {
            "status": "healthy",
            "vector_store": "connected",
            "indexed_chunks": doc_count
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower()
    )
