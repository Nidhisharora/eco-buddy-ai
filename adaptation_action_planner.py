"""
Adaptation Action Planner.
Generates prioritized, cost-effective adaptation recommendations and calculates their risk-reduction impact.
"""

from typing import Dict, Any, List


class AdaptationActionPlanner:
    """Manages and calculates the impact of household climate adaptation actions."""

    ADAPTATION_ACTIONS = {
        "rain_barrel": {
            "name": "Install Rain Barrels",
            "targets": ["flood", "drought"],
            "cost_range": "$50 - $150",
            "effort": "Low",
            "risk_reduction_pts": 0.5,
            "description": "Captures roof runoff to reduce local flooding and provide water for drought periods.",
        },
        "weatherstripping": {
            "name": "Upgrade Weatherstripping & Insulation",
            "targets": ["heat", "storm"],
            "cost_range": "$100 - $300",
            "effort": "Medium",
            "risk_reduction_pts": 0.8,
            "description": "Seals gaps to maintain indoor temperatures during extreme heat or cold storms.",
        },
        "emergency_kit": {
            "name": "Build a 7-Day Emergency Kit",
            "targets": ["storm", "flood", "heat", "drought"],
            "cost_range": "$100 - $200",
            "effort": "Low",
            "risk_reduction_pts": 1.0,
            "description": "Ensures survival and comfort during extended power or water outages.",
        },
        "shade_trees": {
            "name": "Plant Deciduous Shade Trees",
            "targets": ["heat", "drought"],
            "cost_range": "$150 - $500",
            "effort": "High",
            "risk_reduction_pts": 1.2,
            "description": "Provides natural cooling in summer and windbreaks in winter.",
        },
        "sump_pump": {
            "name": "Install Battery-Backed Sump Pump",
            "targets": ["flood", "storm"],
            "cost_range": "$1000 - $2000",
            "effort": "High",
            "risk_reduction_pts": 1.5,
            "description": "Prevents basement flooding during heavy rainfall or storm surges.",
        },
    }

    def __init__(self, hazard_scores: Dict[str, float], base_resilience_score: float):
        self.hazard_scores = hazard_scores
        self.base_resilience_score = base_resilience_score
        self.completed_actions: List[str] = []

    def get_recommended_actions(self) -> List[Dict[str, Any]]:
        """Prioritizes actions based on the household's highest risk hazards."""
        recommendations = []
        sorted_hazards = sorted(
            self.hazard_scores.items(), key=lambda x: x[1], reverse=True
        )
        top_hazards = [h[0] for h in sorted_hazards[:2]]  # Top 2 hazards

        for action_key, details in self.ADAPTATION_ACTIONS.items():
            if action_key in self.completed_actions:
                continue

            # Check if action targets any of the top hazards
            if any(target in top_hazards for target in details["targets"]):
                recommendations.append(
                    {
                        "key": action_key,
                        **details,
                        "relevance": "High"
                        if any(target in top_hazards for target in details["targets"])
                        else "Medium",
                    }
                )

        # Sort by risk reduction points descending
        return sorted(
            recommendations, key=lambda x: x["risk_reduction_pts"], reverse=True
        )

    def complete_action(self, action_key: str) -> bool:
        """Marks an action as completed and updates the resilience score."""
        if (
            action_key not in self.ADAPTATION_ACTIONS
            or action_key in self.completed_actions
        ):
            return False

        self.completed_actions.append(action_key)
        return True

    def calculate_current_resilience_score(self) -> float:
        """Calculates the updated resilience score based on completed actions."""
        total_reduction = sum(
            self.ADAPTATION_ACTIONS[key]["risk_reduction_pts"]
            for key in self.completed_actions
        )

        # Each point of risk reduction adds to the resilience score (max 100)
        new_score = min(100.0, self.base_resilience_score + (total_reduction * 5))
        return round(new_score, 1)

    def get_action_summary(self) -> Dict[str, Any]:
        """Returns a summary of the adaptation plan."""
        return {
            "base_resilience_score": self.base_resilience_score,
            "current_resilience_score": self.calculate_current_resilience_score(),
            "completed_actions": self.completed_actions,
            "pending_recommendations": self.get_recommended_actions(),
        }
