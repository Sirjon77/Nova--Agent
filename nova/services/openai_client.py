"""Thin wrapper around openai.ChatCompletion with alias translation + telemetry."""
from typing import Sequence, Optional, Dict, Any
import openai
import logging

from nova_core.model_registry import to_official, Model

logger = logging.getLogger(__name__)


def chat_completion(
    messages: Sequence[Dict[str, str]],
    model: Optional[str] = None,
    **kwargs
) -> Any:
    """Create a chat completion *always* using a valid OpenAI model id."""
    official_name = to_official(model or Model.DEFAULT.value)
    
    logger.info(f"OpenAI API call: {model} -> {official_name}")
    
    return openai.ChatCompletion.create(
        model=official_name, 
        messages=messages, 
        **kwargs
    )


def completion(
    prompt: str,
    model: Optional[str] = None,
    **kwargs
) -> Any:
    """Create a completion *always* using a valid OpenAI model id."""
    official_name = to_official(model or Model.DEFAULT.value)
    
    logger.info(f"OpenAI completion call: {model} -> {official_name}")
    
    return openai.Completion.create(
        model=official_name,
        prompt=prompt,
        **kwargs
    ) 