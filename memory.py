"""
Memory Management System for Nova Agent - DEPRECATED

This module is deprecated. Use utils.memory_manager.MemoryManager instead.
This file is kept for backward compatibility but will be removed in Nova v8.0.
"""

import warnings
from typing import Optional, Dict, Any, List

def save_to_memory(namespace: str, key: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """
    ⚠️ DEPRECATED. Will be removed in Nova v8.0.
    Use MemoryManager.add_long_term instead.
    """
    warnings.warn(
        "save_to_memory is deprecated; use MemoryManager.add_long_term", 
        DeprecationWarning, 
        stacklevel=2
    )
    
    try:
        from utils.memory_manager import get_global_memory_manager
        mm = get_global_memory_manager()
        mm.add_long_term(namespace, key, content, metadata or {})
        return True
    except Exception as e:
        print(f"Warning: Failed to save to memory via manager: {e}")
        return False

def query_memory(namespace: str, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    ⚠️ DEPRECATED. Will be removed in Nova v8.0.
    Use MemoryManager.get_relevant_memories instead.
    """
    warnings.warn(
        "query_memory is deprecated; use MemoryManager.get_relevant_memories", 
        DeprecationWarning, 
        stacklevel=2
    )
    
    try:
        from utils.memory_manager import get_global_memory_manager
        mm = get_global_memory_manager()
        return mm.get_relevant_memories(query_text, namespace=namespace, limit=top_k)
    except Exception as e:
        print(f"Warning: Failed to query memory via manager: {e}")
        return []

def is_memory_available() -> bool:
    """
    ⚠️ DEPRECATED. Will be removed in Nova v8.0.
    Use MemoryManager.is_available instead.
    """
    warnings.warn(
        "is_memory_available is deprecated; use MemoryManager.is_available", 
        DeprecationWarning, 
        stacklevel=2
    )
    
    try:
        from utils.memory_manager import get_global_memory_manager
        mm = get_global_memory_manager()
        return mm.is_available()
    except Exception:
        return False

def get_memory_status() -> Dict[str, Any]:
    """
    ⚠️ DEPRECATED. Will be removed in Nova v8.0.
    Use MemoryManager.get_status instead.
    """
    warnings.warn(
        "get_memory_status is deprecated; use MemoryManager.get_status", 
        DeprecationWarning, 
        stacklevel=2
    )
    
    try:
        from utils.memory_manager import get_global_memory_manager
        mm = get_global_memory_manager()
        return mm.get_status()
    except Exception as e:
        return {
            "fully_available": False,
            "error": str(e),
            "weaviate_available": False,
            "redis_available": False
        }