"""
Unified Trend Intelligence Subsystem for Nova Agent v7.0

This module consolidates "TrendSpotter Channel" and "Nova TrendWatch" into a single,
advanced trend intelligence system. It provides comprehensive trend analysis,
semantic clustering, viral format prediction, and content ideation capabilities.

Design Goals:
- Consolidate multiple trend sources into unified interface
- Provide semantic clustering and trend analysis
- Predict viral formats and generate content ideas
- Integrate with Nova's governance and content systems
- Support real-time trend monitoring and alerts
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from nova.governance.trend_scanner import TrendScanner
from nova.policy import PolicyEnforcer

log = logging.getLogger(__name__)


class TrendSource(Enum):
    """Enumeration of trend data sources."""
    GOOGLE_TRENDS = "google_trends"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    REDDIT = "reddit"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    GWI = "gwi"
    AFFILIATE = "affiliate"
    GOOGLE_ADS = "google_ads"


@dataclass
class TrendData:
    """Structured trend data with metadata."""
    keyword: str
    interest_score: float
    projected_rpm: float
    source: TrendSource
    timestamp: datetime
    category: Optional[str] = None
    sentiment: Optional[float] = None
    velocity: Optional[float] = None
    competition_level: Optional[str] = None
    audience_demographics: Optional[Dict[str, Any]] = None


@dataclass
class TrendCluster:
    """Semantic cluster of related trends."""
    cluster_id: str
    primary_keyword: str
    related_keywords: List[str]
    cluster_score: float
    rpm_potential: float
    content_opportunities: List[str]
    viral_format_suggestions: List[str]
    created_at: datetime


@dataclass
class ContentIdea:
    """Generated content idea from trend analysis."""
    idea_id: str
    title: str
    description: str
    target_channels: List[str]
    estimated_rpm: float
    content_format: str
    hook_type: str
    hashtags: List[str]
    source_trends: List[str]
    priority_score: float


class TrendFetcherAggregator:
    """Fetches and aggregates trend data from multiple sources."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.trend_scanner = TrendScanner(config.get('trends', {}))
        self.policy_enforcer = PolicyEnforcer()
        
    async def fetch_all_trends(self, seed_keywords: List[str]) -> List[TrendData]:
        """Fetch trends from all configured sources."""
        self.policy_enforcer.enforce_tool('trend_intelligence')
        
        # Use existing TrendScanner for Google Trends and other sources
        scanner_results = await self.trend_scanner.scan(seed_keywords)
        
        trend_data = []
        for result in scanner_results:
            trend = TrendData(
                keyword=result['keyword'],
                interest_score=result['interest'],
                projected_rpm=result['projected_rpm'],
                source=TrendSource(result['source']),
                timestamp=datetime.now(),
                category=self._categorize_trend(result['keyword']),
                sentiment=self._analyze_sentiment(result['keyword']),
                velocity=self._calculate_velocity(result['keyword']),
                competition_level=self._assess_competition(result['keyword'])
            )
            trend_data.append(trend)
        
        # Add additional sources not covered by TrendScanner
        additional_trends = await self._fetch_additional_sources(seed_keywords)
        trend_data.extend(additional_trends)
        
        return trend_data
    
    def _categorize_trend(self, keyword: str) -> str:
        """Categorize trend into predefined categories."""
        categories = {
            'finance': ['money', 'invest', 'crypto', 'stock', 'finance', 'wealth'],
            'tech': ['ai', 'tech', 'gadget', 'software', 'app', 'digital'],
            'lifestyle': ['fitness', 'health', 'beauty', 'fashion', 'lifestyle'],
            'entertainment': ['game', 'movie', 'music', 'celebrity', 'viral'],
            'education': ['learn', 'study', 'course', 'skill', 'tutorial'],
            'business': ['entrepreneur', 'business', 'startup', 'marketing']
        }
        
        keyword_lower = keyword.lower()
        for category, keywords in categories.items():
            if any(kw in keyword_lower for kw in keywords):
                return category
        return 'general'
    
    def _analyze_sentiment(self, keyword: str) -> float:
        """Analyze sentiment of trend keyword (placeholder)."""
        # Placeholder implementation - would use NLP model in production
        positive_words = ['best', 'amazing', 'incredible', 'awesome', 'great']
        negative_words = ['worst', 'terrible', 'awful', 'bad', 'horrible']
        
        keyword_lower = keyword.lower()
        positive_count = sum(1 for word in positive_words if word in keyword_lower)
        negative_count = sum(1 for word in negative_words if word in keyword_lower)
        
        if positive_count > negative_count:
            return 0.7
        elif negative_count > positive_count:
            return 0.3
        else:
            return 0.5
    
    def _calculate_velocity(self, keyword: str) -> float:
        """Calculate trend velocity (placeholder)."""
        # Placeholder implementation - would use historical data in production
        return 0.6
    
    def _assess_competition(self, keyword: str) -> str:
        """Assess competition level for trend (placeholder)."""
        # Placeholder implementation - would use market analysis in production
        return 'medium'
    
    async def _fetch_additional_sources(self, seed_keywords: List[str]) -> List[TrendData]:
        """Fetch trends from additional sources not covered by TrendScanner."""
        additional_trends = []
        
        # Reddit trends (placeholder)
        try:
            reddit_trends = await self._fetch_reddit_trends(seed_keywords)
            additional_trends.extend(reddit_trends)
        except Exception as e:
            log.warning(f"Failed to fetch Reddit trends: {e}")
        
        # Twitter trends (placeholder)
        try:
            twitter_trends = await self._fetch_twitter_trends(seed_keywords)
            additional_trends.extend(twitter_trends)
        except Exception as e:
            log.warning(f"Failed to fetch Twitter trends: {e}")
        
        return additional_trends
    
    async def _fetch_reddit_trends(self, seed_keywords: List[str]) -> List[TrendData]:
        """Fetch trending topics from Reddit (placeholder)."""
        # Placeholder implementation
        return []
    
    async def _fetch_twitter_trends(self, seed_keywords: List[str]) -> List[TrendData]:
        """Fetch trending topics from Twitter (placeholder)."""
        # Placeholder implementation
        return []


class TrendFilterSemanticClusterer:
    """Filters and semantically clusters trend data."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.min_interest_threshold = config.get('min_interest_threshold', 0.3)
        self.min_rpm_threshold = config.get('min_rpm_threshold', 5.0)
    
    def filter_and_cluster(self, trends: List[TrendData]) -> List[TrendCluster]:
        """Filter trends and create semantic clusters."""
        # Filter trends by thresholds
        filtered_trends = self._filter_trends(trends)
        
        # Create semantic clusters
        clusters = self._create_semantic_clusters(filtered_trends)
        
        return clusters
    
    def _filter_trends(self, trends: List[TrendData]) -> List[TrendData]:
        """Filter trends based on interest and RPM thresholds."""
        return [
            trend for trend in trends
            if trend.interest_score >= self.min_interest_threshold
            and trend.projected_rpm >= self.min_rpm_threshold
        ]
    
    def _create_semantic_clusters(self, trends: List[TrendData]) -> List[TrendCluster]:
        """Create semantic clusters from filtered trends."""
        clusters = []
        
        # Group by category first
        category_groups = {}
        for trend in trends:
            category = trend.category or 'general'
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(trend)
        
        # Create clusters within each category
        for category, category_trends in category_groups.items():
            # Simple clustering by keyword similarity (placeholder)
            # In production, would use more sophisticated NLP clustering
            cluster = TrendCluster(
                cluster_id=f"cluster_{category}_{len(clusters)}",
                primary_keyword=category_trends[0].keyword,
                related_keywords=[t.keyword for t in category_trends],
                cluster_score=sum(t.interest_score for t in category_trends) / len(category_trends),
                rpm_potential=sum(t.projected_rpm for t in category_trends) / len(category_trends),
                content_opportunities=self._generate_content_opportunities(category_trends),
                viral_format_suggestions=self._suggest_viral_formats(category_trends),
                created_at=datetime.now()
            )
            clusters.append(cluster)
        
        return clusters
    
    def _generate_content_opportunities(self, trends: List[TrendData]) -> List[str]:
        """Generate content opportunities from trend cluster."""
        opportunities = []
        for trend in trends:
            opportunities.extend([
                f"Top 10 {trend.keyword} tips",
                f"How to {trend.keyword} in 2024",
                f"Best {trend.keyword} strategies",
                f"{trend.keyword} explained",
                f"Why {trend.keyword} is trending"
            ])
        return opportunities[:10]  # Limit to top 10
    
    def _suggest_viral_formats(self, trends: List[TrendData]) -> List[str]:
        """Suggest viral content formats for trend cluster."""
        formats = [
            "Before/After transformation",
            "Day in the life",
            "Myth busting",
            "Expert interview",
            "Behind the scenes",
            "Challenge video",
            "Tutorial/How-to",
            "Comparison video",
            "Story time",
            "Reaction video"
        ]
        return formats[:5]  # Return top 5 formats


class TrendAnalyzerEnrichment:
    """Analyzes and enriches trend data with additional insights."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def analyze_trends(self, clusters: List[TrendCluster]) -> List[Dict[str, Any]]:
        """Analyze trend clusters and provide insights."""
        analysis_results = []
        
        for cluster in clusters:
            analysis = {
                'cluster_id': cluster.cluster_id,
                'primary_keyword': cluster.primary_keyword,
                'trend_analysis': self._analyze_trend_strength(cluster),
                'audience_insights': self._generate_audience_insights(cluster),
                'content_recommendations': self._generate_content_recommendations(cluster),
                'monetization_opportunities': self._identify_monetization_opportunities(cluster),
                'risk_assessment': self._assess_risks(cluster),
                'timing_recommendations': self._recommend_timing(cluster)
            }
            analysis_results.append(analysis)
        
        return analysis_results
    
    def _analyze_trend_strength(self, cluster: TrendCluster) -> Dict[str, Any]:
        """Analyze the strength and sustainability of a trend."""
        return {
            'momentum_score': cluster.cluster_score,
            'sustainability': 'high' if cluster.cluster_score > 0.7 else 'medium',
            'growth_potential': 'high' if cluster.rpm_potential > 15 else 'medium',
            'seasonality': self._assess_seasonality(cluster.primary_keyword)
        }
    
    def _generate_audience_insights(self, cluster: TrendCluster) -> Dict[str, Any]:
        """Generate audience insights for trend cluster."""
        return {
            'target_demographics': self._identify_demographics(cluster),
            'engagement_patterns': self._predict_engagement_patterns(cluster),
            'platform_preferences': self._suggest_platforms(cluster)
        }
    
    def _generate_content_recommendations(self, cluster: TrendCluster) -> List[str]:
        """Generate specific content recommendations."""
        recommendations = []
        for opportunity in cluster.content_opportunities:
            recommendations.extend([
                f"{opportunity} - Tutorial format",
                f"{opportunity} - Story format",
                f"{opportunity} - Expert interview",
                f"{opportunity} - Comparison format"
            ])
        return recommendations[:8]
    
    def _identify_monetization_opportunities(self, cluster: TrendCluster) -> List[str]:
        """Identify monetization opportunities for trend cluster."""
        opportunities = []
        if cluster.rpm_potential > 10:
            opportunities.extend([
                "Affiliate marketing",
                "Sponsored content",
                "Product reviews",
                "Course creation",
                "Consulting services"
            ])
        return opportunities
    
    def _assess_risks(self, cluster: TrendCluster) -> Dict[str, Any]:
        """Assess risks associated with trend cluster."""
        return {
            'competition_level': 'high' if cluster.rpm_potential > 20 else 'medium',
            'trend_volatility': 'medium',
            'content_appropriateness': 'safe',
            'platform_policy_risks': 'low'
        }
    
    def _recommend_timing(self, cluster: TrendCluster) -> Dict[str, Any]:
        """Recommend optimal timing for content creation."""
        return {
            'optimal_posting_time': 'peak_hours',
            'content_creation_timeline': '1-2_weeks',
            'trend_lifespan': '2-4_weeks',
            'urgency_level': 'high' if cluster.cluster_score > 0.8 else 'medium'
        }
    
    def _assess_seasonality(self, keyword: str) -> str:
        """Assess seasonality of trend keyword."""
        seasonal_keywords = {
            'christmas': 'seasonal',
            'halloween': 'seasonal',
            'summer': 'seasonal',
            'winter': 'seasonal',
            'back_to_school': 'seasonal'
        }
        keyword_lower = keyword.lower()
        for seasonal, pattern in seasonal_keywords.items():
            if seasonal in keyword_lower:
                return pattern
        return 'year_round'
    
    def _identify_demographics(self, cluster: TrendCluster) -> Dict[str, Any]:
        """Identify target demographics for trend cluster."""
        return {
            'age_range': '18-34',
            'gender': 'all',
            'interests': [cluster.primary_keyword],
            'income_level': 'middle_income'
        }
    
    def _predict_engagement_patterns(self, cluster: TrendCluster) -> Dict[str, Any]:
        """Predict engagement patterns for trend cluster."""
        return {
            'expected_ctr': 0.03,
            'expected_avd': 0.65,
            'expected_comments': 'high',
            'expected_shares': 'medium'
        }
    
    def _suggest_platforms(self, cluster: TrendCluster) -> List[str]:
        """Suggest optimal platforms for trend cluster."""
        return ['tiktok', 'youtube', 'instagram']


class ViralFormatPredictorContentIdeation:
    """Predicts viral formats and generates content ideas."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.viral_formats = {
            'tutorial': {'engagement': 0.8, 'rpm': 0.9},
            'story': {'engagement': 0.9, 'rpm': 0.7},
            'challenge': {'engagement': 0.95, 'rpm': 0.6},
            'comparison': {'engagement': 0.7, 'rpm': 0.8},
            'transformation': {'engagement': 0.85, 'rpm': 0.75},
            'reaction': {'engagement': 0.8, 'rpm': 0.65},
            'behind_scenes': {'engagement': 0.75, 'rpm': 0.7},
            'expert_interview': {'engagement': 0.6, 'rpm': 0.9}
        }
    
    def predict_viral_formats(self, clusters: List[TrendCluster]) -> List[Dict[str, Any]]:
        """Predict viral formats for trend clusters."""
        predictions = []
        
        for cluster in clusters:
            cluster_predictions = {
                'cluster_id': cluster.cluster_id,
                'primary_keyword': cluster.primary_keyword,
                'predicted_formats': self._predict_formats_for_cluster(cluster),
                'content_ideas': self._generate_content_ideas(cluster)
            }
            predictions.append(cluster_predictions)
        
        return predictions
    
    def _predict_formats_for_cluster(self, cluster: TrendCluster) -> List[Dict[str, Any]]:
        """Predict viral formats for a specific cluster."""
        format_predictions = []
        
        for format_name, metrics in self.viral_formats.items():
            # Calculate format score based on cluster characteristics
            format_score = self._calculate_format_score(cluster, format_name, metrics)
            
            if format_score > 0.6:  # Only include high-scoring formats
                format_predictions.append({
                    'format': format_name,
                    'score': format_score,
                    'expected_engagement': metrics['engagement'],
                    'expected_rpm': metrics['rpm'] * cluster.rpm_potential,
                    'content_structure': self._suggest_content_structure(format_name, cluster)
                })
        
        # Sort by score descending
        format_predictions.sort(key=lambda x: x['score'], reverse=True)
        return format_predictions[:5]  # Return top 5 formats
    
    def _calculate_format_score(self, cluster: TrendCluster, format_name: str, metrics: Dict[str, float]) -> float:
        """Calculate score for a specific format based on cluster characteristics."""
        base_score = metrics['engagement'] * metrics['rpm']
        
        # Adjust based on cluster characteristics
        if cluster.cluster_score > 0.8:
            base_score *= 1.2  # High-trending topics get bonus
        if cluster.rpm_potential > 20:
            base_score *= 1.1  # High-RPM topics get bonus
        
        # Format-specific adjustments
        if format_name == 'tutorial' and 'how' in cluster.primary_keyword.lower():
            base_score *= 1.3
        elif format_name == 'story' and any(word in cluster.primary_keyword.lower() for word in ['experience', 'journey', 'story']):
            base_score *= 1.2
        
        return min(base_score, 1.0)  # Cap at 1.0
    
    def _suggest_content_structure(self, format_name: str, cluster: TrendCluster) -> Dict[str, Any]:
        """Suggest content structure for a specific format."""
        structures = {
            'tutorial': {
                'hook': f"Learn {cluster.primary_keyword} in 60 seconds",
                'intro': "Quick overview of what you'll learn",
                'steps': "3-5 key steps or tips",
                'outro': "Call to action and engagement prompt"
            },
            'story': {
                'hook': f"My {cluster.primary_keyword} journey",
                'intro': "Set the scene and context",
                'conflict': "The challenge or problem",
                'resolution': "How it was solved",
                'outro': "Key takeaways and lessons"
            },
            'challenge': {
                'hook': f"{cluster.primary_keyword} challenge",
                'intro': "Challenge explanation and rules",
                'execution': "Performing the challenge",
                'outro': "Tagging others and engagement"
            }
        }
        return structures.get(format_name, {'hook': f"Amazing {cluster.primary_keyword} content"})
    
    def _generate_content_ideas(self, cluster: TrendCluster) -> List[ContentIdea]:
        """Generate specific content ideas for trend cluster."""
        content_ideas = []
        
        for i, opportunity in enumerate(cluster.content_opportunities[:5]):
            idea = ContentIdea(
                idea_id=f"idea_{cluster.cluster_id}_{i}",
                title=opportunity,
                description=f"Create engaging content about {cluster.primary_keyword}",
                target_channels=self._suggest_target_channels(cluster),
                estimated_rpm=cluster.rpm_potential,
                content_format=self._suggest_content_format(cluster),
                hook_type=self._suggest_hook_type(cluster),
                hashtags=self._generate_hashtags(cluster),
                source_trends=[cluster.primary_keyword],
                priority_score=cluster.cluster_score
            )
            content_ideas.append(idea)
        
        return content_ideas
    
    def _suggest_target_channels(self, cluster: TrendCluster) -> List[str]:
        """Suggest target channels for content idea."""
        # Map cluster characteristics to appropriate channels
        if cluster.rpm_potential > 15:
            return ['WealthWise', 'TechPulse', 'Living Luxe']
        elif cluster.cluster_score > 0.8:
            return ['Viral Vortex', 'HypeHub']
        else:
            return ['GlamLab', 'Twinkle Tales & Tunes']
    
    def _suggest_content_format(self, cluster: TrendCluster) -> str:
        """Suggest content format for trend cluster."""
        if cluster.rpm_potential > 20:
            return 'educational_video'
        elif cluster.cluster_score > 0.8:
            return 'entertainment_video'
        else:
            return 'lifestyle_video'
    
    def _suggest_hook_type(self, cluster: TrendCluster) -> str:
        """Suggest hook type for trend cluster."""
        # Simple heuristic based on cluster characteristics
        if cluster.cluster_score > 0.8:
            return 'shock'
        elif 'how' in cluster.primary_keyword.lower():
            return 'tip'
        else:
            return 'story'
    
    def _generate_hashtags(self, cluster: TrendCluster) -> List[str]:
        """Generate relevant hashtags for trend cluster."""
        base_hashtags = [cluster.primary_keyword.replace(' ', '')]
        base_hashtags.extend([
            'trending',
            'viral',
            'fyp',
            'content',
            'tips'
        ])
        return base_hashtags[:8]  # Limit to 8 hashtags


class TrendRankingRecommendationOutput:
    """Ranks trends and provides final recommendations."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def rank_and_recommend(self, 
                          clusters: List[TrendCluster],
                          analysis_results: List[Dict[str, Any]],
                          format_predictions: List[Dict[str, Any]],
                          content_ideas: List[ContentIdea]) -> Dict[str, Any]:
        """Rank trends and provide final recommendations."""
        
        # Rank clusters by overall potential
        ranked_clusters = self._rank_clusters(clusters, analysis_results)
        
        # Generate final recommendations
        recommendations = {
            'timestamp': datetime.now().isoformat(),
            'top_trends': ranked_clusters[:10],
            'content_priorities': self._prioritize_content(content_ideas),
            'channel_recommendations': self._generate_channel_recommendations(ranked_clusters),
            'action_items': self._generate_action_items(ranked_clusters, content_ideas),
            'performance_metrics': self._calculate_performance_metrics(ranked_clusters)
        }
        
        return recommendations
    
    def _rank_clusters(self, clusters: List[TrendCluster], analysis_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank clusters by overall potential score."""
        ranked_data = []
        
        for cluster, analysis in zip(clusters, analysis_results):
            # Calculate overall score
            overall_score = (
                cluster.cluster_score * 0.3 +
                cluster.rpm_potential / 25.0 * 0.4 +
                analysis['trend_analysis']['momentum_score'] * 0.2 +
                (1.0 if analysis['trend_analysis']['sustainability'] == 'high' else 0.5) * 0.1
            )
            
            ranked_data.append({
                'cluster': cluster,
                'analysis': analysis,
                'overall_score': overall_score,
                'rank': 0  # Will be set after sorting
            })
        
        # Sort by overall score descending
        ranked_data.sort(key=lambda x: x['overall_score'], reverse=True)
        
        # Assign ranks
        for i, data in enumerate(ranked_data):
            data['rank'] = i + 1
        
        return ranked_data
    
    def _prioritize_content(self, content_ideas: List[ContentIdea]) -> List[Dict[str, Any]]:
        """Prioritize content ideas by potential impact."""
        prioritized = []
        
        for idea in content_ideas:
            priority_score = (
                idea.priority_score * 0.4 +
                idea.estimated_rpm / 25.0 * 0.4 +
                (0.8 if idea.hook_type == 'shock' else 0.6) * 0.2
            )
            
            prioritized.append({
                'idea': idea,
                'priority_score': priority_score,
                'estimated_impact': self._estimate_content_impact(idea)
            })
        
        # Sort by priority score descending
        prioritized.sort(key=lambda x: x['priority_score'], reverse=True)
        return prioritized[:20]  # Return top 20 content ideas
    
    def _estimate_content_impact(self, idea: ContentIdea) -> Dict[str, Any]:
        """Estimate the potential impact of a content idea."""
        return {
            'estimated_views': int(idea.estimated_rpm * 1000),
            'estimated_revenue': idea.estimated_rpm * 0.001,  # Rough estimate
            'engagement_potential': 'high' if idea.priority_score > 0.7 else 'medium',
            'viral_potential': 'high' if idea.hook_type == 'shock' else 'medium'
        }
    
    def _generate_channel_recommendations(self, ranked_clusters: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Generate channel-specific recommendations."""
        channel_recommendations = {
            'WealthWise': [],
            'TechPulse': [],
            'Living Luxe': [],
            'GlamLab': [],
            'Viral Vortex': [],
            'Twinkle Tales & Tunes': [],
            'HypeHub': []
        }
        
        for data in ranked_clusters[:15]:  # Top 15 trends
            cluster = data['cluster']
            data['analysis']
            
            # Assign to appropriate channels based on characteristics
            if cluster.rpm_potential > 15 and 'finance' in cluster.primary_keyword.lower():
                channel_recommendations['WealthWise'].append(cluster.primary_keyword)
            elif 'tech' in cluster.primary_keyword.lower():
                channel_recommendations['TechPulse'].append(cluster.primary_keyword)
            elif cluster.rpm_potential > 20:
                channel_recommendations['Living Luxe'].append(cluster.primary_keyword)
            elif cluster.cluster_score > 0.8:
                channel_recommendations['Viral Vortex'].append(cluster.primary_keyword)
            else:
                channel_recommendations['HypeHub'].append(cluster.primary_keyword)
        
        return channel_recommendations
    
    def _generate_action_items(self, ranked_clusters: List[Dict[str, Any]], content_ideas: List[ContentIdea]) -> List[Dict[str, Any]]:
        """Generate actionable items for immediate execution."""
        action_items = []
        
        # High-priority content creation
        top_ideas = sorted(content_ideas, key=lambda x: x.priority_score, reverse=True)[:5]
        for idea in top_ideas:
            action_items.append({
                'action': 'create_content',
                'priority': 'high',
                'description': f"Create content: {idea.title}",
                'target_channels': idea.target_channels,
                'estimated_effort': '2-4 hours',
                'deadline': (datetime.now() + timedelta(days=3)).isoformat()
            })
        
        # Trend monitoring
        top_trends = ranked_clusters[:5]
        for data in top_trends:
            action_items.append({
                'action': 'monitor_trend',
                'priority': 'medium',
                'description': f"Monitor trend: {data['cluster'].primary_keyword}",
                'frequency': 'daily',
                'metrics': ['interest_score', 'rpm_potential', 'competition_level']
            })
        
        return action_items
    
    def _calculate_performance_metrics(self, ranked_clusters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall performance metrics."""
        if not ranked_clusters:
            return {}
        
        avg_cluster_score = sum(data['cluster'].cluster_score for data in ranked_clusters) / len(ranked_clusters)
        avg_rpm_potential = sum(data['cluster'].rpm_potential for data in ranked_clusters) / len(ranked_clusters)
        high_potential_trends = sum(1 for data in ranked_clusters if data['cluster'].rpm_potential > 15)
        
        return {
            'average_cluster_score': avg_cluster_score,
            'average_rpm_potential': avg_rpm_potential,
            'high_potential_trends': high_potential_trends,
            'total_trends_analyzed': len(ranked_clusters),
            'trend_quality_score': avg_cluster_score * avg_rpm_potential / 25.0
        }


class UnifiedTrendIntelligence:
    """Main class that orchestrates the unified trend intelligence system."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.fetcher = TrendFetcherAggregator(config)
        self.clusterer = TrendFilterSemanticClusterer(config)
        self.analyzer = TrendAnalyzerEnrichment(config)
        self.predictor = ViralFormatPredictorContentIdeation(config)
        self.ranker = TrendRankingRecommendationOutput(config)
    
    async def run_full_analysis(self, seed_keywords: List[str]) -> Dict[str, Any]:
        """Run complete trend intelligence analysis."""
        log.info("Starting unified trend intelligence analysis")
        
        try:
            # Step 1: Fetch and aggregate trends
            log.info("Fetching trends from all sources")
            trends = await self.fetcher.fetch_all_trends(seed_keywords)
            
            # Step 2: Filter and cluster trends
            log.info("Filtering and clustering trends")
            clusters = self.clusterer.filter_and_cluster(trends)
            
            # Step 3: Analyze and enrich trends
            log.info("Analyzing and enriching trends")
            analysis_results = self.analyzer.analyze_trends(clusters)
            
            # Step 4: Predict viral formats and generate content ideas
            log.info("Predicting viral formats and generating content ideas")
            format_predictions = self.predictor.predict_viral_formats(clusters)
            
            # Extract content ideas from format predictions
            all_content_ideas = []
            for prediction in format_predictions:
                all_content_ideas.extend(prediction['content_ideas'])
            
            # Step 5: Rank and provide final recommendations
            log.info("Ranking trends and generating final recommendations")
            recommendations = self.ranker.rank_and_recommend(
                clusters, analysis_results, format_predictions, all_content_ideas
            )
            
            # Add metadata
            recommendations['metadata'] = {
                'analysis_timestamp': datetime.now().isoformat(),
                'trends_analyzed': len(trends),
                'clusters_created': len(clusters),
                'content_ideas_generated': len(all_content_ideas),
                'system_version': 'v7.0'
            }
            
            log.info("Unified trend intelligence analysis completed successfully")
            return recommendations
            
        except Exception as e:
            log.error(f"Error in unified trend intelligence analysis: {e}")
            raise
    
    async def get_trend_summary(self, seed_keywords: List[str]) -> Dict[str, Any]:
        """Get a summary of current trends without full analysis."""
        try:
            trends = await self.fetcher.fetch_all_trends(seed_keywords)
            clusters = self.clusterer.filter_and_cluster(trends)
            
            return {
                'summary_timestamp': datetime.now().isoformat(),
                'total_trends': len(trends),
                'active_clusters': len(clusters),
                'top_keywords': [c.primary_keyword for c in clusters[:5]],
                'average_rpm_potential': sum(c.rpm_potential for c in clusters) / len(clusters) if clusters else 0
            }
        except Exception as e:
            log.error(f"Error getting trend summary: {e}")
            return {'error': str(e)}
    
    def save_analysis_results(self, results: Dict[str, Any], filepath: str) -> None:
        """Save analysis results to file."""
        try:
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            log.info(f"Analysis results saved to {filepath}")
        except Exception as e:
            log.error(f"Error saving analysis results: {e}")
            raise

