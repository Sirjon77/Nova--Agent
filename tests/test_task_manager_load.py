"""
Basic load test for the TaskManager.

This asynchronous test enqueues a number of dummy tasks in quick
succession to ensure that the TaskManager can handle concurrent task
execution without race conditions or missed updates. All tasks are
configured to sleep for zero seconds so the test runs quickly. After
enqueuing, the test waits briefly and asserts that all tasks have
completed.
"""

import asyncio
import pytest


@pytest.mark.asyncio
async def test_task_manager_handles_many_tasks(monkeypatch):
    # Import task_manager and dummy_task from nova
    from nova.task_manager import task_manager, TaskType, dummy_task
    # Monkeypatch dummy_task to return immediately instead of sleeping
    async def fast_task(duration: int = 0):
        return {"slept": duration}
    monkeypatch.setattr('nova.task_manager.dummy_task', fast_task)
    # Enqueue multiple tasks concurrently
    num_tasks = 30
    task_ids = []
    for _ in range(num_tasks):
        tid = await task_manager.enqueue(TaskType.CUSTOM, fast_task, duration=0)
        task_ids.append(tid)
    # Wait a small amount of time for tasks to complete
    await asyncio.sleep(0.5)
    # Assert that all tasks have completed and are recorded in the task manager
    completed = [task_manager.all_tasks()[tid] for tid in task_ids]
    assert all(t.status == t.status.COMPLETED for t in completed)