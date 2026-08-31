"""Environmental Metric Normalization for EcoBuddy AI.

Problem this solves
--------------------
EcoBuddy AI handles multiple environmental domains (carbon, water, energy,
food, transportation, waste) and these modules can represent measurements
using different units, periods, precision, and source formats. Directly
combining them makes downstream analytics difficult to maintain and prone
to bugs.

Solution
--------
Define a canonical metric representation that all domain modules convert
to before being consumed by analytics, goals, reports, or recommendations.

The canonical representation includes:
- Metric type (carbon_kg_co2e, water_liters, energy_kwh, etc.)
- Value in canonical unit
- Original value and unit (for audit trail)
- Measurement period (e.g., "daily", "weekly", "yearly")
- Source (which domain/module generated this)
- Precision (significant figures or decimal places)
- Conversion version (for reproducibility if conversion factors change)
- Timestamp (when measurement was taken)

This ensures:
- All analytics consumers see consistent data
- Conversions are versioned and reproducible
- Original data is never lost
- New environmental metrics can be added without changing consumers
- Invalid units are rejected safely
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple
import threading

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Canonical environmental metric types."""
    # Carbon & Greenhouse Gases (kg CO2e)
    CARBON_FOOTPRINT_KG_CO2E = "carbon_footprint_kg_co2e"
    CARBON_SEQUESTERED_KG_CO2E = "carbon_sequestered_kg_co2e"
    
    # Water (liters)
    WATER_CONSUMPTION_LITERS = "water_consumption_liters"
    WATER_SAVED_LITERS = "water_saved_liters"
    
    # Energy (kWh)
    ENERGY_CONSUMPTION_KWH = "energy_consumption_kwh"
    ENERGY_PRODUCED_KWH = "energy_produced_kwh"
    ENERGY_SAVED_KWH = "energy_saved_kwh"
    
    # Food & Diet (kg)
    FOOD_WASTE_KG = "food_waste_kg"
    FOOD_CONSUMED_KG = "food_consumed_kg"
    
    # Waste (kg)
    WASTE_GENERATED_KG = "waste_generated_kg"
    WASTE_RECYCLED_KG = "waste_recycled_kg"
    WASTE_COMPOSTED_KG = "waste_composted_kg"
    
    # Transportation (km)
    DISTANCE_TRAVELED_KM = "distance_traveled_km"
    DISTANCE_BY_CAR_KM = "distance_by_car_km"
    DISTANCE_BY_PUBLIC_TRANSPORT_KM = "distance_by_public_transport_km"


class MeasurementPeriod(str, Enum):
    """Time periods over which measurements are taken."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    INSTANTANEOUS = "instantaneous"  # Single point in time


class MetricSource(str, Enum):
    """Which domain/module generated the metric."""
    CARBON = "carbon"
    WATER = "water"
    ENERGY = "energy"
    FOOD = "food"
    WASTE = "waste"
    TRANSPORTATION = "transportation"
    USER_INPUT = "user_input"
    CALCULATED = "calculated"
    IMPORTED = "imported"


@dataclass(frozen=True)
class CanonicalMetric:
    """Canonical representation of an environmental measurement.
    
    Frozen to ensure immutability - metrics should never be mutated
    after creation. If a value changes, create a new metric.
    """
    metric_type: MetricType
    value: float  # Value in canonical unit
    unit: str  # Canonical unit (e.g., "kg CO2e", "liters", "kWh")
    original_value: float  # Source value before conversion
    original_unit: str  # Source unit name
    period: MeasurementPeriod
    source: MetricSource
    precision: int = 2  # Decimal places for rounding
    conversion_version: str = "1.0"  # Version of conversion factors used
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_type": self.metric_type.value,
            "value": round(self.value, self.precision),
            "unit": self.unit,
            "original_value": self.original_value,
            "original_unit": self.original_unit,
            "period": self.period.value,
            "source": self.source.value,
            "precision": self.precision,
            "conversion_version": self.conversion_version,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CanonicalMetric:
        return cls(
            metric_type=MetricType(data["metric_type"]),
            value=data["value"],
            unit=data["unit"],
            original_value=data["original_value"],
            original_unit=data["original_unit"],
            period=MeasurementPeriod(data["period"]),
            source=MetricSource(data["source"]),
            precision=data.get("precision", 2),
            conversion_version=data.get("conversion_version", "1.0"),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            metadata=data.get("metadata", {}),
        )


# Conversion factors: from unit -> to canonical unit
CONVERSION_FACTORS_V1_0 = {
    # Carbon conversions to kg CO2e
    "carbon_kg_co2e": 1.0,
    "carbon_g_co2e": 0.001,
    "carbon_tonnes_co2e": 1000.0,
    "carbon_mtco2e": 1_000_000.0,
    
    # Water conversions to liters
    "water_liters": 1.0,
    "water_ml": 0.001,
    "water_gallons": 3.78541,
    "water_m3": 1000.0,
    
    # Energy conversions to kWh
    "energy_kwh": 1.0,
    "energy_mwh": 1000.0,
    "energy_j": 0.000000278,  # 1 Joule = 0.000000278 kWh
    "energy_mj": 0.000278,
    "energy_kj": 0.000000278,
    "energy_wh": 0.001,
    
    # Distance conversions to km
    "distance_km": 1.0,
    "distance_m": 0.001,
    "distance_miles": 1.60934,
    
    # Weight conversions to kg
    "weight_kg": 1.0,
    "weight_g": 0.001,
    "weight_tonnes": 1000.0,
    "weight_lbs": 0.453592,
}

CONVERSION_VERSIONS = {
    "1.0": CONVERSION_FACTORS_V1_0,
}


class UnitConversionError(Exception):
    """Raised when a unit conversion cannot be performed."""
    pass


class MetricNormalizer:
    """Normalizes environmental metrics from various sources."""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._custom_conversions: Dict[str, float] = {}
    
    def normalize(
        self,
        value: float,
        source_unit: str,
        metric_type: MetricType,
        period: MeasurementPeriod,
        source: MetricSource,
        conversion_version: str = "1.0",
        precision: int = 2,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CanonicalMetric:
        """Convert a source measurement into canonical form.
        
        Args:
            value: The measured value
            source_unit: The unit it was measured in
            metric_type: What type of metric this is
            period: The measurement period
            source: Which domain produced this
            conversion_version: Version of conversion factors to use
            precision: Decimal places for rounding
            metadata: Optional additional data
        
        Returns:
            CanonicalMetric: The normalized measurement
        
        Raises:
            UnitConversionError: If unit is invalid or unsupported
        """
        if conversion_version not in CONVERSION_VERSIONS:
            raise UnitConversionError(
                f"Unknown conversion version {conversion_version!r}. "
                f"Available: {list(CONVERSION_VERSIONS.keys())}"
            )
        
        conversions = CONVERSION_VERSIONS[conversion_version]
        
        if source_unit not in conversions:
            available = sorted(conversions.keys())
            raise UnitConversionError(
                f"Unknown unit {source_unit!r} in version {conversion_version}. "
                f"Available units: {available}"
            )
        
        # Get canonical unit based on metric type
        canonical_unit = self._get_canonical_unit(metric_type)
        conversion_factor = conversions[source_unit]
        canonical_value = value * conversion_factor
        
        return CanonicalMetric(
            metric_type=metric_type,
            value=canonical_value,
            unit=canonical_unit,
            original_value=value,
            original_unit=source_unit,
            period=period,
            source=source,
            precision=precision,
            conversion_version=conversion_version,
            metadata=metadata or {},
        )
    
    def _get_canonical_unit(self, metric_type: MetricType) -> str:
        """Get the canonical unit for a metric type."""
        unit_map = {
            # Carbon
            MetricType.CARBON_FOOTPRINT_KG_CO2E: "kg CO2e",
            MetricType.CARBON_SEQUESTERED_KG_CO2E: "kg CO2e",
            
            # Water
            MetricType.WATER_CONSUMPTION_LITERS: "liters",
            MetricType.WATER_SAVED_LITERS: "liters",
            
            # Energy
            MetricType.ENERGY_CONSUMPTION_KWH: "kWh",
            MetricType.ENERGY_PRODUCED_KWH: "kWh",
            MetricType.ENERGY_SAVED_KWH: "kWh",
            
            # Food & Diet
            MetricType.FOOD_WASTE_KG: "kg",
            MetricType.FOOD_CONSUMED_KG: "kg",
            
            # Waste
            MetricType.WASTE_GENERATED_KG: "kg",
            MetricType.WASTE_RECYCLED_KG: "kg",
            MetricType.WASTE_COMPOSTED_KG: "kg",
            
            # Transportation
            MetricType.DISTANCE_TRAVELED_KM: "km",
            MetricType.DISTANCE_BY_CAR_KM: "km",
            MetricType.DISTANCE_BY_PUBLIC_TRANSPORT_KM: "km",
        }
        return unit_map.get(metric_type, "unknown")
    
    def register_custom_conversion(
        self,
        source_unit: str,
        conversion_factor: float,
        conversion_version: str = "1.0",
    ) -> None:
        """Register a custom conversion factor (for testing or extensions).
        
        Args:
            source_unit: The source unit name
            conversion_factor: Multiply source value by this to get canonical
            conversion_version: Version to add this conversion to
        """
        with self._lock:
            if conversion_version not in CONVERSION_VERSIONS:
                raise ValueError(f"Unknown conversion version {conversion_version}")
            
            CONVERSION_VERSIONS[conversion_version][source_unit] = conversion_factor
            logger.debug(f"Registered custom conversion: {source_unit} -> {conversion_factor}")
    
    def validate_metric(self, metric: CanonicalMetric) -> Tuple[bool, Optional[str]]:
        """Validate a canonical metric.
        
        Args:
            metric: The metric to validate
        
        Returns:
            (is_valid, error_message)
        """
        if metric.value < 0:
            return False, f"Metric value cannot be negative: {metric.value}"
        
        if metric.original_value < 0:
            return False, f"Original value cannot be negative: {metric.original_value}"
        
        if metric.precision < 0 or metric.precision > 10:
            return False, f"Precision must be between 0 and 10: {metric.precision}"
        
        if not isinstance(metric.value, (int, float)):
            return False, f"Value must be numeric: {metric.value}"
        
        return True, None


# Global normalizer instance
_normalizer: Optional[MetricNormalizer] = None
_normalizer_lock = threading.Lock()


def get_metric_normalizer() -> MetricNormalizer:
    """Get or create the global metric normalizer."""
    global _normalizer
    with _normalizer_lock:
        if _normalizer is None:
            _normalizer = MetricNormalizer()
        return _normalizer


def normalize_carbon_metric(
    value: float,
    source_unit: str,
    period: MeasurementPeriod,
    metadata: Optional[Dict[str, Any]] = None,
) -> CanonicalMetric:
    """Convenience function to normalize a carbon metric."""
    normalizer = get_metric_normalizer()
    return normalizer.normalize(
        value=value,
        source_unit=source_unit,
        metric_type=MetricType.CARBON_FOOTPRINT_KG_CO2E,
        period=period,
        source=MetricSource.CARBON,
        metadata=metadata,
    )


def normalize_water_metric(
    value: float,
    source_unit: str,
    period: MeasurementPeriod,
    metadata: Optional[Dict[str, Any]] = None,
) -> CanonicalMetric:
    """Convenience function to normalize a water metric."""
    normalizer = get_metric_normalizer()
    return normalizer.normalize(
        value=value,
        source_unit=source_unit,
        metric_type=MetricType.WATER_CONSUMPTION_LITERS,
        period=period,
        source=MetricSource.WATER,
        metadata=metadata,
    )


def normalize_energy_metric(
    value: float,
    source_unit: str,
    period: MeasurementPeriod,
    metadata: Optional[Dict[str, Any]] = None,
) -> CanonicalMetric:
    """Convenience function to normalize an energy metric."""
    normalizer = get_metric_normalizer()
    return normalizer.normalize(
        value=value,
        source_unit=source_unit,
        metric_type=MetricType.ENERGY_CONSUMPTION_KWH,
        period=period,
        source=MetricSource.ENERGY,
        metadata=metadata,
    )