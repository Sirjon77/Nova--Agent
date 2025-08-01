"""
Automation flags for Nova Agent.

This module manages global toggles that control certain automated
behaviours of the system, such as whether posting or content
generation is enabled and whether approval is required before
publishing. Flags are persisted to a JSON file (by default
``config/automation_flags.json``) so that they survive process
restarts. Thread‑safe read and update functions are provided.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict

_lock = threading.Lock()

# Location of the flags file. Relative to the project root.
STATE_FILE = Path(os.getenv("AUTOMATION_FLAGS_FILE", "config/automation_flags.json"))

# Default flag values. New flags should be added here with sensible defaults.
DEFAULTS: Dict[str, Any] = {
    "posting_enabled": True,
    "generation_enabled": True,
    "require_approval": False,
}


def _load_state() -> Dict[str, Any]:
    """Read the current automation flags from disk.

    If the state file does not exist or is invalid, a copy of
    ``DEFAULTS`` is returned. Unknown keys are ignored and missing keys
    are filled with default values.
    """
    with _lock:
        try:
            data = json.loads(STATE_FILE.read_text())
        except Exception:
            data = {}
        # Merge defaults
        state: Dict[str, Any] = DEFAULTS.copy()
        for key, value in data.items():
            if key in DEFAULTS:
                state[key] = value
        return state


def _save_state(state: Dict[str, Any]) -> None:
    """Write the given state dictionary to disk.

    Ensures that the parent directory exists before writing.
    """
    with _lock:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2))


def get_flags() -> Dict[str, Any]:
    """Return a copy of the current automation flags."""
    return _load_state().copy()


def set_flags(**kwargs: Any) -> Dict[str, Any]:
    """Update one or more automation flags.

    Args:
        **kwargs: Keyword arguments mapping flag names to new values.

    Returns:
        The updated state after applying the changes.

    Raises:
        KeyError: If an unknown flag name is provided.
    """
    state = _load_state()
    for key, value in kwargs.items():
        if key not in DEFAULTS:
            raise KeyError(f"Unknown automation flag: {key}")
        state[key] = bool(value) if isinstance(DEFAULTS[key], bool) else value
    _save_state(state)
    return state.copy()


def is_posting_enabled() -> bool:
    """Return True if automated posting is currently enabled."""
    return bool(_load_state()["posting_enabled"])


def set_posting_enabled(value: bool) -> Dict[str, Any]:
    """Set the posting_enabled flag."""
    return set_flags(posting_enabled=value)


def is_generation_enabled() -> bool:
    """Return True if automated content generation is currently enabled."""
    return bool(_load_state()["generation_enabled"])


def set_generation_enabled(value: bool) -> Dict[str, Any]:
    """Set the generation_enabled flag."""
    return set_flags(generation_enabled=value)


def is_approval_required() -> bool:
    """Return True if content approval is required before publishing."""
    return bool(_load_state()["require_approval"])


def set_approval_required(value: bool) -> Dict[str, Any]:
    """Set the require_approval flag."""
    return set_flags(require_approval=value)