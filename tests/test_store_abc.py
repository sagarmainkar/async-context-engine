import pytest
from async_context_engine.store import TaskStore


def test_task_store_is_abstract():
    """TaskStore cannot be instantiated directly."""
    with pytest.raises(TypeError):
        TaskStore()


def test_task_store_has_required_methods():
    """TaskStore defines the expected abstract methods."""
    abstract_methods = TaskStore.__abstractmethods__
    assert "create_task" in abstract_methods
    assert "update_task" in abstract_methods
    assert "get_task" in abstract_methods
    assert "get_tasks_by_thread" in abstract_methods
    assert "get_tasks_by_status" in abstract_methods
