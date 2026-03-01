# Async Context Engine

[![PyPI version](https://img.shields.io/pypi/v/async-context-engine.svg)](https://pypi.org/project/async-context-engine/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Plug-and-play **async context re-entry** for [LangGraph](https://github.com/langchain-ai/langgraph) agents.

Dispatch long-running tasks to external systems, let the user keep chatting, and deliver results back into the conversation automatically — without blocking.

## The Problem

LangGraph agents are synchronous. When a task takes 10 seconds or 5 minutes, you have two bad options: block the user, or lose the result. This library gives you a third option: **dispatch, continue, re-enter**.

## How It Works

```
1. User asks for something slow     →  Your graph dispatches the task
2. Library tracks it in a TaskStore  →  User keeps chatting normally
3. External system finishes work     →  Calls update_task_result()
4. Built-in poller detects it        →  Re-enters the graph automatically
5. Result appears in conversation    →  Without the user asking again
```

## Install

```bash
pip install async-context-engine

# Or with uv (recommended):
uv add async-context-engine
```

## Quick Start

**1. Extend your state:**

```python
from async_context_engine import AsyncTaskState

class MyState(AsyncTaskState):
    messages: Annotated[list[dict], operator.add]
```

**2. Dispatch tasks in your graph:**

```python
from async_context_engine import dispatch_task

def dispatcher(state, config):
    task = dispatch_task(store, config["configurable"]["thread_id"], "calculate total")
    my_system.run(task.task_id, "calculate total")  # Send to your worker
    return {"messages": [...], "task_records": {task.task_id: task}}
```

**3. Report results from your external system:**

```python
from async_context_engine import update_task_result

update_task_result(store, task_id="abc-123", result="$1,250")
```

**4. Start the poller:**

```python
from async_context_engine import AsyncPoller

poller = AsyncPoller(store=store, graph=graph, config=config, interval=5, on_result=display)
poller.start()
```

That's it. Results flow back into the conversation automatically.

## What You Build vs. What the Library Handles

| You | Library |
|---|---|
| Your LangGraph graph (nodes, edges, LLM) | Task ID generation |
| Decide what's async (classifier) | Task persistence (TaskStore) |
| Execute the actual work (sub-agents, APIs) | Background polling |
| Call `dispatch_task()` and `update_task_result()` | Graph re-entry with results |
| Display output (`on_result` callback) | Deduplication (each result delivered once) |

## Documentation

**[Developer Guide](docs/guide.md)** — Comprehensive walkthrough of every concept, the full API reference, architecture diagrams, and step-by-step integration instructions.

## Shipped Components

| Component | Description |
|---|---|
| `TaskRecord` | Dataclass representing a tracked task |
| `TaskStore` | ABC for pluggable persistence |
| `InMemoryTaskStore` | Dict-backed store for tests |
| `FileTaskStore` | JSON file store for prototyping |
| `AsyncTaskState` | LangGraph state mixin (extend this) |
| `dispatch_task()` | Create a pending task in the store |
| `update_task_result()` | Mark a task complete/failed (called from external systems) |
| `has_pending_results()` | Check if results are waiting in state |
| `AsyncPoller` | Background thread that polls and re-enters the graph |

## Running the Example

```bash
git clone https://github.com/sagarmainkar/async-context-engine.git
cd async-context-engine

# Install everything (library + example dependencies)
uv sync --extra examples

# Start Ollama (required for the example LLM)
ollama serve

# Run the demo
cd examples/basic
uv run runner.py
```

> **No venv creation needed.** `uv sync` creates the `.venv` automatically, resolves all dependencies, and installs the library in editable mode — one command, everything works.

## License

[MIT](LICENSE)
