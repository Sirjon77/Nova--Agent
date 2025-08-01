import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

try:
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say hello from Nova"}]
    )
    print("✅ OpenAI is working. Response:")
    print(response.choices[0].message["content"])
except Exception as e:
    print("❌ OpenAI test failed:", e)