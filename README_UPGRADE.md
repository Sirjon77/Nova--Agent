
# Nova Agent – Upgrade Patch

This patch adds production‑readiness essentials:

1. **Environment template** – `.env.example`
2. **Bootstrap helper** – `bootstrap.sh`
3. **Continuous Integration** – GitHub workflow (.github/workflows/ci.yml)
4. **Task queue & rate‑limit guard** – `celeryconfig.py`, `rate_limit.py`
5. **Memory hygiene** – `memory_guard.py` + daily schedule
6. **Container health checks** – updated Dockerfile & docker‑compose override
7. **Observability starter** – Prometheus & Grafana configs
8. **Finance layer scaffold** – `payments/stripe_webhook.py`

## How to apply

```bash
# Inside the root of your NovaAgent_v4.4 repo
unzip nova_upgrade_package.zip -d .
cp .env.example .env  # then edit
./bootstrap.sh        # set up deps
```

Commit each section in order (CI first, then queue, etc.) for easier rollbacks.
