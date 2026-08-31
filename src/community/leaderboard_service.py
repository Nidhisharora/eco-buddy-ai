"""
Community Leaderboard & Team Carbon Challenges Service

Provides functionality for global and category-specific leaderboards,
team formation, team challenges, and carbon savings aggregation.
Integrates with the existing SQLAlchemy models and gamification system.
"""

import json
import sqlite3
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class LeaderboardEntry:
    """A single entry on a leaderboard."""
    rank: int
    user_id: int
    username: str
    score: float
    carbon_saved_kg: float
    streak_days: int
    level: int
    badges_count: int
    team_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Team:
    """A sustainability team that users can join."""
    team_id: str
    name: str
    description: str
    created_by: int
    created_at: str
    member_count: int = 0
    total_carbon_saved_kg: float = 0.0
    avg_eco_score: float = 0.0
    challenge_wins: int = 0
    icon: str = "🌿"
    max_members: int = 10
    is_open: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TeamChallenge:
    """A challenge that entire teams compete in."""
    challenge_id: str
    title: str
    description: str
    category: str
    target_kg: float
    duration_days: int
    xp_reward: int
    starts_at: str
    ends_at: str
    status: str = "upcoming"  # upcoming, active, completed
    winner_team_id: Optional[str] = None
    icon: str = "🏆"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TeamChallengeProgress:
    """Tracks a team's progress in a specific challenge."""
    team_id: str
    challenge_id: str
    carbon_saved_kg: float = 0.0
    participants: int = 0
    last_updated: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LEADERBOARD_CATEGORIES = {
    "overall": "🌍 Overall Carbon Savings",
    "transport": "🚗 Transport Savings",
    "energy": "⚡ Energy Savings",
    "diet": "🥗 Diet Savings",
    "water": "💧 Water Savings",
    "streak": "🔥 Longest Streak",
}

TEAM_ICONS = ["🌿", "🌲", "🌱", "🍃", "🌎", "🌍", "💚", "🦋", "🐝", "🌊"]

SAMPLE_TEAMS = [
    {"id": "team_green_warriors", "name": "Green Warriors", "icon": "⚔️", "desc": "Fighting climate change one action at a time"},
    {"id": "team_eco_rangers", "name": "Eco Rangers", "icon": "🌍", "desc": "Protecting the planet through sustainable living"},
    {"id": "team_carbon_busters", "name": "Carbon Busters", "icon": "👻", "desc": "Ghosting carbon emissions since day one"},
    {"id": "team_leaf_legion", "name": "Leaf Legion", "icon": "🍃", "desc": "A legion of leaf-loving environmentalists"},
    {"id": "team_sun_seekers", "name": "Sun Seekers", "icon": "☀️", "desc": "Harnessing the power of renewable energy"},
]

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

DB_PATH = "eco_buddy.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_leaderboard_tables():
    """Create leaderboard and team tables if they don't exist."""
    conn = _get_conn()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS teams (
                team_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_by INTEGER,
                created_at TEXT,
                icon TEXT DEFAULT '🌿',
                max_members INTEGER DEFAULT 10,
                is_open INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS team_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                joined_at TEXT,
                role TEXT DEFAULT 'member',
                UNIQUE(team_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS team_challenges (
                challenge_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                target_kg REAL,
                duration_days INTEGER,
                xp_reward INTEGER,
                starts_at TEXT,
                ends_at TEXT,
                status TEXT DEFAULT 'upcoming',
                winner_team_id TEXT,
                icon TEXT DEFAULT '🏆'
            );

            CREATE TABLE IF NOT EXISTS team_challenge_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id TEXT NOT NULL,
                challenge_id TEXT NOT NULL,
                carbon_saved_kg REAL DEFAULT 0,
                participants INTEGER DEFAULT 0,
                last_updated TEXT,
                UNIQUE(team_id, challenge_id)
            );

            CREATE TABLE IF NOT EXISTS user_carbon_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                amount_kg REAL NOT NULL,
                description TEXT,
                logged_at TEXT
            );

            CREATE TABLE IF NOT EXISTS user_weekly_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                week_start TEXT,
                eco_score REAL DEFAULT 0,
                carbon_saved_kg REAL DEFAULT 0,
                streak_days INTEGER DEFAULT 0,
                badges_count INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                UNIQUE(user_id, week_start)
            );
        """)
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Leaderboard logic
# ---------------------------------------------------------------------------

def get_global_leaderboard(
    category: str = "overall",
    limit: int = 50,
) -> List[LeaderboardEntry]:
    """
    Fetch the global leaderboard for a given category.
    Aggregates data from user_carbon_log, user_weekly_summary, and gamification tables.
    """
    conn = _get_conn()
    try:
        # Build ranking query based on category
        if category == "streak":
            query = """
                SELECT
                    u.id AS user_id,
                    u.username,
                    COALESCE(SUM(uc.carbon_saved_kg), 0) AS total_carbon_saved,
                    COALESCE(MAX(ws.streak_days), 0) AS max_streak,
                    COALESCE(MAX(ws.eco_score), 0) AS eco_score,
                    COALESCE(MAX(ws.level), 1) AS level,
                    COALESCE(ws2.badges_count, 0) AS badges_count,
                    t.name AS team_name
                FROM user u
                LEFT JOIN user_weekly_summary ws ON ws.user_id = u.id
                LEFT JOIN (
                    SELECT user_id, SUM(streak_days) AS streak_days
                    FROM user_weekly_summary
                    GROUP BY user_id
                ) ws2 ON ws2.user_id = u.id
                LEFT JOIN (
                    SELECT user_id, COUNT(*) AS badges_count
                    FROM unlocked_badge
                    GROUP BY user_id
                ) ws3 ON ws3.user_id = u.id
                LEFT JOIN team_members tm ON tm.user_id = u.id
                LEFT JOIN teams t ON t.team_id = tm.team_id
                GROUP BY u.id
                ORDER BY max_streak DESC, total_carbon_saved DESC
                LIMIT ?
            """
        elif category in ("transport", "energy", "diet", "water"):
            query = """
                SELECT
                    u.id AS user_id,
                    u.username,
                    COALESCE(SUM(CASE WHEN uc.category = ? THEN uc.amount_kg ELSE 0 END), 0) AS total_carbon_saved,
                    COALESCE(MAX(ws.streak_days), 0) AS max_streak,
                    COALESCE(MAX(ws.eco_score), 0) AS eco_score,
                    COALESCE(MAX(ws.level), 1) AS level,
                    COALESCE(ws3.badges_count, 0) AS badges_count,
                    t.name AS team_name
                FROM user u
                LEFT JOIN user_carbon_log uc ON uc.user_id = u.id
                LEFT JOIN user_weekly_summary ws ON ws.user_id = u.id
                LEFT JOIN (
                    SELECT user_id, COUNT(*) AS badges_count
                    FROM unlocked_badge
                    GROUP BY user_id
                ) ws3 ON ws3.user_id = u.id
                LEFT JOIN team_members tm ON tm.user_id = u.id
                LEFT JOIN teams t ON t.team_id = tm.team_id
                GROUP BY u.id
                ORDER BY total_carbon_saved DESC
                LIMIT ?
            """
        else:  # overall
            query = """
                SELECT
                    u.id AS user_id,
                    u.username,
                    COALESCE(SUM(uc.amount_kg), 0) AS total_carbon_saved,
                    COALESCE(MAX(ws.streak_days), 0) AS max_streak,
                    COALESCE(MAX(ws.eco_score), 0) AS eco_score,
                    COALESCE(MAX(ws.level), 1) AS level,
                    COALESCE(ws3.badges_count, 0) AS badges_count,
                    t.name AS team_name
                FROM user u
                LEFT JOIN user_carbon_log uc ON uc.user_id = u.id
                LEFT JOIN user_weekly_summary ws ON ws.user_id = u.id
                LEFT JOIN (
                    SELECT user_id, COUNT(*) AS badges_count
                    FROM unlocked_badge
                    GROUP BY user_id
                ) ws3 ON ws3.user_id = u.id
                LEFT JOIN team_members tm ON tm.user_id = u.id
                LEFT JOIN teams t ON t.team_id = tm.team_id
                GROUP BY u.id
                ORDER BY total_carbon_saved DESC
                LIMIT ?
            """

        if category in ("transport", "energy", "diet", "water"):
            rows = conn.execute(query, (category, limit)).fetchall()
        else:
            rows = conn.execute(query, (limit,)).fetchall()

        entries = []
        for rank, row in enumerate(rows, start=1):
            entries.append(LeaderboardEntry(
                rank=rank,
                user_id=row["user_id"],
                username=row["username"],
                score=row["eco_score"],
                carbon_saved_kg=row["total_carbon_saved"],
                streak_days=row["max_streak"],
                level=row["level"],
                badges_count=row["badges_count"],
                team_name=row["team_name"],
            ))
        return entries
    finally:
        conn.close()


def log_carbon_saving(
    user_id: int,
    category: str,
    amount_kg: float,
    description: str = "",
) -> bool:
    """Log a carbon saving event for a user."""
    if category not in ("transport", "energy", "diet", "water"):
        return False
    if amount_kg <= 0:
        return False

    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO user_carbon_log (user_id, category, amount_kg, description, logged_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, category, amount_kg, description, datetime.utcnow().isoformat()),
        )
        conn.commit()
        # Also update team challenge progress if user is on a team
        _update_team_progress_for_user(conn, user_id, amount_kg)
        return True
    except Exception:
        return False
    finally:
        conn.close()


def _update_team_progress_for_user(conn: sqlite3.Connection, user_id: int, amount_kg: float):
    """Update team challenge progress when a user logs carbon savings."""
    try:
        # Find user's team
        row = conn.execute(
            "SELECT team_id FROM team_members WHERE user_id = ?", (user_id,)
        ).fetchone()
        if not row:
            return

        team_id = row["team_id"]
        # Find active challenges for this team
        now = datetime.utcnow().isoformat()
        challenges = conn.execute(
            """SELECT challenge_id FROM team_challenges
               WHERE status = 'active' AND starts_at <= ? AND ends_at >= ?""",
            (now, now),
        ).fetchall()

        for ch in challenges:
            ch_id = ch["challenge_id"]
            conn.execute(
                """INSERT INTO team_challenge_progress (team_id, challenge_id, carbon_saved_kg, participants, last_updated)
                   VALUES (?, ?, ?, 1, ?)
                   ON CONFLICT(team_id, challenge_id) DO UPDATE SET
                   carbon_saved_kg = carbon_saved_kg + excluded.carbon_saved_kg,
                   participants = (SELECT COUNT(DISTINCT user_id) FROM user_carbon_log WHERE user_id IN
                       (SELECT user_id FROM team_members WHERE team_id = excluded.team_id)),
                   last_updated = excluded.last_updated""",
                (team_id, ch_id, amount_kg, now),
            )
        conn.commit()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Team management
# ---------------------------------------------------------------------------

def get_all_teams() -> List[Team]:
    """Fetch all teams with member counts and aggregate stats."""
    conn = _get_conn()
    try:
        rows = conn.execute("""
            SELECT
                t.team_id,
                t.name,
                t.description,
                t.created_by,
                t.created_at,
                t.icon,
                t.max_members,
                t.is_open,
                COUNT(DISTINCT tm.user_id) AS member_count,
                COALESCE(SUM(uc.amount_kg), 0) AS total_carbon_saved,
                COALESCE(AVG(ws.eco_score), 0) AS avg_eco_score,
                (SELECT COUNT(*) FROM team_challenges WHERE winner_team_id = t.team_id) AS challenge_wins
            FROM teams t
            LEFT JOIN team_members tm ON tm.team_id = t.team_id
            LEFT JOIN user_carbon_log uc ON uc.user_id = tm.user_id
            LEFT JOIN user_weekly_summary ws ON ws.user_id = tm.user_id
            GROUP BY t.team_id
            ORDER BY total_carbon_saved DESC
        """).fetchall()

        teams = []
        for row in rows:
            teams.append(Team(
                team_id=row["team_id"],
                name=row["name"],
                description=row["description"] or "",
                created_by=row["created_by"] or 0,
                created_at=row["created_at"] or "",
                member_count=row["member_count"],
                total_carbon_saved_kg=row["total_carbon_saved"],
                avg_eco_score=row["avg_eco_score"],
                challenge_wins=row["challenge_wins"],
                icon=row["icon"] or "🌿",
                max_members=row["max_members"],
                is_open=bool(row["is_open"]),
            ))
        return teams
    finally:
        conn.close()


def get_user_team(user_id: int) -> Optional[Team]:
    """Get the team a user belongs to, if any."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT team_id FROM team_members WHERE user_id = ?", (user_id,)
        ).fetchone()
        if not row:
            return None
        teams = get_all_teams()
        for t in teams:
            if t.team_id == row["team_id"]:
                return t
        return None
    finally:
        conn.close()


def create_team(name: str, description: str, created_by: int, icon: str = "🌿") -> str:
    """Create a new team and add the creator as captain."""
    team_id = f"team_{name.lower().replace(' ', '_')}_{int(datetime.utcnow().timestamp())}"
    conn = _get_conn()
    try:
        now = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO teams (team_id, name, description, created_by, created_at, icon) VALUES (?, ?, ?, ?, ?, ?)",
            (team_id, name, description, created_by, now, icon),
        )
        conn.execute(
            "INSERT INTO team_members (team_id, user_id, joined_at, role) VALUES (?, ?, ?, 'captain')",
            (team_id, created_by, now),
        )
        conn.commit()
        return team_id
    finally:
        conn.close()


def join_team(user_id: int, team_id: str) -> Tuple[bool, str]:
    """Join an existing team."""
    conn = _get_conn()
    try:
        # Check if already on a team
        existing = conn.execute(
            "SELECT team_id FROM team_members WHERE user_id = ?", (user_id,)
        ).fetchone()
        if existing:
            return False, "You are already on a team. Leave your current team first."

        # Check team exists and is open
        team = conn.execute(
            "SELECT * FROM teams WHERE team_id = ?", (team_id,)
        ).fetchone()
        if not team:
            return False, "Team not found."
        if not team["is_open"]:
            return False, "This team is not accepting new members."

        # Check member count
        count = conn.execute(
            "SELECT COUNT(*) AS cnt FROM team_members WHERE team_id = ?", (team_id,)
        ).fetchone()["cnt"]
        if count >= team["max_members"]:
            return False, "This team is full."

        now = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO team_members (team_id, user_id, joined_at, role) VALUES (?, ?, ?, 'member')",
            (team_id, user_id, now),
        )
        conn.commit()
        return True, "Welcome to the team! 🎉"
    finally:
        conn.close()


def leave_team(user_id: int) -> Tuple[bool, str]:
    """Leave the current team."""
    conn = _get_conn()
    try:
        existing = conn.execute(
            "SELECT team_id, role FROM team_members WHERE user_id = ?", (user_id,)
        ).fetchone()
        if not existing:
            return False, "You are not on a team."
        if existing["role"] == "captain":
            member_count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM team_members WHERE team_id = ?",
                (existing["team_id"],)
            ).fetchone()["cnt"]
            if member_count > 1:
                return False, "Transfer captaincy before leaving, or disband the team."

        conn.execute(
            "DELETE FROM team_members WHERE user_id = ?", (user_id,)
        )
        conn.commit()
        return True, "You have left the team."
    finally:
        conn.close()


def get_team_members(team_id: str) -> List[Dict[str, Any]]:
    """Get all members of a team with their stats."""
    conn = _get_conn()
    try:
        rows = conn.execute("""
            SELECT
                u.id AS user_id,
                u.username,
                tm.role,
                tm.joined_at,
                COALESCE(SUM(uc.amount_kg), 0) AS carbon_saved_kg,
                COALESCE(MAX(ws.eco_score), 0) AS eco_score,
                COALESCE(MAX(ws.level), 1) AS level
            FROM team_members tm
            JOIN user u ON u.id = tm.user_id
            LEFT JOIN user_carbon_log uc ON uc.user_id = u.id
            LEFT JOIN user_weekly_summary ws ON ws.user_id = u.id
            WHERE tm.team_id = ?
            GROUP BY u.id
            ORDER BY carbon_saved_kg DESC
        """, (team_id,)).fetchall()

        return [
            {
                "user_id": row["user_id"],
                "username": row["username"],
                "role": row["role"],
                "joined_at": row["joined_at"],
                "carbon_saved_kg": row["carbon_saved_kg"],
                "eco_score": row["eco_score"],
                "level": row["level"],
            }
            for row in rows
        ]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Team challenges
# ---------------------------------------------------------------------------

def get_team_challenges(status: Optional[str] = None) -> List[TeamChallenge]:
    """Fetch team challenges, optionally filtered by status."""
    conn = _get_conn()
    try:
        if status:
            rows = conn.execute(
                "SELECT * FROM team_challenges WHERE status = ? ORDER BY starts_at DESC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM team_challenges ORDER BY starts_at DESC"
            ).fetchall()

        return [
            TeamChallenge(
                challenge_id=row["challenge_id"],
                title=row["title"],
                description=row["description"] or "",
                category=row["category"] or "overall",
                target_kg=row["target_kg"] or 100,
                duration_days=row["duration_days"] or 7,
                xp_reward=row["xp_reward"] or 100,
                starts_at=row["starts_at"] or "",
                ends_at=row["ends_at"] or "",
                status=row["status"] or "upcoming",
                winner_team_id=row["winner_team_id"],
                icon=row["icon"] or "🏆",
            )
            for row in rows
        ]
    finally:
        conn.close()


def create_team_challenge(
    title: str,
    description: str,
    category: str,
    target_kg: float,
    duration_days: int,
    xp_reward: int,
    icon: str = "🏆",
) -> str:
    """Create a new team challenge."""
    challenge_id = f"tc_{int(datetime.utcnow().timestamp())}_{title[:20].lower().replace(' ', '_')}"
    now = datetime.utcnow()
    ends = now + timedelta(days=duration_days)

    conn = _get_conn()
    try:
        conn.execute(
            """INSERT INTO team_challenges
               (challenge_id, title, description, category, target_kg, duration_days,
                xp_reward, starts_at, ends_at, status, icon)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)""",
            (
                challenge_id, title, description, category, target_kg,
                duration_days, xp_reward, now.isoformat(), ends.isoformat(), icon,
            ),
        )
        conn.commit()
        return challenge_id
    finally:
        conn.close()


def get_challenge_leaderboard(challenge_id: str) -> List[Dict[str, Any]]:
    """Get team rankings for a specific challenge."""
    conn = _get_conn()
    try:
        rows = conn.execute("""
            SELECT
                t.team_id,
                t.name,
                t.icon,
                COALESCE(tcp.carbon_saved_kg, 0) AS carbon_saved,
                COALESCE(tcp.participants, 0) AS participants,
                tcp.last_updated
            FROM teams t
            LEFT JOIN team_challenge_progress tcp ON tcp.team_id = t.team_id AND tcp.challenge_id = ?
            ORDER BY carbon_saved DESC
        """, (challenge_id,)).fetchall()

        return [
            {
                "rank": idx + 1,
                "team_id": row["team_id"],
                "team_name": row["name"],
                "icon": row["icon"],
                "carbon_saved": row["carbon_saved"],
                "participants": row["participants"],
                "last_updated": row["last_updated"],
            }
            for idx, row in enumerate(rows)
        ]
    finally:
        conn.close()


def get_user_leaderboard_position(user_id: int, category: str = "overall") -> Optional[LeaderboardEntry]:
    """Get the current user's position on the leaderboard."""
    entries = get_global_leaderboard(category, limit=1000)
    for entry in entries:
        if entry.user_id == user_id:
            return entry
    # If not found, compute their stats manually
    conn = _get_conn()
    try:
        row = conn.execute("""
            SELECT
                u.id AS user_id,
                u.username,
                COALESCE(SUM(uc.amount_kg), 0) AS total_carbon_saved,
                COALESCE(MAX(ws.streak_days), 0) AS max_streak,
                COALESCE(MAX(ws.eco_score), 0) AS eco_score,
                COALESCE(MAX(ws.level), 1) AS level,
                COALESCE(ws2.badges_count, 0) AS badges_count,
                t.name AS team_name
            FROM user u
            LEFT JOIN user_carbon_log uc ON uc.user_id = u.id
            LEFT JOIN user_weekly_summary ws ON ws.user_id = u.id
            LEFT JOIN (
                SELECT user_id, COUNT(*) AS badges_count
                FROM unlocked_badge
                GROUP BY user_id
            ) ws2 ON ws2.user_id = u.id
            LEFT JOIN team_members tm ON tm.user_id = u.id
            LEFT JOIN teams t ON t.team_id = tm.team_id
            WHERE u.id = ?
            GROUP BY u.id
        """, (user_id,)).fetchone()

        if row:
            return LeaderboardEntry(
                rank=len(entries) + 1,
                user_id=row["user_id"],
                username=row["username"],
                score=row["eco_score"],
                carbon_saved_kg=row["total_carbon_saved"],
                streak_days=row["max_streak"],
                level=row["level"],
                badges_count=row["badges_count"],
                team_name=row["team_name"],
            )
        return None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Utility / seeding
# ---------------------------------------------------------------------------

def seed_sample_teams():
    """Insert sample teams if none exist."""
    conn = _get_conn()
    try:
        count = conn.execute("SELECT COUNT(*) AS cnt FROM teams").fetchone()["cnt"]
        if count > 0:
            return

        now = datetime.utcnow().isoformat()
        for team in SAMPLE_TEAMS:
            conn.execute(
                "INSERT OR IGNORE INTO teams (team_id, name, description, created_by, created_at, icon) VALUES (?, ?, ?, 0, ?, ?)",
                (team["id"], team["name"], team["desc"], now, team["icon"]),
            )
        conn.commit()
    finally:
        conn.close()


def seed_sample_challenges():
    """Insert sample team challenges if none exist."""
    conn = _get_conn()
    try:
        count = conn.execute("SELECT COUNT(*) AS cnt FROM team_challenges").fetchone()["cnt"]
        if count > 0:
            return

        now = datetime.utcnow()
        challenges = [
            ("tc_weekly_carbon_cut", "Weekly Carbon Cut", "Teams compete to save the most carbon this week", "overall", 50, 7, 200, "🏆"),
            ("tc_transport_takeover", "Transport Takeover", "Switch to green transport and log your savings", "transport", 30, 14, 300, "🚲"),
            ("tc_energy_elimination", "Energy Elimination", "Reduce your electricity usage and prove it", "energy", 40, 10, 250, "⚡"),
            ("tc_diet_revolution", "Diet Revolution", "Eat more plant-based meals and track impact", "diet", 25, 7, 150, "🥗"),
            ("tc_water_guardians", "Water Guardians", "Conserve water and log daily savings", "water", 20, 7, 100, "💧"),
        ]
        for ch_id, title, desc, cat, target, days, xp, icon in challenges:
            ends = now + timedelta(days=days)
            conn.execute(
                """INSERT OR IGNORE INTO team_challenges
                   (challenge_id, title, description, category, target_kg, duration_days,
                    xp_reward, starts_at, ends_at, status, icon)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)""",
                (ch_id, title, desc, cat, target, days, xp, now.isoformat(), ends.isoformat(), icon),
            )
        conn.commit()
    finally:
        conn.close()
