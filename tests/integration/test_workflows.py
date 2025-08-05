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
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock trend scanner to return dummy trends
            dummy_trends = [
                {
                    "keyword": "fitness",
                    "interest": 100,
                    "projected_rpm": 80,
                    "scanned_on": "2025-08-01"
                }
            ]
            
            with patch('nova.governance.trend_scanner.TrendScanner.scan') as mock_scan:
                mock_scan.return_value = dummy_trends
                
                # Mock research cycle
                with patch('nova.autonomous_research.AutonomousResearcher.run_research_cycle') as mock_research:
                    mock_research.return_value = {
                        "hypotheses_generated": 2,
                        "experiments_designed": 1,
                        "insights": ["Fitness content performs better in mornings"]
                    }
                    
                    # Mock Publer integration
                    with patch('integrations.publer.schedule_post') as mock_schedule:
                        mock_schedule.return_value = {
                            "pending_approval": True,
                            "approval_id": "DRAFT123"
                        }
                        
                        # Run governance loop
                        config = {
                            "output_dir": temp_dir,
                            "trends": {"use_gwi": True, "rpm_multiplier": 1},
                            "niche": {},
                            "tools": {}
                        }
                        
                        from nova.governance.governance_loop import run as governance_run
                        report = await governance_run(
                            config, 
                            channel_metrics=[], 
                            trend_seeds=["fitness"], 
                            tools_cfg=[]
                        )
                        
                        # Verify governance found trends
                        assert any(item.get("keyword") == "fitness" for item in report["trends"])
                        
                        # Verify research was conducted and content was scheduled
                        mock_research.assert_called()
                        mock_schedule.assert_called()

    @pytest.mark.asyncio
    async def test_memory_to_analytics_workflow(self, mock_redis, mock_openai):
        """Test workflow from memory storage to analytics generation."""
        from utils.memory_manager import MemoryManager
        from nova.analytics import generate_analytics_report
        
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
            with patch('nova.analytics.generate_analytics_report') as mock_analytics:
                mock_analytics.return_value = {
                    "total_posts": 2,
                    "avg_engagement": 175,
                    "top_content": "Nutrition post"
                }
                
                report = generate_analytics_report(mm)
                
                assert report["total_posts"] == 2
                assert report["avg_engagement"] == 175

    @pytest.mark.asyncio
    async def test_research_to_posting_workflow(self, mock_redis, mock_openai, authenticated_client):
        """Test workflow from research to automated posting."""
        from nova.autonomous_research import AutonomousResearcher
        from integrations.publer import schedule_post
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock research results
            research_results = {
                "trends": ["fitness", "nutrition"],
                "content_ideas": ["10 fitness tips", "Healthy meal prep"],
                "best_times": ["09:00", "18:00"]
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
                        research_data = await researcher.research_topic("fitness")
                        post_content = await researcher.generate_post(research_data)
                        post_result = schedule_post(**post_content)
                        
                        # Verify workflow completed successfully
                        assert research_data["trends"] == ["fitness", "nutrition"]
                        assert post_content["title"] == "10 Fitness Tips for Beginners"
                        assert post_result["status"] == "scheduled"

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
            
            # Mock OpenAI failure
            with patch('utils.summarizer.chat_completion', side_effect=Exception("API Error")):
                # Should fall back to file-based summarization
                result = mm.store_short("test_key", {"data": "test_value"})
                assert result is True
                
                retrieved = mm.get_short("test_key")
                assert retrieved == {"data": "test_value"}

    @pytest.mark.asyncio
    async def test_multi_platform_posting_workflow(self, mock_redis, mock_openai, authenticated_client):
        """Test workflow for posting to multiple platforms."""
        from integrations.publer import schedule_post
        from integrations.facebook import post_to_facebook
        from integrations.instagram import post_to_instagram
        
        content = {
            "title": "Test Post",
            "content": "This is a test post for multiple platforms",
            "media_url": "https://example.com/image.jpg"
        }
        
        # Mock platform-specific posting
        with patch('integrations.publer.schedule_post') as mock_publer:
            mock_publer.return_value = {"status": "scheduled", "platform": "publer"}
            
            with patch('integrations.facebook.post_to_facebook') as mock_fb:
                mock_fb.return_value = {"status": "posted", "platform": "facebook"}
                
                with patch('integrations.instagram.post_to_instagram') as mock_ig:
                    mock_ig.return_value = {"status": "posted", "platform": "instagram"}
                    
                    # Post to multiple platforms
                    results = []
                    results.append(schedule_post(**content))
                    results.append(post_to_facebook(**content))
                    results.append(post_to_instagram(**content))
                    
                    # Verify all platforms received the post
                    assert len(results) == 3
                    assert any(r["platform"] == "publer" for r in results)
                    assert any(r["platform"] == "facebook" for r in results)
                    assert any(r["platform"] == "instagram" for r in results)

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