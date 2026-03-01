import operator
from typing import Annotated
from async_context_engine import AsyncTaskState

ASYNC_KEYWORDS = ["calculate", "find", "search", "order", "research"]


class AgentState(AsyncTaskState):
    messages: Annotated[list[dict], operator.add]


def detect_async(user_msg: str) -> bool:
    """Classify a user message as async or sync."""
    return any(k in user_msg.lower() for k in ASYNC_KEYWORDS)
