"""Publish high-quality reflections into shared Weaviate KB."""
import os, uuid, time
from utils.memory_router import retrieve_relevant, store_long

try:
    import weaviate
    client = weaviate.Client(os.getenv("WEAVIATE_URL", "http://localhost:8080"))
except ModuleNotFoundError:
    client = None

def publish_reflection(session_id: str, reflection: str, tags: list = None):
    if not client:
        return
    obj = {
        "session_id": session_id,
        "content": reflection,
        "tags": tags or [],
        "timestamp": time.time()
    }
    client.data_object.create(obj, class_name="GlobalReflection")
    # also store in session-long memory
    store_long(session_id, reflection)
