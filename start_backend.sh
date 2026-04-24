#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/backend"
export DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///./planner.db}"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
