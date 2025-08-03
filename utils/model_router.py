
import json
import re

# Use model registry for model resolution
try:
    from nova_core.model_registry import resolve as resolve_model, get_default_model
except ImportError:
    # Fallback function if model registry not available
    def resolve_model(alias: str) -> str:
        return alias
    def get_default_model() -> str:
        return "gpt-4o"

MODELS_FILE = "models.json"
STATE = {"active_model": None}

def load_model_config():
    with open(MODELS_FILE, "r") as f:
        return json.load(f)

def get_active_model_config():
    cfg = load_model_config()
    active = STATE.get("active_model") or cfg["default"]
    return cfg["models"].get(active, cfg["models"][cfg["default"]])

def set_active_model(name):
    cfg = load_model_config()
    if name in cfg["models"]:
        STATE["active_model"] = name
        return True
    return False

def detect_model_switch_command(message: str):
    match = re.search(r"@Nova switch to ([\w\-.]+)", message)
    if match:
        return match.group(1)
    return None

def detect_task_based_model(message: str):
    lower = message.lower()
    if any(word in lower for word in ["research", "analyze", "scientific", "compare", "study", "evaluate", "report"]):
        return "o3-deep-research"
    elif "script" in lower:
        return "gpt-4.1"
    elif "hook" in lower or "idea" in lower:
        return resolve_model("gpt-4o-mini")  # Use model registry
    elif "summarize" in lower or "shorten" in lower:
        return "gpt-4.1-nano"
    return None

# log_model_usage removed

# Usage after calling OpenAI:
# log_model_usage(model_name, num_tokens_used)
# ---- Auto Model Selector patch (Tier‑A upgrade) ----
import os
def _choose_model(prompt: str, preferred: str = None):
    """Select cheaper/faster model if prompt is short."""
    if preferred is None:
        preferred = get_default_model()  # Use model registry default
    
    length = len(prompt)
    if length > 4000:
        return preferred  # large prompt: stick to mini
    elif length < 1500:
        return os.getenv("DEFAULT_MODEL", "o3")  # faster & cheaper
    return preferred

_original_chat_completion = chat_completion

def chat_completion(prompt: str, temperature: float = 0.2, **kwargs):
    model = _choose_model(prompt)
    return _original_chat_completion(prompt, temperature=temperature, model=model, **kwargs)
