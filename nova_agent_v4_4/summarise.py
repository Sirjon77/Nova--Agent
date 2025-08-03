import os
from redis_client import r
from openai import OpenAI

# Use model registry for model resolution
try:
    from nova_core.model_registry import resolve as resolve_model
except ImportError:
    # Fallback function if model registry not available
    def resolve_model(alias: str) -> str:
        return alias

client = OpenAI()

def summarise_if_needed(session_id: str):
    key = f"hist:{session_id}"
    turns = r.lrange(key, 0, -1)
    joined = "".join(turns)
    if len(joined) < 8000:
        return
    
    # Use model registry to resolve model alias
    model = resolve_model("gpt-4o-mini")
    
    completion = client.chat.completions.create(
        model=model,  # Now uses resolved official model ID
        messages=[
            {"role": "system", "content": "Summarise the following chat as one sentence."},
            {"role": "user", "content": joined},
        ],
    )
    summary = completion.choices[0].message.content.strip()
    r.set(f"summary:{session_id}", summary)
    r.delete(key)
