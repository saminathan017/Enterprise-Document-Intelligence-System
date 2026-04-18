"""
Feedback API — collect thumbs-up / thumbs-down ratings per message.

Ratings are appended as JSONL to data/feedback.jsonl for:
  • Model fine-tuning ground truth
  • Offline evaluation calibration
  • UX quality monitoring
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

FEEDBACK_FILE = Path("data/feedback.jsonl")


class FeedbackRequest(BaseModel):
    session_id: str
    message_id: str
    query: str
    answer: str
    rating: int          # +1 thumbs-up  /  -1 thumbs-down
    comment: Optional[str] = None
    model: Optional[str] = None
    processing_ms: Optional[int] = None


class FeedbackSummary(BaseModel):
    total: int
    positive: int
    negative: int
    positive_rate: float


@router.post("/feedback")
async def submit_feedback(req: FeedbackRequest):
    """Append a single feedback record to the JSONL store."""
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "session_id":    req.session_id,
        "message_id":    req.message_id,
        "query":         req.query,
        "answer":        req.answer[:500],   # truncate for storage efficiency
        "rating":        req.rating,
        "comment":       req.comment,
        "model":         req.model,
        "processing_ms": req.processing_ms,
        "timestamp":     datetime.now(timezone.utc).isoformat(),
    }

    with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return {"success": True, "recorded": record["timestamp"]}


@router.get("/feedback/summary")
async def feedback_summary() -> FeedbackSummary:
    """Return aggregate positive/negative counts."""
    if not FEEDBACK_FILE.exists():
        return FeedbackSummary(total=0, positive=0, negative=0, positive_rate=0.0)

    total = positive = negative = 0
    with open(FEEDBACK_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                total += 1
                if rec.get("rating", 0) > 0:
                    positive += 1
                else:
                    negative += 1
            except json.JSONDecodeError:
                continue

    rate = positive / total if total > 0 else 0.0
    return FeedbackSummary(
        total=total,
        positive=positive,
        negative=negative,
        positive_rate=round(rate, 4),
    )


@router.get("/feedback/recent")
async def recent_feedback(limit: int = 20):
    """Return the most recent N feedback records."""
    if not FEEDBACK_FILE.exists():
        return {"records": []}

    records = []
    with open(FEEDBACK_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    # Return newest first
    return {"records": list(reversed(records[-limit:]))}
