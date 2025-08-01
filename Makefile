test:
	pytest --cov=nova --cov-fail-under=95
package:
	zip -r nova-agent-v6.6-stage1-full.zip .
\nrun-api:\n\tuvicorn nova.api.app:app --port 8000 --reload\n\nloadtest:\n\tk6 run tests/load_test.js\n
chaos-run:
	python scripts/chaos_runner.py
