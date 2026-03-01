from datetime import datetime

from async_context_engine.models import TaskRecord
from async_context_engine.store import TaskStore


class InMemoryTaskStore(TaskStore):
    """Dict-backed task store. Useful for tests and single-process apps."""

    def __init__(self):
        self._tasks: dict[str, TaskRecord] = {}

    def create_task(self, record: TaskRecord) -> None:
        """Store a task record in memory."""
        self._tasks[record.task_id] = record

    def update_task(
        self,
        task_id: str,
        status: str,
        result: str | None = None,
        error: str | None = None,
    ) -> None:
        """Update a task's status, result, or error in memory."""
        record = self._tasks[task_id]
        record.status = status
        if result is not None:
            record.result = result
        if error is not None:
            record.error = error
        record.updated_at = datetime.now()

    def get_task(self, task_id: str) -> TaskRecord | None:
        """Look up a task by ID, or return None."""
        return self._tasks.get(task_id)

    def get_tasks_by_thread(self, thread_id: str) -> list[TaskRecord]:
        """Return all tasks for a given thread."""
        return [t for t in self._tasks.values() if t.thread_id == thread_id]

    def get_tasks_by_status(self, thread_id: str, status: str) -> list[TaskRecord]:
        """Return tasks matching a status within a thread."""
        return [
            t
            for t in self._tasks.values()
            if t.thread_id == thread_id and t.status == status
        ]
