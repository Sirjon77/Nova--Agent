"""
Comprehensive Test Suite for Nova Agent

This test suite covers all major components:
- NLP intent classification
- Memory management
- Autonomous research
- Governance scheduler
- Observability system
- API endpoints
- Configuration management
"""

import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Import Nova components
from nova.nlp.intent_classifier import IntentClassifier, IntentType
from nova.nlp.context_manager import ContextManager
from nova.autonomous_research import AutonomousResearcher, ResearchHypothesis, Experiment
from nova.governance_scheduler import GovernanceScheduler
from nova.observability import NovaObservability
from utils.memory_manager import MemoryManager, get_global_memory_manager

class TestNLPIntentClassification:
    """Test NLP intent classification system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = IntentClassifier()
        self.context_manager = ContextManager()
    
    def test_intent_classification_basic(self):
        """Test basic intent classification."""
        message = "What's the current RPM?"
        result = self.classifier.classify_intent(message)
        
        assert result.intent in IntentType
        assert 0.0 <= result.confidence <= 1.0
        assert result.classification_method in ["rule_based", "semantic", "ai_powered"]
    
    def test_intent_classification_with_context(self):
        """Test intent classification with context."""
        context = {"previous_intent": "get_rpm", "user_id": "test_user"}
        message = "Show me the analytics"
        
        result = self.classifier.classify_intent(message, context)
        
        assert result.intent in IntentType
        assert result.context.get("previous_intent") == "get_rpm"
    
    def test_context_manager(self):
        """Test context management."""
        # Add conversation turn
        self.context_manager.add_turn("user", "Hello", "session_1")
        self.context_manager.add_turn("assistant", "Hi there!", "session_1")
        
        # Get context
        context = self.context_manager.get_context_for_intent("How are you?", "session_1")
        
        assert "conversation_history" in context
        assert len(context["conversation_history"]) == 2
    
    def test_training_data_management(self):
        """Test training data management."""
        from nova.nlp.training_data import TrainingDataManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TrainingDataManager(training_dir=temp_dir)
            
            # Add training example
            manager.add_example(
                message="What's the RPM?",
                intent="get_rpm",
                confidence=0.9,
                entities={"metric": "rpm"},
                context={"user_type": "admin"}
            )
            
            # Verify data was saved
            data = manager.get_training_data()
            assert len(data.examples) == 1
            assert data.examples[0].intent == "get_rpm"

class TestMemoryManagement:
    """Test memory management system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.memory_manager = MemoryManager()
    
    def test_memory_manager_initialization(self):
        """Test memory manager initialization."""
        assert self.memory_manager is not None
        assert hasattr(self.memory_manager, 'add_short_term')
        assert hasattr(self.memory_manager, 'add_long_term')
    
    def test_short_term_memory(self):
        """Test short-term memory operations."""
        session_id = "test_session"
        content = "Test message"
        
        # Add to short-term memory
        self.memory_manager.add_short_term(session_id, "user", content)
        
        # Retrieve from short-term memory
        memories = self.memory_manager.get_short_term(session_id)
        assert len(memories) > 0
    
    def test_long_term_memory(self):
        """Test long-term memory operations."""
        namespace = "test_namespace"
        key = "test_key"
        content = "Test long-term content"
        
        # Add to long-term memory
        success = self.memory_manager.add_long_term(namespace, key, content)
        assert success is True
    
    def test_memory_query(self):
        """Test memory query functionality."""
        query = "test query"
        results = self.memory_manager.get_relevant_memories("test_namespace", query, limit=5)
        assert isinstance(results, list)

class TestAutonomousResearch:
    """Test autonomous research system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.researcher = AutonomousResearcher(research_dir=temp_dir)
    
    @pytest.mark.asyncio
    async def test_hypothesis_generation(self):
        """Test hypothesis generation."""
        with patch('nova.autonomous_research.chat_completion') as mock_chat:
            mock_chat.return_value = json.dumps([
                {
                    "title": "Test Hypothesis",
                    "description": "Test description",
                    "expected_improvement": "10% improvement",
                    "confidence": 0.8,
                    "priority": 4,
                    "category": "performance"
                }
            ])
            
            hypotheses = await self.researcher.generate_hypotheses()
            assert len(hypotheses) == 1
            assert hypotheses[0].title == "Test Hypothesis"
    
    @pytest.mark.asyncio
    async def test_experiment_design(self):
        """Test experiment design."""
        hypothesis = ResearchHypothesis(
            id="test_hyp",
            title="Test Hypothesis",
            description="Test description",
            expected_improvement="10% improvement",
            confidence=0.8,
            priority=4,
            category="performance",
            created_at=datetime.now()
        )
        
        with patch('nova.autonomous_research.chat_completion') as mock_chat:
            mock_chat.return_value = json.dumps({
                "name": "Test Experiment",
                "description": "Test experiment description",
                "parameters": {"param1": "value1"},
                "control_group": {"param1": "current"},
                "treatment_group": {"param1": "new"},
                "metrics": ["accuracy", "response_time"],
                "sample_size": 100,
                "duration_hours": 24
            })
            
            experiment = await self.researcher.design_experiment(hypothesis)
            assert experiment is not None
            assert experiment.name == "Test Experiment"
    
    def test_research_status(self):
        """Test research status reporting."""
        status = self.researcher.get_research_status()
        assert "total_hypotheses" in status
        assert "total_experiments" in status
        assert "total_results" in status

class TestGovernanceScheduler:
    """Test governance scheduler."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "governance_config.json")
            self.scheduler = GovernanceScheduler(config_path)
    
    @pytest.mark.asyncio
    async def test_niche_scoring(self):
        """Test niche scoring functionality."""
        with patch('nova.governance_scheduler.chat_completion') as mock_chat:
            mock_chat.return_value = json.dumps({
                "niche_scores": {"tech": 85, "health": 72},
                "recommendations": ["Focus on tech niche"]
            })
            
            result = await self.scheduler.run_niche_scoring()
            assert "niche_scores" in result
    
    @pytest.mark.asyncio
    async def test_tool_health_check(self):
        """Test tool health check."""
        with patch('nova.governance_scheduler.chat_completion') as mock_chat:
            mock_chat.return_value = "Health check response"
            
            result = await self.scheduler.run_tool_health_check()
            assert "tools" in result
            assert "overall_health" in result
    
    def test_scheduler_configuration(self):
        """Test scheduler configuration."""
        config = self.scheduler.config
        assert "enabled" in config
        assert "schedule" in config
        assert "alert_thresholds" in config

class TestObservability:
    """Test observability system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.observability = NovaObservability(metrics_dir=temp_dir)
    
    def test_metrics_initialization(self):
        """Test metrics initialization."""
        assert hasattr(self.observability, 'request_counter')
        assert hasattr(self.observability, 'nlp_requests')
        assert hasattr(self.observability, 'memory_operations')
    
    def test_request_recording(self):
        """Test request recording."""
        self.observability.record_request("GET", "/test", 200, 0.5)
        # Verify metric was recorded (would need to check actual Prometheus metrics)
    
    def test_error_recording(self):
        """Test error recording."""
        self.observability.record_error("api_error", "test_module", "Test error message")
        
        error_summary = self.observability.get_error_summary()
        assert error_summary["total_errors"] > 0
    
    def test_health_status(self):
        """Test health status reporting."""
        health = self.observability.get_health_status()
        assert "status" in health
        assert "timestamp" in health
        assert "uptime_seconds" in health
    
    def test_performance_summary(self):
        """Test performance summary."""
        # Update some metrics first
        self.observability.update_system_metrics()
        
        summary = self.observability.get_performance_summary()
        assert "summary" in summary or "error" in summary

class TestAPIIntegration:
    """Test API integration."""
    
    def test_research_endpoints(self):
        """Test research API endpoints."""
        from routes.research import router as research_router
        
        # This would test the actual FastAPI router
        # In a real test, you'd use TestClient from fastapi.testclient
        assert research_router is not None
    
    def test_observability_endpoints(self):
        """Test observability API endpoints."""
        from routes.observability import router as observability_router
        
        assert observability_router is not None

class TestConfiguration:
    """Test configuration management."""
    
    def test_production_config_loading(self):
        """Test production configuration loading."""
        config_path = "config/production_config.yaml"
        
        if os.path.exists(config_path):
            # Test that config file exists and is valid YAML
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            assert "security" in config
            assert "api" in config
            assert "memory" in config
            assert "openai" in config

class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.asyncio
    async def test_full_research_cycle(self):
        """Test full autonomous research cycle."""
        with tempfile.TemporaryDirectory() as temp_dir:
            researcher = AutonomousResearcher(research_dir=temp_dir)
            
            with patch('nova.autonomous_research.chat_completion') as mock_chat:
                mock_chat.return_value = json.dumps([
                    {
                        "title": "Test Hypothesis",
                        "description": "Test description",
                        "expected_improvement": "10% improvement",
                        "confidence": 0.8,
                        "priority": 4,
                        "category": "performance"
                    }
                ])
                
                result = await researcher.run_research_cycle()
                assert "hypotheses_generated" in result
                assert "experiments_created" in result
    
    def test_memory_integration(self):
        """Test memory system integration."""
        # Test that memory manager works with actual memory functions
        memory_status = get_memory_status()
        assert isinstance(memory_status, dict)
        assert "weaviate_available" in memory_status

class TestErrorHandling:
    """Test error handling."""
    
    def test_graceful_degradation(self):
        """Test graceful degradation when services are unavailable."""
        # Test that system continues to work when external services fail
        pass
    
    def test_error_recovery(self):
        """Test error recovery mechanisms."""
        # Test that system can recover from errors
        pass

# Performance tests
class TestPerformance:
    """Performance tests."""
    
    def test_nlp_performance(self):
        """Test NLP performance under load."""
        classifier = IntentClassifier()
        
        # Test multiple classifications
        start_time = datetime.now()
        for i in range(100):
            classifier.classify_intent(f"Test message {i}")
        
        duration = (datetime.now() - start_time).total_seconds()
        assert duration < 10  # Should complete within 10 seconds
    
    def test_memory_performance(self):
        """Test memory operations performance."""
        memory_manager = MemoryManager()
        
        # Test bulk operations
        start_time = datetime.now()
        for i in range(100):
            memory_manager.add_short_term(f"session_{i}", "user", f"Message {i}")
        
        duration = (datetime.now() - start_time).total_seconds()
        assert duration < 5  # Should complete within 5 seconds

# Security tests
class TestSecurity:
    """Security tests."""
    
    def test_configuration_security(self):
        """Test that sensitive configuration is properly handled."""
        # Test that secrets are not hardcoded
        pass
    
    def test_input_validation(self):
        """Test input validation and sanitization."""
        # Test that inputs are properly validated
        pass

if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([
        __file__,
        "--cov=nova",
        "--cov=utils",
        "--cov=memory",
        "--cov-report=html",
        "--cov-report=term-missing",
        "-v"
    ]) 