"""
Sustainable Portfolio Analyzer.
Calculates the total portfolio carbon footprint, identifies high-emission "hotspot" holdings, and simulates rebalancing.
"""

from typing import Dict, Any, List
from asset_carbon_db import AssetCarbonDB


class SustainablePortfolioAnalyzer:
    """Analyzes and optimizes the carbon footprint of an investment portfolio."""

    def __init__(self):
        self.db = AssetCarbonDB()
        self.holdings: Dict[str, float] = {}  # asset_key: amount_invested_usd

    def add_holding(self, asset_key: str, amount_usd: float) -> bool:
        """Adds or updates a holding in the portfolio."""
        if self.db.get_asset_details(asset_key):
            self.holdings[asset_key] = self.holdings.get(asset_key, 0.0) + amount_usd
            return True
        return False

    def analyze_portfolio(self) -> Dict[str, Any]:
        """Calculates the total financed emissions and Paris alignment of the portfolio."""
        total_invested = sum(self.holdings.values())
        if total_invested == 0:
            return self._empty_analysis()

        total_emissions_tonnes = 0.0
        weighted_alignment_score = 0.0
        asset_breakdown = []

        for asset_key, amount in self.holdings.items():
            details = self.db.get_asset_details(asset_key)
            weight = amount / total_invested

            # Emissions: (amount / 1,000,000) * intensity
            emissions = (amount / 1_000_000.0) * details["emission_intensity"]
            total_emissions_tonnes += emissions

            weighted_alignment_score += weight * details["paris_alignment_score"]

            asset_breakdown.append(
                {
                    "asset_key": asset_key,
                    "name": details["name"],
                    "amount_usd": amount,
                    "weight_pct": round(weight * 100, 1),
                    "emissions_tonnes": round(emissions, 3),
                    "alignment_score": details["paris_alignment_score"],
                }
            )

        # Sort breakdown by emissions descending to identify hotspots
        asset_breakdown.sort(key=lambda x: x["emissions_tonnes"], reverse=True)

        return {
            "total_invested_usd": round(total_invested, 2),
            "total_emissions_tonnes": round(total_emissions_tonnes, 3),
            "weighted_alignment_score": round(weighted_alignment_score, 1),
            "asset_breakdown": asset_breakdown,
            "hotspots": asset_breakdown[:2],  # Top 2 emission contributors
        }

    def simulate_rebalance(
        self, hotspot_asset_key: str, alternative_asset_key: str, amount_to_swap: float
    ) -> Dict[str, Any]:
        """Simulates the carbon impact of swapping a portion of a hotspot holding."""
        if (
            hotspot_asset_key not in self.holdings
            or amount_to_swap > self.holdings[hotspot_asset_key]
        ):
            return {"error": "Invalid swap parameters."}

        current_analysis = self.analyze_portfolio()

        # Calculate new emissions
        hotspot_details = self.db.get_asset_details(hotspot_asset_key)
        alt_details = self.db.get_asset_details(alternative_asset_key)

        current_emissions_from_swap = (amount_to_swap / 1_000_000.0) * hotspot_details[
            "emission_intensity"
        ]
        new_emissions_from_swap = (amount_to_swap / 1_000_000.0) * alt_details[
            "emission_intensity"
        ]

        emissions_reduced = current_emissions_from_swap - new_emissions_from_swap

        return {
            "amount_swapped_usd": amount_to_swap,
            "from_asset": hotspot_details["name"],
            "to_asset": alt_details["name"],
            "emissions_reduced_tonnes": round(emissions_reduced, 3),
            "new_portfolio_emissions_tonnes": round(
                current_analysis["total_emissions_tonnes"] - emissions_reduced, 3
            ),
            "new_alignment_score": round(
                current_analysis["weighted_alignment_score"] + 2.0, 1
            ),  # Mock improvement
        }

    def _empty_analysis(self) -> Dict[str, Any]:
        return {
            "total_invested_usd": 0.0,
            "total_emissions_tonnes": 0.0,
            "weighted_alignment_score": 0.0,
            "asset_breakdown": [],
            "hotspots": [],
        }
