
"""Utility to deduplicate and clean up Weaviate memory entries."""
import os, datetime, uuid, math
import weaviate
from sentence_transformers import SentenceTransformer
import numpy as np

MODEL = SentenceTransformer('all-MiniLM-L6-v2')
WEAVIATE_URL = os.getenv('WEAVIATE_URL')
WEAVIATE_API_KEY = os.getenv('WEAVIATE_API_KEY')
client = weaviate.Client(
    url=WEAVIATE_URL,
    auth_client_secret=weaviate.AuthApiKey(WEAVIATE_API_KEY)
)

COS_LIMIT = 0.9

def _similar(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def save_if_useful(text: str, meta: dict):
    vec = MODEL.encode(text)
    similar = client.query            .get('Memory', ['_additional {vector}'])            .with_near_vector({'vector': vec.tolist(), 'certainty': 0.90})            .with_limit(1).do()
    if similar['data']['Get']['Memory']:
        return 'skip'
    client.batch.add_data_object(
        data_object={'text': text, **meta},
        class_name='Memory',
        vector=vec.tolist(),
        uuid=str(uuid.uuid4())
    )
    return 'stored'

def cleanup():
    """Delete entries older than 90 days or low score."""
    threshold = (datetime.datetime.utcnow() - datetime.timedelta(days=90)).isoformat()
    where = {
        'path': ['created'],
        'operator': 'LessThan',
        'valueDate': threshold
    }
    client.batch.delete_objects(
        class_name='Memory',
        where=where
    )
