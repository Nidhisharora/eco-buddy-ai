import logging
from typing import List, Dict, Any
import time

logger = logging.getLogger(__name__)

class TimescaleDBClient:
    """
    Simulates a connection to a PostgreSQL/TimescaleDB instance optimized for time-series data.
    """

    def bulk_upsert_ticks(self, records: List[Dict[str, Any]]):
        """
        Executes a massive bulk INSERT instead of individual row-by-row queries.
        This drastically reduces network overhead and prevents Postgres lock saturation.
        """
        if not records:
            return

        logger.info(f"[DB] Initiating bulk upsert for {len(records)} IoT ticks...")
        
        # Simulate network trip to Database
        time.sleep(0.5)

        # In production, this would use executemany or a bulk COPY command:
        # e.g., INSERT INTO iot_hypertable (device_id, kwh, timestamp) VALUES %s ON CONFLICT DO UPDATE
        
        logger.info(f"[DB] Successfully committed {len(records)} records to hypertable.")

# Export a default instance
timescale_client = TimescaleDBClient()
