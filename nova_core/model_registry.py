"""Single‑source registry for OpenAI model identifiers.

Internal aliases (e.g. "gpt‑4o‑mini") are translated to official model names
before an API request is issued so that *only* valid identifiers reach OpenAI.
"""
from enum import Enum
from typing import Optional


class Model(str, Enum):
    # ── Official public models ────────────────────────────────────────────────
    GPT_4 = "gpt-4o"
    GPT_3_5_TURBO = "gpt-3.5-turbo"

    # ── Internal shorthands / legacy aliases ─────────────────────────────────
    GPT_4_MINI = "gpt-4o-mini"          # maps → GPT_4
    GPT_4_VISION = "gpt-4o-vision"      # maps → GPT_4
    O3 = "o3"                           # maps → GPT_3_5_TURBO
    O3_PRO = "o3-pro"                   # maps → GPT_4

    DEFAULT = GPT_4


_ALIAS_TO_OFFICIAL = {
    Model.GPT_4_MINI: Model.GPT_4,
    Model.GPT_4_VISION: Model.GPT_4,
    Model.O3: Model.GPT_3_5_TURBO,
    Model.O3_PRO: Model.GPT_4,
}


def to_official(name: Optional[str] = None) -> str:
    """Return an official OpenAI model name for *any* supported alias."""
    if not name:
        return Model.DEFAULT.value
    
    # Strip whitespace
    name = name.strip()
    
    if not name:
        return Model.DEFAULT.value
    
    try:
        alias = Model(name)
    except ValueError:  # unknown → assume caller supplied a valid public name
        return name
    return _ALIAS_TO_OFFICIAL.get(alias, alias).value


# Backward compatibility functions
def resolve(alias: Optional[str] = None) -> str:
    """Convert a friendly alias to the exact OpenAI model name."""
    return to_official(alias)


def get_default_model() -> str:
    """Get the default model ID."""
    return Model.DEFAULT.value


def get_available_aliases() -> list[str]:
    """Get list of all available model aliases."""
    return [model.value for model in Model]


def get_official_models() -> list[str]:
    """Get list of all official OpenAI model IDs used."""
    return list(set(_ALIAS_TO_OFFICIAL.values()))


def is_valid_alias(alias: str) -> bool:
    """Check if an alias is valid."""
    try:
        Model(alias)
        return True
    except ValueError:
        return False 