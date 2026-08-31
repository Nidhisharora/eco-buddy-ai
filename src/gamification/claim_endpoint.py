import threading
import logging
from .eco_ledger import eco_ledger_db, DuplicateEventError
from .point_engine import PointEngine

logger = logging.getLogger(__name__)

class MockRedlock:
    """
    Simulates a distributed Redis lock (Redlock).
    Used to prevent race conditions when a user spam-clicks the claim button,
    ensuring only one thread can process the challenge claim at a time.
    """
    def __init__(self):
        self._locks = set()
        self._mutex = threading.Lock()

    def acquire(self, lock_key: str) -> bool:
        with self._mutex:
            if lock_key in self._locks:
                return False
            self._locks.add(lock_key)
            return True

    def release(self, lock_key: str):
        with self._mutex:
            if lock_key in self._locks:
                self._locks.remove(lock_key)

# Global Mock Distributed Lock
redlock = MockRedlock()

class ClaimService:
    """
    The secure API endpoint handler for claiming Eco-Challenge points.
    Protects against race conditions and state desynchronization (Issue #1471).
    """

    @staticmethod
    def claim_challenge(user_id: str, challenge_id: str, points: int, idempotency_key: str) -> dict:
        lock_key = f"claim_lock:{user_id}:{challenge_id}"
        
        # 1. Attempt to acquire the distributed lock
        if not redlock.acquire(lock_key):
            logger.warning(f"Lock collision for {lock_key}. Request rejected.")
            return {"status": "error", "message": "Too many requests. Please wait."}

        try:
            # 2. Safely write to the immutable ledger
            eco_ledger_db.insert_event(
                user_id=user_id,
                challenge_id=challenge_id,
                points=points,
                idempotency_key=idempotency_key
            )
            
            # 3. Deterministically calculate the new total score
            new_total = PointEngine.calculate_total_points(user_id)
            
            return {
                "status": "success",
                "message": f"Claimed {points} points!",
                "new_total": new_total
            }

        except DuplicateEventError:
            # The database caught a retry using the same idempotency key
            return {"status": "success", "message": "Already claimed.", "new_total": PointEngine.calculate_total_points(user_id)}
        
        except Exception as e:
            logger.error(f"Internal error during claim: {e}")
            return {"status": "error", "message": "Internal server error"}
            
        finally:
            # 4. Release the distributed lock
            redlock.release(lock_key)
