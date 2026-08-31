"""
Personal Sustainability Intelligence & Recommendation Platform - Profile Builder
Builds unified sustainability profiles from user data.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from intelligence.models import (
    SustainabilityProfile, ProfileStrength, ProfileWeakness,
    UserPreference
)

logger = logging.getLogger(__name__)


class ProfileBuilder:
    """
    Builds sustainability profiles from user data.
    """
    
    def __init__(self):
        """Initialize the profile builder."""
        logger.info("Profile Builder initialized")
    
    def build_profile(self,
                     user_id: str,
                     sustainability_data: Dict[str, Any],
                     goals: List[Dict[str, Any]],
                     habits: List[Dict[str, Any]],
                     roadmap_data: Optional[Dict[str, Any]] = None,
                     household_data: Optional[Dict[str, Any]] = None) -> SustainabilityProfile:
        """
        Build a sustainability profile from user data.
        
        Args:
            user_id: User ID
            sustainability_data: Sustainability metrics
            goals: List of goals
            habits: List of habits
            roadmap_data: Roadmap data
            household_data: Household data
        
        Returns:
            SustainabilityProfile: Built profile
        """
        profile = SustainabilityProfile(
            user_id=user_id,
            household_id=household_data.get('id') if household_data else None
        )
        
        # Extract category scores
        profile.energy_score = sustainability_data.get('energy_score', 50.0)
        profile.water_score = sustainability_data.get('water_score', 50.0)
        profile.food_score = sustainability_data.get('food_score', 50.0)
        profile.waste_score = sustainability_data.get('waste_score', 50.0)
        profile.transport_score = sustainability_data.get('transport_score', 50.0)
        profile.shopping_score = sustainability_data.get('shopping_score', 50.0)
        
        # Calculate overall scores
        category_scores = [
            profile.energy_score,
            profile.water_score,
            profile.food_score,
            profile.waste_score,
            profile.transport_score,
            profile.shopping_score
        ]
        profile.overall_sustainability_score = statistics.mean(category_scores)
        profile.overall_efficiency_score = sustainability_data.get('efficiency_score', 50.0)
        
        # Process goals
        if goals:
            profile.active_goals = [g.get('id', '') for g in goals if g.get('status') in ['active', 'in_progress']]
            profile.completed_goals = [g.get('id', '') for g in goals if g.get('status') == 'completed']
        
        # Process habits
        if habits:
            profile.active_habits = [h.get('id', '') for h in habits if h.get('status') == 'active']
            consistency_scores = [h.get('consistency', 0) for h in habits if h.get('consistency')]
            profile.habit_consistency = statistics.mean(consistency_scores) if consistency_scores else 0.0
        
        # Process roadmap
        if roadmap_data:
            profile.roadmap_progress = roadmap_data.get('progress', 0.0)
            profile.roadmap_stage = roadmap_data.get('current_stage', 0)
        
        # Identify strengths and weaknesses
        profile.strengths = self._identify_strengths(profile)
        profile.weaknesses = self._identify_weaknesses(profile)
        
        # Set preferences
        profile.preferences = UserPreference(user_id=user_id)
        
        # Set benchmarks
        profile.benchmark_comparison = self._calculate_benchmarks(profile)
        
        profile.last_analysis_date = datetime.now()
        profile.profile_version = 1
        profile.updated_at = datetime.now()
        
        logger.info(f"Profile built for user {user_id}")
        return profile
    
    def _identify_strengths(self, profile: SustainabilityProfile) -> List[ProfileStrength]:
        """
        Identify strengths in the profile.
        """
        strengths = []
        categories = [
            ('energy', profile.energy_score),
            ('water', profile.water_score),
            ('food', profile.food_score),
            ('waste', profile.waste_score),
            ('transport', profile.transport_score),
            ('shopping', profile.shopping_score)
        ]
        
        for category, score in categories:
            if score >= 70:
                strengths.append(ProfileStrength(
                    category=category,
                    score=score,
                    description=f"Strong performance in {category}",
                    evidence=[f"Sustainability score: {score:.1f}%"]
                ))
        
        # Sort by score
        strengths.sort(key=lambda x: x.score, reverse=True)
        return strengths[:3]  # Top 3 strengths
    
    def _identify_weaknesses(self, profile: SustainabilityProfile) -> List[ProfileWeakness]:
        """
        Identify weaknesses in the profile.
        """
        weaknesses = []
        categories = [
            ('energy', profile.energy_score),
            ('water', profile.water_score),
            ('food', profile.food_score),
            ('waste', profile.waste_score),
            ('transport', profile.transport_score),
            ('shopping', profile.shopping_score)
        ]
        
        for category, score in categories:
            if score < 50:
                weaknesses.append(ProfileWeakness(
                    category=category,
                    score=score,
                    description=f"Improvement needed in {category}",
                    improvement_potential=max(0, 70 - score),
                    suggested_actions=[f"Focus on improving {category} sustainability"]
                ))
        
        # Sort by potential improvement
        weaknesses.sort(key=lambda x: x.improvement_potential, reverse=True)
        return weaknesses[:3]  # Top 3 weaknesses
    
    def _calculate_benchmarks(self, profile: SustainabilityProfile) -> Dict[str, float]:
        """
        Calculate benchmark comparisons.
        """
        benchmarks = {}
        
        # National averages (simplified)
        national_averages = {
            'energy': 60.0,
            'water': 55.0,
            'food': 50.0,
            'waste': 45.0,
            'transport': 50.0,
            'shopping': 50.0
        }
        
        for category, avg in national_averages.items():
            score = getattr(profile, f"{category}_score", 50.0)
            benchmarks[f"{category}_vs_avg"] = ((score - avg) / avg) * 100
        
        return benchmarks
    
    def update_profile(self,
                      profile: SustainabilityProfile,
                      new_data: Dict[str, Any]) -> SustainabilityProfile:
        """
        Update an existing profile with new data.
        
        Args:
            profile: Existing profile
            new_data: New data to incorporate
        
        Returns:
            SustainabilityProfile: Updated profile
        """
        # Update scores
        for key in ['energy_score', 'water_score', 'food_score', 'waste_score', 'transport_score', 'shopping_score']:
            if key in new_data:
                setattr(profile, key, new_data[key])
        
        # Recalculate overall
        category_scores = [
            profile.energy_score,
            profile.water_score,
            profile.food_score,
            profile.waste_score,
            profile.transport_score,
            profile.shopping_score
        ]
        profile.overall_sustainability_score = statistics.mean(category_scores)
        profile.overall_efficiency_score = new_data.get('efficiency_score', profile.overall_efficiency_score)
        
        # Update strengths and weaknesses
        profile.strengths = self._identify_strengths(profile)
        profile.weaknesses = self._identify_weaknesses(profile)
        
        # Update benchmarks
        profile.benchmark_comparison = self._calculate_benchmarks(profile)
        
        profile.profile_version += 1
        profile.last_analysis_date = datetime.now()
        profile.updated_at = datetime.now()
        
        logger.info(f"Profile updated for user {profile.user_id}")
        return profile