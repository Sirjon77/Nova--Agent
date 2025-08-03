"""
User-Friendly Error Handling and Feedback System

This module provides user-friendly error messages and feedback mechanisms
that translate technical errors into helpful user responses.
"""

import logging
from typing import Dict, Any, Optional, List
from utils.memory_manager import get_global_memory_manager

logger = logging.getLogger(__name__)

class UserFeedbackManager:
    """
    Manages user-friendly error messages and feedback.
    
    Translates technical errors into helpful user responses and
    provides suggestions for next steps.
    """
    
    def __init__(self):
        """Initialize the feedback manager."""
        self.error_templates = self._load_error_templates()
        self.suggestion_templates = self._load_suggestion_templates()
        
    def _load_error_templates(self) -> Dict[str, str]:
        """Load user-friendly error message templates."""
        return {
            "openai_missing_key": "I'm sorry, I cannot process your request right now because my AI service is not configured. Please check your OpenAI API key settings.",
            "openai_rate_limit": "I'm experiencing high demand right now. Please try again in a few moments.",
            "openai_quota_exceeded": "I've reached my usage limit for today. Please try again tomorrow or check your OpenAI account settings.",
            "memory_unavailable": "I'm having trouble accessing my memory system. Your request will still be processed, but I may not remember our previous conversation.",
            "summarization_failed": "I'm sorry, I couldn't summarize that content. The text might be too long, empty, or in an unsupported format.",
            "tool_execution_failed": "I encountered an error while trying to complete your request. Let me try a different approach.",
            "file_not_found": "I couldn't find the file you're looking for. Please check the file path and try again.",
            "permission_denied": "I don't have permission to access that resource. Please check your file permissions or try a different location.",
            "network_error": "I'm having trouble connecting to external services. Please check your internet connection and try again.",
            "validation_error": "I couldn't understand your request. Please try rephrasing it or provide more details.",
            "timeout_error": "The request is taking longer than expected. Please try again with a simpler request.",
            "unknown_error": "I encountered an unexpected error. Please try again, and if the problem persists, let me know what you were trying to do."
        }
    
    def _load_suggestion_templates(self) -> Dict[str, List[str]]:
        """Load suggestion templates for different scenarios."""
        return {
            "openai_missing_key": [
                "Check if your OpenAI API key is set in the environment variables",
                "Verify your OpenAI account has sufficient credits",
                "Try restarting the application to reload configuration"
            ],
            "summarization_failed": [
                "Try providing a shorter text to summarize",
                "Check if the text contains readable content",
                "Try breaking long content into smaller sections"
            ],
            "memory_unavailable": [
                "Your request will still be processed normally",
                "Try restarting the application to reconnect to memory services",
                "Check if Redis or Weaviate services are running"
            ],
            "tool_execution_failed": [
                "Try rephrasing your request",
                "Provide more specific details about what you want to accomplish",
                "Check if all required services are running"
            ],
            "general": [
                "Try rephrasing your request",
                "Provide more specific details",
                "Check if all required services are running",
                "Try restarting the application"
            ]
        }
    
    def get_user_friendly_error(self, error_type: str, original_error: Optional[str] = None) -> str:
        """
        Get a user-friendly error message.
        
        Args:
            error_type: Type of error
            original_error: Original technical error message
            
        Returns:
            str: User-friendly error message
        """
        # Get the error template
        error_message = self.error_templates.get(error_type, self.error_templates["unknown_error"])
        
        # Log the original error for debugging
        if original_error:
            logger.error(f"Technical error ({error_type}): {original_error}")
        
        return error_message
    
    def get_suggestions(self, error_type: str) -> List[str]:
        """
        Get suggestions for resolving an error.
        
        Args:
            error_type: Type of error
            
        Returns:
            List of suggestion strings
        """
        return self.suggestion_templates.get(error_type, self.suggestion_templates["general"])
    
    def format_error_response(self, error_type: str, original_error: Optional[str] = None) -> Dict[str, Any]:
        """
        Format a complete error response with message and suggestions.
        
        Args:
            error_type: Type of error
            original_error: Original technical error message
            
        Returns:
            Dict containing error message and suggestions
        """
        return {
            "error_message": self.get_user_friendly_error(error_type, original_error),
            "suggestions": self.get_suggestions(error_type),
            "error_type": error_type,
            "technical_details": original_error if original_error else None
        }
    
    def classify_error(self, error: Exception) -> str:
        """
        Classify an exception into an error type.
        
        Args:
            error: Exception to classify
            
        Returns:
            str: Error type
        """
        error_str = str(error).lower()
        
        if "api key" in error_str or "authentication" in error_str:
            return "openai_missing_key"
        elif "rate limit" in error_str or "too many requests" in error_str:
            return "openai_rate_limit"
        elif "quota" in error_str or "billing" in error_str:
            return "openai_quota_exceeded"
        elif "memory" in error_str or "redis" in error_str or "weaviate" in error_str:
            return "memory_unavailable"
        elif "summar" in error_str or "text" in error_str:
            return "summarization_failed"
        elif "file" in error_str and "not found" in error_str:
            return "file_not_found"
        elif "permission" in error_str or "access" in error_str:
            return "permission_denied"
        elif "network" in error_str or "connection" in error_str:
            return "network_error"
        elif "validation" in error_str or "invalid" in error_str:
            return "validation_error"
        elif "timeout" in error_str:
            return "timeout_error"
        else:
            return "unknown_error"
    
    def handle_error(self, error: Exception, context: Optional[str] = None) -> str:
        """
        Handle an error and return a user-friendly response.
        
        Args:
            error: Exception that occurred
            context: Optional context about what was being attempted
            
        Returns:
            str: User-friendly error response
        """
        error_type = self.classify_error(error)
        error_response = self.format_error_response(error_type, str(error))
        
        # Log the error with context
        logger.error(f"Error in {context or 'unknown context'}: {error}")
        
        # Format the response for the user
        response = error_response["error_message"]
        
        # Add suggestions if available
        if error_response["suggestions"]:
            response += "\n\n💡 Suggestions:\n"
            for suggestion in error_response["suggestions"]:
                response += f"• {suggestion}\n"
        
        return response
    
    def log_user_interaction(self, session_id: str, user_message: str, agent_response: str, 
                           success: bool = True, error_type: Optional[str] = None) -> None:
        """
        Log user interactions for analysis and improvement.
        
        Args:
            session_id: Session identifier
            user_message: User's message
            agent_response: Agent's response
            success: Whether the interaction was successful
            error_type: Type of error if any
        """
        try:
            metadata = {
                "success": success,
                "error_type": error_type,
                "response_length": len(agent_response),
                "user_message_length": len(user_message)
            }
            
            memory_manager.log_interaction(session_id, user_message, agent_response, metadata)
            
        except Exception as e:
            logger.error(f"Failed to log user interaction: {e}")

# Global feedback manager instance
feedback_manager = UserFeedbackManager()

# Convenience functions
def get_user_friendly_error(error_type: str, original_error: Optional[str] = None) -> str:
    """Get a user-friendly error message."""
    return feedback_manager.get_user_friendly_error(error_type, original_error)

def handle_error(error: Exception, context: Optional[str] = None) -> str:
    """Handle an error and return a user-friendly response."""
    return feedback_manager.handle_error(error, context)

def log_user_interaction(session_id: str, user_message: str, agent_response: str, 
                        success: bool = True, error_type: Optional[str] = None) -> None:
    """Log user interactions for analysis."""
    feedback_manager.log_user_interaction(session_id, user_message, agent_response, success, error_type) 