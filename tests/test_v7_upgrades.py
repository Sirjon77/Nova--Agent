"""
Tests for Nova Agent v7.0 Upgrades

This module tests the enhanced governance system, planning engine, and task scheduler
that were implemented as part of the v7.0 upgrade.
"""

import pytest
from datetime import datetime, timedelta

# Import the modules to test
from nova.governance.niche_manager import (
    NicheManager, ChannelMetrics, VelocityCalculator, ExternalContextAdjuster, PredictiveAnalytics
)
from nova.planner import (
    PlanningEngine, PlanningContext, DecisionType, ApprovalStatus,
    Decision
)
from nova.task_scheduler import (
    TaskScheduler, TaskExecutor, ScheduledTask, TaskStatus, TaskPriority
)

class TestEnhancedGovernance:
    """Test the enhanced governance system with dynamic weight tuning and predictive analytics."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'weights': {'rpm': 2.0, 'watch': 1.5, 'ctr': 1.0, 'subs': 1.0},
            'consistency_bonus': 5,
            'thresholds': {'retire': 25, 'watch': 40, 'promote': 65}
        }
        
        self.sample_metrics = [
            ChannelMetrics(
                channel_id="test_channel_1",
                rpm=8.5,
                avg_watch_minutes=4.2,
                ctr=0.045,
                subs_gained=150,
                rpm_history=[7.0, 7.5, 8.0, 8.2, 8.3, 8.4, 8.5],
                views=5000,
                engagement_rate=0.032,
                audience_retention=0.68,
                platform="youtube",
                niche="tech",
                created_date=datetime.now() - timedelta(days=30),
                last_updated=datetime.now(),
                external_context={
                    'market_conditions': 1.1,
                    'competition_level': 0.8
                }
            ),
            ChannelMetrics(
                channel_id="test_channel_2",
                rpm=6.2,
                avg_watch_minutes=3.8,
                ctr=0.038,
                subs_gained=120,
                rpm_history=[6.0, 6.1, 6.1, 6.2, 6.2, 6.2, 6.2],
                views=3200,
                engagement_rate=0.028,
                audience_retention=0.62,
                platform="tiktok",
                niche="entertainment",
                created_date=datetime.now() - timedelta(days=45),
                last_updated=datetime.now(),
                external_context={
                    'market_conditions': 0.9,
                    'competition_level': 1.2
                }
            )
        ]
    
    def test_velocity_calculator(self):
        """Test velocity calculation for trend analysis."""
        calculator = VelocityCalculator()
        
        # Test with increasing RPM trend
        metrics = self.sample_metrics[0]
        velocity = calculator.calculate_velocity_metrics(metrics)
        assert velocity > 0  # Should be positive for increasing trend
        
        # Test with flat RPM trend
        flat_metrics = ChannelMetrics(
            channel_id="flat_channel",
            rpm=5.0,
            avg_watch_minutes=3.0,
            ctr=0.04,
            subs_gained=100,
            rpm_history=[5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
            views=3000,
            engagement_rate=0.03,
            audience_retention=0.6,
            platform="youtube",
            niche="test",
            created_date=datetime.now(),
            last_updated=datetime.now()
        )
        velocity = calculator.calculate_velocity_metrics(flat_metrics)
        assert abs(velocity) < 0.01  # Should be close to zero for flat trend
    
    def test_external_context_adjuster(self):
        """Test external context adjustment based on market conditions."""
        adjuster = ExternalContextAdjuster()
        
        # Test holiday season adjustment
        holiday_metrics = ChannelMetrics(
            channel_id="holiday_channel",
            rpm=5.0,
            avg_watch_minutes=3.0,
            ctr=0.04,
            subs_gained=100,
            rpm_history=[5.0] * 7,
            views=3000,
            engagement_rate=0.03,
            audience_retention=0.6,
            platform="youtube",
            niche="test",
            created_date=datetime.now(),
            last_updated=datetime(2024, 12, 15)  # December
        )
        adjustment = adjuster.calculate_external_adjustment(holiday_metrics)
        assert adjustment > 1.0  # Should be boosted for holiday season
        
        # Test platform-specific adjustment
        tiktok_metrics = ChannelMetrics(
            channel_id="tiktok_channel",
            rpm=5.0,
            avg_watch_minutes=3.0,
            ctr=0.04,
            subs_gained=100,
            rpm_history=[5.0] * 7,
            views=3000,
            engagement_rate=0.03,
            audience_retention=0.6,
            platform="tiktok",
            niche="test",
            created_date=datetime.now(),
            last_updated=datetime.now()
        )
        adjustment = adjuster.calculate_external_adjustment(tiktok_metrics)
        assert adjustment > 1.0  # TikTok should get a boost
    
    def test_predictive_analytics(self):
        """Test predictive analytics for future performance forecasting."""
        predictor = PredictiveAnalytics()
        
        # Test with sufficient historical data
        metrics = self.sample_metrics[0]
        predictions = predictor.predict_channel_metrics(metrics)
        
        assert 'predicted_rpm' in predictions
        assert 'confidence_lower' in predictions
        assert 'confidence_upper' in predictions
        assert 'confidence' in predictions
        assert predictions['confidence'] >= 0.0
        assert predictions['confidence'] <= 1.0
        
        # Test with insufficient data
        short_metrics = ChannelMetrics(
            channel_id="short_channel",
            rpm=5.0,
            avg_watch_minutes=3.0,
            ctr=0.04,
            subs_gained=100,
            rpm_history=[5.0, 5.1],  # Only 2 data points
            views=3000,
            engagement_rate=0.03,
            audience_retention=0.6,
            platform="youtube",
            niche="test",
            created_date=datetime.now(),
            last_updated=datetime.now()
        )
        predictions = predictor.predict_channel_metrics(short_metrics)
        assert predictions['confidence'] == 0.5  # Default confidence for insufficient data
    
    def test_enhanced_niche_manager(self):
        """Test the enhanced niche manager with all new features."""
        manager = NicheManager(self.config)
        
        # Test scoring with enhanced features
        scored_channels = manager.score_channels(self.sample_metrics)
        
        assert len(scored_channels) == 2
        
        for scored in scored_channels:
            assert hasattr(scored, 'velocity_score')
            assert hasattr(scored, 'predicted_rpm')
            assert hasattr(scored, 'confidence_interval')
            assert hasattr(scored, 'external_adjustment')
            assert hasattr(scored, 'recommendation')
            assert hasattr(scored, 'risk_factors')
            
            assert isinstance(scored.velocity_score, float)
            assert isinstance(scored.predicted_rpm, float)
            assert isinstance(scored.confidence_interval, tuple)
            assert len(scored.confidence_interval) == 2
            assert isinstance(scored.external_adjustment, float)
            assert isinstance(scored.recommendation, str)
            assert isinstance(scored.risk_factors, list)

class TestPlanningEngine:
    """Test the AI Planning & Decision Engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.planning_engine = PlanningEngine()
        self.context = PlanningContext(
            current_metrics={'rpm': 8.5, 'views': 5000},
            historical_data={'avg_rpm': 7.2, 'growth_rate': 0.15},
            external_factors={'trend_score': 0.8, 'competition': 'medium'},
            constraints={'budget': 1000, 'time_limit': '7d'},
            goals={'target_rpm': 10.0, 'growth_target': 0.2}
        )
    
    @pytest.mark.asyncio
    async def test_strategic_plan_generation(self):
        """Test strategic plan generation."""
        goal = "Increase RPM by 20% within 30 days"
        
        plan = await self.planning_engine.generate_strategic_plan(self.context, goal)
        
        assert 'llm_plan' in plan
        assert 'rule_decisions' in plan
        assert 'recommended_actions' in plan
        assert 'automated_actions' in plan
        assert 'pending_approvals' in plan
        assert 'generated_at' in plan
        
        # Check LLM plan structure
        llm_plan = plan['llm_plan']
        assert 'analysis' in llm_plan
        assert 'strategies' in llm_plan
        assert 'recommended_actions' in llm_plan
        assert 'risks' in llm_plan
        assert 'success_metrics' in llm_plan
        assert 'confidence' in llm_plan
    
    def test_policy_engine_rules(self):
        """Test policy engine rule evaluation."""
        # Create a context that should trigger rules
        context = {
            'current_rpm': 3.0,  # Below threshold
            'trend_score': 0.9,  # High trend
            'channel_score': 20   # Below retirement threshold
        }
        
        decisions = self.planning_engine.policy_engine.evaluate_rules(context)
        
        # Should trigger at least the RPM drop alert rule
        assert len(decisions) > 0
        
        # Check that decisions have proper structure
        for decision in decisions:
            assert hasattr(decision, 'decision_id')
            assert hasattr(decision, 'decision_type')
            assert hasattr(decision, 'description')
            assert hasattr(decision, 'proposed_actions')
            assert hasattr(decision, 'approval_status')
    
    def test_decision_approval_flow(self):
        """Test decision approval and rejection flow."""
        # Create a test decision
        decision = Decision(
            decision_id="test_decision_1",
            decision_type=DecisionType.CHANNEL_INVESTMENT,
            description="Test decision",
            rationale="Testing approval flow",
            proposed_actions=[{"type": "test_action"}],
            expected_outcome="Test outcome",
            risk_assessment="Low risk",
            confidence_score=0.8,
            requires_approval=True,
            approval_status=ApprovalStatus.PENDING,
            created_at=datetime.now()
        )
        
        # Add to decision logger properly
        self.planning_engine.decision_logger.log_decision(decision)
        
        # Test approval
        success = self.planning_engine.approve_decision("test_decision_1", "test_user")
        assert success
        
        # Get the updated decision from the logger
        updated_decision = next((d for d in self.planning_engine.decision_logger.decisions 
                               if d.decision_id == "test_decision_1"), None)
        assert updated_decision is not None
        assert updated_decision.approval_status == ApprovalStatus.APPROVED
        assert updated_decision.approved_by == "test_user"
        
        # Test rejection
        success = self.planning_engine.reject_decision("test_decision_1", "test_user", "Test rejection")
        assert success
        
        # Get the updated decision again
        updated_decision = next((d for d in self.planning_engine.decision_logger.decisions 
                               if d.decision_id == "test_decision_1"), None)
        assert updated_decision is not None
        assert updated_decision.approval_status == ApprovalStatus.REJECTED
        assert updated_decision.outcome_metrics['rejection_reason'] == "Test rejection"

class TestTaskScheduler:
    """Test the task scheduler and executor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scheduler = TaskScheduler()
        self.executor = TaskExecutor()
    
    @pytest.mark.asyncio
    async def test_task_execution(self):
        """Test task execution with different action types."""
        # Test content creation task
        content_task = ScheduledTask(
            task_id="test_content_1",
            name="Create Test Content",
            description="Test content creation",
            action_type="create_content",
            parameters={"format": "video", "duration": "5min"},
            scheduled_time=datetime.now(),
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        result = await self.executor.execute_task(content_task)
        assert content_task.status == TaskStatus.COMPLETED
        assert 'content_id' in result
        assert 'status' in result
        
        # Test metrics analysis task
        analysis_task = ScheduledTask(
            task_id="test_analysis_1",
            name="Analyze Metrics",
            description="Test metrics analysis",
            action_type="analyze_metrics",
            parameters={"channels": ["test_channel"]},
            scheduled_time=datetime.now(),
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        result = await self.executor.execute_task(analysis_task)
        assert analysis_task.status == TaskStatus.COMPLETED
        assert 'analysis_id' in result
        assert 'insights' in result
    
    def test_task_scheduling(self):
        """Test task scheduling and management."""
        # Schedule a task
        task_id = self.scheduler.schedule_task(
            name="Test Task",
            description="A test task",
            action_type="analyze_metrics",
            parameters={"test": True},
            scheduled_time=datetime.now() + timedelta(minutes=5),
            priority=TaskPriority.HIGH
        )
        
        assert task_id is not None
        
        # Check pending tasks
        pending_tasks = self.scheduler.get_pending_tasks()
        assert len(pending_tasks) > 0
        
        # Get task status
        status = self.scheduler.get_task_status(task_id)
        assert status is not None
        assert status['name'] == "Test Task"
        
        # Cancel task
        success = self.scheduler.cancel_task(task_id)
        assert success
        
        # Verify task is cancelled
        status = self.scheduler.get_task_status(task_id)
        assert status['status'] == TaskStatus.CANCELLED
    
    def test_task_dependencies(self):
        """Test task dependency management."""
        # Schedule a task with dependencies
        task_id_1 = self.scheduler.schedule_task(
            name="Dependency Task",
            description="Task that others depend on",
            action_type="analyze_metrics",
            parameters={},
            scheduled_time=datetime.now(),
            priority=TaskPriority.MEDIUM
        )
        
        task_id_2 = self.scheduler.schedule_task(
            name="Dependent Task",
            description="Task that depends on another",
            action_type="create_content",
            parameters={},
            scheduled_time=datetime.now(),
            priority=TaskPriority.MEDIUM,
            dependencies=[task_id_1]
        )
        
        # Check that dependent task is not ready until dependency is met
        ready_tasks = [t for t in self.scheduler.scheduled_tasks 
                      if t.status == TaskStatus.PENDING and 
                      t.scheduled_time <= datetime.now() and
                      self.scheduler._dependencies_met(t)]
        
        # Should only include the first task, not the dependent one
        task_ids = [t.task_id for t in ready_tasks]
        assert task_id_1 in task_ids
        assert task_id_2 not in task_ids
    
    def test_schedule_from_plan(self):
        """Test scheduling tasks from a planning engine plan."""
        plan = {
            'recommended_actions': [
                {
                    'action': 'Create content for trending topic',
                    'timeline': 'immediate',
                    'priority': 'high',
                    'expected_impact': 'Capitalize on trend'
                }
            ],
            'automated_actions': [
                [
                    {
                        'type': 'send_alert',
                        'message': 'Trend detected',
                        'channel': 'slack'
                    }
                ]
            ]
        }
        
        task_ids = self.scheduler.schedule_from_plan(plan)
        assert len(task_ids) == 2  # One recommended + one automated
        
        # Verify tasks were created
        for task_id in task_ids:
            status = self.scheduler.get_task_status(task_id)
            assert status is not None

class TestIntegration:
    """Integration tests for the v7.0 system."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test a complete workflow from planning to execution."""
        # Create planning engine and scheduler
        planning_engine = PlanningEngine()
        scheduler = TaskScheduler()
        
        # Create planning context
        context = PlanningContext(
            current_metrics={'rpm': 6.0, 'views': 3000},
            historical_data={'avg_rpm': 5.5, 'growth_rate': 0.1},
            external_factors={'trend_score': 0.7, 'competition': 'low'},
            constraints={'budget': 500, 'time_limit': '14d'},
            goals={'target_rpm': 8.0, 'growth_target': 0.15}
        )
        
        # Generate strategic plan
        goal = "Improve channel performance by 25%"
        plan = await planning_engine.generate_strategic_plan(context, goal)
        
        # Schedule tasks from plan
        task_ids = scheduler.schedule_from_plan(plan)
        
        # Verify plan and tasks were created
        assert 'llm_plan' in plan
        assert len(task_ids) > 0
        
        # Check that tasks are properly scheduled
        pending_tasks = scheduler.get_pending_tasks()
        assert len(pending_tasks) >= len(task_ids)
        
        # Verify task details
        for task_id in task_ids:
            task_status = scheduler.get_task_status(task_id)
            assert task_status is not None
            assert task_status['status'] == TaskStatus.PENDING

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
