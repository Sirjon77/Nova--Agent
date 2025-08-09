
"""
Legacy Celery configuration - DEPRECATED

This file is kept for backward compatibility but is no longer used.
The new Celery configuration is in nova/celery_app.py with enhanced
scheduling, retry logic, and task organization.

To use the new system:
1. Import from nova.celery_app instead
2. Use the new beat schedule with cron-style timing
3. Tasks are organized by module (governance, maintenance, metrics, etc.)
"""

from datetime import timedelta
import warnings

warnings.warn(
    "celeryconfig.py is deprecated. Use nova/celery_app.py for new Celery configuration.",
    DeprecationWarning,
    stacklevel=2
)

# Legacy configuration for backward compatibility
broker_url = 'redis://redis:6379/0'
result_backend = 'redis://redis:6379/1'
task_acks_late = True
worker_max_tasks_per_child = 100

# Legacy beat schedule - these tasks have been migrated to nova/celery_app.py
beat_schedule = {
    # DEPRECATED: Use nova.maintenance.memory_cleanup_task instead
    'memory-cleanup-daily': {
        'task': 'memory_guard.cleanup',
        'schedule': timedelta(days=1),
    },
    # DEPRECATED: Use nova.metrics.generate_weekly_report_task instead
    'weekly-digest': {
        'task': 'nova.weekly_digest',
        'schedule': timedelta(days=7),
    },
    # DEPRECATED: Use nova.analysis.competitor_analysis_task instead
    'competitor-analysis-72h': {
        'task': 'nova.competitor_analysis',
        'schedule': timedelta(days=3),
        'args': (None, 10),
    },
    # DEPRECATED: Use nova.metrics.process_daily_metrics_task instead
    'metrics-processing-daily': {
        'task': 'nova.process_metrics',
        'schedule': timedelta(days=1),
    },
}
