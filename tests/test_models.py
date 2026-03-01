from datetime import datetime
from async_context_engine.models import TaskRecord


def test_task_record_creation():
    now = datetime.now()
    record = TaskRecord(
        task_id="task-123",
        thread_id="thread-abc",
        status="pending",
        description="Process order",
        result=None,
        error=None,
        created_at=now,
        updated_at=now,
    )
    assert record.task_id == "task-123"
    assert record.thread_id == "thread-abc"
    assert record.status == "pending"
    assert record.description == "Process order"
    assert record.result is None
    assert record.error is None
    assert record.created_at == now
    assert record.updated_at == now


def test_task_record_with_result():
    now = datetime.now()
    record = TaskRecord(
        task_id="task-456",
        thread_id="thread-abc",
        status="completed",
        description="Process order",
        result="Order total: $1,250",
        error=None,
        created_at=now,
        updated_at=now,
    )
    assert record.status == "completed"
    assert record.result == "Order total: $1,250"


def test_task_record_with_error():
    now = datetime.now()
    record = TaskRecord(
        task_id="task-789",
        thread_id="thread-abc",
        status="failed",
        description="Process order",
        result=None,
        error="Connection timeout",
        created_at=now,
        updated_at=now,
    )
    assert record.status == "failed"
    assert record.error == "Connection timeout"
