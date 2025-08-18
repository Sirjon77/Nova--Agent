
import json
import pathlib
import datetime
from datetime import timezone
LOGFILE = pathlib.Path('logs/audit.log')
LOGFILE.parent.mkdir(exist_ok=True)
def audit(event, user='system', meta=None):
    rec = {'ts': datetime.datetime.now(timezone.utc).isoformat(timespec='seconds'),
           'user': user,
           'event': event,
           'meta': meta or {}}
    with LOGFILE.open('a') as f:
        f.write(json.dumps(rec) + '\n')
