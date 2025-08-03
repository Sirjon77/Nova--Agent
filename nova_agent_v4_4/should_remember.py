from openai import OpenAI

# Use model registry for model resolution
try:
    from nova_core.model_registry import resolve as resolve_model
except ImportError:
    # Fallback function if model registry not available
    def resolve_model(alias: str) -> str:
        return alias

client = OpenAI()

def should_remember(user_message: str) -> bool:
    # Use model registry to resolve model alias
    model = resolve_model("gpt-4o-mini")
    
    completion = client.chat.completions.create(
        model=model,  # Now uses resolved official model ID
        messages=[
            {"role": "system", "content": "Return 'yes' if the message should be stored long‑term."},
            {"role": "user", "content": user_message},
        ],
    )
    return completion.choices[0].message.content.lower().startswith("yes")
