"""
Verified supplier interventions catalog for Scope 3 supply chain insetting.
"""

INSETTING_PROJECTS_CATALOG = [
    {
        "project_id": "proj_regen_farm_01",
        "supplier_name": "AgriCrop Co-op",
        "tier_level": 2,
        "intervention_type": "regenerative_ag",
        "capital_expenditure_usd": 45000.0,
        "annual_abatement_tco2e": 1200.0,
        "verification_standard": "GoldStandard",
        "risk_factor": 0.05
    },
    {
        "project_id": "proj_fleet_ev_02",
        "supplier_name": "LogiTrans Logistics",
        "tier_level": 1,
        "intervention_type": "fleet_electrification",
        "capital_expenditure_usd": 120000.0,
        "annual_abatement_tco2e": 2800.0,
        "verification_standard": "GHGP_Insetting",
        "risk_factor": 0.02
    },
    {
        "project_id": "proj_biomass_boiler_03",
        "supplier_name": "PaperKraft Mill",
        "tier_level": 3,
        "intervention_type": "renewable_heat",
        "capital_expenditure_usd": 85000.0,
        "annual_abatement_tco2e": 1950.0,
        "verification_standard": "Verra",
        "risk_factor": 0.08
    }
]
