"""
Lifecycle Analysis Module

Evaluates the full lifecycle of carbon offset projects — from planning
through verification, serialization, and completion. Computes permanence
scores, co-effectiveness ratios, and lifecycle health indicators.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from src.portfolio.models import (
    LifecycleStage,
    OffsetProject,
    PortfolioHolding,
    RiskAssessment,
    RiskLevel,
)

logger = logging.getLogger(__name__)


# ── Constants ─────────────────────────────────────────────────────────────

# Average project lifespans by type (years)
PROJECT_TYPE_LIFESPANS: Dict[str, int] = {
    "reforestation": 30,
    "afforestation": 25,
    "renewable_energy": 20,
    "methane_capture": 15,
    "clean_cookstoves": 5,
    "direct_air_capture": 25,
    "ocean_restoration": 20,
    "soil_carbon": 15,
    "industrial_efficiency": 10,
    "other": 15,
}

# Permanence risk factors by type (lower = more permanent)
PERMANENCE_RISK_BASE: Dict[str, float] = {
    "reforestation": 45,
    "afforestation": 50,
    "renewable_energy": 20,
    "methane_capture": 30,
    "clean_cookstoves": 35,
    "direct_air_capture": 15,
    "ocean_restoration": 40,
    "soil_carbon": 55,
    "industrial_efficiency": 25,
    "other": 40,
}

# Registry trust scores (lower = more trustworthy)
REGISTRY_TRUST: Dict[str, float] = {
    "Verra": 25,
    "Gold Standard": 20,
    "ACR": 30,
    "CAR": 35,
    "Plan Vivo": 30,
    "CDM": 40,
    "REDD+": 45,
    "": 60,
}

# Lifecycle stage progression weights (higher = more advanced)
STAGE_PROGRESSION: Dict[str, float] = {
    "planning": 0.1,
    "validation": 0.2,
    "registration": 0.35,
    "verification": 0.5,
    "active": 0.8,
    "serialization": 0.9,
    "on_hold": 0.4,
    "completed": 1.0,
    "expired": 0.0,
    "revoked": 0.0,
}


# ── Pure helper functions ─────────────────────────────────────────────────


def estimate_project_lifespan(project_type: str) -> int:
    """Return the expected lifespan in years for a given project type."""
    return PROJECT_TYPE_LIFESPANS.get(project_type, 15)


def calculate_permanence_score(project: OffsetProject) -> float:
    """
    Score 0-100 measuring the permanence (durability) of carbon storage.
    Based on project type, methodology, and registry standards.
    """
    base = PERMANENCE_RISK_BASE.get(project.project_type.value, 40)

    # Adjust for methodology keyword hints
    method_lower = project.methodology.lower() if project.methodology else ""
    method_bonus = 0
    if "permanence" in method_lower:
        method_bonus = -10
    if "monitoring" in method_lower:
        method_bonus -= 5
    if "leakage" in method_lower:
        method_bonus += 5

    # Adjust for registry trust
    registry_score = REGISTRY_TRUST.get(project.registry, 50)

    # Weighted average (lower risk = higher permanence score)
    risk_score = (base * 0.5 + registry_score * 0.3 + method_bonus * 0.2)
    permanence = max(0.0, min(100.0, 100.0 - risk_score))

    return round(permanence, 1)


def compute_coeffectiveness_ratio(project: OffsetProject) -> float:
    """
    Compute a co-effectiveness ratio measuring the project's value beyond
    carbon sequestration (co-benefits, SDG alignment, community impact).
    Returns 0-1 where higher is better.
    """
    co_benefit_score = min(len(project.co_benefits) / 5.0, 1.0) * 0.4
    sdg_score = min(len(project.sdg_alignment) / 7.0, 1.0) * 0.35

    # Standard/certification bonus
    cert_bonus = 0.0
    if project.standard in ("VCS", "CDM", "Gold Standard"):
        cert_bonus = 0.15
    elif project.standard:
        cert_bonus = 0.05

    # Lifecycle stage bonus
    stage_bonus = STAGE_PROGRESSION.get(project.lifecycle_stage.value, 0.3) * 0.1

    ratio = co_benefit_score + sdg_score + cert_bonus + stage_bonus
    return round(min(1.0, ratio), 3)


def calculate_vintage_adjustment(vintage_year: int, current_year: Optional[int] = None) -> float:
    """
    Calculate a vintage quality multiplier (0-1).
    Recent vintages score higher; older credits are discounted.
    """
    if vintage_year <= 0:
        return 0.5

    if current_year is None:
        current_year = datetime.utcnow().year

    age = current_year - vintage_year

    if age <= 0:
        return 1.0
    elif age == 1:
        return 0.95
    elif age == 2:
        return 0.85
    elif age <= 3:
        return 0.75
    elif age <= 5:
        return 0.60
    elif age <= 7:
        return 0.45
    else:
        return max(0.20, 0.45 - (age - 7) * 0.05)


def estimate_geopolitical_risk(country: str) -> float:
    """
    Rough geopolitical risk score (0-100) for a project's host country.
    Higher = more risky.
    """
    # Simplified risk tiers
    low_risk = {
        "United States", "Canada", "United Kingdom", "Germany", "France",
        "Australia", "Japan", "South Korea", "Netherlands", "Sweden",
        "Norway", "Denmark", "Switzerland", "New Zealand",
    }
    medium_risk = {
        "Brazil", "Mexico", "Colombia", "Chile", "Argentina", "Peru",
        "India", "China", "Indonesia", "Thailand", "Vietnam",
        "South Africa", "Kenya", "Morocco", "Turkey", "Poland",
        "Spain", "Italy", "Portugal",
    }
    # Everything else is higher risk

    if country in low_risk:
        return 20.0
    elif country in medium_risk:
        return 45.0
    elif not country:
        return 55.0
    else:
        return 65.0


# ── Lifecycle Analyzer class ─────────────────────────────────────────────


class LifecycleAnalyzer:
    """
    Comprehensive lifecycle analysis engine for offset projects.
    Combines permanence scoring, co-effectiveness, vintage quality,
    geopolitical assessment, and lifecycle health metrics.
    """

    def __init__(self):
        self.current_year = datetime.utcnow().year

    def analyze_project(self, project: OffsetProject) -> Dict[str, Any]:
        """Produce a full lifecycle analysis for a single project."""
        permanence = calculate_permanence_score(project)
        coeffectiveness = compute_coeffectiveness_ratio(project)
        vintage_adj = calculate_vintage_adjustment(
            project.vintage_year, self.current_year
        )
        geo_risk = estimate_geopolitical_risk(project.country)
        stage_health = self._stage_health(project.lifecycle_stage)

        # Overall lifecycle score
        lifecycle_score = (
            permanence * 0.30
            + stage_health * 0.25
            + (100 - geo_risk) * 0.15
            + vintage_adj * 100 * 0.15
            + coeffectiveness * 100 * 0.15
        )

        # Risk assessment
        risk = self._build_risk_assessment(project, permanence, geo_risk, vintage_adj)

        # Recommendations
        recommendations = self._generate_project_recommendations(
            project, permanence, vintage_adj, geo_risk
        )

        return {
            "project_id": project.project_id,
            "project_name": project.name,
            "project_type": project.project_type.value,
            "lifecycle_stage": project.lifecycle_stage.value,
            "lifecycle_score": round(lifecycle_score, 1),
            "permanence_score": permanence,
            "permanence_risk": round(100 - permanence, 1),
            "coeffectiveness_ratio": coeffectiveness,
            "vintage_adjustment": vintage_adj,
            "vintage_age_years": (
                self.current_year - project.vintage_year if project.vintage_year > 0 else None
            ),
            "geopolitical_risk": geo_risk,
            "stage_health": stage_health,
            "estimated_lifespan_years": estimate_project_lifespan(project.project_type.value),
            "risk_assessment": risk,
            "recommendations": recommendations,
        }

    def analyze_portfolio_lifecycle(
        self, holdings: List[PortfolioHolding], projects: Dict[str, OffsetProject]
    ) -> Dict[str, Any]:
        """
        Analyze the lifecycle health of an entire portfolio.
        Requires a dict mapping project_id -> OffsetProject for each holding.
        """
        if not holdings:
            return {
                "overall_score": 0.0,
                "total_units": 0,
                "avg_permanence": 0.0,
                "avg_vintage_age": 0.0,
                "stage_distribution": {},
                "health_grade": "N/A",
                "project_analyses": [],
            }

        analyses = []
        permanence_scores = []
        vintage_ages = []
        stage_counts: Dict[str, int] = {}

        total_units = 0

        for holding in holdings:
            project = projects.get(holding.project_id)
            if not project:
                continue

            analysis = self.analyze_project(project)
            analyses.append(analysis)
            permanence_scores.append(analysis["permanence_score"])

            if analysis["vintage_age_years"] is not None:
                vintage_ages.append(analysis["vintage_age_years"])

            stage = project.lifecycle_stage.value
            stage_counts[stage] = stage_counts.get(stage, 0) + holding.units_available
            total_units += holding.units_available

        avg_permanence = (
            round(sum(permanence_scores) / len(permanence_scores), 1)
            if permanence_scores
            else 0.0
        )
        avg_vintage_age = (
            round(sum(vintage_ages) / len(vintage_ages), 1)
            if vintage_ages
            else 0.0
        )

        # Overall portfolio lifecycle score
        if analyses:
            scores = [a["lifecycle_score"] for a in analyses]
            # Weight by units held
            weighted_sum = 0.0
            weight_total = 0.0
            for a, h in zip(analyses, holdings):
                if h.project_id in projects:
                    w = h.units_available
                    weighted_sum += a["lifecycle_score"] * w
                    weight_total += w
            overall = round(weighted_sum / weight_total, 1) if weight_total > 0 else 0.0
        else:
            overall = 0.0

        grade = self._score_to_grade(overall)

        return {
            "overall_score": overall,
            "health_grade": grade,
            "total_units": total_units,
            "avg_permanence": avg_permanence,
            "avg_vintage_age": avg_vintage_age,
            "stage_distribution": stage_counts,
            "project_analyses": analyses,
        }

    def _stage_health(self, stage: LifecycleStage) -> float:
        """Map lifecycle stage to a 0-100 health score."""
        mapping = {
            LifecycleStage.PLANNING: 20.0,
            LifecycleStage.VALIDATION: 35.0,
            LifecycleStage.REGISTRATION: 50.0,
            LifecycleStage.VERIFICATION: 65.0,
            LifecycleStage.ACTIVE: 85.0,
            LifecycleStage.SERIALIZATION: 90.0,
            LifecycleStage.ON_HOLD: 40.0,
            LifecycleStage.COMPLETED: 100.0,
            LifecycleStage.EXPIRED: 10.0,
            LifecycleStage.REVOKED: 0.0,
        }
        return mapping.get(stage, 50.0)

    def _build_risk_assessment(
        self,
        project: OffsetProject,
        permanence: float,
        geo_risk: float,
        vintage_adj: float,
    ) -> RiskAssessment:
        """Build a RiskAssessment from lifecycle analysis data."""
        permanence_risk = round(100 - permanence, 1)
        vintage_risk = round((1 - vintage_adj) * 100, 1)
        registry_risk = REGISTRY_TRUST.get(project.registry, 50)

        # Additionality heuristic: nature-based projects are harder to prove
        additionality_risk = 50.0
        if project.project_type.value in ("reforestation", "afforestation", "soil_carbon"):
            additionality_risk = 60.0
        elif project.project_type.value in ("direct_air_capture", "industrial_efficiency"):
            additionality_risk = 35.0

        # Leakage risk
        leakage_risk = 50.0
        if project.project_type.value in ("reforestation", "afforestation"):
            leakage_risk = 55.0
        elif project.project_type.value in ("direct_air_capture", "renewable_energy"):
            leakage_risk = 20.0

        market_risk = 40.0  # Baseline market risk

        # Overall weighted score
        overall_score = (
            permanence_risk * 0.25
            + additionality_risk * 0.20
            + leakage_risk * 0.15
            + registry_risk * 0.15
            + vintage_risk * 0.10
            + geo_risk * 0.10
            + market_risk * 0.05
        )

        # Map score to level
        if overall_score < 30:
            risk_level = RiskLevel.LOW
        elif overall_score < 50:
            risk_level = RiskLevel.MEDIUM
        elif overall_score < 70:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL

        # Identify risk factors
        risk_factors: List[str] = []
        if permanence_risk > 50:
            risk_factors.append("High permanence risk for project type")
        if additionality_risk > 55:
            risk_factors.append("Additionality may be difficult to demonstrate")
        if leakage_risk > 50:
            risk_factors.append("Non-negligible leakage risk")
        if registry_risk > 40:
            risk_factors.append("Registry has limited recognition")
        if vintage_risk > 50:
            risk_factors.append("Credit vintage is aging")
        if geo_risk > 55:
            risk_factors.append("Host country has elevated geopolitical risk")

        # Mitigations
        mitigations: List[str] = []
        if permanence_risk > 50:
            mitigations.append("Look for projects with buffer pool allocations")
        if leakage_risk > 40:
            mitigations.append("Verify project has leakage reduction methodology")
        if registry_risk > 40:
            mitigations.append("Prefer Verra or Gold Standard certified projects")
        if vintage_risk > 40:
            mitigations.append("Prioritize recent vintages (1-2 years old)")

        return RiskAssessment(
            entity_id=project.project_id,
            entity_type="project",
            overall_risk=risk_level,
            overall_risk_score=round(overall_score, 1),
            permanence_risk=permanence_risk,
            additionality_risk=additionality_risk,
            leakage_risk=leakage_risk,
            registry_risk=registry_risk,
            vintage_risk=vintage_risk,
            geopolitical_risk=geo_risk,
            market_risk=market_risk,
            risk_factors=risk_factors,
            mitigations=mitigations,
        )

    def _generate_project_recommendations(
        self,
        project: OffsetProject,
        permanence: float,
        vintage_adj: float,
        geo_risk: float,
    ) -> List[str]:
        """Generate actionable recommendations for a project."""
        recs: List[str] = []

        if permanence < 50:
            recs.append(
                f"Consider offsetting this project's permanence risk by pairing with "
                f"a direct air capture or renewable energy offset."
            )
        if vintage_adj < 0.6:
            recs.append(
                "This project's vintage is aging. Prioritize newer credits for "
                "better market credibility."
            )
        if geo_risk > 55:
            recs.append(
                "The host country presents elevated risk. Diversify with projects "
                "in more stable regions."
            )
        if not project.co_benefits:
            recs.append(
                "This project lacks documented co-benefits. Projects with community "
                "or biodiversity co-benefits often deliver stronger impact."
            )
        if len(project.co_benefits) >= 3:
            recs.append(
                f"Strong co-benefit portfolio ({len(project.co_benefits)} benefits). "
                "Highlight these for impact reporting."
            )
        if project.lifecycle_stage in (LifecycleStage.EXPIRED, LifecycleStage.REVOKED):
            recs.append(
                "⚠️ This project is expired/revoked. Do not purchase additional credits."
            )
        if not recs:
            recs.append("Project lifecycle indicators look healthy. Continue monitoring.")

        return recs

    @staticmethod
    def _score_to_grade(score: float) -> str:
        """Convert a 0-100 lifecycle score to a letter grade."""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B+"
        elif score >= 60:
            return "B"
        elif score >= 50:
            return "C+"
        elif score >= 40:
            return "C"
        elif score >= 30:
            return "D"
        else:
            return "F"


# ── Standalone reporting helpers ──────────────────────────────────────────


def generate_lifecycle_report(
    projects: List[OffsetProject],
) -> Dict[str, Any]:
    """
    Generate a summary lifecycle report for a list of projects.
    Useful for portfolio-level reporting without holdings context.
    """
    analyzer = LifecycleAnalyzer()

    project_reports = []
    for project in projects:
        analysis = analyzer.analyze_project(project)
        project_reports.append(analysis)

    if not project_reports:
        return {"total_projects": 0, "projects": [], "summary": {}}

    avg_score = sum(r["lifecycle_score"] for r in project_reports) / len(project_reports)
    avg_permanence = sum(r["permanence_score"] for r in project_reports) / len(project_reports)

    stage_summary: Dict[str, int] = {}
    for r in project_reports:
        stage = r["lifecycle_stage"]
        stage_summary[stage] = stage_summary.get(stage, 0) + 1

    return {
        "total_projects": len(project_reports),
        "average_lifecycle_score": round(avg_score, 1),
        "average_permanence_score": round(avg_permanence, 1),
        "stage_summary": stage_summary,
        "projects": project_reports,
    }


def compute_retirement_impact(
    holdings: List[PortfolioHolding],
) -> Dict[str, Any]:
    """
    Calculate the real-world impact of retired offsets.
    Translates retired units into tangible equivalents.
    """
    total_retired_kg = sum(h.units_retired * 1000 for h in holdings)

    return {
        "total_retired_kg": total_retired_kg,
        "total_retired_tonnes": round(total_retired_kg / 1000, 2),
        "trees_saved_equivalent": round(total_retired_kg / 22.0, 0),
        "cars_off_road_days": round(total_retired_kg / 12.6, 0),
        "homes_powered_days": round(total_retired_kg / 24.0, 0),
        "smartphones_charged": round(total_retired_kg / 0.008, 0),
        "internet_hours": round(total_retired_kg / 0.006, 0),
    }
