import json
from pathlib import Path
from datetime import datetime
from async_context_engine.models import TaskRecord
from async_context_engine.store.file import FileTaskStore


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


def test_create_and_get_task(tmp_path):
    store = FileTaskStore(path=tmp_path / "tasks.json")
    record = _make_record()
    store.create_task(record)
    retrieved = store.get_task("task-1")
    assert retrieved is not None
    assert retrieved.task_id == "task-1"
    assert retrieved.status == "pending"


def test_file_is_created_on_disk(tmp_path):
    filepath = tmp_path / "tasks.json"
    store = FileTaskStore(path=filepath)
    store.create_task(_make_record())
    assert filepath.exists()
    data = json.loads(filepath.read_text())
    assert "task-1" in data


def test_update_task_persists_to_file(tmp_path):
    store = FileTaskStore(path=tmp_path / "tasks.json")
    store.create_task(_make_record())
    store.update_task("task-1", status="completed", result="done")
    # Read from a fresh store instance to verify persistence
    store2 = FileTaskStore(path=tmp_path / "tasks.json")
    record = store2.get_task("task-1")
    assert record.status == "completed"
    assert record.result == "done"


def test_get_tasks_by_thread(tmp_path):
    store = FileTaskStore(path=tmp_path / "tasks.json")
    store.create_task(_make_record(task_id="t1", thread_id="thread-a"))
    store.create_task(_make_record(task_id="t2", thread_id="thread-b"))
    tasks = store.get_tasks_by_thread("thread-a")
    assert len(tasks) == 1
    assert tasks[0].task_id == "t1"


def test_get_tasks_by_status(tmp_path):
    store = FileTaskStore(path=tmp_path / "tasks.json")
    store.create_task(_make_record(task_id="t1", status="pending"))
    store.create_task(_make_record(task_id="t2", status="completed"))
    pending = store.get_tasks_by_status("thread-a", "pending")
    assert len(pending) == 1
    assert pending[0].task_id == "t1"


def test_get_task_returns_none_for_missing(tmp_path):
    store = FileTaskStore(path=tmp_path / "tasks.json")
    assert store.get_task("nonexistent") is None
