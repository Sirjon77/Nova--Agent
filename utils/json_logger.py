import json
import sys
import datetime

def log(event: str, **kwargs):
    entry = {"ts": datetime.datetime.utcnow().isoformat(), "event": event}
    entry.update(kwargs)
    json_str = json.dumps(entry)
    print(json_str, file=sys.stderr)
    return json_str
