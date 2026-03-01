import threading
import time

from async_context_engine.store import TaskStore


class AsyncPoller:
    """Built-in poller that checks the TaskStore for completed tasks
    and re-enters the graph with results.

    Runs as a daemon thread at a configurable cadence.
    """

    def __init__(
        self,
        store: TaskStore,
        graph,
        config: dict,
        interval: int = 5,
    ):
        self._store = store
        self._graph = graph
        self._config = config
        self._interval = interval
        self._running = False
        self._thread: threading.Thread | None = None
        self._delivered: set[str] = set()  # task_ids already delivered

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def _poll_loop(self) -> None:
        while self._running:
            time.sleep(self._interval)
            if not self._running:
                break
            self._check_and_deliver()

    def _check_and_deliver(self) -> None:
        thread_id = self._config["configurable"]["thread_id"]
        completed = self._store.get_tasks_by_status(thread_id, "completed")
        failed = self._store.get_tasks_by_status(thread_id, "failed")

        new_results = []
        for task in completed + failed:
            if task.task_id not in self._delivered:
                self._delivered.add(task.task_id)
                new_results.append({
                    "task_id": task.task_id,
                    "description": task.description,
                    "result": task.result,
                    "error": task.error,
                    "status": task.status,
                })

        if not new_results:
            return

        # Patch results into graph state
        self._graph.update_state(self._config, {"results_buffer": new_results})

        # Trigger graph run with synthetic message
        self._graph.stream(
            {"messages": [{"role": "user", "content": "[system: background task completed]"}]},
            self._config,
        )
