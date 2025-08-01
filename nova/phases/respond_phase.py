"""
Advanced Response Phase for Nova Agent

This module provides sophisticated response formatting and delivery based on:
- Execution results
- Context and metadata
- User preferences
- Response optimization
"""

import logging
from typing import Dict, Any, Optional
import json
import time

logger = logging.getLogger(__name__)

def respond(result: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Advanced response formatting and delivery
    
    Args:
        result: Execution result from execute_phase
        metadata: Additional metadata about the execution
        
    Returns:
        Formatted response string
    """
    try:
        # Add metadata context if available
        if metadata:
            response = _enhance_response_with_metadata(result, metadata)
        else:
            response = result
        
        # Apply response optimization
        response = _optimize_response(response)
        
        # Log response for analytics
        _log_response(response, metadata)
        
        return response
        
    except Exception as e:
        logger.error(f"Response formatting failed: {e}")
        return f"💬 {result}"

def _enhance_response_with_metadata(result: str, metadata: Dict[str, Any]) -> str:
    """Enhance response with metadata context"""
    
    # Add confidence indicator if available
    confidence = metadata.get("confidence", 0.0)
    if confidence > 0.0:
        confidence_emoji = _get_confidence_emoji(confidence)
        if confidence_emoji:
            result = f"{confidence_emoji} {result}"
    
    # Add execution time if available
    execution_time = metadata.get("execution_time", 0.0)
    if execution_time > 0.0:
        result += f"\n⏱️ Response time: {execution_time:.2f}s"
    
    # Add classification method if available
    classification_method = metadata.get("classification_method", "")
    if classification_method:
        method_emoji = _get_method_emoji(classification_method)
        if method_emoji:
            result += f"\n{method_emoji} Classified via: {classification_method.replace('_', ' ').title()}"
    
    # Add entities if available
    entities = metadata.get("entities", {})
    if entities:
        entity_info = _format_entities(entities)
        if entity_info:
            result += f"\n🔍 Detected: {entity_info}"
    
    # Add suggestions if confidence is low
    if confidence < 0.6:
        result += "\n💡 Tip: Try being more specific for better results."
    
    return result

def _optimize_response(response: str) -> str:
    """Optimize response for better user experience"""
    
    # Remove excessive whitespace
    response = " ".join(response.split())
    
    # Ensure proper line breaks for readability
    response = response.replace(". ", ".\n")
    
    # Add emojis for better visual appeal
    response = _add_response_emojis(response)
    
    return response

def _get_confidence_emoji(confidence: float) -> str:
    """Get emoji based on confidence level"""
    if confidence >= 0.9:
        return "🎯"
    elif confidence >= 0.8:
        return "✅"
    elif confidence >= 0.7:
        return "👍"
    elif confidence >= 0.6:
        return "🤔"
    else:
        return "❓"

def _get_method_emoji(method: str) -> str:
    """Get emoji based on classification method"""
    method_emojis = {
        "rule_based": "🔧",
        "semantic": "🧠",
        "ai_powered": "🤖",
        "fallback": "🔄"
    }
    return method_emojis.get(method, "📝")

def _format_entities(entities: Dict[str, Any]) -> str:
    """Format detected entities for display"""
    entity_parts = []
    
    if "platform" in entities:
        entity_parts.append(f"Platform: {entities['platform']}")
    
    if "number" in entities:
        entity_parts.append(f"Number: {entities['number']}")
    
    if "time_reference" in entities:
        entity_parts.append(f"Time: {entities['time_reference']}")
    
    return ", ".join(entity_parts)

def _add_response_emojis(response: str) -> str:
    """Add contextual emojis to response"""
    
    # System control responses
    if "resumed" in response.lower() or "started" in response.lower():
        response = "🚀 " + response
    elif "paused" in response.lower() or "stopped" in response.lower():
        response = "⏸️ " + response
    
    # Analytics responses
    elif "rpm" in response.lower() or "revenue" in response.lower():
        response = "💰 " + response
    elif "analytics" in response.lower() or "performance" in response.lower():
        response = "📊 " + response
    
    # Content responses
    elif "creating" in response.lower() or "generating" in response.lower():
        response = "🎬 " + response
    
    # Avatar responses
    elif "avatar" in response.lower() or "switched" in response.lower():
        response = "👤 " + response
    
    # Memory responses
    elif "memory" in response.lower() or "history" in response.lower():
        response = "🧠 " + response
    
    # Help responses
    elif "help" in response.lower() or "capabilities" in response.lower():
        response = "🤖 " + response
    
    # Error responses
    elif "error" in response.lower() or "failed" in response.lower():
        response = "❌ " + response
    
    # Status responses
    elif "status" in response.lower():
        response = "📊 " + response
    
    return response

def _log_response(response: str, metadata: Optional[Dict[str, Any]]) -> None:
    """Log response for analytics and improvement"""
    try:
        log_data = {
            "response": response[:200] + "..." if len(response) > 200 else response,
            "response_length": len(response),
            "timestamp": time.time()
        }
        
        if metadata:
            log_data.update({
                "confidence": metadata.get("confidence", 0.0),
                "classification_method": metadata.get("classification_method", ""),
                "intent": metadata.get("intent", ""),
                "entities": metadata.get("entities", {})
            })
        
        logger.info(f"Response logged: {json.dumps(log_data, indent=2)}")
        
    except Exception as e:
        logger.error(f"Failed to log response: {e}")

# Legacy compatibility function
def respond_legacy(result: str) -> str:
    """
    Legacy response function for backward compatibility
    """
    return result
