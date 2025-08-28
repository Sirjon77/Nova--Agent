#!/usr/bin/env bash
set -euo pipefail

PY=${PY:-python3}
VENV_DIR=${VENV_DIR:-.venv}
FULL_INSTALL=${FULL_INSTALL:-0}

echo "[bootstrap] Creating virtual environment at ${VENV_DIR} (if missing)"
if [ ! -d "${VENV_DIR}" ]; then
  ${PY} -m venv "${VENV_DIR}"
fi

echo "[bootstrap] Activating virtual environment"
. "${VENV_DIR}/bin/activate"

echo "[bootstrap] Upgrading pip"
python -m pip install --upgrade pip

if [ "$FULL_INSTALL" = "1" ]; then
  echo "[bootstrap] Installing FULL runtime requirements"
  pip install -r requirements.txt
else
  echo "[bootstrap] Installing CORE runtime requirements (set FULL_INSTALL=1 for full)"
  pip install -r requirements-core.txt
fi

if [ -f requirements-dev.txt ]; then
  echo "[bootstrap] Installing dev requirements"
  pip install -r requirements-dev.txt
fi

if command -v pre-commit >/dev/null 2>&1; then
  echo "[bootstrap] Installing git hooks via pre-commit"
  pre-commit install --hook-type pre-commit --hook-type pre-push || true
fi

echo "[bootstrap] Done. Activate with: source ${VENV_DIR}/bin/activate"
