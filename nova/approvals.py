"""
Pending approvals management for Nova Agent.

This module provides an interface for storing, listing and processing
content items that require human approval before publishing. When the
`require_approval` automation flag is enabled, integrations will
defer posting and instead create a draft entry using ``add_draft``.
Operators can retrieve pending drafts via the API and either approve
them (which triggers the posting) or reject them (discarding the
content).

Drafts are persisted to a JSON file to survive process restarts. Each
draft entry contains at minimum the following keys:

* ``id``: a unique identifier (UUID4 string)
* ``provider``: the name of the integration module (e.g. ``publer``,
  ``youtube``, ``instagram``)
* ``function``: the function name within the provider to call upon
  approval (e.g. ``schedule_post``, ``publish_video``)
* ``args``: a list of positional arguments used when calling the
  function
* ``kwargs``: a dict of keyword arguments used when calling the
  function
* ``metadata``: optional free‑form metadata such as channel ID,
  timestamp or description for display in the UI

Callers should avoid storing sensitive information in drafts as
contents may be visible to operators via the dashboard.

Thread safety: This module uses a threading lock to protect read
and write operations. However, if multiple processes write to the
same file concurrently race conditions may occur. In a multi‑process
deployment consider using a database or other central store instead.
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

_lock = threading.Lock()

# Location of the approvals file. Configurable via environment variable.
STATE_FILE = Path(os.getenv("APPROVALS_FILE", "data/pending_approvals.json"))


def _load() -> List[Dict[str, Any]]:
    """Load the list of pending drafts from disk.

    Returns an empty list if the file does not exist or cannot be
    parsed. Each draft is a dict as described in the module docstring.
    """
    with _lock:
        try:
            data = json.loads(STATE_FILE.read_text())
            if isinstance(data, list):
                return data
            return []
        except Exception:
            return []


def _save(drafts: List[Dict[str, Any]]) -> None:
    """Persist the list of drafts to disk.

    Ensures the parent directory exists before writing. Writes a
    formatted JSON file for human readability.
    """
    with _lock:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(drafts, indent=2))


def list_drafts() -> List[Dict[str, Any]]:
    """Return a list of all pending approval drafts.

    Each draft is returned as stored; consumers should treat the
    returned list as read‑only.
    """
    return _load()


def add_draft(
    provider: str,
    function: str,
    *,
    args: Optional[List[Any]] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Add a new draft to the pending approvals list.

    Args:
        provider: Name of the integration provider/module.
        function: Name of the function to call upon approval.
        args: Positional arguments for the function.
        kwargs: Keyword arguments for the function.
        metadata: Optional metadata for display (e.g. channel id).

    Returns:
        The unique identifier of the created draft.
    """
    drafts = _load()
    draft_id = str(uuid.uuid4())
    entry: Dict[str, Any] = {
        "id": draft_id,
        "provider": provider,
        "function": function,
        "args": args or [],
        "kwargs": kwargs or {},
        "metadata": metadata or {},
        "created_at": datetime.utcnow().isoformat(),
    }
    drafts.append(entry)
    _save(drafts)
    return draft_id


def get_draft(draft_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single draft by its identifier.

    Args:
        draft_id: The unique ID of the draft to fetch.

    Returns:
        The draft dictionary if found, otherwise None.
    """
    drafts = _load()
    for d in drafts:
        if d.get("id") == draft_id:
            return d
    return None


def _remove_draft(draft_id: str) -> Optional[Dict[str, Any]]:
    """Remove a draft from storage and return it.

    Returns the removed draft if present, else None.
    """
    drafts = _load()
    for i, d in enumerate(drafts):
        if d.get("id") == draft_id:
            removed = drafts.pop(i)
            _save(drafts)
            return removed
    return None


def approve_draft(draft_id: str) -> Optional[Dict[str, Any]]:
    """Mark a draft as approved and remove it from the pending list.

    This does not perform the actual posting; callers are responsible
    for invoking the associated integration function using the stored
    ``provider`` and ``function``.

    Args:
        draft_id: Identifier of the draft to approve.

    Returns:
        The removed draft dictionary if found, else None.
    """
    return _remove_draft(draft_id)


def reject_draft(draft_id: str) -> Optional[Dict[str, Any]]:
    """Discard a draft without posting it.

    Args:
        draft_id: Identifier of the draft to reject.

    Returns:
        The removed draft dictionary if found, else None.
    """
    return _remove_draft(draft_id)