"""
Task Scheduler for Nova Agent v7.0

This module integrates with the planning engine to execute planned actions
and manage task workflows with proper scheduling and monitoring.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path
import uuid
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """Status of a scheduled task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """Priority levels for tasks."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class ScheduledTask:
    """A task scheduled for execution."""
    task_id: str
    name: str
    description: str
    action_type: str
    parameters: Dict[str, Any]
    scheduled_time: datetime
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    dependencies: List[str] = None  # List of task IDs this task depends on
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

class TaskExecutor:
    """Executes different types of tasks."""
    
    def __init__(self):
        self.action_handlers = {
            'create_content': self._handle_create_content,
            'schedule_post': self._handle_schedule_post,
            'analyze_metrics': self._handle_analyze_metrics,
            'send_alert': self._handle_send_alert,
            'optimize_channel': self._handle_optimize_channel,
            'trend_response': self._handle_trend_response,
            'tool_switch': self._handle_tool_switch,
            'budget_allocation': self._handle_budget_allocation,
        }
    
    async def execute_task(self, task: ScheduledTask) -> Dict[str, Any]:
        """Execute a scheduled task."""
        try:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            
            # Get the appropriate handler
            handler = self.action_handlers.get(task.action_type)
            if not handler:
                raise ValueError(f"Unknown action type: {task.action_type}")
            
            # Execute the task
            result = await handler(task.parameters)
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            
            logger.info(f"Task {task.task_id} completed successfully")
            return result
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
            
            logger.error(f"Task {task.task_id} failed: {e}")
            
            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                logger.info(f"Retrying task {task.task_id} (attempt {task.retry_count})")
                return await self.execute_task(task)
            
            return {"error": str(e), "retries_exhausted": True}
    
    async def _handle_create_content(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle content creation tasks."""
        # This would integrate with the content generation pipeline
        logger.info(f"Creating content with parameters: {parameters}")
        
        # Simulate content creation
        await asyncio.sleep(2)  # Simulate processing time
        
        return {
            "content_id": f"content_{uuid.uuid4().hex[:8]}",
            "status": "created",
            "format": parameters.get("format", "video"),
            "estimated_completion": (datetime.now() + timedelta(hours=1)).isoformat()
        }
    
    async def _handle_schedule_post(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle post scheduling tasks."""
        logger.info(f"Scheduling post with parameters: {parameters}")
        
        # This would integrate with the posting scheduler
        platforms = parameters.get("platforms", ["youtube"])
        scheduled_time = parameters.get("scheduled_time")
        
        return {
            "post_id": f"post_{uuid.uuid4().hex[:8]}",
            "platforms": platforms,
            "scheduled_time": scheduled_time,
            "status": "scheduled"
        }
    
    async def _handle_analyze_metrics(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle metrics analysis tasks."""
        logger.info(f"Analyzing metrics with parameters: {parameters}")
        
        # This would integrate with the analytics system
        await asyncio.sleep(1)  # Simulate analysis time
        
        return {
            "analysis_id": f"analysis_{uuid.uuid4().hex[:8]}",
            "insights": [
                "RPM trending upward",
                "Engagement rate stable",
                "View retention improving"
            ],
            "recommendations": [
                "Continue current content strategy",
                "Monitor competitor activity"
            ]
        }
    
    async def _handle_send_alert(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle alert sending tasks."""
        logger.info(f"Sending alert with parameters: {parameters}")
        
        message = parameters.get("message", "Alert triggered")
        channel = parameters.get("channel", "slack")
        
        # This would integrate with notification systems
        return {
            "alert_id": f"alert_{uuid.uuid4().hex[:8]}",
            "message": message,
            "channel": channel,
            "status": "sent"
        }
    
    async def _handle_optimize_channel(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle channel optimization tasks."""
        logger.info(f"Optimizing channel with parameters: {parameters}")
        
        channel_id = parameters.get("channel_id")
        optimization_type = parameters.get("type", "content")
        
        # This would integrate with the optimization engine
        await asyncio.sleep(3)  # Simulate optimization time
        
        return {
            "optimization_id": f"opt_{uuid.uuid4().hex[:8]}",
            "channel_id": channel_id,
            "type": optimization_type,
            "improvements": [
                "Content format optimized",
                "Posting schedule adjusted",
                "Audience targeting refined"
            ]
        }
    
    async def _handle_trend_response(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle trend response tasks."""
        logger.info(f"Responding to trend with parameters: {parameters}")
        
        trend_topic = parameters.get("topic")
        response_type = parameters.get("response_type", "content")
        
        # This would integrate with the trend response system
        await asyncio.sleep(2)
        
        return {
            "response_id": f"trend_{uuid.uuid4().hex[:8]}",
            "topic": trend_topic,
            "response_type": response_type,
            "actions_taken": [
                "Content created",
                "Scheduled for immediate posting",
                "Cross-platform distribution initiated"
            ]
        }
    
    async def _handle_tool_switch(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool switching tasks."""
        logger.info(f"Switching tools with parameters: {parameters}")
        
        old_tool = parameters.get("old_tool")
        new_tool = parameters.get("new_tool")
        reason = parameters.get("reason", "Performance issues")
        
        # This would integrate with the tool management system
        await asyncio.sleep(1)
        
        return {
            "switch_id": f"switch_{uuid.uuid4().hex[:8]}",
            "old_tool": old_tool,
            "new_tool": new_tool,
            "reason": reason,
            "status": "completed"
        }
    
    async def _handle_budget_allocation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle budget allocation tasks."""
        logger.info(f"Allocating budget with parameters: {parameters}")
        
        total_budget = parameters.get("total_budget", 1000)
        allocations = parameters.get("allocations", {})
        
        # This would integrate with the budget management system
        await asyncio.sleep(1)
        
        return {
            "allocation_id": f"budget_{uuid.uuid4().hex[:8]}",
            "total_budget": total_budget,
            "allocations": allocations,
            "status": "allocated"
        }

class TaskScheduler:
    """Main task scheduler that manages task execution."""
    
    def __init__(self):
        self.executor = TaskExecutor()
        self.scheduled_tasks: List[ScheduledTask] = []
        self.running_tasks: Dict[str, ScheduledTask] = {}
        self.completed_tasks: List[ScheduledTask] = []
        self.task_queue: List[ScheduledTask] = []
        
        # Load existing tasks
        self.load_tasks()
    
    def load_tasks(self):
        """Load tasks from persistent storage."""
        tasks_file = "data/scheduler/tasks.json"
        try:
            if Path(tasks_file).exists():
                with open(tasks_file, 'r') as f:
                    tasks_data = json.load(f)
                    for task_data in tasks_data:
                        task = ScheduledTask(**task_data)
                        if task.status == TaskStatus.PENDING:
                            self.scheduled_tasks.append(task)
                        elif task.status == TaskStatus.COMPLETED:
                            self.completed_tasks.append(task)
        except Exception as e:
            logger.error(f"Failed to load tasks: {e}")
    
    def save_tasks(self):
        """Save tasks to persistent storage."""
        tasks_file = "data/scheduler/tasks.json"
        try:
            os.makedirs(Path(tasks_file).parent, exist_ok=True)
            all_tasks = self.scheduled_tasks + self.completed_tasks
            tasks_data = [asdict(task) for task in all_tasks]
            with open(tasks_file, 'w') as f:
                json.dump(tasks_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save tasks: {e}")
    
    def schedule_task(self, name: str, description: str, action_type: str,
                     parameters: Dict[str, Any], scheduled_time: datetime,
                     priority: TaskPriority = TaskPriority.MEDIUM,
                     dependencies: List[str] = None) -> str:
        """Schedule a new task."""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            description=description,
            action_type=action_type,
            parameters=parameters,
            scheduled_time=scheduled_time,
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            dependencies=dependencies or []
        )
        
        self.scheduled_tasks.append(task)
        self.save_tasks()
        
        logger.info(f"Scheduled task {task_id}: {name}")
        return task_id
    
    def schedule_immediate_task(self, name: str, description: str, action_type: str,
                              parameters: Dict[str, Any], 
                              priority: TaskPriority = TaskPriority.MEDIUM,
                              dependencies: List[str] = None) -> str:
        """Schedule a task for immediate execution."""
        return self.schedule_task(
            name=name,
            description=description,
            action_type=action_type,
            parameters=parameters,
            scheduled_time=datetime.now(),
            priority=priority,
            dependencies=dependencies
        )
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        for task in self.scheduled_tasks:
            if task.task_id == task_id and task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                self.save_tasks()
                logger.info(f"Cancelled task {task_id}")
                return True
        return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a task."""
        # Check scheduled tasks
        for task in self.scheduled_tasks:
            if task.task_id == task_id:
                return asdict(task)
        
        # Check completed tasks
        for task in self.completed_tasks:
            if task.task_id == task_id:
                return asdict(task)
        
        return None
    
    def get_pending_tasks(self) -> List[ScheduledTask]:
        """Get all pending tasks."""
        return [task for task in self.scheduled_tasks if task.status == TaskStatus.PENDING]
    
    def get_running_tasks(self) -> List[ScheduledTask]:
        """Get all currently running tasks."""
        return list(self.running_tasks.values())
    
    def get_completed_tasks(self, limit: int = 100) -> List[ScheduledTask]:
        """Get recently completed tasks."""
        return sorted(self.completed_tasks, key=lambda t: t.completed_at, reverse=True)[:limit]
    
    async def process_scheduled_tasks(self):
        """Process all scheduled tasks that are ready to run."""
        current_time = datetime.now()
        ready_tasks = []
        
        # Find tasks that are ready to run
        for task in self.scheduled_tasks:
            if (task.status == TaskStatus.PENDING and 
                task.scheduled_time <= current_time and
                self._dependencies_met(task)):
                ready_tasks.append(task)
        
        # Sort by priority (higher priority first)
        ready_tasks.sort(key=lambda t: t.priority.value, reverse=True)
        
        # Execute ready tasks
        for task in ready_tasks:
            await self._execute_task(task)
    
    def _dependencies_met(self, task: ScheduledTask) -> bool:
        """Check if all dependencies for a task are met."""
        if not task.dependencies:
            return True
        
        # Check if all dependencies are completed
        completed_task_ids = {t.task_id for t in self.completed_tasks}
        return all(dep_id in completed_task_ids for dep_id in task.dependencies)
    
    async def _execute_task(self, task: ScheduledTask):
        """Execute a single task."""
        # Move task from scheduled to running
        self.scheduled_tasks.remove(task)
        self.running_tasks[task.task_id] = task
        
        try:
            # Execute the task
            await self.executor.execute_task(task)
            
            # Move task to completed
            del self.running_tasks[task.task_id]
            self.completed_tasks.append(task)
            
            # Keep only recent completed tasks
            if len(self.completed_tasks) > 1000:
                self.completed_tasks = self.completed_tasks[-500:]
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
            
            # Move task to completed (even if failed)
            del self.running_tasks[task.task_id]
            self.completed_tasks.append(task)
        
        self.save_tasks()
    
    async def run_scheduler_loop(self, interval_seconds: int = 30):
        """Run the scheduler loop continuously."""
        logger.info("Starting task scheduler loop")
        
        while True:
            try:
                await self.process_scheduled_tasks()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(interval_seconds)
    
    def schedule_from_plan(self, plan: Dict[str, Any]) -> List[str]:
        """Schedule tasks from a planning engine plan."""
        task_ids = []
        
        # Schedule recommended actions
        recommended_actions = plan.get('recommended_actions', [])
        for action in recommended_actions:
            task_id = self.schedule_immediate_task(
                name=action.get('action', 'Unknown Action'),
                description=action.get('expected_impact', ''),
                action_type=self._map_action_to_type(action),
                parameters=action,
                priority=self._map_priority(action.get('priority', 'medium'))
            )
            task_ids.append(task_id)
        
        # Schedule automated actions
        automated_actions = plan.get('automated_actions', [])
        for action_group in automated_actions:
            for action in action_group:
                task_id = self.schedule_immediate_task(
                    name=action.get('type', 'Automated Action'),
                    description=action.get('message', ''),
                    action_type=action.get('type', 'unknown'),
                    parameters=action,
                    priority=TaskPriority.HIGH
                )
                task_ids.append(task_id)
        
        logger.info(f"Scheduled {len(task_ids)} tasks from plan")
        return task_ids
    
    def _map_action_to_type(self, action: Dict[str, Any]) -> str:
        """Map action description to action type."""
        action_desc = action.get('action', '').lower()
        
        if 'content' in action_desc or 'create' in action_desc:
            return 'create_content'
        elif 'post' in action_desc or 'schedule' in action_desc:
            return 'schedule_post'
        elif 'analyze' in action_desc or 'metrics' in action_desc:
            return 'analyze_metrics'
        elif 'alert' in action_desc or 'notify' in action_desc:
            return 'send_alert'
        elif 'optimize' in action_desc:
            return 'optimize_channel'
        elif 'trend' in action_desc:
            return 'trend_response'
        else:
            return 'analyze_metrics'  # Default fallback
    
    def _map_priority(self, priority_str: str) -> TaskPriority:
        """Map priority string to TaskPriority enum."""
        priority_map = {
            'high': TaskPriority.HIGH,
            'medium': TaskPriority.MEDIUM,
            'low': TaskPriority.LOW,
            'critical': TaskPriority.CRITICAL
        }
        return priority_map.get(priority_str.lower(), TaskPriority.MEDIUM)
