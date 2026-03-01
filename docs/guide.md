# Async Context Engine — Developer Guide

This guide walks you through every concept in the library, what each piece does, what **you** implement vs. what the **library** handles, and how to integrate it into your own LangGraph agent.

---

## Table of Contents

- [Async Context Engine — Developer Guide](#async-context-engine--developer-guide)
  - [Table of Contents](#table-of-contents)
  - [The Problem](#the-problem)
  - [How the Library Solves It](#how-the-library-solves-it)
  - [Architecture Overview](#architecture-overview)
  - [Core Concepts](#core-concepts)
    - [TaskRecord](#taskrecord)
    - [TaskStore](#taskstore)
    - [AsyncTaskState](#asynctaskstate)
    - [dispatch\_task()](#dispatch_task)
    - [update\_task\_result()](#update_task_result)
    - [has\_pending\_results()](#has_pending_results)
    - [AsyncPoller](#asyncpoller)
  - [What You Implement vs. What the Library Provides](#what-you-implement-vs-what-the-library-provides)
  - [Step-by-Step Integration](#step-by-step-integration)
    - [Step 1: Install](#step-1-install)
    - [Step 2: Define your state](#step-2-define-your-state)
    - [Step 3: Pick a store](#step-3-pick-a-store)
    - [Step 4: Build your graph](#step-4-build-your-graph)
    - [Step 5: Wire up the external system](#step-5-wire-up-the-external-system)
    - [Step 6: Start the poller and run](#step-6-start-the-poller-and-run)
  - [API Reference](#api-reference)
    - [`dispatch_task(store, thread_id, description) -> TaskRecord`](#dispatch_taskstore-thread_id-description---taskrecord)
    - [`update_task_result(store, task_id, result=None, error=None) -> None`](#update_task_resultstore-task_id-resultnone-errornone---none)
    - [`has_pending_results(state) -> bool`](#has_pending_resultsstate---bool)
    - [`AsyncPoller(store, graph, config, interval=5, on_result=None)`](#asyncpollerstore-graph-config-interval5-on_resultnone)
    - [`TaskStore` (ABC)](#taskstore-abc)
    - [`TaskRecord` (dataclass)](#taskrecord-dataclass)
    - [`AsyncTaskState` (TypedDict)](#asynctaskstate-typeddict)
  - [Running the Example](#running-the-example)

---

## The Problem

LangGraph agents run synchronously — when a user sends a message, the graph processes it and returns a response. But what if a task does not take 10 seconds, 30 seconds, or 5 minutes, takes may be an hour ?(database queries, API calls to slow services, sub-agent work, report generation)

You don't want to block the conversation. You want to:

1. **Acknowledge** the task immediately ("I'm working on it")
2. **Let the user keep chatting** while it runs in the background
3. **Proactively deliver results** when the background work finishes

This is the **async context re-entry** problem. The library solves it.

---

## How the Library Solves It

```
User says "calculate the total for Order Alpha"
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  YOUR GRAPH                                             │
│                                                         │
│  classifier() ──► "async" ──► dispatcher()              │
│       │                           │                     │
│       │                     dispatch_task()  ◄── LIBRARY │
│       │                           │                     │
│       │                     returns TaskRecord          │
│       │                     with task_id                │
│       │                           │                     │
│       │                     YOU send task_id to          │
│       │                     your external system         │
│       │                           │                     │
│       ▼                           ▼                     │
│  "sync" ──► conductor()     ack message to user         │
└─────────────────────────────────────────────────────────┘

Meanwhile, in the background:

┌─────────────────────────────────────────────────────────┐
│  EXTERNAL SYSTEM (yours)                                │
│                                                         │
│  Does the actual work...                                │
│  When done, calls:                                      │
│                                                         │
│    update_task_result(store, task_id, result="$1,250")   │
│                                              ◄── LIBRARY │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  ASYNC POLLER (library, runs automatically)             │
│                                                         │
│  Every N seconds:                                       │
│    1. Checks TaskStore for completed/failed tasks       │
│    2. Injects results into graph state                  │
│    3. Triggers a graph run                              │
│    4. Calls your on_result callback with the output     │
│                                                         │
│  Result appears in the user's terminal automatically.   │
└─────────────────────────────────────────────────────────┘
```

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                  async_context_engine                 │
│                                                      │
│  ┌────────────┐  ┌────────────┐  ┌───────────────┐  │
│  │ TaskRecord  │  │ TaskStore  │  │AsyncTaskState │  │
│  │ (dataclass) │  │   (ABC)    │  │  (TypedDict)  │  │
│  └────────────┘  └─────┬──────┘  └───────────────┘  │
│                        │                             │
│              ┌─────────┴─────────┐                   │
│              │                   │                   │
│     ┌────────┴───────┐ ┌────────┴────────┐           │
│     │InMemoryTaskStore│ │ FileTaskStore   │           │
│     │  (for tests)    │ │ (JSON on disk)  │           │
│     └────────────────┘ └────────────────┘           │
│                                                      │
│  ┌──────────────┐  ┌───────────────────┐             │
│  │dispatch_task()│  │update_task_result()│             │
│  │ (create task) │  │ (complete task)    │             │
│  └──────────────┘  └───────────────────┘             │
│                                                      │
│  ┌────────────────────┐  ┌──────────────────┐        │
│  │has_pending_results()│  │   AsyncPoller    │        │
│  │ (check state)       │  │ (background poll)│        │
│  └────────────────────┘  └──────────────────┘        │
└──────────────────────────────────────────────────────┘
```

---

## Core Concepts

### TaskRecord

**What it is:** A dataclass representing a single background task.

**Who creates it:** The library, when you call `dispatch_task()`.

```python
@dataclass
class TaskRecord:
    task_id: str       # UUID, auto-generated
    thread_id: str     # Links task to a conversation session
    status: str        # "pending" → "completed" | "failed"
    description: str   # Human-readable, e.g. "calculate total for Order Alpha"
    result: str | None # Filled when task completes
    error: str | None  # Filled when task fails
    created_at: datetime
    updated_at: datetime
```

**Lifecycle:**

```
pending ──► completed  (success: result is set)
   │
   └─────► failed      (failure: error is set)
```

---

### TaskStore

**What it is:** An abstract base class (ABC) defining how tasks are persisted. Think of it as the database interface.

**Who implements it:** The library ships two implementations. You can write your own.

| Implementation | Use case |
|---|---|
| `InMemoryTaskStore` | Unit tests, prototyping |
| `FileTaskStore` | Single-machine apps, demos |
| *Your own* | Postgres, Redis, DynamoDB, etc. |

**The interface** (5 methods):

```python
class TaskStore(ABC):
    def create_task(self, record: TaskRecord) -> None: ...
    def update_task(self, task_id, status, result=None, error=None) -> None: ...
    def get_task(self, task_id: str) -> TaskRecord | None: ...
    def get_tasks_by_thread(self, thread_id: str) -> list[TaskRecord]: ...
    def get_tasks_by_status(self, thread_id, status) -> list[TaskRecord]: ...
```

**To write your own store**, subclass `TaskStore` and implement all 5 methods:

```python
from async_context_engine import TaskStore, TaskRecord

class PostgresTaskStore(TaskStore):
    def __init__(self, connection_string: str):
        self._conn = connect(connection_string)

    def create_task(self, record: TaskRecord) -> None:
        self._conn.execute("INSERT INTO tasks ...", ...)

    # ... implement the other 4 methods
```

---

### AsyncTaskState

**What it is:** A `TypedDict` mixin that adds two fields to your LangGraph state.

**Who uses it:** You. Extend it when defining your graph's state.

```python
class AsyncTaskState(TypedDict):
    task_records: dict[str, TaskRecord]  # All dispatched tasks, keyed by task_id
    results_buffer: list[dict]           # Filled by the poller when results arrive
```

**How to use it** — extend it with your own fields:

```python
from async_context_engine import AsyncTaskState

class MyAgentState(AsyncTaskState):
    messages: Annotated[list[dict], operator.add]
    # ... your other state fields
```

You never write to `task_records` or `results_buffer` directly. The library manages them.

---

### dispatch_task()

**What it does:** Creates a new task in the store with status `"pending"` and returns the `TaskRecord`.

**Who calls it:** You, inside your graph's dispatcher node.

```python
from async_context_engine import dispatch_task

def my_dispatcher(state, config):
    thread_id = config["configurable"]["thread_id"]
    task = dispatch_task(store, thread_id, description="calculate total")

    # Send task.task_id to your external system
    my_external_system.run(task.task_id, "calculate total")

    return {
        "messages": [{"role": "assistant", "content": "Working on it..."}],
        "task_records": {task.task_id: task},
    }
```

---

### update_task_result()

**What it does:** Marks a task as `"completed"` (with a result) or `"failed"` (with an error) in the store.

**Who calls it:** Your external system, sub-agent, or worker — the thing doing the actual work. This can be a completely separate process, a different microservice, or a background thread.

```python
from async_context_engine import update_task_result

# On success:
update_task_result(store, task_id="abc-123", result="$1,250")

# On failure:
update_task_result(store, task_id="abc-123", error="API timeout")
```

This is the bridge between your external system and the library. After you call this, the poller will pick it up automatically.

---

### has_pending_results()

**What it does:** Returns `True` if `results_buffer` in the graph state is non-empty.

**Who calls it:** You, in your classifier/router node, to detect when the poller has injected results.

```python
from async_context_engine import has_pending_results

def classifier(state) -> str:
    if has_pending_results(state):
        return "sync"  # Route to conductor to present results

    if is_async_task(state):
        return "async"  # Route to dispatcher
    return "sync"       # Normal conversation
```

---

### AsyncPoller

**What it is:** A daemon thread that runs in the background, checking the `TaskStore` at a configurable interval. When it finds completed or failed tasks, it:

1. Injects results into the graph state via `graph.update_state()`
2. Triggers a graph run with a synthetic message
3. Calls your `on_result` callback with each output chunk

**Who creates it:** You, in your application's entry point (outside the graph).

```python
from async_context_engine import AsyncPoller

def display(output):
    if "conductor" in output:
        print(output["conductor"]["messages"][-1].content)

poller = AsyncPoller(
    store=store,        # Your TaskStore instance
    graph=graph,        # Your compiled LangGraph
    config=config,      # Must include configurable.thread_id
    interval=5,         # Poll every 5 seconds
    on_result=display,  # Called with each graph output chunk
)
poller.start()
# ... your app runs ...
poller.stop()
```

---

## What You Implement vs. What the Library Provides

| Responsibility | Who | Details |
|---|---|---|
| Define graph state | **You** | Extend `AsyncTaskState` with your fields |
| Build the LangGraph | **You** | Nodes, edges, classifier logic |
| Decide what's async | **You** | Your classifier routes messages |
| Dispatch tasks | **You** | Call `dispatch_task()` in your dispatcher node |
| Execute the work | **You** | Sub-agents, APIs, workers — your choice |
| Report results back | **You** | Call `update_task_result()` when work finishes |
| Display output | **You** | Pass `on_result` callback to poller |
| Generate task IDs | **Library** | UUID generated by `dispatch_task()` |
| Persist task state | **Library** | Via `TaskStore` (you pick the backend) |
| Poll for completions | **Library** | `AsyncPoller` runs automatically |
| Re-enter the graph | **Library** | Poller calls `graph.update_state()` + `graph.stream()` |
| Track delivered tasks | **Library** | Poller deduplicates — each task delivered once |

---

## Step-by-Step Integration

### Step 1: Install

```bash
pip install async-context-engine

# Or with uv (recommended):
uv add async-context-engine
```

### Step 2: Define your state

```python
import operator
from typing import Annotated
from async_context_engine import AsyncTaskState

class MyState(AsyncTaskState):
    messages: Annotated[list[dict], operator.add]
```

### Step 3: Pick a store

```python
from async_context_engine import FileTaskStore  # or InMemoryTaskStore

store = FileTaskStore(path="./tasks.json")
```

### Step 4: Build your graph

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from async_context_engine import dispatch_task, has_pending_results

def classifier(state) -> str:
    if has_pending_results(state):
        return "sync"
    # Your async detection logic here
    return "async" if needs_background_work(state) else "sync"

def dispatcher(state, config):
    thread_id = config["configurable"]["thread_id"]
    task = dispatch_task(store, thread_id, description="...")

    # Send to your external system
    my_system.run(task.task_id, "...")

    return {
        "messages": [{"role": "assistant", "content": "On it!"}],
        "task_records": {task.task_id: task},
    }

def conductor(state):
    results = state.get("results_buffer", [])
    # Use results in your LLM prompt if present
    # Clear the buffer after processing
    return {"messages": [...], "results_buffer": []}

builder = StateGraph(MyState)
builder.add_node("conductor", conductor)
builder.add_node("dispatcher", dispatcher)
builder.add_conditional_edges(START, classifier, {"sync": "conductor", "async": "dispatcher"})
builder.add_edge("conductor", END)
builder.add_edge("dispatcher", END)

graph = builder.compile(checkpointer=MemorySaver())
```

### Step 5: Wire up the external system

Your external system receives the `task_id` and calls `update_task_result()` when done:

```python
from async_context_engine import update_task_result

# This can be anywhere — a different process, a webhook handler, a worker
def on_work_complete(task_id, data):
    update_task_result(store, task_id=task_id, result=data)
```

### Step 6: Start the poller and run

```python
from async_context_engine import AsyncPoller

config = {"configurable": {"thread_id": "session-001"}}

poller = AsyncPoller(
    store=store, graph=graph, config=config,
    interval=5,
    on_result=lambda output: print(output),
)
poller.start()

# Your main loop (CLI, web server, etc.)
for user_input in get_user_messages():
    for chunk in graph.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config,
    ):
        handle_output(chunk)

poller.stop()
```

---

## API Reference

### `dispatch_task(store, thread_id, description) -> TaskRecord`

| Parameter | Type | Description |
|---|---|---|
| `store` | `TaskStore` | The persistence backend |
| `thread_id` | `str` | Conversation/session identifier |
| `description` | `str` | Human-readable task description |
| **Returns** | `TaskRecord` | The created record (status="pending") |

### `update_task_result(store, task_id, result=None, error=None) -> None`

| Parameter | Type | Description |
|---|---|---|
| `store` | `TaskStore` | The persistence backend |
| `task_id` | `str` | The task to update |
| `result` | `str \| None` | Set for success (status → "completed") |
| `error` | `str \| None` | Set for failure (status → "failed") |

### `has_pending_results(state) -> bool`

| Parameter | Type | Description |
|---|---|---|
| `state` | `dict` | The current graph state |
| **Returns** | `bool` | `True` if `results_buffer` is non-empty |

### `AsyncPoller(store, graph, config, interval=5, on_result=None)`

| Parameter | Type | Description |
|---|---|---|
| `store` | `TaskStore` | The persistence backend |
| `graph` | Compiled graph | Your LangGraph graph |
| `config` | `dict` | Must contain `configurable.thread_id` |
| `interval` | `int` | Seconds between poll cycles (default: 5) |
| `on_result` | `(dict) -> None \| None` | Callback for each graph output chunk |

**Methods:**

| Method | Description |
|---|---|
| `start()` | Launch the background polling thread |
| `stop()` | Signal the thread to stop after the current cycle |

### `TaskStore` (ABC)

| Method | Signature |
|---|---|
| `create_task` | `(record: TaskRecord) -> None` |
| `update_task` | `(task_id, status, result=None, error=None) -> None` |
| `get_task` | `(task_id: str) -> TaskRecord \| None` |
| `get_tasks_by_thread` | `(thread_id: str) -> list[TaskRecord]` |
| `get_tasks_by_status` | `(thread_id, status) -> list[TaskRecord]` |

### `TaskRecord` (dataclass)

| Field | Type | Description |
|---|---|---|
| `task_id` | `str` | UUID, auto-generated |
| `thread_id` | `str` | Conversation session ID |
| `status` | `str` | `"pending"`, `"completed"`, or `"failed"` |
| `description` | `str` | Human-readable description |
| `result` | `str \| None` | Output data on success |
| `error` | `str \| None` | Error message on failure |
| `created_at` | `datetime` | When the task was dispatched |
| `updated_at` | `datetime` | Last status change |

### `AsyncTaskState` (TypedDict)

| Field | Type | Description |
|---|---|---|
| `task_records` | `dict[str, TaskRecord]` | All tasks, keyed by task_id |
| `results_buffer` | `list[dict]` | Completed results awaiting processing |

---

## Running the Example

The repo includes a working demo in `examples/basic/`.

```bash
# Clone the repo
git clone https://github.com/sagarmainkar/async-context-engine.git
cd async-context-engine

# Install everything — library + example dependencies
# uv creates .venv automatically, no manual venv setup needed
uv sync --extra examples

# Start Ollama (required for the example LLM)
ollama serve

# Run the demo
cd examples/basic
uv run runner.py
```

> `uv sync` handles venv creation, dependency resolution, and editable install in one step. If you prefer pip, use `pip install -e ".[examples]"` inside a manually created venv.

Try these prompts to trigger async tasks:

| Prompt | What happens |
|---|---|
| "calculate the total for Order Alpha" | Dispatched, result in ~20s |
| "search for quarterly reports" | Dispatched, result in ~10s |
| "What is the capital of France?" | Answered immediately (sync) |
