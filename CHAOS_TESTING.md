# Chaos Testing Guide

Nova Agent includes a lightweight chaos kit that helps you test resilience
against latency spikes, exceptions, and subsystem outages.

## Components

| File | Purpose |
|------|---------|
| `nova/chaos/injector.py` | Utility that randomly introduces delays or raised exceptions. |
| `tests/chaos/` | pytest suite validating chaos helpers. |
| `Makefile` target `chaos-run` | Runs a one‑minute chaos session against the local API. |

## Example usage

```bash
# Start API in one shell
make run-api

# Run chaos script in another
make chaos-run
```

During the session you should see occasional error logs but the
process must stay alive and respond on /health within SLA (< 1 s).

## Scenarios to test manually

1. **Memory pressure** – use `stress --vm 1 --vm-bytes 600M --timeout 30s`.
2. **DB outage** – shut down your Redis/Postgres container and watch governance loop.
3. **Tool timeout** – set `CHAOS_FAIL_RATE=1.0` in env so every external ping times out.
