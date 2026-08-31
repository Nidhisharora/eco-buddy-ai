"""
Commute Cost Calculator Engine.

Provides comprehensive cost analysis for daily commutes including:
- Financial costs (fuel, maintenance, insurance, parking, tolls, fares)
- Environmental costs (CO2 emissions, pollution equivalents)
- Time costs (travel time, productivity loss)
- Comparison across multiple transport modes
- Annual projections and savings calculations
- Historical cost tracking
"""

import math
import logging
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class TransportMode(Enum):
    """Supported transport modes for cost calculation."""
    DRIVING_GAS = "driving_gas"
    DRIVING_DIESEL = "driving_diesel"
    DRIVING_HYBRID = "driving_hybrid"
    DRIVING_EV = "driving_ev"
    PUBLIC_BUS = "public_bus"
    PUBLIC_SUBWAY = "public_subway"
    PUBLIC_TRAIN = "public_train"
    RIDE_SHARE = "ride_share"
    TAXI = "taxi"
    BIKING = "biking"
    EBIKE = "ebike"
    WALKING = "walking"
    CARPOOL = "carpool"
    SCOOTER = "scooter"


class CostCategory(Enum):
    """Categories of commute costs."""
    FUEL = "fuel"
    MAINTENANCE = "maintenance"
    INSURANCE = "insurance"
    PARKING = "parking"
    TOLLS = "tolls"
    FARE = "fare"
    DEPRECIATION = "depreciation"
    CHARGING = "charging"
    WEAR_TEAR = "wear_tear"
    TIME = "time"
    HEALTH_BENEFIT = "health_benefit"


class WeatherCondition(Enum):
    """Weather conditions affecting commute costs."""
    SUNNY = "sunny"
    RAINY = "rainy"
    SNOWY = "snowy"
    EXTREME_HEAT = "extreme_heat"
    WINDY = "windy"


class TrafficLevel(Enum):
    """Traffic congestion levels."""
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"
    GRIDLOCK = "gridlock"


@dataclass
class VehicleInfo:
    """Details about the user's personal vehicle."""
    vehicle_type: str = "sedan"
    fuel_type: str = "gasoline"
    fuel_efficiency_mpg: float = 28.0
    annual_insurance_usd: float = 1800.0
    annual_depreciation_usd: float = 3000.0
    monthly_parking_usd: float = 150.0
    vehicle_weight_kg: float = 1500.0
    tire_wear_per_km: float = 0.002
    oil_change_interval_km: float = 8000.0
    oil_change_cost: float = 75.0
    tire_replacement_km: float = 60000.0
    tire_replacement_cost: float = 600.0


@dataclass
class CommuteProfile:
    """Complete profile for a commute cost calculation."""
    distance_km: float
    work_days_per_week: int = 5
    weeks_per_year: int = 48
    vehicle: VehicleInfo = field(default_factory=VehicleInfo)
    weather: WeatherCondition = WeatherCondition.SUNNY
    traffic: TrafficLevel = TrafficLevel.MODERATE
    parking_cost_per_day: float = 0.0
    toll_cost_per_trip: float = 0.0
    hourly_wage_usd: float = 25.0
    region: str = "US"


@dataclass
class CostBreakdown:
    """Detailed breakdown of costs for a single commute trip."""
    fuel_cost: float = 0.0
    maintenance_cost: float = 0.0
    insurance_daily: float = 0.0
    parking_cost: float = 0.0
    toll_cost: float = 0.0
    depreciation_daily: float = 0.0
    charging_cost: float = 0.0
    wear_tear_cost: float = 0.0
    fare_cost: float = 0.0
    time_cost: float = 0.0
    health_benefit: float = 0.0

    @property
    def total_financial(self) -> float:
        """Total direct financial cost per trip."""
        return (
            self.fuel_cost
            + self.maintenance_cost
            + self.insurance_daily
            + self.parking_cost
            + self.toll_cost
            + self.depreciation_daily
            + self.charging_cost
            + self.wear_tear_cost
            + self.fare_cost
        )

    @property
    def total_with_time(self) -> float:
        """Total cost including time value."""
        return self.total_financial + self.time_cost - self.health_benefit

    @property
    def net_cost(self) -> float:
        """Net cost after health benefits."""
        return self.total_with_time

    def to_dict(self) -> dict[str, float]:
        """Convert breakdown to dictionary for serialization."""
        return {
            "fuel_cost": round(self.fuel_cost, 4),
            "maintenance_cost": round(self.maintenance_cost, 4),
            "insurance_daily": round(self.insurance_daily, 4),
            "parking_cost": round(self.parking_cost, 4),
            "toll_cost": round(self.toll_cost, 4),
            "depreciation_daily": round(self.depreciation_daily, 4),
            "charging_cost": round(self.charging_cost, 4),
            "wear_tear_cost": round(self.wear_tear_cost, 4),
            "fare_cost": round(self.fare_cost, 4),
            "time_cost": round(self.time_cost, 4),
            "health_benefit": round(self.health_benefit, 4),
            "total_financial": round(self.total_financial, 4),
            "total_with_time": round(self.total_with_time, 4),
            "net_cost": round(self.net_cost, 4),
        }


@dataclass
class EnvironmentalImpact:
    """Environmental impact metrics for a commute."""
    co2_kg: float = 0.0
    nox_grams: float = 0.0
    pm25_grams: float = 0.0
    co2_annual_kg: float = 0.0
    trees_needed: int = 0
    equivalence_car_days: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "co2_kg": round(self.co2_kg, 4),
            "nox_grams": round(self.nox_grams, 4),
            "pm25_grams": round(self.pm25_grams, 4),
            "co2_annual_kg": round(self.co2_annual_kg, 4),
            "trees_needed": self.trees_needed,
            "equivalence_car_days": round(self.equivalence_car_days, 2),
        }


@dataclass
class TimeMetrics:
    """Time-related metrics for a commute."""
    travel_time_minutes: float = 0.0
    travel_time_annual_hours: float = 0.0
    productivity_loss_usd: float = 0.0
    health_minutes_gained: float = 0.0
    health_annual_hours: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "travel_time_minutes": round(self.travel_time_minutes, 1),
            "travel_time_annual_hours": round(self.travel_time_annual_hours, 1),
            "productivity_loss_usd": round(self.productivity_loss_usd, 2),
            "health_minutes_gained": round(self.health_minutes_gained, 1),
            "health_annual_hours": round(self.health_annual_hours, 1),
        }


@dataclass
class ModeComparison:
    """Complete comparison result for a single transport mode."""
    mode: str
    mode_label: str
    cost_breakdown: CostBreakdown
    environmental: EnvironmentalImpact
    time_metrics: TimeMetrics
    annual_financial_cost: float = 0.0
    annual_total_cost: float = 0.0
    annual_co2_kg: float = 0.0
    score: float = 0.0
    recommendation_tag: str = ""
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "mode": self.mode,
            "mode_label": self.mode_label,
            "cost_breakdown": self.cost_breakdown.to_dict(),
            "environmental": self.environmental.to_dict(),
            "time_metrics": self.time_metrics.to_dict(),
            "annual_financial_cost": round(self.annual_financial_cost, 2),
            "annual_total_cost": round(self.annual_total_cost, 2),
            "annual_co2_kg": round(self.annual_co2_kg, 2),
            "score": round(self.score, 2),
            "recommendation_tag": self.recommendation_tag,
            "warnings": self.warnings,
        }


# ---------------------------------------------------------------------------
# Emission factors (kg CO2 per km) for each transport mode
# ---------------------------------------------------------------------------
EMISSION_FACTORS: dict[str, float] = {
    "driving_gas": 0.192,
    "driving_diesel": 0.172,
    "driving_hybrid": 0.109,
    "driving_ev": 0.053,
    "public_bus": 0.105,
    "public_subway": 0.041,
    "public_train": 0.060,
    "ride_share": 0.210,
    "taxi": 0.220,
    "biking": 0.0,
    "ebike": 0.015,
    "walking": 0.0,
    "carpool": 0.096,
    "scooter": 0.085,
}

# Average speed (km/h) per mode for time estimation
AVERAGE_SPEEDS: dict[str, float] = {
    "driving_gas": 35.0,
    "driving_diesel": 35.0,
    "driving_hybrid": 35.0,
    "driving_ev": 35.0,
    "public_bus": 20.0,
    "public_subway": 30.0,
    "public_train": 45.0,
    "ride_share": 30.0,
    "taxi": 30.0,
    "biking": 16.0,
    "ebike": 24.0,
    "walking": 5.0,
    "carpool": 35.0,
    "scooter": 20.0,
}

# Fuel price per liter (approximate defaults by region)
FUEL_PRICES: dict[str, dict[str, float]] = {
    "US": {"gasoline": 0.95, "diesel": 1.05, "electricity_per_kwh": 0.13},
    "EU": {"gasoline": 1.70, "diesel": 1.60, "electricity_per_kwh": 0.25},
    "UK": {"gasoline": 1.60, "diesel": 1.70, "electricity_per_kwh": 0.28},
    "India": {"gasoline": 1.10, "diesel": 0.95, "electricity_per_kwh": 0.08},
    "Global": {"gasoline": 1.20, "diesel": 1.10, "electricity_per_kwh": 0.15},
}

# Public transit fares (USD per km, approximate)
TRANSIT_FARES_PER_KM: dict[str, float] = {
    "public_bus": 0.15,
    "public_subway": 0.18,
    "public_train": 0.20,
    "ride_share": 1.50,
    "taxi": 2.00,
    "carpool": 0.08,
    "scooter": 0.25,
}

# NOx emission (grams per km) per mode
NOX_FACTORS: dict[str, float] = {
    "driving_gas": 0.30,
    "driving_diesel": 0.60,
    "driving_hybrid": 0.15,
    "driving_ev": 0.02,
    "public_bus": 0.80,
    "public_subway": 0.05,
    "public_train": 0.10,
    "ride_share": 0.35,
    "taxi": 0.40,
    "biking": 0.0,
    "ebike": 0.0,
    "walking": 0.0,
    "carpool": 0.15,
    "scooter": 0.20,
}

# PM2.5 emission (grams per km)
PM25_FACTORS: dict[str, float] = {
    "driving_gas": 0.01,
    "driving_diesel": 0.03,
    "driving_hybrid": 0.005,
    "driving_ev": 0.002,
    "public_bus": 0.04,
    "public_subway": 0.003,
    "public_train": 0.005,
    "ride_share": 0.012,
    "taxi": 0.015,
    "biking": 0.0,
    "ebike": 0.0,
    "walking": 0.0,
    "carpool": 0.005,
    "scooter": 0.008,
}

# Weather time multipliers by mode
WEATHER_TIME_MULTIPLIERS: dict[str, dict[str, float]] = {
    "sunny": {m: 1.0 for m in EMISSION_FACTORS},
    "rainy": {
        "driving_gas": 1.15, "driving_diesel": 1.15, "driving_hybrid": 1.15,
        "driving_ev": 1.15, "public_bus": 1.20, "public_subway": 1.05,
        "public_train": 1.10, "ride_share": 1.20, "taxi": 1.20,
        "biking": 1.40, "ebike": 1.30, "walking": 1.50,
        "carpool": 1.15, "scooter": 1.35,
    },
    "snowy": {
        "driving_gas": 1.50, "driving_diesel": 1.50, "driving_hybrid": 1.50,
        "driving_ev": 1.50, "public_bus": 1.40, "public_subway": 1.10,
        "public_train": 1.20, "ride_share": 1.50, "taxi": 1.50,
        "biking": 2.50, "ebike": 2.00, "walking": 2.20,
        "carpool": 1.50, "scooter": 2.00,
    },
    "extreme_heat": {
        "driving_gas": 1.05, "driving_diesel": 1.05, "driving_hybrid": 1.05,
        "driving_ev": 1.05, "public_bus": 1.10, "public_subway": 1.02,
        "public_train": 1.05, "ride_share": 1.10, "taxi": 1.10,
        "biking": 1.25, "ebike": 1.15, "walking": 1.30,
        "carpool": 1.05, "scooter": 1.20,
    },
    "windy": {
        "driving_gas": 1.10, "driving_diesel": 1.10, "driving_hybrid": 1.10,
        "driving_ev": 1.10, "public_bus": 1.05, "public_subway": 1.00,
        "public_train": 1.02, "ride_share": 1.10, "taxi": 1.10,
        "biking": 1.30, "ebike": 1.20, "walking": 1.25,
        "carpool": 1.10, "scooter": 1.25,
    },
}

# Traffic time multipliers
TRAFFIC_TIME_MULTIPLIERS: dict[str, dict[str, float]] = {
    "light": {m: 1.0 for m in EMISSION_FACTORS},
    "moderate": {
        "driving_gas": 1.30, "driving_diesel": 1.30, "driving_hybrid": 1.30,
        "driving_ev": 1.30, "public_bus": 1.15, "public_subway": 1.05,
        "public_train": 1.05, "ride_share": 1.30, "taxi": 1.30,
        "biking": 1.05, "ebike": 1.05, "walking": 1.00,
        "carpool": 1.30, "scooter": 1.10,
    },
    "heavy": {
        "driving_gas": 1.80, "driving_diesel": 1.80, "driving_hybrid": 1.80,
        "driving_ev": 1.80, "public_bus": 1.30, "public_subway": 1.10,
        "public_train": 1.10, "ride_share": 1.80, "taxi": 1.80,
        "biking": 1.10, "ebike": 1.10, "walking": 1.00,
        "carpool": 1.80, "scooter": 1.15,
    },
    "gridlock": {
        "driving_gas": 2.50, "driving_diesel": 2.50, "driving_hybrid": 2.50,
        "driving_ev": 2.50, "public_bus": 1.50, "public_subway": 1.15,
        "public_train": 1.15, "ride_share": 2.50, "taxi": 2.50,
        "biking": 1.15, "ebike": 1.15, "walking": 1.00,
        "carpool": 2.50, "scooter": 1.20,
    },
}

# Health benefit per km (USD value of calories burned, health improvement)
HEALTH_BENEFIT_PER_KM: dict[str, float] = {
    "biking": 0.85,
    "ebike": 0.35,
    "walking": 0.65,
    "scooter": 0.15,
}

# Mode display labels
MODE_LABELS: dict[str, str] = {
    "driving_gas": "🚗 Gasoline Car",
    "driving_diesel": "🚗 Diesel Car",
    "driving_hybrid": "🚙 Hybrid Car",
    "driving_ev": "⚡ Electric Car",
    "public_bus": "🚌 Public Bus",
    "public_subway": "🚇 Subway",
    "public_train": "🚆 Train",
    "ride_share": "📲 Ride-share",
    "taxi": "🚕 Taxi",
    "biking": "🚲 Biking",
    "ebike": "🔋 E-Bike",
    "walking": "🚶 Walking",
    "carpool": "🤝 Carpool",
    "scooter": "🛴 Scooter",
}

# Modes that require a personal vehicle
VEHICLE_REQUIRED_MODES = {
    "driving_gas", "driving_diesel", "driving_hybrid", "driving_ev",
}

# Modes that are physically active
ACTIVE_MODES = {"biking", "walking", "ebike", "scooter"}


def _get_fuel_price(region: str, fuel_type: str) -> float:
    """Get fuel price per liter for a region and fuel type."""
    region_prices = FUEL_PRICES.get(region, FUEL_PRICES["Global"])
    return region_prices.get(fuel_type, 1.20)


def _get_electricity_price(region: str) -> float:
    """Get electricity price per kWh for a region."""
    region_prices = FUEL_PRICES.get(region, FUEL_PRICES["Global"])
    return region_prices.get("electricity_per_kwh", 0.15)


def _compute_fuel_cost(
    mode: str, distance_km: float, vehicle: VehicleInfo, region: str,
) -> float:
    """Compute fuel/electricity cost for a trip."""
    if mode in VEHICLE_REQUIRED_MODES:
        if mode == "driving_ev":
            # EV: energy consumption ~0.2 kWh/km
            kwh_per_km = 0.20
            elec_price = _get_electricity_price(region)
            return round(distance_km * kwh_per_km * elec_price, 4)
        elif mode == "driving_hybrid":
            # Hybrid: ~45 mpg effective
            mpg = 45.0
            liters_per_100km = 235.215 / mpg
            fuel_price = _get_fuel_price(region, "gasoline")
            return round(distance_km * liters_per_100km / 100 * fuel_price, 4)
        elif mode == "driving_diesel":
            mpg = vehicle.fuel_efficiency_mpg * 1.1  # diesel ~10% better
            liters_per_100km = 235.215 / mpg
            fuel_price = _get_fuel_price(region, "diesel")
            return round(distance_km * liters_per_100km / 100 * fuel_price, 4)
        else:  # driving_gas
            mpg = vehicle.fuel_efficiency_mpg
            liters_per_100km = 235.215 / mpg
            fuel_price = _get_fuel_price(region, "gasoline")
            return round(distance_km * liters_per_100km / 100 * fuel_price, 4)
    return 0.0


def _compute_maintenance_cost(mode: str, distance_km: float, vehicle: VehicleInfo) -> float:
    """Compute per-trip maintenance cost (oil, tires, wear)."""
    if mode not in VEHICLE_REQUIRED_MODES:
        return 0.0
    oil_cost_per_km = vehicle.oil_change_cost / vehicle.oil_change_interval_km
    tire_cost_per_km = vehicle.tire_replacement_cost / vehicle.tire_replacement_km
    general_wear_per_km = 0.03  # misc wear per km
    return round(distance_km * (oil_cost_per_km + tire_cost_per_km + general_wear_per_km), 4)


def _compute_insurance_daily(vehicle: VehicleInfo) -> float:
    """Compute per-trip insurance allocation."""
    return round(vehicle.annual_insurance_usd / 365 / 2, 4)  # /2 for round-trip share


def _compute_depreciation_daily(vehicle: VehicleInfo) -> float:
    """Compute per-trip depreciation."""
    return round(vehicle.annual_depreciation_usd / 365 / 2, 4)


def _compute_wear_tear_cost(mode: str, distance_km: float, vehicle: VehicleInfo) -> float:
    """Compute tire/road wear cost."""
    if mode not in VEHICLE_REQUIRED_MODES:
        return 0.0
    return round(distance_km * vehicle.tire_wear_per_km * 2.5, 4)  # $2.50 per unit wear


def _compute_charging_cost(mode: str, distance_km: float) -> float:
    """Compute charging cost for EV specifically (handled in fuel, placeholder for e-bike)."""
    if mode == "ebike":
        kwh_per_km = 0.015
        return round(distance_km * kwh_per_km * 0.15, 4)
    return 0.0


def _compute_fare_cost(mode: str, distance_km: float) -> float:
    """Compute public transit / ride-share fare."""
    fare_per_km = TRANSIT_FARES_PER_KM.get(mode, 0.0)
    if mode in ("ride_share", "taxi"):
        base_fare = 3.0 if mode == "ride_share" else 4.0
        return round(base_fare + distance_km * fare_per_km, 4)
    return round(distance_km * fare_per_km, 4)


def _compute_travel_time(
    mode: str, distance_km: float, weather: WeatherCondition, traffic: TrafficLevel,
) -> float:
    """Compute one-way travel time in minutes."""
    base_speed = AVERAGE_SPEEDS.get(mode, 30.0)
    weather_mult = WEATHER_TIME_MULTIPLIERS.get(weather.value, {}).get(mode, 1.0)
    traffic_mult = TRAFFIC_TIME_MULTIPLIERS.get(traffic.value, {}).get(mode, 1.0)

    effective_speed = base_speed / (weather_mult * traffic_mult)
    time_hours = distance_km / effective_speed if effective_speed > 0 else 999.0
    return round(time_hours * 60, 1)


def _compute_health_benefit(mode: str, distance_km: float) -> float:
    """Compute health benefit value (positive = savings)."""
    benefit_per_km = HEALTH_BENEFIT_PER_KM.get(mode, 0.0)
    return round(distance_km * benefit_per_km, 4)


def _compute_environmental_impact(
    mode: str, distance_km: float, profile: CommuteProfile,
) -> EnvironmentalImpact:
    """Compute environmental impact metrics."""
    co2_factor = EMISSION_FACTORS.get(mode, 0.1)
    nox_factor = NOX_FACTORS.get(mode, 0.1)
    pm25_factor = PM25_FACTORS.get(mode, 0.01)

    co2_per_trip = distance_km * co2_factor
    annual_trips = profile.work_days_per_week * profile.weeks_per_year * 2  # round-trip
    co2_annual = co2_per_trip * annual_trips

    # Trees needed: 1 tree absorbs ~22 kg CO2/year
    trees_needed = math.ceil(co2_annual / 22.0) if co2_annual > 0 else 0

    # Equivalence: average car emits 4.6 metric tons/year -> 12.6 kg/day
    equivalence_car_days = co2_annual / 12.6 if co2_annual > 0 else 0.0

    return EnvironmentalImpact(
        co2_kg=round(co2_per_trip, 4),
        nox_grams=round(distance_km * nox_factor, 4),
        pm25_grams=round(distance_km * pm25_factor, 4),
        co2_annual_kg=round(co2_annual, 2),
        trees_needed=trees_needed,
        equivalence_car_days=round(equivalence_car_days, 2),
    )


def _compute_time_metrics(
    mode: str, distance_km: float, weather: WeatherCondition,
    traffic: TrafficLevel, hourly_wage: float,
    profile: CommuteProfile,
) -> TimeMetrics:
    """Compute time-related metrics."""
    travel_time = _compute_travel_time(mode, distance_km, weather, traffic)
    annual_trips = profile.work_days_per_week * profile.weeks_per_year * 2
    annual_hours = (travel_time / 60) * annual_trips
    productivity_loss = (travel_time / 60) * hourly_wage

    health_minutes = 0.0
    if mode in ACTIVE_MODES:
        # Active transport: health minutes gained equals travel time
        health_minutes = travel_time
    elif mode in ("public_bus", "public_subway", "public_train"):
        # Transit: can read/relax, partial health benefit
        health_minutes = travel_time * 0.2

    annual_health_hours = (health_minutes / 60) * annual_trips

    return TimeMetrics(
        travel_time_minutes=travel_time,
        travel_time_annual_hours=round(annual_hours, 1),
        productivity_loss_usd=round(productivity_loss, 2),
        health_minutes_gained=health_minutes,
        health_annual_hours=round(annual_health_hours, 1),
    )


def _compute_cost_breakdown(
    mode: str, distance_km: float, profile: CommuteProfile,
) -> CostBreakdown:
    """Compute complete cost breakdown for a single trip."""
    vehicle = profile.vehicle
    region = profile.region

    fuel = _compute_fuel_cost(mode, distance_km, vehicle, region)
    maintenance = _compute_maintenance_cost(mode, distance_km, vehicle)
    insurance = _compute_insurance_daily(vehicle) if mode in VEHICLE_REQUIRED_MODES else 0.0
    parking = profile.parking_cost_per_day if mode in VEHICLE_REQUIRED_MODES else 0.0
    tolls = profile.toll_cost_per_trip if mode in VEHICLE_REQUIRED_MODES else 0.0
    depreciation = _compute_depreciation_daily(vehicle) if mode in VEHICLE_REQUIRED_MODES else 0.0
    charging = _compute_charging_cost(mode, distance_km)
    wear_tear = _compute_wear_tear_cost(mode, distance_km, vehicle)
    fare = _compute_fare_cost(mode, distance_km)

    travel_time = _compute_travel_time(mode, distance_km, profile.weather, profile.traffic)
    time_cost = round((travel_time / 60) * profile.hourly_wage_usd, 4)
    health_benefit = _compute_health_benefit(mode, distance_km)

    return CostBreakdown(
        fuel_cost=fuel,
        maintenance_cost=maintenance,
        insurance_daily=insurance,
        parking_cost=parking,
        toll_cost=tolls,
        depreciation_daily=depreciation,
        charging_cost=charging,
        wear_tear_cost=wear_tear,
        fare_cost=fare,
        time_cost=time_cost,
        health_benefit=health_benefit,
    )


def _assign_recommendation_tag(
    score: float, mode: str, annual_co2: float,
) -> str:
    """Assign a recommendation tag based on score and environmental impact."""
    if mode in ACTIVE_MODES:
        return "🏆 Health Champion"
    if annual_co2 < 100:
        return "🌿 Eco Leader"
    if score >= 80:
        return "✅ Great Choice"
    if score >= 60:
        return "👍 Good Option"
    if score >= 40:
        return "⚠️ Consider Alternatives"
    return "🔴 High Impact"


def _collect_warnings(
    mode: str, cost: CostBreakdown, env: EnvironmentalImpact, time_m: TimeMetrics,
) -> list[str]:
    """Collect warnings about the commute mode."""
    warnings = []
    if cost.time_cost > 20.0:
        warnings.append("⏰ High time cost — consider faster alternatives")
    if env.co2_kg > 2.0:
        warnings.append("🏭 High CO₂ per trip — a significant polluter")
    if mode in ("driving_gas", "driving_diesel") and cost.fuel_cost > 5.0:
        warnings.append("⛽ Expensive fuel costs — consider EV or hybrid")
    if mode in ACTIVE_MODES and time_m.travel_time_minutes > 60:
        warnings.append("⏰ Very long active commute — consider combining modes")
    if cost.total_financial > 15.0:
        warnings.append("💰 Very expensive commute mode")
    if env.nox_grams > 2.0:
        warnings.append("🫁 High NOx emissions — health concern")
    return warnings


def calculate_single_mode(
    mode: str, profile: CommuteProfile,
) -> ModeComparison:
    """Calculate complete cost analysis for a single transport mode."""
    distance_km = profile.distance_km

    cost = _compute_cost_breakdown(mode, distance_km, profile)
    env = _compute_environmental_impact(mode, distance_km, profile)
    time_m = _compute_time_metrics(
        mode, distance_km, profile.weather, profile.traffic,
        profile.hourly_wage_usd, profile,
    )

    annual_trips = profile.work_days_per_week * profile.weeks_per_year * 2
    annual_financial = round(cost.total_financial * annual_trips, 2)
    annual_total = round(cost.net_cost * annual_trips, 2)
    annual_co2 = env.co2_annual_kg

    # Score: 0-100, higher is better
    # Factors: cost efficiency, environmental impact, time, health
    cost_score = max(0, 100 - (cost.total_financial / 15.0) * 100)
    env_score = max(0, 100 - (env.co2_kg / 3.0) * 100)
    time_score = max(0, 100 - (time_m.travel_time_minutes / 60.0) * 100)
    health_score = min(100, (time_m.health_minutes_gained / 30.0) * 100)

    raw_score = (
        cost_score * 0.30
        + env_score * 0.30
        + time_score * 0.25
        + health_score * 0.15
    )
    score = round(max(0, min(100, raw_score)), 2)

    warnings = _collect_warnings(mode, cost, env, time_m)
    tag = _assign_recommendation_tag(score, mode, annual_co2)

    return ModeComparison(
        mode=mode,
        mode_label=MODE_LABELS.get(mode, mode),
        cost_breakdown=cost,
        environmental=env,
        time_metrics=time_m,
        annual_financial_cost=annual_financial,
        annual_total_cost=annual_total,
        annual_co2_kg=annual_co2,
        score=score,
        recommendation_tag=tag,
        warnings=warnings,
    )


def calculate_commute_comparison(profile: CommuteProfile) -> list[ModeComparison]:
    """
    Calculate and compare costs across all transport modes.

    Returns a list of ModeComparison sorted by score (best first).
    """
    comparisons = []
    for mode in TransportMode:
        try:
            comparison = calculate_single_mode(mode.value, profile)
            comparisons.append(comparison)
        except Exception as e:
            logger.warning("Failed to calculate cost for mode %s: %s", mode.value, e)

    comparisons.sort(key=lambda c: c.score, reverse=True)
    return comparisons


def calculate_savings_vs_driving(
    profile: CommuteProfile, alternative_mode: str,
) -> dict[str, Any]:
    """Calculate savings compared to baseline driving_gas."""
    baseline = calculate_single_mode("driving_gas", profile)
    alternative = calculate_single_mode(alternative_mode, profile)

    financial_saved = baseline.annual_financial_cost - alternative.annual_financial_cost
    co2_saved = baseline.annual_co2_kg - alternative.annual_co2_kg
    time_diff = (
        baseline.time_metrics.travel_time_minutes
        - alternative.time_metrics.travel_time_minutes
    )

    return {
        "baseline_mode": baseline.mode_label,
        "alternative_mode": alternative.mode_label,
        "annual_financial_saved_usd": round(max(0, financial_saved), 2),
        "annual_co2_saved_kg": round(max(0, co2_saved), 2),
        "daily_time_diff_minutes": round(time_diff, 1),
        "trees_equivalent": math.ceil(max(0, co2_saved) / 22.0),
        "equivalent_car_days_saved": round(max(0, co2_saved) / 12.6, 1),
        "baseline_annual_cost": baseline.annual_financial_cost,
        "alternative_annual_cost": alternative.annual_financial_cost,
        "percent_cost_reduction": (
            round((financial_saved / baseline.annual_financial_cost) * 100, 1)
            if baseline.annual_financial_cost > 0 else 0.0
        ),
    }


def calculate_breakeven_analysis(
    profile: CommuteProfile, target_mode: str,
    investment_usd: float, investment_item: str,
) -> dict[str, Any]:
    """
    Calculate how long it takes for a mode switch to pay for itself.

    For example: buying an e-bike for $1500 vs driving gasoline car.
    """
    baseline = calculate_single_mode("driving_gas", profile)
    target = calculate_single_mode(target_mode, profile)

    daily_saving = (
        baseline.total_financial - target.total_financial
    ) if baseline.total_financial > target.total_financial else 0.0

    work_days_per_year = profile.work_days_per_week * profile.weeks_per_year

    if daily_saving > 0:
        days_to_breakeven = math.ceil(investment_usd / daily_saving)
        years_to_breakeven = days_to_breakeven / work_days_per_year
        annual_savings_after = daily_saving * work_days_per_year
    else:
        days_to_breakeven = -1
        years_to_breakeven = -1
        annual_savings_after = 0.0

    return {
        "investment_item": investment_item,
        "investment_usd": investment_usd,
        "target_mode": MODE_LABELS.get(target_mode, target_mode),
        "daily_saving_usd": round(daily_saving, 4),
        "days_to_breakeven": days_to_breakeven,
        "years_to_breakeven": round(years_to_breakeven, 1) if years_to_breakeven > 0 else -1,
        "annual_savings_after_breakeven": round(annual_savings_after, 2),
        "five_year_net_benefit": round(
            (annual_savings_after * 5) - investment_usd, 2
        ) if annual_savings_after > 0 else -investment_usd,
    }


def generate_commute_report(profile: CommuteProfile) -> dict[str, Any]:
    """
    Generate a comprehensive commute cost report with all comparisons,
    top recommendations, and savings analysis.
    """
    comparisons = calculate_commute_comparison(profile)
    savings_analysis = []

    for comp in comparisons[1:6]:  # Top 5 alternatives to best
        savings = calculate_savings_vs_driving(profile, comp.mode)
        savings_analysis.append(savings)

    best_mode = comparisons[0] if comparisons else None
    worst_mode = comparisons[-1] if comparisons else None

    # Build category rankings
    cheapest = min(comparisons, key=lambda c: c.annual_financial_cost) if comparisons else None
    greenest = min(comparisons, key=lambda c: c.annual_co2_kg) if comparisons else None
    fastest = min(comparisons, key=lambda c: c.time_metrics.travel_time_minutes) if comparisons else None
    healthiest = max(comparisons, key=lambda c: c.time_metrics.health_minutes_gained) if comparisons else None

    annual_trips = profile.work_days_per_week * profile.weeks_per_year * 2

    return {
        "profile": {
            "distance_km": profile.distance_km,
            "work_days_per_week": profile.work_days_per_week,
            "weeks_per_year": profile.weeks_per_year,
            "weather": profile.weather.value,
            "traffic": profile.traffic.value,
            "hourly_wage": profile.hourly_wage_usd,
            "region": profile.region,
            "annual_trips": annual_trips,
        },
        "comparisons": [c.to_dict() for c in comparisons],
        "top_recommendation": best_mode.to_dict() if best_mode else None,
        "category_leaders": {
            "cheapest": cheapest.to_dict() if cheapest else None,
            "greenest": greenest.to_dict() if greenest else None,
            "fastest": fastest.to_dict() if fastest else None,
            "healthiest": healthiest.to_dict() if healthiest else None,
        },
        "savings_analysis": savings_analysis,
        "summary": {
            "modes_compared": len(comparisons),
            "best_mode": best_mode.mode_label if best_mode else "N/A",
            "best_score": best_mode.score if best_mode else 0,
            "worst_mode": worst_mode.mode_label if worst_mode else "N/A",
            "potential_annual_savings_usd": (
                round(worst_mode.annual_financial_cost - best_mode.annual_financial_cost, 2)
                if worst_mode and best_mode else 0
            ),
            "potential_annual_co2_reduction_kg": (
                round(worst_mode.annual_co2_kg - best_mode.annual_co2_kg, 2)
                if worst_mode and best_mode else 0
            ),
        },
        "generated_at": datetime.now().isoformat(),
    }


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format a currency amount for display."""
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "INR": "₹"}
    symbol = symbols.get(currency, "$")
    if amount >= 1000:
        return f"{symbol}{amount:,.0f}"
    return f"{symbol}{amount:.2f}"


def format_co2(kg: float) -> str:
    """Format CO2 amount for display."""
    if kg >= 1000:
        return f"{kg / 1000:.1f} t CO₂"
    return f"{kg:.1f} kg CO₂"


def format_time(minutes: float) -> str:
    """Format time duration for display."""
    if minutes >= 60:
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours}h {mins}m"
    return f"{minutes:.0f} min"
