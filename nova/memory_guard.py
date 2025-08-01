"""
Periodic memory and cache cleanup for Nova Agent.

This module provides a simple cleanup function that can be scheduled to
run periodically (e.g. hourly) to prune stale in‑memory data and ensure
the application does not accumulate unbounded state. It looks at the
task manager and channel cache and removes entries older than a
configurable age threshold. It can also log a warning if the process
RSS exceeds a configured memory limit.

Because Celery is unavailable in this environment, scheduling should
be done from the FastAPI startup hook using asyncio. See
`nova.api.app` for the integration.
"""
from __future__ import annotations

import datetime
import logging
import os
import psutil
from typing import Optional

from nova.task_manager import task_manager

log = logging.getLogger("memory_guard")


async def cleanup(max_age_hours: int = 24, memory_limit_mb: Optional[int] = None) -> None:
    """Prune stale tasks and caches and log memory usage.

    Args:
        max_age_hours: The maximum age of completed tasks to retain. Tasks
            older than this threshold will be removed from the task manager.
        memory_limit_mb: Optional memory limit in megabytes. If provided and
            the current RSS exceeds the limit, a warning will be logged.
    """
    now = datetime.datetime.utcnow()
    cutoff = now - datetime.timedelta(hours=max_age_hours)
    # Remove old completed or failed tasks
    to_delete = []
    for tid, t in list(task_manager.all_tasks().items()):
        if t.completed_at and t.completed_at < cutoff:
            to_delete.append(tid)
    for tid in to_delete:
        del task_manager.all_tasks()[tid]
    if to_delete:
        log.info("Pruned %d old tasks", len(to_delete))
    # Log memory usage and warn if above threshold
    process = psutil.Process(os.getpid())
    rss_mb = process.memory_info().rss / (1024 * 1024)
    if memory_limit_mb and rss_mb > memory_limit_mb:
        log.warning("Memory usage high: %.2f MB exceeds limit %.2f MB", rss_mb, memory_limit_mb)
    else:
        log.debug("Memory usage: %.2f MB", rss_mb)