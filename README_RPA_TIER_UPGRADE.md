# NovaAgent v4.3 – RPA Tier‑A Upgrade

**Generated:** 2025-06-30T02:12:31.345106 UTC

This release integrates the Tier‑B→A upgrade ladder for scripted RPA + GPT bots.

## Included features

| Step | Feature | Implementation |
|------|---------|----------------|
| 1 | Central prompt store | `/prompts/*.yml` + `utils/prompt_store.py` |
| 2 | Secrets & model router | `.env.template` keys + `utils/openai_wrapper.py` |
| 3 | Retry & back‑off wrapper | `utils/openai_wrapper.chat_completion()` |
| 4 | Token watchdog | built into `openai_wrapper` |
| 5 | Memory‑lite vault | `utils/memory_vault.py` (Redis JSON) |
| 6 | Decision matrix agent | `agents/decision_matrix_agent.py` (FastAPI) |
| 7 | Dynamic tool invocation | `utils/tool_registry.py` |
| 8 | Reflex loop | `utils/tool_wrapper.run_tool_call_with_reflex()` |
| 9 | Governance dashboard | Loki + Grafana services in `docker-compose.yml` |

### Tool picks (Barbados‑friendly)

| Need | Lightweight pick (bundled) | Enterprise‑grade (optional) |
|------|---------------------------|-----------------------------|
| Prompt store | Local YAML in Git | **PromptLayer** (global) |
| Token estimator | `tiktoken` | LangChain Cost Tracker |
| Memory vault | Redis (open‑source) | DynamoDB (AWS global) |
| Decision orchestration | FastAPI microservice | Temporal Cloud (no region blocks) |
| Monitoring | Grafana + Loki (self) | Datadog (Caribbean‑accessible) |

## Quick start

```bash
docker compose up -d grafana loki promtail redis
source .venv/bin/activate
uvicorn agents.decision_matrix_agent:app --reload --port 9000
```
