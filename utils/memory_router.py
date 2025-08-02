"""MemoryRouter - DEPRECATED

This module is deprecated. Use utils.memory_manager instead for unified memory management.
This file is kept for backward compatibility but redirects to the new system.
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Import the new unified memory manager
try:
    from utils.memory_manager import MemoryManager, store_short, store_long, get_short, get_relevant_memories
    logger.info("Using unified memory manager")
except ImportError as e:
    logger.error(f"Failed to import unified memory manager: {e}")
    # Fallback to old implementation
    from memory import save_to_memory, query_memory
    
    def store_short(session_id: str, role: str, content: str) -> None:
        """Fallback: Store in file-based memory."""
        save_to_memory("short_term", f"{session_id}_{role}", content)
    
    def get_short(session_id: str) -> List[str]:
        """Fallback: Get from file-based memory."""
        results = query_memory("short_term", session_id, top_k=20)
        return [r.get("content", "") for r in results]
    
    def store_long(session_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Fallback: Store in file-based memory."""
        save_to_memory("long_term", f"{session_id}", content, metadata)
    
    def retrieve_relevant(session_id: str, query: str, k: int = 3) -> List[str]:
        """Fallback: Query from file-based memory."""
        results = query_memory("long_term", query, top_k=k)
        return [r.get("content", "") for r in results]

logger.warning("Using deprecated memory_router.py - migrate to utils.memory_manager")
