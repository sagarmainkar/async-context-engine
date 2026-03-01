"""
Multi-Agent Fan-Out/Fan-In Example

Demonstrates dispatching multiple tasks to different specialized sub-agents.
Each sub-agent works independently and reports results back via
update_task_result(). The poller collects all results and the conductor
synthesizes them.
"""
import operator
from typing import Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from async_context_engine import (
    AsyncTaskState,
    AsyncPoller,
    FileTaskStore,
    dispatch_task,
    update_task_result,
    has_pending_results,
)


class AgentState(AsyncTaskState):
    messages: Annotated[list[dict], operator.add]


store = FileTaskStore(path="./multi_agent_tasks.json")


def classifier(state: AgentState) -> str:
    if has_pending_results(state):
        return "conductor"
    return "conductor"


def fan_out_dispatcher(state: AgentState, config):
    """Dispatch multiple tasks to different sub-agents."""
    thread_id = config["configurable"]["thread_id"]

    research_task = dispatch_task(store, thread_id, description="Research market trends")
    data_task = dispatch_task(store, thread_id, description="Fetch sales data")
    analysis_task = dispatch_task(store, thread_id, description="Run sentiment analysis")

    # --- INTEGRATION POINT ---
    # Fire each sub-agent independently:
    #
    # fire_sub_agent("research-agent", task_id=research_task.task_id, ...)
    # fire_sub_agent("data-agent", task_id=data_task.task_id, ...)
    # fire_sub_agent("analysis-agent", task_id=analysis_task.task_id, ...)
    #
    # Each sub-agent calls update_task_result() when done.
    # The poller collects results as they arrive.
    # The conductor synthesizes all results together.
    # --- END INTEGRATION POINT ---

    return {
        "messages": [{"role": "assistant", "content": (
            f"Dispatched 3 sub-agents:\n"
            f"- Research: {research_task.task_id}\n"
            f"- Data: {data_task.task_id}\n"
            f"- Analysis: {analysis_task.task_id}"
        )}],
        "task_records": {
            research_task.task_id: research_task,
            data_task.task_id: data_task,
            analysis_task.task_id: analysis_task,
        },
    }


def conductor(state: AgentState):
    results = state.get("results_buffer", [])
    if results:
        summary = "\n".join(f"- {r['description']}: {r['result']}" for r in results)
        return {
            "messages": [{"role": "assistant", "content": f"Sub-agent results:\n{summary}"}],
            "results_buffer": [],
        }
    return {
        "messages": [{"role": "assistant", "content": "Waiting for sub-agent results..."}],
    }


builder = StateGraph(AgentState)
builder.add_node("conductor", conductor)
builder.add_node("fan_out_dispatcher", fan_out_dispatcher)
builder.add_conditional_edges(START, classifier, {"conductor": "conductor", "dispatcher": "fan_out_dispatcher"})
builder.add_edge("conductor", END)
builder.add_edge("fan_out_dispatcher", END)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)
