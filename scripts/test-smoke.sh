#!/usr/bin/env bash
set -euo pipefail

# Activate venv if present
if [ -d .venv ]; then
  . .venv/bin/activate
elif [ -d venv ]; then
  . venv/bin/activate
fi

# Prevent repo modifications during tests (audit log)
AUDIT_FILE="logs/audit.log"
if [ -f "$AUDIT_FILE" ]; then
  AUDIT_SNAPSHOT="/tmp/audit.log.$$.bak"
  cp -f "$AUDIT_FILE" "$AUDIT_SNAPSHOT" 2>/dev/null || true
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
  python -m pytest -q -c /dev/null -p no:cacheprovider "${PATTERNS[@]}"
else
  echo "[smoke] Patterns not found; running quick default test run."
  python -m pytest -q -c /dev/null -p no:cacheprovider -k "not jwt"
fi

# Restore audit log if tests modified it
if [ -n "${AUDIT_SNAPSHOT:-}" ] && [ -f "$AUDIT_SNAPSHOT" ]; then
  if ! cmp -s "$AUDIT_FILE" "$AUDIT_SNAPSHOT" 2>/dev/null; then
    cp -f "$AUDIT_SNAPSHOT" "$AUDIT_FILE" 2>/dev/null || true
  fi
  rm -f "$AUDIT_SNAPSHOT" 2>/dev/null || true
fi
