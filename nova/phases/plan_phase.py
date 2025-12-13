"""
Advanced Planning Phase for Nova Agent

This module provides sophisticated action planning based on:
- Advanced intent analysis
- Context-aware decision making
- Entity extraction and utilization
- Confidence-based action selection
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def plan(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Advanced action planning based on intent analysis
    
    Args:
        analysis: Result from analyze_phase containing intent, confidence, entities, etc.
        
    Returns:
        Dictionary containing planned actions, parameters, and execution strategy
    """
    try:
        intent = analysis.get("intent", "unknown")
        confidence = analysis.get("confidence", 0.0)
        entities = analysis.get("entities", {})
        context = analysis.get("context", {})
        
        logger.info(f"Planning for intent: {intent} (confidence: {confidence:.2f})")
        
        # Get base plan from intent
        base_plan = _get_base_plan(intent, confidence, entities)
        
        # Enhance plan with context
        enhanced_plan = _enhance_plan_with_context(base_plan, context)
        
        # Add execution strategy
        execution_strategy = _get_execution_strategy(intent, confidence, entities)
        
        # Combine into final plan
        plan = {
            **base_plan,
            **enhanced_plan,
            "execution_strategy": execution_strategy,
            "confidence": confidence,
            "entities": entities,
            "context": context
        }
        
        logger.info(f"Planned action: {plan.get('action')} with strategy: {execution_strategy}")
        
        return plan
        
    except Exception as e:
        logger.error(f"Planning failed: {e}")
        return {
            "action": "error_handling",
            "error": str(e),
            "fallback_action": "chat",
            "msg": analysis.get("raw_message", "")
        }

def _get_base_plan(intent: str, confidence: float, entities: Dict[str, Any]) -> Dict[str, Any]:
    """Get base action plan based on intent"""
    
    # High-confidence intents get direct actions
    if confidence > 0.8:
        return _get_high_confidence_plan(intent, entities)
    
    # Medium-confidence intents get confirmation actions
    elif confidence > 0.6:
        return _get_medium_confidence_plan(intent, entities)
    
    # Low-confidence intents get clarification actions
    else:
        return _get_low_confidence_plan(intent, entities)

def _get_high_confidence_plan(intent: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """Get direct action plan for high-confidence intents"""
    
    intent_mapping = {
        "resume_loop": {
            "action": "resume_loop",
            "parameters": {
                "check_system_health": True,
                "validate_credentials": True,
                "start_monitoring": True
            }
        },
        "pause_loop": {
            "action": "pause_loop",
            "parameters": {
                "graceful_shutdown": True,
                "save_state": True,
                "notify_user": True
            }
        },
        "get_rpm": {
            "action": "get_rpm",
            "parameters": {
                "platforms": entities.get("platforms", ["all"]),
                "time_range": entities.get("time_reference", "today"),
                "include_breakdown": True
            }
        },
        "get_analytics": {
            "action": "get_analytics",
            "parameters": {
                "metrics": ["rpm", "engagement", "reach", "conversions"],
                "platforms": entities.get("platforms", ["all"]),
                "time_range": entities.get("time_reference", "today")
            }
        },
        "create_content": {
            "action": "create_content",
            "parameters": {
                "content_type": entities.get("content_type", "video"),
                "platform": entities.get("platform", "all"),
                "avatar": entities.get("avatar", "auto"),
                "topic": entities.get("topic", "auto_generate")
            }
        },
        "switch_avatar": {
            "action": "switch_avatar",
            "parameters": {
                "target_avatar": entities.get("avatar", "next"),
                "validate_availability": True,
                "update_config": True
            }
        },
        "query_memory": {
            "action": "query_memory",
            "parameters": {
                "query": entities.get("query", "recent"),
                "depth": entities.get("depth", 10),
                "include_context": True
            }
        },
        "help": {
            "action": "help",
            "parameters": {
                "topic": entities.get("topic", "general"),
                "include_examples": True,
                "show_capabilities": True
            }
        }
    }
    
    return intent_mapping.get(intent, {
        "action": "chat",
        "parameters": {},
        "msg": f"Handling {intent} with high confidence"
    })

def _get_medium_confidence_plan(intent: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """Get confirmation plan for medium-confidence intents"""
    
    return {
        "action": "confirm_intent",
        "parameters": {
            "intent": intent,
            "entities": entities,
            "suggested_action": _get_suggested_action(intent, entities),
            "confidence": "medium"
        },
        "confirmation_prompt": f"I think you want to {intent.replace('_', ' ')}. Is that correct?"
    }

def _get_low_confidence_plan(intent: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """Get clarification plan for low-confidence intents"""
    
    return {
        "action": "clarify_intent",
        "parameters": {
            "intent": intent,
            "entities": entities,
            "confidence": "low"
        },
        "clarification_prompt": "I'm not sure what you'd like me to do. Could you please clarify?",
        "suggested_options": _get_suggested_options(intent)
    }

def _get_suggested_action(intent: str, entities: Dict[str, Any]) -> str:
    """Get suggested action for medium-confidence intents"""
    
    suggestions = {
        "resume_loop": "resume the Nova automation system",
        "get_rpm": "show current revenue metrics",
        "create_content": "generate new video content",
        "switch_avatar": "change to a different avatar",
        "query_memory": "search conversation history"
    }
    
    return suggestions.get(intent, f"perform {intent.replace('_', ' ')}")

def _get_suggested_options(intent: str) -> List[str]:
    """Get suggested options for low-confidence intents"""
    
    common_actions = [
        "Check RPM and analytics",
        "Create new content",
        "Switch avatar",
        "Resume/pause system",
        "Get help",
        "Query memory"
    ]
    
    return common_actions

def _enhance_plan_with_context(base_plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance plan with contextual information"""
    
    enhanced_plan = base_plan.copy()
    
    # Add system state context
    system_state = context.get("system_state", {})
    if system_state.get("loop_active") and base_plan.get("action") == "resume_loop":
        enhanced_plan["warning"] = "System is already running"
        enhanced_plan["action"] = "status_check"
    
    # Add time context
    time_context = context.get("time_context", {})
    if time_context.get("is_business_hours"):
        enhanced_plan["priority"] = "high"
    else:
        enhanced_plan["priority"] = "normal"
    
    # Add recent conversation context
    recent_intents = context.get("recent_intents", [])
    if len(recent_intents) > 3 and len(set(recent_intents[-3:])) == 1:
        enhanced_plan["repetition_warning"] = True
        enhanced_plan["suggestion"] = "You've asked for this several times. Is there an issue?"
    
    return enhanced_plan

def _get_execution_strategy(intent: str, confidence: float, entities: Dict[str, Any]) -> Dict[str, Any]:
    """Get execution strategy based on intent and confidence"""
    
    strategies = {
        "resume_loop": {
            "method": "sequential",
            "steps": ["validate_system", "check_credentials", "start_services", "begin_monitoring"],
            "timeout": 60,
            "retry_count": 3
        },
        "get_rpm": {
            "method": "parallel",
            "steps": ["fetch_analytics", "calculate_metrics", "format_results"],
            "timeout": 30,
            "retry_count": 2
        },
        "create_content": {
            "method": "pipeline",
            "steps": ["generate_script", "create_visuals", "add_audio", "optimize"],
            "timeout": 300,
            "retry_count": 1
        },
        "switch_avatar": {
            "method": "atomic",
            "steps": ["validate_avatar", "update_config", "notify_system"],
            "timeout": 15,
            "retry_count": 2
        }
    }
    
    return strategies.get(intent, {
        "method": "direct",
        "steps": ["execute"],
        "timeout": 30,
        "retry_count": 1
    })

# Legacy compatibility function
def plan_legacy(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Legacy planning function for backward compatibility
    """
    intent = analysis.get("intent", "unknown")
    
    if intent == "resume":
        return {"action": "resume_loop"}
    if intent == "rpm":
        return {"action": "get_rpm"}
    
    return {"action": "chat", "msg": analysis.get("msg", "")}
