import uuid
from datetime import datetime

from async_context_engine.models import TaskRecord
from async_context_engine.store import TaskStore


def dispatch_task(
    store: TaskStore,
    thread_id: str,
    description: str,
) -> TaskRecord:
    """Create a new task with status='pending', persist it, and return the record.

    The caller should send ``record.task_id`` to the external system
    so it can later call ``update_task_result()`` with the same ID.
    """
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
    """Mark a task as completed (or failed) in the store.

    Designed to be called from external systems or sub-agents.
    Pass ``result`` for success or ``error`` for failure.
    The poller will pick up the change and re-enter the graph.
    """
    if error is not None:
        store.update_task(task_id, status="failed", error=error)
    else:
        store.update_task(task_id, status="completed", result=result)
