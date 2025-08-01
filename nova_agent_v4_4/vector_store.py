"""Wrap calls to Weaviate or fallback Chroma for long‑term memory."""
import os
import uuid
import weaviate
from openai import OpenAI
client = OpenAI()

WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
if WEAVIATE_URL:
    weaviate_client = weaviate.Client(url=WEAVIATE_URL, auth_client_secret=WEAVIATE_API_KEY)
    CLASS = "ChatMemory"

def store_long(session_id: str, text: str):
    if not WEAVIATE_URL:
        return
    vector = client.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding
    data_obj = {"session_id": session_id, "text": text}
    weaviate_client.data_object.create(data_obj, CLASS, uuid.uuid4(), vector=vector)

def retrieve_relevant(session_id: str, query: str, k: int = 3):
    if not WEAVIATE_URL:
        return []
    vector = client.embeddings.create(input=[query], model="text-embedding-3-small").data[0].embedding
    resp = weaviate_client.query.get(CLASS, ["text", "session_id"]).with_near_vector({"vector": vector}).with_limit(k).do()
    return [o["text"] for o in resp["data"]["Get"].get(CLASS, []) if o["session_id"] == session_id]
