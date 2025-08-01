# Nova Agent v4.4 (Tier A +)
Generated: 2025-06-30T03:02:25.077110Z

This build implements the complete 8‑rung improvement ladder:
1. Session cookie
2. Redis rolling buffer
3. Transient summariser
4. Vector memory (Weaviate/Chroma)
5. “Should‑we‑remember?” heuristic
6. Mini‑tool JSON functions
7. Proactive FAQ suggestions
8. Human hand‑off to Slack/Zendesk

## Quick start (local)

```bash
cp .env.example .env   # then fill secrets
docker compose up --build
open http://localhost:8000/docs
```

See comments in each file for integration points.
