"""
Carbon Offset Portfolio Tracker

A complete module for tracking carbon offset investments, analyzing portfolio
performance, assessing offset project lifecycle, and providing actionable
insights for maximizing climate impact through strategic offset purchasing.
"""

from src.portfolio.models import (
    OffsetProject,
    PortfolioHolding,
    OffsetTransaction,
    PortfolioSnapshot,
    RiskAssessment,
    LifecycleStage,
    ProjectType,
)
from src.portfolio.analytics import (
    PortfolioAnalyzer,
    calculate_diversification_score,
    calculate_portfolio_value,
    calculate_weighted_risk,
    optimize_offset_allocation,
)
from src.portfolio.lifecycle import (
    LifecycleAnalyzer,
    estimate_project_lifespan,
    calculate_permanence_score,
    compute_coeffectiveness_ratio,
)

__all__ = [
    "OffsetProject",
    "PortfolioHolding",
    "OffsetTransaction",
    "PortfolioSnapshot",
    "RiskAssessment",
    "LifecycleStage",
    "ProjectType",
    "PortfolioAnalyzer",
    "LifecycleAnalyzer",
    "calculate_diversification_score",
    "calculate_portfolio_value",
    "calculate_weighted_risk",
    "optimize_offset_allocation",
    "estimate_project_lifespan",
    "calculate_permanence_score",
    "compute_coeffectiveness_ratio",
]
