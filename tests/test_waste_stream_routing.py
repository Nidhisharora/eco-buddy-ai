"""
Unit tests for Smart Waste Stream Circularity Routing Engine.
"""

import unittest
from src.environment.waste_stream_routing_engine import WasteStreamRoutingEngine
from src.environment.waste_stream_routing_cards import render_waste_routing_card

class TestWasteStreamRoutingEngine(unittest.TestCase):

    def setUp(self):
        self.engine = WasteStreamRoutingEngine()

    def test_route_electronics(self):
        item = {
            "item_id": "item_laptop_01",
            "material_type": "electronics",
            "weight_kg": 2.5,
            "condition": "working",
            "location_zip": "90210"
        }
        res = self.engine.route_waste_item(item)
        self.assertEqual(res["best_destination"]["facility_id"], "fac_e_waste_refurb")
        self.assertGreater(res["net_carbon_benefit_kg"], 0)
        self.assertGreater(res["expected_payout_usd"], 0)

    def test_route_fallback(self):
        item = {
            "item_id": "item_unknown_01",
            "material_type": "hazardous_glass",
            "weight_kg": 1.0,
            "condition": "scrap",
            "location_zip": "90210"
        }
        res = self.engine.route_waste_item(item)
        self.assertEqual(res["best_destination"]["facility_id"], "fac_generic_recycling")

    def test_render_cards_html(self):
        result = {
            "item_id": "item_1",
            "best_destination": {
                "facility_name": "TechCycle Refurbishment Hub",
                "processing_type": "refurbish"
            },
            "net_carbon_benefit_kg": 42.5,
            "expected_payout_usd": 6.25
        }
        html = render_waste_routing_card(result)
        self.assertIn("TechCycle Refurbishment Hub", html)
        self.assertIn("42.5", html)

if __name__ == "__main__":
    unittest.main()
