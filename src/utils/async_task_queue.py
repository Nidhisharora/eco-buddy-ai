"""
Asynchronous Task Queue System for Background Processing
Purpose: Move heavy operations to background threads to prevent the app from freezing.
"""

import asyncio
import threading
import queue
import time
import logging
from typing import Dict, Any, Callable, List

logger = logging.getLogger(__name__)


class AsyncTaskQueue:
    """
    A thread-safe asynchronous task queue for background processing.
    """

    def __init__(self, max_workers: int = 3):
        self.task_queue: queue.Queue = queue.Queue()
        self.max_workers = max_workers
        self.task_status: Dict[str, str] = {}
        self.task_results: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self.workers: List[threading.Thread] = []

    def add_task(self, task_id: str, task_func: Callable, *args, **kwargs) -> bool:
        """
        Adds a new background task to the queue.
        """
        with self._lock:
            self.task_status[task_id] = "Pending"
        self.task_queue.put((task_id, task_func, args, kwargs))
        logger.info(f"Task {task_id} added to queue.")
        return True

    def start_workers(self):
        """
        Starts background worker threads.
        """
        for _ in range(self.max_workers):
            worker = threading.Thread(target=self._process_queue, daemon=True)
            worker.start()
            self.workers.append(worker)
        logger.info(f"Started {self.max_workers} background workers.")

    def _process_queue(self):
        """
        Internal worker loop to process tasks.
        """
        while True:
            try:
                task_id, task_func, args, kwargs = self.task_queue.get(timeout=1)
            except queue.Empty:
                continue

            try:
                with self._lock:
                    self.task_status[task_id] = "Running"
                
                result = task_func(*args, **kwargs)
                
                with self._lock:
                    self.task_status[task_id] = "Completed"
                    self.task_results[task_id] = result
                logger.info(f"Task {task_id} completed successfully.")
            
            except Exception as e:
                with self._lock:
                    self.task_status[task_id] = "Failed"
                logger.error(f"Task {task_id} failed: {e}")
            
            finally:
                self.task_queue.task_done()

    def get_task_status(self, task_id: str) -> str:
        """
        Retrieves the status of a specific task.
        """
        with self._lock:
            return self.task_status.get(task_id, "Not Found")

    def get_task_result(self, task_id: str) -> Any:
        """
        Retrieves the result of a completed task.
        """
        with self._lock:
            return self.task_results.get(task_id)

    def get_all_status(self) -> Dict[str, str]:
        """
        Retrieves the status of all tasks.
        """
        with self._lock:
            return self.task_status.copy()


# Global queue instance
task_queue = AsyncTaskQueue()