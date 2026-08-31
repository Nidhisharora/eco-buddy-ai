"""
Circular waste processing facility database & material recovery metrics.
"""

CIRCULAR_FACILITIES_CATALOG = [
    {
        "facility_id": "fac_e_waste_refurb",
        "facility_name": "TechCycle Refurbishment Hub",
        "accepted_materials": ["electronics"],
        "processing_type": "refurbish",
        "distance_km": 4.5,
        "carbon_avoided_kg_per_kg": 18.5,
        "payout_usd_per_kg": 2.50
    },
    {
        "facility_id": "fac_textile_upcycle",
        "facility_name": "EcoThread Fabric Upcyclers",
        "accepted_materials": ["textile"],
        "processing_type": "upcycle",
        "distance_km": 6.2,
        "carbon_avoided_kg_per_kg": 8.2,
        "payout_usd_per_kg": 0.80
    },
    {
        "facility_id": "fac_city_compost",
        "facility_name": "Municipal Bio-Compost Plant",
        "accepted_materials": ["organic"],
        "processing_type": "compost",
        "distance_km": 2.1,
        "carbon_avoided_kg_per_kg": 1.4,
        "payout_usd_per_kg": 0.05
    }
]
