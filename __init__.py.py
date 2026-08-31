"""
Personal Sustainability Intelligence & Recommendation Platform
A comprehensive system for generating personalized sustainability recommendations.
"""

from intelligence.models import (
    SustainabilityProfile, Recommendation, RecommendationStatus,
    RecommendationCategory, RecommendationPriority,
    RecommendationFeedback, RecommendationAnalytics,
    ProfileStrength, ProfileWeakness, UserPreference
)
from intelligence.profile import ProfileBuilder
from intelligence.recommendation_engine import RecommendationEngine
from intelligence.scoring import RecommendationScorer
from intelligence.context import ContextAnalyzer
from intelligence.feedback import FeedbackManager
from intelligence.analytics import RecommendationAnalyticsEngine
from intelligence.database import IntelligenceDatabase

__all__ = [
    'SustainabilityProfile',
    'Recommendation',
    'RecommendationStatus',
    'RecommendationCategory',
    'RecommendationPriority',
    'RecommendationFeedback',
    'RecommendationAnalytics',
    'ProfileStrength',
    'ProfileWeakness',
    'UserPreference',
    'ProfileBuilder',
    'RecommendationEngine',
    'RecommendationScorer',
    'ContextAnalyzer',
    'FeedbackManager',
    'RecommendationAnalyticsEngine',
    'IntelligenceDatabase'
]