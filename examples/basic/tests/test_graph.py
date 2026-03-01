import sys
import os

# Add examples/basic to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state import AgentState, detect_async


def _make_state(user_content: str, results_buffer=None) -> AgentState:
    return {
        "messages": [{"role": "user", "content": user_content}],
        "results_buffer": results_buffer or [],
        "task_records": {},
    }


def test_detect_async_keyword():
    assert detect_async("calculate the total for Order Alpha") is True


def test_detect_async_no_keyword():
    assert detect_async("what's a good pizza place?") is False


def test_state_has_expected_fields():
    state = _make_state("hello")
    assert "messages" in state
    assert "results_buffer" in state
    assert "task_records" in state
