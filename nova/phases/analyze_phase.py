"""
Advanced Analysis Phase for Nova Agent

This module provides sophisticated message analysis using:
- Advanced NLP intent classification
- Context-aware processing
- Entity extraction
- Confidence scoring
"""

import logging
from typing import Dict, Any
from nova.nlp import classify_intent, get_context_for_intent, update_system_state, ConversationTurn
from nova.nlp.intent_classifier import IntentType
import time

logger = logging.getLogger(__name__)

def analyze(message: str) -> Dict[str, Any]:
    """
    Advanced message analysis using NLP intent classification
    
    Args:
        message: User input message to analyze
        
    Returns:
        Dictionary containing analysis results with intent, confidence, entities, and context
    """
    try:
        # Get context for better intent classification
        context = get_context_for_intent(message)
        
        # Classify intent using advanced NLP
        intent_result = classify_intent(message, context)
        
        # Log the classification for debugging
        logger.info(f"Intent classified: {intent_result.intent.value} "
                   f"(confidence: {intent_result.confidence:.2f}, "
                   f"method: {intent_result.classification_method})")
        
        # Prepare analysis result
        analysis = {
            "intent": intent_result.intent.value,
            "confidence": intent_result.confidence,
            "entities": intent_result.entities,
            "context": context,
            "raw_message": message,
            "classification_method": intent_result.classification_method,
            "timestamp": intent_result.context.get("timestamp", 0)
        }
        
        # Add intent-specific metadata
        analysis.update(_get_intent_metadata(intent_result))
        
        # Update system state based on intent
        _update_system_state_from_intent(intent_result)
        
        return analysis
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        # Fallback to basic analysis
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "entities": {},
            "context": {},
            "raw_message": message,
            "classification_method": "fallback",
            "error": str(e)
        }

def _get_intent_metadata(intent_result) -> Dict[str, Any]:
    """Get additional metadata based on the classified intent"""
    metadata = {}
    
    if intent_result.intent == IntentType.GET_RPM:
        metadata["requires_real_time_data"] = True
        metadata["data_sources"] = ["analytics", "platform_apis"]
        
    elif intent_result.intent == IntentType.CREATE_CONTENT:
        metadata["requires_ai_generation"] = True
        metadata["estimated_processing_time"] = "30-60 seconds"
        
    elif intent_result.intent == IntentType.SWITCH_AVATAR:
        metadata["requires_avatar_validation"] = True
        metadata["available_avatars"] = ["Avatar 1", "Avatar 2", "Avatar 3"]
        
    elif intent_result.intent == IntentType.RESUME_LOOP:
        metadata["requires_system_check"] = True
        metadata["estimated_startup_time"] = "10-30 seconds"
        
    elif intent_result.intent == IntentType.QUERY_MEMORY:
        metadata["requires_memory_search"] = True
        metadata["search_depth"] = "recent_50_turns"
    
    return metadata

def _update_system_state_from_intent(intent_result):
    """Update system state based on the classified intent"""
    try:
        if intent_result.intent == IntentType.RESUME_LOOP:
            update_system_state(loop_active=True, current_task="system_startup")
            
        elif intent_result.intent == IntentType.PAUSE_LOOP:
            update_system_state(loop_active=False, current_task=None)
            
        elif intent_result.intent == IntentType.GET_RPM:
            update_system_state(last_rpm_check=time.time())
            
        elif intent_result.intent == IntentType.CREATE_CONTENT:
            update_system_state(last_content_created=time.time())
            
        elif intent_result.intent == IntentType.SWITCH_AVATAR:
            # Extract avatar from entities if available
            new_avatar = intent_result.entities.get("avatar", "default")
            update_system_state(current_avatar=new_avatar)
            
    except Exception as e:
        logger.error(f"Failed to update system state: {e}")

# Legacy compatibility function
def analyze_legacy(message: str) -> Dict[str, Any]:
    """
    Legacy analysis function for backward compatibility
    
    This maintains the old simple string matching approach
    """
    if message.lower().startswith("resume"):
        return {"intent": "resume"}
    if "rpm" in message.lower():
        return {"intent": "rpm"}
    return {"intent": "generic", "msg": message}
