"""
Tests for Nova Agent NLP Intent Classification System

This module provides comprehensive tests for:
- Intent classification accuracy
- Context management
- Training data management
- Edge cases and error handling
"""

import pytest
import json
from unittest.mock import Mock, patch
from nova.nlp.intent_classifier import IntentClassifier, IntentType, IntentResult
from nova.nlp.context_manager import ContextManager, ConversationTurn
from nova.nlp.training_data import TrainingDataManager, TrainingExample

class TestIntentClassifier:
    """Test cases for IntentClassifier"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.classifier = IntentClassifier()
        
    def test_rule_based_classification(self):
        """Test rule-based classification with regex patterns"""
        # Test resume loop intent
        result = self.classifier._rule_based_classification("resume the system")
        assert result.intent == IntentType.RESUME_LOOP
        assert result.confidence > 0.8
        assert result.classification_method == "rule_based"
        
        # Test RPM intent
        result = self.classifier._rule_based_classification("what's our current RPM")
        assert result.intent == IntentType.GET_RPM
        assert result.confidence > 0.8
        
        # Test unknown intent
        result = self.classifier._rule_based_classification("random gibberish text")
        assert result.intent == IntentType.UNKNOWN
        assert result.confidence == 0.0
        
    def test_entity_extraction(self):
        """Test entity extraction from messages"""
        # Test platform extraction
        result = self.classifier._rule_based_classification("show me TikTok analytics")
        assert "platform" in result.entities
        assert result.entities["platform"] == "tiktok"
        
        # Test number extraction
        result = self.classifier._rule_based_classification("get RPM for last 7 days")
        assert "number" in result.entities
        assert result.entities["number"] == 7.0
        
        # Test time reference extraction
        result = self.classifier._rule_based_classification("show analytics from yesterday")
        assert "time_reference" in result.entities
        assert result.entities["time_reference"] == "yesterday"
        
    @patch('nova.nlp.intent_classifier.SentenceTransformer')
    def test_semantic_classification(self, mock_transformer):
        """Test semantic classification with embeddings"""
        # Mock the transformer
        mock_embedder = Mock()
        mock_embedder.encode.return_value = [[0.1, 0.2, 0.3]]  # Mock embedding
        mock_transformer.return_value = mock_embedder
        
        classifier = IntentClassifier()
        result = classifier._semantic_classification("start the nova system")
        
        # Should return some intent (even if low confidence due to mock)
        assert result.intent != IntentType.UNKNOWN
        assert result.classification_method == "semantic"
        
    @patch('nova.nlp.intent_classifier.chat_completion')
    def test_ai_classification(self, mock_chat):
        """Test AI-powered classification"""
        # Mock AI response
        mock_response = json.dumps({
            "intent": "resume_loop",
            "confidence": 0.95,
            "entities": {"platform": "all"},
            "reasoning": "User wants to resume the system"
        })
        mock_chat.return_value = mock_response
        
        result = self.classifier._ai_classification("please start nova", {})
        
        assert result.intent == IntentType.RESUME_LOOP
        assert result.confidence == 0.95
        assert result.classification_method == "ai_powered"
        
    def test_classify_intent_fallback(self):
        """Test fallback behavior when all methods fail"""
        with patch.object(self.classifier, '_rule_based_classification') as mock_rule:
            with patch.object(self.classifier, '_semantic_classification') as mock_semantic:
                with patch.object(self.classifier, '_ai_classification') as mock_ai:
                    # All methods return low confidence
                    mock_rule.return_value = IntentResult(
                        intent=IntentType.UNKNOWN, confidence=0.0, entities={},
                        context={}, raw_message="test", classification_method="rule_based"
                    )
                    mock_semantic.return_value = IntentResult(
                        intent=IntentType.UNKNOWN, confidence=0.0, entities={},
                        context={}, raw_message="test", classification_method="semantic"
                    )
                    mock_ai.return_value = IntentResult(
                        intent=IntentType.UNKNOWN, confidence=0.0, entities={},
                        context={}, raw_message="test", classification_method="ai"
                    )
                    
                    result = self.classifier.classify_intent("unclear message")
                    
                    assert result.intent == IntentType.CHAT
                    assert result.confidence == 0.5
                    assert result.classification_method == "fallback"

class TestContextManager:
    """Test cases for ContextManager"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.context_manager = ContextManager(max_history=10)
        
    def test_add_conversation_turn(self):
        """Test adding conversation turns"""
        turn = ConversationTurn(
            timestamp=1234567890.0,
            user_message="test message",
            system_response="test response",
            intent="test_intent",
            confidence=0.9,
            entities={},
            context_snapshot={}
        )
        
        self.context_manager.add_conversation_turn(turn)
        assert len(self.context_manager.conversation_history) == 1
        
    def test_get_recent_context(self):
        """Test getting recent context"""
        # Add multiple turns
        for i in range(5):
            turn = ConversationTurn(
                timestamp=1234567890.0 + i,
                user_message=f"message {i}",
                system_response=f"response {i}",
                intent=f"intent_{i}",
                confidence=0.9,
                entities={},
                context_snapshot={}
            )
            self.context_manager.add_conversation_turn(turn)
            
        recent = self.context_manager.get_recent_context(3)
        assert len(recent) == 3
        assert recent[-1].user_message == "message 4"
        
    def test_get_context_for_intent(self):
        """Test context generation for intent classification"""
        context = self.context_manager.get_context_for_intent("test message")
        
        assert "system_state" in context
        assert "recent_intents" in context
        assert "user_preferences" in context
        assert "session_duration" in context
        assert "conversation_length" in context
        
    def test_update_system_state(self):
        """Test system state updates"""
        self.context_manager.update_system_state(loop_active=True, current_avatar="test_avatar")
        
        state = self.context_manager.get_system_state()
        assert state.loop_active
        assert state.current_avatar == "test_avatar"
        
    def test_context_persistence(self, tmp_path):
        """Test context saving and loading"""
        # Add some data
        self.context_manager.update_system_state(loop_active=True)
        self.context_manager.update_user_preferences({"theme": "dark"})
        
        # Save context
        save_path = tmp_path / "context.json"
        self.context_manager.save_context(str(save_path))
        
        # Create new manager and load context
        new_manager = ContextManager()
        new_manager.load_context(str(save_path))
        
        # Verify data was restored
        state = new_manager.get_system_state()
        assert state.loop_active
        
        prefs = new_manager.get_user_preferences()
        assert prefs["theme"] == "dark"

class TestTrainingDataManager:
    """Test cases for TrainingDataManager"""
    
    def setup_method(self, tmp_path):
        """Set up test fixtures"""
        self.data_dir = tmp_path / "nlp_training"
        self.manager = TrainingDataManager(str(self.data_dir))
        
    def test_add_training_example(self):
        """Test adding training examples"""
        example = TrainingExample(
            message="test message",
            intent="test_intent",
            confidence=0.9,
            entities={"test": "value"},
            context={},
            timestamp=1234567890.0
        )
        
        self.manager.add_training_example(example)
        assert len(self.manager.training_examples) == 1
        assert self.manager.training_examples[0].intent == "test_intent"
        
    def test_add_user_feedback(self):
        """Test adding user feedback"""
        self.manager.add_user_feedback(
            original_intent="wrong_intent",
            corrected_intent="correct_intent",
            message="test message",
            feedback="This was wrong"
        )
        
        assert len(self.manager.user_feedback) == 1
        feedback = self.manager.user_feedback[0]
        assert feedback["original_intent"] == "wrong_intent"
        assert feedback["corrected_intent"] == "correct_intent"
        
    def test_get_training_examples_filtered(self):
        """Test getting training examples filtered by intent"""
        # Add examples for different intents
        for intent in ["intent_a", "intent_b", "intent_a"]:
            example = TrainingExample(
                message=f"message for {intent}",
                intent=intent,
                confidence=0.9,
                entities={},
                context={},
                timestamp=1234567890.0
            )
            self.manager.add_training_example(example)
            
        # Filter by intent
        intent_a_examples = self.manager.get_training_examples("intent_a")
        assert len(intent_a_examples) == 2
        
        intent_b_examples = self.manager.get_training_examples("intent_b")
        assert len(intent_b_examples) == 1
        
    def test_update_intent_patterns(self):
        """Test updating intent patterns"""
        patterns = [r"\btest\b", r"\bexample\b"]
        self.manager.update_intent_patterns("test_intent", patterns)
        
        intent_data = self.manager.get_intent_data("test_intent")
        assert intent_data is not None
        assert intent_data.patterns == patterns
        
    def test_generate_training_report(self):
        """Test training report generation"""
        # Add some training data
        for i in range(3):
            example = TrainingExample(
                message=f"message {i}",
                intent=f"intent_{i % 2}",  # Two different intents
                confidence=0.9,
                entities={},
                context={},
                timestamp=1234567890.0
            )
            self.manager.add_training_example(example)
            
        report = self.manager.generate_training_report()
        
        assert report["total_examples"] == 3
        assert report["intents_covered"] == 2
        assert "examples_per_intent" in report
        assert report["examples_per_intent"]["intent_0"] == 2
        assert report["examples_per_intent"]["intent_1"] == 1

class TestIntegration:
    """Integration tests for the complete NLP system"""
    
    def test_end_to_end_classification(self):
        """Test complete end-to-end intent classification"""
        from nova.nlp import classify_intent, get_context_for_intent
        
        # Test with context
        context = get_context_for_intent("resume the system")
        result = classify_intent("resume the system", context)
        
        assert result.intent == IntentType.RESUME_LOOP
        assert result.confidence > 0.7
        assert result.classification_method in ["rule_based", "semantic", "ai_powered"]
        
    def test_context_aware_classification(self):
        """Test that context improves classification accuracy"""
        from nova.nlp import classify_intent, get_context_for_intent, update_system_state
        
        # Set system state
        update_system_state(loop_active=True, current_avatar="test_avatar")
        
        # Get context and classify
        context = get_context_for_intent("what's the status")
        result = classify_intent("what's the status", context)
        
        # Should recognize this as a status check due to context
        assert result.intent in [IntentType.STATUS_CHECK, IntentType.GET_ANALYTICS]
        
    def test_training_data_integration(self):
        """Test integration with training data collection"""
        from nova.nlp import classify_intent, get_context_for_intent
        from nova.nlp.training_data import add_training_example
        
        # Classify intent
        context = get_context_for_intent("test message")
        result = classify_intent("test message", context)
        
        # Add to training data
        add_training_example(
            message="test message",
            intent=result.intent.value,
            confidence=result.confidence,
            entities=result.entities,
            context=context
        )
        
        # Verify it was added
        from nova.nlp.training_data import training_data_manager
        examples = training_data_manager.get_training_examples()
        assert len(examples) > 0
        assert examples[-1].message == "test message"

if __name__ == "__main__":
    pytest.main([__file__]) 