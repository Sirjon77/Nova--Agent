
from dataclasses import dataclass
from statistics import mean, stdev
from typing import List, Union, Dict, Tuple
import numpy as np
from datetime import datetime
import json
import os

@dataclass
class ChannelMetrics:
    channel_id: str
    rpm: float
    avg_watch_minutes: float
    ctr: float
    subs_gained: int
    rpm_history: List[float]
    # New fields for v7.0 (defaults provided for backward compatibility)
    views: int = 0
    engagement_rate: float = 0.0
    audience_retention: float = 0.0
    platform: str = "unknown"
    niche: str = "general"
    created_date: datetime = None
    last_updated: datetime = None
    external_context: Dict[str, float] = None  # Market conditions, seasonality, etc.

    def __post_init__(self):
        # Ensure datetime defaults are set if not provided
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()

@dataclass
class ScoredChannel:
    channel_id: str
    score: float
    flag: Union[str, None]
    # New fields for v7.0
    velocity_score: float
    predicted_rpm: float
    confidence_interval: Tuple[float, float]
    external_adjustment: float
    recommendation: str
    risk_factors: List[str]

class ScoreWeightTuner:
    """Dynamic weight tuning using evolutionary algorithms and historical performance."""
    
    def __init__(self, learning_rate: float = 0.01, memory_size: int = 100):
        self.learning_rate = learning_rate
        self.memory_size = memory_size
        self.performance_history = []
        self.weight_history = []
        
    def tune_weights(self, current_weights: Dict[str, float], 
                    historical_performance: List[Dict[str, float]]) -> Dict[str, float]:
        """Tune weights based on historical performance correlation."""
        if len(historical_performance) < 10:
            return current_weights
            
        # Calculate correlation between weight changes and performance improvements
        correlations = {}
        for metric in ['rpm', 'watch', 'ctr', 'subs']:
            if metric in current_weights:
                # Simple correlation-based adjustment
                metric_performance = [p.get(metric, 0) for p in historical_performance]
                if len(metric_performance) > 1:
                    trend = np.polyfit(range(len(metric_performance)), metric_performance, 1)[0]
                    correlations[metric] = trend
                    
        # Adjust weights based on performance trends
        new_weights = current_weights.copy()
        for metric, correlation in correlations.items():
            if abs(correlation) > 0.1:  # Only adjust if there's a meaningful trend
                adjustment = self.learning_rate * correlation
                new_weights[metric] = max(0.1, min(5.0, new_weights[metric] + adjustment))
                
        return new_weights

class VelocityCalculator:
    """Calculate velocity metrics for trend analysis."""
    
    @staticmethod
    def calculate_velocity_metrics(metrics: ChannelMetrics) -> float:
        """Calculate velocity score based on recent performance trends."""
        if len(metrics.rpm_history) < 7:
            return 0.0
            
        # Calculate 7-day velocity
        recent_rpm = metrics.rpm_history[-7:]
        if len(recent_rpm) >= 7:
            # Linear regression slope as velocity indicator
            x = np.arange(len(recent_rpm))
            slope = np.polyfit(x, recent_rpm, 1)[0]
            
            # Normalize by current RPM to get relative velocity
            current_rpm = recent_rpm[-1]
            velocity = slope / (current_rpm + 0.1)  # Avoid division by zero
            
            return velocity
            
        return 0.0

class ExternalContextAdjuster:
    """Adjust scores based on external market conditions."""
    
    def __init__(self):
        self.seasonality_factors = {
            'holiday_season': 1.2,  # December
            'back_to_school': 1.1,  # August-September
            'summer_slowdown': 0.9,  # June-July
            'new_year': 1.15,       # January
        }
        
    def calculate_external_adjustment(self, metrics: ChannelMetrics) -> float:
        """Calculate external context adjustment factor."""
        adjustment = 1.0
        
        # Seasonality adjustment
        current_month = metrics.last_updated.month
        if current_month == 12:
            adjustment *= self.seasonality_factors['holiday_season']
        elif current_month in [8, 9]:
            adjustment *= self.seasonality_factors['back_to_school']
        elif current_month in [6, 7]:
            adjustment *= self.seasonality_factors['summer_slowdown']
        elif current_month == 1:
            adjustment *= self.seasonality_factors['new_year']
            
        # Platform-specific adjustments
        platform_adjustments = {
            'youtube': 1.0,
            'tiktok': 1.1,  # Higher growth potential
            'instagram': 0.95,
            'facebook': 0.9,
        }
        adjustment *= platform_adjustments.get(metrics.platform, 1.0)
        
        # External context from metrics (if available)
        if metrics.external_context:
            market_conditions = metrics.external_context.get('market_conditions', 1.0)
            competition_level = metrics.external_context.get('competition_level', 1.0)
            adjustment *= market_conditions * competition_level
            
        return adjustment

class PredictiveAnalytics:
    """Predict future channel performance using historical data."""
    
    def __init__(self, prediction_horizon: int = 30):
        self.prediction_horizon = prediction_horizon
        
    def predict_channel_metrics(self, metrics: ChannelMetrics) -> Dict[str, float]:
        """Predict future RPM and other metrics."""
        if len(metrics.rpm_history) < 14:  # Need at least 2 weeks of data
            return {
                'predicted_rpm': metrics.rpm,
                'confidence_lower': metrics.rpm * 0.8,
                'confidence_upper': metrics.rpm * 1.2,
                'confidence': 0.5
            }
            
        # Simple linear regression for prediction
        x = np.arange(len(metrics.rpm_history))
        y = np.array(metrics.rpm_history)
        
        # Fit polynomial regression (degree 2 for non-linear trends)
        coeffs = np.polyfit(x, y, 2)
        
        # Predict future value
        future_x = len(metrics.rpm_history) + self.prediction_horizon
        predicted_rpm = np.polyval(coeffs, future_x)
        
        # Calculate confidence interval using standard error
        y_pred = np.polyval(coeffs, x)
        residuals = y - y_pred
        std_error = np.std(residuals)
        
        confidence_interval = (
            max(0, predicted_rpm - 1.96 * std_error),
            predicted_rpm + 1.96 * std_error
        )
        
        # Calculate confidence based on R-squared
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return {
            'predicted_rpm': predicted_rpm,
            'confidence_lower': confidence_interval[0],
            'confidence_upper': confidence_interval[1],
            'confidence': r_squared
        }

class NicheManager:
    def __init__(self, cfg):
        self.cfg = cfg
        self.w_rpm   = cfg['weights']['rpm']
        self.w_watch = cfg['weights']['watch']
        self.w_ctr   = cfg['weights']['ctr']
        self.w_subs  = cfg['weights']['subs']
        self.consistency_bonus = cfg.get('consistency_bonus', 5)
        
        # New v7.0 components
        self.weight_tuner = ScoreWeightTuner()
        self.velocity_calculator = VelocityCalculator()
        self.external_adjuster = ExternalContextAdjuster()
        self.predictive_analytics = PredictiveAnalytics()
        
        # Load historical performance for weight tuning
        self.performance_history = self._load_performance_history()

    def _load_performance_history(self) -> List[Dict[str, float]]:
        """Load historical performance data for weight tuning."""
        history_file = "data/governance/performance_history.json"
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []

    def _save_performance_history(self, performance: Dict[str, float]):
        """Save performance data for future weight tuning."""
        os.makedirs("data/governance", exist_ok=True)
        history_file = "data/governance/performance_history.json"
        
        self.performance_history.append(performance)
        if len(self.performance_history) > 100:  # Keep last 100 entries
            self.performance_history = self.performance_history[-100:]
            
        try:
            with open(history_file, 'w') as f:
                json.dump(self.performance_history, f)
        except:
            pass

    def _z(self, x: float, population: List[float]) -> float:
        if len(population) < 2:
            return 0.0
        return (x - mean(population)) / (stdev(population) or 1)

    def _calculate_risk_factors(self, metrics: ChannelMetrics, score: float) -> List[str]:
        """Identify risk factors for the channel."""
        risk_factors = []
        
        # Low engagement risk
        if metrics.engagement_rate < 0.02:
            risk_factors.append("low_engagement")
            
        # Declining RPM risk
        if len(metrics.rpm_history) >= 7:
            recent_trend = np.polyfit(range(7), metrics.rpm_history[-7:], 1)[0]
            if recent_trend < -0.1:
                risk_factors.append("declining_rpm")
                
        # High competition risk (if external context available)
        if metrics.external_context and metrics.external_context.get('competition_level', 1.0) > 1.5:
            risk_factors.append("high_competition")
            
        # Platform saturation risk
        if metrics.platform in ['facebook', 'instagram'] and metrics.views < 1000:
            risk_factors.append("platform_saturation")
            
        return risk_factors

    def _generate_recommendation(self, metrics: ChannelMetrics, score: float, 
                               velocity: float, risk_factors: List[str]) -> str:
        """Generate actionable recommendation based on analysis."""
        if score < self.cfg['thresholds']['retire']:
            return "Consider retiring channel - low performance across all metrics"
        elif score < self.cfg['thresholds']['watch']:
            return "Monitor closely - implement optimization strategies"
        elif velocity > 0.1:
            return "Strong growth trajectory - consider increasing investment"
        elif velocity < -0.1:
            return "Declining performance - review content strategy"
        elif 'low_engagement' in risk_factors:
            return "Focus on engagement optimization - review content format"
        elif 'declining_rpm' in risk_factors:
            return "RPM declining - investigate monetization strategy"
        else:
            return "Stable performance - maintain current strategy"

    def score_channels(self, sample: List[ChannelMetrics]) -> List[ScoredChannel]:
        # Tune weights based on historical performance
        tuned_weights = self.weight_tuner.tune_weights({
            'rpm': self.w_rpm,
            'watch': self.w_watch,
            'ctr': self.w_ctr,
            'subs': self.w_subs
        }, self.performance_history)
        
        # Update weights
        self.w_rpm = tuned_weights['rpm']
        self.w_watch = tuned_weights['watch']
        self.w_ctr = tuned_weights['ctr']
        self.w_subs = tuned_weights['subs']
        
        rpms  = [c.rpm for c in sample]
        watch = [c.avg_watch_minutes for c in sample]
        ctrs  = [c.ctr for c in sample]
        subs  = [c.subs_gained for c in sample]
        
        scored = []
        for ch in sample:
            # Calculate base score
            s = (
                self.w_rpm   * self._z(ch.rpm, rpms) +
                self.w_watch * self._z(ch.avg_watch_minutes, watch) +
                self.w_ctr   * self._z(ch.ctr, ctrs) +
                self.w_subs  * self._z(ch.subs_gained, subs)
            )
            
            # Consistency bonus
            if len(ch.rpm_history) >= 7 and all(r > 0 for r in ch.rpm_history[-7:]):
                s += self.consistency_bonus
                
            # Calculate velocity metrics
            velocity = self.velocity_calculator.calculate_velocity_metrics(ch)
            
            # Calculate external context adjustment
            external_adjustment = self.external_adjuster.calculate_external_adjustment(ch)
            
            # Apply external adjustment
            s *= external_adjustment
            
            # Predict future metrics
            predictions = self.predictive_analytics.predict_channel_metrics(ch)
            
            # Calculate risk factors
            risk_factors = self._calculate_risk_factors(ch, s)
            
            # Generate recommendation
            recommendation = self._generate_recommendation(ch, s, velocity, risk_factors)
            
            # Determine flag
            flag = None
            if s < self.cfg['thresholds']['retire']:
                flag = 'retire'
            elif s < self.cfg['thresholds']['watch']:
                flag = 'watch'
            elif s > self.cfg['thresholds']['promote']:
                flag = 'promote'
                
            scored.append(ScoredChannel(
                channel_id=ch.channel_id,
                score=round(s, 2),
                flag=flag,
                velocity_score=round(velocity, 3),
                predicted_rpm=round(predictions['predicted_rpm'], 2),
                confidence_interval=(round(predictions['confidence_lower'], 2), 
                                   round(predictions['confidence_upper'], 2)),
                external_adjustment=round(external_adjustment, 3),
                recommendation=recommendation,
                risk_factors=risk_factors
            ))
            
        # Save performance data for future tuning
        avg_performance = {
            'rpm': mean(rpms),
            'watch': mean(watch),
            'ctr': mean(ctrs),
            'subs': mean(subs),
            'timestamp': datetime.now().isoformat()
        }
        self._save_performance_history(avg_performance)
        
        return scored
