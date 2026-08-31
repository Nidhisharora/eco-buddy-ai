"""
Surplus Logistics Engine.
Calculates the optimal routing and batching of food pickups, estimating fuel emissions vs. landfill methane avoidance.
"""

from typing import Dict, Any, List
from food_rescue_matcher import FoodRescueMatcher


class SurplusLogisticsEngine:
    """Optimizes food rescue logistics and calculates net carbon impact."""

    # Mock emission factors
    TRANSPORT_EMISSIONS_PER_KM = 0.25  # kg CO2e per km for a small van
    LANDFILL_METHANE_AVOIDED_PER_KG_FOOD = (
        0.5  # kg CO2e equivalent avoided per kg of food diverted
    )

    def __init__(self, matcher: FoodRescueMatcher):
        self.matcher = matcher
        # Mock distances between donors and recipients (km)
        self.distances = {
            ("downtown", "downtown_food_bank"): 2.0,
            ("downtown", "westside_shelter"): 8.0,
            ("downtown", "university_fridge"): 5.0,
            ("westside", "downtown_food_bank"): 8.0,
            ("westside", "westside_shelter"): 3.0,
            ("westside", "university_fridge"): 10.0,
            ("university", "downtown_food_bank"): 5.0,
            ("university", "westside_shelter"): 10.0,
            ("university", "university_fridge"): 1.5,
        }

    def calculate_rescue_impact(
        self, donation_id: str, donor_location: str
    ) -> Dict[str, Any]:
        """Calculates the net carbon benefit of rescuing a specific donation."""
        match_result = self.matcher.find_best_match(donation_id)

        if "error" in match_result:
            return match_result

        recipient_id = match_result["matched_recipient_id"]
        weight_kg = match_result["weight_kg"]

        # Estimate transport distance
        distance_key = (donor_location, recipient_id)
        distance_km = self.distances.get(distance_key, 5.0)  # Default 5km if unknown

        # Calculate emissions
        transport_emissions_kg = distance_km * self.TRANSPORT_EMISSIONS_PER_KM
        landfill_avoided_kg = weight_kg * self.LANDFILL_METHANE_AVOIDED_PER_KG_FOOD

        net_carbon_benefit_kg = landfill_avoided_kg - transport_emissions_kg

        return {
            "donation_id": donation_id,
            "recipient": match_result["recipient_name"],
            "weight_kg": weight_kg,
            "distance_km": distance_km,
            "transport_emissions_kg": round(transport_emissions_kg, 2),
            "landfill_avoided_kg": round(landfill_avoided_kg, 2),
            "net_carbon_benefit_kg": round(net_carbon_benefit_kg, 2),
            "is_net_positive": net_carbon_benefit_kg > 0,
        }

    def simulate_community_impact(self) -> Dict[str, Any]:
        """Aggregates the total impact of all matched donations."""
        total_weight_rescued = 0.0
        total_transport_emissions = 0.0
        total_landfill_avoided = 0.0

        for donation in self.matcher.active_donations:
            if donation["status"] == "matched":
                # Mock calculation for historical data
                weight = donation["weight_kg"]
                total_weight_rescued += weight
                total_landfill_avoided += (
                    weight * self.LANDFILL_METHANE_AVOIDED_PER_KG_FOOD
                )
                total_transport_emissions += 3.0  # Mock average 3km trip

        net_community_benefit = total_landfill_avoided - total_transport_emissions

        return {
            "total_donations_matched": len(
                [d for d in self.matcher.active_donations if d["status"] == "matched"]
            ),
            "total_weight_rescued_kg": round(total_weight_rescued, 2),
            "total_transport_emissions_kg": round(total_transport_emissions, 2),
            "total_landfill_avoided_kg": round(total_landfill_avoided, 2),
            "net_community_carbon_benefit_kg": round(net_community_benefit, 2),
        }
