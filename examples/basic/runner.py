import time
import threading
import uuid
from dotenv import load_dotenv

load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from graph import graph, scout_manager

console = Console()

# Session config — single thread for the demo
config = {"configurable": {"thread_id": f"session-{uuid.uuid4().hex[:8]}"}}


def result_poller(interval=5):
    """Periodically check ScoutManager for completed results and deliver them."""
    while True:
        time.sleep(interval)
        completed = scout_manager.get_completed()
        if not completed:
            continue

        # Ingest results into graph state
        graph.update_state(config, {"results_buffer": completed})

        # Trigger graph run to deliver results via the conductor
        for output in graph.stream(
            {"messages": [{"role": "user", "content": "[system: background task completed]"}]},
            config,
        ):
            if "conductor" in output:
                msg = output["conductor"]["messages"][-1]
                content = msg.content if hasattr(msg, "content") else msg.get("content", "")
                console.print()
                console.print(
                    Panel(
                        content,
                        title="[bold green]Async Result[/bold green]",
                        border_style="green",
                        subtitle="background task completed",
                    )
                )
                console.print("[bold yellow]You:[/bold yellow] ", end="")


def main():
    console.print()
    console.print(
        Panel(
            "[bold cyan]Async Context Engine[/bold cyan]\n"
            "[dim]Context-aware async task orchestration powered by LangGraph[/dim]",
            border_style="cyan",
            subtitle="v3.0",
        )
    )
    console.print("[dim]Type your messages. Async tasks run in the background.[/dim]")
    console.print("[dim]Type 'quit' to exit.[/dim]\n")

    # Start background poller
    poller = threading.Thread(target=result_poller, daemon=True)
    poller.start()

    while True:
        try:
            user_input = console.input("[bold yellow]You:[/bold yellow] ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            break

        # Run the graph
        for output in graph.stream(
            {"messages": [{"role": "user", "content": user_input}]},
            config,
        ):
            if "conductor" in output:
                msg = output["conductor"]["messages"][-1]
                content = msg.content if hasattr(msg, "content") else msg.get("content", "")
                console.print(
                    Panel(
                        content,
                        title="[bold magenta]Conductor[/bold magenta]",
                        border_style="magenta",
                    )
                )
            elif "dispatcher" in output:
                msg = output["dispatcher"]["messages"][-1]
                content = msg.get("content", "")
                console.print(
                    Panel(
                        content,
                        title="[bold blue]Dispatcher[/bold blue]",
                        border_style="blue",
                        subtitle="task queued",
                    )
                )

    console.print("\n[dim]Session ended. Goodbye![/dim]")


if __name__ == "__main__":
    main()
