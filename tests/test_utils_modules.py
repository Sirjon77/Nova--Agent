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
from utils.confidence import calculate_confidence
from utils.json_logger import log_json
from utils.logger import setup_logger
from utils.memory_ranker import rank_memories
from utils.memory_vault import MemoryVault
from utils.prompt_store import PromptStore
from utils.retry import retry_with_backoff
from utils.self_repair import SelfRepair
from utils.summarizer import summarize_text
from utils.telemetry import Telemetry
from utils.tool_registry import ToolRegistry
from utils.tool_wrapper import ToolWrapper
from utils.user_feedback import UserFeedback


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
    """Test confidence calculation."""
    
    def test_calculate_confidence(self):
        """Test confidence calculation."""
        confidence = calculate_confidence(0.8, 0.9)
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
    
    def test_calculate_confidence_edge_cases(self):
        """Test confidence calculation edge cases."""
        # Test with zero values
        confidence = calculate_confidence(0, 0)
        assert isinstance(confidence, float)
        
        # Test with high values
        confidence = calculate_confidence(1.0, 1.0)
        assert isinstance(confidence, float)


class TestJsonLogger:
    """Test JSON logger functionality."""
    
    def test_log_json(self):
        """Test JSON logging."""
        data = {"test": "value", "number": 42}
        result = log_json(data)
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
    
    def test_memory_vault_initialization(self):
        """Test MemoryVault initialization."""
        vault = MemoryVault()
        assert vault is not None
    
    def test_memory_vault_operations(self):
        """Test MemoryVault operations."""
        vault = MemoryVault()
        
        # Test storing and retrieving
        vault.store("test_key", "test_value")
        value = vault.retrieve("test_key")
        assert value == "test_value"


class TestPromptStore:
    """Test prompt store functionality."""
    
    def test_prompt_store_initialization(self):
        """Test PromptStore initialization."""
        store = PromptStore()
        assert store is not None
    
    def test_prompt_store_operations(self):
        """Test PromptStore operations."""
        store = PromptStore()
        
        # Test storing and retrieving prompts
        store.add_prompt("test_prompt", "Hello world")
        prompt = store.get_prompt("test_prompt")
        assert prompt == "Hello world"


class TestRetry:
    """Test retry functionality."""
    
    def test_retry_with_backoff(self):
        """Test retry with backoff."""
        call_count = 0
        
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = retry_with_backoff(failing_function, max_retries=3)
        assert result == "success"
        assert call_count == 3


class TestSelfRepair:
    """Test self repair functionality."""
    
    def test_self_repair_initialization(self):
        """Test SelfRepair initialization."""
        repair = SelfRepair()
        assert repair is not None
    
    def test_self_repair_operations(self):
        """Test SelfRepair operations."""
        repair = SelfRepair()
        
        # Test repair attempt
        result = repair.attempt_repair("test_error")
        assert isinstance(result, bool)


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
        """Test Telemetry initialization."""
        telemetry = Telemetry()
        assert telemetry is not None
    
    def test_telemetry_operations(self):
        """Test Telemetry operations."""
        telemetry = Telemetry()
        
        # Test tracking events
        telemetry.track_event("test_event", {"param": "value"})
        assert telemetry is not None


class TestToolRegistry:
    """Test tool registry functionality."""
    
    def test_tool_registry_initialization(self):
        """Test ToolRegistry initialization."""
        registry = ToolRegistry()
        assert registry is not None
    
    def test_tool_registry_operations(self):
        """Test ToolRegistry operations."""
        registry = ToolRegistry()
        
        # Test registering and getting tools
        def test_tool():
            return "test_result"
        
        registry.register("test_tool", test_tool)
        tool = registry.get("test_tool")
        assert tool == test_tool


class TestToolWrapper:
    """Test tool wrapper functionality."""
    
    def test_tool_wrapper_initialization(self):
        """Test ToolWrapper initialization."""
        def test_function():
            return "test"
        
        wrapper = ToolWrapper(test_function)
        assert wrapper is not None
    
    def test_tool_wrapper_execution(self):
        """Test ToolWrapper execution."""
        def test_function(x, y):
            return x + y
        
        wrapper = ToolWrapper(test_function)
        result = wrapper.execute(2, 3)
        assert result == 5


class TestUserFeedback:
    """Test user feedback functionality."""
    
    def test_user_feedback_initialization(self):
        """Test UserFeedback initialization."""
        feedback = UserFeedback()
        assert feedback is not None
    
    def test_user_feedback_operations(self):
        """Test UserFeedback operations."""
        feedback = UserFeedback()
        
        # Test collecting feedback
        feedback.collect_feedback("test_session", "positive", "Great job!")
        assert feedback is not None


if __name__ == "__main__":
    pytest.main([__file__]) 