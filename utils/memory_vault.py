"""Store tiny per‑workflow JSON summaries in Redis JSON."""
import os
import json
import time
try:
    import redis
except ModuleNotFoundError:
    redis = None

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True) if redis else None

def _key(workflow: str, obj_id: str):
    return f"vault:{workflow}:{obj_id}"

def save_summary(workflow: str, obj_id: str, summary: dict):
    if not redis_client:
        return
    redis_client.set(_key(workflow, obj_id), json.dumps({"ts": time.time(), **summary}))

def get_summary(workflow: str, obj_id: str):
    if not redis_client:
        return None
    data = redis_client.get(_key(workflow, obj_id))
    return json.loads(data) if data else None
