"""
Unit tests for Sustainable Portfolio Analyzer and Asset Carbon DB.
"""

import pytest
from sustainable_portfolio_analyzer import SustainablePortfolioAnalyzer
from asset_carbon_db import AssetCarbonDB


def test_db_retrieval_and_alternatives():
    db = AssetCarbonDB()
    details = db.get_asset_details("fossil_fuel_corp")

    assert details is not None
    assert details["emission_intensity"] == 450.0

    alts = db.find_green_alternatives("fossil_fuel_corp")
    assert len(alts) > 0
    assert all(alt["emission_intensity"] < 450.0 for alt in alts)
    assert all(alt["paris_alignment_score"] > 10 for alt in alts)


def test_analyzer_portfolio_calculation():
    analyzer = SustainablePortfolioAnalyzer()
    analyzer.add_holding("fossil_fuel_corp", 1_000_000.0)  # $1M invested
    analyzer.add_holding("clean_energy_etf", 1_000_000.0)  # $1M invested

    analysis = analyzer.analyze_portfolio()

    assert analysis["total_invested_usd"] == 2_000_000.0
    # Emissions: (1M/1M * 450) + (1M/1M * 35) = 485
    assert analysis["total_emissions_tonnes"] == 485.0
    assert len(analysis["hotspots"]) == 2
    assert analysis["hotspots"][0]["name"] == "Major Oil & Gas Corp"


def test_analyzer_rebalance_simulation():
    analyzer = SustainablePortfolioAnalyzer()
    analyzer.add_holding("fossil_fuel_corp", 100_000.0)

    # Swap $50,000 from fossil fuel (450 intensity) to clean energy (35 intensity)
    # Emissions reduced = (50,000 / 1,000,000) * (450 - 35) = 0.05 * 415 = 20.75
    sim = analyzer.simulate_rebalance("fossil_fuel_corp", "clean_energy_etf", 50_000.0)

    assert sim["amount_swapped_usd"] == 50_000.0
    assert sim["emissions_reduced_tonnes"] == 20.75
    assert sim["new_portfolio_emissions_tonnes"] == 24.25  # 45.0 - 20.75


def test_analyzer_invalid_rebalance():
    analyzer = SustainablePortfolioAnalyzer()
    analyzer.add_holding("tech_giant", 10_000.0)

    # Try to swap more than held
    sim = analyzer.simulate_rebalance("tech_giant", "esg_leaders_fund", 20_000.0)
    assert "error" in sim
