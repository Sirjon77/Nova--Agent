"""
Observability API Routes for Nova Agent

Provides REST API endpoints for:
- Prometheus metrics
- Health checks
- Performance monitoring
- Audit logs
- Error tracking
"""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import PlainTextResponse
from typing import Dict, List, Any, Optional
import time

from nova.observability import (
    get_health_status,
    get_metrics,
    get_performance_summary,
    get_audit_log,
    get_error_summary,
    record_request,
    record_error
)

router = APIRouter(prefix="/observability", tags=["observability"])

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Get comprehensive health status."""
    try:
        return get_health_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def prometheus_metrics() -> Response:
    """Get Prometheus metrics."""
    try:
        metrics = get_metrics()
        return Response(content=metrics, media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance")
async def performance_summary() -> Dict[str, Any]:
    """Get performance summary."""
    try:
        return get_performance_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit")
async def audit_log_endpoint(
    limit: int = 100,
    log_type: Optional[str] = None
) -> Dict[str, Any]:
    """Get audit log entries."""
    try:
        if limit > 1000:
            raise HTTPException(status_code=400, detail="Limit cannot exceed 1000")
        
        log_entries = get_audit_log(limit, log_type)
        return {
            "entries": log_entries,
            "count": len(log_entries),
            "limit": limit,
            "log_type": log_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/errors")
async def error_summary() -> Dict[str, Any]:
    """Get error summary."""
    try:
        return get_error_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def system_status() -> Dict[str, Any]:
    """Get system status overview."""
    try:
        health = get_health_status()
        performance = get_performance_summary()
        errors = get_error_summary()
        
        return {
            "health": health,
            "performance": performance,
            "errors": errors,
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/uptime")
async def uptime() -> Dict[str, Any]:
    """Get system uptime information."""
    try:
        health = get_health_status()
        uptime_seconds = health.get("uptime_seconds", 0)
        
        # Convert to human readable format
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        
        return {
            "uptime_seconds": uptime_seconds,
            "uptime_formatted": f"{days}d {hours}h {minutes}m {seconds}s",
            "start_time": health.get("timestamp"),
            "status": health.get("status")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs")
async def system_logs(
    log_type: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """Get system logs with filtering."""
    try:
        if limit > 500:
            raise HTTPException(status_code=400, detail="Limit cannot exceed 500")
        
        log_entries = get_audit_log(limit, log_type)
        
        # Filter by log type if specified
        if log_type:
            filtered_entries = [entry for entry in log_entries if entry.get("type") == log_type]
        else:
            filtered_entries = log_entries
        
        return {
            "logs": filtered_entries,
            "count": len(filtered_entries),
            "log_type": log_type,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def system_alerts() -> Dict[str, Any]:
    """Get current system alerts."""
    try:
        health = get_health_status()
        errors = get_error_summary()
        
        alerts = []
        
        # Health alerts
        if health.get("status") != "healthy":
            alerts.append({
                "type": "health",
                "severity": "high" if health.get("status") == "unhealthy" else "medium",
                "message": f"System health is {health.get('status')}",
                "details": health.get("issues", [])
            })
        
        # Error alerts
        recent_errors = errors.get("recent_errors", 0)
        if recent_errors > 5:
            alerts.append({
                "type": "errors",
                "severity": "high" if recent_errors > 10 else "medium",
                "message": f"High error rate: {recent_errors} errors in last hour",
                "details": errors.get("latest_errors", [])
            })
        
        # Performance alerts
        performance = get_performance_summary()
        if "summary" in performance:
            cpu_current = performance["summary"]["cpu"]["current"]
            memory_current = performance["summary"]["memory"]["current"]
            
            if cpu_current > 80:
                alerts.append({
                    "type": "performance",
                    "severity": "medium",
                    "message": f"High CPU usage: {cpu_current}%",
                    "details": {"cpu_percent": cpu_current}
                })
            
            if memory_current > 85:
                alerts.append({
                    "type": "performance",
                    "severity": "medium",
                    "message": f"High memory usage: {memory_current}%",
                    "details": {"memory_percent": memory_current}
                })
        
        return {
            "alerts": alerts,
            "count": len(alerts),
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard")
async def observability_dashboard() -> Dict[str, Any]:
    """Get comprehensive dashboard data."""
    try:
        health = get_health_status()
        performance = get_performance_summary()
        errors = get_error_summary()
        alerts = await system_alerts()
        
        # Get recent activity
        recent_logs = get_audit_log(20)
        
        return {
            "health": health,
            "performance": performance,
            "errors": errors,
            "alerts": alerts,
            "recent_activity": recent_logs,
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/summary")
async def metrics_summary() -> Dict[str, Any]:
    """Get metrics summary for dashboard."""
    try:
        health = get_health_status()
        performance = get_performance_summary()
        errors = get_error_summary()
        
        # Calculate key metrics
        uptime_seconds = health.get("uptime_seconds", 0)
        uptime_hours = uptime_seconds / 3600
        
        total_errors = errors.get("total_errors", 0)
        recent_errors = errors.get("recent_errors", 0)
        
        error_rate = (recent_errors / max(uptime_hours, 1)) if uptime_hours > 0 else 0
        
        return {
            "uptime_hours": uptime_hours,
            "status": health.get("status"),
            "total_errors": total_errors,
            "recent_errors": recent_errors,
            "error_rate_per_hour": error_rate,
            "performance": performance.get("summary", {}),
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 