"""
Types for Smart HVAC Pre-cooling and Phase Change Thermal Storage Engine.
"""

from typing import TypedDict, List, Dict, Any

class HVACBuildingConfig(TypedDict):
    building_area_sqm: float
    thermal_mass_capacity_kWh_C: float
    pcm_installed_capacity_kWh: float  # Phase Change Material capacity
    hvac_cop: float  # Coefficient of Performance
    target_indoor_temp_c: float
    max_allowable_temp_c: float

class HourlyGridTariff(TypedDict):
    hour: int  # 0 to 23
    price_usd_per_kwh: float
    carbon_intensity_g_per_kwh: float

class ThermalStoragePlan(TypedDict):
    hour: int
    hvac_power_kw: float
    pcm_state_of_charge: float
    indoor_temp_c: float
    cost_usd: float
    carbon_emissions_kg: float
