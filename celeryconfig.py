
from datetime import timedelta

broker_url = 'redis://redis:6379/0'
result_backend = 'redis://redis:6379/1'
task_acks_late = True
worker_max_tasks_per_child = 100

beat_schedule = {
    'memory-cleanup-daily': {
        'task': 'memory_guard.cleanup',
        'schedule': timedelta(days=1),
    },
    # Weekly digest: run once every 7 days to generate and upload a
    # performance summary and landing pages.  Adjust timing as
    # necessary for your workflow.
    'weekly-digest': {
        'task': 'nova.weekly_digest',
        'schedule': timedelta(days=7),
    },
    # Competitor analysis every 72 hours; seeds are derived from the
    # COMPETITOR_SEEDS environment variable (comma separated) or
    # default to an empty list.  Adjust the schedule as needed.
    'competitor-analysis-72h': {
        'task': 'nova.competitor_analysis',
        'schedule': timedelta(days=3),
        # args will be resolved by the competitor_analysis task when None
        'args': (None, 10),
    },
    # Daily processing of metrics to retire underperformers and update the
    # leaderboard.  The RETIRE_THRESHOLD environment variable can
    # override the default threshold.
    'metrics-processing-daily': {
        'task': 'nova.process_metrics',
        'schedule': timedelta(days=1),
    },
}
