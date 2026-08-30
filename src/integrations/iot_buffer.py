import threading
import logging
from collections import deque
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class IoTDataBuffer:
    """
    Singleton In-Memory Buffer for high-frequency WebSocket IoT ticks.
    Decouples the fast ingest stream from the slow database write layer,
    preventing connection pool exhaustion (Issue #1470).
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(IoTDataBuffer, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance

    def _initialize(self):
        # A thread-safe deque to act as our circular buffer
        self.queue = deque()
        self.queue_lock = threading.Lock()

    def push_tick(self, device_id: str, kwh: float, timestamp: str):
        """
        Instantly ingests a WebSocket tick without blocking on a database connection.
        """
        with self.queue_lock:
            self.queue.append({
                'device_id': device_id,
                'kwh': kwh,
                'timestamp': timestamp
            })

    def drain_all(self) -> List[Dict[str, Any]]:
        """
        Pops all currently buffered ticks for background aggregation.
        """
        with self.queue_lock:
            # Transfer references to a new list and clear the deque instantly
            items = list(self.queue)
            self.queue.clear()
            return items

# Export the singleton instance
iot_buffer = IoTDataBuffer()
