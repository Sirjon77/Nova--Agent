#!/usr/bin/env bash
set -euo pipefail

# Load dev env if present, otherwise minimal sane defaults for local run
if [ -f .env.dev ]; then
  export $(grep -v '^#' .env.dev | xargs -0 echo 2>/dev/null || true)
fi

# Minimal defaults to satisfy env validator (override by setting in shell/.env.dev)
export JWT_SECRET_KEY=${JWT_SECRET_KEY:-"Dev-Secret-Key-This-Is-At-Least-32-CHARS-1!"}
export NOVA_ADMIN_USERNAME=${NOVA_ADMIN_USERNAME:-admin}
export NOVA_ADMIN_PASSWORD=${NOVA_ADMIN_PASSWORD:-admin123!Strong}
export OPENAI_API_KEY=${OPENAI_API_KEY:-"sk-dev-placeholder-1234"}
export REDIS_URL=${REDIS_URL:-"redis://localhost:6379"}
export WEAVIATE_URL=${WEAVIATE_URL:-"http://localhost:8080"}

# Prefer venv if present
if [ -d .venv ]; then
  . .venv/bin/activate
elif [ -d venv ]; then
  . venv/bin/activate
fi

exec uvicorn nova.api.app:app --host 0.0.0.0 --port 8000 --reload

