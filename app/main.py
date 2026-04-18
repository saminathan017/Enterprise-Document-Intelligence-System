"""
FastAPI application — v3.0
All tiers wired: hybrid RAG, streaming, documents, knowledge graph,
analytics, feedback, cost tracking, jobs, rate limiting.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings
from app.api import ingest, query, session, evaluate
from app.api import stream, documents, feedback
from app.api.costs import router as costs_router

# Optional rate limiting
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    _limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
    _RATE_LIMIT = True
except ImportError:
    _RATE_LIMIT = False

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Enterprise Document Intelligence API",
    description=(
        "v3.0 — BGE-large embeddings, BM25+dense hybrid RRF, parent-child chunking, "
        "pdfplumber table extraction, DOCX/XLSX/PPTX support, GPT-4o Vision OCR, "
        "CoT prompts, contextual compression, CRAG, NLI faithfulness, LLM-as-judge, "
        "SSE streaming, cost tracking, async ingestion, rate limiting."
    ),
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

if _RATE_LIMIT:
    app.state.limiter = _limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "X-Request-ID"],
)

# ── API routes ────────────────────────────────────────────────────────────────

app.include_router(ingest.router,    prefix="/api/v1", tags=["Ingestion"])
app.include_router(query.router,     prefix="/api/v1", tags=["Query"])
app.include_router(session.router,   prefix="/api/v1", tags=["Session"])
app.include_router(evaluate.router,  prefix="/api/v1", tags=["Evaluation"])
app.include_router(stream.router,    prefix="/api/v1", tags=["Streaming"])
app.include_router(documents.router, prefix="/api/v1", tags=["Documents"])
app.include_router(feedback.router,  prefix="/api/v1", tags=["Feedback"])
app.include_router(costs_router,     prefix="/api/v1", tags=["Costs"])

# ── Job status endpoints ──────────────────────────────────────────────────────

from app.ingestion.pipeline import get_job, list_jobs
from fastapi import APIRouter as _Router

_jobs_router = _Router()

@_jobs_router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"detail": "Job not found"})
    return job

@_jobs_router.get("/jobs")
async def list_all_jobs():
    return {"jobs": list_jobs()}

app.include_router(_jobs_router, prefix="/api/v1", tags=["Jobs"])

# ── Static React SPA ──────────────────────────────────────────────────────────

_STATIC = Path(__file__).parent.parent / "static"
if _STATIC.is_dir():
    app.mount("/assets", StaticFiles(directory=str(_STATIC / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        index = _STATIC / "index.html"
        return FileResponse(str(index)) if index.exists() else JSONResponse(
            status_code=404, content={"detail": "Frontend not built — run: cd frontend && npm run build"}
        )

# ── Health / root ─────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {
        "name":    "Enterprise Document Intelligence API",
        "version": "3.0.0",
        "status":  "operational",
        "docs":    "/api/docs",
        "features": [
            "BGE-large-en-v1.5 embeddings (1024-dim)",
            "BM25 + dense hybrid search with RRF",
            "Parent-child chunking + table preservation",
            "pdfplumber table extraction",
            "DOCX / XLSX / CSV / PPTX support",
            "GPT-4o Vision OCR for scanned PDFs",
            "Chain-of-thought prompting + inline citations",
            "Contextual compression (LLM per-chunk)",
            "CRAG relevance filtering",
            "Lost-in-the-middle context reordering",
            "SSE token streaming with pipeline events",
            "NLI faithfulness (DeBERTa cross-encoder)",
            "LLM-as-judge evaluation",
            "BERTScore generation quality",
            "Per-query cost + token tracking",
            "Async background ingestion",
            "Rate limiting (120 req/min)",
            "Feedback collection (thumbs up/down)",
        ],
    }


@app.get("/health", tags=["Health"])
async def health_check():
    from app.vectorstore.store import get_vector_store
    from app.vectorstore.embeddings import get_embedding_generator
    try:
        vs  = get_vector_store()
        emb = get_embedding_generator()
        return {
            "status":         "healthy",
            "version":        "3.0.0",
            "vector_store":   "connected",
            "indexed_chunks": vs.get_document_count(),
            "embedding_model": emb.model_name,
            "embedding_dim":   emb.get_embedding_dimension(),
            "embedding_cache_size": emb.cache_size,
            "bm25_available": True,
            "rate_limiting":  _RATE_LIMIT,
        }
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(exc)},
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )
