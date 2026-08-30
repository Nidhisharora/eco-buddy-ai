"""
Type definitions for Corporate Scope 3 Value-Chain Insetting & Intervention Exchange.
"""

from typing import TypedDict, List, Dict, Any

class InsettingProject(TypedDict):
    project_id: str
    supplier_name: str
    tier_level: int  # Tier 1, 2, 3 supplier
    intervention_type: str  # e.g., 'regenerative_ag', 'fleet_electrification', 'renewable_heat'
    capital_expenditure_usd: float
    annual_abatement_tco2e: float
    verification_standard: str  # 'Verra', 'GoldStandard', 'GHGP_Insetting'
    risk_factor: float  # 0.0 to 1.0

class PortfolioInsettingRequest(TypedDict):
    company_id: str
    target_scope3_reduction_tco2e: float
    max_budget_usd: float
    preferred_tiers: List[int]
