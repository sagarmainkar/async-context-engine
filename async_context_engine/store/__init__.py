from abc import ABC, abstractmethod

from async_context_engine.models import TaskRecord


class TaskStore(ABC):
    """Abstract persistence backend for task records.

    Implement this to plug in your own storage (Postgres, Redis, etc.).
    The library ships ``InMemoryTaskStore`` and ``FileTaskStore``.
    """

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
        """Retrieve a single task by ID, or None if not found."""

    @abstractmethod
    def get_tasks_by_thread(self, thread_id: str) -> list[TaskRecord]:
        """Return all tasks belonging to a conversation thread."""

    @abstractmethod
    def get_tasks_by_status(self, thread_id: str, status: str) -> list[TaskRecord]:
        """Return tasks matching a specific status within a thread."""
