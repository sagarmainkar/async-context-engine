from dataclasses import dataclass
from datetime import datetime


@dataclass
class TaskRecord:
    """Represents a single async task tracked by the engine.

    Lifecycle: pending → running → completed | failed.
    Created by ``dispatch_task()``, updated by ``update_task_result()``.
    """

    task_id: str
    thread_id: str
    status: str  # "pending" | "running" | "completed" | "failed"
    description: str
    result: str | None
    error: str | None
    created_at: datetime
    updated_at: datetime
