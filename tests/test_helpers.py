from async_context_engine.helpers import has_pending_results


def test_has_pending_results_true():
    state = {"results_buffer": [{"task_id": "t1", "result": "done"}]}
    assert has_pending_results(state) is True


def test_has_pending_results_false_empty_list():
    state = {"results_buffer": []}
    assert has_pending_results(state) is False


def test_has_pending_results_false_missing_key():
    state = {}
    assert has_pending_results(state) is False
