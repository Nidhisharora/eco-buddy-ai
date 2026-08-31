"""Tests for goal progress reconciliation."""
import pytest
from datetime import datetime

from src.utils.goal_progress_reconciliation import (
    GoalProgressReconciler,
    GoalProgressRecord,
    SourceType,
    ChangeType,
    SourceChange,
    get_goal_progress_reconciler,
)


@pytest.fixture
def reconciler():
    return GoalProgressReconciler()


def test_register_goal_dependency():
    reconciler = GoalProgressReconciler()
    reconciler.register_goal_dependency(
        goal_id="goal_001",
        source_type=SourceType.ASSESSMENT,
        source_id="assessment_001",
    )

    assert "goal_001" in reconciler._goal_dependencies
    assert SourceType.ASSESSMENT in reconciler._goal_dependencies["goal_001"]
    assert "assessment_001" in reconciler._goal_dependencies["goal_001"][SourceType.ASSESSMENT]


def test_source_change_identifies_affected_goals():
    reconciler = GoalProgressReconciler()
    reconciler.register_goal_dependency("goal_001", SourceType.ASSESSMENT, "assessment_001")
    reconciler.register_goal_dependency("goal_002", SourceType.ASSESSMENT, "assessment_001")
    reconciler.register_goal_dependency("goal_003", SourceType.ASSESSMENT, "assessment_002")

    change = SourceChange(
        source_type=SourceType.ASSESSMENT,
        change_type=ChangeType.UPDATED,
        source_id="assessment_001",
    )

    affected = reconciler.record_source_change(change)
    assert affected == {"goal_001", "goal_002"}
    assert "goal_003" not in affected


def test_record_progress_measurement():
    reconciler = GoalProgressReconciler()
    record = reconciler.record_progress_measurement(
        goal_id="goal_001",
        user_id=1,
        source_type=SourceType.ASSESSMENT,
        value=100.0,
        source_metadata={"assessment_id": "a123"},
    )

    assert record.goal_id == "goal_001"
    assert record.user_id == 1
    assert record.value == 100.0
    assert record.source_type == SourceType.ASSESSMENT
    assert record.source_metadata["assessment_id"] == "a123"


def test_get_source_records_for_goal():
    reconciler = GoalProgressReconciler()
    reconciler.record_progress_measurement("goal_001", 1, SourceType.ASSESSMENT, 100.0)
    reconciler.record_progress_measurement("goal_001", 1, SourceType.ACTIVITY_RECORD, 50.0)
    reconciler.record_progress_measurement("goal_002", 1, SourceType.ASSESSMENT, 200.0)

    records = reconciler.get_source_records_for_goal("goal_001")
    assert len(records) == 2
    assert all(r.goal_id == "goal_001" for r in records)


def test_register_goal_calculator():
    reconciler = GoalProgressReconciler()

    def dummy_calculator(goal_id, user_id, records):
        total = sum(r.value for r in records)
        progress = min(total / 1000 * 100, 100.0)
        return total, progress

    reconciler.register_goal_calculator("goal_001", dummy_calculator)
    assert "goal_001" in reconciler._goal_calculators


def test_reconcile_goal_consistent():
    reconciler = GoalProgressReconciler()

    def simple_calculator(goal_id, user_id, records):
        total = sum(r.value for r in records)
        progress = min(total / 1000 * 100, 100.0)
        return total, progress

    reconciler.register_goal_calculator("goal_001", simple_calculator)
    reconciler.record_progress_measurement("goal_001", 1, SourceType.ASSESSMENT, 800.0)
    reconciler.record_progress_measurement("goal_001", 1, SourceType.ASSESSMENT, 200.0)

    # Total is 1000, so progress should be 100%
    calculated_progress, is_consistent = reconciler.reconcile_goal(
        goal_id="goal_001", user_id=1, current_stored_progress=100.0
    )

    assert calculated_progress == 100.0
    assert is_consistent is True


def test_reconcile_goal_inconsistent():
    reconciler = GoalProgressReconciler()

    def simple_calculator(goal_id, user_id, records):
        total = sum(r.value for r in records)
        progress = min(total / 1000 * 100, 100.0)
        return total, progress

    reconciler.register_goal_calculator("goal_001", simple_calculator)
    reconciler.record_progress_measurement("goal_001", 1, SourceType.ASSESSMENT, 500.0)

    # Total is 500, so progress should be 50%, but stored is 75%
    calculated_progress, is_consistent = reconciler.reconcile_goal(
        goal_id="goal_001", user_id=1, current_stored_progress=75.0
    )

    assert calculated_progress == 50.0
    assert is_consistent is False


def test_discrepancy_is_recorded():
    reconciler = GoalProgressReconciler()

    def simple_calculator(goal_id, user_id, records):
        total = sum(r.value for r in records)
        progress = min(total / 1000 * 100, 100.0)
        return total, progress

    reconciler.register_goal_calculator("goal_001", simple_calculator)
    reconciler.record_progress_measurement("goal_001", 1, SourceType.ASSESSMENT, 300.0)

    # Trigger discrepancy
    reconciler.reconcile_goal(goal_id="goal_001", user_id=1, current_stored_progress=50.0)

    discrepancies = reconciler.get_discrepancies_for_goal("goal_001")
    assert len(discrepancies) == 1
    assert discrepancies[0].stored_progress == 50.0
    assert discrepancies[0].calculated_progress == 30.0


def test_unrelated_goals_not_affected():
    reconciler = GoalProgressReconciler()
    reconciler.register_goal_dependency("goal_001", SourceType.ASSESSMENT, "assessment_001")
    reconciler.register_goal_dependency("goal_002", SourceType.ASSESSMENT, "assessment_002")

    change = SourceChange(
        source_type=SourceType.ASSESSMENT,
        change_type=ChangeType.UPDATED,
        source_id="assessment_001",
    )

    affected = reconciler.record_source_change(change)
    assert "goal_001" in affected
    assert "goal_002" not in affected


def test_duplicate_activity_records_are_tracked():
    reconciler = GoalProgressReconciler()

    # Record same measurement twice
    r1 = reconciler.record_progress_measurement(
        "goal_001", 1, SourceType.ACTIVITY_RECORD, 50.0
    )
    r2 = reconciler.record_progress_measurement(
        "goal_001", 1, SourceType.ACTIVITY_RECORD, 50.0
    )

    records = reconciler.get_source_records_for_goal("goal_001")
    assert len(records) == 2
    assert r1.record_id != r2.record_id  # Unique record IDs


def test_repair_goal():
    reconciler = GoalProgressReconciler()

    def simple_calculator(goal_id, user_id, records):
        total = sum(r.value for r in records)
        progress = min(total / 1000 * 100, 100.0)
        return total, progress

    reconciler.register_goal_calculator("goal_001", simple_calculator)
    reconciler.record_progress_measurement("goal_001", 1, SourceType.ASSESSMENT, 500.0)

    # Introduce discrepancy
    reconciler.reconcile_goal(goal_id="goal_001", user_id=1, current_stored_progress=75.0)
    discrepancies_before = reconciler.get_discrepancies_for_goal("goal_001")
    assert len(discrepancies_before) == 1

    # Repair the goal
    reconciler.repair_goal("goal_001", 1, 50.0)

    records = reconciler.get_source_records_for_goal("goal_001")
    assert any(r.source_metadata.get("repair_action") for r in records)


def test_historical_progress_preserved():
    reconciler = GoalProgressReconciler()
    r1 = reconciler.record_progress_measurement("goal_001", 1, SourceType.ASSESSMENT, 100.0)
    r2 = reconciler.record_progress_measurement("goal_001", 1, SourceType.ASSESSMENT, 100.0)
    r3 = reconciler.record_progress_measurement("goal_001", 1, SourceType.ASSESSMENT, 100.0)

    records = reconciler.get_source_records_for_goal("goal_001")
    assert len(records) == 3
    assert records[0].record_id == r1.record_id
    assert records[1].record_id == r2.record_id
    assert records[2].record_id == r3.record_id


def test_audit_log_tracks_changes():
    reconciler = GoalProgressReconciler()
    reconciler.register_goal_dependency("goal_001", SourceType.ASSESSMENT, "a1")
    reconciler.register_goal_dependency("goal_002", SourceType.ASSESSMENT, "a1")

    change1 = SourceChange(
        source_type=SourceType.ASSESSMENT,
        change_type=ChangeType.UPDATED,
        source_id="a1",
    )
    change2 = SourceChange(
        source_type=SourceType.ASSESSMENT,
        change_type=ChangeType.DELETED,
        source_id="a1",
    )

    reconciler.record_source_change(change1)
    reconciler.record_source_change(change2)

    audit_log = reconciler.get_audit_log()
    assert len(audit_log) == 2
    assert audit_log[0].change_type == ChangeType.UPDATED
    assert audit_log[1].change_type == ChangeType.DELETED


def test_reconcile_multiple_goals_from_source_change():
    reconciler = GoalProgressReconciler()

    def simple_calculator(goal_id, user_id, records):
        total = sum(r.value for r in records)
        progress = min(total / 1000 * 100, 100.0)
        return total, progress

    reconciler.register_goal_dependency("goal_001", SourceType.ASSESSMENT, "a1")
    reconciler.register_goal_dependency("goal_002", SourceType.ASSESSMENT, "a1")
    reconciler.register_goal_calculator("goal_001", simple_calculator)
    reconciler.register_goal_calculator("goal_002", simple_calculator)

    reconciler.record_progress_measurement("goal_001", 1, SourceType.ASSESSMENT, 500.0)
    reconciler.record_progress_measurement("goal_002", 1, SourceType.ASSESSMENT, 800.0)

    def goal_fetcher(goal_id):
        class MockGoal:
            def __init__(self, gid):
                self.id = gid
                self.user_id = 1
                self.progress = 50.0

        return MockGoal(goal_id)

    change = SourceChange(
        source_type=SourceType.ASSESSMENT,
        change_type=ChangeType.UPDATED,
        source_id="a1",
    )

    results = reconciler.reconcile_goals_affected_by_source(change, goal_fetcher)

    assert len(results) == 2
    assert results["goal_001"][0] == 50.0
    assert results["goal_002"][0] == 80.0


def test_global_reconciler_instance():
    r1 = get_goal_progress_reconciler()
    r2 = get_goal_progress_reconciler()
    assert r1 is r2