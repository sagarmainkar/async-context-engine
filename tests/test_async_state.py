import operator
from typing import Annotated
from async_context_engine.state import AsyncTaskState


def test_async_task_state_has_required_keys():
    annotations = AsyncTaskState.__annotations__
    assert "task_records" in annotations
    assert "results_buffer" in annotations


def test_async_task_state_composable():
    from typing import TypedDict

    class MyState(AsyncTaskState):
        messages: Annotated[list[dict], operator.add]

    annotations = MyState.__annotations__
    assert "messages" in annotations
    assert "task_records" in annotations
    assert "results_buffer" in annotations
