# Use the new OpenAI client wrapper that forces model translation
try:
    from nova.services.openai_client import chat_completion
except ImportError:
    # Fallback to direct OpenAI call if wrapper not available
    from openai import OpenAI
    client = OpenAI()
    def chat_completion(messages, model=None, **kwargs):
        return client.chat.completions.create(messages=messages, **kwargs)

def should_remember(user_message: str) -> bool:
    # Use the wrapper that automatically translates model aliases
    completion = chat_completion(
        messages=[
            {"role": "system", "content": "Return 'yes' if the message should be stored long‑term."},
            {"role": "user", "content": user_message},
        ],
        model="gpt-4o-mini",  # Will be automatically translated to "gpt-4o"
    )
    return completion.choices[0].message.content.lower().startswith("yes")
