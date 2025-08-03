"""MemoryRouter - DEPRECATED

This module is deprecated. Use utils.memory_manager instead for unified memory management.
This file is kept for backward compatibility but redirects to the new system.
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Unified helpers (always use global MemoryManager)
# ---------------------------------------------------------------------

from utils.memory_manager import get_global_memory_manager
logger.info("Using global memory manager")

def store_short(session_id: str, role: str, content: str) -> None:
    """Persist short‑term memory (e.g., Redis) via MemoryManager."""
    mm = get_global_memory_manager()
    mm.add_short_term(session_id, role, content)

def get_short(session_id: str) -> List[str]:
    """Retrieve recent messages from short‑term memory."""
    mm = get_global_memory_manager()
    memories = mm.get_short_term(session_id, limit=20)
    return [m.get("content", "") for m in memories]

def store_long(session_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """Persist long‑term memory (vector DB)."""
    mm = get_global_memory_manager()
    mm.add_long_term("long_term", session_id, content, metadata or {})

def retrieve_relevant(session_id: str, query: str, k: int = 3) -> List[str]:
    """Semantic search over long‑term memory."""
    mm = get_global_memory_manager()
    memories = mm.get_relevant_memories(query, namespace="long_term", top_k=k)
    return [m.get("content", "") for m in memories]

logger.warning("Using deprecated memory_router.py - migrate to utils.memory_manager")
