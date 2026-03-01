import time
from async_context_engine import dispatch_task, InMemoryTaskStore
from scout_manager import ScoutManager


def test_dispatch_starts_background_work():
    store = InMemoryTaskStore()
    sm = ScoutManager(store=store)
    task = dispatch_task(store, thread_id="thread-a", description="calculate total")
    sm.dispatch(task.task_id, "calculate total")
    # Scout is running — task still pending
    record = store.get_task(task.task_id)
    assert record.status == "pending"


def test_scout_completes_and_updates_store():
    store = InMemoryTaskStore()
    sm = ScoutManager(store=store)
    sm.SIMULATED_RESULTS = {"calculate": {"data": "$1,250", "delay": 1}}
    task = dispatch_task(store, thread_id="thread-a", description="calculate total")
    sm.dispatch(task.task_id, "calculate total")
    time.sleep(2)
    record = store.get_task(task.task_id)
    assert record.status == "completed"
    assert record.result == "$1,250"


def test_multiple_tasks_complete_independently():
    store = InMemoryTaskStore()
    sm = ScoutManager(store=store)
    sm.SIMULATED_RESULTS = {
        "calculate": {"data": "$1,250", "delay": 1},
        "search": {"data": "Found 3 docs", "delay": 1},
    }
    t1 = dispatch_task(store, thread_id="thread-a", description="calculate total")
    t2 = dispatch_task(store, thread_id="thread-a", description="search for reports")
    sm.dispatch(t1.task_id, "calculate total")
    sm.dispatch(t2.task_id, "search for reports")
    time.sleep(3)
    r1 = store.get_task(t1.task_id)
    r2 = store.get_task(t2.task_id)
    assert r1.status == "completed"
    assert r2.status == "completed"
