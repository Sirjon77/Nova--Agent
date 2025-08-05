import pytest
import time
import asyncio
from unittest.mock import Mock, patch
from nova.chaos.injector import ChaosConfig, maybe_fail, inject_delay

class TestChaosEnhanced:
    @pytest.mark.asyncio
    async def test_maybe_fail_always_fails(self):
        """Test that maybe_fail always raises when fail_rate=1.0."""
        cfg = ChaosConfig(fail_rate=1.0, delay_ms=0)
        
        with pytest.raises(Exception):
            await maybe_fail(cfg)

    @pytest.mark.asyncio
    async def test_maybe_fail_never_fails(self):
        """Test that maybe_fail never raises when fail_rate=0.0."""
        cfg = ChaosConfig(fail_rate=0.0, delay_ms=0)
        
        # Should not raise any exception
        await maybe_fail(cfg)

    @pytest.mark.asyncio
    async def test_maybe_fail_delay(self):
        """Test that maybe_fail respects delay configuration."""
        cfg = ChaosConfig(fail_rate=0.0, delay_ms=50)
        
        start_time = time.time()
        await maybe_fail(cfg)
        end_time = time.time()
        
        # Should delay for at least 50ms
        assert end_time - start_time >= 0.05

    @pytest.mark.asyncio
    async def test_maybe_fail_probabilistic(self):
        """Test that maybe_fail follows probability distribution."""
        cfg = ChaosConfig(fail_rate=0.5, delay_ms=0)
        
        failure_count = 0
        total_tests = 100
        
        for _ in range(total_tests):
            try:
                await maybe_fail(cfg)
            except Exception:
                failure_count += 1
        
        # Should fail approximately 50% of the time (with some tolerance)
        failure_rate = failure_count / total_tests
        assert 0.3 <= failure_rate <= 0.7

    def test_inject_delay_sync(self):
        """Test synchronous delay injection."""
        start_time = time.time()
        inject_delay(100)  # 100ms delay
        end_time = time.time()
        
        assert end_time - start_time >= 0.1

    @pytest.mark.asyncio
    async def test_inject_delay_async(self):
        """Test asynchronous delay injection."""
        start_time = time.time()
        await inject_delay(50, async_delay=True)  # 50ms delay
        end_time = time.time()
        
        assert end_time - start_time >= 0.05

    @pytest.mark.asyncio
    async def test_chaos_with_memory_operations(self, mock_redis):
        """Test chaos injection with memory operations."""
        from utils.memory_manager import MemoryManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            mm = MemoryManager(
                short_term_dir=temp_dir,
                long_term_dir=temp_dir
            )
            
            cfg = ChaosConfig(fail_rate=0.3, delay_ms=10)
            
            # Test memory operations with chaos
            success_count = 0
            for i in range(10):
                try:
                    with patch('nova.chaos.injector.maybe_fail') as mock_chaos:
                        mock_chaos.side_effect = lambda cfg: asyncio.sleep(0.01)
                        mm.store_short(f"key_{i}", {"data": f"value_{i}"})
                        success_count += 1
                except Exception:
                    pass  # Expected failures due to chaos
            
            # Should have some successful operations
            assert success_count > 0

    @pytest.mark.asyncio
    async def test_chaos_with_api_calls(self, mock_openai):
        """Test chaos injection with API calls."""
        from utils.summarizer import summarize_text
        
        cfg = ChaosConfig(fail_rate=0.2, delay_ms=20)
        
        with patch('nova.chaos.injector.maybe_fail') as mock_chaos:
            mock_chaos.side_effect = lambda cfg: asyncio.sleep(0.02)
            
            # Test summarization with chaos
            text = "This is a test text for summarization with chaos injection."
            result = summarize_text(text, max_length=30)
            
            assert len(result) <= 30

    @pytest.mark.asyncio
    async def test_chaos_with_file_operations(self):
        """Test chaos injection with file operations."""
        import tempfile
        import os
        
        cfg = ChaosConfig(fail_rate=0.1, delay_ms=5)
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            
            with patch('nova.chaos.injector.maybe_fail') as mock_chaos:
                mock_chaos.side_effect = lambda cfg: asyncio.sleep(0.005)
                
                # Test file operations with chaos
                try:
                    with open(temp_path, 'w') as f:
                        f.write("test data")
                    
                    with open(temp_path, 'r') as f:
                        content = f.read()
                    
                    assert content == "test data"
                finally:
                    os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_chaos_config_validation(self):
        """Test chaos configuration validation."""
        # Valid configurations
        valid_configs = [
            ChaosConfig(fail_rate=0.0, delay_ms=0),
            ChaosConfig(fail_rate=0.5, delay_ms=100),
            ChaosConfig(fail_rate=1.0, delay_ms=1000)
        ]
        
        for cfg in valid_configs:
            assert 0.0 <= cfg.fail_rate <= 1.0
            assert cfg.delay_ms >= 0

    @pytest.mark.asyncio
    async def test_chaos_performance_impact(self):
        """Test that chaos injection doesn't significantly impact performance."""
        cfg = ChaosConfig(fail_rate=0.0, delay_ms=1)  # Minimal delay
        
        start_time = time.time()
        for _ in range(100):
            await maybe_fail(cfg)
        end_time = time.time()
        
        # Should complete quickly even with chaos
        assert end_time - start_time < 1.0

    @pytest.mark.asyncio
    async def test_chaos_with_concurrent_operations(self):
        """Test chaos injection with concurrent operations."""
        import asyncio
        
        cfg = ChaosConfig(fail_rate=0.1, delay_ms=10)
        
        async def worker(worker_id):
            results = []
            for i in range(10):
                try:
                    await maybe_fail(cfg)
                    results.append(f"worker_{worker_id}_task_{i}")
                except Exception:
                    results.append(f"worker_{worker_id}_failed_{i}")
            return results
        
        # Run multiple workers concurrently
        tasks = [worker(i) for i in range(3)]
        results = await asyncio.gather(*tasks)
        
        # All workers should complete
        assert len(results) == 3
        for worker_results in results:
            assert len(worker_results) == 10 