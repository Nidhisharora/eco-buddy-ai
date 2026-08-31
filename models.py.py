"""
Personal Sustainability Intelligence & Recommendation Platform - Data Models
Comprehensive models for intelligence and recommendations.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any
import uuid


class RecommendationCategory(Enum):
    """Categories of recommendations."""
    ENERGY = "energy"
    WATER = "water"
    FOOD = "food"
    WASTE = "waste"
    TRANSPORTATION = "transportation"
    SHOPPING = "shopping"
    TRAVEL = "travel"
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
            'user_id': self.user_id,
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
            'user_id': self.user_id,
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
            'recommendation_id': self.recommendation_id,
            'user_id': self.user_id,
            'feedback_type': self.feedback_type.value,
            'timestamp': self.timestamp.isoformat(),
            'notes': self.notes,
            'rating': self.rating,
            'actual_impact': self.actual_impact
        }


@dataclass
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