"""
Ingestion pipeline v2 — async background processing with job tracking.

Supports:
  • Sync ingestion (small files, immediate response)
  • Async background jobs (large files, returns job_id)
  • Job status polling via GET /api/v1/jobs/{job_id}
"""

from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from enum import Enum

from app.ingestion.loaders import DocumentLoaderFactory
from app.ingestion.chunker import DocumentChunker
from app.vectorstore.store import VectorStore


# ── Job store (in-process; replace with Redis for multi-worker) ───────────────

class JobStatus(str, Enum):
    PENDING    = "pending"
    PROCESSING = "processing"
    DONE       = "done"
    FAILED     = "failed"


_jobs: Dict[str, Dict[str, Any]] = {}


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    return _jobs.get(job_id)


def list_jobs() -> list:
    return list(_jobs.values())


# ── Pipeline ──────────────────────────────────────────────────────────────────

class IngestionPipeline:
    """Orchestrates document ingestion: load → chunk → embed → index."""

    def __init__(self, vector_store: VectorStore):
        self.vector_store    = vector_store
        self.chunker         = DocumentChunker()
        self.loader_factory  = DocumentLoaderFactory()

    # ── Sync (small files) ────────────────────────────────────────────────────

    def ingest_document(
        self,
        content: bytes,
        filename: str,
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Synchronous ingest — returns result immediately."""
        loader   = self.loader_factory.get_loader(filename)
        doc_data = loader.load(content, filename, metadata)

        doc_id = self._generate_doc_id(content, filename)
        doc_data["metadata"]["document_id"]  = doc_id
        doc_data["metadata"]["ingested_at"]  = datetime.now(timezone.utc).isoformat()
        doc_data["metadata"]["file_size_bytes"] = len(content)

        chunks = self.chunker.chunk_document(
            text=doc_data["text"],
            metadata=doc_data["metadata"],
        )

        if not chunks:
            return {
                "success": False,
                "document_id": doc_id,
                "chunks_created": 0,
                "error": "No text could be extracted from document",
            }

        chunk_ids = self.vector_store.add_documents(chunks)

        return {
            "success":       True,
            "document_id":   doc_id,
            "filename":      filename,
            "chunks_created": len(chunks),
            "chunk_ids":     chunk_ids,
            "metadata":      doc_data["metadata"],
        }

    # ── Async background (large files) ────────────────────────────────────────

    async def ingest_async(
        self,
        content: bytes,
        filename: str,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Kick off background ingestion; return job_id immediately."""
        job_id = self._generate_doc_id(content, filename)
        _jobs[job_id] = {
            "job_id":   job_id,
            "filename": filename,
            "status":   JobStatus.PENDING,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "chunks_created": 0,
            "error":    None,
        }

        asyncio.create_task(self._run_async(job_id, content, filename, metadata))
        return job_id

    async def _run_async(
        self,
        job_id: str,
        content: bytes,
        filename: str,
        metadata: Optional[Dict[str, Any]],
    ) -> None:
        _jobs[job_id]["status"] = JobStatus.PROCESSING
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.ingest_document(content, filename, metadata),
            )
            _jobs[job_id].update({
                "status":         JobStatus.DONE if result["success"] else JobStatus.FAILED,
                "chunks_created": result.get("chunks_created", 0),
                "document_id":    result.get("document_id"),
                "completed_at":   datetime.now(timezone.utc).isoformat(),
                "error":          result.get("error"),
            })
        except Exception as exc:
            _jobs[job_id].update({
                "status": JobStatus.FAILED,
                "error":  str(exc),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            })

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _generate_doc_id(content: bytes, filename: str) -> str:
        h = hashlib.sha256(content).hexdigest()[:16]
        return f"{filename}_{h}"

    def get_document_count(self) -> int:
        return self.vector_store.get_document_count()

    def delete_document(self, document_id: str) -> bool:
        return self.vector_store.delete_by_metadata("document_id", document_id)
