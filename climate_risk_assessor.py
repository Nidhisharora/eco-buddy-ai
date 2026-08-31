"""
Climate Risk Assessor.
Evaluates household vulnerability based on mock geographic data, housing type, and existing infrastructure against projected climate hazards.
"""

from typing import Dict, Any, List


class ClimateRiskAssessor:
    """Assesses multi-hazard climate risks for a specific household."""

    # Mock hazard baseline scores (0-10, 10 being highest risk)
    REGIONAL_HAZARDS = {
        "coastal_florida": {"heat": 8, "flood": 9, "storm": 9, "drought": 4},
        "midwest_plains": {"heat": 6, "flood": 5, "storm": 8, "drought": 7},
        "southwest_desert": {"heat": 9, "flood": 3, "storm": 4, "drought": 9},
        "pacific_northwest": {"heat": 4, "flood": 6, "storm": 7, "drought": 5},
        "northeast_urban": {"heat": 7, "flood": 6, "storm": 6, "drought": 3},
    }

    # Housing type vulnerability multipliers (1.0 is baseline)
    HOUSING_MULTIPLIERS = {
        "mobile_home": {"heat": 1.3, "flood": 1.5, "storm": 1.8, "drought": 1.0},
        "older_wood_frame": {"heat": 1.2, "flood": 1.2, "storm": 1.4, "drought": 1.1},
        "modern_built": {"heat": 0.9, "flood": 0.9, "storm": 0.8, "drought": 0.9},
        "concrete_masonry": {"heat": 0.8, "flood": 1.1, "storm": 0.7, "drought": 0.8},
    }

    def __init__(
        self, region: str, housing_type: str, has_ac: bool, has_backup_power: bool
    ):
        self.region = region.lower().replace(" ", "_")
        self.housing_type = housing_type.lower().replace(" ", "_")
        self.has_ac = has_ac
        self.has_backup_power = has_backup_power

        if self.region not in self.REGIONAL_HAZARDS:
            self.region = "midwest_plains"
        if self.housing_type not in self.HOUSING_MULTIPLIERS:
            self.housing_type = "older_wood_frame"

    def assess_risks(self) -> Dict[str, Any]:
        """Calculates the vulnerability score for each hazard category."""
        base_hazards = self.REGIONAL_HAZARDS[self.region]
        multipliers = self.HOUSING_MULTIPLIERS[self.housing_type]

        risk_scores = {}
        for hazard, base_score in base_hazards.items():
            multiplier = multipliers[hazard]

            if hazard == "heat" and self.has_ac:
                multiplier *= 0.8
            if hazard == "storm" and self.has_backup_power:
                multiplier *= 0.8

            final_score = min(10.0, max(0.0, base_score * multiplier))
            risk_scores[hazard] = round(final_score, 1)

        avg_risk = sum(risk_scores.values()) / len(risk_scores)
        base_resilience_score = round(max(0.0, 100.0 - (avg_risk * 10)), 1)

        return {
            "region": self.region.replace("_", " ").title(),
            "housing_type": self.housing_type.replace("_", " ").title(),
            "hazard_scores": risk_scores,
            "base_resilience_score": base_resilience_score,
            "overall_risk_level": self._categorize_risk(avg_risk),
        }

    def _categorize_risk(self, avg_risk: float) -> str:
        if avg_risk < 4.0:
            return "Low Risk"
        elif avg_risk < 6.5:
            return "Moderate Risk"
        elif avg_risk < 8.5:
            return "High Risk"
        else:
            return "Severe Risk"
