"""
Advanced chunking: parent-child (small-to-big) + table-aware preservation.

Strategy:
  - CHILD chunks (400 chars / 80 overlap) — used for precise vector retrieval
  - PARENT chunks (1200 chars / 200 overlap) — stored for generation context
  - Tables detected as atomic units — never split mid-table
  - Each child carries parent_id so retrieval can expand to full parent context
"""

from __future__ import annotations

import re
from typing import List, Dict, Any, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import settings


# ── Table detection ───────────────────────────────────────────────────────────

_TABLE_LINE_RE = re.compile(r"(\|.*\||\+[-+]+\+)")  # markdown + box tables

def _split_tables(text: str) -> List[Tuple[str, bool]]:
    """
    Split text into segments, tagging each as (text, is_table).
    Table blocks are kept atomic so the chunker never splits mid-table.
    """
    segments: List[Tuple[str, bool]] = []
    lines = text.splitlines(keepends=True)
    buf: List[str] = []
    in_table = False

    for line in lines:
        is_table_line = bool(_TABLE_LINE_RE.match(line.rstrip()))
        if is_table_line and not in_table:
            if buf:
                segments.append(("".join(buf), False))
                buf = []
            in_table = True
            buf.append(line)
        elif not is_table_line and in_table:
            segments.append(("".join(buf), True))
            buf = [line]
            in_table = False
        else:
            buf.append(line)

    if buf:
        segments.append(("".join(buf), in_table))

    return segments


# ── Splitter factory ──────────────────────────────────────────────────────────

_SEPARATORS = ["\n\n\n", "\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]

def _make_splitter(chunk_size: int, chunk_overlap: int) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=_SEPARATORS,
    )


# ── DocumentChunker ────────────────────────────────────────────────────────────

class DocumentChunker:
    """
    Parent-child chunker with table preservation.

    child_size  → used for retrieval (small, precise)
    parent_size → used for generation context (large, coherent)
    """

    CHILD_SIZE    = 400
    CHILD_OVERLAP = 80
    PARENT_SIZE   = 1200
    PARENT_OVERLAP = 200

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ):
        # Respect legacy config values if explicitly set
        self._legacy_size    = chunk_size    or settings.chunk_size
        self._legacy_overlap = chunk_overlap or settings.chunk_overlap

        self._child_splitter  = _make_splitter(self.CHILD_SIZE, self.CHILD_OVERLAP)
        self._parent_splitter = _make_splitter(self.PARENT_SIZE, self.PARENT_OVERLAP)

    # ── Public API ────────────────────────────────────────────────────────────

    def chunk_document(
        self,
        text: str,
        metadata: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Return a flat list of CHILD chunks, each carrying:
          - parent_text   : the larger context window
          - parent_id     : shared across siblings from the same parent
          - chunk_type    : 'child'
          - is_table      : True if chunk is an atomic table block
        """
        if not text or not text.strip():
            return []

        source = metadata.get("source", "unknown")
        doc_id = metadata.get("document_id", source)

        segments = _split_tables(text)
        child_chunks: List[Dict[str, Any]] = []

        for seg_text, is_table in segments:
            if not seg_text.strip():
                continue

            if is_table:
                # Tables are atomic — emit as a single child with itself as parent
                parent_id = f"{doc_id}_table_{len(child_chunks)}"
                child_chunks.append(
                    self._make_chunk(
                        text=seg_text,
                        parent_text=seg_text,
                        parent_id=parent_id,
                        metadata=metadata,
                        idx=len(child_chunks),
                        is_table=True,
                    )
                )
            else:
                # Split regular text into parents then children
                parents = self._parent_splitter.split_text(seg_text)
                for p_idx, parent_text in enumerate(parents):
                    parent_id = f"{doc_id}_parent_{len(child_chunks)}_{p_idx}"
                    children = self._child_splitter.split_text(parent_text)
                    for child_text in children:
                        if not child_text.strip():
                            continue
                        child_chunks.append(
                            self._make_chunk(
                                text=child_text,
                                parent_text=parent_text,
                                parent_id=parent_id,
                                metadata=metadata,
                                idx=len(child_chunks),
                                is_table=False,
                            )
                        )

        # Back-fill total_chunks
        total = len(child_chunks)
        for c in child_chunks:
            c["metadata"]["total_chunks"] = total

        return child_chunks

    def chunk_batch(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        all_chunks: List[Dict[str, Any]] = []
        for doc in documents:
            all_chunks.extend(self.chunk_document(doc["text"], doc["metadata"]))
        return all_chunks

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _make_chunk(
        text: str,
        parent_text: str,
        parent_id: str,
        metadata: Dict[str, Any],
        idx: int,
        is_table: bool,
    ) -> Dict[str, Any]:
        source = metadata.get("source", "unknown")
        chunk_id = f"{source}_chunk_{idx}"
        return {
            "text": text,
            "metadata": {
                **metadata,
                "chunk_index": idx,
                "chunk_id": chunk_id,
                "parent_id": parent_id,
                "parent_text": parent_text,
                "chunk_type": "table" if is_table else "child",
                "is_table": is_table,
                "total_chunks": 0,  # filled after all chunks collected
            },
        }
