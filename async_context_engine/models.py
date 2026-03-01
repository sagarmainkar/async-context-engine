from dataclasses import dataclass
from datetime import datetime


@dataclass
class TaskRecord:
    task_id: str
    thread_id: str
    status: str  # "pending" | "running" | "completed" | "failed"
    description: str
    result: str | None
    error: str | None
    created_at: datetime
    updated_at: datetime
