from datetime import datetime
from state import Task, AgentState, detect_task


def test_task_create_generates_id_and_timestamps():
    task = Task.create(user_query="calculate total for Order Alpha")
    assert task.task_id.startswith("Task-")
    assert task.user_query == "calculate total for Order Alpha"
    assert task.is_async is True
    assert isinstance(task.created_at, datetime)


def test_task_create_sync():
    task = Task.create(user_query="what time is it", is_async=False)
    assert task.is_async is False


def test_detect_task_returns_async_task_for_keyword():
    task = detect_task("calculate the total for Order Alpha")
    assert task is not None
    assert task.is_async is True
    assert task.user_query == "calculate the total for Order Alpha"


def test_detect_task_returns_sync_task_for_no_keyword():
    task = detect_task("what's a good pizza place?")
    assert task is not None
    assert task.is_async is False
    assert task.user_query == "what's a good pizza place?"
