
import os
import openai
from datetime import datetime

openai.api_key = os.getenv("OPENAI_API_KEY", "")

# Use model registry for model resolution
try:
    from nova_core.model_registry import resolve as resolve_model
except ImportError:
    # Fallback function if model registry not available
    def resolve_model(alias: str) -> str:
        return alias

def summarize_text(text, max_tokens=500):
    if not openai.api_key:
        print("[OpenAI] API key missing. Skipping summarization.")
        return text[:max_tokens]

    try:
        # Use model registry to resolve model alias
        model = resolve_model("gpt-3.5-turbo")
        
        response = openai.ChatCompletion.create(
            model=model,  # Now uses resolved official model ID
            messages=[
                {"role": "system", "content": "Summarize this web content concisely."},
                {"role": "user", "content": text[:3000]}
            ],
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
