"""
Unit tests for Smart HVAC Pre-cooling and Phase Change Thermal Storage Engine.
"""

import unittest
from src.energy.hvac_thermal_storage_engine import HVACThermalStorageEngine
from src.energy.hvac_thermal_storage_cards import render_hvac_schedule_summary

class TestHVACThermalStorageEngine(unittest.TestCase):

    def setUp(self):
        self.config = {
            "building_area_sqm": 250.0,
            "thermal_mass_capacity_kWh_C": 15.0,
            "pcm_installed_capacity_kWh": 30.0,
            "hvac_cop": 3.5,
            "target_indoor_temp_c": 22.0,
            "max_allowable_temp_c": 24.5
        }
        self.engine = HVACThermalStorageEngine(self.config)

    def test_24h_optimization_schedule(self):
        result = self.engine.optimize_24h_schedule()
        self.assertEqual(len(result["schedule"]), 24)
        self.assertGreater(result["total_daily_cost_usd"], 0)
        self.assertGreater(result["total_daily_carbon_kg"], 0)

    def test_pcm_discharge_during_peak(self):
        result = self.engine.optimize_24h_schedule()
        # Hour 15 is peak (price = 0.35)
        peak_hour_data = result["schedule"][15]
        self.assertLess(peak_hour_data["hvac_power_kw"], 3.0)

    def test_render_cards_html(self):
        summary = {
            "total_daily_cost_usd": 12.50,
            "total_daily_carbon_kg": 18.4,
            "peak_shaving_percentage": 34.5
        }
        html = render_hvac_schedule_summary(summary)
        self.assertIn("HVAC Thermal Storage", html)
        self.assertIn("34.5%", html)

if __name__ == "__main__":
    unittest.main()
