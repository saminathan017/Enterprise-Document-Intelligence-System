#!/usr/bin/env bash
# ── Enterprise AI Analyst — Production Build + Serve ─────────────────────────
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
FRONTEND="$ROOT/frontend"

echo "⟳  Building React frontend…"
cd "$FRONTEND"
npm install
npm run build
cd "$ROOT"

echo "⟳  Starting production server on :8000…"
echo "   Visit → http://localhost:8000"
source "$ROOT/venv/bin/activate" 2>/dev/null || true
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
