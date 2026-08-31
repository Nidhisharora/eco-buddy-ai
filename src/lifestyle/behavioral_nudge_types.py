"""
Type definitions for Behavioral Nudge Engine & Loss Aversion Framing.
"""

from typing import TypedDict, List, Optional, Dict, Any

class NudgeContext(TypedDict):
    user_id: str
    current_weekly_carbon_kg: float
    target_weekly_carbon_kg: float
    streak_days: int
    primary_transport_mode: str
    dietary_preference: str
    monthly_budget_spent: float
    monthly_budget_limit: float

class NudgeRecommendation(TypedDict):
    nudge_id: str
    category: str
    framing: str  # 'loss_aversion', 'social_proof', 'commitment_device', 'gain_framing'
    headline: str
    message: str
    potential_carbon_saving_kg: float
    potential_cost_saving_usd: float
    action_url: str
    confidence_score: float
