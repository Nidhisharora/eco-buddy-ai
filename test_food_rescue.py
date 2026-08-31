"""
Unit tests for Food Rescue Matcher and Surplus Logistics Engine.
"""

import pytest
from food_rescue_matcher import FoodRescueMatcher
from surplus_logistics_engine import SurplusLogisticsEngine


def test_matcher_registration():
    matcher = FoodRescueMatcher()
    don_id = matcher.register_donation("Test Bakery", "bakery", 10.0, 24.0)

    assert don_id.startswith("don_")
    pending = matcher.get_pending_donations()
    assert len(pending) == 1
    assert pending[0]["item_type"] == "bakery"


def test_matcher_successful_match():
    matcher = FoodRescueMatcher()
    don_id = matcher.register_donation("Test Farm", "produce", 50.0, 48.0)

    # Westside shelter accepts produce and has 200kg capacity
    match = matcher.find_best_match(don_id)

    assert "error" not in match
    assert match["matched_recipient_id"] in [
        "westside_shelter",
        "downtown_food_bank",
        "university_fridge",
    ]
    assert matcher.active_donations[0]["status"] == "matched"


def test_matcher_no_capacity():
    matcher = FoodRescueMatcher()
    # Try to donate 1000kg, which exceeds all capacities
    don_id = matcher.register_donation("Huge Wholesaler", "canned", 1000.0, 100.0)

    match = matcher.find_best_match(don_id)
    assert "error" in match
    assert "No suitable recipient found" in match["error"]


def test_logistics_impact_calculation():
    matcher = FoodRescueMatcher()
    logistics = SurplusLogisticsEngine(matcher)

    don_id = matcher.register_donation("Downtown Cafe", "bakery", 10.0, 12.0)

    impact = logistics.calculate_rescue_impact(don_id, "downtown")

    assert "error" not in impact
    assert impact["weight_kg"] == 10.0
    # Landfill avoided: 10 * 0.5 = 5.0
    assert impact["landfill_avoided_kg"] == 5.0
    # Transport: mock distance 2.0 * 0.25 = 0.5
    assert impact["transport_emissions_kg"] == 0.5
    # Net: 5.0 - 0.5 = 4.5
    assert impact["net_carbon_benefit_kg"] == 4.5
    assert impact["is_net_positive"] is True


def test_logistics_community_simulation():
    matcher = FoodRescueMatcher()
    logistics = SurplusLogisticsEngine(matcher)

    matcher.register_donation("Donor 1", "produce", 20.0, 24.0)
    matcher.find_best_match("don_1")

    matcher.register_donation("Donor 2", "bakery", 15.0, 12.0)
    matcher.find_best_match("don_2")

    sim = logistics.simulate_community_impact()

    assert sim["total_donations_matched"] == 2
    assert sim["total_weight_rescued_kg"] == 35.0
    assert sim["total_landfill_avoided_kg"] == 17.5  # 35 * 0.5
