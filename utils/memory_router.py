"""MemoryRouter

Wraps *short‑term* context (Redis) and *long‑term* vector memory (Weaviate).
Swap the clients out if you prefer Chroma, Supabase, etc.
"""
import os
from typing import List, Dict, Any, Optional

# Short‑term memory (rolling chat log)
try:
    import redis

    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
except ModuleNotFoundError:  # Local dev without redis‑py
    redis_client = None

# Long‑term vector memory
try:
    import weaviate
    WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    weaviate_client = weaviate.Client(WEAVIATE_URL)
except ModuleNotFoundError:
    weaviate_client = None

SHORT_TURN_LIMIT = int(os.getenv("SHORT_TURN_LIMIT", 20))

def _short_key(session_id: str) -> str:
    return f"chat:{session_id}:history"

# -----------------------------------------
# Public functions
# -----------------------------------------

def store_short(session_id: str, role: str, content: str) -> None:
    """Push a chat turn into the rolling buffer."""
    if not redis_client:
        return
    redis_client.rpush(_short_key(session_id), f"{role}||{content}")
    redis_client.ltrim(_short_key(session_id), -SHORT_TURN_LIMIT, -1)  # keep last N

def get_short(session_id: str) -> List[str]:
    if not redis_client:
        return []
    return redis_client.lrange(_short_key(session_id), 0, -1)

def store_long(session_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """Store an embedded memory snippet for long‑term recall."""
    if not weaviate_client:
        return
    obj = {
        "session_id": session_id,
        "content": content,
        "metadata": metadata or {},
    }
    weaviate_client.data_object.create(obj, class_name="Memory")

def retrieve_relevant(session_id: str, query: str, k: int = 3) -> List[str]:
    if not weaviate_client:
        return []
    res = (
        weaviate_client.query
        .get("Memory", ["content"])
        .with_where({"path": ["session_id"], "operator": "Equal", "valueString": session_id})
        .with_near_text({"concepts": [query], "distance": 0.7})
        .with_limit(k)
        .do()
    )
    return [d["content"] for d in res["data"]["Get"]["Memory"]]
