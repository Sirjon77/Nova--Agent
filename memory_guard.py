
"""Utility to deduplicate and clean up Weaviate memory entries."""
import os
import datetime
import weaviate
from sentence_transformers import SentenceTransformer
import numpy as np

MODEL = SentenceTransformer('all-MiniLM-L6-v2')
WEAVIATE_URL = os.getenv('WEAVIATE_URL')
WEAVIATE_API_KEY = os.getenv('WEAVIATE_API_KEY')

# Fix for Weaviate v4: use WeaviateClient instead of Client
if WEAVIATE_URL and WEAVIATE_API_KEY:
    client = weaviate.WeaviateClient(
        connection_params=weaviate.connect.ConnectionParams.from_url(
            WEAVIATE_URL,
            grpc_port=50051,  # Default gRPC port
            auth_credentials=weaviate.auth.AuthApiKey(WEAVIATE_API_KEY)
        )
    )
else:
    client = None

COS_LIMIT = 0.9

def _similar(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def save_if_useful(text: str, meta: dict):
    if not client:
        return 'skip'
    
    vec = MODEL.encode(text)
    # Fix for Weaviate v4: use new API
    similar = client.collections.get('Memory').query.near_vector(
        vector=vec.tolist(),
        limit=1,
        return_properties=['_additional {vector}']
    )
    
    if similar.objects:
        return 'skip'
    
    # Fix for Weaviate v4: use new API
    client.collections.get('Memory').data.insert({
        'text': text,
        **meta
    }, vector=vec.tolist())
    return 'stored'

def cleanup():
    """Delete entries older than 90 days or low score."""
    if not client:
        return
        
    threshold = (datetime.datetime.utcnow() - datetime.timedelta(days=90)).isoformat()
    # Fix for Weaviate v4: use new API
    client.collections.get('Memory').data.delete_many(
        where={
            'path': ['created'],
            'operator': 'LessThan',
            'valueDate': threshold
        }
    )
