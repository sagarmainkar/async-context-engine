import logging
import threading
import time
from collections.abc import Callable

from async_context_engine.store import TaskStore

logger = logging.getLogger(__name__)


class AsyncPoller:
    """Built-in poller that checks the TaskStore for completed tasks
    and re-enters the graph with results.

    Runs as a daemon thread at a configurable cadence.

    Args:
        on_result: Optional callback invoked with each output chunk from
            the graph run triggered by result delivery. Signature:
            ``(output: dict) -> None``.
    """

    def __init__(
        self,
        store: TaskStore,
        graph,
        config: dict,
        interval: int = 5,
        on_result: Callable[[dict], None] | None = None,
    ):
        self._store = store
        self._graph = graph
        self._config = config
        self._interval = interval
        self._on_result = on_result
        self._running = False
        self._thread: threading.Thread | None = None
        self._delivered: set[str] = set()  # task_ids already delivered

    def start(self) -> None:
        """Start the background polling thread."""
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signal the polling thread to stop after the current cycle."""
        self._running = False

    def _poll_loop(self) -> None:
        while self._running:
            time.sleep(self._interval)
            if not self._running:
                break
            try:
                self._check_and_deliver()
            except Exception:
                logger.exception("Poller error during check_and_deliver")

    def _check_and_deliver(self) -> None:
        thread_id = self._config["configurable"]["thread_id"]
        completed = self._store.get_tasks_by_status(thread_id, "completed")
        failed = self._store.get_tasks_by_status(thread_id, "failed")

        for task in completed + failed:
            if task.task_id not in self._delivered:
                self._delivered.add(task.task_id)
                result_entry = {
                    "task_id": task.task_id,
                    "description": task.description,
                    "result": task.result,
                    "error": task.error,
                    "status": task.status,
                }

                # Deliver one result at a time so each gets its own graph run
                self._graph.update_state(
                    self._config, {"results_buffer": [result_entry]},
                )
                for output in self._graph.stream(
                    {"messages": [{"role": "user", "content": "[system: background task completed]"}]},
                    self._config,
                ):
                    if self._on_result is not None:
                        self._on_result(output)
