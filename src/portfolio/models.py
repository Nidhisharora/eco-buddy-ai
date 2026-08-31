"""
Portfolio Data Models

Defines the core data structures for the Carbon Offset Portfolio Tracker,
including offset projects, portfolio holdings, transactions, snapshots,
risk assessments, and lifecycle metadata.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ProjectType(str, Enum):
    """Categories of carbon offset projects."""
    REFORESTATION = "reforestation"
    AFFORESTATION = "afforestation"
    RENEWABLE_ENERGY = "renewable_energy"
    METHANE_CAPTURE = "methane_capture"
    CLEAN_COOKSTOVES = "clean_cookstoves"
    DIRECT_AIR_CAPTURE = "direct_air_capture"
    OCEAN_RESTORATION = "ocean_restoration"
    SOIL_CARBON = "soil_carbon"
    INDUSTRIAL_EFFICIENCY = "industrial_efficiency"
    OTHER = "other"


class LifecycleStage(str, Enum):
    """Lifecycle stages of an offset project."""
    PLANNING = "planning"
    VALIDATION = "validation"
    REGISTRATION = "registration"
    VERIFICATION = "verification"
    ACTIVE = "active"
    SERIALIZATION = "serialization"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    EXPIRED = "expired"
    REVOKED = "revoked"


class TransactionType(str, Enum):
    """Types of offset transactions."""
    PURCHASE = "purchase"
    RETIREMENT = "retirement"
    TRANSFER = "transfer"
    GIFT = "gift"
    CANCELLATION = "cancellation"
    EXPIRY = "expiry"


class RiskLevel(str, Enum):
    """Risk classification levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class OffsetProject:
    """Represents a carbon offset project available in the marketplace."""
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    project_type: ProjectType = ProjectType.OTHER
    registry: str = ""  # e.g. Verra, Gold Standard, ACR
    registry_id: str = ""  # Original registry identifier
    country: str = ""
    region: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    methodology: str = ""
    standard: str = ""  # e.g. VCS, CDM, REDD+
    vintage_year: int = 0
    unit_price_usd: float = 0.0
    total_units: int = 0
    available_units: int = 0
    min_purchase_units: int = 1
    co_benefits: List[str] = field(default_factory=list)
    sdg_alignment: List[int] = field(default_factory=list)
    lifecycle_stage: LifecycleStage = LifecycleStage.ACTIVE
    registry_url: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["project_type"] = self.project_type.value
        d["lifecycle_stage"] = self.lifecycle_stage.value
        d["created_at"] = self.created_at.isoformat() if self.created_at else None
        d["updated_at"] = self.updated_at.isoformat() if self.updated_at else None
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OffsetProject":
        data = dict(data)
        data["project_type"] = ProjectType(data.get("project_type", "other"))
        data["lifecycle_stage"] = LifecycleStage(data.get("lifecycle_stage", "active"))
        data["co_benefits"] = data.get("co_benefits", [])
        data["sdg_alignment"] = data.get("sdg_alignment", [])
        for date_field in ("created_at", "updated_at"):
            val = data.get(date_field)
            if isinstance(val, str):
                data[date_field] = datetime.fromisoformat(val)
            elif val is None:
                data[date_field] = datetime.utcnow()
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class PortfolioHolding:
    """A single offset holding in a user's portfolio."""
    holding_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int = 0
    project_id: str = ""
    project_name: str = ""
    project_type: ProjectType = ProjectType.OTHER
    units_held: int = 0
    units_retired: int = 0
    avg_cost_per_unit: float = 0.0
    total_invested_usd: float = 0.0
    purchase_date: datetime = field(default_factory=datetime.utcnow)
    last_valuation: float = 0.0
    last_valuation_date: Optional[datetime] = None
    vintage_year: int = 0
    registry: str = ""
    is_active: bool = True
    tags: List[str] = field(default_factory=list)
    notes: str = ""

    @property
    def units_available(self) -> int:
        return max(0, self.units_held - self.units_retired)

    @property
    def cost_basis(self) -> float:
        return self.units_held * self.avg_cost_per_unit

    @property
    def unrealized_gain_usd(self) -> float:
        if self.last_valuation <= 0:
            return 0.0
        return (self.last_valuation - self.avg_cost_per_unit) * self.units_available

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["project_type"] = self.project_type.value
        d["purchase_date"] = self.purchase_date.isoformat()
        d["last_valuation_date"] = self.last_valuation_date.isoformat() if self.last_valuation_date else None
        d["units_available"] = self.units_available
        d["cost_basis"] = self.cost_basis
        d["unrealized_gain_usd"] = self.unrealized_gain_usd
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PortfolioHolding":
        data = dict(data)
        data["project_type"] = ProjectType(data.get("project_type", "other"))
        for date_field in ("purchase_date", "last_valuation_date"):
            val = data.get(date_field)
            if isinstance(val, str):
                data[date_field] = datetime.fromisoformat(val)
        data["tags"] = data.get("tags", [])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class OffsetTransaction:
    """Records a purchase, retirement, or transfer of offset credits."""
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int = 0
    project_id: str = ""
    project_name: str = ""
    transaction_type: TransactionType = TransactionType.PURCHASE
    units: int = 0
    price_per_unit: float = 0.0
    total_cost_usd: float = 0.0
    fee_usd: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: str = "completed"  # pending, completed, failed, cancelled
    reference_number: str = ""
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_with_fee(self) -> float:
        return self.total_cost_usd + self.fee_usd

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["transaction_type"] = self.transaction_type.value
        d["timestamp"] = self.timestamp.isoformat()
        d["total_with_fee"] = self.total_with_fee
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OffsetTransaction":
        data = dict(data)
        data["transaction_type"] = TransactionType(data.get("transaction_type", "purchase"))
        val = data.get("timestamp")
        if isinstance(val, str):
            data["timestamp"] = datetime.fromisoformat(val)
        data["metadata"] = data.get("metadata", {})
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class PortfolioSnapshot:
    """Point-in-time summary of a user's offset portfolio."""
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    total_units_held: int = 0
    total_units_retired: int = 0
    total_invested_usd: float = 0.0
    current_value_usd: float = 0.0
    unrealized_gain_usd: float = 0.0
    total_carbon_offset_kg: float = 0.0
    total_carbon_retired_kg: float = 0.0
    diversification_score: float = 0.0  # 0-100
    risk_score: float = 0.0  # 0-100 (lower = less risky)
    lifecycle_health: float = 0.0  # 0-100
    project_count: int = 0
    registry_breakdown: Dict[str, int] = field(default_factory=dict)
    type_breakdown: Dict[str, int] = field(default_factory=dict)
    vintage_distribution: Dict[str, int] = field(default_factory=dict)

    @property
    def roi_percent(self) -> float:
        if self.total_invested_usd <= 0:
            return 0.0
        return round(
            ((self.current_value_usd - self.total_invested_usd) / self.total_invested_usd) * 100,
            2,
        )

    @property
    def effective_cost_per_tonne(self) -> float:
        if self.total_carbon_offset_kg <= 0:
            return 0.0
        return round(
            self.total_invested_usd / (self.total_carbon_offset_kg / 1000), 2
        )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        d["roi_percent"] = self.roi_percent
        d["effective_cost_per_tonne"] = self.effective_cost_per_tonne
        return d


@dataclass
class RiskAssessment:
    """Comprehensive risk assessment for a single offset project or portfolio."""
    assessment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_id: str = ""  # project_id or 'portfolio'
    entity_type: str = "project"  # project | portfolio
    timestamp: datetime = field(default_factory=datetime.utcnow)
    overall_risk: RiskLevel = RiskLevel.MEDIUM
    overall_risk_score: float = 50.0  # 0-100
    permanence_risk: float = 50.0
    additionality_risk: float = 50.0
    leakage_risk: float = 50.0
    registry_risk: float = 50.0
    vintage_risk: float = 50.0
    geopolitical_risk: float = 50.0
    market_risk: float = 50.0
    risk_factors: List[str] = field(default_factory=list)
    mitigations: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["overall_risk"] = self.overall_risk.value
        d["timestamp"] = self.timestamp.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskAssessment":
        data = dict(data)
        data["overall_risk"] = RiskLevel(data.get("overall_risk", "medium"))
        val = data.get("timestamp")
        if isinstance(val, str):
            data["timestamp"] = datetime.fromisoformat(val)
        data["risk_factors"] = data.get("risk_factors", [])
        data["mitigations"] = data.get("mitigations", [])
        data["recommendations"] = data.get("recommendations", [])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
