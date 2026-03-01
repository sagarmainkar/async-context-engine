import re
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from async_context_engine import dispatch_task, has_pending_results, FileTaskStore
from state import AgentState, detect_async
from scout_manager import ScoutManager

store = FileTaskStore(path="./demo_tasks.json")
scout_manager = ScoutManager(store=store)

llm = ChatOllama(model="gemini-3-flash-preview:cloud", base_url="http://127.0.0.1:11434")


def classifier(state: AgentState) -> str:
    if has_pending_results(state):
        return "sync"

    last_user_msg = next(
        (m for m in reversed(state["messages"]) if m["role"] == "user"), None
    )
    if last_user_msg and detect_async(last_user_msg["content"]):
        return "async"
    return "sync"


def task_dispatcher(state: AgentState, config):
    last_user_msg = next(
        (m for m in reversed(state["messages"]) if m["role"] == "user"), None
    )
    user_query = last_user_msg["content"] if last_user_msg else "unknown task"
    thread_id = config["configurable"]["thread_id"]

    task = dispatch_task(store, thread_id, description=user_query)
    scout_manager.dispatch(task.task_id, user_query)

    ack_message = {
        "role": "assistant",
        "content": (
            f"Got it! I'm working on that now — it may take a moment. "
            f"I'll let you know as soon as the results are ready. "
            f"In the meantime, feel free to ask me anything else."
        ),
    }

    return {
        "messages": [ack_message],
        "task_records": {task.task_id: task},
    }


def conductor(state: AgentState):
    messages = list(state["messages"])
    results = state.get("results_buffer", [])

    system_notes = []

    task_records = state.get("task_records", {})
    pending = {tid: t for tid, t in task_records.items() if t.status == "pending"}
    if pending:
        job_lines = [f'- "{t.description}" (task {tid})' for tid, t in pending.items()]
        system_notes.append(
            "SYSTEM: The following tasks are being processed in the background by "
            "separate workers. Do NOT try to answer these — "
            "results will arrive automatically when ready.\n" + "\n".join(job_lines)
        )

    if results:
        parts = [
            f"COMPLETED: Task '{r['task_id']}' Result: {r['result']}"
            for r in results
        ]
        data_str = "\n".join(parts)
        system_notes.append(
            f"SYSTEM: Background task results just landed:\n{data_str}\n"
            "Proactively inform the user about these results."
        )

    history = messages + [{"role": "system", "content": note} for note in system_notes]
    response = llm.invoke(history)

    if hasattr(response, "content"):
        response.content = re.sub(r"<\|[^>]+\|>", "", response.content).strip()

    return {
        "messages": [response],
        "results_buffer": [],
    }


builder = StateGraph(AgentState)
builder.add_node("conductor", conductor)
builder.add_node("dispatcher", task_dispatcher)
builder.add_conditional_edges(
    START, classifier, {"sync": "conductor", "async": "dispatcher"},
)
builder.add_edge("conductor", END)
builder.add_edge("dispatcher", END)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)
