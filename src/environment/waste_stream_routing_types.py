"""
Type definitions for Smart Waste Stream Circularity Routing Engine.
"""

from typing import TypedDict, List, Dict, Any

class WasteItemInput(TypedDict):
    item_id: str
    material_type: str  # 'electronics', 'textile', 'organic', 'plastic', 'metal'
    weight_kg: float
    condition: str  # 'working', 'repairable', 'scrap'
    location_zip: str

class CircularDestination(TypedDict):
    facility_id: str
    facility_name: str
    accepted_materials: List[str]
    processing_type: str  # 'refurbish', 'recycle', 'compost', 'upcycle'
    distance_km: float
    carbon_avoided_kg_per_kg: float
    payout_usd_per_kg: float

class WasteRoutingResult(TypedDict):
    item_id: str
    best_destination: CircularDestination
    net_carbon_benefit_kg: float
    expected_payout_usd: float
    recycling_tier: str
