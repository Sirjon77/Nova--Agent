"""
Content Selection Engine for Nova Agent

This module implements content selection logic with policy enforcement,
including the silent video ratio requirement (1 in 3 posts silent).
"""

import math
import random
import yaml
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import logging

# Import Prometheus metrics for monitoring
try:
    from nova.metrics import (
        silent_video_ratio_compliance, 
        silent_video_ratio_actual,
        content_posts_processed,
        silent_posts_generated
    )
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class ContentPost:
    """Represents a content post with metadata and policy flags."""
    post_id: str
    content_type: str  # 'short_form', 'long_form', etc.
    duration: int  # Duration in seconds
    category: str
    channel: str
    platform: str
    scheduled_time: Optional[datetime] = None
    silent_mode: bool = False
    audio_track: str = "narration"  # 'narration', 'music', 'both'
    include_avatar: bool = True
    policy_exempt: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SelectionConfig:
    """Configuration for content selection policies."""
    silent_video_ratio: float = 0.33
    max_duration: int = 60
    exempt_categories: List[str] = field(default_factory=lambda: ["Twinkle Tales & Tunes"])
    avatar_for_silent_enabled: bool = True
    engagement_threshold: float = 0.05

class ContentSelector:
    """Main content selection engine with policy enforcement."""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = self._load_config(config_path)
        
    def _load_config(self, config_path: str) -> SelectionConfig:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                settings = yaml.safe_load(f)
            
            content_cfg = settings.get('content', {}).get('short_form', {})
            avatar_cfg = content_cfg.get('avatar_for_silent', {})
            
            return SelectionConfig(
                silent_video_ratio=content_cfg.get('silent_video_ratio', 0.33),
                max_duration=content_cfg.get('max_duration', 60),
                exempt_categories=content_cfg.get('exempt_categories', ["Twinkle Tales & Tunes"]),
                avatar_for_silent_enabled=avatar_cfg.get('enabled', True),
                engagement_threshold=avatar_cfg.get('engagement_threshold', 0.05)
            )
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}. Using defaults.")
            return SelectionConfig()
    
    def enforce_silent_video_ratio(self, posts: List[ContentPost]) -> List[ContentPost]:
        """
        Enforce the silent video ratio policy on a batch of posts.
        
        Args:
            posts: List of ContentPost objects to process
            
        Returns:
            List of ContentPost objects with silent_mode flags set
        """
        # Filter eligible posts for silent video enforcement
        eligible_posts = self._get_eligible_posts(posts)
        
        if not eligible_posts:
            logger.info("No eligible posts for silent video ratio enforcement")
            return posts
        
        # Calculate target number of silent videos
        N = len(eligible_posts)
        target_silent_count = math.ceil(N * self.config.silent_video_ratio)
        
        logger.info(f"Enforcing silent ratio: {target_silent_count}/{N} posts will be silent "
                   f"(ratio: {self.config.silent_video_ratio})")
        
        # Randomly select posts to be silent (for distribution)
        if target_silent_count > 0:
            silent_posts = random.sample(eligible_posts, k=min(target_silent_count, N))
            
            for post in silent_posts:
                self._configure_silent_post(post)
        
        # Ensure non-silent posts have narration
        non_silent_posts = [p for p in eligible_posts if not p.silent_mode]
        for post in non_silent_posts:
            self._configure_narrated_post(post)
        
        # Update metrics after processing
        self._update_metrics(posts)
        
        return posts
    
    def _get_eligible_posts(self, posts: List[ContentPost]) -> List[ContentPost]:
        """Filter posts eligible for silent video ratio enforcement."""
        eligible = []
        
        for post in posts:
            # Skip if already exempt
            if post.policy_exempt:
                continue
                
            # Only apply to short-form content
            if post.content_type != 'short_form':
                continue
                
            # Skip videos that are too long
            if post.duration >= self.config.max_duration:
                logger.debug(f"Post {post.post_id} too long ({post.duration}s >= {self.config.max_duration}s)")
                continue
                
            # Skip exempt categories
            if post.category in self.config.exempt_categories:
                logger.debug(f"Post {post.post_id} category '{post.category}' is exempt")
                continue
                
            eligible.append(post)
        
        return eligible
    
    def _configure_silent_post(self, post: ContentPost) -> None:
        """Configure a post to be silent (no spoken dialogue)."""
        post.silent_mode = True
        post.audio_track = "music"  # Use background music instead of narration
        
        # Data-driven avatar decision
        if self.config.avatar_for_silent_enabled:
            post.include_avatar = self._should_use_avatar_for_silent(post)
        else:
            post.include_avatar = False
            
        logger.debug(f"Configured post {post.post_id} as silent (avatar: {post.include_avatar})")
    
    def _configure_narrated_post(self, post: ContentPost) -> None:
        """Configure a post to have narration."""
        post.silent_mode = False
        post.audio_track = "narration"
        post.include_avatar = True  # Default for narrated content
        
        logger.debug(f"Configured post {post.post_id} with narration")
    
    def _should_use_avatar_for_silent(self, post: ContentPost) -> bool:
        """
        Data-driven decision on whether to include avatar in silent videos.
        
        This is a placeholder that should be replaced with actual analytics.
        In practice, this would check historical engagement data for the
        channel/niche to determine if avatar presence improves performance.
        """
        # Placeholder logic - in practice, query analytics for this channel/category
        engagement_data = self._get_historical_engagement(post.channel, post.category)
        
        if engagement_data:
            avatar_improvement = engagement_data.get('avatar_improvement', 0.0)
            return avatar_improvement >= self.config.engagement_threshold
        
        # Default to including avatar if no data available
        return True
    
    def _get_historical_engagement(self, channel: str, category: str) -> Optional[Dict[str, float]]:
        """
        Get historical engagement data for avatar decisions.
        
        This is a placeholder that should be replaced with real analytics queries.
        """
        # Placeholder - return simulated data
        # In practice, this would query the analytics database
        channel_avatar_performance = {
            "WealthWise": {"avatar_improvement": 0.08},
            "TechPulse": {"avatar_improvement": 0.12}, 
            "Living Luxe": {"avatar_improvement": 0.03},
            "GlamLab": {"avatar_improvement": 0.15},
            "Viral Vortex": {"avatar_improvement": 0.06},
            "HypeHub": {"avatar_improvement": 0.04}
        }
        
        return channel_avatar_performance.get(channel, {"avatar_improvement": 0.06})
    
    def distribute_silent_posts(self, posts: List[ContentPost]) -> List[ContentPost]:
        """
        Distribute silent posts evenly throughout the schedule to avoid clustering.
        
        Args:
            posts: List of posts already marked with silent_mode
            
        Returns:
            Reordered list with better distribution of silent posts
        """
        if len(posts) <= 1:
            return posts
            
        silent_posts = [p for p in posts if p.silent_mode]
        non_silent_posts = [p for p in posts if not p.silent_mode]
        
        if not silent_posts:
            return posts
            
        # Simple distribution: interleave silent posts among non-silent ones
        result = []
        silent_idx = 0
        
        # Calculate spacing
        total_posts = len(posts)
        silent_count = len(silent_posts)
        spacing = total_posts // silent_count if silent_count > 0 else total_posts
        
        for i, post in enumerate(posts):
            if post.silent_mode:
                continue  # Skip, we'll place these strategically
                
            result.append(post)
            
            # Insert a silent post at regular intervals
            if (silent_idx < len(silent_posts) and 
                len(result) % max(1, spacing) == 0):
                result.append(silent_posts[silent_idx])
                silent_idx += 1
        
        # Add any remaining silent posts
        while silent_idx < len(silent_posts):
            result.append(silent_posts[silent_idx])
            silent_idx += 1
            
        logger.info(f"Distributed {len(silent_posts)} silent posts among {len(result)} total posts")
        return result
    
    def validate_ratio_compliance(self, posts: List[ContentPost]) -> Dict[str, Any]:
        """
        Validate that the silent video ratio is met.
        
        Returns compliance metrics and any violations.
        """
        eligible_posts = self._get_eligible_posts(posts)
        
        if not eligible_posts:
            return {"compliant": True, "reason": "no_eligible_posts"}
            
        total_eligible = len(eligible_posts)
        silent_count = sum(1 for p in eligible_posts if p.silent_mode)
        actual_ratio = silent_count / total_eligible if total_eligible > 0 else 0
        
        # Allow some tolerance for small batches
        tolerance = 0.1
        target_ratio = self.config.silent_video_ratio
        compliant = abs(actual_ratio - target_ratio) <= tolerance
        
        return {
            "compliant": compliant,
            "target_ratio": target_ratio,
            "actual_ratio": actual_ratio,
            "silent_count": silent_count,
            "total_eligible": total_eligible,
            "tolerance": tolerance
        }
    
    def _update_metrics(self, posts: List[ContentPost]) -> None:
        """Update Prometheus metrics for monitoring."""
        if not METRICS_AVAILABLE:
            return
            
        try:
            # Group posts by channel for per-channel metrics
            channels = {}
            for post in posts:
                if post.channel not in channels:
                    channels[post.channel] = {
                        "total": 0,
                        "eligible": 0,
                        "silent": 0,
                        "posts": []
                    }
                channels[post.channel]["total"] += 1
                channels[post.channel]["posts"].append(post)
            
            # Calculate metrics per channel
            for channel, data in channels.items():
                # Count eligible posts for this channel
                eligible_posts = self._get_eligible_posts(data["posts"])
                data["eligible"] = len(eligible_posts)
                data["silent"] = sum(1 for p in eligible_posts if p.silent_mode)
                
                # Update content processing counter
                for post in data["posts"]:
                    content_posts_processed.labels(
                        content_type=post.content_type,
                        channel=channel
                    ).inc()
                
                # Update silent post counter
                for post in eligible_posts:
                    if post.silent_mode:
                        silent_posts_generated.labels(
                            channel=channel,
                            avatar_included=str(post.include_avatar).lower()
                        ).inc()
                
                # Calculate and update ratio metrics
                if data["eligible"] > 0:
                    actual_ratio = data["silent"] / data["eligible"]
                    silent_video_ratio_actual.labels(channel=channel).set(actual_ratio)
                    
                    # Check compliance
                    tolerance = 0.1
                    target_ratio = self.config.silent_video_ratio
                    compliant = abs(actual_ratio - target_ratio) <= tolerance
                    silent_video_ratio_compliance.labels(channel=channel).set(1 if compliant else 0)
                    
                    logger.debug(f"Metrics updated for channel {channel}: "
                               f"ratio={actual_ratio:.2f}, compliant={compliant}")
                else:
                    # No eligible posts, mark as compliant
                    silent_video_ratio_compliance.labels(channel=channel).set(1)
                    silent_video_ratio_actual.labels(channel=channel).set(0)
                    
        except Exception as e:
            logger.warning(f"Failed to update metrics: {e}")
    
    def monitor_daily_compliance(self, posts_last_24h: List[ContentPost]) -> Dict[str, Any]:
        """
        Monitor compliance for posts from the last 24 hours.
        
        This method is intended to be called by the governance loop
        to check if channels are meeting the silent video ratio policy.
        """
        compliance_report = {
            "overall_compliant": True,
            "channels": {},
            "violations": [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Group posts by channel
        channels = {}
        for post in posts_last_24h:
            if post.channel not in channels:
                channels[post.channel] = []
            channels[post.channel].append(post)
        
        # Check compliance per channel
        for channel, channel_posts in channels.items():
            compliance = self.validate_ratio_compliance(channel_posts)
            compliance_report["channels"][channel] = compliance
            
            # Only consider it a violation if there are eligible posts
            if not compliance["compliant"] and compliance.get("total_eligible", 0) > 0:
                compliance_report["overall_compliant"] = False
                violation = {
                    "channel": channel,
                    "target_ratio": compliance.get("target_ratio", 0),
                    "actual_ratio": compliance.get("actual_ratio", 0),
                    "silent_count": compliance.get("silent_count", 0),
                    "total_eligible": compliance.get("total_eligible", 0)
                }
                compliance_report["violations"].append(violation)
                
                actual_ratio = compliance.get("actual_ratio", 0)
                target_ratio = compliance.get("target_ratio", 0)
                logger.warning(f"Silent ratio violation in channel {channel}: "
                             f"{actual_ratio:.1%} vs target {target_ratio:.1%}")
        
        return compliance_report

def create_sample_posts() -> List[ContentPost]:
    """Create sample posts for testing."""
    sample_posts = [
        ContentPost("post_1", "short_form", 45, "Finance", "WealthWise", "youtube"),
        ContentPost("post_2", "short_form", 30, "Tech", "TechPulse", "tiktok"),  
        ContentPost("post_3", "short_form", 35, "Lifestyle", "Living Luxe", "instagram"),
        ContentPost("post_4", "short_form", 50, "Beauty", "GlamLab", "youtube"),
        ContentPost("post_5", "short_form", 25, "Viral", "Viral Vortex", "tiktok"),
        ContentPost("post_6", "long_form", 180, "Education", "TechPulse", "youtube"),  # Should be exempt
        ContentPost("post_7", "short_form", 40, "Twinkle Tales & Tunes", "Twinkle Tales & Tunes", "youtube"),  # Exempt category
        ContentPost("post_8", "short_form", 35, "Promo", "HypeHub", "instagram"),
        ContentPost("post_9", "short_form", 55, "Finance", "WealthWise", "tiktok"),
    ]
    return sample_posts

# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create content selector
    selector = ContentSelector()
    
    # Generate sample posts
    posts = create_sample_posts()
    print(f"Created {len(posts)} sample posts")
    
    # Apply silent video ratio enforcement
    processed_posts = selector.enforce_silent_video_ratio(posts)
    
    # Distribute posts
    distributed_posts = selector.distribute_silent_posts(processed_posts)
    
    # Validate compliance
    compliance = selector.validate_ratio_compliance(distributed_posts)
    
    # Report results
    print(f"\nRatio compliance: {compliance}")
    
    eligible_posts = selector._get_eligible_posts(distributed_posts)
    silent_posts = [p for p in eligible_posts if p.silent_mode]
    
    print(f"\nEligible posts: {len(eligible_posts)}")
    print(f"Silent posts: {len(silent_posts)}")
    print(f"Actual ratio: {len(silent_posts)/len(eligible_posts) if eligible_posts else 0:.2%}")
    
    print("\nPost details:")
    for post in distributed_posts:
        status = "SILENT" if post.silent_mode else "NARRATED"
        eligible = "✓" if post in eligible_posts else "✗"
        print(f"  {post.post_id}: {post.category} ({post.duration}s) - {status} - Eligible: {eligible}")
