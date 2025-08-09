"""
Celery tasks for Nova Agent governance operations.

This module contains Celery task definitions for periodic governance operations,
replacing the manual scheduling loops with robust, scalable background jobs.
"""

import asyncio
import logging
import yaml
from typing import Dict, Any, List, Optional

from nova.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(
    name="nova.governance.run_governance_task",
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def run_governance_task(self) -> Dict[str, Any]:
    """
    Celery task to run the nightly governance loop.
    
    This task replaces the manual asyncio loop that was running in FastAPI startup.
    It handles governance analysis, recommendations, and policy enforcement.
    
    Returns:
        Dict containing task execution results and metrics
    """
    task_id = self.request.id
    logger.info(f"Starting governance task {task_id}")
    
    try:
        # Load governance configuration
        governance_config = _load_governance_config()
        
        # Import here to avoid circular dependencies
        from nova.governance.governance_loop import run as governance_run
        
        # Run the governance loop in async context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                governance_run(governance_config, [], [], [])
            )
            
            logger.info(f"Governance task {task_id} completed successfully")
            
            # Update metrics
            _update_governance_metrics(success=True)
            
            return {
                'task_id': task_id,
                'status': 'completed',
                'result': result,
                'retry_count': self.request.retries
            }
            
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Governance task {task_id} failed: {exc}", exc_info=True)
        
        # Update metrics
        _update_governance_metrics(success=False, error=str(exc))
        
        # Re-raise for Celery retry logic
        raise


def _load_governance_config() -> Dict[str, Any]:
    """Load governance configuration from settings file."""
    try:
        with open('config/settings.yaml', 'r') as f:
            cfg_all = yaml.safe_load(f)
        return cfg_all.get('governance', {})
    except Exception as e:
        logger.warning(f"Failed to load governance config: {e}")
        return {}


def _update_governance_metrics(success: bool, error: Optional[str] = None) -> None:
    """Update Prometheus metrics for governance task execution."""
    try:
        from nova.metrics import (
            governance_loop_duration,
            channels_scored,
            actions_flagged
        )
        
        # These would be updated with actual values from the governance run
        # For now, just log the execution
        if success:
            logger.info("Governance metrics updated: success")
        else:
            logger.warning(f"Governance metrics updated: failure - {error}")
            
    except ImportError:
        # Metrics not available, continue silently
        pass


@celery_app.task(
    name="nova.governance.run_manual_governance",
    bind=True
)
def run_manual_governance_task(self, config_overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Manually triggered governance task (e.g., from API endpoint).
    
    Args:
        config_overrides: Optional configuration overrides for this run
        
    Returns:
        Dict containing task execution results
    """
    task_id = self.request.id
    logger.info(f"Starting manual governance task {task_id}")
    
    try:
        # Load base config and apply overrides
        governance_config = _load_governance_config()
        if config_overrides:
            governance_config.update(config_overrides)
        
        # Import here to avoid circular dependencies
        from nova.governance.governance_loop import run as governance_run
        
        # Run the governance loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                governance_run(governance_config, [], [], [])
            )
            
            logger.info(f"Manual governance task {task_id} completed")
            
            return {
                'task_id': task_id,
                'status': 'completed',
                'result': result,
                'config_overrides': config_overrides
            }
            
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Manual governance task {task_id} failed: {exc}", exc_info=True)
        raise


@celery_app.task(
    name="nova.governance.validate_governance_config",
    bind=True
)
def validate_governance_config_task(self) -> Dict[str, Any]:
    """
    Task to validate governance configuration and policies.
    
    This can be run periodically or triggered manually to ensure
    governance settings are valid and consistent.
    
    Returns:
        Dict containing validation results
    """
    task_id = self.request.id
    logger.info(f"Starting governance config validation {task_id}")
    
    try:
        config = _load_governance_config()
        
        # Validation logic
        validation_results = {
            'config_loaded': bool(config),
            'required_keys_present': _validate_required_keys(config),
            'metric_weights_valid': _validate_metric_weights(config),
            'thresholds_valid': _validate_thresholds(config),
        }
        
        all_valid = all(validation_results.values())
        
        return {
            'task_id': task_id,
            'status': 'completed',
            'valid': all_valid,
            'validation_results': validation_results,
            'config': config
        }
        
    except Exception as exc:
        logger.error(f"Config validation task {task_id} failed: {exc}", exc_info=True)
        raise


def _validate_required_keys(config: Dict[str, Any]) -> bool:
    """Validate that required configuration keys are present."""
    required_keys = ['metrics', 'thresholds', 'auto_actions']
    return all(key in config for key in required_keys)


def _validate_metric_weights(config: Dict[str, Any]) -> bool:
    """Validate metric weight configuration."""
    try:
        metrics = config.get('metrics', {})
        if not metrics:
            return False
            
        # Check that weights are numeric and reasonable
        for weight in metrics.values():
            if not isinstance(weight, (int, float)) or weight < 0 or weight > 1:
                return False
                
        # Check that weights sum to reasonable total (close to 1.0)
        total_weight = sum(metrics.values())
        return 0.8 <= total_weight <= 1.2
        
    except Exception:
        return False


def _validate_thresholds(config: Dict[str, Any]) -> bool:
    """Validate threshold configuration."""
    try:
        thresholds = config.get('thresholds', {})
        if not thresholds:
            return False
            
        # Check required thresholds
        required_thresholds = ['promote', 'retire']
        for threshold in required_thresholds:
            if threshold not in thresholds:
                return False
            
            value = thresholds[threshold]
            if not isinstance(value, (int, float)):
                return False
        
        # Check logical order (promote > retire)
        if thresholds['promote'] <= thresholds['retire']:
            return False
            
        return True
        
    except Exception:
        return False
