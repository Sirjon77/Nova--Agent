"""
Celery tasks for Nova Agent trend intelligence and analysis.

This module handles scheduled trend scanning, analysis, and content opportunity identification.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from nova.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(
    name="nova.trends.daily_trend_scan_task",
    bind=True,
    autoretry_for=(Exception,),
    max_retries=2,
    retry_backoff=True
)
def daily_trend_scan_task(self) -> Dict[str, Any]:
    """
    Daily trend intelligence scanning task.
    
    Scans for trending topics, keywords, and content opportunities
    across various platforms and data sources.
    
    Returns:
        Dict containing trend scan results and insights
    """
    task_id = self.request.id
    logger.info(f"Starting daily trend scan task {task_id}")
    
    try:
        # Import trend intelligence module
        from nova.trend_intelligence import TrendIntelligence
        
        # Initialize trend scanner
        trend_scanner = TrendIntelligence()
        
        # Run trend scanning in async context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Scan multiple sources
            scan_results = loop.run_until_complete(_run_comprehensive_scan(trend_scanner))
            
            # Process and analyze results
            analysis = _analyze_trend_data(scan_results)
            
            # Identify content opportunities
            opportunities = _identify_content_opportunities(analysis)
            
            # Save results
            _save_trend_results(scan_results, analysis, opportunities)
            
            logger.info(f"Daily trend scan completed: {len(opportunities)} opportunities identified")
            
            return {
                'task_id': task_id,
                'status': 'completed',
                'scan_date': datetime.utcnow().date().isoformat(),
                'sources_scanned': len(scan_results),
                'trends_identified': len(analysis.get('trending_topics', [])),
                'opportunities_found': len(opportunities),
                'top_opportunities': opportunities[:5]  # Top 5 for quick review
            }
            
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Daily trend scan task {task_id} failed: {exc}", exc_info=True)
        raise


@celery_app.task(
    name="nova.trends.competitor_analysis_task",
    bind=True
)
def competitor_analysis_task(self, competitor_seeds: Optional[List[str]] = None, limit: int = 10) -> Dict[str, Any]:
    """
    Analyze competitor content and performance.
    
    Args:
        competitor_seeds: List of competitor identifiers/URLs
        limit: Maximum number of competitors to analyze
        
    Returns:
        Dict containing competitor analysis results
    """
    task_id = self.request.id
    logger.info(f"Starting competitor analysis task {task_id}")
    
    try:
        import os
        
        # Use provided seeds or get from environment
        if not competitor_seeds:
            seeds_env = os.getenv('COMPETITOR_SEEDS', '')
            competitor_seeds = [s.strip() for s in seeds_env.split(',') if s.strip()]
        
        if not competitor_seeds:
            logger.warning("No competitor seeds provided, using default list")
            competitor_seeds = _get_default_competitor_seeds()
        
        # Limit the number of competitors to analyze
        competitor_seeds = competitor_seeds[:limit]
        
        # Import analysis module
        from nova.competitor_analyzer import CompetitorAnalyzer
        
        analyzer = CompetitorAnalyzer()
        
        # Analyze each competitor
        analysis_results = []
        for seed in competitor_seeds:
            try:
                result = analyzer.analyze_competitor(seed)
                if result:
                    analysis_results.append(result)
                    logger.debug(f"Analyzed competitor: {seed}")
            except Exception as e:
                logger.warning(f"Failed to analyze competitor {seed}: {e}")
                analysis_results.append({
                    'seed': seed,
                    'error': str(e),
                    'status': 'failed'
                })
        
        # Generate insights from analysis
        insights = _generate_competitor_insights(analysis_results)
        
        # Save analysis results
        _save_competitor_analysis(analysis_results, insights)
        
        logger.info(f"Competitor analysis completed: {len(analysis_results)} competitors analyzed")
        
        return {
            'task_id': task_id,
            'status': 'completed',
            'competitors_analyzed': len([r for r in analysis_results if 'error' not in r]),
            'competitors_failed': len([r for r in analysis_results if 'error' in r]),
            'total_competitors': len(analysis_results),
            'insights': insights,
            'analysis_date': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Competitor analysis task {task_id} failed: {exc}", exc_info=True)
        raise


async def _run_comprehensive_scan(trend_scanner) -> Dict[str, Any]:
    """Run comprehensive trend scanning across multiple sources."""
    scan_results = {}
    
    try:
        # Scan Google Trends
        google_trends = await trend_scanner.scan_google_trends()
        scan_results['google_trends'] = google_trends
    except Exception as e:
        logger.warning(f"Google Trends scan failed: {e}")
        scan_results['google_trends'] = {'error': str(e)}
    
    try:
        # Scan social media trends (Twitter, TikTok, etc.)
        social_trends = await trend_scanner.scan_social_media_trends()
        scan_results['social_trends'] = social_trends
    except Exception as e:
        logger.warning(f"Social media trends scan failed: {e}")
        scan_results['social_trends'] = {'error': str(e)}
    
    try:
        # Scan news and content trends
        news_trends = await trend_scanner.scan_news_trends()
        scan_results['news_trends'] = news_trends
    except Exception as e:
        logger.warning(f"News trends scan failed: {e}")
        scan_results['news_trends'] = {'error': str(e)}
    
    try:
        # Scan YouTube trends
        youtube_trends = await trend_scanner.scan_youtube_trends()
        scan_results['youtube_trends'] = youtube_trends
    except Exception as e:
        logger.warning(f"YouTube trends scan failed: {e}")
        scan_results['youtube_trends'] = {'error': str(e)}
    
    return scan_results


def _analyze_trend_data(scan_results: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze trend data and extract insights."""
    try:
        analysis = {
            'trending_topics': [],
            'emerging_keywords': [],
            'content_gaps': [],
            'audience_interests': [],
            'seasonal_patterns': []
        }
        
        # Process each data source
        for source, data in scan_results.items():
            if 'error' in data:
                continue
                
            # Extract trending topics
            if 'topics' in data:
                analysis['trending_topics'].extend(data['topics'])
            
            # Extract keywords
            if 'keywords' in data:
                analysis['emerging_keywords'].extend(data['keywords'])
            
            # Extract audience data
            if 'audience' in data:
                analysis['audience_interests'].extend(data['audience'])
        
        # Remove duplicates and rank by relevance
        analysis['trending_topics'] = _deduplicate_and_rank(analysis['trending_topics'])
        analysis['emerging_keywords'] = _deduplicate_and_rank(analysis['emerging_keywords'])
        
        return analysis
        
    except Exception as e:
        logger.error(f"Failed to analyze trend data: {e}")
        return {'error': str(e)}


def _identify_content_opportunities(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify content creation opportunities from trend analysis."""
    opportunities = []
    
    try:
        trending_topics = analysis.get('trending_topics', [])
        
        for topic in trending_topics[:20]:  # Top 20 topics
            opportunity = {
                'topic': topic.get('name', ''),
                'trend_score': topic.get('score', 0),
                'content_type': _suggest_content_type(topic),
                'urgency': _calculate_urgency(topic),
                'estimated_reach': _estimate_reach(topic),
                'competition_level': _assess_competition(topic),
                'suggested_angles': _suggest_content_angles(topic)
            }
            opportunities.append(opportunity)
        
        # Sort by combined score (trend_score + urgency - competition)
        opportunities.sort(
            key=lambda x: x['trend_score'] + x['urgency'] - x['competition_level'],
            reverse=True
        )
        
        return opportunities
        
    except Exception as e:
        logger.error(f"Failed to identify content opportunities: {e}")
        return []


def _get_default_competitor_seeds() -> List[str]:
    """Get default competitor list for analysis."""
    return [
        'example_competitor_1',
        'example_competitor_2',
        'example_competitor_3'
    ]


def _generate_competitor_insights(analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate insights from competitor analysis."""
    try:
        insights = {
            'content_gaps': [],
            'successful_strategies': [],
            'market_opportunities': [],
            'competitive_advantages': []
        }
        
        successful_competitors = [r for r in analysis_results if 'error' not in r]
        
        if successful_competitors:
            # Analyze common successful strategies
            strategies = []
            for competitor in successful_competitors:
                if 'strategies' in competitor:
                    strategies.extend(competitor['strategies'])
            
            insights['successful_strategies'] = _find_common_patterns(strategies)
            
            # Identify content gaps
            content_types = []
            for competitor in successful_competitors:
                if 'content_types' in competitor:
                    content_types.extend(competitor['content_types'])
            
            insights['content_gaps'] = _identify_gaps(content_types)
        
        return insights
        
    except Exception as e:
        logger.error(f"Failed to generate competitor insights: {e}")
        return {'error': str(e)}


def _deduplicate_and_rank(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicates and rank items by relevance."""
    # Simple deduplication by name/topic
    seen = set()
    unique_items = []
    
    for item in items:
        identifier = item.get('name', '') or item.get('topic', '')
        if identifier and identifier not in seen:
            seen.add(identifier)
            unique_items.append(item)
    
    # Sort by score if available
    return sorted(unique_items, key=lambda x: x.get('score', 0), reverse=True)


def _suggest_content_type(topic: Dict[str, Any]) -> str:
    """Suggest content type based on topic characteristics."""
    # Simple logic - could be enhanced with ML
    keywords = topic.get('keywords', [])
    
    if any(keyword in ['tutorial', 'how-to', 'guide'] for keyword in keywords):
        return 'tutorial'
    elif any(keyword in ['news', 'breaking', 'update'] for keyword in keywords):
        return 'news'
    elif any(keyword in ['review', 'comparison', 'vs'] for keyword in keywords):
        return 'review'
    else:
        return 'general'


def _calculate_urgency(topic: Dict[str, Any]) -> int:
    """Calculate urgency score for content creation."""
    # Simple urgency calculation
    trend_velocity = topic.get('velocity', 0)
    recency = topic.get('recency_hours', 24)
    
    # Higher urgency for fast-moving, recent trends
    urgency = min(100, trend_velocity * 10 + (48 - min(48, recency)))
    return max(0, urgency)


def _estimate_reach(topic: Dict[str, Any]) -> int:
    """Estimate potential reach for content on this topic."""
    # Simple reach estimation
    search_volume = topic.get('search_volume', 1000)
    social_mentions = topic.get('social_mentions', 100)
    
    estimated_reach = (search_volume * 0.1) + (social_mentions * 0.5)
    return int(estimated_reach)


def _assess_competition(topic: Dict[str, Any]) -> int:
    """Assess competition level for the topic."""
    # Simple competition assessment
    competitor_count = topic.get('competitor_count', 10)
    content_saturation = topic.get('content_saturation', 0.5)
    
    competition_score = (competitor_count * 2) + (content_saturation * 50)
    return min(100, int(competition_score))


def _suggest_content_angles(topic: Dict[str, Any]) -> List[str]:
    """Suggest content angles for the topic."""
    # Basic angle suggestions
    angles = [
        f"Beginner's guide to {topic.get('name', '')}",
        f"Latest trends in {topic.get('name', '')}",
        f"Expert tips for {topic.get('name', '')}",
    ]
    
    # Add specific angles based on topic characteristics
    if topic.get('controversy_score', 0) > 0.5:
        angles.append(f"The truth about {topic.get('name', '')}")
    
    if topic.get('technical_complexity', 0) > 0.7:
        angles.append(f"Simplified explanation of {topic.get('name', '')}")
    
    return angles


def _find_common_patterns(strategies: List[str]) -> List[str]:
    """Find common patterns in successful strategies."""
    # Simple pattern detection
    from collections import Counter
    
    strategy_counts = Counter(strategies)
    common_strategies = [strategy for strategy, count in strategy_counts.most_common(5)]
    
    return common_strategies


def _identify_gaps(content_types: List[str]) -> List[str]:
    """Identify content gaps in the market."""
    # Simple gap identification
    all_types = ['tutorial', 'review', 'news', 'opinion', 'case-study', 'comparison']
    covered_types = set(content_types)
    
    gaps = [content_type for content_type in all_types if content_type not in covered_types]
    return gaps


def _save_trend_results(scan_results: Dict[str, Any], analysis: Dict[str, Any], opportunities: List[Dict[str, Any]]) -> None:
    """Save trend analysis results to file."""
    import json
    import os
    
    results_dir = "trend_results"
    os.makedirs(results_dir, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"trend_analysis_{timestamp}.json"
    
    data = {
        'timestamp': datetime.utcnow().isoformat(),
        'scan_results': scan_results,
        'analysis': analysis,
        'opportunities': opportunities
    }
    
    filepath = os.path.join(results_dir, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def _save_competitor_analysis(analysis_results: List[Dict[str, Any]], insights: Dict[str, Any]) -> None:
    """Save competitor analysis results to file."""
    import json
    import os
    
    results_dir = "competitor_analysis"
    os.makedirs(results_dir, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"competitor_analysis_{timestamp}.json"
    
    data = {
        'timestamp': datetime.utcnow().isoformat(),
        'analysis_results': analysis_results,
        'insights': insights
    }
    
    filepath = os.path.join(results_dir, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)
