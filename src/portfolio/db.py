"""
Portfolio Database Layer

SQLite-backed persistence for the Carbon Offset Portfolio Tracker.
Manages projects, holdings, transactions, snapshots, and risk assessments.
"""

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.portfolio.models import (
    OffsetProject,
    OffsetTransaction,
    PortfolioHolding,
    PortfolioSnapshot,
    ProjectType,
    RiskAssessment,
    RiskLevel,
    TransactionType,
    LifecycleStage,
)

logger = logging.getLogger(__name__)

TABLES_DDL = """
CREATE TABLE IF NOT EXISTS offset_projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    project_type TEXT NOT NULL DEFAULT 'other',
    registry TEXT DEFAULT '',
    registry_id TEXT DEFAULT '',
    country TEXT DEFAULT '',
    region TEXT DEFAULT '',
    latitude REAL DEFAULT 0.0,
    longitude REAL DEFAULT 0.0,
    methodology TEXT DEFAULT '',
    standard TEXT DEFAULT '',
    vintage_year INTEGER DEFAULT 0,
    unit_price_usd REAL DEFAULT 0.0,
    total_units INTEGER DEFAULT 0,
    available_units INTEGER DEFAULT 0,
    min_purchase_units INTEGER DEFAULT 1,
    co_benefits TEXT DEFAULT '[]',
    sdg_alignment TEXT DEFAULT '[]',
    lifecycle_stage TEXT DEFAULT 'active',
    registry_url TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS portfolio_holdings (
    holding_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    project_id TEXT NOT NULL,
    project_name TEXT DEFAULT '',
    project_type TEXT NOT NULL DEFAULT 'other',
    units_held INTEGER DEFAULT 0,
    units_retired INTEGER DEFAULT 0,
    avg_cost_per_unit REAL DEFAULT 0.0,
    total_invested_usd REAL DEFAULT 0.0,
    purchase_date TEXT NOT NULL,
    last_valuation REAL DEFAULT 0.0,
    last_valuation_date TEXT,
    vintage_year INTEGER DEFAULT 0,
    registry TEXT DEFAULT '',
    is_active INTEGER DEFAULT 1,
    tags TEXT DEFAULT '[]',
    notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS offset_transactions (
    transaction_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    project_id TEXT NOT NULL,
    project_name TEXT DEFAULT '',
    transaction_type TEXT NOT NULL DEFAULT 'purchase',
    units INTEGER DEFAULT 0,
    price_per_unit REAL DEFAULT 0.0,
    total_cost_usd REAL DEFAULT 0.0,
    fee_usd REAL DEFAULT 0.0,
    timestamp TEXT NOT NULL,
    status TEXT DEFAULT 'completed',
    reference_number TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    metadata TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    total_units_held INTEGER DEFAULT 0,
    total_units_retired INTEGER DEFAULT 0,
    total_invested_usd REAL DEFAULT 0.0,
    current_value_usd REAL DEFAULT 0.0,
    unrealized_gain_usd REAL DEFAULT 0.0,
    total_carbon_offset_kg REAL DEFAULT 0.0,
    total_carbon_retired_kg REAL DEFAULT 0.0,
    diversification_score REAL DEFAULT 0.0,
    risk_score REAL DEFAULT 0.0,
    lifecycle_health REAL DEFAULT 0.0,
    project_count INTEGER DEFAULT 0,
    registry_breakdown TEXT DEFAULT '{}',
    type_breakdown TEXT DEFAULT '{}',
    vintage_distribution TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS risk_assessments (
    assessment_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    entity_type TEXT NOT NULL DEFAULT 'project',
    timestamp TEXT NOT NULL,
    overall_risk TEXT NOT NULL DEFAULT 'medium',
    overall_risk_score REAL DEFAULT 50.0,
    permanence_risk REAL DEFAULT 50.0,
    additionality_risk REAL DEFAULT 50.0,
    leakage_risk REAL DEFAULT 50.0,
    registry_risk REAL DEFAULT 50.0,
    vintage_risk REAL DEFAULT 50.0,
    geopolitical_risk REAL DEFAULT 50.0,
    market_risk REAL DEFAULT 50.0,
    risk_factors TEXT DEFAULT '[]',
    mitigations TEXT DEFAULT '[]',
    recommendations TEXT DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_holdings_user ON portfolio_holdings(user_id);
CREATE INDEX IF NOT EXISTS idx_holdings_project ON portfolio_holdings(project_id);
CREATE INDEX IF NOT EXISTS idx_tx_user ON offset_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_tx_project ON offset_transactions(project_id);
CREATE INDEX IF NOT EXISTS idx_tx_type ON offset_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_snapshots_user ON portfolio_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_risk_entity ON risk_assessments(entity_id, entity_type);
"""


class PortfolioDB:
    """SQLite interface for the offset portfolio subsystem."""

    def __init__(self, db_path: str = "ecobuddy.db"):
        self.db_path = db_path
        self._init_tables()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        try:
            conn = self._get_conn()
            conn.executescript(TABLES_DDL)
            conn.commit()
        except sqlite3.Error as exc:
            logger.error("Failed to init portfolio tables: %s", exc)
        finally:
            conn.close()

    # ── Projects ──────────────────────────────────────────────────────────

    def upsert_project(self, project: OffsetProject) -> bool:
        try:
            conn = self._get_conn()
            conn.execute(
                """
                INSERT OR REPLACE INTO offset_projects
                (project_id, name, description, project_type, registry, registry_id,
                 country, region, latitude, longitude, methodology, standard,
                 vintage_year, unit_price_usd, total_units, available_units,
                 min_purchase_units, co_benefits, sdg_alignment, lifecycle_stage,
                 registry_url, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    project.project_id,
                    project.name,
                    project.description,
                    project.project_type.value,
                    project.registry,
                    project.registry_id,
                    project.country,
                    project.region,
                    project.latitude,
                    project.longitude,
                    project.methodology,
                    project.standard,
                    project.vintage_year,
                    project.unit_price_usd,
                    project.total_units,
                    project.available_units,
                    project.min_purchase_units,
                    json.dumps(project.co_benefits),
                    json.dumps(project.sdg_alignment),
                    project.lifecycle_stage.value,
                    project.registry_url,
                    project.created_at.isoformat(),
                    project.updated_at.isoformat(),
                ),
            )
            conn.commit()
            return True
        except sqlite3.Error as exc:
            logger.error("upsert_project failed: %s", exc)
            return False
        finally:
            conn.close()

    def get_project(self, project_id: str) -> Optional[OffsetProject]:
        try:
            conn = self._get_conn()
            row = conn.execute(
                "SELECT * FROM offset_projects WHERE project_id = ?",
                (project_id,),
            ).fetchone()
            if not row:
                return None
            return self._row_to_project(row)
        except sqlite3.Error as exc:
            logger.error("get_project failed: %s", exc)
            return None
        finally:
            conn.close()

    def list_projects(
        self,
        project_type: Optional[str] = None,
        registry: Optional[str] = None,
        country: Optional[str] = None,
        limit: int = 50,
    ) -> List[OffsetProject]:
        try:
            conn = self._get_conn()
            query = "SELECT * FROM offset_projects WHERE 1=1"
            params: list = []
            if project_type:
                query += " AND project_type = ?"
                params.append(project_type)
            if registry:
                query += " AND registry = ?"
                params.append(registry)
            if country:
                query += " AND country = ?"
                params.append(country)
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_project(r) for r in rows]
        except sqlite3.Error as exc:
            logger.error("list_projects failed: %s", exc)
            return []
        finally:
            conn.close()

    # ── Holdings ──────────────────────────────────────────────────────────

    def add_holding(self, holding: PortfolioHolding) -> bool:
        try:
            conn = self._get_conn()
            conn.execute(
                """
                INSERT INTO portfolio_holdings
                (holding_id, user_id, project_id, project_name, project_type,
                 units_held, units_retired, avg_cost_per_unit, total_invested_usd,
                 purchase_date, last_valuation, last_valuation_date, vintage_year,
                 registry, is_active, tags, notes)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    holding.holding_id,
                    holding.user_id,
                    holding.project_id,
                    holding.project_name,
                    holding.project_type.value,
                    holding.units_held,
                    holding.units_retired,
                    holding.avg_cost_per_unit,
                    holding.total_invested_usd,
                    holding.purchase_date.isoformat(),
                    holding.last_valuation,
                    holding.last_valuation_date.isoformat() if holding.last_valuation_date else None,
                    holding.vintage_year,
                    holding.registry,
                    1 if holding.is_active else 0,
                    json.dumps(holding.tags),
                    holding.notes,
                ),
            )
            conn.commit()
            return True
        except sqlite3.Error as exc:
            logger.error("add_holding failed: %s", exc)
            return False
        finally:
            conn.close()

    def get_user_holdings(
        self, user_id: int, active_only: bool = True
    ) -> List[PortfolioHolding]:
        try:
            conn = self._get_conn()
            query = "SELECT * FROM portfolio_holdings WHERE user_id = ?"
            params: list = [user_id]
            if active_only:
                query += " AND is_active = 1"
            query += " ORDER BY purchase_date DESC"
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_holding(r) for r in rows]
        except sqlite3.Error as exc:
            logger.error("get_user_holdings failed: %s", exc)
            return []
        finally:
            conn.close()

    def update_holding_retirement(
        self, holding_id: str, units_retired: int
    ) -> bool:
        try:
            conn = self._get_conn()
            conn.execute(
                "UPDATE portfolio_holdings SET units_retired = ? WHERE holding_id = ?",
                (units_retired, holding_id),
            )
            conn.commit()
            return True
        except sqlite3.Error as exc:
            logger.error("update_holding_retirement failed: %s", exc)
            return False
        finally:
            conn.close()

    def update_holding_valuation(
        self, holding_id: str, valuation: float
    ) -> bool:
        try:
            conn = self._get_conn()
            now = datetime.utcnow().isoformat()
            conn.execute(
                "UPDATE portfolio_holdings SET last_valuation = ?, last_valuation_date = ? WHERE holding_id = ?",
                (valuation, now, holding_id),
            )
            conn.commit()
            return True
        except sqlite3.Error as exc:
            logger.error("update_holding_valuation failed: %s", exc)
            return False
        finally:
            conn.close()

    # ── Transactions ──────────────────────────────────────────────────────

    def add_transaction(self, tx: OffsetTransaction) -> bool:
        try:
            conn = self._get_conn()
            conn.execute(
                """
                INSERT INTO offset_transactions
                (transaction_id, user_id, project_id, project_name,
                 transaction_type, units, price_per_unit, total_cost_usd,
                 fee_usd, timestamp, status, reference_number, notes, metadata)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    tx.transaction_id,
                    tx.user_id,
                    tx.project_id,
                    tx.project_name,
                    tx.transaction_type.value,
                    tx.units,
                    tx.price_per_unit,
                    tx.total_cost_usd,
                    tx.fee_usd,
                    tx.timestamp.isoformat(),
                    tx.status,
                    tx.reference_number,
                    tx.notes,
                    json.dumps(tx.metadata),
                ),
            )
            conn.commit()
            return True
        except sqlite3.Error as exc:
            logger.error("add_transaction failed: %s", exc)
            return False
        finally:
            conn.close()

    def get_user_transactions(
        self,
        user_id: int,
        tx_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[OffsetTransaction]:
        try:
            conn = self._get_conn()
            query = "SELECT * FROM offset_transactions WHERE user_id = ?"
            params: list = [user_id]
            if tx_type:
                query += " AND transaction_type = ?"
                params.append(tx_type)
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_transaction(r) for r in rows]
        except sqlite3.Error as exc:
            logger.error("get_user_transactions failed: %s", exc)
            return []
        finally:
            conn.close()

    def get_total_invested(self, user_id: int) -> float:
        try:
            conn = self._get_conn()
            row = conn.execute(
                """
                SELECT COALESCE(SUM(total_cost_usd), 0) AS total
                FROM offset_transactions
                WHERE user_id = ? AND transaction_type = 'purchase' AND status = 'completed'
                """,
                (user_id,),
            ).fetchone()
            return float(row["total"]) if row else 0.0
        except sqlite3.Error as exc:
            logger.error("get_total_invested failed: %s", exc)
            return 0.0
        finally:
            conn.close()

    # ── Snapshots ─────────────────────────────────────────────────────────

    def save_snapshot(self, snapshot: PortfolioSnapshot) -> bool:
        try:
            conn = self._get_conn()
            conn.execute(
                """
                INSERT INTO portfolio_snapshots
                (snapshot_id, user_id, timestamp, total_units_held, total_units_retired,
                 total_invested_usd, current_value_usd, unrealized_gain_usd,
                 total_carbon_offset_kg, total_carbon_retired_kg,
                 diversification_score, risk_score, lifecycle_health,
                 project_count, registry_breakdown, type_breakdown, vintage_distribution)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    snapshot.snapshot_id,
                    snapshot.user_id,
                    snapshot.timestamp.isoformat(),
                    snapshot.total_units_held,
                    snapshot.total_units_retired,
                    snapshot.total_invested_usd,
                    snapshot.current_value_usd,
                    snapshot.unrealized_gain_usd,
                    snapshot.total_carbon_offset_kg,
                    snapshot.total_carbon_retired_kg,
                    snapshot.diversification_score,
                    snapshot.risk_score,
                    snapshot.lifecycle_health,
                    snapshot.project_count,
                    json.dumps(snapshot.registry_breakdown),
                    json.dumps(snapshot.type_breakdown),
                    json.dumps(snapshot.vintage_distribution),
                ),
            )
            conn.commit()
            return True
        except sqlite3.Error as exc:
            logger.error("save_snapshot failed: %s", exc)
            return False
        finally:
            conn.close()

    def get_snapshot_history(
        self, user_id: int, limit: int = 52
    ) -> List[PortfolioSnapshot]:
        try:
            conn = self._get_conn()
            rows = conn.execute(
                """
                SELECT * FROM portfolio_snapshots
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
            return [self._row_to_snapshot(r) for r in rows]
        except sqlite3.Error as exc:
            logger.error("get_snapshot_history failed: %s", exc)
            return []
        finally:
            conn.close()

    # ── Risk Assessments ──────────────────────────────────────────────────

    def save_risk_assessment(self, assessment: RiskAssessment) -> bool:
        try:
            conn = self._get_conn()
            conn.execute(
                """
                INSERT INTO risk_assessments
                (assessment_id, entity_id, entity_type, timestamp,
                 overall_risk, overall_risk_score, permanence_risk,
                 additionality_risk, leakage_risk, registry_risk,
                 vintage_risk, geopolitical_risk, market_risk,
                 risk_factors, mitigations, recommendations)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    assessment.assessment_id,
                    assessment.entity_id,
                    assessment.entity_type,
                    assessment.timestamp.isoformat(),
                    assessment.overall_risk.value,
                    assessment.overall_risk_score,
                    assessment.permanence_risk,
                    assessment.additionality_risk,
                    assessment.leakage_risk,
                    assessment.registry_risk,
                    assessment.vintage_risk,
                    assessment.geopolitical_risk,
                    assessment.market_risk,
                    json.dumps(assessment.risk_factors),
                    json.dumps(assessment.mitigations),
                    json.dumps(assessment.recommendations),
                ),
            )
            conn.commit()
            return True
        except sqlite3.Error as exc:
            logger.error("save_risk_assessment failed: %s", exc)
            return False
        finally:
            conn.close()

    def get_risk_assessments(
        self, entity_id: str, entity_type: str = "project"
    ) -> List[RiskAssessment]:
        try:
            conn = self._get_conn()
            rows = conn.execute(
                """
                SELECT * FROM risk_assessments
                WHERE entity_id = ? AND entity_type = ?
                ORDER BY timestamp DESC
                """,
                (entity_id, entity_type),
            ).fetchall()
            return [self._row_to_risk(r) for r in rows]
        except sqlite3.Error as exc:
            logger.error("get_risk_assessments failed: %s", exc)
            return []
        finally:
            conn.close()

    # ── Row → Model helpers ───────────────────────────────────────────────

    @staticmethod
    def _row_to_project(row: sqlite3.Row) -> OffsetProject:
        d = dict(row)
        return OffsetProject(
            project_id=d["project_id"],
            name=d["name"],
            description=d["description"],
            project_type=ProjectType(d["project_type"]),
            registry=d["registry"],
            registry_id=d["registry_id"],
            country=d["country"],
            region=d["region"],
            latitude=d["latitude"],
            longitude=d["longitude"],
            methodology=d["methodology"],
            standard=d["standard"],
            vintage_year=d["vintage_year"],
            unit_price_usd=d["unit_price_usd"],
            total_units=d["total_units"],
            available_units=d["available_units"],
            min_purchase_units=d["min_purchase_units"],
            co_benefits=json.loads(d["co_benefits"]) if d["co_benefits"] else [],
            sdg_alignment=json.loads(d["sdg_alignment"]) if d["sdg_alignment"] else [],
            lifecycle_stage=LifecycleStage(d["lifecycle_stage"]),
            registry_url=d["registry_url"],
            created_at=datetime.fromisoformat(d["created_at"]),
            updated_at=datetime.fromisoformat(d["updated_at"]),
        )

    @staticmethod
    def _row_to_holding(row: sqlite3.Row) -> PortfolioHolding:
        d = dict(row)
        return PortfolioHolding(
            holding_id=d["holding_id"],
            user_id=d["user_id"],
            project_id=d["project_id"],
            project_name=d["project_name"],
            project_type=ProjectType(d["project_type"]),
            units_held=d["units_held"],
            units_retired=d["units_retired"],
            avg_cost_per_unit=d["avg_cost_per_unit"],
            total_invested_usd=d["total_invested_usd"],
            purchase_date=datetime.fromisoformat(d["purchase_date"]),
            last_valuation=d["last_valuation"],
            last_valuation_date=datetime.fromisoformat(d["last_valuation_date"]) if d["last_valuation_date"] else None,
            vintage_year=d["vintage_year"],
            registry=d["registry"],
            is_active=bool(d["is_active"]),
            tags=json.loads(d["tags"]) if d["tags"] else [],
            notes=d["notes"],
        )

    @staticmethod
    def _row_to_transaction(row: sqlite3.Row) -> OffsetTransaction:
        d = dict(row)
        return OffsetTransaction(
            transaction_id=d["transaction_id"],
            user_id=d["user_id"],
            project_id=d["project_id"],
            project_name=d["project_name"],
            transaction_type=TransactionType(d["transaction_type"]),
            units=d["units"],
            price_per_unit=d["price_per_unit"],
            total_cost_usd=d["total_cost_usd"],
            fee_usd=d["fee_usd"],
            timestamp=datetime.fromisoformat(d["timestamp"]),
            status=d["status"],
            reference_number=d["reference_number"],
            notes=d["notes"],
            metadata=json.loads(d["metadata"]) if d["metadata"] else {},
        )

    @staticmethod
    def _row_to_snapshot(row: sqlite3.Row) -> PortfolioSnapshot:
        d = dict(row)
        return PortfolioSnapshot(
            snapshot_id=d["snapshot_id"],
            user_id=d["user_id"],
            timestamp=datetime.fromisoformat(d["timestamp"]),
            total_units_held=d["total_units_held"],
            total_units_retired=d["total_units_retired"],
            total_invested_usd=d["total_invested_usd"],
            current_value_usd=d["current_value_usd"],
            unrealized_gain_usd=d["unrealized_gain_usd"],
            total_carbon_offset_kg=d["total_carbon_offset_kg"],
            total_carbon_retired_kg=d["total_carbon_retired_kg"],
            diversification_score=d["diversification_score"],
            risk_score=d["risk_score"],
            lifecycle_health=d["lifecycle_health"],
            project_count=d["project_count"],
            registry_breakdown=json.loads(d["registry_breakdown"]) if d["registry_breakdown"] else {},
            type_breakdown=json.loads(d["type_breakdown"]) if d["type_breakdown"] else {},
            vintage_distribution=json.loads(d["vintage_distribution"]) if d["vintage_distribution"] else {},
        )

    @staticmethod
    def _row_to_risk(row: sqlite3.Row) -> RiskAssessment:
        d = dict(row)
        return RiskAssessment(
            assessment_id=d["assessment_id"],
            entity_id=d["entity_id"],
            entity_type=d["entity_type"],
            timestamp=datetime.fromisoformat(d["timestamp"]),
            overall_risk=RiskLevel(d["overall_risk"]),
            overall_risk_score=d["overall_risk_score"],
            permanence_risk=d["permanence_risk"],
            additionality_risk=d["additionality_risk"],
            leakage_risk=d["leakage_risk"],
            registry_risk=d["registry_risk"],
            vintage_risk=d["vintage_risk"],
            geopolitical_risk=d["geopolitical_risk"],
            market_risk=d["market_risk"],
            risk_factors=json.loads(d["risk_factors"]) if d["risk_factors"] else [],
            mitigations=json.loads(d["mitigations"]) if d["mitigations"] else [],
            recommendations=json.loads(d["recommendations"]) if d["recommendations"] else [],
        )
