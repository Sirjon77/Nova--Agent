"""
Observability System for Nova Agent

Provides comprehensive monitoring, metrics, and health checks:
- Prometheus metrics collection
- Health check endpoints
- Centralized audit logging
- Performance monitoring
- Alert system
"""

import time
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import asyncio
from collections import defaultdict, deque
import threading

from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest, CONTENT_TYPE_LATEST
from fastapi import HTTPException
import psutil

from utils.memory_manager import store_long, get_relevant_memories

logger = logging.getLogger(__name__)

class NovaObservability:
    """
    Comprehensive observability system for Nova Agent.
    """
    
    def __init__(self, metrics_dir: str = "data/metrics"):
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Prometheus metrics
        self._init_prometheus_metrics()
        
        # Performance tracking
        self.performance_history = deque(maxlen=1000)
        self.error_history = deque(maxlen=100)
        self.audit_log = deque(maxlen=10000)
        
        # System monitoring
        self.start_time = time.time()
        self.last_health_check = time.time()
        
        # Thread safety
        self._lock = threading.Lock()
        
    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics."""
        # Request metrics
        self.request_counter = Counter(
            'nova_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status']
        )
        
        self.request_duration = Histogram(
            'nova_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint']
        )
        
        # NLP metrics
        self.nlp_requests = Counter(
            'nova_nlp_requests_total',
            'Total NLP requests',
            ['intent_type', 'confidence_level']
        )
        
        self.nlp_accuracy = Gauge(
            'nova_nlp_accuracy',
            'NLP intent classification accuracy'
        )
        
        # Memory metrics
        self.memory_operations = Counter(
            'nova_memory_operations_total',
            'Memory operations',
            ['operation_type', 'namespace']
        )
        
        self.memory_size = Gauge(
            'nova_memory_size_bytes',
            'Memory storage size in bytes'
        )
        
        # System metrics
        self.cpu_usage = Gauge(
            'nova_cpu_usage_percent',
            'CPU usage percentage'
        )
        
        self.memory_usage = Gauge(
            'nova_memory_usage_bytes',
            'Memory usage in bytes'
        )
        
        self.disk_usage = Gauge(
            'nova_disk_usage_bytes',
            'Disk usage in bytes'
        )
        
        # Research metrics
        self.research_experiments = Counter(
            'nova_research_experiments_total',
            'Research experiments',
            ['status', 'category']
        )
        
        self.research_success_rate = Gauge(
            'nova_research_success_rate',
            'Research experiment success rate'
        )
        
        # Governance metrics
        self.governance_cycles = Counter(
            'nova_governance_cycles_total',
            'Governance cycles',
            ['status']
        )
        
        self.governance_duration = Histogram(
            'nova_governance_duration_seconds',
            'Governance cycle duration in seconds'
        )
        
        # Error metrics
        self.error_counter = Counter(
            'nova_errors_total',
            'Total errors',
            ['error_type', 'module']
        )
        
        # Performance summary
        self.performance_summary = Summary(
            'nova_performance_summary',
            'Performance summary statistics'
        )
    
    def record_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record a request metric."""
        self.request_counter.labels(method=method, endpoint=endpoint, status=status).inc()
        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)
        
        # Store in audit log
        self._add_audit_entry({
            "type": "request",
            "method": method,
            "endpoint": endpoint,
            "status": status,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        })
    
    def record_nlp_request(self, intent_type: str, confidence: float):
        """Record an NLP request metric."""
        confidence_level = self._get_confidence_level(confidence)
        self.nlp_requests.labels(intent_type=intent_type, confidence_level=confidence_level).inc()
        
        # Update accuracy gauge
        self._update_nlp_accuracy()
    
    def record_memory_operation(self, operation: str, namespace: str, size_bytes: int = 0):
        """Record a memory operation metric."""
        self.memory_operations.labels(operation_type=operation, namespace=namespace).inc()
        
        if size_bytes > 0:
            self.memory_size.inc(size_bytes)
    
    def record_research_experiment(self, status: str, category: str, success: bool):
        """Record a research experiment metric."""
        self.research_experiments.labels(status=status, category=category).inc()
        
        # Update success rate
        self._update_research_success_rate()
    
    def record_governance_cycle(self, status: str, duration: float):
        """Record a governance cycle metric."""
        self.governance_cycles.labels(status=status).inc()
        self.governance_duration.observe(duration)
    
    def record_error(self, error_type: str, module: str, error_message: str):
        """Record an error metric."""
        self.error_counter.labels(error_type=error_type, module=module).inc()
        
        # Store in error history
        with self._lock:
            self.error_history.append({
                "type": error_type,
                "module": module,
                "message": error_message,
                "timestamp": datetime.now().isoformat()
            })
        
        # Store in audit log
        self._add_audit_entry({
            "type": "error",
            "error_type": error_type,
            "module": module,
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        })
    
    def update_system_metrics(self):
        """Update system metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_usage.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.memory_usage.set(memory.used)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.disk_usage.set(disk.used)
            
            # Store performance data
            performance_data = {
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": cpu_percent,
                "memory_used": memory.used,
                "memory_percent": memory.percent,
                "disk_used": disk.used,
                "disk_percent": (disk.used / disk.total) * 100
            }
            
            with self._lock:
                self.performance_history.append(performance_data)
            
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        try:
            # System health
            system_health = self._check_system_health()
            
            # Service health
            service_health = self._check_service_health()
            
            # Memory health
            memory_health = self._check_memory_health()
            
            # Overall health
            overall_health = "healthy"
            issues = []
            
            if system_health["status"] != "healthy":
                overall_health = "degraded"
                issues.extend(system_health.get("issues", []))
            
            if service_health["status"] != "healthy":
                overall_health = "degraded"
                issues.extend(service_health.get("issues", []))
            
            if memory_health["status"] != "healthy":
                overall_health = "degraded"
                issues.extend(memory_health.get("issues", []))
            
            if len(issues) > 5:
                overall_health = "unhealthy"
            
            return {
                "status": overall_health,
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": time.time() - self.start_time,
                "system": system_health,
                "services": service_health,
                "memory": memory_health,
                "issues": issues,
                "last_health_check": self.last_health_check
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _check_system_health(self) -> Dict[str, Any]:
        """Check system health."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            issues = []
            status = "healthy"
            
            if cpu_percent > 80:
                issues.append(f"High CPU usage: {cpu_percent}%")
                status = "degraded"
            
            if memory.percent > 85:
                issues.append(f"High memory usage: {memory.percent}%")
                status = "degraded"
            
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > 90:
                issues.append(f"High disk usage: {disk_percent:.1f}%")
                status = "degraded"
            
            return {
                "status": status,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk_percent,
                "issues": issues
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "issues": [f"System check failed: {str(e)}"]
            }
    
    def _check_service_health(self) -> Dict[str, Any]:
        """Check service health."""
        try:
            issues = []
            status = "healthy"
            
            # Check if recent errors are too frequent
            recent_errors = [e for e in self.error_history 
                           if (datetime.now() - datetime.fromisoformat(e["timestamp"])).seconds < 300]
            
            if len(recent_errors) > 10:
                issues.append(f"Too many recent errors: {len(recent_errors)} in last 5 minutes")
                status = "degraded"
            
            # Check if requests are failing
            # This would need to be implemented based on actual request tracking
            
            return {
                "status": status,
                "recent_errors": len(recent_errors),
                "issues": issues
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "issues": [f"Service check failed: {str(e)}"]
            }
    
    def _check_memory_health(self) -> Dict[str, Any]:
        """Check memory system health."""
        try:
            from memory import get_memory_status
            memory_status = get_memory_status()
            
            issues = []
            status = "healthy"
            
            if not memory_status["fully_available"]:
                issues.append("Memory system not fully available")
                status = "degraded"
            
            if not memory_status["weaviate_available"]:
                issues.append("Weaviate not available")
                status = "degraded"
            
            if not memory_status["sentence_transformers_available"]:
                issues.append("Sentence transformers not available")
                status = "degraded"
            
            return {
                "status": status,
                "memory_status": memory_status,
                "issues": issues
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "issues": [f"Memory check failed: {str(e)}"]
            }
    
    def get_metrics(self) -> str:
        """Get Prometheus metrics."""
        return generate_latest()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        try:
            with self._lock:
                if not self.performance_history:
                    return {"error": "No performance data available"}
                
                recent_data = list(self.performance_history)[-100:]  # Last 100 entries
                
                cpu_values = [d["cpu_percent"] for d in recent_data]
                memory_values = [d["memory_percent"] for d in recent_data]
                disk_values = [d["disk_percent"] for d in recent_data]
                
                return {
                    "summary": {
                        "cpu": {
                            "current": cpu_values[-1] if cpu_values else 0,
                            "average": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                            "max": max(cpu_values) if cpu_values else 0,
                            "min": min(cpu_values) if cpu_values else 0
                        },
                        "memory": {
                            "current": memory_values[-1] if memory_values else 0,
                            "average": sum(memory_values) / len(memory_values) if memory_values else 0,
                            "max": max(memory_values) if memory_values else 0,
                            "min": min(memory_values) if memory_values else 0
                        },
                        "disk": {
                            "current": disk_values[-1] if disk_values else 0,
                            "average": sum(disk_values) / len(disk_values) if disk_values else 0,
                            "max": max(disk_values) if disk_values else 0,
                            "min": min(disk_values) if disk_values else 0
                        }
                    },
                    "data_points": len(recent_data),
                    "time_range": "Last 100 measurements"
                }
                
        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {"error": str(e)}
    
    def get_audit_log(self, limit: int = 100, log_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get audit log entries."""
        try:
            with self._lock:
                if log_type:
                    filtered_log = [entry for entry in self.audit_log if entry.get("type") == log_type]
                    return list(filtered_log)[-limit:]
                else:
                    return list(self.audit_log)[-limit:]
                    
        except Exception as e:
            logger.error(f"Failed to get audit log: {e}")
            return []
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary."""
        try:
            with self._lock:
                if not self.error_history:
                    return {"error": "No error data available"}
                
                # Group errors by type
                error_counts = defaultdict(int)
                module_counts = defaultdict(int)
                
                for error in self.error_history:
                    error_counts[error["type"]] += 1
                    module_counts[error["module"]] += 1
                
                recent_errors = [e for e in self.error_history 
                               if (datetime.now() - datetime.fromisoformat(e["timestamp"])).seconds < 3600]
                
                return {
                    "total_errors": len(self.error_history),
                    "recent_errors": len(recent_errors),
                    "error_types": dict(error_counts),
                    "error_modules": dict(module_counts),
                    "latest_errors": list(self.error_history)[-10:]  # Last 10 errors
                }
                
        except Exception as e:
            logger.error(f"Failed to get error summary: {e}")
            return {"error": str(e)}
    
    def _add_audit_entry(self, entry: Dict[str, Any]):
        """Add an entry to the audit log."""
        with self._lock:
            self.audit_log.append(entry)
        
        # Store in long-term memory
        try:
            store_long("audit", "log", json.dumps(entry))
        except Exception as e:
            logger.error(f"Failed to store audit entry: {e}")
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Convert confidence score to level."""
        if confidence >= 0.9:
            return "very_high"
        elif confidence >= 0.8:
            return "high"
        elif confidence >= 0.7:
            return "medium"
        elif confidence >= 0.6:
            return "low"
        else:
            return "very_low"
    
    def _update_nlp_accuracy(self):
        """Update NLP accuracy gauge."""
        try:
            # This would need to be implemented based on actual accuracy tracking
            # For now, use a placeholder value
            self.nlp_accuracy.set(0.85)
        except Exception as e:
            logger.error(f"Failed to update NLP accuracy: {e}")
    
    def _update_research_success_rate(self):
        """Update research success rate gauge."""
        try:
            # This would need to be implemented based on actual success tracking
            # For now, use a placeholder value
            self.research_success_rate.set(0.75)
        except Exception as e:
            logger.error(f"Failed to update research success rate: {e}")
    
    def start_monitoring(self):
        """Start the monitoring loop."""
        def monitor_loop():
            while True:
                try:
                    self.update_system_metrics()
                    self.last_health_check = time.time()
                    time.sleep(60)  # Update every minute
                except Exception as e:
                    logger.error(f"Monitoring loop error: {e}")
                    time.sleep(60)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        logger.info("Observability monitoring started")

# Global observability instance
nova_observability = NovaObservability()

def get_health_status():
    """Get health status."""
    return nova_observability.get_health_status()

def get_metrics():
    """Get Prometheus metrics."""
    return nova_observability.get_metrics()

def get_performance_summary():
    """Get performance summary."""
    return nova_observability.get_performance_summary()

def get_audit_log(limit: int = 100, log_type: Optional[str] = None):
    """Get audit log."""
    return nova_observability.get_audit_log(limit, log_type)

def get_error_summary():
    """Get error summary."""
    return nova_observability.get_error_summary()

def record_request(method: str, endpoint: str, status: int, duration: float):
    """Record a request."""
    nova_observability.record_request(method, endpoint, status, duration)

def record_error(error_type: str, module: str, error_message: str):
    """Record an error."""
    nova_observability.record_error(error_type, module, error_message) 