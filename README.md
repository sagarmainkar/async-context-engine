# Async Context Engine

[![GitHub stars](https://img.shields.io/github/stars/sagarmainkar/async-context-engine?style=social)](https://github.com/sagarmainkar/async-context-engine/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A **context-aware async task orchestration engine** built with [LangGraph](https://github.com/langchain-ai/langgraph). It demonstrates how to handle long-running background tasks in a conversational AI system — without blocking the user.

The engine classifies user messages in real time, dispatches async work to background scouts, and proactively delivers results back into the conversation when ready.

![demo](https://img.shields.io/badge/status-proof%20of%20concept-orange)

---

## How It Works

```
User Input
    |
    v
 classifier()  ──── checks for async keywords + pending results
    |
    ├──► [ASYNC] ── dispatcher ── ScoutManager.dispatch()
    |                                   |
    |                              background thread
    |                                   |
    |                              result queue
    |                                   |
    |                              result_poller (5s interval)
    |                                   |
    └──► [SYNC] ─── conductor ◄── delivers results via LLM
                        |
                     response
```

**Sync path** — Direct LLM response for regular conversation.

**Async path** — The dispatcher acknowledges the task, a background scout processes it, and the conductor delivers results proactively when they land.

---

## Prerequisites

- **Python 3.11+**
- **[Ollama](https://ollama.com/)** running locally

## Quick Start

```bash
# Clone the repo
git clone https://github.com/sagarmainkar/async-context-engine.git
cd async-context-engine

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Pull the default model
ollama pull gemini-3-flash-preview:cloud

# Run
python runner.py
```

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

---

## Project Structure

```
async-context-engine/
├── runner.py           # Interactive CLI with Rich console UI
├── graph.py            # LangGraph workflow — classifier, dispatcher, conductor
├── state.py            # State schema, Task dataclass, async detection
├── scout_manager.py    # Background task processing with threads + queue
├── tests/
│   ├── test_graph.py
│   ├── test_state.py
│   └── test_scout_manager.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Key Concepts

| Component | Role |
|---|---|
| **Classifier** | Routes each message to sync or async path based on keyword detection |
| **Dispatcher** | Acknowledges async tasks and hands them to the ScoutManager |
| **ScoutManager** | Runs background threads that simulate long-running work |
| **Conductor** | Core LLM node — handles conversation and delivers background results |
| **Result Poller** | Daemon thread that checks for completed tasks every 5 seconds |

## Async Keywords

Messages containing these words are routed to the async path:

`calculate` · `find` · `search` · `order` · `research`

Everything else goes through the sync conversational path.

---

## Configuration

| Setting | Default | Description |
|---|---|---|
| `model` | `gemini-3-flash-preview:cloud` | Ollama model (change in `graph.py`) |
| `poll_interval` | `5s` | How often the poller checks for results |

To use a different model, edit the `llm` variable in `graph.py`:

```python
llm = ChatOllama(model="your-model-name")
```

---

## License

[MIT](LICENSE)
