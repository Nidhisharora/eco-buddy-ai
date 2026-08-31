"""
Portfolio Analytics Engine

Provides comprehensive portfolio analytics for the Carbon Offset Portfolio
Tracker, including diversification scoring, value calculations, risk-weighted
returns, and allocation optimization.
"""

from __future__ import annotations

import logging
import math
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.portfolio.models import (
    OffsetProject,
    OffsetTransaction,
    PortfolioHolding,
    PortfolioSnapshot,
    ProjectType,
    RiskAssessment,
    RiskLevel,
    TransactionType,
)

logger = logging.getLogger(__name__)


# ── Constants ─────────────────────────────────────────────────────────────

MAX_DIVERSIFICATION_PROJECTS = 10
MAX_DIVERSIFICATION_TYPES = 6
MAX_DIVERSIFICATION_REGISTRIES = 4
VINTAGE_FRESHNESS_PENALTY_YEARS = 3
MIN_RISK_FREE_RATE = 0.02
MARKET_AVG_CARBON_PRICE_USD = 25.0


# ── Pure helper functions ─────────────────────────────────────────────────


def calculate_portfolio_value(holdings: List[PortfolioHolding]) -> float:
    """Sum the cost basis across all holdings."""
    return sum(h.cost_basis for h in holdings)


def calculate_current_value(holdings: List[PortfolioHolding]) -> float:
    """Sum the latest valuation across all active units."""
    total = 0.0
    for h in holdings:
        if h.last_valuation > 0:
            total += h.last_valuation * h.units_available
        else:
            total += h.avg_cost_per_unit * h.units_available
    return round(total, 2)


def calculate_total_carbon_kg(holdings: List[PortfolioHolding]) -> float:
    """Total carbon represented by held units (1 unit = 1 tCO₂e = 1000 kg)."""
    return float(sum(h.units_available for h in holdings)) * 1000.0


def calculate_total_carbon_retired_kg(holdings: List[PortfolioHolding]) -> float:
    """Total carbon retired by the user."""
    return float(sum(h.units_retired for h in holdings)) * 1000.0


def calculate_diversification_score(holdings: List[PortfolioHolding]) -> float:
    """
    Score 0-100 measuring how well-diversified a portfolio is.
    Based on distribution across project types, registries, vintage years,
    and countries. Higher = better diversified.
    """
    if not holdings:
        return 0.0

    n = len(holdings)

    # Type diversity (Shannon entropy normalized)
    type_counts = Counter(h.project_type.value for h in holdings)
    type_entropy = _shannon_entropy(type_counts)
    max_type_entropy = math.log2(MAX_DIVERSIFICATION_TYPES) if MAX_DIVERSIFICATION_TYPES > 1 else 1.0
    type_score = min(type_entropy / max_type_entropy, 1.0) * 100

    # Registry diversity
    registry_counts = Counter(h.registry for h in holdings)
    registry_entropy = _shannon_entropy(registry_counts)
    max_reg_entropy = math.log2(MAX_DIVERSIFICATION_REGISTRIES) if MAX_DIVERSIFICATION_REGISTRIES > 1 else 1.0
    registry_score = min(registry_entropy / max_reg_entropy, 1.0) * 100

    # Vintage diversity
    vintage_counts = Counter(str(h.vintage_year) for h in holdings)
    vintage_entropy = _shannon_entropy(vintage_counts)
    max_vintage_entropy = math.log2(max(len(vintage_counts), 2))
    vintage_score = min(vintage_entropy / max_vintage_entropy, 1.0) * 100

    # Concentration penalty — if one holding > 50% of portfolio by value
    total_value = sum(h.cost_basis for h in holdings) or 1.0
    max_single_pct = max(h.cost_basis / total_value for h in holdings)
    concentration_penalty = max(0, (max_single_pct - 0.4) * 100)

    # Weighted average
    raw_score = (type_score * 0.35) + (registry_score * 0.25) + (vintage_score * 0.20)
    # Bonus for having many projects
    project_count_bonus = min(n / MAX_DIVERSIFICATION_PROJECTS, 1.0) * 20

    final = raw_score + project_count_bonus - concentration_penalty
    return round(max(0.0, min(100.0, final)), 1)


def _shannon_entropy(counts: Counter) -> float:
    """Compute Shannon entropy from a Counter."""
    total = sum(counts.values())
    if total == 0:
        return 0.0
    entropy = 0.0
    for count in counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy


def calculate_weighted_risk(
    holdings: List[PortfolioHolding],
    risk_assessments: Dict[str, RiskAssessment],
) -> float:
    """
    Compute a portfolio-weighted risk score (0-100).
    Risk assessments are keyed by project_id.
    Missing risk data defaults to 50 (medium).
    """
    if not holdings:
        return 50.0

    total_value = sum(h.cost_basis for h in holdings) or 1.0
    weighted_score = 0.0

    for h in holdings:
        weight = h.cost_basis / total_value
        assessment = risk_assessments.get(h.project_id)
        risk_val = assessment.overall_risk_score if assessment else 50.0
        weighted_score += weight * risk_val

    return round(weighted_score, 1)


def optimize_offset_allocation(
    target_co2_kg: float,
    budget_usd: float,
    available_projects: List[OffsetProject],
    risk_tolerance: str = "medium",
) -> List[Dict[str, Any]]:
    """
    Suggest an optimal allocation of offset purchases to meet a CO₂ target
    within budget, considering risk tolerance.

    Returns a list of dicts with keys: project_id, name, units, cost, rationale.
    """
    if not available_projects or budget_usd <= 0 or target_co2_kg <= 0:
        return []

    target_tonnes = target_co2_kg / 1000.0

    # Filter by risk tolerance
    risk_limits = {"conservative": 30.0, "medium": 60.0, "aggressive": 100.0}
    max_price = risk_limits.get(risk_tolerance, 60.0)

    candidates = [
        p for p in available_projects
        if p.available_units > 0 and p.unit_price_usd <= max_price
    ]

    if not candidates:
        return []

    # Sort by cost-effectiveness (lowest price first, then prefer higher co_benefits count)
    candidates.sort(key=lambda p: (p.unit_price_usd, -len(p.co_benefits)))

    allocations: List[Dict[str, Any]] = []
    remaining_budget = budget_usd
    remaining_tonnes = target_tonnes

    for project in candidates:
        if remaining_budget <= 0 or remaining_tonnes <= 0:
            break

        max_affordable = int(remaining_budget / project.unit_price_usd) if project.unit_price_usd > 0 else 0
        units_to_buy = min(max_affordable, project.available_units, int(remaining_tonnes) + 1)
        units_to_buy = max(0, min(units_to_buy, int(remaining_tonnes / 1.0) + 1))

        if units_to_buy <= 0:
            continue

        cost = units_to_buy * project.unit_price_usd
        remaining_budget -= cost
        remaining_tonnes -= units_to_buy

        rationale = _generate_allocation_rationale(project, units_to_buy, risk_tolerance)

        allocations.append({
            "project_id": project.project_id,
            "name": project.name,
            "project_type": project.project_type.value,
            "units": units_to_buy,
            "cost_usd": round(cost, 2),
            "co2_offset_tonnes": units_to_buy,
            "price_per_unit": project.unit_price_usd,
            "registry": project.registry,
            "country": project.country,
            "rationale": rationale,
        })

    return allocations


def _generate_allocation_rationale(
    project: OffsetProject, units: int, risk_tolerance: str
) -> str:
    """Generate a human-readable rationale for an allocation."""
    parts = []
    if project.unit_price_usd <= 10:
        parts.append("cost-effective")
    if len(project.co_benefits) >= 3:
        parts.append(f"{len(project.co_benefits)} co-benefits")
    if project.lifecycle_stage.value == "active":
        parts.append("active project")
    if project.registry in ("Verra", "Gold Standard"):
        parts.append(f"{project.registry} certified")
    if project.vintage_year >= datetime.utcnow().year - 1:
        parts.append("recent vintage")
    parts.append(f"{units} unit{'s' if units != 1 else ''}")

    return f"Selected: {', '.join(parts[:4])}"


# ── Portfolio-level analytics class ──────────────────────────────────────


class PortfolioAnalyzer:
    """
    High-level analytics engine that works with holdings, transactions,
    and risk data to produce portfolio-level insights.
    """

    def __init__(
        self,
        holdings: List[PortfolioHolding],
        transactions: Optional[List[OffsetTransaction]] = None,
        risk_assessments: Optional[Dict[str, RiskAssessment]] = None,
    ):
        self.holdings = holdings
        self.transactions = transactions or []
        self.risk_assessments = risk_assessments or {}

    def generate_snapshot(self, user_id: int) -> PortfolioSnapshot:
        """Build a comprehensive point-in-time portfolio snapshot."""
        total_held = sum(h.units_held for h in self.holdings)
        total_retired = sum(h.units_retired for h in self.holdings)
        total_invested = calculate_portfolio_value(self.holdings)
        current_val = calculate_current_value(self.holdings)
        unrealized = round(current_val - total_invested, 2)
        carbon_kg = calculate_total_carbon_kg(self.holdings)
        retired_kg = calculate_total_carbon_retired_kg(self.holdings)
        div_score = calculate_diversification_score(self.holdings)
        risk_score = calculate_weighted_risk(self.holdings, self.risk_assessments)

        # Registry breakdown
        registry_breakdown: Dict[str, int] = defaultdict(int)
        type_breakdown: Dict[str, int] = defaultdict(int)
        vintage_dist: Dict[str, int] = defaultdict(int)
        for h in self.holdings:
            registry_breakdown[h.registry] += h.units_available
            type_breakdown[h.project_type.value] += h.units_available
            vintage_dist[str(h.vintage_year)] += h.units_available

        snapshot = PortfolioSnapshot(
            user_id=user_id,
            total_units_held=total_held,
            total_units_retired=total_retired,
            total_invested_usd=round(total_invested, 2),
            current_value_usd=current_val,
            unrealized_gain_usd=unrealized,
            total_carbon_offset_kg=carbon_kg,
            total_carbon_retired_kg=retired_kg,
            diversification_score=div_score,
            risk_score=risk_score,
            lifecycle_health=self._compute_lifecycle_health(),
            project_count=len(self.holdings),
            registry_breakdown=dict(registry_breakdown),
            type_breakdown=dict(type_breakdown),
            vintage_distribution=dict(vintage_dist),
        )
        return snapshot

    def _compute_lifecycle_health(self) -> float:
        """Estimate lifecycle health (0-100) from vintage years and project states."""
        if not self.holdings:
            return 0.0

        current_year = datetime.utcnow().year
        scores: List[float] = []

        for h in self.holdings:
            age = current_year - h.vintage_year if h.vintage_year > 0 else 5
            if age <= 1:
                score = 95.0
            elif age <= 2:
                score = 85.0
            elif age <= VINTAGE_FRESHNESS_PENALTY_YEARS:
                score = 70.0
            elif age <= 5:
                score = 50.0
            else:
                score = max(20.0, 70.0 - (age - 5) * 5)

            scores.append(score)

        return round(sum(scores) / len(scores), 1)

    def get_purchase_history_summary(self) -> Dict[str, Any]:
        """Summarize purchase history for display."""
        purchases = [t for t in self.transactions if t.transaction_type == TransactionType.PURCHASE]
        retirements = [t for t in self.transactions if t.transaction_type == TransactionType.RETIREMENT]

        total_spent = sum(t.total_cost_usd for t in purchases)
        total_fees = sum(t.fee_usd for t in purchases)
        total_units_bought = sum(t.units for t in purchases)
        total_units_retired = sum(t.units for t in retirements)
        avg_price = (total_spent / total_units_bought) if total_units_bought > 0 else 0.0

        # Monthly spend breakdown
        monthly_spend: Dict[str, float] = defaultdict(float)
        for t in purchases:
            month_key = t.timestamp.strftime("%Y-%m")
            monthly_spend[month_key] += t.total_cost_usd

        return {
            "total_purchases": len(purchases),
            "total_retirements": len(retirements),
            "total_spent_usd": round(total_spent, 2),
            "total_fees_usd": round(total_fees, 2),
            "total_units_bought": total_units_bought,
            "total_units_retired": total_units_retired,
            "average_price_per_unit": round(avg_price, 2),
            "monthly_spend": dict(sorted(monthly_spend.items())),
        }

    def get_impact_metrics(self) -> Dict[str, Any]:
        """Compute environmental impact metrics from holdings and transactions."""
        total_offset_kg = calculate_total_carbon_kg(self.holdings)
        retired_kg = calculate_total_carbon_retired_kg(self.holdings)
        trees_equivalent = round(total_offset_kg / 22.0, 1)  # ~22 kg CO2 per tree per year
        cars_off_road_days = round(total_offset_kg / 12.6, 1)  # ~12.6 kg CO2/day per car
        flights_offset = round(total_offset_kg / 250.0, 1)  # ~250 kg CO2 per short flight

        # Co-benefits aggregation
        co_benefit_counts: Dict[str, int] = defaultdict(int)
        for h in self.holdings:
            # We don't store co_benefits in holdings directly, but we can track by type
            pass

        type_carbon: Dict[str, float] = defaultdict(float)
        for h in self.holdings:
            type_carbon[h.project_type.value] += h.units_available * 1000

        return {
            "total_offset_kg": total_offset_kg,
            "total_retired_kg": retired_kg,
            "trees_equivalent": trees_equivalent,
            "cars_off_road_days": cars_off_road_days,
            "flights_offset": flights_offset,
            "effective_cost_per_tonne": (
                round(self._total_invested() / (total_offset_kg / 1000), 2)
                if total_offset_kg > 0
                else 0.0
            ),
            "carbon_by_type": dict(type_carbon),
        }

    def _total_invested(self) -> float:
        return sum(h.total_invested_usd for h in self.holdings)

    def generate_insights(self) -> List[Dict[str, str]]:
        """Produce actionable portfolio insights."""
        insights: List[Dict[str, str]] = []

        if not self.holdings:
            insights.append({
                "title": "No offset holdings yet",
                "message": "Start building your offset portfolio by purchasing credits from verified projects.",
                "icon": "🌱",
                "category": "getting_started",
            })
            return insights

        div_score = calculate_diversification_score(self.holdings)
        if div_score < 40:
            insights.append({
                "title": "Low diversification",
                "message": (
                    f"Your diversification score is {div_score}/100. "
                    "Consider spreading investments across different project types and registries."
                ),
                "icon": "📊",
                "category": "diversification",
            })

        risk = calculate_weighted_risk(self.holdings, self.risk_assessments)
        if risk > 70:
            insights.append({
                "title": "High portfolio risk",
                "message": (
                    f"Your weighted risk score is {risk:.0f}/100. "
                    "Consider adding offset projects from established registries."
                ),
                "icon": "⚠️",
                "category": "risk",
            })

        # Vintage freshness check
        current_year = datetime.utcnow().year
        old_vintage_count = sum(
            1 for h in self.holdings
            if h.vintage_year > 0 and current_year - h.vintage_year > 3
        )
        if old_vintage_count > 0:
            insights.append({
                "title": "Aging vintage credits",
                "message": (
                    f"{old_vintage_count} holding(s) have vintages older than 3 years. "
                    "Older credits may have reduced market value and credibility."
                ),
                "icon": "📅",
                "category": "vintage",
            })

        # Single registry concentration
        registries = set(h.registry for h in self.holdings if h.registry)
        if len(registries) == 1 and len(self.holdings) > 1:
            insights.append({
                "title": "Single registry dependency",
                "message": (
                    f"All holdings use {list(registries)[0]}. "
                    "Diversifying across registries (Verra, Gold Standard, ACR) reduces counterparty risk."
                ),
                "icon": "🏛️",
                "category": "registry",
            })

        # Low retirements
        total_held = sum(h.units_held for h in self.holdings)
        total_retired = sum(h.units_retired for h in self.holdings)
        if total_held > 0 and total_retired == 0:
            insights.append({
                "title": "No retired offsets yet",
                "message": (
                    "You haven't retired any offset credits. "
                    "Retiring credits permanently claims their environmental benefit."
                ),
                "icon": "🔄",
                "category": "retirement",
            })

        # Cost efficiency vs market average
        impact = self.get_impact_metrics()
        if impact["effective_cost_per_tonne"] > 0:
            efficiency = impact["effective_cost_per_tonne"]
            if efficiency > MARKET_AVG_CARBON_PRICE_USD * 1.5:
                insights.append({
                    "title": "Above-market pricing",
                    "message": (
                        f"Your effective cost is ${efficiency:.2f}/tCO₂ vs the ~${MARKET_AVG_CARBON_PRICE_USD:.0f} "
                        "market average. Consider cost-effective project types."
                    ),
                    "icon": "💰",
                    "category": "cost",
                })
            elif efficiency < MARKET_AVG_CARBON_PRICE_USD * 0.5:
                insights.append({
                    "title": "Great cost efficiency",
                    "message": (
                        f"Your effective cost is ${efficiency:.2f}/tCO₂ — well below market average. "
                        "Ensure the quality and additionality of your offsets."
                    ),
                    "icon": "✅",
                    "category": "cost",
                })

        return insights


# ── Portfolio comparison ──────────────────────────────────────────────────


def compare_snapshots(
    snapshots: List[PortfolioSnapshot],
) -> List[Dict[str, Any]]:
    """
    Compare a sequence of portfolio snapshots and return trend data.
    Each item represents a metric change between consecutive snapshots.
    """
    if len(snapshots) < 2:
        return []

    trends: List[Dict[str, Any]] = []
    for i in range(1, len(snapshots)):
        curr = snapshots[i]
        prev = snapshots[i - 1]

        metrics = [
            ("Investment ($)", prev.total_invested_usd, curr.total_invested_usd),
            ("Current Value ($)", prev.current_value_usd, curr.current_value_usd),
            ("Carbon Offset (kg)", prev.total_carbon_offset_kg, curr.total_carbon_offset_kg),
            ("Diversification", prev.diversification_score, curr.diversification_score),
            ("Risk Score", prev.risk_score, curr.risk_score),
            ("Lifecycle Health", prev.lifecycle_health, curr.lifecycle_health),
        ]

        trend_data: Dict[str, Any] = {
            "from_date": prev.timestamp.isoformat(),
            "to_date": curr.timestamp.isoformat(),
            "metrics": [],
        }

        for name, prev_val, curr_val in metrics:
            delta = curr_val - prev_val
            pct = (delta / prev_val * 100) if prev_val else 0
            trend_data["metrics"].append({
                "name": name,
                "previous": prev_val,
                "current": curr_val,
                "delta": round(delta, 2),
                "delta_percent": round(pct, 1),
                "direction": (
                    "improved" if (
                        ("Risk" in name and delta < 0)
                        or ("Risk" not in name and delta > 0)
                    )
                    else ("worsened" if delta != 0 else "stable")
                ),
            })

        trends.append(trend_data)

    return trends
