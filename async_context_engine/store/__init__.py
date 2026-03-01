from abc import ABC, abstractmethod

from async_context_engine.models import TaskRecord


class TaskStore(ABC):
    @abstractmethod
    def create_task(self, record: TaskRecord) -> None:
        """Persist a new task record."""

    @abstractmethod
    def update_task(
        self,
        task_id: str,
        status: str,
        result: str | None = None,
        error: str | None = None,
    ) -> None:
        """Update task status, result, or error. Sets updated_at automatically."""

    @abstractmethod
    def get_task(self, task_id: str) -> TaskRecord | None:
        """Retrieve a single task by ID."""

    @abstractmethod
    def get_tasks_by_thread(self, thread_id: str) -> list[TaskRecord]:
        """Get all tasks for a given thread/session."""

    @abstractmethod
    def get_tasks_by_status(self, thread_id: str, status: str) -> list[TaskRecord]:
        """Get tasks filtered by status within a thread."""
