from state import AgentState, Task


def _make_state(user_content: str, results_buffer=None) -> AgentState:
    return {
        "messages": [{"role": "user", "content": user_content}],
        "results_buffer": results_buffer or [],
        "active_jobs": {},
    }


def test_classifier_routes_async_keyword():
    from graph import classifier
    state = _make_state("calculate the total for Order Alpha")
    result = classifier(state)
    assert result == "async"


def test_classifier_routes_sync_no_keyword():
    from graph import classifier
    state = _make_state("what's a good pizza place?")
    result = classifier(state)
    assert result == "sync"


def test_classifier_routes_sync_when_results_buffer_has_data():
    """Even if message has async keyword, if results_buffer has data, route to sync
    so the conductor can deliver the results."""
    from graph import classifier
    state = _make_state(
        "calculate something",
        results_buffer=[{"task_id": "Task-1", "user_query": "old question", "data": "$100"}],
    )
    result = classifier(state)
    assert result == "sync"


def test_task_dispatcher_returns_ack_message():
    from graph import task_dispatcher
    state = _make_state("calculate the total for Order Alpha")
    result = task_dispatcher(state)
    # Should return messages with an acknowledgment
    assert len(result["messages"]) == 1
    ack = result["messages"][0]
    assert ack["role"] == "assistant"
    assert "take" in ack["content"].lower() or "working" in ack["content"].lower()


def test_task_dispatcher_registers_active_job():
    from graph import task_dispatcher
    state = _make_state("calculate the total for Order Alpha")
    result = task_dispatcher(state)
    # Should have registered the task — check that active_jobs is returned
    assert "active_jobs" in result
    assert len(result["active_jobs"]) == 1
    task_id = list(result["active_jobs"].keys())[0]
    assert task_id.startswith("Task-")


def test_graph_has_expected_nodes():
    from graph import graph
    # The compiled graph should have our two application nodes
    node_names = set(graph.get_graph().nodes.keys())
    # LangGraph adds __start__ and __end__ automatically
    assert "conductor" in node_names
    assert "dispatcher" in node_names


def test_task_dispatcher_dispatches_to_scout_manager():
    """Verify task_dispatcher calls scout_manager.dispatch()."""
    import graph as graph_module
    original_dispatch = graph_module.scout_manager.dispatch
    dispatched_tasks = []
    graph_module.scout_manager.dispatch = lambda task: dispatched_tasks.append(task)
    try:
        state = _make_state("calculate the total for Order Alpha")
        graph_module.task_dispatcher(state)
        assert len(dispatched_tasks) == 1
        assert dispatched_tasks[0].user_query == "calculate the total for Order Alpha"
        assert dispatched_tasks[0].is_async is True
    finally:
        graph_module.scout_manager.dispatch = original_dispatch
