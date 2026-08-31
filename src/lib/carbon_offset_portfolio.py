"""
Carbon Offset Portfolio Tracker
===============================

Manages a user's carbon offset investment portfolio: adding offset purchases,
computing portfolio analytics (diversification, cost-efficiency, risk),
tracking net-zero progress, and projecting future offset trajectories.
"""

import sqlite3
import json
import math
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

from src.core.database import DB_NAME

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Offset project catalog
# ---------------------------------------------------------------------------
OFFSET_PROJECTS: dict[str, dict[str, Any]] = {
    "reforestation_amazon": {
        "name": "Amazon Reforestation",
        "category": "reforestation",
        "region": "South America",
        "price_per_tonne": 25.0,
        "rating": 4.8,
        "co_benefits": ["biodiversity", "water", "community"],
        "vintage": "2024",
        "verification": "Verra VCS",
    },
    "wind_india": {
        "name": "Wind Energy India",
        "category": "renewable_energy",
        "region": "Asia",
        "price_per_tonne": 18.5,
        "rating": 4.5,
        "co_benefits": ["air_quality", "jobs"],
        "vintage": "2024",
        "verification": "Gold Standard",
    },
    "methane_landfill_us": {
        "name": "Landfill Methane Capture US",
        "category": "methane_capture",
        "region": "North America",
        "price_per_tonne": 12.0,
        "rating": 4.2,
        "co_benefits": ["air_quality"],
        "vintage": "2024",
        "verification": "Climate Action Reserve",
    },
    "cookstoves_africa": {
        "name": "Clean Cookstoves East Africa",
        "category": "community",
        "region": "Africa",
        "price_per_tonne": 15.0,
        "rating": 4.6,
        "co_benefits": ["health", "women_empowerment", "jobs"],
        "vintage": "2024",
        "verification": "Gold Standard",
    },
    "ocean_kelp": {
        "name": "Kelp Forest Restoration",
        "category": "blue_carbon",
        "region": "Oceania",
        "price_per_tonne": 35.0,
        "rating": 4.3,
        "co_benefits": ["marine_life", "fisheries"],
        "vintage": "2024",
        "verification": "Plan Vivo",
    },
    "solar_mexico": {
        "name": "Solar Microgrids Mexico",
        "category": "renewable_energy",
        "region": "Latin America",
        "price_per_tonne": 20.0,
        "rating": 4.4,
        "co_benefits": ["energy_access", "jobs"],
        "vintage": "2024",
        "verification": "Gold Standard",
    },
}

RISK_WEIGHTS: dict[str, float] = {
    "reforestation": 0.7,
    "renewable_energy": 0.3,
    "methane_capture": 0.4,
    "community": 0.5,
    "blue_carbon": 0.6,
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class OffsetHolding:
    """Single offset purchase record."""
    id: Optional[int] = None
    user_id: int = 0
    project_id: str = ""
    tonnes: float = 0.0
    cost_usd: float = 0.0
    purchase_date: str = ""
    notes: str = ""


@dataclass
class PortfolioSummary:
    """Aggregated portfolio analytics."""
    total_tonnes: float = 0.0
    total_cost_usd: float = 0.0
    avg_cost_per_tonne: float = 0.0
    diversification_score: float = 0.0
    risk_rating: str = "Low"
    risk_score: float = 0.0
    category_breakdown: dict = field(default_factory=dict)
    regional_breakdown: dict = field(default_factory=dict)
    verification_breakdown: dict = field(default_factory=dict)
    holdings_count: int = 0
    net_zero_progress_pct: float = 0.0
    projected_neutral_date: Optional[str] = None


@dataclass
class NetZeroProjection:
    """Projection toward carbon neutrality."""
    annual_emissions_kg: float = 0.0
    current_offset_tonnes: float = 0.0
    annual_offset_rate_tonnes: float = 0.0
    years_to_neutral: Optional[float] = None
    neutral_date: Optional[str] = None
    monthly_offset_needed_tonnes: float = 0.0
    cost_to_neutral_usd: float = 0.0
    recommended_actions: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------
def _get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_offset_portfolio_db() -> None:
    """Create the portfolio tables if they don't exist."""
    conn = _get_conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS offset_holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                project_id TEXT NOT NULL,
                tonnes REAL NOT NULL,
                cost_usd REAL NOT NULL,
                purchase_date TEXT NOT NULL,
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS offset_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                snapshot_date TEXT NOT NULL,
                total_tonnes REAL,
                total_cost REAL,
                diversification_score REAL,
                risk_rating TEXT,
                payload TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
    except sqlite3.Error as exc:
        logger.error("Failed to init offset portfolio DB: %s", exc)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------
def add_offset_purchase(
    user_id: int,
    project_id: str,
    tonnes: float,
    cost_usd: float,
    purchase_date: Optional[str] = None,
    notes: str = "",
) -> Optional[int]:
    """Record a new offset purchase. Returns the new holding id or None."""
    if project_id not in OFFSET_PROJECTS:
        logger.warning("Unknown project_id: %s", project_id)
        return None
    if tonnes <= 0 or cost_usd < 0:
        logger.warning("Invalid tonnes=%.2f or cost=%.2f", tonnes, cost_usd)
        return None

    date = purchase_date or datetime.utcnow().strftime("%Y-%m-%d")
    conn = _get_conn()
    try:
        cursor = conn.execute(
            """
            INSERT INTO offset_holdings
                (user_id, project_id, tonnes, cost_usd, purchase_date, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, project_id, round(tonnes, 4), round(cost_usd, 2), date, notes),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as exc:
        logger.error("Failed to add offset purchase: %s", exc)
        return None
    finally:
        conn.close()


def get_user_holdings(user_id: int) -> list[OffsetHolding]:
    """Return all offset holdings for *user_id*."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM offset_holdings WHERE user_id = ? ORDER BY purchase_date DESC",
            (user_id,),
        ).fetchall()
        return [
            OffsetHolding(
                id=r["id"],
                user_id=r["user_id"],
                project_id=r["project_id"],
                tonnes=r["tonnes"],
                cost_usd=r["cost_usd"],
                purchase_date=r["purchase_date"],
                notes=r["notes"],
            )
            for r in rows
        ]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


def delete_offset_holding(user_id: int, holding_id: int) -> bool:
    """Remove a single holding."""
    conn = _get_conn()
    try:
        conn.execute(
            "DELETE FROM offset_holdings WHERE id = ? AND user_id = ?",
            (holding_id, user_id),
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Failed to delete holding %s: %s", holding_id, exc)
        return False
    finally:
        conn.close()


def clear_user_holdings(user_id: int) -> bool:
    """Remove all holdings for a user."""
    conn = _get_conn()
    try:
        conn.execute("DELETE FROM offset_holdings WHERE user_id = ?", (user_id,))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
def _diversification_score(category_counts: dict[str, int], total: float) -> float:
    """
    Shannon-entropy-based diversification score normalised to 0-100.
    Higher means more balanced across categories.
    """
    if total <= 0 or len(category_counts) <= 1:
        return 0.0

    import math as _m
    proportions = [c / total for c in category_counts.values() if c > 0]
    entropy = -sum(p * _m.log2(p) for p in proportions if p > 0)
    max_entropy = _m.log2(len(proportions))
    return round((entropy / max_entropy) * 100, 1) if max_entropy > 0 else 0.0


def _risk_assessment(holdings: list[OffsetHolding]) -> tuple[float, str]:
    """Weighted average risk across portfolio based on project category weights."""
    if not holdings:
        return 0.0, "N/A"

    weighted_risk = 0.0
    total_tonnes = 0.0
    for h in holdings:
        project = OFFSET_PROJECTS.get(h.project_id, {})
        cat = project.get("category", "community")
        weight = RISK_WEIGHTS.get(cat, 0.5)
        weighted_risk += weight * h.tonnes
        total_tonnes += h.tonnes

    if total_tonnes == 0:
        return 0.0, "N/A"

    score = round(weighted_risk / total_tonnes, 2)
    if score <= 0.35:
        rating = "Low"
    elif score <= 0.55:
        rating = "Medium"
    else:
        rating = "Elevated"
    return score, rating


def compute_portfolio_summary(
    user_id: int,
    annual_emissions_kg: float = 0.0,
) -> PortfolioSummary:
    """Build a full portfolio summary for *user_id*."""
    holdings = get_user_holdings(user_id)
    if not holdings:
        return PortfolioSummary()

    total_tonnes = sum(h.tonnes for h in holdings)
    total_cost = sum(h.cost_usd for h in holdings)
    avg_cost = total_cost / total_tonnes if total_tonnes > 0 else 0.0

    # Category breakdown
    cat_tonnes: dict[str, float] = {}
    cat_cost: dict[str, float] = {}
    reg_tonnes: dict[str, float] = {}
    ver_tonnes: dict[str, float] = {}

    for h in holdings:
        project = OFFSET_PROJECTS.get(h.project_id, {})
        cat = project.get("category", "other")
        reg = project.get("region", "Unknown")
        ver = project.get("verification", "Unknown")

        cat_tonnes[cat] = cat_tonnes.get(cat, 0) + h.tonnes
        cat_cost[cat] = cat_cost.get(cat, 0) + h.cost_usd
        reg_tonnes[reg] = reg_tonnes.get(reg, 0) + h.tonnes
        ver_tonnes[ver] = ver_tonnes.get(ver, 0) + h.tonnes

    cat_counts = {k: int(v) for k, v in cat_tonnes.items()}
    div_score = _diversification_score(cat_counts, total_tonnes)
    risk_score, risk_rating = _risk_assessment(holdings)

    category_breakdown = {}
    for cat in cat_tonnes:
        category_breakdown[cat] = {
            "tonnes": round(cat_tonnes[cat], 4),
            "cost_usd": round(cat_cost.get(cat, 0), 2),
            "pct": round(cat_tonnes[cat] / total_tonnes * 100, 1) if total_tonnes else 0,
        }

    regional_breakdown = {k: round(v, 4) for k, v in reg_tonnes.items()}
    verification_breakdown = {k: round(v, 4) for k, v in ver_tonnes.items()}

    net_zero_pct = 0.0
    neutral_date = None
    if annual_emissions_kg > 0:
        annual_emissions_tonnes = annual_emissions_kg / 1000.0
        net_zero_pct = round((total_tonnes / annual_emissions_tonnes) * 100, 2)
        if total_tonnes < annual_emissions_tonnes:
            years_left = (annual_emissions_tonnes - total_tonnes) / annual_emissions_tonnes
            neutral_date = (datetime.utcnow() + timedelta(days=years_left * 365)).strftime("%Y-%m-%d")

    return PortfolioSummary(
        total_tonnes=round(total_tonnes, 4),
        total_cost_usd=round(total_cost, 2),
        avg_cost_per_tonne=round(avg_cost, 2),
        diversification_score=div_score,
        risk_rating=risk_rating,
        risk_score=risk_score,
        category_breakdown=category_breakdown,
        regional_breakdown=regional_breakdown,
        verification_breakdown=verification_breakdown,
        holdings_count=len(holdings),
        net_zero_progress_pct=min(net_zero_pct, 100.0),
        projected_neutral_date=neutral_date,
    )


# ---------------------------------------------------------------------------
# Net-zero projection
# ---------------------------------------------------------------------------
def project_net_zero(
    user_id: int,
    annual_emissions_kg: float,
    monthly_offset_budget_usd: float = 0.0,
) -> NetZeroProjection:
    """Compute a net-zero roadmap projection."""
    holdings = get_user_holdings(user_id)
    total_offset_tonnes = sum(h.tonnes for h in holdings)

    if not holdings:
        annual_rate = 0.0
    else:
        dates = sorted(h.purchase_date for h in holdings)
        try:
            first = datetime.fromisoformat(dates[0])
            last = datetime.fromisoformat(dates[-1])
            span_years = max((last - first).days / 365.0, 1 / 365)
            annual_rate = total_offset_tonnes / span_years
        except (ValueError, TypeError):
            annual_rate = 0.0

    annual_emissions_tonnes = annual_emissions_kg / 1000.0
    remaining = max(0, annual_emissions_tonnes - total_offset_tonnes)

    years_to_neutral = None
    neutral_date = None
    monthly_needed = 0.0
    cost_to_neutral = 0.0
    recommended: list[str] = []

    if remaining > 0 and annual_rate > 0:
        years_to_neutral = round(remaining / annual_rate, 1)
        neutral_date = (datetime.utcnow() + timedelta(days=years_to_neutral * 365)).strftime("%Y-%m-%d")
        monthly_needed = round(remaining / max(years_to_neutral * 12, 1), 4)

        # Estimate cost at average market price
        avg_price = 22.0  # blended average across projects
        cost_to_neutral = round(monthly_needed * 12 * avg_price, 2)
    elif remaining <= 0:
        recommended.append("🎉 You are already carbon-neutral via offsets!")
    else:
        recommended.append("Start offsetting regularly to build momentum.")

    if annual_emissions_kg > 5000:
        recommended.append("Your emissions are high — consider reducing transport or electricity usage.")
    if total_offset_tonnes < annual_emissions_tonnes * 0.1:
        recommended.append("You've offset less than 10% — increase your offset purchases.")
    if monthly_offset_budget_usd > 0 and cost_to_neutral > 0:
        months_budget = cost_to_neutral / monthly_offset_budget_usd
        if months_budget < (years_to_neutral or 999) * 12:
            recommended.append(
                f"At ${monthly_offset_budget_usd:.0f}/mo you'd reach neutrality in "
                f"~{months_budget:.0f} months instead of {years_to_neutral} years."
            )

    return NetZeroProjection(
        annual_emissions_kg=annual_emissions_kg,
        current_offset_tonnes=round(total_offset_tonnes, 4),
        annual_offset_rate_tonnes=round(annual_rate, 4),
        years_to_neutral=years_to_neutral,
        neutral_date=neutral_date,
        monthly_offset_needed_tonnes=monthly_needed,
        cost_to_neutral_usd=cost_to_neutral,
        recommended_actions=recommended,
    )


# ---------------------------------------------------------------------------
# Snapshot persistence
# ---------------------------------------------------------------------------
def save_portfolio_snapshot(user_id: int) -> bool:
    """Persist a portfolio snapshot for historical tracking."""
    summary = compute_portfolio_summary(user_id)
    conn = _get_conn()
    try:
        conn.execute(
            """
            INSERT INTO offset_snapshots
                (user_id, snapshot_date, total_tonnes, total_cost,
                 diversification_score, risk_rating, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                datetime.utcnow().strftime("%Y-%m-%d"),
                summary.total_tonnes,
                summary.total_cost_usd,
                summary.diversification_score,
                summary.risk_rating,
                json.dumps(asdict(summary), default=str),
            ),
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Snapshot save failed: %s", exc)
        return False
    finally:
        conn.close()


def get_portfolio_snapshots(user_id: int, limit: int = 12) -> list[dict]:
    """Load historical portfolio snapshots."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT id, snapshot_date, total_tonnes, total_cost,
                   diversification_score, risk_rating, payload
            FROM offset_snapshots
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()
