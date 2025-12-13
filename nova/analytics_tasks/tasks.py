"""
Celery tasks for Nova Agent analytics processing and aggregation.

This module handles scheduled analytics processing, reporting, and analysis tasks.
Note: Renamed from metrics.tasks to avoid conflict with nova/metrics.py
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from nova.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(
    name="nova.analytics.process_daily_metrics_task",
    bind=True,
    autoretry_for=(Exception,),
    max_retries=2,
    retry_backoff=True
)
def process_daily_metrics_task(self) -> Dict[str, Any]:
    """
    Daily analytics processing task.
    
    Processes and aggregates metrics from the previous day,
    updates leaderboards, and generates reports.
    
    Returns:
        Dict containing processing results
    """
    task_id = self.request.id
    logger.info(f"Starting daily analytics processing task {task_id}")
    
    try:
        # Calculate date range for processing
        end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=1)
        
        # Import analytics modules
        from nova.analytics import aggregate_metrics, top_prompts, rpm_by_audience
        from nova.rpm_leaderboard import PromptLeaderboard
        
        # Process analytics
        results = {}
        
        # Aggregate daily metrics
        try:
            aggregated = aggregate_metrics(start_date, end_date)
            results['aggregated_metrics'] = aggregated
            logger.info(f"Aggregated metrics for {start_date.date()}")
        except Exception as e:
            logger.error(f"Failed to aggregate metrics: {e}")
            results['aggregated_metrics'] = {'error': str(e)}
        
        # Update prompt leaderboard
        try:
            leaderboard = PromptLeaderboard()
            top_performers = top_prompts(limit=50, start_date=start_date, end_date=end_date)
            
            # Process leaderboard updates
            leaderboard_results = []
            for prompt_data in top_performers:
                try:
                    leaderboard.update_prompt_performance(
                        prompt_id=prompt_data.get('id'),
                        metrics=prompt_data.get('metrics', {})
                    )
                    leaderboard_results.append({
                        'prompt_id': prompt_data.get('id'),
                        'status': 'updated'
                    })
                except Exception as e:
                    leaderboard_results.append({
                        'prompt_id': prompt_data.get('id'),
                        'status': 'failed',
                        'error': str(e)
                    })
            
            results['leaderboard_updates'] = leaderboard_results
            logger.info(f"Updated leaderboard with {len(top_performers)} prompts")
            
        except Exception as e:
            logger.error(f"Failed to update leaderboard: {e}")
            results['leaderboard_updates'] = {'error': str(e)}
        
        # Generate RPM analysis by audience
        try:
            rpm_analysis = rpm_by_audience(start_date=start_date, end_date=end_date)
            results['rpm_analysis'] = rpm_analysis
            logger.info("Generated RPM analysis by audience")
        except Exception as e:
            logger.error(f"Failed to generate RPM analysis: {e}")
            results['rpm_analysis'] = {'error': str(e)}
        
        # Calculate overall success rate
        successful_operations = sum(
            1 for result in results.values() 
            if isinstance(result, (dict, list)) and 'error' not in result
        )
        total_operations = len(results)
        
        return {
            'task_id': task_id,
            'status': 'completed',
            'date_processed': start_date.date().isoformat(),
            'successful_operations': successful_operations,
            'total_operations': total_operations,
            'results': results
        }
        
    except Exception as exc:
        logger.error(f"Daily analytics processing task {task_id} failed: {exc}", exc_info=True)
        raise


@celery_app.task(
    name="nova.analytics.generate_weekly_report_task",
    bind=True
)
def generate_weekly_report_task(self) -> Dict[str, Any]:
    """
    Generate comprehensive weekly analytics report.
    
    Creates a detailed report covering the past week's performance,
    trends, and insights.
    
    Returns:
        Dict containing report data and metadata
    """
    task_id = self.request.id
    logger.info(f"Starting weekly report generation task {task_id}")
    
    try:
        # Calculate week range
        end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=7)
        
        # Import required modules
        
        # Generate report sections
        report = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'duration_days': 7
            },
            'overview': _generate_metrics_overview(start_date, end_date),
            'top_performers': _generate_top_performers_report(start_date, end_date),
            'trend_analysis': _generate_trend_analysis(start_date, end_date),
            'recommendations': _generate_recommendations(start_date, end_date)
        }
        
        # Save report to file
        report_filename = f"weekly_report_{start_date.date()}_to_{end_date.date()}.json"
        _save_report(report, report_filename)
        
        logger.info(f"Weekly report generated and saved as {report_filename}")
        
        return {
            'task_id': task_id,
            'status': 'completed',
            'report_filename': report_filename,
            'report_size_kb': len(str(report)) // 1024,
            'period': report['period']
        }
        
    except Exception as exc:
        logger.error(f"Weekly report generation task {task_id} failed: {exc}", exc_info=True)
        raise


def _generate_metrics_overview(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Generate high-level metrics overview."""
    try:
        from nova.analytics import aggregate_metrics
        
        metrics = aggregate_metrics(start_date, end_date)
        
        return {
            'total_requests': metrics.get('total_requests', 0),
            'average_rpm': metrics.get('average_rpm', 0),
            'total_revenue': metrics.get('total_revenue', 0),
            'unique_users': metrics.get('unique_users', 0),
            'error_rate': metrics.get('error_rate', 0)
        }
    except Exception as e:
        logger.error(f"Failed to generate metrics overview: {e}")
        return {'error': str(e)}


def _generate_top_performers_report(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Generate top performers analysis."""
    try:
        from nova.analytics import top_prompts
        
        top_performers = top_prompts(limit=20, start_date=start_date, end_date=end_date)
        
        return {
            'top_prompts': top_performers[:10],
            'rising_stars': top_performers[10:20] if len(top_performers) > 10 else [],
            'total_analyzed': len(top_performers)
        }
    except Exception as e:
        logger.error(f"Failed to generate top performers report: {e}")
        return {'error': str(e)}


def _generate_trend_analysis(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Generate trend analysis for the reporting period."""
    try:
        # This would analyze trends over the week
        # For now, return placeholder data
        return {
            'growth_trends': {
                'rpm_growth': 5.2,  # percentage
                'user_growth': 12.1,
                'revenue_growth': 8.7
            },
            'seasonal_patterns': {
                'peak_hours': [14, 15, 16, 20, 21],
                'peak_days': ['Tuesday', 'Wednesday', 'Thursday']
            },
            'content_trends': {
                'popular_categories': ['Finance', 'Technology', 'Health'],
                'emerging_topics': ['AI Tools', 'Crypto DeFi', 'Remote Work']
            }
        }
    except Exception as e:
        logger.error(f"Failed to generate trend analysis: {e}")
        return {'error': str(e)}


def _generate_recommendations(start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
    """Generate actionable recommendations based on metrics."""
    try:
        # This would analyze performance and generate recommendations
        # For now, return placeholder recommendations
        return [
            {
                'type': 'optimization',
                'priority': 'high',
                'title': 'Increase content in top-performing categories',
                'description': 'Finance and Technology content shows 25% higher engagement',
                'action': 'Schedule more finance/tech content during peak hours'
            },
            {
                'type': 'growth',
                'priority': 'medium', 
                'title': 'Expand into emerging topics',
                'description': 'AI Tools content showing rapid growth trend',
                'action': 'Create content series on AI productivity tools'
            },
            {
                'type': 'efficiency',
                'priority': 'low',
                'title': 'Optimize posting schedule',
                'description': 'Content posted 2-4 PM shows best performance',
                'action': 'Reschedule low-performing posts to peak hours'
            }
        ]
    except Exception as e:
        logger.error(f"Failed to generate recommendations: {e}")
        return [{'error': str(e)}]


def _save_report(report: Dict[str, Any], filename: str) -> None:
    """Save report to file."""
    import json
    import os
    
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    
    filepath = os.path.join(reports_dir, filename)
    with open(filepath, 'w') as f:
        json.dump(report, f, indent=2, default=str)
