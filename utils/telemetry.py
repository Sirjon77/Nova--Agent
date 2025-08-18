"""Simple telemetry emitter; routes to LangSmith if API key provided,
else stdout JSON for Grafana Loki scrape."""
import os
import json
import time
import sys

LS_API = os.getenv("LANGSMITH_API_KEY")

def emit(event: str, payload: dict):
    data = {"event": event, "ts": time.time(), **payload}
    if LS_API:
        try:
            import langsmith
            langsmith.log(data)   # pseudo
        except ModuleNotFoundError:
            pass
    print(json.dumps(data), file=sys.stderr)
