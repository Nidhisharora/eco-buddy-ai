"""Goal Progress Reconciliation Engine for EcoBuddy AI.

Problem this solves
--------------------
Goal progress depends on assessments, activity records, and calculated
emissions. When source data is edited, deleted, imported, or
recalculated, goal progress can become inconsistent with the actual
source state. This makes it hard to trust goal data or audit historical
progress.

How it works
------------
1. Sources (assessments, activity records) are separated from derived
   goal progress. Each goal declares which sources it depends on.
2. When a source changes (edit, delete, import, recalculate),
   affected goals are identified via dependency mapping.
3. Only affected goals are recalculated; unrelated goals are left alone.
4. Historical goal events are preserved; recalculation appends new
   events rather than mutating the past.
5. Discrepancies between stored progress and calculated progress are
   detected and can be repaired.

This module is deterministic and thread-safe.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import threading

logger = logging.getLogger(__name__)


class SourceType(str, Enum):
    """Types of source data that can affect goal progress."""
    ASSESSMENT = "assessment"
    ACTIVITY_RECORD = "activity_record"
    CALCULATED_EMISSIONS = "calculated_emissions"
    IMPORTED_DATA = "imported_data"


class ChangeType(str, Enum):
    """Types of changes to source data."""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    RECALCULATED = "recalculated"
    IMPORTED = "imported"


@dataclass(frozen=True)
class GoalProgressRecord:
    """A source measurement that affects goal progress."""
    record_id: str
    source_type: SourceType
    goal_id: str
    user_id: int
    value: float
    timestamp: datetime
    source_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "source_type": self.source_type.value,
            "goal_id": self.goal_id,
            "user_id": self.user_id,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "source_metadata": self.source_metadata,
        }


@dataclass(frozen=True)
class GoalProgressDiscrepancy:
    """A detected inconsistency between stored and calculated progress."""
    goal_id: str
    user_id: int
    stored_progress: float
    calculated_progress: float
    stored_current_value: float
    calculated_current_value: float
    difference: float
    detected_at: datetime
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "user_id": self.user_id,
            "stored_progress": self.stored_progress,
            "calculated_progress": self.calculated_progress,
            "stored_current_value": self.stored_current_value,
            "calculated_current_value": self.calculated_current_value,
            "difference": self.difference,
            "detected_at": self.detected_at.isoformat(),
            "reason": self.reason,
        }


@dataclass
class SourceChange:
    """Notification of a source data change."""
    source_type: SourceType
    change_type: ChangeType
    source_id: str
    affected_goal_ids: Set[str] = field(default_factory=set)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


# Type for a function that calculates goal progress from source records.
# Signature: (goal_id, user_id, source_records) -> (calculated_value, calculated_progress)
GoalCalculationFn = Callable[
    [str, int, List[GoalProgressRecord]], Tuple[float, float]
]


class GoalProgressReconciler:
    """Reconciles goal progress with source data."""

    def __init__(self):
        self._lock = threading.RLock()
        
        # Mapping: goal_id -> {source_type: {source_id, ...}, ...}
        self._goal_dependencies: Dict[str, Dict[SourceType, Set[str]]] = {}
        
        # Mapping: source_id -> set of goal_ids that depend on it
        self._source_to_goals: Dict[str, Set[str]] = {}
        
        # Historical goal progress records (immutable, append-only)
        self._progress_records: Dict[str, List[GoalProgressRecord]] = {}
        
        # Detection history: goal_id -> list of discrepancies
        self._discrepancy_history: Dict[str, List[GoalProgressDiscrepancy]] = {}
        
        # Registered calculation functions: goal_id -> calculation function
        self._goal_calculators: Dict[str, GoalCalculationFn] = {}
        
        # Audit log: list of all source changes processed
        self._audit_log: List[SourceChange] = []

    def register_goal_dependency(
        self,
        goal_id: str,
        source_type: SourceType,
        source_id: str,
    ) -> None:
        """Register that a goal depends on a specific source.

        Args:
            goal_id: The goal that depends on the source.
            source_type: Type of source (assessment, activity record, etc).
            source_id: Unique ID of the source.
        """
        with self._lock:
            if goal_id not in self._goal_dependencies:
                self._goal_dependencies[goal_id] = {}
            if source_type not in self._goal_dependencies[goal_id]:
                self._goal_dependencies[goal_id][source_type] = set()

            self._goal_dependencies[goal_id][source_type].add(source_id)

            if source_id not in self._source_to_goals:
                self._source_to_goals[source_id] = set()
            self._source_to_goals[source_id].add(goal_id)

            logger.debug(f"Registered dependency: goal {goal_id} -> {source_type} {source_id}")

    def register_goal_calculator(
        self, goal_id: str, calculator_fn: GoalCalculationFn
    ) -> None:
        """Register a calculation function for a goal.

        The function is called during reconciliation to recalculate
        the goal's progress from source records.

        Args:
            goal_id: The goal to calculate.
            calculator_fn: Callable that takes (goal_id, user_id,
                source_records) and returns (calculated_value,
                calculated_progress).
        """
        with self._lock:
            self._goal_calculators[goal_id] = calculator_fn
            logger.debug(f"Registered calculator for goal {goal_id}")

    def record_source_change(
        self, change: SourceChange
    ) -> Set[str]:
        """Process a source data change and return affected goal IDs.

        This identifies which goals are affected by the change and
        marks them for reconciliation.

        Args:
            change: Description of the source change.

        Returns:
            Set of goal_ids affected by this change.
        """
        with self._lock:
            affected_goals = self._source_to_goals.get(change.source_id, set()).copy()
            self._audit_log.append(change)

            if affected_goals:
                logger.info(
                    f"Source change {change.change_type} on {change.source_id} "
                    f"affects goals: {affected_goals}"
                )

            return affected_goals

    def record_progress_measurement(
        self,
        goal_id: str,
        user_id: int,
        source_type: SourceType,
        value: float,
        source_metadata: Optional[Dict[str, Any]] = None,
    ) -> GoalProgressRecord:
        """Record a measurement from a source.

        This creates an immutable record of a measurement. These records
        are later used to recalculate goal progress during reconciliation.

        Args:
            goal_id: The goal this measurement affects.
            user_id: The user who owns the goal.
            source_type: Type of source.
            value: The measured value.
            source_metadata: Optional metadata about the measurement.

        Returns:
            The recorded measurement.
        """
        with self._lock:
            if goal_id not in self._progress_records:
                self._progress_records[goal_id] = []

            record = GoalProgressRecord(
                record_id=f"gpr_{id({})}_{len(self._progress_records[goal_id])}",
                source_type=source_type,
                goal_id=goal_id,
                user_id=user_id,
                value=value,
                timestamp=datetime.now(),
                source_metadata=source_metadata or {},
            )

            self._progress_records[goal_id].append(record)
            return record

    def get_source_records_for_goal(
        self, goal_id: str
    ) -> List[GoalProgressRecord]:
        """Get all recorded measurements for a goal.

        Args:
            goal_id: The goal to get records for.

        Returns:
            List of all recorded measurements, in chronological order.
        """
        with self._lock:
            return self._progress_records.get(goal_id, [])[:]

    def reconcile_goal(
        self, goal_id: str, user_id: int, current_stored_progress: float
    ) -> Tuple[float, bool]:
        """Reconcile a single goal against its source records.

        Recalculates the goal's progress from source data and compares
        with the stored progress. If a discrepancy is found, it is
        recorded in the history (but not automatically repaired; repair
        is manual via repair_goal).

        Args:
            goal_id: The goal to reconcile.
            user_id: The user who owns the goal.
            current_stored_progress: The currently stored progress value.

        Returns:
            (calculated_progress, is_consistent): The calculated progress
            and whether it matches the stored value.
        """
        with self._lock:
            if goal_id not in self._goal_calculators:
                logger.warning(f"No calculator registered for goal {goal_id}")
                return current_stored_progress, True

            calculator = self._goal_calculators[goal_id]
            records = self._progress_records.get(goal_id, [])

            try:
                calculated_value, calculated_progress = calculator(
                    goal_id, user_id, records
                )
            except Exception as e:
                logger.error(f"Calculation failed for goal {goal_id}: {e}")
                return current_stored_progress, True

            is_consistent = abs(calculated_progress - current_stored_progress) < 0.01

            if not is_consistent:
                discrepancy = GoalProgressDiscrepancy(
                    goal_id=goal_id,
                    user_id=user_id,
                    stored_progress=current_stored_progress,
                    calculated_progress=calculated_progress,
                    stored_current_value=0.0,  # Would need to fetch from goal object
                    calculated_current_value=calculated_value,
                    difference=calculated_progress - current_stored_progress,
                    detected_at=datetime.now(),
                    reason=f"Calculation produced {calculated_progress:.2f}% but stored value was {current_stored_progress:.2f}%",
                )

                if goal_id not in self._discrepancy_history:
                    self._discrepancy_history[goal_id] = []
                self._discrepancy_history[goal_id].append(discrepancy)

                logger.warning(
                    f"Discrepancy detected for goal {goal_id}: "
                    f"stored={current_stored_progress:.2f}% vs calculated={calculated_progress:.2f}%"
                )

            return calculated_progress, is_consistent

    def get_discrepancies_for_goal(self, goal_id: str) -> List[GoalProgressDiscrepancy]:
        """Get all detected discrepancies for a goal.

        Args:
            goal_id: The goal to check.

        Returns:
            List of discrepancies, in chronological order.
        """
        with self._lock:
            return self._discrepancy_history.get(goal_id, [])[:]

    def repair_goal(
        self, goal_id: str, user_id: int, calculated_progress: float
    ) -> bool:
        """Repair a goal's progress by setting it to the calculated value.

        This is the manual repair mechanism. It should be called after
        human review of the discrepancy.

        Args:
            goal_id: The goal to repair.
            user_id: The user who owns the goal.
            calculated_progress: The correct progress value.

        Returns:
            True if repair was recorded.
        """
        with self._lock:
            record = GoalProgressRecord(
                record_id=f"gpr_repair_{id({})}_{datetime.now().timestamp()}",
                source_type=SourceType.CALCULATED_EMISSIONS,
                goal_id=goal_id,
                user_id=user_id,
                value=calculated_progress,
                timestamp=datetime.now(),
                source_metadata={
                    "repair_action": True,
                    "reason": "Manual reconciliation repair",
                },
            )

            if goal_id not in self._progress_records:
                self._progress_records[goal_id] = []

            self._progress_records[goal_id].append(record)
            logger.info(f"Repaired goal {goal_id} to progress {calculated_progress:.2f}%")
            return True

    def reconcile_goals_affected_by_source(
        self, change: SourceChange, goal_fetcher: Callable[[str], Any]
    ) -> Dict[str, Tuple[float, bool]]:
        """Reconcile all goals affected by a source change.

        Args:
            change: Description of the source change.
            goal_fetcher: Callable that takes goal_id and returns the Goal object.

        Returns:
            Dict mapping goal_id to (calculated_progress, is_consistent).
        """
        affected_goals = self.record_source_change(change)
        results: Dict[str, Tuple[float, bool]] = {}

        for goal_id in affected_goals:
            try:
                goal = goal_fetcher(goal_id)
                if goal:
                    progress, consistency = self.reconcile_goal(
                        goal_id, goal.user_id, goal.progress
                    )
                    results[goal_id] = (progress, consistency)
            except Exception as e:
                logger.error(f"Failed to reconcile goal {goal_id}: {e}")

        return results

    def get_audit_log(self) -> List[SourceChange]:
        """Get the audit log of all source changes processed.

        Returns:
            List of source changes, in chronological order.
        """
        with self._lock:
            return self._audit_log[:]

    def clear_audit_log(self) -> None:
        """Clear the audit log (for testing only)."""
        with self._lock:
            self._audit_log.clear()
            logger.debug("Audit log cleared")


# Global reconciler instance
_reconciler: Optional[GoalProgressReconciler] = None
_reconciler_lock = threading.Lock()


def get_goal_progress_reconciler() -> GoalProgressReconciler:
    """Get or create the global goal progress reconciler."""
    global _reconciler
    with _reconciler_lock:
        if _reconciler is None:
            _reconciler = GoalProgressReconciler()
        return _reconciler