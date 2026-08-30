"""
Smart Waste Stream Circularity Routing Engine.
"""

from typing import List, Dict, Any
from src.environment.waste_stream_routing_types import WasteItemInput, CircularDestination, WasteRoutingResult
from src.environment.waste_stream_routing_db import CIRCULAR_FACILITIES_CATALOG

class WasteStreamRoutingEngine:
    """
    Optimizes municipal/household waste diversion to circular processing hubs, maximizing carbon offset
    and financial payout while minimizing logistics transport emissions.
    """

    def __init__(self, catalog: List[CircularDestination] = None):
        self.catalog = catalog or CIRCULAR_FACILITIES_CATALOG

    def route_waste_item(self, item: WasteItemInput) -> WasteRoutingResult:
        material = item["material_type"]
        weight = item["weight_kg"]

        matching_facs = [f for f in self.catalog if material in f["accepted_materials"]]

        if not matching_facs:
            # Fallback facility
            best_fac = {
                "facility_id": "fac_generic_recycling",
                "facility_name": "General Recycling Depot",
                "accepted_materials": [material],
                "processing_type": "recycle",
                "distance_km": 10.0,
                "carbon_avoided_kg_per_kg": 0.5,
                "payout_usd_per_kg": 0.0
            }
        else:
            # Rank facilities by net carbon benefit (avoided carbon - transport carbon)
            best_fac = max(matching_facs, key=lambda f: (f["carbon_avoided_kg_per_kg"] * weight) - (f["distance_km"] * 0.1))

        transport_emissions = best_fac["distance_km"] * 0.12  # kg CO2/km transport
        gross_avoided = best_fac["carbon_avoided_kg_per_kg"] * weight
        net_carbon = gross_avoided - transport_emissions
        payout = best_fac["payout_usd_per_kg"] * weight

        return {
            "item_id": item["item_id"],
            "best_destination": best_fac,
            "net_carbon_benefit_kg": round(net_carbon, 2),
            "expected_payout_usd": round(payout, 2),
            "recycling_tier": "Tier-1 Circular Reuse" if best_fac["processing_type"] in ["refurbish", "upcycle"] else "Tier-2 Material Recovery"
        }
