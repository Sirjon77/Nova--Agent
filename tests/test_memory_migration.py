"""
Unit tests for memory migration from legacy save_to_memory to MemoryManager.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from utils.memory_manager import get_global_memory_manager, MemoryManager
from memory import save_to_memory, query_memory, is_memory_available, get_memory_status


class TestMemoryMigration:
    """Test the migration from legacy memory functions to MemoryManager."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        temp_dir = tempfile.mkdtemp()
        short_term_dir = Path(temp_dir) / "short_term"
        long_term_dir = Path(temp_dir) / "long_term"
        log_dir = Path(temp_dir) / "logs"
        summaries_dir = Path(temp_dir) / "summaries"
        
        for dir_path in [short_term_dir, long_term_dir, log_dir, summaries_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        yield {
            "short_term": str(short_term_dir),
            "long_term": str(long_term_dir),
            "log": str(log_dir),
            "summaries": str(summaries_dir)
        }
        
        shutil.rmtree(temp_dir)
    
    def test_deprecated_save_to_memory_warning(self):
        """Test that save_to_memory emits deprecation warning."""
        with pytest.warns(DeprecationWarning, match="save_to_memory is deprecated"):
            save_to_memory("test_namespace", "test_key", "test_content")
    
    def test_deprecated_query_memory_warning(self):
        """Test that query_memory emits deprecation warning."""
        with pytest.warns(DeprecationWarning, match="query_memory is deprecated"):
            query_memory("test_namespace", "test_query")
    
    def test_deprecated_is_memory_available_warning(self):
        """Test that is_memory_available emits deprecation warning."""
        with pytest.warns(DeprecationWarning, match="is_memory_available is deprecated"):
            is_memory_available()
    
    def test_deprecated_get_memory_status_warning(self):
        """Test that get_memory_status emits deprecation warning."""
        with pytest.warns(DeprecationWarning, match="get_memory_status is deprecated"):
            get_memory_status()
    
    def test_global_memory_manager_singleton(self):
        """Test that get_global_memory_manager returns the same instance."""
        mm1 = get_global_memory_manager()
        mm2 = get_global_memory_manager()
        assert mm1 is mm2
    
    def test_memory_manager_initialization(self, temp_dirs):
        """Test MemoryManager initialization with custom directories."""
        mm = MemoryManager(
            short_term_dir=temp_dirs["short_term"],
            long_term_dir=temp_dirs["long_term"],
            log_dir=temp_dirs["log"],
            summaries_dir=temp_dirs["summaries"]
        )
        
        assert mm.short_term_dir.exists()
        assert mm.long_term_dir.exists()
        assert mm.log_dir.exists()
        assert mm.summaries_dir.exists()
    
    def test_add_long_term_memory(self, temp_dirs):
        """Test adding long-term memory."""
        mm = MemoryManager(
            short_term_dir=temp_dirs["short_term"],
            long_term_dir=temp_dirs["long_term"],
            log_dir=temp_dirs["log"],
            summaries_dir=temp_dirs["summaries"]
        )
        
        result = mm.add_long_term("test_namespace", "test_key", "test_content", {"test": "metadata"})
        assert result is True
        
        # Verify file was created
        namespace_file = Path(temp_dirs["long_term"]) / "test_namespace.json"
        assert namespace_file.exists()
    
    def test_get_relevant_memories(self, temp_dirs):
        """Test retrieving relevant memories."""
        mm = MemoryManager(
            short_term_dir=temp_dirs["short_term"],
            long_term_dir=temp_dirs["long_term"],
            log_dir=temp_dirs["log"],
            summaries_dir=temp_dirs["summaries"]
        )
        
        # Add some test memories
        mm.add_long_term("test_namespace", "key1", "content about python programming")
        mm.add_long_term("test_namespace", "key2", "content about machine learning")
        mm.add_long_term("test_namespace", "key3", "content about web development")
        
        # Search for relevant memories
        results = mm.get_relevant_memories("python", "test_namespace", top_k=2)
        assert len(results) > 0
        assert any("python" in result.get("content", "").lower() for result in results)
    
    def test_add_short_term_memory(self, temp_dirs):
        """Test adding short-term memory."""
        mm = MemoryManager(
            short_term_dir=temp_dirs["short_term"],
            long_term_dir=temp_dirs["long_term"],
            log_dir=temp_dirs["log"],
            summaries_dir=temp_dirs["summaries"]
        )
        
        result = mm.add_short_term("test_session", "user", "test message")
        assert result is True
        
        # Verify file was created
        session_file = Path(temp_dirs["short_term"]) / "test_session.json"
        assert session_file.exists()
    
    def test_get_short_term_memory(self, temp_dirs):
        """Test retrieving short-term memory."""
        mm = MemoryManager(
            short_term_dir=temp_dirs["short_term"],
            long_term_dir=temp_dirs["long_term"],
            log_dir=temp_dirs["log"],
            summaries_dir=temp_dirs["summaries"]
        )
        
        # Add some test messages
        mm.add_short_term("test_session", "user", "hello")
        mm.add_short_term("test_session", "assistant", "hi there")
        mm.add_short_term("test_session", "user", "how are you?")
        
        # Retrieve messages
        messages = mm.get_short_term("test_session", limit=5)
        assert len(messages) == 3
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "hello"
    
    def test_memory_status(self, temp_dirs):
        """Test memory status reporting."""
        mm = MemoryManager(
            short_term_dir=temp_dirs["short_term"],
            long_term_dir=temp_dirs["long_term"],
            log_dir=temp_dirs["log"],
            summaries_dir=temp_dirs["summaries"]
        )
        
        status = mm.get_memory_status()
        assert "redis_available" in status
        assert "weaviate_available" in status
        assert "fully_available" in status
        assert "short_term_count" in status
        assert "long_term_count" in status
    
    def test_is_available(self, temp_dirs):
        """Test memory availability check."""
        mm = MemoryManager(
            short_term_dir=temp_dirs["short_term"],
            long_term_dir=temp_dirs["long_term"],
            log_dir=temp_dirs["log"],
            summaries_dir=temp_dirs["summaries"]
        )
        
        # Should be available even without Redis/Weaviate (file fallback)
        assert mm.is_available() is True
    
    @patch('utils.memory_manager.redis.Redis')
    def test_redis_integration(self, mock_redis, temp_dirs):
        """Test Redis integration when available."""
        # Mock Redis to be available
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis.return_value = mock_redis_instance
        
        mm = MemoryManager(
            short_term_dir=temp_dirs["short_term"],
            long_term_dir=temp_dirs["long_term"],
            log_dir=temp_dirs["log"],
            summaries_dir=temp_dirs["summaries"]
        )
        
        assert mm.redis_available is True
        assert mm.is_available() is True
    
    def test_cleanup_old_memories(self, temp_dirs):
        """Test cleanup of old memories."""
        mm = MemoryManager(
            short_term_dir=temp_dirs["short_term"],
            long_term_dir=temp_dirs["long_term"],
            log_dir=temp_dirs["log"],
            summaries_dir=temp_dirs["summaries"]
        )
        
        # Add some memories
        mm.add_short_term("test_session", "user", "test message")
        mm.add_long_term("test_namespace", "test_key", "test content")
        
        # Clean up (should not remove recent memories)
        cleaned = mm.cleanup_old_memories(days=1)
        assert cleaned >= 0  # Should not fail
    
    def test_error_handling(self, temp_dirs):
        """Test error handling in memory operations."""
        mm = MemoryManager(
            short_term_dir=temp_dirs["short_term"],
            long_term_dir=temp_dirs["long_term"],
            log_dir=temp_dirs["log"],
            summaries_dir=temp_dirs["summaries"]
        )
        
        # Test with invalid inputs
        result = mm.add_long_term("", "", "")  # Empty inputs
        assert result is False  # Should handle gracefully
        
        result = mm.get_relevant_memories("", "", top_k=-1)  # Invalid top_k
        assert isinstance(result, list)  # Should return empty list


if __name__ == "__main__":
    pytest.main([__file__]) 