test:
	pytest --cov=nova --cov-fail-under=95

package:
	zip -r nova-agent-v6.6-stage1-full.zip .

run-api:
	uvicorn nova.api.app:app --port 8000 --reload

loadtest:
	k6 run tests/load_test.js

chaos-run:
	python scripts/chaos_runner.py

# --- Developer friendly targets (non-breaking) ---
bootstrap:
	bash scripts/bootstrap.sh

lint:
	pre-commit run ruff --all-files || true
	pre-commit run black --all-files || true

format:
	pre-commit run black --all-files || true
	pre-commit run ruff --all-files || true

test-quick:
	pytest -q

smoke:
	bash scripts/test-smoke.sh

run-api-dev:
	bash scripts/run-api-dev.sh

install-core:
	. .venv/bin/activate 2>/dev/null || true; pip install -r requirements-core.txt -r requirements-dev.txt

install-all:
	. .venv/bin/activate 2>/dev/null || true; pip install -r requirements.txt -r requirements-dev.txt
