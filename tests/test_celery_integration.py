"""
Tests for Celery integration and task execution.

This module tests the Celery setup, task definitions, and basic execution
to ensure the background job system is working correctly.
"""

import pytest
import os
from unittest.mock import patch, MagicMock

# Set test environment before importing Celery app
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'


class TestCeleryApp:
    """Test Celery application configuration."""
    
    def test_celery_app_creation(self):
        """Test that Celery app can be created and configured."""
        from nova.celery_app import celery_app
        
        assert celery_app.main == 'nova_agent'
        assert celery_app.conf.timezone == 'UTC'
        assert celery_app.conf.enable_utc is True
    
    def test_beat_schedule_configuration(self):
        """Test that beat schedule is properly configured."""
        from nova.celery_app import celery_app
        
        beat_schedule = celery_app.conf.beat_schedule
        
        # Check that required tasks are scheduled
        assert 'nightly-governance-loop' in beat_schedule
        assert 'hourly-memory-cleanup' in beat_schedule
        assert 'daily-metrics-processing' in beat_schedule
        
        # Check governance task configuration
        governance_task = beat_schedule['nightly-governance-loop']
        assert governance_task['task'] == 'nova.governance.run_governance_task'
        assert 'schedule' in governance_task
    
    def test_health_check_task(self):
        """Test the health check task."""
        from nova.celery_app import health_check
        
        # Mock the task execution
        with patch.object(health_check, 'delay') as mock_delay:
            mock_delay.return_value = MagicMock(id='test-task-id')
            
            # This would normally be called by Celery
            result = health_check()
            
            assert 'status' in result
            assert result['status'] == 'healthy'
            assert 'worker' in result
            assert result['worker'] is True


class TestGovernanceTasks:
    """Test governance-related Celery tasks."""
    
    @patch('nova.governance.tasks.governance_run')
    @patch('nova.governance.tasks._load_governance_config')
    def test_governance_task_execution(self, mock_load_config, mock_governance_run):
        """Test governance task execution."""
        from nova.governance.tasks import run_governance_task
        
        # Setup mocks
        mock_load_config.return_value = {'auto_actions': False}
        mock_governance_run.return_value = {'status': 'completed'}
        
        # Create a mock task instance
        mock_task = MagicMock()
        mock_task.request.id = 'test-task-id'
        mock_task.request.retries = 0
        
        # Execute the task function directly
        result = run_governance_task(mock_task)
        
        assert result['status'] == 'completed'
        assert result['task_id'] == 'test-task-id'
        assert result['retry_count'] == 0
        
        # Verify governance was called
        mock_governance_run.assert_called_once()
    
    @patch('nova.governance.tasks._load_governance_config')
    def test_governance_config_validation(self, mock_load_config):
        """Test governance configuration validation task."""
        from nova.governance.tasks import validate_governance_config_task
        
        # Setup mock config
        mock_load_config.return_value = {
            'metrics': {'RPM': 0.4, 'growth': 0.3, 'engagement': 0.3},
            'thresholds': {'promote': 1.0, 'retire': -1.0},
            'auto_actions': False
        }
        
        # Create mock task instance
        mock_task = MagicMock()
        mock_task.request.id = 'validation-task-id'
        
        # Execute validation
        result = validate_governance_config_task(mock_task)
        
        assert result['status'] == 'completed'
        assert result['valid'] is True
        assert 'validation_results' in result


class TestMaintenanceTasks:
    """Test maintenance-related Celery tasks."""
    
    @patch('nova.maintenance.tasks.memory_cleanup')
    @patch('nova.maintenance.tasks._load_memory_limit')
    def test_memory_cleanup_task(self, mock_load_limit, mock_cleanup):
        """Test memory cleanup task execution."""
        from nova.maintenance.tasks import memory_cleanup_task
        
        # Setup mocks
        mock_load_limit.return_value = 512  # 512MB limit
        mock_cleanup.return_value = {
            'cleaned_items': 10,
            'memory_freed_mb': 50
        }
        
        # Create mock task instance
        mock_task = MagicMock()
        mock_task.request.id = 'cleanup-task-id'
        mock_task.request.retries = 0
        
        # Execute task
        result = memory_cleanup_task(mock_task, max_age_hours=24)
        
        assert result['status'] == 'completed'
        assert result['cleaned_items'] == 10
        assert result['memory_freed_mb'] == 50
        assert result['max_age_hours'] == 24
        assert result['memory_limit_mb'] == 512
    
    def test_system_health_check_task(self):
        """Test system health check task."""
        from nova.maintenance.tasks import system_health_check_task
        
        # Create mock task instance
        mock_task = MagicMock()
        mock_task.request.id = 'health-check-id'
        
        # Mock the health check functions
        with patch('nova.maintenance.tasks._check_disk_space') as mock_disk, \
             patch('nova.maintenance.tasks._check_memory_usage') as mock_memory, \
             patch('nova.maintenance.tasks._check_database_connection') as mock_db, \
             patch('nova.maintenance.tasks._check_redis_connection') as mock_redis, \
             patch('nova.maintenance.tasks._check_config_files') as mock_config:
            
            # Setup health check results
            mock_disk.return_value = {'healthy': True, 'free_percent': 45.0}
            mock_memory.return_value = {'healthy': True, 'used_percent': 65.0}
            mock_db.return_value = {'healthy': True, 'status': 'connected'}
            mock_redis.return_value = {'healthy': True, 'status': 'connected'}
            mock_config.return_value = {'healthy': True, 'files': {}}
            
            # Execute health check
            result = system_health_check_task(mock_task)
            
            assert result['status'] == 'completed'
            assert result['overall_healthy'] is True
            assert result['healthy_checks'] == 5
            assert result['total_checks'] == 5


class TestMetricsTasks:
    """Test metrics-related Celery tasks."""
    
    @patch('nova.metrics.tasks.aggregate_metrics')
    @patch('nova.metrics.tasks.PromptLeaderboard')
    @patch('nova.metrics.tasks.top_prompts')
    def test_daily_metrics_processing(self, mock_top_prompts, mock_leaderboard_class, mock_aggregate):
        """Test daily metrics processing task."""
        from nova.metrics.tasks import process_daily_metrics_task
        
        # Setup mocks
        mock_aggregate.return_value = {'total_requests': 1000, 'avg_rpm': 2.5}
        mock_top_prompts.return_value = [
            {'id': 'prompt1', 'metrics': {'rpm': 3.0}},
            {'id': 'prompt2', 'metrics': {'rpm': 2.8}}
        ]
        
        mock_leaderboard = MagicMock()
        mock_leaderboard_class.return_value = mock_leaderboard
        
        # Create mock task instance
        mock_task = MagicMock()
        mock_task.request.id = 'metrics-task-id'
        
        # Execute task
        result = process_daily_metrics_task(mock_task)
        
        assert result['status'] == 'completed'
        assert result['successful_operations'] >= 0
        assert 'results' in result


class TestTaskIntegration:
    """Test task integration and scheduling."""
    
    def test_task_autodiscovery(self):
        """Test that tasks are properly autodiscovered."""
        from nova.celery_app import celery_app
        
        # Check that tasks are registered
        registered_tasks = list(celery_app.tasks.keys())
        
        # Should include our custom tasks
        expected_tasks = [
            'nova.governance.run_governance_task',
            'nova.maintenance.memory_cleanup_task',
            'nova.metrics.process_daily_metrics_task',
            'nova.health_check'
        ]
        
        for task in expected_tasks:
            assert task in registered_tasks
    
    @patch('redis.from_url')
    def test_redis_connectivity(self, mock_redis):
        """Test Redis broker connectivity."""
        from nova.celery_app import celery_app
        
        # Mock Redis connection
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client
        mock_redis_client.ping.return_value = True
        
        # Test broker URL configuration
        assert 'redis://' in celery_app.conf.broker_url
        assert 'redis://' in celery_app.conf.result_backend


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
