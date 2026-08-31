"""
Personal Sustainability Intelligence & Recommendation Platform - Recommendation Scorer
Scores and ranks recommendations.
"""

import logging
from typing import List, Optional, Dict, Any

from intelligence.models import (
    Recommendation, SustainabilityProfile, RecommendationPriority
)

logger = logging.getLogger(__name__)


class RecommendationScorer:
    """
    Scores and ranks recommendations.
    """
    
    def __init__(self):
        """Initialize the scorer."""
        self.weights = {
            'impact': 0.30,
            'relevance': 0.25,
            'benefit': 0.15,
            'difficulty': 0.10,
            'effort': 0.10,
            'savings': 0.10
        }
        logger.info("Recommendation Scorer initialized")
    
    def score_recommendation(self,
                            recommendation: Recommendation,
                            profile: SustainabilityProfile) -> Recommendation:
        """
        Score a recommendation.
        
        Args:
            recommendation: Recommendation to score
            profile: Sustainability profile
        
        Returns:
            Recommendation: Scored recommendation
        """
        # Calculate component scores
        impact_score = recommendation.impact_score / 100
        relevance_score = recommendation.relevance_score / 100
        benefit_score = recommendation.benefit_score / 100
        
        # Difficulty (lower is better, so invert)
        difficulty_score = 1 - (recommendation.difficulty_score / 100)
        
        # Effort (lower is better, so invert)
        effort_score = 1 - (recommendation.effort_score / 100)
        
        # Savings (normalize)
        savings_score = min(1.0, recommendation.savings_estimate / 500)
        
        # Calculate overall priority
        recommendation.overall_priority = (
            impact_score * self.weights['impact'] * 100 +
            relevance_score * self.weights['relevance'] * 100 +
            benefit_score * self.weights['benefit'] * 100 +
            difficulty_score * self.weights['difficulty'] * 100 +
            effort_score * self.weights['effort'] * 100 +
            savings_score * self.weights['savings'] * 100
        )
        
        # Apply profile adjustments
        recommendation.overall_priority += self._apply_profile_adjustments(recommendation, profile)
        
        # Cap at 100
        recommendation.overall_priority = min(100, recommendation.overall_priority)
        
        return recommendation
    
    def _apply_profile_adjustments(self,
                                  recommendation: Recommendation,
                                  profile: SustainabilityProfile) -> float:
        """
        Apply profile-based adjustments.
        """
        adjustment = 0.0
        
        # Weakness bonus
        for weakness in profile.weaknesses:
            if weakness.category == recommendation.category.value:
                adjustment += 5
        
        # Strength penalty
        for strength in profile.strengths:
            if strength.category == recommendation.category.value:
                adjustment -= 5
        
        # Roadmap bonus
        if profile.roadmap_progress > 30:
            adjustment += 3
        
        # Habit consistency bonus
        if profile.habit_consistency > 70:
            adjustment += 5
        
        return adjustment
    
    def rank_recommendations(self,
                           recommendations: List[Recommendation],
                           limit: int = 10) -> List[Recommendation]:
        """
        Rank recommendations by priority.
        
        Args:
            recommendations: List of recommendations
            limit: Number to return
        
        Returns:
            List[Recommendation]: Ranked recommendations
        """
        # Sort by overall priority
        sorted_recs = sorted(recommendations, key=lambda x: x.overall_priority, reverse=True)
        
        # Filter out duplicates and conflicting
        filtered = [r for r in sorted_recs if not r.is_duplicate]
        
        return filtered[:limit]
    
    def get_top_recommendations(self,
                               recommendations: List[Recommendation],
                               count: int = 3) -> List[Recommendation]:
        """
        Get top recommendations.
        
        Args:
            recommendations: List of recommendations
            count: Number to return
        
        Returns:
            List[Recommendation]: Top recommendations
        """
        ranked = self.rank_recommendations(recommendations, count)
        return ranked[:count]
    
    def get_recommendations_by_category(self,
                                       recommendations: List[Recommendation],
                                       category: str) -> List[Recommendation]:
        """
        Get recommendations for a specific category.
        
        Args:
            recommendations: List of recommendations
            category: Category to filter
        
        Returns:
            List[Recommendation]: Filtered recommendations
        """
        return [r for r in recommendations if r.category.value == category]
    
    def calculate_recommendation_summary(self,
                                       recommendations: List[Recommendation]) -> Dict[str, Any]:
        """
        Calculate summary of recommendations.
        
        Args:
            recommendations: List of recommendations
        
        Returns:
            Dict: Summary statistics
        """
        if not recommendations:
            return {'message': 'No recommendations available'}
        
        total = len(recommendations)
        critical = sum(1 for r in recommendations if r.priority == RecommendationPriority.CRITICAL)
        high = sum(1 for r in recommendations if r.priority == RecommendationPriority.HIGH)
        medium = sum(1 for r in recommendations if r.priority == RecommendationPriority.MEDIUM)
        low = sum(1 for r in recommendations if r.priority == RecommendationPriority.LOW)
        
        avg_impact = sum(r.impact_score for r in recommendations) / total
        avg_savings = sum(r.savings_estimate for r in recommendations) / total
        avg_difficulty = sum(r.difficulty_score for r in recommendations) / total
        
        return {
            'total': total,
            'critical': critical,
            'high': high,
            'medium': medium,
            'low': low,
            'average_impact': avg_impact,
            'average_savings': avg_savings,
            'average_difficulty': avg_difficulty,
            'top_recommendation': recommendations[0].title if recommendations else None
        }