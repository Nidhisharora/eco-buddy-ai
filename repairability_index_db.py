"""
Repairability Index Database.
Manages a dataset of common consumer electronics and appliances, including repairability scores, common failure points, and spare parts availability.
"""
from typing import Dict, Any, Optional

class RepairabilityIndexDB:
    """Provides access to product repairability metrics and resources."""
    
    # Mock dataset: repairability_score (1-10, 10 is easiest), embodied_carbon_kg, common_failures
    PRODUCT_DATABASE = {
        "framework_laptop": {
            "name": "Framework Laptop",
            "category": "electronics",
            "repairability_score": 9.5,
            "embodied_carbon_kg": 250.0,
            "common_failures": ["battery degradation", "screen hinge", "keyboard spill"],
            "parts_availability": "Excellent",
            "repair_guide_url": "https://frame.work/repair"
        },
        "iphone_standard": {
            "name": "Standard Smartphone",
            "category": "electronics",
            "repairability_score": 4.0,
            "embodied_carbon_kg": 85.0,
            "common_failures": ["cracked screen", "battery degradation", "charging port"],
            "parts_availability": "Moderate",
            "repair_guide_url": "https://www.ifixit.com/Device/Smartphone"
        },
        "washing_machine_basic": {
            "name": "Basic Washing Machine",
            "category": "appliance",
            "repairability_score": 7.0,
            "embodied_carbon_kg": 400.0,
            "common_failures": ["drain pump clog", "door seal wear", "control board"],
            "parts_availability": "Good",
            "repair_guide_url": "https://www.ifixit.com/Appliance"
        },
        "fast_fashion_shirt": {
            "name": "Fast Fashion T-Shirt",
            "category": "clothing",
            "repairability_score": 3.0,
            "embodied_carbon_kg": 15.0,
            "common_failures": ["seam ripping", "fabric thinning", "stain"],
            "parts_availability": "N/A (Use scrap fabric)",
            "repair_guide_url": "https://www.visiblemending.com/"
        },
        "dyson_vacuum": {
            "name": "Premium Cordless Vacuum",
            "category": "appliance",
            "repairability_score": 5.5,
            "embodied_carbon_kg": 60.0,
            "common_failures": ["battery failure", "clogged filter", "brush roll jam"],
            "parts_availability": "Moderate",
            "repair_guide_url": "https://www.ifixit.com/Appliance/Vacuum_Cleaner"
        }
    }

    def __init__(self):
        self.database = self.PRODUCT_DATABASE

    def get_product_details(self, product_key: str) -> Optional[Dict[str, Any]]:
        """Retrieves repairability details for a specific product."""
        return self.database.get(product_key.lower())

    def get_all_products(self) -> list:
        """Returns a list of all available product keys."""
        return list(self.database.keys())

    def get_product_display_name(self, product_key: str) -> str:
        """Returns the human-readable name of the product."""
        details = self.get_product_details(product_key)
        return details["name"] if details else product_key.replace("_", " ").title()

    def get_products_by_category(self, category: str) -> list:
        """Filters products by category (e.g., 'electronics', 'appliance')."""
        return [key for key, data in self.database.items() if data["category"].lower() == category.lower()]
