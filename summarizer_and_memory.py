
import os
import openai
from datetime import datetime

openai.api_key = os.getenv("OPENAI_API_KEY", "")

# Use the new OpenAI client wrapper that forces model translation
try:
    from nova.services.openai_client import chat_completion
except ImportError:
    # Fallback to direct OpenAI call if wrapper not available
    def chat_completion(messages, model=None, **kwargs):
        return openai.ChatCompletion.create(messages=messages, **kwargs)

def summarize_text(text, max_tokens=500):
    if not openai.api_key:
        print("[OpenAI] API key missing. Skipping summarization.")
        return text[:max_tokens]

    try:
        # Use the wrapper that automatically translates model aliases
        response = chat_completion(
            messages=[
                {"role": "system", "content": "Summarize this web content concisely."},
                {"role": "user", "content": text[:3000]}
            ],
            model="gpt-3.5-turbo",  # Will be automatically translated to "gpt-3.5-turbo"
            max_tokens=max_tokens,
            temperature=0.5
        )
        summary = response['choices'][0]['message']['content']
        return summary
    except Exception as e:
        print(f"[OpenAI] Error during summarization: {e}")
        return text[:max_tokens]

def store_summary_to_memory(url, summary):
    ts = datetime.utcnow().isoformat()
    memory_file = "memory_crawled_summaries.json"
    record = {"timestamp": ts, "url": url, "summary": summary}
    import json
    try:
        if os.path.exists(memory_file):
            with open(memory_file, "r") as f:
                data = json.load(f)
        else:
            data = []
        data.append(record)
        with open(memory_file, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[Memory] Stored summary for {url}")
    except Exception as e:
        print(f"[Memory] Failed to write summary: {e}")
