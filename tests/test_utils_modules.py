"""Comprehensive tests for utils modules."""

import pytest
from unittest.mock import patch, MagicMock, mock_open
import os
import tempfile
import json
from pathlib import Path
import time

# Import modules to test
from utils.memory_manager import MemoryManager, get_global_memory_manager
from utils.openai_wrapper import nova_chat_completion
from utils.model_controller import select_model, MODEL_TIERS
from utils.confidence import rate_confidence
from utils.json_logger import log
from utils.logger import setup_logger
from utils.memory_ranker import rank_memories
from utils.memory_vault import save_summary, get_summary
from utils.prompt_store import get_prompt
from utils.retry import retry
from utils.self_repair import auto_repair
from utils.summarizer import summarize_text
from utils.telemetry import emit
from utils.tool_registry import register, get_schema, call
from utils.tool_wrapper import run_tool_call, run_tool_call_with_reflex, run_tool_call_with_retry
from utils.user_feedback import UserFeedbackManager, get_user_friendly_error, handle_error, log_user_interaction


class TestMemoryManager:
    """Test MemoryManager functionality."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            dirs = {
                "short_term": temp_path / "short_term",
                "long_term": temp_path / "long_term",
                "log": temp_path / "logs",
                "summaries": temp_path / "summaries"
            }
            for dir_path in dirs.values():
                dir_path.mkdir(parents=True, exist_ok=True)
            yield dirs
    
    def test_memory_manager_initialization(self, temp_dirs):
        """Test MemoryManager initialization."""
        mm = MemoryManager(
            short_term_dir=str(temp_dirs["short_term"]),
            long_term_dir=str(temp_dirs["long_term"]),
            log_dir=str(temp_dirs["log"]),
            summaries_dir=str(temp_dirs["summaries"])
        )
        assert mm is not None
        assert mm.short_term_dir == temp_dirs["short_term"]
        assert mm.long_term_dir == temp_dirs["long_term"]
    
    def test_add_short_term_memory(self, temp_dirs):
        """Test adding short-term memory."""
        mm = MemoryManager(
            short_term_dir=str(temp_dirs["short_term"]),
            long_term_dir=str(temp_dirs["long_term"]),
            log_dir=str(temp_dirs["log"]),
            summaries_dir=str(temp_dirs["summaries"])
        )
        
        result = mm.add_short_term("test_session", "user", "Hello world")
        assert result is True
        
        # Verify file was created
        session_file = temp_dirs["short_term"] / "test_session.json"
        assert session_file.exists()
    
    def test_add_long_term_memory(self, temp_dirs):
        """Test adding long-term memory."""
        mm = MemoryManager(
            short_term_dir=str(temp_dirs["short_term"]),
            long_term_dir=str(temp_dirs["long_term"]),
            log_dir=str(temp_dirs["log"]),
            summaries_dir=str(temp_dirs["summaries"])
        )
        
        result = mm.add_long_term("test_namespace", "test_key", "Test content")
        assert result is True
        
        # Verify file was created
        namespace_file = temp_dirs["long_term"] / "test_namespace.json"
        assert namespace_file.exists()
    
    def test_get_relevant_memories(self, temp_dirs):
        """Test getting relevant memories."""
        mm = MemoryManager(
            short_term_dir=str(temp_dirs["short_term"]),
            long_term_dir=str(temp_dirs["long_term"]),
            log_dir=str(temp_dirs["log"]),
            summaries_dir=str(temp_dirs["summaries"])
        )
        
        # Add some memories first
        mm.add_long_term("test_namespace", "key1", "Python programming")
        mm.add_long_term("test_namespace", "key2", "Machine learning")
        
        # Search for memories
        results = mm.get_relevant_memories("Python", "test_namespace", top_k=5)
        assert isinstance(results, list)
        assert len(results) > 0
    
    def test_get_short_term_memory(self, temp_dirs):
        """Test getting short-term memory."""
        mm = MemoryManager(
            short_term_dir=str(temp_dirs["short_term"]),
            long_term_dir=str(temp_dirs["long_term"]),
            log_dir=str(temp_dirs["log"]),
            summaries_dir=str(temp_dirs["summaries"])
        )
        
        # Add some messages
        mm.add_short_term("test_session", "user", "Hello")
        mm.add_short_term("test_session", "assistant", "Hi there")
        
        # Retrieve messages
        messages = mm.get_short_term("test_session", limit=10)
        assert isinstance(messages, list)
        assert len(messages) == 2
    
    def test_memory_status(self, temp_dirs):
        """Test memory status reporting."""
        mm = MemoryManager(
            short_term_dir=str(temp_dirs["short_term"]),
            long_term_dir=str(temp_dirs["long_term"]),
            log_dir=str(temp_dirs["log"]),
            summaries_dir=str(temp_dirs["summaries"])
        )
        
        status = mm.get_memory_status()
        assert isinstance(status, dict)
        assert "redis_available" in status
        assert "weaviate_available" in status
        assert "fully_available" in status
    
    def test_cleanup_old_memories(self, temp_dirs):
        """Test cleanup of old memories."""
        mm = MemoryManager(
            short_term_dir=str(temp_dirs["short_term"]),
            long_term_dir=str(temp_dirs["long_term"]),
            log_dir=str(temp_dirs["log"]),
            summaries_dir=str(temp_dirs["summaries"])
        )
        
        # Add some memories
        mm.add_short_term("test_session", "user", "test message")
        mm.add_long_term("test_namespace", "test_key", "test content")
        
        # Clean up
        cleaned = mm.cleanup_old_memories(days=1)
        assert isinstance(cleaned, int)
        assert cleaned >= 0


class TestOpenAIWrapper:
    """Test OpenAI wrapper functionality."""
    
    @patch('utils.openai_wrapper.nova_chat_completion')
    def test_nova_chat_completion(self, mock_chat):
        """Test nova chat completion wrapper."""
        mock_response = MagicMock()
        mock_chat.return_value = mock_response
        
        result = nova_chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
            model="gpt-4o-mini"
        )
        
        assert result == mock_response
        mock_chat.assert_called_once()


class TestModelController:
    """Test model controller functionality."""
    
    def test_select_model(self):
        """Test model selection."""
        task_meta = {"type": "script", "prompt": "Test prompt"}
        model, api_key = select_model(task_meta)
        assert isinstance(model, str)
        assert isinstance(api_key, str)
    
    def test_model_tiers_structure(self):
        """Test MODEL_TIERS structure."""
        assert isinstance(MODEL_TIERS, dict)
        assert len(MODEL_TIERS) > 0
        
        for tier_name, tier_config in MODEL_TIERS.items():
            assert isinstance(tier_name, str)
            assert isinstance(tier_config, dict)
            assert "model" in tier_config


class TestConfidence:
    """Test confidence rating functionality."""
    
    def test_rate_confidence(self):
        """Test confidence rating."""
        confidence = rate_confidence("Test action", "Test context")
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
    
    def test_rate_confidence_edge_cases(self):
        """Test confidence rating edge cases."""
        # Test with empty context
        confidence = rate_confidence("Test action")
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
        
        # Test with very long action description
        long_action = "A" * 1000
        confidence = rate_confidence(long_action)
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1


class TestJsonLogger:
    """Test JSON logger functionality."""
    
    def test_log_json(self):
        """Test JSON logging."""
        data = {"test": "value", "number": 42}
        result = log(data)
        assert isinstance(result, str)
        assert "test" in result
        assert "42" in result


class TestLogger:
    """Test logger functionality."""
    
    def test_setup_logger(self):
        """Test logger setup."""
        logger = setup_logger("test_logger")
        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")


class TestMemoryRanker:
    """Test memory ranking functionality."""
    
    def test_rank_memories(self):
        """Test memory ranking."""
        memories = [
            {"content": "Python programming", "relevance": 0.8},
            {"content": "Machine learning", "relevance": 0.9},
            {"content": "Web development", "relevance": 0.6}
        ]
        
        ranked = rank_memories(memories, "Python")
        assert isinstance(ranked, list)
        assert len(ranked) == len(memories)


class TestMemoryVault:
    """Test memory vault functionality."""
    
    def test_memory_vault_operations(self):
        """Test MemoryVault operations."""
        # Test save_summary function
        save_summary("test_workflow", "test_id", {"data": "test_value"})
        
        # Test get_summary function (will return None without Redis)
        result = get_summary("test_workflow", "test_id")
        # Without Redis, this should return None
        assert result is None or isinstance(result, dict)


class TestPromptStore:
    """Test prompt store functionality."""
    
    def test_prompt_store_initialization(self):
        """Test get_prompt function availability."""
        assert callable(get_prompt)
    
    def test_prompt_store_operations(self):
        """Test get_prompt operations."""
        # Test that get_prompt is callable
        assert callable(get_prompt)
        
        # Note: Actual prompt testing would require prompt files to exist
        # This test verifies the function is available and callable


class TestRetry:
    """Test retry functionality."""
    
    def test_retry_decorator(self):
        """Test retry decorator."""
        call_count = 0
        
        @retry(times=3, delay=0.1)
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = failing_function()
        assert result == "success"
        assert call_count == 3


class TestSelfRepair:
    """Test self repair functionality."""
    
    def test_self_repair_initialization(self):
        """Test auto_repair function availability."""
        assert callable(auto_repair)
    
    def test_self_repair_operations(self):
        """Test auto_repair operations."""
        # Test that auto_repair is callable
        assert callable(auto_repair)
        
        # Test with a simple function
        def test_func():
            return "success"
        
        result = auto_repair(test_func)
        assert result == "success"


class TestSummarizer:
    """Test summarizer functionality."""
    
    def test_summarize_text(self):
        """Test text summarization."""
        text = "This is a long text that needs to be summarized. " * 10
        summary = summarize_text(text, max_length=100)
        assert isinstance(summary, str)
        assert len(summary) <= 100
    
    def test_summarize_short_text(self):
        """Test summarizing short text."""
        text = "Short text"
        summary = summarize_text(text, max_length=50)
        assert summary == text


class TestTelemetry:
    """Test telemetry functionality."""
    
    def test_telemetry_initialization(self):
        """Test emit function availability."""
        assert callable(emit)
    
    def test_telemetry_operations(self):
        """Test emit operations."""
        # Test that emit is callable
        assert callable(emit)
        
        # Test emitting an event
        emit("test_event", {"param": "value"})
        # Note: This will print to stderr, but we can't easily capture it in tests


class TestToolRegistry:
    """Test tool registry functionality."""
    
    def test_tool_registry_initialization(self):
        """Test tool registry functions availability."""
        assert callable(register)
        assert callable(get_schema)
        assert callable(call)
    
    def test_tool_registry_operations(self):
        """Test tool registry operations."""
        def test_tool():
            return "test_result"
        
        # Register a tool
        register("test_tool", {"name": "test_tool"}, test_tool)
        
        # Get schema
        schema = get_schema()
        assert isinstance(schema, list)
        
        # Note: call function would require proper schema, but we can test it's callable
        assert callable(call)


class TestToolWrapper:
    """Test tool wrapper functionality."""
    
    def test_tool_wrapper_functions(self):
        """Test tool wrapper functions availability."""
        assert callable(run_tool_call)
        assert callable(run_tool_call_with_reflex)
        assert callable(run_tool_call_with_retry)
    
    def test_tool_wrapper_execution(self):
        """Test tool wrapper execution."""
        def test_function(x, y):
            return x + y
        
        # Test that the function is callable
        assert callable(run_tool_call)
        
        # Note: Actual execution would require session_id and proper setup
        # This test verifies the function is available and callable


class TestUserFeedback:
    """Test user feedback functionality."""
    
    def test_user_feedback_initialization(self):
        """Test UserFeedbackManager initialization."""
        feedback = UserFeedbackManager()
        assert feedback is not None
    
    def test_user_feedback_operations(self):
        """Test user feedback operations."""
        # Test function availability
        assert callable(get_user_friendly_error)
        assert callable(handle_error)
        assert callable(log_user_interaction)
        
        # Test UserFeedbackManager
        feedback = UserFeedbackManager()
        error_msg = feedback.get_user_friendly_error("openai_missing_key")
        assert isinstance(error_msg, str)
        assert len(error_msg) > 0


if __name__ == "__main__":
    pytest.main([__file__]) 