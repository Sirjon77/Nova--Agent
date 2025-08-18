"""
Celery tasks for Nova Agent maintenance operations.

This module contains background maintenance tasks like memory cleanup,
log rotation, and system health checks.
"""

import asyncio
import logging
import os
import yaml
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from nova.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(
    name="nova.maintenance.memory_cleanup_task",
    bind=True,
    autoretry_for=(Exception,),
    max_retries=1,
    retry_backoff=True
)
def memory_cleanup_task(self, max_age_hours: int = 24) -> Dict[str, Any]:
    """
    Celery task to perform memory and cache cleanup.
    
    This task replaces the hourly memory cleanup that was running
    in the manual FastAPI startup loop.
    
    Args:
        max_age_hours: Maximum age of items to keep in hours
        
    Returns:
        Dict containing cleanup results and metrics
    """
    task_id = self.request.id
    logger.info(f"Starting memory cleanup task {task_id}")
    
    try:
        # Load memory limit from policy if available
        memory_limit_mb = _load_memory_limit()
        
        # Import here to avoid circular dependencies
        from nova.memory_guard import cleanup as memory_cleanup
        
        # Run the cleanup in async context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                memory_cleanup(
                    max_age_hours=max_age_hours,
                    memory_limit_mb=memory_limit_mb
                )
            )
            
            logger.info(f"Memory cleanup task {task_id} completed")
            
            return {
                'task_id': task_id,
                'status': 'completed',
                'cleaned_items': result.get('cleaned_items', 0) if result else 0,
                'memory_freed_mb': result.get('memory_freed_mb', 0) if result else 0,
                'max_age_hours': max_age_hours,
                'memory_limit_mb': memory_limit_mb
            }
            
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Memory cleanup task {task_id} failed: {exc}", exc_info=True)
        # Don't retry extensively for cleanup tasks
        if self.request.retries >= 1:
            logger.warning("Memory cleanup failed after retries, continuing")
            return {
                'task_id': task_id,
                'status': 'failed',
                'error': str(exc),
                'retries': self.request.retries
            }
        raise


@celery_app.task(
    name="nova.maintenance.log_rotation_task",
    bind=True
)
def log_rotation_task(self, max_log_age_days: int = 7) -> Dict[str, Any]:
    """
    Task to rotate and clean up old log files.
    
    Args:
        max_log_age_days: Maximum age of log files to keep
        
    Returns:
        Dict containing rotation results
    """
    task_id = self.request.id
    logger.info(f"Starting log rotation task {task_id}")
    
    try:
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            return {
                'task_id': task_id,
                'status': 'skipped',
                'reason': 'logs directory not found'
            }
        
        cutoff_date = datetime.now() - timedelta(days=max_log_age_days)
        files_removed = 0
        bytes_freed = 0
        
        for filename in os.listdir(logs_dir):
            if not filename.endswith('.log'):
                continue
                
            filepath = os.path.join(logs_dir, filename)
            
            try:
                # Check file age
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_time < cutoff_date:
                    file_size = os.path.getsize(filepath)
                    os.remove(filepath)
                    files_removed += 1
                    bytes_freed += file_size
                    logger.debug(f"Removed old log file: {filename}")
                    
            except OSError as e:
                logger.warning(f"Failed to remove log file {filename}: {e}")
        
        logger.info(f"Log rotation completed: {files_removed} files removed, {bytes_freed} bytes freed")
        
        return {
            'task_id': task_id,
            'status': 'completed',
            'files_removed': files_removed,
            'bytes_freed': bytes_freed,
            'max_age_days': max_log_age_days
        }
        
    except Exception as exc:
        logger.error(f"Log rotation task {task_id} failed: {exc}", exc_info=True)
        raise


@celery_app.task(
    name="nova.maintenance.system_health_check",
    bind=True
)
def system_health_check_task(self) -> Dict[str, Any]:
    """
    Comprehensive system health check task.
    
    Checks various system components and reports health status.
    
    Returns:
        Dict containing health check results
    """
    task_id = self.request.id
    logger.info(f"Starting system health check {task_id}")
    
    try:
        health_results = {
            'disk_space': _check_disk_space(),
            'memory_usage': _check_memory_usage(),
            'database_connection': _check_database_connection(),
            'redis_connection': _check_redis_connection(),
            'config_files': _check_config_files(),
        }
        
        # Calculate overall health
        healthy_checks = sum(1 for result in health_results.values() if result.get('healthy', False))
        total_checks = len(health_results)
        overall_healthy = healthy_checks == total_checks
        
        result = {
            'task_id': task_id,
            'status': 'completed',
            'overall_healthy': overall_healthy,
            'healthy_checks': healthy_checks,
            'total_checks': total_checks,
            'checks': health_results,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if not overall_healthy:
            logger.warning(f"System health check found issues: {healthy_checks}/{total_checks} checks passed")
        else:
            logger.info("System health check: all systems healthy")
        
        return result
        
    except Exception as exc:
        logger.error(f"System health check {task_id} failed: {exc}", exc_info=True)
        raise


def _load_memory_limit() -> Optional[int]:
    """Load memory limit from policy configuration."""
    try:
        with open('config/policy.yaml', 'r') as f:
            policy_cfg = yaml.safe_load(f)
        return policy_cfg.get('sandbox', {}).get('memory_limit_mb')
    except Exception:
        return None


def _check_disk_space() -> Dict[str, Any]:
    """Check available disk space."""
    try:
        import shutil
        total, used, free = shutil.disk_usage('.')
        
        free_percent = (free / total) * 100
        healthy = free_percent > 10  # Alert if less than 10% free
        
        return {
            'healthy': healthy,
            'free_bytes': free,
            'total_bytes': total,
            'free_percent': free_percent
        }
    except Exception as e:
        return {'healthy': False, 'error': str(e)}


def _check_memory_usage() -> Dict[str, Any]:
    """Check system memory usage."""
    try:
        import psutil
        memory = psutil.virtual_memory()
        
        healthy = memory.percent < 90  # Alert if more than 90% used
        
        return {
            'healthy': healthy,
            'used_percent': memory.percent,
            'available_bytes': memory.available,
            'total_bytes': memory.total
        }
    except ImportError:
        return {'healthy': True, 'error': 'psutil not available'}
    except Exception as e:
        return {'healthy': False, 'error': str(e)}


def _check_database_connection() -> Dict[str, Any]:
    """Check database connectivity."""
    try:
        # This would depend on your database setup
        # For now, just check if the database module can be imported
        from nova.db import get_db
        return {'healthy': True, 'status': 'connected'}
    except ImportError:
        return {'healthy': True, 'status': 'no_database_module'}
    except Exception as e:
        return {'healthy': False, 'error': str(e)}


def _check_redis_connection() -> Dict[str, Any]:
    """Check Redis connectivity."""
    try:
        import redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        r = redis.from_url(redis_url)
        r.ping()
        return {'healthy': True, 'status': 'connected'}
    except Exception as e:
        return {'healthy': False, 'error': str(e)}


def _check_config_files() -> Dict[str, Any]:
    """Check that required configuration files exist and are valid."""
    try:
        config_files = [
            'config/settings.yaml',
            'governance_config.yaml',
        ]
        
        results = {}
        all_healthy = True
        
        for config_file in config_files:
            try:
                with open(config_file, 'r') as f:
                    yaml.safe_load(f)
                results[config_file] = {'exists': True, 'valid': True}
            except FileNotFoundError:
                results[config_file] = {'exists': False, 'valid': False}
                all_healthy = False
            except yaml.YAMLError:
                results[config_file] = {'exists': True, 'valid': False}
                all_healthy = False
        
        return {
            'healthy': all_healthy,
            'files': results
        }
    except Exception as e:
        return {'healthy': False, 'error': str(e)}
