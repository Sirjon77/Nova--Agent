"""
Task management and event broadcasting for Nova Agent.

This module provides a simple in‑memory task manager that can be used
to offload potentially long‑running operations away from the HTTP
request/response cycle. It tracks the status of each task and emits
updates over the WebSocket event channel so that connected clients
receive real‑time feedback. Because Celery is not available in this
environment, tasks are executed using asyncio coroutines. Should
Celery become available in a future deployment the TaskManager can be
adapted to enqueue work onto a broker instead of running it in the
same process.

Usage:

    from nova.task_manager import task_manager, TaskType

    async def some_work(duration: int):
        # ... long running job ...
        await asyncio.sleep(duration)
        return {"finished": True}

    task_id = await task_manager.enqueue(TaskType.GENERATE_CONTENT, some_work, duration=10)

The manager will update its internal state and broadcast updates over
WebSockets as the task starts and completes. Consumers can fetch all
tasks via the API or listen for live updates via `/ws/events`.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import timezone,  datetime
from enum import Enum
from typing import Callable, Any, Awaitable, Dict, Optional

from nova.metrics import tasks_executed, task_duration

# Import broadcast helper from the API. This import is done inside the
# function to avoid circular dependencies on module import. See
# ``_broadcast_event`` below.


class TaskStatus(str, Enum):
    """Enumeration of task lifecycle states."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskType(str, Enum):
    """Enumeration of supported task types.

    Additional task types can be added here as new functionality is
    integrated (e.g. content generation, video upload, governance run).
    """

    GENERATE_CONTENT = "generate_content"
    PUBLISH_POST = "publish_post"
    RUN_GOVERNANCE = "run_governance"
    CUSTOM = "custom"

    # Extended task types for advanced modules
    DISCOVER_PROMPTS = "discover_prompts"
    GENERATE_FUNNEL = "generate_funnel"
    GENERATE_LEARNING_PLAN = "generate_learning_plan"
    GENERATE_NEGOTIATION = "generate_negotiation"
    GENERATE_DIRECT_MARKETING = "generate_direct_marketing"
    SUGGEST_HASHTAGS = "suggest_hashtags"
    SCHEDULE_POSTS = "schedule_posts"
    GENERATE_HOOKS = "generate_hooks"
    PROCESS_METRICS = "process_metrics"

    # Analyse competitors based on trending data
    ANALYZE_COMPETITORS = "analyze_competitors"

    # Distribute posts across multiple accounts on a platform
    DISTRIBUTE_POSTS = "distribute_posts"


class Task:
    """Represents a unit of work managed by TaskManager."""

    def __init__(self, task_type: TaskType, params: Dict[str, Any]) -> None:
        self.id: str = str(uuid.uuid4())
        self.type: TaskType = task_type
        self.params: Dict[str, Any] = params
        self.status: TaskStatus = TaskStatus.QUEUED
        self.created_at: datetime = datetime.now(timezone.utc)
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize task fields into a JSON‑serialisable dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "params": self.params,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
        }


class TaskManager:
    """Simple in‑memory task registry and executor.

    Tasks are executed using asyncio and updates are broadcast over the
    WebSocket event channel. Consumers can poll the manager for task
    state via the API.
    """

    def __init__(self) -> None:
        # Store tasks keyed by their ID
        self._tasks: Dict[str, Task] = {}

    def all_tasks(self) -> Dict[str, Task]:
        """Return a dictionary of all known tasks."""
        return self._tasks

    async def enqueue(self, task_type: TaskType, coro: Callable[..., Awaitable[Any]], **params: Any) -> str:
        """Create a task and schedule its execution.

        Args:
            task_type: The type of work to perform.
            coro: An awaitable function performing the work.
            **params: Arbitrary keyword arguments passed to the coroutine.

        Returns:
            The unique task ID.
        """
        task = Task(task_type, params)
        self._tasks[task.id] = task
        # Schedule the coroutine to run in the background
        asyncio.create_task(self._run_task(task, coro, **params))
        return task.id

    async def _run_task(self, task: Task, coro: Callable[..., Awaitable[Any]], **params: Any) -> None:
        """Internal helper to update task state while running the coroutine."""
        # Import broadcast helper lazily to avoid circular imports
        from nova.api.app import broadcast_event
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(timezone.utc)
        # Notify clients of status change
        await broadcast_event({"event": "task_update", "task": task.to_dict()})
        # Track duration
        start_time = asyncio.get_event_loop().time()
        try:
            result = await coro(**params)
            task.result = result
            task.status = TaskStatus.COMPLETED
        except Exception as exc:
            # Capture exception string as result for observability
            task.result = f"{type(exc).__name__}: {exc}"
            task.status = TaskStatus.FAILED
            # Send an alert asynchronously to notify operators of the failure.
            # Import inside the exception handler to avoid circular imports at module load.
            try:
                from nova.notify import send_alert  # type: ignore
                alert_msg = f"Task {task.id} ({task.type.value}) failed: {task.result}"
                # Fire and forget; do not block task completion
                asyncio.create_task(send_alert(alert_msg))
            except Exception:
                # If alerting fails, we silently ignore to avoid masking the original error
                pass
        finally:
            task.completed_at = datetime.now(timezone.utc)
            elapsed = asyncio.get_event_loop().time() - start_time
            # Update Prometheus metrics
            tasks_executed.inc()
            task_duration.observe(elapsed)
            # Notify clients of completion
            await broadcast_event({"event": "task_update", "task": task.to_dict()})


# Singleton instance used across the application
task_manager = TaskManager()


async def dummy_task(duration: int = 5) -> Dict[str, Any]:
    """A placeholder task that simply sleeps for a given duration.

    This function can be used for testing the task manager without
    integrating real external services. It returns a simple result
    indicating completion.

    Args:
        duration: Number of seconds to sleep.

    Returns:
        A dictionary indicating the task completed successfully.
    """
    await asyncio.sleep(duration)
    return {"slept": duration}