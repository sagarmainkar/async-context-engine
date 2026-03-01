import re
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from state import AgentState, detect_task
from scout_manager import ScoutManager

scout_manager = ScoutManager()

# Setup Ollama model
llm = ChatOllama(model="gemini-3-flash-preview:cloud", base_url="http://127.0.0.1:11434")

def classifier(state: AgentState) -> str:
    """Router: classify the latest user message as sync or async.
    If results_buffer has pending data, always route to sync so
    the conductor can deliver the results."""
    if state.get("results_buffer"):
        return "sync"

    last_user_msg = next(
        (m for m in reversed(state["messages"]) if m["role"] == "user"), None
    )
    if last_user_msg:
        task = detect_task(last_user_msg["content"])
        if task.is_async:
            return "async"
    return "sync"

def task_dispatcher(state: AgentState):
    """Acknowledge async task and register it for background processing."""
    last_user_msg = next(
        (m for m in reversed(state["messages"]) if m["role"] == "user"), None
    )
    user_query = last_user_msg["content"] if last_user_msg else "unknown task"
    task = detect_task(user_query)

    scout_manager.dispatch(task)

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
        "active_jobs": {task.task_id: task},
    }

def conductor(state: AgentState):
    """Core conductor node: sees conversation history, background results, and synthesizes."""
    messages = list(state["messages"])
    results = state.get("results_buffer", [])

    system_notes = []

    # Tell the LLM about tasks being handled in the background
    active_jobs = state.get("active_jobs", {})
    if active_jobs:
        job_lines = [f"- \"{t.user_query}\" (task {tid})" for tid, t in active_jobs.items()]
        system_notes.append(
            "SYSTEM: The following tasks are being processed in the background by "
            "separate workers. Do NOT try to answer, address, or help with these — "
            "results will arrive automatically when ready. Just focus on the user's "
            "current message.\n" + "\n".join(job_lines)
        )

    # Deliver completed background results
    if results:
        parts = []
        for r in results:
            parts.append(
                f"COMPLETED: Task '{r['task_id']}' "
                f"(Original question: \"{r['user_query']}\") "
                f"Result: {r['data']}"
            )
        data_str = "\n".join(parts)
        system_notes.append(
            f"SYSTEM: Background task results just landed:\n{data_str}\n"
            "These were requested earlier in the conversation. "
            "Proactively inform the user about these results. "
            "Link each result back to their original question. "
            "Be natural — say something like 'Hey, remember when you asked about X? "
            "I have the results now.'"
        )

    history = messages + [{"role": "system", "content": note} for note in system_notes]
    response = llm.invoke(history)

    # Strip leaked special tokens from small models (e.g. llama3.2:1b)
    if hasattr(response, "content"):
        response.content = re.sub(r"<\|[^>]+\|>", "", response.content).strip()

    return {
        "messages": [response],
        "results_buffer": [],  # Clear buffer after synthesis
    }

# --- Build Graph ---

builder = StateGraph(AgentState)

# Add nodes
builder.add_node("conductor", conductor)
builder.add_node("dispatcher", task_dispatcher)

# Conditional routing from START based on classifier
builder.add_conditional_edges(
    START,
    classifier,
    {"sync": "conductor", "async": "dispatcher"},
)

# Both nodes terminate
builder.add_edge("conductor", END)
builder.add_edge("dispatcher", END)

# Checkpointer to maintain state across runs
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)
