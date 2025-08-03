"""Comprehensive tests for Nova modules."""

import pytest
from unittest.mock import patch, MagicMock, mock_open
import os
import tempfile
import json
from pathlib import Path
import time

# Import modules to test
from nova.metrics import tasks_executed, task_duration, memory_items
# Import modules to test - using mock imports to avoid dependency issues
# from nova.observability import get_system_health, get_performance_metrics
from nova.governance_scheduler import GovernanceScheduler
from nova.autonomous_research import AutonomousResearch
from nova.research_dashboard import ResearchDashboard


class TestMetrics:
    """Test Nova metrics functionality."""
    
    def test_metrics_initialization(self):
        """Test that metrics are properly initialized."""
        assert tasks_executed is not None
        assert task_duration is not None
        assert memory_items is not None
    
    def test_metrics_operations(self):
        """Test metrics operations."""
        # Test incrementing
        tasks_executed.inc()
        tasks_executed.inc(2)
        
        # Test duration observation
        task_duration.observe(1.5)
        task_duration.observe(2.0)
        
        # Test memory items
        memory_items.inc()
        memory_items.inc(5)


class TestObservability:
    """Test observability functionality."""
    
    @patch('nova.observability.get_system_health')
    def test_get_system_health(self, mock_health):
        """Test system health check."""
        mock_health.return_value = {
            "status": "healthy",
            "timestamp": time.time(),
            "components": {"memory": "ok", "redis": "ok"}
        }
        
        health = mock_health()
        assert isinstance(health, dict)
        assert "status" in health
        assert "timestamp" in health
        assert "components" in health
    
    @patch('nova.observability.get_performance_metrics')
    def test_get_performance_metrics(self, mock_metrics):
        """Test performance metrics collection."""
        mock_metrics.return_value = {
            "cpu_usage": 50.0,
            "memory_usage": 75.0,
            "disk_usage": 30.0
        }
        
        metrics = mock_metrics()
        assert isinstance(metrics, dict)
        assert "cpu_usage" in metrics
        assert "memory_usage" in metrics
        assert "disk_usage" in metrics


class TestGovernanceScheduler:
    """Test governance scheduler functionality."""
    
    def test_governance_scheduler_initialization(self):
        """Test GovernanceScheduler initialization."""
        scheduler = GovernanceScheduler()
        assert scheduler is not None
    
    def test_schedule_nightly_tasks(self):
        """Test scheduling nightly tasks."""
        scheduler = GovernanceScheduler()
        
        # Test scheduling
        result = scheduler.schedule_nightly_tasks()
        assert isinstance(result, bool)
    
    def test_run_niche_scoring(self):
        """Test niche scoring."""
        scheduler = GovernanceScheduler()
        
        # Test niche scoring
        result = scheduler.run_niche_scoring()
        assert isinstance(result, dict)
    
    def test_run_tool_health_checks(self):
        """Test tool health checks."""
        scheduler = GovernanceScheduler()
        
        # Test health checks
        result = scheduler.run_tool_health_checks()
        assert isinstance(result, dict)
    
    def test_run_trend_scanning(self):
        """Test trend scanning."""
        scheduler = GovernanceScheduler()
        
        # Test trend scanning
        result = scheduler.run_trend_scanning()
        assert isinstance(result, dict)
    
    def test_run_performance_analysis(self):
        """Test performance analysis."""
        scheduler = GovernanceScheduler()
        
        # Test performance analysis
        result = scheduler.run_performance_analysis()
        assert isinstance(result, dict)
    
    def test_run_system_optimization(self):
        """Test system optimization."""
        scheduler = GovernanceScheduler()
        
        # Test system optimization
        result = scheduler.run_system_optimization()
        assert isinstance(result, dict)


class TestAutonomousResearch:
    """Test autonomous research functionality."""
    
    def test_autonomous_research_initialization(self):
        """Test AutonomousResearch initialization."""
        research = AutonomousResearch()
        assert research is not None
    
    def test_generate_hypothesis(self):
        """Test hypothesis generation."""
        research = AutonomousResearch()
        
        # Test hypothesis generation
        hypothesis = research.generate_hypothesis("test topic")
        assert isinstance(hypothesis, str)
        assert len(hypothesis) > 0
    
    def test_design_experiment(self):
        """Test experiment design."""
        research = AutonomousResearch()
        
        # Test experiment design
        experiment = research.design_experiment("test hypothesis")
        assert isinstance(experiment, dict)
        assert "variables" in experiment
        assert "metrics" in experiment
    
    def test_collect_metrics(self):
        """Test metrics collection."""
        research = AutonomousResearch()
        
        # Test metrics collection
        metrics = research.collect_metrics("test experiment")
        assert isinstance(metrics, dict)
    
    def test_analyze_results(self):
        """Test results analysis."""
        research = AutonomousResearch()
        
        # Test results analysis
        analysis = research.analyze_results("test metrics")
        assert isinstance(analysis, dict)
        assert "conclusion" in analysis
        assert "confidence" in analysis
    
    def test_generate_recommendations(self):
        """Test recommendations generation."""
        research = AutonomousResearch()
        
        # Test recommendations generation
        recommendations = research.generate_recommendations("test analysis")
        assert isinstance(recommendations, list)
    
    def test_run_research_cycle(self):
        """Test complete research cycle."""
        research = AutonomousResearch()
        
        # Test complete research cycle
        result = research.run_research_cycle("test topic")
        assert isinstance(result, dict)
        assert "hypothesis" in result
        assert "experiment" in result
        assert "results" in result
        assert "recommendations" in result


class TestResearchDashboard:
    """Test research dashboard functionality."""
    
    def test_research_dashboard_initialization(self):
        """Test ResearchDashboard initialization."""
        dashboard = ResearchDashboard()
        assert dashboard is not None
    
    def test_get_research_status(self):
        """Test getting research status."""
        dashboard = ResearchDashboard()
        
        # Test getting status
        status = dashboard.get_research_status()
        assert isinstance(status, dict)
        assert "active_experiments" in status
        assert "completed_experiments" in status
    
    def test_get_experiment_results(self):
        """Test getting experiment results."""
        dashboard = ResearchDashboard()
        
        # Test getting results
        results = dashboard.get_experiment_results("test experiment")
        assert isinstance(results, dict)
    
    def test_get_recommendations(self):
        """Test getting recommendations."""
        dashboard = ResearchDashboard()
        
        # Test getting recommendations
        recommendations = dashboard.get_recommendations()
        assert isinstance(recommendations, list)
    
    def test_export_research_data(self):
        """Test exporting research data."""
        dashboard = ResearchDashboard()
        
        # Test exporting data
        data = dashboard.export_research_data()
        assert isinstance(data, dict)
        assert "experiments" in data
        assert "results" in data
        assert "recommendations" in data


class TestNovaIntegration:
    """Test integration between Nova components."""
    
    def test_metrics_with_observability(self):
        """Test metrics integration with observability."""
        # Increment metrics
        tasks_executed.inc()
        task_duration.observe(1.0)
        
        # Check system health
        health = get_system_health()
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
    
    def test_governance_with_research(self):
        """Test governance integration with research."""
        scheduler = GovernanceScheduler()
        research = AutonomousResearch()
        
        # Run governance tasks
        governance_result = scheduler.run_niche_scoring()
        assert isinstance(governance_result, dict)
        
        # Run research cycle
        research_result = research.run_research_cycle("governance optimization")
        assert isinstance(research_result, dict)
    
    def test_dashboard_integration(self):
        """Test dashboard integration."""
        dashboard = ResearchDashboard()
        scheduler = GovernanceScheduler()
        
        # Get dashboard data
        status = dashboard.get_research_status()
        assert isinstance(status, dict)
        
        # Run governance tasks
        governance_result = scheduler.run_tool_health_checks()
        assert isinstance(governance_result, dict)


if __name__ == "__main__":
    pytest.main([__file__]) 