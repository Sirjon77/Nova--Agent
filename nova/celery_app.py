"""
Celery application configuration for Nova Agent v7.0

This module sets up Celery with Redis broker for handling scheduled background tasks,
replacing the manual asyncio loops with a robust, scalable scheduler.
"""

import os
from celery import Celery
from celery.schedules import crontab

# Initialize Celery application
celery_app = Celery('nova_agent')

# Broker configuration - use Redis
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
celery_app.conf.update(
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    timezone='UTC',
    enable_utc=True,
    task_acks_late=True,
    worker_max_tasks_per_child=100,
    task_default_retry_delay=60,  # seconds
    task_max_retries=3,
    broker_connection_retry_on_startup=True,
    # Task routing - all tasks go to 'celery' queue by default
    task_routes={'*': {'queue': 'celery'}},
)

# Beat schedule configuration
celery_app.conf.beat_schedule = {
    # Nightly governance loop - runs at 2:00 AM UTC
    'nightly-governance-loop': {
        'task': 'nova.governance.run_governance_task',
        'schedule': crontab(hour=2, minute=0),
        'args': [],
        'options': {'queue': 'governance'}
    },
    
    # Hourly memory cleanup
    'hourly-memory-cleanup': {
        'task': 'nova.maintenance.memory_cleanup_task', 
        'schedule': crontab(minute=0),  # Every hour on the hour
        'args': [],
        'options': {'queue': 'maintenance'}
    },
    
    # Daily analytics processing - runs at 3:00 AM UTC (after governance)
    'daily-analytics-processing': {
        'task': 'nova.analytics.process_daily_metrics_task',
        'schedule': crontab(hour=3, minute=0),
        'args': [],
        'options': {'queue': 'analytics'}
    },
    
    # Weekly competitor analysis - runs Sunday at 4:00 AM UTC
    'weekly-competitor-analysis': {
        'task': 'nova.analysis.competitor_analysis_task',
        'schedule': crontab(hour=4, minute=0, day_of_week=0),  # Sunday
        'args': [],
        'options': {'queue': 'analysis'}
    },
    
    # Daily trend intelligence scan - runs at 6:00 AM UTC
    'daily-trend-scan': {
        'task': 'nova.trends.daily_trend_scan_task',
        'schedule': crontab(hour=6, minute=0),
        'args': [],
        'options': {'queue': 'trends'}
    },
}

# Task configuration
celery_app.conf.task_annotations = {
    'nova.governance.run_governance_task': {
        'rate_limit': '1/h',  # Max once per hour
        'max_retries': 3,
        'default_retry_delay': 300,  # 5 minutes
    },
    'nova.maintenance.memory_cleanup_task': {
        'rate_limit': '2/h',  # Max twice per hour
        'max_retries': 1,
        'default_retry_delay': 60,
    },
}

# Auto-discover tasks from all nova modules
celery_app.autodiscover_tasks([
    'nova.governance',
    'nova.maintenance', 
    'nova.analytics_tasks',
    'nova.analysis',
    'nova.trends',
])

# Health check task for monitoring
@celery_app.task(name='nova.health_check')
def health_check():
    """Simple health check task for monitoring Celery workers."""
    return {
        'status': 'healthy',
        'worker': True,
        'timestamp': celery_app.now().isoformat()
    }
