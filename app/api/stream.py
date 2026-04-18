"""
SSE streaming endpoint v2 — full advanced pipeline:
  HyDE → hybrid BM25+dense retrieval → CRAG filter → parent expansion
  → lost-in-the-middle reorder → contextual compression → CoT generation
  → NLI faithfulness scoring → cost tracking → session persistence
"""

from __future__ import annotations

import json
import logging
import time
from typing import AsyncGenerator, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from openai import AsyncOpenAI

from app.config import settings
from app.vectorstore.store import get_vector_store
from app.vectorstore.retrieval import Retriever
from app.rag.prompts import SYSTEM_PROMPT, RAG_PROMPT_TEMPLATE, HYDE_PROMPT
from app.rag.chain import _reorder_lost_in_middle, _format_context, _extract_citations
from app.memory.session_manager import get_session_manager
from app.memory.conversation_memory import ConversationMemory
from app.core.cost_tracker import get_cost_tracker

logger = logging.getLogger(__name__)
router = APIRouter()


class StreamQueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    top_k: int = 5
    model: Optional[str] = None
    use_hyde: bool = True
    use_crag: bool = True
    use_compression: bool = False  # off by default — adds latency
    expand_parents: bool = True


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


async def _stream_response(req: StreamQueryRequest) -> AsyncGenerator[str, None]:
    start = time.time()
    model = req.model or settings.llm_model
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    try:
        # ── Step 1: HyDE (optional) ──────────────────────────────────────────
        retrieval_query = req.query

        if req.use_hyde:
            yield _sse({"type": "step", "step": "hyde", "status": "running",
                        "message": "Generating hypothetical document…"})
            try:
                hyp = await client.chat.completions.create(
                    model=settings.helper_model,
                    messages=[
                        {"role": "system", "content": "Write a concise, factual document that would perfectly answer the question."},
                        {"role": "user", "content": HYDE_PROMPT.format(query=req.query)},
                    ],
                    max_tokens=300,
                    temperature=0.0,
                )
                retrieval_query = hyp.choices[0].message.content or req.query
                yield _sse({"type": "step", "step": "hyde", "status": "done",
                            "elapsed_ms": int((time.time() - start) * 1000)})
            except Exception as e:
                logger.warning("HyDE failed, falling back to original query: %s", e)
                yield _sse({"type": "step", "step": "hyde", "status": "skipped",
                            "message": "HyDE unavailable, using original query"})

        # ── Step 2: Hybrid retrieval (BM25 + dense via store.query) ──────────
        yield _sse({"type": "step", "step": "retrieval", "status": "running",
                    "message": "Hybrid BM25 + dense search…",
                    "elapsed_ms": int((time.time() - start) * 1000)})

        vector_store = get_vector_store()
        retriever = Retriever(vector_store)

        # Over-fetch then deduplicate when HyDE is active
        if req.use_hyde and retrieval_query != req.query:
            docs_hyp  = retriever.retrieve_with_scores(retrieval_query, req.top_k)
            docs_orig = retriever.retrieve_with_scores(req.query, req.top_k)
            seen: set = set()
            docs: list = []
            for d in docs_orig + docs_hyp:
                if d["id"] not in seen:
                    seen.add(d["id"])
                    docs.append(d)
            docs = sorted(docs, key=lambda x: x["score"], reverse=True)[: req.top_k]
        else:
            docs = retriever.retrieve_with_scores(req.query, req.top_k)

        retrieval_ms = int((time.time() - start) * 1000)
        yield _sse({"type": "step", "step": "retrieval", "status": "done",
                    "count": len(docs), "elapsed_ms": retrieval_ms})

        if not docs:
            yield _sse({"type": "error", "message": "No relevant documents found in knowledge base."})
            yield _sse({"type": "done", "elapsed_ms": retrieval_ms})
            return

        # ── Step 3: CRAG quality filter ───────────────────────────────────────
        if req.use_crag:
            yield _sse({"type": "step", "step": "crag", "status": "running",
                        "message": "Scoring document relevance…"})
            try:
                from app.rag.crag import CRAGFilter
                docs, needs_web = await _run_sync(CRAGFilter().filter, req.query, docs)
                if needs_web:
                    yield _sse({"type": "step", "step": "crag", "status": "done",
                                "message": "Low-relevance docs filtered; web fallback suggested"})
                else:
                    yield _sse({"type": "step", "step": "crag", "status": "done",
                                "count": len(docs)})
            except Exception as e:
                logger.warning("CRAG filter failed: %s", e)
                yield _sse({"type": "step", "step": "crag", "status": "skipped"})

        # ── Step 4: Parent-context expansion ──────────────────────────────────
        if req.expand_parents:
            yield _sse({"type": "step", "step": "context", "status": "running",
                        "message": "Expanding to parent chunks…"})
            try:
                docs = vector_store.expand_to_parents(docs)
            except Exception as e:
                logger.warning("Parent expansion failed: %s", e)
            yield _sse({"type": "step", "step": "context", "status": "done",
                        "count": len(docs)})

        # ── Step 5: Lost-in-the-middle reorder ────────────────────────────────
        docs = _reorder_lost_in_middle(docs)

        # ── Step 6: Contextual compression (optional, latency-heavy) ──────────
        if req.use_compression:
            yield _sse({"type": "step", "step": "compression", "status": "running",
                        "message": "Compressing context chunks…"})
            try:
                from app.rag.contextual_compression import ContextualCompressor
                docs = await _run_sync(ContextualCompressor().compress, req.query, docs)
                yield _sse({"type": "step", "step": "compression", "status": "done",
                            "count": len(docs)})
            except Exception as e:
                logger.warning("Compression failed: %s", e)
                yield _sse({"type": "step", "step": "compression", "status": "skipped"})

        # ── Step 7: Session history ────────────────────────────────────────────
        history_messages: list = []
        conv = None
        session_mgr = None
        if req.session_id:
            try:
                session_mgr = get_session_manager()
                conv = ConversationMemory(req.session_id, session_mgr)
                history_messages = [
                    {"role": m["role"], "content": m["content"]}
                    for m in conv.get_history()[-6:]
                ]
            except Exception as e:
                logger.warning("Session load failed: %s", e)

        # ── Step 8: CoT generation (streaming) ────────────────────────────────
        context     = _format_context(docs)
        user_prompt = RAG_PROMPT_TEMPLATE.format(context=context, query=req.query)
        messages    = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history_messages,
            {"role": "user", "content": user_prompt},
        ]

        gen_start = time.time()
        yield _sse({"type": "step", "step": "generation", "status": "running",
                    "message": f"Generating with {model}…",
                    "elapsed_ms": int((time.time() - start) * 1000)})

        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            max_tokens=settings.max_tokens,
            temperature=settings.llm_temperature,
        )

        full_response = ""
        token_count   = 0
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                full_response += delta.content
                token_count   += 1
                yield _sse({"type": "token", "content": delta.content})

        gen_ms = int((time.time() - gen_start) * 1000)
        yield _sse({"type": "step", "step": "generation", "status": "done",
                    "tokens": token_count, "elapsed_ms": gen_ms})

        # ── Step 9: Citations ──────────────────────────────────────────────────
        citations = _extract_citations(docs)
        yield _sse({
            "type": "citations",
            "citations": [
                {
                    "source":   c.source,
                    "chunk_id": c.chunk_id,
                    "score":    round(c.score, 4),
                    "excerpt":  c.excerpt,
                }
                for c in citations
            ],
        })

        # ── Step 10: NLI faithfulness (async, non-blocking) ───────────────────
        total_ms = int((time.time() - start) * 1000)
        try:
            from app.evaluation.metrics import faithfulness_nli
            faith_score = faithfulness_nli(full_response, context)
            yield _sse({"type": "metrics", "faithfulness": round(faith_score, 3),
                        "processing_ms": total_ms})
        except Exception:
            pass

        # ── Step 11: Cost tracking ─────────────────────────────────────────────
        try:
            get_cost_tracker().record(
                model=model,
                prompt_text=user_prompt,
                completion_text=full_response,
                operation="stream_query",
            )
        except Exception as e:
            logger.debug("Cost tracking error: %s", e)

        # ── Step 12: Persist session ───────────────────────────────────────────
        if req.session_id and conv and session_mgr:
            try:
                conv.add_user_message(req.query)
                conv.add_ai_message(full_response)
                session_mgr.update_session(
                    session_id=req.session_id,
                    history=conv.get_history(),
                    increment_count=True,
                )
            except Exception as e:
                logger.warning("Session persist failed: %s", e)

        yield _sse({"type": "done", "total_tokens": token_count,
                    "elapsed_ms": total_ms, "docs_used": len(docs)})

    except Exception as exc:
        logger.exception("Stream pipeline error")
        yield _sse({"type": "error", "message": str(exc)})
        yield _sse({"type": "done", "elapsed_ms": int((time.time() - start) * 1000)})


async def _run_sync(fn, *args):
    """Run a synchronous function in the default executor without blocking the event loop."""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, fn, *args)


@router.post("/stream/query")
async def stream_query(request: StreamQueryRequest):
    """SSE endpoint: full advanced RAG pipeline with real-time token streaming."""
    return StreamingResponse(
        _stream_response(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":       "keep-alive",
        },
    )
