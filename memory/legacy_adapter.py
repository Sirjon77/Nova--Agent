# memory/legacy_adapter.py
# TEMPORARY SHIM ──────────────────────────────────────────────────────────────
"""
Bridges legacy `memory.save_to_memory()` style calls to the new MemoryManager.
❗ Delete this file once every caller is migrated and grep returns zero hits.

Usage pattern in legacy modules stays the same until refactor is done:
    from memory.legacy_adapter import save_to_memory, fetch_from_memory
"""
from warnings import warn
from typing import Optional, Dict, Any, List

from utils.memory_manager import get_global_memory_manager  # new subsystem

_manager = None


def _mgr():
    global _manager
    if _manager is None:
        _manager = get_global_memory_manager()
    return _manager


# ---- Legacy façades --------------------------------------------------------


def save_to_memory(namespace: str, key: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Legacy façade → routes to MemoryManager.add_long_term."""
    warn(
        "save_to_memory() is deprecated. Import MemoryManager instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _mgr().add_long_term(namespace, key, content, metadata or {})


def query_memory(namespace: str, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Legacy façade → routes to MemoryManager.get_relevant_memories."""
    warn(
        "query_memory() is deprecated. Import MemoryManager instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _mgr().get_relevant_memories(query_text, namespace=namespace, top_k=top_k)


def fetch_from_memory(query: str, *, top_k: int = 5):
    """Legacy façade → routes to MemoryManager.query()."""
    warn(
        "fetch_from_memory() is deprecated. Import MemoryManager instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _mgr().get_relevant_memories(query, namespace="global", top_k=top_k)


def is_memory_available() -> bool:
    """Legacy façade → routes to MemoryManager.is_available."""
    warn(
        "is_memory_available() is deprecated. Import MemoryManager instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _mgr().is_available()


def get_memory_status() -> Dict[str, Any]:
    """Legacy façade → routes to MemoryManager.get_memory_status."""
    warn(
        "get_memory_status() is deprecated. Import MemoryManager instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _mgr().get_memory_status() 