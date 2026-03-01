from datetime import datetime

from async_context_engine.models import TaskRecord
from async_context_engine.store import TaskStore


class InMemoryTaskStore(TaskStore):
    def __init__(self):
        self._tasks: dict[str, TaskRecord] = {}

    def create_task(self, record: TaskRecord) -> None:
        self._tasks[record.task_id] = record

    def update_task(
        self,
        task_id: str,
        status: str,
        result: str | None = None,
        error: str | None = None,
    ) -> None:
        record = self._tasks[task_id]
        record.status = status
        if result is not None:
            record.result = result
        if error is not None:
            record.error = error
        record.updated_at = datetime.now()

    def get_task(self, task_id: str) -> TaskRecord | None:
        return self._tasks.get(task_id)

    def get_tasks_by_thread(self, thread_id: str) -> list[TaskRecord]:
        return [t for t in self._tasks.values() if t.thread_id == thread_id]

    def get_tasks_by_status(self, thread_id: str, status: str) -> list[TaskRecord]:
        return [
            t
            for t in self._tasks.values()
            if t.thread_id == thread_id and t.status == status
        ]
