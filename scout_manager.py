import queue
import time
import threading
from state import Task


class ScoutManager:
    """Manages background scout threads and collects their results."""

    SIMULATED_RESULTS = {
        "calculate": {"data": "$1,250", "delay": 30},
        "search": {"data": "Found 3 matching documents", "delay": 30},
        "research": {
            "data": "Analysis complete: 5 key findings identified",
            "delay": 45,
        },
        "find": {"data": "Located item in warehouse B, shelf 14", "delay": 40},
        "order": {
            "data": "Order total: $1,250 (3 items, shipping included)",
            "delay": 30,
        },
    }

    FALLBACK_DELAY = 20
    FALLBACK_DATA = "Task completed (generic result)"

    def __init__(self):
        self._completed: queue.Queue = queue.Queue()

    def dispatch(self, task: Task):
        """Spawn a daemon thread to simulate the task."""
        delay, data = self._match_task(task.user_query)
        t = threading.Thread(
            target=self._run_scout,
            args=(task.task_id, task.user_query, delay, data),
            daemon=True,
        )
        t.start()

    def get_completed(self) -> list[dict]:
        """Non-blocking drain of all completed results."""
        results = []
        while not self._completed.empty():
            try:
                results.append(self._completed.get_nowait())
            except queue.Empty:
                break
        return results

    def _match_task(self, user_query: str) -> tuple[int, str]:
        """Match user query to simulated result config."""
        query_lower = user_query.lower()
        for keyword, sim in self.SIMULATED_RESULTS.items():
            if keyword in query_lower:
                return sim["delay"], sim["data"]
        return self.FALLBACK_DELAY, self.FALLBACK_DATA

    def _run_scout(self, task_id: str, user_query: str, delay: int, data: str):
        """Background thread: sleep then enqueue result."""
        time.sleep(delay)
        self._completed.put(
            {
                "task_id": task_id,
                "user_query": user_query,
                "data": data,
            }
        )
