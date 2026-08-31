"""
Unit tests for Corporate Scope 3 Value-Chain Insetting & Intervention Exchange Engine.
"""

import unittest
from src.business.scope3_insetting_engine import Scope3InsettingEngine
from src.business.scope3_insetting_cards import render_insetting_portfolio_summary

class TestScope3InsettingEngine(unittest.TestCase):

    def setUp(self):
        self.engine = Scope3InsettingEngine()

    def test_optimize_insetting_portfolio(self):
        request = {
            "company_id": "corp_88",
            "target_scope3_reduction_tco2e": 3000.0,
            "max_budget_usd": 150000.0,
            "preferred_tiers": [1, 2, 3]
        }
        result = self.engine.optimize_insetting_portfolio(request)
        self.assertGreater(len(result["selected_projects"]), 0)
        self.assertLessEqual(result["total_budget_allocated_usd"], 150000.0)
        self.assertGreater(result["total_annual_abatement_tco2e"], 0)

    def test_tier_filtering(self):
        request = {
            "company_id": "corp_89",
            "target_scope3_reduction_tco2e": 2000.0,
            "max_budget_usd": 200000.0,
            "preferred_tiers": [1]
        }
        result = self.engine.optimize_insetting_portfolio(request)
        for proj in result["selected_projects"]:
            self.assertEqual(proj["tier_level"], 1)

    def test_render_cards_html(self):
        result = {
            "total_budget_allocated_usd": 130000.0,
            "total_annual_abatement_tco2e": 3150.0,
            "target_completion_percentage": 100.0
        }
        html = render_insetting_portfolio_summary(result)
        self.assertIn("Scope 3 Supply Chain Insetting", html)
        self.assertIn("130000.0", html)

if __name__ == "__main__":
    unittest.main()
