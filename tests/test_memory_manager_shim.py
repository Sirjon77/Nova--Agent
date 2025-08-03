"""
Unit tests for memory manager shim (legacy adapter).
"""

import pytest
from unittest.mock import patch, MagicMock

from memory.legacy_adapter import save_to_memory, query_memory, fetch_from_memory, is_memory_available, get_memory_status


def test_legacy_shim_routes(monkeypatch):
    """Test that legacy shim routes calls to MemoryManager."""
    called = {"short": False, "long": False, "query": False, "status": False, "available": False}

    class StubMgr:
        def add_long_term(self, namespace, key, content, metadata=None):
            called["long"] = True
            return True

        def get_relevant_memories(self, query, namespace="global", top_k=5):
            called["query"] = True
            return [{"doc": "ok"}]

        def get_memory_status(self):
            called["status"] = True
            return {"fully_available": True}

        def is_available(self):
            called["available"] = True
            return True

    monkeypatch.setattr(
        "memory.legacy_adapter._mgr", lambda: StubMgr()
    )

    # Test save_to_memory routes to add_long_term
    save_to_memory("test_namespace", "test_key", "test_content")
    assert called["long"]

    # Test query_memory routes to get_relevant_memories
    result = query_memory("test_namespace", "test_query")
    assert called["query"]
    assert result == [{"doc": "ok"}]

    # Test fetch_from_memory routes to get_relevant_memories
    result = fetch_from_memory("test_query")
    assert result == [{"doc": "ok"}]

    # Test is_memory_available routes to is_available
    result = is_memory_available()
    assert called["available"]
    assert result is True

    # Test get_memory_status routes to get_memory_status
    result = get_memory_status()
    assert called["status"]
    assert result["fully_available"] is True


def test_legacy_shim_deprecation_warnings():
    """Test that legacy functions emit deprecation warnings."""
    with pytest.warns(DeprecationWarning, match="save_to_memory.*deprecated"):
        save_to_memory("test", "test", "test")

    with pytest.warns(DeprecationWarning, match="query_memory.*deprecated"):
        query_memory("test", "test")

    with pytest.warns(DeprecationWarning, match="fetch_from_memory.*deprecated"):
        fetch_from_memory("test")

    with pytest.warns(DeprecationWarning, match="is_memory_available.*deprecated"):
        is_memory_available()

    with pytest.warns(DeprecationWarning, match="get_memory_status.*deprecated"):
        get_memory_status()


def test_legacy_shim_singleton_manager():
    """Test that the shim uses a singleton manager."""
    from memory.legacy_adapter import _mgr
    
    manager1 = _mgr()
    manager2 = _mgr()
    
    assert manager1 is manager2 