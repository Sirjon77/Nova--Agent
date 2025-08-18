"""
Context Management System for Nova Agent NLP

This module manages conversation context, user history, and system state
to provide better intent classification and response generation.
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import deque
import logging

logger = logging.getLogger(__name__)

@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation"""
    timestamp: float
    user_message: str
    system_response: str
    intent: str
    confidence: float
    entities: Dict[str, Any]
    context_snapshot: Dict[str, Any]

@dataclass
class SystemState:
    """Current system state for context awareness"""
    loop_active: bool
    current_avatar: str
    last_rpm_check: float
    last_content_created: float
    active_platforms: List[str]
    current_task: Optional[str]
    error_count: int
    performance_metrics: Dict[str, float]

class ContextManager:
    """Manages conversation context and system state"""
    
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.conversation_history = deque(maxlen=max_history)
        self.system_state = SystemState(
            loop_active=False,
            current_avatar="default",
            last_rpm_check=0.0,
            last_content_created=0.0,
            active_platforms=[],
            current_task=None,
            error_count=0,
            performance_metrics={}
        )
        self.user_preferences = {}
        self.session_start = time.time()
        
    def add_conversation_turn(self, turn: ConversationTurn):
        """Add a new conversation turn to history"""
        self.conversation_history.append(turn)
        logger.info(f"Added conversation turn: {turn.intent} (confidence: {turn.confidence})")
    
    def get_recent_context(self, turns: int = 5) -> List[ConversationTurn]:
        """Get the most recent conversation turns"""
        return list(self.conversation_history)[-turns:]
    
    def get_context_for_intent(self, message: str) -> Dict[str, Any]:
        """Get relevant context for intent classification"""
        context = {
            "system_state": asdict(self.system_state),
            "recent_intents": self._get_recent_intents(),
            "user_preferences": self.user_preferences,
            "session_duration": time.time() - self.session_start,
            "conversation_length": len(self.conversation_history)
        }
        
        # Add conversation history if relevant
        if self.conversation_history:
            recent_turns = self.get_recent_context(3)
            context["recent_conversation"] = [
                {
                    "user": turn.user_message,
                    "intent": turn.intent,
                    "timestamp": turn.timestamp
                }
                for turn in recent_turns
            ]
        
        # Add time-based context
        context["time_context"] = self._get_time_context()
        
        return context
    
    def update_system_state(self, **kwargs):
        """Update system state with new information"""
        for key, value in kwargs.items():
            if hasattr(self.system_state, key):
                setattr(self.system_state, key, value)
                logger.info(f"Updated system state: {key} = {value}")
    
    def get_system_state(self) -> SystemState:
        """Get current system state"""
        return self.system_state
    
    def _get_recent_intents(self) -> List[str]:
        """Get list of recent intents for context"""
        recent_turns = self.get_recent_context(10)
        return [turn.intent for turn in recent_turns]
    
    def _get_time_context(self) -> Dict[str, Any]:
        """Get time-based context information"""
        now = datetime.now()
        return {
            "hour": now.hour,
            "day_of_week": now.weekday(),
            "is_business_hours": 9 <= now.hour <= 17,
            "time_since_last_rpm": time.time() - self.system_state.last_rpm_check,
            "time_since_last_content": time.time() - self.system_state.last_content_created
        }
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """Get user preferences for context"""
        return self.user_preferences.copy()
    
    def update_user_preferences(self, preferences: Dict[str, Any]):
        """Update user preferences"""
        self.user_preferences.update(preferences)
        logger.info(f"Updated user preferences: {preferences}")
    
    def save_context(self, filepath: str):
        """Save context to file for persistence"""
        try:
            context_data = {
                "conversation_history": [asdict(turn) for turn in self.conversation_history],
                "system_state": asdict(self.system_state),
                "user_preferences": self.user_preferences,
                "session_start": self.session_start
            }
            
            with open(filepath, 'w') as f:
                json.dump(context_data, f, indent=2, default=str)
            
            logger.info(f"Context saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save context: {e}")
    
    def load_context(self, filepath: str):
        """Load context from file"""
        try:
            with open(filepath, 'r') as f:
                context_data = json.load(f)
            
            # Restore conversation history
            self.conversation_history.clear()
            for turn_data in context_data.get("conversation_history", []):
                turn = ConversationTurn(**turn_data)
                self.conversation_history.append(turn)
            
            # Restore system state
            state_data = context_data.get("system_state", {})
            self.system_state = SystemState(**state_data)
            
            # Restore user preferences
            self.user_preferences = context_data.get("user_preferences", {})
            
            # Restore session start
            self.session_start = context_data.get("session_start", time.time())
            
            logger.info(f"Context loaded from {filepath}")
        except Exception as e:
            logger.error(f"Failed to load context: {e}")

# Global context manager instance
context_manager = ContextManager()

def get_context_for_intent(message: str) -> Dict[str, Any]:
    """Convenience function to get context for intent classification"""
    return context_manager.get_context_for_intent(message)

def update_system_state(**kwargs):
    """Convenience function to update system state"""
    context_manager.update_system_state(**kwargs) 