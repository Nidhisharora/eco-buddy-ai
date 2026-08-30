import threading
import time
import logging
from .iot_buffer import iot_buffer
from .iot_db import timescale_client

logger = logging.getLogger(__name__)

class IoTAggregatorWorker:
    """
    Background worker that runs on a dedicated thread.
    It periodically wakes up, drains the high-frequency in-memory buffer,
    and executes a single bulk upsert to the database.
    """
    
    def __init__(self, interval_seconds: int = 60):
        self.interval_seconds = interval_seconds
        self._thread = None
        self._stop_event = threading.Event()

    def start(self):
        """Starts the background worker thread."""
        if self._thread and self._thread.is_alive():
            return
            
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info(f"IoTAggregatorWorker started. Flushing buffer every {self.interval_seconds} seconds.")

    def stop(self):
        """Signals the background thread to stop."""
        self._stop_event.set()
        if self._thread:
            self._thread.join()
            logger.info("IoTAggregatorWorker stopped.")

    def _run_loop(self):
        while not self._stop_event.is_set():
            # Wait for the specified interval, but allow for graceful shutdown interception
            self._stop_event.wait(self.interval_seconds)
            
            if not self._stop_event.is_set():
                self._flush_buffer()

    def _flush_buffer(self):
        try:
            # Drain the entire memory buffer instantly to free up locks for WebSockets
            records = iot_buffer.drain_all()
            
            if records:
                logger.info(f"[Aggregator] Drained {len(records)} records from memory buffer.")
                # Perform the massive bulk insert
                timescale_client.bulk_upsert_ticks(records)
                
        except Exception as e:
            logger.error(f"[Aggregator] Failed to bulk upsert: {e}")
            # In a resilient production system, we would push these records into a Dead Letter Queue (DLQ)

# Export a default instance
iot_aggregator = IoTAggregatorWorker()
