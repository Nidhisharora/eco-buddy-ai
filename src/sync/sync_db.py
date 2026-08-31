import threading
from typing import List, Dict
from .delta_models import EcoLogDelta

class SyncDatabaseMock:
    """
    Simulates the PostgreSQL backend holding the definitive server state.
    """
    
    def __init__(self):
        # Maps user_id -> Dict[log_id -> EcoLogDelta]
        self.db: Dict[str, Dict[str, EcoLogDelta]] = {}
        self.lock = threading.Lock()

    def get_server_deltas_since(self, user_id: str, last_sync_timestamp: int) -> List[EcoLogDelta]:
        """
        Retrieves all records modified on the server after the client's last sync.
        This includes tombstones (is_deleted=True) so the client knows to delete them locally.
        """
        with self.lock:
            user_records = self.db.get(user_id, {})
            return [
                record for record in user_records.values()
                if record.last_modified > last_sync_timestamp
            ]

    def get_record(self, user_id: str, log_id: str) -> EcoLogDelta:
        with self.lock:
            return self.db.get(user_id, {}).get(log_id)

    def apply_delta(self, delta: EcoLogDelta):
        """
        Upserts the client's delta into the server database.
        Note: We DO NOT delete the record if is_deleted=True, we just save the tombstone state.
        """
        with self.lock:
            if delta.user_id not in self.db:
                self.db[delta.user_id] = {}
            self.db[delta.user_id][delta.id] = delta

sync_db = SyncDatabaseMock()
