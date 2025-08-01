"""
Tool Wrapper Module for Nova Agent

This module provides wrapper functions for external tool calls with error handling,
logging, and reflex capabilities for automatic error recovery.
"""

import traceback
import logging
from typing import Any, Callable, Optional
from utils.memory_router import store_short, store_long

logger = logging.getLogger(__name__)

def run_tool_call(session_id: str, tool_fn: Callable, *args, **kwargs) -> Any:
    """
    Execute a tool function with error handling and logging.
    
    Args:
        session_id: Session identifier for logging
        tool_fn: Function to execute
        *args: Positional arguments for tool_fn
        **kwargs: Keyword arguments for tool_fn
        
    Returns:
        Result from tool_fn if successful
        
    Raises:
        Exception: Re-raises any exception from tool_fn for reflex handling
    """
    try:
        result = tool_fn(*args, **kwargs)
        status = "success"
        feedback = f"TOOL_CALL [{tool_fn.__name__}] -> {status}: {str(result)[:400]}"
        store_short(session_id, "SYSTEM", feedback)
        store_long(session_id, feedback)
        logger.info(f"Tool call successful: {tool_fn.__name__}")
        return result
        
    except Exception as e:
        error_msg = f"{e}\n{traceback.format_exc()}"
        status = "error"
        feedback = f"TOOL_CALL [{tool_fn.__name__}] -> {status}: {str(e)[:400]}"
        store_short(session_id, "SYSTEM", feedback)
        logger.error(f"Tool call failed: {tool_fn.__name__} - {e}")
        # Re-raise the exception for reflex handling
        raise

def run_tool_call_with_reflex(session_id: str, tool_fn: Callable, *args, **kwargs) -> Any:
    """
    Execute a tool function with automatic error recovery using AI suggestions.
    
    Args:
        session_id: Session identifier for logging
        tool_fn: Function to execute
        *args: Positional arguments for tool_fn
        **kwargs: Keyword arguments for tool_fn
        
    Returns:
        Result from tool_fn if successful
        
    Raises:
        Exception: Final exception after reflex attempts are exhausted
    """
    try:
        return run_tool_call(session_id, tool_fn, *args, **kwargs)
        
    except Exception as e:
        feedback = f"ERROR calling {tool_fn.__name__}: {e}"
        store_short(session_id, "SYSTEM", feedback)
        logger.warning(f"Tool call failed, attempting reflex recovery: {tool_fn.__name__}")
        
        # Attempt to get AI suggestion for fix
        try:
            from utils.openai_wrapper import chat_completion
            suggestion = chat_completion(
                f"A tool call failed with error:\n{feedback}\nSuggest quick fix.",
                temperature=0
            )
            store_short(session_id, "SYSTEM", "SUGGESTED_FIX: " + suggestion)
            logger.info(f"AI suggested fix for {tool_fn.__name__}: {suggestion[:100]}...")
            
        except Exception as ai_error:
            logger.error(f"Failed to get AI suggestion: {ai_error}")
            store_short(session_id, "SYSTEM", f"REFLEX_FAILED: Could not get AI suggestion - {ai_error}")
        
        # Re-raise the original exception
        raise

def run_tool_call_with_retry(session_id: str, tool_fn: Callable, max_retries: int = 3, 
                            *args, **kwargs) -> Any:
    """
    Execute a tool function with retry logic.
    
    Args:
        session_id: Session identifier for logging
        tool_fn: Function to execute
        max_retries: Maximum number of retry attempts
        *args: Positional arguments for tool_fn
        **kwargs: Keyword arguments for tool_fn
        
    Returns:
        Result from tool_fn if successful
        
    Raises:
        Exception: Final exception after all retry attempts
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            result = run_tool_call(session_id, tool_fn, *args, **kwargs)
            if attempt > 0:
                logger.info(f"Tool call succeeded on attempt {attempt + 1}: {tool_fn.__name__}")
            return result
            
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(f"Tool call failed on attempt {attempt + 1}, retrying: {tool_fn.__name__} - {e}")
                store_short(session_id, "SYSTEM", f"RETRY_{attempt + 1}: {tool_fn.__name__} failed - {e}")
            else:
                logger.error(f"Tool call failed after {max_retries + 1} attempts: {tool_fn.__name__} - {e}")
    
    # All retries exhausted
    raise last_exception

def run_tool_call_safe(session_id: str, tool_fn: Callable, *args, **kwargs) -> Any:
    """
    Execute a tool function with safe error handling (no exceptions raised).
    
    Args:
        session_id: Session identifier for logging
        tool_fn: Function to execute
        *args: Positional arguments for tool_fn
        **kwargs: Keyword arguments for tool_fn
        
    Returns:
        Result from tool_fn if successful, error message string if failed
    """
    try:
        return run_tool_call(session_id, tool_fn, *args, **kwargs)
    except Exception as e:
        error_msg = f"Tool call failed: {tool_fn.__name__} - {e}"
        logger.error(error_msg)
        store_short(session_id, "SYSTEM", error_msg)
        return error_msg 