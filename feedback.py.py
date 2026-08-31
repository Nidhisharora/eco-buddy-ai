"""
Personal Sustainability Intelligence & Recommendation Platform - Feedback Manager
Manages recommendation feedback.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from intelligence.models import (
    Recommendation, RecommendationFeedback, FeedbackType,
    RecommendationStatus
)

logger = logging.getLogger(__name__)


class FeedbackManager:
    """
    Manages recommendation feedback.
    """
    
    def __init__(self):
        """Initialize the feedback manager."""
        logger.info("Feedback Manager initialized")
    
    def accept_recommendation(self,
                            recommendation: Recommendation,
                            notes: str = "") -> Recommendation:
        """
        Accept a recommendation.
        
        Args:
            recommendation: Recommendation to accept
            notes: Additional notes
        
        Returns:
            Recommendation: Updated recommendation
        """
        recommendation.status = RecommendationStatus.ACCEPTED
        recommendation.acceptance_count += 1
        
        feedback = RecommendationFeedback(
            recommendation_id=recommendation.id,
            user_id=recommendation.user_id,
            feedback_type=FeedbackType.ACCEPT,
            notes=notes
        )
        recommendation.feedback_history.append(feedback)
        
        logger.info(f"Recommendation accepted: {recommendation.title}")
        return recommendation
    
    def reject_recommendation(self,
                            recommendation: Recommendation,
                            notes: str = "") -> Recommendation:
        """
        Reject a recommendation.
        
        Args:
            recommendation: Recommendation to reject
            notes: Additional notes
        
        Returns:
            Recommendation: Updated recommendation
        """
        recommendation.status = RecommendationStatus.REJECTED
        
        feedback = RecommendationFeedback(
            recommendation_id=recommendation.id,
            user_id=recommendation.user_id,
            feedback_type=FeedbackType.REJECT,
            notes=notes
        )
        recommendation.feedback_history.append(feedback)
        
        logger.info(f"Recommendation rejected: {recommendation.title}")
        return recommendation
    
    def snooze_recommendation(self,
                            recommendation: Recommendation,
                            days: int = 7,
                            notes: str = "") -> Recommendation:
        """
        Snooze a recommendation.
        
        Args:
            recommendation: Recommendation to snooze
            days: Number of days to snooze
            notes: Additional notes
        
        Returns:
            Recommendation: Updated recommendation
        """
        recommendation.status = RecommendationStatus.SNOOZED
        recommendation.snoozed_until = datetime.now() + timedelta(days=days)
        
        feedback = RecommendationFeedback(
            recommendation_id=recommendation.id,
            user_id=recommendation.user_id,
            feedback_type=FeedbackType.SNOOZE,
            notes=notes
        )
        recommendation.feedback_history.append(feedback)
        
        logger.info(f"Recommendation snoozed: {recommendation.title}")
        return recommendation
    
    def complete_recommendation(self,
                              recommendation: Recommendation,
                              actual_impact: Optional[float] = None,
                              rating: Optional[int] = None,
                              notes: str = "") -> Recommendation:
        """
        Mark a recommendation as completed.
        
        Args:
            recommendation: Recommendation to complete
            actual_impact: Actual impact achieved
            rating: Rating (1-5)
            notes: Additional notes
        
        Returns:
            Recommendation: Updated recommendation
        """
        recommendation.status = RecommendationStatus.COMPLETED
        recommendation.completion_count += 1
        
        feedback = RecommendationFeedback(
            recommendation_id=recommendation.id,
            user_id=recommendation.user_id,
            feedback_type=FeedbackType.COMPLETE,
            notes=notes,
            rating=rating,
            actual_impact=actual_impact
        )
        recommendation.feedback_history.append(feedback)
        
        logger.info(f"Recommendation completed: {recommendation.title}")
        return recommendation
    
    def mark_helpful(self,
                    recommendation: Recommendation,
                    notes: str = "") -> Recommendation:
        """
        Mark a recommendation as helpful.
        
        Args:
            recommendation: Recommendation to mark
            notes: Additional notes
        
        Returns:
            Recommendation: Updated recommendation
        """
        feedback = RecommendationFeedback(
            recommendation_id=recommendation.id,
            user_id=recommendation.user_id,
            feedback_type=FeedbackType.HELPFUL,
            notes=notes
        )
        recommendation.feedback_history.append(feedback)
        
        logger.info(f"Recommendation marked helpful: {recommendation.title}")
        return recommendation
    
    def mark_not_helpful(self,
                        recommendation: Recommendation,
                        notes: str = "") -> Recommendation:
        """
        Mark a recommendation as not helpful.
        
        Args:
            recommendation: Recommendation to mark
            notes: Additional notes
        
        Returns:
            Recommendation: Updated recommendation
        """
        feedback = RecommendationFeedback(
            recommendation_id=recommendation.id,
            user_id=recommendation.user_id,
            feedback_type=FeedbackType.NOT_HELPFUL,
            notes=notes
        )
        recommendation.feedback_history.append(feedback)
        
        logger.info(f"Recommendation marked not helpful: {recommendation.title}")
        return recommendation
    
    def get_feedback_summary(self, recommendations: List[Recommendation]) -> Dict[str, Any]:
        """
        Get feedback summary.
        
        Args:
            recommendations: List of recommendations
        
        Returns:
            Dict: Feedback summary
        """
        if not recommendations:
            return {'message': 'No recommendations available'}
        
        total = len(recommendations)
        accepted = sum(1 for r in recommendations if r.status == RecommendationStatus.ACCEPTED)
        rejected = sum(1 for r in recommendations if r.status == RecommendationStatus.REJECTED)
        completed = sum(1 for r in recommendations if r.status == RecommendationStatus.COMPLETED)
        snoozed = sum(1 for r in recommendations if r.status == RecommendationStatus.SNOOZED)
        pending = sum(1 for r in recommendations if r.status == RecommendationStatus.PENDING)
        
        return {
            'total': total,
            'accepted': accepted,
            'rejected': rejected,
            'completed': completed,
            'snoozed': snoozed,
            'pending': pending,
            'acceptance_rate': (accepted / total * 100) if total > 0 else 0,
            'completion_rate': (completed / total * 100) if total > 0 else 0,
            'rejection_rate': (rejected / total * 100) if total > 0 else 0,
            'feedback_count': sum(len(r.feedback_history) for r in recommendations)
        }