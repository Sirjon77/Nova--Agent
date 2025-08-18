"""
Research Dashboard for Nova's Autonomous Research System

This module provides a comprehensive dashboard for monitoring and controlling
Nova's autonomous research activities, including:
- Real-time status of experiments and hypotheses
- Performance metrics and trends
- Research insights and recommendations
- Manual control over research cycles
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from nova.autonomous_research import autonomous_researcher

logger = logging.getLogger(__name__)

class ResearchDashboard:
    """
    Dashboard for monitoring and controlling autonomous research activities.
    """
    
    def __init__(self):
        self.researcher = autonomous_researcher
        
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        try:
            # Get basic status
            status = self.researcher.get_research_status()
            
            # Get recent activity
            recent_activity = self._get_recent_activity()
            
            # Get performance trends
            performance_trends = self._get_performance_trends()
            
            # Get top insights
            top_insights = self._get_top_insights()
            
            # Get upcoming experiments
            upcoming_experiments = self._get_upcoming_experiments()
            
            return {
                "status": status,
                "recent_activity": recent_activity,
                "performance_trends": performance_trends,
                "top_insights": top_insights,
                "upcoming_experiments": upcoming_experiments,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {"error": str(e)}
    
    def _get_recent_activity(self) -> List[Dict[str, Any]]:
        """Get recent research activity."""
        try:
            activities = []
            
            # Recent hypotheses
            recent_hypotheses = [h for h in self.researcher.hypotheses 
                               if (datetime.now() - h.created_at).days <= 7]
            
            for hypothesis in recent_hypotheses[-5:]:  # Last 5
                activities.append({
                    "type": "hypothesis_created",
                    "id": hypothesis.id,
                    "title": hypothesis.title,
                    "category": hypothesis.category,
                    "priority": hypothesis.priority,
                    "timestamp": hypothesis.created_at.isoformat(),
                    "status": hypothesis.status
                })
            
            # Recent experiments
            recent_experiments = [e for e in self.researcher.experiments 
                                if (datetime.now() - e.created_at).days <= 7]
            
            for experiment in recent_experiments[-5:]:  # Last 5
                activities.append({
                    "type": "experiment_created",
                    "id": experiment.id,
                    "name": experiment.name,
                    "hypothesis_id": experiment.hypothesis_id,
                    "timestamp": experiment.created_at.isoformat(),
                    "status": experiment.status
                })
            
            # Recent results
            recent_results = [r for r in self.researcher.results 
                            if (datetime.now() - r.completed_at).days <= 7]
            
            for result in recent_results[-5:]:  # Last 5
                activities.append({
                    "type": "experiment_completed",
                    "id": result.experiment_id,
                    "confidence": result.confidence,
                    "timestamp": result.completed_at.isoformat(),
                    "recommendation": result.recommendation[:100] + "..." if len(result.recommendation) > 100 else result.recommendation
                })
            
            # Sort by timestamp
            activities.sort(key=lambda x: x["timestamp"], reverse=True)
            return activities[:10]  # Return last 10 activities
            
        except Exception as e:
            logger.error(f"Failed to get recent activity: {e}")
            return []
    
    def _get_performance_trends(self) -> Dict[str, List[float]]:
        """Get performance trends over time."""
        try:
            # Group results by day
            daily_results = {}
            
            for result in self.researcher.results:
                date = result.completed_at.date().isoformat()
                if date not in daily_results:
                    daily_results[date] = []
                daily_results[date].append(result.confidence)
            
            # Calculate daily averages
            trends = {
                "dates": [],
                "confidence_scores": [],
                "improvement_rates": []
            }
            
            for date in sorted(daily_results.keys()):
                confidences = daily_results[date]
                trends["dates"].append(date)
                trends["confidence_scores"].append(sum(confidences) / len(confidences))
                
                # Calculate improvement rate (simplified)
                if len(trends["confidence_scores"]) > 1:
                    improvement = trends["confidence_scores"][-1] - trends["confidence_scores"][-2]
                    trends["improvement_rates"].append(improvement)
                else:
                    trends["improvement_rates"].append(0.0)
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to get performance trends: {e}")
            return {"dates": [], "confidence_scores": [], "improvement_rates": []}
    
    def _get_top_insights(self) -> List[Dict[str, Any]]:
        """Get top research insights."""
        try:
            insights = []
            
            # Most successful experiments
            successful_results = [r for r in self.researcher.results if r.confidence > 0.8]
            if successful_results:
                best_result = max(successful_results, key=lambda x: x.confidence)
                experiment = next((e for e in self.researcher.experiments if e.id == best_result.experiment_id), None)
                
                if experiment:
                    insights.append({
                        "type": "best_experiment",
                        "title": f"Best Performing Experiment: {experiment.name}",
                        "description": f"Confidence: {best_result.confidence:.2f}",
                        "recommendation": best_result.recommendation[:200] + "..." if len(best_result.recommendation) > 200 else best_result.recommendation,
                        "timestamp": best_result.completed_at.isoformat()
                    })
            
            # Most improved category
            category_improvements = {}
            for result in self.researcher.results:
                experiment = next((e for e in self.researcher.experiments if e.id == result.experiment_id), None)
                if experiment:
                    hypothesis = next((h for h in self.researcher.hypotheses if h.id == experiment.hypothesis_id), None)
                    if hypothesis:
                        category = hypothesis.category
                        if category not in category_improvements:
                            category_improvements[category] = []
                        category_improvements[category].extend(result.improvement_percentage.values())
            
            if category_improvements:
                best_category = max(category_improvements.items(), 
                                  key=lambda x: sum(x[1]) / len(x[1]) if x[1] else 0)
                avg_improvement = sum(best_category[1]) / len(best_category[1]) if best_category[1] else 0
                
                insights.append({
                    "type": "best_category",
                    "title": f"Most Improved Category: {best_category[0]}",
                    "description": f"Average improvement: {avg_improvement:.1f}%",
                    "recommendation": f"Focus research efforts on {best_category[0]} for maximum impact",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Recent breakthroughs
            recent_breakthroughs = [r for r in self.researcher.results 
                                  if r.confidence > 0.9 and (datetime.now() - r.completed_at).days <= 3]
            
            if recent_breakthroughs:
                breakthrough = recent_breakthroughs[0]
                experiment = next((e for e in self.researcher.experiments if e.id == breakthrough.experiment_id), None)
                
                if experiment:
                    insights.append({
                        "type": "breakthrough",
                        "title": f"Recent Breakthrough: {experiment.name}",
                        "description": f"Confidence: {breakthrough.confidence:.2f}",
                        "recommendation": "Consider implementing this improvement immediately",
                        "timestamp": breakthrough.completed_at.isoformat()
                    })
            
            return insights[:5]  # Return top 5 insights
            
        except Exception as e:
            logger.error(f"Failed to get top insights: {e}")
            return []
    
    def _get_upcoming_experiments(self) -> List[Dict[str, Any]]:
        """Get upcoming experiments."""
        try:
            upcoming = []
            
            # Pending experiments
            pending_experiments = [e for e in self.researcher.experiments if e.status == "pending"]
            
            for experiment in pending_experiments[:5]:  # Next 5
                hypothesis = next((h for h in self.researcher.hypotheses if h.id == experiment.hypothesis_id), None)
                
                upcoming.append({
                    "id": experiment.id,
                    "name": experiment.name,
                    "hypothesis_title": hypothesis.title if hypothesis else "Unknown",
                    "category": hypothesis.category if hypothesis else "Unknown",
                    "priority": hypothesis.priority if hypothesis else 1,
                    "sample_size": experiment.sample_size,
                    "duration_hours": experiment.duration_hours,
                    "created_at": experiment.created_at.isoformat()
                })
            
            return upcoming
            
        except Exception as e:
            logger.error(f"Failed to get upcoming experiments: {e}")
            return []
    
    async def start_research_cycle(self) -> Dict[str, Any]:
        """Manually start a research cycle."""
        try:
            logger.info("Starting manual research cycle")
            result = await self.researcher.run_research_cycle()
            
            # Update dashboard data
            dashboard_data = self.get_dashboard_data()
            
            return {
                "research_cycle_result": result,
                "updated_dashboard": dashboard_data,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Failed to start research cycle: {e}")
            return {"error": str(e), "status": "failed"}
    
    def get_experiment_details(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific experiment."""
        try:
            experiment = next((e for e in self.researcher.experiments if e.id == experiment_id), None)
            if not experiment:
                return None
            
            hypothesis = next((h for h in self.researcher.hypotheses if h.id == experiment.hypothesis_id), None)
            result = next((r for r in self.researcher.results if r.experiment_id == experiment_id), None)
            
            return {
                "experiment": {
                    "id": experiment.id,
                    "name": experiment.name,
                    "description": experiment.description,
                    "parameters": experiment.parameters,
                    "control_group": experiment.control_group,
                    "treatment_group": experiment.treatment_group,
                    "metrics": experiment.metrics,
                    "sample_size": experiment.sample_size,
                    "duration_hours": experiment.duration_hours,
                    "status": experiment.status,
                    "created_at": experiment.created_at.isoformat()
                },
                "hypothesis": {
                    "id": hypothesis.id if hypothesis else None,
                    "title": hypothesis.title if hypothesis else "Unknown",
                    "description": hypothesis.description if hypothesis else "Unknown",
                    "category": hypothesis.category if hypothesis else "Unknown",
                    "priority": hypothesis.priority if hypothesis else 1
                },
                "result": {
                    "control_metrics": result.control_metrics if result else {},
                    "treatment_metrics": result.treatment_metrics if result else {},
                    "statistical_significance": result.statistical_significance if result else {},
                    "improvement_percentage": result.improvement_percentage if result else {},
                    "recommendation": result.recommendation if result else "No results yet",
                    "confidence": result.confidence if result else 0.0,
                    "completed_at": result.completed_at.isoformat() if result else None
                } if result else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get experiment details: {e}")
            return None
    
    def get_hypothesis_details(self, hypothesis_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific hypothesis."""
        try:
            hypothesis = next((h for h in self.researcher.hypotheses if h.id == hypothesis_id), None)
            if not hypothesis:
                return None
            
            # Get related experiments
            related_experiments = [e for e in self.researcher.experiments if e.hypothesis_id == hypothesis_id]
            
            return {
                "hypothesis": {
                    "id": hypothesis.id,
                    "title": hypothesis.title,
                    "description": hypothesis.description,
                    "expected_improvement": hypothesis.expected_improvement,
                    "confidence": hypothesis.confidence,
                    "priority": hypothesis.priority,
                    "category": hypothesis.category,
                    "status": hypothesis.status,
                    "created_at": hypothesis.created_at.isoformat()
                },
                "related_experiments": [
                    {
                        "id": e.id,
                        "name": e.name,
                        "status": e.status,
                        "created_at": e.created_at.isoformat()
                    }
                    for e in related_experiments
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get hypothesis details: {e}")
            return None
    
    def get_research_summary(self) -> Dict[str, Any]:
        """Get a comprehensive research summary."""
        try:
            # Calculate success rates
            total_experiments = len(self.researcher.experiments)
            completed_experiments = len([e for e in self.researcher.experiments if e.status == "completed"])
            successful_experiments = len([r for r in self.researcher.results if r.confidence > 0.7])
            
            success_rate = (successful_experiments / completed_experiments * 100) if completed_experiments > 0 else 0
            
            # Calculate average improvements
            all_improvements = []
            for result in self.researcher.results:
                all_improvements.extend(result.improvement_percentage.values())
            
            avg_improvement = sum(all_improvements) / len(all_improvements) if all_improvements else 0
            
            # Get category breakdown
            category_counts = {}
            for hypothesis in self.researcher.hypotheses:
                category = hypothesis.category
                category_counts[category] = category_counts.get(category, 0) + 1
            
            return {
                "total_hypotheses": len(self.researcher.hypotheses),
                "total_experiments": total_experiments,
                "completed_experiments": completed_experiments,
                "successful_experiments": successful_experiments,
                "success_rate": success_rate,
                "average_improvement": avg_improvement,
                "category_breakdown": category_counts,
                "research_started": min([h.created_at for h in self.researcher.hypotheses]).isoformat() if self.researcher.hypotheses else None,
                "last_activity": max([r.completed_at for r in self.researcher.results]).isoformat() if self.researcher.results else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get research summary: {e}")
            return {"error": str(e)}

# Global dashboard instance
research_dashboard = ResearchDashboard()

def get_dashboard_data():
    """Convenience function to get dashboard data."""
    return research_dashboard.get_dashboard_data()

async def start_research_cycle():
    """Convenience function to start research cycle."""
    return await research_dashboard.start_research_cycle()

def get_research_summary():
    """Convenience function to get research summary."""
    return research_dashboard.get_research_summary() 