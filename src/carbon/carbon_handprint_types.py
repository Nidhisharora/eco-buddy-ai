"""
Type definitions for Dynamic Carbon Handprint & Positive Impact Acceleration Engine.
"""

from typing import TypedDict, List, Dict, Any

class PositiveActionInput(TypedDict):
    action_id: str
    action_type: str  # 'solar_sharing', 'community_mentoring', 'tree_planting', 'public_policy_advocacy'
    scale_units: float  # e.g., kWh shared, hours advocated, trees planted
    beneficiaries_count: int

class HandprintMetricResult(TypedDict):
    action_id: str
    direct_avoided_carbon_kg: float
    indirect_handprint_multiplier: float
    total_handprint_impact_kg: float
    handprint_score: float
