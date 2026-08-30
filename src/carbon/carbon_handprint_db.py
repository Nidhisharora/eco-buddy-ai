"""
Database and multiplication factors for positive carbon handprint calculation.
"""

HANDPRINT_FACTORS_CATALOG = {
    "solar_sharing": {
        "base_avoided_kg_per_unit": 0.45,  # per kWh shared
        "ripple_multiplier_per_beneficiary": 0.15
    },
    "community_mentoring": {
        "base_avoided_kg_per_unit": 12.0,  # per hour mentoring
        "ripple_multiplier_per_beneficiary": 0.25
    },
    "tree_planting": {
        "base_avoided_kg_per_unit": 22.0,  # per tree annual
        "ripple_multiplier_per_beneficiary": 0.05
    },
    "public_policy_advocacy": {
        "base_avoided_kg_per_unit": 50.0,  # per campaign hour
        "ripple_multiplier_per_beneficiary": 0.50
    }
}
