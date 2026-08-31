"""
Unit tests for Behavioral Nudge Engine and Loss Aversion Framing.
"""

import unittest
from src.lifestyle.behavioral_nudge_engine import BehavioralNudgeEngine
from src.lifestyle.behavioral_nudge_cards import render_nudge_cards

class TestBehavioralNudgeEngine(unittest.TestCase):

    def setUp(self):
        self.engine = BehavioralNudgeEngine()

    def test_streak_loss_aversion_nudge(self):
        context = {
            "user_id": "user_101",
            "current_weekly_carbon_kg": 65.0,
            "target_weekly_carbon_kg": 50.0,
            "streak_days": 5,
            "primary_transport_mode": "gasoline_car",
            "dietary_preference": "omnivore",
            "monthly_budget_spent": 120.0,
            "monthly_budget_limit": 150.0
        }
        nudges = self.engine.generate_nudges(context)
        self.assertGreater(len(nudges), 0)
        top_nudge = nudges[0]
        self.assertIn("streak", top_nudge["headline"].lower())
        self.assertEqual(top_nudge["framing"], "loss_aversion")

    def test_social_proof_nudge(self):
        context = {
            "user_id": "user_102",
            "current_weekly_carbon_kg": 45.0,
            "target_weekly_carbon_kg": 45.0,
            "streak_days": 1,
            "primary_transport_mode": "bus",
            "dietary_preference": "vegetarian",
            "monthly_budget_spent": 50.0,
            "monthly_budget_limit": 100.0
        }
        nudges = self.engine.generate_nudges(context)
        self.assertTrue(any(n["framing"] == "social_proof" for n in nudges))

    def test_render_cards_html(self):
        nudges = [
            {
                "nudge_id": "nudge_streak_loss",
                "framing": "loss_aversion",
                "headline": "Don't break your streak!",
                "message": "Log your transport today.",
                "potential_carbon_saving_kg": 3.5,
                "potential_cost_saving_usd": 2.0
            }
        ]
        html = render_nudge_cards(nudges)
        self.assertIn("Don't break your streak!", html)
        self.assertIn("loss_aversion", html)

if __name__ == "__main__":
    unittest.main()
