import time
from unittest.mock import MagicMock

from async_context_engine.dispatch import dispatch_task, update_task_result
from async_context_engine.poller import AsyncPoller
from async_context_engine.store.memory import InMemoryTaskStore


def test_poller_detects_completed_task():
    """Poller finds a completed task and calls graph.update_state + graph.stream."""
    store = InMemoryTaskStore()
    task = dispatch_task(store, thread_id="thread-a", description="Test task")

    # Simulate external system completing the task
    update_task_result(store, task_id=task.task_id, result="Done!")

    mock_graph = MagicMock()
    mock_graph.stream.return_value = []
    config = {"configurable": {"thread_id": "thread-a"}}

    poller = AsyncPoller(store=store, graph=mock_graph, config=config, interval=1)
    poller.start()
    time.sleep(2)
    poller.stop()

    # Poller should have called update_state with results_buffer
    mock_graph.update_state.assert_called()
    update_call_args = mock_graph.update_state.call_args
    results_buffer = update_call_args[0][1]["results_buffer"]
    assert len(results_buffer) >= 1
    assert results_buffer[0]["task_id"] == task.task_id
    assert results_buffer[0]["result"] == "Done!"


def test_poller_on_result_callback():
    """on_result callback receives each output chunk from graph.stream."""
    store = InMemoryTaskStore()
    task = dispatch_task(store, thread_id="thread-a", description="Test task")
    update_task_result(store, task_id=task.task_id, result="Done!")

    mock_graph = MagicMock()
    stream_output = [{"conductor": {"messages": ["hello"]}}]
    mock_graph.stream.return_value = stream_output
    config = {"configurable": {"thread_id": "thread-a"}}

    received = []
    poller = AsyncPoller(
        store=store, graph=mock_graph, config=config, interval=1,
        on_result=lambda output: received.append(output),
    )
    poller.start()
    time.sleep(2)
    poller.stop()

    assert len(received) == 1
    assert received[0] == {"conductor": {"messages": ["hello"]}}


def test_poller_delivers_each_result_individually():
    """When multiple tasks complete, each gets its own graph run."""
    store = InMemoryTaskStore()
    task1 = dispatch_task(store, thread_id="thread-a", description="Task 1")
    task2 = dispatch_task(store, thread_id="thread-a", description="Task 2")
    update_task_result(store, task_id=task1.task_id, result="Result 1")
    update_task_result(store, task_id=task2.task_id, result="Result 2")

    mock_graph = MagicMock()
    mock_graph.stream.return_value = [{"conductor": {"messages": ["ok"]}}]
    config = {"configurable": {"thread_id": "thread-a"}}

    received = []
    poller = AsyncPoller(
        store=store, graph=mock_graph, config=config, interval=1,
        on_result=lambda output: received.append(output),
    )
    poller.start()
    time.sleep(2)
    poller.stop()

    # Each task should trigger its own update_state + stream call
    assert mock_graph.update_state.call_count == 2
    assert mock_graph.stream.call_count == 2

    # Each update_state should have exactly 1 result
    for call in mock_graph.update_state.call_args_list:
        results_buffer = call[0][1]["results_buffer"]
        assert len(results_buffer) == 1


def test_poller_ignores_pending_tasks():
    """Poller does NOT trigger for tasks that are still pending."""
    store = InMemoryTaskStore()
    dispatch_task(store, thread_id="thread-a", description="Still pending")

    mock_graph = MagicMock()
    config = {"configurable": {"thread_id": "thread-a"}}

    poller = AsyncPoller(store=store, graph=mock_graph, config=config, interval=1)
    poller.start()
    time.sleep(2)
    poller.stop()

    mock_graph.update_state.assert_not_called()


def test_poller_marks_delivered_tasks():
    """After delivering results, poller marks tasks so they aren't re-delivered."""
    store = InMemoryTaskStore()
    task = dispatch_task(store, thread_id="thread-a", description="Test task")
    update_task_result(store, task_id=task.task_id, result="Done!")

    mock_graph = MagicMock()
    mock_graph.stream.return_value = []
    config = {"configurable": {"thread_id": "thread-a"}}

    poller = AsyncPoller(store=store, graph=mock_graph, config=config, interval=1)
    poller.start()
    time.sleep(3)  # Wait for at least 2 poll cycles
    poller.stop()

    # Should only have been called once (not re-delivered on second poll)
    assert mock_graph.update_state.call_count == 1


def test_poller_stop():
    """Poller can be stopped cleanly."""
    store = InMemoryTaskStore()
    mock_graph = MagicMock()
    config = {"configurable": {"thread_id": "thread-a"}}

    poller = AsyncPoller(store=store, graph=mock_graph, config=config, interval=1)
    poller.start()
    assert poller._running is True
    poller.stop()
    assert poller._running is False
