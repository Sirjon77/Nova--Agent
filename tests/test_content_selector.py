"""
Unit tests for the content selector module, particularly silent video ratio enforcement.
"""

import pytest
import tempfile
import yaml
from unittest.mock import patch
from nova.content.selector import ContentSelector, ContentPost, SelectionConfig, create_sample_posts


class TestContentPost:
    """Test ContentPost dataclass functionality."""
    
    def test_content_post_creation(self):
        """Test basic ContentPost creation."""
        post = ContentPost(
            post_id="test_1",
            content_type="short_form", 
            duration=45,
            category="Finance",
            channel="WealthWise",
            platform="youtube"
        )
        
        assert post.post_id == "test_1"
        assert post.silent_mode is False  # Default
        assert post.include_avatar is True  # Default
        assert post.audio_track == "narration"  # Default


class TestSelectionConfig:
    """Test SelectionConfig functionality."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = SelectionConfig()
        
        assert config.silent_video_ratio == 0.33
        assert config.max_duration == 60
        assert "Twinkle Tales & Tunes" in config.exempt_categories
        assert config.avatar_for_silent_enabled is True
        assert config.engagement_threshold == 0.05


class TestContentSelector:
    """Test ContentSelector main functionality."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file for testing."""
        config_data = {
            'content': {
                'short_form': {
                    'silent_video_ratio': 0.5,  # 50% for testing
                    'max_duration': 60,
                    'exempt_categories': ['Kids Content'],
                    'avatar_for_silent': {
                        'enabled': True,
                        'engagement_threshold': 0.1
                    }
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            return f.name
    
    def test_config_loading(self, temp_config_file):
        """Test configuration loading from YAML file."""
        selector = ContentSelector(temp_config_file)
        
        assert selector.config.silent_video_ratio == 0.5
        assert "Kids Content" in selector.config.exempt_categories
        assert selector.config.engagement_threshold == 0.1
    
    def test_config_loading_fallback(self):
        """Test fallback to default config when file doesn't exist."""
        selector = ContentSelector("nonexistent_file.yaml")
        
        # Should use defaults
        assert selector.config.silent_video_ratio == 0.33
        assert "Twinkle Tales & Tunes" in selector.config.exempt_categories
    
    def test_eligible_posts_filtering(self):
        """Test filtering of posts eligible for silent ratio enforcement."""
        selector = ContentSelector()
        
        posts = [
            ContentPost("1", "short_form", 45, "Finance", "WealthWise", "youtube"),
            ContentPost("2", "short_form", 30, "Tech", "TechPulse", "tiktok"),
            ContentPost("3", "long_form", 180, "Education", "TechPulse", "youtube"),  # Too long
            ContentPost("4", "short_form", 40, "Twinkle Tales & Tunes", "Twinkle Tales & Tunes", "youtube"),  # Exempt
            ContentPost("5", "short_form", 70, "Finance", "WealthWise", "youtube"),  # Too long
            ContentPost("6", "short_form", 35, "Beauty", "GlamLab", "instagram"),
        ]
        
        # Mark one as exempt
        posts[0].policy_exempt = True
        
        eligible = selector._get_eligible_posts(posts)
        
        # Should only include posts 1 (index 1) and 5 (index 5)
        assert len(eligible) == 2
        assert eligible[0].post_id == "2"
        assert eligible[1].post_id == "6"
    
    def test_silent_ratio_enforcement_exact(self):
        """Test exact silent ratio enforcement with 3 posts."""
        selector = ContentSelector()
        
        posts = [
            ContentPost("1", "short_form", 45, "Finance", "WealthWise", "youtube"),
            ContentPost("2", "short_form", 30, "Tech", "TechPulse", "tiktok"),
            ContentPost("3", "short_form", 35, "Beauty", "GlamLab", "instagram"),
        ]
        
        # With ratio 0.33 and 3 posts, should have ceil(3 * 0.33) = 1 silent post
        processed = selector.enforce_silent_video_ratio(posts)
        
        silent_count = sum(1 for p in processed if p.silent_mode)
        assert silent_count == 1
    
    def test_silent_ratio_enforcement_five_posts(self):
        """Test silent ratio enforcement with 5 posts."""
        selector = ContentSelector()
        
        posts = [
            ContentPost(f"{i}", "short_form", 30+i*5, "Finance", "WealthWise", "youtube")
            for i in range(1, 6)
        ]
        
        # With ratio 0.33 and 5 posts, should have ceil(5 * 0.33) = 2 silent posts
        processed = selector.enforce_silent_video_ratio(posts)
        
        silent_count = sum(1 for p in processed if p.silent_mode)
        assert silent_count == 2
    
    def test_silent_ratio_enforcement_changed_ratio(self, temp_config_file):
        """Test enforcement with different ratio (50%)."""
        selector = ContentSelector(temp_config_file)  # Has 0.5 ratio
        
        posts = [
            ContentPost(f"{i}", "short_form", 30+i*5, "Finance", "WealthWise", "youtube")
            for i in range(1, 5)  # 4 posts
        ]
        
        # With ratio 0.5 and 4 posts, should have ceil(4 * 0.5) = 2 silent posts
        processed = selector.enforce_silent_video_ratio(posts)
        
        silent_count = sum(1 for p in processed if p.silent_mode)
        assert silent_count == 2
    
    def test_silent_post_configuration(self):
        """Test that silent posts are configured correctly."""
        selector = ContentSelector()
        
        posts = [
            ContentPost("1", "short_form", 45, "Finance", "WealthWise", "youtube"),
            ContentPost("2", "short_form", 30, "Tech", "TechPulse", "tiktok"),
            ContentPost("3", "short_form", 35, "Beauty", "GlamLab", "instagram"),
        ]
        
        processed = selector.enforce_silent_video_ratio(posts)
        
        # Find the silent post
        silent_post = next(p for p in processed if p.silent_mode)
        
        assert silent_post.audio_track == "music"
        # Avatar decision is data-driven, so just check it's a boolean
        assert isinstance(silent_post.include_avatar, bool)
    
    def test_narrated_post_configuration(self):
        """Test that narrated posts are configured correctly."""
        selector = ContentSelector()
        
        posts = [
            ContentPost("1", "short_form", 45, "Finance", "WealthWise", "youtube"),
            ContentPost("2", "short_form", 30, "Tech", "TechPulse", "tiktok"),
            ContentPost("3", "short_form", 35, "Beauty", "GlamLab", "instagram"),
        ]
        
        processed = selector.enforce_silent_video_ratio(posts)
        
        # Find a narrated post
        narrated_posts = [p for p in processed if not p.silent_mode]
        
        for post in narrated_posts:
            assert post.audio_track == "narration"
            assert post.include_avatar is True
    
    def test_no_eligible_posts(self):
        """Test behavior when no posts are eligible for silent enforcement."""
        selector = ContentSelector()
        
        posts = [
            ContentPost("1", "long_form", 180, "Education", "TechPulse", "youtube"),  # Too long
            ContentPost("2", "short_form", 40, "Twinkle Tales & Tunes", "Twinkle Tales & Tunes", "youtube"),  # Exempt
        ]
        
        processed = selector.enforce_silent_video_ratio(posts)
        
        # No posts should be marked silent
        silent_count = sum(1 for p in processed if p.silent_mode)
        assert silent_count == 0
    
    def test_avatar_decision_logic(self):
        """Test data-driven avatar decision for silent videos."""
        selector = ContentSelector()
        
        # Test with high-performing channel
        post = ContentPost("1", "short_form", 45, "Finance", "TechPulse", "youtube")  # High improvement
        should_include = selector._should_use_avatar_for_silent(post)
        assert should_include is True  # TechPulse has 0.12 improvement > 0.05 threshold
        
        # Test with low-performing channel  
        post = ContentPost("2", "short_form", 45, "Finance", "Living Luxe", "youtube")  # Low improvement
        should_include = selector._should_use_avatar_for_silent(post)
        assert should_include is False  # Living Luxe has 0.03 improvement < 0.05 threshold
    
    def test_distribution_spacing(self):
        """Test that silent posts are distributed evenly."""
        selector = ContentSelector()
        
        posts = [
            ContentPost(f"{i}", "short_form", 30+i*5, "Finance", "WealthWise", "youtube")
            for i in range(1, 7)  # 6 posts
        ]
        
        # Mark some as silent manually for testing distribution
        posts[0].silent_mode = True
        posts[3].silent_mode = True
        
        distributed = selector.distribute_silent_posts(posts)
        
        # Check that silent posts aren't clustered together
        silent_indices = [i for i, p in enumerate(distributed) if p.silent_mode]
        
        # With good distribution, silent posts shouldn't be adjacent
        for i in range(len(silent_indices) - 1):
            gap = silent_indices[i+1] - silent_indices[i]
            assert gap > 1, "Silent posts should not be adjacent"
    
    def test_ratio_compliance_validation(self):
        """Test compliance validation logic."""
        selector = ContentSelector()
        
        posts = [
            ContentPost(f"{i}", "short_form", 30+i*5, "Finance", "WealthWise", "youtube")
            for i in range(1, 4)  # 3 posts
        ]
        
        # Mark 1 as silent (33% ratio)
        posts[0].silent_mode = True
        
        compliance = selector.validate_ratio_compliance(posts)
        
        assert compliance["compliant"] is True
        assert compliance["target_ratio"] == 0.33
        assert compliance["actual_ratio"] == pytest.approx(0.33, abs=0.01)
        assert compliance["silent_count"] == 1
        assert compliance["total_eligible"] == 3
    
    def test_ratio_compliance_violation(self):
        """Test compliance validation when ratio is violated."""
        selector = ContentSelector()
        
        posts = [
            ContentPost(f"{i}", "short_form", 30+i*5, "Finance", "WealthWise", "youtube")
            for i in range(1, 11)  # 10 posts
        ]
        
        # Mark none as silent (0% ratio, should violate 33% target)
        
        compliance = selector.validate_ratio_compliance(posts)
        
        # Should be non-compliant due to 0% vs 33% target (> 10% tolerance)
        assert compliance["compliant"] is False
        assert compliance["actual_ratio"] == 0.0
        assert compliance["silent_count"] == 0
        assert compliance["total_eligible"] == 10


class TestSamplePosts:
    """Test the sample post generation."""
    
    def test_sample_posts_creation(self):
        """Test that sample posts are created correctly."""
        posts = create_sample_posts()
        
        assert len(posts) == 9
        
        # Check that we have the expected mix
        short_form_posts = [p for p in posts if p.content_type == "short_form"]
        long_form_posts = [p for p in posts if p.content_type == "long_form"]
        
        assert len(short_form_posts) == 8
        assert len(long_form_posts) == 1
        
        # Check exempt category exists
        exempt_posts = [p for p in posts if p.category == "Twinkle Tales & Tunes"]
        assert len(exempt_posts) == 1


class TestIntegration:
    """Integration tests for the complete workflow."""
    
    def test_complete_workflow(self):
        """Test the complete content selection workflow."""
        selector = ContentSelector()
        posts = create_sample_posts()
        
        # Step 1: Enforce silent ratio
        processed = selector.enforce_silent_video_ratio(posts)
        
        # Step 2: Distribute posts
        distributed = selector.distribute_silent_posts(processed)
        
        # Step 3: Validate compliance
        compliance = selector.validate_ratio_compliance(distributed)
        
        # Verify workflow completed successfully
        assert compliance["compliant"] is True
        assert compliance["silent_count"] > 0
        assert len(distributed) == len(posts)
        
        # Verify silent posts have correct configuration
        silent_posts = [p for p in distributed if p.silent_mode]
        for post in silent_posts:
            assert post.audio_track == "music"
            assert isinstance(post.include_avatar, bool)
    
    def test_edge_case_single_post(self):
        """Test edge case with only one eligible post."""
        selector = ContentSelector()
        
        posts = [
            ContentPost("1", "short_form", 45, "Finance", "WealthWise", "youtube"),
        ]
        
        processed = selector.enforce_silent_video_ratio(posts)
        distributed = selector.distribute_silent_posts(processed)
        compliance = selector.validate_ratio_compliance(distributed)
        
        # With 1 post and 33% ratio, ceil(1 * 0.33) = 1, so it should be silent
        assert compliance["silent_count"] == 1
        assert processed[0].silent_mode is True
    
    def test_edge_case_no_posts(self):
        """Test edge case with no posts."""
        selector = ContentSelector()
        
        posts = []
        
        processed = selector.enforce_silent_video_ratio(posts)
        distributed = selector.distribute_silent_posts(processed)
        compliance = selector.validate_ratio_compliance(distributed)
        
        assert len(processed) == 0
        assert compliance["compliant"] is True
        assert compliance["reason"] == "no_eligible_posts"


if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__, "-v"])
