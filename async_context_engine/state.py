from typing import TypedDict

from async_context_engine.models import TaskRecord


class AsyncTaskState(TypedDict):
    task_records: dict[str, TaskRecord]
    results_buffer: list[dict]
