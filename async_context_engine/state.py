from typing import TypedDict

from async_context_engine.models import TaskRecord


class AsyncTaskState(TypedDict):
    """LangGraph state mixin for async task tracking.

    Extend this in your graph's state to enable async context re-entry.
    ``task_records`` holds all dispatched tasks keyed by task_id.
    ``results_buffer`` is populated by the poller when results arrive.
    """

    task_records: dict[str, TaskRecord]
    results_buffer: list[dict]
