"""
API Routes for Nova's Autonomous Research System

Provides REST API endpoints for:
- Getting research dashboard data
- Starting research cycles
- Viewing experiment details
- Getting research insights
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
import asyncio

from nova.research_dashboard import (
    get_dashboard_data, 
    start_research_cycle, 
    get_research_summary,
    research_dashboard
)

router = APIRouter(prefix="/research", tags=["autonomous_research"])

@router.get("/dashboard")
async def get_research_dashboard() -> Dict[str, Any]:
    """Get comprehensive research dashboard data."""
    try:
        data = get_dashboard_data()
        if "error" in data:
            raise HTTPException(status_code=500, detail=data["error"])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_research_summary_endpoint() -> Dict[str, Any]:
    """Get research summary statistics."""
    try:
        summary = get_research_summary()
        if "error" in summary:
            raise HTTPException(status_code=500, detail=summary["error"])
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start-cycle")
async def start_research_cycle_endpoint() -> Dict[str, Any]:
    """Manually start a research cycle."""
    try:
        result = await start_research_cycle()
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/experiment/{experiment_id}")
async def get_experiment_details(experiment_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific experiment."""
    try:
        details = research_dashboard.get_experiment_details(experiment_id)
        if not details:
            raise HTTPException(status_code=404, detail="Experiment not found")
        return details
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hypothesis/{hypothesis_id}")
async def get_hypothesis_details(hypothesis_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific hypothesis."""
    try:
        details = research_dashboard.get_hypothesis_details(hypothesis_id)
        if not details:
            raise HTTPException(status_code=404, detail="Hypothesis not found")
        return details
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_research_status() -> Dict[str, Any]:
    """Get current research system status."""
    try:
        from nova.autonomous_research import get_research_status
        return get_research_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights")
async def get_research_insights() -> Dict[str, Any]:
    """Get top research insights and recommendations."""
    try:
        dashboard_data = get_dashboard_data()
        if "error" in dashboard_data:
            raise HTTPException(status_code=500, detail=dashboard_data["error"])
        
        return {
            "top_insights": dashboard_data.get("top_insights", []),
            "performance_trends": dashboard_data.get("performance_trends", {}),
            "recent_activity": dashboard_data.get("recent_activity", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/experiments")
async def list_experiments(limit: int = 10, status: Optional[str] = None) -> Dict[str, Any]:
    """List experiments with optional filtering."""
    try:
        from nova.autonomous_research import autonomous_researcher
        
        experiments = autonomous_researcher.experiments
        
        # Filter by status if provided
        if status:
            experiments = [e for e in experiments if e.status == status]
        
        # Sort by creation date (newest first)
        experiments.sort(key=lambda x: x.created_at, reverse=True)
        
        # Limit results
        experiments = experiments[:limit]
        
        # Format response
        experiment_list = []
        for experiment in experiments:
            hypothesis = next((h for h in autonomous_researcher.hypotheses 
                             if h.id == experiment.hypothesis_id), None)
            
            experiment_list.append({
                "id": experiment.id,
                "name": experiment.name,
                "hypothesis_title": hypothesis.title if hypothesis else "Unknown",
                "category": hypothesis.category if hypothesis else "Unknown",
                "status": experiment.status,
                "created_at": experiment.created_at.isoformat(),
                "sample_size": experiment.sample_size,
                "duration_hours": experiment.duration_hours
            })
        
        return {
            "experiments": experiment_list,
            "total_count": len(autonomous_researcher.experiments),
            "filtered_count": len(experiment_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hypotheses")
async def list_hypotheses(limit: int = 10, category: Optional[str] = None) -> Dict[str, Any]:
    """List hypotheses with optional filtering."""
    try:
        from nova.autonomous_research import autonomous_researcher
        
        hypotheses = autonomous_researcher.hypotheses
        
        # Filter by category if provided
        if category:
            hypotheses = [h for h in hypotheses if h.category == category]
        
        # Sort by priority (highest first), then by creation date (newest first)
        hypotheses.sort(key=lambda x: (x.priority, x.created_at), reverse=True)
        
        # Limit results
        hypotheses = hypotheses[:limit]
        
        # Format response
        hypothesis_list = []
        for hypothesis in hypotheses:
            hypothesis_list.append({
                "id": hypothesis.id,
                "title": hypothesis.title,
                "description": hypothesis.description,
                "category": hypothesis.category,
                "priority": hypothesis.priority,
                "confidence": hypothesis.confidence,
                "status": hypothesis.status,
                "created_at": hypothesis.created_at.isoformat()
            })
        
        return {
            "hypotheses": hypothesis_list,
            "total_count": len(autonomous_researcher.hypotheses),
            "filtered_count": len(hypothesis_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 