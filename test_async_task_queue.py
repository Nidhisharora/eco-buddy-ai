"""
Comprehensive Unit Tests for Asynchronous Task Queue
Tests threading, task status, error handling, and concurrency.
"""

import time
import pytest
from async_task_queue import AsyncTaskQueue


def sample_task(duration: float):
    time.sleep(duration)
    return f"Completed in {duration}s"


def failing_task():
    return 1 / 0


class TestTaskQueueBasic:
    def test_add_task_success(self):
        """Should add a task and update its status."""
        q = AsyncTaskQueue()
        q.add_task("task-1", lambda: 0)
        assert q.get_task_status("task-1") == "Pending"

    def test_add_task_with_arguments(self):
        """Should accept arguments and keyword arguments."""
        q = AsyncTaskQueue()
        q.add_task("task-2", sample_task, 0.1)
        assert q.get_task_status("task-2") == "Pending"

    def test_get_nonexistent_task(self):
        """Should return 'Not Found' for a non-existent task."""
        q = AsyncTaskQueue()
        assert q.get_task_status("invalid") == "Not Found"

    def test_task_queue_is_thread_safe(self):
        """Should allow adding tasks from different threads."""
        import threading
        q = AsyncTaskQueue()
        for i in range(10):
            t = threading.Thread(target=q.add_task, args=(f"task-{i}", lambda: 0))
            t.start()
            t.join()
        assert len(q.get_all_status()) == 10


class TestTaskQueueExecution:
    def test_task_completes_successfully(self):
        """Should successfully execute a task and update its status."""
        q = AsyncTaskQueue()
        q.add_task("task-1", lambda: 1 + 1)
        q.start_workers()
        time.sleep(1)
        assert q.get_task_status("task-1") == "Completed"

    def test_task_handles_errors(self):
        """Should catch exceptions and update status to 'Failed'."""
        q = AsyncTaskQueue()
        q.add_task("fail-task", failing_task)
        q.start_workers()
        time.sleep(1)
        assert q.get_task_status("fail-task") == "Failed"

    def test_multiple_tasks_process(self):
        """Should process multiple tasks successfully."""
        q = AsyncTaskQueue(max_workers=3)
        for i in range(5):
            q.add_task(f"multi-{i}", lambda: 0)
        q.start_workers()
        time.sleep(2)
        statuses = q.get_all_status()
        assert all(status == "Completed" for status in statuses.values())


class TestTaskQueueResults:
    def test_get_task_result(self):
        """Should retrieve the result of a completed task."""
        q = AsyncTaskQueue()
        q.add_task("calc-task", lambda: 10 * 2)
        q.start_workers()
        time.sleep(1)
        assert q.get_task_result("calc-task") == 20

    def test_get_task_result_for_failed_task(self):
        """Should return None for failed tasks."""
        q = AsyncTaskQueue()
        q.add_task("fail-task", failing_task)
        q.start_workers()
        time.sleep(1)
        assert q.get_task_result("fail-task") is None


class TestTaskQueuePerformance:
    def test_queue_processes_batch_quickly(self):
        """Should process a batch of tasks quickly."""
        q = AsyncTaskQueue(max_workers=5)
        start_time = time.time()
        for i in range(10):
            q.add_task(f"batch-{i}", sample_task, 0.01)
        q.start_workers()
        q.task_queue.join()
        end_time = time.time()
        assert q.task_queue.unfinished_tasks == 0
        assert end_time - start_time < 2.0