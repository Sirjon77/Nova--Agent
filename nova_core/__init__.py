"""
Nova Core - Centralized core functionality for Nova Agent.

This package contains essential components that are used throughout
the Nova Agent system, including the model registry, memory management,
and other core utilities.
"""

__version__ = "1.0.0"
__author__ = "Nova Agent Team"

# Import core modules for easy access
try:
    from .model_registry import (
        resolve,
        get_available_aliases,
        get_official_models,
        is_valid_alias,
        get_default_model,
        MODEL_MAP
    )
except ImportError:
    # Handle case where model_registry is not available
    pass

__all__ = [
    "resolve",
    "get_available_aliases", 
    "get_official_models",
    "is_valid_alias",
    "get_default_model",
    "MODEL_MAP"
] 