from redis_client import r

# Use the new OpenAI client wrapper that forces model translation
try:
    from nova.services.openai_client import chat_completion
except ImportError:
    # Fallback to direct OpenAI call if wrapper not available
    from openai import OpenAI
    client = OpenAI()
    def chat_completion(messages, model=None, **kwargs):
        return client.chat.completions.create(messages=messages, **kwargs)

def summarise_if_needed(session_id: str):
    key = f"hist:{session_id}"
    turns = r.lrange(key, 0, -1)
    joined = "".join(turns)
    if len(joined) < 8000:
        return
    
    # Use the wrapper that automatically translates model aliases
    completion = chat_completion(
        messages=[
            {"role": "system", "content": "Summarise the following chat as one sentence."},
            {"role": "user", "content": joined},
        ],
        model="gpt-4o-mini",  # Will be automatically translated to "gpt-4o"
    )
    summary = completion.choices[0].message.content.strip()
    r.set(f"summary:{session_id}", summary)
    r.delete(key)
