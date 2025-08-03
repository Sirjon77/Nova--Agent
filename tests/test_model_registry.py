"""Tests for the model registry system."""
import pytest
from unittest.mock import patch
from nova_core.model_registry import to_official, Model, resolve, get_default_model, get_available_aliases, get_official_models, is_valid_alias


def test_alias_translation():
    """Test that aliases are correctly translated to official model names."""
    assert to_official("gpt-4o-mini") == "gpt-4o"
    assert to_official("gpt-4o-vision") == "gpt-4o"
    assert to_official("o3") == "gpt-3.5-turbo"
    assert to_official("o3-pro") == "gpt-4o"
    assert to_official("gpt-4o") == "gpt-4o"
    assert to_official("gpt-3.5-turbo") == "gpt-3.5-turbo"


def test_legacy_invalid_aliases():
    """Test that legacy invalid aliases are now mapped correctly."""
    assert to_official("gpt-4o-mini-search") == "gpt-4o-mini-search"  # Unknown alias passed through
    assert to_official("gpt-4o-mini-TTS") == "gpt-4o-mini-TTS"  # Unknown alias passed through


def test_default_model():
    """Test default model handling."""
    assert to_official(None) == Model.DEFAULT.value
    assert to_official("") == ""


def test_backward_compatibility():
    """Test backward compatibility functions."""
    assert resolve("gpt-4o-mini") == "gpt-4o"
    assert get_default_model() == Model.DEFAULT.value


def test_model_enum():
    """Test Model enum functionality."""
    assert Model.GPT_4.value == "gpt-4o"
    assert Model.GPT_3_5_TURBO.value == "gpt-3.5-turbo"
    assert Model.GPT_4_MINI.value == "gpt-4o-mini"
    assert Model.GPT_4_VISION.value == "gpt-4o-vision"


def test_available_aliases():
    """Test getting available aliases."""
    aliases = get_available_aliases()
    assert "gpt-4o" in aliases
    assert "gpt-3.5-turbo" in aliases
    assert "gpt-4o-mini" in aliases
    assert "gpt-4o-vision" in aliases


def test_official_models():
    """Test getting official models."""
    official_models = get_official_models()
    assert "gpt-4o" in official_models
    assert "gpt-3.5-turbo" in official_models


def test_is_valid_alias():
    """Test alias validation."""
    assert is_valid_alias("gpt-4o-mini") is True
    assert is_valid_alias("gpt-4o-vision") is True
    assert is_valid_alias("o3") is True
    assert is_valid_alias("o3-pro") is True
    assert is_valid_alias("gpt-4o") is True
    assert is_valid_alias("gpt-3.5-turbo") is True
    assert is_valid_alias("invalid-model") is False


def test_whitespace_handling():
    """Test that whitespace is handled correctly."""
    assert to_official("  gpt-4o-mini  ") == "gpt-4o"


def test_unknown_aliases():
    """Test that unknown aliases are passed through."""
    assert to_official("gpt-4") == "gpt-4"  # Unknown but valid-looking
    assert to_official("custom-model") == "custom-model"  # Unknown custom model


if __name__ == "__main__":
    pytest.main([__file__]) 