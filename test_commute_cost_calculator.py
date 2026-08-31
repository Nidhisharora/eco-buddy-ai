"""
Tests for Commute Cost Calculator Engine.

Tests cover:
- Cost breakdown calculations for each transport mode
- Environmental impact calculations
- Time metrics calculations
- Multi-mode comparison
- Savings analysis
- Breakeven analysis
- Report generation
- Edge cases (zero distance, extreme weather, etc.)
"""

import math
import pytest
from src.lifestyle.commute_cost_calculator import (
    TransportMode,
    CostCategory,
    WeatherCondition,
    TrafficLevel,
    VehicleInfo,
    CommuteProfile,
    CostBreakdown,
    EnvironmentalImpact,
    TimeMetrics,
    ModeComparison,
    EMISSION_FACTORS,
    AVERAGE_SPEEDS,
    MODE_LABELS,
    ACTIVE_MODES,
    VEHICLE_REQUIRED_MODES,
    calculate_single_mode,
    calculate_commute_comparison,
    calculate_savings_vs_driving,
    calculate_breakeven_analysis,
    generate_commute_report,
    format_currency,
    format_co2,
    format_time,
    _compute_fuel_cost,
    _compute_maintenance_cost,
    _compute_fare_cost,
    _compute_travel_time,
    _compute_health_benefit,
    _get_fuel_price,
    _get_electricity_price,
)


class TestVehicleInfo:
    """Tests for VehicleInfo dataclass."""

    def test_default_values(self):
        v = VehicleInfo()
        assert v.fuel_efficiency_mpg == 28.0
        assert v.annual_insurance_usd == 1800.0
        assert v.annual_depreciation_usd == 3000.0

    def test_custom_values(self):
        v = VehicleInfo(fuel_efficiency_mpg=40.0, annual_insurance_usd=1200.0)
        assert v.fuel_efficiency_mpg == 40.0
        assert v.annual_insurance_usd == 1200.0


class TestCommuteProfile:
    """Tests for CommuteProfile dataclass."""

    def test_default_profile(self):
        p = CommuteProfile(distance_km=10.0)
        assert p.distance_km == 10.0
        assert p.work_days_per_week == 5
        assert p.weather == WeatherCondition.SUNNY
        assert p.traffic == TrafficLevel.MODERATE

    def test_custom_profile(self):
        p = CommuteProfile(
            distance_km=25.0,
            work_days_per_week=4,
            weather=WeatherCondition.RAINY,
            traffic=TrafficLevel.HEAVY,
            hourly_wage_usd=35.0,
        )
        assert p.distance_km == 25.0
        assert p.work_days_per_week == 4
        assert p.weather == WeatherCondition.RAINY
        assert p.hourly_wage_usd == 35.0


class TestFuelPrices:
    """Tests for fuel price lookups."""

    def test_us_gasoline_price(self):
        price = _get_fuel_price("US", "gasoline")
        assert price == 0.95

    def test_eu_gasoline_price(self):
        price = _get_fuel_price("EU", "gasoline")
        assert price == 1.70

    def test_unknown_region_fallback(self):
        price = _get_fuel_price("Mars", "gasoline")
        assert price == 1.20  # Global fallback

    def test_us_electricity_price(self):
        price = _get_electricity_price("US")
        assert price == 0.13


class TestFuelCostCalculation:
    """Tests for fuel cost calculation."""

    def test_gasoline_car_fuel_cost(self):
        v = VehicleInfo(fuel_efficiency_mpg=28.0)
        cost = _compute_fuel_cost("driving_gas", 10.0, v, "US")
        assert cost > 0
        # 28 mpg = 235.215/28 = 8.4 L/100km -> 10km = 0.84L * $0.95 = $0.798
        assert 0.5 < cost < 1.5

    def test_ev_fuel_cost_lower_than_gas(self):
        v = VehicleInfo()
        ev_cost = _compute_fuel_cost("driving_ev", 10.0, v, "US")
        gas_cost = _compute_fuel_cost("driving_gas", 10.0, v, "US")
        assert ev_cost < gas_cost

    def test_biking_fuel_cost_zero(self):
        v = VehicleInfo()
        cost = _compute_fuel_cost("biking", 10.0, v, "US")
        assert cost == 0.0

    def test_walking_fuel_cost_zero(self):
        v = VehicleInfo()
        cost = _compute_fuel_cost("walking", 10.0, v, "US")
        assert cost == 0.0


class TestMaintenanceCost:
    """Tests for maintenance cost calculation."""

    def test_driving_has_maintenance(self):
        v = VehicleInfo()
        cost = _compute_maintenance_cost("driving_gas", 10.0, v)
        assert cost > 0

    def test_biking_no_maintenance(self):
        v = VehicleInfo()
        cost = _compute_maintenance_cost("biking", 10.0, v)
        assert cost == 0.0

    def test_maintenance_increases_with_distance(self):
        v = VehicleInfo()
        cost_short = _compute_maintenance_cost("driving_gas", 5.0, v)
        cost_long = _compute_maintenance_cost("driving_gas", 50.0, v)
        assert cost_long > cost_short


class TestFareCost:
    """Tests for fare cost calculation."""

    def test_bus_fare(self):
        fare = _compute_fare_cost("public_bus", 10.0)
        assert fare > 0
        assert fare < 5.0  # Should be reasonable

    def test_taxi_expensive(self):
        taxi_fare = _compute_fare_cost("taxi", 10.0)
        bus_fare = _compute_fare_cost("public_bus", 10.0)
        assert taxi_fare > bus_fare

    def test_carpool_cheap(self):
        carpool_fare = _compute_fare_cost("carpool", 10.0)
        taxi_fare = _compute_fare_cost("taxi", 10.0)
        assert carpool_fare < taxi_fare

    def test_driving_no_fare(self):
        fare = _compute_fare_cost("driving_gas", 10.0)
        assert fare == 0.0


class TestTravelTime:
    """Tests for travel time calculation."""

    def test_walking_slowest(self):
        time_walk = _compute_travel_time("walking", 10.0, WeatherCondition.SUNNY, TrafficLevel.LIGHT)
        time_drive = _compute_travel_time("driving_gas", 10.0, WeatherCondition.SUNNY, TrafficLevel.LIGHT)
        assert time_walk > time_drive

    def test_train_fast(self):
        time_train = _compute_travel_time("public_train", 10.0, WeatherCondition.SUNNY, TrafficLevel.LIGHT)
        time_bus = _compute_travel_time("public_bus", 10.0, WeatherCondition.SUNNY, TrafficLevel.LIGHT)
        assert time_train < time_bus

    def test_rainy_slows_biking(self):
        time_sunny = _compute_travel_time("biking", 10.0, WeatherCondition.SUNNY, TrafficLevel.LIGHT)
        time_rainy = _compute_travel_time("biking", 10.0, WeatherCondition.RAINY, TrafficLevel.LIGHT)
        assert time_rainy > time_sunny

    def test_traffic_slows_driving(self):
        time_light = _compute_travel_time("driving_gas", 10.0, WeatherCondition.SUNNY, TrafficLevel.LIGHT)
        time_gridlock = _compute_travel_time("driving_gas", 10.0, WeatherCondition.SUNNY, TrafficLevel.GRIDLOCK)
        assert time_gridlock > time_light * 1.5

    def test_biking_not_affected_by_traffic(self):
        time_light = _compute_travel_time("biking", 10.0, WeatherCondition.SUNNY, TrafficLevel.LIGHT)
        time_gridlock = _compute_travel_time("biking", 10.0, WeatherCondition.SUNNY, TrafficLevel.GRIDLOCK)
        ratio = time_gridlock / time_light
        assert ratio < 1.5  # Minimal traffic impact


class TestHealthBenefit:
    """Tests for health benefit calculation."""

    def test_biking_has_benefit(self):
        benefit = _compute_health_benefit("biking", 10.0)
        assert benefit > 0

    def test_walking_has_benefit(self):
        benefit = _compute_health_benefit("walking", 10.0)
        assert benefit > 0

    def test_driving_no_benefit(self):
        benefit = _compute_health_benefit("driving_gas", 10.0)
        assert benefit == 0.0

    def test_ebike_partial_benefit(self):
        biking = _compute_health_benefit("biking", 10.0)
        ebike = _compute_health_benefit("ebike", 10.0)
        assert biking > ebike > 0


class TestCostBreakdown:
    """Tests for CostBreakdown dataclass."""

    def test_total_financial(self):
        cb = CostBreakdown(fuel_cost=5.0, maintenance_cost=2.0, toll_cost=1.0)
        assert cb.total_financial == 8.0

    def test_total_with_time(self):
        cb = CostBreakdown(total_financial=8.0, time_cost=10.0, health_benefit=2.0)
        assert cb.total_with_time == 16.0

    def test_net_cost(self):
        cb = CostBreakdown(fuel_cost=5.0, time_cost=10.0, health_benefit=3.0)
        assert cb.net_cost == 12.0

    def test_to_dict(self):
        cb = CostBreakdown(fuel_cost=1.5, maintenance_cost=0.3)
        d = cb.to_dict()
        assert d["fuel_cost"] == 1.5
        assert d["maintenance_cost"] == 0.3
        assert "total_financial" in d


class TestEnvironmentalImpact:
    """Tests for EnvironmentalImpact dataclass."""

    def test_to_dict(self):
        ei = EnvironmentalImpact(co2_kg=1.5, nox_grams=0.3)
        d = ei.to_dict()
        assert d["co2_kg"] == 1.5
        assert d["nox_grams"] == 0.3

    def test_zero_emissions_modes(self):
        profile = CommuteProfile(distance_km=10.0)
        comp = calculate_single_mode("biking", profile)
        assert comp.environmental.co2_kg == 0.0
        assert comp.environmental.nox_grams == 0.0


class TestSingleModeCalculation:
    """Tests for single mode cost calculation."""

    def test_driving_gas_profile(self):
        profile = CommuteProfile(distance_km=10.0)
        comp = calculate_single_mode("driving_gas", profile)
        assert comp.mode == "driving_gas"
        assert comp.cost_breakdown.fuel_cost > 0
        assert comp.annual_financial_cost > 0
        assert comp.annual_co2_kg > 0
        assert 0 <= comp.score <= 100
        assert len(comp.warnings) >= 0

    def test_biking_profile(self):
        profile = CommuteProfile(distance_km=5.0)
        comp = calculate_single_mode("biking", profile)
        assert comp.environmental.co2_kg == 0.0
        assert comp.cost_breakdown.fuel_cost == 0.0
        assert comp.time_metrics.health_minutes_gained > 0
        assert comp.recommendation_tag == "🏆 Health Champion"

    def test_ev_has_charging_cost(self):
        profile = CommuteProfile(distance_km=10.0)
        comp = calculate_single_mode("driving_ev", profile)
        assert comp.cost_breakdown.charging_cost == 0.0  # Handled in fuel_cost
        assert comp.cost_breakdown.fuel_cost > 0

    def test_taxi_has_fare(self):
        profile = CommuteProfile(distance_km=10.0)
        comp = calculate_single_mode("taxi", profile)
        assert comp.cost_breakdown.fare_cost > 0

    def test_mode_label_exists(self):
        for mode in TransportMode:
            profile = CommuteProfile(distance_km=10.0)
            comp = calculate_single_mode(mode.value, profile)
            assert comp.mode_label != ""

    def test_annual_calculations(self):
        profile = CommuteProfile(distance_km=15.0, work_days_per_week=5, weeks_per_year=48)
        comp = calculate_single_mode("driving_gas", profile)
        expected_trips = 5 * 48 * 2
        assert comp.annual_financial_cost == pytest.approx(
            comp.cost_breakdown.total_financial * expected_trips, rel=0.01
        )


class TestCommuteComparison:
    """Tests for multi-mode comparison."""

    def test_comparison_returns_all_modes(self):
        profile = CommuteProfile(distance_km=10.0)
        comparisons = calculate_commute_comparison(profile)
        assert len(comparisons) == len(TransportMode)

    def test_comparison_sorted_by_score(self):
        profile = CommuteProfile(distance_km=10.0)
        comparisons = calculate_commute_comparison(profile)
        scores = [c.score for c in comparisons]
        assert scores == sorted(scores, reverse=True)

    def test_biking_beats_driving(self):
        profile = CommuteProfile(distance_km=10.0)
        comparisons = calculate_commute_comparison(profile)
        modes = {c.mode: c for c in comparisons}
        assert modes["biking"].score >= modes["driving_gas"].score

    def test_different_distances(self):
        for dist in [1.0, 5.0, 15.0, 30.0, 50.0]:
            profile = CommuteProfile(distance_km=dist)
            comparisons = calculate_commute_comparison(profile)
            assert len(comparisons) > 0


class TestSavingsAnalysis:
    """Tests for savings vs driving analysis."""

    def test_ev_savings(self):
        profile = CommuteProfile(distance_km=20.0)
        savings = calculate_savings_vs_driving(profile, "driving_ev")
        assert savings["baseline_mode"] != savings["alternative_mode"]
        assert savings["baseline_annual_cost"] > 0

    def test_biking_vs_driving(self):
        profile = CommuteProfile(distance_km=10.0)
        savings = calculate_savings_vs_driving(profile, "biking")
        assert savings["annual_co2_saved_kg"] > 0

    def test_bus_vs_driving(self):
        profile = CommuteProfile(distance_km=15.0)
        savings = calculate_savings_vs_driving(profile, "public_bus")
        assert savings["percent_cost_reduction"] >= 0 or savings["annual_co2_saved_kg"] >= 0


class TestBreakevenAnalysis:
    """Tests for breakeven analysis."""

    def test_ebike_breakeven(self):
        profile = CommuteProfile(distance_km=10.0)
        result = calculate_breakeven_analysis(
            profile, "ebike", 1500.0, "E-Bike",
        )
        assert result["investment_usd"] == 1500.0
        assert result["investment_item"] == "E-Bike"
        assert result["daily_saving_usd"] >= 0

    def test_ev_breakeven(self):
        profile = CommuteProfile(distance_km=25.0)
        result = calculate_breakeven_analysis(
            profile, "driving_ev", 8000.0, "EV Conversion",
        )
        assert result["target_mode"] != ""


class TestReportGeneration:
    """Tests for comprehensive report generation."""

    def test_report_structure(self):
        profile = CommuteProfile(distance_km=15.0)
        report = generate_commute_report(profile)
        assert "profile" in report
        assert "comparisons" in report
        assert "category_leaders" in report
        assert "savings_analysis" in report
        assert "summary" in report
        assert "generated_at" in report

    def test_report_profile_data(self):
        profile = CommuteProfile(distance_km=20.0, work_days_per_week=4)
        report = generate_commute_report(profile)
        assert report["profile"]["distance_km"] == 20.0
        assert report["profile"]["work_days_per_week"] == 4
        assert report["profile"]["annual_trips"] == 4 * 48 * 2

    def test_report_has_recommendations(self):
        profile = CommuteProfile(distance_km=10.0)
        report = generate_commute_report(profile)
        assert report["top_recommendation"] is not None
        assert "mode" in report["top_recommendation"]

    def test_report_category_leaders(self):
        profile = CommuteProfile(distance_km=10.0)
        report = generate_commute_report(profile)
        leaders = report["category_leaders"]
        assert leaders["cheapest"] is not None
        assert leaders["greenest"] is not None
        assert leaders["fastest"] is not None
        assert leaders["healthiest"] is not None

    def test_report_summary(self):
        profile = CommuteProfile(distance_km=10.0)
        report = generate_commute_report(profile)
        summary = report["summary"]
        assert summary["modes_compared"] > 0
        assert summary["best_mode"] != "N/A"


class TestFormatting:
    """Tests for display formatting utilities."""

    def test_format_currency(self):
        assert format_currency(1234.56) == "$1,235"
        assert format_currency(0.50) == "$0.50"
        assert format_currency(15000) == "$15,000"

    def test_format_co2(self):
        assert format_co2(500.0) == "500.0 kg CO₂"
        assert format_co2(1500.0) == "1.5 t CO₂"

    def test_format_time(self):
        assert format_time(45) == "45 min"
        assert format_time(90) == "1h 30m"
        assert format_time(120) == "2h 0m"


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_zero_distance(self):
        profile = CommuteProfile(distance_km=0.0)
        comp = calculate_single_mode("driving_gas", profile)
        assert comp.cost_breakdown.fuel_cost == 0.0
        assert comp.environmental.co2_kg == 0.0

    def test_very_long_distance(self):
        profile = CommuteProfile(distance_km=200.0)
        comp = calculate_single_mode("driving_gas", profile)
        assert comp.annual_financial_cost > 1000

    def test_all_weather_conditions(self):
        for weather in WeatherCondition:
            profile = CommuteProfile(distance_km=10.0, weather=weather)
            comp = calculate_single_mode("driving_gas", profile)
            assert comp.time_metrics.travel_time_minutes > 0

    def test_all_traffic_levels(self):
        for traffic in TrafficLevel:
            profile = CommuteProfile(distance_km=10.0, traffic=traffic)
            comp = calculate_single_mode("driving_gas", profile)
            assert comp.time_metrics.travel_time_minutes > 0

    def test_different_regions(self):
        for region in ["US", "EU", "UK", "India", "Global"]:
            profile = CommuteProfile(distance_km=10.0, region=region)
            comp = calculate_single_mode("driving_gas", profile)
            assert comp.cost_breakdown.fuel_cost > 0

    def test_very_high_wage(self):
        profile = CommuteProfile(distance_km=10.0, hourly_wage_usd=200.0)
        comp = calculate_single_mode("driving_gas", profile)
        assert comp.time_metrics.productivity_loss_usd > 0

    def test_zero_wage(self):
        profile = CommuteProfile(distance_km=10.0, hourly_wage_usd=0.0)
        comp = calculate_single_mode("driving_gas", profile)
        assert comp.time_metrics.productivity_loss_usd == 0.0

    def test_emission_factors_coverage(self):
        """Ensure all modes have emission factors."""
        for mode in TransportMode:
            assert mode.value in EMISSION_FACTORS, f"Missing emission factor for {mode.value}"

    def test_average_speeds_coverage(self):
        """Ensure all modes have average speeds."""
        for mode in TransportMode:
            assert mode.value in AVERAGE_SPEEDS, f"Missing average speed for {mode.value}"

    def test_mode_labels_coverage(self):
        """Ensure all modes have labels."""
        for mode in TransportMode:
            assert mode.value in MODE_LABELS, f"Missing label for {mode.value}"

    def test_extreme_weather_driving(self):
        profile = CommuteProfile(
            distance_km=10.0,
            weather=WeatherCondition.SNOWY,
            traffic=TrafficLevel.GRIDLOCK,
        )
        comp = calculate_single_mode("driving_gas", profile)
        assert comp.time_metrics.travel_time_minutes > 0
        assert comp.warnings  # Should have warnings

    def test_walking_short_distance(self):
        profile = CommuteProfile(distance_km=1.0)
        comp = calculate_single_mode("walking", profile)
        assert comp.time_metrics.health_minutes_gained > 0
        assert comp.cost_breakdown.total_financial == 0.0

    def test_mode_comparison_deterministic(self):
        """Same inputs should produce same outputs."""
        profile = CommuteProfile(distance_km=10.0)
        comp1 = calculate_single_mode("driving_gas", profile)
        comp2 = calculate_single_mode("driving_gas", profile)
        assert comp1.score == comp2.score
        assert comp1.annual_financial_cost == comp2.annual_financial_cost

    def test_highway_vs_city_driving(self):
        """Longer distance should have different cost profile than short."""
        short = CommuteProfile(distance_km=3.0)
        long = CommuteProfile(distance_km=50.0)
        comp_short = calculate_single_mode("driving_gas", short)
        comp_long = calculate_single_mode("driving_gas", long)
        assert comp_long.annual_financial_cost > comp_short.annual_financial_cost
        assert comp_long.annual_co2_kg > comp_short.annual_co2_kg
