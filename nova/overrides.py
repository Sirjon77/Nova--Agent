"""
nova.overrides
================

This module provides a simple mechanism for operators to override the
automatic governance decisions made by the Nova Agent. Overrides are
persisted to a JSON file on disk and can be used to force certain
channels to be retired or promoted, or to ignore retire/promote flags
for a channel. The available override directives are:

* ``force_retire`` – Always retire the channel regardless of score.
* ``force_promote`` – Always promote the channel regardless of score.
* ``ignore_retire`` – Suppress a retire flag if one would normally be set.
* ``ignore_promote`` – Suppress a promote flag if one would normally be set.

Overrides are stored in a dictionary keyed by ``channel_id``. The JSON
structure on disk looks like::

    {
        "channelA": "force_retire",
        "channelB": "ignore_promote"
    }

This file is loaded on each governance run to apply overrides, and
updated whenever an operator sets or clears an override via the API.

Note: this module deliberately avoids importing any FastAPI or other
framework‑specific modules so that it can be reused in the governance
loop without introducing circular dependencies.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Optional

log = logging.getLogger(__name__)

# Define valid override directives
VALID_OVERRIDES = {
    "force_retire",
    "force_promote",
    "ignore_retire",
    "ignore_promote",
}

def _overrides_file() -> Path:
    """Return the path to the overrides JSON file.

    The file is located in the ``config`` directory relative to the
    project root. If the file does not exist, it will be created on
    first write. Consumers should ensure the parent directory exists.

    Returns:
        Path object pointing to ``config/overrides.json``.
    """
    # Use Path.cwd() to find project root; fall back to current working dir
    base = Path('config')
    return base / 'overrides.json'


def load_overrides() -> Dict[str, str]:
    """Load all overrides from disk.

    Returns an empty dict if the overrides file does not exist or cannot be
    parsed. Invalid override directives will be filtered out.

    Returns:
        Dictionary mapping channel IDs to override directives.
    """
    path = _overrides_file()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            raise ValueError("Overrides file must contain a JSON object")
    except Exception as exc:
        log.warning("Failed to read overrides file %s: %s", path, exc)
        return {}
    overrides: Dict[str, str] = {}
    for channel_id, directive in data.items():
        if directive in VALID_OVERRIDES:
            overrides[channel_id] = directive
        else:
            log.warning("Invalid override directive '%s' for channel %s", directive, channel_id)
    return overrides


def get_override(channel_id: str) -> Optional[str]:
    """Return the override directive for a given channel, if any.

    Args:
        channel_id: Identifier of the channel.

    Returns:
        The override directive as a string, or ``None`` if no override is set.
    """
    overrides = load_overrides()
    return overrides.get(channel_id)


def _save_overrides(overrides: Dict[str, str]) -> None:
    """Persist overrides to disk.

    Creates the overrides file parent directory if it does not exist. The
    file is written atomically by writing to a temporary file and then
    renaming. This reduces the risk of corruption if the process is
    interrupted during write.

    Args:
        overrides: Dictionary of overrides to persist.
    """
    path = _overrides_file()
    # ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix('.tmp')
    try:
        tmp_path.write_text(json.dumps(overrides, indent=2))
        tmp_path.rename(path)
    except Exception as exc:
        log.error("Failed to write overrides file %s: %s", path, exc)


def set_override(channel_id: str, directive: str) -> None:
    """Set or update an override for a channel.

    Args:
        channel_id: The channel identifier.
        directive: One of the values in ``VALID_OVERRIDES``.

    Raises:
        ValueError: If the directive is not valid.
    """
    if directive not in VALID_OVERRIDES:
        raise ValueError(f"Invalid override directive: {directive}")
    overrides = load_overrides()
    overrides[channel_id] = directive
    _save_overrides(overrides)


def clear_override(channel_id: str) -> None:
    """Remove an override for a channel, if it exists.

    Args:
        channel_id: Identifier of the channel whose override should be removed.
    """
    overrides = load_overrides()
    if channel_id in overrides:
        overrides.pop(channel_id)
        _save_overrides(overrides)