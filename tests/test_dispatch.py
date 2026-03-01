from async_context_engine.dispatch import dispatch_task, update_task_result
from async_context_engine.store.memory import InMemoryTaskStore


def test_dispatch_task_creates_pending_record():
    store = InMemoryTaskStore()
    task = dispatch_task(store, thread_id="thread-a", description="Process order")
    assert task.task_id is not None
    assert task.thread_id == "thread-a"
    assert task.status == "pending"
    assert task.description == "Process order"
    retrieved = store.get_task(task.task_id)
    assert retrieved is not None
    assert retrieved.status == "pending"


def test_dispatch_task_generates_unique_ids():
    store = InMemoryTaskStore()
    t1 = dispatch_task(store, thread_id="thread-a", description="Task 1")
    t2 = dispatch_task(store, thread_id="thread-a", description="Task 2")
    assert t1.task_id != t2.task_id


def test_update_task_result_sets_completed():
    store = InMemoryTaskStore()
    task = dispatch_task(store, thread_id="thread-a", description="Process order")
    update_task_result(store, task_id=task.task_id, result="Order total: $1,250")
    record = store.get_task(task.task_id)
    assert record.status == "completed"
    assert record.result == "Order total: $1,250"


def test_update_task_result_with_error():
    store = InMemoryTaskStore()
    task = dispatch_task(store, thread_id="thread-a", description="Process order")
    update_task_result(store, task_id=task.task_id, error="Connection failed")
    record = store.get_task(task.task_id)
    assert record.status == "failed"
    assert record.error == "Connection failed"
