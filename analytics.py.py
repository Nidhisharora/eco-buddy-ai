"""
Personal Sustainability Intelligence & Recommendation Platform - Analytics
Provides analytics for recommendations.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict

from intelligence.models import (
    Recommendation, RecommendationAnalytics, RecommendationStatus
)

logger = logging.getLogger(__name__)


class RecommendationAnalyticsEngine:
    """
    Provides analytics for recommendations.
    """
    
    def __init__(self):
        """Initialize the analytics engine."""
        logger.info("Recommendation Analytics Engine initialized")
    
    def generate_analytics(self,
                          user_id: str,
                          recommendations: List[Recommendation],
                          period: str = 'all_time') -> RecommendationAnalytics:
        """
        Generate analytics for recommendations.
        
        Args:
            user_id: User ID
            recommendations: List of recommendations
            period: Analysis period
        
        Returns:
            RecommendationAnalytics: Analytics results
        """
        analytics = RecommendationAnalytics(
            user_id=user_id,
            period=period
        )
        
        if not recommendations:
            return analytics
        
        # Filter by period
        filtered = self._filter_by_period(recommendations, period)
        
        if not filtered:
            return analytics
        
        # Basic statistics
        analytics.total_recommendations = len(filtered)
        analytics.accepted_count = sum(1 for r in filtered if r.status == RecommendationStatus.ACCEPTED)
        analytics.rejected_count = sum(1 for r in filtered if r.status == RecommendationStatus.REJECTED)
        analytics.completed_count = sum(1 for r in filtered if r.status == RecommendationStatus.COMPLETED)
        analytics.snoozed_count = sum(1 for r in filtered if r.status == RecommendationStatus.SNOOZED)
        analytics.pending_count = sum(1 for r in filtered if r.status == RecommendationStatus.PENDING)
        
        # Calculate rates
        total = analytics.total_recommendations
        analytics.acceptance_rate = (analytics.accepted_count / total * 100) if total > 0 else 0
        analytics.completion_rate = (analytics.completed_count / total * 100) if total > 0 else 0
        analytics.rejection_rate = (analytics.rejected_count / total * 100) if total > 0 else 0
        
        # Impact metrics
        impact_scores = [r.impact_score for r in filtered]
        relevance_scores = [r.relevance_score for r in filtered]
        
        analytics.average_impact_score = statistics.mean(impact_scores) if impact_scores else 0
        analytics.average_relevance_score = statistics.mean(relevance_scores) if relevance_scores else 0
        
        # Total impact generated
        completed_recs = [r for r in filtered if r.status == RecommendationStatus.COMPLETED]
        analytics.total_impact_generated = sum(r.impact_score for r in completed_recs)
        analytics.total_savings_generated = sum(r.savings_estimate for r in completed_recs)
        
        # Category statistics
        analytics.category_stats = self._calculate_category_stats(filtered)
        
        # Most useful recommendations
        analytics.most_useful_recommendations = self._get_most_useful(filtered)
        
        # Trends
        analytics.recommendation_trends = self._calculate_trends(filtered)
        
        analytics.generated_at = datetime.now()
        
        return analytics
    
    def _filter_by_period(self, recommendations: List[Recommendation], period: str) -> List[Recommendation]:
        """
        Filter recommendations by period.
        """
        if period == 'all_time':
            return recommendations
        
        now = datetime.now()
        cutoff = now
        
        if period == 'daily':
            cutoff = now - timedelta(days=1)
        elif period == 'weekly':
            cutoff = now - timedelta(days=7)
        elif period == 'monthly':
            cutoff = now - timedelta(days=30)
        
        return [r for r in recommendations if r.created_at >= cutoff]
    
    def _calculate_category_stats(self, recommendations: List[Recommendation]) -> Dict[str, Dict[str, Any]]:
        """
        Calculate category statistics.
        """
        stats = defaultdict(lambda: {'total': 0, 'accepted': 0, 'completed': 0, 'impact': 0})
        
        for rec in recommendations:
            category = rec.category.value
            stats[category]['total'] += 1
            if rec.status == RecommendationStatus.ACCEPTED:
                stats[category]['accepted'] += 1
            if rec.status == RecommendationStatus.COMPLETED:
                stats[category]['completed'] += 1
                stats[category]['impact'] += rec.impact_score
        
        # Calculate rates
        result = {}
        for category, data in stats.items():
            total = data['total']
            result[category] = {
                'total': total,
                'accepted': data['accepted'],
                'completed': data['completed'],
                'acceptance_rate': (data['accepted'] / total * 100) if total > 0 else 0,
                'completion_rate': (data['completed'] / total * 100) if total > 0 else 0,
                'total_impact': data['impact'],
                'average_impact': data['impact'] / data['completed'] if data['completed'] > 0 else 0
            }
        
        return result
    
    def _get_most_useful(self, recommendations: List[Recommendation]) -> List[Dict[str, Any]]:
        """
        Get most useful recommendations.
        """
        completed = [r for r in recommendations if r.status == RecommendationStatus.COMPLETED]
        
        if not completed:
            return []
        
        # Sort by impact score
        sorted_recs = sorted(completed, key=lambda x: x.impact_score, reverse=True)
        
        return [
            {
                'title': r.title,
                'category': r.category.value,
                'impact': r.impact_score,
                'savings': r.savings_estimate,
                'completed_at': r.created_at.isoformat()
            }
            for r in sorted_recs[:5]
        ]
    
    def _calculate_trends(self, recommendations: List[Recommendation]) -> Dict[str, Any]:
        """
        Calculate recommendation trends.
        """
        if not recommendations:
            return {}
        
        # Group by month
        monthly = defaultdict(list)
        for rec in recommendations:
            month_key = rec.created_at.strftime('%Y-%m')
            monthly[month_key].append(rec)
        
        # Calculate monthly metrics
        monthly_data = {}
        for month, recs in monthly.items():
            monthly_data[month] = {
                'total': len(recs),
                'accepted': sum(1 for r in recs if r.status == RecommendationStatus.ACCEPTED),
                'completed': sum(1 for r in recs if r.status == RecommendationStatus.COMPLETED),
                'avg_impact': sum(r.impact_score for r in recs) / len(recs) if recs else 0
            }
        
        # Sort by month
        sorted_months = sorted(monthly_data.keys())
        
        return {
            'months': sorted_months,
            'data': [monthly_data[m] for m in sorted_months],
            'trend': self._calculate_trend_direction(sorted_months, monthly_data)
        }
    
    def _calculate_trend_direction(self, months: List[str], data: Dict[str, Dict]) -> str:
        """
        Calculate trend direction.
        """
        if len(months) < 2:
            return 'insufficient_data'
        
        # Compare first and last month
        first = data[months[0]]
        last = data[months[-1]]
        
        if last['avg_impact'] > first['avg_impact'] * 1.1:
            return 'improving'
        elif last['avg_impact'] < first['avg_impact'] * 0.9:
            return 'declining'
        else:
            return 'stable'