"""
Personal Sustainability Intelligence & Recommendation Platform - Context Analyzer
Analyzes context for recommendations.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from intelligence.models import SustainabilityProfile

logger = logging.getLogger(__name__)


class ContextAnalyzer:
    """
    Analyzes context for recommendations.
    """
    
    def __init__(self):
        """Initialize the context analyzer."""
        self.seasonal_factors = self._initialize_seasonal_factors()
        logger.info("Context Analyzer initialized")
    
    def _initialize_seasonal_factors(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize seasonal factors.
        """
        return {
            'summer': {
                'energy': 'Reduce AC usage and use fans',
                'water': 'Water plants early morning or evening',
                'transportation': 'Walk or bike when weather is good'
            },
            'winter': {
                'energy': 'Lower thermostat and insulate home',
                'water': 'Prevent pipes from freezing',
                'transportation': 'Use public transit in bad weather'
            },
            'spring': {
                'food': 'Eat seasonal produce',
                'waste': 'Start composting garden waste',
                'shopping': 'Buy local spring produce'
            },
            'fall': {
                'energy': 'Prepare home for winter heating',
                'waste': 'Prepare garden for winter',
                'shopping': 'Buy seasonal fall produce'
            }
        }
    
    def analyze_context(self, profile: SustainabilityProfile) -> Dict[str, Any]:
        """
        Analyze context for recommendations.
        
        Args:
            profile: Sustainability profile
        
        Returns:
            Dict: Context analysis
        """
        context = {
            'relevant_goals': self._get_relevant_goals(profile),
            'relevant_habits': self._get_relevant_habits(profile),
            'seasonal_factors': self._get_seasonal_factors(),
            'profile_stage': self._get_profile_stage(profile),
            'recent_activity': self._get_recent_activity(profile)
        }
        
        return context
    
    def _get_relevant_goals(self, profile: SustainabilityProfile) -> List[str]:
        """
        Get relevant goals from profile.
        """
        goals = []
        
        for goal_id in profile.active_goals:
            # In a real implementation, would fetch goal details
            goals.append(goal_id)
        
        return goals[:3]
    
    def _get_relevant_habits(self, profile: SustainabilityProfile) -> List[str]:
        """
        Get relevant habits from profile.
        """
        habits = []
        
        for habit_id in profile.active_habits:
            habits.append(habit_id)
        
        return habits[:3]
    
    def _get_seasonal_factors(self) -> Dict[str, Any]:
        """
        Get seasonal factors based on current date.
        """
        now = datetime.now()
        month = now.month
        
        if 6 <= month <= 8:
            season = 'summer'
        elif 9 <= month <= 11:
            season = 'fall'
        elif 12 <= month <= 2:
            season = 'winter'
        else:
            season = 'spring'
        
        factors = self.seasonal_factors.get(season, {})
        factors['season'] = season
        
        return factors
    
    def _get_profile_stage(self, profile: SustainabilityProfile) -> str:
        """
        Get profile stage based on overall score.
        """
        if profile.overall_sustainability_score >= 80:
            return 'advanced'
        elif profile.overall_sustainability_score >= 60:
            return 'intermediate'
        elif profile.overall_sustainability_score >= 40:
            return 'beginner'
        else:
            return 'starter'
    
    def _get_recent_activity(self, profile: SustainabilityProfile) -> Dict[str, Any]:
        """
        Get recent activity from profile.
        """
        return {
            'has_recent_activity': True,
            'last_update': profile.last_analysis_date.isoformat() if profile.last_analysis_date else None,
            'profile_version': profile.profile_version
        }
    
    def get_context_for_category(self,
                               profile: SustainabilityProfile,
                               category: str) -> Dict[str, Any]:
        """
        Get context for a specific category.
        
        Args:
            profile: Sustainability profile
            category: Category to analyze
        
        Returns:
            Dict: Category context
        """
        context = {
            'score': self._get_category_score(profile, category),
            'is_strength': self._is_category_strength(profile, category),
            'is_weakness': self._is_category_weakness(profile, category),
            'improvement_potential': self._get_improvement_potential(profile, category),
            'has_related_goals': self._has_related_goals(profile, category),
            'has_related_habits': self._has_related_habits(profile, category)
        }
        
        return context
    
    def _get_category_score(self, profile: SustainabilityProfile, category: str) -> float:
        """
        Get score for a category.
        """
        score_map = {
            'energy': profile.energy_score,
            'water': profile.water_score,
            'food': profile.food_score,
            'waste': profile.waste_score,
            'transportation': profile.transport_score,
            'shopping': profile.shopping_score
        }
        return score_map.get(category, 50.0)
    
    def _is_category_strength(self, profile: SustainabilityProfile, category: str) -> bool:
        """
        Check if a category is a strength.
        """
        for strength in profile.strengths:
            if strength.category == category:
                return True
        return False
    
    def _is_category_weakness(self, profile: SustainabilityProfile, category: str) -> bool:
        """
        Check if a category is a weakness.
        """
        for weakness in profile.weaknesses:
            if weakness.category == category:
                return True
        return False
    
    def _get_improvement_potential(self, profile: SustainabilityProfile, category: str) -> float:
        """
        Get improvement potential for a category.
        """
        score = self._get_category_score(profile, category)
        return max(0, 100 - score)
    
    def _has_related_goals(self, profile: SustainabilityProfile, category: str) -> bool:
        """
        Check if there are related goals.
        """
        # Simplified check
        return len(profile.active_goals) > 0
    
    def _has_related_habits(self, profile: SustainabilityProfile, category: str) -> bool:
        """
        Check if there are related habits.
        """
        return len(profile.active_habits) > 0