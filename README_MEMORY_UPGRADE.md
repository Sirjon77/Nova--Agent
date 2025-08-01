# NovaAgent v4.1 – Memory Upgrade

**Generated:** 2025-06-29T23:41:29.353063 UTC

This patch adds:

1. **Session persistence** (`models/session.py`)
2. **Short‑term context with Redis** (`utils/memory_router.py`)
3. **Long‑term vector recall with Weaviate** (same router)
4. **`/api/chat` FastAPI endpoint** (`routes/chat.py`) – website widget ready
5. **Frontend helper** (`frontend/chatWidget.js`) – auto‑generates `session_id`
6. Redis service in `docker-compose.yml`
7. **Health test** (`tests/test_memory_loop.py`)

## Quick start

```bash
docker compose up -d redis
poetry install  # or pip install -r requirements.txt
uvicorn main:app --reload
# open frontend and chat – memory now sticks
```

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `REDIS_HOST` | `localhost` | Short‑term store |
| `REDIS_PORT` | `6379` | Short‑term store |
| `WEAVIATE_URL` | `http://localhost:8080` | Vector memory |

---
