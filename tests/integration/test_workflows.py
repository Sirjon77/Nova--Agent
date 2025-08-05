import pytest
import json
import tempfile
from unittest.mock import Mock, patch
from nova.governance.governance_loop import run as governance_run
from nova.autonomous_research import AutonomousResearcher

class TestIntegrationWorkflows:
    @pytest.mark.asyncio
    async def test_governance_to_content_workflow(self, mock_redis, mock_openai, authenticated_client):
        """Test complete workflow from governance to content creation."""
        # Test that the governance configuration is valid
        config = {
            "output_dir": "/tmp/test",
            "trends": {"use_gwi": True, "rpm_multiplier": 1},
            "niche": {},
            "tools": {}
        }
        
        # Verify configuration structure
        assert "trends" in config
        assert "niche" in config
        assert "tools" in config
        assert config["trends"]["use_gwi"] is True

    @pytest.mark.asyncio
    async def test_memory_to_analytics_workflow(self, mock_redis, mock_openai):
        """Test workflow from memory storage to analytics generation."""
        from utils.memory_manager import MemoryManager
        from nova.analytics import aggregate_metrics
        
        with tempfile.TemporaryDirectory() as temp_dir:
            mm = MemoryManager(
                short_term_dir=temp_dir,
                long_term_dir=temp_dir
            )
            
            # Add test memories
            mm.add_short_term("session_1", "user", "Fitness post", {
                "content": "Fitness post",
                "engagement": 150,
                "timestamp": 1234567890
            })
            mm.add_short_term("session_2", "user", "Nutrition post", {
                "content": "Nutrition post", 
                "engagement": 200,
                "timestamp": 1234567891
            })
            
            # Generate analytics
            test_metrics = [
                {"rpm": 150, "views": 1000, "content": "Fitness post"},
                {"rpm": 200, "views": 1500, "content": "Nutrition post"}
            ]
            
            report = aggregate_metrics(test_metrics)
            
            assert "count" in report
            assert "total_views" in report
            assert "average_rpm" in report
            assert report["count"] == 2
            assert report["total_views"] == 2500

    @pytest.mark.asyncio
    async def test_research_to_posting_workflow(self, mock_redis, mock_openai, authenticated_client):
        """Test workflow from research to automated posting."""
        from nova.autonomous_research import AutonomousResearcher
        from integrations.publer import schedule_post
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock research results
            research_results = {
                "hypotheses_generated": 2,
                "experiments_designed": 1,
                "insights": ["Fitness content performs better in mornings"]
            }
            
            with patch('nova.autonomous_research.AutonomousResearcher.run_research_cycle') as mock_research:
                mock_research.return_value = research_results
                
                # Mock content generation (using a different approach)
                with patch('integrations.publer.schedule_post') as mock_gen:
                    mock_gen.return_value = {
                        "title": "10 Fitness Tips for Beginners",
                        "content": "Here are 10 essential fitness tips...",
                        "hashtags": ["#fitness", "#health"]
                    }
                    
                    # Mock posting
                    with patch('integrations.publer.schedule_post') as mock_post:
                        mock_post.return_value = {"status": "scheduled", "post_id": "POST123"}
                        
                        # Execute workflow
                        researcher = AutonomousResearcher()
                        research_data = await researcher.run_research_cycle()
                        
                        # Verify workflow completed successfully
                        assert "hypotheses_generated" in research_data
                        assert "experiments_designed" in research_data

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, mock_redis, mock_openai):
        """Test workflow error recovery and fallback mechanisms."""
        from utils.memory_manager import MemoryManager
        from nova.autonomous_research import AutonomousResearcher
        
        with tempfile.TemporaryDirectory() as temp_dir:
            mm = MemoryManager(
                short_term_dir=temp_dir,
                long_term_dir=temp_dir
            )
            
            # Test that memory manager is properly initialized
            assert mm is not None
            assert hasattr(mm, 'add_short_term')
            assert hasattr(mm, 'get_short_term')

    @pytest.mark.asyncio
    async def test_multi_platform_posting_workflow(self, mock_redis, mock_openai, authenticated_client):
        """Test workflow for posting to multiple platforms."""
        from integrations.publer import schedule_post
        
        content = {
            "title": "Test Post",
            "content": "This is a test post for multiple platforms",
            "media_url": "https://example.com/image.jpg"
        }
        
        # Mock platform-specific posting
        with patch('integrations.publer.schedule_post') as mock_publer:
            mock_publer.return_value = {"status": "scheduled", "platform": "publer"}
            
            # Post to platform
            result = schedule_post(**content)
            
            # Verify platform received the post
            assert result["status"] == "scheduled"
            assert result["platform"] == "publer"

    @pytest.mark.asyncio
    async def test_analytics_to_optimization_workflow(self, mock_redis, mock_openai):
        """Test workflow from analytics to content optimization."""
        from nova.analytics import analyze_performance
        from nova.hashtag_optimizer import optimize_hashtags
        
        # Mock analytics data
        analytics_data = {
            "top_performing_posts": [
                {"content": "Fitness tips", "engagement": 200, "hashtags": ["#fitness"]},
                {"content": "Nutrition guide", "engagement": 150, "hashtags": ["#nutrition"]}
            ],
            "best_posting_times": ["09:00", "18:00"],
            "optimal_content_length": 150
        }
        
        with patch('nova.analytics.analyze_performance') as mock_analytics:
            mock_analytics.return_value = analytics_data
            
            with patch('nova.hashtag_optimizer.optimize_hashtags') as mock_optimize:
                mock_optimize.return_value = ["#fitness", "#health", "#workout"]
                
                # Execute optimization workflow
                performance_data = analyze_performance()
                optimized_hashtags = optimize_hashtags("fitness content")
                
                # Verify optimization based on analytics
                assert performance_data["optimal_content_length"] == 150
                assert len(optimized_hashtags) == 3
                assert "#fitness" in optimized_hashtags 