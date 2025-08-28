#!/usr/bin/env bash
set -euo pipefail

# Activate venv if present
if [ -d .venv ]; then
  . .venv/bin/activate
elif [ -d venv ]; then
  . venv/bin/activate
fi

# Run a lightweight but representative subset (falls back to all tests if patterns not found)
PATTERNS=(
  tests/test_metrics_endpoint.py
  tests/test_task_manager_load.py
  tests/test_ws_echo.py
)

FOUND=0
for p in "${PATTERNS[@]}"; do
  if [ -f "$p" ]; then
    FOUND=1
  fi
done

if [ "$FOUND" = "1" ]; then
  echo "[smoke] Running targeted smoke tests..."
  python -m pytest -q -c /dev/null "${PATTERNS[@]}"
else
  echo "[smoke] Patterns not found; running quick default test run."
  python -m pytest -q -c /dev/null -k "not jwt"
fi
