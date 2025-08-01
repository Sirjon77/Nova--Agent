
import json
from datetime import datetime

def log_monetization_event(source, revenue=0.0, event_type='click'):
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'source': source,
        'event_type': event_type,
        'revenue': revenue
    }
    try:
        if os.path.exists("funnel_log.json"):
            with open("funnel_log.json", "r") as f:
                data = json.load(f)
        else:
            data = []
        data.append(log_entry)
        with open("funnel_log.json", "w") as f:
            json.dump(data, f, indent=2)
        print(f"[Funnel] Logged: {event_type} from {source}")
    except Exception as e:
        print(f"[Funnel Error] {e}")
