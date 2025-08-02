"""
Governance Scheduler for Nova Agent

This module implements the nightly governance loop that performs:
- Niche scoring and evaluation
- Tool health checks
- Trend scanning and analysis
- System optimization recommendations
- Performance monitoring and alerts

Runs automatically on a schedule to ensure Nova maintains optimal performance.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import schedule

from utils.memory_manager import store_long, get_relevant_memories
from utils.openai_wrapper import chat_completion

logger = logging.getLogger(__name__)

class GovernanceScheduler:
    """
    Scheduler for Nova's governance and self-optimization tasks.
    """
    
    def __init__(self, config_path: str = "config/governance_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.last_run = None
        self.is_running = False
        
    def _load_config(self) -> Dict[str, Any]:
        """Load governance configuration."""
        default_config = {
            "enabled": True,
            "schedule": {
                "niche_scoring": "02:00",  # 2 AM
                "tool_health_check": "03:00",  # 3 AM
                "trend_scanning": "04:00",  # 4 AM
                "performance_analysis": "05:00",  # 5 AM
                "system_optimization": "06:00"  # 6 AM
            },
            "retention_days": 30,
            "alert_thresholds": {
                "performance_degradation": 0.1,
                "error_rate": 0.05,
                "memory_usage": 0.8
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.error(f"Failed to load governance config: {e}")
        
        return default_config
    
    def _save_config(self):
        """Save governance configuration."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save governance config: {e}")
    
    async def run_niche_scoring(self) -> Dict[str, Any]:
        """Run niche scoring and evaluation."""
        try:
            logger.info("Starting niche scoring cycle")
            
            # Get recent performance data
            recent_memories = get_relevant_memories("performance", "recent", limit=100)
            
            # Analyze niche performance
            prompt = f"""
            Analyze Nova's recent performance across different niches and content types.
            Based on the following performance data, score each niche and provide recommendations:
            
            Performance Data:
            {recent_memories[:2000]}
            
            Provide analysis in JSON format with:
            1. Niche scores (0-100)
            2. Performance trends
            3. Optimization recommendations
            4. Priority actions
            """
            
            response = await chat_completion(prompt, temperature=0.3)
            
            try:
                analysis = json.loads(response)
            except json.JSONDecodeError:
                analysis = {"error": "Failed to parse analysis", "raw_response": response}
            
            # Store results
            store_long("governance", "niche_scoring", json.dumps(analysis))
            
            logger.info("Niche scoring completed")
            return analysis
            
        except Exception as e:
            logger.error(f"Niche scoring failed: {e}")
            return {"error": str(e)}
    
    async def run_tool_health_check(self) -> Dict[str, Any]:
        """Check health of all integrated tools and APIs."""
        try:
            logger.info("Starting tool health check")
            
            health_status = {
                "timestamp": datetime.now().isoformat(),
                "tools": {},
                "overall_health": "healthy",
                "issues": []
            }
            
            # Check OpenAI API
            try:
                test_response = await chat_completion("Health check", temperature=0)
                health_status["tools"]["openai"] = {
                    "status": "healthy",
                    "response_time": "normal"
                }
            except Exception as e:
                health_status["tools"]["openai"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["issues"].append(f"OpenAI API: {str(e)}")
            
            # Check memory systems
            try:
                from memory import get_memory_status
                memory_status = get_memory_status()
                health_status["tools"]["memory"] = {
                    "status": "healthy" if memory_status["fully_available"] else "degraded",
                    "details": memory_status
                }
                if not memory_status["fully_available"]:
                    health_status["issues"].append("Memory system not fully available")
            except Exception as e:
                health_status["tools"]["memory"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["issues"].append(f"Memory system: {str(e)}")
            
            # Check external integrations
            integrations = [
                ("notion", "notion_sync"),
                ("sheets", "sheets_export"),
                ("metricool", "metricool_post"),
                ("convertkit", "convertkit_push"),
                ("gumroad", "gumroad_sync")
            ]
            
            for name, module in integrations:
                try:
                    __import__(module)
                    health_status["tools"][name] = {"status": "available"}
                except ImportError:
                    health_status["tools"][name] = {"status": "not_installed"}
                except Exception as e:
                    health_status["tools"][name] = {"status": "error", "error": str(e)}
                    health_status["issues"].append(f"{name}: {str(e)}")
            
            # Determine overall health
            if health_status["issues"]:
                health_status["overall_health"] = "degraded" if len(health_status["issues"]) < 3 else "unhealthy"
            
            # Store results
            store_long("governance", "tool_health", json.dumps(health_status))
            
            logger.info(f"Tool health check completed: {health_status['overall_health']}")
            return health_status
            
        except Exception as e:
            logger.error(f"Tool health check failed: {e}")
            return {"error": str(e)}
    
    async def run_trend_scanning(self) -> Dict[str, Any]:
        """Scan for trends and market changes."""
        try:
            logger.info("Starting trend scanning")
            
            # Get recent content and performance data
            recent_content = get_relevant_memories("content", "recent", limit=50)
            recent_performance = get_relevant_memories("performance", "recent", limit=50)
            
            # Analyze trends
            prompt = f"""
            Analyze recent content performance and identify emerging trends.
            Based on the following data, provide trend analysis:
            
            Recent Content:
            {recent_content[:1500]}
            
            Recent Performance:
            {recent_performance[:1500]}
            
            Provide analysis in JSON format with:
            1. Emerging trends
            2. Declining trends
            3. Content recommendations
            4. Platform opportunities
            5. Risk factors
            """
            
            response = await chat_completion(prompt, temperature=0.4)
            
            try:
                trends = json.loads(response)
            except json.JSONDecodeError:
                trends = {"error": "Failed to parse trends", "raw_response": response}
            
            # Store results
            store_long("governance", "trend_analysis", json.dumps(trends))
            
            logger.info("Trend scanning completed")
            return trends
            
        except Exception as e:
            logger.error(f"Trend scanning failed: {e}")
            return {"error": str(e)}
    
    async def run_performance_analysis(self) -> Dict[str, Any]:
        """Analyze system performance and identify optimization opportunities."""
        try:
            logger.info("Starting performance analysis")
            
            # Collect performance metrics
            metrics = {
                "response_time": await self._measure_response_time(),
                "accuracy": await self._measure_accuracy(),
                "user_satisfaction": await self._measure_user_satisfaction(),
                "memory_efficiency": await self._measure_memory_efficiency(),
                "error_rate": await self._measure_error_rate(),
                "throughput": await self._measure_throughput()
            }
            
            # Analyze performance trends
            recent_metrics = get_relevant_memories("metrics", "recent", limit=20)
            
            prompt = f"""
            Analyze Nova's performance metrics and identify optimization opportunities.
            
            Current Metrics:
            {json.dumps(metrics, indent=2)}
            
            Recent Metrics History:
            {recent_metrics[:1000]}
            
            Provide analysis in JSON format with:
            1. Performance trends
            2. Bottlenecks identified
            3. Optimization recommendations
            4. Priority improvements
            5. Risk assessments
            """
            
            response = await chat_completion(prompt, temperature=0.3)
            
            try:
                analysis = json.loads(response)
                analysis["current_metrics"] = metrics
            except json.JSONDecodeError:
                analysis = {
                    "error": "Failed to parse analysis",
                    "raw_response": response,
                    "current_metrics": metrics
                }
            
            # Store results
            store_long("governance", "performance_analysis", json.dumps(analysis))
            
            logger.info("Performance analysis completed")
            return analysis
            
        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return {"error": str(e)}
    
    async def run_system_optimization(self) -> Dict[str, Any]:
        """Generate system optimization recommendations."""
        try:
            logger.info("Starting system optimization")
            
            # Get recent governance data
            niche_data = get_relevant_memories("governance", "niche_scoring", limit=5)
            health_data = get_relevant_memories("governance", "tool_health", limit=5)
            trend_data = get_relevant_memories("governance", "trend_analysis", limit=5)
            performance_data = get_relevant_memories("governance", "performance_analysis", limit=5)
            
            # Generate optimization recommendations
            prompt = f"""
            Based on recent governance data, generate system optimization recommendations.
            
            Niche Scoring:
            {niche_data[:1000]}
            
            Tool Health:
            {health_data[:1000]}
            
            Trend Analysis:
            {trend_data[:1000]}
            
            Performance Analysis:
            {performance_data[:1000]}
            
            Provide comprehensive optimization plan in JSON format with:
            1. Immediate actions (next 24 hours)
            2. Short-term improvements (next week)
            3. Long-term optimizations (next month)
            4. Resource allocation recommendations
            5. Risk mitigation strategies
            6. Success metrics
            """
            
            response = await chat_completion(prompt, temperature=0.3)
            
            try:
                optimization = json.loads(response)
            except json.JSONDecodeError:
                optimization = {"error": "Failed to parse optimization", "raw_response": response}
            
            # Store results
            store_long("governance", "optimization_plan", json.dumps(optimization))
            
            logger.info("System optimization completed")
            return optimization
            
        except Exception as e:
            logger.error(f"System optimization failed: {e}")
            return {"error": str(e)}
    
    async def _measure_response_time(self) -> float:
        """Measure average response time."""
        # Simulate measurement
        return 0.65
    
    async def _measure_accuracy(self) -> float:
        """Measure intent classification accuracy."""
        # Simulate measurement
        return 0.85
    
    async def _measure_user_satisfaction(self) -> float:
        """Measure user satisfaction score."""
        # Simulate measurement
        return 0.78
    
    async def _measure_memory_efficiency(self) -> float:
        """Measure memory usage efficiency."""
        # Simulate measurement
        return 0.92
    
    async def _measure_error_rate(self) -> float:
        """Measure error rate."""
        # Simulate measurement
        return 0.12
    
    async def _measure_throughput(self) -> float:
        """Measure requests per second throughput."""
        # Simulate measurement
        return 0.88
    
    async def run_full_governance_cycle(self) -> Dict[str, Any]:
        """Run the complete governance cycle."""
        if self.is_running:
            logger.warning("Governance cycle already running")
            return {"error": "Already running"}
        
        self.is_running = True
        start_time = time.time()
        
        try:
            logger.info("Starting full governance cycle")
            
            results = {
                "cycle_start": datetime.now().isoformat(),
                "tasks": {}
            }
            
            # Run all governance tasks
            tasks = [
                ("niche_scoring", self.run_niche_scoring),
                ("tool_health_check", self.run_tool_health_check),
                ("trend_scanning", self.run_trend_scanning),
                ("performance_analysis", self.run_performance_analysis),
                ("system_optimization", self.run_system_optimization)
            ]
            
            for task_name, task_func in tasks:
                try:
                    logger.info(f"Running {task_name}")
                    task_result = await task_func()
                    results["tasks"][task_name] = {
                        "status": "completed",
                        "result": task_result
                    }
                except Exception as e:
                    logger.error(f"Task {task_name} failed: {e}")
                    results["tasks"][task_name] = {
                        "status": "failed",
                        "error": str(e)
                    }
            
            results["cycle_duration"] = time.time() - start_time
            results["cycle_end"] = datetime.now().isoformat()
            
            # Store cycle results
            store_long("governance", "cycle_results", json.dumps(results))
            
            self.last_run = datetime.now()
            logger.info(f"Governance cycle completed in {results['cycle_duration']:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Governance cycle failed: {e}")
            return {"error": str(e)}
        finally:
            self.is_running = False
    
    def schedule_governance_tasks(self):
        """Schedule governance tasks."""
        if not self.config.get("enabled", True):
            logger.info("Governance scheduler disabled")
            return
        
        schedule_config = self.config.get("schedule", {})
        
        # Schedule individual tasks
        for task_name, time_str in schedule_config.items():
            schedule.every().day.at(time_str).do(
                lambda t=task_name: asyncio.create_task(self._run_scheduled_task(t))
            )
            logger.info(f"Scheduled {task_name} at {time_str}")
        
        # Schedule full cycle as backup
        schedule.every().day.at("01:00").do(
            lambda: asyncio.create_task(self.run_full_governance_cycle())
        )
        logger.info("Scheduled full governance cycle at 01:00")
    
    async def _run_scheduled_task(self, task_name: str):
        """Run a scheduled governance task."""
        try:
            if task_name == "niche_scoring":
                await self.run_niche_scoring()
            elif task_name == "tool_health_check":
                await self.run_tool_health_check()
            elif task_name == "trend_scanning":
                await self.run_trend_scanning()
            elif task_name == "performance_analysis":
                await self.run_performance_analysis()
            elif task_name == "system_optimization":
                await self.run_system_optimization()
        except Exception as e:
            logger.error(f"Scheduled task {task_name} failed: {e}")
    
    def run_scheduler(self):
        """Run the scheduler loop."""
        logger.info("Starting governance scheduler")
        self.schedule_governance_tasks()
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Governance scheduler stopped")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)

# Global scheduler instance
governance_scheduler = GovernanceScheduler()

async def run_governance_cycle():
    """Convenience function to run governance cycle."""
    return await governance_scheduler.run_full_governance_cycle()

def start_governance_scheduler():
    """Start the governance scheduler."""
    governance_scheduler.run_scheduler() 