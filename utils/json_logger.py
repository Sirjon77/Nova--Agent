import json, sys, datetime

def log(event: str, **kwargs):
    entry = {"ts": datetime.datetime.utcnow().isoformat(), "event": event}
    entry.update(kwargs)
    print(json.dumps(entry), file=sys.stderr)
