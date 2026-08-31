"""
Unit tests for Dynamic Carbon Handprint & Positive Impact Acceleration Engine.
"""

import unittest
from src.carbon.carbon_handprint_engine import CarbonHandprintEngine
from src.carbon.carbon_handprint_cards import render_handprint_card

class TestCarbonHandprintEngine(unittest.TestCase):

    def setUp(self):
        self.engine = CarbonHandprintEngine()

    def test_calculate_solar_sharing_handprint(self):
        action = {
            "action_id": "act_solar_01",
            "action_type": "solar_sharing",
            "scale_units": 100.0,  # 100 kWh
            "beneficiaries_count": 4
        }
        res = self.engine.calculate_handprint(action)
        self.assertEqual(res["direct_avoided_carbon_kg"], 45.0)
        self.assertEqual(res["indirect_handprint_multiplier"], 1.6)
        self.assertEqual(res["total_handprint_impact_kg"], 72.0)

    def test_calculate_policy_advocacy(self):
        action = {
            "action_id": "act_advocacy_02",
            "action_type": "public_policy_advocacy",
            "scale_units": 5.0,  # 5 hours
            "beneficiaries_count": 10
        }
        res = self.engine.calculate_handprint(action)
        self.assertGreater(res["total_handprint_impact_kg"], res["direct_avoided_carbon_kg"])

    def test_render_cards_html(self):
        result = {
            "direct_avoided_carbon_kg": 45.0,
            "indirect_handprint_multiplier": 1.6,
            "total_handprint_impact_kg": 72.0
        }
        html = render_handprint_card(result)
        self.assertIn("Positive Carbon Handprint", html)
        self.assertIn("72.0", html)

if __name__ == "__main__":
    unittest.main()
