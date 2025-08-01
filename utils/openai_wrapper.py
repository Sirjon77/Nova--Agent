"""Unified OpenAI call with retry, back‑off and token watchdog."""
import os, time, openai, tiktoken, logging
from typing import List, Dict

logger = logging.getLogger("openai_wrapper")

API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
openai.api_key = API_KEY

DEFAULT_MODEL = os.getenv("DEFAULT_GPT_MODEL", "o3")
FALLBACK_MODEL = os.getenv("FALLBACK_GPT_MODEL", "gpt-3.5-turbo")
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
    chosen = model or DEFAULT_MODEL
    # watchdog
    if estimate_cost(prompt, chosen) > MAX_COST_DOLLARS:
        logger.info("Downgrading model due to cost watchdog")
        chosen = FALLBACK_MODEL
    for attempt in range(3):
        try:
            resp = openai.ChatCompletion.create(
                model=chosen,
                messages=[{"role":"user","content":prompt}],
                temperature=temperature,
                **kwargs
            )
            return resp.choices[0].message.content
        except openai.error.OpenAIError as e:
            logger.warning("OpenAI error: %s. retry %d", e, attempt)
            time.sleep(2 ** attempt)
    raise RuntimeError("OpenAI failed 3×")
