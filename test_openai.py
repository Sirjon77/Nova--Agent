import os
import openai

# Use the new OpenAI client wrapper that forces model translation
try:
    from nova.services.openai_client import chat_completion
except ImportError:
    # Fallback to direct OpenAI call if wrapper not available
    def chat_completion(messages, model=None, **kwargs):
        return openai.ChatCompletion.create(messages=messages, **kwargs)

openai.api_key = os.getenv("OPENAI_API_KEY")

# Use the wrapper that automatically translates model aliases
response = chat_completion(
    messages=[
        {"role": "user", "content": "Hello, this is a test message."}
    ],
    model="gpt-4o-mini"  # Will be automatically translated to "gpt-4o"
)

print(response.choices[0].message.content)