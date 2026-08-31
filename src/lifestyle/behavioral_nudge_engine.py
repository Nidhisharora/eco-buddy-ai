"""
Behavioral Nudge Engine implementing loss aversion, social proof, and pre-commitment framing.
"""

from typing import List, Dict, Any
from src.lifestyle.behavioral_nudge_types import NudgeContext, NudgeRecommendation
from src.lifestyle.behavioral_nudge_db import NUDGE_TEMPLATE_CATALOG

class BehavioralNudgeEngine:
    """
    Evaluates user sustainability context and generates personalized behavioral nudges
    leveraging prospect theory and behavioral economics principles.
    """

    def __init__(self, catalog: List[Dict[str, Any]] = None):
        self.catalog = catalog or NUDGE_TEMPLATE_CATALOG

    def generate_nudges(self, context: NudgeContext) -> List[NudgeRecommendation]:
        """
        Evaluates context against nudge rules and returns top prioritized nudges.
        """
        recommendations: List[NudgeRecommendation] = []
        excess_carbon = max(0.0, context.get("current_weekly_carbon_kg", 0) - context.get("target_weekly_carbon_kg", 0))
        money_at_risk = max(0.0, context.get("monthly_budget_spent", 0) - (context.get("monthly_budget_limit", 0) * 0.8))

        for template in self.catalog:
            try:
                if template["trigger"](context):
                    carb_saving = template["carbon_saving_factor"] * (1.0 + (excess_carbon / 50.0))
                    cost_saving = template["cost_saving_factor"] * (1.0 + (money_at_risk / 20.0))

                    headline = template["headline_template"].format(
                        streak_days=context.get("streak_days", 0),
                        money_at_risk=money_at_risk
                    )
                    message = template["message_template"].format(
                        excess_carbon=excess_carbon,
                        potential_carbon=carb_saving
                    )

                    score = 0.85 if template["framing"] == "loss_aversion" else 0.75

                    recommendations.append({
                        "nudge_id": template["nudge_id"],
                        "category": template["category"],
                        "framing": template["framing"],
                        "headline": headline,
                        "message": message,
                        "potential_carbon_saving_kg": round(carb_saving, 2),
                        "potential_cost_saving_usd": round(cost_saving, 2),
                        "action_url": f"/app/actions/{template['category']}",
                        "confidence_score": score,
                    })
            except Exception:
                continue

        # Sort by confidence and potential impact
        recommendations.sort(key=lambda x: (x["confidence_score"], x["potential_carbon_saving_kg"]), reverse=True)
        return recommendations
