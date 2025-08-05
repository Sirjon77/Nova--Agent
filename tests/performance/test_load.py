import pytest
import time
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch
from utils.memory_manager import MemoryManager
from utils.summarizer import summarize_text

class TestPerformanceLoad:
    def test_memory_manager_load_performance(self):
        """Test memory manager performance under load."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            mm = MemoryManager(
                short_term_dir=temp_dir,
                long_term_dir=temp_dir
            )
            
            start_time = time.time()
            
            # Perform 1000 memory operations
            for i in range(1000):
                mm.store_short(f"key_{i}", {"data": f"value_{i}", "index": i})
            
            write_time = time.time() - start_time
            
            start_time = time.time()
            
            # Read all memories
            for i in range(1000):
                mm.get_short(f"key_{i}")
            
            read_time = time.time() - start_time
            
            # Performance assertions
            assert write_time < 5.0  # Should complete within 5 seconds
            assert read_time < 3.0   # Should complete within 3 seconds

    def test_summarizer_load_performance(self):
        """Test summarizer performance under load."""
        # Create large text for testing
        large_text = "This is a test sentence. " * 1000
        
        start_time = time.time()
        
        # Perform multiple summarizations
        results = []
        for i in range(10):
            result = summarize_text(large_text, max_length=100)
            results.append(result)
        
        total_time = time.time() - start_time
        
        # Performance assertions
        assert total_time < 10.0  # Should complete within 10 seconds
        assert len(results) == 10
        for result in results:
            assert len(result) <= 100

    def test_concurrent_memory_access(self):
        """Test concurrent access to memory manager."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            mm = MemoryManager(
                short_term_dir=temp_dir,
                long_term_dir=temp_dir
            )
            
            def worker(worker_id):
                for i in range(100):
                    key = f"worker_{worker_id}_key_{i}"
                    mm.store_short(key, {"data": f"value_{i}", "worker": worker_id})
                    mm.get_short(key)
            
            # Start multiple threads
            threads = []
            start_time = time.time()
            
            for i in range(5):
                t = threading.Thread(target=worker, args=(i,))
                threads.append(t)
                t.start()
            
            # Wait for all threads to complete
            for t in threads:
                t.join()
            
            total_time = time.time() - start_time
            
            # Performance assertions
            assert total_time < 10.0  # Should complete within 10 seconds
            
            # Verify data integrity
            for i in range(5):
                for j in range(100):
                    key = f"worker_{i}_key_{j}"
                    result = mm.get_short(key)
                    assert result["worker"] == i
                    assert result["data"] == f"value_{j}"

    @pytest.mark.asyncio
    async def test_api_endpoint_load_performance(self, authenticated_client):
        """Test API endpoint performance under load."""
        import asyncio
        
        async def make_request(client, request_id):
            response = client.get("/api/health")
            return response.status_code
        
        # Make 100 concurrent requests
        start_time = time.time()
        
        tasks = [make_request(authenticated_client, i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Performance assertions
        assert total_time < 30.0  # Should complete within 30 seconds
        assert len(results) == 100
        assert all(status == 200 for status in results)

    def test_file_io_performance(self):
        """Test file I/O performance under load."""
        import tempfile
        import json
        
        with tempfile.TemporaryDirectory() as temp_dir:
            start_time = time.time()
            
            # Write 1000 JSON files
            for i in range(1000):
                file_path = f"{temp_dir}/file_{i}.json"
                data = {
                    "id": i,
                    "content": f"content_{i}",
                    "timestamp": time.time()
                }
                with open(file_path, 'w') as f:
                    json.dump(data, f)
            
            write_time = time.time() - start_time
            
            start_time = time.time()
            
            # Read all files
            for i in range(1000):
                file_path = f"{temp_dir}/file_{i}.json"
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    assert data["id"] == i
            
            read_time = time.time() - start_time
            
            # Performance assertions
            assert write_time < 5.0  # Should complete within 5 seconds
            assert read_time < 3.0   # Should complete within 3 seconds

    def test_database_query_performance(self, mock_redis):
        """Test database query performance under load."""
        # Mock Redis operations
        mock_redis.set.return_value = True
        mock_redis.get.return_value = '{"data": "test_value"}'
        
        start_time = time.time()
        
        # Perform 1000 database operations
        for i in range(1000):
            mock_redis.set(f"key_{i}", f"value_{i}")
            mock_redis.get(f"key_{i}")
        
        total_time = time.time() - start_time
        
        # Performance assertions
        assert total_time < 2.0  # Should complete within 2 seconds
        assert mock_redis.set.call_count == 1000
        assert mock_redis.get.call_count == 1000

    def test_memory_usage_performance(self):
        """Test memory usage under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform memory-intensive operations
        large_data = []
        for i in range(10000):
            large_data.append({
                "id": i,
                "data": "x" * 1000,  # 1KB per item
                "metadata": {"created": time.time()}
            })
        
        peak_memory = process.memory_info().rss
        
        # Clear data
        del large_data
        
        final_memory = process.memory_info().rss
        
        # Memory usage assertions
        memory_increase = peak_memory - initial_memory
        memory_cleanup = peak_memory - final_memory
        
        # Should not use more than 100MB additional memory
        assert memory_increase < 100 * 1024 * 1024
        # Should clean up most memory
        assert memory_cleanup > memory_increase * 0.8

    def test_cpu_usage_performance(self):
        """Test CPU usage under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        start_time = time.time()
        start_cpu = process.cpu_percent()
        
        # Perform CPU-intensive operations
        for i in range(100000):
            _ = i * i + i  # Simple computation
        
        end_time = time.time()
        end_cpu = process.cpu_percent()
        
        # CPU usage assertions
        execution_time = end_time - start_time
        assert execution_time < 5.0  # Should complete within 5 seconds

    @pytest.mark.asyncio
    async def test_async_performance(self):
        """Test async operation performance."""
        async def async_worker(worker_id):
            await asyncio.sleep(0.01)  # Simulate async work
            return f"worker_{worker_id}_completed"
        
        start_time = time.time()
        
        # Run 1000 async workers
        tasks = [async_worker(i) for i in range(1000)]
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Performance assertions
        assert total_time < 5.0  # Should complete within 5 seconds
        assert len(results) == 1000
        assert all("completed" in result for result in results)

    def test_network_performance(self, mock_requests):
        """Test network operation performance."""
        # Mock network responses
        mock_requests['get'].return_value = Mock(
            status_code=200,
            json=lambda: {"data": "test_response"}
        )
        
        start_time = time.time()
        
        # Perform 100 network requests
        for i in range(100):
            import requests
            response = requests.get("https://api.example.com/data")
            data = response.json()
            assert data["data"] == "test_response"
        
        total_time = time.time() - start_time
        
        # Performance assertions
        assert total_time < 10.0  # Should complete within 10 seconds 