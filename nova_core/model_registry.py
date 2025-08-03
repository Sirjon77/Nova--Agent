"""
Central mapping of *friendly* model aliases -> official OpenAI model IDs.

Add new aliases here only. This ensures all model names are validated
and normalized before being sent to the OpenAI API.
"""

from os import getenv
from typing import Dict, List, Optional, Union

# 1️⃣ canonical mapping
MODEL_MAP: Dict[str, str] = {
    # GPT-4 tier
    "gpt-4o-mini":   "gpt-4o",          # official name 2025-05-13
    "gpt-4o-vision": "gpt-4o",          # same backend, diff alias
    "gpt-4-turbo":   "gpt-4o",          # team shorthand
    "gpt-4":         "gpt-4o",          # legacy alias
    "gpt-4o":        "gpt-4o",          # direct mapping (no change)
    
    # GPT-3.5 tier
    "gpt-3.5-mini":  "gpt-3.5-turbo",
    "gpt-3.5":       "gpt-3.5-turbo",
    "gpt-3.5-turbo": "gpt-3.5-turbo",   # direct mapping (no change)
    
    # Legacy/alternative names
    "gpt-4o-mini-search": "gpt-4o",     # was invalid, now maps to gpt-4o
    "gpt-4o-mini-TTS": "gpt-4o",        # was invalid, now maps to gpt-4o
}

# 2️⃣ default used by Nova when nothing is configured
DEFAULT_ALIAS = getenv("NOVA_DEFAULT_MODEL", "gpt-4o-mini")

def resolve(alias: Optional[str] = None) -> str:
    """
    Convert a friendly alias to the exact OpenAI model name.
    
    Args:
        alias: Model alias to resolve. If None, uses DEFAULT_ALIAS.
        
    Returns:
        str: Official OpenAI model ID
        
    Raises:
        KeyError: if alias not in registry
    """
    alias = (alias or DEFAULT_ALIAS).strip()
    
    # Check if it's a known alias
    if alias in MODEL_MAP:
        return MODEL_MAP[alias]
    
    # If it's already an official model ID, allow but warn
    if alias.startswith("gpt-"):
        import warnings
        warnings.warn(
            f"Prefer using a Nova alias, not raw model id '{alias}'.",
            UserWarning,
            stacklevel=2,
        )
        return alias
    
    # Unknown alias
    raise KeyError(
        f"Unknown model alias '{alias}'. "
        f"Available aliases: {list(MODEL_MAP.keys())}. "
        "Add it to MODEL_MAP or use an official model ID."
    )

def get_available_aliases() -> List[str]:
    """Get list of all available model aliases."""
    return list(MODEL_MAP.keys())

def get_official_models() -> List[str]:
    """Get list of all official OpenAI model IDs used."""
    return list(set(MODEL_MAP.values()))

def is_valid_alias(alias: str) -> bool:
    """Check if an alias is valid."""
    return alias in MODEL_MAP

def get_default_model() -> str:
    """Get the default model ID."""
    return resolve(DEFAULT_ALIAS) 