
import os
import json
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")
MEMORY_LOG = "nova_memory_log.json"

# Use the new OpenAI client wrapper that forces model translation
try:
    from nova.services.openai_client import chat_completion
except ImportError:
    # Fallback to direct OpenAI call if wrapper not available
    def chat_completion(messages, model=None, **kwargs):
        return openai.ChatCompletion.create(messages=messages, **kwargs)

def refine_code_snippets():
    if not os.path.exists(MEMORY_LOG):
        print("[Reflector] No memory log found.")
        return

    with open(MEMORY_LOG, "r") as f:
        entries = json.load(f)

    for entry in entries[-5:]:  # Only review the most recent 5
        prompt = entry["prompt"]
        original = entry["response"]

        prompt_refine = (
            "Improve this Python code to be more reliable, modular, and readable. "
            "Ensure the functionality remains the same.\n\n"
            f"{original}"
        )

        # Use the wrapper that automatically translates model aliases
        response = chat_completion(
            messages=[
                {"role": "system", "content": "You are a senior Python refactor bot."},
                {"role": "user", "content": prompt_refine}
            ],
            model="gpt-4o-mini",  # Will be automatically translated to "gpt-4o"
            temperature=0.3
        )

        improved_code = response['choices'][0]['message']['content']
        fname = f"refined_module_{entries.index(entry)}.py"
        with open(fname, "w") as f_out:
            f_out.write(improved_code)
        print(f"[Reflector] Wrote improved version to: {fname}")
