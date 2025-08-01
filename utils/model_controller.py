"""
Adaptive Model Controller for Nova Agent v3.8 – Collaborative Superagent.

Routes tasks to the most cost‑effective OpenAI model according to:
    • task metadata flags
    • token budget heuristics
    • reasoning‑depth estimation
The routing table is also persisted to `config/model_tiers.json` for runtime overrides.
"""

import os
import json
from pathlib import Path
from typing import Dict, Tuple

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "model_tiers.json"

# Default model map (can be overridden by on‑disk JSON)
_DEFAULT_TIERS = {
    "ultra_light":   {"model": "gpt-4o-mini",          "routes": ["micro_summary", "caption_fix"]},
    "budget_creative": {"model": "gpt-4.1-nano",      "routes": ["ab_test", "hashtag", "hook"]},
    "standard_brain": {"model": "o3",                 "routes": ["script", "carousel", "dev"]},
    "multimodal_core": {"model": "gpt-4o",            "routes": ["multimodal"]},
    "deep_research": {"model": "o3-pro",              "routes": ["deep_reason"]},
    "retrieval":     {"model": "gpt-4o-mini-search",  "routes": ["retrieval"]},
    "embeddings":    {"model": "text-embedding-3-small", "routes": ["embedding"]},
    "tts_asr":       {"model": "gpt-4o-mini-TTS",     "routes": ["voice"]},
    "images":        {"model": "GPT-Image-1",         "routes": ["image"]},
}

def _load_config() -> Dict:
    """Load tier config, falling back to defaults if missing"""
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception:
            pass
    return _DEFAULT_TIERS

MODEL_TIERS = _load_config()

# Map model name to ENV var suffix
_ENV_MAP = {
    "gpt-4o-mini": "OPENAI_KEY_MINI",
    "gpt-4.1-nano": "OPENAI_KEY_NANO",
    "o3": "OPENAI_KEY_STANDARD",
    "gpt-4o": "OPENAI_KEY_FAST",
    "o3-pro": "OPENAI_KEY_PRO",
    "gpt-4o-mini-search": "OPENAI_KEY_MINI",
    "text-embedding-3-small": "OPENAI_KEY_EMBED",
    "gpt-4o-mini-TTS": "OPENAI_KEY_MINI",
    "GPT-Image-1": "OPENAI_KEY_IMAGE",
}

def _estimate_reasoning_depth(prompt: str) -> int:
    """Very naive heuristic: longer + question words => higher depth (0‑10)."""
    keywords = ("why", "how", "analysis", "compare", "evaluate", "strategy")
    depth = len(prompt.split()) // 100
    depth += sum(1 for kw in keywords if kw in prompt.lower())
    return min(depth, 10)

def select_model(task_meta: Dict) -> Tuple[str, str]:
    """
    Decide the best model for a given task.
    :param task_meta: {
       'type': 'script' | 'caption_fix' | ...,
       'prompt': str,
       'force_model': str | None
    }
    :return: (model_name, api_key)
    """

    # 1. Explicit override
    if task_meta.get("force_model"):
        model = task_meta["force_model"]
    else:
        task_type = task_meta.get("type", "")
        # Find tier by route
        selected = None
        for tier in MODEL_TIERS.values():
            if task_type in tier["routes"]:
                selected = tier
                break
        # Fallback to standard brain
        model = selected["model"] if selected else "o3"

        # 2. Escalate from o3 to o3-pro if reasoning depth > 6
        if model == "o3":
            depth_score = _estimate_reasoning_depth(task_meta.get("prompt", ""))
            if depth_score >= 6:
                model = "o3-pro"

    api_key = os.getenv(_ENV_MAP.get(model, "OPENAI_API_KEY"), os.getenv("OPENAI_API_KEY"))
    return model, api_key