"""
Unit tests for Advocacy Campaign Generator and Civic Action Tracker.
"""

import pytest
from advocacy_campaign_generator import AdvocacyCampaignGenerator
from civic_action_tracker import CivicActionTracker


def test_generator_campaign_mapping():
    generator = AdvocacyCampaignGenerator(
        user_hotspots=["high_aviation", "high_vehicle"]
    )
    campaigns = generator.generate_personalized_campaigns()

    assert len(campaigns) > 0
    assert any(c["hotspot"] == "High Aviation" for c in campaigns)
    assert any(c["hotspot"] == "High Vehicle" for c in campaigns)
    assert all("policy_issue" in c for c in campaigns)


def test_generator_civic_multiplier():
    generator = AdvocacyCampaignGenerator(user_hotspots=["high_home_energy"])

    assert generator.get_civic_impact_multiplier("sign_petition") == 1.0
    assert generator.get_civic_impact_multiplier("email_representative") == 2.5
    assert generator.get_civic_impact_multiplier("attend_town_hall") == 5.0
    assert generator.get_civic_impact_multiplier("unknown_action") == 1.0


def test_tracker_action_completion():
    tracker = CivicActionTracker(user_hotspots=["high_diet_meat"])

    actions = tracker.get_available_actions()
    assert len(actions) > 0

    first_action = actions[0]
    record = tracker.complete_action(first_action["name"], first_action["action_type"])

    assert record["campaign_name"] == first_action["name"]
    assert record["points_awarded"] > 0.0
    assert tracker.total_civic_impact_points == record["points_awarded"]
    assert tracker.get_tracker_summary()["actions_completed_count"] == 1


def test_tracker_cumulative_points():
    tracker = CivicActionTracker(user_hotspots=["high_aviation"])

    # Complete a low effort action (10 * 1.0 = 10)
    tracker.complete_action("Petition A", "sign_petition")
    # Complete a high effort action (10 * 5.0 = 50)
    tracker.complete_action("Town Hall B", "attend_town_hall")

    summary = tracker.get_tracker_summary()
    assert summary["total_civic_impact_points"] == 60.0
    assert summary["actions_completed_count"] == 2
