"""
Advanced NLP Intent Classification System for Nova Agent

This module provides sophisticated intent detection using multiple approaches:
1. Rule-based classification with regex patterns
2. Semantic similarity using embeddings
3. Machine learning classification with OpenAI
4. Context-aware intent resolution
5. Confidence scoring and fallback handling
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np
from sentence_transformers import SentenceTransformer
from utils.openai_wrapper import chat_completion
from utils.model_router import get_model_for_task

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntentType(Enum):
    """Enumeration of all possible intents in the Nova system"""
    # System Control Intents
    RESUME_LOOP = "resume_loop"
    PAUSE_LOOP = "pause_loop"
    STOP_LOOP = "stop_loop"
    STATUS_CHECK = "status_check"
    
    # Analytics & Reporting Intents
    GET_RPM = "get_rpm"
    GET_ANALYTICS = "get_analytics"
    GET_PERFORMANCE = "get_performance"
    GET_REPORTS = "get_reports"
    
    # Content Management Intents
    CREATE_CONTENT = "create_content"
    EDIT_CONTENT = "edit_content"
    DELETE_CONTENT = "delete_content"
    SCHEDULE_CONTENT = "schedule_content"
    
    # Avatar Management Intents
    SWITCH_AVATAR = "switch_avatar"
    CONFIGURE_AVATAR = "configure_avatar"
    AVATAR_PERFORMANCE = "avatar_performance"
    
    # Platform Management Intents
    PLATFORM_STATUS = "platform_status"
    CONNECT_PLATFORM = "connect_platform"
    DISCONNECT_PLATFORM = "disconnect_platform"
    
    # Memory & Learning Intents
    QUERY_MEMORY = "query_memory"
    LEARN_FROM_DATA = "learn_from_data"
    OPTIMIZE_PROMPTS = "optimize_prompts"
    
    # Configuration Intents
    UPDATE_CONFIG = "update_config"
    GET_CONFIG = "get_config"
    RESET_CONFIG = "reset_config"
    
    # Emergency & Debug Intents
    EMERGENCY_STOP = "emergency_stop"
    DEBUG_MODE = "debug_mode"
    SYSTEM_HEALTH = "system_health"
    
    # Generic Intents
    CHAT = "chat"
    HELP = "help"
    UNKNOWN = "unknown"

@dataclass
class IntentResult:
    """Structured result from intent classification"""
    intent: IntentType
    confidence: float
    entities: Dict[str, Any]
    context: Dict[str, Any]
    raw_message: str
    classification_method: str

class IntentClassifier:
    """Advanced intent classification system"""
    
    def __init__(self):
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.intent_patterns = self._load_intent_patterns()
        self.intent_examples = self._load_intent_examples()
        self.confidence_threshold = 0.7
        
    def _load_intent_patterns(self) -> Dict[IntentType, List[str]]:
        """Load regex patterns for each intent type"""
        return {
            IntentType.RESUME_LOOP: [
                r'\b(resume|start|begin|continue|restart)\b',
                r'\b(turn on|activate|enable)\b.*\b(loop|system|nova)\b',
                r'\b(get|make)\b.*\b(going|running)\b'
            ],
            IntentType.PAUSE_LOOP: [
                r'\b(pause|stop|halt|suspend)\b',
                r'\b(turn off|deactivate|disable)\b.*\b(loop|system)\b',
                r'\b(put|set)\b.*\b(on hold|standby)\b'
            ],
            IntentType.GET_RPM: [
                r'\b(rpm|revenue|earnings|money|income)\b',
                r'\b(how much|what is|show me)\b.*\b(making|earning)\b',
                r'\b(performance|metrics|stats)\b.*\b(revenue|money)\b'
            ],
            IntentType.GET_ANALYTICS: [
                r'\b(analytics|data|insights|metrics|stats)\b',
                r'\b(how are|what are)\b.*\b(performing|doing)\b',
                r'\b(show|get|display)\b.*\b(performance|results)\b'
            ],
            IntentType.CREATE_CONTENT: [
                r'\b(create|make|generate|produce)\b.*\b(content|video|post)\b',
                r'\b(new|fresh)\b.*\b(content|video|post)\b',
                r'\b(write|script|film)\b.*\b(video|content)\b'
            ],
            IntentType.SWITCH_AVATAR: [
                r'\b(switch|change|swap)\b.*\b(avatar|character|persona)\b',
                r'\b(use|activate)\b.*\b(avatar|character)\b',
                r'\b(different|new)\b.*\b(avatar|character)\b'
            ],
            IntentType.QUERY_MEMORY: [
                r'\b(remember|recall|memory|history)\b',
                r'\b(what did|when did|how did)\b.*\b(before|previously)\b',
                r'\b(show|get)\b.*\b(history|past|memory)\b'
            ],
            IntentType.HELP: [
                r'\b(help|assist|support)\b',
                r'\b(what can|how do|how to)\b',
                r'\b(guide|tutorial|instructions)\b'
            ]
        }
    
    def _load_intent_examples(self) -> Dict[IntentType, List[str]]:
        """Load example phrases for each intent for semantic matching"""
        return {
            IntentType.RESUME_LOOP: [
                "resume the system",
                "start nova loop",
                "continue operations",
                "turn on the automation",
                "get the system running",
                "activate nova agent"
            ],
            IntentType.GET_RPM: [
                "what's our current RPM",
                "show me the revenue",
                "how much money are we making",
                "what are our earnings",
                "display RPM metrics",
                "current revenue performance"
            ],
            IntentType.CREATE_CONTENT: [
                "create a new video",
                "generate content",
                "make a post",
                "write a script",
                "produce a video",
                "create fresh content"
            ],
            IntentType.SWITCH_AVATAR: [
                "switch to a different avatar",
                "change the character",
                "use a new persona",
                "activate different avatar",
                "swap the character",
                "different avatar please"
            ],
            IntentType.QUERY_MEMORY: [
                "what did we do before",
                "show me the history",
                "recall previous actions",
                "what's in memory",
                "show past operations",
                "get historical data"
            ]
        }
    
    def classify_intent(self, message: str, context: Dict[str, Any] = None) -> IntentResult:
        """
        Main intent classification method using multiple approaches
        
        Args:
            message: User input message
            context: Additional context (user history, system state, etc.)
            
        Returns:
            IntentResult with classified intent and metadata
        """
        context = context or {}
        
        # Method 1: Rule-based classification
        rule_result = self._rule_based_classification(message)
        if rule_result.confidence > self.confidence_threshold:
            return rule_result
        
        # Method 2: Semantic similarity
        semantic_result = self._semantic_classification(message)
        if semantic_result.confidence > self.confidence_threshold:
            return semantic_result
        
        # Method 3: AI-powered classification
        ai_result = self._ai_classification(message, context)
        if ai_result.confidence > self.confidence_threshold:
            return ai_result
        
        # Fallback to generic chat
        return IntentResult(
            intent=IntentType.CHAT,
            confidence=0.5,
            entities={},
            context=context,
            raw_message=message,
            classification_method="fallback"
        )
    
    def _rule_based_classification(self, message: str) -> IntentResult:
        """Rule-based classification using regex patterns"""
        message_lower = message.lower()
        
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    # Extract entities from the match
                    entities = self._extract_entities(message, pattern)
                    
                    return IntentResult(
                        intent=intent_type,
                        confidence=0.85,  # High confidence for exact matches
                        entities=entities,
                        context={},
                        raw_message=message,
                        classification_method="rule_based"
                    )
        
        return IntentResult(
            intent=IntentType.UNKNOWN,
            confidence=0.0,
            entities={},
            context={},
            raw_message=message,
            classification_method="rule_based"
        )
    
    def _semantic_classification(self, message: str) -> IntentResult:
        """Semantic classification using sentence embeddings"""
        try:
            message_embedding = self.embedder.encode([message])[0]
            
            best_intent = IntentType.UNKNOWN
            best_similarity = 0.0
            
            for intent_type, examples in self.intent_examples.items():
                if not examples:
                    continue
                
                # Encode all examples for this intent
                example_embeddings = self.embedder.encode(examples)
                
                # Calculate similarity with each example
                similarities = []
                for example_emb in example_embeddings:
                    similarity = np.dot(message_embedding, example_emb) / (
                        np.linalg.norm(message_embedding) * np.linalg.norm(example_emb)
                    )
                    similarities.append(similarity)
                
                # Get max similarity for this intent
                max_similarity = max(similarities)
                if max_similarity > best_similarity:
                    best_similarity = max_similarity
                    best_intent = intent_type
            
            return IntentResult(
                intent=best_intent,
                confidence=best_similarity,
                entities={},
                context={},
                raw_message=message,
                classification_method="semantic"
            )
            
        except Exception as e:
            logger.error(f"Semantic classification failed: {e}")
            return IntentResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                entities={},
                context={},
                raw_message=message,
                classification_method="semantic_error"
            )
    
    def _ai_classification(self, message: str, context: Dict[str, Any]) -> IntentResult:
        """AI-powered classification using OpenAI"""
        try:
            # Prepare context for AI
            context_str = ""
            if context:
                context_str = f"\nContext: {json.dumps(context, indent=2)}"
            
            # Create classification prompt
            prompt = f"""Classify the user's intent from the following message. Choose from these intent types:

{chr(10).join([f"- {intent.value}: {self._get_intent_description(intent)}" for intent in IntentType])}

Message: "{message}"{context_str}

Respond with JSON only:
{{
    "intent": "intent_type_value",
    "confidence": 0.0-1.0,
    "entities": {{"key": "value"}},
    "reasoning": "brief explanation"
}}"""

            # Get AI classification
            model = get_model_for_task("intent_classification")
            response = chat_completion(prompt, model=model, temperature=0.1)
            
            # Parse response
            try:
                result = json.loads(response)
                intent_type = IntentType(result.get("intent", "unknown"))
                confidence = float(result.get("confidence", 0.5))
                entities = result.get("entities", {})
                
                return IntentResult(
                    intent=intent_type,
                    confidence=confidence,
                    entities=entities,
                    context=context,
                    raw_message=message,
                    classification_method="ai_powered"
                )
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse AI classification response: {e}")
                return IntentResult(
                    intent=IntentType.UNKNOWN,
                    confidence=0.0,
                    entities={},
                    context=context,
                    raw_message=message,
                    classification_method="ai_parse_error"
                )
                
        except Exception as e:
            logger.error(f"AI classification failed: {e}")
            return IntentResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                entities={},
                context=context,
                raw_message=message,
                classification_method="ai_error"
            )
    
    def _extract_entities(self, message: str, pattern: str) -> Dict[str, Any]:
        """Extract named entities from message using regex patterns"""
        entities = {}
        
        # Extract platform mentions
        platform_patterns = {
            'tiktok': r'\b(tiktok|tiktok)\b',
            'instagram': r'\b(instagram|ig)\b',
            'youtube': r'\b(youtube|yt)\b',
            'facebook': r'\b(facebook|fb)\b'
        }
        
        for platform, platform_pattern in platform_patterns.items():
            if re.search(platform_pattern, message.lower()):
                entities['platform'] = platform
        
        # Extract numbers (for RPM, counts, etc.)
        number_match = re.search(r'\b(\d+(?:\.\d+)?)\b', message)
        if number_match:
            entities['number'] = float(number_match.group(1))
        
        # Extract time references
        time_patterns = {
            'today': r'\b(today|now)\b',
            'yesterday': r'\b(yesterday)\b',
            'this_week': r'\b(this week|current week)\b',
            'this_month': r'\b(this month|current month)\b'
        }
        
        for time_ref, time_pattern in time_patterns.items():
            if re.search(time_pattern, message.lower()):
                entities['time_reference'] = time_ref
        
        return entities
    
    def _get_intent_description(self, intent: IntentType) -> str:
        """Get human-readable description for each intent"""
        descriptions = {
            IntentType.RESUME_LOOP: "Resume or start the Nova automation loop",
            IntentType.PAUSE_LOOP: "Pause or stop the Nova automation loop",
            IntentType.GET_RPM: "Get current revenue per mille metrics",
            IntentType.GET_ANALYTICS: "Get performance analytics and insights",
            IntentType.CREATE_CONTENT: "Create new video content or posts",
            IntentType.SWITCH_AVATAR: "Switch to a different avatar/character",
            IntentType.QUERY_MEMORY: "Query system memory or history",
            IntentType.HELP: "Get help or assistance",
            IntentType.CHAT: "General conversation or chat",
            IntentType.UNKNOWN: "Unknown or unclear intent"
        }
        return descriptions.get(intent, "No description available")

# Global classifier instance
intent_classifier = IntentClassifier()

def classify_intent(message: str, context: Dict[str, Any] = None) -> IntentResult:
    """Convenience function to classify intent"""
    return intent_classifier.classify_intent(message, context) 