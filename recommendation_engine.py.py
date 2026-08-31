"""
Sustainability Gamification & Challenge Platform - Recommendation Engine
Recommends challenges based on user data.
Personal Sustainability Intelligence & Recommendation Platform - Recommendation Engine
Generates personalized recommendations.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from gamification.models import (
    Challenge, ChallengeRecommendation, ChallengeType,
    ChallengeDifficulty, ChallengeCategory, ChallengeStatus,
    ChallengeTemplate
)
from intelligence.models import (
    SustainabilityProfile, Recommendation, RecommendationCategory,
    RecommendationPriority, RecommendationStatus
)
from intelligence.scoring import RecommendationScorer
from intelligence.context import ContextAnalyzer

logger = logging.getLogger(__name__)


class ChallengeRecommendationEngine:
    """
    Recommends challenges based on user data.
class RecommendationEngine:
    """
    Generates personalized sustainability recommendations.
    """
    
    def __init__(self):
        """Initialize the recommendation engine."""
        self.recommendation_weights = {
            'habit_match': 0.3,
            'goal_match': 0.25,
            'roadmap_match': 0.2,
            'difficulty_appropriate': 0.15,
            'diversity': 0.1
        }
        logger.info("Challenge Recommendation Engine initialized")
    
    def generate_recommendations(self,
                                user_id: str,
                                available_challenges: List[Challenge],
                                completed_challenges: List[str],
                                user_habits: List[Dict[str, Any]],
                                user_goals: List[Dict[str, Any]],
                                roadmap_progress: Dict[str, Any],
                                user_level: int) -> List[ChallengeRecommendation]:
        """
        Generate challenge recommendations for a user.
        
        Args:
            user_id: User ID
            available_challenges: List of available challenges
            completed_challenges: List of completed challenge IDs
            user_habits: List of user habits
            user_goals: List of user goals
            roadmap_progress: Roadmap progress data
            user_level: User's current level
        
        Returns:
            List[ChallengeRecommendation]: Recommendations
        """
        recommendations = []
        
        # Filter out completed challenges
        available = [c for c in available_challenges if c.id not in completed_challenges]
        
        if not available:
            return recommendations
        
        for challenge in available:
            # Calculate recommendation score
            score = self._calculate_score(challenge, user_habits, user_goals, roadmap_progress, user_level)
            
            # Generate reason
            reason = self._generate_reason(challenge, user_habits, user_goals, roadmap_progress)
            
            # Determine priority
            priority = self._determine_priority(score)
            
            recommendation = ChallengeRecommendation(
                user_id=user_id,
                challenge_id=challenge.id,
                challenge_title=challenge.title,
                reason=reason,
                confidence=score / 100,
                priority=priority,
                based_on_habits=self._match_habits(challenge, user_habits),
                based_on_goals=self._match_goals(challenge, user_goals),
                based_on_roadmap=self._match_roadmap(challenge, roadmap_progress)
            )
            
            recommendations.append(recommendation)
        
        # Sort by confidence and priority
        recommendations.sort(key=lambda r: (r.confidence, r.priority), reverse=True)
        
        return recommendations[:10]  # Top 10 recommendations
    
    def _calculate_score(self,
                        challenge: Challenge,
                        user_habits: List[Dict[str, Any]],
                        user_goals: List[Dict[str, Any]],
                        roadmap_progress: Dict[str, Any],
                        user_level: int) -> float:
        """
        Calculate recommendation score.
        """
        score = 0.0
        
        # Habit match
        habit_score = self._calculate_habit_match(challenge, user_habits)
        score += habit_score * self.recommendation_weights['habit_match']
        
        # Goal match
        goal_score = self._calculate_goal_match(challenge, user_goals)
        score += goal_score * self.recommendation_weights['goal_match']
        
        # Roadmap match
        roadmap_score = self._calculate_roadmap_match(challenge, roadmap_progress)
        score += roadmap_score * self.recommendation_weights['roadmap_match']
        
        # Difficulty appropriateness
        difficulty_score = self._calculate_difficulty_score(challenge, user_level)
        score += difficulty_score * self.recommendation_weights['difficulty_appropriate']
        
        # Diversity
        diversity_score = self._calculate_diversity_score(challenge)
        score += diversity_score * self.recommendation_weights['diversity']
        
        return score
    
    def _calculate_habit_match(self,
                              challenge: Challenge,
                              user_habits: List[Dict[str, Any]]) -> float:
        """
        Calculate habit match score.
        """
        if not user_habits:
            return 0.0
        
        match_count = 0
        total = len(user_habits)
        
        for habit in user_habits:
            habit_category = habit.get('category', '')
            habit_name = habit.get('name', '').lower()
            
            # Check if habit matches challenge
            if challenge.category.value == habit_category:
                match_count += 1
            elif habit_name in challenge.title.lower():
                match_count += 0.5
        
        return min(100, (match_count / total) * 100) if total > 0 else 0
    
    def _calculate_goal_match(self,
                             challenge: Challenge,
                             user_goals: List[Dict[str, Any]]) -> float:
        """
        Calculate goal match score.
        """
        if not user_goals:
            return 0.0
        
        match_count = 0
        total = len(user_goals)
        
        for goal in user_goals:
            goal_category = goal.get('category', '')
            goal_title = goal.get('title', '').lower()
            
            if challenge.category.value == goal_category:
                match_count += 1
            elif goal_title in challenge.title.lower():
                match_count += 0.5
        
        return min(100, (match_count / total) * 100) if total > 0 else 0
    
    def _calculate_roadmap_match(self,
                               challenge: Challenge,
                               roadmap_progress: Dict[str, Any]) -> float:
        """
        Calculate roadmap match score.
        """
        if not roadmap_progress:
            return 50.0
        
        # If challenge matches current roadmap stage
        current_stage = roadmap_progress.get('current_stage', 0)
        total_stages = roadmap_progress.get('total_stages', 5)
        
        if total_stages > 0:
            stage_progress = (current_stage / total_stages) * 100
            
            # Challenges that match the current stage get higher scores
            if challenge.difficulty.value == self._get_difficulty_for_stage(current_stage, total_stages):
                return 80.0 + (stage_progress * 0.2)
        
        return 50.0
    
    def _get_difficulty_for_stage(self, current_stage: int, total_stages: int) -> str:
        """
        Get appropriate difficulty for a roadmap stage.
        """
        progress = current_stage / total_stages
        
        if progress < 0.3:
            return 'beginner'
        elif progress < 0.6:
            return 'intermediate'
        elif progress < 0.8:
            return 'advanced'
        else:
            return 'expert'
    
    def _calculate_difficulty_score(self,
                                   challenge: Challenge,
                                   user_level: int) -> float:
        """
        Calculate difficulty appropriateness score.
        """
        difficulty_levels = {
            ChallengeDifficulty.BEGINNER: 1,
            ChallengeDifficulty.INTERMEDIATE: 2,
            ChallengeDifficulty.ADVANCED: 3,
            ChallengeDifficulty.EXPERT: 4
        }
        
        challenge_level = difficulty_levels.get(challenge.difficulty, 1)
        
        # User level maps to difficulty
        if user_level <= 2:
            recommended = 1
        elif user_level <= 5:
            recommended = 2
        elif user_level <= 10:
            recommended = 3
        else:
            recommended = 4
        
        # Score based on how close the challenge difficulty is to recommended
        diff = abs(challenge_level - recommended)
        
        if diff == 0:
            return 100.0
        elif diff == 1:
            return 70.0
        elif diff == 2:
            return 40.0
        else:
            return 10.0
    
    def _calculate_diversity_score(self, challenge: Challenge) -> float:
        """
        Calculate diversity score to ensure varied recommendations.
        """
        # Randomize slightly to ensure diversity
        return 50.0 + (random.random() * 20)
    
    def _generate_reason(self,
                        challenge: Challenge,
                        user_habits: List[Dict[str, Any]],
                        user_goals: List[Dict[str, Any]],
                        roadmap_progress: Dict[str, Any]) -> str:
        """
        Generate recommendation reason.
        """
        reasons = []
        
        # Based on habits
        if user_habits:
            matched_habits = self._match_habits(challenge, user_habits)
            if matched_habits:
                reasons.append(f"Matches your habit: {matched_habits[0]}")
        
        # Based on goals
        if user_goals:
            matched_goals = self._match_goals(challenge, user_goals)
            if matched_goals:
                reasons.append(f"Aligns with your goal: {matched_goals[0]}")
        
        # Based on roadmap
        if roadmap_progress:
            reasons.append("Fits your current roadmap stage")
        
        # General reason
        if not reasons:
            reasons.append(f"Good challenge for your level ({challenge.difficulty.value})")
        
        return "; ".join(reasons[:2])
    
    def _match_habits(self,
                     challenge: Challenge,
                     user_habits: List[Dict[str, Any]]) -> List[str]:
        """
        Get matching habits for a challenge.
        """
        matches = []
        for habit in user_habits:
            if challenge.category.value == habit.get('category', ''):
                matches.append(habit.get('name', ''))
        return matches
    
    def _match_goals(self,
                    challenge: Challenge,
                    user_goals: List[Dict[str, Any]]) -> List[str]:
        """
        Get matching goals for a challenge.
        """
        matches = []
        for goal in user_goals:
            if challenge.category.value == goal.get('category', ''):
                matches.append(goal.get('title', ''))
        return matches
    
    def _match_roadmap(self,
                      challenge: Challenge,
                      roadmap_progress: Dict[str, Any]) -> List[str]:
        """
        Get matching roadmap items for a challenge.
        """
        matches = []
        if roadmap_progress:
            current_stage = roadmap_progress.get('current_stage', 0)
            if current_stage >= 0:
                matches.append(f"Stage {current_stage + 1}")
        return matches
    
    def _determine_priority(self, score: float) -> int:
        """
        Determine recommendation priority.
        """
        if score >= 80:
            return 1  # Highest
        elif score >= 60:
            return 2
        elif score >= 40:
            return 3
        else:
            return 4
    
    def get_top_recommendations(self,
                               recommendations: List[ChallengeRecommendation],
                               limit: int = 5) -> List[ChallengeRecommendation]:
        """
        Get top recommendations.
        
        Args:
            recommendations: List of recommendations
            limit: Number to return
        
        Returns:
            List[ChallengeRecommendation]: Top recommendations
        """
        sorted_recs = sorted(recommendations, key=lambda r: (r.confidence, -r.priority), reverse=True)
        return sorted_recs[:limit]
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
