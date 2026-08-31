"""Tests for the versioned recommendation decision engine."""

from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from src.ai.recommendation_decision_engine import (
    LATEST_RULE_VERSION,
    RULE_SETS,
    RecommendationDecision,
    evaluate_decision_effectiveness,
    generate_recommendation_decisions,
    personalize_wording,
)


def sample_inputs():
    return {
        "energy_usage_kwh": 5000,
        "transport_emissions_kg": 2400,
        "food_emissions_kg": 1200,
        "water_usage_liters": 50000,
    }


def test_rule_sets_are_versioned():
    assert "v1" in RULE_SETS
    assert "v2" in RULE_SETS
    assert LATEST_RULE_VERSION in RULE_SETS


def test_same_inputs_and_version_produce_identical_decisions():
    inputs = sample_inputs()

    first = generate_recommendation_decisions(inputs, rule_version="v1")
    second = generate_recommendation_decisions(inputs, rule_version="v1")

    assert [decision.to_dict() for decision in first] == [
        decision.to_dict() for decision in second
    ]


def test_decisions_record_rule_version():
    decisions = generate_recommendation_decisions(
        sample_inputs(),
        rule_version="v1",
    )

    assert decisions
    assert all(decision.rule_version == "v1" for decision in decisions)


def test_decisions_record_input_metrics():
    inputs = sample_inputs()

    decisions = generate_recommendation_decisions(
        inputs,
        rule_version="v1",
    )

    assert decisions
    for decision in decisions:
        assert decision.input_metrics
        assert isinstance(decision.input_metrics, dict)


def test_decisions_record_thresholds_evaluated():
    decisions = generate_recommendation_decisions(
        sample_inputs(),
        rule_version="v1",
    )

    assert decisions
    for decision in decisions:
        assert isinstance(decision.thresholds_evaluated, dict)


def test_selected_decisions_have_expected_impact_and_reason():
    decisions = generate_recommendation_decisions(
        sample_inputs(),
        rule_version="v1",
    )

    selected = [decision for decision in decisions if decision.status == "selected"]

    assert selected

    for decision in selected:
        assert decision.expected_impact is not None
        assert decision.reason


def test_rejected_decisions_have_rejection_reason():
    inputs = {
        "energy_usage_kwh": 0,
        "transport_emissions_kg": 0,
        "food_emissions_kg": 0,
        "water_usage_liters": 0,
    }

    decisions = generate_recommendation_decisions(
        inputs,
        rule_version="v1",
    )

    rejected = [decision for decision in decisions if decision.status == "rejected"]

    assert rejected

    for decision in rejected:
        assert decision.reason


def test_generation_timestamp_is_recorded():
    decisions = generate_recommendation_decisions(
        sample_inputs(),
        rule_version="v1",
    )

    assert decisions

    for decision in decisions:
        assert decision.generated_at
        datetime.fromisoformat(decision.generated_at)


def test_personalization_only_changes_wording():
    decisions = generate_recommendation_decisions(
        sample_inputs(),
        rule_version="v1",
    )

    decision = decisions[0]

    personalized = personalize_wording(
        decision,
        title="My Personalized Recommendation",
        description="A personalized explanation.",
    )

    assert personalized.title == "My Personalized Recommendation"
    assert personalized.description == "A personalized explanation."

    assert personalized.rule_id == decision.rule_id
    assert personalized.rule_version == decision.rule_version
    assert personalized.input_metrics == decision.input_metrics
    assert personalized.thresholds_evaluated == decision.thresholds_evaluated
    assert personalized.expected_impact == decision.expected_impact
    assert personalized.status == decision.status
    assert personalized.reason == decision.reason
    assert personalized.generated_at == decision.generated_at


def test_recommendation_decision_is_immutable():
    decisions = generate_recommendation_decisions(
        sample_inputs(),
        rule_version="v1",
    )

    decision = decisions[0]

    with pytest.raises(FrozenInstanceError):
        decision.status = "rejected"


def test_decision_effectiveness_compares_expected_and_actual_impact():
    decisions = generate_recommendation_decisions(
        sample_inputs(),
        rule_version="v1",
    )

    decision = next(
        decision
        for decision in decisions
        if decision.status == "selected"
    )

    result = evaluate_decision_effectiveness(
        decision,
        actual_impact=decision.expected_impact,
    )

    assert isinstance(result, dict)
    assert result["expected_impact"] == decision.expected_impact
    assert result["actual_impact"] == decision.expected_impact
    assert result["difference"] == 0