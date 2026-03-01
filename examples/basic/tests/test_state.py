from state import detect_async, AgentState


def test_detect_async_returns_true_for_keyword():
    assert detect_async("calculate the total for Order Alpha") is True


def test_detect_async_returns_false_for_no_keyword():
    assert detect_async("what's a good pizza place?") is False


def test_agent_state_has_library_fields():
    """AgentState extends AsyncTaskState with messages."""
    annotations = AgentState.__annotations__
    assert "messages" in annotations
    assert "task_records" in annotations
    assert "results_buffer" in annotations
