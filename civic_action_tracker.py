"""
Civic Action Tracker.
Manages a registry of actionable civic tasks and assigns "Civic Impact" points upon completion.
"""

from typing import Dict, Any, List
from advocacy_campaign_generator import AdvocacyCampaignGenerator


class CivicActionTracker:
    """Tracks user civic engagement and calculates their cumulative Civic Impact score."""

    def __init__(self, user_hotspots: List[str]):
        self.generator = AdvocacyCampaignGenerator(user_hotspots)
        self.completed_actions: List[Dict[str, Any]] = []
        self.total_civic_impact_points = 0.0

    def get_available_actions(self) -> List[Dict[str, Any]]:
        """Returns all available campaigns for the user's hotspots."""
        return self.generator.generate_personalized_campaigns()

    def complete_action(self, campaign_name: str, action_type: str) -> Dict[str, Any]:
        """
        Marks a civic action as completed and awards impact points.
        """
        multiplier = self.generator.get_civic_impact_multiplier(action_type)
        points_awarded = 10.0 * multiplier  # Base 10 points * effort multiplier

        action_record = {
            "campaign_name": campaign_name,
            "action_type": action_type,
            "points_awarded": points_awarded,
            "timestamp": "Just now",  # Mock timestamp
        }

        self.completed_actions.append(action_record)
        self.total_civic_impact_points += points_awarded

        return action_record

    def get_tracker_summary(self) -> Dict[str, Any]:
        """Returns a summary of the user's civic engagement."""
        return {
            "total_civic_impact_points": round(self.total_civic_impact_points, 1),
            "actions_completed_count": len(self.completed_actions),
            "recent_actions": self.completed_actions[-5:],  # Last 5 actions
        }
