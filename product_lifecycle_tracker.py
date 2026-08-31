"""
Product Lifecycle Tracker.
Calculates the embodied carbon avoided when a user successfully repairs an item, factoring in the carbon cost of replacement parts.
"""
from typing import Dict, Any, List
from repairability_index_db import RepairabilityIndexDB

class ProductLifecycleTracker:
    """Tracks repair events and calculates the net environmental benefit."""
    
    # Mock carbon cost of common replacement parts (kg CO2e)
    PART_CARBON_COSTS = {
        "battery": 15.0,
        "screen": 25.0,
        "pump": 8.0,
        "seal": 2.0,
        "fabric_patch": 0.5,
        "control_board": 12.0
    }

    def __init__(self):
        self.db = RepairabilityIndexDB()
        self.repair_log: List[Dict[str, Any]] = []

    def log_repair(self, product_key: str, replaced_part: str, successful: bool) -> Dict[str, Any]:
        """
        Logs a repair attempt and calculates the net carbon impact.
        
        Args:
            product_key: The identifier for the product.
            replaced_part: The part that was replaced or fixed.
            successful: Whether the repair was successful.
        """
        details = self.db.get_product_details(product_key)
        if not details:
            raise ValueError(f"Unknown product: {product_key}")
            
        part_carbon_cost = self.PART_CARBON_COSTS.get(replaced_part.lower(), 5.0)
        
        if successful:
            # Net savings = Embodied carbon of new product - Carbon cost of repair parts
            # We assume a successful repair extends life by 1 full lifecycle, avoiding new purchase
            net_carbon_saved = details["embodied_carbon_kg"] - part_carbon_cost
            net_carbon_saved = max(0.0, net_carbon_saved) # Ensure non-negative
            status = "Successful"
        else:
            net_carbon_saved = 0.0
            status = "Failed"
            
        repair_record = {
            "product_name": details["name"],
            "repairability_score": details["repairability_score"],
            "replaced_part": replaced_part,
            "part_carbon_cost_kg": part_carbon_cost,
            "embodied_carbon_avoided_kg": round(net_carbon_saved, 2),
            "status": status
        }
        
        self.repair_log.append(repair_record)
        return repair_record

    def get_cumulative_impact(self) -> Dict[str, Any]:
        """Aggregates the total environmental impact of all logged repairs."""
        successful_repairs = [r for r in self.repair_log if r["status"] == "Successful"]
        
        total_carbon_saved = sum(r["embodied_carbon_avoided_kg"] for r in successful_repairs)
        total_parts_carbon = sum(r["part_carbon_cost_kg"] for r in successful_repairs)
        
        # Mock waste diverted: assume 2kg of e-waste/appliance waste per successful repair
        waste_diverted_kg = len(successful_repairs) * 2.0
        
        return {
            "total_repairs_attempted": len(self.repair_log),
            "successful_repairs": len(successful_repairs),
            "total_carbon_saved_kg": round(total_carbon_saved, 2),
            "total_parts_carbon_kg": round(total_parts_carbon, 2),
            "estimated_waste_diverted_kg": round(waste_diverted_kg, 2)
        }

    def get_repair_resources(self, product_key: str) -> Dict[str, str]:
        """Returns helpful resources for repairing a specific product."""
        details = self.db.get_product_details(product_key)
        if not details:
            return {}
            
        return {
            "guide": details["repair_guide_url"],
            "parts_note": f"Spare parts availability is rated as: {details['parts_availability']}",
            "common_issues": ", ".join(details["common_failures"])
        }
