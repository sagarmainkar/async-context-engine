import time
import threading
from async_context_engine import update_task_result
from async_context_engine.store import TaskStore


class ScoutManager:
    """Simulated external system that runs background work
    and reports results back to the TaskStore."""

    SIMULATED_RESULTS = {
        "calculate": {"data": "$1,250", "delay": 20},
        "search": {"data": "Found 3 matching documents", "delay": 10},
        "research": {"data": "Analysis complete: 5 key findings identified", "delay": 15},
        "find": {"data": "Located item in warehouse B, shelf 14", "delay": 10},
        "order": {"data": "Order total: $1,250 (3 items, shipping included)", "delay": 10},
    }

    FALLBACK_DELAY = 20
    FALLBACK_DATA = "Task completed (generic result)"

    def __init__(self, store: TaskStore):
        self._store = store

    def dispatch(self, task_id: str, description: str):
        """Spawn a daemon thread to simulate the task."""
        delay, data = self._match_task(description)
        t = threading.Thread(
            target=self._run_scout,
            args=(task_id, delay, data),
            daemon=True,
        )
        t.start()

    def _match_task(self, description: str) -> tuple[int, str]:
        query_lower = description.lower()
        for keyword, sim in self.SIMULATED_RESULTS.items():
            if keyword in query_lower:
                return sim["delay"], sim["data"]
        return self.FALLBACK_DELAY, self.FALLBACK_DATA

    def _run_scout(self, task_id: str, delay: int, data: str):
        time.sleep(delay)
        update_task_result(self._store, task_id=task_id, result=data)
