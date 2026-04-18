"""
Document management API — list, delete, and knowledge-graph extraction.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import json

from openai import OpenAI

from app.config import settings
from app.vectorstore.store import get_vector_store

router = APIRouter()


# ── Document listing ──────────────────────────────────────────────────────────

@router.get("/documents")
async def list_documents():
    """Return deduplicated list of ingested documents with metadata."""
    try:
        vector_store = get_vector_store()
        result = vector_store.collection.get(include=["metadatas"])

        seen: dict = {}
        for meta in result["metadatas"]:
            src = meta.get("source", "unknown")
            if src not in seen:
                seen[src] = {
                    "source": src,
                    "document_id": meta.get("document_id", src),
                    "file_type": meta.get("file_type", "unknown"),
                    "total_chunks": 0,
                    "ingested_at": meta.get("ingested_at", ""),
                    "file_size_bytes": meta.get("file_size_bytes", 0),
                }
            seen[src]["total_chunks"] += 1

        return {
            "success": True,
            "documents": list(seen.values()),
            "total": len(seen)
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Remove all chunks for a document from the vector store."""
    try:
        vector_store = get_vector_store()
        result = vector_store.collection.get(
            where={"document_id": document_id},
            include=["metadatas"]
        )
        ids_to_delete = result.get("ids", [])

        if not ids_to_delete:
            # Try by source name
            result2 = vector_store.collection.get(
                where={"source": document_id},
                include=["metadatas"]
            )
            ids_to_delete = result2.get("ids", [])

        if not ids_to_delete:
            raise HTTPException(status_code=404, detail="Document not found")

        vector_store.collection.delete(ids=ids_to_delete)

        return {"success": True, "deleted_chunks": len(ids_to_delete)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Knowledge Graph ───────────────────────────────────────────────────────────

class KGParams(BaseModel):
    max_docs: Optional[int] = 30
    session_id: Optional[str] = None


@router.post("/knowledge-graph")
async def build_knowledge_graph(params: KGParams):
    """
    Extract entities and relationships from the vector store using GPT-4o-mini
    and return a graph payload for cytoscape.js.
    """
    try:
        vector_store = get_vector_store()
        result = vector_store.collection.get(include=["documents", "metadatas"])

        docs = list(zip(result["documents"], result["metadatas"]))[:params.max_docs]

        if not docs:
            return {"nodes": [], "edges": []}

        # Sample unique sources for representative coverage
        from collections import defaultdict
        by_source: dict = defaultdict(list)
        for text, meta in docs:
            by_source[meta.get("source", "unknown")].append(text)

        node_map: dict = {}
        edges: list = []
        node_id_counter = 0

        client = OpenAI(api_key=settings.openai_api_key)

        def get_or_create_node(label: str, node_type: str) -> str:
            key = label.lower().strip()
            if key not in node_map:
                nonlocal node_id_counter
                node_id_counter += 1
                nid = f"n{node_id_counter}"
                node_map[key] = {
                    "id": nid,
                    "label": label,
                    "type": node_type,
                    "sources": []
                }
            return node_map[key]["id"]

        for source, texts in list(by_source.items())[:10]:
            sample_text = " ".join(texts[:2])[:600]

            try:
                resp = client.chat.completions.create(
                    model=settings.helper_model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Extract the most important entities and relationships from the text. "
                                "Return ONLY valid JSON with this exact structure: "
                                '{"entities": [{"label": "...", "type": "person|organization|metric|concept|date|location"}], '
                                '"relationships": [{"source": "entity_label", "target": "entity_label", "label": "relationship"}]}'
                            )
                        },
                        {"role": "user", "content": f"Text: {sample_text}"}
                    ],
                    max_tokens=400,
                    temperature=0.0
                )
                raw = resp.choices[0].message.content.strip()
                # Strip markdown code fences if present
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                data = json.loads(raw)
            except Exception:
                continue

            for ent in data.get("entities", []):
                nid = get_or_create_node(ent.get("label", ""), ent.get("type", "concept"))
                if source not in node_map[ent["label"].lower().strip()].get("sources", []):
                    node_map[ent["label"].lower().strip()].setdefault("sources", []).append(source)

            for rel in data.get("relationships", []):
                src_label = rel.get("source", "")
                tgt_label = rel.get("target", "")
                if not src_label or not tgt_label:
                    continue
                src_key = src_label.lower().strip()
                tgt_key = tgt_label.lower().strip()
                if src_key not in node_map or tgt_key not in node_map:
                    continue
                edges.append({
                    "id": f"e{len(edges)+1}",
                    "source": node_map[src_key]["id"],
                    "target": node_map[tgt_key]["id"],
                    "label": rel.get("label", "related_to")
                })

        return {
            "nodes": list(node_map.values()),
            "edges": edges
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Analytics Summary ─────────────────────────────────────────────────────────

@router.get("/analytics")
async def get_analytics():
    """Return real-time analytics from session files and vector store."""
    import os
    from pathlib import Path
    from datetime import datetime

    try:
        vector_store = get_vector_store()
        chunk_count = vector_store.get_document_count()

        result = vector_store.collection.get(include=["metadatas"])
        unique_docs = len({m.get("source") for m in result["metadatas"]})

        sessions_dir = settings.session_persist_dir
        session_stats: list = []
        query_times: list = []
        total_queries = 0

        if os.path.isdir(sessions_dir):
            for fname in os.listdir(sessions_dir):
                if not fname.endswith(".json"):
                    continue
                try:
                    with open(os.path.join(sessions_dir, fname)) as f:
                        s = json.load(f)
                    cnt = s.get("message_count", 0)
                    total_queries += cnt
                    session_stats.append({
                        "session_id": s.get("session_id", fname),
                        "message_count": cnt,
                        "created_at": s.get("created_at", ""),
                        "last_activity": s.get("last_activity", "")
                    })
                except Exception:
                    continue

        # Sort most-recent first
        session_stats.sort(key=lambda x: x.get("last_activity", ""), reverse=True)

        return {
            "total_chunks": chunk_count,
            "unique_documents": unique_docs,
            "total_sessions": len(session_stats),
            "total_queries": total_queries,
            "sessions": session_stats[:20],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Sessions management ────────────────────────────────────────────────────────

@router.get("/sessions/list")
async def list_sessions():
    """List all sessions with metadata."""
    import os
    import json as _json
    sessions = []
    sdir = settings.session_persist_dir
    if not os.path.isdir(sdir):
        return {"sessions": []}
    for fname in sorted(os.listdir(sdir), reverse=True):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(sdir, fname)) as f:
                s = _json.load(f)
            sessions.append({
                "session_id": s.get("session_id", fname.replace(".json", "")),
                "message_count": s.get("message_count", 0),
                "created_at": s.get("created_at", ""),
                "last_activity": s.get("last_activity", ""),
                "title": _derive_title(s)
            })
        except Exception:
            continue
    return {"sessions": sessions}


def _derive_title(session: dict) -> str:
    """Derive a human-readable title from first user message."""
    history = session.get("history", [])
    for msg in history:
        if msg.get("role") == "human":
            content = msg.get("content", "")
            return content[:60] + ("..." if len(content) > 60 else "")
    return "New conversation"


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session file."""
    import os
    path = os.path.join(settings.session_persist_dir, f"{session_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Session not found")
    os.remove(path)
    return {"success": True}
