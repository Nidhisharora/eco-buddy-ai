"""
Tests for Community Leaderboard & Team Carbon Challenges Service.

Tests cover leaderboard ranking, team management, challenge lifecycle,
carbon logging, and database operations.
"""

import os
import sys
import sqlite3
import tempfile
from datetime import datetime, timedelta

import pytest

# Ensure project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.community import leaderboard_service as lbs


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path):
    """Use a temporary database for each test."""
    db_path = str(tmp_path / "test_leaderboard.db")
    original = lbs.DB_PATH
    lbs.DB_PATH = db_path
    lbs.init_leaderboard_tables()
    lbs.seed_sample_teams()
    lbs.seed_sample_challenges()
    yield
    lbs.DB_PATH = original


def _create_test_user(user_id: int, username: str):
    """Insert a test user into the DB."""
    conn = sqlite3.connect(lbs.DB_PATH)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO user (id, username, email) VALUES (?, ?, ?)",
            (user_id, username, f"{username}@test.com"),
        )
        conn.commit()
    finally:
        conn.close()


def _log_carbon_raw(user_id: int, category: str, amount_kg: float):
    """Insert a raw carbon log entry."""
    conn = sqlite3.connect(lbs.DB_PATH)
    try:
        conn.execute(
            "INSERT INTO user_carbon_log (user_id, category, amount_kg, description, logged_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, category, amount_kg, "test", datetime.utcnow().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def _set_weekly_summary(user_id: int, eco_score: float = 80, carbon: float = 10, streak: int = 5):
    """Insert a weekly summary row."""
    conn = sqlite3.connect(lbs.DB_PATH)
    try:
        week = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        conn.execute(
            "INSERT OR REPLACE INTO user_weekly_summary (user_id, week_start, eco_score, carbon_saved_kg, streak_days, badges_count, level) VALUES (?, ?, ?, ?, ?, 2, 3)",
            (user_id, week, eco_score, carbon, streak),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Test: Leaderboard tables
# ---------------------------------------------------------------------------

class TestInitTables:
    def test_tables_created(self):
        conn = sqlite3.connect(lbs.DB_PATH)
        tables = [
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]
        conn.close()
        assert "teams" in tables
        assert "team_members" in tables
        assert "team_challenges" in tables
        assert "team_challenge_progress" in tables
        assert "user_carbon_log" in tables
        assert "user_weekly_summary" in tables

    def test_seeded_teams(self):
        teams = lbs.get_all_teams()
        assert len(teams) >= 5

    def test_seeded_challenges(self):
        challenges = lbs.get_team_challenges()
        assert len(challenges) >= 5


# ---------------------------------------------------------------------------
# Test: Leaderboard ranking
# ---------------------------------------------------------------------------

class TestLeaderboard:
    def test_empty_leaderboard(self):
        entries = lbs.get_global_leaderboard("overall")
        assert entries == []

    def test_ranking_with_data(self):
        _create_test_user(1, "alice")
        _create_test_user(2, "bob")
        _log_carbon_raw(1, "energy", 50.0)
        _log_carbon_raw(1, "transport", 30.0)
        _log_carbon_raw(2, "energy", 20.0)
        _set_weekly_summary(1, eco_score=90, carbon=80, streak=10)
        _set_weekly_summary(2, eco_score=70, carbon=20, streak=3)

        entries = lbs.get_global_leaderboard("overall")
        assert len(entries) == 2
        assert entries[0].user_id == 1
        assert entries[0].rank == 1
        assert entries[1].user_id == 2
        assert entries[1].rank == 2

    def test_category_ranking(self):
        _create_test_user(1, "alice")
        _create_test_user(2, "bob")
        _log_carbon_raw(1, "energy", 100.0)
        _log_carbon_raw(2, "energy", 50.0)
        _log_carbon_raw(1, "transport", 200.0)
        _log_carbon_raw(2, "transport", 300.0)

        energy_entries = lbs.get_global_leaderboard("energy")
        assert energy_entries[0].user_id == 1

        transport_entries = lbs.get_global_leaderboard("transport")
        assert transport_entries[0].user_id == 2

    def test_streak_ranking(self):
        _create_test_user(1, "alice")
        _create_test_user(2, "bob")
        _set_weekly_summary(1, streak=15)
        _set_weekly_summary(2, streak=3)

        entries = lbs.get_global_leaderboard("streak")
        assert entries[0].user_id == 1

    def test_leaderboard_entry_to_dict(self):
        entry = lbs.LeaderboardEntry(
            rank=1, user_id=1, username="test", score=80.0,
            carbon_saved_kg=100.0, streak_days=5, level=3,
            badges_count=2, team_name="Green Team",
        )
        d = entry.to_dict()
        assert d["rank"] == 1
        assert d["username"] == "test"
        assert d["team_name"] == "Green Team"


# ---------------------------------------------------------------------------
# Test: Carbon logging
# ---------------------------------------------------------------------------

class TestCarbonLogging:
    def test_log_valid(self):
        _create_test_user(1, "alice")
        assert lbs.log_carbon_saving(1, "energy", 10.0, "saved electricity") is True

    def test_log_invalid_category(self):
        _create_test_user(1, "alice")
        assert lbs.log_carbon_saving(1, "invalid", 10.0) is False

    def test_log_negative_amount(self):
        _create_test_user(1, "alice")
        assert lbs.log_carbon_saving(1, "energy", -5.0) is False

    def test_log_zero_amount(self):
        _create_test_user(1, "alice")
        assert lbs.log_carbon_saving(1, "energy", 0.0) is False

    def test_log_updates_leaderboard(self):
        _create_test_user(1, "alice")
        lbs.log_carbon_saving(1, "energy", 25.0)
        entries = lbs.get_global_leaderboard("energy")
        assert len(entries) == 1
        assert entries[0].carbon_saved_kg == 25.0

    def test_multiple_logs_accumulate(self):
        _create_test_user(1, "alice")
        lbs.log_carbon_saving(1, "energy", 10.0)
        lbs.log_carbon_saving(1, "energy", 15.0)
        lbs.log_carbon_saving(1, "transport", 5.0)

        energy_entries = lbs.get_global_leaderboard("energy")
        assert energy_entries[0].carbon_saved_kg == 25.0

        transport_entries = lbs.get_global_leaderboard("transport")
        assert transport_entries[0].carbon_saved_kg == 5.0


# ---------------------------------------------------------------------------
# Test: Team management
# ---------------------------------------------------------------------------

class TestTeamManagement:
    def test_create_team(self):
        _create_test_user(1, "alice")
        team_id = lbs.create_team("Test Team", "A test team", 1, "🌿")
        assert team_id.startswith("team_")

        teams = lbs.get_all_teams()
        names = [t.name for t in teams]
        assert "Test Team" in names

    def test_join_team(self):
        _create_test_user(1, "alice")
        _create_test_user(2, "bob")
        team_id = lbs.create_team("Test Team", "desc", 1)

        success, msg = lbs.join_team(2, team_id)
        assert success is True
        assert "Welcome" in msg

    def test_cannot_join_twice(self):
        _create_test_user(1, "alice")
        _create_test_user(2, "bob")
        team_id = lbs.create_team("Test Team", "desc", 1)
        lbs.join_team(2, team_id)

        success, msg = lbs.join_team(2, team_id)
        assert success is False
        assert "already on a team" in msg

    def test_leave_team(self):
        _create_test_user(1, "alice")
        _create_test_user(2, "bob")
        team_id = lbs.create_team("Test Team", "desc", 1)
        lbs.join_team(2, team_id)

        success, msg = lbs.leave_team(2)
        assert success is True

    def test_captain_cannot_leave_with_members(self):
        _create_test_user(1, "alice")
        _create_test_user(2, "bob")
        team_id = lbs.create_team("Test Team", "desc", 1)
        lbs.join_team(2, team_id)

        success, msg = lbs.leave_team(1)
        assert success is False
        assert "captain" in msg.lower()

    def test_team_full(self):
        _create_test_user(1, "alice")
        team_id = lbs.create_team("Tiny Team", "desc", 1)
        # Update max_members to 1
        conn = sqlite3.connect(lbs.DB_PATH)
        conn.execute("UPDATE teams SET max_members = 1 WHERE team_id = ?", (team_id,))
        conn.commit()
        conn.close()

        _create_test_user(2, "bob")
        success, msg = lbs.join_team(2, team_id)
        assert success is False
        assert "full" in msg.lower()

    def test_get_user_team(self):
        _create_test_user(1, "alice")
        team_id = lbs.create_team("My Team", "desc", 1)

        team = lbs.get_user_team(1)
        assert team is not None
        assert team.name == "My Team"

    def test_get_user_team_none(self):
        _create_test_user(1, "alice")
        team = lbs.get_user_team(1)
        assert team is None

    def test_get_team_members(self):
        _create_test_user(1, "alice")
        _create_test_user(2, "bob")
        team_id = lbs.create_team("Test Team", "desc", 1)
        lbs.join_team(2, team_id)

        members = lbs.get_team_members(team_id)
        assert len(members) == 2
        usernames = [m["username"] for m in members]
        assert "alice" in usernames
        assert "bob" in usernames

    def test_team_icon(self):
        _create_test_user(1, "alice")
        team_id = lbs.create_team("Icon Team", "desc", 1, "🌍")

        teams = lbs.get_all_teams()
        team = next(t for t in teams if t.team_id == team_id)
        assert team.icon == "🌍"


# ---------------------------------------------------------------------------
# Test: Team challenges
# ---------------------------------------------------------------------------

class TestTeamChallenges:
    def test_get_challenges(self):
        challenges = lbs.get_team_challenges()
        assert len(challenges) >= 5

    def test_get_challenge_by_status(self):
        active = lbs.get_team_challenges(status="active")
        assert len(active) >= 1

    def test_create_challenge(self):
        ch_id = lbs.create_team_challenge(
            "Test Challenge", "A test challenge", "energy", 50, 7, 100, "⚡"
        )
        assert ch_id.startswith("tc_")

        challenges = lbs.get_team_challenges()
        titles = [c.title for c in challenges]
        assert "Test Challenge" in titles

    def test_challenge_leaderboard(self):
        _create_test_user(1, "alice")
        _create_test_user(2, "bob")
        team_id1 = lbs.create_team("Team A", "desc", 1)
        team_id2 = lbs.create_team("Team B", "desc", 2)
        lbs.join_team(2, team_id2)

        ch_id = lbs.create_team_challenge("Test", "desc", "overall", 100, 7, 100)
        rankings = lbs.get_challenge_leaderboard(ch_id)
        assert len(rankings) == 2
        assert rankings[0]["team_name"] == "Team A"

    def test_challenge_to_dict(self):
        ch = lbs.TeamChallenge(
            challenge_id="tc1", title="Test", description="desc",
            category="energy", target_kg=50, duration_days=7,
            xp_reward=100, starts_at="2025-01-01", ends_at="2025-01-08",
            status="active", icon="⚡",
        )
        d = ch.to_dict()
        assert d["challenge_id"] == "tc1"
        assert d["xp_reward"] == 100


# ---------------------------------------------------------------------------
# Test: User position
# ---------------------------------------------------------------------------

class TestUserPosition:
    def test_position_found(self):
        _create_test_user(1, "alice")
        _log_carbon_raw(1, "energy", 50.0)
        _set_weekly_summary(1, eco_score=80, carbon=50, streak=5)

        entry = lbs.get_user_leaderboard_position(1, "overall")
        assert entry is not None
        assert entry.user_id == 1

    def test_position_not_found(self):
        entry = lbs.get_user_leaderboard_position(999)
        # Should still return a basic entry or None
        assert entry is None


# ---------------------------------------------------------------------------
# Test: Data classes
# ---------------------------------------------------------------------------

class TestDataClasses:
    def test_team_to_dict(self):
        team = lbs.Team(
            team_id="t1", name="Test", description="desc",
            created_by=1, created_at="2025-01-01",
            member_count=5, total_carbon_saved_kg=100.0,
            avg_eco_score=75.0, challenge_wins=2,
            icon="🌿", max_members=10, is_open=True,
        )
        d = team.to_dict()
        assert d["team_id"] == "t1"
        assert d["member_count"] == 5

    def test_challenge_progress_to_dict(self):
        cp = lbs.TeamChallengeProgress(
            team_id="t1", challenge_id="c1",
            carbon_saved_kg=50.0, participants=3,
            last_updated="2025-01-01",
        )
        d = cp.to_dict()
        assert d["carbon_saved_kg"] == 50.0

    def test_leaderboard_categories(self):
        assert "overall" in lbs.LEADERBOARD_CATEGORIES
        assert "transport" in lbs.LEADERBOARD_CATEGORIES
        assert "energy" in lbs.LEADERBOARD_CATEGORIES
        assert "diet" in lbs.LEADERBOARD_CATEGORIES
        assert "water" in lbs.LEADERBOARD_CATEGORIES
        assert "streak" in lbs.LEADERBOARD_CATEGORIES


# ---------------------------------------------------------------------------
# Test: Carbon progress updates
# ---------------------------------------------------------------------------

class TestTeamProgressUpdates:
    def test_carbon_log_updates_team_progress(self):
        _create_test_user(1, "alice")
        _create_test_user(2, "bob")
        team_id = lbs.create_team("Team A", "desc", 1)
        lbs.join_team(2, team_id)

        # Create active challenge
        ch_id = lbs.create_team_challenge("Test", "desc", "energy", 100, 7, 100)

        # Log carbon — should update team progress
        lbs.log_carbon_saving(1, "energy", 20.0)
        lbs.log_carbon_saving(2, "energy", 15.0)

        rankings = lbs.get_challenge_leaderboard(ch_id)
        team_progress = next(r for r in rankings if r["team_id"] == team_id)
        assert team_progress["carbon_saved"] == 35.0
