"""
Sub-Agent Integration Example

Demonstrates how to use async_context_engine with sub-agents
that run in separate systems. The main graph dispatches a task,
a sub-agent does the work (possibly with 2-way communication),
and reports results back via update_task_result().
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


store = FileTaskStore(path="./sub_agent_tasks.json")


def classifier(state: AgentState) -> str:
    if has_pending_results(state):
        return "conductor"
    # Developer's own routing logic here
    return "conductor"


def dispatcher(state: AgentState, config):
    """Dispatch a task and fire off a sub-agent."""
    thread_id = config["configurable"]["thread_id"]
    task = dispatch_task(store, thread_id, description="Sub-agent research task")

    # --- INTEGRATION POINT ---
    # Fire your sub-agent here. Examples:
    #
    # Option A: HTTP call to a sub-agent service
    # requests.post("http://sub-agent-service/run", json={
    #     "task_id": task.task_id,
    #     "thread_id": thread_id,
    #     "payload": {"query": "research topic X"},
    # })
    #
    # Option B: Message queue (Kafka, SQS, RabbitMQ)
    # producer.send("sub-agent-tasks", {
    #     "task_id": task.task_id,
    #     "payload": {"query": "research topic X"},
    # })
    #
    # Option C: Another LangGraph graph in a separate process
    # sub_graph.invoke({"task_id": task.task_id, ...})
    #
    # The sub-agent, when done, calls:
    #   update_task_result(store, task_id=task.task_id, result="findings...")
    # That's it. The poller handles the rest.
    # --- END INTEGRATION POINT ---

    return {
        "messages": [{"role": "assistant", "content": f"Sub-agent dispatched ({task.task_id})"}],
        "task_records": {task.task_id: task},
    }


def conductor(state: AgentState):
    results = state.get("results_buffer", [])
    if results:
        summary = "\n".join(f"- Task {r['task_id']}: {r['result']}" for r in results)
        return {
            "messages": [{"role": "assistant", "content": f"Results received:\n{summary}"}],
            "results_buffer": [],
        }
    return {
        "messages": [{"role": "assistant", "content": "How can I help?"}],
    }


builder = StateGraph(AgentState)
builder.add_node("conductor", conductor)
builder.add_node("dispatcher", dispatcher)
builder.add_conditional_edges(START, classifier, {"conductor": "conductor", "dispatcher": "dispatcher"})
builder.add_edge("conductor", END)
builder.add_edge("dispatcher", END)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

# --- Poller ---
# config = {"configurable": {"thread_id": "your-session-id"}}
# poller = AsyncPoller(store=store, graph=graph, config=config, interval=5)
# poller.start()
