"""
Smart Household Resource Optimization Engine - Data Models
Comprehensive models for resource optimization.
Sustainability Analytics & Forecasting Engine - Data Models
Comprehensive models for analytics and forecasting.
Personal Sustainability Intelligence & Recommendation Platform - Data Models
Comprehensive models for intelligence and recommendations.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
import uuid
import json


class TrendType(Enum):
    """Types of trends."""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    VOLATILE = "volatile"
    CYCLICAL = "cyclical"
    EXPONENTIAL = "exponential"
    LOGARITHMIC = "logarithmic"
    S_CURVE = "s_curve"
    PLATEAU = "plateau"
    UNDEFINED = "undefined"


class ForecastModel(Enum):
    """Forecasting models."""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    ARIMA = "arima"
    MOVING_AVERAGE = "moving_average"
    HOLT_WINTERS = "holt_winters"
    NEURAL_NETWORK = "neural_network"
    ENSEMBLE = "ensemble"
    NAIVE = "naive"


class AnomalyType(Enum):
    """Types of anomalies."""
    SPIKE = "spike"  # Sudden increase
    DROP = "drop"  # Sudden decrease
    OUTLIER = "outlier"  # Unusual value
    TREND_CHANGE = "trend_change"  # Sudden trend change
    SEASONAL_SHIFT = "seasonal_shift"  # Seasonality change
    CYCLE_BREAK = "cycle_break"  # Cycle disruption
    INCONSISTENCY = "inconsistency"  # Inconsistent pattern


class ComparisonType(Enum):
    """Types of comparisons."""
    PERIOD_OVER_PERIOD = "period_over_period"
    CATEGORY_COMPARISON = "category_comparison"
    MEMBER_COMPARISON = "member_comparison"
    ACTUAL_VS_TARGET = "actual_vs_target"
    BENCHMARK_COMPARISON = "benchmark_comparison"
    YEAR_OVER_YEAR = "year_over_year"
    MONTH_OVER_MONTH = "month_over_month"


class AnalyticsPeriod(Enum):
    """Analytics time periods."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class DataGranularity(Enum):
    """Data granularity levels."""
    RAW = "raw"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ConfidenceLevel(Enum):
    """Confidence levels for forecasts."""
    HIGH = "high"  # 95%
    MEDIUM = "medium"  # 80%
    LOW = "low"  # 60%
    VERY_LOW = "very_low"  # 40%


class AnalyticsMetric(Enum):
    """Analytics metrics."""
    SUSTAINABILITY_SCORE = "sustainability_score"
    CARBON_FOOTPRINT = "carbon_footprint"
    ENERGY_CONSUMPTION = "energy_consumption"
    WATER_CONSUMPTION = "water_consumption"
    WASTE_GENERATION = "waste_generation"
    TRANSPORTATION_IMPACT = "transportation_impact"
    FOOD_IMPACT = "food_impact"
    SHOPPING_IMPACT = "shopping_impact"
    HOUSEHOLD_PERFORMANCE = "household_performance"
    GOAL_COMPLETION_RATE = "goal_completion_rate"
    HABIT_CONSISTENCY = "habit_consistency"
    RECYCLING_RATE = "recycling_rate"
    COMPOSTING_RATE = "composting_rate"


class AnalyticsCategory(Enum):
    """Analytics categories."""
    CARBON = "carbon"
    ENERGY = "energy"
    WATER = "water"
    WASTE = "waste"
    TRANSPORTATION = "transportation"
    FOOD = "food"
    SHOPPING = "shopping"
    HOUSEHOLD = "household"
    OVERALL = "overall"


@dataclass
class HistoricalData:
    """
    Represents historical sustainability data.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    household_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metric: AnalyticsMetric = AnalyticsMetric.SUSTAINABILITY_SCORE
    value: float = 0.0
    unit: str = ""
    category: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    is_verified: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'household_id': self.household_id,
            'timestamp': self.timestamp.isoformat(),
            'metric': self.metric.value,
            'value': self.value,
            'unit': self.unit,
            'category': self.category,
            'metadata': self.metadata,
            'source': self.source,
            'is_verified': self.is_verified
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HistoricalData':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            user_id=data.get('user_id', ''),
            household_id=data.get('household_id'),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else datetime.now(),
            metric=AnalyticsMetric(data.get('metric', 'sustainability_score')),
            value=data.get('value', 0.0),
            unit=data.get('unit', ''),
            category=data.get('category', ''),
            metadata=data.get('metadata', {}),
            source=data.get('source', ''),
            is_verified=data.get('is_verified', False)
        )


@dataclass
class TrendAnalysis:
    """
    Represents trend analysis results.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    metric: AnalyticsMetric = AnalyticsMetric.SUSTAINABILITY_SCORE
    period: AnalyticsPeriod = AnalyticsPeriod.MONTHLY
    start_date: datetime = field(default_factory=datetime.now)
    end_date: datetime = field(default_factory=datetime.now)
    
    # Trend data
    values: List[float] = field(default_factory=list)
    dates: List[str] = field(default_factory=list)
    granularity: DataGranularity = DataGranularity.DAILY
    
    # Trend statistics
    mean: float = 0.0
    median: float = 0.0
    variance: float = 0.0
    std_dev: float = 0.0
    min_value: float = 0.0
    max_value: float = 0.0
    
    # Trend direction
    trend_type: TrendType = TrendType.UNDEFINED
    slope: float = 0.0
    intercept: float = 0.0
    r_squared: float = 0.0
    p_value: float = 0.0
    
    # Seasonality
    has_seasonality: bool = False
    seasonality_period: int = 0
    seasonality_strength: float = 0.0
    
    # Change metrics
    absolute_change: float = 0.0
    percentage_change: float = 0.0
    daily_rate: float = 0.0
    monthly_rate: float = 0.0
    
    # Moving averages
    moving_average_7: List[float] = field(default_factory=list)
    moving_average_30: List[float] = field(default_factory=list)
    moving_average_90: List[float] = field(default_factory=list)
    
    # Metadata
    confidence: float = 0.0
    data_points: int = 0
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'metric': self.metric.value,
            'period': self.period.value,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'values': self.values,
            'dates': self.dates,
            'granularity': self.granularity.value,
            'mean': self.mean,
            'median': self.median,
            'variance': self.variance,
            'std_dev': self.std_dev,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'trend_type': self.trend_type.value,
            'slope': self.slope,
            'intercept': self.intercept,
            'r_squared': self.r_squared,
            'p_value': self.p_value,
            'has_seasonality': self.has_seasonality,
            'seasonality_period': self.seasonality_period,
            'seasonality_strength': self.seasonality_strength,
            'absolute_change': self.absolute_change,
            'percentage_change': self.percentage_change,
            'daily_rate': self.daily_rate,
            'monthly_rate': self.monthly_rate,
            'moving_average_7': self.moving_average_7,
            'moving_average_30': self.moving_average_30,
            'moving_average_90': self.moving_average_90,
            'confidence': self.confidence,
            'data_points': self.data_points,
            'notes': self.notes
        }


@dataclass
class ForecastResult:
    """
    Represents forecasting results.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    metric: AnalyticsMetric = AnalyticsMetric.SUSTAINABILITY_SCORE
    model: ForecastModel = ForecastModel.LINEAR
    forecast_date: datetime = field(default_factory=datetime.now)
    horizon_days: int = 30
    
    # Forecast values
    forecasts: List[Dict[str, Any]] = field(default_factory=list)
    projected_values: List[float] = field(default_factory=list)
    confidence_intervals: List[Tuple[float, float]] = field(default_factory=list)
    
    # Statistics
    mean_forecast: float = 0.0
    median_forecast: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    
    # Scenarios
    best_case: float = 0.0
    current_trend: float = 0.0
    worst_case: float = 0.0
    
    # Model performance
    model_accuracy: float = 0.0
    mape: float = 0.0  # Mean Absolute Percentage Error
    rmse: float = 0.0  # Root Mean Square Error
    
    # Metadata
    data_points_used: int = 0
    is_reliable: bool = False
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'metric': self.metric.value,
            'model': self.model.value,
            'forecast_date': self.forecast_date.isoformat(),
            'horizon_days': self.horizon_days,
            'forecasts': self.forecasts,
            'projected_values': self.projected_values,
            'confidence_intervals': [(l, u) for l, u in self.confidence_intervals],
            'mean_forecast': self.mean_forecast,
            'median_forecast': self.median_forecast,
            'confidence_level': self.confidence_level.value,
            'best_case': self.best_case,
            'current_trend': self.current_trend,
            'worst_case': self.worst_case,
            'model_accuracy': self.model_accuracy,
            'mape': self.mape,
            'rmse': self.rmse,
            'data_points_used': self.data_points_used,
            'is_reliable': self.is_reliable,
            'notes': self.notes
        }


@dataclass
class AnomalyDetection:
    """
    Represents anomaly detection results.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    metric: AnalyticsMetric = AnalyticsMetric.SUSTAINABILITY_SCORE
    detected_at: datetime = field(default_factory=datetime.now)
    anomaly_type: AnomalyType = AnomalyType.OUTLIER
    
    # Anomaly details
    value: float = 0.0
    expected_value: float = 0.0
    deviation: float = 0.0
    deviation_percentage: float = 0.0
    z_score: float = 0.0
    
    # Context
    context_value: float = 0.0
    context_range: Tuple[float, float] = (0.0, 0.0)
    
    # Explanation
    explanation: str = ""
    possible_causes: List[str] = field(default_factory=list)
    
    # Severity
    severity: str = ""  # low, medium, high, critical
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    # Metadata
    confidence: float = 0.0
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'metric': self.metric.value,
            'detected_at': self.detected_at.isoformat(),
            'anomaly_type': self.anomaly_type.value,
            'value': self.value,
            'expected_value': self.expected_value,
            'deviation': self.deviation,
            'deviation_percentage': self.deviation_percentage,
            'z_score': self.z_score,
            'context_value': self.context_value,
            'context_range': self.context_range,
            'explanation': self.explanation,
            'possible_causes': self.possible_causes,
            'severity': self.severity,
            'is_resolved': self.is_resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'confidence': self.confidence,
            'notes': self.notes
        }


@dataclass
class GoalTrajectory:
    """
    Represents goal trajectory analysis.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    goal_id: str = ""
    goal_name: str = ""
    category: str = ""
    
    # Goal details
    target_value: float = 0.0
    current_value: float = 0.0
    start_value: float = 0.0
    
    # Trajectory
    is_on_track: bool = False
    estimated_completion: Optional[datetime] = None
    days_remaining: int = 0
    
    # Progress
    progress_percentage: float = 0.0
    expected_progress: float = 0.0
    progress_gap: float = 0.0
    
    # Risk assessment
    risk_level: str = ""  # low, medium, high
    risk_factors: List[str] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    # History
    trajectory_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'goal_id': self.goal_id,
            'goal_name': self.goal_name,
            'category': self.category,
            'target_value': self.target_value,
            'current_value': self.current_value,
            'start_value': self.start_value,
            'is_on_track': self.is_on_track,
            'estimated_completion': self.estimated_completion.isoformat() if self.estimated_completion else None,
            'days_remaining': self.days_remaining,
            'progress_percentage': self.progress_percentage,
            'expected_progress': self.expected_progress,
            'progress_gap': self.progress_gap,
            'risk_level': self.risk_level,
            'risk_factors': self.risk_factors,
            'recommendations': self.recommendations,
            'trajectory_history': self.trajectory_history,
            'last_updated': self.last_updated.isoformat(),
            'notes': self.notes
        }


@dataclass
class ComparativeAnalysis:
    """
    Represents comparative analysis results.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    comparison_type: ComparisonType = ComparisonType.PERIOD_OVER_PERIOD
    metric: AnalyticsMetric = AnalyticsMetric.SUSTAINABILITY_SCORE
    
    # Comparison data
    current_period: Dict[str, Any] = field(default_factory=dict)
    previous_period: Dict[str, Any] = field(default_factory=dict)
    comparison_results: Dict[str, Any] = field(default_factory=dict)
    
    # Differences
    absolute_difference: float = 0.0
    percentage_difference: float = 0.0
    relative_performance: float = 0.0
    
    # Rankings
    rank: int = 0
    percentile: float = 0.0
    
    # Insights
    insights: List[str] = field(default_factory=list)
    
    # Metadata
    confidence: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
from typing import List, Optional, Dict, Any
import uuid
import json


class ResourceType(Enum):
    """Types of household resources."""


class RecommendationCategory(Enum):
    """Categories of recommendations."""
    ENERGY = "energy"
    WATER = "water"
    FOOD = "food"
    WASTE = "waste"
    TRANSPORTATION = "transportation"
    SHOPPING = "shopping"
    TRAVEL = "travel"
    OTHER = "other"


class RecommendationPriority(Enum):
    """Priority levels for optimization recommendations."""
    LIFESTYLE = "lifestyle"
    HABIT = "habit"
    GOAL = "goal"
    ROADMAP = "roadmap"
    OTHER = "other"


class RecommendationStatus(Enum):
    """Status of a recommendation."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SNOOZED = "snoozed"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CONFLICTING = "conflicting"


class RecommendationPriority(Enum):
    """Priority levels for recommendations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class OptimizationStatus(Enum):
    """Status of optimization plans."""
    DRAFT = "draft"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class OptimizationCategory(Enum):
    """Categories of optimization opportunities."""
    ENERGY_EFFICIENCY = "energy_efficiency"
    WATER_CONSERVATION = "water_conservation"
    WASTE_REDUCTION = "waste_reduction"
    FOOD_OPTIMIZATION = "food_optimization"
    TRANSPORTATION_OPTIMIZATION = "transportation_optimization"
    SHOPPING_OPTIMIZATION = "shopping_optimization"
    BEHAVIORAL_CHANGE = "behavioral_change"
    TECHNOLOGY_UPGRADE = "technology_upgrade"
    MAINTENANCE = "maintenance"
    OTHER = "other"


@dataclass
class HouseholdResource:
    """
    Represents a household resource with consumption data.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    resource_type: ResourceType = ResourceType.ENERGY
    name: str = ""
    description: str = ""
    
    # Consumption data
    current_usage: float = 0.0
    baseline_usage: float = 0.0
    unit: str = ""
    cost_per_unit: float = 0.0
    
    # Historical data
    historical_usage: List[Dict[str, Any]] = field(default_factory=list)
    monthly_averages: Dict[str, float] = field(default_factory=dict)
    yearly_averages: Dict[str, float] = field(default_factory=dict)
    
    # Efficiency metrics
    efficiency_score: float = 0.0  # 0-100
    efficiency_grade: str = ""  # A, B, C, D, F
    
    # Optimization potential
    optimization_potential: float = 0.0  # Percentage
    estimated_savings: float = 0.0
    estimated_impact: float = 0.0
    
    # Member contributions
    member_contributions: Dict[str, float] = field(default_factory=dict)  # member_id -> percentage
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'household_id': self.household_id,
            'resource_type': self.resource_type.value,
            'name': self.name,
            'description': self.description,
            'current_usage': self.current_usage,
            'baseline_usage': self.baseline_usage,
            'unit': self.unit,
            'cost_per_unit': self.cost_per_unit,
            'historical_usage': self.historical_usage,
            'monthly_averages': self.monthly_averages,
            'yearly_averages': self.yearly_averages,
            'efficiency_score': self.efficiency_score,
            'efficiency_grade': self.efficiency_grade,
            'optimization_potential': self.optimization_potential,
            'estimated_savings': self.estimated_savings,
            'estimated_impact': self.estimated_impact,
            'member_contributions': self.member_contributions,
            'last_updated': self.last_updated.isoformat(),
            'notes': self.notes,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HouseholdResource':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            household_id=data.get('household_id', ''),
            resource_type=ResourceType(data.get('resource_type', 'energy')),
            name=data.get('name', ''),
            description=data.get('description', ''),
            current_usage=data.get('current_usage', 0.0),
            baseline_usage=data.get('baseline_usage', 0.0),
            unit=data.get('unit', ''),
            cost_per_unit=data.get('cost_per_unit', 0.0),
            historical_usage=data.get('historical_usage', []),
            monthly_averages=data.get('monthly_averages', {}),
            yearly_averages=data.get('yearly_averages', {}),
            efficiency_score=data.get('efficiency_score', 0.0),
            efficiency_grade=data.get('efficiency_grade', ''),
            optimization_potential=data.get('optimization_potential', 0.0),
            estimated_savings=data.get('estimated_savings', 0.0),
            estimated_impact=data.get('estimated_impact', 0.0),
            member_contributions=data.get('member_contributions', {}),
            last_updated=datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else datetime.now(),
            notes=data.get('notes', ''),
            tags=data.get('tags', [])
        )
    
    def calculate_efficiency_score(self) -> float:
        """Calculate efficiency score based on usage vs baseline."""
        if self.baseline_usage == 0:
            return 50.0
        
        ratio = self.current_usage / self.baseline_usage
        if ratio <= 0.5:
            score = 90 + (1 - ratio) * 20
        elif ratio <= 0.8:
            score = 70 + (0.8 - ratio) * 66.67
        elif ratio <= 1.0:
            score = 50 + (1 - ratio) * 100
        elif ratio <= 1.2:
            score = 30 + (1.2 - ratio) * 100
        else:
            score = max(0, 30 - (ratio - 1.2) * 50)
        
        return min(100, max(0, score))
    
    def get_efficiency_grade(self) -> str:
        """Get efficiency grade based on score."""
        score = self.calculate_efficiency_score()
        if score >= 85:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 55:
            return "C"
        elif score >= 40:
            return "D"
        else:
            return "F"


@dataclass
class BaselineAnalysis:
    """
    Baseline analysis of household resource consumption.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    analysis_date: datetime = field(default_factory=datetime.now)
    period_days: int = 30
    
    # Consumption averages
    total_energy_kwh: float = 0.0
    total_water_liters: float = 0.0
    total_food_kg: float = 0.0
    total_waste_kg: float = 0.0
    total_transport_km: float = 0.0
    
    # Per capita averages
    per_capita_energy: float = 0.0
    per_capita_water: float = 0.0
    per_capita_food: float = 0.0
    per_capita_waste: float = 0.0
    per_capita_transport: float = 0.0
    
    # Efficiency scores
    energy_efficiency: float = 0.0
    water_efficiency: float = 0.0
    waste_efficiency: float = 0.0
    food_efficiency: float = 0.0
    transport_efficiency: float = 0.0
    overall_efficiency: float = 0.0
    
    # Category breakdown
    category_breakdown: Dict[str, float] = field(default_factory=dict)
    
    # Member breakdown
    member_breakdown: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Benchmarks
    benchmarks: Dict[str, float] = field(default_factory=dict)
    
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'household_id': self.household_id,
            'analysis_date': self.analysis_date.isoformat(),
            'period_days': self.period_days,
            'total_energy_kwh': self.total_energy_kwh,
            'total_water_liters': self.total_water_liters,
            'total_food_kg': self.total_food_kg,
            'total_waste_kg': self.total_waste_kg,
            'total_transport_km': self.total_transport_km,
            'per_capita_energy': self.per_capita_energy,
            'per_capita_water': self.per_capita_water,
            'per_capita_food': self.per_capita_food,
            'per_capita_waste': self.per_capita_waste,
            'per_capita_transport': self.per_capita_transport,
            'energy_efficiency': self.energy_efficiency,
            'water_efficiency': self.water_efficiency,
            'waste_efficiency': self.waste_efficiency,
            'food_efficiency': self.food_efficiency,
            'transport_efficiency': self.transport_efficiency,
            'overall_efficiency': self.overall_efficiency,
            'category_breakdown': self.category_breakdown,
            'member_breakdown': self.member_breakdown,
            'benchmarks': self.benchmarks,
            'notes': self.notes
        }


@dataclass
class EnergyOptimization:
    """
    Energy optimization analysis and recommendations.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    analysis_date: datetime = field(default_factory=datetime.now)
    
    # Consumption analysis
    total_consumption: float = 0.0
    baseline_consumption: float = 0.0
    consumption_difference: float = 0.0
    
    # High consumption detection
    high_consumption_areas: List[Dict[str, Any]] = field(default_factory=list)
    peak_usage_times: List[Dict[str, Any]] = field(default_factory=list)
    
    # Efficiency opportunities
    efficiency_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    reduction_scenarios: List[Dict[str, Any]] = field(default_factory=list)
    
    # Savings estimates
    estimated_energy_savings: float = 0.0  # kWh
    estimated_cost_savings: float = 0.0
    estimated_carbon_savings: float = 0.0
    
    # Recommendations
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    priority_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'household_id': self.household_id,
            'analysis_date': self.analysis_date.isoformat(),
            'total_consumption': self.total_consumption,
            'baseline_consumption': self.baseline_consumption,
            'consumption_difference': self.consumption_difference,
            'high_consumption_areas': self.high_consumption_areas,
            'peak_usage_times': self.peak_usage_times,
            'efficiency_opportunities': self.efficiency_opportunities,
            'reduction_scenarios': self.reduction_scenarios,
            'estimated_energy_savings': self.estimated_energy_savings,
            'estimated_cost_savings': self.estimated_cost_savings,
            'estimated_carbon_savings': self.estimated_carbon_savings,
            'recommendations': self.recommendations,
            'priority_recommendations': self.priority_recommendations,
            'notes': self.notes
        }


@dataclass
class WaterOptimization:
    """
    Water optimization analysis and recommendations.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    analysis_date: datetime = field(default_factory=datetime.now)
    
    # Usage analysis
    total_usage: float = 0.0
    baseline_usage: float = 0.0
    usage_difference: float = 0.0
    
    # High usage detection
    high_usage_areas: List[Dict[str, Any]] = field(default_factory=list)
    peak_usage_times: List[Dict[str, Any]] = field(default_factory=list)
    
    # Reduction opportunities
    reduction_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    efficiency_improvements: List[Dict[str, Any]] = field(default_factory=list)
    
    # Savings estimates
    estimated_water_savings: float = 0.0  # liters
    estimated_cost_savings: float = 0.0
    estimated_environmental_impact: float = 0.0
    
    # Recommendations
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    priority_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    


class FeedbackType(Enum):
    """Types of feedback."""
    ACCEPT = "accept"
    REJECT = "reject"
    SNOOZE = "snooze"
    COMPLETE = "complete"
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"


@dataclass
class UserPreference:
    """User preferences for recommendations."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    preferred_categories: List[str] = field(default_factory=list)
    excluded_categories: List[str] = field(default_factory=list)
    max_recommendations_per_day: int = 5
    notification_enabled: bool = True
    difficulty_preference: str = "medium"  # easy, medium, hard
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProfileStrength:
    """Strength area in sustainability profile."""
    category: str = ""
    score: float = 0.0
    description: str = ""
    evidence: List[str] = field(default_factory=list)


@dataclass
class ProfileWeakness:
    """Weakness area in sustainability profile."""
    category: str = ""
    score: float = 0.0
    description: str = ""
    improvement_potential: float = 0.0
    suggested_actions: List[str] = field(default_factory=list)


@dataclass
class SustainabilityProfile:
    """
    Unified sustainability profile for a user.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    household_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Overall scores
    overall_sustainability_score: float = 0.0
    overall_efficiency_score: float = 0.0
    
    # Category scores
    energy_score: float = 0.0
    water_score: float = 0.0
    food_score: float = 0.0
    waste_score: float = 0.0
    transport_score: float = 0.0
    shopping_score: float = 0.0
    
    # Strengths and weaknesses
    strengths: List[ProfileStrength] = field(default_factory=list)
    weaknesses: List[ProfileWeakness] = field(default_factory=list)
    
    # Preferences
    preferences: UserPreference = field(default_factory=UserPreference)
    
    # Goals and habits
    active_goals: List[str] = field(default_factory=list)
    completed_goals: List[str] = field(default_factory=list)
    active_habits: List[str] = field(default_factory=list)
    habit_consistency: float = 0.0
    
    # Roadmap progress
    roadmap_progress: float = 0.0
    roadmap_stage: int = 0
    
    # Benchmark data
    benchmark_comparison: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    last_analysis_date: Optional[datetime] = None
    profile_version: int = 1
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'household_id': self.household_id,
            'analysis_date': self.analysis_date.isoformat(),
            'total_usage': self.total_usage,
            'baseline_usage': self.baseline_usage,
            'usage_difference': self.usage_difference,
            'high_usage_areas': self.high_usage_areas,
            'peak_usage_times': self.peak_usage_times,
            'reduction_opportunities': self.reduction_opportunities,
            'efficiency_improvements': self.efficiency_improvements,
            'estimated_water_savings': self.estimated_water_savings,
            'estimated_cost_savings': self.estimated_cost_savings,
            'estimated_environmental_impact': self.estimated_environmental_impact,
            'recommendations': self.recommendations,
            'priority_recommendations': self.priority_recommendations,
            'user_id': self.user_id,
            'comparison_type': self.comparison_type.value,
            'metric': self.metric.value,
            'current_period': self.current_period,
            'previous_period': self.previous_period,
            'comparison_results': self.comparison_results,
            'absolute_difference': self.absolute_difference,
            'percentage_difference': self.percentage_difference,
            'relative_performance': self.relative_performance,
            'rank': self.rank,
            'percentile': self.percentile,
            'insights': self.insights,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat(),
            'household_id': self.household_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'overall_sustainability_score': self.overall_sustainability_score,
            'overall_efficiency_score': self.overall_efficiency_score,
            'energy_score': self.energy_score,
            'water_score': self.water_score,
            'food_score': self.food_score,
            'waste_score': self.waste_score,
            'transport_score': self.transport_score,
            'shopping_score': self.shopping_score,
            'strengths': [{'category': s.category, 'score': s.score, 'description': s.description} for s in self.strengths],
            'weaknesses': [{'category': w.category, 'score': w.score, 'description': w.description, 'improvement_potential': w.improvement_potential} for w in self.weaknesses],
            'preferences': self.preferences.__dict__,
            'active_goals': self.active_goals,
            'completed_goals': self.completed_goals,
            'active_habits': self.active_habits,
            'habit_consistency': self.habit_consistency,
            'roadmap_progress': self.roadmap_progress,
            'roadmap_stage': self.roadmap_stage,
            'benchmark_comparison': self.benchmark_comparison,
            'last_analysis_date': self.last_analysis_date.isoformat() if self.last_analysis_date else None,
            'profile_version': self.profile_version,
            'notes': self.notes
        }


@dataclass
class FoodWasteOptimization:
    """
    Food and waste optimization analysis.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    analysis_date: datetime = field(default_factory=datetime.now)
    
    # Food consumption
    total_food_consumption: float = 0.0
    food_waste_amount: float = 0.0
    food_waste_percentage: float = 0.0
    
    # Waste analysis
    total_waste: float = 0.0
    recyclable_waste: float = 0.0
    compostable_waste: float = 0.0
    landfill_waste: float = 0.0
    
    # Reduction opportunities
    food_waste_reduction_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    recycling_improvement_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    composting_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    
    # Savings estimates
    estimated_waste_reduction: float = 0.0
    estimated_cost_savings: float = 0.0
    estimated_environmental_impact: float = 0.0
    
    # Recommendations
    food_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    waste_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    
    notes: str = ""


@dataclass
class TransportationOptimization:
    """
    Transportation optimization analysis.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    analysis_date: datetime = field(default_factory=datetime.now)
    
    # Transportation analysis
    total_distance: float = 0.0
    primary_modes: List[Dict[str, Any]] = field(default_factory=list)
    carbon_emissions: float = 0.0
    
    # Optimization opportunities
    shared_transport_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    lower_impact_alternatives: List[Dict[str, Any]] = field(default_factory=list)
    
    # Comparison
    cost_comparison: Dict[str, float] = field(default_factory=dict)
    carbon_comparison: Dict[str, float] = field(default_factory=dict)
    
    # Savings estimates
    estimated_carbon_savings: float = 0.0
    estimated_cost_savings: float = 0.0
    
    # Recommendations
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    
    notes: str = ""


@dataclass
class CostImpactAnalysis:
    """
    Cost and impact analysis of household optimization.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    analysis_date: datetime = field(default_factory=datetime.now)
    
    # Current costs
    current_energy_cost: float = 0.0
    current_water_cost: float = 0.0
    current_food_cost: float = 0.0
    current_waste_cost: float = 0.0
    current_transport_cost: float = 0.0
    total_current_cost: float = 0.0
    
    # Potential savings
    potential_energy_savings: float = 0.0
    potential_water_savings: float = 0.0
    potential_food_savings: float = 0.0
    potential_waste_savings: float = 0.0
    potential_transport_savings: float = 0.0
    total_potential_savings: float = 0.0
    
    # Environmental impact
    current_carbon_footprint: float = 0.0
    potential_carbon_reduction: float = 0.0
    current_water_footprint: float = 0.0
    potential_water_reduction: float = 0.0
    
    # Return on effort
    roi_indicators: Dict[str, float] = field(default_factory=dict)
    effort_vs_impact: Dict[str, str] = field(default_factory=dict)  # high, medium, low
    
    notes: str = ""


@dataclass
class WhatIfScenario:
    """
    What-if scenario for optimization simulation.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    name: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    # Scenario parameters
    energy_reduction_percentage: float = 0.0
    water_reduction_percentage: float = 0.0
    waste_reduction_percentage: float = 0.0
    transport_shift_percentage: float = 0.0
    behavioral_changes: List[str] = field(default_factory=list)
    
    # Results
    projected_energy_savings: float = 0.0
    projected_water_savings: float = 0.0
    projected_waste_reduction: float = 0.0
    projected_cost_savings: float = 0.0
    projected_carbon_reduction: float = 0.0
    
    # Comparison to baseline
    improvement_percentage: float = 0.0
    efficiency_gain: float = 0.0
    
    notes: str = ""


@dataclass
class OptimizationPlan:
    """
    Comprehensive optimization plan for a household.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    name: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: OptimizationStatus = OptimizationStatus.DRAFT
    
    # Targets
    targets: List['OptimizationTarget'] = field(default_factory=list)
    deadlines: Dict[str, datetime] = field(default_factory=dict)
    
    # Actions
    actions: List[Dict[str, Any]] = field(default_factory=list)
    prioritized_actions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Progress
    overall_progress: float = 0.0
    completed_actions: int = 0
    total_actions: int = 0
    
    # Impact
    estimated_savings: float = 0.0
    estimated_impact: float = 0.0
    achieved_savings: float = 0.0
    
    # Timeline
    start_date: Optional[datetime] = None
    target_completion_date: Optional[datetime] = None
    actual_completion_date: Optional[datetime] = None
    
    notes: str = ""


@dataclass
class OptimizationTarget:
    """
    Target for optimization plan.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    plan_id: str = ""
    category: OptimizationCategory = OptimizationCategory.OTHER
    target_value: float = 0.0
    current_value: float = 0.0
    unit: str = ""
    deadline: Optional[datetime] = None
    achieved: bool = False
    achieved_date: Optional[datetime] = None
class CategoryAnalytics:
    """
    Represents category-specific analytics.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    category: AnalyticsCategory = AnalyticsCategory.OVERALL
    period: AnalyticsPeriod = AnalyticsPeriod.MONTHLY
    start_date: datetime = field(default_factory=datetime.now)
    end_date: datetime = field(default_factory=datetime.now)
    
    # Performance metrics
    current_score: float = 0.0
    previous_score: float = 0.0
    change: float = 0.0
    change_percentage: float = 0.0
    
    # Trend
    trend_type: TrendType = TrendType.UNDEFINED
    trend_slope: float = 0.0
    
    # Breakdown
    subcategory_scores: Dict[str, float] = field(default_factory=dict)
    subcategory_trends: Dict[str, float] = field(default_factory=dict)
    
    # Ranking
    rank_among_categories: int = 0
    percentile: float = 0.0
    
    # Insights
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    
    # Metadata
    confidence: float = 0.0
    data_points: int = 0
    notes: str = ""
class Recommendation:
    """
    Personalized sustainability recommendation.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    title: str = ""
    description: str = ""
    category: RecommendationCategory = RecommendationCategory.OTHER
    priority: RecommendationPriority = RecommendationPriority.MEDIUM
    status: RecommendationStatus = RecommendationStatus.PENDING
    
    # Scoring
    impact_score: float = 0.0  # Environmental impact (0-100)
    cost_estimate: float = 0.0
    savings_estimate: float = 0.0
    difficulty_score: float = 0.0  # 0-100 (higher = harder)
    effort_score: float = 0.0  # 0-100 (higher = more effort)
    benefit_score: float = 0.0  # 0-100
    relevance_score: float = 0.0  # 0-100
    overall_priority: float = 0.0  # 0-100
    
    # Context
    based_on_goals: List[str] = field(default_factory=list)
    based_on_habits: List[str] = field(default_factory=list)
    based_on_weakness: Optional[str] = None
    based_on_benchmark: Optional[str] = None
    based_on_roadmap: Optional[str] = None
    based_on_household: Optional[str] = None
    
    # Explanation
    explanation: str = ""
    why_matters: str = ""
    how_to_implement: str = ""
    resources: List[str] = field(default_factory=list)
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    snoozed_until: Optional[datetime] = None
    
    # Feedback
    feedback_history: List['RecommendationFeedback'] = field(default_factory=list)
    acceptance_count: int = 0
    completion_count: int = 0
    
    # Metadata
    is_duplicate: bool = False
    is_conflicting: bool = False
    conflicting_with: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'category': self.category.value,
            'target_value': self.target_value,
            'current_value': self.current_value,
            'unit': self.unit,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'achieved': self.achieved,
            'achieved_date': self.achieved_date.isoformat() if self.achieved_date else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OptimizationTarget':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            plan_id=data.get('plan_id', ''),
            category=OptimizationCategory(data.get('category', 'other')),
            target_value=data.get('target_value', 0.0),
            current_value=data.get('current_value', 0.0),
            unit=data.get('unit', ''),
            deadline=datetime.fromisoformat(data['deadline']) if data.get('deadline') else None,
            achieved=data.get('achieved', False),
            achieved_date=datetime.fromisoformat(data['achieved_date']) if data.get('achieved_date') else None
        )


@dataclass
class MemberContribution:
    """
    Member contribution analysis.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    member_id: str = ""
    member_name: str = ""
    analysis_date: datetime = field(default_factory=datetime.now)
    
    # Individual contributions
    individual_energy: float = 0.0
    individual_water: float = 0.0
    individual_food: float = 0.0
    individual_waste: float = 0.0
    individual_transport: float = 0.0
    
    # Shared contributions
    shared_energy: float = 0.0
    shared_water: float = 0.0
    shared_food: float = 0.0
    shared_waste: float = 0.0
    shared_transport: float = 0.0
    
    # Total contributions
    total_energy: float = 0.0
    total_water: float = 0.0
    total_food: float = 0.0
    total_waste: float = 0.0
    total_transport: float = 0.0
    
    # Category contributions
    category_contributions: Dict[str, float] = field(default_factory=dict)
    
    # Improvement opportunities
    improvement_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    
    # Household impact
    household_impact_percentage: float = 0.0
    
    notes: str = ""


@dataclass
class ResourceOptimization:
    """
    Complete resource optimization result.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    optimization_date: datetime = field(default_factory=datetime.now)
    
    # Analyses
    baseline: Optional[BaselineAnalysis] = None
    energy_optimization: Optional[EnergyOptimization] = None
    water_optimization: Optional[WaterOptimization] = None
    food_waste_optimization: Optional[FoodWasteOptimization] = None
    transportation_optimization: Optional[TransportationOptimization] = None
    cost_impact: Optional[CostImpactAnalysis] = None
    
    # Member analysis
    member_contributions: List[MemberContribution] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Summary
    summary: Dict[str, Any] = field(default_factory=dict)
    
    # Optimization plan
    optimization_plan: Optional[OptimizationPlan] = None
    
    notes: str = ""
            'user_id': self.user_id,
            'category': self.category.value,
            'period': self.period.value,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'current_score': self.current_score,
            'previous_score': self.previous_score,
            'change': self.change,
            'change_percentage': self.change_percentage,
            'trend_type': self.trend_type.value,
            'trend_slope': self.trend_slope,
            'subcategory_scores': self.subcategory_scores,
            'subcategory_trends': self.subcategory_trends,
            'rank_among_categories': self.rank_among_categories,
            'percentile': self.percentile,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'opportunities': self.opportunities,
            'confidence': self.confidence,
            'data_points': self.data_points,
            'notes': self.notes
        }


@dataclass
class HouseholdAnalytics:
    """
    Represents household-level analytics.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    period: AnalyticsPeriod = AnalyticsPeriod.MONTHLY
    start_date: datetime = field(default_factory=datetime.now)
    end_date: datetime = field(default_factory=datetime.now)
    
    # Overall metrics
    total_sustainability_score: float = 0.0
    average_sustainability_score: float = 0.0
    member_count: int = 0
    
    # Member breakdown
    member_scores: Dict[str, float] = field(default_factory=dict)
    member_rankings: List[Dict[str, Any]] = field(default_factory=list)
    
    # Category breakdown
    category_scores: Dict[str, float] = field(default_factory=dict)
    category_rankings: Dict[str, int] = field(default_factory=dict)
    
    # Trends
    household_trend: TrendType = TrendType.UNDEFINED
    member_trends: Dict[str, TrendType] = field(default_factory=dict)
    
    # Impact
    total_carbon_saved: float = 0.0
    total_water_saved: float = 0.0
    total_waste_reduced: float = 0.0
    
    # Insights
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Metadata
    confidence: float = 0.0
    data_points: int = 0
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'household_id': self.household_id,
            'period': self.period.value,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'total_sustainability_score': self.total_sustainability_score,
            'average_sustainability_score': self.average_sustainability_score,
            'member_count': self.member_count,
            'member_scores': self.member_scores,
            'member_rankings': self.member_rankings,
            'category_scores': self.category_scores,
            'category_rankings': self.category_rankings,
            'household_trend': self.household_trend.value,
            'member_trends': {k: v.value for k, v in self.member_trends.items()},
            'total_carbon_saved': self.total_carbon_saved,
            'total_water_saved': self.total_water_saved,
            'total_waste_reduced': self.total_waste_reduced,
            'insights': self.insights,
            'recommendations': self.recommendations,
            'confidence': self.confidence,
            'data_points': self.data_points,
            'notes': self.notes
            'title': self.title,
            'description': self.description,
            'category': self.category.value,
            'priority': self.priority.value,
            'status': self.status.value,
            'impact_score': self.impact_score,
            'cost_estimate': self.cost_estimate,
            'savings_estimate': self.savings_estimate,
            'difficulty_score': self.difficulty_score,
            'effort_score': self.effort_score,
            'benefit_score': self.benefit_score,
            'relevance_score': self.relevance_score,
            'overall_priority': self.overall_priority,
            'based_on_goals': self.based_on_goals,
            'based_on_habits': self.based_on_habits,
            'based_on_weakness': self.based_on_weakness,
            'based_on_benchmark': self.based_on_benchmark,
            'based_on_roadmap': self.based_on_roadmap,
            'based_on_household': self.based_on_household,
            'explanation': self.explanation,
            'why_matters': self.why_matters,
            'how_to_implement': self.how_to_implement,
            'resources': self.resources,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'snoozed_until': self.snoozed_until.isoformat() if self.snoozed_until else None,
            'acceptance_count': self.acceptance_count,
            'completion_count': self.completion_count,
            'is_duplicate': self.is_duplicate,
            'is_conflicting': self.is_conflicting,
            'conflicting_with': self.conflicting_with,
            'tags': self.tags,
            'version': self.version
        }


@dataclass
class AnalyticsReport:
    """
    Represents a comprehensive analytics report.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    household_id: Optional[str] = None
    report_type: str = ""  # historical, forecast, comparative, comprehensive
    period: str = ""
    generated_at: datetime = field(default_factory=datetime.now)
    
    # Executive summary
    summary: str = ""
    key_findings: List[str] = field(default_factory=list)
    
    # Trend analysis
    trend_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Forecasts
    forecasts: Dict[str, Any] = field(default_factory=dict)
    
    # Anomalies
    anomalies: List[Dict[str, Any]] = field(default_factory=list)
    
    # Trajectories
    trajectories: List[Dict[str, Any]] = field(default_factory=list)
    
    # Comparisons
    comparisons: List[Dict[str, Any]] = field(default_factory=list)
    
    # Insights
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Charts
    charts: Dict[str, str] = field(default_factory=dict)  # Chart ID to URL
    
    # Metadata
    content: str = ""
    file_path: str = ""
    shareable: bool = False
    notes: str = ""
class RecommendationFeedback:
    """
    Feedback for a recommendation.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    recommendation_id: str = ""
    user_id: str = ""
    feedback_type: FeedbackType = FeedbackType.ACCEPT
    timestamp: datetime = field(default_factory=datetime.now)
    notes: str = ""
    rating: Optional[int] = None  # 1-5
    actual_impact: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'household_id': self.household_id,
            'optimization_date': self.optimization_date.isoformat(),
            'baseline': self.baseline.to_dict() if self.baseline else None,
            'energy_optimization': self.energy_optimization.to_dict() if self.energy_optimization else None,
            'water_optimization': self.water_optimization.to_dict() if self.water_optimization else None,
            'food_waste_optimization': self.food_waste_optimization.to_dict() if self.food_waste_optimization else None,
            'transportation_optimization': self.transportation_optimization.to_dict() if self.transportation_optimization else None,
            'cost_impact': self.cost_impact.to_dict() if self.cost_impact else None,
            'member_contributions': [m.to_dict() for m in self.member_contributions],
            'recommendations': self.recommendations,
            'summary': self.summary,
            'optimization_plan': self.optimization_plan.to_dict() if self.optimization_plan else None,
            'notes': self.notes
        }


@dataclass
class EfficiencyScore:
    """
    Efficiency score for household or category.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    category: str = ""
    score: float = 0.0
    grade: str = ""
    benchmark: float = 0.0
    percentile: float = 0.0
    improvement_potential: float = 0.0
    calculated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'household_id': self.household_id,
            'category': self.category,
            'score': self.score,
            'grade': self.grade,
            'benchmark': self.benchmark,
            'percentile': self.percentile,
            'improvement_potential': self.improvement_potential,
            'calculated_at': self.calculated_at.isoformat()
        }


@dataclass
class HouseholdEfficiency:
    """
    Overall household efficiency.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    overall_score: float = 0.0
    overall_grade: str = ""
    
    # Category scores
    energy_score: float = 0.0
    water_score: float = 0.0
    waste_score: float = 0.0
    food_score: float = 0.0
    transport_score: float = 0.0
    shopping_score: float = 0.0
    
    # Rankings
    category_rankings: Dict[str, int] = field(default_factory=dict)
    
    # Improvement
    improvement_potential: float = 0.0
    recommended_actions: List[str] = field(default_factory=list)
    
    calculated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'household_id': self.household_id,
            'overall_score': self.overall_score,
            'overall_grade': self.overall_grade,
            'energy_score': self.energy_score,
            'water_score': self.water_score,
            'waste_score': self.waste_score,
            'food_score': self.food_score,
            'transport_score': self.transport_score,
            'shopping_score': self.shopping_score,
            'category_rankings': self.category_rankings,
            'improvement_potential': self.improvement_potential,
            'recommended_actions': self.recommended_actions,
            'calculated_at': self.calculated_at.isoformat()
            'user_id': self.user_id,
            'household_id': self.household_id,
            'report_type': self.report_type,
            'period': self.period,
            'generated_at': self.generated_at.isoformat(),
            'summary': self.summary,
            'key_findings': self.key_findings,
            'trend_analysis': self.trend_analysis,
            'forecasts': self.forecasts,
            'anomalies': self.anomalies,
            'trajectories': self.trajectories,
            'comparisons': self.comparisons,
            'insights': self.insights,
            'recommendations': self.recommendations,
            'charts': self.charts,
            'content': self.content,
            'file_path': self.file_path,
            'shareable': self.shareable,
            'notes': self.notes
            'recommendation_id': self.recommendation_id,
            'user_id': self.user_id,
            'feedback_type': self.feedback_type.value,
            'timestamp': self.timestamp.isoformat(),
            'notes': self.notes,
            'rating': self.rating,
            'actual_impact': self.actual_impact
        }


@dataclass
class OptimizationProgress:
    """
    Progress tracking for optimization plans.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    plan_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Progress metrics
    overall_progress: float = 0.0
    completed_actions: int = 0
    total_actions: int = 0
    achieved_targets: int = 0
    total_targets: int = 0
    
    # Savings achieved
    achieved_energy_savings: float = 0.0
    achieved_water_savings: float = 0.0
    achieved_waste_reduction: float = 0.0
    achieved_cost_savings: float = 0.0
    
    # Status
    on_track: bool = True
    issues_detected: List[str] = field(default_factory=list)
    
    notes: str = ""
class AnalyticsInsight:
    """
    Represents an analytics insight.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    insight_type: str = ""  # trend, anomaly, opportunity, risk, achievement
    title: str = ""
    description: str = ""
    category: str = ""
    
    # Supporting data
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    
    # Action
    recommended_action: str = ""
    priority: str = ""  # high, medium, low
    
    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_actioned: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'timestamp': self.timestamp.isoformat(),
            'overall_progress': self.overall_progress,
            'completed_actions': self.completed_actions,
            'total_actions': self.total_actions,
            'achieved_targets': self.achieved_targets,
            'total_targets': self.total_targets,
            'achieved_energy_savings': self.achieved_energy_savings,
            'achieved_water_savings': self.achieved_water_savings,
            'achieved_waste_reduction': self.achieved_waste_reduction,
            'achieved_cost_savings': self.achieved_cost_savings,
            'on_track': self.on_track,
            'issues_detected': self.issues_detected,
            'notes': self.notes
            'user_id': self.user_id,
            'insight_type': self.insight_type,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'supporting_data': self.supporting_data,
            'confidence': self.confidence,
            'recommended_action': self.recommended_action,
            'priority': self.priority,
            'generated_at': self.generated_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_actioned': self.is_actioned
        }


@dataclass
class AnalyticsSummary:
    """
    Comprehensive analytics summary.
    """
    user_id: str = ""
    period: AnalyticsPeriod = AnalyticsPeriod.MONTHLY
    generated_at: datetime = field(default_factory=datetime.now)
    
    # Overall metrics
    current_sustainability_score: float = 0.0
    previous_sustainability_score: float = 0.0
    score_change: float = 0.0
    score_change_percentage: float = 0.0
    
    # Category summaries
    category_summaries: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Trend summary
    overall_trend: TrendType = TrendType.UNDEFINED
    improving_categories: List[str] = field(default_factory=list)
    declining_categories: List[str] = field(default_factory=list)
    stable_categories: List[str] = field(default_factory=list)
    
    # Impact summary
    total_carbon_saved: float = 0.0
    total_water_saved: float = 0.0
    total_waste_reduced: float = 0.0
    
    # Key metrics
    best_performing_category: str = ""
    worst_performing_category: str = ""
    fastest_improving_category: str = ""
    most_declining_category: str = ""
    
    # Goals
    goals_on_track: int = 0
    goals_at_risk: int = 0
    goals_completed: int = 0
    
    # Forecast
    forecast_30_day: float = 0.0
    forecast_30_day_confidence: float = 0.0
    
    # Anomalies
    anomaly_count: int = 0
    unresolved_anomalies: int = 0
    
    # Insights
    top_insights: List[str] = field(default_factory=list)
    top_recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'period': self.period.value,
            'generated_at': self.generated_at.isoformat(),
            'current_sustainability_score': self.current_sustainability_score,
            'previous_sustainability_score': self.previous_sustainability_score,
            'score_change': self.score_change,
            'score_change_percentage': self.score_change_percentage,
            'category_summaries': self.category_summaries,
            'overall_trend': self.overall_trend.value,
            'improving_categories': self.improving_categories,
            'declining_categories': self.declining_categories,
            'stable_categories': self.stable_categories,
            'total_carbon_saved': self.total_carbon_saved,
            'total_water_saved': self.total_water_saved,
            'total_waste_reduced': self.total_waste_reduced,
            'best_performing_category': self.best_performing_category,
            'worst_performing_category': self.worst_performing_category,
            'fastest_improving_category': self.fastest_improving_category,
            'most_declining_category': self.most_declining_category,
            'goals_on_track': self.goals_on_track,
            'goals_at_risk': self.goals_at_risk,
            'goals_completed': self.goals_completed,
            'forecast_30_day': self.forecast_30_day,
            'forecast_30_day_confidence': self.forecast_30_day_confidence,
            'anomaly_count': self.anomaly_count,
            'unresolved_anomalies': self.unresolved_anomalies,
            'top_insights': self.top_insights,
            'top_recommendations': self.top_recommendations
        }
class RecommendationAnalytics:
    """
    Analytics for recommendations.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    period: str = ""  # daily, weekly, monthly, all_time
    generated_at: datetime = field(default_factory=datetime.now)
    
    # Statistics
    total_recommendations: int = 0
    accepted_count: int = 0
    rejected_count: int = 0
    completed_count: int = 0
    snoozed_count: int = 0
    pending_count: int = 0
    
    # Rates
    acceptance_rate: float = 0.0
    completion_rate: float = 0.0
    rejection_rate: float = 0.0
    
    # Impact
    total_impact_generated: float = 0.0
    total_savings_generated: float = 0.0
    average_impact_score: float = 0.0
    average_relevance_score: float = 0.0
    
    # Category breakdown
    category_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Most useful
    most_useful_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Trends
    recommendation_trends: Dict[str, Any] = field(default_factory=dict)
