"""
Asset Carbon Database.
Manages a mock dataset of major market indices, sector ETFs, and specific companies with estimated financed emission intensities.
"""

from typing import Dict, Any, Optional


class AssetCarbonDB:
    """Provides access to financed emission data for financial assets."""

    # Mock dataset: emission_intensity (tonnes CO2e per $1M invested), paris_alignment_score (0-100, 100 is best)
    ASSET_DATABASE = {
        "sp500_etf": {
            "name": "S&P 500 Index ETF",
            "type": "index",
            "emission_intensity": 120.0,
            "paris_alignment_score": 45,
            "description": "Broad market exposure, includes high carbon sectors like energy and materials.",
        },
        "clean_energy_etf": {
            "name": "Global Clean Energy ETF",
            "type": "sector",
            "emission_intensity": 35.0,
            "paris_alignment_score": 85,
            "description": "Focused on renewable energy producers and technology.",
        },
        "fossil_fuel_corp": {
            "name": "Major Oil & Gas Corp",
            "type": "equity",
            "emission_intensity": 450.0,
            "paris_alignment_score": 10,
            "description": "High Scope 3 emissions from end-use of fossil fuel products.",
        },
        "tech_giant": {
            "name": "Major Tech Company",
            "type": "equity",
            "emission_intensity": 40.0,
            "paris_alignment_score": 75,
            "description": "Low direct emissions, but significant data center energy usage.",
        },
        "esg_leaders_fund": {
            "name": "ESG Leaders Mutual Fund",
            "type": "mutual_fund",
            "emission_intensity": 60.0,
            "paris_alignment_score": 80,
            "description": "Actively screened for low carbon intensity and strong governance.",
        },
        "bond_aggregate": {
            "name": "Total Bond Market Fund",
            "type": "fixed_income",
            "emission_intensity": 80.0,
            "paris_alignment_score": 50,
            "description": "Mixed portfolio of government and corporate debt.",
        },
    }

    def __init__(self):
        self.database = self.ASSET_DATABASE

    def get_asset_details(self, asset_key: str) -> Optional[Dict[str, Any]]:
        """Retrieves carbon data for a specific financial asset."""
        return self.database.get(asset_key.lower())

    def get_all_assets(self) -> list:
        """Returns a list of all available asset keys."""
        return list(self.database.keys())

    def get_asset_display_name(self, asset_key: str) -> str:
        """Returns the human-readable name of the asset."""
        details = self.get_asset_details(asset_key)
        return details["name"] if details else asset_key.replace("_", " ").title()

    def find_green_alternatives(self, current_asset_key: str) -> list:
        """Suggests lower-carbon alternatives to a given asset."""
        current = self.get_asset_details(current_asset_key)
        if not current:
            return []

        alternatives = []
        for key, details in self.database.items():
            if key == current_asset_key:
                continue
            # Suggest if it has lower emission intensity and higher Paris alignment
            if (
                details["emission_intensity"] < current["emission_intensity"]
                and details["paris_alignment_score"] > current["paris_alignment_score"]
            ):
                alternatives.append(
                    {
                        "key": key,
                        "name": details["name"],
                        "emission_intensity": details["emission_intensity"],
                        "paris_alignment_score": details["paris_alignment_score"],
                        "description": details["description"],
                    }
                )

        # Sort by lowest emission intensity
        return sorted(alternatives, key=lambda x: x["emission_intensity"])
