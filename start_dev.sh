#!/usr/bin/env bash
# ── Enterprise AI Analyst — Development Startup ──────────────────────────────
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
FRONTEND="$ROOT/frontend"

# ── Python backend ────────────────────────────────────────────────────────────
if [ ! -d "$ROOT/venv" ]; then
  echo "⟳  Creating Python virtual environment…"
  python3 -m venv "$ROOT/venv"
fi

source "$ROOT/venv/bin/activate"
echo "⟳  Installing/upgrading Python dependencies…"
pip install -q -r "$ROOT/requirements.txt"

# ── Frontend dependencies ──────────────────────────────────────────────────────
if [ ! -d "$FRONTEND/node_modules" ]; then
  echo "⟳  Installing frontend dependencies (npm ci)…"
  cd "$FRONTEND" && npm install && cd "$ROOT"
fi

# ── Launch ─────────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Enterprise AI Analyst  v2.0"
echo "  Backend  → http://localhost:8000"
echo "  Frontend → http://localhost:3000"
echo "  API Docs → http://localhost:8000/api/docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start backend in background
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start frontend dev server
cd "$FRONTEND" && npm run dev &
FRONTEND_PID=$!

# Trap Ctrl+C and kill both
trap "echo ''; echo 'Shutting down…'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM

wait
