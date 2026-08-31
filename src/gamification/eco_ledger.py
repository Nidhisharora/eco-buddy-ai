import threading
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class DuplicateEventError(Exception):
    pass

class EcoLedgerDB:
    """
    Mock interface for the PostgreSQL EcoLedger table.
    Replaces the mutable 'points' column with an append-only event sourcing ledger.
    """
    
    def __init__(self):
        # In-memory mock database: Map[user_id -> List[Events]]
        self.ledger = {}
        # Tracks composite uniqueness (user_id + idempotency_key)
        self.idempotency_store = set()
        self.db_lock = threading.Lock()

    def insert_event(self, user_id: str, challenge_id: str, points: int, idempotency_key: str):
        """
        Appends an immutable point event to the user's ledger.
        Enforces strict idempotency to prevent double-awarding during network retries.
        """
        with self.db_lock:
            # 1. Enforce Idempotency Constraint
            composite_key = f"{user_id}:{idempotency_key}"
            if composite_key in self.idempotency_store:
                logger.warning(f"Duplicate idempotency key detected: {composite_key}. Silently dropping request to prevent double-award.")
                raise DuplicateEventError("This challenge has already been processed.")

            # 2. Append Event
            if user_id not in self.ledger:
                self.ledger[user_id] = []
                
            event = {
                'user_id': user_id,
                'challenge_id': challenge_id,
                'points': points,
                'idempotency_key': idempotency_key,
                'timestamp': datetime.now().isoformat()
            }
            
            self.ledger[user_id].append(event)
            self.idempotency_store.add(composite_key)
            
            logger.info(f"Successfully recorded +{points} points for {user_id} via {challenge_id}")

    def get_events_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the immutable ledger of point events for a specific user.
        """
        with self.db_lock:
            return self.ledger.get(user_id, []).copy()

# Export a singleton instance for the mock DB
eco_ledger_db = EcoLedgerDB()
