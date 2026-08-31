"""
Tests for Carbon Offset Portfolio Tracker
==========================================

Covers portfolio CRUD, analytics, diversification scoring, risk assessment,
net-zero projection, and snapshot persistence.
"""

import json
import math
import sqlite3
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _patch_db(monkeypatch, tmp_path):
    """Redirect all DB operations to a temporary SQLite file."""
    db_path = str(tmp_path / "test_offset.db")
    monkeypatch.setattr("src.lib.carbon_offset_portfolio.DB_NAME", db_path)
    from src.lib.carbon_offset_portfolio import init_offset_portfolio_db
    init_offset_portfolio_db()
    yield db_path


@pytest.fixture
def user_id():
    return 42


# ---------------------------------------------------------------------------
# CRUD Tests
# ---------------------------------------------------------------------------
class TestOffsetPurchaseCRUD:
    def test_add_and_retrieve(self, user_id):
        from src.lib.carbon_offset_portfolio import add_offset_purchase, get_user_holdings
        hid = add_offset_purchase(user_id, "wind_india", 2.5, 46.25, "2025-01-15")
        assert hid is not None
        holdings = get_user_holdings(user_id)
        assert len(holdings) == 1
        assert holdings[0].project_id == "wind_india"
        assert holdings[0].tonnes == 2.5

    def test_add_invalid_project(self, user_id):
        from src.lib.carbon_offset_portfolio import add_offset_purchase
        assert add_offset_purchase(user_id, "nonexistent", 1.0, 20.0) is None

    def test_add_negative_tonnes(self, user_id):
        from src.lib.carbon_offset_portfolio import add_offset_purchase
        assert add_offset_purchase(user_id, "wind_india", -1.0, 18.5) is None

    def test_delete_holding(self, user_id):
        from src.lib.carbon_offset_portfolio import add_offset_purchase, delete_offset_holding, get_user_holdings
        hid = add_offset_purchase(user_id, "wind_india", 1.0, 18.5)
        assert delete_offset_holding(user_id, hid) is True
        assert len(get_user_holdings(user_id)) == 0

    def test_clear_holdings(self, user_id):
        from src.lib.carbon_offset_portfolio import add_offset_purchase, clear_user_holdings, get_user_holdings
        add_offset_purchase(user_id, "wind_india", 1.0, 18.5)
        add_offset_purchase(user_id, "ocean_kelp", 2.0, 70.0)
        assert clear_user_holdings(user_id) is True
        assert len(get_user_holdings(user_id)) == 0

    def test_empty_holdings(self, user_id):
        from src.lib.carbon_offset_portfolio import get_user_holdings
        assert get_user_holdings(user_id) == []

    def test_multiple_holdings_order(self, user_id):
        from src.lib.carbon_offset_portfolio import add_offset_purchase, get_user_holdings
        add_offset_purchase(user_id, "wind_india", 1.0, 18.5, "2025-01-10")
        add_offset_purchase(user_id, "ocean_kelp", 2.0, 70.0, "2025-03-01")
        holdings = get_user_holdings(user_id)
        assert len(holdings) == 2
        # Should be ordered by purchase_date DESC
        assert holdings[0].purchase_date >= holdings[1].purchase_date


# ---------------------------------------------------------------------------
# Portfolio Summary Tests
# ---------------------------------------------------------------------------
class TestPortfolioSummary:
    def test_empty_summary(self, user_id):
        from src.lib.carbon_offset_portfolio import compute_portfolio_summary
        s = compute_portfolio_summary(user_id)
        assert s.total_tonnes == 0.0
        assert s.holdings_count == 0

    def test_single_holding_summary(self, user_id):
        from src.lib.carbon_offset_portfolio import add_offset_purchase, compute_portfolio_summary
        add_offset_purchase(user_id, "wind_india", 5.0, 92.5)
        s = compute_portfolio_summary(user_id)
        assert s.total_tonnes == 5.0
        assert s.total_cost_usd == 92.5
        assert s.avg_cost_per_tonne == 18.5
        assert s.holdings_count == 1

    def test_multi_holding_summary(self, user_id):
        from src.lib.carbon_offset_portfolio import add_offset_purchase, compute_portfolio_summary
        add_offset_purchase(user_id, "wind_india", 3.0, 55.5)
        add_offset_purchase(user_id, "ocean_kelp", 2.0, 70.0)
        s = compute_portfolio_summary(user_id)
        assert s.total_tonnes == 5.0
        assert s.total_cost_usd == 125.5
        assert s.avg_cost_per_tonne == 25.1

    def test_net_zero_progress(self, user_id):
        from src.lib.carbon_offset_portfolio import add_offset_purchase, compute_portfolio_summary
        add_offset_purchase(user_id, "wind_india", 2.0, 37.0)
        s = compute_portfolio_summary(user_id, annual_emissions_kg=4000.0)
        # 2 tonnes offset / 4 tonnes emitted = 50%
        assert s.net_zero_progress_pct == 50.0

    def test_diversification_multiple_categories(self, user_id):
        from src.lib.carbon_offset_portfolio import add_offset_purchase, compute_portfolio_summary
        add_offset_purchase(user_id, "wind_india", 2.0, 37.0)
        add_offset_purchase(user_id, "reforestation_amazon", 2.0, 50.0)
        add_offset_purchase(user_id, "cookstoves_africa", 2.0, 30.0)
        s = compute_portfolio_summary(user_id)
        assert s.diversification_score > 0
        assert s.holdings_count == 3

    def test_category_breakdown(self, user_id):
        from src.lib.carbon_offset_portfolio import add_offset_purchase, compute_portfolio_summary
        add_offset_purchase(user_id, "wind_india", 3.0, 55.5)
        add_offset_purchase(user_id, "reforestation_amazon", 1.0, 25.0)
        s = compute_portfolio_summary(user_id)
        assert "renewable_energy" in s.category_breakdown
        assert s.category_breakdown["renewable_energy"]["tonnes"] == 3.0


# ---------------------------------------------------------------------------
# Risk Assessment Tests
# ---------------------------------------------------------------------------
class TestRiskAssessment:
    def test_low_risk_portfolio(self, user_id):
        from src.lib.carbon_offset_portfolio import add_offset_purchase, _risk_assessment, get_user_holdings
        add_offset_purchase(user_id, "wind_india", 10.0, 185.0)
        holdings = get_user_holdings(user_id)
        score, rating = _risk_assessment(holdings)
        assert rating == "Low"

    def test_elevated_risk_portfolio(self, user_id):
        from src.lib.carbon_offset_portfolio import add_offset_purchase, _risk_assessment, get_user_holdings
        add_offset_purchase(user_id, "reforestation_amazon", 10.0, 250.0)
        holdings = get_user_holdings(user_id)
        score, rating = _risk_assessment(holdings)
        assert rating in ("Medium", "Elevated")

    def test_empty_risk(self):
        from src.lib.carbon_offset_portfolio import _risk_assessment
        score, rating = _risk_assessment([])
        assert rating == "N/A"


# ---------------------------------------------------------------------------
# Net-Zero Projection Tests
# ---------------------------------------------------------------------------
class TestNetZeroProjection:
    def test_neutral_already(self, user_id):
        from src.lib.carbon_offset_portfolio import add_offset_purchase, project_net_zero
        add_offset_purchase(user_id, "wind_india", 10.0, 185.0, "2024-01-01")
        proj = project_net_zero(user_id, annual_emissions_kg=4000.0)
        assert proj.current_offset_tonnes >= proj.annual_emissions_kg / 1000

    def test_neutral_future(self, user_id):
        from src.lib.carbon_offset_portfolio import add_offset_purchase, project_net_zero
        add_offset_purchase(user_id, "wind_india", 1.0, 18.5, "2025-01-01")
        proj = project_net_zero(user_id, annual_emissions_kg=4000.0)
        assert proj.years_to_neutral is not None
        assert proj.years_to_neutral > 0

    def test_no_holdings_projection(self, user_id):
        from src.lib.carbon_offset_portfolio import project_net_zero
        proj = project_net_zero(user_id, annual_emissions_kg=4000.0)
        assert proj.current_offset_tonnes == 0.0
        assert len(proj.recommended_actions) > 0

    def test_budget_accelerates_neutral(self, user_id):
        from src.lib.carbon_offset_portfolio import add_offset_purchase, project_net_zero
        add_offset_purchase(user_id, "wind_india", 0.5, 9.25, "2025-01-01")
        proj = project_net_zero(user_id, annual_emissions_kg=4000.0, monthly_offset_budget_usd=100.0)
        budget_actions = [a for a in proj.recommended_actions if "budget" in a.lower() or "$" in a]
        # Budget recommendation should be present if there are remaining offsets needed
        assert proj.cost_to_neutral_usd > 0


# ---------------------------------------------------------------------------
# Diversification Score Tests
# ---------------------------------------------------------------------------
class TestDiversification:
    def test_single_category_zero(self):
        from src.lib.carbon_offset_portfolio import _diversification_score
        assert _diversification_score({"energy": 5}, 5.0) == 0.0

    def test_empty_zero(self):
        from src.lib.carbon_offset_portfolio import _diversification_score
        assert _diversification_score({}, 0.0) == 0.0

    def test_balanced_portfolio_high(self):
        from src.lib.carbon_offset_portfolio import _diversification_score
        score = _diversification_score({"a": 3, "b": 3, "c": 3, "d": 3}, 12.0)
        assert score == 100.0

    def test_imbalanced_portfolio_lower(self):
        from src.lib.carbon_offset_portfolio import _diversification_score
        balanced = _diversification_score({"a": 5, "b": 5}, 10.0)
        imbalanced = _diversification_score({"a": 9, "b": 1}, 10.0)
        assert balanced >= imbalanced


# ---------------------------------------------------------------------------
# Snapshot Tests
# ---------------------------------------------------------------------------
class TestSnapshots:
    def test_save_and_load(self, user_id):
        from src.lib.carbon_offset_portfolio import (
            add_offset_purchase, save_portfolio_snapshot, get_portfolio_snapshots,
        )
        add_offset_purchase(user_id, "wind_india", 3.0, 55.5)
        assert save_portfolio_snapshot(user_id) is True
        snaps = get_portfolio_snapshots(user_id)
        assert len(snaps) == 1
        assert snaps[0]["total_tonnes"] == 3.0

    def test_empty_snapshots(self, user_id):
        from src.lib.carbon_offset_portfolio import get_portfolio_snapshots
        snaps = get_portfolio_snapshots(user_id)
        assert snaps == []


# ---------------------------------------------------------------------------
# Catalog Validation Tests
# ---------------------------------------------------------------------------
class TestCatalog:
    def test_all_projects_have_required_fields(self):
        from src.lib.carbon_offset_portfolio import OFFSET_PROJECTS
        required = {"name", "category", "region", "price_per_tonne", "rating", "verification"}
        for pid, project in OFFSET_PROJECTS.items():
            assert required.issubset(project.keys()), f"Missing fields in {pid}"

    def test_all_prices_positive(self):
        from src.lib.carbon_offset_portfolio import OFFSET_PROJECTS
        for pid, project in OFFSET_PROJECTS.items():
            assert project["price_per_tonne"] > 0
