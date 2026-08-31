"""
Unit tests for Assessment Locking & Concurrent Edit Protection (#1467).
"""

from concurrent.futures import ThreadPoolExecutor

import pytest

from src.core.database import (
    init_db,
    save_assessment,
    get_assessments,
    get_assessment_by_id,
    update_assessment,
    finalize_assessment,
    reopen_finalized_assessment,
)


@pytest.fixture(autouse=True)
def setup_test_database():
    """Ensure database schema (incl. the #1467 migration) is initialized."""
    init_db()


def _create_assessment(user_id: int) -> int:
    saved = save_assessment(
        user_id=user_id,
        transport="Car",
        distance=50.0,
        electricity=100.0,
        diet="Vegetarian",
        flights=0,
        footprint=120.5,
        eco_score=80,
    )
    assert saved is True
    return get_assessments(user_id=user_id)[0][0]


def test_new_assessment_starts_at_revision_one():
    user_id = 87001
    assessment_id = _create_assessment(user_id)

    row = get_assessment_by_id(assessment_id, user_id)
    assert row["revision"] == 1
    assert row["is_finalized"] == 0


def test_update_increments_revision_atomically():
    user_id = 87002
    assessment_id = _create_assessment(user_id)

    result = update_assessment(
        assessment_id, user_id, expected_revision=1, updates={"footprint": 99.0}
    )
    assert result["status"] == "ok"
    assert result["revision"] == 2

    row = get_assessment_by_id(assessment_id, user_id)
    assert row["revision"] == 2
    assert row["footprint"] == 99.0


def test_stale_update_returns_conflict_without_overwriting():
    user_id = 87003
    assessment_id = _create_assessment(user_id)

    first = update_assessment(
        assessment_id, user_id, expected_revision=1, updates={"footprint": 10.0}
    )
    assert first["status"] == "ok"

    stale = update_assessment(
        assessment_id, user_id, expected_revision=1, updates={"footprint": 999.0}
    )
    assert stale["status"] == "conflict"
    assert stale["current"]["footprint"] == 10.0

    row = get_assessment_by_id(assessment_id, user_id)
    assert row["footprint"] == 10.0
    assert row["revision"] == 2


def test_concurrent_updates_cannot_silently_overwrite_each_other():
    user_id = 87004
    assessment_id = _create_assessment(user_id)

    def attempt_update(footprint_value: float) -> dict:
        return update_assessment(
            assessment_id,
            user_id,
            expected_revision=1,
            updates={"footprint": footprint_value},
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(attempt_update, [float(i) for i in range(8)]))

    ok_results = [r for r in results if r["status"] == "ok"]
    conflict_results = [r for r in results if r["status"] == "conflict"]

    assert len(ok_results) == 1
    assert len(conflict_results) == 7

    row = get_assessment_by_id(assessment_id, user_id)
    assert row["revision"] == 2


def test_finalized_assessment_cannot_be_modified_via_update():
    user_id = 87005
    assessment_id = _create_assessment(user_id)

    finalize_result = finalize_assessment(assessment_id, user_id, expected_revision=1)
    assert finalize_result["status"] == "ok"

    blocked = update_assessment(
        assessment_id, user_id, expected_revision=finalize_result["revision"],
        updates={"footprint": 5.0},
    )
    assert blocked["status"] == "finalized"

    row = get_assessment_by_id(assessment_id, user_id)
    assert row["is_finalized"] == 1
    assert row["footprint"] == 120.5


def test_finalized_assessment_can_be_edited_via_explicit_reopen_workflow():
    user_id = 87006
    assessment_id = _create_assessment(user_id)

    finalize_result = finalize_assessment(assessment_id, user_id, expected_revision=1)
    assert finalize_result["status"] == "ok"

    reopen_result = reopen_finalized_assessment(
        assessment_id, user_id, expected_revision=finalize_result["revision"]
    )
    assert reopen_result["status"] == "ok"

    row = get_assessment_by_id(assessment_id, user_id)
    assert row["is_finalized"] == 0

    edit_result = update_assessment(
        assessment_id, user_id, expected_revision=reopen_result["revision"],
        updates={"footprint": 42.0},
    )
    assert edit_result["status"] == "ok"


def test_frontend_can_recover_from_stale_edit_conflict():
    """Simulates the UI flow: stale save -> reload latest -> retry succeeds."""
    user_id = 87007
    assessment_id = _create_assessment(user_id)

    update_assessment(
        assessment_id, user_id, expected_revision=1, updates={"footprint": 7.0}
    )

    stale_attempt = update_assessment(
        assessment_id, user_id, expected_revision=1, updates={"footprint": 8.0}
    )
    assert stale_attempt["status"] == "conflict"

    latest = stale_attempt["current"]

    retry = update_assessment(
        assessment_id, user_id, expected_revision=latest["revision"],
        updates={"footprint": 8.0},
    )
    assert retry["status"] == "ok"