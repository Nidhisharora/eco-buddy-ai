"""
Unit tests for Climate Risk Assessor and Adaptation Action Planner.
"""

import pytest
from climate_risk_assessor import ClimateRiskAssessor
from adaptation_action_planner import AdaptationActionPlanner


def test_risk_assessor_base():
    assessor = ClimateRiskAssessor(
        region="Southwest Desert",
        housing_type="Modern Built",
        has_ac=True,
        has_backup_power=False,
    )
    result = assessor.assess_risks()

    assert result["region"] == "Southwest Desert"
    assert result["housing_type"] == "Modern Built"
    # Heat base is 9, modern built multiplier is 0.9, AC mitigation is 0.8 -> 9 * 0.9 * 0.8 = 6.48
    assert result["hazard_scores"]["heat"] == 6.5
    assert result["base_resilience_score"] > 0.0


def test_risk_assessor_default_fallback():
    assessor = ClimateRiskAssessor(
        region="Unknown Region",
        housing_type="Unknown Type",
        has_ac=False,
        has_backup_power=False,
    )
    result = assessor.assess_risks()

    assert result["region"] == "Midwest Plains"
    assert result["housing_type"] == "Older Wood Frame"


def test_adaptation_planner_recommendations():
    assessor = ClimateRiskAssessor("Coastal Florida", "Mobile Home", False, False)
    risk_data = assessor.assess_risks()

    planner = AdaptationActionPlanner(
        hazard_scores=risk_data["hazard_scores"],
        base_resilience_score=risk_data["base_resilience_score"],
    )

    recs = planner.get_recommended_actions()
    assert len(recs) > 0
    # Storm and flood are highest in Coastal Florida, so sump_pump or emergency_kit should be high
    assert any(r["key"] in ["sump_pump", "emergency_kit"] for r in recs)


def test_adaptation_planner_completion():
    assessor = ClimateRiskAssessor("Midwest Plains", "Older Wood Frame", True, True)
    risk_data = assessor.assess_risks()

    planner = AdaptationActionPlanner(
        hazard_scores=risk_data["hazard_scores"],
        base_resilience_score=risk_data["base_resilience_score"],
    )

    base_score = planner.calculate_current_resilience_score()

    # Complete an action
    success = planner.complete_action("weatherstripping")
    assert success is True

    new_score = planner.calculate_current_resilience_score()
    # weatherstripping gives 0.8 pts * 5 = 4.0 increase
    assert new_score == base_score + 4.0

    # Try completing same action again
    success_again = planner.complete_action("weatherstripping")
    assert success_again is False
