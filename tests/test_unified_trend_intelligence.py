"""
Test suite for Unified Trend Intelligence Subsystem.

Tests the consolidation of trend scanning functionality and advanced features.
"""

import pytest
from unittest.mock import patch
from datetime import datetime

from nova.trend_intelligence import (
    UnifiedTrendIntelligence,
    TrendData,
    TrendCluster,
    ContentIdea,
    TrendSource
)


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        'trends': {
            'rpm_multiplier': 0.8,
            'top_n': 25,
            'use_tiktok': False,
            'use_vidiq': False,
            'use_gwi': False
        },
        'min_interest_threshold': 0.3,
        'min_rpm_threshold': 5.0
    }


@pytest.fixture
def sample_trends():
    """Sample trend data for testing."""
    return [
        TrendData(
            keyword="ai tools",
            interest_score=0.8,
            projected_rpm=15.0,
            source=TrendSource.GOOGLE_TRENDS,
            timestamp=datetime.now(),
            category="tech"
        ),
        TrendData(
            keyword="cryptocurrency",
            interest_score=0.7,
            projected_rpm=18.0,
            source=TrendSource.GOOGLE_TRENDS,
            timestamp=datetime.now(),
            category="finance"
        ),
        TrendData(
            keyword="sustainable fashion",
            interest_score=0.6,
            projected_rpm=12.0,
            source=TrendSource.GOOGLE_TRENDS,
            timestamp=datetime.now(),
            category="lifestyle"
        )
    ]


@pytest.fixture
def sample_clusters():
    """Sample trend clusters for testing."""
    return [
        TrendCluster(
            cluster_id="cluster_tech_0",
            primary_keyword="ai tools",
            related_keywords=["ai tools", "machine learning"],
            cluster_score=0.8,
            rpm_potential=15.0,
            content_opportunities=["Top 10 ai tools tips"],
            viral_format_suggestions=["Tutorial/How-to"],
            created_at=datetime.now()
        ),
        TrendCluster(
            cluster_id="cluster_finance_0",
            primary_keyword="cryptocurrency",
            related_keywords=["cryptocurrency", "bitcoin"],
            cluster_score=0.7,
            rpm_potential=18.0,
            content_opportunities=["How to cryptocurrency in 2024"],
            viral_format_suggestions=["Expert interview"],
            created_at=datetime.now()
        )
    ]


class TestUnifiedTrendIntelligence:
    """Test the main UnifiedTrendIntelligence class."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, sample_config):
        """Test that the system initializes correctly."""
        system = UnifiedTrendIntelligence(sample_config)
        
        assert system.fetcher is not None
        assert system.clusterer is not None
        assert system.analyzer is not None
        assert system.predictor is not None
        assert system.ranker is not None
    
    @pytest.mark.asyncio
    async def test_trend_summary(self, sample_config):
        """Test trend summary functionality."""
        system = UnifiedTrendIntelligence(sample_config)
        
        # Mock the fetcher to return sample data
        with patch.object(system.fetcher, 'fetch_all_trends') as mock_fetch:
            mock_fetch.return_value = [
                TrendData(
                    keyword="test trend",
                    interest_score=0.5,
                    projected_rpm=10.0,
                    source=TrendSource.GOOGLE_TRENDS,
                    timestamp=datetime.now(),
                    category="general"
                )
            ]
            
            summary = await system.get_trend_summary(["test"])
            
            assert 'summary_timestamp' in summary
            assert summary['total_trends'] == 1
            assert summary['active_clusters'] >= 0
    
    @pytest.mark.asyncio
    async def test_full_analysis_integration(self, sample_config):
        """Test the full analysis pipeline."""
        system = UnifiedTrendIntelligence(sample_config)
        
        # Mock all components to return expected data
        with patch.object(system.fetcher, 'fetch_all_trends') as mock_fetch, \
             patch.object(system.clusterer, 'filter_and_cluster') as mock_cluster, \
             patch.object(system.analyzer, 'analyze_trends') as mock_analyze, \
             patch.object(system.predictor, 'predict_viral_formats') as mock_predict, \
             patch.object(system.ranker, 'rank_and_recommend') as mock_rank:
            
            # Setup mock returns
            mock_fetch.return_value = [
                TrendData(
                    keyword="test trend",
                    interest_score=0.5,
                    projected_rpm=10.0,
                    source=TrendSource.GOOGLE_TRENDS,
                    timestamp=datetime.now(),
                    category="general"
                )
            ]
            
            mock_cluster.return_value = [
                TrendCluster(
                    cluster_id="test_cluster",
                    primary_keyword="test trend",
                    related_keywords=["test trend"],
                    cluster_score=0.5,
                    rpm_potential=10.0,
                    content_opportunities=["Test content"],
                    viral_format_suggestions=["Tutorial"],
                    created_at=datetime.now()
                )
            ]
            
            mock_analyze.return_value = [{'cluster_id': 'test_cluster'}]
            mock_predict.return_value = [{'cluster_id': 'test_cluster', 'content_ideas': []}]
            mock_rank.return_value = {'timestamp': '2024-01-01', 'top_trends': []}
            
            # Run full analysis
            results = await system.run_full_analysis(["test"])
            
            # Verify results structure
            assert 'timestamp' in results
            assert 'metadata' in results
            assert results['metadata']['system_version'] == 'v7.0'
    
    def test_save_analysis_results(self, sample_config, tmp_path):
        """Test saving analysis results to file."""
        system = UnifiedTrendIntelligence(sample_config)
        
        test_results = {
            'timestamp': '2024-01-01',
            'top_trends': [],
            'metadata': {'system_version': 'v7.0'}
        }
        
        filepath = tmp_path / "test_results.json"
        system.save_analysis_results(test_results, str(filepath))
        
        assert filepath.exists()
        
        # Verify file contents
        import json
        with open(filepath, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data['timestamp'] == '2024-01-01'
        assert saved_data['metadata']['system_version'] == 'v7.0'


class TestTrendFilterSemanticClusterer:
    """Test the trend filtering and clustering functionality."""
    
    def test_filter_trends(self, sample_config, sample_trends):
        """Test trend filtering based on thresholds."""
        from nova.trend_intelligence import TrendFilterSemanticClusterer
        
        clusterer = TrendFilterSemanticClusterer(sample_config)
        filtered_trends = clusterer._filter_trends(sample_trends)
        
        # All trends should pass the filter (interest_score >= 0.3, projected_rpm >= 5.0)
        assert len(filtered_trends) == 3
        
        # Test with low-scoring trend
        low_trend = TrendData(
            keyword="low trend",
            interest_score=0.2,  # Below threshold
            projected_rpm=3.0,   # Below threshold
            source=TrendSource.GOOGLE_TRENDS,
            timestamp=datetime.now(),
            category="general"
        )
        
        test_trends = sample_trends + [low_trend]
        filtered = clusterer._filter_trends(test_trends)
        
        # Low-scoring trend should be filtered out
        assert len(filtered) == 3
        assert low_trend not in filtered
    
    def test_create_semantic_clusters(self, sample_config, sample_trends):
        """Test semantic clustering functionality."""
        from nova.trend_intelligence import TrendFilterSemanticClusterer
        
        clusterer = TrendFilterSemanticClusterer(sample_config)
        clusters = clusterer._create_semantic_clusters(sample_trends)
        
        # Should create clusters for each category
        assert len(clusters) >= 2  # At least tech and finance categories
        
        # Verify cluster structure
        for cluster in clusters:
            assert hasattr(cluster, 'cluster_id')
            assert hasattr(cluster, 'primary_keyword')
            assert hasattr(cluster, 'related_keywords')
            assert hasattr(cluster, 'cluster_score')
            assert hasattr(cluster, 'rpm_potential')
            assert hasattr(cluster, 'content_opportunities')
            assert hasattr(cluster, 'viral_format_suggestions')


class TestViralFormatPredictorContentIdeation:
    """Test viral format prediction and content ideation."""
    
    def test_predict_viral_formats(self, sample_config, sample_clusters):
        """Test viral format prediction."""
        from nova.trend_intelligence import ViralFormatPredictorContentIdeation
        
        predictor = ViralFormatPredictorContentIdeation(sample_config)
        predictions = predictor.predict_viral_formats(sample_clusters)
        
        assert len(predictions) == len(sample_clusters)
        
        for prediction in predictions:
            assert 'cluster_id' in prediction
            assert 'primary_keyword' in prediction
            assert 'predicted_formats' in prediction
            assert 'content_ideas' in prediction
            
            # Should have predicted formats
            assert len(prediction['predicted_formats']) > 0
            
            # Should have content ideas
            assert len(prediction['content_ideas']) > 0
    
    def test_generate_content_ideas(self, sample_config, sample_clusters):
        """Test content idea generation."""
        from nova.trend_intelligence import ViralFormatPredictorContentIdeation
        
        predictor = ViralFormatPredictorContentIdeation(sample_config)
        
        for cluster in sample_clusters:
            ideas = predictor._generate_content_ideas(cluster)
            
            assert len(ideas) > 0
            
            for idea in ideas:
                assert isinstance(idea, ContentIdea)
                assert idea.idea_id.startswith(f"idea_{cluster.cluster_id}")
                assert idea.title in cluster.content_opportunities
                assert len(idea.target_channels) > 0
                assert idea.estimated_rpm == cluster.rpm_potential
                assert idea.priority_score == cluster.cluster_score


class TestTrendRankingRecommendationOutput:
    """Test trend ranking and recommendation output."""
    
    def test_rank_clusters(self, sample_config, sample_clusters):
        """Test cluster ranking functionality."""
        from nova.trend_intelligence import TrendRankingRecommendationOutput
        
        ranker = TrendRankingRecommendationOutput(sample_config)
        
        # Mock analysis results
        analysis_results = [
            {
                'cluster_id': cluster.cluster_id,
                'trend_analysis': {
                    'momentum_score': cluster.cluster_score,
                    'sustainability': 'high' if cluster.cluster_score > 0.7 else 'medium'
                }
            }
            for cluster in sample_clusters
        ]
        
        ranked = ranker._rank_clusters(sample_clusters, analysis_results)
        
        assert len(ranked) == len(sample_clusters)
        
        # Should be sorted by overall score descending
        for i in range(len(ranked) - 1):
            assert ranked[i]['overall_score'] >= ranked[i + 1]['overall_score']
        
        # Should have ranks assigned
        for i, data in enumerate(ranked):
            assert data['rank'] == i + 1
    
    def test_prioritize_content(self, sample_config):
        """Test content prioritization."""
        from nova.trend_intelligence import TrendRankingRecommendationOutput
        
        ranker = TrendRankingRecommendationOutput(sample_config)
        
        content_ideas = [
            ContentIdea(
                idea_id="test_idea_1",
                title="High priority idea",
                description="Test description",
                target_channels=["WealthWise"],
                estimated_rpm=20.0,
                content_format="educational_video",
                hook_type="shock",
                hashtags=["test"],
                source_trends=["test"],
                priority_score=0.9
            ),
            ContentIdea(
                idea_id="test_idea_2",
                title="Low priority idea",
                description="Test description",
                target_channels=["HypeHub"],
                estimated_rpm=5.0,
                content_format="lifestyle_video",
                hook_type="story",
                hashtags=["test"],
                source_trends=["test"],
                priority_score=0.3
            )
        ]
        
        prioritized = ranker._prioritize_content(content_ideas)
        
        assert len(prioritized) == len(content_ideas)
        
        # Should be sorted by priority score descending
        for i in range(len(prioritized) - 1):
            assert prioritized[i]['priority_score'] >= prioritized[i + 1]['priority_score']


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

