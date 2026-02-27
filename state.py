from typing import TypedDict, List, Annotated, Dict
from dataclasses import dataclass
import operator
from datetime import datetime


ASYNC_KEYWORDS = ["calculate", "find", "search", "order", "research"]


@dataclass
class Task:
    task_id: str
    user_query: str
    is_async: bool
    created_at: datetime

    @staticmethod
    def create(user_query: str, is_async: bool = True) -> "Task":
        now = datetime.now()
        return Task(
            task_id=f"Task-{now.strftime('%H%M%S')}",
            user_query=user_query,
            is_async=is_async,
            created_at=now,
        )


class AgentState(TypedDict):
    messages: Annotated[List[dict], operator.add]
    results_buffer: List[dict]
    active_jobs: Dict[str, Task]


def detect_task(user_msg: str) -> Task:
    """Classify every user message as sync or async."""
    is_async = any(k in user_msg.lower() for k in ASYNC_KEYWORDS)
    return Task.create(user_query=user_msg, is_async=is_async)
