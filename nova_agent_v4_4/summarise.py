import os
from redis_client import r
from openai import OpenAI
client = OpenAI()

def summarise_if_needed(session_id: str):
    key = f"hist:{session_id}"
    turns = r.lrange(key, 0, -1)
    joined = "".join(turns)
    if len(joined) < 8000:
        return
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Summarise the following chat as one sentence."},
            {"role": "user", "content": joined},
        ],
    )
    summary = completion.choices[0].message.content.strip()
    r.set(f"summary:{session_id}", summary)
    r.delete(key)
