import os
import openai

# Use model registry for model resolution
try:
    from nova_core.model_registry import resolve as resolve_model
except ImportError:
    # Fallback function if model registry not available
    def resolve_model(alias: str) -> str:
        return alias

openai.api_key = os.getenv("OPENAI_API_KEY")

# Use model registry to resolve model alias
model = resolve_model("gpt-4o-mini")

response = openai.ChatCompletion.create(
    model=model,  # Now uses resolved official model ID
    messages=[
        {"role": "user", "content": "Hello, this is a test message."}
    ]
)

print(response.choices[0].message.content)