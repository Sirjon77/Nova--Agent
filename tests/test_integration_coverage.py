"""
Additional integration tests to improve coverage for modules below 90%.

These tests focus on edge cases and error conditions to achieve ≥90% coverage.
"""
import os
import sys
import pytest
import requests
from unittest.mock import patch, MagicMock

# Add current directory to Python path
sys.path.insert(0, os.path.abspath('.'))

import integrations.metricool as metricool
import integrations.publer as publer
import nova.ab_testing as ab_testing
import nova.approvals as approvals
import nova.automation_flags as automation_flags

class TestMetricoolCoverage:
    """Additional tests for metricool integration to improve coverage."""
    
    def test_get_metrics_missing_token(self, monkeypatch):
        """Test get_metrics with missing API token."""
        monkeypatch.delenv("METRICOOL_API_TOKEN", raising=False)
        with pytest.raises(ValueError) as excinfo:
            metricool.get_metrics("test_account")
        assert "METRICOOL_API_TOKEN" in str(excinfo.value)
    
    def test_get_metrics_http_error(self, monkeypatch):
        """Test get_metrics with HTTP error response."""
        # Need to patch the module-level variables
        monkeypatch.setattr(metricool, 'METRICOOL_API_TOKEN', 'test-token')
        monkeypatch.setattr(metricool, 'METRICOOL_ACCOUNT_ID', 'test-account')
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_get.return_value = mock_response
            
            with pytest.raises(metricool.MetricoolError) as excinfo:
                metricool.get_metrics("test_account")
            assert "401" in str(excinfo.value)
    
    def test_get_metrics_invalid_json(self, monkeypatch):
        """Test get_metrics with invalid JSON response."""
        # Need to patch the module-level variables
        monkeypatch.setattr(metricool, 'METRICOOL_API_TOKEN', 'test-token')
        monkeypatch.setattr(metricool, 'METRICOOL_ACCOUNT_ID', 'test-account')
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_get.return_value = mock_response
            
            with pytest.raises(metricool.MetricoolError) as excinfo:
                metricool.get_metrics("test_account")
            assert "Invalid JSON" in str(excinfo.value)
    
    def test_get_metrics_success_with_data(self, monkeypatch):
        """Test get_metrics with successful response and data."""
        # Need to patch the module-level variables
        monkeypatch.setattr(metricool, 'METRICOOL_API_TOKEN', 'test-token')
        monkeypatch.setattr(metricool, 'METRICOOL_ACCOUNT_ID', 'test-account')
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [
                    {"metric": "engagement", "value": 85},
                    {"metric": "reach", "value": 1200}
                ]
            }
            mock_get.return_value = mock_response
            
            result = metricool.get_metrics("test_account")
            assert isinstance(result, dict)
            assert "data" in result
            assert len(result["data"]) == 2
            assert result["data"][0]["metric"] == "engagement"

class TestPublerCoverage:
    """Additional tests for publer integration to improve coverage."""
    
    def test_schedule_post_missing_credentials(self, monkeypatch):
        """Test schedule_post with missing credentials."""
        # Need to patch the module-level variables
        monkeypatch.setattr(publer, 'PUBLER_API_KEY', None)
        monkeypatch.setattr(publer, 'PUBLER_WORKSPACE_ID', None)
        
        with pytest.raises(ValueError) as excinfo:
            publer.schedule_post("Test content")
        assert "Publer API key" in str(excinfo.value)
    
    def test_schedule_post_http_error(self, monkeypatch):
        """Test schedule_post with HTTP error response."""
        # Need to patch the module-level variables and automation flags
        monkeypatch.setattr(publer, 'PUBLER_API_KEY', 'test-key')
        monkeypatch.setattr(publer, 'PUBLER_WORKSPACE_ID', 'test-workspace')
        
        with patch('nova.automation_flags.is_posting_enabled', return_value=True), \
             patch('nova.automation_flags.is_approval_required', return_value=False), \
             patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_post.return_value = mock_response
            
            with pytest.raises(publer.PublerError) as excinfo:
                publer.schedule_post("Test content")
            assert "400" in str(excinfo.value)
    
    def test_schedule_post_success_with_scheduling(self, monkeypatch):
        """Test schedule_post with scheduling options."""
        # Need to patch the module-level variables and automation flags
        monkeypatch.setattr(publer, 'PUBLER_API_KEY', 'test-key')
        monkeypatch.setattr(publer, 'PUBLER_WORKSPACE_ID', 'test-workspace')
        
        with patch('nova.automation_flags.is_posting_enabled', return_value=True), \
             patch('nova.automation_flags.is_approval_required', return_value=False), \
             patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "id": "post_123",
                "status": "scheduled",
                "scheduled_at": "2025-01-15T10:00:00Z"
            }
            mock_post.return_value = mock_response
            
            from datetime import datetime, timezone
            scheduled_time = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
            
            result = publer.schedule_post(
                "Test content", 
                platforms=["facebook"], 
                scheduled_time=scheduled_time
            )
            assert result["id"] == "post_123"
            assert result["status"] == "scheduled"

class TestAbTestingCoverage:
    """Additional tests for ab_testing to improve coverage."""
    
    def test_create_test_invalid_variants(self):
        """Test create_test with invalid variants."""
        from nova.ab_testing import ABTestManager
        manager = ABTestManager()
        with pytest.raises(ValueError) as excinfo:
            manager.create_test("test_name", [])
        assert "variants" in str(excinfo.value)
    
    def test_choose_variant_nonexistent(self):
        """Test choose_variant for non-existent test."""
        from nova.ab_testing import ABTestManager
        manager = ABTestManager()
        with pytest.raises(KeyError) as excinfo:
            manager.choose_variant("nonexistent_test")
        assert "does not exist" in str(excinfo.value)
    
    def test_get_test_nonexistent(self):
        """Test get_test for non-existent test."""
        from nova.ab_testing import ABTestManager
        manager = ABTestManager()
        with pytest.raises(KeyError) as excinfo:
            manager.get_test("nonexistent_test")
        assert "does not exist" in str(excinfo.value)

class TestApprovalsCoverage:
    """Additional tests for approvals to improve coverage."""
    
    def test_get_draft_nonexistent(self):
        """Test get_draft with non-existent draft ID."""
        result = approvals.get_draft("nonexistent_id")
        assert result is None
    
    def test_approve_draft_nonexistent(self):
        """Test approve_draft with non-existent draft ID."""
        result = approvals.approve_draft("nonexistent_id")
        assert result is None
    
    def test_reject_draft_nonexistent(self):
        """Test reject_draft with non-existent draft ID."""
        result = approvals.reject_draft("nonexistent_id")
        assert result is None
    
    def test_list_drafts_empty(self):
        """Test list_drafts when no drafts exist."""
        result = approvals.list_drafts()
        assert isinstance(result, list)

class TestAutomationFlagsCoverage:
    """Additional tests for automation_flags to improve coverage."""
    
    def test_set_flags_invalid(self):
        """Test set_flags with invalid parameters."""
        with pytest.raises(TypeError):
            automation_flags.set_flags("invalid")
    
    def test_get_flags(self):
        """Test get_flags functionality."""
        flags = automation_flags.get_flags()
        assert isinstance(flags, dict)
    
    def test_set_posting_enabled(self):
        """Test set_posting_enabled functionality."""
        result = automation_flags.set_posting_enabled(True)
        assert isinstance(result, dict)
        assert automation_flags.is_posting_enabled() is True
    
    def test_set_generation_enabled(self):
        """Test set_generation_enabled functionality."""
        result = automation_flags.set_generation_enabled(False)
        assert isinstance(result, dict)
        assert automation_flags.is_generation_enabled() is False
    
    def test_set_approval_required(self):
        """Test set_approval_required functionality."""
        result = automation_flags.set_approval_required(True)
        assert isinstance(result, dict)
        assert automation_flags.is_approval_required() is True 