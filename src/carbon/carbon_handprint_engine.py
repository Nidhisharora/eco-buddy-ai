"""
Dynamic Carbon Handprint & Positive Impact Acceleration Engine.
"""

from typing import List, Dict, Any
from src.carbon.carbon_handprint_types import PositiveActionInput, HandprintMetricResult
from src.carbon.carbon_handprint_db import HANDPRINT_FACTORS_CATALOG

class CarbonHandprintEngine:
    """
    Calculates positive environmental impact (Handprint) beyond negative footprint reduction.
    Measures ripple effects of community climate actions, mentoring, and clean energy sharing.
    """

    def __init__(self, catalog: Dict[str, Any] = None):
        self.catalog = catalog or HANDPRINT_FACTORS_CATALOG

    def calculate_handprint(self, action: PositiveActionInput) -> HandprintMetricResult:
        action_type = action["action_type"]
        scale = action["scale_units"]
        beneficiaries = action["beneficiaries_count"]

        factor_data = self.catalog.get(action_type, {
            "base_avoided_kg_per_unit": 1.0,
            "ripple_multiplier_per_beneficiary": 0.10
        })

        direct_avoided = scale * factor_data["base_avoided_kg_per_unit"]
        multiplier = 1.0 + (beneficiaries * factor_data["ripple_multiplier_per_beneficiary"])
        total_handprint = direct_avoided * multiplier
        score = total_handprint / 10.0

        return {
            "action_id": action["action_id"],
            "direct_avoided_carbon_kg": round(direct_avoided, 2),
            "indirect_handprint_multiplier": round(multiplier, 2),
            "total_handprint_impact_kg": round(total_handprint, 2),
            "handprint_score": round(score, 2)
        }
