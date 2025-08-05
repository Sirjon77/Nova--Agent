"""Publish high-quality reflections into shared Weaviate KB."""
import os, uuid, time
from utils.memory_router import retrieve_relevant, store_long

try:
    import weaviate
    # Fix for Weaviate v4: use WeaviateClient instead of Client
    client = weaviate.WeaviateClient(
        connection_params=weaviate.connect.ConnectionParams.from_url(
            os.getenv("WEAVIATE_URL", "http://localhost:8080"),
            grpc_port=50051  # Default gRPC port
        )
    )
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
    # Fix for Weaviate v4: use new API
    client.collections.get("GlobalReflection").data.insert(obj)
    # also store in session-long memory
    store_long(session_id, reflection)
