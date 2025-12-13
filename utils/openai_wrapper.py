"""Unified OpenAI call with retry, back‑off and token watchdog."""
import os
import time
import openai
import tiktoken
import logging

logger = logging.getLogger("openai_wrapper")

API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
openai.api_key = API_KEY

# Use the new OpenAI client wrapper that forces model translation
try:
    from nova.services.openai_client import chat_completion as nova_chat_completion
    from nova_core.model_registry import get_default_model
    DEFAULT_MODEL = get_default_model()
    FALLBACK_MODEL = "gpt-3.5-turbo"
except ImportError:
    # Fallback if wrapper not available
    def nova_chat_completion(messages, model=None, **kwargs):
        return openai.ChatCompletion.create(messages=messages, **kwargs)
    DEFAULT_MODEL = "gpt-4o"
    FALLBACK_MODEL = "gpt-3.5-turbo"

MAX_COST_DOLLARS = float(os.getenv("MAX_PROMPT_COST", "0.005"))

_enc_cache = {}

def _num_tokens(text: str, model: str = "gpt-3.5-turbo"):
    if model not in _enc_cache:
        _enc_cache[model] = tiktoken.encoding_for_model(model)
    enc = _enc_cache[model]
    return len(enc.encode(text))

def estimate_cost(prompt: str, model: str):
    # rough: assume 1k tokens ≈ $0.01 for o3, $0.03 for 4o-mini
    tok = _num_tokens(prompt, model)
    if "o3" in model:
        return tok / 1000 * 0.01
    return tok / 1000 * 0.03

def chat_completion(prompt: str, model: str = None, temperature: float = 0.2, **kwargs) -> str:
    # Use the wrapper that automatically translates model aliases
    chosen = model or DEFAULT_MODEL
    
    # watchdog
    if estimate_cost(prompt, chosen) > MAX_COST_DOLLARS:
        logger.info("Downgrading model due to cost watchdog")
        chosen = FALLBACK_MODEL
    
    for attempt in range(3):
        try:
            resp = nova_chat_completion(
                messages=[{"role":"user","content":prompt}],
                model=chosen,  # Will be automatically translated to official model ID
                temperature=temperature,
                **kwargs
            )
            return resp.choices[0].message.content
        except openai.error.OpenAIError as e:
            logger.warning("OpenAI error: %s. retry %d", e, attempt)
            time.sleep(2 ** attempt)
    raise RuntimeError("OpenAI failed 3×")
