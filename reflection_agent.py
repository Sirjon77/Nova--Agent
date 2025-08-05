"""Reflection Agent - Stores high-quality reflections in Weaviate."""
import os, uuid, time
import weaviate

# Fix for Weaviate v4: use WeaviateClient instead of Client
try:
    client = weaviate.WeaviateClient(
        connection_params=weaviate.connect.ConnectionParams.from_url(
            os.getenv("WEAVIATE_URL", "http://localhost:8080"),
            grpc_port=50051  # Default gRPC port
        )
    )
except:
    client = None

def store_reflection(reflection: str, tags: list = None):
    if not client:
        return False
    
    obj = {
        "content": reflection,
        "tags": tags or [],
        "timestamp": time.time()
    }
    
    # Fix for Weaviate v4: use new API
    try:
        client.collections.get("Reflection").data.insert(obj)
        return True
    except:
        return False

def get_reflections(limit: int = 10):
    if not client:
        return []
    
    # Fix for Weaviate v4: use new API
    try:
        resp = client.collections.get("Reflection").query.fetch_objects(
            limit=limit,
            return_properties=["content", "tags", "timestamp"]
        )
        return [obj.properties for obj in resp.objects]
    except:
        return []