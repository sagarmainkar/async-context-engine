from datetime import datetime

from async_context_engine.models import TaskRecord
from async_context_engine.store.memory import InMemoryTaskStore


def _make_record(task_id="task-1", thread_id="thread-a", status="pending"):
    now = datetime.now()
    return TaskRecord(
        task_id=task_id,
        thread_id=thread_id,
        status=status,
        description="Test task",
        result=None,
        error=None,
        created_at=now,
        updated_at=now,
    )


def test_create_and_get_task():
    store = InMemoryTaskStore()
    record = _make_record()
    store.create_task(record)
    retrieved = store.get_task("task-1")
    assert retrieved is not None
    assert retrieved.task_id == "task-1"
    assert retrieved.status == "pending"


def test_get_task_returns_none_for_missing():
    store = InMemoryTaskStore()
    assert store.get_task("nonexistent") is None


def test_update_task_status():
    store = InMemoryTaskStore()
    store.create_task(_make_record())
    store.update_task("task-1", status="completed", result="done")
    record = store.get_task("task-1")
    assert record.status == "completed"
    assert record.result == "done"


def test_update_task_error():
    store = InMemoryTaskStore()
    store.create_task(_make_record())
    store.update_task("task-1", status="failed", error="timeout")
    record = store.get_task("task-1")
    assert record.status == "failed"
    assert record.error == "timeout"


def test_update_task_sets_updated_at():
    store = InMemoryTaskStore()
    record = _make_record()
    original_updated = record.updated_at
    store.create_task(record)
    store.update_task("task-1", status="running")
    updated = store.get_task("task-1")
    assert updated.updated_at >= original_updated


def test_get_tasks_by_thread():
    store = InMemoryTaskStore()
    store.create_task(_make_record(task_id="t1", thread_id="thread-a"))
    store.create_task(_make_record(task_id="t2", thread_id="thread-a"))
    store.create_task(_make_record(task_id="t3", thread_id="thread-b"))
    tasks = store.get_tasks_by_thread("thread-a")
    assert len(tasks) == 2
    assert {t.task_id for t in tasks} == {"t1", "t2"}


def test_get_tasks_by_status():
    store = InMemoryTaskStore()
    store.create_task(_make_record(task_id="t1", thread_id="thread-a", status="pending"))
    store.create_task(_make_record(task_id="t2", thread_id="thread-a", status="completed"))
    store.create_task(_make_record(task_id="t3", thread_id="thread-a", status="pending"))
    pending = store.get_tasks_by_status("thread-a", "pending")
    assert len(pending) == 2
    assert {t.task_id for t in pending} == {"t1", "t3"}
