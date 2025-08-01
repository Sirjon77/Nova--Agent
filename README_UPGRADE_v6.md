
# Nova Agent Upgrade v6 – Safety, Secrets & Analytics

Date: 2025-07-01

## What’s new
* **Global safety wrapper** – `core.safe_run.safe_run` decorator reports errors to Sentry and prevents worker crashes.
* **Secret loader** – optional HashiCorp Vault integration via `core.secret_loader`.
* **Analytics micro‑service** – new `nova-analytics` container for KPI aggregation.
* Docker Compose updated to include the analytics service.
* `.env.example` now lists **SENTRY_DSN** and Vault variables.

## How to enable
1. Add your Sentry DSN to Render Secret Store or local `.env`.
2. If using Vault, set `VAULT_ADDR` and `VAULT_TOKEN`; otherwise ensure secrets exist in environment.
3. Build: `docker compose build nova-analytics`.
4. Run the stack: `docker compose up -d`.
