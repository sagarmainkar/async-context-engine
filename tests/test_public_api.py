def test_public_api_imports():
    """All public API symbols are importable from the top-level package."""
    from async_context_engine import (
        TaskRecord,
        AsyncTaskState,
        TaskStore,
        InMemoryTaskStore,
        FileTaskStore,
        dispatch_task,
        update_task_result,
        has_pending_results,
        AsyncPoller,
    )
    assert TaskRecord is not None
    assert AsyncTaskState is not None
    assert TaskStore is not None
    assert InMemoryTaskStore is not None
    assert FileTaskStore is not None
    assert dispatch_task is not None
    assert update_task_result is not None
    assert has_pending_results is not None
    assert AsyncPoller is not None
