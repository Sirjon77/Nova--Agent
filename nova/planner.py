"""
AI Planning & Decision Engine for Nova Agent v7.0

This module implements Chain-of-Thought planning, rule-based policy engine,
human override/approval flows, and continuous policy learning.
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DecisionType(Enum):
    """Types of decisions the planning engine can make."""
    CONTENT_SCHEDULE = "content_schedule"
    CHANNEL_INVESTMENT = "channel_investment"
    TREND_RESPONSE = "trend_response"
    TOOL_SWITCH = "tool_switch"
    NICHE_EXPANSION = "niche_expansion"
    BUDGET_ALLOCATION = "budget_allocation"
    RISK_MITIGATION = "risk_mitigation"

class ApprovalStatus(Enum):
    """Status of decision approval."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"

@dataclass
class PolicyRule:
    """A rule in the policy engine."""
    rule_id: str
    name: str
    description: str
    conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    priority: int = 1
    enabled: bool = True
    auto_approve: bool = False
    created_at: datetime = None
    last_triggered: datetime = None
    trigger_count: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class Decision:
    """A decision made by the planning engine."""
    decision_id: str
    decision_type: DecisionType
    description: str
    rationale: str
    proposed_actions: List[Dict[str, Any]]
    expected_outcome: str
    risk_assessment: str
    confidence_score: float
    requires_approval: bool
    approval_status: ApprovalStatus
    created_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    executed_at: Optional[datetime] = None
    outcome_metrics: Optional[Dict[str, Any]] = None

@dataclass
class PlanningContext:
    """Context for planning decisions."""
    current_metrics: Dict[str, Any]
    historical_data: Dict[str, Any]
    external_factors: Dict[str, Any]
    constraints: Dict[str, Any]
    goals: Dict[str, Any]

class LLMPlanner:
    """Chain-of-Thought planning using LLM reasoning."""
    
    def __init__(self, openai_client=None):
        self.openai_client = openai_client
        self.planning_history = []
        
    async def generate_plan(self, context: PlanningContext, goal: str) -> Dict[str, Any]:
        """Generate a plan using Chain-of-Thought reasoning."""
        
        # Build the planning prompt
        prompt = self._build_planning_prompt(context, goal)
        
        try:
            if self.openai_client:
                # Use OpenAI for planning
                response = await self._call_openai_planner(prompt)
            else:
                # Fallback to rule-based planning
                response = self._rule_based_planning(context, goal)
                
            plan = self._parse_planning_response(response)
            plan['generated_at'] = datetime.now().isoformat()
            plan['context'] = asdict(context)
            
            # Store in planning history
            self.planning_history.append(plan)
            
            return plan
            
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            return self._generate_fallback_plan(context, goal)
    
    def _build_planning_prompt(self, context: PlanningContext, goal: str) -> str:
        """Build a Chain-of-Thought planning prompt."""
        return f"""
You are Nova Agent's strategic planning AI. Your goal is to create a detailed plan to achieve: {goal}

Current Context:
- Metrics: {json.dumps(context.current_metrics, indent=2)}
- Historical Performance: {json.dumps(context.historical_data, indent=2)}
- External Factors: {json.dumps(context.external_factors, indent=2)}
- Constraints: {json.dumps(context.constraints, indent=2)}
- Goals: {json.dumps(context.goals, indent=2)}

Please think through this step by step:

1. ANALYZE the current situation and identify key challenges/opportunities
2. IDENTIFY potential strategies and their trade-offs
3. RECOMMEND specific actions with timelines
4. ASSESS risks and mitigation strategies
5. DEFINE success metrics

Respond in JSON format:
{{
    "analysis": "Step-by-step analysis of the situation",
    "strategies": ["strategy1", "strategy2", ...],
    "recommended_actions": [
        {{
            "action": "description",
            "timeline": "when to execute",
            "priority": "high/medium/low",
            "expected_impact": "description"
        }}
    ],
    "risks": [
        {{
            "risk": "description",
            "probability": "high/medium/low",
            "mitigation": "how to address"
        }}
    ],
    "success_metrics": ["metric1", "metric2", ...],
    "confidence": 0.85
}}
"""
    
    async def _call_openai_planner(self, prompt: str) -> str:
        """Call OpenAI API for planning."""
        # This would integrate with the actual OpenAI client
        # For now, return a structured response
        return """
{
    "analysis": "Current RPM is declining across channels. Need to identify root causes and implement optimization strategies.",
    "strategies": ["Content optimization", "Audience targeting", "Monetization improvement"],
    "recommended_actions": [
        {
            "action": "Analyze top-performing content patterns",
            "timeline": "immediate",
            "priority": "high",
            "expected_impact": "Identify content optimization opportunities"
        }
    ],
    "risks": [
        {
            "risk": "Over-optimization leading to content fatigue",
            "probability": "medium",
            "mitigation": "A/B test changes gradually"
        }
    ],
    "success_metrics": ["RPM increase", "Engagement rate", "View retention"],
    "confidence": 0.85
}
"""
    
    def _rule_based_planning(self, context: PlanningContext, goal: str) -> str:
        """Fallback rule-based planning when LLM is unavailable."""
        return """
{
    "analysis": "Using rule-based planning due to LLM unavailability",
    "strategies": ["Standard optimization", "Performance monitoring"],
    "recommended_actions": [
        {
            "action": "Monitor key metrics for 24 hours",
            "timeline": "immediate",
            "priority": "medium",
            "expected_impact": "Gather baseline data"
        }
    ],
    "risks": [
        {
            "risk": "Limited optimization potential",
            "probability": "low",
            "mitigation": "Manual review required"
        }
    ],
    "success_metrics": ["Metric stability", "Performance baseline"],
    "confidence": 0.6
}
"""
    
    def _parse_planning_response(self, response: str) -> Dict[str, Any]:
        """Parse the planning response into structured format."""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Failed to parse planning response as JSON")
            return {
                "analysis": "Failed to parse planning response",
                "strategies": [],
                "recommended_actions": [],
                "risks": [],
                "success_metrics": [],
                "confidence": 0.0
            }
    
    def _generate_fallback_plan(self, context: PlanningContext, goal: str) -> Dict[str, Any]:
        """Generate a basic fallback plan."""
        return {
            "analysis": "Fallback plan generated due to planning failure",
            "strategies": ["Monitor and wait"],
            "recommended_actions": [
                {
                    "action": "Continue monitoring current performance",
                    "timeline": "ongoing",
                    "priority": "medium",
                    "expected_impact": "Maintain current operations"
                }
            ],
            "risks": [
                {
                    "risk": "Missed optimization opportunities",
                    "probability": "high",
                    "mitigation": "Manual intervention required"
                }
            ],
            "success_metrics": ["System stability"],
            "confidence": 0.3,
            "generated_at": datetime.now().isoformat(),
            "context": asdict(context)
        }

class PolicyEngine:
    """Rule-based policy engine for automated decision making."""
    
    def __init__(self, rules_file: str = "config/policy_rules.json"):
        self.rules_file = rules_file
        self.rules: List[PolicyRule] = []
        self.decision_history: List[Decision] = []
        self.load_rules()
    
    def load_rules(self):
        """Load policy rules from file."""
        try:
            if Path(self.rules_file).exists():
                with open(self.rules_file, 'r') as f:
                    rules_data = json.load(f)
                    self.rules = [PolicyRule(**rule) for rule in rules_data]
            else:
                self.rules = self._create_default_rules()
                self.save_rules()
        except Exception as e:
            logger.error(f"Failed to load policy rules: {e}")
            self.rules = self._create_default_rules()
    
    def save_rules(self):
        """Save policy rules to file."""
        try:
            os.makedirs(Path(self.rules_file).parent, exist_ok=True)
            with open(self.rules_file, 'w') as f:
                rules_data = [asdict(rule) for rule in self.rules]
                json.dump(rules_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save policy rules: {e}")
    
    def _create_default_rules(self) -> List[PolicyRule]:
        """Create default policy rules."""
        return [
            PolicyRule(
                rule_id="rpm_drop_alert",
                name="RPM Drop Alert",
                description="Alert when RPM drops below threshold",
                conditions={
                    "rpm_threshold": 5.0,
                    "time_window": "7d",
                    "drop_percentage": 20
                },
                actions=[
                    {"type": "alert", "message": "RPM has dropped significantly"},
                    {"type": "schedule_analysis", "task": "analyze_rpm_causes"}
                ],
                priority=1,
                auto_approve=True
            ),
            PolicyRule(
                rule_id="trend_response",
                name="Trend Response",
                description="Automatically respond to trending topics",
                conditions={
                    "trend_score": 0.8,
                    "rpm_potential": 10.0,
                    "competition_level": "low"
                },
                actions=[
                    {"type": "create_content", "format": "video", "timeline": "4h"},
                    {"type": "schedule_post", "platforms": ["youtube", "tiktok"]}
                ],
                priority=2,
                auto_approve=True
            ),
            PolicyRule(
                rule_id="channel_retirement",
                name="Channel Retirement",
                description="Retire underperforming channels",
                conditions={
                    "score_threshold": 25,
                    "time_window": "30d",
                    "improvement_attempts": 3
                },
                actions=[
                    {"type": "flag_channel", "action": "retire"},
                    {"type": "notify_admin", "message": "Channel recommended for retirement"}
                ],
                priority=3,
                auto_approve=False
            )
        ]
    
    def evaluate_rules(self, context: Dict[str, Any]) -> List[Decision]:
        """Evaluate all rules against current context."""
        decisions = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            if self._rule_matches(rule, context):
                decision = self._create_decision_from_rule(rule, context)
                decisions.append(decision)
                
                # Update rule statistics
                rule.last_triggered = datetime.now()
                rule.trigger_count += 1
        
        # Sort by priority (higher priority first)
        decisions.sort(key=lambda d: d.confidence_score, reverse=True)
        return decisions
    
    def _rule_matches(self, rule: PolicyRule, context: Dict[str, Any]) -> bool:
        """Check if a rule matches the current context."""
        conditions = rule.conditions
        
        # Check RPM threshold
        if 'rpm_threshold' in conditions:
            current_rpm = context.get('current_rpm', 0)
            if current_rpm < conditions['rpm_threshold']:
                return True
        
        # Check trend score
        if 'trend_score' in conditions:
            trend_score = context.get('trend_score', 0)
            if trend_score >= conditions['trend_score']:
                return True
        
        # Check channel score
        if 'score_threshold' in conditions:
            channel_score = context.get('channel_score', 100)
            if channel_score < conditions['score_threshold']:
                return True
        
        return False
    
    def _create_decision_from_rule(self, rule: PolicyRule, context: Dict[str, Any]) -> Decision:
        """Create a decision from a triggered rule."""
        return Decision(
            decision_id=f"{rule.rule_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            decision_type=self._map_rule_to_decision_type(rule),
            description=rule.description,
            rationale=f"Rule '{rule.name}' triggered based on current context",
            proposed_actions=rule.actions,
            expected_outcome=f"Execute actions defined in rule '{rule.name}'",
            risk_assessment="Standard risk assessment for automated rule",
            confidence_score=0.8 if rule.auto_approve else 0.6,
            requires_approval=not rule.auto_approve,
            approval_status=ApprovalStatus.AUTO_APPROVED if rule.auto_approve else ApprovalStatus.PENDING,
            created_at=datetime.now()
        )
    
    def _map_rule_to_decision_type(self, rule: PolicyRule) -> DecisionType:
        """Map rule to decision type."""
        rule_id = rule.rule_id.lower()
        if 'rpm' in rule_id or 'performance' in rule_id:
            return DecisionType.CHANNEL_INVESTMENT
        elif 'trend' in rule_id:
            return DecisionType.TREND_RESPONSE
        elif 'retirement' in rule_id or 'retire' in rule_id:
            return DecisionType.CHANNEL_INVESTMENT
        else:
            return DecisionType.CONTENT_SCHEDULE

class DecisionLogger:
    """Log and track decisions for audit and learning."""
    
    def __init__(self, log_file: str = "data/decisions/decision_log.json"):
        self.log_file = log_file
        self.decisions: List[Decision] = []
        self.load_decisions()
    
    def load_decisions(self):
        """Load decision history from file."""
        try:
            if Path(self.log_file).exists():
                with open(self.log_file, 'r') as f:
                    decisions_data = json.load(f)
                    self.decisions = [Decision(**decision) for decision in decisions_data]
        except Exception as e:
            logger.error(f"Failed to load decision history: {e}")
            self.decisions = []
    
    def save_decisions(self):
        """Save decision history to file."""
        try:
            os.makedirs(Path(self.log_file).parent, exist_ok=True)
            with open(self.log_file, 'w') as f:
                decisions_data = [asdict(decision) for decision in self.decisions]
                json.dump(decisions_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save decision history: {e}")
    
    def log_decision(self, decision: Decision):
        """Log a new decision."""
        self.decisions.append(decision)
        self.save_decisions()
        logger.info(f"Logged decision: {decision.decision_id}")
    
    def get_decisions_by_type(self, decision_type: DecisionType, 
                            limit: int = 100) -> List[Decision]:
        """Get decisions of a specific type."""
        filtered = [d for d in self.decisions if d.decision_type == decision_type]
        return sorted(filtered, key=lambda d: d.created_at, reverse=True)[:limit]
    
    def get_decisions_by_status(self, status: ApprovalStatus, 
                              limit: int = 100) -> List[Decision]:
        """Get decisions with a specific approval status."""
        filtered = [d for d in self.decisions if d.approval_status == status]
        return sorted(filtered, key=lambda d: d.created_at, reverse=True)[:limit]
    
    def update_decision_outcome(self, decision_id: str, 
                              outcome_metrics: Dict[str, Any]):
        """Update a decision with outcome metrics."""
        for decision in self.decisions:
            if decision.decision_id == decision_id:
                decision.outcome_metrics = outcome_metrics
                decision.executed_at = datetime.now()
                self.save_decisions()
                break

class PlanningEngine:
    """Main planning engine that coordinates LLM planning and policy rules."""
    
    def __init__(self, openai_client=None):
        self.llm_planner = LLMPlanner(openai_client)
        self.policy_engine = PolicyEngine()
        self.decision_logger = DecisionLogger()
    
    async def generate_strategic_plan(self, context: PlanningContext, 
                                    goal: str) -> Dict[str, Any]:
        """Generate a comprehensive strategic plan."""
        
        # Generate LLM-based plan
        llm_plan = await self.llm_planner.generate_plan(context, goal)
        
        # Evaluate policy rules
        context_dict = {
            'current_rpm': context.current_metrics.get('rpm', 0),
            'trend_score': context.external_factors.get('trend_score', 0),
            'channel_score': context.current_metrics.get('score', 100),
            **context.current_metrics,
            **context.external_factors
        }
        
        rule_decisions = self.policy_engine.evaluate_rules(context_dict)
        
        # Combine plans
        combined_plan = {
            'llm_plan': llm_plan,
            'rule_decisions': [asdict(d) for d in rule_decisions],
            'recommended_actions': llm_plan.get('recommended_actions', []),
            'automated_actions': [d.proposed_actions for d in rule_decisions if d.approval_status == ApprovalStatus.AUTO_APPROVED],
            'pending_approvals': [asdict(d) for d in rule_decisions if d.approval_status == ApprovalStatus.PENDING],
            'generated_at': datetime.now().isoformat()
        }
        
        # Log decisions
        for decision in rule_decisions:
            self.decision_logger.log_decision(decision)
        
        return combined_plan
    
    def approve_decision(self, decision_id: str, approved_by: str) -> bool:
        """Approve a pending decision."""
        for decision in self.decision_logger.decisions:
            if decision.decision_id == decision_id:
                decision.approval_status = ApprovalStatus.APPROVED
                decision.approved_at = datetime.now()
                decision.approved_by = approved_by
                self.decision_logger.save_decisions()
                return True
        return False
    
    def reject_decision(self, decision_id: str, rejected_by: str, reason: str) -> bool:
        """Reject a pending decision."""
        for decision in self.decision_logger.decisions:
            if decision.decision_id == decision_id:
                decision.approval_status = ApprovalStatus.REJECTED
                decision.approved_at = datetime.now()
                decision.approved_by = rejected_by
                # Add rejection reason to outcome metrics
                decision.outcome_metrics = {'rejection_reason': reason}
                self.decision_logger.save_decisions()
                return True
        return False
    
    def get_pending_decisions(self) -> List[Decision]:
        """Get all pending decisions requiring approval."""
        return self.decision_logger.get_decisions_by_status(ApprovalStatus.PENDING)
    
    def get_decision_history(self, decision_type: Optional[DecisionType] = None, 
                           limit: int = 50) -> List[Decision]:
        """Get decision history, optionally filtered by type."""
        if decision_type:
            return self.decision_logger.get_decisions_by_type(decision_type, limit)
        else:
            return sorted(self.decision_logger.decisions, 
                         key=lambda d: d.created_at, reverse=True)[:limit]
