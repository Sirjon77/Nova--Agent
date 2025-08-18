"""
Autonomous Research System for Nova Agent

This module implements self-directed research capabilities that allow Nova to:
- Design and run experiments autonomously
- Analyze performance data and identify improvement opportunities
- Generate hypotheses and test them systematically
- Optimize its own architecture and parameters
- Conduct A/B testing on different approaches

Inspired by ASI-ARCH principles for autonomous AI research.
"""

import json
import time
import logging
import random
import statistics
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from utils.openai_wrapper import chat_completion
from utils.memory_manager import store_long, get_relevant_memories

logger = logging.getLogger(__name__)

@dataclass
class ResearchHypothesis:
    """A research hypothesis to be tested."""
    id: str
    title: str
    description: str
    expected_improvement: str
    confidence: float
    priority: int
    category: str
    created_at: datetime
    status: str = "pending"  # pending, running, completed, failed
    
@dataclass
class Experiment:
    """An experiment to test a hypothesis."""
    id: str
    hypothesis_id: str
    name: str
    description: str
    parameters: Dict[str, Any]
    control_group: Dict[str, Any]
    treatment_group: Dict[str, Any]
    metrics: List[str]
    sample_size: int
    duration_hours: int
    created_at: datetime
    status: str = "pending"  # pending, running, completed, failed
    
@dataclass
class ExperimentResult:
    """Results from an experiment."""
    experiment_id: str
    control_metrics: Dict[str, float]
    treatment_metrics: Dict[str, float]
    statistical_significance: Dict[str, float]
    improvement_percentage: Dict[str, float]
    recommendation: str
    confidence: float
    completed_at: datetime

class AutonomousResearcher:
    """
    Autonomous research system that can design and conduct experiments
    to improve Nova's performance without human intervention.
    """
    
    def __init__(self, research_dir: str = "data/autonomous_research"):
        self.research_dir = Path(research_dir)
        self.research_dir.mkdir(parents=True, exist_ok=True)
        
        self.hypotheses_file = self.research_dir / "hypotheses.json"
        self.experiments_file = self.research_dir / "experiments.json"
        self.results_file = self.research_dir / "results.json"
        
        self.hypotheses: List[ResearchHypothesis] = []
        self.experiments: List[Experiment] = []
        self.results: List[ExperimentResult] = []
        
        self._load_data()
        self.executor = ThreadPoolExecutor(max_workers=3)
        
    def _load_data(self):
        """Load existing research data from files."""
        try:
            if self.hypotheses_file.exists():
                with open(self.hypotheses_file, 'r') as f:
                    data = json.load(f)
                    self.hypotheses = [ResearchHypothesis(**h) for h in data]
                    
            if self.experiments_file.exists():
                with open(self.experiments_file, 'r') as f:
                    data = json.load(f)
                    self.experiments = [Experiment(**e) for e in data]
                    
            if self.results_file.exists():
                with open(self.results_file, 'r') as f:
                    data = json.load(f)
                    self.results = [ExperimentResult(**r) for r in data]
                    
        except Exception as e:
            logger.error(f"Failed to load research data: {e}")
            
    def _save_data(self):
        """Save research data to files."""
        try:
            with open(self.hypotheses_file, 'w') as f:
                json.dump([asdict(h) for h in self.hypotheses], f, indent=2, default=str)
                
            with open(self.experiments_file, 'w') as f:
                json.dump([asdict(e) for e in self.experiments], f, indent=2, default=str)
                
            with open(self.results_file, 'w') as f:
                json.dump([asdict(r) for r in self.results], f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to save research data: {e}")
    
    async def generate_hypotheses(self) -> List[ResearchHypothesis]:
        """
        Generate new research hypotheses based on current performance data
        and identified improvement opportunities.
        """
        try:
            # Analyze current performance and identify bottlenecks
            performance_analysis = await self._analyze_current_performance()
            
            # Get relevant memories for context
            memories = get_relevant_memories("performance", "recent", top_k=50)
            
            prompt = f"""
            Based on the following performance analysis and recent system behavior,
            generate 3-5 specific, testable hypotheses for improving Nova's performance.
            
            Performance Analysis:
            {json.dumps(performance_analysis, indent=2)}
            
            Recent System Behavior:
            {memories[:1000]}
            
            For each hypothesis, provide:
            1. A clear, specific title
            2. Detailed description of the proposed improvement
            3. Expected performance improvement (quantified if possible)
            4. Confidence level (0.0-1.0)
            5. Priority level (1-5, where 5 is highest)
            6. Category (nlp, memory, response_time, accuracy, user_satisfaction, etc.)
            
            Return as JSON array of hypothesis objects.
            """
            
            response = await chat_completion(prompt, temperature=0.7)
            
            try:
                hypotheses_data = json.loads(response)
                new_hypotheses = []
                
                for h_data in hypotheses_data:
                    hypothesis = ResearchHypothesis(
                        id=f"hyp_{int(time.time())}_{random.randint(1000, 9999)}",
                        title=h_data["title"],
                        description=h_data["description"],
                        expected_improvement=h_data["expected_improvement"],
                        confidence=float(h_data["confidence"]),
                        priority=int(h_data["priority"]),
                        category=h_data["category"],
                        created_at=datetime.now()
                    )
                    new_hypotheses.append(hypothesis)
                    
                self.hypotheses.extend(new_hypotheses)
                self._save_data()
                
                logger.info(f"Generated {len(new_hypotheses)} new hypotheses")
                return new_hypotheses
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse hypothesis response: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to generate hypotheses: {e}")
            return []
    
    async def design_experiment(self, hypothesis: ResearchHypothesis) -> Optional[Experiment]:
        """
        Design an experiment to test a specific hypothesis.
        """
        try:
            prompt = f"""
            Design a rigorous experiment to test the following hypothesis:
            
            Title: {hypothesis.title}
            Description: {hypothesis.description}
            Expected Improvement: {hypothesis.expected_improvement}
            Category: {hypothesis.category}
            
            Design an A/B test experiment that includes:
            1. Clear control and treatment groups
            2. Specific parameters to test
            3. Relevant metrics to measure
            4. Appropriate sample size
            5. Reasonable duration
            
            Return as JSON with the following structure:
            {{
                "name": "Experiment name",
                "description": "Detailed experiment description",
                "parameters": {{"param1": "value1"}},
                "control_group": {{"param1": "current_value"}},
                "treatment_group": {{"param1": "new_value"}},
                "metrics": ["metric1", "metric2"],
                "sample_size": 100,
                "duration_hours": 24
            }}
            """
            
            response = await chat_completion(prompt, temperature=0.3)
            
            try:
                exp_data = json.loads(response)
                
                experiment = Experiment(
                    id=f"exp_{int(time.time())}_{random.randint(1000, 9999)}",
                    hypothesis_id=hypothesis.id,
                    name=exp_data["name"],
                    description=exp_data["description"],
                    parameters=exp_data["parameters"],
                    control_group=exp_data["control_group"],
                    treatment_group=exp_data["treatment_group"],
                    metrics=exp_data["metrics"],
                    sample_size=exp_data["sample_size"],
                    duration_hours=exp_data["duration_hours"],
                    created_at=datetime.now()
                )
                
                self.experiments.append(experiment)
                self._save_data()
                
                logger.info(f"Designed experiment: {experiment.name}")
                return experiment
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse experiment design: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to design experiment: {e}")
            return None
    
    async def run_experiment(self, experiment: Experiment) -> Optional[ExperimentResult]:
        """
        Execute an experiment and collect results.
        """
        try:
            logger.info(f"Starting experiment: {experiment.name}")
            experiment.status = "running"
            self._save_data()
            
            # Collect baseline metrics (control group)
            control_metrics = await self._collect_metrics(experiment.control_group, experiment.sample_size)
            
            # Apply treatment and collect metrics
            treatment_metrics = await self._collect_metrics(experiment.treatment_group, experiment.sample_size)
            
            # Calculate statistical significance and improvements
            statistical_significance = self._calculate_significance(control_metrics, treatment_metrics)
            improvement_percentage = self._calculate_improvements(control_metrics, treatment_metrics)
            
            # Generate recommendation
            recommendation = await self._generate_recommendation(
                experiment, control_metrics, treatment_metrics, 
                statistical_significance, improvement_percentage
            )
            
            # Calculate overall confidence
            confidence = self._calculate_confidence(statistical_significance, improvement_percentage)
            
            result = ExperimentResult(
                experiment_id=experiment.id,
                control_metrics=control_metrics,
                treatment_metrics=treatment_metrics,
                statistical_significance=statistical_significance,
                improvement_percentage=improvement_percentage,
                recommendation=recommendation,
                confidence=confidence,
                completed_at=datetime.now()
            )
            
            experiment.status = "completed"
            self.results.append(result)
            self._save_data()
            
            logger.info(f"Completed experiment: {experiment.name} (confidence: {confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Failed to run experiment: {e}")
            experiment.status = "failed"
            self._save_data()
            return None
    
    async def _analyze_current_performance(self) -> Dict[str, Any]:
        """Analyze current system performance to identify improvement opportunities."""
        try:
            # Collect various performance metrics
            metrics = {
                "response_time": await self._measure_response_time(),
                "accuracy": await self._measure_accuracy(),
                "user_satisfaction": await self._measure_user_satisfaction(),
                "memory_efficiency": await self._measure_memory_efficiency(),
                "error_rate": await self._measure_error_rate(),
                "throughput": await self._measure_throughput()
            }
            
            # Identify bottlenecks and improvement opportunities
            bottlenecks = []
            for metric, value in metrics.items():
                if value < 0.7:  # Threshold for "good" performance
                    bottlenecks.append({
                        "metric": metric,
                        "current_value": value,
                        "target_value": 0.9,
                        "improvement_potential": 0.9 - value
                    })
            
            return {
                "current_metrics": metrics,
                "bottlenecks": bottlenecks,
                "overall_performance": statistics.mean(metrics.values()),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze performance: {e}")
            return {"error": str(e)}
    
    async def _collect_metrics(self, parameters: Dict[str, Any], sample_size: int) -> Dict[str, float]:
        """Collect metrics for a given parameter set."""
        try:
            metrics = {}
            
            # Simulate metric collection based on parameters
            for i in range(sample_size):
                # Simulate different metrics based on parameters
                if "nlp_confidence_threshold" in parameters:
                    threshold = parameters["nlp_confidence_threshold"]
                    accuracy = 0.8 + (threshold - 0.7) * 0.3  # Simulated relationship
                    response_time = 0.5 - (threshold - 0.7) * 0.2
                    
                    if "accuracy" not in metrics:
                        metrics["accuracy"] = []
                    if "response_time" not in metrics:
                        metrics["response_time"] = []
                        
                    metrics["accuracy"].append(accuracy + random.uniform(-0.1, 0.1))
                    metrics["response_time"].append(response_time + random.uniform(-0.1, 0.1))
                
                # Add other parameter-based metrics as needed
                
            # Calculate averages
            return {k: statistics.mean(v) for k, v in metrics.items()}
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            return {}
    
    def _calculate_significance(self, control: Dict[str, float], treatment: Dict[str, float]) -> Dict[str, float]:
        """Calculate statistical significance between control and treatment groups."""
        significance = {}
        
        for metric in control.keys():
            if metric in treatment:
                # Simplified t-test simulation
                control_val = control[metric]
                treatment_val = treatment[metric]
                
                # Calculate p-value (simplified)
                diff = abs(treatment_val - control_val)
                p_value = max(0.01, 1.0 - diff)  # Simplified p-value calculation
                
                significance[metric] = 1.0 - p_value  # Convert to significance level
                
        return significance
    
    def _calculate_improvements(self, control: Dict[str, float], treatment: Dict[str, float]) -> Dict[str, float]:
        """Calculate percentage improvements between control and treatment groups."""
        improvements = {}
        
        for metric in control.keys():
            if metric in treatment:
                control_val = control[metric]
                treatment_val = treatment[metric]
                
                if control_val != 0:
                    improvement = ((treatment_val - control_val) / control_val) * 100
                    improvements[metric] = improvement
                else:
                    improvements[metric] = 0.0
                    
        return improvements
    
    async def _generate_recommendation(self, experiment: Experiment, control: Dict[str, float], 
                                     treatment: Dict[str, float], significance: Dict[str, float], 
                                     improvements: Dict[str, float]) -> str:
        """Generate a recommendation based on experiment results."""
        try:
            prompt = f"""
            Based on the following experiment results, provide a clear recommendation:
            
            Experiment: {experiment.name}
            Description: {experiment.description}
            
            Control Group Metrics: {json.dumps(control, indent=2)}
            Treatment Group Metrics: {json.dumps(treatment, indent=2)}
            Statistical Significance: {json.dumps(significance, indent=2)}
            Improvements: {json.dumps(improvements, indent=2)}
            
            Provide a recommendation that includes:
            1. Whether to adopt the treatment (yes/no/maybe)
            2. Confidence level in the recommendation
            3. Key factors influencing the decision
            4. Any additional considerations or follow-up experiments needed
            
            Keep the recommendation concise but comprehensive.
            """
            
            response = await chat_completion(prompt, temperature=0.3)
            return response.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate recommendation: {e}")
            return "Unable to generate recommendation due to error."
    
    def _calculate_confidence(self, significance: Dict[str, float], improvements: Dict[str, float]) -> float:
        """Calculate overall confidence in the experiment results."""
        try:
            # Average significance across all metrics
            avg_significance = statistics.mean(significance.values()) if significance else 0.0
            
            # Consider improvement magnitude
            avg_improvement = statistics.mean([abs(v) for v in improvements.values()]) if improvements else 0.0
            
            # Normalize improvement to 0-1 scale (assuming 50% improvement is "high confidence")
            normalized_improvement = min(avg_improvement / 50.0, 1.0)
            
            # Combine factors (70% significance, 30% improvement magnitude)
            confidence = (0.7 * avg_significance) + (0.3 * normalized_improvement)
            
            return max(0.0, min(1.0, confidence))
            
        except Exception as e:
            logger.error(f"Failed to calculate confidence: {e}")
            return 0.0
    
    async def _measure_response_time(self) -> float:
        """Measure average response time."""
        # Simulate response time measurement
        return random.uniform(0.3, 0.8)
    
    async def _measure_accuracy(self) -> float:
        """Measure intent classification accuracy."""
        # Simulate accuracy measurement
        return random.uniform(0.75, 0.95)
    
    async def _measure_user_satisfaction(self) -> float:
        """Measure user satisfaction score."""
        # Simulate user satisfaction measurement
        return random.uniform(0.6, 0.9)
    
    async def _measure_memory_efficiency(self) -> float:
        """Measure memory usage efficiency."""
        # Simulate memory efficiency measurement
        return random.uniform(0.7, 0.95)
    
    async def _measure_error_rate(self) -> float:
        """Measure error rate (lower is better)."""
        # Simulate error rate measurement
        return random.uniform(0.05, 0.25)
    
    async def _measure_throughput(self) -> float:
        """Measure requests per second throughput."""
        # Simulate throughput measurement
        return random.uniform(0.8, 0.95)
    
    async def run_research_cycle(self) -> Dict[str, Any]:
        """
        Run a complete autonomous research cycle:
        1. Generate hypotheses
        2. Design experiments
        3. Run experiments
        4. Analyze results
        5. Make recommendations
        """
        try:
            logger.info("Starting autonomous research cycle")
            
            # Step 1: Generate new hypotheses
            new_hypotheses = await self.generate_hypotheses()
            
            # Step 2: Design experiments for high-priority hypotheses
            experiments_created = 0
            for hypothesis in new_hypotheses:
                if hypothesis.priority >= 4:  # High priority
                    experiment = await self.design_experiment(hypothesis)
                    if experiment:
                        experiments_created += 1
            
            # Step 3: Run pending experiments
            experiments_completed = 0
            for experiment in self.experiments:
                if experiment.status == "pending":
                    result = await self.run_experiment(experiment)
                    if result:
                        experiments_completed += 1
            
            # Step 4: Analyze results and generate insights
            insights = await self._generate_research_insights()
            
            # Step 5: Store research summary
            research_summary = {
                "cycle_timestamp": datetime.now().isoformat(),
                "hypotheses_generated": len(new_hypotheses),
                "experiments_created": experiments_created,
                "experiments_completed": experiments_completed,
                "total_hypotheses": len(self.hypotheses),
                "total_experiments": len(self.experiments),
                "total_results": len(self.results),
                "insights": insights
            }
            
            # Store in memory for future reference
            store_long("autonomous_research", "research_cycle", json.dumps(research_summary))
            
            logger.info(f"Completed research cycle: {experiments_completed} experiments completed")
            return research_summary
            
        except Exception as e:
            logger.error(f"Failed to run research cycle: {e}")
            return {"error": str(e)}
    
    async def _generate_research_insights(self) -> List[str]:
        """Generate insights from all research results."""
        try:
            if not self.results:
                return ["No research results available yet"]
            
            # Analyze recent results
            recent_results = [r for r in self.results 
                            if (datetime.now() - r.completed_at).days <= 7]
            
            if not recent_results:
                return ["No recent research results"]
            
            # Generate insights
            insights = []
            
            # Most successful experiments
            successful_results = [r for r in recent_results if r.confidence > 0.7]
            if successful_results:
                best_result = max(successful_results, key=lambda x: x.confidence)
                insights.append(f"Best performing experiment: {best_result.experiment_id} "
                              f"(confidence: {best_result.confidence:.2f})")
            
            # Areas with most improvement
            all_improvements = []
            for result in recent_results:
                all_improvements.extend(result.improvement_percentage.values())
            
            if all_improvements:
                avg_improvement = statistics.mean(all_improvements)
                insights.append(f"Average improvement across experiments: {avg_improvement:.1f}%")
            
            # Most tested categories
            experiment_categories = {}
            for experiment in self.experiments:
                for result in recent_results:
                    if result.experiment_id == experiment.id:
                        hypothesis = next((h for h in self.hypotheses if h.id == experiment.hypothesis_id), None)
                        if hypothesis:
                            category = hypothesis.category
                            experiment_categories[category] = experiment_categories.get(category, 0) + 1
            
            if experiment_categories:
                most_tested = max(experiment_categories.items(), key=lambda x: x[1])
                insights.append(f"Most researched category: {most_tested[0]} ({most_tested[1]} experiments)")
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            return ["Error generating insights"]
    
    def get_research_status(self) -> Dict[str, Any]:
        """Get current status of all research activities."""
        return {
            "total_hypotheses": len(self.hypotheses),
            "pending_hypotheses": len([h for h in self.hypotheses if h.status == "pending"]),
            "total_experiments": len(self.experiments),
            "pending_experiments": len([e for e in self.experiments if e.status == "pending"]),
            "running_experiments": len([e for e in self.experiments if e.status == "running"]),
            "completed_experiments": len([e for e in self.experiments if e.status == "completed"]),
            "total_results": len(self.results),
            "recent_results": len([r for r in self.results 
                                 if (datetime.now() - r.completed_at).days <= 7]),
            "research_directory": str(self.research_dir)
        }

# Global researcher instance
autonomous_researcher = AutonomousResearcher()

async def run_autonomous_research():
    """Convenience function to run autonomous research."""
    return await autonomous_researcher.run_research_cycle()

def get_research_status():
    """Convenience function to get research status."""
    return autonomous_researcher.get_research_status() 