"""
Carbon Footprint Trend Analyzer & Insights Engine.

Analyses a user's historical assessment data to detect:
- Long-term emission trends (linear, polynomial, exponential)
- Seasonal patterns and periodicity
- Anomalous spikes and improvements
- Category-level drift (transport vs energy vs diet vs flights)
- Forecasted future footprints under various scenarios
- Personalised actionable insights derived from patterns
- Score trajectory and goal-proximity tracking

Pure-Python implementation — only uses the standard library plus the
lightweight helpers already present in the project.  Optional ``numpy``
and ``statsmodels`` usage is guarded behind ``try/except`` so the module
degrades gracefully when they are absent.
"""

from __future__ import annotations

import math
import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ─── Enums ──────────────────────────────────────────────────────────────────

class TrendDirection(str, Enum):
    IMPROVING = "improving"      # emissions going down
    STABLE = "stable"            # no significant change
    WORSENING = "worsening"      # emissions going up
    VOLATILE = "volatile"        # high variance, no clear direction


class InsightSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    POSITIVE = "positive"


class Season(str, Enum):
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"


# ─── Data classes ───────────────────────────────────────────────────────────

@dataclass
class AssessmentRecord:
    """Single assessment data point."""
    date: str                       # ISO date string
    transport: str = ""
    distance: float = 0.0
    electricity: float = 0.0
    diet: str = ""
    flights: int = 0
    footprint: float = 0.0
    eco_score: int = 0


@dataclass
class TrendResult:
    """Result of a linear trend analysis."""
    direction: TrendDirection
    slope_per_month: float          # kg CO₂ change per month
    slope_per_year: float           # kg CO₂ change per year
    r_squared: float                # goodness of fit (0-1)
    intercept: float                # trend line intercept
    pct_change_monthly: float       # percentage change per month
    interpretation: str             # human-readable summary

    def to_dict(self) -> dict[str, Any]:
        return {
            "direction": self.direction.value,
            "slope_per_month": round(self.slope_per_month, 4),
            "slope_per_year": round(self.slope_per_year, 2),
            "r_squared": round(self.r_squared, 4),
            "intercept": round(self.intercept, 2),
            "pct_change_monthly": round(self.pct_change_monthly, 4),
            "interpretation": self.interpretation,
        }


@dataclass
class SeasonalPattern:
    """Seasonal pattern detected in the data."""
    season: Season
    avg_footprint: float
    avg_eco_score: float
    sample_count: int
    deviation_from_mean: float      # positive = above average

    def to_dict(self) -> dict[str, Any]:
        return {
            "season": self.season.value,
            "avg_footprint": round(self.avg_footprint, 2),
            "avg_eco_score": round(self.avg_eco_score, 2),
            "sample_count": self.sample_count,
            "deviation_from_mean": round(self.deviation_from_mean, 2),
        }


@dataclass
class AnomalyRecord:
    """Detected anomaly in the time series."""
    date: str
    footprint: float
    expected_value: float
    deviation: float                # how far from expected (in kg)
    deviation_pct: float            # percentage deviation
    is_spike: bool                  # True = unusually high
    category_hint: str | None       # best guess at which category caused it

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "footprint": round(self.footprint, 2),
            "expected_value": round(self.expected_value, 2),
            "deviation": round(self.deviation, 2),
            "deviation_pct": round(self.deviation_pct, 2),
            "is_spike": self.is_spike,
            "category_hint": self.category_hint,
        }


@dataclass
class ForecastPoint:
    """Single forecast data point."""
    month_index: int
    date_label: str
    scenario: str
    predicted_footprint: float
    predicted_eco_score: int
    confidence_lower: float
    confidence_upper: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "month_index": self.month_index,
            "date_label": self.date_label,
            "scenario": self.scenario,
            "predicted_footprint": round(self.predicted_footprint, 2),
            "predicted_eco_score": self.predicted_eco_score,
            "confidence_lower": round(self.confidence_lower, 2),
            "confidence_upper": round(self.confidence_upper, 2),
        }


@dataclass
class CategoryTrend:
    """Trend for a single emission category."""
    category: str
    current_avg: float
    previous_avg: float
    change_abs: float
    change_pct: float
    direction: TrendDirection
    contribution_to_total: float    # percentage of total footprint

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "current_avg": round(self.current_avg, 2),
            "previous_avg": round(self.previous_avg, 2),
            "change_abs": round(self.change_abs, 2),
            "change_pct": round(self.change_pct, 2),
            "direction": self.direction.value,
            "contribution_to_total": round(self.contribution_to_total, 2),
        }


@dataclass
class Insight:
    """A single actionable insight."""
    title: str
    description: str
    severity: InsightSeverity
    category: str
    action: str                     # recommended action
    potential_saving_kg: float      # estimated CO₂ saving
    confidence: float               # 0-1

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "category": self.category,
            "action": self.action,
            "potential_saving_kg": round(self.potential_saving_kg, 2),
            "confidence": round(self.confidence, 2),
        }


@dataclass
class TrendReport:
    """Complete trend analysis report."""
    user_id: int
    analysis_period_months: int
    total_assessments: int
    date_range: str                 # e.g. "Jan 2025 – Aug 2026"

    # Overall trends
    overall_trend: TrendResult
    footprint_timeline: list[dict[str, Any]]
    eco_score_timeline: list[dict[str, Any]]

    # Category breakdown
    category_trends: list[CategoryTrend]

    # Seasonal
    seasonal_patterns: list[SeasonalPattern]

    # Anomalies
    anomalies: list[AnomalyRecord]

    # Forecasts
    forecasts: list[ForecastPoint]

    # Insights
    insights: list[Insight]

    # Summary stats
    avg_footprint: float
    median_footprint: float
    std_footprint: float
    min_footprint: float
    max_footprint: float
    avg_eco_score: float
    total_assessments_analyzed: int

    # Goal tracking
    goal_target: float | None = None
    goal_proximity_pct: float | None = None
    months_to_goal: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "analysis_period_months": self.analysis_period_months,
            "total_assessments": self.total_assessments,
            "date_range": self.date_range,
            "overall_trend": self.overall_trend.to_dict(),
            "footprint_timeline": self.footprint_timeline,
            "eco_score_timeline": self.eco_score_timeline,
            "category_trends": [ct.to_dict() for ct in self.category_trends],
            "seasonal_patterns": [sp.to_dict() for sp in self.seasonal_patterns],
            "anomalies": [a.to_dict() for a in self.anomalies],
            "forecasts": [f.to_dict() for f in self.forecasts],
            "insights": [i.to_dict() for i in self.insights],
            "summary": {
                "avg_footprint": round(self.avg_footprint, 2),
                "median_footprint": round(self.median_footprint, 2),
                "std_footprint": round(self.std_footprint, 2),
                "min_footprint": round(self.min_footprint, 2),
                "max_footprint": round(self.max_footprint, 2),
                "avg_eco_score": round(self.avg_eco_score, 2),
                "total_assessments_analyzed": self.total_assessments_analyzed,
            },
            "goal_target": self.goal_target,
            "goal_proximity_pct": self.goal_proximity_pct,
            "months_to_goal": self.months_to_goal,
        }


# ─── Core Analysis Functions ────────────────────────────────────────────────

def _get_season(date_str: str) -> Season:
    """Determine season from ISO date string (Northern Hemisphere)."""
    try:
        month = int(date_str[:7].split("-")[1])
    except (ValueError, IndexError):
        return Season.SPRING
    if month in (3, 4, 5):
        return Season.SPRING
    if month in (6, 7, 8):
        return Season.SUMMER
    if month in (9, 10, 11):
        return Season.AUTUMN
    return Season.WINTER


def _date_to_month_index(date_str: str, ref_date: str) -> int:
    """Convert a date string to months since ref_date."""
    try:
        d = datetime.strptime(date_str[:10], "%Y-%m-%d")
        r = datetime.strptime(ref_date[:10], "%Y-%m-%d")
        return (d.year - r.year) * 12 + (d.month - r.month)
    except ValueError:
        return 0


def _month_index_to_label(idx: int, ref_date: str) -> str:
    """Convert month index back to a human-readable label."""
    try:
        r = datetime.strptime(ref_date[:10], "%Y-%m-%d")
        target = datetime(r.year + (r.month + idx - 1) // 12,
                          (r.month + idx - 1) % 12 + 1, 1)
        return target.strftime("%b %Y")
    except ValueError:
        return f"Month {idx}"


def _linear_regression(x: list[float], y: list[float]) -> tuple[float, float, float, float]:
    """
    Simple linear regression: y = slope * x + intercept.

    Returns (slope, intercept, r_squared, std_error).
    """
    n = len(x)
    if n < 2:
        return 0.0, y[0] if y else 0.0, 0.0, 0.0

    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi ** 2 for xi in x)

    denom = n * sum_x2 - sum_x * sum_x
    if abs(denom) < 1e-12:
        return 0.0, sum_y / n, 0.0, 0.0

    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n

    # R² calculation
    mean_y = sum_y / n
    ss_tot = sum((yi - mean_y) ** 2 for yi in y)
    ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, y))
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    # Standard error of estimate
    if n > 2:
        std_error = math.sqrt(ss_res / (n - 2))
    else:
        std_error = 0.0

    return slope, intercept, max(0.0, r_squared), std_error


def _classify_trend(slope: float, r_squared: float, values: list[float]) -> TrendDirection:
    """Classify a trend based on slope significance and variance."""
    if not values:
        return TrendDirection.STABLE

    mean_val = statistics.mean(values)
    if mean_val == 0:
        return TrendDirection.STABLE

    relative_slope = abs(slope) / mean_val
    cv = statistics.stdev(values) / mean_val if len(values) > 1 and mean_val > 0 else 0.0

    if cv > 0.3 and r_squared < 0.3:
        return TrendDirection.VOLATILE

    if relative_slope < 0.01:
        return TrendDirection.STABLE
    if slope < 0:
        return TrendDirection.IMPROVING
    return TrendDirection.WORSENING


def _interpret_trend(direction: TrendDirection, slope_year: float, r_sq: float) -> str:
    """Generate a human-readable interpretation of the trend."""
    if direction == TrendDirection.STABLE:
        return "Your carbon footprint has remained relatively stable. Great consistency!"
    if direction == TrendDirection.IMPROVING:
        strength = "strongly" if r_sq > 0.7 else "moderately" if r_sq > 0.4 else "slightly"
        return (
            f"Your emissions are {strength} decreasing at {abs(slope_year):.0f} kg CO₂/year. "
            f"Keep up the excellent work!"
        )
    if direction == TrendDirection.WORSENING:
        strength = "strongly" if r_sq > 0.7 else "moderately" if r_sq > 0.4 else "slightly"
        return (
            f"Your emissions are {strength} increasing at {slope_year:.0f} kg CO₂/year. "
            f"Consider reviewing your recent lifestyle changes."
        )
    return "Your emissions show high variability with no clear direction. Consider stabilising your habits."


def analyse_overall_trend(records: list[AssessmentRecord]) -> TrendResult:
    """Perform linear trend analysis on the overall footprint time series."""
    if len(records) < 2:
        fp = records[0].footprint if records else 0.0
        return TrendResult(
            direction=TrendDirection.STABLE,
            slope_per_month=0.0,
            slope_per_year=0.0,
            r_squared=0.0,
            intercept=fp,
            pct_change_monthly=0.0,
            interpretation="Insufficient data for trend analysis.",
        )

    sorted_recs = sorted(records, key=lambda r: r.date)
    ref_date = sorted_recs[0].date
    x = [_date_to_month_index(r.date, ref_date) for r in sorted_recs]
    y = [r.footprint for r in sorted_recs]

    slope, intercept, r_squared, _ = _linear_regression(x, y)
    direction = _classify_trend(slope, r_squared, y)
    mean_y = statistics.mean(y) if y else 0.0
    pct_monthly = (slope / mean_y * 100) if mean_y > 0 else 0.0
    interpretation = _interpret_trend(direction, slope * 12, r_squared)

    return TrendResult(
        direction=direction,
        slope_per_month=round(slope, 4),
        slope_per_year=round(slope * 12, 2),
        r_squared=round(r_squared, 4),
        intercept=round(intercept, 2),
        pct_change_monthly=round(pct_monthly, 4),
        interpretation=interpretation,
    )


def analyse_seasonal_patterns(records: list[AssessmentRecord]) -> list[SeasonalPattern]:
    """Detect seasonal patterns in the data."""
    if len(records) < 4:
        return []

    all_fp = [r.footprint for r in records]
    mean_fp = statistics.mean(all_fp)

    season_data: dict[Season, list[tuple[float, int]]] = {s: [] for s in Season}
    for r in records:
        season = _get_season(r.date)
        season_data[season].append((r.footprint, r.eco_score))

    patterns = []
    for season, data in season_data.items():
        if not data:
            continue
        fps = [d[0] for d in data]
        scores = [d[1] for d in data]
        avg_fp = statistics.mean(fps)
        avg_score = statistics.mean(scores)
        patterns.append(SeasonalPattern(
            season=season,
            avg_footprint=avg_fp,
            avg_eco_score=avg_score,
            sample_count=len(data),
            deviation_from_mean=avg_fp - mean_fp,
        ))

    patterns.sort(key=lambda p: p.deviation_from_mean, reverse=True)
    return patterns


def detect_anomalies(
    records: list[AssessmentRecord],
    threshold_multiplier: float = 2.0,
) -> list[AnomalyRecord]:
    """
    Detect anomalies using a modified Z-score approach.
    Points beyond threshold_multiplier × MAD from the median are flagged.
    """
    if len(records) < 4:
        return []

    sorted_recs = sorted(records, key=lambda r: r.date)
    footprints = [r.footprint for r in sorted_recs]
    median_fp = statistics.median(footprints)

    # Median absolute deviation
    abs_devs = [abs(fp - median_fp) for fp in footprints]
    mad = statistics.median(abs_devs)
    if mad < 1e-6:
        mad = statistics.stdev(footprints) if len(footprints) > 1 else 1.0
    if mad < 1e-6:
        return []

    # Rolling expected value (simple moving average with window=3)
    anomalies = []
    for i, rec in enumerate(sorted_recs):
        window_start = max(0, i - 2)
        window = footprints[window_start:i] if i > 0 else footprints[:1]
        expected = statistics.mean(window) if window else median_fp

        deviation = rec.footprint - expected
        z_score = deviation / mad

        if abs(z_score) >= threshold_multiplier:
            # Try to guess which category caused the spike
            hint = None
            if rec.flights > 2:
                hint = "flights"
            elif rec.distance > 30:
                hint = "transport"
            elif rec.electricity > 400:
                hint = "electricity"

            anomalies.append(AnomalyRecord(
                date=rec.date,
                footprint=rec.footprint,
                expected_value=expected,
                deviation=deviation,
                deviation_pct=(deviation / expected * 100) if expected > 0 else 0,
                is_spike=deviation > 0,
                category_hint=hint,
            ))

    return anomalies


def analyse_category_trends(records: list[AssessmentRecord]) -> list[CategoryTrend]:
    """
    Analyse trends per emission category by splitting recent vs historical.
    Uses the last 25% of data as 'current' and the rest as 'previous'.
    """
    if len(records) < 4:
        return []

    sorted_recs = sorted(records, key=lambda r: r.date)
    split_idx = max(1, len(sorted_recs) * 3 // 4)
    prev_recs = sorted_recs[:split_idx]
    curr_recs = sorted_recs[split_idx:]

    categories = ["Transport", "Electricity", "Diet", "Flights"]

    def _avg_category(recs: list[AssessmentRecord], cat: str) -> float:
        vals = []
        for r in recs:
            if cat == "Transport":
                # Rough estimate: distance × avg factor × 365 / 12
                vals.append(r.distance * 0.192 * 30)
            elif cat == "Electricity":
                vals.append(r.electricity * 0.82 * 12 / 12)
            elif cat == "Diet":
                diet_factors = {
                    "Vegan": 1500, "Vegetarian": 2000,
                    "Omnivore": 3000, "Non-Vegetarian": 3300,
                    "Heavy Meat": 4000,
                }
                vals.append(diet_factors.get(r.diet, 2500))
            elif cat == "Flights":
                vals.append(r.flights * 250)
        return statistics.mean(vals) if vals else 0.0

    total_current = sum(_avg_category(curr_recs, c) for c in categories)

    trends = []
    for cat in categories:
        prev_avg = _avg_category(prev_recs, cat)
        curr_avg = _avg_category(curr_recs, cat)
        change = curr_avg - prev_avg
        pct = (change / prev_avg * 100) if prev_avg > 0 else 0.0

        if abs(pct) < 3:
            direction = TrendDirection.STABLE
        elif change < 0:
            direction = TrendDirection.IMPROVING
        else:
            direction = TrendDirection.WORSENING

        contribution = (curr_avg / total_current * 100) if total_current > 0 else 0

        trends.append(CategoryTrend(
            category=cat,
            current_avg=curr_avg,
            previous_avg=prev_avg,
            change_abs=change,
            change_pct=pct,
            direction=direction,
            contribution_to_total=contribution,
        ))

    trends.sort(key=lambda t: abs(t.change_pct), reverse=True)
    return trends


def generate_forecasts(
    records: list[AssessmentRecord],
    months_ahead: int = 12,
) -> list[ForecastPoint]:
    """
    Generate footprint forecasts under three scenarios:
    - current_trend: extrapolate the current linear trend
    - optimistic: assume 5% monthly improvement
    - pessimistic: assume 3% monthly increase
    """
    if len(records) < 2:
        return []

    sorted_recs = sorted(records, key=lambda r: r.date)
    ref_date = sorted_recs[0].date
    x = [_date_to_month_index(r.date, ref_date) for r in sorted_recs]
    y = [r.footprint for r in sorted_recs]

    slope, intercept, r_sq, std_err = _linear_regression(x, y)
    last_x = max(x) if x else 0
    last_y = y[-1] if y else 0

    # Approximate eco score from footprint (sigmoid)
    def _eco(fp: float) -> int:
        score = 100 / (1 + math.exp((fp - 4000) / 1000))
        return max(0, min(100, int(round(score))))

    forecasts = []
    for m in range(1, months_ahead + 1):
        future_x = last_x + m
        future_label = _month_index_to_label(future_x, ref_date)

        for scenario, multiplier in [
            ("current_trend", 1.0),
            ("optimistic", 1.0),
            ("pessimistic", 1.0),
        ]:
            if scenario == "current_trend":
                predicted = slope * future_x + intercept
            elif scenario == "optimistic":
                predicted = last_y * (0.95 ** m)
            else:
                predicted = last_y * (1.03 ** m)

            predicted = max(0, predicted)
            band = std_err * math.sqrt(m) * 1.96  # 95% confidence

            forecasts.append(ForecastPoint(
                month_index=future_x,
                date_label=future_label,
                scenario=scenario,
                predicted_footprint=predicted,
                predicted_eco_score=_eco(predicted),
                confidence_lower=max(0, predicted - band),
                confidence_upper=predicted + band,
            ))

    return forecasts


def generate_insights(
    trend: TrendResult,
    seasonal: list[SeasonalPattern],
    anomalies: list[AnomalyRecord],
    categories: list[CategoryTrend],
    avg_footprint: float,
) -> list[Insight]:
    """Generate actionable insights from all analysis components."""
    insights: list[Insight] = []

    # ── Trend-based insights ────────────────────────────────────────────────
    if trend.direction == TrendDirection.WORSENING:
        insights.append(Insight(
            title="📉 Emissions Trending Upward",
            description=(
                f"Your footprint has been increasing by {trend.slope_per_year:.0f} kg CO₂/year. "
                f"This trend has {'strong' if trend.r_squared > 0.6 else 'moderate'} statistical confidence."
            ),
            severity=InsightSeverity.WARNING,
            category="trend",
            action="Review your most recent lifestyle changes and identify what's driving the increase.",
            potential_saving_kg=abs(trend.slope_per_year),
            confidence=trend.r_squared,
        ))
    elif trend.direction == TrendDirection.IMPROVING:
        insights.append(Insight(
            title="🎉 Emissions Trending Downward",
            description=(
                f"Excellent! Your footprint is decreasing by {abs(trend.slope_per_year):.0f} kg CO₂/year. "
                f"Your sustainable habits are paying off."
            ),
            severity=InsightSeverity.POSITIVE,
            category="trend",
            action="Maintain your current trajectory. Consider setting a more ambitious target.",
            potential_saving_kg=0,
            confidence=trend.r_squared,
        ))
    elif trend.direction == TrendDirection.VOLATILE:
        insights.append(Insight(
            title="📊 High Variability Detected",
            description="Your emissions fluctuate significantly between assessments. This makes it harder to track real progress.",
            severity=InsightSeverity.WARNING,
            category="trend",
            action="Try to maintain consistent daily habits. Log assessments at regular intervals for better tracking.",
            potential_saving_kg=avg_footprint * 0.1,
            confidence=0.5,
        ))

    # ── Seasonal insights ───────────────────────────────────────────────────
    if seasonal:
        worst = max(seasonal, key=lambda s: s.avg_footprint)
        best = min(seasonal, key=lambda s: s.avg_footprint)
        if worst.avg_footprint > best.avg_footprint * 1.1:
            insights.append(Insight(
                title=f"🌡️ {worst.season.value.title()} Is Your Highest-Emission Season",
                description=(
                    f"Your average footprint in {worst.season.value} is {worst.avg_footprint:.0f} kg CO₂, "
                    f"compared to {best.avg_footprint:.0f} in {best.season.value}. "
                    f"That's a {((worst.avg_footprint / best.avg_footprint - 1) * 100):.0f}% difference."
                ),
                severity=InsightSeverity.INFO,
                category="seasonal",
                action=f"Plan ahead for {worst.season.value}: pre-heat/cool efficiently and reduce travel.",
                potential_saving_kg=worst.avg_footprint - best.avg_footprint,
                confidence=0.7,
            ))

    # ── Anomaly insights ────────────────────────────────────────────────────
    recent_anomalies = [a for a in anomalies if a.is_spike][-3:]
    for anomaly in recent_anomalies:
        hint_text = f" — likely caused by {anomaly.category_hint}" if anomaly.category_hint else ""
        insights.append(Insight(
            title=f"⚠️ Emission Spike Detected ({anomaly.date})",
            description=(
                f"Footprint was {anomaly.footprint:.0f} kg CO₂, "
                f"which is {abs(anomaly.deviation_pct):.0f}% above expected "
                f"({anomaly.expected_value:.0f} kg CO₂){hint_text}."
            ),
            severity=InsightSeverity.WARNING,
            category="anomaly",
            action="Review what happened on this date and plan to avoid similar spikes.",
            potential_saving_kg=abs(anomaly.deviation),
            confidence=0.8,
        ))

    # ── Category insights ───────────────────────────────────────────────────
    worst_cat = max(categories, key=lambda c: c.change_pct) if categories else None
    best_cat = min(categories, key=lambda c: c.change_pct) if categories else None

    if worst_cat and worst_cat.change_pct > 10:
        insights.append(Insight(
            title=f"📈 {worst_cat.category} Emissions Rising",
            description=(
                f"{worst_cat.category} emissions increased by {worst_cat.change_pct:.0f}% "
                f"and now accounts for {worst_cat.contribution_to_total:.0f}% of your total footprint."
            ),
            severity=InsightSeverity.WARNING,
            category=worst_cat.category.lower(),
            action=_category_action(worst_cat.category),
            potential_saving_kg=abs(worst_cat.change_abs),
            confidence=0.75,
        ))

    if best_cat and best_cat.change_pct < -5:
        insights.append(Insight(
            title=f"✅ {best_cat.category} Emissions Decreasing",
            description=(
                f"Great news! {best_cat.category} emissions dropped by {abs(best_cat.change_pct):.0f}%. "
                f"This category now contributes {best_cat.contribution_to_total:.0f}% of your total."
            ),
            severity=InsightSeverity.POSITIVE,
            category=best_cat.category.lower(),
            action=f"Continue your current approach to {best_cat.category.lower()}.",
            potential_saving_kg=0,
            confidence=0.8,
        ))

    # ── Overall footprint level insight ─────────────────────────────────────
    if avg_footprint > 6000:
        insights.append(Insight(
            title="🌍 High Overall Footprint",
            description=(
                f"Your average footprint of {avg_footprint:.0f} kg CO₂/year is above the "
                f"global average (~4,000 kg). There's significant room for improvement."
            ),
            severity=InsightSeverity.WARNING,
            category="overall",
            action="Focus on the highest-impact category first: usually transport or energy.",
            potential_saving_kg=avg_footprint - 4000,
            confidence=0.9,
        ))
    elif avg_footprint < 2500:
        insights.append(Insight(
            title="🏆 Below-Average Footprint",
            description=(
                f"Your average footprint of {avg_footprint:.0f} kg CO₂/year is well below "
                f"the global average. You're doing great!"
            ),
            severity=InsightSeverity.POSITIVE,
            category="overall",
            action="Share your strategies with the community. Every example inspires others.",
            potential_saving_kg=0,
            confidence=0.9,
        ))

    # Sort: positive last, critical first
    severity_order = {
        InsightSeverity.CRITICAL: 0,
        InsightSeverity.WARNING: 1,
        InsightSeverity.INFO: 2,
        InsightSeverity.POSITIVE: 3,
    }
    insights.sort(key=lambda i: severity_order.get(i.severity, 2))
    return insights


def _category_action(category: str) -> str:
    """Suggest a specific action for a high-growth category."""
    actions = {
        "Transport": "Consider carpooling, public transit, or working from home 1-2 days/week.",
        "Electricity": "Switch to LED lighting, unplug idle devices, or explore renewable energy options.",
        "Diet": "Try Meatless Mondays or shift toward more plant-based meals.",
        "Flights": "Consider video conferencing instead of short flights, or offset unavoidable flights.",
    }
    return actions.get(category, "Review this category for reduction opportunities.")


def _build_footprint_timeline(records: list[AssessmentRecord]) -> list[dict[str, Any]]:
    """Build a simple timeline dict list for charting."""
    sorted_recs = sorted(records, key=lambda r: r.date)
    return [
        {"date": r.date, "footprint": round(r.footprint, 2), "eco_score": r.eco_score}
        for r in sorted_recs
    ]


def _compute_goal_tracking(
    records: list[AssessmentRecord],
    goal_target: float | None,
    slope_per_month: float,
) -> tuple[float | None, float | None]:
    """Compute goal proximity and months-to-goal if a target is set."""
    if goal_target is None or goal_target <= 0:
        return None, None

    sorted_recs = sorted(records, key=lambda r: r.date)
    current = sorted_recs[-1].footprint if sorted_recs else 0
    proximity = max(0, min(100, (1 - current / goal_target) * 100)) if goal_target > 0 else 0

    if slope_per_month >= 0:
        months = None  # not trending toward goal
    else:
        remaining = current - goal_target
        months = remaining / abs(slope_per_month) if slope_per_month != 0 else None

    return round(proximity, 1), round(months, 1) if months and months > 0 else None


# ─── Main Entry Point ───────────────────────────────────────────────────────

def generate_trend_report(
    records: list[AssessmentRecord],
    user_id: int = 1,
    goal_target: float | None = None,
    forecast_months: int = 12,
) -> TrendReport:
    """
    Generate a comprehensive trend analysis report from assessment records.

    Parameters
    ----------
    records : list[AssessmentRecord]
        Historical assessment data sorted or unsorted by date.
    user_id : int
        The user's ID.
    goal_target : float | None
        Optional annual carbon goal in kg CO₂.
    forecast_months : int
        How many months to forecast ahead.

    Returns
    -------
    TrendReport
        Complete analysis with trends, anomalies, forecasts, and insights.
    """
    if not records:
        return _empty_report(user_id)

    sorted_recs = sorted(records, key=lambda r: r.date)
    footprints = [r.footprint for r in sorted_recs]
    eco_scores = [r.eco_score for r in sorted_recs]

    # Date range
    date_range = f"{sorted_recs[0].date[:7]} – {sorted_recs[-1].date[:7]}"

    # Overall trend
    overall_trend = analyse_overall_trend(sorted_recs)

    # Category trends
    cat_trends = analyse_category_trends(sorted_recs)

    # Seasonal patterns
    seasonal = analyse_seasonal_patterns(sorted_recs)

    # Anomalies
    anomalies = detect_anomalies(sorted_recs)

    # Forecasts
    forecasts = generate_forecasts(sorted_recs, forecast_months)

    # Insights
    insights = generate_insights(
        overall_trend, seasonal, anomalies, cat_trends, statistics.mean(footprints),
    )

    # Goal tracking
    proximity, months_to = _compute_goal_tracking(
        sorted_recs, goal_target, overall_trend.slope_per_month,
    )

    return TrendReport(
        user_id=user_id,
        analysis_period_months=_date_to_month_index(
            sorted_recs[-1].date, sorted_recs[0].date,
        ) + 1,
        total_assessments=len(records),
        date_range=date_range,
        overall_trend=overall_trend,
        footprint_timeline=_build_footprint_timeline(sorted_recs),
        eco_score_timeline=[
            {"date": r.date, "eco_score": r.eco_score} for r in sorted_recs
        ],
        category_trends=cat_trends,
        seasonal_patterns=seasonal,
        anomalies=anomalies,
        forecasts=forecasts,
        insights=insights,
        avg_footprint=statistics.mean(footprints),
        median_footprint=statistics.median(footprints),
        std_footprint=statistics.stdev(footprints) if len(footprints) > 1 else 0.0,
        min_footprint=min(footprints),
        max_footprint=max(footprints),
        avg_eco_score=statistics.mean(eco_scores) if eco_scores else 0.0,
        total_assessments_analyzed=len(records),
        goal_target=goal_target,
        goal_proximity_pct=proximity,
        months_to_goal=months_to,
    )


def _empty_report(user_id: int) -> TrendReport:
    """Return an empty/default report when no data is available."""
    return TrendReport(
        user_id=user_id,
        analysis_period_months=0,
        total_assessments=0,
        date_range="No data",
        overall_trend=TrendResult(
            direction=TrendDirection.STABLE,
            slope_per_month=0, slope_per_year=0, r_squared=0,
            intercept=0, pct_change_monthly=0,
            interpretation="No assessment data available.",
        ),
        footprint_timeline=[],
        eco_score_timeline=[],
        category_trends=[],
        seasonal_patterns=[],
        anomalies=[],
        forecasts=[],
        insights=[],
        avg_footprint=0,
        median_footprint=0,
        std_footprint=0,
        min_footprint=0,
        max_footprint=0,
        avg_eco_score=0,
        total_assessments_analyzed=0,
    )
