"""
Corporate Scope 3 Value-Chain Insetting & Intervention Exchange Engine.
"""

from typing import List, Dict, Any
from src.business.scope3_insetting_types import InsettingProject, PortfolioInsettingRequest
from src.business.scope3_insetting_db import INSETTING_PROJECTS_CATALOG

class Scope3InsettingEngine:
    """
    Optimizes allocation of corporate carbon budgets into direct supply chain intervention (insetting)
    rather than unverified external carbon offsets.
    """

    def __init__(self, catalog: List[InsettingProject] = None):
        self.catalog = catalog or INSETTING_PROJECTS_CATALOG

    def optimize_insetting_portfolio(self, request: PortfolioInsettingRequest) -> Dict[str, Any]:
        available_budget = request["max_budget_usd"]
        target_abatement = request["target_scope3_reduction_tco2e"]
        preferred_tiers = request.get("preferred_tiers", [1, 2, 3])

        # Filter eligible projects by tier
        eligible = [p for p in self.catalog if p["tier_level"] in preferred_tiers]

        # Sort by Abatement Cost Efficiency ($ per tCO2e) ascending
        eligible.sort(key=lambda p: (p["capital_expenditure_usd"] / p["annual_abatement_tco2e"]))

        selected_projects = []
        spent_budget = 0.0
        total_abatement = 0.0

        for proj in eligible:
            cost = proj["capital_expenditure_usd"]
            abatement = proj["annual_abatement_tco2e"]

            if spent_budget + cost <= available_budget:
                selected_projects.append(proj)
                spent_budget += cost
                total_abatement += abatement

        weighted_cost_per_ton = (spent_budget / total_abatement) if total_abatement > 0 else 0.0
        gap_to_target = max(0.0, target_abatement - total_abatement)

        return {
            "selected_projects": selected_projects,
            "total_budget_allocated_usd": round(spent_budget, 2),
            "total_annual_abatement_tco2e": round(total_abatement, 2),
            "average_abatement_cost_usd_per_tco2e": round(weighted_cost_per_ton, 2),
            "target_completion_percentage": round(min(100.0, (total_abatement / target_abatement) * 100.0), 2) if target_abatement > 0 else 100.0,
            "unmet_abatement_gap_tco2e": round(gap_to_target, 2)
        }
