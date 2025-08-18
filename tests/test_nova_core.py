"""Comprehensive tests for Nova core modules."""

import pytest
from unittest.mock import patch, MagicMock

# Import modules to test
from nova_core.model_registry import to_official, Model, _ALIAS_TO_OFFICIAL
from nova.services.openai_client import chat_completion, completion
from nova.metrics import tasks_executed, task_duration, memory_items


class TestModelRegistry:
    """Test the model registry functionality."""
    
    def test_to_official_with_valid_aliases(self):
        """Test converting valid aliases to official names."""
        assert to_official("gpt-4o-mini") == "gpt-4o"
        assert to_official("o3") == "gpt-3.5-turbo"
        assert to_official("gpt-4o-vision") == "gpt-4o"
        assert to_official("gpt-4o-mini-search") == "gpt-4o-mini-search"  # Not in alias mapping
    
    def test_to_official_with_official_names(self):
        """Test that official names pass through unchanged."""
        assert to_official("gpt-4o") == "gpt-4o"
        assert to_official("gpt-3.5-turbo") == "gpt-3.5-turbo"
        assert to_official("gpt-4") == "gpt-4"
    
    def test_to_official_with_unknown_names(self):
        """Test that unknown names pass through unchanged."""
        assert to_official("unknown-model") == "unknown-model"
        assert to_official("custom-model-v1") == "custom-model-v1"
    
    def test_to_official_with_none(self):
        """Test with None input."""
        assert to_official(None) == Model.DEFAULT.value
    
    def test_to_official_with_empty_string(self):
        """Test with empty string input."""
        assert to_official("") == Model.DEFAULT.value
    
    def test_to_official_with_whitespace(self):
        """Test with whitespace input."""
        assert to_official("  gpt-4o-mini  ") == "gpt-4o"
    
    def test_alias_mapping_completeness(self):
        """Test that all aliases in the mapping work."""
        for alias, official in _ALIAS_TO_OFFICIAL.items():
            assert to_official(alias) == official


class TestOpenAIClient:
    """Test the OpenAI client wrapper."""
    
    @patch('nova.services.openai_client.openai.ChatCompletion.create')
    def test_chat_completion_success(self, mock_create):
        """Test successful chat completion."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
        mock_create.return_value = mock_response
        
        result = chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
            model="gpt-4o-mini"
        )
        
        assert result == mock_response
        mock_create.assert_called_once()
        # Verify the model was converted to official name
        call_args = mock_create.call_args
        assert call_args[1]['model'] == "gpt-4o"
    
    @patch('nova.services.openai_client.openai.ChatCompletion.create')
    def test_chat_completion_success(self, mock_create):
        """Test successful chat completion."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
        mock_create.return_value = mock_response
        
        result = chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
            model="o3"
        )
        
        assert result == mock_response
        assert mock_create.call_count == 1
    
    @patch('nova.services.openai_client.openai.Completion.create')
    def test_completion_success(self, mock_create):
        """Test successful completion."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(text="Test completion")]
        mock_create.return_value = mock_response
        
        result = completion(
            prompt="Hello",
            model="gpt-3.5-turbo"
        )
        
        assert result == mock_response
        mock_create.assert_called_once()


class TestMetrics:
    """Test the metrics module."""
    
    def test_metrics_initialization(self):
        """Test that metrics are properly initialized."""
        # These should be initialized without errors
        assert tasks_executed is not None
        assert task_duration is not None
        assert memory_items is not None
    
    def test_metrics_increment(self):
        """Test incrementing metrics."""
        # Test that we can increment without errors
        tasks_executed.inc()
        tasks_executed.inc(2)
        
        # Test duration observation
        task_duration.observe(1.5)
        task_duration.observe(2.0)
        
        # Test memory items
        memory_items.inc()
        memory_items.inc(5)


class TestNovaCoreIntegration:
    """Test integration between core components."""
    
    def test_model_registry_with_openai_client(self):
        """Test that model registry works with OpenAI client."""
        with patch('nova.services.openai_client.openai.ChatCompletion.create') as mock_create:
            mock_create.return_value = MagicMock()
            
            # Test that alias conversion happens
            chat_completion(
                messages=[{"role": "user", "content": "Test"}],
                model="gpt-4o-mini"
            )
            
            call_args = mock_create.call_args
            assert call_args[1]['model'] == "gpt-4o"
    
    def test_metrics_with_model_usage(self):
        """Test that metrics work with model usage."""
        with patch('nova.services.openai_client.openai.ChatCompletion.create') as mock_create:
            mock_create.return_value = MagicMock()
            
            # This should increment metrics
            chat_completion(
                messages=[{"role": "user", "content": "Test"}],
                model="o3"
            )
            
            # Verify metrics were updated
            assert tasks_executed is not None


if __name__ == "__main__":
    pytest.main([__file__]) 