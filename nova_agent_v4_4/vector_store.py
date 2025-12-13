"""Wrap calls to Weaviate or fallback Chroma for long‑term memory."""
import os
import weaviate
from openai import OpenAI

# Initialize OpenAI client only if API key is available
client = None
if os.getenv("OPENAI_API_KEY"):
    try:
        client = OpenAI()
    except Exception:
        client = None

WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")

# Fix for Weaviate v4: use WeaviateClient instead of Client
if WEAVIATE_URL and WEAVIATE_API_KEY:
    weaviate_client = weaviate.WeaviateClient(
        connection_params=weaviate.connect.ConnectionParams.from_url(
            WEAVIATE_URL,
            grpc_port=50051,  # Default gRPC port
            auth_credentials=weaviate.auth.AuthApiKey(WEAVIATE_API_KEY)
        )
    )
    CLASS = "ChatMemory"
else:
    weaviate_client = None

def store_long(session_id: str, text: str):
    if not WEAVIATE_URL or not client or not weaviate_client:
        return
    try:
        vector = client.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding
        data_obj = {"session_id": session_id, "text": text}
        # Fix for Weaviate v4: use new API
        weaviate_client.collections.get(CLASS).data.insert(data_obj, vector=vector)
    except Exception:
        # Silently fail if embedding creation fails
        pass

def retrieve_relevant(session_id: str, query: str, k: int = 3):
    if not WEAVIATE_URL or not client or not weaviate_client:
        return []
    try:
        vector = client.embeddings.create(input=[query], model="text-embedding-3-small").data[0].embedding
        # Fix for Weaviate v4: use new API
        resp = weaviate_client.collections.get(CLASS).query.near_vector(
            vector=vector,
            limit=k,
            return_properties=["text", "session_id"]
        )
        return [obj.properties["text"] for obj in resp.objects if obj.properties.get("session_id") == session_id]
    except Exception:
        # Return empty list if embedding creation fails
        return []
