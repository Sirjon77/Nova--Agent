import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from utils.memory_manager import MemoryManager

class TestMemoryManagerEnhanced:
    def test_redis_fallback_when_unavailable(self, mock_redis):
        """Test memory manager falls back to file storage when Redis unavailable."""
        # Mock Redis to be unavailable
        mock_redis.ping.return_value = False
        
        with tempfile.TemporaryDirectory() as temp_dir:
            mm = MemoryManager(
                short_term_dir=temp_dir,
                long_term_dir=temp_dir
            )
            
            # Should still work with file storage
            mm.store_short("test_key", {"data": "test_value"})
            result = mm.get_short("test_key")
            assert result == {"data": "test_value"}

    def test_error_handling_with_invalid_data(self):
        """Test memory manager handles errors gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mm = MemoryManager(
                short_term_dir=temp_dir,
                long_term_dir=temp_dir
            )
            
            # Test with None data
            result = mm.store_short("test_key", None)
            assert result is False
            
            # Test with invalid JSON data
            result = mm.store_short("test_key", {"data": object()})  # Non-serializable
            assert result is False

    def test_memory_cleanup_old_entries(self):
        """Test cleanup of old memory entries."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mm = MemoryManager(
                short_term_dir=temp_dir,
                long_term_dir=temp_dir
            )
            
            # Add some test memories
            mm.store_short("old_key", {"data": "old_value", "timestamp": 0})
            mm.store_short("new_key", {"data": "new_value", "timestamp": 999999999})
            
            # Run cleanup
            mm.cleanup_old_memories(max_age_days=1)
            
            # Old memory should be removed
            old_result = mm.get_short("old_key")
            new_result = mm.get_short("new_key")
            
            assert old_result is None
            assert new_result is not None

    def test_memory_search_functionality(self):
        """Test memory search functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mm = MemoryManager(
                short_term_dir=temp_dir,
                long_term_dir=temp_dir
            )
            
            # Add memories with searchable content
            mm.store_short("key1", {"content": "python programming", "tags": ["coding"]})
            mm.store_short("key2", {"content": "machine learning", "tags": ["ai"]})
            mm.store_short("key3", {"content": "python testing", "tags": ["coding"]})
            
            # Search for python-related memories
            results = mm.search_memories("python")
            assert len(results) == 2
            assert any("programming" in result["content"] for result in results)
            assert any("testing" in result["content"] for result in results)

    def test_memory_tagging_system(self):
        """Test memory tagging system."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mm = MemoryManager(
                short_term_dir=temp_dir,
                long_term_dir=temp_dir
            )
            
            # Add memories with tags
            mm.store_short("key1", {"content": "test1", "tags": ["important", "urgent"]})
            mm.store_short("key2", {"content": "test2", "tags": ["important"]})
            mm.store_short("key3", {"content": "test3", "tags": ["urgent"]})
            
            # Get memories by tag
            important_memories = mm.get_memories_by_tag("important")
            urgent_memories = mm.get_memories_by_tag("urgent")
            
            assert len(important_memories) == 2
            assert len(urgent_memories) == 2

    def test_memory_statistics(self):
        """Test memory statistics functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mm = MemoryManager(
                short_term_dir=temp_dir,
                long_term_dir=temp_dir
            )
            
            # Add some memories
            mm.store_short("key1", {"data": "value1"})
            mm.store_short("key2", {"data": "value2"})
            mm.store_long("long_key1", {"data": "long_value1"})
            
            stats = mm.get_statistics()
            
            assert stats["short_term_count"] == 2
            assert stats["long_term_count"] == 1
            assert stats["total_count"] == 3

    def test_memory_export_import(self):
        """Test memory export and import functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mm = MemoryManager(
                short_term_dir=temp_dir,
                long_term_dir=temp_dir
            )
            
            # Add memories
            mm.store_short("key1", {"data": "value1"})
            mm.store_long("long_key1", {"data": "long_value1"})
            
            # Export memories
            export_data = mm.export_memories()
            
            # Create new memory manager and import
            with tempfile.TemporaryDirectory() as new_temp_dir:
                new_mm = MemoryManager(
                    short_term_dir=new_temp_dir,
                    long_term_dir=new_temp_dir
                )
                
                new_mm.import_memories(export_data)
                
                # Verify memories were imported
                assert new_mm.get_short("key1") == {"data": "value1"}
                assert new_mm.get_long("long_key1") == {"data": "long_value1"}

    def test_concurrent_memory_access(self):
        """Test concurrent access to memory manager."""
        import threading
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            mm = MemoryManager(
                short_term_dir=temp_dir,
                long_term_dir=temp_dir
            )
            
            def write_memories(thread_id):
                for i in range(10):
                    mm.store_short(f"thread_{thread_id}_key_{i}", {"data": f"value_{i}"})
                    time.sleep(0.01)
            
            def read_memories(thread_id):
                for i in range(10):
                    mm.get_short(f"thread_{thread_id}_key_{i}")
                    time.sleep(0.01)
            
            # Start multiple threads
            threads = []
            for i in range(3):
                t1 = threading.Thread(target=write_memories, args=(i,))
                t2 = threading.Thread(target=read_memories, args=(i,))
                threads.extend([t1, t2])
                t1.start()
                t2.start()
            
            # Wait for all threads to complete
            for t in threads:
                t.join()
            
            # Verify no data corruption occurred
            stats = mm.get_statistics()
            assert stats["short_term_count"] == 30  # 3 threads * 10 memories each 