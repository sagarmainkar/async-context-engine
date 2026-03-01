import uuid
from datetime import datetime

from async_context_engine.models import TaskRecord
from async_context_engine.store import TaskStore


def dispatch_task(
    store: TaskStore,
    thread_id: str,
    description: str,
) -> TaskRecord:
    """Create a new task record with status='pending' and persist it."""
    now = datetime.now()
    record = TaskRecord(
        task_id=str(uuid.uuid4()),
        thread_id=thread_id,
        status="pending",
        description=description,
        result=None,
        error=None,
        created_at=now,
        updated_at=now,
    )
    store.create_task(record)
    return record


def update_task_result(
    store: TaskStore,
    task_id: str,
    result: str | None = None,
    error: str | None = None,
) -> None:
    """Update a task in the store. Called from external systems."""
    if error is not None:
        store.update_task(task_id, status="failed", error=error)
    else:
        store.update_task(task_id, status="completed", result=result)
