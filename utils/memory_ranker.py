"""Memory Ranking & Pruning utilities.

*Score = recency_weight * (1 / age_days) + relevance_weight * similarity*

For speed we stub the similarity with length‑based heuristic; swap in
`langchain.retrievers.ContextualCompressionRetriever`
+ `OpenAIEmbeddings` for production.
"""
import time
from datetime import datetime, timezone
from typing import List, Dict

RECENCY_WEIGHT = 0.6
RELEVANCE_WEIGHT = 0.4
SIM_THRESHOLD = 0.25      # below this → delete

def _age_days(ts: float) -> float:
    return (time.time() - ts) / 86400

def _fake_similarity(text: str, query: str) -> float:
    """Placeholder similarity: ratio of common words."""
    if not query:
        return 0.0
    a, b = set(text.lower().split()), set(query.lower().split())
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

def score_memory(mem: Dict, query: str = "") -> float:
    age = _age_days(mem.get("timestamp", time.time()))
    recency_score = 1.0 / (1.0 + age)
    sim_score = _fake_similarity(mem.get("content",""), query)
    return RECENCY_WEIGHT * recency_score + RELEVANCE_WEIGHT * sim_score

# --- Weaviate prune stub ----
def prune_low_value(weaviate_client, session_id: str, query: str = ""):
    """Delete memories for `session_id` whose score < SIM_THRESHOLD."""
    res = (
        weaviate_client.query
        .get("Memory", ["_additional { id }", "content", "timestamp"])
        .with_where({"path": ["session_id"], "operator": "Equal", "valueString": session_id})
        .with_limit(1000)
        .do()
    )
    ids_to_delete = []
    if res and "data" in res:
        for obj in res["data"]["Get"]["Memory"]:
            s = score_memory(obj, query)
            if s < SIM_THRESHOLD:
                ids_to_delete.append(obj["_additional"]["id"])
    for mem_id in ids_to_delete:
        weaviate_client.data_object.delete(mem_id, class_name="Memory")
    return len(ids_to_delete)
