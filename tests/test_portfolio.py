"""
Tests for Carbon Offset Portfolio Tracker

Covers models, database operations, analytics, and lifecycle analysis.
"""

import os
import sys
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.portfolio.models import (
    OffsetProject,
    PortfolioHolding,
    OffsetTransaction,
    PortfolioSnapshot,
    RiskAssessment,
    LifecycleStage,
    ProjectType,
    TransactionType,
    RiskLevel,
)
from src.portfolio.analytics import (
    PortfolioAnalyzer,
    calculate_diversification_score,
    calculate_portfolio_value,
    calculate_current_value,
    calculate_total_carbon_kg,
    calculate_weighted_risk,
    optimize_offset_allocation,
    compare_snapshots,
    _shannon_entropy,
)
from src.portfolio.lifecycle import (
    LifecycleAnalyzer,
    estimate_project_lifespan,
    calculate_permanence_score,
    compute_coeffectiveness_ratio,
    calculate_vintage_adjustment,
    estimate_geopolitical_risk,
    compute_retirement_impact,
    generate_lifecycle_report,
)
from src.portfolio.db import PortfolioDB


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
    """Create a temporary in-memory database for testing."""
    database = PortfolioDB(":memory:")
    return database


@pytest.fixture
def sample_project():
    """A sample reforestation project."""
    return OffsetProject(
        project_id="test-proj-1",
        name="Test Reforestation",
        description="A test reforestation project",
        project_type=ProjectType.REFORESTATION,
        registry="Verra",
        registry_id="VCS-9999",
        country="Brazil",
        region="Amazonas",
        methodology="VM0015",
        standard="VCS",
        vintage_year=2024,
        unit_price_usd=15.00,
        total_units=10000,
        available_units=8000,
        co_benefits=["Biodiversity", "Community support"],
        sdg_alignment=[13, 15],
        lifecycle_stage=LifecycleStage.ACTIVE,
    )


@pytest.fixture
def sample_holding(sample_project):
    """A sample portfolio holding."""
    return PortfolioHolding(
        holding_id="test-hold-1",
        user_id=1,
        project_id=sample_project.project_id,
        project_name=sample_project.name,
        project_type=sample_project.project_type,
        units_held=100,
        units_retired=10,
        avg_cost_per_unit=15.00,
        total_invested_usd=1500.00,
        purchase_date=datetime(2025, 1, 15),
        last_valuation=18.00,
        last_valuation_date=datetime(2026, 8, 1),
        vintage_year=2024,
        registry="Verra",
    )


@pytest.fixture
def sample_transactions():
    """A sample list of transactions."""
    return [
        OffsetTransaction(
            transaction_id="tx-1",
            user_id=1,
            project_id="test-proj-1",
            project_name="Test Reforestation",
            transaction_type=TransactionType.PURCHASE,
            units=50,
            price_per_unit=15.00,
            total_cost_usd=750.00,
            fee_usd=15.00,
            timestamp=datetime(2025, 6, 1),
            status="completed",
        ),
        OffsetTransaction(
            transaction_id="tx-2",
            user_id=1,
            project_id="test-proj-2",
            project_name="Solar Micro-Grid",
            transaction_type=TransactionType.PURCHASE,
            units=30,
            price_per_unit=12.00,
            total_cost_usd=360.00,
            fee_usd=7.20,
            timestamp=datetime(2025, 7, 15),
            status="completed",
        ),
        OffsetTransaction(
            transaction_id="tx-3",
            user_id=1,
            project_id="test-proj-1",
            project_name="Test Reforestation",
            transaction_type=TransactionType.RETIREMENT,
            units=10,
            price_per_unit=0.0,
            total_cost_usd=0.0,
            timestamp=datetime(2025, 8, 1),
            status="completed",
        ),
    ]


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class TestModels:
    def test_offset_project_to_dict(self, sample_project):
        d = sample_project.to_dict()
        assert d["project_id"] == "test-proj-1"
        assert d["project_type"] == "reforestation"
        assert d["lifecycle_stage"] == "active"
        assert isinstance(d["co_benefits"], list)
        assert len(d["co_benefits"]) == 2

    def test_offset_project_from_dict(self, sample_project):
        d = sample_project.to_dict()
        restored = OffsetProject.from_dict(d)
        assert restored.project_id == sample_project.project_id
        assert restored.project_type == ProjectType.REFORESTATION
        assert restored.unit_price_usd == 15.00

    def test_holding_properties(self, sample_holding):
        assert sample_holding.units_available == 90
        assert sample_holding.cost_basis == 1500.00
        assert sample_holding.unrealized_gain_usd == (18.00 - 15.00) * 90

    def test_holding_from_dict(self, sample_holding):
        d = sample_holding.to_dict()
        restored = PortfolioHolding.from_dict(d)
        assert restored.holding_id == sample_holding.holding_id
        assert restored.units_held == 100

    def test_transaction_total_with_fee(self):
        tx = OffsetTransaction(total_cost_usd=100.0, fee_usd=5.0)
        assert tx.total_with_fee == 105.0

    def test_transaction_from_dict(self, sample_transactions):
        d = sample_transactions[0].to_dict()
        restored = OffsetTransaction.from_dict(d)
        assert restored.transaction_type == TransactionType.PURCHASE
        assert restored.units == 50

    def test_snapshot_roi_percent(self):
        snap = PortfolioSnapshot(
            total_invested_usd=1000.0,
            current_value_usd=1200.0,
            total_carbon_offset_kg=10000.0,
        )
        assert snap.roi_percent == 20.0

    def test_snapshot_effective_cost_per_tonne(self):
        snap = PortfolioSnapshot(
            total_invested_usd=500.0,
            total_carbon_offset_kg=5000.0,
        )
        assert snap.effective_cost_per_tonne == 100.0

    def test_risk_assessment_from_dict(self):
        r = RiskAssessment(
            entity_id="p1",
            overall_risk=RiskLevel.HIGH,
            risk_factors=["Factor 1"],
        )
        d = r.to_dict()
        assert d["overall_risk"] == "high"
        restored = RiskAssessment.from_dict(d)
        assert restored.risk_factors == ["Factor 1"]


# ---------------------------------------------------------------------------
# Analytics tests
# ---------------------------------------------------------------------------

class TestAnalytics:
    def test_calculate_portfolio_value(self, sample_holding):
        value = calculate_portfolio_value([sample_holding])
        assert value == 1500.00

    def test_calculate_current_value(self, sample_holding):
        value = calculate_current_value([sample_holding])
        assert value == 18.00 * 90

    def test_calculate_total_carbon_kg(self, sample_holding):
        kg = calculate_total_carbon_kg([sample_holding])
        assert kg == 90 * 1000.0

    def test_shannon_entropy(self):
        from collections import Counter
        # Uniform distribution should have max entropy
        uniform = Counter({"a": 10, "b": 10, "c": 10})
        skewed = Counter({"a": 30, "b": 1, "c": 1})
        assert _shannon_entropy(uniform) > _shannon_entropy(skewed)

    def test_diversification_score_empty(self):
        assert calculate_diversification_score([]) == 0.0

    def test_diversification_score_single_holding(self, sample_holding):
        score = calculate_diversification_score([sample_holding])
        assert 0 <= score <= 100

    def test_diversification_score_multiple(self):
        holdings = [
            PortfolioHolding(
                project_id=f"p{i}",
                project_name=f"Project {i}",
                project_type=list(ProjectType)[i % len(ProjectType)],
                units_held=50,
                avg_cost_per_unit=10.0,
                total_invested_usd=500.0,
                registry=["Verra", "Gold Standard", "ACR"][i % 3],
                vintage_year=2022 + (i % 3),
                user_id=1,
            )
            for i in range(6)
        ]
        score = calculate_diversification_score(holdings)
        assert score > 50  # Well-diversified should score high

    def test_weighted_risk_no_assessments(self, sample_holding):
        risk = calculate_weighted_risk([sample_holding], {})
        assert risk == 50.0  # Default medium risk

    def test_weighted_risk_with_assessments(self, sample_holding):
        assessment = RiskAssessment(
            entity_id=sample_holding.project_id,
            overall_risk_score=25.0,
        )
        risk = calculate_weighted_risk([sample_holding], {sample_holding.project_id: assessment})
        assert risk == 25.0

    def test_optimize_offset_allocation_empty(self):
        result = optimize_offset_allocation(1000, 500, [])
        assert result == []

    def test_optimize_offset_allocation(self, sample_project):
        projects = [sample_project]
        alloc = optimize_offset_allocation(
            target_co2_kg=5000.0,
            budget_usd=1000.0,
            available_projects=projects,
            risk_tolerance="medium",
        )
        assert len(alloc) > 0
        assert alloc[0]["units"] > 0
        assert alloc[0]["cost_usd"] > 0

    def test_compare_snapshots(self):
        s1 = PortfolioSnapshot(
            timestamp=datetime(2025, 1, 1),
            total_invested_usd=1000.0,
            current_value_usd=1000.0,
        )
        s2 = PortfolioSnapshot(
            timestamp=datetime(2025, 2, 1),
            total_invested_usd=1500.0,
            current_value_usd=1600.0,
        )
        trends = compare_snapshots([s1, s2])
        assert len(trends) == 1
        assert len(trends[0]["metrics"]) > 0


# ---------------------------------------------------------------------------
# Lifecycle tests
# ---------------------------------------------------------------------------

class TestLifecycle:
    def test_estimate_project_lifespan(self):
        assert estimate_project_lifespan("reforestation") == 30
        assert estimate_project_lifespan("renewable_energy") == 20
        assert estimate_project_lifespan("unknown") == 15

    def test_permanence_score(self, sample_project):
        score = calculate_permanence_score(sample_project)
        assert 0 <= score <= 100

    def test_coeffectiveness_ratio(self, sample_project):
        ratio = compute_coeffectiveness_ratio(sample_project)
        assert 0 <= ratio <= 1.0

    def test_coeffectiveness_no_benefits(self):
        project = OffsetProject(co_benefits=[], sdg_alignment=[], standard="")
        ratio = compute_coeffectiveness_ratio(project)
        assert ratio < 0.2

    def test_vintage_adjustment_recent(self):
        current = datetime.utcnow().year
        adj = calculate_vintage_adjustment(current)
        assert adj == 1.0

    def test_vintage_adjustment_old(self):
        adj = calculate_vintage_adjustment(2015)
        assert adj < 0.5

    def test_geopolitical_risk_low(self):
        assert estimate_geopolitical_risk("Canada") == 20.0

    def test_geopolitical_risk_high(self):
        assert estimate_geopolitical_risk("Somalia") == 65.0

    def test_geopolitical_risk_unknown(self):
        assert estimate_geopolitical_risk("") == 55.0

    def test_lifecycle_analyzer_analyze_project(self, sample_project):
        analyzer = LifecycleAnalyzer()
        result = analyzer.analyze_project(sample_project)
        assert "lifecycle_score" in result
        assert "permanence_score" in result
        assert "risk_assessment" in result
        assert "recommendations" in result
        assert 0 <= result["lifecycle_score"] <= 100

    def test_lifecycle_analyzer_portfolio(self, sample_holding, sample_project):
        analyzer = LifecycleAnalyzer()
        result = analyzer.analyze_portfolio_lifecycle(
            [sample_holding], {sample_holding.project_id: sample_project}
        )
        assert "overall_score" in result
        assert "health_grade" in result
        assert result["total_units"] == 90

    def test_lifecycle_analyzer_empty_portfolio(self):
        analyzer = LifecycleAnalyzer()
        result = analyzer.analyze_portfolio_lifecycle([], {})
        assert result["overall_score"] == 0.0
        assert result["health_grade"] == "N/A"

    def test_generate_lifecycle_report(self, sample_project):
        report = generate_lifecycle_report([sample_project])
        assert report["total_projects"] == 1
        assert "projects" in report

    def test_compute_retirement_impact(self):
        holding = PortfolioHolding(
            user_id=1, units_held=100, units_retired=50,
            avg_cost_per_unit=10.0, total_invested_usd=1000.0,
        )
        impact = compute_retirement_impact([holding])
        assert impact["total_retired_tonnes"] == 50.0
        assert impact["trees_saved_equivalent"] > 0


# ---------------------------------------------------------------------------
# Database tests
# ---------------------------------------------------------------------------

class TestDatabase:
    def test_upsert_and_get_project(self, db, sample_project):
        assert db.upsert_project(sample_project) is True
        fetched = db.get_project(sample_project.project_id)
        assert fetched is not None
        assert fetched.name == "Test Reforestation"

    def test_list_projects(self, db, sample_project):
        db.upsert_project(sample_project)
        projects = db.list_projects()
        assert len(projects) == 1

    def test_list_projects_by_type(self, db, sample_project):
        db.upsert_project(sample_project)
        projects = db.list_projects(project_type="reforestation")
        assert len(projects) == 1
        projects = db.list_projects(project_type="renewable_energy")
        assert len(projects) == 0

    def test_add_and_get_holding(self, db, sample_holding):
        assert db.add_holding(sample_holding) is True
        holdings = db.get_user_holdings(1)
        assert len(holdings) == 1
        assert holdings[0].project_name == "Test Reforestation"

    def test_update_holding_retirement(self, db, sample_holding):
        db.add_holding(sample_holding)
        assert db.update_holding_retirement(sample_holding.holding_id, 20) is True
        holdings = db.get_user_holdings(1)
        assert holdings[0].units_retired == 20

    def test_add_and_get_transactions(self, db, sample_transactions):
        for tx in sample_transactions:
            assert db.add_transaction(tx) is True
        txns = db.get_user_transactions(1)
        assert len(txns) == 3

    def test_get_total_invested(self, db, sample_transactions):
        for tx in sample_transactions:
            db.add_transaction(tx)
        total = db.get_total_invested(1)
        assert total == 750.00 + 360.00  # Only purchases

    def test_save_and_get_snapshot(self, db):
        snap = PortfolioSnapshot(
            user_id=1,
            total_units_held=100,
            current_value_usd=1500.0,
            total_invested_usd=1200.0,
        )
        assert db.save_snapshot(snap) is True
        history = db.get_snapshot_history(1)
        assert len(history) == 1

    def test_save_and_get_risk_assessment(self, db):
        risk = RiskAssessment(
            entity_id="test-proj-1",
            overall_risk=RiskLevel.LOW,
            overall_risk_score=20.0,
        )
        assert db.save_risk_assessment(risk) is True
        assessments = db.get_risk_assessments("test-proj-1")
        assert len(assessments) == 1
        assert assessments[0].overall_risk == RiskLevel.LOW
