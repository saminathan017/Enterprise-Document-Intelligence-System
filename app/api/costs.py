"""Cost and token usage analytics endpoint."""

from fastapi import APIRouter
from app.core.cost_tracker import get_cost_tracker
import json
from pathlib import Path

router = APIRouter()
COST_LOG = Path("data/cost_log.jsonl")


@router.get("/costs")
async def cost_summary():
    tracker = get_cost_tracker()
    return {"success": True, **tracker.totals}


@router.get("/costs/recent")
async def recent_costs(limit: int = 50):
    if not COST_LOG.exists():
        return {"records": []}
    records = []
    with open(COST_LOG) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return {"records": list(reversed(records[-limit:]))}
