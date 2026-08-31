"""
Personal Sustainability Intelligence & Recommendation Platform - Recommendation Engine
Generates personalized recommendations.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from intelligence.models import (
    SustainabilityProfile, Recommendation, RecommendationCategory,
    RecommendationPriority, RecommendationStatus
)
from intelligence.scoring import RecommendationScorer
from intelligence.context import ContextAnalyzer

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Generates personalized sustainability recommendations.
    """
    
    def __init__(self):
        """Initialize the recommendation engine."""
        self.scorer = RecommendationScorer()
        self.context_analyzer = ContextAnalyzer()
        self.recommendation_templates = self._initialize_templates()
        logger.info("Recommendation Engine initialized")
    
    def _initialize_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Initialize recommendation templates by category.
        """
        return {
            'energy': [
                {
                    'title': 'Switch to LED Lighting',
                    'description': 'Replace all incandescent bulbs with LED bulbs',
                    'impact_score': 75,
                    'cost_estimate': 50,
                    'savings_estimate': 100,
                    'difficulty_score': 20,
                    'effort_score': 25,
                    'benefit_score': 80,
                    'how_to_implement': 'Purchase LED bulbs and replace old bulbs room by room',
                    'why_matters': 'LED bulbs use 75% less energy and last 25 times longer'
                },
                {
                    'title': 'Install Smart Thermostat',
                    'description': 'Use programmable thermostat to optimize heating and cooling',
                    'impact_score': 85,
                    'cost_estimate': 250,
                    'savings_estimate': 200,
                    'difficulty_score': 40,
                    'effort_score': 35,
                    'benefit_score': 85,
                    'how_to_implement': 'Purchase and install a smart thermostat following manufacturer instructions',
                    'why_matters': 'Smart thermostats can save 10-15% on heating and cooling costs'
                },
                {
                    'title': 'Unplug Electronics When Not in Use',
                    'description': 'Eliminate phantom energy usage by unplugging devices',
                    'impact_score': 60,
                    'cost_estimate': 0,
                    'savings_estimate': 50,
                    'difficulty_score': 10,
                    'effort_score': 15,
                    'benefit_score': 65,
                    'how_to_implement': 'Unplug devices when not in use or use smart power strips',
                    'why_matters': 'Phantom loads account for 5-10% of household energy usage'
                }
            ],
            'water': [
                {
                    'title': 'Fix Leaky Faucets',
                    'description': 'Repair all leaking faucets and pipes',
                    'impact_score': 80,
                    'cost_estimate': 25,
                    'savings_estimate': 150,
                    'difficulty_score': 30,
                    'effort_score': 35,
                    'benefit_score': 85,
                    'how_to_implement': 'Identify and repair leaks or call a plumber',
                    'why_matters': 'One dripping faucet can waste 3,000 gallons of water per year'
                },
                {
                    'title': 'Install Low-Flow Showerheads',
                    'description': 'Replace existing showerheads with water-efficient models',
                    'impact_score': 70,
                    'cost_estimate': 30,
                    'savings_estimate': 100,
                    'difficulty_score': 20,
                    'effort_score': 25,
                    'benefit_score': 75,
                    'how_to_implement': 'Purchase and install low-flow showerheads',
                    'why_matters': 'Low-flow showerheads can reduce water usage by 40%'
                }
            ],
            'waste': [
                {
                    'title': 'Start Composting',
                    'description': 'Compost food waste and yard trimmings',
                    'impact_score': 75,
                    'cost_estimate': 50,
                    'savings_estimate': 50,
                    'difficulty_score': 35,
                    'effort_score': 40,
                    'benefit_score': 80,
                    'how_to_implement': 'Set up a compost bin and start collecting organic waste',
                    'why_matters': 'Composting reduces landfill waste and creates nutrient-rich soil'
                },
                {
                    'title': 'Set Up Recycling Station',
                    'description': 'Create a dedicated recycling area with proper sorting',
                    'impact_score': 65,
                    'cost_estimate': 20,
                    'savings_estimate': 30,
                    'difficulty_score': 15,
                    'effort_score': 20,
                    'benefit_score': 70,
                    'how_to_implement': 'Get bins and labels for different recyclable materials',
                    'why_matters': 'Proper recycling reduces waste and conserves resources'
                }
            ],
            'food': [
                {
                    'title': 'Plan Weekly Meals',
                    'description': 'Create meal plans to reduce food waste',
                    'impact_score': 70,
                    'cost_estimate': 0,
                    'savings_estimate': 200,
                    'difficulty_score': 25,
                    'effort_score': 30,
                    'benefit_score': 80,
                    'how_to_implement': 'Plan meals for the week and create a shopping list',
                    'why_matters': 'Meal planning reduces food waste and saves money'
                }
            ],
            'transportation': [
                {
                    'title': 'Use Public Transit',
                    'description': 'Switch to public transportation for commute',
                    'impact_score': 85,
                    'cost_estimate': 50,
                    'savings_estimate': 300,
                    'difficulty_score': 45,
                    'effort_score': 50,
                    'benefit_score': 85,
                    'how_to_implement': 'Research public transit routes and get a transit pass',
                    'why_matters': 'Public transit reduces carbon emissions and traffic congestion'
                }
            ]
        }
    
    def generate_recommendations(self,
                                profile: SustainabilityProfile,
                                limit: int = 10) -> List[Recommendation]:
        """
        Generate personalized recommendations.
        
        Args:
            profile: Sustainability profile
            limit: Maximum number of recommendations
        
        Returns:
            List[Recommendation]: Generated recommendations
        """
        recommendations = []
        
        # Get context insights
        context = self.context_analyzer.analyze_context(profile)
        
        # Generate recommendations for each category
        for category in ['energy', 'water', 'waste', 'food', 'transportation']:
            templates = self.recommendation_templates.get(category, [])
            
            for template in templates:
                # Check if recommendation is relevant
                relevance = self._calculate_relevance(template, profile, context)
                if relevance < 30:
                    continue
                
                # Create recommendation
                rec = Recommendation(
                    user_id=profile.user_id,
                    title=template['title'],
                    description=template['description'],
                    category=RecommendationCategory(category),
                    impact_score=template['impact_score'],
                    cost_estimate=template['cost_estimate'],
                    savings_estimate=template['savings_estimate'],
                    difficulty_score=template['difficulty_score'],
                    effort_score=template['effort_score'],
                    benefit_score=template['benefit_score'],
                    relevance_score=relevance,
                    how_to_implement=template.get('how_to_implement', ''),
                    why_matters=template.get('why_matters', ''),
                    based_on_weakness=self._get_based_on_weakness(category, profile),
                    based_on_goals=context.get('relevant_goals', []),
                    based_on_habits=context.get('relevant_habits', [])
                )
                
                # Score the recommendation
                rec = self.scorer.score_recommendation(rec, profile)
                
                # Set priority
                rec.priority = self._get_priority(rec.overall_priority)
                
                # Set explanation
                rec.explanation = self._generate_explanation(rec, profile)
                
                # Set expiration
                rec.expires_at = datetime.now() + timedelta(days=30)
                
                recommendations.append(rec)
        
        # Remove duplicates
        recommendations = self._remove_duplicates(recommendations)
        
        # Sort by overall priority
        recommendations.sort(key=lambda x: x.overall_priority, reverse=True)
        
        return recommendations[:limit]
    
    def _calculate_relevance(self,
                            template: Dict[str, Any],
                            profile: SustainabilityProfile,
                            context: Dict[str, Any]) -> float:
        """
        Calculate relevance of a recommendation.
        """
        category = template.get('category', '')
        relevance = 50.0  # Base
        
        # Check if category is a weakness
        for weakness in profile.weaknesses:
            if weakness.category == category:
                relevance += 20
        
        # Check if category is a strength (less relevant)
        for strength in profile.strengths:
            if strength.category == category:
                relevance -= 10
        
        # Check if related to goals
        if context.get('relevant_goals'):
            relevance += 15
        
        # Check if related to habits
        if context.get('relevant_habits'):
            relevance += 10
        
        # Check roadmap progress
        if profile.roadmap_progress > 50:
            relevance += 5
        
        return max(0, min(100, relevance))
    
    def _get_based_on_weakness(self, category: str, profile: SustainabilityProfile) -> Optional[str]:
        """
        Get weakness description for a category.
        """
        for weakness in profile.weaknesses:
            if weakness.category == category:
                return weakness.description
        return None
    
    def _get_priority(self, overall_priority: float) -> RecommendationPriority:
        """
        Get priority based on overall score.
        """
        if overall_priority >= 80:
            return RecommendationPriority.CRITICAL
        elif overall_priority >= 60:
            return RecommendationPriority.HIGH
        elif overall_priority >= 40:
            return RecommendationPriority.MEDIUM
        else:
            return RecommendationPriority.LOW
    
    def _generate_explanation(self, rec: Recommendation, profile: SustainabilityProfile) -> str:
        """
        Generate explanation for a recommendation.
        """
        explanations = []
        
        if rec.based_on_weakness:
            explanations.append(f"This addresses your weakness in {rec.category.value}")
        
        if rec.based_on_goals:
            explanations.append(f"Aligns with your sustainability goals")
        
        if rec.based_on_habits:
            explanations.append(f"Builds on your existing habits")
        
        if rec.impact_score > 70:
            explanations.append(f"High environmental impact ({rec.impact_score:.0f}%)")
        
        if rec.savings_estimate > 100:
            explanations.append(f"Estimated savings: ${rec.savings_estimate:.0f}/year")
        
        if rec.difficulty_score < 30:
            explanations.append("Easy to implement")
        
        if not explanations:
            explanations.append("Good opportunity for improvement")
        
        return " ".join(explanations[:3])
    
    def _remove_duplicates(self, recommendations: List[Recommendation]) -> List[Recommendation]:
        """
        Remove duplicate recommendations.
        """
        seen_titles = set()
        unique = []
        
        for rec in recommendations:
            if rec.title not in seen_titles:
                seen_titles.add(rec.title)
                unique.append(rec)
            else:
                rec.is_duplicate = True
        
        return unique