"""
Token cost tracker — counts tokens per query and accumulates totals.
Uses tiktoken for accurate OpenAI token counting.
Stores a rolling log in data/cost_log.jsonl.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

# Pricing per 1M tokens (USD) as of mid-2025
_PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4o":              {"input": 5.0,   "output": 15.0},
    "gpt-4o-mini":         {"input": 0.15,  "output": 0.60},
    "gpt-4-turbo-preview": {"input": 10.0,  "output": 30.0},
    "gpt-4":               {"input": 30.0,  "output": 60.0},
    "gpt-3.5-turbo":       {"input": 0.50,  "output": 1.50},
}
_DEFAULT_PRICING = {"input": 5.0, "output": 15.0}

COST_LOG = Path("data/cost_log.jsonl")

try:
    import tiktoken
    _TIKTOKEN = True
except ImportError:
    _TIKTOKEN = False


def _count_tokens(text: str, model: str) -> int:
    if not _TIKTOKEN:
        return len(text.split()) * 4 // 3   # rough fallback: ~1.33 tokens/word
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


class CostTracker:
    """
    Per-query and aggregate token / cost tracking.

    Usage:
        tracker = get_cost_tracker()
        entry = tracker.record(model, prompt_text, completion_text)
        print(entry)  # {'input_tokens': ..., 'output_tokens': ..., 'cost_usd': ...}
    """

    def __init__(self):
        self._total_input  = 0
        self._total_output = 0
        self._total_cost   = 0.0
        self._by_model: Dict[str, Dict] = defaultdict(lambda: {"input": 0, "output": 0, "cost": 0.0})
        COST_LOG.parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        model: str,
        prompt_text: str = "",
        completion_text: str = "",
        session_id: Optional[str] = None,
        operation: Optional[str] = None,
        # legacy aliases
        prompt: str = "",
        completion: str = "",
    ) -> Dict:
        # support both old (prompt/completion) and new (prompt_text/completion_text) keyword names
        _prompt     = prompt_text or prompt
        _completion = completion_text or completion
        pricing = _PRICING.get(model, _DEFAULT_PRICING)
        n_in  = _count_tokens(_prompt,     model)
        n_out = _count_tokens(_completion, model)
        cost  = (n_in * pricing["input"] + n_out * pricing["output"]) / 1_000_000

        self._total_input  += n_in
        self._total_output += n_out
        self._total_cost   += cost
        self._by_model[model]["input"]  += n_in
        self._by_model[model]["output"] += n_out
        self._by_model[model]["cost"]   += cost

        entry = {
            "timestamp":     datetime.now(timezone.utc).isoformat(),
            "model":         model,
            "session_id":    session_id,
            "operation":     operation,
            "input_tokens":  n_in,
            "output_tokens": n_out,
            "cost_usd":      round(cost, 6),
        }
        try:
            with open(COST_LOG, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except OSError:
            pass

        return entry

    @property
    def totals(self) -> Dict:
        return {
            "total_input_tokens":  self._total_input,
            "total_output_tokens": self._total_output,
            "total_cost_usd":      round(self._total_cost, 6),
            "by_model":            dict(self._by_model),
        }


_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    global _tracker
    if _tracker is None:
        _tracker = CostTracker()
    return _tracker
