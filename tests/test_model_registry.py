"""
Unit tests for the model registry system.
"""

import pytest
import warnings
from unittest.mock import patch

from nova_core.model_registry import (
    resolve, 
    get_available_aliases, 
    get_official_models, 
    is_valid_alias, 
    get_default_model,
    MODEL_MAP
)


class TestModelRegistry:
    """Test the model registry functionality."""
    
    def test_alias_resolution(self):
        """Test that aliases resolve to correct official model IDs."""
        assert resolve("gpt-4o-mini") == "gpt-4o"
        assert resolve("gpt-4o-vision") == "gpt-4o"
        assert resolve("gpt-4-turbo") == "gpt-4o"
        assert resolve("gpt-3.5-mini") == "gpt-3.5-turbo"
        assert resolve("gpt-3.5") == "gpt-3.5-turbo"
    
    def test_legacy_alias_resolution(self):
        """Test that legacy invalid aliases now resolve correctly."""
        assert resolve("gpt-4o-mini-search") == "gpt-4o"
        assert resolve("gpt-4o-mini-TTS") == "gpt-4o"
    
    def test_direct_model_ids(self):
        """Test that direct model IDs work and emit warnings."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = resolve("gpt-4")  # This is in MODEL_MAP, so no warning
            assert result == "gpt-4o"
            assert len(w) == 0  # No warning because it's a known alias
            
            # Test with a direct model ID not in the map
            result = resolve("gpt-4o-2024-01-01")  # Hypothetical future model
            assert result == "gpt-4o-2024-01-01"
            assert len(w) == 1
            assert "Prefer using a Nova alias" in str(w[0].message)
    
    def test_unknown_alias(self):
        """Test that unknown aliases raise KeyError."""
        with pytest.raises(KeyError) as exc_info:
            resolve("bogus-model")
        assert "Unknown model alias" in str(exc_info.value)
        assert "Available aliases" in str(exc_info.value)
    
    def test_none_alias_uses_default(self):
        """Test that None alias uses default."""
        with patch('nova_core.model_registry.DEFAULT_ALIAS', 'gpt-4o-mini'):
            result = resolve(None)
            assert result == "gpt-4o"
    
    def test_empty_string_uses_default(self):
        """Test that empty string uses default."""
        with patch('nova_core.model_registry.DEFAULT_ALIAS', 'gpt-4o-mini'):
            result = resolve("")
            assert result == "gpt-4o"
    
    def test_whitespace_stripping(self):
        """Test that whitespace is stripped from aliases."""
        assert resolve("  gpt-4o-mini  ") == "gpt-4o"
    
    def test_get_available_aliases(self):
        """Test getting list of available aliases."""
        aliases = get_available_aliases()
        assert isinstance(aliases, list)
        assert "gpt-4o-mini" in aliases
        assert "gpt-4o-vision" in aliases
        assert "gpt-3.5-mini" in aliases
        assert len(aliases) == len(MODEL_MAP)
    
    def test_get_official_models(self):
        """Test getting list of official model IDs."""
        official_models = get_official_models()
        assert isinstance(official_models, list)
        assert "gpt-4o" in official_models
        assert "gpt-3.5-turbo" in official_models
        # Should be unique values
        assert len(official_models) == len(set(official_models))
    
    def test_is_valid_alias(self):
        """Test alias validation."""
        assert is_valid_alias("gpt-4o-mini") is True
        assert is_valid_alias("gpt-4o-vision") is True
        assert is_valid_alias("bogus-model") is False
        assert is_valid_alias("") is False
        assert is_valid_alias(None) is False
    
    def test_get_default_model(self):
        """Test getting default model ID."""
        with patch('nova_core.model_registry.DEFAULT_ALIAS', 'gpt-4o-mini'):
            result = get_default_model()
            assert result == "gpt-4o"
    
    def test_model_map_structure(self):
        """Test that MODEL_MAP has correct structure."""
        assert isinstance(MODEL_MAP, dict)
        assert len(MODEL_MAP) > 0
        
        # All keys should be strings
        for key in MODEL_MAP.keys():
            assert isinstance(key, str)
            assert len(key) > 0
        
        # All values should be valid OpenAI model IDs
        for value in MODEL_MAP.values():
            assert isinstance(value, str)
            assert value.startswith("gpt-") or value in ["o3", "o3-pro", "text-embedding-3-small", "GPT-Image-1"]
    
    def test_no_duplicate_aliases(self):
        """Test that there are no duplicate aliases."""
        aliases = list(MODEL_MAP.keys())
        assert len(aliases) == len(set(aliases))
    
    def test_environment_override(self):
        """Test that environment variable can override default."""
        with patch.dict('os.environ', {'NOVA_DEFAULT_MODEL': 'gpt-3.5-mini'}):
            # Re-import to get updated default
            import importlib
            import nova_core.model_registry
            importlib.reload(nova_core.model_registry)
            
            result = nova_core.model_registry.get_default_model()
            assert result == "gpt-3.5-turbo"
    
    def test_error_message_includes_aliases(self):
        """Test that error messages include available aliases."""
        with pytest.raises(KeyError) as exc_info:
            resolve("invalid-model")
        
        error_msg = str(exc_info.value)
        assert "Available aliases:" in error_msg
        assert "gpt-4o-mini" in error_msg
        assert "gpt-3.5-mini" in error_msg


if __name__ == "__main__":
    pytest.main([__file__]) 