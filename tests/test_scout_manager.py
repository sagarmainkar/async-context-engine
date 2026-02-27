import time
from state import Task
from scout_manager import ScoutManager


def test_dispatch_starts_background_work():
    sm = ScoutManager()
    task = Task.create(user_query="calculate total for Order Alpha")
    sm.dispatch(task)
    # Scout is running — nothing completed yet
    assert sm.get_completed() == []


def test_scout_completes_and_returns_result():
    """Use a short delay to verify end-to-end: dispatch -> wait -> get_completed."""
    sm = ScoutManager()
    task = Task.create(user_query="calculate total")
    # Override delay for testing
    sm.SIMULATED_RESULTS = {"calculate": {"data": "$1,250", "delay": 1}}
    sm.dispatch(task)
    time.sleep(2)  # Wait for scout to finish
    completed = sm.get_completed()
    assert len(completed) == 1
    assert completed[0]["task_id"] == task.task_id
    assert completed[0]["user_query"] == "calculate total"
    assert completed[0]["data"] == "$1,250"


def test_get_completed_drains_queue():
    """After get_completed(), the queue should be empty."""
    sm = ScoutManager()
    task = Task.create(user_query="calculate total")
    sm.SIMULATED_RESULTS = {"calculate": {"data": "$1,250", "delay": 1}}
    sm.dispatch(task)
    time.sleep(2)
    first = sm.get_completed()
    assert len(first) == 1
    second = sm.get_completed()
    assert second == []


def test_multiple_tasks_complete_independently():
    sm = ScoutManager()
    sm.SIMULATED_RESULTS = {
        "calculate": {"data": "$1,250", "delay": 1},
        "search": {"data": "Found 3 docs", "delay": 1},
    }
    task1 = Task.create(user_query="calculate total")
    time.sleep(0.01)  # Avoid task_id collision (timestamp-based IDs)
    task2 = Task.create(user_query="search for reports")
    sm.dispatch(task1)
    sm.dispatch(task2)
    time.sleep(3)
    completed = sm.get_completed()
    assert len(completed) == 2
    task_ids = {r["task_id"] for r in completed}
    assert task1.task_id in task_ids
    assert task2.task_id in task_ids


def test_dispatch_with_no_keyword_match_uses_fallback():
    """Fallback: no keyword match still dispatches without crashing."""
    sm = ScoutManager()
    task = Task.create(user_query="do something unusual")
    sm.SIMULATED_RESULTS = {}  # No keywords to match
    sm.FALLBACK_DELAY = 1  # Override so test doesn't take 20s
    sm.dispatch(task)
    time.sleep(2)
    completed = sm.get_completed()
    assert len(completed) == 1
    assert completed[0]["task_id"] == task.task_id
    assert completed[0]["data"] == "Task completed (generic result)"
